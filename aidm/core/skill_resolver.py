"""Skill check resolution for D&D 3.5e PHB Chapter 4.

This module resolves skill checks and opposed skill checks per D&D 3.5e rules:
- Standard checks (roll vs DC)
- Opposed checks (roll vs roll)
- Armor check penalties
- Trained-only skill enforcement

Reference: Player's Handbook 3.5e, Chapter 4 (Skills)
"""

from dataclasses import dataclass
from typing import Optional

from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.skills import SKILLS, SkillDefinition


@dataclass(frozen=True)
class SkillCheckResult:
    """Result of a skill check against a fixed DC.

    Attributes:
        success: Whether the check succeeded
        total: Total check result (d20 + modifiers)
        dc: Target DC
        d20_roll: The d20 roll value
        ability_modifier: Ability modifier contribution
        skill_ranks: Skill ranks contribution
        circumstance_modifier: Circumstance modifier contribution
        armor_check_penalty: Armor check penalty applied (negative)
        skill_id: Skill being checked
        skill_name: Display name of skill
    """
    success: bool
    total: int
    dc: int
    d20_roll: int
    ability_modifier: int
    skill_ranks: int
    circumstance_modifier: int
    armor_check_penalty: int
    skill_id: str
    skill_name: str


@dataclass(frozen=True)
class OpposedCheckResult:
    """Result of an opposed skill check (actor vs opponent).

    Attributes:
        actor_wins: Whether the actor won the opposed check
        actor_total: Actor's check total
        opponent_total: Opponent's check total
        actor_d20: Actor's d20 roll
        opponent_d20: Opponent's d20 roll
        actor_skill: Actor's skill ID
        opponent_skill: Opponent's skill ID
        tie: Whether the check was a tie (ties favor the active checker)
    """
    actor_wins: bool
    actor_total: int
    opponent_total: int
    actor_d20: int
    opponent_d20: int
    actor_skill: str
    opponent_skill: str
    tie: bool


def _get_ability_modifier(entity: dict, ability: str) -> int:
    """Get ability modifier from entity dict.

    Args:
        entity: Entity dict
        ability: Ability score name ("dex", "con", "wis", "str", "int", "cha")

    Returns:
        Ability modifier value
    """
    # Map ability name to EF field
    ability_field_map = {
        "dex": EF.DEX_MOD,
        "con": EF.CON_MOD,
        "wis": EF.WIS_MOD,
        "str": EF.STR_MOD,
        "int": EF.INT_MOD,
        "cha": EF.CHA_MOD,
    }

    field = ability_field_map.get(ability)
    if field is None:
        return 0

    return entity.get(field, 0)


def _get_skill_ranks(entity: dict, skill_id: str) -> int:
    """Get skill ranks from entity dict.

    Args:
        entity: Entity dict
        skill_id: Skill identifier

    Returns:
        Number of ranks in the skill (0 if not trained)
    """
    skill_ranks_dict = entity.get(EF.SKILL_RANKS, {})
    return skill_ranks_dict.get(skill_id, 0)


def _get_armor_check_penalty(entity: dict) -> int:
    """Get armor check penalty from entity dict.

    Args:
        entity: Entity dict

    Returns:
        Armor check penalty value (default 0 if not present)
    """
    return entity.get(EF.ARMOR_CHECK_PENALTY, 0)


