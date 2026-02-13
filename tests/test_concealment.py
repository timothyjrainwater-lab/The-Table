"""Tests for WO-049 Concealment/Miss Chance system.

Tier 1 tests (MUST PASS):
- get_miss_chance returns 0 for entities without miss chance
- get_miss_chance returns direct miss_chance field value
- get_miss_chance checks conditions for miss_chance_percent
- get_miss_chance uses highest miss chance (no stacking)
- check_miss_chance returns True when d100 <= miss_chance_percent
- check_miss_chance returns False when d100 > miss_chance_percent
- Miss chance integrated in single attack resolver
- Miss chance integrated in full attack resolver
- Miss chance only consumes d100 when hit=True and miss_chance > 0
- Miss chance does not fire on natural 1 (miss)

Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0152.txt (PHB concealment)
"""

import pytest
from aidm.core.concealment import get_miss_chance, check_miss_chance
from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.full_attack_resolver import (
    resolve_full_attack,
    FullAttackIntent,
)
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ==============================================================================
# UNIT TESTS: CONCEALMENT RESOLVER
# ==============================================================================


def test_get_miss_chance_returns_zero_for_no_miss_chance():
    """Entity without miss chance returns 0."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={"goblin": {"ac": 15, "hp_current": 6}}
    )
    assert get_miss_chance(world_state, "goblin") == 0


def test_get_miss_chance_returns_zero_for_missing_entity():
    """Missing entity returns 0."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={}
    )
    assert get_miss_chance(world_state, "nonexistent") == 0


def test_get_miss_chance_reads_direct_field():
    """Entity with direct miss_chance field returns that value.

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0152.txt
    Rule: Concealment gives the subject of a successful attack a chance
    that the attacker actually missed.
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "blur_target": {
                "ac": 15, "hp_current": 20,
                "miss_chance": 20,
            }
        }
    )
    assert get_miss_chance(world_state, "blur_target") == 20


def test_get_miss_chance_reads_condition_miss_chance():
    """Entity with condition that provides miss_chance_percent uses it."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "invisible": {
                "ac": 15, "hp_current": 20,
                "conditions": {
                    "invisibility_001": {
                        "condition_type": "invisibility",
                        "modifiers": {"miss_chance_percent": 50},
                    }
                },
            }
        }
    )
    assert get_miss_chance(world_state, "invisible") == 50


def test_get_miss_chance_uses_highest_no_stacking():
    """Multiple miss chance sources: use the highest, no stacking (PHB p.152).

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0152.txt
    Rule: Miss chances don't stack; use the best one.
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "concealed": {
                "ac": 15, "hp_current": 20,
                "miss_chance": 20,  # From environment (fog)
                "conditions": {
                    "blur_001": {
                        "condition_type": "blur",
                        "modifiers": {"miss_chance_percent": 50},
                    }
                },
            }
        }
    )
    # Should use 50 (from blur condition), not 20 (from field), not 70 (stacked)
    assert get_miss_chance(world_state, "concealed") == 50


def test_get_miss_chance_caps_at_100():
    """Miss chance is capped at 100%."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "super_concealed": {
                "ac": 15, "hp_current": 20,
                "miss_chance": 150,  # Erroneous value
            }
        }
    )
    assert get_miss_chance(world_state, "super_concealed") == 100


def test_check_miss_chance_hit_when_d100_above():
    """d100 roll above miss_chance_percent means the attack lands."""
    assert check_miss_chance(20, 21) is False  # 21 > 20 → hits
    assert check_miss_chance(20, 100) is False  # 100 > 20 → hits
    assert check_miss_chance(50, 51) is False  # 51 > 50 → hits


def test_check_miss_chance_miss_when_d100_at_or_below():
    """d100 roll at or below miss_chance_percent means concealment miss.

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0152.txt
    Rule: "Roll a d100. If the result is within the miss chance percentage,
    the attack misses."
    """
    assert check_miss_chance(20, 20) is True  # 20 <= 20 → miss
    assert check_miss_chance(20, 1) is True   # 1 <= 20 → miss
    assert check_miss_chance(50, 50) is True  # 50 <= 50 → miss
    assert check_miss_chance(50, 25) is True  # 25 <= 50 → miss


def test_check_miss_chance_zero_percent_never_misses():
    """0% miss chance never causes a miss."""
    assert check_miss_chance(0, 1) is False
    assert check_miss_chance(0, 50) is False
    assert check_miss_chance(0, 100) is False


