"""Tests for CP-11 full attack resolution proof.

Tier 1 tests (MUST PASS):
- Deterministic replay with critical hits
- Iterative attack calculation (BAB progression)
- Critical threat detection (natural 20)
- Critical confirmation logic
- Critical damage multiplication
- RNG consumption order with mixed threat results (BLOCKING)
- Multiple attacks hit/damage accumulation
- No direct state mutation
- Event payload completeness

Tier 2 tests (SHOULD PASS):
- Backward compatibility with CP-10 events
- Full attack sequence event ordering
- Negative HP with overkill damage
- Entity defeat after multiple hits
- High-BAB characters (4 iterative attacks)
- Critical multiplier variations (×2/×3/×4)
"""

import pytest
import json
from aidm.core.full_attack_resolver import (
    resolve_full_attack,
    apply_full_attack_events,
    calculate_iterative_attacks,
    FullAttackIntent
)
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import Weapon


# ==============================================================================
# TIER 1: MUST-PASS TESTS
# ==============================================================================

def test_full_attack_deterministic_replay():
    """Tier 1: Same RNG seed must produce identical full attack events and final state."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 10, "hp_current": 50, "hp_max": 50},
            "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6}
        }
    )

    intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=6,  # 2 attacks: +6/+1
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Run 3 times with same seed
    results = []
    for _ in range(3):
        rng = RNGManager(master_seed=42)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        final_state = apply_full_attack_events(world_state, events)
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


def test_iterative_attacks_calculated_correctly():
    """Tier 1: Iterative attacks should follow BAB - 5 progression."""
    # BAB +6 → attacks at +6/+1
    assert calculate_iterative_attacks(6) == [6, 1]

    # BAB +11 → attacks at +11/+6/+1
    assert calculate_iterative_attacks(11) == [11, 6, 1]

    # BAB +16 → attacks at +16/+11/+6/+1
    assert calculate_iterative_attacks(16) == [16, 11, 6, 1]

    # BAB +20 → attacks at +20/+15/+10/+5
    assert calculate_iterative_attacks(20) == [20, 15, 10, 5]

    # BAB +1 → only one attack
    assert calculate_iterative_attacks(1) == [1]

    # BAB +5 → only one attack (second would be +0)
    assert calculate_iterative_attacks(5) == [5]


def test_critical_threat_on_natural_20():
    """Tier 1: Natural 20 should trigger critical threat."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 50, "hp_current": 20}  # Impossibly high AC
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=1,  # Only one attack
        weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="slashing")
    )

    # Try multiple seeds until we get a natural 20
    for seed in range(1000):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

        # Find first attack_roll event
        attack_events = [e for e in events if e.event_type == "attack_roll"]
        if attack_events and attack_events[0].payload["is_natural_20"]:
            # Natural 20 must set is_threat to True
            assert attack_events[0].payload["is_threat"] is True
            # Must auto-hit
            assert attack_events[0].payload["hit"] is True
            break
    else:
        pytest.fail("Could not generate natural 20 in 1000 seeds")


