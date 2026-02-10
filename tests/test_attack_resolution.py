"""Tests for CP-10 attack resolution proof.

Tier 1 tests (MUST PASS):
- Deterministic replay
- Hit/miss logic correctness
- Damage application
- No direct state mutation
- Event payload completeness

Tier 2 tests (SHOULD PASS):
- RNG stream isolation
- Negative HP
- Event ID monotonicity
- JSONL serialization
"""

import pytest
import json
from aidm.core.attack_resolver import resolve_attack, apply_attack_events, parse_damage_dice
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent, Weapon


# ==============================================================================
# TIER 1: MUST-PASS TESTS
# ==============================================================================

def test_attack_resolution_deterministic_replay():
    """Tier 1: Same RNG seed must produce identical attack events and final state."""
    # Setup identical scenarios
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {"ac": 15, "hp_current": 6, "hp_max": 6},
            "pc_fighter": {"ac": 18, "hp_current": 10, "hp_max": 10}
        }
    )

    intent = AttackIntent(
        attacker_id="goblin_1",
        target_id="pc_fighter",
        attack_bonus=3,
        weapon=Weapon(damage_dice="1d6", damage_bonus=1, damage_type="slashing")
    )

    # Run 3 times with same seed
    results = []
    for _ in range(3):
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        final_state = apply_attack_events(world_state, events)
        results.append((events, final_state))

    # Verify all runs produce identical results
    first_events, first_state = results[0]
    for events, state in results[1:]:
        # Check event payloads are identical
        assert len(events) == len(first_events)
        for e1, e2 in zip(first_events, events):
            assert e1.event_type == e2.event_type
            assert e1.payload == e2.payload

        # Check final state hash is identical
        assert state.state_hash() == first_state.state_hash()


def test_attack_hits_when_roll_meets_or_exceeds_ac():
    """Tier 1: Attack should hit when total meets or exceeds target AC."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 10}  # Low AC for guaranteed hit
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=10,  # High bonus ensures hit unless natural 1
        weapon=Weapon(damage_dice="1d6", damage_bonus=2, damage_type="slashing")
    )

    # Try multiple seeds until we get a non-natural-1 hit
    for seed in range(100):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

        attack_event = events[0]
        assert attack_event.event_type == "attack_roll"

        # If not natural 1, should hit
        if not attack_event.payload["is_natural_1"]:
            assert attack_event.payload["total"] >= attack_event.payload["target_ac"]
            assert attack_event.payload["hit"] is True
            # Should have damage events
            assert len(events) > 1
            break
    else:
        pytest.fail("Could not generate non-natural-1 result in 100 seeds")


def test_attack_misses_when_roll_below_ac():
    """Tier 1: Attack should miss when total is below target AC."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 20, "hp_current": 10}  # High AC
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=0,  # Need d20=20 to hit AC 20
        weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="piercing")
    )

    # Use seed that produces low d20 roll
    rng = RNGManager(master_seed=50)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    attack_event = events[0]
    assert attack_event.event_type == "attack_roll"

    # If not natural 20, should miss
    if not attack_event.payload["is_natural_20"]:
        assert attack_event.payload["hit"] is False
        # Should only have attack_roll event (no damage)
        assert len(events) == 1


def test_natural_20_always_hits():
    """Tier 1: Natural 20 should always hit regardless of AC."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 50, "hp_current": 10}  # Impossibly high AC
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=0,
        weapon=Weapon(damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning")
    )

    # Try multiple seeds until we get a natural 20
    for seed in range(1000):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

        attack_event = events[0]
        if attack_event.payload["is_natural_20"]:
            # Natural 20 must hit
            assert attack_event.payload["hit"] is True
            # Must have damage events
            assert len(events) > 1
            break
    else:
        pytest.fail("Could not generate natural 20 in 1000 seeds")


def test_natural_1_always_misses():
    """Tier 1: Natural 1 should always miss regardless of attack bonus."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 5, "hp_current": 10}  # Very low AC
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=50,  # Huge bonus, would hit anything except nat 1
        weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="piercing")
    )

    # Try multiple seeds until we get a natural 1
    for seed in range(1000):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

        attack_event = events[0]
        if attack_event.payload["is_natural_1"]:
            # Natural 1 must miss
            assert attack_event.payload["hit"] is False
            # Should only have attack_roll event (no damage)
            assert len(events) == 1
            break
    else:
        pytest.fail("Could not generate natural 1 in 1000 seeds")


def test_damage_reduces_target_hp():
    """Tier 1: Damage should reduce target HP on hit."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 20, "hp_max": 20}
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=10,  # Will definitely hit AC 10
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
    final_state = apply_attack_events(world_state, events)

    # HP should be reduced
    assert final_state.entities["target"]["hp_current"] < 20


def test_damage_not_applied_on_miss():
    """Tier 1: Damage should not be applied when attack misses."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 30, "hp_current": 20, "hp_max": 20}  # High AC
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=0,  # Low bonus, likely to miss
        weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="piercing")
    )

    rng = RNGManager(master_seed=50)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    attack_event = events[0]
    if not attack_event.payload["hit"]:
        # No damage events should be present
        damage_events = [e for e in events if e.event_type == "damage_roll"]
        assert len(damage_events) == 0

        # HP should remain unchanged
        final_state = apply_attack_events(world_state, events)
        assert final_state.entities["target"]["hp_current"] == 20


