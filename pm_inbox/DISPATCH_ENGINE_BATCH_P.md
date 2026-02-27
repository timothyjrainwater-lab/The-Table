# ENGINE DISPATCH — BATCH P
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**To:** Chisel (lead builder)
**Batch:** P — 4 WOs, 32 gate tests
**Prerequisite:** ENGINE BATCH O ACCEPTED

**Note:** WO detail is inline in this file. Combined format (inbox at cap).

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

**Four untracked test files + one untracked resolver — read all on boot:**
- `tests/test_engine_divine_grace_gate.py` — untracked. WO1 may be SAI.
- `tests/test_engine_lay_on_hands_gate.py` — untracked. WO2 may be SAI.
- `aidm/core/lay_on_hands_resolver.py` — untracked. WO2 resolver may be SAI.
- `tests/test_engine_evasion_gate.py` — untracked. WO3 may be SAI.
- `tests/test_engine_uncanny_dodge_gate.py` — untracked. WO4 may be SAI.

If any is SAI: run gate, verify 8/8 PASS, commit existing file(s), finding CLOSED. Zero production changes (ML-003).

**Batch N note:** SF-007 (Save Feats) tests Divine Grace + Great Fortitude stacking. If SF-007 failed in Batch N, that informs WO1 scope here — read the Batch N debrief before writing.

**EF.CLASS_LEVELS pattern:** `entity.get(EF.CLASS_LEVELS, {}).get("class_name", 0)` — EF.CLASS_FEATURES does not exist.

**Event constructor:** `Event(event_id=..., event_type=..., payload=...)` — not `id=`, `type=`, `data=`.

---

## WO 1 — WO-ENGINE-DIVINE-GRACE-001

**Scope:** `aidm/core/save_resolver.py`
**Gate file:** `tests/test_engine_divine_grace_gate.py`
**Gate label:** ENGINE-DIVINE-GRACE
**Gate count:** 8 tests (DG-001 – DG-008)
**Kernel touch:** NONE
**Source:** PHB p.44

### Gap Verification
Coverage map: NOT STARTED — "CHA mod not added to saves." Paladin class feature: CHA modifier applies to all three saving throws (Fort, Ref, Will). Not capped at zero; negative CHA modifier penalizes saves.

**Assumptions to Validate on boot:**
- Read `test_engine_divine_grace_gate.py` — if it exists and passes 8/8, SAI.
- Read `save_resolver.py` — search "divine_grace" and "paladin" to confirm not already wired.
- Confirm how paladin class is detected: `entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0) > 0`.

### Implementation

In `save_resolver.py`, in the save accumulation path (shared helper or per-save function), after base save computed:

```python
# Divine Grace: paladin adds CHA modifier to all saves
paladin_levels = entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
if paladin_levels > 0:
    cha_mod = (entity.get(EF.CHA, 10) - 10) // 2
    fort_bonus += cha_mod
    ref_bonus += cha_mod
    will_bonus += cha_mod
```

Apply before the save roll. Negative CHA mod IS subtracted (no floor). Include `divine_grace_bonus` key in save event breakdown payload.

### Gate Tests (DG-001 – DG-008)
```python
# DG-001: Paladin CHA 16 (+3 mod) → Fort save = base + 3
# DG-002: Paladin CHA 16 → Ref save = base + 3
# DG-003: Paladin CHA 16 → Will save = base + 3
# DG-004: Non-paladin entity → no Divine Grace bonus on any save
# DG-005: Paladin CHA 8 (-1 mod) → Fort save = base - 1 (no floor at 0)
# DG-006: Paladin CHA 10 (+0 mod) → saves unchanged (regression)
# DG-007: Paladin with Great Fortitude → Fort = base + CHA_mod + 2 (feat stacks)
# DG-008: Save event breakdown contains divine_grace_bonus field when paladin
```

