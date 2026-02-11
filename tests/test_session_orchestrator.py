"""WO-039: Session Orchestrator Tests

Validates the full turn cycle conductor:
- Text command parsing (keyword-based)
- Attack/spell/move turn cycles through IntentBridge
- Scene transitions and rest mechanics
- Voice input (STT) with fallback
- TTS output with fallback
- Error recovery at every stage
- Session state tracking
- Boundary law compliance (BL-020, Axiom 2)

Test Categories:
1. Command Parsing (8 tests)
2. Turn Cycle — Attack/Spell/Move (8 tests)
3. Scene Transitions and Rest (5 tests)
4. Error Recovery (7 tests)
5. Session State Tracking (5 tests)
6. Boundary Law Compliance (3 tests)

Total: 36 tests
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from aidm.runtime.session_orchestrator import (
    SessionOrchestrator,
    TurnResult,
    SessionState,
    ParsedCommand,
    parse_text_command,
)
from aidm.interaction.intent_bridge import (
    IntentBridge,
    ClarificationRequest,
    AmbiguityType,
)
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.narrative_brief import NarrativeBrief
from aidm.lens.scene_manager import (
    SceneManager,
    SceneState,
    Exit,
    TransitionResult,
    RestResult,
)
from aidm.narration.guarded_narration_service import (
    GuardedNarrationService,
    NarrationResult,
)
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.core.spell_resolver import SpellCastIntent
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
                EF.HP_CURRENT: 30,
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
                EF.HP_CURRENT: 6,
                EF.HP_MAX: 6,
                EF.AC: 15,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 2,
            },
        },
    )


@pytest.fixture
def multi_goblin_state():
    """World state with multiple goblins for ambiguity tests."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Kael",
                EF.TEAM: "party",
                EF.HP_CURRENT: 30,
                EF.HP_MAX: 50,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 5,
                EF.WEAPON: "longsword",
                "weapon_damage": "1d8+2",
            },
            "goblin_1": {
                EF.ENTITY_ID: "goblin_1",
                "name": "Goblin Warrior",
                EF.TEAM: "enemy",
                EF.DEFEATED: False,
            },
            "goblin_2": {
                EF.ENTITY_ID: "goblin_2",
                "name": "Goblin Scout",
                EF.TEAM: "enemy",
                EF.DEFEATED: False,
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
    """Create a SessionOrchestrator with all components wired."""
    return SessionOrchestrator(
        world_state=world_state,
        intent_bridge=IntentBridge(),
        scene_manager=scene_manager,
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
    )


@pytest.fixture
def mock_stt():
    """Mock STT adapter."""
    stt = MagicMock()
    stt.is_available.return_value = True
    transcript = MagicMock()
    transcript.text = "attack Goblin Warrior"
    stt.transcribe.return_value = transcript
    return stt


@pytest.fixture
def mock_tts():
    """Mock TTS adapter."""
    tts = MagicMock()
    tts.is_available.return_value = True
    tts.synthesize.return_value = b"\x00\x01\x02\x03"
    return tts


# ======================================================================
# CATEGORY 1: COMMAND PARSING (8 tests)
# ======================================================================


class TestCommandParsing:
    """Keyword-based command parsing (NOT NLU)."""

    def test_parse_attack(self):
        """'attack Goblin' parses to attack command."""
        cmd = parse_text_command("attack Goblin Warrior")
        assert cmd.command_type == "attack"
        assert cmd.target_ref == "goblin warrior"

    def test_parse_attack_with_weapon(self):
        """'attack Goblin with longsword' parses weapon."""
        cmd = parse_text_command("attack Goblin with longsword")
        assert cmd.command_type == "attack"
        assert cmd.target_ref == "goblin"
        assert cmd.weapon == "longsword"

    def test_parse_cast_spell(self):
        """'cast fireball' parses to spell command."""
        cmd = parse_text_command("cast fireball")
        assert cmd.command_type == "spell"
        assert cmd.spell_name == "fireball"

    def test_parse_cast_spell_on_target(self):
        """'cast magic missile on Goblin' parses target."""
        cmd = parse_text_command("cast magic missile on Goblin")
        assert cmd.command_type == "spell"
        assert cmd.spell_name == "magic missile"
        assert cmd.target_ref == "goblin"

    def test_parse_cast_spell_at_position(self):
        """'cast fireball at 10,5' parses position."""
        cmd = parse_text_command("cast fireball at 10,5")
        assert cmd.command_type == "spell"
        assert cmd.spell_name == "fireball"
        assert cmd.destination == Position(x=10, y=5)

    def test_parse_move(self):
        """'move to 5,5' parses to move command."""
        cmd = parse_text_command("move to 5,5")
        assert cmd.command_type == "move"
        assert cmd.destination == Position(x=5, y=5)

    def test_parse_rest(self):
        """'rest' parses to rest command with default type."""
        cmd = parse_text_command("rest")
        assert cmd.command_type == "rest"
        assert cmd.rest_type == "8_hours"

    def test_parse_unknown(self):
        """Unknown input parses as 'unknown'."""
        cmd = parse_text_command("dance wildly")
        assert cmd.command_type == "unknown"


# ======================================================================
# CATEGORY 2: TURN CYCLE — ATTACK/SPELL/MOVE (8 tests)
# ======================================================================


class TestTurnCycle:
    """Full turn cycle through orchestrator."""

    def test_text_attack_full_cycle(self, orchestrator):
        """Text 'attack Goblin Warrior' → resolve → narrate → TurnResult."""
        result = orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        assert isinstance(result, TurnResult)
        assert result.success is True
        assert result.narration_text != ""
        assert len(result.events) > 0
        assert result.events[0]["type"] == "attack_declared"
        assert result.provenance in ("[NARRATIVE]", "[NARRATIVE:TEMPLATE]")

    def test_text_spell_full_cycle(self, orchestrator):
        """Text 'cast fireball at 10,5' → resolve → narrate."""
        result = orchestrator.process_text_turn("cast fireball at 10,5", "pc_fighter")

        assert result.success is True
        assert result.narration_text != ""
        assert result.events[0]["type"] == "spell_cast"
        assert result.events[0]["spell_id"] == "fireball"

    def test_text_move_turn(self, orchestrator):
        """Text 'move to 5,5' → move resolution."""
        result = orchestrator.process_text_turn("move to 5,5", "pc_fighter")

        assert result.success is True
        assert result.events[0]["type"] == "movement"
        assert result.events[0]["destination_x"] == 5
        assert result.events[0]["destination_y"] == 5

    def test_voice_attack_turn(self, orchestrator, mock_stt):
        """Audio → STT → 'attack Goblin Warrior' → resolve → narrate."""
        orchestrator._stt = mock_stt

        result = orchestrator.process_voice_turn(b"\x00\x01", "pc_fighter")

        assert result.success is True
        assert result.narration_text != ""
        mock_stt.transcribe.assert_called_once()

    def test_clarification_on_ambiguous_target(self, multi_goblin_state, scene_manager):
        """'attack Goblin' with 3 goblins → clarification."""
        orch = SessionOrchestrator(
            world_state=multi_goblin_state,
            intent_bridge=IntentBridge(),
            scene_manager=scene_manager,
            dm_persona=DMPersona(),
            narration_service=GuardedNarrationService(),
            context_assembler=ContextAssembler(),
        )

        result = orch.process_text_turn("attack Goblin", "pc_fighter")

        assert result.clarification_needed is True
        assert result.candidates is not None
        assert len(result.candidates) >= 2

    def test_clarification_on_unknown_target(self, orchestrator):
        """'attack Dragon' → clarification with available targets."""
        result = orchestrator.process_text_turn("attack Dragon", "pc_fighter")

        assert result.clarification_needed is True
        assert result.clarification_message is not None
        assert "Goblin Warrior" in result.candidates

    def test_unknown_command_returns_clarification(self, orchestrator):
        """'dance wildly' → clarification with available actions."""
        result = orchestrator.process_text_turn("dance wildly", "pc_fighter")

        assert result.clarification_needed is True
        assert "attack" in result.clarification_message.lower()

    def test_turn_result_immutable(self, orchestrator):
        """TurnResult is frozen (immutable)."""
        result = orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        with pytest.raises((AttributeError, TypeError)):
            result.success = False


# ======================================================================
# CATEGORY 3: SCENE TRANSITIONS AND REST (5 tests)
# ======================================================================


class TestSceneAndRest:
    """Scene transitions and rest through orchestrator."""

    def test_scene_transition_turn(self, orchestrator):
        """'go north' → SceneManager transition → narration."""
        orchestrator.load_scene("room_a")

        result = orchestrator.process_text_turn("go north", "pc_fighter")

        assert result.success is True
        assert orchestrator.current_scene_id == "room_b"
        assert result.narration_text != ""

    def test_transition_without_scene_fails(self, orchestrator):
        """Transition with no loaded scene returns error."""
        result = orchestrator.process_text_turn("go north", "pc_fighter")

        assert result.success is False
        assert "No current scene" in result.error_message

    def test_transition_invalid_exit(self, orchestrator):
        """Transition with invalid exit returns error."""
        orchestrator.load_scene("room_a")

        result = orchestrator.process_text_turn("go east", "pc_fighter")

        assert result.success is False

    def test_rest_turn(self, orchestrator):
        """'rest' → SceneManager rest → healing events."""
        result = orchestrator.process_text_turn("rest", "pc_fighter")

        assert result.success is True
        assert result.narration_text != ""

    def test_load_scene_sets_current(self, orchestrator):
        """load_scene() sets current_scene_id."""
        orchestrator.load_scene("room_a")
        assert orchestrator.current_scene_id == "room_a"

        orchestrator.load_scene("room_b")
        assert orchestrator.current_scene_id == "room_b"


# ======================================================================
# CATEGORY 4: ERROR RECOVERY (7 tests)
# ======================================================================


class TestErrorRecovery:
    """Error recovery at every subsystem level."""

    def test_stt_unavailable_returns_text_fallback(self, orchestrator):
        """STT unavailable → text fallback message."""
        # No STT adapter set
        result = orchestrator.process_voice_turn(b"\x00", "pc_fighter")

        assert result.success is False
        assert result.clarification_needed is True
        assert "type your action" in result.clarification_message.lower()

    def test_stt_failure_returns_text_fallback(self, orchestrator, mock_stt):
        """STT raises exception → text fallback."""
        mock_stt.transcribe.side_effect = RuntimeError("Whisper failed")
        orchestrator._stt = mock_stt

        result = orchestrator.process_voice_turn(b"\x00", "pc_fighter")

        assert result.success is False
        assert result.clarification_needed is True
        assert "failed" in result.clarification_message.lower()

    def test_tts_unavailable_returns_text_only(self, orchestrator):
        """TTS unavailable → narration_audio=None."""
        result = orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        assert result.success is True
        assert result.narration_text != ""
        assert result.narration_audio is None

    def test_tts_failure_returns_text_only(self, orchestrator, mock_tts):
        """TTS raises → narration_audio=None, text still works."""
        mock_tts.synthesize.side_effect = RuntimeError("Kokoro failed")
        orchestrator._tts = mock_tts

        result = orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        assert result.success is True
        assert result.narration_text != ""
        assert result.narration_audio is None

    def test_tts_available_returns_audio(self, orchestrator, mock_tts):
        """TTS available → narration_audio has bytes."""
        orchestrator._tts = mock_tts

        result = orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        assert result.success is True
        assert result.narration_audio is not None
        assert len(result.narration_audio) > 0

    def test_narration_provenance_template_tagged(self, orchestrator):
        """Template fallback tags provenance as [NARRATIVE:TEMPLATE]."""
        result = orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        # GuardedNarrationService with no LLM uses templates
        assert result.provenance in ("[NARRATIVE]", "[NARRATIVE:TEMPLATE]")

    def test_all_subsystems_down_still_returns(self, orchestrator):
        """With no STT, no Spark, no TTS — text in, template out, text only."""
        result = orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        assert result.success is True
        assert result.narration_text != ""
        assert result.narration_audio is None


# ======================================================================
# CATEGORY 5: SESSION STATE TRACKING (5 tests)
# ======================================================================


class TestSessionState:
    """Session state transitions."""

    def test_session_state_exploration_default(self, orchestrator):
        """New session starts in EXPLORATION."""
        assert orchestrator.session_state == SessionState.EXPLORATION

    def test_session_state_combat_on_enter(self, orchestrator):
        """enter_combat() transitions to COMBAT."""
        orchestrator.enter_combat()
        assert orchestrator.session_state == SessionState.COMBAT

    def test_session_state_exploration_after_combat(self, orchestrator):
        """exit_combat() returns to EXPLORATION."""
        orchestrator.enter_combat()
        assert orchestrator.session_state == SessionState.COMBAT

        orchestrator.exit_combat()
        assert orchestrator.session_state == SessionState.EXPLORATION

    def test_current_scene_tracks_transitions(self, orchestrator):
        """Scene transitions update current_scene_id."""
        orchestrator.load_scene("room_a")
        assert orchestrator.current_scene_id == "room_a"

        orchestrator.process_text_turn("go north", "pc_fighter")
        assert orchestrator.current_scene_id == "room_b"

    def test_session_history_accumulates(self, orchestrator):
        """Multiple turns build NarrativeBrief history."""
        assert len(orchestrator.brief_history) == 0

        orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")
        assert len(orchestrator.brief_history) == 1

        orchestrator.process_text_turn("cast fireball at 10,5", "pc_fighter")
        assert len(orchestrator.brief_history) == 2


# ======================================================================
# CATEGORY 6: BOUNDARY LAW COMPLIANCE (3 tests)
# ======================================================================


class TestBoundaryCompliance:
    """Boundary law enforcement."""

    def test_frozen_world_state_view_enforced(self, orchestrator):
        """Orchestrator uses FrozenWorldStateView for reads (BL-020)."""
        initial_hash = orchestrator.world_state.state_hash()

        # Process a turn
        orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        # World state should be unchanged (no mutations)
        assert orchestrator.world_state.state_hash() == initial_hash

    def test_no_state_mutation_during_narration(self, orchestrator):
        """World state hash unchanged after narration generation."""
        hash_before = orchestrator.world_state.state_hash()

        # Multiple turns should not mutate state
        orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")
        orchestrator.process_text_turn("cast fireball at 10,5", "pc_fighter")

        assert orchestrator.world_state.state_hash() == hash_before

    def test_narration_receives_narrative_brief_not_raw_state(self, orchestrator):
        """Narration gets NarrativeBrief, not raw state."""
        orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

        # Brief history should contain NarrativeBrief objects
        assert len(orchestrator.brief_history) == 1
        brief = orchestrator.brief_history[0]
        assert isinstance(brief, NarrativeBrief)

        # No entity IDs in brief
        assert "pc_fighter" not in brief.actor_name
        assert "goblin_1" not in (brief.target_name or "")
