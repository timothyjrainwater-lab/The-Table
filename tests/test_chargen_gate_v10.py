"""Gate V10 — Animal Companion Generation.

WO-CHARGEN-COMPANION-001

Tests that build_animal_companion() correctly generates combat-ready entity
dicts for druid/ranger companions scaled per PHB Table 3-4.

PHB references:
- Druid companion: PHB p.36-37 (Table 3-4)
- Ranger companion: PHB p.47
"""

import pytest
from aidm.chargen.builder import build_character
from aidm.chargen.companions import build_animal_companion, COMPANION_PROGRESSION
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers — build parent entities
# ---------------------------------------------------------------------------

def _druid(level: int):
    return build_character(
        "human", "druid", level=level,
        ability_overrides={"str": 10, "dex": 10, "con": 12, "int": 10, "wis": 14, "cha": 10},
    )


def _ranger(level: int):
    return build_character(
        "human", "ranger", level=level,
        ability_overrides={"str": 14, "dex": 14, "con": 12, "int": 10, "wis": 12, "cha": 10},
    )


def _druid_ranger(druid_lvl: int, ranger_lvl: int):
    return build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 12, "int": 10, "wis": 14, "cha": 10},
        class_mix={"druid": druid_lvl, "ranger": ranger_lvl},
    )


def _fighter():
    return build_character(
        "human", "fighter", level=5,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
    )


# ---------------------------------------------------------------------------
# V10-01: Druid 1 → wolf at effective level 1
# ---------------------------------------------------------------------------

def test_v10_01_druid_1_wolf_effective_level_1():
    """Druid 1 → wolf at effective level 1: base stats, 2 HD, natural AC 2."""
    druid = _druid(1)
    wolf = build_animal_companion(druid, "wolf")

    # Base wolf: STR 13, DEX 15, CON 15, 2 HD, natural AC +2
    assert wolf[EF.BASE_STATS]["str"] == 13  # no progression bonus at level 1
    assert wolf[EF.BASE_STATS]["dex"] == 15
    assert wolf[EF.BASE_STATS]["con"] == 15
    assert wolf[EF.LEVEL] == 2  # 2 base HD + 0 bonus = 2
    # AC = 10 + DEX mod(+2) + natural AC(2+0) = 14
    assert wolf[EF.AC] == 14


# ---------------------------------------------------------------------------
# V10-02: Druid 4 → wolf at effective level 4
# ---------------------------------------------------------------------------

def test_v10_02_druid_4_wolf_effective_level_4():
    """Druid 4 → wolf at effective level 4: +2 HD, +2 natural AC, +1 Str/Dex, Multiattack feat."""
    druid = _druid(4)
    wolf = build_animal_companion(druid, "wolf")

    # At eff level 4: bonus_hd=2, nat_ac_adj=2, str_dex_adj=1
    assert wolf[EF.BASE_STATS]["str"] == 14  # 13 + 1
    assert wolf[EF.BASE_STATS]["dex"] == 16  # 15 + 1
    assert wolf[EF.LEVEL] == 4   # 2 base + 2 bonus HD
    # AC = 10 + dex_mod(+3) + natural_ac(2+2) = 17
    assert wolf[EF.AC] == 17
    # Multiattack feat added at eff level >= 4
    assert "multiattack" in wolf[EF.FEATS]


# ---------------------------------------------------------------------------
# V10-03: Druid 7 → wolf at effective level 7
# ---------------------------------------------------------------------------

def test_v10_03_druid_7_wolf_effective_level_7():
    """Druid 7 → wolf at effective level 7: +4 HD, +4 nat AC, +2 Str/Dex."""
    druid = _druid(7)
    wolf = build_animal_companion(druid, "wolf")

    # At eff level 7: bonus_hd=4, nat_ac_adj=4, str_dex_adj=2
    assert wolf[EF.BASE_STATS]["str"] == 15  # 13 + 2
    assert wolf[EF.BASE_STATS]["dex"] == 17  # 15 + 2
    assert wolf[EF.LEVEL] == 6   # 2 + 4


# ---------------------------------------------------------------------------
# V10-04: Ranger 4 → wolf at effective level 1 (4 - 3 = 1)
# ---------------------------------------------------------------------------

