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
from aidm.data.races import RACE_REGISTRY, get_race, apply_racial_mods
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
    effective_dex = dex_mod

    if armor_id:
        a = _catalog_armor(armor_id)
        if a and gold >= a.get("cost_gp", 0):
            gold -= a.get("cost_gp", 0)
            inventory.append({"item_id": armor_id, "quantity": 1})
            total_weight += a.get("weight_lb", 0.0)
            armor_ac_bonus = a.get("ac_bonus", 0)
            armor_check_penalty = a.get("armor_check_penalty", 0)
            max_dex = a.get("max_dex_bonus")
            if max_dex is not None and max_dex < 99:
                effective_dex = min(dex_mod, max_dex)

    # AC (§3.5): 10 + effective_dex + armor_bonus [+ WIS for monk]
    ac = 10 + effective_dex + armor_ac_bonus
    if kit.get("wis_to_ac"):  # Monk class feature PHB p.41
        ac += wis_mod
    entity[EF.AC] = ac
    entity[EF.ARMOR_CHECK_PENALTY] = armor_check_penalty

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


def _merge_spellcasting(
    class_mix: Dict[str, int],
    final_scores: Dict[str, int],
    spell_choices: Optional[List[str]],
) -> Tuple[Dict, Dict, Dict, int]:
    """Resolve spellcasting for a multiclass character.

    Decision (WO-CHARGEN-MULTICLASS-001): If multiple caster classes are present,
    each is resolved independently at its own class level. Spell slots and spells
    known/prepared are keyed by class name when more than one caster class exists.
    For a single caster class, results are stored flat (same as single-class path).

    Args:
        class_mix: Dict mapping class name to level
        final_scores: Final ability scores after racial mods
        spell_choices: Optional list of spell IDs to assign

    Returns:
        Tuple of (spell_slots, spells_known, spells_prepared, caster_level)
    """
    caster_classes = [(cls, lvl) for cls, lvl in class_mix.items() if is_caster(cls)]

    if not caster_classes:
        return {}, {}, {}, 0

    if len(caster_classes) == 1:
        # Single caster — use existing flat format
        cls, lvl = caster_classes[0]
        casting_stat = CASTING_ABILITY[cls]
        casting_score = final_scores[casting_stat]

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
                spells_known = {lvl: [] for lvl in known_counts}
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

        return spell_slots, spells_known, spells_prepared, lvl

    else:
        # Multiple casters — resolve each independently, keyed by class name.
        # Spell slots from primary (highest-level) caster are stored flat;
        # secondary casters stored under their class key.
        # Dual-caster slot merging is deferred per WO scope boundary.
        primary_cls, primary_lvl = max(caster_classes, key=lambda x: x[1])
        casting_stat = CASTING_ABILITY[primary_cls]
        casting_score = final_scores[casting_stat]
        spell_slots = get_spell_slots(primary_cls, primary_lvl, casting_score)

        spells_known: Dict = {}
        spells_prepared: Dict = {}

        if primary_cls in SPONTANEOUS_CASTERS:
            known_counts = get_spells_known_count(primary_cls, primary_lvl) or {}
            if spell_choices:
                remaining = list(spell_choices)
                for spell_level in sorted(known_counts.keys()):
                    count = known_counts[spell_level]
                    available = get_class_spell_list(primary_cls, spell_level)
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
            if spell_choices:
                from aidm.data.spell_definitions import SPELL_REGISTRY
                for sid in spell_choices:
                    if sid in SPELL_REGISTRY:
                        spell = SPELL_REGISTRY[sid]
                        slvl = spell.level
                        if slvl not in spells_prepared:
                            spells_prepared[slvl] = []
                        spells_prepared[slvl].append(sid)

        return spell_slots, spells_known, spells_prepared, primary_lvl


def build_character(
    race: str,
    class_name: str,
    level: int = 1,
    ability_method: str = "standard",
    ability_overrides: Optional[Dict[str, int]] = None,
    feat_choices: Optional[List[str]] = None,
    skill_allocations: Optional[Dict[str, int]] = None,
    spell_choices: Optional[List[str]] = None,
    starting_equipment: Optional[Dict[str, int]] = None,
    use_rolled_gold: bool = False,
    class_mix: Optional[Dict[str, int]] = None,
    favored_class: Optional[str] = None,
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
        starting_equipment: Dict of item_id -> quantity. Currently stored only.
        use_rolled_gold: If True, use rolled gold for starting equipment.
        class_mix: Multiclass dict, e.g. {"fighter": 3, "wizard": 2}. If provided,
            class_name and level are ignored.
        favored_class: Optional favored class name (PHB p.56). Stored informational only.

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
    entity[EF.SPELLS_KNOWN] = spells_known
    entity[EF.SPELLS_PREPARED] = spells_prepared
    entity[EF.CASTER_LEVEL] = caster_level

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

    return entity


def _build_multiclass_character(
    race: str,
    class_mix: Dict[str, int],
    ability_method: str = "standard",
    ability_overrides: Optional[Dict[str, int]] = None,
    feat_choices: Optional[List[str]] = None,
    skill_allocations: Optional[Dict[str, int]] = None,
    spell_choices: Optional[List[str]] = None,
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
    spell_slots, spells_known, spells_prepared, caster_level = _merge_spellcasting(
        class_mix, final_scores, spell_choices,
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
    entity[EF.SPELLS_KNOWN] = spells_known
    entity[EF.SPELLS_PREPARED] = spells_prepared
    entity[EF.CASTER_LEVEL] = caster_level

    # Favored class (informational, PHB p.56)
    if favored_class is not None:
        entity["favored_class"] = favored_class

    return entity
