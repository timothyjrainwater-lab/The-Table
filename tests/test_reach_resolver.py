"""Tests for reach_resolver.py — Reach weapons and threatened squares.

WO-006: Reach Weapons and Threatened Squares
Reference: PHB p.137 (AoO), p.157 (Reach Weapons), p.149 (Size/Reach Table)
"""

import pytest

from aidm.schemas.position import Position
from aidm.schemas.geometry import SizeCategory
from aidm.core.geometry_engine import BattleGrid
from aidm.core.reach_resolver import (
    get_natural_reach,
    get_weapon_reach,
    get_threatened_squares,
    get_threatened_squares_for_entity,
    is_square_threatened,
    can_threaten,
    get_aoo_eligible_squares,
    _discrete_distance,
    _get_occupied_squares,
    _get_ring_at_distance,
)


# ==============================================================================
# NATURAL REACH TESTS
# ==============================================================================

class TestGetNaturalReach:
    """Tests for get_natural_reach() function."""

    def test_fine_has_zero_reach(self):
        """Fine creatures have 0 reach."""
        assert get_natural_reach(SizeCategory.FINE) == 0

    def test_diminutive_has_zero_reach(self):
        """Diminutive creatures have 0 reach."""
        assert get_natural_reach(SizeCategory.DIMINUTIVE) == 0

    def test_tiny_has_zero_reach(self):
        """Tiny creatures have 0 reach."""
        assert get_natural_reach(SizeCategory.TINY) == 0

    def test_small_has_5ft_reach(self):
        """Small creatures have 5ft reach."""
        assert get_natural_reach(SizeCategory.SMALL) == 5

    def test_medium_has_5ft_reach(self):
        """Medium creatures have 5ft reach."""
        assert get_natural_reach(SizeCategory.MEDIUM) == 5

    def test_large_tall_has_10ft_reach(self):
        """Large tall (bipedal) creatures have 10ft reach."""
        assert get_natural_reach(SizeCategory.LARGE, is_long=False) == 10

    def test_large_long_has_5ft_reach(self):
        """Large long (quadruped) creatures have 5ft reach."""
        assert get_natural_reach(SizeCategory.LARGE, is_long=True) == 5

    def test_huge_tall_has_15ft_reach(self):
        """Huge tall creatures have 15ft reach."""
        assert get_natural_reach(SizeCategory.HUGE, is_long=False) == 15

    def test_huge_long_has_10ft_reach(self):
        """Huge long creatures have 10ft reach."""
        assert get_natural_reach(SizeCategory.HUGE, is_long=True) == 10

    def test_gargantuan_tall_has_20ft_reach(self):
        """Gargantuan tall creatures have 20ft reach."""
        assert get_natural_reach(SizeCategory.GARGANTUAN, is_long=False) == 20

    def test_gargantuan_long_has_15ft_reach(self):
        """Gargantuan long creatures have 15ft reach."""
        assert get_natural_reach(SizeCategory.GARGANTUAN, is_long=True) == 15

    def test_colossal_tall_has_30ft_reach(self):
        """Colossal tall creatures have 30ft reach."""
        assert get_natural_reach(SizeCategory.COLOSSAL, is_long=False) == 30

    def test_colossal_long_has_20ft_reach(self):
        """Colossal long creatures have 20ft reach."""
        assert get_natural_reach(SizeCategory.COLOSSAL, is_long=True) == 20

    def test_default_is_tall(self):
        """Default is_long=False gives tall values."""
        assert get_natural_reach(SizeCategory.LARGE) == 10
        assert get_natural_reach(SizeCategory.HUGE) == 15


# ==============================================================================
# WEAPON REACH TESTS
# ==============================================================================

class TestGetWeaponReach:
    """Tests for get_weapon_reach() function."""

    def test_reach_weapon_returns_weapon_reach(self):
        """Reach weapon reach replaces natural reach."""
        # Medium creature (5ft natural) with longspear (10ft)
        assert get_weapon_reach(5, 10) == 10

    def test_large_creature_with_reach_weapon(self):
        """Large creature with reach weapon uses weapon reach."""
        # Large creature (10ft natural) with reach weapon (15ft)
        assert get_weapon_reach(10, 15) == 15


# ==============================================================================
# DISCRETE DISTANCE TESTS
# ==============================================================================

