# ENGINE DISPATCH — BATCH S
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Lifecycle:** DISPATCH-READY
**To:** Chisel (lead builder)
**Batch:** S — 4 WOs, 32 gate tests
**Prerequisite:** NONE — third parallel track

**Parallel track:** Batch S locks only `builder.py` and `save_resolver.py`. No overlap with Batch P (`attack_resolver.py` / `maneuver_resolver.py` / `play_loop.py`) or Batch R (`spell_resolver.py` / `aoo.py` / `full_attack_resolver.py`). Can run immediately alongside both.

**File pre-check:** `builder.py` and `save_resolver.py` are both clean (not in the dirty working tree from the Batch P baseline). Confirm with `git status` on boot.

**Batch R coupling note:** Batch R WO1 (IE) confirmed SAI — no `builder.py` touch. Batch S can start immediately without waiting for any Batch R WO to settle.

---

## Boot Sequence

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm dirty-tree baseline committed (`git status` clean tracked files)
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md`
4. Run `python scripts/verify_session_start.py`
5. Orphan check: any WO IN EXECUTION with no debrief? Flag before proceeding.
6. Record pre-existing failure count: `pytest --tb=no -q`

---

## Intelligence Update

**File conflicts — none with Batch P or R:**

| WO | File(s) | Batch P conflict? | Batch R conflict? |
|---|---|---|---|
| WO1 (BDR) | `builder.py` | None | None |
| WO2 (RSV) | `builder.py`, `save_resolver.py` | None | None |
| WO3 (ETN) | `builder.py` | None | None |
| WO4 (MUP) | `builder.py` | None | None |

**All 4 WOs touch `builder.py`.** Commit WO1 before WO2, WO2 before WO3, WO3 before WO4.

**Recommended commit order:** WO1 → WO2 → WO3 → WO4.

**DR system pattern:** `EF.DR_VALUE` (int) and `EF.DR_TYPE` (str, e.g. `"—"`) are set on the entity. `damage_reduction.py` reads these via `get_applicable_dr()`. Confirmed wired (ENGINE-DR 10/10). WO1 only sets these fields at chargen — zero changes to `damage_reduction.py` or `attack_resolver.py` needed.

**Stackable feat pattern (Extra Turning):** Use `entity.get(EF.FEATS, []).count("extra_turning")` — same as Toughness (Batch O TG debrief, commit 99d79af). NOT `"extra_turning" in feats`.

**Racial save bonus pattern:** Save bonus at chargen sets an EF field (e.g. `EF.RACIAL_SAVE_BONUS_ALL`, `EF.RACIAL_SAVE_BONUS_VS_POISON`, etc.). `save_resolver.py` reads and adds to the computed bonus. On boot: search for existing racial save bonus handling in save_resolver.py to confirm field names or establish new ones.

**EF.CLASS_LEVELS pattern:** `entity.get(EF.CLASS_LEVELS, {}).get("barbarian", 0)` — confirmed.

**V11 SAI risk (WO2 + WO4):** V11 (racial traits 18/18) wired "mechanical trait EF fields for all 7 PHB races." Unknown whether saving throw bonuses and monk unarmed dice were included. SAI check on boot for BOTH WOs — search builder.py for the specific EF fields before writing production code.

---

## WO 1 — WO-ENGINE-BARBARIAN-DR-001

**Scope:** `aidm/core/builder.py`
**Gate file:** `tests/test_engine_barbarian_dr_gate.py`
**Gate label:** ENGINE-BARBARIAN-DR
**Gate count:** 8 tests (BDR-001 – BDR-008)
**Kernel touch:** NONE
**Source:** PHB p.26

### Gap Verification

Coverage map: MISSING. PHB p.26: Barbarian gains Damage Reduction starting at level 7. DR scales as follows:

| Level | DR |
|---|---|
| 7–9 | 1/— |
| 10–12 | 2/— |
| 13–15 | 3/— |
| 16–18 | 4/— |
| 19–20 | 5/— |

DR/— means no bypass material — all physical damage reduced. DR system (ENGINE-DR 10/10) is already wired and reads `EF.DR_VALUE` / `EF.DR_TYPE`. This WO only sets those fields at chargen.

**Assumptions to Validate on boot:**
- SAI check: search `builder.py` for `"barbarian"` near DR-related fields. If already wired, document as SAI and run gate tests only.
- Confirm `EF.DR_VALUE` (int) and `EF.DR_TYPE` (str) are the correct field names (from ENGINE-DR 10/10 implementation).
- Confirm `EF.DR_TYPE = "—"` (em dash, not hyphen-minus) if that is the convention, or whatever string `damage_reduction.py` uses for the "no bypass" type.
- Multiclass check: a fighter 6 / barbarian 7 multiclass should still grant DR 1/—. `EF.CLASS_LEVELS.get("barbarian", 0)` is the correct lookup.

### Implementation

In `builder.py`, after barbarian class features are applied:

```python
# Barbarian DR (PHB p.26): DR/— at level 7, scales by 1 every 3 levels
_barb_level = entity.get(EF.CLASS_LEVELS, {}).get("barbarian", 0)
_dr_table = [(19, 5), (16, 4), (13, 3), (10, 2), (7, 1)]
for _threshold, _value in _dr_table:
    if _barb_level >= _threshold:
        entity[EF.DR_VALUE] = _value
        entity[EF.DR_TYPE] = "—"
        break
