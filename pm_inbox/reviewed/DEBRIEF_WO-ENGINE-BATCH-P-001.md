# DEBRIEF — ENGINE BATCH P (WO-ENGINE-POWER-ATTACK-001 / WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001 / WO-ENGINE-PRECISE-SHOT-001 / WO-ENGINE-IMPROVED-DISARM-COUNTER-001)

**Commit hashes:**
- WO1 PA: `cd429fb`
- WO2 IMB: `336f04d`
- WO3 PS: `e39c921`
- WO4 IDC: `5d088d6`

**Gate results:** 32/32 PASS (PA 8/8, IMB 8/8, PS 8/8, IDC 8/8)
**Regression suite:** 8465 passed / 141 pre-existing failures / 34 skipped / 0 new failures
**Date:** 2026-02-27
**Status:** FILED

---

## Pass 1 — Context Dump

### WO1 — WO-ENGINE-POWER-ATTACK-001 (PA)

**Status: FULL SAI.** Implementation already committed at `cd429fb` before this session.

**Files changed:** `aidm/core/attack_resolver.py`, `aidm/core/feat_resolver.py`, `aidm/schemas/attack.py`, `tests/test_engine_power_attack_gate.py`

**Implementation location:**
- `feat_resolver.py:172-174` — `get_attack_modifier()`: if `FeatID.POWER_ATTACK in feats`, subtract `power_attack_penalty` from attack modifier
- `feat_resolver.py:219-228` — `get_damage_modifier()`: two-handed `int(penalty * 1.5)`, off-hand `penalty // 2`, else `penalty * 1`
- `attack_resolver.py:462-464` — `feat_context` dict passes `power_attack_penalty`, `is_two_handed`, `grip` to `feat_resolver`
- `attack_resolver.py:468-499` — Validation block: `power_attack_penalty > 0` → checks feat presence (`feat_requirement_not_met`) then BAB ceiling (`penalty_exceeds_bab`); returns early on failure

**Pattern used:** Same `feat_context` dict pattern as Combat Expertise (Batch C). Penalty declared on `AttackIntent.power_attack_penalty: int = 0`. NOT stored in `EF.TEMPORARY_MODIFIERS` — ephemeral per-attack intent pattern (same as Smite Evil per MEMORY.md bonus injection patterns).

**Key finding (WO1 Pass 3):** Dispatch spec says `int(pa_penalty * 1.5)` for two-handed. Implementation uses `int(power_attack_penalty * 1.5)` — same result. RAW (PHB p.98) says 2:1; dispatch specified 1.5:1 to mirror STR-to-damage multipliers. This variance is documented in feat_resolver.py:216-218 as a comment. Consistent with STR grip multiplier pattern from WO-FIX-01.

**Gate tests (PA-001–PA-008):**
- PA-001: 1H, PA=2 → attack feat_modifier=-2, damage feat_modifier=+2 ✓
- PA-002: 2H, PA=2 → damage feat_modifier=+3 (floor(2×1.5)=3) ✓
- PA-003: off-hand, PA=2 → damage feat_modifier=+1 (floor(2×0.5)=1) ✓
- PA-004: PA=3 with BAB=2 → `intent_validation_failed` reason=`penalty_exceeds_bab` ✓
- PA-005: PA=0 → no error, feat_modifier=0 ✓
- PA-006: no feat, PA=2 → `intent_validation_failed` reason=`feat_requirement_not_met` ✓
- PA-007: Full attack — both iterative attacks show feat_modifier=-3 ✓
- PA-008: PA=2 + Weapon Focus +1 → net feat_modifier=-1 on attack, +2 on damage ✓

---

### WO2 — WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001 (IMB)

**Status: FULL SAI.** Implementation already committed at `336f04d` before this session.

**Files changed:** `aidm/core/maneuver_resolver.py`, `tests/test_engine_improved_maneuver_bonuses_gate.py`

**Implementation — all 5 maneuvers, single primary check site each:**
- `maneuver_resolver.py:309-311` — Improved Bull Rush: `if "improved_bull_rush" in ... EF.FEATS: attacker_modifier += 4` (inside `resolve_bull_rush()`, after charge bonus applied)
- `maneuver_resolver.py:623-625` — Improved Trip: `if "improved_trip" in ... EF.FEATS: attacker_modifier += 4` (inside trip opposed check path)
- `maneuver_resolver.py:1208-1210` — Improved Sunder: `if "improved_sunder" in ... EF.FEATS: attacker_modifier += 4` (inside `resolve_sunder()`)
- `maneuver_resolver.py:1467-1469` — Improved Disarm: `if "improved_disarm" in ... EF.FEATS: attacker_modifier += 4` (inside `resolve_disarm()`)
- `maneuver_resolver.py:1748-1750` — Improved Grapple: `if "improved_grapple" in ... EF.FEATS: attacker_grapple_modifier += 4` (inside `resolve_grapple()`)

