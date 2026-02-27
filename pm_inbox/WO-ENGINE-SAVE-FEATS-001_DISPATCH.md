# WO-ENGINE-SAVE-FEATS-001 — Save Feats Wire (Great Fortitude / Iron Will / Lightning Reflexes)

**WO ID:** WO-ENGINE-SAVE-FEATS-001
**Type:** Engine feature
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Batch:** Engine Batch N
**Gate label:** ENGINE-SAVE-FEATS
**Gate file:** `tests/test_engine_save_feats_gate.py`
**Gate count:** 8 tests (SF-001 – SF-008)

---

## Gap Verification (coverage map confirmed PARTIAL 2026-02-26)

| Feat | PHB | Status in schemas/feats.py | Status in save_resolver.py |
|------|-----|---------------------------|---------------------------|
| Great Fortitude | p.94 | Registered | NOT WIRED |
| Iron Will | p.97 | Registered | NOT WIRED |
| Lightning Reflexes | p.97 | Registered | NOT WIRED |

**⚠ CRITICAL: `tests/test_engine_save_feats_gate.py` already exists as an UNTRACKED file.**
On session boot, read this file immediately. If it already has 8 passing tests, run them first. If they all pass, treat as SAI — commit the existing test file, finding CLOSED. Do **not** write duplicate tests.

**Assumptions to Validate before writing:**
1. Confirm `save_resolver.py` does NOT currently read feat bonuses for GF/IW/LR.
2. Confirm feat IDs in `schemas/feats.py` — exact string values needed for feat check (e.g., `"great_fortitude"`, `"iron_will"`, `"lightning_reflexes"`).
3. Check if `EF.FEATS` list is how feats are stored on entity, or if there's a dedicated EF field per feat.

---

## Scope

**Files:** `aidm/core/save_resolver.py`
**Read only:** `aidm/schemas/feats.py` (find exact feat ID strings), `aidm/schemas/entity_fields.py` (confirm EF.FEATS field structure)

---

## Implementation

In `save_resolver.py`, in the function that accumulates save modifiers (likely `resolve_fort_save`, `resolve_ref_save`, `resolve_will_save` or a shared bonus accumulation), add feat bonus lookup:

```python
# Great Fortitude
if "great_fortitude" in entity.get(EF.FEATS, []):
    fort_bonus += 2

# Iron Will
if "iron_will" in entity.get(EF.FEATS, []):
    will_bonus += 2

# Lightning Reflexes
if "lightning_reflexes" in entity.get(EF.FEATS, []):
    ref_bonus += 2
```

Use exact feat ID strings from `schemas/feats.py` — do not guess. These are named bonuses (feat type), which stack with morale, circumstance, and condition modifiers.

The save bonus should appear in the `save_result` payload so it's visible in event output. If save events include a `breakdown` dict, add a `feat_bonus` key.

---

## Gate Tests (SF-001 – SF-008)

```python
# SF-001: Entity with feat="great_fortitude" → Fort save +2 vs baseline
# Expect: entity with feat saves at base+2 vs identical entity without feat

# SF-002: Entity with feat="iron_will" → Will save +2 vs baseline
# Expect: +2 on Will save roll (or same roll, higher result)

# SF-003: Entity with feat="lightning_reflexes" → Ref save +2 vs baseline
# Expect: +2 on Ref save roll

# SF-004: Entity with no save feats → no bonus (regression check)
# Expect: save at base value, no feat_bonus in breakdown

# SF-005: Great Fortitude stacks with condition penalties (e.g., SHAKEN -2)
# Expect: net Fort save = base + 2 (feat) - 2 (shaken) = base

# SF-006: All three feats on one entity → each applies to its save type only
# Expect: +2 Fort (from GF), +2 Will (from IW), +2 Ref (from LR) — no cross-contamination

# SF-007: Divine Grace (paladin CHA bonus to saves) stacks with save feats
# Expect: Fort = base + CHA_mod + 2 (GF) on a paladin with both

# SF-008: Save event breakdown includes feat_bonus field when feat present
# Expect: save event payload contains feat_bonus=2 for relevant save type
```

---

## Debrief Requirements

Three-pass format. Pass 3: document whether the untracked `test_engine_save_feats_gate.py` was SAI (already complete) or was a stub. Note the exact feat ID strings confirmed in schemas/feats.py.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-SAVE-FEATS-001.md`

---

## Session Close Conditions

- [ ] `git add aidm/core/save_resolver.py tests/test_engine_save_feats_gate.py`
- [ ] `git commit`
- [ ] SF-001–SF-008: 8/8 PASS; zero regressions
