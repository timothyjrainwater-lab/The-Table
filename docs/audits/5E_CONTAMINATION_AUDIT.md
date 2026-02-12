# 5e Contamination Terminology Audit

**RWO-004 | Date: 2026-02-12**
**Auditor: Claude Opus 4.6 (automated code audit)**
**Scope: Entire codebase (aidm/, tests/, docs/)**

---

## Executive Summary

Five contamination vectors were audited across the entire codebase. The audit found:

- **1 CONTAMINATED finding** (active 5e mechanic implemented in code)
- **9 WARNING findings** (ambiguous terminology that could mislead future implementers)
- **18 CLEAN findings** (correct 3.5e usage or proper anti-contamination guards)

The single CONTAMINATED finding is **critical**: the DurationTracker implements a 5e-style "one concentration spell per caster" global limiter that directly contradicts 3.5e rules. This is not a terminology issue -- it is a mechanical implementation of a 5e rule in production code.

---

## 1. Cantrip Audit

### 1.1 Findings in Production Code

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| C-1 | `aidm/schemas/spell_definitions.py` | 447 | `# -- LEVEL 0 CANTRIPS (4 new) --` | **WARNING** | Comment uses "cantrips" as section header for 0-level spells. No at-will implication, but terminology should be "0-level spells" per project guidelines. |
| C-2 | `aidm/immersion/voice_intent_parser.py` | 225 | `# Level 0 (Cantrips)` | **WARNING** | Comment in KNOWN_SPELLS dict uses "Cantrips" as synonym for Level 0. No mechanical implication, but inconsistent with terminology policy. |

### 1.2 Findings in Tests

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| C-3 | `tests/test_expanded_spells.py` | 137 | `def test_level_0_cantrips():` | **WARNING** | Test function name uses "cantrips". |
| C-4 | `tests/test_expanded_spells.py` | 138 | `"""WO-036: Level 0 contains 4 new cantrips."""` | **WARNING** | Docstring uses "cantrips". |
| C-5 | `tests/test_expanded_spells.py` | 140 | `new_cantrips = ["resistance", "guidance", "mending", "read_magic"]` | **WARNING** | Variable named `new_cantrips`. |
| C-6 | `tests/test_expanded_spells.py` | 142 | `assert spell_id in level_0, f"Cantrip {spell_id} not found"` | **WARNING** | Assert message uses "Cantrip". |

### 1.3 Findings in Documentation

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| C-7 | `AGENT_DEVELOPMENT_GUIDELINES.md` | 175 | `\| Cantrips at will \| 0-level spells use spell slots \|` | CLEAN | Anti-contamination table -- correctly identifies "cantrips at will" as 5e and maps to 3.5e equivalent. |
| C-8 | `AGENT_ONBOARDING_CHECKLIST.md` | 89 | `0-level spells use spell slots (not at-will cantrips)` | CLEAN | Correctly warns against at-will cantrips. |
| C-9 | `AGENT_ONBOARDING_CHECKLIST.md` | 115 | `DO NOT introduce 5e terminology (advantage, short rest, electric damage, cantrips at will)` | CLEAN | Correct prohibition. |
| C-10 | `CP_TEMPLATE.md` | 102 | `Spell slots used for 0-level spells (not at-will cantrips)` | CLEAN | Correct checklist item. |
| C-11 | `PROJECT_STATE_DIGEST.md` | 159 | `4 cantrips, 6 L1, 7 L2, 5 L3, 6 L4, 5 L5` | **WARNING** | Uses "cantrips" as label for level-0 spells in inventory summary. This was flagged by GPT research (GAP-005). |
| C-12 | `pm_inbox/reviewed/SONNET_WO-036_EXPANDED_SPELLS.md` | 44 | `### Level 0 Cantrips (4 new -> 6 total)` | **WARNING** | Work order uses "Cantrips" as section header. |
| C-13 | `pm_inbox/reviewed/SONNET_WO-036_EXPANDED_SPELLS.md` | 127 | `test_level_0_cantrips -- 4 new cantrips present` | **WARNING** | Test reference uses "cantrips". |
| C-14 | `pm_inbox/reviewed/OPUS_WO-036_EXPANDED_SPELLS_DISPATCH.md` | 78 | `### Level 0 Cantrips (4 new)` | **WARNING** (in dispatch doc) |
| C-15 | `docs/research/findings/RQ_SPARK_001_C_IMPROVISATION_AND_NPCS.md` | 941 | `Cantrips scale with level \| Cantrips fixed damage` | CLEAN | Anti-contamination table comparing 5e vs 3.5e. |
| C-16 | `docs/planning/GPT_RESEARCH_SYNTHESIS_ACTION_PLAN.md` | 170, 173 | References to cantrip contamination vector | CLEAN | This is the research that identified the problem. |

