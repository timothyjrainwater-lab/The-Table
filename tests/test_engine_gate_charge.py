"""Gate ENGINE-CHARGE — WO-ENGINE-CHARGE-001: Charge Action Wire.

Tests:
CH-01: Charge attack applies +2 attack bonus
CH-02: Charge applies -2 AC penalty to charger
CH-03: charge_attack event emitted before attack roll events
CH-04: Charge is full-round action — denied if standard already used
CH-05: path_clear=False emits intent_validation_failed
CH-06: Spirited Charge + mounted → damage ×2
CH-07: Spirited Charge + mounted + lance → damage ×3
CH-08: Spirited Charge feat present but no mount → normal damage
CH-09: Charge AC penalty clears at start of charger's next turn
CH-10: Charge against DEFEATED target → intent_validation_failed
"""

import unittest.mock as mock
from typing import Any, Dict, List

import pytest

from aidm.core.attack_resolver import resolve_charge, apply_charge_events
from aidm.core.play_loop import TurnContext, execute_turn
from aidm.core.action_economy import ActionBudget
from aidm.core.state import WorldState
from aidm.schemas.intents import ChargeIntent, parse_intent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WEAPON_LONGSWORD = {
    "damage_dice": "1d8",
    "damage_bonus": 0,
    "critical_range": 19,
    "critical_multiplier": 2,
    "grip": "one-handed",
    "damage_type": "slashing",
    "weapon_type": "one-handed",
    "range_increment": 0,
    "is_two_handed": False,
}

WEAPON_LANCE = {
    "damage_dice": "1d8",
    "damage_bonus": 0,
    "critical_range": 20,
    "critical_multiplier": 3,
    "grip": "one-handed",
    "damage_type": "piercing",
    "weapon_type": "one-handed",  # mapped from "lance" game type
    "range_increment": 0,
    "is_two_handed": False,
    "lance": True,  # extra key — ignored by Weapon(**) via filtered call
}

WEAPON_LANCE_TYPE = {
    "damage_dice": "1d8",
    "damage_bonus": 0,
    "critical_range": 20,
    "critical_multiplier": 3,
    "grip": "one-handed",
    "damage_type": "piercing",
    "weapon_type": "one-handed",
    "range_increment": 0,
    "is_two_handed": False,
    "weapon_game_type": "lance",  # extra key, ignored by Weapon
}


def _weapon_lance_with_type() -> dict:
    """Weapon dict that has weapon_type='one-handed' but game_type='lance' for Spirited Charge ×3."""
    return {
        "damage_dice": "1d8",
        "damage_bonus": 0,
        "critical_range": 20,
        "critical_multiplier": 3,
        "grip": "one-handed",
        "damage_type": "piercing",
        "weapon_type": "lance",   # triggers ×3 in Spirited Charge check
        "range_increment": 0,
        "is_two_handed": False,
    }


