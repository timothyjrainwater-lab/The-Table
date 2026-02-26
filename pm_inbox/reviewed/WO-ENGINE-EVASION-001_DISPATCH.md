# WO-ENGINE-EVASION-001 — Rogue / Monk Evasion: AoE Reflex Save Damage Negation

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** HIGH (FINDING-COVERAGE-MAP-001 — every rogue takes full AoE damage on successful Ref save instead of zero)
**WO type:** BUG (class ability present in chargen; enforcement absent in spell resolver)
**Gate:** ENGINE-EVASION (10 tests)

---

## 1. Target Lock

**What works:** Evasion is recognized as a class ability in `aidm/chargen/builder.py`:
- Rogue level 2: `"evasion"` (line ~1108)
- Monk level 2: `"evasion"` (line ~1157)
- Monk level 9: `"improved_evasion"` (line ~1167)

These strings are stored in the character's class ability list during chargen.

**What's missing:** `aidm/core/spell_resolver.py` — `_resolve_damage()` (lines ~828–887) — applies damage based on save result with only two paths: HALF (halve damage on save) or NEGATES (zero damage on save). No evasion check exists. A rogue who makes a Reflex save against a Fireball receives 50% of the damage. PHB p.56: with Evasion, a successful Reflex save against an area effect that normally deals half damage instead deals no damage.

**No entity field constant exists** for evasion — only a class ability string in chargen output. This WO adds a proper EF constant and wires it into damage resolution.

**PHB references:**
- Evasion (Rogue p.56, Monk p.41): successful Ref save against half-damage AoE → 0 damage
- Improved Evasion (Rogue p.57, Monk p.43): failed Ref save → half damage; success → 0 damage

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | New EF field or check class ability string? | New EF field: `EF.EVASION` (bool) and `EF.IMPROVED_EVASION` (bool). Set during chargen when class ability `"evasion"` / `"improved_evasion"` is granted. Reading a string out of a class ability list is fragile; a typed EF field is the correct pattern. |
| 2 | Does this WO wire chargen? | Yes — the chargen builder must set `EF.EVASION = True` at Rogue 2 / Monk 2 and `EF.IMPROVED_EVASION = True` at Rogue 10 / Monk 9. Without this, the resolver has nothing to check. This is a small addition to `builder.py`. |
| 3 | Where in spell_resolver is the check? | Inside `_resolve_damage()`, in the `if saved:` branch, after checking `spell.save_effect == SaveEffect.HALF`. If EVASION is present, override total to 0. For IMPROVED_EVASION, also check the `else` branch (failed save) and halve damage there. |
| 4 | Does evasion apply to all Ref saves or only AoE half-damage? | PHB is specific: evasion applies when a Reflex save "would allow you to take no damage or only half damage." Practically: `save_type == SaveType.REF` and `save_effect == SaveEffect.HALF`. If `save_effect == SaveEffect.NEGATES`, the target already takes 0 on success — evasion adds nothing. |
| 5 | Does evasion work in medium/heavy armor? | PHB p.56: "A rogue who wears medium or heavy armor loses this ability." This WO does NOT enforce the armor restriction — that requires the equip system. For now, check EF.EVASION only. The armor restriction is a follow-up WO. Document as known gap. |
| 6 | Improved Evasion — both branches? | Yes. On failed save: `total = total // 2`. On successful save: `total = 0`. |

---

## 3. Contract Spec

### New EF constants in `aidm/schemas/entity_fields.py`

```python
EVASION = "evasion"
# bool: True if entity has Evasion class ability (Rogue 2, Monk 2).
# On successful Reflex save vs half-damage area effect: take 0 damage instead of half.
# PHB Rogue p.56, Monk p.41. Armor restriction not enforced by this WO.

IMPROVED_EVASION = "improved_evasion"
# bool: True if entity has Improved Evasion (Rogue 10, Monk 9).
# On failed Reflex save vs half-damage area effect: take half damage instead of full.
# On successful save: take 0 damage (same as Evasion).
# PHB Rogue p.57, Monk p.43.
```

### Modification: `aidm/chargen/builder.py`

At the level-up block that grants `"evasion"` and `"improved_evasion"` class abilities, also set the EF field:

```python
# When granting "evasion":
entity[EF.EVASION] = True

# When granting "improved_evasion":
entity[EF.IMPROVED_EVASION] = True
```

### Modification: `_resolve_damage()` in `aidm/core/spell_resolver.py`

In the `if saved:` branch, after the existing save_effect logic:

```python
if saved:
    if spell.save_effect == SaveEffect.HALF:
        total = total // 2
        # WO-ENGINE-EVASION-001: Evasion / Improved Evasion
        if save_type == SaveType.REF:
            if target_entity.get(EF.EVASION, False) or target_entity.get(EF.IMPROVED_EVASION, False):
                total = 0
    elif spell.save_effect == SaveEffect.NEGATES:
        total = 0
else:
    # Failed save
    # WO-ENGINE-EVASION-001: Improved Evasion on failed save → half damage
    if save_type == SaveType.REF and spell.save_effect == SaveEffect.HALF:
        if target_entity.get(EF.IMPROVED_EVASION, False):
            total = total // 2
```

