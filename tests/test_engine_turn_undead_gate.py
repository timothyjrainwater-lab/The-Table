"""Gate ENGINE-TURN-UNDEAD — WO-ENGINE-TURN-UNDEAD-001: Turn/Destroy Undead.

Tests (10/10):
TU-01: TurnUndeadIntent consumes a standard action slot
TU-02: TURN_UNDEAD_USES == 0 → turn_undead_uses_exhausted, no other events
TU-03: turning_check_rolled event has correct roll (2d6 + cleric_level + CHA_mod)
TU-04: Undead with HD > cleric_level + 4 → undead_immune_to_turning event
TU-05: Good cleric + undead HD ≤ turning check → undead_turned + TURNED condition applied
TU-06: Good cleric + undead HD ≤ cleric_level - 4 → undead_destroyed + entity defeated
TU-07: Evil cleric → undead_rebuked instead of undead_turned for eligible targets
TU-08: Paladin uses paladin_level // 2 as effective cleric level for turning
TU-09: HP budget (2d6×10) limits affected targets; lowest HD processed first; stops at budget
TU-10: TURN_UNDEAD_USES decrements by 1; restored to MAX on overnight rest
"""

import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.core.action_economy import get_action_type
from aidm.core.rest_resolver import resolve_rest
from aidm.core.state import WorldState
from aidm.core.turn_undead_resolver import (
    apply_turn_undead_events,
    resolve_turn_undead,
)
from aidm.schemas.conditions import ConditionType
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RestIntent, TurnUndeadIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cleric(
    eid: str = "cleric1",
    level: int = 5,
    cha_mod: int = 2,
    uses: int = 5,
    uses_max: int = 5,
    class_levels: Dict = None,
    class_features: Dict = None,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 15,
        EF.LEVEL: level,
        EF.CHA_MOD: cha_mod,
        EF.TURN_UNDEAD_USES: uses,
        EF.TURN_UNDEAD_USES_MAX: uses_max,
        EF.CLASS_LEVELS: class_levels if class_levels is not None else {"cleric": level},
        "class_features": class_features if class_features is not None else {},
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 0, "y": 0},
    }


def _undead(
    eid: str,
    hd: int,
    hp: int = None,
    hp_max: int = None,
) -> Dict[str, Any]:
    hp_max = hp_max if hp_max is not None else hd * 5
    hp = hp if hp is not None else hp_max
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: 12,
        EF.HD_COUNT: hd,
        EF.IS_UNDEAD: True,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 1, "y": 0},
    }


def _world(*entities) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={e[EF.ENTITY_ID]: e for e in entities},
        active_combat={"initiative_order": [e[EF.ENTITY_ID] for e in entities]},
    )


def _rng_fixed(*rolls):
    """RNG that returns rolls from the combat stream in order."""
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [3] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# TU-01: TurnUndeadIntent → standard action slot
# ---------------------------------------------------------------------------

def test_tu01_turn_undead_is_standard_action():
    """TurnUndeadIntent registers as a standard action in action_economy."""
    intent = TurnUndeadIntent(cleric_id="c1", target_ids=[])
    assert get_action_type(intent) == "standard"


# ---------------------------------------------------------------------------
# TU-02: TURN_UNDEAD_USES == 0 → uses_exhausted event, nothing else
# ---------------------------------------------------------------------------

def test_tu02_no_uses_exhausted_event():
    """TURN_UNDEAD_USES == 0 → turn_undead_uses_exhausted emitted, no other events."""
    cleric = _cleric(uses=0)
    ws = _world(cleric)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=[])
    rng = _rng_fixed()

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    assert len(events) == 1
    assert events[0].event_type == "turn_undead_uses_exhausted"
    assert events[0].payload["uses_remaining"] == 0
    assert events[0].payload["cleric_id"] == "cleric1"


# ---------------------------------------------------------------------------
# TU-03: turning_check_rolled event has correct arithmetic
# ---------------------------------------------------------------------------

def test_tu03_turning_check_rolled_event():
    """turning_check_rolled: roll_result = d1+d2+cleric_level+cha_mod, all fields present."""
    cleric = _cleric(level=5, cha_mod=2, uses=3)
    ws = _world(cleric)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=[])
    # Turning check dice: d1=3, d2=4 → 7 + 5 + 2 = 14
    # Budget dice: d1=2, d2=3 → (2+3)*10 = 50
    rng = _rng_fixed(3, 4, 2, 3)

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    tc_ev = next((e for e in events if e.event_type == "turning_check_rolled"), None)
    assert tc_ev is not None
    p = tc_ev.payload
    assert p["roll_result"] == 14  # 3+4+5+2
    assert p["cleric_level"] == 5
    assert p["cha_mod"] == 2
    assert p["hp_budget"] == 50  # (2+3)*10
    assert p["cleric_id"] == "cleric1"
    assert "is_evil" in p


