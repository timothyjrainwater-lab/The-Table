# Action Plan: Post-Fix Phase Stabilization & Forward Path

**Author:** Builder (Opus 4.6)
**Date:** 2026-02-14
**For:** PM review and prioritization
**Lifecycle:** NEW
**Context:** All 13 bone-layer fix WOs are committed. Test suite is GREEN (5,532 passed, 24 skipped, 0 failed). This plan covers what to do next based on findings from the fix phase, codebase health audit, verification coverage audit, and architectural debt analysis.

---

## Current State Summary

| Metric | Value |
|--------|-------|
| Fix WOs dispatched | 13 |
| Fix WOs committed | **13/13 (100%)** |
| Test suite | **5,532 passed**, 24 skipped, 0 failed |
| Warnings | 88 (6 unregistered marker, ~80 deprecation, 2 resource leaks) |
| WRONG verdicts resolved | **30/30 (100%)** |
| AMBIGUOUS verdicts resolved | 21/28 (7 awaiting operator decision) |
| UNCITED formulas | 25 across 7 domains |
| TODO debt | 15 items across 5 files |
| Lazy imports (circular pressure) | 66 across 18 files |

---

## Priority 1: Immediate — Correctness & Hygiene (this week)

### P1-A: Sunder grip multiplier gap

**Effort:** Trivial (< 10 lines)
**Risk:** LOW
**What:** WO-FIX-09 applies flat `attacker_str` to sunder damage at `maneuver_resolver.py:1071` instead of the grip-adjusted value from WO-FIX-01. A greatsword sunder should deal `int(STR * 1.5)` damage, not flat STR.
**Why now:** The grip multiplier was the highest-priority fix in the dispatch (WO-FIX-01). Leaving one code path unpatched creates an inconsistency that will surface when sunder gets used in play.
**Fix:** Apply the same `weapon_grip` → `str_to_damage` branch from `attack_resolver.py:370-378` to sunder damage calculation. Add 1 test.

### P1-B: XP table cross-verification

**Effort:** Low (research, no code if values are correct)
**Risk:** LOW
**What:** The level 11-20 XP table values committed in `b52d8d8` were derived by extending the level 1-10 mathematical pattern. They match the 2 reference points from the verification doc (`(11,-1)=500`, `(11,-2)=450`), but were NOT transcribed from a clean DMG Table 2-6 source. The Vault OCR at `Vault/00-System/Staging/fed77f68501d/pages/0039.txt` is too garbled to use.
**Why now:** If the values are wrong, XP awards for half the level range are incorrect. A 5-minute spot-check against a physical DMG closes this.
**Action:** Operator spot-checks 5+ cells from levels 14-20 against a physical copy of DMG Table 2-6 (p.38). If values match, mark verified. If not, file a micro-WO with the correct values.

### P1-C: Register `narration` pytest marker

**Effort:** Trivial (1 line in `pyproject.toml`)
**Risk:** NONE
**What:** `@pytest.mark.narration` is used 6 times in `test_spark_integration_stress.py` but not registered. With `--strict-markers` enabled (it is), this emits 6 `PytestUnknownMarkWarning` per run.
**Fix:** Add `"narration: Spark narration boundary and integration tests"` to the `markers` list in `pyproject.toml`.

### P1-D: Fix 3 broken `TestPerformance` tests

**Effort:** Low (update test signatures)
**Risk:** LOW
**What:** `test_narration_latency_under_budget`, `test_narration_throughput_10_turns`, and `test_kill_switch_latency_overhead` in `test_spark_integration_stress.py` pass a bare `EngineResult` to `GuardedNarrationService.generate_narration()`, which expects a `NarrationRequest`. They raise `AttributeError: 'EngineResult' object has no attribute 'memory_snapshot'`. Currently masked in the full suite by `@skipif(not _gpu_available())`.
**Why now:** These tests are testing dead code paths. Either update them to the current API or delete them if the scenarios they cover are tested elsewhere.

### P1-E: pm_inbox hygiene

**Effort:** Trivial (file moves)
**Risk:** NONE
**What:** Two stale dispatch files remain in active `pm_inbox/`:
- `WO-BUGFIX-TIER0-001_DISPATCH.md` — superseded by `FIX_WO_DISPATCH_PACKET.md`
- `WO-FIX-12-DESKCHECK.md` — resolved by commit `b52d8d8`
**Fix:** Move both to `pm_inbox/reviewed/`.

---

## Priority 2: Near-Term — Verification Closure (next 1-2 sessions)

### P2-A: Resolve 7 AMBIGUOUS verdicts requiring operator decision

**Effort:** Operator decisions, possibly 1-3 micro-WOs depending on choices
**Risk:** MEDIUM (A-AMB-05 cascades)
**What:** 7 AMBIGUOUS verdicts have blank DECISION fields in `AMBIGUOUS_VERDICTS_DECISION_LOG.md`. The remaining 21 are either auto-resolved (8), PM-recommends-KEEP (12), or already fixed (1).

