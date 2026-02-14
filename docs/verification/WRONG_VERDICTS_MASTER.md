# WRONG Verdicts Master List — Bone-Layer Verification

**Generated:** 2026-02-14
**Source:** 9 domain verification files (DOMAIN_A through DOMAIN_I)
**Total WRONG verdicts:** 34
**Purpose:** Aggregate all WRONG verdicts for fix WO creation. No code changes — this is a tracking and dispatch artifact.

---

## Summary by Domain

| Domain | WRONG Count | Bugs |
|--------|-------------|------|
| D — Conditions & Modifiers | 8 | BUG-3, BUG-4, BUG-5, BUG-6, BUG-7, + 3 duplicates of BUG-3/4 pattern |
| A — Attack Resolution | 7 | BUG-1, BUG-2, BUG-8, BUG-9, BUG-10 (2 locations each for 8/9/10) |
| B — Combat Maneuvers | 5 | B-BUG-1 through B-BUG-5 |
| C — Saves & Spells | 3 | BUG-C-001, BUG-C-002, BUG-C-003 |
| E — Movement & Terrain | 3 | E-BUG-01, E-BUG-02, E-BUG-03 |
| F — Char Progression | 5 | BUG-F1, BUG-F2, BUG-F3, + 2 sub-bugs in XP table |
| G — Initiative & Turn | 2 | G-PLAY-71-86 (3 entries in 1 table) |
| H — Skill System | 0 | — |
| I — Geometry & Size | 1 | I-GEOM-291 |
| **TOTAL** | **34** | |

---

## Summary by Severity

| Severity | Count | Bug IDs |
|----------|-------|---------|
| HIGH | 8 | BUG-1, BUG-3, BUG-4, BUG-10, B-BUG-2, E-BUG-02, BUG-C-002 (+BUG-C-001/003 same root) |
| MEDIUM | 16 | BUG-2, BUG-5, BUG-6, BUG-7, B-BUG-1, B-BUG-3, B-BUG-5, E-BUG-01, E-BUG-03, BUG-F2, BUG-F3, G-PLAY-71-86 (3 entries), I-GEOM-291 |
| LOW | 6 | BUG-8, BUG-9, B-BUG-4, BUG-F1 |
| TRIVIAL | 2 | BUG-8, BUG-9 fix complexity |

---

## Fix WO Grouping

Bugs are grouped into fix WOs by affected file/subsystem to minimize context switching for builders.

---

### FIX-WO-01: Attack Damage Pipeline (HIGH — 4 bugs, 4 files)

**Bugs:** BUG-1, BUG-8, BUG-9
**Files:** `aidm/core/attack_resolver.py`, `aidm/core/full_attack_resolver.py`
**Effort:** LOW-MEDIUM

| Bug | Location | Fix |
|-----|----------|-----|
| BUG-1 | attack_resolver.py:363, full_attack_resolver.py:297-299 | Add weapon grip detection: `int(str_mod * 1.5)` for two-handed, `int(str_mod * 0.5)` for off-hand, flat `str_mod` for one-handed |
| BUG-8 | attack_resolver.py:369, full_attack_resolver.py:303 | Change `max(0, ...)` to `max(1, ...)` for critical damage path |
| BUG-9 | attack_resolver.py:371, full_attack_resolver.py:305 | Change `max(0, ...)` to `max(1, ...)` for non-critical damage path |

**Test impact:** Existing damage tests will need updated expected values. New tests needed for two-handed and off-hand STR multipliers.

---

### FIX-WO-02: Full Attack Loop Early Termination (MEDIUM — 1 bug, 1 file)

**Bugs:** BUG-2
**Files:** `aidm/core/full_attack_resolver.py`
**Effort:** LOW

| Bug | Location | Fix |
|-----|----------|-----|
| BUG-2 | full_attack_resolver.py:546-590 | Add HP check between iterative attacks. If target HP <= 0 after any attack, break loop. |

