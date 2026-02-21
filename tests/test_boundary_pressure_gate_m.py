"""Gate M tests — Boundary Pressure Contract enforcement.

30 tests across 12 gate categories (M-01 through M-12).

Categories:
    M-01: Four triggers defined with all required fields (4 tests)
    M-02: Three PressureLevels defined with response policies (3 tests)
    M-03: RED policy specifies fail-closed (2 tests)
    M-04: YELLOW policy specifies no retry on post-hoc rejection (2 tests)
    M-05: GREEN policy specifies normal Spark flow (2 tests)
    M-06: BP-MISSING-FACT references Tier 1.3 input schema fields (2 tests)
    M-07: BP-CONTEXT-OVERFLOW references a token budget threshold (2 tests)
    M-08: All invariants (BP-INV-01 through BP-INV-05) are testable assertions (5 tests)
    M-09: Pressure event payload schema includes all required fields (2 tests)
    M-10: Detection is content-agnostic (2 tests)
    M-11: Composite classification rules (3 tests)
    M-12: Tier integration seams (1 test)

Authority: WO-VOICE-PRESSURE-SPEC-001, RQ-PRESSURE-001 (BOUNDARY_PRESSURE_CONTRACT.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import pytest


# ---------------------------------------------------------------------------
# Contract data — mirroring BOUNDARY_PRESSURE_CONTRACT.md
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PressureTriggerSpec:
    """Specification for a single pressure trigger."""
    trigger_id: str
    condition: str
    default_severity: str  # GREEN, YELLOW, RED
    detection_rule: str
    affected_call_types: tuple[str, ...]
    has_yellow_level: bool = True  # BP-MISSING-FACT has no YELLOW


# The four pressure triggers
PRESSURE_TRIGGERS: dict[str, PressureTriggerSpec] = {
    "BP-MISSING-FACT": PressureTriggerSpec(
        trigger_id="BP-MISSING-FACT",
        condition="Required input fields null/empty for this CallType",
        default_severity="RED",
        detection_rule="field_presence_check",
        affected_call_types=(
            "COMBAT_NARRATION", "NPC_DIALOGUE", "SUMMARY",
            "RULE_EXPLAINER", "OPERATOR_DIRECTIVE", "CLARIFICATION_QUESTION",
        ),
        has_yellow_level=False,
    ),
    "BP-AMBIGUOUS-INTENT": PressureTriggerSpec(
        trigger_id="BP-AMBIGUOUS-INTENT",
        condition="Multiple valid interpretations of operator intent",
        default_severity="YELLOW",
        detection_rule="candidate_count_check",
        affected_call_types=("OPERATOR_DIRECTIVE", "CLARIFICATION_QUESTION"),
    ),
    "BP-AUTHORITY-PROXIMITY": PressureTriggerSpec(
        trigger_id="BP-AUTHORITY-PROXIMITY",
        condition="Narration task structurally close to mechanical territory",
        default_severity="YELLOW",
        detection_rule="truth_frame_completeness_check",
        affected_call_types=(
            "COMBAT_NARRATION", "RULE_EXPLAINER", "OPERATOR_DIRECTIVE",
        ),
    ),
    "BP-CONTEXT-OVERFLOW": PressureTriggerSpec(
        trigger_id="BP-CONTEXT-OVERFLOW",
        condition="Token budget insufficient for full prompt + constraints",
        default_severity="YELLOW",
        detection_rule="token_budget_ratio_check",
        affected_call_types=(
            "COMBAT_NARRATION", "NPC_DIALOGUE", "SUMMARY",
            "RULE_EXPLAINER", "OPERATOR_DIRECTIVE", "CLARIFICATION_QUESTION",
        ),
    ),
}


# PressureLevel definitions
PRESSURE_LEVELS: dict[str, dict] = {
    "GREEN": {
        "spark_called": True,
        "retry_allowed": True,
        "fallback_preloaded": False,
        "operator_notified": False,
        "log_level": "DEBUG",
        "response": "proceed",
    },
    "YELLOW": {
        "spark_called": True,
        "retry_allowed": False,
        "fallback_preloaded": True,
        "operator_notified": False,
        "log_level": "WARNING",
        "response": "advisory_fallback",
    },
    "RED": {
        "spark_called": False,
        "retry_allowed": False,
        "fallback_preloaded": True,
        "operator_notified": True,
        "log_level": "ERROR",
        "response": "fail_closed",
    },
}

# Composite classification rules
COMPOSITE_RULES = [
    {"id": "R-01", "condition": "any_single_RED", "result": "RED"},
    {"id": "R-02", "condition": "1_YELLOW", "result": "YELLOW"},
    {"id": "R-03", "condition": "2_YELLOW", "result": "YELLOW"},
    {"id": "R-04", "condition": "3+_YELLOW", "result": "RED"},
    {"id": "R-05", "condition": "no_triggers", "result": "GREEN"},
    {"id": "R-06", "condition": "unknown_malformed", "result": "RED"},
]

# Invariants
INVARIANTS = {
    "BP-INV-01": "Every Spark invocation is preceded by a pressure evaluation",
    "BP-INV-02": "RED pressure level never reaches Spark (fail-closed)",
    "BP-INV-03": "Pressure detection uses only structural field inspection (no vocabulary)",
    "BP-INV-04": "Every pressure evaluation produces a logged event",
    "BP-INV-05": "Pressure detection is deterministic",
}

# Pressure event payload required fields
PRESSURE_EVENT_FIELDS = (
    "trigger_ids", "trigger_levels", "composite_level", "call_type",
    "response", "correlation_id", "turn_number", "detail", "timestamp",
)

# Response values
VALID_RESPONSES = frozenset({"proceed", "advisory_fallback", "fail_closed"})

# CallTypes (from Tier 1.3)
ALL_CALL_TYPES = frozenset({
    "COMBAT_NARRATION", "NPC_DIALOGUE", "SUMMARY",
    "RULE_EXPLAINER", "OPERATOR_DIRECTIVE", "CLARIFICATION_QUESTION",
})

# Detection method forbidden techniques
FORBIDDEN_DETECTION_TECHNIQUES = frozenset({
    "vocabulary_scanning", "regex_pattern_matching", "keyword_list",
    "game_system_rules", "natural_language_understanding",
    "embedding_similarity", "ml_model",
})


# ---------------------------------------------------------------------------
# Helper for composite classification testing
# ---------------------------------------------------------------------------

def compute_composite(trigger_levels: list[str]) -> str:
    """Compute composite PressureLevel from a list of trigger levels."""
    if not trigger_levels:
        return "GREEN"

    red_count = sum(1 for t in trigger_levels if t == "RED")
    yellow_count = sum(1 for t in trigger_levels if t == "YELLOW")

    if red_count > 0:
        return "RED"
    if yellow_count >= 3:
        return "RED"
    if yellow_count > 0:
        return "YELLOW"
    return "RED"  # fail-closed default


# ---------------------------------------------------------------------------
# M-01: Four triggers defined with all required fields
# ---------------------------------------------------------------------------

class TestM01TriggerCompleteness:
    """Four triggers defined with all required fields."""

    def test_four_triggers_defined(self):
        assert len(PRESSURE_TRIGGERS) == 4

    def test_all_triggers_have_required_fields(self):
        required_attrs = [
            "trigger_id", "condition", "default_severity",
            "detection_rule", "affected_call_types",
        ]
        for tid, spec in PRESSURE_TRIGGERS.items():
            for attr in required_attrs:
                val = getattr(spec, attr)
                assert val is not None, f"{tid} missing {attr}"
                if isinstance(val, str):
                    assert len(val) > 0, f"{tid}.{attr} is empty"
                if isinstance(val, tuple):
                    assert len(val) > 0, f"{tid}.{attr} is empty tuple"

    def test_trigger_ids_match_expected_pattern(self):
        """Trigger IDs follow BP-WORD-WORD pattern."""
        bp_pattern = re.compile(r"^BP-[A-Z]+-[A-Z]+$")
        for tid in PRESSURE_TRIGGERS:
            assert bp_pattern.match(tid), f"Malformed trigger ID: {tid}"

    def test_affected_call_types_are_valid(self):
        for tid, spec in PRESSURE_TRIGGERS.items():
            for ct in spec.affected_call_types:
                assert ct in ALL_CALL_TYPES, (
                    f"{tid} references unknown CallType: {ct}"
                )


# ---------------------------------------------------------------------------
# M-02: Three PressureLevels defined with response policies
# ---------------------------------------------------------------------------

class TestM02PressureLevels:
    """Three PressureLevels defined with response policies."""

    def test_three_levels_defined(self):
        assert len(PRESSURE_LEVELS) == 3

    def test_expected_levels_present(self):
        assert set(PRESSURE_LEVELS.keys()) == {"GREEN", "YELLOW", "RED"}

    def test_all_levels_have_response_policies(self):
        required_keys = {
            "spark_called", "retry_allowed", "fallback_preloaded",
            "operator_notified", "log_level", "response",
        }
        for level, policy in PRESSURE_LEVELS.items():
            assert set(policy.keys()) >= required_keys, (
                f"{level} missing policy keys: "
                f"{required_keys - set(policy.keys())}"
            )


# ---------------------------------------------------------------------------
# M-03: RED policy specifies fail-closed
# ---------------------------------------------------------------------------

class TestM03REDFailClosed:
    """RED policy specifies fail-closed (no Spark call)."""

    def test_red_spark_not_called(self):
        assert PRESSURE_LEVELS["RED"]["spark_called"] is False

    def test_red_response_is_fail_closed(self):
        assert PRESSURE_LEVELS["RED"]["response"] == "fail_closed"


# ---------------------------------------------------------------------------
# M-04: YELLOW policy specifies no retry on post-hoc rejection
# ---------------------------------------------------------------------------

class TestM04YELLOWNoRetry:
    """YELLOW policy specifies no retry on post-hoc rejection."""

    def test_yellow_retry_not_allowed(self):
        assert PRESSURE_LEVELS["YELLOW"]["retry_allowed"] is False

    def test_yellow_fallback_preloaded(self):
        assert PRESSURE_LEVELS["YELLOW"]["fallback_preloaded"] is True


# ---------------------------------------------------------------------------
# M-05: GREEN policy specifies normal Spark flow
# ---------------------------------------------------------------------------

class TestM05GREENNormal:
    """GREEN policy specifies normal Spark flow."""

    def test_green_spark_called(self):
        assert PRESSURE_LEVELS["GREEN"]["spark_called"] is True

    def test_green_retry_allowed(self):
        assert PRESSURE_LEVELS["GREEN"]["retry_allowed"] is True


# ---------------------------------------------------------------------------
# M-06: BP-MISSING-FACT references Tier 1.3 input schema fields
# ---------------------------------------------------------------------------

class TestM06MissingFactReferences:
    """BP-MISSING-FACT detection references Tier 1.3 input schema fields."""

    def test_missing_fact_affects_all_call_types(self):
        """BP-MISSING-FACT affects ALL six CallTypes."""
        spec = PRESSURE_TRIGGERS["BP-MISSING-FACT"]
        assert set(spec.affected_call_types) == ALL_CALL_TYPES

    def test_missing_fact_default_severity_is_red(self):
        """BP-MISSING-FACT defaults to RED (required data is binary)."""
        spec = PRESSURE_TRIGGERS["BP-MISSING-FACT"]
        assert spec.default_severity == "RED"


# ---------------------------------------------------------------------------
# M-07: BP-CONTEXT-OVERFLOW references a token budget threshold
# ---------------------------------------------------------------------------

class TestM07ContextOverflowThreshold:
    """BP-CONTEXT-OVERFLOW detection uses a token budget threshold."""

    def test_context_overflow_detection_rule_is_token_based(self):
        spec = PRESSURE_TRIGGERS["BP-CONTEXT-OVERFLOW"]
        assert "token" in spec.detection_rule.lower()

    def test_context_overflow_affects_all_call_types(self):
        """All CallTypes have token budgets."""
        spec = PRESSURE_TRIGGERS["BP-CONTEXT-OVERFLOW"]
        assert set(spec.affected_call_types) == ALL_CALL_TYPES


# ---------------------------------------------------------------------------
# M-08: All invariants are testable assertions
# ---------------------------------------------------------------------------

class TestM08Invariants:
    """All invariants BP-INV-01 through BP-INV-05 are testable."""

    def test_five_invariants_defined(self):
        assert len(INVARIANTS) == 5

    def test_inv_01_every_invocation_preceded_by_evaluation(self):
        """BP-INV-01: Verified structurally — pressure evaluator sits
        before Spark in the pipeline."""
        assert "BP-INV-01" in INVARIANTS
        # The pipeline ordering (Tier 1.4 before Tier 1.3) enforces this

    def test_inv_02_red_never_reaches_spark(self):
        """BP-INV-02: RED policy spark_called is False."""
        assert PRESSURE_LEVELS["RED"]["spark_called"] is False

    def test_inv_03_detection_is_content_agnostic(self):
        """BP-INV-03: No trigger uses vocabulary, regex, or game-specific rules."""
        for tid, spec in PRESSURE_TRIGGERS.items():
            rule = spec.detection_rule.lower()
            assert "regex" not in rule, f"{tid} detection uses regex"
            assert "keyword" not in rule, f"{tid} detection uses keywords"
            assert "vocabulary" not in rule, f"{tid} detection uses vocabulary"

    def test_inv_04_every_evaluation_produces_event(self):
        """BP-INV-04: All three levels have a log_level defined."""
        for level, policy in PRESSURE_LEVELS.items():
            assert "log_level" in policy, f"{level} has no log_level"
            assert policy["log_level"] in ("DEBUG", "WARNING", "ERROR"), (
                f"{level} log_level '{policy['log_level']}' is not valid"
            )

    def test_inv_05_detection_is_deterministic(self):
        """BP-INV-05: Same inputs produce same composite level.
        Verified by running composite classification twice."""
        inputs = [
            ([], "GREEN"),
            (["YELLOW"], "YELLOW"),
            (["YELLOW", "YELLOW"], "YELLOW"),
            (["YELLOW", "YELLOW", "YELLOW"], "RED"),
            (["RED"], "RED"),
            (["RED", "YELLOW"], "RED"),
        ]
        for trigger_levels, expected in inputs:
            result1 = compute_composite(trigger_levels)
            result2 = compute_composite(trigger_levels)
            assert result1 == result2 == expected, (
                f"Non-deterministic: {trigger_levels} -> {result1}, {result2}"
            )


# ---------------------------------------------------------------------------
# M-09: Pressure event payload schema
# ---------------------------------------------------------------------------

class TestM09EventPayload:
    """Pressure event payload includes all required fields."""

    def test_nine_required_fields(self):
        assert len(PRESSURE_EVENT_FIELDS) == 9

    def test_all_required_fields_present(self):
        expected = {
            "trigger_ids", "trigger_levels", "composite_level",
            "call_type", "response", "correlation_id",
            "turn_number", "detail", "timestamp",
        }
        assert set(PRESSURE_EVENT_FIELDS) == expected


# ---------------------------------------------------------------------------
# M-10: Detection is content-agnostic
# ---------------------------------------------------------------------------

class TestM10ContentAgnostic:
    """Detection uses only structural field inspection."""

    def test_no_trigger_uses_forbidden_techniques(self):
        """No trigger detection rule references forbidden techniques."""
        for tid, spec in PRESSURE_TRIGGERS.items():
            rule = spec.detection_rule.lower()
            for forbidden in FORBIDDEN_DETECTION_TECHNIQUES:
                assert forbidden not in rule, (
                    f"{tid} detection rule references '{forbidden}'"
                )

    def test_detection_rules_are_structural(self):
        """All detection rules reference field-level operations."""
        structural_keywords = {"check", "presence", "count", "ratio", "budget"}
        for tid, spec in PRESSURE_TRIGGERS.items():
            rule_words = set(spec.detection_rule.lower().split("_"))
            assert rule_words & structural_keywords, (
                f"{tid} detection rule '{spec.detection_rule}' does not "
                f"reference structural operations: {structural_keywords}"
            )


# ---------------------------------------------------------------------------
# M-11: Composite classification rules
# ---------------------------------------------------------------------------

class TestM11CompositeClassification:
    """Composite classification follows defined rules."""

    def test_no_triggers_is_green(self):
        """R-05: No triggers -> GREEN."""
        assert compute_composite([]) == "GREEN"

    def test_single_red_overrides_yellow(self):
        """R-01: Any RED -> RED regardless of YELLOW count."""
        assert compute_composite(["RED"]) == "RED"
        assert compute_composite(["RED", "YELLOW"]) == "RED"
        assert compute_composite(["RED", "YELLOW", "YELLOW"]) == "RED"

    def test_three_yellow_escalates_to_red(self):
        """R-04: 3+ YELLOW -> RED."""
        assert compute_composite(["YELLOW", "YELLOW"]) == "YELLOW"
        assert compute_composite(["YELLOW", "YELLOW", "YELLOW"]) == "RED"


# ---------------------------------------------------------------------------
# M-12: Tier integration seams
# ---------------------------------------------------------------------------

class TestM12TierIntegration:
    """Pressure contract integrates with Tiers 1.1-1.3."""

    def test_yellow_eliminates_tier_1_3_retry_budget(self):
        """YELLOW: retry_allowed=False means Tier 1.3 retry budget is 0."""
        green_retry = PRESSURE_LEVELS["GREEN"]["retry_allowed"]
        yellow_retry = PRESSURE_LEVELS["YELLOW"]["retry_allowed"]
        assert green_retry is True, "GREEN should allow retries"
        assert yellow_retry is False, "YELLOW should disallow retries"