**Secondary call sites:** No secondary call sites found for any of the 5 maneuvers. Each maneuver has a single opposed-check computation path. IMB-005 explicitly confirmed Improved Bull Rush +4 stacks correctly with charge bonus (+2) in the same `attacker_modifier` accumulation.

**Closed findings:**
- FINDING-ENGINE-IMPROVED-DISARM-BONUS-001 → CLOSED
- FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001 → CLOSED
- FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001 → CLOSED
- FINDING-ENGINE-IMPROVED-TRIP-BONUS-001 → CLOSED
- FINDING-ENGINE-IMPROVED-SUNDER-BONUS-001 → CLOSED

**Gate tests (IMB-001–IMB-008):**
- IMB-001: Improved Disarm → attacker_modifier = 11 (baseline 7 + 4) ✓
- IMB-002: Improved Sunder → attacker_modifier = 11 (baseline 7 + 4) ✓
- IMB-003: Improved Trip → attacker_modifier = 6 (baseline 2 + 4) ✓
- IMB-004: Improved Grapple → attacker_modifier = 11 (baseline 7 + 4) ✓
- IMB-005: Improved Bull Rush + charge → attacker_modifier = 8 (baseline 2 + charge 2 + 4) ✓
- IMB-006: No feat → attacker_modifier = 7 (baseline only) ✓
- IMB-007: improved_trip + improved_disarm doing trip → +4 only (not +8) ✓
- IMB-008: All 5 maneuver +4 visible in opposed_check payload ✓

---

### WO3 — WO-ENGINE-PRECISE-SHOT-001 (PS)

**Status: FULL SAI.** Implementation already committed at `e39c921` before this session.

**Files changed:** `aidm/core/attack_resolver.py`, `tests/test_engine_precise_shot_gate.py`

**Implementation location:**
- `attack_resolver.py:185-198` — `_is_target_in_melee(target_id, attacker_team, world_state)`: helper function. Target is "in melee" if any non-defeated ally of the attacker is adjacent (within 5 ft) using `Position` adjacency check.
- `attack_resolver.py:623-637` — Guard block: `if not is_melee and _is_target_in_melee(...)`: if `"precise_shot" in feats` → emit `precise_shot_active` event; else `_ranged_into_melee_penalty = -4`
- `attack_resolver.py:656` — `_ranged_into_melee_penalty` added to attack bonus accumulation

**Adjacency check:** Reused `_is_target_in_melee()` which was already implemented (leverages `Position` geometry from Batch C Cleave adjacency WO). Not new code — pre-existing helper.

**Point Blank Shot interaction:** PS does not affect PBShot's +1/+1. They are computed in separate locations: PBShot is in `feat_resolver.get_attack_modifier()`; PS penalty is an inline guard in `attack_resolver.py`. No interaction; both apply cleanly.

**Feat key confirmed:** `"precise_shot"` (lowercase, underscore).

**Gate tests (PS-001–PS-008):**
- PS-001: Precise Shot + target in melee → no -4 ✓
- PS-002: No Precise Shot + target in melee → -4 applied ✓
- PS-003: Target not in melee → no penalty regardless ✓
- PS-004: Melee attack → Precise Shot irrelevant ✓
- PS-005: `precise_shot_active` event emitted ✓
- PS-006: Precise Shot + Point Blank Shot → PBShot +1/+1 unaffected ✓
- PS-007: Full-attack iterative — no -4 on second attack with feat ✓
- PS-008: Regression — non-Precise-Shot actor still gets -4 into melee ✓

---

### WO4 — WO-ENGINE-IMPROVED-DISARM-COUNTER-001 (IDC)

**Status: FULL SAI.** Implementation already committed at `5d088d6` before this session.

**Files changed:** `aidm/core/maneuver_resolver.py`, `tests/test_engine_improved_disarm_counter_gate.py`

**Implementation location:** `maneuver_resolver.py:1523-1635` — inside `resolve_disarm()`, in the failure branch.

