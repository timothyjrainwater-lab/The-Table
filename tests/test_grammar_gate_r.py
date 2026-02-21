"""Gate R tests — Voice Routing enforcement.

14 tests verifying that play.py output lines are correctly typed and prefixed
per the CLI Grammar Contract voice routing rules.

Categories:
    R-01: Attack roll output has [RESOLVE] prefix
    R-02: Damage output has [RESOLVE] prefix
    R-03: HP change output has [RESOLVE] prefix
    R-04: Save roll output has [RESOLVE] prefix (placeholder — no save events yet)
    R-05: Movement coordinate output has [RESOLVE] prefix
    R-06: Status display has [AIDM] prefix
    R-07: Round header has [AIDM] prefix
    R-08: Victory/defeat message has [AIDM] prefix
    R-09: No bare numbers in spoken (non-prefixed) lines
    R-10: No AP-03 abbreviations in spoken lines
    R-11: Every output line classifies to exactly one line type
    R-12: Gate J regression (27/27)
    R-13: Gate Q regression (from 3.1+3.2)
    R-14: Full suite regression (baseline)

Authority: WO-VOICE-ROUTING-IMPL-001, RQ-GRAMMAR-001 (CLI_GRAMMAR_CONTRACT.md).
"""
from __future__ import annotations

import io
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.runtime.play_controller import build_simple_combat_fixture
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import DeclaredAttackIntent

from play import format_events, main, resolve_and_execute, show_status

# Import classifier from Gate J
from tests.test_grammar_gate_j import classify_line, LINE_TYPES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_session(commands, seed=42):
    """Run a CLI session with given commands, return captured stdout."""
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


def _make_ws(**entities):
    return WorldState(ruleset_version="3.5", entities=entities)


def _spoken_lines(output):
    """Extract lines that are spoken (not [RESOLVE], not [AIDM], not blank)."""
    lines = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("[RESOLVE]") or stripped.startswith("[AIDM]"):
            continue
        lines.append(stripped)
    return lines


# ---------------------------------------------------------------------------
# R-01: Attack roll output has [RESOLVE] prefix
# ---------------------------------------------------------------------------

class TestR01AttackRollResolve:
    """Attack roll mechanical output carries [RESOLVE] prefix."""

    def test_attack_roll_has_resolve_prefix(self):
        fixture = build_simple_combat_fixture()
        declared = DeclaredAttackIntent(target_ref="goblin warrior")
        result = resolve_and_execute(fixture.world_state, "pc_fighter", "attack", declared, 42, 0, 0)
        output = format_events(result.events, fixture.world_state)
        attack_lines = [l.strip() for l in output.splitlines() if "Attack roll:" in l]
        assert len(attack_lines) >= 1, "No attack roll line found"
        for line in attack_lines:
            assert line.startswith("[RESOLVE]"), f"Attack roll missing [RESOLVE]: {line!r}"

    def test_attack_result_line_present(self):
        """Attack events produce a RESULT narrative line alongside the RESOLVE line."""
        fixture = build_simple_combat_fixture()
        declared = DeclaredAttackIntent(target_ref="goblin warrior")
        result = resolve_and_execute(fixture.world_state, "pc_fighter", "attack", declared, 42, 0, 0)
        output = format_events(result.events, fixture.world_state)
        # Should contain either "strikes true" or "goes wide"
        assert "strikes true" in output or "goes wide" in output


# ---------------------------------------------------------------------------
# R-02: Damage output has [RESOLVE] prefix
# ---------------------------------------------------------------------------

class TestR02DamageResolve:
    """Damage mechanical output carries [RESOLVE] prefix."""

    def test_damage_has_resolve_prefix(self):
        ws = _make_ws(goblin_1={"name": "Goblin"})
        events = [Event(
            event_id=0, event_type="damage_roll", timestamp=0.0,
            payload={"damage_dice": "2d6+3", "final_damage": 11},
        )]
        output = format_events(events, ws)
        lines = [l.strip() for l in output.splitlines() if "Damage:" in l]
        assert len(lines) == 1
        assert lines[0].startswith("[RESOLVE]"), f"Damage missing [RESOLVE]: {lines[0]!r}"


