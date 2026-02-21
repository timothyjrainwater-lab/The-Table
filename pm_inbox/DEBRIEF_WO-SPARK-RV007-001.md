# DEBRIEF: WO-SPARK-RV007-001 — Forbidden Meta-Game Claims Detection

**Builder:** Claude Opus 4.6
**Date:** 2026-02-22
**Status:** COMPLETE — all 22 gate tests pass, zero regressions (7 pre-existing failures unrelated to this WO)

---

## 0. Scope Accuracy

Delivered exactly what was asked. Added `_check_rv009_forbidden_claims()` with 9 compiled regex patterns (MV-01 through MV-09) and `_check_rv010_rule_citations()` with 4 compiled regex patterns (RC-01 through RC-04) to `aidm/narration/narration_validator.py`. Both rules are severity FAIL, always active, no CallType filter (DD-03), case-insensitive (DD-04), and report all matches without early break (DD-05). Fixed RV-004 underscore normalization (FINDING-HOOLIGAN-01) by adding `.replace("_", " ")` before keyword lookup in both condition_applied and condition_removed paths. Wired both rules into `validate()` P0 section after RV-005. Updated module docstring rule inventory. Created `tests/test_forbidden_claims_p.py` with 22 tests across 18 gate classes (P-01 through P-18, with P-14 and P-16 having extra sub-tests). Converted Anvil's FUZZ-01, FUZZ-02, and FUZZ-03 into permanent fixtures (P-01, P-02, P-03). No deviations from the dispatch.

## 1. Discovery Log

All 9 MV patterns compile and match their target strings with no false positives on clean prose. The key design insight is that all patterns require a digit adjacent to a mechanics keyword — "damage" alone does not match MV-01, only "\d+ damage" does. This is why "minor damage on Kael's shield" passes clean (verified in P-14 sub-test).

MV-08 (`\b\d+\s*(?:feet|ft\.?|squares?)\s+(?:of\s+)?(?:movement|range|reach)\b`) is the most restrictive — it requires both a digit-unit pair AND a mechanics keyword (movement/range/reach). "The arrow flies thirty feet" does NOT match because "thirty" is prose (no `\d+`) and there's no mechanics keyword. "30 feet of movement" matches correctly. The dispatch radar was right to flag this as the most aggressive pattern, but it passed all tests including the false-positive checks.

The RV-004 fix required normalizing at two points: `condition_applied` and `condition_removed`. The `_CONDITION_MENTION_MAP` keys use spaces (e.g., "prone", "grappled"), but engine condition names use underscores (e.g., "mummy_rot"). Without normalization, `_CONDITION_MENTION_MAP.get("mummy_rot")` returns `None` and falls through to `["mummy_rot"]` — which never matches "mummy rot" in the text. The fix normalizes to spaces before the map lookup, so "mummy_rot" becomes "mummy rot" and falls through to `["mummy rot"]` which matches.

## 2. Methodology Challenge

The patterns are specified in markdown tables where `|` is both a table delimiter and regex alternation. The dispatch warned about this explicitly. The implementation uses raw Python strings with standard `|` for alternation. Each pattern was individually verified against its contract example before compilation.

RC-04 in the contract shows `\brules?\s+(as\s+written\|state|say)\b` — note the inconsistent escaping (first pipe escaped, second not). The authoritative regex intent is clear: match "rules as written", "rule states", or "rule say". I used `as\s+written|state|say` with standard alternation.

## 3. Field Manual Entry

**When implementing regex patterns from a markdown specification, watch for pipe characters.** Markdown tables use `|` as column delimiters, so embedded regex alternation `|` is often escaped as `\|` in the spec. When copying to Python, strip the backslash — `\|` in a markdown cell means `|` in the actual regex. Compile each pattern individually and test against the spec's own example strings before wiring into production.

## 4. Builder Radar

- **Trap.** The `validate()` method lowercases the text once (`text_lower = narration_text.lower()`) and passes it to all rules. All MV/RC patterns are compiled with `re.IGNORECASE`. This means the patterns match against already-lowered text with case-insensitive flags — redundant but harmless. If a future builder removes the `text_lower` call (passing raw text), the patterns still work because of `re.IGNORECASE`. If they remove `re.IGNORECASE`, the patterns still work because of `text_lower`. Remove both and it breaks.
- **Drift.** These 13 patterns (9 MV + 4 RC) are copied from Typed Call Contract Section 3.1-3.2. If the contract adds MV-10 or modifies MV-03, the validator must be updated manually. There is no automated sync between the contract and the compiled patterns.
- **Near stop.** MV-04 (`[+-]\d+\s*(to\s+)?(attack|hit)\b`) does not start with `\b` — it uses `[+-]` which is a character class, not a word boundary. This means "+7 to hit" matches mid-word if preceded by text like "foo+7 to hit". In practice this is not a real narration scenario, but a pedantic builder might add `(?<!\w)` before `[+-]` for safety. Left as-is per contract spec.
