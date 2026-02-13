"""Terrain and traversal schemas.

Defines contracts for terrain tags, solidity, and traversal check triggers.
NO ALGORITHMS - schema only for pathfinding/movement resolution.

CP-19 EXTENSION:
- TerrainCell: Full terrain properties for a single grid cell
- ElevationDifference: Query result for elevation comparison
- FallingResult: Result of a falling event
- CoverCheckResult: Result of checking cover between entities

CP-001: Position Type Unification
- Migrated from local GridPosition to canonical Position type
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from aidm.schemas.position import Position  # CP-001: Canonical position type


class TerrainTag(Enum):
    """Terrain property tags affecting movement and cover."""

    DIFFICULT_TERRAIN = "difficult_terrain"
    SLIPPERY = "slippery"
    MUDDY = "muddy"
    SHALLOW_WATER = "shallow_water"
    DEEP_WATER = "deep_water"
    DENSE_FOREST = "dense_forest"
    WALL_SMOOTH = "wall_smooth"
    WALL_ROUGH = "wall_rough"
    BLOCKING_SOLID = "blocking_solid"
    HALF_COVER = "half_cover"
    THREE_QUARTERS_COVER = "three_quarters_cover"
    # CP-19: Additional terrain tags
    PIT = "pit"
    LEDGE = "ledge"
    STEEP_SLOPE_UP = "steep_slope_up"
    STEEP_SLOPE_DOWN = "steep_slope_down"
    GRADUAL_SLOPE = "gradual_slope"


# Cover type constants (PHB p.150-152)
class CoverType:
    """Cover type constants for terrain system."""
    NONE = None
    STANDARD = "standard"      # +4 AC, +2 Reflex
    IMPROVED = "improved"      # +8 AC, +4 Reflex
    TOTAL = "total"            # Cannot be targeted
    SOFT = "soft"              # +4 AC melee only, does not block AoO


# Traversal check types
TraversalCheckType = Literal["climb", "balance", "swim", "jump"]


@dataclass
class TraversalRequirement:
    """Requirement to traverse difficult terrain or obstacles."""

    check_type: TraversalCheckType
    """Type of skill/ability check required"""

    dc_base: int
    """Base DC for the check"""

    dc_modifiers: List[str]
    """Explainable modifiers (e.g., 'slippery: +2', 'rope: -5')"""

    citation: Optional[Dict[str, Any]] = None
    """Citation if DC derived from RAW table"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "check_type": self.check_type,
            "dc_base": self.dc_base,
            "dc_modifiers": list(self.dc_modifiers)
        }

        if self.citation is not None:
            result["citation"] = self.citation

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraversalRequirement":
        """Create from dictionary."""
        return cls(
            check_type=data["check_type"],
            dc_base=data["dc_base"],
            dc_modifiers=data.get("dc_modifiers", []),
            citation=data.get("citation")
        )


# ==============================================================================
# CP-19: TERRAIN CELL SCHEMA
# ==============================================================================

