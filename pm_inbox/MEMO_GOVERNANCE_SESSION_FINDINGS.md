# MEMO: Governance Session Findings — State of Play After Verification

**From:** Builder (Opus 4.6)
**To:** PM (Aegis)
**Date:** 2026-02-14
**Context:** Full-context review of governance docs, all 9 verification domains, research corpus, dispatch infrastructure, and planning files.

---

## What Was Done This Session

1. **Governance patch committed** (`25542e3`):
   - Created `VERIFICATION_GUIDELINES.md` (verdict decision tree, 8-pattern error taxonomy, research cross-reference requirement, re-verification protocol)
   - Added Section 15 (Context Boundary Protocol) to `AGENT_DEVELOPMENT_GUIDELINES.md`
   - Added `VERIFICATION_GUIDELINES.md` to `AGENT_ONBOARDING_CHECKLIST.md` reading table

2. **Dead link fixed** (`66ede51`):
   - Onboarding checklist referenced `docs/planning/REVISED_PROGRAM_SEQUENCING_2026_02_12.md` — file is actually in `docs/planning/archived/`

3. **Domain C consistency fix** was delegated to another worker session (BUG-C-001/003 reclassification). That commit may already be in the log (`6982005`).

---

## Items Requiring PM Action

### ACTION 1: Resolve 7 AMBIGUOUS Design Decisions (BLOCKING RED BLOCK LIFT)

These are in `docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md`. Each needs a binary choice from the project owner. The PM should present these to Thunder for decision:

| ID | Question | Options |
|----|----------|---------|
| D-AMB-04 | Grappled Dex penalty | 3.5e RAW (no penalty) vs Pathfinder (penalty applied) |
| A-AMB-05 | Cover AC values | SRD 2-tier (+4/+8) vs code's 4-tier (+2/+5) |
| B-AMB-02 | Opposed check ties | Defender wins vs re-roll |
| B-AMB-04 | Disarm weapon modifiers | Include size/weight modifiers vs simplified |
| B-AMB-05 | Overrun charge bonus | Include +2 charge vs omit |
| E-AMB-03 | 5-foot step in difficult terrain | Allow vs prohibit |
| G-AMB-01 | Initiative tiebreak | Total modifier vs Dex only, actor_id vs re-roll |

**Note:** None of these block the fix WOs currently running. They block the formal RED BLOCK lift.

### ACTION 2: Add Research Cross-Reference to Future Verification Dispatches

Gap 3 from `pm_inbox/HANDOFF_GOVERNANCE_PATCH.md` is still open. The dispatch template needs this block added to all future verification and re-verification dispatches:

```
## Required Reading — Research Cross-Reference

**MANDATORY: Before writing any verdict, check these research documents
for documented design decisions that affect this domain:**

- `docs/research/RQ_BOX_001_GEOMETRIC_ENGINE.md`
- `docs/research/findings/PF_DELTA_INDEX.md`
- `docs/research/findings/SKIP_WILLIAMS_DESIGNER_INTENT.md`
- `docs/research/findings/RQ-BOX-002-F_FAQ_MINING_RESULTS.md`
- `docs/research/RQ-BOX-002-A_COMMUNITY_RAW_ARGUMENT_SURVEY.md`
- `VERIFICATION_GUIDELINES.md`
```

This is a PM-side template change, not a builder task.

### ACTION 3: Triage FAQ Mining Findings (Post-RED-BLOCK)

`docs/research/findings/RQ-BOX-002-F_FAQ_MINING_RESULTS.md` contains 25 findings with 23 recommended new silence entries (SIL-011 through SIL-033). Six are Tier 1 (must-resolve-before-combat-ships):

1. **F-0020:** Bonus stacking (ALWAYS frequency, MAJOR)
2. **F-0012:** Mounted action economy (OFTEN, MAJOR)
3. **F-0011:** Lance charge damage multiplication
4. **F-0001:** Cover from creatures (OFTEN, every ranged attack)
5. **F-0025:** 5-ft step in difficult terrain (OFTEN)
6. **F-0015:** Concealment vs critical hits (OFTEN)

None overlap with current fix WOs. These are net-new work items for the next WO batch.

### ACTION 4: SIL-007 House Policy Decision (Low Priority)

PHB says enhancement bonus = +2/+10 scale. DMG says +1/+1 scale. They contradict each other. Two independent research sources converge on PHB being correct:
- Skip Williams (SW-0012): Designer uses PHB numbers in examples
- Community RAW Survey (A-1): Community consensus favors PHB

This needs a house policy ruling. Not blocking anything currently, but will affect equipment bonus calculations when that system is built.

---

## Items NOT Requiring PM Action (Informational)

- **Fix WOs running in parallel session:** 13 WOs covering 30 bugs. Risk of research cross-ref conflict assessed as LOW — fixes revert to SRD behavior, which is the safe default even if a bug later gets reclassified as AMBIGUOUS.
- **PSD update needed:** Formula count is 338 (not 303 as PSD states), test counts need refresh. Should happen when RED BLOCK lifts. Not urgent.
- **Knowledge Synthesis stale:** Dated 2026-02-08, predates verification. Confidence numbers overstated. Low priority — defer until re-verifications complete.
- **Skip Williams findings:** 15+ rulings not yet mapped to verification criteria. Informational debt, not blocking. One finding (sunder mechanics) is relevant to WO-FIX-09 but assessed as low conflict risk.

---

## Recommended PM Rehydration Priority

When the PM opens a new context window, read in this order:

1. This memo (current state summary)
2. `docs/verification/BONE_LAYER_CHECKLIST.md` (verification completion status)
3. `docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md` (the 7 decisions needed)
4. `VERIFICATION_GUIDELINES.md` (new — the process improvements)

That's ~800 lines of reading. Everything else can be referenced on demand.

---

**End of Memo**
