"""Unit tests for canonical Position type (CP-001).

This module tests the canonical Position type that consolidates three legacy
position types (GridPoint from intents.py, GridPoint from targeting.py, and
GridPosition from attack.py).

INTRODUCED: CP-001 (Position Type Unification)
RESOLVES: TD-001 (Three Duplicate Grid Position Types)
"""

import pytest
from aidm.schemas.position import (
    Position,
    from_legacy_gridpoint_intents,
    from_legacy_gridpoint_targeting,
    from_legacy_gridposition_attack,
    to_legacy_dict,
)


# =============================================================================
# Tier-1 Tests: Position Creation & Validation
# =============================================================================

class TestPositionCreation:
    """Tests for Position creation and validation."""

    def test_position_creation_valid(self):
        """Should create Position with valid integer coordinates."""
        pos = Position(x=5, y=10)
        assert pos.x == 5
        assert pos.y == 10

    def test_position_creation_negative_coords(self):
        """Should allow negative coordinates (for grids with negative indices)."""
        pos = Position(x=-3, y=-7)
        assert pos.x == -3
        assert pos.y == -7

    def test_position_creation_zero_coords(self):
        """Should allow zero coordinates."""
        pos = Position(x=0, y=0)
        assert pos.x == 0
        assert pos.y == 0

    def test_position_creation_invalid_types(self):
        """Should reject non-integer coordinates."""
        with pytest.raises(TypeError, match="Position coordinates must be integers"):
            Position(x="5", y=10)

        with pytest.raises(TypeError, match="Position coordinates must be integers"):
            Position(x=5, y=10.5)

        with pytest.raises(TypeError, match="Position coordinates must be integers"):
            Position(x=5.0, y=10)


# =============================================================================
# Tier-1 Tests: Distance Calculation
# =============================================================================

class TestDistanceTo:
    """Tests for distance_to() method (PHB p.145 movement rules)."""

    def test_distance_to_orthogonal_horizontal(self):
        """Horizontal distance: (0,0) to (5,0) = 25 feet (5 squares × 5 feet)."""
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=5, y=0)
        assert pos1.distance_to(pos2) == 25
        assert pos2.distance_to(pos1) == 25  # Symmetric

    def test_distance_to_orthogonal_vertical(self):
        """Vertical distance: (0,0) to (0,5) = 25 feet (5 squares × 5 feet)."""
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=0, y=5)
        assert pos1.distance_to(pos2) == 25
        assert pos2.distance_to(pos1) == 25  # Symmetric

    def test_distance_to_diagonal(self):
        """Diagonal distance using 1-2-1-2 rule (PHB p.148).

        (0,0) to (3,3): 3 diagonal moves
        - 1st diagonal: 5 feet
        - 2nd diagonal: 10 feet
        - 3rd diagonal: 5 feet
        Total: 5 + 10 + 5 = 20 feet
        """
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=3, y=3)
        assert pos1.distance_to(pos2) == 20
        assert pos2.distance_to(pos1) == 20  # Symmetric

    def test_distance_to_mixed(self):
        """Mixed orthogonal/diagonal using 1-2-1-2 rule.

        (0,0) to (3,5): dx=3, dy=5
        - 3 diagonals: 5 + 10 + 5 = 20 feet
        - 2 orthogonal: 2 × 5 = 10 feet
        Total: 20 + 10 = 30 feet
        """
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=3, y=5)
        assert pos1.distance_to(pos2) == 30
        assert pos2.distance_to(pos1) == 30  # Symmetric

    def test_distance_to_self(self):
        """Distance to self = 0."""
        pos = Position(x=5, y=10)
        assert pos.distance_to(pos) == 0

    def test_distance_to_negative_coords(self):
        """Distance calculation works with negative coordinates.

        pos1=(-2,-3) to pos2=(2,3): dx=4, dy=6
        - 4 diagonals: 5 + 10 + 5 + 10 = 30 feet (2 pairs)
        - 2 orthogonal: 2 × 5 = 10 feet
        Total: 30 + 10 = 40 feet
        """
        pos1 = Position(x=-2, y=-3)
        pos2 = Position(x=2, y=3)
        assert pos1.distance_to(pos2) == 40


# =============================================================================
# Tier-1 Tests: Adjacency Checks
# =============================================================================

