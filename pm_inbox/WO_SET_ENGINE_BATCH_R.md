# ENGINE DISPATCH — BATCH R
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Lifecycle:** DISPATCH-READY
**To:** Chisel (lead builder)
**Batch:** R — 4 WOs, 24 new gate tests (WO3 is SAI — existing gate confirmed, no new tests)
**Prerequisite:** NONE — runs in parallel with ENGINE BATCH P

**Parallel track:** Batch R intentionally avoids `attack_resolver.py`, `maneuver_resolver.py`, and `play_loop.py` — the three files locked by Batch P. Start immediately after dirty-tree baseline is committed; do not wait for Batch P to close.

**Batch Q coupling note:** Batch R WO4 (GTWF) and Batch Q WO3 (WFC) both touch `full_attack_resolver.py`. Ensure Batch R WO4 is committed and clean before Batch Q WO3 begins.

---

## Boot Sequence

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm dirty-tree baseline is committed — `git status` must show clean tracked files before any WO begins. If dirty tree is still present from the Batch P baseline commit, stop and flag to Thunder.
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md`
4. Run `python scripts/verify_session_start.py`
5. Orphan check: any WO IN EXECUTION with no debrief? Flag before proceeding.
6. Record pre-existing failure count: `pytest --tb=no -q`

---

## Intelligence Update

**File ownership — zero overlap with Batch P:**

| WO | File(s) | Batch P conflict? |
|---|---|---|
| WO1 (IE) | `spell_resolver.py` | None |
| WO2 (MB) | `aoo.py` | None |
| WO3 (SP) | `aoo.py` | None |
| WO4 (GTWF) | `full_attack_resolver.py` | None |

**WO2 and WO3 both touch `aoo.py`.** Commit WO2 before WO3.

**Recommended commit order:** WO1 → WO2 → WO3 → WO4.

---

### Pre-dispatch Reconnaissance (2026-02-27)

**WO1 IE — HIGH SAI RISK.** `spell_resolver.py:914-927` already contains both Improved Evasion
branches. Line 915: `if _evasion_active and (EF.EVASION or EF.IMPROVED_EVASION): total = 0` (save
pass). Line 926: `if EF.IMPROVED_EVASION and armor in ("none","light"): total = total // 2` (save
fail). The existing dispatch's implementation plan (class-level check) may still be needed IF
`EF.IMPROVED_EVASION` is not set at chargen — that would be the actual production change. Builder
must check both the chargen path and the spell_resolver path on boot.

**WO2 MOBILITY — DEEP CORRECTION BELOW.** The TEMPORARY_MODIFIERS approach described in this dispatch
is NOT what is implemented. `aoo.py:596-624` already calls `get_ac_modifier(provoker, reactor,
feat_context)` (which uses `feat_resolver.py:262-268` to detect Mobility) and applies the result via
a `deepcopy` of `world_state.entities`, mutating `EF.AC` on the copy before calling `resolve_attack()`.
The "BLOCKED" condition in WO2 is based on the wrong assumption. The deepcopy approach does NOT require
touching `attack_resolver.py`. See corrected WO2 implementation plan below.

**WO3 AOO-STANDING-PRONE — FULL SAI.** `check_stand_from_prone_aoo()` is fully implemented at
`aoo.py:709-817`. Gate file `tests/test_engine_aoo_stand_from_prone_001_gate.py` already exists
(Batch I, WO-ENGINE-AOO-STAND-FROM-PRONE-001). Builder must NOT create a new gate file. Builder
confirms existing implementation and gate, then files debrief as SAI. The FINDING-CE-STANDING-AOO-001
flat-footed reactor guard is also present at `aoo.py:779`. Confirm on boot and close the finding.

**WO4 GTWF — FEAT KEY DISCREPANCY.** The existing dispatch uses `"greater_two_weapon_fighting"`
(lowercase underscore). However, TWF and ITWF in `full_attack_resolver.py` use Title Case:
`"Two-Weapon Fighting"`, `"Improved Two-Weapon Fighting"`. Builder must confirm the feat key
convention for TWF feats on boot and use whichever matches the actual stored string in `EF.FEATS`.
If Title Case: use `"Greater Two-Weapon Fighting"`. If lowercase: use `"greater_two_weapon_fighting"`.
Do not guess — read the existing ITWF check at `full_attack_resolver.py:902`.