# ---------------------------------------------------------------------------
# TU-04: Undead HD > cleric_level + 4 → immune
# ---------------------------------------------------------------------------

def test_tu04_undead_immune_to_turning():
    """Undead with HD > cleric_level + 4 → undead_immune_to_turning event."""
    cleric = _cleric(level=3, cha_mod=1, uses=3)
    # HD 8 > 3 + 4 = 7 → immune
    zombie = _undead("zombie1", hd=8, hp_max=40)
    ws = _world(cleric, zombie)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=["zombie1"])
    # Turning check: 5+5+3+1=14; budget: 3+3=6*10=60
    rng = _rng_fixed(5, 5, 3, 3)

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    immune_ev = next((e for e in events if e.event_type == "undead_immune_to_turning"), None)
    assert immune_ev is not None
    assert immune_ev.payload["target_id"] == "zombie1"
    assert immune_ev.payload["target_hd"] == 8
    assert immune_ev.payload["cleric_level"] == 3

    # Immune targets don't get turned or destroyed
    assert not any(e.event_type in ("undead_turned", "undead_destroyed") for e in events)


# ---------------------------------------------------------------------------
# TU-05: Good cleric + HD ≤ turning check → undead_turned + TURNED condition
# ---------------------------------------------------------------------------

def test_tu05_undead_turned_condition_applied():
    """Good cleric, undead HD ≤ turning check → undead_turned; apply gives TURNED condition."""
    cleric = _cleric(level=5, cha_mod=2, uses=3)
    # HD 3 ≤ turning check (guaranteed with dice 6+6=12 + 5 + 2 = 19)
    zombie = _undead("zombie1", hd=3, hp_max=15)
    ws = _world(cleric, zombie)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=["zombie1"])
    # Turning check: 6+6+5+2=19; budget: 3+3=60
    # HP_MAX=15 ≤ budget 60 ✓; HD=3 ≤ 19 ✓; HD=3 > 5-4=1 → turned (not destroyed)
    rng = _rng_fixed(6, 6, 3, 3)

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    turned_ev = next((e for e in events if e.event_type == "undead_turned"), None)
    assert turned_ev is not None
    assert turned_ev.payload["target_id"] == "zombie1"
    assert turned_ev.payload["duration_rounds"] == 10

    # Apply and check condition
    updated = apply_turn_undead_events(events, ws)
    zombie_after = updated.entities["zombie1"]
    conds = zombie_after.get(EF.CONDITIONS, {})
    assert ConditionType.TURNED.value in conds


# ---------------------------------------------------------------------------
# TU-06: Good cleric + HD ≤ cleric_level - 4 → undead_destroyed
# ---------------------------------------------------------------------------

def test_tu06_undead_destroyed():
    """Good cleric level 10, zombie HD 2 (≤ 10-4=6) → undead_destroyed + entity defeated."""
    cleric = _cleric(level=10, cha_mod=2, uses=3, class_levels={"cleric": 10})
    zombie = _undead("zombie1", hd=2, hp_max=10)
    ws = _world(cleric, zombie)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=["zombie1"])
    # Turning check: 4+4+10+2=20; budget: 3+3=60
    rng = _rng_fixed(4, 4, 3, 3)

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    destroyed_ev = next((e for e in events if e.event_type == "undead_destroyed"), None)
    assert destroyed_ev is not None
    assert destroyed_ev.payload["target_id"] == "zombie1"

    updated = apply_turn_undead_events(events, ws)
    zombie_after = updated.entities["zombie1"]
    assert zombie_after[EF.DEFEATED] is True
    assert zombie_after[EF.HP_CURRENT] == -10


# ---------------------------------------------------------------------------
# TU-07: Evil cleric → undead_rebuked
# ---------------------------------------------------------------------------

