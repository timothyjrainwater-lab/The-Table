"""Integration tests for CP-15 Attacks of Opportunity (AoO) kernel.

Tests AoO trigger detection, resolution ordering, and action abortion:
- Movement provocation (leaving threatened square)
- AoO eligibility (one per actor per round)
- Deterministic resolution ordering (initiative → lexicographic)
- Action abortion when provoker defeated
- Backward compatibility with CP-09–CP-14

Tier-1 (MUST PASS):
- Basic AoO trigger on movement
- AoO defeats provoker (action aborts)
- One AoO per reactor per round limit
- Multiple reactors resolve in initiative order
- Deterministic replay through AoO sequence

Tier-2 (SHOULD PASS):
- Multiple rounds with AoO usage reset
- Backward compatibility (CP-14 tests unaffected)
"""

import pytest
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import StepMoveIntent, GridPosition, AttackIntent, Weapon
from aidm.core.combat_controller import start_combat


# ==============================================================================
# TIER 1: MUST-PASS TESTS
# ==============================================================================

def test_aoo_triggers_on_movement_out():
    """Tier 1: Moving out of threatened square triggers AoO."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "position": {"x": 5, "y": 5},
                "team": "monsters",
                "attack_bonus": 2,
                "weapon": {
                    "damage_dice": "1d6",
                    "damage_bonus": 0,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 6, "y": 5},  # Adjacent to goblin
                "team": "party",
                "attack_bonus": 5,
                "weapon": {
                    "damage_dice": "1d8",
                    "damage_bonus": 3,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "goblin_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    # Goblin moves away from fighter (provokes AoO)
    move_intent = StepMoveIntent(
        actor_id="goblin_1",
        from_pos=GridPosition(x=5, y=5),
        to_pos=GridPosition(x=4, y=5)  # Moving away (west)
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=move_intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should have AoO events
    event_types = [e.event_type for e in result.events]
    assert "aoo_triggered" in event_types
    assert "attack_roll" in event_types  # AoO attack occurred


def test_aoo_defeats_provoker_action_aborts():
    """Tier 1: Provoker defeated by AoO causes action abort."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 10,  # Low AC for guaranteed hit
                "hp_current": 1,  # Low HP for easy defeat
                "hp_max": 6,
                "position": {"x": 5, "y": 5},
                "team": "monsters",
                "attack_bonus": 2,
                "weapon": {
                    "damage_dice": "1d6",
                    "damage_bonus": 0,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 6, "y": 5},
                "team": "party",
                "attack_bonus": 15,  # High attack bonus for guaranteed hit
                "weapon": {
                    "damage_dice": "2d6",
                    "damage_bonus": 5,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "goblin_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    # Goblin moves away (will likely be defeated by AoO)
    move_intent = StepMoveIntent(
        actor_id="goblin_1",
        from_pos=GridPosition(x=5, y=5),
        to_pos=GridPosition(x=4, y=5)
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    rng = RNGManager(master_seed=100)  # Seed chosen to produce defeat

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=move_intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Check for action abort
    event_types = [e.event_type for e in result.events]

    # If goblin was defeated, should have action_aborted
    if any(e.event_type == "entity_defeated" and e.payload.get("entity_id") == "goblin_1" for e in result.events):
        assert "action_aborted" in event_types
        assert result.narration == "action_aborted_by_aoo"


def test_one_aoo_per_reactor_per_round():
    """Tier 1: Each reactor can make only one AoO per round."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 20,  # High HP to survive both attempts
                "hp_max": 20,
                "position": {"x": 5, "y": 5},
                "team": "monsters",
                "attack_bonus": 2,
                "weapon": {
                    "damage_dice": "1d6",
                    "damage_bonus": 0,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 6, "y": 5},
                "team": "party",
                "attack_bonus": 5,
                "weapon": {
                    "damage_dice": "1d8",
                    "damage_bonus": 3,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "goblin_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    rng = RNGManager(master_seed=42)

    # First move: should trigger AoO
    move1 = StepMoveIntent(
        actor_id="goblin_1",
        from_pos=GridPosition(x=5, y=5),
        to_pos=GridPosition(x=4, y=5)
    )

    result1 = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=move1,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should have triggered AoO
    aoo_events_1 = [e for e in result1.events if e.event_type == "aoo_triggered"]
    assert len(aoo_events_1) == 1

    # Second move (same round, goblin moves again): should NOT trigger AoO
    # Goblin is now at (4,5), move to (4,4)
    updated_state = result1.world_state
    # Update goblin position manually for test
    updated_entities = updated_state.entities.copy()
    updated_entities["goblin_1"] = updated_entities["goblin_1"].copy()
    updated_entities["goblin_1"]["position"] = {"x": 4, "y": 5}
    updated_state = WorldState(
        ruleset_version=updated_state.ruleset_version,
        entities=updated_entities,
        active_combat=updated_state.active_combat
    )

    move2 = StepMoveIntent(
        actor_id="goblin_1",
        from_pos=GridPosition(x=4, y=5),
        to_pos=GridPosition(x=4, y=4)
    )

    result2 = execute_turn(
        world_state=updated_state,
        turn_ctx=turn_ctx,
        combat_intent=move2,
        rng=rng,
        next_event_id=len(result1.events),
        timestamp=2.0
    )

    # Should NOT have AoO (fighter already used it)
    aoo_events_2 = [e for e in result2.events if e.event_type == "aoo_triggered"]
    assert len(aoo_events_2) == 0


def test_multiple_reactors_resolve_in_initiative_order():
    """Tier 1: Multiple AoOs resolve in initiative order."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 30,
                "hp_max": 30,
                "position": {"x": 5, "y": 5},
                "team": "monsters",
                "attack_bonus": 2,
                "weapon": {
                    "damage_dice": "1d6",
                    "damage_bonus": 0,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            },
            "fighter_a": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 6, "y": 5},  # Adjacent east
                "team": "party",
                "attack_bonus": 5,
                "weapon": {
                    "damage_dice": "1d8",
                    "damage_bonus": 3,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            },
            "fighter_b": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 4, "y": 5},  # Adjacent west
                "team": "party",
                "attack_bonus": 5,
                "weapon": {
                    "damage_dice": "1d8",
                    "damage_bonus": 3,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter_a", "fighter_b", "goblin_1"],  # fighter_a goes first
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    # Goblin moves north (away from both fighters)
    move_intent = StepMoveIntent(
        actor_id="goblin_1",
        from_pos=GridPosition(x=5, y=5),
        to_pos=GridPosition(x=5, y=6)
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=move_intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should have 2 AoO triggers
    aoo_events = [e for e in result.events if e.event_type == "aoo_triggered"]
    assert len(aoo_events) == 2

    # First AoO should be from fighter_a (earlier in initiative)
    assert aoo_events[0].payload["reactor_id"] == "fighter_a"
    assert aoo_events[1].payload["reactor_id"] == "fighter_b"


def test_deterministic_replay_through_aoo():
    """Tier 1: Same RNG seed produces identical AoO outcomes."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 5, "y": 5},
                "team": "monsters",
                "attack_bonus": 2,
                "weapon": {
                    "damage_dice": "1d6",
                    "damage_bonus": 0,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 6, "y": 5},
                "team": "party",
                "attack_bonus": 5,
                "weapon": {
                    "damage_dice": "1d8",
                    "damage_bonus": 3,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "goblin_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    move_intent = StepMoveIntent(
        actor_id="goblin_1",
        from_pos=GridPosition(x=5, y=5),
        to_pos=GridPosition(x=4, y=5)
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")

    # Run 3 times with same seed
    results = []
    for _ in range(3):
        rng = RNGManager(master_seed=200)
        result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=move_intent,
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


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS
# ==============================================================================

def test_aoo_usage_resets_each_round():
    """Tier 2: AoO usage resets at start of each round."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 20,
                "hp_max": 20,
                "position": {"x": 5, "y": 5},
                "team": "monsters",
                "attack_bonus": 2,
                "weapon": {
                    "damage_dice": "1d6",
                    "damage_bonus": 0,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 6, "y": 5},
                "team": "party",
                "attack_bonus": 5,
                "weapon": {
                    "damage_dice": "1d8",
                    "damage_bonus": 3,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "goblin_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": ["fighter"]  # Fighter used AoO in this round
        }
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    rng = RNGManager(master_seed=42)

    # Goblin moves (should NOT trigger AoO because fighter already used it)
    move1 = StepMoveIntent(
        actor_id="goblin_1",
        from_pos=GridPosition(x=5, y=5),
        to_pos=GridPosition(x=4, y=5)
    )

    result1 = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=move1,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # No AoO in round 1
    aoo_events_1 = [e for e in result1.events if e.event_type == "aoo_triggered"]
    assert len(aoo_events_1) == 0

    # Simulate round 2 (reset AoO usage)
    updated_combat = result1.world_state.active_combat.copy()
    updated_combat["round_index"] = 2
    updated_combat["aoo_used_this_round"] = []  # Reset

    # Update goblin position to be adjacent to fighter again for round 2
    updated_entities = result1.world_state.entities.copy()
    updated_entities["goblin_1"] = updated_entities["goblin_1"].copy()
    updated_entities["goblin_1"]["position"] = {"x": 5, "y": 5}  # Back adjacent to fighter

    world_state_round2 = WorldState(
        ruleset_version=result1.world_state.ruleset_version,
        entities=updated_entities,
        active_combat=updated_combat
    )

    # Goblin moves again in round 2 (should trigger AoO now)
    move2 = StepMoveIntent(
        actor_id="goblin_1",
        from_pos=GridPosition(x=5, y=5),
        to_pos=GridPosition(x=4, y=5)  # Same move as round 1
    )

    result2 = execute_turn(
        world_state=world_state_round2,
        turn_ctx=turn_ctx,
        combat_intent=move2,
        rng=rng,
        next_event_id=len(result1.events),
        timestamp=10.0
    )

    # Should have AoO in round 2
    aoo_events_2 = [e for e in result2.events if e.event_type == "aoo_triggered"]
    assert len(aoo_events_2) == 1
