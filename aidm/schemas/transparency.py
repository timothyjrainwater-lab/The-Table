"""Transparency mode schemas for the Tri-Gem Socket system.

WO-023: Transparency Tri-Gem Socket
Provides three visibility modes for players to understand DM decisions:
- RUBY: Minimal — final results only ("The attack hits for 12 damage")
- SAPPHIRE: Standard — key rolls and modifiers ("Attack roll: 18 + 5 = 23 vs AC 15")
- DIAMOND: Full — complete mechanical breakdown with rule references

All types are immutable (frozen dataclasses) and support JSON serialization.
Default mode is SAPPHIRE for balanced transparency.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TransparencyMode(Enum):
    """Transparency level for combat event display.

    Controls how much mechanical detail is shown to players.
    Per Tri-Gem metaphor:
    - RUBY (red): Narrative focus, minimal mechanics
    - SAPPHIRE (blue): Balanced, shows key numbers
    - DIAMOND (clear): Full transparency, all details
    """

    RUBY = "ruby"
    """Minimal transparency: final results only.
    Example: 'The attack hits for 12 damage.'
    """

    SAPPHIRE = "sapphire"
    """Standard transparency: key rolls and modifiers.
    Example: 'Attack roll: 18 + 5 = 23 vs AC 15. Hit! 12 damage.'
    Default mode for balanced gameplay experience.
    """

    DIAMOND = "diamond"
    """Full transparency: complete mechanical breakdown.
    Example: 'd20=18, BAB +3, STR +2 = 23 vs AC 15 (base 10 + armor 4 + DEX +1).
    Includes rule citations and all modifier sources.'
    """


@dataclass(frozen=True)
class ModifierBreakdown:
    """Single modifier in a roll breakdown.

    Tracks the source and value of each bonus/penalty.
    """

    source: str
    """Source of the modifier (e.g., 'BAB', 'STR', 'flanking')."""

    value: int
    """Numeric value of the modifier (can be negative for penalties)."""

    rule_citation: Optional[str] = None
    """Optional PHB page reference (e.g., 'PHB p.143')."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "source": self.source,
            "value": self.value,
        }
        if self.rule_citation is not None:
            result["rule_citation"] = self.rule_citation
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModifierBreakdown":
        """Create from dictionary."""
        return cls(
            source=data["source"],
            value=data["value"],
            rule_citation=data.get("rule_citation"),
        )


@dataclass(frozen=True)
class RollBreakdown:
    """Complete breakdown of a dice roll.

    Contains the natural roll, all modifiers, and final total.
    """

    roll_type: str
    """Type of roll: 'attack', 'd20', 'damage', 'save', 'skill', etc."""

    natural_roll: int
    """Unmodified die result (e.g., 18 on d20)."""

    die_size: int = 20
    """Size of die rolled (default d20)."""

    modifiers: tuple = field(default_factory=tuple)
    """Tuple of ModifierBreakdown objects."""

    total: int = 0
    """Final total after all modifiers."""

    target_value: Optional[int] = None
    """Value to beat (AC for attacks, DC for saves)."""

    target_name: Optional[str] = None
    """Name of target value (e.g., 'AC', 'DC', 'SR')."""

    success: Optional[bool] = None
    """Whether the roll succeeded (None if no target)."""

    is_critical: bool = False
    """Whether this was a natural 20 (or threat range for attacks)."""

    is_fumble: bool = False
    """Whether this was a natural 1."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "roll_type": self.roll_type,
            "natural_roll": self.natural_roll,
            "die_size": self.die_size,
            "modifiers": [m.to_dict() for m in self.modifiers],
            "total": self.total,
            "is_critical": self.is_critical,
            "is_fumble": self.is_fumble,
        }
        if self.target_value is not None:
            result["target_value"] = self.target_value
        if self.target_name is not None:
            result["target_name"] = self.target_name
        if self.success is not None:
            result["success"] = self.success
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RollBreakdown":
        """Create from dictionary."""
        modifiers = tuple(
            ModifierBreakdown.from_dict(m) for m in data.get("modifiers", [])
        )
        return cls(
            roll_type=data["roll_type"],
            natural_roll=data["natural_roll"],
            die_size=data.get("die_size", 20),
            modifiers=modifiers,
            total=data.get("total", 0),
            target_value=data.get("target_value"),
            target_name=data.get("target_name"),
            success=data.get("success"),
            is_critical=data.get("is_critical", False),
            is_fumble=data.get("is_fumble", False),
        )


@dataclass(frozen=True)
class DamageBreakdown:
    """Complete breakdown of damage calculation.

    Contains dice rolls, modifiers, and final damage.
    """

    dice_expression: str
    """Original dice expression (e.g., '2d6+4')."""

    dice_results: tuple = field(default_factory=tuple)
    """Individual die results (e.g., (3, 5) for 2d6)."""

    modifiers: tuple = field(default_factory=tuple)
    """Tuple of ModifierBreakdown objects."""

    total: int = 0
    """Final damage total."""

    damage_type: str = "untyped"
    """Damage type: 'slashing', 'fire', etc."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "dice_expression": self.dice_expression,
            "dice_results": list(self.dice_results),
            "modifiers": [m.to_dict() for m in self.modifiers],
            "total": self.total,
            "damage_type": self.damage_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DamageBreakdown":
        """Create from dictionary."""
        modifiers = tuple(
            ModifierBreakdown.from_dict(m) for m in data.get("modifiers", [])
        )
        return cls(
            dice_expression=data["dice_expression"],
            dice_results=tuple(data.get("dice_results", [])),
            modifiers=modifiers,
            total=data.get("total", 0),
            damage_type=data.get("damage_type", "untyped"),
        )


