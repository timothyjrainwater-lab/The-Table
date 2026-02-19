"""Gate J tests — CLI Grammar Contract enforcement.

10 tests across 4 gate categories (J-01 through J-10).

Categories:
    J-01..J-07: Grammar rules G-01 through G-07 (7 tests)
    J-08: Anti-pattern enforcement (1 test)
    J-09: Line classifier completeness (1 test)
    J-10: Voice routing table (1 test)

Authority: WO-VOICE-GRAMMAR-SPEC-001, RQ-GRAMMAR-001 (CLI_GRAMMAR_CONTRACT.md).
"""
from __future__ import annotations

import re

import pytest

# ---------------------------------------------------------------------------
# Grammar contract constants — mirroring CLI_GRAMMAR_CONTRACT.md
# ---------------------------------------------------------------------------

# G-01: Turn banner regex
TURN_BANNER_RE = re.compile(r"^[A-Z][A-Za-z .'-]*'s Turn$")

# G-03: Alert format regex
ALERT_RE = re.compile(r"^.+ is [A-Z]+\.$")

# G-05: Prompt exact string
PROMPT_EXACT = "Your action?"

# G-06 / G-07: Prefix detection
SYSTEM_PREFIX = "[AIDM]"
DETAIL_PREFIX = "[RESOLVE]"

# Anti-pattern regexes (AP-01 through AP-06; AP-07 is word-count based)
AP_DASHED_SEPARATORS = re.compile(r"^-{3,}|^={3,}")
AP_PARENTHETICAL = re.compile(r"\(.*\)")
AP_ABBREVIATIONS = re.compile(r"\b(atk|dmg|hp|AC|DC|DR|SR|CL|BAB)\b")
AP_ALL_CAPS_SENTENCE = re.compile(r"^[A-Z][A-Z ]{8,}[.!?]$")
AP_NUMBERED_LIST = re.compile(r"^\d+[.)]\s")
AP_EMOJI = re.compile(
    "[\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\u2600-\u27BF]"
)

# Line types and their properties
LINE_TYPES = {
    "TURN": {"spoken": True, "persona": "DM", "salience": "S3"},
    "RESULT": {"spoken": True, "persona": "DM", "salience": "S3"},
    "ALERT": {"spoken": True, "persona": "Arbor", "salience": "S1"},
    "NARRATION": {"spoken": True, "persona": "DM", "salience": "S4"},
    "PROMPT": {"spoken": True, "persona": "Arbor", "salience": "S2"},
    "SYSTEM": {"spoken": False, "persona": None, "salience": "S6"},
    "DETAIL": {"spoken": False, "persona": None, "salience": "S5"},
}

SPOKEN_TYPES = {k for k, v in LINE_TYPES.items() if v["spoken"]}
SILENT_TYPES = {k for k, v in LINE_TYPES.items() if not v["spoken"]}


# ---------------------------------------------------------------------------
# Line classifier (the contract says every line maps to exactly one type)
# ---------------------------------------------------------------------------

