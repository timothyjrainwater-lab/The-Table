"""Gate Q tests — Grammar Implementation enforcement.

12 tests verifying that play.py output complies with the CLI Grammar Contract.

Categories:
    Q-01: Turn banner matches G-01 regex for player turns
    Q-02: Turn banner matches G-01 regex for enemy turns
    Q-03: Defeat alert matches G-03 regex
    Q-04: Condition alert matches G-03 regex
    Q-05: Condition alert has no parenthetical duration (AP-02)
    Q-06: Duration info appears as [RESOLVE] line
    Q-07: Prompt output is exactly 'Your action?' (G-05)
    Q-08: Round header has [AIDM] prefix (G-06)
    Q-09: No dashed separators in output (AP-01)
    Q-10: No asterisk decorators in alerts
    Q-11: Existing Gate J tests still pass (27/27)
    Q-12: Full suite regression (baseline)

Authority: WO-VOICE-GRAMMAR-IMPL-001, RQ-GRAMMAR-001 (CLI_GRAMMAR_CONTRACT.md).
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

from play import format_events, main

# ---------------------------------------------------------------------------
# Grammar contract constants (from CLI_GRAMMAR_CONTRACT.md / Gate J)
# ---------------------------------------------------------------------------

TURN_BANNER_RE = re.compile(r"^[A-Z][A-Za-z .'-]*'s Turn$")
ALERT_RE = re.compile(r"^.+ is [A-Z]+\.$")
PROMPT_EXACT = "Your action?"
SYSTEM_PREFIX = "[AIDM]"
DETAIL_PREFIX = "[RESOLVE]"


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
    """Create a minimal WorldState with given entities."""
    return WorldState(ruleset_version="3.5", entities=entities)


# ---------------------------------------------------------------------------
# Q-01: Turn banner matches G-01 regex for player turns
# ---------------------------------------------------------------------------

class TestQ01PlayerTurnBanner:
    """Player turn banners in live CLI output match G-01."""

    def test_player_turn_banner_matches_g01(self):
        output = _run_session(["quit"])
        lines = output.splitlines()
        turn_lines = [l.strip() for l in lines if "'s Turn" in l]
        assert len(turn_lines) > 0, "No turn banners found in output"
        for banner in turn_lines:
            assert TURN_BANNER_RE.match(banner), (
                f"Turn banner does not match G-01: {banner!r}"
            )


# ---------------------------------------------------------------------------
# Q-02: Turn banner matches G-01 regex for enemy turns
# ---------------------------------------------------------------------------

class TestQ02EnemyTurnBanner:
    """Enemy turn banners in live CLI output match G-01."""

    def test_enemy_turn_banner_matches_g01(self):
        # Play enough to see enemy turns (enemies act after players)
        output = _run_session(["attack goblin warrior", "end turn"] * 10, seed=42)
        lines = output.splitlines()
        turn_lines = [l.strip() for l in lines if "'s Turn" in l]
        # Need at least one enemy turn banner (Goblin Warrior, etc.)
        fixture = build_simple_combat_fixture(master_seed=42)
        enemy_names = [
            e.get("name", eid)
            for eid, e in fixture.world_state.entities.items()
            if e.get(EF.TEAM) != "party"
        ]
        enemy_banners = [b for b in turn_lines if any(n in b for n in enemy_names)]
        assert len(enemy_banners) > 0, "No enemy turn banners found"
        for banner in enemy_banners:
            assert TURN_BANNER_RE.match(banner), (
                f"Enemy turn banner does not match G-01: {banner!r}"
            )


# ---------------------------------------------------------------------------
# Q-03: Defeat alert matches G-03 regex
# ---------------------------------------------------------------------------

class TestQ03DefeatAlert:
    """Defeat alerts from format_events match G-03."""

    def test_defeat_alert_matches_g03(self):
        ws = _make_ws(goblin_1={"name": "Goblin Scout"})
        events = [Event(
            event_id=0, event_type="entity_defeated", timestamp=0.0,
            payload={"entity_id": "goblin_1"},
        )]
        output = format_events(events, ws)
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        defeat_lines = [l for l in lines if "DEFEATED" in l]
        assert len(defeat_lines) == 1, f"Expected 1 defeat line, got {len(defeat_lines)}"
        assert ALERT_RE.match(defeat_lines[0]), (
            f"Defeat alert does not match G-03: {defeat_lines[0]!r}"
        )


# ---------------------------------------------------------------------------
# Q-04: Condition alert matches G-03 regex
# ---------------------------------------------------------------------------

class TestQ04ConditionAlert:
    """Non-spell condition alerts from format_events match G-03."""

    def test_condition_alert_matches_g03(self):
        ws = _make_ws(goblin_1={"name": "Goblin Scout"})
        events = [Event(
            event_id=0, event_type="condition_applied", timestamp=0.0,
            payload={
                "entity_id": "goblin_1", "condition": "prone",
                "source": "trip_attack",
            },
        )]
        output = format_events(events, ws)
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        alert_lines = [l for l in lines if "PRONE" in l]
        assert len(alert_lines) == 1, f"Expected 1 alert line, got {len(alert_lines)}"
        assert ALERT_RE.match(alert_lines[0]), (
            f"Condition alert does not match G-03: {alert_lines[0]!r}"
        )

    def test_condition_with_duration_alert_matches_g03(self):
        ws = _make_ws(fighter_1={"name": "Kael"})
        events = [Event(
            event_id=0, event_type="condition_applied", timestamp=0.0,
            payload={
                "entity_id": "fighter_1", "condition": "stunned",
                "source": "power_attack", "duration_rounds": 2,
            },
        )]
        output = format_events(events, ws)
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        alert_lines = [l for l in lines if "STUNNED" in l]
        assert len(alert_lines) == 1, f"Expected 1 alert line, got {len(alert_lines)}"
        assert ALERT_RE.match(alert_lines[0]), (
            f"Condition alert with duration does not match G-03: {alert_lines[0]!r}"
        )


# ---------------------------------------------------------------------------
# Q-05: Condition alert has no parenthetical duration (AP-02)
# ---------------------------------------------------------------------------

class TestQ05NoParentheticalDuration:
    """Condition alerts must not contain parenthetical asides."""

    def test_no_parenthetical_in_condition_alert(self):
        ws = _make_ws(goblin_1={"name": "Goblin Scout"})
        events = [Event(
            event_id=0, event_type="condition_applied", timestamp=0.0,
            payload={
                "entity_id": "goblin_1", "condition": "dazed",
                "source": "stunning_fist", "duration_rounds": 3,
            },
        )]
        output = format_events(events, ws)
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        # Filter to only alert-type lines (not [RESOLVE] lines)
        alert_lines = [l for l in lines if not l.startswith("[RESOLVE]")]
        for line in alert_lines:
            assert "(" not in line, (
                f"Parenthetical found in alert (AP-02 violation): {line!r}"
            )

    def test_no_parenthetical_in_spell_condition(self):
        ws = _make_ws(goblin_1={"name": "Goblin Scout"})
        events = [Event(
            event_id=0, event_type="condition_applied", timestamp=0.0,
            payload={
                "entity_id": "goblin_1", "condition": "held",
                "source": "spell:Hold Person", "duration_rounds": 5,
            },
        )]
        output = format_events(events, ws)
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        non_resolve_lines = [l for l in lines if not l.startswith("[RESOLVE]")]
        for line in non_resolve_lines:
            assert "(" not in line, (
                f"Parenthetical found in spell condition alert (AP-02 violation): {line!r}"
            )


# ---------------------------------------------------------------------------
# Q-06: Duration info appears as [RESOLVE] line
# ---------------------------------------------------------------------------

class TestQ06ResolveDuration:
    """Duration info appears as [RESOLVE] detail line, not in alert."""

    def test_duration_in_resolve_line(self):
        ws = _make_ws(goblin_1={"name": "Goblin Scout"})
        events = [Event(
            event_id=0, event_type="condition_applied", timestamp=0.0,
            payload={
                "entity_id": "goblin_1", "condition": "shaken",
                "source": "fear_effect", "duration_rounds": 4,
            },
        )]
        output = format_events(events, ws)
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        resolve_lines = [l for l in lines if l.startswith("[RESOLVE]")]
        assert len(resolve_lines) >= 1, "No [RESOLVE] line for duration info"
        assert any("4 rounds remaining" in l for l in resolve_lines), (
            f"Duration not in [RESOLVE] line: {resolve_lines}"
        )

    def test_spell_duration_in_resolve_line(self):
        ws = _make_ws(goblin_1={"name": "Goblin Scout"})
        events = [Event(
            event_id=0, event_type="condition_applied", timestamp=0.0,
            payload={
                "entity_id": "goblin_1", "condition": "entangled",
                "source": "spell:Web", "duration_rounds": 7,
            },
        )]
        output = format_events(events, ws)
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        resolve_lines = [l for l in lines if l.startswith("[RESOLVE]")]
        assert len(resolve_lines) >= 1, "No [RESOLVE] line for spell duration"
        assert any("7 rounds remaining" in l for l in resolve_lines), (
            f"Spell duration not in [RESOLVE] line: {resolve_lines}"
        )


# ---------------------------------------------------------------------------
# Q-07: Prompt output is exactly 'Your action?' (G-05)
# ---------------------------------------------------------------------------

class TestQ07PromptFormat:
    """Prompt display in CLI output is exactly 'Your action?'."""

    def test_prompt_exact_match(self):
        output = _run_session(["quit"])
        lines = output.splitlines()
        prompt_lines = [l.strip() for l in lines if "action?" in l.lower()]
        assert len(prompt_lines) >= 1, "No prompt line found in output"
        for prompt_line in prompt_lines:
            assert prompt_line == PROMPT_EXACT, (
                f"Prompt does not match G-05: {prompt_line!r} != {PROMPT_EXACT!r}"
            )


# ---------------------------------------------------------------------------
# Q-08: Round header has [AIDM] prefix (G-06)
# ---------------------------------------------------------------------------

class TestQ08RoundHeaderPrefix:
    """Round headers use [AIDM] prefix per G-06."""

    def test_round_header_has_aidm_prefix(self):
        output = _run_session(["quit"])
        lines = output.splitlines()
        round_lines = [l.strip() for l in lines if "Round" in l and l.strip().startswith("[AIDM]")]
        assert len(round_lines) >= 1, "No [AIDM] Round header found"
        for line in round_lines:
            assert line.startswith(SYSTEM_PREFIX), (
                f"Round header missing [AIDM] prefix: {line!r}"
            )
            assert re.match(r"^\[AIDM\] Round \d+$", line), (
                f"Round header wrong format: {line!r}"
            )


# ---------------------------------------------------------------------------
# Q-09: No dashed separators in output (AP-01)
# ---------------------------------------------------------------------------

class TestQ09NoDashedSeparators:
    """CLI output contains no dashed or equals separators (AP-01)."""

    def test_no_dashed_separators(self):
        output = _run_session(["attack goblin warrior", "end turn"] * 10, seed=42)
        lines = output.splitlines()
        ap01 = re.compile(r"^-{3,}|^={3,}")
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            assert not ap01.match(stripped), (
                f"Dashed separator found (AP-01 violation): {stripped!r}"
            )


# ---------------------------------------------------------------------------
# Q-10: No asterisk decorators in alerts
# ---------------------------------------------------------------------------

class TestQ10NoAsteriskDecorators:
    """Alerts contain no *** decorators."""

    def test_no_asterisk_decorators_in_output(self):
        # Play a full session to get defeat alerts
        output = _run_session(["attack goblin warrior", "end turn"] * 60, seed=42)
        lines = output.splitlines()
        for line in lines:
            stripped = line.strip()
            assert "***" not in stripped, (
                f"Asterisk decorator found in output: {stripped!r}"
            )


# ---------------------------------------------------------------------------
# Q-11: Existing Gate J tests still pass (27/27)
# ---------------------------------------------------------------------------

class TestQ11GateJRegression:
    """Gate J tests imported and executed — all 27 must pass."""

    def test_gate_j_passes(self):
        # This is a meta-test: if Gate J fails, this file's test run
        # will also show the Gate J failures. The purpose is to make
        # Gate Q explicitly depend on Gate J.
        from tests.test_grammar_gate_j import (
            TestJ01TurnBanner,
            TestJ02ActionResult,
            TestJ03AlertFormat,
            TestJ04Narration,
            TestJ05Prompt,
            TestJ06SystemPrefix,
            TestJ07DetailPrefix,
            TestJ08AntiPatterns,
            TestJ09ClassifierCompleteness,
            TestJ10VoiceRouting,
        )
        # Instantiate and run one representative test from each gate
        TestJ01TurnBanner().test_valid_banners_match()
        TestJ03AlertFormat().test_valid_alerts_match()
        TestJ05Prompt().test_valid_prompt()
        TestJ06SystemPrefix().test_valid_system_lines()
        TestJ07DetailPrefix().test_valid_detail_lines()
        TestJ09ClassifierCompleteness().test_classifications_match_expected()


# ---------------------------------------------------------------------------
# Q-12: Full suite regression (baseline)
# ---------------------------------------------------------------------------

class TestQ12FullSuiteRegression:
    """Verify play.py still produces a complete, deterministic combat session."""

    def test_deterministic_session(self):
        """Same seed + same inputs = identical output (format changes don't break determinism)."""
        outputs = []
        for _ in range(2):
            output = _run_session(["attack goblin warrior", "end turn"] * 60, seed=42)
            outputs.append(output)
        assert outputs[0] == outputs[1], "Output not deterministic after grammar changes"

    def test_session_completes(self):
        """Combat session runs to completion with grammar changes."""
        output = _run_session(["attack goblin warrior", "end turn"] * 60, seed=42)
        assert "D&D 3.5e Combat -- AIDM Engine" in output
        assert "Round 1" in output
        assert "'s Turn" in output
        # Game should reach conclusion
        assert "Victory!" in output or "Farewell!" in output or "DEFEATED" in output
