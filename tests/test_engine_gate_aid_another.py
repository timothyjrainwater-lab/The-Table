"""Gate ENGINE-AID-ANOTHER — WO-ENGINE-AID-ANOTHER-001

Tests:
AA-01: Successful Aid Another adds +2 attack bonus to ally vs enemy
AA-02: Failed Aid Another (roll < 10) adds no bonus
AA-03: Multiple helpers' bonuses stack on same ally
AA-04: consume_aid_another_bonus removes matched entry and returns total
AA-05: consume returns 0 and is no-op if no matching bonus
AA-06: Aid Another costs standard action slot
AA-07: aid_another_success event emitted with roll details
AA-08: aid_another_fail event emitted with roll details
AA-09: expire_aid_another_bonuses removes helper's unclaimed bonuses
AA-10: parse_intent roundtrips AidAnotherIntent
"""

import pytest
import unittest.mock as mock
from typing import Any, Dict

from aidm.core.state import WorldState
from aidm.core.action_economy import ActionBudget, get_action_type, check_economy
from aidm.core.aid_another_resolver import (
    resolve_aid_another,
    consume_aid_another_bonus,
    expire_aid_another_bonuses,
)
from aidm.schemas.intents import AidAnotherIntent, parse_intent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(eid: str, team: str, hp: int = 20, bab: int = 3,
             str_mod: int = 2) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 10,
        EF.ATTACK_BONUS: bab + str_mod,
        EF.BAB: bab,
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 0,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
    }


def _world(entities: dict, aid_bonuses: list = None) -> WorldState:
    combat: Dict[str, Any] = {"initiative_order": list(entities.keys())}
    if aid_bonuses is not None:
        combat["aid_another_bonuses"] = aid_bonuses
    return WorldState(ruleset_version="3.5e", entities=entities, active_combat=combat)


def _rng(d20: int) -> mock.MagicMock:
    stream = mock.MagicMock()
    stream.randint.side_effect = [d20] + [5] * 50
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# AA-01: Successful aid adds +2 attack bonus
# ---------------------------------------------------------------------------

def test_aa01_success_adds_attack_bonus():
    """Roll >= 10: aid_another_success event emitted; bonus stored in queue."""
    helper = _entity("cleric", "party", bab=3, str_mod=2)
    ally = _entity("fighter", "party")
    enemy = _entity("orc", "enemy")
    ws = _world({"cleric": helper, "fighter": ally, "orc": enemy})

    intent = AidAnotherIntent(
        actor_id="cleric", ally_id="fighter", enemy_id="orc", aid_type="attack"
    )
    # d20=12 + bab 3 + str 2 = 17 >= 10 → success
    ws2, events, _ = resolve_aid_another(ws, intent, _rng(12), 0, 0.0)

    success = [e for e in events if e["event_type"] == "aid_another_success"]
    assert len(success) == 1
    assert success[0]["payload"]["bonus"] == 2
    assert success[0]["payload"]["aid_type"] == "attack"

    bonuses = ws2.active_combat.get("aid_another_bonuses", [])
    assert len(bonuses) == 1
    assert bonuses[0]["beneficiary_id"] == "fighter"
    assert bonuses[0]["bonus"] == 2


# ---------------------------------------------------------------------------
# AA-02: Failed aid adds no bonus
# ---------------------------------------------------------------------------

def test_aa02_fail_adds_no_bonus():
    """Roll < 10: aid_another_fail event; no bonus stored."""
    helper = _entity("cleric", "party", bab=1, str_mod=0)
    ally = _entity("fighter", "party")
    enemy = _entity("orc", "enemy")
    ws = _world({"cleric": helper, "fighter": ally, "orc": enemy})

    intent = AidAnotherIntent(
        actor_id="cleric", ally_id="fighter", enemy_id="orc", aid_type="attack"
    )
    # d20=1 + bab 1 + str 0 = 2 < 10 → fail
    ws2, events, _ = resolve_aid_another(ws, intent, _rng(1), 0, 0.0)

    fail_events = [e for e in events if e["event_type"] == "aid_another_fail"]
    assert len(fail_events) == 1
    assert ws2.active_combat.get("aid_another_bonuses", []) == []


# ---------------------------------------------------------------------------
# AA-03: Multiple helpers' bonuses stack
# ---------------------------------------------------------------------------

def test_aa03_stacking_bonuses():
    """Two helpers successfully aiding the same ally vs same enemy stacks."""
    existing = [{
        "beneficiary_id": "fighter",
        "enemy_id": "orc",
        "aid_type": "attack",
        "bonus": 2,
        "registered_at_event_id": 0,
        "expires_at_actor_id": "cleric1",
    }]
    fighter = _entity("fighter", "party")
    orc = _entity("orc", "enemy")
    cleric2 = _entity("cleric2", "party", bab=3, str_mod=2)
    ws = _world({"fighter": fighter, "orc": orc, "cleric2": cleric2}, aid_bonuses=existing)

    intent = AidAnotherIntent(
        actor_id="cleric2", ally_id="fighter", enemy_id="orc", aid_type="attack"
    )
    ws2, events, _ = resolve_aid_another(ws, intent, _rng(12), 10, 1.0)

    bonuses = ws2.active_combat["aid_another_bonuses"]
    assert len(bonuses) == 2

    # Consume all matching bonuses at once
    ws3, total = consume_aid_another_bonus(ws2, "fighter", "orc", "attack")
    assert total == 4  # 2 + 2 stacked


# ---------------------------------------------------------------------------
# AA-04: consume removes matched entries and returns total
# ---------------------------------------------------------------------------

