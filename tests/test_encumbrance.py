"""Tests for WO-054 Inventory and Encumbrance system.

Validates AD-005 Layer 1 (Weight/Encumbrance) compliance:
- Carrying capacity matches PHB Table 9-1 (p.162)
- Load tiers match PHB Table 9-2 (p.162)
- Speed penalties correct per load tier
- Max Dex bonus and check penalty correct
- Overloaded state works correctly
- Entity inventory weight calculation
- High STR progression (STR 30+)

Evidence:
- PHB Table 9-1 (p.162): Carrying Capacity by Strength
- PHB Table 9-2 (p.162): Carrying Loads penalties
- AD-005 Physical Affordance Policy
"""

import pytest
from aidm.core.encumbrance import (
    get_carrying_capacity,
    get_load_tier,
    get_load_penalties,
    get_encumbered_speed,
    calculate_total_weight,
    get_entity_encumbrance,
    LoadPenalties,
    LOAD_LIGHT,
    LOAD_MEDIUM,
    LOAD_HEAVY,
    LOAD_OVERLOADED,
)
from aidm.data.equipment_catalog_loader import EquipmentCatalog
from aidm.schemas.entity_fields import EF


@pytest.fixture
def catalog():
    return EquipmentCatalog()


# ==============================================================================
# CARRYING CAPACITY TABLE (PHB Table 9-1)
# ==============================================================================


def test_str_10_capacity():
    """PHB Table 9-1: STR 10 = 33/66/100 lb."""
    light, med, heavy = get_carrying_capacity(10)
    assert light == 33
    assert med == 66
    assert heavy == 100


def test_str_1_capacity():
    """PHB Table 9-1: STR 1 = 3/6/10 lb."""
    light, med, heavy = get_carrying_capacity(1)
    assert light == 3
    assert med == 6
    assert heavy == 10


def test_str_18_capacity():
    """PHB Table 9-1: STR 18 = 100/200/300 lb."""
    light, med, heavy = get_carrying_capacity(18)
    assert light == 100
    assert med == 200
    assert heavy == 300


def test_str_20_capacity():
    """PHB Table 9-1: STR 20 = 133/266/400 lb."""
    light, med, heavy = get_carrying_capacity(20)
    assert light == 133
    assert med == 266
    assert heavy == 400


def test_str_15_capacity():
    """PHB Table 9-1: STR 15 = 66/133/200 lb."""
    light, med, heavy = get_carrying_capacity(15)
    assert light == 66
    assert med == 133
    assert heavy == 200


def test_str_0_capacity():
    """STR 0 has zero capacity."""
    assert get_carrying_capacity(0) == (0, 0, 0)


def test_str_29_capacity():
    """PHB Table 9-1: STR 29 = 466/933/1400 lb."""
    light, med, heavy = get_carrying_capacity(29)
    assert light == 466
    assert med == 933
    assert heavy == 1400


def test_str_30_capacity():
    """PHB: STR 30 = STR 20 × 4 = 532/1064/1600 lb."""
    light, med, heavy = get_carrying_capacity(30)
    # STR 20 = (133, 266, 400), × 4
    assert light == 133 * 4
    assert med == 266 * 4
    assert heavy == 400 * 4


# ==============================================================================
# LOAD TIER DETERMINATION
# ==============================================================================


def test_light_load():
    """33 lb or less with STR 10 = light load."""
    assert get_load_tier(33, 10) == LOAD_LIGHT
    assert get_load_tier(0, 10) == LOAD_LIGHT
    assert get_load_tier(20, 10) == LOAD_LIGHT


def test_medium_load():
    """34-66 lb with STR 10 = medium load."""
    assert get_load_tier(34, 10) == LOAD_MEDIUM
    assert get_load_tier(50, 10) == LOAD_MEDIUM
    assert get_load_tier(66, 10) == LOAD_MEDIUM


