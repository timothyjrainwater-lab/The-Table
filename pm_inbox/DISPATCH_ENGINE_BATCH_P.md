# ENGINE DISPATCH — BATCH P (REVISED)
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**To:** Chisel (lead builder)
**Batch:** P — 4 WOs, 32 gate tests
**Prerequisite:** ENGINE BATCH O ACCEPTED

**Note:** WO detail is inline in this file. Combined format (inbox at cap).

**Planning correction:** Original Batch P (DG/LH/EV/UD) retracted — all 4 WOs were already accepted
in prior batches (Batch B R1, Batch C, Paladin/Immunity batch). Coverage map used without
cross-referencing briefing gate table. This revision contains genuinely new work.

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

**Batch N WO4 architecture note:** Improved Trip/Sunder AoO suppression was implemented in
`schemas/maneuvers.py + play_loop.py`, NOT `maneuver_resolver.py` or `aoo.py`. Read the
Improved Trip implementation from Batch N before writing WO2 and WO4.

**WO1 and WO3 both touch attack_resolver.py.** Commit WO1 first, then WO3.
**WO2 and WO4 both touch the maneuver resolution path.** Commit WO2 first, then WO4.

**EF.CLASS_LEVELS pattern:** `entity.get(EF.CLASS_LEVELS, {}).get("class_name", 0)`
**Event constructor:** `Event(event_id=..., event_type=..., payload=...)` — not `id=`, `type=`, `data=`

---

## WO 1 — WO-ENGINE-POWER-ATTACK-001

**Scope:** `aidm/core/attack_resolver.py`
**Gate file:** `tests/test_engine_power_attack_gate.py`
**Gate label:** ENGINE-POWER-ATTACK
**Gate count:** 8 tests (PA-001 – PA-008)
**Kernel touch:** NONE
**Source:** PHB p.98

### Gap Verification
Coverage map: NOT STARTED. Melee feat. Before attacking, declare a penalty (1–5, capped at current
BAB). Apply that penalty to ALL attack rolls this turn. Gain equal bonus to damage (1H weapon: ×1,
2H weapon: ×1.5 round down, off-hand: ×0.5 round down). Prerequisite: STR 13.

**Assumptions to Validate on boot:**
- Search "power_attack" in attack_resolver.py — if already present, SAI.
- Confirm how TEMPORARY_MODIFIERS pattern is cleared at turn start (same as fight_defensively, charge_ac).
- Confirm EF.TEMPORARY_MODIFIERS is a dict on entity (not a list).

### Implementation

Use `EF.TEMPORARY_MODIFIERS` dict pattern (same as Fight Defensively / Charge):

```python
# Declared at turn start via PowerAttackIntent(actor_id, penalty: int):
entity[EF.TEMPORARY_MODIFIERS]["power_attack_penalty"] = -penalty    # capped at BAB
entity[EF.TEMPORARY_MODIFIERS]["power_attack_damage_1h"] = +penalty
entity[EF.TEMPORARY_MODIFIERS]["power_attack_damage_2h"] = int(penalty * 1.5)
entity[EF.TEMPORARY_MODIFIERS]["power_attack_damage_offhand"] = penalty // 2
```

Clear at actor's turn start alongside fight_defensively/charge entries.

In `attack_resolver.py` attack roll: apply `power_attack_penalty` to all attack rolls this turn.
In damage calculation: read appropriate damage key based on weapon type (1h/2h/off-hand).

Guard: actor must have `"power_attack"` feat AND STR ≥ 13. If STR < 13, emit
`intent_validation_failed` with `reason="prerequisite_not_met"`. Penalty capped at current BAB.

### Gate Tests (PA-001 – PA-008)
```python
# PA-001: Power Attack -2 penalty → attack -2, damage +2 (1H weapon)
# PA-002: Power Attack -2 penalty → attack -2, damage +3 (2H weapon, 1.5×2=3)
# PA-003: Penalty capped at BAB (BAB 3, declared 5 → actual penalty 3)
# PA-004: No feat → intent_validation_failed
# PA-005: STR 12 (< 13) → intent_validation_failed reason="prerequisite_not_met"
# PA-006: Modifier clears at start of next turn
# PA-007: Full attack while PA active → penalty applies to ALL iterative attacks
# PA-008: Power Attack + weapon enhancement → damage bonuses are additive
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_power_attack_gate.py`
- [ ] `git commit`
- [ ] PA-001–PA-008: 8/8 PASS; zero regressions

---

## WO 2 — WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001

**Scope:** `aidm/core/maneuver_resolver.py` (or schemas/maneuvers.py + play_loop.py — read Batch N WO4 first)
**Gate file:** `tests/test_engine_improved_maneuver_bonuses_gate.py`
**Gate label:** ENGINE-IMPROVED-MANEUVER-BONUSES
**Gate count:** 8 tests (IMB-001 – IMB-008)
**Kernel touch:** NONE
**Source:** PHB p.96–98