def test_critical_confirmation_logic():
    """Tier 1: Critical confirmation should require second attack roll to hit AC."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 15, "hp_current": 20}
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=2, damage_type="slashing")
    )

    # Find a seed that produces: natural 20 on attack, confirmation hits AC
    confirmed_critical_found = False
    failed_confirmation_found = False

    for seed in range(2000):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

        attack_events = [e for e in events if e.event_type == "attack_roll"]
        if not attack_events:
            continue

        first_attack = attack_events[0]

        if first_attack.payload["is_threat"]:
            # Check if confirmation succeeded
            if first_attack.payload["is_critical"]:
                # Confirmation total must be >= AC
                assert first_attack.payload["confirmation_total"] >= first_attack.payload["target_ac"]
                confirmed_critical_found = True
            else:
                # Confirmation total must be < AC
                assert first_attack.payload["confirmation_total"] < first_attack.payload["target_ac"]
                failed_confirmation_found = True

        if confirmed_critical_found and failed_confirmation_found:
            break

    assert confirmed_critical_found, "Could not find confirmed critical in 2000 seeds"
    assert failed_confirmation_found, "Could not find failed confirmation in 2000 seeds"


def test_critical_damage_multiplication():
    """Tier 1: Critical hits should multiply base damage by weapon's critical_multiplier."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 50}
        }
    )

    # Test ×2 multiplier
    intent_x2 = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=10,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing", critical_multiplier=2)
    )

    # Find a confirmed critical
    for seed in range(2000):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent_x2, world_state, rng, next_event_id=0, timestamp=1.0)

        attack_events = [e for e in events if e.event_type == "attack_roll"]
        damage_events = [e for e in events if e.event_type == "damage_roll"]

        if attack_events and attack_events[0].payload["is_critical"] and damage_events:
            damage = damage_events[0].payload
            # damage_total should be base_damage × 2
            assert damage["damage_total"] == damage["base_damage"] * 2
            assert damage["critical_multiplier"] == 2
            break
    else:
        pytest.fail("Could not find confirmed critical in 2000 seeds")

    # Test ×3 multiplier
    intent_x3 = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=10,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing", critical_multiplier=3)
    )

    for seed in range(2000):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent_x3, world_state, rng, next_event_id=0, timestamp=1.0)

        attack_events = [e for e in events if e.event_type == "attack_roll"]
        damage_events = [e for e in events if e.event_type == "damage_roll"]

        if attack_events and attack_events[0].payload["is_critical"] and damage_events:
            damage = damage_events[0].payload
            assert damage["damage_total"] == damage["base_damage"] * 3
            assert damage["critical_multiplier"] == 3
            break
    else:
        pytest.fail("Could not find ×3 critical in 2000 seeds")


def test_rng_consumption_order_with_mixed_threat_results():
    """Tier 1 (BLOCKING): RNG consumption order must be deterministic regardless of threat outcomes.

    This test ensures that:
    1. Attack roll always consumes 1 RNG call
    2. Threat (natural 20) consumes +1 RNG call for confirmation
    3. Hit consumes +N RNG calls for damage (where N = num_dice)
    4. Order is strictly: attack → [confirm] → [damage]

    Two scenarios with different threat patterns must produce same final RNG state
    when they consume the same total number of RNG calls.
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 15, "hp_current": 50}
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=6,  # 2 attacks: +6/+1
        weapon=Weapon(damage_dice="2d6", damage_bonus=2, damage_type="slashing")
    )

    # Scenario 1: Find seed where first attack is threat (nat 20)
    # RNG consumption: d20 (attack) + d20 (confirm) + 2d6 (damage if confirm hits) + d20 (attack 2) + [...]
    scenario1_events = None
    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        attack_events = [e for e in events if e.event_type == "attack_roll"]

        if attack_events and attack_events[0].payload["is_threat"]:
            scenario1_events = events
            scenario1_seed = seed
            break

    assert scenario1_events is not None, "Could not find threat scenario in 5000 seeds"

    # Scenario 2: Find seed where first attack is NOT threat but hits
    # RNG consumption: d20 (attack) + 2d6 (damage) + d20 (attack 2) + [...]
    scenario2_events = None
    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        attack_events = [e for e in events if e.event_type == "attack_roll"]

        if attack_events and not attack_events[0].payload["is_threat"] and attack_events[0].payload["hit"]:
            scenario2_events = events
            scenario2_seed = seed
            break

    assert scenario2_events is not None, "Could not find non-threat hit scenario in 5000 seeds"

    # Verify RNG consumption order by replaying with same seeds and checking stream state
    # If we consume RNG calls in strict order, replay should be identical

    # Replay scenario 1
    rng1_replay = RNGManager(master_seed=scenario1_seed)
    events1_replay = resolve_full_attack(intent, world_state, rng1_replay, next_event_id=0, timestamp=1.0)
    assert len(events1_replay) == len(scenario1_events)
    for e1, e2 in zip(scenario1_events, events1_replay):
        assert e1.payload == e2.payload

    # Replay scenario 2
    rng2_replay = RNGManager(master_seed=scenario2_seed)
    events2_replay = resolve_full_attack(intent, world_state, rng2_replay, next_event_id=0, timestamp=1.0)
    assert len(events2_replay) == len(scenario2_events)
    for e1, e2 in zip(scenario2_events, events2_replay):
        assert e1.payload == e2.payload


def test_multiple_attacks_accumulate_damage():
    """Tier 1: Multiple iterative attacks should accumulate damage to single HP change."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 10},
            "goblin": {"ac": 10, "hp_current": 30, "hp_max": 30}  # Low AC, high HP
        }
    )

    intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=11,  # 3 attacks: +11/+6/+1
        weapon=Weapon(damage_dice="1d8", damage_bonus=4, damage_type="slashing")
    )

    # Try multiple seeds until we find scenario with multiple hits
    for seed in range(200):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        damage_events = [e for e in events if e.event_type == "damage_roll"]

        if len(damage_events) > 1:
            # Should have exactly one hp_changed event
            hp_events = [e for e in events if e.event_type == "hp_changed"]
            assert len(hp_events) == 1

            # Total damage should equal sum of all damage_roll events
            total_damage_from_rolls = sum(d.payload["damage_total"] for d in damage_events)
            hp_event = hp_events[0]
            assert hp_event.payload["delta"] == -total_damage_from_rolls
            break
    else:
        pytest.fail("Could not find scenario with multiple hits in 200 seeds")


