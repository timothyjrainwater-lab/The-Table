"""ENGINE-BARDIC-DURATION Gate -- Inspire Courage ends when bard is incapacitated (10 tests).

Gate: ENGINE-BARDIC-DURATION
Tests: BD-01 through BD-10
WO: WO-ENGINE-BARDIC-DURATION-001

PHB p.29: Inspire Courage ends if the bard is killed, goes unconscious, or is deafened.
The effect must expire on the NEXT TICK after the bard enters one of those states.
"""

import pytest
from copy import deepcopy

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import BardicMusicIntent
from aidm.core.bardic_music_resolver import (
    resolve_bardic_music,
    tick_inspire_courage,
    _bard_is_incapacitated,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _bard(eid="bard", level=1, uses=3, defeated=False, dying=False, conditions=None):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 0 if (defeated or dying) else 20,
        EF.HP_MAX: 20,
        EF.AC: 13,
        EF.DEFEATED: defeated,
        EF.DYING: dying,
        EF.CLASS_LEVELS: {"bard": level},
        EF.CONDITIONS: conditions or {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.BARDIC_MUSIC_USES_REMAINING: uses,
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
        EF.INSPIRE_COURAGE_ROUNDS_REMAINING: 0,
        EF.INSPIRE_COURAGE_BARD_ID: None,
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.CON_MOD: 0,
        EF.CHA_MOD: 2, EF.WIS_MOD: 0, EF.INT_MOD: 0,
        EF.BAB: 0,
    }


def _ally(eid="fighter", rounds=4, bard_id="bard"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 25,
        EF.HP_MAX: 25,
        EF.AC: 15,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.CLASS_LEVELS: {"fighter": 3},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.INSPIRE_COURAGE_ACTIVE: True,
        EF.INSPIRE_COURAGE_BONUS: 1,
        EF.INSPIRE_COURAGE_ROUNDS_REMAINING: rounds,
        EF.INSPIRE_COURAGE_BARD_ID: bard_id,
        EF.STR_MOD: 3, EF.DEX_MOD: 0,
    }


def _world(entities):
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
        },
    )


# ---------------------------------------------------------------------------
# BD-01: bard_id stored at activation
# ---------------------------------------------------------------------------

def test_bd01_bard_id_stored_at_activation():
    """BD-01: INSPIRE_COURAGE_BARD_ID is set to the bard's entity_id on all affected entities."""
    bard = _bard()
    ally = _ally(bard_id=None)
    ally[EF.INSPIRE_COURAGE_ACTIVE] = False
    ally[EF.INSPIRE_COURAGE_ROUNDS_REMAINING] = 0
    ally[EF.INSPIRE_COURAGE_BARD_ID] = None

    ws = _world({"bard": bard, "fighter": ally})
    intent = BardicMusicIntent(actor_id="bard", performance="inspire_courage", ally_ids=["fighter"])
    _, ws2 = resolve_bardic_music(intent, ws, 0, 0.0)

    assert ws2.entities["bard"][EF.INSPIRE_COURAGE_BARD_ID] == "bard"
    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_BARD_ID] == "bard"


# ---------------------------------------------------------------------------
# BD-02: Healthy bard -- effect does NOT expire early
# ---------------------------------------------------------------------------

def test_bd02_healthy_bard_effect_continues():
    """BD-02: Tick with a healthy bard decrements rounds normally, does not expire."""
    bard = _bard(defeated=False, dying=False)
    ally = _ally(rounds=4)
    ws = _world({"bard": bard, "fighter": ally})

    _, ws2 = tick_inspire_courage(ws, 0, 0.0)

    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ACTIVE] is True
    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ROUNDS_REMAINING] == 3


# ---------------------------------------------------------------------------
# BD-03: Bard defeated -- effect expires on next tick
# ---------------------------------------------------------------------------

def test_bd03_bard_defeated_expires_effect():
    """BD-03: When bard is DEFEATED, inspire courage expires on the next tick."""
    bard = _bard(defeated=True)
    ally = _ally(rounds=4)
    ws = _world({"bard": bard, "fighter": ally})

    events, ws2 = tick_inspire_courage(ws, 0, 0.0)

    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ACTIVE] is False
    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_BONUS] == 0
    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ROUNDS_REMAINING] == 0
    assert any(e.event_type == "inspire_courage_end" for e in events)


# ---------------------------------------------------------------------------
# BD-04: Bard dying -- effect expires on next tick
# ---------------------------------------------------------------------------

