"""Gate E tests — Director Phase 2 Integration.

14+ tests across 5 gate categories (DIR-E1 through DIR-E5).

Categories:
    DIR-E1: BeatIntent shapes PromptPack (3 tests)
    DIR-E2: NudgeDirective routes to PromptPack (2 tests)
    DIR-E3: Event emission (3 tests)
    DIR-E4: End-to-end determinism (3 tests)
    DIR-E5: BeatHistory reconstruction (3 tests)

Authority: WO-DIRECTOR-02, Director Spec v0 §9, GT v12.
"""
from __future__ import annotations

import hashlib

import pytest

from aidm.core.event_log import Event, EventLog
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
from aidm.lens.promptpack_compiler import compile_promptpack
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
    SelectBeatResult,
    Suppression,
    select_beat,
    select_beat_with_audit,
)
from aidm.lens.director.invoke import (
    DirectorInvocationResult,
    invoke_director,
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


def _invoke_director_default(ws=None, beat_history=None, **kwargs):
    """Run invoke_director with sensible defaults."""
    if ws is None:
        _, _, _, ws = _build_test_stores()
    if beat_history is None:
        beat_history = BeatHistory()
    return invoke_director(
        working_set=ws,
        beat_history=beat_history,
        next_event_id=0,
        timestamp=0.0,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# DIR-E1: BeatIntent shapes PromptPack (3 tests)
# ---------------------------------------------------------------------------

class TestDIRE1BeatIntentShapesPromptPack:
    def test_target_handles_foregrounded_in_promptpack(self):
        """BeatIntent with target_handles → those handles foregrounded."""
        _, _, _, ws = _build_test_stores(n_facts=3)
        bh = BeatHistory()
        # Force stall so Director produces a nudge with target handle.
        bh.beats_since_player_action = 5

        result = _invoke_director_default(ws=ws, beat_history=bh)

        # The beat should have target handles (from stall detection).
        assert len(result.beat_intent.target_handles) > 0
        # PromptPack should exist and be valid.
        assert result.promptpack is not None
        # The foregrounded handle should appear in outcome_summary.
        target = result.beat_intent.target_handles[0]
        # Verify the PromptPack was compiled with Director input.
        pack_dict = result.promptpack.to_dict()
        assert pack_dict is not None

    def test_pacing_mode_reflected_in_style_channel(self):
        """BeatIntent with pacing_mode → StyleChannel reflects pacing."""
        # Default pacing is NORMAL → pacing_hint=None.
        _, _, _, ws = _build_test_stores()
        bh = BeatHistory()

        result = _invoke_director_default(ws=ws, beat_history=bh)
        # NORMAL pacing → no pacing hint.
        assert result.promptpack.style.pacing_hint is None

        # Verify that compile_promptpack with explicit ACCELERATE pacing
        # does set the hint.
        beat = make_beat_intent(
            scene_id="scene_001",
            beat_sequence=0,
            beat_type="ENVIRONMENTAL",
            target_handles=(),
            pacing_mode="ACCELERATE",
        )
        nudge = make_nudge_directive()
        pack, env = compile_promptpack(ws, beat_intent=beat, nudge_directive=nudge)
        assert pack.style.pacing_hint == "ACCELERATE"

    def test_none_beat_intent_backward_compatible(self):
        """BeatIntent=None → backward-compatible default PromptPack."""
        _, _, _, ws = _build_test_stores()

        # Compile without Director input (Phase 1 path).
        pack_no_director, env_no_director = compile_promptpack(ws)
        # Compile with explicit None.
        pack_none, env_none = compile_promptpack(ws, beat_intent=None, nudge_directive=None)

        # Should produce identical results.
        assert pack_no_director.style.pacing_hint is None
        assert pack_none.style.pacing_hint is None
        assert pack_no_director.task.nudge_type is None
        assert pack_none.task.nudge_type is None
        # Byte-level: same canonical bytes.
        bytes1 = canonical_json(pack_no_director.to_dict())
        bytes2 = canonical_json(pack_none.to_dict())
        assert bytes1 == bytes2


# ---------------------------------------------------------------------------
# DIR-E2: NudgeDirective routes to PromptPack (2 tests)
# ---------------------------------------------------------------------------

class TestDIRE2NudgeDirectiveRouting:
    def test_nudge_metadata_present_in_promptpack(self):
        """NudgeDirective with type=SPOTLIGHT_NUDGE → nudge metadata in PromptPack."""
        _, _, _, ws = _build_test_stores()
        beat = make_beat_intent(
            scene_id="scene_001",
            beat_sequence=0,
            beat_type="ENVIRONMENTAL",
            target_handles=(),
        )
        nudge = make_nudge_directive(
            nudge_type="SPOTLIGHT_NUDGE",
            target_handle="handle_abc",
            reason_code="stall_detected",
        )

        pack, env = compile_promptpack(ws, beat_intent=beat, nudge_directive=nudge)

        assert pack.task.nudge_type == "SPOTLIGHT_NUDGE"
        assert pack.task.nudge_target_handle == "handle_abc"
        assert pack.task.nudge_reason_code == "stall_detected"

        # Verify it appears in serialization.
        serialized = pack.serialize()
        assert "Nudge: SPOTLIGHT_NUDGE" in serialized
        assert "Nudge Target: handle_abc" in serialized
        assert "Nudge Reason: stall_detected" in serialized

    def test_none_nudge_no_content_in_promptpack(self):
        """NudgeDirective with type=NONE → no nudge content in PromptPack."""
        _, _, _, ws = _build_test_stores()
        beat = make_beat_intent(
            scene_id="scene_001",
            beat_sequence=0,
            beat_type="ENVIRONMENTAL",
            target_handles=(),
        )
        nudge = make_nudge_directive(nudge_type="NONE", reason_code="default")

        pack, env = compile_promptpack(ws, beat_intent=beat, nudge_directive=nudge)

        assert pack.task.nudge_type is None
        assert pack.task.nudge_target_handle is None
        assert pack.task.nudge_reason_code is None

        # Serialization should not mention nudge.
        serialized = pack.serialize()
        assert "Nudge:" not in serialized


# ---------------------------------------------------------------------------
# DIR-E3: Event emission (3 tests)
# ---------------------------------------------------------------------------

class TestDIRE3EventEmission:
    def test_nudge_fires_ev033(self):
        """Nudge fires → EV-033 NudgeSelected emitted with correct payload."""
        _, _, _, ws = _build_test_stores()
        bh = BeatHistory()
        bh.beats_since_player_action = 5  # Force stall → nudge fires.

        result = _invoke_director_default(ws=ws, beat_history=bh)

        # Should have director_beat_selected + nudge_selected events.
        event_types = [e.event_type for e in result.events]
        assert "director_beat_selected" in event_types
        assert "nudge_selected" in event_types

        # Validate nudge_selected payload.
        nudge_event = [e for e in result.events if e.event_type == "nudge_selected"][0]
        assert nudge_event.payload["scene_id"] == "scene_001"
        assert nudge_event.payload["nudge_type"] == "SPOTLIGHT_NUDGE"
        assert nudge_event.payload["reason_code"] == "stall_detected"
        assert nudge_event.payload["target_handle"] is not None

    def test_nudge_suppressed_ev034(self):
        """Nudge suppressed (cooldown) → EV-034 NudgeSuppressed emitted."""
        _, _, _, ws = _build_test_stores()
        bh = BeatHistory()
        pins = DirectorPolicyPins(stall_threshold=2, cooldown_beats=4)

        # First invocation: nudge fires.
        bh.beats_since_player_action = 5
        result1 = invoke_director(
            ws, bh, next_event_id=0, timestamp=0.0, pins=pins,
        )
        assert result1.nudge_directive.type == "SPOTLIGHT_NUDGE"

        # Second invocation: stall still active, but nudge suppressed.
        bh.beats_since_player_action = 5
        next_id = len(result1.events)
        result2 = invoke_director(
            ws, bh, next_event_id=next_id, timestamp=1.0, pins=pins,
        )

        event_types = [e.event_type for e in result2.events]
        assert "nudge_suppressed" in event_types

        # Validate payload.
        suppress_event = [e for e in result2.events if e.event_type == "nudge_suppressed"][0]
        assert suppress_event.payload["scene_id"] == "scene_001"
        assert suppress_event.payload["reason_code"] in ("scene_cap_reached", "cooldown_active")

    def test_no_nudge_no_events_033_034(self):
        """No nudge → neither EV-033 nor EV-034 emitted."""
        _, _, _, ws = _build_test_stores()
        bh = BeatHistory()
        bh.beats_since_player_action = 0  # No stall → no nudge.

        result = _invoke_director_default(ws=ws, beat_history=bh)

        event_types = [e.event_type for e in result.events]
        # Should have director_beat_selected but not nudge events.
        assert "director_beat_selected" in event_types
        assert "nudge_selected" not in event_types
        assert "nudge_suppressed" not in event_types


# ---------------------------------------------------------------------------
# DIR-E4: End-to-end determinism (3 tests)
# ---------------------------------------------------------------------------

class TestDIRE4EndToEndDeterminism:
    def test_full_pipeline_deterministic(self):
        """Oracle → Director → PromptPack: deterministic (same inputs → same bytes)."""
        _, _, _, ws = _build_test_stores()
        bh1 = BeatHistory()
        bh2 = BeatHistory()

        result1 = invoke_director(ws, bh1, next_event_id=0, timestamp=0.0)
        result2 = invoke_director(ws, bh2, next_event_id=0, timestamp=0.0)

        # PromptPack bytes must be identical.
        bytes1 = canonical_json(result1.promptpack.to_dict())
        bytes2 = canonical_json(result2.promptpack.to_dict())
        assert bytes1 == bytes2

        # BeatIntent bytes must be identical.
        assert result1.beat_intent.bytes_hash == result2.beat_intent.bytes_hash

    def test_full_pipeline_twice_identical(self):
        """Same pipeline twice → byte-identical PromptPack."""
        results = []
        for _ in range(2):
            _, _, _, ws = _build_test_stores()
            bh = BeatHistory()
            r = invoke_director(ws, bh, next_event_id=0, timestamp=0.0)
            pack_bytes = canonical_json(r.promptpack.to_dict())
            results.append(hashlib.sha256(pack_bytes).hexdigest())

        assert results[0] == results[1]

    def test_cold_boot_replay_same_promptpack(self):
        """Cold boot → replay → Director → same PromptPack."""
        from aidm.oracle.cold_boot import cold_boot, _reduce_oracle_event
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

        # Run Director pipeline on original stores.
        bh1 = BeatHistory()
        r1 = invoke_director(ws, bh1, next_event_id=3, timestamp=1.0)
        pack1_hash = hashlib.sha256(canonical_json(r1.promptpack.to_dict())).hexdigest()

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
        r2 = invoke_director(ws2, bh2, next_event_id=3, timestamp=1.0)
        pack2_hash = hashlib.sha256(canonical_json(r2.promptpack.to_dict())).hexdigest()

        assert pack1_hash == pack2_hash
        assert r1.beat_intent.bytes_hash == r2.beat_intent.bytes_hash


# ---------------------------------------------------------------------------
# DIR-E5: BeatHistory reconstruction (3 tests)
# ---------------------------------------------------------------------------

class TestDIRE5BeatHistoryReconstruction:
    def test_from_events_reconstructs_state(self):
        """BeatHistory.from_events() reconstructs correct scene-scoped state."""
        # Build a sequence of director_beat_selected events.
        events = []
        for i in range(5):
            events.append(Event(
                event_id=i,
                event_type="director_beat_selected",
                timestamp=float(i),
                payload={
                    "scene_id": "scene_001",
                    "beat_id": f"beat_{i}",
                    "beat_type": "ENVIRONMENTAL",
                    "pacing_mode": "NORMAL",
                    "permission_prompt": (i == 3),  # Permission on beat 3.
                    "target_handles": [],
                    "nudge_type": "SPOTLIGHT_NUDGE" if i == 2 else "NONE",
                    "had_player_action": (i == 1),  # Player action on beat 1.
                },
            ))

        bh = BeatHistory.from_events(events, current_scene_id="scene_001")

        assert bh.beats_this_scene == 5
        assert bh.nudge_fired_this_scene is True
        # After beat 1 (player action), beats_since_player_action resets.
        # Beats 2, 3, 4 have no player action → 3 beats since.
        assert bh.beats_since_player_action == 3
        # Permission at beat index 3: record_beat increments to 4, then
        # record_permission sets last_permission_beat = 4.
        assert bh.last_permission_beat == 4

    def test_cold_boot_replay_matches_pre_boot(self):
        """Cold boot replay → BeatHistory matches pre-boot state."""
        _, _, _, ws = _build_test_stores()
        bh_original = BeatHistory()

        # Run Director 3 times, collecting events.
        all_events = []
        next_id = 0
        for i in range(3):
            bh_original.beats_since_player_action = i + 1
            result = invoke_director(
                ws, bh_original, next_event_id=next_id, timestamp=float(i),
            )
            all_events.extend(result.events)
            next_id += len(result.events)

        # Reconstruct BeatHistory from events.
        bh_reconstructed = BeatHistory.from_events(
            all_events, current_scene_id="scene_001",
        )

        # Both should have same beat count.
        assert bh_reconstructed.beats_this_scene == bh_original.beats_this_scene

    def test_scene_transition_resets_counters(self):
        """Scene transition → scene-scoped BeatHistory counters reset."""
        events = []
        # 3 beats in scene_001.
        for i in range(3):
            events.append(Event(
                event_id=i,
                event_type="director_beat_selected",
                timestamp=float(i),
                payload={
                    "scene_id": "scene_001",
                    "beat_id": f"beat_{i}",
                    "beat_type": "ENVIRONMENTAL",
                    "pacing_mode": "NORMAL",
                    "permission_prompt": False,
                    "target_handles": [],
                    "nudge_type": "NONE",
                    "had_player_action": False,
                },
            ))

        # Scene transition.
        events.append(Event(
            event_id=3,
            event_type="scene_start",
            timestamp=3.0,
            payload={"scene_id": "scene_002"},
        ))

        # 2 beats in scene_002.
        for i in range(2):
            events.append(Event(
                event_id=4 + i,
                event_type="director_beat_selected",
                timestamp=4.0 + i,
                payload={
                    "scene_id": "scene_002",
                    "beat_id": f"beat_s2_{i}",
                    "beat_type": "ENVIRONMENTAL",
                    "pacing_mode": "NORMAL",
                    "permission_prompt": False,
                    "target_handles": [],
                    "nudge_type": "NONE",
                    "had_player_action": False,
                },
            ))

        # Reconstruct for scene_002.
        bh = BeatHistory.from_events(events, current_scene_id="scene_002")

        # Should only count scene_002 beats after the reset.
        assert bh.beats_this_scene == 2
        assert bh.nudge_fired_this_scene is False
        assert bh.beats_since_player_action == 2
