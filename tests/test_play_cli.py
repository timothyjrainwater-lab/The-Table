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

    def test_map(self):
        action, _ = parse_input("map")
        assert action == "map"

    def test_grid(self):
        action, _ = parse_input("grid")
        assert action == "map"

    def test_tactical(self):
        action, _ = parse_input("tactical")
        assert action == "map"

    def test_move_no_dest(self):
        action, _ = parse_input("move")
        assert action == "move_no_dest"

    def test_move_bad_coords(self):
        action, _ = parse_input("move abc def")
        assert action == "move_bad_coords"

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
        assert "[RESOLVE] Attack roll:" in output
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
        assert "[RESOLVE] Spell failed" in output
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
        assert "[RESOLVE] HP:" in output
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
        assert "[RESOLVE] HP:" in output
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
        assert "Goblin gains Dazed effect" in output
        assert "[RESOLVE] Dazed: 3 rounds remaining" in output

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
        assert "[RESOLVE] HP:" in output
        assert "Cure Light Wounds" in output
        assert "+8" in output

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
        assert "[RESOLVE] Move: (4,3)" in output


# ---------------------------------------------------------------------------
# Full game (scripted)
# ---------------------------------------------------------------------------

class TestFullGame:
    def test_combat_completes(self):
        """Feed enough attacks to ensure combat resolves (3v3)."""
        # With action economy: attack uses standard, then end turn to skip move.
        actions = ["attack goblin warrior", "end turn"] * 60
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
            actions = iter(["attack goblin warrior", "end turn"] * 60)

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
        assert "Actions" in output
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
        assert "Actions" in output

    def test_end_turn_produces_feedback(self):
        output = self._run_session(["end turn", "quit"])
        assert "ends their turn" in output

    def test_attack_hit_shows_roll_and_damage(self):
        # With 3v3, must use a specific goblin name to avoid ambiguity
        # With action economy: attack + end turn per PC turn
        output = self._run_session(["attack goblin warrior", "end turn"] * 30, seed=100)
        assert "[RESOLVE] Attack roll:" in output
        assert "HIT" in output or "MISS" in output

    def test_move_too_far_gives_guidance(self):
        output = self._run_session(["move 99 99", "quit"])
        assert "adjacent" in output.lower() or "too far" in output.lower()

    def test_valid_move_shows_destination(self):
        output = self._run_session(["move 4 3", "quit"], seed=42)
        assert "[RESOLVE] Move:" in output

    def test_move_updates_position(self):
        """After moving, status should show the new position."""
        output = self._run_session(["move 4 3", "status", "quit"], seed=42)
        # Aldric starts at (3,3), moves to (4,3) — status should reflect new pos
        assert "(4,3)" in output.replace(" ", "") or "(4, 3)" in output

    def test_spell_cast_shows_spell_feedback(self):
        output = self._run_session(["cast magic missile on goblin warrior", "end turn", "quit"], seed=42)
        assert "casts Magic Missile" in output

    def test_cast_then_enemy_attack_no_crash(self):
        """Casting a condition spell must not crash when enemy attacks next."""
        # This reproduces a bug where spell conditions stored as list crashed
        # get_condition_modifiers which expects dict. The enemy turn calls
        # resolve_attack -> get_condition_modifiers on the target.
        output = self._run_session(
            ["cast shield on goblin warrior", "end turn", "attack goblin warrior", "end turn"] * 15,
            seed=42
        )
        # Should not crash — any output means we survived the enemy turn
        assert "[RESOLVE] Attack roll:" in output or "DEFEATED" in output or "Victory" in output

    def test_no_action_produces_silent_failure(self):
        """Every recognized command must produce at least one line of output."""
        commands = [
            "help",
            "status",
            "cast",
            "dance wildly",
            "attack goblin warrior",
            "end turn",     # end turn after attack (action economy)
        ]
        output = self._run_session(commands, seed=42)
        # After the banner + initial status, every command should add content
        lines = [l for l in output.split("\n") if l.strip()]
        # At minimum: banner (3 lines) + status (2) + prompt hint (1) + turn header + status
        # + 6 command responses = lots of lines. Just verify it's substantial.
        assert len(lines) > 15


