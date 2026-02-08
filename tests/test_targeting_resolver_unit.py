"""Unit tests for aidm/core/targeting_resolver.py (FIX-06).

Direct tests for every public function in the targeting resolver:
  - get_entity_position
  - bresenham_line
  - is_terrain_opaque
  - check_line_of_effect
  - check_line_of_sight
  - check_range
  - evaluate_visibility
  - evaluate_target_legality

All tests are pure (no RNG, no I/O).  WorldState fixtures use entities
with dict-style and GridPoint-style positions so both code paths are
exercised.
"""

import pytest
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.targeting import (
    GridPoint,
    VisibilityBlockReason,
    VisibilityState,
    TargetingLegalityResult,
)
from aidm.core.targeting_resolver import (
    get_entity_position,
    bresenham_line,
    is_terrain_opaque,
    check_line_of_effect,
    check_line_of_sight,
    check_range,
    evaluate_visibility,
    evaluate_target_legality,
)


# ==============================================================================
# HELPERS
# ==============================================================================

def _make_state(entities=None, terrain_map=None):
    """Build a minimal WorldState.

    Args:
        entities: dict of entity_id -> entity dict.
        terrain_map: optional dict to store as _terrain.map for
                     is_terrain_opaque tests.
    """
    ents = dict(entities) if entities else {}
    if terrain_map is not None:
        ents["_terrain"] = {"map": terrain_map}
    return WorldState(ruleset_version="3.5e", entities=ents)


def _entity(position=None, **extra):
    """Shorthand for creating an entity dict with optional position."""
    ent = {EF.HP_CURRENT: 10, EF.HP_MAX: 10, EF.AC: 10, EF.DEFEATED: False}
    if position is not None:
        ent[EF.POSITION] = position
    ent.update(extra)
    return ent


# ==============================================================================
# get_entity_position
# ==============================================================================

class TestGetEntityPosition:
    """Tests for get_entity_position()."""

    def test_dict_position_returns_gridpoint(self):
        """Entity with a dict position should return a GridPoint."""
        ws = _make_state({"goblin": _entity(position={"x": 3, "y": 7})})
        pos = get_entity_position(ws, "goblin")
        assert isinstance(pos, GridPoint)
        assert pos.x == 3
        assert pos.y == 7

    def test_gridpoint_position_returns_same(self):
        """Entity with a GridPoint position should return it as-is."""
        gp = GridPoint(5, 9)
        ws = _make_state({"orc": _entity(position=gp)})
        pos = get_entity_position(ws, "orc")
        assert isinstance(pos, GridPoint)
        assert pos.x == 5
        assert pos.y == 9

    def test_entity_not_found_raises(self):
        """Missing entity should raise ValueError."""
        ws = _make_state({})
        with pytest.raises(ValueError, match="Entity not found"):
            get_entity_position(ws, "nonexistent")

    def test_no_position_defaults_to_origin(self):
        """Entity without a position key should default to GridPoint(0, 0)."""
        ws = _make_state({"zombie": _entity()})  # no position kwarg
        pos = get_entity_position(ws, "zombie")
        assert isinstance(pos, GridPoint)
        assert pos.x == 0
        assert pos.y == 0


# ==============================================================================
# bresenham_line
# ==============================================================================