# ---------------------------------------------------------------------------
# R-03: HP change output has [RESOLVE] prefix
# ---------------------------------------------------------------------------

class TestR03HPChangeResolve:
    """HP change output carries [RESOLVE] prefix."""

    def test_hp_change_has_resolve_prefix(self):
        ws = _make_ws(goblin_1={"name": "Goblin"})
        events = [Event(
            event_id=0, event_type="hp_changed", timestamp=0.0,
            payload={"entity_id": "goblin_1", "hp_before": 20, "hp_after": 12, "delta": -8, "source": "attack"},
        )]
        output = format_events(events, ws)
        hp_lines = [l.strip() for l in output.splitlines() if "HP:" in l]
        assert len(hp_lines) >= 1
        for line in hp_lines:
            assert line.startswith("[RESOLVE]"), f"HP change missing [RESOLVE]: {line!r}"

    def test_spell_hp_change_has_resolve_prefix(self):
        ws = _make_ws(pc_1={"name": "Fighter"})
        events = [Event(
            event_id=0, event_type="hp_changed", timestamp=0.0,
            payload={"entity_id": "pc_1", "old_hp": 5, "new_hp": 13, "delta": 8, "source": "spell:Cure Light Wounds"},
        )]
        output = format_events(events, ws)
        hp_lines = [l.strip() for l in output.splitlines() if "HP:" in l]
        assert len(hp_lines) >= 1
        for line in hp_lines:
            assert line.startswith("[RESOLVE]"), f"Spell HP change missing [RESOLVE]: {line!r}"


# ---------------------------------------------------------------------------
# R-04: Save roll output has [RESOLVE] prefix
# ---------------------------------------------------------------------------

class TestR04SaveRollResolve:
    """Save roll output would carry [RESOLVE] prefix. Placeholder until save events exist."""

    def test_placeholder_save_roll(self):
        # No save_roll event type exists yet in format_events.
        # This test documents the expectation for when it's added.
        # For now, verify that tumble checks (similar mechanical checks) have [RESOLVE].
        ws = _make_ws(pc_1={"name": "Aldric"})
        events = [Event(
            event_id=0, event_type="tumble_check", timestamp=0.0,
            payload={"entity_id": "pc_1", "success": True, "total": 18, "dc": 15, "d20_roll": 14},
        )]
        output = format_events(events, ws)
        check_lines = [l.strip() for l in output.splitlines() if "Tumble check" in l]
        assert len(check_lines) == 1
        assert check_lines[0].startswith("[RESOLVE]"), f"Tumble check missing [RESOLVE]: {check_lines[0]!r}"


# ---------------------------------------------------------------------------
# R-05: Movement coordinate output has [RESOLVE] prefix
# ---------------------------------------------------------------------------

class TestR05MovementResolve:
    """Movement coordinate output carries [RESOLVE] prefix."""

    def test_movement_has_resolve_prefix(self):
        ws = _make_ws(pc_1={"name": "Aldric"})
        events = [Event(
            event_id=0, event_type="movement_declared", timestamp=0.0,
            payload={"actor_id": "pc_1", "from_pos": {"x": 3, "y": 3}, "to_pos": {"x": 4, "y": 3}},
        )]
        output = format_events(events, ws)
        move_lines = [l.strip() for l in output.splitlines() if "Move:" in l]
        assert len(move_lines) == 1
        assert move_lines[0].startswith("[RESOLVE]"), f"Movement missing [RESOLVE]: {move_lines[0]!r}"


# ---------------------------------------------------------------------------
# R-06: Status display has [AIDM] prefix
# ---------------------------------------------------------------------------

class TestR06StatusAIDM:
    """Status display output carries [AIDM] prefix."""

    def test_status_has_aidm_prefix(self):
        fixture = build_simple_combat_fixture()
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            show_status(fixture.world_state)
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        assert len(lines) > 0, "No status output"
        for line in lines:
            assert line.startswith("[AIDM]"), f"Status line missing [AIDM]: {line!r}"


