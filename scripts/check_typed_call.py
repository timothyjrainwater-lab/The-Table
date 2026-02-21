#!/usr/bin/env python3
"""Typed Call Contract Validator — checks contract structural completeness.

Usage:
    python scripts/check_typed_call.py
    python scripts/check_typed_call.py docs/contracts/TYPED_CALL_CONTRACT.md

Exit code 0 if compliant, 1 if violations found.

Also importable:
    from scripts.check_typed_call import check_typed_call_contract, Violation
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants (mirrors TYPED_CALL_CONTRACT.md)
# ---------------------------------------------------------------------------

EXPECTED_CALL_TYPES = frozenset({
    "COMBAT_NARRATION", "NPC_DIALOGUE", "SUMMARY",
    "RULE_EXPLAINER", "OPERATOR_DIRECTIVE", "CLARIFICATION_QUESTION",
})

EXPECTED_AUTHORITY_LEVELS = frozenset({
    "ATMOSPHERIC", "UNCERTAIN", "INFORMATIONAL", "NON-AUTHORITATIVE",
})

EXPECTED_PROVENANCE_TAGS = frozenset({
    "[NARRATIVE]", "[UNCERTAIN]", "[DERIVED]",
})

TIER_1_1_LINE_TYPES = frozenset({
    "TURN", "RESULT", "ALERT", "NARRATION", "PROMPT", "SYSTEM", "DETAIL",
})

EXPECTED_INVARIANTS = frozenset({
    "TC-INV-01", "TC-INV-02", "TC-INV-03", "TC-INV-04",
})

EXPECTED_PIPELINE_STAGES = [
    "GrammarShield",
    "ForbiddenClaimChecker",
    "EvidenceValidator",
]

EXPECTED_FORBIDDEN_CATEGORIES = frozenset({
    "mechanical_values", "rule_citations", "outcome_assertions",
})

# Per-CallType required sections (heading patterns)
REQUIRED_PER_TYPE_SECTIONS = [
    "Input Schema",
    "Output Schema",
    "Forbidden Claims",
    "Line Type Mapping",
    "Fallback",
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

def _check_call_types_present(text: str) -> list[Violation]:
    """Verify all 6 CallTypes are defined in the contract."""
    violations = []
    for ct in sorted(EXPECTED_CALL_TYPES):
        if ct not in text:
            violations.append(Violation(
                "CT-01", f"CallType '{ct}' not found in contract"
            ))
    return violations


def _check_authority_levels(text: str) -> list[Violation]:
    """Verify all 4 authority levels are defined."""
    violations = []
    for level in sorted(EXPECTED_AUTHORITY_LEVELS):
        if level not in text:
            violations.append(Violation(
                "CT-02", f"Authority level '{level}' not found in contract"
            ))
    return violations


def _check_provenance_tags(text: str) -> list[Violation]:
    """Verify all provenance tags are referenced."""
    violations = []
    for tag in sorted(EXPECTED_PROVENANCE_TAGS):
        if tag not in text:
            violations.append(Violation(
                "CT-03", f"Provenance tag '{tag}' not found in contract"
            ))
    return violations


def _check_invariants(text: str) -> list[Violation]:
    """Verify all 4 invariants are defined."""
    violations = []
    for inv in sorted(EXPECTED_INVARIANTS):
        if inv not in text:
            violations.append(Violation(
                "CT-04", f"Invariant '{inv}' not found in contract"
            ))
    return violations


def _check_pipeline_stages(text: str) -> list[Violation]:
    """Verify all 3 pipeline stages are defined."""
    violations = []
    for stage in EXPECTED_PIPELINE_STAGES:
        if stage not in text:
            violations.append(Violation(
                "CT-05", f"Pipeline stage '{stage}' not found in contract"
            ))
    return violations


def _check_forbidden_categories(text: str) -> list[Violation]:
    """Verify all 3 forbidden claim categories are defined."""
    violations = []
    for cat in sorted(EXPECTED_FORBIDDEN_CATEGORIES):
        if cat not in text:
            violations.append(Violation(
                "CT-06", f"Forbidden claim category '{cat}' not found in contract"
            ))
    return violations


def _check_per_type_completeness(text: str) -> list[Violation]:
    """Verify each CallType has required subsections."""
    violations = []
    for ct in sorted(EXPECTED_CALL_TYPES):
        for section in REQUIRED_PER_TYPE_SECTIONS:
            # Look for section heading near the CallType definition
            # Using a loose search — the section just needs to exist in the doc
            pattern = re.compile(
                rf"{re.escape(ct)}.*?{re.escape(section)}",
                re.DOTALL,
            )
            if not pattern.search(text):
                # Try reverse order too (section might come before CT name in heading)
                if section.lower() not in text.lower():
                    violations.append(Violation(
                        "CT-07",
                        f"CallType '{ct}': missing '{section}' section",
                        severity="WARNING",
                    ))
    return violations


def _check_tier_references(text: str) -> list[Violation]:
    """Verify Tier 1.1 and Tier 1.2 cross-references exist."""
    violations = []
    tier_refs = [
        ("CLI_GRAMMAR_CONTRACT", "Tier 1.1 contract reference"),
        ("UNKNOWN_HANDLING_CONTRACT", "Tier 1.2 contract reference"),
    ]
    for ref, desc in tier_refs:
        if ref not in text:
            violations.append(Violation(
                "CT-08", f"Missing {desc}: '{ref}' not referenced"
            ))
    return violations


def _check_no_box_provenance(text: str) -> list[Violation]:
    """Verify contract explicitly forbids [BOX] provenance from CallTypes."""
    violations = []
    if "[BOX]" not in text:
        violations.append(Violation(
            "CT-09",
            "[BOX] provenance not mentioned — contract should explicitly "
            "forbid CallTypes from producing [BOX]-tagged output",
        ))
    return violations


def _check_latency_ceilings(text: str) -> list[Violation]:
    """Verify latency ceilings are defined (the word 'latency' or 'Latency' appears)."""
    violations = []
    if "latency" not in text.lower():
        violations.append(Violation(
            "CT-10", "No latency ceiling definitions found in contract"
        ))
    return violations


def _check_fallback_section(text: str) -> list[Violation]:
    """Verify a template fallback section exists."""
    violations = []
    if "Template Fallback" not in text and "Fallback Guarantee" not in text:
        violations.append(Violation(
            "CT-11", "No 'Template Fallback' or 'Fallback Guarantee' section found"
        ))
    return violations


# All checks
CONTRACT_CHECKS = [
    _check_call_types_present,
    _check_authority_levels,
    _check_provenance_tags,
    _check_invariants,
    _check_pipeline_stages,
    _check_forbidden_categories,
    _check_per_type_completeness,
    _check_tier_references,
    _check_no_box_provenance,
    _check_latency_ceilings,
    _check_fallback_section,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_typed_call_contract(text: str) -> list[Violation]:
    """Check contract text for structural completeness.

    Args:
        text: Full text of the TYPED_CALL_CONTRACT.md document.

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
    """Run contract validator on the typed call contract document."""
    default_path = Path("docs/contracts/TYPED_CALL_CONTRACT.md")

    if len(sys.argv) >= 2:
        source = sys.argv[1]
        path = Path(source)
    else:
        path = default_path

    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        print(f"Usage: check_typed_call.py [contract_file]", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    violations = check_typed_call_contract(text)

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
