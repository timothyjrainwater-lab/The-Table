# WO-ENGINE-WILD-SHAPE-001 — Druid Wild Shape Runtime (v1 — Small/Medium Beast)

**Type:** Builder WO
**Gate:** ENGINE-WILD-SHAPE
**Tests:** 10 (WS-01 through WS-10)
**Depends on:** Nothing
**Blocks:** Nothing
**Priority:** LOW-MEDIUM — Druid class feature, complex scope. v1 limited to Small/Medium beast forms only.

---

## 1. Target Lock

Druid Wild Shape (PHB p.36) allows the Druid to transform into a natural animal. At chargen, Druids receive `"wild_shape_small_medium"`, `"wild_shape_N_per_day"` etc. as class feature strings. At runtime, there is no `WildShapeIntent`, no resolver, no form-swapping logic, and no EF fields for current form or uses remaining. A Druid PC can be built but cannot transform.

**PHB spec (p.36):**
- Starts at Druid 4 (Small or Medium animal). Gains Large at level 6, Tiny at level 8. Huge/Plant/Elemental later.
- Uses per day: 1 (level 4), scaling by 1 per 2 levels.
- Druid may remain in animal form a number of hours equal to Druid level, or revert voluntarily as a free action.
- While in animal form: gains the animal's physical stats (Str, Dex, Con), natural armor, movement modes, natural attacks. Retains own mental stats (Int, Wis, Cha), class features, feats, and skills. Cannot cast spells (unless has Natural Spell feat).
- Equipment melds into the new form (non-functional).
- HP: The Druid does NOT gain the animal's HP total — instead, HP changes proportionally by the ratio of the animal's Con vs the Druid's Con (PHB p.36). For v1: simply swap physical stats and recalculate max HP from new Con modifier × existing HD count.

**v1 Scope:** Small and Medium beast forms only. Form library: Wolf, Black Bear, Riding Dog, Eagle, Constrictor Snake, Crocodile. Builder uses these six forms as the v1 form library (stats from SRD/bestiary data already in `oracle_db/`). Large, Tiny, Elemental, Plant deferred.

**Deliver:** `WildShapeIntent`, `RevertFormIntent`, `aidm/core/wild_shape_resolver.py`, EF constants, and gate ENGINE-WILD-SHAPE 10/10.

---

## 2. Binary Decisions

| # | Question | Answer |
|---|----------|--------|
| BD-01 | How is Wild Shape activated? | `WildShapeIntent(actor_id: str, form: str)`. `form` is one of: `"wolf"`, `"black_bear"`, `"riding_dog"`, `"eagle"`, `"constrictor_snake"`, `"crocodile"`. |
| BD-02 | How is reversion handled? | `RevertFormIntent(actor_id: str)`. Free action. Restores Druid's own stats. |
| BD-03 | How are uses tracked? | `EF.WILD_SHAPE_USES_REMAINING` (int). Decremented on transformation. Not decremented on reversion. |
| BD-04 | How is "currently transformed" tracked? | `EF.WILD_SHAPE_ACTIVE` (bool). `EF.WILD_SHAPE_FORM` (str: current form name). `EF.WILD_SHAPE_SAVED_STATS` (dict: snapshot of original Str, Dex, Con, AC, HP, attacks). |
| BD-05 | How are physical stats swapped? | `wild_shape_resolver` reads the form's stat block from a local lookup dict (hardcoded for v1 — 6 forms). Writes the form's Str/Dex/Con/natural_AC into the entity. Saves original values in `EF.WILD_SHAPE_SAVED_STATS`. On revert: restores from the saved snapshot. |
| BD-06 | HP during transformation? | On transformation: recalculate `max_hp = (new_con_modifier + 1) * druid_level` (simplified formula for v1). Set `current_hp = min(current_hp, new_max_hp)`. Emit `hp_changed` if current_hp was reduced. On revert: restore original max_hp; if current_hp > original max_hp, cap it. Log actual PHB HP proportional swap as FINDING-WILDSHAPE-HP-001 LOW. |
| BD-07 | Natural attacks during transformation? | Builder sets `EF.NATURAL_ATTACKS` on the entity to the form's attack list (e.g., wolf: bite 1d6+Str). Existing attack_resolver must have a path for natural attacks — builder verifies. If no natural attack path exists, emit an `unresolved_action` stub and log as FINDING-WILDSHAPE-NATURAL-ATTACKS-001 MEDIUM. Do not implement natural attack path in this WO. |
| BD-08 | Duration tracking? | `EF.WILD_SHAPE_HOURS_REMAINING` (int: Druid level). For v1, duration is not auto-decremented — DM calls `RevertFormIntent` explicitly or after sufficient in-game time. Log as FINDING-WILDSHAPE-DURATION-001 LOW. |
| BD-09 | Equipment handling? | Set `EF.EQUIPMENT_MELDED = True` on transformation. Attack resolver checks this flag — all weapon attacks blocked during transformation (use natural attacks only). Cleared on revert. |
| BD-10 | Natural Spell feat? | Deferred. If entity has `"natural_spell"` in EF.FEATS, log a warning event but do not implement spellcasting in animal form for v1. |

