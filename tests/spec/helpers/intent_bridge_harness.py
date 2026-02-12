"""Intent Bridge pipeline harness for compliance testing.

WO-CODE-INTENT-002: Thin wrapper that runs the full intent pipeline
(voice parser → intent bridge → clarification engine) through its
public APIs. Used by compliance tests to verify:
- Determinism (same inputs → same outputs)
- Candidate ordering (lexicographic by display_name)
- No-coaching constraint (clarification phrasing)
- Authority boundary (bridge doesn't compute mechanics)
- Lifecycle immutability (CONFIRMED intents frozen)

This harness uses ONLY public APIs. It does not reach into private
methods or internal state.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from aidm.interaction.intent_bridge import (
    IntentBridge,
    AmbiguityType,
    ClarificationRequest as BridgeClarification,
)
from aidm.immersion.voice_intent_parser import (
    VoiceIntentParser,
    ParseResult,
    STMContext,
)
from aidm.immersion.clarification_loop import (
    ClarificationEngine,
    ClarificationRequest as VoiceClarification,
)
from aidm.schemas.immersion import Transcript
from aidm.schemas.intents import (
    DeclaredAttackIntent,
    CastSpellIntent,
    MoveIntent,
)
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.schemas.entity_fields import EF


@dataclass
class PipelineResult:
    """Complete result from running the intent pipeline."""

    # Stage 1: Parse
    parse_result: Optional[ParseResult] = None

    # Stage 2: Bridge resolution or clarification
    bridge_result: Optional[Any] = None
    bridge_clarification: Optional[BridgeClarification] = None

    # Stage 3: Voice-layer clarification (if needed)
    voice_clarification: Optional[VoiceClarification] = None

    # Metadata
    stages_completed: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def needs_clarification(self) -> bool:
        """Whether the pipeline stopped for clarification."""
        return self.bridge_clarification is not None or self.voice_clarification is not None

    @property
    def resolved(self) -> bool:
        """Whether the pipeline produced a resolved intent."""
        return self.bridge_result is not None and not self.needs_clarification


def build_world_state(entities: Dict[str, Dict[str, Any]]) -> WorldState:
    """Build a WorldState from an entity dict.

    Adds default fields if missing so tests don't need to
    specify every field.
    """
    full_entities = {}
    for eid, data in entities.items():
        entity = {
            EF.ENTITY_ID: eid,
            EF.HP_CURRENT: data.get(EF.HP_CURRENT, 20),
            EF.HP_MAX: data.get("hp_max", 20),
            EF.AC: data.get(EF.AC, 15),
            EF.DEFEATED: data.get(EF.DEFEATED, False),
        }
        entity.update(data)
        full_entities[eid] = entity
    return WorldState(ruleset_version="3.5e", entities=full_entities)


def run_pipeline(
    transcript_text: str,
    entities: Dict[str, Dict[str, Any]],
    stm_context: Optional[STMContext] = None,
    confidence: float = 1.0,
) -> PipelineResult:
    """Run the full intent pipeline from transcript to resolution.

    This is the primary entry point for compliance tests. It exercises:
    1. VoiceIntentParser.parse_transcript()
    2. IntentBridge.resolve_attack/spell/move()
    3. ClarificationEngine.generate_clarification() (if needed)

    Args:
        transcript_text: Raw player speech text
        entities: Entity definitions for world state
        stm_context: Short-term memory context (optional)
        confidence: STT confidence score (default 1.0)

    Returns:
        PipelineResult with all stage outputs
    """
    result = PipelineResult()

    # Build inputs
    transcript = Transcript(text=transcript_text, confidence=confidence)
    stm = stm_context or STMContext()
    world_state = build_world_state(entities)
    view = FrozenWorldStateView(world_state)

    # Stage 1: Parse
    parser = VoiceIntentParser()
    try:
        parse_result = parser.parse_transcript(transcript, stm)
        result.parse_result = parse_result
        result.stages_completed.append("parse")
    except Exception as e:
        result.error = f"Parse failed: {e}"
        return result

    # Check if parse produced a usable intent
    if parse_result.intent is None:
        # Generate clarification for failed parse
        engine = ClarificationEngine()
        try:
            clarification = engine.generate_clarification(parse_result)
            result.voice_clarification = clarification
            result.stages_completed.append("voice_clarification")
        except Exception as e:
            result.error = f"Clarification generation failed: {e}"
        return result

    # Stage 2: Bridge resolution
    bridge = IntentBridge()
    intent = parse_result.intent

    try:
        if isinstance(intent, DeclaredAttackIntent):
            bridge_output = bridge.resolve_attack(
                actor_id=_find_actor_id(entities),
                declared=intent,
                view=view,
            )
        elif isinstance(intent, CastSpellIntent):
            bridge_output = bridge.resolve_spell(
                caster_id=_find_actor_id(entities),
                declared=intent,
                view=view,
            )
        elif isinstance(intent, MoveIntent):
            bridge_output = bridge.resolve_move(
                actor_id=_find_actor_id(entities),
                declared=intent,
                view=view,
            )
        else:
            result.error = f"Unknown intent type: {type(intent).__name__}"
            return result

        if isinstance(bridge_output, BridgeClarification):
            result.bridge_clarification = bridge_output
            result.stages_completed.append("bridge_clarification")

            # Also generate voice-layer clarification
            engine = ClarificationEngine()
            voice_clar = engine.generate_clarification(
                parse_result,
                world_context={"entities": entities},
            )
            result.voice_clarification = voice_clar
            result.stages_completed.append("voice_clarification")
        else:
            result.bridge_result = bridge_output
            result.stages_completed.append("bridge_resolve")
    except Exception as e:
        result.error = f"Bridge resolution failed: {e}"

    return result


def _find_actor_id(entities: Dict[str, Dict[str, Any]]) -> str:
    """Find the player character entity ID from entities dict.

    Convention: the first entity with team="party" is the actor.
    Fallback: first entity in the dict.
    """
    for eid, data in entities.items():
        if data.get(EF.TEAM) == "party" or data.get("team") == "party":
            return eid
    # Fallback: first entity
    return next(iter(entities))


def normalize_pipeline_result(result: PipelineResult) -> Dict[str, Any]:
    """Normalize pipeline result for determinism comparison.

    Produces a dictionary with only determinism-relevant fields,
    stripping timestamps, object IDs, and other non-deterministic
    artifacts.
    """
    normalized = {
        "stages": result.stages_completed,
        "error": result.error,
    }

    if result.parse_result is not None:
        pr = result.parse_result
        normalized["parse"] = {
            "confidence": pr.confidence,
            "ambiguous_target": pr.ambiguous_target,
            "ambiguous_location": pr.ambiguous_location,
            "ambiguous_action": pr.ambiguous_action,
            "intent_type": type(pr.intent).__name__ if pr.intent else None,
        }

    if result.bridge_clarification is not None:
        bc = result.bridge_clarification
        normalized["bridge_clarification"] = {
            "intent_type": bc.intent_type,
            "ambiguity_type": bc.ambiguity_type.value if hasattr(bc.ambiguity_type, 'value') else str(bc.ambiguity_type),
            "candidates": list(bc.candidates),
            "message": bc.message,
        }

    if result.voice_clarification is not None:
        vc = result.voice_clarification
        normalized["voice_clarification"] = {
            "prompt": vc.prompt,
            "clarification_type": vc.clarification_type,
            "suggested_options": vc.suggested_options,
            "missing_fields": vc.missing_fields,
        }

    if result.bridge_result is not None:
        br = result.bridge_result
        normalized["bridge_result"] = {
            "type": type(br).__name__,
        }
        if hasattr(br, "to_dict"):
            normalized["bridge_result"]["data"] = br.to_dict()

    return normalized
