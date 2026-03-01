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

from aidm.schemas.box_events import (
    AttackRollPayload,
    HPChangedPayload,
    EntityDefeatedPayload,
    validate_event_payload,
)

from aidm.core.play_loop import (
    execute_turn as box_execute_turn,
    TurnContext as BoxTurnContext,
    TurnResult as BoxTurnResult,
)
from play import run_enemy_turn as _play_run_enemy_turn  # WO-UI-PHASE1-ENEMY-LOOP-001: canonical enemy logic
from aidm.core.boundary_pressure import evaluate_pressure
from aidm.core.rng_manager import RNGManager
from aidm.core.spell_resolver import SpellCastIntent as BoxSpellCastIntent
from aidm.core.state import FrozenWorldStateView, WorldState
from aidm.interaction.intent_bridge import (
    AmbiguityType,
    ClarificationRequest,
    IntentBridge,
)
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.narrative_brief import NarrativeBrief, compute_severity
from aidm.lens.scene_manager import SceneManager, SceneState
from aidm.lens.segment_summarizer import SegmentTracker
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
from aidm.schemas.boundary_pressure import PressureLevel
from aidm.spark.dm_persona import DMPersona
from aidm.voice.line_classifier import filter_spoken_lines

from aidm.immersion.prosodic_preset_manager import ProsodicPresetManager
from aidm.schemas.immersion import VoicePersona

logger = logging.getLogger(__name__)

# WO-VOICE-PRESSURE-IMPL-001: Dedicated logger for boundary pressure events
bp_logger = logging.getLogger("aidm.boundary_pressure")

# WO-VOICE-PRESSURE-IMPL-001: PressureLevel -> logging level mapping
_PRESSURE_LOG_LEVELS = {
    PressureLevel.GREEN: logging.DEBUG,
    PressureLevel.YELLOW: logging.WARNING,
    PressureLevel.RED: logging.ERROR,
}


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


# WO-VOICE-PAS-PRESETS-001: SessionState -> prosodic preset mode
_SESSION_TO_PRESET_MODE = {
    SessionState.COMBAT: "combat",
    SessionState.EXPLORATION: "scene",
    SessionState.REST: "reflection",
    SessionState.DIALOGUE: "scene",
}


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

    command_type: str  # "attack", "spell", "move", "rest", "transition", "skill", "unknown"
    target_ref: Optional[str] = None
    weapon: Optional[str] = None
    spell_name: Optional[str] = None
    destination: Optional[Position] = None
    exit_id: Optional[str] = None
    rest_type: str = "8_hours"
    # WO-ENGINE-RETRY-002: skill check fields
    skill_name: Optional[str] = None
    take_10: bool = False
    take_20: bool = False
    dc: Optional[int] = None


