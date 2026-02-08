"""Integration tests for CP-16 Conditions & Status Effects Kernel.

Tests condition storage, modifier queries, and combat integration:
- Condition application and removal
- Modifier aggregation and stacking
- Attack/AC modifier integration
- Deterministic replay with conditions
- Event-driven lifecycle

Tier-1 (MUST PASS):
- Condition modifiers affect attack rolls
- Condition modifiers affect AC
- Condition modifiers affect damage rolls
- Multiple conditions stack correctly
- Deterministic replay through condition changes

Tier-2 (SHOULD PASS):
- Condition application events
- Condition removal
- Query system fail-closed behavior
"""

import pytest
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.conditions import (
    get_condition_modifiers,
    apply_condition,
    remove_condition,
    has_condition
)
from aidm.schemas.conditions import (
    ConditionType,
    create_prone_condition,
    create_flat_footed_condition,
    create_grappled_condition,
    create_helpless_condition,
    create_stunned_condition,
    create_dazed_condition,
    create_shaken_condition,
    create_sickened_condition
)


# ==============================================================================
# TIER 1: MUST-PASS TESTS
# ==============================================================================

def test_condition_modifiers_affect_attack_rolls():
    """Tier 1: Shaken condition (-2 attack) affects attack roll total."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "team": "party"
            },
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply shaken condition to fighter (-2 attack)
    shaken = create_shaken_condition(source="intimidate", applied_at_event_id=0)
    world_state = apply_condition(world_state, "fighter", shaken)

    # Attack intent
    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=Weapon(
            damage_dice="1d8",
            damage_bonus=3,
            damage_type="slashing",
            critical_multiplier=2
        )
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Check attack_roll event has condition_modifier
    attack_event = [e for e in events if e.event_type == "attack_roll"][0]
    assert attack_event.payload["condition_modifier"] == -2
    assert attack_event.payload["attack_bonus"] == 5
    # Total should be d20 + 5 - 2
    expected_total = attack_event.payload["d20_result"] + 5 - 2
    assert attack_event.payload["total"] == expected_total


def test_condition_modifiers_affect_ac():
    """Tier 1: Prone condition (-4 AC vs melee) affects target AC."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "team": "party"
            },
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply prone condition to goblin (-4 AC)
    prone = create_prone_condition(source="trip", applied_at_event_id=0)
    world_state = apply_condition(world_state, "goblin", prone)

    # Attack intent
    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=Weapon(
            damage_dice="1d8",
            damage_bonus=3,
            damage_type="slashing",
            critical_multiplier=2
        )
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Check attack_roll event has modified AC
    attack_event = [e for e in events if e.event_type == "attack_roll"][0]
    assert attack_event.payload["target_base_ac"] == 15
    assert attack_event.payload["target_ac_modifier"] == -4
    assert attack_event.payload["target_ac"] == 11  # 15 - 4


def test_condition_modifiers_affect_damage_rolls():
    """Tier 1: Sickened condition (-2 damage) affects damage total."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "team": "party"
            },
            "goblin": {
                "ac": 10,  # Low AC for guaranteed hit
                "hp_current": 20,
                "hp_max": 20,
                "team": "monsters"
            }
        }
    )

    # Apply sickened condition to fighter (-2 attack, -2 damage)
    sickened = create_sickened_condition(source="poison", applied_at_event_id=0)
    world_state = apply_condition(world_state, "fighter", sickened)

    # Attack intent
    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=10,  # High bonus for guaranteed hit
        weapon=Weapon(
            damage_dice="1d8",
            damage_bonus=3,
            damage_type="slashing",
            critical_multiplier=2
        )
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Check damage_roll event has condition_modifier
    damage_events = [e for e in events if e.event_type == "damage_roll"]
    if damage_events:  # Only if attack hit
        damage_event = damage_events[0]
        assert damage_event.payload["condition_modifier"] == -2
        # Damage total should include -2 penalty
        base_damage = sum(damage_event.payload["damage_rolls"]) + damage_event.payload["damage_bonus"]
        expected_damage = max(0, base_damage - 2)
        assert damage_event.payload["damage_total"] == expected_damage


def test_multiple_conditions_stack_correctly():
    """Tier 1: Multiple conditions with same modifier type stack additively."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "team": "party"
            },
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply shaken (-2 attack) and sickened (-2 attack, -2 damage) to fighter
    shaken = create_shaken_condition(source="fear", applied_at_event_id=0)
    sickened = create_sickened_condition(source="poison", applied_at_event_id=1)
    world_state = apply_condition(world_state, "fighter", shaken)
    world_state = apply_condition(world_state, "fighter", sickened)

    # Query modifiers
    modifiers = get_condition_modifiers(world_state, "fighter")
    assert modifiers.attack_modifier == -4  # -2 from shaken + -2 from sickened
    assert modifiers.damage_modifier == -2  # -2 from sickened only

    # Attack intent
    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=10,
        weapon=Weapon(
            damage_dice="1d8",
            damage_bonus=3,
            damage_type="slashing",
            critical_multiplier=2
        )
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Check attack event has stacked modifier
    attack_event = [e for e in events if e.event_type == "attack_roll"][0]
    assert attack_event.payload["condition_modifier"] == -4


