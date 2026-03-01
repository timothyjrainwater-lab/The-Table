**Lifecycle:** ARCHIVE

# DEBRIEF — WO-ENGINE-CONDITIONS-LEGACY-FIX-001

**Commit:** `801875d`
**Gates:** CLF-001..008 — 8/8 PASS
**Batch:** AM (WO4 of 4)

---

## Pass 1 — Context Dump

### Files Changed

| File | Lines | Change |
|------|-------|--------|
| `aidm/core/conditions.py` | ~127–136 (type guard in get_condition_modifiers) | `isinstance(list)` warn+return → `not isinstance(dict)` raise ValueError |
| `aidm/core/conditions.py` | ~74–86 (_normalize_condition_dict docstring) | Added NOTE: test-verifiability only, not on live path |

### Before / After

**Before:**
```python
if isinstance(conditions_data, list):
    _log.warning(
        "get_condition_modifiers() called with list format for entity %s; "
        "returning zero modifiers. Use dict format.",
        actor_id,
    )
    return ConditionModifiers()
```

**After:**
```python
# WO-ENGINE-CONDITIONS-LEGACY-FIX-001: Raise ValueError on non-dict conditions data.
if not isinstance(conditions_data, dict):
    raise ValueError(
        f"get_condition_modifiers() requires a dict of {{condition_name: ConditionInstance}}, "
        f"got {type(conditions_data).__name__!r} for entity {actor_id!r}. "
        "Legacy list format ['condition'] is not supported. "
        "Use create_*_condition().to_dict() or build ConditionInstance directly."
    )
```

**Scope extension:** Old guard caught only `list`; new guard catches `list`, `str`, `int`, or any non-dict — includes all malformed formats. CLF-003 (int) proves this.

### Gate file
`tests/test_engine_conditions_legacy_fix_gate.py` — 8 tests.

### Test architecture note
`get_condition_modifiers(world_state, actor_id)` takes WorldState + entity ID — NOT a conditions dict. Gate tests construct WorldState with entity having `EF.CONDITIONS = test_value` to exercise the guard path.

---

## Pass 2 — PM Summary

`get_condition_modifiers()` now raises `ValueError` (not silently returns zero) when `EF.CONDITIONS` is any non-dict value (list, str, int). Old behavior: `isinstance(list)` check logged a warning and returned `ConditionModifiers()` — bugs from list-format conditions went undetected. New behavior: immediate `ValueError` with entity ID + actual type in message, forcing callers to discover format errors at the point of failure. The empty-dict falsy-path (`if not conditions_data:`) still returns zero cleanly — only truthy non-dicts raise. CLF-008 confirms missing entity also stays silent (returns zero, not raises). 8/8 gates pass.

---

## Pass 3 — Retrospective

**_normalize_condition_dict()** is now test-verifiability only — it is not called from any live code path. Docstring updated with explicit NOTE to prevent future confusion.

**Existing call sites audited:** `get_condition_modifiers()` is called from `attack_resolver.py`, `save_resolver.py`, `combat_controller.py`. All current callers set `EF.CONDITIONS` as a proper dict via `apply_condition()` or `create_*_condition().to_dict()`. No existing call sites broken.

**None/0 edge case:** `if not conditions_data:` catches `None`, empty dict, `0`, and empty list before the type guard fires — only truthy non-dicts (non-empty list, non-empty string, etc.) hit the ValueError. This is correct behavior: a None-conditions entity is treated as "no conditions", not an error.

**Kernel touches:** None.

---

## Radar

| ID | Severity | Status | Note |
|----|----------|--------|------|
| — | — | — | No new findings |

---

## Coverage Map Update

Row 171 (Condition empty-dict format robustness) updated:
- Changed "legacy list format logs warning + returns zero" → "legacy list format (or any non-dict) raises ValueError"
- Added: `CLF-001..008. Batch AM.`

## Consume-Site Confirmation

This WO is behavioral / guard-layer — no EF field set/read chain.

- **Write site:** N/A (no new field; guard applies to existing EF.CONDITIONS read)
- **Read site:** `conditions.py get_condition_modifiers()` — type guard at top of function
- **Effect:** Any caller that stored `EF.CONDITIONS` as a list now gets immediate ValueError instead of silent zero-modifiers
- **Gate proof:** CLF-001 (list raises ValueError), CLF-005 (actor_id in message), CLF-006 (valid dict no exception), CLF-008 (missing entity → zero, not raise)
