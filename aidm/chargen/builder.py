"""Character builder for D&D 3.5e — assembles a complete entity dict.

WO-CHARGEN-BUILDER-001 / WO-CHARGEN-MULTICLASS-001 / WO-CHARGEN-EQUIPMENT-001

Pulls together ability scores, racial mods, class progression, feats,
skills, and spellcasting into a single entity dict ready for the combat
engine or any other consumer.

Usage:
    from aidm.chargen.builder import build_character

    entity = build_character("human", "fighter", level=1)
    entity = build_character("elf", "wizard", level=10, ability_method="standard")

    # Multiclass (WO-CHARGEN-MULTICLASS-001)
    entity = build_character("human", "fighter", class_mix={"fighter": 3, "wizard": 2})
"""

import random
from typing import Dict, List, Optional, Any, Tuple
import json
import os

from aidm.schemas.entity_fields import EF
from aidm.schemas.leveling import (
    CLASS_PROGRESSIONS,
    BAB_PROGRESSION,
    GOOD_SAVE_PROGRESSION,
    POOR_SAVE_PROGRESSION,
)
from aidm.chargen.ability_scores import (
    ABILITY_NAMES,
    ability_modifier,
    generate_ability_array,
)
from aidm.data.races import RACE_REGISTRY, get_race, apply_racial_mods, apply_racial_trait_fields
from aidm.schemas.feats import FEAT_REGISTRY, get_feat_definition
from aidm.schemas.skills import SKILLS
from aidm.chargen.spellcasting import (
    SPELLS_PER_DAY,
    CASTING_ABILITY,
    SPONTANEOUS_CASTERS,
    get_spell_slots,
    get_spells_known_count,
    get_class_spell_list,
    is_caster,
)


# ---------------------------------------------------------------------------
# Equipment catalog helpers (WO-CHARGEN-EQUIPMENT-001) — read-only
# Canonical runtime source for equipment data (armor, weapons, gear).
# aidm/data/equipment_definitions.py was deleted 2026-02-27 (no runtime consumer — Thunder Option B).
# ---------------------------------------------------------------------------

_CATALOG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "equipment_catalog.json"
)
_CATALOG_CACHE: Optional[Dict] = None


def _load_catalog() -> Dict:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is None:
        with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
            _CATALOG_CACHE = json.load(f)
    return _CATALOG_CACHE


def _catalog_weapon(item_id: str) -> Optional[Dict]:
    return _load_catalog().get("weapons", {}).get(item_id)


def _catalog_armor(item_id: str) -> Optional[Dict]:
    return _load_catalog().get("armor", {}).get(item_id)


def _catalog_gear(item_id: str) -> Optional[Dict]:
    cat = _load_catalog()
    return (
        cat.get("adventuring_gear", {}).get(item_id)
        or cat.get("containers", {}).get(item_id)
    )


# Per-class starting kit (PHB Table 5-1 averages)
_CLASS_KIT: Dict[str, Dict] = {
    "barbarian": {"gold_gp": 100.0, "weapon_id": "greataxe",    "armor_id": "hide",       "is_caster": False},
    "bard":      {"gold_gp": 125.0, "weapon_id": "rapier",       "armor_id": "leather",    "is_caster": True},
    "cleric":    {"gold_gp": 125.0, "weapon_id": "mace_heavy",   "armor_id": "scale_mail", "is_caster": True},
    "druid":     {"gold_gp": 50.0,  "weapon_id": "quarterstaff", "armor_id": "hide",       "is_caster": True,  "no_metal_armor": True},
    "fighter":   {"gold_gp": 175.0, "weapon_id": "longsword",    "armor_id": "chainmail",  "is_caster": False},
    "monk":      {"gold_gp": 25.0,  "weapon_id": None,           "armor_id": None,         "is_caster": False, "wis_to_ac": True},
    "paladin":   {"gold_gp": 175.0, "weapon_id": "longsword",    "armor_id": "chainmail",  "is_caster": True},
    "ranger":    {"gold_gp": 150.0, "weapon_id": "longsword",    "armor_id": "leather",    "is_caster": True},
    "rogue":     {"gold_gp": 125.0, "weapon_id": "short_sword",  "armor_id": "leather",    "is_caster": False},
    "sorcerer":  {"gold_gp": 75.0,  "weapon_id": "quarterstaff", "armor_id": None,         "is_caster": True},
    "wizard":    {"gold_gp": 75.0,  "weapon_id": "quarterstaff", "armor_id": None,         "is_caster": True},
}

_STANDARD_GEAR_ORDER = [
    ("backpack", 1),
    ("bedroll", 1),
    ("waterskin", 1),
    ("torch", 3),
    ("rations_trail_1day", 5),
]

# PHB Table 9-1: carrying capacity (light / medium / heavy lbs) by STR score
_STR_CARRY: Dict[int, tuple] = {
    1:  (3.33,   6.67,   10),
    2:  (6.67,   13.33,  20),
    3:  (10,     20,     30),
    4:  (13.33,  26.67,  40),
    5:  (16.67,  33.33,  50),
    6:  (20,     40,     60),
    7:  (23.33,  46.67,  70),
    8:  (26.67,  53.33,  80),
    9:  (30,     60,     90),
    10: (33.33,  66.67,  100),
    11: (38.33,  76.67,  115),
    12: (43.33,  86.67,  130),
    13: (50,     100,    150),
    14: (58.33,  116.67, 175),
    15: (66.67,  133.33, 200),
    16: (76.67,  153.33, 230),
    17: (86.67,  173.33, 260),
    18: (100,    200,    300),
    19: (116.67, 233.33, 350),
    20: (133.33, 266.67, 400),
}


def _encumbrance_tier(total_weight: float, str_score: int) -> str:
    """Return 'light', 'medium', 'heavy', or 'overloaded'."""
    str_score = max(1, min(str_score, 20))
    light, medium, heavy = _STR_CARRY.get(str_score, _STR_CARRY[10])
    if total_weight <= light:
        return "light"
    if total_weight <= medium:
        return "medium"
    if total_weight <= heavy:
        return "heavy"
    return "overloaded"


