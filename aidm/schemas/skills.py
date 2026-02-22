"""Skill definitions for D&D 3.5e PHB Chapter 4.

Complete PHB skill list (34 skills). Original 7 combat-adjacent skills from
WO-035; remaining 27 added by WO-CHARGEN-SKILLS-COMPLETE.

Reference: Player's Handbook 3.5e, Chapter 4 (Skills), Table 4-2 p.63
"""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class SkillDefinition:
    """Defines a D&D 3.5e skill with its properties.

    Attributes:
        skill_id: Unique identifier (lowercase, underscores)
        name: Display name
        key_ability: Ability score modifier used ("dex", "con", "wis", etc.)
        armor_check_penalty: Whether armor check penalty applies
        trained_only: Whether skill requires training (ranks > 0) to use
        phb_page: PHB page number for reference
    """
    skill_id: str
    name: str
    key_ability: str
    armor_check_penalty: bool
    trained_only: bool
    phb_page: int


# Skill ID constants
class SkillID:
    """Constants for skill IDs used throughout the system."""
    # Original 7 (WO-035)
    TUMBLE: ClassVar[str] = "tumble"
    CONCENTRATION: ClassVar[str] = "concentration"
    HIDE: ClassVar[str] = "hide"
    MOVE_SILENTLY: ClassVar[str] = "move_silently"
    SPOT: ClassVar[str] = "spot"
    LISTEN: ClassVar[str] = "listen"
    BALANCE: ClassVar[str] = "balance"
    # STR-based
    CLIMB: ClassVar[str] = "climb"
    JUMP: ClassVar[str] = "jump"
    SWIM: ClassVar[str] = "swim"
    # DEX-based
    ESCAPE_ARTIST: ClassVar[str] = "escape_artist"
    OPEN_LOCK: ClassVar[str] = "open_lock"
    RIDE: ClassVar[str] = "ride"
    SLEIGHT_OF_HAND: ClassVar[str] = "sleight_of_hand"
    USE_ROPE: ClassVar[str] = "use_rope"
    # INT-based
    APPRAISE: ClassVar[str] = "appraise"
    CRAFT: ClassVar[str] = "craft"
    DECIPHER_SCRIPT: ClassVar[str] = "decipher_script"
    DISABLE_DEVICE: ClassVar[str] = "disable_device"
    FORGERY: ClassVar[str] = "forgery"
    KNOWLEDGE_ARCANA: ClassVar[str] = "knowledge_arcana"
    KNOWLEDGE_DUNGEONEERING: ClassVar[str] = "knowledge_dungeoneering"
    KNOWLEDGE_NATURE: ClassVar[str] = "knowledge_nature"
    KNOWLEDGE_RELIGION: ClassVar[str] = "knowledge_religion"
    KNOWLEDGE_THE_PLANES: ClassVar[str] = "knowledge_the_planes"
    SEARCH: ClassVar[str] = "search"
    SPELLCRAFT: ClassVar[str] = "spellcraft"
    # WIS-based
    HEAL: ClassVar[str] = "heal"
    PROFESSION: ClassVar[str] = "profession"
    SENSE_MOTIVE: ClassVar[str] = "sense_motive"
    SURVIVAL: ClassVar[str] = "survival"
    # CHA-based
    BLUFF: ClassVar[str] = "bluff"
    DIPLOMACY: ClassVar[str] = "diplomacy"
    DISGUISE: ClassVar[str] = "disguise"
    GATHER_INFORMATION: ClassVar[str] = "gather_information"
    HANDLE_ANIMAL: ClassVar[str] = "handle_animal"
    INTIMIDATE: ClassVar[str] = "intimidate"
    PERFORM: ClassVar[str] = "perform"
    USE_MAGIC_DEVICE: ClassVar[str] = "use_magic_device"


