"""M3 Combat Receipts — Formatted parchment objects for combat events.

WO-025: Table-Native UX (Combat Receipts, Ghost Stencils, Judge's Lens)

Provides:
- CombatReceipt: Formatted parchment object from FilteredSTP
- ReceiptTome: Collection of receipts, filterable by encounter/actor/type
- create_receipt(): Factory function for building receipts
- format_parchment(): Text rendering for display

All data models, no rendering. Rendering is frontend responsibility.
Pure functions with immutable dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from aidm.schemas.transparency import FilteredSTP, TransparencyMode


# ==============================================================================
# COMBAT RECEIPT DATACLASS
# ==============================================================================

@dataclass(frozen=True)
class CombatReceipt:
    """Formatted parchment object representing a combat event.

    Contains event summary, mechanical breakdown (filtered by transparency mode),
    rule citations, and timestamp. Immutable for deterministic replay.
    """

    receipt_id: int
    """Unique receipt identifier (matches event_id)."""

    event_type: str
    """Event type (e.g., 'attack_roll', 'damage_roll')."""

    mode: TransparencyMode
    """Transparency mode used for this receipt."""

    timestamp: float
    """Event timestamp (Unix time)."""

    summary: str
    """Event summary text (final_result from FilteredSTP)."""

    # Optional fields populated based on mode
    mechanical_breakdown: str = ""
    """Mechanical breakdown text (SAPPHIRE+ only)."""

    actor: str = ""
    """Acting entity name."""

    target: str = ""
    """Target entity name (if any)."""

    rule_citations: tuple = field(default_factory=tuple)
    """Tuple of (source_id, page) citation tuples (DIAMOND only)."""

    raw_data: Optional[Dict[str, Any]] = None
    """Raw FilteredSTP data for debugging (DIAMOND only)."""

    encounter_id: Optional[str] = None
    """Optional encounter ID for filtering."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation for persistence
        """
        result = {
            "receipt_id": self.receipt_id,
            "event_type": self.event_type,
            "mode": self.mode.value,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "mechanical_breakdown": self.mechanical_breakdown,
            "actor": self.actor,
            "target": self.target,
            "rule_citations": [list(c) for c in self.rule_citations],
        }
        if self.raw_data is not None:
            result["raw_data"] = self.raw_data
        if self.encounter_id is not None:
            result["encounter_id"] = self.encounter_id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CombatReceipt":
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            CombatReceipt instance
        """
        mode = TransparencyMode(data["mode"])
        return cls(
            receipt_id=data["receipt_id"],
            event_type=data["event_type"],
            mode=mode,
            timestamp=data["timestamp"],
            summary=data["summary"],
            mechanical_breakdown=data.get("mechanical_breakdown", ""),
            actor=data.get("actor", ""),
            target=data.get("target", ""),
            rule_citations=tuple(tuple(c) for c in data.get("rule_citations", [])),
            raw_data=data.get("raw_data"),
            encounter_id=data.get("encounter_id"),
        )


# ==============================================================================
# RECEIPT CREATION
# ==============================================================================