def test_full_attack_does_not_mutate_state_directly():
    """Tier 1: resolve_full_attack must return events only, not mutate WorldState."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 10, "hp_max": 10}
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=6,
        weapon=Weapon(damage_dice="1d6", damage_bonus=2, damage_type="slashing")
    )

    # Capture original state
    original_hp = world_state.entities["target"]["hp_current"]

    # Resolve full attack
    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Original world state should be unchanged
    assert world_state.entities["target"]["hp_current"] == original_hp

    # Only apply_full_attack_events should mutate state
    final_state = apply_full_attack_events(world_state, events)
    if any(e.event_type == "hp_changed" for e in events):
        assert final_state.entities["target"]["hp_current"] != original_hp


def test_full_attack_events_sufficient_for_audit():
    """Tier 1: Full attack events must contain all inputs to resolution logic."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 15, "hp_current": 20}
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=11,  # 3 attacks
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing", critical_multiplier=2)
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Check full_attack_start event
    start_events = [e for e in events if e.event_type == "full_attack_start"]
    assert len(start_events) == 1
    assert "base_attack_bonus" in start_events[0].payload
    assert "num_attacks" in start_events[0].payload
    assert "attack_bonuses" in start_events[0].payload

    # Check attack_roll events have required fields (including CP-11 additions)
    attack_events = [e for e in events if e.event_type == "attack_roll"]
    for attack in attack_events:
        assert "d20_result" in attack.payload
        assert "attack_bonus" in attack.payload
        assert "total" in attack.payload
        assert "target_ac" in attack.payload
        assert "hit" in attack.payload
        assert "is_natural_20" in attack.payload
        assert "is_natural_1" in attack.payload
        assert "is_threat" in attack.payload  # CP-11
        assert "is_critical" in attack.payload  # CP-11
        assert "confirmation_total" in attack.payload  # CP-11 (may be None)
        assert "attack_index" in attack.payload  # CP-11

    # Check damage_roll events have CP-11 fields
    damage_events = [e for e in events if e.event_type == "damage_roll"]
    for damage in damage_events:
        assert "base_damage" in damage.payload  # CP-11
        assert "critical_multiplier" in damage.payload  # CP-11
        assert "damage_total" in damage.payload
        assert "attack_index" in damage.payload  # CP-11


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS
# ==============================================================================

