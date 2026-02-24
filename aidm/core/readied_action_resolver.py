"""Readied Action resolver for D&D 3.5e (PHB p.160).

WO-ENGINE-READIED-ACTION-001

A readied action is a standard action that fires as an interrupt when a
specified trigger condition occurs during another actor's turn.

Trigger types supported:
- enemy_casts: fires when the target actor begins casting a spell
- enemy_enters_range: fires when the target moves within trigger_range_ft
- enemy_enters_square: fires when the target occupies a specified grid square

State: active_combat["readied_actions"] — list of pending readied action dicts.
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF


def register_readied_action(
    world_state: WorldState,
    intent,  # ReadyActionIntent
    event_id: int,
) -> WorldState:
    """Add a readied action to the active_combat queue.

    Fails closed (ValueError) when readied_intent is None.

    WO-ENGINE-READIED-ACTION-001
    """
    if intent.readied_intent is None:
        raise ValueError(
            f"ReadyActionIntent from {intent.actor_id} has no readied_intent — "
            "cannot register (fail-closed per WO-ENGINE-READIED-ACTION-001)"
        )

    if world_state.active_combat is None:
        return world_state  # No combat context — ignore silently

    entry = {
        "actor_id": intent.actor_id,
        "trigger_type": intent.trigger_type,
        "trigger_target_id": intent.trigger_target_id,
        "trigger_square": intent.trigger_square,
        "trigger_range_ft": intent.trigger_range_ft,
        "readied_intent": intent.readied_intent,
        "registered_at_event_id": event_id,
    }

    new_combat = deepcopy(world_state.active_combat)
    queue = list(new_combat.get("readied_actions", []))
    queue.append(entry)
    new_combat["readied_actions"] = queue

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=new_combat,
    )


def _are_enemies(world_state: WorldState, actor_a: str, actor_b: str) -> bool:
    """Return True if actor_a and actor_b are on opposing teams."""
    entity_a = world_state.entities.get(actor_a, {})
    entity_b = world_state.entities.get(actor_b, {})
    team_a = entity_a.get(EF.TEAM, "")
    team_b = entity_b.get(EF.TEAM, "")
    if not team_a or not team_b:
        return False
    return team_a != team_b


def _distance_ft(world_state: WorldState, actor_a: str, actor_b: str) -> float:
    """Compute distance in feet between two entities using their positions."""
    try:
        from aidm.core.targeting_resolver import get_entity_position
        pos_a = get_entity_position(world_state, actor_a)
        pos_b = get_entity_position(world_state, actor_b)
        return pos_a.distance_to(pos_b)
    except Exception:
        return 999.0  # Cannot determine — don't fire


def check_readied_triggers(
    world_state: WorldState,
    current_actor_id: str,
    trigger_event_type: str,
    event_payload: Dict[str, Any],
    rng: RNGProvider,
    current_event_id: int,
    timestamp: float = 0.0,
) -> Tuple[WorldState, List[Dict[str, Any]], int]:
    """Check all readied actions for trigger conditions.

    Called from execute_turn() before each intent resolves.

    trigger_event_type is the __class__.__name__ of the intent being resolved
    (e.g. "SpellCastIntent", "MoveIntent", "StepMoveIntent").

    Returns (updated_world_state, new_events, next_event_id).

    WO-ENGINE-READIED-ACTION-001
    """
    if world_state.active_combat is None:
        return world_state, [], current_event_id

    readied = world_state.active_combat.get("readied_actions", [])
    if not readied:
        return world_state, [], current_event_id

    events: List[Dict[str, Any]] = []
    remaining = []

    for entry in readied:
        readying_actor = entry["actor_id"]
        trigger_type = entry["trigger_type"]
        trigger_target = entry.get("trigger_target_id")

        # Readied action fires only against enemies of the readying actor
        if not _are_enemies(world_state, readying_actor, current_actor_id):
            remaining.append(entry)
            continue

        # If a specific target is designated, only watch that target
        if trigger_target is not None and trigger_target != current_actor_id:
            remaining.append(entry)
            continue

        triggered = False

        if trigger_type == "enemy_casts":
            # Fires when current_actor_id is about to cast a spell
            if trigger_event_type in ("SpellCastIntent", "CastSpellIntent"):
                triggered = True

        elif trigger_type == "enemy_enters_range":
            # Fires when enemy is within trigger_range_ft of the readying actor
            if trigger_event_type in ("MoveIntent", "StepMoveIntent"):
                dist = _distance_ft(world_state, readying_actor, current_actor_id)
                if dist <= entry.get("trigger_range_ft", 5.0):
                    triggered = True

        elif trigger_type == "enemy_enters_square":
            # Fires when enemy's position matches the watched square
            if trigger_event_type in ("MoveIntent", "StepMoveIntent"):
                sq = entry.get("trigger_square")
                if sq is not None:
                    dest = event_payload.get("destination") or event_payload.get("dest")
                    if dest and dest.get("x") == sq.get("x") and dest.get("y") == sq.get("y"):
                        triggered = True

        if not triggered:
            remaining.append(entry)
            continue

        # --- Trigger fires ---
        readied_intent_dict = entry["readied_intent"]
        resolved_type = readied_intent_dict.get("type", "unknown")

        # Execute the readied intent
        world_state, exec_events, current_event_id = _execute_readied_intent(
            world_state=world_state,
            readied_intent_dict=readied_intent_dict,
            readying_actor_id=readying_actor,
            triggering_actor_id=current_actor_id,
            rng=rng,
            current_event_id=current_event_id,
            timestamp=timestamp,
        )
        events.extend(exec_events)

        # Emit readied_action_triggered
        events.append({
            "event_id": current_event_id,
            "event_type": "readied_action_triggered",
            "timestamp": timestamp + 0.001,
            "payload": {
                "actor_id": readying_actor,
                "trigger_type": trigger_type,
                "triggering_actor_id": current_actor_id,
                "resolved_intent_type": resolved_type,
            },
            "citations": [{"source_id": "681f92bc94ff", "page": 160}],
        })
        current_event_id += 1
        # Entry is consumed — not added to remaining

    # Write back remaining readied actions
    new_combat = deepcopy(world_state.active_combat)
    new_combat["readied_actions"] = remaining
    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=new_combat,
    )

    return world_state, events, current_event_id


def _execute_readied_intent(
    world_state: WorldState,
    readied_intent_dict: Dict[str, Any],
    readying_actor_id: str,
    triggering_actor_id: str,
    rng: RNGProvider,
    current_event_id: int,
    timestamp: float,
) -> Tuple[WorldState, List[Dict[str, Any]], int]:
    """Deserialize and resolve a readied intent dict.

    Supports AttackIntent (most common readied action).
    Returns (world_state, events, next_event_id).
    """
    events: List[Dict[str, Any]] = []

    intent_type = readied_intent_dict.get("type", "")

    if intent_type == "attack":
        try:
            from aidm.schemas.attack import AttackIntent, Weapon
            from aidm.core.attack_resolver import resolve_attack, apply_attack_events
            from aidm.core.event_log import Event

            weapon_data = readied_intent_dict.get("weapon", {})
            weapon = Weapon(**{k: v for k, v in weapon_data.items() if k in Weapon.__dataclass_fields__})
            attack_intent = AttackIntent(
                attacker_id=readied_intent_dict["attacker_id"],
                target_id=readied_intent_dict["target_id"],
                attack_bonus=readied_intent_dict.get("attack_bonus", 0),
                weapon=weapon,
                power_attack_penalty=readied_intent_dict.get("power_attack_penalty", 0),
            )
            raw_events = resolve_attack(
                intent=attack_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp,
            )
            world_state = apply_attack_events(world_state, raw_events)
            for e in raw_events:
                events.append(e.to_dict())
            current_event_id += len(raw_events)
        except Exception:
            pass  # Resolution failure is non-fatal; trigger was consumed

    # Other intent types (spell cast, etc.) can be added in future WOs.

    return world_state, events, current_event_id


def expire_readied_actions(
    world_state: WorldState,
    actor_id: str,
    current_event_id: int,
    timestamp: float = 0.0,
) -> Tuple[WorldState, List[Dict[str, Any]], int]:
    """Expire readied actions for actor_id at the start of their turn.

    PHB p.160: Readied action is lost if the trigger never fires before
    the readying character's next turn.

    Returns (updated_world_state, new_events, next_event_id).

    WO-ENGINE-READIED-ACTION-001
    """
    if world_state.active_combat is None:
        return world_state, [], current_event_id

    readied = world_state.active_combat.get("readied_actions", [])
    if not readied:
        return world_state, [], current_event_id

    events: List[Dict[str, Any]] = []
    remaining = []

    for entry in readied:
        if entry["actor_id"] == actor_id:
            # Expired
            events.append({
                "event_id": current_event_id,
                "event_type": "readied_action_expired",
                "timestamp": timestamp,
                "payload": {
                    "actor_id": actor_id,
                    "trigger_type": entry["trigger_type"],
                },
                "citations": [{"source_id": "681f92bc94ff", "page": 160}],
            })
            current_event_id += 1
        else:
            remaining.append(entry)

    if events:
        new_combat = deepcopy(world_state.active_combat)
        new_combat["readied_actions"] = remaining
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=world_state.entities,
            active_combat=new_combat,
        )

    return world_state, events, current_event_id
