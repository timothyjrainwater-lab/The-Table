# DEBRIEF: AUDIT-WO-001 — Attack Modifier Pipeline Audit (20+ Mechanics)
**From:** Builder (Opus 4.6)
**Date:** 2026-02-27
**Status:** Complete
**Lifecycle:** NEW

---

## Pass 1: Full Context Dump

### Scope
Comprehensive audit of all attack modifier mechanics across the engine's attack resolution pipeline. Covers `resolve_attack()` (single attack), `resolve_full_attack()` (iterative), `resolve_nonlethal_attack()`, `resolve_charge()`, `resolve_natural_attack()`, and all supporting subsystems.

### Files Read

| File | Lines | Purpose |
|------|-------|---------|
| `aidm/core/attack_resolver.py` | 1–1382 | Single attack, charge, nonlethal resolution |
| `aidm/core/full_attack_resolver.py` | 1–1121 | Full attack / iterative / TWF / GTWF |
| `aidm/core/feat_resolver.py` | 1–440 | Feat-based attack/damage/AC modifiers |
| `aidm/core/natural_attack_resolver.py` | 1–182 | Natural attack delegation + Multiattack + INA |
| `aidm/core/conditions.py` | 1–200 | Condition modifier aggregation |
| `aidm/schemas/conditions.py` | (full) | 24 canonical conditions with modifiers |
| `aidm/schemas/entity_fields.py` | 1–354 | All EF constants |
| `aidm/schemas/attack.py` | (full) | Weapon, AttackIntent, NonlethalAttackIntent |
| `aidm/core/condition_combat_resolver.py` | (full) | Blinded/deafened/entangled combat effects |
| `aidm/core/sneak_attack.py` | (full) | Precision damage eligibility + dice |
| `aidm/core/flanking.py` | (full) | Flanking detection + bonus |
| `aidm/core/concealment.py` | (full) | Miss chance resolution |
| `aidm/core/mounted_combat.py` | (full) | Mounted higher ground bonus |
| `aidm/core/damage_reduction.py` | (full) | DR application |
| `aidm/core/terrain_resolver.py` | (full) | Higher ground, cover |
| `aidm/core/feint_resolver.py` | (full) | Feint flat-footed marker |
| `aidm/core/dying_resolver.py` | (full) | Death/dying transitions |
| `docs/RAW_FIDELITY_AUDIT.md` | (full) | Mechanic coverage status |

---

### Section A: Attack Modifier Catalog (30 Mechanics Audited)

#### A1. Attack Roll Modifiers — `resolve_attack()` (Single Attack)

| # | Mechanic | Value | PHB Ref | Code Location | Status |
|---|----------|-------|---------|---------------|--------|
| 1 | BAB + STR_MOD base | intent.attack_bonus | p.134 | attack_resolver.py:639 | FULL |
| 2 | Condition attack modifier | varies | p.307-315 | attack_resolver.py:641 | FULL |
| 3 | Mounted higher ground | +1 melee | p.157 | attack_resolver.py:426,642 | FULL |
| 4 | Terrain higher ground | +1 melee | p.151 | attack_resolver.py:430,643 | FULL |
| 5 | Feat attack modifier (WF/PBS/PA/RS) | varies | p.96,97,98,99 | attack_resolver.py:466,644 | FULL |
| 6 | Flanking | +2 melee | p.153 | attack_resolver.py:503,645 | DEGRADED (angle heuristic) |
| 7 | Negative Levels | -1/level | p.215 | attack_resolver.py:646 | FULL |
| 8 | Fight Defensively attack penalty | -4 | p.142 | attack_resolver.py:597,647 | FULL |
| 9 | Weapon Broken penalty | -2 | p.155 | attack_resolver.py:422,648 | FULL |
| 10 | +2 vs Blinded defender | +2 | p.309 | attack_resolver.py:572,649 | FULL |
| 11 | Inspire Courage morale bonus | +1 to +4 | p.29 | attack_resolver.py:599-601,650 | FULL |
| 12 | Favored Enemy | +2/+4/+6/... | p.47 | attack_resolver.py:605-612,651 | FULL |
| 13 | Weapon Enhancement bonus | +1 to +5 | p.224 | attack_resolver.py:652 | FULL |
| 14 | Weapon Finesse DEX delta | DEX-STR | p.102 | attack_resolver.py:617-621,653 | FULL |
| 15 | Combat Expertise attack penalty | -1 to -5 | p.92 | attack_resolver.py:654 | FULL |
| 16 | Weapon Proficiency | -4 if non-prof | p.113 | attack_resolver.py:655 | FULL |
| 17 | Precise Shot / ranged-into-melee | -4 / negated | p.140,99 | attack_resolver.py:625-637,656 | FULL |
| 18 | Charge bonus | +2 | p.150 | attack_resolver.py:1447 | FULL |

