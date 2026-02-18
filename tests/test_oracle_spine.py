"""Gate A tests — Oracle spine store determinism.

15 required test cases proving same inputs -> same canonical bytes
across all Oracle stores.

Authority: WO-ORACLE-01 Change 5, Oracle Memo v5.2 section 6.
"""
from __future__ import annotations

import random
import pytest
from pathlib import Path

from aidm.oracle.canonical import (
    canonical_json,
    canonical_hash,
    canonical_short_hash,
)
from aidm.oracle.facts_ledger import Fact, FactsLedger, make_fact
from aidm.oracle.unlock_state import UnlockEntry, UnlockState
from aidm.oracle.story_state import StoryState, StoryStateLog


# ── Canonical JSON profile ────────────────────────────────────────────


class TestCanonicalJson:
    """Tests 1-3: canonical_json determinism and float rejection."""

    def test_canonical_json_deterministic(self):
        """Test 1: Same input -> byte-identical output, 10 iterations."""
        obj = {"z": 1, "a": [3, 2, 1], "m": {"b": "hello", "a": 42}}
        first = canonical_json(obj)
        for _ in range(10):
            assert canonical_json(obj) == first

    def test_canonical_json_rejects_floats(self):
        """Test 2: canonical_json({\"x\": 1.5}) raises TypeError."""
        with pytest.raises(TypeError, match="[Ff]loat"):
            canonical_json({"x": 1.5})

    def test_canonical_json_rejects_nested_floats(self):
        """Float nested inside a list inside a dict."""
        with pytest.raises(TypeError, match="[Ff]loat"):
            canonical_json({"a": [1, 2, 3.0]})

    def test_canonical_hash_stable(self):
        """Test 3: Same input -> same hash, 10 iterations."""
        obj = {"key": "value", "num": 42}
        first = canonical_hash(obj)
        assert len(first) == 64  # Full SHA-256 hex digest.
        for _ in range(10):
            assert canonical_hash(obj) == first

    def test_canonical_short_hash_length(self):
        """Short hash is first 16 chars of full hash."""
        obj = {"test": True}
        full = canonical_hash(obj)
        short = canonical_short_hash(obj)
        assert len(short) == 16
        assert full.startswith(short)


# ── FactsLedger ───────────────────────────────────────────────────────

def _make_test_fact(kind: str = "WORLD_RULE", suffix: str = "") -> Fact:
    """Helper: create a fact with deterministic payload."""
    payload = {"rule": f"test_rule_{suffix}", "value": 42}
    provenance = {"source": "test", "event_ids": [1], "rule_refs": []}
    return make_fact(
        kind=kind,
        payload=payload,
        provenance=provenance,
        created_event_id=1,
    )


class TestFactsLedger:
    """Tests 4-6: FactsLedger determinism, dedup, roundtrip."""

    def test_facts_ledger_digest_deterministic(self):
        """Test 4: Insert N facts in random order; digest identical.

        Run 5 times with shuffled insertion order.
        """
        facts = []
        for i in range(10):
            facts.append(make_fact(
                kind="WORLD_RULE",
                payload={"rule": f"rule_{i}", "value": i},
                provenance={"source": "test", "event_ids": [i], "rule_refs": []},
                created_event_id=i,
            ))

        digests = []
        for _ in range(5):
            ledger = FactsLedger()
            shuffled = list(facts)
            random.shuffle(shuffled)
            for f in shuffled:
                ledger.append(f)
            digests.append(ledger.digest())

        assert len(set(digests)) == 1, f"Digests differ across insertion orders: {digests}"

    def test_facts_ledger_rejects_duplicate(self):
        """Test 5: Same payload -> same fact_id -> ValueError on second append."""
        payload = {"rule": "unique_rule", "value": 99}
        provenance = {"source": "test", "event_ids": [1], "rule_refs": []}
        f1 = make_fact("WORLD_RULE", payload, provenance, created_event_id=1)
        f2 = make_fact("WORLD_RULE", payload, provenance, created_event_id=2)
        assert f1.fact_id == f2.fact_id  # Content-addressed — same payload.

        ledger = FactsLedger()
        ledger.append(f1)
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            ledger.append(f2)

    def test_facts_ledger_jsonl_roundtrip(self, tmp_path: Path):
        """Test 6: Write to JSONL, load, digest matches."""
        ledger = FactsLedger()
        for i in range(5):
            ledger.append(make_fact(
                kind="CLUE",
                payload={"clue": f"clue_{i}", "importance": i},
                provenance={"source": "test", "event_ids": [i], "rule_refs": []},
                created_event_id=i,
            ))

        original_digest = ledger.digest()
        path = tmp_path / "facts.jsonl"
        ledger.to_jsonl(path)

        loaded = FactsLedger.from_jsonl(path)
        assert loaded.digest() == original_digest
        assert len(loaded) == 5

    def test_facts_ledger_query(self):
        """Query by kind and visibility_mask."""
        ledger = FactsLedger()
        ledger.append(make_fact(
            kind="WORLD_RULE",
            payload={"rule": "gravity", "value": 1},
            provenance={"source": "test", "event_ids": [1], "rule_refs": []},
            created_event_id=1,
        ))
        ledger.append(make_fact(
            kind="CLUE",
            payload={"clue": "secret_door", "value": 2},
            provenance={"source": "test", "event_ids": [2], "rule_refs": []},
            created_event_id=2,
            visibility_mask="PUBLIC",
        ))

        rules = ledger.query(kind="WORLD_RULE")
        assert len(rules) == 1
        assert rules[0].kind == "WORLD_RULE"

        public = ledger.query(visibility_mask="PUBLIC")
        assert len(public) == 1
        assert public[0].visibility_mask == "PUBLIC"