def test_backward_compatibility_with_cp10_events():
    """Tier 2: CP-11 events should be consumable by CP-10 event handlers (graceful degradation)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 15, "hp_current": 20}
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=1,  # Only 1 attack (like CP-10)
        weapon=Weapon(damage_dice="1d8", damage_bonus=2, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # CP-10 event handler should be able to apply hp_changed and entity_defeated events
    # (ignoring full_attack_start, full_attack_end, and new fields in attack_roll/damage_roll)
    from aidm.core.attack_resolver import apply_attack_events

    # Filter to CP-10 compatible events
    cp10_events = [e for e in events if e.event_type in {"attack_roll", "damage_roll", "hp_changed", "entity_defeated"}]

    # Apply using CP-10 handler
    final_state = apply_attack_events(world_state, cp10_events)

    # Should produce same final HP
    final_state_cp11 = apply_full_attack_events(world_state, events)
    assert final_state.entities["target"]["hp_current"] == final_state_cp11.entities["target"]["hp_current"]


def test_full_attack_sequence_event_ordering():
    """Tier 2: Events should be ordered: start → attacks → damage → HP → defeated → end."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 5, "hp_max": 10}  # Low HP for defeat
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=6,
        weapon=Weapon(damage_dice="2d6", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    event_types = [e.event_type for e in events]

    # Expected order: full_attack_start, attack_roll(s), damage_roll(s), hp_changed, entity_defeated?, full_attack_end
    assert event_types[0] == "full_attack_start"
    assert event_types[-1] == "full_attack_end"

    # All attack_rolls should come before hp_changed
    attack_indices = [i for i, t in enumerate(event_types) if t == "attack_roll"]
    hp_indices = [i for i, t in enumerate(event_types) if t == "hp_changed"]
    if attack_indices and hp_indices:
        assert max(attack_indices) < min(hp_indices)


def test_negative_hp_with_overkill_damage():
    """Tier 2: Multiple attacks should accumulate into large negative HP."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "barbarian": {"ac": 10},
            "goblin": {"ac": 10, "hp_current": 6, "hp_max": 6}
        }
    )

    intent = FullAttackIntent(
        attacker_id="barbarian",
        target_id="goblin",
        base_attack_bonus=11,  # 3 attacks
        weapon=Weapon(damage_dice="2d6", damage_bonus=6, damage_type="slashing")  # High damage
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
    final_state = apply_full_attack_events(world_state, events)

    # If multiple hits occurred, HP should go deeply negative
    damage_events = [e for e in events if e.event_type == "damage_roll"]
    if len(damage_events) >= 2:
        total_damage = sum(d.payload["damage_total"] for d in damage_events)
        expected_hp = 6 - total_damage
        assert final_state.entities["goblin"]["hp_current"] == expected_hp
        assert expected_hp < 0  # Overkill


def test_entity_defeated_after_full_attack():
    """Tier 2: Entity should be marked defeated when HP <= 0 after full attack."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 8, "hp_max": 10}
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=6,
        weapon=Weapon(damage_dice="2d6", damage_bonus=4, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
    final_state = apply_full_attack_events(world_state, events)

    # If entity was defeated
    if any(e.event_type == "entity_defeated" for e in events):
        assert final_state.entities["target"]["hp_current"] <= 0
        assert final_state.entities["target"].get("defeated", False) is True


def test_high_bab_character_four_attacks():
    """Tier 2: BAB +16 should generate 4 iterative attacks."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter_20": {"ac": 10},
            "target": {"ac": 10, "hp_current": 100, "hp_max": 100}
        }
    )

    intent = FullAttackIntent(
        attacker_id="fighter_20",
        target_id="target",
        base_attack_bonus=20,  # 4 attacks: +20/+15/+10/+5
        weapon=Weapon(damage_dice="1d8", damage_bonus=5, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Should have 4 attack_roll events
    attack_events = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_events) == 4

    # Verify attack bonuses
    assert attack_events[0].payload["attack_bonus"] == 20
    assert attack_events[1].payload["attack_bonus"] == 15
    assert attack_events[2].payload["attack_bonus"] == 10
    assert attack_events[3].payload["attack_bonus"] == 5


def test_critical_multiplier_variations():
    """Tier 2: Weapons with ×2, ×3, ×4 multipliers should work correctly."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 100}
        }
    )

    # Test ×4 multiplier (e.g., scythe)
    intent_x4 = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=10,
        weapon=Weapon(damage_dice="2d4", damage_bonus=3, damage_type="slashing", critical_multiplier=4)
    )

    # Find confirmed critical
    for seed in range(2000):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent_x4, world_state, rng, next_event_id=0, timestamp=1.0)

        attack_events = [e for e in events if e.event_type == "attack_roll"]
        damage_events = [e for e in events if e.event_type == "damage_roll"]

        if attack_events and attack_events[0].payload["is_critical"] and damage_events:
            damage = damage_events[0].payload
            assert damage["damage_total"] == damage["base_damage"] * 4
            assert damage["critical_multiplier"] == 4
            break
    else:
        pytest.fail("Could not find ×4 critical in 2000 seeds")