def resolve_skill_check(
    entity: dict,
    skill_id: str,
    dc: int,
    rng: RNGManager,
    circumstance_modifier: int = 0,
) -> SkillCheckResult:
    """Resolve a skill check against a fixed DC.

    Formula: d20 + ability_mod + skill_ranks + circumstance_modifier - armor_check_penalty

    Args:
        entity: Entity making the skill check
        skill_id: Skill identifier (e.g., "tumble", "concentration")
        dc: Target DC
        rng: RNG manager for d20 roll
        circumstance_modifier: Circumstance modifier (cover, terrain, magic, etc.)

    Returns:
        SkillCheckResult with success status and breakdown

    Raises:
        KeyError: If skill_id not found in skill registry
        ValueError: If entity attempts to use trained-only skill without ranks
    """
    skill_def = SKILLS[skill_id]

    # Check trained-only restriction
    ranks = _get_skill_ranks(entity, skill_id)
    if skill_def.trained_only and ranks == 0:
        raise ValueError(
            f"Skill '{skill_def.name}' is trained-only and entity has 0 ranks"
        )

    # Roll d20
    combat_rng = rng.stream("combat")
    d20_roll = combat_rng.randint(1, 20)

    # Get components
    ability_mod = _get_ability_modifier(entity, skill_def.key_ability)
    acp = 0
    if skill_def.armor_check_penalty:
        acp = _get_armor_check_penalty(entity)

    # Total = d20 + ability + ranks + circumstance - armor_check_penalty
    total = d20_roll + ability_mod + ranks + circumstance_modifier - acp

    return SkillCheckResult(
        success=(total >= dc),
        total=total,
        dc=dc,
        d20_roll=d20_roll,
        ability_modifier=ability_mod,
        skill_ranks=ranks,
        circumstance_modifier=circumstance_modifier,
        armor_check_penalty=acp,
        skill_id=skill_id,
        skill_name=skill_def.name,
    )


def resolve_opposed_check(
    actor: dict,
    opponent: dict,
    actor_skill: str,
    opponent_skill: str,
    rng: RNGManager,
    actor_circumstance: int = 0,
    opponent_circumstance: int = 0,
) -> OpposedCheckResult:
    """Resolve an opposed skill check (e.g., Hide vs Spot).

    Both sides roll d20 + modifiers. Higher total wins. Ties favor the active checker (actor).

    Args:
        actor: Entity making the active check (e.g., hiding)
        opponent: Entity making the opposing check (e.g., spotting)
        actor_skill: Actor's skill ID
        opponent_skill: Opponent's skill ID
        rng: RNG manager for d20 rolls
        actor_circumstance: Circumstance modifier for actor
        opponent_circumstance: Circumstance modifier for opponent

    Returns:
        OpposedCheckResult with winner and breakdown

    Raises:
        KeyError: If skill_id not found in skill registry
        ValueError: If entity attempts to use trained-only skill without ranks
    """
    actor_skill_def = SKILLS[actor_skill]
    opponent_skill_def = SKILLS[opponent_skill]

    # Check trained-only restrictions
    actor_ranks = _get_skill_ranks(actor, actor_skill)
    opponent_ranks = _get_skill_ranks(opponent, opponent_skill)

    if actor_skill_def.trained_only and actor_ranks == 0:
        raise ValueError(
            f"Skill '{actor_skill_def.name}' is trained-only and actor has 0 ranks"
        )
    if opponent_skill_def.trained_only and opponent_ranks == 0:
        raise ValueError(
            f"Skill '{opponent_skill_def.name}' is trained-only and opponent has 0 ranks"
        )

    # Roll d20 for both
    combat_rng = rng.stream("combat")
    actor_d20 = combat_rng.randint(1, 20)
    opponent_d20 = combat_rng.randint(1, 20)

    # Actor total
    actor_ability_mod = _get_ability_modifier(actor, actor_skill_def.key_ability)
    actor_acp = 0
    if actor_skill_def.armor_check_penalty:
        actor_acp = _get_armor_check_penalty(actor)
    actor_total = actor_d20 + actor_ability_mod + actor_ranks + actor_circumstance - actor_acp

    # Opponent total
    opponent_ability_mod = _get_ability_modifier(opponent, opponent_skill_def.key_ability)
    opponent_acp = 0
    if opponent_skill_def.armor_check_penalty:
        opponent_acp = _get_armor_check_penalty(opponent)
    opponent_total = (
        opponent_d20 + opponent_ability_mod + opponent_ranks + opponent_circumstance - opponent_acp
    )

    # Winner: higher total wins, ties favor the actor (active checker)
    tie = (actor_total == opponent_total)
    actor_wins = (actor_total >= opponent_total)  # >= because ties favor actor

    return OpposedCheckResult(
        actor_wins=actor_wins,
        actor_total=actor_total,
        opponent_total=opponent_total,
        actor_d20=actor_d20,
        opponent_d20=opponent_d20,
        actor_skill=actor_skill,
        opponent_skill=opponent_skill,
        tie=tie,
    )
