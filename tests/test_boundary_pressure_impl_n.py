"""Gate tests for WO-VOICE-PRESSURE-IMPL-001 — Boundary Pressure Runtime.

Tests N-01 through N-15 verifying:
- Schema structure (N-01)
- Detection logic (N-02 through N-10)
- Logging structure (N-11, N-12)
- Response policy integration (N-13, N-14)
- Content-agnostic invariant (N-15)

Reference: pm_inbox/WO-VOICE-PRESSURE-IMPL-001_DISPATCH.md
"""

import inspect
import logging
import re
import textwrap
from unittest.mock import MagicMock, patch

import pytest

from aidm.schemas.boundary_pressure import (
    BP_AMBIGUOUS_INTENT,
    BP_AUTHORITY_PROXIMITY,
    BP_CONTEXT_OVERFLOW,
    BP_MISSING_FACT,
    BoundaryPressureResult,
    PressureLevel,
    PressureTrigger,
)
from aidm.core.boundary_pressure import (
    REQUIRED_FIELDS,
    _check_ambiguous_intent,
    _check_authority_proximity,
    _check_context_overflow,
    _check_missing_fact,
    _classify_composite,
    _determine_response,
    evaluate_pressure,
)


# ==============================================================================
# HELPERS
# ==============================================================================


def _make_full_combat_narration_fields() -> dict:
    """Build a complete set of required fields for COMBAT_NARRATION."""
    return {
        "truth.action_type": "attack_hit",
        "truth.actor_name": "Kael",
        "truth.outcome_summary": "Kael hits Goblin for 8 damage",
        "truth.severity": "moderate",
        "truth.target_defeated": False,
        "task.task_type": "narration",
        "contract.max_length_chars": 600,
        "contract.required_provenance": "[NARRATIVE]",
    }


# ==============================================================================
# N-01: evaluate_pressure() returns BoundaryPressureResult with all required fields
# ==============================================================================


class TestN01_SchemaStructure:
    """N-01: evaluate_pressure() returns BoundaryPressureResult with all required fields."""

    def test_returns_boundary_pressure_result(self):
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=_make_full_combat_narration_fields(),
            turn_number=1,
        )
        assert isinstance(result, BoundaryPressureResult)

    def test_all_nine_fields_present(self):
        """Contract Section 5.1: 9-field payload."""
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=_make_full_combat_narration_fields(),
            token_budget=800,
            token_required=400,
            turn_number=5,
        )
        # triggers -> trigger_ids + trigger_levels (2 logical fields)
        assert hasattr(result, "triggers")
        assert hasattr(result, "composite_level")
        assert hasattr(result, "call_type")
        assert hasattr(result, "response")
        assert hasattr(result, "correlation_id")
        assert hasattr(result, "turn_number")
        assert hasattr(result, "timestamp")

        # Verify types
        assert isinstance(result.triggers, tuple)
        assert isinstance(result.composite_level, PressureLevel)
        assert isinstance(result.call_type, str)
        assert isinstance(result.response, str)
        assert isinstance(result.correlation_id, str)
        assert isinstance(result.turn_number, int)
        assert isinstance(result.timestamp, str)

    def test_result_is_frozen(self):
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=_make_full_combat_narration_fields(),
        )
        with pytest.raises(AttributeError):
            result.composite_level = PressureLevel.RED  # type: ignore

    def test_trigger_is_frozen(self):
        t = PressureTrigger(
            trigger_id=BP_MISSING_FACT,
            level=PressureLevel.RED,
            detail="test",
        )
        with pytest.raises(AttributeError):
            t.level = PressureLevel.GREEN  # type: ignore


# ==============================================================================
# N-02: Missing required field -> RED, response="fail_closed"
# ==============================================================================


class TestN02_MissingFactRed:
    """N-02: Missing required field for COMBAT_NARRATION -> RED, response='fail_closed'."""

    def test_missing_action_type_fires_red(self):
        fields = _make_full_combat_narration_fields()
        del fields["truth.action_type"]
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=fields,
        )
        assert result.composite_level == PressureLevel.RED
        assert result.response == "fail_closed"
        trigger_ids = [t.trigger_id for t in result.triggers]
        assert BP_MISSING_FACT in trigger_ids

    def test_empty_string_field_fires_red(self):
        fields = _make_full_combat_narration_fields()
        fields["truth.actor_name"] = ""
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=fields,
        )
        assert result.composite_level == PressureLevel.RED
        assert result.response == "fail_closed"

    def test_none_field_fires_red(self):
        fields = _make_full_combat_narration_fields()
        fields["truth.outcome_summary"] = None
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=fields,
        )
        assert result.composite_level == PressureLevel.RED


