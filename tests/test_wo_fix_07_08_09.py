"""WO-FIX-07/08/09 -- Combat Maneuver Bug Fixes Tests.

Tests verifying:
- WO-FIX-07: Touch attacks use STANDARD attack size modifier, opposed checks use SPECIAL
- WO-FIX-08: Overrun failure prone determination uses opposed STR check (not flat margin)
- WO-FIX-09: Sunder damage uses actual weapon dice (not hardcoded 1d8)
"""

import pytest
from copy import deepcopy
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import (
    TripIntent, OverrunIntent, SunderIntent, GrappleIntent,
    get_size_modifier, get_standard_attack_size_modifier,
    SIZE_MODIFIER_SCALE, STANDARD_ATTACK_SIZE_MODIFIER,
)
from aidm.core.maneuver_resolver import (
    resolve_trip, resolve_overrun, resolve_sunder, resolve_grapple,
)
from aidm.core.conditions import has_condition


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def large_creature_world():
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "ogre": {
                EF.ENTITY_ID: "ogre", EF.TEAM: "monsters",
                EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: 14,
                EF.DEFEATED: False, EF.POSITION: {"x": 5, "y": 5},
                EF.STR_MOD: 5, EF.DEX_MOD: -1, EF.SIZE_CATEGORY: "large",
                EF.STABILITY_BONUS: 0, "attack_bonus": 6, "bab": 6,
            },
            "human": {
                EF.ENTITY_ID: "human", EF.TEAM: "party",
                EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 15,
                EF.DEFEATED: False, EF.POSITION: {"x": 6, "y": 5},
                EF.STR_MOD: 2, EF.DEX_MOD: 1, EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0, "attack_bonus": 5, "bab": 5,
            },
        },
        active_combat={"initiative_order": ["ogre", "human"], "aoo_used_this_round": []},
    )


@pytest.fixture
def small_creature_world():
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "halfling": {
                EF.ENTITY_ID: "halfling", EF.TEAM: "party",
                EF.HP_CURRENT: 20, EF.HP_MAX: 20, EF.AC: 16,
                EF.DEFEATED: False, EF.POSITION: {"x": 5, "y": 5},
                EF.STR_MOD: -1, EF.DEX_MOD: 3, EF.SIZE_CATEGORY: "small",
                EF.STABILITY_BONUS: 0, "attack_bonus": 3, "bab": 3,
            },
            "goblin": {
                EF.ENTITY_ID: "goblin", EF.TEAM: "monsters",
                EF.HP_CURRENT: 10, EF.HP_MAX: 10, EF.AC: 12,
                EF.DEFEATED: False, EF.POSITION: {"x": 6, "y": 5},
                EF.STR_MOD: 0, EF.DEX_MOD: 1, EF.SIZE_CATEGORY: "small",
                EF.STABILITY_BONUS: 0, "attack_bonus": 1, "bab": 1,
            },
        },
        active_combat={"initiative_order": ["halfling", "goblin"], "aoo_used_this_round": []},
    )


@pytest.fixture
def overrun_world():
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                EF.ENTITY_ID: "attacker", EF.TEAM: "party",
                EF.HP_CURRENT: 40, EF.HP_MAX: 40, EF.AC: 15,
                EF.DEFEATED: False, EF.POSITION: {"x": 5, "y": 5},
                EF.STR_MOD: 2, EF.DEX_MOD: 1, EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0, "attack_bonus": 4, "bab": 4,
            },
            "defender": {
                EF.ENTITY_ID: "defender", EF.TEAM: "monsters",
                EF.HP_CURRENT: 40, EF.HP_MAX: 40, EF.AC: 15,
                EF.DEFEATED: False, EF.POSITION: {"x": 6, "y": 5},
                EF.STR_MOD: 3, EF.DEX_MOD: 1, EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0, "attack_bonus": 4, "bab": 4,
            },
        },
        active_combat={"initiative_order": ["attacker", "defender"], "aoo_used_this_round": []},
    )


