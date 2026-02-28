**Lifecycle:** ARCHIVE
**Commit:** ab44488

---

# DEBRIEF — Batch AE Engine (WO-AE-WO1 through WO-AE-WO4)
**32/32 gate tests pass. 4 WOs delivered.**

---

## Pass 1 — Context Dump

### WO-AE-WO1-A: play_loop._create_target_stats() save_descriptor fix

**File:** `aidm/core/play_loop.py:274`
**Before:** `_save_descriptor = "spell" if school else ""`
**After:** `_save_descriptor = "spell"  # WO-AE-WO1: always "spell"`
**Gap confirmed:** Zero-school spells (e.g. magic missile, touch attacks) got empty descriptor → dwarf +2 vs spells, halfling SAVE_BONUS_SPELLS never fired. Fix: unconditional assignment.
**Gate file:** `tests/test_engine_spell_resolver_save_bypass_gate.py` (SRSP-AE-001–004, 4 tests)

---

### WO-AE-WO1-B: poison_disease_resolver.py CON double-count

**File:** `aidm/core/poison_disease_resolver.py`
**4 call sites fixed** (EF.SAVE_FORT is Type 2 — already includes CON; resolver must not re-add):
- `apply_poison()` lines ~139-143: removed `con_mod = entity.get(EF.CON_MOD, 0)` and `+ con_mod`
- `process_poison_secondaries()` lines ~238-243: same
- `apply_disease_exposure()` lines ~363-366: same
- `process_disease_ticks()` lines ~457-461: same

**Before:** `total = roll + fort_base + con_mod + bonus`
**After:** `total = roll + fort_base + bonus`
**Gate file:** `tests/test_engine_poison_con_double_count_gate.py` (PCD-AE-001–004, 4 tests)

---

### WO-AE-WO2: EF.FATIGUED → -2 Ref penalty in save_resolver

**File:** `aidm/core/save_resolver.py`
**New block inserted** before `total_bonus` assembly:
```python
fatigue_ref_penalty = 0
if save_type == SaveType.REF and entity.get(EF.FATIGUED, False):
    fatigue_ref_penalty = -2
```
**total_bonus updated:** `+ fatigue_ref_penalty`
**Why:** EF.FATIGUED is a boolean field set by rage_resolver.py. The condition system reads ConditionInstance objects; the FATIGUED bool was invisible to get_condition_modifiers(). Direct boolean check resolves the KERNEL-02 dual-track issue.
**Gate file:** `tests/test_engine_rage_fatigue_save_gate.py` (RFS-AE-001–008, 8 tests)

---

### WO-AE-WO3-A: Aura of Courage level threshold L2→L3

**File:** `aidm/chargen/builder.py`
- Line 1066 (single-class): `if _paladin_level >= 2:` → `if _paladin_level >= 3:`
- Line 1339 (multiclass): same fix
- Line 217 save_resolver (ally check): `< 2` → `< 3`

**PHB p.49:** "Beginning at 3rd level, a paladin is immune to fear (magical or otherwise)."
Old code granted AoC at L2 (off by one). Existing test `test_scs_003` updated L2→L3 paladin; `test_ssu_006` renamed to `test_ssu_006_inspire_courage_not_in_spell`.
**Gate file:** `tests/test_engine_aoc_level_threshold_gate.py` (ALT-AE-001–004, 4 tests)

---

### WO-AE-WO3-B: Inspire Courage save scope → fear/charm only

**File:** `aidm/core/save_resolver.py`
**Before:**
```python
inspire_courage_bonus = entity.get(EF.INSPIRE_COURAGE_BONUS, 0) if _inspire_active else 0
```
**After:**
```python
_inspire_active = entity.get(EF.INSPIRE_COURAGE_ACTIVE, False)
inspire_courage_bonus = 0
if _inspire_active and save_descriptor in ("fear", "charm"):
    inspire_courage_bonus = entity.get(EF.INSPIRE_COURAGE_BONUS, 0)
```
**PHB p.29:** IC grants morale bonus vs charm and fear effects — not all saves. Old code applied the bonus to every save regardless of descriptor.
Existing tests `test_sf10` (save_feats), `test_ssu_006` (spell_save_unify) updated with correct behavior assertions.
**Gate file:** `tests/test_engine_bardic_save_scope_gate.py` (BSS-AE-001–004, 4 tests)

---

### WO-AE-WO4: Trap Sense — EF field + chargen write + resolver consume

**New EF field:** `entity_fields.py` line 321–327: `TRAP_SENSE_BONUS = "trap_sense_bonus"` (Type 3 Runtime-Only per field contract).

**Chargen write (single-class)** `builder.py` after `_barbarian_level` assignment (~line 998):
```python
_trap_sense_rogue_level = level if class_name == "rogue" else 0
entity[EF.TRAP_SENSE_BONUS] = (_barbarian_level // 3) + (_trap_sense_rogue_level // 3)
```

**Chargen write (multiclass)** `builder.py` after `_barbarian_level = class_mix.get("barbarian", 0)` (~line 1273):
```python
_trap_sense_rogue_level = class_mix.get("rogue", 0)
entity[EF.TRAP_SENSE_BONUS] = (_barbarian_level // 3) + (_trap_sense_rogue_level // 3)
```