**Counter-disarm base — already implemented (not newly added):** The docstring at line 1366-1378 already describes counter-disarm as part of the original `resolve_disarm()` implementation. Full counter-disarm logic was wired in WO-ENGINE-SUNDER-DISARM-FULL-001 (ENGINE DISPATCH #6).

**Threshold behavior:** `margin = check_result.defender_total - check_result.attacker_total; counter_disarm_allowed = margin >= 10` (line 1525-1526). Boundary: margin=10 triggers counter; margin=9 does not.

**Improved Disarm suppression:** `maneuver_resolver.py:1548-1564` — `if "improved_disarm" in _att_feats: emit counter_disarm_suppressed event; return ManeuverResult(success=False)`

**Attacker DEX on counter:** Counter disarm uses `_roll_opposed_check(rng, defender_modifier, attacker_modifier, "counter_disarm")` at line 1568. `attacker_modifier` (original attacker, now counter-target) is the pre-computed `attacker_modifier` from the outer disarm computation (includes BAB+STR+size+weapon_type modifiers). PHB says attacker loses DEX to AC for the counter — this affects AC, not the opposed attack check (disarm is opposed attack rolls, not AC-based). AC stripping on counter is a separate future scope item. FINDING logged below.

**Closed findings:**
- FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 → CLOSED

**Gate tests (IDC-001–IDC-008):**
- IDC-001: Disarm success → no counter triggered ✓
- IDC-002: Fail by <10 → no counter ✓
- IDC-003: Fail by ≥10, no Improved Disarm → counter rolled ✓
- IDC-004: Improved Disarm, fail by ≥10 → `counter_disarm_suppressed` event ✓
- IDC-005: Counter disarm wins → attacker disarmed ✓
- IDC-006: Counter disarm fails → no disarm on original attacker ✓
- IDC-007: Threshold uses totals (not raw d20) ✓
- IDC-008: `counter_disarm_suppressed` payload contains `feat: "improved_disarm"` ✓

---

## Pass 2 — PM Summary (≤100 words)

Batch P: 4/4 SAI. All implementations (PA/IMB/PS/IDC) were committed prior to this session — cd429fb/336f04d/e39c921/5d088d6. Gate run: 32/32 PASS. Regression: 8465 passed / 141 pre-existing / 0 new failures. Findings closed: IMPROVED-DISARM-BONUS, IMPROVED-GRAPPLE-BONUS, IMPROVED-BULL-RUSH-BONUS, IMPROVED-TRIP-BONUS, IMPROVED-SUNDER-BONUS, IMPROVED-DISARM-COUNTER — all 6 findings resolved by SAI confirmation. Power Attack uses 1.5× two-handed multiplier (documented variance from PHB 2× RAW per dispatch spec). No regressions. Batch P FILED.

---

## Pass 3 — Retrospective

**WO1 (PA):** PA uses the same `feat_context` dict pattern as Combat Expertise. The `feat_resolver.py` is the single damage/attack modifier choke point. 2H multiplier is 1.5×, not 2× RAW — this is a deliberate dispatch decision, documented in code comment at feat_resolver.py:216-218. Feat key confirmed `"power_attack"`. Combat Expertise reference pattern confirmed used correctly.

**WO2 (IMB):** No secondary call sites found for any maneuver. The dispatch concern about secondary paths (e.g., "follow-through bull rush after charge") is resolved by the gate: IMB-005 passes with is_charge=True, confirming +4 stacks with charge bonus in the single accumulation point. All 5 findings closed by this SAI confirmation.

**WO3 (PS):** `_is_target_in_melee()` was already implemented — it's not new code. Pre-existing helper from prior Cleave/positioning work. Reuse is correct architecture. Precise Shot and Point Blank Shot are fully independent (different code paths, different modifier buckets).

**WO4 (IDC):** Counter-disarm base was implemented in WO-ENGINE-SUNDER-DISARM-FULL-001 (ENGINE DISPATCH #6). The IDC WO adds only the Improved Disarm suppression check. PHB says attacker loses DEX to AC for the counter-attempt — this is AC-based, not opposed-check-based. Current implementation does not strip DEX from AC during counter. Minor architectural gap; documented as FINDING below.

**KERNEL TOUCH:** NONE on any of the 4 WOs.

---

## Radar

| ID | Severity | Status | Notes |
|----|----------|--------|-------|
| FINDING-ENGINE-IDC-DEX-AC-STRIP-001 | LOW | OPEN | PHB p.155: attacker loses DEX bonus to AC on counter-disarm attempt. Current counter-disarm uses opposed attack rolls (not AC), so DEX strip is not applicable to the check itself. If counter-disarm ever extends to AC-based defense resolution, this becomes a gap. Deferred. |
| FINDING-ENGINE-PA-2H-MULTIPLIER-001 | LOW | DOCUMENTED | Dispatch specifies 1.5× for 2H PA (matches STR grip pattern). PHB RAW says 2×. Variance documented in feat_resolver.py:216-218. Not a bug — deliberate dispatch decision. No action needed. |

---

*Debrief filed by Chisel. Three-pass format complete. Commit before debrief: confirmed (cd429fb/336f04d/e39c921/5d088d6).*