```

Do not overwrite DR if a higher DR value is already set from another source (e.g., magic items or creature type). Guard: `if _value > entity.get(EF.DR_VALUE, 0):`.

### Gate Tests (BDR-001 – BDR-008)

```python
# BDR-001: Barbarian level 7 → EF.DR_VALUE=1, EF.DR_TYPE="—"
# BDR-002: Barbarian level 10 → DR_VALUE=2
# BDR-003: Barbarian level 13 → DR_VALUE=3
# BDR-004: Barbarian level 16 → DR_VALUE=4
# BDR-005: Barbarian level 19 → DR_VALUE=5
# BDR-006: Barbarian level 6 (below threshold) → EF.DR_VALUE not set (or 0)
# BDR-007: Non-barbarian class, same level → no barbarian DR set
# BDR-008: Barbarian DR readable by damage_reduction.py — DR system reduces damage correctly (integration smoke test)
```

### Session Close Conditions
- [ ] `git add aidm/core/builder.py tests/test_engine_barbarian_dr_gate.py`
- [ ] `git commit`
- [ ] BDR-001–BDR-008: 8/8 PASS; zero regressions

---

## WO 2 — WO-ENGINE-RACIAL-SAVES-001

**Scope:** `aidm/core/builder.py`, `aidm/core/save_resolver.py`
**Gate file:** `tests/test_engine_racial_saves_gate.py`
**Gate label:** ENGINE-RACIAL-SAVES
**Gate count:** 8 tests (RSV-001 – RSV-008)
**Kernel touch:** NONE
**Source:** PHB Table 2-1 (p.12–20)

**Commit WO1 first** — both WO1 and WO2 touch `builder.py`.

### Gap Verification

PHB racial saving throw bonuses:
- **Halfling:** +1 bonus on all saving throws
- **Dwarf:** +2 bonus on saving throws vs. poison; +2 bonus on saving throws vs. spells and spell-like abilities
- **Gnome:** +2 bonus on saving throws vs. illusions

**Assumptions to Validate on boot:**
- V11 SAI check: search `builder.py` for halfling/dwarf/gnome save bonus logic. If wired, document as SAI — confirm all three races covered, run gate tests.
- On boot, search `save_resolver.py` for existing racial save bonus read. If present, confirm the EF field name and use it. If absent, establish new EF constants:
  - `EF.RACIAL_SAVE_BONUS_ALL` — int, added to Fort + Ref + Will (halfling)
  - `EF.RACIAL_SAVE_BONUS_VS_POISON` — int (dwarf)
  - `EF.RACIAL_SAVE_BONUS_VS_SPELL` — int (dwarf, applies to spells and SLAs)
  - `EF.RACIAL_SAVE_BONUS_VS_ILLUSION` — int (gnome, applies when save is vs. illusion school)
- Gnome illusion save: requires the save event to carry spell school. Confirm whether this is available. If school not present in save context, defer gnome WO4 check and file a FINDING.

### Implementation

In `builder.py`, in the racial feature application block:

```python
if race == "halfling":
    entity[EF.RACIAL_SAVE_BONUS_ALL] = 1

if race == "dwarf":
    entity[EF.RACIAL_SAVE_BONUS_VS_POISON] = 2
    entity[EF.RACIAL_SAVE_BONUS_VS_SPELL] = 2

if race == "gnome":
    entity[EF.RACIAL_SAVE_BONUS_VS_ILLUSION] = 2
```

In `save_resolver.py`, in the save bonus computation:

```python
# Racial save bonuses
save_bonus += entity.get(EF.RACIAL_SAVE_BONUS_ALL, 0)
if save_type == "fort":
    save_bonus += entity.get(EF.RACIAL_SAVE_BONUS_VS_POISON, 0) if is_vs_poison else 0
if is_vs_spell or is_vs_sla:
    save_bonus += entity.get(EF.RACIAL_SAVE_BONUS_VS_SPELL, 0)
if is_vs_illusion:
    save_bonus += entity.get(EF.RACIAL_SAVE_BONUS_VS_ILLUSION, 0)