### Session Close Conditions
- [ ] `git add aidm/core/save_resolver.py tests/test_engine_divine_grace_gate.py`
- [ ] `git commit`
- [ ] DG-001–DG-008: 8/8 PASS; zero regressions

---

## WO 2 — WO-ENGINE-LAY-ON-HANDS-001

**Scope:** `aidm/core/lay_on_hands_resolver.py`, `aidm/schemas/intents.py`, `aidm/core/play_loop.py`
**Gate file:** `tests/test_engine_lay_on_hands_gate.py`
**Gate label:** ENGINE-LAY-ON-HANDS
**Gate count:** 8 tests (LH-001 – LH-008)
**Kernel touch:** KERNEL-01 (Entity Lifecycle — lay_on_hands_pool field on entity)
**Source:** PHB p.44

### Gap Verification
Coverage map: NOT STARTED — "No healing ability." Paladin uses Lay on Hands (standard action) to heal any creature by touch. Pool = CHA modifier × paladin level HP/day. Pool tracked as `EF.LAY_ON_HANDS_POOL` on entity; set at chargen in `builder.py`.

**⚠ TWO UNTRACKED FILES — read on boot:**
- `aidm/core/lay_on_hands_resolver.py` — already untracked. Read immediately. If fully implemented: SAI.
- `tests/test_engine_lay_on_hands_gate.py` — already untracked. Read immediately. If 8/8 pass: commit, SAI.

**Assumptions to Validate on boot:**
- Confirm `EF.LAY_ON_HANDS_POOL` exists in `entity_fields.py`. If not, add it.
- Confirm `builder.py` sets `EF.LAY_ON_HANDS_POOL` at chargen for paladins.
- Confirm `LayOnHandsIntent` does not already exist in `intents.py`.

### Intent Schema

```python
@dataclass
class LayOnHandsIntent:
    actor_id: str       # paladin doing the healing
    target_id: str      # recipient (may be self)
    amount: int         # HP to spend from pool (must be ≤ remaining pool)
```

### Implementation

In `lay_on_hands_resolver.py`:
- Guard 1: actor must be paladin (`EF.CLASS_LEVELS.paladin > 0`)
- Guard 2: `EF.LAY_ON_HANDS_POOL > 0` (pool not exhausted)
- Guard 3: `amount ≤ remaining pool`
- On success: add `amount` HP to target (capped at HP_MAX), decrement pool by `amount`
- On target that is undead: Lay on Hands deals damage instead of healing (PHB p.44). Emit `lay_on_hands_damage` event.

Wire `LayOnHandsIntent` in `play_loop.py` → `resolve_lay_on_hands()`. Standard action slot.

### Gate Tests (LH-001 – LH-008)
```python
# LH-001: Paladin CHA 16 level 5 → pool=15; heal 5 HP → target HP+5, pool=10
# LH-002: Pool exhausted (pool=0) → intent_validation_failed reason="pool_empty"
# LH-003: Non-paladin actor → intent_validation_failed reason="class_requirement_not_met"
# LH-004: Self-target heal → paladin's own HP increases
# LH-005: Heal capped at HP_MAX (cannot exceed max HP)
# LH-006: Pool decrements correctly (pool before - amount = pool after)
# LH-007: Undead target → lay_on_hands_damage event instead of heal
# LH-008: Standard action consumed (second standard action in same turn denied)
```

### Session Close Conditions
- [ ] `git add aidm/core/lay_on_hands_resolver.py aidm/schemas/intents.py aidm/core/play_loop.py tests/test_engine_lay_on_hands_gate.py`
- [ ] `git commit`
- [ ] LH-001–LH-008: 8/8 PASS; zero regressions

---

## WO 3 — WO-ENGINE-EVASION-001

**Scope:** `aidm/core/save_resolver.py`
**Gate file:** `tests/test_engine_evasion_gate.py`
**Gate label:** ENGINE-EVASION
**Gate count:** 8 tests (EV-001 – EV-008)
**Kernel touch:** NONE
**Source:** PHB p.48 (Ranger), p.50 (Rogue)

