"""Animal companion generation for D&D 3.5e.

WO-CHARGEN-COMPANION-001

Provides build_animal_companion() which returns a combat-engine-ready entity dict
for druid and ranger animal companions.

PHB references:
- Druid companion: PHB p.36-37 (Table 3-4)
- Ranger companion: PHB p.47
- Companion stat blocks: PHB Appendix / MM
"""

from typing import Any, Dict

from aidm.schemas.entity_fields import EF
from aidm.schemas.leveling import BAB_PROGRESSION, GOOD_SAVE_PROGRESSION, POOR_SAVE_PROGRESSION
from aidm.chargen.ability_scores import ability_modifier


# ---------------------------------------------------------------------------
# Base companion stat blocks (PHB Appendix / MM entries)
# ---------------------------------------------------------------------------

BASE_COMPANION_STATS: Dict[str, Dict] = {
    "wolf": {
        "size": "medium", "speed": 50, "hd": 2, "hd_die": 8,
        "str": 13, "dex": 15, "con": 15, "int": 2, "wis": 12, "cha": 6,
        "natural_ac_bonus": 2,
        "fort_good": True, "ref_good": True, "will_good": False,
        "bab_progression": "threequarters",
        "attack": {"name": "bite", "damage_dice": "1d6", "crit_range": 20, "crit_mult": 2},
        "special": ["trip"],
        "class_skills": ["hide", "listen", "move_silently", "spot", "survival", "swim"],
        "skill_ranks": {"listen": 2, "spot": 2, "hide": 1, "move_silently": 1},
    },
    "riding_dog": {
        "size": "medium", "speed": 40, "hd": 2, "hd_die": 8,
        "str": 13, "dex": 13, "con": 15, "int": 2, "wis": 12, "cha": 6,
        "natural_ac_bonus": 1,
        "fort_good": True, "ref_good": True, "will_good": False,
        "bab_progression": "threequarters",
        "attack": {"name": "bite", "damage_dice": "1d6", "crit_range": 20, "crit_mult": 2},
        "special": [],
        "class_skills": ["jump", "listen", "spot", "survival", "swim"],
        "skill_ranks": {"listen": 2, "spot": 2},
    },
    "eagle": {
        "size": "small", "speed": 10, "speed_fly": 80, "hd": 1, "hd_die": 8,
        "str": 10, "dex": 15, "con": 12, "int": 2, "wis": 14, "cha": 6,
        "natural_ac_bonus": 1,
        "fort_good": True, "ref_good": True, "will_good": False,
        "bab_progression": "threequarters",
        "attack": {"name": "talons", "damage_dice": "1d4", "crit_range": 20, "crit_mult": 2},
        "special": [],
        "class_skills": ["listen", "spot"],
        "skill_ranks": {"listen": 2, "spot": 6},
    },
    "light_horse": {
        "size": "large", "speed": 60, "hd": 3, "hd_die": 8,
        "str": 14, "dex": 13, "con": 15, "int": 2, "wis": 12, "cha": 6,
        "natural_ac_bonus": 1,
        "fort_good": True, "ref_good": True, "will_good": False,
        "bab_progression": "threequarters",
        "attack": {"name": "2 hooves", "damage_dice": "1d4", "crit_range": 20, "crit_mult": 2},
        "special": [],
        "class_skills": ["listen", "spot"],
        "skill_ranks": {"listen": 2, "spot": 2},
    },
    "viper_snake": {
        "size": "small", "speed": 20, "speed_climb": 20, "speed_swim": 20,
        "hd": 1, "hd_die": 8,
        "str": 6, "dex": 17, "con": 11, "int": 1, "wis": 12, "cha": 2,
        "natural_ac_bonus": 4,
        "fort_good": True, "ref_good": True, "will_good": False,
        "bab_progression": "threequarters",
        "attack": {"name": "bite", "damage_dice": "1d2", "crit_range": 20, "crit_mult": 2},
        "special": ["poison"],
        "class_skills": ["balance", "climb", "hide", "listen", "spot", "swim"],
        "skill_ranks": {"balance": 4, "climb": 4, "hide": 4, "listen": 2, "spot": 2, "swim": 4},
    },
}

