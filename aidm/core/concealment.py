"""Concealment and miss chance resolver for WO-049.

Implements D&D 3.5e Concealment (PHB p.152):
- Concealment grants a miss chance on attacks that would otherwise hit
- Miss chance is rolled AFTER the attack hits AC (d100 percentile)
- Concealment does NOT affect AC; it creates a separate miss chance
- Total concealment prevents targeting entirely (handled by targeting resolver)

CONCEALMENT LEVELS (PHB p.152):
- 20%: Light obscurement (fog, smoke, dense foliage)
- 50%: Concealment (blur spell, displacement, invisibility)
- Total: Cannot be targeted (not handled here — targeting resolver blocks)

INVISIBILITY (PHB p.152):
- Invisible creatures have total concealment to attackers who can't see them
- If attacker has some means of locating (Listen, blindsense), 50% miss chance
- Invisible attacker gets +2 attack bonus (denies Dex to AC, covered by conditions)

RNG CONSUMPTION:
- Miss chance check uses combat stream AFTER hit determination
- Consumes 1 d100 roll only when hit=True and miss_chance > 0

ENTITY FORMAT:
  entity[EF.MISS_CHANCE] = 20  # 20% miss chance (0-100)
  # OR via conditions:
  condition with miss_chance_percent field
"""

from typing import Optional
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


def get_miss_chance(
    world_state: WorldState,
    defender_id: str,
) -> int:
    """Get the effective miss chance percentage for a defender.

    Checks entity's direct miss_chance field first, then aggregates
    miss chance from conditions. Uses the highest miss chance found
    (PHB p.152: miss chances don't stack, use the best one).

    Args:
        world_state: Current world state
        defender_id: Entity ID of the defender

    Returns:
        Miss chance percentage (0-100). 0 means no miss chance.
    """
    entity = world_state.entities.get(defender_id)
    if entity is None:
        return 0

    # Direct miss chance field (e.g., from blur spell or environment)
    best_miss_chance = entity.get(EF.MISS_CHANCE, 0)

    # Check conditions for miss chance
    conditions_data = entity.get(EF.CONDITIONS, {})
    if isinstance(conditions_data, dict):
        for condition_id, condition_dict in conditions_data.items():
            modifiers = condition_dict.get("modifiers", {})
            condition_miss_chance = modifiers.get("miss_chance_percent", 0)
            if condition_miss_chance > best_miss_chance:
                best_miss_chance = condition_miss_chance

    return min(best_miss_chance, 100)  # Cap at 100%


def check_miss_chance(
    miss_chance_percent: int,
    d100_roll: int,
) -> bool:
    """Check if an attack misses due to concealment.

    PHB p.152: "Roll a d100. If the result is within the miss chance
    percentage, the attack misses."

    Convention: d100 roll of 1-miss_chance_percent = miss.

    Args:
        miss_chance_percent: Miss chance percentage (1-100)
        d100_roll: d100 roll result (1-100)

    Returns:
        True if the attack MISSES due to concealment.
    """
    if miss_chance_percent <= 0:
        return False
    return d100_roll <= miss_chance_percent
