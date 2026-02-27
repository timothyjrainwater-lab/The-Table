# ENGINE DISPATCH — BATCH P
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Lifecycle:** DISPATCH-READY
**To:** Chisel (lead builder)
**Batch:** P — 4 WOs, 32 gate tests
**Prerequisite:** ENGINE BATCH O ACCEPTED

**Note:** WO detail is inline in this file. Combined format (inbox at cap).

**Planning note:** Original Batch P (DG/LH/EV/UD) retracted — all 4 were already accepted in prior batches (Batch B R1, Batch C, Paladin/Immunity). Current content is genuine new work.

---

## Boot Sequence

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm Batch O ACCEPTED — verify IO/CE/BF/TG gate counts
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md`
4. Run `python scripts/verify_session_start.py`
5. Orphan check: any WO IN EXECUTION with no debrief? Flag before proceeding.
6. Record pre-existing failure count: `pytest --tb=no -q`

---

## Intelligence Update

**File conflicts:**
- WO1 (PA) and WO3 (PS) both touch `attack_resolver.py`. Commit WO1 before WO3.
- WO2 (IMB) and WO4 (IDC) both touch `schemas/maneuvers.py` + `play_loop.py`. Commit WO2 before WO4.

**Recommended commit order:** WO1 → WO2 → WO3 → WO4.

**Batch N WO4 architecture note:** Improved maneuver path lives in `schemas/maneuvers.py` + `play_loop.py` — NOT `maneuver_resolver.py` or `aoo.py`. Confirmed by Chisel during Batch N execution.

**EF.TEMPORARY_MODIFIERS pattern (Power Attack):** Same pattern as Fight Defensively and Combat Expertise. Declare penalty before rolling; store in EF.TEMPORARY_MODIFIERS. Clear at turn start (already handled by play_loop.py turn reset). Check Combat Expertise implementation from Batch C as the reference pattern.

**EF.CLASS_LEVELS pattern:** `entity.get(EF.CLASS_LEVELS, {}).get("class_name", 0)` — EF.CLASS_FEATURES does not exist.

**Event constructor:** `Event(event_id=..., event_type=..., payload=...)` — not `id=`, `type=`, `data=`.

**Improved maneuver bonus context:**
- IMPROVED-DISARM, IMPROVED-GRAPPLE, IMPROVED-BULL-RUSH: +4 wired in Batch L. Open FINDINGs indicate secondary call sites may be missing the bonus. WO2 audits all call sites and closes findings.
- IMPROVED-TRIP, IMPROVED-SUNDER: +4 bonus NOT yet wired at any call site. WO2 adds it fresh.

---

## WO 1 — WO-ENGINE-POWER-ATTACK-001

**Scope:** `aidm/core/attack_resolver.py`
**Gate file:** `tests/test_engine_power_attack_gate.py`
**Gate label:** ENGINE-POWER-ATTACK
**Gate count:** 8 tests (PA-001 – PA-008)
**Kernel touch:** NONE
**Source:** PHB p.98

### Gap Verification

Coverage map: MISSING. Before attacking, declare penalty N (1 ≤ N ≤ BAB, not more than 5 in most cases). -N to all attack rolls in the round. +N to damage with 1H weapon or natural attack. +floor(N×1.5) to damage with 2H weapon. +floor(N×0.5) to damage with off-hand weapon (TWF). Prerequisite: STR 13 (enforced at chargen; gate tests check feat presence only).

**Assumptions to Validate on boot:**
- Confirm no existing `power_attack` handling in attack_resolver.py or EF.TEMPORARY_MODIFIERS.
- Confirm `Weapon.weapon_type` values: `light`, `one-handed`, `two-handed`, `ranged`, `natural`. Use this to determine damage multiplier (1×, 1.5×, 0.5×).
- Check how Combat Expertise was wired in Batch C (AttackIntent attribute vs separate intent). Mirror the same pattern for consistency.

### Implementation

Add `power_attack_penalty: int = 0` to `AttackIntent` and `FullAttackIntent` (same pattern as `combat_expertise_penalty` from Batch C).

In `attack_resolver.py`, apply before rolling:
```python
pa_penalty = intent.power_attack_penalty  # 0 if not declared
if pa_penalty > 0:
    if pa_penalty > attacker_bab:
        raise ValidationError("penalty_exceeds_bab")
    attack_roll -= pa_penalty
    # Damage bonus based on weapon_type:
    if weapon.weapon_type == "two-handed":
        damage_bonus += int(pa_penalty * 1.5)
    elif weapon.weapon_type in ("light", "one-handed", "natural"):
        damage_bonus += pa_penalty
    else:  # off-hand (TWF context)
        damage_bonus += pa_penalty // 2
