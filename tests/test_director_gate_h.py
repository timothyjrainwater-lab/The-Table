"""Gate H tests — Director Phase 3: TableMood + StyleCapsule + Scene Lifecycle.

10 tests across 8 gate categories (DIR-H1a through DIR-H8).

Categories:
    DIR-H1a: No Mechanical Influence — static import scan (1 test)
    DIR-H1b: No Mechanical Influence — identical combat, different StyleCapsule (1 test)
    DIR-H2:  No Canon Writes — table_mood has no FactsLedger dependency (1 test)
    DIR-H3:  Determinism — same observations → same StyleCapsule → same pacing (1 test)
    DIR-H4:  Director backward compat — style_capsule=None produces same output (1 test)
    DIR-H5:  Scene lifecycle — scene_start resets Director beat counter (1 test)
    DIR-H6:  Cold boot reconstruction — mood events roundtrip through reducer (1 test)
    DIR-H7:  StyleCapsule compilation rules — signal → capsule mapping (1 test)
    DIR-H8:  Oracle boundary — table_mood.py in aidm/oracle/, no boundary violations (1 test)

Authority: WO-DIRECTOR-03, Director Spec v0 §9, MEMO_TABLE_MOOD_SUBSYSTEM.
"""
from __future__ import annotations

import hashlib
import os

import pytest

from aidm.core.event_log import Event, EventLog
from aidm.oracle.canonical import canonical_json, canonical_short_hash
from aidm.oracle.facts_ledger import FactsLedger, make_fact
from aidm.oracle.unlock_state import UnlockEntry, UnlockState
from aidm.oracle.story_state import StoryState, StoryStateLog
from aidm.oracle.table_mood import (
    MOOD_TAGS,
    MoodObservation,
    TableMoodStore,
    make_mood_observation,
)
from aidm.oracle.working_set import (
    CompilationPolicy,
    ScopeCursor,
    WorkingSet,
    compile_working_set,
)
from aidm.lens.style_capsule import StyleCapsule, compile_style_capsule
from aidm.lens.director.models import (
    BeatHistory,
    BeatIntent,
    DirectorPromptPack,
    compile_director_promptpack,
    make_beat_intent,
    make_nudge_directive,
)
from aidm.lens.director.policy import (
    DirectorPolicyPins,
    select_beat,
    select_beat_with_audit,
)
from aidm.lens.director.invoke import invoke_director


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


