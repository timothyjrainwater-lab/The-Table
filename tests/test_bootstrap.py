"""Integration tests for M1 Runtime Session Bootstrap.

Tests:
- New campaign session start
- Resume with full replay
- Partial write recovery (discard after last turn_end)
- Corruption detection (invalid JSON, missing files)
- Hash mismatch detection (10× replay verification)
- Log desync detection (EventLog vs SessionLog)

All tests use tmp_path fixture (no persistent state).
"""

import json
import pytest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from aidm.runtime.bootstrap import (
    SessionBootstrap,
    BootstrapError,
    PartialWriteRecoveryResult,
    LogSyncCheckResult,
)
from aidm.core.campaign_store import CampaignStore
from aidm.core.state import WorldState
from aidm.core.event_log import Event, EventLog
from aidm.core.session_log import SessionLog as CoreSessionLog, SessionLogEntry
from aidm.schemas.campaign import SessionZeroConfig, CampaignManifest
from aidm.schemas.intent_lifecycle import IntentObject, IntentStatus, ActionType
from aidm.schemas.engine_result import EngineResult, EngineResultStatus, EngineResultBuilder


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def prepared_store(tmp_path):
    """Create a campaign store with a prepared campaign."""
    store = CampaignStore(tmp_path)
    sz = SessionZeroConfig()

    manifest = store.create_campaign(
        campaign_id=str(uuid.uuid4()),
        session_zero=sz,
        title="Test Campaign",
        created_at=datetime.now(timezone.utc).isoformat(),
        seed=42,
    )

    # Write start_state.json
    campaign_dir = tmp_path / manifest.campaign_id
    start_state = WorldState(ruleset_version="RAW_3.5")
    start_state.entities["pc1"] = {"name": "Hero", "hp": 20, "ac": 15}

    with open(campaign_dir / "start_state.json", "w") as f:
        json.dump(start_state.to_dict(), f, sort_keys=True)

    return store, manifest.campaign_id


@pytest.fixture
def store_with_events(tmp_path):
    """Create a campaign with some events in the log."""
    store = CampaignStore(tmp_path)
    sz = SessionZeroConfig()

    manifest = store.create_campaign(
        campaign_id=str(uuid.uuid4()),
        session_zero=sz,
        title="Campaign With Events",
        created_at=datetime.now(timezone.utc).isoformat(),
        seed=42,
    )

    campaign_dir = tmp_path / manifest.campaign_id

    # Write start_state.json
    start_state = WorldState(ruleset_version="RAW_3.5")
    start_state.entities["pc1"] = {"name": "Hero", "hp": 20, "ac": 15}

    with open(campaign_dir / "start_state.json", "w") as f:
        json.dump(start_state.to_dict(), f, sort_keys=True)

    # Write events.jsonl with 2 complete turns
    event_log = EventLog()
    event_log.append(
        Event(
            event_id=0,
            event_type="turn_start",
            timestamp=1.0,
            payload={"entity_id": "pc1"},
        )
    )
    event_log.append(
        Event(
            event_id=1,
            event_type="hp_changed",
            timestamp=2.0,
            payload={"entity_id": "pc1", "hp_after": 18, "delta": -2},
        )
    )
    event_log.append(
        Event(
            event_id=2,
            event_type="turn_end",
            timestamp=3.0,
            payload={"entity_id": "pc1"},
        )
    )
    event_log.append(
        Event(
            event_id=3,
            event_type="turn_start",
            timestamp=4.0,
            payload={"entity_id": "pc1"},
        )
    )
    event_log.append(
        Event(
            event_id=4,
            event_type="hp_changed",
            timestamp=5.0,
            payload={"entity_id": "pc1", "hp_after": 16, "delta": -2},
        )
    )
    event_log.append(
        Event(
            event_id=5,
            event_type="turn_end",
            timestamp=6.0,
            payload={"entity_id": "pc1"},
        )
    )

    event_log.to_jsonl(campaign_dir / "events.jsonl")

    # Write intents.jsonl with 2 resolved intents
    session_log = CoreSessionLog()
    session_log.master_seed = 42
    session_log.initial_state_hash = start_state.state_hash()

    for i in range(2):
        now = datetime.now(timezone.utc)
        intent = IntentObject(
            intent_id=f"intent-{i}",
            actor_id="pc1",
            source_text="test",
            action_type=ActionType.ATTACK,
            created_at=now,
            updated_at=now,
            status=IntentStatus.RESOLVED,
        )

        builder = EngineResultBuilder(intent_id=intent.intent_id, rng_offset=0)
        result = builder.build(
            result_id=f"result-{i}",
            resolved_at=datetime.now(timezone.utc),
            status=EngineResultStatus.SUCCESS,
        )

        session_log.append(intent, result)

    session_log.to_jsonl(campaign_dir / "intents.jsonl")

    return store, manifest.campaign_id