**Test impact:** New tests for multi-attack sequences against low-HP targets. Verify accumulated damage stops at defeat.

---

### FIX-WO-03: Condition AC Melee/Ranged Differentiation (HIGH — 2 bugs, 1 file + consumers)

**Bugs:** BUG-3, BUG-4
**Files:** `aidm/schemas/conditions.py`, `aidm/core/attack_resolver.py`, `aidm/core/full_attack_resolver.py`
**Effort:** MEDIUM — requires schema change + consumer updates

| Bug | Location | Fix |
|-----|----------|-----|
| BUG-3 | conditions.py:208 (Prone) | Replace `ac_modifier=-4` with `ac_modifier_melee=-4, ac_modifier_ranged=+4`. Update attack resolvers to select correct modifier based on attack type. |
| BUG-4 | conditions.py:281 (Helpless) | Replace `ac_modifier=-4` with `ac_modifier_melee=-4, ac_modifier_ranged=0`. Same consumer updates as BUG-3. |

**Cascading impact:** Paralyzed and Unconscious conditions (D-AMB-02, D-AMB-03) inherit Helpless behavior and will be fixed by the same schema change.

**Test impact:** All tests using Prone/Helpless AC modifiers need melee vs ranged variants. New tests for Paralyzed/Unconscious ranged AC.

---

### FIX-WO-04: Condition Modifier Gaps (MEDIUM — 3 bugs, 1 file)

**Bugs:** BUG-5, BUG-6, BUG-7
**Files:** `aidm/schemas/conditions.py`
**Effort:** LOW

| Bug | Location | Fix |
|-----|----------|-----|
| BUG-5 | conditions.py:431 (Panicked) | Remove `loses_dex_to_ac=True`. SRD Panicked does not cause loss of Dex to AC. |
| BUG-6 | conditions.py:467 (Fatigued) | Add `damage_modifier=-1` (derived from -2 STR penalty → -1 damage mod) |
| BUG-7 | conditions.py:485 (Exhausted) | Add `damage_modifier=-3` (derived from -6 STR penalty → -3 damage mod) |

**Test impact:** New tests for Panicked Dex-to-AC retention. New tests for Fatigued/Exhausted damage modifiers.

---

### FIX-WO-05: Cover Bonus Values (HIGH — 3 bugs, 1 file)

**Bugs:** BUG-10, BUG-C-001, BUG-C-003
**Files:** `aidm/core/cover_resolver.py`
**Effort:** MEDIUM — design decision needed on cover tier system

| Bug | Location | Fix |
|-----|----------|-----|
| BUG-10 | cover_resolver.py:97-98 | HALF_COVER: change ac=2,ref=1 to ac=4,ref=2. THREE_QUARTERS: change ac=5,ref=2 to ac=7,ref=3. **OR** collapse to SRD two-tier (standard +4/+2, improved +8/+4) and remap thresholds. |
| BUG-C-001 | cover_resolver.py:96-99 | Same root cause as BUG-10. Reflex values are wrong. |
| BUG-C-003 | cover_resolver.py:96-99 | Same root cause as BUG-10. Duplicate entry confirming the values are wrong from save perspective. |

**Design decision required:** SRD has two cover tiers (standard +4/+2, improved +8/+4). Code has four tiers (none, half, three-quarters, total). Options:
- **(a)** Keep 4-tier system, fix values to SRD-adjacent: half=+4/+2, three-quarters=+8/+4 (maps half→standard, three-quarters→improved)
- **(b)** Collapse to SRD 2-tier: standard (+4/+2) and improved (+8/+4) only, plus total

**Test impact:** All cover-related AC and Reflex save tests will need updated expected values.

---

### FIX-WO-06: Concentration DC Formula (HIGH — 1 bug, 2 files)

**Bugs:** BUG-C-002
**Files:** `aidm/core/spell_resolver.py`, `aidm/core/play_loop.py`
**Effort:** LOW

