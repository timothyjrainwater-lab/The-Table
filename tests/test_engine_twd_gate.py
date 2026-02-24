"""Gate ENGINE-TWD — WO-ENGINE-TWD-001

Tests:
TWD-01: Defender with TWD feat + off-hand weapon: effective AC is +1 higher
TWD-02: Defender with Improved TWD: effective AC is +2 higher
TWD-03: Defender with Greater TWD: effective AC is +3 higher
TWD-04: Defender with TWD but no off-hand weapon: bonus is 0
TWD-05: Defender with TWD + off-hand but HELPLESS condition: bonus is 0
TWD-06: Defender with TWD + off-hand but PINNED: bonus is 0
TWD-07: attack_roll event payload contains twd_ac_bonus field (0 when not active)
TWD-08: attack_roll event payload contains twd_ac_bonus field (correct value when active)
"""

import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.core.state import WorldState
from aidm.core.attack_resolver import resolve_attack
from aidm.core.full_attack_resolver import _compute_twd_ac_bonus, _has_off_hand_weapon
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import ConditionType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _weapon() -> Weapon:
    return Weapon(
        damage_dice="1d6",
        damage_bonus=0,
        damage_type="slashing",
        critical_range=20,
        critical_multiplier=2,
        is_two_handed=False,
        grip="one-handed",
        weapon_type="one-handed",
        range_increment=0,
    )


def _entity(eid: str, team: str, hp: int = 30, ac: int = 10,
            feats: list = None, conditions: dict = None,
            off_hand: bool = False, pos: dict = None) -> Dict[str, Any]:
    e = {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.ATTACK_BONUS: 5,
        EF.BAB: 5,
        EF.STR_MOD: 2,
        EF.DEX_MOD: 1,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: conditions or {},
        EF.FEATS: feats or [],
        EF.POSITION: pos or {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.TEMPORARY_MODIFIERS: {},
        EF.WEAPON: {
            "damage_dice": "1d6",
            "damage_bonus": 0,
            "damage_type": "slashing",
            "critical_range": 20,
            "critical_multiplier": 2,
            "is_two_handed": False,
            "grip": "one-handed",
            "weapon_type": "one-handed",
            "range_increment": 0,
        },
    }
    if off_hand:
        e["off_hand_weapon"] = {
            "damage_dice": "1d4",
            "damage_bonus": 0,
            "damage_type": "slashing",
            "is_light": True,
        }
    return e


def _world(attacker: dict, defender: dict) -> WorldState:
    entities = {attacker[EF.ENTITY_ID]: attacker, defender[EF.ENTITY_ID]: defender}
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": [attacker[EF.ENTITY_ID], defender[EF.ENTITY_ID]],
            "aoo_used_this_round": [],
        },
    )


def _rng(rolls=(20, 5, 5)) -> mock.MagicMock:
    """RNG that returns predictable rolls."""
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [4] * 50
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _attack_roll_event(events):
    return next(e for e in events if e.event_type == "attack_roll")


# ---------------------------------------------------------------------------
# Unit tests on helpers
# ---------------------------------------------------------------------------

def test_twd_01_basic_twd_bonus():
    """TWD-01: Defender with TWD feat + off-hand weapon: bonus is +1."""
    defender = _entity("def", "enemy", feats=["Two-Weapon Defense"], off_hand=True)
    bonus = _compute_twd_ac_bonus(defender)
    assert bonus == 1


def test_twd_02_improved_twd_bonus():
    """TWD-02: Defender with Improved TWD: bonus is +2."""
    defender = _entity("def", "enemy",
                       feats=["Two-Weapon Defense", "Improved Two-Weapon Defense"],
                       off_hand=True)
    bonus = _compute_twd_ac_bonus(defender)
    assert bonus == 2


def test_twd_03_greater_twd_bonus():
    """TWD-03: Defender with Greater TWD: bonus is +3."""
    defender = _entity("def", "enemy",
                       feats=["Two-Weapon Defense", "Improved Two-Weapon Defense",
                              "Greater Two-Weapon Defense"],
                       off_hand=True)
    bonus = _compute_twd_ac_bonus(defender)
    assert bonus == 3


def test_twd_04_no_off_hand_weapon():
    """TWD-04: Defender with TWD but no off-hand weapon: bonus is 0."""
    defender = _entity("def", "enemy", feats=["Two-Weapon Defense"], off_hand=False)
    bonus = _compute_twd_ac_bonus(defender)
    assert bonus == 0


def test_twd_05_flat_footed_helpless():
    """TWD-05: Defender with TWD + off-hand but HELPLESS: bonus is 0."""
    defender = _entity("def", "enemy",
                       feats=["Two-Weapon Defense"],
                       off_hand=True,
                       conditions={ConditionType.HELPLESS.value: {}})
    bonus = _compute_twd_ac_bonus(defender)
    assert bonus == 0


def test_twd_06_flat_footed_pinned():
    """TWD-06: Defender with TWD + off-hand but PINNED: bonus is 0."""
    defender = _entity("def", "enemy",
                       feats=["Two-Weapon Defense"],
                       off_hand=True,
                       conditions={ConditionType.PINNED.value: {}})
    bonus = _compute_twd_ac_bonus(defender)
    assert bonus == 0


# ---------------------------------------------------------------------------
# Integration tests: resolve_attack event payload
# ---------------------------------------------------------------------------

def test_twd_07_event_payload_zero_when_inactive():
    """TWD-07: attack_roll event payload contains twd_ac_bonus field (0 when not active)."""
    attacker = _entity("atk", "party", pos={"x": 0, "y": 0})
    defender = _entity("def", "enemy", feats=[], off_hand=False, pos={"x": 1, "y": 0})

    ws = _world(attacker, defender)
    intent = AttackIntent(
        attacker_id="atk",
        target_id="def",
        attack_bonus=5,
        weapon=_weapon(),
    )

    events = resolve_attack(intent, ws, _rng(rolls=(15, 5, 4)), 0, 0.0)
    ev = _attack_roll_event(events)

    assert "twd_ac_bonus" in ev.payload
    assert ev.payload["twd_ac_bonus"] == 0


def test_twd_08_event_payload_correct_when_active():
    """TWD-08: attack_roll event payload contains twd_ac_bonus field (correct value when active)."""
    attacker = _entity("atk", "party", pos={"x": 0, "y": 0})
    defender = _entity("def", "enemy",
                       feats=["Two-Weapon Defense"],
                       off_hand=True,
                       pos={"x": 1, "y": 0})

    ws = _world(attacker, defender)
    intent = AttackIntent(
        attacker_id="atk",
        target_id="def",
        attack_bonus=5,
        weapon=_weapon(),
    )

    events = resolve_attack(intent, ws, _rng(rolls=(15, 5, 4)), 0, 0.0)
    ev = _attack_roll_event(events)

    assert "twd_ac_bonus" in ev.payload
    assert ev.payload["twd_ac_bonus"] == 1

    # Confirm the bonus actually inflated target_ac in the payload
    # target_ac should include base_ac + twd_bonus
    assert ev.payload["target_ac"] == defender[EF.AC] + 1  # base AC 10 + TWD +1
