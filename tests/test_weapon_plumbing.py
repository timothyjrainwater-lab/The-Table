"""Tests for WO-WEAPON-PLUMBING-001: Weapon Data Pipeline.

Verifies:
- Weapon dataclass: weapon_type, range_increment, is_ranged, is_light
- Attack resolver: is_ranged detection, range_ft, max_range from range_increment
- Full attack resolver: same ranged detection pipeline
- Disarm: weapon type modifiers (+4 two-handed, -4 light)
- Sunder: grip-adjusted STR multiplier (1.5x two-handed, 0.5x off-hand)
- Intent bridge: dict EF.WEAPON -> Weapon with weapon_type/range_increment
- Backward compat: string EF.WEAPON defaults to one-handed melee
"""

import pytest

from aidm.core.attack_resolver import resolve_attack
from aidm.core.full_attack_resolver import resolve_full_attack
from aidm.core.maneuver_resolver import (
    resolve_disarm, resolve_sunder,
    _get_weapon_type, _get_weapon_grip,
)
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.interaction.intent_bridge import IntentBridge
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import DisarmIntent, SunderIntent


# ======================================================================
# Helpers
# ======================================================================


def _melee_weapon(**overrides):
    """Create a standard melee weapon."""
    defaults = {
        "damage_dice": "1d8",
        "damage_bonus": 0,
        "damage_type": "slashing",
        "weapon_type": "one-handed",
        "range_increment": 0,
    }
    defaults.update(overrides)
    return Weapon(**defaults)


def _ranged_weapon(**overrides):
    """Create a standard ranged weapon (longbow)."""
    defaults = {
        "damage_dice": "1d8",
        "damage_bonus": 0,
        "damage_type": "piercing",
        "weapon_type": "ranged",
        "range_increment": 100,
    }
    defaults.update(overrides)
    return Weapon(**defaults)


def _two_combatants(distance_squares=1, attacker_weapon=None, target_weapon=None):
    """Create world state with two positioned combatants.

    Args:
        distance_squares: Distance in grid squares (1 = adjacent = 5ft)
        attacker_weapon: Dict or string for attacker's EF.WEAPON
        target_weapon: Dict or string for target's EF.WEAPON
    """
    attacker = {
        EF.ENTITY_ID: "attacker",
        EF.TEAM: "party",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.AC: 15,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: 3,
        EF.DEX_MOD: 1,
        EF.SIZE_CATEGORY: "medium",
        EF.ATTACK_BONUS: 5,
        EF.BAB: 5,
    }
    if attacker_weapon is not None:
        attacker[EF.WEAPON] = attacker_weapon

    target = {
        EF.ENTITY_ID: "target",
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 12,
        EF.DEFEATED: False,
        EF.POSITION: {"x": distance_squares, "y": 0},
        EF.STR_MOD: 2,
        EF.DEX_MOD: 0,
        EF.SIZE_CATEGORY: "medium",
        EF.ATTACK_BONUS: 3,
        EF.BAB: 3,
    }
    if target_weapon is not None:
        target[EF.WEAPON] = target_weapon

    return WorldState(
        ruleset_version="3.5e",
        entities={"attacker": attacker, "target": target},
        active_combat={
            "initiative_order": ["attacker", "target"],
            "aoo_used_this_round": [],
        },
    )


# ======================================================================
# TestWeaponDataclass
# ======================================================================


class TestWeaponDataclass:
    """Weapon dataclass: weapon_type, range_increment, is_ranged, is_light."""

    def test_weapon_type_defaults_to_one_handed(self):
        w = Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing")
        assert w.weapon_type == "one-handed"

    def test_range_increment_defaults_to_zero(self):
        w = Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing")
        assert w.range_increment == 0

    def test_is_ranged_true_for_ranged_type(self):
        w = _ranged_weapon()
        assert w.is_ranged is True

    def test_is_ranged_false_for_melee_types(self):
        for wtype in ("light", "one-handed", "two-handed", "natural"):
            w = _melee_weapon(weapon_type=wtype)
            assert w.is_ranged is False, f"Expected is_ranged=False for {wtype}"

    def test_is_light_true_for_light_type(self):
        w = _melee_weapon(weapon_type="light")
        assert w.is_light is True

    def test_is_light_false_for_other_types(self):
        for wtype in ("one-handed", "two-handed", "ranged", "natural"):
            w = _melee_weapon(weapon_type=wtype)
            assert w.is_light is False, f"Expected is_light=False for {wtype}"

    def test_weapon_type_validation_rejects_invalid(self):
        with pytest.raises(ValueError, match="weapon_type"):
            Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing",
                   weapon_type="ballista")

    def test_range_increment_validation_rejects_negative(self):
        with pytest.raises(ValueError, match="range_increment"):
            Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing",
                   range_increment=-1)

    def test_existing_fields_unchanged(self):
        """Existing fields (grip, is_two_handed, etc.) still work."""
        w = Weapon(
            damage_dice="2d6",
            damage_bonus=1,
            damage_type="slashing",
            critical_multiplier=3,
            critical_range=19,
            is_two_handed=True,
            grip="two-handed",
            weapon_type="two-handed",
            range_increment=0,
        )
        assert w.damage_dice == "2d6"
        assert w.critical_multiplier == 3
        assert w.is_two_handed is True
        assert w.grip == "two-handed"
        assert w.weapon_type == "two-handed"
        assert w.is_ranged is False


