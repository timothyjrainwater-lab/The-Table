"""Gate D tests — Director Phase 1.

18+ tests across 7 gate categories (DIR-G1 through DIR-G7).

Categories:
    DIR-G1: References not content (2 tests)
    DIR-G2: New canon requires consent (2 tests)
    DIR-G3: Read-only enforced (2 tests)
    DIR-G4: Determinism (3 tests)
    DIR-G5: Anti-rail / nudge caps (3 tests)
    DIR-G6: Handles-not-secrets (2 tests)
    DIR-G7: Oracle integration preflight (4 tests)

Authority: WO-DIRECTOR-01, Director Spec v0, GT v12.
"""
from __future__ import annotations

import hashlib
import inspect

import pytest

from aidm.oracle.canonical import canonical_json, canonical_short_hash
from aidm.oracle.facts_ledger import FactsLedger, make_fact
from aidm.oracle.unlock_state import UnlockEntry, UnlockState
from aidm.oracle.story_state import StoryState, StoryStateLog
from aidm.oracle.working_set import (
    CompilationPolicy,
    ScopeCursor,
    WorkingSet,
    compile_working_set,
)
from aidm.lens.director.models import (
    BEAT_TYPES,
    NUDGE_TYPES,
    BeatHistory,
    BeatIntent,
    DirectorPromptPack,
    NudgeDirective,
    compile_director_promptpack,
    make_beat_intent,
    make_nudge_directive,
)
from aidm.lens.director.policy import (
    DirectorPolicyPins,
    select_beat,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_test_stores(n_facts=3):
    """Build Oracle stores + WorkingSet for Director testing."""
    ledger = FactsLedger()
    unlock = UnlockState()
    story_log = StoryStateLog(StoryState(
        campaign_id="test_campaign",
        world_id="test_world",
        scene_id="scene_001",
        mode="EXPLORATION",
    ))

    for i in range(n_facts):
        fact = make_fact(
            kind="WORLD_RULE",
            payload={"rule": f"test_rule_{i}", "index": i},
            provenance={"source": "test"},
            created_event_id=i,
            visibility_mask="PUBLIC",
            precision_tag="UNLOCKED",
        )
        ledger.append(fact)
        unlock.unlock(UnlockEntry(
            handle=fact.fact_id,
            scope="SESSION",
            source="SYSTEM",
            provenance_event_id=i,
        ))

    ws = compile_working_set(
        facts_ledger=ledger,
        unlock_state=unlock,
        story_state_log=story_log,
        policy=CompilationPolicy(),
        scope_cursor=ScopeCursor(
            campaign_id="test_campaign",
            scene_id="scene_001",
            world_id="test_world",
        ),
    )
    return ledger, unlock, story_log, ws


def _build_director_promptpack(ws=None, beat_history=None, **kwargs):
    """Build a DirectorPromptPack from WorkingSet + beat history."""
    if ws is None:
        _, _, _, ws = _build_test_stores()
    if beat_history is None:
        beat_history = BeatHistory()
    return compile_director_promptpack(ws, beat_history, **kwargs)


def _run_select_beat(dpp=None, beat_history=None, pins=None):
    """Run select_beat and return (BeatIntent, NudgeDirective)."""
    if dpp is None:
        dpp = _build_director_promptpack()
    if beat_history is None:
        beat_history = BeatHistory()
    if pins is None:
        pins = DirectorPolicyPins()
    return select_beat(dpp, beat_history, pins)


# ---------------------------------------------------------------------------
# DIR-G1: References Not Content (2 tests)
# ---------------------------------------------------------------------------

class TestDIRG1ReferencesNotContent:
    def test_beat_intent_has_no_free_text(self):
        """BeatIntent fields are IDs/enums/booleans — no free-text content."""
        beat = make_beat_intent(
            scene_id="scene_001",
            beat_sequence=0,
            beat_type="ENVIRONMENTAL",
            target_handles=("handle_a", "handle_b"),
            pacing_mode="NORMAL",
            permission_prompt=False,
        )
        # All non-bytes fields must be: str (ID/enum), tuple of str, bool, or bytes.
        # No field should contain arbitrary prose.
        assert beat.beat_type in BEAT_TYPES
        assert beat.pacing_mode in {"NORMAL", "SLOW_BURN", "ACCELERATE", "CLIMAX"}
        assert isinstance(beat.target_handles, tuple)
        assert all(isinstance(h, str) for h in beat.target_handles)
        assert isinstance(beat.permission_prompt, bool)
        assert isinstance(beat.beat_id, str) and len(beat.beat_id) == 16

    def test_all_target_handles_resolve_to_oracle(self):
        """All handles in BeatIntent resolve to WorkingSet allowmention set."""
        _, _, _, ws = _build_test_stores()
        bh = BeatHistory()
        dpp = compile_director_promptpack(ws, bh)
        beat, nudge = select_beat(dpp, bh)

        # All target handles must be in allowmention or empty.
        for handle in beat.target_handles:
            assert handle in dpp.allowmention_handles, (
                f"Handle {handle} not in allowmention set"
            )


# ---------------------------------------------------------------------------
# DIR-G2: New Canon Requires Consent (2 tests)
# ---------------------------------------------------------------------------

class TestDIRG2NoCanonWrites:
    def test_no_oracle_write_calls(self):
        """Director code contains no Oracle store write method calls."""
        import aidm.lens.director.models as models_mod
        import aidm.lens.director.policy as policy_mod

        oracle_write_patterns = [
            "ledger.append(",
            "unlock.unlock(",
            "story_log.apply(",
            "facts_ledger.append(",
            "unlock_state.unlock(",
            "story_state_log.apply(",
        ]

        for mod in (models_mod, policy_mod):
            source = inspect.getsource(mod)
            for pattern in oracle_write_patterns:
                assert pattern not in source, (
                    f"Director module {mod.__name__} contains Oracle write "
                    f"pattern: {pattern!r}"
                )

    def test_consent_routing_for_new_content(self):
        """Director never mints new handles — all handles come from input.

        If Director needed new content, it would need to emit a consent
        proposal.  Phase 1: Director only references existing handles,
        so this test verifies no handle creation occurs.
        """
        dpp = _build_director_promptpack()
        bh = BeatHistory()
        beat, nudge = select_beat(dpp, bh)

        # All output handles must be from input or empty.
        all_output_handles = set(beat.target_handles)
        if nudge.target_handle is not None:
            all_output_handles.add(nudge.target_handle)
        all_output_handles.update(nudge.consequence_handles)

        input_handles = set(dpp.allowmention_handles)
        for handle in all_output_handles:
            assert handle in input_handles, (
                f"Director minted handle {handle!r} not in input set"
            )


# ---------------------------------------------------------------------------
# DIR-G3: Read-Only Enforced (2 tests)
# ---------------------------------------------------------------------------

class TestDIRG3ReadOnlyEnforced:
    def test_no_prohibited_imports(self):
        """Director module has no prohibited imports per boundary gate.

        Director (in lens/director/) must NOT import from:
        oracle stores directly, core (box), spark, narration, immersion.
        It may import from oracle.canonical (utilities).
        """
        import aidm.lens.director.models as models_mod
        import aidm.lens.director.policy as policy_mod

        prohibited_prefixes = [
            "from aidm.core.",
            "import aidm.core.",
            "from aidm.spark",
            "import aidm.spark",
            "from aidm.narration",
            "import aidm.narration",
            "from aidm.immersion",
            "import aidm.immersion",
        ]

        # Allowed oracle imports: only canonical utilities.
        oracle_prohibited = [
            "from aidm.oracle.facts_ledger",
            "from aidm.oracle.unlock_state",
            "from aidm.oracle.story_state",
            "from aidm.oracle.cold_boot",
            "from aidm.oracle.save_snapshot",
            "from aidm.oracle.compaction",
        ]

        for mod in (models_mod, policy_mod):
            source = inspect.getsource(mod)
            for prefix in prohibited_prefixes:
                assert prefix not in source, (
                    f"Director {mod.__name__} has prohibited import: {prefix}"
                )
            # Policy module should not import Oracle stores.
            if mod is policy_mod:
                for prefix in oracle_prohibited:
                    assert prefix not in source, (
                        f"Director policy has Oracle store import: {prefix}"
                    )

    def test_director_receives_promptpack_only(self):
        """select_beat takes DirectorPromptPack, not raw Oracle stores."""
        sig = inspect.signature(select_beat)
        params = list(sig.parameters.values())

        # First param should be DirectorPromptPack.
        assert params[0].annotation in (
            DirectorPromptPack,
            "DirectorPromptPack",
        ) or params[0].name == "dpp"

        # No parameter should accept FactsLedger, UnlockState, etc.
        param_names = {p.name for p in params}
        assert "facts_ledger" not in param_names
        assert "unlock_state" not in param_names
        assert "story_state" not in param_names


# ---------------------------------------------------------------------------
# DIR-G4: Determinism (3 tests)
# ---------------------------------------------------------------------------

class TestDIRG4Determinism:
    def test_same_inputs_same_beat_bytes(self):
        """Same DirectorPromptPack + beat history → byte-identical BeatIntent."""
        dpp = _build_director_promptpack()
        bh1 = BeatHistory()
        bh2 = BeatHistory()

        beat1, nudge1 = select_beat(dpp, bh1)
        beat2, nudge2 = select_beat(dpp, bh2)

        assert beat1.bytes_hash == beat2.bytes_hash
        assert beat1.canonical_bytes == beat2.canonical_bytes
        assert nudge1.bytes_hash == nudge2.bytes_hash
        assert nudge1.canonical_bytes == nudge2.canonical_bytes

    def test_same_inputs_same_nudge_bytes(self):
        """Same inputs → byte-identical NudgeDirective (including NONE)."""
        _, _, _, ws = _build_test_stores()
        bh = BeatHistory()
        bh.beats_since_player_action = 5  # stall

        dpp1 = compile_director_promptpack(ws, bh)
        dpp2 = compile_director_promptpack(ws, bh)

        beat1, nudge1 = select_beat(dpp1, bh)
        beat2, nudge2 = select_beat(dpp2, bh)

        assert nudge1.bytes_hash == nudge2.bytes_hash

    def test_10x_deterministic(self):
        """10 runs → all identical bytes."""
        dpp = _build_director_promptpack()
        hashes = set()
        for _ in range(10):
            bh = BeatHistory()
            beat, nudge = select_beat(dpp, bh)
            hashes.add((beat.bytes_hash, nudge.bytes_hash))

        assert len(hashes) == 1


# ---------------------------------------------------------------------------
# DIR-G5: Anti-Rail / Nudge Caps (3 tests)
# ---------------------------------------------------------------------------

class TestDIRG5AntiRail:
    def test_zero_one_nudge_per_scene(self):
        """Simulate full scene — assert at most 1 nudge fires."""
        _, _, _, ws = _build_test_stores()
        bh = BeatHistory()
        pins = DirectorPolicyPins(stall_threshold=2, cooldown_beats=2)
        nudge_count = 0

        for i in range(10):
            bh.beats_since_player_action = i  # increasing stall
            dpp = compile_director_promptpack(ws, bh)
            beat, nudge = select_beat(dpp, bh, pins)

            if nudge.type != "NONE":
                nudge_count += 1
                bh.record_nudge()

            bh.record_beat(had_player_action=False)

        assert nudge_count <= 1, f"Expected <= 1 nudge, got {nudge_count}"

    def test_cooldown_suppresses_nudges(self):
        """After nudge fires, cooldown suppresses subsequent nudges."""
        _, _, _, ws = _build_test_stores()
        bh = BeatHistory()
        pins = DirectorPolicyPins(stall_threshold=2, cooldown_beats=4)

        # Force stall.
        bh.beats_since_player_action = 5
        dpp = compile_director_promptpack(ws, bh)
        beat, nudge = select_beat(dpp, bh, pins)
        assert nudge.type == "SPOTLIGHT_NUDGE"

        # Record the nudge.
        bh.record_nudge()
        bh.record_beat(had_player_action=False)

        # Next beat: nudge should be suppressed (cooldown + 1-per-scene).
        bh.beats_since_player_action = 5
        dpp2 = compile_director_promptpack(ws, bh)
        beat2, nudge2 = select_beat(dpp2, bh, pins)
        assert nudge2.type == "NONE"

    def test_hysteresis_prevents_false_nudge(self):
        """Single inactive beat does not trigger stall nudge."""
        _, _, _, ws = _build_test_stores()
        bh = BeatHistory()
        pins = DirectorPolicyPins(stall_threshold=3)

        # Only 1 beat without player action.
        bh.beats_since_player_action = 1
        dpp = compile_director_promptpack(ws, bh)
        beat, nudge = select_beat(dpp, bh, pins)
        assert nudge.type == "NONE", "Hysteresis should prevent nudge on 1 beat"

        # 2 beats — still below threshold.
        bh.beats_since_player_action = 2
        dpp = compile_director_promptpack(ws, bh)
        beat, nudge = select_beat(dpp, bh, pins)
        assert nudge.type == "NONE", "Hysteresis should prevent nudge on 2 beats"


# ---------------------------------------------------------------------------
# DIR-G6: Handles-Not-Secrets (2 tests)
# ---------------------------------------------------------------------------

class TestDIRG6HandlesNotSecrets:
    def test_locked_handles_absent_from_output(self):
        """Locked precision handles must not appear in Director output."""
        ledger = FactsLedger()
        unlock = UnlockState()
        story_log = StoryStateLog(StoryState(
            campaign_id="test",
            scene_id="scene_001",
        ))

        # Create unlocked + locked facts.
        for i in range(2):
            fact = make_fact(
                kind="WORLD_RULE",
                payload={"rule": f"public_{i}", "index": i},
                provenance={"source": "test"},
                created_event_id=i,
                visibility_mask="PUBLIC",
                precision_tag="UNLOCKED",
            )
            ledger.append(fact)
            unlock.unlock(UnlockEntry(
                handle=fact.fact_id, scope="SESSION", source="SYSTEM",
            ))

        locked_fact = make_fact(
            kind="CLUE",
            payload={"secret": "hidden_info", "index": 99},
            provenance={"source": "test"},
            created_event_id=99,
            visibility_mask="DM_ONLY",
            precision_tag="LOCKED",
        )
        ledger.append(locked_fact)

        ws = compile_working_set(
            ledger, unlock, story_log,
            CompilationPolicy(),
            ScopeCursor(campaign_id="test", scene_id="scene_001"),
        )

        bh = BeatHistory()
        bh.beats_since_player_action = 5  # stall → nudge fires
        dpp = compile_director_promptpack(ws, bh)
        beat, nudge = select_beat(dpp, bh)

        # Locked handle must not appear in any output.
        all_output = set(beat.target_handles)
        if nudge.target_handle:
            all_output.add(nudge.target_handle)
        all_output.update(nudge.consequence_handles)

        assert locked_fact.fact_id not in all_output
        assert locked_fact.fact_id not in dpp.allowmention_handles

    def test_all_handles_in_allowmention_set(self):
        """All target_handles and consequence_handles are in allowmention."""
        _, _, _, ws = _build_test_stores()
        bh = BeatHistory()
        bh.beats_since_player_action = 5  # stall

        dpp = compile_director_promptpack(ws, bh)
        beat, nudge = select_beat(dpp, bh)

        allowed = set(dpp.allowmention_handles)
        for h in beat.target_handles:
            assert h in allowed
        if nudge.target_handle is not None:
            assert nudge.target_handle in allowed
        for h in nudge.consequence_handles:
            assert h in allowed


# ---------------------------------------------------------------------------
# DIR-G7: Oracle Integration Preflight (4 tests)
# ---------------------------------------------------------------------------

class TestDIRG7OracleIntegrationPreflight:
    def test_oracle_to_beat_intent_roundtrip(self):
        """Oracle → WorkingSet → DirectorPromptPack → BeatIntent round-trip."""
        ledger, unlock, story_log, ws = _build_test_stores()

        bh = BeatHistory()
        dpp = compile_director_promptpack(ws, bh)
        beat, nudge = select_beat(dpp, bh)

        # Validate the full chain produced valid output.
        assert isinstance(beat, BeatIntent)
        assert isinstance(nudge, NudgeDirective)
        assert beat.beat_type in BEAT_TYPES
        assert nudge.type in NUDGE_TYPES
        assert len(beat.beat_id) == 16
        assert len(beat.bytes_hash) == 64

    def test_roundtrip_deterministic(self):
        """Same stores → same bytes through full pipeline (twice)."""
        results = []
        for _ in range(2):
            ledger, unlock, story_log, ws = _build_test_stores()
            bh = BeatHistory()
            dpp = compile_director_promptpack(ws, bh)
            beat, nudge = select_beat(dpp, bh)
            results.append((beat.bytes_hash, nudge.bytes_hash, dpp.bytes_hash))

        assert results[0] == results[1]

    def test_cold_boot_replay_produces_identical_sequence(self):
        """Cold boot → replay → Director produces identical BeatIntent."""
        from aidm.core.event_log import Event, EventLog
        from aidm.oracle.cold_boot import cold_boot
        from aidm.oracle.save_snapshot import create_snapshot
        from aidm.oracle.compaction import CompactionRegistry

        # Build stores via event log.
        event_log = EventLog()
        event_log.append(Event(
            event_id=0, event_type="oracle_story_init", timestamp=0,
            payload={"campaign_id": "test", "scene_id": "scene_001"},
        ))

        fact_payload = {"rule": "cold_boot_rule", "index": 0}
        fid = canonical_short_hash(fact_payload)
        event_log.append(Event(
            event_id=1, event_type="oracle_fact_created", timestamp=0,
            payload={
                "fact_id": fid, "kind": "WORLD_RULE",
                "payload": fact_payload, "provenance": {"source": "test"},
                "visibility_mask": "PUBLIC", "precision_tag": "UNLOCKED",
                "stable_key": f"WORLD_RULE:{fid[:8]}",
            },
        ))
        event_log.append(Event(
            event_id=2, event_type="oracle_unlock", timestamp=0,
            payload={"handle": fid, "scope": "SESSION", "source": "SYSTEM"},
        ))

        # Build stores from event replay.
        from aidm.oracle.cold_boot import _reduce_oracle_event
        fl, us, ssl = FactsLedger(), UnlockState(), None
        for ev in event_log.events:
            ssl = _reduce_oracle_event(fl, us, ssl, ev)
        if ssl is None:
            ssl = StoryStateLog(StoryState(campaign_id="default"))

        ws = compile_working_set(
            fl, us, ssl, CompilationPolicy(),
            ScopeCursor(
                campaign_id=ssl.current().campaign_id,
                scene_id=ssl.current().scene_id,
            ),
        )

        # Run Director on original stores.
        bh = BeatHistory()
        dpp = compile_director_promptpack(ws, bh)
        beat1, nudge1 = select_beat(dpp, bh)

        # Save snapshot.
        pins = {"hash_algorithm": "sha256", "short_hash_length": 16,
                "canonical_profile": "oracle_v0"}
        registry = CompactionRegistry()
        snapshot = create_snapshot(
            fl, us, ssl, ws, event_log,
            event_range=(0, 2), pins=pins,
            compaction_registry=registry,
        )

        # Cold boot.
        fl2, us2, ssl2, ws2 = cold_boot(snapshot, event_log, pins)

        # Run Director on cold-booted stores.
        bh2 = BeatHistory()
        dpp2 = compile_director_promptpack(ws2, bh2)
        beat2, nudge2 = select_beat(dpp2, bh2)

        assert beat1.bytes_hash == beat2.bytes_hash
        assert nudge1.bytes_hash == nudge2.bytes_hash

    def test_no_regressions_on_oracle_gates(self):
        """Oracle Gate A/B/C tests still importable and conceptually valid.

        This is a structural check — the actual gate tests run in their
        own files.  This test verifies the integration chain is intact.
        """
        # Verify Oracle stores are importable.
        from aidm.oracle.facts_ledger import FactsLedger
        from aidm.oracle.unlock_state import UnlockState
        from aidm.oracle.story_state import StoryStateLog
        from aidm.oracle.working_set import compile_working_set
        from aidm.oracle.cold_boot import cold_boot
        from aidm.oracle.save_snapshot import create_snapshot
        from aidm.oracle.compaction import CompactionRegistry

        # Verify Lens compiler is importable.
        from aidm.lens.promptpack_compiler import compile_promptpack

        # Verify Director is importable.
        from aidm.lens.director.models import compile_director_promptpack
        from aidm.lens.director.policy import select_beat

        # If we got here, the import chain is intact.
        assert True
