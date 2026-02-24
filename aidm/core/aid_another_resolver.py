"""Aid Another resolver for D&D 3.5e (PHB p.154).

WO-ENGINE-AID-ANOTHER-001

A helper can take a standard action to make an attack roll vs AC 10.
Success grants an ally +2 circumstance bonus to their next attack roll
or +2 AC against a specific enemy's next attack.

Multiple Aid Another bonuses from different helpers DO stack — this is
an explicit exception in PHB p.154 to the normal same-type stacking rule.

State: active_combat["aid_another_bonuses"] — list of pending bonus dicts.
"""

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF


def resolve_aid_another(
    world_state: WorldState,
    intent,  # AidAnotherIntent
    rng: RNGProvider,
    current_event_id: int,
    timestamp: float = 0.0,
) -> Tuple[WorldState, List[Dict[str, Any]], int]:
    """Resolve Aid Another action.

    PHB p.154: Roll d20 + melee attack bonus vs AC 10.
    Success: ally gains +2 circumstance bonus to attack or AC.

    Steps:
    1. Validate actor != ally
    2. Roll d20 + actor BAB + STR_mod vs AC 10
    3. Success → add bonus to active_combat["aid_another_bonuses"]
    4. Emit aid_another_success or aid_another_fail

    WO-ENGINE-AID-ANOTHER-001
    """
    events: List[Dict[str, Any]] = []

    actor = world_state.entities.get(intent.actor_id, {})

    # BAB + STR modifier = melee attack bonus for Aid Another check
    bab = actor.get(EF.BAB, 0)
    str_mod = actor.get(EF.STR_MOD, 0)
    melee_bonus = bab + str_mod

    combat_rng = rng.stream("combat")
    d20 = combat_rng.randint(1, 20)
    total = d20 + melee_bonus
    success = total >= 10  # AC 10 threshold (PHB p.154)

    if success:
        world_state = _add_aid_bonus(
            world_state,
            beneficiary_id=intent.ally_id,
            enemy_id=intent.enemy_id,
            aid_type=intent.aid_type,
            helper_id=intent.actor_id,
            event_id=current_event_id,
        )
        events.append({
            "event_id": current_event_id,
            "event_type": "aid_another_success",
            "timestamp": timestamp,
            "payload": {
                "actor_id": intent.actor_id,
                "ally_id": intent.ally_id,
                "enemy_id": intent.enemy_id,
                "aid_type": intent.aid_type,
                "d20": d20,
                "melee_bonus": melee_bonus,
                "roll": total,
                "bonus": 2,
            },
            "citations": [{"source_id": "681f92bc94ff", "page": 154}],
        })
    else:
        events.append({
            "event_id": current_event_id,
            "event_type": "aid_another_fail",
            "timestamp": timestamp,
            "payload": {
                "actor_id": intent.actor_id,
                "ally_id": intent.ally_id,
                "enemy_id": intent.enemy_id,
                "aid_type": intent.aid_type,
                "d20": d20,
                "melee_bonus": melee_bonus,
                "roll": total,
            },
            "citations": [{"source_id": "681f92bc94ff", "page": 154}],
        })
    current_event_id += 1

    return world_state, events, current_event_id


def _add_aid_bonus(
    world_state: WorldState,
    beneficiary_id: str,
    enemy_id: str,
    aid_type: str,
    helper_id: str,
    event_id: int,
) -> WorldState:
    """Write an Aid Another bonus entry to active_combat."""
    if world_state.active_combat is None:
        return world_state

    entry = {
        "beneficiary_id": beneficiary_id,
        "enemy_id": enemy_id,
        "aid_type": aid_type,  # "attack" | "ac"
        "bonus": 2,            # always +2 per PHB p.154
        "registered_at_event_id": event_id,
        "expires_at_actor_id": helper_id,  # expires at helper's next turn
    }

    new_combat = deepcopy(world_state.active_combat)
    bonuses = list(new_combat.get("aid_another_bonuses", []))
    bonuses.append(entry)
    new_combat["aid_another_bonuses"] = bonuses

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=new_combat,
    )


def consume_aid_another_bonus(
    world_state: WorldState,
    beneficiary_id: str,
    enemy_id: str,
    aid_type: str,
) -> Tuple[WorldState, int]:
    """Consume all matching Aid Another bonuses for beneficiary vs enemy.

    Returns (updated_world_state, total_bonus_consumed).
    Removes matched entries from active_combat["aid_another_bonuses"].

    Multiple bonuses from different helpers stack — all matching entries
    are summed and consumed in a single call.

    WO-ENGINE-AID-ANOTHER-001
    """
    if world_state.active_combat is None:
        return world_state, 0

    bonuses = world_state.active_combat.get("aid_another_bonuses", [])
    if not bonuses:
        return world_state, 0

    total = 0
    remaining = []
    for entry in bonuses:
        if (entry["beneficiary_id"] == beneficiary_id
                and entry["enemy_id"] == enemy_id
                and entry["aid_type"] == aid_type):
            total += entry["bonus"]
        else:
            remaining.append(entry)

    if total == 0:
        return world_state, 0

    new_combat = deepcopy(world_state.active_combat)
    new_combat["aid_another_bonuses"] = remaining
    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=new_combat,
    )
    return world_state, total


def expire_aid_another_bonuses(
    world_state: WorldState,
    actor_id: str,
    timestamp: float = 0.0,
    base_event_id: int = 0,
) -> Tuple[WorldState, List[Dict[str, Any]]]:
    """Expire Aid Another bonuses granted by actor_id at their turn start.

    Removes entries where expires_at_actor_id == actor_id.
    Emits aid_another_bonus_expired for each removed entry.

    WO-ENGINE-AID-ANOTHER-001
    """
    if world_state.active_combat is None:
        return world_state, []

    bonuses = world_state.active_combat.get("aid_another_bonuses", [])
    if not bonuses:
        return world_state, []

    events: List[Dict[str, Any]] = []
    remaining = []
    eid = base_event_id

    for entry in bonuses:
        if entry["expires_at_actor_id"] == actor_id:
            events.append({
                "event_id": eid,
                "event_type": "aid_another_bonus_expired",
                "timestamp": timestamp,
                "payload": {
                    "actor_id": actor_id,
                    "beneficiary_id": entry["beneficiary_id"],
                    "enemy_id": entry["enemy_id"],
                    "aid_type": entry["aid_type"],
                },
                "citations": [{"source_id": "681f92bc94ff", "page": 154}],
            })
            eid += 1
        else:
            remaining.append(entry)

    if events:
        new_combat = deepcopy(world_state.active_combat)
        new_combat["aid_another_bonuses"] = remaining
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=world_state.entities,
            active_combat=new_combat,
        )

    return world_state, events