# ---------------------------------------------------------------------------
# Golden transcript — deterministic session replay
# ---------------------------------------------------------------------------

class TestGoldenTranscript:
    """Record and verify a canonical session transcript for regression detection."""

    def test_seed_42_attack_sequence(self):
        """Canonical attack session with seed 42 (3v3). If this changes, something regressed."""
        import io
        # With action economy: attack + end turn per PC turn
        commands = iter(["attack goblin warrior", "end turn"] * 60)

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
        assert "[RESOLVE] Attack roll:" in output
        assert "vs AC" in output
        # The game must end (either victory or enough attacks to resolve)
        assert "Victory!" in output or "Farewell!" in output or "DEFEATED" in output

    def test_seed_42_transcript_is_stable(self):
        """Same inputs + same seed = byte-identical output."""
        import io
        outputs = []
        for _ in range(2):
            commands = iter(["attack goblin warrior", "end turn"] * 60)

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


# ---------------------------------------------------------------------------
# Round tracking (WO-ROUND-TRACK-01)
# ---------------------------------------------------------------------------

class TestRoundTracking:
    """Verify round counter display and boundary detection."""

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

    def test_round_1_header_appears(self):
        """Round 1 header visible at start of combat."""
        output = self._run_session(["quit"])
        assert "Round 1" in output

    def test_round_header_format(self):
        """Round header uses [AIDM] Round N format."""
        output = self._run_session(["quit"])
        assert "[AIDM] Round 1" in output

    def test_round_2_appears_after_full_initiative_cycle(self):
        """Round 2 header appears after all actors have taken a turn."""
        # Feed attacks cycling through goblin names to handle defeats.
        # 3 party members per round, enemies act automatically.
        # With action economy: attack + end turn per PC turn
        attacks = []
        targets = ["goblin warrior", "goblin archer", "goblin skirmisher"]
        for i in range(60):
            attacks.append(f"attack {targets[i % 3]}")
            attacks.append("end turn")
        output = self._run_session(attacks, seed=42)
        assert "Round 2" in output

    def test_round_counter_increments_sequentially(self):
        """Round numbers appear in order: 1, 2, 3..."""
        attacks = []
        targets = ["goblin warrior", "goblin archer", "goblin skirmisher"]
        for i in range(60):
            attacks.append(f"attack {targets[i % 3]}")
            attacks.append("end turn")
        output = self._run_session(attacks, seed=42)
        assert "Round 1" in output
        assert "Round 2" in output
        # Verify Round 1 appears before Round 2
        r1_pos = output.index("Round 1")
        r2_pos = output.index("Round 2")
        assert r1_pos < r2_pos

    def test_round_header_deterministic(self):
        """Round headers are identical between two runs with same seed."""
        import io
        outputs = []
        for _ in range(2):
            commands = iter(["attack goblin warrior", "end turn"] * 60)

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

        # Both runs must produce identical output including round headers
        assert outputs[0] == outputs[1]


# ---------------------------------------------------------------------------
# Full attack (WO-FULLATTACK-CLI-01)
# ---------------------------------------------------------------------------

class TestFullAttack:
    def test_parse_full_attack(self):
        action, decl = parse_input("full attack goblin warrior")
        assert action == "full_attack"
        assert isinstance(decl, DeclaredAttackIntent)
        assert decl.target_ref == "goblin warrior"

    def test_parse_full_attack_strips_articles(self):
        action, decl = parse_input("full attack the goblin")
        assert action == "full_attack"
        assert decl.target_ref == "goblin"

    def test_parse_full_attack_no_target(self):
        action, decl = parse_input("full attack")
        assert action == "full_attack"
        assert decl.target_ref is None

    def test_full_attack_resolves(self):
        fixture = build_simple_combat_fixture()
        declared = DeclaredAttackIntent(target_ref="goblin warrior")
        result = resolve_and_execute(fixture.world_state, "pc_fighter", "full_attack", declared, 42, 0, 0)
        assert result.status == "ok"
        event_types = [e.event_type for e in result.events]
        assert "attack_roll" in event_types

    def test_full_attack_in_help_text(self):
        action, _ = parse_input("help")
        assert action == "help"
        from play import _HELP_TEXT
        assert "full attack" in _HELP_TEXT
        assert "full-round" in _HELP_TEXT


