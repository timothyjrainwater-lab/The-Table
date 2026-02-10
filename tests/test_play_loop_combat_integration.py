"""Integration tests for CP-12 combat intent routing in play loop.

Tests that combat intents (AttackIntent, FullAttackIntent) are correctly:
- Validated (actor match, target exists, target not defeated)
- Routed to CP-10/CP-11 resolvers
- Applied to WorldState via events
- Returned with correct status and narration tokens

Tier-1 (MUST PASS):
- Player intent triggers correct resolver
- Events match CP-10/CP-11 behavior
- WorldState changes only via events
- Deterministic replay through full loop
- Invalid intent produces no state change

Tier-2 (SHOULD PASS):
- Narration tokens correct
- Mixed attack/full attack works
- Backward compatibility preserved
"""

import pytest
from aidm.core.play_loop import execute_turn, TurnContext, TurnResult
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.full_attack_resolver import FullAttackIntent
from aidm.core.rng_manager import RNGManager


# ==============================================================================
# TIER 1: MUST-PASS TESTS
# ==============================================================================

def test_attack_intent_triggers_cp10_resolver():
    """Tier 1: AttackIntent should route to resolve_attack() and emit attack events."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6}
        },
        active_combat={"turn_counter": 0}
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should succeed
    assert result.status == "ok"

    # Should have turn_start, attack_roll, damage_roll (if hit), hp_changed (if hit), turn_end
    event_types = [e.event_type for e in result.events]
    assert "turn_start" in event_types
    assert "attack_roll" in event_types
    assert "turn_end" in event_types

    # If hit occurred, should have damage events
    attack_events = [e for e in result.events if e.event_type == "attack_roll"]
    if attack_events and attack_events[0].payload["hit"]:
        assert "damage_roll" in event_types
        assert "hp_changed" in event_types


def test_full_attack_intent_triggers_cp11_resolver():
    """Tier 1: FullAttackIntent should route to resolve_full_attack() and emit full attack events."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 50, "hp_max": 50},
            "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6}
        },
        active_combat={"turn_counter": 0}
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=6,  # 2 attacks: +6/+1
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should succeed
    assert result.status == "ok"

    # Should have turn_start, full_attack_start, attack_roll(s), full_attack_end, turn_end
    event_types = [e.event_type for e in result.events]
    assert "turn_start" in event_types
    assert "full_attack_start" in event_types
    assert "attack_roll" in event_types
    assert "full_attack_end" in event_types
    assert "turn_end" in event_types


def test_combat_events_match_cp10_cp11_behavior():
    """Tier 1: Events from combat intents should be identical to standalone CP-10/CP-11 resolution."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6}
        }
    )

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng1 = RNGManager(master_seed=100)
    rng2 = RNGManager(master_seed=100)

    # Resolve via play loop
    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")
    loop_result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng1,
        next_event_id=0,
        timestamp=1.0
    )

    # Resolve via standalone CP-10
    from aidm.core.attack_resolver import resolve_attack
    standalone_events = resolve_attack(intent, world_state, rng2, next_event_id=1, timestamp=1.1)

    # Extract combat events from play loop (skip turn_start and turn_end)
    loop_combat_events = [e for e in loop_result.events if e.event_type not in {"turn_start", "turn_end"}]

    # Event payloads should be identical (ignoring event IDs and timestamps)
    assert len(loop_combat_events) == len(standalone_events)
    for loop_event, standalone_event in zip(loop_combat_events, standalone_events):
        assert loop_event.event_type == standalone_event.event_type
        assert loop_event.payload == standalone_event.payload


def test_world_state_changes_only_via_events():
    """Tier 1: WorldState should only change via event application, not direct mutation."""
    original_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"ac": 10, "hp_current": 6, "hp_max": 6}
        }
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=10,  # High bonus, likely to hit
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)

    # Capture original HP
    original_hp = original_state.entities["goblin"]["hp_current"]

    result = execute_turn(
        world_state=original_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Original state should be unchanged
    assert original_state.entities["goblin"]["hp_current"] == original_hp

    # Result state should reflect HP change (if hit occurred)
    hp_events = [e for e in result.events if e.event_type == "hp_changed"]
    if hp_events:
        assert result.world_state.entities["goblin"]["hp_current"] != original_hp


def test_deterministic_replay_through_loop():
    """Tier 1: Same RNG seed should produce identical state hash through full play loop."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6}
        },
        active_combat={"turn_counter": 0}
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Run 3 times with same seed
    results = []
    for _ in range(3):
        rng = RNGManager(master_seed=100)
        result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0
        )
        results.append(result)

    # All final states should be identical
    first_result = results[0]
    for result in results[1:]:
        assert result.world_state.state_hash() == first_result.world_state.state_hash()

        # Event payloads should be identical
        assert len(result.events) == len(first_result.events)
        for e1, e2 in zip(first_result.events, result.events):
            assert e1.event_type == e2.event_type
            assert e1.payload == e2.payload