def _normalize_skill(verb: str) -> str:
    """Map player-facing skill verbs to canonical SKILL_TIME_COSTS keys.

    WO-ENGINE-RETRY-002: Handles common player phrasings.
    """
    _MAP = {
        "search": "search",
        "look": "search",
        "examine": "search",
        "listen": "listen",
        "hear": "listen",
        "hide": "hide",
        "sneak": "move_silently",
        "move silently": "move_silently",
        "move_silently": "move_silently",
        "disable": "disable_device",
        "disable device": "disable_device",
        "disable_device": "disable_device",
        "pick lock": "open_lock",
        "open lock": "open_lock",
        "open_lock": "open_lock",
        "climb": "climb",
        "swim": "swim",
        "jump": "jump",
        "balance": "balance",
        "tumble": "tumble",
        "bluff": "bluff",
        "diplomacy": "diplomacy",
        "intimidate": "intimidate",
        "sense motive": "sense_motive",
        "sense_motive": "sense_motive",
        "gather information": "gather_information",
        "gather_information": "gather_information",
        "knowledge": "knowledge",
        "spellcraft": "spellcraft",
    }
    return _MAP.get(verb.lower(), verb.lower().replace(" ", "_"))


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

    # Take 10: "take 10 [on] [skill]" or "take ten [on] [skill]"
    take10_match = re.match(r"take\s+(?:10|ten)\s+(?:on\s+)?(.+)$", lower)
    if take10_match:
        raw = take10_match.group(1).strip()
        skill_name = _normalize_skill(raw)
        return ParsedCommand(command_type="skill", skill_name=skill_name, take_10=True)

    # Take 20: "take 20 [on] [skill]" or "take twenty [on] [skill]"
    take20_match = re.match(r"take\s+(?:20|twenty)\s+(?:on\s+)?(.+)$", lower)
    if take20_match:
        raw = take20_match.group(1).strip()
        skill_name = _normalize_skill(raw)
        return ParsedCommand(command_type="skill", skill_name=skill_name, take_20=True)

    # Skill check: recognized skill verbs
    _SKILL_VERBS = (
        r"search|listen|hide|sneak|climb|swim|jump|balance|tumble|bluff|diplomacy|"
        r"intimidate|knowledge|spellcraft|disable|pick\s+lock|open\s+lock|"
        r"move\s+silently|sense\s+motive|gather\s+information"
    )
    skill_match = re.match(
        r"(?P<verb>" + _SKILL_VERBS + r")(?:\s+.*)?$", lower
    )
    if skill_match:
        raw_verb = skill_match.group("verb").strip()
        skill_name = _normalize_skill(raw_verb)
        return ParsedCommand(command_type="skill", skill_name=skill_name)

    return ParsedCommand(command_type="unknown")


# ======================================================================
# TEMPLATE CONTEXT BUILDER (pure function, no RNG, no state mutation)
# ======================================================================


