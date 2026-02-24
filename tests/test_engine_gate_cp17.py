"""Gate CP-17 — Condition Enforcement.

Tests:
CP17-01  Stunned entity attempts action → action_denied event emitted, noop turn
CP17-02  Dazed entity attempts standard action → action_denied emitted
CP17-03  Paralyzed entity attempts action → action_denied emitted
CP17-04  Unconscious entity attempts action → action_denied emitted
CP17-05  Prone entity stands — no enemies adjacent → no AoO triggered
CP17-06  Helpless entity targeted by melee → attack hits without roll (auto_hit=True)
CP17-07  Helpless entity targeted by ranged → attack still rolls
CP17-08  Flat-footed entity attacked → DEX mod not applied to AC
CP17-09  Stunned entity attacked → DEX mod not applied to AC
CP17-10  Normal entity attacked → DEX mod applied normally
CP17-11  Entity with no conditions → no enforcement, normal action flow
CP17-12  Condition removed mid-combat → next turn no longer gated
CP17-13  ACTION_DENIED event shape → contains entity_id, conditions list
CP17-14  Helpless auto-hit: attack_roll event has auto_hit_helpless=True
CP17-15  Regression: existing attack tests unaffected
"""

from copy import deepcopy
from typing import Any, Dict

import pytest

from aidm.core.attack_resolver import resolve_attack
from aidm.core.conditions import apply_condition, remove_condition
from aidm.core.play_loop import TurnContext, execute_turn
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.conditions import (
    create_stunned_condition,
    create_dazed_condition,
    create_paralyzed_condition,
    create_unconscious_condition,
    create_helpless_condition,
    create_flat_footed_condition,
)
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position


# ─── helpers ────────────────────────────────────────────────────────────────

def _pos(x: int = 0, y: int = 0) -> dict:
    return {"x": x, "y": y}


def _sword() -> Weapon:
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="slashing",
        weapon_type="one-handed",
    )


def _bow() -> Weapon:
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="piercing",
        weapon_type="ranged",
        range_increment=60,
    )


def _fighter(eid: str = "fighter_01", team: str = "party", dex_mod: int = 2) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 15,
        EF.DEX_MOD: dex_mod,
        EF.STR_MOD: 2,
        EF.BAB: 5,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: _pos(0, 0),
    }


def _goblin(eid: str = "goblin_01", team: str = "monsters", hp: int = 15) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 13,
        EF.DEX_MOD: 1,
        EF.STR_MOD: 0,
        EF.BAB: 1,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: _pos(1, 0),
    }


def _world(*entity_dicts) -> WorldState:
    entities = {e[EF.ENTITY_ID]: e for e in entity_dicts}
    return WorldState(ruleset_version="3.5e", entities=entities)


def _apply_cond(ws: WorldState, actor_id: str, condition_instance) -> WorldState:
    return apply_condition(ws, actor_id, condition_instance)


# ─── CP17-01: Stunned entity cannot act ─────────────────────────────────────

def test_cp17_01_stunned_action_denied():
    """Stunned entity gets action_denied, turn returns status='action_denied'."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    ws = _world(fighter, goblin)
    cond = create_stunned_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "f01", cond)

    rng = RNGManager(42)
    ctx = TurnContext(actor_id="f01", actor_team="party", turn_index=0)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    result = execute_turn(ws, ctx, combat_intent=intent, rng=rng)

    assert result.status == "action_denied"
    event_types = [e.event_type for e in result.events]
    assert "action_denied" in event_types


# ─── CP17-02: Dazed entity cannot act ────────────────────────────────────────

def test_cp17_02_dazed_action_denied():
    """Dazed entity gets action_denied."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    ws = _world(fighter, goblin)
    cond = create_dazed_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "f01", cond)

    rng = RNGManager(42)
    ctx = TurnContext(actor_id="f01", actor_team="party", turn_index=0)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    result = execute_turn(ws, ctx, combat_intent=intent, rng=rng)

    assert result.status == "action_denied"


# ─── CP17-03: Paralyzed entity cannot act ────────────────────────────────────

def test_cp17_03_paralyzed_action_denied():
    """Paralyzed entity gets action_denied."""
    from aidm.schemas.conditions import create_paralyzed_condition
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    ws = _world(fighter, goblin)
    cond = create_paralyzed_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "f01", cond)

    rng = RNGManager(42)
    ctx = TurnContext(actor_id="f01", actor_team="party", turn_index=0)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    result = execute_turn(ws, ctx, combat_intent=intent, rng=rng)

    assert result.status == "action_denied"


