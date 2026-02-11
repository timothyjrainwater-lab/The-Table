#!/usr/bin/env python3
"""Performance profiling script for AIDM system.

Executes all profiling benchmarks and outputs a human-readable report.
Exits with non-zero code if any latency target is missed.

Usage:
    python scripts/run_performance_profile.py
    python scripts/run_performance_profile.py --iterations 50
    python scripts/run_performance_profile.py --quick

WO-017: Performance Profiling Suite
"""

import argparse
import sys
from typing import List

from aidm.schemas.testing import ScenarioConfig, CombatantConfig, AttackConfig
from aidm.schemas.position import Position
from aidm.core.geometry_engine import BattleGrid
from aidm.core.lens_index import LensIndex, SourceTier
from aidm.testing.performance_profiler import (
    PerformanceProfiler,
    LatencyResult,
    create_profiler,
)


# ==============================================================================
# SCENARIO BUILDERS — Create test scenarios
# ==============================================================================

def create_tavern_scenario() -> ScenarioConfig:
    """Create the tavern brawl scenario."""
    from tests.integration.conftest import (
        create_melee_fighter,
        create_archer,
        create_wizard,
        create_rogue,
        create_bandit,
    )
    from aidm.schemas.testing import TerrainPlacement, CoverDegree

    terrain = [
        TerrainPlacement(
            coord=Position(x=5, y=5),
            terrain_type="table",
            cover_provided=CoverDegree.PARTIAL,
            blocks_los=False,
            blocks_loe=False,
            height=3,
        ),
    ]

    combatants = [
        create_melee_fighter("fighter_1", "party", Position(x=3, y=3)),
        create_melee_fighter("fighter_2", "party", Position(x=5, y=3)),
        create_archer("archer_1", "party", Position(x=12, y=2)),
        create_wizard("wizard_1", "party", Position(x=7, y=2)),
        create_rogue("rogue_1", "party", Position(x=8, y=4)),
        create_bandit("bandit_1", Position(x=4, y=10)),
        create_bandit("bandit_2", Position(x=8, y=11)),
        create_bandit("bandit_3", Position(x=11, y=10)),
    ]

    return ScenarioConfig(
        name="Tavern Brawl",
        grid_width=15,
        grid_height=15,
        terrain=terrain,
        combatants=combatants,
        round_limit=15,
        seed=42,
    )


def create_field_battle_scenario() -> ScenarioConfig:
    """Create a larger field battle scenario."""
    from tests.integration.conftest import (
        create_melee_fighter,
        create_archer,
        create_wizard,
        create_rogue,
    )
    from aidm.schemas.testing import TerrainPlacement, CoverDegree

    terrain = [
        TerrainPlacement(
            coord=Position(x=20, y=20),
            terrain_type="boulder",
            cover_provided=CoverDegree.IMPROVED,
            blocks_los=True,
            blocks_loe=True,
            height=5,
        ),
    ]

    combatants = [
        create_melee_fighter("party_fighter_1", "party", Position(x=18, y=15)),
        create_melee_fighter("party_fighter_2", "party", Position(x=22, y=15)),
        create_archer("party_archer_1", "party", Position(x=15, y=13)),
        create_archer("party_archer_2", "party", Position(x=25, y=13)),
        create_wizard("party_wizard", "party", Position(x=20, y=12)),
        create_rogue("party_rogue", "party", Position(x=20, y=16)),
        create_melee_fighter("enemy_fighter_1", "enemy", Position(x=18, y=25)),
        create_melee_fighter("enemy_fighter_2", "enemy", Position(x=22, y=25)),
        create_archer("enemy_archer_1", "enemy", Position(x=15, y=27)),
        create_archer("enemy_archer_2", "enemy", Position(x=25, y=27)),
        create_wizard("enemy_wizard", "enemy", Position(x=20, y=28)),
        create_rogue("enemy_rogue", "enemy", Position(x=20, y=24)),
    ]

    return ScenarioConfig(
        name="Field Battle",
        grid_width=40,
        grid_height=40,
        terrain=terrain,
        combatants=combatants,
        round_limit=15,
        seed=456,
    )


