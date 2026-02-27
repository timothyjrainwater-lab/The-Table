# ENGINE DISPATCH — BATCH O
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**To:** Chisel (lead builder)
**Batch:** O — 4 WOs, 32 gate tests
**Prerequisite:** ENGINE BATCH N ACCEPTED

**Note:** WO detail is inline in this file. Individual dispatch files created after Batch M clears inbox slots.

---

## Boot Sequence

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm Batch N ACCEPTED — verify MD/SA/SF/IT gate counts
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md`
4. Run `python scripts/verify_session_start.py`
5. Orphan check: any WO IN EXECUTION with no debrief? Flag before proceeding.
6. Record pre-existing failure count: `pytest --tb=no -q`

---

## Intelligence Update

**Event constructor:** `Event(event_id=..., event_type=..., payload=...)` — not `id=`, `type=`, `data=`.
**EF.CLASS_LEVELS:** `entity.get(EF.CLASS_LEVELS, {}).get("class_name", 0)` — `EF.CLASS_FEATURES` does not exist.
**Fight Defensively/Total Defense pattern:** Already implemented via `EF.TEMPORARY_MODIFIERS` dict. WO2 (Combat Expertise) uses the same pattern — reference that implementation before writing.
**SAI guard — untracked test file:** `tests/test_engine_combat_expertise_gate.py` is untracked. Read it on boot for WO2. If it has complete tests and they pass: commit the file, finding CLOSED, zero production changes.

---

## WO 1 — WO-ENGINE-IMPROVED-OVERRUN-001

**Scope:** `aidm/core/maneuver_resolver.py`, `aidm/core/aoo.py`
**Gate file:** `tests/test_engine_improved_overrun_gate.py`
**Gate label:** ENGINE-IMPROVED-OVERRUN
**Gate count:** 8 tests (IO-001 – IO-008)
**Kernel touch:** NONE
**Source:** PHB p.96/158 + FINDING-ENGINE-IMPROVED-OVERRUN-AOO-001 (deferred from Batch L)

### Gap Verification
Improved Overrun: (1) no AoO on overrun attempt, (2) defender cannot choose to avoid (must take the opposed check). Coverage map: PARTIAL — feat registered, neither mechanic wired.

**Assumptions to Validate on boot:**
- Confirm AoO suppression for Improved Disarm/Grapple/Bull Rush (Batch L) is in `aoo.py` — reference that pattern exactly.
- Confirm `maneuver_resolver.py` `resolve_overrun()` has a defender-avoid path and identify its guard condition.
- Search for "improved_overrun" in aoo.py — if AoO suppression already present, SAI.

### Implementation

**Part 1 — AoO suppression (aoo.py):** When `OverrunIntent` triggers AoO from target, check attacker feat `"improved_overrun"`. If present, suppress. Same pattern as Improved Disarm/Grapple/Bull Rush in Batch L.

**Part 2 — Defender cannot avoid (maneuver_resolver.py):** In `resolve_overrun()`, after the AoO step and before the defender-avoid check, add:
```python
if "improved_overrun" in attacker.get(EF.FEATS, []):
    # Defender cannot choose to avoid — skip the avoid path, force opposed check
    defender_avoided = False
