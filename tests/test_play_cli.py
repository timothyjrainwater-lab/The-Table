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

    def test_help(self):
        action, _ = parse_input("help")
        assert action == "help"

    def test_help_question_mark(self):
        action, _ = parse_input("?")
        assert action == "help"

    def test_status(self):
        action, _ = parse_input("status")
        assert action == "status"

    def test_look(self):
        action, _ = parse_input("look")
        assert action == "status"

    def test_cast_no_spell(self):
        action, _ = parse_input("cast")
        assert action == "cast_no_spell"

    def test_cast_on_self(self):
        action, decl = parse_input("cast shield on self")
        assert action == "cast"
        assert decl == ("shield", "__SELF__")

    def test_cast_on_me(self):
        action, decl = parse_input("cast mage armor on me")
        assert action == "cast"
        assert decl == ("mage armor", "__SELF__")

    def test_cast_on_myself(self):
        action, decl = parse_input("cast bull's strength on myself")
        assert action == "cast"
        assert decl == ("bull's strength", "__SELF__")


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
        for eid in ("goblin_1", "goblin_2", "goblin_3"):
            fixture.world_state.entities[eid][EF.DEFEATED] = True
        over, reason = is_combat_over(fixture.world_state)
        assert over is True
        assert "Victory" in reason

    def test_party_dead(self):
        fixture = build_simple_combat_fixture()
        for eid in ("pc_fighter", "pc_cleric", "pc_rogue"):
            fixture.world_state.entities[eid][EF.DEFEATED] = True
        over, reason = is_combat_over(fixture.world_state)
        assert over is True
        assert "fallen" in reason

    def test_partial_monsters_dead_not_over(self):
        fixture = build_simple_combat_fixture()
        fixture.world_state.entities["goblin_1"][EF.DEFEATED] = True
        over, _ = is_combat_over(fixture.world_state)
        assert over is False

    def test_partial_party_dead_not_over(self):
        fixture = build_simple_combat_fixture()
        fixture.world_state.entities["pc_fighter"][EF.DEFEATED] = True
        over, _ = is_combat_over(fixture.world_state)
        assert over is False


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
        # sorted entity IDs: pc_cleric < pc_fighter < pc_rogue
        assert target == "pc_cleric"

    def test_no_target_if_all_defeated(self):
        fixture = build_simple_combat_fixture()
        for eid in ("goblin_1", "goblin_2", "goblin_3"):
            fixture.world_state.entities[eid][EF.DEFEATED] = True
        target = pick_enemy_target(fixture.world_state, "pc_fighter")
        assert target is None

    def test_skips_defeated_targets(self):
        fixture = build_simple_combat_fixture()
        fixture.world_state.entities["goblin_1"][EF.DEFEATED] = True
        target = pick_enemy_target(fixture.world_state, "pc_fighter")
        assert target == "goblin_2"


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

    def test_formats_spell_cast(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={
            "wizard_1": {"name": "Gandalf"},
            "goblin_1": {"name": "Goblin"},
        })
        events = [Event(
            event_id=0, event_type="spell_cast", timestamp=0.0,
            payload={
                "cast_id": "c1", "caster_id": "wizard_1", "spell_id": "SPELL_001",
                "spell_name": "Magic Missile", "spell_level": 1,
                "affected_entities": ["goblin_1"], "turn_index": 0,
            },
        )]
        output = format_events(events, ws)
        assert "Gandalf casts Magic Missile on Goblin!" in output

    def test_formats_spell_cast_failed(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={})
        events = [Event(
            event_id=0, event_type="spell_cast_failed", timestamp=0.0,
            payload={
                "caster_id": "wizard_1", "spell_id": "SPELL_001",
                "spell_name": "Fireball", "reason": "No valid targets in range",
                "turn_index": 0,
            },
        )]
        output = format_events(events, ws)
        assert "Spell failed" in output
        assert "Fireball" in output
        assert "No valid targets in range" in output

    def test_formats_spell_hp_changed_with_old_hp_convention(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={"goblin_1": {"name": "Goblin"}})
        events = [Event(
            event_id=0, event_type="hp_changed", timestamp=0.0,
            payload={
                "entity_id": "goblin_1", "old_hp": 10, "new_hp": 3,
                "delta": -7, "source": "spell:Magic Missile",
            },
        )]
        output = format_events(events, ws)
        assert "Goblin" in output
        assert "7 damage" in output
        assert "Magic Missile" in output
        assert "10" in output
        assert "3" in output

    def test_formats_hp_changed_with_hp_before_convention(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={"goblin_1": {"name": "Goblin"}})
        events = [Event(
            event_id=0, event_type="hp_changed", timestamp=0.0,
            payload={
                "entity_id": "goblin_1", "hp_before": 20, "hp_after": 12,
                "delta": -8, "source": "full_attack_damage",
            },
        )]
        output = format_events(events, ws)
        assert "Goblin" in output
        assert "20" in output
        assert "12" in output

    def test_formats_condition_applied(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={"goblin_1": {"name": "Goblin"}})
        events = [Event(
            event_id=0, event_type="condition_applied", timestamp=0.0,
            payload={
                "entity_id": "goblin_1", "condition": "dazed",
                "source": "spell:Color Spray", "duration_rounds": 3,
            },
        )]
        output = format_events(events, ws)
        assert "Goblin gains Dazed effect (3 rounds)" in output

    def test_formats_condition_applied_no_duration(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={"goblin_1": {"name": "Goblin"}})
        events = [Event(
            event_id=0, event_type="condition_applied", timestamp=0.0,
            payload={
                "entity_id": "goblin_1", "condition": "prone",
                "source": "spell:Grease",
            },
        )]
        output = format_events(events, ws)
        assert "Goblin gains Prone effect" in output
        assert "rounds" not in output

    def test_formats_healing(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={"pc_1": {"name": "Fighter"}})
        events = [Event(
            event_id=0, event_type="hp_changed", timestamp=0.0,
            payload={
                "entity_id": "pc_1", "old_hp": 5, "new_hp": 13,
                "delta": 8, "source": "spell:Cure Light Wounds",
            },
        )]
        output = format_events(events, ws)
        assert "healed 8 HP" in output
        assert "Cure Light Wounds" in output

    def test_no_visible_effect_only_for_truly_empty(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={})
        output = format_events([], ws)
        assert "no visible effect" in output

    def test_formats_movement_declared(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={"pc_1": {"name": "Aldric"}})
        events = [Event(
            event_id=0, event_type="movement_declared", timestamp=0.0,
            payload={
                "actor_id": "pc_1",
                "from_pos": {"x": 3, "y": 3},
                "to_pos": {"x": 4, "y": 3},
            },
        )]
        output = format_events(events, ws)
        assert "Aldric moves to (4, 3)" in output


