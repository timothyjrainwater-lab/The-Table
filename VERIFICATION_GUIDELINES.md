<!--
VERIFICATION GUIDELINES — VERIFICATION-SPECIFIC PITFALL AVOIDANCE & PROTOCOL

This file is MANDATORY READING for all agents performing verification or re-verification
work orders. It documents lessons learned from the bone-layer verification (338 formulas,
9 domains) and the Domain A re-verification that discovered research cross-reference gaps.

Companion to AGENT_DEVELOPMENT_GUIDELINES.md (which covers coding pitfalls).

LAST UPDATED: 2026-02-14 (Post bone-layer verification, 338 formulas across 9 domains)
-->

# Verification Guidelines

**Status:** CANONICAL (Binding for all verification and re-verification work)
**Companion to:** `AGENT_DEVELOPMENT_GUIDELINES.md` (coding pitfalls)

---

## 1. Verdict Decision Tree

Use this tree for every formula verification. Follow it top to bottom.

```
Code matches SRD exactly?
├── Yes → CORRECT
├── No → Is there a documented design decision in the research corpus?
│   ├── Yes → AMBIGUOUS (cite research doc + finding ID)
│   └── No → Is the SRD itself ambiguous or silent on this point?
│       ├── Yes → AMBIGUOUS (cite the ambiguity)
│       └── No → WRONG (assign BUG-ID, file in WRONG_VERDICTS_MASTER)
└── No specific SRD citation exists for this formula?
    └── UNCITED (standard arithmetic, universal rule, no SRD page needed)
```

### Verdict Definitions

| Verdict | Meaning | Action Required |
|---------|---------|-----------------|
| CORRECT | Code matches SRD exactly | None |
| WRONG | Code diverges from SRD with no documented justification | Assign BUG-ID, add to WRONG_VERDICTS_MASTER |
| AMBIGUOUS | Code diverges from SRD but matches a documented design decision, OR the SRD is genuinely ambiguous | Cite the design reference or ambiguity source |
| UNCITED | Formula implements universally understood arithmetic with no specific SRD page citation | None — note why no citation is needed |

---

## 2. Required Research Cross-Reference

**MANDATORY: Before writing any WRONG verdict**, search these documents for keywords related to the formula being verified. If the code behavior matches a documented design decision, classify as AMBIGUOUS with a DESIGN REFERENCE citation, not WRONG.

| Document | Path | Relevant To |
|----------|------|-------------|
| Geometric Engine Research | `docs/research/RQ_BOX_001_GEOMETRIC_ENGINE.md` | Cover, geometry, LOS/LOE, grid calculations |
| PF Delta Index | `docs/research/findings/PF_DELTA_INDEX.md` | Pathfinder corrections adopted as design decisions |
| Skip Williams Designer Intent | `docs/research/findings/SKIP_WILLIAMS_DESIGNER_INTENT.md` | RAW disambiguations, designer rulings |
| FAQ Mining Results | `docs/research/findings/RQ-BOX-002-F_FAQ_MINING_RESULTS.md` | Official FAQ rulings on ambiguous rules |
| Community RAW Survey | `docs/research/RQ-BOX-002-A_COMMUNITY_RAW_ARGUMENT_SURVEY.md` | Known SRD contradictions between PHB/DMG/MM |

### Why This Matters

Domain A re-verification found 4 reclassifications (WRONG→AMBIGUOUS) from one domain because the initial verifier didn't have the research corpus in context. BUG-10 (cover values +2/+1 half, +5/+2 three-quarters) was flagged WRONG when it was actually a documented design decision in RQ-BOX-001 Finding 3. The same root cause cascaded into Domain C (BUG-C-001/003).

**Estimate:** Of 30 WRONG verdicts across all domains, ~8-10 may be documented design decisions that need reclassification once cross-referenced against research. The genuine bug count is likely 20-22.

---

## 3. Common Verification Error Patterns

These are categories of errors discovered during verification. When verifying formulas, actively look for these patterns.

| Pattern | Description | Example | Domains Affected |
|---------|-------------|---------|-----------------|
| **Research Cross-Ref Miss** | Code diverges from SRD but matches a documented design decision. Flagged WRONG when it should be AMBIGUOUS. | BUG-10: cover values. Design decision in RQ-BOX-001 Finding 3. | A, C, I |
| **SRD Table Transcription Error** | A lookup table was coded by formula approximation instead of hardcoding the source table. Works for some rows, diverges for others. | BUG-F2/F3: XP table levels 11-20 computed by formula instead of DMG Table 2-6 values. | F |
| **Sign/Direction Inversion** | A boolean condition or comparison operator is backwards. One-character fix, high impact. | E-BUG-01: soft cover `is_melee` should be `not is_melee`. | E |
| **Incomplete Enumeration** | A lookup table or constant set is missing entries. Works for common cases, fails for edge cases. | I-GEOM-291: SIZE_ORDER missing Fine, Diminutive, Colossal (6 of 9 categories present). | E, I |
| **Modifier Not Differentiated** | A modifier is applied as a flat value when the SRD specifies different values for different contexts (melee vs ranged, etc.). | BUG-3/4: Prone/Helpless AC modifier is flat -4 instead of -4 melee / +4 ranged. | D, A (propagated) |
| **Missing Formula Component** | A formula is partially correct but missing one term. | BUG-C-002: Concentration DC = 10 + damage (missing + spell_level). | C |
| **Minimum/Maximum Floor Error** | A min/max clamp uses the wrong boundary value. | BUG-8/9: `max(0, damage)` should be `max(1, damage)` per PHB p.141. | A |
| **Helper Function Blind Spot** | Formulas in helper functions, gate checks, and constant definitions were not in the initial formula inventory. | 4 unverified formulas found in Domain A re-verification (sneak attack immunity, reach weapon donut, flanking HP gate). | All |

