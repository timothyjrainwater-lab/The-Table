"""Gate tests — WO-ENGINE-CONFUSED-BEHAVIOR-001
CFB-001..008: d100 roll at turn start; 5 behavioral branches (3 enforced, 2 CONSUME_DEFERRED).
"""
from __future__ import annotations
from typing import Any, Dict
from unittest.mock import MagicMock
from aidm.schemas.entity_fields import EF
from aidm.core.condition_combat_resolver import create_confused_condition
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.play_loop import TurnContext, execute_turn

_SWORD = Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing")
_SWORD_DICT = {"name": "longsword", "enhancement_bonus": 0, "damage_dice": "1d8",
               "damage_bonus": 0, "damage_type": "slashing", "tags": [], "material": "steel"}


def _entity(eid: str, conditions: dict = None, pos: dict = None) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid, EF.TEAM: "party",
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 12,
        EF.ATTACK_BONUS: 4, EF.BAB: 4, EF.STR_MOD: 2, EF.DEX_MOD: 0,
        EF.DEFEATED: False, EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: conditions or {},
        EF.FEATS: [], EF.POSITION: pos or {"x": 0, "y": 0}, EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.NEGATIVE_LEVELS: 0, EF.WEAPON_BROKEN: False, EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {}, EF.WEAPON: _SWORD_DICT,
    }


def _ws(entities: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e", entities=entities,
        active_combat={
            "turn_counter": 0, "round_index": 1,
            "initiative_order": list(entities.keys()),
            "flat_footed_actors": [], "aoo_used_this_round": [],
            "aoo_count_this_round": {}, "deflect_arrows_used": [],
            "cleave_used_this_turn": set(),
        },
    )


def _ctx() -> TurnContext:
    return TurnContext(turn_index=0, actor_id="actor_1", actor_team="party")


def _rng(roll: int = 15) -> MagicMock:
    rng = MagicMock()
    rng.stream.return_value.randint.return_value = roll
    return rng


def test_CFB001_confused_act_normally_intent_proceeds():
    """CFB-001: Confused entity + seeded roll 15 (act normally, 11–20) → intent proceeds (not early-returned as confused)."""
    ci = create_confused_condition("test", 0)
    ws = _ws({
        "actor_1": _entity("actor_1", {"confused": ci.to_dict()}),
        "target_1": _entity("target_1"),
    })
    intent = AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD)
    # roll=15 → bracket 11-20 → act_normally → fall through
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(15))
    # Should NOT return confused_babble or confused_*_deferred
    assert result.status not in ("confused_babble", "confused_attack_caster_deferred", "confused_flee_deferred"), (
        f"Confused act_normally incorrectly blocked with status={result.status}"
    )
    # confused_behavior_roll event should exist with behavior="act_normally"
    roll_events = [e for e in result.events if e.event_type == "confused_behavior_roll"]
    assert roll_events, "No confused_behavior_roll event emitted"
    assert roll_events[0].payload.get("behavior") == "act_normally"


def test_CFB002_confused_babble_blocks_turn():
    """CFB-002: Confused entity + seeded roll 35 (babble, 21–50) → TurnResult(status="confused_babble")."""
    ci = create_confused_condition("test", 0)
    ws = _ws({
        "actor_1": _entity("actor_1", {"confused": ci.to_dict()}),
        "target_1": _entity("target_1"),
    })
    intent = AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD)
    # roll=35 → bracket 21-50 → babble
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(35))
    assert result.status == "confused_babble", f"Expected confused_babble, got {result.status}"
    babble_events = [e for e in result.events if e.event_type == "confused_babble"]
    assert babble_events, "No confused_babble event emitted"


def test_CFB003_confused_attack_nearest():
    """CFB-003: Confused entity + seeded roll 85 (attack nearest, 71–100) → attack toward nearest entity."""
    ci = create_confused_condition("test", 0)
    ws = _ws({
        "actor_1": _entity("actor_1", {"confused": ci.to_dict()}, pos={"x": 0, "y": 0}),
        "target_1": _entity("target_1", pos={"x": 1, "y": 0}),
    })
    # No explicit combat_intent — confused entity will substitute nearest target
    intent = AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD)
    # roll=85 → bracket 71-100 → attack_nearest
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(85))
    assert result.status not in ("confused_babble", "confused_attack_caster_deferred", "confused_flee_deferred"), (
        f"attack_nearest should proceed to attack, got status={result.status}"
    )
    roll_events = [e for e in result.events if e.event_type == "confused_behavior_roll"]
    assert roll_events, "No confused_behavior_roll event emitted"
    assert roll_events[0].payload.get("behavior") == "attack_nearest"


