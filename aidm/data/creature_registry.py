"""Creature stat block registry — D&D 3.5e MM facts (data layer).

Priority creatures covering Tier 1–2 play (CR 1/4 through CR 10).
All values are from Monster Manual 3.5e (OGL content — facts not copyrightable).

WO-DATA-MONSTERS-001: initial population (25–30 priority creatures).

Schema note: aidm/schemas/bestiary.py contains the world-compiler BestiaryEntry
schema.  That schema is for compiled campaign content.  This file uses a simpler
flat CreatureStatBlock for direct engine use and content-pack lookup.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class CreatureStatBlock:
    """Flat stat block for a D&D 3.5e creature."""

    creature_id: str           # snake_case, e.g. "goblin"
    name: str                  # display name, e.g. "Goblin"
    creature_type: str         # "humanoid", "undead", "animal", "giant", etc.
    size: str                  # "tiny","small","medium","large","huge","gargantuan"
    hp: int                    # average HP per MM
    ac: int                    # total AC as listed in MM
    bab: int                   # base attack bonus
    fort: int                  # Fortitude save (total)
    ref: int                   # Reflex save (total)
    will: int                  # Will save (total)
    str_score: int
    dex_score: int
    con_score: int             # 0 for undead (no Constitution score)
    int_score: int             # 0 for mindless (oozes, vermin)
    wis_score: int
    cha_score: int
    attacks: List[Dict]        # [{name, attack_bonus, damage_dice, damage_type}]
    cr: float                  # challenge rating
    special_qualities: List[str]  # string tags: "darkvision", "regeneration_5", etc.


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CREATURE_REGISTRY: Dict[str, CreatureStatBlock] = {

    # =======================================================================
    # TIER 1 — CR 1/4 to CR 1
    # =======================================================================

    "goblin": CreatureStatBlock(
        creature_id="goblin", name="Goblin",
        creature_type="humanoid", size="small",
        hp=5, ac=15, bab=0,
        fort=1, ref=3, will=-1,
        str_score=8, dex_score=13, con_score=11,
        int_score=10, wis_score=9, cha_score=8,
        attacks=[
            {"name": "morningstar", "attack_bonus": 2, "damage_dice": "1d6-1",
             "damage_type": "bludgeoning"},
        ],
        cr=0.25,
        special_qualities=["darkvision_60"],
    ),

    "kobold": CreatureStatBlock(
        creature_id="kobold", name="Kobold",
        creature_type="humanoid", size="small",
        hp=4, ac=15, bab=0,
        fort=0, ref=1, will=-1,
        str_score=9, dex_score=13, con_score=10,
        int_score=10, wis_score=9, cha_score=8,
        attacks=[
            {"name": "spear", "attack_bonus": 1, "damage_dice": "1d6-1",
             "damage_type": "piercing"},
        ],
        cr=0.25,
        special_qualities=["darkvision_60", "light_sensitivity"],
    ),

    "dire_rat": CreatureStatBlock(
        creature_id="dire_rat", name="Dire Rat",
        creature_type="animal", size="small",
        hp=5, ac=15, bab=0,
        fort=3, ref=5, will=1,
        str_score=10, dex_score=17, con_score=12,
        int_score=1, wis_score=12, cha_score=4,
        attacks=[
            {"name": "bite", "attack_bonus": 4, "damage_dice": "1d4",
             "damage_type": "piercing"},
        ],
        cr=0.33,
        special_qualities=["low_light_vision", "scent"],
    ),

    "giant_centipede": CreatureStatBlock(
        creature_id="giant_centipede", name="Monstrous Centipede (Small)",
        creature_type="vermin", size="small",
        hp=4, ac=14, bab=0,
        fort=2, ref=3, will=0,
        str_score=9, dex_score=17, con_score=10,
        int_score=0, wis_score=10, cha_score=2,
        attacks=[
            {"name": "bite", "attack_bonus": 4, "damage_dice": "1d4-1",
             "damage_type": "piercing"},
        ],
        cr=0.25,
        special_qualities=["darkvision_60", "vermin_traits"],
    ),

    "skeleton_human": CreatureStatBlock(
        creature_id="skeleton_human", name="Human Skeleton",
        creature_type="undead", size="medium",
        hp=6, ac=13, bab=0,
        fort=0, ref=0, will=2,
        str_score=15, dex_score=10, con_score=0,
        int_score=0, wis_score=10, cha_score=1,
        attacks=[
            {"name": "claw", "attack_bonus": 2, "damage_dice": "1d4+2",
             "damage_type": "slashing"},
            {"name": "claw", "attack_bonus": 2, "damage_dice": "1d4+2",
             "damage_type": "slashing"},
        ],
        cr=0.33,
        special_qualities=["undead_traits", "darkvision_60",
                           "immunity_cold", "immunity_mind_affecting"],
    ),

    "zombie_human": CreatureStatBlock(
        creature_id="zombie_human", name="Human Zombie",
        creature_type="undead", size="medium",
        hp=16, ac=11, bab=1,
        fort=0, ref=0, will=3,
        str_score=15, dex_score=10, con_score=0,
        int_score=0, wis_score=10, cha_score=1,
        attacks=[
            {"name": "slam", "attack_bonus": 2, "damage_dice": "1d6+1",
             "damage_type": "bludgeoning"},
        ],
        cr=0.5,
        special_qualities=["undead_traits", "darkvision_60",
                           "immunity_mind_affecting", "single_actions_only"],
    ),

    "orc": CreatureStatBlock(
        creature_id="orc", name="Orc",
        creature_type="humanoid", size="medium",
        hp=5, ac=13, bab=1,
        fort=3, ref=0, will=-2,
        str_score=15, dex_score=10, con_score=12,
        int_score=9, wis_score=8, cha_score=8,
        attacks=[
            {"name": "falchion", "attack_bonus": 4, "damage_dice": "2d4+4",
             "damage_type": "slashing"},
        ],
        cr=0.5,
        special_qualities=["darkvision_60", "light_sensitivity"],
    ),

    "wolf": CreatureStatBlock(
        creature_id="wolf", name="Wolf",
        creature_type="animal", size="medium",
        hp=13, ac=14, bab=1,
        fort=5, ref=5, will=1,
        str_score=13, dex_score=15, con_score=15,
        int_score=2, wis_score=12, cha_score=6,
        attacks=[
            {"name": "bite", "attack_bonus": 3, "damage_dice": "1d6+1",
             "damage_type": "piercing"},
        ],
        cr=1.0,
        special_qualities=["low_light_vision", "scent"],
    ),

    # =======================================================================
    # TIER 1-2 — CR 1 to CR 3
    # =======================================================================

    "hobgoblin": CreatureStatBlock(
        creature_id="hobgoblin", name="Hobgoblin",
        creature_type="humanoid", size="medium",
        hp=9, ac=15, bab=2,
        fort=5, ref=1, will=0,
        str_score=13, dex_score=13, con_score=14,
        int_score=10, wis_score=10, cha_score=10,
        attacks=[
            {"name": "longsword", "attack_bonus": 3, "damage_dice": "1d8+1",
             "damage_type": "slashing"},
        ],
        cr=1.0,
        special_qualities=["darkvision_60"],
    ),

    "gnoll": CreatureStatBlock(
        creature_id="gnoll", name="Gnoll",
        creature_type="humanoid", size="medium",
        hp=11, ac=15, bab=1,
        fort=4, ref=0, will=0,
        str_score=15, dex_score=10, con_score=13,
        int_score=8, wis_score=11, cha_score=8,
        attacks=[
            {"name": "battleaxe", "attack_bonus": 3, "damage_dice": "1d8+3",
             "damage_type": "slashing"},
        ],
        cr=1.0,
        special_qualities=["darkvision_60"],
    ),

    "lizardfolk": CreatureStatBlock(
        creature_id="lizardfolk", name="Lizardfolk",
        creature_type="humanoid", size="medium",
        hp=11, ac=15, bab=1,
        fort=4, ref=0, will=1,
        str_score=15, dex_score=10, con_score=13,
        int_score=9, wis_score=12, cha_score=10,
        attacks=[
            {"name": "claw", "attack_bonus": 2, "damage_dice": "1d4+2",
             "damage_type": "slashing"},
            {"name": "claw", "attack_bonus": 2, "damage_dice": "1d4+2",
             "damage_type": "slashing"},
            {"name": "bite", "attack_bonus": 0, "damage_dice": "1d4+1",
             "damage_type": "piercing"},
        ],
        cr=1.0,
        special_qualities=["hold_breath"],
    ),

    "troglodyte": CreatureStatBlock(
        creature_id="troglodyte", name="Troglodyte",
        creature_type="humanoid", size="medium",
        hp=13, ac=15, bab=1,
        fort=5, ref=0, will=0,
        str_score=12, dex_score=10, con_score=14,
        int_score=8, wis_score=10, cha_score=10,
        attacks=[
            {"name": "claw", "attack_bonus": 2, "damage_dice": "1d4+1",
             "damage_type": "slashing"},
            {"name": "claw", "attack_bonus": 2, "damage_dice": "1d4+1",
             "damage_type": "slashing"},
            {"name": "bite", "attack_bonus": 0, "damage_dice": "1d4",
             "damage_type": "piercing"},
        ],
        cr=1.0,
        special_qualities=["darkvision_90", "stench"],
    ),

    "ghoul": CreatureStatBlock(
        creature_id="ghoul", name="Ghoul",
        creature_type="undead", size="medium",
        hp=13, ac=14, bab=1,
        fort=0, ref=2, will=5,
        str_score=13, dex_score=15, con_score=0,
        int_score=13, wis_score=14, cha_score=16,
        attacks=[
            {"name": "claw", "attack_bonus": 3, "damage_dice": "1d3+1",
             "damage_type": "slashing"},
            {"name": "claw", "attack_bonus": 3, "damage_dice": "1d3+1",
             "damage_type": "slashing"},
            {"name": "bite", "attack_bonus": 0, "damage_dice": "1d6",
             "damage_type": "piercing"},
        ],
        cr=1.0,
        special_qualities=["undead_traits", "darkvision_60", "paralysis",
                           "turn_resistance_2"],
    ),

    "giant_spider": CreatureStatBlock(
        creature_id="giant_spider", name="Monstrous Spider (Medium)",
        creature_type="vermin", size="medium",
        hp=11, ac=14, bab=1,
        fort=4, ref=3, will=0,
        str_score=11, dex_score=17, con_score=12,
        int_score=0, wis_score=10, cha_score=2,
        attacks=[
            {"name": "bite", "attack_bonus": 4, "damage_dice": "1d6",
             "damage_type": "piercing"},
        ],
        cr=1.0,
        special_qualities=["darkvision_60", "vermin_traits", "poison", "web"],
    ),

    "black_bear": CreatureStatBlock(
        creature_id="black_bear", name="Black Bear",
        creature_type="animal", size="medium",
        hp=19, ac=13, bab=2,
        fort=5, ref=4, will=2,
        str_score=19, dex_score=13, con_score=15,
        int_score=2, wis_score=12, cha_score=6,
        attacks=[
            {"name": "claw", "attack_bonus": 6, "damage_dice": "1d4+4",
             "damage_type": "slashing"},
            {"name": "claw", "attack_bonus": 6, "damage_dice": "1d4+4",
             "damage_type": "slashing"},
            {"name": "bite", "attack_bonus": 1, "damage_dice": "1d6+2",
             "damage_type": "piercing"},
        ],
        cr=2.0,
        special_qualities=["low_light_vision", "scent"],
    ),

    "bugbear": CreatureStatBlock(
        creature_id="bugbear", name="Bugbear",
        creature_type="humanoid", size="medium",
        hp=16, ac=17, bab=2,
        fort=4, ref=2, will=1,
        str_score=15, dex_score=12, con_score=13,
        int_score=10, wis_score=10, cha_score=9,
        attacks=[
            {"name": "morningstar", "attack_bonus": 5, "damage_dice": "1d8+2",
             "damage_type": "bludgeoning"},
        ],
        cr=2.0,
        special_qualities=["darkvision_60", "scent"],
    ),

    "crocodile": CreatureStatBlock(
        creature_id="crocodile", name="Crocodile",
        creature_type="animal", size="medium",
        hp=22, ac=15, bab=3,
        fort=5, ref=4, will=2,
        str_score=19, dex_score=12, con_score=13,
        int_score=1, wis_score=12, cha_score=2,
        attacks=[
            {"name": "bite", "attack_bonus": 6, "damage_dice": "2d6+4",
             "damage_type": "piercing"},
            {"name": "tail_slap", "attack_bonus": 6, "damage_dice": "1d12+4",
             "damage_type": "bludgeoning"},
        ],
        cr=2.0,
        special_qualities=["hold_breath", "low_light_vision"],
    ),

    "wight": CreatureStatBlock(
        creature_id="wight", name="Wight",
        creature_type="undead", size="medium",
        hp=26, ac=15, bab=2,
        fort=1, ref=3, will=5,
        str_score=15, dex_score=13, con_score=0,
        int_score=11, wis_score=13, cha_score=12,
        attacks=[
            {"name": "slam", "attack_bonus": 3, "damage_dice": "1d4+3",
             "damage_type": "bludgeoning"},
        ],
        cr=3.0,
        special_qualities=["undead_traits", "darkvision_60",
                           "energy_drain", "create_spawn"],
    ),

    "dire_wolf": CreatureStatBlock(
        creature_id="dire_wolf", name="Dire Wolf",
        creature_type="animal", size="large",
        hp=45, ac=14, bab=4,
        fort=8, ref=7, will=3,
        str_score=25, dex_score=15, con_score=17,
        int_score=2, wis_score=12, cha_score=10,
        attacks=[
            {"name": "bite", "attack_bonus": 10, "damage_dice": "2d6+10",
             "damage_type": "piercing"},
        ],
        cr=3.0,
        special_qualities=["low_light_vision", "scent"],
    ),

    "ogre": CreatureStatBlock(
        creature_id="ogre", name="Ogre",
        creature_type="giant", size="large",
        hp=29, ac=17, bab=3,
        fort=6, ref=0, will=1,
        str_score=21, dex_score=8, con_score=15,
        int_score=6, wis_score=10, cha_score=7,
        attacks=[
            {"name": "greatclub", "attack_bonus": 8, "damage_dice": "2d8+7",
             "damage_type": "bludgeoning"},
        ],
        cr=3.0,
        special_qualities=["darkvision_60", "low_light_vision"],
    ),

    # =======================================================================
    # TIER 2 — CR 4 to CR 10
    # =======================================================================

    "brown_bear": CreatureStatBlock(
        creature_id="brown_bear", name="Brown Bear",
        creature_type="animal", size="large",
        hp=51, ac=15, bab=4,
        fort=9, ref=6, will=3,
        str_score=27, dex_score=13, con_score=19,
        int_score=2, wis_score=12, cha_score=6,
        attacks=[
            {"name": "claw", "attack_bonus": 11, "damage_dice": "1d8+8",
             "damage_type": "slashing"},
            {"name": "claw", "attack_bonus": 11, "damage_dice": "1d8+8",
             "damage_type": "slashing"},
            {"name": "bite", "attack_bonus": 6, "damage_dice": "1d8+4",
             "damage_type": "piercing"},
        ],
        cr=4.0,
        special_qualities=["low_light_vision", "scent"],
    ),

    "owlbear": CreatureStatBlock(
        creature_id="owlbear", name="Owlbear",
        creature_type="magical_beast", size="large",
        hp=52, ac=15, bab=7,
        fort=7, ref=6, will=3,
        str_score=21, dex_score=12, con_score=15,
        int_score=2, wis_score=12, cha_score=8,
        attacks=[
            {"name": "claw", "attack_bonus": 9, "damage_dice": "1d6+5",
             "damage_type": "slashing"},
            {"name": "claw", "attack_bonus": 9, "damage_dice": "1d6+5",
             "damage_type": "slashing"},
            {"name": "bite", "attack_bonus": 4, "damage_dice": "1d8+2",
             "damage_type": "piercing"},
        ],
        cr=4.0,
        special_qualities=["darkvision_60", "low_light_vision", "scent"],
    ),

    "vampire_spawn": CreatureStatBlock(
        creature_id="vampire_spawn", name="Vampire Spawn",
        creature_type="undead", size="medium",
        hp=25, ac=14, bab=2,
        fort=1, ref=5, will=3,
        str_score=15, dex_score=16, con_score=0,
        int_score=11, wis_score=13, cha_score=14,
        attacks=[
            {"name": "slam", "attack_bonus": 4, "damage_dice": "1d6+3",
             "damage_type": "bludgeoning"},
        ],
        cr=4.0,
        special_qualities=["undead_traits", "darkvision_60", "energy_drain",
                           "blood_drain", "gaseous_form", "spider_climb"],
    ),

    "basilisk": CreatureStatBlock(
        creature_id="basilisk", name="Basilisk",
        creature_type="magical_beast", size="medium",
        hp=45, ac=16, bab=6,
        fort=7, ref=4, will=3,
        str_score=15, dex_score=8, con_score=15,
        int_score=2, wis_score=12, cha_score=11,
        attacks=[
            {"name": "bite", "attack_bonus": 8, "damage_dice": "1d8+3",
             "damage_type": "piercing"},
        ],
        cr=5.0,
        special_qualities=["darkvision_60", "low_light_vision", "petrifying_gaze"],
    ),

    "troll": CreatureStatBlock(
        creature_id="troll", name="Troll",
        creature_type="giant", size="large",
        hp=63, ac=16, bab=4,
        fort=11, ref=4, will=1,
        str_score=23, dex_score=14, con_score=23,
        int_score=6, wis_score=9, cha_score=6,
        attacks=[
            {"name": "claw", "attack_bonus": 9, "damage_dice": "1d6+6",
             "damage_type": "slashing"},
            {"name": "claw", "attack_bonus": 9, "damage_dice": "1d6+6",
             "damage_type": "slashing"},
            {"name": "bite", "attack_bonus": 4, "damage_dice": "1d6+3",
             "damage_type": "piercing"},
        ],
        cr=5.0,
        special_qualities=["darkvision_90", "low_light_vision",
                           "regeneration_5", "scent"],
    ),

    "will_o_wisp": CreatureStatBlock(
        creature_id="will_o_wisp", name="Will-o'-Wisp",
        creature_type="aberration", size="small",
        hp=40, ac=29, bab=6,
        fort=3, ref=12, will=7,
        str_score=1, dex_score=29, con_score=10,
        int_score=15, wis_score=13, cha_score=12,
        attacks=[
            {"name": "shock", "attack_bonus": 16, "damage_dice": "2d8",
             "damage_type": "electricity"},
        ],
        cr=6.0,
        special_qualities=["darkvision_60", "immunity_magic",
                           "natural_invisibility", "glowing"],
    ),

    "hill_giant": CreatureStatBlock(
        creature_id="hill_giant", name="Hill Giant",
        creature_type="giant", size="large",
        hp=102, ac=20, bab=9,
        fort=12, ref=3, will=4,
        str_score=25, dex_score=8, con_score=19,
        int_score=6, wis_score=10, cha_score=7,
        attacks=[
            {"name": "greatclub", "attack_bonus": 16, "damage_dice": "2d8+10",
             "damage_type": "bludgeoning"},
        ],
        cr=7.0,
        special_qualities=["low_light_vision", "rock_catching", "rock_throwing"],
    ),

    "medusa": CreatureStatBlock(
        creature_id="medusa", name="Medusa",
        creature_type="monstrous_humanoid", size="medium",
        hp=45, ac=15, bab=7,
        fort=4, ref=7, will=6,
        str_score=10, dex_score=15, con_score=14,
        int_score=12, wis_score=13, cha_score=15,
        attacks=[
            {"name": "shortbow", "attack_bonus": 9, "damage_dice": "1d6",
             "damage_type": "piercing"},
            {"name": "snake_bite", "attack_bonus": 2, "damage_dice": "1d4",
             "damage_type": "piercing"},
        ],
        cr=7.0,
        special_qualities=["darkvision_60", "petrifying_gaze", "poison_snakes"],
    ),

    "fire_giant": CreatureStatBlock(
        creature_id="fire_giant", name="Fire Giant",
        creature_type="giant", size="large",
        hp=142, ac=23, bab=11,
        fort=14, ref=4, will=9,
        str_score=31, dex_score=9, con_score=21,
        int_score=10, wis_score=14, cha_score=11,
        attacks=[
            {"name": "greatsword", "attack_bonus": 21, "damage_dice": "3d6+15",
             "damage_type": "slashing"},
        ],
        cr=10.0,
        special_qualities=["darkvision_60", "low_light_vision",
                           "immunity_fire", "rock_catching", "rock_throwing"],
    ),
}
