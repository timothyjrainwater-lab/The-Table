"""Tests for WO-FIX-01 and WO-FIX-02 fixes.

WO-FIX-01: Attack Damage Pipeline
- BUG-1: Two-handed STR multiplier (PHB p.113)
- BUG-8/BUG-9: Minimum damage on hit = 1 before DR

WO-FIX-02: Full Attack Loop Early Termination
- BUG-2: Loop breaks on target defeat
"""

import pytest
from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.full_attack_resolver import (
    resolve_full_attack,
    apply_full_attack_events,
    FullAttackIntent,
)
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent, Weapon


def _ws(ents):
    return WorldState(ruleset_version="3.5e", entities=ents)


# ==============================================================================
# WO-FIX-01 BUG-1: Grip-based STR-to-damage multiplier (PHB p.113)
# ==============================================================================


def test_two_handed_grip_1_5x_str():
    """Two-handed grip applies int(STR * 1.5) to damage (PHB p.113)."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": 4, "team": "party"},
        "def": {"ac": 10, "hp_current": 50, "hp_max": 50, "team": "monsters"},
    })
    weapon = Weapon(
        damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning",
        grip="two-handed",
    )
    intent = AttackIntent(
        attacker_id="atk", target_id="def",
        attack_bonus=20, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        if not dmg_evts:
            continue
        dmg = dmg_evts[0].payload
        roll_sum = sum(dmg["damage_rolls"])
        expected_str = int(4 * 1.5)  # 6
        expected_base = roll_sum + 0 + expected_str
        assert dmg["base_damage"] == expected_base
        break
    else:
        pytest.fail("Could not find a hit in 500 seeds")


def test_off_hand_grip_0_5x_str():
    """Off-hand grip applies int(STR * 0.5) to damage (PHB p.113)."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": 4, "team": "party"},
        "def": {"ac": 10, "hp_current": 50, "hp_max": 50, "team": "monsters"},
    })
    weapon = Weapon(
        damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning",
        grip="off-hand",
    )
    intent = AttackIntent(
        attacker_id="atk", target_id="def",
        attack_bonus=20, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        if not dmg_evts:
            continue
        dmg = dmg_evts[0].payload
        roll_sum = sum(dmg["damage_rolls"])
        expected_str = int(4 * 0.5)  # 2
        expected_base = roll_sum + 0 + expected_str
        assert dmg["base_damage"] == expected_base
        break
    else:
        pytest.fail("Could not find a hit in 500 seeds")


def test_one_handed_grip_flat_str():
    """One-handed grip applies flat STR to damage (PHB p.113)."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": 4, "team": "party"},
        "def": {"ac": 10, "hp_current": 50, "hp_max": 50, "team": "monsters"},
    })
    weapon = Weapon(
        damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning",
        grip="one-handed",
    )
    intent = AttackIntent(
        attacker_id="atk", target_id="def",
        attack_bonus=20, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        if not dmg_evts:
            continue
        dmg = dmg_evts[0].payload
        roll_sum = sum(dmg["damage_rolls"])
        expected_base = roll_sum + 0 + 4
        assert dmg["base_damage"] == expected_base
        break
    else:
        pytest.fail("Could not find a hit in 500 seeds")


def test_two_handed_grip_truncates_toward_zero():
    """int() truncation: STR_MOD=3 -> int(3*1.5)=int(4.5)=4 (not 5)."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": 3, "team": "party"},
        "def": {"ac": 10, "hp_current": 50, "hp_max": 50, "team": "monsters"},
    })
    weapon = Weapon(
        damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning",
        grip="two-handed",
    )
    intent = AttackIntent(
        attacker_id="atk", target_id="def",
        attack_bonus=20, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        if not dmg_evts:
            continue
        dmg = dmg_evts[0].payload
        roll_sum = sum(dmg["damage_rolls"])
        expected_str = int(3 * 1.5)  # 4, not 5
        assert expected_str == 4
        expected_base = roll_sum + 0 + expected_str
        assert dmg["base_damage"] == expected_base
        break
    else:
        pytest.fail("Could not find a hit in 500 seeds")


def test_grip_multiplier_in_full_attack():
    """Two-handed grip STR multiplier also works in full_attack_resolver."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": 4, "team": "party"},
        "def": {"ac": 10, "hp_current": 100, "hp_max": 100, "team": "monsters"},
    })
    weapon = Weapon(
        damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning",
        grip="two-handed",
    )
    intent = FullAttackIntent(
        attacker_id="atk", target_id="def",
        base_attack_bonus=6, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        if not dmg_evts:
            continue
        dmg = dmg_evts[0].payload
        roll_sum = sum(dmg["damage_rolls"])
        expected_str = int(4 * 1.5)  # 6
        expected_base = roll_sum + 0 + expected_str
        assert dmg["base_damage"] == expected_base
        break
    else:
        pytest.fail("Could not find a hit in 500 seeds")


# ==============================================================================
# WO-FIX-01 BUG-8/BUG-9: Minimum damage on hit = 1 (before DR)
# ==============================================================================


def test_minimum_damage_on_hit_is_1():
    """Minimum damage on a hit is 1 before DR (PHB p.113)."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": -5, "team": "party"},
        "def": {"ac": 10, "hp_current": 50, "hp_max": 50, "team": "monsters"},
    })
    weapon = Weapon(damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning")
    intent = AttackIntent(
        attacker_id="atk", target_id="def",
        attack_bonus=20, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        if not dmg_evts:
            continue
        dmg = dmg_evts[0].payload
        assert dmg["damage_total"] >= 1
        break
    else:
        pytest.fail("Could not find a hit in 500 seeds")


def test_after_dr_damage_can_be_zero():
    """After DR, final_damage CAN be 0 (DR absorbs the minimum 1)."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": -5, "team": "party"},
        "def": {
            "ac": 10, "hp_current": 50, "hp_max": 50,
            "team": "monsters",
            "damage_reductions": [{"amount": 5, "bypass": "magic"}],
        },
    })
    weapon = Weapon(damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning")
    intent = AttackIntent(
        attacker_id="atk", target_id="def",
        attack_bonus=20, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        if not dmg_evts:
            continue
        dmg = dmg_evts[0].payload
        if dmg["damage_total"] == 1:
            assert dmg["final_damage"] == 0
            break
    else:
        pytest.fail("Could not find a hit with damage_total=1 in 500 seeds")


def test_minimum_damage_on_critical_hit_is_1():
    """Critical hit with negative STR still has min damage_total=1."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": -5, "team": "party"},
        "def": {"ac": 10, "hp_current": 50, "hp_max": 50, "team": "monsters"},
    })
    weapon = Weapon(
        damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning",
        critical_multiplier=2,
    )
    intent = AttackIntent(
        attacker_id="atk", target_id="def",
        attack_bonus=20, weapon=weapon,
    )

    for seed in range(5000):
        rng = RNGManager(master_seed=seed)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        atk_evts = [e for e in events if e.event_type == "attack_roll"]
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        if not atk_evts or not atk_evts[0].payload.get("is_critical"):
            continue
        if not dmg_evts:
            continue
        dmg = dmg_evts[0].payload
        assert dmg["damage_total"] >= 1
        break
    else:
        pytest.fail("Could not find a critical hit in 5000 seeds")


