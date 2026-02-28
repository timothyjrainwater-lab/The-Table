"""Gate tests: WO-ENGINE-MONK-FAST-MOVEMENT-001

Monk Fast Movement (PHB p.41, Table 3-13):
L3: +10, L6: +20, L9: +30, L12: +40, L15: +50, L18: +60.
Blocked by ANY armor or medium/heavy load (stricter than barbarian).

MFM-001 – MFM-008 (8 tests)
"""
import pytest

from aidm.core.movement_resolver import build_full_move_intent
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ent(eid, class_levels, armor_type="none", base_speed=30,
         fast_movement=0, enc_load="light"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "player",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.DEFEATED: False,
        EF.AC: 10,
        EF.CLASS_LEVELS: class_levels,
        EF.BASE_SPEED: base_speed,
        EF.FAST_MOVEMENT_BONUS: fast_movement,
        EF.ARMOR_TYPE: armor_type,
        EF.ARMOR_AC_BONUS: 0,
        EF.ENCUMBRANCE_LOAD: enc_load,
        EF.CONDITIONS: [],
        EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0},
    }


def _ws(entity):
    return WorldState(
        ruleset_version="3.5",
        entities={entity[EF.ENTITY_ID]: entity},
        active_combat=None,
    )


# ---------------------------------------------------------------------------
# MFM-001: Monk L3 unarmored, light load → base + 10 = 40ft (8 squares)
# ---------------------------------------------------------------------------

def test_mfm_001_monk_l3_speed_bonus():
    """MFM-001: Monk L3 unarmored, light load: speed = 30 + 10 = 40ft."""
    ent = _ent("m", {"monk": 3}, armor_type="none", enc_load="light")
    # 8 squares = 40ft should succeed
    intent, msg = build_full_move_intent("m", Position(x=8, y=0), _ws(ent))
    assert intent is not None, f"40ft move should succeed: {msg}"
    # 9 squares = 45ft should fail
    intent2, msg2 = build_full_move_intent("m", Position(x=9, y=0), _ws(ent))
    assert intent2 is None, "45ft should fail with 40ft speed"


# ---------------------------------------------------------------------------
# MFM-002: Monk L9 unarmored, light load → base + 30 = 60ft (12 squares)
# ---------------------------------------------------------------------------

def test_mfm_002_monk_l9_speed_bonus():
    """MFM-002: Monk L9 unarmored, light load: speed = 30 + 30 = 60ft."""
    ent = _ent("m", {"monk": 9}, armor_type="none", enc_load="light")
    intent, msg = build_full_move_intent("m", Position(x=12, y=0), _ws(ent))
    assert intent is not None, f"60ft move should succeed: {msg}"
    intent2, msg2 = build_full_move_intent("m", Position(x=13, y=0), _ws(ent))
    assert intent2 is None, "65ft should fail with 60ft speed"


# ---------------------------------------------------------------------------
# MFM-003: Monk L18 unarmored, light load → base + 60 = 90ft (18 squares)
# ---------------------------------------------------------------------------

def test_mfm_003_monk_l18_speed_bonus():
    """MFM-003: Monk L18 unarmored, light load: speed = 30 + 60 = 90ft."""
    ent = _ent("m", {"monk": 18}, armor_type="none", enc_load="light")
    intent, msg = build_full_move_intent("m", Position(x=18, y=0), _ws(ent))
    assert intent is not None, f"90ft move should succeed: {msg}"
    intent2, msg2 = build_full_move_intent("m", Position(x=19, y=0), _ws(ent))
    assert intent2 is None, "95ft should fail with 90ft speed"


# ---------------------------------------------------------------------------
# MFM-004: Monk L3 in light armor → no monk speed bonus (30ft only)
# ---------------------------------------------------------------------------

