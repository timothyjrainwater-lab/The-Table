"""Skill definitions for D&D 3.5e PHB Chapter 4.

This module defines the 7 combat-adjacent skills implemented in WO-035:
- Tumble (p.84) — Avoid AoO when moving through threatened squares
- Concentration (p.69) — Maintain spells when taking damage
- Hide (p.76) — Avoid detection (opposed vs Spot)
- Move Silently (p.79) — Approach without detection (opposed vs Listen)
- Spot (p.83) — Detect hidden creatures
- Listen (p.78) — Hear approaching enemies
- Balance (p.67) — Move on difficult surfaces

Reference: Player's Handbook 3.5e, Chapter 4 (Skills)
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
    TUMBLE: ClassVar[str] = "tumble"
    CONCENTRATION: ClassVar[str] = "concentration"
    HIDE: ClassVar[str] = "hide"
    MOVE_SILENTLY: ClassVar[str] = "move_silently"
    SPOT: ClassVar[str] = "spot"
    LISTEN: ClassVar[str] = "listen"
    BALANCE: ClassVar[str] = "balance"


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
