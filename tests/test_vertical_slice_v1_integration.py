"""Integration tests for Vertical Slice V1 play loop.

Tests deterministic execution of 3-turn scenario with replay verification.
"""

import pytest
from aidm.core.play_loop import execute_scenario, TurnContext
from aidm.core.state import WorldState
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.core.doctrine_rules import derive_tactical_envelope


def test_vertical_slice_v1_deterministic_replay():
    """Vertical slice V1 should produce identical state hash across multiple runs."""
    # Create initial world state
    initial_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            },
            "pc_fighter": {
                "hp_current": 10,
                "hp_max": 10,
                "conditions": [],
                "position": {"x": 10, "y": 0},
                "team": "party"
            },
            "pc_wizard": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 15, "y": 5},
                "team": "party"
            }
        },
        active_combat={"turn_counter": 0}
    )

    # Create goblin doctrine
    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid"
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

    # Define turn sequence: goblin, PC, goblin
    turn_sequence = [
        TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters"),
        TurnContext(turn_index=1, actor_id="pc_fighter", actor_team="party"),
        TurnContext(turn_index=2, actor_id="goblin_1", actor_team="monsters")
    ]

    # Execute scenario 3 times
    final_states = []
    event_logs = []

    for run_index in range(3):
        final_state, event_log = execute_scenario(
            initial_state=initial_state,
            turn_sequence=turn_sequence,
            doctrines={"goblin_1": goblin_doctrine},
            initial_event_id=0,
            initial_timestamp=0.0
        )
        final_states.append(final_state)
        event_logs.append(event_log)

    # Verify all runs produce identical final state hash
    hash_run1 = final_states[0].state_hash()
    hash_run2 = final_states[1].state_hash()
    hash_run3 = final_states[2].state_hash()

    assert hash_run1 == hash_run2, "Run 1 and Run 2 produced different state hashes"
    assert hash_run2 == hash_run3, "Run 2 and Run 3 produced different state hashes"


def test_vertical_slice_v1_event_id_monotonicity():
    """Vertical slice V1 should produce strictly monotonic event IDs."""
    initial_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            },
            "pc_fighter": {
                "hp_current": 10,
                "hp_max": 10,
                "conditions": [],
                "position": {"x": 10, "y": 0},
                "team": "party"
            }
        },
        active_combat={"turn_counter": 0}
    )

    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid"
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

    turn_sequence = [
        TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters"),
        TurnContext(turn_index=1, actor_id="pc_fighter", actor_team="party")
    ]

    final_state, event_log = execute_scenario(
        initial_state=initial_state,
        turn_sequence=turn_sequence,
        doctrines={"goblin_1": goblin_doctrine}
    )

    # Verify event IDs are strictly increasing
    event_ids = [event.event_id for event in event_log.events]
    for i in range(len(event_ids) - 1):
        assert event_ids[i] < event_ids[i + 1], f"Event IDs not strictly increasing: {event_ids[i]} >= {event_ids[i + 1]}"


def test_vertical_slice_v1_turn_counter_advances():
    """Vertical slice V1 should advance turn counter in world state."""
    initial_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        },
        active_combat={"turn_counter": 0}
    )

    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid"
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

    turn_sequence = [
        TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters"),
        TurnContext(turn_index=1, actor_id="goblin_1", actor_team="monsters"),
        TurnContext(turn_index=2, actor_id="goblin_1", actor_team="monsters")
    ]

    final_state, event_log = execute_scenario(
        initial_state=initial_state,
        turn_sequence=turn_sequence,
        doctrines={"goblin_1": goblin_doctrine}
    )

    # Verify turn counter advanced to 3 (0->1->2->3)
    assert final_state.active_combat["turn_counter"] == 3


def test_vertical_slice_v1_policy_evaluation_events():
    """Vertical slice V1 should emit policy evaluation events for monsters."""
    initial_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            },
            "pc_fighter": {
                "hp_current": 10,
                "hp_max": 10,
                "conditions": [],
                "position": {"x": 10, "y": 0},
                "team": "party"
            }
        },
        active_combat={"turn_counter": 0}
    )

    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid"
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

    turn_sequence = [
        TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    ]

    final_state, event_log = execute_scenario(
        initial_state=initial_state,
        turn_sequence=turn_sequence,
        doctrines={"goblin_1": goblin_doctrine}
    )

    # Find tactic_selected event
    tactic_events = [e for e in event_log.events if e.event_type == "tactic_selected"]
    assert len(tactic_events) == 1, "Expected exactly one tactic_selected event"

    tactic_event = tactic_events[0]
    assert tactic_event.payload["actor_id"] == "goblin_1"
    assert "tactic_class" in tactic_event.payload
    assert "score" in tactic_event.payload
    assert "reasons" in tactic_event.payload
    assert len(tactic_event.citations) > 0, "tactic_selected event should have citations"


def test_vertical_slice_v1_pc_stub_events():
    """Vertical slice V1 should emit stub action events for PCs."""
    initial_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "pc_fighter": {
                "hp_current": 10,
                "hp_max": 10,
                "conditions": [],
                "position": {"x": 10, "y": 0},
                "team": "party"
            }
        },
        active_combat={"turn_counter": 0}
    )

    turn_sequence = [
        TurnContext(turn_index=0, actor_id="pc_fighter", actor_team="party")
    ]

    final_state, event_log = execute_scenario(
        initial_state=initial_state,
        turn_sequence=turn_sequence,
        doctrines={}
    )

    # Find action_declared event
    action_events = [e for e in event_log.events if e.event_type == "action_declared"]
    assert len(action_events) == 1, "Expected exactly one action_declared event"

    action_event = action_events[0]
    assert action_event.payload["actor_id"] == "pc_fighter"
    assert action_event.payload["action_type"] == "attack"
    assert len(action_event.citations) > 0, "action_declared event should have citations"