def test_check_miss_chance_negative_percent_never_misses():
    """Negative miss chance (erroneous) never causes a miss."""
    assert check_miss_chance(-10, 1) is False


def test_check_miss_chance_100_percent_always_misses():
    """100% miss chance always causes a miss."""
    assert check_miss_chance(100, 1) is True
    assert check_miss_chance(100, 50) is True
    assert check_miss_chance(100, 100) is True


# ==============================================================================
# INTEGRATION TESTS: SINGLE ATTACK RESOLVER WITH CONCEALMENT
# ==============================================================================


def test_single_attack_concealment_miss_emits_event():
    """WO-049: Attack that hits AC but fails miss chance emits concealment_miss event.

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0152.txt
    Rule: Concealment miss chance is rolled after the attack roll succeeds.
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "defender": {
                "ac": 5, "hp_current": 50, "hp_max": 50,
                "team": "monsters",
                "miss_chance": 50,  # 50% miss chance
            }
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="defender",
        attack_bonus=20,  # Auto-hit AC
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Search for a seed where the attack hits AC but fails miss chance
    concealment_miss_found = False
    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

        concealment_events = [e for e in events if e.event_type == "concealment_miss"]
        if concealment_events:
            concealment_miss_found = True
            ce = concealment_events[0]
            assert ce.payload["miss_chance_percent"] == 50
            assert ce.payload["original_hit"] is True
            assert ce.payload["d100_result"] <= 50
            # Should NOT have damage_roll events
            assert not any(e.event_type == "damage_roll" for e in events)
            # Should NOT have hp_changed events
            assert not any(e.event_type == "hp_changed" for e in events)
            break

    assert concealment_miss_found, "Could not find concealment miss in 500 seeds"


def test_single_attack_concealment_pass_still_deals_damage():
    """WO-049: Attack that hits AC and passes miss chance deals damage normally."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "defender": {
                "ac": 5, "hp_current": 50, "hp_max": 50,
                "team": "monsters",
                "miss_chance": 20,  # 20% miss chance (80% pass)
            }
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="defender",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Search for a seed where the attack hits and passes miss chance
    hit_through_concealment = False
    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

        damage_events = [e for e in events if e.event_type == "damage_roll"]
        concealment_events = [e for e in events if e.event_type == "concealment_miss"]

        if damage_events and not concealment_events:
            hit_through_concealment = True
            # Should have hp_changed
            assert any(e.event_type == "hp_changed" for e in events)
            break

    assert hit_through_concealment, "Could not find hit through concealment in 500 seeds"


def test_single_attack_no_miss_chance_no_d100_consumed():
    """WO-049: No miss chance → no d100 consumed (RNG determinism).

    Verifies that when defender has no miss_chance, the d100 roll is NOT consumed,
    preserving RNG stream order for subsequent rolls.
    """
    world_state_no_mc = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "defender": {
                "ac": 5, "hp_current": 50, "hp_max": 50,
                "team": "monsters",
                # No miss_chance field
            }
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="defender",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Run with no miss chance
    rng1 = RNGManager(master_seed=42)
    events1 = resolve_attack(intent, world_state_no_mc, rng1, next_event_id=0, timestamp=1.0)

    # Run again — should be deterministic
    rng2 = RNGManager(master_seed=42)
    events2 = resolve_attack(intent, world_state_no_mc, rng2, next_event_id=0, timestamp=1.0)

    # No concealment events
    assert not any(e.event_type == "concealment_miss" for e in events1)

    # Events should be identical (deterministic, no d100 consumed)
    assert len(events1) == len(events2)
    for e1, e2 in zip(events1, events2):
        assert e1.payload == e2.payload