class TestDiscreteDistance:
    """Tests for _discrete_distance() helper."""

    def test_same_position_is_zero(self):
        """Same position has distance 0."""
        pos = Position(x=5, y=5)
        assert _discrete_distance(pos, pos) == 0

    def test_adjacent_orthogonal_is_one(self):
        """Orthogonally adjacent is distance 1."""
        pos1 = Position(x=5, y=5)
        pos2 = Position(x=5, y=6)
        assert _discrete_distance(pos1, pos2) == 1

    def test_adjacent_diagonal_is_one(self):
        """Diagonally adjacent is distance 1."""
        pos1 = Position(x=5, y=5)
        pos2 = Position(x=6, y=6)
        assert _discrete_distance(pos1, pos2) == 1

    def test_distance_two_orthogonal(self):
        """Two squares orthogonally is distance 2."""
        pos1 = Position(x=5, y=5)
        pos2 = Position(x=5, y=7)
        assert _discrete_distance(pos1, pos2) == 2

    def test_distance_two_diagonal(self):
        """Two squares diagonally is distance 2."""
        pos1 = Position(x=5, y=5)
        pos2 = Position(x=7, y=7)
        assert _discrete_distance(pos1, pos2) == 2

    def test_distance_three(self):
        """Three squares is distance 3."""
        pos1 = Position(x=5, y=5)
        pos2 = Position(x=8, y=5)
        assert _discrete_distance(pos1, pos2) == 3


# ==============================================================================
# OCCUPIED SQUARES TESTS
# ==============================================================================

class TestGetOccupiedSquares:
    """Tests for _get_occupied_squares() helper."""

    def test_medium_occupies_one_square(self):
        """Medium creature occupies 1 square."""
        pos = Position(x=5, y=5)
        occupied = _get_occupied_squares(pos, SizeCategory.MEDIUM)
        assert len(occupied) == 1
        assert Position(x=5, y=5) in occupied

    def test_large_occupies_four_squares(self):
        """Large creature occupies 4 squares (2x2)."""
        pos = Position(x=5, y=5)
        occupied = _get_occupied_squares(pos, SizeCategory.LARGE)
        assert len(occupied) == 4
        assert Position(x=5, y=5) in occupied
        assert Position(x=6, y=5) in occupied
        assert Position(x=5, y=6) in occupied
        assert Position(x=6, y=6) in occupied

    def test_huge_occupies_nine_squares(self):
        """Huge creature occupies 9 squares (3x3)."""
        pos = Position(x=5, y=5)
        occupied = _get_occupied_squares(pos, SizeCategory.HUGE)
        assert len(occupied) == 9


# ==============================================================================
# THREATENED SQUARES (5FT REACH) TESTS
# ==============================================================================

class TestThreatenedSquares5ftReach:
    """Tests for get_threatened_squares() with 5ft reach."""

    def test_medium_creature_center_threatens_eight(self):
        """Medium creature in center threatens 8 adjacent squares."""
        pos = Position(x=5, y=5)
        threatened = get_threatened_squares(pos, SizeCategory.MEDIUM, 5)
        assert len(threatened) == 8
        # Check all 8 adjacent
        expected = [
            Position(x=4, y=4), Position(x=5, y=4), Position(x=6, y=4),
            Position(x=4, y=5),                     Position(x=6, y=5),
            Position(x=4, y=6), Position(x=5, y=6), Position(x=6, y=6),
        ]
        for exp in expected:
            assert exp in threatened

    def test_at_corner_threatens_fewer(self):
        """Creature at corner threatens fewer squares."""
        pos = Position(x=0, y=0)
        threatened = get_threatened_squares(pos, SizeCategory.MEDIUM, 5)
        # At (0,0) corner: only (1,0), (0,1), (1,1) are valid
        assert len(threatened) == 3
        assert Position(x=1, y=0) in threatened
        assert Position(x=0, y=1) in threatened
        assert Position(x=1, y=1) in threatened

    def test_at_edge_threatens_five(self):
        """Creature at edge threatens 5 squares."""
        pos = Position(x=0, y=5)
        threatened = get_threatened_squares(pos, SizeCategory.MEDIUM, 5)
        # At left edge: 5 squares (no x=-1)
        assert len(threatened) == 5

    def test_zero_reach_threatens_none(self):
        """Zero reach threatens no squares."""
        pos = Position(x=5, y=5)
        threatened = get_threatened_squares(pos, SizeCategory.FINE, 0)
        assert len(threatened) == 0


# ==============================================================================
# THREATENED SQUARES (10FT REACH) TESTS
# ==============================================================================