# ======================================================================
# TestRangedDetection
# ======================================================================


class TestRangedDetection:
    """is_ranged flows from weapon_type through resolvers."""

    def test_melee_weapon_resolves_as_melee(self):
        """Melee weapon attack at adjacent range proceeds normally."""
        ws = _two_combatants(distance_squares=1)
        intent = AttackIntent(
            attacker_id="attacker",
            target_id="target",
            attack_bonus=5,
            weapon=_melee_weapon(),
        )
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        event_types = [e.event_type for e in events]
        assert "attack_roll" in event_types

    def test_ranged_weapon_resolves_within_range(self):
        """Ranged weapon at 15ft (within range_increment*10=1000ft) proceeds."""
        ws = _two_combatants(distance_squares=3)  # 3 squares = 15 ft
        intent = AttackIntent(
            attacker_id="attacker",
            target_id="target",
            attack_bonus=5,
            weapon=_ranged_weapon(range_increment=100),  # max 1000 ft
        )
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        event_types = [e.event_type for e in events]
        assert "attack_roll" in event_types


class TestMaxRange:
    """max_range computed from range_increment."""

    def test_ranged_out_of_range_fails(self):
        """Ranged weapon beyond max range fails targeting."""
        # range_increment=10 -> max_range=100ft. Place target at 22 squares = 110ft
        ws = _two_combatants(distance_squares=22)
        intent = AttackIntent(
            attacker_id="attacker",
            target_id="target",
            attack_bonus=5,
            weapon=_ranged_weapon(range_increment=10),  # max 100 ft
        )
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        event_types = [e.event_type for e in events]
        assert "targeting_failed" in event_types

    def test_ranged_within_range_succeeds(self):
        """Ranged weapon within max range proceeds."""
        # range_increment=10 -> max_range=100ft. Place target at 18 squares = 90ft
        ws = _two_combatants(distance_squares=18)
        intent = AttackIntent(
            attacker_id="attacker",
            target_id="target",
            attack_bonus=5,
            weapon=_ranged_weapon(range_increment=10),  # max 100 ft
        )
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        event_types = [e.event_type for e in events]
        assert "attack_roll" in event_types

    def test_melee_adjacent_succeeds(self):
        """Melee weapon at adjacent range (5ft) always succeeds range check."""
        ws = _two_combatants(distance_squares=1)
        intent = AttackIntent(
            attacker_id="attacker",
            target_id="target",
            attack_bonus=5,
            weapon=_melee_weapon(),
        )
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        event_types = [e.event_type for e in events]
        assert "attack_roll" in event_types

    def test_legacy_entities_no_position_succeed(self):
        """Entities without positions default to (0,0) - melee range check passes."""
        ws = WorldState(
            ruleset_version="3.5e",
            entities={
                "attacker": {EF.HP_CURRENT: 10, EF.HP_MAX: 10, EF.AC: 10},
                "target": {EF.HP_CURRENT: 10, EF.HP_MAX: 10, EF.AC: 10},
            },
        )
        intent = AttackIntent(
            attacker_id="attacker",
            target_id="target",
            attack_bonus=5,
            weapon=_melee_weapon(),
        )
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        event_types = [e.event_type for e in events]
        # Should not fail on range - distance is 0, max_range=max(5,0)=5
        assert "targeting_failed" not in event_types or all(
            e.payload.get("reason") != "out_of_range"
            for e in events if e.event_type == "targeting_failed"
        )


# ======================================================================
# TestDisarmWeaponModifiers
# ======================================================================


