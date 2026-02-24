"""Attack resolution schemas for CP-10.

Data-only contracts for attack intent and weapon definitions.
NO RESOLUTION LOGIC IN THIS MODULE.

CP-15: Added StepMoveIntent for AoO trigger detection.
CP-16: Added FullMoveIntent for multi-square movement with speed enforcement.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import warnings

# CP-001: Canonical position type (replaces legacy GridPosition below)
from aidm.schemas.position import Position


@dataclass
class Weapon:
    """Weapon definition for attack resolution."""

    damage_dice: str
    """Damage dice expression (e.g., '1d8', '2d6')"""

    damage_bonus: int
    """Flat damage bonus from enhancement, specialization, or magic effects.
    Does NOT include STR modifier — the resolver adds STR via entity[EF.STR_MOD]."""

    damage_type: str
    """Damage type: 'slashing', 'piercing', 'bludgeoning', 'fire', 'cold', etc."""

    critical_multiplier: int = 2
    """Critical hit damage multiplier (×2, ×3, ×4). Default ×2 per D&D 3.5e PHB p.140."""

    critical_range: int = 20
    """Minimum d20 roll that threatens a critical hit. Default 20 per PHB p.140.
    Examples: 20 (most weapons), 19 (longsword, rapier 19-20), 18 (keen longsword 18-20)."""

    is_two_handed: bool = False
    """WO-034-FIX: Whether weapon is wielded two-handed (PHB p.98).
    Affects Power Attack damage ratio (1:2 instead of 1:1)."""

    grip: str = "one-handed"
    """WO-FIX-01: Weapon grip for STR-to-damage multiplier (PHB p.113).
    'two-handed' = 1.5x STR, 'off-hand' = 0.5x STR, 'one-handed' = 1x STR."""

    weapon_type: str = "one-handed"
    """WO-WEAPON-PLUMBING-001: Weapon type category (PHB p.113/p.155).
    Values: 'light', 'one-handed', 'two-handed', 'ranged', 'natural'.
    Affects disarm modifiers (+4 two-handed, -4 light) and is_ranged derivation.
    Default 'one-handed' preserves existing behavior."""

    range_increment: int = 0
    """WO-WEAPON-PLUMBING-001: Range increment in feet (PHB p.113).
    0 = melee weapon. Positive = ranged weapon.
    Max range = range_increment * 10 (10 increments per SRD)."""

    def __post_init__(self):
        """Validate weapon data."""
        if not self.damage_dice:
            raise ValueError("damage_dice cannot be empty")

        # Validate damage type is recognized (not exhaustive, descriptive)
        # D&D 3.5e PHB p.309: energy types use "electricity" (not "electric")
        valid_types = {
            "slashing", "piercing", "bludgeoning",
            "fire", "cold", "acid", "electricity", "sonic",
            "force", "positive", "negative", "nonlethal"
        }
        if self.damage_type not in valid_types:
            raise ValueError(f"damage_type must be one of {valid_types}, got {self.damage_type}")

        # Validate critical multiplier
        if self.critical_multiplier not in {2, 3, 4}:
            raise ValueError(f"critical_multiplier must be 2, 3, or 4, got {self.critical_multiplier}")

        # Validate critical range (PHB p.140: threat range is 20 for most,
        # 19-20 for longswords/rapiers, 18-20 for keen weapons)
        if not (1 <= self.critical_range <= 20):
            raise ValueError(f"critical_range must be 1-20, got {self.critical_range}")

        # WO-FIX-01: Validate grip
        valid_grips = {"one-handed", "two-handed", "off-hand"}
        if self.grip not in valid_grips:
            raise ValueError(f"grip must be one of {valid_grips}, got {self.grip}")

        # WO-WEAPON-PLUMBING-001: Validate weapon type
        valid_weapon_types = {"light", "one-handed", "two-handed", "ranged", "natural"}
        if self.weapon_type not in valid_weapon_types:
            raise ValueError(f"weapon_type must be one of {valid_weapon_types}, got {self.weapon_type}")

        # WO-WEAPON-PLUMBING-001: Validate range increment
        if self.range_increment < 0:
            raise ValueError(f"range_increment must be >= 0, got {self.range_increment}")

    @property
    def is_ranged(self) -> bool:
        """Derived: True if weapon_type is 'ranged' (PHB p.113)."""
        return self.weapon_type == "ranged"

    @property
    def is_light(self) -> bool:
        """Derived: True if weapon_type is 'light' (PHB p.155)."""
        return self.weapon_type == "light"


@dataclass
class AttackIntent:
    """Intent to perform a single attack action."""

    attacker_id: str
    """Entity performing the attack"""

    target_id: str
    """Entity being attacked"""

    attack_bonus: int
    """Total attack bonus (BAB + STR/DEX + misc)"""

    weapon: Weapon
    """Weapon being used for this attack"""

    power_attack_penalty: int = 0
    """WO-034-FIX: Power Attack trade-off penalty (PHB p.98).
    0 = not using Power Attack. Max = BAB."""

    def __post_init__(self):
        """Validate attack intent."""
        if not self.attacker_id:
            raise ValueError("attacker_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.power_attack_penalty < 0:
            raise ValueError("power_attack_penalty cannot be negative")


@dataclass
class NonlethalAttackIntent:
    """Intent to perform a nonlethal (subdual) attack.

    PHB p.146: A melee attack declared as nonlethal incurs a -4 penalty to the
    attack roll. On a hit, damage goes to the nonlethal pool (NONLETHAL_DAMAGE),
    not to HP directly. When nonlethal damage >= current HP, the target is
    staggered or unconscious.

    Only valid with melee weapons. Using a lethal weapon to deal nonlethal damage
    is permitted with the -4 penalty.

    WO-ENGINE-NONLETHAL-001
    """

    attacker_id: str
    """Entity performing the nonlethal attack"""

    target_id: str
    """Entity being attacked"""

    attack_bonus: int
    """Total attack bonus BEFORE the -4 nonlethal penalty.
    The resolver applies the -4 penalty internally."""

    weapon: "Weapon"
    """Weapon being used. Must be melee (range_increment == 0)."""

    def __post_init__(self):
        if not self.attacker_id:
            raise ValueError("attacker_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.weapon.is_ranged:
            raise ValueError(
                "NonlethalAttackIntent requires a melee weapon (PHB p.146). "
                f"Got ranged weapon with range_increment={self.weapon.range_increment}."
            )


@dataclass
class EnergyDrainAttackIntent:
    """Intent to perform an energy drain attack (bestow negative levels).

    PHB p.215 (Energy Drain): A creature with the energy drain ability bestows
    one or more negative levels with a successful melee attack. Each
    negative level gives the target:
      -1 penalty to all attack rolls, saves, skill checks, and ability checks
      -1 to effective level for level-dependent quantities
      -5 max HP (target loses 5 hp per negative level)

    Uses the standard attack path (resolve_attack) internally; on hit,
    additionally applies negative_levels_per_hit negative levels.

    The 24h Fortitude save to make permanent vs temporary is DEFERRED.

    WO-ENGINE-ENERGY-DRAIN-001
    """

    attacker_id: str
    """Entity performing the energy drain (must be a creature with this ability)."""

    target_id: str
    """Entity being attacked."""

    attack_bonus: int
    """Total attack bonus for the attack roll (BAB + STR/misc)."""

    weapon: "Weapon"
    """Natural weapon used (claw, slam, incorporeal touch, etc.)."""

    negative_levels_per_hit: int = 1
    """Number of negative levels bestowed on a successful hit.
    Wight = 1, Vampire = 2."""

    def __post_init__(self):
        if not self.attacker_id:
            raise ValueError("attacker_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.negative_levels_per_hit < 1:
            raise ValueError(
                f"negative_levels_per_hit must be >= 1, got {self.negative_levels_per_hit}"
            )


@dataclass
class GridPosition:
    """2D grid position for movement and positioning.

    DEPRECATED: Use aidm.schemas.position.Position instead.
    This class will be removed in CP-002.
    """

    x: int
    """X coordinate (grid square)"""

    y: int
    """Y coordinate (grid square)"""

    def __post_init__(self):
        """Validate and warn about deprecation."""
        warnings.warn(
            "GridPosition in attack.py is deprecated. Use aidm.schemas.position.Position instead. "
            "This class will be removed in CP-002.",
            DeprecationWarning,
            stacklevel=2
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridPosition":
        """Create from dictionary."""
        return cls(x=data["x"], y=data["y"])

    def __eq__(self, other):
        """Check equality."""
        if not isinstance(other, GridPosition):
            return False
        return self.x == other.x and self.y == other.y

    def is_adjacent_to(self, other: "GridPosition") -> bool:
        """Check if this position is adjacent to another (5-ft reach)."""
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)
        # Adjacent: within 1 square in any direction (including diagonals)
        return (dx <= 1 and dy <= 1) and not (dx == 0 and dy == 0)


@dataclass
class StepMoveIntent:
    """Intent to move one step (CP-15 scoped movement for AoO detection).

    CP-15 SCOPE:
    - Single-step movement only (one 5-ft square)
    - No speed accounting, terrain, or diagonal restrictions
    - Minimal movement representation for AoO trigger evaluation
    - Full movement legality deferred to CP-16+

    from_pos must be provided explicitly (not inferred from WorldState)
    to ensure AoO timing is based on declared intent, not state diffs.
    """

    actor_id: str
    """Entity performing the move"""

    from_pos: Position
    """Starting position (must be current entity position)"""

    to_pos: Position
    """Destination position (must be adjacent to from_pos)"""

    def __post_init__(self):
        """Validate step move intent."""
        if not self.actor_id:
            raise ValueError("actor_id cannot be empty")

        # Validate adjacency (one-step constraint)
        if not self.from_pos.is_adjacent_to(self.to_pos):
            raise ValueError(
                f"StepMoveIntent requires adjacent positions: "
                f"from ({self.from_pos.x},{self.from_pos.y}) to ({self.to_pos.x},{self.to_pos.y})"
            )


@dataclass
class FullMoveIntent:
    """Intent to move up to speed across multiple squares (CP-16).

    CP-16 SCOPE:
    - Multi-square movement up to entity's base speed
    - Path must be contiguous (each step adjacent to previous)
    - Cannot pass through occupied enemy squares
    - Distance uses 5/10/5 diagonal rule (Position.distance_to)
    - Terrain movement cost applied per square entered
    - Each square departed triggers AoO check independently
    - Flat grid only (no elevation changes)

    The path field contains the sequence of positions from start (exclusive)
    to destination (inclusive). AoO is checked at each departure square.
    """

    actor_id: str
    """Entity performing the move."""

    from_pos: Position
    """Starting position (must be current entity position)."""

    path: List[Position] = field(default_factory=list)
    """Ordered list of positions to traverse (excludes from_pos, includes destination).
    Each position must be adjacent to the previous one."""

    speed_ft: int = 30
    """Entity's movement speed in feet. Path cost must not exceed this."""

    def __post_init__(self):
        """Validate full move intent."""
        if not self.actor_id:
            raise ValueError("actor_id cannot be empty")
        if self.speed_ft <= 0:
            raise ValueError(f"speed_ft must be positive, got {self.speed_ft}")
        if not self.path:
            raise ValueError("path must contain at least one position")

        # Validate path contiguity: each step must be adjacent to the previous
        prev = self.from_pos
        for i, pos in enumerate(self.path):
            if not prev.is_adjacent_to(pos):
                raise ValueError(
                    f"Path is not contiguous at step {i}: "
                    f"({prev.x},{prev.y}) to ({pos.x},{pos.y}) are not adjacent"
                )
            prev = pos

    @property
    def to_pos(self) -> Position:
        """Final destination (last position in path)."""
        return self.path[-1]

    def path_cost_ft(self, terrain_costs: Optional[List[int]] = None) -> int:
        """Calculate total movement cost in feet using 5/10/5 diagonal rule.

        Args:
            terrain_costs: Optional per-square terrain cost multiplier (1, 2, or 4).
                           Must have same length as path. Defaults to 1 for all squares.

        Returns:
            Total movement cost in feet.
        """
        if terrain_costs is None:
            terrain_costs = [1] * len(self.path)

        total_ft = 0
        prev = self.from_pos
        diagonal_count = 0

        for pos, terrain_mult in zip(self.path, terrain_costs):
            dx = abs(pos.x - prev.x)
            dy = abs(pos.y - prev.y)
            is_diagonal = dx == 1 and dy == 1

            if is_diagonal:
                diagonal_count += 1
                # 5/10/5/10 pattern: odd diagonals cost 5ft, even cost 10ft
                base_cost = 10 if diagonal_count % 2 == 0 else 5
            else:
                base_cost = 5

            total_ft += base_cost * terrain_mult
            prev = pos

        return total_ft