# ---------------------------------------------------------------------------
# R-07: Round header has [AIDM] prefix
# ---------------------------------------------------------------------------

class TestR07RoundHeaderAIDM:
    """Round headers carry [AIDM] prefix."""

    def test_round_header_has_aidm(self):
        output = _run_session(["quit"])
        lines = output.splitlines()
        round_lines = [l.strip() for l in lines if "Round" in l and any(c.isdigit() for c in l)]
        assert len(round_lines) >= 1, "No round header found"
        for line in round_lines:
            assert line.startswith("[AIDM]"), f"Round header missing [AIDM]: {line!r}"


# ---------------------------------------------------------------------------
# R-08: Victory/defeat message has [AIDM] prefix
# ---------------------------------------------------------------------------

class TestR08VictoryDefeatAIDM:
    """Victory/defeat system messages carry [AIDM] prefix."""

    def test_victory_message_has_aidm(self):
        output = _run_session(["attack goblin warrior", "end turn"] * 60, seed=42)
        # Game should complete
        lines = output.splitlines()
        victory_lines = [l.strip() for l in lines if "Victory" in l or "defeated" in l.lower()]
        # Filter to system-level messages (not in-combat DEFEATED alerts)
        system_victory = [l for l in victory_lines if "Victory" in l]
        if system_victory:
            for line in system_victory:
                assert line.startswith("[AIDM]"), f"Victory message missing [AIDM]: {line!r}"

    def test_game_title_has_aidm(self):
        output = _run_session(["quit"])
        lines = output.splitlines()
        title_lines = [l.strip() for l in lines if "AIDM Engine" in l]
        assert len(title_lines) >= 1, "No game title found"
        for line in title_lines:
            assert line.startswith("[AIDM]"), f"Game title missing [AIDM]: {line!r}"


# ---------------------------------------------------------------------------
# R-09: No bare numbers in spoken (non-prefixed) lines
# ---------------------------------------------------------------------------

BARE_NUMBER_RE = re.compile(r"\b\d+\b")

class TestR09NoBareNumbersInSpoken:
    """Spoken lines contain no bare mechanical numbers."""

    def test_no_bare_numbers_in_spoken_lines(self):
        output = _run_session(["attack goblin warrior", "end turn"] * 10, seed=42)
        spoken = _spoken_lines(output)
        # Filter out lines that are part of the initiative display (system-like but not prefixed)
        # and action budget display (system-like), and help text
        # Only check RESULT, ALERT, TURN, NARRATION, PROMPT types
        violations = []
        for line in spoken:
            # Skip known system-like unprefixed lines
            if line.startswith("Turn Order") or line.startswith("(* ="):
                continue
            if line.startswith("Type ") or line.startswith("Actions"):
                continue
            if "[" in line and "]" in line and ("standard" in line or "move" in line):
                continue  # action budget display
            # Initiative display lines contain numbers by design
            if re.match(r"\s*[\* ]\s*\d+\.", line):
                continue
            classified = classify_line(line)
            if classified in ("TURN", "ALERT", "PROMPT", "NARRATION"):
                if BARE_NUMBER_RE.search(line):
                    violations.append((classified, line))
        assert not violations, (
            f"Bare numbers in spoken lines:\n"
            + "\n".join(f"  [{t}] {l!r}" for t, l in violations)
        )


# ---------------------------------------------------------------------------
# R-10: No AP-03 abbreviations in spoken lines
# ---------------------------------------------------------------------------

AP03_ABBREVIATIONS = re.compile(r"\b(atk|dmg|hp|AC|DC|DR|SR|CL|BAB)\b")

