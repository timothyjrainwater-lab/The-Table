"""Ranged attack resolution for Box geometric engine.

Implements RAW 3.5e ranged attack calculations including:
- Distance calculation using 1-2-1-2 diagonal rule (PHB p.148)
- Range increment penalties (PHB p.158)
- Cover integration with cover_resolver
- Targeting validation for ranged weapons and spells

WO-005: Ranged Attack Resolution
Reference: RQ-BOX-001 (Geometric Engine Research)
"""

from dataclasses import dataclass
from typing import Optional

from aidm.schemas.position import Position
from aidm.core.geometry_engine import BattleGrid
from aidm.core.cover_resolver import calculate_cover, CoverResult, CoverDegree


# ==============================================================================
# RANGE PENALTY CONSTANTS
# ==============================================================================

# Per PHB p.158: -2 penalty per range increment beyond the first
PENALTY_PER_INCREMENT = -2

# Default maximum increments for projectile and thrown weapons
DEFAULT_MAX_INCREMENTS = 10
THROWN_MAX_INCREMENTS = 5


# ==============================================================================
# RANGED ATTACK RESULT
# ==============================================================================

@dataclass(frozen=True)
class RangedAttackResult:
    """Result of ranged attack evaluation.

    Immutable for determinism and event logging.
    """

    is_valid: bool
    """Whether the attack is valid (in range, has LOE, not total cover)."""

    attacker_id: str
    """Attacker's entity ID."""

    target_id: str
    """Target's entity ID."""

    distance_ft: int
    """Distance in feet between attacker and target."""

    range_increment: int
    """Which range increment the target is in (1 = no penalty)."""

    range_penalty: int
    """Attack roll penalty from range (0, -2, -4, etc.)."""

    cover_result: Optional[CoverResult]
    """Cover calculation result, or None if not computed."""

    failure_reason: Optional[str]
    """Reason for invalid attack, or None if valid."""

    def to_dict(self) -> dict:
        """Serialize for event logging."""
        return {
            "is_valid": self.is_valid,
            "attacker_id": self.attacker_id,
            "target_id": self.target_id,
            "distance_ft": self.distance_ft,
            "range_increment": self.range_increment,
            "range_penalty": self.range_penalty,
            "cover_result": self.cover_result.to_dict() if self.cover_result else None,
            "failure_reason": self.failure_reason,
        }


# ==============================================================================
# DISTANCE CALCULATION
# ==============================================================================

def calculate_distance_feet(attacker_pos: Position, target_pos: Position) -> int:
    """Calculate distance in feet using 1-2-1-2 diagonal rule.

    Uses Position.distance_to() which implements PHB p.148 diagonal movement:
    - First diagonal costs 5 feet (1 square)
    - Second diagonal costs 10 feet (2 squares)
    - Pattern alternates: 1-2-1-2-1-2...

    Args:
        attacker_pos: Attacker's grid position
        target_pos: Target's grid position

    Returns:
        Distance in feet (integer, multiples of 5)

    Example:
        (0,0) to (3,3) = 20 feet (diagonal: 5+10+5 = 20)
        (0,0) to (4,0) = 20 feet (orthogonal: 4 * 5 = 20)
    """
    return attacker_pos.distance_to(target_pos)


def calculate_distance_squares(attacker_pos: Position, target_pos: Position) -> int:
    """Calculate distance in squares using 1-2-1-2 diagonal rule.

    Convenience wrapper that returns distance divided by 5.

    Args:
        attacker_pos: Attacker's grid position
        target_pos: Target's grid position

    Returns:
        Distance in squares (equivalent to feet / 5)
    """
    return calculate_distance_feet(attacker_pos, target_pos) // 5


# ==============================================================================
# RANGE INCREMENT CALCULATION
# ==============================================================================

