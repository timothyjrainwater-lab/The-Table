"""Gate tests: WO-ENGINE-ENCUMBRANCE-WIRE-001 — Encumbrance integration.

PHB p.26: Barbarian Fast Movement suppressed by medium/heavy load.
PHB p.41: Monk WIS bonus to AC suppressed by medium/heavy load.

EF.ENCUMBRANCE_LOAD = "encumbrance_load" confirmed at entity_fields.py:133.
Load tier read directly from entity dict — no catalog required.

Gate label: ENGINE-ENCUMBRANCE-WIRE
Tests: EW-001 – EW-010
"""

import pytest
from aidm.core.attack_resolver import resolve_attack
from aidm.core.movement_resolver import build_full_move_intent
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.core.state import WorldState


class _FixedRNG:
    class _Stream:
        def randint(self, lo, hi): return 15
    def stream(self, name): return _FixedRNG._Stream()


def _weapon():
    return Weapon(damage_dice="1d6", damage_bonus=0, damage_type="slashing", weapon_type="one-handed")


def _attacker():
    return {
        EF.ENTITY_ID: "att", EF.TEAM: "enemy",
        EF.STR_MOD: 2, EF.DEX_MOD: 0, EF.WIS_MOD: 0,
        EF.FEATS: [], EF.ATTACK_BONUS: 20,
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 15, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: [],
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.FAVORED_ENEMIES: [], EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.COMBAT_EXPERTISE_BONUS: 0,
        EF.CLASS_LEVELS: {"fighter": 1},
        EF.MONK_WIS_AC_BONUS: 0,
        EF.ARMOR_AC_BONUS: 0,
        EF.ARMOR_TYPE: "none",
        EF.ENCUMBRANCE_LOAD: "light",
    }


def _monk_target(wis_mod=3, ac=10, load="light"):
    return {
        EF.ENTITY_ID: "tgt", EF.TEAM: "player",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: ac, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.WIS_MOD: wis_mod,
        EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.COMBAT_EXPERTISE_BONUS: 0,
        EF.CLASS_LEVELS: {"monk": 5},
        EF.MONK_WIS_AC_BONUS: wis_mod,
        EF.ARMOR_AC_BONUS: 0,
        EF.ARMOR_TYPE: "none",
        EF.ENCUMBRANCE_LOAD: load,
    }


def _get_target_ac(att, tgt):
    ws = WorldState(
        ruleset_version="3.5",
        entities={"att": att, "tgt": tgt},
        active_combat={
            "initiative_order": ["att", "tgt"],
            "aoo_used_this_round": [], "aoo_count_this_round": {},
        },
    )
    intent = AttackIntent(attacker_id="att", target_id="tgt", attack_bonus=20, weapon=_weapon())
    events = resolve_attack(intent=intent, world_state=ws, rng=_FixedRNG(), next_event_id=0, timestamp=0.0)
    for e in events:
        if e.event_type == "attack_roll":
            return e.payload["target_ac"]
    raise AssertionError("No attack_roll event found")


def _barb_entity(load="light", armor_type="none", base_speed=30):
    return {
        EF.ENTITY_ID: "b", EF.TEAM: "player",
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 14, EF.DEFEATED: False,
        EF.CLASS_LEVELS: {"barbarian": 1},
        EF.BASE_SPEED: base_speed,
        EF.FAST_MOVEMENT_BONUS: 10,
        EF.ARMOR_TYPE: armor_type,
        EF.ARMOR_AC_BONUS: 0,
        EF.CONDITIONS: [], EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.ENCUMBRANCE_LOAD: load,
    }


def _fighter_entity(load="light"):
    return {
        EF.ENTITY_ID: "f", EF.TEAM: "player",
        EF.HP_CURRENT: 20, EF.HP_MAX: 20, EF.AC: 10, EF.DEFEATED: False,
        EF.CLASS_LEVELS: {"fighter": 1},
        EF.BASE_SPEED: 30,
        EF.FAST_MOVEMENT_BONUS: 0,
        EF.ARMOR_TYPE: "none",
        EF.ARMOR_AC_BONUS: 0,
        EF.CONDITIONS: [], EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.ENCUMBRANCE_LOAD: load,
    }


def _ws_move(ent):
    return WorldState(
        ruleset_version="3.5",
        entities={ent[EF.ENTITY_ID]: ent},
        active_combat=None,
    )


# ---------------------------------------------------------------------------
# EW-001: Monk at light load retains WIS AC bonus
# ---------------------------------------------------------------------------
def test_ew001_monk_light_load_retains_wis_ac():
    # Monk level 5, WIS +3, light load → WIS AC bonus applied → AC = 10 + 3 = 13
    att = _attacker()
    tgt = _monk_target(wis_mod=3, ac=10, load="light")
    ac = _get_target_ac(att, tgt)
    assert ac == 13, f"Monk at light load: expected AC 13 (WIS +3 applied), got {ac}"


# ---------------------------------------------------------------------------
# EW-002: Monk at medium load loses WIS AC bonus
# ---------------------------------------------------------------------------
def test_ew002_monk_medium_load_loses_wis_ac():
    # Monk level 5, WIS +3, medium load → WIS AC bonus suppressed → AC = 10
    att = _attacker()
    tgt = _monk_target(wis_mod=3, ac=10, load="medium")
    ac = _get_target_ac(att, tgt)
    assert ac == 10, f"Monk at medium load: expected AC 10 (WIS suppressed by load), got {ac}"