class TestIsAdjacentTo:
    """Tests for is_adjacent_to() method (PHB p.137 adjacency rules)."""

    def test_is_adjacent_orthogonal_right(self):
        """Orthogonal adjacency: (0,0) and (1,0) are adjacent."""
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=1, y=0)
        assert pos1.is_adjacent_to(pos2)
        assert pos2.is_adjacent_to(pos1)  # Symmetric

    def test_is_adjacent_orthogonal_down(self):
        """Orthogonal adjacency: (0,0) and (0,1) are adjacent."""
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=0, y=1)
        assert pos1.is_adjacent_to(pos2)
        assert pos2.is_adjacent_to(pos1)  # Symmetric

    def test_is_adjacent_diagonal(self):
        """Diagonal adjacency: (0,0) and (1,1) are adjacent (PHB p.137)."""
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=1, y=1)
        assert pos1.is_adjacent_to(pos2)
        assert pos2.is_adjacent_to(pos1)  # Symmetric

    def test_is_adjacent_not_orthogonal(self):
        """Non-adjacent: (0,0) and (2,0) are NOT adjacent."""
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=2, y=0)
        assert not pos1.is_adjacent_to(pos2)
        assert not pos2.is_adjacent_to(pos1)  # Symmetric

    def test_is_adjacent_not_diagonal(self):
        """Non-adjacent: (0,0) and (2,2) are NOT adjacent."""
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=2, y=2)
        assert not pos1.is_adjacent_to(pos2)
        assert not pos2.is_adjacent_to(pos1)  # Symmetric

    def test_is_adjacent_self(self):
        """A position is NOT adjacent to itself."""
        pos = Position(x=5, y=10)
        assert not pos.is_adjacent_to(pos)

    def test_is_adjacent_all_eight_directions(self):
        """All 8 surrounding squares are adjacent (PHB p.137)."""
        center = Position(x=5, y=5)
        adjacent_positions = [
            Position(x=4, y=4),  # NW
            Position(x=5, y=4),  # N
            Position(x=6, y=4),  # NE
            Position(x=4, y=5),  # W
            Position(x=6, y=5),  # E
            Position(x=4, y=6),  # SW
            Position(x=5, y=6),  # S
            Position(x=6, y=6),  # SE
        ]
        for pos in adjacent_positions:
            assert center.is_adjacent_to(pos), f"{center} should be adjacent to {pos}"


# =============================================================================
# Tier-1 Tests: Serialization & Deserialization
# =============================================================================

class TestSerialization:
    """Tests for to_dict() and from_dict() methods."""

    def test_to_dict_serialization(self):
        """to_dict() should produce {"x": int, "y": int}."""
        pos = Position(x=7, y=13)
        result = pos.to_dict()
        assert result == {"x": 7, "y": 13}
        assert isinstance(result, dict)

    def test_from_dict_deserialization(self):
        """from_dict() should reconstruct Position from dict."""
        data = {"x": 7, "y": 13}
        pos = Position.from_dict(data)
        assert pos.x == 7
        assert pos.y == 13

    def test_to_dict_from_dict_roundtrip(self):
        """to_dict() → from_dict() should be lossless."""
        original = Position(x=42, y=-17)
        roundtrip = Position.from_dict(original.to_dict())
        assert roundtrip == original

    def test_from_dict_missing_x(self):
        """from_dict() should raise KeyError if 'x' missing."""
        with pytest.raises(KeyError):
            Position.from_dict({"y": 10})

    def test_from_dict_missing_y(self):
        """from_dict() should raise KeyError if 'y' missing."""
        with pytest.raises(KeyError):
            Position.from_dict({"x": 10})

    def test_from_dict_invalid_type(self):
        """from_dict() should raise TypeError if x or y are not integers."""
        with pytest.raises(TypeError, match="Position coordinates must be integers"):
            Position.from_dict({"x": "5", "y": 10})


# =============================================================================
# Tier-1 Tests: Immutability
# =============================================================================

class TestImmutability:
    """Tests for Position immutability (frozen=True)."""

    def test_position_immutable_x(self):
        """Cannot modify Position.x after creation."""
        pos = Position(x=5, y=10)
        with pytest.raises(AttributeError):
            pos.x = 99

    def test_position_immutable_y(self):
        """Cannot modify Position.y after creation."""
        pos = Position(x=5, y=10)
        with pytest.raises(AttributeError):
            pos.y = 99


