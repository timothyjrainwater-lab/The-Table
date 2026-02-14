# HANDOFF: Governance Patch — Context Boundary, Verification, & Research Cross-Reference

**From:** Builder (Opus 4.6)
**To:** Next builder agent
**Date:** 2026-02-14
**Status:** READY TO EXECUTE — no dependencies on other sessions
**Lifecycle:** NEW

---

## Situation

The bone-layer verification (338 formulas across 9 domains) and the Domain A re-verification revealed four process gaps in the project's governance framework. These are not code bugs — they are documentation and protocol gaps that caused verification errors and will cause more if unfixed.

The PM has reviewed and approved this analysis. This handoff contains the executable steps.

---

## Uncommitted Work (DO FIRST)

There is ONE uncommitted edit in the working tree:

**File:** `docs/verification/DOMAIN_C_VERIFICATION.md`
**Change:** BUG-C-001 and BUG-C-003 reclassified from SEVERITY: WRONG to SEVERITY: AMBIGUOUS. Domain Summary updated from "3 WRONG / 1 AMBIGUOUS" to "1 WRONG / 3 AMBIGUOUS". Section headers updated with "(RECLASSIFIED → AMBIGUOUS)".
**Why:** The checklist and WRONG_VERDICTS_MASTER were already updated in commit `6f882c4`, but this file was missed. This commit closes that consistency gap.

**Action:**
1. Run `git diff docs/verification/DOMAIN_C_VERIFICATION.md` to verify the edit looks correct
2. Commit: `verify: Domain C — BUG-C-001/003 reclassified AMBIGUOUS (consistency with checklist)`
3. Verify `pm_inbox/MEMO_REVERIFY_A_FINDINGS.md` is also staged (untracked file from prior session)

---

## Gap 1: Verification Guidelines Document (NEW FILE)

**Create:** `VERIFICATION_GUIDELINES.md` (root level, alongside AGENT_DEVELOPMENT_GUIDELINES.md)

This document captures verification-specific pitfalls discovered during the bone-layer verification. It is the verification equivalent of AGENT_DEVELOPMENT_GUIDELINES.md (which covers coding pitfalls).

### Required Contents

**Section 1: Verdict Decision Tree**

```
Code matches SRD exactly?
├── Yes → CORRECT
├── No → Is there a documented design decision in the research corpus?
│   ├── Yes → AMBIGUOUS (cite the research doc + finding ID)
│   └── No → Is the SRD itself ambiguous or silent on this point?
│       ├── Yes → AMBIGUOUS (cite the ambiguity)
│       └── No → WRONG (assign BUG-ID, file in WRONG_VERDICTS_MASTER)
└── No specific SRD citation exists for this formula?
    └── UNCITED (standard arithmetic, universal rule, no SRD page needed)
```

**Section 2: Required Research Cross-Reference**

Before writing any WRONG verdict, search these documents for keywords related to the formula being verified:

- `docs/research/RQ_BOX_001_GEOMETRIC_ENGINE.md` (cover, geometry, LOS/LOE)
- `docs/research/findings/PF_DELTA_INDEX.md` (Pathfinder corrections adopted as design decisions)
- `docs/research/findings/SKIP_WILLIAMS_DESIGNER_INTENT.md` (RAW disambiguations)
- `docs/research/findings/RQ-BOX-002-F_FAQ_MINING_RESULTS.md` (FAQ rulings)
- `docs/research/RQ-BOX-002-A_COMMUNITY_RAW_ARGUMENT_SURVEY.md` (known SRD contradictions)

If the code behavior matches a documented design decision, classify as AMBIGUOUS with a DESIGN REFERENCE citation, not WRONG.

**Evidence:** Domain A re-verification found 4 reclassifications (WRONG→AMBIGUOUS) from one domain because the initial verifier didn't have the research corpus in context. BUG-10 (cover values) was the primary case — documented in RQ-BOX-001 Finding 3.

**Section 3: Common Verification Error Patterns (Taxonomy)**

