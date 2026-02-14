# Bone-Layer Verification Checklist

**Tracks:** BONE_LAYER_VERIFICATION_PLAN.md execution progress
**Updated by:** Any agent executing a verification iteration
**Format:** Update counts after each domain iteration, commit with the iteration

---

## Verification Status

| Domain | Description | Files | Formulas | Verified | Correct | Wrong | Ambiguous | Uncited | Status |
|--------|-------------|-------|----------|----------|---------|-------|-----------|---------|--------|
| D | Conditions & Modifiers | 2 | 57 | 57 | 38 | 8 | 5 | 6 | COMPLETE |
| A | Attack Resolution | 9 | 53 | 0 | 0 | 0 | 0 | 0 | NOT STARTED |
| B | Combat Maneuvers | 2 | 27 | 0 | 0 | 0 | 0 | 0 | NOT STARTED |
| C | Saves & Spells | 2 | 21 | 0 | 0 | 0 | 0 | 0 | NOT STARTED |
| G | Initiative & Turn | 3 | 10 | 10 | 6 | 2 | 2 | 0 | COMPLETE |
| E | Movement & Terrain | 5 | 34 | 0 | 0 | 0 | 0 | 0 | NOT STARTED |
| F | Char Progression | 4 | 77 | 0 | 0 | 0 | 0 | 0 | NOT STARTED |
| H | Skill System | 1 | 6 | 0 | 0 | 0 | 0 | 0 | NOT STARTED |
| I | Geometry & Size | 10 | 49 | 49 | 40 | 1 | 2 | 6 | COMPLETE |
| **TOTAL** | | **38** | **334** | **116** | **85** | **11** | **8** | **12** | **IN PROGRESS** |

---

## Completion Gate

- [ ] All 9 domains show status COMPLETE
- [ ] All WRONG verdicts have corresponding fix WOs
- [ ] All AMBIGUOUS verdicts have documented design decisions
- [ ] Operator has reviewed and approved AMBIGUOUS decisions
- [ ] PSD updated to reflect verification completion
- [ ] RED block lifted by Operator

---

## Iteration Log

| Date | Agent | Domain | Formulas Verified | Wrong Found | Commit |
|------|-------|--------|-------------------|-------------|--------|
| 2026-02-14 | Builder (Opus 4.6) | I | 49 | 1 | (pending commit) |
| 2026-02-14 | Builder (Opus 4.6) | G | 10 | 2 | (pending commit) |

---

## Known Bugs Pre-Verification

These bugs were found during the Action Economy Audit (pre-verification). They will be re-confirmed during Domain A and D verification:

| Bug ID | Domain | Description | Pre-Verification Status |
|--------|--------|-------------|------------------------|
| BUG-1 | A | Two-handed STR 1.5x not applied | Known WRONG |
| BUG-2 | A | Full attack doesn't stop on target death | Known WRONG |
| BUG-3 | D→A | Prone AC not melee/ranged differentiated | Known WRONG |
| BUG-4 | D→A | Helpless AC not melee/ranged differentiated | Known WRONG |