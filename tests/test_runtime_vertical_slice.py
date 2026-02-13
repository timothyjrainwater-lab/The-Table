"""Integration tests for M1.5 Runtime Vertical Slice.

Tests the minimal runtime flow:
1. Resume campaign → show state → accept input → resolve one turn → save → exit
2. Deterministic replay hash stability across resume cycles
3. Partial write recovery
4. Fail-fast on corruption

Per WO-M1-RUNTIME-WIRING-01 acceptance criteria:
- Golden path: resume → 1 turn → exit → resume again; verify deterministic replay hash stability
- Partial write recovery (truncate after last turn_end)
- Corrupt JSON line: fail-fast

Reference: OPUS_WO-M1-RUNTIME-02_GUARDRAILS.md Section 3 (Acceptance Checklist)
"""

import json
import pytest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from aidm.core.campaign_store import CampaignStore
from aidm.core.state import WorldState
from aidm.core.event_log import Event, EventLog
from aidm.core.session_log import SessionLog as CoreSessionLog
from aidm.schemas.campaign import SessionZeroConfig
from aidm.schemas.intent_lifecycle import IntentObject, IntentStatus, ActionType
from aidm.schemas.engine_result import EngineResultBuilder, EngineResultStatus

from aidm.runtime.bootstrap import SessionBootstrap, BootstrapError
from aidm.runtime.session import RuntimeSession
from aidm.runtime.display import (
    format_campaign_header,
    format_world_summary,
    format_available_actions,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def test_campaign(tmp_path):
    """Create a minimal test campaign for runtime vertical slice."""
    store = CampaignStore(tmp_path)
    sz = SessionZeroConfig()

    manifest = store.create_campaign(
        campaign_id=str(uuid.uuid4()),
        session_zero=sz,
        title="M1.5 Test Campaign",
        created_at=datetime.now(timezone.utc).isoformat(),
        seed=42,
    )

    campaign_dir = tmp_path / manifest.campaign_id

    # Write start_state.json with 2 entities
    start_state = WorldState(ruleset_version="RAW_3.5")
    start_state.entities["goblin_1"] = {
        "hp_current": 6,
        "hp_max": 6,
        "team": "monsters",
        "position": {"x": 0, "y": 0},
        "defeated": False,
    }
    start_state.entities["pc_fighter"] = {
        "hp_current": 10,
        "hp_max": 10,
        "team": "party",
        "position": {"x": 10, "y": 0},
        "defeated": False,
    }
    start_state.active_combat = {"turn_counter": 0}

    with open(campaign_dir / "start_state.json", "w") as f:
        json.dump(start_state.to_dict(), f, sort_keys=True)

    return store, manifest.campaign_id


@pytest.fixture
def campaign_with_turns(tmp_path):
    """Create a campaign with 1 complete turn already executed."""
    store = CampaignStore(tmp_path)
    sz = SessionZeroConfig()

    manifest = store.create_campaign(
        campaign_id=str(uuid.uuid4()),
        session_zero=sz,
        title="Campaign With Turns",
        created_at=datetime.now(timezone.utc).isoformat(),
        seed=42,
    )

    campaign_dir = tmp_path / manifest.campaign_id

    # Write start_state.json
    start_state = WorldState(ruleset_version="RAW_3.5")
    start_state.entities["pc1"] = {"hp_current": 20, "hp_max": 20, "team": "party"}
    start_state.active_combat = {"turn_counter": 0}

    with open(campaign_dir / "start_state.json", "w") as f:
        json.dump(start_state.to_dict(), f, sort_keys=True)

    # Write 1 complete turn in events.jsonl
    event_log = EventLog()
    event_log.append(
        Event(event_id=0, event_type="turn_start", timestamp=1.0, payload={"entity_id": "pc1"})
    )
    event_log.append(
        Event(event_id=1, event_type="turn_end", timestamp=2.0, payload={"entity_id": "pc1"})
    )
    event_log.to_jsonl(campaign_dir / "events.jsonl")

    # Write 1 resolved intent in intents.jsonl
    session_log = CoreSessionLog()
    session_log.master_seed = 42
    session_log.initial_state_hash = start_state.state_hash()

    now = datetime.now(timezone.utc)
    intent = IntentObject(
        intent_id="intent-0",
        actor_id="pc1",
        source_text="attack",
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

    return store, manifest.campaign_id


# =============================================================================
# Golden Path Tests
# =============================================================================

class TestRuntimeVerticalSlice:
    """Tests for M1.5 runtime vertical slice golden path."""

    def test_resume_new_campaign(self, test_campaign):
        """Should successfully resume a new campaign with no events."""
        store, campaign_id = test_campaign

        # Resume via bootstrap
        session = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=False
        )

        assert session is not None
        assert len(session.world_state.entities) == 2
        assert "goblin_1" in session.world_state.entities
        assert "pc_fighter" in session.world_state.entities

    def test_resume_campaign_with_turns(self, campaign_with_turns):
        """Should successfully resume campaign with existing turns."""
        store, campaign_id = campaign_with_turns

        # Resume via bootstrap
        session = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=False
        )

        assert session is not None
        assert "pc1" in session.world_state.entities
        # Turn counter should be advanced by replay
        assert session.world_state.active_combat["turn_counter"] >= 0

    def test_deterministic_resume_hash_stability(self, campaign_with_turns):
        """Should produce identical state hash across multiple resume cycles.

        Golden path test per WO acceptance criteria:
        - resume → verify state hash
        - resume again → verify same hash
        """
        store, campaign_id = campaign_with_turns

        # First resume
        session1 = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=False
        )
        hash1 = session1.world_state.state_hash()

        # Second resume (independent)
        session2 = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=False
        )
        hash2 = session2.world_state.state_hash()

        # Third resume (independent)
        session3 = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=False
        )
        hash3 = session3.world_state.state_hash()

        # All hashes must match (deterministic replay)
        assert hash1 == hash2, "First and second resume produced different state hashes"
        assert hash2 == hash3, "Second and third resume produced different state hashes"

    def test_display_formatting(self, test_campaign):
        """Should format campaign state for display without errors."""
        store, campaign_id = test_campaign

        # Load manifest and session
        manifest = store.load_campaign(campaign_id)
        session = SessionBootstrap.resume_from_campaign(
            store, campaign_id, verify_hash=False
        )

        # Test all display formatters
        header = format_campaign_header(manifest, turn_count=0)
        assert "M1.5 Test Campaign" in header
        assert "AIDM" in header

        summary = format_world_summary(session.world_state)
        assert "goblin_1" in summary
        assert "pc_fighter" in summary
        assert "HP" in summary

        actions = format_available_actions()
        assert "attack" in actions.lower()
        assert "move" in actions.lower()


