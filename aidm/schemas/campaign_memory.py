"""Campaign memory and character evidence ledger schemas.

Defines data-only contracts for campaign-scale memory, session ledgers,
character behavioral evidence, and investigation clue tracking.

NO ALIGNMENT EVALUATION. NO DIVINE LOGIC. Descriptive only.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal, Tuple


# Evidence type enumeration (descriptive, not evaluative)
EvidenceType = Literal[
    "harm_inflicted",
    "harm_prevented",
    "mercy_shown",
    "betrayal",
    "loyalty",
    "theft",
    "deception",
    "obedience_authority",
    "defiance_authority",
    "self_sacrifice",
    "self_interest",
    "respect_life",
    "disregard_life",
    "promise_made",
    "promise_broken"
]


# Alignment axis tags (for later mapping, not evaluation)
AlignmentAxisTag = Literal[
    "lawful",
    "neutral_lc",
    "chaotic",
    "good",
    "neutral_ge",
    "evil"
]


# Clue status enumeration
ClueStatus = Literal["unresolved", "partial", "resolved"]


@dataclass
class SessionLedgerEntry:
    """
    High-level session summary entry (write-once record).

    Captures key facts and state changes from a session.
    """

    session_id: str
    """Unique session identifier"""

    campaign_id: str
    """Campaign this session belongs to"""

    session_number: int
    """Sequential session number (1-indexed)"""

    created_at: str
    """ISO timestamp of session creation"""

    summary: str
    """Short factual summary of session"""

    facts_added: List[str] = field(default_factory=list)
    """Factual bullets added this session"""

    state_changes: List[str] = field(default_factory=list)
    """Factual state change bullets"""

    event_id_range: Optional[Tuple[int, int]] = None
    """Optional event ID range (start_id, end_id) for this session"""

    citations: List[Dict[str, Any]] = field(default_factory=list)
    """Optional citations referenced this session"""

    def __post_init__(self):
        """Validate session ledger entry."""
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.campaign_id:
            raise ValueError("campaign_id cannot be empty")
        if self.session_number < 1:
            raise ValueError(f"session_number must be >= 1, got {self.session_number}")
        if not self.summary:
            raise ValueError("summary cannot be empty")

        # Validate event_id_range if present
        if self.event_id_range is not None:
            start_id, end_id = self.event_id_range
            if start_id < 0:
                raise ValueError(f"event_id_range start must be >= 0, got {start_id}")
            if end_id < start_id:
                raise ValueError(f"event_id_range end must be >= start, got {end_id} < {start_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "session_id": self.session_id,
            "campaign_id": self.campaign_id,
            "session_number": self.session_number,
            "created_at": self.created_at,
            "summary": self.summary,
            "facts_added": self.facts_added,
            "state_changes": self.state_changes,
            "citations": self.citations
        }

        if self.event_id_range is not None:
            result["event_id_range"] = list(self.event_id_range)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionLedgerEntry":
        """Create from dictionary."""
        event_id_range = data.get("event_id_range")
        if event_id_range is not None:
            event_id_range = tuple(event_id_range)

        return cls(
            session_id=data["session_id"],
            campaign_id=data["campaign_id"],
            session_number=data["session_number"],
            created_at=data["created_at"],
            summary=data["summary"],
            facts_added=data.get("facts_added", []),
            state_changes=data.get("state_changes", []),
            event_id_range=event_id_range,
            citations=data.get("citations", [])
        )


@dataclass
class CharacterEvidenceEntry:
    """
    Single piece of behavioral evidence for a character.

    Descriptive only - no alignment scoring or judgment.
    """

    id: str
    """Unique identifier within campaign evidence ledger"""

    character_id: str
    """Character this evidence is about"""

    session_id: str
    """Session where this evidence occurred"""

    evidence_type: str
    """Type of evidence (must match EvidenceType values)"""

    description: str
    """Factual description (no judgment)"""

    event_id: Optional[int] = None
    """Event ID if known"""

    targets: List[str] = field(default_factory=list)
    """Entity IDs targeted (optional)"""

    location_ref: Optional[str] = None
    """Location reference (optional)"""

    faction_ref: Optional[str] = None
    """Faction reference (optional)"""

    deity_ref: Optional[str] = None
    """Deity reference for clerics/paladins (optional)"""

    alignment_axis_tags: List[str] = field(default_factory=list)
    """Alignment axis tags (not final alignment, just tags)"""

    citations: List[Dict[str, Any]] = field(default_factory=list)
    """Optional citations"""

    def __post_init__(self):
        """Validate evidence entry."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.character_id:
            raise ValueError("character_id cannot be empty")
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.evidence_type:
            raise ValueError("evidence_type cannot be empty")
        if not self.description:
            raise ValueError("description cannot be empty")

        # Validate evidence_type against known types
        valid_types = [
            "harm_inflicted", "harm_prevented", "mercy_shown", "betrayal",
            "loyalty", "theft", "deception", "obedience_authority",
            "defiance_authority", "self_sacrifice", "self_interest",
            "respect_life", "disregard_life", "promise_made", "promise_broken"
        ]
        if self.evidence_type not in valid_types:
            raise ValueError(f"evidence_type must be one of {valid_types}, got {self.evidence_type}")

        # Validate alignment_axis_tags if present
        valid_tags = ["lawful", "neutral_lc", "chaotic", "good", "neutral_ge", "evil"]
        for tag in self.alignment_axis_tags:
            if tag not in valid_tags:
                raise ValueError(f"alignment_axis_tag must be one of {valid_tags}, got {tag}")

        # Validate event_id if present
        if self.event_id is not None and self.event_id < 0:
            raise ValueError(f"event_id must be >= 0, got {self.event_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "character_id": self.character_id,
            "session_id": self.session_id,
            "evidence_type": self.evidence_type,
            "description": self.description,
            "targets": self.targets,
            "alignment_axis_tags": self.alignment_axis_tags,
            "citations": self.citations
        }

        if self.event_id is not None:
            result["event_id"] = self.event_id

        if self.location_ref is not None:
            result["location_ref"] = self.location_ref

        if self.faction_ref is not None:
            result["faction_ref"] = self.faction_ref

        if self.deity_ref is not None:
            result["deity_ref"] = self.deity_ref

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterEvidenceEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            character_id=data["character_id"],
            session_id=data["session_id"],
            evidence_type=data["evidence_type"],
            description=data["description"],
            event_id=data.get("event_id"),
            targets=data.get("targets", []),
            location_ref=data.get("location_ref"),
            faction_ref=data.get("faction_ref"),
            deity_ref=data.get("deity_ref"),
            alignment_axis_tags=data.get("alignment_axis_tags", []),
            citations=data.get("citations", [])
        )


