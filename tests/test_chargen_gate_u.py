"""Gate U: Chargen Foundation Tests (WO-CHARGEN-FOUNDATION-001).

21 tests covering:
- Ability score generation (U-01 through U-05)
- Race definitions (U-06 through U-10)
- Weapon catalog (U-11, U-13, U-15, U-16, U-19)
- Armor catalog (U-12, U-14, U-17, U-20)
- Entity field constant (U-18)

Source: WO-CHARGEN-FOUNDATION-001 Gate Specification.
"""

import pytest

from aidm.chargen.ability_scores import (
    roll_4d6_drop_lowest,
    generate_ability_array,
    ability_modifier,
    validate_point_buy,
    ABILITY_NAMES,
    STANDARD_ARRAY,
)
from aidm.data.races import (
    RACE_REGISTRY,
    get_race,
    apply_racial_mods,
    list_races,
)
from aidm.data.equipment_catalog_loader import (
    EquipmentCatalog,
    WeaponTemplate,
    ArmorTemplate,
)
from aidm.schemas.entity_fields import EF
from aidm.schemas.attack import Weapon


@pytest.fixture
def catalog():
    """Load the default Equipment Item Catalog."""
    return EquipmentCatalog()


# ==============================================================================
# ABILITY SCORES (U-01 through U-05)
# ==============================================================================


def test_u01_roll_4d6_drop_lowest_range():
    """U-01: roll_4d6_drop_lowest() returns int in range 3-18."""
    for _ in range(100):
        result = roll_4d6_drop_lowest()
        assert isinstance(result, int)
        assert 3 <= result <= 18, f"Got {result}, expected 3-18"


def test_u02_generate_ability_array_4d6():
    """U-02: generate_ability_array('4d6') returns dict with 6 keys."""
    scores = generate_ability_array("4d6")
    assert isinstance(scores, dict)
    assert len(scores) == 6
    assert set(scores.keys()) == set(ABILITY_NAMES)
    for name, score in scores.items():
        assert 3 <= score <= 18, f"{name}={score} out of range"


def test_u03_generate_ability_array_standard():
    """U-03: generate_ability_array('standard') returns [15,14,13,12,10,8]."""
    scores = generate_ability_array("standard")
    expected = dict(zip(ABILITY_NAMES, STANDARD_ARRAY))
    assert scores == expected


def test_u04_generate_ability_array_point_buy():
    """U-04: generate_ability_array('point_buy') validates 25-point budget."""
    scores = generate_ability_array("point_buy")
    assert len(scores) == 6
    assert validate_point_buy(scores, budget=25) is True


def test_u05_ability_modifier():
    """U-05: ability_modifier formula: (score - 10) // 2."""
    assert ability_modifier(10) == 0
    assert ability_modifier(18) == 4
    assert ability_modifier(7) == -2
    assert ability_modifier(1) == -5
    assert ability_modifier(20) == 5
    assert ability_modifier(8) == -1
    assert ability_modifier(9) == -1
    assert ability_modifier(11) == 0


# ==============================================================================
# RACES (U-06 through U-10)
# ==============================================================================


def test_u06_all_7_races_exist():
    """U-06: All 7 races exist in RACE_REGISTRY."""
    expected = {"human", "elf", "dwarf", "halfling", "gnome", "half_elf", "half_orc"}
    assert set(RACE_REGISTRY.keys()) == expected
    assert len(list_races()) == 7


def test_u07_dwarf_fields():
    """U-07: Dwarf has +2 CON, -2 CHA, speed 20, size medium."""
    dwarf = get_race("dwarf")
    assert dwarf.ability_mods == {"con": 2, "cha": -2}
    assert dwarf.base_speed == 20
    assert dwarf.size == "medium"
    assert dwarf.speed_ignores_armor is True
    assert dwarf.favored_class == "fighter"


def test_u08_halfling_fields():
    """U-08: Halfling has +2 DEX, -2 STR, size small."""
    halfling = get_race("halfling")
    assert halfling.ability_mods == {"dex": 2, "str": -2}
    assert halfling.size == "small"
    assert halfling.base_speed == 20
    assert halfling.favored_class == "rogue"


def test_u09_human_bonuses():
    """U-09: Human has bonus_feats=1, bonus_skill_points_per_level=1."""
    human = get_race("human")
    assert human.bonus_feats == 1
    assert human.bonus_skill_points_per_level == 1
    assert human.ability_mods == {}
    assert human.favored_class == "any"


def test_u10_apply_racial_mods_elf():
    """U-10: apply_racial_mods for elf: dex=12, con=8 from base 10."""
    base = {name: 10 for name in ABILITY_NAMES}
    result = apply_racial_mods(base, "elf")
    assert result["dex"] == 12
    assert result["con"] == 8
    # Other stats unchanged
    assert result["str"] == 10
    assert result["int"] == 10
    assert result["wis"] == 10
    assert result["cha"] == 10
    # Original not mutated
    assert base["dex"] == 10
    assert base["con"] == 10


