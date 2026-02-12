"""Sneak Attack precision damage for D&D 3.5e (PHB p.50).

WO-050B: Sneak Attack implementation.

SNEAK ATTACK RULES (PHB p.50):
A rogue can strike a vital spot for extra damage whenever the target is
denied Dexterity bonus to AC (flat-footed, stunned, helpless, etc.) or
when the rogue flanks the target.

DAMAGE:
- +1d6 per qualifying class level pair:
  Rogue level 1-2: 1d6, level 3-4: 2d6, level 5-6: 3d6, etc.
  Formula: (rogue_level + 1) // 2 dice of d6

CRITICAL HIT INTERACTION (PHB p.50):
- Sneak attack damage is NOT multiplied on critical hits.
  It is precision damage, added flat after base damage is multiplied.

IMMUNITY (PHB p.50):
- Creatures immune to critical hits are also immune to sneak attack:
  undead, constructs, oozes, plants, elementals, incorporeal creatures.
- Not effective if attacker cannot see the target.

RANGE LIMITATION (PHB p.50):
- Ranged sneak attacks only within 30 feet.

RNG CONSUMPTION:
- Sneak attack dice are rolled AFTER base damage + critical multiplier.
- This affects the deterministic RNG stream ordering.

CITATIONS:
- PHB p.50: Rogue class, Sneak Attack feature
- PHB p.153: Flanking rules (used for eligibility)
"""

from typing import List, Optional, Tuple

from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF


# Creature types immune to sneak attack (PHB p.50, DMG p.290)
# These creatures have no discernible anatomy or vital spots.
SNEAK_ATTACK_IMMUNE_TYPES = frozenset({
    "undead",
    "construct",
    "ooze",
    "plant",
    "elemental",
    "incorporeal",
})

# PHB p.50: Ranged sneak attacks only within 30 feet
SNEAK_ATTACK_MAX_RANGE = 30


def get_sneak_attack_dice(entity: dict) -> int:
    """Calculate number of sneak attack d6 dice from class levels.

    PHB p.50: Rogue gains sneak attack at 1st level (1d6) and every
    odd level thereafter: 1d6 at 1, 2d6 at 3, 3d6 at 5, etc.
    Formula: (rogue_level + 1) // 2

    This function also checks for other sources of sneak attack
    (e.g., assassin prestige class, other class features stored
    in entity["precision_damage_dice"]).

    Args:
        entity: Entity data dict

    Returns:
        Number of d6 dice for sneak attack (0 if no sneak attack)
    """
    total_dice = 0

    # Check class levels for rogue
    class_levels = entity.get(EF.CLASS_LEVELS, {})
    if isinstance(class_levels, dict):
        rogue_level = class_levels.get("rogue", 0)
        if rogue_level > 0:
            total_dice += (rogue_level + 1) // 2

    # Check for explicit precision damage dice override
    # (supports prestige classes, feats, or templates that grant sneak attack)
    explicit_dice = entity.get("precision_damage_dice", 0)
    if isinstance(explicit_dice, int) and explicit_dice > 0:
        total_dice += explicit_dice

    return total_dice


def is_target_immune(world_state: WorldState, target_id: str) -> bool:
    """Check if target is immune to sneak attack.

    PHB p.50: Creatures immune to critical hits are also immune
    to sneak attack (no discernible anatomy).

    Args:
        world_state: Current world state
        target_id: Entity ID of the target

    Returns:
        True if target is immune to sneak attack
    """
    target = world_state.entities.get(target_id)
    if target is None:
        return True  # Nonexistent target is "immune"

    # Check creature type
    creature_type = target.get("creature_type", "")
    if isinstance(creature_type, str) and creature_type.lower() in SNEAK_ATTACK_IMMUNE_TYPES:
        return True

    # Check explicit immunity flag
    if target.get("immune_to_critical_hits", False):
        return True
    if target.get("immune_to_sneak_attack", False):
        return True

    return False