def test_v10_04_ranger_4_wolf_effective_level_1():
    """Ranger 4 → wolf companion at effective level 1 (ranger 4 − 3 = 1)."""
    ranger = _ranger(4)
    wolf = build_animal_companion(ranger, "wolf")

    # Same as druid 1: eff level 1, no bonuses
    assert wolf[EF.BASE_STATS]["str"] == 13
    assert wolf[EF.LEVEL] == 2   # 2 base HD, no bonus
    assert "multiattack" not in wolf[EF.FEATS]


# ---------------------------------------------------------------------------
# V10-05: Ranger 7 → wolf at effective level 4 (7 - 3 = 4)
# ---------------------------------------------------------------------------

def test_v10_05_ranger_7_wolf_effective_level_4():
    """Ranger 7 → wolf at effective level 4 (7 − 3 = 4)."""
    ranger = _ranger(7)
    wolf = build_animal_companion(ranger, "wolf")

    # eff level 4: same as druid 4
    assert wolf[EF.BASE_STATS]["str"] == 14  # 13 + 1
    assert wolf[EF.LEVEL] == 4
    assert "multiattack" in wolf[EF.FEATS]


# ---------------------------------------------------------------------------
# V10-06: Druid 2 / Ranger 4 multiclass → effective level 3 (2 + max(0, 4-3) = 3)
# ---------------------------------------------------------------------------

def test_v10_06_druid_2_ranger_4_effective_level_3():
    """Druid 2 / Ranger 4 → effective companion level = 2 + 1 = 3."""
    parent = _druid_ranger(2, 4)
    wolf = build_animal_companion(parent, "wolf")

    # eff level 3 → progression row at level 1 (highest ≤ 3)
    # bonus_hd=0, nat_ac_adj=0, str_dex_adj=0
    assert wolf[EF.BASE_STATS]["str"] == 13  # no bonus at eff 3
    assert wolf[EF.LEVEL] == 2
    assert "multiattack" not in wolf[EF.FEATS]


# ---------------------------------------------------------------------------
# V10-07: Ranger 3 raises ValueError (no companion yet, 3-3=0)
# ---------------------------------------------------------------------------

def test_v10_07_ranger_3_raises_value_error():
    """Ranger 3 → effective level 0 → ValueError (no companion yet)."""
    ranger = _ranger(3)
    with pytest.raises(ValueError, match="no qualifying companion class"):
        build_animal_companion(ranger, "wolf")


# ---------------------------------------------------------------------------
# V10-08: Fighter entity raises ValueError (not a qualifying class)
# ---------------------------------------------------------------------------

def test_v10_08_fighter_raises_value_error():
    """Fighter entity raises ValueError (no druid or ranger levels)."""
    fighter = _fighter()
    with pytest.raises(ValueError, match="no qualifying companion class"):
        build_animal_companion(fighter, "wolf")


# ---------------------------------------------------------------------------
# V10-09: Riding dog companion — correct base stats and attack
# ---------------------------------------------------------------------------

def test_v10_09_riding_dog_base_stats():
    """Riding dog companion: correct base stats and attack field."""
    druid = _druid(1)
    dog = build_animal_companion(druid, "riding_dog")

    assert dog[EF.BASE_STATS]["str"] == 13
    assert dog[EF.BASE_STATS]["dex"] == 13
    assert dog[EF.WEAPON]["name"] == "bite"
    assert dog[EF.WEAPON]["damage_dice"] == "1d6"


# ---------------------------------------------------------------------------
# V10-10: Eagle companion — small size, fly speed, correct stats
# ---------------------------------------------------------------------------

def test_v10_10_eagle_companion():
    """Eagle companion: small size, fly speed recorded, correct stats."""
    druid = _druid(1)
    eagle = build_animal_companion(druid, "eagle")

    assert eagle[EF.SIZE_CATEGORY] == "small"
    assert "speed_fly" in eagle
    assert eagle["speed_fly"] == 80
    assert eagle[EF.BASE_STATS]["dex"] == 15
    assert eagle[EF.WEAPON]["name"] == "talons"


# ---------------------------------------------------------------------------
# V10-11: Light horse companion — large size, correct HD and natural AC
# ---------------------------------------------------------------------------

