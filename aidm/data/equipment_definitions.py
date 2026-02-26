"""Armor and weapon catalog — D&D 3.5e PHB mechanical values.

Source: PHB 3.5e pp.123-126 (armor table) and pp.116-122 (weapon table).
Cross-referenced with PCGen rsrd_equip.lst (OGL) via LST-PARSER-001.
Facts (game mechanic values) are not copyrightable.

Note: PCGen rsrd_equip.lst is the authoritative OSS source. When LST-PARSER-001
output is available, re-run spot-checks against this table and flag discrepancies
as FINDINGs in the DATA-EQUIPMENT-001 debrief.
"""

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class ArmorDefinition:
    armor_id: str           # snake_case canonical ID
    name: str               # Display name (PHB name)
    armor_type: str         # "light" | "medium" | "heavy" | "shield"
    ac_bonus: int           # Armor bonus to AC (PHB column "Armor Bonus")
    max_dex_bonus: int      # Max DEX bonus while wearing; 99 = no limit
    armor_check_penalty: int  # ACP value; negative (e.g., -6) or 0
    arcane_spell_failure: int  # ASF percentage 0-100
    weight_lb: float        # Weight in pounds


@dataclass(frozen=True)
class WeaponDefinition:
    weapon_id: str
    name: str
    damage_dice: str        # e.g., "1d8" (medium-sized weapon)
    damage_dice_small: str  # Damage for small-sized wielder
    crit_range: int         # Lower bound of threat range (e.g., 19 for 19-20)
    crit_mult: int          # e.g., 2 for x2, 3 for x3
    damage_type: str        # "slashing" | "piercing" | "bludgeoning" or combinations
    weight_lb: float
    weapon_category: str    # "simple" | "martial" | "exotic"
    weapon_type: str        # "light" | "one-handed" | "two-handed" | "ranged"


# ==============================================================================
# ARMOR REGISTRY — PHB p.123-126
# ==============================================================================
#
# Spot-check table (PHB p.123 vs values below):
# | Armor        | AC | Max DEX | ACP | ASF% |
# |--------------|-----|---------|-----|------|
# | Padded       |  1  |   8     |  0  |  5   |
# | Leather      |  2  |   6     |  0  | 10   |
# | Studded Leat |  3  |   5     | -1  | 15   |
# | Chain Shirt  |  4  |   4     | -2  | 20   |
# | Hide         |  3  |   4     | -3  | 20   |
# | Scale Mail   |  4  |   3     | -4  | 25   |
# | Chainmail    |  5  |   2     | -5  | 30   |
# | Breastplate  |  5  |   3     | -4  | 25   |
# | Splint Mail  |  6  |   0     | -7  | 40   |
# | Banded Mail  |  6  |   1     | -6  | 35   |
# | Half Plate   |  7  |   0     | -7  | 40   |
# | Full Plate   |  8  |   1     | -6  | 35   |
#
# Shields (PHB p.124):
# | Buckler      | +1  |   -     | -1  |  5   |
# | Lt Shield    | +1  |   -     | -1  |  5   |
# | Hvy Shield   | +2  |   -     | -2  | 15   |
# | Tower Shield | +4  |   2     | -10 | 50   |