### Gap Verification
Closes 5 open findings simultaneously:
- FINDING-ENGINE-IMPROVED-DISARM-BONUS-001 — Improved Disarm +4 bonus
- FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001 — Improved Grapple +4 bonus
- FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001 — Improved Bull Rush +4 bonus
- FINDING-ENGINE-IMPROVED-TRIP-BONUS-001 — Improved Trip +4 bonus
- FINDING-ENGINE-IMPROVED-SUNDER-BONUS-001 — Improved Sunder +4 bonus

All follow the same pattern: feat check → +4 to opposed check/attack roll for that maneuver.

**Assumptions to Validate on boot:**
- Read the Batch N WO4 implementation for Improved Trip AoO suppression — find the exact file
  and line where feat checks happen for maneuvers.
- Confirm whether the +4 bonus goes into the same resolution path or needs a separate site.
- Confirm "improved_disarm", "improved_grapple", "improved_bull_rush", "improved_trip",
  "improved_sunder" feat ID strings from schemas/feats.py.

### Implementation

At each maneuver's opposed-check accumulation site, add:
```python
# Improved Disarm bonus
if "improved_disarm" in attacker.get(EF.FEATS, []):
    disarm_bonus += 4

# Improved Grapple bonus
if "improved_grapple" in attacker.get(EF.FEATS, []):
    grapple_bonus += 4

# Improved Bull Rush bonus
if "improved_bull_rush" in attacker.get(EF.FEATS, []):
    bull_rush_bonus += 4

# Improved Trip bonus
if "improved_trip" in attacker.get(EF.FEATS, []):
    trip_bonus += 4

# Improved Sunder bonus
if "improved_sunder" in attacker.get(EF.FEATS, []):
    sunder_bonus += 4
```

Apply each bonus only at the correct maneuver resolution call. No cross-contamination.

### Gate Tests (IMB-001 – IMB-008)
```python
# IMB-001: Improved Disarm feat → +4 to disarm opposed check total
# IMB-002: Improved Grapple feat → +4 to grapple check total
# IMB-003: Improved Bull Rush feat → +4 to bull rush STR check total
# IMB-004: Improved Trip feat → +4 to trip opposed check total
# IMB-005: Improved Sunder feat → +4 to sunder attack roll total
# IMB-006: No feat → no bonus on any maneuver (regression check)
# IMB-007: Bonus stacks correctly with STR modifier (total = STR_mod + base + 4)
# IMB-008: Entity with multiple improved feats → each applies to its own maneuver only
```

### Session Close Conditions
- [ ] `git add` (relevant files per architecture) `tests/test_engine_improved_maneuver_bonuses_gate.py`
- [ ] `git commit`
- [ ] IMB-001–IMB-008: 8/8 PASS; zero regressions
- [ ] Note in debrief: 5 FINDINGs closed simultaneously

---

## WO 3 — WO-ENGINE-PRECISE-SHOT-001

**Scope:** `aidm/core/attack_resolver.py` (commit WO1 first)
**Gate file:** `tests/test_engine_precise_shot_gate.py`
**Gate label:** ENGINE-PRECISE-SHOT
**Gate count:** 8 tests (PS-001 – PS-008)
**Kernel touch:** NONE
**Source:** PHB p.99

### Gap Verification
Coverage map: NOT STARTED (check first — no untracked test file seen, likely new work).
Precise Shot: removes the standard −4 attack penalty when making a ranged attack against a target
that is engaged in melee combat. Prerequisite: Point Blank Shot.

**Assumptions to Validate on boot:**
- Find where the −4 "firing into melee" penalty is applied in attack_resolver.py.
  Search for "into_melee" or "-4" or "firing_into_melee" to locate the guard.
- Confirm "precise_shot" feat ID string in schemas/feats.py.
- Confirm "point_blank_shot" is the prerequisite (PHB p.99) — this WO does not enforce the
  prerequisite chain, just wires the mechanic.

### Implementation

At the "firing into melee" penalty site in `attack_resolver.py`:
```python
# Before applying -4 firing-into-melee penalty:
if target_is_engaged_in_melee and not ("precise_shot" in attacker.get(EF.FEATS, [])):
    attack_bonus -= 4
# else: Precise Shot suppresses the penalty entirely
```

If the penalty is not yet implemented, implement it at the same time: when making a ranged attack
and the target has a melee combatant adjacent to it (or has GRAPPLED condition), apply −4 unless
attacker has Precise Shot.