# ---------------------------------------------------------------------------
# PHB Table 3-4 (p.36) — companion progression by effective druid level
# ---------------------------------------------------------------------------

COMPANION_PROGRESSION: Dict[int, Dict] = {
    1:  {"bonus_hd": 0, "natural_ac_adj": 0,  "str_dex_adj": 0, "bonus_tricks": 1},
    4:  {"bonus_hd": 2, "natural_ac_adj": 2,  "str_dex_adj": 1, "bonus_tricks": 2},
    7:  {"bonus_hd": 4, "natural_ac_adj": 4,  "str_dex_adj": 2, "bonus_tricks": 3},
    10: {"bonus_hd": 6, "natural_ac_adj": 6,  "str_dex_adj": 3, "bonus_tricks": 4},
    13: {"bonus_hd": 8, "natural_ac_adj": 8,  "str_dex_adj": 4, "bonus_tricks": 5},
    16: {"bonus_hd": 10, "natural_ac_adj": 10, "str_dex_adj": 5, "bonus_tricks": 6},
    19: {"bonus_hd": 12, "natural_ac_adj": 12, "str_dex_adj": 6, "bonus_tricks": 7},
}


def _effective_companion_level(entity: Dict[str, Any]) -> int:
    """Compute effective companion druid level per PHB p.36-37.

    Effective level = druid_level + max(0, ranger_level - 3).
    Raises ValueError if the entity has no qualifying class.
    """
    class_levels: Dict[str, int] = entity.get(EF.CLASS_LEVELS, {})
    druid_lvl = class_levels.get("druid", 0)
    ranger_lvl = class_levels.get("ranger", 0)
    effective = druid_lvl + max(0, ranger_lvl - 3)
    if effective < 1:
        raise ValueError(
            f"Entity has no qualifying companion class (druid or ranger level 4+). "
            f"CLASS_LEVELS={class_levels}"
        )
    return effective


def _companion_progression_row(effective_level: int) -> Dict:
    """Return the highest applicable progression row for effective_level."""
    applicable = [lvl for lvl in sorted(COMPANION_PROGRESSION.keys()) if lvl <= effective_level]
    return COMPANION_PROGRESSION[applicable[-1]]


def _calc_bab(bab_progression: str, total_hd: int) -> int:
    """Calculate BAB from BAB progression type and total HD."""
    idx = min(total_hd - 1, 19)
    return BAB_PROGRESSION[bab_progression][idx]


def _calc_save(good: bool, total_hd: int, mod: int) -> int:
    """Calculate saving throw for creature with given HD."""
    idx = min(total_hd - 1, 19)
    base = GOOD_SAVE_PROGRESSION[idx] if good else POOR_SAVE_PROGRESSION[idx]
    return base + mod


