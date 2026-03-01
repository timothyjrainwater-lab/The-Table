"""Gate tests for Whirlwind Attack (PHB p.102). WO-ENGINE-AI-WO1.
Gate IDs: WA-001 through WA-008.
"""

import pytest
from unittest import mock
from aidm.core.attack_resolver import resolve_whirlwind_attack
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


def _make_ws(attacker_feats=None, n_targets=2, target_ids=None):
    """Build minimal WorldState for whirlwind attack tests."""
    attacker = {
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 10,
        EF.ATTACK_BONUS: 5,
        EF.FEATS: attacker_feats or ["whirlwind_attack"],
        EF.TEAM: "players",
        EF.STR_MOD: 2,
        EF.CONDITIONS: {},
        EF.DEFEATED: False,
    }
    entities = {"attacker": attacker}
    ids = target_ids or [f"target_{i}" for i in range(n_targets)]
    for tid in ids:
        entities[tid] = {
            EF.HP_CURRENT: 20,
            EF.HP_MAX: 20,
            EF.AC: 10,
            EF.TEAM: "monsters",
            EF.CONDITIONS: {},
            EF.DEFEATED: False,
        }
    return WorldState(ruleset_version="3.5", entities=entities, active_combat=None)


def _make_intent(attacker_id="attacker", target_ids=None, weapon=None):
    """Build a WhirlwindAttackIntent-like object."""
    class _FakeIntent:
        pass

    intent = _FakeIntent()
    intent.attacker_id = attacker_id
    intent.target_ids = target_ids if target_ids is not None else ["target_0", "target_1"]
    intent.weapon = weapon or {
        "damage_dice": "1d8",
        "damage_bonus": 0,
        "damage_type": "slashing",
        "critical_multiplier": 2,
        "critical_range": 20,
        "is_two_handed": False,
        "grip": "one-handed",
        "weapon_type": "one-handed",
        "range_increment": 0,
    }
    return intent


def _rng(rolls=None):
    """Mock RNG that returns specified roll sequence."""
    stream = mock.MagicMock()
    if rolls is None:
        rolls = [15, 4] * 20
    stream.randint.side_effect = rolls
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# --- WA-001: feat present, 2 targets → 2 attack_roll events ---

def test_wa_001_two_targets_two_rolls():
    """WA-001: whirlwind with 2 targets emits exactly 2 attack_roll events."""
    ws = _make_ws()
    intent = _make_intent(target_ids=["target_0", "target_1"])
    events = resolve_whirlwind_attack(intent, ws, _rng(), 0, 0.0)
    rolls = [e for e in events if e.event_type == "attack_roll"]
    assert len(rolls) == 2, f"Expected 2 attack rolls, got {len(rolls)}"


# --- WA-002: each target gets exactly 1 attack roll ---

def test_wa_002_each_target_one_roll():
    """WA-002: each target in target_ids gets exactly one attack_roll."""
    ws = _make_ws(n_targets=3)
    intent = _make_intent(target_ids=["target_0", "target_1", "target_2"])
    events = resolve_whirlwind_attack(intent, ws, _rng([15, 4] * 15), 0, 0.0)
    rolls = [e for e in events if e.event_type == "attack_roll"]
    target_ids_found = [e.payload["target_id"] for e in rolls]
    assert "target_0" in target_ids_found
    assert "target_1" in target_ids_found
    assert "target_2" in target_ids_found


# --- WA-003: len(attack_roll events) == len(target_ids) ---

def test_wa_003_event_count_equals_target_count():
    """WA-003: number of attack_roll events equals number of target_ids."""
    for n in [1, 2, 4]:
        ws = _make_ws(n_targets=n)
        ids = [f"target_{i}" for i in range(n)]
        intent = _make_intent(target_ids=ids)
        events = resolve_whirlwind_attack(intent, ws, _rng([15, 4] * 20), 0, 0.0)
        rolls = [e for e in events if e.event_type == "attack_roll"]
        assert len(rolls) == n, f"Expected {n} rolls, got {len(rolls)}"


# --- WA-004: attacks use full attack bonus (no iterative penalty) ---

def test_wa_004_full_attack_bonus_no_penalty():
    """WA-004: each attack_roll uses full attack bonus (EF.ATTACK_BONUS, no iterative penalty)."""
    ws = _make_ws()
    ws.entities["attacker"][EF.ATTACK_BONUS] = 8
    intent = _make_intent(target_ids=["target_0", "target_1"])
    events = resolve_whirlwind_attack(intent, ws, _rng(), 0, 0.0)
    rolls = [e for e in events if e.event_type == "attack_roll"]
    for roll in rolls:
        assert roll.payload.get("attack_bonus") == 8, (
            f"Expected attack_bonus 8, got {roll.payload.get('attack_bonus')}"
        )


# --- WA-005: action type is full_round ---

def test_wa_005_action_type_full_round():
    """WA-005: WhirlwindAttackIntent maps to 'full_round' in action_economy."""
    from aidm.core.action_economy import get_action_type
    from aidm.schemas.intents import WhirlwindAttackIntent
    intent = WhirlwindAttackIntent(
        attacker_id="attacker",
        target_ids=["target_0"],
        weapon={},
    )
    assert get_action_type(intent) == "full_round"


# --- WA-006: no full_attack_start event emitted ---

def test_wa_006_no_full_attack_start_event():
    """WA-006: resolve_whirlwind_attack does NOT emit full_attack_start event."""
    ws = _make_ws()
    intent = _make_intent()
    events = resolve_whirlwind_attack(intent, ws, _rng(), 0, 0.0)
    fa_events = [e for e in events if e.event_type == "full_attack_start"]
    assert fa_events == [], "No full_attack_start should be emitted"


# --- WA-007: feat absent → whirlwind_attack_invalid ---

def test_wa_007_feat_absent_invalid():
    """WA-007: attacker lacking whirlwind_attack feat → whirlwind_attack_invalid event."""
    ws = _make_ws(attacker_feats=["power_attack"])
    intent = _make_intent()
    events = resolve_whirlwind_attack(intent, ws, _rng(), 0, 0.0)
    assert len(events) == 1
    assert events[0].event_type == "whirlwind_attack_invalid"
    assert events[0].payload["reason"] == "feat_not_present"


# --- WA-008: empty target_ids → whirlwind_attack_invalid (no_valid_targets) ---

def test_wa_008_empty_targets_invalid():
    """WA-008: empty target_ids → whirlwind_attack_invalid with reason no_valid_targets."""
    ws = _make_ws()
    intent = _make_intent(target_ids=[])
    events = resolve_whirlwind_attack(intent, ws, _rng(), 0, 0.0)
    assert len(events) == 1
    assert events[0].event_type == "whirlwind_attack_invalid"
    assert events[0].payload["reason"] == "no_valid_targets"
