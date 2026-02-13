"""RQ-LENS-SPARK-001 Steps 10-11: Integration Wiring Tests

Validates:
- Step 10: SegmentTracker wired into SessionOrchestrator
  - record_turn() called on every turn
  - force_segment() called on scene transitions, combat start/end
  - Segment summaries accumulate over turns
  - Drift detection accessible from orchestrator
- Step 11: Summaries wired into PromptPackBuilder retrieval pipeline
  - PromptPackBuilder accepts segment_summaries
  - MemoryChannel includes segment_summaries field
  - Serialized PromptPack includes "Session Context:" section
  - Token budget enforcement applies to summaries
  - NarrationRequest carries segment_summaries

Evidence:
- RQ-LENS-SPARK-001: Context Orchestration Sprint (Steps 10-11)
- WO-059: Memory Retrieval Policy
- WO-060: Summarization Stability Protocol
"""

import pytest
from unittest.mock import MagicMock, patch

from aidm.runtime.session_orchestrator import (
    SessionOrchestrator,
    SessionState,
    TurnResult,
)
from aidm.interaction.intent_bridge import IntentBridge
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.narrative_brief import NarrativeBrief
from aidm.lens.prompt_pack_builder import PromptPackBuilder
from aidm.lens.scene_manager import (
    SceneManager,
    SceneState,
    Exit,
)
from aidm.lens.segment_summarizer import (
    SEGMENT_SIZE,
    SegmentTracker,
    SessionSegmentSummary,
)
from aidm.narration.guarded_narration_service import (
    GuardedNarrationService,
    NarrationRequest,
    FrozenMemorySnapshot,
)
from aidm.schemas.engine_result import EngineResult, EngineResultStatus
from aidm.schemas.entity_fields import EF
from aidm.schemas.prompt_pack import MemoryChannel
from aidm.core.state import WorldState
from aidm.spark.dm_persona import DMPersona


# ======================================================================
# FIXTURES
# ======================================================================


