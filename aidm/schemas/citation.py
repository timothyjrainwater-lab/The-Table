"""Citation schema for attaching source references to rulings and log entries."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aidm.core.rule_lookup import SearchHit


@dataclass
class Citation:
    """
    Structured citation to a D&D 3.5e source material.

    Used to attach provenance to rulings, event log entries, and rule interpretations.
    """

    source_id: str
    """12-character hex sourceId (e.g., '681f92bc94ff' for PHB)"""

    short_name: Optional[str] = None
    """Human-readable short name (e.g., 'PHB', 'DMG', 'MM')"""

    page: Optional[int] = None
    """Page number (1-indexed) where rule/content is found"""

    span: Optional[str] = None
    """Text span or section reference (e.g., 'Grapple rules', 'Table 8-2')"""

    rule_id: Optional[str] = None
    """Structured rule identifier if available (future use)"""

    obsidian_uri: Optional[str] = None
    """Obsidian vault URI for deep-linking (future use)"""

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns dict with stable key ordering for deterministic serialization.
        """
        result = {"source_id": self.source_id}

        if self.short_name is not None:
            result["short_name"] = self.short_name

        if self.page is not None:
            result["page"] = self.page

        if self.span is not None:
            result["span"] = self.span

        if self.rule_id is not None:
            result["rule_id"] = self.rule_id

        if self.obsidian_uri is not None:
            result["obsidian_uri"] = self.obsidian_uri

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Citation":
        """
        Create Citation from dictionary.

        Args:
            data: Dictionary with citation fields

        Returns:
            Citation instance
        """
        return cls(
            source_id=data["source_id"],
            short_name=data.get("short_name"),
            page=data.get("page"),
            span=data.get("span"),
            rule_id=data.get("rule_id"),
            obsidian_uri=data.get("obsidian_uri"),
        )

    def __str__(self) -> str:
        """Human-readable citation string."""
        parts = []

        if self.short_name:
            parts.append(self.short_name)
        else:
            parts.append(self.source_id[:8])  # Abbreviated sourceId

        if self.page:
            parts.append(f"p. {self.page}")

        if self.span:
            parts.append(f"({self.span})")

        return " ".join(parts)


def build_citation(hit: "SearchHit") -> Citation:
    """
    Build a Citation from a SearchHit.

    Args:
        hit: SearchHit from rule lookup

    Returns:
        Citation instance with source_id, short_name, and page populated
    """
    return Citation(
        source_id=hit.source_id,
        short_name=hit.short_name,
        page=hit.page,
        span=None  # SearchHit doesn't include semantic span info
    )


def with_obsidian_uri(citation: Citation, vault_name: str, note_path: str) -> Citation:
    """
    Create a new Citation with Obsidian URI attached.

    Args:
        citation: Original citation
        vault_name: Obsidian vault name
        note_path: Path to note within vault

    Returns:
        New Citation instance with obsidian_uri populated
    """
    from aidm.core.obsidian_links import build_obsidian_uri

    return Citation(
        source_id=citation.source_id,
        short_name=citation.short_name,
        page=citation.page,
        span=citation.span,
        rule_id=citation.rule_id,
        obsidian_uri=build_obsidian_uri(vault_name, note_path)
    )
