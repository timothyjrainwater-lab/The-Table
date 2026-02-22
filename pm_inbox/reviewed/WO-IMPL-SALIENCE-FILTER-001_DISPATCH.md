# WO-IMPL-SALIENCE-FILTER-001 — Line Salience Filter for TTS

**Type:** CODE
**Priority:** BURST-001 Tier 4.4
**Depends on:** WO-VOICE-GRAMMAR-IMPL-001 (ACCEPTED — line type definitions), WO-VOICE-PAS-PRESETS-001 (ACCEPTED)
**Blocked by:** Nothing — ready to dispatch (parallel with 4.3)
**Lifecycle:** NEW

---

## Target Lock

Build a line-level salience filter that classifies narration output into line types (TURN, RESULT, ALERT, NARRATION, PROMPT, SYSTEM, DETAIL) and strips non-spoken lines (S5 DETAIL, S6 SYSTEM) before passing text to TTS. Currently, `_synthesize_tts()` receives the full narration text including `[RESOLVE]` and `[AIDM]` prefixed lines, which should never be spoken aloud.

This is the last BURST-001 implementation WO before 5.5 (Playtest v1).

## Binary Decisions (all resolved)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | Where does the classifier live? | New production module `aidm/voice/line_classifier.py` | Promotes logic from `scripts/check_cli_grammar.py` |
| 2 | Where does the filter live? | New function `filter_spoken_lines()` in same module | Co-located with classifier |
| 3 | Where is the filter called? | Inside `_synthesize_tts()`, filtering `narration_text` before `_tts.synthesize()` | Single injection point |
| 4 | What about multi-line NARRATION blocks? | Split on `\n`, classify each line, keep spoken lines, rejoin | Line-by-line classification is deterministic |
| 5 | Empty result after filtering? | Return `None` from `_synthesize_tts()` (no audio) | Same behavior as TTS unavailable |

## Contract Spec

**Source:** CLI Grammar Contract (Gate J — line types G-01 through G-07), Voice Grammar tests (Gate R — routing rules), `scripts/check_cli_grammar.py` (reference classifier)

### Line Type Salience Hierarchy

| Salience | Line Type | Spoken? | Prefix/Detection | Persona |
|----------|-----------|---------|-------------------|---------|
| S1 | ALERT | Yes | Regex: `.+ is [A-Z]+\.$` | Arbor |
| S2 | PROMPT | Yes | Exact: `"Your action?"` | Arbor |
| S3 | TURN | Yes | Regex: `[A-Z][A-Za-z .'-]*'s Turn$` | DM |
| S3 | RESULT | Yes | Fallback (short non-prefixed lines) | DM |
| S4 | NARRATION | Yes | Fallback (8+ words/sentence, 1-3 sentences) | DM |
| S5 | DETAIL | No | Prefix: `[RESOLVE]` | — |
| S6 | SYSTEM | No | Prefix: `[AIDM]` or blank line | — |

### New Module: `aidm/voice/line_classifier.py`

Promote classifier from `scripts/check_cli_grammar.py` into production code.

```python
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


def classify_lines(text: str) -> List[Tuple[str, LineType]]:
    """Classify all lines in a multi-line text block.

    Args:
        text: Multi-line narration text.

    Returns:
        List of (line, LineType) tuples.
    """


def filter_spoken_lines(text: str) -> str:
    """Filter text to only spoken lines (S1-S4).

    Removes DETAIL ([RESOLVE]) and SYSTEM ([AIDM]) lines.
    Returns empty string if no spoken lines remain.

    Args:
        text: Multi-line narration text.

    Returns:
        Filtered text with only spoken lines, newline-joined.
    """
```

### Integration Seam: `_synthesize_tts()`

Insert filter before TTS call:

```python
# After pressure modulation (4.3), before TTS:
from aidm.voice.line_classifier import filter_spoken_lines

# Filter non-spoken lines (S5 DETAIL, S6 SYSTEM)
spoken_text = filter_spoken_lines(narration_text)
if not spoken_text.strip():
    return None  # Nothing to speak

# Pass only spoken text to TTS
return self._tts.synthesize(spoken_text, persona=persona)
```

### Important: Return Value

