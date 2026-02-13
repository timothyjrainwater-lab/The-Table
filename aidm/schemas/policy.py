"""Tactical policy schemas for deterministic tactic selection.

Defines data-only contracts for policy evaluation and tactic scoring.
NO POLICY ENGINE LOGIC - schema only.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal

# Re-export TacticClass from doctrine (already defined there)
from aidm.schemas.doctrine import TacticClass


# Policy status literals
PolicyStatus = Literal["ok", "requires_clarification", "no_legal_tactics"]


@dataclass
class TacticCandidate:
    """
    Single tactic candidate for evaluation.

    Data-only representation of a potential tactical choice.
    """

    tactic_class: str
    """Tactic class identifier (must match TacticClass values)"""

    target_ids: List[str] = field(default_factory=list)
    """Entity IDs targeted by this tactic (empty for positional/non-targeted tactics)"""

    position_ref: Optional[Dict[str, Any]] = None
    """Optional position reference (e.g., {"x": 10, "y": 15})"""

    notes: str = ""
    """Optional notes about this candidate"""

    def __post_init__(self):
        """Validate candidate fields."""
        if not self.tactic_class:
            raise ValueError("tactic_class cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "tactic_class": self.tactic_class,
            "target_ids": self.target_ids,
            "notes": self.notes
        }

        if self.position_ref is not None:
            result["position_ref"] = self.position_ref

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TacticCandidate":
        """Create from dictionary."""
        return cls(
            tactic_class=data["tactic_class"],
            target_ids=data.get("target_ids", []),
            position_ref=data.get("position_ref"),
            notes=data.get("notes", "")
        )


@dataclass
class ScoredTactic:
    """
    Tactic candidate with score and scoring rationale.

    Score is an integer (no floating point) for determinism.
    """

    candidate: TacticCandidate
    """The tactic candidate being scored"""

    score: int
    """Integer score (higher is better)"""

    reasons: List[str] = field(default_factory=list)
    """Structured list of scoring reasons (human-readable)"""

    def __post_init__(self):
        """Validate scored tactic."""
        # Score can be negative (penalties), but must be an integer
        if not isinstance(self.score, int):
            raise ValueError(f"score must be an integer, got {type(self.score)}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "candidate": self.candidate.to_dict(),
            "score": self.score,
            "reasons": self.reasons
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoredTactic":
        """Create from dictionary."""
        return cls(
            candidate=TacticCandidate.from_dict(data["candidate"]),
            score=data["score"],
            reasons=data.get("reasons", [])
        )


@dataclass
class TacticalPolicyTrace:
    """
    Trace of policy evaluation process.

    Captures all inputs, intermediate computations, and final selection
    for deterministic replay and debugging.
    """

    actor_id: str
    """Entity ID of the acting creature"""

    doctrine_snapshot: Dict[str, Any]
    """Snapshot of MonsterDoctrine at evaluation time"""

    extracted_features: Dict[str, Any]
    """Features extracted from WorldState"""

    candidates_before_filtering: List[str] = field(default_factory=list)
    """All tactic classes before doctrine filtering"""

    candidates_after_filtering: List[str] = field(default_factory=list)
    """Allowed tactic classes after doctrine filtering"""

    scoring_breakdown: List[Dict[str, Any]] = field(default_factory=list)
    """Detailed scoring for each candidate"""

    rng_draw: Optional[Dict[str, Any]] = None
    """RNG draw details if stochastic selection was used"""

    final_selection_rationale: str = ""
    """Why this tactic was selected"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "actor_id": self.actor_id,
            "doctrine_snapshot": self.doctrine_snapshot,
            "extracted_features": self.extracted_features,
            "candidates_before_filtering": self.candidates_before_filtering,
            "candidates_after_filtering": self.candidates_after_filtering,
            "scoring_breakdown": self.scoring_breakdown,
            "final_selection_rationale": self.final_selection_rationale
        }

        if self.rng_draw is not None:
            result["rng_draw"] = self.rng_draw

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TacticalPolicyTrace":
        """Create from dictionary."""
        return cls(
            actor_id=data["actor_id"],
            doctrine_snapshot=data["doctrine_snapshot"],
            extracted_features=data["extracted_features"],
            candidates_before_filtering=data.get("candidates_before_filtering", []),
            candidates_after_filtering=data.get("candidates_after_filtering", []),
            scoring_breakdown=data.get("scoring_breakdown", []),
            rng_draw=data.get("rng_draw"),
            final_selection_rationale=data.get("final_selection_rationale", "")
        )


@dataclass
class TacticalPolicyResult:
    """
    Result of tactical policy evaluation.

    Contains status, ranked candidates, optional selection, and trace.
    """

    status: PolicyStatus
    """Evaluation status (ok, requires_clarification, no_legal_tactics)"""

    ranked: List[ScoredTactic] = field(default_factory=list)
    """Ranked list of scored tactics (descending score order)"""

    selected: Optional[ScoredTactic] = None
    """Selected tactic (if any)"""

    trace: Optional[TacticalPolicyTrace] = None
    """Evaluation trace for debugging/replay"""

    missing_fields: List[str] = field(default_factory=list)
    """Missing required state fields (if status=requires_clarification)"""

    def __post_init__(self):
        """Validate result invariants."""
        # If selected is present, it must be in ranked
        if self.selected is not None and self.ranked:
            # Check by tactic_class match (identity check is too strict)
            selected_found = any(
                r.candidate.tactic_class == self.selected.candidate.tactic_class
                for r in self.ranked
            )
            if not selected_found:
                raise ValueError("selected tactic must appear in ranked list")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "status": self.status,
            "ranked": [r.to_dict() for r in self.ranked],
            "missing_fields": self.missing_fields
        }

        if self.selected is not None:
            result["selected"] = self.selected.to_dict()

        if self.trace is not None:
            result["trace"] = self.trace.to_dict()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TacticalPolicyResult":
        """Create from dictionary."""
        return cls(
            status=data["status"],
            ranked=[ScoredTactic.from_dict(r) for r in data.get("ranked", [])],
            selected=ScoredTactic.from_dict(data["selected"]) if "selected" in data else None,
            trace=TacticalPolicyTrace.from_dict(data["trace"]) if "trace" in data else None,
            missing_fields=data.get("missing_fields", [])
        )