### 1.4 Findings in Source Text (SRD extracts -- excluded from audit)

Files under `sources/text/` and `Vault/` are PHB/SRD text extracts where "cantrip" is the official 3.5e glossary term for arcane 0-level spells (PHB p.305: "Arcane spellcasters often call their 0-level spells 'cantrips'"). These are **not contamination** -- they are source material.

### 1.5 Cantrip Summary

The word "cantrip" appears in 2 production code files (comments only), 1 test file (function name + variable + docstring + assert), and multiple docs. None imply at-will casting. However, per the project's own guidelines (AGENT_DEVELOPMENT_GUIDELINES.md Section 7) and the GPT research (GAP-005), the preferred term in project-authored code/docs is "0-level spell".

**Recommended fixes for WARNING items:**
- C-1: Change comment to `# -- LEVEL 0 SPELLS (4 new) --`
- C-2: Change comment to `# Level 0 (0-level spells)`
- C-3 through C-6: Rename test function to `test_level_0_spells`, variable to `new_level_0`, etc.
- C-11: Change to `4 0-level, 6 L1, ...`
- C-12 through C-14: Change section headers to `### Level 0 Spells`

---

## 2. Concentration Audit

### 2.1 CRITICAL FINDING: 5e-Style Global Concentration Limiter

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| CON-1 | `aidm/core/duration_tracker.py` | 115 | `self._concentration: Dict[str, str] = {}    # caster_id -> effect_id` | **CONTAMINATED** | This is a **one-to-one mapping** from caster to effect. It enforces "one concentration spell per caster" -- the 5e rule, NOT 3.5e. |
| CON-2 | `aidm/core/duration_tracker.py` | 124-136 | `If the effect requires concentration and the caster already has a concentration effect active, the old effect is automatically ended.` | **CONTAMINATED** | The `add_effect()` method automatically removes existing concentration effects when a new one is added. This is 5e behavior. In 3.5e, a caster can maintain **multiple** concentration-duration spells simultaneously. |
| CON-3 | `aidm/core/duration_tracker.py` | 250-262 | `get_concentration_effect()` returns singular Optional | **CONTAMINATED** | Returns a single effect (singular), implying one-at-a-time. Should return a list. |
| CON-4 | `aidm/core/duration_tracker.py` | 298-317 | `break_concentration()` removes single effect from `_concentration` dict | **CONTAMINATED** | Only breaks one effect because the data structure only allows one. |
| CON-5 | `aidm/core/duration_tracker.py` | 355-364 | `has_active_concentration()` checks singular slot | **CONTAMINATED** | Checks the one-to-one `_concentration` dict. |

**Evidence this is 5e contamination:**

The project's own research explicitly identifies this risk:
- `docs/research/findings/RQ_SPARK_001_C_IMPROVISATION_AND_NPCS.md` line 943: `"Concentration (one spell only) | No concentration limit | (3.5e = duration only)"`
- `pm_inbox/gpt_rehydration/findings/01_architecture_integration/3.txt` line 8: `"Concentration" is a contamination trap: you correctly implement Concentration as a skill check (DC 10+damage) but the system also talks about "concentration management" in DurationTracker -- risk of someone introducing 5e-style "one concentration spell" global limiter.`

**Yet the limiter exists in the code.** The `_concentration` dict on line 115 of `duration_tracker.py` is exactly the 5e-style global limiter the research warned about.

**3.5e RAW (PHB p.174):** Concentration is a **spell duration type**. A caster can maintain multiple spells with "Concentration" duration simultaneously, but must make Concentration skill checks (DC 10 + damage) to maintain each one when taking damage. There is no limit to how many concentration-duration spells a caster can maintain at once. The limitation is practical (each requires a standard action to maintain if the spell requires it), not a hard mechanical cap.

### 2.2 Correct 3.5e Concentration Implementations

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| CON-6 | `aidm/core/spell_resolver.py` | 992-1077 | `check_concentration_on_damage()` | CLEAN | Correctly implements DC = 10 + damage using Concentration skill. The skill check logic itself is 3.5e-correct. |
| CON-7 | `tests/test_concentration_integration.py` | all | Tests for concentration check mechanic | CLEAN | Tests verify DC = 10 + damage, skill check, break on failure. The skill check tests are correct 3.5e. |
| CON-8 | `PROJECT_STATE_DIGEST.md` | 120 | `Concentration (CON)` in skill list | CLEAN | Correctly lists Concentration as a 3.5e skill (CON-based). |
| CON-9 | `PROJECT_STATE_DIGEST.md` | 123 | `Concentration DC (10+damage) in spell_resolver.py` | CLEAN | Correctly describes the 3.5e DC formula. |
| CON-10 | `aidm/schemas/spell_definitions.py` | multiple | `concentration=False` / `concentration=True` | CLEAN | Spell property marking duration type. This is a correct 3.5e concept (Concentration is a valid duration type in 3.5e). |

