# WO-ENGINE-WILDSHAPE-HP-001 — Wild Shape HP: PHB Proportional Formula

**Issued:** 2026-02-24
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** LOW (FINDING-WILDSHAPE-HP-001 — correctness gap; current formula underestimates HP for high-CON forms)
**WO type:** BUG (wrong formula)
**Gate:** ENGINE-WILDSHAPE-HP (10 tests)

---

## 1. Target Lock

Wild Shape HP is calculated as:
```python
new_hp_max = max(1, (new_con_mod + 1) * max(1, druid_level))
```

This formula is not in the PHB. PHB p.37: "The druid gains the animal's physical ability scores (Strength, Dexterity, Constitution), movement, natural armor, natural weapons, and special attacks." HP is NOT drawn from the animal's stats — the druid uses their **own HP pool**, adjusted for CON change.

**PHB p.37 Wild Shape HP rule:** The druid retains their current HP total. When CON changes, HP_MAX adjusts proportionally: new HP_MAX = (old HP_MAX / old CON modifier bonus) × new CON modifier bonus. More precisely: `new_HP_MAX = druid_HP_MAX × (new_CON_mod / old_CON_mod)` where CON mod is the HP-per-level contribution.

**Correct 3.5e formula (PHB p.37 + DMG p.290):**
```
new_HP_MAX = druid_base_HP_MAX + (new_CON_mod - old_CON_mod) × druid_level
new_HP_CURRENT = new_HP_MAX - (saved_HP_MAX - current_HP_CURRENT)
```

This preserves current damage taken while scaling max HP for the CON change. A 10th-level druid (HP_MAX=80, CON_mod=+2) transforming into a wolf (CON_mod=+2) keeps HP_MAX=80. Transforming into a black bear (CON_mod=+3) gets HP_MAX=90. The current formula gives `(3+1)×10 = 40` — half what it should be.

**Root cause:** `WILD_SHAPE_FORMS` has no `hit_dice` field. The current formula was a placeholder that uses druid_level as a substitute for HD count. This WO replaces it with the PHB-correct CON-delta formula, which requires no form-level schema change.