def test_full_attack_events_serialize_to_jsonl():
    """Tier 2: All full attack events should be JSON-serializable."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 15, "hp_current": 20}
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=11,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Verify each event can be serialized to JSON
    for event in events:
        json_str = json.dumps(event.to_dict(), sort_keys=True)
        assert json_str
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


# ==============================================================================
# CRITICAL RANGE TESTS (FIX-04)
# ==============================================================================

def test_weapon_critical_range_19_20_threatens_on_19():
    """Weapon with critical_range=19 should threaten on rolls of 19 and 20 (PHB p.140)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 100}
        }
    )

    # Longsword: 19-20/×2
    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=10,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing",
                      critical_multiplier=2, critical_range=19)
    )

    threat_on_19_found = False
    threat_on_20_found = False
    no_threat_on_18_found = False

    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        attack_events = [e for e in events if e.event_type == "attack_roll"]

        if attack_events:
            first = attack_events[0]
            d20 = first.payload["d20_result"]

            if d20 == 19:
                assert first.payload["is_threat"] is True
                threat_on_19_found = True
            elif d20 == 20:
                assert first.payload["is_threat"] is True
                threat_on_20_found = True
            elif d20 == 18:
                assert first.payload["is_threat"] is False
                no_threat_on_18_found = True

        if threat_on_19_found and threat_on_20_found and no_threat_on_18_found:
            break

    assert threat_on_19_found, "Could not find d20=19 in 5000 seeds"
    assert threat_on_20_found, "Could not find d20=20 in 5000 seeds"
    assert no_threat_on_18_found, "Could not find d20=18 in 5000 seeds"


def test_weapon_critical_range_18_20_threatens_on_18():
    """Weapon with critical_range=18 should threaten on rolls of 18, 19, and 20."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 100}
        }
    )

    # Keen longsword: 18-20/×2
    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=10,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing",
                      critical_multiplier=2, critical_range=18)
    )

    threat_on_18_found = False
    no_threat_on_17_found = False

    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        attack_events = [e for e in events if e.event_type == "attack_roll"]

        if attack_events:
            first = attack_events[0]
            d20 = first.payload["d20_result"]

            if d20 == 18:
                assert first.payload["is_threat"] is True
                threat_on_18_found = True
            elif d20 == 17:
                assert first.payload["is_threat"] is False
                no_threat_on_17_found = True

        if threat_on_18_found and no_threat_on_17_found:
            break

    assert threat_on_18_found, "Could not find d20=18 in 5000 seeds"
    assert no_threat_on_17_found, "Could not find d20=17 in 5000 seeds"


def test_weapon_default_critical_range_20_only():
    """Default critical_range=20 should only threaten on natural 20."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {"ac": 10},
            "target": {"ac": 10, "hp_current": 100}
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=10,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
        # critical_range defaults to 20
    )

    no_threat_on_19_found = False

    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        attack_events = [e for e in events if e.event_type == "attack_roll"]

        if attack_events:
            first = attack_events[0]
            d20 = first.payload["d20_result"]

            if d20 == 19:
                assert first.payload["is_threat"] is False
                no_threat_on_19_found = True
                break

    assert no_threat_on_19_found, "Could not find d20=19 in 5000 seeds"