@dataclass
class EvidenceLedger:
    """
    Campaign-wide evidence ledger.

    Deterministic ordering: sort by (character_id, session_id, id).
    """

    campaign_id: str
    """Campaign this ledger belongs to"""

    entries: List[CharacterEvidenceEntry] = field(default_factory=list)
    """Evidence entries (sorted deterministically)"""

    def __post_init__(self):
        """Validate evidence ledger."""
        if not self.campaign_id:
            raise ValueError("campaign_id cannot be empty")

        # Enforce deterministic ordering
        self.entries = sorted(
            self.entries,
            key=lambda e: (e.character_id, e.session_id, e.id)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "campaign_id": self.campaign_id,
            "entries": [e.to_dict() for e in self.entries]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceLedger":
        """Create from dictionary."""
        return cls(
            campaign_id=data["campaign_id"],
            entries=[CharacterEvidenceEntry.from_dict(e) for e in data.get("entries", [])]
        )


@dataclass
class ClueCard:
    """
    Investigation clue card for tracking campaign mysteries.
    """

    id: str
    """Unique clue identifier"""

    session_id: str
    """Session where clue was discovered"""

    discovered_by: List[str] = field(default_factory=list)
    """Character IDs who discovered this clue"""

    description: str = ""
    """Clue description"""

    status: str = "unresolved"
    """Clue status (unresolved/partial/resolved)"""

    links: List[str] = field(default_factory=list)
    """IDs of related clues/NPCs/locations"""

    citations: List[Dict[str, Any]] = field(default_factory=list)
    """Optional citations"""

    def __post_init__(self):
        """Validate clue card."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.session_id:
            raise ValueError("session_id cannot be empty")

        # Validate status
        valid_statuses = ["unresolved", "partial", "resolved"]
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}, got {self.status}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "discovered_by": self.discovered_by,
            "description": self.description,
            "status": self.status,
            "links": self.links,
            "citations": self.citations
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClueCard":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            discovered_by=data.get("discovered_by", []),
            description=data.get("description", ""),
            status=data.get("status", "unresolved"),
            links=data.get("links", []),
            citations=data.get("citations", [])
        )


@dataclass
class ThreadRegistry:
    """
    Campaign-wide clue and mystery thread registry.
    """

    campaign_id: str
    """Campaign this registry belongs to"""

    clues: List[ClueCard] = field(default_factory=list)
    """Clue cards (stable ordering by id)"""

    def __post_init__(self):
        """Validate thread registry."""
        if not self.campaign_id:
            raise ValueError("campaign_id cannot be empty")

        # Enforce deterministic ordering by id
        self.clues = sorted(self.clues, key=lambda c: c.id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "campaign_id": self.campaign_id,
            "clues": [c.to_dict() for c in self.clues]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreadRegistry":
        """Create from dictionary."""
        return cls(
            campaign_id=data["campaign_id"],
            clues=[ClueCard.from_dict(c) for c in data.get("clues", [])]
        )