@dataclass(frozen=True)
class FilteredSTP:
    """Filtered Structured Truth Packet for display.

    Contains only the information appropriate for the selected
    TransparencyMode. Built from raw Event data by the filter functions.

    RUBY: Only final_result populated
    SAPPHIRE: summary_text + roll_summaries + final_result
    DIAMOND: All fields populated including full breakdowns and citations
    """

    event_id: int
    """Original event ID for traceability."""

    event_type: str
    """Event type (e.g., 'attack_roll', 'damage_roll', 'save_rolled')."""

    mode: TransparencyMode
    """Transparency mode used to filter this packet."""

    # RUBY level (minimal)
    final_result: str = ""
    """Plain English result (e.g., 'Fighter hits Goblin for 12 damage')."""

    # SAPPHIRE level (standard)
    summary_text: str = ""
    """Key numbers summary (e.g., '18 + 5 = 23 vs AC 15')."""

    actor_name: str = ""
    """Name of the acting entity."""

    target_name: str = ""
    """Name of the target entity (if any)."""

    roll_summaries: tuple = field(default_factory=tuple)
    """Tuple of (roll_type, natural, total, success) tuples."""

    # DIAMOND level (full)
    roll_breakdowns: tuple = field(default_factory=tuple)
    """Tuple of RollBreakdown objects with full modifier details."""

    damage_breakdown: Optional[DamageBreakdown] = None
    """Full damage calculation if damage was dealt."""

    rule_citations: tuple = field(default_factory=tuple)
    """Tuple of (source_id, page) citation tuples."""

    raw_payload: Optional[Dict[str, Any]] = None
    """Original event payload for debugging (DIAMOND only)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "mode": self.mode.value,
            "final_result": self.final_result,
        }

        # SAPPHIRE+ fields
        if self.mode in (TransparencyMode.SAPPHIRE, TransparencyMode.DIAMOND):
            result["summary_text"] = self.summary_text
            result["actor_name"] = self.actor_name
            result["target_name"] = self.target_name
            result["roll_summaries"] = [
                list(rs) for rs in self.roll_summaries
            ]

        # DIAMOND fields
        if self.mode == TransparencyMode.DIAMOND:
            result["roll_breakdowns"] = [
                rb.to_dict() for rb in self.roll_breakdowns
            ]
            if self.damage_breakdown is not None:
                result["damage_breakdown"] = self.damage_breakdown.to_dict()
            result["rule_citations"] = [list(c) for c in self.rule_citations]
            if self.raw_payload is not None:
                result["raw_payload"] = self.raw_payload

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilteredSTP":
        """Create from dictionary."""
        mode = TransparencyMode(data["mode"])

        roll_breakdowns = tuple(
            RollBreakdown.from_dict(rb)
            for rb in data.get("roll_breakdowns", [])
        )

        damage_breakdown = None
        if data.get("damage_breakdown") is not None:
            damage_breakdown = DamageBreakdown.from_dict(data["damage_breakdown"])

        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            mode=mode,
            final_result=data.get("final_result", ""),
            summary_text=data.get("summary_text", ""),
            actor_name=data.get("actor_name", ""),
            target_name=data.get("target_name", ""),
            roll_summaries=tuple(
                tuple(rs) for rs in data.get("roll_summaries", [])
            ),
            roll_breakdowns=roll_breakdowns,
            damage_breakdown=damage_breakdown,
            rule_citations=tuple(
                tuple(c) for c in data.get("rule_citations", [])
            ),
            raw_payload=data.get("raw_payload"),
        )


@dataclass(frozen=True)
class TransparencyConfig:
    """Per-player transparency mode configuration.

    Immutable to ensure deterministic behavior.
    Mode can be changed by creating a new config.
    """

    player_id: str
    """Player identifier."""

    mode: TransparencyMode = TransparencyMode.SAPPHIRE
    """Current transparency mode (default SAPPHIRE)."""

    show_enemy_hp: bool = False
    """Whether to show enemy HP values (separate from mode)."""

    show_npc_modifiers: bool = False
    """Whether to show NPC modifier breakdowns (DIAMOND only)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "player_id": self.player_id,
            "mode": self.mode.value,
            "show_enemy_hp": self.show_enemy_hp,
            "show_npc_modifiers": self.show_npc_modifiers,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransparencyConfig":
        """Create from dictionary."""
        return cls(
            player_id=data["player_id"],
            mode=TransparencyMode(data.get("mode", "sapphire")),
            show_enemy_hp=data.get("show_enemy_hp", False),
            show_npc_modifiers=data.get("show_npc_modifiers", False),
        )

    def with_mode(self, new_mode: TransparencyMode) -> "TransparencyConfig":
        """Create new config with different mode (immutable update)."""
        return TransparencyConfig(
            player_id=self.player_id,
            mode=new_mode,
            show_enemy_hp=self.show_enemy_hp,
            show_npc_modifiers=self.show_npc_modifiers,
        )
