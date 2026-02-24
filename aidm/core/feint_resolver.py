"""Feint resolver for D&D 3.5e (PHB p.68, 76).

WO-ENGINE-FEINT-001

Feint is a standard action that uses Bluff to deny the target their Dex
bonus to AC against the feinting actor's next melee attack.

Bluff check: d20 + skill_ranks["bluff"] + CHA_mod
Sense Motive check: d20 + skill_ranks["sense_motive"] + WIS_mod + BAB

Success condition: Bluff strictly greater than Sense Motive total.
Ties go to defender (PHB p.76: "exceeds this defender's check result").

State: active_combat["feint_flat_footed"] — list of pending feint marker dicts.
"""

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF


def resolve_feint(
    world_state: WorldState,
    intent,  # FeintIntent
    rng: RNGProvider,
    current_event_id: int,
    timestamp: float = 0.0,
) -> Tuple[WorldState, List[Dict[str, Any]], int]:
    """Resolve a Feint action.

    PHB p.76: Roll Bluff vs (target Sense Motive + target BAB).
    Success stores feint marker in active_combat["feint_flat_footed"].

    Steps:
    1. Validate actor has Bluff ranks (>= 1) — emit feint_invalid if absent
    2. Roll actor Bluff: d20 + skill_ranks["bluff"] + CHA_mod
    3. Roll target Sense Motive: d20 + skill_ranks["sense_motive"] + WIS_mod + BAB
    4. If Bluff > Sense Motive total: success
    5. Emit feint_success or feint_fail

    WO-ENGINE-FEINT-001
    """
    events: List[Dict[str, Any]] = []

    actor = world_state.entities.get(intent.actor_id, {})
    target = world_state.entities.get(intent.target_id, {})

    # Step 1: Validate Bluff ranks
    skill_ranks = actor.get(EF.SKILL_RANKS, {}) if isinstance(actor.get(EF.SKILL_RANKS), dict) else {}
    bluff_ranks = skill_ranks.get("bluff", 0)

    if bluff_ranks < 1:
        events.append({
            "event_id": current_event_id,
            "event_type": "feint_invalid",
            "timestamp": timestamp,
            "payload": {
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "reason": "no_bluff_ranks",
                "bluff_ranks": bluff_ranks,
            },
            "citations": [{"source_id": "681f92bc94ff", "page": 76}],
        })
        current_event_id += 1
        return world_state, events, current_event_id

    # Step 2: Actor Bluff roll
    cha_mod = actor.get(EF.CHA_MOD, 0)
    combat_rng = rng.stream("combat")
    bluff_d20 = combat_rng.randint(1, 20)
    bluff_total = bluff_d20 + bluff_ranks + cha_mod

    # Step 3: Target Sense Motive + BAB
    target_skills = target.get(EF.SKILL_RANKS, {}) if isinstance(target.get(EF.SKILL_RANKS), dict) else {}
    sense_motive_ranks = target_skills.get("sense_motive", 0)
    wis_mod = target.get(EF.WIS_MOD, 0)
    target_bab = target.get(EF.BAB, 0)
    sm_d20 = combat_rng.randint(1, 20)
    sm_total = sm_d20 + sense_motive_ranks + wis_mod + target_bab

    # Step 4: Success if strictly greater (PHB: "exceeds")
    success = bluff_total > sm_total

    if success:
        world_state = _add_feint_marker(
            world_state,
            feinting_actor_id=intent.actor_id,
            target_id=intent.target_id,
            event_id=current_event_id,
        )
        events.append({
            "event_id": current_event_id,
            "event_type": "feint_success",
            "timestamp": timestamp,
            "payload": {
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "bluff_d20": bluff_d20,
                "bluff_ranks": bluff_ranks,
                "cha_mod": cha_mod,
                "bluff_roll": bluff_total,
                "sm_d20": sm_d20,
                "sense_motive_ranks": sense_motive_ranks,
                "wis_mod": wis_mod,
                "target_bab": target_bab,
                "sense_motive_roll": sm_total,
            },
            "citations": [{"source_id": "681f92bc94ff", "page": 76}],
        })
    else:
        events.append({
            "event_id": current_event_id,
            "event_type": "feint_fail",
            "timestamp": timestamp,
            "payload": {
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "bluff_d20": bluff_d20,
                "bluff_ranks": bluff_ranks,
                "cha_mod": cha_mod,
                "bluff_roll": bluff_total,
                "sm_d20": sm_d20,
                "sense_motive_ranks": sense_motive_ranks,
                "wis_mod": wis_mod,
                "target_bab": target_bab,
                "sense_motive_roll": sm_total,
            },
            "citations": [{"source_id": "681f92bc94ff", "page": 76}],
        })
    current_event_id += 1

    return world_state, events, current_event_id