def is_sneak_attack_eligible(
    world_state: WorldState,
    attacker_id: str,
    target_id: str,
    is_flanking: bool,
    is_ranged: bool = False,
    range_ft: float = 5.0,
) -> Tuple[bool, str]:
    """Determine if attacker can deal sneak attack damage to target.

    PHB p.50: Sneak attack applies when:
    1. Attacker has sneak attack dice (rogue levels or other source)
    2. Target is either flanked OR denied Dex to AC
    3. Target is not immune (undead, construct, ooze, etc.)
    4. If ranged, range must be <= 30 feet

    Args:
        world_state: Current world state
        attacker_id: Entity ID of the attacker
        target_id: Entity ID of the target
        is_flanking: Whether the attacker is currently flanking the target
        is_ranged: Whether this is a ranged attack
        range_ft: Distance to target in feet (for ranged limitation)

    Returns:
        Tuple of (is_eligible, reason) where reason explains why/why not
    """
    attacker = world_state.entities.get(attacker_id)
    if attacker is None:
        return (False, "attacker_not_found")

    # Check if attacker has sneak attack capability
    dice = get_sneak_attack_dice(attacker)
    if dice <= 0:
        return (False, "no_sneak_attack_dice")

    # Check target immunity
    if is_target_immune(world_state, target_id):
        return (False, "target_immune")

    # Check range limitation for ranged attacks
    if is_ranged and range_ft > SNEAK_ATTACK_MAX_RANGE:
        return (False, "range_exceeds_30ft")

    # Check eligibility conditions: flanking OR denied Dex to AC
    from aidm.core.flanking import is_denied_dex_to_ac

    target_denied_dex = is_denied_dex_to_ac(world_state, target_id)

    if is_flanking:
        return (True, "flanking")
    elif target_denied_dex:
        return (True, "denied_dex_to_ac")
    else:
        return (False, "target_not_flanked_or_denied_dex")


def roll_sneak_attack_damage(
    num_dice: int,
    rng: RNGManager,
) -> Tuple[int, str, List[int]]:
    """Roll sneak attack damage dice.

    PHB p.50: Sneak attack damage is Xd6 where X is determined by
    class level. This damage is precision-based and NOT multiplied
    on critical hits.

    Args:
        num_dice: Number of d6 to roll
        rng: RNG manager (uses "combat" stream)

    Returns:
        Tuple of (total_damage, dice_expression, individual_rolls)
    """
    if num_dice <= 0:
        return (0, "", [])

    combat_rng = rng.stream("combat")
    rolls = [combat_rng.randint(1, 6) for _ in range(num_dice)]
    total = sum(rolls)
    dice_expr = f"{num_dice}d6"

    return (total, dice_expr, rolls)


def calculate_sneak_attack(
    world_state: WorldState,
    attacker_id: str,
    target_id: str,
    is_flanking: bool,
    rng: RNGManager,
    is_ranged: bool = False,
    range_ft: float = 5.0,
) -> Tuple[bool, int, str, List[int], str]:
    """Full sneak attack calculation: eligibility check + damage roll.

    Combines eligibility check and damage roll into one call.
    If not eligible, returns zero damage with no RNG consumption.

    Args:
        world_state: Current world state
        attacker_id: Entity ID of the attacker
        target_id: Entity ID of the target
        is_flanking: Whether the attacker is currently flanking the target
        rng: RNG manager
        is_ranged: Whether this is a ranged attack
        range_ft: Distance to target in feet

    Returns:
        Tuple of (eligible, damage, dice_expr, rolls, reason)
    """
    eligible, reason = is_sneak_attack_eligible(
        world_state, attacker_id, target_id,
        is_flanking=is_flanking,
        is_ranged=is_ranged,
        range_ft=range_ft,
    )

    if not eligible:
        return (False, 0, "", [], reason)

    attacker = world_state.entities[attacker_id]
    num_dice = get_sneak_attack_dice(attacker)

    total, dice_expr, rolls = roll_sneak_attack_damage(num_dice, rng)

    return (True, total, dice_expr, rolls, reason)