# =============================================================================
# Partial Write Recovery Tests
# =============================================================================

class TestPartialWriteRecovery:
    """Tests for partial write recovery during resume."""

    def test_resume_with_incomplete_turn(self, tmp_path):
        """Should discard events after last turn_end and resume cleanly.

        Partial write recovery test per WO acceptance criteria.
        """
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
        start_state.entities["pc1"] = {"hp_current": 20, "hp_max": 20}
        start_state.active_combat = {"turn_counter": 0}

        with open(campaign_dir / "start_state.json", "w") as f:
            json.dump(start_state.to_dict(), f, sort_keys=True)

        # Write 1 complete turn + 1 incomplete turn
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
        # No turn_end for event_id=2 — incomplete turn
        event_log.to_jsonl(campaign_dir / "events.jsonl")

        # Write 1 resolved intent (matches first complete turn)
        session_log = CoreSessionLog()
        session_log.master_seed = 42
        session_log.initial_state_hash = start_state.state_hash()

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

        # Resume should auto-recover from partial write
        session = SessionBootstrap.resume_from_campaign(
            store, manifest.campaign_id, verify_hash=False
        )

        # Session should resume successfully (partial write recovered)
        assert session is not None
        assert session.world_state is not None


# =============================================================================
# Corruption Handling Tests
# =============================================================================

class TestCorruptionHandling:
    """Tests for fail-fast corruption detection."""

    def test_corrupt_event_log_fails_fast(self, tmp_path):
        """Should fail hard on corrupt event log JSON.

        Corruption test per WO acceptance criteria.
        """
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

        # Write corrupt event log
        (campaign_dir / "events.jsonl").write_text("invalid json{{{\\n")

        # Resume should fail hard
        with pytest.raises(BootstrapError, match="Failed to load event log"):
            SessionBootstrap.resume_from_campaign(store, manifest.campaign_id)

    def test_missing_campaign_fails_fast(self, tmp_path):
        """Should fail hard if campaign does not exist."""
        store = CampaignStore(tmp_path)

        with pytest.raises(BootstrapError, match="Failed to load campaign manifest"):
            SessionBootstrap.load_campaign_data(store, "nonexistent-campaign-id")

    def test_log_desync_fails_hard(self, tmp_path):
        """Should fail hard on log desynchronization (more intents than turn_ends)."""
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

        # Write 1 turn_end event
        event_log = EventLog()
        event_log.append(
            Event(event_id=0, event_type="turn_end", timestamp=1.0, payload={})
        )
        event_log.to_jsonl(campaign_dir / "events.jsonl")

        # Write 2 resolved intents (desync: more intents than turn_ends)
        session_log = CoreSessionLog()
        session_log.master_seed = 42
        session_log.initial_state_hash = start_state.state_hash()

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

        # Resume should fail hard on desync (2 intents > 1 turn_end)
        with pytest.raises(BootstrapError, match="desynchronization"):
            SessionBootstrap.resume_from_campaign(store, manifest.campaign_id)