### 2.3 Concentration Summary

The Concentration **skill check** (DC 10 + damage) is correctly implemented as 3.5e. However, the DurationTracker's **global concentration limiter** (one concentration spell per caster, auto-end on new) is a 5e mechanic. This is the most serious finding in this audit.

**Recommended fix for CON-1 through CON-5:**
- Replace `_concentration: Dict[str, str]` (one-to-one) with `_concentration: Dict[str, List[str]]` (one-to-many)
- Remove the auto-end logic in `add_effect()` that removes existing concentration effects
- Change `get_concentration_effect()` to return `List[ActiveSpellEffect]`
- Change `break_concentration()` to break ALL concentration effects for a caster (needed when caster is killed, etc.)
- Add `break_concentration_for_spell(effect_id)` for when a specific spell's concentration is broken
- Concentration checks on damage should iterate over ALL active concentration effects, making a separate check for each

---

## 3. Rest/Healing Audit

### 3.1 Findings

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| R-1 | `aidm/lens/scene_manager.py` | 11-15 | `D&D 3.5E REST MECHANICS (NOT 5E): ... NO "short rest" hit dice spending (that's 5e only)` | CLEAN | Explicitly correct 3.5e implementation with anti-contamination comment. |
| R-2 | `aidm/lens/scene_manager.py` | 418-501 | `process_rest()` with `rest_type: Literal["8_hours", "long_term_care", "bed_rest"]` | CLEAN | Uses 3.5e rest categories (PHB p.146). No short rest. No hit dice spending. Healing formula is 3.5e-correct. |
| R-3 | `tests/test_time.py` | 153 | `reason="long_rest"` | **WARNING** | The string `"long_rest"` is used as a reason label for a TimeAdvanceEvent. While this is just a free-text label (not mechanical), "long rest" is 5e terminology. In 3.5e, the equivalent is "8-hour rest" or "overnight rest". |
| R-4 | `aidm/schemas/entity_fields.py` | 79 | `# --- Hit Dice (SKR-002 Phase 3) ---` | CLEAN | "Hit Dice" is a legitimate 3.5e term (HD is used for creature type, not healing resource). The fields `HD_COUNT` and `BASE_HP` are standard 3.5e entity properties. |

### 3.2 Findings in Documentation (anti-contamination guards)

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| R-5 | `AGENT_DEVELOPMENT_GUIDELINES.md` | 172 | `Short rest / Long rest \| 8-hour rest / Full day bed rest` | CLEAN | Anti-contamination mapping table. |
| R-6 | `AGENT_ONBOARDING_CHECKLIST.md` | 87 | `No short rest/long rest (use "overnight"/"full_day")` | CLEAN | Correct prohibition. |
| R-7 | `CP_TEMPLATE.md` | 99 | `No short rest/long rest terminology` | CLEAN | Checklist item. |
| R-8 | `docs/CP001_POSITION_UNIFICATION_DECISIONS.md` | 357 | `[x] No short rest/long rest terminology` | CLEAN | Confirmed checked off. |
| R-9 | `docs/research/findings/RQ_SPARK_001_C_IMPROVISATION_AND_NPCS.md` | 942 | `Short/Long Rest (1hr/8hr) \| 8hr rest only (no short rest)` | CLEAN | Anti-contamination reference table. |

### 3.3 Rest/Healing Summary

Rest mechanics are correctly implemented as 3.5e. The only concern is the string `"long_rest"` in a test fixture (R-3), which is a minor terminology issue.

**Recommended fix for R-3:**
- Change `reason="long_rest"` to `reason="overnight_rest"` or `reason="8_hour_rest"`.

---

## 4. Skill Naming Audit

### 4.1 Findings in Production Code

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| S-1 | `aidm/core/targeting_resolver.py` | 196 | `- No perception checks (deferred)` | **WARNING** | Comment says "perception checks" instead of "Spot/Listen checks". While contextually referring to a general capability rather than a specific skill, it could be read as referencing the 5e Perception skill. |