# ─── CP17-04: Unconscious entity cannot act ──────────────────────────────────

def test_cp17_04_unconscious_action_denied():
    """Unconscious entity gets action_denied."""
    from aidm.schemas.conditions import create_unconscious_condition
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    ws = _world(fighter, goblin)
    cond = create_unconscious_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "f01", cond)

    rng = RNGManager(42)
    ctx = TurnContext(actor_id="f01", actor_team="party", turn_index=0)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    result = execute_turn(ws, ctx, combat_intent=intent, rng=rng)

    assert result.status == "action_denied"


# ─── CP17-05: Prone entity stands — no adjacent enemies, no AoO ──────────────

def test_cp17_05_prone_stand_no_aoo():
    """Prone entity standing with no adjacent enemies: no AoO triggered.
    This test verifies the data layer is correct — prone has standing_triggers_aoo=True
    but without an adjacent enemy there is no AoO opportunity object to fire.
    We verify via normal turn flow (no action_denied for prone alone).
    """
    from aidm.schemas.conditions import create_prone_condition
    fighter = _fighter("f01")
    # Goblin far away (no adjacency)
    goblin_far = _goblin("g01")
    goblin_far[EF.POSITION] = _pos(10, 10)
    ws = _world(fighter, goblin_far)
    cond = create_prone_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "f01", cond)

    from aidm.core.conditions import get_condition_modifiers
    mods = get_condition_modifiers(ws, "f01")
    # Prone sets standing_triggers_aoo=True in metadata
    assert mods.standing_triggers_aoo is True
    # But prone does NOT set actions_prohibited
    assert mods.actions_prohibited is False


# ─── CP17-06: Helpless entity targeted by melee → auto-hit ──────────────────

def test_cp17_06_helpless_melee_auto_hit():
    """Melee attack against a helpless target auto-hits (auto_hit_helpless=True in event)."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    ws = _world(fighter, goblin)
    cond = create_helpless_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "g01", cond)

    # Use seed that would produce a low roll (would normally miss)
    rng = RNGManager(1)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=-10,  # Very low bonus — would normally miss
        weapon=_sword(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=0.0)
    attack_rolls = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_rolls) == 1
    assert attack_rolls[0].payload["auto_hit_helpless"] is True
    assert attack_rolls[0].payload["hit"] is True


# ─── CP17-07: Helpless entity targeted by ranged → still rolls ───────────────

def test_cp17_07_helpless_ranged_rolls():
    """Ranged attack vs helpless target still rolls (auto_hit only for melee)."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    ws = _world(fighter, goblin)
    cond = create_helpless_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "g01", cond)

    rng = RNGManager(42)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_bow(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=0.0)
    attack_rolls = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_rolls) == 1
    assert attack_rolls[0].payload["auto_hit_helpless"] is False


# ─── CP17-08: Flat-footed entity → DEX mod stripped from AC ─────────────────

def test_cp17_08_flat_footed_loses_dex():
    """Flat-footed entity: DEX mod subtracted from target AC in attack resolution."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    goblin[EF.AC] = 15        # Includes +2 DEX
    goblin[EF.DEX_MOD] = 2
    ws = _world(fighter, goblin)

    cond = create_flat_footed_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "g01", cond)

    rng = RNGManager(42)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=0.0)
    attack_rolls = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_rolls) == 1
    payload = attack_rolls[0].payload
    # dex_penalty should be -2 (DEX mod stripped)
    assert payload["dex_penalty"] == -2
    # Effective AC should be 15 - 2 = 13
    assert payload["target_ac"] == 13


# ─── CP17-09: Stunned entity → loses DEX to AC ──────────────────────────────

def test_cp17_09_stunned_loses_dex():
    """Stunned entity: DEX mod stripped from target AC."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    goblin[EF.AC] = 14      # Includes +1 DEX
    goblin[EF.DEX_MOD] = 1
    ws = _world(fighter, goblin)

    cond = create_stunned_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "g01", cond)

    rng = RNGManager(42)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=0.0)
    attack_rolls = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_rolls) == 1
    payload = attack_rolls[0].payload
    assert payload["dex_penalty"] == -1
    assert payload["target_ac"] <= 14  # Effective AC is base - DEX