---

**Evasion insertion site:** `spell_resolver.py:905-930` block. `EF.IMPROVED_EVASION` field read
at lines 915 and 926. If IE is not set at chargen, the chargen path is the production change.

**Improved Evasion detection:** The existing code reads `EF.IMPROVED_EVASION` directly from entity
dict (not a class-level check). Chargen must set this field. Rogue ≥10, Monk ≥9. Use
`entity.get(EF.CLASS_LEVELS, {}).get("rogue", 0)` to determine eligibility at chargen.

**Mobility wiring:** `feat_resolver.py:262-268` computes +4 via `FeatID.MOBILITY`. `aoo.py:615-624`
applies via deepcopy. No `attack_resolver.py` touch required. Stale TODO at `aoo.py:609-613`
predates the workaround — clean it up.

**AoO standing from prone:** Already wired. See reconnaissance note above.

**Greater TWF chain:** TWF and ITWF confirmed wired. GTWF missing. Feat key: verify on boot.

**EF.CLASS_LEVELS pattern:** `entity.get(EF.CLASS_LEVELS, {}).get("rogue", 0)` — confirmed.

**EF.ARMOR_TYPE pattern:** `entity.get(EF.ARMOR_TYPE, "none")` — values: `"none"`, `"light"`,
`"medium"`, `"heavy"`.

**Event constructor:** `Event(event_id=..., event_type=..., payload=...)`.

---

## WO 1 — WO-ENGINE-IMPROVED-EVASION-001

**Scope:** `aidm/core/spell_resolver.py`
**Gate file:** `tests/test_engine_improved_evasion_gate.py`
**Gate label:** ENGINE-IMPROVED-EVASION
**Gate count:** 8 tests (IE-001 – IE-008)
**Kernel touch:** NONE
**Source:** PHB p.50 (Rogue), p.41 (Monk)

### Gap Verification

Deferred explicitly from Batch B R1 WO1 debrief: "Improved Evasion: still takes half on failed save. Deferred: Improved Evasion with Reflex fail-half (separate WO candidate)."

PHB p.50: "If a rogue with improved evasion is exposed to any effect that normally allows her to attempt a Reflex saving throw for half damage, she takes no damage if she makes a saving throw and only half damage on a failed save." Armor restriction: cannot use Improved Evasion in medium or heavy armor (same as Evasion).

**Assumptions to Validate on boot:**
- **SAI CHECK FIRST:** Read `spell_resolver.py:905-930`. Reconnaissance found both branches already
  wired at lines 915-916 (save pass → 0) and lines 921-927 (save fail → half). Confirm these lines
  exist and are active. If both are present: this WO is SAI. Gate tests validate existing behavior;
  zero production changes to `spell_resolver.py`.
- If SAI: the only remaining question is whether `EF.IMPROVED_EVASION` is set at chargen. If not set
  at chargen, adding the chargen write IS the production change. Use `EF.CLASS_LEVELS` pattern.
  Rogue ≥10, Monk ≥9 → write `EF.IMPROVED_EVASION = True` on entity.
- Confirm armor check at line 914: `_armor in ("none", "light")` gates both branches. Medium/heavy
  suppress IE. This is correct behavior — do not modify.
- Class level thresholds: rogue ≥ 10, monk ≥ 9 (PHB p.50/41). The existing code reads
  `EF.IMPROVED_EVASION` directly, not class levels. Chargen sets the field; resolver reads it.

### Implementation

**If SAI (spell_resolver.py:914-927 already wired):** Zero production changes to `spell_resolver.py`.
Only production change (if needed): ensure `EF.IMPROVED_EVASION = True` is written at chargen for
eligible classes. Write gate tests that validate existing behavior.

**If NOT SAI:** In `spell_resolver.py`, in the FAILED Reflex save branch for `SaveEffect.HALF`,
immediately below the existing Evasion check:

