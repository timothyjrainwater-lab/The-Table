# DEBRIEF — WO-DATA-DEAD-FILES-CLEANUP-001

**Commit:** `45a3e55`
**Date:** 2026-02-27
**WO:** WO-DATA-DEAD-FILES-CLEANUP-001
**Lifecycle:** ARCHIVE

---

## Pass 1 — Context Dump

### Gap Verified
Grep of `aidm/` (excluding the dead files themselves) confirmed zero production imports of:
- `aidm/data/equipment_definitions.py`
- `aidm/data/feat_definitions.py`
- `aidm/data/class_definitions.py`

All three files were test-only consumers (test files for the dead modules). Confirmed not SAI.

### Files Deleted
- `aidm/data/equipment_definitions.py` — ARMOR_REGISTRY, WEAPON_REGISTRY (runtime replaced by equipment_catalog.json)
- `aidm/data/feat_definitions.py` — FEAT_REGISTRY (runtime replaced by EF.FEATS list in entity dict)
- `aidm/data/class_definitions.py` — CLASS_FEATURE_GRANTS, MONK_UDAM_BY_LEVEL (runtime replaced by `_CLASS_FEATURES` dict in builder.py)
- `tests/test_data_equipment_001_gate.py` — stale test for deleted module
- `tests/test_data_feats_001_gate.py` — stale test for deleted module
- `tests/test_data_class_tables_001_gate.py` — stale test for deleted module
- `tests/test_data_feats_prereqs_001_gate.py` — stale test for deleted module

### Files Modified
| File | Change |
|------|--------|
| `aidm/chargen/builder.py` | Added canonical docstrings at equipment catalog section, `_CLASS_FEATURES` dict, and Step 8 Feats block |

### Files Created
| File | Tests |
|------|-------|
| `tests/test_data_dead_files_gate.py` | DDC-001 through DDC-004: 4/4 PASS |

### Gate Results
DDC-001–DDC-004: **4/4 PASS**

### `aidm/data/__init__.py` Check
Only re-exports from `policy_defaults_loader`, `scene_generator`, `equipment_catalog_loader`. No re-exports of deleted modules. No changes needed.

### Parallel Implementation Paths
N/A — deletion WO. No resolver modified.

---

## Pass 2 — PM Summary

Deleted 3 dead data registry files (equipment_definitions, feat_definitions, class_definitions) and their 4 stale test files. Added canonical docstrings at the live sources in builder.py marking where the data actually lives at runtime. New gate file confirms files are gone and imports raise ImportError. 4/4 DDC tests pass.

---

## Pass 3 — Retrospective

- **Out-of-scope findings:** None.
- **Kernel touches:** None.
- **Radar:** No findings.

---

*Debrief filed by Chisel.*