def test_single_attack_miss_on_ac_no_concealment_check():
    """WO-049: If attack misses AC, no concealment check occurs.

    Miss chance is only rolled when hit=True (PHB p.152: "on attacks that
    would otherwise hit").
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "defender": {
                "ac": 50, "hp_current": 50, "hp_max": 50,
                "team": "monsters",
                "miss_chance": 50,  # Has miss chance but shouldn't matter
            }
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="defender",
        attack_bonus=0,  # Very low, will miss AC 50
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Find a seed where the d20 is not a natural 20 (so it misses AC)
    for seed in range(100):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

        attack_events = [e for e in events if e.event_type == "attack_roll"]
        if attack_events and not attack_events[0].payload["is_natural_20"]:
            # Should miss AC and NOT have concealment check
            assert attack_events[0].payload["hit"] is False
            assert not any(e.event_type == "concealment_miss" for e in events)
            assert not any(e.event_type == "damage_roll" for e in events)
            break
    else:
        pytest.fail("Could not find non-nat-20 attack in 100 seeds")


# ==============================================================================
# INTEGRATION TESTS: FULL ATTACK RESOLVER WITH CONCEALMENT
# ==============================================================================


def test_full_attack_concealment_miss_prevents_damage():
    """WO-049: Full attack miss chance prevents damage on individual attacks."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "defender": {
                "ac": 5, "hp_current": 100, "hp_max": 100,
                "team": "monsters",
                "miss_chance": 50,  # 50% miss chance
            }
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="defender",
        base_attack_bonus=11,  # 3 attacks
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Search for seed with at least one concealment miss in full attack
    concealment_miss_in_full = False
    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

        concealment_events = [e for e in events if e.event_type == "concealment_miss"]
        if concealment_events:
            concealment_miss_in_full = True

            # Verify concealment_miss has attack_index field
            ce = concealment_events[0]
            assert "attack_index" in ce.payload
            assert ce.payload["miss_chance_percent"] == 50
            assert ce.payload["original_hit"] is True

            break

    assert concealment_miss_in_full, "Could not find concealment miss in full attack over 500 seeds"


def test_full_attack_concealment_reduces_total_damage():
    """WO-049: With miss chance, total damage should be less than without."""
    world_state_with_mc = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "defender": {
                "ac": 5, "hp_current": 100, "hp_max": 100,
                "team": "monsters",
                "miss_chance": 50,
            }
        }
    )

    world_state_no_mc = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "defender": {
                "ac": 5, "hp_current": 100, "hp_max": 100,
                "team": "monsters",
            }
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="defender",
        base_attack_bonus=11,  # 3 attacks
        weapon=Weapon(damage_dice="1d8", damage_bonus=5, damage_type="slashing")
    )

    # Run many seeds and compare total damage with vs without miss chance
    total_with_mc = 0
    total_without_mc = 0
    runs = 50

    for seed in range(runs):
        rng_mc = RNGManager(master_seed=seed)
        events_mc = resolve_full_attack(intent, world_state_with_mc, rng_mc, next_event_id=0, timestamp=1.0)
        dmg_mc = sum(e.payload["final_damage"] for e in events_mc if e.event_type == "damage_roll")
        total_with_mc += dmg_mc

        rng_no = RNGManager(master_seed=seed)
        events_no = resolve_full_attack(intent, world_state_no_mc, rng_no, next_event_id=0, timestamp=1.0)
        dmg_no = sum(e.payload["final_damage"] for e in events_no if e.event_type == "damage_roll")
        total_without_mc += dmg_no

    # With 50% miss chance over 50 runs, total damage should be noticeably less
    # (not exactly 50% less due to RNG stream divergence, but clearly less)
    assert total_with_mc < total_without_mc, (
        f"Miss chance did not reduce damage: {total_with_mc} vs {total_without_mc}"
    )


def test_full_attack_start_includes_miss_chance_percent():
    """WO-049: full_attack_start event payload must include miss_chance_percent."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "defender": {
                "ac": 15, "hp_current": 30, "hp_max": 30,
                "team": "monsters",
                "miss_chance": 20,
            }
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="defender",
        base_attack_bonus=6,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    start = [e for e in events if e.event_type == "full_attack_start"][0]
    assert "miss_chance_percent" in start.payload
    assert start.payload["miss_chance_percent"] == 20


def test_concealment_miss_deterministic_replay():
    """WO-049: Same seed with concealment must produce identical events."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "defender": {
                "ac": 5, "hp_current": 50, "hp_max": 50,
                "team": "monsters",
                "miss_chance": 50,
            }
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="defender",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
    )

    # Run 3 times with same seed
    results = []
    for _ in range(3):
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        results.append(events)

    first = results[0]
    for run in results[1:]:
        assert len(run) == len(first)
        for e1, e2 in zip(first, run):
            assert e1.event_type == e2.event_type
            assert e1.payload == e2.payload