def test_v10_11_light_horse_companion():
    """Light horse companion: large size, correct HD and natural AC."""
    druid = _druid(1)
    horse = build_animal_companion(druid, "light_horse")

    assert horse[EF.SIZE_CATEGORY] == "large"
    assert horse[EF.LEVEL] == 3   # base 3 HD, no bonus at eff level 1


# ---------------------------------------------------------------------------
# V10-12: Viper snake — small size, natural AC 4, poison in special
# ---------------------------------------------------------------------------

def test_v10_12_viper_snake_companion():
    """Viper snake: small size, natural AC 4, poison in special field."""
    druid = _druid(1)
    snake = build_animal_companion(druid, "viper_snake")

    assert snake[EF.SIZE_CATEGORY] == "small"
    # AC = 10 + dex_mod(+3) + natural_ac(4) = 17
    assert snake[EF.AC] == 17
    assert "poison" in snake["special"]


# ---------------------------------------------------------------------------
# V10-13: Unknown companion type raises ValueError
# ---------------------------------------------------------------------------

def test_v10_13_unknown_companion_type_raises():
    """Unknown companion type raises ValueError."""
    druid = _druid(1)
    with pytest.raises(ValueError, match="Unknown companion type"):
        build_animal_companion(druid, "dragon")


# ---------------------------------------------------------------------------
# V10-14: Companion ENTITY_ID includes parent entity ID
# ---------------------------------------------------------------------------

def test_v10_14_companion_entity_id_includes_parent():
    """Companion ENTITY_ID includes parent entity ID."""
    druid = _druid(1)
    wolf = build_animal_companion(druid, "wolf")

    parent_id = druid[EF.ENTITY_ID]
    assert parent_id in wolf[EF.ENTITY_ID]
    assert wolf[EF.ENTITY_ID].startswith("companion_wolf_")


# ---------------------------------------------------------------------------
# V10-15: Companion TEAM matches parent TEAM
# ---------------------------------------------------------------------------

def test_v10_15_companion_team_matches_parent():
    """Companion TEAM matches parent entity's TEAM."""
    druid = _druid(1)
    wolf = build_animal_companion(druid, "wolf")

    assert wolf[EF.TEAM] == druid[EF.TEAM]


# ---------------------------------------------------------------------------
# V10-16: Companion has no SPELL_SLOTS field
# ---------------------------------------------------------------------------

def test_v10_16_companion_has_no_spell_slots():
    """Animal companion has no SPELL_SLOTS field."""
    druid = _druid(1)
    wolf = build_animal_companion(druid, "wolf")

    assert EF.SPELL_SLOTS not in wolf


# ---------------------------------------------------------------------------
# V10-17: Companion has no INVENTORY field
# ---------------------------------------------------------------------------

def test_v10_17_companion_has_no_inventory():
    """Animal companion has no INVENTORY field (carries no gear)."""
    druid = _druid(1)
    wolf = build_animal_companion(druid, "wolf")

    assert EF.INVENTORY not in wolf


# ---------------------------------------------------------------------------
# V10-18: Wolf SAVE_FORT correct (good save, 2 HD, CON=15 mod=+2)
# ---------------------------------------------------------------------------

def test_v10_18_wolf_save_fort_correct():
    """Wolf companion SAVE_FORT correct (good save, 2 HD, CON mod +2)."""
    from aidm.schemas.leveling import GOOD_SAVE_PROGRESSION
    druid = _druid(1)
    wolf = build_animal_companion(druid, "wolf")

    # 2 HD, good fort: GOOD_SAVE_PROGRESSION[1] + CON mod(+2)
    expected = GOOD_SAVE_PROGRESSION[1] + 2  # CON=15 → mod=+2
    assert wolf[EF.SAVE_FORT] == expected


# ---------------------------------------------------------------------------
# V10-19: Wolf BAB correct (3/4 progression at 2 HD)
# ---------------------------------------------------------------------------

def test_v10_19_wolf_bab_correct():
    """Wolf companion BAB correct (3/4 progression at 2 HD = BAB 1)."""
    from aidm.schemas.leveling import BAB_PROGRESSION
    druid = _druid(1)
    wolf = build_animal_companion(druid, "wolf")

    # threequarters BAB at HD 2: index 1 → BAB_PROGRESSION["threequarters"][1]
    expected = BAB_PROGRESSION["threequarters"][1]
    assert wolf[EF.BAB] == expected