---

## 3. Contract Spec

### 3.1 New EF constants (entity_fields.py)

```python
WILD_SHAPE_ACTIVE = "wild_shape_active"                   # bool: currently transformed
WILD_SHAPE_FORM = "wild_shape_form"                       # str: current form name
WILD_SHAPE_USES_REMAINING = "wild_shape_uses_remaining"   # int: uses left today
WILD_SHAPE_SAVED_STATS = "wild_shape_saved_stats"         # dict: original stat snapshot
WILD_SHAPE_HOURS_REMAINING = "wild_shape_hours_remaining" # int: hours left in form
EQUIPMENT_MELDED = "equipment_melded"                     # bool: equipment non-functional
```

### 3.2 New intents (intents.py)

```python
@dataclass
class WildShapeIntent:
    type: Literal["wild_shape"] = "wild_shape"
    actor_id: str = ""
    form: str = ""  # must be in v1 form library

@dataclass
class RevertFormIntent:
    type: Literal["revert_form"] = "revert_form"
    actor_id: str = ""
```

Add both to `Intent` union and `parse_intent()`.

### 3.3 v1 Form library (local dict in wild_shape_resolver.py)

```python
WILD_SHAPE_FORMS = {
    "wolf":            {"str": 13, "dex": 15, "con": 15, "size": "medium", "natural_ac": 2, "attacks": [{"name": "bite", "dice": "1d6", "type": "piercing"}]},
    "black_bear":      {"str": 19, "dex": 13, "con": 15, "size": "medium", "natural_ac": 4, "attacks": [{"name": "claw", "dice": "1d4", "type": "slashing"}, {"name": "bite", "dice": "1d6", "type": "piercing"}]},
    "riding_dog":      {"str": 13, "dex": 15, "con": 15, "size": "medium", "natural_ac": 2, "attacks": [{"name": "bite", "dice": "1d6", "type": "piercing"}]},
    "eagle":           {"str": 10, "dex": 15, "con": 12, "size": "small",  "natural_ac": 1, "attacks": [{"name": "talon", "dice": "1d4", "type": "slashing"}]},
    "constrictor_snake": {"str": 15, "dex": 17, "con": 13, "size": "medium", "natural_ac": 3, "attacks": [{"name": "bite", "dice": "1d3", "type": "piercing"}]},
    "crocodile":       {"str": 15, "dex": 10, "con": 13, "size": "medium", "natural_ac": 5, "attacks": [{"name": "bite", "dice": "1d8", "type": "piercing"}]},
}
```

Builder verifies these values against `oracle_db/` bestiary data before writing. Values above are approximate — source of truth is oracle_db.

### 3.4 Events

| Event | Payload |
|-------|---------|
| `wild_shape_start` | `actor_id`, `form`, `uses_remaining`, `new_str`, `new_dex`, `new_con`, `new_natural_ac` |
| `wild_shape_end` | `actor_id`, `form_was`, `restored_str`, `restored_dex`, `restored_con` |

---

## 4. Implementation Plan

1. **Add EF constants** to `entity_fields.py`.

2. **Add `WildShapeIntent` and `RevertFormIntent`** to `intents.py`. Wire `parse_intent()`.

3. **Create `aidm/core/wild_shape_resolver.py`** with form library dict, `validate_wild_shape()`, `resolve_wild_shape()`, `resolve_revert_form()`.