```

Feat guard: if `"power_attack" not in attacker_feats` and `pa_penalty > 0`, emit `intent_validation_failed`.

### Gate Tests (PA-001 – PA-008)

```python
# PA-001: PA=2, 1H weapon, BAB=6 → attack roll -2, damage +2
# PA-002: PA=2, 2H weapon → damage +3 (floor(2×1.5)=3)
# PA-003: PA=2, off-hand weapon (TWF) → damage +1 (floor(2×0.5)=1)
# PA-004: PA=N where N > BAB (BAB=2, declare PA=3) → validation_failed "penalty_exceeds_bab"
# PA-005: PA=0 declared → no effect (or treat 0 as undeclared; no error)
# PA-006: Actor without Power Attack feat, PA=2 → validation_failed "feat_requirement_not_met"
# PA-007: Full attack with PA=3 → all iterative attacks in the round have -3 penalty
# PA-008: PA bonus stacks with other modifiers (Weapon Focus +1) — net roll and damage correct
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_power_attack_gate.py`
- [ ] `git commit`
- [ ] PA-001–PA-008: 8/8 PASS; zero regressions

---

## WO 2 — WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001

**Scope:** `aidm/schemas/maneuvers.py`, `aidm/core/play_loop.py`
**Gate file:** `tests/test_engine_improved_maneuver_bonuses_gate.py`
**Gate label:** ENGINE-IMPROVED-MANEUVER-BONUSES
**Gate count:** 8 tests (IMB-001 – IMB-008)
**Kernel touch:** NONE
**Source:** PHB p.95–98

**Closes:** FINDING-ENGINE-IMPROVED-DISARM-BONUS-001, FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001, FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001, FINDING-ENGINE-IMPROVED-TRIP-BONUS-001, FINDING-ENGINE-IMPROVED-SUNDER-BONUS-001

### Gap Verification

Batch L wired Improved Disarm / Grapple / Bull Rush core mechanics (+4 bonus in main path). Open FINDINGs indicate secondary call sites may be missing the bonus (e.g., follow-through bull rush after charge, secondary grapple check paths).

Batch N WO4 deferred Improved Trip +4 STR check bonus (debrief note: "free attack wired but +4 bonus not wired"). Improved Sunder +4 opposed attack bonus: not wired at any call site.

**Assumptions to Validate on boot:**
- Read `schemas/maneuvers.py` — trace each maneuver's opposed check computation. Identify ALL call sites for disarm/grapple/bull rush feat bonus. Document which are wired and which are missing.
- Read `play_loop.py` — locate maneuver dispatch paths. For trip (same `elif` pattern introduced Batch N WO4) and sunder, find where opposed check is resolved.
- For trip: `TripIntent.weapon: Optional[Weapon]` was added Batch N WO4. The +4 STR check bonus is separate from the free-attack; add it in the trip opposed check path.
- For sunder: locate sunder opposed check path. Add `if "improved_sunder" in attacker_feats: attacker_check += 4`.

### Implementation

For TRIP and SUNDER (new work):
```python
# In trip opposed check resolution:
if "improved_trip" in attacker_feats:
    attacker_check += 4

# In sunder opposed check resolution:
if "improved_sunder" in attacker_feats:
    attacker_check += 4