# =============================================================================
# New Campaign Session Start Tests
# =============================================================================

class TestNewSessionStart:
    """Tests for SessionBootstrap.start_new_session()."""

    def test_start_new_session_empty_logs(self, prepared_store):
        """Should start new session with empty logs."""
        store, campaign_id = prepared_store

        session = SessionBootstrap.start_new_session(store, campaign_id)

        assert session is not None
        assert session.world_state is not None
        assert session.rng is not None
        assert len(session.log) == 0

    def test_start_new_session_loads_initial_state(self, prepared_store):
        """Should load initial WorldState from start_state.json."""
        store, campaign_id = prepared_store

        session = SessionBootstrap.start_new_session(store, campaign_id)

        assert "pc1" in session.world_state.entities
        assert session.world_state.entities["pc1"]["name"] == "Hero"
        assert session.world_state.entities["pc1"]["hp"] == 20

    def test_start_new_session_initializes_rng(self, prepared_store):
        """Should initialize RNG with manifest.master_seed."""
        store, campaign_id = prepared_store

        session = SessionBootstrap.start_new_session(store, campaign_id)

        # Verify RNG is initialized (deterministic stream)
        combat_rng = session.rng.stream("combat")
        roll1 = combat_rng.randint(1, 20)
        roll2 = combat_rng.randint(1, 20)

        # Reset RNG and verify same rolls
        session.rng = session.rng.__class__(42)
        combat_rng_reset = session.rng.stream("combat")
        roll1_again = combat_rng_reset.randint(1, 20)
        roll2_again = combat_rng_reset.randint(1, 20)

        assert roll1 == roll1_again
        assert roll2 == roll2_again

    def test_start_new_session_rejects_non_empty_log(self, store_with_events):
        """Should reject starting new session if event log is not empty."""
        store, campaign_id = store_with_events

        with pytest.raises(BootstrapError, match="event log is not empty"):
            SessionBootstrap.start_new_session(store, campaign_id)

    def test_start_new_session_missing_start_state(self, prepared_store):
        """Should fail if start_state.json is missing."""
        store, campaign_id = prepared_store

        campaign_dir = store.campaign_dir(campaign_id)
        (campaign_dir / "start_state.json").unlink()

        with pytest.raises(BootstrapError, match="Missing start_state.json"):
            SessionBootstrap.start_new_session(store, campaign_id)


# =============================================================================
# Resume Session with Full Replay Tests
# =============================================================================

class TestResumeSession:
    """Tests for SessionBootstrap.resume_from_campaign()."""

    def test_resume_replays_events(self, store_with_events):
        """Should replay all events and reconstruct WorldState."""
        store, campaign_id = store_with_events

        session = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=False
        )

        # After 2 turns with -2 HP each, HP should be 16
        assert session.world_state.entities["pc1"]["hp"] == 16

    def test_resume_deterministic_replay(self, store_with_events):
        """Should produce same state on multiple resume calls."""
        store, campaign_id = store_with_events

        session1 = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=False
        )
        hash1 = session1.world_state.state_hash()

        session2 = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=False
        )
        hash2 = session2.world_state.state_hash()

        assert hash1 == hash2

    def test_resume_with_hash_verification(self, store_with_events):
        """Should run 10× replay verification and pass."""
        store, campaign_id = store_with_events

        # Should not raise (10× replay produces same hash)
        session = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=True
        )

        assert session.world_state.entities["pc1"]["hp"] == 16

    def test_resume_empty_log_succeeds(self, prepared_store):
        """Should resume campaign with empty log (no events yet)."""
        store, campaign_id = prepared_store

        session = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=False
        )

        # State unchanged (no events to replay)
        assert session.world_state.entities["pc1"]["hp"] == 20


# =============================================================================
# Partial Write Recovery Tests
# =============================================================================