---

## 4. Implementation Plan

### Step 1 — `aidm/schemas/entity_fields.py`
Add `EVASION` and `IMPROVED_EVASION` constants.

### Step 2 — `aidm/chargen/builder.py`
At the blocks granting `"evasion"` (Rogue 2, Monk 2) and `"improved_evasion"` (Rogue 10, Monk 9), add the corresponding EF field assignment.

### Step 3 — `aidm/core/spell_resolver.py`
Update `_resolve_damage()` with the evasion/improved_evasion check blocks as specified above. Confirm `target_entity` (the raw entity dict) is accessible in this method alongside `target: TargetStats`.

### Step 4 — Tests (`tests/test_engine_evasion_gate.py`)
Gate: ENGINE-EVASION — 10 tests

| Test | Description |
|------|-------------|
| EV-01 | Rogue (EF.EVASION=True) succeeds Ref save vs Fireball (HALF): takes 0 damage |
| EV-02 | Rogue (EF.EVASION=True) fails Ref save vs Fireball: takes full damage (evasion does not apply on fail) |
| EV-03 | Fighter (no evasion) succeeds Ref save vs Fireball: takes half damage (no change from current) |
| EV-04 | Monk (EF.EVASION=True) succeeds Ref save vs Cone of Cold: takes 0 damage |
| EV-05 | Rogue with Improved Evasion (EF.IMPROVED_EVASION=True) succeeds Ref save: takes 0 damage |
| EV-06 | Rogue with Improved Evasion fails Ref save vs Fireball: takes half damage (not full) |
| EV-07 | Evasion does NOT apply to Will/Fort saves (only REF) |
| EV-08 | Evasion does NOT apply to NEGATES save_effect spells (target already takes 0 on success) |
| EV-09 | Chargen: Rogue at level 2 has EF.EVASION=True; Rogue at level 1 does not |
| EV-10 | Regression: ENGINE-SPELL-SLOTS 12/12 unchanged; non-evasion damage paths unaffected |

---

## Integration Seams

**Files touched:**
- `aidm/schemas/entity_fields.py` — 2 new constants
- `aidm/chargen/builder.py` — 2 EF field assignments at class ability grant points
- `aidm/core/spell_resolver.py` — `_resolve_damage()` updated (~10 lines)

**Files NOT touched:**
- `aidm/core/save_resolver.py` — no change; evasion is a damage modifier, not a save modifier
- Equipment files — armor restriction deferred

**Event constructor signature (mandatory):**
```python
Event(
    event_id=<int>,
    event_type=<str>,
    payload=<dict>,
    timestamp=<float>,
    citations=[],
)
```

**CLASS_LEVELS pattern (mandatory):**
```python
entity.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
```

**Target entity access:** Builder must confirm `target_entity` (raw dict) is available in `_resolve_damage()`. If it is not, it must be threaded through from the call site in `resolve_spell()`, which already has access to `world_state.entities`.

---

## Assumptions to Validate

1. `_resolve_damage()` has access to `target_entity` dict (not just `TargetStats`) — **validate before writing; if not, thread it through from `resolve_spell()`**
2. `save_type` is available inside `_resolve_damage()` — validate from function signature
3. `SaveEffect.HALF` and `SaveType.REF` are importable enums in spell_resolver.py — confirmed from current code
4. `EF.EVASION` check is safe on entities without the field (`entity.get(EF.EVASION, False)` = False) — standard pattern
5. Chargen builder at Rogue level 2 grants `"evasion"` string — confirmed from inspection; EF field assignment goes immediately alongside

---

## Known Gap (document, do not implement)

**Armor restriction:** PHB p.56 — rogue loses Evasion in medium/heavy armor. This WO does not enforce it. `EF.EVASION` is set at chargen and not cleared on armor equip. A separate WO (post-equip-system WO) must clear `EF.EVASION` when armor above light is equipped and restore it when removed. File this as FINDING-ENGINE-EVASION-ARMOR-001, LOW, OPEN at debrief.

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_spell_slots.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_evasion_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

ENGINE-EVASION 10/10 new. Existing spell/save gates unchanged.

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/schemas/entity_fields.py` — `EVASION`, `IMPROVED_EVASION` constants
- [ ] `aidm/chargen/builder.py` — EF field assignments at class ability grant
- [ ] `aidm/core/spell_resolver.py` — `_resolve_damage()` evasion check blocks
- [ ] `tests/test_engine_evasion_gate.py` — 10/10

**Gate:** ENGINE-EVASION 10/10
**Regression bar:** ENGINE-SPELL-SLOTS 12/12 unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-EVASION-001.md` on completion.

**Three-pass format:**
- Pass 1: per-file breakdown, key findings, open findings table
- Pass 2: PM summary ≤100 words
- Pass 3: retrospective — drift caught, patterns, recommendations

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
