"""Tests for WO-034-FIX Power Attack integration in attack resolvers.

Verifies that power_attack_penalty flows from AttackIntent/FullAttackIntent
through the feat resolver to produce correct attack/damage modifiers.

Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0098.txt (PHB Power Attack)
"""

import pytest
from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.full_attack_resolver import (
    resolve_full_attack,
    FullAttackIntent,
)
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.feats import FeatID


def _make_power_attack_entity(team="party"):
    """Create an entity with Power Attack feat and STR 16 (+3)."""
    return {
        "ac": 10, "hp_current": 50, "hp_max": 50,
        "team": team,
        "str_mod": 3,
        "feats": [FeatID.POWER_ATTACK],
    }


# ==============================================================================
# SINGLE ATTACK: POWER ATTACK INTEGRATION
# ==============================================================================


def test_single_attack_power_attack_reduces_attack_bonus():
    """WO-034-FIX: Power Attack penalty reduces attack total.

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0098.txt
    Rule: "On your action, before making attack rolls for a round, you may
    choose to subtract a number from all melee attack rolls and add the
    same number to all melee damage rolls."
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": _make_power_attack_entity("party"),
            "goblin": {
                "ac": 15, "hp_current": 30, "hp_max": 30,
                "team": "monsters",
            }
        }
    )

    # Attack without Power Attack
    intent_no_pa = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=10,
        weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing"),
        power_attack_penalty=0,
    )

    # Attack with Power Attack 5
    intent_pa5 = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=10,
        weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing"),
        power_attack_penalty=5,
    )

    rng1 = RNGManager(master_seed=42)
    events_no_pa = resolve_attack(intent_no_pa, world_state, rng1, next_event_id=0, timestamp=1.0)

    rng2 = RNGManager(master_seed=42)
    events_pa5 = resolve_attack(intent_pa5, world_state, rng2, next_event_id=0, timestamp=1.0)

    atk_no_pa = [e for e in events_no_pa if e.event_type == "attack_roll"][0]
    atk_pa5 = [e for e in events_pa5 if e.event_type == "attack_roll"][0]

    # Same d20 roll (same seed)
    assert atk_no_pa.payload["d20_result"] == atk_pa5.payload["d20_result"]
    # Power Attack total should be 5 less
    assert atk_pa5.payload["total"] == atk_no_pa.payload["total"] - 5
    # Feat modifier should reflect -5
    assert atk_pa5.payload["feat_modifier"] == atk_no_pa.payload["feat_modifier"] - 5


def test_single_attack_power_attack_increases_damage_one_handed():
    """WO-034-FIX: Power Attack adds 1:1 damage for one-handed weapons.

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0098.txt
    Rule: "...add the same number to all melee damage rolls."
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": _make_power_attack_entity("party"),
            "goblin": {
                "ac": 5, "hp_current": 100, "hp_max": 100,
                "team": "monsters",
            }
        }
    )

    # One-handed weapon, Power Attack 3
    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,  # Auto-hit
        weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing",
                      is_two_handed=False),
        power_attack_penalty=3,
    )

    # Find a seed where the attack hits
    for seed in range(100):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        dmg_events = [e for e in events if e.event_type == "damage_roll"]
        if dmg_events:
            dmg = dmg_events[0].payload
            # feat_modifier should be +3 (from Power Attack 3, one-handed)
            assert dmg["feat_modifier"] == 3
            break
    else:
        pytest.fail("Could not find hit in 100 seeds")


def test_single_attack_power_attack_increases_damage_two_handed():
    """WO-034-FIX: Power Attack adds 1:2 damage for two-handed weapons.

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0098.txt
    Rule: "If you attack with a two-handed weapon... you can add twice
    the number subtracted from your attack rolls."
    """
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": _make_power_attack_entity("party"),
            "goblin": {
                "ac": 5, "hp_current": 100, "hp_max": 100,
                "team": "monsters",
            }
        }
    )

    # Two-handed weapon, Power Attack 3
    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="2d6", damage_bonus=0, damage_type="slashing",
                      is_two_handed=True),
        power_attack_penalty=3,
    )

    for seed in range(100):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        dmg_events = [e for e in events if e.event_type == "damage_roll"]
        if dmg_events:
            dmg = dmg_events[0].payload
            # feat_modifier should be +6 (Power Attack 3 × 2 for two-handed)
            assert dmg["feat_modifier"] == 6
            break
    else:
        pytest.fail("Could not find hit in 100 seeds")