#### A2. AC Modifiers on Defender — `resolve_attack()` (Single Attack)

| # | Mechanic | Value | PHB Ref | Code Location | Status |
|---|----------|-------|---------|---------------|--------|
| 19 | Base AC | EF.AC | p.136 | attack_resolver.py:514 | FULL |
| 20 | Condition AC (melee/ranged split) | varies | p.307-315 | attack_resolver.py:523-528 | FULL |
| 21 | Cover AC bonus | +4/+4 | p.150 | attack_resolver.py:568 | FULL |
| 22 | DEX denial (flat-footed/stunned/etc.) | -DEX_MOD | p.311 | attack_resolver.py:517-521 | FULL |
| 23 | Uncanny Dodge DEX retention | bypasses denial | p.51,47,26 | attack_resolver.py:280-304,518 | FULL |
| 24 | Fight Defensively AC bonus | +2 | p.142 | attack_resolver.py:531-532 | FULL |
| 25 | Total Defense AC bonus | +4 | p.142 | attack_resolver.py:532-533 | FULL |
| 26 | Two-Weapon Defense AC | +1/+2/+3 | p.102 | attack_resolver.py:537 | FULL |
| 27 | Combat Expertise dodge AC | +1/+2 | p.92 | attack_resolver.py:540 | FULL |
| 28 | Monk WIS AC bonus | WIS_MOD | p.41 | attack_resolver.py:556-562 | FULL |
| 29 | Deflection bonus | varies | p.136 | attack_resolver.py:566 | FULL |
| 30 | Feint denied-DEX consumption | loses Dex | p.76 | attack_resolver.py:543-552 | FULL |

#### A3. Damage Modifiers — `resolve_attack()` (Single Attack)

| # | Mechanic | Value | PHB Ref | Code Location | Status |
|---|----------|-------|---------|---------------|--------|
| 31 | STR-to-damage (grip: 1/1.5/0.5) | STR_MOD * mult | p.113 | attack_resolver.py:823-830 | FULL |
| 32 | Weapon damage bonus | weapon.damage_bonus | p.113 | attack_resolver.py:832 | FULL |
| 33 | Weapon Enhancement bonus (pre-crit) | +1 to +5 | p.224 | attack_resolver.py:832 | FULL |
| 34 | Condition damage modifier | varies | p.307 | attack_resolver.py:839 | FULL |
| 35 | Feat damage modifier (WS/PBS/PA) | varies | p.96-98 | attack_resolver.py:839 | FULL |
| 36 | Inspire Courage damage bonus | +1 to +4 | p.29 | attack_resolver.py:835-838,839 | FULL |
| 37 | Critical multiplier | ×2/×3/×4 | p.140 | attack_resolver.py:843 | FULL |
| 38 | Improved Critical threat range | doubled | p.96 | attack_resolver.py:668-672 | FULL |
| 39 | Favored Enemy damage (post-crit) | +2/+4/... | p.47 | attack_resolver.py:848 | FULL |
| 40 | Sneak Attack (post-crit) | +Xd6 | p.50 | attack_resolver.py:853-859 | FULL |
| 41 | Damage Reduction | -X post-crit | p.291 | attack_resolver.py:867-876 | FULL |
| 42 | Massive Damage Fort save | DC 15 at 50+ | p.145 | attack_resolver.py:935-961 | FULL |

#### A4. Other Attack Subsystems

| # | Mechanic | Value | PHB Ref | Code Location | Status |
|---|----------|-------|---------|---------------|--------|
| 43 | Concealment miss chance | 0-100% d100 | p.152 | attack_resolver.py:747-791 | FULL |
| 44 | Blind-Fight reroll | one reroll | p.91 | attack_resolver.py:752-772 | FULL |
| 45 | Blinded attacker 50% miss | d100 | p.309 | attack_resolver.py:576-589 | FULL |
| 46 | Helpless auto-hit (melee) | auto-hit | p.153 | attack_resolver.py:509-511,681 | FULL |
| 47 | Natural 20/1 rules | auto-hit/miss | p.140 | attack_resolver.py:682-687 | FULL |
| 48 | Disarmed guard | blocks attack | p.155 | attack_resolver.py:406-419 | FULL |
| 49 | Equipment Melded guard | blocks weapon | p.36 | attack_resolver.py:384-398 | FULL |
| 50 | Charge -2 AC penalty | TEMP_MOD | p.150 | attack_resolver.py:1397+ | FULL |
| 51 | Spirited Charge multiplier | ×2/×3 | p.100 | attack_resolver.py:1490-1497 | FULL |
| 52 | Nonlethal -4 attack penalty | -4 | p.146 | attack_resolver.py:1104 | FULL |