@pytest.fixture
def sunder_world():
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.ENTITY_ID: "fighter", EF.TEAM: "party",
                EF.HP_CURRENT: 40, EF.HP_MAX: 40, EF.AC: 16,
                EF.DEFEATED: False, EF.POSITION: {"x": 5, "y": 5},
                EF.STR_MOD: 3, EF.DEX_MOD: 1, EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0, "attack_bonus": 6, "bab": 6,
                EF.WEAPON: {"damage_dice": "2d6", "damage_bonus": 0, "damage_type": "slashing"},
            },
            "orc": {
                EF.ENTITY_ID: "orc", EF.TEAM: "monsters",
                EF.HP_CURRENT: 20, EF.HP_MAX: 20, EF.AC: 14,
                EF.DEFEATED: False, EF.POSITION: {"x": 6, "y": 5},
                EF.STR_MOD: 4, EF.DEX_MOD: 0, EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0, "attack_bonus": 3, "bab": 3,
            },
        },
        active_combat={"initiative_order": ["fighter", "orc"], "aoo_used_this_round": []},
    )


# ==============================================================================
# WO-FIX-07: SIZE MODIFIER TABLE TESTS
# ==============================================================================

class TestStandardAttackSizeModifierTable:

    def test_standard_table_values(self):
        assert STANDARD_ATTACK_SIZE_MODIFIER["fine"] == 8
        assert STANDARD_ATTACK_SIZE_MODIFIER["diminutive"] == 4
        assert STANDARD_ATTACK_SIZE_MODIFIER["tiny"] == 2
        assert STANDARD_ATTACK_SIZE_MODIFIER["small"] == 1
        assert STANDARD_ATTACK_SIZE_MODIFIER["medium"] == 0
        assert STANDARD_ATTACK_SIZE_MODIFIER["large"] == -1
        assert STANDARD_ATTACK_SIZE_MODIFIER["huge"] == -2
        assert STANDARD_ATTACK_SIZE_MODIFIER["gargantuan"] == -4
        assert STANDARD_ATTACK_SIZE_MODIFIER["colossal"] == -8

    def test_special_table_unchanged(self):
        assert SIZE_MODIFIER_SCALE["fine"] == -16
        assert SIZE_MODIFIER_SCALE["small"] == -4
        assert SIZE_MODIFIER_SCALE["medium"] == 0
        assert SIZE_MODIFIER_SCALE["large"] == 4
        assert SIZE_MODIFIER_SCALE["colossal"] == 16

    def test_get_standard_attack_size_modifier_function(self):
        assert get_standard_attack_size_modifier("large") == -1
        assert get_standard_attack_size_modifier("small") == 1
        assert get_standard_attack_size_modifier("medium") == 0

    def test_get_standard_attack_size_modifier_invalid(self):
        with pytest.raises(ValueError, match="Unknown size category"):
            get_standard_attack_size_modifier("invalid")


class TestTripTouchAttackSizeModifier:

    def test_large_creature_trip_touch_attack_uses_minus_1(self, large_creature_world):
        """Large creature trip touch attack: size modifier = -1 (not +4)."""
        for seed in range(200):
            rng = RNGManager(master_seed=seed)
            intent = TripIntent(attacker_id="ogre", target_id="human")
            events, new_state, result = resolve_trip(
                intent=intent, world_state=large_creature_world,
                rng=rng, next_event_id=0, timestamp=0.0,
            )
            touch_events = [e for e in events if e.event_type == "touch_attack_roll"]
            if touch_events:
                touch = touch_events[0].payload
                # Ogre: BAB 6 + STR +5 + STANDARD size -1 = 10
                assert touch["attack_bonus"] == 10, (
                    f"Large creature trip touch attack_bonus should be 10, got {touch['attack_bonus']}"
                )
                break
        else:
            pytest.fail("Could not find seed that produces touch attack event")

    def test_opposed_trip_check_still_uses_special_size(self, large_creature_world):
        """Opposed trip check after touch attack STILL uses special size modifier."""
        for seed in range(200):
            rng = RNGManager(master_seed=seed)
            intent = TripIntent(attacker_id="ogre", target_id="human")
            events, new_state, result = resolve_trip(
                intent=intent, world_state=large_creature_world,
                rng=rng, next_event_id=0, timestamp=0.0,
            )
            touch_events = [e for e in events if e.event_type == "touch_attack_roll"]
            check_events = [e for e in events if e.event_type == "opposed_check"
                           and e.payload.get("check_type") == "trip"]
            if touch_events and touch_events[0].payload["hit"] and check_events:
                check = check_events[0].payload
                # Ogre opposed check: STR +5 + SPECIAL size +4 = +9
                assert check["attacker_modifier"] == 9, (
                    f"Trip opposed check modifier should be 9, got {check['attacker_modifier']}"
                )
                break
        else:
            pytest.fail("Could not find seed with both touch hit and opposed check")


