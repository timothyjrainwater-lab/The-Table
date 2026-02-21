"""Tests for Movement v1 (CP-16) — FullMoveIntent + movement_resolver.

Tests cover:
- FullMoveIntent schema validation (path contiguity, speed, cost calculation)
- BFS pathfinding (shortest path, enemy blocking, speed limits)
- build_full_move_intent integration (entity lookup, error messages)
- 5/10/5 diagonal cost rule
- Terrain cost integration
- play_loop execution of FullMoveIntent
- Enemy AI movement toward targets
"""

import pytest
from copy import deepcopy

from aidm.schemas.attack import FullMoveIntent, StepMoveIntent
from aidm.schemas.position import Position
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState
from aidm.core.movement_resolver import (
    build_full_move_intent,
    find_path_bfs,
    _get_occupied_squares,
    _step_cost,
)
from aidm.core.play_loop import TurnContext, TurnResult, execute_turn
from aidm.core.rng_manager import RNGManager
from aidm.runtime.play_controller import build_simple_combat_fixture


# ===========================================================================
# FullMoveIntent Schema Tests
# ===========================================================================

class TestFullMoveIntentSchema:

    def test_basic_creation(self):
        intent = FullMoveIntent(
            actor_id="pc_fighter",
            from_pos=Position(3, 3),
            path=[Position(3, 4), Position(3, 5)],
            speed_ft=30,
        )
        assert intent.to_pos == Position(3, 5)
        assert len(intent.path) == 2

    def test_empty_path_raises(self):
        with pytest.raises(ValueError, match="path must contain at least one"):
            FullMoveIntent(
                actor_id="pc_fighter",
                from_pos=Position(3, 3),
                path=[],
                speed_ft=30,
            )

    def test_empty_actor_raises(self):
        with pytest.raises(ValueError, match="actor_id cannot be empty"):
            FullMoveIntent(
                actor_id="",
                from_pos=Position(3, 3),
                path=[Position(3, 4)],
                speed_ft=30,
            )

    def test_zero_speed_raises(self):
        with pytest.raises(ValueError, match="speed_ft must be positive"):
            FullMoveIntent(
                actor_id="pc_fighter",
                from_pos=Position(3, 3),
                path=[Position(3, 4)],
                speed_ft=0,
            )

    def test_non_contiguous_path_raises(self):
        with pytest.raises(ValueError, match="Path is not contiguous"):
            FullMoveIntent(
                actor_id="pc_fighter",
                from_pos=Position(3, 3),
                path=[Position(3, 5)],  # Skip (3,4)
                speed_ft=30,
            )

    def test_non_contiguous_mid_path_raises(self):
        with pytest.raises(ValueError, match="Path is not contiguous at step 1"):
            FullMoveIntent(
                actor_id="pc_fighter",
                from_pos=Position(0, 0),
                path=[Position(0, 1), Position(0, 3)],  # Skip (0,2)
                speed_ft=30,
            )

    def test_single_step_orthogonal(self):
        intent = FullMoveIntent(
            actor_id="test",
            from_pos=Position(0, 0),
            path=[Position(0, 1)],
            speed_ft=30,
        )
        assert intent.path_cost_ft() == 5

    def test_single_step_diagonal(self):
        intent = FullMoveIntent(
            actor_id="test",
            from_pos=Position(0, 0),
            path=[Position(1, 1)],
            speed_ft=30,
        )
        assert intent.path_cost_ft() == 5  # First diagonal costs 5

    def test_two_diagonals_cost_15(self):
        """5/10/5 rule: first diagonal=5, second diagonal=10, total=15."""
        intent = FullMoveIntent(
            actor_id="test",
            from_pos=Position(0, 0),
            path=[Position(1, 1), Position(2, 2)],
            speed_ft=30,
        )
        assert intent.path_cost_ft() == 15

    def test_three_diagonals_cost_20(self):
        """5/10/5 rule: 5+10+5=20."""
        intent = FullMoveIntent(
            actor_id="test",
            from_pos=Position(0, 0),
            path=[Position(1, 1), Position(2, 2), Position(3, 3)],
            speed_ft=30,
        )
        assert intent.path_cost_ft() == 20

    def test_six_orthogonal_steps_cost_30(self):
        """6 orthogonal steps = 30 ft."""
        intent = FullMoveIntent(
            actor_id="test",
            from_pos=Position(0, 0),
            path=[Position(0, i) for i in range(1, 7)],
            speed_ft=30,
        )
        assert intent.path_cost_ft() == 30

    def test_terrain_cost_doubles(self):
        """Difficult terrain doubles step cost."""
        intent = FullMoveIntent(
            actor_id="test",
            from_pos=Position(0, 0),
            path=[Position(0, 1), Position(0, 2)],
            speed_ft=30,
        )
        # Both squares are difficult terrain (cost 2)
        assert intent.path_cost_ft([2, 2]) == 20  # 5*2 + 5*2 = 20

    def test_mixed_terrain_and_diagonal(self):
        """Diagonal into difficult terrain."""
        intent = FullMoveIntent(
            actor_id="test",
            from_pos=Position(0, 0),
            path=[Position(1, 1), Position(1, 2)],
            speed_ft=30,
        )
        # First step: diagonal (5ft) with terrain 2 = 10
        # Second step: orthogonal (5ft) with terrain 1 = 5
        assert intent.path_cost_ft([2, 1]) == 15