# ---------------------------------------------------------------------------
# V10-20: Wolf AC includes natural AC bonus + DEX mod
# ---------------------------------------------------------------------------

def test_v10_20_wolf_ac_correct():
    """Wolf companion AC = 10 + DEX mod + natural AC bonus (at eff level 1)."""
    druid = _druid(1)
    wolf = build_animal_companion(druid, "wolf")

    # DEX=15 → mod=+2; natural AC=2 at eff level 1
    # AC = 10 + 2 + 2 = 14
    assert wolf[EF.AC] == 14


# ---------------------------------------------------------------------------
# V10-21: Wolf WEAPON field present with correct schema
# ---------------------------------------------------------------------------

def test_v10_21_wolf_weapon_field():
    """Wolf companion WEAPON field: bite 1d6, 20/x2."""
    druid = _druid(1)
    wolf = build_animal_companion(druid, "wolf")

    weapon = wolf[EF.WEAPON]
    assert weapon is not None
    assert weapon["name"] == "bite"
    assert weapon["damage_dice"] == "1d6"
    assert weapon["critical_range"] == 20
    assert weapon["critical_multiplier"] == 2


# ---------------------------------------------------------------------------
# V10-22: Wolf SKILL_RANKS present (listen, spot, hide)
# ---------------------------------------------------------------------------

def test_v10_22_wolf_skill_ranks_present():
    """Wolf companion SKILL_RANKS present with listen, spot, hide."""
    druid = _druid(1)
    wolf = build_animal_companion(druid, "wolf")

    ranks = wolf[EF.SKILL_RANKS]
    assert "listen" in ranks
    assert "spot" in ranks
    assert "hide" in ranks


# ---------------------------------------------------------------------------
# V10-23: Druid 10 wolf: +6 HD total, progression at level 10
# ---------------------------------------------------------------------------

def test_v10_23_druid_10_wolf_progression():
    """Druid 10 wolf: +6 HD, +6 AC adj, +3 Str/Dex, 4 bonus tricks."""
    druid = _druid(10)
    wolf = build_animal_companion(druid, "wolf")

    # eff level 10: bonus_hd=6, nat_ac_adj=6, str_dex_adj=3, bonus_tricks=4
    assert wolf[EF.LEVEL] == 8        # 2 base + 6 bonus
    assert wolf[EF.BASE_STATS]["str"] == 16   # 13 + 3
    assert wolf[EF.BASE_STATS]["dex"] == 18   # 15 + 3
    assert wolf["bonus_tricks"] == 4


# ---------------------------------------------------------------------------
# V10-24: FEATS includes Multiattack at effective level >= 4
# ---------------------------------------------------------------------------

def test_v10_24_feats_multiattack_at_effective_4():
    """Companion FEATS includes Multiattack at effective companion level >= 4."""
    druid_4 = _druid(4)
    druid_1 = _druid(1)

    wolf_4 = build_animal_companion(druid_4, "wolf")
    wolf_1 = build_animal_companion(druid_1, "wolf")

    assert "multiattack" in wolf_4[EF.FEATS]
    assert "multiattack" not in wolf_1[EF.FEATS]


# ---------------------------------------------------------------------------
# V10-25: V6/V8 regression — build_character() unchanged (no new params)
# ---------------------------------------------------------------------------

def test_v10_25_build_character_unchanged():
    """build_character() still works correctly — no accidental changes from V10."""
    # Spot-check a few standard builds
    wizard = build_character("elf", "wizard", level=3,
                             ability_overrides={"str": 8, "dex": 12, "con": 10, "int": 16, "wis": 10, "cha": 10})
    assert wizard[EF.RACE] == "elf"
    assert wizard[EF.LEVEL] == 3

    fighter = build_character("dwarf", "fighter", level=5,
                               ability_overrides={"str": 16, "dex": 10, "con": 14, "int": 10, "wis": 10, "cha": 8})
    assert fighter[EF.RACE] == "dwarf"
    assert fighter[EF.LEVEL] == 5

    multiclass = build_character("human", "fighter",
                                  ability_overrides={"str": 14, "dex": 12, "con": 12, "int": 14, "wis": 10, "cha": 10},
                                  class_mix={"fighter": 3, "wizard": 3})
    assert multiclass[EF.CLASS_LEVELS] == {"fighter": 3, "wizard": 3}