The 7 requiring operator input:

| ID | Domain | Issue | Cascade Risk |
|----|--------|-------|-------------|
| **A-AMB-05** | Attack | Cover AC: 4-tier graduated vs. SRD 2-tier | **HIGH** — cascades to A-AMB-06 + C-AMB-02 |
| D-AMB-04 | Conditions | Grappled Dex handling: PF -4 vs. 3.5e loses-Dex | Low |
| B-AMB-02 | Maneuvers | Opposed check ties: defender wins vs. re-roll | Low (linked to H-AMB-01) |
| B-AMB-04 | Maneuvers | Disarm missing weapon type modifiers | Low |
| B-AMB-05 | Maneuvers | Overrun charge bonus | Low |
| E-AMB-03 | Movement | 5-foot step in difficult terrain | Low |
| G-AMB-01 | Initiative | Tie-break rule | Low |

**Recommendation:** Start with A-AMB-05 since its decision cascades. If operator chooses KEEP (graduated 4-tier cover), the other two auto-resolve. If FIX-SRD (binary cover), it requires changes to cover resolver, save resolver, and tests.

### P2-B: Domain C verification header update

**Effort:** Trivial (text edit)
**Risk:** NONE
**What:** `DOMAIN_C_VERIFICATION.md` header shows "3 WRONG, 1 AMBIGUOUS" but `WRONG_VERDICTS_MASTER.md` reclassified BUG-C-001 and BUG-C-003 to AMBIGUOUS. Correct counts: 1 WRONG, 3 AMBIGUOUS.
**Fix:** Update the summary table header.

### P2-C: Triage 25 UNCITED formulas

**Effort:** Medium (research pass)
**Risk:** LOW — no code changes expected, just classification
**What:** 25 formulas across 7 domains have no SRD citation. They may be correct (just undocumented), wrong (new bugs), or ambiguous (new design decisions). Largest clusters: Geometry (6), Conditions (6), Attack (4), Movement (4).
**Action:** A focused verification pass to classify each as CORRECT (add citation), WRONG (file bug), or AMBIGUOUS (add to decision log). Could be dispatched as a single WO.

---

## Priority 3: Medium-Term — Test Infrastructure (next 2-4 sessions)

### P3-A: Implement root conftest cleanup hooks

**Effort:** Medium
**Risk:** LOW
**What:** `tests/conftest.py` contains a docstring promising "cross-test cleanup for resources that can leak between test modules (daemon threads, background managers, etc.)" but implements zero fixtures. Evidence of the gap: 2 `ResourceWarning: unclosed file` in `test_intent_bridge_contract_compliance.py`, and the `sys.modules` torch contamination that was just fixed (which a cleanup hook could have prevented).
**Action:** Implement:
1. An autouse session-scoped fixture that snapshots `sys.modules` at session start and restores on teardown
2. Resource leak detection (unclosed files/sockets)
3. Global state reset between test modules for known singletons

### P3-B: Deprecation warning triage

**Effort:** Medium (code changes across ~10 files)
**Risk:** LOW-MEDIUM
**What:** 80 of 88 test warnings are deprecation-related:
- ~48 from `GridPosition`/`GridPoint` in `test_aoo_kernel.py` and `test_mounted_combat_integration.py` (tagged for CP-002, not scheduled)
- ~32 from Pillow `'mode'` parameter in image critique tests (**deadline: 2026-10-15**, 8 months)
- 1 from deprecated `aidm.services.discovery_log` shim
**Action:**
1. Schedule CP-002 (position type unification) or suppress the warnings in tests
2. Fix Pillow `mode=` calls before Pillow 13 drops (October 2026)
3. Update `test_asset_pool_determinism_replay.py` to use `aidm.lens.discovery_log`

### P3-C: `.gitignore` hardening

**Effort:** Trivial
**Risk:** NONE
**What:** Missing patterns for `.env`, `*.egg-info`, `dist/`, `build/`, `venv/`, `.venv/`, `*.log`. No secrets have leaked (`.gitignore` covers `config/user_profile.yaml`), but `.env` files are not protected.
**Fix:** Add standard Python project patterns.

---

## Priority 4: Strategic — Architectural Debt (backlog)

These are systemic issues identified during the audit. They don't block feature work but increase the cost and risk of future changes.

### P4-A: Combat resolver circular import cluster

**Severity:** CRITICAL (architectural)
**What:** 66 lazy imports across 18 files. The combat subsystems (`attack_resolver`, `full_attack_resolver`, `aoo`, `flanking`, `concealment`, `sneak_attack`, `damage_reduction`, `feat_resolver`, `terrain_resolver`, `mounted_combat`) form a dense bidirectional dependency graph. Every new subsystem integration requires new lazy imports.
**Impact:** Slows development, makes refactoring dangerous, obscures actual dependencies.
**Recommendation:** Extract a `CombatContext` or modifier pipeline that subsystems contribute to without importing each other. This is a significant refactor — should be planned as a dedicated milestone, not incremental.

