"""Race definitions for D&D 3.5e character creation.

WO-CHARGEN-FOUNDATION-001 (Part B, GAP-CG-002).

All 7 PHB races with complete mechanical data.
Racial traits are stored as string IDs — mechanical effects are OUT OF SCOPE.

Source: PHB Chapter 2 (Races), pp.12-18.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Dict, List


@dataclass(frozen=True)
class RaceDefinition:
    """Complete mechanical definition of a D&D 3.5e race."""

    race_id: str
    """Unique identifier (e.g., 'human', 'elf', 'dwarf')."""

    name: str
    """Display name (e.g., 'Human', 'Elf', 'Dwarf')."""

    size: str
    """Size category: 'small' or 'medium'."""

    base_speed: int
    """Base land speed in feet."""

    ability_mods: Dict[str, int]
    """Racial ability score modifiers (e.g., {'dex': 2, 'con': -2})."""

    favored_class: str
    """Favored class ID or 'any' for multiclassing (PHB p.56)."""

    bonus_feats: int
    """Bonus feats at 1st level (1 for Human, 0 for others)."""

    bonus_skill_points_per_level: int
    """Bonus skill points per level (1 for Human, 0 for others).
    At 1st level this is multiplied by 4 (PHB p.12)."""

    racial_traits: List[str]
    """Descriptive trait IDs (e.g., 'darkvision_60', 'stonecunning').
    Mechanical effects are out of scope for this WO."""

    languages: List[str]
    """Automatic starting languages."""

    speed_ignores_armor: bool
    """True for Dwarf — speed not reduced by medium/heavy armor (PHB p.15)."""

    provenance: str
    """'RAW' for all PHB races."""

    source_ref: str
    """PHB page reference."""

    def __post_init__(self):
        """Freeze mutable containers for true immutability."""
        object.__setattr__(self, "ability_mods", MappingProxyType(dict(self.ability_mods)))
        object.__setattr__(self, "racial_traits", tuple(self.racial_traits))
        object.__setattr__(self, "languages", tuple(self.languages))


# ---------------------------------------------------------------------------
# Race Registry — all 7 PHB races
# ---------------------------------------------------------------------------

RACE_REGISTRY: Dict[str, RaceDefinition] = {

    "human": RaceDefinition(
        race_id="human",
        name="Human",
        size="medium",
        base_speed=30,
        ability_mods={},
        favored_class="any",
        bonus_feats=1,
        bonus_skill_points_per_level=1,
        racial_traits=["bonus_feat", "bonus_skill_points"],
        languages=["Common"],
        speed_ignores_armor=False,
        provenance="RAW",
        source_ref="PHB p.12",
    ),

    "elf": RaceDefinition(
        race_id="elf",
        name="Elf",
        size="medium",
        base_speed=30,
        ability_mods={"dex": 2, "con": -2},
        favored_class="wizard",
        bonus_feats=0,
        bonus_skill_points_per_level=0,
        racial_traits=[
            "immunity_sleep",
            "elven_blood",
            "low_light_vision",
            "weapon_proficiency_elven",
            "search_bonus_2",
            "listen_spot_bonus_2",
            "secret_door_detection",
        ],
        languages=["Common", "Elven"],
        speed_ignores_armor=False,
        provenance="RAW",
        source_ref="PHB p.15",
    ),

    "dwarf": RaceDefinition(
        race_id="dwarf",
        name="Dwarf",
        size="medium",
        base_speed=20,
        ability_mods={"con": 2, "cha": -2},
        favored_class="fighter",
        bonus_feats=0,
        bonus_skill_points_per_level=0,
        racial_traits=[
            "darkvision_60",
            "stonecunning",
            "weapon_familiarity_dwarf",
            "stability",
            "save_bonus_poison_2",
            "save_bonus_spells_2",
            "attack_bonus_orc_goblin_1",
            "dodge_bonus_ac_giant_4",
            "appraise_stone_bonus_2",
            "craft_stone_bonus_2",
        ],
        languages=["Common", "Dwarven"],
        speed_ignores_armor=True,
        provenance="RAW",
        source_ref="PHB p.14",
    ),

    "halfling": RaceDefinition(
        race_id="halfling",
        name="Halfling",
        size="small",
        base_speed=20,
        ability_mods={"dex": 2, "str": -2},
        favored_class="rogue",
        bonus_feats=0,
        bonus_skill_points_per_level=0,
        racial_traits=[
            "small_size",
            "attack_bonus_thrown_sling_1",
            "save_bonus_all_1",
            "save_bonus_fear_2",
            "climb_jump_move_silently_bonus_2",
            "listen_bonus_2",
        ],
        languages=["Common", "Halfling"],
        speed_ignores_armor=False,
        provenance="RAW",
        source_ref="PHB p.16",
    ),

    "gnome": RaceDefinition(
        race_id="gnome",
        name="Gnome",
        size="small",
        base_speed=20,
        ability_mods={"con": 2, "str": -2},
        favored_class="bard",
        bonus_feats=0,
        bonus_skill_points_per_level=0,
        racial_traits=[
            "small_size",
            "low_light_vision",
            "weapon_familiarity_gnome",
            "illusion_save_bonus_2",
            "illusion_dc_bonus_1",
            "attack_bonus_kobold_goblin_1",
            "dodge_bonus_ac_giant_4",
            "listen_bonus_2",
            "craft_alchemy_bonus_2",
            "speak_with_burrowing_animals",
            "spell_like_speak_animals",
            "spell_like_dancing_lights",
            "spell_like_ghost_sound",
            "spell_like_prestidigitation",
        ],
        languages=["Common", "Gnome"],
        speed_ignores_armor=False,
        provenance="RAW",
        source_ref="PHB p.16",
    ),

    "half_elf": RaceDefinition(
        race_id="half_elf",
        name="Half-Elf",
        size="medium",
        base_speed=30,
        ability_mods={},
        favored_class="any",
        bonus_feats=0,
        bonus_skill_points_per_level=0,
        racial_traits=[
            "immunity_sleep",
            "elven_blood",
            "low_light_vision",
            "search_bonus_1",
            "listen_spot_bonus_1",
            "diplomacy_gather_info_bonus_2",
        ],
        languages=["Common", "Elven"],
        speed_ignores_armor=False,
        provenance="RAW",
        source_ref="PHB p.18",
    ),

    "half_orc": RaceDefinition(
        race_id="half_orc",
        name="Half-Orc",
        size="medium",
        base_speed=30,
        ability_mods={"str": 2, "int": -2, "cha": -2},
        favored_class="barbarian",
        bonus_feats=0,
        bonus_skill_points_per_level=0,
        racial_traits=[
            "darkvision_60",
            "orc_blood",
        ],
        languages=["Common", "Orc"],
        speed_ignores_armor=False,
        provenance="RAW",
        source_ref="PHB p.18",
    ),
}


def get_race(race_id: str) -> RaceDefinition:
    """Look up race by ID.

    Args:
        race_id: Race identifier (e.g., 'dwarf', 'halfling').

    Returns:
        RaceDefinition for the specified race.

    Raises:
        KeyError: If race_id is not in the registry.
    """
    if race_id not in RACE_REGISTRY:
        raise KeyError(
            f"Unknown race '{race_id}'. Available: {list(RACE_REGISTRY.keys())}"
        )
    return RACE_REGISTRY[race_id]


def apply_racial_mods(scores: Dict[str, int], race_id: str) -> Dict[str, int]:
    """Apply racial ability modifiers to a score array.

    Args:
        scores: Dict mapping ability name to score (6 entries).
        race_id: Race identifier.

    Returns:
        New dict with racial modifiers applied. Original is not mutated.
    """
    race = get_race(race_id)
    result = dict(scores)
    for ability, mod in race.ability_mods.items():
        if ability in result:
            result[ability] += mod
    return result


def list_races() -> List[str]:
    """Return all available race IDs.

    Returns:
        Sorted list of race_id strings.
    """
    return sorted(RACE_REGISTRY.keys())
