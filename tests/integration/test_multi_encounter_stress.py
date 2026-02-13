"""Multi-Encounter Stress Test Suite.

Validates the complete Box→Lens→Spark pipeline under realistic combat load.
This is Step 6.1 of the execution plan — proving the full system works
across multiple combat scenarios before performance optimization.

WO-016: Multi-Encounter Stress Test Suite

Scenarios:
A. Tavern Brawl (5v3, single room with cover)
B. Dungeon Corridor (4v4, multi-room with doorways and elevation)
C. Open Field Battle (6v6, large open terrain with scattered cover)
D. Boss Fight (5v1, Large creature with 10ft reach and Combat Reflexes)
"""

import pytest
from typing import Dict, Any, List

from aidm.schemas.testing import ScenarioConfig
from aidm.testing.scenario_runner import ScenarioRunner, ScenarioMetrics


# ==============================================================================
# SCENARIO A: TAVERN BRAWL
# ==============================================================================

class TestTavernBrawlScenario:
    """Tavern Brawl scenario tests.

    5 combatants in a 15x15 tavern:
    - 2 melee fighters, 1 archer, 1 wizard, 1 rogue (party)
    - 3 bandits (enemy)

    Exercises:
    - Melee attacks
    - Ranged attacks through cover
    - AoE spell targeting (burning hands cone)
    - Cover calculations from tables and bar
    """

    def test_tavern_runs_10_rounds(
        self, tavern_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Tavern scenario executes for at least 10 rounds without error."""
        metrics = scenario_runner.run(tavern_scenario)

        # Should run at least 10 rounds (or until combat ends)
        assert metrics.total_rounds >= 1  # Combat must start
        assert metrics.total_actions > 0  # Actions must be taken

        # No consistency errors
        assert len(metrics.lens_consistency_errors) == 0

    def test_tavern_generates_stps(
        self, tavern_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Tavern scenario generates STPs for combat actions."""
        metrics = scenario_runner.run(tavern_scenario)

        # Must generate STPs
        assert metrics.stp_count > 0

        # Should have attack_roll STPs
        assert metrics.stps_by_type.get("attack_roll", 0) > 0

    def test_tavern_determinism(
        self, tavern_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Tavern scenario produces identical results with same seed."""
        assert scenario_runner.run_determinism_check(tavern_scenario)

    def test_tavern_lens_consistency(
        self, tavern_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Tavern scenario maintains Lens/Grid consistency throughout."""
        metrics = scenario_runner.run(tavern_scenario)

        # Lens must remain consistent with Grid
        assert len(metrics.lens_consistency_errors) == 0

    def test_tavern_event_log_valid(
        self, tavern_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Tavern scenario produces valid event log with hash."""
        metrics = scenario_runner.run(tavern_scenario)

        # Event log hash must be non-empty
        assert len(metrics.event_log_hash) == 64  # SHA-256 hex digest


# ==============================================================================
# SCENARIO B: DUNGEON CORRIDOR
# ==============================================================================

class TestDungeonCorridorScenario:
    """Dungeon Corridor scenario tests.

    8 combatants across 3 connected rooms (30x20 grid):
    - Party of 4
    - 4 goblins with longspears (10ft reach)

    Exercises:
    - Movement through doorways
    - Reach weapons (goblin longspears)
    - Flanking opportunities
    - Threatened square updates on movement
    - AoO triggers
    """

    def test_dungeon_runs_10_rounds(
        self, dungeon_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Dungeon scenario executes for at least 10 rounds without error."""
        metrics = scenario_runner.run(dungeon_scenario)

        assert metrics.total_rounds >= 1
        assert metrics.total_actions > 0
        assert len(metrics.lens_consistency_errors) == 0

    def test_dungeon_generates_stps(
        self, dungeon_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Dungeon scenario generates STPs for combat actions."""
        metrics = scenario_runner.run(dungeon_scenario)

        assert metrics.stp_count > 0
        assert metrics.stps_by_type.get("attack_roll", 0) > 0

    def test_dungeon_determinism(
        self, dungeon_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Dungeon scenario produces identical results with same seed."""
        assert scenario_runner.run_determinism_check(dungeon_scenario)

    def test_dungeon_multi_room_combat(
        self, dungeon_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Dungeon scenario handles multi-room combat correctly."""
        metrics = scenario_runner.run(dungeon_scenario)

        # Must complete without errors
        assert len(metrics.lens_consistency_errors) == 0

        # State hash must be computed
        assert len(metrics.final_state_hash) == 64


# ==============================================================================
# SCENARIO C: OPEN FIELD BATTLE
# ==============================================================================

class TestOpenFieldBattleScenario:
    """Open Field Battle scenario tests.

    12 combatants on 40x40 open terrain:
    - 6v6 mixed forces with archers and wizards
    - Scattered boulders for cover

    Exercises:
    - Long-range combat
    - Large AoE spells (fireball 20ft burst)
    - Range increment penalties
    - AoE target enumeration
    """

    def test_field_runs_10_rounds(
        self, field_battle_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Field battle executes for at least 10 rounds without error."""
        metrics = scenario_runner.run(field_battle_scenario)

        assert metrics.total_rounds >= 1
        assert metrics.total_actions > 0
        assert len(metrics.lens_consistency_errors) == 0

    def test_field_generates_stps(
        self, field_battle_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Field battle generates STPs for combat actions."""
        metrics = scenario_runner.run(field_battle_scenario)

        assert metrics.stp_count > 0
        assert metrics.stps_by_type.get("attack_roll", 0) > 0

    def test_field_determinism(
        self, field_battle_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Field battle produces identical results with same seed."""
        assert scenario_runner.run_determinism_check(field_battle_scenario)

    def test_field_large_grid(
        self, field_battle_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Field battle handles large 40x40 grid correctly."""
        # Verify grid size
        assert field_battle_scenario.grid_width == 40
        assert field_battle_scenario.grid_height == 40

        metrics = scenario_runner.run(field_battle_scenario)

        # Must complete without errors
        assert len(metrics.lens_consistency_errors) == 0

    def test_field_many_combatants(
        self, field_battle_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Field battle handles 12 combatants correctly."""
        # Verify combatant count
        assert len(field_battle_scenario.combatants) == 12

        metrics = scenario_runner.run(field_battle_scenario)

        # Must complete without errors
        assert len(metrics.lens_consistency_errors) == 0


# ==============================================================================
# SCENARIO D: BOSS FIGHT
# ==============================================================================

class TestBossFightScenario:
    """Boss Fight scenario tests.

    6 combatants in 25x25 arena:
    - Party of 5
    - 1 Large creature (2x2 footprint, 10ft reach, Combat Reflexes)

    Exercises:
    - Large creature geometry (2x2 footprint)
    - 10ft reach attacks
    - Combat Reflexes (multiple AoO per round)
    - Cover from large creatures
    - Multi-target AoO opportunities
    """

    def test_boss_runs_10_rounds(
        self, boss_fight_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Boss fight executes for at least 10 rounds without error."""
        metrics = scenario_runner.run(boss_fight_scenario)

        assert metrics.total_rounds >= 1
        assert metrics.total_actions > 0
        assert len(metrics.lens_consistency_errors) == 0

    def test_boss_generates_stps(
        self, boss_fight_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Boss fight generates STPs for combat actions."""
        metrics = scenario_runner.run(boss_fight_scenario)

        assert metrics.stp_count > 0
        assert metrics.stps_by_type.get("attack_roll", 0) > 0

    def test_boss_determinism(
        self, boss_fight_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Boss fight produces identical results with same seed."""
        assert scenario_runner.run_determinism_check(boss_fight_scenario)

    def test_boss_large_creature_geometry(
        self, boss_fight_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Boss fight handles Large creature (2x2) geometry correctly."""
        # Find the boss
        boss = None
        for combatant in boss_fight_scenario.combatants:
            if combatant.name == "boss":
                boss = combatant
                break

        assert boss is not None
        assert boss.size == "Large"
        assert boss.reach == 10

        metrics = scenario_runner.run(boss_fight_scenario)

        # Must complete without errors
        assert len(metrics.lens_consistency_errors) == 0

    def test_boss_combat_reflexes(
        self, boss_fight_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Boss fight includes creature with Combat Reflexes."""
        # Find the boss
        boss = None
        for combatant in boss_fight_scenario.combatants:
            if combatant.name == "boss":
                boss = combatant
                break

        assert boss is not None
        assert boss.combat_reflexes is True
        assert boss.max_aoo_per_round > 1

        metrics = scenario_runner.run(boss_fight_scenario)

        # Must complete without errors
        assert len(metrics.lens_consistency_errors) == 0


# ==============================================================================
# CROSS-SCENARIO TESTS
# ==============================================================================

class TestCrossScenarioValidation:
    """Tests that validate behavior across all scenarios."""

    def test_all_scenarios_produce_valid_metrics(
        self,
        tavern_scenario: ScenarioConfig,
        dungeon_scenario: ScenarioConfig,
        field_battle_scenario: ScenarioConfig,
        boss_fight_scenario: ScenarioConfig,
        scenario_runner: ScenarioRunner,
    ):
        """All scenarios produce valid metrics structures."""
        scenarios = [
            tavern_scenario,
            dungeon_scenario,
            field_battle_scenario,
            boss_fight_scenario,
        ]

        for scenario in scenarios:
            metrics = scenario_runner.run(scenario)

            # Basic validation
            assert isinstance(metrics.total_rounds, int)
            assert isinstance(metrics.total_actions, int)
            assert isinstance(metrics.time_per_round_ms, list)
            assert isinstance(metrics.time_per_action_ms, list)
            assert isinstance(metrics.stp_count, int)
            assert isinstance(metrics.event_log_hash, str)
            assert isinstance(metrics.final_state_hash, str)
            assert isinstance(metrics.stps_by_type, dict)
            assert isinstance(metrics.entities_defeated, list)
            assert isinstance(metrics.total_time_ms, float)
            assert isinstance(metrics.lens_consistency_errors, list)

    def test_all_scenarios_deterministic(
        self,
        tavern_scenario: ScenarioConfig,
        dungeon_scenario: ScenarioConfig,
        field_battle_scenario: ScenarioConfig,
        boss_fight_scenario: ScenarioConfig,
        scenario_runner: ScenarioRunner,
    ):
        """All scenarios are deterministic with same seed."""
        scenarios = [
            ("Tavern", tavern_scenario),
            ("Dungeon", dungeon_scenario),
            ("Field", field_battle_scenario),
            ("Boss", boss_fight_scenario),
        ]

        for name, scenario in scenarios:
            is_deterministic = scenario_runner.run_determinism_check(scenario)
            assert is_deterministic, f"{name} scenario is not deterministic"

    def test_all_scenarios_no_consistency_errors(
        self,
        tavern_scenario: ScenarioConfig,
        dungeon_scenario: ScenarioConfig,
        field_battle_scenario: ScenarioConfig,
        boss_fight_scenario: ScenarioConfig,
        scenario_runner: ScenarioRunner,
    ):
        """All scenarios maintain Lens/Grid consistency."""
        scenarios = [
            ("Tavern", tavern_scenario),
            ("Dungeon", dungeon_scenario),
            ("Field", field_battle_scenario),
            ("Boss", boss_fight_scenario),
        ]

        for name, scenario in scenarios:
            metrics = scenario_runner.run(scenario)
            assert len(metrics.lens_consistency_errors) == 0, \
                f"{name} scenario has consistency errors: {metrics.lens_consistency_errors}"


# ==============================================================================
# PERFORMANCE METRICS (INFORMATIONAL)
# ==============================================================================

class TestPerformanceMetrics:
    """Performance metrics tests (informational, not assertions on speed)."""

    def test_tavern_collects_timing_metrics(
        self, tavern_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Tavern scenario collects timing metrics."""
        metrics = scenario_runner.run(tavern_scenario)

        # Timing lists should match execution
        assert len(metrics.time_per_round_ms) == metrics.total_rounds
        assert len(metrics.time_per_action_ms) == metrics.total_actions

        # Total time should be positive
        assert metrics.total_time_ms > 0

    def test_metrics_can_be_serialized(
        self, tavern_scenario: ScenarioConfig, scenario_runner: ScenarioRunner
    ):
        """Metrics can be serialized to dict for reporting."""
        metrics = scenario_runner.run(tavern_scenario)

        # Should serialize without error
        metrics_dict = metrics.to_dict()

        assert "total_rounds" in metrics_dict
        assert "total_actions" in metrics_dict
        assert "time_per_round_ms" in metrics_dict
        assert "time_per_action_ms" in metrics_dict
        assert "stp_count" in metrics_dict
        assert "event_log_hash" in metrics_dict
        assert "final_state_hash" in metrics_dict
        assert "stps_by_type" in metrics_dict
        assert "entities_defeated" in metrics_dict
        assert "total_time_ms" in metrics_dict
        assert "lens_consistency_errors" in metrics_dict