# ── UnlockState ───────────────────────────────────────────────────────


class TestUnlockState:
    """Tests 7-10: UnlockState scope, idempotency, determinism, roundtrip."""

    def test_unlock_state_scope_ordering(self):
        """Test 7: CAMPAIGN unlock satisfies SESSION and SCENE checks."""
        state = UnlockState()
        entry = UnlockEntry(
            handle="fact_abc123",
            scope="CAMPAIGN",
            source="NOTEBOOK",
            provenance_event_id=1,
            created_at="2026-01-01T00:00:00Z",
        )
        state.unlock(entry)

        assert state.is_unlocked("fact_abc123", "CAMPAIGN")
        assert state.is_unlocked("fact_abc123", "SESSION")
        assert state.is_unlocked("fact_abc123", "SCENE")

    def test_unlock_state_scope_does_not_over_satisfy(self):
        """SCENE unlock does NOT satisfy SESSION or CAMPAIGN checks."""
        state = UnlockState()
        entry = UnlockEntry(
            handle="fact_xyz",
            scope="SCENE",
            source="SYSTEM",
            provenance_event_id=1,
        )
        state.unlock(entry)

        assert state.is_unlocked("fact_xyz", "SCENE")
        assert not state.is_unlocked("fact_xyz", "SESSION")
        assert not state.is_unlocked("fact_xyz", "CAMPAIGN")

    def test_unlock_state_idempotent_upgrade(self):
        """Test 8: Re-unlock with broader scope upgrades; narrower ignored."""
        state = UnlockState()

        # Start with SCENE.
        state.unlock(UnlockEntry(
            handle="fact_001",
            scope="SCENE",
            source="SYSTEM",
            provenance_event_id=1,
        ))
        assert not state.is_unlocked("fact_001", "SESSION")

        # Upgrade to SESSION.
        state.unlock(UnlockEntry(
            handle="fact_001",
            scope="SESSION",
            source="NOTEBOOK",
            provenance_event_id=2,
        ))
        assert state.is_unlocked("fact_001", "SESSION")

        # Attempt downgrade to SCENE — should be ignored.
        state.unlock(UnlockEntry(
            handle="fact_001",
            scope="SCENE",
            source="SYSTEM",
            provenance_event_id=3,
        ))
        # Still at SESSION.
        assert state.is_unlocked("fact_001", "SESSION")

    def test_unlock_state_digest_deterministic(self):
        """Test 9: Same unlocks in different order -> same digest."""
        entries = [
            UnlockEntry(handle=f"h_{i}", scope="SESSION", source="SYSTEM",
                        provenance_event_id=i, created_at=f"2026-01-0{i+1}T00:00:00Z")
            for i in range(5)
        ]

        digests = []
        for _ in range(5):
            state = UnlockState()
            shuffled = list(entries)
            random.shuffle(shuffled)
            for e in shuffled:
                state.unlock(e)
            digests.append(state.digest())

        assert len(set(digests)) == 1, f"Digests differ across insertion orders: {digests}"

    def test_unlock_state_jsonl_roundtrip(self, tmp_path: Path):
        """Test 10: Write, load, digest matches."""
        state = UnlockState()
        for i in range(5):
            state.unlock(UnlockEntry(
                handle=f"handle_{i}",
                scope=["SCENE", "SESSION", "CAMPAIGN"][i % 3],
                source="SYSTEM",
                provenance_event_id=i,
                created_at=f"2026-01-0{i+1}T00:00:00Z",
            ))

        original_digest = state.digest()
        path = tmp_path / "unlocks.jsonl"
        state.to_jsonl(path)

        loaded = UnlockState.from_jsonl(path)
        assert loaded.digest() == original_digest
        assert len(loaded) == 5

    def test_unlock_state_unlocked_handles(self):
        """unlocked_handles returns correct handles at scope level."""
        state = UnlockState()
        state.unlock(UnlockEntry(handle="scene_only", scope="SCENE", source="SYSTEM"))
        state.unlock(UnlockEntry(handle="session_up", scope="SESSION", source="SYSTEM"))
        state.unlock(UnlockEntry(handle="campaign_all", scope="CAMPAIGN", source="SYSTEM"))

        scene_handles = state.unlocked_handles("SCENE")
        assert scene_handles == frozenset({"scene_only", "session_up", "campaign_all"})

        session_handles = state.unlocked_handles("SESSION")
        assert session_handles == frozenset({"session_up", "campaign_all"})

        campaign_handles = state.unlocked_handles("CAMPAIGN")
        assert campaign_handles == frozenset({"campaign_all"})