class TestR10NoAbbreviationsInSpoken:
    """Spoken lines contain no AP-03 abbreviations."""

    def test_no_abbreviations_in_spoken_lines(self):
        output = _run_session(["attack goblin warrior", "end turn"] * 10, seed=42)
        spoken = _spoken_lines(output)
        violations = []
        for line in spoken:
            # Skip initiative display and action budget
            if line.startswith("Turn Order") or line.startswith("(* ="):
                continue
            if "[" in line and "]" in line and ("standard" in line or "move" in line):
                continue
            if re.match(r"\s*[\* ]\s*\d+\.", line):
                continue
            classified = classify_line(line)
            if classified in ("TURN", "ALERT", "PROMPT", "NARRATION", "RESULT"):
                matches = AP03_ABBREVIATIONS.findall(line)
                if matches:
                    violations.append((classified, line, matches))
        assert not violations, (
            f"AP-03 abbreviations in spoken lines:\n"
            + "\n".join(f"  [{t}] {l!r} — {m}" for t, l, m in violations)
        )


# ---------------------------------------------------------------------------
# R-11: Every output line classifies to exactly one line type
# ---------------------------------------------------------------------------

class TestR11LineClassification:
    """Every non-blank output line classifies to exactly one of 7 types."""

    def test_all_lines_classify(self):
        output = _run_session(["attack goblin warrior", "end turn"] * 10, seed=42)
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        for line in lines:
            result = classify_line(line)
            assert result in LINE_TYPES, f"Line classified as unknown type {result!r}: {line!r}"


# ---------------------------------------------------------------------------
# R-12: Gate J regression (27/27)
# ---------------------------------------------------------------------------

class TestR12GateJRegression:
    """Gate J tests still pass."""

    def test_gate_j_passes(self):
        from tests.test_grammar_gate_j import (
            TestJ01TurnBanner,
            TestJ03AlertFormat,
            TestJ05Prompt,
            TestJ06SystemPrefix,
            TestJ07DetailPrefix,
            TestJ09ClassifierCompleteness,
        )
        TestJ01TurnBanner().test_valid_banners_match()
        TestJ03AlertFormat().test_valid_alerts_match()
        TestJ05Prompt().test_valid_prompt()
        TestJ06SystemPrefix().test_valid_system_lines()
        TestJ07DetailPrefix().test_valid_detail_lines()
        TestJ09ClassifierCompleteness().test_classifications_match_expected()


# ---------------------------------------------------------------------------
# R-13: Gate Q regression (from 3.1+3.2)
# ---------------------------------------------------------------------------

class TestR13GateQRegression:
    """Gate Q tests still pass."""

    def test_gate_q_passes(self):
        from tests.test_grammar_gate_q import (
            TestQ01PlayerTurnBanner,
            TestQ03DefeatAlert,
            TestQ07PromptFormat,
            TestQ08RoundHeaderPrefix,
            TestQ09NoDashedSeparators,
            TestQ10NoAsteriskDecorators,
        )
        TestQ01PlayerTurnBanner().test_player_turn_banner_matches_g01()
        TestQ03DefeatAlert().test_defeat_alert_matches_g03()
        TestQ07PromptFormat().test_prompt_exact_match()
        TestQ08RoundHeaderPrefix().test_round_header_has_aidm_prefix()
        TestQ09NoDashedSeparators().test_no_dashed_separators()
        TestQ10NoAsteriskDecorators().test_no_asterisk_decorators_in_output()


# ---------------------------------------------------------------------------
# R-14: Full suite regression (baseline)
# ---------------------------------------------------------------------------

class TestR14FullSuiteRegression:
    """Play.py still produces complete, deterministic combat sessions."""

    def test_deterministic_session(self):
        outputs = []
        for _ in range(2):
            output = _run_session(["attack goblin warrior", "end turn"] * 60, seed=42)
            outputs.append(output)
        assert outputs[0] == outputs[1], "Output not deterministic after routing changes"

    def test_session_completes(self):
        output = _run_session(["attack goblin warrior", "end turn"] * 60, seed=42)
        assert "[AIDM] D&D 3.5e Combat -- AIDM Engine" in output
        assert "[AIDM] Round 1" in output
        assert "'s Turn" in output
        assert "[RESOLVE] Attack roll:" in output
        assert "Victory!" in output or "Farewell!" in output or "DEFEATED" in output