def test_mfm_004_monk_l3_light_armor_no_bonus():
    """MFM-004: Monk L3 in light armor — monk speed bonus blocked."""
    ent = _ent("m", {"monk": 3}, armor_type="light", enc_load="light")
    # 6 squares = 30ft should succeed (base speed only)
    intent, msg = build_full_move_intent("m", Position(x=6, y=0), _ws(ent))
    assert intent is not None, f"30ft should succeed: {msg}"
    # 7 squares = 35ft should fail (no monk bonus with armor)
    intent2, msg2 = build_full_move_intent("m", Position(x=7, y=0), _ws(ent))
    assert intent2 is None, "35ft should fail (light armor blocks monk speed bonus)"


# ---------------------------------------------------------------------------
# MFM-005: Monk L3 unarmored, medium load → no monk speed bonus
# ---------------------------------------------------------------------------

def test_mfm_005_monk_l3_medium_load_no_bonus():
    """MFM-005: Monk L3 unarmored, medium load — monk speed bonus blocked."""
    ent = _ent("m", {"monk": 3}, armor_type="none", enc_load="medium")
    intent, msg = build_full_move_intent("m", Position(x=6, y=0), _ws(ent))
    assert intent is not None, f"30ft should succeed: {msg}"
    intent2, msg2 = build_full_move_intent("m", Position(x=7, y=0), _ws(ent))
    assert intent2 is None, "35ft should fail (medium load blocks monk speed bonus)"


# ---------------------------------------------------------------------------
# MFM-006: Monk L2 unarmored, light load → no bonus (level too low)
# ---------------------------------------------------------------------------

def test_mfm_006_monk_l2_no_bonus():
    """MFM-006: Monk L2 — Fast Movement not yet available."""
    ent = _ent("m", {"monk": 2}, armor_type="none", enc_load="light")
    intent, msg = build_full_move_intent("m", Position(x=6, y=0), _ws(ent))
    assert intent is not None, f"30ft should succeed: {msg}"
    intent2, msg2 = build_full_move_intent("m", Position(x=7, y=0), _ws(ent))
    assert intent2 is None, "35ft should fail (monk L2, no fast movement yet)"


# ---------------------------------------------------------------------------
# MFM-007: Barbarian 4 / Monk 6 unarmored, light load → both stack
# ---------------------------------------------------------------------------

def test_mfm_007_multiclass_both_stack():
    """MFM-007: Barb4/Monk6 unarmored: barb +10 + monk +20 = +30 total (60ft)."""
    ent = _ent("bm", {"barbarian": 4, "monk": 6}, armor_type="none",
               fast_movement=10, enc_load="light")
    # 30 base + 10 barb + 20 monk = 60ft (12 squares)
    intent, msg = build_full_move_intent("bm", Position(x=12, y=0), _ws(ent))
    assert intent is not None, f"60ft move should succeed (barb+monk stacking): {msg}"
    intent2, msg2 = build_full_move_intent("bm", Position(x=13, y=0), _ws(ent))
    assert intent2 is None, "65ft should fail with 60ft speed"


# ---------------------------------------------------------------------------
# MFM-008: Barbarian 4 / Monk 6 in medium armor → barbarian only
# ---------------------------------------------------------------------------

def test_mfm_008_multiclass_medium_armor_barb_only():
    """MFM-008: Barb4/Monk6 medium armor: barb +10 only (monk blocked), total 40ft."""
    ent = _ent("bm", {"barbarian": 4, "monk": 6}, armor_type="medium",
               fast_movement=10, enc_load="light")
    # 30 base + 10 barb = 40ft (8 squares) — monk blocked by medium armor
    intent, msg = build_full_move_intent("bm", Position(x=8, y=0), _ws(ent))
    assert intent is not None, f"40ft should succeed (barb only, monk blocked): {msg}"
    intent2, msg2 = build_full_move_intent("bm", Position(x=9, y=0), _ws(ent))
    assert intent2 is None, "45ft should fail (monk speed blocked by medium armor)"