class TestDisarmWeaponModifiers:
    """Disarm opposed check includes weapon type modifiers (PHB p.155)."""

    def test_helper_returns_weapon_type_from_dict(self):
        """_get_weapon_type extracts weapon_type from dict EF.WEAPON."""
        ws = _two_combatants(
            attacker_weapon={"damage_dice": "2d6", "damage_bonus": 0,
                             "damage_type": "slashing", "weapon_type": "two-handed"},
        )
        assert _get_weapon_type(ws, "attacker") == "two-handed"

    def test_helper_defaults_one_handed_for_string_weapon(self):
        """_get_weapon_type returns one-handed for string EF.WEAPON."""
        ws = _two_combatants(attacker_weapon="longsword")
        assert _get_weapon_type(ws, "attacker") == "one-handed"

    def test_helper_defaults_one_handed_for_no_weapon(self):
        """_get_weapon_type returns one-handed when no EF.WEAPON."""
        ws = _two_combatants()
        assert _get_weapon_type(ws, "attacker") == "one-handed"

    def test_two_handed_vs_light_modifiers(self):
        """Two-handed attacker (+4) vs light defender (-4) = net +8 advantage."""
        ws = _two_combatants(
            attacker_weapon={"damage_dice": "2d6", "damage_bonus": 0,
                             "damage_type": "slashing", "weapon_type": "two-handed"},
            target_weapon={"damage_dice": "1d4", "damage_bonus": 0,
                           "damage_type": "piercing", "weapon_type": "light"},
        )
        intent = DisarmIntent(attacker_id="attacker", target_id="target")

        # Run across many seeds - attacker should win far more often
        # due to +8 net modifier advantage (attacker gets +4, defender gets -4)
        wins = 0
        for seed in range(100):
            rng = RNGManager(master_seed=seed)
            events, _, result = resolve_disarm(intent, ws, rng, next_event_id=0, timestamp=1.0)
            if result.success:
                wins += 1

        # With +8 advantage on opposed checks (both d20+mod), attacker wins most
        assert wins >= 60, f"Two-handed vs light should win often, got {wins}/100"

    def test_one_handed_vs_one_handed_baseline(self):
        """One-handed vs one-handed = no weapon type modifier advantage."""
        ws = _two_combatants(
            attacker_weapon={"damage_dice": "1d8", "damage_bonus": 0,
                             "damage_type": "slashing", "weapon_type": "one-handed"},
            target_weapon={"damage_dice": "1d8", "damage_bonus": 0,
                           "damage_type": "slashing", "weapon_type": "one-handed"},
        )
        intent = DisarmIntent(attacker_id="attacker", target_id="target")

        wins = 0
        for seed in range(100):
            rng = RNGManager(master_seed=seed)
            events, _, result = resolve_disarm(intent, ws, rng, next_event_id=0, timestamp=1.0)
            if result.success:
                wins += 1

        # Attacker has BAB 5 + STR 3 = +8, defender has BAB 3 + STR 2 = +5
        # +3 advantage but no weapon type bonus, should win moderately
        assert 40 <= wins <= 95, f"Baseline one-handed should be moderate, got {wins}/100"

    def test_light_attacker_disadvantage(self):
        """Light attacker (-4) vs two-handed defender (+4) = net -8 disadvantage."""
        ws = _two_combatants(
            attacker_weapon={"damage_dice": "1d4", "damage_bonus": 0,
                             "damage_type": "piercing", "weapon_type": "light"},
            target_weapon={"damage_dice": "2d6", "damage_bonus": 0,
                           "damage_type": "slashing", "weapon_type": "two-handed"},
        )
        intent = DisarmIntent(attacker_id="attacker", target_id="target")

        wins = 0
        for seed in range(100):
            rng = RNGManager(master_seed=seed)
            events, _, result = resolve_disarm(intent, ws, rng, next_event_id=0, timestamp=1.0)
            if result.success:
                wins += 1

        # -8 net disadvantage: attacker(BAB5+STR3-4=4) vs defender(BAB3+STR2+4=9)
        # Attacker should lose more than baseline
        assert wins <= 50, f"Light vs two-handed should lose often, got {wins}/100"


# ======================================================================
# TestSunderGripMultiplier
# ======================================================================


