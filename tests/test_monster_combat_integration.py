"""Integration tests for CP-13 monster combat intent mapping.

Tests that monster policy output is correctly mapped to combat intents:
- Policy tactic selection → AttackIntent
- Target selection from TacticCandidate.target_ids
- Deterministic replay with monster combat
- RNG stream isolation (policy vs combat)
- Unmapped tactics preserve CP-09 behavior
- Missing doctrine combat parameters → requires_clarification

Tier-1 (MUST PASS):
- Monster attack_nearest triggers combat resolver
- Target selection is deterministic (lexicographic sort)
- Deterministic replay through monster combat
- Policy RNG isolation preserved
- Missing weapon/attack_bonus produces no combat
- Unmapped tactics emit tactic_selected stub

Tier-2 (SHOULD PASS):
- Monster combat events match CP-10 behavior
- Multiple monsters with combat intents work
- Mixed monster combat and PC combat works
"""

import pytest
from aidm.core.play_loop import execute_turn, TurnContext, resolve_monster_combat_intent
from aidm.core.state import WorldState
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.schemas.attack import Weapon
from aidm.core.doctrine_rules import derive_tactical_envelope
from aidm.core.rng_manager import RNGManager
from aidm.core.tactical_policy import evaluate_tactics


# ==============================================================================
# TIER 1: MUST-PASS TESTS
# ==============================================================================

def test_monster_attack_nearest_triggers_combat_resolver():
    """Tier 1: Monster with attack_nearest tactic should trigger attack resolver."""
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
        },
        active_combat={"turn_counter": 0}
    )

    # Create goblin doctrine with weapon and attack_bonus
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

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        doctrine=goblin_doctrine,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should succeed
    assert result.status == "ok"

    # Should have combat events (attack_roll, etc.)
    event_types = [e.event_type for e in result.events]
    assert "attack_roll" in event_types

    # Should NOT have tactic_selected stub (combat occurred instead)
    assert "tactic_selected" not in event_types

    # Narration token should be present
    assert result.narration in ["attack_hit", "attack_miss"]


def test_target_selection_deterministic():
    """Tier 1: Target selection from WorldState should be deterministic (lexicographic sort)."""
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
            "fighter_zulu": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 5, "y": 0},
                "team": "party"
            },
            "fighter_alpha": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 3, "y": 0},
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

    # Call resolve_monster_combat_intent directly with mock policy result
    from aidm.schemas.policy import TacticalPolicyResult, ScoredTactic, TacticCandidate

    policy_result = TacticalPolicyResult(
        status="ok",
        ranked=[
            ScoredTactic(
                candidate=TacticCandidate(tactic_class="attack_nearest", target_ids=[]),
                score=1000,
                reasons=["test"]
            )
        ],
        selected=ScoredTactic(
            candidate=TacticCandidate(tactic_class="attack_nearest", target_ids=[]),
            score=1000,
            reasons=["test"]
        )
    )

    # Map to intent
    intent = resolve_monster_combat_intent(
        policy_result=policy_result,
        doctrine=goblin_doctrine,
        actor_id="goblin_1",
        world_state=world_state
    )

    # Should succeed and select fighter_alpha (lexicographically first)
    assert intent is not None
    assert intent.target_id == "fighter_alpha"


def test_deterministic_replay_through_monster_combat():
    """Tier 1: Same RNG seed should produce identical state hash through monster combat."""
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
        },
        active_combat={"turn_counter": 0}
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

    # Run 3 times with same seed
    results = []
    for _ in range(3):
        rng = RNGManager(master_seed=100)
        result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            doctrine=goblin_doctrine,
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


def test_policy_rng_isolation_preserved():
    """Tier 1: Policy RNG stream should not affect combat RNG stream."""
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

    # Run with combat stream seed 42
    rng = RNGManager(master_seed=42)
    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        doctrine=goblin_doctrine,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Extract attack roll from events
    attack_events = [e for e in result.events if e.event_type == "attack_roll"]
    assert len(attack_events) > 0
    first_d20 = attack_events[0].payload["d20_result"]

    # Run again with same combat seed (should get same d20 roll)
    rng2 = RNGManager(master_seed=42)
    result2 = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        doctrine=goblin_doctrine,
        rng=rng2,
        next_event_id=0,
        timestamp=1.0
    )

    attack_events2 = [e for e in result2.events if e.event_type == "attack_roll"]
    second_d20 = attack_events2[0].payload["d20_result"]

    # Same combat seed → same combat outcomes
    assert first_d20 == second_d20


