"""D&D 3.5e edge case tests — RAW compliance verification.

Tests mechanical edge cases from PHB/DMG that are easy to get wrong:
- Natural 1 always misses regardless of bonuses (PHB p.139)
- Natural 20 always hits regardless of AC (PHB p.139)
- Minimum 1 damage on a successful hit (PHB p.145 interpretation)
- Condition stacking with critical hits
- BAB progression boundary values
- Falling damage cap (20d6 max, DMG p.304)
- Condition removal restores modifiers to zero
- Save natural 1/20 rules (PHB p.177)
"""

import pytest
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.attack_resolver import resolve_attack
from aidm.core.full_attack_resolver import (
    resolve_full_attack,
    FullAttackIntent,
    calculate_iterative_attacks,
)
from aidm.core.conditions import (
    apply_condition,
    remove_condition,
    get_condition_modifiers,
)
from aidm.schemas.conditions import (
    create_shaken_condition,
    create_sickened_condition,
    create_prone_condition,
    create_exhausted_condition,
)
from aidm.core.terrain_resolver import calculate_falling_damage
from aidm.core.save_resolver import resolve_save, get_save_bonus
from aidm.schemas.saves import SaveContext, SaveType


# ==============================================================================
# EDGE CASE 1: Natural 1 always misses (PHB p.139)
# ==============================================================================

def test_natural_1_always_misses_even_with_huge_bonus():
    """Natural 1 on attack roll is always a miss, even with +50 bonus vs AC 5."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 10, "hp_current": 50, "hp_max": 50, "team": "party"},
            "goblin": {"ac": 5, "hp_current": 6, "hp_max": 6, "team": "monsters"},
        }
    )

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=50,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing",
                      critical_multiplier=2),
    )

    # Find a seed that rolls natural 1
    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        attack_event = [e for e in events if e.event_type == "attack_roll"][0]
        if attack_event.payload["d20_result"] == 1:
            assert attack_event.payload["is_natural_1"] is True
            assert attack_event.payload["hit"] is False
            # No damage_roll event should follow
            damage_events = [e for e in events if e.event_type == "damage_roll"]
            assert len(damage_events) == 0
            return

    pytest.fail("Could not find natural 1 in 5000 seeds")


# ==============================================================================
# EDGE CASE 2: Natural 20 always hits (PHB p.139)
# ==============================================================================

def test_natural_20_always_hits_even_against_extreme_ac():
    """Natural 20 on attack roll always hits, even vs AC 100."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 10, "hp_current": 50, "hp_max": 50, "team": "party"},
            "dragon": {"ac": 100, "hp_current": 200, "hp_max": 200, "team": "monsters"},
        }
    )

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="dragon",
        attack_bonus=1,
        weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing",
                      critical_multiplier=2),
    )

    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        attack_event = [e for e in events if e.event_type == "attack_roll"][0]
        if attack_event.payload["d20_result"] == 20:
            assert attack_event.payload["is_natural_20"] is True
            assert attack_event.payload["hit"] is True
            return

    pytest.fail("Could not find natural 20 in 5000 seeds")


# ==============================================================================
# EDGE CASE 3: Damage floor is 1 on hit, before DR (PHB p.113)
# WO-FIX-01 (BUG-8/9): Updated from 0 to 1 — a hit always deals min 1 damage
# ==============================================================================