**Resolver consume** `save_resolver.py` before total_bonus:
```python
trap_sense_bonus = 0
if save_type == SaveType.REF and save_descriptor == "trap":
    trap_sense_bonus = entity.get(EF.TRAP_SENSE_BONUS, 0)
```
**total_bonus updated:** `+ trap_sense_bonus`

**CONSUME_DEFERRED:** AC vs traps (no trap attack subsystem). Filed FINDING-ENGINE-TRAP-SENSE-AC-001 in BACKLOG_OPEN.
**Gate file:** `tests/test_engine_trap_sense_gate.py` (TSB-AE-001–008, 8 tests)

---

### Coverage Map Updates (5 rows)
- Line 149 (Fatigued): updated — -2 Ref now wired in save_resolver
- Line 534 (Barb Trap Sense): NOT STARTED → IMPLEMENTED
- Line 546 (Inspire Courage): updated — save scope fix noted
- Line 635 (Aura of Courage): updated — L2→L3 threshold noted
- Line 669 (Rogue Trap Sense): NOT STARTED → IMPLEMENTED

### Old Test Corrections (not regressions — wrong assertions corrected)
| Test | Old assertion | New assertion | Reason |
|------|--------------|---------------|--------|
| `test_ssu_006` | IC fires on spell Fort save → 7 | IC does NOT fire on spell Fort save → 6 | PHB p.29: IC is fear/charm only |
| `test_sf10` | IC fires on generic Fort (no descriptor) → 6 | IC fires on Fort with `save_descriptor="fear"` → 6 | PHB p.29 |
| `test_scs_003` | Paladin L2 ally gets AoC | Paladin L3 ally gets AoC | PHB p.49: AoC at L3 |

---

## Pass 2 — PM Summary (100 words)

Batch AE delivered 4 WOs targeting the save resolver subsystem. WO1 closed a dual-gap: the play_loop spell descriptor conditional (zero-school spells missing racial bonuses) and CON double-count in poison/disease saves (Type 2 field contract violation at 4 sites). WO2 wired EF.FATIGUED boolean directly to -2 Ref penalty, bypassing the KERNEL-02 ConditionInstance dual-track. WO3 corrected AoC level threshold (L2→L3 per PHB p.49) and scoped Inspire Courage to fear/charm saves only (PHB p.29). WO4 delivered Trap Sense end-to-end: new EF field, chargen write (barb//3 + rogue//3), resolver consume gated on REF+"trap". 32/32 gates pass; no new regressions.

---

## Pass 3 — Retrospective

**Out-of-scope findings discovered:**
- **FINDING-ENGINE-TRAP-SENSE-AC-001 (CONSUME_DEFERRED):** EF.TRAP_SENSE_BONUS is not consumed for AC vs traps (PHB p.26/p.51). No trap attack subsystem exists. Filed in BACKLOG_OPEN.

**Kernel touches:**
- This WO touches KERNEL-02 (EF field contract / dual-track) — the FATIGUED fix demonstrates the exact class of write-only field failure the kernel documents. The direct boolean check pattern is now confirmed as the correct solution for boolean ability fields that bypass the ConditionInstance path.

**Dispatch parity check (CLAUDE.md requirement):**
- save_resolver.get_save_bonus() is the canonical save path. No parallel implementation of save math was found outside of old poison_disease_resolver sites (which were fixed).

---

## Radar

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-ENGINE-TRAP-SENSE-AC-001 | LOW | CONSUME_DEFERRED | AC vs traps not wired (no trap attack subsystem) |
| FINDING-ENGINE-INSPIRE-COURAGE-SCOPE-001 | CLOSED | FIXED | IC was firing on all saves; now fear/charm only |
| FINDING-ENGINE-AOC-THRESHOLD-001 | CLOSED | FIXED | AoC was granted at L2; fixed to L3 |
| FINDING-ENGINE-POISON-CON-DOUBLE-001 | CLOSED | FIXED | CON double-counted in 4 poison/disease save sites |
| FINDING-ENGINE-SPELL-DESCRIPTOR-ZERO-SCHOOL | CLOSED | FIXED | Zero-school spell saves got empty descriptor |

---

## Consume-Site Confirmation

| WO | Write site | Read site | Effect | Gate |
|----|-----------|-----------|--------|------|
| WO1-A | `play_loop._create_target_stats():274` | `save_resolver.get_save_bonus()` | Dwarf +2 vs spells fires for all spells | SRSP-AE-001 |
| WO1-B | (removed) `poison_disease_resolver.py` (4 sites) | n/a (field no longer double-used) | CON not added twice to poison/disease Fort saves | PCD-AE-001 |
| WO2 | `rage_resolver.py` (EF.FATIGUED=True on rage end) | `save_resolver.get_save_bonus():~259` | -2 Ref penalty when fatigued | RFS-AE-001 |
| WO3-A | `builder.py:1066,1339` (EF.FEAR_IMMUNE) | `save_resolver.get_save_bonus():~200` (AoC ally path) | AoC granted at L3 not L2 | ALT-AE-002 |
| WO3-B | `save_resolver.get_save_bonus():120-123` | same function | IC +morale only fires for fear/charm | BSS-AE-001,002 |
| WO4 | `builder.py:999,1274` (EF.TRAP_SENSE_BONUS) | `save_resolver.get_save_bonus():~259` | +N Ref vs traps from trap sense | TSB-AE-005,008 |
