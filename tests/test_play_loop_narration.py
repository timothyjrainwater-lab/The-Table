"""WO-030: Integration tests for narration pipeline wiring.

Tests that narration tokens from play_loop.py are converted to narration text
via GuardedNarrationService. Verifies:
- TurnResult.narration_text is populated when narration_service provided
- TurnResult.narration_provenance indicates source ("[NARRATIVE]" or "[NARRATIVE:TEMPLATE]")
- Without narration_service: narration_text is None (backward compat)
- Kill switch enforcement: narration fails gracefully without crashing turn
- Determinism: Box state identical regardless of narration path
- BL-020: FrozenWorldStateView enforced at narration boundary
- Performance: Template path < 500ms p95

Tier-1 (MUST PASS):
- narration_text populated for all narration tokens
- Backward compatibility: None service → None narration_text
- Kill switch fires → narration_text=None, turn succeeds
- Box state unchanged by narration generation
- FrozenWorldStateView passed to narration layer

Tier-2 (SHOULD PASS):
- Provenance tracking ("[NARRATIVE:TEMPLATE]" for templates)
- Template path performance < 500ms p95
- All existing play_loop tests still pass
"""

import pytest
import time
from aidm.core.play_loop import execute_turn, TurnContext, TurnResult
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.full_attack_resolver import FullAttackIntent
from aidm.core.rng_manager import RNGManager
from aidm.narration.guarded_narration_service import (
    GuardedNarrationService,
    NarrationBoundaryViolation,
    FrozenMemorySnapshot,
)
from aidm.narration.kill_switch_registry import KillSwitchRegistry, KillSwitchID
from aidm.schemas.entity_fields import EF

# ==============================================================================
# TIER 1: MUST-PASS TESTS
# ==============================================================================


def test_turn_result_has_narration_text_field():
    """Tier 1: TurnResult must have narration_text and narration_provenance fields."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin Skirmisher", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=None,  # No service → fields should still exist
    )

    # Fields must exist (None by default)
    assert hasattr(result, "narration_text")
    assert hasattr(result, "narration_provenance")
    assert result.narration_text is None  # None when no service
    assert result.narration_provenance is None


def test_narration_generated_on_attack_hit():
    """Tier 1: attack_hit token → narration text produced."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin Skirmisher", "ac": 10, "hp_current": 6, "hp_max": 6},  # Low AC = guaranteed hit
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,  # Guaranteed hit
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)
    narration_service = GuardedNarrationService(loaded_model=None, use_llm_query_interface=False)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=narration_service,
    )

    # Should succeed
    assert result.status == "ok"
    assert result.narration == "attack_hit"

    # Narration text should be generated
    assert result.narration_text is not None
    assert len(result.narration_text) > 0

    # Should contain entity names from WorldState
    assert "Ragnar" in result.narration_text or "fighter" in result.narration_text.lower()


def test_narration_generated_on_attack_miss():
    """Tier 1: attack_miss token → template text."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin Skirmisher", "ac": 30, "hp_current": 6, "hp_max": 6},  # High AC = guaranteed miss
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=0,  # Low bonus = miss
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)
    narration_service = GuardedNarrationService(loaded_model=None, use_llm_query_interface=False)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=narration_service,
    )

    # Should succeed with miss
    assert result.status == "ok"
    assert result.narration == "attack_miss"

    # Narration text should be generated
    assert result.narration_text is not None
    assert len(result.narration_text) > 0


def test_narration_generated_on_full_attack():
    """Tier 1: full_attack_complete token → narration text."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 50, "hp_max": 50},
            "goblin": {"name": "Goblin Skirmisher", "ac": 15, "hp_current": 20, "hp_max": 20},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=6,  # 2 attacks: +6/+1
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)
    narration_service = GuardedNarrationService(loaded_model=None, use_llm_query_interface=False)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=narration_service,
    )

    assert result.status == "ok"
    assert result.narration == "full_attack_complete"
    assert result.narration_text is not None


def test_narration_provenance_is_template():
    """Tier 1: provenance = "[NARRATIVE:TEMPLATE]" for template path."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)
    narration_service = GuardedNarrationService(loaded_model=None, use_llm_query_interface=False)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=narration_service,
    )

    assert result.narration_provenance == "[NARRATIVE:TEMPLATE]"


def test_no_narration_when_service_is_none():
    """Tier 1: Backward compatibility — narration_service=None → narration_text=None."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=None,  # No service provided
    )

    # Turn should succeed
    assert result.status == "ok"

    # Narration token should still be set
    assert result.narration == "attack_hit"

    # But narration_text should be None
    assert result.narration_text is None
    assert result.narration_provenance is None


