"""Rulings and conflicts record schemas.

Defines data-only contracts for rules questions, conflicts, and resolutions.
NO RESOLUTION/INTERPRETATION LOGIC.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class RulesQuestion:
    """
    Single rules question requiring clarification.

    Descriptive only - no resolution logic.
    """

    question_text: str
    """The rules question being asked"""

    context_refs: List[str] = field(default_factory=list)
    """Entity IDs, event IDs, or situation references"""

    citations: List[Dict[str, Any]] = field(default_factory=list)
    """Potentially relevant citations"""

    def __post_init__(self):
        """Validate rules question."""
        if not self.question_text:
            raise ValueError("question_text cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "question_text": self.question_text,
            "context_refs": self.context_refs,
            "citations": self.citations
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RulesQuestion":
        """Create from dictionary."""
        return cls(
            question_text=data["question_text"],
            context_refs=data.get("context_refs", []),
            citations=data.get("citations", [])
        )


@dataclass
class RulingConflict:
    """
    Detected conflict between rules, citations, or interpretations.

    Descriptive only - no resolution logic.
    """

    question: RulesQuestion
    """The rules question that led to this conflict"""

    conflict_notes: str
    """Description of the conflict"""

    conflicting_citations: List[Dict[str, Any]] = field(default_factory=list)
    """Citations that appear to conflict"""

    def __post_init__(self):
        """Validate ruling conflict."""
        if not self.conflict_notes:
            raise ValueError("conflict_notes cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "question": self.question.to_dict(),
            "conflict_notes": self.conflict_notes,
            "conflicting_citations": self.conflicting_citations
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RulingConflict":
        """Create from dictionary."""
        return cls(
            question=RulesQuestion.from_dict(data["question"]),
            conflict_notes=data["conflict_notes"],
            conflicting_citations=data.get("conflicting_citations", [])
        )


@dataclass
class RulingDecision:
    """
    Resolution of a rules question or conflict.

    Descriptive only - no interpretation engine.
    """

    resolution_text: str
    """The final ruling text"""

    precedence_rationale: str
    """Why this ruling takes precedence (e.g., 'DMG p.5 errata', 'specific beats general')"""

    citations_used: List[Dict[str, Any]] = field(default_factory=list)
    """Citations that support this ruling"""

    timestamp: Optional[str] = None
    """ISO timestamp of when ruling was made (optional)"""

    event_link: Optional[int] = None
    """Event ID where this ruling was applied (optional)"""

    def __post_init__(self):
        """Validate ruling decision."""
        if not self.resolution_text:
            raise ValueError("resolution_text cannot be empty")
        if not self.precedence_rationale:
            raise ValueError("precedence_rationale cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "resolution_text": self.resolution_text,
            "precedence_rationale": self.precedence_rationale,
            "citations_used": sorted(
                self.citations_used,
                key=lambda c: (c.get("source_id", ""), c.get("page", 0))
            )
        }

        if self.timestamp is not None:
            result["timestamp"] = self.timestamp

        if self.event_link is not None:
            result["event_link"] = self.event_link

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RulingDecision":
        """Create from dictionary."""
        return cls(
            resolution_text=data["resolution_text"],
            precedence_rationale=data["precedence_rationale"],
            citations_used=data.get("citations_used", []),
            timestamp=data.get("timestamp"),
            event_link=data.get("event_link")
        )