def _entity(
    eid: str,
    team: str,
    hp: int = 30,
    hp_max: int = 30,
    ac: int = 10,
    attack_bonus: int = 5,
    defeated: bool = False,
    dying: bool = False,
    feats: list = None,
    mounted_state=None,
    temporary_modifiers: dict = None,
    pos: dict = None,
    str_mod: int = 2,
) -> Dict[str, Any]:
    e = {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: ac,
        EF.ATTACK_BONUS: attack_bonus,
        EF.BAB: attack_bonus,
        "bab": attack_bonus,
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 0,
        EF.DEFEATED: defeated,
        EF.DYING: dying,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats if feats is not None else [],
        EF.POSITION: pos if pos is not None else {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
    }
    if mounted_state is not None:
        e[EF.MOUNTED_STATE] = mounted_state
    if temporary_modifiers is not None:
        e[EF.TEMPORARY_MODIFIERS] = temporary_modifiers
    return e


def _world(attacker: dict, target: dict, action_budget: dict = None, budget_actor: str = None) -> WorldState:
    combat = {"initiative_order": ["attacker", "target"]}
    if action_budget is not None:
        combat["action_budget"] = action_budget
        combat["action_budget_actor"] = budget_actor or "attacker"
    return WorldState(
        ruleset_version="3.5e",
        entities={"attacker": attacker, "target": target},
        active_combat=combat,
    )


def _ctx(actor_id: str = "attacker", team: str = "party") -> TurnContext:
    return TurnContext(turn_index=0, actor_id=actor_id, actor_team=team)


def _rng(attack_roll: int = 15, damage_roll: int = 5) -> mock.MagicMock:
    """RNG: combat stream returns attack_roll then damage_roll (and repeats)."""
    stream = mock.MagicMock()
    stream.randint.side_effect = [attack_roll, damage_roll] + [damage_roll] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# CH-01: Charge attack applies +2 attack bonus
# ---------------------------------------------------------------------------

def test_ch01_charge_applies_plus2_attack_bonus():
    """charge_attack event has attack_bonus_applied==2; attack_roll bonus matches base+2."""
    attacker = _entity("attacker", "party", attack_bonus=4)
    target = _entity("target", "monsters", ac=10)
    ws = _world(attacker, target)

    intent = ChargeIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=WEAPON_LONGSWORD,
        path_clear=True,
    )
    rng = _rng(attack_roll=10, damage_roll=4)
    events = resolve_charge(intent, ws, rng, next_event_id=0, timestamp=0.0)

    # charge_attack event present with attack_bonus_applied == 2
    ca_events = [e for e in events if e.event_type == "charge_attack"]
    assert len(ca_events) == 1, "charge_attack event must be emitted"
    assert ca_events[0].payload["attack_bonus_applied"] == 2

    # attack_roll event present; roll + (base+2) compared to AC
    atk_events = [e for e in events if e.event_type == "attack_roll"]
    assert len(atk_events) >= 1
    atk = atk_events[0]
    # With attack_bonus=4 + 2 charge = 6, roll=10 -> total=16 vs AC=10 -> hit
    # Verify the recorded attack_bonus in event matches expected value
    assert atk.payload.get("attack_bonus") == 6


# ---------------------------------------------------------------------------
# CH-02: Charge applies -2 AC penalty to charger
# ---------------------------------------------------------------------------

def test_ch02_charge_ac_penalty_written():
    """After apply_charge_events(), charger has EF.TEMPORARY_MODIFIERS['charge_ac'] == -2."""
    attacker = _entity("attacker", "party", attack_bonus=5, ac=14)
    target = _entity("target", "monsters", ac=10)
    ws = _world(attacker, target)

    intent = ChargeIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=WEAPON_LONGSWORD,
        path_clear=True,
    )
    rng = _rng(attack_roll=15, damage_roll=3)
    events = resolve_charge(intent, ws, rng, next_event_id=0, timestamp=0.0)
    ws2 = apply_charge_events(ws, events)

    mods = ws2.entities["attacker"].get(EF.TEMPORARY_MODIFIERS, {})
    assert mods.get("charge_ac") == -2, (
        f"Expected charge_ac == -2, got {mods.get('charge_ac')}"
    )


# ---------------------------------------------------------------------------
# CH-03: charge_attack event emitted before attack roll events
# ---------------------------------------------------------------------------

def test_ch03_charge_attack_event_before_attack_roll():
    """Index of charge_attack event < index of first attack_roll event."""
    attacker = _entity("attacker", "party", attack_bonus=5)
    target = _entity("target", "monsters", ac=10)
    ws = _world(attacker, target)

    intent = ChargeIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=WEAPON_LONGSWORD,
        path_clear=True,
    )
    rng = _rng(attack_roll=15, damage_roll=3)
    events = resolve_charge(intent, ws, rng, next_event_id=0, timestamp=0.0)

    types = [e.event_type for e in events]
    assert "charge_attack" in types, "charge_attack event must be present"
    assert "attack_roll" in types, "attack_roll event must be present"
    charge_idx = types.index("charge_attack")
    atk_idx = types.index("attack_roll")
    assert charge_idx < atk_idx, (
        f"charge_attack (idx {charge_idx}) must precede attack_roll (idx {atk_idx})"
    )


# ---------------------------------------------------------------------------
# CH-04: Charge is full-round action — denied if standard already used
# ---------------------------------------------------------------------------