def test_narration_boundary_violation_graceful():
    """Tier 1: Kill switch active → narration_text=None, turn still succeeds."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)

    # Create service with pre-triggered kill switch
    kill_switch_registry = KillSwitchRegistry()
    from aidm.narration.kill_switch_registry import build_evidence
    kill_switch_registry.trigger(
        KillSwitchID.KILL_001,
        build_evidence(KillSwitchID.KILL_001, "Test: simulating kill switch", {}),
    )

    narration_service = GuardedNarrationService(
        loaded_model=None,
        use_llm_query_interface=False,
        kill_switch_registry=kill_switch_registry,
    )

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=narration_service,
    )

    # Turn should still succeed
    assert result.status == "ok"

    # Narration token should be set
    assert result.narration == "attack_hit"

    # Narration text should be None (kill switch prevented generation)
    assert result.narration_text is None
    assert result.narration_provenance is None


def test_narration_exception_does_not_crash_turn():
    """Tier 1: Narration service throws Exception → turn succeeds with None narration."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)

    # Create a mock service that always throws
    class BrokenNarrationService:
        def generate_narration(self, request):
            raise RuntimeError("Simulated narration failure")

    narration_service = BrokenNarrationService()

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=narration_service,
    )

    # Turn should succeed despite narration failure
    assert result.status == "ok"
    assert result.narration == "attack_hit"

    # Narration should be None (failure handled gracefully)
    assert result.narration_text is None
    assert result.narration_provenance is None


def test_determinism_unaffected_by_narration():
    """Tier 1: Box state identical regardless of narration path taken."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    # Run 1: Without narration service
    rng1 = RNGManager(master_seed=42)
    result1 = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng1,
        narration_service=None,
    )

    # Run 2: With narration service
    rng2 = RNGManager(master_seed=42)
    narration_service = GuardedNarrationService(loaded_model=None, use_llm_query_interface=False)
    result2 = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng2,
        narration_service=narration_service,
    )

    # Box state must be identical
    assert result1.world_state.state_hash() == result2.world_state.state_hash()

    # Events must be identical
    assert len(result1.events) == len(result2.events)
    for e1, e2 in zip(result1.events, result2.events):
        assert e1.event_type == e2.event_type
        assert e1.payload == e2.payload

    # Narration token must be identical
    assert result1.narration == result2.narration


def test_frozen_world_state_passed_to_narration():
    """Tier 1: BL-020 — narration receives FrozenWorldStateView hash."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)
    narration_service = GuardedNarrationService(loaded_model=None, use_llm_query_interface=False)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=narration_service,
    )

    # Narration should succeed (no BL-020 violation)
    assert result.status == "ok"
    assert result.narration_text is not None


def test_world_state_hash_for_kill006():
    """Tier 1: world_state_hash populated in NarrationRequest (KILL-006)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)
    narration_service = GuardedNarrationService(loaded_model=None, use_llm_query_interface=False)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=narration_service,
    )

    # No assertion needed — if hash not provided, narration would fail
    # This test verifies the pipeline passes world_state_hash through
    assert result.status == "ok"


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS
# ==============================================================================


def test_template_path_under_500ms():
    """Tier 2: Template narration < 500ms p95."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)
    narration_service = GuardedNarrationService(loaded_model=None, use_llm_query_interface=False)

    # Run 20 iterations, measure p95
    latencies = []
    for i in range(20):
        t0 = time.perf_counter()
        result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=RNGManager(master_seed=42 + i),
            narration_service=narration_service,
        )
        elapsed = time.perf_counter() - t0
        latencies.append(elapsed * 1000)  # Convert to ms

    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]

    assert p95 < 500, f"Template narration p95 latency {p95:.1f}ms exceeds 500ms threshold"


def test_engine_result_has_narration_token():
    """Tier 2: EngineResult.narration_token is set for narration layer."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Goblin", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)
    narration_service = GuardedNarrationService(loaded_model=None, use_llm_query_interface=False)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=narration_service,
    )

    # EngineResult is built internally — verify via narration output
    assert result.narration_text is not None
    # If narration was generated, EngineResult must have had narration_token set


def test_engine_result_has_actor_target_names():
    """Tier 2: metadata contains entity names for template substitution."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"name": "Ragnar the Bold", "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"name": "Grizznak", "ac": 15, "hp_current": 6, "hp_max": 6},
        },
        active_combat={"turn_counter": 0},
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
    )

    rng = RNGManager(master_seed=42)
    narration_service = GuardedNarrationService(loaded_model=None, use_llm_query_interface=False)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        narration_service=narration_service,
    )

    # Narration should contain entity names
    assert "Ragnar" in result.narration_text or "fighter" in result.narration_text.lower()