# ---------------------------------------------------------------------------
# Full game (scripted)
# ---------------------------------------------------------------------------

class TestFullGame:
    def test_combat_completes(self):
        """Feed enough attacks to ensure combat resolves (3v3)."""
        # Use specific goblin name to avoid ambiguity. 60 commands for 3 PCs.
        actions = ["attack goblin warrior"] * 60
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
            actions = iter(["attack goblin warrior"] * 60)

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


# ---------------------------------------------------------------------------
# CLI smoke test — every command type produces non-empty, non-crash output
# ---------------------------------------------------------------------------

class TestCLISmoke:
    """Verify every player command produces visible, non-crash output."""

    def _run_session(self, commands, seed=42):
        """Run a CLI session with given commands, return captured stdout."""
        import io
        action_iter = iter(commands)

        def mock_input(prompt=""):
            try:
                return next(action_iter)
            except StopIteration:
                return "quit"

        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            main(seed=seed, input_fn=mock_input)
        finally:
            sys.stdout = old_stdout
        return buf.getvalue()

    def test_help_produces_output(self):
        output = self._run_session(["help", "quit"])
        assert "Commands:" in output
        assert "attack" in output
        assert "cast" in output

    def test_status_produces_output(self):
        output = self._run_session(["status", "quit"])
        assert "HP" in output

    def test_cast_no_spell_produces_guidance(self):
        output = self._run_session(["cast", "quit"])
        assert "Cast what?" in output

    def test_unknown_command_shows_help(self):
        output = self._run_session(["dance wildly", "quit"])
        assert "Unknown command" in output
        assert "Commands:" in output

    def test_end_turn_produces_feedback(self):
        output = self._run_session(["end turn", "quit"])
        assert "ends their turn" in output

    def test_attack_hit_shows_roll_and_damage(self):
        # With 3v3, must use a specific goblin name to avoid ambiguity
        output = self._run_session(["attack goblin warrior"] * 30, seed=100)
        assert "Roll:" in output
        assert "HIT" in output or "MISS" in output

    def test_move_too_far_gives_guidance(self):
        output = self._run_session(["move 99 99", "quit"])
        assert "adjacent" in output or "too far" in output

    def test_valid_move_shows_destination(self):
        output = self._run_session(["move 4 3", "quit"], seed=42)
        assert "moves to" in output

    def test_move_updates_position(self):
        """After moving, status should show the new position."""
        output = self._run_session(["move 4 3", "status", "quit"], seed=42)
        # Aldric starts at (3,3), moves to (4,3) — status should reflect new pos
        assert "(4,3)" in output.replace(" ", "") or "(4, 3)" in output

    def test_spell_cast_shows_spell_feedback(self):
        output = self._run_session(["cast magic missile on goblin warrior", "quit"], seed=42)
        assert "casts Magic Missile" in output

    def test_cast_then_enemy_attack_no_crash(self):
        """Casting a condition spell must not crash when enemy attacks next."""
        # This reproduces a bug where spell conditions stored as list crashed
        # get_condition_modifiers which expects dict. The enemy turn calls
        # resolve_attack -> get_condition_modifiers on the target.
        output = self._run_session(
            ["cast shield on goblin warrior", "attack goblin warrior"] * 15,
            seed=42
        )
        # Should not crash — any output means we survived the enemy turn
        assert "Roll:" in output or "DEFEATED" in output or "Victory" in output

    def test_no_action_produces_silent_failure(self):
        """Every recognized command must produce at least one line of output."""
        commands = [
            "help",
            "status",
            "cast",
            "dance wildly",
            "attack goblin warrior",
        ]
        output = self._run_session(commands, seed=42)
        # After the banner + initial status, every command should add content
        lines = [l for l in output.split("\n") if l.strip()]
        # At minimum: banner (3 lines) + status (2) + prompt hint (1) + turn header + status
        # + 5 command responses = lots of lines. Just verify it's substantial.
        assert len(lines) > 15