```python
# Improved Evasion: on FAILED Reflex save vs half-damage spell → half damage (PHB p.50)
_rogue_lvl = target.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
_monk_lvl = target.get(EF.CLASS_LEVELS, {}).get("monk", 0)
_armor = target.get(EF.ARMOR_TYPE, "none")
_has_ie = (_rogue_lvl >= 10 or _monk_lvl >= 9) and _armor in ("none", "light")
if _has_ie:
    final_damage = final_damage // 2
    events.append(Event(event_id=..., event_type="improved_evasion_active",
                        payload={"target_id": target_id, "damage_halved": final_damage}))
```

**If using EF.IMPROVED_EVASION field (preferred, matches existing code pattern):**
```python
_armor = target.get(EF.ARMOR_TYPE, "none")
if _armor in ("none", "light") and target.get(EF.IMPROVED_EVASION, False):
    final_damage = final_damage // 2
```

### Gate Tests (IE-001 – IE-008)

```python
# IE-001: Rogue 10, fails Reflex save vs AoE → half damage (not full)
# IE-002: Monk 9, fails Reflex save → half damage
# IE-003: Rogue 10, succeeds Reflex save → no damage (Evasion success case unaffected)
# IE-004: Rogue 9 (below threshold), fails Reflex → full damage (no IE)
# IE-005: No Evasion class, fails Reflex → full damage (regression guard)
# IE-006: Rogue 10 in medium armor, fails → full damage (armor suppresses IE)
# IE-007: improved_evasion_active event emitted with damage_halved payload when IE triggers
# IE-008: Rogue 10 in light armor, fails → half damage (light armor does NOT suppress)
```

