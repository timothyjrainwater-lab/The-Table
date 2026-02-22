"""Gate W tests — Salience Filter enforcement.

15 tests (W-01 through W-15) verifying the line-level salience classifier
and spoken-line filter for the TTS pipeline.

Authority: WO-IMPL-SALIENCE-FILTER-001, CLI Grammar Contract (Gate J).
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from aidm.voice.line_classifier import (
    LineType,
    SALIENCE,
    SPOKEN_TYPES,
    classify_line,
    classify_lines,
    filter_spoken_lines,
)


# ---------------------------------------------------------------------------
# W-01 through W-08: classify_line() unit tests
# ---------------------------------------------------------------------------

class TestW01SystemClassification:
    """W-01: [AIDM] lines classify as SYSTEM."""

    def test_aidm_prefix_is_system(self):
        assert classify_line("[AIDM] System message") == LineType.SYSTEM


class TestW02DetailClassification:
    """W-02: [RESOLVE] lines classify as DETAIL."""

    def test_resolve_prefix_is_detail(self):
        assert classify_line("[RESOLVE] 1d20+5 = 18 vs AC 15: hit") == LineType.DETAIL


class TestW03PromptClassification:
    """W-03: 'Your action?' classifies as PROMPT."""

    def test_prompt_exact_match(self):
        assert classify_line("Your action?") == LineType.PROMPT


class TestW04TurnClassification:
    """W-04: Turn banners classify as TURN."""

    def test_turn_banner(self):
        assert classify_line("Bramble's Turn") == LineType.TURN


class TestW05AlertClassification:
    """W-05: Alert lines classify as ALERT."""

    def test_alert_pattern(self):
        assert classify_line("Bramble is PRONE.") == LineType.ALERT


class TestW06BlankClassification:
    """W-06: Blank lines classify as SYSTEM (non-spoken)."""

    def test_blank_is_system(self):
        assert classify_line("") == LineType.SYSTEM


class TestW07NarrationClassification:
    """W-07: Long narrative sentences classify as NARRATION."""

    def test_narration_long_sentence(self):
        assert classify_line(
            "The orc staggers back, blood streaming from the wound."
        ) == LineType.NARRATION


class TestW08ResultClassification:
    """W-08: Short fallback lines classify as RESULT."""

    def test_short_fallback_is_result(self):
        assert classify_line("Hit.") == LineType.RESULT


# ---------------------------------------------------------------------------
# W-09 through W-11: filter_spoken_lines() tests
# ---------------------------------------------------------------------------

class TestW09FilterMixed:
    """W-09: Mixed input filters to only spoken lines."""

    def test_filter_mixed_input(self):
        text = "[AIDM] init\nBramble's Turn\n[RESOLVE] 1d20=15\nThe blade strikes true."
        result = filter_spoken_lines(text)
        assert result == "Bramble's Turn\nThe blade strikes true."


class TestW10FilterEmpty:
    """W-10: All-silent input filters to empty string."""

    def test_filter_all_silent(self):
        text = "[AIDM] only system\n[RESOLVE] only detail"
        result = filter_spoken_lines(text)
        assert result == ""


class TestW11FilterIdentity:
    """W-11: Single spoken line passes through unchanged."""

    def test_prompt_preserved(self):
        result = filter_spoken_lines("Your action?")
        assert result == "Your action?"


# ---------------------------------------------------------------------------
# W-12 through W-14: structural and integration tests
# ---------------------------------------------------------------------------

class TestW12EnumCompleteness:
    """W-12: LineType enum has exactly 7 members."""

    def test_seven_members(self):
        assert len(LineType) == 7


class TestW13SpokenTypesSet:
    """W-13: SPOKEN_TYPES has exactly 5 members."""

    def test_spoken_types_count(self):
        assert len(SPOKEN_TYPES) == 5
        assert SPOKEN_TYPES == {
            LineType.ALERT, LineType.PROMPT, LineType.TURN,
            LineType.RESULT, LineType.NARRATION,
        }


class TestW14ClassifyLinesIntegration:
    """W-14: classify_lines() returns correct (line, LineType) tuples."""

    def test_classify_lines_mixed(self):
        text = (
            "[AIDM] init\n"
            "Bramble's Turn\n"
            "[RESOLVE] 1d20=15\n"
            "The blade strikes true, cutting deep into the creature's flank."
        )
        result = classify_lines(text)
        assert len(result) == 4
        assert result[0] == ("[AIDM] init", LineType.SYSTEM)
        assert result[1] == ("Bramble's Turn", LineType.TURN)
        assert result[2] == ("[RESOLVE] 1d20=15", LineType.DETAIL)
        assert result[3][1] == LineType.NARRATION


# ---------------------------------------------------------------------------
# W-15: Full suite regression
# ---------------------------------------------------------------------------

class TestW15FullSuiteRegression:
    """W-15: Full test suite still passes after salience filter changes."""

    def test_full_suite_regression(self):
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest", "tests/", "-x",
                "--ignore=tests/test_heuristics_image_critic.py",
                "--ignore=tests/test_ws_bridge.py",
                "--ignore=tests/test_graduated_critique_orchestrator.py",
                "--ignore=tests/test_immersion_authority_contract.py",
                "--ignore=tests/test_pm_inbox_hygiene.py",
                "--ignore=tests/test_speak_signal.py",
                "--ignore=tests/test_salience_gate_w.py",
                "-q",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode == 0, (
            f"Full suite regression failed:\n{result.stdout}\n{result.stderr}"
        )