4. **Modify `play_loop.py`**: wire `WildShapeIntent` and `RevertFormIntent`.

5. **Modify `attack_resolver.py`**: if `EF.EQUIPMENT_MELDED = True`, block weapon attacks (emit `intent_validation_failed` with `reason: equipment_melded`).

6. **Create `tests/test_engine_gate_wild_shape.py`** — 10 gate tests.

7. **Preflight:** 10/10 pass. Full suite: 0 new failures.

---

## 5. Gate Tests (ENGINE-WILD-SHAPE 10/10)

| ID | Description |
|----|-------------|
| WS-01 | Transform to Wolf: `wild_shape_start` event emitted, entity Str/Dex/Con updated to wolf stats |
| WS-02 | `EF.WILD_SHAPE_ACTIVE = True`, `EF.WILD_SHAPE_FORM = "wolf"`, original stats in `EF.WILD_SHAPE_SAVED_STATS` |
| WS-03 | `EF.WILD_SHAPE_USES_REMAINING` decremented on transformation |
| WS-04 | `EF.EQUIPMENT_MELDED = True` on transformation |
| WS-05 | Weapon attack while transformed: `intent_validation_failed`, `reason: equipment_melded` |
| WS-06 | Revert: `wild_shape_end` event, original Str/Dex/Con restored from saved snapshot |
| WS-07 | Revert clears `EF.WILD_SHAPE_ACTIVE`, `EF.EQUIPMENT_MELDED`, `EF.WILD_SHAPE_FORM` |
| WS-08 | Cannot transform while already transformed: `intent_validation_failed`, `reason: already_transformed` |
| WS-09 | No uses remaining: `intent_validation_failed`, `reason: no_wild_shape_uses` |
| WS-10 | Unsupported form (not in v1 library): `intent_validation_failed`, `reason: unsupported_form` |

---

## 6. Delivery Footer

**Files to create:**
```
aidm/core/wild_shape_resolver.py
tests/test_engine_gate_wild_shape.py
```

**Files to modify:**
```
aidm/schemas/entity_fields.py    ← add 6 new EF constants
aidm/schemas/intents.py          ← add WildShapeIntent + RevertFormIntent, wire parse_intent()
aidm/core/play_loop.py           ← wire both new intent types
aidm/core/attack_resolver.py     ← block weapon attacks when EQUIPMENT_MELDED
```

**Commit requirement:**
```
feat: WO-ENGINE-WILD-SHAPE-001 — Druid Wild Shape v1 (Small/Medium beast forms) — Gate ENGINE-WILD-SHAPE 10/10
```

**Preflight:**
```
pytest tests/test_engine_gate_wild_shape.py -v
```
10/10 must pass. Full suite: 0 new failures.

---

## 7. Integration Seams

- `EF.WILD_SHAPE_SAVED_STATS` must store a deep copy of the original stat fields — builder must use `copy.deepcopy()` to prevent aliasing
- `attack_resolver.py` EQUIPMENT_MELDED check: must fire before weapon lookup, not after — builder confirms the exact gate location in the resolver
- Form stats from oracle_db: builder reads bestiary data from `oracle_db/` to verify the hardcoded form stats are accurate before committing

---

## 8. Assumptions to Validate

- `oracle_db/` contains bestiary entries for all 6 v1 forms with mechanical stats (Str/Dex/Con/AC/attacks) — builder confirms before writing form library dict
- `EF.NATURAL_ATTACKS` field exists (or can be added without conflict) for storing the form's attack list — builder checks entity_fields.py first
- `attack_resolver.py` has a path for natural attacks or will return a stub — builder verifies and logs FINDING-WILDSHAPE-NATURAL-ATTACKS-001 if path is absent

---

## 9. Open Findings (deferred — log on completion)

| ID | Severity | Description |
|----|----------|-------------|
| FINDING-WILDSHAPE-HP-001 | LOW | HP swap uses simplified Con-based formula; actual PHB proportional swap deferred |
| FINDING-WILDSHAPE-DURATION-001 | LOW | Duration not auto-decremented; DM manually triggers revert |
| FINDING-WILDSHAPE-NATURAL-ATTACKS-001 | MEDIUM | Natural attack resolution path may be absent in attack_resolver; builder verifies and logs |

---

## 10. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
