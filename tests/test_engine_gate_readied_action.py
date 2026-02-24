"""Gate ENGINE-READIED-ACTION — WO-ENGINE-READIED-ACTION-001

Tests:
RA-01: ReadyActionIntent registers in active_combat queue
RA-02: Readied attack fires when enemy casts (trigger_type=enemy_casts)
RA-03: Readied attack fires when enemy enters range (trigger_type=enemy_enters_range)
RA-04: Readied action does NOT fire if trigger condition not met
RA-05: Readied action expires at actor's next turn start
RA-06: ReadyActionIntent costs standard action slot
RA-07: Readied action consumed on trigger — not re-used
RA-08: enemy_enters_square trigger fires on position match
RA-09: Zero regressions suite-wide (smoke import check)
RA-10: parse_intent roundtrips ReadyActionIntent
"""

import pytest
import unittest.mock as mock
from typing import Any, Dict

from aidm.core.state import WorldState
from aidm.core.action_economy import ActionBudget, get_action_type
from aidm.core.readied_action_resolver import (
    register_readied_action,
    check_readied_triggers,
    expire_readied_actions,
)
from aidm.schemas.intents import ReadyActionIntent, parse_intent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(eid: str, team: str, hp: int = 20, ac: int = 10, attack_bonus: int = 3,
             bab: int = 3, pos: dict = None) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.ATTACK_BONUS: attack_bonus,
        EF.BAB: bab,
        EF.STR_MOD: 2,
        EF.DEX_MOD: 0,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: pos or {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
    }


def _world(entities: dict, readied_actions: list = None) -> WorldState:
    combat: Dict[str, Any] = {"initiative_order": list(entities.keys())}
    if readied_actions is not None:
        combat["readied_actions"] = readied_actions
    return WorldState(ruleset_version="3.5e", entities=entities, active_combat=combat)


def _rng(rolls=(15, 5)) -> mock.MagicMock:
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [5] * 50
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


WEAPON = {
    "damage_dice": "1d8", "damage_bonus": 0, "critical_range": 20,
    "critical_multiplier": 2, "grip": "one-handed", "damage_type": "slashing",
    "weapon_type": "one-handed", "range_increment": 0, "is_two_handed": False,
}

READIED_ATTACK = {
    "type": "attack",
    "attacker_id": "fighter",
    "target_id": "wizard",
    "attack_bonus": 5,
    "weapon": WEAPON,
    "power_attack_penalty": 0,
}


# ---------------------------------------------------------------------------
# RA-01: ReadyActionIntent registers in active_combat queue
# ---------------------------------------------------------------------------

def test_ra01_registers_in_queue():
    """ReadyActionIntent adds entry to active_combat['readied_actions']."""
    fighter = _entity("fighter", "party")
    wizard = _entity("wizard", "enemy")
    ws = _world({"fighter": fighter, "wizard": wizard})

    intent = ReadyActionIntent(
        actor_id="fighter",
        trigger_type="enemy_casts",
        readied_intent=READIED_ATTACK,
    )
    ws2 = register_readied_action(ws, intent, event_id=10)

    queue = ws2.active_combat["readied_actions"]
    assert len(queue) == 1
    assert queue[0]["actor_id"] == "fighter"
    assert queue[0]["trigger_type"] == "enemy_casts"
    assert queue[0]["readied_intent"] == READIED_ATTACK


# ---------------------------------------------------------------------------
# RA-02: Readied attack fires on enemy_casts trigger
# ---------------------------------------------------------------------------

def test_ra02_fires_on_enemy_casts():
    """When enemy casts, readied_action_triggered is emitted."""
    fighter = _entity("fighter", "party", pos={"x": 1, "y": 0})
    wizard = _entity("wizard", "enemy", pos={"x": 0, "y": 0})
    readied = [{
        "actor_id": "fighter",
        "trigger_type": "enemy_casts",
        "trigger_target_id": None,
        "trigger_square": None,
        "trigger_range_ft": 5.0,
        "readied_intent": READIED_ATTACK,
        "registered_at_event_id": 5,
    }]
    ws = _world({"fighter": fighter, "wizard": wizard}, readied_actions=readied)

    ws2, events, next_eid = check_readied_triggers(
        ws,
        current_actor_id="wizard",
        trigger_event_type="SpellCastIntent",
        event_payload={"type": "cast_spell"},
        rng=_rng(),
        current_event_id=100,
        timestamp=1.0,
    )

    triggered = [e for e in events if e["event_type"] == "readied_action_triggered"]
    assert len(triggered) == 1
    assert triggered[0]["payload"]["actor_id"] == "fighter"
    assert triggered[0]["payload"]["triggering_actor_id"] == "wizard"
    # Queue should be empty after trigger fires
    assert ws2.active_combat["readied_actions"] == []