# ── StoryState ────────────────────────────────────────────────────────


class TestStoryState:
    """Tests 11-15: StoryState immutability, versioning, determinism, roundtrip."""

    def test_story_state_immutable(self):
        """Test 11: Applying event produces new version, old unchanged."""
        initial = StoryState(campaign_id="camp_001", version=0)
        log = StoryStateLog(initial)

        new = log.apply("scene_start", {"scene_id": "scene_alpha"})

        # New state has updated scene_id and version.
        assert new.scene_id == "scene_alpha"
        assert new.version == 1

        # Original is unchanged (frozen dataclass).
        assert initial.scene_id is None
        assert initial.version == 0

        # Log history has both.
        assert len(log.history()) == 2
        assert log.history()[0].version == 0
        assert log.history()[1].version == 1

    def test_story_state_version_monotonic(self):
        """Test 12: Versions strictly increase."""
        log = StoryStateLog(StoryState(campaign_id="camp_001", version=0))

        log.apply("scene_start", {"scene_id": "s1"})
        log.apply("mode_changed", {"mode": "COMBAT"})
        log.apply("scene_end", {})
        log.apply("world_id_set", {"world_id": "w_abc"})

        versions = [s.version for s in log.history()]
        assert versions == [0, 1, 2, 3, 4]
        # Strictly increasing.
        for i in range(1, len(versions)):
            assert versions[i] == versions[i - 1] + 1

    def test_story_state_digest_deterministic(self):
        """Test 13: Same events -> same digest."""
        digests = []
        for _ in range(5):
            log = StoryStateLog(StoryState(campaign_id="camp_001", version=0))
            log.apply("scene_start", {"scene_id": "s1"})
            log.apply("mode_changed", {"mode": "COMBAT"})
            digests.append(log.digest())

        assert len(set(digests)) == 1

    def test_story_state_ignores_unknown_events(self):
        """Test 14: Unknown event type does not crash."""
        log = StoryStateLog(StoryState(campaign_id="camp_001", version=0))

        result = log.apply("totally_unknown_event", {"foo": "bar"})

        # Returns current state unchanged.
        assert result.version == 0
        assert len(log.history()) == 1  # No new entry.

    def test_story_state_jsonl_roundtrip(self, tmp_path: Path):
        """Test 15: Write, load, history matches."""
        log = StoryStateLog(StoryState(campaign_id="camp_001", version=0))
        log.apply("scene_start", {"scene_id": "s1"})
        log.apply("mode_changed", {"mode": "COMBAT"})
        log.apply("scene_end", {})

        path = tmp_path / "story.jsonl"
        log.to_jsonl(path)

        loaded = StoryStateLog.from_jsonl(path)
        assert len(loaded.history()) == len(log.history())
        assert loaded.digest() == log.digest()

        # Verify full history matches.
        for orig, reloaded in zip(log.history(), loaded.history()):
            assert orig.to_dict() == reloaded.to_dict()

    def test_story_state_mode_values(self):
        """All supported modes can be set."""
        log = StoryStateLog(StoryState(campaign_id="camp_001", version=0))
        for mode in ("COMBAT", "EXPLORATION", "ROLEPLAY", "REFERENCE", "NOTEBOOK"):
            result = log.apply("mode_changed", {"mode": mode})
            assert result.mode == mode
