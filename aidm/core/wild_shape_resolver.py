"""Wild Shape resolver for D&D 3.5e Druid Wild Shape rules.

Handles transformation into animal forms, stat application, and reversion.
"""

import math  # noqa: F401
from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF

# ---------------------------------------------------------------------------
# Form definitions
# ---------------------------------------------------------------------------

WILD_SHAPE_FORMS: Dict[str, dict] = {
    "wolf": {
        "str": 13,
        "dex": 15,
        "con": 15,
        "size": "medium",
        "natural_ac": 2,
        "attacks": [{"name": "bite", "damage": "1d6", "damage_type": "piercing"}],
    },
    "black_bear": {
        "str": 19,
        "dex": 13,
        "con": 15,
        "size": "medium",
        "natural_ac": 4,
        "attacks": [
            {"name": "claw", "damage": "1d4", "damage_type": "slashing"},
            {"name": "bite", "damage": "1d6", "damage_type": "piercing"},
        ],
    },
    "riding_dog": {
        "str": 13,
        "dex": 15,
        "con": 15,
        "size": "medium",
        "natural_ac": 2,
        "attacks": [{"name": "bite", "damage": "1d6", "damage_type": "piercing"}],
    },
    "eagle": {
        "str": 10,
        "dex": 15,
        "con": 12,
        "size": "small",
        "natural_ac": 1,
        "attacks": [{"name": "talon", "damage": "1d4", "damage_type": "slashing"}],
    },
    "constrictor_snake": {
        "str": 15,
        "dex": 17,
        "con": 13,
        "size": "medium",
        "natural_ac": 3,
        "attacks": [{"name": "bite", "damage": "1d3", "damage_type": "piercing"}],
    },
    "crocodile": {
        "str": 15,
        "dex": 10,
        "con": 13,
        "size": "medium",
        "natural_ac": 5,
        "attacks": [{"name": "bite", "damage": "1d8", "damage_type": "piercing"}],
    },
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _ability_modifier(score: int) -> int:
    """Return the D&D 3.5e ability modifier for a given score."""
    return (score - 10) // 2


def _has_wild_shape_feature(actor: dict) -> bool:
    """Return True if the actor has at least 4 levels of Druid (Wild Shape unlock)."""
    class_levels: dict = actor.get(EF.CLASS_LEVELS, {})
    return class_levels.get("druid", 0) >= 4


def _get_druid_level(actor: dict) -> int:
    """Return the actor's Druid class level (0 if none)."""
    return actor.get(EF.CLASS_LEVELS, {}).get("druid", 0)


def _get_wild_shape_uses(druid_level: int) -> int:
    """Return the maximum Wild Shape uses per day for the given Druid level."""
    if druid_level < 4:
        return 0
    return max(1, 1 + (druid_level - 4) // 2)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_wild_shape(
    actor: dict,
    form: str,
    world_state: WorldState,
) -> Optional[str]:
    """Validate a Wild Shape request.

    Returns an error reason string on failure, or None if the request is valid.
    """
    if not _has_wild_shape_feature(actor):
        return "not_a_druid"
    if actor.get(EF.WILD_SHAPE_ACTIVE, False):
        return "already_transformed"
    if actor.get(EF.WILD_SHAPE_USES_REMAINING, 0) <= 0:
        return "no_wild_shape_uses"
    if form not in WILD_SHAPE_FORMS:
        return "unsupported_form"
    return None


# ---------------------------------------------------------------------------
# Resolve Wild Shape (transform)
# ---------------------------------------------------------------------------


def resolve_wild_shape(
    intent: dict,
    world_state: WorldState,
    next_event_id: int,
    timestamp: str,
) -> Tuple[List[Event], WorldState]:
    """Apply Wild Shape transformation to the actor.

    Returns a list of events and the mutated WorldState.
    """
    events: List[Event] = []
    ws = deepcopy(world_state)

    actor_id: str = intent.actor_id
    form: str = intent.form
    actor: dict = ws.entities[actor_id]

    error = validate_wild_shape(actor, form, ws)
    if error:
        events.append(
            Event(
                event_id=next_event_id,
                timestamp=timestamp,
                event_type="intent_validation_failed",
                payload={"actor_id": actor_id, "intent": "wild_shape", "reason": error},
            )
        )
        return events, ws

    druid_level = _get_druid_level(actor)
    form_data = WILD_SHAPE_FORMS[form]

    # --- Save original stats ---
    saved = {
        "str_mod": actor.get(EF.STR_MOD, 0),
        "dex_mod": actor.get(EF.DEX_MOD, 0),
        "con_mod": actor.get(EF.CON_MOD, 0),
        "ac": actor.get(EF.AC, 10),
        "hp_max": actor.get(EF.HP_MAX, 1),
        "hp_current": actor.get(EF.HP_CURRENT, 1),
        "size_category": actor.get(EF.SIZE_CATEGORY, "medium"),
    }
    actor[EF.WILD_SHAPE_SAVED_STATS] = saved

    # --- Compute new ability modifiers ---
    new_str_mod = _ability_modifier(form_data["str"])
    new_dex_mod = _ability_modifier(form_data["dex"])
    new_con_mod = _ability_modifier(form_data["con"])
    natural_ac = form_data["natural_ac"]

    # --- Apply new stats ---
    actor[EF.STR_MOD] = new_str_mod
    actor[EF.DEX_MOD] = new_dex_mod
    actor[EF.CON_MOD] = new_con_mod
    actor[EF.AC] = 10 + natural_ac + new_dex_mod
    actor[EF.SIZE_CATEGORY] = form_data["size"]

    # PHB p.37: HP_MAX adjusts by CON_mod delta × druid level
    old_con_mod = saved.get("con_mod", 0)
    saved_hp_max = saved.get("hp_max", 1)
    current_hp = actor.get(EF.HP_CURRENT, saved_hp_max)
    damage_taken = max(0, saved_hp_max - current_hp)

    con_delta = new_con_mod - old_con_mod
    new_hp_max = max(1, saved_hp_max + con_delta * druid_level)
    new_hp_current = max(1, new_hp_max - damage_taken)

    actor[EF.HP_MAX] = new_hp_max
    actor[EF.HP_CURRENT] = new_hp_current

    # --- Wild Shape bookkeeping ---
    uses_remaining = actor.get(EF.WILD_SHAPE_USES_REMAINING, 0) - 1
    actor[EF.WILD_SHAPE_ACTIVE] = True
    actor[EF.WILD_SHAPE_FORM] = form
    actor[EF.WILD_SHAPE_USES_REMAINING] = uses_remaining
    actor[EF.WILD_SHAPE_HOURS_REMAINING] = druid_level
    actor[EF.WILD_SHAPE_ROUNDS_REMAINING] = druid_level * 10  # combat proxy (WO-ENGINE-WILDSHAPE-DURATION-001)
    actor[EF.EQUIPMENT_MELDED] = True
    actor[EF.NATURAL_ATTACKS] = list(form_data["attacks"])

    events.append(
        Event(
            event_id=next_event_id,
            timestamp=timestamp,
            event_type="wild_shape_start",
            payload={
                "actor_id": actor_id,
                "form": form,
                "uses_remaining": uses_remaining,
                "new_str": form_data["str"],
                "new_dex": form_data["dex"],
                "new_con": form_data["con"],
                "new_natural_ac": natural_ac,
            },
        )
    )
    return events, ws


# ---------------------------------------------------------------------------
# Resolve Revert Form
# ---------------------------------------------------------------------------


def resolve_revert_form(
    intent: dict,
    world_state: WorldState,
    next_event_id: int,
    timestamp: str,
) -> Tuple[List[Event], WorldState]:
    """Revert the actor from Wild Shape back to their original form.

    Returns a list of events and the mutated WorldState.
    """
    events: List[Event] = []
    ws = deepcopy(world_state)

    actor_id: str = intent.actor_id
    actor: dict = ws.entities[actor_id]

    if not actor.get(EF.WILD_SHAPE_ACTIVE, False):
        events.append(
            Event(
                event_id=next_event_id,
                timestamp=timestamp,
                event_type="intent_validation_failed",
                payload={
                    "actor_id": actor_id,
                    "intent": "revert_form",
                    "reason": "not_transformed",
                },
            )
        )
        return events, ws

    form_was: str = actor.get(EF.WILD_SHAPE_FORM, "")

    # --- Restore saved stats ---
    saved: dict = actor.get(EF.WILD_SHAPE_SAVED_STATS) or {}

    restored_str_mod = saved.get("str_mod", 0)
    restored_dex_mod = saved.get("dex_mod", 0)
    restored_con_mod = saved.get("con_mod", 0)
    restored_ac = saved.get("ac", 10)
    restored_hp_max = saved.get("hp_max", 1)
    restored_size = saved.get("size_category", "medium")

    actor[EF.STR_MOD] = restored_str_mod
    actor[EF.DEX_MOD] = restored_dex_mod
    actor[EF.CON_MOD] = restored_con_mod
    actor[EF.AC] = restored_ac
    actor[EF.HP_MAX] = restored_hp_max
    actor[EF.HP_CURRENT] = min(actor.get(EF.HP_CURRENT, 1), restored_hp_max)
    actor[EF.SIZE_CATEGORY] = restored_size

    # --- Clear Wild Shape state ---
    actor[EF.WILD_SHAPE_ACTIVE] = False
    actor[EF.WILD_SHAPE_FORM] = ""
    actor[EF.WILD_SHAPE_SAVED_STATS] = {}
    actor[EF.WILD_SHAPE_HOURS_REMAINING] = 0
    actor[EF.WILD_SHAPE_ROUNDS_REMAINING] = 0
    actor[EF.EQUIPMENT_MELDED] = False
    actor[EF.NATURAL_ATTACKS] = []

    events.append(
        Event(
            event_id=next_event_id,
            timestamp=timestamp,
            event_type="wild_shape_end",
            payload={
                "actor_id": actor_id,
                "form_was": form_was,
                "restored_str_mod": restored_str_mod,
                "restored_dex_mod": restored_dex_mod,
                "restored_con_mod": restored_con_mod,
            },
        )
    )
    return events, ws


# ---------------------------------------------------------------------------
# Tick Wild Shape Duration (WO-ENGINE-WILDSHAPE-DURATION-001)
# ---------------------------------------------------------------------------


def tick_wild_shape_duration(
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Decrement Wild Shape round counter for all transformed druids.

    Called at round-end by play_loop.py. When WILD_SHAPE_ROUNDS_REMAINING
    reaches 0, triggers auto-revert via resolve_revert_form().

    PHB p.37: Wild Shape lasts druid_level hours. This function uses
    druid_level * 10 rounds as a combat-session proxy (no real-time
    infrastructure exists). The PHB display value WILD_SHAPE_HOURS_REMAINING
    is unchanged and retained for reference only.
    """
    from aidm.schemas.intents import RevertFormIntent  # lazy import

    events: List[Event] = []
    ws = deepcopy(world_state)
    current_event_id = next_event_id

    # Pass 1: decrement all transformed entities' counters (and reconstruct if missing)
    expired_ids: List[str] = []
    for entity_id, entity in ws.entities.items():
        if not entity.get(EF.WILD_SHAPE_ACTIVE, False):
            continue

        druid_level = entity.get(EF.CLASS_LEVELS, {}).get("druid", 1)

        # Reconstruct counter if missing (entity transformed before this WO landed)
        if entity.get(EF.WILD_SHAPE_ROUNDS_REMAINING, None) is None:
            entity[EF.WILD_SHAPE_ROUNDS_REMAINING] = druid_level * 10

        rounds_left = entity.get(EF.WILD_SHAPE_ROUNDS_REMAINING, 1) - 1
        entity[EF.WILD_SHAPE_ROUNDS_REMAINING] = rounds_left

        if rounds_left <= 0:
            expired_ids.append(entity_id)

    # Pass 2: trigger auto-revert for expired entities
    # resolve_revert_form deepcopies ws, so feed updated ws through each revert
    for entity_id in expired_ids:
        entity = ws.entities[entity_id]
        events.append(Event(
            event_id=current_event_id,
            event_type="wild_shape_expired",
            timestamp=timestamp,
            payload={
                "actor_id": entity_id,
                "reason": "duration_expired",
                "form_was": entity.get(EF.WILD_SHAPE_FORM, ""),
            },
            citations=[],
        ))
        current_event_id += 1

        synthetic_intent = RevertFormIntent(actor_id=entity_id)
        revert_events, ws = resolve_revert_form(
            intent=synthetic_intent,
            world_state=ws,
            next_event_id=current_event_id,
            timestamp=timestamp + 0.01,
        )
        events.extend(revert_events)
        current_event_id += len(revert_events)

    return events, ws