---

### Section B: CRITICAL FINDING — `resolve_full_attack()` Modifier Divergence

**FINDING-AUDIT-FULL-ATTACK-MODIFIER-DRIFT-001 — SEVERITY: HIGH**

`resolve_full_attack()` in `full_attack_resolver.py` has **drifted significantly** from `resolve_attack()`. The full attack path uses its own `resolve_single_attack_with_critical()` function which does NOT call `resolve_attack()`. As WOs added modifiers to `resolve_attack()`, they were NOT propagated to the full attack path.

#### B1. Attack Roll Modifiers MISSING from full_attack_resolver

| # | Mechanic | PHB | In resolve_attack | In resolve_full_attack | Gap |
|---|----------|-----|-------------------|----------------------|-----|
| 1 | Inspire Courage attack bonus | p.29 | Lines 599-601 | **ABSENT** | MISSING |
| 2 | Weapon Finesse DEX delta | p.102 | Lines 617-621 | **ABSENT** | MISSING |
| 3 | Negative Levels -1/level | p.215 | Line 646 | **ABSENT** | MISSING |
| 4 | Fight Defensively attack penalty | p.142 | Lines 596-597 | **ABSENT** | MISSING |
| 5 | Weapon Broken -2 | p.155 | Line 648 | **ABSENT** | MISSING |
| 6 | +2 vs Blinded defender | p.309 | Lines 571-572 | **ABSENT** | MISSING |
| 7 | Blinded attacker 50% miss | p.309 | Lines 576-589 | **ABSENT** | MISSING |
| 8 | Combat Expertise attack penalty | p.92 | Line 654 | **ABSENT** | MISSING |
| 9 | Precise Shot / ranged-into-melee | p.140,99 | Lines 625-637 | **ABSENT** | MISSING |

#### B2. AC Modifiers MISSING from full_attack_resolver target_ac computation

The full_attack_resolver's target_ac is `base_ac + condition_ac + cover_result.ac_bonus` (line 659). Missing:

| # | Mechanic | PHB | In resolve_attack | In resolve_full_attack | Gap |
|---|----------|-----|-------------------|----------------------|-----|
| 10 | DEX denial + Uncanny Dodge check | p.51,311 | Lines 517-521 | **ABSENT** | MISSING |
| 11 | Fight Defensively/Total Defense AC | p.142 | Lines 530-533 | **ABSENT** | MISSING |
| 12 | Two-Weapon Defense AC | p.102 | Line 537 | **ABSENT** | MISSING |
| 13 | Combat Expertise dodge AC on target | p.92 | Line 540 | **ABSENT** | MISSING |
| 14 | Monk WIS AC bonus | p.41 | Lines 556-562 | **ABSENT** | MISSING |
| 15 | Deflection Bonus | p.136 | Line 566 | **ABSENT** | MISSING |
| 16 | Feint marker consumption | p.76 | Lines 543-552 | **ABSENT** | MISSING |

#### B3. Damage Modifiers MISSING from full_attack_resolver

| # | Mechanic | PHB | In resolve_attack | In resolve_full_attack | Gap |
|---|----------|-----|-------------------|----------------------|-----|
| 17 | Inspire Courage damage bonus | p.29 | Lines 835-838 | **ABSENT** | MISSING |

#### B4. Guard Checks MISSING from full_attack_resolver

| # | Mechanic | PHB | In resolve_attack | In resolve_full_attack | Gap |
|---|----------|-----|-------------------|----------------------|-----|
| 18 | Disarmed guard | p.155 | Lines 406-419 | **ABSENT** | MISSING |
| 19 | Equipment Melded guard | p.36 | Lines 384-398 | **ABSENT** | MISSING |

#### B5. Post-Hit Logic MISSING from full_attack_resolver

| # | Mechanic | PHB | In resolve_attack | In resolve_full_attack | Gap |
|---|----------|-----|-------------------|----------------------|-----|
| 20 | Blind-Fight concealment reroll | p.91 | Lines 752-772 | **ABSENT** | MISSING |
| 21 | Massive Damage Fort save | p.145 | Lines 935-961 | **ABSENT (per-hit)** | MISSING |

