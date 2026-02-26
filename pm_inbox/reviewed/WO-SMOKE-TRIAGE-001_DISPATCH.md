# WO-SMOKE-TRIAGE-001 — Smoke Test Failure Triage (Group 3)

**Issued:** 2026-02-25
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE / QA
**Priority:** MEDIUM (4 possibly-new failures from hooligan smoke test — pre-existing vs regression unknown)
**WO type:** TRIAGE (read-only investigation — no fixes, findings only)
**Gate:** None (triage WO — builder files findings, PM renders verdict)

---

## 1. Target Lock

A hooligan protocol smoke test run on 2026-02-25 produced 39 failures. 35 of these are confirmed pre-existing or frozen-track. 4 are **unclassified** — they were not in the prior pre-existing list of 23 and are not in the frozen track set. The pre-existing count moved from 23 to 44 when Anvil installed Starlette during WO-UI-2D-WIRING-001. It is unknown whether these 4 tests are:
- Pre-existing failures that were newly exposed by Starlette installation enabling collection of previously-skipped tests, OR
- New regressions introduced by recent ENGINE DISPATCH WOs (#8, #9, #10, #11)

**Builder task: read each of the 4 failing tests and the test output, determine pre-existing vs new regression, file findings. No code changes.**

---

## 2. The 4 Unclassified Failures

| # | Test | File |
|---|------|------|
| 1 | `test_aoo_usage_resets_each_round` | `tests/test_aoo_kernel.py` |
| 2 | `test_all_condition_types_have_factories` | `tests/test_conditions_kernel.py` |
| 3 | `TestUIG2ZoneValidation::test_position_update_to_valid_zone_accepted` | `tests/test_ui_gate_g.py` |
| 4 | `TestCanaryStillPasses::test_b_amb_04_in_disarm_source` | `tests/test_weapon_plumbing.py` |

---

## 3. Investigation Plan

For each of the 4 tests, builder will:

### Step 1 — Read the test

Read the test file. Understand what the test checks. Note what source module it imports.

### Step 2 — Run the test with verbose output

```bash
python -m pytest tests/test_aoo_kernel.py::test_aoo_usage_resets_each_round -v --tb=long
python -m pytest tests/test_conditions_kernel.py::test_all_condition_types_have_factories -v --tb=long
python -m pytest "tests/test_ui_gate_g.py::TestUIG2ZoneValidation::test_position_update_to_valid_zone_accepted" -v --tb=long
python -m pytest "tests/test_weapon_plumbing.py::TestCanaryStillPasses::test_b_amb_04_in_disarm_source" -v --tb=long
```

Capture the exact failure output (assert message, traceback).

### Step 3 — Determine classification

For each test, answer:
1. Does the test import anything that was touched by ENGINE DISPATCH #8–11 (WO-ENGINE-NATURAL-ATTACK-001, WO-ENGINE-PLAY-LOOP-ROUTING-001, WO-ENGINE-BARDIC-DURATION-001, WO-ENGINE-WILDSHAPE-DURATION-001, WO-ENGINE-WILDSHAPE-HP-001, WO-UI-2D-WIRING-001)?
2. Is the failure consistent with a known pre-existing condition (e.g., `boundary_law`, `content_id`, `pm_inbox_hygiene` failure patterns)?
3. Does the git log show any recent touch to the tested source files?

Classification options:
- **PRE-EXISTING (COLLECTION-EXPOSED):** Was failing before, newly visible because Starlette install enabled collection.
- **PRE-EXISTING (DORMANT):** Was always failing but not previously tracked in the 23-count list.
- **NEW REGRESSION:** Introduced by a specific recent WO. Name the WO.
- **NEEDS-PM-VERDICT:** Cannot determine from code inspection alone — escalate.

### Step 4 — File findings in debrief

No fixes. Do not modify any source file. Do not modify any test file. Read and report only.

---

## 4. Recent ENGINE DISPATCH reference

For Step 3 cross-reference:

| WO | Commit | Files touched |
|----|--------|---------------|
| WO-ENGINE-NATURAL-ATTACK-001 | ENGINE DISPATCH #9 | `natural_attack_resolver.py`, `play_loop.py`, `entity_fields.py` |
| WO-ENGINE-PLAY-LOOP-ROUTING-001 | ENGINE DISPATCH #9 | `play_loop.py` |
| WO-ENGINE-BARDIC-DURATION-001 | ENGINE DISPATCH #10 | `bardic_music_resolver.py`, `play_loop.py` |
| WO-ENGINE-WILDSHAPE-DURATION-001 | ENGINE DISPATCH #11 | `wild_shape_resolver.py`, `play_loop.py`, `entity_fields.py` |
| WO-ENGINE-WILDSHAPE-HP-001 | ENGINE DISPATCH #11 | `wild_shape_resolver.py`, `entity_fields.py` |
| WO-UI-2D-WIRING-001 | UI DISPATCH | `ws_bridge.py`, `client2d/main.js`, `client2d/orb.js` |

---

## Integration Seams

**Files to read (no edits):**
- `tests/test_aoo_kernel.py`
- `tests/test_conditions_kernel.py`
- `tests/test_ui_gate_g.py`
- `tests/test_weapon_plumbing.py`

**Files NOT touched:**
- All source files — no changes
- All test files — no changes

---

## Assumptions to Validate

1. All 4 tests were present in the repo before this smoke test run — builder confirms via git log.
2. The Starlette install (FIND-WIRING-003) expanded test collection from ~23 to ~44 failures — confirm whether any of these 4 tests were previously skipped due to import errors.
3. Recent ENGINE DISPATCH WOs (#8–11) may have changed `play_loop.py` and `entity_fields.py` — check for coupling.

---

## Preflight

```bash
python scripts/verify_session_start.py
```

---

## Delivery Footer

**Deliverables:**
- [ ] Per-test classification (PRE-EXISTING vs NEW REGRESSION vs NEEDS-PM-VERDICT) for all 4 tests
- [ ] Exact failure output (assert message + short traceback) for each
- [ ] Recommendation: which (if any) require a fix WO

**Gate:** None — triage only
**Regression bar:** No changes to source or tests permitted.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-SMOKE-TRIAGE-001.md` on completion.

**Three-pass format:**
- Pass 1: per-test findings — classification, failure text, rationale
- Pass 2: PM summary ≤100 words
- Pass 3: retrospective — patterns, recommendations for fix WOs (if any)

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