def create_receipt(
    filtered_stp: FilteredSTP,
    timestamp: Optional[float] = None,
    encounter_id: Optional[str] = None,
) -> CombatReceipt:
    """Create a CombatReceipt from a FilteredSTP.

    Pure function: no state mutation.

    Args:
        filtered_stp: Filtered STP containing event data
        timestamp: Optional override timestamp (uses current time if None)
        encounter_id: Optional encounter ID for filtering

    Returns:
        CombatReceipt with mode-appropriate data
    """
    if timestamp is None:
        timestamp = datetime.now().timestamp()

    # Build mechanical breakdown based on mode
    mechanical_breakdown = ""
    if filtered_stp.mode in (TransparencyMode.SAPPHIRE, TransparencyMode.DIAMOND):
        if filtered_stp.summary_text:
            mechanical_breakdown = filtered_stp.summary_text

        # Add roll summaries for SAPPHIRE+
        if filtered_stp.roll_summaries and not filtered_stp.summary_text:
            roll_lines = []
            for roll_type, natural, total, success in filtered_stp.roll_summaries:
                outcome = "success" if success else "failure"
                roll_lines.append(f"{roll_type}: {natural} → {total} ({outcome})")
            mechanical_breakdown = "; ".join(roll_lines)

    # For DIAMOND mode, enhance with full breakdown
    if filtered_stp.mode == TransparencyMode.DIAMOND:
        breakdown_parts = []

        # Add roll breakdowns
        if filtered_stp.roll_breakdowns:
            for rb in filtered_stp.roll_breakdowns:
                mod_parts = [f"{m.source}: {m.value:+d}" for m in rb.modifiers]
                if mod_parts:
                    breakdown_parts.append(
                        f"{rb.roll_type}: d{rb.die_size}={rb.natural_roll} + "
                        f"({', '.join(mod_parts)}) = {rb.total}"
                    )
                else:
                    breakdown_parts.append(
                        f"{rb.roll_type}: d{rb.die_size}={rb.natural_roll} = {rb.total}"
                    )

        # Add damage breakdown
        if filtered_stp.damage_breakdown:
            db = filtered_stp.damage_breakdown
            dice_str = "+".join(str(r) for r in db.dice_results)
            mod_parts = [f"{m.source}: {m.value:+d}" for m in db.modifiers]
            if mod_parts:
                breakdown_parts.append(
                    f"Damage: {db.dice_expression}=[{dice_str}] + "
                    f"({', '.join(mod_parts)}) = {db.total} {db.damage_type}"
                )
            else:
                breakdown_parts.append(
                    f"Damage: {db.dice_expression}=[{dice_str}] = {db.total} {db.damage_type}"
                )

        if breakdown_parts:
            mechanical_breakdown = " | ".join(breakdown_parts)

    # Prepare raw data for DIAMOND mode
    raw_data = None
    if filtered_stp.mode == TransparencyMode.DIAMOND and filtered_stp.raw_payload:
        raw_data = filtered_stp.to_dict()

    return CombatReceipt(
        receipt_id=filtered_stp.event_id,
        event_type=filtered_stp.event_type,
        mode=filtered_stp.mode,
        timestamp=timestamp,
        summary=filtered_stp.final_result,
        mechanical_breakdown=mechanical_breakdown,
        actor=filtered_stp.actor_name,
        target=filtered_stp.target_name,
        rule_citations=filtered_stp.rule_citations,
        raw_data=raw_data,
        encounter_id=encounter_id,
    )


# ==============================================================================
# PARCHMENT FORMATTING
# ==============================================================================

def format_parchment(receipt: CombatReceipt, include_timestamp: bool = True) -> str:
    """Format a CombatReceipt as parchment text.

    Pure function: no state mutation.

    Args:
        receipt: CombatReceipt to format
        include_timestamp: Whether to include timestamp header

    Returns:
        Human-readable parchment text
    """
    lines = []

    # Timestamp header (optional)
    if include_timestamp:
        dt = datetime.fromtimestamp(receipt.timestamp)
        lines.append(f"[{dt.strftime('%H:%M:%S')}] Receipt #{receipt.receipt_id}")

    # Summary (always present)
    lines.append(receipt.summary)

    # Mechanical breakdown (SAPPHIRE+)
    if receipt.mechanical_breakdown and receipt.mode != TransparencyMode.RUBY:
        lines.append(f"  ↳ {receipt.mechanical_breakdown}")

    # Rule citations (DIAMOND only)
    if receipt.rule_citations and receipt.mode == TransparencyMode.DIAMOND:
        citations = [f"{source_id} p.{page}" for source_id, page in receipt.rule_citations if page > 0]
        if citations:
            lines.append(f"  ↳ Rules: {', '.join(citations)}")

    return "\n".join(lines)


# ==============================================================================
# RECEIPT TOME (COLLECTION)
# ==============================================================================