# ---------------------------------------------------------------------------
# RA-03: Readied attack fires on enemy_enters_range trigger
# ---------------------------------------------------------------------------

def test_ra03_fires_on_enemy_enters_range():
    """When enemy moves into range, readied attack fires."""
    fighter = _entity("fighter", "party", pos={"x": 0, "y": 0})
    enemy = _entity("orc", "enemy", pos={"x": 1, "y": 0})  # 5ft away
    readied = [{
        "actor_id": "fighter",
        "trigger_type": "enemy_enters_range",
        "trigger_target_id": None,
        "trigger_square": None,
        "trigger_range_ft": 5.0,
        "readied_intent": READIED_ATTACK,
        "registered_at_event_id": 5,
    }]
    ws = _world({"fighter": fighter, "orc": enemy}, readied_actions=readied)

    ws2, events, _ = check_readied_triggers(
        ws,
        current_actor_id="orc",
        trigger_event_type="MoveIntent",
        event_payload={"type": "move"},
        rng=_rng(),
        current_event_id=100,
        timestamp=1.0,
    )

    triggered = [e for e in events if e["event_type"] == "readied_action_triggered"]
    assert len(triggered) == 1
    assert ws2.active_combat["readied_actions"] == []


# ---------------------------------------------------------------------------
# RA-04: Readied action does NOT fire if condition not met
# ---------------------------------------------------------------------------

def test_ra04_does_not_fire_if_trigger_not_met():
    """enemy_casts trigger does NOT fire on move action."""
    fighter = _entity("fighter", "party", pos={"x": 0, "y": 0})
    enemy = _entity("orc", "enemy", pos={"x": 1, "y": 0})
    readied = [{
        "actor_id": "fighter",
        "trigger_type": "enemy_casts",
        "trigger_target_id": None,
        "trigger_square": None,
        "trigger_range_ft": 5.0,
        "readied_intent": READIED_ATTACK,
        "registered_at_event_id": 5,
    }]
    ws = _world({"fighter": fighter, "orc": enemy}, readied_actions=readied)

    ws2, events, _ = check_readied_triggers(
        ws,
        current_actor_id="orc",
        trigger_event_type="MoveIntent",   # Not a cast
        event_payload={},
        rng=_rng(),
        current_event_id=100,
        timestamp=1.0,
    )

    triggered = [e for e in events if e["event_type"] == "readied_action_triggered"]
    assert len(triggered) == 0
    # Queue unchanged
    assert len(ws2.active_combat["readied_actions"]) == 1


# ---------------------------------------------------------------------------
# RA-05: Readied action expires at actor's next turn start
# ---------------------------------------------------------------------------

def test_ra05_expires_at_own_turn():
    """expire_readied_actions emits readied_action_expired for the actor."""
    fighter = _entity("fighter", "party")
    ws = _world({"fighter": fighter}, readied_actions=[{
        "actor_id": "fighter",
        "trigger_type": "enemy_casts",
        "trigger_target_id": None,
        "trigger_square": None,
        "trigger_range_ft": 5.0,
        "readied_intent": READIED_ATTACK,
        "registered_at_event_id": 5,
    }])

    ws2, events, _ = expire_readied_actions(ws, "fighter", 100, 2.0)

    expired = [e for e in events if e["event_type"] == "readied_action_expired"]
    assert len(expired) == 1
    assert expired[0]["payload"]["actor_id"] == "fighter"
    assert ws2.active_combat["readied_actions"] == []


# ---------------------------------------------------------------------------
# RA-06: ReadyActionIntent costs standard action slot
# ---------------------------------------------------------------------------