def _add_feint_marker(
    world_state: WorldState,
    feinting_actor_id: str,
    target_id: str,
    event_id: int,
) -> WorldState:
    """Write a feint flat-footed marker to active_combat."""
    if world_state.active_combat is None:
        return world_state

    entry = {
        "feinting_actor_id": feinting_actor_id,
        "target_id": target_id,
        "registered_at_event_id": event_id,
        "expires_at_actor_id": feinting_actor_id,  # expires at feinter's next turn
    }

    new_combat = deepcopy(world_state.active_combat)
    markers = list(new_combat.get("feint_flat_footed", []))
    markers.append(entry)
    new_combat["feint_flat_footed"] = markers

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=new_combat,
    )


def consume_feint_marker(
    world_state: WorldState,
    attacker_id: str,
    target_id: str,
) -> Tuple[WorldState, bool]:
    """Check if attacker has a feint marker on target; consume it if present.

    Returns (updated_world_state, feint_active).
    Removes the matching entry on consumption (consumed by first attack).

    Called from attack_resolver.py before AC calculation.

    WO-ENGINE-FEINT-001
    """
    if world_state.active_combat is None:
        return world_state, False

    markers = world_state.active_combat.get("feint_flat_footed", [])
    if not markers:
        return world_state, False

    remaining = []
    consumed = False
    for entry in markers:
        if (not consumed
                and entry["feinting_actor_id"] == attacker_id
                and entry["target_id"] == target_id):
            consumed = True  # consume first match only
        else:
            remaining.append(entry)

    if not consumed:
        return world_state, False

    new_combat = deepcopy(world_state.active_combat)
    new_combat["feint_flat_footed"] = remaining
    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=new_combat,
    )
    return world_state, True


def expire_feint_markers(
    world_state: WorldState,
    actor_id: str,
    current_event_id: int,
    timestamp: float = 0.0,
) -> Tuple[WorldState, List[Dict[str, Any]], int]:
    """Expire feint markers set by actor_id at the start of their turn.

    PHB p.76: Feint must be used on or before the feinting actor's next turn.
    Unexpired markers are cleared here.

    Returns (updated_world_state, new_events, next_event_id).

    WO-ENGINE-FEINT-001
    """
    if world_state.active_combat is None:
        return world_state, [], current_event_id

    markers = world_state.active_combat.get("feint_flat_footed", [])
    if not markers:
        return world_state, [], current_event_id

    events: List[Dict[str, Any]] = []
    remaining = []

    for entry in markers:
        if entry["expires_at_actor_id"] == actor_id:
            events.append({
                "event_id": current_event_id,
                "event_type": "feint_expired",
                "timestamp": timestamp,
                "payload": {
                    "actor_id": actor_id,
                    "target_id": entry["target_id"],
                },
                "citations": [{"source_id": "681f92bc94ff", "page": 76}],
            })
            current_event_id += 1
        else:
            remaining.append(entry)

    if events:
        new_combat = deepcopy(world_state.active_combat)
        new_combat["feint_flat_footed"] = remaining
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=world_state.entities,
            active_combat=new_combat,
        )

    return world_state, events, current_event_id
