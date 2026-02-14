# BONE-LAYER VERIFICATION PLAN — Execution Document

**Document ID:** BONE-VERIFY-PLAN-001
**Created:** 2026-02-14
**Authority:** PM (Opus), authorized by Operator (Thunder)
**Status:** ACTIVE — ALL OTHER WORK BLOCKED UNTIL GREEN

---

## 1. What This Is

This document defines the execution plan for a formula-by-formula verification of every mathematical computation in the combat engine. The engine implements a tabletop combat algorithm derived from the d20 SRD 3.5e ruleset, with known corrections from the Pathfinder SRD where 3.5e has documented flaws or ambiguities.

**The foundational contract of this project is: "The box doesn't lie."** Every number the engine produces must be provably correct against the source algorithm. If this contract is broken, everything built on top — AI, voice, UX, narrative — is decoration on a wrong foundation.

This verification was triggered by an Action Economy Audit (2026-02-13) that found 4 HIGH severity arithmetic bugs in core resolvers — areas that should have been trivially correct. If basic STR multipliers and AC modifiers are wrong, the verification surface has not been inspected.

---

## 2. Blocking Policy

**RED FLAG — FULL STOP on all feature work, builder dispatches, and playtesting until this verification is complete.**

The following are explicitly BLOCKED:
- All Wave C WOs (WO-SPELLSLOTS-01, WO-SPELLLIST-CLI-01, WO-CHARSHEET-CLI-01)
- WO-BUGFIX-TIER0-001 (Tier 0 bug fixes — these fix symptoms; this plan verifies the whole surface)
- All BURST queue items (BURST-001, BURST-002, BURST-003)
- Any new feature WOs
- Any playtesting or playtest signal analysis

The following are NOT BLOCKED:
- This verification work itself
- PM housekeeping (PSD updates, kernel updates, WO tracking)
- Documentation-only changes
- Test additions that verify existing behavior (verification tests)

---

## 3. Architecture: Bone / Muscle / Skin

The engine uses a three-layer model:

- **BONE**: Raw numeric constants, lookup tables, modifier values. These are the numbers themselves — the +4, the -2, the 1d8, the DC 15. These come directly from rulebook tables and must match exactly.

- **MUSCLE**: The mathematical algorithms that combine bones into results. Attack roll = d20 + BAB + STR_MOD + condition_modifier + feat_modifier + flanking_bonus vs AC. These are the formulas, and both the formula structure and the operator precedence must match the source rules.

- **SKIN**: Flavor text, event descriptions, CLI formatting, voice output. Not in scope for this verification.

This plan verifies BONE and MUSCLE layers only.

---

## 4. Source Rule Authority

For each formula, the verification checks against this authority chain (in priority order):

1. **SRD 3.5e** (primary source — the IP-clean algorithm reference)
2. **Pathfinder SRD** (correction source — where 3.5e has known errata, ambiguity, or design flaws that Pathfinder explicitly fixed)
3. **DMG 3.5e tables** (for XP, treasure, encounter balance formulas)
4. **Errata documents** (official 3.5e errata where applicable)

When 3.5e and Pathfinder disagree, the chosen algorithm MUST be documented with a rationale. There is no "default to 3.5e" — each divergence is a deliberate design decision.

---

## 5. Verification Surface — File Inventory

The formula inventory (produced 2026-02-14) identified formulas across 22 source files. These are grouped into verification domains:

### Domain A: Attack Resolution (highest risk — bugs already found here)
| File | Formula Count | Priority |
|------|--------------|----------|
| `aidm/core/attack_resolver.py` | 18 | CRITICAL |
| `aidm/core/full_attack_resolver.py` | 8 | CRITICAL |
| `aidm/core/sneak_attack.py` | 3 | HIGH |
| `aidm/core/damage_reduction.py` | 6 | HIGH |
| `aidm/core/flanking.py` | 3 | HIGH |
| `aidm/core/concealment.py` | 2 | MEDIUM |
| `aidm/core/ranged_resolver.py` | 4 | MEDIUM |
| `aidm/core/reach_resolver.py` | 5 | MEDIUM |
| `aidm/core/cover_resolver.py` | 4 | MEDIUM |

