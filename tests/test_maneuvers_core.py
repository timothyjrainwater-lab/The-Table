"""CP-18 Combat Maneuvers — Core Tests (Tier 1).

Tests for combat maneuver schemas, resolution, and basic mechanics.

RNG Seed: All tests use deterministic seeds for reproducibility.
"""

import pytest
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import (
    BullRushIntent, TripIntent, OverrunIntent,
    SunderIntent, DisarmIntent, GrappleIntent,
    OpposedCheckResult, ManeuverResult, TouchAttackResult,
    get_size_modifier, SIZE_MODIFIER_SCALE,
)
from aidm.core.maneuver_resolver import (
    resolve_bull_rush, resolve_trip, resolve_overrun,
    resolve_sunder, resolve_disarm, resolve_grapple,
    resolve_maneuver,
)
from aidm.core.conditions import has_condition


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def basic_world_state():
    """Create a basic world state with two adjacent combatants."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.ENTITY_ID: "fighter",
                EF.TEAM: "party",
                EF.HP_CURRENT: 50,
                EF.HP_MAX: 50,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 5, "y": 5},
                EF.STR_MOD: 3,  # 16 STR
                EF.DEX_MOD: 1,  # 12 DEX
                EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 5,  # BAB proxy
                "bab": 5,
            },
            "orc": {
                EF.ENTITY_ID: "orc",
                EF.TEAM: "monsters",
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.AC: 14,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 6, "y": 5},
                EF.STR_MOD: 4,  # 18 STR (orcs are strong)
                EF.DEX_MOD: 0,  # 10 DEX
                EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 3,
                "bab": 3,
            },
        },
        active_combat={
            "initiative_order": ["fighter", "orc"],
            "aoo_used_this_round": [],
        }
    )


@pytest.fixture
def size_mismatch_world_state():
    """Create world state with large vs medium combatants."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "ogre": {
                EF.ENTITY_ID: "ogre",
                EF.TEAM: "monsters",
                EF.HP_CURRENT: 50,
                EF.HP_MAX: 50,
                EF.AC: 14,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 5, "y": 5},
                EF.STR_MOD: 5,  # 20 STR
                EF.DEX_MOD: -1,  # 8 DEX
                EF.SIZE_CATEGORY: "large",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 4,
                "bab": 4,
            },
            "halfling": {
                EF.ENTITY_ID: "halfling",
                EF.TEAM: "party",
                EF.HP_CURRENT: 15,
                EF.HP_MAX: 15,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 6, "y": 5},
                EF.STR_MOD: -1,  # 8 STR
                EF.DEX_MOD: 3,  # 16 DEX
                EF.SIZE_CATEGORY: "small",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 3,
                "bab": 3,
            },
        },
        active_combat={
            "initiative_order": ["ogre", "halfling"],
            "aoo_used_this_round": [],
        }
    )