### Session Close Conditions
- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_improved_evasion_gate.py`
- [ ] `git commit`
- [ ] IE-001–IE-008: 8/8 PASS; zero regressions

---

## WO 2 — WO-ENGINE-MOBILITY-001

**Scope:** `aidm/core/aoo.py`
**Gate file:** `tests/test_engine_mobility_gate.py`
**Gate label:** ENGINE-MOBILITY
**Gate count:** 8 tests (MB-001 – MB-008)
**Kernel touch:** NONE
**Source:** PHB p.97

**Wiring already present — gate test is the deliverable.** Pre-dispatch reconnaissance confirmed that
`feat_resolver.py:262-268` computes the +4 and `aoo.py:615-624` applies it via deepcopy. The
TEMPORARY_MODIFIERS approach described in the original draft was never implemented and is NOT correct.
Do NOT use TEMPORARY_MODIFIERS. Do NOT touch `attack_resolver.py`. The BLOCKED condition below is
superseded by this finding.

### Gap Verification

`feat_resolver.py:262-268` uses `FeatID.MOBILITY` to compute +4 when `is_aoo=True` and
`aoo_trigger in ("movement_out", "mounted_movement_out")`.
`aoo.py:596-624` calls `get_ac_modifier(provoker, reactor, feat_context)` and applies the result via
`deepcopy(world_state.entities)` — mutates `EF.AC` on the copy, rebuilds `WorldState`, then calls
`resolve_attack()` with the modified state. This delivers the +4 to the attack resolver without any
changes to `attack_resolver.py`.

**Assumptions to Validate on boot:**
- Read `aoo.py:596-624`. Confirm the deepcopy block mutates `temp_entities[trigger.provoker_id][EF.AC]`
  BEFORE `resolve_attack()` is called. If yes: wiring is complete.
- Confirm `FeatID.MOBILITY` resolves to the same string stored in `EF.FEATS`. Search `feat_resolver.py`
  for `FeatID.MOBILITY` definition. If `EF.FEATS` stores strings (e.g., `"mobility"`) and
  `FeatID.MOBILITY == "mobility"`, the check works. Document the resolution in debrief.
- Confirm the stale TODO comment at `aoo.py:609-613` ("Current limitation...") predates the deepcopy
  workaround at lines 615-624. Remove the TODO comment block (lines 609-613) if the wiring is
  confirmed complete. Keep the deepcopy block.
- Confirm Mobility does NOT apply to `"stand_from_prone"` AoOs (not in the allowed trigger set).
  Gate test MB-006 validates this.

### Implementation

No production code changes expected. The deepcopy path at `aoo.py:615-624` is the implementation.
If on-boot validation reveals a bug in that path, diagnose and fix without touching `attack_resolver.py`.
The only expected production change: remove the stale TODO comment at `aoo.py:609-613`.

### Gate Tests (MB-001 – MB-008)

```python
# MB-001: Mobility feat, movement provokes AoO (StepMoveIntent) → AoO attack roll is vs AC+4
# MB-002: No Mobility feat, movement provokes AoO → normal AC (no bonus)
# MB-003: Mobility feat, non-movement AoO (e.g., spellcasting) → no +4 bonus (movement-only)
# MB-004: Mobility +4 sufficient to cause attacker to miss (threshold test: roll exactly hits without
#         Mobility, misses with it)
# MB-005: mobility_active event OR AC delta verifiable — +4 reaches resolve_attack() AC check
# MB-006: Mobility feat + stand_from_prone AoO → NO +4 (trigger is "stand_from_prone", not in allowed set)
# MB-007: Multiple movement AoOs in same round → Mobility applies to each (deepcopy path per-AoO)
# MB-008: Regression — mounted_movement_out trigger → +4 applies (in allowed trigger set)
```

### Session Close Conditions
- [ ] `git add aidm/core/aoo.py tests/test_engine_mobility_gate.py`
- [ ] `git commit`
- [ ] MB-001–MB-008: 8/8 PASS; zero regressions

---

## WO 3 — WO-ENGINE-AOO-STANDING-PRONE-001

**Scope:** `aidm/core/aoo.py`
**Gate file:** `tests/test_engine_aoo_stand_from_prone_001_gate.py` ← EXISTING FILE (Batch I)
**Gate label:** ENGINE-AOO-STAND-FROM-PRONE (pre-existing)
**Gate count:** Run existing gate, confirm pass count; do NOT write new gate tests
**Kernel touch:** NONE
**Source:** PHB p.137, p.154

**Closes:** FINDING-CE-STANDING-AOO-001

**Commit WO2 first** — both WO2 and WO3 touch `aoo.py`.

**STATUS: FULL SAI.** `check_stand_from_prone_aoo()` is implemented at `aoo.py:709-817`. Gate file
`tests/test_engine_aoo_stand_from_prone_001_gate.py` exists (Batch I). Zero production changes needed.
Builder confirms existing implementation, runs existing gate test, files debrief as SAI + closes finding.

### Gap Verification

**Pre-dispatch finding:** `check_stand_from_prone_aoo()` fully implemented at `aoo.py:709-817`:
- Checks actor has `"prone"` in `EF.CONDITIONS` (line 737)
- Finds all adjacent enemies (AoO-limit-aware, flat-footed reactor check at line 779)
- Returns `AooTrigger` list in initiative order
- Gate file `tests/test_engine_aoo_stand_from_prone_001_gate.py` exists and passes

**FINDING-CE-STANDING-AOO-001 resolution:** The flat-footed reactor guard is at `aoo.py:779`:
`if "flat_footed" in _reactor_conditions: continue`. This is correctly implemented inside
`check_stand_from_prone_aoo()`. The finding's "flat-footed AoO suppression for standing entities"
refers to this guard — it is present. CLOSE the finding.

**Assumptions to Validate on boot:**
- Read `aoo.py:709-817`. Confirm `check_stand_from_prone_aoo()` exists and is called from `play_loop.py`
  when a `StandIntent` is processed.
- Run `pytest tests/test_engine_aoo_stand_from_prone_001_gate.py -v`. All tests should pass.
- Confirm flat-footed reactor guard at `aoo.py:779` is present. If present: FINDING-CE-STANDING-AOO-001 CLOSED.
- Do NOT create `tests/test_engine_aoo_standing_prone_gate.py` — that name would duplicate the existing gate.

### Implementation

None. Zero production changes.

### Gate Tests

Run EXISTING gate file only:
```bash
pytest tests/test_engine_aoo_stand_from_prone_001_gate.py -v
```

Do not write new gate tests for this WO.

### Session Close Conditions
- [ ] Existing gate confirmed: all tests PASS; zero regressions
- [ ] Debrief filed as SAI
- [ ] FINDING-CE-STANDING-AOO-001: CLOSED in debrief (flat-footed guard at aoo.py:779 confirmed)

---

## WO 4 — WO-ENGINE-GREATER-TWF-001

**Scope:** `aidm/core/full_attack_resolver.py`
**Gate file:** `tests/test_engine_greater_twf_gate.py`
**Gate label:** ENGINE-GREATER-TWF
**Gate count:** 8 tests (GTWF-001 – GTWF-008)
**Kernel touch:** NONE
**Source:** PHB p.96

### Gap Verification

TWF chain status: TWF (−2/−2, one off-hand) + Improved TWF (second off-hand at −5 from highest BAB) ACCEPTED via WO-ENGINE-TWF-WIRE (Gate CP-21 12/12). Greater TWF: third off-hand attack at highest BAB −10. Not yet wired — no ENGINE-GREATER-TWF in gate table.

**Assumptions to Validate on boot:**
- Read `full_attack_resolver.py:902`: `if "Improved Two-Weapon Fighting" in feats`. **Confirm the exact
  string casing used for TWF/ITWF.** The TWF feat string is Title Case in the engine (`"Two-Weapon
  Fighting"`, `"Improved Two-Weapon Fighting"`), NOT lowercase underscore. GTWF MUST follow the same
  pattern: `"Greater Two-Weapon Fighting"`. If the original draft's `"greater_two_weapon_fighting"`
  (lowercase) does not match, use Title Case.