### Domain B: Combat Maneuvers
| File | Formula Count | Priority |
|------|--------------|----------|
| `aidm/core/maneuver_resolver.py` | 18 | HIGH |
| `aidm/schemas/maneuvers.py` | 9 | HIGH (size modifiers — verify against table) |

### Domain C: Saves & Spells
| File | Formula Count | Priority |
|------|--------------|----------|
| `aidm/core/save_resolver.py` | 10 | HIGH |
| `aidm/core/spell_resolver.py` | 11 | HIGH |

### Domain D: Conditions & Modifiers
| File | Formula Count | Priority |
|------|--------------|----------|
| `aidm/schemas/conditions.py` | 42 | CRITICAL (every modifier value must match PHB p.311 table) |
| `aidm/core/conditions.py` | 15 | HIGH (aggregation logic — stacking rules) |

### Domain E: Movement & Terrain
| File | Formula Count | Priority |
|------|--------------|----------|
| `aidm/core/movement_resolver.py` | 2 | HIGH |
| `aidm/core/terrain_resolver.py` | 13 | MEDIUM |
| `aidm/core/mounted_combat.py` | 12 | MEDIUM |
| `aidm/schemas/attack.py` (FullMoveIntent) | 5 | HIGH |
| `aidm/schemas/position.py` | 2 | HIGH (distance formula) |

### Domain F: Character Progression & Economy
| File | Formula Count | Priority |
|------|--------------|----------|
| `aidm/core/experience_resolver.py` | 10 | MEDIUM |
| `aidm/core/encumbrance.py` | 18 | MEDIUM |
| `aidm/schemas/leveling.py` | 30+ | MEDIUM (table verification) |
| `aidm/schemas/feats.py` | 12 | MEDIUM (prerequisite values) |
| `aidm/schemas/skills.py` | 7 | LOW |

### Domain G: Initiative & Turn Structure
| File | Formula Count | Priority |
|------|--------------|----------|
| `aidm/core/initiative.py` | 3 | HIGH |
| `aidm/core/combat_controller.py` | 1 | LOW |
| `play.py` (ActionBudget) | 6 | HIGH |

### Domain H: Skill System
| File | Formula Count | Priority |
|------|--------------|----------|
| `aidm/core/skill_resolver.py` | 6 | MEDIUM |

### Domain I: Geometry & Size
| File | Formula Count | Priority |
|------|--------------|----------|
| `aidm/schemas/geometry.py` | 3 | HIGH (footprint table) |
| `aidm/schemas/bestiary.py` | 10 | LOW (default values) |
| `aidm/schemas/terrain.py` | 5 | HIGH (cover values) |

**Total: ~280+ formulas across 22 files, 9 domains**

---

## 6. Execution Method — Per-Formula Verification

For each formula, the verifying agent must produce a **Verification Record** with these exact fields:

```
FORMULA ID: <DOMAIN>-<FILE_SHORT>-<LINE>
FILE: <full path>
LINE: <line number(s)>
CODE: <exact code snippet>
RULE SOURCE: <book, page, paragraph or table reference>
EXPECTED: <what the rule says the formula should be>
ACTUAL: <what the code does>
VERDICT: CORRECT | WRONG | AMBIGUOUS | UNCITED
NOTES: <if WRONG: what's wrong and what the fix is>
        <if AMBIGUOUS: what the ambiguity is and what Pathfinder says>
        <if UNCITED: what rule this likely implements>
```

### Verdict Definitions

- **CORRECT**: Code exactly matches source rule. No interpretation required.
- **WRONG**: Code produces a different result than the source rule specifies. This is a bug.
- **AMBIGUOUS**: Source rule is unclear or has multiple valid interpretations. Must document which interpretation was chosen and why. If Pathfinder clarifies, note the Pathfinder ruling.
- **UNCITED**: Code implements something reasonable but no source rule citation exists. Must either find the citation or flag as a design decision.

---

## 7. Execution Sequence

This work is divided into **iterations** (one domain per iteration). Each iteration is a self-contained unit that can be executed by any agent with access to this plan and the codebase.

### Iteration Order (by risk priority):

1. **Domain D: Conditions & Modifiers** — 57 formulas
   - WHY FIRST: Every other domain consumes condition modifiers. If these are wrong, everything downstream is wrong. The PHB p.311 table is a single authoritative source — verification is mechanical comparison.