class TestPartialWriteRecovery:
    """Tests for partial write recovery (incomplete turn detection)."""

    def test_detect_partial_write_complete_log(self, store_with_events):
        """Should detect no partial write in complete log."""
        store, campaign_id = store_with_events
        _, _, event_log, _ = SessionBootstrap.load_campaign_data(store, campaign_id)

        recovery = SessionBootstrap.detect_partial_write(event_log)

        assert recovery.incomplete_turn_detected is False
        assert recovery.events_discarded == 0
        assert "complete" in recovery.recovery_details.lower()

    def test_detect_partial_write_incomplete_turn(self, tmp_path):
        """Should detect incomplete turn (events after last turn_end)."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = store.create_campaign(
            campaign_id=str(uuid.uuid4()),
            session_zero=sz,
            title="Partial Write Test",
            created_at=datetime.now(timezone.utc).isoformat(),
            seed=42,
        )

        campaign_dir = tmp_path / manifest.campaign_id

        # Write start_state.json
        start_state = WorldState(ruleset_version="RAW_3.5")
        with open(campaign_dir / "start_state.json", "w") as f:
            json.dump(start_state.to_dict(), f, sort_keys=True)

        # Write incomplete turn (turn_start + hp_changed, no turn_end)
        event_log = EventLog()
        event_log.append(
            Event(event_id=0, event_type="turn_start", timestamp=1.0, payload={})
        )
        event_log.append(
            Event(event_id=1, event_type="hp_changed", timestamp=2.0, payload={})
        )
        event_log.to_jsonl(campaign_dir / "events.jsonl")

        # Write empty intents.jsonl
        CoreSessionLog().to_jsonl(campaign_dir / "intents.jsonl")

        # Detect partial write
        _, _, loaded_event_log, _ = SessionBootstrap.load_campaign_data(
            store, manifest.campaign_id
        )
        recovery = SessionBootstrap.detect_partial_write(loaded_event_log)

        assert recovery.incomplete_turn_detected is True
        assert recovery.events_discarded == 2
        assert "no turn_end" in recovery.recovery_details.lower()

    def test_apply_partial_write_recovery(self, tmp_path):
        """Should discard events after last turn_end."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = store.create_campaign(
            campaign_id=str(uuid.uuid4()),
            session_zero=sz,
            title="Recovery Test",
            created_at=datetime.now(timezone.utc).isoformat(),
            seed=42,
        )

        campaign_dir = tmp_path / manifest.campaign_id

        # Write start_state.json
        start_state = WorldState(ruleset_version="RAW_3.5")
        with open(campaign_dir / "start_state.json", "w") as f:
            json.dump(start_state.to_dict(), f, sort_keys=True)

        # Write 1 complete turn + incomplete turn
        event_log = EventLog()
        event_log.append(
            Event(event_id=0, event_type="turn_start", timestamp=1.0, payload={})
        )
        event_log.append(
            Event(event_id=1, event_type="turn_end", timestamp=2.0, payload={})
        )
        event_log.append(
            Event(event_id=2, event_type="turn_start", timestamp=3.0, payload={})
        )
        event_log.append(
            Event(event_id=3, event_type="hp_changed", timestamp=4.0, payload={})
        )
        event_log.to_jsonl(campaign_dir / "events.jsonl")

        # Write empty intents.jsonl
        CoreSessionLog().to_jsonl(campaign_dir / "intents.jsonl")

        # Load and recover
        _, _, loaded_event_log, _ = SessionBootstrap.load_campaign_data(
            store, manifest.campaign_id
        )
        recovery = SessionBootstrap.detect_partial_write(loaded_event_log)
        recovered_log = SessionBootstrap.apply_partial_write_recovery(
            loaded_event_log, recovery
        )

        assert len(recovered_log) == 2  # Only first complete turn
        assert recovered_log[0].event_type == "turn_start"
        assert recovered_log[1].event_type == "turn_end"

    def test_resume_with_partial_write_recovery(self, tmp_path):
        """Should automatically recover from partial write on resume."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = store.create_campaign(
            campaign_id=str(uuid.uuid4()),
            session_zero=sz,
            title="Auto Recovery Test",
            created_at=datetime.now(timezone.utc).isoformat(),
            seed=42,
        )

        campaign_dir = tmp_path / manifest.campaign_id

        # Write start_state.json
        start_state = WorldState(ruleset_version="RAW_3.5")
        start_state.entities["pc1"] = {"hp": 20}
        with open(campaign_dir / "start_state.json", "w") as f:
            json.dump(start_state.to_dict(), f, sort_keys=True)

        # Write 1 complete turn + incomplete turn
        event_log = EventLog()
        event_log.append(
            Event(
                event_id=0,
                event_type="hp_changed",
                timestamp=1.0,
                payload={"entity_id": "pc1", "hp_after": 18},
            )
        )
        event_log.append(
            Event(event_id=1, event_type="turn_end", timestamp=2.0, payload={})
        )
        event_log.append(
            Event(
                event_id=2,
                event_type="hp_changed",
                timestamp=3.0,
                payload={"entity_id": "pc1", "hp_after": 10},
            )
        )  # No turn_end
        event_log.to_jsonl(campaign_dir / "events.jsonl")

        # Write intents.jsonl with 1 resolved intent
        session_log = CoreSessionLog()
        session_log.master_seed = 42
        now = datetime.now(timezone.utc)
        intent = IntentObject(
            intent_id="intent-0",
            actor_id="pc1",
            source_text="test",
            action_type=ActionType.ATTACK,
            created_at=now,
            updated_at=now,
            status=IntentStatus.RESOLVED,
        )
        builder = EngineResultBuilder(intent_id=intent.intent_id, rng_offset=0)
        result = builder.build(
            result_id="result-0",
            resolved_at=datetime.now(timezone.utc),
            status=EngineResultStatus.SUCCESS,
        )
        session_log.append(intent, result)
        session_log.to_jsonl(campaign_dir / "intents.jsonl")

        # Resume should auto-recover
        session = SessionBootstrap.resume_from_campaign(
            store, manifest.campaign_id, verify_hash=False
        )

        # Only first turn applied (hp=18, not hp=10)
        assert session.world_state.entities["pc1"]["hp"] == 18


# =============================================================================
# Log Synchronization Tests
# =============================================================================

class TestLogSync:
    """Tests for log synchronization checks."""

    def test_check_log_sync_in_sync(self, store_with_events):
        """Should detect synchronized logs."""
        store, campaign_id = store_with_events
        _, _, event_log, session_log = SessionBootstrap.load_campaign_data(
            store, campaign_id
        )

        sync_check = SessionBootstrap.check_log_sync(event_log, session_log)

        assert sync_check.in_sync is True
        assert sync_check.event_log_turns == 2
        assert sync_check.session_log_resolved == 2

    def test_check_log_sync_desync_more_events(self, tmp_path):
        """AI turns without intents should NOT cause desync (turn_end >= intents is valid)."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = store.create_campaign(
            campaign_id=str(uuid.uuid4()),
            session_zero=sz,
            title="Desync Test",
            created_at=datetime.now(timezone.utc).isoformat(),
            seed=42,
        )

        campaign_dir = tmp_path / manifest.campaign_id

        # Write start_state.json
        start_state = WorldState(ruleset_version="RAW_3.5")
        with open(campaign_dir / "start_state.json", "w") as f:
            json.dump(start_state.to_dict(), f, sort_keys=True)

        # Write 2 turn_end events (1 AI turn + 1 player turn)
        event_log = EventLog()
        event_log.append(
            Event(event_id=0, event_type="turn_end", timestamp=1.0, payload={})
        )
        event_log.append(
            Event(event_id=1, event_type="turn_end", timestamp=2.0, payload={})
        )
        event_log.to_jsonl(campaign_dir / "events.jsonl")

        # Write only 1 resolved intent (player turn only, AI turn has no intent)
        session_log = CoreSessionLog()
        session_log.master_seed = 42
        now = datetime.now(timezone.utc)
        intent = IntentObject(
            intent_id="intent-0",
            actor_id="pc1",
            source_text="test",
            action_type=ActionType.ATTACK,
            created_at=now,
            updated_at=now,
            status=IntentStatus.RESOLVED,
        )
        builder = EngineResultBuilder(intent_id=intent.intent_id, rng_offset=0)
        result = builder.build(
            result_id="result-0",
            resolved_at=datetime.now(timezone.utc),
            status=EngineResultStatus.SUCCESS,
        )
        session_log.append(intent, result)
        session_log.to_jsonl(campaign_dir / "intents.jsonl")

        # Check sync
        _, _, loaded_event_log, loaded_session_log = SessionBootstrap.load_campaign_data(
            store, manifest.campaign_id
        )
        sync_check = SessionBootstrap.check_log_sync(
            loaded_event_log, loaded_session_log
        )

        # Should PASS (turn_end >= intents is valid for AI turns)
        assert sync_check.in_sync is True
        assert sync_check.event_log_turns == 2
        assert sync_check.session_log_resolved == 1

    def test_resume_fails_on_log_desync(self, tmp_path):
        """Should fail hard on log desync during resume (more intents than turn_ends)."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = store.create_campaign(
            campaign_id=str(uuid.uuid4()),
            session_zero=sz,
            title="Fail on Desync",
            created_at=datetime.now(timezone.utc).isoformat(),
            seed=42,
        )

        campaign_dir = tmp_path / manifest.campaign_id

        # Write start_state.json
        start_state = WorldState(ruleset_version="RAW_3.5")
        with open(campaign_dir / "start_state.json", "w") as f:
            json.dump(start_state.to_dict(), f, sort_keys=True)

        # Write 1 turn_end
        event_log = EventLog()
        event_log.append(
            Event(event_id=0, event_type="turn_end", timestamp=1.0, payload={})
        )
        event_log.to_jsonl(campaign_dir / "events.jsonl")

        # Write 2 resolved intents (more intents than turn_ends — desync!)
        session_log = CoreSessionLog()
        session_log.master_seed = 42
        now = datetime.now(timezone.utc)

        for i in range(2):
            intent = IntentObject(
                intent_id=f"intent-{i}",
                actor_id="pc1",
                source_text="test",
                action_type=ActionType.ATTACK,
                created_at=now,
                updated_at=now,
                status=IntentStatus.RESOLVED,
            )
            builder = EngineResultBuilder(intent_id=intent.intent_id, rng_offset=0)
            result = builder.build(
                result_id=f"result-{i}",
                resolved_at=datetime.now(timezone.utc),
                status=EngineResultStatus.SUCCESS,
            )
            session_log.append(intent, result)

        session_log.to_jsonl(campaign_dir / "intents.jsonl")

        # Resume should fail (2 intents > 1 turn_end)
        with pytest.raises(BootstrapError, match="desynchronization"):
            SessionBootstrap.resume_from_campaign(store, manifest.campaign_id)


# =============================================================================
# Corruption and Error Handling Tests
# =============================================================================

class TestCorruptionHandling:
    """Tests for corruption detection and fail-fast behavior."""

    def test_corrupt_manifest_fails(self, tmp_path):
        """Should fail if manifest.json is corrupt."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = store.create_campaign(
            campaign_id=str(uuid.uuid4()),
            session_zero=sz,
            title="Corrupt Manifest",
            created_at=datetime.now(timezone.utc).isoformat(),
            seed=42,
        )

        campaign_dir = tmp_path / manifest.campaign_id

        # Corrupt manifest
        (campaign_dir / "manifest.json").write_text("not valid json{{{")

        with pytest.raises(BootstrapError):
            SessionBootstrap.load_campaign_data(store, manifest.campaign_id)

    def test_corrupt_event_log_fails(self, tmp_path):
        """Should fail if events.jsonl is corrupt."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = store.create_campaign(
            campaign_id=str(uuid.uuid4()),
            session_zero=sz,
            title="Corrupt Events",
            created_at=datetime.now(timezone.utc).isoformat(),
            seed=42,
        )

        campaign_dir = tmp_path / manifest.campaign_id

        # Write start_state.json
        start_state = WorldState(ruleset_version="RAW_3.5")
        with open(campaign_dir / "start_state.json", "w") as f:
            json.dump(start_state.to_dict(), f, sort_keys=True)

        # Corrupt event log
        (campaign_dir / "events.jsonl").write_text("invalid json\n")

        with pytest.raises(BootstrapError, match="Failed to load event log"):
            SessionBootstrap.load_campaign_data(store, manifest.campaign_id)

    def test_missing_campaign_fails(self, tmp_path):
        """Should fail if campaign does not exist."""
        store = CampaignStore(tmp_path)

        with pytest.raises(BootstrapError, match="Failed to load campaign manifest"):
            SessionBootstrap.load_campaign_data(store, "nonexistent-campaign-id")