- In `full_attack_resolver.py`, locate where ITWF off-hand attack is appended (line ~900). GTWF
  inserts after this, gated on `"Greater Two-Weapon Fighting" in attacker_feats` (or whatever casing
  is confirmed above).
- Confirm the off-hand penalty scheme: GTWF third off-hand at `intent.base_attack_bonus - 10 + off_penalty`.
  The ITWF block uses `-5`; GTWF uses `-10`.
- Confirm half-STR damage applies to the third off-hand attack.
- SAI check: search `full_attack_resolver.py` for `"Greater Two-Weapon"` or `"greater_two_weapon"`.
  If already wired, document as SAI.

### Implementation

In `full_attack_resolver.py`, immediately after the ITWF off-hand attack block (after line ~952):

```python
# Greater Two-Weapon Fighting: third off-hand attack at intent.base_attack_bonus - 10 + off_penalty
# Feat string: "Greater Two-Weapon Fighting" (Title Case — matches TWF/ITWF convention)
if "Greater Two-Weapon Fighting" in feats and current_hp > 0:
    gtwf_bab = intent.base_attack_bonus - 10 + off_penalty
    gtwf_adjusted = (
        gtwf_bab
        + attacker_modifiers.attack_modifier
        + mounted_bonus
        + terrain_higher_ground
        + feat_attack_modifier
        + flanking_bonus
        + (0 if _wp_proficient_check(attacker, intent.off_hand_weapon) else -4)
    )
    gtwf_events, current_event_id, gtwf_damage = resolve_single_attack_with_critical(
        attacker_id=intent.attacker_id,
        target_id=intent.target_id,
        attack_bonus=gtwf_adjusted,
        weapon=intent.off_hand_weapon,
        target_ac=target_ac,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.5 * attacks_executed,
        attack_index=attacks_executed,
        str_modifier=off_str_mod,
        condition_damage_modifier=attacker_modifiers.damage_modifier,
        feat_damage_modifier=0,
        base_attack_bonus_raw=gtwf_bab,
        condition_attack_modifier=attacker_modifiers.attack_modifier,
        mounted_bonus=mounted_bonus,
        terrain_higher_ground=terrain_higher_ground,
        feat_attack_modifier=0,
        target_base_ac=base_ac,
        target_ac_modifier=condition_ac,
        cover_type=cover_result.cover_type,
        cover_ac_bonus=cover_result.ac_bonus,
        dr_amount=dr_amount,
        miss_chance_percent=miss_chance_percent,
        flanking_bonus=flanking_bonus,
        is_flanking=is_flanking,
        flanking_ally_ids=flanking_ally_ids,
        sneak_attack_dice=sa_dice,
        sneak_attack_eligible=sa_eligible,
        sneak_attack_reason=sa_reason,
        favored_enemy_bonus=_favored_enemy_bonus,
        attacker_feats=_attacker_feats,
    )
    events.extend(gtwf_events)
    total_damage += gtwf_damage
    for ev in gtwf_events:
        if ev.event_type == "damage_roll":
            total_dr_absorbed += ev.payload.get("damage_reduced", 0)
    current_hp -= gtwf_damage
    attacks_executed += 1
```