2. **Domain A: Attack Resolution** — 53 formulas
   - WHY SECOND: Known bugs here (BUG-1 through BUG-4). Highest gameplay impact. Most complex formula chains.

3. **Domain B: Combat Maneuvers** — 27 formulas
   - WHY THIRD: Maneuver formulas reference size modifiers, STR, BAB — same inputs as attacks. Verifying after Domain A ensures shared inputs are already confirmed.

4. **Domain C: Saves & Spells** — 21 formulas
   - WHY FOURTH: Saves are the second most common roll type. Spell DCs feed into saves.

5. **Domain G: Initiative & Turn Structure** — 10 formulas
   - WHY FIFTH: Small surface, high impact on game flow.

6. **Domain E: Movement & Terrain** — 34 formulas
   - WHY SIXTH: Recently implemented (CP-16). Fresh code, more likely correct, but must verify.

7. **Domain F: Character Progression & Economy** — 77 formulas
   - WHY SEVENTH: Mostly table lookups. Tedious but mechanical verification.

8. **Domain H: Skill System** — 6 formulas
   - WHY EIGHTH: Small, self-contained.

9. **Domain I: Geometry & Size** — 18 formulas
   - WHY NINTH: Support data. Low risk.

### Per-Iteration Protocol

Each iteration produces:
1. A verification record for every formula in that domain
2. A summary: X CORRECT, Y WRONG, Z AMBIGUOUS, W UNCITED
3. A bug list (if any WRONG verdicts) with exact fix descriptions
4. An update to the tracking checklist (see Section 8)

Each iteration is committed separately with message format:
```
verify: Domain <X> — <domain name> (<N> formulas, <Y> wrong, <Z> ambiguous)
```

### Iteration Completion Gate

An iteration is COMPLETE when:
- Every formula in the domain has a verification record
- All WRONG verdicts have fix descriptions (fixes are NOT applied — they become WOs)
- All AMBIGUOUS verdicts have documented design decisions
- The tracking checklist is updated
- The iteration is committed

**IMPORTANT: This verification does NOT fix bugs.** It identifies them. Fixes are separate WOs dispatched after the full verification is complete. This prevents scope creep and ensures the verification itself is a clean, auditable artifact.

---

## 8. Tracking Checklist

A separate file `docs/verification/BONE_LAYER_CHECKLIST.md` tracks verification status per domain. Format:

```markdown
| Domain | Files | Formulas | Verified | Correct | Wrong | Ambiguous | Uncited | Status |
|--------|-------|----------|----------|---------|-------|-----------|---------|--------|
| D: Conditions | 2 | 57 | 0 | 0 | 0 | 0 | 0 | NOT STARTED |
| A: Attack | 9 | 53 | 0 | 0 | 0 | 0 | 0 | NOT STARTED |
| ... | | | | | | | | |
```

This checklist is the canonical progress tracker. When all domains show status COMPLETE and the WRONG count has corresponding fix WOs, the verification is done.

---

## 9. Completion Criteria

The bone-layer verification is COMPLETE when:

1. All 9 domains are verified (every formula has a record)
2. All WRONG verdicts have fix WOs written
3. All AMBIGUOUS verdicts have documented design decisions approved by Operator
4. The tracking checklist shows all domains COMPLETE
5. The PSD is updated to reflect verification status
6. The blocking policy (Section 2) is lifted by Operator decision

At that point:
- Fix WOs are dispatched (priority: Domain A and D first)
- After fixes land and tests pass, the RED block is lifted
- Feature work can resume with confidence that "the box doesn't lie"

---

## 10. Agent Instructions — How To Execute This Plan

If you are an agent picking up this work cold:

1. Read this document fully.
2. Read the formula inventory at `docs/verification/FORMULA_INVENTORY.md`.
3. Read the tracking checklist at `docs/verification/BONE_LAYER_CHECKLIST.md`.
4. Find the first domain with status NOT STARTED or IN PROGRESS.
5. For each formula in that domain:
   a. Read the code at the specified file and line.
   b. Look up the cited rule in the SRD 3.5e (or Pathfinder SRD if 3.5e is ambiguous).
   c. Compare the code's arithmetic to the rule's specification.
   d. Write the verification record.
   e. Assign a verdict.
6. When all formulas in the domain are verified, write the domain summary.
7. Update the tracking checklist.
8. Commit with the iteration commit message format.
9. If you run out of context, commit what you have and update the checklist to IN PROGRESS so the next agent knows where to resume.