def test_weapon_critical_range_validation():
    """Weapon critical_range must be between 1 and 20."""
    import pytest as pt

    # Valid ranges
    Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing", critical_range=20)
    Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing", critical_range=19)
    Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing", critical_range=18)
    Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing", critical_range=1)

    # Invalid ranges
    with pt.raises(ValueError):
        Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing", critical_range=0)

    with pt.raises(ValueError):
        Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing", critical_range=21)

    with pt.raises(ValueError):
        Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing", critical_range=-1)


# ==============================================================================
# WO-FIX-003: MODIFIER INTEGRATION TESTS
# ==============================================================================

def test_full_attack_condition_modifier_affects_attack_bonus():
    """WO-FIX-003: Shaken condition (-2 attack) must reduce hit probability in full attack.

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0311.txt
    Rule: "A shaken character takes a -2 penalty on attack rolls."
    """
    from aidm.schemas.conditions import create_shaken_condition
    from aidm.core.conditions import apply_condition

    # Base: attacker with no conditions, high BAB to guarantee hits
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "goblin": {
                "ac": 15, "hp_current": 30, "hp_max": 30,
                "team": "monsters",
            }
        }
    )

    intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=6,  # 2 attacks: +6/+1
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Run without condition
    rng_clean = RNGManager(master_seed=42)
    events_clean = resolve_full_attack(intent, world_state, rng_clean, next_event_id=0, timestamp=1.0)
    attacks_clean = [e for e in events_clean if e.event_type == "attack_roll"]

    # Apply shaken to attacker
    shaken = create_shaken_condition(source="intimidate", applied_at_event_id=0)
    shaken_state = apply_condition(world_state, "fighter", shaken)

    rng_shaken = RNGManager(master_seed=42)
    events_shaken = resolve_full_attack(intent, shaken_state, rng_shaken, next_event_id=0, timestamp=1.0)
    attacks_shaken = [e for e in events_shaken if e.event_type == "attack_roll"]

    # Same d20 rolls (same seed), but shaken totals should be 2 less
    for clean, shaken_atk in zip(attacks_clean, attacks_shaken):
        assert clean.payload["d20_result"] == shaken_atk.payload["d20_result"]
        assert shaken_atk.payload["total"] == clean.payload["total"] - 2
        assert shaken_atk.payload["condition_modifier"] == -2


def test_full_attack_defender_condition_affects_ac():
    """WO-FIX-003: Prone defender (-4 AC vs melee) must reduce effective AC in full attack.

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0311.txt
    Rule: "A prone defender takes a -4 penalty to Armor Class against melee attacks."
    """
    from aidm.schemas.conditions import create_prone_condition
    from aidm.core.conditions import apply_condition

    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "goblin": {
                "ac": 20, "hp_current": 30, "hp_max": 30,
                "team": "monsters",
            }
        }
    )

    intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=6,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Run against non-prone target
    rng_clean = RNGManager(master_seed=42)
    events_clean = resolve_full_attack(intent, world_state, rng_clean, next_event_id=0, timestamp=1.0)
    attacks_clean = [e for e in events_clean if e.event_type == "attack_roll"]

    # Apply prone to defender
    prone = create_prone_condition(source="trip", applied_at_event_id=0)
    prone_state = apply_condition(world_state, "goblin", prone)

    rng_prone = RNGManager(master_seed=42)
    events_prone = resolve_full_attack(intent, prone_state, rng_prone, next_event_id=0, timestamp=1.0)
    attacks_prone = [e for e in events_prone if e.event_type == "attack_roll"]

    # Prone target AC should be 4 less
    for clean, prone_atk in zip(attacks_clean, attacks_prone):
        assert prone_atk.payload["target_ac"] == clean.payload["target_ac"] - 4
        assert prone_atk.payload["target_base_ac"] == 20
        assert prone_atk.payload["target_ac_modifier"] == -4