### P4-B: God module decomposition

**What:** `play_loop.py` (1,639 lines) and `maneuver_resolver.py` (1,600 lines) are both at the threshold where cognitive load impedes safe modification.
**Recommendation:**
- Split `maneuver_resolver.py` into per-maneuver modules (`trip.py`, `grapple.py`, etc.) behind the existing dispatcher
- Extract `play_loop.py` sub-orchestrators (combat dispatch, movement dispatch, spell dispatch)

### P4-C: Attack resolver duplication

**What:** `attack_resolver.py` (507 lines) and `full_attack_resolver.py` (707 lines) share 3 identical TODO stubs and parallel code paths for concealment, sneak attack, and damage reduction application. Changes must be made in both files (as seen in WO-FIX-01 and WO-FIX-03).
**Recommendation:** Extract shared attack utility module. The full attack resolver should call the single attack resolver for each individual attack, rather than duplicating the resolution logic.

### P4-D: Weapon system stubs

**What:** 6 of 15 TODOs relate to the weapon/equipment system not being plumbed through resolvers. Hardcoded values: `max_range=100`, `is_ranged=False`, `is_twf=False`. This means ranged/melee detection is broken, weapon range is fake, and TWF detection doesn't work.
**Impact:** All ranged vs. melee differentiation (including the Prone AC fix from WO-FIX-03) depends on `is_ranged` being detected correctly. Currently it's hardcoded `False`, meaning **Prone always applies the melee AC modifier**, never the ranged one. The schema fix is correct but the consumer can't use it yet.
**Recommendation:** This is the highest-impact stub to resolve. Plumbing weapon type through to the attack context would immediately activate several already-implemented rules.

### P4-E: Dead code removal

**What:** `_is_entity_defeated()` at `maneuver_resolver.py:117` has zero callers anywhere in the codebase.
**Fix:** Delete it. Safe, zero-risk.

---

## Priority 5: Informational — No Action Required

### Positive findings

- **Schema layer is clean.** 0 TODOs, 0 FIXMEs, 0 HACKs in `aidm/schemas/*.py`.
- **No deprecated imports in test files.** Test suite is clean on this dimension.
- **PF Delta Index is complete.** 25 Pathfinder deltas documented, cross-referenced to 7 SILs. Ready for operator review when needed.
- **All 30 WRONG verdicts are resolved.** No untracked bugs exist outside the dispatch.
- **Test file count is healthy.** 197 test files, 5,532 tests across 5 directories.

### Items explicitly NOT recommended

- **Do not refactor surrounding code** in the fix WO files. The WO protocol says surgical fixes only. Architectural improvements (P4) should be separate milestones.
- **Do not fix the 3 `TestPerformance` API mismatch tests** by changing the production code. The tests are wrong, not the API.
- **Do not pursue CP-002 (position unification)** as part of post-fix cleanup. It's a feature-level refactor with its own scope.

---

## Recommended Dispatch Sequence

```
Wave 1 (immediate, parallel-safe):
  P1-A  Sunder grip multiplier         — 1 micro-WO
  P1-C  Register narration marker       — 1-line commit
  P1-D  Fix TestPerformance tests       — 1 commit
  P1-E  pm_inbox hygiene               — file moves only

Wave 2 (operator-gated):
  P1-B  XP table spot-check            — operator action, no code
  P2-A  AMBIGUOUS verdict decisions     — operator action, possibly micro-WOs

Wave 3 (builder work, after Wave 2):
  P2-B  Domain C header update          — 1-line commit
  P2-C  UNCITED formula triage          — 1 verification WO
  P3-A  Root conftest cleanup hooks     — 1 WO
  P3-B  Deprecation warning triage      — 1 WO
  P3-C  .gitignore hardening            — 1-line commit

Backlog (milestone-level, not fix-phase scope):
  P4-A  Combat resolver dependency graph
  P4-B  God module decomposition
  P4-C  Attack resolver deduplication
  P4-D  Weapon system stubs (HIGH IMPACT — activates is_ranged detection)
  P4-E  Dead code removal
```

---

## Key Risk: `is_ranged` Hardcoded False (P4-D)

This deserves a callout separate from the backlog. The WO-FIX-03 schema change (Prone/Helpless melee vs. ranged AC differentiation) is correctly implemented in the schema and in the attack resolver consumers. But the attack context currently hardcodes `"is_ranged": False` at `attack_resolver.py:227` and `full_attack_resolver.py:474`. This means:

- **Prone targets always get -4 AC** (melee modifier), never +4 (ranged modifier)
- **Helpless targets always get -4 AC** (melee modifier), never +0 (ranged modifier)
- The fix is architecturally correct but functionally dormant for ranged attacks

This is not a regression (ranged attacks were also incorrect before the fix), but it means the Prone/Helpless AC differentiation won't actually work until weapon type detection is implemented. The PM should decide whether this constitutes a blocking gap or an acceptable known limitation.

---

*End of action plan.*
