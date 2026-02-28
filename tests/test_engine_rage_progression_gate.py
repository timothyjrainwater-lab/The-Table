"""Gate tests: WO-ENGINE-RAGE-PROGRESSION-001

Level-gated rage bonuses: Greater Rage (L11), Mighty Rage (L20), Tireless Rage (L17).

RAP-001 – RAP-008 (8 tests)
"""
import pytest
from copy import deepcopy

from aidm.core.rage_resolver import activate_rage, end_rage
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


def _barbarian(barb_level, hp=50, con_mod=2):
    """Create minimal barbarian entity at given level."""
    return {
        EF.ENTITY_ID: "barb",
        EF.CLASS_LEVELS: {"barbarian": barb_level},
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.CON_MOD: con_mod,
        EF.RAGE_ACTIVE: False,
        EF.RAGE_USES_REMAINING: 3,
        EF.RAGE_ROUNDS_REMAINING: 0,
        EF.FATIGUED: False,
        EF.TEMPORARY_MODIFIERS: {},
    }


def _ws(entity):
    eid = entity[EF.ENTITY_ID]
    return WorldState(ruleset_version="3.5", entities={eid: entity}, active_combat=None)


# ---------------------------------------------------------------------------
# RAP-001: Barbarian L1 → base rage: STR +4, CON +4, Will +2, AC -2
# ---------------------------------------------------------------------------

def test_rap_001_base_rage_l1():
    """RAP-001: L1 barbarian gets base rage bonuses."""
    entity = _barbarian(1)
    ws = _ws(entity)
    events, new_ws = activate_rage("barb", ws, next_event_id=1, timestamp=0.0)
    actor = new_ws.entities["barb"]
    mods = actor[EF.TEMPORARY_MODIFIERS]
    assert mods["rage_str_bonus"] == 4
    assert mods["rage_con_bonus"] == 4
    assert mods["rage_will_bonus"] == 2
    assert mods["rage_ac_penalty"] == -2


# ---------------------------------------------------------------------------
# RAP-002: Barbarian L11 → Greater Rage: STR +6, CON +6, Will +3, AC -2
# ---------------------------------------------------------------------------

def test_rap_002_greater_rage_l11():
    """RAP-002: L11 barbarian gets Greater Rage bonuses."""
    entity = _barbarian(11)
    ws = _ws(entity)
    events, new_ws = activate_rage("barb", ws, next_event_id=1, timestamp=0.0)
    actor = new_ws.entities["barb"]
    mods = actor[EF.TEMPORARY_MODIFIERS]
    assert mods["rage_str_bonus"] == 6
    assert mods["rage_con_bonus"] == 6
    assert mods["rage_will_bonus"] == 3
    assert mods["rage_ac_penalty"] == -2


# ---------------------------------------------------------------------------
# RAP-003: Barbarian L20 → Mighty Rage: STR +8, CON +8, Will +4, AC -2
# ---------------------------------------------------------------------------

def test_rap_003_mighty_rage_l20():
    """RAP-003: L20 barbarian gets Mighty Rage bonuses."""
    entity = _barbarian(20)
    ws = _ws(entity)
    events, new_ws = activate_rage("barb", ws, next_event_id=1, timestamp=0.0)
    actor = new_ws.entities["barb"]
    mods = actor[EF.TEMPORARY_MODIFIERS]
    assert mods["rage_str_bonus"] == 8
    assert mods["rage_con_bonus"] == 8
    assert mods["rage_will_bonus"] == 4
    assert mods["rage_ac_penalty"] == -2


# ---------------------------------------------------------------------------
# RAP-004: Barbarian L17 → Tireless Rage: rage ends, EF.FATIGUED remains False
# ---------------------------------------------------------------------------

