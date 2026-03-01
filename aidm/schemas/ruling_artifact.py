# WO-JUDGMENT-SHADOW-001: Phase 0 Ruling Contract schema
# SPEC-RULING-CONTRACT-001 defines the full schema.
# This dataclass is expanded to full schema in Guarded phase.
from dataclasses import dataclass, field
from typing import List, Literal, Optional


@dataclass
class RulingArtifactShadow:
    """
    Phase 0 (Shadow) subset of the full Ruling Contract.
    SPEC-RULING-CONTRACT-001 defines the full schema.
    This dataclass is expanded to full schema in Guarded phase.
    """

    player_action_raw: str
    route_class: Literal[
        "named",
        "named_plus_circumstance",
        "improvised_synthesis",
        "impossible_or_clarify",
    ]
    routing_confidence: Literal["certain", "probable", "uncertain", "escalate"]

    # Validator output (filled by ruling_validator.py, not by caller)
    validator_verdict: Literal["pass", "fail", "needs_clarification"] = "needs_clarification"
    validator_reasons: List[str] = field(default_factory=list)

    # Optional Phase 0 fields (populated when routing hook has more context)
    dc: Optional[int] = None
    clarification_message: Optional[str] = None