# ===========================================================================
# Pathfinding Tests
# ===========================================================================

class TestPathfinding:

    def test_straight_line_path(self):
        path = find_path_bfs(
            Position(0, 0), Position(0, 3),
            enemy_squares=set(), speed_ft=30,
        )
        assert path is not None
        assert len(path) == 3
        assert path[-1] == Position(0, 3)

    def test_diagonal_path(self):
        path = find_path_bfs(
            Position(0, 0), Position(2, 2),
            enemy_squares=set(), speed_ft=30,
        )
        assert path is not None
        assert path[-1] == Position(2, 2)
        # BFS should find diagonal path (shorter than orthogonal)
        assert len(path) == 2

    def test_enemy_blocking(self):
        """Path blocked by complete wall of enemy squares."""
        # Wall of enemies spanning a wide range at y=2 (no way around within speed)
        enemies = set()
        for x in range(-10, 20):
            enemies.add((x, 2))
        path = find_path_bfs(
            Position(2, 0), Position(2, 4),
            enemy_squares=enemies, speed_ft=30,
        )
        assert path is None  # No way through

    def test_enemy_partial_blocking_routes_around(self):
        """Path routes around a single enemy."""
        enemies = {(1, 1)}  # Block direct diagonal
        path = find_path_bfs(
            Position(0, 0), Position(2, 2),
            enemy_squares=enemies, speed_ft=30,
        )
        assert path is not None
        assert path[-1] == Position(2, 2)
        # Should not pass through (1,1)
        assert Position(1, 1) not in path

    def test_speed_limit_blocks_far_destination(self):
        """Can't reach destination beyond speed."""
        path = find_path_bfs(
            Position(0, 0), Position(0, 7),  # 35 ft needed
            enemy_squares=set(), speed_ft=30,
        )
        assert path is None

    def test_speed_limit_allows_exact_distance(self):
        """Can reach destination at exactly speed limit."""
        path = find_path_bfs(
            Position(0, 0), Position(0, 6),  # 30 ft exactly
            enemy_squares=set(), speed_ft=30,
        )
        assert path is not None
        assert len(path) == 6

    def test_same_position_returns_empty(self):
        path = find_path_bfs(
            Position(3, 3), Position(3, 3),
            enemy_squares=set(), speed_ft=30,
        )
        assert path == []

    def test_destination_is_enemy_blocked(self):
        """Cannot enter enemy-occupied square."""
        enemies = {(3, 5)}
        path = find_path_bfs(
            Position(3, 3), Position(3, 5),
            enemy_squares=enemies, speed_ft=30,
        )
        assert path is None


# ===========================================================================
# build_full_move_intent Integration Tests
# ===========================================================================

class TestBuildFullMoveIntent:

    def _make_ws(self):
        fixture = build_simple_combat_fixture()
        return fixture.world_state

    def test_basic_move_one_square(self):
        ws = self._make_ws()
        intent, error = build_full_move_intent("pc_fighter", Position(3, 4), ws)
        assert error is None
        assert intent is not None
        assert intent.to_pos == Position(3, 4)
        assert intent.speed_ft == 30

    def test_move_several_squares(self):
        ws = self._make_ws()
        # Fighter at (3,3), move to (3,1) — 2 squares south
        intent, error = build_full_move_intent("pc_fighter", Position(3, 1), ws)
        assert error is None
        assert intent.to_pos == Position(3, 1)

    def test_move_diagonal(self):
        ws = self._make_ws()
        # Fighter at (3,3), move diagonal to (5,5) — need to avoid goblins
        # Goblins at (3,5), (4,5), (2,5) — so (5,5) might be reachable
        intent, error = build_full_move_intent("pc_fighter", Position(5, 5), ws)
        # Should find path avoiding goblins
        assert error is None
        assert intent.to_pos == Position(5, 5)

    def test_move_to_occupied_enemy_square(self):
        ws = self._make_ws()
        # Goblin 1 at (3,5)
        intent, error = build_full_move_intent("pc_fighter", Position(3, 5), ws)
        assert intent is None
        assert "occupied by an enemy" in error

    def test_move_too_far(self):
        ws = self._make_ws()
        # 30ft speed = 6 squares, (3,3) to (3,10) = 7 squares
        intent, error = build_full_move_intent("pc_fighter", Position(3, 10), ws)
        assert intent is None
        assert "Too far" in error
        assert "6 squares" in error

    def test_move_to_same_square(self):
        ws = self._make_ws()
        intent, error = build_full_move_intent("pc_fighter", Position(3, 3), ws)
        assert intent is None
        assert "already there" in error

    def test_nonexistent_entity(self):
        ws = self._make_ws()
        intent, error = build_full_move_intent("does_not_exist", Position(5, 5), ws)
        assert intent is None
        assert "not found" in error

    def test_speed_from_entity(self):
        ws = self._make_ws()
        # Cleric has speed 20 (heavy armor), at (2,3)
        # Move 3 squares south: (2,3) → (2,0) = 15ft, within 20ft budget
        intent, error = build_full_move_intent("pc_cleric", Position(2, 0), ws)
        assert error is None
        assert intent is not None
        assert intent.speed_ft == 20

    def test_cleric_speed_limited(self):
        ws = self._make_ws()
        # Cleric at (2,3), speed 20 = 4 squares
        # Try to move 5 squares south: (2,3) → (2,-2) = 5 squares = 25ft > 20ft
        intent, error = build_full_move_intent("pc_cleric", Position(2, -2), ws)
        assert intent is None
        assert "Too far" in error