def test_rap_004_tireless_rage_l17():
    """RAP-004: L17 barbarian ends rage without fatigue."""
    entity = _barbarian(17)
    ws = _ws(entity)
    events, ws2 = activate_rage("barb", ws, next_event_id=1, timestamp=0.0)
    events, ws3 = end_rage("barb", ws2, next_event_id=2, timestamp=1.0)
    actor = ws3.entities["barb"]
    assert actor[EF.FATIGUED] is False
    # No fatigue penalties in temp mods
    mods = actor.get(EF.TEMPORARY_MODIFIERS, {})
    assert "fatigued_str_penalty" not in mods
    assert "fatigued_dex_penalty" not in mods


# ---------------------------------------------------------------------------
# RAP-005: Barbarian L16 → NOT tireless: rage ends, EF.FATIGUED = True
# ---------------------------------------------------------------------------

def test_rap_005_not_tireless_l16():
    """RAP-005: L16 barbarian (below tireless threshold) gets fatigued."""
    entity = _barbarian(16)
    ws = _ws(entity)
    events, ws2 = activate_rage("barb", ws, next_event_id=1, timestamp=0.0)
    events, ws3 = end_rage("barb", ws2, next_event_id=2, timestamp=1.0)
    actor = ws3.entities["barb"]
    assert actor[EF.FATIGUED] is True
    mods = actor.get(EF.TEMPORARY_MODIFIERS, {})
    assert mods.get("fatigued_str_penalty") == -2


# ---------------------------------------------------------------------------
# RAP-006: Barbarian L10 → still base rage (just below Greater Rage threshold)
# ---------------------------------------------------------------------------

def test_rap_006_base_rage_l10():
    """RAP-006: L10 barbarian gets base rage, not Greater."""
    entity = _barbarian(10)
    ws = _ws(entity)
    events, new_ws = activate_rage("barb", ws, next_event_id=1, timestamp=0.0)
    actor = new_ws.entities["barb"]
    mods = actor[EF.TEMPORARY_MODIFIERS]
    assert mods["rage_str_bonus"] == 4, "L10 should still be base rage, not Greater"
    assert mods["rage_con_bonus"] == 4
    assert mods["rage_will_bonus"] == 2


# ---------------------------------------------------------------------------
# RAP-007: Multiclass Barbarian 11 / Fighter 2 → Greater Rage (barbarian level)
# ---------------------------------------------------------------------------

def test_rap_007_multiclass_greater_rage():
    """RAP-007: Barbarian 11/Fighter 2 uses barbarian level for rage tier."""
    entity = _barbarian(11)
    entity[EF.CLASS_LEVELS] = {"barbarian": 11, "fighter": 2}
    ws = _ws(entity)
    events, new_ws = activate_rage("barb", ws, next_event_id=1, timestamp=0.0)
    actor = new_ws.entities["barb"]
    mods = actor[EF.TEMPORARY_MODIFIERS]
    assert mods["rage_str_bonus"] == 6, "Greater Rage based on barbarian level 11"
    # HP gain: +6 CON → +3 HP/HD × 13 HD (11 barb + 2 fighter) = 39
    assert events[0].payload["hp_gain"] == 3 * 13


# ---------------------------------------------------------------------------
# RAP-008: Tireless Rage: HP loss still occurs on rage exit
# ---------------------------------------------------------------------------

def test_rap_008_tireless_hp_loss_still_occurs():
    """RAP-008: L17+ tireless barbarian still loses HP when rage ends."""
    entity = _barbarian(17, hp=100)
    ws = _ws(entity)
    events, ws2 = activate_rage("barb", ws, next_event_id=1, timestamp=0.0)
    hp_after_rage = ws2.entities["barb"][EF.HP_CURRENT]
    events, ws3 = end_rage("barb", ws2, next_event_id=2, timestamp=1.0)
    hp_after_end = ws3.entities["barb"][EF.HP_CURRENT]
    # HP should drop back (Greater Rage +6 CON → 3 HP/HD × 17 HD = 51)
    assert hp_after_end < hp_after_rage, "HP loss must still fire with Tireless Rage"
    assert ws3.entities["barb"][EF.FATIGUED] is False, "But no fatigue"