### Gate Tests (PS-001 – PS-008)
```python
# PS-001: Ranged attacker with Precise Shot, target in melee → no -4 penalty
# PS-002: Ranged attacker WITHOUT Precise Shot, target in melee → -4 penalty applied
# PS-003: Ranged attack with Precise Shot, target NOT in melee → no penalty (baseline)
# PS-004: Melee attack with Precise Shot → feat has no effect (ranged only)
# PS-005: -4 penalty applies correctly without feat (regression baseline)
# PS-006: Precise Shot + Rapid Shot → both independent (no interaction)
# PS-007: precise_shot_active=True in attack event payload when feat suppresses penalty
# PS-008: No feat registered → behavior identical to pre-WO state
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_precise_shot_gate.py`
- [ ] `git commit`
- [ ] PS-001–PS-008: 8/8 PASS; zero regressions

---

## WO 4 — WO-ENGINE-IMPROVED-DISARM-COUNTER-001

**Scope:** Same files as WO2 (commit WO2 first)
**Gate file:** `tests/test_engine_improved_disarm_counter_gate.py`
**Gate label:** ENGINE-IMPROVED-DISARM-COUNTER
**Gate count:** 8 tests (IDC-001 – IDC-008)
**Kernel touch:** NONE
**Source:** PHB p.96

### Gap Verification
FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 OPEN. PHB p.96 Disarm rules: if the attacker fails
the opposed disarm check by 10 or more, the attacker is themselves disarmed (counter-disarm).
However: with Improved Disarm feat, "your opponent does not get a chance to disarm you." This
protection — the counter-disarm suppression — is NOT currently wired.

**Assumptions to Validate on boot:**
- Find where the "fail by 10+" → attacker disarmed logic is implemented (same files as WO2).
- Confirm the counter-disarm fires when attacker_roll + 0 <= defender_roll - 10 (i.e., fail by 10+).
- Confirm "improved_disarm" feat ID string (same as WO2).

### Implementation

At the counter-disarm site (where attacker gets disarmed on fail by 10+):
```python
# Before applying counter-disarm to attacker:
margin = defender_total - attacker_total  # positive = attacker failed
if margin >= 10:
    if "improved_disarm" not in attacker.get(EF.FEATS, []):
        # Counter-disarm: attacker drops weapon
        attacker[EF.DISARMED] = True
        events.append(Event(..., event_type="counter_disarmed",
                            payload={"entity_id": attacker_id}))
    else:
        # Improved Disarm: counter-disarm suppressed
        events.append(Event(..., event_type="counter_disarm_suppressed",
                            payload={"entity_id": attacker_id}))
```

### Gate Tests (IDC-001 – IDC-008)
```python
# IDC-001: Without Improved Disarm, fail by 10+ → attacker DISARMED (existing behavior preserved)
# IDC-002: WITH Improved Disarm, fail by 10+ → attacker NOT disarmed (counter_disarm_suppressed)
# IDC-003: WITH Improved Disarm, fail by 9 (< 10) → no counter-disarm either way (boundary)
# IDC-004: Improved Disarm succeeds → target DISARMED normally (no change to success path)
# IDC-005: Without Improved Disarm, fail by exactly 10 → counter-disarm fires (boundary)
# IDC-006: counter_disarm_suppressed event emitted when feat prevents counter-disarm
# IDC-007: Non-disarm maneuver unaffected by Improved Disarm feat
# IDC-008: Regression — Improved Disarm AoO suppression (Batch L/N) still active after this WO
```

### Session Close Conditions
- [ ] `git add` (relevant files) `tests/test_engine_improved_disarm_counter_gate.py`
- [ ] `git commit`
- [ ] IDC-001–IDC-008: 8/8 PASS; zero regressions
- [ ] FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 CLOSED in debrief

---

## File Ownership

| WO | Files touched |
|---|---|
| WO1 | attack_resolver.py |
| WO2 | maneuver resolution path (schemas/maneuvers.py + play_loop.py per Batch N WO4 pattern) |
| WO3 | attack_resolver.py ← same as WO1, commit WO1 first |
| WO4 | same as WO2, commit WO2 first |

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
- WO1 Pass 3: document whether Power Attack was truly NOT STARTED or if partial exists; confirm
  2H vs 1H multiplier implementation site; confirm turn-start clear location
- WO2 Pass 3: cite exact file + line for Batch N WO4 Improved Trip pattern used as reference;
  confirm all 5 FINDINGs closed; note if +4 bonus was in same resolution site or different
- WO3 Pass 3: document where the -4 firing-into-melee penalty was implemented; if it didn't
  exist, note that it was implemented fresh as part of this WO (both the penalty and the feat bypass)
- WO4 Pass 3: document whether counter-disarm (fail by 10+) was already wired or also needed
  fresh implementation; confirm FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 CLOSED

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
