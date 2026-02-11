"""M3 Judge's Lens — Entity inspection data model.

WO-025: Table-Native UX (Judge's Lens)

Provides:
- JudgesLens: Entity inspection interface
- EntityInspection: Entity status summary filtered by transparency mode
- inspect_entity(): Entity inspection per transparency mode
- get_recent_receipts(): Entity-specific combat history

Transparency levels:
- RUBY: Name, HP bar (no numbers), basic status
- SAPPHIRE: Name, HP, AC, active conditions, cover status
- DIAMOND: Full stat block, all modifiers, threatened squares, rule citations

All data models, no rendering. Rendering is frontend responsibility.
Pure functions with immutable dataclasses.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aidm.schemas.position import Position
from aidm.schemas.transparency import TransparencyMode
from aidm.immersion.combat_receipt import CombatReceipt, ReceiptTome


# ==============================================================================
# HP BAR STATUS
# ==============================================================================

class HPStatus(Enum):
    """HP bar status levels (RUBY mode)."""
    FULL = "full"               # 100% HP
    HEALTHY = "healthy"         # 75-99% HP
    WOUNDED = "wounded"         # 50-74% HP
    BLOODIED = "bloodied"       # 25-49% HP
    CRITICAL = "critical"       # 1-24% HP
    UNCONSCIOUS = "unconscious" # 0 HP or below


def compute_hp_status(hp_current: int, hp_max: int) -> HPStatus:
    """Compute HP status from current/max HP.

    Args:
        hp_current: Current HP
        hp_max: Maximum HP

    Returns:
        HPStatus enum value
    """
    if hp_current <= 0:
        return HPStatus.UNCONSCIOUS
    if hp_max <= 0:
        return HPStatus.FULL

    pct = (hp_current / hp_max) * 100

    if pct >= 100:
        return HPStatus.FULL
    elif pct >= 75:
        return HPStatus.HEALTHY
    elif pct >= 50:
        return HPStatus.WOUNDED
    elif pct >= 25:
        return HPStatus.BLOODIED
    else:
        return HPStatus.CRITICAL


# ==============================================================================
# ENTITY INSPECTION DATACLASS
# ==============================================================================

@dataclass(frozen=True)
class EntityInspection:
    """Entity status summary filtered by transparency mode.

    Immutable inspection result containing mode-appropriate data.
    """

    entity_id: str
    """Entity identifier."""

    mode: TransparencyMode
    """Transparency mode used for inspection."""

    # RUBY level (minimal)
    name: str
    """Entity display name."""

    hp_status: HPStatus
    """HP bar status (RUBY visual indicator)."""

    is_conscious: bool = True
    """Whether entity is conscious."""

    # SAPPHIRE level (standard)
    hp_current: int = 0
    """Current HP (SAPPHIRE+ only)."""

    hp_max: int = 0
    """Maximum HP (SAPPHIRE+ only)."""

    ac: int = 10
    """Armor Class (SAPPHIRE+ only)."""

    active_conditions: tuple = field(default_factory=tuple)
    """Tuple of active condition names (SAPPHIRE+ only)."""

    position: Optional[Position] = None
    """Current position (SAPPHIRE+ only)."""

    has_cover: bool = False
    """Whether entity has cover (SAPPHIRE+ only)."""

    # DIAMOND level (full)
    stats: Optional[Dict[str, int]] = None
    """Full stat block (DIAMOND only)."""

    modifiers: tuple = field(default_factory=tuple)
    """Tuple of (source, value) modifier tuples (DIAMOND only)."""

    threatened_squares: tuple = field(default_factory=tuple)
    """Tuple of threatened Position objects (DIAMOND only)."""

    rule_citations: tuple = field(default_factory=tuple)
    """Tuple of (source_id, page) citation tuples (DIAMOND only)."""

    raw_data: Optional[Dict[str, Any]] = None
    """Raw entity data for debugging (DIAMOND only)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        result = {
            "entity_id": self.entity_id,
            "mode": self.mode.value,
            "name": self.name,
            "hp_status": self.hp_status.value,
            "is_conscious": self.is_conscious,
        }

        # SAPPHIRE+ fields
        if self.mode in (TransparencyMode.SAPPHIRE, TransparencyMode.DIAMOND):
            result["hp_current"] = self.hp_current
            result["hp_max"] = self.hp_max
            result["ac"] = self.ac
            result["active_conditions"] = list(self.active_conditions)
            if self.position:
                result["position"] = self.position.to_dict()
            result["has_cover"] = self.has_cover

        # DIAMOND fields
        if self.mode == TransparencyMode.DIAMOND:
            if self.stats:
                result["stats"] = self.stats
            result["modifiers"] = [list(m) for m in self.modifiers]
            result["threatened_squares"] = [p.to_dict() for p in self.threatened_squares]
            result["rule_citations"] = [list(c) for c in self.rule_citations]
            if self.raw_data:
                result["raw_data"] = self.raw_data

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityInspection":
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            EntityInspection instance
        """
        mode = TransparencyMode(data["mode"])
        hp_status = HPStatus(data["hp_status"])

        position = None
        if "position" in data and data["position"]:
            position = Position.from_dict(data["position"])

        threatened_squares = tuple(
            Position.from_dict(p) for p in data.get("threatened_squares", [])
        )

        return cls(
            entity_id=data["entity_id"],
            mode=mode,
            name=data["name"],
            hp_status=hp_status,
            is_conscious=data.get("is_conscious", True),
            hp_current=data.get("hp_current", 0),
            hp_max=data.get("hp_max", 0),
            ac=data.get("ac", 10),
            active_conditions=tuple(data.get("active_conditions", [])),
            position=position,
            has_cover=data.get("has_cover", False),
            stats=data.get("stats"),
            modifiers=tuple(tuple(m) for m in data.get("modifiers", [])),
            threatened_squares=threatened_squares,
            rule_citations=tuple(tuple(c) for c in data.get("rule_citations", [])),
            raw_data=data.get("raw_data"),
        )


# ==============================================================================
# ENTITY STATE VIEW (READ-ONLY)
# ==============================================================================

@dataclass(frozen=True)
class EntityStateView:
    """Read-only view of entity state.

    Simplified entity data without importing from core.
    Used as input to inspect_entity().
    """

    entity_id: str
    name: str
    hp_current: int
    hp_max: int
    ac: int
    position: Optional[Position] = None
    conditions: tuple = field(default_factory=tuple)
    has_cover: bool = False

    # Optional DIAMOND-level data
    stats: Optional[Dict[str, int]] = None
    modifiers: tuple = field(default_factory=tuple)
    threatened_squares: tuple = field(default_factory=tuple)
    raw_data: Optional[Dict[str, Any]] = None


# ==============================================================================
# INSPECTION FUNCTIONS
# ==============================================================================

def inspect_entity(
    entity_view: EntityStateView,
    mode: TransparencyMode,
) -> EntityInspection:
    """Inspect entity and return mode-appropriate data.

    Pure function: no state mutation.

    Args:
        entity_view: Entity state view (read-only)
        mode: Transparency mode

    Returns:
        EntityInspection with mode-appropriate data
    """
    # Compute HP status
    hp_status = compute_hp_status(entity_view.hp_current, entity_view.hp_max)
    is_conscious = entity_view.hp_current > 0

    # RUBY: Only name and HP status
    if mode == TransparencyMode.RUBY:
        return EntityInspection(
            entity_id=entity_view.entity_id,
            mode=mode,
            name=entity_view.name,
            hp_status=hp_status,
            is_conscious=is_conscious,
        )

    # SAPPHIRE: Add HP numbers, AC, conditions, cover
    if mode == TransparencyMode.SAPPHIRE:
        return EntityInspection(
            entity_id=entity_view.entity_id,
            mode=mode,
            name=entity_view.name,
            hp_status=hp_status,
            is_conscious=is_conscious,
            hp_current=entity_view.hp_current,
            hp_max=entity_view.hp_max,
            ac=entity_view.ac,
            active_conditions=entity_view.conditions,
            position=entity_view.position,
            has_cover=entity_view.has_cover,
        )

    # DIAMOND: Full transparency with stats, modifiers, threats
    return EntityInspection(
        entity_id=entity_view.entity_id,
        mode=mode,
        name=entity_view.name,
        hp_status=hp_status,
        is_conscious=is_conscious,
        hp_current=entity_view.hp_current,
        hp_max=entity_view.hp_max,
        ac=entity_view.ac,
        active_conditions=entity_view.conditions,
        position=entity_view.position,
        has_cover=entity_view.has_cover,
        stats=entity_view.stats,
        modifiers=entity_view.modifiers,
        threatened_squares=entity_view.threatened_squares,
        raw_data=entity_view.raw_data,
    )


def get_recent_receipts(
    entity_id: str,
    tome: ReceiptTome,
    count: int = 5
) -> List[CombatReceipt]:
    """Get recent combat receipts involving an entity.

    Pure function: no state mutation.

    Args:
        entity_id: Entity identifier (matches receipt actor/target name)
        tome: ReceiptTome to search
        count: Maximum number of receipts to return

    Returns:
        List of recent receipts involving entity (newest first)
    """
    # Get all receipts for entity
    entity_receipts = tome.get_for_entity(entity_id)

    # Return most recent N
    return list(reversed(entity_receipts[-count:]))


# ==============================================================================
# JUDGE'S LENS CLASS
# ==============================================================================

class JudgesLens:
    """Judge's Lens for entity inspection.

    Provides entity status inspection filtered by transparency mode.
    Stateless interface (mode can be changed per inspection).
    """

    def __init__(
        self,
        default_mode: TransparencyMode = TransparencyMode.SAPPHIRE,
        receipt_tome: Optional[ReceiptTome] = None,
    ):
        """Initialize Judge's Lens.

        Args:
            default_mode: Default transparency mode
            receipt_tome: Optional receipt tome for combat history
        """
        self._default_mode = default_mode
        self._receipt_tome = receipt_tome or ReceiptTome()

    @property
    def default_mode(self) -> TransparencyMode:
        """Get default transparency mode."""
        return self._default_mode

    @property
    def receipt_tome(self) -> ReceiptTome:
        """Get receipt tome."""
        return self._receipt_tome

    def set_receipt_tome(self, tome: ReceiptTome) -> None:
        """Set receipt tome for combat history.

        Args:
            tome: ReceiptTome to use
        """
        self._receipt_tome = tome

    def inspect(
        self,
        entity_view: EntityStateView,
        mode: Optional[TransparencyMode] = None,
    ) -> EntityInspection:
        """Inspect entity with specified mode.

        Args:
            entity_view: Entity state view
            mode: Transparency mode (uses default if None)

        Returns:
            EntityInspection with mode-appropriate data
        """
        effective_mode = mode or self._default_mode
        return inspect_entity(entity_view, effective_mode)

    def get_combat_history(
        self,
        entity_id: str,
        count: int = 5
    ) -> List[CombatReceipt]:
        """Get recent combat history for entity.

        Args:
            entity_id: Entity identifier
            count: Maximum number of receipts

        Returns:
            List of recent combat receipts
        """
        return get_recent_receipts(entity_id, self._receipt_tome, count)

    def format_inspection(
        self,
        inspection: EntityInspection,
        include_history: bool = False,
        history_count: int = 3,
    ) -> str:
        """Format inspection as human-readable text.

        Args:
            inspection: EntityInspection to format
            include_history: Whether to include combat history
            history_count: Number of history entries to include

        Returns:
            Formatted inspection text
        """
        lines = []

        # Header
        lines.append(f"=== {inspection.name} ===")

        # RUBY: Just HP status
        if inspection.mode == TransparencyMode.RUBY:
            status_desc = {
                HPStatus.FULL: "Uninjured",
                HPStatus.HEALTHY: "Slightly wounded",
                HPStatus.WOUNDED: "Wounded",
                HPStatus.BLOODIED: "Bloodied",
                HPStatus.CRITICAL: "Critically wounded",
                HPStatus.UNCONSCIOUS: "Unconscious",
            }
            lines.append(f"Status: {status_desc[inspection.hp_status]}")

        # SAPPHIRE: Add numbers
        elif inspection.mode == TransparencyMode.SAPPHIRE:
            lines.append(f"HP: {inspection.hp_current}/{inspection.hp_max}")
            lines.append(f"AC: {inspection.ac}")

            if inspection.active_conditions:
                cond_str = ", ".join(inspection.active_conditions)
                lines.append(f"Conditions: {cond_str}")

            if inspection.has_cover:
                lines.append("Cover: Yes")

            if inspection.position:
                lines.append(f"Position: ({inspection.position.x}, {inspection.position.y})")

        # DIAMOND: Full details
        else:  # DIAMOND
            lines.append(f"HP: {inspection.hp_current}/{inspection.hp_max} ({inspection.hp_status.value})")
            lines.append(f"AC: {inspection.ac}")

            if inspection.stats:
                stat_str = ", ".join(f"{k.upper()}:{v}" for k, v in inspection.stats.items())
                lines.append(f"Stats: {stat_str}")

            if inspection.active_conditions:
                cond_str = ", ".join(inspection.active_conditions)
                lines.append(f"Conditions: {cond_str}")

            if inspection.modifiers:
                mod_lines = [f"  - {src}: {val:+d}" for src, val in inspection.modifiers]
                lines.append("Modifiers:")
                lines.extend(mod_lines)

            if inspection.has_cover:
                lines.append("Cover: Yes (+4 AC)")

            if inspection.threatened_squares:
                lines.append(f"Threatens: {len(inspection.threatened_squares)} squares")

            if inspection.position:
                lines.append(f"Position: ({inspection.position.x}, {inspection.position.y})")

        # Combat history
        if include_history and self._receipt_tome.count() > 0:
            history = self.get_combat_history(inspection.name, history_count)
            if history:
                lines.append("")
                lines.append("Recent Combat:")
                for receipt in history:
                    lines.append(f"  - {receipt.summary}")

        return "\n".join(lines)


# ==============================================================================
# PUBLIC API
# ==============================================================================

__all__ = [
    "HPStatus",
    "EntityInspection",
    "EntityStateView",
    "JudgesLens",
    "inspect_entity",
    "get_recent_receipts",
    "compute_hp_status",
]