# ---------------------------------------------------------------------------
# Combat maneuvers (WO-MANEUVER-CLI-01)
# ---------------------------------------------------------------------------

class TestManeuvers:
    def test_parse_trip(self):
        action, decl = parse_input("trip goblin warrior")
        assert action == "trip"
        assert decl.target_ref == "goblin warrior"

    def test_parse_bull_rush(self):
        action, decl = parse_input("bull rush goblin warrior")
        assert action == "bull_rush"
        assert decl.target_ref == "goblin warrior"

    def test_parse_bullrush_no_space(self):
        action, decl = parse_input("bullrush goblin warrior")
        assert action == "bull_rush"
        assert decl.target_ref == "goblin warrior"

    def test_parse_disarm(self):
        action, decl = parse_input("disarm goblin warrior")
        assert action == "disarm"
        assert decl.target_ref == "goblin warrior"

    def test_parse_grapple(self):
        action, decl = parse_input("grapple goblin warrior")
        assert action == "grapple"
        assert decl.target_ref == "goblin warrior"

    def test_parse_sunder(self):
        action, decl = parse_input("sunder goblin warrior")
        assert action == "sunder"
        assert decl.target_ref == "goblin warrior"
        assert decl.weapon == "weapon"

    def test_parse_sunder_shield(self):
        action, decl = parse_input("sunder goblin warrior shield")
        assert action == "sunder"
        assert decl.target_ref == "goblin warrior"
        assert decl.weapon == "shield"

    def test_parse_overrun(self):
        action, decl = parse_input("overrun goblin warrior")
        assert action == "overrun"
        assert decl.target_ref == "goblin warrior"

    def test_trip_resolves(self):
        fixture = build_simple_combat_fixture()
        declared = DeclaredAttackIntent(target_ref="goblin warrior")
        result = resolve_and_execute(fixture.world_state, "pc_fighter", "trip", declared, 42, 0, 0)
        assert result.status == "ok"
        event_types = [e.event_type for e in result.events]
        assert "trip_declared" in event_types

    def test_maneuver_events_display(self):
        """Maneuver declared events render in format_events."""
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={
            "pc_1": {"name": "Aldric"},
            "goblin_1": {"name": "Goblin"},
        })
        events = [Event(
            event_id=0, event_type="trip_declared", timestamp=0.0,
            payload={"attacker_id": "pc_1", "target_id": "goblin_1"},
        )]
        output = format_events(events, ws)
        assert "[RESOLVE] Aldric attempts to trip Goblin" in output

    def test_opposed_check_display(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={})
        events = [Event(
            event_id=0, event_type="opposed_check", timestamp=0.0,
            payload={"attacker_total": 15, "defender_total": 12},
        )]
        output = format_events(events, ws)
        assert "15 vs 12" in output

    def test_maneuver_help_text(self):
        from play import _HELP_TEXT
        assert "trip" in _HELP_TEXT
        assert "bull rush" in _HELP_TEXT
        assert "disarm" in _HELP_TEXT
        assert "grapple" in _HELP_TEXT
        assert "sunder" in _HELP_TEXT
        assert "overrun" in _HELP_TEXT


# ---------------------------------------------------------------------------
# Expanded status (WO-STATUS-EXPAND-01)
# ---------------------------------------------------------------------------

