#!/usr/bin/env python3
"""Unknown Handling Policy Validator — checks voice interaction transcripts.

Usage:
    python scripts/check_unknown_handling.py events.jsonl
    cat events.jsonl | python scripts/check_unknown_handling.py -

Event format (one JSON object per line):
    {"transcript": "attack goblin", "asr_confidence": 0.90, "stoplight": "GREEN",
     "confirmed": true, "provenance_tags": ["[VOICE]"], ...}

Exit code 0 if compliant, 1 if violations found.

Also importable:
    from scripts.check_unknown_handling import check_unknown_policy, Violation
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants (mirrors UNKNOWN_HANDLING_CONTRACT.md)
# ---------------------------------------------------------------------------

GREEN_THRESHOLD = 0.85
YELLOW_THRESHOLD = 0.50
STALE_THRESHOLD_S = 5.0
MAX_CLARIFICATIONS = 2

VALID_STOPLIGHT_COLORS = frozenset({"GREEN", "YELLOW", "RED", "ROUTING"})

REQUIRED_PROVENANCE_TAGS = frozenset({
    "[VOICE]", "[INFERRED]", "[CONSTRAINED]",
    "[CLARIFIED]", "[MENU-SELECTED]", "[CANCELLED]",
})

FORBIDDEN_RESOLUTION_METHODS = frozenset({
    "llm_inference", "embedding_similarity", "probabilistic_nlp",
})


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Violation:
    """A single policy violation."""
    event_index: int
    rule: str
    message: str
    event_summary: str

    def __str__(self) -> str:
        return f"Event {self.event_index} [{self.rule}]: {self.message}\n  > {self.event_summary}"


# ---------------------------------------------------------------------------
# Policy checks
# ---------------------------------------------------------------------------

def _check_stoplight_classification(idx: int, event: dict[str, Any]) -> list[Violation]:
    """Check that STOPLIGHT classification exists and is valid."""
    violations = []
    summary = _event_summary(event)
    stoplight = event.get("stoplight")

    if stoplight is None:
        violations.append(Violation(idx, "INVARIANT-1", "No STOPLIGHT classification assigned", summary))
        return violations

    if stoplight not in VALID_STOPLIGHT_COLORS:
        violations.append(Violation(idx, "INVARIANT-1", f"Invalid STOPLIGHT color: {stoplight!r}", summary))

    return violations


def _check_confidence_thresholds(idx: int, event: dict[str, Any]) -> list[Violation]:
    """Check that STOPLIGHT color matches ASR confidence thresholds."""
    violations = []
    summary = _event_summary(event)
    confidence = event.get("asr_confidence")
    stoplight = event.get("stoplight")

    if confidence is None or stoplight is None:
        return violations

    if confidence < YELLOW_THRESHOLD and stoplight == "GREEN":
        violations.append(Violation(
            idx, "STOPLIGHT",
            f"GREEN assigned with confidence {confidence} (below YELLOW threshold {YELLOW_THRESHOLD})",
            summary,
        ))

    if confidence < YELLOW_THRESHOLD and stoplight == "YELLOW":
        violations.append(Violation(
            idx, "STOPLIGHT",
            f"YELLOW assigned with confidence {confidence} (below YELLOW threshold {YELLOW_THRESHOLD}; should be RED)",
            summary,
        ))

    return violations


def _check_no_silent_commit(idx: int, event: dict[str, Any]) -> list[Violation]:
    """INVARIANT-2: No action committed without confirmed status."""
    violations = []
    summary = _event_summary(event)

    committed = event.get("committed", False)
    confirmed = event.get("confirmed", False)

    if committed and not confirmed:
        violations.append(Violation(
            idx, "INVARIANT-2",
            "Action committed without confirmed status",
            summary,
        ))

    return violations


def _check_red_terminal(idx: int, event: dict[str, Any]) -> list[Violation]:
    """INVARIANT-3: RED is terminal — no promotion from RED."""
    violations = []
    summary = _event_summary(event)

    stoplight = event.get("stoplight")
    promoted_from = event.get("promoted_from")

    if promoted_from == "RED":
        violations.append(Violation(
            idx, "INVARIANT-3",
            f"Promoted from RED to {stoplight} — RED is terminal",
            summary,
        ))

    return violations


def _check_provenance_tags(idx: int, event: dict[str, Any]) -> list[Violation]:
    """Check that voice-derived intents carry provenance tags."""
    violations = []
    summary = _event_summary(event)

    is_voice = event.get("source") == "voice"
    tags = set(event.get("provenance_tags", []))

    if is_voice and "[VOICE]" not in tags:
        violations.append(Violation(
            idx, "PROVENANCE",
            "Voice-derived intent missing [VOICE] provenance tag",
            summary,
        ))

    # Check for unknown tags
    for tag in tags:
        if tag not in REQUIRED_PROVENANCE_TAGS:
            violations.append(Violation(
                idx, "PROVENANCE",
                f"Unknown provenance tag: {tag!r}",
                summary,
            ))

    return violations


def _check_forbidden_resolution(idx: int, event: dict[str, Any]) -> list[Violation]:
    """Check that no forbidden resolution methods were used."""
    violations = []
    summary = _event_summary(event)

    method = event.get("resolution_method")
    if method and method in FORBIDDEN_RESOLUTION_METHODS:
        violations.append(Violation(
            idx, "NO-PROBABILISTIC",
            f"Forbidden resolution method used: {method!r}",
            summary,
        ))

    return violations


def _check_clarification_budget(idx: int, event: dict[str, Any]) -> list[Violation]:
    """Check that clarification budget was not exceeded."""
    violations = []
    summary = _event_summary(event)

    clarification_count = event.get("clarification_count", 0)
    escalated_to_menu = event.get("escalated_to_menu", False)

    if clarification_count > MAX_CLARIFICATIONS and not escalated_to_menu:
        violations.append(Violation(
            idx, "BUDGET",
            f"Clarification count {clarification_count} exceeds MAX_CLARIFICATIONS={MAX_CLARIFICATIONS} without menu escalation",
            summary,
        ))

    return violations


def _check_stale_transcript(idx: int, event: dict[str, Any]) -> list[Violation]:
    """Check that stale transcripts are not processed."""
    violations = []
    summary = _event_summary(event)

    delay = event.get("speech_to_transcript_delay_s", 0)
    stoplight = event.get("stoplight")
    committed = event.get("committed", False)

    if delay > STALE_THRESHOLD_S and (stoplight == "GREEN" or committed):
        violations.append(Violation(
            idx, "FC-TIMING-04",
            f"Stale transcript ({delay}s delay) processed as valid input",
            summary,
        ))

    return violations


POLICY_CHECKS = [
    _check_stoplight_classification,
    _check_confidence_thresholds,
    _check_no_silent_commit,
    _check_red_terminal,
    _check_provenance_tags,
    _check_forbidden_resolution,
    _check_clarification_budget,
    _check_stale_transcript,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _event_summary(event: dict[str, Any]) -> str:
    """Create a concise summary of an event for violation reports."""
    transcript = event.get("transcript", "<no transcript>")
    confidence = event.get("asr_confidence", "?")
    stoplight = event.get("stoplight", "?")
    return f"transcript={transcript!r}, confidence={confidence}, stoplight={stoplight}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_unknown_policy(events: list[dict[str, Any]]) -> list[Violation]:
    """Check a list of voice interaction events against the unknown handling policy.

    Args:
        events: List of event dictionaries (see module docstring for schema).

    Returns:
        List of Violation objects. Empty list means compliant.
    """
    violations: list[Violation] = []
    for i, event in enumerate(events, start=1):
        for check_fn in POLICY_CHECKS:
            violations.extend(check_fn(i, event))
    return violations


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Run policy check on a JSONL event file or stdin."""
    if len(sys.argv) < 2:
        print("Usage: check_unknown_handling.py <events.jsonl | ->", file=sys.stderr)
        return 2

    source = sys.argv[1]
    if source == "-":
        lines = sys.stdin.readlines()
    else:
        path = Path(source)
        if not path.exists():
            print(f"File not found: {source}", file=sys.stderr)
            return 2
        lines = path.read_text(encoding="utf-8").splitlines()

    events: list[dict[str, Any]] = []
    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"Line {i}: Invalid JSON: {e}", file=sys.stderr)
            return 2

    violations = check_unknown_policy(events)

    if not violations:
        print(f"PASS: {len(events)} events checked, 0 violations.")
        return 0

    print(f"FAIL: {len(violations)} violation(s) in {len(events)} events.\n")
    for v in violations:
        print(v)
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