# =============================================================================
# Tier-1 Tests: Equality & Hashing
# =============================================================================

class TestEqualityAndHashing:
    """Tests for Position equality and hashability."""

    def test_position_equality_same_coords(self):
        """Position(1,2) == Position(1,2)."""
        pos1 = Position(x=1, y=2)
        pos2 = Position(x=1, y=2)
        assert pos1 == pos2

    def test_position_equality_different_coords(self):
        """Position(1,2) != Position(1,3)."""
        pos1 = Position(x=1, y=2)
        pos2 = Position(x=1, y=3)
        assert pos1 != pos2

    def test_position_hashable(self):
        """Position can be used in sets and as dict keys."""
        pos1 = Position(x=1, y=2)
        pos2 = Position(x=1, y=2)
        pos3 = Position(x=3, y=4)

        # Can create a set
        position_set = {pos1, pos2, pos3}
        assert len(position_set) == 2  # pos1 and pos2 are equal, so set has 2 items

        # Can use as dict key
        position_dict = {pos1: "location A", pos3: "location B"}
        assert position_dict[pos2] == "location A"  # pos2 == pos1


# =============================================================================
# Tier-1 Tests: String Representation
# =============================================================================

class TestStringRepresentation:
    """Tests for __str__ and __repr__ methods."""

    def test_str_representation(self):
        """__str__ should produce human-readable (x, y) format."""
        pos = Position(x=7, y=13)
        assert str(pos) == "(7, 13)"

    def test_repr_representation(self):
        """__repr__ should produce debug-friendly Position(x=..., y=...) format."""
        pos = Position(x=7, y=13)
        assert repr(pos) == "Position(x=7, y=13)"


# =============================================================================
# Tier-2 Tests: Legacy Conversion Helpers
# =============================================================================

class TestLegacyConversion:
    """Tests for backward compatibility conversion helpers (DEPRECATED)."""

    def test_legacy_gridpoint_targeting_conversion(self):
        """from_legacy_gridpoint_targeting() converts legacy GridPoint to Position."""
        # Create a mock legacy GridPoint (targeting.py style)
        class MockGridPoint:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        legacy_gp = MockGridPoint(x=10, y=20)
        pos = from_legacy_gridpoint_targeting(legacy_gp)
        assert pos.x == 10
        assert pos.y == 20

    def test_legacy_gridposition_attack_conversion(self):
        """from_legacy_gridposition_attack() converts legacy GridPosition to Position."""
        # Create a mock legacy GridPosition (attack.py style)
        class MockGridPosition:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        legacy_gpos = MockGridPosition(x=15, y=25)
        pos = from_legacy_gridposition_attack(legacy_gpos)
        assert pos.x == 15
        assert pos.y == 25

    def test_to_legacy_dict_conversion(self):
        """to_legacy_dict() converts Position to legacy dict format."""
        pos = Position(x=42, y=17)
        legacy_dict = to_legacy_dict(pos)
        assert legacy_dict == {"x": 42, "y": 17}


# =============================================================================
# PBHA Test: Determinism Verification
# =============================================================================

class TestDeterminism:
    """PBHA test: Position operations must be deterministic."""

    def test_position_operations_deterministic(self):
        """10 runs: same positions → identical distance/adjacency results.

        This test verifies that Position operations are fully deterministic:
        - Same inputs always produce same outputs
        - No floating-point drift
        - No randomness in distance/adjacency calculations
        """
        pos1 = Position(x=5, y=10)
        pos2 = Position(x=8, y=14)

        # Run 10 times and collect results
        distance_results = [pos1.distance_to(pos2) for _ in range(10)]
        adjacency_results = [pos1.is_adjacent_to(pos2) for _ in range(10)]

        # All results should be identical
        assert all(d == distance_results[0] for d in distance_results)
        assert all(a == adjacency_results[0] for a in adjacency_results)

        # Verify expected values using 1-2-1-2 diagonal math
        # dx = |8 - 5| = 3, dy = |14 - 10| = 4
        # 3 diagonals (5+10+5=20) + 1 orthogonal (5) = 25 feet
        assert distance_results[0] == 25
        assert adjacency_results[0] is False  # Not adjacent (distance > 1)