```

### Gate Tests (RSV-001 – RSV-008)

```python
# RSV-001: Halfling → +1 Fort save
# RSV-002: Halfling → +1 Ref save (same field covers all three)
# RSV-003: Halfling → +1 Will save
# RSV-004: Dwarf → +2 Fort vs poison (context: is_vs_poison=True)
# RSV-005: Dwarf → +2 save vs spell (context: is_vs_spell=True)
# RSV-006: Gnome → +2 Will vs illusion spell (if school context available; else BLOCKED — note in debrief)
# RSV-007: Human → no racial save bonus (regression guard)
# RSV-008: Halfling racial +1 stacks with Great Fortitude feat +2 → total +3 Fort (different bonus types)
```

### Session Close Conditions
- [ ] `git add aidm/core/builder.py aidm/core/save_resolver.py tests/test_engine_racial_saves_gate.py`
- [ ] `git commit`
- [ ] RSV-001–RSV-008: 8/8 PASS; zero regressions

---

## WO 3 — WO-ENGINE-EXTRA-TURNING-001

**Scope:** `aidm/core/builder.py`
**Gate file:** `tests/test_engine_extra_turning_gate.py`
**Gate label:** ENGINE-EXTRA-TURNING
**Gate count:** 8 tests (ETN-001 – ETN-008)
**Kernel touch:** NONE
**Source:** PHB p.94

**Commit WO2 first** — both WO2 and WO3 touch `builder.py`.

### Gap Verification

Coverage map: MISSING. PHB p.94: Extra Turning — "You can turn or rebuke creatures more often than normal. You gain four extra turning attempts per day." Stackable: each instance of the feat adds 4 uses. Prerequisite: ability to turn or rebuke undead.

ENGINE-TURN-UNDEAD (10/10 ACCEPTED) wired `EF.TURN_UNDEAD_USES` / `EF.TURN_UNDEAD_USES_MAX`. Extra Turning increments `EF.TURN_UNDEAD_USES_MAX` at chargen. Uses the stackable feat pattern confirmed by Toughness (Batch O, commit 99d79af): `feats.count("extra_turning")`.

**Assumptions to Validate on boot:**
- SAI check: search `builder.py` for `extra_turning`. If wired, document as SAI.
- Confirm `EF.TURN_UNDEAD_USES_MAX` is the correct field name from ENGINE-TURN-UNDEAD.
- Confirm `rest_resolver.py` restores `EF.TURN_UNDEAD_USES_REMAINING` from `EF.TURN_UNDEAD_USES_MAX` on full rest (ETN-005 tests this path).

### Implementation

In `builder.py`, after base turning uses are set:

```python
# Extra Turning feat: +4 uses per instance (stackable)
_extra_turning_count = entity.get(EF.FEATS, []).count("extra_turning")
if _extra_turning_count > 0:
    entity[EF.TURN_UNDEAD_USES_MAX] = (
        entity.get(EF.TURN_UNDEAD_USES_MAX, 0) + 4 * _extra_turning_count
    )
    entity[EF.TURN_UNDEAD_USES_REMAINING] = entity[EF.TURN_UNDEAD_USES_MAX]