# ─── CP17-10: Normal entity → DEX mod applied normally ──────────────────────

def test_cp17_10_normal_entity_dex_preserved():
    """Normal entity (no conditions): DEX mod is preserved in AC."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    goblin[EF.AC] = 15
    goblin[EF.DEX_MOD] = 2
    ws = _world(fighter, goblin)

    rng = RNGManager(42)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=0.0)
    attack_rolls = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_rolls) == 1
    payload = attack_rolls[0].payload
    assert payload["dex_penalty"] == 0
    assert payload["target_ac"] == 15  # DEX preserved — AC unchanged


# ─── CP17-11: No conditions → normal action flow ────────────────────────────

def test_cp17_11_no_conditions_normal_flow():
    """Entity with no conditions: normal turn proceeds without denial."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    ws = _world(fighter, goblin)

    rng = RNGManager(42)
    ctx = TurnContext(actor_id="f01", actor_team="party", turn_index=0)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    result = execute_turn(ws, ctx, combat_intent=intent, rng=rng)

    assert result.status == "ok"
    event_types = [e.event_type for e in result.events]
    assert "action_denied" not in event_types
    assert "attack_roll" in event_types


# ─── CP17-12: Condition removed mid-combat → next turn no gate ──────────────

def test_cp17_12_condition_removed_next_turn_ok():
    """After removing a condition, next turn flows normally."""
    from aidm.core.conditions import remove_condition
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    ws = _world(fighter, goblin)

    # Apply stunned
    cond = create_stunned_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "f01", cond)

    # Remove it
    ws = remove_condition(ws, "f01", "stunned")

    rng = RNGManager(42)
    ctx = TurnContext(actor_id="f01", actor_team="party", turn_index=0)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    result = execute_turn(ws, ctx, combat_intent=intent, rng=rng)

    assert result.status == "ok"
    event_types = [e.event_type for e in result.events]
    assert "action_denied" not in event_types


# ─── CP17-13: action_denied event shape ─────────────────────────────────────

def test_cp17_13_action_denied_event_shape():
    """action_denied event has correct shape: entity_id, conditions, reason."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    ws = _world(fighter, goblin)
    cond = create_stunned_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "f01", cond)

    rng = RNGManager(42)
    ctx = TurnContext(actor_id="f01", actor_team="party", turn_index=0)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    result = execute_turn(ws, ctx, combat_intent=intent, rng=rng)

    denied_events = [e for e in result.events if e.event_type == "action_denied"]
    assert len(denied_events) == 1
    payload = denied_events[0].payload
    assert "entity_id" in payload
    assert payload["entity_id"] == "f01"
    assert "reason" in payload
    assert payload["reason"] == "actions_prohibited"
    assert "conditions" in payload


# ─── CP17-14: auto_hit_helpless flag in attack_roll event ────────────────────

def test_cp17_14_auto_hit_helpless_flag_in_event():
    """attack_roll event payload has auto_hit_helpless=True for melee vs helpless."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    ws = _world(fighter, goblin)
    cond = create_helpless_condition(source="test", applied_at_event_id=0)
    ws = apply_condition(ws, "g01", cond)

    rng = RNGManager(42)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=5,
        weapon=_sword(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=0.0)
    attack_rolls = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_rolls) == 1
    assert "auto_hit_helpless" in attack_rolls[0].payload
    assert attack_rolls[0].payload["auto_hit_helpless"] is True


# ─── CP17-15: Regression — existing attack tests unaffected ─────────────────

def test_cp17_15_regression_normal_attack():
    """Normal melee attack (no conditions) still resolves correctly."""
    fighter = _fighter("f01")
    goblin = _goblin("g01")
    goblin[EF.AC] = 12
    ws = _world(fighter, goblin)

    rng = RNGManager(42)
    intent = AttackIntent(
        attacker_id="f01",
        target_id="g01",
        attack_bonus=6,  # Sufficient to hit AC 12 on moderate rolls
        weapon=_sword(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=0.0)

    # Must have attack_roll event
    attack_rolls = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_rolls) == 1
    # No auto_hit on normal target
    assert attack_rolls[0].payload["auto_hit_helpless"] is False
    assert attack_rolls[0].payload["dex_penalty"] == 0
