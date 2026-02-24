"""Barbarian Rage runtime resolver — WO-ENGINE-BARBARIAN-RAGE-001.

Implements Rage activation, per-turn tick, and end-of-rage fatigue.
PHB p.25: +4 Str, +4 Con, +2 Will, -2 AC for (3 + CON modifier) rounds.
After rage: FATIGUED until rest.
"""

from copy import deepcopy
from typing import List, Optional, Tuple, Any, Dict

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


def _has_rage_feature(actor: dict) -> bool:
    """True if entity is a Barbarian (has barbarian class level) or has rage feature."""
    # Primary check: CLASS_LEVELS dict contains "barbarian"
    class_levels = actor.get(EF.CLASS_LEVELS, {}) or {}
    if isinstance(class_levels, dict) and class_levels.get("barbarian", 0) >= 1:
        return True
    # Fallback: explicit class_features list (hand-crafted entities in tests)
    class_features = actor.get("class_features", []) or []
    return any(str(f).startswith("rage_") and str(f).endswith("_per_day") for f in class_features)


def _get_max_rage_uses(actor: dict) -> int:
    """Compute max rage uses per day from Barbarian level (PHB p.25 Table 3-4).

    Level 1-3: 1/day, 4-7: 2/day, 8-11: 3/day, 12-15: 4/day, 16-19: 5/day, 20: 6/day.
    Also checks explicit class_features list as fallback.
    """
    class_levels = actor.get(EF.CLASS_LEVELS, {}) or {}
    barb_level = 0
    if isinstance(class_levels, dict):
        barb_level = class_levels.get("barbarian", 0)

    if barb_level >= 1:
        if barb_level >= 20:
            return 6
        elif barb_level >= 16:
            return 5
        elif barb_level >= 12:
            return 4
        elif barb_level >= 8:
            return 3
        elif barb_level >= 4:
            return 2
        else:
            return 1

    # Fallback: parse class_features list
    class_features = actor.get("class_features", []) or []
    for f in class_features:
        s = str(f)
        if s.startswith("rage_") and s.endswith("_per_day"):
            try:
                return int(s.split("_")[1])
            except (IndexError, ValueError):
                pass
    return 0


def validate_rage(actor: dict, world_state: WorldState) -> Optional[str]:
    """Validate rage activation preconditions.

    Returns error reason string, or None if valid.
    """
    if not _has_rage_feature(actor):
        return "not_a_barbarian"
    if actor.get(EF.RAGE_ACTIVE, False):
        return "already_raging"
    if actor.get(EF.FATIGUED, False):
        return "already_fatigued"
    if actor.get(EF.RAGE_USES_REMAINING, 0) <= 0:
        return "no_rage_uses"
    return None


def activate_rage(
    actor_id: str,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Activate Barbarian Rage.

    Applies bonuses to TEMPORARY_MODIFIERS, sets RAGE_ACTIVE, decrements uses.
    Duration = 3 + base CON modifier (computed before rage-enhanced CON).

    Returns (events, updated_world_state).
    """
    events: List[Event] = []
    entities = deepcopy(world_state.entities)
    actor = entities[actor_id]

    con_mod = actor.get(EF.CON_MOD, 0)
    rage_rounds = max(1, 3 + con_mod)  # PHB p.25: minimum 1 round
    uses_before = actor.get(EF.RAGE_USES_REMAINING, 0)
    uses_after = max(0, uses_before - 1)

    # Apply rage modifiers to TEMPORARY_MODIFIERS
    temp_mods = dict(actor.get(EF.TEMPORARY_MODIFIERS, {}) or {})
    temp_mods["rage_str_bonus"] = 4
    temp_mods["rage_con_bonus"] = 4
    temp_mods["rage_will_bonus"] = 2
    temp_mods["rage_ac_penalty"] = -2

    actor[EF.TEMPORARY_MODIFIERS] = temp_mods
    actor[EF.RAGE_ACTIVE] = True
    actor[EF.RAGE_ROUNDS_REMAINING] = rage_rounds
    actor[EF.RAGE_USES_REMAINING] = uses_after

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )

    events.append(Event(
        event_id=next_event_id,
        event_type="rage_start",
        timestamp=timestamp,
        payload={
            "actor_id": actor_id,
            "rage_rounds_total": rage_rounds,
            "rage_uses_remaining": uses_after,
            "str_bonus": 4,
            "con_bonus": 4,
            "will_bonus": 2,
            "ac_penalty": -2,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 25}],
    ))

    return events, world_state


def end_rage(
    actor_id: str,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
    reason: str = "expired",
) -> Tuple[List[Event], WorldState]:
    """End Barbarian Rage and apply fatigue.

    Removes rage TEMPORARY_MODIFIERS, sets FATIGUED, adds fatigue penalties.

    Returns (events, updated_world_state).
    """
    events: List[Event] = []
    entities = deepcopy(world_state.entities)
    actor = entities[actor_id]

    # Remove rage modifiers
    temp_mods = dict(actor.get(EF.TEMPORARY_MODIFIERS, {}) or {})
    for key in ("rage_str_bonus", "rage_con_bonus", "rage_will_bonus", "rage_ac_penalty"):
        temp_mods.pop(key, None)

    # Apply fatigue penalties (PHB p.25: -2 Str, -2 Dex after rage)
    temp_mods["fatigued_str_penalty"] = -2
    temp_mods["fatigued_dex_penalty"] = -2

    actor[EF.TEMPORARY_MODIFIERS] = temp_mods
    actor[EF.RAGE_ACTIVE] = False
    actor[EF.RAGE_ROUNDS_REMAINING] = 0
    actor[EF.FATIGUED] = True

    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )

    events.append(Event(
        event_id=next_event_id,
        event_type="rage_end",
        timestamp=timestamp,
        payload={
            "actor_id": actor_id,
            "reason": reason,
            "fatigued": True,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 25}],
    ))

    return events, world_state


def tick_rage(
    actor_id: str,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Decrement RAGE_ROUNDS_REMAINING at end of actor's turn while raging.

    Calls end_rage() when rounds reach 0.

    Returns (events, updated_world_state).
    """
    actor = world_state.entities.get(actor_id, {})
    if not actor.get(EF.RAGE_ACTIVE, False):
        return [], world_state

    rounds_left = actor.get(EF.RAGE_ROUNDS_REMAINING, 0)
    new_rounds = max(0, rounds_left - 1)

    if new_rounds <= 0:
        return end_rage(actor_id, world_state, next_event_id, timestamp, reason="expired")

    # Just decrement
    entities = deepcopy(world_state.entities)
    entities[actor_id][EF.RAGE_ROUNDS_REMAINING] = new_rounds
    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )
    return [], world_state