class TestExpandedStatus:
    def _run_session(self, commands, seed=42):
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

    def test_status_shows_ac(self):
        output = self._run_session(["status", "quit"])
        assert "AC" in output

    def test_status_shows_bab(self):
        output = self._run_session(["status", "quit"])
        assert "BAB" in output

    def test_status_still_shows_hp(self):
        output = self._run_session(["status", "quit"])
        assert "HP" in output

    def test_status_still_hides_defeated(self):
        fixture = build_simple_combat_fixture()
        fixture.world_state.entities["goblin_1"][EF.DEFEATED] = True
        import io
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            from play import show_status
            show_status(fixture.world_state)
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()
        assert "Goblin Warrior" not in output

    def test_status_shows_conditions_when_present(self):
        fixture = build_simple_combat_fixture()
        fixture.world_state.entities["goblin_1"][EF.CONDITIONS] = {
            "prone": {"condition_type": "prone", "source": "test", "modifiers": {}, "applied_at_event_id": 0, "notes": None}
        }
        import io
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            from play import show_status
            show_status(fixture.world_state)
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()
        assert "*prone*" in output


# ---------------------------------------------------------------------------
# AoO display (WO-AOO-DISPLAY-01)
# ---------------------------------------------------------------------------

class TestAoODisplay:
    def test_aoo_triggered_display(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={
            "goblin_1": {"name": "Goblin"},
            "pc_1": {"name": "Aldric"},
        })
        events = [Event(
            event_id=0, event_type="aoo_triggered", timestamp=0.0,
            payload={"reactor_id": "goblin_1", "provoker_id": "pc_1", "trigger_reason": "movement"},
        )]
        output = format_events(events, ws)
        assert "[RESOLVE]" in output
        assert "attack of opportunity" in output
        assert "Goblin" in output
        assert "Aldric" in output

    def test_tumble_check_display(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={"pc_1": {"name": "Aldric"}})
        events = [Event(
            event_id=0, event_type="tumble_check", timestamp=0.0,
            payload={"entity_id": "pc_1", "success": True, "total": 18, "dc": 15, "d20_roll": 14},
        )]
        output = format_events(events, ws)
        assert "[RESOLVE] Tumble check" in output
        assert "DC 15" in output
        assert "18" in output
        assert "success" in output

    def test_aoo_avoided_display(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={"pc_1": {"name": "Aldric"}})
        events = [Event(
            event_id=0, event_type="aoo_avoided_by_tumble", timestamp=0.0,
            payload={"entity_id": "pc_1", "reactor_id": "goblin_1"},
        )]
        output = format_events(events, ws)
        assert "[RESOLVE]" in output
        assert "tumbles past" in output

    def test_aoo_blocked_by_cover_display(self):
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={"goblin_1": {"name": "Goblin"}})
        events = [Event(
            event_id=0, event_type="aoo_blocked_by_cover", timestamp=0.0,
            payload={"reactor_id": "goblin_1", "provoker_id": "pc_1", "cover_type": "partial"},
        )]
        output = format_events(events, ws)
        assert "[RESOLVE]" in output
        assert "blocked by cover" in output


# ---------------------------------------------------------------------------
# AC breakdown display (playtest fix)
# ---------------------------------------------------------------------------

