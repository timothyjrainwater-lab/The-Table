"""Flanking detection for D&D 3.5e (PHB p.153).

A character flanks a defender when an allied combatant threatens the
defender from a position on the opposite side or corner. Both the attacker
and the ally must be threatening the defender (i.e., adjacent and not
incapacitated).

FLANKING BONUS: +2 to melee attack rolls when flanking (PHB p.153).

GEOMETRY RULE (PHB p.153 diagram):
Draw a line from the center of the attacker's square to the center of
the ally's square. If this line passes through opposite sides or
opposite corners of the defender's square, the attacker and ally flank
the defender.

SIMPLIFIED IMPLEMENTATION (grid-based):
For Medium creatures on a 5-foot grid, the "opposite sides" rule maps
to: attacker and ally are on roughly opposite sides of the target.
Formally, the vector from target to attacker and the vector from target
to ally must have an angle >= 135 degrees between them (covering the
opposite-side/opposite-corner cases from PHB p.153 diagrams).

REQUIREMENTS:
- Both attacker and ally must be adjacent to target (melee threat)
- Both must be alive and undefeated
- Both must be on the same team
- Target must be alive and undefeated
- Attacker and ally must be on opposite sides (angle >= 135 degrees)

CITATIONS:
- PHB p.153: Flanking diagram and rules
- PHB p.137: Threatened area (adjacent squares for melee)
"""

import math
from typing import List, Optional, Tuple

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position


# PHB p.153: Flanking grants +2 to melee attack rolls
FLANKING_BONUS = 2

# Minimum angle (degrees) between attacker-target and ally-target vectors
# for flanking to apply. 135 degrees covers the PHB p.153 diagram cases
# (opposite sides and opposite corners).
MIN_FLANKING_ANGLE = 135.0


def _get_position(entity: dict) -> Optional[Position]:
    """Extract Position from entity dict, or None if not set.

    Args:
        entity: Entity data dict

    Returns:
        Position instance or None
    """
    pos_data = entity.get(EF.POSITION)
    if pos_data is None:
        return None
    if isinstance(pos_data, Position):
        return pos_data
    if isinstance(pos_data, dict) and "x" in pos_data and "y" in pos_data:
        return Position(x=pos_data["x"], y=pos_data["y"])
    return None


def _is_threatening(entity: dict) -> bool:
    """Check if entity is capable of threatening (alive, not incapacitated).

    PHB p.137: A character threatens the area within natural reach.
    An incapacitated character does not threaten.

    Args:
        entity: Entity data dict

    Returns:
        True if entity can threaten adjacent squares
    """
    if entity.get(EF.DEFEATED, False):
        return False

    hp = entity.get(EF.HP_CURRENT, 0)
    if hp <= 0:
        return False

    # Check for incapacitating conditions
    conditions = entity.get(EF.CONDITIONS, {})
    for cond_id, cond_data in conditions.items():
        mods = cond_data.get("modifiers", {})
        if mods.get("actions_prohibited", False):
            return False

    return True


def _angle_between(target: Position, a: Position, b: Position) -> float:
    """Calculate angle between vectors (target->a) and (target->b) in degrees.

    Args:
        target: Center position (defender)
        a: First position (attacker)
        b: Second position (ally)

    Returns:
        Angle in degrees (0-180)
    """
    # Vectors from target to each combatant
    ax = a.x - target.x
    ay = a.y - target.y
    bx = b.x - target.x
    by = b.y - target.y

    # Dot product
    dot = ax * bx + ay * by
    # Magnitudes
    mag_a = math.sqrt(ax * ax + ay * ay)
    mag_b = math.sqrt(bx * bx + by * by)

    if mag_a == 0 or mag_b == 0:
        return 0.0

    # Clamp for floating point safety
    cos_angle = max(-1.0, min(1.0, dot / (mag_a * mag_b)))
    return math.degrees(math.acos(cos_angle))


def check_flanking(
    world_state: WorldState,
    attacker_id: str,
    target_id: str,
) -> int:
    """Check if attacker flanks the target and return the flanking bonus.

    PHB p.153: When making a melee attack, you get a +2 flanking bonus
    if your opponent is threatened by a character or creature friendly
    to you on the opponent's opposite border or opposite corner.

    Args:
        world_state: Current world state
        attacker_id: Entity ID of the attacker
        target_id: Entity ID of the defender

    Returns:
        +2 if flanking, 0 if not flanking
    """
    result = get_flanking_info(world_state, attacker_id, target_id)
    return result[0]


def get_flanking_info(
    world_state: WorldState,
    attacker_id: str,
    target_id: str,
) -> Tuple[int, bool, List[str]]:
    """Get full flanking information including which allies enable it.

    Args:
        world_state: Current world state
        attacker_id: Entity ID of the attacker
        target_id: Entity ID of the defender

    Returns:
        Tuple of (bonus, is_flanking, flanking_ally_ids)
    """
    entities = world_state.entities

    # Validate entities exist
    attacker = entities.get(attacker_id)
    target = entities.get(target_id)
    if attacker is None or target is None:
        return (0, False, [])

    # Attacker must be threatening
    if not _is_threatening(attacker):
        return (0, False, [])

    # Target must be alive
    if target.get(EF.DEFEATED, False):
        return (0, False, [])
    if target.get(EF.HP_CURRENT, 0) <= 0:
        return (0, False, [])

    # Get positions
    attacker_pos = _get_position(attacker)
    target_pos = _get_position(target)
    if attacker_pos is None or target_pos is None:
        return (0, False, [])

    # Attacker must be adjacent to target (melee threat)
    if not attacker_pos.is_adjacent_to(target_pos):
        return (0, False, [])

    # Get attacker's team
    attacker_team = attacker.get(EF.TEAM)
    if attacker_team is None:
        return (0, False, [])

    # Search for allies that enable flanking
    flanking_allies = []

    for entity_id, entity in entities.items():
        # Skip self and target
        if entity_id == attacker_id or entity_id == target_id:
            continue

        # Must be on the same team
        if entity.get(EF.TEAM) != attacker_team:
            continue

        # Must be threatening
        if not _is_threatening(entity):
            continue

        # Must have a position
        ally_pos = _get_position(entity)
        if ally_pos is None:
            continue

        # Must be adjacent to target (melee threat)
        if not ally_pos.is_adjacent_to(target_pos):
            continue

        # Must be on opposite side (angle check)
        angle = _angle_between(target_pos, attacker_pos, ally_pos)
        if angle >= MIN_FLANKING_ANGLE:
            flanking_allies.append(entity_id)

    if flanking_allies:
        return (FLANKING_BONUS, True, flanking_allies)

    return (0, False, [])


def is_denied_dex_to_ac(
    world_state: WorldState,
    target_id: str,
) -> bool:
    """Check if target is denied Dexterity bonus to AC.

    PHB p.311: Several conditions cause a character to lose its
    Dexterity bonus to AC: flat-footed, stunned, helpless, etc.

    This is used by Sneak Attack to determine eligibility when
    the attacker is not flanking.

    Args:
        world_state: Current world state
        target_id: Entity ID of the target

    Returns:
        True if target is denied Dex bonus to AC
    """
    from aidm.core.conditions import get_condition_modifiers
    mods = get_condition_modifiers(world_state, target_id, context="defense")
    return mods.loses_dex_to_ac