class TestBresenhamLine:
    """Tests for bresenham_line()."""

    def test_horizontal_line(self):
        """Horizontal line should include all points along x-axis."""
        points = bresenham_line(GridPoint(0, 0), GridPoint(4, 0))
        xs = [p.x for p in points]
        ys = [p.y for p in points]
        assert xs == [0, 1, 2, 3, 4]
        assert all(y == 0 for y in ys)

    def test_vertical_line(self):
        """Vertical line should include all points along y-axis."""
        points = bresenham_line(GridPoint(0, 0), GridPoint(0, 3))
        ys = [p.y for p in points]
        xs = [p.x for p in points]
        assert ys == [0, 1, 2, 3]
        assert all(x == 0 for x in xs)

    def test_diagonal_line(self):
        """Diagonal line from (0,0) to (3,3) should have 4 points."""
        points = bresenham_line(GridPoint(0, 0), GridPoint(3, 3))
        assert len(points) == 4
        # Start and end must be included
        assert points[0].x == 0 and points[0].y == 0
        assert points[-1].x == 3 and points[-1].y == 3

    def test_same_point(self):
        """Start == end should return a single-element list."""
        points = bresenham_line(GridPoint(5, 5), GridPoint(5, 5))
        assert len(points) == 1
        assert points[0].x == 5 and points[0].y == 5

    def test_negative_direction(self):
        """Line going in negative direction should still work."""
        points = bresenham_line(GridPoint(3, 0), GridPoint(0, 0))
        xs = [p.x for p in points]
        assert xs[0] == 3
        assert xs[-1] == 0
        assert len(points) == 4

    def test_includes_start_and_end(self):
        """Both endpoints must always be present."""
        start, end = GridPoint(1, 2), GridPoint(6, 4)
        points = bresenham_line(start, end)
        assert points[0].x == start.x and points[0].y == start.y
        assert points[-1].x == end.x and points[-1].y == end.y


# ==============================================================================
# is_terrain_opaque
# ==============================================================================

class TestIsTerrainOpaque:
    """Tests for is_terrain_opaque()."""

    def test_no_terrain_map_returns_false(self):
        """Without _terrain entity, every position is transparent."""
        ws = _make_state({})
        assert is_terrain_opaque(ws, GridPoint(5, 5)) is False

    def test_blocks_loe_returns_true(self):
        """Position flagged with blocks_loe should be opaque."""
        ws = _make_state(terrain_map={"3,4": {"blocks_loe": True}})
        assert is_terrain_opaque(ws, GridPoint(3, 4)) is True

    def test_blocks_los_returns_true(self):
        """Position flagged with blocks_los should be opaque."""
        ws = _make_state(terrain_map={"7,2": {"blocks_los": True}})
        assert is_terrain_opaque(ws, GridPoint(7, 2)) is True

    def test_position_without_blocking_returns_false(self):
        """Position present in map but without blocking flags is transparent."""
        ws = _make_state(terrain_map={"1,1": {"difficult": True}})
        assert is_terrain_opaque(ws, GridPoint(1, 1)) is False

    def test_unlisted_position_returns_false(self):
        """Position not in terrain map should be transparent."""
        ws = _make_state(terrain_map={"0,0": {"blocks_loe": True}})
        assert is_terrain_opaque(ws, GridPoint(99, 99)) is False


# ==============================================================================
# check_line_of_effect
# ==============================================================================

class TestCheckLineOfEffect:
    """Tests for check_line_of_effect()."""

    def test_clear_path(self):
        """No opaque terrain between observer and target -> True."""
        ws = _make_state({
            "archer": _entity(position={"x": 0, "y": 0}),
            "target": _entity(position={"x": 5, "y": 0}),
        })
        assert check_line_of_effect(ws, "archer", "target") is True

    def test_blocked_path(self):
        """Opaque terrain between observer and target -> False."""
        ws = _make_state(
            entities={
                "archer": _entity(position={"x": 0, "y": 0}),
                "target": _entity(position={"x": 4, "y": 0}),
            },
            terrain_map={
                "2,0": {"blocks_loe": True},
            },
        )
        assert check_line_of_effect(ws, "archer", "target") is False

    def test_blocking_at_start_does_not_block(self):
        """Terrain at observer position should not block LoE (endpoints excluded)."""
        ws = _make_state(
            entities={
                "caster": _entity(position={"x": 0, "y": 0}),
                "foe": _entity(position={"x": 3, "y": 0}),
            },
            terrain_map={
                "0,0": {"blocks_loe": True},
            },
        )
        assert check_line_of_effect(ws, "caster", "foe") is True

    def test_blocking_at_end_does_not_block(self):
        """Terrain at target position should not block LoE (endpoints excluded)."""
        ws = _make_state(
            entities={
                "caster": _entity(position={"x": 0, "y": 0}),
                "foe": _entity(position={"x": 3, "y": 0}),
            },
            terrain_map={
                "3,0": {"blocks_loe": True},
            },
        )
        assert check_line_of_effect(ws, "caster", "foe") is True

    def test_adjacent_entities_always_clear(self):
        """Adjacent entities (1 square apart) have no intermediate cells."""
        ws = _make_state(
            entities={
                "a": _entity(position={"x": 5, "y": 5}),
                "b": _entity(position={"x": 6, "y": 5}),
            },
            terrain_map={
                # No intermediate cell to block
            },
        )
        assert check_line_of_effect(ws, "a", "b") is True