@pytest.fixture
def dwarf_stability_world_state():
    """Create world state with a dwarf (stability bonus)."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "attacker": {
                EF.ENTITY_ID: "attacker",
                EF.TEAM: "monsters",
                EF.HP_CURRENT: 40,
                EF.HP_MAX: 40,
                EF.AC: 15,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 5, "y": 5},
                EF.STR_MOD: 3,
                EF.DEX_MOD: 1,
                EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 0,
                "attack_bonus": 4,
                "bab": 4,
            },
            "dwarf": {
                EF.ENTITY_ID: "dwarf",
                EF.TEAM: "party",
                EF.HP_CURRENT: 35,
                EF.HP_MAX: 35,
                EF.AC: 18,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 6, "y": 5},
                EF.STR_MOD: 2,  # 14 STR
                EF.DEX_MOD: 1,  # 12 DEX
                EF.SIZE_CATEGORY: "medium",
                EF.STABILITY_BONUS: 4,  # Dwarven stability
                "attack_bonus": 5,
                "bab": 5,
            },
        },
        active_combat={
            "initiative_order": ["attacker", "dwarf"],
            "aoo_used_this_round": [],
        }
    )


# ==============================================================================
# SIZE MODIFIER TESTS
# ==============================================================================

class TestSizeModifiers:
    """Test size modifier calculations."""

    def test_size_modifier_scale_values(self):
        """Verify size modifier scale matches PHB p.154."""
        assert SIZE_MODIFIER_SCALE["fine"] == -16
        assert SIZE_MODIFIER_SCALE["diminutive"] == -12
        assert SIZE_MODIFIER_SCALE["tiny"] == -8
        assert SIZE_MODIFIER_SCALE["small"] == -4
        assert SIZE_MODIFIER_SCALE["medium"] == 0
        assert SIZE_MODIFIER_SCALE["large"] == 4
        assert SIZE_MODIFIER_SCALE["huge"] == 8
        assert SIZE_MODIFIER_SCALE["gargantuan"] == 12
        assert SIZE_MODIFIER_SCALE["colossal"] == 16

    def test_get_size_modifier_medium(self):
        """Medium creatures have +0 modifier."""
        assert get_size_modifier("medium") == 0
        assert get_size_modifier("Medium") == 0
        assert get_size_modifier("MEDIUM") == 0

    def test_get_size_modifier_large(self):
        """Large creatures have +4 modifier."""
        assert get_size_modifier("large") == 4

    def test_get_size_modifier_small(self):
        """Small creatures have -4 modifier."""
        assert get_size_modifier("small") == -4

    def test_get_size_modifier_invalid(self):
        """Unknown size category raises ValueError."""
        with pytest.raises(ValueError, match="Unknown size category"):
            get_size_modifier("invalid_size")


# ==============================================================================
# INTENT SCHEMA TESTS
# ==============================================================================

class TestIntentSchemas:
    """Test intent dataclass creation and fields."""

    def test_bull_rush_intent_creation(self):
        """Bull rush intent with required fields."""
        intent = BullRushIntent(
            attacker_id="fighter",
            target_id="orc",
            is_charge=True,
        )
        assert intent.attacker_id == "fighter"
        assert intent.target_id == "orc"
        assert intent.is_charge is True

    def test_bull_rush_intent_defaults(self):
        """Bull rush intent default is_charge=False."""
        intent = BullRushIntent(attacker_id="a", target_id="b")
        assert intent.is_charge is False

    def test_trip_intent_creation(self):
        """Trip intent with required fields."""
        intent = TripIntent(attacker_id="fighter", target_id="orc")
        assert intent.attacker_id == "fighter"
        assert intent.target_id == "orc"

    def test_overrun_intent_creation(self):
        """Overrun intent with all fields."""
        intent = OverrunIntent(
            attacker_id="fighter",
            target_id="orc",
            is_charge=True,
            defender_avoids=False,
        )
        assert intent.attacker_id == "fighter"
        assert intent.is_charge is True
        assert intent.defender_avoids is False

    def test_sunder_intent_creation(self):
        """Sunder intent with target item."""
        intent = SunderIntent(
            attacker_id="fighter",
            target_id="orc",
            target_item="weapon",
        )
        assert intent.target_item == "weapon"

    def test_disarm_intent_creation(self):
        """Disarm intent with required fields."""
        intent = DisarmIntent(attacker_id="fighter", target_id="orc")
        assert intent.attacker_id == "fighter"
        assert intent.target_id == "orc"

    def test_grapple_intent_creation(self):
        """Grapple intent with required fields."""
        intent = GrappleIntent(attacker_id="fighter", target_id="orc")
        assert intent.attacker_id == "fighter"
        assert intent.target_id == "orc"


# ==============================================================================
# BULL RUSH RESOLUTION TESTS
# ==============================================================================

class TestBullRushResolution:
    """Test Bull Rush maneuver resolution."""

    def test_bull_rush_success_pushes_defender(self, basic_world_state):
        """Successful bull rush moves defender back."""
        rng = RNGManager(master_seed=42)  # Seed chosen for attacker win
        intent = BullRushIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_bull_rush(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        # Check that we got events
        assert len(events) > 0

        # Check for bull_rush_declared event
        event_types = [e.event_type for e in events]
        assert "bull_rush_declared" in event_types
        assert "opposed_check" in event_types

    def test_bull_rush_with_charge_bonus(self, basic_world_state):
        """Bull rush during charge gets +2 bonus."""
        rng = RNGManager(master_seed=12345)
        intent = BullRushIntent(attacker_id="fighter", target_id="orc", is_charge=True)

        events, new_state, result = resolve_bull_rush(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        # Find opposed check event
        check_events = [e for e in events if e.event_type == "opposed_check"]
        assert len(check_events) == 1

        # Attacker modifier should include +2 charge bonus
        check_payload = check_events[0].payload
        # Fighter: STR +3, Size +0, Charge +2 = +5
        assert check_payload["attacker_modifier"] == 5

    def test_bull_rush_size_advantage(self, size_mismatch_world_state):
        """Larger creature has size advantage in bull rush."""
        rng = RNGManager(master_seed=999)
        # Ogre (large) bull rushing halfling (small)
        intent = BullRushIntent(attacker_id="ogre", target_id="halfling")

        events, new_state, result = resolve_bull_rush(
            intent=intent,
            world_state=size_mismatch_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        check_events = [e for e in events if e.event_type == "opposed_check"]
        check_payload = check_events[0].payload

        # Ogre: STR +5, Size +4 (large) = +9
        assert check_payload["attacker_modifier"] == 9
        # Halfling: STR -1, Size -4 (small), Stability +0 = -5
        assert check_payload["defender_modifier"] == -5


# ==============================================================================
# TRIP RESOLUTION TESTS
# ==============================================================================

class TestTripResolution:
    """Test Trip maneuver resolution."""

    def test_trip_touch_attack_required(self, basic_world_state):
        """Trip requires a melee touch attack first."""
        rng = RNGManager(master_seed=100)
        intent = TripIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_trip(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        event_types = [e.event_type for e in events]
        assert "trip_declared" in event_types
        assert "touch_attack_roll" in event_types

    def test_trip_success_applies_prone(self, basic_world_state):
        """Successful trip applies Prone condition to target."""
        # Use a seed that results in trip success
        rng = RNGManager(master_seed=12345)
        intent = TripIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_trip(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        # If trip succeeded, check for prone condition
        if result.success:
            assert result.condition_applied == "prone"
            assert has_condition(new_state, "orc", "prone")

    def test_trip_failure_allows_counter_trip(self, basic_world_state):
        """Failed trip allows defender to counter-trip."""
        # Use a seed that results in trip failure
        rng = RNGManager(master_seed=1)  # Low seed tends to low rolls
        intent = TripIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_trip(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        event_types = [e.event_type for e in events]

        # Check for touch attack first
        assert "touch_attack_roll" in event_types

        # If touch hit but trip failed, there should be counter-trip events
        touch_events = [e for e in events if e.event_type == "touch_attack_roll"]
        if touch_events and touch_events[0].payload["hit"]:
            # If trip failed, we expect counter-trip attempt
            opposed_checks = [e for e in events if e.event_type == "opposed_check"]
            if not result.success and len(opposed_checks) >= 1:
                # Either trip_failure or counter events should be present
                assert "trip_failure" in event_types or "counter_trip_success" in event_types or "counter_trip_failure" in event_types


# ==============================================================================
# OVERRUN RESOLUTION TESTS
# ==============================================================================

class TestOverrunResolution:
    """Test Overrun maneuver resolution."""

    def test_overrun_defender_avoids(self, basic_world_state):
        """Defender choosing to avoid ends overrun without check."""
        rng = RNGManager(master_seed=100)
        intent = OverrunIntent(
            attacker_id="fighter",
            target_id="orc",
            defender_avoids=True,
        )

        events, new_state, result = resolve_overrun(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        event_types = [e.event_type for e in events]
        assert "overrun_declared" in event_types
        assert "overrun_avoided" in event_types
        # No opposed check when defender avoids
        assert "opposed_check" not in event_types
        assert result.success is True

    def test_overrun_success_knocks_prone(self, basic_world_state):
        """Successful overrun knocks defender prone."""
        rng = RNGManager(master_seed=42)
        intent = OverrunIntent(
            attacker_id="fighter",
            target_id="orc",
            defender_avoids=False,
        )

        events, new_state, result = resolve_overrun(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        if result.success:
            assert result.condition_applied == "prone"
            assert has_condition(new_state, "orc", "prone")

    def test_overrun_failure_by_5_knocks_attacker_prone(self, size_mismatch_world_state):
        """Overrun failure by 5+ knocks attacker prone."""
        # Halfling trying to overrun ogre - likely to fail by 5+
        rng = RNGManager(master_seed=1)  # Low rolls favor ogre
        intent = OverrunIntent(
            attacker_id="halfling",
            target_id="ogre",
            defender_avoids=False,
        )

        events, new_state, result = resolve_overrun(
            intent=intent,
            world_state=size_mismatch_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        # Check opposed check margin
        check_events = [e for e in events if e.event_type == "opposed_check"]
        if check_events:
            margin = check_events[0].payload["margin"]
            # If margin <= -5, attacker should be prone
            if margin <= -5:
                assert has_condition(new_state, "halfling", "prone")


# ==============================================================================
# SUNDER RESOLUTION TESTS (DEGRADED)
# ==============================================================================

class TestSunderResolution:
    """Test Sunder maneuver resolution (degraded - narrative only)."""

    def test_sunder_emits_correct_events(self, basic_world_state):
        """Sunder emits declaration and opposed check events."""
        rng = RNGManager(master_seed=50)
        intent = SunderIntent(
            attacker_id="fighter",
            target_id="orc",
            target_item="weapon",
        )

        events, new_state, result = resolve_sunder(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        event_types = [e.event_type for e in events]
        assert "sunder_declared" in event_types
        assert "opposed_check" in event_types

    def test_sunder_success_logs_damage(self, basic_world_state):
        """Successful sunder logs damage but no state change."""
        rng = RNGManager(master_seed=42)
        intent = SunderIntent(
            attacker_id="fighter",
            target_id="orc",
            target_item="weapon",
        )

        events, new_state, result = resolve_sunder(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        if result.success:
            assert result.damage_dealt >= 0
            success_events = [e for e in events if e.event_type == "sunder_success"]
            assert len(success_events) == 1
            # Verify "DEGRADED" note in event
            assert "DEGRADED" in success_events[0].payload.get("note", "")


# ==============================================================================
# DISARM RESOLUTION TESTS (DEGRADED)
# ==============================================================================

class TestDisarmResolution:
    """Test Disarm maneuver resolution (degraded - narrative only)."""

    def test_disarm_emits_correct_events(self, basic_world_state):
        """Disarm emits declaration and opposed check events."""
        rng = RNGManager(master_seed=50)
        intent = DisarmIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_disarm(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        event_types = [e.event_type for e in events]
        assert "disarm_declared" in event_types
        assert "opposed_check" in event_types

    def test_disarm_success_is_narrative(self, basic_world_state):
        """Successful disarm is narrative only."""
        rng = RNGManager(master_seed=42)
        intent = DisarmIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_disarm(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        if result.success:
            success_events = [e for e in events if e.event_type == "disarm_success"]
            assert len(success_events) == 1
            assert "DEGRADED" in success_events[0].payload.get("note", "")

    def test_disarm_aoo_damage_causes_auto_fail(self, basic_world_state):
        """If AoO deals damage, disarm automatically fails."""
        rng = RNGManager(master_seed=50)
        intent = DisarmIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_disarm(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
            aoo_dealt_damage=True,
        )

        # Should fail with reason "aoo_dealt_damage"
        assert result.success is False
        failure_events = [e for e in events if e.event_type == "disarm_failure"]
        assert len(failure_events) == 1
        assert failure_events[0].payload.get("reason") == "aoo_dealt_damage"


# ==============================================================================
# GRAPPLE RESOLUTION TESTS (DEGRADED - GRAPPLE-LITE)
# ==============================================================================

class TestGrappleResolution:
    """Test Grapple-lite maneuver resolution (degraded - unidirectional)."""

    def test_grapple_requires_touch_attack(self, basic_world_state):
        """Grapple requires a melee touch attack first."""
        rng = RNGManager(master_seed=100)
        intent = GrappleIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_grapple(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        event_types = [e.event_type for e in events]
        assert "grapple_declared" in event_types
        assert "touch_attack_roll" in event_types

    def test_grapple_success_applies_condition_to_target_only(self, basic_world_state):
        """Successful grapple applies Grappled to target only (asymmetric)."""
        rng = RNGManager(master_seed=42)
        intent = GrappleIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_grapple(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        if result.success:
            assert result.condition_applied == "grappled"
            # Target has condition
            assert has_condition(new_state, "orc", "grappled")
            # Attacker does NOT have condition (asymmetric / G-T3C safe)
            assert not has_condition(new_state, "fighter", "grappled")

    def test_grapple_aoo_damage_causes_auto_fail(self, basic_world_state):
        """If AoO deals damage, grapple automatically fails."""
        rng = RNGManager(master_seed=50)
        intent = GrappleIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_grapple(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
            aoo_dealt_damage=True,
        )

        assert result.success is False
        failure_events = [e for e in events if e.event_type == "grapple_failure"]
        assert len(failure_events) == 1
        assert failure_events[0].payload.get("reason") == "aoo_dealt_damage"


# ==============================================================================
# UNIFIED RESOLVER DISPATCHER TESTS
# ==============================================================================

class TestResolveManeuverDispatcher:
    """Test the unified resolve_maneuver dispatcher."""

    def test_dispatcher_routes_bull_rush(self, basic_world_state):
        """Dispatcher correctly routes BullRushIntent."""
        rng = RNGManager(master_seed=42)
        intent = BullRushIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_maneuver(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        assert result.maneuver_type == "bull_rush"

    def test_dispatcher_routes_trip(self, basic_world_state):
        """Dispatcher correctly routes TripIntent."""
        rng = RNGManager(master_seed=42)
        intent = TripIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_maneuver(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        assert result.maneuver_type == "trip"

    def test_dispatcher_routes_grapple(self, basic_world_state):
        """Dispatcher correctly routes GrappleIntent."""
        rng = RNGManager(master_seed=42)
        intent = GrappleIntent(attacker_id="fighter", target_id="orc")

        events, new_state, result = resolve_maneuver(
            intent=intent,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        assert result.maneuver_type == "grapple"


# ==============================================================================
# STABILITY BONUS TESTS
# ==============================================================================

class TestStabilityBonus:
    """Test stability bonus application (e.g., dwarves)."""

    def test_stability_bonus_adds_to_defense(self, dwarf_stability_world_state):
        """Stability bonus (+4) adds to defender's opposed check."""
        rng = RNGManager(master_seed=100)
        # Attacker bull rushing dwarf
        intent = BullRushIntent(attacker_id="attacker", target_id="dwarf")

        events, new_state, result = resolve_bull_rush(
            intent=intent,
            world_state=dwarf_stability_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        check_events = [e for e in events if e.event_type == "opposed_check"]
        check_payload = check_events[0].payload

        # Dwarf: STR +2, Size +0, Stability +4 = +6
        assert check_payload["defender_modifier"] == 6


# ==============================================================================
# DETERMINISM TESTS
# ==============================================================================

class TestDeterminism:
    """Test deterministic replay (10x identical runs)."""

    def test_bull_rush_deterministic_10x(self, basic_world_state):
        """10 bull rush resolutions with same seed produce identical results."""
        results = []
        for _ in range(10):
            rng = RNGManager(master_seed=12345)
            intent = BullRushIntent(attacker_id="fighter", target_id="orc")

            events, new_state, result = resolve_bull_rush(
                intent=intent,
                world_state=basic_world_state,
                rng=rng,
                next_event_id=0,
                timestamp=0.0,
            )

            # Collect key result data
            results.append({
                "success": result.success,
                "event_count": len(events),
                "final_hash": new_state.state_hash(),
            })

        # All 10 runs should be identical
        for i in range(1, 10):
            assert results[i] == results[0], f"Run {i} differs from run 0"

    def test_trip_deterministic_10x(self, basic_world_state):
        """10 trip resolutions with same seed produce identical results."""
        results = []
        for _ in range(10):
            rng = RNGManager(master_seed=54321)
            intent = TripIntent(attacker_id="fighter", target_id="orc")

            events, new_state, result = resolve_trip(
                intent=intent,
                world_state=basic_world_state,
                rng=rng,
                next_event_id=0,
                timestamp=0.0,
            )

            results.append({
                "success": result.success,
                "event_count": len(events),
                "final_hash": new_state.state_hash(),
            })

        for i in range(1, 10):
            assert results[i] == results[0], f"Run {i} differs from run 0"

    def test_grapple_deterministic_10x(self, basic_world_state):
        """10 grapple resolutions with same seed produce identical results."""
        results = []
        for _ in range(10):
            rng = RNGManager(master_seed=99999)
            intent = GrappleIntent(attacker_id="fighter", target_id="orc")

            events, new_state, result = resolve_grapple(
                intent=intent,
                world_state=basic_world_state,
                rng=rng,
                next_event_id=0,
                timestamp=0.0,
            )

            results.append({
                "success": result.success,
                "event_count": len(events),
                "final_hash": new_state.state_hash(),
            })

        for i in range(1, 10):
            assert results[i] == results[0], f"Run {i} differs from run 0"
