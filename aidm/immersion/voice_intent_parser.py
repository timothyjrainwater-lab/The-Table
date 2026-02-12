"""Voice-First Intent Parser — Transcript to ActionIntent translation.

Converts STT transcripts into structured ActionIntents using deterministic
keyword/pattern matching with short-term memory context for pronoun resolution.

WO-024: Voice-First Intent Parser
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aidm.schemas.immersion import Transcript
from aidm.schemas.intents import (
    Intent,
    CastSpellIntent,
    MoveIntent,
    DeclaredAttackIntent,
    BuyIntent,
    RestIntent,
)
from aidm.schemas.position import Position


# =============================================================================
# SHORT-TERM MEMORY CONTEXT
# =============================================================================

@dataclass
class STMContext:
    """Short-Term Memory buffer for pronoun and reference resolution.

    Retains the last 3 turns of player actions/targets to resolve
    vague references like "him", "there", "again".

    Attributes:
        last_target: Most recent target entity ID
        last_location: Most recent location reference
        last_action: Most recent action type
        last_weapon: Most recent weapon used
        last_spell: Most recent spell cast
        history: Rolling buffer of last 3 action snapshots
    """

    last_target: Optional[str] = None
    last_location: Optional[Position] = None
    last_action: Optional[str] = None
    last_weapon: Optional[str] = None
    last_spell: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)

    def update(
        self,
        action: Optional[str] = None,
        target: Optional[str] = None,
        location: Optional[Position] = None,
        weapon: Optional[str] = None,
        spell: Optional[str] = None,
    ) -> None:
        """Update STM context with new action info.

        Args:
            action: Action type performed
            target: Target entity ID
            location: Location referenced
            weapon: Weapon used
            spell: Spell cast
        """
        # Create snapshot
        snapshot = {
            "action": action or self.last_action,
            "target": target or self.last_target,
            "location": location,
            "weapon": weapon or self.last_weapon,
            "spell": spell or self.last_spell,
        }

        # Update current state
        if action:
            self.last_action = action
        if target:
            self.last_target = target
        if location:
            self.last_location = location
        if weapon:
            self.last_weapon = weapon
        if spell:
            self.last_spell = spell

        # Add to history buffer (keep last 3)
        self.history.append(snapshot)
        if len(self.history) > 3:
            self.history.pop(0)

    def clear(self) -> None:
        """Reset all tracked referents.

        Called on scene transition to prevent cross-scene pronoun carryover.
        """
        self.last_target = None
        self.last_location = None
        self.last_action = None
        self.last_weapon = None
        self.last_spell = None
        self.history.clear()


# =============================================================================
# PARSE RESULT
# =============================================================================

@dataclass
class ParseResult:
    """Result of transcript parsing.

    Contains the parsed intent, confidence score, and ambiguity flags
    for routing to auto-confirm / clarify / re-prompt.

    Attributes:
        intent: Parsed Intent object (may have missing fields)
        confidence: Confidence score (0.0-1.0)
        ambiguous_target: True if target is ambiguous/missing
        ambiguous_location: True if location is ambiguous/missing
        ambiguous_action: True if action type is unclear
        parse_errors: List of parsing issues encountered
        raw_slots: Raw slot extraction results for debugging
    """

    intent: Optional[Intent] = None
    confidence: float = 0.0
    ambiguous_target: bool = False
    ambiguous_location: bool = False
    ambiguous_action: bool = False
    parse_errors: List[str] = field(default_factory=list)
    raw_slots: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is high enough for auto-confirm (>0.8)."""
        return self.confidence > 0.8

    @property
    def is_medium_confidence(self) -> bool:
        """Check if confidence is medium (0.5-0.8), requires clarification."""
        return 0.5 <= self.confidence <= 0.8

    @property
    def is_low_confidence(self) -> bool:
        """Check if confidence is low (<0.5), requires re-prompt."""
        return self.confidence < 0.5

    @property
    def needs_clarification(self) -> bool:
        """Check if any ambiguity flags are set."""
        return self.ambiguous_target or self.ambiguous_location or self.ambiguous_action


# =============================================================================
# VOICE INTENT PARSER
# =============================================================================

