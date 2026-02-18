# Debrief: WO-SMOKE-FUZZER — Generative Smoke Test Infrastructure

**From:** Builder
**Date:** 2026-02-18
**Lifecycle:** COMPLETE
**Commit:** `330760b`

---

## Scope Accuracy

WO scope was accurate — the modular structure and fuzzer were partially built by a previous session, requiring a critical bug fix (FrozenWorldStateView.from_world_state does not exist) and validation that the full pipeline works end-to-end.

## Discovery Log

- **Checked existing state first.** Found `scripts/smoke_scenarios/` already existed with `common.py`, `manual.py`, `fuzzer.py`, and `tests/test_smoke_fuzzer.py` from a previous session. The refactored `smoke_test.py` was also already in place.
- **Found critical bug in fuzzer.py line 216:** `FrozenWorldStateView.from_world_state(world_state)` — this classmethod does not exist. The constructor is `FrozenWorldStateView(state)`. Also, it was passing the pre-execution `world_state` instead of `turn_result.world_state`.
- **Found secondary bug in fuzzer.py line 272:** `except KeyError` handler referenced `template` variable that may not be assigned if the KeyError came from `get_template`.
- **Fixed both bugs.** Also added `event_type` and `citations` keys to the event dict construction to match what `assemble_narrative_brief` expects.
- **Ran fuzzer with 20 scenarios (seed=42):** 19 PASS, 1 FINDING.
- **Finding: Cone of Cold damage_type is None.** Spell has `damage_dice=10d6` but `NarrativeBrief.damage_type` is not populated. This is an actual integration gap in the NarrativeBrief assembler for AoE damage spells — the fuzzer found something hand-authored scenarios missed.
- **Verified 44/44 manual stages still pass.** No regressions.
- **Meta-tests: 2/2 PASS** (completion + reproducibility).
- **Full test suite: 5794 passed, 16 failed (all pre-existing).** Failures are TTS/immersion dependencies and pm_inbox hygiene on unrelated files.

## Methodology Challenge

The WO specified "refactor first, then build fuzzer" as a binary decision. In reality, a previous session had already done the refactoring but left the fuzzer broken (would crash on first NarrativeBrief assembly). The gap between "files exist" and "files work" is the debrief integrity boundary in action — the previous session may have reported the refactoring as complete without running the fuzzer end-to-end. The PM should verify that previous-session artifacts actually run before marking WOs complete.

## Field Manual Entry

**#12 — Verify Inherited Artifacts.** When a session picks up files written by a previous session, run the code before assuming it works. Check for constructor signatures, classmethod existence, and exception handler variable scoping. The gap between "code exists" and "code runs" is a silent failure mode that wastes context window on debugging instead of building.