Copy from ITWF block verbatim. Only change: variable prefix `itwf_` → `gtwf_`, and `-5` → `-10` in
BAB line. **Adjust feat string if on-boot validation confirms different casing.**

### Gate Tests (GTWF-001 – GTWF-008)

```python
# GTWF-001: Greater TWF feat, full attack → third off-hand attack appears in event sequence
# GTWF-002: ITWF only (no GTWF) → exactly two off-hand attacks; third not triggered (regression guard)
# GTWF-003: TWF only (no ITWF, no GTWF) → exactly one off-hand attack (regression guard)
# GTWF-004: GTWF third off-hand attack uses highest_bab - 10 as attack bonus
# GTWF-005: GTWF third off-hand: half-STR damage applied (same as first and second off-hand)
# GTWF-006: Main-hand iterative attacks unaffected by GTWF — count and bonuses unchanged
# GTWF-007: Three off-hand attack events emitted in sequence (event ordering: main then off-hand interleaved per existing pattern)
# GTWF-008: Regression — full suite of TWF events unaffected (CP-21 pattern preserved)
```

### Session Close Conditions
- [ ] `git add aidm/core/full_attack_resolver.py tests/test_engine_greater_twf_gate.py`
- [ ] `git commit`
- [ ] GTWF-001–GTWF-008: 8/8 PASS; zero regressions

---

## File Ownership

| WO | Files touched |
|---|---|
| WO1 | `spell_resolver.py` |
| WO2 | `aoo.py` |
| WO3 | `aoo.py` |
| WO4 | `full_attack_resolver.py` |

**WO2 and WO3 both touch `aoo.py`.** Commit WO2 before WO3. All other WOs are independent of each other.

**No overlap with Batch P** (`attack_resolver.py` / `maneuver_resolver.py` / `play_loop.py`).

---

## Regression Protocol

WO-specific gates first:
```bash
pytest tests/test_engine_improved_evasion_gate.py -v
pytest tests/test_engine_mobility_gate.py -v
pytest tests/test_engine_aoo_standing_prone_gate.py -v
pytest tests/test_engine_greater_twf_gate.py -v
```

Full suite after all committed:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. Record in debrief and stop. Do not loop.

**If WO2 (Mobility) encounters an unexpected bug in the deepcopy path:** diagnose without touching
`attack_resolver.py`. The deepcopy approach is the correct implementation path — escalate to PM if
`attack_resolver.py` changes appear required.

---

## Debrief Requirements

Three-pass format for all WOs executed.
- WO1 Pass 3: state SAI or new work. If SAI: confirm both branches at spell_resolver.py (line numbers).
  State whether `EF.IMPROVED_EVASION` was found at chargen and whether a chargen write was added. If
  NOT SAI: confirm insertion site in `_resolve_damage()` failed-save branch.
- WO2 Pass 3: confirm deepcopy path at `aoo.py:615-624` delivers correct +4 AC (evidence: gate test
  MB-001 passes). Document `FeatID.MOBILITY` resolution. Confirm stale TODO at `aoo.py:609-613` was
  removed. Confirm MB-006 (stand_from_prone trigger: no Mobility bonus).
- WO3 Pass 3: SAI confirmed — state file and line of existing `check_stand_from_prone_aoo()`.
  State gate file already existed (Batch I). File CLOSED on FINDING-CE-STANDING-AOO-001; confirm
  flat-footed reactor guard at `aoo.py:779` is present.
- WO4 Pass 3: state feat string actually used (Title Case vs lowercase — confirm from boot audit).
  Confirm `-10` vs `-5` BAB line. Confirm `current_hp > 0` guard. Confirm GTWF-005 (5-attack sequence) passes.

Post-debrief: ask builder "Anything else you noticed outside the debrief?" File loose threads before closing.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`
Missing debrief or missing Pass 3 → REJECT.

---

## Session Close Conditions

- [ ] All executed WOs committed with gate run before each
- [ ] IE: 8/8, MB: 8/8, SP: existing gate PASS (SAI confirmed), GTWF: 8/8
- [ ] Zero regressions
- [ ] Chisel kernel updated
- [ ] FINDING-CE-STANDING-AOO-001: CLOSED (flat-footed guard at aoo.py:779 confirmed)

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel per ops contract.*