```

### Gate Tests (ETN-001 – ETN-008)

```python
# ETN-001: Cleric with one Extra Turning → TURN_UNDEAD_USES_MAX = base + 4
# ETN-002: Cleric with two Extra Turning feats → base + 8 (stackable, count() verified)
# ETN-003: Cleric with three Extra Turning feats → base + 12
# ETN-004: Cleric without Extra Turning → TURN_UNDEAD_USES_MAX = base (unaffected)
# ETN-005: Full rest with Extra Turning → USES_REMAINING restored to new max (base + 4)
# ETN-006: Paladin with Extra Turning → turning uses also increment (paladin uses turning via cleric÷2 path)
# ETN-007: Extra Turning + higher-level cleric → extra uses stack on top of level-based base correctly
# ETN-008: Toughness stackable pattern regression — Toughness HP bonus unaffected by Extra Turning commit
```

### Session Close Conditions
- [ ] `git add aidm/core/builder.py tests/test_engine_extra_turning_gate.py`
- [ ] `git commit`
- [ ] ETN-001–ETN-008: 8/8 PASS; zero regressions

---

## WO 4 — WO-ENGINE-MONK-UNARMED-PROGRESSION-001

**Scope:** `aidm/core/builder.py`
**Gate file:** `tests/test_engine_monk_unarmed_progression_gate.py`
**Gate label:** ENGINE-MONK-UNARMED-PROGRESSION
**Gate count:** 8 tests (MUP-001 – MUP-008)
**Kernel touch:** NONE
**Source:** PHB p.41 (Table 3-10)

**Commit WO3 first** — both WO3 and WO4 touch `builder.py`.

### Gap Verification

Coverage map: MISSING (or PARTIAL — confirm on boot). PHB Table 3-10: Monk unarmed damage scales with level:

| Level | Damage (Medium) |
|---|---|
| 1–3 | 1d6 |
| 4–7 | 1d8 |
| 8–11 | 1d10 |
| 12–15 | 2d6 |
| 16–19 | 2d8 |
| 20 | 2d10 |

(Small monk: one size category smaller throughout)

**Assumptions to Validate on boot:**
- V11 SAI check: search `builder.py` for `monk` near `unarmed` or `damage_dice`. If table-driven progression is already wired, document as SAI — verify table values are correct.
- Confirm how monk unarmed strikes are stored in the entity. Likely as `EF.WEAPON` dict (same as other weapons), or as a `natural_attacks` list. Confirm the field and key name where `damage_dice` is stored.
- Confirm `Weapon.damage_dice` is the string format used (e.g., `"1d6"`, `"2d8"`).
- Unarmed strike `weapon_type`: likely `"natural"` or possibly a new `"unarmed"` category. Do NOT introduce a new weapon_type string — use the existing `"natural"` category if that's what the engine uses. Document in debrief.

### Implementation

In `builder.py`, in monk class feature application:

```python
# Monk unarmed strike damage progression (PHB Table 3-10)
_monk_level = entity.get(EF.CLASS_LEVELS, {}).get("monk", 0)
_unarmed_table = [
    (20, "2d10"), (16, "2d8"), (12, "2d6"),
    (8, "1d10"), (4, "1d8"), (1, "1d6"),
]
for _threshold, _dice in _unarmed_table:
    if _monk_level >= _threshold:
        # Set unarmed strike damage dice in entity weapon config
        entity[EF.MONK_UNARMED_DICE] = _dice  # or wherever unarmed damage_dice is stored
        break
```

Use the confirmed field name from boot. If `EF.MONK_UNARMED_DICE` does not exist, establish it as a new EF constant and document in debrief.

### Gate Tests (MUP-001 – MUP-008)

```python
# MUP-001: Monk level 1 → unarmed damage_dice = "1d6"
# MUP-002: Monk level 4 → "1d8"
# MUP-003: Monk level 8 → "1d10"
# MUP-004: Monk level 12 → "2d6"
# MUP-005: Monk level 16 → "2d8"
# MUP-006: Monk level 20 → "2d10"
# MUP-007: Non-monk class at level 12 → no monk unarmed progression applied
# MUP-008: Monk level 3 → still "1d6" (boundary: level 4 triggers upgrade, not level 3)
```

### Session Close Conditions
- [ ] `git add aidm/core/builder.py tests/test_engine_monk_unarmed_progression_gate.py`
- [ ] `git commit`
- [ ] MUP-001–MUP-008: 8/8 PASS; zero regressions

---

## File Ownership

| WO | Files touched |
|---|---|
| WO1 | `builder.py` |
| WO2 | `builder.py`, `save_resolver.py` |
| WO3 | `builder.py` |
| WO4 | `builder.py` |

**All 4 WOs touch `builder.py`.** Commit each before starting the next.

**No overlap with Batch P or Batch R.**

---

## Regression Protocol

WO-specific gates first:
```bash
pytest tests/test_engine_barbarian_dr_gate.py -v
pytest tests/test_engine_racial_saves_gate.py -v
pytest tests/test_engine_extra_turning_gate.py -v
pytest tests/test_engine_monk_unarmed_progression_gate.py -v
```

Full suite after all committed:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. Record in debrief and stop. Do not loop.

---

## Debrief Requirements

Three-pass format for all 4 WOs.
- WO1 Pass 3: confirm DR_VALUE / DR_TYPE field names used; document the guard against overwriting a higher existing DR value; confirm DR system reads the new values correctly (BDR-008)
- WO2 Pass 3: document which EF fields were established or confirmed; note whether gnome illusion save (RSV-006) was achievable or BLOCKED (spell school context availability); confirm halfling bonus is "all saves" not just Fort
- WO3 Pass 3: confirm TURN_UNDEAD_USES_MAX field name; document how base uses (level-based) are set and where Extra Turning appends; confirm rest_resolver.py restores from new max (ETN-005)
- WO4 Pass 3: document where unarmed damage_dice is stored in entity (EF.MONK_UNARMED_DICE or weapon dict key); confirm weapon_type used for unarmed strikes; note Small monk table if tested

Post-debrief: ask builder "Anything else you noticed outside the debrief?" File loose threads before closing.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`
Missing debrief or missing Pass 3 → REJECT.

---

## Session Close Conditions

- [ ] All 4 WOs committed with gate run before each
- [ ] BDR: 8/8, RSV: 8/8, ETN: 8/8, MUP: 8/8
- [ ] Zero regressions
- [ ] Chisel kernel updated

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel per ops contract.*
