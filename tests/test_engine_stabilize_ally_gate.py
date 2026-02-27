"""Gate tests: ENGINE-STABILIZE-ALLY — WO-ENGINE-STABILIZE-ALLY-001.

Tests:
SA-01: Actor Heal DC 15 succeeds → target EF.STABLE = True
SA-02: Actor Heal DC 15 fails → target EF.STABLE remains False, still bleeding
SA-03: stabilize_success event payload correct
SA-04: stabilize_failed event payload correct
SA-05: Target not dying (HP > 0) → stabilize_invalid, reason=target_not_dying
SA-06: Target already stable → stabilize_invalid, reason=target_not_dying
SA-07: Self-stabilization → stabilize_invalid, reason=cannot_stabilize_self
SA-08: Action budget: StabilizeIntent costs a standard action
SA-09: After success: EF.STABLE = True present on world_state.entities[target]
SA-10: Regression: AidAnotherIntent routing unchanged
"""

import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.core.stabilize_resolver import resolve_stabilize, STABILIZE_DC
from aidm.core.state import WorldState
from aidm.core.action_economy import get_action_type, ActionBudget, check_economy
from aidm.schemas.intents import StabilizeIntent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _actor(
    eid: str = "cleric",
    heal_ranks: int = 5,
    wis_mod: int = 2,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 15,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SKILL_RANKS: {"heal": heal_ranks},
        EF.CLASS_SKILLS: ["heal"],
        EF.WIS_MOD: wis_mod,
        EF.ARMOR_CHECK_PENALTY: 0,
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
    }


def _dying_target(
    eid: str = "fighter",
    hp: int = -3,
    stable: bool = False,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: 30,
        EF.AC: 14,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SKILL_RANKS: {},
        EF.WIS_MOD: 0,
        EF.ARMOR_CHECK_PENALTY: 0,
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.DEFEATED: False,
        EF.DYING: True,
        EF.STABLE: stable,
    }


def _world(actor: dict, target: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={
            actor[EF.ENTITY_ID]: actor,
            target[EF.ENTITY_ID]: target,
        },
        active_combat={
            "initiative_order": [actor[EF.ENTITY_ID], target[EF.ENTITY_ID]],
        },
    )


def _rng(heal_roll: int = 15):
    """Cleric Heal check uses rng.stream('combat').randint."""
    stream = mock.MagicMock()
    stream.randint.side_effect = [heal_roll] + [heal_roll] * 10
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _intent(actor_id: str = "cleric", target_id: str = "fighter") -> StabilizeIntent:
    return StabilizeIntent(actor_id=actor_id, target_id=target_id)


# ---------------------------------------------------------------------------
# SA-01: Heal success → EF.STABLE = True
# ---------------------------------------------------------------------------

def test_sa01_heal_success_sets_stable():
    """SA-01: Heal roll high enough → target EF.STABLE = True after resolve_stabilize."""
    # heal_ranks=5, wis_mod=2 → bonus=7; roll=8 → total=15 → success
    actor = _actor(heal_ranks=5, wis_mod=2)
    target = _dying_target(hp=-3)
    ws = _world(actor, target)
    rng = _rng(heal_roll=8)

    events, ws_after = resolve_stabilize(_intent(), ws, rng, 0, 0.0)

    success_evts = [e for e in events if e.event_type == "stabilize_success"]
    assert len(success_evts) == 1, "stabilize_success event must be emitted on success"
    assert ws_after.entities["fighter"][EF.STABLE] is True, "EF.STABLE must be True after success"


# ---------------------------------------------------------------------------
# SA-02: Heal failure → EF.STABLE remains False
# ---------------------------------------------------------------------------

def test_sa02_heal_fail_stable_unchanged():
    """SA-02: Heal roll too low → EF.STABLE remains False."""
    # heal_ranks=0, wis_mod=0 → bonus=0; roll=5 → total=5 < 15 → fail
    actor = _actor(heal_ranks=0, wis_mod=0)
    target = _dying_target(hp=-5)
    ws = _world(actor, target)
    rng = _rng(heal_roll=5)

    events, ws_after = resolve_stabilize(_intent(), ws, rng, 0, 0.0)

    fail_evts = [e for e in events if e.event_type == "stabilize_failed"]
    assert len(fail_evts) == 1, "stabilize_failed event must be emitted on fail"
    assert ws_after.entities["fighter"].get(EF.STABLE, False) is False, (
        "EF.STABLE must remain False on fail"
    )


# ---------------------------------------------------------------------------
# SA-03: stabilize_success event payload fields
# ---------------------------------------------------------------------------

def test_sa03_success_event_payload():
    """SA-03: stabilize_success event contains required payload fields."""
    actor = _actor(heal_ranks=5, wis_mod=2)
    target = _dying_target(hp=-4)
    ws = _world(actor, target)
    rng = _rng(heal_roll=8)  # 8 + 7 = 15 → success

    events, _ = resolve_stabilize(_intent(), ws, rng, 0, 0.0)

    evt = next(e for e in events if e.event_type == "stabilize_success")
    required = {"actor_id", "target_id", "heal_roll", "heal_bonus", "heal_total", "dc", "target_hp"}
    missing = required - set(evt.payload.keys())
    assert not missing, f"Missing stabilize_success payload fields: {missing}"
    assert evt.payload["dc"] == STABILIZE_DC
    assert evt.payload["actor_id"] == "cleric"
    assert evt.payload["target_id"] == "fighter"
    assert evt.payload["target_hp"] == -4