def test_aa04_consume_removes_and_returns_bonus():
    """consume_aid_another_bonus removes all matching entries and returns sum."""
    existing = [
        {"beneficiary_id": "fighter", "enemy_id": "orc", "aid_type": "attack",
         "bonus": 2, "registered_at_event_id": 0, "expires_at_actor_id": "cleric"},
        {"beneficiary_id": "rogue", "enemy_id": "orc", "aid_type": "ac",
         "bonus": 2, "registered_at_event_id": 1, "expires_at_actor_id": "paladin"},
    ]
    ws = _world({"fighter": _entity("fighter", "party"), "rogue": _entity("rogue", "party"),
                 "orc": _entity("orc", "enemy")}, aid_bonuses=existing)

    ws2, total = consume_aid_another_bonus(ws, "fighter", "orc", "attack")
    assert total == 2
    remaining = ws2.active_combat["aid_another_bonuses"]
    assert len(remaining) == 1
    assert remaining[0]["beneficiary_id"] == "rogue"


# ---------------------------------------------------------------------------
# AA-05: consume returns 0 if no match
# ---------------------------------------------------------------------------

def test_aa05_consume_no_match_returns_zero():
    """consume returns 0 and state unchanged if no matching bonus."""
    ws = _world({"fighter": _entity("fighter", "party"), "orc": _entity("orc", "enemy")})
    ws2, total = consume_aid_another_bonus(ws, "fighter", "orc", "attack")
    assert total == 0
    assert ws2 is ws


# ---------------------------------------------------------------------------
# AA-06: AidAnotherIntent costs standard action
# ---------------------------------------------------------------------------

def test_aa06_costs_standard_action():
    """get_action_type returns 'standard' for AidAnotherIntent."""
    intent = AidAnotherIntent(
        actor_id="cleric", ally_id="fighter", enemy_id="orc", aid_type="attack"
    )
    assert get_action_type(intent) == "standard"

    budget = ActionBudget(standard_used=True)
    denied = check_economy(intent, budget)
    assert denied == "standard"


# ---------------------------------------------------------------------------
# AA-07: aid_another_success event has correct roll details
# ---------------------------------------------------------------------------

def test_aa07_success_event_has_roll_details():
    """Success event contains d20, melee_bonus, and roll fields."""
    helper = _entity("cleric", "party", bab=3, str_mod=2)
    ally = _entity("fighter", "party")
    enemy = _entity("orc", "enemy")
    ws = _world({"cleric": helper, "fighter": ally, "orc": enemy})

    intent = AidAnotherIntent(
        actor_id="cleric", ally_id="fighter", enemy_id="orc", aid_type="ac"
    )
    ws2, events, _ = resolve_aid_another(ws, intent, _rng(10), 0, 0.0)

    success = [e for e in events if e["event_type"] == "aid_another_success"][0]
    assert success["payload"]["d20"] == 10
    assert success["payload"]["melee_bonus"] == 5  # bab 3 + str 2
    assert success["payload"]["roll"] == 15
    assert success["payload"]["aid_type"] == "ac"


# ---------------------------------------------------------------------------
# AA-08: aid_another_fail event has correct roll details
# ---------------------------------------------------------------------------

def test_aa08_fail_event_has_roll_details():
    """Fail event contains d20 and roll fields."""
    helper = _entity("cleric", "party", bab=0, str_mod=0)
    ally = _entity("fighter", "party")
    enemy = _entity("orc", "enemy")
    ws = _world({"cleric": helper, "fighter": ally, "orc": enemy})

    intent = AidAnotherIntent(
        actor_id="cleric", ally_id="fighter", enemy_id="orc", aid_type="attack"
    )
    ws2, events, _ = resolve_aid_another(ws, intent, _rng(5), 0, 0.0)

    fail = [e for e in events if e["event_type"] == "aid_another_fail"][0]
    assert fail["payload"]["d20"] == 5
    assert fail["payload"]["roll"] == 5  # d20=5, bonus=0


# ---------------------------------------------------------------------------
# AA-09: expire removes unclaimed bonuses from helper
# ---------------------------------------------------------------------------

def test_aa09_expire_removes_helper_bonuses():
    """expire_aid_another_bonuses removes entries belonging to a specific helper."""
    existing = [
        {"beneficiary_id": "fighter", "enemy_id": "orc", "aid_type": "attack",
         "bonus": 2, "registered_at_event_id": 0, "expires_at_actor_id": "cleric"},
        {"beneficiary_id": "rogue", "enemy_id": "orc", "aid_type": "attack",
         "bonus": 2, "registered_at_event_id": 1, "expires_at_actor_id": "paladin"},
    ]
    ws = _world({
        "fighter": _entity("fighter", "party"),
        "rogue": _entity("rogue", "party"),
        "orc": _entity("orc", "enemy"),
        "cleric": _entity("cleric", "party"),
    }, aid_bonuses=existing)

    ws2, events = expire_aid_another_bonuses(ws, "cleric", 0.0, 0)
    expired = [e for e in events if e["event_type"] == "aid_another_bonus_expired"]
    assert len(expired) == 1
    assert expired[0]["payload"]["actor_id"] == "cleric"

    remaining = ws2.active_combat["aid_another_bonuses"]
    assert len(remaining) == 1
    assert remaining[0]["expires_at_actor_id"] == "paladin"


# ---------------------------------------------------------------------------
# AA-10: parse_intent roundtrip
# ---------------------------------------------------------------------------

def test_aa10_parse_intent_roundtrip():
    """AidAnotherIntent serializes and deserializes correctly."""
    intent = AidAnotherIntent(
        actor_id="cleric", ally_id="fighter", enemy_id="orc", aid_type="ac"
    )
    d = intent.to_dict()
    restored = parse_intent(d)
    assert isinstance(restored, AidAnotherIntent)
    assert restored.actor_id == "cleric"
    assert restored.ally_id == "fighter"
    assert restored.aid_type == "ac"
