"""Boundary Pressure Schema — Frozen dataclasses and enums.

Defines the data model for pre-generation risk signal evaluation
per the Boundary Pressure Contract (RQ-PRESSURE-001, Tier 1.4).

All types are frozen (immutable). Detection logic lives in
aidm.core.boundary_pressure — this module is pure data.

SINGLE SOURCE OF TRUTH for: PressureLevel, PressureTrigger,
BoundaryPressureResult, and trigger ID constants.

Reference: docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md
"""

from dataclasses import dataclass
from enum import Enum


# ==============================================================================
# PRESSURE LEVEL (Section 2.1)
# ==============================================================================


class PressureLevel(str, Enum):
    """Three-level pressure classification (STOPLIGHT pattern).

    GREEN: No pressure. Normal Spark operation.
    YELLOW: Advisory. Spark fires, but no retry on validation failure.
    RED: Fail-closed. Spark does NOT fire. Template fallback.
    """
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


# ==============================================================================
# TRIGGER ID CONSTANTS (Section 1)
# ==============================================================================

BP_MISSING_FACT = "BP-MISSING-FACT"
BP_AMBIGUOUS_INTENT = "BP-AMBIGUOUS-INTENT"
BP_AUTHORITY_PROXIMITY = "BP-AUTHORITY-PROXIMITY"
BP_CONTEXT_OVERFLOW = "BP-CONTEXT-OVERFLOW"


# ==============================================================================
# PRESSURE TRIGGER (Section 1)
# ==============================================================================


@dataclass(frozen=True)
class PressureTrigger:
    """A single pressure trigger that fired during evaluation.

    Attributes:
        trigger_id: One of BP_MISSING_FACT, BP_AMBIGUOUS_INTENT,
                    BP_AUTHORITY_PROXIMITY, BP_CONTEXT_OVERFLOW
        level: The severity level this trigger fires at
        detail: Human-readable explanation (1 line)
    """
    trigger_id: str
    level: PressureLevel
    detail: str


# ==============================================================================
# BOUNDARY PRESSURE RESULT (Section 5.1)
# ==============================================================================


@dataclass(frozen=True)
class BoundaryPressureResult:
    """Complete result of a boundary pressure evaluation.

    Contains all fired triggers, the composite level, the response
    policy decision, and observability metadata. Every evaluation
    produces exactly one of these, logged as a structured event.

    Attributes:
        triggers: All triggers that fired (may be empty for GREEN)
        composite_level: Final computed PressureLevel after escalation rules
        call_type: The CallType that was attempted
        response: Action taken — "proceed", "advisory_fallback", or "fail_closed"
        correlation_id: UUID linking to post-hoc validation result
        turn_number: Game turn when evaluation occurred
        timestamp: ISO 8601 timestamp
    """
    triggers: tuple
    composite_level: PressureLevel
    call_type: str
    response: str
    correlation_id: str
    turn_number: int
    timestamp: str