def test_attack_events_sufficient_for_audit():
    """Tier 1: Attack events must contain all inputs to resolution logic."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 15, "hp_current": 10}
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d6", damage_bonus=2, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Check attack_roll event has all required fields
    attack_event = events[0]
    assert attack_event.event_type == "attack_roll"
    assert "d20_result" in attack_event.payload
    assert "attack_bonus" in attack_event.payload
    assert "total" in attack_event.payload
    assert "target_ac" in attack_event.payload
    assert "hit" in attack_event.payload
    assert "is_natural_20" in attack_event.payload
    assert "is_natural_1" in attack_event.payload


def test_attack_does_not_mutate_state_directly():
    """Tier 1: resolve_attack must return events only, not mutate WorldState."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 10, "hp_max": 10}
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=10,
        weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="slashing")
    )

    # Capture original state
    original_hp = world_state.entities["target"]["hp_current"]

    # Resolve attack
    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Original world state should be unchanged
    assert world_state.entities["target"]["hp_current"] == original_hp

    # Only apply_attack_events should mutate state
    final_state = apply_attack_events(world_state, events)
    if any(e.event_type == "hp_changed" for e in events):
        assert final_state.entities["target"]["hp_current"] != original_hp


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS
# ==============================================================================

def test_combat_rng_does_not_affect_policy_rng():
    """Tier 2: Combat RNG stream should be isolated from policy RNG stream."""
    # Create two scenarios with different combat results but same policy stream
    rng1 = RNGManager(master_seed=42)
    rng2 = RNGManager(master_seed=42)

    # Use combat stream in rng1
    combat_rng1 = rng1.stream("combat")
    roll1 = combat_rng1.randint(1, 20)

    # Use policy stream in both (should be identical)
    policy_rng1 = rng1.stream("policy")
    policy_rng2 = rng2.stream("policy")

    policy_roll1 = policy_rng1.randint(1, 100)
    policy_roll2 = policy_rng2.randint(1, 100)

    # Policy rolls should be identical even though combat was used in rng1
    assert policy_roll1 == policy_roll2


def test_negative_hp_recorded_when_damage_exceeds_current_hp():
    """Tier 2: Negative HP should be recorded when damage exceeds current HP."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 3, "hp_max": 10}  # Low HP
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=10,  # Will hit
        weapon=Weapon(damage_dice="2d6", damage_bonus=5, damage_type="slashing")  # High damage
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
    final_state = apply_attack_events(world_state, events)

    # If hit occurred, check HP
    if any(e.event_type == "hp_changed" for e in events):
        hp_event = [e for e in events if e.event_type == "hp_changed"][0]
        # HP should go negative
        if hp_event.payload["hp_after"] < 0:
            # Verify negative HP is recorded in final state
            assert final_state.entities["target"]["hp_current"] < 0


def test_attack_events_have_strictly_increasing_ids():
    """Tier 2: Attack events should have strictly monotonic event IDs."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 10}
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=10,
        weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="piercing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=100, timestamp=1.0)

    # Check event IDs are strictly increasing
    event_ids = [e.event_id for e in events]
    for i in range(len(event_ids) - 1):
        assert event_ids[i] < event_ids[i + 1]


def test_attack_events_serialize_to_jsonl():
    """Tier 2: Attack events should be JSON-serializable for JSONL output."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 15, "hp_current": 10}
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=2, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Verify each event can be serialized to JSON
    for event in events:
        json_str = json.dumps(event.to_dict(), sort_keys=True)
        assert json_str  # Should not raise exception
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


def test_entity_defeated_when_hp_drops_to_zero_or_below():
    """Tier 2: Entities should be marked defeated when HP <= 0."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 5, "hp_max": 10}
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=10,  # Will hit
        weapon=Weapon(damage_dice="2d6", damage_bonus=5, damage_type="slashing")  # Will likely kill
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
    final_state = apply_attack_events(world_state, events)

    # Check if entity was defeated
    if any(e.event_type == "entity_defeated" for e in events):
        # Verify hp_current <= 0
        assert final_state.entities["target"]["hp_current"] <= 0
        # Verify defeated flag is set
        assert final_state.entities["target"].get("defeated", False) is True


def test_parse_damage_dice_valid():
    """Test damage dice parser with valid inputs."""
    assert parse_damage_dice("1d6") == (1, 6)
    assert parse_damage_dice("2d8") == (2, 8)
    assert parse_damage_dice("3d10") == (3, 10)


def test_parse_damage_dice_invalid():
    """Test damage dice parser rejects invalid inputs."""
    with pytest.raises(ValueError):
        parse_damage_dice("d6")  # Missing count

    with pytest.raises(ValueError):
        parse_damage_dice("1d")  # Missing size

    with pytest.raises(ValueError):
        parse_damage_dice("1x6")  # Wrong separator

    with pytest.raises(ValueError):
        parse_damage_dice("0d6")  # Zero dice

    with pytest.raises(ValueError):
        parse_damage_dice("1d0")  # Zero die size