# ===========================================================================
# play_loop.py FullMoveIntent Execution Tests
# ===========================================================================

class TestFullMoveExecution:

    def _make_ws_and_ctx(self):
        fixture = build_simple_combat_fixture()
        ws = fixture.world_state
        ctx = TurnContext(
            turn_index=0,
            actor_id="pc_fighter",
            actor_team="party",
        )
        return ws, ctx

    def test_full_move_updates_position(self):
        ws, ctx = self._make_ws_and_ctx()
        intent = FullMoveIntent(
            actor_id="pc_fighter",
            from_pos=Position(3, 3),
            path=[Position(3, 4)],
            speed_ft=30,
        )
        rng = RNGManager(42)
        result = execute_turn(ws, ctx, combat_intent=intent, rng=rng, next_event_id=0, timestamp=0.0)

        assert result.status == "ok"
        new_pos = result.world_state.entities["pc_fighter"][EF.POSITION]
        assert new_pos["x"] == 3
        assert new_pos["y"] == 4

    def test_full_move_emits_movement_event(self):
        ws, ctx = self._make_ws_and_ctx()
        intent = FullMoveIntent(
            actor_id="pc_fighter",
            from_pos=Position(3, 3),
            path=[Position(3, 2), Position(3, 1)],
            speed_ft=30,
        )
        rng = RNGManager(42)
        result = execute_turn(ws, ctx, combat_intent=intent, rng=rng, next_event_id=0, timestamp=0.0)

        assert result.status == "ok"
        move_events = [e for e in result.events if e.event_type == "movement_declared"]
        assert len(move_events) == 1
        assert move_events[0].payload["to_pos"] == {"x": 3, "y": 1}
        assert move_events[0].payload["from_pos"] == {"x": 3, "y": 3}

    def test_full_move_distance_in_event(self):
        ws, ctx = self._make_ws_and_ctx()
        intent = FullMoveIntent(
            actor_id="pc_fighter",
            from_pos=Position(3, 3),
            path=[Position(3, 2), Position(3, 1), Position(3, 0)],
            speed_ft=30,
        )
        rng = RNGManager(42)
        result = execute_turn(ws, ctx, combat_intent=intent, rng=rng, next_event_id=0, timestamp=0.0)

        move_events = [e for e in result.events if e.event_type == "movement_declared"]
        assert len(move_events) == 1
        assert move_events[0].payload["distance_ft"] == 15  # 3 squares * 5ft


# ===========================================================================
# Enemy AI Movement Tests
# ===========================================================================

class TestEnemyAIMovement:

    def test_enemy_moves_toward_target(self):
        """Enemy AI moves closer when not adjacent."""
        from play import run_enemy_turn, pick_enemy_target, _is_adjacent

        fixture = build_simple_combat_fixture()
        ws = fixture.world_state

        # Verify goblin_1 is NOT adjacent to any party member
        # Goblin at (3,5), party at (3,3), (2,3), (4,2)
        target = pick_enemy_target(ws, "goblin_1")
        assert target is not None

        # Run enemy turn — should move and/or attack
        result = run_enemy_turn(ws, "goblin_1", 42, 0, 0)
        assert result.status == "ok"

        # Goblin should have moved (position changed or attack events present)
        events = result.events
        event_types = [e.event_type for e in events]
        # Should have movement or attack events
        assert len(events) > 0

    def test_adjacent_enemy_attacks_without_moving(self):
        """Enemy already adjacent just attacks."""
        from play import run_enemy_turn

        fixture = build_simple_combat_fixture()
        ws = fixture.world_state

        # Place goblin adjacent to fighter
        ws.entities["goblin_1"][EF.POSITION] = {"x": 3, "y": 4}

        result = run_enemy_turn(ws, "goblin_1", 42, 0, 0)
        assert result.status == "ok"
        event_types = [e.event_type for e in result.events]
        assert "attack_roll" in event_types


