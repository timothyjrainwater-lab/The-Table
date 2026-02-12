"""Tests for WO-048 Damage Reduction system.

Tier 1 tests (MUST PASS):
- DR reduces physical damage
- DR does not reduce energy damage
- DR bypass matching (magic, material, alignment)
- DR/- is never bypassed
- Multiple DR sources: best applicable wins
- DR applied in single attack resolver
- DR applied in full attack resolver

Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0291.txt (PHB glossary)
"""

import pytest
from aidm.core.damage_reduction import (
    get_applicable_dr,
    apply_dr_to_damage,
    _weapon_bypasses_dr,
)
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
# UNIT TESTS: DR RESOLVER
# ==============================================================================


def test_apply_dr_reduces_damage():
    """DR 5 against 13 damage yields 8 final, 5 reduced (PHB p.291).

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0291.txt
    Rule: "Whenever damage reduction completely negates the damage from
    an attack, it also negates most special effects that accompany the attack."
    """
    final, reduced = apply_dr_to_damage(13, 5)
    assert final == 8
    assert reduced == 5


def test_apply_dr_cannot_reduce_below_zero():
    """DR 10 against 3 damage yields 0 final, 3 reduced (PHB p.291)."""
    final, reduced = apply_dr_to_damage(3, 10)
    assert final == 0
    assert reduced == 3


def test_apply_dr_zero_dr_no_effect():
    """DR 0 has no effect on damage."""
    final, reduced = apply_dr_to_damage(10, 0)
    assert final == 10
    assert reduced == 0


def test_apply_dr_zero_damage():
    """0 damage with DR yields 0."""
    final, reduced = apply_dr_to_damage(0, 5)
    assert final == 0
    assert reduced == 0


def test_dr_does_not_apply_to_fire():
    """DR does not apply to energy damage types (PHB p.291)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "zombie": {
                "ac": 10, "hp_current": 30,
                "damage_reductions": [{"amount": 5, "bypass": "slashing"}],
            }
        }
    )
    assert get_applicable_dr(world_state, "zombie", "fire") == 0


def test_dr_does_not_apply_to_force():
    """DR does not apply to force damage (PHB p.291)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "zombie": {
                "ac": 10, "hp_current": 30,
                "damage_reductions": [{"amount": 5, "bypass": "magic"}],
            }
        }
    )
    assert get_applicable_dr(world_state, "zombie", "force") == 0


def test_dr_applies_to_slashing():
    """DR applies to physical damage types."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "zombie": {
                "ac": 10, "hp_current": 30,
                "damage_reductions": [{"amount": 5, "bypass": "slashing"}],
            }
        }
    )
    # Non-slashing weapon → DR applies
    assert get_applicable_dr(world_state, "zombie", "bludgeoning") == 5


def test_dr_magic_bypassed_by_magic_weapon():
    """DR/magic is bypassed by a +1 or better weapon (PHB p.291)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "demon": {
                "ac": 20, "hp_current": 60,
                "damage_reductions": [{"amount": 10, "bypass": "magic"}],
            }
        }
    )
    # Non-magic weapon
    assert get_applicable_dr(world_state, "demon", "slashing", is_magic_weapon=False) == 10
    # Magic weapon bypasses
    assert get_applicable_dr(world_state, "demon", "slashing", is_magic_weapon=True) == 0


def test_dr_adamantine_bypassed_by_adamantine():
    """DR/adamantine is bypassed by adamantine weapons."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "golem": {
                "ac": 26, "hp_current": 100,
                "damage_reductions": [{"amount": 10, "bypass": "adamantine"}],
            }
        }
    )
    assert get_applicable_dr(world_state, "golem", "slashing", weapon_material="steel") == 10
    assert get_applicable_dr(world_state, "golem", "slashing", weapon_material="adamantine") == 0


def test_dr_cold_iron_bypassed_by_cold_iron():
    """DR/cold iron is bypassed by cold iron weapons."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fey": {
                "ac": 15, "hp_current": 20,
                "damage_reductions": [{"amount": 5, "bypass": "cold_iron"}],
            }
        }
    )
    assert get_applicable_dr(world_state, "fey", "slashing", weapon_material="steel") == 5
    assert get_applicable_dr(world_state, "fey", "slashing", weapon_material="cold_iron") == 0


def test_dr_silver_bypassed_by_silver():
    """DR/silver is bypassed by silver or alchemical silver weapons."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "werewolf": {
                "ac": 15, "hp_current": 30,
                "damage_reductions": [{"amount": 10, "bypass": "silver"}],
            }
        }
    )
    assert get_applicable_dr(world_state, "werewolf", "slashing", weapon_material="steel") == 10
    assert get_applicable_dr(world_state, "werewolf", "slashing", weapon_material="silver") == 0
    assert get_applicable_dr(world_state, "werewolf", "slashing", weapon_material="alchemical_silver") == 0


def test_dr_dash_never_bypassed():
    """DR/- cannot be bypassed by any weapon property (PHB p.291).

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0291.txt
    Rule: "Some monsters are vulnerable to certain materials...
    A few very powerful monsters are vulnerable to no type of weapon."
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "barbarian": {
                "ac": 14, "hp_current": 80,
                "damage_reductions": [{"amount": 2, "bypass": "-"}],
            }
        }
    )
    # Nothing bypasses DR/-
    assert get_applicable_dr(world_state, "barbarian", "slashing", is_magic_weapon=True) == 2
    assert get_applicable_dr(world_state, "barbarian", "slashing", weapon_material="adamantine") == 2
    assert get_applicable_dr(world_state, "barbarian", "slashing", weapon_enhancement=5) == 2