ARMOR_REGISTRY: Dict[str, ArmorDefinition] = {
    # =========================================================================
    # LIGHT ARMOR
    # =========================================================================
    "padded_armor": ArmorDefinition(
        armor_id="padded_armor",
        name="Padded Armor",
        armor_type="light",
        ac_bonus=1,
        max_dex_bonus=8,
        armor_check_penalty=0,
        arcane_spell_failure=5,
        weight_lb=10.0,
    ),
    "leather_armor": ArmorDefinition(
        armor_id="leather_armor",
        name="Leather Armor",
        armor_type="light",
        ac_bonus=2,
        max_dex_bonus=6,
        armor_check_penalty=0,
        arcane_spell_failure=10,
        weight_lb=15.0,
    ),
    "studded_leather": ArmorDefinition(
        armor_id="studded_leather",
        name="Studded Leather",
        armor_type="light",
        ac_bonus=3,
        max_dex_bonus=5,
        armor_check_penalty=-1,
        arcane_spell_failure=15,
        weight_lb=20.0,
    ),
    "chain_shirt": ArmorDefinition(
        armor_id="chain_shirt",
        name="Chain Shirt",
        armor_type="light",
        ac_bonus=4,
        max_dex_bonus=4,
        armor_check_penalty=-2,
        arcane_spell_failure=20,
        weight_lb=25.0,
    ),

    # =========================================================================
    # MEDIUM ARMOR
    # =========================================================================
    "hide_armor": ArmorDefinition(
        armor_id="hide_armor",
        name="Hide Armor",
        armor_type="medium",
        ac_bonus=3,
        max_dex_bonus=4,
        armor_check_penalty=-3,
        arcane_spell_failure=20,
        weight_lb=25.0,
    ),
    "scale_mail": ArmorDefinition(
        armor_id="scale_mail",
        name="Scale Mail",
        armor_type="medium",
        ac_bonus=4,
        max_dex_bonus=3,
        armor_check_penalty=-4,
        arcane_spell_failure=25,
        weight_lb=30.0,
    ),
    "chainmail": ArmorDefinition(
        armor_id="chainmail",
        name="Chainmail",
        armor_type="medium",
        ac_bonus=5,
        max_dex_bonus=2,
        armor_check_penalty=-5,
        arcane_spell_failure=30,
        weight_lb=40.0,
    ),
    "breastplate": ArmorDefinition(
        armor_id="breastplate",
        name="Breastplate",
        armor_type="medium",
        ac_bonus=5,
        max_dex_bonus=3,
        armor_check_penalty=-4,
        arcane_spell_failure=25,
        weight_lb=30.0,
    ),

    # =========================================================================
    # HEAVY ARMOR
    # =========================================================================
    "splint_mail": ArmorDefinition(
        armor_id="splint_mail",
        name="Splint Mail",
        armor_type="heavy",
        ac_bonus=6,
        max_dex_bonus=0,
        armor_check_penalty=-7,
        arcane_spell_failure=40,
        weight_lb=45.0,
    ),
    "banded_mail": ArmorDefinition(
        armor_id="banded_mail",
        name="Banded Mail",
        armor_type="heavy",
        ac_bonus=6,
        max_dex_bonus=1,
        armor_check_penalty=-6,
        arcane_spell_failure=35,
        weight_lb=35.0,
    ),
    "half_plate": ArmorDefinition(
        armor_id="half_plate",
        name="Half-Plate",
        armor_type="heavy",
        ac_bonus=7,
        max_dex_bonus=0,
        armor_check_penalty=-7,
        arcane_spell_failure=40,
        weight_lb=50.0,
    ),
    "full_plate": ArmorDefinition(
        armor_id="full_plate",
        name="Full Plate",
        armor_type="heavy",
        ac_bonus=8,
        max_dex_bonus=1,
        armor_check_penalty=-6,
        arcane_spell_failure=35,
        weight_lb=50.0,
    ),

    # =========================================================================
    # SHIELDS
    # =========================================================================
    "buckler": ArmorDefinition(
        armor_id="buckler",
        name="Buckler",
        armor_type="shield",
        ac_bonus=1,
        max_dex_bonus=99,  # No limit
        armor_check_penalty=-1,
        arcane_spell_failure=5,
        weight_lb=5.0,
    ),
    "light_wooden_shield": ArmorDefinition(
        armor_id="light_wooden_shield",
        name="Light Wooden Shield",
        armor_type="shield",
        ac_bonus=1,
        max_dex_bonus=99,
        armor_check_penalty=-1,
        arcane_spell_failure=5,
        weight_lb=5.0,
    ),
    "light_steel_shield": ArmorDefinition(
        armor_id="light_steel_shield",
        name="Light Steel Shield",
        armor_type="shield",
        ac_bonus=1,
        max_dex_bonus=99,
        armor_check_penalty=-1,
        arcane_spell_failure=5,
        weight_lb=6.0,
    ),
    "heavy_wooden_shield": ArmorDefinition(
        armor_id="heavy_wooden_shield",
        name="Heavy Wooden Shield",
        armor_type="shield",
        ac_bonus=2,
        max_dex_bonus=99,
        armor_check_penalty=-2,
        arcane_spell_failure=15,
        weight_lb=10.0,
    ),
    "heavy_steel_shield": ArmorDefinition(
        armor_id="heavy_steel_shield",
        name="Heavy Steel Shield",
        armor_type="shield",
        ac_bonus=2,
        max_dex_bonus=99,
        armor_check_penalty=-2,
        arcane_spell_failure=15,
        weight_lb=15.0,
    ),
    "tower_shield": ArmorDefinition(
        armor_id="tower_shield",
        name="Tower Shield",
        armor_type="shield",
        ac_bonus=4,
        max_dex_bonus=2,
        armor_check_penalty=-10,
        arcane_spell_failure=50,
        weight_lb=45.0,
    ),
}