```

For DISARM, GRAPPLE, BULL RUSH (audit):
Trace each maneuver from play_loop.py through to every opposed check computation site. At any site missing the feat bonus, add the `if feat in feats: check += 4` guard. Document each site in the debrief.

### Gate Tests (IMB-001 – IMB-008)

```python
# IMB-001: Improved Trip attacker → +4 to trip STR opposed check (new work)
# IMB-002: Improved Sunder attacker → +4 to sunder opposed attack roll (new work)
# IMB-003: Improved Disarm attacker → +4 applied at ALL disarm check sites (includes secondary paths)
# IMB-004: Improved Grapple attacker → +4 applied at all grapple check paths
# IMB-005: Improved Bull Rush attacker → +4 for follow-through bull rush (after initial charge)
# IMB-006: No improved feat → no bonus on any maneuver (regression guard)
# IMB-007: Multiple improved feats held → each applies only to its own maneuver
# IMB-008: +4 bonus appears in maneuver_result event payload for all 5 maneuvers
```

### Session Close Conditions
- [ ] `git add aidm/schemas/maneuvers.py aidm/core/play_loop.py tests/test_engine_improved_maneuver_bonuses_gate.py`
- [ ] `git commit`
- [ ] IMB-001–IMB-008: 8/8 PASS; zero regressions
- [ ] File CLOSED on all 5 maneuver bonus FINDINGs in debrief

---

## WO 3 — WO-ENGINE-PRECISE-SHOT-001

**Scope:** `aidm/core/attack_resolver.py`
**Gate file:** `tests/test_engine_precise_shot_gate.py`
**Gate label:** ENGINE-PRECISE-SHOT
**Gate count:** 8 tests (PS-001 – PS-008)
**Kernel touch:** NONE
**Source:** PHB p.99

**Commit WO1 first** — both WO1 and WO3 touch `attack_resolver.py`.

### Gap Verification

Coverage map: MISSING. Ranged attacks into melee (target adjacent to an enemy) currently take -4 penalty (PHB p.140). Precise Shot feat removes this penalty entirely. Prerequisite: Point Blank Shot (enforced at chargen; gate tests check feat presence). Precise Shot does not affect Point Blank Shot's +1/+1 bonus; they are independent.

**Assumptions to Validate on boot:**
- Search `attack_resolver.py` for existing ranged-into-melee penalty code. Confirm the -4 is currently applied unconditionally.
- Confirm how "target has adjacent enemy" is determined. If a `_is_target_in_melee()` helper exists (used for flanking/cleave), reuse it.
- Confirm Precise Shot feat key in registry: `"precise_shot"` (lowercase, underscore). Verify against the feat data from WO-DATA-FEATS-001.

### Implementation

In `attack_resolver.py`, in the ranged attack path, where the -4 into-melee penalty is applied:
```python
if is_ranged and _is_target_in_melee(target, world_state):
    if "precise_shot" not in attacker_feats:
        attack_roll -= 4
    else:
        events.append(Event(..., event_type="precise_shot_active",
                            payload={"actor_id": attacker_id}))
```

If `_is_target_in_melee()` does not exist, implement it as: target has at least one non-allied creature within 5 feet (using position data, same logic as flanking adjacency from Batch C Cleave WO).

### Gate Tests (PS-001 – PS-008)

```python
# PS-001: Ranged attack, target in melee, attacker HAS Precise Shot → no -4 penalty
# PS-002: Ranged attack, target in melee, attacker lacks Precise Shot → -4 applied
# PS-003: Ranged attack, target NOT in melee → no penalty regardless of feat
# PS-004: Melee attack, target in melee → Precise Shot irrelevant; no ranged penalty
# PS-005: Precise Shot active → precise_shot_active event emitted in event sequence
# PS-006: Precise Shot + Point Blank Shot → PBShot +1/+1 bonus unaffected; both apply
# PS-007: Full-attack with ranged: second iterative attack also has no -4 (feat covers round)
# PS-008: Regression — after WO1 (PA) commit, non-Precise-Shot actor still gets -4 into melee
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_precise_shot_gate.py`
- [ ] `git commit`
- [ ] PS-001–PS-008: 8/8 PASS; zero regressions

---

## WO 4 — WO-ENGINE-IMPROVED-DISARM-COUNTER-001

**Scope:** `aidm/schemas/maneuvers.py`, `aidm/core/play_loop.py`
**Gate file:** `tests/test_engine_improved_disarm_counter_gate.py`
**Gate label:** ENGINE-IMPROVED-DISARM-COUNTER
**Gate count:** 8 tests (IDC-001 – IDC-008)
**Kernel touch:** NONE
**Source:** PHB p.96

**Closes:** FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001

**Commit WO2 first** — both WO2 and WO4 touch `schemas/maneuvers.py` + `play_loop.py`.

### Gap Verification

PHB p.96: "If your disarm attempt fails by 10 or more, the target may immediately attempt to disarm you with the same kind of action and you lose your Dexterity bonus to AC (if any) against this disarm attempt." With **Improved Disarm feat**: attacker is NOT subject to this counter-disarm.

FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 was filed from Batch L debrief: "opponent's failed disarm attempt should not disarm attacker with feat." The base counter-disarm trigger may or may not be implemented — check on boot.

**Assumptions to Validate on boot:**
- In `play_loop.py` / `schemas/maneuvers.py`: search for counter-disarm logic. If it exists, determine the exact trigger condition (margin ≥ 10).
- If counter-disarm base is NOT implemented: implement both the base trigger AND the Improved Disarm suppression in this WO. Document both in debrief.
- Confirm: "fail by 10+" means `defender_check - attacker_check >= 10`. IDC-003 (fail by 9) and IDC-004 (fail by exactly 10) bracket the boundary.

### Implementation

In the disarm resolution path:
```python
margin = defender_check - attacker_check
if margin >= 10:
    if "improved_disarm" in attacker_feats:
        events.append(Event(..., event_type="counter_disarm_suppressed",
                            payload={"feat": "improved_disarm", "actor_id": attacker_id}))
    else:
        # Trigger counter-disarm: defender gets free disarm attempt on attacker
        # Attacker loses DEX to AC for this counter attempt
        _trigger_counter_disarm(attacker_id, defender_id, world_state, events)