### Using This Taxonomy

When writing verification records, check each formula against these 8 patterns. If you find an error, note which pattern it matches — this helps the PM prioritize fixes and detect systemic issues.

---

## 4. Cross-File Consistency Requirement

When a verdict changes (especially WRONG → AMBIGUOUS or vice versa), **ALL** of these files must be updated in the same commit:

1. **The domain verification file** — verdict text and summary counts
2. **`docs/verification/WRONG_VERDICTS_MASTER.md`** — row counts and fix WO status
3. **`docs/verification/BONE_LAYER_CHECKLIST.md`** — domain row counts and global totals
4. **`docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md`** — if adding a new AMBIGUOUS entry
5. **Any fix WO referencing the reclassified bug** — retire or update

### Why This Matters

Domain A re-verification updated the checklist and WRONG_VERDICTS_MASTER but missed `DOMAIN_C_VERIFICATION.md`, creating an inconsistency that required a separate fix commit. Partial updates compound across context boundaries — the next agent sees conflicting numbers and can't determine which is correct without re-reading source files.

---

## 5. Re-Verification Protocol

Re-verification is **NOT rubber-stamping**. On re-verification passes:

1. **Independently re-derive each verdict** — don't just confirm existing text matches code. Re-read the SRD reference and re-evaluate.
2. **Search for unverified formulas** — helper functions, gate checks, constant tables, and enum definitions often contain verifiable formulas that weren't in the initial inventory.
3. **Cross-reference the research corpus** — see Section 2. This is the step the initial verification missed.
4. **Check for cross-domain propagation** — if a formula consumes values from another domain's code (e.g., attack resolver consuming condition modifiers), note the dependency even if the formula itself is correct.
5. **Verify line numbers still match** — code may have shifted since initial verification due to fixes or refactoring.

### Re-Verification Output

A re-verification pass should produce:

- Updated verdict for any reclassified formulas (with rationale)
- New verification records for any previously unverified formulas found
- Updated summary counts in the domain verification file
- Research cross-reference findings section documenting which research docs were consulted
- Updated formula count table showing initial vs re-verification deltas

---

## 6. SRD Edition Contamination

This project implements **D&D 3.5e** rules. The SRD reference is d20srd.org (3.5e SRD).

Common traps when verifying against the wrong edition:

| 3.5e (Correct) | 5e (Wrong) | Impact |
|----------------|------------|--------|
| Cover: +4 AC, +2 Reflex | Cover: half cover +2 AC, three-quarters +5 AC | Cover bonus values completely different |
| Two-handed STR: 1.5× | Two-handed: same as 3.5e but different damage dice | STR multiplier is the same, but context differs |
| Damage type: "electricity" | Damage type: "lightning" | Wrong string constant |
| 0-level spells use spell slots | Cantrips are at-will | Fundamental spell slot economy difference |
| Feat prerequisites: numeric (BAB +1, STR 13) | Feat system doesn't exist in 5e | Different prerequisite model entirely |
| Size categories: 9 (Fine through Colossal) | Size categories: 6 (Tiny through Gargantuan) | Missing 3 categories at extremes |

When in doubt, verify against d20srd.org, not any 5e source.

---

## 7. Verification Record Format

Every formula must have a verification record in this format:

```
FORMULA ID: [Domain]-[source]-[line]
FILE: [path/to/file.py]
LINE: [line number(s)]
CODE: `[exact code snippet]`
RULE SOURCE: [SRD section, PHB page, or other citation]
EXPECTED: [what the SRD says the value/behavior should be]
ACTUAL: [what the code actually does]
VERDICT: [CORRECT | WRONG | AMBIGUOUS | UNCITED]
NOTES: [explanation, especially for WRONG/AMBIGUOUS verdicts]
```

For WRONG verdicts, also add a bug entry in the Bug List section:

```
### BUG-[ID]: [Short description]
- **Locations:** [file:line, file:line]
- **SRD Rule:** [quoted rule text]
- **Expected:** [correct behavior]
- **Actual:** [current behavior]
- **Impact:** [what breaks in gameplay]
```

For AMBIGUOUS verdicts with design decisions, add:

```
DESIGN REFERENCE: [path to research document + finding ID]
```

---

## Revision History

- **2026-02-14 v1.0:** Initial creation from bone-layer verification lessons learned
  - Verdict decision tree
  - Research cross-reference requirement (5 documents)
  - 8-pattern error taxonomy from 30 bugs across 9 domains
  - Cross-file consistency requirement
  - Re-verification protocol
  - SRD edition contamination guide

---

**END OF VERIFICATION GUIDELINES**

**Status:** CANONICAL (Binding for all verification work)
**Enforcement:** Immediate (effective for all current and future verification dispatches)
