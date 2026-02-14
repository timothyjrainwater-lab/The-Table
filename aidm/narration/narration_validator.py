"""WO-NARRATION-VALIDATOR-001: Runtime Narration Validation.

Unified validation pass that compares Spark's narration text against the
NarrativeBrief truth frame. Returns PASS/WARN/FAIL with actionable rule IDs.

Consumes ContradictionChecker's keyword lists — does NOT duplicate them.

RULE INVENTORY:
  P0 (FAIL on violation):
    RV-001: Hit/Miss Consistency
    RV-002: Defeat Consistency
    RV-008: Save Result Consistency
    RV-005: Contraindication Enforcement (Layer B, dormant until content_id)

  P1 (WARN on violation):
    RV-003: Severity-Narration Alignment
    RV-004: Condition Consistency
    RV-007: Delivery Mode Consistency (Layer B, dormant until content_id)

BOUNDARY LAW (BL-003): This module lives in aidm/narration/.
It does NOT import from aidm.core.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from aidm.narration.contradiction_checker import (
    HIT_KEYWORDS,
    MISS_KEYWORDS,
    DEFEAT_KEYWORDS,
    STANDING_KEYWORDS,
    SEVERITY_INFLATION,
    SEVERITY_DEFLATION,
    _compile_keywords,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# RESULT TYPES
# ==============================================================================


@dataclass(frozen=True)
class RuleViolation:
    """A single rule violation found by NarrationValidator.

    Attributes:
        rule_id: Rule identifier (e.g., "RV-001")
        severity: "FAIL" or "WARN"
        detail: Human-readable explanation
    """
    rule_id: str
    severity: str  # "FAIL" or "WARN"
    detail: str


@dataclass(frozen=True)
class ValidationResult:
    """Result of narration validation.

    Attributes:
        verdict: "PASS", "WARN", or "FAIL"
        violations: All violations found (empty tuple if PASS)
    """
    verdict: str  # "PASS", "WARN", "FAIL"
    violations: Tuple[RuleViolation, ...]


# ==============================================================================
# COMPILED KEYWORD PATTERNS (reuse ContradictionChecker lists)
# ==============================================================================

_HIT_PATTERNS = _compile_keywords(HIT_KEYWORDS)
_MISS_PATTERNS = _compile_keywords(MISS_KEYWORDS)
_DEFEAT_PATTERNS = _compile_keywords(DEFEAT_KEYWORDS)
_STANDING_PATTERNS = _compile_keywords(STANDING_KEYWORDS)

# Save result keywords
_FULL_EFFECT_KEYWORDS = _compile_keywords([
    "full force", "full effect", "undiminished", "completely engulfs",
    "nothing can stop", "no resistance", "overwhelms",
])
_SHRUG_OFF_KEYWORDS = _compile_keywords([
    "shrugs off", "unaffected", "no effect", "completely resists",
    "immune", "unfazed", "unharmed", "harmless",
])

# Condition reference keywords (soft match for RV-004)
_CONDITION_MENTION_MAP = {
    "prone": ["prone", "knocked down", "falls", "sprawled", "on the ground", "face down"],
    "grappled": ["grappled", "grabbed", "seized", "held", "restrained", "wrestling"],
    "stunned": ["stunned", "dazed", "reeling", "staggered"],
    "blinded": ["blinded", "blind", "cannot see", "sightless"],
    "deafened": ["deafened", "deaf", "cannot hear"],
    "paralyzed": ["paralyzed", "paralysed", "frozen", "cannot move", "immobilized"],
    "frightened": ["frightened", "scared", "terrified", "fearful", "panicked"],
    "entangled": ["entangled", "tangled", "ensnared", "caught", "webbed"],
    "fatigued": ["fatigued", "tired", "weary", "exhausted"],
    "exhausted": ["exhausted", "spent", "drained"],
    "sickened": ["sickened", "nauseous", "queasy", "ill"],
    "nauseated": ["nauseated", "retching", "nauseous"],
    "dazzled": ["dazzled", "squinting", "blinking"],
    "fascinated": ["fascinated", "mesmerized", "entranced", "captivated"],
    "shaken": ["shaken", "unnerved", "rattled"],
    "confused": ["confused", "disoriented", "bewildered"],
    "haste": ["quickened", "sped", "hastened", "accelerated", "blur of speed"],
    "invisible": ["invisible", "vanished", "unseen", "disappeared"],
    "flat-footed": ["flat-footed", "caught off guard", "unaware"],
}

# Delivery mode directional language
_DELIVERY_MODE_KEYWORDS = {
    "cone": ["cone", "fan", "spread", "sweeps", "arc", "blast"],
    "line": ["line", "beam", "ray", "bolt", "streak", "lance"],
    "projectile": ["hurls", "launches", "fires", "shoots", "flings", "throws"],
    "touch": ["touches", "lays hands", "reaches out", "grasps", "contact"],
    "burst_from_point": ["erupts", "explodes", "detonates", "bursts", "blooms"],
    "aura": ["radiates", "emanates", "surrounds", "pulses outward"],
    "gaze": ["gaze", "eyes", "stare", "glare", "look"],
    "emanation": ["emanates", "radiates", "pulses", "waves"],
}


# ==============================================================================
# NARRATION VALIDATOR
# ==============================================================================


class NarrationValidator:
    """Unified narration validation against NarrativeBrief truth frame.

    Runs P0 negative rules (FAIL) and P1 positive rules (WARN) against
    Spark output. Returns ValidationResult with actionable rule IDs.
    """

    def validate(self, narration_text: str, brief: Any) -> ValidationResult:
        """Validate narration text against NarrativeBrief truth frame.

        Args:
            narration_text: Spark's generated narration text
            brief: NarrativeBrief truth frame

        Returns:
            ValidationResult with verdict and violations
        """
        violations: List[RuleViolation] = []
        text_lower = narration_text.lower()

        # === P0 NEGATIVE RULES (FAIL) ===
        violations.extend(self._check_rv001_hit_miss(text_lower, brief))
        violations.extend(self._check_rv002_defeat(text_lower, brief))
        violations.extend(self._check_rv008_save_result(text_lower, brief))
        violations.extend(self._check_rv005_contraindications(text_lower, brief))

        # === P1 POSITIVE/STRUCTURAL RULES (WARN) ===
        violations.extend(self._check_rv003_severity(text_lower, brief))
        violations.extend(self._check_rv004_condition(text_lower, brief))
        violations.extend(self._check_rv007_delivery_mode(text_lower, brief))

        # Determine verdict
        if any(v.severity == "FAIL" for v in violations):
            verdict = "FAIL"
        elif violations:
            verdict = "WARN"
        else:
            verdict = "PASS"

        return ValidationResult(
            verdict=verdict,
            violations=tuple(violations),
        )

    # ------------------------------------------------------------------
    # P0 RULES
    # ------------------------------------------------------------------

    def _check_rv001_hit_miss(self, text: str, brief: Any) -> List[RuleViolation]:
        """RV-001: Hit/Miss Consistency.

        If action_type == "attack_hit": must NOT contain miss-language.
        If action_type == "attack_miss": must NOT contain hit-language.
        """
        violations = []
        action = getattr(brief, "action_type", "")

        if "attack_hit" in action or "critical" in action:
            for pattern in _MISS_PATTERNS:
                match = pattern.search(text)
                if match:
                    violations.append(RuleViolation(
                        rule_id="RV-001",
                        severity="FAIL",
                        detail=f"Hit narration contains miss-language: '{match.group()}'",
                    ))
                    break  # One violation per rule suffices

        elif "attack_miss" in action:
            for pattern in _HIT_PATTERNS:
                match = pattern.search(text)
                if match:
                    violations.append(RuleViolation(
                        rule_id="RV-001",
                        severity="FAIL",
                        detail=f"Miss narration contains hit-language: '{match.group()}'",
                    ))
                    break

        return violations

    def _check_rv002_defeat(self, text: str, brief: Any) -> List[RuleViolation]:
        """RV-002: Defeat Consistency.

        If target_defeated == True: must NOT contain standing-language.
        If target_defeated == False: must NOT contain defeat-language.
        """
        violations = []
        defeated = getattr(brief, "target_defeated", False)

        if defeated:
            for pattern in _STANDING_PATTERNS:
                match = pattern.search(text)
                if match:
                    violations.append(RuleViolation(
                        rule_id="RV-002",
                        severity="FAIL",
                        detail=f"Defeat narration contains standing-language: '{match.group()}'",
                    ))
                    break
        else:
            # Only check for non-combat tokens that shouldn't have defeat
            action = getattr(brief, "action_type", "")
            # Don't flag defeat keywords if the narration is for a defeat-related action
            if "defeat" not in action:
                for pattern in _DEFEAT_PATTERNS:
                    match = pattern.search(text)
                    if match:
                        violations.append(RuleViolation(
                            rule_id="RV-002",
                            severity="FAIL",
                            detail=f"Non-defeat narration contains defeat-language: '{match.group()}'",
                        ))
                        break

        return violations

    def _check_rv008_save_result(self, text: str, brief: Any) -> List[RuleViolation]:
        """RV-008: Save Result Consistency.

        If action_type == "spell_resisted": must NOT describe full unmitigated effect.
        If action_type == "spell_damage_dealt": must NOT describe target shrugging off.
        """
        violations = []
        action = getattr(brief, "action_type", "")

        if action == "spell_resisted":
            for pattern in _FULL_EFFECT_KEYWORDS:
                match = pattern.search(text)
                if match:
                    violations.append(RuleViolation(
                        rule_id="RV-008",
                        severity="FAIL",
                        detail=f"Resisted-spell narration describes full effect: '{match.group()}'",
                    ))
                    break

        elif action == "spell_damage_dealt":
            for pattern in _SHRUG_OFF_KEYWORDS:
                match = pattern.search(text)
                if match:
                    violations.append(RuleViolation(
                        rule_id="RV-008",
                        severity="FAIL",
                        detail=f"Spell-damage narration describes target shrugging off: '{match.group()}'",
                    ))
                    break

        return violations

    def _check_rv005_contraindications(self, text: str, brief: Any) -> List[RuleViolation]:
        """RV-005: Contraindication Enforcement (Layer B).

        If presentation_semantics.contraindications is non-empty: narration must NOT
        contain any contraindicated term.

        Dormant when presentation_semantics is None.
        """
        violations = []
        semantics = getattr(brief, "presentation_semantics", None)
        if semantics is None:
            return violations

        contraindications = getattr(semantics, "contraindications", ())
        if not contraindications:
            return violations

        for term in contraindications:
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            match = pattern.search(text)
            if match:
                violations.append(RuleViolation(
                    rule_id="RV-005",
                    severity="FAIL",
                    detail=f"Narration contains contraindicated term: '{match.group()}'",
                ))
                break  # One violation per rule

        return violations

    # ------------------------------------------------------------------
    # P1 RULES
    # ------------------------------------------------------------------

    def _check_rv003_severity(self, text: str, brief: Any) -> List[RuleViolation]:
        """RV-003: Severity-Narration Alignment.

        If severity == "minor": must NOT contain severity-inflation keywords.
        If severity in ("lethal", "devastating"): must NOT contain severity-deflation keywords.
        """
        violations = []
        severity = getattr(brief, "severity", "minor")

        # Check inflation
        inflation_keywords = SEVERITY_INFLATION.get(severity, [])
        if inflation_keywords:
            patterns = _compile_keywords(inflation_keywords)
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    violations.append(RuleViolation(
                        rule_id="RV-003",
                        severity="WARN",
                        detail=f"Severity '{severity}' narration uses inflated language: '{match.group()}'",
                    ))
                    break

        # Check deflation
        deflation_keywords = SEVERITY_DEFLATION.get(severity, [])
        if deflation_keywords:
            patterns = _compile_keywords(deflation_keywords)
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    violations.append(RuleViolation(
                        rule_id="RV-003",
                        severity="WARN",
                        detail=f"Severity '{severity}' narration uses deflated language: '{match.group()}'",
                    ))
                    break

        return violations

    def _check_rv004_condition(self, text: str, brief: Any) -> List[RuleViolation]:
        """RV-004: Condition Consistency.

        If condition_applied is set: narration should reference the condition.
        If condition_removed is set: narration should reference removal.
        Soft match — at least one keyword from the condition's keyword list.
        """
        violations = []

        # Check condition_applied
        condition_applied = getattr(brief, "condition_applied", None)
        if condition_applied:
            keywords = _CONDITION_MENTION_MAP.get(condition_applied.lower(), [condition_applied.lower()])
            found = any(kw in text for kw in keywords)
            if not found:
                violations.append(RuleViolation(
                    rule_id="RV-004",
                    severity="WARN",
                    detail=f"Condition '{condition_applied}' applied but not referenced in narration",
                ))

        # Check condition_removed
        condition_removed = getattr(brief, "condition_removed", None)
        if condition_removed:
            keywords = _CONDITION_MENTION_MAP.get(condition_removed.lower(), [condition_removed.lower()])
            # For removal, also accept "no longer", "shakes off", "recovers"
            removal_phrases = ["no longer", "shakes off", "recovers", "breaks free", "gets up",
                               "rises", "stands"]
            found_condition = any(kw in text for kw in keywords)
            found_removal = any(phrase in text for phrase in removal_phrases)
            if not (found_condition or found_removal):
                violations.append(RuleViolation(
                    rule_id="RV-004",
                    severity="WARN",
                    detail=f"Condition '{condition_removed}' removed but not referenced in narration",
                ))

        return violations

    def _check_rv007_delivery_mode(self, text: str, brief: Any) -> List[RuleViolation]:
        """RV-007: Delivery Mode Consistency (Layer B).

        If presentation_semantics.delivery_mode is set: narration should contain
        language consistent with delivery mode.

        Dormant when presentation_semantics is None.
        """
        violations = []
        semantics = getattr(brief, "presentation_semantics", None)
        if semantics is None:
            return violations

        delivery_mode = getattr(semantics, "delivery_mode", None)
        if delivery_mode is None:
            return violations

        # Get the string value (could be an enum)
        mode_str = delivery_mode.value if hasattr(delivery_mode, "value") else str(delivery_mode)
        keywords = _DELIVERY_MODE_KEYWORDS.get(mode_str, [])
        if not keywords:
            return violations

        found = any(kw in text for kw in keywords)
        if not found:
            violations.append(RuleViolation(
                rule_id="RV-007",
                severity="WARN",
                detail=f"Delivery mode '{mode_str}' not reflected in narration language",
            ))

        return violations