def test_heavy_load():
    """67-100 lb with STR 10 = heavy load."""
    assert get_load_tier(67, 10) == LOAD_HEAVY
    assert get_load_tier(85, 10) == LOAD_HEAVY
    assert get_load_tier(100, 10) == LOAD_HEAVY


def test_overloaded():
    """Over 100 lb with STR 10 = overloaded."""
    assert get_load_tier(101, 10) == LOAD_OVERLOADED
    assert get_load_tier(500, 10) == LOAD_OVERLOADED


def test_boundary_light_medium():
    """Boundary between light and medium at exactly light_max."""
    assert get_load_tier(33, 10) == LOAD_LIGHT
    assert get_load_tier(33.5, 10) == LOAD_MEDIUM


def test_boundary_medium_heavy():
    """Boundary between medium and heavy at exactly medium_max."""
    assert get_load_tier(66, 10) == LOAD_MEDIUM
    assert get_load_tier(66.5, 10) == LOAD_HEAVY


def test_boundary_heavy_overloaded():
    """Boundary between heavy and overloaded at exactly heavy_max."""
    assert get_load_tier(100, 10) == LOAD_HEAVY
    assert get_load_tier(100.5, 10) == LOAD_OVERLOADED


# ==============================================================================
# LOAD PENALTIES (PHB Table 9-2)
# ==============================================================================


def test_light_penalties():
    """Light load: no penalties."""
    p = get_load_penalties(LOAD_LIGHT)
    assert p.max_dex_bonus is None  # Unlimited
    assert p.check_penalty == 0
    assert p.speed_30_ft == 30
    assert p.speed_20_ft == 20
    assert p.run_multiplier == 4


def test_medium_penalties():
    """Medium load: max Dex +3, -3 check, speed 20/15."""
    p = get_load_penalties(LOAD_MEDIUM)
    assert p.max_dex_bonus == 3
    assert p.check_penalty == -3
    assert p.speed_30_ft == 20
    assert p.speed_20_ft == 15
    assert p.run_multiplier == 4


def test_heavy_penalties():
    """Heavy load: max Dex +1, -6 check, speed 20/15, run ×3."""
    p = get_load_penalties(LOAD_HEAVY)
    assert p.max_dex_bonus == 1
    assert p.check_penalty == -6
    assert p.speed_30_ft == 20
    assert p.speed_20_ft == 15
    assert p.run_multiplier == 3


def test_overloaded_penalties():
    """Overloaded: max Dex +0, -6 check, 5 ft only, cannot run."""
    p = get_load_penalties(LOAD_OVERLOADED)
    assert p.max_dex_bonus == 0
    assert p.check_penalty == -6
    assert p.speed_30_ft == 5
    assert p.speed_20_ft == 5
    assert p.run_multiplier == 1


def test_invalid_load_tier_raises():
    """Invalid load tier raises ValueError."""
    with pytest.raises(ValueError, match="Unknown load tier"):
        get_load_penalties("invalid")


# ==============================================================================
# SPEED CALCULATIONS
# ==============================================================================


def test_speed_30ft_light():
    """30 ft base + light load = 30 ft."""
    assert get_encumbered_speed(30, LOAD_LIGHT) == 30


def test_speed_30ft_medium():
    """30 ft base + medium load = 20 ft."""
    assert get_encumbered_speed(30, LOAD_MEDIUM) == 20


def test_speed_30ft_heavy():
    """30 ft base + heavy load = 20 ft."""
    assert get_encumbered_speed(30, LOAD_HEAVY) == 20


def test_speed_20ft_light():
    """20 ft base + light load = 20 ft (dwarf, halfling)."""
    assert get_encumbered_speed(20, LOAD_LIGHT) == 20


def test_speed_20ft_medium():
    """20 ft base + medium load = 15 ft."""
    assert get_encumbered_speed(20, LOAD_MEDIUM) == 15


def test_speed_20ft_heavy():
    """20 ft base + heavy load = 15 ft."""
    assert get_encumbered_speed(20, LOAD_HEAVY) == 15


