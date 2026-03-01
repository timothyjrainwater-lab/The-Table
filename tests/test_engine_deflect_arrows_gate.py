"""Gate tests for Deflect Arrows (PHB p.93). WO-ENGINE-AI-WO3.
Gate IDs: DA-001 through DA-008.

Tests call resolve_attack() directly and inspect for deflect_arrows event.
"""

import pytest
from unittest import mock
from aidm.core.attack_resolver import resolve_attack
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


def _ranged_weapon():
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="piercing",
        critical_multiplier=2,
        critical_range=20,
        is_two_handed=False,
        grip="one-handed",
        weapon_type="ranged",
        range_increment=60,
    )


def _melee_weapon():
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="slashing",
        critical_multiplier=2,
        critical_range=20,
        is_two_handed=False,
        grip="one-handed",
        weapon_type="one-handed",
        range_increment=0,
    )


def _make_ws(
    target_feats=None,
    target_conditions=None,
    free_hands=1,
    deflect_arrows_used=None,
):
    """Build WorldState for deflect arrows tests."""
    attacker = {
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 10,
        EF.ATTACK_BONUS: 20,  # High enough to always hit AC 10 (roll ≥ 2)
        EF.FEATS: [],
        EF.TEAM: "monsters",
        EF.STR_MOD: 2,
        EF.CONDITIONS: {},
        EF.DEFEATED: False,
    }
    target = {
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 10,
        EF.FEATS: target_feats if target_feats is not None else ["deflect_arrows"],
        EF.CONDITIONS: target_conditions if target_conditions is not None else {},
        EF.FREE_HANDS: free_hands,
        EF.TEAM: "players",
        EF.DEFEATED: False,
    }
    active_combat = {
        "initiative_order": ["attacker", "target"],
        "aoo_used_this_round": [],
        "aoo_count_this_round": {},
        "grapple_pairs": [],
        "deflect_arrows_used": deflect_arrows_used if deflect_arrows_used is not None else [],
    }
    return WorldState(
        ruleset_version="3.5",
        entities={"attacker": attacker, "target": target},
        active_combat=active_combat,
    )


def _rng(d20_roll=15, dmg_roll=4):
    """Mock RNG returning specified d20 then damage roll."""
    stream = mock.MagicMock()
    stream.randint.side_effect = [d20_roll, d20_roll, dmg_roll] + [dmg_roll] * 10
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _make_attack(attack_bonus=20, weapon=None):
    return AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=attack_bonus,
        weapon=weapon or _ranged_weapon(),
    )


# --- DA-001: hit + ranged + feat + free hand + not flat-footed → deflect_arrows event, no damage ---

def test_da_001_deflect_fires_on_ranged_hit():
    """DA-001: valid deflect conditions → deflect_arrows event emitted, no damage_roll."""
    ws = _make_ws()
    intent = _make_attack()
    events = resolve_attack(intent, ws, _rng(d20_roll=15), 0, 0.0)
    da_events = [e for e in events if e.event_type == "deflect_arrows"]
    dmg_events = [e for e in events if e.event_type == "damage_roll"]
    assert len(da_events) == 1, f"Expected 1 deflect_arrows event, got {len(da_events)}"
    assert len(dmg_events) == 0, "No damage_roll should follow deflect_arrows"


# --- DA-002: feat absent → no DA, damage proceeds normally on hit ---

def test_da_002_feat_absent_no_deflect():
    """DA-002: target lacks deflect_arrows feat → no DA event."""
    ws = _make_ws(target_feats=[])
    intent = _make_attack()
    events = resolve_attack(intent, ws, _rng(d20_roll=15), 0, 0.0)
    da_events = [e for e in events if e.event_type == "deflect_arrows"]
    assert da_events == [], "No deflect_arrows event when feat absent"


# --- DA-003: melee weapon → no DA (ranged only) ---

def test_da_003_melee_weapon_no_deflect():
    """DA-003: melee weapon → deflect_arrows does not fire (PHB p.93: ranged attacks only)."""
    ws = _make_ws()
    intent = _make_attack(weapon=_melee_weapon())
    events = resolve_attack(intent, ws, _rng(d20_roll=15), 0, 0.0)
    da_events = [e for e in events if e.event_type == "deflect_arrows"]
    assert da_events == [], "No deflect_arrows for melee weapon"


# --- DA-004: flat-footed target → no DA ---

def test_da_004_flat_footed_no_deflect():
    """DA-004: flat-footed target → deflect_arrows does not fire (PHB: not flat-footed)."""
    ws = _make_ws(target_conditions={"flat_footed": {"condition_type": "flat_footed"}})
    intent = _make_attack()
    events = resolve_attack(intent, ws, _rng(d20_roll=15), 0, 0.0)
    da_events = [e for e in events if e.event_type == "deflect_arrows"]
    assert da_events == [], "No deflect_arrows when target is flat-footed"


# --- DA-005: second ranged attack same round → no DA (already used) ---

def test_da_005_already_used_this_round():
    """DA-005: target already in deflect_arrows_used list → no DA (once per round)."""
    ws = _make_ws(deflect_arrows_used=["target"])
    intent = _make_attack()
    events = resolve_attack(intent, ws, _rng(d20_roll=15), 0, 0.0)
    da_events = [e for e in events if e.event_type == "deflect_arrows"]
    assert da_events == [], "No deflect_arrows when already used this round"


# --- DA-006: no free hand → no DA ---

def test_da_006_no_free_hand():
    """DA-006: free_hands=0 → deflect_arrows does not fire (PHB: at least one hand free)."""
    ws = _make_ws(free_hands=0)
    intent = _make_attack()
    events = resolve_attack(intent, ws, _rng(d20_roll=15), 0, 0.0)
    da_events = [e for e in events if e.event_type == "deflect_arrows"]
    assert da_events == [], "No deflect_arrows when free_hands=0"


# --- DA-007: miss → no DA (feat irrelevant on miss) ---

def test_da_007_miss_no_deflect():
    """DA-007: attack misses → no deflect_arrows event (DA only matters on hit)."""
    ws = _make_ws()
    # Natural 1 always misses in D&D 3.5
    intent = _make_attack(attack_bonus=-20)
    events = resolve_attack(intent, ws, _rng(d20_roll=1), 0, 0.0)
    da_events = [e for e in events if e.event_type == "deflect_arrows"]
    assert da_events == [], "No deflect_arrows on miss"


# --- DA-008: EF.FREE_HANDS defaults to 1 when field absent ---

def test_da_008_free_hands_default_1():
    """DA-008: entity without EF.FREE_HANDS field → defaults to 1 → DA fires normally."""
    ws = _make_ws(free_hands=1)
    # Remove free_hands field entirely to test default
    del ws.entities["target"][EF.FREE_HANDS]
    intent = _make_attack()
    events = resolve_attack(intent, ws, _rng(d20_roll=15), 0, 0.0)
    da_events = [e for e in events if e.event_type == "deflect_arrows"]
    assert len(da_events) == 1, "DA should fire when EF.FREE_HANDS is absent (defaults to 1)"
