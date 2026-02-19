#!/usr/bin/env python3
"""CLI Grammar Validator — checks CLI output against G-01 through G-07.

Usage:
    python scripts/check_cli_grammar.py transcript.txt
    cat transcript.txt | python scripts/check_cli_grammar.py -

Exit code 0 if compliant, 1 if violations found.

Also importable:
    from scripts.check_cli_grammar import check_grammar, Violation
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Line type constants (mirrors CLI_GRAMMAR_CONTRACT.md)
# ---------------------------------------------------------------------------

TURN_BANNER_RE = re.compile(r"^[A-Z][A-Za-z .'-]*'s Turn$")
ALERT_RE = re.compile(r"^.+ is [A-Z]+\.$")
PROMPT_EXACT = "Your action?"
SYSTEM_PREFIX = "[AIDM]"
DETAIL_PREFIX = "[RESOLVE]"

# Anti-pattern regexes (AP-01 through AP-06)
AP_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AP-01", re.compile(r"^-{3,}|^={3,}")),
    ("AP-02", re.compile(r"\(.*\)")),
    ("AP-03", re.compile(r"\b(atk|dmg|hp|AC|DC|DR|SR|CL|BAB)\b")),
    ("AP-04", re.compile(r"^[A-Z][A-Z ]{8,}[.!?]$")),
    ("AP-05", re.compile(r"^\d+[.)]\s")),
    ("AP-06", re.compile(
        "[\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\u2600-\u27BF]"
    )),
]

SPOKEN_TYPES = {"TURN", "RESULT", "ALERT", "NARRATION", "PROMPT"}
NARRATION_TYPES = {"NARRATION"}


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Violation:
    """A single grammar violation."""
    line_number: int
    line_text: str
    rule: str
    message: str

    def __str__(self) -> str:
        return f"L{self.line_number} [{self.rule}]: {self.message}\n  > {self.line_text}"


# ---------------------------------------------------------------------------
# Line classifier
# ---------------------------------------------------------------------------

def classify_line(line: str) -> str:
    """Classify a CLI output line into one of 7 line types."""
    stripped = line.strip()
    if not stripped:
        return "SYSTEM"

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

    sentences = _split_sentences(stripped)
    if 1 <= len(sentences) <= 3 and all(len(s.split()) >= 8 for s in sentences):
        return "NARRATION"

    return "RESULT"


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on terminal punctuation boundaries."""
    raw = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in raw if s.strip()]


# ---------------------------------------------------------------------------
# Grammar checks
# ---------------------------------------------------------------------------

def _check_g01(line_num: int, line: str, line_type: str) -> list[Violation]:
    """G-01: Turn banners must match regex."""
    if line_type != "TURN":
        return []
    if not TURN_BANNER_RE.match(line.strip()):
        return [Violation(line_num, line, "G-01", "Turn banner does not match pattern")]
    return []


def _check_g02(line_num: int, line: str, line_type: str) -> list[Violation]:
    """G-02: Action results — 2 sentences max, no bare numbers."""
    if line_type != "RESULT":
        return []
    violations = []
    stripped = line.strip()
    sentences = _split_sentences(stripped)
    if len(sentences) > 2:
        violations.append(Violation(line_num, line, "G-02", f"Result has {len(sentences)} sentences (max 2)"))
    if re.search(r"\b\d+\b", stripped):
        violations.append(Violation(line_num, line, "G-02", "Bare mechanical number in spoken result"))
    return violations


def _check_g03(line_num: int, line: str, line_type: str) -> list[Violation]:
    """G-03: Alert format — {name} is {STATUS}."""
    if line_type != "ALERT":
        return []
    if not ALERT_RE.match(line.strip()):
        return [Violation(line_num, line, "G-03", "Alert does not match '{name} is {STATUS}.' pattern")]
    return []