class TestSunderGripMultiplier:
    """Sunder damage applies grip-adjusted STR multiplier."""

    def test_helper_returns_grip_from_dict(self):
        """_get_weapon_grip extracts grip from dict EF.WEAPON."""
        ws = _two_combatants(
            attacker_weapon={"damage_dice": "2d6", "damage_bonus": 0,
                             "damage_type": "slashing", "grip": "two-handed"},
        )
        assert _get_weapon_grip(ws, "attacker") == "two-handed"

    def test_helper_defaults_one_handed(self):
        """_get_weapon_grip defaults to one-handed for string/missing weapon."""
        ws = _two_combatants(attacker_weapon="longsword")
        assert _get_weapon_grip(ws, "attacker") == "one-handed"

    def test_two_handed_grip_1_5x_str(self):
        """Two-handed grip gives int(STR * 1.5) damage bonus on sunder."""
        # attacker STR_MOD = 3 -> two-handed = int(3 * 1.5) = 4
        ws = _two_combatants(
            attacker_weapon={"damage_dice": "2d6", "damage_bonus": 0,
                             "damage_type": "slashing", "grip": "two-handed"},
            target_weapon={"damage_dice": "1d8", "damage_bonus": 0,
                           "damage_type": "slashing"},
        )
        intent = SunderIntent(
            attacker_id="attacker",
            target_id="target",
            target_item="shield",
        )

        # Find a seed where sunder succeeds
        for seed in range(200):
            rng = RNGManager(master_seed=seed)
            events, _, result = resolve_sunder(intent, ws, rng, next_event_id=0, timestamp=1.0)
            if result.success:
                sunder_event = next(
                    e for e in events if e.event_type == "sunder_success"
                )
                # STR_MOD=3, grip=two-handed -> damage_bonus = int(3*1.5) = 4
                assert sunder_event.payload["damage_bonus"] == 4, (
                    f"Expected damage_bonus=4 (int(3*1.5)), got {sunder_event.payload['damage_bonus']}"
                )
                return

        pytest.fail("No sunder success found in 200 seeds")

    def test_off_hand_grip_0_5x_str(self):
        """Off-hand grip gives int(STR * 0.5) damage bonus on sunder."""
        # attacker STR_MOD = 3 -> off-hand = int(3 * 0.5) = 1
        ws = _two_combatants(
            attacker_weapon={"damage_dice": "1d6", "damage_bonus": 0,
                             "damage_type": "slashing", "grip": "off-hand"},
            target_weapon={"damage_dice": "1d8", "damage_bonus": 0,
                           "damage_type": "slashing"},
        )
        intent = SunderIntent(
            attacker_id="attacker",
            target_id="target",
            target_item="weapon",
        )

        for seed in range(200):
            rng = RNGManager(master_seed=seed)
            events, _, result = resolve_sunder(intent, ws, rng, next_event_id=0, timestamp=1.0)
            if result.success:
                sunder_event = next(
                    e for e in events if e.event_type == "sunder_success"
                )
                assert sunder_event.payload["damage_bonus"] == 1, (
                    f"Expected damage_bonus=1 (int(3*0.5)), got {sunder_event.payload['damage_bonus']}"
                )
                return

        pytest.fail("No sunder success found in 200 seeds")

    def test_one_handed_grip_1x_str(self):
        """One-handed grip gives 1x STR damage bonus on sunder (default)."""
        ws = _two_combatants(
            attacker_weapon={"damage_dice": "1d8", "damage_bonus": 0,
                             "damage_type": "slashing", "grip": "one-handed"},
            target_weapon={"damage_dice": "1d8", "damage_bonus": 0,
                           "damage_type": "slashing"},
        )
        intent = SunderIntent(
            attacker_id="attacker",
            target_id="target",
            target_item="weapon",
        )

        for seed in range(200):
            rng = RNGManager(master_seed=seed)
            events, _, result = resolve_sunder(intent, ws, rng, next_event_id=0, timestamp=1.0)
            if result.success:
                sunder_event = next(
                    e for e in events if e.event_type == "sunder_success"
                )
                # STR_MOD=3, grip=one-handed -> damage_bonus = 3
                assert sunder_event.payload["damage_bonus"] == 3, (
                    f"Expected damage_bonus=3 (1x STR), got {sunder_event.payload['damage_bonus']}"
                )
                return

        pytest.fail("No sunder success found in 200 seeds")


# ======================================================================
# TestIntentBridgeDict
# ======================================================================