def build_animal_companion(
    parent_entity: Dict[str, Any],
    companion_type: str,
) -> Dict[str, Any]:
    """Build a combat-ready animal companion entity dict.

    Args:
        parent_entity: The druid or ranger entity dict (output of build_character()).
        companion_type: One of "wolf", "riding_dog", "eagle", "light_horse", "viper_snake".

    Returns:
        Complete entity dict ready for WorldState insertion.

    Raises:
        ValueError: If companion_type is unknown, or entity has no qualifying class.
    """
    if companion_type not in BASE_COMPANION_STATS:
        raise ValueError(
            f"Unknown companion type '{companion_type}'. "
            f"Available: {list(BASE_COMPANION_STATS.keys())}"
        )

    effective_level = _effective_companion_level(parent_entity)
    prog = _companion_progression_row(effective_level)
    base = BASE_COMPANION_STATS[companion_type]

    # --- Apply progression adjustments ---
    bonus_hd = prog["bonus_hd"]
    nat_ac_adj = prog["natural_ac_adj"]
    str_dex_adj = prog["str_dex_adj"]
    bonus_tricks = prog["bonus_tricks"]

    total_hd = base["hd"] + bonus_hd

    # Ability scores with progression bonuses (Str and Dex each get str_dex_adj)
    final_str = base["str"] + str_dex_adj
    final_dex = base["dex"] + str_dex_adj
    final_con = base["con"]
    final_int = base["int"]
    final_wis = base["wis"]
    final_cha = base["cha"]

    ability_scores = {
        "str": final_str,
        "dex": final_dex,
        "con": final_con,
        "int": final_int,
        "wis": final_wis,
        "cha": final_cha,
    }
    mods = {ab: ability_modifier(score) for ab, score in ability_scores.items()}

    # --- HP: max HD die at HD 1, average thereafter ---
    hd_die = base["hd_die"]
    hp = max(1, hd_die + mods["con"])  # first HD: max
    for _ in range(total_hd - 1):
        avg_roll = round(hd_die / 2.0 + 0.5)
        hp += max(1, avg_roll + mods["con"])

    # --- BAB ---
    bab = _calc_bab(base["bab_progression"], total_hd)

    # --- AC: 10 + dex_mod + natural_ac ---
    natural_ac = base["natural_ac_bonus"] + nat_ac_adj
    ac = 10 + mods["dex"] + natural_ac

    # --- Saves ---
    save_fort = _calc_save(base["fort_good"], total_hd, mods["con"])
    save_ref = _calc_save(base["ref_good"], total_hd, mods["dex"])
    save_will = _calc_save(base["will_good"], total_hd, mods["wis"])

    # --- Feats ---
    feats = []
    if effective_level >= 4:
        feats.append("multiattack")

    # --- Weapon (primary attack) ---
    atk = base["attack"]
    weapon = {
        "name": atk["name"],
        "damage_dice": atk["damage_dice"],
        "damage_bonus": mods["str"],
        "damage_type": "physical",
        "critical_multiplier": atk["crit_mult"],
        "critical_range": atk["crit_range"],
        "weapon_type": "natural",
        "is_two_handed": False,
        "grip": "natural",
        "range_increment": 0,
    }

    # --- Entity ID ---
    parent_id = parent_entity.get(EF.ENTITY_ID, "unknown")
    entity_id = f"companion_{companion_type}_{parent_id}"

    # --- Team matches parent ---
    team = parent_entity.get(EF.TEAM, "player")

    # --- Assemble entity dict ---
    entity: Dict[str, Any] = {
        EF.ENTITY_ID: entity_id,
        EF.RACE: "animal",
        EF.TEAM: team,

        # Ability scores
        EF.BASE_STATS: dict(ability_scores),
        EF.STR_MOD: mods["str"],
        EF.DEX_MOD: mods["dex"],
        EF.CON_MOD: mods["con"],
        EF.INT_MOD: mods["int"],
        EF.WIS_MOD: mods["wis"],
        EF.CHA_MOD: mods["cha"],

        # Hit points
        EF.HP_MAX: hp,
        EF.HP_CURRENT: hp,

        # Combat
        EF.BAB: bab,
        EF.ATTACK_BONUS: bab + mods["str"],
        EF.AC: ac,
        EF.DEFEATED: False,

        # Saves
        EF.SAVE_FORT: save_fort,
        EF.SAVE_REF: save_ref,
        EF.SAVE_WILL: save_will,

        # Level & class (companions have no class levels)
        EF.LEVEL: total_hd,
        EF.CLASS_LEVELS: {},
        EF.XP: 0,

        # Feats & skills
        EF.FEATS: feats,
        EF.FEAT_SLOTS: 0,
        EF.SKILL_RANKS: dict(base["skill_ranks"]),
        EF.CLASS_SKILLS: list(base["class_skills"]),

        # Size & speed
        EF.SIZE_CATEGORY: base["size"],
        EF.BASE_SPEED: base["speed"],

        # Combat status
        EF.CONDITIONS: [],
        EF.POSITION: (0, 0),

        # Weapon
        EF.WEAPON: weapon,

        # Bonus tricks (informational — trick system deferred to future WO)
        "bonus_tricks": bonus_tricks,

        # Special abilities (informational)
        "special": list(base["special"]),
    }

    # Optional fly/climb/swim speeds
    if "speed_fly" in base:
        entity["speed_fly"] = base["speed_fly"]
    if "speed_climb" in base:
        entity["speed_climb"] = base["speed_climb"]
    if "speed_swim" in base:
        entity["speed_swim"] = base["speed_swim"]

    return entity
