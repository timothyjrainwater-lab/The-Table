"""Gate tests: WO-ENGINE-RAGE-HP-TRANSITION-001

ENGINE-RAGE-HP-TRANSITION: HP gain on rage enter (+2 per HD from CON+4),
HP loss on rage exit, unconsciousness if HP drops to 0.
PHB p.25: "These extra hit points are not lost first the way temporary hit
points are."

RHPT-001 – RHPT-008 (8 tests)
"""
import pytest
from copy import deepcopy

from aidm.core.rage_resolver import activate_rage, end_rage, validate_rage
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _barbarian(level=5, hp_current=None, hp_max=None, con_mod=2, extra_classes=None):
    """Build a barbarian entity dict for testing."""
    class_levels = {"barbarian": level}
    if extra_classes:
        class_levels.update(extra_classes)
    total_hd = sum(class_levels.values())
    _hp_max = hp_max if hp_max is not None else total_hd * 10
    _hp_cur = hp_current if hp_current is not None else _hp_max
    return {
        EF.ENTITY_ID: "barb1",
        EF.TEAM: "player",
        EF.HP_CURRENT: _hp_cur,
        EF.HP_MAX: _hp_max,
        EF.CLASS_LEVELS: class_levels,
        EF.CON_MOD: con_mod,
        EF.STR_MOD: 3,
        EF.RAGE_ACTIVE: False,
        EF.RAGE_USES_REMAINING: 2,
        EF.RAGE_ROUNDS_REMAINING: 0,
        EF.FATIGUED: False,
        EF.TEMPORARY_MODIFIERS: {},
        EF.CONDITIONS: {},
        EF.DEFEATED: False,
    }


def _ws(entity):
    return WorldState(
        ruleset_version="3.5",
        entities={entity[EF.ENTITY_ID]: entity},
        active_combat=None,
    )


# ---------------------------------------------------------------------------
# RHPT-001: Barbarian L5 (5 HD) enters rage → HP increases by 10 (2 * 5)
# ---------------------------------------------------------------------------

def test_rhpt_001_hp_gain_on_rage_enter():
    """RHPT-001: Barbarian L5 enters rage → HP +10."""
    entity = _barbarian(level=5, hp_max=50, hp_current=50, con_mod=2)
    ws = _ws(entity)
    events, new_ws = activate_rage("barb1", ws, next_event_id=1, timestamp=1.0)
    actor = new_ws.entities["barb1"]
    assert actor[EF.HP_CURRENT] == 60  # 50 + 2*5
    assert actor[EF.HP_MAX] == 60
    rage_ev = [e for e in events if e.event_type == "rage_start"]
    assert len(rage_ev) == 1
    assert rage_ev[0].payload["hp_gain"] == 10


# ---------------------------------------------------------------------------
# RHPT-002: Barbarian L5 exits rage → HP decreases by 10
# ---------------------------------------------------------------------------

def test_rhpt_002_hp_loss_on_rage_exit():
    """RHPT-002: Barbarian L5 exits rage → HP -10."""
    entity = _barbarian(level=5, hp_max=60, hp_current=60, con_mod=2)
    entity[EF.RAGE_ACTIVE] = True
    entity[EF.RAGE_ROUNDS_REMAINING] = 1
    entity[EF.TEMPORARY_MODIFIERS] = {
        "rage_str_bonus": 4, "rage_con_bonus": 4,
        "rage_will_bonus": 2, "rage_ac_penalty": -2,
    }
    ws = _ws(entity)
    events, new_ws = end_rage("barb1", ws, next_event_id=1, timestamp=1.0)
    actor = new_ws.entities["barb1"]
    assert actor[EF.HP_CURRENT] == 50  # 60 - 2*5
    assert actor[EF.HP_MAX] == 50
    rage_ev = [e for e in events if e.event_type == "rage_end"]
    assert len(rage_ev) == 1
    assert rage_ev[0].payload["hp_loss"] == 10


# ---------------------------------------------------------------------------
# RHPT-003: Full cycle — HP returns to original value
# ---------------------------------------------------------------------------

def test_rhpt_003_full_cycle_hp_roundtrip():
    """RHPT-003: Barbarian at full HP enters/exits rage → HP returns to original."""
    entity = _barbarian(level=5, hp_max=50, hp_current=50, con_mod=2)
    ws = _ws(entity)
    # Enter rage
    events1, ws_raged = activate_rage("barb1", ws, next_event_id=1, timestamp=1.0)
    assert ws_raged.entities["barb1"][EF.HP_CURRENT] == 60
    # Exit rage
    events2, ws_after = end_rage("barb1", ws_raged, next_event_id=10, timestamp=2.0)
    assert ws_after.entities["barb1"][EF.HP_CURRENT] == 50
    assert ws_after.entities["barb1"][EF.HP_MAX] == 50


# ---------------------------------------------------------------------------
# RHPT-004: Damaged during rage → exits with lower HP
# ---------------------------------------------------------------------------

