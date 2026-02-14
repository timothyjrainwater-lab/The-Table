# Verification Addendum: Edge Case Research Reference

**ALL verification builders MUST read this before flagging any formula as AMBIGUOUS.**

---

## Purpose

The project has completed extensive research into D&D 3.5e edge cases, errata, designer intent, Pathfinder corrections, and community RAW disputes. Before marking any formula as AMBIGUOUS, check these artifacts for an existing design decision or clarification.

---

## Research Artifacts (check in this order)

### 1. Official FAQ Errata
**File:** `docs/research/findings/RQ-BOX-002-F_FAQ_MINING_RESULTS.md` (1415 lines)
**Contains:** Official D&D 3.5e FAQ (June 2008) — errata, rule clarifications, and corrections from WotC. If the FAQ addresses a formula you're verifying, the FAQ ruling is authoritative.

### 2. Pathfinder Delta Index
**File:** `docs/research/findings/PF_DELTA_INDEX.md` (685 lines)
**Contains:** Complete index of mechanics Pathfinder 1e changed from 3.5e, with rationale. If 3.5e has a known flaw that Pathfinder explicitly fixed, note both the 3.5e formula and the Pathfinder correction in your AMBIGUOUS record. The project may adopt the Pathfinder fix — that's an Operator decision, not a builder decision.

### 3. Designer Intent (Skip Williams)
**File:** `docs/research/findings/SKIP_WILLIAMS_DESIGNER_INTENT.md` (970 lines)
**Contains:** Rulings from Skip Williams' "Rules of the Game" column — the lead designer of 3.5e explaining how rules were intended to work. Use this when the SRD text is ambiguous but designer intent is clear.

### 4. Community RAW Survey
**File:** `docs/research/RQ-BOX-002-A_COMMUNITY_RAW_ARGUMENT_SURVEY.md` (342 lines)
**Contains:** Survey of major community RAW debates with outcomes. Lowest priority — use only when sources 1-3 don't address the issue.

---

## How To Use During Verification

When you encounter a formula that doesn't clearly match the SRD:

1. Search the FAQ (source 1) for the relevant topic. If the FAQ clarifies, cite it and verdict CORRECT or WRONG based on the FAQ ruling.
2. If no FAQ entry, check the PF Delta Index (source 2). If Pathfinder changed this mechanic, note the 3.5e version AND the Pathfinder version in your record. Verdict: AMBIGUOUS with both options documented.
3. If neither FAQ nor PF Delta addresses it, check Designer Intent (source 3). If Skip Williams clarified, cite the column.
4. If none of the above apply, verdict AMBIGUOUS with your analysis of the ambiguity.

**DO NOT** read these files cover-to-cover. Search them for the specific mechanic you're verifying (Ctrl+F or grep for keywords). These files are large — targeted searches only.