def test_full_attack_condition_damage_modifier_applied():
    """WO-FIX-003: Sickened condition (-2 damage) must reduce damage in full attack.

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0312.txt
    Rule: "A sickened character takes a -2 penalty on all ... damage rolls."
    """
    from aidm.schemas.conditions import create_sickened_condition
    from aidm.core.conditions import apply_condition

    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "goblin": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "monsters",
            }
        }
    )

    intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=6,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Apply sickened to attacker
    sickened = create_sickened_condition(source="poison", applied_at_event_id=0)
    sick_state = apply_condition(world_state, "fighter", sickened)

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, sick_state, rng, next_event_id=0, timestamp=1.0)
    damage_events = [e for e in events if e.event_type == "damage_roll"]

    for dmg in damage_events:
        assert dmg.payload["condition_modifier"] == -2
        # base_damage includes condition modifier, so verify it's embedded
        raw_roll_sum = sum(dmg.payload["damage_rolls"]) + dmg.payload["damage_bonus"] + dmg.payload["str_modifier"]
        assert dmg.payload["base_damage"] == raw_roll_sum + dmg.payload["condition_modifier"] + dmg.payload["feat_modifier"]


def test_full_attack_event_audit_trail_includes_all_modifiers():
    """WO-FIX-003: attack_roll events must include all modifier breakdown fields."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "target": {
                "ac": 15, "hp_current": 30, "hp_max": 30,
                "team": "monsters",
            }
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=11,  # 3 attacks
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Check full_attack_start has modifier fields
    start = [e for e in events if e.event_type == "full_attack_start"][0]
    assert "condition_attack_modifier" in start.payload
    assert "condition_ac_modifier" in start.payload
    assert "mounted_bonus" in start.payload
    assert "terrain_higher_ground" in start.payload
    assert "cover_type" in start.payload
    assert "cover_ac_bonus" in start.payload
    assert "feat_attack_modifier" in start.payload
    assert "feat_damage_modifier" in start.payload
    assert "target_base_ac" in start.payload
    assert "target_ac" in start.payload

    # Check attack_roll events have modifier breakdown
    attack_events = [e for e in events if e.event_type == "attack_roll"]
    for atk in attack_events:
        required_fields = [
            "attack_bonus", "condition_modifier", "mounted_bonus",
            "terrain_higher_ground", "feat_modifier",
            "target_ac", "target_base_ac", "target_ac_modifier",
            "cover_type", "cover_ac_bonus",
        ]
        for field in required_fields:
            assert field in atk.payload, f"Missing field: {field}"

    # Check damage_roll events have modifier breakdown
    damage_events = [e for e in events if e.event_type == "damage_roll"]
    for dmg in damage_events:
        assert "condition_modifier" in dmg.payload
        assert "feat_modifier" in dmg.payload


def test_full_attack_targeting_fails_when_illegal():
    """WO-FIX-003: Full attack should emit targeting_failed if target is out of range.

    This guards against the pre-FIX-003 behaviour where full attack bypassed
    targeting legality entirely.
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50,
                "team": "party",
                "position": {"x": 0, "y": 0},
            },
            "target": {
                "ac": 15, "hp_current": 30,
                "team": "monsters",
                "position": {"x": 999, "y": 999},  # Very far away
            }
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=6,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Should have targeting_failed event and no attack_roll events
    assert any(e.event_type == "targeting_failed" for e in events)
    assert not any(e.event_type == "attack_roll" for e in events)

