# MEMO: Domain A Re-Verification Results + Strategic Observations

**From:** Builder (Opus 4.6)
**To:** PM
**Date:** 2026-02-14
**Re:** WO-VERIFY-A re-verification complete; process findings for remaining domains

---

## What Changed

| Metric | Before | After |
|--------|--------|-------|
| Domain A formulas | 53 | 57 (+4 found unverified) |
| Domain A WRONG | 7 | 5 |
| Domain A AMBIGUOUS | 4 | 6 |
| Domain C WRONG | 3 | 1 (BUG-C-001/003 same root as BUG-10) |
| Domain C AMBIGUOUS | 1 | 3 |
| **Global WRONG** | **34** | **30** |
| **Global AMBIGUOUS** | **24** | **28** |

**Root cause:** BUG-10 (cover values +2/+1, +5/+2) was WRONG but is actually a documented design decision in RQ-BOX-001 Finding 3. Initial verifier didn't have the research corpus in context. Reclassified to AMBIGUOUS across Domains A and C. FIX-WO-05 retired.

---

## Strategic Finding

**The initial verification pass did not cross-reference the research wave.** This is the gap. The PF Delta Index, Skip Williams mining, FAQ mining, and RQ-BOX-001 contain design decisions that look like bugs if you only compare code against raw SRD text. The re-verify caught 4 reclassifications from one domain. The other 7 domains have not had this treatment.

**Estimate:** Of the 30 remaining WRONG verdicts, ~8-10 may be documented design decisions that need reclassification once cross-referenced against research. The genuine bug count is likely 20-22.

---

## Specific Concerns

1. **BUG-F2/F3 (XP table levels 11-20):** Real bug, not a design decision. Computed formula diverges from DMG Table 2-6 silently. Players get wrong XP. High priority fix.

2. **BUG-8/BUG-9 (min damage 0 vs 1):** Trivial fix but exists in 4 locations across 2 files. Fix WO must list all 4 to prevent partial repair.

3. **Formula count keeps growing.** Each re-verify finds unverified formulas in helper functions and gate checks. Initial inventory was ~90% complete. If precision matters, budget for this in remaining re-verify dispatches.

---

## Recommendation for Remaining Re-Verify Dispatches

Add this to each WO preamble:

> **REQUIRED: Before writing verdicts, read these research documents and check for documented design decisions that affect this domain:**
> - `docs/research/RQ_BOX_001_GEOMETRIC_ENGINE.md` (cover, geometry)
> - `docs/research/findings/PF_DELTA_INDEX.md` (PF corrections adopted)
> - `docs/research/findings/SKIP_WILLIAMS_DESIGNER_INTENT.md` (RAW disambiguations)
> - `docs/research/findings/RQ-BOX-002-F_FAQ_MINING_RESULTS.md` (FAQ rulings)
> - `docs/research/RQ-BOX-002-A_COMMUNITY_RAW_ARGUMENT_SURVEY.md` (known contradictions)

This is the difference between rubber-stamping verdicts and catching reclassifications.

---

## Artifacts Updated

- `docs/verification/DOMAIN_A_VERIFICATION.md` — re-verification section appended, 4 new formulas, BUG-10 reclassified
- `docs/verification/WRONG_VERDICTS_MASTER.md` — 34→30, FIX-WO-05 retired, Domain C updated
- `docs/verification/BONE_LAYER_CHECKLIST.md` — all totals updated, iteration log entry added
- Commit: `6f882c4`