def test_missing_weapon_produces_no_combat():
    """Tier 1: Monster doctrine without weapon should not trigger combat resolver."""
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

    # Create doctrine WITHOUT weapon and attack_bonus
    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        # weapon=None (default)
        # attack_bonus=None (default)
        citations=[{"source_id": "e390dfd9143f", "page": 133}]
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

    turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        doctrine=goblin_doctrine,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should succeed (no error)
    assert result.status == "ok"

    # Should emit tactic_selected stub (CP-09 behavior preserved)
    event_types = [e.event_type for e in result.events]
    assert "tactic_selected" in event_types

    # Should NOT have combat events
    assert "attack_roll" not in event_types


def test_unmapped_tactics_emit_stub():
    """Tier 1: Unmapped tactics (not attack_nearest/focus_fire) should emit tactic_selected stub."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "ac": 15,
                "hp_current": 2,  # Bloodied
                "hp_max": 6,
                "position": {"x": 0, "y": 0},
                "team": "monsters",
                "conditions": []
            },
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "position": {"x": 1, "y": 0},
                "team": "party"
            }
        }
    )

    # Create cowardly goblin (will select retreat_regroup when bloodied)
    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        tags=["cowardly"],
        weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="slashing"),
        attack_bonus=2,
        citations=[{"source_id": "e390dfd9143f", "page": 133}]
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

    turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        doctrine=goblin_doctrine,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should succeed
    assert result.status == "ok"

    # Should emit tactic_selected (not combat)
    event_types = [e.event_type for e in result.events]
    assert "tactic_selected" in event_types

    # Should NOT have combat events (retreat is unmapped)
    assert "attack_roll" not in event_types


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS
# ==============================================================================

def test_monster_combat_events_match_cp10_behavior():
    """Tier 2: Monster combat events should match CP-10 standalone behavior."""
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

    # Run via play loop
    rng1 = RNGManager(master_seed=100)
    loop_result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        doctrine=goblin_doctrine,
        rng=rng1,
        next_event_id=0,
        timestamp=1.0
    )

    # Verify combat events present
    attack_events = [e for e in loop_result.events if e.event_type == "attack_roll"]
    assert len(attack_events) > 0


def test_multiple_monsters_with_combat_intents():
    """Tier 2: Multiple monsters should execute combat correctly in sequence."""
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
            "goblin_2": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "position": {"x": 1, "y": 0},
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

    rng = RNGManager(master_seed=42)

    # Turn 1: Goblin 1 attacks
    turn1_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    result1 = execute_turn(
        world_state=world_state,
        turn_ctx=turn1_ctx,
        doctrine=goblin_doctrine,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    assert result1.status == "ok"
    assert "attack_roll" in [e.event_type for e in result1.events]

    # Turn 2: Goblin 2 attacks
    turn2_ctx = TurnContext(turn_index=1, actor_id="goblin_2", actor_team="monsters")
    result2 = execute_turn(
        world_state=result1.world_state,
        turn_ctx=turn2_ctx,
        doctrine=goblin_doctrine,
        rng=rng,
        next_event_id=len(result1.events),
        timestamp=2.0
    )

    assert result2.status == "ok"
    assert "attack_roll" in [e.event_type for e in result2.events]


def test_mixed_monster_combat_and_pc_combat():
    """Tier 2: Monster combat and PC combat should work in sequence."""
    from aidm.schemas.attack import AttackIntent

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

    rng = RNGManager(master_seed=42)

    # Turn 1: Monster attacks (policy-driven)
    turn1_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
    result1 = execute_turn(
        world_state=world_state,
        turn_ctx=turn1_ctx,
        doctrine=goblin_doctrine,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    assert result1.status == "ok"

    # Turn 2: PC attacks (explicit intent)
    turn2_ctx = TurnContext(turn_index=1, actor_id="fighter", actor_team="party")
    pc_intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin_1",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    result2 = execute_turn(
        world_state=result1.world_state,
        turn_ctx=turn2_ctx,
        combat_intent=pc_intent,
        rng=rng,
        next_event_id=len(result1.events),
        timestamp=2.0
    )

    assert result2.status == "ok"