def test_invalid_intent_actor_mismatch():
    """Tier 1: Intent with wrong actor should fail validation and produce no state change."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6}
        }
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    # Intent has wrong attacker (goblin instead of fighter)
    intent = AttackIntent(
        attacker_id="goblin",
        target_id="fighter",
        attack_bonus=3,
        weapon=Weapon(damage_dice="1d6", damage_bonus=1, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should fail validation
    assert result.status == "invalid_intent"
    assert result.failure_reason is not None
    assert "does not match turn actor" in result.failure_reason

    # Should emit validation failure event
    validation_events = [e for e in result.events if e.event_type == "intent_validation_failed"]
    assert len(validation_events) == 1
    assert validation_events[0].payload["reason"] == "intent_actor_mismatch"

    # State should be unchanged
    assert result.world_state.state_hash() == world_state.state_hash()


def test_invalid_intent_target_not_found():
    """Tier 1: Intent with nonexistent target should fail validation."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 10, "hp_max": 10}
        }
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="nonexistent_target",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should fail validation
    assert result.status == "invalid_intent"
    assert "not found in world state" in result.failure_reason

    # Should emit validation failure event
    validation_events = [e for e in result.events if e.event_type == "intent_validation_failed"]
    assert len(validation_events) == 1
    assert validation_events[0].payload["reason"] == "target_not_found"


def test_invalid_intent_target_already_defeated():
    """Tier 1: Intent targeting defeated entity should fail validation."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"ac": 15, "hp_current": -5, "hp_max": 6, "defeated": True}
        }
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should fail validation
    assert result.status == "invalid_intent"
    assert "already defeated" in result.failure_reason

    # Should emit validation failure event
    validation_events = [e for e in result.events if e.event_type == "intent_validation_failed"]
    assert len(validation_events) == 1
    assert validation_events[0].payload["reason"] == "target_already_defeated"


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS
# ==============================================================================

def test_narration_token_attack_hit():
    """Tier 2: Narration token should be "attack_hit" when attack succeeds."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"ac": 10, "hp_current": 6, "hp_max": 6}  # Low AC
        }
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=10,  # High bonus, very likely to hit
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Find seed that produces hit
    for seed in range(100):
        rng = RNGManager(master_seed=seed)
        result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0
        )

        attack_events = [e for e in result.events if e.event_type == "attack_roll"]
        if attack_events and attack_events[0].payload["hit"]:
            assert result.narration == "attack_hit"
            break
    else:
        pytest.fail("Could not find seed with attack hit in 100 tries")


def test_narration_token_attack_miss():
    """Tier 2: Narration token should be "attack_miss" when attack fails."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"ac": 20, "hp_current": 6, "hp_max": 6}  # High AC
        }
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=0,  # Low bonus
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Find seed that produces miss
    for seed in range(100):
        rng = RNGManager(master_seed=seed)
        result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0
        )

        attack_events = [e for e in result.events if e.event_type == "attack_roll"]
        if attack_events and not attack_events[0].payload["hit"]:
            assert result.narration == "attack_miss"
            break
    else:
        pytest.fail("Could not find seed with attack miss in 100 tries")


def test_narration_token_full_attack_complete():
    """Tier 2: Narration token should be "full_attack_complete" for full attacks."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 50, "hp_max": 50},
            "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6}
        }
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=6,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    assert result.narration == "full_attack_complete"


def test_mixed_attack_and_full_attack():
    """Tier 2: Play loop should handle both attack types in sequence."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 50, "hp_max": 50},
            "rogue": {"ac": 14, "hp_current": 30, "hp_max": 30},
            "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6}
        }
    )

    rng = RNGManager(master_seed=42)

    # Turn 1: Fighter uses AttackIntent
    turn1_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")
    intent1 = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    result1 = execute_turn(
        world_state=world_state,
        turn_ctx=turn1_ctx,
        combat_intent=intent1,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    assert result1.status == "ok"

    # Turn 2: Rogue uses FullAttackIntent
    turn2_ctx = TurnContext(turn_index=1, actor_id="rogue", actor_team="party")
    intent2 = FullAttackIntent(
        attacker_id="rogue",
        target_id="goblin",
        base_attack_bonus=4,
        weapon=Weapon(damage_dice="1d6", damage_bonus=2, damage_type="piercing")
    )

    result2 = execute_turn(
        world_state=result1.world_state,
        turn_ctx=turn2_ctx,
        combat_intent=intent2,
        rng=rng,
        next_event_id=len(result1.events),
        timestamp=2.0
    )

    assert result2.status == "ok"


def test_backward_compatibility_policy_based_resolution():
    """Tier 2: Play loop should still support policy-based resolution (no combat intent)."""
    from aidm.schemas.doctrine import MonsterDoctrine
    from aidm.core.doctrine_rules import derive_tactical_envelope

    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {"ac": 15, "hp_current": 6, "hp_max": 6, "position": {"x": 0, "y": 0}, "team": "monsters"},
            "fighter": {"ac": 16, "hp_current": 10, "hp_max": 10, "position": {"x": 10, "y": 0}, "team": "party"}
        }
    )

    # Create goblin doctrine
    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        citations=[{"source_id": "e390dfd9143f", "page": 133}]
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

    turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")

    # Execute turn WITHOUT combat intent (policy-based)
    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        doctrine=goblin_doctrine,
        next_event_id=0,
        timestamp=1.0
    )

    # Should succeed with policy evaluation
    assert result.status == "ok"

    # Should have tactic_selected event
    tactic_events = [e for e in result.events if e.event_type == "tactic_selected"]
    assert len(tactic_events) == 1