def test_deterministic_replay_with_conditions():
    """Tier 1: Same RNG seed produces identical outcomes with conditions."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "ac": 16,
                "hp_current": 10,
                "hp_max": 10,
                "team": "party"
            },
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply prone to goblin
    prone = create_prone_condition(source="trip", applied_at_event_id=0)
    world_state = apply_condition(world_state, "goblin", prone)

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=Weapon(
            damage_dice="1d8",
            damage_bonus=3,
            damage_type="slashing",
            critical_multiplier=2
        )
    )

    # Run 3 times with same seed
    results = []
    for _ in range(3):
        rng = RNGManager(master_seed=100)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        final_state = apply_attack_events(world_state, events)
        results.append((events, final_state))

    # All results should be identical
    first_events, first_state = results[0]
    for events, state in results[1:]:
        assert state.state_hash() == first_state.state_hash()
        assert len(events) == len(first_events)
        for e1, e2 in zip(first_events, events):
            assert e1.event_type == e2.event_type
            assert e1.payload == e2.payload


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS
# ==============================================================================

def test_condition_application_and_storage():
    """Tier 2: Conditions are stored correctly in WorldState."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply prone condition
    prone = create_prone_condition(source="trip", applied_at_event_id=0)
    updated_state = apply_condition(world_state, "goblin", prone)

    # Check storage
    assert "goblin" in updated_state.entities
    goblin = updated_state.entities["goblin"]
    assert "conditions" in goblin
    assert "prone" in goblin["conditions"]

    # Check condition data
    condition_dict = goblin["conditions"]["prone"]
    assert condition_dict["condition_type"] == "prone"
    assert condition_dict["source"] == "trip"
    assert condition_dict["applied_at_event_id"] == 0


def test_condition_removal():
    """Tier 2: Conditions can be removed correctly."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply and then remove prone condition
    prone = create_prone_condition(source="trip", applied_at_event_id=0)
    world_state = apply_condition(world_state, "goblin", prone)
    assert has_condition(world_state, "goblin", "prone")

    # Remove condition
    world_state = remove_condition(world_state, "goblin", "prone")
    assert not has_condition(world_state, "goblin", "prone")

    # Query should return zero modifiers
    modifiers = get_condition_modifiers(world_state, "goblin")
    assert modifiers.ac_modifier == 0
    assert modifiers.attack_modifier == 0


def test_query_system_fail_closed():
    """Tier 2: Query system returns zero modifiers for missing entities."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Query non-existent entity
    modifiers = get_condition_modifiers(world_state, "nonexistent_actor")
    assert modifiers.ac_modifier == 0
    assert modifiers.attack_modifier == 0
    assert modifiers.damage_modifier == 0


def test_helpless_condition_modifiers():
    """Tier 2: Helpless condition has correct modifiers."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply helpless condition
    helpless = create_helpless_condition(source="sleep", applied_at_event_id=0)
    world_state = apply_condition(world_state, "goblin", helpless)

    # Query modifiers
    modifiers = get_condition_modifiers(world_state, "goblin")
    assert modifiers.ac_modifier == -4  # Melee attacks get +4 bonus
    assert modifiers.loses_dex_to_ac is True
    assert modifiers.actions_prohibited is True
    assert modifiers.auto_hit_if_helpless is True


def test_stunned_condition_modifiers():
    """Tier 2: Stunned condition has correct modifiers."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply stunned condition
    stunned = create_stunned_condition(source="stunning_fist", applied_at_event_id=0)
    world_state = apply_condition(world_state, "goblin", stunned)

    # Query modifiers
    modifiers = get_condition_modifiers(world_state, "goblin")
    assert modifiers.ac_modifier == -2
    assert modifiers.loses_dex_to_ac is True
    assert modifiers.actions_prohibited is True


def test_grappled_condition_modifiers():
    """Tier 2: Grappled condition has correct modifiers."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply grappled condition
    grappled = create_grappled_condition(source="grapple", applied_at_event_id=0)
    world_state = apply_condition(world_state, "goblin", grappled)

    # Query modifiers
    modifiers = get_condition_modifiers(world_state, "goblin")
    assert modifiers.dex_modifier == -4
    assert modifiers.movement_prohibited is True


def test_dazed_condition_modifiers():
    """Tier 2: Dazed condition has correct modifiers."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply dazed condition
    dazed = create_dazed_condition(source="spell", applied_at_event_id=0)
    world_state = apply_condition(world_state, "goblin", dazed)

    # Query modifiers
    modifiers = get_condition_modifiers(world_state, "goblin")
    assert modifiers.ac_modifier == 0  # No AC penalty
    assert modifiers.actions_prohibited is True


def test_flat_footed_condition_modifiers():
    """Tier 2: Flat-footed condition has correct modifiers."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply flat-footed condition
    flat_footed = create_flat_footed_condition(source="combat_start", applied_at_event_id=0)
    world_state = apply_condition(world_state, "goblin", flat_footed)

    # Query modifiers
    modifiers = get_condition_modifiers(world_state, "goblin")
    assert modifiers.loses_dex_to_ac is True


def test_condition_overwrite_same_type():
    """Tier 2: Applying same condition type overwrites previous instance."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "team": "monsters"
            }
        }
    )

    # Apply shaken twice with different sources
    shaken1 = create_shaken_condition(source="intimidate", applied_at_event_id=0)
    shaken2 = create_shaken_condition(source="fear_spell", applied_at_event_id=5)

    world_state = apply_condition(world_state, "goblin", shaken1)
    world_state = apply_condition(world_state, "goblin", shaken2)

    # Should only have one shaken condition (latest)
    goblin = world_state.entities["goblin"]
    assert len(goblin["conditions"]) == 1
    assert goblin["conditions"]["shaken"]["source"] == "fear_spell"
    assert goblin["conditions"]["shaken"]["applied_at_event_id"] == 5