```

### Gate Tests (IO-001 – IO-008)
```python
# IO-001: Improved Overrun feat → no AoO on overrun attempt from target
# IO-002: No feat → AoO fires on overrun (existing behavior preserved)
# IO-003: Improved Overrun → defender cannot avoid (forced into opposed check)
# IO-004: No feat → defender CAN choose to avoid (existing behavior preserved)
# IO-005: Defender avoidance suppressed; opposed STR check still resolves normally
# IO-006: Overrun succeeds (STR check passes) with feat → target knocked prone
# IO-007: Overrun fails (STR check fails) with feat → attacker stops (no prone)
# IO-008: No AoO AND no avoid-path simultaneously — both suppressed correctly
```

### Session Close Conditions
- [ ] `git add aidm/core/maneuver_resolver.py aidm/core/aoo.py tests/test_engine_improved_overrun_gate.py`
- [ ] `git commit`
- [ ] IO-001–IO-008: 8/8 PASS; zero regressions

---

## WO 2 — WO-ENGINE-COMBAT-EXPERTISE-001

**Scope:** `aidm/core/attack_resolver.py`, `aidm/core/play_loop.py`
**Gate file:** `tests/test_engine_combat_expertise_gate.py`
**Gate label:** ENGINE-COMBAT-EXPERTISE
**Gate count:** 8 tests (CE-001 – CE-008)
**Kernel touch:** NONE
**Source:** PHB p.92

### Gap Verification
Coverage map: PARTIAL — feat registered in `schemas/feats.py`, trade-attack-for-AC mechanic not wired.
**⚠ `tests/test_engine_combat_expertise_gate.py` is untracked. Read it on boot — may be SAI.**

### Implementation

Same pattern as Fight Defensively (`EF.TEMPORARY_MODIFIERS`). `CombatExpertiseIntent(actor_id, penalty: int)` where penalty is 1–5 (capped at actor's BAB).

In `play_loop.py` execute_turn routing: `CombatExpertiseIntent` → store into `EF.TEMPORARY_MODIFIERS`:
```python
# Keys mirror Fight Defensively pattern:
entity[EF.TEMPORARY_MODIFIERS]["combat_expertise_attack"] = -penalty
entity[EF.TEMPORARY_MODIFIERS]["combat_expertise_ac"] = +penalty   # dodge type
```

Clear at turn start alongside fight_defensively entries.

In `attack_resolver.py` attack accumulation: read `combat_expertise_attack` penalty and apply to attack roll. In AC calculation: read `combat_expertise_ac` and add as dodge bonus (stackable with Dodge feat per PHB).

**Prerequisite check:** `"improved_trip"` requires Combat Expertise — feat is registered but this WO does not need to enforce that prerequisite chain. Just wire the mechanic.

**Guard:** Entity must have `"combat_expertise"` feat AND INT ≥ 13 to declare the intent. If INT < 13, emit `intent_validation_failed` with `reason="prerequisite_not_met"`.

### Gate Tests (CE-001 – CE-008)
```python
# CE-001: Combat Expertise -2 penalty → attack roll -2, AC +2 dodge
# CE-002: Combat Expertise -5 penalty → attack roll -5, AC +5 dodge
# CE-003: Penalty capped at BAB (BAB 3 → max penalty 3 even if 5 declared)
# CE-004: No feat → intent_validation_failed
# CE-005: INT < 13 → intent_validation_failed reason="prerequisite_not_met"
# CE-006: Modifier clears at start of next turn
# CE-007: Combat Expertise stacks with Dodge feat AC (+1 designated target)
# CE-008: Full attack while CE active → penalty applies to all iterative attacks
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py aidm/core/play_loop.py tests/test_engine_combat_expertise_gate.py`
- [ ] `git commit`
- [ ] CE-001–CE-008: 8/8 PASS; zero regressions

---

## WO 3 — WO-ENGINE-BLIND-FIGHT-001

**Scope:** `aidm/core/attack_resolver.py`, `aidm/core/concealment.py` (or wherever miss chance is resolved)
**Gate file:** `tests/test_engine_blind_fight_gate.py`
**Gate label:** ENGINE-BLIND-FIGHT
**Gate count:** 8 tests (BF-001 – BF-008)
**Kernel touch:** NONE
**Source:** PHB p.91

### Gap Verification
Coverage map: PARTIAL — feat registered, "reroll miss chance not wired." Normal concealment (50% miss chance) rolls d100; if miss, attack fails. With Blind-Fight: on a miss roll, reroll the d100 once. If the reroll also fails, attack misses. Net effect: 50% → 25% effective miss on attacks (50%×50%).

**Assumptions to Validate on boot:**
- Find the exact line in `attack_resolver.py` or `concealment.py` where the d100 miss chance is rolled and the result checked.
- Confirm `"blind_fight"` feat ID string in `schemas/feats.py`.

### Implementation

At the miss-chance resolution site, after `roll = rng.randint(1, 100)` and the miss check:
```python
if roll <= miss_chance:
    # Normal miss — but check Blind-Fight reroll
    if "blind_fight" in attacker.get(EF.FEATS, []):
        reroll = rng.randint(1, 100)
        if reroll > miss_chance:
            # Reroll succeeds — attack proceeds past miss chance
            events.append(Event(..., event_type="blind_fight_reroll",
                                payload={"attacker_id": ..., "original_roll": roll,
                                         "reroll": reroll}))
            # Continue to attack resolution
        else:
            # Both rolls failed — miss
            events.append(Event(..., event_type="miss_concealment", ...))
            return events
    else:
        # No feat — original miss stands
        return events