# ---------------------------------------------------------------------------
# EW-003: Monk at heavy load loses WIS AC bonus
# ---------------------------------------------------------------------------
def test_ew003_monk_heavy_load_loses_wis_ac():
    att = _attacker()
    tgt = _monk_target(wis_mod=3, ac=10, load="heavy")
    ac = _get_target_ac(att, tgt)
    assert ac == 10, f"Monk at heavy load: expected AC 10 (WIS suppressed), got {ac}"


# ---------------------------------------------------------------------------
# EW-004: Non-monk unaffected by load check (no WIS AC bonus field, no error)
# ---------------------------------------------------------------------------
def test_ew004_nonmonk_unaffected_by_load():
    att = _attacker()
    tgt = {
        EF.ENTITY_ID: "tgt", EF.TEAM: "player",
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 15, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.STR_MOD: 0, EF.DEX_MOD: 2, EF.WIS_MOD: 3,
        EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.COMBAT_EXPERTISE_BONUS: 0,
        EF.CLASS_LEVELS: {"fighter": 5},  # not monk
        EF.MONK_WIS_AC_BONUS: 0,
        EF.ARMOR_AC_BONUS: 0,
        EF.ARMOR_TYPE: "none",
        EF.ENCUMBRANCE_LOAD: "heavy",  # heavy load, but not a monk
    }
    # Should not raise; AC should be 15 (the base_ac — no monk bonus possible)
    ac = _get_target_ac(att, tgt)
    assert ac == 15, f"Non-monk should not get WIS AC; expected 15, got {ac}"


# ---------------------------------------------------------------------------
# EW-005: Barbarian at light load retains fast movement
# ---------------------------------------------------------------------------
def test_ew005_barbarian_light_load_retains_fast_movement():
    # 30 + 10 = 40 ft → 8 squares should succeed
    ent = _barb_entity(load="light", armor_type="none")
    intent, msg = build_full_move_intent("b", Position(x=8, y=0), _ws_move(ent))
    assert intent is not None, f"Barbarian at light load: 40ft move should succeed. msg={msg}"


# ---------------------------------------------------------------------------
# EW-006: Barbarian at medium load loses fast movement
# ---------------------------------------------------------------------------
def test_ew006_barbarian_medium_load_loses_fast_movement():
    # Speed = 30 ft (no fast movement bonus)
    ent = _barb_entity(load="medium", armor_type="none")
    # 8 squares = 40ft — should fail with 30ft speed
    intent8, _ = build_full_move_intent("b", Position(x=8, y=0), _ws_move(ent))
    assert intent8 is None, "Barbarian at medium load: 40ft move should fail (speed=30)"
    # 6 squares = 30ft — should succeed
    intent6, msg = build_full_move_intent("b", Position(x=6, y=0), _ws_move(ent))
    assert intent6 is not None, f"Barbarian at medium load: 30ft move should succeed. msg={msg}"


# ---------------------------------------------------------------------------
# EW-007: Barbarian at heavy load loses fast movement
# ---------------------------------------------------------------------------
def test_ew007_barbarian_heavy_load_loses_fast_movement():
    ent = _barb_entity(load="heavy", armor_type="none")
    intent8, _ = build_full_move_intent("b", Position(x=8, y=0), _ws_move(ent))
    assert intent8 is None, "Barbarian at heavy load: 40ft move should fail (speed=30)"
    intent6, msg = build_full_move_intent("b", Position(x=6, y=0), _ws_move(ent))
    assert intent6 is not None, f"Barbarian at heavy load: 30ft move should succeed. msg={msg}"


# ---------------------------------------------------------------------------
# EW-008: Barbarian in light armor at light load retains fast movement
# ---------------------------------------------------------------------------
def test_ew008_barbarian_light_armor_light_load_retains_fast_movement():
    ent = _barb_entity(load="light", armor_type="light")
    intent, msg = build_full_move_intent("b", Position(x=8, y=0), _ws_move(ent))
    assert intent is not None, f"Barbarian light armor + light load: 40ft should succeed. msg={msg}"


# ---------------------------------------------------------------------------
# EW-009: Barbarian in heavy armor loses fast movement regardless of load
# PHB p.26: heavy armor blocks fast movement; medium armor does NOT (PHB p.26 explicit).
# ---------------------------------------------------------------------------
def test_ew009_barbarian_heavy_armor_blocks_fast_movement():
    # Heavy armor blocks fast movement regardless of load tier (pre-existing behavior)
    ent = _barb_entity(load="light", armor_type="heavy")
    intent8, _ = build_full_move_intent("b", Position(x=8, y=0), _ws_move(ent))
    assert intent8 is None, "Barbarian in heavy armor: 40ft should fail regardless of light load"
    intent6, msg = build_full_move_intent("b", Position(x=6, y=0), _ws_move(ent))
    assert intent6 is not None, f"Barbarian in heavy armor: 30ft should succeed. msg={msg}"


# ---------------------------------------------------------------------------
# EW-010: Regression — non-barbarian movement unaffected by load field
# ---------------------------------------------------------------------------
def test_ew010_fighter_heavy_load_normal_speed():
    # Fighter has no fast movement bonus; heavy load doesn't change base speed
    ent = _fighter_entity(load="heavy")
    # 6 squares = 30ft should succeed (base speed 30)
    intent6, msg = build_full_move_intent("f", Position(x=6, y=0), _ws_move(ent))
    assert intent6 is not None, f"Fighter at heavy load: 30ft should succeed. msg={msg}"
    # 7 squares = 35ft should fail
    intent7, _ = build_full_move_intent("f", Position(x=7, y=0), _ws_move(ent))
    assert intent7 is None, "Fighter at heavy load: 35ft should fail (base speed 30)"
