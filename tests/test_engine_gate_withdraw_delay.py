"""Gate ENGINE-WITHDRAW-DELAY — WO-ENGINE-WITHDRAW-DELAY-001

Tests:
WD-01: resolve_withdraw sets withdrew_actors in active_combat
WD-02: is_withdrawn returns True after resolve_withdraw
WD-03: is_withdrawn returns False if not withdrawn
WD-04: withdraw suppresses first-square AoO in check_aoo_triggers
WD-05: clear_withdrew_actors removes actor from list
WD-06: resolve_delay emits delay_declared event with new_initiative
WD-07: resolve_delay reorders initiative_order correctly
WD-08: resolve_delay denied if new_initiative >= current initiative
WD-09: resolve_delay denied if actor not in initiative_order
WD-10: WithdrawIntent and DelayIntent roundtrip via parse_intent
"""

import unittest.mock as mock
from typing import Any, Dict
from copy import deepcopy

import pytest

from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import WithdrawIntent, DelayIntent, parse_intent
from aidm.core.state import WorldState
from aidm.core.withdraw_delay_resolver import (
    resolve_withdraw, resolve_delay, is_withdrawn, clear_withdrew_actors,
)
from aidm.core.aoo import check_aoo_triggers
from aidm.schemas.attack import StepMoveIntent
from aidm.schemas.position import Position


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(eid: str, team: str, pos: dict = None) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 12,
        EF.ATTACK_BONUS: 4,
        EF.BAB: 4,
        EF.STR_MOD: 2,
        EF.DEX_MOD: 0,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.POSITION: pos or {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
    }


def _combat_world(entities: dict, initiative_order=None, initiative_scores=None,
                  withdrew_actors=None) -> WorldState:
    order = initiative_order or list(entities.keys())
    active = {
        "initiative_order": order,
        "aoo_used_this_round": [],
        "withdrew_actors": withdrew_actors or [],
    }
    if initiative_scores:
        active["initiative_scores"] = initiative_scores
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat=active,
    )


# ---------------------------------------------------------------------------
# WD-01: resolve_withdraw sets withdrew_actors in active_combat
# ---------------------------------------------------------------------------

def test_wd01_resolve_withdraw_sets_flag():
    hero = _entity("hero", "party")
    ws = _combat_world({"hero": hero})
    intent = WithdrawIntent(actor_id="hero")
    new_ws, events = resolve_withdraw(intent, ws, next_event_id=1, timestamp=0.0)
    assert "hero" in new_ws.active_combat["withdrew_actors"]


# ---------------------------------------------------------------------------
# WD-02: is_withdrawn returns True after resolve_withdraw
# ---------------------------------------------------------------------------

def test_wd02_is_withdrawn_true():
    hero = _entity("hero", "party")
    ws = _combat_world({"hero": hero})
    ws2, _ = resolve_withdraw(WithdrawIntent("hero"), ws, 1, 0.0)
    assert is_withdrawn(ws2, "hero") is True


# ---------------------------------------------------------------------------
# WD-03: is_withdrawn returns False when not withdrawn
# ---------------------------------------------------------------------------

def test_wd03_is_withdrawn_false():
    hero = _entity("hero", "party")
    ws = _combat_world({"hero": hero})
    assert is_withdrawn(ws, "hero") is False


# ---------------------------------------------------------------------------
# WD-04: withdraw suppresses first-square AoO in check_aoo_triggers
# ---------------------------------------------------------------------------

def test_wd04_withdraw_suppresses_aoo():
    hero = _entity("hero", "party", pos={"x": 1, "y": 0})
    orc = _entity("orc", "monsters", pos={"x": 0, "y": 0})
    ws = _combat_world({"hero": hero, "orc": orc}, withdrew_actors=["hero"])
    move_intent = StepMoveIntent(
        actor_id="hero",
        from_pos=Position(x=1, y=0),
        to_pos=Position(x=2, y=0),
    )
    triggers = check_aoo_triggers(ws, "hero", move_intent)
    assert triggers == []