### Gap Verification
Coverage map: NOT STARTED. On a successful Reflex save vs a half-damage effect, the entity takes **0 damage** instead of half. Rogue (level 2+) and Ranger (level 9+). Improved Evasion (rogue level 10+, monk level 9+): successful Ref → 0 damage; **failed** Ref → half damage (not full). Wire both in this WO.

**Commit WO1 first** — both WO1 and WO3 touch `save_resolver.py`.

**Assumptions to Validate on boot:**
- Read `test_engine_evasion_gate.py` — if it exists and passes 8/8, SAI.
- Confirm evasion flag: entity field `EF.EVASION` (bool) or feature in `EF.CLASS_FEATURES`. Search `entity_fields.py`.
- Confirm Evasion is suppressed in medium/heavy armor (PHB p.50) — check if armor weight tracked on entity.

### Implementation

In `save_resolver.py`, in the half-damage Reflex save path:

```python
# After determining save success/fail for half-damage effect:
if save_succeeded:
    if entity.get(EF.EVASION, False):
        damage = 0  # Evasion: 0 damage on successful Ref save
        events.append(Event(..., event_type="evasion_triggered",
                            payload={"entity_id": entity_id}))
    else:
        damage = full_damage // 2  # Normal half
elif not save_succeeded:
    if entity.get(EF.IMPROVED_EVASION, False):
        damage = full_damage // 2  # Improved Evasion: half even on fail
    else:
        damage = full_damage  # Normal full
```

Evasion suppressed if wearing medium or heavy armor: check `entity.get(EF.ARMOR_WEIGHT, "none")` in `["medium", "heavy"]`.

### Gate Tests (EV-001 – EV-008)
```python
# EV-001: Entity with evasion, Ref save succeeds → 0 damage, evasion_triggered event
# EV-002: Entity with evasion, Ref save fails → full damage (no evasion on fail)
# EV-003: Entity without evasion, Ref save succeeds → half damage (existing behavior)
# EV-004: Entity with improved_evasion, Ref save fails → half damage (not full)
# EV-005: Entity with improved_evasion, Ref save succeeds → 0 damage
# EV-006: Evasion entity in medium/heavy armor → evasion suppressed; half damage on success
# EV-007: Rogue at level 2+ → evasion feature active; level 1 rogue → no evasion
# EV-008: Event sequence: evasion_triggered appears before damage resolution event
```

### Session Close Conditions
- [ ] `git add aidm/core/save_resolver.py tests/test_engine_evasion_gate.py`
- [ ] `git commit`
- [ ] EV-001–EV-008: 8/8 PASS; zero regressions

---

## WO 4 — WO-ENGINE-UNCANNY-DODGE-001

**Scope:** `aidm/core/attack_resolver.py`
**Gate file:** `tests/test_engine_uncanny_dodge_gate.py`
**Gate label:** ENGINE-UNCANNY-DODGE
**Gate count:** 8 tests (UD-001 – UD-008)
**Kernel touch:** NONE
**Source:** PHB p.51 (Rogue), p.26 (Barbarian)

### Gap Verification
Coverage map: NOT STARTED. Uncanny Dodge: entity retains DEX bonus to AC when flat-footed. Rogue (level 4+), Barbarian (level 2+). Improved Uncanny Dodge (cannot be flanked for sneak attack purposes) is deferred — file FINDING-ENGINE-IMPROVED-UNCANNY-DODGE-001 (LOW) in debrief.

**Assumptions to Validate on boot:**
- Read `test_engine_uncanny_dodge_gate.py` — if it exists and passes 8/8, SAI.
- Find the exact location in `attack_resolver.py` where flat-footed AC is computed (where DEX is zeroed out). Reference the FLAT_FOOTED condition check.
- Confirm entity field for uncanny dodge: `EF.UNCANNY_DODGE` (bool) or derived from class levels.