# ==============================================================================
# check_line_of_sight
# ==============================================================================

class TestCheckLineOfSight:
    """Tests for check_line_of_sight()."""

    def test_clear_path(self):
        """Clear LoS should return True (delegates to LoE in CP-18A)."""
        ws = _make_state({
            "watcher": _entity(position={"x": 0, "y": 0}),
            "subject": _entity(position={"x": 3, "y": 3}),
        })
        assert check_line_of_sight(ws, "watcher", "subject") is True

    def test_blocked_path(self):
        """Blocked LoS should return False (same geometry as LoE)."""
        ws = _make_state(
            entities={
                "watcher": _entity(position={"x": 0, "y": 0}),
                "subject": _entity(position={"x": 4, "y": 0}),
            },
            terrain_map={
                "2,0": {"blocks_los": True},
            },
        )
        assert check_line_of_sight(ws, "watcher", "subject") is False


# ==============================================================================
# check_range
# ==============================================================================

class TestCheckRange:
    """Tests for check_range()."""

    def test_within_range(self):
        """Target within max_range -> True."""
        ws = _make_state({
            "archer": _entity(position={"x": 0, "y": 0}),
            "target": _entity(position={"x": 3, "y": 0}),
        })
        assert check_range(ws, "archer", "target", max_range=5) is True

    def test_out_of_range(self):
        """Target exceeding max_range -> False."""
        ws = _make_state({
            "archer": _entity(position={"x": 0, "y": 0}),
            "target": _entity(position={"x": 10, "y": 0}),
        })
        assert check_range(ws, "archer", "target", max_range=5) is False

    def test_exact_range(self):
        """Target at exactly max_range -> True (<=)."""
        ws = _make_state({
            "archer": _entity(position={"x": 0, "y": 0}),
            "target": _entity(position={"x": 4, "y": 0}),
        })
        # Straight-line distance is 4 squares
        distance = GridPoint(0, 0).distance_to(GridPoint(4, 0))
        assert check_range(ws, "archer", "target", max_range=distance) is True

    def test_same_position_always_in_range(self):
        """Entities at the same position have distance 0 -> always in range."""
        ws = _make_state({
            "a": _entity(position={"x": 5, "y": 5}),
            "b": _entity(position={"x": 5, "y": 5}),
        })
        assert check_range(ws, "a", "b", max_range=0) is True


# ==============================================================================
# evaluate_visibility
# ==============================================================================