def _check_g04(line_num: int, line: str, line_type: str) -> list[Violation]:
    """G-04: Narration — 1-3 sentences, min 8 words, max 120 chars."""
    if line_type != "NARRATION":
        return []
    violations = []
    stripped = line.strip()
    sentences = _split_sentences(stripped)
    if not (1 <= len(sentences) <= 3):
        violations.append(Violation(line_num, line, "G-04", f"Narration has {len(sentences)} sentences (need 1-3)"))
    for sent in sentences:
        wc = len(sent.split())
        if wc < 8:
            violations.append(Violation(line_num, line, "G-04", f"Narration sentence has {wc} words (min 8): {sent!r}"))
    if len(stripped) > 120:
        violations.append(Violation(line_num, line, "G-04", f"Narration line is {len(stripped)} chars (max 120)"))
    return violations


def _check_g05(line_num: int, line: str, line_type: str) -> list[Violation]:
    """G-05: Prompt must be exactly 'Your action?'."""
    if line_type != "PROMPT":
        return []
    if line.strip() != PROMPT_EXACT:
        return [Violation(line_num, line, "G-05", f"Prompt is not exactly '{PROMPT_EXACT}'")]
    return []


def _check_g06(line_num: int, line: str, line_type: str) -> list[Violation]:
    """G-06: System lines must start with [AIDM]."""
    if line_type != "SYSTEM":
        return []
    stripped = line.strip()
    if stripped and not stripped.startswith(SYSTEM_PREFIX):
        return [Violation(line_num, line, "G-06", "System line does not start with [AIDM]")]
    return []


def _check_g07(line_num: int, line: str, line_type: str) -> list[Violation]:
    """G-07: Detail lines must start with [RESOLVE]."""
    if line_type != "DETAIL":
        return []
    if not line.strip().startswith(DETAIL_PREFIX):
        return [Violation(line_num, line, "G-07", "Detail line does not start with [RESOLVE]")]
    return []


def _check_anti_patterns(line_num: int, line: str, line_type: str) -> list[Violation]:
    """AP-01 through AP-07: Forbidden content in spoken output."""
    if line_type not in SPOKEN_TYPES:
        return []
    violations = []
    stripped = line.strip()
    for ap_id, pattern in AP_PATTERNS:
        # AP-05 only applies to narration
        if ap_id == "AP-05" and line_type not in NARRATION_TYPES:
            continue
        if pattern.search(stripped):
            violations.append(Violation(line_num, line, ap_id, f"Anti-pattern {ap_id} in spoken output"))

    # AP-07: Short sentences in narration (word count < 8)
    if line_type in NARRATION_TYPES:
        for sent in _split_sentences(stripped):
            if len(sent.split()) < 8:
                violations.append(Violation(line_num, line, "AP-07", f"Short sentence in narration ({len(sent.split())} words): {sent!r}"))
    return violations


GRAMMAR_CHECKS = [
    _check_g01,
    _check_g02,
    _check_g03,
    _check_g04,
    _check_g05,
    _check_g06,
    _check_g07,
    _check_anti_patterns,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_grammar(lines: list[str]) -> list[Violation]:
    """Check a list of CLI output lines against the grammar contract.

    Args:
        lines: Raw CLI output lines (may include newlines).

    Returns:
        List of Violation objects. Empty list means compliant.
    """
    violations: list[Violation] = []
    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")
        line_type = classify_line(line)
        for check_fn in GRAMMAR_CHECKS:
            violations.extend(check_fn(i, line, line_type))
    return violations


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Run grammar check on a transcript file or stdin."""
    if len(sys.argv) < 2:
        print("Usage: check_cli_grammar.py <transcript_file | ->", file=sys.stderr)
        return 2

    source = sys.argv[1]
    if source == "-":
        lines = sys.stdin.readlines()
    else:
        path = Path(source)
        if not path.exists():
            print(f"File not found: {source}", file=sys.stderr)
            return 2
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    violations = check_grammar(lines)

    if not violations:
        print(f"PASS: {len(lines)} lines checked, 0 violations.")
        return 0

    print(f"FAIL: {len(violations)} violation(s) in {len(lines)} lines.\n")
    for v in violations:
        print(v)
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
