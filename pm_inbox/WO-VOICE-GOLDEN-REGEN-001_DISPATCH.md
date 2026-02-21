# WO-VOICE-GOLDEN-REGEN-001 — Regenerate Golden Transcript Baselines

**Type:** CODE
**Priority:** BURST-001 Tier 3.4
**Depends on:** WO-VOICE-GRAMMAR-IMPL-001 (3.1+3.2) AND WO-VOICE-ROUTING-IMPL-001 (3.3)
**Blocked by:** Both preceding WOs must land — this WO regenerates baselines AFTER all formatting changes are complete.

---

## Target Lock

Regenerate golden transcript test baselines so CC-15 (golden transcript stable for non-Spark output lines) passes with the new grammar-compliant output format.

## Binary Decisions

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | Which baselines need regen? | All smoke test scenarios that capture CLI output | CC-15 |
| 2 | Are Spark output lines pinned? | No — only non-Spark lines are golden. Spark output varies by model. | CC-15 scope |
| 3 | Do we need new scenarios? | No — existing scenarios with new expected output. | Scope control |

## Contract Spec

**CC-15 (from Voice-First Reliability Playbook Section 5.2):** Golden transcript stable for non-Spark output lines.

After WO-VOICE-GRAMMAR-IMPL-001 and WO-VOICE-ROUTING-IMPL-001 land, the CLI output format will have changed:
- Turn banners: `--- Name's Turn ---` → `Name's Turn`
- Alerts: `*** Name is DEFEATED! ***` → `Name is DEFEATED.`
- Mechanical output: unprefixed → `[RESOLVE]` prefixed
- System output: unprefixed → `[AIDM]` prefixed
- Prompt: `{name}> ` → `Your action?`

All existing golden transcripts that match against CLI output will need baseline regeneration.

## Implementation Plan

1. Identify all test files that use golden transcript comparison (expected output strings)
2. Run all smoke scenarios, capture new output
3. Update expected output in test fixtures to match grammar-compliant format
4. Verify all Gate J (27), Gate Q, and Gate R tests pass
5. Verify full suite passes with updated baselines
6. Document which baselines changed and why

## Gate Specification

No new gate — this WO updates existing test baselines. Pass criteria:

| Check | Assertion |
|-------|-----------|
| All existing gates pass | J:27, Q (from 3.1+3.2), R (from 3.3) |
| Full suite regression | 6,234+ baseline, 0 new failures |
| Smoke scenarios pass | All smoke stages with updated baselines |
| CC-15 compliance | Golden transcript matches grammar-compliant output |

## Integration Seams

- `tests/test_smoke_*.py` — smoke scenario expected output
- `scripts/smoke_scenarios/*.py` — scenario definitions that check output
- Any fixture files with hardcoded CLI output strings
- Determinism gate baselines (seed=42) — output format changed but values unchanged

## Assumptions to Validate

1. Smoke test scenarios use string matching (not regex) for output validation — verify whether the matching is exact or pattern-based. If pattern-based, fewer baselines need updating.
2. Determinism tests compare output hashes — if hashes include display formatting, they need regen. If they only hash game state, no change needed.

## Preflight

```bash
python scripts/preflight_canary.py
python -m pytest tests/ -x --timeout=30
```

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order ready. Golden transcript regeneration. Awaiting Thunder."
```

## Delivery Footer

**Commit requirement:** After all tests pass, commit changes with a descriptive message referencing this WO ID. Do not leave accepted changes uncommitted.
**Debrief format:** CODE — 500 words max, 5 sections + Radar (3 lines).
**Radar bank:** (1) Which baselines broke and why, (2) Any test that needed structural change beyond baseline update, (3) CC-15 compliance status.