| Bug | Location | Fix |
|-----|----------|-----|
| BUG-C-002 | spell_resolver.py:1035, play_loop.py:618 | Change `DC = 10 + damage_taken` to `DC = 10 + damage_taken + spell_level`. Requires passing spell_level into the concentration check function. |

**Test impact:** All concentration check tests need updated expected DCs. New tests parameterized by spell level.

---

### FIX-WO-07: Combat Maneuver Size Modifiers (MEDIUM — 3 bugs, 1 file)

**Bugs:** B-BUG-1, B-BUG-3, B-BUG-5
**Files:** `aidm/core/maneuver_resolver.py`
**Effort:** LOW

| Bug | Location | Fix |
|-----|----------|-----|
| B-BUG-1 | maneuver_resolver.py:501 | Trip touch attack: use standard attack size modifier, not special size modifier |
| B-BUG-3 | maneuver_resolver.py:1004, 1009 | Sunder opposed rolls: use standard attack size modifier |
| B-BUG-5 | maneuver_resolver.py:1382 | Grapple touch attack: use standard attack size modifier |

**Root cause:** All three bugs are the same pattern — using `special_size_modifier` (for grapple/bull rush/overrun/trip opposed checks) instead of `standard_attack_size_modifier` for the initial touch/attack roll. The initial roll to hit is a standard attack; only the opposed check uses special size modifiers.

**Test impact:** Size modifier tests for trip/sunder/grapple touch attacks.

---

### FIX-WO-08: Overrun Failure Mechanic (HIGH — 1 bug, 1 file)

**Bugs:** B-BUG-2
**Files:** `aidm/core/maneuver_resolver.py`
**Effort:** MEDIUM

| Bug | Location | Fix |
|-----|----------|-----|
| B-BUG-2 | maneuver_resolver.py:859 | Replace flat threshold (margin <= -5) with SRD-mandated separate opposed Strength check to determine if overrunner is knocked prone |

**SRD rule:** "If you fail to overrun your opponent, the defender may immediately react and make a Strength check to try to knock you down." This is a separate opposed check, not a margin threshold.

**Test impact:** New tests for overrun failure prone check as opposed roll.

---

### FIX-WO-09: Sunder Damage Placeholder (LOW — 1 bug, 1 file)

**Bugs:** B-BUG-4
**Files:** `aidm/core/maneuver_resolver.py`
**Effort:** LOW

| Bug | Location | Fix |
|-----|----------|-----|
| B-BUG-4 | maneuver_resolver.py:1027 | Replace hardcoded 1d8 sunder damage with attacker's actual weapon damage dice |

**Test impact:** Sunder damage tests with various weapon types.

---

### FIX-WO-10: Movement & Terrain Bugs (MIXED — 3 bugs, 2 files)

**Bugs:** E-BUG-01, E-BUG-02, E-BUG-03
**Files:** `aidm/core/terrain_resolver.py`, `aidm/core/mounted_combat.py`
**Effort:** LOW-MEDIUM

| Bug | Location | Severity | Fix |
|-----|----------|----------|-----|
| E-BUG-01 | terrain_resolver.py:256 | MEDIUM | Change `soft_cover and is_melee` to `soft_cover and not is_melee` (invert condition) |
| E-BUG-02 | terrain_resolver.py:619 | HIGH | Implement proper water fall: d3 nonlethal instead of d6 lethal, add DC 15 Swim/Dive check for first-20ft-free |
| E-BUG-03 | mounted_combat.py:667 | LOW | Add Fine, Diminutive, Colossal to SIZE_ORDER dict. Renumber ordinals: fine=0 through colossal=8. |

**Test impact:** Soft cover ranged tests, water fall damage tests, size category comparison tests for extreme sizes.

---

### FIX-WO-11: Action Cost Table (MEDIUM — 1 bug, 1 file)

**Bugs:** G-PLAY-71-86
**Files:** `aidm/core/play_loop.py` (or equivalent action cost table)
**Effort:** MEDIUM — architectural impact on CLI action parsing