```

If `_trigger_counter_disarm()` doesn't exist, implement it inline or as a small helper that resolves the counter with normal disarm rules but the attacker is treated as flat-footed (DEX stripped from AC) for that single attempt.

### Gate Tests (IDC-001 – IDC-008)

```python
# IDC-001: Attacker WITH Improved Disarm, fails by 10+ → no counter-disarm triggered
# IDC-002: Attacker WITHOUT Improved Disarm, fails by 10+ → counter-disarm triggered
# IDC-003: Attacker fails by 9 → no counter-disarm either way (below threshold)
# IDC-004: Attacker fails by exactly 10 → counter-disarm IS triggered (boundary)
# IDC-005: Attacker succeeds at disarm → no counter-disarm regardless of feat
# IDC-006: Counter-disarm uses normal disarm resolution (not auto-success for defender)
# IDC-007: counter_disarm_suppressed event emitted when Improved Disarm active (IDC-001 case)
# IDC-008: Regression — standard disarm (margin < 10) unaffected after WO2 (IMB) commit
```

### Session Close Conditions
- [ ] `git add aidm/schemas/maneuvers.py aidm/core/play_loop.py tests/test_engine_improved_disarm_counter_gate.py`
- [ ] `git commit`
- [ ] IDC-001–IDC-008: 8/8 PASS; zero regressions
- [ ] FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001: CLOSED in debrief

---

## File Ownership

| WO | Files touched |
|---|---|
| WO1 | `attack_resolver.py` |
| WO2 | `schemas/maneuvers.py`, `play_loop.py` |
| WO3 | `attack_resolver.py` |
| WO4 | `schemas/maneuvers.py`, `play_loop.py` |

**WO1 and WO3 both touch attack_resolver.py.** Commit WO1 first, then WO3 builds on it.

**WO2 and WO4 both touch maneuvers.py + play_loop.py.** Commit WO2 first, then WO4 builds on it.

**Recommended commit order:** WO1 → WO2 → WO3 → WO4.

---

## Regression Protocol

WO-specific gates first:
```bash
pytest tests/test_engine_power_attack_gate.py -v
pytest tests/test_engine_improved_maneuver_bonuses_gate.py -v
pytest tests/test_engine_precise_shot_gate.py -v
pytest tests/test_engine_improved_disarm_counter_gate.py -v
```

Full suite after all committed:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. Record in debrief and stop. Do not loop.

---

## Debrief Requirements

Three-pass format for all 4 WOs.
- WO1 Pass 3: note which Combat Expertise pattern was used for intent (attribute on AttackIntent vs separate intent); document 2H multiplier (1.5×) and off-hand multiplier (0.5×) implementation; confirm feat key string used
- WO2 Pass 3: for each of 5 maneuvers — explicitly state where the +4 was added/confirmed; file CLOSED on each finding; document any secondary call sites that were missing for disarm/grapple/bull rush
- WO3 Pass 3: document how "target in melee" adjacency was determined (existing helper or new); confirm Precise Shot feat string; note Point Blank Shot interaction
- WO4 Pass 3: document whether counter-disarm base was already implemented or newly added; confirm threshold boundary behavior (≥10 vs >10); confirm attacker DEX-stripped behavior on counter

Post-debrief: ask builder "Anything else you noticed outside the debrief?" File loose threads before closing.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`
Missing debrief or missing Pass 3 → REJECT.

---

## Session Close Conditions

- [ ] All 4 WOs committed with gate run before each
- [ ] PA: 8/8, IMB: 8/8, PS: 8/8, IDC: 8/8
- [ ] Zero regressions
- [ ] Chisel kernel updated

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel per ops contract.*