# ==============================================================================
# MAIN PROFILING FUNCTION
# ==============================================================================

def run_profiling(
    box_iterations: int = 100,
    lens_iterations: int = 100,
    action_iterations: int = 20,
    round_iterations: int = 10,
    warmup: int = 3,
    verbose: bool = False,
) -> List[LatencyResult]:
    """Run all profiling benchmarks.

    Args:
        box_iterations: Iterations for Box query profiling
        lens_iterations: Iterations for Lens query profiling
        action_iterations: Iterations for action resolution
        round_iterations: Iterations for full round
        warmup: Number of warmup iterations
        verbose: Print progress messages

    Returns:
        List of LatencyResult
    """
    profiler = create_profiler(warmup_iterations=warmup)
    results = []

    # Box query profiling
    if verbose:
        print("Profiling Box layer queries...")
    grid = BattleGrid(50, 50)
    result = profiler.profile_box_query(grid, iterations=box_iterations)
    results.append(result)
    if verbose:
        print(f"  Box query p95: {result.p95_ms:.3f}ms (target: 50ms)")

    # Lens query profiling
    if verbose:
        print("Profiling Lens layer queries...")
    lens = LensIndex()
    for i in range(20):
        entity_id = f"entity_{i:02d}"
        lens.register_entity(entity_id, "creature", turn=0)
        lens.set_position(entity_id, Position(x=i * 2, y=i * 2), turn=0)
        lens.set_fact(entity_id, "hp", 50 + i, SourceTier.BOX, turn=0)
    result = profiler.profile_lens_query(lens, iterations=lens_iterations)
    results.append(result)
    if verbose:
        print(f"  Lens query p95: {result.p95_ms:.3f}ms (target: 20ms)")

    # Action resolution profiling
    if verbose:
        print("Profiling action resolution...")
    scenario = create_tavern_scenario()
    result = profiler.profile_action_resolution(scenario, iterations=action_iterations)
    results.append(result)
    if verbose:
        print(f"  Action resolution p95: {result.p95_ms:.3f}ms (target: 3000ms)")

    # Full round profiling
    if verbose:
        print("Profiling full combat round...")
    result = profiler.profile_full_round(scenario, iterations=round_iterations)
    results.append(result)
    if verbose:
        print(f"  Full round p95: {result.p95_ms:.3f}ms")

    return results


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 = all pass, 1 = some failed)
    """
    parser = argparse.ArgumentParser(
        description="AIDM Performance Profiling Suite"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Base number of iterations (default: 50)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode with fewer iterations",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print progress messages",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="Number of warmup iterations (default: 3)",
    )

    args = parser.parse_args()

    # Adjust iterations based on mode
    if args.quick:
        box_iter = 20
        lens_iter = 20
        action_iter = 5
        round_iter = 3
    else:
        box_iter = args.iterations
        lens_iter = args.iterations
        action_iter = max(10, args.iterations // 5)
        round_iter = max(5, args.iterations // 10)

    print("=" * 60)
    print("AIDM Performance Profiling Suite")
    print("=" * 60)
    print()

    # Run profiling
    results = run_profiling(
        box_iterations=box_iter,
        lens_iterations=lens_iter,
        action_iterations=action_iter,
        round_iterations=round_iter,
        warmup=args.warmup,
        verbose=args.verbose,
    )

    # Generate and print report
    profiler = create_profiler()
    report = profiler.generate_report(results)
    print()
    print(report)

    # Determine exit code
    all_pass = all(r.meets_target for r in results)

    print()
    if all_pass:
        print("All latency targets met.")
        return 0
    else:
        failed = [r.name for r in results if not r.meets_target]
        print(f"FAILED targets: {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
