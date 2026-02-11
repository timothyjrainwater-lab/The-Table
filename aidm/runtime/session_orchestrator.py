"""WO-039: Session Orchestrator — Full Turn Cycle Conductor

Wires all subsystems into a playable turn loop:
STT → Intent Bridge → Box Resolution → NarrativeBrief → Spark Narration → TTS

This is the central conductor that connects Phase 1-3 components.
It does NOT replace RuntimeSession — it wraps it and connects surrounding
subsystems (STT, TTS, IntentBridge, SceneManager, DMPersona, narration).

TURN CYCLE:
1. INPUT: audio → STT → text (or text directly)
2. PARSE: text → declared intent (keyword-based, NOT NLU)
3. BRIDGE: IntentBridge → engine intent or ClarificationRequest
4. RESOLVE: RuntimeSession → EngineResult + events
5. BRIEF: NarrativeBrief from events + FrozenWorldStateView
6. NARRATE: DMPersona + GuardedNarrationService → narration text
7. VOICE: TTSAdapter → audio output

ERROR RECOVERY:
- STT failure → text input fallback
- Bridge ambiguity → ClarificationRequest with candidates
- Spark failure → template narration
- TTS failure → text-only output
- No turn ever stalls.

BOUNDARY LAWS:
- BL-020: FrozenWorldStateView for all reads outside engine resolution
- BL-003: Imports adapters by protocol, not concrete implementations
- Axiom 2: Narration output has zero mechanical authority
- Axiom 5: No Spark→State writes; one-way valve via NarrativeBrief

Reference: docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md (WO-039)
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable

from aidm.core.state import FrozenWorldStateView, WorldState
from aidm.interaction.intent_bridge import (
    AmbiguityType,
    ClarificationRequest,
    IntentBridge,
)
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.narrative_brief import NarrativeBrief
from aidm.lens.scene_manager import SceneManager, SceneState
from aidm.narration.guarded_narration_service import (
    FrozenMemorySnapshot,
    GuardedNarrationService,
    NarrationRequest,
    NarrationResult,
)
from aidm.schemas.engine_result import EngineResult, EngineResultStatus
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import CastSpellIntent, DeclaredAttackIntent, MoveIntent
from aidm.schemas.position import Position
from aidm.spark.dm_persona import DMPersona

logger = logging.getLogger(__name__)


# ======================================================================
# PROTOCOLS — Adapter interfaces (BL-003: protocol, not concrete)
# ======================================================================


@runtime_checkable
class STTProtocol(Protocol):
    """Speech-to-text adapter protocol."""

    def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> Any: ...
    def is_available(self) -> bool: ...


@runtime_checkable
class TTSProtocol(Protocol):
    """Text-to-speech adapter protocol."""

    def synthesize(self, text: str, persona: Optional[Any] = None) -> bytes: ...
    def is_available(self) -> bool: ...


@runtime_checkable
class ImageProtocol(Protocol):
    """Image generation adapter protocol."""

    def is_available(self) -> bool: ...


# ======================================================================
# SESSION STATE
# ======================================================================


class SessionState(str, Enum):
    """Current session mode."""

    EXPLORATION = "exploration"
    COMBAT = "combat"
    REST = "rest"
    DIALOGUE = "dialogue"


# ======================================================================
# TURN RESULT
# ======================================================================


@dataclass(frozen=True)
class TurnResult:
    """Immutable result of a single turn cycle.

    Contains everything the caller needs: narration text/audio,
    events generated, clarification requests, and error info.
    """

    success: bool
    narration_text: str
    narration_audio: Optional[bytes] = None
    events: Tuple[Dict[str, Any], ...] = ()
    clarification_needed: bool = False
    clarification_message: Optional[str] = None
    candidates: Optional[Tuple[str, ...]] = None
    provenance: str = "[NARRATIVE:TEMPLATE]"
    error_message: Optional[str] = None


# ======================================================================
# INTENT PARSER (keyword-based, NOT NLU)
# ======================================================================


@dataclass(frozen=True)
class ParsedCommand:
    """Result of keyword-based intent parsing."""

    command_type: str  # "attack", "spell", "move", "rest", "transition", "unknown"
    target_ref: Optional[str] = None
    weapon: Optional[str] = None
    spell_name: Optional[str] = None
    destination: Optional[Position] = None
    exit_id: Optional[str] = None
    rest_type: str = "8_hours"


def parse_text_command(text: str) -> ParsedCommand:
    """Parse player text into a structured command.

    Keyword-based parsing — NOT NLU. Recognizes structured commands:
    - "attack [target]" / "attack [target] with [weapon]"
    - "cast [spell]" / "cast [spell] on [target]" / "cast [spell] at [x],[y]"
    - "move to [x],[y]"
    - "rest" / "rest [type]"
    - "go [exit]" / "use [exit]"

    Args:
        text: Raw player input text

    Returns:
        ParsedCommand with extracted fields
    """
    text = text.strip()
    lower = text.lower()

    # Attack: "attack [target]" or "attack [target] with [weapon]"
    attack_match = re.match(
        r"(?:attack|hit|strike)\s+(.+?)(?:\s+with\s+(.+))?$", lower
    )
    if attack_match:
        target = attack_match.group(1).strip()
        weapon = attack_match.group(2).strip() if attack_match.group(2) else None
        return ParsedCommand(
            command_type="attack", target_ref=target, weapon=weapon
        )

    # Spell with position: "cast [spell] at [x],[y]"
    spell_pos_match = re.match(
        r"(?:cast)\s+(.+?)\s+at\s+(\d+)\s*,\s*(\d+)$", lower
    )
    if spell_pos_match:
        spell_name = spell_pos_match.group(1).strip()
        x = int(spell_pos_match.group(2))
        y = int(spell_pos_match.group(3))
        return ParsedCommand(
            command_type="spell",
            spell_name=spell_name,
            destination=Position(x=x, y=y),
        )

    # Spell with target: "cast [spell] on [target]"
    spell_target_match = re.match(
        r"(?:cast)\s+(.+?)\s+on\s+(.+)$", lower
    )
    if spell_target_match:
        spell_name = spell_target_match.group(1).strip()
        target = spell_target_match.group(2).strip()
        return ParsedCommand(
            command_type="spell", spell_name=spell_name, target_ref=target
        )

    # Spell (no target): "cast [spell]"
    spell_match = re.match(r"(?:cast)\s+(.+)$", lower)
    if spell_match:
        spell_name = spell_match.group(1).strip()
        return ParsedCommand(command_type="spell", spell_name=spell_name)

    # Move: "move to [x],[y]"
    move_match = re.match(r"(?:move|walk|run)\s+(?:to\s+)?(\d+)\s*,\s*(\d+)$", lower)
    if move_match:
        x = int(move_match.group(1))
        y = int(move_match.group(2))
        return ParsedCommand(
            command_type="move", destination=Position(x=x, y=y)
        )

    # Rest: "rest" or "rest [type]"
    rest_match = re.match(r"rest(?:\s+(8_hours|long_term_care|bed_rest))?$", lower)
    if rest_match:
        rest_type = rest_match.group(1) or "8_hours"
        return ParsedCommand(command_type="rest", rest_type=rest_type)

    # Scene transition: "go [exit]" or "use [exit]"
    go_match = re.match(r"(?:go|use|enter|exit|leave)\s+(.+)$", lower)
    if go_match:
        exit_id = go_match.group(1).strip()
        return ParsedCommand(command_type="transition", exit_id=exit_id)

    return ParsedCommand(command_type="unknown")


# ======================================================================
# SESSION ORCHESTRATOR
# ======================================================================


class SessionOrchestrator:
    """Conducts the full turn cycle: input → resolution → narration → output.

    Wires together all Phase 1-3 subsystems into a playable turn loop.
    Does NOT replace RuntimeSession — wraps it and connects the surrounding
    immersion, interaction, lens, and spark layers.
    """

    def __init__(
        self,
        world_state: WorldState,
        intent_bridge: IntentBridge,
        scene_manager: SceneManager,
        dm_persona: DMPersona,
        narration_service: GuardedNarrationService,
        context_assembler: ContextAssembler,
        stt_adapter: Optional[STTProtocol] = None,
        tts_adapter: Optional[TTSProtocol] = None,
        image_adapter: Optional[ImageProtocol] = None,
    ):
        """Initialize the session orchestrator.

        Args:
            world_state: Current world state (authoritative)
            intent_bridge: IntentBridge for name resolution
            scene_manager: SceneManager for scene transitions and rest
            dm_persona: DMPersona for system prompt construction
            narration_service: GuardedNarrationService for narration
            context_assembler: ContextAssembler for token-budgeted context
            stt_adapter: Optional STT adapter (None = text-only)
            tts_adapter: Optional TTS adapter (None = text-only)
            image_adapter: Optional image adapter
        """
        self._world_state = world_state
        self._intent_bridge = intent_bridge
        self._scene_manager = scene_manager
        self._dm_persona = dm_persona
        self._narration_service = narration_service
        self._context_assembler = context_assembler
        self._stt = stt_adapter
        self._tts = tts_adapter
        self._image = image_adapter

        self._session_state = SessionState.EXPLORATION
        self._current_scene_id: Optional[str] = None
        self._brief_history: List[NarrativeBrief] = []
        self._turn_count: int = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def session_state(self) -> SessionState:
        """Current session mode (exploration, combat, rest, dialogue)."""
        return self._session_state

    @property
    def current_scene_id(self) -> Optional[str]:
        """ID of the current scene, if any."""
        return self._current_scene_id

    @property
    def world_state(self) -> WorldState:
        """Current authoritative world state."""
        return self._world_state

    @property
    def brief_history(self) -> List[NarrativeBrief]:
        """Accumulated NarrativeBrief history for context assembly."""
        return list(self._brief_history)

    @property
    def turn_count(self) -> int:
        """Number of turns processed."""
        return self._turn_count

    # ------------------------------------------------------------------
    # Main Turn Cycle Entry Points
    # ------------------------------------------------------------------

    def process_voice_turn(self, audio_bytes: bytes, actor_id: str) -> TurnResult:
        """Process a voice input turn.

        Flow: audio → STT → text → process_text_turn()

        Args:
            audio_bytes: Raw audio from microphone
            actor_id: Entity ID of the acting player character

        Returns:
            TurnResult with narration and optional audio
        """
        # STT: audio → text
        if self._stt is None or not self._stt.is_available():
            return TurnResult(
                success=False,
                narration_text="",
                clarification_needed=True,
                clarification_message="Voice input unavailable. Please type your action.",
                provenance="[SYSTEM]",
            )

        try:
            transcript = self._stt.transcribe(audio_bytes)
            text = transcript.text if hasattr(transcript, "text") else str(transcript)
        except Exception as e:
            logger.warning("STT transcription failed: %s", e)
            return TurnResult(
                success=False,
                narration_text="",
                clarification_needed=True,
                clarification_message="Voice input failed. Please type your action.",
                provenance="[SYSTEM]",
                error_message=str(e),
            )

        return self.process_text_turn(text, actor_id)

    def process_text_turn(self, text_input: str, actor_id: str) -> TurnResult:
        """Process a text input turn.

        Flow: text → parse → bridge → resolve → narrate → TTS

        Args:
            text_input: Player text input
            actor_id: Entity ID of the acting player character

        Returns:
            TurnResult with narration and optional audio
        """
        self._turn_count += 1

        # 1. Parse text into structured command
        command = parse_text_command(text_input)

        if command.command_type == "unknown":
            return self._build_clarification_result(
                "I don't understand that command. Try: attack [target], "
                "cast [spell], move to [x,y], rest, or go [exit].",
                self._get_available_actions(),
            )

        # 2. Route by command type
        if command.command_type == "attack":
            return self._process_attack(actor_id, command)
        elif command.command_type == "spell":
            return self._process_spell(actor_id, command)
        elif command.command_type == "move":
            return self._process_move(actor_id, command)
        elif command.command_type == "rest":
            return self._process_rest(command)
        elif command.command_type == "transition":
            return self._process_transition(command)

        return self._build_clarification_result(
            "Unknown command type.", self._get_available_actions()
        )

    # ------------------------------------------------------------------
    # Command Processors
    # ------------------------------------------------------------------

    def _process_attack(self, actor_id: str, command: ParsedCommand) -> TurnResult:
        """Process an attack command through IntentBridge."""
        view = FrozenWorldStateView(self._world_state)
        declared = DeclaredAttackIntent(
            target_ref=command.target_ref or "",
            weapon=command.weapon,
        )

        result = self._intent_bridge.resolve_attack(actor_id, declared, view)

        if isinstance(result, ClarificationRequest):
            return self._build_clarification_result(
                result.message, list(result.candidates)
            )

        # Build a brief for this attack resolution
        target_entity = self._world_state.entities.get(result.target_id, {})
        target_name = target_entity.get("name", result.target_id)
        actor_entity = self._world_state.entities.get(actor_id, {})
        actor_name = actor_entity.get("name", actor_id)

        brief = NarrativeBrief(
            action_type="attack_declared",
            actor_name=actor_name,
            target_name=target_name,
            outcome_summary=f"{actor_name} attacks {target_name}",
            weapon_name=result.weapon.damage_type if result.weapon else None,
        )

        events = [
            {
                "type": "attack_declared",
                "attacker_id": actor_id,
                "target_id": result.target_id,
                "weapon": str(result.weapon) if result.weapon else "unarmed",
            }
        ]

        return self._narrate_and_output(brief, events)

    def _process_spell(self, actor_id: str, command: ParsedCommand) -> TurnResult:
        """Process a spell command through IntentBridge."""
        view = FrozenWorldStateView(self._world_state)
        declared = CastSpellIntent(spell_name=command.spell_name or "")

        kwargs = {}
        if command.target_ref:
            kwargs["target_entity_ref"] = command.target_ref
        if command.destination:
            kwargs["target_position"] = command.destination

        result = self._intent_bridge.resolve_spell(actor_id, declared, view, **kwargs)

        if isinstance(result, ClarificationRequest):
            return self._build_clarification_result(
                result.message, list(result.candidates)
            )

        actor_entity = self._world_state.entities.get(actor_id, {})
        actor_name = actor_entity.get("name", actor_id)

        brief = NarrativeBrief(
            action_type="spell_cast",
            actor_name=actor_name,
            outcome_summary=f"{actor_name} casts {result.spell_id}",
        )

        events = [
            {
                "type": "spell_cast",
                "caster_id": actor_id,
                "spell_id": result.spell_id,
            }
        ]

        return self._narrate_and_output(brief, events)

    def _process_move(self, actor_id: str, command: ParsedCommand) -> TurnResult:
        """Process a move command."""
        view = FrozenWorldStateView(self._world_state)
        declared = MoveIntent(destination=command.destination)

        result = self._intent_bridge.resolve_move(actor_id, declared, view)

        if isinstance(result, ClarificationRequest):
            return self._build_clarification_result(
                result.message, list(result.candidates) if result.candidates else []
            )

        actor_entity = self._world_state.entities.get(actor_id, {})
        actor_name = actor_entity.get("name", actor_id)
        dest = command.destination

        brief = NarrativeBrief(
            action_type="movement",
            actor_name=actor_name,
            outcome_summary=f"{actor_name} moves to ({dest.x}, {dest.y})" if dest else f"{actor_name} moves",
        )

        events = [
            {
                "type": "movement",
                "entity_id": actor_id,
                "destination_x": dest.x if dest else 0,
                "destination_y": dest.y if dest else 0,
            }
        ]

        return self._narrate_and_output(brief, events)

    def _process_rest(self, command: ParsedCommand) -> TurnResult:
        """Process rest through SceneManager."""
        from aidm.core.rng_manager import RNGManager

        self._session_state = SessionState.REST
        rng = RNGManager(master_seed=42)

        try:
            rest_result = self._scene_manager.process_rest(
                rest_type=command.rest_type,
                world_state=self._world_state,
                rng=rng,
            )
        except Exception as e:
            logger.warning("Rest processing failed: %s", e)
            self._session_state = SessionState.EXPLORATION
            return TurnResult(
                success=False,
                narration_text="",
                error_message=f"Rest failed: {e}",
                provenance="[SYSTEM]",
            )

        brief = NarrativeBrief(
            action_type="rest",
            actor_name="The party",
            outcome_summary=f"The party rests ({command.rest_type})",
        )

        self._session_state = SessionState.EXPLORATION
        return self._narrate_and_output(brief, rest_result.events)

    def _process_transition(self, command: ParsedCommand) -> TurnResult:
        """Process scene transition through SceneManager."""
        if self._current_scene_id is None:
            return TurnResult(
                success=False,
                narration_text="",
                error_message="No current scene. Load a scene first.",
                provenance="[SYSTEM]",
            )

        transition_result = self._scene_manager.transition_scene(
            from_scene=self._current_scene_id,
            exit_id=command.exit_id or "",
            world_state=self._world_state,
        )

        if not transition_result.success:
            return TurnResult(
                success=False,
                narration_text="",
                error_message=transition_result.error_message or "Transition failed",
                provenance="[SYSTEM]",
            )

        # Update current scene
        self._current_scene_id = transition_result.new_scene.scene_id

        brief = NarrativeBrief(
            action_type="scene_transition",
            actor_name="The party",
            outcome_summary=transition_result.narrative_hint or "The party moves on.",
            scene_description=transition_result.new_scene.description if transition_result.new_scene else None,
        )

        return self._narrate_and_output(brief, transition_result.events)

    # ------------------------------------------------------------------
    # Scene Management
    # ------------------------------------------------------------------

    def load_scene(self, scene_id: str) -> SceneState:
        """Load a scene and set it as current.

        Args:
            scene_id: Scene to load

        Returns:
            Loaded SceneState
        """
        scene = self._scene_manager.load_scene(scene_id)
        self._current_scene_id = scene_id
        return scene

    def enter_combat(self) -> None:
        """Transition session to combat state."""
        self._session_state = SessionState.COMBAT

    def exit_combat(self) -> None:
        """Transition session back to exploration state."""
        self._session_state = SessionState.EXPLORATION

    # ------------------------------------------------------------------
    # Narration Pipeline (Steps 5-7 of turn cycle)
    # ------------------------------------------------------------------

    def _narrate_and_output(
        self,
        brief: NarrativeBrief,
        events: List[Dict[str, Any]],
    ) -> TurnResult:
        """Assemble context, generate narration, synthesize TTS.

        Steps:
        5. Context assembly (ContextAssembler)
        6. System prompt (DMPersona) + narration (GuardedNarrationService)
        7. TTS synthesis (TTSAdapter)

        Args:
            brief: NarrativeBrief for this turn
            events: Box events generated

        Returns:
            Complete TurnResult
        """
        # Track brief history
        self._brief_history.append(brief)

        # 5. Context assembly
        session_context = self._context_assembler.assemble(
            brief, session_history=self._brief_history[:-1]
        )

        # 6. Narration generation
        narration_text, provenance = self._generate_narration(brief, session_context)

        # 7. TTS synthesis
        narration_audio = self._synthesize_tts(narration_text, brief)

        return TurnResult(
            success=True,
            narration_text=narration_text,
            narration_audio=narration_audio,
            events=tuple(events),
            provenance=provenance,
        )

    def _generate_narration(
        self, brief: NarrativeBrief, session_context: str
    ) -> Tuple[str, str]:
        """Generate narration text via Spark or template fallback.

        Args:
            brief: NarrativeBrief for context
            session_context: Assembled context string

        Returns:
            Tuple of (narration_text, provenance_tag)
        """
        # Build system prompt via DMPersona
        system_prompt = self._dm_persona.build_system_prompt(
            brief, session_context=session_context
        )

        # Build a minimal EngineResult for the narration service
        engine_result = EngineResult(
            result_id=f"turn_{self._turn_count}",
            intent_id=f"intent_{self._turn_count}",
            status=EngineResultStatus.SUCCESS,
            resolved_at=datetime.now(timezone.utc),
            narration_token=brief.action_type,
        )

        memory_snapshot = FrozenMemorySnapshot.create()
        world_state_hash = self._world_state.state_hash()

        request = NarrationRequest(
            engine_result=engine_result,
            memory_snapshot=memory_snapshot,
            temperature=0.8,
            world_state_hash=world_state_hash,
        )

        try:
            result: NarrationResult = self._narration_service.generate_narration(request)
            return result.text, result.provenance
        except Exception as e:
            logger.warning("Narration generation failed: %s", e)
            # Template fallback — use the brief's outcome_summary
            fallback = brief.outcome_summary or f"{brief.actor_name} acts."
            return fallback, "[NARRATIVE:TEMPLATE]"

    def _synthesize_tts(
        self, narration_text: str, brief: NarrativeBrief
    ) -> Optional[bytes]:
        """Synthesize TTS audio from narration text.

        Args:
            narration_text: Text to synthesize
            brief: NarrativeBrief for NPC voice selection

        Returns:
            Audio bytes or None if TTS unavailable
        """
        if self._tts is None or not self._tts.is_available():
            return None

        # Select voice persona based on actor
        persona = None
        if brief.actor_name:
            voice_id = self._dm_persona.get_npc_voice(brief.actor_name)
            if voice_id != self._dm_persona.default_voice:
                persona = voice_id

        try:
            return self._tts.synthesize(narration_text, persona=persona)
        except Exception as e:
            logger.warning("TTS synthesis failed: %s", e)
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_clarification_result(
        self, message: str, candidates: List[str]
    ) -> TurnResult:
        """Build a TurnResult requesting clarification."""
        return TurnResult(
            success=True,
            narration_text="",
            clarification_needed=True,
            clarification_message=message,
            candidates=tuple(candidates) if candidates else None,
            provenance="[SYSTEM]",
        )

    def _get_available_actions(self) -> List[str]:
        """Get list of available action types for the current state."""
        actions = ["attack [target]", "cast [spell]", "move to [x,y]"]
        if self._session_state == SessionState.EXPLORATION:
            actions.extend(["rest", "go [exit]"])
        return actions