def test_minimum_damage_in_full_attack_resolver():
    """Minimum damage on hit = 1 also works in full_attack_resolver."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": -5, "team": "party"},
        "def": {"ac": 10, "hp_current": 50, "hp_max": 50, "team": "monsters"},
    })
    weapon = Weapon(damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning")
    intent = FullAttackIntent(
        attacker_id="atk", target_id="def",
        base_attack_bonus=6, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        if not dmg_evts:
            continue
        for d in dmg_evts:
            assert d.payload["damage_total"] >= 1
        break
    else:
        pytest.fail("Could not find a hit in 500 seeds")


# ==============================================================================
# WO-FIX-02 BUG-2: Full attack loop early termination on target defeat
# ==============================================================================


def test_full_attack_breaks_on_defeat():
    """Full attack stops iterating when target HP <= 0 (BUG-2)."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": 4, "team": "party"},
        "def": {"ac": 10, "hp_current": 1, "hp_max": 10, "team": "monsters"},
    })
    weapon = Weapon(damage_dice="2d6", damage_bonus=4, damage_type="slashing")
    intent = FullAttackIntent(
        attacker_id="atk", target_id="def",
        base_attack_bonus=11, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        end_evts = [e for e in events if e.event_type == "full_attack_end"]
        if not dmg_evts:
            continue
        first_dmg = dmg_evts[0].payload["final_damage"]
        if first_dmg <= 0:
            continue
        assert end_evts[0].payload["num_attacks"] == 1
        assert any(e.event_type == "entity_defeated" for e in events)
        break
    else:
        pytest.fail("Could not find seed where first attack kills target")


def test_full_attack_total_damage_matches():
    """Total damage in full_attack_end matches sum of individual damage events."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": 2, "team": "party"},
        "def": {"ac": 10, "hp_current": 100, "hp_max": 100, "team": "monsters"},
    })
    weapon = Weapon(damage_dice="1d8", damage_bonus=2, damage_type="slashing")
    intent = FullAttackIntent(
        attacker_id="atk", target_id="def",
        base_attack_bonus=11, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        end_evts = [e for e in events if e.event_type == "full_attack_end"]
        if len(dmg_evts) < 2:
            continue
        sum_final = sum(d.payload["final_damage"] for d in dmg_evts)
        assert end_evts[0].payload["total_damage"] == sum_final
        break
    else:
        pytest.fail("Could not find seed with multiple hits in 500 seeds")


def test_full_attack_remaining_attacks_not_executed_after_defeat():
    """After target defeat, remaining attacks are NOT executed."""
    ws = _ws({
        "atk": {"ac": 10, "str_mod": 10, "team": "party"},
        "def": {"ac": 10, "hp_current": 1, "hp_max": 10, "team": "monsters"},
    })
    weapon = Weapon(damage_dice="2d6", damage_bonus=5, damage_type="slashing")
    intent = FullAttackIntent(
        attacker_id="atk", target_id="def",
        base_attack_bonus=16, weapon=weapon,
    )

    for seed in range(500):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        atk_evts = [e for e in events if e.event_type == "attack_roll"]
        dmg_evts = [e for e in events if e.event_type == "damage_roll"]
        if not dmg_evts:
            continue
        first_final = dmg_evts[0].payload["final_damage"]
        if first_final <= 0:
            continue
        assert len(atk_evts) == 1
        assert len(dmg_evts) == 1
        break
    else:
        pytest.fail("Could not find seed where first attack kills target")


# ==============================================================================
# Schema validation tests
# ==============================================================================


def test_weapon_grip_validation():
    """Weapon grip must be one of: one-handed, two-handed, off-hand."""
    with pytest.raises(ValueError, match="grip must be one of"):
        Weapon(
            damage_dice="1d8", damage_bonus=0, damage_type="slashing",
            grip="both-hands",
        )


def test_weapon_grip_defaults_to_one_handed():
    """Weapon grip defaults to one-handed when not specified."""
    w = Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing")
    assert w.grip == "one-handed"
