"""Skill check resolution for D&D 3.5e PHB Chapter 4.

This module resolves skill checks and opposed skill checks per D&D 3.5e rules:
- Standard checks (roll vs DC)
- Opposed checks (roll vs roll)
- Armor check penalties
- Trained-only skill enforcement
- Skill synergy bonuses (PHB p.65)

Reference: Player's Handbook 3.5e, Chapter 4 (Skills)
"""

from dataclasses import dataclass
from typing import Optional

from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF
from aidm.schemas.skills import SKILLS, SkillDefinition


# WO-ENGINE-AH-WO1: Skill-bonus feat table (PHB p.91-102)
# Each feat grants +2 untyped bonus to two specific skills. Untyped = stacks with everything.
# All 12 PHB skill-bonus feats wired. Authority: RAW (PHB names no bonus type for these).
_SKILL_BONUS_FEATS: dict = {
    "alertness":       ("listen",             "spot"),
    "athletic":        ("climb",              "swim"),
    "acrobatic":       ("jump",               "tumble"),
    "deceitful":       ("bluff",              "forgery"),
    "deft_hands":      ("sleight_of_hand",    "use_rope"),
    "diligent":        ("appraise",           "decipher_script"),
    "investigator":    ("gather_information", "search"),
    "negotiator":      ("diplomacy",          "sense_motive"),
    "nimble_fingers":  ("disable_device",     "open_lock"),
    "persuasive":      ("bluff",              "intimidate"),
    "self_sufficient": ("heal",               "survival"),
    "stealthy":        ("hide",               "move_silently"),
}


def _get_feat_skill_bonus(actor_feats: list, target_skill_id: str) -> int:
    """Sum all applicable skill-bonus feat bonuses for target_skill_id.

    Args:
        actor_feats: List of feat IDs the actor has (EF.FEATS)
        target_skill_id: The skill being checked

    Returns:
        Total untyped bonus from skill-bonus feats (PHB p.91-102, untyped, stacks)
    """
    total = 0
    for feat_id in actor_feats:
        skills = _SKILL_BONUS_FEATS.get(feat_id)
        if skills and target_skill_id in skills:
            total += 2
    return total


# WO-ENGINE-SKILL-SYNERGY-001: Skill synergy bonuses (PHB p.65)
# 5+ ranks in source skill → +2 circumstance bonus to target skill.
# Source: PHB Table 4-5, p.65. All entries wired.
# FINDING-ENGINE-SYNERGY-CONTEXT-001: PHB specifies three synergies apply only in
# specific contexts (knowledge_dungeoneering→survival only underground;
# knowledge_planes→survival only on other planes; search→survival only for tracking).
# Engine applies them universally — no context tracking exists. Known gap.
_SKILL_SYNERGIES: dict = {
    # source_skill: [(target_skill, bonus), ...]
    "bluff":                    [("disguise", 2), ("diplomacy", 2), ("intimidate", 2), ("sleight_of_hand", 2)],
    "escape_artist":            [("use_rope", 2)],
    "handle_animal":            [("ride", 2), ("wild_empathy", 2)],
    "jump":                     [("tumble", 2)],
    "knowledge_arcana":         [("spellcraft", 2)],
    "knowledge_architecture":   [("search", 2)],
    "knowledge_dungeoneering":  [("survival", 2)],   # underground only — FINDING-ENGINE-SYNERGY-CONTEXT-001
    "knowledge_geography":      [("survival", 2), ("navigate", 2)],
    "knowledge_history":        [("bardic_knowledge", 2)],
    "knowledge_local":          [("gather_information", 2)],
    "knowledge_nature":         [("survival", 2), ("handle_animal", 2)],
    "knowledge_nobility":       [("diplomacy", 2)],
    "knowledge_planes":         [("survival", 2)],   # other planes only — FINDING-ENGINE-SYNERGY-CONTEXT-001
    "knowledge_religion":       [("turn_undead", 2)],
    "search":                   [("survival", 2)],   # tracking only — FINDING-ENGINE-SYNERGY-CONTEXT-001
    "sense_motive":             [("diplomacy", 2)],
    "spellcraft":               [("use_magic_device", 2)],
    "survival":                 [("knowledge_nature", 2)],
    "tumble":                   [("balance", 2), ("jump", 2)],
    "use_magic_device":         [("spellcraft", 2)],
    "use_rope":                 [("climb", 2), ("escape_artist", 2)],
}