### Implementation

In `attack_resolver.py`, at the flat-footed AC calculation site:

```python
# Before applying flat-footed DEX strip:
is_flat_footed = EF.FLAT_FOOTED in entity.get(EF.CONDITIONS, {})
if is_flat_footed and not entity.get(EF.UNCANNY_DODGE, False):
    dex_mod = 0  # Flat-footed: lose DEX
elif is_flat_footed and entity.get(EF.UNCANNY_DODGE, False):
    pass  # Uncanny Dodge: keep DEX even when flat-footed
```

Also wire in chargen/level-up: set `EF.UNCANNY_DODGE = True` when rogue reaches level 4 or barbarian reaches level 2. If this is already handled via class feature grants in `builder.py`, verify and use existing field.

### Gate Tests (UD-001 – UD-008)
```python
# UD-001: Flat-footed entity WITH uncanny_dodge=True → retains DEX to AC
# UD-002: Flat-footed entity WITHOUT uncanny_dodge → loses DEX (existing behavior preserved)
# UD-003: Barbarian level 2+ → uncanny_dodge active; level 1 barbarian → not active
# UD-004: Rogue level 4+ → uncanny_dodge active; level 3 rogue → not active
# UD-005: Non-flat-footed entity with uncanny_dodge → normal DEX applies (no effect either way)
# UD-006: Uncanny dodge does NOT prevent sneak attack from flanking
# UD-007: uncanny_dodge_retained event emitted when DEX kept due to Uncanny Dodge
# UD-008: Regression — entity without uncanny_dodge still loses DEX when flat-footed
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_uncanny_dodge_gate.py`
- [ ] `git commit`
- [ ] UD-001–UD-008: 8/8 PASS; zero regressions
- [ ] File FINDING-ENGINE-IMPROVED-UNCANNY-DODGE-001 LOW in debrief

---

## File Ownership

| WO | Files touched |
|---|---|
| WO1 | save_resolver.py |
| WO2 | lay_on_hands_resolver.py, intents.py, play_loop.py |
| WO3 | save_resolver.py |
| WO4 | attack_resolver.py |

**WO1 and WO3 both touch save_resolver.py.** Commit WO1 first, then WO3 builds on it.

**Recommended commit order:** WO1 → WO2 → WO3 → WO4.

---

## Regression Protocol

WO-specific gates first:
```bash
pytest tests/test_engine_divine_grace_gate.py -v
pytest tests/test_engine_lay_on_hands_gate.py -v
pytest tests/test_engine_evasion_gate.py -v
pytest tests/test_engine_uncanny_dodge_gate.py -v
```

Full suite after all committed:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. Record in debrief and stop. Do not loop.

---

## Debrief Requirements

Three-pass format for all 4 WOs.
- WO1 Pass 3: document whether SF-007 (Batch N Save Feats) had already wired Divine Grace or if it was fresh work; note CHA modifier floor behavior
- WO2 Pass 3: document state of untracked `lay_on_hands_resolver.py` on boot (SAI or stub/partial); confirm pool formula (CHA_mod × level or CHA × level)
- WO3 Pass 3: document state of untracked `test_engine_evasion_gate.py`; confirm armor weight field name used for suppression; file FINDING on Improved Evasion if not scoped
- WO4 Pass 3: file FINDING-ENGINE-IMPROVED-UNCANNY-DODGE-001 LOW (cannot-be-flanked mechanic deferred); document uncanny_dodge field source (builder.py vs manual flag)

Post-debrief: ask builder "Anything else you noticed outside the debrief?" File loose threads before closing.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`
Missing debrief or missing Pass 3 → REJECT.

---

## Session Close Conditions

- [ ] All 4 WOs committed with gate run before each
- [ ] DG: 8/8, LH: 8/8, EV: 8/8, UD: 8/8
- [ ] Zero regressions
- [ ] Chisel kernel updated

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel per ops contract.*