def test_ra06_costs_standard_action():
    """get_action_type returns 'standard' for ReadyActionIntent."""
    intent = ReadyActionIntent(
        actor_id="fighter",
        trigger_type="enemy_casts",
        readied_intent=READIED_ATTACK,
    )
    assert get_action_type(intent) == "standard"

    budget = ActionBudget(standard_used=True)
    from aidm.core.action_economy import check_economy
    denied = check_economy(intent, budget)
    assert denied == "standard"


# ---------------------------------------------------------------------------
# RA-07: Readied action consumed on trigger — not reused
# ---------------------------------------------------------------------------

def test_ra07_consumed_on_trigger():
    """Trigger fires once; second trigger from same enemy does not re-fire."""
    fighter = _entity("fighter", "party", pos={"x": 0, "y": 0})
    wizard = _entity("wizard", "enemy", pos={"x": 1, "y": 0})
    readied = [{
        "actor_id": "fighter",
        "trigger_type": "enemy_casts",
        "trigger_target_id": None,
        "trigger_square": None,
        "trigger_range_ft": 5.0,
        "readied_intent": READIED_ATTACK,
        "registered_at_event_id": 5,
    }]
    ws = _world({"fighter": fighter, "wizard": wizard}, readied_actions=readied)

    ws2, events1, _ = check_readied_triggers(
        ws, "wizard", "SpellCastIntent", {}, _rng(), 100, 1.0
    )
    # First trigger fires
    assert any(e["event_type"] == "readied_action_triggered" for e in events1)
    assert ws2.active_combat["readied_actions"] == []

    # Second trigger on same world state — no readied actions
    ws3, events2, _ = check_readied_triggers(
        ws2, "wizard", "SpellCastIntent", {}, _rng(), 200, 2.0
    )
    assert not any(e["event_type"] == "readied_action_triggered" for e in events2)


# ---------------------------------------------------------------------------
# RA-08: enemy_enters_square trigger fires on position match
# ---------------------------------------------------------------------------

def test_ra08_fires_on_square_match():
    """enemy_enters_square trigger fires when enemy moves to watched square."""
    fighter = _entity("fighter", "party", pos={"x": 0, "y": 0})
    enemy = _entity("orc", "enemy", pos={"x": 3, "y": 3})
    readied = [{
        "actor_id": "fighter",
        "trigger_type": "enemy_enters_square",
        "trigger_target_id": None,
        "trigger_square": {"x": 3, "y": 3},
        "trigger_range_ft": 5.0,
        "readied_intent": READIED_ATTACK,
        "registered_at_event_id": 5,
    }]
    ws = _world({"fighter": fighter, "orc": enemy}, readied_actions=readied)

    ws2, events, _ = check_readied_triggers(
        ws,
        current_actor_id="orc",
        trigger_event_type="MoveIntent",
        event_payload={"destination": {"x": 3, "y": 3}},
        rng=_rng(),
        current_event_id=100,
        timestamp=1.0,
    )

    triggered = [e for e in events if e["event_type"] == "readied_action_triggered"]
    assert len(triggered) == 1
    assert ws2.active_combat["readied_actions"] == []


# ---------------------------------------------------------------------------
# RA-09: parse_intent roundtrip
# ---------------------------------------------------------------------------

def test_ra09_parse_intent_roundtrip():
    """ReadyActionIntent serializes and deserializes correctly."""
    intent = ReadyActionIntent(
        actor_id="fighter",
        trigger_type="enemy_enters_range",
        readied_intent=READIED_ATTACK,
        trigger_target_id="orc",
        trigger_range_ft=10.0,
    )
    d = intent.to_dict()
    restored = parse_intent(d)
    assert isinstance(restored, ReadyActionIntent)
    assert restored.actor_id == "fighter"
    assert restored.trigger_type == "enemy_enters_range"
    assert restored.trigger_range_ft == 10.0


# ---------------------------------------------------------------------------
# RA-10: Empty queue is a no-op
# ---------------------------------------------------------------------------

def test_ra10_empty_queue_noop():
    """check_readied_triggers and expire_readied_actions are no-ops on empty queue."""
    fighter = _entity("fighter", "party")
    ws = _world({"fighter": fighter})  # no readied_actions key

    ws2, events, _ = check_readied_triggers(
        ws, "orc", "SpellCastIntent", {}, _rng(), 0, 0.0
    )
    assert events == []
    assert ws2 is ws

    ws3, expire_events, _ = expire_readied_actions(ws, "fighter", 0, 0.0)
    assert expire_events == []