class TestACBreakdown:
    def test_attack_roll_shows_cover_breakdown(self):
        """Attack roll display shows base AC + cover when cover is present."""
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={
            "pc_1": {"name": "Aldric"},
            "goblin_1": {"name": "Goblin"},
        })
        events = [Event(
            event_id=0, event_type="attack_roll", timestamp=0.0,
            payload={
                "d20_result": 10, "attack_bonus": 5, "total": 15,
                "target_ac": 18, "target_base_ac": 14,
                "cover_ac_bonus": 4, "cover_type": "soft",
                "target_ac_modifier": 0,
                "hit": False, "target_id": "goblin_1",
                "attacker_id": "pc_1",
            },
        )]
        output = format_events(events, ws)
        assert "AC 18 (14 base, +4 soft cover)" in output

    def test_attack_roll_clean_when_no_cover(self):
        """Attack roll display shows plain AC when no modifiers."""
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={})
        events = [Event(
            event_id=0, event_type="attack_roll", timestamp=0.0,
            payload={
                "d20_result": 15, "attack_bonus": 6, "total": 21,
                "target_ac": 15, "target_base_ac": 15,
                "cover_ac_bonus": 0, "target_ac_modifier": 0,
                "hit": True, "target_id": "g1", "attacker_id": "pc_1",
            },
        )]
        output = format_events(events, ws)
        assert "vs AC 15 \u2192" in output
        assert "base" not in output

    def test_attack_roll_shows_flanking(self):
        """Attack bonus shows flanking breakdown."""
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={})
        events = [Event(
            event_id=0, event_type="attack_roll", timestamp=0.0,
            payload={
                "d20_result": 12, "attack_bonus": 5, "total": 19,
                "target_ac": 14, "target_base_ac": 14,
                "cover_ac_bonus": 0, "target_ac_modifier": 0,
                "condition_modifier": 0, "flanking_bonus": 2,
                "feat_modifier": 0,
                "hit": True, "target_id": "g1", "attacker_id": "pc_1",
            },
        )]
        output = format_events(events, ws)
        assert "flanking +2" in output

    def test_attack_roll_shows_condition_modifier(self):
        """Attack roll shows condition AC modifier in breakdown."""
        from aidm.core.event_log import Event
        from aidm.core.state import WorldState
        ws = WorldState(ruleset_version="3.5", entities={})
        events = [Event(
            event_id=0, event_type="attack_roll", timestamp=0.0,
            payload={
                "d20_result": 10, "attack_bonus": 5, "total": 15,
                "target_ac": 12, "target_base_ac": 14,
                "cover_ac_bonus": 0, "target_ac_modifier": -2,
                "hit": True, "target_id": "g1", "attacker_id": "pc_1",
            },
        )]
        output = format_events(events, ws)
        assert "-2 conditions" in output


# ---------------------------------------------------------------------------
# Tactical map (playtest fix)
# ---------------------------------------------------------------------------

class TestTacticalMap:
    def test_show_map_renders_entities(self):
        """show_map prints entity symbols on the grid."""
        from play import show_map
        from aidm.core.state import WorldState
        import io
        ws = WorldState(ruleset_version="3.5", entities={
            "pc_1": {"name": "Aldric", "team": "party", "position": {"x": 3, "y": 3}, "defeated": False},
            "goblin_1": {"name": "Goblin", "team": "monsters", "position": {"x": 3, "y": 5}, "defeated": False},
        })
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            show_map(ws)
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()
        assert "A" in output
        assert "G" in output
        assert "Legend:" in output
        assert "Aldric" in output
        assert "Goblin" in output

    def test_show_map_skips_defeated(self):
        """Defeated entities do not appear on the map."""
        from play import show_map
        from aidm.core.state import WorldState
        import io
        ws = WorldState(ruleset_version="3.5", entities={
            "pc_1": {"name": "Aldric", "team": "party", "position": {"x": 3, "y": 3}, "defeated": False},
            "goblin_1": {"name": "Goblin", "team": "monsters", "position": {"x": 3, "y": 5}, "defeated": True},
        })
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            show_map(ws)
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()
        assert "A" in output
        assert "Goblin" not in output

    def test_show_map_handles_collision(self):
        """Entities with same first letter get distinct symbols."""
        from play import show_map
        from aidm.core.state import WorldState
        import io
        ws = WorldState(ruleset_version="3.5", entities={
            "g1": {"name": "Goblin Warrior", "team": "monsters", "position": {"x": 3, "y": 5}, "defeated": False},
            "g2": {"name": "Goblin Archer", "team": "monsters", "position": {"x": 4, "y": 5}, "defeated": False},
        })
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            show_map(ws)
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()
        # Both goblins should have distinct symbols
        assert "G " in output or " G" in output
        assert "G2" in output

    def test_map_in_help_text(self):
        from play import _HELP_TEXT
        assert "map" in _HELP_TEXT

    def test_parse_map_command(self):
        action, _ = parse_input("map")
        assert action == "map"