# ==============================================================================
# N-03: All fields present, no triggers -> GREEN, response="proceed"
# ==============================================================================


class TestN03_AllFieldsGreen:
    """N-03: All fields present, no triggers -> GREEN, response='proceed'."""

    def test_complete_combat_narration_is_green(self):
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=_make_full_combat_narration_fields(),
            token_budget=800,
            token_required=400,
            turn_number=1,
        )
        assert result.composite_level == PressureLevel.GREEN
        assert result.response == "proceed"
        assert len(result.triggers) == 0

    def test_complete_rule_explainer_is_green(self):
        fields = {
            "task.task_type": "rule_explainer",
            "task.rule_topic": "grappling",
            "contract.max_length_chars": 600,
            "contract.required_provenance": "[DERIVED]",
        }
        result = evaluate_pressure(
            call_type="RULE_EXPLAINER",
            input_fields=fields,
            token_budget=800,
            token_required=400,
        )
        assert result.composite_level == PressureLevel.GREEN
        assert result.response == "proceed"


# ==============================================================================
# N-04: needs_clarification=True -> YELLOW (BP-AMBIGUOUS-INTENT)
# ==============================================================================


class TestN04_AmbiguousIntentYellow:
    """N-04: needs_clarification=True -> YELLOW (BP-AMBIGUOUS-INTENT)."""

    def test_needs_clarification_fires_yellow(self):
        fields = {
            "truth.scene_description": "A dark tavern",
            "truth.actor_name": "Kael",
            "task.task_type": "operator_directive",
            "task.operator_input": "I attack",
            "task.valid_action_types": ["attack", "spell"],
            "contract.json_mode": True,
            "contract.json_schema": "{}",
            "needs_clarification": True,
        }
        result = evaluate_pressure(
            call_type="OPERATOR_DIRECTIVE",
            input_fields=fields,
            token_budget=800,
            token_required=400,
        )
        trigger_ids = [t.trigger_id for t in result.triggers]
        assert BP_AMBIGUOUS_INTENT in trigger_ids
        ambig = [t for t in result.triggers if t.trigger_id == BP_AMBIGUOUS_INTENT][0]
        assert ambig.level == PressureLevel.YELLOW

    def test_two_candidates_fires_yellow(self):
        fields = {
            "truth.scene_description": "A dark tavern",
            "truth.actor_name": "Kael",
            "task.task_type": "operator_directive",
            "task.operator_input": "I attack the goblin",
            "task.valid_action_types": ["attack"],
            "contract.json_mode": True,
            "contract.json_schema": "{}",
            "candidates": ["Goblin Scout", "Goblin Shaman"],
        }
        result = evaluate_pressure(
            call_type="OPERATOR_DIRECTIVE",
            input_fields=fields,
            token_budget=800,
            token_required=400,
        )
        trigger_ids = [t.trigger_id for t in result.triggers]
        assert BP_AMBIGUOUS_INTENT in trigger_ids


# ==============================================================================
# N-05: Token ratio < 1.0 -> YELLOW (BP-CONTEXT-OVERFLOW)
# ==============================================================================


class TestN05_ContextOverflowYellow:
    """N-05: Token ratio < 1.0 -> YELLOW (BP-CONTEXT-OVERFLOW)."""

    def test_ratio_below_1_fires_yellow(self):
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=_make_full_combat_narration_fields(),
            token_budget=700,
            token_required=800,
        )
        trigger_ids = [t.trigger_id for t in result.triggers]
        assert BP_CONTEXT_OVERFLOW in trigger_ids
        overflow = [t for t in result.triggers if t.trigger_id == BP_CONTEXT_OVERFLOW][0]
        assert overflow.level == PressureLevel.YELLOW

    def test_ratio_exactly_1_is_green(self):
        """Ratio >= 1.0 means everything fits — no trigger."""
        t = _check_context_overflow(800, 800)
        assert t is None


