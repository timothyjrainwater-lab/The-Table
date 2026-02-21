#!/usr/bin/env python3
"""Boundary Pressure Contract Validator — checks contract structural completeness.

Usage:
    python scripts/check_boundary_pressure.py
    python scripts/check_boundary_pressure.py docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md

Exit code 0 if compliant, 1 if violations found.

Also importable:
    from scripts.check_boundary_pressure import check_boundary_pressure_contract, Violation
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants (mirrors BOUNDARY_PRESSURE_CONTRACT.md)
# ---------------------------------------------------------------------------

EXPECTED_TRIGGERS = frozenset({
    "BP-MISSING-FACT", "BP-AMBIGUOUS-INTENT",
    "BP-AUTHORITY-PROXIMITY", "BP-CONTEXT-OVERFLOW",
})

EXPECTED_LEVELS = frozenset({"GREEN", "YELLOW", "RED"})

EXPECTED_INVARIANTS = frozenset({
    "BP-INV-01", "BP-INV-02", "BP-INV-03", "BP-INV-04", "BP-INV-05",
})

EXPECTED_COMPOSITE_RULES = frozenset({
    "R-01", "R-02", "R-03", "R-04", "R-05", "R-06",
})

EXPECTED_EVENT_FIELDS = frozenset({
    "trigger_ids", "trigger_levels", "composite_level", "call_type",
    "response", "correlation_id", "turn_number", "detail", "timestamp",
})

EXPECTED_RESPONSE_VALUES = frozenset({
    "proceed", "advisory_fallback", "fail_closed",
})

EXPECTED_TIER_REFERENCES = frozenset({
    "TYPED_CALL_CONTRACT", "CLI_GRAMMAR_CONTRACT", "UNKNOWN_HANDLING_CONTRACT",
})

REQUIRED_PER_TRIGGER_SECTIONS = [
    "Detection Rule", "Affected CallTypes", "Fail-closed",
]

# Vocabulary-related terms that should NOT appear in detection rules
VOCABULARY_TERMS = [
    "regex", "keyword", "vocabulary", "pattern matching",
    "game-specific", "D&D-specific",
]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Violation:
    """A single contract compliance violation."""
    check_id: str
    message: str
    severity: str = "ERROR"

    def __str__(self) -> str:
        return f"[{self.severity}] {self.check_id}: {self.message}"


# ---------------------------------------------------------------------------
# Contract checks
# ---------------------------------------------------------------------------

def _check_triggers_present(text: str) -> list[Violation]:
    """Verify all 4 triggers are defined."""
    violations = []
    for trigger in sorted(EXPECTED_TRIGGERS):
        if trigger not in text:
            violations.append(Violation(
                "BP-01", f"Trigger '{trigger}' not found in contract"
            ))
    return violations


def _check_levels_present(text: str) -> list[Violation]:
    """Verify all 3 PressureLevels are defined."""
    violations = []
    for level in sorted(EXPECTED_LEVELS):
        if level not in text:
            violations.append(Violation(
                "BP-02", f"PressureLevel '{level}' not found in contract"
            ))
    return violations


def _check_invariants(text: str) -> list[Violation]:
    """Verify all 5 invariants are defined."""
    violations = []
    for inv in sorted(EXPECTED_INVARIANTS):
        if inv not in text:
            violations.append(Violation(
                "BP-03", f"Invariant '{inv}' not found in contract"
            ))
    return violations


def _check_composite_rules(text: str) -> list[Violation]:
    """Verify all 6 composite classification rules."""
    violations = []
    for rule in sorted(EXPECTED_COMPOSITE_RULES):
        if rule not in text:
            violations.append(Violation(
                "BP-04", f"Composite rule '{rule}' not found in contract"
            ))
    return violations


def _check_event_fields(text: str) -> list[Violation]:
    """Verify all 9 event payload fields are referenced."""
    violations = []
    for field_name in sorted(EXPECTED_EVENT_FIELDS):
        if field_name not in text:
            violations.append(Violation(
                "BP-05", f"Event payload field '{field_name}' not found"
            ))
    return violations


def _check_response_values(text: str) -> list[Violation]:
    """Verify all 3 response values are defined."""
    violations = []
    for resp in sorted(EXPECTED_RESPONSE_VALUES):
        if resp not in text:
            violations.append(Violation(
                "BP-06", f"Response value '{resp}' not found"
            ))
    return violations


def _check_tier_references(text: str) -> list[Violation]:
    """Verify cross-references to Tiers 1.1, 1.2, 1.3."""
    violations = []
    for ref in sorted(EXPECTED_TIER_REFERENCES):
        if ref not in text:
            violations.append(Violation(
                "BP-07", f"Tier reference '{ref}' not found"
            ))
    return violations


def _check_fail_closed_keyword(text: str) -> list[Violation]:
    """Verify fail-closed semantics are defined."""
    violations = []
    if "fail-closed" not in text.lower() and "fail_closed" not in text.lower():
        violations.append(Violation(
            "BP-08", "No 'fail-closed' semantics found"
        ))
    return violations


def _check_content_agnostic_claim(text: str) -> list[Violation]:
    """Verify contract claims content-agnostic detection."""
    violations = []
    if "content-agnostic" not in text.lower():
        violations.append(Violation(
            "BP-09", "No 'content-agnostic' claim found in contract"
        ))
    return violations


def _check_observability_section(text: str) -> list[Violation]:
    """Verify observability section exists."""
    violations = []
    if "Observability" not in text and "observability" not in text:
        violations.append(Violation(
            "BP-10", "No 'Observability' section found"
        ))
    return violations


def _check_detection_method_section(text: str) -> list[Violation]:
    """Verify detection method section exists."""
    violations = []
    if "Detection Method" not in text and "Detection Algorithm" not in text:
        violations.append(Violation(
            "BP-11", "No 'Detection Method' or 'Detection Algorithm' section found"
        ))
    return violations


# All checks
CONTRACT_CHECKS = [
    _check_triggers_present,
    _check_levels_present,
    _check_invariants,
    _check_composite_rules,
    _check_event_fields,
    _check_response_values,
    _check_tier_references,
    _check_fail_closed_keyword,
    _check_content_agnostic_claim,
    _check_observability_section,
    _check_detection_method_section,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_boundary_pressure_contract(text: str) -> list[Violation]:
    """Check contract text for structural completeness.

    Args:
        text: Full text of the BOUNDARY_PRESSURE_CONTRACT.md document.

    Returns:
        List of Violation objects. Empty list means compliant.
    """
    violations: list[Violation] = []
    for check_fn in CONTRACT_CHECKS:
        violations.extend(check_fn(text))
    return violations


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Run contract validator on the boundary pressure contract document."""
    default_path = Path("docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md")

    if len(sys.argv) >= 2:
        source = sys.argv[1]
        path = Path(source)
    else:
        path = default_path

    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        print(f"Usage: check_boundary_pressure.py [contract_file]", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    violations = check_boundary_pressure_contract(text)

    errors = [v for v in violations if v.severity == "ERROR"]
    warnings = [v for v in violations if v.severity == "WARNING"]

    if not violations:
        print(f"PASS: Contract is structurally complete. 0 violations.")
        return 0

    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s).\n")
    else:
        print(f"WARN: 0 errors, {len(warnings)} warning(s).\n")

    for v in violations:
        print(v)
        print()

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