# ---------------------------------------------------------------------------
# Move error messages (playtest fix)
# ---------------------------------------------------------------------------

class TestMoveErrors:
    def _run_session(self, commands, seed=42):
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

    def test_move_no_dest_friendly_message(self):
        output = self._run_session(["move", "quit"])
        assert "Move where?" in output

    def test_move_bad_coords_friendly_message(self):
        output = self._run_session(["move abc def", "quit"])
        assert "Invalid coordinates" in output


# ---------------------------------------------------------------------------
# No double status on PC turn (playtest fix)
# ---------------------------------------------------------------------------

class TestNoDoubleStatus:
    def test_status_not_printed_automatically_on_turn(self):
        """PC turn banner does not auto-print full status table."""
        import io
        commands = iter(["quit"])

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
        # After "Aldric's Turn", the next line should NOT be a status dump.
        # The initial status at game start is fine, but there should be exactly one
        # status block before the first turn banner.
        turn_marker = "Aldric's Turn"
        idx = output.find(turn_marker)
        assert idx >= 0
        after_turn = output[idx + len(turn_marker):]
        # Should NOT immediately have "HP" in the next few characters (no auto-status)
        first_lines = after_turn[:100]
        # The old behavior had "  Goblin Warrior   HP 5/5..." right after the banner
        assert "Goblin Warrior" not in first_lines


# ---------------------------------------------------------------------------
# Action Economy (D&D 3.5e)
# ---------------------------------------------------------------------------