def test_ch04_charge_denied_if_standard_used():
    """ACTION_DENIED emitted if standard_used=True; no charge_attack event."""
    attacker = _entity("attacker", "party", attack_bonus=5)
    target = _entity("target", "monsters", ac=10)

    budget = ActionBudget(standard_used=True).to_dict()
    ws = _world(attacker, target, action_budget=budget)

    intent = ChargeIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=WEAPON_LONGSWORD,
        path_clear=True,
    )
    rng = _rng(attack_roll=15, damage_roll=3)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    event_types = [e.event_type for e in result.events]
    assert "ACTION_DENIED" in event_types, "ACTION_DENIED must be emitted when budget exhausted"
    assert "charge_attack" not in event_types, "charge_attack must NOT appear when denied"

    denied_ev = next(e for e in result.events if e.event_type == "ACTION_DENIED")
    assert denied_ev.payload.get("slot") == "full_round"


# ---------------------------------------------------------------------------
# CH-05: path_clear=False emits intent_validation_failed
# ---------------------------------------------------------------------------

def test_ch05_path_blocked_emits_validation_failed():
    """resolve_charge() with path_clear=False returns exactly one intent_validation_failed."""
    attacker = _entity("attacker", "party", attack_bonus=5)
    target = _entity("target", "monsters", ac=10)
    ws = _world(attacker, target)

    intent = ChargeIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=WEAPON_LONGSWORD,
        path_clear=False,
    )
    rng = _rng()
    events = resolve_charge(intent, ws, rng, next_event_id=0, timestamp=0.0)

    assert len(events) == 1
    assert events[0].event_type == "intent_validation_failed"
    assert events[0].payload["reason"] == "charge_path_blocked"

    # No attack_roll
    assert not any(e.event_type == "attack_roll" for e in events)


# ---------------------------------------------------------------------------
# CH-06: Spirited Charge + mounted → damage ×2
# ---------------------------------------------------------------------------

def test_ch06_spirited_charge_mounted_double_damage():
    """Spirited Charge feat + mounted → hp_changed delta is ×2; spirited_charge_multiplier event with multiplier==2."""
    attacker = _entity(
        "attacker", "party",
        attack_bonus=10,
        feats=["spirited_charge"],
        mounted_state={"mount_id": "horse_01"},
        str_mod=3,
    )
    target = _entity("target", "monsters", ac=5, hp=50, hp_max=50)
    ws = _world(attacker, target)

    intent = ChargeIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=WEAPON_LONGSWORD,
        path_clear=True,
    )
    # attack_roll=15 (guaranteed hit vs AC 5), damage_roll=4
    # base damage = 4 + 3(str) + 0(bonus) = 7, ×2 = 14
    rng = _rng(attack_roll=15, damage_roll=4)
    events = resolve_charge(intent, ws, rng, next_event_id=0, timestamp=0.0)

    sc_events = [e for e in events if e.event_type == "spirited_charge_multiplier"]
    assert len(sc_events) == 1
    assert sc_events[0].payload["multiplier"] == 2

    hp_events = [e for e in events if e.event_type == "hp_changed"]
    assert len(hp_events) >= 1
    delta = hp_events[0].payload["delta"]
    assert delta == -14, f"Expected delta=-14 (×2), got {delta}"


# ---------------------------------------------------------------------------
# CH-07: Spirited Charge + mounted + lance → damage ×3
# ---------------------------------------------------------------------------

def test_ch07_spirited_charge_lance_triple_damage():
    """Spirited Charge + mounted + lance weapon_type → hp_changed delta is ×3; multiplier==3."""
    attacker = _entity(
        "attacker", "party",
        attack_bonus=10,
        feats=["spirited_charge"],
        mounted_state={"mount_id": "horse_01"},
        str_mod=3,
    )
    target = _entity("target", "monsters", ac=5, hp=100, hp_max=100)
    ws = _world(attacker, target)

    weapon = _weapon_lance_with_type()
    intent = ChargeIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=weapon,
        path_clear=True,
    )
    # attack_roll=15, damage_roll=4
    # base = 4 + 3 + 0 = 7, ×3 = 21
    rng = _rng(attack_roll=15, damage_roll=4)
    events = resolve_charge(intent, ws, rng, next_event_id=0, timestamp=0.0)

    sc_events = [e for e in events if e.event_type == "spirited_charge_multiplier"]
    assert len(sc_events) == 1
    assert sc_events[0].payload["multiplier"] == 3

    hp_events = [e for e in events if e.event_type == "hp_changed"]
    assert len(hp_events) >= 1
    delta = hp_events[0].payload["delta"]
    assert delta == -21, f"Expected delta=-21 (×3), got {delta}"