def test_rhpt_004_damaged_during_rage():
    """RHPT-004: Barbarian takes 25 damage during rage, exits → lower HP."""
    entity = _barbarian(level=5, hp_max=50, hp_current=50, con_mod=2)
    ws = _ws(entity)
    # Enter rage: HP goes to 60
    events1, ws_raged = activate_rage("barb1", ws, next_event_id=1, timestamp=1.0)
    assert ws_raged.entities["barb1"][EF.HP_CURRENT] == 60
    # Simulate 25 damage during rage
    entities = deepcopy(ws_raged.entities)
    entities["barb1"][EF.HP_CURRENT] = 35  # 60 - 25 = 35
    ws_damaged = WorldState(
        ruleset_version="3.5", entities=entities, active_combat=None,
    )
    # Exit rage: HP goes to 35 - 10 = 25
    events2, ws_after = end_rage("barb1", ws_damaged, next_event_id=10, timestamp=2.0)
    assert ws_after.entities["barb1"][EF.HP_CURRENT] == 25


# ---------------------------------------------------------------------------
# RHPT-005: HP drops to negative → unconscious
# ---------------------------------------------------------------------------

def test_rhpt_005_unconscious_on_rage_exit():
    """RHPT-005: Barbarian at 8 HP, 5 HD → exits rage → HP = -2 → unconscious."""
    entity = _barbarian(level=5, hp_max=60, hp_current=8, con_mod=2)
    entity[EF.RAGE_ACTIVE] = True
    entity[EF.RAGE_ROUNDS_REMAINING] = 1
    entity[EF.TEMPORARY_MODIFIERS] = {
        "rage_str_bonus": 4, "rage_con_bonus": 4,
        "rage_will_bonus": 2, "rage_ac_penalty": -2,
    }
    ws = _ws(entity)
    events, new_ws = end_rage("barb1", ws, next_event_id=1, timestamp=1.0)
    actor = new_ws.entities["barb1"]
    assert actor[EF.HP_CURRENT] == -2  # 8 - 10
    # Must emit unconsciousness event
    uncon_events = [e for e in events if e.event_type == "entity_unconscious"]
    assert len(uncon_events) == 1
    assert uncon_events[0].payload["entity_id"] == "barb1"
    assert uncon_events[0].payload["reason"] == "rage_hp_loss"


# ---------------------------------------------------------------------------
# RHPT-006: HP drops to exactly 0 → unconscious (boundary)
# ---------------------------------------------------------------------------

def test_rhpt_006_boundary_zero_hp():
    """RHPT-006: Barbarian at exactly 10 HP, 5 HD → exits rage → HP = 0 → unconscious."""
    entity = _barbarian(level=5, hp_max=60, hp_current=10, con_mod=2)
    entity[EF.RAGE_ACTIVE] = True
    entity[EF.RAGE_ROUNDS_REMAINING] = 1
    entity[EF.TEMPORARY_MODIFIERS] = {
        "rage_str_bonus": 4, "rage_con_bonus": 4,
        "rage_will_bonus": 2, "rage_ac_penalty": -2,
    }
    ws = _ws(entity)
    events, new_ws = end_rage("barb1", ws, next_event_id=1, timestamp=1.0)
    assert new_ws.entities["barb1"][EF.HP_CURRENT] == 0
    uncon_events = [e for e in events if e.event_type == "entity_unconscious"]
    assert len(uncon_events) == 1


# ---------------------------------------------------------------------------
# RHPT-007: HP drops to 1 → still conscious (boundary)
# ---------------------------------------------------------------------------

def test_rhpt_007_boundary_one_hp_conscious():
    """RHPT-007: Barbarian at 11 HP, 5 HD → exits rage → HP = 1 → still conscious."""
    entity = _barbarian(level=5, hp_max=60, hp_current=11, con_mod=2)
    entity[EF.RAGE_ACTIVE] = True
    entity[EF.RAGE_ROUNDS_REMAINING] = 1
    entity[EF.TEMPORARY_MODIFIERS] = {
        "rage_str_bonus": 4, "rage_con_bonus": 4,
        "rage_will_bonus": 2, "rage_ac_penalty": -2,
    }
    ws = _ws(entity)
    events, new_ws = end_rage("barb1", ws, next_event_id=1, timestamp=1.0)
    assert new_ws.entities["barb1"][EF.HP_CURRENT] == 1
    uncon_events = [e for e in events if e.event_type == "entity_unconscious"]
    assert len(uncon_events) == 0


# ---------------------------------------------------------------------------
# RHPT-008: Max HP adjusts both directions correctly
# ---------------------------------------------------------------------------

def test_rhpt_008_max_hp_adjusts_both_directions():
    """RHPT-008: Max HP correctly adjusts both directions (enter +10, exit -10)."""
    entity = _barbarian(level=5, hp_max=50, hp_current=50, con_mod=2)
    ws = _ws(entity)
    # Enter: max_hp goes 50 → 60
    _, ws_raged = activate_rage("barb1", ws, next_event_id=1, timestamp=1.0)
    assert ws_raged.entities["barb1"][EF.HP_MAX] == 60
    # Exit: max_hp goes 60 → 50
    _, ws_after = end_rage("barb1", ws_raged, next_event_id=10, timestamp=2.0)
    assert ws_after.entities["barb1"][EF.HP_MAX] == 50