class TestGrappleTouchAttackSizeModifier:

    def test_small_creature_grapple_touch_attack_uses_plus_1(self, small_creature_world):
        """Small creature grapple touch attack: size modifier = +1 (not -4)."""
        for seed in range(200):
            rng = RNGManager(master_seed=seed)
            intent = GrappleIntent(attacker_id="halfling", target_id="goblin")
            events, new_state, result = resolve_grapple(
                intent=intent, world_state=small_creature_world,
                rng=rng, next_event_id=0, timestamp=0.0,
            )
            touch_events = [e for e in events if e.event_type == "touch_attack_roll"]
            if touch_events:
                touch = touch_events[0].payload
                # Halfling: BAB 3 + STR -1 + STANDARD size +1 = 3
                assert touch["attack_bonus"] == 3, (
                    f"Small creature grapple touch attack_bonus should be 3, got {touch['attack_bonus']}"
                )
                break
        else:
            pytest.fail("Could not find seed that produces touch attack event")


# ==============================================================================
# WO-FIX-08: OVERRUN FAILURE OPPOSED STR CHECK
# ==============================================================================

class TestOverrunFailureOpposedStrCheck:

    def test_overrun_failure_defender_wins_str_check_attacker_prone(self, overrun_world):
        """Failed overrun with defender winning opposed STR -> attacker prone."""
        found = False
        for seed in range(500):
            rng = RNGManager(master_seed=seed)
            intent = OverrunIntent(
                attacker_id="attacker", target_id="defender", defender_avoids=False,
            )
            events, new_state, result = resolve_overrun(
                intent=intent, world_state=overrun_world,
                rng=rng, next_event_id=0, timestamp=0.0,
            )
            failure_events = [e for e in events if e.event_type == "overrun_failure"]
            if failure_events:
                payload = failure_events[0].payload
                if payload["attacker_prone"]:
                    assert "prone_check" in payload
                    pc = payload["prone_check"]
                    assert pc["defender_total"] >= pc["attacker_total"]
                    assert has_condition(new_state, "attacker", "prone")
                    found = True
                    break
        assert found, "Could not find seed where overrun fails and attacker goes prone"

    def test_overrun_failure_attacker_wins_str_check_not_prone(self, overrun_world):
        """Failed overrun with defender losing opposed STR -> attacker not prone."""
        found = False
        for seed in range(500):
            rng = RNGManager(master_seed=seed)
            intent = OverrunIntent(
                attacker_id="attacker", target_id="defender", defender_avoids=False,
            )
            events, new_state, result = resolve_overrun(
                intent=intent, world_state=overrun_world,
                rng=rng, next_event_id=0, timestamp=0.0,
            )
            failure_events = [e for e in events if e.event_type == "overrun_failure"]
            if failure_events:
                payload = failure_events[0].payload
                if not payload["attacker_prone"]:
                    assert "prone_check" in payload
                    pc = payload["prone_check"]
                    assert pc["attacker_total"] > pc["defender_total"]
                    assert not has_condition(new_state, "attacker", "prone")
                    found = True
                    break
        assert found, "Could not find seed where overrun fails and attacker is not prone"

    def test_overrun_failure_prone_check_uses_special_size(self, overrun_world):
        """Prone check in overrun failure uses SPECIAL size modifier."""
        ws = deepcopy(overrun_world)
        ws.entities["attacker"][EF.SIZE_CATEGORY] = "large"
        found = False
        for seed in range(500):
            rng = RNGManager(master_seed=seed)
            intent = OverrunIntent(
                attacker_id="attacker", target_id="defender", defender_avoids=False,
            )
            events, new_state, result = resolve_overrun(
                intent=intent, world_state=ws,
                rng=rng, next_event_id=0, timestamp=0.0,
            )
            failure_events = [e for e in events if e.event_type == "overrun_failure"]
            if failure_events:
                payload = failure_events[0].payload
                assert "prone_check" in payload
                pc = payload["prone_check"]
                # Large attacker: SPECIAL size = +4 (not standard -1)
                assert pc["attacker_special_size_mod"] == 4, (
                    f"Prone check should use SPECIAL size mod +4 for large, got {pc['attacker_special_size_mod']}"
                )
                assert pc["defender_special_size_mod"] == 0
                found = True
                break
        assert found, "Could not find seed where overrun fails"


