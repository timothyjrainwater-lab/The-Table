"""WO-058: ContradictionChecker v1 — Post-Hoc Spark Output Validation.

Detects fictional state contradictions in LLM narration output by checking
against the NarrativeBrief truth frame. Runs AFTER GrammarShield/KILL-002
(mechanical assertion detection), BEFORE output delivery.

GrammarShield catches mechanical numbers leaking (AC 18, 2d6 damage).
ContradictionChecker catches fictional state mutations:
- "the ogre falls unconscious" when target_defeated=False
- "strikes the goblin" when action_type=attack_miss
- "devastating blow" when severity=minor

THREE CONTRADICTION CLASSES (ordered by severity):
  Class A — Entity State: Spark contradicts NarrativeBrief truth frame fields
  Class B — Outcome: Spark claims mechanical outcomes not in the brief
  Class C — Continuity: Spark contradicts scene or recent narration history

RESPONSE POLICY (from RQ-LENS-SPARK-001 Deliverable 4):
  | Class | 1st Occurrence    | 2nd Consecutive   | 3rd Consecutive       |
  |-------|-------------------|-------------------|-----------------------|
  | A     | retry             | template_fallback | template_fallback+log |
  | B     | retry             | template_fallback | template_fallback+log |
  | C     | annotate          | retry             | template_fallback     |

BOUNDARY LAW (BL-003): This module lives in aidm/narration/.
It does NOT import from aidm.core. NarrativeBrief is received as data
via function parameters, not via module import.

CITATIONS:
- RQ-LENS-SPARK-001: Context Orchestration Sprint (Deliverable 4)
- RQ-LENS-002: Contradiction Surface Mapping (keyword dictionaries)
- AD-002: Lens Context Orchestration
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ==============================================================================
# CONTRADICTION CLASSES
# ==============================================================================


class ContradictionClass(str, Enum):
    """Contradiction severity classes (RQ-LENS-SPARK-001 taxonomy)."""
    CLASS_A = "A"  # Entity state contradiction (Critical)
    CLASS_B = "B"  # Outcome contradiction (High)
    CLASS_C = "C"  # Continuity contradiction (Medium)


class RecommendedAction(str, Enum):
    """Actions to take when a contradiction is detected."""
    RETRY = "retry"
    ANNOTATE = "annotate"
    TEMPLATE_FALLBACK = "template_fallback"


# ==============================================================================
# KEYWORD DICTIONARIES (from RQ-LENS-SPARK-001 + RQ-LENS-002)
# ==============================================================================

# Class A: Entity State Keywords

DEFEAT_KEYWORDS = [
    "falls", "collapses", "dies", "slain", "defeated", "unconscious",
    "crumples", "drops dead", "last breath", "life fades",
    "goes limp", "topples", "expires", "lifeless", "dead",
    "perishes", "succumbs", "breathes no more", "motionless",
]

HIT_KEYWORDS = [
    "strikes", "hits", "wounds", "cuts", "slashes", "pierces",
    "connects", "lands", "bites into", "finds its mark",
    "draws blood", "carves", "cleaves", "slices", "stabs",
    "smashes", "crunches", "tears into",
]

MISS_KEYWORDS = [
    "misses", "fails", "goes wide", "deflected", "dodges",
    "parries", "evades", "sidesteps", "blocks", "glances off",
    "swings wild", "falls short", "whiffs", "sails past",
]

SEVERITY_INFLATION = {
    "minor": ["devastating", "brutal", "crushing", "terrible", "crippling",
              "savage", "vicious", "lethal", "fatal", "mortal"],
    "moderate": ["devastating", "lethal", "fatal", "mortal", "crippling"],
}

SEVERITY_DEFLATION = {
    "lethal": ["scratches", "barely", "minor", "glancing", "superficial",
               "light scratch", "nick", "graze"],
    "devastating": ["minor", "barely", "light", "superficial", "nick",
                    "scratch", "graze"],
}

# Stance contradiction keywords
STANDING_KEYWORDS = ["stands tall", "on their feet", "standing", "upright",
                     "rises to full height"]
PRONE_KEYWORDS = ["sprawled", "on the ground", "prone", "face down",
                  "falls flat", "knocked down"]


# Compile multi-word patterns into regex for reliable matching
def _compile_keywords(keywords: List[str]) -> List[re.Pattern]:
    """Compile keyword list into case-insensitive regex patterns."""
    return [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            if ' ' not in kw
            else re.compile(re.escape(kw), re.IGNORECASE)
            for kw in keywords]


_DEFEAT_PATTERNS = _compile_keywords(DEFEAT_KEYWORDS)
_HIT_PATTERNS = _compile_keywords(HIT_KEYWORDS)
_MISS_PATTERNS = _compile_keywords(MISS_KEYWORDS)
_STANDING_PATTERNS = _compile_keywords(STANDING_KEYWORDS)
_PRONE_PATTERNS = _compile_keywords(PRONE_KEYWORDS)


# ==============================================================================
# RESULT TYPES
# ==============================================================================


@dataclass(frozen=True)
class ContradictionMatch:
    """A single contradiction found in narration text.

    Attributes:
        contradiction_class: Class A, B, or C
        subtype: Specific contradiction type (e.g., "defeat_in_non_defeat")
        matched_text: The text span that triggered the match
        field_name: NarrativeBrief field that was contradicted
        expected: What the truth frame says
        found: What the narration claimed
    """
    contradiction_class: ContradictionClass
    subtype: str
    matched_text: str
    field_name: str
    expected: str
    found: str


@dataclass(frozen=True)
class ContradictionResult:
    """Result of contradiction checking.

    Attributes:
        has_contradiction: Whether any contradiction was found
        matches: All contradictions found (may be multiple)
        recommended_action: What to do about it
        narration_text: The checked narration text
    """
    has_contradiction: bool
    matches: Tuple[ContradictionMatch, ...]
    recommended_action: RecommendedAction
    narration_text: str

    @property
    def worst_class(self) -> Optional[ContradictionClass]:
        """Return the most severe contradiction class found."""
        if not self.matches:
            return None
        # A > B > C (A is worst)
        classes = {m.contradiction_class for m in self.matches}
        if ContradictionClass.CLASS_A in classes:
            return ContradictionClass.CLASS_A
        if ContradictionClass.CLASS_B in classes:
            return ContradictionClass.CLASS_B
        return ContradictionClass.CLASS_C


# ==============================================================================
# CONTRADICTION CHECKER
# ==============================================================================


# Response policy lookup: (class, consecutive_count) → action
_RESPONSE_POLICY = {
    (ContradictionClass.CLASS_A, 1): RecommendedAction.RETRY,
    (ContradictionClass.CLASS_A, 2): RecommendedAction.TEMPLATE_FALLBACK,
    (ContradictionClass.CLASS_A, 3): RecommendedAction.TEMPLATE_FALLBACK,
    (ContradictionClass.CLASS_B, 1): RecommendedAction.RETRY,
    (ContradictionClass.CLASS_B, 2): RecommendedAction.TEMPLATE_FALLBACK,
    (ContradictionClass.CLASS_B, 3): RecommendedAction.TEMPLATE_FALLBACK,
    (ContradictionClass.CLASS_C, 1): RecommendedAction.ANNOTATE,
    (ContradictionClass.CLASS_C, 2): RecommendedAction.RETRY,
    (ContradictionClass.CLASS_C, 3): RecommendedAction.TEMPLATE_FALLBACK,
}


class ContradictionChecker:
    """Post-hoc contradiction detection against NarrativeBrief truth frame.

    Runs AFTER GrammarShield, BEFORE output delivery. Checks LLM narration
    output for fictional state claims that conflict with the mechanical
    truth established by Box.

    Usage:
        checker = ContradictionChecker()
        result = checker.check(narration_text, narrative_brief)
        if result.has_contradiction:
            # result.recommended_action tells you what to do
            ...
    """

    def __init__(self):
        """Initialize checker. Tracks consecutive contradiction count for
        response policy escalation."""
        self._consecutive_contradictions = 0

    def check(
        self,
        narration_text: str,
        brief: Any,  # NarrativeBrief — typed as Any to avoid BL-003 import
    ) -> ContradictionResult:
        """Check narration text against NarrativeBrief truth frame.

        Args:
            narration_text: LLM-generated narration text
            brief: NarrativeBrief with truth frame fields

        Returns:
            ContradictionResult with all matches and recommended action
        """
        matches: List[ContradictionMatch] = []

        # Class A checks: Entity state contradictions
        matches.extend(self._check_defeat_keywords(narration_text, brief))
        matches.extend(self._check_hit_miss_keywords(narration_text, brief))
        matches.extend(self._check_severity(narration_text, brief))
        matches.extend(self._check_stance(narration_text, brief))

        # Class B checks: Outcome contradictions
        matches.extend(self._check_weapon_name(narration_text, brief))
        matches.extend(self._check_damage_type(narration_text, brief))
        matches.extend(self._check_actor_name(narration_text, brief))
        matches.extend(self._check_target_name(narration_text, brief))

        # Class C checks: Continuity contradictions
        matches.extend(self._check_scene_continuity(narration_text, brief))

        has_contradiction = len(matches) > 0

        if has_contradiction:
            self._consecutive_contradictions += 1
            worst_class = self._get_worst_class(matches)
            action = self._get_response_action(worst_class)
            logger.warning(
                f"Contradiction detected: {len(matches)} match(es), "
                f"worst_class={worst_class.value}, "
                f"consecutive={self._consecutive_contradictions}, "
                f"action={action.value}"
            )
        else:
            self._consecutive_contradictions = 0
            action = RecommendedAction.RETRY  # unused when no contradiction

        return ContradictionResult(
            has_contradiction=has_contradiction,
            matches=tuple(matches),
            recommended_action=action,
            narration_text=narration_text,
        )

    def reset_consecutive_count(self) -> None:
        """Reset consecutive contradiction counter (call on successful narration)."""
        self._consecutive_contradictions = 0

    @property
    def consecutive_contradictions(self) -> int:
        """Current consecutive contradiction count."""
        return self._consecutive_contradictions

    # ══════════════════════════════════════════════════════════════════════
    # CLASS A: ENTITY STATE CONTRADICTIONS
    # ══════════════════════════════════════════════════════════════════════

    def _check_defeat_keywords(
        self, text: str, brief: Any
    ) -> List[ContradictionMatch]:
        """Check for defeat language when target is NOT defeated (and vice versa)."""
        matches = []
        target_defeated = getattr(brief, 'target_defeated', False)

        if not target_defeated:
            # Target NOT defeated — defeat keywords should NOT appear
            for pattern in _DEFEAT_PATTERNS:
                m = pattern.search(text)
                if m:
                    matches.append(ContradictionMatch(
                        contradiction_class=ContradictionClass.CLASS_A,
                        subtype="defeat_in_non_defeat",
                        matched_text=m.group(0),
                        field_name="target_defeated",
                        expected="False",
                        found=f"defeat keyword: '{m.group(0)}'",
                    ))
                    break  # One match is enough to flag

        return matches

    def _check_hit_miss_keywords(
        self, text: str, brief: Any
    ) -> List[ContradictionMatch]:
        """Check for hit keywords in miss context (and vice versa)."""
        matches = []
        action_type = getattr(brief, 'action_type', '')

        # Miss context: hit keywords should not appear
        miss_actions = {'attack_miss', 'concealment_miss', 'spell_no_effect',
                        'spell_resisted'}
        if action_type in miss_actions:
            for pattern in _HIT_PATTERNS:
                m = pattern.search(text)
                if m:
                    matches.append(ContradictionMatch(
                        contradiction_class=ContradictionClass.CLASS_A,
                        subtype="hit_keyword_in_miss",
                        matched_text=m.group(0),
                        field_name="action_type",
                        expected=action_type,
                        found=f"hit keyword: '{m.group(0)}'",
                    ))
                    break

        # Hit context: miss keywords should not appear
        hit_actions = {'attack_hit', 'critical', 'spell_damage_dealt'}
        if action_type in hit_actions:
            for pattern in _MISS_PATTERNS:
                m = pattern.search(text)
                if m:
                    matches.append(ContradictionMatch(
                        contradiction_class=ContradictionClass.CLASS_A,
                        subtype="miss_keyword_in_hit",
                        matched_text=m.group(0),
                        field_name="action_type",
                        expected=action_type,
                        found=f"miss keyword: '{m.group(0)}'",
                    ))
                    break

        return matches

    def _check_severity(
        self, text: str, brief: Any
    ) -> List[ContradictionMatch]:
        """Check for severity inflation or deflation."""
        matches = []
        severity = getattr(brief, 'severity', 'minor')

        # Inflation check: narration overstates severity
        inflation_words = SEVERITY_INFLATION.get(severity, [])
        for word in inflation_words:
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            m = pattern.search(text)
            if m:
                matches.append(ContradictionMatch(
                    contradiction_class=ContradictionClass.CLASS_A,
                    subtype="severity_inflation",
                    matched_text=m.group(0),
                    field_name="severity",
                    expected=severity,
                    found=f"inflated: '{m.group(0)}'",
                ))
                break

        # Deflation check: narration understates severity
        deflation_words = SEVERITY_DEFLATION.get(severity, [])
        for word in deflation_words:
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            m = pattern.search(text)
            if m:
                matches.append(ContradictionMatch(
                    contradiction_class=ContradictionClass.CLASS_A,
                    subtype="severity_deflation",
                    matched_text=m.group(0),
                    field_name="severity",
                    expected=severity,
                    found=f"deflated: '{m.group(0)}'",
                ))
                break

        return matches

    def _check_stance(
        self, text: str, brief: Any
    ) -> List[ContradictionMatch]:
        """Check for stance contradictions (prone/standing)."""
        matches = []
        condition = getattr(brief, 'condition_applied', None)

        if condition == 'prone':
            # Target should be described as prone, NOT standing
            for pattern in _STANDING_PATTERNS:
                m = pattern.search(text)
                if m:
                    matches.append(ContradictionMatch(
                        contradiction_class=ContradictionClass.CLASS_A,
                        subtype="stance_contradiction",
                        matched_text=m.group(0),
                        field_name="condition_applied",
                        expected="prone",
                        found=f"standing keyword: '{m.group(0)}'",
                    ))
                    break

        return matches

    # ══════════════════════════════════════════════════════════════════════
    # CLASS B: OUTCOME CONTRADICTIONS
    # ══════════════════════════════════════════════════════════════════════

    def _check_weapon_name(
        self, text: str, brief: Any
    ) -> List[ContradictionMatch]:
        """Check if narration references wrong weapon."""
        matches = []
        weapon_name = getattr(brief, 'weapon_name', None)
        if not weapon_name:
            return matches

        # Common weapon names to check for substitution
        common_weapons = [
            "longsword", "shortsword", "greatsword", "greataxe", "battleaxe",
            "handaxe", "dagger", "rapier", "scimitar", "warhammer", "maul",
            "mace", "morningstar", "flail", "spear", "javelin", "longbow",
            "shortbow", "crossbow", "sling", "staff", "quarterstaff",
            "halberd", "glaive", "trident", "pike",
        ]

        weapon_lower = weapon_name.lower()
        text_lower = text.lower()

        for other_weapon in common_weapons:
            if other_weapon == weapon_lower:
                continue  # Skip the correct weapon
            if other_weapon in weapon_lower or weapon_lower in other_weapon:
                continue  # Skip partial matches (e.g., "sword" in "longsword")
            pattern = re.compile(r'\b' + re.escape(other_weapon) + r'\b', re.IGNORECASE)
            m = pattern.search(text)
            if m:
                # Only flag if the correct weapon is NOT also mentioned
                correct_pattern = re.compile(
                    r'\b' + re.escape(weapon_name) + r'\b', re.IGNORECASE
                )
                if not correct_pattern.search(text):
                    matches.append(ContradictionMatch(
                        contradiction_class=ContradictionClass.CLASS_B,
                        subtype="wrong_weapon",
                        matched_text=m.group(0),
                        field_name="weapon_name",
                        expected=weapon_name,
                        found=m.group(0),
                    ))
                    break

        return matches

    def _check_damage_type(
        self, text: str, brief: Any
    ) -> List[ContradictionMatch]:
        """Check if narration describes wrong damage type."""
        matches = []
        damage_type = getattr(brief, 'damage_type', None)
        if not damage_type:
            return matches

        # Damage type language clusters
        damage_language = {
            "slashing": ["slash", "cut", "cleave", "slice", "carve", "hew"],
            "piercing": ["pierce", "stab", "puncture", "impale", "skewer"],
            "bludgeoning": ["crush", "smash", "slam", "pummel", "batter"],
            "fire": ["burn", "ignite", "flame", "blaze", "scorch", "sear", "incinerate"],
            "cold": ["freeze", "frost", "chill", "ice", "frigid"],
            "acid": ["dissolve", "corrode", "melt", "acid", "caustic"],
            "lightning": ["shock", "jolt", "electr", "lightning", "thunder"],
            "sonic": ["sonic", "thunder", "deafen", "shatter"],
            "force": ["force", "invisible"],
            "negative": ["wither", "drain", "necrotic", "decay"],
            "positive": ["radiant", "holy", "divine light"],
        }

        expected_words = damage_language.get(damage_type.lower(), [])
        if not expected_words:
            return matches

        text_lower = text.lower()

        # Check if narration uses damage language from a DIFFERENT type
        for other_type, other_words in damage_language.items():
            if other_type == damage_type.lower():
                continue
            for word in other_words:
                if word in text_lower:
                    # Only flag if expected damage language is absent
                    expected_present = any(w in text_lower for w in expected_words)
                    if not expected_present:
                        matches.append(ContradictionMatch(
                            contradiction_class=ContradictionClass.CLASS_B,
                            subtype="wrong_damage_type",
                            matched_text=word,
                            field_name="damage_type",
                            expected=damage_type,
                            found=f"{other_type} language: '{word}'",
                        ))
                        return matches  # One match sufficient

        return matches

    def _check_actor_name(
        self, text: str, brief: Any
    ) -> List[ContradictionMatch]:
        """Check if narration uses wrong actor name."""
        matches = []
        actor_name = getattr(brief, 'actor_name', None)
        if not actor_name:
            return matches

        # Only check if the actor name is NOT present in the narration
        # This catches cases where Spark invents a different actor
        pattern = re.compile(re.escape(actor_name), re.IGNORECASE)
        if not pattern.search(text):
            # Actor name missing — this is suspicious but not always wrong
            # (narration might use "he/she/they" pronouns)
            # Only flag for action types where actor should be named
            action_type = getattr(brief, 'action_type', '')
            named_actions = {'attack_hit', 'attack_miss', 'critical',
                             'spell_damage_dealt', 'spell_cast',
                             'spell_healed'}
            if action_type in named_actions:
                # Check if a different proper noun is used instead
                # (Don't flag pronoun usage, only wrong-name usage)
                pass  # Deferred to v2: requires NER or name registry

        return matches

    def _check_target_name(
        self, text: str, brief: Any
    ) -> List[ContradictionMatch]:
        """Check if narration uses wrong target name."""
        matches = []
        target_name = getattr(brief, 'target_name', None)
        if not target_name:
            return matches

        # Same approach as actor name — deferred full check to v2
        # For v1, we only check if target name is present when it should be
        return matches

    # ══════════════════════════════════════════════════════════════════════
    # CLASS C: CONTINUITY CONTRADICTIONS
    # ══════════════════════════════════════════════════════════════════════

    def _check_scene_continuity(
        self, text: str, brief: Any
    ) -> List[ContradictionMatch]:
        """Check if narration contradicts scene description."""
        matches = []
        scene = getattr(brief, 'scene_description', None)
        if not scene:
            return matches

        text_lower = text.lower()
        scene_lower = scene.lower()

        # Indoor/outdoor contradiction
        indoor_words = ["dungeon", "corridor", "chamber", "cave", "tunnel",
                        "basement", "cellar", "crypt", "tomb", "hallway",
                        "room", "tower", "castle"]
        outdoor_words = ["forest", "clearing", "meadow", "field", "plains",
                         "desert", "mountain", "beach", "ocean", "river",
                         "lake", "swamp", "marsh", "hill"]

        scene_is_indoor = any(w in scene_lower for w in indoor_words)
        scene_is_outdoor = any(w in scene_lower for w in outdoor_words)

        if scene_is_indoor:
            for word in outdoor_words:
                if word in text_lower and word not in scene_lower:
                    matches.append(ContradictionMatch(
                        contradiction_class=ContradictionClass.CLASS_C,
                        subtype="scene_location_mismatch",
                        matched_text=word,
                        field_name="scene_description",
                        expected=f"indoor: {scene}",
                        found=f"outdoor keyword: '{word}'",
                    ))
                    return matches

        if scene_is_outdoor:
            for word in indoor_words:
                if word in text_lower and word not in scene_lower:
                    matches.append(ContradictionMatch(
                        contradiction_class=ContradictionClass.CLASS_C,
                        subtype="scene_location_mismatch",
                        matched_text=word,
                        field_name="scene_description",
                        expected=f"outdoor: {scene}",
                        found=f"indoor keyword: '{word}'",
                    ))
                    return matches

        return matches

    # ══════════════════════════════════════════════════════════════════════
    # RESPONSE POLICY
    # ══════════════════════════════════════════════════════════════════════

    def _get_worst_class(
        self, matches: List[ContradictionMatch]
    ) -> ContradictionClass:
        """Get the most severe contradiction class from matches."""
        classes = {m.contradiction_class for m in matches}
        if ContradictionClass.CLASS_A in classes:
            return ContradictionClass.CLASS_A
        if ContradictionClass.CLASS_B in classes:
            return ContradictionClass.CLASS_B
        return ContradictionClass.CLASS_C

    def _get_response_action(
        self, worst_class: ContradictionClass
    ) -> RecommendedAction:
        """Determine response action based on class and consecutive count.

        Uses the response policy table from RQ-LENS-SPARK-001 Deliverable 4.
        """
        count = min(self._consecutive_contradictions, 3)
        key = (worst_class, count)
        return _RESPONSE_POLICY.get(key, RecommendedAction.TEMPLATE_FALLBACK)

    # ══════════════════════════════════════════════════════════════════════
    # RETRY PROMPT AUGMENTATION
    # ══════════════════════════════════════════════════════════════════════

    def build_retry_correction(
        self, result: ContradictionResult, brief: Any
    ) -> str:
        """Build correction text to append to retry prompt.

        When a contradiction is detected and the response policy says "retry",
        this method generates the correction text that should be appended to
        the PromptPack's task instruction.

        Args:
            result: ContradictionResult from a failed check
            brief: NarrativeBrief with truth frame

        Returns:
            Correction text string to append to prompt
        """
        corrections = ["CORRECTION: Your previous narration contradicted the truth frame."]

        for match in result.matches:
            if match.subtype == "defeat_in_non_defeat":
                corrections.append(
                    f"The target was NOT defeated. Do not describe death, "
                    f"collapse, or unconsciousness."
                )
            elif match.subtype == "hit_keyword_in_miss":
                corrections.append(
                    f"The attack MISSED. Do not describe hitting, "
                    f"wounding, or connecting."
                )
            elif match.subtype == "miss_keyword_in_hit":
                corrections.append(
                    f"The attack HIT. Do not describe missing, dodging, "
                    f"or parrying."
                )
            elif match.subtype == "severity_inflation":
                severity = getattr(brief, 'severity', 'minor')
                corrections.append(
                    f"Severity is {severity}. Do not use words like "
                    f"'{match.matched_text}'."
                )
            elif match.subtype == "severity_deflation":
                severity = getattr(brief, 'severity', 'minor')
                corrections.append(
                    f"Severity is {severity}. Do not downplay with words like "
                    f"'{match.matched_text}'."
                )
            elif match.subtype == "stance_contradiction":
                corrections.append(
                    f"The target was knocked prone. Do not describe them "
                    f"as standing or upright."
                )
            elif match.subtype == "wrong_weapon":
                weapon = getattr(brief, 'weapon_name', 'the weapon')
                corrections.append(
                    f"Weapon used: {weapon}. Do not reference "
                    f"'{match.matched_text}'."
                )
            elif match.subtype == "wrong_damage_type":
                dtype = getattr(brief, 'damage_type', 'the damage type')
                corrections.append(
                    f"Damage type is {dtype}. Do not describe "
                    f"'{match.matched_text}' effects."
                )
            elif match.subtype == "scene_location_mismatch":
                scene = getattr(brief, 'scene_description', 'the current scene')
                corrections.append(
                    f"Scene is: {scene}. Do not reference "
                    f"'{match.matched_text}'."
                )

        return "\n".join(corrections)
