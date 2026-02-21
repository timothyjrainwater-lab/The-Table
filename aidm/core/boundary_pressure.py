"""Boundary Pressure Detection — Pure function pressure evaluation.

Implements the four pressure detectors and composite classification logic
per the Boundary Pressure Contract (RQ-PRESSURE-001, Tier 1.4).

All detectors are pure functions: no side effects, no state mutation,
no vocabulary scanning, no game-specific patterns. Detection uses ONLY
structural field inspection (BP-INV-03, BP-INV-05).

REQUIRED_FIELDS sourced from TYPED_CALL_CONTRACT.md (Tier 1.3) input schemas.

Reference: docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from aidm.schemas.boundary_pressure import (
    BP_AMBIGUOUS_INTENT,
    BP_AUTHORITY_PROXIMITY,
    BP_CONTEXT_OVERFLOW,
    BP_MISSING_FACT,
    BoundaryPressureResult,
    PressureLevel,
    PressureTrigger,
)


# ==============================================================================
# REQUIRED FIELDS PER CALLTYPE (from Tier 1.3 input schemas)
# ==============================================================================

REQUIRED_FIELDS: Dict[str, Tuple[str, ...]] = {
    "COMBAT_NARRATION": (
        "truth.action_type",
        "truth.actor_name",
        "truth.outcome_summary",
        "truth.severity",
        "truth.target_defeated",
        "task.task_type",
        "contract.max_length_chars",
        "contract.required_provenance",
    ),
    "NPC_DIALOGUE": (
        "truth.actor_name",
        "truth.scene_description",
        "task.task_type",
        "task.npc_name",
        "task.npc_personality",
        "task.dialogue_context",
        "contract.max_length_chars",
        "contract.required_provenance",
    ),
    "SUMMARY": (
        "truth.scene_description",
        "memory.previous_narrations",
        "memory.session_facts",
        "task.task_type",
        "task.events_to_summarize",
        "contract.json_mode",
        "contract.json_schema",
        "contract.max_length_chars",
    ),
    "RULE_EXPLAINER": (
        "task.task_type",
        "task.rule_topic",
        "contract.max_length_chars",
        "contract.required_provenance",
    ),
    "OPERATOR_DIRECTIVE": (
        "truth.scene_description",
        "truth.actor_name",
        "task.task_type",
        "task.operator_input",
        "task.valid_action_types",
        "contract.json_mode",
        "contract.json_schema",
    ),
    "CLARIFICATION_QUESTION": (
        "task.task_type",
        "task.ambiguity_type",
        "task.operator_input",
        "truth.actor_name",
        "contract.max_length_chars",
        "contract.required_provenance",
    ),
}


# ==============================================================================
# DETECTOR: BP-MISSING-FACT (Section 1.1)
# ==============================================================================


def _check_missing_fact(
    call_type: str,
    input_fields: Dict[str, object],
) -> Optional[PressureTrigger]:
    """Check for missing required fields per CallType input schema.

    Detection rule: For the invocation's CallType, enumerate all fields
    marked Required: YES in the Tier 1.3 input schema. If any required
    field is null, empty string, empty list, or absent, this trigger fires.

    BP-MISSING-FACT has no YELLOW level — it fires RED or not at all.

    Args:
        call_type: The CallType being invoked
        input_fields: Dict of field_name -> value (dot-notation keys)

    Returns:
        PressureTrigger at RED if any required field is missing, else None
    """
    required = REQUIRED_FIELDS.get(call_type)
    if required is None:
        return None

    for field_name in required:
        value = input_fields.get(field_name)
        if _is_empty(value):
            return PressureTrigger(
                trigger_id=BP_MISSING_FACT,
                level=PressureLevel.RED,
                detail=f"Required field '{field_name}' is missing/empty for {call_type}",
            )

    return None


# ==============================================================================
# DETECTOR: BP-AMBIGUOUS-INTENT (Section 1.2)
# ==============================================================================


def _check_ambiguous_intent(
    input_fields: Dict[str, object],
) -> Optional[PressureTrigger]:
    """Check for ambiguous operator intent.

    Detection rule: Structural field inspection of candidate count
    and needs_clarification flag. Content-agnostic — does not parse
    natural language.

    Affected CallTypes: OPERATOR_DIRECTIVE, CLARIFICATION_QUESTION
    (caller must filter before calling).

    Args:
        input_fields: Dict of field_name -> value

    Returns:
        PressureTrigger at YELLOW or RED depending on candidate count, else None
    """
    needs_clarification = input_fields.get("needs_clarification", False)
    candidates = input_fields.get("candidates", None)

    candidate_count = 0
    if isinstance(candidates, (list, tuple)):
        candidate_count = len(candidates)

    # RED: 0 candidates (routing failure) or 4+ candidates
    if candidates is not None and (candidate_count == 0 or candidate_count >= 4):
        return PressureTrigger(
            trigger_id=BP_AMBIGUOUS_INTENT,
            level=PressureLevel.RED,
            detail=f"Ambiguous intent: {candidate_count} candidates (expected 1-3)",
        )

    # YELLOW: 2-3 candidates or needs_clarification=True
    if candidate_count >= 2 or needs_clarification:
        return PressureTrigger(
            trigger_id=BP_AMBIGUOUS_INTENT,
            level=PressureLevel.YELLOW,
            detail=f"Ambiguous intent: {candidate_count} candidates, needs_clarification={needs_clarification}",
        )

    return None


# ==============================================================================
# DETECTOR: BP-AUTHORITY-PROXIMITY (Section 1.3)
# ==============================================================================


def _check_authority_proximity(
    call_type: str,
    input_fields: Dict[str, object],
) -> Optional[PressureTrigger]:
    """Check for structural proximity to authority boundary violations.

    Detection rule: Structural field inspection of truth channel.
    Checks sentinel values and field presence — not content.

    Affected CallTypes: COMBAT_NARRATION, RULE_EXPLAINER, OPERATOR_DIRECTIVE

    Args:
        call_type: The CallType being invoked
        input_fields: Dict of field_name -> value

    Returns:
        PressureTrigger at YELLOW if proximity signal detected, else None
    """
    # Only check outcome_summary if the field is present in input_fields.
    # CallTypes that don't include truth.outcome_summary (e.g., RULE_EXPLAINER)
    # should not trigger based on its absence.
    if "truth.outcome_summary" in input_fields:
        outcome_summary = input_fields["truth.outcome_summary"]
        if isinstance(outcome_summary, str):
            if outcome_summary == "" or "pending" in outcome_summary:
                return PressureTrigger(
                    trigger_id=BP_AUTHORITY_PROXIMITY,
                    level=PressureLevel.YELLOW,
                    detail="Authority proximity: outcome_summary contains 'pending' or is empty",
                )

    if call_type == "COMBAT_NARRATION":
        severity = input_fields.get("truth.severity")
        if severity is None:
            return PressureTrigger(
                trigger_id=BP_AUTHORITY_PROXIMITY,
                level=PressureLevel.YELLOW,
                detail="Authority proximity: severity is null for COMBAT_NARRATION",
            )

    return None


# ==============================================================================
# DETECTOR: BP-CONTEXT-OVERFLOW (Section 1.4)
# ==============================================================================


def _check_context_overflow(
    token_budget: int,
    token_required: int,
) -> Optional[PressureTrigger]:
    """Check for token budget overflow.

    Detection rule: Compute inclusion_ratio = budget / required.
    Ratio < 0.5 -> RED. Ratio < 1.0 -> YELLOW. >= 1.0 -> None.

    Content-agnostic — numerical comparison only.

    Args:
        token_budget: Available tokens for this CallType
        token_required: Estimated tokens needed for required content

    Returns:
        PressureTrigger at YELLOW or RED depending on ratio, else None
    """
    if token_budget <= 0 or token_required <= 0:
        return PressureTrigger(
            trigger_id=BP_CONTEXT_OVERFLOW,
            level=PressureLevel.RED,
            detail=f"Context overflow: invalid budget={token_budget} or required={token_required}",
        )

    ratio = token_budget / token_required

    if ratio < 0.5:
        return PressureTrigger(
            trigger_id=BP_CONTEXT_OVERFLOW,
            level=PressureLevel.RED,
            detail=f"Context overflow: inclusion_ratio={ratio:.2f} < 0.5 (critical)",
        )

    if ratio < 1.0:
        return PressureTrigger(
            trigger_id=BP_CONTEXT_OVERFLOW,
            level=PressureLevel.YELLOW,
            detail=f"Context overflow: inclusion_ratio={ratio:.2f} < 1.0 (tight budget)",
        )

    return None


# ==============================================================================
# COMPOSITE CLASSIFICATION (Section 2.2)
# ==============================================================================


def _classify_composite(triggers: List[PressureTrigger]) -> PressureLevel:
    """Compute composite PressureLevel from fired triggers.

    Rules:
        R-01: Any single RED -> RED
        R-02: 1 YELLOW -> YELLOW
        R-03: 2 YELLOW -> YELLOW
        R-04: 3+ YELLOW -> RED (escalation)
        R-05: No triggers -> GREEN
        R-06: Unknown/malformed -> RED (fail-closed)

    Args:
        triggers: List of fired PressureTrigger objects

    Returns:
        Composite PressureLevel
    """
    if not triggers:
        return PressureLevel.GREEN

    red_count = sum(1 for t in triggers if t.level == PressureLevel.RED)
    yellow_count = sum(1 for t in triggers if t.level == PressureLevel.YELLOW)

    # R-01: Any single RED -> composite RED
    if red_count > 0:
        return PressureLevel.RED

    # R-04: 3+ YELLOW -> escalate to RED
    if yellow_count >= 3:
        return PressureLevel.RED

    # R-02, R-03: 1-2 YELLOW -> composite YELLOW
    if yellow_count > 0:
        return PressureLevel.YELLOW

    # R-06: Unknown/malformed -> RED (fail-closed default)
    return PressureLevel.RED


# ==============================================================================
# RESPONSE POLICY (Section 3)
# ==============================================================================


def _determine_response(level: PressureLevel) -> str:
    """Map PressureLevel to response action.

    GREEN  -> "proceed"
    YELLOW -> "advisory_fallback"
    RED    -> "fail_closed"

    Args:
        level: Composite PressureLevel

    Returns:
        Response string per contract Section 5.2
    """
    if level == PressureLevel.GREEN:
        return "proceed"
    elif level == PressureLevel.YELLOW:
        return "advisory_fallback"
    else:
        return "fail_closed"


# ==============================================================================
# MAIN EVALUATION (Section 4.2)
# ==============================================================================


def evaluate_pressure(
    call_type: str,
    input_fields: Dict[str, object],
    token_budget: int = 0,
    token_required: int = 0,
    turn_number: int = 0,
) -> BoundaryPressureResult:
    """Evaluate boundary pressure for a Spark invocation.

    Runs all four detectors, computes composite classification,
    determines response policy, and returns a complete result.

    This function is the single entry point for pressure evaluation.
    It is pure (no side effects) and deterministic (BP-INV-05).

    If the function itself throws, the caller must fail-closed to RED
    (ND-03). This function catches its own internal errors to ensure
    a result is always returned.

    Args:
        call_type: The CallType being invoked (e.g., "COMBAT_NARRATION")
        input_fields: Dict of field_name -> value (dot-notation keys)
        token_budget: Available tokens for this CallType (0 = skip overflow check)
        token_required: Estimated tokens needed (0 = skip overflow check)
        turn_number: Current game turn

    Returns:
        BoundaryPressureResult with all evaluation data
    """
    try:
        triggers: List[PressureTrigger] = []

        # BP-MISSING-FACT
        t = _check_missing_fact(call_type, input_fields)
        if t is not None:
            triggers.append(t)

        # BP-AMBIGUOUS-INTENT (only for affected CallTypes)
        if call_type in ("OPERATOR_DIRECTIVE", "CLARIFICATION_QUESTION"):
            t = _check_ambiguous_intent(input_fields)
            if t is not None:
                triggers.append(t)

        # BP-AUTHORITY-PROXIMITY (only for affected CallTypes)
        if call_type in ("COMBAT_NARRATION", "RULE_EXPLAINER", "OPERATOR_DIRECTIVE"):
            t = _check_authority_proximity(call_type, input_fields)
            if t is not None:
                triggers.append(t)

        # BP-CONTEXT-OVERFLOW (only if budget info provided)
        if token_budget > 0 or token_required > 0:
            t = _check_context_overflow(token_budget, token_required)
            if t is not None:
                triggers.append(t)

        composite = _classify_composite(triggers)
        response = _determine_response(composite)

        # Build detail string from triggers
        if triggers:
            detail = "; ".join(
                f"{t.trigger_id}={t.level.value}" for t in triggers
            )
        else:
            detail = "No pressure triggers fired"

        return BoundaryPressureResult(
            triggers=tuple(triggers),
            composite_level=composite,
            call_type=call_type,
            response=response,
            correlation_id=str(uuid.uuid4()),
            turn_number=turn_number,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        # ND-03: If evaluate_pressure itself throws, fail-closed to RED
        return BoundaryPressureResult(
            triggers=(),
            composite_level=PressureLevel.RED,
            call_type=call_type,
            response="fail_closed",
            correlation_id=str(uuid.uuid4()),
            turn_number=turn_number,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


# ==============================================================================
# HELPERS
# ==============================================================================


def _is_empty(value: object) -> bool:
    """Check if a value is null, empty string, or empty list.

    Args:
        value: The field value to check

    Returns:
        True if the value is considered "missing"
    """
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, tuple)) and len(value) == 0:
        return True
    return False