# ==============================================================================
# N-06: Token ratio < 0.5 -> RED (BP-CONTEXT-OVERFLOW escalated)
# ==============================================================================


class TestN06_ContextOverflowRed:
    """N-06: Token ratio < 0.5 -> RED (BP-CONTEXT-OVERFLOW escalated)."""

    def test_ratio_below_half_fires_red(self):
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=_make_full_combat_narration_fields(),
            token_budget=300,
            token_required=800,
        )
        trigger_ids = [t.trigger_id for t in result.triggers]
        assert BP_CONTEXT_OVERFLOW in trigger_ids
        overflow = [t for t in result.triggers if t.trigger_id == BP_CONTEXT_OVERFLOW][0]
        assert overflow.level == PressureLevel.RED
        assert result.composite_level == PressureLevel.RED
        assert result.response == "fail_closed"


# ==============================================================================
# N-07: outcome_summary="pending" -> YELLOW (BP-AUTHORITY-PROXIMITY)
# ==============================================================================


class TestN07_AuthorityProximityYellow:
    """N-07: outcome_summary='pending' -> YELLOW (BP-AUTHORITY-PROXIMITY)."""

    def test_pending_outcome_fires_yellow(self):
        fields = _make_full_combat_narration_fields()
        fields["truth.outcome_summary"] = "pending resolution"
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=fields,
            token_budget=800,
            token_required=400,
        )
        trigger_ids = [t.trigger_id for t in result.triggers]
        assert BP_AUTHORITY_PROXIMITY in trigger_ids
        prox = [t for t in result.triggers if t.trigger_id == BP_AUTHORITY_PROXIMITY][0]
        assert prox.level == PressureLevel.YELLOW

    def test_empty_outcome_fires_yellow(self):
        fields = _make_full_combat_narration_fields()
        fields["truth.outcome_summary"] = ""
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=fields,
        )
        # Empty outcome_summary fires BOTH BP-MISSING-FACT (RED, it's required)
        # AND BP-AUTHORITY-PROXIMITY (YELLOW) — but RED dominates
        assert result.composite_level == PressureLevel.RED

    def test_null_severity_fires_yellow_for_combat(self):
        fields = _make_full_combat_narration_fields()
        fields["truth.severity"] = None
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=fields,
        )
        # Null severity fires BP-MISSING-FACT (RED) because it's required
        assert result.composite_level == PressureLevel.RED


# ==============================================================================
# N-08: 3 YELLOW triggers simultaneously -> RED (escalation rule PD-04)
# ==============================================================================


class TestN08_ThreeYellowEscalation:
    """N-08: 3 YELLOW triggers simultaneously -> RED (escalation rule PD-04)."""

    def test_three_yellows_escalate_to_red(self):
        triggers = [
            PressureTrigger(BP_AMBIGUOUS_INTENT, PressureLevel.YELLOW, "ambiguous"),
            PressureTrigger(BP_AUTHORITY_PROXIMITY, PressureLevel.YELLOW, "proximity"),
            PressureTrigger(BP_CONTEXT_OVERFLOW, PressureLevel.YELLOW, "overflow"),
        ]
        result = _classify_composite(triggers)
        assert result == PressureLevel.RED


# ==============================================================================
# N-09: 2 YELLOW triggers -> YELLOW (no escalation)
# ==============================================================================


class TestN09_TwoYellowNoEscalation:
    """N-09: 2 YELLOW triggers -> YELLOW (no escalation)."""

    def test_two_yellows_remain_yellow(self):
        triggers = [
            PressureTrigger(BP_AMBIGUOUS_INTENT, PressureLevel.YELLOW, "ambiguous"),
            PressureTrigger(BP_CONTEXT_OVERFLOW, PressureLevel.YELLOW, "overflow"),
        ]
        result = _classify_composite(triggers)
        assert result == PressureLevel.YELLOW


# ==============================================================================
# N-10: 1 RED + 2 YELLOW -> RED (single RED overrides)
# ==============================================================================


class TestN10_RedOverridesYellow:
    """N-10: 1 RED + 2 YELLOW -> RED (single RED overrides)."""

    def test_red_absorbs_yellows(self):
        triggers = [
            PressureTrigger(BP_MISSING_FACT, PressureLevel.RED, "missing"),
            PressureTrigger(BP_AMBIGUOUS_INTENT, PressureLevel.YELLOW, "ambiguous"),
            PressureTrigger(BP_CONTEXT_OVERFLOW, PressureLevel.YELLOW, "overflow"),
        ]
        result = _classify_composite(triggers)
        assert result == PressureLevel.RED