def get_range_increment(distance_ft: int, range_increment_ft: int) -> int:
    """Determine which range increment the target is in.

    Per PHB p.158: A ranged weapon has a maximum range of 10 range increments.
    The first increment (0 to range_increment_ft) is increment 1 (no penalty).
    The second increment (range_increment_ft+1 to 2*range_increment_ft) is
    increment 2 (-2 penalty), and so on.

    Args:
        distance_ft: Distance in feet to target
        range_increment_ft: Weapon's range increment in feet

    Returns:
        Range increment number (1, 2, 3, etc.)
        Returns 0 if distance is 0 (same square, melee range)

    Example:
        Shortbow (60 ft increment):
        - 30 ft → increment 1
        - 60 ft → increment 1
        - 61 ft → increment 2
        - 120 ft → increment 2
        - 121 ft → increment 3
    """
    if distance_ft <= 0:
        return 0  # Same square or invalid distance

    if range_increment_ft <= 0:
        raise ValueError("Range increment must be positive")

    # Calculate which increment (1-indexed)
    # 0-60 ft = increment 1, 61-120 ft = increment 2, etc.
    return ((distance_ft - 1) // range_increment_ft) + 1


def calculate_range_increment_penalty(
    distance_ft: int,
    range_increment_ft: int,
    max_increments: int = DEFAULT_MAX_INCREMENTS
) -> Optional[int]:
    """Calculate attack penalty based on range increment.

    Per PHB p.158: Each full range increment causes a cumulative -2 penalty.
    The first increment has no penalty.

    Args:
        distance_ft: Distance in feet to target
        range_increment_ft: Weapon's range increment in feet
        max_increments: Maximum allowed increments (10 for most, 5 for thrown)

    Returns:
        Penalty (0, -2, -4, etc.) or None if beyond max range

    Example:
        Shortbow (60 ft increment, 10 max):
        - 60 ft → 0 penalty
        - 61-120 ft → -2 penalty
        - 121-180 ft → -4 penalty
        - 541-600 ft → -18 penalty (10th increment)
        - 601+ ft → None (beyond max range)
    """
    if distance_ft <= 0:
        return 0  # Same square, no range penalty (melee)

    if range_increment_ft <= 0:
        raise ValueError("Range increment must be positive")

    increment = get_range_increment(distance_ft, range_increment_ft)

    if increment > max_increments:
        return None  # Beyond maximum range

    # First increment = 0 penalty, second = -2, third = -4, etc.
    return (increment - 1) * PENALTY_PER_INCREMENT


# ==============================================================================
# COVER INTEGRATION
# ==============================================================================

def get_cover_ac_bonus(
    attacker_pos: Position,
    target_pos: Position,
    grid: BattleGrid
) -> int:
    """Get the AC bonus defender receives from cover.

    Uses calculate_cover() from cover_resolver to determine cover degree,
    then returns the corresponding AC bonus.

    Args:
        attacker_pos: Attacker's grid position
        target_pos: Target's (defender's) grid position
        grid: BattleGrid for cover calculation

    Returns:
        AC bonus (0 for no cover, 2 for half, 5 for 3/4, 0 for total)
        Note: Total cover returns 0 because target is untargetable

    Per PHB p.150-152:
    - No cover: +0 AC
    - Half cover: +2 AC
    - Three-quarters cover: +5 AC
    - Total cover: Untargetable (use is_valid_ranged_target to check)
    """
    result = calculate_cover(
        attacker_pos=attacker_pos,
        defender_pos=target_pos,
        grid=grid
    )
    return result.ac_bonus


def has_line_of_effect(
    attacker_pos: Position,
    target_pos: Position,
    grid: BattleGrid
) -> bool:
    """Check if attacker has line of effect to target.

    Line of effect is not blocked by total cover. This is a simplified
    check that uses the cover resolver - if cover is NOT total, LOE exists.

    Args:
        attacker_pos: Attacker's grid position
        target_pos: Target's grid position
        grid: BattleGrid for LOE calculation

    Returns:
        True if LOE exists, False if blocked (total cover)
    """
    result = calculate_cover(
        attacker_pos=attacker_pos,
        defender_pos=target_pos,
        grid=grid
    )
    return not result.blocks_targeting


# ==============================================================================
# TARGETING VALIDATION
# ==============================================================================

def is_valid_ranged_target(
    grid: BattleGrid,
    attacker_id: str,
    target_id: str,
    max_range_ft: int
) -> bool:
    """Quick check if target is valid for ranged attack.

    Validates:
    1. Target is within maximum range
    2. Attacker has line of effect (not total cover)

    Args:
        grid: BattleGrid with entities placed
        attacker_id: Attacker's entity ID
        target_id: Target's entity ID
        max_range_ft: Maximum range in feet

    Returns:
        True if target is valid, False otherwise

    Raises:
        ValueError: If attacker or target not found on grid
    """
    attacker_pos = grid.get_entity_position(attacker_id)
    target_pos = grid.get_entity_position(target_id)

    if attacker_pos is None:
        raise ValueError(f"Attacker '{attacker_id}' not found on grid")
    if target_pos is None:
        raise ValueError(f"Target '{target_id}' not found on grid")

    # Check range
    distance_ft = calculate_distance_feet(attacker_pos, target_pos)
    if distance_ft > max_range_ft:
        return False

    # Check LOE (not total cover)
    if not has_line_of_effect(attacker_pos, target_pos, grid):
        return False

    return True


# ==============================================================================
# FULL RANGED ATTACK EVALUATION
# ==============================================================================

def evaluate_ranged_attack(
    grid: BattleGrid,
    attacker_id: str,
    target_id: str,
    range_increment_ft: int,
    max_range_ft: int,
    max_increments: int = DEFAULT_MAX_INCREMENTS
) -> RangedAttackResult:
    """Evaluate a ranged attack for validity and penalties.

    Comprehensive evaluation that:
    1. Validates attacker and target positions
    2. Calculates distance and range increment
    3. Checks if within maximum range
    4. Calculates cover and LOE
    5. Computes range penalty

    Args:
        grid: BattleGrid with entities placed
        attacker_id: Attacker's entity ID
        target_id: Target's entity ID
        range_increment_ft: Weapon's range increment in feet
        max_range_ft: Maximum range in feet
        max_increments: Maximum range increments allowed

    Returns:
        RangedAttackResult with validity, penalties, and failure reason

    Example:
        Shortbow attack at 90 ft (60 ft increment):
        - is_valid: True
        - distance_ft: 90
        - range_increment: 2
        - range_penalty: -2
        - cover_result: (depends on terrain)
    """
    # Get positions
    attacker_pos = grid.get_entity_position(attacker_id)
    target_pos = grid.get_entity_position(target_id)

    if attacker_pos is None:
        return RangedAttackResult(
            is_valid=False,
            attacker_id=attacker_id,
            target_id=target_id,
            distance_ft=0,
            range_increment=0,
            range_penalty=0,
            cover_result=None,
            failure_reason=f"Attacker '{attacker_id}' not found on grid"
        )

    if target_pos is None:
        return RangedAttackResult(
            is_valid=False,
            attacker_id=attacker_id,
            target_id=target_id,
            distance_ft=0,
            range_increment=0,
            range_penalty=0,
            cover_result=None,
            failure_reason=f"Target '{target_id}' not found on grid"
        )

    # Calculate distance
    distance_ft = calculate_distance_feet(attacker_pos, target_pos)

    # Check if same square (distance 0 - melee, not ranged)
    if distance_ft == 0:
        return RangedAttackResult(
            is_valid=False,
            attacker_id=attacker_id,
            target_id=target_id,
            distance_ft=0,
            range_increment=0,
            range_penalty=0,
            cover_result=None,
            failure_reason="Target in same square (melee range, not ranged)"
        )

    # Check maximum range
    if distance_ft > max_range_ft:
        return RangedAttackResult(
            is_valid=False,
            attacker_id=attacker_id,
            target_id=target_id,
            distance_ft=distance_ft,
            range_increment=get_range_increment(distance_ft, range_increment_ft),
            range_penalty=0,
            cover_result=None,
            failure_reason=f"Beyond maximum range ({distance_ft} ft > {max_range_ft} ft)"
        )

    # Calculate range increment and penalty
    range_increment = get_range_increment(distance_ft, range_increment_ft)
    range_penalty = calculate_range_increment_penalty(
        distance_ft, range_increment_ft, max_increments
    )

    # Check if beyond max increments
    if range_penalty is None:
        return RangedAttackResult(
            is_valid=False,
            attacker_id=attacker_id,
            target_id=target_id,
            distance_ft=distance_ft,
            range_increment=range_increment,
            range_penalty=0,
            cover_result=None,
            failure_reason=f"Beyond maximum range increments ({range_increment} > {max_increments})"
        )

    # Calculate cover
    cover_result = calculate_cover(
        attacker_pos=attacker_pos,
        defender_pos=target_pos,
        grid=grid
    )

    # Check for total cover (blocks targeting)
    if cover_result.blocks_targeting:
        return RangedAttackResult(
            is_valid=False,
            attacker_id=attacker_id,
            target_id=target_id,
            distance_ft=distance_ft,
            range_increment=range_increment,
            range_penalty=range_penalty,
            cover_result=cover_result,
            failure_reason="Target has total cover (untargetable)"
        )

    # Valid attack
    return RangedAttackResult(
        is_valid=True,
        attacker_id=attacker_id,
        target_id=target_id,
        distance_ft=distance_ft,
        range_increment=range_increment,
        range_penalty=range_penalty,
        cover_result=cover_result,
        failure_reason=None
    )