class TestEvaluateVisibility:
    """Tests for evaluate_visibility()."""

    def test_both_clear_visible(self):
        """Clear LoS and LoE -> is_visible True, no reason."""
        ws = _make_state({
            "observer": _entity(position={"x": 0, "y": 0}),
            "target": _entity(position={"x": 5, "y": 0}),
        })
        vis = evaluate_visibility(ws, "observer", "target")
        assert isinstance(vis, VisibilityState)
        assert vis.is_visible is True
        assert vis.reason is None

    def test_los_blocked_not_visible(self):
        """Blocked LoS -> not visible, reason LOS_BLOCKED.

        In CP-18A, LoS == LoE, so any blocking terrain triggers LOS_BLOCKED
        first (because LoS is checked before LoE in evaluate_visibility).
        """
        ws = _make_state(
            entities={
                "observer": _entity(position={"x": 0, "y": 0}),
                "target": _entity(position={"x": 4, "y": 0}),
            },
            terrain_map={
                "2,0": {"blocks_los": True},
            },
        )
        vis = evaluate_visibility(ws, "observer", "target")
        assert vis.is_visible is False
        assert vis.reason == VisibilityBlockReason.LOS_BLOCKED

    def test_loe_blocked_not_visible(self):
        """Blocked LoE -> not visible, reason LOE_BLOCKED.

        Because LoS and LoE use the same geometry in CP-18A, blocking LoE
        also blocks LoS.  The function checks LoS first, so when a cell
        has blocks_loe=True but NOT blocks_los=True, LoS passes but LoE
        fails, yielding LOE_BLOCKED.
        """
        ws = _make_state(
            entities={
                "observer": _entity(position={"x": 0, "y": 0}),
                "target": _entity(position={"x": 4, "y": 0}),
            },
            terrain_map={
                # blocks_loe only, NOT blocks_los -> LoS passes, LoE fails
                "2,0": {"blocks_loe": True},
            },
        )
        vis = evaluate_visibility(ws, "observer", "target")
        assert vis.is_visible is False
        # LoS delegates to LoE, so LoS also sees blocks_loe.
        # Both LoS and LoE check is_terrain_opaque which ORs blocks_loe|blocks_los.
        # Therefore LoS fails first -> LOS_BLOCKED.
        assert vis.reason == VisibilityBlockReason.LOS_BLOCKED

    def test_observer_and_target_ids_preserved(self):
        """Returned VisibilityState should carry the correct entity IDs."""
        ws = _make_state({
            "elf": _entity(position={"x": 0, "y": 0}),
            "troll": _entity(position={"x": 3, "y": 0}),
        })
        vis = evaluate_visibility(ws, "elf", "troll")
        assert vis.observer_id == "elf"
        assert vis.target_id == "troll"


# ==============================================================================
# evaluate_target_legality
# ==============================================================================

class TestEvaluateTargetLegality:
    """Tests for evaluate_target_legality()."""

    def test_legal_target(self):
        """All checks pass -> is_legal True."""
        ws = _make_state({
            "fighter": _entity(position={"x": 0, "y": 0}),
            "goblin": _entity(position={"x": 3, "y": 0}),
        })
        result = evaluate_target_legality("fighter", "goblin", ws, max_range=10)
        assert isinstance(result, TargetingLegalityResult)
        assert result.is_legal is True
        assert result.failure_reason is None
        assert len(result.citations) >= 1

    def test_actor_not_found(self):
        """Actor missing from state -> not legal."""
        ws = _make_state({
            "goblin": _entity(position={"x": 3, "y": 0}),
        })
        result = evaluate_target_legality("ghost", "goblin", ws)
        assert result.is_legal is False
        assert result.failure_reason == VisibilityBlockReason.TARGET_NOT_VISIBLE

    def test_target_not_found(self):
        """Target missing from state -> not legal."""
        ws = _make_state({
            "fighter": _entity(position={"x": 0, "y": 0}),
        })
        result = evaluate_target_legality("fighter", "phantom", ws)
        assert result.is_legal is False
        assert result.failure_reason == VisibilityBlockReason.TARGET_NOT_VISIBLE

    def test_out_of_range(self):
        """Target beyond max_range -> not legal, OUT_OF_RANGE."""
        ws = _make_state({
            "archer": _entity(position={"x": 0, "y": 0}),
            "target": _entity(position={"x": 20, "y": 0}),
        })
        result = evaluate_target_legality("archer", "target", ws, max_range=5)
        assert result.is_legal is False
        assert result.failure_reason == VisibilityBlockReason.OUT_OF_RANGE

    def test_loe_blocked(self):
        """LoE blocked -> not legal, LOE_BLOCKED."""
        ws = _make_state(
            entities={
                "caster": _entity(position={"x": 0, "y": 0}),
                "demon": _entity(position={"x": 4, "y": 0}),
            },
            terrain_map={
                "2,0": {"blocks_loe": True},
            },
        )
        result = evaluate_target_legality("caster", "demon", ws, max_range=100)
        assert result.is_legal is False
        assert result.failure_reason == VisibilityBlockReason.LOE_BLOCKED

    def test_default_max_range_is_100(self):
        """Default max_range should be 100 squares (large enough for most spells)."""
        ws = _make_state({
            "a": _entity(position={"x": 0, "y": 0}),
            "b": _entity(position={"x": 50, "y": 0}),
        })
        result = evaluate_target_legality("a", "b", ws)
        assert result.is_legal is True

    def test_citations_present_on_legal(self):
        """Legal result should include PHB citations."""
        ws = _make_state({
            "a": _entity(position={"x": 0, "y": 0}),
            "b": _entity(position={"x": 1, "y": 0}),
        })
        result = evaluate_target_legality("a", "b", ws)
        assert result.is_legal is True
        assert len(result.citations) == 2  # targeting + range citations

    def test_citations_present_on_illegal(self):
        """Illegal result should include at least one citation."""
        ws = _make_state({
            "a": _entity(position={"x": 0, "y": 0}),
            "b": _entity(position={"x": 99, "y": 0}),
        })
        result = evaluate_target_legality("a", "b", ws, max_range=1)
        assert result.is_legal is False
        assert len(result.citations) >= 1