class VoiceIntentParser:
    """Voice-first intent parser using deterministic pattern matching.

    Converts STT transcripts into structured ActionIntents using:
    - Keyword/pattern-based slot filling (no LLM dependency)
    - Short-term memory for pronoun resolution
    - Confidence scoring for routing to clarification

    Design constraints:
    - Deterministic (same input → same output)
    - <600ms parse time per RQ-INTERACT-001
    - No LLM in parse loop
    """

    # =========================================================================
    # ACTION KEYWORDS
    # =========================================================================

    # Attack verbs
    ATTACK_KEYWORDS = {
        "attack", "hit", "strike", "slash", "stab", "shoot", "fire",
        "swing", "punch", "kick", "smite", "charge"
    }

    # Movement verbs
    MOVE_KEYWORDS = {
        "move", "go", "walk", "run", "dash", "rush", "retreat",
        "advance", "step", "approach", "flee"
    }

    # Spell casting verbs
    CAST_KEYWORDS = {
        "cast", "use", "invoke", "channel", "unleash", "summon"
    }

    # Shopping verbs
    BUY_KEYWORDS = {
        "buy", "purchase", "acquire", "shop"
    }

    # Rest keywords
    REST_KEYWORDS = {
        "rest", "sleep", "camp", "recover"
    }

    # =========================================================================
    # TARGET REFERENCE PATTERNS
    # =========================================================================

    # Pronouns for target resolution
    TARGET_PRONOUNS = {
        "him", "her", "it", "them", "that", "this", "one"
    }

    # Location pronouns
    LOCATION_PRONOUNS = {
        "there", "here", "that spot", "this place"
    }

    # Spatial constraints
    SPATIAL_KEYWORDS = {
        "near": "proximity",
        "by": "proximity",
        "next to": "proximity",
        "beside": "proximity",
        "behind": "cover",
        "in front of": "forward",
        "around": "area",
    }

    # =========================================================================
    # SPELL NAMES (COMMON D&D 3.5E SPELLS)
    # =========================================================================

    KNOWN_SPELLS = {
        # Level 0 (Cantrips)
        "acid splash": "point",
        "ray of frost": "creature",
        "touch of fatigue": "creature",

        # Level 1
        "magic missile": "creature",
        "burning hands": "point",
        "shield": "self",
        "mage armor": "creature",
        "grease": "point",

        # Level 2
        "scorching ray": "creature",
        "web": "point",
        "invisibility": "creature",
        "mirror image": "self",

        # Level 3
        "fireball": "point",
        "lightning bolt": "point",
        "haste": "creature",
        "fly": "creature",

        # Level 4
        "ice storm": "point",
        "wall of fire": "point",
        "dimension door": "self",

        # Level 5
        "cone of cold": "point",
        "cloudkill": "point",
        "teleport": "self",
    }

    def __init__(self):
        """Initialize the voice intent parser."""
        pass

    # =========================================================================
    # MAIN PARSE ENTRY POINT
    # =========================================================================

    def parse_transcript(
        self,
        transcript: Transcript,
        context: STMContext,
    ) -> ParseResult:
        """Parse transcript into ActionIntent with confidence scoring.

        Args:
            transcript: STT output (text, confidence, adapter_id)
            context: Short-term memory for reference resolution

        Returns:
            ParseResult with intent, confidence, and ambiguity flags
        """
        # Validate transcript
        if not transcript.text or not transcript.text.strip():
            return ParseResult(
                confidence=0.0,
                ambiguous_action=True,
                parse_errors=["Empty transcript"],
            )

        # Normalize text
        text = self._normalize_text(transcript.text)

        # Extract semantic slots
        slots = self._extract_slots(text, context)

        # Determine action type
        action_type = self._determine_action(text, slots)

        if not action_type:
            return ParseResult(
                confidence=0.0,
                ambiguous_action=True,
                parse_errors=["Could not determine action type"],
                raw_slots=slots,
            )

        # Build intent based on action type
        if action_type == "cast_spell":
            result = self._build_spell_intent(text, slots, context, transcript)
        elif action_type == "attack":
            result = self._build_attack_intent(text, slots, context, transcript)
        elif action_type == "move":
            result = self._build_move_intent(text, slots, context, transcript)
        elif action_type == "buy":
            result = self._build_buy_intent(text, slots, context, transcript)
        elif action_type == "rest":
            result = self._build_rest_intent(text, slots, context, transcript)
        else:
            result = ParseResult(
                confidence=0.0,
                ambiguous_action=True,
                parse_errors=[f"Unsupported action type: {action_type}"],
                raw_slots=slots,
            )

        result.raw_slots = slots
        return result

    # =========================================================================
    # TEXT NORMALIZATION
    # =========================================================================

    def _normalize_text(self, text: str) -> str:
        """Normalize text for parsing.

        Args:
            text: Raw transcript text

        Returns:
            Normalized lowercase text
        """
        # Lowercase and strip whitespace
        text = text.lower().strip()

        # Remove punctuation but keep apostrophes
        text = re.sub(r"[^\w\s']", " ", text)

        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)

        return text

    # =========================================================================
    # SLOT EXTRACTION
    # =========================================================================

    def _extract_slots(self, text: str, context: STMContext) -> Dict[str, Any]:
        """Extract semantic slots from text.

        Args:
            text: Normalized text
            context: STM context for reference resolution

        Returns:
            Dictionary of extracted slots
        """
        slots: Dict[str, Any] = {
            "action_verb": None,
            "target": None,
            "spell": None,
            "weapon": None,
            "location": None,
            "spatial_constraint": None,
            "quantity": None,
            "item": None,
            "has_pronoun": False,
        }

        words = text.split()

        # Extract action verb
        for keyword_set, action_name in [
            (self.ATTACK_KEYWORDS, "attack"),
            (self.MOVE_KEYWORDS, "move"),
            (self.CAST_KEYWORDS, "cast"),
            (self.BUY_KEYWORDS, "buy"),
            (self.REST_KEYWORDS, "rest"),
        ]:
            for word in words:
                if word in keyword_set:
                    slots["action_verb"] = action_name
                    break
            if slots["action_verb"]:
                break

        # Extract spell name (multi-word matching)
        for spell_name, target_mode in self.KNOWN_SPELLS.items():
            if spell_name in text:
                slots["spell"] = spell_name
                slots["spell_target_mode"] = target_mode
                break

        # Extract target pronouns
        for word in words:
            if word in self.TARGET_PRONOUNS:
                slots["has_pronoun"] = True
                # Resolve from context
                if context.last_target:
                    slots["target"] = context.last_target
                break

        # Extract location pronouns
        for word in words:
            if word in self.LOCATION_PRONOUNS:
                slots["has_pronoun"] = True
                # Resolve from context
                if context.last_location:
                    slots["location"] = context.last_location
                break

        # Extract spatial constraints
        for keyword, constraint_type in self.SPATIAL_KEYWORDS.items():
            if keyword in text:
                slots["spatial_constraint"] = constraint_type
                # Extract anchor object (word after spatial keyword)
                # Handle multi-word keywords like "next to"
                keyword_pattern = re.escape(keyword)
                pattern = rf"{keyword_pattern}\s+(?:the\s+)?(\w+)"
                match = re.search(pattern, text)
                if match:
                    slots["spatial_anchor"] = match.group(1)
                break

        # Extract explicit targets (entity references like "goblin", "orc")
        # This is a simplified heuristic - real implementation would query world state
        target_candidates = []
        for word in words:
            if word in ["goblin", "orc", "skeleton", "zombie", "guard", "wizard", "fighter"]:
                target_candidates.append(word)
        if target_candidates and not slots["target"]:
            slots["target"] = target_candidates[0]  # Take first match

        # Extract weapon names
        weapons = ["sword", "longsword", "shortsword", "bow", "crossbow", "axe", "dagger", "mace"]
        for weapon in weapons:
            if weapon in text:
                slots["weapon"] = weapon
                break

        # Extract "again" keyword (repeat last action)
        if "again" in text:
            slots["repeat_last"] = True

        return slots

    # =========================================================================
    # ACTION TYPE DETERMINATION
    # =========================================================================

    def _determine_action(self, text: str, slots: Dict[str, Any]) -> Optional[str]:
        """Determine action type from text and slots.

        Args:
            text: Normalized text
            slots: Extracted semantic slots

        Returns:
            Action type string or None
        """
        # Spell name implies casting (highest priority)
        if slots["spell"]:
            return "cast_spell"

        # Explicit action verb
        if slots["action_verb"]:
            return slots["action_verb"]

        # Weapon + target implies attack
        if slots["weapon"] and slots["target"]:
            return "attack"

        # Item keywords without target suggest buying
        item_keywords = ["sword", "shield", "armor", "potion", "rope", "arrows"]
        if any(item in text for item in item_keywords):
            return "buy"

        # Rest keywords
        if any(word in text for word in self.REST_KEYWORDS):
            return "rest"

        return None

    # =========================================================================
    # INTENT BUILDERS
    # =========================================================================

    def _build_spell_intent(
        self,
        text: str,
        slots: Dict[str, Any],
        context: STMContext,
        transcript: Transcript,
    ) -> ParseResult:
        """Build CastSpellIntent from slots.

        Args:
            text: Normalized text
            slots: Extracted slots
            context: STM context
            transcript: Original transcript

        Returns:
            ParseResult with CastSpellIntent
        """
        spell_name = slots.get("spell", "")
        target_mode = slots.get("spell_target_mode", "none")

        if not spell_name:
            return ParseResult(
                confidence=0.0,
                ambiguous_action=True,
                parse_errors=["No spell name found"],
            )

        intent = CastSpellIntent(
            spell_name=spell_name,
            target_mode=target_mode,
        )

        # Calculate confidence
        confidence = transcript.confidence

        # Adjust confidence based on completeness
        ambiguous_target = False
        ambiguous_location = False

        if target_mode == "creature" and not slots.get("target"):
            ambiguous_target = True
            confidence *= 0.7

        if target_mode == "point" and not slots.get("location"):
            ambiguous_location = True
            confidence *= 0.7

        return ParseResult(
            intent=intent,
            confidence=confidence,
            ambiguous_target=ambiguous_target,
            ambiguous_location=ambiguous_location,
        )

    def _build_attack_intent(
        self,
        text: str,
        slots: Dict[str, Any],
        context: STMContext,
        transcript: Transcript,
    ) -> ParseResult:
        """Build DeclaredAttackIntent from slots.

        Args:
            text: Normalized text
            slots: Extracted slots
            context: STM context
            transcript: Original transcript

        Returns:
            ParseResult with DeclaredAttackIntent
        """
        target = slots.get("target")
        weapon = slots.get("weapon")

        # Handle "again" — repeat last attack
        if slots.get("repeat_last") and context.last_target:
            target = context.last_target
            weapon = weapon or context.last_weapon

        intent = DeclaredAttackIntent(
            target_ref=target,
            weapon=weapon,
        )

        # Calculate confidence
        confidence = transcript.confidence

        ambiguous_target = target is None
        if ambiguous_target:
            confidence *= 0.6

        # Bonus confidence if weapon is specified
        if weapon:
            confidence = min(1.0, confidence * 1.1)

        return ParseResult(
            intent=intent,
            confidence=confidence,
            ambiguous_target=ambiguous_target,
        )

    def _build_move_intent(
        self,
        text: str,
        slots: Dict[str, Any],
        context: STMContext,
        transcript: Transcript,
    ) -> ParseResult:
        """Build MoveIntent from slots.

        Args:
            text: Normalized text
            slots: Extracted slots
            context: STM context
            transcript: Original transcript

        Returns:
            ParseResult with MoveIntent
        """
        location = slots.get("location")

        intent = MoveIntent(
            destination=location,
        )

        # Calculate confidence
        confidence = transcript.confidence

        ambiguous_location = location is None
        if ambiguous_location:
            confidence *= 0.6

        # Spatial constraint gives some context even without exact location
        if slots.get("spatial_constraint"):
            confidence = min(1.0, confidence * 1.2)

        return ParseResult(
            intent=intent,
            confidence=confidence,
            ambiguous_location=ambiguous_location,
        )

    def _build_buy_intent(
        self,
        text: str,
        slots: Dict[str, Any],
        context: STMContext,
        transcript: Transcript,
    ) -> ParseResult:
        """Build BuyIntent from slots.

        Args:
            text: Normalized text
            slots: Extracted slots
            context: STM context
            transcript: Original transcript

        Returns:
            ParseResult with BuyIntent
        """
        # Extract items from text (simplified — real parser would be more robust)
        items = []

        # Look for "N <item>" patterns
        pattern = r"(\d+)\s+(\w+)"
        matches = re.findall(pattern, text)
        for qty_str, item_name in matches:
            items.append({"name": item_name, "qty": int(qty_str)})

        # If no quantity specified, assume 1
        if not items:
            words = text.split()
            # Find first noun after buy keyword
            buy_idx = -1
            for i, word in enumerate(words):
                if word in self.BUY_KEYWORDS:
                    buy_idx = i
                    break

            if buy_idx >= 0 and buy_idx + 1 < len(words):
                item_name = words[buy_idx + 1]
                items.append({"name": item_name, "qty": 1})

        intent = BuyIntent(items=items)

        # Calculate confidence
        confidence = transcript.confidence

        if not items:
            confidence *= 0.5

        return ParseResult(
            intent=intent,
            confidence=confidence,
        )

    def _build_rest_intent(
        self,
        text: str,
        slots: Dict[str, Any],
        context: STMContext,
        transcript: Transcript,
    ) -> ParseResult:
        """Build RestIntent from slots.

        Args:
            text: Normalized text
            slots: Extracted slots
            context: STM context
            transcript: Original transcript

        Returns:
            ParseResult with RestIntent
        """
        # Determine rest type from keywords
        rest_type = "overnight"  # Default

        if "full day" in text or "full rest" in text or "complete rest" in text:
            rest_type = "full_day"

        intent = RestIntent(rest_type=rest_type)

        # Rest is usually unambiguous
        confidence = transcript.confidence

        return ParseResult(
            intent=intent,
            confidence=confidence,
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_voice_intent_parser() -> VoiceIntentParser:
    """Create a configured VoiceIntentParser.

    Returns:
        VoiceIntentParser instance
    """
    return VoiceIntentParser()
