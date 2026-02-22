"""Line-level salience classifier for CLI output.

Classifies each line of narration output into one of 7 line types
with associated salience levels (S1-S6). Used by the TTS pipeline
to filter non-spoken lines before synthesis.

Source: CLI Grammar Contract (Gate J), WO-VOICE-GRAMMAR-IMPL-001.
"""
import re
from enum import Enum
from typing import List, Tuple


class LineType(str, Enum):
    """CLI output line types with salience ordering."""
    ALERT = "ALERT"          # S1 — highest
    PROMPT = "PROMPT"        # S2
    TURN = "TURN"            # S3
    RESULT = "RESULT"        # S3
    NARRATION = "NARRATION"  # S4
    DETAIL = "DETAIL"        # S5 — not spoken
    SYSTEM = "SYSTEM"        # S6 — not spoken


# Salience levels — S1 through S6
SALIENCE = {
    LineType.ALERT: 1,
    LineType.PROMPT: 2,
    LineType.TURN: 3,
    LineType.RESULT: 3,
    LineType.NARRATION: 4,
    LineType.DETAIL: 5,
    LineType.SYSTEM: 6,
}

# Lines at or below this salience level are spoken
SPOKEN_THRESHOLD = 4  # S1-S4 spoken, S5-S6 silent

SPOKEN_TYPES = {LineType.ALERT, LineType.PROMPT, LineType.TURN,
                LineType.RESULT, LineType.NARRATION}

# Detection patterns (from CLI Grammar Contract)
SYSTEM_PREFIX = "[AIDM]"
DETAIL_PREFIX = "[RESOLVE]"
PROMPT_EXACT = "Your action?"
TURN_BANNER_RE = re.compile(r"^[A-Z][A-Za-z .'-]*'s Turn$")
ALERT_RE = re.compile(r"^.+ is [A-Z]+\.$")


def _split_sentences(text: str) -> list:
    """Split text into sentences on terminal punctuation boundaries."""
    raw = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in raw if s.strip()]


def classify_line(line: str) -> LineType:
    """Classify a single line into one of 7 line types.

    Priority order:
    1. SYSTEM — starts with [AIDM] or blank
    2. DETAIL — starts with [RESOLVE]
    3. PROMPT — exact match "Your action?"
    4. TURN — matches turn banner regex
    5. ALERT — matches alert regex
    6. NARRATION or RESULT — fallback heuristic

    Args:
        line: A single line of CLI output.

    Returns:
        LineType enum value.
    """
    stripped = line.strip()
    if not stripped:
        return LineType.SYSTEM

    if stripped.startswith(SYSTEM_PREFIX):
        return LineType.SYSTEM
    if stripped.startswith(DETAIL_PREFIX):
        return LineType.DETAIL
    if stripped == PROMPT_EXACT:
        return LineType.PROMPT
    if TURN_BANNER_RE.match(stripped):
        return LineType.TURN
    if ALERT_RE.match(stripped):
        return LineType.ALERT

    # Fallback: NARRATION if 1-3 sentences with >= 8 words each, else RESULT
    sentences = _split_sentences(stripped)
    if 1 <= len(sentences) <= 3 and all(len(s.split()) >= 8 for s in sentences):
        return LineType.NARRATION

    return LineType.RESULT


def classify_lines(text: str) -> List[Tuple[str, LineType]]:
    """Classify all lines in a multi-line text block.

    Args:
        text: Multi-line narration text.

    Returns:
        List of (line, LineType) tuples.
    """
    return [(line, classify_line(line)) for line in text.split("\n")]


def filter_spoken_lines(text: str) -> str:
    """Filter text to only spoken lines (S1-S4).

    Removes DETAIL ([RESOLVE]) and SYSTEM ([AIDM]) lines.
    Returns empty string if no spoken lines remain.

    Args:
        text: Multi-line narration text.

    Returns:
        Filtered text with only spoken lines, newline-joined.
    """
    spoken = []
    for line, line_type in classify_lines(text):
        if line_type in SPOKEN_TYPES:
            spoken.append(line)
    return "\n".join(spoken)