```

Note: Blind-Fight also grants other benefits (melee attackers do not lose DEX bonus vs invisible; ignore penalty for fighting invisible creature). These require more investigation of the invisibility path. **Scope this WO to the miss chance reroll only. File FINDING-ENGINE-BLIND-FIGHT-INVIS-001 (LOW) for the invisible attacker path.**

### Gate Tests (BF-001 – BF-008)
```python
# BF-001: Blind-Fight feat → miss chance reroll triggers on initial miss (seeded RNG)
# BF-002: Reroll succeeds → attack proceeds past concealment (blind_fight_reroll event)
# BF-003: Both rolls fail → attack misses
# BF-004: No Blind-Fight feat → no reroll on miss (existing behavior)
# BF-005: 20% miss chance (partial concealment) — reroll fires on miss
# BF-006: 50% miss chance (full concealment) — reroll fires on miss
# BF-007: Miss chance = 0 → no reroll triggered (no miss chance to check)
# BF-008: Event sequence: blind_fight_reroll appears before hit/miss resolution event
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_blind_fight_gate.py`
- [ ] `git commit`
- [ ] BF-001–BF-008: 8/8 PASS; zero regressions
- [ ] File FINDING-ENGINE-BLIND-FIGHT-INVIS-001 LOW in debrief

---

## WO 4 — WO-ENGINE-TOUGHNESS-001

**Scope:** `aidm/chargen/builder.py`
**Gate file:** `tests/test_engine_toughness_gate.py`
**Gate label:** ENGINE-TOUGHNESS
**Gate count:** 8 tests (TG-001 – TG-008)
**Kernel touch:** KERNEL-01 (Entity Lifecycle — HP_MAX set at creation)
**Source:** PHB p.101

### Gap Verification
Coverage map: PARTIAL — feat registered `(+3 HP); not auto-applied at chargen`. The feat is awarded at chargen level-up via feat slots, but HP_MAX is not incremented.

**Assumptions to Validate on boot:**
- Confirm `builder.py` or `level_up()` does NOT already add +3 HP for Toughness. Search "toughness" in builder.py.
- Confirm `EF.HP_MAX` and `EF.HP` are both set at chargen — both must be incremented.
- Confirm Toughness can be taken multiple times (each instance = +3 HP). Check feats.py for `stackable` or `multiple_times_allowed` flag.

### Implementation

In `builder.py`, after feats are assigned to the entity, count Toughness instances:
```python
# Toughness: +3 HP per instance (can take multiple times)
toughness_count = entity.get(EF.FEATS, []).count("toughness")
if toughness_count > 0:
    bonus_hp = toughness_count * 3
    entity[EF.HP_MAX] = entity.get(EF.HP_MAX, 0) + bonus_hp
    entity[EF.HP] = entity.get(EF.HP, 0) + bonus_hp
```

Also apply in `level_up()` if Toughness is granted as a new feat at that level — the same +3 HP should be added at level-up time, not recalculated from scratch.

### Gate Tests (TG-001 – TG-008)
```python
# TG-001: Build entity with Toughness → HP_MAX = base + 3
# TG-002: Build entity without Toughness → HP_MAX unchanged
# TG-003: Two instances of Toughness → HP_MAX = base + 6
# TG-004: Toughness at level-up (new feat granted) → HP_MAX incremented at level-up
# TG-005: Non-fighter/non-human (no bonus feat slot) with Toughness → still applies
# TG-006: Toughness HP bonus applies to EF.HP as well as EF.HP_MAX (starts with full HP)
# TG-007: Toughness does not affect NONLETHAL_DAMAGE threshold calculation
# TG-008: Regression — chargen entities without Toughness unaffected
```

### Session Close Conditions
- [ ] `git add aidm/chargen/builder.py tests/test_engine_toughness_gate.py`
- [ ] `git commit`
- [ ] TG-001–TG-008: 8/8 PASS; zero regressions

---

## File Ownership

| WO | Files touched |
|---|---|
| WO1 | maneuver_resolver.py, aoo.py |
| WO2 | attack_resolver.py, play_loop.py |
| WO3 | attack_resolver.py |
| WO4 | builder.py |

**WO2 and WO3 both touch attack_resolver.py.** Commit WO2 first, then WO3 builds on it.

**Recommended commit order:** WO1 → WO2 → WO3 → WO4.

---

## Regression Protocol

WO-specific gates first:
```bash
pytest tests/test_engine_improved_overrun_gate.py -v
pytest tests/test_engine_combat_expertise_gate.py -v
pytest tests/test_engine_blind_fight_gate.py -v
pytest tests/test_engine_toughness_gate.py -v
```

Full suite after all committed:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. Record in debrief and stop. Do not loop.

---

## Debrief Requirements

Three-pass format for all 4 WOs.
- WO1 Pass 3: cite Batch L AoO-suppression pattern (file + line) used as reference; document defender-avoid path location
- WO2 Pass 3: document state of untracked test file on boot (SAI or not); note Fight Defensively pattern reference
- WO3 Pass 3: file FINDING-ENGINE-BLIND-FIGHT-INVIS-001 (LOW) for invisible attacker path not scoped; document miss-chance resolution site
- WO4 Pass 3: document whether `level_up()` needed updating as well as `builder.py`; note stackable flag status in feats.py

Post-debrief: ask builder "Anything else you noticed outside the debrief?" File loose threads before closing.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`
Missing debrief or missing Pass 3 → REJECT.

---

## Session Close Conditions

- [ ] All 4 WOs committed with gate run before each
- [ ] IO: 8/8, CE: 8/8, BF: 8/8, TG: 8/8
- [ ] Zero regressions
- [ ] Chisel kernel updated

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel per ops contract.*
