"""Integration tests for CP-14 initiative and action economy.

Tests initiative rolling, ordering, round progression, flat-footed state,
and deterministic replay.

Tier-1 (MUST PASS):
- Initiative rolls are deterministic
- Initiative ordering follows tie-breaking rules
- Flat-footed clears after first action
- Combat rounds progress correctly
- Backward compatibility with CP-09/CP-12

Tier-2 (SHOULD PASS):
- Multiple rounds with state persistence
- Actors with identical initiative + Dex
- Empty initiative order handling
"""

import pytest
from aidm.core.initiative import roll_initiative, sort_initiative_order, roll_initiative_for_all_actors, InitiativeRoll
from aidm.core.combat_controller import start_combat, execute_combat_round
from aidm.core.play_loop import TurnContext, execute_turn
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.schemas.attack import Weapon
from aidm.core.doctrine_rules import derive_tactical_envelope


# ==============================================================================
# TIER 1: MUST-PASS TESTS
# ==============================================================================

def test_initiative_roll_deterministic():
    """Tier 1: Same RNG seed → identical initiative rolls."""
    rng1 = RNGManager(master_seed=42)
    rng2 = RNGManager(master_seed=42)

    roll1 = roll_initiative("fighter", dex_modifier=2, rng=rng1)
    roll2 = roll_initiative("fighter", dex_modifier=2, rng=rng2)

    assert roll1.d20_roll == roll2.d20_roll
    assert roll1.total == roll2.total


def test_initiative_ordering_by_total():
    """Tier 1: Higher initiative total comes first."""
    rolls = [
        InitiativeRoll("fighter", d20_roll=15, dex_modifier=2, misc_modifier=0, total=17),
        InitiativeRoll("wizard", d20_roll=10, dex_modifier=3, misc_modifier=0, total=13),
        InitiativeRoll("goblin", d20_roll=18, dex_modifier=1, misc_modifier=0, total=19)
    ]

    order = sort_initiative_order(rolls)

    assert order == ["goblin", "fighter", "wizard"]


def test_initiative_ordering_tie_break_by_dex():
    """Tier 1: Same initiative total → higher Dex modifier wins."""
    rolls = [
        InitiativeRoll("fighter", d20_roll=10, dex_modifier=2, misc_modifier=0, total=12),
        InitiativeRoll("wizard", d20_roll=9, dex_modifier=3, misc_modifier=0, total=12),
        InitiativeRoll("rogue", d20_roll=8, dex_modifier=4, misc_modifier=0, total=12)
    ]

    order = sort_initiative_order(rolls)

    # All have total=12, sort by Dex: rogue(4) > wizard(3) > fighter(2)
    assert order == ["rogue", "wizard", "fighter"]


def test_initiative_ordering_tie_break_by_actor_id():
    """Tier 1: Same initiative total and Dex → lexicographic actor_id wins."""
    rolls = [
        InitiativeRoll("goblin_2", d20_roll=10, dex_modifier=2, misc_modifier=0, total=12),
        InitiativeRoll("goblin_1", d20_roll=10, dex_modifier=2, misc_modifier=0, total=12),
        InitiativeRoll("goblin_3", d20_roll=10, dex_modifier=2, misc_modifier=0, total=12)
    ]

    order = sort_initiative_order(rolls)

    # All have total=12 and dex=2, sort lexicographically
    assert order == ["goblin_1", "goblin_2", "goblin_3"]


def test_start_combat_emits_correct_events():
    """Tier 1: start_combat emits combat_started and initiative_rolled events."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6}
        }
    )

    actors = [("fighter", 2), ("goblin", 1)]
    rng = RNGManager(master_seed=42)

    updated_state, events, next_id = start_combat(world_state, actors, rng, next_event_id=0, timestamp=1.0)

    # Should have combat_started + 2 initiative_rolled events
    event_types = [e.event_type for e in events]
    assert "combat_started" in event_types
    assert event_types.count("initiative_rolled") == 2

    # Should initialize active_combat
    assert updated_state.active_combat is not None
    assert "initiative_order" in updated_state.active_combat
    assert len(updated_state.active_combat["initiative_order"]) == 2


def test_flat_footed_clears_after_first_action():
    """Tier 1: Flat-footed flag clears after actor's first successful action."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "position": {"x": 0, "y": 0},
                "team": "monsters",
                "conditions": []
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 5, "y": 0},
                "team": "party"
            }
        }
    )

    actors = [("goblin_1", 1), ("fighter", 2)]
    rng = RNGManager(master_seed=42)

    # Start combat
    world_state, start_events, next_id = start_combat(world_state, actors, rng, next_event_id=0, timestamp=1.0)

    # All actors should be flat-footed initially
    assert "goblin_1" in world_state.active_combat["flat_footed_actors"]
    assert "fighter" in world_state.active_combat["flat_footed_actors"]

    # Get initiative order to know who acts first
    initiative_order = world_state.active_combat["initiative_order"]

    # Create goblin doctrine with combat parameters
    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="slashing"),
        attack_bonus=2,
        citations=[{"source_id": "e390dfd9143f", "page": 133}]
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

    # Execute one round
    round_result = execute_combat_round(
        world_state=world_state,
        doctrines={"goblin_1": goblin_doctrine},
        rng=rng,
        next_event_id=next_id,
        timestamp=10.0
    )

    # Check if flat_footed_cleared events were emitted
    flat_footed_events = [e for e in round_result.events if e.event_type == "flat_footed_cleared"]

    # Should have at least one flat-footed cleared event (first actor to act)
    assert len(flat_footed_events) > 0

    # First flat-footed clear should be for first actor in initiative order
    first_actor = initiative_order[0]
    assert flat_footed_events[0].payload["actor_id"] == first_actor

    # That actor should no longer be flat-footed
    assert first_actor not in round_result.world_state.active_combat.get("flat_footed_actors", [])