# ==============================================================================
# WEAPON CATALOG (U-11, U-13, U-15, U-16, U-19)
# ==============================================================================


def test_u11_weapon_catalog_count(catalog):
    """U-11: Weapon catalog has >= 20 weapons."""
    weapons = catalog.get_all_weapons()
    assert len(weapons) >= 20, f"Expected >= 20 weapons, got {len(weapons)}"


def test_u13_longsword_fields(catalog):
    """U-13: get_weapon('longsword') returns correct damage/crit/type."""
    sword = catalog.get_weapon("longsword")
    assert sword is not None
    assert sword.name == "Longsword"
    assert sword.damage_dice == "1d8"
    assert sword.critical_range == 19
    assert sword.critical_multiplier == 2
    assert sword.damage_type == "slashing"
    assert sword.weapon_type == "one-handed"
    assert sword.proficiency_group == "martial"


def test_u15_weapon_template_to_weapon(catalog):
    """U-15: WeaponTemplate.to_weapon() produces valid Weapon instance."""
    sword = catalog.get_weapon("longsword")
    weapon = sword.to_weapon(damage_bonus=2)
    assert isinstance(weapon, Weapon)
    assert weapon.damage_dice == "1d8"
    assert weapon.damage_bonus == 2
    assert weapon.damage_type == "slashing"
    assert weapon.critical_range == 19
    assert weapon.critical_multiplier == 2
    assert weapon.grip == "one-handed"
    assert weapon.is_two_handed is False

    # Test two-handed weapon conversion
    gs = catalog.get_weapon("greatsword")
    gs_weapon = gs.to_weapon()
    assert gs_weapon.is_two_handed is True
    assert gs_weapon.grip == "two-handed"
    assert gs_weapon.damage_dice == "2d6"


def test_u16_get_weapons_by_proficiency_simple(catalog):
    """U-16: get_weapons_by_proficiency('simple') returns only simple weapons."""
    simple = catalog.get_weapons_by_proficiency("simple")
    assert len(simple) >= 9, f"Expected >= 9 simple weapons, got {len(simple)}"
    for w in simple:
        assert w.proficiency_group == "simple", (
            f"{w.item_id} is {w.proficiency_group}, not simple"
        )

    # Verify martial weapons are not included
    martial_ids = {w.item_id for w in catalog.get_weapons_by_proficiency("martial")}
    simple_ids = {w.item_id for w in simple}
    assert simple_ids.isdisjoint(martial_ids), "Simple and martial overlap"


def test_u19_dwarven_waraxe_exotic(catalog):
    """U-19: Dwarven waraxe is exotic proficiency group."""
    waraxe = catalog.get_weapon("dwarven_waraxe")
    assert waraxe is not None
    assert waraxe.proficiency_group == "exotic"
    assert waraxe.damage_dice == "1d10"
    assert waraxe.critical_multiplier == 3


# ==============================================================================
# ARMOR CATALOG (U-12, U-14, U-17, U-20)
# ==============================================================================


def test_u12_armor_catalog_count(catalog):
    """U-12: Armor catalog has >= 15 entries (armor + shields)."""
    armor = catalog.get_all_armor()
    assert len(armor) >= 15, f"Expected >= 15 armor entries, got {len(armor)}"


def test_u14_full_plate_fields(catalog):
    """U-14: get_armor('full_plate') returns ac_bonus=8, max_dex=1."""
    plate = catalog.get_armor("full_plate")
    assert plate is not None
    assert plate.name == "Full Plate"
    assert plate.ac_bonus == 8
    assert plate.max_dex_bonus == 1
    assert plate.armor_type == "heavy"
    assert plate.armor_check_penalty == -6
    assert plate.arcane_spell_failure == 35


def test_u17_get_armor_by_type_heavy(catalog):
    """U-17: get_armor_by_type('heavy') returns only heavy armor."""
    heavy = catalog.get_armor_by_type("heavy")
    assert len(heavy) >= 4, f"Expected >= 4 heavy armor, got {len(heavy)}"
    for a in heavy:
        assert a.armor_type == "heavy", (
            f"{a.item_id} is {a.armor_type}, not heavy"
        )

    # Verify shields are not included
    shield_ids = {a.item_id for a in catalog.get_armor_by_type("shield")}
    heavy_ids = {a.item_id for a in heavy}
    assert heavy_ids.isdisjoint(shield_ids), "Heavy and shield overlap"


def test_u20_tower_shield_fields(catalog):
    """U-20: Tower shield has max_dex_bonus=2, armor_check_penalty=-10."""
    tower = catalog.get_armor("tower_shield")
    assert tower is not None
    assert tower.max_dex_bonus == 2
    assert tower.armor_check_penalty == -10
    assert tower.armor_type == "shield"
    assert tower.ac_bonus == 4


# ==============================================================================
# ENTITY FIELD (U-18)
# ==============================================================================


def test_u18_ef_race_field():
    """U-18: EF.RACE field constant exists."""
    assert hasattr(EF, "RACE")
    assert EF.RACE == "race"