def test_speed_overloaded():
    """Overloaded = 5 ft regardless of base speed."""
    assert get_encumbered_speed(30, LOAD_OVERLOADED) == 5
    assert get_encumbered_speed(20, LOAD_OVERLOADED) == 5


# ==============================================================================
# ENTITY INVENTORY WEIGHT CALCULATION
# ==============================================================================


def test_empty_inventory_zero_weight():
    """No inventory = 0 weight."""
    entity = {}
    assert calculate_total_weight(entity) == 0.0


def test_inventory_with_weight_lb():
    """Items with explicit weight_lb in entry."""
    entity = {
        EF.INVENTORY: [
            {"item_id": "rope", "weight_lb": 10.0, "quantity": 1},
            {"item_id": "torch", "weight_lb": 1.0, "quantity": 3},
        ]
    }
    assert calculate_total_weight(entity) == 13.0


def test_inventory_with_catalog(catalog):
    """Items resolved against equipment catalog."""
    entity = {
        EF.INVENTORY: [
            {"item_id": "rope_hemp_50ft", "quantity": 1},
            {"item_id": "grappling_hook", "quantity": 1},
            {"item_id": "torch", "quantity": 5},
        ]
    }
    # rope=10 + hook=4 + 5*torch=5 = 19
    assert calculate_total_weight(entity, catalog) == 19.0


def test_inventory_string_ids_with_catalog(catalog):
    """Simple string item IDs resolved against catalog."""
    entity = {
        EF.INVENTORY: ["rope_hemp_50ft", "grappling_hook"]
    }
    # rope=10 + hook=4 = 14
    assert calculate_total_weight(entity, catalog) == 14.0


def test_inventory_mixed_sources(catalog):
    """Mix of catalog items and items with explicit weights."""
    entity = {
        EF.INVENTORY: [
            {"item_id": "rope_hemp_50ft", "quantity": 1},
            {"item_id": "custom_thing", "weight_lb": 7.5, "quantity": 2},
        ]
    }
    # rope=10 + 2*7.5=15 = 25
    assert calculate_total_weight(entity, catalog) == 25.0


def test_inventory_unknown_item_no_catalog():
    """Unknown item without catalog and without weight_lb = 0 weight."""
    entity = {
        EF.INVENTORY: [
            {"item_id": "unknown_thing", "quantity": 1},
        ]
    }
    assert calculate_total_weight(entity) == 0.0


# ==============================================================================
# FULL ENCUMBRANCE STATUS
# ==============================================================================


def test_entity_encumbrance_light(catalog):
    """Entity with light load."""
    entity = {
        EF.STRENGTH_SCORE: 10,
        EF.BASE_SPEED: 30,
        EF.INVENTORY: [
            {"item_id": "torch", "quantity": 2},
        ]
    }
    status = get_entity_encumbrance(entity, catalog)
    assert status["total_weight_lb"] == 2.0
    assert status["strength"] == 10
    assert status["light_max_lb"] == 33
    assert status["load_tier"] == LOAD_LIGHT
    assert status["effective_speed_ft"] == 30
    assert status["penalties"].check_penalty == 0


def test_entity_encumbrance_medium(catalog):
    """Entity with medium load (STR 10, carrying ~50 lb)."""
    entity = {
        EF.STRENGTH_SCORE: 10,
        EF.BASE_SPEED: 30,
        EF.INVENTORY: [
            {"item_id": "rope_hemp_50ft", "quantity": 1},   # 10
            {"item_id": "tent", "quantity": 1},               # 20
            {"item_id": "ladder_10ft", "quantity": 1},        # 20
        ]
    }
    status = get_entity_encumbrance(entity, catalog)
    assert status["total_weight_lb"] == 50.0
    assert status["load_tier"] == LOAD_MEDIUM
    assert status["effective_speed_ft"] == 20
    assert status["penalties"].max_dex_bonus == 3
    assert status["penalties"].check_penalty == -3