def _make_mood_obs(scene_id, tags, source="EXPLICIT_FEEDBACK",
                   event_id=0, confidence=None, evidence=None):
    """Shorthand helper for test mood observations."""
    return make_mood_observation(
        source=source,
        scope="SCENE",
        tags=tags,
        scene_id=scene_id,
        provenance_event_id=event_id,
        confidence=confidence,
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# DIR-H1a: No Mechanical Influence — static import scan
# ---------------------------------------------------------------------------

class TestDIRH1aNoMechanicalInfluenceStatic:
    def test_style_capsule_not_imported_in_core(self):
        """StyleCapsule fields do not appear in any Box input.

        Static scan: aidm/core/ must not import style_capsule.
        """
        core_dir = os.path.join(os.path.dirname(__file__), "..", "aidm", "core")
        core_dir = os.path.normpath(core_dir)

        violations = []
        if os.path.isdir(core_dir):
            for root, _dirs, files in os.walk(core_dir):
                for fname in files:
                    if not fname.endswith(".py"):
                        continue
                    fpath = os.path.join(root, fname)
                    with open(fpath, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    if "style_capsule" in content or "StyleCapsule" in content:
                        violations.append(fpath)

        assert violations == [], (
            f"StyleCapsule imported in aidm/core/: {violations}"
        )


# ---------------------------------------------------------------------------
# DIR-H1b: No Mechanical Influence — identical combat, different capsules
# ---------------------------------------------------------------------------

class TestDIRH1bNoMechanicalInfluenceBehavioral:
    def test_different_style_capsules_same_box_output(self):
        """Identical combat scenario, different StyleCapsules → same Box outputs.

        Box (attack_resolver, save_resolver) must not be influenced by
        StyleCapsule.  We verify by running the Director pipeline with two
        different capsules and asserting the PromptPack's mechanical
        sections (if any) are identical.
        """
        _, _, _, ws = _build_test_stores()

        capsule_push = StyleCapsule(pacing_mode="push", target_beat_length="short")
        capsule_normal = StyleCapsule(pacing_mode="normal")

        bh1 = BeatHistory()
        bh2 = BeatHistory()

        r1 = invoke_director(ws, bh1, next_event_id=0, timestamp=0.0,
                             style_capsule=capsule_push)
        r2 = invoke_director(ws, bh2, next_event_id=0, timestamp=0.0,
                             style_capsule=capsule_normal)

        # The PromptPack mechanical content (world data, entity data)
        # must be identical. Only style/pacing may differ.
        pack1 = r1.promptpack.to_dict()
        pack2 = r2.promptpack.to_dict()

        # Truth, memory, contract — all mechanical content is the same.
        assert pack1["truth"] == pack2["truth"]
        assert pack1["memory"] == pack2["memory"]
        assert pack1["contract"] == pack2["contract"]


# ---------------------------------------------------------------------------
# DIR-H2: No Canon Writes — TableMoodStore has no FactsLedger dependency
# ---------------------------------------------------------------------------

class TestDIRH2NoCanonWrites:
    def test_table_mood_no_facts_ledger_import(self):
        """table_mood.py does not import from facts_ledger.

        Static scan proves TableMoodStore cannot write to FactsLedger.
        """
        table_mood_path = os.path.join(
            os.path.dirname(__file__), "..", "aidm", "oracle", "table_mood.py"
        )
        table_mood_path = os.path.normpath(table_mood_path)

        with open(table_mood_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        assert "facts_ledger" not in content, (
            "table_mood.py imports from facts_ledger — no canon writes allowed"
        )
        assert "FactsLedger" not in content, (
            "table_mood.py references FactsLedger — no canon writes allowed"
        )


# ---------------------------------------------------------------------------
# DIR-H3: Determinism — same observations → same StyleCapsule bytes
# ---------------------------------------------------------------------------

class TestDIRH3Determinism:
    def test_same_observations_same_capsule_same_pacing(self):
        """Same mood observations → same StyleCapsule → same BeatIntent pacing.

        Run twice, assert byte-equal at every stage.
        """
        obs1 = _make_mood_obs("scene_001", ("bored",), event_id=1)
        obs2 = _make_mood_obs("scene_001", ("frustrated",), event_id=2)

        # Run compilation twice.
        capsule_a = compile_style_capsule([obs1, obs2], "scene_001")
        capsule_b = compile_style_capsule([obs1, obs2], "scene_001")

        # StyleCapsule must be byte-identical.
        bytes_a = canonical_json(capsule_a.to_dict())
        bytes_b = canonical_json(capsule_b.to_dict())
        assert bytes_a == bytes_b

        # Feed through Director pipeline.
        _, _, _, ws = _build_test_stores()
        bh1 = BeatHistory()
        bh2 = BeatHistory()

        dpp1 = compile_director_promptpack(ws, bh1, style_capsule=capsule_a)
        dpp2 = compile_director_promptpack(ws, bh2, style_capsule=capsule_b)

        assert dpp1.bytes_hash == dpp2.bytes_hash

        result1 = select_beat(dpp1, bh1)
        result2 = select_beat(dpp2, bh2)

        assert result1[0].bytes_hash == result2[0].bytes_hash
        assert result1[0].pacing_mode == result2[0].pacing_mode


# ---------------------------------------------------------------------------
# DIR-H4: Director backward compat — style_capsule=None unchanged
# ---------------------------------------------------------------------------

class TestDIRH4BackwardCompat:
    def test_none_style_capsule_same_as_phase2(self):
        """When style_capsule=None, Director produces identical output to Phase 2.

        Run Gate E scenarios without StyleCapsule, assert pass.
        """
        _, _, _, ws = _build_test_stores()
        bh1 = BeatHistory()
        bh2 = BeatHistory()

        # Without style_capsule (Phase 2 path).
        r1 = invoke_director(ws, bh1, next_event_id=0, timestamp=0.0)
        # Explicitly None (Phase 3 backward-compat path).
        r2 = invoke_director(ws, bh2, next_event_id=0, timestamp=0.0,
                             style_capsule=None)

        # Must produce byte-identical PromptPack.
        bytes1 = canonical_json(r1.promptpack.to_dict())
        bytes2 = canonical_json(r2.promptpack.to_dict())
        assert bytes1 == bytes2

        # BeatIntent must be identical.
        assert r1.beat_intent.bytes_hash == r2.beat_intent.bytes_hash

        # Pacing must be NORMAL (default).
        assert r1.beat_intent.pacing_mode == "NORMAL"
        assert r2.beat_intent.pacing_mode == "NORMAL"


# ---------------------------------------------------------------------------
# DIR-H5: Scene lifecycle — scene_start resets Director beat counter
# ---------------------------------------------------------------------------

class TestDIRH5SceneLifecycle:
    def test_scene_start_resets_beat_counter(self):
        """scene_start event resets Director beat counter.

        scene_end does not crash. BeatHistory.from_events() handles scene
        boundaries correctly.
        """
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

        # scene_end for scene_001.
        events.append(Event(
            event_id=3,
            event_type="scene_end",
            timestamp=3.0,
            payload={"scene_id": "scene_001", "reason": "transition"},
        ))

        # scene_start for scene_002.
        events.append(Event(
            event_id=4,
            event_type="scene_start",
            timestamp=4.0,
            payload={"scene_id": "scene_002"},
        ))

        # 1 beat in scene_002.
        events.append(Event(
            event_id=5,
            event_type="director_beat_selected",
            timestamp=5.0,
            payload={
                "scene_id": "scene_002",
                "beat_id": "beat_s2_0",
                "beat_type": "ENVIRONMENTAL",
                "pacing_mode": "NORMAL",
                "permission_prompt": False,
                "target_handles": [],
                "nudge_type": "NONE",
                "had_player_action": False,
            },
        ))

        bh = BeatHistory.from_events(events, current_scene_id="scene_002")

        # Should only count scene_002 beats after the reset.
        assert bh.beats_this_scene == 1
        assert bh.nudge_fired_this_scene is False
        assert bh.beats_since_player_action == 1


# ---------------------------------------------------------------------------
# DIR-H6: Cold boot reconstruction — mood events roundtrip through reducer
# ---------------------------------------------------------------------------

class TestDIRH6ColdBootReconstruction:
    def test_mood_observation_cold_boot_roundtrip(self):
        """Construct TableMoodStore, serialize to events, cold boot,
        assert reconstructed store matches original.
        """
        from aidm.oracle.cold_boot import _reduce_oracle_event

        # Build original TableMoodStore.
        original_store = TableMoodStore()
        obs1 = make_mood_observation(
            source="EXPLICIT_FEEDBACK",
            scope="SCENE",
            tags=("fun", "engaged"),
            scene_id="scene_001",
            provenance_event_id=1,
        )
        obs2 = make_mood_observation(
            source="INFERRED_SIGNAL",
            scope="SCENE",
            tags=("confused",),
            scene_id="scene_001",
            provenance_event_id=2,
            confidence="medium",
        )
        original_store.append(obs1)
        original_store.append(obs2)

        original_digest = original_store.digest()

        # Serialize to events.
        event_log = EventLog()
        event_log.append(Event(
            event_id=0, event_type="oracle_story_init", timestamp=0,
            payload={"campaign_id": "test", "scene_id": "scene_001"},
        ))
        event_log.append(Event(
            event_id=1, event_type="mood_observation", timestamp=1.0,
            payload=obs1.to_dict(),
        ))
        event_log.append(Event(
            event_id=2, event_type="mood_observation", timestamp=2.0,
            payload=obs2.to_dict(),
        ))

        # Cold boot replay — reconstruct TableMoodStore.
        fl = FactsLedger()
        us = UnlockState()
        ssl = None
        reconstructed_store = TableMoodStore()

        for ev in event_log.events:
            ssl = _reduce_oracle_event(fl, us, ssl, ev,
                                       table_mood_store=reconstructed_store)

        # Digests must match.
        assert reconstructed_store.digest() == original_digest
        assert len(reconstructed_store) == 2

        # Verify individual observations roundtripped.
        all_obs = reconstructed_store.all_observations()
        assert all_obs[0].observation_id == obs1.observation_id
        assert all_obs[1].observation_id == obs2.observation_id
        assert all_obs[1].confidence == "medium"


# ---------------------------------------------------------------------------
# DIR-H7: StyleCapsule compilation rules — signal → capsule mapping
# ---------------------------------------------------------------------------

class TestDIRH7CompilationRules:
    def test_confusion_signals_recap_needed(self):
        """Confusion markers in last 3 observations → recap_needed=True."""
        obs = _make_mood_obs("s1", ("confused",), event_id=1)
        capsule = compile_style_capsule([obs], "s1")
        assert capsule.recap_needed is True

    def test_fun_signals_humor_window(self):
        """Laughter/fun markers in last 3 → humor_window=True."""
        obs = _make_mood_obs("s1", ("fun",), event_id=1)
        capsule = compile_style_capsule([obs], "s1")
        assert capsule.humor_window is True

    def test_bored_signals_push(self):
        """Bored signals → pacing_mode='push'."""
        obs = _make_mood_obs("s1", ("bored",), event_id=1)
        capsule = compile_style_capsule([obs], "s1")
        assert capsule.pacing_mode == "push"
        assert capsule.target_beat_length == "short"

    def test_frustrated_signals_push(self):
        """Frustrated signals → pacing_mode='push'."""
        obs = _make_mood_obs("s1", ("frustrated",), event_id=1)
        capsule = compile_style_capsule([obs], "s1")
        assert capsule.pacing_mode == "push"

    def test_engaged_signals_normal(self):
        """Engaged signals → pacing_mode='normal'."""
        obs = _make_mood_obs("s1", ("engaged",), event_id=1)
        capsule = compile_style_capsule([obs], "s1")
        assert capsule.pacing_mode == "normal"

    def test_engaged_overrides_bored(self):
        """Engaged overrides bored/frustrated → pacing_mode='normal'."""
        obs1 = _make_mood_obs("s1", ("bored",), event_id=1)
        obs2 = _make_mood_obs("s1", ("engaged",), event_id=2)
        capsule = compile_style_capsule([obs1, obs2], "s1")
        assert capsule.pacing_mode == "normal"

    def test_no_signals_defaults(self):
        """No signals → all defaults."""
        capsule = compile_style_capsule([], "s1")
        assert capsule.target_beat_length == "medium"
        assert capsule.recap_needed is False
        assert capsule.humor_window is False
        assert capsule.pacing_mode == "normal"


# ---------------------------------------------------------------------------
# DIR-H8: Oracle boundary — table_mood.py in aidm/oracle/
# ---------------------------------------------------------------------------

class TestDIRH8OracleBoundary:
    def test_table_mood_in_oracle_package(self):
        """table_mood.py is in aidm/oracle/ — no new aidm/ package created."""
        table_mood_path = os.path.join(
            os.path.dirname(__file__), "..", "aidm", "oracle", "table_mood.py"
        )
        table_mood_path = os.path.normpath(table_mood_path)
        assert os.path.isfile(table_mood_path), (
            f"table_mood.py not found at expected Oracle path: {table_mood_path}"
        )

    def test_no_backflow_from_table_mood(self):
        """table_mood.py does not import from aidm/spark/, aidm/immersion/,
        or aidm/voice/.
        """
        table_mood_path = os.path.join(
            os.path.dirname(__file__), "..", "aidm", "oracle", "table_mood.py"
        )
        table_mood_path = os.path.normpath(table_mood_path)

        with open(table_mood_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        for forbidden in ("aidm.spark", "aidm.immersion", "aidm.voice",
                          "aidm/spark", "aidm/immersion", "aidm/voice"):
            assert forbidden not in content, (
                f"Backflow violation: table_mood.py imports from {forbidden}"
            )