### 4.2 Findings in Tests

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| S-2 | `tests/test_skill_resolver.py` | 57 | `"""Level 5 rogue with stealth skills."""` | CLEAN | Lowercase "stealth skills" as a category description (Hide + Move Silently). Not the 5e skill name. Acceptable usage. |

### 4.3 Findings in Documentation

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| S-3 | `docs/research/RQ_VOICE_001_BENCHMARK_RESULTS.md` | 198 | `"Your stealth check fails. The sentry turns toward you."` | **WARNING** | TTS benchmark sample sentence uses "stealth check" -- a 5e term. In 3.5e, this should be "Hide check" or "Move Silently check". This is an example sentence for TTS testing, not mechanical code, but it normalizes 5e terminology in narration output. |
| S-4 | `docs/design/BATTLE_MAP_AND_ENVIRONMENTAL_PHYSICS.md` | 216 | `The Box must check LoS for every attack, spell targeting, and perception check` | **WARNING** | Uses "perception check" instead of "Spot check" or "Listen check". |
| S-5 | `docs/research/findings/RQ_NARR_001_B_TEMPLATES_AND_CONFIRMATION.md` | 1078 | `Tumble check: Acrobatics check to avoid AoO (DC 15)` | **CONTAMINATED** | Describes a "Tumble check" then immediately calls it an "Acrobatics check" -- "Acrobatics" is the 5e skill that replaced Tumble and Balance. The correct 3.5e term is "Tumble check". |
| S-6 | `docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md` | 305-306 | `Hide/Move Silently -- stealth with opposed checks` / `Spot/Listen -- perception with opposed checks` | CLEAN | Uses correct 3.5e skill names. The lowercase "stealth" and "perception" are category descriptors, not skill names. |
| S-7 | `pm_inbox/reviewed/OPUS_WO-035_SKILL_SYSTEM_DISPATCH.md` | 38 | `Hide \| ... \| stealth in/before combat` | CLEAN | Correct skill name (Hide), lowercase "stealth" is a category description. |

### 4.4 Skill Naming Summary

The skill system code correctly uses 3.5e names (Hide, Move Silently, Spot, Listen, Tumble, Balance). However, documentation and example text sometimes uses 5e-esque terms ("perception check", "stealth check", "Acrobatics check"). The most concerning is S-5, which explicitly calls a Tumble check an "Acrobatics check" -- the 5e replacement skill name.

**Recommended fixes:**
- S-1: Change to "No Spot/Listen checks (deferred)"
- S-3: Change sample sentence to `"Your Hide check fails. The sentry turns toward you."`
- S-4: Change to "Spot/Listen check"
- S-5: Change "Acrobatics check" to "Tumble check"

---

## 5. Action Economy Audit

### 5.1 Findings in Production Code

No occurrences of "bonus action" were found in any production code under `aidm/`.
No occurrences of "reaction" (as a 5e action economy term) were found in production code.

### 5.2 Findings in Tests

No occurrences of "bonus action" or "reaction" (as 5e terms) in tests.

### 5.3 Findings in Documentation

| # | File | Line | Text | Classification | Notes |
|---|------|------|------|----------------|-------|
| A-1 | `docs/CP18A_RULES_COVERAGE_LEDGER.md` | 238, 244, 331, 376 | `Feat reaction system`, `Mounted Combat feat reaction`, `Mounted Combat feat (reaction)` | CLEAN | These refer to the Mounted Combat feat's triggered ability (negate a hit on mount with a Ride check, once per round). In 3.5e, this is an "immediate" or "triggered" ability -- the word "reaction" here describes a generic game concept, not the 5e action type. However, the consistent pairing with "system" language could be confusing. |
| A-2 | `docs/CP18A_MOUNTED_COMBAT_DECISIONS.md` | 60, 86, 1053 | `Mounted Combat feat reaction is OUT`, `Negate mount hit with Ride check (reaction)` | CLEAN (borderline) | Same as A-1. The word "reaction" describes the feat's triggered ability, not a 5e action type. But the parenthetical `(reaction)` could be misread as 5e terminology. |
| A-3 | `docs/TIER1_EXHAUSTION_ANALYSIS.md` | 62 | `Reaction timing polish` | CLEAN (borderline) | Refers to triggered ability timing in general, not 5e reaction action. |
| A-4 | `docs/planning/GPT_RESEARCH_SYNTHESIS_ACTION_PLAN.md` | 170 | `bonus action/reaction` | CLEAN | Part of the contamination audit specification itself. |

### 5.4 Action Economy Summary