| Bug | Location | Fix |
|-----|----------|-----|
| G-PLAY-71-86 | play_loop.py:71-86 | Change Trip, Disarm, Grapple action type from "standard" to "varies" (melee attack substitution). Requires CLI to support these as attack replacements during full attack. |

**Test impact:** Action economy tests for trip/disarm/grapple as part of full attack sequences.

---

### FIX-WO-12: Character Progression Bugs (MEDIUM — 3 bugs, 2 files)

**Bugs:** BUG-F1, BUG-F2, BUG-F3
**Files:** `aidm/core/experience_resolver.py`, `aidm/schemas/leveling.py`
**Effort:** MEDIUM

| Bug | Location | Severity | Fix |
|-----|----------|----------|-----|
| BUG-F1 | experience_resolver.py:230 | LOW | Add `or new_level == 1` to feat grant condition (or confirm 1st-level feat is handled in character creation) |
| BUG-F2 | leveling.py:291-308 | MEDIUM | Replace computed XP table for levels 11-20 with hardcoded DMG Table 2-6 values |
| BUG-F3 | leveling.py:308 | LOW-MEDIUM | Same fix as BUG-F2 — hardcode complete table |

**Test impact:** XP award tests for levels 11-20 with various CR deltas. Feat grant tests at level 1.

---

### FIX-WO-13: Geometry — Colossal Footprint (MEDIUM — 1 bug, 1 file)

**Bugs:** I-GEOM-291
**Files:** `aidm/schemas/geometry.py`
**Effort:** TRIVIAL

| Bug | Location | Fix |
|-----|----------|-----|
| I-GEOM-291 | geometry.py:291-301 | Change `SizeCategory.COLOSSAL: 25` to `SizeCategory.COLOSSAL: 36`. Update docstring from "5x5" to "6x6". |

**Test impact:** Colossal creature footprint tests. Verify no downstream code assumes 5x5 for Colossal.

---

## Dispatch Priority

Recommended fix order based on severity, blast radius, and dependency chains:

| Priority | WO | Severity | Reason |
|----------|----|----------|--------|
| 1 | FIX-WO-03 | HIGH | Schema change — all other attack fixes depend on correct condition modifiers |
| 2 | FIX-WO-01 | HIGH | Core damage pipeline — most frequently executed code path |
| 3 | FIX-WO-05 | HIGH | Cover values affect both AC and Reflex saves (cross-domain) |
| 4 | FIX-WO-06 | HIGH | Concentration DC — simple fix, high correctness impact |
| 5 | FIX-WO-02 | MEDIUM | Full attack loop — functional correctness |
| 6 | FIX-WO-04 | MEDIUM | Condition gaps — incremental fixes |
| 7 | FIX-WO-07 | MEDIUM | Maneuver size modifiers — same-pattern fix |
| 8 | FIX-WO-08 | HIGH | Overrun — single mechanic, needs design |
| 9 | FIX-WO-10 | MIXED | Terrain — independent fixes |
| 10 | FIX-WO-11 | MEDIUM | Action types — architectural impact |
| 11 | FIX-WO-12 | MEDIUM | Character progression — lower combat impact |
| 12 | FIX-WO-09 | LOW | Sunder placeholder — low priority |
| 13 | FIX-WO-13 | MEDIUM | Colossal footprint — trivial fix |

---

## Relationship to Existing WO-BUGFIX-TIER0-001

The existing `WO-BUGFIX-TIER0-001_DISPATCH.md` covers BUG-1, BUG-2, BUG-3, BUG-4. These are now subsumed into:
- FIX-WO-01 (BUG-1)
- FIX-WO-02 (BUG-2)
- FIX-WO-03 (BUG-3, BUG-4)

WO-BUGFIX-TIER0-001 should be superseded by these more detailed fix WOs.

---

## End of WRONG Verdicts Master List