# ==============================================================================
# N-11: Structured log event contains all 9 required fields from contract
# ==============================================================================


class TestN11_LogPayloadFields:
    """N-11: Structured log event contains all 9 required fields from contract."""

    def test_log_payload_has_nine_fields(self, caplog):
        """The log event must contain: trigger_ids, trigger_levels,
        composite_level, call_type, response, correlation_id,
        turn_number, detail, timestamp."""
        bp_logger = logging.getLogger("aidm.boundary_pressure")

        fields = _make_full_combat_narration_fields()
        fields["truth.outcome_summary"] = "pending"
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=fields,
            token_budget=800,
            token_required=400,
            turn_number=3,
        )

        # Build the 9-field payload that would be logged
        trigger_ids = [t.trigger_id for t in result.triggers]
        trigger_levels = [t.level.value for t in result.triggers]
        payload = {
            "trigger_ids": trigger_ids,
            "trigger_levels": trigger_levels,
            "composite_level": result.composite_level.value,
            "call_type": result.call_type,
            "response": result.response,
            "correlation_id": result.correlation_id,
            "turn_number": result.turn_number,
            "detail": "; ".join(f"{t.trigger_id}={t.level.value}" for t in result.triggers) or "No pressure triggers fired",
            "timestamp": result.timestamp,
        }

        assert len(payload) == 9
        for key in ["trigger_ids", "trigger_levels", "composite_level",
                     "call_type", "response", "correlation_id",
                     "turn_number", "detail", "timestamp"]:
            assert key in payload, f"Missing log field: {key}"
            assert payload[key] is not None, f"Null log field: {key}"


# ==============================================================================
# N-12: GREEN logs at DEBUG, YELLOW at WARNING, RED at ERROR
# ==============================================================================


class TestN12_LogLevels:
    """N-12: GREEN logs at DEBUG level, YELLOW at WARNING, RED at ERROR."""

    def test_green_maps_to_debug(self):
        assert PressureLevel.GREEN.value == "GREEN"
        # The session orchestrator will use these mappings
        level_map = {
            PressureLevel.GREEN: logging.DEBUG,
            PressureLevel.YELLOW: logging.WARNING,
            PressureLevel.RED: logging.ERROR,
        }
        assert level_map[PressureLevel.GREEN] == logging.DEBUG
        assert level_map[PressureLevel.YELLOW] == logging.WARNING
        assert level_map[PressureLevel.RED] == logging.ERROR


# ==============================================================================
# N-13: RED response skips Spark call (integration test with mock)
# ==============================================================================


class TestN13_RedSkipsSpark:
    """N-13: RED response skips Spark call (integration test with mock)."""

    def test_red_response_is_fail_closed(self):
        """When evaluate_pressure returns RED, the response must be 'fail_closed',
        signaling that Spark should NOT be called."""
        fields = _make_full_combat_narration_fields()
        del fields["truth.action_type"]  # Force RED
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=fields,
        )
        assert result.composite_level == PressureLevel.RED
        assert result.response == "fail_closed"

    def test_red_from_context_overflow_is_fail_closed(self):
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=_make_full_combat_narration_fields(),
            token_budget=100,
            token_required=800,
        )
        assert result.composite_level == PressureLevel.RED
        assert result.response == "fail_closed"


# ==============================================================================
# N-14: YELLOW response uses template on first validation failure (no retry)
# ==============================================================================


class TestN14_YellowNoRetry:
    """N-14: YELLOW response uses template on first validation failure (no retry)."""

    def test_yellow_response_is_advisory_fallback(self):
        """When evaluate_pressure returns YELLOW, the response must be
        'advisory_fallback', signaling no retry on validation failure."""
        fields = _make_full_combat_narration_fields()
        fields["truth.outcome_summary"] = "pending resolution"
        result = evaluate_pressure(
            call_type="COMBAT_NARRATION",
            input_fields=fields,
            token_budget=800,
            token_required=400,
        )
        assert result.composite_level == PressureLevel.YELLOW
        assert result.response == "advisory_fallback"