| Pattern | Description | Example |
|---------|-------------|---------|
| **Research Cross-Ref Miss** | Code diverges from SRD but matches a documented design decision. Flagged WRONG when it should be AMBIGUOUS. | BUG-10: cover values +2/+1 half, +5/+2 three-quarters. Design decision in RQ-BOX-001 Finding 3. |
| **SRD Table Transcription Error** | A formula or lookup table was coded by formula approximation instead of hardcoding the source table. Works for some rows, diverges for others. | BUG-F2/F3: XP table levels 11-20 computed by formula instead of DMG Table 2-6 values. |
| **Sign/Direction Inversion** | A boolean condition or comparison operator is backwards. One-character fix, high impact. | E-BUG-01: soft cover `is_melee` should be `not is_melee`. |
| **Incomplete Enumeration** | A lookup table or constant set is missing entries. Works for common cases, fails for edge cases. | I-GEOM-291: SIZE_ORDER missing Fine, Diminutive, Colossal. |
| **Modifier Not Differentiated** | A modifier is applied as a flat value when the SRD specifies different values for different contexts (melee vs ranged, etc.). | BUG-3/4: Prone/Helpless AC modifier is flat -4 instead of -4 melee / +4 ranged. |
| **Missing Formula Component** | A formula is partially correct but missing one term. | BUG-C-002: Concentration DC = 10 + damage (missing + spell_level). |
| **Minimum/Maximum Floor Error** | A min/max clamp uses the wrong boundary value. | BUG-8/9: `max(0, damage)` should be `max(1, damage)`. |
| **Helper Function Blind Spot** | Formulas in helper functions, gate checks, and constant definitions were not included in the initial formula inventory. | 4 unverified formulas found in Domain A during re-verification (sneak attack immunity, reach weapon donut, flanking HP gate). |

**Section 4: Cross-File Consistency Requirement**

When a verdict changes (especially WRONG → AMBIGUOUS or vice versa), ALL of these files must be updated in the same commit:

1. The domain verification file (verdict text + summary counts)
2. `docs/verification/WRONG_VERDICTS_MASTER.md` (row counts, fix WO status)
3. `docs/verification/BONE_LAYER_CHECKLIST.md` (domain row counts + global totals)
4. `docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md` (if new AMBIGUOUS entry)
5. Any fix WO referencing the reclassified bug (retire or update)

**Evidence:** Domain A re-verification updated the checklist and WRONG_VERDICTS_MASTER but missed DOMAIN_C_VERIFICATION.md — creating an inconsistency that had to be fixed in a separate commit.

**Section 5: Re-Verification Protocol**

Re-verification is NOT rubber-stamping. On re-verification passes:

1. Independently re-derive each verdict (don't just confirm existing text matches code)
2. Search for unverified formulas in helper functions, gate checks, and constants
3. Cross-reference the research corpus (Section 2 above)
4. Check for cross-domain propagation (does this formula consume values from another domain?)
5. Verify line numbers still match (code may have shifted since initial verification)

---

## Gap 2: Context Boundary Protocol (ADD TO AGENT_DEVELOPMENT_GUIDELINES.md)

**Add a new Section 15** to `AGENT_DEVELOPMENT_GUIDELINES.md`:

### Section 15: Context Boundary Protocol

Agents have perfect recall within a context window and zero recall across context boundaries. These rules ensure institutional knowledge survives rotation.

**15.1 Artifact Primacy Rule**
Any fact that must survive a context boundary MUST be written to a file. Conversational knowledge not pinned to an artifact is assumed lost at next context rotation.

**15.2 Handoff Checklist (Before Context Window Closes)**
Before a session ends or approaches context limits, verify:
- [ ] State summaries updated (checklist, master lists, iteration log)
- [ ] PM memo written if strategic findings emerged
- [ ] Any mid-session reclassifications reflected in ALL affected files
- [ ] Uncommitted work documented in a handoff file (`pm_inbox/HANDOFF_*.md`)
- [ ] No implicit knowledge required — next agent can execute from artifacts alone

**15.3 Dispatch Self-Containment Rule**
Every dispatch or work order must be executable by an agent with zero prior context. The dispatch plus the files it cites must contain everything needed. No reliance on "the previous agent will have explained this."

**15.4 Cross-File Consistency Gate**
When a status, count, verdict, or classification changes, update ALL files that reference it in the same commit. Partial updates create inconsistencies that compound across context boundaries.

---

## Gap 3: Dispatch Template Amendment (FOR PM)

The PM should add this block to all future verification and re-verification dispatches, between the "Execution Instructions" and "Formulas To Verify" sections:

```markdown
## Required Reading — Research Cross-Reference

**MANDATORY: Before writing any verdict, check these research documents
for documented design decisions that affect this domain:**

- `docs/research/RQ_BOX_001_GEOMETRIC_ENGINE.md` (cover, geometry)
- `docs/research/findings/PF_DELTA_INDEX.md` (PF corrections adopted)
- `docs/research/findings/SKIP_WILLIAMS_DESIGNER_INTENT.md` (RAW disambiguations)
- `docs/research/findings/RQ-BOX-002-F_FAQ_MINING_RESULTS.md` (FAQ rulings)
- `docs/research/RQ-BOX-002-A_COMMUNITY_RAW_ARGUMENT_SURVEY.md` (known contradictions)
- `docs/verification/VERIFICATION_GUIDELINES.md` (verdict decision tree, error taxonomy)

If the code diverges from SRD but matches a documented design decision,
classify as AMBIGUOUS with DESIGN REFERENCE citation, not WRONG.
```

**Note:** The fix WO dispatch packet (`pm_inbox/FIX_WO_DISPATCH_PACKET.md`) already includes a similar cross-reference requirement in its Universal Builder Instructions. This is correct and should be preserved.

---

## Gap 4: Knowledge Synthesis Addendum (LOW PRIORITY — DEFER)

`docs/PROJECT_KNOWLEDGE_SYNTHESIS.md` is dated 2026-02-08 and predates the bone-layer verification. Its confidence numbers (0.98 for CP-09-17 foundation) should be qualified with verification results. However, this is low priority — the PM has the data via `pm_inbox/MEMO_REVERIFY_A_FINDINGS.md`. A formal synthesis update should wait until the remaining re-verifications are done and the fix WOs land.

No action needed from the rollover agent on this gap.

---

## Execution Order

1. **Commit the Domain C consistency fix** (uncommitted edit, see "Uncommitted Work" above)
2. **Create `VERIFICATION_GUIDELINES.md`** using the contents specified in Gap 1
3. **Add Section 15 to `AGENT_DEVELOPMENT_GUIDELINES.md`** using the contents in Gap 2
4. **Update `AGENT_ONBOARDING_CHECKLIST.md`** — add `VERIFICATION_GUIDELINES.md` to the Step 1 reading table (after KNOWN_TECH_DEBT.md, applicable to verification work orders)
5. **Commit:** `docs: add verification guidelines + context boundary protocol (governance patch)`

---

## Files to Read Before Executing

- This file (you're reading it)
- `AGENT_DEVELOPMENT_GUIDELINES.md` (to understand where Section 15 goes)
- `AGENT_ONBOARDING_CHECKLIST.md` (to understand the reading table format)
- `docs/verification/DOMAIN_C_VERIFICATION.md` (to verify the uncommitted edit)
- `pm_inbox/MEMO_REVERIFY_A_FINDINGS.md` (context on why these gaps exist)

---

## What NOT To Do

- Do NOT touch any source code files (*.py)
- Do NOT modify any verification domain files except the Domain C consistency fix
- Do NOT update BONE_LAYER_CHECKLIST or WRONG_VERDICTS_MASTER (already correct)
- Do NOT run tests (this is documentation-only work)
- Do NOT start any fix WOs (those are running in a separate session)

---

**End of Handoff**