def test_entity_encumbrance_heavy(catalog):
    """Entity with heavy load (STR 10, carrying ~80 lb)."""
    entity = {
        EF.STRENGTH_SCORE: 10,
        EF.BASE_SPEED: 30,
        EF.INVENTORY: [
            {"item_id": "custom_gear", "weight_lb": 80.0, "quantity": 1},
        ]
    }
    status = get_entity_encumbrance(entity, catalog)
    assert status["total_weight_lb"] == 80.0
    assert status["load_tier"] == LOAD_HEAVY
    assert status["effective_speed_ft"] == 20
    assert status["penalties"].max_dex_bonus == 1
    assert status["penalties"].run_multiplier == 3


def test_entity_encumbrance_overloaded(catalog):
    """Entity overloaded (STR 10, carrying 150 lb)."""
    entity = {
        EF.STRENGTH_SCORE: 10,
        EF.BASE_SPEED: 30,
        EF.INVENTORY: [
            {"item_id": "heavy_stuff", "weight_lb": 150.0, "quantity": 1},
        ]
    }
    status = get_entity_encumbrance(entity, catalog)
    assert status["total_weight_lb"] == 150.0
    assert status["load_tier"] == LOAD_OVERLOADED
    assert status["effective_speed_ft"] == 5
    assert status["penalties"].max_dex_bonus == 0


def test_entity_encumbrance_defaults():
    """Entity with no fields defaults to STR 10, speed 30, empty inventory."""
    status = get_entity_encumbrance({})
    assert status["strength"] == 10
    assert status["total_weight_lb"] == 0.0
    assert status["load_tier"] == LOAD_LIGHT
    assert status["effective_speed_ft"] == 30


def test_strong_character_carries_more(catalog):
    """STR 18 character handles 100 lb as light load."""
    entity = {
        EF.STRENGTH_SCORE: 18,
        EF.BASE_SPEED: 30,
        EF.INVENTORY: [
            {"item_id": "gear", "weight_lb": 95.0, "quantity": 1},
        ]
    }
    status = get_entity_encumbrance(entity, catalog)
    assert status["load_tier"] == LOAD_LIGHT  # 95 <= 100 (light max for STR 18)
    assert status["effective_speed_ft"] == 30


def test_dwarf_20ft_base_speed_encumbered(catalog):
    """Dwarf (20 ft base) at medium load = 15 ft speed."""
    entity = {
        EF.STRENGTH_SCORE: 14,
        EF.BASE_SPEED: 20,
        EF.INVENTORY: [
            {"item_id": "gear", "weight_lb": 70.0, "quantity": 1},
        ]
    }
    status = get_entity_encumbrance(entity, catalog)
    # STR 14: light=58, medium=116, heavy=175
    assert status["load_tier"] == LOAD_MEDIUM
    assert status["effective_speed_ft"] == 15


# ==============================================================================
# LOAD PENALTIES DATACLASS
# ==============================================================================


def test_load_penalties_frozen():
    """LoadPenalties must be immutable (frozen dataclass)."""
    p = get_load_penalties(LOAD_LIGHT)
    with pytest.raises(AttributeError):
        p.check_penalty = 999


# ==============================================================================
# CARRYING CAPACITY PROGRESSION
# ==============================================================================


def test_capacity_increases_with_strength():
    """Each STR point should increase capacity."""
    prev_heavy = 0
    for strength in range(1, 30):
        _, _, heavy = get_carrying_capacity(strength)
        assert heavy > prev_heavy, f"STR {strength} not > STR {strength - 1}"
        prev_heavy = heavy


def test_all_capacity_entries_positive():
    """All capacity values must be positive for STR 1+."""
    for strength in range(1, 30):
        light, med, heavy = get_carrying_capacity(strength)
        assert light > 0
        assert med > light
        assert heavy > med