def _get_synergy_bonus(actor_ranks: dict, target_skill_id: str) -> int:
    """Sum all applicable synergy bonuses for target_skill_id.

    Args:
        actor_ranks: dict mapping skill_id → rank count (EF.SKILL_RANKS)
        target_skill_id: The skill being checked

    Returns:
        Total synergy bonus from all qualifying source skills (PHB p.65)
    """
    total = 0
    for source_skill, targets in _SKILL_SYNERGIES.items():
        if actor_ranks.get(source_skill, 0) >= 5:
            for target, bonus in targets:
                if target == target_skill_id:
                    total += bonus
    return total


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
    rng: RNGProvider,
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

    # WO-ENGINE-DAZZLED-CONDITION-001: -1 penalty to Spot checks when dazzled (PHB p.310)
    _entity_conditions = entity.get(EF.CONDITIONS, {})
    if skill_id == "spot" and "dazzled" in _entity_conditions:
        total -= 1

    # WO-ENGINE-SKILL-SYNERGY-001: Apply synergy bonuses (PHB p.65)
    # 5+ ranks in a source skill → +2 circumstance bonus on synergistic target skills.
    # Circumstance bonuses from different sources stack (PHB — confirmed KERNEL-14).
    _actor_ranks = entity.get(EF.SKILL_RANKS, {})
    total += _get_synergy_bonus(_actor_ranks, skill_id)

    # WO-ENGINE-DRUID-SAVES-FEATURES-001: RACIAL_SKILL_BONUS dict (PHB p.36 Nature Sense)
    # Also used by racial bonuses set at chargen. Dict: {skill_id: bonus_int}.
    # Untyped bonuses — stacks with ranks, synergy, and circumstance.
    _skill_bonus_dict = entity.get(EF.RACIAL_SKILL_BONUS, {}) or {}
    _racial_skill_bonus = _skill_bonus_dict.get(skill_id, 0)
    total += _racial_skill_bonus

    # WO-ENGINE-AH-WO1: Skill-bonus feat bonuses (PHB p.91-102, untyped, stacks with everything)
    # Alertness +2 Listen/Spot, Athletic +2 Climb/Swim, etc. See _SKILL_BONUS_FEATS table.
    _actor_feats = entity.get(EF.FEATS, []) or []
    total += _get_feat_skill_bonus(_actor_feats, skill_id)

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
    rng: RNGProvider,
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


def resolve_demoralize(world_state, intent, next_event_id: int, rng: RNGProvider):
    """Resolve Intimidate — Demoralize Opponent (PHB p.76).

    Standard action opposed check:
    - Actor: d20 + Intimidate bonus (CHA mod + skill ranks)
    - Target DC: target HD + WIS mod

    On success: SHAKEN for 1 round + 1 round per 5 by which roll beats DC.
    On failure: skill_check_failed event, no condition applied.
    PHB p.76: already-Shaken target does not become Frightened — duration refreshed.

    WO-ENGINE-INTIMIDATE-DEMORALIZE-001
    """
    from copy import deepcopy
    from aidm.core.event_log import Event
    from aidm.schemas.conditions import create_shaken_condition
    from aidm.schemas.entity_fields import EF

    actor = world_state.entities.get(intent.actor_id, {})
    target = world_state.entities.get(intent.target_id, {})
    entities = deepcopy(world_state.entities)
    events = []

    # Actor roll: d20 + CHA mod + Intimidate ranks
    combat_rng = rng.stream("combat")
    d20_roll = combat_rng.randint(1, 20)
    cha_mod = actor.get(EF.CHA_MOD, 0)
    intimidate_ranks = actor.get(EF.SKILL_RANKS, {}).get("intimidate", 0)
    intimidate_total = d20_roll + cha_mod + intimidate_ranks

    # Target DC: HD + WIS mod
    target_hd = target.get(EF.HD_COUNT, 1)
    target_wis_mod = target.get(EF.WIS_MOD, 0)
    dc = target_hd + target_wis_mod

    if intimidate_total >= dc:
        margin = intimidate_total - dc
        duration = 1 + (margin // 5)

        # Apply SHAKEN — refresh if already present (PHB p.76: does not escalate to Frightened)
        shaken_instance = create_shaken_condition(
            source="intimidate_demoralize",
            applied_at_event_id=next_event_id,
        )
        shaken_dict = shaken_instance.to_dict()
        shaken_dict["duration_rounds"] = duration

        if EF.CONDITIONS not in entities[intent.target_id]:
            entities[intent.target_id][EF.CONDITIONS] = {}
        entities[intent.target_id][EF.CONDITIONS]["shaken"] = shaken_dict

        events.append(Event(
            event_id=next_event_id,
            event_type="condition_applied",
            timestamp=0.0,
            payload={
                "target_id": intent.target_id,
                "condition": "shaken",
                "duration_rounds": duration,
                "source": "intimidate_demoralize",
                "actor_id": intent.actor_id,
                "roll": intimidate_total,
                "dc": dc,
            },
            citations=["PHB p.76"],
        ))
    else:
        events.append(Event(
            event_id=next_event_id,
            event_type="skill_check_failed",
            timestamp=0.0,
            payload={
                "actor_id": intent.actor_id,
                "skill": "intimidate",
                "roll": intimidate_total,
                "dc": dc,
                "target_id": intent.target_id,
            },
        ))

    from aidm.core.state import WorldState
    new_world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat,
    )
    return new_world_state, next_event_id + len(events), events