class TestThreatenedSquares10ftReach:
    """Tests for get_threatened_squares() with 10ft reach."""

    def test_medium_with_10ft_reach_threatens_ring_at_distance_2(self):
        """Medium with 10ft reach threatens squares at distance 1-2."""
        pos = Position(x=5, y=5)
        threatened = get_threatened_squares(pos, SizeCategory.MEDIUM, 10)
        # Distance 1: 8 adjacent
        # Distance 2: ring at distance 2
        # Total should include both for natural 10ft reach
        assert len(threatened) > 8
        # Check some distance 2 squares are included
        assert Position(x=3, y=5) in threatened  # 2 squares left
        assert Position(x=7, y=5) in threatened  # 2 squares right
        assert Position(x=5, y=3) in threatened  # 2 squares up
        assert Position(x=5, y=7) in threatened  # 2 squares down

    def test_large_creature_threatens_from_all_squares(self):
        """Large creature with 10ft reach threatens from all 4 occupied squares."""
        pos = Position(x=5, y=5)  # 2x2 at (5,5), (6,5), (5,6), (6,6)
        threatened = get_threatened_squares(pos, SizeCategory.LARGE, 10)

        # Large creature should threaten more squares than Medium
        # due to 2x2 footprint
        assert len(threatened) > 16

        # Check threats extend from multiple occupied squares
        # From (5,5): can threaten (3,5) at distance 2
        # From (6,6): can threaten (8,6) at distance 2
        assert Position(x=3, y=5) in threatened
        assert Position(x=8, y=6) in threatened


# ==============================================================================
# THREATENED SQUARES (15FT REACH) TESTS
# ==============================================================================

class TestThreatenedSquares15ftReach:
    """Tests for get_threatened_squares() with 15ft reach."""

    def test_huge_creature_natural_reach_15ft(self):
        """Huge creature with 15ft natural reach threatens distance 1-3."""
        pos = Position(x=10, y=10)  # Center of grid, 3x3 footprint
        threatened = get_threatened_squares(pos, SizeCategory.HUGE, 15)

        # Should include distance 3 squares
        assert Position(x=7, y=10) in threatened  # 3 squares left of (10,10)

        # Should be a large number of threatened squares
        assert len(threatened) > 30


# ==============================================================================
# REACH WEAPON (AoO) TESTS — Key rule: don't threaten adjacent
# ==============================================================================

class TestReachWeaponRules:
    """Tests for reach weapon AoO rules (PHB p.157)."""

    def test_10ft_reach_weapon_excludes_adjacent(self):
        """10ft reach weapon does NOT threaten adjacent squares."""
        pos = Position(x=5, y=5)
        # get_aoo_eligible_squares with weapon reach > natural reach
        aoo_squares = get_aoo_eligible_squares(
            entity_pos=pos,
            size=SizeCategory.MEDIUM,
            natural_reach_ft=5,
            weapon_reach_ft=10
        )

        # Should NOT include adjacent squares (distance 1)
        assert Position(x=4, y=5) not in aoo_squares
        assert Position(x=6, y=5) not in aoo_squares
        assert Position(x=5, y=4) not in aoo_squares
        assert Position(x=5, y=6) not in aoo_squares
        assert Position(x=4, y=4) not in aoo_squares

        # SHOULD include distance 2 squares
        assert Position(x=3, y=5) in aoo_squares
        assert Position(x=7, y=5) in aoo_squares

    def test_natural_reach_includes_adjacent(self):
        """Natural reach (no weapon) includes adjacent squares."""
        pos = Position(x=5, y=5)
        aoo_squares = get_aoo_eligible_squares(
            entity_pos=pos,
            size=SizeCategory.MEDIUM,
            natural_reach_ft=5,
            weapon_reach_ft=0  # No reach weapon
        )

        # SHOULD include adjacent squares
        assert Position(x=4, y=5) in aoo_squares
        assert Position(x=6, y=5) in aoo_squares
        assert len(aoo_squares) == 8

    def test_ring_at_distance_only_exact(self):
        """_get_ring_at_distance returns only exact distance."""
        pos = Position(x=5, y=5)
        ring = _get_ring_at_distance(pos, SizeCategory.MEDIUM, 2)

        # All squares should be exactly distance 2
        for sq in ring:
            dist = _discrete_distance(pos, sq)
            assert dist == 2

    def test_large_with_reach_weapon(self):
        """Large creature with reach weapon threatens at weapon distance only."""
        pos = Position(x=5, y=5)  # 2x2 footprint
        aoo_squares = get_aoo_eligible_squares(
            entity_pos=pos,
            size=SizeCategory.LARGE,
            natural_reach_ft=10,
            weapon_reach_ft=15
        )

        # Should NOT include distance 1-2 squares (natural reach)
        # Should only include distance 3 squares
        for sq in aoo_squares:
            # Must be exactly distance 3 from nearest occupied square
            occupied = _get_occupied_squares(pos, SizeCategory.LARGE)
            min_dist = min(_discrete_distance(sq, occ) for occ in occupied)
            assert min_dist == 3


