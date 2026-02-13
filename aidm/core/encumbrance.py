"""Inventory and Encumbrance resolver for WO-054 (AD-005 Layer 1).

Implements D&D 3.5e carrying capacity and load tier mechanics:
- Carrying capacity indexed by Strength (PHB Table 9-1, p.162)
- Three load tiers: light, medium, heavy (PHB Table 9-2, p.162)
- Mechanical penalties: speed reduction, max Dex bonus, check penalty
- Overloaded state when exceeding maximum load

This module is pure Box — deterministic, no LLM involvement.

RNG consumption: None (no randomness in encumbrance).

CITATIONS:
- PHB Table 9-1 (p.162): Carrying Capacity by Strength
- PHB Table 9-2 (p.162): Carrying Loads penalties
- PHB p.162: "Lift over head = max load, lift off ground = 2x max, push/drag = 5x max"
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass

from aidm.schemas.entity_fields import EF


# =============================================================================
# CARRYING CAPACITY TABLE (PHB Table 9-1, p.162)
# =============================================================================

# Maps Strength score → (light_load_max_lb, medium_load_max_lb, heavy_load_max_lb)
# For STR 1-29. Scores above 29 follow the progression formula.
_CAPACITY_TABLE = {
    1:  (3, 6, 10),
    2:  (6, 13, 20),
    3:  (10, 20, 30),
    4:  (13, 26, 40),
    5:  (16, 33, 50),
    6:  (20, 40, 60),
    7:  (23, 46, 70),
    8:  (26, 53, 80),
    9:  (30, 60, 90),
    10: (33, 66, 100),
    11: (38, 76, 115),
    12: (43, 86, 130),
    13: (50, 100, 150),
    14: (58, 116, 175),
    15: (66, 133, 200),
    16: (76, 153, 230),
    17: (86, 173, 260),
    18: (100, 200, 300),
    19: (116, 233, 350),
    20: (133, 266, 400),
    21: (153, 306, 460),
    22: (173, 346, 520),
    23: (200, 400, 600),
    24: (233, 466, 700),
    25: (266, 533, 800),
    26: (306, 613, 920),
    27: (346, 693, 1040),
    28: (400, 800, 1200),
    29: (466, 933, 1400),
}

# PHB Table 9-1 footnote: for STR 30+, multiply the value at STR-10 by 4.
# So STR 30 = STR 20 × 4, STR 40 = STR 30 × 4 = STR 20 × 16, etc.


def get_carrying_capacity(strength: int) -> tuple:
    """Get carrying capacity thresholds for a given Strength score.

    Args:
        strength: The creature's Strength score (1+).

    Returns:
        Tuple of (light_max_lb, medium_max_lb, heavy_max_lb).
        Items up to light_max are light load, up to medium_max are medium,
        up to heavy_max are heavy. Above heavy_max is overloaded.

    Citations:
        PHB Table 9-1, p.162
    """
    if strength <= 0:
        return (0, 0, 0)

    if strength <= 29:
        return _CAPACITY_TABLE[strength]

    # PHB: for every 10 STR above 20, multiply by 4
    # STR 30 = STR 20 × 4, STR 40 = STR 30 × 4, etc.
    multiplier = 4 ** ((strength - 20) // 10)
    base_str = strength - 10 * ((strength - 20) // 10)
    if base_str in _CAPACITY_TABLE:
        base = _CAPACITY_TABLE[base_str]
        return (
            base[0] * multiplier,
            base[1] * multiplier,
            base[2] * multiplier,
        )
    # Fallback for edge cases
    return _CAPACITY_TABLE[29]


# =============================================================================
# LOAD TIER DETERMINATION
# =============================================================================

# Load tier constants
LOAD_LIGHT = "light"
LOAD_MEDIUM = "medium"
LOAD_HEAVY = "heavy"
LOAD_OVERLOADED = "overloaded"


def get_load_tier(total_weight_lb: float, strength: int) -> str:
    """Determine the load tier for a given weight and Strength.

    Args:
        total_weight_lb: Total weight carried in pounds.
        strength: The creature's Strength score.

    Returns:
        One of: "light", "medium", "heavy", "overloaded".

    Citations:
        PHB Table 9-1, p.162
    """
    light_max, medium_max, heavy_max = get_carrying_capacity(strength)

    if total_weight_lb <= light_max:
        return LOAD_LIGHT
    elif total_weight_lb <= medium_max:
        return LOAD_MEDIUM
    elif total_weight_lb <= heavy_max:
        return LOAD_HEAVY
    else:
        return LOAD_OVERLOADED


# =============================================================================
# LOAD PENALTIES (PHB Table 9-2, p.162)
# =============================================================================

@dataclass(frozen=True)
class LoadPenalties:
    """Mechanical penalties for a load tier.

    Citations:
        PHB Table 9-2, p.162
    """
    max_dex_bonus: Optional[int]  # None = unlimited
    check_penalty: int            # Applied to STR/DEX-based skill checks
    speed_30_ft: int              # Speed for creatures with 30 ft base
    speed_20_ft: int              # Speed for creatures with 20 ft base
    run_multiplier: int           # Run action multiplier (×3 or ×4)


_LOAD_PENALTIES = {
    LOAD_LIGHT: LoadPenalties(
        max_dex_bonus=None,
        check_penalty=0,
        speed_30_ft=30,
        speed_20_ft=20,
        run_multiplier=4,
    ),
    LOAD_MEDIUM: LoadPenalties(
        max_dex_bonus=3,
        check_penalty=-3,
        speed_30_ft=20,
        speed_20_ft=15,
        run_multiplier=4,
    ),
    LOAD_HEAVY: LoadPenalties(
        max_dex_bonus=1,
        check_penalty=-6,
        speed_30_ft=20,
        speed_20_ft=15,
        run_multiplier=3,
    ),
    LOAD_OVERLOADED: LoadPenalties(
        max_dex_bonus=0,
        check_penalty=-6,
        speed_30_ft=5,  # Can only stagger (5 ft)
        speed_20_ft=5,
        run_multiplier=1,  # Cannot run
    ),
}


def get_load_penalties(load_tier: str) -> LoadPenalties:
    """Get the mechanical penalties for a load tier.

    Args:
        load_tier: One of "light", "medium", "heavy", "overloaded".

    Returns:
        LoadPenalties with max_dex_bonus, check_penalty, speed, run_multiplier.

    Raises:
        ValueError: If load_tier is not recognized.

    Citations:
        PHB Table 9-2, p.162
    """
    if load_tier not in _LOAD_PENALTIES:
        raise ValueError(f"Unknown load tier: {load_tier}")
    return _LOAD_PENALTIES[load_tier]


def get_encumbered_speed(base_speed_ft: int, load_tier: str) -> int:
    """Calculate effective speed after encumbrance penalties.

    Args:
        base_speed_ft: Base movement speed in feet (typically 30 or 20).
        load_tier: Current load tier.

    Returns:
        Effective speed in feet.

    Citations:
        PHB Table 9-2, p.162: "Reduced Speed" column
        PHB p.162: Speed reduction applies to creatures with base 30 ft or 20 ft.
    """
    penalties = get_load_penalties(load_tier)

    if load_tier == LOAD_LIGHT:
        return base_speed_ft  # No penalty
    elif load_tier == LOAD_OVERLOADED:
        return 5  # Can only stagger

    # Medium and Heavy: standard 3.5e speed reduction
    if base_speed_ft >= 30:
        return penalties.speed_30_ft
    else:
        return penalties.speed_20_ft


# =============================================================================
# ENTITY INVENTORY WEIGHT CALCULATION
# =============================================================================


def calculate_total_weight(entity: Dict[str, Any], catalog=None) -> float:
    """Calculate the total weight of an entity's inventory.

    Args:
        entity: Entity dict with EF.INVENTORY field.
        catalog: Optional EquipmentCatalog for looking up item weights.
                 If None, uses weight_lb from inventory item dicts.

    Returns:
        Total weight in pounds.
    """
    inventory = entity.get(EF.INVENTORY, [])
    total = 0.0

    for item_entry in inventory:
        if isinstance(item_entry, dict):
            item_id = item_entry.get("item_id", "")
            quantity = item_entry.get("quantity", 1)

            # Try catalog lookup first
            if catalog is not None:
                catalog_item = catalog.get(item_id)
                if catalog_item is not None:
                    total += catalog_item.weight_lb * quantity
                    continue

            # Fall back to weight_lb in the item entry itself
            total += item_entry.get("weight_lb", 0.0) * quantity
        elif isinstance(item_entry, str):
            # Simple string item ID — requires catalog
            if catalog is not None:
                catalog_item = catalog.get(item_entry)
                if catalog_item is not None:
                    total += catalog_item.weight_lb

    return total


def get_entity_encumbrance(entity: Dict[str, Any], catalog=None) -> dict:
    """Calculate complete encumbrance status for an entity.

    Args:
        entity: Entity dict with EF.INVENTORY and EF.STRENGTH_SCORE fields.
        catalog: Optional EquipmentCatalog for item weight lookups.

    Returns:
        Dict with:
        - total_weight_lb: float
        - strength: int
        - light_max_lb: float
        - medium_max_lb: float
        - heavy_max_lb: float
        - load_tier: str ("light", "medium", "heavy", "overloaded")
        - penalties: LoadPenalties
        - effective_speed_ft: int
    """
    strength = entity.get(EF.STRENGTH_SCORE, 10)
    base_speed = entity.get(EF.BASE_SPEED, 30)
    total_weight = calculate_total_weight(entity, catalog)

    light_max, medium_max, heavy_max = get_carrying_capacity(strength)
    load_tier = get_load_tier(total_weight, strength)
    penalties = get_load_penalties(load_tier)
    effective_speed = get_encumbered_speed(base_speed, load_tier)

    return {
        "total_weight_lb": total_weight,
        "strength": strength,
        "light_max_lb": light_max,
        "medium_max_lb": medium_max,
        "heavy_max_lb": heavy_max,
        "load_tier": load_tier,
        "penalties": penalties,
        "effective_speed_ft": effective_speed,
    }