def test_CFB004_confused_attack_caster_deferred():
    """CFB-004: Confused entity + seeded roll 5 (attack caster, 01–10) → CONSUME_DEFERRED event + skip turn."""
    ci = create_confused_condition("test", 0)
    ws = _ws({
        "actor_1": _entity("actor_1", {"confused": ci.to_dict()}),
        "target_1": _entity("target_1"),
    })
    intent = AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD)
    # roll=5 → bracket 01-10 → attack_caster CONSUME_DEFERRED
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(5))
    assert result.status == "confused_attack_caster_deferred", (
        f"Expected confused_attack_caster_deferred, got {result.status}"
    )
    deferred_events = [e for e in result.events if e.event_type == "confused_attack_caster_deferred"]
    assert deferred_events, "No confused_attack_caster_deferred event emitted (must not be silent)"


def test_CFB005_confused_flee_deferred():
    """CFB-005: Confused entity + seeded roll 60 (flee, 51–70) → CONSUME_DEFERRED event + skip turn."""
    ci = create_confused_condition("test", 0)
    ws = _ws({
        "actor_1": _entity("actor_1", {"confused": ci.to_dict()}),
        "target_1": _entity("target_1"),
    })
    intent = AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD)
    # roll=60 → bracket 51-70 → flee CONSUME_DEFERRED
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(60))
    assert result.status == "confused_flee_deferred", (
        f"Expected confused_flee_deferred, got {result.status}"
    )
    flee_events = [e for e in result.events if e.event_type == "confused_flee_deferred"]
    assert flee_events, "No confused_flee_deferred event emitted (must not be silent)"


def test_CFB006_non_confused_no_gate():
    """CFB-006: Non-confused entity → no confused gate fires; intent proceeds normally."""
    ws = _ws({
        "actor_1": _entity("actor_1"),
        "target_1": _entity("target_1"),
    })
    intent = AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD)
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(15))
    roll_events = [e for e in result.events if e.event_type == "confused_behavior_roll"]
    assert not roll_events, f"confused_behavior_roll fired for non-confused entity: {roll_events}"


def test_CFB007_attack_nearest_does_not_target_self():
    """CFB-007: attack_nearest (71–100) in 2-entity world_state → confused entity attacks the other entity, not self."""
    ci = create_confused_condition("test", 0)
    ws = _ws({
        "actor_1": _entity("actor_1", {"confused": ci.to_dict()}, pos={"x": 0, "y": 0}),
        "target_1": _entity("target_1", pos={"x": 1, "y": 0}),
    })
    intent = AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD)
    # roll=85 → attack_nearest
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(85))
    # Check that any attack events target "target_1" not "actor_1"
    attack_events = [
        e for e in result.events
        if e.event_type in ("attack_roll", "attack_resolved", "damage_dealt")
    ]
    for ev in attack_events:
        target = ev.payload.get("target_id") or ev.payload.get("defender_id")
        if target is not None:
            assert target != "actor_1", f"Confused entity attacked self in event {ev.event_type}"


def test_CFB008_confused_behavior_roll_event_payload():
    """CFB-008: confused_behavior_roll event carries roll value + bracket + behavior label."""
    ci = create_confused_condition("test", 0)
    ws = _ws({
        "actor_1": _entity("actor_1", {"confused": ci.to_dict()}),
        "target_1": _entity("target_1"),
    })
    intent = AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD)
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(35))
    roll_events = [e for e in result.events if e.event_type == "confused_behavior_roll"]
    assert roll_events, "No confused_behavior_roll event emitted"
    payload = roll_events[0].payload
    assert "d100_roll" in payload, f"d100_roll missing from payload: {payload}"
    assert "behavior" in payload, f"behavior missing from payload: {payload}"
    assert payload["d100_roll"] == 35, f"Expected d100_roll=35, got {payload['d100_roll']}"
    assert payload["behavior"] == "babble", f"Expected behavior=babble, got {payload['behavior']}"