# ==============================================================================
# IS_SQUARE_THREATENED TESTS
# ==============================================================================

class TestIsSquareThreatened:
    """Tests for is_square_threatened() function."""

    def test_adjacent_is_threatened_5ft(self):
        """Adjacent square is threatened with 5ft reach."""
        entity_pos = Position(x=5, y=5)
        target_pos = Position(x=6, y=5)
        assert is_square_threatened(entity_pos, SizeCategory.MEDIUM, 5, target_pos)

    def test_distance_2_not_threatened_5ft(self):
        """Distance 2 square is NOT threatened with 5ft reach."""
        entity_pos = Position(x=5, y=5)
        target_pos = Position(x=7, y=5)
        assert not is_square_threatened(entity_pos, SizeCategory.MEDIUM, 5, target_pos)

    def test_distance_2_threatened_10ft(self):
        """Distance 2 square IS threatened with 10ft reach."""
        entity_pos = Position(x=5, y=5)
        target_pos = Position(x=7, y=5)
        assert is_square_threatened(entity_pos, SizeCategory.MEDIUM, 10, target_pos)

    def test_own_square_not_threatened(self):
        """Entity's own square is not threatened."""
        entity_pos = Position(x=5, y=5)
        assert not is_square_threatened(entity_pos, SizeCategory.MEDIUM, 5, entity_pos)

    def test_occupied_square_not_threatened(self):
        """Large creature's occupied squares are not threatened."""
        entity_pos = Position(x=5, y=5)  # 2x2 at (5,5), (6,5), (5,6), (6,6)
        # Check an occupied square
        assert not is_square_threatened(entity_pos, SizeCategory.LARGE, 10, Position(x=6, y=6))

    def test_zero_reach_threatens_nothing(self):
        """Zero reach never threatens."""
        entity_pos = Position(x=5, y=5)
        target_pos = Position(x=6, y=5)
        assert not is_square_threatened(entity_pos, SizeCategory.FINE, 0, target_pos)


# ==============================================================================
# CAN_THREATEN TESTS
# ==============================================================================

class TestCanThreaten:
    """Tests for can_threaten() function."""

    def test_medium_vs_medium_adjacent_true(self):
        """Medium threatens adjacent Medium."""
        attacker = Position(x=5, y=5)
        target = Position(x=6, y=5)
        assert can_threaten(attacker, SizeCategory.MEDIUM, 5, target, SizeCategory.MEDIUM)

    def test_medium_vs_medium_distance_2_false_5ft(self):
        """Medium with 5ft reach doesn't threaten Medium at distance 2."""
        attacker = Position(x=5, y=5)
        target = Position(x=7, y=5)
        assert not can_threaten(attacker, SizeCategory.MEDIUM, 5, target, SizeCategory.MEDIUM)

    def test_medium_with_reach_vs_medium_distance_2_true(self):
        """Medium with 10ft reach threatens Medium at distance 2."""
        attacker = Position(x=5, y=5)
        target = Position(x=7, y=5)
        assert can_threaten(attacker, SizeCategory.MEDIUM, 10, target, SizeCategory.MEDIUM)

    def test_large_vs_medium_correct_distance(self):
        """Large creature threatens from all occupied squares."""
        attacker = Position(x=5, y=5)  # 2x2
        # Target at (8,5) is distance 2 from (6,5) occupied square
        target = Position(x=8, y=5)
        assert can_threaten(attacker, SizeCategory.LARGE, 10, target, SizeCategory.MEDIUM)

    def test_same_square_false(self):
        """Cannot threaten if on same square (distance 0)."""
        pos = Position(x=5, y=5)
        assert not can_threaten(pos, SizeCategory.MEDIUM, 5, pos, SizeCategory.MEDIUM)

    def test_medium_vs_large_target(self):
        """Medium threatens Large if any Large square is in reach."""
        attacker = Position(x=5, y=5)
        # Large target at (7,5) occupies (7,5), (8,5), (7,6), (8,6)
        # (7,5) is distance 2 from attacker
        target = Position(x=7, y=5)
        # With 5ft reach, cannot threaten
        assert not can_threaten(attacker, SizeCategory.MEDIUM, 5, target, SizeCategory.LARGE)
        # With 10ft reach, can threaten (7,5)
        assert can_threaten(attacker, SizeCategory.MEDIUM, 10, target, SizeCategory.LARGE)