@dataclass
class TerrainCell:
    """Terrain properties for a single grid cell.

    Designed for grid-based lookup during movement resolution.
    Per CP-19: Read-only terrain (no mutations during play).
    """

    position: Position
    """Grid coordinates of this cell (CP-001: uses canonical Position type)."""

    elevation: int = 0
    """Elevation in feet above base level (0 = ground floor)."""

    movement_cost: int = 1
    """Movement cost multiplier (1 = normal, 2 = difficult, 4 = very difficult)."""

    terrain_tags: List[str] = field(default_factory=list)
    """List of TerrainTag values affecting this cell."""

    cover_type: Optional[str] = None
    """Cover provided by this cell: 'standard', 'improved', 'total', or None."""

    is_pit: bool = False
    """True if this cell is a pit (triggers falling on entry)."""

    pit_depth: int = 0
    """Depth of pit in feet (0 if not a pit)."""

    is_ledge: bool = False
    """True if this cell is adjacent to a drop-off."""

    ledge_drop: int = 0
    """Height of drop-off in feet (0 if not a ledge)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "position": self.position.to_dict(),
            "elevation": self.elevation,
            "movement_cost": self.movement_cost,
            "terrain_tags": list(self.terrain_tags),
            "cover_type": self.cover_type,
            "is_pit": self.is_pit,
            "pit_depth": self.pit_depth,
            "is_ledge": self.is_ledge,
            "ledge_drop": self.ledge_drop,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TerrainCell":
        """Create from dictionary."""
        return cls(
            position=Position.from_dict(data["position"]),
            elevation=data.get("elevation", 0),
            movement_cost=data.get("movement_cost", 1),
            terrain_tags=data.get("terrain_tags", []),
            cover_type=data.get("cover_type"),
            is_pit=data.get("is_pit", False),
            pit_depth=data.get("pit_depth", 0),
            is_ledge=data.get("is_ledge", False),
            ledge_drop=data.get("ledge_drop", 0),
        )


# ==============================================================================
# CP-19: ELEVATION QUERY SCHEMA
# ==============================================================================

@dataclass
class ElevationDifference:
    """Result of comparing elevation between two positions.

    Used to determine higher ground bonus (PHB p.151).
    """

    attacker_elevation: int
    """Attacker's elevation in feet."""

    defender_elevation: int
    """Defender's elevation in feet."""

    difference: int
    """Positive = attacker higher, negative = defender higher."""

    @property
    def attacker_has_higher_ground(self) -> bool:
        """True if attacker is on higher ground (PHB p.151)."""
        return self.difference > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "attacker_elevation": self.attacker_elevation,
            "defender_elevation": self.defender_elevation,
            "difference": self.difference,
            "attacker_has_higher_ground": self.attacker_has_higher_ground,
        }


# ==============================================================================
# CP-19: FALLING RESULT SCHEMA
# ==============================================================================

@dataclass
class FallingResult:
    """Result of a falling event.

    Falling damage: 1d6 per 10 feet, max 20d6 (DMG p.304).
    """

    entity_id: str
    """Entity that fell."""

    fall_distance: int
    """Distance fallen in feet."""

    damage_dice: int
    """Number of d6 to roll (max 20)."""

    damage_rolls: List[int] = field(default_factory=list)
    """Individual die results (filled after rolling)."""

    total_damage: int = 0
    """Total damage dealt (filled after rolling)."""

    landing_position: Optional[Position] = None
    """Position where entity lands (if applicable)."""

    is_into_water: bool = False
    """True if falling into water (reduced damage)."""

    water_depth: int = 0
    """Depth of water in feet, if falling into water."""

    is_intentional: bool = False
    """True if deliberate jump (first 10 feet free)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "entity_id": self.entity_id,
            "fall_distance": self.fall_distance,
            "damage_dice": self.damage_dice,
            "damage_rolls": list(self.damage_rolls),
            "total_damage": self.total_damage,
            "is_into_water": self.is_into_water,
            "water_depth": self.water_depth,
            "is_intentional": self.is_intentional,
        }
        if self.landing_position is not None:
            result["landing_position"] = self.landing_position.to_dict()
        return result


# ==============================================================================
# CP-19: COVER CHECK RESULT SCHEMA
# ==============================================================================

@dataclass
class CoverCheckResult:
    """Result of checking cover between attacker and defender.

    Cover bonuses (PHB p.150-152):
    - Standard: +4 AC, +2 Reflex, blocks AoO
    - Improved: +8 AC, +4 Reflex, blocks AoO
    - Total: Cannot be targeted, blocks AoO
    - Soft: +4 AC melee only, does NOT block AoO
    """

    attacker_id: str
    """Attacking entity."""

    defender_id: str
    """Defending entity."""

    cover_type: Optional[str]
    """Cover type: None, 'standard', 'improved', 'total', 'soft'."""

    ac_bonus: int
    """AC bonus from cover."""

    reflex_bonus: int
    """Reflex save bonus from cover."""

    blocks_aoo: bool
    """True if cover blocks Attacks of Opportunity."""

    blocks_targeting: bool
    """True for total cover (cannot be targeted)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "attacker_id": self.attacker_id,
            "defender_id": self.defender_id,
            "cover_type": self.cover_type,
            "ac_bonus": self.ac_bonus,
            "reflex_bonus": self.reflex_bonus,
            "blocks_aoo": self.blocks_aoo,
            "blocks_targeting": self.blocks_targeting,
        }
