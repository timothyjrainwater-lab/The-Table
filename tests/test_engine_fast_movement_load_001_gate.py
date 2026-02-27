"""Gate tests for WO-ENGINE-FAST-MOVEMENT-LOAD-FIX-001.

Verifies barbarian Fast Movement (+10 ft) is blocked only by heavy load,
NOT medium load (PHB p.25).

Authority: RAW — PHB p.25
"""

from aidm.core.movement_resolver import build_full_move_intent
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.core.state import WorldState


def _ent(entity_id, class_levels, armor_type="none", enc_load="light",
         base_speed=30, fast_movement=0):
    return {
        EF.ENTITY_ID: entity_id, EF.TEAM: "player",
        EF.HP_CURRENT: 20, EF.HP_MAX: 20, EF.DEFEATED: False, EF.AC: 10,
        EF.CLASS_LEVELS: class_levels,
        EF.BASE_SPEED: base_speed,
        EF.FAST_MOVEMENT_BONUS: fast_movement,
        EF.ARMOR_TYPE: armor_type,
        EF.ENCUMBRANCE_LOAD: enc_load,
        EF.ARMOR_AC_BONUS: 0,
        EF.CONDITIONS: [], EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0},
    }


def _ws(entity):
    return WorldState(
        ruleset_version="3.5",
        entities={entity[EF.ENTITY_ID]: entity},
        active_combat=None,
    )


# ---------- FMLF-001: Barbarian + no armor + light load → +10 ----------
def test_fmlf_001_no_armor_light_load():
    ent = _ent("b", {"barbarian": 1}, armor_type="none", enc_load="light",
               base_speed=30, fast_movement=10)
    intent, msg = build_full_move_intent("b", Position(x=8, y=0), _ws(ent))
    assert intent is not None, "40ft should succeed (no armor, light load): %s" % msg


# ---------- FMLF-002: Barbarian + light armor + light load → +10 ----------
def test_fmlf_002_light_armor_light_load():
    ent = _ent("b", {"barbarian": 1}, armor_type="light", enc_load="light",
               base_speed=30, fast_movement=10)
    intent, msg = build_full_move_intent("b", Position(x=8, y=0), _ws(ent))
    assert intent is not None, "40ft should succeed (light armor, light load): %s" % msg


# ---------- FMLF-003: Barbarian + medium armor + light load → +10 ----------
def test_fmlf_003_medium_armor_light_load():
    ent = _ent("b", {"barbarian": 1}, armor_type="medium", enc_load="light",
               base_speed=30, fast_movement=10)
    intent, msg = build_full_move_intent("b", Position(x=8, y=0), _ws(ent))
    assert intent is not None, "40ft should succeed (medium armor, light load): %s" % msg


# ---------- FMLF-004: Barbarian + heavy armor → no +10 ----------
def test_fmlf_004_heavy_armor_blocks():
    ent = _ent("b", {"barbarian": 1}, armor_type="heavy", enc_load="light",
               base_speed=30, fast_movement=10)
    # 40ft move should fail (30ft base, heavy armor blocks +10)
    intent, msg = build_full_move_intent("b", Position(x=8, y=0), _ws(ent))
    assert intent is None, "40ft should FAIL (heavy armor blocks fast movement)"
    # 30ft move should succeed
    intent2, msg2 = build_full_move_intent("b", Position(x=6, y=0), _ws(ent))
    assert intent2 is not None, "30ft should succeed with heavy armor: %s" % msg2


# ---------- FMLF-005: Barbarian + no armor + MEDIUM load → +10 (KEY FIX) ----------
def test_fmlf_005_medium_load_allows():
    ent = _ent("b", {"barbarian": 1}, armor_type="none", enc_load="medium",
               base_speed=30, fast_movement=10)
    intent, msg = build_full_move_intent("b", Position(x=8, y=0), _ws(ent))
    assert intent is not None, "40ft should succeed (medium load does NOT block fast movement, PHB p.25): %s" % msg


# ---------- FMLF-006: Barbarian + no armor + heavy load → no +10 ----------
def test_fmlf_006_heavy_load_blocks():
    ent = _ent("b", {"barbarian": 1}, armor_type="none", enc_load="heavy",
               base_speed=30, fast_movement=10)
    # 40ft move should fail (heavy load blocks)
    intent, msg = build_full_move_intent("b", Position(x=8, y=0), _ws(ent))
    assert intent is None, "40ft should FAIL (heavy load blocks fast movement)"
    # 30ft should succeed
    intent2, msg2 = build_full_move_intent("b", Position(x=6, y=0), _ws(ent))
    assert intent2 is not None, "30ft should succeed with heavy load: %s" % msg2


# ---------- FMLF-007: Non-barbarian + no armor + light load → no fast movement ----------
def test_fmlf_007_non_barbarian():
    ent = _ent("f", {"fighter": 1}, armor_type="none", enc_load="light",
               base_speed=30, fast_movement=0)
    # 35ft move should fail (30ft base only)
    intent, msg = build_full_move_intent("f", Position(x=7, y=0), _ws(ent))
    assert intent is None, "35ft should FAIL for non-barbarian (no fast movement)"


# ---------- FMLF-008: Barbarian L1 → fast movement present (PHB p.25) ----------
def test_fmlf_008_barbarian_l1_has_fast_movement():
    from aidm.chargen.builder import build_character
    entity = build_character(
        race="human", class_name="barbarian", level=1,
        ability_overrides={"str": 14, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 8},
    )
    assert entity.get(EF.FAST_MOVEMENT_BONUS) == 10, "Barbarian L1 should have fast movement +10"