The codebase does **not** use "bonus action" or "reaction" as 5e mechanical terms. All uses of "reaction" in docs refer to the general concept of a triggered ability (like the Mounted Combat feat). The correct 3.5e terms for the action economy (standard action, move action, full-round action, swift action, immediate action, free action) are not yet extensively present in code either, since the action economy system is not yet fully implemented.

**Recommended clarification:**
- A-1 / A-2: Consider changing "reaction" to "triggered ability" or "immediate ability" to avoid ambiguity with 5e terminology. E.g., `Mounted Combat feat triggered ability` instead of `Mounted Combat feat reaction`.

---

## Contamination Glossary

| 5e Term | Correct 3.5e Term | Notes |
|---------|--------------------|-------|
| Cantrip (at-will) | 0-level spell (consumes spell slot) | "Cantrip" is acceptable as a flavor synonym for arcane 0-level spells per PHB p.305, but must NOT imply at-will casting |
| Concentration (one spell limit) | Concentration (duration type, no limit on simultaneous spells) | 3.5e: Concentration is a skill check (DC 10+damage) AND a spell duration type. No global limiter. |
| Short rest | Does not exist in 3.5e | Use "8-hour rest" or "overnight rest" |
| Long rest | Does not exist in 3.5e | Use "full day bed rest" or "complete bed rest" |
| Hit dice (healing resource) | Hit dice (creature type only) | 3.5e HD determine HP, BAB, saves -- NOT a rest healing resource |
| Perception (skill) | Spot (WIS) + Listen (WIS) | Two separate skills in 3.5e |
| Stealth (skill) | Hide (DEX) + Move Silently (DEX) | Two separate skills in 3.5e |
| Athletics (skill) | Climb (STR) + Jump (STR) + Swim (STR) | Three separate skills in 3.5e |
| Acrobatics (skill) | Tumble (DEX) + Balance (DEX) | Two separate skills in 3.5e |
| Bonus action | Swift action (3.5e, 1/round) | 3.5e swift actions are similar but not identical |
| Reaction | Immediate action (3.5e, 1/round, uses next swift) | 3.5e immediate actions can be taken off-turn but consume next turn's swift action |
| Advantage / Disadvantage | Circumstance bonuses/penalties (+2/-2 typical) | Does not exist in 3.5e |
| Proficiency bonus | Base Attack Bonus (BAB) + feat/class bonuses | 3.5e has no unified "proficiency" mechanic |
| Death saving throws | Negative HP tracking (-1 to -9 dying, -10 = death) | 3.5e has no death saves |

---

## Severity Summary

| Classification | Count | Description |
|----------------|-------|-------------|
| **CONTAMINATED** | 1 instance (5 code locations) | DurationTracker one-concentration-per-caster limiter (CON-1 through CON-5) |
| **CONTAMINATED** | 1 instance (1 doc location) | "Acrobatics check" used for Tumble check (S-5) |
| **WARNING** | 9 instances | "Cantrip" terminology in code/tests/docs (C-1 through C-6, C-11 through C-14), "long_rest" string (R-3), "perception check" in docs (S-1, S-4), "stealth check" in docs (S-3) |
| **CLEAN** | 18 instances | Correct 3.5e usage or anti-contamination guards |

---

## Priority Recommendations

### P0 -- Fix Immediately (Mechanical 5e Rule in Code)
1. **CON-1 through CON-5**: Rewrite DurationTracker to allow multiple concentration-duration spells per caster. The `_concentration: Dict[str, str]` data structure enforces 5e's "one concentration spell at a time" rule. In 3.5e, there is no such limit. This requires structural changes to the DurationTracker and its callers.

### P1 -- Fix Before Next Implementation Sprint (Terminology)
2. **S-5**: Change "Acrobatics check" to "Tumble check" in `docs/research/findings/RQ_NARR_001_B_TEMPLATES_AND_CONFIRMATION.md` line 1078.
3. **C-1, C-2**: Change code comments from "Cantrips" to "0-level spells".
4. **C-3 through C-6**: Rename test function/variable/docstring from "cantrip" to "level_0_spell".

### P2 -- Fix When Touching These Files (Low Risk)
5. **C-11 through C-14**: Update doc references from "cantrips" to "0-level spells".
6. **R-3**: Change `reason="long_rest"` to `reason="overnight_rest"` in test_time.py.
7. **S-1, S-3, S-4**: Change "perception check" and "stealth check" to 3.5e equivalents.
8. **A-1, A-2**: Consider changing "reaction" to "triggered ability" in mounted combat docs.

---

*End of audit. This document is a snapshot -- findings should be re-verified after any fixes are applied.*