**Total: 21 modifiers/guards present in resolve_attack() are ABSENT from resolve_full_attack().**

**Root cause:** `resolve_full_attack()` was established at CP-11 and uses its own attack resolution path (`resolve_single_attack_with_critical()`). Subsequent WOs (Batches I through T) added modifiers to `resolve_attack()` but were not required to update the full attack path. The dispatch docs never flagged full_attack_resolver as a second touch site.

**Impact:** Any combat that uses a full attack action (which is the majority of mid-level+ melee rounds) computes attack rolls, target AC, and damage WITHOUT: Inspire Courage, Weapon Finesse, Negative Levels, Fight Defensively, Weapon Broken, Blinded, Combat Expertise, Precise Shot, Uncanny Dodge, Monk WIS AC, Deflection Bonus, TWD AC, Feint, Massive Damage, and guard checks for Disarmed/Equipment Melded. This is a **systemic fidelity gap**.

**Recommended fix direction:** Refactor `resolve_full_attack()` to delegate individual attacks to `resolve_attack()` instead of `resolve_single_attack_with_critical()`. This eliminates the dual-path divergence permanently. Alternatively, systematically port all 21 missing items — but this recreates the drift risk.

---

### Section C: `resolve_nonlethal_attack()` Modifier Gaps

**FINDING-AUDIT-NONLETHAL-MODIFIER-DRIFT-001 — SEVERITY: MEDIUM**

`resolve_nonlethal_attack()` (attack_resolver.py:1071-1283) has its own inline attack resolution. Missing relative to `resolve_attack()`:

| # | Missing Mechanic | PHB |
|---|-----------------|-----|
| 1 | Feat attack modifiers (WF, PBS, PA) | p.96-99 |
| 2 | Feat damage modifiers (WS, PBS, PA) | p.96-99 |
| 3 | Flanking bonus | p.153 |
| 4 | Mounted higher ground bonus | p.157 |
| 5 | Terrain higher ground bonus | p.151 |
| 6 | Cover AC bonus | p.150 |
| 7 | Concealment miss chance | p.152 |
| 8 | Sneak Attack (nonlethal eligible) | p.50 |
| 9 | Damage Reduction | p.146 (debatable) |
| 10 | Inspire Courage | p.29 |
| 11 | Favored Enemy | p.47 |
| 12 | Weapon Enhancement | p.224 |
| 13 | Enhancement to attack bonus | p.224 |
| 14 | Precise Shot / ranged-into-melee | p.140 |
| 15 | Negative Levels | p.215 |
| 16 | Fight Defensively (attack and AC) | p.142 |
| 17 | TWD/CE/Deflection AC on defender | p.102,92,136 |
| 18 | Disarmed / Equipment Melded guards | p.155,36 |

**Root cause:** Same as B — nonlethal was added as a standalone resolver without delegating to `resolve_attack()`.

---

### Section D: Other Subsystem Findings

| ID | Severity | Status | Finding |
|----|----------|--------|---------|
| FINDING-AUDIT-TUMBLE-FIGHT-DEFENSIVELY-001 | LOW | OPEN | Fight Defensively with 5+ Tumble ranks should grant +3 AC (not +2). Total Defense with 5+ Tumble should grant +6 (not +4). PHB p.142. Not implemented. |
| FINDING-AUDIT-IMPROVED-FEINT-001 | LOW | OPEN | Improved Feint feat (feint as move action, PHB p.95) not implemented. Feint always standard action. |
| FINDING-AUDIT-FLANKING-GEOMETRY-001 | LOW | OPEN (existing) | Flanking uses 135° heuristic, PHB requires line through opposite corners/sides. RAW_FIDELITY_AUDIT.md marks as DEGRADED. |
| FINDING-AUDIT-KI-STRIKE-DR-001 | LOW | OPEN | Monk Ki Strike (magic fists at L4, PHB p.41) not recognized by DR resolver — natural attacks hardcoded as non-magic. |
| FINDING-AUDIT-SNEAK-BARE-KEY-001 | LOW | OPEN | `sneak_attack.py` line ~86 uses bare string `"precision_damage_dice"` instead of EF constant. CLAUDE.md Rule 1 violation. |
| FINDING-AUDIT-FATIGUED-STR-FLAT-001 | LOW | OPEN | Fatigued/Exhausted approximate STR penalty as flat -1/-3 attack/damage rather than computing from actual ability score reduction. Loses fidelity at high STR. |
| FINDING-AUDIT-MOUNTED-COMBAT-FEAT-001 | LOW | OPEN | Mounted Combat feat (negate hit with Ride check, PHB p.98) not implemented. Ride modifier hardcoded as 5. |
| FINDING-AUDIT-PA-2H-DEVIATION-001 | LOW | OPEN (existing) | Power Attack 2H at 1.5× (spec) vs PHB 2×. Tracked by FINDING-ENGINE-PA-2H-PHB-DEVIATION-001. Thunder decision pending. |