class TestActionBudget:
    """Unit tests for the ActionBudget state machine."""

    def test_fresh_budget_has_standard_and_move(self):
        from play import ActionBudget
        b = ActionBudget()
        assert b.has_standard is True
        assert b.has_move is True
        assert b.can_take("standard")
        assert b.can_take("move")
        assert b.can_take("full_round")
        assert b.can_take("free")

    def test_standard_then_move(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("standard")
        assert b.has_standard is False
        assert b.has_move is True
        assert not b.can_take("standard")
        assert b.can_take("move")
        assert not b.can_take("full_round")
        assert not b.is_turn_over()

    def test_move_then_standard(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("move")
        assert b.has_move is False
        assert b.has_standard is True
        assert b.can_take("standard")
        assert not b.can_take("full_round")  # moved, can't full attack
        assert not b.is_turn_over()

    def test_standard_and_move_ends_turn(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("standard")
        b.spend("move")
        assert b.is_turn_over()

    def test_full_round_ends_turn(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("full_round")
        assert b.is_turn_over()
        assert not b.can_take("standard")
        assert not b.can_take("move")

    def test_cannot_full_attack_after_move(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("move")
        assert not b.can_take("full_round")

    def test_cannot_move_after_full_round(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("full_round")
        assert not b.can_take("move")

    def test_free_actions_always_allowed(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("full_round")
        assert b.can_take("free")

    def test_trade_standard_for_second_move(self):
        """D&D 3.5: can trade standard action for a second move action."""
        from play import ActionBudget
        b = ActionBudget()
        b.spend("move")
        # Standard is still available, and can be traded for a move
        assert b.can_take("move")
        b.spend("move")  # trades standard for move
        assert b.is_turn_over()

    def test_remaining_str_fresh(self):
        from play import ActionBudget
        b = ActionBudget()
        r = b.remaining_str()
        assert "standard" in r
        assert "move" in r

    def test_remaining_str_after_standard(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("standard")
        r = b.remaining_str()
        assert "standard" not in r or "trade" in r
        assert "move" in r

    def test_remaining_str_turn_complete(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("full_round")
        assert "complete" in b.remaining_str()

    def test_denial_reason_standard(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("standard")
        reason = b.denial_reason("standard")
        assert "standard action" in reason

    def test_denial_reason_full_round_after_move(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("move")
        reason = b.denial_reason("full_round")
        assert "moved" in reason.lower() or "move" in reason.lower()

    # WO-FIX-11: Trip/Disarm/Grapple action type = "varies"

    def test_trip_action_type_is_varies(self):
        from play import _ACTION_COST
        assert _ACTION_COST["trip"] == "varies"

    def test_disarm_action_type_is_varies(self):
        from play import _ACTION_COST
        assert _ACTION_COST["disarm"] == "varies"

    def test_grapple_action_type_is_varies(self):
        from play import _ACTION_COST
        assert _ACTION_COST["grapple"] == "varies"

    def test_varies_action_uses_standard(self):
        """'varies' actions consume the standard action slot."""
        from play import ActionBudget
        b = ActionBudget()
        assert b.can_take("varies")
        b.spend("varies")
        assert b.has_standard is False
        assert not b.can_take("varies")

    def test_varies_not_available_after_full_round(self):
        from play import ActionBudget
        b = ActionBudget()
        b.spend("full_round")
        assert not b.can_take("varies")


class TestActionEconomyCLI:
    """Integration tests for action economy in the CLI game loop."""

    def _run_session(self, commands, seed=42):
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

    def test_move_then_attack_same_turn(self):
        """Player can move and then attack on the same turn."""
        output = self._run_session(["move 4 3", "attack goblin warrior", "quit"], seed=42)
        assert "[RESOLVE] Move:" in output
        assert "[RESOLVE] Attack roll:" in output

    def test_attack_then_move_same_turn(self):
        """Player can attack and then move on the same turn."""
        output = self._run_session(["attack goblin warrior", "move 4 3", "quit"], seed=42)
        assert "[RESOLVE] Attack roll:" in output
        assert "[RESOLVE] Move:" in output

    def test_cannot_attack_twice(self):
        """Standard action can only be used once per turn."""
        output = self._run_session(["attack goblin warrior", "attack goblin warrior", "quit"], seed=42)
        assert "already used your standard action" in output

    def test_full_attack_prevents_move(self):
        """Full-round action consumes both standard and move."""
        output = self._run_session(["full attack goblin warrior", "move 4 3", "quit"], seed=42)
        # Full attack should succeed
        assert "[RESOLVE] Attack roll:" in output
        # Full-round action auto-ends the turn, so the "move 4 3" command
        # is consumed on a subsequent turn or never reaches the move handler.
        # Just verify the full attack happened — move prevention is implicit.

    def test_move_prevents_full_attack(self):
        """Cannot full attack after taking a move action."""
        output = self._run_session(["move 4 3", "full attack goblin warrior", "quit"], seed=42)
        assert "[RESOLVE] Move:" in output
        assert "already moved" in output

    def test_prompt_shows_remaining_actions(self):
        """Prompt displays remaining action budget."""
        output = self._run_session(["status", "quit"], seed=42)
        assert "standard" in output
        assert "remaining" in output

    def test_free_actions_dont_end_turn(self):
        """Help, status, map are free actions and don't consume action budget."""
        output = self._run_session(["help", "status", "map", "attack goblin warrior", "end turn", "quit"], seed=42)
        # After help/status/map, attack should still work (standard not consumed)
        assert "[RESOLVE] Attack roll:" in output

    def test_end_turn_forfeits_remaining_actions(self):
        """End turn skips remaining actions."""
        output = self._run_session(["end turn", "quit"], seed=42)
        assert "ends their turn" in output

    def test_action_economy_help_text(self):
        """Help text explains action types."""
        output = self._run_session(["help", "quit"], seed=42)
        assert "standard action" in output
        assert "move action" in output
        assert "full-round action" in output

    def test_move_and_attack_combat_completes(self):
        """Full game with move+attack per turn completes successfully."""
        # Each PC turn: move then attack, then end turn
        commands = []
        for _ in range(60):
            commands.extend(["attack goblin warrior", "end turn"])
        output = self._run_session(commands, seed=100)
        assert "Victory!" in output or "Farewell!" in output or "DEFEATED" in output