# ==============================================================================
# WO-FIX-09: SUNDER DAMAGE USES WEAPON DICE
# ==============================================================================

class TestSunderDamageUsesWeaponDice:

    def test_sunder_uses_weapon_damage_dice(self, sunder_world):
        """Sunder damage uses 2d6 from weapon data, not hardcoded 1d8."""
        for seed in range(200):
            rng = RNGManager(master_seed=seed)
            intent = SunderIntent(attacker_id="fighter", target_id="orc", target_item="weapon")
            events, new_state, result = resolve_sunder(
                intent=intent, world_state=sunder_world,
                rng=rng, next_event_id=0, timestamp=0.0,
            )
            if result.success:
                success_events = [e for e in events if e.event_type == "sunder_success"]
                assert len(success_events) == 1
                payload = success_events[0].payload
                assert payload["damage_dice"] == "2d6", (
                    f"Sunder should use weapon damage_dice 2d6, got {payload['damage_dice']}"
                )
                assert len(payload["damage_rolls"]) == 2
                for r in payload["damage_rolls"]:
                    assert 1 <= r <= 6
                assert payload["damage_roll"] == sum(payload["damage_rolls"])
                assert payload["damage_bonus"] == 3  # fighter STR_MOD
                break
        else:
            pytest.fail("Could not find seed where sunder succeeds")

    def test_sunder_without_weapon_data_falls_back_to_1d8(self, sunder_world):
        """Sunder without weapon data on attacker falls back to 1d8."""
        ws = deepcopy(sunder_world)
        del ws.entities["fighter"][EF.WEAPON]
        for seed in range(200):
            rng = RNGManager(master_seed=seed)
            intent = SunderIntent(attacker_id="fighter", target_id="orc", target_item="weapon")
            events, new_state, result = resolve_sunder(
                intent=intent, world_state=ws,
                rng=rng, next_event_id=0, timestamp=0.0,
            )
            if result.success:
                success_events = [e for e in events if e.event_type == "sunder_success"]
                payload = success_events[0].payload
                assert payload["damage_dice"] == "1d8"
                assert len(payload["damage_rolls"]) == 1
                break
        else:
            pytest.fail("Could not find seed where sunder succeeds")

    def test_sunder_str_modifier_applies(self, sunder_world):
        """STR modifier applies to sunder damage per normal melee rules."""
        for seed in range(200):
            rng = RNGManager(master_seed=seed)
            intent = SunderIntent(attacker_id="fighter", target_id="orc", target_item="weapon")
            events, new_state, result = resolve_sunder(
                intent=intent, world_state=sunder_world,
                rng=rng, next_event_id=0, timestamp=0.0,
            )
            if result.success:
                success_events = [e for e in events if e.event_type == "sunder_success"]
                payload = success_events[0].payload
                assert payload["damage_bonus"] == 3
                expected = max(0, sum(payload["damage_rolls"]) + 3)
                assert payload["total_damage"] == expected
                break
        else:
            pytest.fail("Could not find seed where sunder succeeds")