def test_single_attack_no_power_attack_no_penalty():
    """WO-034-FIX: power_attack_penalty=0 means no feat penalty/bonus."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": _make_power_attack_entity("party"),
            "goblin": {
                "ac": 5, "hp_current": 100, "hp_max": 100,
                "team": "monsters",
            }
        }
    )

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=20,
        weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing"),
        power_attack_penalty=0,
    )

    for seed in range(100):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        dmg_events = [e for e in events if e.event_type == "damage_roll"]
        if dmg_events:
            # No Power Attack → feat_modifier should be 0
            assert dmg_events[0].payload["feat_modifier"] == 0
            break


# ==============================================================================
# FULL ATTACK: POWER ATTACK INTEGRATION
# ==============================================================================


def test_full_attack_power_attack_all_attacks_penalized():
    """WO-034-FIX: Power Attack penalty applies to all iterative attacks."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": _make_power_attack_entity("party"),
            "goblin": {
                "ac": 5, "hp_current": 200, "hp_max": 200,
                "team": "monsters",
            }
        }
    )

    # Without Power Attack
    intent_no_pa = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=11,  # 3 attacks
        weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing"),
        power_attack_penalty=0,
    )

    # With Power Attack 4
    intent_pa4 = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=11,
        weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing"),
        power_attack_penalty=4,
    )

    rng1 = RNGManager(master_seed=42)
    events_no_pa = resolve_full_attack(intent_no_pa, world_state, rng1, next_event_id=0, timestamp=1.0)

    rng2 = RNGManager(master_seed=42)
    events_pa4 = resolve_full_attack(intent_pa4, world_state, rng2, next_event_id=0, timestamp=1.0)

    atk_no_pa = [e for e in events_no_pa if e.event_type == "attack_roll"]
    atk_pa4 = [e for e in events_pa4 if e.event_type == "attack_roll"]

    # All attacks should have -4 penalty from Power Attack
    for no_pa, pa4 in zip(atk_no_pa, atk_pa4):
        assert no_pa.payload["d20_result"] == pa4.payload["d20_result"]
        assert pa4.payload["total"] == no_pa.payload["total"] - 4


def test_full_attack_power_attack_damage_bonus_two_handed():
    """WO-034-FIX: Full attack with two-handed Power Attack gets 2× damage bonus."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": _make_power_attack_entity("party"),
            "goblin": {
                "ac": 5, "hp_current": 200, "hp_max": 200,
                "team": "monsters",
            }
        }
    )

    intent = FullAttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        base_attack_bonus=11,
        weapon=Weapon(damage_dice="2d6", damage_bonus=0, damage_type="slashing",
                      is_two_handed=True),
        power_attack_penalty=5,
    )

    for seed in range(200):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, world_state, rng, next_event_id=0, timestamp=1.0)
        dmg_events = [e for e in events if e.event_type == "damage_roll"]
        if dmg_events:
            # Two-handed: damage bonus = penalty × 2 = 10
            for dmg in dmg_events:
                assert dmg.payload["feat_modifier"] == 10
            break
    else:
        pytest.fail("Could not find hits in 200 seeds")


# ==============================================================================
# VALIDATION TESTS
# ==============================================================================


def test_attack_intent_rejects_negative_power_attack():
    """power_attack_penalty must be non-negative."""
    with pytest.raises(ValueError, match="power_attack_penalty cannot be negative"):
        AttackIntent(
            attacker_id="a",
            target_id="b",
            attack_bonus=5,
            weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing"),
            power_attack_penalty=-1,
        )


def test_full_attack_intent_rejects_negative_power_attack():
    """power_attack_penalty must be non-negative."""
    with pytest.raises(ValueError, match="power_attack_penalty cannot be negative"):
        FullAttackIntent(
            attacker_id="a",
            target_id="b",
            base_attack_bonus=5,
            weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing"),
            power_attack_penalty=-1,
        )


def test_backward_compatibility_default_zero():
    """Existing code that doesn't set power_attack_penalty still works."""
    intent = AttackIntent(
        attacker_id="a",
        target_id="b",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing"),
    )
    assert intent.power_attack_penalty == 0

    full_intent = FullAttackIntent(
        attacker_id="a",
        target_id="b",
        base_attack_bonus=5,
        weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing"),
    )
    assert full_intent.power_attack_penalty == 0


def test_weapon_is_two_handed_default_false():
    """Weapon.is_two_handed defaults to False for backward compatibility."""
    weapon = Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing")
    assert weapon.is_two_handed is False

    weapon_2h = Weapon(damage_dice="2d6", damage_bonus=0, damage_type="slashing",
                       is_two_handed=True)
    assert weapon_2h.is_two_handed is True