def test_bd04_bard_dying_expires_effect():
    """BD-04: When bard is DYING, inspire courage expires on the next tick."""
    bard = _bard(dying=True)
    ally = _ally(rounds=6)
    ws = _world({"bard": bard, "fighter": ally})

    events, ws2 = tick_inspire_courage(ws, 0, 0.0)

    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ACTIVE] is False
    assert any(e.event_type == "inspire_courage_end" for e in events)


# ---------------------------------------------------------------------------
# BD-05: Bard deafened -- effect expires on next tick
# ---------------------------------------------------------------------------

def test_bd05_bard_deafened_expires_effect():
    """BD-05: When bard has the DEAFENED condition, inspire courage expires on the next tick."""
    bard = _bard(conditions={"deafened": {"source": "test", "applied_at_event_id": 0}})
    ally = _ally(rounds=5)
    ws = _world({"bard": bard, "fighter": ally})

    events, ws2 = tick_inspire_courage(ws, 0, 0.0)

    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ACTIVE] is False
    assert any(e.event_type == "inspire_courage_end" for e in events)


# ---------------------------------------------------------------------------
# BD-06: bard_id cleared on expiry
# ---------------------------------------------------------------------------

def test_bd06_bard_id_cleared_on_expiry():
    """BD-06: INSPIRE_COURAGE_BARD_ID is set to None on all entities when effect expires."""
    bard = _bard(defeated=True)
    ally = _ally(rounds=4)
    ws = _world({"bard": bard, "fighter": ally})

    _, ws2 = tick_inspire_courage(ws, 0, 0.0)

    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_BARD_ID] is None


# ---------------------------------------------------------------------------
# BD-07: Effect expires on tick even with rounds remaining (bard defeated)
# ---------------------------------------------------------------------------

def test_bd07_rounds_remaining_does_not_prevent_expiry():
    """BD-07: Many rounds remaining does not prevent expiry when bard is incapacitated."""
    bard = _bard(defeated=True)
    ally = _ally(rounds=8)
    ws = _world({"bard": bard, "fighter": ally})

    _, ws2 = tick_inspire_courage(ws, 0, 0.0)

    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ACTIVE] is False
    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ROUNDS_REMAINING] == 0


# ---------------------------------------------------------------------------
# BD-08: Multiple allies all expire when bard goes down
# ---------------------------------------------------------------------------

def test_bd08_multiple_allies_all_expire():
    """BD-08: All allies' inspire courage expires on the same tick when the bard is defeated."""
    bard = _bard(defeated=True)
    ally1 = _ally(eid="fighter1", rounds=4)
    ally2 = _ally(eid="fighter2", rounds=7)
    ws = _world({"bard": bard, "fighter1": ally1, "fighter2": ally2})

    events, ws2 = tick_inspire_courage(ws, 0, 0.0)

    assert ws2.entities["fighter1"][EF.INSPIRE_COURAGE_ACTIVE] is False
    assert ws2.entities["fighter2"][EF.INSPIRE_COURAGE_ACTIVE] is False
    end_events = [e for e in events if e.event_type == "inspire_courage_end"]
    assert len(end_events) == 1
    affected = end_events[0].payload["affected_ids"]
    assert "fighter1" in affected
    assert "fighter2" in affected


# ---------------------------------------------------------------------------
# BD-09: _bard_is_incapacitated helper -- all three states
# ---------------------------------------------------------------------------

def test_bd09_incapacitated_helper_all_states():
    """BD-09: _bard_is_incapacitated returns True for defeated, dying, and deafened."""
    base = _bard()

    defeated = deepcopy(base)
    defeated[EF.DEFEATED] = True
    assert _bard_is_incapacitated(defeated) is True

    dying = deepcopy(base)
    dying[EF.DYING] = True
    assert _bard_is_incapacitated(dying) is True

    deafened = deepcopy(base)
    deafened[EF.CONDITIONS] = {"deafened": {"source": "test", "applied_at_event_id": 0}}
    assert _bard_is_incapacitated(deafened) is True

    healthy = deepcopy(base)
    assert _bard_is_incapacitated(healthy) is False


# ---------------------------------------------------------------------------
# BD-10: Unknown bard_id (bard not in entities) -- effect continues normally
# ---------------------------------------------------------------------------

def test_bd10_missing_bard_entity_does_not_crash():
    """BD-10: If INSPIRE_COURAGE_BARD_ID points to an entity not in world, tick proceeds
    normally (no KeyError) and the effect continues its countdown."""
    ally = _ally(rounds=3, bard_id="ghost_bard")
    ws = _world({"fighter": ally})  # bard not in entities

    _, ws2 = tick_inspire_courage(ws, 0, 0.0)

    # Effect should tick normally -- bard not found means no incapacitation check
    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ACTIVE] is True
    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ROUNDS_REMAINING] == 2