# ==============================================================================
# WEAPON REGISTRY — PHB pp.116-122
# ==============================================================================
#
# Spot-check table (PHB p.116-118):
# | Weapon         | Dmg(M) | Crit    | Dmg Type   | Cat     |
# |----------------|--------|---------|------------|---------|
# | Dagger         | 1d4    | 19-20/x2| P or S     | simple  |
# | Quarterstaff   | 1d6    | x2      | B          | simple  |
# | Longsword      | 1d8    | 19-20/x2| S          | martial |
# | Greataxe       | 1d12   | x3      | S          | martial |
# | Rapier         | 1d6    | 18-20/x2| P          | martial |
# | Shortbow       | 1d6    | x3      | P          | martial |
# | Longbow        | 1d8    | x3      | P          | martial |

WEAPON_REGISTRY: Dict[str, WeaponDefinition] = {
    # =========================================================================
    # SIMPLE WEAPONS — LIGHT
    # =========================================================================
    "dagger": WeaponDefinition(
        weapon_id="dagger",
        name="Dagger",
        damage_dice="1d4",
        damage_dice_small="1d3",
        crit_range=19,
        crit_mult=2,
        damage_type="piercing",
        weight_lb=1.0,
        weapon_category="simple",
        weapon_type="light",
    ),
    "punching_dagger": WeaponDefinition(
        weapon_id="punching_dagger",
        name="Punching Dagger",
        damage_dice="1d4",
        damage_dice_small="1d3",
        crit_range=20,
        crit_mult=3,
        damage_type="piercing",
        weight_lb=1.0,
        weapon_category="simple",
        weapon_type="light",
    ),
    "spiked_gauntlet": WeaponDefinition(
        weapon_id="spiked_gauntlet",
        name="Spiked Gauntlet",
        damage_dice="1d4",
        damage_dice_small="1d3",
        crit_range=20,
        crit_mult=2,
        damage_type="piercing",
        weight_lb=1.0,
        weapon_category="simple",
        weapon_type="light",
    ),
    "light_mace": WeaponDefinition(
        weapon_id="light_mace",
        name="Light Mace",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=20,
        crit_mult=2,
        damage_type="bludgeoning",
        weight_lb=4.0,
        weapon_category="simple",
        weapon_type="light",
    ),
    "sickle": WeaponDefinition(
        weapon_id="sickle",
        name="Sickle",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=20,
        crit_mult=2,
        damage_type="slashing",
        weight_lb=2.0,
        weapon_category="simple",
        weapon_type="light",
    ),

    # =========================================================================
    # SIMPLE WEAPONS — ONE-HANDED
    # =========================================================================
    "club": WeaponDefinition(
        weapon_id="club",
        name="Club",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=20,
        crit_mult=2,
        damage_type="bludgeoning",
        weight_lb=3.0,
        weapon_category="simple",
        weapon_type="one-handed",
    ),
    "heavy_mace": WeaponDefinition(
        weapon_id="heavy_mace",
        name="Heavy Mace",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=2,
        damage_type="bludgeoning",
        weight_lb=8.0,
        weapon_category="simple",
        weapon_type="one-handed",
    ),
    "morningstar": WeaponDefinition(
        weapon_id="morningstar",
        name="Morningstar",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=2,
        damage_type="bludgeoning",
        weight_lb=6.0,
        weapon_category="simple",
        weapon_type="one-handed",
    ),
    "shortspear": WeaponDefinition(
        weapon_id="shortspear",
        name="Shortspear",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=20,
        crit_mult=2,
        damage_type="piercing",
        weight_lb=3.0,
        weapon_category="simple",
        weapon_type="one-handed",
    ),

    # =========================================================================
    # SIMPLE WEAPONS — TWO-HANDED
    # =========================================================================
    "quarterstaff": WeaponDefinition(
        weapon_id="quarterstaff",
        name="Quarterstaff",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=20,
        crit_mult=2,
        damage_type="bludgeoning",
        weight_lb=4.0,
        weapon_category="simple",
        weapon_type="two-handed",
    ),
    "spear": WeaponDefinition(
        weapon_id="spear",
        name="Spear",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=3,
        damage_type="piercing",
        weight_lb=6.0,
        weapon_category="simple",
        weapon_type="two-handed",
    ),

    # =========================================================================
    # SIMPLE WEAPONS — RANGED
    # =========================================================================
    "light_crossbow": WeaponDefinition(
        weapon_id="light_crossbow",
        name="Light Crossbow",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=19,
        crit_mult=2,
        damage_type="piercing",
        weight_lb=4.0,
        weapon_category="simple",
        weapon_type="ranged",
    ),
    "heavy_crossbow": WeaponDefinition(
        weapon_id="heavy_crossbow",
        name="Heavy Crossbow",
        damage_dice="1d10",
        damage_dice_small="1d8",
        crit_range=19,
        crit_mult=2,
        damage_type="piercing",
        weight_lb=8.0,
        weapon_category="simple",
        weapon_type="ranged",
    ),
    "dart": WeaponDefinition(
        weapon_id="dart",
        name="Dart",
        damage_dice="1d4",
        damage_dice_small="1d3",
        crit_range=20,
        crit_mult=2,
        damage_type="piercing",
        weight_lb=0.5,
        weapon_category="simple",
        weapon_type="ranged",
    ),
    "sling": WeaponDefinition(
        weapon_id="sling",
        name="Sling",
        damage_dice="1d4",
        damage_dice_small="1d3",
        crit_range=20,
        crit_mult=2,
        damage_type="bludgeoning",
        weight_lb=0.0,
        weapon_category="simple",
        weapon_type="ranged",
    ),

    # =========================================================================
    # MARTIAL WEAPONS — LIGHT
    # =========================================================================
    "handaxe": WeaponDefinition(
        weapon_id="handaxe",
        name="Handaxe",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=20,
        crit_mult=3,
        damage_type="slashing",
        weight_lb=3.0,
        weapon_category="martial",
        weapon_type="light",
    ),
    "kukri": WeaponDefinition(
        weapon_id="kukri",
        name="Kukri",
        damage_dice="1d4",
        damage_dice_small="1d3",
        crit_range=18,
        crit_mult=2,
        damage_type="slashing",
        weight_lb=2.0,
        weapon_category="martial",
        weapon_type="light",
    ),
    "short_sword": WeaponDefinition(
        weapon_id="short_sword",
        name="Short Sword",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=19,
        crit_mult=2,
        damage_type="piercing",
        weight_lb=2.0,
        weapon_category="martial",
        weapon_type="light",
    ),

    # =========================================================================
    # MARTIAL WEAPONS — ONE-HANDED
    # =========================================================================
    "battleaxe": WeaponDefinition(
        weapon_id="battleaxe",
        name="Battleaxe",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=3,
        damage_type="slashing",
        weight_lb=6.0,
        weapon_category="martial",
        weapon_type="one-handed",
    ),
    "flail": WeaponDefinition(
        weapon_id="flail",
        name="Flail",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=2,
        damage_type="bludgeoning",
        weight_lb=5.0,
        weapon_category="martial",
        weapon_type="one-handed",
    ),
    "longsword": WeaponDefinition(
        weapon_id="longsword",
        name="Longsword",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=19,
        crit_mult=2,
        damage_type="slashing",
        weight_lb=4.0,
        weapon_category="martial",
        weapon_type="one-handed",
    ),
    "rapier": WeaponDefinition(
        weapon_id="rapier",
        name="Rapier",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=18,
        crit_mult=2,
        damage_type="piercing",
        weight_lb=2.0,
        weapon_category="martial",
        weapon_type="one-handed",
    ),
    "scimitar": WeaponDefinition(
        weapon_id="scimitar",
        name="Scimitar",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=18,
        crit_mult=2,
        damage_type="slashing",
        weight_lb=4.0,
        weapon_category="martial",
        weapon_type="one-handed",
    ),
    "trident": WeaponDefinition(
        weapon_id="trident",
        name="Trident",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=2,
        damage_type="piercing",
        weight_lb=4.0,
        weapon_category="martial",
        weapon_type="one-handed",
    ),
    "warhammer": WeaponDefinition(
        weapon_id="warhammer",
        name="Warhammer",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=3,
        damage_type="bludgeoning",
        weight_lb=5.0,
        weapon_category="martial",
        weapon_type="one-handed",
    ),

    # =========================================================================
    # MARTIAL WEAPONS — TWO-HANDED
    # =========================================================================
    "falchion": WeaponDefinition(
        weapon_id="falchion",
        name="Falchion",
        damage_dice="2d4",
        damage_dice_small="1d6",
        crit_range=18,
        crit_mult=2,
        damage_type="slashing",
        weight_lb=8.0,
        weapon_category="martial",
        weapon_type="two-handed",
    ),
    "glaive": WeaponDefinition(
        weapon_id="glaive",
        name="Glaive",
        damage_dice="1d10",
        damage_dice_small="1d8",
        crit_range=20,
        crit_mult=3,
        damage_type="slashing",
        weight_lb=10.0,
        weapon_category="martial",
        weapon_type="two-handed",
    ),
    "greataxe": WeaponDefinition(
        weapon_id="greataxe",
        name="Greataxe",
        damage_dice="1d12",
        damage_dice_small="1d10",
        crit_range=20,
        crit_mult=3,
        damage_type="slashing",
        weight_lb=12.0,
        weapon_category="martial",
        weapon_type="two-handed",
    ),
    "greatclub": WeaponDefinition(
        weapon_id="greatclub",
        name="Greatclub",
        damage_dice="1d10",
        damage_dice_small="1d8",
        crit_range=20,
        crit_mult=2,
        damage_type="bludgeoning",
        weight_lb=8.0,
        weapon_category="martial",
        weapon_type="two-handed",
    ),
    "greatsword": WeaponDefinition(
        weapon_id="greatsword",
        name="Greatsword",
        damage_dice="2d6",
        damage_dice_small="1d10",
        crit_range=19,
        crit_mult=2,
        damage_type="slashing",
        weight_lb=8.0,
        weapon_category="martial",
        weapon_type="two-handed",
    ),
    "guisarme": WeaponDefinition(
        weapon_id="guisarme",
        name="Guisarme",
        damage_dice="2d4",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=3,
        damage_type="slashing",
        weight_lb=12.0,
        weapon_category="martial",
        weapon_type="two-handed",
    ),
    "halberd": WeaponDefinition(
        weapon_id="halberd",
        name="Halberd",
        damage_dice="1d10",
        damage_dice_small="1d8",
        crit_range=20,
        crit_mult=3,
        damage_type="piercing",
        weight_lb=12.0,
        weapon_category="martial",
        weapon_type="two-handed",
    ),
    "lance": WeaponDefinition(
        weapon_id="lance",
        name="Lance",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=3,
        damage_type="piercing",
        weight_lb=10.0,
        weapon_category="martial",
        weapon_type="two-handed",
    ),
    "ranseur": WeaponDefinition(
        weapon_id="ranseur",
        name="Ranseur",
        damage_dice="2d4",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=3,
        damage_type="piercing",
        weight_lb=12.0,
        weapon_category="martial",
        weapon_type="two-handed",
    ),

    # =========================================================================
    # MARTIAL WEAPONS — RANGED
    # =========================================================================
    "shortbow": WeaponDefinition(
        weapon_id="shortbow",
        name="Shortbow",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=20,
        crit_mult=3,
        damage_type="piercing",
        weight_lb=2.0,
        weapon_category="martial",
        weapon_type="ranged",
    ),
    "longbow": WeaponDefinition(
        weapon_id="longbow",
        name="Longbow",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=3,
        damage_type="piercing",
        weight_lb=3.0,
        weapon_category="martial",
        weapon_type="ranged",
    ),
    "composite_shortbow": WeaponDefinition(
        weapon_id="composite_shortbow",
        name="Composite Shortbow",
        damage_dice="1d6",
        damage_dice_small="1d4",
        crit_range=20,
        crit_mult=3,
        damage_type="piercing",
        weight_lb=2.0,
        weapon_category="martial",
        weapon_type="ranged",
    ),
    "composite_longbow": WeaponDefinition(
        weapon_id="composite_longbow",
        name="Composite Longbow",
        damage_dice="1d8",
        damage_dice_small="1d6",
        crit_range=20,
        crit_mult=3,
        damage_type="piercing",
        weight_lb=3.0,
        weapon_category="martial",
        weapon_type="ranged",
    ),
}