`_synthesize_tts()` already returns `None` when TTS is unavailable. If filtering removes all lines (e.g., a turn that's entirely `[RESOLVE]` lines), returning `None` is the correct behavior — the text still appears in CLI output via `narration_text` in the TurnResult.

### What NOT to Change

- `narration_text` in `TurnResult` is **not filtered** — the full text (including `[RESOLVE]` and `[AIDM]` lines) is still returned for CLI display. The filter only affects what goes to TTS.
- `_generate_narration()` output is unchanged.
- No changes to the CLI Grammar Contract or line type definitions.

## Implementation Plan

1. Create `aidm/voice/line_classifier.py` — promote `classify_line()` from `scripts/check_cli_grammar.py`, add `LineType` enum, `classify_lines()`, `filter_spoken_lines()`
2. Wire `filter_spoken_lines()` into `_synthesize_tts()` before `_tts.synthesize()` call
3. Handle empty-after-filter case (return `None`)
4. Write gate tests (see gate spec below)
5. Run full suite regression

### Out of Scope

- Persona switching based on line type (ALERT→Arbor voice, NARRATION→DM voice) — future WO
- Salience-based priority when TTS budget is exceeded — future WO
- Changes to `scripts/check_cli_grammar.py` (keep both; script is for offline validation)
- Changes to narration output format — that's the grammar contract (ACCEPTED)

## Gate Specification

**New gate:** Gate W (Salience Filter)

| Test ID | Assertion | Type |
|---------|-----------|------|
| W-01 | `classify_line("[AIDM] System message")` returns SYSTEM | classifier |
| W-02 | `classify_line("[RESOLVE] 1d20+5 = 18 vs AC 15: hit")` returns DETAIL | classifier |
| W-03 | `classify_line("Your action?")` returns PROMPT | classifier |
| W-04 | `classify_line("Bramble's Turn")` returns TURN | classifier |
| W-05 | `classify_line("Bramble is PRONE.")` returns ALERT | classifier |
| W-06 | `classify_line("")` returns SYSTEM (blank = non-spoken) | classifier |
| W-07 | `classify_line("The orc staggers back, blood streaming from the wound.")` returns NARRATION | classifier |
| W-08 | `classify_line("Hit.")` returns RESULT (short fallback) | classifier |
| W-09 | `filter_spoken_lines("[AIDM] init\nBramble's Turn\n[RESOLVE] 1d20=15\nThe blade strikes true.")` returns `"Bramble's Turn\nThe blade strikes true."` | filter |
| W-10 | `filter_spoken_lines("[AIDM] only system\n[RESOLVE] only detail")` returns `""` | empty filter |
| W-11 | `filter_spoken_lines("Your action?")` returns `"Your action?"` (prompt preserved) | identity |
| W-12 | `LineType` enum has exactly 7 members | completeness |
| W-13 | `SPOKEN_TYPES` has exactly 5 members (ALERT, PROMPT, TURN, RESULT, NARRATION) | set check |
| W-14 | `classify_lines()` returns correct list of (line, LineType) tuples for mixed input | integration |
| W-15 | Full suite regression | regression |

**Expected test count:** 15 (14 functional + regression run).

## Integration Seams

- `aidm/voice/line_classifier.py` — NEW file (classifier + filter)
- `aidm/runtime/session_orchestrator.py:1057-1061` — Insert `filter_spoken_lines()` call between preset/pressure modulation and TTS synthesis

## Files to Read

1. `scripts/check_cli_grammar.py` — Reference classifier (promote to production)
2. `tests/test_grammar_gate_j.py` — LINE_TYPES dict, classify_line() test patterns
3. `tests/test_grammar_gate_r.py` — `_spoken_lines()` helper showing existing filter pattern
4. `aidm/runtime/session_orchestrator.py` — `_synthesize_tts()` integration point

## Preflight

```bash
python scripts/preflight_canary.py
python -m pytest tests/test_grammar_gate_j.py tests/test_grammar_gate_r.py -v
python -m pytest tests/ -x --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py
```

## Delivery Footer

**Commit requirement:** After all tests pass, commit changes with a descriptive message referencing this WO ID.
**Debrief format:** CODE — 500 words max, 5 sections + Radar (3 lines).
**Radar bank:** (1) Anything that broke unexpectedly, (2) Anything that was harder than expected, (3) Anything the next WO should know.