# ==============================================================================
# GET_THREATENED_SQUARES_FOR_ENTITY TESTS
# ==============================================================================

class TestGetThreatenedSquaresForEntity:
    """Tests for get_threatened_squares_for_entity() with BattleGrid."""

    def test_entity_on_grid(self):
        """Get threatened squares for entity tracked on grid."""
        grid = BattleGrid(20, 20)
        grid.place_entity("fighter", Position(x=5, y=5), SizeCategory.MEDIUM)

        threatened = get_threatened_squares_for_entity(grid, "fighter", 5)
        assert len(threatened) == 8

    def test_large_entity_on_grid(self):
        """Large entity tracked on grid threatens correctly."""
        grid = BattleGrid(20, 20)
        grid.place_entity("ogre", Position(x=5, y=5), SizeCategory.LARGE)

        threatened = get_threatened_squares_for_entity(grid, "ogre", 10)
        # Large with 10ft reach should threaten many squares
        assert len(threatened) > 16

    def test_unknown_entity_returns_empty(self):
        """Unknown entity returns empty list."""
        grid = BattleGrid(20, 20)
        threatened = get_threatened_squares_for_entity(grid, "unknown", 5)
        assert threatened == []


# ==============================================================================
# EDGE CASE TESTS
# ==============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_creature_at_map_boundary(self):
        """Creature at boundary doesn't crash."""
        pos = Position(x=0, y=0)
        threatened = get_threatened_squares(pos, SizeCategory.MEDIUM, 5, grid_width=10, grid_height=10)
        # Should only include valid squares
        assert all(0 <= sq.x < 10 and 0 <= sq.y < 10 for sq in threatened)

    def test_large_creature_near_boundary(self):
        """Large creature near boundary handles correctly."""
        pos = Position(x=8, y=8)  # 2x2 at (8,8), (9,8), (8,9), (9,9)
        threatened = get_threatened_squares(pos, SizeCategory.LARGE, 10, grid_width=10, grid_height=10)
        # Should only include valid squares
        assert all(0 <= sq.x < 10 and 0 <= sq.y < 10 for sq in threatened)

    def test_deterministic_ordering(self):
        """Threatened squares are returned in deterministic order."""
        pos = Position(x=5, y=5)
        t1 = get_threatened_squares(pos, SizeCategory.MEDIUM, 5)
        t2 = get_threatened_squares(pos, SizeCategory.MEDIUM, 5)
        assert t1 == t2

    def test_negative_reach_threatens_none(self):
        """Negative reach (edge case) threatens nothing."""
        pos = Position(x=5, y=5)
        threatened = get_threatened_squares(pos, SizeCategory.MEDIUM, -5)
        assert len(threatened) == 0


# ==============================================================================
# COUNT VERIFICATION TESTS
# ==============================================================================

class TestCountVerification:
    """Verify threatened square counts match expected values."""

    def test_medium_5ft_reach_count(self):
        """Medium with 5ft reach threatens 8 squares (center of grid)."""
        pos = Position(x=50, y=50)
        threatened = get_threatened_squares(pos, SizeCategory.MEDIUM, 5)
        assert len(threatened) == 8

    def test_medium_10ft_reach_count(self):
        """Medium with 10ft reach threatens 24 squares (8 at d1 + 16 at d2)."""
        pos = Position(x=50, y=50)
        threatened = get_threatened_squares(pos, SizeCategory.MEDIUM, 10)
        # Distance 1: 8 squares
        # Distance 2: 16 squares (ring around the 8)
        assert len(threatened) == 24

    def test_reach_weapon_ring_count(self):
        """10ft reach weapon threatens 16 squares (ring at distance 2 only)."""
        pos = Position(x=50, y=50)
        aoo_squares = get_aoo_eligible_squares(
            entity_pos=pos,
            size=SizeCategory.MEDIUM,
            natural_reach_ft=5,
            weapon_reach_ft=10
        )
        assert len(aoo_squares) == 16
