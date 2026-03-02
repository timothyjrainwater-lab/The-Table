**Lifecycle:** ARCHIVE

# DEBRIEF — WO-JUDGMENT-VALIDATOR-001

**Commit:** `9df4140`
**Gates:** JV-001..008 — 8/8 PASS
**Batch:** AN (single WO)

---

## Pass 1 — Context Dump

### Files Changed

| File | Change |
|------|--------|
| `aidm/schemas/ruling_artifact.py` | Added `ability_or_skill: Optional[str] = None` after `clarification_message` |
| `aidm/core/ruling_validator.py` | Load srd_dc_ranges.json + srd_skills.json at module init; build `_VALID_MECHANICS` frozenset; mechanic legality check; docstring updated |
| `tests/test_engine_judgment_validator_001_gate.py` | New — JV-001..008 |

### Before / After — `ruling_artifact.py`

**Before (line 31):** `clarification_message: Optional[str] = None` (last field)

**After:**
```python
    # Optional Phase 0 fields (populated when routing hook has more context)
    dc: Optional[int] = None
    clarification_message: Optional[str] = None

    # Phase 1: mechanic legality check (WO-JUDGMENT-VALIDATOR-001)
    ability_or_skill: Optional[str] = None
```

### Before / After — `ruling_validator.py`

**Before (lines 1–6):**
```python
# WO-JUDGMENT-SHADOW-001: Phase 0 validator shell
from typing import List, Tuple
from aidm.schemas.ruling_artifact import RulingArtifactShadow

_DC_MIN = 5
_DC_MAX = 40
```

**After (module init):**
```python
import json
import os
from typing import List, Tuple
from aidm.schemas.ruling_artifact import RulingArtifactShadow

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

with open(os.path.join(_DATA_DIR, "srd_dc_ranges.json"), encoding="utf-8") as _f:
    _dc_data = json.load(_f)
_DC_MIN: int = _dc_data["dc_min"]   # 5 — PHB p.65
_DC_MAX: int = _dc_data["dc_max"]   # 40 — PHB p.65

with open(os.path.join(_DATA_DIR, "srd_skills.json"), encoding="utf-8") as _f:
    _srd_skills = json.load(_f)

_VALID_MECHANICS: frozenset = frozenset(
    {s["name"] for s in _srd_skills}
    | {
        "strength", "dexterity", "constitution",
        "intelligence", "wisdom", "charisma",
        "str", "dex", "con", "int", "wis", "cha",
        "none",
    }
)
```

**Mechanic legality block added after DC bounds check:**
```python
# Mechanic legality (Phase 1: WO-JUDGMENT-VALIDATOR-001)
if artifact.ability_or_skill is not None:
    normalized = artifact.ability_or_skill.lower().strip().replace(" ", "_")
    if normalized not in _VALID_MECHANICS:
        reasons.append(
            f"unrecognized mechanic: {artifact.ability_or_skill!r} — "
            "not in SRD skill list or ability score set (srd_skills.json, PHB p.7)"
        )
```

### SRD file load confirmed (actual run)

- `srd_skills.json` loaded at module import: **49 skills**, `_VALID_MECHANICS` set size: **61** (49 skills + 6 full ability names + 6 abbreviations + "none")
- `srd_dc_ranges.json` loaded: `dc_min=5`, `dc_max=40` (PHB p.65)

### Normalization worked example

Input: `"Jump"` → `.lower()` → `"jump"` → `.strip()` → `"jump"` → `.replace(" ", "_")` → `"jump"` → found in `_VALID_MECHANICS` ✓

### Gate file
`tests/test_engine_judgment_validator_001_gate.py` — 8 tests. JV-001 cross-checks loaded values against the actual JSON file to prove data-driven load (not coincidental constant match).

---

## Pass 2 — PM Summary

Phase 0 ruling_validator.py advanced to Phase 1. Two changes: (1) `_DC_MIN`/`_DC_MAX` now loaded from `srd_dc_ranges.json` at module import — hardcoded constants eliminated, JV-001 proves the load against file content. (2) `_VALID_MECHANICS` frozenset built from `srd_skills.json` (49 skills) + 6 ability score full names + 6 abbreviations + "none" sentinel; when `ability_or_skill` is provided and doesn't normalize-match, verdict is "fail" with "unrecognized" reason. `RulingArtifactShadow` gains `ability_or_skill: Optional[str] = None`. Phase 0 DC bounds + schema completeness paths structurally unchanged — JV-008 confirms `needs_clarification` still fires for dc=45. 8/8 gates pass.