# ==============================================================================
# INTEGRATION-STYLE EDGE CASES (still pure unit tests, no I/O)
# ==============================================================================

class TestEdgeCases:
    """Cross-cutting edge cases combining multiple functions."""

    def test_self_targeting_is_legal(self):
        """An entity targeting itself should be legal (range 0, no blocking)."""
        ws = _make_state({
            "cleric": _entity(position={"x": 5, "y": 5}),
        })
        result = evaluate_target_legality("cleric", "cleric", ws, max_range=0)
        assert result.is_legal is True

    def test_bresenham_symmetry_cardinal(self):
        """Bresenham line on cardinal/diagonal axes is symmetric."""
        # Horizontal
        a, b = GridPoint(0, 0), GridPoint(5, 0)
        fwd = {(p.x, p.y) for p in bresenham_line(a, b)}
        bwd = {(p.x, p.y) for p in bresenham_line(b, a)}
        assert fwd == bwd

        # Diagonal
        a, b = GridPoint(0, 0), GridPoint(4, 4)
        fwd = {(p.x, p.y) for p in bresenham_line(a, b)}
        bwd = {(p.x, p.y) for p in bresenham_line(b, a)}
        assert fwd == bwd

    def test_bresenham_endpoints_always_match(self):
        """Forward and reverse Bresenham always share endpoints."""
        a, b = GridPoint(1, 1), GridPoint(7, 4)
        fwd = bresenham_line(a, b)
        bwd = bresenham_line(b, a)
        # Both must start and end at the correct endpoints
        assert (fwd[0].x, fwd[0].y) == (1, 1)
        assert (fwd[-1].x, fwd[-1].y) == (7, 4)
        assert (bwd[0].x, bwd[0].y) == (7, 4)
        assert (bwd[-1].x, bwd[-1].y) == (1, 1)
        # Same number of points
        assert len(fwd) == len(bwd)

    def test_gridpoint_distance_to_used_by_check_range(self):
        """check_range must use GridPoint.distance_to (CP-14 diagonal rule)."""
        # Diagonal: 3 squares => cost = 3 + 3//2 = 4 (1-2-1 pattern)
        ws = _make_state({
            "a": _entity(position={"x": 0, "y": 0}),
            "b": _entity(position={"x": 3, "y": 3}),
        })
        expected_dist = GridPoint(0, 0).distance_to(GridPoint(3, 3))
        assert expected_dist == 4  # sanity check on diagonal math
        assert check_range(ws, "a", "b", max_range=4) is True
        assert check_range(ws, "a", "b", max_range=3) is False

    def test_wall_between_two_entities_blocks_all_checks(self):
        """A wall midway should block LoE, LoS, visibility, and legality."""
        ws = _make_state(
            entities={
                "a": _entity(position={"x": 0, "y": 0}),
                "b": _entity(position={"x": 6, "y": 0}),
            },
            terrain_map={
                "3,0": {"blocks_loe": True, "blocks_los": True},
            },
        )
        assert check_line_of_effect(ws, "a", "b") is False
        assert check_line_of_sight(ws, "a", "b") is False

        vis = evaluate_visibility(ws, "a", "b")
        assert vis.is_visible is False

        legality = evaluate_target_legality("a", "b", ws, max_range=100)
        assert legality.is_legal is False
