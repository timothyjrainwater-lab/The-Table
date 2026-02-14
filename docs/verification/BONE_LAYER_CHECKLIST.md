# Bone-Layer Verification Checklist

**Tracks:** BONE_LAYER_VERIFICATION_PLAN.md execution progress
**Updated by:** Any agent executing a verification iteration
**Format:** Update counts after each domain iteration, commit with the iteration

---

## Verification Status

| Domain | Description | Files | Formulas | Verified | Correct | Wrong | Ambiguous | Uncited | Status |
|--------|-------------|-------|----------|----------|---------|-------|-----------|---------|--------|
| D | Conditions & Modifiers | 2 | 57 | 57 | 38 | 8 | 5 | 6 | COMPLETE |
| A | Attack Resolution | 9 | 57 | 57 | 42 | 5 | 6 | 4 | COMPLETE |
| B | Combat Maneuvers | 2 | 27 | 27 | 18 | 5 | 3 | 1 | COMPLETE |
| C | Saves & Spells | 2 | 21 | 21 | 15 | 1 | 3 | 2 | COMPLETE |
| G | Initiative & Turn | 3 | 10 | 10 | 6 | 2 | 2 | 0 | COMPLETE |
| E | Movement & Terrain | 5 | 34 | 34 | 24 | 3 | 3 | 4 | COMPLETE |
| F | Char Progression | 5 | 77 | 77 | 68 | 5 | 3 | 1 | COMPLETE |
| H | Skill System | 1 | 6 | 6 | 4 | 0 | 1 | 1 | COMPLETE |
| I | Geometry & Size | 10 | 49 | 49 | 40 | 1 | 2 | 6 | COMPLETE |
| **TOTAL** | | **39** | **338** | **338** | **255** | **30** | **28** | **25** | **ALL DOMAINS COMPLETE** |

---

## Completion Gate

- [x] All 9 domains show status COMPLETE
- [x] All WRONG verdicts have corresponding fix WOs → `docs/verification/WRONG_VERDICTS_MASTER.md` (13 fix WOs covering 32 bugs)
- [x] All AMBIGUOUS verdicts have documented design decisions → `docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md` (28 verdicts, all resolved)
- [x] Operator has reviewed and approved AMBIGUOUS decisions (7 decisions: 4 KEEP, 3 FIX-SRD)
- [x] 3 FIX-SRD micro-WOs dispatched and committed (f517592 — B-AMB-02/H-AMB-01, B-AMB-04, E-AMB-03)
- [x] PSD updated to reflect verification completion (0b2b46e)
- [x] Pre-gate-lift inspection PASSED — all 7 checks (WO-PREFLIGHT-001)
- [ ] RED block lifted by Operator

---

## Iteration Log

| Date | Agent | Domain | Formulas Verified | Wrong Found | Commit |
|------|-------|--------|-------------------|-------------|--------|
| 2026-02-14 | Builder (Opus 4.6) | I | 49 | 1 | 86efc18 |
| 2026-02-14 | Builder (Opus 4.6) | G | 10 | 2 | (pending commit) |
| 2026-02-14 | Builder (Opus 4.6) | D | 57 | 8 | (pending commit) |
| 2026-02-14 | Builder (Opus 4.6) | B | 27 | 5 | (pending commit) |
| 2026-02-14 | Builder (Opus 4.6) | H | 6 | 0 | (pending commit) |
| 2026-02-14 | Builder (Opus 4.6) | H (re-verify) | 6 | 0 | (pending commit) |
| 2026-02-14 | Builder (Opus 4.6) | E | 34 | 3 | (pending commit) |
| 2026-02-14 | Builder (Opus 4.6) | A | 53 | 7 | (pending commit) |
| 2026-02-14 | Builder (Opus 4.6) | C | 21 | 3 | (pending commit) |
| 2026-02-14 | Builder (Opus 4.6) | D (re-verify) | 57 | 8 | Grappled 3.5e/PF divergence found, verdict CORRECT→AMBIGUOUS |
| 2026-02-14 | Builder (Opus 4.6) | F | 77 | 5 | (pending commit) |
| 2026-02-14 | Builder (Opus 4.6) | A (re-verify) | 53 | 5 | BUG-10 cover values WRONG→AMBIGUOUS (RQ-BOX-001 documented design decision) |
| 2026-02-14 | PM (Opus 4.6) | ALL | — | — | Aggregated 32 WRONG into 13 fix WOs + 26 AMBIGUOUS into decision log |

---

## Known Bugs Pre-Verification

These bugs were found during the Action Economy Audit (pre-verification). They will be re-confirmed during Domain A and D verification:

| Bug ID | Domain | Description | Pre-Verification Status |
|--------|--------|-------------|------------------------|
| BUG-1 | A | Two-handed STR 1.5x not applied | Known WRONG |
| BUG-2 | A | Full attack doesn't stop on target death | Known WRONG |
| BUG-3 | D→A | Prone AC not melee/ranged differentiated | Known WRONG |
| BUG-4 | D→A | Helpless AC not melee/ranged differentiated | Known WRONG |