def _assign_starting_equipment(
    entity: Dict[str, Any],
    class_name: str,
    str_score: int,
    str_mod: int,
    wis_mod: int,
    dex_mod: int,
    starting_equipment: Optional[Dict[str, int]] = None,
) -> None:
    """Populate INVENTORY, WEAPON, AC, ARMOR_CHECK_PENALTY, ENCUMBRANCE_LOAD.

    Mutates entity in-place.  WO-CHARGEN-EQUIPMENT-001 §3.3.

    Args:
        entity: The entity dict (mutated in-place).
        class_name: Class name (must be in _CLASS_KIT).
        str_score: Raw STR score (for encumbrance thresholds).
        str_mod: STR modifier (weapon damage bonus).
        wis_mod: WIS modifier (monk AC bonus).
        dex_mod: DEX modifier (AC calculation).
        starting_equipment: Override {item_id: qty}. Bypasses default kit.
    """
    kit = _CLASS_KIT.get(class_name, {})
    inventory: List[Dict] = []
    total_weight = 0.0

    # -- Override path: explicit loadout bypasses all defaults --
    if starting_equipment is not None:
        for item_id, qty in starting_equipment.items():
            inventory.append({"item_id": item_id, "quantity": qty})
            entry = (
                _catalog_weapon(item_id)
                or _catalog_armor(item_id)
                or _catalog_gear(item_id)
            )
            if entry:
                total_weight += entry.get("weight_lb", 0.0) * qty
        entity[EF.INVENTORY] = inventory
        entity[EF.ARMOR_CHECK_PENALTY] = 0
        entity[EF.ENCUMBRANCE_LOAD] = _encumbrance_tier(total_weight, str_score)
        return

    # -- Default kit path --
    gold = kit.get("gold_gp", 0.0)

    # Weapon
    weapon_id = kit.get("weapon_id")
    weapon_dict = None
    if weapon_id:
        w = _catalog_weapon(weapon_id)
        if w and gold >= w.get("cost_gp", 0):
            gold -= w.get("cost_gp", 0)
            inventory.append({"item_id": weapon_id, "quantity": 1})
            total_weight += w.get("weight_lb", 0.0)
            is_two_handed = w.get("weapon_type") == "two-handed"
            weapon_dict = {
                "name": w["name"],
                "damage_dice": w["damage_dice"],
                "damage_bonus": str_mod,
                "damage_type": w["damage_type"],
                "critical_multiplier": w.get("critical_multiplier", 2),
                "critical_range": w.get("critical_range", 20),
                "weapon_type": w.get("weapon_type", "one-handed"),
                "is_two_handed": is_two_handed,
                "grip": "two-handed" if is_two_handed else "one-handed",
                "range_increment": w.get("range_increment_ft", 0),
            }

    entity[EF.WEAPON] = weapon_dict

    # Armor
    armor_id = kit.get("armor_id")
    armor_ac_bonus = 0
    armor_check_penalty = 0
    armor_type_str = "none"  # WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001: "none"|"light"|"medium"|"heavy"
    effective_dex = dex_mod

    if armor_id:
        a = _catalog_armor(armor_id)
        if a and gold >= a.get("cost_gp", 0):
            gold -= a.get("cost_gp", 0)
            inventory.append({"item_id": armor_id, "quantity": 1})
            total_weight += a.get("weight_lb", 0.0)
            armor_ac_bonus = a.get("ac_bonus", 0)
            armor_check_penalty = a.get("armor_check_penalty", 0)
            armor_type_str = a.get("armor_type", "none")  # WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001
            max_dex = a.get("max_dex_bonus")
            if max_dex is not None and max_dex < 99:
                effective_dex = min(dex_mod, max_dex)

    # AC (§3.5): 10 + effective_dex + armor_bonus
    # WO-ENGINE-MONK-WIS-AC-001: WIS bonus tracked separately; applied at runtime by attack_resolver
    ac = 10 + effective_dex + armor_ac_bonus
    entity[EF.AC] = ac
    entity[EF.ARMOR_CHECK_PENALTY] = armor_check_penalty

    # WO-ENGINE-MONK-WIS-AC-001: Track WIS AC bonus separately for runtime computation (PHB p.41)
    # Branch B: WIS is NOT pre-baked into EF.AC — attack_resolver adds MONK_WIS_AC_BONUS at runtime.
    if kit.get("wis_to_ac"):
        entity[EF.MONK_WIS_AC_BONUS] = wis_mod
    else:
        entity[EF.MONK_WIS_AC_BONUS] = 0

    # WO-ENGINE-MONK-WIS-AC-001 / WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001: Armor tracking fields
    entity[EF.ARMOR_AC_BONUS] = armor_ac_bonus  # 0 = unarmored
    entity[EF.ARMOR_TYPE] = armor_type_str  # "none"|"light"|"medium"|"heavy"

    # Standard adventuring gear
    for item_id, qty in _STANDARD_GEAR_ORDER:
        entry = _catalog_gear(item_id)
        if entry is None:
            continue
        cost = entry.get("cost_gp", 0.0) * qty
        if gold >= cost:
            gold -= cost
            inventory.append({"item_id": item_id, "quantity": qty})
            total_weight += entry.get("weight_lb", 0.0) * qty

    # Spell component pouch for casters
    if kit.get("is_caster"):
        scp = _catalog_gear("spell_component_pouch")
        if scp is not None and gold >= scp.get("cost_gp", 0.0):
            gold -= scp.get("cost_gp", 0.0)
            inventory.append({"item_id": "spell_component_pouch", "quantity": 1})
            total_weight += scp.get("weight_lb", 0.0)

    entity[EF.INVENTORY] = inventory
    entity[EF.ENCUMBRANCE_LOAD] = _encumbrance_tier(total_weight, str_score)


def _roll_hit_die(die_size: int) -> int:
    """Roll a single hit die."""
    return random.randint(1, die_size)


def _calculate_hp(
    hit_die: int,
    level: int,
    con_mod: int,
) -> int:
    """Calculate HP for a character.

    Level 1: max hit die + CON mod (minimum 1 per level).
    Levels 2+: roll hit die + CON mod each level (minimum 1 per level).

    Args:
        hit_die: Hit die size (4, 6, 8, 10, 12)
        level: Character level (1-20)
        con_mod: Constitution modifier

    Returns:
        Total HP
    """
    # Level 1: max hit die
    hp = max(1, hit_die + con_mod)

    # Levels 2+
    for _ in range(level - 1):
        roll = _roll_hit_die(hit_die)
        hp += max(1, roll + con_mod)

    return hp


def _calculate_bab(bab_type: str, level: int) -> int:
    """Get BAB for a given class type and level.

    Args:
        bab_type: "full", "threequarters", or "half"
        level: Class level (1-20)

    Returns:
        Base Attack Bonus
    """
    return BAB_PROGRESSION[bab_type][level - 1]


def _calculate_saves(
    good_saves: tuple,
    level: int,
    modifiers: Dict[str, int],
) -> Dict[str, int]:
    """Calculate saving throw bonuses.

    Args:
        good_saves: Tuple of save types with good progression ("fort", "ref", "will")
        level: Character level (1-20)
        modifiers: Dict with con_mod, dex_mod, wis_mod

    Returns:
        Dict mapping save type to total bonus
    """
    save_ability_map = {
        "fort": modifiers.get("con_mod", 0),
        "ref": modifiers.get("dex_mod", 0),
        "will": modifiers.get("wis_mod", 0),
    }

    saves = {}
    for save_type in ("fort", "ref", "will"):
        if save_type in good_saves:
            base = GOOD_SAVE_PROGRESSION[level - 1]
        else:
            base = POOR_SAVE_PROGRESSION[level - 1]
        saves[save_type] = base + save_ability_map[save_type]

    return saves


def _calculate_skill_points(
    class_name: str,
    level: int,
    int_mod: int,
    race_id: str,
) -> int:
    """Calculate total skill points available.

    Level 1: (base + INT mod + racial bonus) * 4
    Levels 2+: (base + INT mod + racial bonus) per level

    Minimum 1 skill point per level.

    Args:
        class_name: Class name
        level: Character level
        int_mod: Intelligence modifier
        race_id: Race ID (for human bonus skill points)

    Returns:
        Total skill points to allocate
    """
    progression = CLASS_PROGRESSIONS[class_name]
    race = get_race(race_id)
    base = progression.skill_points_per_level
    per_level = max(1, base + int_mod + race.bonus_skill_points_per_level)

    # Level 1 gets x4
    total = per_level * 4

    # Levels 2+
    total += per_level * (level - 1)

    return total


