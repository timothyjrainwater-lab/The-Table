# WO-SPARK-RV007-001: Forbidden Meta-Game Claims Detection

**Classification:** CODE (implementation — new validator rule + fuzz regression suite)
**Priority:** HIGH — next in queue. Core promise breach if unresolved.
**Dispatched by:** Slate (PM)
**Date:** 2026-02-22
**Assigned to:** Builder
**Origin:** FINDING-HOOLIGAN-02 (Anvil, WO-SPARK-EXPLORE-001) + Aegis Audit (ACCEPT with HIGH risk)

---

## Context

The NarrationValidator catches structural contradictions — wrong hit/miss, wrong defeat state, wrong save result, wrong condition. It does NOT catch **forbidden meta-game content**: damage numbers, HP values, dice rolls, AC references, DC values, rulebook citations. Anvil's hooligan run proved this: "deals 14 damage" returns PASS, "(42 HP remaining)" returns PASS, "rolled a 19" returns PASS.

This is a core promise breach. The Spark contract says narration NEVER mints mechanics. The validator is the enforcement mechanism. Without this rule, the validator has a blind spot exactly where the highest-severity violation would occur.

The Typed Call Contract (`docs/contracts/TYPED_CALL_CONTRACT.md`) already specifies the exact regex patterns (MV-01 through MV-09, RC-01 through RC-04). This WO implements those patterns in the validator and adds a permanent fuzz regression suite.

---

## Objective

1. Add a new P0 FAIL rule to `NarrationValidator` that detects forbidden meta-game claims
2. Add a second P0 FAIL rule for rulebook citations
3. Fix FINDING-HOOLIGAN-01: condition keyword underscore normalization in RV-004
4. Write gate tests that permanently guard against regression
5. Convert Anvil's FUZZ-01 through FUZZ-03 into permanent test fixtures

---

## Scope

### IN SCOPE

1. **New rule: `_check_rv009_forbidden_claims()`** in `aidm/narration/narration_validator.py`
   - Rule ID: `RV-009` (new slot — do NOT renumber existing RV-007)
   - Severity: **FAIL** (P0 — forces template fallback)
   - Always active (not dormant, not Layer B)
   - Patterns: MV-01 through MV-09 from Typed Call Contract Section 3.1
   - On match: return `RuleViolation(rule_id="RV-009", severity="FAIL", detail=...)`
   - Detail must include the pattern ID (e.g., "MV-01") and the matched text

2. **New rule: `_check_rv010_rule_citations()`** in `aidm/narration/narration_validator.py`
   - Rule ID: `RV-010` (new slot)
   - Severity: **FAIL** (P0)
   - Always active
   - Patterns: RC-01 through RC-04 from Typed Call Contract Section 3.2
   - Same violation format as RV-009

3. **Fix: RV-004 underscore normalization** (FINDING-HOOLIGAN-01)
   - In `_check_rv004_condition()`, normalize condition names by replacing underscores with spaces before keyword matching
   - e.g., `mummy_rot` → `mummy rot` so it matches the narration text "mummy rot"

4. **Wire new rules into `validate()`**
   - Add `_check_rv009_forbidden_claims()` to P0 section (after RV-005, before P1)
   - Add `_check_rv010_rule_citations()` to P0 section (after RV-009)

5. **Gate tests: `tests/test_forbidden_claims_p.py`** — Gate P
   - See Gate Tests section below

### OUT OF SCOPE

- No changes to `guarded_narration_service.py` (already forces fallback on FAIL — wiring is free)
- No changes to `contradiction_checker.py`
- No changes to the Typed Call Contract (patterns already specified)
- No changes to RV-001 compound narration false positive (FINDING-HOOLIGAN-03 — separate WO, needs contract decision)
- No changes to stop sequences, model config, or adapter
- No changes to existing test files

---

## Design Decisions (PM-resolved)

| # | Decision | Resolution | Rationale |
|---|----------|------------|-----------|
| DD-01 | New rule ID or repurpose RV-007? | **New: RV-009 + RV-010.** Existing RV-007 (delivery mode) stays untouched. | Renaming breaks existing test references and log analysis. New IDs are clean. |
| DD-02 | FAIL or WARN severity? | **FAIL.** Hard stop, template fallback. | Aegis recommendation. This is the one violation that must never reach the user. |
| DD-03 | Run on all narrations or only specific CallTypes? | **All narrations.** No CallType filter. | Forbidden claims are forbidden in ALL narration, not just COMBAT_NARRATION. |
| DD-04 | Match on lowered text or case-sensitive? | **Case-insensitive.** Patterns compiled with `re.IGNORECASE`. | "AC 18", "ac 18", "Ac 18" are all forbidden. |
| DD-05 | One violation per pattern or one per category? | **One violation per matched pattern.** No early break — report all matches. | Multiple forbidden claims in one narration means the model is badly misbehaving. Report everything for diagnostic value. |
| DD-06 | Include Aegis's additional patterns beyond MV-01..MV-09? | **No.** Stick to contract patterns only. | Contract is the source of truth. Aegis patterns overlap but use different syntax. Builder uses the contract. |