def test_tu07_evil_cleric_rebukes():
    """Evil cleric (channels_negative_energy) → undead_rebuked instead of undead_turned."""
    cleric = _cleric(
        level=5, cha_mod=2, uses=3,
        class_features={"channels_negative_energy": True}
    )
    zombie = _undead("zombie1", hd=3, hp_max=15)
    ws = _world(cleric, zombie)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=["zombie1"])
    # Turning check: 6+6+5+2=19; budget: 3+3=60
    rng = _rng_fixed(6, 6, 3, 3)

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    assert not any(e.event_type == "undead_turned" for e in events)
    rebuked_ev = next((e for e in events if e.event_type == "undead_rebuked"), None)
    assert rebuked_ev is not None
    assert rebuked_ev.payload["target_id"] == "zombie1"


# ---------------------------------------------------------------------------
# TU-08: Paladin uses paladin_level // 2 as effective cleric level
# ---------------------------------------------------------------------------

def test_tu08_paladin_effective_level():
    """Paladin level 6 → effective turning level = 3 (6 // 2)."""
    paladin = _cleric(
        eid="paladin1", level=6, cha_mod=1, uses=4, uses_max=4,
        class_levels={"paladin": 6}
    )
    # HD 2 ≤ cleric_eff 3 but NOT ≤ 3-4=-1 → turned (not destroyed)
    # Turning check: 4+4+3+1=12; HD=2 ≤ 12 → turned
    zombie = _undead("zombie1", hd=2, hp_max=10)
    ws = _world(paladin, zombie)
    intent = TurnUndeadIntent(cleric_id="paladin1", target_ids=["zombie1"])
    rng = _rng_fixed(4, 4, 3, 3)

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    tc_ev = next((e for e in events if e.event_type == "turning_check_rolled"), None)
    assert tc_ev is not None
    assert tc_ev.payload["cleric_level"] == 3  # 6 // 2

    turned_ev = next((e for e in events if e.event_type == "undead_turned"), None)
    assert turned_ev is not None


# ---------------------------------------------------------------------------
# TU-09: HP budget limits targets; lowest HD first; stops at budget
# ---------------------------------------------------------------------------

def test_tu09_hp_budget_limits_targets():
    """HP budget (2d6×10) limits which undead are affected; lowest HD processed first."""
    cleric = _cleric(level=10, cha_mod=2, uses=3, class_levels={"cleric": 10})
    # Two targets: zombie HD=2 (HP_MAX=10), spectre HD=7 (HP_MAX=35)
    # Budget: (1+1)*10=20 → zombie (10) fits, spectre (35) does not
    zombie = _undead("zombie1", hd=2, hp_max=10)
    spectre = _undead("spectre1", hd=7, hp_max=35)
    ws = _world(cleric, zombie, spectre)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=["zombie1", "spectre1"])
    # Turning check: 6+6+10+2=24 (both ≤ 24); budget dice: 1+1=2*10=20
    rng = _rng_fixed(6, 6, 1, 1)

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    # Zombie destroyed (HD 2 ≤ 10-4=6), spectre skipped (HP_MAX 35 > budget 20)
    destroyed = [e for e in events if e.event_type == "undead_destroyed"]
    assert len(destroyed) == 1
    assert destroyed[0].payload["target_id"] == "zombie1"

    turned = [e for e in events if e.event_type == "undead_turned"]
    assert len(turned) == 0  # spectre skipped by budget


# ---------------------------------------------------------------------------
# TU-10: Uses decrement + overnight rest restores
# ---------------------------------------------------------------------------

def test_tu10_uses_decrement_and_rest_restore():
    """TURN_UNDEAD_USES decrements by 1 per use; overnight rest restores to MAX."""
    cleric = _cleric(level=5, cha_mod=1, uses=3, uses_max=4)
    ws = _world(cleric)
    intent = TurnUndeadIntent(cleric_id="cleric1", target_ids=[])
    rng = _rng_fixed(3, 3, 2, 2)

    events = resolve_turn_undead(intent, ws, rng, next_event_id=0, timestamp=0.0)

    use_ev = next((e for e in events if e.event_type == "turn_undead_use_spent"), None)
    assert use_ev is not None
    assert use_ev.payload["uses_remaining"] == 2  # 3 - 1

    updated = apply_turn_undead_events(events, ws)
    assert updated.entities["cleric1"][EF.TURN_UNDEAD_USES] == 2

    # Overnight rest should restore to MAX=4
    ws_no_combat = WorldState(
        ruleset_version="3.5e",
        entities=updated.entities,
        active_combat=None,
    )
    rest_intent = RestIntent(rest_type="overnight")
    resolve_rest(rest_intent, ws_no_combat, actor_id="cleric1")
    assert ws_no_combat.entities["cleric1"][EF.TURN_UNDEAD_USES] == 4