def _feat_slots_at_level(level: int, race_id: str) -> int:
    """Calculate total feat slots available at a given level.

    Every character gets 1 feat at level 1, then 1 more at levels 3, 6, 9, 12, 15, 18.
    Humans get +1 bonus feat at level 1.
    Fighters get bonus feats at 1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20.

    Note: Fighter bonus feats are NOT counted here — they're class-specific.
    This returns general feat slots only.

    Args:
        level: Character level (1-20)
        race_id: Race ID

    Returns:
        Total general feat slots
    """
    race = get_race(race_id)
    # 1 at level 1, +1 at every 3rd level
    slots = 1 + (level // 3)
    # Human bonus feat
    slots += race.bonus_feats
    return slots


def _resolve_multiclass_stats(
    class_mix: Dict[str, int],
    modifiers: Dict[str, int],
    race_id: str,
) -> Dict[str, Any]:
    """Compute BAB, saves, HP, skill points, feat count, and class skills for a multiclass character.

    PHB p.57:
    - BAB: highest BAB value among all classes (not summed)
    - Saves: each save independently takes the best progression across classes
    - HP: sum of each class's HD contributions (max at overall level 1, average thereafter)
    - Skill points: sum each class's skill points per level (L1 gets ×4 per class)
    - Class skills: union of all classes
    - Feats: based on total character level, not per-class

    Args:
        class_mix: Dict mapping class name to level, e.g. {"fighter": 3, "wizard": 2}
        modifiers: Dict with str, dex, con, int, wis, cha modifier values
        race_id: Race ID (for human bonus skill points)

    Returns:
        Dict with keys: bab, saves, hp, skill_points, class_skills, feat_slots
    """
    total_level = sum(class_mix.values())

    # --- BAB: best single class BAB (PHB p.57) ---
    bab = max(
        BAB_PROGRESSION[CLASS_PROGRESSIONS[cls].bab_type][lvl - 1]
        for cls, lvl in class_mix.items()
    )

    # --- Saves: each save takes best progression independently ---
    def _save_val(cls: str, lvl: int, save_type: str) -> int:
        prog = CLASS_PROGRESSIONS[cls]
        if save_type in prog.good_saves:
            return GOOD_SAVE_PROGRESSION[lvl - 1]
        return POOR_SAVE_PROGRESSION[lvl - 1]

    fort_base = max(_save_val(cls, lvl, "fort") for cls, lvl in class_mix.items())
    ref_base  = max(_save_val(cls, lvl, "ref")  for cls, lvl in class_mix.items())
    will_base = max(_save_val(cls, lvl, "will") for cls, lvl in class_mix.items())

    saves = {
        "fort": fort_base + modifiers["con"],
        "ref":  ref_base  + modifiers["dex"],
        "will": will_base + modifiers["wis"],
    }

    # --- HP: max HD at character level 1, average thereafter ---
    con_mod = modifiers["con"]
    total_hp = 0
    first_level = True
    for cls, lvls in class_mix.items():
        hd = CLASS_PROGRESSIONS[cls].hit_die
        for _ in range(lvls):
            if first_level:
                total_hp += max(1, hd + con_mod)
                first_level = False
            else:
                avg_roll = round(hd / 2.0 + 0.5)  # e.g. d10 → 6, d4 → 3
                total_hp += max(1, avg_roll + con_mod)

    # --- Skill points: each class contributes its own per level ---
    int_mod = modifiers["int"]
    race = get_race(race_id)
    total_skill_points = 0
    for cls, lvls in class_mix.items():
        base = CLASS_PROGRESSIONS[cls].skill_points_per_level
        per_level = max(1, base + int_mod + race.bonus_skill_points_per_level)
        # Level 1 of this class gets ×4; remaining levels get ×1
        total_skill_points += per_level * 4 + per_level * (lvls - 1)

    # Human racial bonus: +1 skill point per total character level
    if race_id == "human":
        total_skill_points += total_level

    # --- Class skills: union of all classes ---
    class_skills: List[str] = []
    seen = set()
    for cls in class_mix:
        for skill in CLASS_PROGRESSIONS[cls].class_skills:
            if skill not in seen:
                class_skills.append(skill)
                seen.add(skill)

    # --- Feats: based on total character level ---
    feat_slots = _feat_slots_at_level(total_level, race_id)

    return {
        "bab": bab,
        "saves": saves,
        "hp": total_hp,
        "skill_points": total_skill_points,
        "class_skills": class_skills,
        "feat_slots": feat_slots,
    }


def _resolve_single_caster_spells(
    cls: str,
    lvl: int,
    casting_score: int,
    spell_choices: Optional[List[str]],
) -> Tuple[Dict, Dict, Dict]:
    """Resolve spell slots, spells_known, spells_prepared for one caster class.

    Returns:
        Tuple of (spell_slots, spells_known, spells_prepared)
    """
    spell_slots = get_spell_slots(cls, lvl, casting_score)
    spells_known: Dict = {}
    spells_prepared: Dict = {}

    if cls in SPONTANEOUS_CASTERS:
        known_counts = get_spells_known_count(cls, lvl) or {}
        if spell_choices:
            remaining = list(spell_choices)
            for spell_level in sorted(known_counts.keys()):
                count = known_counts[spell_level]
                available = get_class_spell_list(cls, spell_level)
                level_spells = []
                for sid in remaining[:]:
                    if sid in available and len(level_spells) < count:
                        level_spells.append(sid)
                        remaining.remove(sid)
                if level_spells:
                    spells_known[spell_level] = level_spells
        else:
            spells_known = {sl: [] for sl in known_counts}
    else:
        if spell_choices:
            from aidm.data.spell_definitions import SPELL_REGISTRY
            for sid in spell_choices:
                if sid in SPELL_REGISTRY:
                    spell = SPELL_REGISTRY[sid]
                    slvl = spell.level
                    if slvl not in spells_prepared:
                        spells_prepared[slvl] = []
                    spells_prepared[slvl].append(sid)

    return spell_slots, spells_known, spells_prepared


def _merge_spellcasting(
    class_mix: Dict[str, int],
    final_scores: Dict[str, int],
    spell_choices: Optional[List[str]],
    spell_choices_2: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Resolve spellcasting for a multiclass character.

    WO-CHARGEN-DUALCASTER-001: Dual-caster support.
    - 0 casters: returns empty dict
    - 1 caster: single-caster flat format (SPELL_SLOTS, CASTER_LEVEL, CASTER_CLASS)
    - 2 casters: alphabetical primary/secondary split with _2 suffix fields for secondary
    - 3+ casters: raises ValueError

    Args:
        class_mix: Dict mapping class name to level
        final_scores: Final ability scores after racial mods
        spell_choices: Optional list of spell IDs for primary caster
        spell_choices_2: Optional list of spell IDs for secondary caster

    Returns:
        Dict of entity fields to merge (may be empty)
    """
    caster_classes = sorted([cls for cls in class_mix if is_caster(cls)])

    if len(caster_classes) == 0:
        return {}

    if len(caster_classes) == 1:
        cls = caster_classes[0]
        lvl = class_mix[cls]
        casting_stat = CASTING_ABILITY[cls]
        casting_score = final_scores[casting_stat]
        spell_slots, spells_known, spells_prepared = _resolve_single_caster_spells(
            cls, lvl, casting_score, spell_choices
        )
        return {
            EF.SPELL_SLOTS: spell_slots,
            EF.SPELL_SLOTS_MAX: dict(spell_slots),   # snapshot for rest recovery (WO-ENGINE-REST-001)
            EF.SPELLS_KNOWN: spells_known,
            EF.SPELLS_PREPARED: spells_prepared,
            EF.CASTER_LEVEL: lvl,
            EF.CASTER_CLASS: cls,
        }

    if len(caster_classes) > 2:
        raise ValueError("Only two caster classes supported in class_mix")

    # Dual-caster path: alphabetical order is deterministic
    primary, secondary = caster_classes[0], caster_classes[1]
    primary_lvl = class_mix[primary]
    secondary_lvl = class_mix[secondary]

    primary_casting_score = final_scores[CASTING_ABILITY[primary]]
    secondary_casting_score = final_scores[CASTING_ABILITY[secondary]]

    primary_slots, primary_known, primary_prepared = _resolve_single_caster_spells(
        primary, primary_lvl, primary_casting_score, spell_choices
    )
    secondary_slots, secondary_known, secondary_prepared = _resolve_single_caster_spells(
        secondary, secondary_lvl, secondary_casting_score, spell_choices_2
    )

    result: Dict[str, Any] = {
        EF.SPELL_SLOTS: primary_slots,
        EF.SPELL_SLOTS_MAX: dict(primary_slots),     # snapshot for rest recovery (WO-ENGINE-REST-001)
        EF.CASTER_LEVEL: primary_lvl,
        EF.CASTER_CLASS: primary,
        EF.SPELL_SLOTS_2: secondary_slots,
        EF.SPELL_SLOTS_MAX_2: dict(secondary_slots), # snapshot for rest recovery (WO-ENGINE-REST-001)
        EF.CASTER_LEVEL_2: secondary_lvl,
        EF.CASTER_CLASS_2: secondary,
    }

    # Primary caster spells (use top-level fields)
    if primary in SPONTANEOUS_CASTERS:
        result[EF.SPELLS_KNOWN] = primary_known
        result[EF.SPELLS_PREPARED] = {}
    else:
        result[EF.SPELLS_KNOWN] = {}
        result[EF.SPELLS_PREPARED] = primary_prepared

    # Secondary caster spells (use _2 suffix fields)
    if secondary in SPONTANEOUS_CASTERS:
        result[EF.SPELLS_KNOWN_2] = secondary_known
        result[EF.SPELLS_PREPARED_2] = {}
    else:
        result[EF.SPELLS_KNOWN_2] = {}
        result[EF.SPELLS_PREPARED_2] = secondary_prepared

    return result


# =============================================================================
# WO-ENGINE-SNEAK-ATTACK-AUTO-IMMUNE-001: Creature type immunity auto-set
# =============================================================================

# PHB p.50: Immune to sneak attack (no discernible anatomy or vital spots)
_SA_IMMUNE_TYPES = frozenset({"undead", "construct", "ooze", "plant", "elemental", "incorporeal"})
# PHB p.50 / DMG p.290: Also immune to critical hits
_CRIT_IMMUNE_TYPES = frozenset({"undead", "construct"})


def _apply_creature_type_immunities(entity: Dict[str, Any]) -> None:
    """Auto-set sneak attack / crit immunity from EF.CREATURE_TYPE.

    PHB p.50: undead, constructs, plants, oozes, and elementals are immune
    to sneak attack. Constructs and undead are also immune to critical hits.

    Uses the same field names read by sneak_attack.py:is_target_immune():
      - "creature_type" (= EF.CREATURE_TYPE)
      - "immune_to_sneak_attack"
      - "immune_to_critical_hits"

    Additive: does NOT overwrite an existing explicit True flag.
    """
    creature_type = entity.get(EF.CREATURE_TYPE, "")
    if not creature_type:
        return

    ct = creature_type.lower()

    # WO-ENGINE-SNEAK-ATTACK-AUTO-IMMUNE-001: SA immunity auto-set
    if ct in _SA_IMMUNE_TYPES:
        if not entity.get("immune_to_sneak_attack"):
            entity["immune_to_sneak_attack"] = True

    # WO-ENGINE-SNEAK-ATTACK-AUTO-IMMUNE-001: Crit immunity auto-set (undead + construct only)
    if ct in _CRIT_IMMUNE_TYPES:
        if not entity.get("immune_to_critical_hits"):
            entity["immune_to_critical_hits"] = True


def build_character(
    race: str,
    class_name: str,
    level: int = 1,
    ability_method: str = "standard",
    ability_overrides: Optional[Dict[str, int]] = None,
    feat_choices: Optional[List[str]] = None,
    skill_allocations: Optional[Dict[str, int]] = None,
    spell_choices: Optional[List[str]] = None,
    spell_choices_2: Optional[List[str]] = None,
    starting_equipment: Optional[Dict[str, int]] = None,
    use_rolled_gold: bool = False,
    class_mix: Optional[Dict[str, int]] = None,
    favored_class: Optional[str] = None,
    creature_type: str = "",
    domains: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a complete D&D 3.5e character entity dict.

    This is the capstone function that assembles all chargen subsystems
    into a single entity dict compatible with the combat engine.

    Args:
        race: Race ID (e.g., "human", "elf", "dwarf")
        class_name: Class name (e.g., "fighter", "wizard"). Ignored if class_mix provided.
        level: Character level (1-20). Default 1. Ignored if class_mix provided.
        ability_method: "4d6", "standard", or "point_buy". Default "standard".
        ability_overrides: Manual ability scores. If provided, ability_method is ignored.
        feat_choices: List of feat_ids to assign. If None, no feats assigned.
        skill_allocations: Dict of skill_id -> ranks. If None, no skills allocated.
        spell_choices: List of spell_ids for casters. If None, no spells assigned.
        spell_choices_2: List of spell_ids for second caster (dual-caster multiclass). If None, defaults from class list.
        starting_equipment: Dict of item_id -> quantity. Currently stored only.
        use_rolled_gold: If True, use rolled gold for starting equipment.
        class_mix: Multiclass dict, e.g. {"fighter": 3, "wizard": 2}. If provided,
            class_name and level are ignored.
        favored_class: Optional favored class name (PHB p.56). Stored informational only.
        domains: List of domain name strings for clerics/druids (PHB p.32). Max 2 for clerics.
            Default None → stored as []. E.g. ["sun", "fire"].

    Returns:
        Complete entity dict with all EF fields populated.

    Raises:
        KeyError: If race or class_name is invalid.
        ValueError: If level is out of range, total level > 20, unknown class in class_mix,
            or both class_mix and class_name+level are simultaneously meaningful.
    """
    # --- Multiclass path ---
    if class_mix is not None:
        return _build_multiclass_character(
            race=race,
            class_mix=class_mix,
            ability_method=ability_method,
            ability_overrides=ability_overrides,
            feat_choices=feat_choices,
            skill_allocations=skill_allocations,
            spell_choices=spell_choices,
            spell_choices_2=spell_choices_2,
            favored_class=favored_class,
        )

    # --- Single-class path (existing, unchanged) ---
    if race not in RACE_REGISTRY:
        raise KeyError(f"Unknown race: {race}. Available: {list(RACE_REGISTRY.keys())}")
    if class_name not in CLASS_PROGRESSIONS:
        raise KeyError(f"Unknown class: {class_name}. Available: {list(CLASS_PROGRESSIONS.keys())}")
    if level < 1 or level > 20:
        raise ValueError(f"Level must be 1-20, got {level}")

    race_def = get_race(race)
    class_prog = CLASS_PROGRESSIONS[class_name]

    # --- Step 1: Ability Scores ---
    if ability_overrides:
        base_scores = dict(ability_overrides)
    else:
        base_scores = generate_ability_array(ability_method)

    # --- Step 2: Apply racial mods ---
    final_scores = apply_racial_mods(base_scores, race)

    # --- Step 3: Calculate modifiers ---
    modifiers = {name: ability_modifier(final_scores[name]) for name in ABILITY_NAMES}

    # --- Step 4: Calculate HP ---
    hp = _calculate_hp(class_prog.hit_die, level, modifiers["con"])

    # --- Step 5: Calculate BAB ---
    bab = _calculate_bab(class_prog.bab_type, level)

    # --- Step 6: Calculate saves ---
    save_mods = {
        "con_mod": modifiers["con"],
        "dex_mod": modifiers["dex"],
        "wis_mod": modifiers["wis"],
    }
    saves = _calculate_saves(class_prog.good_saves, level, save_mods)

    # --- Step 7: Skill points & allocations ---
    total_skill_points = _calculate_skill_points(
        class_name, level, modifiers["int"], race,
    )
    skill_ranks = {}
    class_skills_list = list(class_prog.class_skills)

    if skill_allocations:
        max_rank = level + 3  # Max ranks for class skill
        max_cross = (level + 3) / 2  # Max ranks for cross-class
        for skill_id, ranks in skill_allocations.items():
            is_class_skill = skill_id in class_skills_list
            limit = max_rank if is_class_skill else max_cross
            actual_ranks = min(ranks, limit)
            skill_ranks[skill_id] = actual_ranks

    # --- Step 8: Feats ---
    # Canonical runtime source for feat data: feat keys stored directly in EF.FEATS list.
    # aidm/data/feat_definitions.py was deleted 2026-02-27 (no runtime consumer — Thunder Option B).
    feat_slot_count = _feat_slots_at_level(level, race)
    feats = []
    if feat_choices:
        feats = list(feat_choices[:feat_slot_count])

    # --- Step 9: Spellcasting ---
    spell_slots = {}
    spells_known = {}
    spells_prepared = {}
    caster_level = 0

    if is_caster(class_name):
        casting_stat = CASTING_ABILITY[class_name]
        casting_score = final_scores[casting_stat]
        caster_level = level

        spell_slots = get_spell_slots(class_name, level, casting_score)

        if class_name in SPONTANEOUS_CASTERS:
            known_counts = get_spells_known_count(class_name, level) or {}
            if spell_choices:
                # Distribute spell choices across levels
                remaining = list(spell_choices)
                for spell_level in sorted(known_counts.keys()):
                    count = known_counts[spell_level]
                    available = get_class_spell_list(class_name, spell_level)
                    level_spells = []
                    for sid in remaining[:]:
                        if sid in available and len(level_spells) < count:
                            level_spells.append(sid)
                            remaining.remove(sid)
                    if level_spells:
                        spells_known[spell_level] = level_spells
            else:
                spells_known = {lvl: [] for lvl in known_counts}
        else:
            # Prepared caster
            if spell_choices:
                from aidm.data.spell_definitions import SPELL_REGISTRY
                for sid in spell_choices:
                    if sid in SPELL_REGISTRY:
                        spell = SPELL_REGISTRY[sid]
                        slvl = spell.level
                        if slvl not in spells_prepared:
                            spells_prepared[slvl] = []
                        spells_prepared[slvl].append(sid)

    # --- Step 10: Assemble entity dict ---
    entity: Dict[str, Any] = {
        EF.ENTITY_ID: f"{race}_{class_name}_{level}",
        EF.RACE: race,
        EF.TEAM: "player",

        # Ability scores
        EF.BASE_STATS: dict(final_scores),
        EF.STR_MOD: modifiers["str"],
        EF.DEX_MOD: modifiers["dex"],
        EF.CON_MOD: modifiers["con"],
        EF.INT_MOD: modifiers["int"],
        EF.WIS_MOD: modifiers["wis"],
        EF.CHA_MOD: modifiers["cha"],

        # Hit points
        EF.HP_MAX: hp,
        EF.HP_CURRENT: hp,

        # Combat
        EF.BAB: bab,
        EF.ATTACK_BONUS: bab + modifiers["str"],  # Melee default
        EF.AC: 10 + modifiers["dex"],
        EF.DEFEATED: False,

        # Saves
        EF.SAVE_FORT: saves["fort"],
        EF.SAVE_REF: saves["ref"],
        EF.SAVE_WILL: saves["will"],

        # Level & class
        EF.LEVEL: level,
        EF.CLASS_LEVELS: {class_name: level},
        EF.XP: 0,

        # Feats
        EF.FEATS: feats,
        EF.FEAT_SLOTS: max(0, feat_slot_count - len(feats)),

        # Skills
        EF.SKILL_RANKS: skill_ranks,
        EF.CLASS_SKILLS: class_skills_list,

        # WO-ENGINE-CONCENTRATION-WRITE-001: Concentration bonus = ranks + CON_MOD (PHB p.66)
        EF.CONCENTRATION_BONUS: skill_ranks.get("concentration", 0) + modifiers["con"],

        # Size & Speed
        EF.SIZE_CATEGORY: race_def.size,
        EF.BASE_SPEED: race_def.base_speed,

        # Conditions
        EF.CONDITIONS: [],

        # Position
        EF.POSITION: (0, 0),
    }

    # Spellcasting fields (always present, empty for non-casters)
    entity[EF.SPELL_SLOTS] = spell_slots
    entity[EF.SPELL_SLOTS_MAX] = dict(spell_slots)  # snapshot for rest recovery (WO-ENGINE-REST-001)
    entity[EF.SPELLS_KNOWN] = spells_known
    entity[EF.SPELLS_PREPARED] = spells_prepared
    entity[EF.CASTER_LEVEL] = caster_level
    if is_caster(class_name):
        entity[EF.CASTER_CLASS] = class_name

    # --- Racial trait fields (WO-CHARGEN-RACIAL-001) ---
    apply_racial_trait_fields(entity, race)

    # --- Step 11: Equipment (WO-CHARGEN-EQUIPMENT-001) ---
    str_score = final_scores.get("str", 10)
    _assign_starting_equipment(
        entity=entity,
        class_name=class_name,
        str_score=str_score,
        str_mod=modifiers["str"],
        wis_mod=modifiers["wis"],
        dex_mod=modifiers["dex"],
        starting_equipment=starting_equipment,
    )

    # --- Step 12: Class feature pool initialization (FINDING-CHARGEN-POOL-INIT-001) ---
    # Pools that live-engine resolvers consume must be non-None at chargen.
    # class_levels dict for single-class is always {class_name: level}.
    _paladin_level = level if class_name == "paladin" else 0
    _bard_level = level if class_name == "bard" else 0
    _druid_level = level if class_name == "druid" else 0
    _cha_mod = modifiers["cha"]

    # Paladin: Smite Evil uses (PHB p.44 — 1 use at L1, +1 per 5 levels)
    if _paladin_level >= 1:
        smite_count = sum(
            1 for lvl, feats in _CLASS_FEATURES["paladin"].items()
            if lvl <= _paladin_level
            for feat in feats
            if feat.startswith("smite_evil_") and feat.endswith("_per_day")
        )
        entity[EF.SMITE_USES_REMAINING] = smite_count

    # Paladin: Lay on Hands pool (PHB p.44 — unlocks at L2; pool = paladin_level × cha_mod if cha_mod > 0 else 0)
    if _paladin_level >= 2:
        entity[EF.LAY_ON_HANDS_POOL] = _paladin_level * _cha_mod if _cha_mod > 0 else 0
        entity[EF.LAY_ON_HANDS_USED] = 0

    # Bard: Bardic Music uses remaining (PHB p.29 — bard_level + CHA mod per day, min 1)
    if _bard_level >= 1:
        entity[EF.BARDIC_MUSIC_USES_REMAINING] = max(1, _bard_level + _cha_mod)

    # Druid: Wild Shape uses remaining (PHB p.37, Table 3-14 — unlocks at L5; lookup table)
    if _druid_level >= 5:
        from aidm.core.wild_shape_resolver import _get_wild_shape_uses
        entity[EF.WILD_SHAPE_USES_REMAINING] = _get_wild_shape_uses(_druid_level)

    # WO-ENGINE-EVASION-001: Evasion and Improved Evasion boolean flags (PHB Rogue p.56, Monk p.41)
    _rogue_level = level if class_name == "rogue" else 0
    _monk_level = level if class_name == "monk" else 0
    _ranger_level = level if class_name == "ranger" else 0
    if _rogue_level >= 2 or _monk_level >= 2 or _ranger_level >= 9:
        entity[EF.EVASION] = True      # Rogue 2, Monk 2, Ranger 9 (PHB p.56, p.41, p.47)
    if _rogue_level >= 10 or _monk_level >= 9:
        entity[EF.IMPROVED_EVASION] = True  # Rogue 10, Monk 9 (PHB p.57, p.43)

    # WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001: Fast Movement bonus (PHB p.26)
    _barbarian_level = level if class_name == "barbarian" else 0
    entity[EF.FAST_MOVEMENT_BONUS] = 10 if _barbarian_level >= 1 else 0

    # WO-ENGINE-SNEAK-ATTACK-AUTO-IMMUNE-001: Creature type + immunity fields
    if creature_type:
        entity[EF.CREATURE_TYPE] = creature_type
    _apply_creature_type_immunities(entity)

    # WO-ENGINE-TOUGHNESS-001: Toughness feat +3 HP per instance (PHB p.101; stackable)
    _toughness_count = entity.get(EF.FEATS, []).count("toughness")
    if _toughness_count > 0:
        _toughness_hp = _toughness_count * 3
        entity[EF.HP_MAX] = entity.get(EF.HP_MAX, 0) + _toughness_hp
        entity[EF.HP_CURRENT] = entity.get(EF.HP_CURRENT, 0) + _toughness_hp

    # WO-ENGINE-BARBARIAN-DR-001: Barbarian DR/— (PHB p.26)
    # Scales: 7=1/—, 10=2/—, 13=3/—, 16=4/—, 19=5/—
    _barb_dr_table = [(19, 5), (16, 4), (13, 3), (10, 2), (7, 1)]
    for _threshold, _dr_value in _barb_dr_table:
        if _barbarian_level >= _threshold:
            _existing_dr = entity.get(EF.DAMAGE_REDUCTIONS, [])
            _existing_dash = next((d for d in _existing_dr if d.get("bypass") == "-"), None)
            if _existing_dash is None or _existing_dash["amount"] < _dr_value:
                entity[EF.DAMAGE_REDUCTIONS] = (
                    [d for d in _existing_dr if d.get("bypass") != "-"]
                    + [{"amount": _dr_value, "bypass": "-"}]
                )
            break

    # WO-ENGINE-EXTRA-TURNING-001: Turn Undead pool init + Extra Turning feat (PHB p.94)
    # Base uses = max(1, 3 + CHA mod) for cleric (L1+) and paladin (L4+).
    _cleric_level_et = level if class_name == "cleric" else 0
    _paladin_level_et = level if class_name == "paladin" else 0
    if _cleric_level_et >= 1 or _paladin_level_et >= 4:
        _turn_base = max(1, 3 + _cha_mod)
        _extra_turning_count = entity.get(EF.FEATS, []).count("extra_turning")
        _turn_max = _turn_base + 4 * _extra_turning_count
        entity[EF.TURN_UNDEAD_USES_MAX] = _turn_max
        entity[EF.TURN_UNDEAD_USES] = _turn_max

    # WO-ENGINE-DOMAIN-SYSTEM-001 (Batch V WO3): Cleric/druid domain selections (PHB p.32)
    entity[EF.DOMAINS] = list(domains) if domains else []

    # WO-ENGINE-MONK-UNARMED-PROGRESSION-001: Monk unarmed strike damage (PHB Table 3-10)
    _monk_level_mup = level if class_name == "monk" else 0
    _unarmed_table = [
        (20, "2d10"), (16, "2d8"), (12, "2d6"),
        (8, "1d10"), (4, "1d8"), (1, "1d6"),
    ]
    for _threshold, _dice in _unarmed_table:
        if _monk_level_mup >= _threshold:
            entity[EF.MONK_UNARMED_DICE] = _dice
            break

    return entity


def _build_multiclass_character(
    race: str,
    class_mix: Dict[str, int],
    ability_method: str = "standard",
    ability_overrides: Optional[Dict[str, int]] = None,
    feat_choices: Optional[List[str]] = None,
    skill_allocations: Optional[Dict[str, int]] = None,
    spell_choices: Optional[List[str]] = None,
    spell_choices_2: Optional[List[str]] = None,
    favored_class: Optional[str] = None,
) -> Dict[str, Any]:
    """Internal builder for multiclass characters. Called by build_character() when class_mix is set.

    Validates inputs, then delegates stat computation to _resolve_multiclass_stats()
    and spellcasting to _merge_spellcasting().
    """
    # --- Validate ---
    if race not in RACE_REGISTRY:
        raise KeyError(f"Unknown race: {race}. Available: {list(RACE_REGISTRY.keys())}")
    for cls in class_mix:
        if cls not in CLASS_PROGRESSIONS:
            raise KeyError(
                f"Unknown class in class_mix: {cls}. Available: {list(CLASS_PROGRESSIONS.keys())}"
            )
    total_level = sum(class_mix.values())
    if total_level < 1 or total_level > 20:
        raise ValueError(f"Total character level must be 1-20, got {total_level}")

    race_def = get_race(race)

    # --- Ability scores ---
    if ability_overrides:
        base_scores = dict(ability_overrides)
    else:
        base_scores = generate_ability_array(ability_method)
    final_scores = apply_racial_mods(base_scores, race)
    modifiers = {name: ability_modifier(final_scores[name]) for name in ABILITY_NAMES}

    # --- Multiclass stat resolution ---
    mc = _resolve_multiclass_stats(class_mix, modifiers, race)

    bab = mc["bab"]
    saves = mc["saves"]
    hp = mc["hp"]
    class_skills_list = mc["class_skills"]
    feat_slot_count = mc["feat_slots"]

    # --- Skill allocations ---
    skill_ranks = {}
    if skill_allocations:
        max_rank = total_level + 3
        max_cross = (total_level + 3) / 2
        for skill_id, ranks in skill_allocations.items():
            is_class_skill = skill_id in class_skills_list
            limit = max_rank if is_class_skill else max_cross
            skill_ranks[skill_id] = min(ranks, limit)

    # --- Feats ---
    feats = []
    if feat_choices:
        feats = list(feat_choices[:feat_slot_count])

    # --- Spellcasting ---
    spell_data = _merge_spellcasting(
        class_mix, final_scores, spell_choices, spell_choices_2,
    )

    # --- Entity ID: sorted class names for stability ---
    class_tag = "_".join(f"{c}{v}" for c, v in sorted(class_mix.items()))
    entity_id = f"{race}_{class_tag}"

    # --- Assemble entity dict ---
    entity: Dict[str, Any] = {
        EF.ENTITY_ID: entity_id,
        EF.RACE: race,
        EF.TEAM: "player",

        # Ability scores
        EF.BASE_STATS: dict(final_scores),
        EF.STR_MOD: modifiers["str"],
        EF.DEX_MOD: modifiers["dex"],
        EF.CON_MOD: modifiers["con"],
        EF.INT_MOD: modifiers["int"],
        EF.WIS_MOD: modifiers["wis"],
        EF.CHA_MOD: modifiers["cha"],

        # Hit points
        EF.HP_MAX: hp,
        EF.HP_CURRENT: hp,

        # Combat
        EF.BAB: bab,
        EF.ATTACK_BONUS: bab + modifiers["str"],
        EF.AC: 10 + modifiers["dex"],
        EF.DEFEATED: False,

        # Saves
        EF.SAVE_FORT: saves["fort"],
        EF.SAVE_REF: saves["ref"],
        EF.SAVE_WILL: saves["will"],

        # Level & class
        EF.LEVEL: total_level,
        EF.CLASS_LEVELS: dict(class_mix),
        EF.XP: 0,

        # Feats
        EF.FEATS: feats,
        EF.FEAT_SLOTS: max(0, feat_slot_count - len(feats)),

        # Skills
        EF.SKILL_RANKS: skill_ranks,
        EF.CLASS_SKILLS: class_skills_list,

        # WO-ENGINE-CONCENTRATION-WRITE-001: Concentration bonus = ranks + CON_MOD (PHB p.66)
        EF.CONCENTRATION_BONUS: skill_ranks.get("concentration", 0) + modifiers["con"],

        # Size & Speed
        EF.SIZE_CATEGORY: race_def.size,
        EF.BASE_SPEED: race_def.base_speed,

        # Conditions
        EF.CONDITIONS: [],

        # Position
        EF.POSITION: (0, 0),
    }

    # Spellcasting fields — merge all returned spell_data keys into entity
    # For non-casters: spell_data is empty; for single casters: flat fields;
    # for dual casters: primary flat + secondary _2 fields.
    if not spell_data:
        # No casters — populate empty flat fields for consistency
        entity[EF.SPELL_SLOTS] = {}
        entity[EF.SPELLS_KNOWN] = {}
        entity[EF.SPELLS_PREPARED] = {}
        entity[EF.CASTER_LEVEL] = 0
    else:
        entity.update(spell_data)

    # Favored class (informational, PHB p.56)
    if favored_class is not None:
        entity["favored_class"] = favored_class

    # Racial trait fields (WO-CHARGEN-RACIAL-001)
    apply_racial_trait_fields(entity, race)

    # --- Class feature pool initialization (FINDING-CHARGEN-POOL-INIT-001) ---
    _paladin_level = class_mix.get("paladin", 0)
    _bard_level = class_mix.get("bard", 0)
    _druid_level = class_mix.get("druid", 0)
    _cha_mod = modifiers["cha"]

    if _paladin_level >= 1:
        smite_count = sum(
            1 for lvl, feats in _CLASS_FEATURES["paladin"].items()
            if lvl <= _paladin_level
            for feat in feats
            if feat.startswith("smite_evil_") and feat.endswith("_per_day")
        )
        entity[EF.SMITE_USES_REMAINING] = smite_count

    if _paladin_level >= 2:
        entity[EF.LAY_ON_HANDS_POOL] = _paladin_level * _cha_mod if _cha_mod > 0 else 0
        entity[EF.LAY_ON_HANDS_USED] = 0

    if _bard_level >= 1:
        entity[EF.BARDIC_MUSIC_USES_REMAINING] = max(1, _bard_level + _cha_mod)

    if _druid_level >= 5:
        from aidm.core.wild_shape_resolver import _get_wild_shape_uses as _mc_ws_uses
        entity[EF.WILD_SHAPE_USES_REMAINING] = _mc_ws_uses(_druid_level)

    # WO-ENGINE-EVASION-001: Evasion and Improved Evasion for multiclass (PHB Rogue p.56, Monk p.41)
    _rogue_level = class_mix.get("rogue", 0)
    _monk_level = class_mix.get("monk", 0)
    _ranger_level = class_mix.get("ranger", 0)
    if _rogue_level >= 2 or _monk_level >= 2 or _ranger_level >= 9:
        entity[EF.EVASION] = True
    if _rogue_level >= 10 or _monk_level >= 9:
        entity[EF.IMPROVED_EVASION] = True

    # WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001: Fast Movement bonus (PHB p.26)
    _barbarian_level = class_mix.get("barbarian", 0)
    entity[EF.FAST_MOVEMENT_BONUS] = 10 if _barbarian_level >= 1 else 0

    # WO-ENGINE-MONK-WIS-AC-001: Multiclass does not call _assign_starting_equipment;
    # set armor defaults and MONK_WIS_AC_BONUS directly.
    # Multiclass entities start unarmored (no equipment assignment path).
    if EF.ARMOR_AC_BONUS not in entity:
        entity[EF.ARMOR_AC_BONUS] = 0
    if EF.ARMOR_TYPE not in entity:
        entity[EF.ARMOR_TYPE] = "none"
    if EF.MONK_WIS_AC_BONUS not in entity:
        entity[EF.MONK_WIS_AC_BONUS] = modifiers["wis"] if _monk_level >= 1 else 0

    # WO-ENGINE-TOUGHNESS-001: Toughness feat +3 HP per instance (PHB p.101; stackable)
    _toughness_count = entity.get(EF.FEATS, []).count("toughness")
    if _toughness_count > 0:
        _toughness_hp = _toughness_count * 3
        entity[EF.HP_MAX] = entity.get(EF.HP_MAX, 0) + _toughness_hp
        entity[EF.HP_CURRENT] = entity.get(EF.HP_CURRENT, 0) + _toughness_hp

    # WO-ENGINE-BARBARIAN-DR-001: Barbarian DR/— (PHB p.26)
    _barb_dr_table = [(19, 5), (16, 4), (13, 3), (10, 2), (7, 1)]
    for _threshold, _dr_value in _barb_dr_table:
        if _barbarian_level >= _threshold:
            _existing_dr = entity.get(EF.DAMAGE_REDUCTIONS, [])
            _existing_dash = next((d for d in _existing_dr if d.get("bypass") == "-"), None)
            if _existing_dash is None or _existing_dash["amount"] < _dr_value:
                entity[EF.DAMAGE_REDUCTIONS] = (
                    [d for d in _existing_dr if d.get("bypass") != "-"]
                    + [{"amount": _dr_value, "bypass": "-"}]
                )
            break

    # WO-ENGINE-EXTRA-TURNING-001: Turn Undead pool init + Extra Turning feat (PHB p.94)
    _cleric_level_et = class_mix.get("cleric", 0)
    _paladin_level_et = class_mix.get("paladin", 0)
    if _cleric_level_et >= 1 or _paladin_level_et >= 4:
        _turn_base = max(1, 3 + _cha_mod)
        _extra_turning_count = entity.get(EF.FEATS, []).count("extra_turning")
        _turn_max = _turn_base + 4 * _extra_turning_count
        entity[EF.TURN_UNDEAD_USES_MAX] = _turn_max
        entity[EF.TURN_UNDEAD_USES] = _turn_max

    # WO-ENGINE-MONK-UNARMED-PROGRESSION-001: Monk unarmed strike damage (PHB Table 3-10)
    _monk_level_mup = class_mix.get("monk", 0)
    _unarmed_table = [
        (20, "2d10"), (16, "2d8"), (12, "2d6"),
        (8, "1d10"), (4, "1d8"), (1, "1d6"),
    ]
    for _threshold, _dice in _unarmed_table:
        if _monk_level_mup >= _threshold:
            entity[EF.MONK_UNARMED_DICE] = _dice
            break

    return entity


# ---------------------------------------------------------------------------
# Level-Up System (WO-CHARGEN-PHASE3-LEVELUP)
# ---------------------------------------------------------------------------

# Canonical runtime source for class feature and class table data.
# aidm/data/class_definitions.py was deleted 2026-02-27 (no runtime consumer — Thunder Option B).
# Per-class features unlocked at each class level (PHB Chapter 3).
# Only levels with new features are listed — missing levels grant nothing.
_CLASS_FEATURES: Dict[str, Dict[int, List[str]]] = {
    "barbarian": {
        1:  ["fast_movement", "illiteracy", "rage"],
        2:  ["uncanny_dodge"],
        3:  ["trap_sense_1"],
        4:  ["rage_2_per_day"],
        5:  ["improved_uncanny_dodge"],
        6:  ["trap_sense_2"],
        7:  ["damage_reduction_1"],
        8:  ["rage_3_per_day"],
        9:  ["trap_sense_3"],
        10: ["damage_reduction_2"],
        11: ["greater_rage"],
        12: ["rage_4_per_day", "trap_sense_4"],
        13: ["damage_reduction_3"],
        14: ["indomitable_will"],
        15: ["trap_sense_5"],
        16: ["damage_reduction_4", "rage_5_per_day"],
        17: ["tireless_rage"],
        18: ["trap_sense_6"],
        19: ["damage_reduction_5"],
        20: ["mighty_rage", "rage_6_per_day"],
    },
    "bard": {
        1:  ["bardic_music", "bardic_knowledge", "countersong", "fascinate", "inspire_courage_1"],
        2:  ["well_versed"],
        3:  ["inspire_competence"],
        6:  ["suggestion"],
        8:  ["inspire_courage_2"],
        9:  ["inspire_greatness"],
        12: ["song_of_freedom"],
        14: ["inspire_courage_3"],
        15: ["inspire_heroics"],
        18: ["mass_suggestion"],
        20: ["inspire_courage_4"],
    },
    "cleric": {
        1:  ["aura", "spontaneous_casting", "turn_undead"],
    },
    "druid": {
        1:  ["animal_companion", "nature_sense", "wild_empathy"],
        2:  ["woodland_stride"],
        3:  ["trackless_step"],
        4:  ["resist_natures_lure", "wild_shape_small_medium"],
        5:  ["wild_shape_2_per_day"],
        6:  ["wild_shape_large", "wild_shape_3_per_day"],
        7:  ["wild_shape_4_per_day"],
        8:  ["wild_shape_tiny", "wild_shape_5_per_day"],
        9:  ["venom_immunity", "wild_shape_6_per_day"],
        10: ["wild_shape_plant"],
        11: ["wild_shape_huge", "wild_shape_7_per_day"],
        12: ["wild_shape_8_per_day"],
        13: ["a_thousand_faces"],
        14: ["wild_shape_9_per_day"],
        15: ["timeless_body"],
        16: ["wild_shape_elemental_small", "wild_shape_10_per_day"],
        17: ["wild_shape_11_per_day"],
        18: ["wild_shape_elemental_medium", "wild_shape_12_per_day"],
        19: ["wild_shape_13_per_day"],
        20: ["wild_shape_elemental_large", "wild_shape_14_per_day"],
    },
    "fighter": {
        1:  ["bonus_feat"],
        2:  ["bonus_feat"],
        4:  ["bonus_feat"],
        6:  ["bonus_feat"],
        8:  ["bonus_feat"],
        10: ["bonus_feat"],
        12: ["bonus_feat"],
        14: ["bonus_feat"],
        16: ["bonus_feat"],
        18: ["bonus_feat"],
        20: ["bonus_feat"],
    },
    "monk": {
        1:  ["flurry_of_blows", "unarmed_strike", "bonus_feat_monk"],
        2:  ["evasion", "bonus_feat_monk"],
        3:  ["still_mind"],
        4:  ["ki_strike_magic", "slow_fall_20ft"],
        5:  ["purity_of_body"],
        6:  ["bonus_feat_monk", "slow_fall_30ft"],
        7:  ["wholeness_of_body"],
        8:  ["slow_fall_40ft"],
        9:  ["improved_evasion"],
        10: ["ki_strike_lawful", "slow_fall_50ft"],
        11: ["diamond_body", "greater_flurry"],
        12: ["abundant_step", "slow_fall_60ft"],
        13: ["diamond_soul"],
        14: ["slow_fall_70ft"],
        15: ["quivering_palm"],
        16: ["ki_strike_adamantine", "slow_fall_80ft"],
        17: ["timeless_body", "tongue_of_sun_and_moon"],
        18: ["slow_fall_90ft"],
        19: ["empty_body"],
        20: ["perfect_self", "slow_fall_any"],
    },
    "paladin": {
        1:  ["aura_of_good", "detect_evil", "smite_evil_1_per_day"],
        2:  ["divine_grace", "lay_on_hands"],
        3:  ["aura_of_courage", "divine_health"],
        4:  ["turn_undead", "special_mount"],
        6:  ["remove_disease_1_per_week", "smite_evil_2_per_day"],
        9:  ["remove_disease_2_per_week"],
        11: ["remove_disease_3_per_week", "smite_evil_3_per_day"],
        13: ["remove_disease_4_per_week"],
        14: ["remove_disease_5_per_week"],
        16: ["remove_disease_6_per_week", "smite_evil_4_per_day"],
        19: ["remove_disease_7_per_week"],
        20: ["remove_disease_8_per_week"],
    },
    "ranger": {
        1:  ["first_favored_enemy", "track", "wild_empathy"],
        2:  ["combat_style"],
        3:  ["endurance"],
        4:  ["animal_companion"],
        5:  ["second_favored_enemy"],
        6:  ["improved_combat_style"],
        7:  ["woodland_stride"],
        8:  ["swift_tracker"],
        9:  ["evasion"],
        10: ["third_favored_enemy"],
        11: ["combat_style_mastery"],
        13: ["camouflage"],
        15: ["fourth_favored_enemy"],
        17: ["hide_in_plain_sight"],
        20: ["fifth_favored_enemy"],
    },
    "rogue": {
        1:  ["sneak_attack_1d6", "trapfinding"],
        2:  ["evasion"],
        3:  ["sneak_attack_2d6", "trap_sense_1"],
        4:  ["uncanny_dodge"],
        5:  ["sneak_attack_3d6"],
        6:  ["trap_sense_2"],
        7:  ["sneak_attack_4d6"],
        8:  ["improved_uncanny_dodge"],
        9:  ["sneak_attack_5d6", "trap_sense_3"],
        10: ["sneak_attack_6d6", "special_ability"],
        11: ["sneak_attack_7d6"],
        12: ["trap_sense_4"],
        13: ["sneak_attack_8d6"],
        14: ["special_ability"],
        15: ["sneak_attack_9d6", "trap_sense_5"],
        16: ["special_ability"],
        17: ["sneak_attack_10d6"],
        18: ["trap_sense_6"],
        19: ["sneak_attack_11d6"],
        20: ["sneak_attack_12d6", "special_ability"],
    },
    "sorcerer": {
        1:  ["summon_familiar"],
    },
    "wizard": {
        1:  ["summon_familiar", "scribe_scroll"],
        5:  ["bonus_feat_wizard"],
        10: ["bonus_feat_wizard"],
        15: ["bonus_feat_wizard"],
        20: ["bonus_feat_wizard"],
    },
}


def _roll_hp_for_level(
    hit_die: int,
    con_mod: int,
    is_first_class_level: bool,
    seed: Optional[int] = None,
) -> int:
    """Roll HP gained for one level in a class.

    Args:
        hit_die: Hit die size (e.g., 10 for fighter).
        con_mod: Constitution modifier.
        is_first_class_level: True when this is the first level in this class
            (e.g., multiclassing into wizard for the first time). Takes max.
        seed: Optional RNG seed for deterministic tests.

    Returns:
        HP gained (minimum 1).
    """
    if is_first_class_level:
        return max(1, hit_die + con_mod)
    rng = random.Random(seed)
    roll = rng.randint(1, hit_die)
    return max(1, roll + con_mod)


def _skill_points_for_level(class_name: str, int_mod: int) -> int:
    """Skill points awarded for one level in a class.

    Uses the class's base skill points per level from CLASS_PROGRESSIONS,
    plus INT modifier. Minimum 1 per level (PHB p.57).

    Args:
        class_name: Class name.
        int_mod: Intelligence modifier.

    Returns:
        Skill points awarded (minimum 1).
    """
    base = CLASS_PROGRESSIONS[class_name].skill_points_per_level
    return max(1, base + int_mod)


def level_up(
    entity: Dict[str, Any],
    class_name: str,
    new_class_level: int,
    feat_choices: Optional[List[str]] = None,
    skill_allocations: Optional[Dict[str, int]] = None,
    spell_choices: Optional[List[str]] = None,
    hp_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Advance entity by one level in class_name.

    Pure function — does NOT mutate entity. Caller applies the returned
    delta dict to the entity.

    WO-CHARGEN-PHASE3-LEVELUP §3.1.

    Args:
        entity: Existing entity dict (from build_character or prior level_up).
        class_name: Which class gains the level.
        new_class_level: The new level reached in this class (e.g. 2 for L1→L2).
        feat_choices: Feats to add if a feat slot opens this level.
        skill_allocations: {skill_id: ranks_added} for new skill points.
        spell_choices: New spells for caster classes (stored, not applied here).
        hp_seed: Optional RNG seed for deterministic HP rolls.

    Returns:
        Delta dict with keys:
            "hp_gained": int
            "feat_slots_gained": int
            "feats_added": list[str]
            "class_features_gained": list[str]
            "spell_slots": dict  (updated slot table, or {} if non-caster)
            "skill_points_gained": int
            "bab": int
            "saves": {"fort": int, "ref": int, "will": int}
            "new_total_level": int

    Raises:
        ValueError: If class_name is unknown, new_class_level is invalid,
            or the entity's total level would exceed 20.
    """
    if class_name not in CLASS_PROGRESSIONS:
        raise ValueError(
            f"Unknown class '{class_name}'. Available: {list(CLASS_PROGRESSIONS.keys())}"
        )

    class_levels: Dict[str, int] = dict(entity.get(EF.CLASS_LEVELS, {}))
    current_class_level = class_levels.get(class_name, 0)

    # Validate new_class_level is exactly one step up
    if new_class_level != current_class_level + 1:
        raise ValueError(
            f"new_class_level must be current {class_name} level + 1 "
            f"(got {new_class_level}, current is {current_class_level})"
        )

    current_total = entity.get(EF.LEVEL, sum(class_levels.values()))
    new_total_level = current_total + 1
    if new_total_level > 20:
        raise ValueError(f"Total level would exceed 20 (current={current_total})")

    race = entity.get(EF.RACE, "human")
    class_prog = CLASS_PROGRESSIONS[class_name]

    # --- HP ---
    con_mod = entity.get(EF.CON_MOD, 0)
    is_first_class_level = (current_class_level == 0)
    hp_gained = _roll_hp_for_level(class_prog.hit_die, con_mod, is_first_class_level, hp_seed)

    # --- BAB: best single-class BAB across all class levels after advancement ---
    updated_class_levels = dict(class_levels)
    updated_class_levels[class_name] = new_class_level
    bab = max(
        BAB_PROGRESSION[CLASS_PROGRESSIONS[cls].bab_type][lvl - 1]
        for cls, lvl in updated_class_levels.items()
    )

    # --- Saves: best progression independently for each save ---
    def _save_base(cls: str, lvl: int, save_type: str) -> int:
        prog = CLASS_PROGRESSIONS[cls]
        if save_type in prog.good_saves:
            return GOOD_SAVE_PROGRESSION[lvl - 1]
        return POOR_SAVE_PROGRESSION[lvl - 1]

    fort_base = max(_save_base(cls, lvl, "fort") for cls, lvl in updated_class_levels.items())
    ref_base  = max(_save_base(cls, lvl, "ref")  for cls, lvl in updated_class_levels.items())
    will_base = max(_save_base(cls, lvl, "will") for cls, lvl in updated_class_levels.items())

    saves = {
        "fort": fort_base + entity.get(EF.CON_MOD, 0),
        "ref":  ref_base  + entity.get(EF.DEX_MOD, 0),
        "will": will_base + entity.get(EF.WIS_MOD, 0),
    }

    # --- Feat slots ---
    old_total = new_total_level - 1
    old_feat_slots = _feat_slots_at_level(old_total, race)
    new_feat_slots = _feat_slots_at_level(new_total_level, race)
    feat_slots_gained = max(0, new_feat_slots - old_feat_slots)

    feats_added: List[str] = []
    if feat_slots_gained > 0 and feat_choices:
        feats_added = list(feat_choices[:feat_slots_gained])

    # --- Class features ---
    class_features_gained: List[str] = list(
        _CLASS_FEATURES.get(class_name, {}).get(new_class_level, [])
    )

    # --- Skill points ---
    int_mod = entity.get(EF.INT_MOD, 0)
    skill_points_gained = _skill_points_for_level(class_name, int_mod)

    # --- Spell slots (casters only) ---
    spell_slots: Dict = {}
    if is_caster(class_name):
        casting_stat = CASTING_ABILITY[class_name]
        final_scores = entity.get(EF.BASE_STATS, {})
        casting_score = final_scores.get(casting_stat, 10)
        spell_slots = get_spell_slots(class_name, new_class_level, casting_score)

    # WO-ENGINE-TOUGHNESS-001: New Toughness feats at level-up add +3 HP each (PHB p.101)
    _new_toughness = feats_added.count("toughness")
    if _new_toughness > 0:
        hp_gained += _new_toughness * 3

    return {
        "hp_gained": hp_gained,
        "feat_slots_gained": feat_slots_gained,
        "feats_added": feats_added,
        "class_features_gained": class_features_gained,
        "spell_slots": spell_slots,
        "skill_points_gained": skill_points_gained,
        "bab": bab,
        "saves": saves,
        "new_total_level": new_total_level,
    }