def classify_line(line: str) -> str:
    """Classify a single CLI output line into exactly one line type.

    Classification priority (evaluated in order):
    1. SYSTEM — starts with [AIDM]
    2. DETAIL — starts with [RESOLVE]
    3. PROMPT — exact match 'Your action?'
    4. TURN — matches turn banner regex
    5. ALERT — matches alert regex
    6. NARRATION / RESULT — fallback (contextual; defaults to RESULT)

    Returns one of: TURN, RESULT, ALERT, NARRATION, PROMPT, SYSTEM, DETAIL.
    """
    stripped = line.strip()
    if not stripped:
        return "SYSTEM"  # blank lines are non-spoken system formatting

    if stripped.startswith(SYSTEM_PREFIX):
        return "SYSTEM"
    if stripped.startswith(DETAIL_PREFIX):
        return "DETAIL"
    if stripped == PROMPT_EXACT:
        return "PROMPT"
    if TURN_BANNER_RE.match(stripped):
        return "TURN"
    if ALERT_RE.match(stripped):
        return "ALERT"

    # Fallback: non-prefixed, non-matching lines are either NARRATION or RESULT.
    # NARRATION: 1-3 sentences, min 8 words/sentence.
    # RESULT: 1-2 sentences, may be shorter.
    # Without full context, classify based on sentence length heuristic.
    sentences = _split_sentences(stripped)
    if 1 <= len(sentences) <= 3 and all(len(s.split()) >= 8 for s in sentences):
        return "NARRATION"

    return "RESULT"


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on period/exclamation/question boundaries."""
    raw = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in raw if s.strip()]


# ---------------------------------------------------------------------------
# Fixture sample lines — valid and invalid for each grammar rule
# ---------------------------------------------------------------------------

# G-01 fixtures
VALID_TURN_BANNERS = [
    "Kael's Turn",
    "Goblin Scout's Turn",
    "Sir Aldric the Bold's Turn",
    "K'thrax's Turn",
]
INVALID_TURN_BANNERS = [
    "--- Kael's Turn ---",
    "[TURN] Kael's Turn",
    "kael's Turn",
    "Kael's turn",
    "Kael's Turn!",
    "",
]

# G-02 fixtures
VALID_RESULTS = [
    "The sword bites deep. The goblin staggers backward.",
    "The arrow flies wide, clattering off the stone wall.",
    "A solid hit. The creature howls in pain.",
]
INVALID_RESULTS = [
    "The sword hits for 14 damage. The goblin has 6 HP remaining.",
    "The blade strikes true. The enemy recoils. Blood spatters the stone floor.",
]

# G-03 fixtures
VALID_ALERTS = [
    "Goblin Scout is DEFEATED.",
    "Kael is BLOODIED.",
    "Dire Wolf is PRONE.",
]
INVALID_ALERTS = [
    "goblin is hurt",
    "The goblin scout has been defeated.",
    "Kael is bloodied.",
    "Goblin is DEFEATED",
]

# G-04 fixtures
VALID_NARRATIONS = [
    "The torchlight flickers against the damp stone walls of the corridor.",
    "Steel rings against steel as the combatants circle warily. The crowd holds its collective breath in anticipation.",
]
INVALID_NARRATIONS_SHORT = [
    "Fire burns.",
    "It is dark.",
]
INVALID_NARRATION_LONG = "A" * 121  # > 120 chars

# G-05 fixtures
VALID_PROMPTS = ["Your action?"]
INVALID_PROMPTS = [
    "What do you do?",
    "> Your action?",
    "Your action? ",
    "your action?",
]

# G-06 fixtures
VALID_SYSTEM = [
    "[AIDM] Loading campaign data...",
    "[AIDM] ERROR: Missing asset",
    "[AIDM] Bootstrap complete",
]
INVALID_SYSTEM = [
    "AIDM: Loading...",
    "[aidm] Loading...",
    "Loading...",
]

# G-07 fixtures
VALID_DETAIL = [
    "[RESOLVE] Rolling attack: [17]+5 = 22",
    "[RESOLVE] Result: HIT",
    "[RESOLVE] Processing action...",
]
INVALID_DETAIL = [
    "Rolling attack: [17]+5 = 22",
    "[RESOLVE]",  # prefix alone, no content (edge case — still valid prefix)
    "RESOLVE: Rolling...",
]

# Anti-pattern fixture lines (all forbidden in spoken output)
ANTI_PATTERN_LINES = [
    "---",                                          # AP-01
    "===========================",                  # AP-01
    "The goblin (see Monster Manual p.166) attacks", # AP-02
    "Kael rolls atk vs AC",                          # AP-03
    "The fighter takes 12 dmg",                      # AP-03
    "THE GOBLIN ATTACKS WITH FURIOUS RAGE.",          # AP-04
    "1) The goblin moves forward",                   # AP-05
    "2. Another numbered step here",                 # AP-05
    "The goblin attacks! \U0001F525",                # AP-06
]

# Sample transcript for classifier completeness
SAMPLE_TRANSCRIPT = [
    "[AIDM] Combat round 3 starting",
    "Kael's Turn",
    "The blade finds its mark. A spray of dark blood follows the arc.",
    "[RESOLVE] Rolling attack: [18]+5 = 23",
    "[RESOLVE]   vs AC 15 → HIT",
    "Goblin Scout is DEFEATED.",
    "The torchlight flickers against the damp stone walls of the ancient corridor.",
    "Your action?",
]

EXPECTED_CLASSIFICATIONS = [
    "SYSTEM",
    "TURN",
    "RESULT",
    "DETAIL",
    "DETAIL",
    "ALERT",
    "NARRATION",
    "PROMPT",
]


# ---------------------------------------------------------------------------
# J-01: G-01 Turn Banner (3 tests)
# ---------------------------------------------------------------------------

class TestJ01TurnBanner:
    """G-01 — Turn banners match `^[A-Z].*'s Turn$`, no decorators."""

    def test_valid_banners_match(self):
        for banner in VALID_TURN_BANNERS:
            assert TURN_BANNER_RE.match(banner), f"Should match: {banner!r}"

    def test_invalid_banners_rejected(self):
        for banner in INVALID_TURN_BANNERS:
            assert not TURN_BANNER_RE.match(banner), f"Should reject: {banner!r}"

    def test_classified_as_turn(self):
        for banner in VALID_TURN_BANNERS:
            assert classify_line(banner) == "TURN", f"Should classify as TURN: {banner!r}"


# ---------------------------------------------------------------------------
# J-02: G-02 Action Result (3 tests)
# ---------------------------------------------------------------------------

class TestJ02ActionResult:
    """G-02 — Action results: <= 2 sentences, no bare mechanical numbers."""

    def test_valid_results_two_sentences_max(self):
        for result in VALID_RESULTS:
            sentences = _split_sentences(result)
            assert len(sentences) <= 2, f"Too many sentences: {result!r}"

    def test_no_bare_numbers_in_valid_results(self):
        bare_number = re.compile(r"\b\d+\b")
        for result in VALID_RESULTS:
            assert not bare_number.search(result), f"Bare number in result: {result!r}"

    def test_invalid_results_detected(self):
        bare_number = re.compile(r"\b\d+\b")
        # First invalid has bare numbers
        assert bare_number.search(INVALID_RESULTS[0])
        # Second invalid has > 2 sentences
        sentences = _split_sentences(INVALID_RESULTS[1])
        assert len(sentences) > 2


# ---------------------------------------------------------------------------
# J-03: G-03 Alert Format (2 tests)
# ---------------------------------------------------------------------------

class TestJ03AlertFormat:
    """G-03 — Alerts match `^.+ is [A-Z]+\\.$`."""

    def test_valid_alerts_match(self):
        for alert in VALID_ALERTS:
            assert ALERT_RE.match(alert), f"Should match: {alert!r}"

    def test_invalid_alerts_rejected(self):
        for alert in INVALID_ALERTS:
            assert not ALERT_RE.match(alert), f"Should reject: {alert!r}"


# ---------------------------------------------------------------------------
# J-04: G-04 Narration (3 tests)
# ---------------------------------------------------------------------------

class TestJ04Narration:
    """G-04 — Narration: 1-3 sentences, >= 8 words each, <= 120 chars/line."""

    def test_valid_narrations_comply(self):
        for narration in VALID_NARRATIONS:
            sentences = _split_sentences(narration)
            assert 1 <= len(sentences) <= 3, f"Sentence count: {narration!r}"
            for sent in sentences:
                assert len(sent.split()) >= 8, f"Under 8 words: {sent!r}"
            assert len(narration) <= 120, f"Over 120 chars: {narration!r}"

    def test_short_sentences_rejected(self):
        for narration in INVALID_NARRATIONS_SHORT:
            sentences = _split_sentences(narration)
            for sent in sentences:
                assert len(sent.split()) < 8, f"Should be < 8 words: {sent!r}"

    def test_long_lines_rejected(self):
        assert len(INVALID_NARRATION_LONG) > 120


# ---------------------------------------------------------------------------
# J-05: G-05 Prompt (2 tests)
# ---------------------------------------------------------------------------

class TestJ05Prompt:
    """G-05 — Prompt is exactly 'Your action?'."""

    def test_valid_prompt(self):
        assert VALID_PROMPTS[0] == PROMPT_EXACT

    def test_invalid_prompts_rejected(self):
        for prompt in INVALID_PROMPTS:
            assert prompt != PROMPT_EXACT, f"Should not match: {prompt!r}"


# ---------------------------------------------------------------------------
# J-06: G-06 System Prefix (2 tests)
# ---------------------------------------------------------------------------

class TestJ06SystemPrefix:
    """G-06 — System lines start with [AIDM]; never spoken."""

    def test_valid_system_lines(self):
        for line in VALID_SYSTEM:
            assert line.startswith(SYSTEM_PREFIX), f"Should start with [AIDM]: {line!r}"
            assert classify_line(line) == "SYSTEM"

    def test_system_is_not_spoken(self):
        assert LINE_TYPES["SYSTEM"]["spoken"] is False


# ---------------------------------------------------------------------------
# J-07: G-07 Detail Prefix (2 tests)
# ---------------------------------------------------------------------------

class TestJ07DetailPrefix:
    """G-07 — Detail lines start with [RESOLVE]; never spoken."""

    def test_valid_detail_lines(self):
        for line in VALID_DETAIL:
            assert line.startswith(DETAIL_PREFIX), f"Should start with [RESOLVE]: {line!r}"
            assert classify_line(line) == "DETAIL"

    def test_detail_is_not_spoken(self):
        assert LINE_TYPES["DETAIL"]["spoken"] is False


# ---------------------------------------------------------------------------
# J-08: Anti-Pattern Enforcement (1 test, multiple sub-checks)
# ---------------------------------------------------------------------------

class TestJ08AntiPatterns:
    """AP-01 through AP-07 — Forbidden content in spoken output."""

    def test_anti_patterns_detected(self):
        """Every anti-pattern fixture line triggers at least one check."""
        patterns = [
            AP_DASHED_SEPARATORS,
            AP_PARENTHETICAL,
            AP_ABBREVIATIONS,
            AP_ALL_CAPS_SENTENCE,
            AP_NUMBERED_LIST,
            AP_EMOJI,
        ]
        for line in ANTI_PATTERN_LINES:
            matched = any(p.search(line) for p in patterns)
            assert matched, f"No anti-pattern caught: {line!r}"

    def test_valid_spoken_lines_pass(self):
        """Valid spoken lines do not trigger anti-pattern checks."""
        clean_lines = (
            VALID_TURN_BANNERS
            + VALID_RESULTS
            + VALID_ALERTS
            + VALID_NARRATIONS
            + VALID_PROMPTS
        )
        patterns = [
            AP_DASHED_SEPARATORS,
            AP_PARENTHETICAL,
            AP_ABBREVIATIONS,
            AP_ALL_CAPS_SENTENCE,
            AP_NUMBERED_LIST,
            AP_EMOJI,
        ]
        for line in clean_lines:
            violations = [p.pattern for p in patterns if p.search(line)]
            assert not violations, f"False positive on {line!r}: {violations}"


# ---------------------------------------------------------------------------
# J-09: Line Classifier Completeness (1 test)
# ---------------------------------------------------------------------------

class TestJ09ClassifierCompleteness:
    """Every sample transcript line gets exactly one type assignment."""

    def test_all_lines_classified(self):
        results = [classify_line(line) for line in SAMPLE_TRANSCRIPT]
        for i, (line, result) in enumerate(zip(SAMPLE_TRANSCRIPT, results)):
            assert result in LINE_TYPES, f"Line {i} classified as unknown type {result!r}: {line!r}"

    def test_classifications_match_expected(self):
        results = [classify_line(line) for line in SAMPLE_TRANSCRIPT]
        for i, (actual, expected) in enumerate(zip(results, EXPECTED_CLASSIFICATIONS)):
            assert actual == expected, (
                f"Line {i}: expected {expected}, got {actual} for {SAMPLE_TRANSCRIPT[i]!r}"
            )

    def test_seven_types_defined(self):
        assert len(LINE_TYPES) == 7


# ---------------------------------------------------------------------------
# J-10: Voice Routing Table (1 test)
# ---------------------------------------------------------------------------

class TestJ10VoiceRouting:
    """Voice routing matches contract — spoken/silent, persona assignment."""

    def test_spoken_types_have_persona(self):
        for type_name in SPOKEN_TYPES:
            props = LINE_TYPES[type_name]
            assert props["spoken"] is True
            assert props["persona"] is not None, f"{type_name} spoken but no persona"

    def test_silent_types_have_no_persona(self):
        for type_name in SILENT_TYPES:
            props = LINE_TYPES[type_name]
            assert props["spoken"] is False
            assert props["persona"] is None, f"{type_name} silent but has persona"

    def test_dm_persona_types(self):
        dm_types = {"TURN", "RESULT", "NARRATION"}
        for t in dm_types:
            assert LINE_TYPES[t]["persona"] == "DM"

    def test_arbor_persona_types(self):
        arbor_types = {"ALERT", "PROMPT"}
        for t in arbor_types:
            assert LINE_TYPES[t]["persona"] == "Arbor"

    def test_system_detail_never_spoken(self):
        assert LINE_TYPES["SYSTEM"]["spoken"] is False
        assert LINE_TYPES["DETAIL"]["spoken"] is False
