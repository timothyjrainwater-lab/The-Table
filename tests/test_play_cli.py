"""Tests for play.py — the interactive combat CLI."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from aidm.runtime.play_controller import build_simple_combat_fixture
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import DeclaredAttackIntent, MoveIntent
from aidm.schemas.position import Position

from play import (
    parse_input,
    resolve_and_execute,
    pick_enemy_target,
    is_combat_over,
    format_events,
    run_enemy_turn,
    main,
)


# ---------------------------------------------------------------------------
# parse_input
# ---------------------------------------------------------------------------

class TestParseInput:
    def test_attack_basic(self):
        action, decl = parse_input("attack goblin warrior")
        assert action == "attack"
        assert isinstance(decl, DeclaredAttackIntent)
        assert decl.target_ref == "goblin warrior"

    def test_attack_with_weapon(self):
        action, decl = parse_input("strike the orc with greataxe")
        assert action == "attack"
        assert decl.target_ref == "orc"
        assert decl.weapon == "greataxe"

    def test_attack_strips_articles(self):
        action, decl = parse_input("hit the goblin")
        assert action == "attack"
        assert decl.target_ref == "goblin"

    def test_move(self):
        action, decl = parse_input("move 5 3")
        assert action == "move"
        assert isinstance(decl, MoveIntent)
        assert decl.destination == Position(x=5, y=3)

    def test_move_with_to(self):
        action, decl = parse_input("go to 10 7")
        assert action == "move"
        assert decl.destination == Position(x=10, y=7)

    def test_cast_basic(self):
        action, decl = parse_input("cast fireball")
        assert action == "cast"
        assert decl == ("fireball", None)

    def test_cast_on_target(self):
        action, decl = parse_input("cast magic missile on the goblin")
        assert action == "cast"
        assert decl == ("magic missile", "goblin")

    def test_cast_at_target(self):
        action, decl = parse_input("cast burning hands at orc")
        assert action == "cast"
        assert decl == ("burning hands", "orc")

    def test_end_turn(self):
        action, _ = parse_input("end turn")
        assert action == "end_turn"

    def test_pass(self):
        action, _ = parse_input("pass")
        assert action == "end_turn"

    def test_unknown(self):
        action, decl = parse_input("dance wildly")
        assert action is None
        assert decl is None

    def test_empty(self):
        action, decl = parse_input("")
        assert action is None
        assert decl is None


# ---------------------------------------------------------------------------
# is_combat_over
# ---------------------------------------------------------------------------

class TestCombatOver:
    def test_not_over(self):
        fixture = build_simple_combat_fixture()
        over, _ = is_combat_over(fixture.world_state)
        assert over is False

    def test_monsters_dead(self):
        fixture = build_simple_combat_fixture()
        fixture.world_state.entities["goblin_1"][EF.DEFEATED] = True
        over, reason = is_combat_over(fixture.world_state)
        assert over is True
        assert "Victory" in reason

    def test_party_dead(self):
        fixture = build_simple_combat_fixture()
        fixture.world_state.entities["pc_fighter"][EF.DEFEATED] = True
        over, reason = is_combat_over(fixture.world_state)
        assert over is True
        assert "fallen" in reason


# ---------------------------------------------------------------------------
# pick_enemy_target
# ---------------------------------------------------------------------------

class TestPickTarget:
    def test_picks_opposing_team(self):
        fixture = build_simple_combat_fixture()
        target = pick_enemy_target(fixture.world_state, "pc_fighter")
        assert target == "goblin_1"

    def test_picks_pc_for_monster(self):
        fixture = build_simple_combat_fixture()
        target = pick_enemy_target(fixture.world_state, "goblin_1")
        assert target == "pc_fighter"

    def test_no_target_if_all_defeated(self):
        fixture = build_simple_combat_fixture()
        fixture.world_state.entities["goblin_1"][EF.DEFEATED] = True
        target = pick_enemy_target(fixture.world_state, "pc_fighter")
        assert target is None


# ---------------------------------------------------------------------------
# resolve_and_execute
# ---------------------------------------------------------------------------

class TestResolveAndExecute:
    def test_attack_returns_new_state(self):
        fixture = build_simple_combat_fixture()
        ws = fixture.world_state
        declared = DeclaredAttackIntent(target_ref="goblin warrior")
        result = resolve_and_execute(ws, "pc_fighter", "attack", declared, 42, 0, 0)
        assert result.status == "ok"
        # State should be a different object (deep copied)
        assert result.world_state is not ws

    def test_attack_produces_events(self):
        fixture = build_simple_combat_fixture()
        declared = DeclaredAttackIntent(target_ref="goblin warrior")
        result = resolve_and_execute(fixture.world_state, "pc_fighter", "attack", declared, 42, 0, 0)
        event_types = [e.event_type for e in result.events]
        assert "attack_roll" in event_types


# ---------------------------------------------------------------------------
# run_enemy_turn
# ---------------------------------------------------------------------------

class TestEnemyTurn:
    def test_enemy_attacks(self):
        fixture = build_simple_combat_fixture()
        result = run_enemy_turn(fixture.world_state, "goblin_1", 42, 0, 0)
        assert result.status == "ok"
        event_types = [e.event_type for e in result.events]
        assert "attack_roll" in event_types


# ---------------------------------------------------------------------------
# format_events
# ---------------------------------------------------------------------------

class TestFormatEvents:
    def test_formats_attack_roll(self):
        fixture = build_simple_combat_fixture()
        declared = DeclaredAttackIntent(target_ref="goblin warrior")
        result = resolve_and_execute(fixture.world_state, "pc_fighter", "attack", declared, 42, 0, 0)
        output = format_events(result.events, fixture.world_state)
        assert "Roll:" in output
        assert "AC" in output


# ---------------------------------------------------------------------------
# Full game (scripted)
# ---------------------------------------------------------------------------

class TestFullGame:
    def test_combat_completes(self):
        """Feed enough attacks to ensure combat resolves."""
        actions = ["attack goblin warrior"] * 20
        action_iter = iter(actions)

        def mock_input(prompt=""):
            try:
                return next(action_iter)
            except StopIteration:
                return "quit"

        # Should complete without errors
        main(seed=100, input_fn=mock_input)

    def test_determinism(self):
        """Same seed + same actions = same outcome."""
        results = []
        for _ in range(2):
            actions = iter(["attack goblin warrior"] * 10)
            captured = []

            def mock_input(prompt="", _actions=actions):
                try:
                    return next(_actions)
                except StopIteration:
                    return "quit"

            # Capture print output
            import io
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                main(seed=42, input_fn=mock_input)
            finally:
                sys.stdout = old_stdout
            results.append(buf.getvalue())

        assert results[0] == results[1]