# ---------------------------------------------------------------------------
# CH-08: Spirited Charge feat present but no mount → normal damage
# ---------------------------------------------------------------------------

def test_ch08_spirited_charge_no_mount_no_multiplier():
    """Spirited Charge feat without mount → damage ×1; no spirited_charge_multiplier event."""
    attacker = _entity(
        "attacker", "party",
        attack_bonus=10,
        feats=["spirited_charge"],
        str_mod=3,
        # no mounted_state
    )
    target = _entity("target", "monsters", ac=5, hp=50, hp_max=50)
    ws = _world(attacker, target)

    intent = ChargeIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=WEAPON_LONGSWORD,
        path_clear=True,
    )
    # attack_roll=15, damage_roll=4 -> base = 4+3 = 7, no multiplier
    rng = _rng(attack_roll=15, damage_roll=4)
    events = resolve_charge(intent, ws, rng, next_event_id=0, timestamp=0.0)

    # No spirited_charge_multiplier event
    assert not any(e.event_type == "spirited_charge_multiplier" for e in events)

    hp_events = [e for e in events if e.event_type == "hp_changed"]
    if hp_events:
        delta = hp_events[0].payload["delta"]
        assert delta == -7, f"Expected delta=-7 (no multiplier), got {delta}"


# ---------------------------------------------------------------------------
# CH-09: Charge AC penalty clears at start of charger's next turn
# ---------------------------------------------------------------------------

def test_ch09_charge_ac_penalty_clears_next_turn():
    """Execute two turns for the same actor: second turn emits charge_ac_expired and clears the key."""
    attacker = _entity("attacker", "party", attack_bonus=5)
    target = _entity("target", "monsters", ac=5, hp=50)
    ws = _world(attacker, target)

    intent = ChargeIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=WEAPON_LONGSWORD,
        path_clear=True,
    )

    # Turn 1: charge — penalty gets written
    rng1 = _rng(attack_roll=15, damage_roll=3)
    result1 = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng1)
    ws_after_charge = result1.world_state

    mods_after = ws_after_charge.entities["attacker"].get(EF.TEMPORARY_MODIFIERS, {})
    assert "charge_ac" in mods_after, "charge_ac must be present after charge turn"

    # Turn 2: no combat intent — just trigger turn start
    rng2 = _rng(attack_roll=1, damage_roll=1)
    result2 = execute_turn(ws_after_charge, _ctx(), combat_intent=None, rng=rng2)

    # charge_ac_expired emitted in second turn
    types2 = [e.event_type for e in result2.events]
    assert "charge_ac_expired" in types2, "charge_ac_expired must be emitted on charger's next turn"

    # charge_ac key no longer present
    mods2 = result2.world_state.entities["attacker"].get(EF.TEMPORARY_MODIFIERS, {})
    assert "charge_ac" not in mods2, "charge_ac key must be cleared after next turn"


# ---------------------------------------------------------------------------
# CH-10: Charge against DEFEATED target → intent_validation_failed
# ---------------------------------------------------------------------------

def test_ch10_charge_defeated_target_validation_failed():
    """resolve_charge() returns intent_validation_failed when target is defeated."""
    attacker = _entity("attacker", "party", attack_bonus=5)
    target = _entity("target", "monsters", ac=10, defeated=True)
    ws = _world(attacker, target)

    intent = ChargeIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=WEAPON_LONGSWORD,
        path_clear=True,
    )
    rng = _rng()
    events = resolve_charge(intent, ws, rng, next_event_id=0, timestamp=0.0)

    assert len(events) == 1
    assert events[0].event_type == "intent_validation_failed"
    assert events[0].payload["reason"] == "target_already_defeated"

    # No attack_roll, no charge_ac_applied
    assert not any(e.event_type == "attack_roll" for e in events)
    assert not any(e.event_type == "charge_ac_applied" for e in events)