# ---------------------------------------------------------------------------
# SA-04: stabilize_failed event payload fields
# ---------------------------------------------------------------------------

def test_sa04_failed_event_payload():
    """SA-04: stabilize_failed event contains required payload fields."""
    actor = _actor(heal_ranks=0, wis_mod=0)
    target = _dying_target(hp=-7)
    ws = _world(actor, target)
    rng = _rng(heal_roll=3)

    events, _ = resolve_stabilize(_intent(), ws, rng, 0, 0.0)

    evt = next(e for e in events if e.event_type == "stabilize_failed")
    required = {"actor_id", "target_id", "heal_roll", "heal_bonus", "heal_total", "dc", "target_hp"}
    missing = required - set(evt.payload.keys())
    assert not missing, f"Missing stabilize_failed payload fields: {missing}"
    assert evt.payload["dc"] == STABILIZE_DC
    assert evt.payload["target_hp"] == -7


# ---------------------------------------------------------------------------
# SA-05: Target not dying (HP > 0) → stabilize_invalid
# ---------------------------------------------------------------------------

def test_sa05_target_not_dying_invalid():
    """SA-05: Target at HP > 0 → stabilize_invalid, reason=target_not_dying."""
    actor = _actor()
    target = _dying_target(hp=5)  # alive, not dying
    target[EF.DYING] = False
    ws = _world(actor, target)
    rng = _rng(heal_roll=15)

    events, _ = resolve_stabilize(_intent(), ws, rng, 0, 0.0)

    invalid_evts = [e for e in events if e.event_type == "stabilize_invalid"]
    assert len(invalid_evts) == 1
    assert invalid_evts[0].payload["reason"] == "target_not_dying"


# ---------------------------------------------------------------------------
# SA-06: Target already stable → stabilize_invalid
# ---------------------------------------------------------------------------

def test_sa06_already_stable_invalid():
    """SA-06: Target at HP=-3 but EF.STABLE=True → stabilize_invalid."""
    actor = _actor()
    target = _dying_target(hp=-3, stable=True)
    ws = _world(actor, target)
    rng = _rng(heal_roll=15)

    events, _ = resolve_stabilize(_intent(), ws, rng, 0, 0.0)

    invalid_evts = [e for e in events if e.event_type == "stabilize_invalid"]
    assert len(invalid_evts) == 1, "stabilize_invalid must fire for already-stable target"


# ---------------------------------------------------------------------------
# SA-07: Self-stabilization → stabilize_invalid
# ---------------------------------------------------------------------------

def test_sa07_self_stabilization_rejected():
    """SA-07: Actor tries to stabilize self → stabilize_invalid, cannot_stabilize_self."""
    actor = _dying_target(eid="fighter", hp=-3)  # dying actor tries to stabilize themselves
    actor[EF.SKILL_RANKS] = {"heal": 5}
    actor[EF.WIS_MOD] = 2
    actor[EF.ARMOR_CHECK_PENALTY] = 0
    ws = WorldState(
        ruleset_version="3.5e",
        entities={"fighter": actor},
        active_combat={"initiative_order": ["fighter"]},
    )
    rng = _rng(heal_roll=15)

    events, _ = resolve_stabilize(
        StabilizeIntent(actor_id="fighter", target_id="fighter"),
        ws, rng, 0, 0.0,
    )

    invalid_evts = [e for e in events if e.event_type == "stabilize_invalid"]
    assert len(invalid_evts) == 1
    assert invalid_evts[0].payload["reason"] == "cannot_stabilize_self"


# ---------------------------------------------------------------------------
# SA-08: Action budget — StabilizeIntent costs standard action
# ---------------------------------------------------------------------------

def test_sa08_action_budget_standard():
    """SA-08: get_action_type(StabilizeIntent) returns 'standard'."""
    intent = _intent()
    action_type = get_action_type(intent)
    assert action_type == "standard", (
        f"StabilizeIntent must cost a standard action, got '{action_type}'"
    )

    # Verify check_economy blocks second standard action
    budget = ActionBudget(standard_used=True)
    denied = check_economy(intent, budget)
    assert denied == "standard", "StabilizeIntent should be denied when standard already used"


# ---------------------------------------------------------------------------
# SA-09: World state mutation — entities[target][EF.STABLE] confirmed True after success
# ---------------------------------------------------------------------------

def test_sa09_world_state_stable_flag_set():
    """SA-09: On success, ws.entities[target_id][EF.STABLE] is True in returned world_state."""
    actor = _actor(heal_ranks=8, wis_mod=3)  # bonus=11; roll=4 → total=15 → success
    target = _dying_target(hp=-1)
    ws = _world(actor, target)
    rng = _rng(heal_roll=4)

    _, ws_after = resolve_stabilize(_intent(), ws, rng, 0, 0.0)

    assert EF.STABLE in ws_after.entities["fighter"], "EF.STABLE must be present on entity"
    assert ws_after.entities["fighter"][EF.STABLE] is True


# ---------------------------------------------------------------------------
# SA-10: Regression — AidAnotherIntent routing unchanged
# ---------------------------------------------------------------------------

def test_sa10_regression_aid_another_unaffected():
    """SA-10: AidAnotherIntent action type is still 'standard' (regression)."""
    from aidm.schemas.intents import AidAnotherIntent
    intent = AidAnotherIntent(
        actor_id="cleric",
        ally_id="fighter",
        enemy_id="orc",
        aid_type="attack",
    )
    action_type = get_action_type(intent)
    assert action_type == "standard", (
        f"AidAnotherIntent action type regression: expected 'standard', got '{action_type}'"
    )