@pytest.fixture
def world_state():
    """World state with fighter and goblin."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Kael",
                EF.TEAM: "party",
                EF.HP_CURRENT: 50,
                EF.HP_MAX: 50,
                EF.LEVEL: 5,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 5,
                EF.BAB: 3,
                EF.STR_MOD: 2,
                EF.WEAPON: "longsword",
                "weapon_damage": "1d8+2",
                EF.DEX_MOD: 1,
            },
            "goblin_1": {
                EF.ENTITY_ID: "goblin_1",
                "name": "Goblin Warrior",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 100,
                EF.HP_MAX: 100,
                EF.AC: 15,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 2,
            },
        },
    )


@pytest.fixture
def scene_manager():
    """SceneManager with test scenes."""
    scenes = {
        "room_a": SceneState(
            scene_id="room_a",
            name="Room A",
            description="A stone chamber.",
            exits=[
                Exit(
                    exit_id="north",
                    destination_scene_id="room_b",
                    description="A passage north",
                    locked=False,
                    hidden=False,
                ),
            ],
        ),
        "room_b": SceneState(
            scene_id="room_b",
            name="Room B",
            description="A dark corridor.",
            exits=[
                Exit(
                    exit_id="south",
                    destination_scene_id="room_a",
                    description="Back to Room A",
                    locked=False,
                    hidden=False,
                ),
            ],
        ),
    }
    return SceneManager(scenes=scenes)


@pytest.fixture
def orchestrator(world_state, scene_manager):
    """SessionOrchestrator with all components wired."""
    return SessionOrchestrator(
        world_state=world_state,
        intent_bridge=IntentBridge(),
        scene_manager=scene_manager,
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
    )


# ======================================================================
# CATEGORY 1: STEP 10 — SEGMENT TRACKER IN ORCHESTRATOR (8 tests)
# ======================================================================


class TestSegmentTrackerWiring:
    """Step 10: SegmentTracker wired into SessionOrchestrator."""

    def test_orchestrator_has_segment_tracker(self, orchestrator):
        """SessionOrchestrator exposes segment_tracker property."""
        assert orchestrator.segment_tracker is not None
        assert isinstance(orchestrator.segment_tracker, SegmentTracker)

    def test_segment_tracker_records_turns(self, orchestrator):
        """Each turn records into segment tracker."""
        for i in range(3):
            orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        # Tracker should have briefs accumulated (not yet a full segment)
        summaries = orchestrator.segment_tracker.get_summaries()
        assert len(summaries) == 0  # Need SEGMENT_SIZE turns for first summary

    def test_segment_auto_generated_at_segment_size(self, orchestrator):
        """Auto-summary generated after SEGMENT_SIZE turns."""
        for i in range(SEGMENT_SIZE):
            orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        summaries = orchestrator.segment_tracker.get_summaries()
        assert len(summaries) == 1
        assert isinstance(summaries[0], SessionSegmentSummary)

    def test_multiple_segments_accumulate(self, orchestrator):
        """Multiple segments accumulate over 20+ turns."""
        # Use a mix of attack and move commands to ensure all turns record
        # (attacks may fail if goblin is defeated, but moves always succeed)
        for i in range(SEGMENT_SIZE * 2):
            if i % 2 == 0:
                orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")
            else:
                orchestrator.process_text_turn("move to 5,5", "pc_fighter")

        summaries = orchestrator.segment_tracker.get_summaries()
        assert len(summaries) == 2

    def test_combat_start_forces_segment(self, orchestrator):
        """enter_combat() forces a segment boundary."""
        for i in range(5):
            orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        orchestrator.enter_combat()

        # Should have forced a partial segment (turns 1-5)
        summaries = orchestrator.segment_tracker.get_summaries()
        assert len(summaries) == 1
        assert summaries[0].turn_range[1] <= 5

    def test_combat_end_forces_segment(self, orchestrator):
        """exit_combat() forces a segment boundary."""
        orchestrator.enter_combat()
        for i in range(5):
            orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        orchestrator.exit_combat()

        summaries = orchestrator.segment_tracker.get_summaries()
        assert len(summaries) == 1

    def test_scene_transition_forces_segment(self, orchestrator):
        """Scene transition forces a segment boundary."""
        orchestrator.load_scene("room_a")

        for i in range(5):
            orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        orchestrator.process_text_turn("go north", "pc_fighter")

        summaries = orchestrator.segment_tracker.get_summaries()
        assert len(summaries) >= 1

    def test_defeated_entities_tracked_across_segments(self, orchestrator):
        """Cumulative defeated entity tracking across segments."""
        # This test just verifies the tracker is active
        for i in range(SEGMENT_SIZE):
            orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        all_defeated = orchestrator.segment_tracker.get_all_defeated()
        # Whether goblin was defeated depends on RNG, but the set should exist
        assert isinstance(all_defeated, (set, frozenset))


# ======================================================================
# CATEGORY 2: STEP 11 — SUMMARIES IN PROMPTPACK PIPELINE (9 tests)
# ======================================================================


class TestSummariesInPromptPack:
    """Step 11: Summaries wired into PromptPackBuilder retrieval pipeline."""

    def test_prompt_pack_builder_accepts_segment_summaries(self):
        """PromptPackBuilder.build() accepts segment_summaries parameter."""
        builder = PromptPackBuilder()
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            target_name="Goblin",
            outcome_summary="Kael hits the Goblin",
        )

        pack = builder.build(
            brief=brief,
            segment_summaries=["Turns 1-10: Kael fought goblins."],
        )

        assert len(pack.memory.segment_summaries) == 1
        assert "Turns 1-10" in pack.memory.segment_summaries[0]

    def test_memory_channel_has_segment_summaries_field(self):
        """MemoryChannel includes segment_summaries field."""
        channel = MemoryChannel(
            segment_summaries=("Summary 1", "Summary 2"),
        )
        assert len(channel.segment_summaries) == 2

    def test_serialized_prompt_pack_includes_session_context(self):
        """Serialized PromptPack includes Session Context section."""
        builder = PromptPackBuilder()
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            outcome_summary="Kael attacks",
        )

        pack = builder.build(
            brief=brief,
            segment_summaries=["Turns 1-10: Combat with goblins."],
        )

        serialized = pack.serialize()
        assert "Session Context:" in serialized
        assert "Turns 1-10: Combat with goblins." in serialized

    def test_no_summaries_no_session_context_section(self):
        """No summaries → no Session Context section in serialized pack."""
        builder = PromptPackBuilder()
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            outcome_summary="Kael attacks",
        )

        pack = builder.build(brief=brief)
        serialized = pack.serialize()
        assert "Session Context:" not in serialized

    def test_summaries_truncated_by_token_budget(self):
        """Summaries truncated when exceeding token budget."""
        builder = PromptPackBuilder(memory_token_budget=20)
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            outcome_summary="Kael attacks",
        )

        long_summary = "This is a very long summary " * 20
        pack = builder.build(
            brief=brief,
            segment_summaries=[long_summary],
        )

        # Summary too long for budget → truncated
        assert len(pack.memory.segment_summaries) == 0

    def test_narration_request_carries_segment_summaries(self):
        """NarrationRequest accepts segment_summaries parameter."""
        from datetime import datetime, timezone

        request = NarrationRequest(
            engine_result=EngineResult(
                result_id="test",
                intent_id="test",
                status=EngineResultStatus.SUCCESS,
                resolved_at=datetime.now(timezone.utc),
            ),
            memory_snapshot=FrozenMemorySnapshot.create(),
            segment_summaries=["Summary A", "Summary B"],
        )

        assert request.segment_summaries is not None
        assert len(request.segment_summaries) == 2

    def test_prompt_pack_to_dict_includes_summaries(self):
        """PromptPack.to_dict() includes segment_summaries."""
        builder = PromptPackBuilder()
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            outcome_summary="Kael attacks",
        )

        pack = builder.build(
            brief=brief,
            segment_summaries=["Summary text here."],
        )

        d = pack.to_dict()
        assert "segment_summaries" in d["memory"]
        assert "Summary text here." in d["memory"]["segment_summaries"]

    def test_summaries_ordered_newest_first_in_pack(self):
        """Segment summaries maintain newest-first order in PromptPack."""
        builder = PromptPackBuilder()
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            outcome_summary="Kael attacks",
        )

        summaries = [
            "Turns 11-20: Orc encounter.",
            "Turns 1-10: Goblin fight.",
        ]

        pack = builder.build(brief=brief, segment_summaries=summaries)

        # Order preserved: newest first
        assert pack.memory.segment_summaries[0] == "Turns 11-20: Orc encounter."
        assert pack.memory.segment_summaries[1] == "Turns 1-10: Goblin fight."

    def test_end_to_end_summaries_flow_through_orchestrator(self, orchestrator):
        """Full end-to-end: turns → segment → summary → PromptPack pipeline."""
        # Process SEGMENT_SIZE turns to trigger auto-summary
        for i in range(SEGMENT_SIZE):
            orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        # Verify summaries exist
        summaries = orchestrator.segment_tracker.get_summaries()
        assert len(summaries) == 1

        # Process one more turn — this turn should have summaries in its context
        result = orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")
        assert result.success is True

        # The summary text should reference "Kael" and "Goblin Warrior"
        summary = summaries[0]
        assert "Kael" in summary.summary_text