**DO NOT:**
- Fix bugs during verification (write the record, move on)
- Skip formulas because they "look right"
- Verify against memory — always check the actual SRD text
- Change the execution order without Operator approval
- Mark a domain COMPLETE if any formula is unverified

---

## 11. Relationship to Existing Artifacts

- **ACTION_ECONOMY_AUDIT.md**: Muscle-layer audit. Identified structural gaps and wiring issues. This verification is the bone-layer complement.
- **WO-BUGFIX-TIER0-001**: Fixes for 4 known bugs. BLOCKED behind this verification (the fix WO may expand once verification finds more bugs).
- **PROJECT_STATE_DIGEST.md**: Will be updated when verification completes.
- **REHYDRATION_KERNEL_LATEST.md**: Will reference this plan as the active blocking work.
- **Outlier/edge-case research** (in `docs/research/`, `pm_inbox/research/`, `pm_inbox/reviewed/`): Prior research into critical edge cases, errata, and Pathfinder corrections. Builders verifying AMBIGUOUS formulas should check these artifacts for existing design decisions before flagging as unresolved.

## 11a. Post-Verification: IP Skin-Stripping Phase

**This phase is BLOCKED behind verification GREEN + all fix WOs INTEGRATED.**

After the bone layer is verified correct and all bugs fixed, the next phase strips all SRD/D&D naming from the codebase, replacing it with algorithmic identifiers. This requires:

1. **Translation index**: A complete SRD-name → algorithmic-name mapping produced from the verification records. Each verified formula gets an IP-clean algorithmic name (e.g., "Prone" → "condition_posture_ground", "Sneak Attack" → "precision_damage_flanked").
2. **Controlled rename pass**: Code rename using the translation index as lookup. Tests updated in the same pass. No formula logic changes — names only.
3. **Verification anchor preservation**: The translation index is the permanent bridge between the SRD source (used for verification) and the production code (IP-clean). It must be maintained as a reference artifact.

**IMPORTANT**: Do NOT begin skin-stripping during or before verification. The SRD names are verification anchors — they are how we confirm correctness against source material. Renaming before verification is proven complete would break the audit trail.

---

## 12. Risk

- **Context window limits**: This is ~303 formulas. No single agent session will complete all 9 domains. The iteration structure and tracking checklist are designed for multi-session execution.
- **SRD access**: Agents need access to SRD 3.5e text. If web search is available, use d20srd.org or similar. If not, the agent must flag formulas it cannot verify due to lack of source text.
- **Pathfinder divergences**: Some formulas may intentionally differ from 3.5e. These MUST be documented as AMBIGUOUS with rationale, not silently accepted or rejected.
- **Scope creep**: The temptation to fix bugs during verification is strong. Resist it. The verification must be a clean audit artifact.

---

## 13. Context Window Discipline — MANDATORY

**The PM agent's context window is a finite, critical resource.** Continuity through the execution of this plan depends on preserving PM context for coordination, not burning it on implementation.

### Rules:

1. **The PM agent does NOT execute verification iterations.** Verification iterations are dispatched as WOs to builder agents (separate Claude Code sessions). The PM writes the WO, the Operator pastes it into a builder session, the builder executes, and the completion report comes back.

2. **The PM agent's context is reserved for:**
   - Writing and dispatching verification iteration WOs
   - Reviewing completion reports from builder agents
   - Updating the tracking checklist, PSD, and rehydration kernel
   - Making coordination decisions (sequencing, blocking, priority changes)
   - Communicating with the Operator

3. **The PM agent MUST NOT:**
   - Read source files line-by-line to verify formulas (that's builder work)
   - Run code or tests (that's builder work)
   - Fix bugs (that's builder work)
   - Explore the codebase beyond what's needed for coordination

4. **If the PM agent runs out of context**, the rehydration kernel (`pm_inbox/REHYDRATION_KERNEL_LATEST.md`) and this plan document contain everything needed to restore PM state in a new session. The tracking checklist shows progress. The iteration log shows what's been done. A new PM agent can pick up exactly where the previous one left off.

5. **Every action the PM takes must pass this test:** "Does this directly serve the organization, dispatch, or tracking of this verification plan?" If not, it becomes a WO for an outside agent.