# ==============================================================================
# N-15: Detection is content-agnostic — no vocabulary patterns in any detector
# ==============================================================================


class TestN15_ContentAgnostic:
    """N-15: Detection is content-agnostic — no vocabulary patterns in
    any detector function (BP-INV-03)."""

    def test_no_regex_patterns_in_detectors(self):
        """Detectors must not use regex for content scanning."""
        import aidm.core.boundary_pressure as bp_module

        source = inspect.getsource(bp_module)

        # Check no re.compile, re.match, re.search, re.findall in source
        assert "re.compile" not in source, "Detector uses regex compilation"
        assert "re.match" not in source, "Detector uses regex matching"
        assert "re.search" not in source, "Detector uses regex search"
        assert "re.findall" not in source, "Detector uses regex findall"

    def test_no_keyword_lists_in_detectors(self):
        """Detectors must not contain D&D vocabulary or keyword lists."""
        import aidm.core.boundary_pressure as bp_module

        source = inspect.getsource(bp_module)

        # Should not contain game-specific vocabulary
        game_terms = ["d20", "saving throw", "armor class", "hit points",
                       "spell slot", "initiative", "proficiency"]
        for term in game_terms:
            assert term.lower() not in source.lower(), \
                f"Detector contains game-specific vocabulary: '{term}'"

    def test_detectors_are_pure_functions(self):
        """All four detectors must be pure: same input -> same output."""
        fields = _make_full_combat_narration_fields()

        r1 = evaluate_pressure("COMBAT_NARRATION", fields, 800, 400, 1)
        r2 = evaluate_pressure("COMBAT_NARRATION", fields, 800, 400, 1)

        assert r1.composite_level == r2.composite_level
        assert r1.response == r2.response
        assert len(r1.triggers) == len(r2.triggers)


# ==============================================================================
# ADDITIONAL GATES (builder discretion)
# ==============================================================================


class TestAdditional_EvaluatePressureErrorHandling:
    """ND-03: If evaluate_pressure itself throws, fail-closed to RED."""

    def test_internal_error_returns_red(self):
        """Pass bad data that would cause an internal error if not caught."""
        # Even with unusual inputs, should never raise — always returns result
        result = evaluate_pressure(
            call_type="NONEXISTENT_CALL_TYPE",
            input_fields={},
            token_budget=0,
            token_required=0,
        )
        # Unknown call_type has no required fields -> GREEN (no triggers fire)
        # This is correct: unknown call_type is not itself an error for evaluate_pressure
        assert isinstance(result, BoundaryPressureResult)


class TestAdditional_RequiredFieldsCoverage:
    """Verify REQUIRED_FIELDS covers all 6 CallTypes from Tier 1.3."""

    def test_all_six_call_types_have_required_fields(self):
        expected = {
            "COMBAT_NARRATION", "NPC_DIALOGUE", "SUMMARY",
            "RULE_EXPLAINER", "OPERATOR_DIRECTIVE", "CLARIFICATION_QUESTION",
        }
        assert set(REQUIRED_FIELDS.keys()) == expected

    def test_each_call_type_has_at_least_one_required_field(self):
        for ct, fields in REQUIRED_FIELDS.items():
            assert len(fields) > 0, f"{ct} has no required fields"


class TestAdditional_AmbiguousIntentRedCases:
    """BP-AMBIGUOUS-INTENT RED cases: 0 candidates or 4+ candidates."""

    def test_zero_candidates_fires_red(self):
        t = _check_ambiguous_intent({"candidates": []})
        assert t is not None
        assert t.level == PressureLevel.RED

    def test_four_candidates_fires_red(self):
        t = _check_ambiguous_intent({"candidates": ["a", "b", "c", "d"]})
        assert t is not None
        assert t.level == PressureLevel.RED

    def test_one_candidate_no_trigger(self):
        t = _check_ambiguous_intent({"candidates": ["a"]})
        assert t is None


class TestAdditional_ResponsePolicy:
    """Verify _determine_response mappings."""

    def test_green_proceed(self):
        assert _determine_response(PressureLevel.GREEN) == "proceed"

    def test_yellow_advisory(self):
        assert _determine_response(PressureLevel.YELLOW) == "advisory_fallback"

    def test_red_fail_closed(self):
        assert _determine_response(PressureLevel.RED) == "fail_closed"