---

## Pass 2: PM Summary (≤100 words)

**Audit identified a CRITICAL systematic gap:** `resolve_full_attack()` is missing 21 modifiers/guards that `resolve_attack()` has — including Inspire Courage, Weapon Finesse, Negative Levels, Fight Defensively, Uncanny Dodge, Monk WIS AC, Deflection Bonus, Feint, and Massive Damage. Root cause: full attack path diverged at CP-11 and was never synchronized as subsequent WOs added modifiers. `resolve_nonlethal_attack()` has a similar but less severe drift (18 missing). The single-attack path (`resolve_attack()`) is fully wired with 52 mechanics across 30+ WOs. Recommended fix: refactor full attack to delegate to resolve_attack.

---

## Pass 3: Retrospective

### Drift Caught
The full_attack_resolver drift was NOT caught by any prior WO debrief or audit. Each WO that added modifiers to resolve_attack() was scoped to "single attack resolution" and the dispatch never required touching resolve_full_attack. The integration seams section of dispatch docs should list ALL attack resolution paths (single, full, nonlethal, natural, charge) and require the builder to verify parity.

### Pattern: Dual-Path Divergence
This is a known architectural anti-pattern: two code paths that should produce identical results but are maintained independently. The `resolve_single_attack_with_critical()` function is a copy of resolve_attack()'s logic, not a delegation to it. Every modifier added to one must be manually added to the other — and that manual sync has failed 21 times.

### Recommendation
1. **WO-ENGINE-FULL-ATTACK-UNIFY-001** (HIGH priority): Refactor `resolve_full_attack()` to build AttackIntents and delegate each to `resolve_attack()`. Eliminates the dual-path entirely. Estimated scope: ~200 lines refactored, all existing gate tests should pass unchanged.
2. **WO-ENGINE-NONLETHAL-UNIFY-001** (MEDIUM priority): Same treatment for nonlethal.
3. **Dispatch doctrine update**: Every future engine WO that touches attack modifiers must list "Attack Resolution Paths" in the dispatch Integration Seams section and require parity verification.

### Kernel Touches
This audit touches **KERNEL-01 (Entity Lifecycle Ontology)** — the divergence means entities behave differently under full attack vs single attack for conditions, death transitions, and modifier application. Also touches **KERNEL-08 (Resolution Granularity)** — the per-attack vs per-full-attack granularity of massive damage, Blind-Fight rerolls, and feint consumption.

---

## Radar: Open Findings

| ID | Severity | Status | Summary |
|----|----------|--------|---------|
| **FINDING-AUDIT-FULL-ATTACK-MODIFIER-DRIFT-001** | **HIGH** | **OPEN** | 21 modifiers/guards in resolve_attack() absent from resolve_full_attack() |
| **FINDING-AUDIT-NONLETHAL-MODIFIER-DRIFT-001** | **MEDIUM** | **OPEN** | 18 modifiers/guards missing from resolve_nonlethal_attack() |
| FINDING-AUDIT-TUMBLE-FIGHT-DEFENSIVELY-001 | LOW | OPEN | Tumble skill bonus to Fight Defensively/Total Defense not implemented |
| FINDING-AUDIT-IMPROVED-FEINT-001 | LOW | OPEN | Improved Feint feat (move action) not implemented |
| FINDING-AUDIT-FLANKING-GEOMETRY-001 | LOW | OPEN | Flanking simplified angle heuristic vs PHB corner/side rule |
| FINDING-AUDIT-KI-STRIKE-DR-001 | LOW | OPEN | Monk Ki Strike not recognized by DR resolver |
| FINDING-AUDIT-SNEAK-BARE-KEY-001 | LOW | OPEN | Bare string key in sneak_attack.py (EF violation) |
| FINDING-AUDIT-FATIGUED-STR-FLAT-001 | LOW | OPEN | Fatigued/Exhausted STR penalty flat approximation |
| FINDING-AUDIT-MOUNTED-COMBAT-FEAT-001 | LOW | OPEN | Mounted Combat feat not implemented |
| FINDING-AUDIT-PA-2H-DEVIATION-001 | LOW | OPEN | Power Attack 2H 1.5× vs PHB 2× (existing, Thunder decision pending) |
