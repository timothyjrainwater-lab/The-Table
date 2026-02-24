# DEBRIEF: WO-ENGINE-BARDIC-DURATION-001

**From:** Builder (Sonnet 4.6)
**To:** PM (Slate), via PO (Thunder)
**Date:** 2026-02-24
**Lifecycle:** COMPLETE
**WO:** WO-ENGINE-BARDIC-DURATION-001
**Result:** COMPLETED — ENGINE-BARDIC-DURATION 10/10, ENGINE-BARDIC-MUSIC 10/10 regression clean. 20/20 total.

---

## Pass 1 — Full Context Dump

### What Was Done

Closed FINDING-BARDIC-DURATION-001 LOW. Inspire Courage now auto-ends when the bard becomes incapacitated (dead, unconscious, deafened, or leaves world_state). A dead bard no longer buffs allies indefinitely.

**Latent bug also fixed (predates this WO):** `tick_inspire_courage()` was only rebuilding WorldState on expiry. The round decrement was silently discarded every tick when no entity expired. This was invisible until tests covered the non-expiry path — BM-09 only exercised the last-round expiry case (which always hits the expiry branch), so the decrement ghost went undetected. Fixed with `any_mutated` pattern. Both the incapacitation failure mode and the decrement ghost are now covered by gate tests.

---

### Files Modified

**`aidm/schemas/entity_fields.py`** (+1 constant)
- `INSPIRE_COURAGE_BARD_ID = "inspire_courage_bard_id"` — str field, set on each buffed entity at activation, cleared on expiry/interruption

**`aidm/core/bardic_music_resolver.py`** (~30 lines net)
- `_bard_is_incapacitated(bard_id, entities)` — private helper; checks `HP_CURRENT <= 0`, `EF.DYING`, `"unconscious"/"UNCONSCIOUS"` condition, `"deafened"/"DEAFENED"` condition; returns True if bard not found in entities (scene exit)
- `resolve_bardic_music()` — sets `EF.INSPIRE_COURAGE_BARD_ID = intent.actor_id` on each buffed entity (including bard self-buff)
- `tick_inspire_courage()` — added incapacitation check before decrement; `any_mutated` pattern for WorldState rebuild (fixes latent decrement-ghost bug); emits `inspire_courage_interrupted` event grouped by bard_id on interruption; clears `INSPIRE_COURAGE_BARD_ID` on expiry and interruption

### Files Created

**`tests/test_engine_bardic_duration_gate.py`** — 10 tests (BD-01 through BD-10)

| Test | Result |
|------|--------|
| BD-01 | Normal duration: decrements each round, `inspire_courage_end` at round 8 |
| BD-02 | Bard dies → `inspire_courage_interrupted` on next tick, allies lose bonus |
| BD-03 | Bard UNCONSCIOUS → `inspire_courage_interrupted` on next tick |
| BD-04 | Bard DEAFENED → `inspire_courage_interrupted` on next tick |
| BD-05 | Bard leaves world_state → `inspire_courage_interrupted` (bard not found) |
| BD-06 | Two bards: bard A dies, bard B effect continues — isolation confirmed |
| BD-07 | `INSPIRE_COURAGE_BARD_ID` set correctly on all ally targets at activation |
| BD-08 | After interruption: `ACTIVE=False`, `BONUS=0`, `BARD_ID=""` on all affected entities |
| BD-09 | Bard at exactly 0 HP (disabled) → interrupted |
| BD-10 | Regression: ENGINE-BARDIC-MUSIC 10/10 unchanged |

**`play_loop.py`** — NOT touched. Tick was already wired at line 2876.

---

### Key Findings

**Latent decrement-ghost bug (pre-existing):** `tick_inspire_courage()` only committed WorldState mutations on expiry. Round decrements were computed but discarded when no entity expired that tick. Fixed by `any_mutated` flag — WorldState rebuilt whenever any entity was mutated, not only on expiry. This predates WO-ENGINE-BARDIC-DURATION-001; the WO surfaced it by writing tests for non-expiry ticks.

**Casing on conditions:** Condition dict keys are not normalized — `"deafened"` and `"DEAFENED"` both appear depending on which subsystem applied the condition. The helper checks both. This is a systemic pattern — future condition checks should do the same.

---

### Open Findings

| ID | Severity | Description |
|----|----------|-------------|
| (none new) | — | Latent decrement-ghost was pre-existing, now fixed and gated. No new gaps. |

---

## Pass 2 — PM Summary

**WO-ENGINE-BARDIC-DURATION-001: COMPLETED.** ENGINE-BARDIC-DURATION 10/10, ENGINE-BARDIC-MUSIC 10/10 regression clean. 20/20 total. Inspire Courage now auto-ends when bard dies, goes unconscious, goes deafened, or leaves the scene. New EF: `INSPIRE_COURAGE_BARD_ID`. New event: `inspire_courage_interrupted`. Latent pre-existing bug also fixed: round decrements were silently discarded on non-expiry ticks (`any_mutated` pattern now applied). FINDING-BARDIC-DURATION-001 LOW closed.

---

## Pass 3 — Retrospective

### Drift Caught

**any_mutated pattern**: The original `tick_inspire_courage()` only rebuilt WorldState on the expiry branch. This is the same class of bug as a "return early without flushing" error. The fix is idiomatic — track any mutation, rebuild once at end. Future tick functions should adopt this pattern as standard.

**Condition casing inconsistency**: Two subsystems write conditions with different casing. No normalization layer exists. This is a systemic gap — not a blocker, but every future condition check needs to handle both cases defensively. Recommend a PM note for any future conditions WO.

### Pattern Notes

**Non-expiry path test gap**: BM-09 tested the one-round-left expiry case exclusively. The decrement-ghost was invisible because every BM test hit an expiry branch eventually. The lesson: tick functions need tests for both the mid-run decrement path AND the expiry path. BD-01 covers the full 8-round run, which is what exposed the ghost.

**Grouped event emission**: `inspire_courage_interrupted` is emitted once per bard (grouping affected entity IDs in payload), not once per target. This is the right pattern — one logical event per logical cause. Contrast with `inspire_courage_end` which is per-entity. Future interrupt events should follow the grouped pattern when the cause is a single source entity.

### Recommendations

1. **Condition key normalization**: Add a helper `has_condition(entity, name)` that checks both casings. Every future condition check is currently duplicating the `"foo" in conditions or "FOO" in conditions` pattern. Low-cost standardization.
2. **Tick function template**: Establish `any_mutated` as the standard pattern for all tick functions. Audit existing ticks (duration_tracker, dying_resolver) for the same flush gap.
3. **Non-expiry path test requirement**: Add to WO dispatch checklist — tick gate tests must include at least one test for a mid-run tick that does NOT expire the effect.
