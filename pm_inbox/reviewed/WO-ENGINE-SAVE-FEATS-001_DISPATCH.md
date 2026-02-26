# WO-ENGINE-SAVE-FEATS-001 — Wire Great Fortitude / Iron Will / Lightning Reflexes

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** HIGH (FINDING-COVERAGE-MAP-001 — silent wrong saves on every affected character)
**WO type:** BUG (schema complete; enforcement absent)
**Gate:** ENGINE-SAVE-FEATS (10 tests)

---

## 1. Target Lock

**What works:** All three feats are defined in `aidm/schemas/feats.py` (lines ~343–366). `FeatID.GREAT_FORTITUDE`, `FeatID.IRON_WILL`, `FeatID.LIGHTNING_REFLEXES` exist with correct descriptions (+2 to their respective saves, PHB pp.94–97). The feat schema is complete.

**What's missing:** `get_save_bonus()` in `aidm/core/save_resolver.py` (lines 69–128) never queries the entity's feat list. Any character with one of these three feats — by far the most common feat picks for fighters, paladins, and bards — makes saves 2 points lower than PHB specifies. Silent wrong output on every affected save.

**Root cause (confirmed by PM inspection):**
- `get_save_bonus()` computes: `base_save + ability_mod + condition_save_mod + inspire_courage_bonus`
- No `entity.get(EF.FEATS, [])` lookup of any kind
- `feat_resolver.py` has `get_attack_modifier()` and `get_ac_modifier()` as established patterns — no `get_save_modifier()` equivalent

**PHB references:**
- Great Fortitude: PHB p.94 — "+2 on Fortitude saving throws"
- Iron Will: PHB p.97 — "+2 on Will saving throws"
- Lightning Reflexes: PHB p.97 — "+2 on Reflex saving throws"

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Add logic in `save_resolver.py` or `feat_resolver.py`? | `save_resolver.py` directly — inline, matching the `inspire_courage_bonus` pattern. No need for a new `get_save_modifier()` function in feat_resolver; the lookup is 3 lines. |
| 2 | Feat check format? | `entity.get(EF.FEATS, [])` returns a list. Check `"great_fortitude" in feats` etc. Use lowercase string keys matching the existing feat ID convention in the schema. |
| 3 | Does stacking matter here? | No. Each feat is unique. A character cannot have Great Fortitude twice. No stacking guard needed. |
| 4 | Add to STP modifiers list? | Yes — include feat bonus in the STP modifiers breakdown for auditability, matching how `inspire_courage_bonus` is included. |
| 5 | Does Toughness need the same treatment? | No. Toughness adds HP at chargen, not at save resolution time. Out of scope for this WO. |

---

## 3. Contract Spec

### Modification: `aidm/core/save_resolver.py` — `get_save_bonus()`

After the `inspire_courage_bonus` block and before the `total_bonus` sum, add:

```python
# WO-ENGINE-SAVE-FEATS-001: Great Fortitude / Iron Will / Lightning Reflexes
feats = entity.get(EF.FEATS, [])
feat_save_bonus = 0
if save_type == SaveType.FORT and "great_fortitude" in feats:
    feat_save_bonus = 2
elif save_type == SaveType.REF and "lightning_reflexes" in feats:
    feat_save_bonus = 2
elif save_type == SaveType.WILL and "iron_will" in feats:
    feat_save_bonus = 2

total_bonus = base_save + ability_mod + condition_save_mod + inspire_courage_bonus + feat_save_bonus
```

**No other files require changes.** The feat IDs (`"great_fortitude"`, `"iron_will"`, `"lightning_reflexes"`) must match whatever format `EF.FEATS` stores — confirm this from an existing entity fixture. The pattern `"power_attack" in feats` or similar is already used in feat_resolver.py and sets the convention.

---

## 4. Implementation Plan

### Step 1 — `aidm/core/save_resolver.py`
Add the 6-line feat bonus block inside `get_save_bonus()`, after `inspire_courage_bonus` assignment and before `total_bonus` computation.

### Step 2 — Tests (`tests/test_engine_save_feats_gate.py`)
Gate: ENGINE-SAVE-FEATS — 10 tests

| Test | Description |
|------|-------------|
| SF-01 | Entity with Great Fortitude: Fort save gets +2 vs entity without feat |
| SF-02 | Entity with Iron Will: Will save gets +2 |
| SF-03 | Entity with Lightning Reflexes: Ref save gets +2 |
| SF-04 | Great Fortitude does NOT affect Ref or Will saves |
| SF-05 | Iron Will does NOT affect Fort or Ref saves |
| SF-06 | Lightning Reflexes does NOT affect Fort or Will saves |
| SF-07 | Entity with all three feats: each save type gets exactly +2 from the correct feat |
| SF-08 | Entity with no save feats: bonus = 0 (no regression to existing save math) |
| SF-09 | Feat bonus stacks correctly with condition modifiers (shaken = −2 + feat = +2 → net 0) |
| SF-10 | Regression: existing save gate tests unchanged (condition_saves gate CP-18 still 10/10) |

---

## Integration Seams

**Files touched:**
- `aidm/core/save_resolver.py` — ~6 lines added inside `get_save_bonus()`

**Files NOT touched:**
- `aidm/schemas/feats.py` — already complete
- `aidm/schemas/entity_fields.py` — no new constants needed (EF.FEATS already exists)
- `aidm/core/feat_resolver.py` — no change

**Feat lookup pattern (mandatory — match existing usage):**
```python
feats = entity.get(EF.FEATS, [])
if "great_fortitude" in feats:
    ...
```
Confirm feat ID string format from a real entity fixture before writing. If the fixture uses `FeatID.GREAT_FORTITUDE` enum values rather than strings, adapt accordingly.

**SaveType enum values:**
```python
SaveType.FORT  # Fortitude
SaveType.REF   # Reflex
SaveType.WILL  # Will
```
Confirmed from save_resolver.py.

---

## Assumptions to Validate

1. `EF.FEATS` is a list (not a dict) on entity — confirmed from feat_resolver.py pattern
2. Feat IDs are stored as lowercase strings in the list — **validate against a fixture before writing**
3. `SaveType` enum has `FORT`, `REF`, `WILL` — confirmed from save_resolver.py inspection
4. `get_save_bonus()` is the single source of truth for save totals — confirm no parallel path in spell_resolver.py

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_cp18.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_save_feats_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

ENGINE-SAVE-FEATS 10/10 new. CP-18 10/10 unchanged.

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/core/save_resolver.py` — 6-line feat bonus block in `get_save_bonus()`
- [ ] `tests/test_engine_save_feats_gate.py` — 10/10

**Gate:** ENGINE-SAVE-FEATS 10/10
**Regression bar:** CP-18 10/10 unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-SAVE-FEATS-001.md` on completion.

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