---

## Patterns (from Typed Call Contract Section 3.1-3.2)

### Mechanical Values (MV-01 through MV-09)

| ID | Pattern | Catches |
|----|---------|---------|
| MV-01 | `\b\d+\s*(points?\s+of\s+)?damage\b` | "14 damage", "14 points of damage" |
| MV-02 | `\bAC\s*\d+\b` | "AC 18", "AC18" |
| MV-03 | `\b\d+\s*h(it\s*)?p(oints?)?\b` | "42 HP", "42 hit points", "42 hp" |
| MV-04 | `[+-]\d+\s*(to\s+)?(attack\|hit)\b` | "+7 to hit", "+5 attack" |
| MV-05 | `\bDC\s*\d+\b` | "DC 15", "DC15" |
| MV-06 | `\broll(ed)?\s+(a\s+)?\d+\b` | "rolled a 19", "roll 17" |
| MV-07 | `\b\d+d\d+` | "2d6", "1d8", "10d6" |
| MV-08 | `\b\d+\s*(?:feet\|ft\.?\|squares?)\s+(?:of\s+)?(?:movement\|range\|reach)\b` | "30 feet of movement", "5 ft range" |
| MV-09 | `\bnatural\s+\d+\b` | "natural 20", "natural 1" |

### Rule Citations (RC-01 through RC-04)

| ID | Pattern | Catches |
|----|---------|---------|
| RC-01 | `\b(PHB\|DMG\|MM)\s*\d+` | "PHB 145", "DMG 34", "MM 203" |
| RC-02 | `\b(page\|pg\.?\|p\.)\s*\d+\b` | "page 145", "pg. 34", "p. 203" |
| RC-03 | `\bper\s+the\s+\w+\s+rules\b` | "per the grapple rules" |
| RC-04 | `\brules?\s+(as\s+written\|state\|say)\b` | "rules as written", "rule states" |

**Builder note:** These patterns are copied verbatim from the contract. The `\|` in the markdown table is a literal pipe in the regex (alternation). When compiling, use raw strings and standard `|` for alternation.

---

## Gate Tests (`tests/test_forbidden_claims_p.py`)

### P-01: FUZZ-01 Reproduction — Damage Number
- Narration: "Kael's longsword slashes through, dealing 14 damage to the goblin."
- Brief: standard melee hit
- **ASSERT:** verdict == "FAIL", any violation has rule_id == "RV-009"

### P-02: FUZZ-02 Reproduction — HP Reference
- Narration: "The goblin staggers back (42 HP remaining), clutching its wound."
- Brief: standard melee hit
- **ASSERT:** verdict == "FAIL", any violation has rule_id == "RV-009"

### P-03: FUZZ-03 Reproduction — Die Roll Result
- Narration: "Kael rolled a 19, his blade finding its mark in the goblin's side."
- Brief: standard melee hit
- **ASSERT:** verdict == "FAIL", any violation has rule_id == "RV-009"

### P-04: MV-02 — AC Reference
- Narration: "The strike pierces the goblin's AC 16 armor."
- **ASSERT:** verdict == "FAIL", MV-02 matched

### P-05: MV-05 — DC Reference
- Narration: "Seraphine's spell (DC 15) overwhelms the bandit's will."
- **ASSERT:** verdict == "FAIL", MV-05 matched

### P-06: MV-07 — Dice Notation
- Narration: "The fireball erupts, dealing 8d6 fire across the chamber."
- **ASSERT:** verdict == "FAIL", MV-07 matched

### P-07: MV-09 — Natural 20
- Narration: "With a natural 20, Kael's blade finds the perfect gap in the armor."
- **ASSERT:** verdict == "FAIL", MV-09 matched

### P-08: MV-04 — Attack Bonus
- Narration: "Kael swings with +7 to hit, his longsword a blur of steel."
- **ASSERT:** verdict == "FAIL", MV-04 matched

### P-09: MV-08 — Distance/Range
- Narration: "The goblin retreats 30 feet of movement back toward the cave."
- **ASSERT:** verdict == "FAIL", MV-08 matched

### P-10: RC-01 — Rulebook Citation
- Narration: "As described in PHB 154, the charge carries Kael forward."
- **ASSERT:** verdict == "FAIL", any violation has rule_id == "RV-010"

### P-11: RC-03 — Rule Reference Phrasing
- Narration: "Per the grapple rules, the goblin is pinned."
- **ASSERT:** verdict == "FAIL", rule_id == "RV-010"