def _build_template_context(
    brief: NarrativeBrief,
    events: List[Dict[str, Any]],
) -> Dict[str, str]:
    """Build a deterministic template context dict from NarrativeBrief + events.

    This is the single point where brief fields map to template placeholders.
    Templates only claim what's in this context — no fabrication.

    Args:
        brief: NarrativeBrief with actor/target/weapon/severity data
        events: Box event dicts for damage extraction

    Returns:
        Dict with keys matching template placeholders:
        actor_name, target_name, weapon_name, damage, damage_type
    """
    # Extract damage from hp_changed events (authoritative source)
    damage = ""
    for e in events:
        etype = e.get("type", "")
        if etype == "hp_changed":
            delta = e.get("delta", 0)
            if delta < 0:
                damage = str(abs(delta))
                break

    return {
        "actor_name": brief.actor_name or "",
        "target_name": brief.target_name or "",
        "weapon_name": brief.weapon_name or "",
        "damage": damage,
        "damage_type": brief.damage_type or "",
        "severity": brief.severity or "minor",
        "target_defeated": "true" if brief.target_defeated else "",
    }


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
        rng: Optional[RNGManager] = None,
        master_seed: int = 42,
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
            rng: Optional RNGManager for deterministic resolution (created from master_seed if None)
            master_seed: RNG seed used if rng is None
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
        self._rng = rng if rng is not None else RNGManager(master_seed)
        self._stt = stt_adapter
        self._tts = tts_adapter
        self._image = image_adapter

        self._session_state = SessionState.EXPLORATION
        self._current_scene_id: Optional[str] = None
        self._brief_history: List[NarrativeBrief] = []
        self._turn_count: int = 0
        self._initiative_index: int = 0  # WO-UI-PHASE1-ENEMY-LOOP-001: cursor into active_combat[initiative_order]
        self._segment_tracker = SegmentTracker()
        self._preset_manager = ProsodicPresetManager()

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

    @property
    def segment_tracker(self) -> SegmentTracker:
        """Segment tracker for WO-060 session summaries and drift detection."""
        return self._segment_tracker

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
            # WO-JUDGMENT-SHADOW-001: Routing hook - classify and log unroutable action.
            # Phase 0: all unknowns -> impossible_or_clarify / escalate. No LLM. No engine mutation.
            from aidm.schemas.ruling_artifact import RulingArtifactShadow
            from aidm.core.ruling_validator import validate_ruling_artifact

            _clarify_msg = (
                "I don't understand that command. Try: attack [target], "
                "cast [spell], move to [x,y], rest, or go [exit]."
            )
            _artifact = RulingArtifactShadow(
                player_action_raw=text_input,
                route_class="impossible_or_clarify",
                routing_confidence="escalate",
                clarification_message=_clarify_msg,
            )
            _verdict, _reasons = validate_ruling_artifact(_artifact)
            _artifact.validator_verdict = _verdict
            _artifact.validator_reasons = _reasons
            self._log_shadow_ruling(_artifact)  # non-canonical, log-only

            return self._build_clarification_result(
                _clarify_msg,
                self._get_available_actions(),
            )

        # 2. Route by command type
        # WO-UI-PHASE1-ENEMY-LOOP-001: each branch captures player result, then
        # runs _run_enemy_loop() to advance initiative and process all monster turns.
        _player_result: Optional["TurnResult"] = None
        if command.command_type == "attack":
            _player_result = self._process_attack(actor_id, command)
        elif command.command_type == "spell":
            _player_result = self._process_spell(actor_id, command)
        elif command.command_type == "move":
            _player_result = self._process_move(actor_id, command)
        elif command.command_type == "rest":
            _player_result = self._process_rest(command)
        elif command.command_type == "transition":
            _player_result = self._process_transition(command)
        elif command.command_type == "skill":
            _player_result = self._process_skill(actor_id, command)
        if _player_result is not None:
            return self._run_enemy_loop(_player_result, actor_id)

        return self._build_clarification_result(
            "Unknown command type.", self._get_available_actions()
        )

    def _run_enemy_loop(self, player_result: "TurnResult", actor_id: str = "") -> "TurnResult":
        """Run all consecutive enemy turns after the player acts.

        WO-UI-PHASE1-ENEMY-LOOP-001: Delegates to play.run_enemy_turn() (canonical).
        Does NOT reimplement target selection or attack resolution.

        After the player resolves, advances the initiative cursor and runs every
        monster turn sequentially until the cursor returns to a player actor (or
        combat ends). All accumulated events are merged into the returned TurnResult.
        """
        if not player_result.success:
            return player_result

        ws = self._world_state
        active = ws.active_combat if ws.active_combat else {}
        initiative_order = active.get("initiative_order", [])

        if not initiative_order:
            return player_result  # no combat active

        n = len(initiative_order)
        all_enemy_event_dicts: List[Dict[str, Any]] = []

        # Find acting player in initiative order and advance cursor past them
        if actor_id and actor_id in initiative_order:
            self._initiative_index = (initiative_order.index(actor_id) + 1) % n
        else:
            self._initiative_index = (self._initiative_index + 1) % n

        # Run consecutive monster turns until we hit a player actor (or loop completes)
        steps = 0
        while steps < n:
            actor_id = initiative_order[self._initiative_index]
            entity = ws.entities.get(actor_id, {})

            # Skip defeated actors
            if entity.get(EF.DEFEATED, False):
                self._initiative_index = (self._initiative_index + 1) % n
                steps += 1
                continue

            # Stop when we reach a player actor
            if entity.get(EF.TEAM, "monsters") != "monsters":
                break

            # Guard: if all enemies defeated, break (termination guard - EL-007)
            enemies_alive = [
                eid for eid, e in ws.entities.items()
                if e.get(EF.TEAM) == "monsters" and not e.get(EF.DEFEATED, False)
            ]
            if not enemies_alive:
                break

            # Delegate to canonical enemy logic (EL-008: no reimplementation here)
            enemy_box_result = _play_run_enemy_turn(
                ws=ws,
                actor_id=actor_id,
                seed=self._rng._master_seed,
                turn_index=self._turn_count,
                next_event_id=self._turn_count * 100 + len(all_enemy_event_dicts),
            )

            # Update authoritative world state from enemy turn result
            if enemy_box_result.status == "ok":
                ws = enemy_box_result.world_state
                self._world_state = ws
                self._turn_count += 1

                for ev in enemy_box_result.events:
                    ev_dict = {"type": ev.event_type, **ev.payload}
                    # Normalise event_type field for ws_bridge compatibility
                    ev_dict["event_type"] = ev.event_type
                    all_enemy_event_dicts.append(ev_dict)

            self._initiative_index = (self._initiative_index + 1) % n
            steps += 1

        if not all_enemy_event_dicts:
            return player_result

        # Merge enemy events into player result
        merged_events = tuple(player_result.events) + tuple(all_enemy_event_dicts)
        return TurnResult(
            success=player_result.success,
            narration_text=player_result.narration_text,
            narration_audio=player_result.narration_audio,
            events=merged_events,
            clarification_needed=player_result.clarification_needed,
            clarification_message=player_result.clarification_message,
            candidates=player_result.candidates,
            provenance=player_result.provenance,
            error_message=player_result.error_message,
        )

    # ------------------------------------------------------------------
    # Command Processors
    # ------------------------------------------------------------------

    def _process_attack(self, actor_id: str, command: ParsedCommand) -> TurnResult:
        """Process an attack command through IntentBridge → Box resolution.

        Flow: IntentBridge (name → entity ID) → execute_turn (d20 + damage) → NarrativeBrief
        """
        view = FrozenWorldStateView(self._world_state)
        declared = DeclaredAttackIntent(
            target_ref=command.target_ref or "",
            weapon=command.weapon,
        )

        bridge_result = self._intent_bridge.resolve_attack(actor_id, declared, view)

        if isinstance(bridge_result, ClarificationRequest):
            return self._build_clarification_result(
                bridge_result.message, list(bridge_result.candidates)
            )

        # Bridge succeeded — we have an AttackIntent with entity IDs and Weapon
        # Now route through Box (play_loop.execute_turn) for actual combat resolution
        actor_entity = self._world_state.entities.get(actor_id, {})
        actor_name = actor_entity.get("name", actor_id)
        target_entity = self._world_state.entities.get(bridge_result.target_id, {})
        target_name = target_entity.get("name", bridge_result.target_id)
        target_hp_before = target_entity.get(EF.HP_CURRENT, 0)
        target_hp_max = target_entity.get(EF.HP_MAX, 1)

        turn_ctx = BoxTurnContext(
            turn_index=self._turn_count,
            actor_id=actor_id,
            actor_team=actor_entity.get(EF.TEAM, "party"),
        )

        try:
            box_result = box_execute_turn(
                world_state=self._world_state,
                turn_ctx=turn_ctx,
                combat_intent=bridge_result,  # AttackIntent from IntentBridge
                rng=self._rng,
                next_event_id=self._turn_count * 100,
                timestamp=float(self._turn_count),
            )
        except Exception as e:
            logger.error("Box resolution failed during attack: %s", e)
            return TurnResult(
                success=False,
                narration_text="",
                error_message=f"Combat resolution failed: {e}",
                provenance="[SYSTEM]",
            )

        # Update authoritative world state from Box result
        self._world_state = box_result.world_state

        # Extract outcome from Box events via validated contracts
        hit = False
        damage = 0
        target_defeated = False
        event_dicts = []

        for event in box_result.events:
            event_dict = {
                "type": event.event_type,
                **event.payload,
            }
            event_dicts.append(event_dict)

            # Validate and extract typed payloads at the boundary
            validated = validate_event_payload(event.event_type, event.payload)

            if isinstance(validated, AttackRollPayload):
                hit = validated.hit
            elif isinstance(validated, HPChangedPayload):
                damage = abs(validated.delta)
            elif isinstance(validated, EntityDefeatedPayload):
                eid = validated.entity_id
                if eid == bridge_result.target_id:
                    target_defeated = True

        # Build NarrativeBrief from real outcome
        if hit:
            severity = compute_severity(damage, target_hp_before, target_hp_max, target_defeated)
            if target_defeated:
                outcome = f"{actor_name} strikes {target_name} for {damage} damage, defeating them"
            else:
                outcome = f"{actor_name} hits {target_name} for {damage} damage"
            action_type = "attack_hit"
        else:
            severity = "minor"
            outcome = f"{actor_name}'s attack misses {target_name}"
            action_type = "attack_miss"

        brief = NarrativeBrief(
            action_type=action_type,
            actor_name=actor_name,
            target_name=target_name,
            outcome_summary=outcome,
            severity=severity,
            weapon_name=actor_entity.get(EF.WEAPON, bridge_result.weapon.damage_type if bridge_result.weapon else None),
            damage_type=bridge_result.weapon.damage_type if bridge_result.weapon else None,
            target_defeated=target_defeated,
            source_event_ids=[e.event_id for e in box_result.events],
        )

        return self._narrate_and_output(brief, event_dicts)

    def _process_spell(self, actor_id: str, command: ParsedCommand) -> TurnResult:
        """Process a spell command through IntentBridge → Box resolution.

        Flow: IntentBridge (name → spell ID + target) → execute_turn (saves + effects) → NarrativeBrief
        """
        view = FrozenWorldStateView(self._world_state)
        declared = CastSpellIntent(spell_name=command.spell_name or "")

        kwargs = {}
        if command.target_ref:
            kwargs["target_entity_ref"] = command.target_ref
        if command.destination:
            kwargs["target_position"] = command.destination

        bridge_result = self._intent_bridge.resolve_spell(actor_id, declared, view, **kwargs)

        if isinstance(bridge_result, ClarificationRequest):
            return self._build_clarification_result(
                bridge_result.message, list(bridge_result.candidates)
            )

        # Bridge succeeded — we have a SpellCastIntent ready for Box resolution
        actor_entity = self._world_state.entities.get(actor_id, {})
        actor_name = actor_entity.get("name", actor_id)

        turn_ctx = BoxTurnContext(
            turn_index=self._turn_count,
            actor_id=actor_id,
            actor_team=actor_entity.get(EF.TEAM, "party"),
        )

        try:
            box_result = box_execute_turn(
                world_state=self._world_state,
                turn_ctx=turn_ctx,
                combat_intent=bridge_result,  # SpellCastIntent from IntentBridge
                rng=self._rng,
                next_event_id=self._turn_count * 100,
                timestamp=float(self._turn_count),
            )
        except Exception as e:
            logger.error("Box resolution failed during spell: %s", e)
            return TurnResult(
                success=False,
                narration_text="",
                error_message=f"Spell resolution failed: {e}",
                provenance="[SYSTEM]",
            )

        # Update authoritative world state from Box result
        self._world_state = box_result.world_state

        # Extract outcome from Box events
        event_dicts = []
        for event in box_result.events:
            event_dicts.append({"type": event.event_type, **event.payload})

        brief = NarrativeBrief(
            action_type=box_result.narration or "spell_cast",
            actor_name=actor_name,
            outcome_summary=f"{actor_name} casts {bridge_result.spell_id}",
            source_event_ids=[e.event_id for e in box_result.events],
        )

        return self._narrate_and_output(brief, event_dicts)

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
        self._session_state = SessionState.REST

        try:
            rest_result = self._scene_manager.process_rest(
                rest_type=command.rest_type,
                world_state=self._world_state,
                rng=self._rng,
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

        # WO-060: Force segment boundary on scene transition
        self._segment_tracker.force_segment(
            turn_number=self._turn_count, reason="scene_transition",
        )

        brief = NarrativeBrief(
            action_type="scene_transition",
            actor_name="The party",
            outcome_summary=transition_result.narrative_hint or "The party moves on.",
            scene_description=transition_result.new_scene.description if transition_result.new_scene else None,
        )

        return self._narrate_and_output(brief, transition_result.events)

    def _process_skill(self, actor_id: str, command: ParsedCommand) -> TurnResult:
        """Process an exploration skill check.

        WO-ENGINE-RETRY-002: routes through execute_exploration_skill_check().
        WO-ENGINE-SKILL-MODIFIER-001: computes real modifier from entity dict.

        Out-of-combat only. Returns failure if active_combat is not None.
        """
        if self._world_state.active_combat is not None:
            return TurnResult(
                success=False,
                narration_text="You cannot use exploration skill checks in combat.",
                clarification_needed=False,
            )

        skill_name = command.skill_name or "search"

        # WO-ENGINE-SKILL-MODIFIER-001: inline modifier lookup (no private helper imports)
        from aidm.schemas.skills import SKILLS
        from aidm.core import play_loop as _pl_module
        _entity = self._world_state.entities.get(actor_id, {})
        _skill_def = SKILLS.get(skill_name)
        if _skill_def is not None:
            _ability_map = {
                "str": EF.STR_MOD, "dex": EF.DEX_MOD, "con": EF.CON_MOD,
                "int": EF.INT_MOD, "wis": EF.WIS_MOD, "cha": EF.CHA_MOD,
            }
            _ability_mod = _entity.get(_ability_map.get(_skill_def.key_ability, ""), 0)
            _ranks = _entity.get(EF.SKILL_RANKS, {}).get(skill_name, 0)
            _acp = _entity.get(EF.ARMOR_CHECK_PENALTY, 0) if _skill_def.armor_check_penalty else 0
            # WO-ENGINE-RACIAL-SKILL-BONUS-001: Racial skill bonuses (PHB p.14/17/18/21)
            _racial_skill_bonus = _entity.get(EF.RACIAL_SKILL_BONUS, {}).get(skill_name, 0)
            # WO-ENGINE-MD-SAVE-RULES-001: Fascinated -4 penalty on skill checks (PHB p.308)
            _conditions = _entity.get(EF.CONDITIONS, {}) or {}
            _fascinated_penalty = -4 if "fascinated" in _conditions else 0
            modifier = _ability_mod + _ranks - _acp + _racial_skill_bonus + _fascinated_penalty
        else:
            modifier = 0  # skill not in registry — fail soft

        success, roll_used, updated_ws, events = _pl_module.execute_exploration_skill_check(
            world_state=self._world_state,
            actor_id=actor_id,
            skill_name=skill_name,
            dc=command.dc or 15,
            modifier=modifier,
            rng=self._rng,
            take_10=command.take_10,
            take_20=command.take_20,
            next_event_id=self._turn_count * 100,
        )
        self._world_state = updated_ws

        outcome = "succeeded" if success else "failed"
        t10_prefix = "Take 10: " if command.take_10 else ""
        t20_prefix = "Take 20: " if command.take_20 else ""
        narration_text = f"{t10_prefix}{t20_prefix}{skill_name} check {outcome} (rolled {roll_used})."

        event_dicts = tuple(
            {"event_id": e.event_id, "event_type": e.event_type,
             "timestamp": e.timestamp, **e.payload}
            for e in events
        )

        return TurnResult(
            success=True,
            narration_text=narration_text,
            events=event_dicts,
        )

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
        # WO-060: Force segment boundary on combat start
        self._segment_tracker.force_segment(
            turn_number=self._turn_count, reason="combat_start",
        )
        self._session_state = SessionState.COMBAT

    def exit_combat(self) -> None:
        """Transition session back to exploration state."""
        # WO-060: Force segment boundary on combat end
        self._segment_tracker.force_segment(
            turn_number=self._turn_count, reason="combat_end",
        )
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
        8. Segment tracking (SegmentTracker — WO-060)

        Args:
            brief: NarrativeBrief for this turn
            events: Box events generated

        Returns:
            Complete TurnResult
        """
        # Track brief history
        self._brief_history.append(brief)

        # WO-060: Record turn in segment tracker (may auto-generate summary)
        self._segment_tracker.record_turn(brief, turn_number=self._turn_count)

        # 5. Context assembly — use retrieve() with segment summaries
        segment_summaries = self._segment_tracker.get_summaries()
        session_context = self._context_assembler.assemble(
            brief, session_history=self._brief_history[:-1]
        )

        # 6. Narration generation (pass summaries for PromptPack path)
        narration_text, provenance, pressure_level = self._generate_narration(
            brief, session_context, events, segment_summaries=segment_summaries,
        )

        # 7. TTS synthesis
        narration_audio = self._synthesize_tts(
            narration_text, brief, pressure_level=pressure_level,
        )

        return TurnResult(
            success=True,
            narration_text=narration_text,
            narration_audio=narration_audio,
            events=tuple(events),
            provenance=provenance,
        )

    def _generate_narration(
        self, brief: NarrativeBrief, session_context: str,
        events: Optional[List[Dict[str, Any]]] = None,
        segment_summaries: Optional[List] = None,
    ) -> Tuple[str, str, PressureLevel]:
        """Generate narration text via Spark or template fallback.

        WO-VOICE-PRESSURE-IMPL-001: Before calling Spark, evaluate boundary
        pressure. On RED: skip Spark, use template. On YELLOW: proceed but
        no retry on validation failure. On GREEN: normal flow.

        Args:
            brief: NarrativeBrief for context
            session_context: Assembled context string
            events: Box events for damage extraction
            segment_summaries: WO-060 SessionSegmentSummary objects (newest first)

        Returns:
            Tuple of (narration_text, provenance_tag, pressure_level)
        """
        # Build template context from NarrativeBrief + events.
        template_context = _build_template_context(brief, events or [])

        # --- WO-VOICE-PRESSURE-IMPL-001: Boundary Pressure Evaluation ---
        # Assemble input fields for pressure detection from the brief
        input_fields = self._assemble_pressure_input_fields(brief)

        # Get token budget metrics from context assembler
        token_budget, token_required = self._context_assembler.compute_token_pressure(
            brief, session_history=self._brief_history[:-1],
        )

        pressure_result = evaluate_pressure(
            call_type="COMBAT_NARRATION",  # Default; could be derived from brief
            input_fields=input_fields,
            token_budget=token_budget,
            token_required=token_required,
            turn_number=self._turn_count,
        )

        # Log the pressure event (BP-INV-04: every evaluation is logged)
        self._log_pressure_event(pressure_result)

        # RED: skip Spark, template fallback directly (BP-INV-02)
        if pressure_result.composite_level == PressureLevel.RED:
            fallback = brief.outcome_summary or f"{brief.actor_name} acts."
            return fallback, "[NARRATIVE:TEMPLATE]", PressureLevel.RED

        # --- End pressure evaluation ---

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
            metadata=template_context,
        )

        memory_snapshot = FrozenMemorySnapshot.create()
        world_state_hash = self._world_state.state_hash()

        request = NarrationRequest(
            engine_result=engine_result,
            memory_snapshot=memory_snapshot,
            temperature=0.8,
            world_state_hash=world_state_hash,
            narrative_brief=brief,  # WO-057: enables PromptPack path
            segment_summaries=segment_summaries,  # WO-060: session context
        )

        try:
            result: NarrationResult = self._narration_service.generate_narration(request)

            # YELLOW: if validation failed inside generate_narration and it
            # fell back to template, that's fine — no retry is the policy.
            # The GuardedNarrationService already handles template fallback
            # internally. YELLOW's no-retry constraint is enforced by the
            # fact that GuardedNarrationService uses the same retry policy.
            return result.text, result.provenance, pressure_result.composite_level
        except Exception as e:
            logger.warning("Narration generation failed: %s", e)
            # Template fallback — use the brief's outcome_summary
            fallback = brief.outcome_summary or f"{brief.actor_name} acts."
            return fallback, "[NARRATIVE:TEMPLATE]", pressure_result.composite_level

    def _assemble_pressure_input_fields(self, brief: NarrativeBrief) -> Dict[str, object]:
        """Assemble input fields dict for boundary pressure evaluation.

        Maps NarrativeBrief attributes to the dot-notation field names
        expected by the pressure detectors (per Tier 1.3 input schemas).

        Args:
            brief: NarrativeBrief to extract fields from

        Returns:
            Dict with dot-notation field keys
        """
        fields: Dict[str, object] = {}

        # Truth channel
        if brief.action_type is not None:
            fields["truth.action_type"] = brief.action_type
        if brief.actor_name is not None:
            fields["truth.actor_name"] = brief.actor_name
        if brief.outcome_summary is not None:
            fields["truth.outcome_summary"] = brief.outcome_summary
        if brief.severity is not None:
            fields["truth.severity"] = brief.severity
        fields["truth.target_defeated"] = brief.target_defeated

        # Task channel (inferred from brief context)
        fields["task.task_type"] = "narration"

        # Contract channel (defaults for COMBAT_NARRATION)
        fields["contract.max_length_chars"] = 600
        fields["contract.required_provenance"] = "[NARRATIVE]"

        return fields

    def _log_pressure_event(self, result: object) -> None:
        """Log a BoundaryPressureResult as a structured event.

        WO-VOICE-PRESSURE-IMPL-001: Emits 9-field payload per contract
        Section 5.1. Log levels per Section 5.3:
        GREEN=DEBUG, YELLOW=WARNING, RED=ERROR.

        Args:
            result: BoundaryPressureResult to log
        """
        log_level = _PRESSURE_LOG_LEVELS.get(result.composite_level, logging.ERROR)

        trigger_ids = [t.trigger_id for t in result.triggers]
        trigger_levels = [t.level.value for t in result.triggers]
        detail = "; ".join(
            f"{t.trigger_id}={t.level.value}" for t in result.triggers
        ) or "No pressure triggers fired"

        bp_logger.log(
            log_level,
            "Boundary pressure: %s (%s) — %s",
            result.composite_level.value,
            result.response,
            detail,
            extra={
                "trigger_ids": trigger_ids,
                "trigger_levels": trigger_levels,
                "composite_level": result.composite_level.value,
                "call_type": result.call_type,
                "response": result.response,
                "correlation_id": result.correlation_id,
                "turn_number": result.turn_number,
                "detail": detail,
                "timestamp": result.timestamp,
                "prosodic_modulation": result.composite_level.value,
            },
        )

    def _synthesize_tts(
        self, narration_text: str, brief: NarrativeBrief,
        pressure_level: PressureLevel = PressureLevel.GREEN,
    ) -> Optional[bytes]:
        """Synthesize TTS audio from narration text.

        Resolves prosodic preset from session state and applies it to the
        voice persona before synthesis. Then applies pressure modulation
        on top of the mode preset.

        Args:
            narration_text: Text to synthesize
            brief: NarrativeBrief for NPC voice selection
            pressure_level: Current boundary pressure level (default GREEN)

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

        # WO-VOICE-PAS-PRESETS-001: Apply prosodic preset from session state
        preset_mode = _SESSION_TO_PRESET_MODE.get(
            self._session_state, "scene"
        )
        if isinstance(persona, str):
            # Wrap string voice_id into a minimal VoicePersona for preset overlay
            persona = VoicePersona(
                persona_id=persona, name=persona, voice_model=persona
            )
        if persona is None:
            persona = VoicePersona()
        persona = self._preset_manager.apply_preset(persona, preset_mode)
        # WO-IMPL-PRESSURE-ALERTS-001: Apply pressure modulation after mode preset
        persona = self._preset_manager.apply_pressure_modulation(persona, pressure_level)
        logger.debug("Applying %s prosodic preset (pressure=%s)", preset_mode, pressure_level.value)

        # WO-IMPL-SALIENCE-FILTER-001: Strip non-spoken lines (S5/S6)
        spoken_text = filter_spoken_lines(narration_text)
        if not spoken_text.strip():
            return None  # Nothing to speak

        try:
            return self._tts.synthesize(spoken_text, persona=persona)
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

    def _log_shadow_ruling(self, artifact: object) -> None:
        """WO-JUDGMENT-SHADOW-001: Log Shadow phase ruling artifact to structured log.

        Non-canonical -- does not emit to game state engine or canonical event stream.
        Output file: logs/shadow_rulings.jsonl (append mode).
        sort_keys=True ensures idempotent, diffable output.
        """
        import json
        import dataclasses
        from pathlib import Path
        log_path = Path("logs/shadow_rulings.jsonl")
        log_path.parent.mkdir(exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(dataclasses.asdict(artifact), sort_keys=True) + "\n")