# ---------------------------------------------------------------------------
# Golden transcript — deterministic session replay
# ---------------------------------------------------------------------------

class TestGoldenTranscript:
    """Record and verify a canonical session transcript for regression detection."""

    def test_seed_42_attack_sequence(self):
        """Canonical attack session with seed 42 (3v3). If this changes, something regressed."""
        import io
        # Use specific goblin names to avoid ambiguity; 60 commands for 3 PCs
        commands = iter(["attack goblin warrior"] * 60)

        def mock_input(prompt=""):
            try:
                return next(commands)
            except StopIteration:
                return "quit"

        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            main(seed=42, input_fn=mock_input)
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()

        # Structural assertions — these must always hold for seed 42, 3v3
        assert "D&D 3.5e Combat -- AIDM Engine" in output
        assert "Aldric" in output
        assert "Elara" in output
        assert "Snitch" in output
        assert "Goblin Warrior" in output
        assert "Roll:" in output
        assert "vs AC" in output
        # The game must end (either victory or enough attacks to resolve)
        assert "Victory!" in output or "Farewell!" in output or "DEFEATED" in output

    def test_seed_42_transcript_is_stable(self):
        """Same inputs + same seed = byte-identical output."""
        import io
        outputs = []
        for _ in range(2):
            commands = iter(["attack goblin warrior"] * 60)

            def mock_input(prompt="", _cmds=commands):
                try:
                    return next(_cmds)
                except StopIteration:
                    return "quit"

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                main(seed=42, input_fn=mock_input)
            finally:
                sys.stdout = old_stdout
            outputs.append(buf.getvalue())

        assert outputs[0] == outputs[1], "Transcript not deterministic — output differs between runs"