def test_combat_round_progresses_initiative_order():
    """Tier 1: Combat round executes turns in correct initiative order."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "position": {"x": 0, "y": 0},
                "team": "monsters",
                "conditions": []
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 5, "y": 0},
                "team": "party"
            }
        }
    )

    actors = [("goblin_1", 1), ("fighter", 2)]
    rng = RNGManager(master_seed=42)

    # Start combat
    world_state, start_events, next_id = start_combat(world_state, actors, rng, next_event_id=0, timestamp=1.0)

    # Get initiative order
    initiative_order = world_state.active_combat["initiative_order"]

    # Execute one round
    round_result = execute_combat_round(
        world_state=world_state,
        doctrines={},
        rng=rng,
        next_event_id=next_id,
        timestamp=10.0
    )

    # Should have turn_start events in initiative order
    turn_start_events = [e for e in round_result.events if e.event_type == "turn_start"]
    turn_actor_ids = [e.payload["actor_id"] for e in turn_start_events]

    assert turn_actor_ids == initiative_order


def test_deterministic_replay_through_combat_round():
    """Tier 1: Same RNG seed → identical events through full combat round."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "position": {"x": 0, "y": 0},
                "team": "monsters",
                "conditions": []
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 5, "y": 0},
                "team": "party"
            }
        }
    )

    actors = [("goblin_1", 1), ("fighter", 2)]

    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="slashing"),
        attack_bonus=2,
        citations=[{"source_id": "e390dfd9143f", "page": 133}]
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

    # Run 3 times with same seed
    results = []
    for _ in range(3):
        rng = RNGManager(master_seed=100)

        # Start combat
        state, start_events, next_id = start_combat(world_state, actors, rng, next_event_id=0, timestamp=1.0)

        # Execute one round
        round_result = execute_combat_round(
            world_state=state,
            doctrines={"goblin_1": goblin_doctrine},
            rng=rng,
            next_event_id=next_id,
            timestamp=10.0
        )

        results.append(round_result)

    # All final states should be identical
    first_result = results[0]
    for result in results[1:]:
        assert result.world_state.state_hash() == first_result.world_state.state_hash()

        # Event payloads should be identical
        assert len(result.events) == len(first_result.events)
        for e1, e2 in zip(first_result.events, result.events):
            assert e1.event_type == e2.event_type
            assert e1.payload == e2.payload


def test_backward_compatibility_with_cp09_execute_turn():
    """Tier 1: CP-09 manual turn execution still works (no initiative)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "position": {"x": 0, "y": 0},
                "team": "monsters",
                "conditions": []
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 5, "y": 0},
                "team": "party"
            }
        }
    )

    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="slashing"),
        attack_bonus=2,
        citations=[{"source_id": "e390dfd9143f", "page": 133}]
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

    turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    rng = RNGManager(master_seed=42)

    # Execute turn WITHOUT combat controller (CP-09 style)
    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        doctrine=goblin_doctrine,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should succeed with no errors
    assert result.status == "ok"
    assert len(result.events) > 0


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS
# ==============================================================================

def test_multiple_combat_rounds_with_state_persistence():
    """Tier 2: Multiple rounds should maintain state correctly."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "position": {"x": 0, "y": 0},
                "team": "monsters",
                "conditions": []
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 5, "y": 0},
                "team": "party"
            }
        }
    )

    actors = [("goblin_1", 1), ("fighter", 2)]
    rng = RNGManager(master_seed=42)

    # Start combat
    world_state, start_events, next_id = start_combat(world_state, actors, rng, next_event_id=0, timestamp=1.0)

    # Execute 3 rounds
    for expected_round in [1, 2, 3]:
        round_result = execute_combat_round(
            world_state=world_state,
            doctrines={},
            rng=rng,
            next_event_id=next_id,
            timestamp=10.0 * expected_round
        )

        # Check round index
        assert round_result.round_index == expected_round
        assert round_result.world_state.active_combat["round_index"] == expected_round

        # Update state and event ID for next round
        world_state = round_result.world_state
        next_id += len(round_result.events)


def test_initiative_with_misc_modifiers():
    """Tier 2: Misc modifiers affect initiative totals."""
    rng = RNGManager(master_seed=42)

    actors = [("fighter", 2), ("wizard", 3)]
    misc_modifiers = {"fighter": 4}  # Improved Initiative feat

    rolls, order = roll_initiative_for_all_actors(actors, rng, misc_modifiers)

    # Find fighter's roll
    fighter_roll = next(r for r in rolls if r.actor_id == "fighter")

    # Should have misc modifier applied
    assert fighter_roll.misc_modifier == 4
    assert fighter_roll.total == fighter_roll.d20_roll + 2 + 4