---

## Pass 3 — Retrospective

**Phase 0 gates verified:** JS-001..008 all still pass (16 total judgment tests confirmed after commit).

**Import direction confirmed:** `ruling_validator.py` imports only `stdlib` (json, os, typing) + `aidm.schemas.ruling_artifact`. No import of session_orchestrator or any runtime module. Constraint satisfied.

**frozenset confirmed:** `_VALID_MECHANICS` is `frozenset` — not `set`. No mutation at runtime. Determinism rule satisfied.

**`_VALID_MECHANICS` covers "STR" abbreviation:** Normalization lowercases before lookup, so "STR" → "str" which is in the set. All PHB abbreviations covered.

**Out-of-scope finding:** None surfaced. The normalization `.replace(" ", "_")` handles multi-word inputs (e.g., "Use Magic Device" → "use_magic_device") — this is forward-compatible with psionic/exotic skills that may have spaces, though they'd still fail `_VALID_MECHANICS` check since srd_skills.json entries use underscore form.

**Kernel touches:** None.

---

## Radar

| ID | Severity | Status | Note |
|----|----------|--------|------|
| — | — | — | No new findings |

---

## ML Preflight Checklist

- [x] ML-001: Gap verified — `ability_or_skill` absent from `RulingArtifactShadow` before this WO (PM confirmed, ruling_artifact.py line 31)
- [x] ML-002: JV-001..008 all pass; JS-001..008 still pass (no regressions)
- [x] ML-003: No regressions — 16/16 judgment gates pass
- [x] ML-004: EF.* N/A — no EF fields involved
- [x] ML-005: Commit hash `9df4140` in debrief header
- [x] ML-006: Coverage map updated — Section 17 row added for Judgment Layer Validator

## PM Acceptance Notes — all confirmed

1. **JV-001 data-driven load:** Cross-checks `_DC_MIN`/`_DC_MAX` against actual file content. Before/after snippet shown above — hardcoded lines 5-6 replaced with json.load path. ✓
2. **`_VALID_MECHANICS` as frozenset:** Confirmed — `frozenset(...)` in module init. ✓
3. **Normalization documented:** `lower().strip().replace(" ", "_")` shown above; "Jump" → "jump" worked example traced. ✓
4. **Phase 0 path intact:** JV-008 passes (`dc=45, ability_or_skill="bluff"` → `"needs_clarification"`). DC bounds check structurally unchanged. ✓
5. **Import direction:** Only `json`, `os`, `typing`, `aidm.schemas.ruling_artifact` imported. No runtime modules. ✓
6. **SRD file read confirmed:** `srd_skills.json` → 49 skills, `_VALID_MECHANICS` size 61. `srd_dc_ranges.json` → dc_min=5, dc_max=40. Actual values, not from spec. ✓

## Coverage Map Update

Section 17 — new row added:
- **Judgment Layer Validator** | SPEC-RULING-CONTRACT-001 | **PARTIAL** | `ruling_validator.py`, `ruling_artifact.py`
- Phase 0 (JS-001..008) + Phase 1 (JV-001..008) IMPLEMENTED. NOT STARTED: modifier source checking, rationale quality.

## Consume-Site Confirmation

- **Write site (schema):** `ruling_artifact.py` — `ability_or_skill: Optional[str] = None`
- **Write site (data):** `srd_skills.json` + `srd_dc_ranges.json` (WO-DATA-SRD-EXTRACT-001, 70e0509)
- **Read site:** `ruling_validator.py validate_ruling_artifact()` — `artifact.ability_or_skill` → normalized → `_VALID_MECHANICS` lookup
- **Effect:** Unrecognized mechanic → verdict "fail", reason contains "unrecognized"
- **Gate proof:** JV-007 (`ability_or_skill="flurbozle"` → verdict "fail", reason "unrecognized")
