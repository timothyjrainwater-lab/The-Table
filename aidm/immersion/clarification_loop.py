"""Clarification Engine — DM-persona prompts for ambiguous intents.

Generates natural, conversational clarification prompts when intent parsing
produces ambiguous results. Follows reflective questioning style per
RQ-INTERACT-001 Finding 5.

WO-024: Voice-First Intent Parser
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aidm.immersion.voice_intent_parser import ParseResult
from aidm.schemas.intents import (
    Intent,
    CastSpellIntent,
    DeclaredAttackIntent,
    MoveIntent,
)


# =============================================================================
# CLARIFICATION REQUEST
# =============================================================================

@dataclass
class ClarificationRequest:
    """Structured clarification request for ambiguous intent.

    Contains DM-persona prompt and suggested options for disambiguation.

    Attributes:
        prompt: Natural language clarification question
        clarification_type: Type of ambiguity (target, location, spell, direction)
        suggested_options: List of suggested options for disambiguation
        missing_fields: Fields that need to be filled
        can_proceed_without: Whether action can proceed with partial info
    """

    prompt: str
    clarification_type: str
    suggested_options: List[str]
    missing_fields: List[str]
    can_proceed_without: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "prompt": self.prompt,
            "clarification_type": self.clarification_type,
            "suggested_options": self.suggested_options,
            "missing_fields": self.missing_fields,
            "can_proceed_without": self.can_proceed_without,
        }


# =============================================================================
# CLARIFICATION ENGINE
# =============================================================================

class ClarificationEngine:
    """Generates DM-persona clarification prompts for ambiguous intents.

    Uses reflective questioning style to maintain immersion while resolving
    ambiguity. Never uses system error language.

    Design principles (RQ-INTERACT-001 Finding 5):
    - Conversational, not mechanical
    - DM persona, not system prompts
    - Natural questioning, not form fields
    """

    # =========================================================================
    # CLARIFICATION GENERATION
    # =========================================================================

    def generate_clarification(
        self,
        parse_result: ParseResult,
        world_context: Optional[Dict[str, Any]] = None,
    ) -> ClarificationRequest:
        """Generate clarification request for ambiguous parse result.

        Args:
            parse_result: ParseResult with ambiguity flags set
            world_context: Optional world state context for candidate generation

        Returns:
            ClarificationRequest with DM-persona prompt
        """
        if not parse_result.needs_clarification:
            # No clarification needed
            return ClarificationRequest(
                prompt="",
                clarification_type="none",
                suggested_options=[],
                missing_fields=[],
            )

        intent = parse_result.intent

        # Route to specific clarification handler
        if parse_result.ambiguous_target:
            return self._clarify_target(intent, world_context)

        elif parse_result.ambiguous_location:
            return self._clarify_location(intent, world_context)

        elif parse_result.ambiguous_action:
            return self._clarify_action(parse_result)

        else:
            # Generic clarification
            return ClarificationRequest(
                prompt="I didn't quite catch that. What are you trying to do?",
                clarification_type="generic",
                suggested_options=[],
                missing_fields=["action"],
            )

    # =========================================================================
    # TARGET CLARIFICATION
    # =========================================================================

    def _clarify_target(
        self,
        intent: Optional[Intent],
        world_context: Optional[Dict[str, Any]],
    ) -> ClarificationRequest:
        """Generate clarification for ambiguous target.

        Args:
            intent: Parsed intent (may be incomplete)
            world_context: World state for candidate generation

        Returns:
            ClarificationRequest for target disambiguation
        """
        # Extract candidates from world context
        candidates = []
        if world_context and "nearby_entities" in world_context:
            candidates = world_context["nearby_entities"]

        if not candidates:
            # Generic target prompt
            if isinstance(intent, DeclaredAttackIntent):
                prompt = "Who are you attacking?"
            elif isinstance(intent, CastSpellIntent):
                prompt = f"Who is the target of {intent.spell_name}?"
            else:
                prompt = "Which one?"

            return ClarificationRequest(
                prompt=prompt,
                clarification_type="target",
                suggested_options=[],
                missing_fields=["target_ref"],
            )

        # Multiple candidates — offer choices
        if len(candidates) == 2:
            prompt = f"Did you mean {candidates[0]} or {candidates[1]}?"
        elif len(candidates) > 2:
            options_str = ", ".join(candidates[:-1]) + f", or {candidates[-1]}"
            prompt = f"Which one — {options_str}?"
        else:
            prompt = f"Did you mean {candidates[0]}?"

        return ClarificationRequest(
            prompt=prompt,
            clarification_type="target",
            suggested_options=candidates,
            missing_fields=["target_ref"],
        )

    # =========================================================================
    # LOCATION CLARIFICATION
    # =========================================================================

    def _clarify_location(
        self,
        intent: Optional[Intent],
        world_context: Optional[Dict[str, Any]],
    ) -> ClarificationRequest:
        """Generate clarification for ambiguous location.

        Args:
            intent: Parsed intent (may be incomplete)
            world_context: World state for location hints

        Returns:
            ClarificationRequest for location disambiguation
        """
        # Check if this is a spell with area effect
        if isinstance(intent, CastSpellIntent):
            spell_name = intent.spell_name

            if intent.target_mode == "point":
                # Area effect spell
                prompt = f"Where do you want to center {spell_name}?"

                # Suggest tactical options if world context available
                suggestions = []
                if world_context and "tactical_hints" in world_context:
                    suggestions = world_context["tactical_hints"]

                return ClarificationRequest(
                    prompt=prompt,
                    clarification_type="location",
                    suggested_options=suggestions,
                    missing_fields=["target_location"],
                )

        # Movement location
        if isinstance(intent, MoveIntent):
            prompt = "Where are you moving to?"

            suggestions = []
            if world_context and "movement_options" in world_context:
                suggestions = world_context["movement_options"]

            return ClarificationRequest(
                prompt=prompt,
                clarification_type="location",
                suggested_options=suggestions,
                missing_fields=["destination"],
            )

        # Generic location prompt
        return ClarificationRequest(
            prompt="Where?",
            clarification_type="location",
            suggested_options=[],
            missing_fields=["location"],
        )

    # =========================================================================
    # ACTION CLARIFICATION
    # =========================================================================

    def _clarify_action(
        self,
        parse_result: ParseResult,
    ) -> ClarificationRequest:
        """Generate clarification for ambiguous action.

        Args:
            parse_result: ParseResult with parse errors

        Returns:
            ClarificationRequest for action clarification
        """
        # Check parse errors for hints
        errors = parse_result.parse_errors

        if any("empty" in err.lower() for err in errors):
            prompt = "I didn't hear anything. What would you like to do?"
        elif any("determine action" in err.lower() for err in errors):
            prompt = "I'm not sure what you're trying to do. Could you rephrase?"
        else:
            prompt = "I didn't quite catch that. What are you trying to do?"

        # Suggest common actions
        suggestions = [
            "attack",
            "move",
            "cast a spell",
            "use an item",
            "rest",
        ]

        return ClarificationRequest(
            prompt=prompt,
            clarification_type="action",
            suggested_options=suggestions,
            missing_fields=["action_type"],
        )

    # =========================================================================
    # SPELL CLARIFICATION
    # =========================================================================

    def _clarify_spell(
        self,
        candidates: List[str],
    ) -> ClarificationRequest:
        """Generate clarification for ambiguous spell name.

        Args:
            candidates: List of possible spell names

        Returns:
            ClarificationRequest for spell disambiguation
        """
        if len(candidates) == 2:
            prompt = f"Did you mean {candidates[0]} or {candidates[1]}?"
        elif len(candidates) > 2:
            options_str = ", ".join(candidates[:-1]) + f", or {candidates[-1]}"
            prompt = f"Which spell — {options_str}?"
        else:
            prompt = "Which spell are you casting?"

        return ClarificationRequest(
            prompt=prompt,
            clarification_type="spell",
            suggested_options=candidates,
            missing_fields=["spell_name"],
        )

    # =========================================================================
    # DIRECTION CLARIFICATION
    # =========================================================================

    def _clarify_direction(
        self,
        intent: Optional[Intent],
        world_context: Optional[Dict[str, Any]],
    ) -> ClarificationRequest:
        """Generate clarification for unclear direction/facing.

        Args:
            intent: Parsed intent
            world_context: World state

        Returns:
            ClarificationRequest for direction disambiguation
        """
        directions = ["north", "south", "east", "west"]

        # Add relative directions if world context has landmarks
        if world_context and "landmarks" in world_context:
            landmarks = world_context["landmarks"]
            for landmark in landmarks[:2]:  # Limit to 2 landmarks
                directions.append(f"toward the {landmark}")

        prompt = "Which direction?"

        return ClarificationRequest(
            prompt=prompt,
            clarification_type="direction",
            suggested_options=directions,
            missing_fields=["direction"],
        )

    # =========================================================================
    # CONFIRMATION PROMPTS
    # =========================================================================

    def generate_soft_confirmation(
        self,
        intent: Intent,
        world_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate soft confirmation prompt for complete intent.

        This is not a modal confirmation — it's natural DM table talk.
        Player can interrupt verbally if incorrect.

        Args:
            intent: Fully parsed intent
            world_context: World state for contextual confirmation

        Returns:
            Natural language confirmation string
        """
        if isinstance(intent, CastSpellIntent):
            spell = intent.spell_name
            if intent.target_mode == "self":
                return f"Alright, you cast {spell} on yourself."
            elif intent.target_mode == "creature":
                return f"Alright, casting {spell}..."
            elif intent.target_mode == "point":
                return f"Alright, {spell} centered here..."
            else:
                return f"Alright, you cast {spell}."

        elif isinstance(intent, DeclaredAttackIntent):
            target = intent.target_ref or "your target"
            weapon = intent.weapon or "your weapon"
            return f"Alright, you attack {target} with your {weapon}."

        elif isinstance(intent, MoveIntent):
            return "Alright, moving there..."

        else:
            return "Alright..."

    # =========================================================================
    # IMPOSSIBILITY FEEDBACK
    # =========================================================================

    def generate_impossibility_feedback(
        self,
        reason: str,
        intent: Optional[Intent] = None,
        world_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate feedback for impossible actions.

        Uses in-world explanation, never system errors.

        Args:
            reason: Reason code for impossibility
            intent: The impossible intent
            world_context: World state for context

        Returns:
            Natural language feedback string
        """
        if reason == "out_of_range":
            if isinstance(intent, MoveIntent):
                return "That's a bit too far for one turn. You can get to here, or you'd need to Dash."
            elif isinstance(intent, DeclaredAttackIntent):
                return "That's out of range for your weapon. You'll need to get closer."
            else:
                return "You can't reach that far this round."

        elif reason == "blocked":
            return "You can't get there — there's something in the way."

        elif reason == "no_line_of_sight":
            return "You don't have a clear line of sight to that target."

        elif reason == "insufficient_resources":
            if isinstance(intent, CastSpellIntent):
                return f"You don't have {intent.spell_name} prepared right now."
            else:
                return "You don't have the resources for that action."

        elif reason == "invalid_target":
            return "That's not a valid target for this action."

        else:
            return "You can't do that right now."


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_clarification_engine() -> ClarificationEngine:
    """Create a configured ClarificationEngine.

    Returns:
        ClarificationEngine instance
    """
    return ClarificationEngine()


# =============================================================================
# CLARIFICATION LOOP — Round-limited clarification with RETRACTED fallback
# =============================================================================

@dataclass
class ClarificationResult:
    """Result of a clarification round.

    Attributes:
        resolved: Whether clarification succeeded
        retracted: Whether intent was retracted (max rounds exceeded)
        clarification: The clarification request (if still clarifying)
        round_number: Current round number (1-indexed)
    """

    resolved: bool
    retracted: bool
    clarification: Optional[ClarificationRequest] = None
    round_number: int = 0


class ClarificationLoop:
    """Tracks clarification rounds and enforces max_rounds limit.

    Contract §4.6: After max_rounds failed clarification attempts, the intent
    is RETRACTED rather than continuing to ask indefinitely.

    Usage:
        loop = ClarificationLoop(max_rounds=3)
        while True:
            result = loop.attempt(parse_result, world_context)
            if result.retracted:
                # Intent status → RETRACTED
                break
            if result.resolved:
                # Clarification succeeded
                break
            # Present result.clarification to player, get new input
    """

    def __init__(self, max_rounds: int = 3) -> None:
        self._max_rounds = max_rounds
        self._round_count = 0
        self._engine = ClarificationEngine()

    @property
    def max_rounds(self) -> int:
        return self._max_rounds

    @property
    def round_count(self) -> int:
        return self._round_count

    def attempt(
        self,
        parse_result: ParseResult,
        world_context: Optional[Dict[str, Any]] = None,
    ) -> ClarificationResult:
        """Attempt one round of clarification.

        Returns:
            ClarificationResult with resolved/retracted status.
        """
        self._round_count += 1

        if not parse_result.needs_clarification:
            return ClarificationResult(
                resolved=True,
                retracted=False,
                round_number=self._round_count,
            )

        if self._round_count > self._max_rounds:
            return ClarificationResult(
                resolved=False,
                retracted=True,
                round_number=self._round_count,
            )

        clarification = self._engine.generate_clarification(
            parse_result, world_context
        )
        return ClarificationResult(
            resolved=False,
            retracted=False,
            clarification=clarification,
            round_number=self._round_count,
        )

    def reset(self) -> None:
        """Reset round counter for a new intent."""
        self._round_count = 0