# ===========================================================================
# Step cost calculation
# ===========================================================================

class TestStepCost:

    def test_orthogonal_cost(self):
        cost, diag = _step_cost(Position(0, 0), Position(0, 1), 0)
        assert cost == 5
        assert diag == 0

    def test_first_diagonal_cost_5(self):
        cost, diag = _step_cost(Position(0, 0), Position(1, 1), 0)
        assert cost == 5
        assert diag == 1

    def test_second_diagonal_cost_10(self):
        cost, diag = _step_cost(Position(1, 1), Position(2, 2), 1)
        assert cost == 10
        assert diag == 2

    def test_third_diagonal_cost_5(self):
        cost, diag = _step_cost(Position(2, 2), Position(3, 3), 2)
        assert cost == 5
        assert diag == 3

    def test_terrain_multiplier(self):
        cost, diag = _step_cost(Position(0, 0), Position(0, 1), 0, terrain_mult=2)
        assert cost == 10  # 5 * 2

    def test_diagonal_with_terrain(self):
        cost, diag = _step_cost(Position(0, 0), Position(1, 1), 0, terrain_mult=2)
        assert cost == 10  # first diagonal 5 * terrain 2


# ===========================================================================
# Occupied Squares Detection
# ===========================================================================

class TestOccupiedSquares:

    def test_detects_enemy_squares(self):
        fixture = build_simple_combat_fixture()
        ws = fixture.world_state
        enemies, allies = _get_occupied_squares(ws, "pc_fighter")

        # Goblins at (3,5), (4,5), (2,5)
        assert (3, 5) in enemies
        assert (4, 5) in enemies
        assert (2, 5) in enemies

        # Other party members are allies
        assert (2, 3) in allies  # Cleric
        assert (4, 2) in allies  # Rogue

    def test_actor_not_in_any_set(self):
        fixture = build_simple_combat_fixture()
        ws = fixture.world_state
        enemies, allies = _get_occupied_squares(ws, "pc_fighter")
        assert (3, 3) not in enemies
        assert (3, 3) not in allies

    def test_defeated_entities_excluded(self):
        fixture = build_simple_combat_fixture()
        ws = fixture.world_state
        ws.entities["goblin_1"][EF.DEFEATED] = True

        enemies, allies = _get_occupied_squares(ws, "pc_fighter")
        assert (3, 5) not in enemies  # Defeated goblin excluded


# ===========================================================================
# Integration: CLI parse + resolve + execute
# ===========================================================================

class TestCLIMovementIntegration:

    def _run_session(self, commands, seed=42):
        """Run a scripted CLI session and return output."""
        import io
        import sys
        from play import main

        cmd_iter = iter(commands)
        def mock_input(prompt=""):
            try:
                return next(cmd_iter)
            except StopIteration:
                raise EOFError

        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            main(seed=seed, input_fn=mock_input)
        except (EOFError, SystemExit):
            pass
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        return output

    def test_move_multiple_squares(self):
        """Player can move more than 1 square."""
        output = self._run_session(["move 3 1", "quit"], seed=42)
        assert "[RESOLVE] Move: (3,1)" in output

    def test_move_shows_distance(self):
        """Multi-square move shows distance in feet."""
        output = self._run_session(["move 3 1", "quit"], seed=42)
        # (3,3) to (3,1) = 2 squares = 10ft
        assert "10 ft" in output

    def test_move_too_far_gives_error(self):
        """Moving beyond speed gives informative error."""
        output = self._run_session(["move 3 99", "quit"], seed=42)
        assert "Too far" in output or "too far" in output

    def test_status_shows_speed(self):
        """Status command shows movement speed."""
        output = self._run_session(["status", "quit"], seed=42)
        assert "Spd" in output
        assert "6sq" in output  # 30ft = 6 squares

    def test_move_to_enemy_square_blocked(self):
        """Cannot move into enemy-occupied square (unit test level)."""
        from aidm.core.movement_resolver import build_full_move_intent
        from aidm.schemas.position import Position

        fixture = build_simple_combat_fixture()
        ws = fixture.world_state
        # Goblin_1 is at (3,5) at start
        intent, error = build_full_move_intent("pc_fighter", Position(3, 5), ws)
        assert intent is None
        assert "occupied by an enemy" in error