# ---------------------------------------------------------------------------
# WD-05: clear_withdrew_actors removes actor
# ---------------------------------------------------------------------------

def test_wd05_clear_withdrew_actors():
    hero = _entity("hero", "party")
    ws = _combat_world({"hero": hero}, withdrew_actors=["hero"])
    ws2 = clear_withdrew_actors(ws, "hero")
    assert "hero" not in ws2.active_combat.get("withdrew_actors", [])


# ---------------------------------------------------------------------------
# WD-06: resolve_delay emits delay_declared event with new_initiative
# ---------------------------------------------------------------------------

def test_wd06_resolve_delay_emits_event():
    hero = _entity("hero", "party")
    orc = _entity("orc", "monsters")
    ws = _combat_world(
        {"hero": hero, "orc": orc},
        initiative_order=["hero", "orc"],
        initiative_scores={"hero": 15, "orc": 8},
    )
    intent = DelayIntent(actor_id="hero", new_initiative=5)
    new_ws, events = resolve_delay(intent, ws, next_event_id=1, timestamp=0.0)
    event_types = [ev["event_type"] for ev in events]
    assert "delay_declared" in event_types
    delay_ev = next(ev for ev in events if ev["event_type"] == "delay_declared")
    assert delay_ev["payload"]["new_initiative"] == 5


# ---------------------------------------------------------------------------
# WD-07: resolve_delay reorders initiative_order
# ---------------------------------------------------------------------------

def test_wd07_resolve_delay_reorders():
    hero = _entity("hero", "party")
    orc = _entity("orc", "monsters")
    wizard = _entity("wizard", "party")
    ws = _combat_world(
        {"hero": hero, "orc": orc, "wizard": wizard},
        initiative_order=["hero", "orc", "wizard"],
        initiative_scores={"hero": 20, "orc": 12, "wizard": 5},
    )
    intent = DelayIntent(actor_id="hero", new_initiative=3)
    new_ws, _ = resolve_delay(intent, ws, next_event_id=1, timestamp=0.0)
    order = new_ws.active_combat["initiative_order"]
    hero_idx = order.index("hero")
    wizard_idx = order.index("wizard")
    # hero at 3 should come after wizard at 5
    assert hero_idx > wizard_idx


# ---------------------------------------------------------------------------
# WD-08: resolve_delay denied if new_initiative >= current initiative
# ---------------------------------------------------------------------------

def test_wd08_delay_denied_if_not_lower():
    hero = _entity("hero", "party")
    ws = _combat_world(
        {"hero": hero},
        initiative_order=["hero"],
        initiative_scores={"hero": 10},
    )
    intent = DelayIntent(actor_id="hero", new_initiative=10)
    _, events = resolve_delay(intent, ws, next_event_id=1, timestamp=0.0)
    event_types = [ev["event_type"] for ev in events]
    assert "delay_denied" in event_types


# ---------------------------------------------------------------------------
# WD-09: resolve_delay denied if actor not in initiative_order
# ---------------------------------------------------------------------------

def test_wd09_delay_denied_not_in_order():
    hero = _entity("hero", "party")
    ws = _combat_world({"hero": hero}, initiative_order=[])
    intent = DelayIntent(actor_id="hero", new_initiative=5)
    _, events = resolve_delay(intent, ws, next_event_id=1, timestamp=0.0)
    event_types = [ev["event_type"] for ev in events]
    assert "delay_denied" in event_types


# ---------------------------------------------------------------------------
# WD-10: WithdrawIntent and DelayIntent roundtrip via parse_intent
# ---------------------------------------------------------------------------

def test_wd10_parse_intent_roundtrip():
    w = WithdrawIntent(actor_id="hero")
    assert parse_intent(w.to_dict()).actor_id == "hero"

    d = DelayIntent(actor_id="fighter", new_initiative=7)
    parsed = parse_intent(d.to_dict())
    assert isinstance(parsed, DelayIntent)
    assert parsed.new_initiative == 7