### P-12: RC-04 — RAW Assertion
- Narration: "The rules as written state the attack provokes."
- **ASSERT:** verdict == "FAIL", rule_id == "RV-010"

### P-13: Clean Narration — No False Positives
- Narration: "Kael's longsword slices through the goblin's armor, sending sparks flying. The creature staggers back, its green skin marred by a deep gash."
- Brief: standard melee hit
- **ASSERT:** verdict != "FAIL" (may be PASS or WARN from other rules, but NOT FAIL from RV-009/RV-010)

### P-14: Clean Narration With Numbers — No False Positives on Prose Numbers
- Narration: "Three goblins surround Kael. The first lunges, but Kael's blade is faster."
- **ASSERT:** verdict != "FAIL" from RV-009/RV-010
- Prose numbers ("three") and digits not coupled to mechanics keywords must not trigger.

### P-15: Multiple Violations — All Reported
- Narration: "Kael rolled a 19, dealing 14 damage to the goblin (42 HP remaining)."
- **ASSERT:** verdict == "FAIL"
- **ASSERT:** len([v for v in violations if v.rule_id == "RV-009"]) >= 3
- Three MV patterns should match: MV-01 (damage), MV-03 (HP), MV-06 (rolled)

### P-16: RV-004 Underscore Fix — Condition Keyword Normalization
- Narration: "Seraphine's holy light banishes the mummy rot from Grunk's skin."
- Brief: condition_applied = "mummy_rot", condition_removed = True
- **ASSERT:** No RV-004 WARN (the underscore normalization should make "mummy_rot" match "mummy rot")

### P-17: MV-03 Variant — "hit points" with space
- Narration: "The goblin has only 12 hit points left."
- **ASSERT:** verdict == "FAIL", MV-03 matched

### P-18: Existing Rules Still Work — No Regression
- Run the 3 baseline Hooligan scenarios (H-01 melee hit, H-02 miss, H-03 kill shot) with clean narrations
- **ASSERT:** All PASS (no false positives from new rules)

**Total: 18 gate tests. All green or WO is RED.**

---

## Integration Seams

| Seam | Module | What Changes |
|------|--------|-------------|
| Validator | `aidm/narration/narration_validator.py` | Add `_check_rv009_forbidden_claims()`, `_check_rv010_rule_citations()`, fix `_check_rv004_condition()`, update `validate()` call order, update module docstring rule inventory |
| Tests | `tests/test_forbidden_claims_p.py` | New file: 18 Gate P tests |
| No other files change. | | |

---

## Research Sources

Builder should read:

1. `aidm/narration/narration_validator.py` — Current validator. Study `_check_rv001_hit_miss()` as pattern for new rules.
2. `docs/contracts/TYPED_CALL_CONTRACT.md` — Section 3.1 (MV patterns), Section 3.2 (RC patterns). **These are the authoritative patterns.**
3. `tests/test_narration_validator.py` — Existing test structure. `MockBrief` fixture pattern.
4. `pm_inbox/reviewed/archive_spark_explore/AEGIS_AUDIT_SPARK_DEBRIEF.md` — Aegis recommended patterns (reference only — use contract patterns).
5. `pm_inbox/reviewed/archive_spark_explore/DEBRIEF_HOOLIGAN_RUN_001.md` — FINDING-HOOLIGAN-02 (the gap), FINDING-HOOLIGAN-01 (underscore fix).

---

## Delivery

### Commit

Single commit. Message: `feat: WO-SPARK-RV007-001 — forbidden claims detection (RV-009/RV-010) + RV-004 fix`

Include: modified `narration_validator.py`, new `tests/test_forbidden_claims_p.py`.

### Debrief

File as `pm_inbox/DEBRIEF_WO-SPARK-RV007-001.md`. Standard CODE WO format:
0. Scope Accuracy
1. Discovery Log
2. Methodology Challenge
3. Field Manual Entry
4. Builder Radar (Trap / Drift / Near stop — 3 lines mandatory)

---

## Builder Radar (from dispatch)

- **Trap.** MV-01 (`\b\d+\s*(points?\s+of\s+)?damage\b`) will match "14 damage" but also "damage" preceded by any digit. Make sure the regex is compiled correctly — the `\b` word boundary prevents partial matches but the pattern allows optional "points of" in the middle. Test "minor damage" does NOT match (no digit).
- **Drift.** These patterns are copied from the Typed Call Contract. If the contract amends MV patterns (adds MV-10 or changes MV-03), this code must be updated in lockstep. There is no automated sync. The same drift risk exists for Tier 1.4's REQUIRED_FIELDS.
- **Near stop.** MV-08 (distance/range) is the most aggressive pattern. "30 feet of movement" is clearly meta-game, but edge cases like "the arrow flies thirty feet" (prose, no digits) should NOT match. Verify MV-08 requires `\d+` (it does) and that prose numbers like "thirty" don't trigger.