# Skill registry (7 skills from WO-035)
SKILLS: dict[str, SkillDefinition] = {
    SkillID.TUMBLE: SkillDefinition(
        skill_id=SkillID.TUMBLE,
        name="Tumble",
        key_ability="dex",
        armor_check_penalty=True,
        trained_only=True,
        phb_page=84,
    ),
    SkillID.CONCENTRATION: SkillDefinition(
        skill_id=SkillID.CONCENTRATION,
        name="Concentration",
        key_ability="con",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=69,
    ),
    SkillID.HIDE: SkillDefinition(
        skill_id=SkillID.HIDE,
        name="Hide",
        key_ability="dex",
        armor_check_penalty=True,
        trained_only=False,
        phb_page=76,
    ),
    SkillID.MOVE_SILENTLY: SkillDefinition(
        skill_id=SkillID.MOVE_SILENTLY,
        name="Move Silently",
        key_ability="dex",
        armor_check_penalty=True,
        trained_only=False,
        phb_page=79,
    ),
    SkillID.SPOT: SkillDefinition(
        skill_id=SkillID.SPOT,
        name="Spot",
        key_ability="wis",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=83,
    ),
    SkillID.LISTEN: SkillDefinition(
        skill_id=SkillID.LISTEN,
        name="Listen",
        key_ability="wis",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=78,
    ),
    SkillID.BALANCE: SkillDefinition(
        skill_id=SkillID.BALANCE,
        name="Balance",
        key_ability="dex",
        armor_check_penalty=True,
        trained_only=False,
        phb_page=67,
    ),
    # --- STR-based (WO-CHARGEN-SKILLS-COMPLETE) ---
    SkillID.CLIMB: SkillDefinition(
        skill_id=SkillID.CLIMB,
        name="Climb",
        key_ability="str",
        armor_check_penalty=True,
        trained_only=False,
        phb_page=69,
    ),
    SkillID.JUMP: SkillDefinition(
        skill_id=SkillID.JUMP,
        name="Jump",
        key_ability="str",
        armor_check_penalty=True,
        trained_only=False,
        phb_page=77,
    ),
    SkillID.SWIM: SkillDefinition(
        skill_id=SkillID.SWIM,
        name="Swim",
        key_ability="str",
        armor_check_penalty=True,
        trained_only=False,
        phb_page=84,
    ),
    # --- DEX-based ---
    SkillID.ESCAPE_ARTIST: SkillDefinition(
        skill_id=SkillID.ESCAPE_ARTIST,
        name="Escape Artist",
        key_ability="dex",
        armor_check_penalty=True,
        trained_only=False,
        phb_page=73,
    ),
    SkillID.OPEN_LOCK: SkillDefinition(
        skill_id=SkillID.OPEN_LOCK,
        name="Open Lock",
        key_ability="dex",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=79,
    ),
    SkillID.RIDE: SkillDefinition(
        skill_id=SkillID.RIDE,
        name="Ride",
        key_ability="dex",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=80,
    ),
    SkillID.SLEIGHT_OF_HAND: SkillDefinition(
        skill_id=SkillID.SLEIGHT_OF_HAND,
        name="Sleight of Hand",
        key_ability="dex",
        armor_check_penalty=True,
        trained_only=True,
        phb_page=81,
    ),
    SkillID.USE_ROPE: SkillDefinition(
        skill_id=SkillID.USE_ROPE,
        name="Use Rope",
        key_ability="dex",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=86,
    ),
    # --- INT-based ---
    SkillID.APPRAISE: SkillDefinition(
        skill_id=SkillID.APPRAISE,
        name="Appraise",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=67,
    ),
    SkillID.CRAFT: SkillDefinition(
        skill_id=SkillID.CRAFT,
        name="Craft",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=70,
    ),
    SkillID.DECIPHER_SCRIPT: SkillDefinition(
        skill_id=SkillID.DECIPHER_SCRIPT,
        name="Decipher Script",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=71,
    ),
    SkillID.DISABLE_DEVICE: SkillDefinition(
        skill_id=SkillID.DISABLE_DEVICE,
        name="Disable Device",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=72,
    ),
    SkillID.FORGERY: SkillDefinition(
        skill_id=SkillID.FORGERY,
        name="Forgery",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=74,
    ),
    SkillID.KNOWLEDGE_ARCANA: SkillDefinition(
        skill_id=SkillID.KNOWLEDGE_ARCANA,
        name="Knowledge (Arcana)",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=78,
    ),
    SkillID.KNOWLEDGE_DUNGEONEERING: SkillDefinition(
        skill_id=SkillID.KNOWLEDGE_DUNGEONEERING,
        name="Knowledge (Dungeoneering)",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=78,
    ),
    SkillID.KNOWLEDGE_NATURE: SkillDefinition(
        skill_id=SkillID.KNOWLEDGE_NATURE,
        name="Knowledge (Nature)",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=78,
    ),
    SkillID.KNOWLEDGE_RELIGION: SkillDefinition(
        skill_id=SkillID.KNOWLEDGE_RELIGION,
        name="Knowledge (Religion)",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=78,
    ),
    SkillID.KNOWLEDGE_THE_PLANES: SkillDefinition(
        skill_id=SkillID.KNOWLEDGE_THE_PLANES,
        name="Knowledge (The Planes)",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=78,
    ),
    SkillID.SEARCH: SkillDefinition(
        skill_id=SkillID.SEARCH,
        name="Search",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=81,
    ),
    SkillID.SPELLCRAFT: SkillDefinition(
        skill_id=SkillID.SPELLCRAFT,
        name="Spellcraft",
        key_ability="int",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=82,
    ),
    # --- WIS-based ---
    SkillID.HEAL: SkillDefinition(
        skill_id=SkillID.HEAL,
        name="Heal",
        key_ability="wis",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=75,
    ),
    SkillID.PROFESSION: SkillDefinition(
        skill_id=SkillID.PROFESSION,
        name="Profession",
        key_ability="wis",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=80,
    ),
    SkillID.SENSE_MOTIVE: SkillDefinition(
        skill_id=SkillID.SENSE_MOTIVE,
        name="Sense Motive",
        key_ability="wis",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=81,
    ),
    SkillID.SURVIVAL: SkillDefinition(
        skill_id=SkillID.SURVIVAL,
        name="Survival",
        key_ability="wis",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=83,
    ),
    # --- CHA-based ---
    SkillID.BLUFF: SkillDefinition(
        skill_id=SkillID.BLUFF,
        name="Bluff",
        key_ability="cha",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=67,
    ),
    SkillID.DIPLOMACY: SkillDefinition(
        skill_id=SkillID.DIPLOMACY,
        name="Diplomacy",
        key_ability="cha",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=71,
    ),
    SkillID.DISGUISE: SkillDefinition(
        skill_id=SkillID.DISGUISE,
        name="Disguise",
        key_ability="cha",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=72,
    ),
    SkillID.GATHER_INFORMATION: SkillDefinition(
        skill_id=SkillID.GATHER_INFORMATION,
        name="Gather Information",
        key_ability="cha",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=74,
    ),
    SkillID.HANDLE_ANIMAL: SkillDefinition(
        skill_id=SkillID.HANDLE_ANIMAL,
        name="Handle Animal",
        key_ability="cha",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=74,
    ),
    SkillID.INTIMIDATE: SkillDefinition(
        skill_id=SkillID.INTIMIDATE,
        name="Intimidate",
        key_ability="cha",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=76,
    ),
    SkillID.PERFORM: SkillDefinition(
        skill_id=SkillID.PERFORM,
        name="Perform",
        key_ability="cha",
        armor_check_penalty=False,
        trained_only=False,
        phb_page=79,
    ),
    SkillID.USE_MAGIC_DEVICE: SkillDefinition(
        skill_id=SkillID.USE_MAGIC_DEVICE,
        name="Use Magic Device",
        key_ability="cha",
        armor_check_penalty=False,
        trained_only=True,
        phb_page=85,
    ),
}


def get_skill(skill_id: str) -> SkillDefinition:
    """Get skill definition by ID.

    Args:
        skill_id: Skill identifier

    Returns:
        SkillDefinition for the given skill

    Raises:
        KeyError: If skill_id not found in registry
    """
    return SKILLS[skill_id]