class ReceiptTome:
    """Collection of combat receipts, filterable by encounter/actor/type.

    Maintains chronological order and supports filtering for display.
    Not fully immutable (append operation), but receipts themselves are frozen.
    """

    def __init__(self) -> None:
        """Initialize empty receipt tome."""
        self._receipts: List[CombatReceipt] = []

    def append(self, receipt: CombatReceipt) -> None:
        """Add a receipt to the tome.

        Args:
            receipt: CombatReceipt to add
        """
        self._receipts.append(receipt)

    def append_all(self, receipts: List[CombatReceipt]) -> None:
        """Add multiple receipts to the tome.

        Args:
            receipts: List of CombatReceipts to add
        """
        self._receipts.extend(receipts)

    def all(self) -> List[CombatReceipt]:
        """Get all receipts in chronological order.

        Returns:
            List of all receipts
        """
        return list(self._receipts)

    def filter_by_encounter(self, encounter_id: str) -> List[CombatReceipt]:
        """Filter receipts by encounter ID.

        Args:
            encounter_id: Encounter identifier

        Returns:
            List of receipts matching encounter
        """
        return [r for r in self._receipts if r.encounter_id == encounter_id]

    def filter_by_actor(self, actor: str) -> List[CombatReceipt]:
        """Filter receipts by actor name.

        Args:
            actor: Actor name (exact match)

        Returns:
            List of receipts where actor matches
        """
        return [r for r in self._receipts if r.actor == actor]

    def filter_by_target(self, target: str) -> List[CombatReceipt]:
        """Filter receipts by target name.

        Args:
            target: Target name (exact match)

        Returns:
            List of receipts where target matches
        """
        return [r for r in self._receipts if r.target == target]

    def filter_by_type(self, event_type: str) -> List[CombatReceipt]:
        """Filter receipts by event type.

        Args:
            event_type: Event type (e.g., 'attack_roll', 'damage_roll')

        Returns:
            List of receipts matching event type
        """
        return [r for r in self._receipts if r.event_type == event_type]

    def filter_by_mode(self, mode: TransparencyMode) -> List[CombatReceipt]:
        """Filter receipts by transparency mode.

        Args:
            mode: Transparency mode

        Returns:
            List of receipts matching mode
        """
        return [r for r in self._receipts if r.mode == mode]

    def get_recent(self, count: int = 10) -> List[CombatReceipt]:
        """Get the N most recent receipts.

        Args:
            count: Number of receipts to return

        Returns:
            List of most recent receipts (newest first)
        """
        return list(reversed(self._receipts[-count:]))

    def get_for_entity(self, entity_name: str) -> List[CombatReceipt]:
        """Get all receipts involving an entity (as actor or target).

        Args:
            entity_name: Entity name

        Returns:
            List of receipts involving entity
        """
        return [
            r for r in self._receipts
            if r.actor == entity_name or r.target == entity_name
        ]

    def count(self) -> int:
        """Get total count of receipts.

        Returns:
            Number of receipts in tome
        """
        return len(self._receipts)

    def clear(self) -> None:
        """Clear all receipts from tome."""
        self._receipts.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tome to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "receipts": [r.to_dict() for r in self._receipts],
            "count": len(self._receipts),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReceiptTome":
        """Deserialize tome from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ReceiptTome instance
        """
        tome = cls()
        receipts = [CombatReceipt.from_dict(r) for r in data.get("receipts", [])]
        tome.append_all(receipts)
        return tome

    def format_all(self, include_timestamps: bool = True, separator: str = "\n---\n") -> str:
        """Format all receipts as parchment text.

        Args:
            include_timestamps: Whether to include timestamps
            separator: String to separate receipts

        Returns:
            Formatted parchment text for all receipts
        """
        formatted = [format_parchment(r, include_timestamps) for r in self._receipts]
        return separator.join(formatted)


# ==============================================================================
# PUBLIC API
# ==============================================================================

__all__ = [
    "CombatReceipt",
    "ReceiptTome",
    "create_receipt",
    "format_parchment",
]