def test_damage_cannot_go_negative_from_condition_penalties():
    """Condition damage penalties cannot reduce damage below 1 on a hit (PHB p.113).

    WO-FIX-01 (BUG-8/9): Minimum damage on a successful hit is 1 before DR.
    Even with condition penalties that would make raw damage negative,
    the floor is 1 (not 0). DR may then reduce final_damage to 0.
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 10, "hp_current": 50, "hp_max": 50, "team": "party"},
            "goblin": {"ac": 5, "hp_current": 6, "hp_max": 6, "team": "monsters"},
        }
    )

    # Sickened gives -2 damage. With damage_bonus=0 and 1d4, min roll is 1.
    # base_damage = 1 + 0 + 0 = 1, condition = -2 → raw = -1
    # WO-FIX-01: max(1, -1) = 1 (min 1 on hit, before DR)
    sickened = create_sickened_condition(source="poison", applied_at_event_id=0)
    world_state = apply_condition(world_state, "fighter", sickened)

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=50,  # Guarantee hit
        weapon=Weapon(damage_dice="1d4", damage_bonus=0, damage_type="slashing",
                      critical_multiplier=2),
    )

    # Find a seed where the attack hits and damage roll is 1 (min)
    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        damage_events = [e for e in events if e.event_type == "damage_roll"]
        if damage_events:
            dmg = damage_events[0].payload
            # WO-FIX-01: damage_total must be >= 1 on a hit (before DR)
            assert dmg["damage_total"] >= 1
            if dmg["damage_rolls"] == [1]:
                # WO-FIX-01: min 1 on hit (was 0 before fix)
                assert dmg["damage_total"] == 1
                return

    pytest.fail("Could not find min damage roll in 5000 seeds")


# ==============================================================================
# EDGE CASE 4: BAB boundary — BAB 5 gets only 1 attack (PHB p.143)
# ==============================================================================

def test_bab_5_gets_one_attack_not_two():
    """BAB +5 should yield exactly 1 attack (second would be +0, below +1 threshold)."""
    attacks = calculate_iterative_attacks(5)
    assert attacks == [5]


def test_bab_6_gets_two_attacks():
    """BAB +6 should yield exactly 2 attacks: +6/+1."""
    attacks = calculate_iterative_attacks(6)
    assert attacks == [6, 1]


def test_bab_1_gets_one_attack():
    """BAB +1 (level 1 character) should yield exactly 1 attack."""
    attacks = calculate_iterative_attacks(1)
    assert attacks == [1]


# ==============================================================================
# EDGE CASE 5: Falling damage capped at 20d6 (DMG p.304)
# ==============================================================================

def test_falling_damage_capped_at_20d6():
    """Falls greater than 200 feet still only deal 20d6 (DMG p.304)."""
    assert calculate_falling_damage(200) == 20
    assert calculate_falling_damage(300) == 20
    assert calculate_falling_damage(1000) == 20


def test_falling_damage_zero_for_short_falls():
    """Falls under 10 feet deal no damage."""
    assert calculate_falling_damage(0) == 0
    assert calculate_falling_damage(5) == 0
    assert calculate_falling_damage(9) == 0


def test_intentional_fall_first_10_free():
    """Intentional jump: first 10 feet is free."""
    assert calculate_falling_damage(10, is_intentional=True) == 0
    assert calculate_falling_damage(20, is_intentional=True) == 1
    assert calculate_falling_damage(30, is_intentional=True) == 2


# ==============================================================================
# EDGE CASE 6: Condition removal restores zero modifiers
# ==============================================================================

def test_condition_removal_clears_all_modifiers():
    """Removing all conditions should restore modifiers to zero."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 16, "hp_current": 50, "hp_max": 50, "team": "party"},
        }
    )

    # Stack multiple conditions
    shaken = create_shaken_condition(source="fear", applied_at_event_id=0)
    sickened = create_sickened_condition(source="poison", applied_at_event_id=1)
    exhausted = create_exhausted_condition(source="fatigue", applied_at_event_id=2)
    world_state = apply_condition(world_state, "fighter", shaken)
    world_state = apply_condition(world_state, "fighter", sickened)
    world_state = apply_condition(world_state, "fighter", exhausted)

    # Verify non-zero modifiers
    mods = get_condition_modifiers(world_state, "fighter")
    assert mods.attack_modifier != 0

    # Remove all conditions
    world_state = remove_condition(world_state, "fighter", "shaken")
    world_state = remove_condition(world_state, "fighter", "sickened")
    world_state = remove_condition(world_state, "fighter", "exhausted")

    # All modifiers should be zero
    mods = get_condition_modifiers(world_state, "fighter")
    assert mods.attack_modifier == 0
    assert mods.damage_modifier == 0
    assert mods.ac_modifier == 0
    assert mods.dex_modifier == 0


# ==============================================================================
# EDGE CASE 7: Save natural 20 always succeeds (PHB p.177)
# ==============================================================================

def test_save_natural_20_always_succeeds():
    """Natural 20 on a saving throw always succeeds, even with impossible DC."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "ac": 15, "hp_current": 6, "hp_max": 6,
                "team": "monsters", "save_fort": 0,
            }
        }
    )

    save_ctx = SaveContext(
        source_id="death_spell",
        target_id="goblin",
        save_type=SaveType.FORT,
        dc=100,  # Impossible DC
    )

    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        outcome, events = resolve_save(save_ctx, world_state, rng,
                                       next_event_id=0, timestamp=1.0)
        save_events = [e for e in events if e.event_type == "save_rolled"]
        if save_events and save_events[0].payload["d20_result"] == 20:
            assert save_events[0].payload["is_natural_20"] is True
            assert save_events[0].payload["outcome"] == "success"
            return

    pytest.fail("Could not find natural 20 save in 5000 seeds")


def test_save_natural_1_always_fails():
    """Natural 1 on a saving throw always fails, even with huge bonus."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "paladin": {
                "ac": 20, "hp_current": 80, "hp_max": 80,
                "team": "party", "save_fort": 20, "con_mod": 5,
            }
        }
    )

    save_ctx = SaveContext(
        source_id="weak_poison",
        target_id="paladin",
        save_type=SaveType.FORT,
        dc=5,  # Trivial DC
    )

    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        outcome, events = resolve_save(save_ctx, world_state, rng,
                                       next_event_id=0, timestamp=1.0)
        save_events = [e for e in events if e.event_type == "save_rolled"]
        if save_events and save_events[0].payload["d20_result"] == 1:
            assert save_events[0].payload["is_natural_1"] is True
            assert save_events[0].payload["outcome"] == "failure"
            return

    pytest.fail("Could not find natural 1 save in 5000 seeds")


# ==============================================================================
# EDGE CASE 8: Prone defender has -4 AC vs melee (PHB p.311)
# ==============================================================================

def test_prone_defender_ac_reduced_in_attack():
    """Prone target should have -4 AC modifier applied during attack resolution."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"ac": 16, "hp_current": 50, "hp_max": 50, "team": "party"},
            "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6, "team": "monsters"},
        }
    )

    prone = create_prone_condition(source="trip", applied_at_event_id=0)
    world_state = apply_condition(world_state, "goblin", prone)

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing",
                      critical_multiplier=2),
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    attack_event = [e for e in events if e.event_type == "attack_roll"][0]
    assert attack_event.payload["target_base_ac"] == 15
    assert attack_event.payload["target_ac_modifier"] == -4
    assert attack_event.payload["target_ac"] == 11