def test_dr_alignment_good_bypassed():
    """DR/good is bypassed by good-aligned weapons."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "demon": {
                "ac": 20, "hp_current": 60,
                "damage_reductions": [{"amount": 10, "bypass": "good"}],
            }
        }
    )
    assert get_applicable_dr(world_state, "demon", "slashing", weapon_alignment="none") == 10
    assert get_applicable_dr(world_state, "demon", "slashing", weapon_alignment="good") == 0
    assert get_applicable_dr(world_state, "demon", "slashing", weapon_alignment="evil") == 10


def test_multiple_dr_best_applies():
    """With multiple DR sources, the highest applicable one wins (PHB p.291)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "monster": {
                "ac": 20, "hp_current": 80,
                "damage_reductions": [
                    {"amount": 10, "bypass": "magic"},
                    {"amount": 5, "bypass": "-"},
                ],
            }
        }
    )
    # Non-magic weapon: both apply, best is 10/magic
    assert get_applicable_dr(world_state, "monster", "slashing", is_magic_weapon=False) == 10
    # Magic weapon: only 5/- applies (10/magic is bypassed)
    assert get_applicable_dr(world_state, "monster", "slashing", is_magic_weapon=True) == 5


def test_dr_missing_entity_returns_zero():
    """Missing entity returns 0 DR."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={}
    )
    assert get_applicable_dr(world_state, "nonexistent", "slashing") == 0


def test_dr_no_dr_field_returns_zero():
    """Entity without DR field returns 0."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={"goblin": {"ac": 15, "hp_current": 6}}
    )
    assert get_applicable_dr(world_state, "goblin", "slashing") == 0


# ==============================================================================
# INTEGRATION TESTS: DR IN ATTACK RESOLVER
# ==============================================================================


def test_single_attack_dr_reduces_hp_loss():
    """WO-048: DR reduces HP damage from single attacks.

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0291.txt
    Rule: "Damage reduction can reduce damage to 0 but not below 0."
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
                "damage_reductions": [{"amount": 5, "bypass": "magic"}],
            }
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="defender",
        attack_bonus=20,  # Auto-hit
        weapon=Weapon(damage_dice="1d8", damage_bonus=5, damage_type="slashing")
    )

    # Run with seed and without DR
    rng_dr = RNGManager(master_seed=42)
    events_dr = resolve_attack(intent, world_state, rng_dr, next_event_id=0, timestamp=1.0)

    # Also run without DR for comparison
    world_state_no_dr = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50, "hp_max": 50,
                "team": "party",
            },
            "defender": {
                "ac": 5, "hp_current": 50, "hp_max": 50,
                "team": "monsters",
            }
        }
    )
    rng_no_dr = RNGManager(master_seed=42)
    events_no_dr = resolve_attack(intent, world_state_no_dr, rng_no_dr, next_event_id=0, timestamp=1.0)

    # Find damage events
    dmg_dr = [e for e in events_dr if e.event_type == "damage_roll"]
    dmg_no_dr = [e for e in events_no_dr if e.event_type == "damage_roll"]

    if dmg_dr and dmg_no_dr:
        # DR event should have damage_reduced and final_damage fields
        assert dmg_dr[0].payload["dr_amount"] == 5
        assert dmg_dr[0].payload["damage_reduced"] > 0
        assert dmg_dr[0].payload["final_damage"] == dmg_dr[0].payload["damage_total"] - dmg_dr[0].payload["damage_reduced"]

        # HP delta should be based on final_damage, not damage_total
        hp_dr = [e for e in events_dr if e.event_type == "hp_changed"]
        hp_no_dr = [e for e in events_no_dr if e.event_type == "hp_changed"]
        if hp_dr and hp_no_dr:
            assert abs(hp_dr[0].payload["delta"]) < abs(hp_no_dr[0].payload["delta"])


def test_full_attack_dr_reduces_accumulated_damage():
    """WO-048: DR applies per-attack in full attack, reducing each hit's damage."""
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
                "damage_reductions": [{"amount": 3, "bypass": "magic"}],
            }
        }
    )

    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="defender",
        base_attack_bonus=11,  # 3 attacks
        weapon=Weapon(damage_dice="1d8", damage_bonus=5, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    # Every damage_roll event should show dr_amount=3
    dmg_events = [e for e in events if e.event_type == "damage_roll"]
    for dmg in dmg_events:
        assert dmg.payload["dr_amount"] == 3
        assert dmg.payload["final_damage"] == max(0, dmg.payload["damage_total"] - dmg.payload["damage_reduced"])

    # full_attack_start should include dr_amount
    start = [e for e in events if e.event_type == "full_attack_start"][0]
    assert start.payload["dr_amount"] == 3


def test_dr_event_payload_present_even_when_zero():
    """WO-048: DR fields should appear in event payload even when DR is 0."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                "ac": 10, "hp_current": 50,
                "team": "party",
            },
            "defender": {
                "ac": 5, "hp_current": 50,
                "team": "monsters",
                # No DR
            }
        }
    )

    intent = AttackIntent(
        attacker_id="attacker",
        target_id="defender",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=5, damage_type="slashing")
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)

    dmg = [e for e in events if e.event_type == "damage_roll"]
    if dmg:
        assert "dr_amount" in dmg[0].payload
        assert "damage_reduced" in dmg[0].payload
        assert "final_damage" in dmg[0].payload
        assert dmg[0].payload["dr_amount"] == 0
        assert dmg[0].payload["damage_reduced"] == 0
        assert dmg[0].payload["final_damage"] == dmg[0].payload["damage_total"]