class TestIntentBridgeDict:
    """Intent bridge handles dict EF.WEAPON pattern."""

    def test_dict_weapon_type_flows_to_weapon(self):
        """Dict EF.WEAPON with weapon_type produces correct Weapon."""
        bridge = IntentBridge()
        actor = {
            EF.WEAPON: {
                "damage_dice": "1d8",
                "damage_bonus": 0,
                "damage_type": "piercing",
                "weapon_type": "ranged",
                "range_increment": 100,
            },
            EF.ATTACK_BONUS: 5,
        }
        result = bridge._resolve_weapon(None, actor)
        weapon, attack_bonus = result
        assert weapon.weapon_type == "ranged"
        assert weapon.is_ranged is True
        assert weapon.range_increment == 100

    def test_dict_weapon_grip_flows(self):
        """Dict EF.WEAPON grip field flows to Weapon."""
        bridge = IntentBridge()
        actor = {
            EF.WEAPON: {
                "damage_dice": "2d6",
                "damage_bonus": 0,
                "damage_type": "slashing",
                "grip": "two-handed",
                "is_two_handed": True,
                "weapon_type": "two-handed",
            },
            EF.ATTACK_BONUS: 5,
        }
        result = bridge._resolve_weapon(None, actor)
        weapon, _ = result
        assert weapon.grip == "two-handed"
        assert weapon.is_two_handed is True
        assert weapon.weapon_type == "two-handed"

    def test_dict_weapon_defaults(self):
        """Dict EF.WEAPON with minimal fields uses correct defaults."""
        bridge = IntentBridge()
        actor = {
            EF.WEAPON: {
                "damage_dice": "1d8",
                "damage_bonus": 0,
                "damage_type": "slashing",
            },
            EF.ATTACK_BONUS: 5,
        }
        result = bridge._resolve_weapon(None, actor)
        weapon, _ = result
        assert weapon.weapon_type == "one-handed"
        assert weapon.range_increment == 0
        assert weapon.is_ranged is False
        assert weapon.grip == "one-handed"

    def test_dict_weapon_with_weapon_name_still_works(self):
        """Dict EF.WEAPON used even when weapon_name is specified."""
        bridge = IntentBridge()
        actor = {
            EF.WEAPON: {
                "damage_dice": "1d8",
                "damage_bonus": 0,
                "damage_type": "slashing",
                "weapon_type": "two-handed",
            },
            EF.ATTACK_BONUS: 5,
        }
        result = bridge._resolve_weapon("longsword", actor)
        weapon, _ = result
        assert weapon.weapon_type == "two-handed"


# ======================================================================
# TestBackwardCompat
# ======================================================================


class TestBackwardCompat:
    """String EF.WEAPON pattern defaults to one-handed melee."""

    def test_string_weapon_defaults(self):
        """String EF.WEAPON -> weapon_type=one-handed, range_increment=0."""
        bridge = IntentBridge()
        actor = {
            EF.WEAPON: "longsword",
            "weapon_damage": "1d8+2",
            EF.ATTACK_BONUS: 5,
        }
        result = bridge._resolve_weapon(None, actor)
        weapon, _ = result
        assert weapon.weapon_type == "one-handed"
        assert weapon.range_increment == 0
        assert weapon.is_ranged is False

    def test_no_weapon_gives_unarmed(self):
        """No EF.WEAPON -> unarmed strike with natural weapon_type."""
        bridge = IntentBridge()
        actor = {
            EF.ATTACK_BONUS: 5,
            EF.STR_MOD: 2,
        }
        result = bridge._resolve_weapon(None, actor)
        weapon, _ = result
        assert weapon.damage_dice == "1d3"
        assert weapon.weapon_type == "natural"
        assert weapon.is_ranged is False

    def test_existing_attack_resolution_unchanged(self):
        """Existing melee attack with string weapon still resolves."""
        ws = WorldState(
            ruleset_version="3.5e",
            entities={
                "goblin": {EF.HP_CURRENT: 6, EF.HP_MAX: 6, EF.AC: 15},
                "fighter": {EF.HP_CURRENT: 10, EF.HP_MAX: 10, EF.AC: 18},
            },
        )
        intent = AttackIntent(
            attacker_id="goblin",
            target_id="fighter",
            attack_bonus=3,
            weapon=Weapon(damage_dice="1d6", damage_bonus=1, damage_type="slashing"),
        )
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
        # Should not crash - weapon defaults to one-handed, range_increment=0
        assert len(events) > 0


# ======================================================================
# TestCanaryStillPasses
# ======================================================================


class TestCanaryStillPasses:
    """Existing canary test pattern: B-AMB-04 references remain in source."""

    def test_b_amb_04_in_disarm_source(self):
        """B-AMB-04 and weapon type strings present in resolve_disarm source."""
        import inspect
        source = inspect.getsource(resolve_disarm)
        assert "B-AMB-04" in source
        assert "two-handed" in source
        assert "light" in source
        # Now active, not TODO
        assert "_get_weapon_type" in source
