"""Gate C tests — Cold Boot Byte-Equality + Compaction Reproducibility + Pin Assertion.

Oracle Phase 3: 22+ tests across 6 categories.

Categories:
    1. Cold boot byte-equality (6 tests)
    2. Compaction reproducibility (6 tests)
    3. CompactionRegistry (5 tests)
    4. Pin assertion (3 tests)
    5. SaveSnapshot integrity (2 tests)
    6. Oracle reducer (2 tests)

Authority: WO-ORACLE-03 dispatch, Session Lifecycle Spec v0, GT v12.
"""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from aidm.core.event_log import Event, EventLog
from aidm.oracle.canonical import canonical_json, canonical_short_hash
from aidm.oracle.facts_ledger import Fact, FactsLedger, make_fact
from aidm.oracle.unlock_state import UnlockEntry, UnlockState
from aidm.oracle.story_state import StoryState, StoryStateLog
from aidm.oracle.working_set import (
    CompilationPolicy,
    ScopeCursor,
    WorkingSet,
    compile_working_set,
)
from aidm.oracle.save_snapshot import SaveSnapshot, create_snapshot
from aidm.oracle.compaction import (
    Compaction,
    CompactionRegistry,
    make_compaction,
)
from aidm.oracle.cold_boot import (
    ColdBootDigestMismatchError,
    ColdBootEventLogCorruptionError,
    ColdBootPinMismatchError,
    cold_boot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _default_pins():
    return {
        "hash_algorithm": "sha256",
        "short_hash_length": 16,
        "canonical_profile": "oracle_v0",
    }


def _build_event_log_with_oracle_events():
    """Build an EventLog with Oracle-specific events for cold boot testing."""
    log = EventLog()

    # Event 0: Initialize story state.
    log.append(Event(
        event_id=0,
        event_type="oracle_story_init",
        timestamp=0,
        payload={
            "campaign_id": "test_campaign",
            "world_id": "test_world",
            "mode": "EXPLORATION",
        },
    ))

    # Event 1: Create a fact.
    fact_payload = {"rule": "test_rule_0", "index": 0}
    fact_id = canonical_short_hash(fact_payload)
    log.append(Event(
        event_id=1,
        event_type="oracle_fact_created",
        timestamp=0,
        payload={
            "fact_id": fact_id,
            "kind": "WORLD_RULE",
            "payload": fact_payload,
            "provenance": {"source": "test"},
            "visibility_mask": "PUBLIC",
            "precision_tag": "UNLOCKED",
            "stable_key": f"WORLD_RULE:{fact_id[:8]}",
        },
    ))

    # Event 2: Unlock the fact.
    log.append(Event(
        event_id=2,
        event_type="oracle_unlock",
        timestamp=0,
        payload={
            "handle": fact_id,
            "scope": "SESSION",
            "source": "SYSTEM",
        },
    ))

    # Event 3: Create another fact.
    fact_payload_2 = {"rule": "test_rule_1", "index": 1}
    fact_id_2 = canonical_short_hash(fact_payload_2)
    log.append(Event(
        event_id=3,
        event_type="oracle_fact_created",
        timestamp=0,
        payload={
            "fact_id": fact_id_2,
            "kind": "WORLD_RULE",
            "payload": fact_payload_2,
            "provenance": {"source": "test"},
            "visibility_mask": "PUBLIC",
            "precision_tag": "UNLOCKED",
            "stable_key": f"WORLD_RULE:{fact_id_2[:8]}",
        },
    ))

    # Event 4: Unlock second fact.
    log.append(Event(
        event_id=4,
        event_type="oracle_unlock",
        timestamp=0,
        payload={
            "handle": fact_id_2,
            "scope": "SESSION",
            "source": "SYSTEM",
        },
    ))

    # Event 5: Start a scene.
    log.append(Event(
        event_id=5,
        event_type="scene_start",
        timestamp=0,
        payload={"scene_id": "scene_001"},
    ))

    return log


def _build_stores_from_event_log(event_log):
    """Replay an event log through the Oracle reducer to build stores."""
    from aidm.oracle.cold_boot import _reduce_oracle_event

    facts_ledger = FactsLedger()
    unlock_state = UnlockState()
    story_state_log = None

    for event in event_log.events:
        story_state_log = _reduce_oracle_event(
            facts_ledger, unlock_state, story_state_log, event
        )

    if story_state_log is None:
        story_state_log = StoryStateLog(StoryState(campaign_id="default"))

    return facts_ledger, unlock_state, story_state_log


def _build_working_set(facts_ledger, unlock_state, story_state_log):
    """Compile a WorkingSet from Oracle stores."""
    story = story_state_log.current()
    return compile_working_set(
        facts_ledger=facts_ledger,
        unlock_state=unlock_state,
        story_state_log=story_state_log,
        policy=CompilationPolicy(),
        scope_cursor=ScopeCursor(
            campaign_id=story.campaign_id,
            scene_id=story.scene_id,
            world_id=story.world_id,
        ),
    )


def _build_full_snapshot():
    """Build a complete snapshot for cold boot testing."""
    event_log = _build_event_log_with_oracle_events()
    fl, us, ssl = _build_stores_from_event_log(event_log)
    ws = _build_working_set(fl, us, ssl)
    registry = CompactionRegistry()
    pins = _default_pins()

    snapshot = create_snapshot(
        facts_ledger=fl,
        unlock_state=us,
        story_state_log=ssl,
        working_set=ws,
        event_log=event_log,
        event_range=(0, len(event_log) - 1),
        pins=pins,
        compaction_registry=registry,
        save_type="SESSION",
    )
    return snapshot, event_log, fl, us, ssl, ws, registry, pins


# ---------------------------------------------------------------------------
# 1. Cold Boot Byte-Equality (6 tests)
# ---------------------------------------------------------------------------

class TestColdBoot:
    def test_cold_boot_roundtrip(self):
        """Create stores, save snapshot, cold boot, assert all digests match."""
        snapshot, event_log, fl, us, ssl, ws, _, pins = _build_full_snapshot()

        fl2, us2, ssl2, ws2 = cold_boot(snapshot, event_log, pins)

        assert fl2.digest() == fl.digest()
        assert us2.digest() == us.digest()
        assert ssl2.digest() == ssl.digest()
        assert ws2.bytes_hash == ws.bytes_hash

    def test_cold_boot_after_events(self):
        """Append events, save, cold boot, assert state identical."""
        event_log = _build_event_log_with_oracle_events()

        # Add more events.
        fact_payload_3 = {"rule": "test_rule_2", "index": 2}
        fact_id_3 = canonical_short_hash(fact_payload_3)
        event_log.append(Event(
            event_id=6,
            event_type="oracle_fact_created",
            timestamp=0,
            payload={
                "fact_id": fact_id_3,
                "kind": "WORLD_RULE",
                "payload": fact_payload_3,
                "provenance": {"source": "test"},
                "visibility_mask": "PUBLIC",
                "precision_tag": "UNLOCKED",
                "stable_key": f"WORLD_RULE:{fact_id_3[:8]}",
            },
        ))
        event_log.append(Event(
            event_id=7,
            event_type="oracle_unlock",
            timestamp=0,
            payload={"handle": fact_id_3, "scope": "SESSION", "source": "SYSTEM"},
        ))

        fl, us, ssl = _build_stores_from_event_log(event_log)
        ws = _build_working_set(fl, us, ssl)
        registry = CompactionRegistry()
        pins = _default_pins()

        snapshot = create_snapshot(
            fl, us, ssl, ws, event_log,
            event_range=(0, 7), pins=pins,
            compaction_registry=registry,
        )

        fl2, us2, ssl2, ws2 = cold_boot(snapshot, event_log, pins)
        assert fl2.digest() == fl.digest()
        assert us2.digest() == us.digest()
        assert ssl2.digest() == ssl.digest()
        assert ws2.bytes_hash == ws.bytes_hash

    def test_cold_boot_working_set_digest(self):
        """Cold boot reconstructs WorkingSet with matching digest."""
        snapshot, event_log, _, _, _, ws, _, pins = _build_full_snapshot()
        _, _, _, ws2 = cold_boot(snapshot, event_log, pins)
        assert ws2.bytes_hash == snapshot.working_set_digest

    def test_cold_boot_10x(self):
        """Cold boot 10 times, all produce identical digests."""
        snapshot, event_log, _, _, _, _, _, pins = _build_full_snapshot()

        digests = set()
        for _ in range(10):
            fl, us, ssl, ws = cold_boot(snapshot, event_log, pins)
            digests.add((fl.digest(), us.digest(), ssl.digest(), ws.bytes_hash))

        assert len(digests) == 1, f"Expected 1 unique digest set, got {len(digests)}"

    def test_cold_boot_fails_on_corrupted_event_log(self):
        """Tamper with event, assert HARD FAIL."""
        snapshot, event_log, _, _, _, _, _, pins = _build_full_snapshot()

        # Tamper: modify an event payload.
        tampered_log = EventLog()
        for event in event_log.events:
            if event.event_id == 1:
                tampered_payload = dict(event.payload)
                tampered_payload["payload"] = {"rule": "TAMPERED", "index": 999}
                tampered_event = Event(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    timestamp=event.timestamp,
                    payload=tampered_payload,
                    rng_offset=event.rng_offset,
                )
                tampered_log.append(tampered_event)
            else:
                tampered_log.append(event)

        with pytest.raises(ColdBootEventLogCorruptionError):
            cold_boot(snapshot, tampered_log, pins)

    def test_cold_boot_fails_on_digest_mismatch(self):
        """Modify a fact post-snapshot by replaying with extra event, assert HARD FAIL."""
        snapshot, event_log, _, _, _, _, _, pins = _build_full_snapshot()

        # Add an extra event AFTER snapshot range — but lie about the range.
        extra_payload = {"rule": "extra_rule", "index": 99}
        extra_id = canonical_short_hash(extra_payload)
        event_log.append(Event(
            event_id=6,
            event_type="oracle_fact_created",
            timestamp=0,
            payload={
                "fact_id": extra_id,
                "kind": "WORLD_RULE",
                "payload": extra_payload,
                "provenance": {"source": "test"},
                "visibility_mask": "PUBLIC",
                "precision_tag": "UNLOCKED",
                "stable_key": f"WORLD_RULE:{extra_id[:8]}",
            },
        ))

        # Create a manipulated snapshot with wider range but old digests.
        pre_hash = {
            "save_type": "SESSION",
            "timestamp_event_id": 6,
            "facts_ledger_digest": snapshot.facts_ledger_digest,
            "unlock_state_digest": snapshot.unlock_state_digest,
            "story_state_digest": snapshot.story_state_digest,
            "working_set_digest": snapshot.working_set_digest,
            "event_log_range": [0, 6],
            "event_log_hash": _compute_test_event_log_hash(event_log, (0, 6)),
            "pending_state": None,
            "pins_snapshot": dict(snapshot.pins_snapshot),
            "compaction_ids": [],
        }

        from aidm.oracle.canonical import canonical_json as cj
        from aidm.oracle.canonical import canonical_short_hash as csh

        cb = cj(pre_hash)
        bh = hashlib.sha256(cb).hexdigest()

        bad_snapshot = SaveSnapshot(
            snapshot_id=csh(pre_hash),
            save_type="SESSION",
            timestamp_event_id=6,
            facts_ledger_digest=snapshot.facts_ledger_digest,
            unlock_state_digest=snapshot.unlock_state_digest,
            story_state_digest=snapshot.story_state_digest,
            working_set_digest=snapshot.working_set_digest,
            event_log_range=(0, 6),
            event_log_hash=pre_hash["event_log_hash"],
            pending_state=None,
            pins_snapshot=dict(snapshot.pins_snapshot),
            compaction_ids=(),
            canonical_bytes=cb,
            bytes_hash=bh,
        )

        with pytest.raises(ColdBootDigestMismatchError) as exc_info:
            cold_boot(bad_snapshot, event_log, pins)
        assert exc_info.value.store_name == "facts_ledger"


def _compute_test_event_log_hash(event_log, event_range):
    """Test helper: compute event log hash."""
    start_id, end_id = event_range
    lines = []
    for event in event_log.events:
        if start_id <= event.event_id <= end_id:
            lines.append(json.dumps(event.to_dict(), sort_keys=True))
    jsonl_bytes = ("\n".join(lines) + "\n").encode("utf-8") if lines else b""
    return hashlib.sha256(jsonl_bytes).hexdigest()


# ---------------------------------------------------------------------------
# 2. Compaction Reproducibility (6 tests)
# ---------------------------------------------------------------------------

class TestCompactionReproducibility:
    def _build_test_facts(self):
        facts = []
        for i in range(3):
            facts.append(make_fact(
                kind="WORLD_RULE",
                payload={"rule": f"test_rule_{i}", "index": i},
                provenance={"source": "test"},
                created_event_id=i,
                visibility_mask="PUBLIC",
                precision_tag="UNLOCKED",
            ))
        return facts

    def test_compaction_deterministic(self):
        """Same inputs + policy → identical output_bytes."""
        facts = self._build_test_facts()
        handles = tuple(f.fact_id for f in facts)

        c1 = make_compaction("RECAP", "template_v1", handles, facts)
        c2 = make_compaction("RECAP", "template_v1", handles, facts)

        assert c1.output_bytes == c2.output_bytes
        assert c1.output_hash == c2.output_hash
        assert c1.compaction_id == c2.compaction_id

    def test_compaction_deterministic_10x(self):
        """10 generations, all identical."""
        facts = self._build_test_facts()
        handles = tuple(f.fact_id for f in facts)

        hashes = set()
        for _ in range(10):
            c = make_compaction("RECAP", "template_v1", handles, facts)
            hashes.add(c.output_hash)

        assert len(hashes) == 1

    def test_compaction_rebuild_matches_original(self):
        """Register, invalidate, rebuild — assert output_hash matches."""
        facts = self._build_test_facts()
        handles = tuple(f.fact_id for f in facts)

        original = make_compaction("RECAP", "template_v1", handles, facts)
        registry = CompactionRegistry()
        registry.register(original)

        # Invalidate.
        registry.invalidate([facts[0].fact_id])

        # Rebuild with same facts.
        rebuilt = registry.rebuild(
            original.compaction_id, facts, "template_v1"
        )
        assert rebuilt.output_hash == original.output_hash

    def test_compaction_delete_rebuild_identical(self):
        """Delete all, rebuild all — assert all output_hashes match."""
        facts = self._build_test_facts()
        handles = tuple(f.fact_id for f in facts)

        c1 = make_compaction("RECAP", "template_v1", handles, facts)
        original_hash = c1.output_hash
        original_id = c1.compaction_id

        # Fresh registry, rebuild from scratch.
        c2 = make_compaction("RECAP", "template_v1", handles, facts)
        assert c2.output_hash == original_hash
        assert c2.compaction_id == original_id

    def test_compaction_no_canon_writes(self):
        """Assert compaction creation does not modify FactsLedger."""
        ledger = FactsLedger()
        facts = self._build_test_facts()
        for f in facts:
            ledger.append(f)

        digest_before = ledger.digest()
        handles = tuple(f.fact_id for f in facts)
        _ = make_compaction("RECAP", "template_v1", handles, facts)
        digest_after = ledger.digest()

        assert digest_before == digest_after

    def test_compaction_no_canon_writes_on_rebuild(self):
        """Assert rebuild does not modify FactsLedger."""
        ledger = FactsLedger()
        facts = self._build_test_facts()
        for f in facts:
            ledger.append(f)

        handles = tuple(f.fact_id for f in facts)
        original = make_compaction("RECAP", "template_v1", handles, facts)

        registry = CompactionRegistry()
        registry.register(original)

        digest_before = ledger.digest()
        registry.rebuild(original.compaction_id, facts, "template_v1")
        digest_after = ledger.digest()

        assert digest_before == digest_after


# ---------------------------------------------------------------------------
# 3. CompactionRegistry (5 tests)
# ---------------------------------------------------------------------------

class TestCompactionRegistry:
    def _make_test_compaction(self, index=0):
        facts = [make_fact(
            kind="WORLD_RULE",
            payload={"rule": f"reg_test_{index}", "index": index},
            provenance={"source": "test"},
            created_event_id=index,
            visibility_mask="PUBLIC",
            precision_tag="UNLOCKED",
        )]
        handles = tuple(f.fact_id for f in facts)
        return make_compaction(
            "RECAP", f"policy_{index}", handles, facts
        ), facts

    def test_registry_register_and_get(self):
        """Basic CRUD."""
        registry = CompactionRegistry()
        compaction, _ = self._make_test_compaction(0)
        registry.register(compaction)

        assert registry.get(compaction.compaction_id) is compaction
        assert len(registry) == 1
        assert len(registry.all_compactions()) == 1

    def test_registry_invalidate_on_source_change(self):
        """Change source fact → compaction marked stale."""
        compaction, facts = self._make_test_compaction(0)
        registry = CompactionRegistry()
        registry.register(compaction)

        assert compaction.compaction_id in registry.active_ids()

        # Invalidate using the fact_id.
        invalidated = registry.invalidate([facts[0].fact_id])
        assert compaction.compaction_id in invalidated
        assert compaction.compaction_id not in registry.active_ids()

    def test_registry_verify_all_passes(self):
        """All compactions valid → verify returns all True."""
        registry = CompactionRegistry()
        c1, _ = self._make_test_compaction(0)
        c2, _ = self._make_test_compaction(1)
        registry.register(c1)
        registry.register(c2)

        results = registry.verify_all()
        assert all(valid for _, valid in results)

    def test_registry_verify_detects_corruption(self):
        """Tamper with output_bytes → verify returns False."""
        compaction, _ = self._make_test_compaction(0)
        registry = CompactionRegistry()
        registry.register(compaction)

        # Tamper: replace compaction with corrupted output_bytes.
        corrupted = Compaction(
            compaction_id=compaction.compaction_id,
            purpose=compaction.purpose,
            compaction_policy_id=compaction.compaction_policy_id,
            input_handles=compaction.input_handles,
            output_bytes=b"CORRUPTED",
            output_hash=compaction.output_hash,  # hash no longer matches
            allowmention_handles=compaction.allowmention_handles,
        )
        registry._compactions[compaction.compaction_id] = corrupted

        results = registry.verify_all()
        assert any(not valid for _, valid in results)

    def test_registry_rejects_duplicate_id(self):
        """Register same ID twice → ValueError."""
        compaction, _ = self._make_test_compaction(0)
        registry = CompactionRegistry()
        registry.register(compaction)

        with pytest.raises(ValueError, match="Duplicate"):
            registry.register(compaction)


# ---------------------------------------------------------------------------
# 4. Pin Assertion (3 tests)
# ---------------------------------------------------------------------------

class TestPinAssertion:
    def test_pin_assertion_passes_matching_pins(self):
        """Cold boot with matching pins succeeds."""
        snapshot, event_log, _, _, _, _, _, pins = _build_full_snapshot()
        # Should not raise.
        fl, us, ssl, ws = cold_boot(snapshot, event_log, pins)
        assert fl.digest() == snapshot.facts_ledger_digest

    def test_pin_assertion_fails_on_mismatch(self):
        """Cold boot with different pins → HARD FAIL."""
        snapshot, event_log, _, _, _, _, _, pins = _build_full_snapshot()

        wrong_pins = dict(pins)
        wrong_pins["hash_algorithm"] = "md5"  # mismatch

        with pytest.raises(ColdBootPinMismatchError):
            cold_boot(snapshot, event_log, wrong_pins)

    def test_pin_assertion_fails_deterministically(self):
        """Error message includes which pin mismatched."""
        snapshot, event_log, _, _, _, _, _, pins = _build_full_snapshot()

        wrong_pins = dict(pins)
        wrong_pins["short_hash_length"] = 32

        with pytest.raises(ColdBootPinMismatchError) as exc_info:
            cold_boot(snapshot, event_log, wrong_pins)

        assert exc_info.value.mismatched_pin == "short_hash_length"
        assert exc_info.value.expected_value == 16
        assert exc_info.value.actual_value == 32


# ---------------------------------------------------------------------------
# 5. SaveSnapshot Integrity (2 tests)
# ---------------------------------------------------------------------------

class TestSaveSnapshotIntegrity:
    def test_snapshot_frozen(self):
        """All container fields frozen (tuple/MappingProxyType)."""
        snapshot, *_ = _build_full_snapshot()

        # pins_snapshot should be MappingProxyType.
        with pytest.raises(TypeError):
            snapshot.pins_snapshot["new_key"] = "value"

        # compaction_ids should be tuple.
        assert isinstance(snapshot.compaction_ids, tuple)

        # event_log_range should be tuple.
        assert isinstance(snapshot.event_log_range, tuple)

        # Frozen dataclass — attribute assignment should fail.
        with pytest.raises(AttributeError):
            snapshot.save_type = "CAMPAIGN"

    def test_snapshot_canonical_json_no_floats(self):
        """Float injection raises TypeError."""
        from aidm.oracle.canonical import canonical_json

        with pytest.raises(TypeError, match="[Ff]loat"):
            canonical_json({"pins_snapshot": {"bad_float": 3.14}})


# ---------------------------------------------------------------------------
# 6. Oracle Reducer (2 tests)
# ---------------------------------------------------------------------------

class TestOracleReducer:
    def test_reducer_builds_correct_stores(self):
        """Replay events through reducer produces expected store state."""
        event_log = _build_event_log_with_oracle_events()
        fl, us, ssl = _build_stores_from_event_log(event_log)

        # Should have 2 facts.
        assert len(fl) == 2
        # Should have 2 unlocks.
        assert len(us) == 2
        # Should have scene_id set.
        assert ssl.current().scene_id == "scene_001"
        assert ssl.current().campaign_id == "test_campaign"

    def test_reducer_ignores_unknown_events(self):
        """Unknown event types do not crash or mutate stores."""
        log = EventLog()
        log.append(Event(
            event_id=0,
            event_type="oracle_story_init",
            timestamp=0,
            payload={"campaign_id": "test"},
        ))
        log.append(Event(
            event_id=1,
            event_type="totally_unknown_event",
            timestamp=0,
            payload={"irrelevant": "data"},
        ))

        fl, us, ssl = _build_stores_from_event_log(log)
        assert len(fl) == 0
        assert len(us) == 0
        assert ssl.current().campaign_id == "test"