**PM inspection confirmed:** `WILD_SHAPE_FORMS` schema: `{str, dex, con, size, natural_ac, attacks}`. No `hit_dice`. The PHB-correct formula only needs `con` (already present) and the druid's saved stats (also already saved in `WILD_SHAPE_SAVED_STATS`).

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Which HP formula? | PHB delta formula: `new_HP_MAX = saved_HP_MAX + (new_CON_mod - old_CON_mod) × druid_level`. Druid level read from `EF.CLASS_LEVELS.get("druid", 1)`. |
| 2 | HP_CURRENT on transform? | `new_HP_CURRENT = new_HP_MAX - damage_taken` where `damage_taken = saved_HP_MAX - HP_CURRENT`. Preserves current damage. Clamped to `max(1, new_HP_CURRENT)`. |
| 3 | What is `saved_HP_MAX`? | Read from `EF.HP_MAX` before transform (the druid's true-form HP_MAX). It's already stored in `WILD_SHAPE_SAVED_STATS["hp_max"]` at transform time — confirmed by revert logic. |
| 4 | What is `old_CON_mod`? | Read from `EF.CON_MOD` before transform (also in `WILD_SHAPE_SAVED_STATS["con_mod"]`). |
| 5 | What if old_CON_mod == new_CON_mod? | No HP change. HP_MAX unchanged. |
| 6 | Schema change to WILD_SHAPE_FORMS? | **No.** The PHB formula uses CON mod delta, which is derivable from existing `con` stat in form data. No `hit_dice` field needed. |
| 7 | Revert HP calculation change? | Yes — same delta formula in reverse. On revert: `restored_HP_MAX = saved_HP_MAX` (already saved). `restored_HP_CURRENT = restored_HP_MAX - damage_taken_in_form`. Current revert logic already does this correctly (reads from WILD_SHAPE_SAVED_STATS). No change needed on revert. |
| 8 | Does this change WILD_SHAPE_SAVED_STATS? | No. `hp_max` and `con_mod` are already saved at transform. Both are needed for the delta formula and are already there. |

---

## 3. Contract Spec

### Modification: `resolve_wild_shape()` in `aidm/core/wild_shape_resolver.py`

**Replace lines ~187-189** (current placeholder formula):

```python
# CURRENT (wrong):
new_hp_max = max(1, (new_con_mod + 1) * max(1, druid_level))
actor[EF.HP_MAX] = new_hp_max
actor[EF.HP_CURRENT] = min(actor.get(EF.HP_CURRENT, 1), new_hp_max)
```

**With (PHB p.37 delta formula):**
```python
# PHB p.37: HP_MAX adjusts by CON_mod delta × druid level
old_con_mod = saved_stats.get("con_mod", 0)
druid_level = actor.get(EF.CLASS_LEVELS, {}).get("druid", 1)
saved_hp_max = saved_stats.get("hp_max", 1)
current_hp = actor.get(EF.HP_CURRENT, saved_hp_max)
damage_taken = max(0, saved_hp_max - current_hp)

con_delta = new_con_mod - old_con_mod
new_hp_max = max(1, saved_hp_max + con_delta * druid_level)
new_hp_current = max(1, new_hp_max - damage_taken)

actor[EF.HP_MAX] = new_hp_max
actor[EF.HP_CURRENT] = new_hp_current
```

Note: `saved_stats` is already computed earlier in `resolve_wild_shape()` (it stores the pre-transform values). `new_con_mod` is already computed from the form's `con` stat. No new reads required.

### No other files change.

`resolve_revert_form()` already restores `hp_max` from `WILD_SHAPE_SAVED_STATS["hp_max"]` and caps `HP_CURRENT` — that logic is correct and unchanged.

---

## 4. Implementation Plan

### Step 1 — `aidm/core/wild_shape_resolver.py` only
Replace the 3-line HP placeholder with the 9-line PHB delta formula. No other files touched.

Verify insertion point: find `new_hp_max = max(1, (new_con_mod + 1)` — replace that block.

### Step 2 — Tests (`tests/test_engine_wildshape_hp_gate.py`)
Gate: ENGINE-WILDSHAPE-HP — 10 tests

| Test | Description |
|------|-------------|
| WHP-01 | Wolf transform: CON unchanged (wolf CON_mod = druid CON_mod) → HP_MAX unchanged |
| WHP-02 | Black bear transform: CON_mod +1 vs druid → HP_MAX increases by druid_level |
| WHP-03 | Crocodile transform: CON_mod +2 vs druid → HP_MAX increases by 2×druid_level |
| WHP-04 | Eagle transform: CON_mod lower than druid → HP_MAX decreases |
| WHP-05 | Damage-taken preserved: druid at 60% HP transforms → same damage offset in new form |
| WHP-06 | HP_CURRENT clamped to max(1, new_HP_MAX - damage_taken) — not below 1 |
| WHP-07 | Revert: HP_MAX restores to saved value; damage-taken offset preserved across form |
| WHP-08 | Level 5 druid vs level 10 druid: same CON delta produces proportionally different HP change |
| WHP-09 | No regression: existing ENGINE-WILD-SHAPE 10/10 still pass |
| WHP-10 | Full transform-revert cycle: HP_MAX returns exactly to pre-transform value |

---

## Integration Seams

**Files touched:**
- `aidm/core/wild_shape_resolver.py` — 3 lines replaced with 9 lines (~+6 net)

**Files NOT touched:** `entity_fields.py`, `intents.py`, `play_loop.py`, `WILD_SHAPE_FORMS` schema.

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

**Entity field pattern (mandatory):**
```python
actor.get(EF.CLASS_LEVELS, {}).get("druid", 1)
saved_stats = actor.get(EF.WILD_SHAPE_SAVED_STATS, {})
old_con_mod = saved_stats.get("con_mod", 0)
saved_hp_max = saved_stats.get("hp_max", 1)
```

**CON modifier calculation:** The form data has `con` (ability score, e.g. 15). CON_mod = `(con - 10) // 2`. This is computed earlier in `resolve_wild_shape()` as `new_con_mod` — use that existing variable directly.

---

## Assumptions to Validate

1. `WILD_SHAPE_SAVED_STATS` dict contains `"con_mod"` and `"hp_max"` keys — confirmed by revert logic reading these fields
2. `new_con_mod` is computed from `form_data["con"]` before the HP block — confirmed by PM inspection (used for EF.CON_MOD assignment above)
3. `druid_level = actor.get(EF.CLASS_LEVELS, {}).get("druid", 1)` — correct pattern per architectural invariant

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_cp24.py tests/test_engine_gate_natural_attack.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_wildshape_hp_gate.py -v
python -m pytest tests/test_engine_gate_barbarian_rage.py tests/test_engine_gate_cp24.py -x -q
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

ENGINE-WILD-SHAPE 10/10 unchanged. ENGINE-WILDSHAPE-HP 10/10 new.

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/core/wild_shape_resolver.py` — HP formula replaced (~6 lines net change)
- [ ] `tests/test_engine_wildshape_hp_gate.py` — 10/10

**Gate:** ENGINE-WILDSHAPE-HP 10/10
**Regression bar:** ENGINE-WILD-SHAPE 10/10 unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-WILDSHAPE-HP-001.md` on completion.

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
