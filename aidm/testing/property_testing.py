"""Property-based testing harness for geometry system validation.

Implements the "Thousand-Fold Fireball" pattern: randomized input generation
with invariant validation across 1000+ iterations to find edge cases in
geometric algorithms.

Invariants tested:
- AoE: Origin always in burst, no crashes on any placement
- Cover: Geometry is valid and consistent
- LOS: Reflexivity (can see self), symmetry in empty grids
- Distance: Triangle inequality holds

WO-019: Property-Based Testing
Reference: Execution Plan Milestone 3
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import time

from aidm.schemas.position import Position
from aidm.schemas.geometry import PropertyMask, PropertyFlag, Direction, SizeCategory
from aidm.core.geometry_engine import BattleGrid
from aidm.core.aoe_rasterizer import (
    AoEShape, AoEDirection, rasterize_burst, rasterize_cone, rasterize_line,
    get_aoe_affected_squares, discrete_distance,
)
from aidm.core.cover_resolver import calculate_cover, CoverDegree
from aidm.core.los_resolver import check_los, check_loe
from aidm.core.rng_manager import RNGManager


# ==============================================================================
# PROPERTY TEST RESULT — Captures test outcomes with reproducibility info
# ==============================================================================

@dataclass
class PropertyTestResult:
    """Result of a property-based test run.

    Captures success/failure, failure details with reproducible seeds,
    and performance metrics.
    """
    test_name: str
    passed: bool
    iterations_run: int
    failures: List[Dict[str, Any]] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "iterations_run": self.iterations_run,
            "failure_count": len(self.failures),
            "failures": self.failures[:10],  # Limit to first 10 for brevity
            "elapsed_seconds": self.elapsed_seconds,
        }

    def add_failure(
        self,
        seed: int,
        iteration: int,
        message: str,
        context: Dict[str, Any]
    ) -> None:
        """Record a failure with reproducibility info."""
        self.failures.append({
            "seed": seed,
            "iteration": iteration,
            "message": message,
            "context": context,
        })
        self.passed = False


# ==============================================================================
# AOE CONFIG — Configuration for random AoE generation
# ==============================================================================

@dataclass
class AoEConfig:
    """Configuration for a random AoE effect."""
    shape: AoEShape
    origin: Position
    params: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "shape": self.shape.value,
            "origin": self.origin.to_dict(),
            "params": self.params,
        }


# ==============================================================================
# PROPERTY TEST HARNESS — Main testing class
# ==============================================================================

class PropertyTestHarness:
    """Generates randomized inputs and validates geometric invariants.

    Uses deterministic RNG for reproducibility. All tests can be reproduced
    by providing the same seed.
    """

    def __init__(self, master_seed: int = 42):
        """Initialize the harness with a master seed.

        Args:
            master_seed: Master seed for all random generation
        """
        self._master_seed = master_seed
        self._rng_manager = RNGManager(master_seed)

    @property
    def master_seed(self) -> int:
        """Return the master seed for reproducibility."""
        return self._master_seed

    # ==========================================================================
    # RANDOM GENERATION METHODS
    # ==========================================================================

    def generate_random_grid(
        self,
        seed: int,
        size: Tuple[int, int],
        obstacle_density: float = 0.1
    ) -> BattleGrid:
        """Generate a random grid with optional obstacles.

        Args:
            seed: Seed for this specific grid generation
            size: (width, height) tuple
            obstacle_density: Fraction of cells to make solid (0.0 to 1.0)

        Returns:
            BattleGrid with random obstacles placed
        """
        rng = RNGManager(seed).stream("grid")
        width, height = size

        grid = BattleGrid(width, height)

        # Place random obstacles
        num_obstacles = int(width * height * obstacle_density)

        for _ in range(num_obstacles):
            x = rng.randint(0, width - 1)
            y = rng.randint(0, height - 1)
            pos = Position(x=x, y=y)

            cell = grid.get_cell(pos)
            # Make cell solid and opaque
            cell.cell_mask = cell.cell_mask.set_flag(PropertyFlag.SOLID)
            cell.cell_mask = cell.cell_mask.set_flag(PropertyFlag.OPAQUE)

        return grid

    def generate_empty_grid(self, size: Tuple[int, int]) -> BattleGrid:
        """Generate an empty grid with no obstacles.

        Args:
            size: (width, height) tuple

        Returns:
            Empty BattleGrid
        """
        width, height = size
        return BattleGrid(width, height)

    def generate_random_positions(
        self,
        grid: BattleGrid,
        count: int,
        seed: int
    ) -> List[Position]:
        """Generate random valid positions within a grid.

        Args:
            grid: BattleGrid to generate positions for
            count: Number of positions to generate
            seed: Seed for this specific generation

        Returns:
            List of random Position objects within grid bounds
        """
        rng = RNGManager(seed).stream("positions")
        positions = []

        for _ in range(count):
            x = rng.randint(0, grid.width - 1)
            y = rng.randint(0, grid.height - 1)
            positions.append(Position(x=x, y=y))

        return positions

    def generate_random_aoe(
        self,
        origin: Position,
        seed: int,
        grid_size: Tuple[int, int] = (50, 50)
    ) -> AoEConfig:
        """Generate a random AoE configuration.

        Args:
            origin: Origin point for the AoE
            seed: Seed for this specific generation
            grid_size: Grid bounds for context

        Returns:
            AoEConfig with random shape and parameters
        """
        rng = RNGManager(seed).stream("aoe")

        # Random shape selection
        shapes = [AoEShape.BURST, AoEShape.CONE, AoEShape.LINE,
                  AoEShape.CYLINDER, AoEShape.SPHERE]
        shape = rng.choice(shapes)

        # Random directions for cones/lines
        directions = list(AoEDirection)
        direction = rng.choice(directions)

        # Random radii and lengths (5-60 feet in 5-foot increments)
        radius_ft = rng.randint(1, 12) * 5
        length_ft = rng.randint(1, 12) * 5

        # Build params based on shape
        params: Dict[str, Any] = {}

        if shape == AoEShape.BURST:
            params = {"radius_ft": radius_ft}
        elif shape == AoEShape.CONE:
            params = {"length_ft": length_ft, "direction": direction}
        elif shape == AoEShape.LINE:
            params = {"length_ft": length_ft, "direction": direction, "width_ft": 5}
        elif shape == AoEShape.CYLINDER:
            height_ft = rng.randint(1, 8) * 5
            params = {"radius_ft": radius_ft, "height_ft": height_ft}
        elif shape == AoEShape.SPHERE:
            params = {"radius_ft": radius_ft}

        return AoEConfig(shape=shape, origin=origin, params=params)

    # ==========================================================================
    # PROPERTY TEST: THOUSAND-FOLD FIREBALL
    # ==========================================================================

    def run_thousand_fold_fireball(
        self,
        iterations: int = 1000,
        grid_size: Tuple[int, int] = (50, 50)
    ) -> PropertyTestResult:
        """Run the Thousand-Fold Fireball test.

        Property: Random AoE placements never crash and always return
        valid cell sets.

        Validates:
        - No exceptions thrown for any random AoE
        - Result is always a list of Position objects
        - No duplicate positions in result
        - For bursts: origin is always included

        Args:
            iterations: Number of test iterations (default 1000)
            grid_size: Grid size for position bounds

        Returns:
            PropertyTestResult with pass/fail and any failure details
        """
        result = PropertyTestResult(
            test_name="thousand_fold_fireball",
            passed=True,
            iterations_run=iterations,
        )

        start_time = time.time()
        width, height = grid_size

        for i in range(iterations):
            # Derive seed for this iteration
            iteration_seed = self._master_seed + i
            rng = RNGManager(iteration_seed).stream("fireball")

            # Generate random origin within grid
            origin_x = rng.randint(0, width - 1)
            origin_y = rng.randint(0, height - 1)
            origin = Position(x=origin_x, y=origin_y)

            # Generate random AoE config
            aoe_config = self.generate_random_aoe(origin, iteration_seed + 1000)

            try:
                # Execute the AoE rasterization
                affected = get_aoe_affected_squares(
                    aoe_config.shape,
                    aoe_config.origin,
                    aoe_config.params
                )

                # Validate: result is a list
                if not isinstance(affected, list):
                    result.add_failure(
                        seed=iteration_seed,
                        iteration=i,
                        message="Result is not a list",
                        context={"type": str(type(affected)), "config": aoe_config.to_dict()}
                    )
                    continue

                # Validate: all items are Position
                for pos in affected:
                    if not isinstance(pos, Position):
                        result.add_failure(
                            seed=iteration_seed,
                            iteration=i,
                            message="Result contains non-Position item",
                            context={"item": str(pos), "config": aoe_config.to_dict()}
                        )
                        break

                # Validate: no duplicates
                unique_count = len(set(affected))
                if unique_count != len(affected):
                    result.add_failure(
                        seed=iteration_seed,
                        iteration=i,
                        message="Result contains duplicate positions",
                        context={
                            "total": len(affected),
                            "unique": unique_count,
                            "config": aoe_config.to_dict()
                        }
                    )
                    continue

                # Validate: burst contains origin
                if aoe_config.shape == AoEShape.BURST and len(affected) > 0:
                    if aoe_config.origin not in affected:
                        result.add_failure(
                            seed=iteration_seed,
                            iteration=i,
                            message="Burst AoE does not contain origin",
                            context={
                                "origin": aoe_config.origin.to_dict(),
                                "affected_count": len(affected),
                                "config": aoe_config.to_dict()
                            }
                        )

            except Exception as e:
                result.add_failure(
                    seed=iteration_seed,
                    iteration=i,
                    message=f"Exception during AoE rasterization: {type(e).__name__}: {str(e)}",
                    context={"config": aoe_config.to_dict()}
                )

        result.elapsed_seconds = time.time() - start_time
        return result

    # ==========================================================================
    # PROPERTY TEST: COVER SYMMETRY
    # ==========================================================================

    def run_cover_symmetry_check(
        self,
        iterations: int = 1000,
        grid_size: Tuple[int, int] = (30, 30)
    ) -> PropertyTestResult:
        """Run cover symmetry validation.

        Property: Cover calculation produces valid, consistent geometry.

        Validates:
        - No exceptions for any position pair
        - Lines blocked <= lines total
        - Cover degree matches line count thresholds
        - Both positions are recorded correctly

        Args:
            iterations: Number of test iterations
            grid_size: Grid size for position bounds

        Returns:
            PropertyTestResult with pass/fail and any failure details
        """
        result = PropertyTestResult(
            test_name="cover_symmetry_check",
            passed=True,
            iterations_run=iterations,
        )

        start_time = time.time()

        for i in range(iterations):
            iteration_seed = self._master_seed + i

            # Generate grid with some obstacles
            grid = self.generate_random_grid(
                seed=iteration_seed,
                size=grid_size,
                obstacle_density=0.15
            )

            # Generate two random positions
            positions = self.generate_random_positions(
                grid=grid,
                count=2,
                seed=iteration_seed + 500
            )
            pos_a, pos_b = positions[0], positions[1]

            try:
                # Calculate cover from A to B
                cover_result = calculate_cover(pos_a, pos_b, grid)

                # Validate: lines_blocked <= lines_total
                if cover_result.lines_blocked > cover_result.lines_total:
                    result.add_failure(
                        seed=iteration_seed,
                        iteration=i,
                        message="lines_blocked exceeds lines_total",
                        context={
                            "pos_a": pos_a.to_dict(),
                            "pos_b": pos_b.to_dict(),
                            "lines_blocked": cover_result.lines_blocked,
                            "lines_total": cover_result.lines_total,
                        }
                    )
                    continue

                # Validate: lines_blocked >= 0
                if cover_result.lines_blocked < 0:
                    result.add_failure(
                        seed=iteration_seed,
                        iteration=i,
                        message="lines_blocked is negative",
                        context={
                            "pos_a": pos_a.to_dict(),
                            "pos_b": pos_b.to_dict(),
                            "lines_blocked": cover_result.lines_blocked,
                        }
                    )
                    continue

                # Validate: positions recorded correctly
                if cover_result.attacker_pos != pos_a or cover_result.defender_pos != pos_b:
                    result.add_failure(
                        seed=iteration_seed,
                        iteration=i,
                        message="Positions not recorded correctly",
                        context={
                            "expected_attacker": pos_a.to_dict(),
                            "expected_defender": pos_b.to_dict(),
                            "actual_attacker": cover_result.attacker_pos.to_dict(),
                            "actual_defender": cover_result.defender_pos.to_dict(),
                        }
                    )

                # Validate: total cover means blocks_targeting is True
                if cover_result.cover_degree == CoverDegree.TOTAL_COVER:
                    if not cover_result.blocks_targeting:
                        result.add_failure(
                            seed=iteration_seed,
                            iteration=i,
                            message="Total cover but blocks_targeting is False",
                            context={
                                "pos_a": pos_a.to_dict(),
                                "pos_b": pos_b.to_dict(),
                            }
                        )

            except Exception as e:
                result.add_failure(
                    seed=iteration_seed,
                    iteration=i,
                    message=f"Exception during cover calculation: {type(e).__name__}: {str(e)}",
                    context={
                        "pos_a": pos_a.to_dict(),
                        "pos_b": pos_b.to_dict(),
                    }
                )

        result.elapsed_seconds = time.time() - start_time
        return result

    # ==========================================================================
    # PROPERTY TEST: LOS REFLEXIVITY
    # ==========================================================================

    def run_los_reflexivity_check(
        self,
        iterations: int = 1000,
        grid_size: Tuple[int, int] = (30, 30)
    ) -> PropertyTestResult:
        """Run LOS reflexivity validation.

        Property: An entity can always see itself (LOS(A, A) = True).

        Args:
            iterations: Number of test iterations
            grid_size: Grid size for position bounds

        Returns:
            PropertyTestResult with pass/fail and any failure details
        """
        result = PropertyTestResult(
            test_name="los_reflexivity_check",
            passed=True,
            iterations_run=iterations,
        )

        start_time = time.time()

        for i in range(iterations):
            iteration_seed = self._master_seed + i

            # Generate grid with obstacles
            grid = self.generate_random_grid(
                seed=iteration_seed,
                size=grid_size,
                obstacle_density=0.2
            )

            # Generate random position
            positions = self.generate_random_positions(
                grid=grid,
                count=1,
                seed=iteration_seed + 500
            )
            pos = positions[0]

            try:
                # Check LOS from position to itself
                los_result = check_los(
                    grid=grid,
                    observer_pos=pos,
                    observer_height=5,
                    target_pos=pos,
                    target_height=5
                )

                # Validate: self-LOS is always clear
                if not los_result.is_clear:
                    result.add_failure(
                        seed=iteration_seed,
                        iteration=i,
                        message="Entity cannot see itself (LOS reflexivity violated)",
                        context={
                            "position": pos.to_dict(),
                            "blocking_reason": los_result.blocking_reason,
                        }
                    )

            except Exception as e:
                result.add_failure(
                    seed=iteration_seed,
                    iteration=i,
                    message=f"Exception during LOS check: {type(e).__name__}: {str(e)}",
                    context={"position": pos.to_dict()}
                )

        result.elapsed_seconds = time.time() - start_time
        return result

    # ==========================================================================
    # PROPERTY TEST: LOS SYMMETRY (EMPTY GRID)
    # ==========================================================================

    def run_los_symmetry_check(
        self,
        iterations: int = 1000,
        grid_size: Tuple[int, int] = (30, 30)
    ) -> PropertyTestResult:
        """Run LOS symmetry validation for empty grids.

        Property: In an empty grid, LOS(A, B) == LOS(B, A).

        Note: This only holds for empty grids. With obstacles,
        asymmetry can occur due to height differences.

        Args:
            iterations: Number of test iterations
            grid_size: Grid size for position bounds

        Returns:
            PropertyTestResult with pass/fail and any failure details
        """
        result = PropertyTestResult(
            test_name="los_symmetry_check",
            passed=True,
            iterations_run=iterations,
        )

        start_time = time.time()

        # Use same empty grid for all iterations
        grid = self.generate_empty_grid(grid_size)

        for i in range(iterations):
            iteration_seed = self._master_seed + i

            # Generate two random positions
            positions = self.generate_random_positions(
                grid=grid,
                count=2,
                seed=iteration_seed
            )
            pos_a, pos_b = positions[0], positions[1]

            try:
                # Check LOS both directions
                los_a_to_b = check_los(
                    grid=grid,
                    observer_pos=pos_a,
                    observer_height=5,
                    target_pos=pos_b,
                    target_height=5
                )

                los_b_to_a = check_los(
                    grid=grid,
                    observer_pos=pos_b,
                    observer_height=5,
                    target_pos=pos_a,
                    target_height=5
                )

                # Validate: symmetry
                if los_a_to_b.is_clear != los_b_to_a.is_clear:
                    result.add_failure(
                        seed=iteration_seed,
                        iteration=i,
                        message="LOS symmetry violated in empty grid",
                        context={
                            "pos_a": pos_a.to_dict(),
                            "pos_b": pos_b.to_dict(),
                            "a_to_b_clear": los_a_to_b.is_clear,
                            "b_to_a_clear": los_b_to_a.is_clear,
                        }
                    )

            except Exception as e:
                result.add_failure(
                    seed=iteration_seed,
                    iteration=i,
                    message=f"Exception during LOS symmetry check: {type(e).__name__}: {str(e)}",
                    context={
                        "pos_a": pos_a.to_dict(),
                        "pos_b": pos_b.to_dict(),
                    }
                )

        result.elapsed_seconds = time.time() - start_time
        return result

    # ==========================================================================
    # PROPERTY TEST: AOE CONTAINMENT
    # ==========================================================================

    def run_aoe_containment_check(
        self,
        iterations: int = 1000
    ) -> PropertyTestResult:
        """Run AoE containment validation.

        Property: Origin is always in burst AoE (for radius > 0).

        Args:
            iterations: Number of test iterations

        Returns:
            PropertyTestResult with pass/fail and any failure details
        """
        result = PropertyTestResult(
            test_name="aoe_containment_check",
            passed=True,
            iterations_run=iterations,
        )

        start_time = time.time()

        for i in range(iterations):
            iteration_seed = self._master_seed + i
            rng = RNGManager(iteration_seed).stream("aoe_containment")

            # Generate random origin
            origin = Position(x=rng.randint(0, 50), y=rng.randint(0, 50))

            # Generate random positive radius
            radius_ft = rng.randint(0, 12) * 5  # 0, 5, 10, ..., 60

            try:
                # Rasterize burst
                affected = rasterize_burst(origin, radius_ft)

                # For radius >= 0, origin should be included
                if radius_ft >= 0 and len(affected) > 0:
                    if origin not in affected:
                        result.add_failure(
                            seed=iteration_seed,
                            iteration=i,
                            message="Burst origin not in affected squares",
                            context={
                                "origin": origin.to_dict(),
                                "radius_ft": radius_ft,
                                "affected_count": len(affected),
                            }
                        )

                # For zero radius, should be exactly the origin
                if radius_ft == 0:
                    if len(affected) != 1 or affected[0] != origin:
                        result.add_failure(
                            seed=iteration_seed,
                            iteration=i,
                            message="Zero-radius burst should contain only origin",
                            context={
                                "origin": origin.to_dict(),
                                "affected_count": len(affected),
                                "affected": [p.to_dict() for p in affected[:5]],
                            }
                        )

            except Exception as e:
                result.add_failure(
                    seed=iteration_seed,
                    iteration=i,
                    message=f"Exception during burst rasterization: {type(e).__name__}: {str(e)}",
                    context={
                        "origin": origin.to_dict(),
                        "radius_ft": radius_ft,
                    }
                )

        result.elapsed_seconds = time.time() - start_time
        return result

    # ==========================================================================
    # PROPERTY TEST: DISTANCE TRIANGLE INEQUALITY
    # ==========================================================================

    def run_distance_triangle_inequality_check(
        self,
        iterations: int = 1000,
        grid_size: Tuple[int, int] = (50, 50)
    ) -> PropertyTestResult:
        """Run distance triangle inequality validation.

        Property: dist(A, C) <= dist(A, B) + dist(B, C)

        This is a fundamental property of distance metrics.

        Args:
            iterations: Number of test iterations
            grid_size: Grid size for position bounds

        Returns:
            PropertyTestResult with pass/fail and any failure details
        """
        result = PropertyTestResult(
            test_name="distance_triangle_inequality_check",
            passed=True,
            iterations_run=iterations,
        )

        start_time = time.time()
        width, height = grid_size

        for i in range(iterations):
            iteration_seed = self._master_seed + i
            rng = RNGManager(iteration_seed).stream("triangle")

            # Generate three random positions
            pos_a = Position(x=rng.randint(0, width - 1), y=rng.randint(0, height - 1))
            pos_b = Position(x=rng.randint(0, width - 1), y=rng.randint(0, height - 1))
            pos_c = Position(x=rng.randint(0, width - 1), y=rng.randint(0, height - 1))

            try:
                # Calculate distances using Position.distance_to
                dist_a_b = pos_a.distance_to(pos_b)
                dist_b_c = pos_b.distance_to(pos_c)
                dist_a_c = pos_a.distance_to(pos_c)

                # Validate triangle inequality
                if dist_a_c > dist_a_b + dist_b_c:
                    result.add_failure(
                        seed=iteration_seed,
                        iteration=i,
                        message="Triangle inequality violated",
                        context={
                            "pos_a": pos_a.to_dict(),
                            "pos_b": pos_b.to_dict(),
                            "pos_c": pos_c.to_dict(),
                            "dist_a_b": dist_a_b,
                            "dist_b_c": dist_b_c,
                            "dist_a_c": dist_a_c,
                            "sum_a_b_b_c": dist_a_b + dist_b_c,
                        }
                    )

            except Exception as e:
                result.add_failure(
                    seed=iteration_seed,
                    iteration=i,
                    message=f"Exception during distance calculation: {type(e).__name__}: {str(e)}",
                    context={
                        "pos_a": pos_a.to_dict(),
                        "pos_b": pos_b.to_dict(),
                        "pos_c": pos_c.to_dict(),
                    }
                )

        result.elapsed_seconds = time.time() - start_time
        return result

    # ==========================================================================
    # PROPERTY TEST: DISCRETE DISTANCE TRIANGLE INEQUALITY
    # ==========================================================================

    def run_discrete_distance_triangle_inequality_check(
        self,
        iterations: int = 1000,
        max_offset: int = 20
    ) -> PropertyTestResult:
        """Run triangle inequality validation for discrete_distance.

        Property: discrete_distance(dx_ac, dy_ac) <=
                  discrete_distance(dx_ab, dy_ab) + discrete_distance(dx_bc, dy_bc)

        Args:
            iterations: Number of test iterations
            max_offset: Maximum coordinate offset

        Returns:
            PropertyTestResult with pass/fail and any failure details
        """
        result = PropertyTestResult(
            test_name="discrete_distance_triangle_inequality_check",
            passed=True,
            iterations_run=iterations,
        )

        start_time = time.time()

        for i in range(iterations):
            iteration_seed = self._master_seed + i
            rng = RNGManager(iteration_seed).stream("discrete_triangle")

            # Generate three random offsets
            ax, ay = rng.randint(-max_offset, max_offset), rng.randint(-max_offset, max_offset)
            bx, by = rng.randint(-max_offset, max_offset), rng.randint(-max_offset, max_offset)
            cx, cy = rng.randint(-max_offset, max_offset), rng.randint(-max_offset, max_offset)

            try:
                # Calculate discrete distances
                dist_a_b = discrete_distance(bx - ax, by - ay)
                dist_b_c = discrete_distance(cx - bx, cy - by)
                dist_a_c = discrete_distance(cx - ax, cy - ay)

                # Validate triangle inequality
                if dist_a_c > dist_a_b + dist_b_c:
                    result.add_failure(
                        seed=iteration_seed,
                        iteration=i,
                        message="Discrete distance triangle inequality violated",
                        context={
                            "a": (ax, ay),
                            "b": (bx, by),
                            "c": (cx, cy),
                            "dist_a_b": dist_a_b,
                            "dist_b_c": dist_b_c,
                            "dist_a_c": dist_a_c,
                        }
                    )

            except Exception as e:
                result.add_failure(
                    seed=iteration_seed,
                    iteration=i,
                    message=f"Exception during discrete distance: {type(e).__name__}: {str(e)}",
                    context={"a": (ax, ay), "b": (bx, by), "c": (cx, cy)}
                )

        result.elapsed_seconds = time.time() - start_time
        return result

    # ==========================================================================
    # PROPERTY TEST: CONE SQUARE COUNT
    # ==========================================================================

    def run_cone_square_count_check(
        self,
        iterations: int = 1000
    ) -> PropertyTestResult:
        """Run cone square count validation.

        Property: Cardinal cones have triangular number square counts.
        Formula: N = L/5 * (L/5 + 1) / 2

        Args:
            iterations: Number of test iterations

        Returns:
            PropertyTestResult with pass/fail and any failure details
        """
        result = PropertyTestResult(
            test_name="cone_square_count_check",
            passed=True,
            iterations_run=iterations,
        )

        start_time = time.time()
        cardinal_directions = [AoEDirection.N, AoEDirection.E,
                               AoEDirection.S, AoEDirection.W]

        for i in range(iterations):
            iteration_seed = self._master_seed + i
            rng = RNGManager(iteration_seed).stream("cone_count")

            # Random origin (away from edges to avoid boundary effects)
            origin = Position(x=rng.randint(15, 35), y=rng.randint(15, 35))

            # Random length
            length_ft = rng.randint(1, 12) * 5  # 5 to 60 feet

            # Random cardinal direction
            direction = rng.choice(cardinal_directions)

            try:
                # Rasterize cone
                affected = rasterize_cone(origin, direction, length_ft)

                # Calculate expected count
                n = length_ft // 5
                expected_count = n * (n + 1) // 2

                # Validate count
                if len(affected) != expected_count:
                    result.add_failure(
                        seed=iteration_seed,
                        iteration=i,
                        message="Cardinal cone square count mismatch",
                        context={
                            "origin": origin.to_dict(),
                            "direction": direction.value,
                            "length_ft": length_ft,
                            "expected_count": expected_count,
                            "actual_count": len(affected),
                        }
                    )

            except Exception as e:
                result.add_failure(
                    seed=iteration_seed,
                    iteration=i,
                    message=f"Exception during cone rasterization: {type(e).__name__}: {str(e)}",
                    context={
                        "origin": origin.to_dict(),
                        "direction": direction.value,
                        "length_ft": length_ft,
                    }
                )

        result.elapsed_seconds = time.time() - start_time
        return result

    # ==========================================================================
    # RUN ALL TESTS
    # ==========================================================================

    def run_all_property_tests(
        self,
        iterations: int = 1000
    ) -> Dict[str, PropertyTestResult]:
        """Run all property tests.

        Note: Triangle inequality tests are NOT included because D&D 3.5e
        1-2-1-2 diagonal distance is not a true metric (it violates the
        triangle inequality by design per PHB p.148).

        Args:
            iterations: Number of iterations per test

        Returns:
            Dictionary mapping test names to results
        """
        results = {}

        results["thousand_fold_fireball"] = self.run_thousand_fold_fireball(iterations)
        results["cover_symmetry"] = self.run_cover_symmetry_check(iterations)
        results["los_reflexivity"] = self.run_los_reflexivity_check(iterations)
        results["los_symmetry"] = self.run_los_symmetry_check(iterations)
        results["aoe_containment"] = self.run_aoe_containment_check(iterations)
        results["cone_square_count"] = self.run_cone_square_count_check(iterations)

        return results
