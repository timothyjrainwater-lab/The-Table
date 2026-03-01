# DEBRIEF: WO-DATA-SRD-EXTRACT-001 - SRD Skill + DC Data Extract

**Lifecycle:** ARCHIVE
**Commit:** 70e0509
**Filed by:** Chisel
**Session:** 27 (this session)
**Date:** 2026-03-01
**WO:** WO-DATA-SRD-EXTRACT-001
**Status:** FILED - awaiting PM verdict

---

## Pass 1 - Context Dump

### Summary

Extracted 49 PHB SRD skills from zellfaze-zz/dnd-generator (CC0) into `aidm/data/srd_skills.json`.
Created `aidm/data/srd_dc_ranges.json` (dc_min=5, dc_max=40, PHB p.65). Extraction script
`scripts/extract_srd_data.py` is idempotent; phb_source/ gitignored (pre-existing entry on line 59).
CONSUME_DEFERRED: WO-JUDGMENT-VALIDATOR-001 is the designated consumer. 8/8 SE gates pass.

### Files Changed

| File | Type | Change |
|------|------|--------|
| `scripts/extract_srd_data.py` | NEW | 62-line extraction script; reads phb_source/skills.json -> srd_skills.json + srd_dc_ranges.json |
| `aidm/data/srd_skills.json` | NEW | 49 SRD skill entries (sorted by name, sort_keys=True) |
| `aidm/data/srd_dc_ranges.json` | NEW | DC bounds: dc_max=40, dc_min=5, source="PHB p.65" |
| `tests/test_srd_extract_gate.py` | NEW | SE-001..SE-008 gate tests |
| `docs/ENGINE_COVERAGE_MAP.md` | MODIFIED | Phase 2 Data Layer section added with SRD rows |

### PM Acceptance Note 1 - Actual JSON structure documented

**Actual source structure (zellfaze-zz/dnd-generator phb/skills.json):**
- Source is a **LIST** (not dict — spec template used dict, adapted).
- Fields in source:
  - `name`: display name (e.g. `"Spellcraft"`)
  - `key`: ability score abbreviation, capitalized (e.g. `"Int"`)
  - `trained`: boolean for trained_only
  - `armorcheck`: boolean for armor_check_penalty
  - `synergy`: array of skill display names (strings)
  - `magic`, `psi`: boolean flags (not exported — out of scope)

**Mapping applied (vs spec template):**
| Spec field | Source field | Normalization |
|------------|-------------|---------------|
| `name` | `name` | `.lower().replace(" ", "_")` |
| `ability` | `key` | `.lower()` |
| `trained_only` | `trained` | `bool()` |
| `armor_check_penalty` | `armorcheck` | `bool()` |
| `synergy` | `synergy` | each entry: `.lower().replace(" ", "_")`, list sorted |

**Note on Speak Language:** `key: ""` (empty) — exported as `ability: ""`. Valid (Speak Language has no ability check; PHB p.82).

**Note on Knowledge skills:** Parentheses preserved in normalized name (e.g. `"knowledge_(arcana)"`). This is correct per the normalization function `lower().replace(" ", "_")`.

### PM Acceptance Note 2 - Skill count in output

**49 skills extracted.** Confirmed ≥ 30 (SE-002 PASS). Full list includes 10 Knowledge sub-skills, 3 psionic skills (Autohypnosis, Control Shape, Psicraft). All standard PHB combat/skill skills present.

### PM Acceptance Note 3 - Spellcraft spot-check

From `aidm/data/srd_skills.json`:
```json
{
  "ability": "int",
  "armor_check_penalty": false,
  "name": "spellcraft",
  "synergy": ["use_magic_device"],
  "trained_only": true
}
```

- `ability = "int"` ✓ (PHB p.82: Intelligence)
- `trained_only = true` ✓ (PHB p.82: trained only)
- `synergy = ["use_magic_device"]` ✓ (PHB p.82: Spellcraft grants +2 to UMD)

### PM Acceptance Note 4 - sort_keys=True confirmed

`srd_dc_ranges.json` content (keys sorted alphabetically):
```json
{
  "dc_max": 40,
  "dc_min": 5,
  "source": "PHB p.65"
}
```
Keys: `dc_max < dc_min < source` — alphabetical order confirmed. `json.dumps(..., sort_keys=True)` used in extraction script line 58.

### PM Acceptance Note 5 - .gitignore for phb_source/

`scripts/phb_source/` was already present in `.gitignore` (line 59, pre-existing entry from prior sessions). No change needed. Confirmed via `grep -n "phb_source" .gitignore` → line 59. Source file `scripts/phb_source/skills.json` is NOT committed.

### PM Acceptance Note 6 - CONSUME_DEFERRED explicit

`aidm/data/srd_skills.json` and `aidm/data/srd_dc_ranges.json` are **CONSUME_DEFERRED**.
WO-JUDGMENT-VALIDATOR-001 is the designated consumer (will `json.load(srd_skills.json)` at import time).
No runtime consumer exists in the current codebase. This is expected and explicitly authorized by the WO dispatch.

### PM Acceptance Note 7 - DC parity confirmed

`ruling_validator.py` does NOT yet exist (WO-JUDGMENT-SHADOW-001 built `aidm/schemas/ruling_artifact.py` and `aidm/core/ruling_validator.py` — confirmed by `git ls-files aidm/core/ruling_validator.py`).

```
$ git ls-files aidm/core/ruling_validator.py
aidm/core/ruling_validator.py
```

Reading `ruling_validator.py` top section:
```python
_DC_MIN = 5
_DC_MAX = 40
```
Confirmed: `_DC_MIN=5`, `_DC_MAX=40` match `srd_dc_ranges.json` exactly. Parity CONFIRMED.

### Gate Results

| Gate | Description | Result |
|------|-------------|--------|
| SE-001 | srd_skills.json exists on disk | PASS |
| SE-002 | srd_skills.json contains >= 30 skill entries | PASS (49 entries) |
| SE-003 | Each skill entry has exactly the 5 required keys | PASS |
| SE-004 | "spellcraft" present with ability="int" and trained_only=True | PASS |
| SE-005 | srd_dc_ranges.json exists on disk | PASS |
| SE-006 | dc_min=5 and dc_max=40 | PASS |
| SE-007 | Valid JSON; loads as list not dict | PASS |
| SE-008 | Two runs produce byte-identical output (idempotency) | PASS |

**Total: 8/8 PASS. 0 new regressions.**

### PM Acceptance Notes Confirmation

| # | Note | Status | Evidence |
|---|------|--------|----------|
| 1 | Actual JSON structure documented | CONFIRMED | Source is LIST not dict; key→ability, armorcheck→armor_check_penalty, trained→trained_only. Field discrepancy vs spec template documented above. |
| 2 | Skill count in output | CONFIRMED | 49 skills. SE-002 PASS. |
| 3 | Spellcraft spot-check | CONFIRMED | ability="int", trained_only=true, synergy=["use_magic_device"]. JSON snippet above. |
| 4 | sort_keys=True confirmed | CONFIRMED | dc_max < dc_min < source — alphabetical. json.dumps(..., sort_keys=True) at extract script line 58. |
| 5 | .gitignore for phb_source/ | CONFIRMED | Pre-existing entry at .gitignore line 59. phb_source/skills.json not committed. |
| 6 | CONSUME_DEFERRED explicit | CONFIRMED | srd_skills.json + srd_dc_ranges.json are CONSUME_DEFERRED. Consumer: WO-JUDGMENT-VALIDATOR-001. |
| 7 | DC parity confirmed | CONFIRMED | ruling_validator.py exists (from WO-JUDGMENT-SHADOW-001). _DC_MIN=5, _DC_MAX=40 match dc_min/dc_max in srd_dc_ranges.json. |

### ML Preflight Checklist

| Check | ID | Status | Notes |
|-------|----|--------|-------|
| Gap verified before writing | ML-001 | PASS | Grepped aidm/data/ — no srd_skills.json or srd_dc_ranges.json existed. Confirmed aidm/data/ dir exists (other data files present). |
| Consume-site verified end-to-end | ML-002 | PASS | CONSUME_DEFERRED per WO spec. Consumer: WO-JUDGMENT-VALIDATOR-001. Documented in debrief. |
| No ghost targets | ML-003 | PASS | Rule 15c: both output files confirmed absent before extraction. |
| Dispatch parity checked | ML-004 | PASS | Single output path. DC bounds in srd_dc_ranges.json confirmed to match ruling_validator.py (_DC_MIN=5, _DC_MAX=40). |
| Coverage map update | ML-005 | PASS | Phase 2 Data Layer section added to ENGINE_COVERAGE_MAP.md with SRD-DATA-EXTRACT row. |
| Commit before debrief | ML-006 | PASS | Commit 70e0509 precedes this debrief. |
| PM Acceptance Notes addressed | ML-007 | PASS | All 7 notes confirmed above. |
| Source present before WO start | ML-008 | PASS | Source fetched from confirmed URL before extraction. phb_source/skills.json verified: 49 entries. |

### Consumption Chain

| Layer | Location | Action |
|-------|----------|--------|
| Extract | `scripts/extract_srd_data.py` | Reads phb_source/skills.json -> writes srd_skills.json + srd_dc_ranges.json |
| Static data | `aidm/data/srd_skills.json` | 49 PHB skills, sorted by name |
| DC constants | `aidm/data/srd_dc_ranges.json` | dc_min=5, dc_max=40, matches ruling_validator.py constants |
| Consumer WO | WO-JUDGMENT-VALIDATOR-001 (not yet dispatched) | Will json.load(srd_skills.json) at import time |
| Test | SE-001..SE-008 |

**CONSUME_DEFERRED:** No runtime consumer exists. WO-JUDGMENT-VALIDATOR-001 is the designated consumer. Explicitly authorized.

---

## Pass 2 - PM Summary

Data-only WO. `scripts/extract_srd_data.py` downloads zellfaze-zz/dnd-generator phb/skills.json (CC0, LIST structure — spec template assumed dict, adapted without issue), normalizes 49 skill entries to canonical `{name, ability, trained_only, armor_check_penalty, synergy}` format (sorted alphabetically, sort_keys=True), writes `aidm/data/srd_skills.json`. `aidm/data/srd_dc_ranges.json` (dc_min=5, dc_max=40, PHB p.65) matches ruling_validator.py constants confirmed. phb_source/ gitignored (pre-existing). Zero engine wiring. CONSUME_DEFERRED; WO-JUDGMENT-VALIDATOR-001 is designated consumer. 8/8 SE gates pass. 0 regressions.

---

## Pass 3 - Retrospective

### Key Investigation Findings

**Source structure discrepancy:** The WO spec's `extract_skills(raw: dict)` template used `raw.items()` iteration (assumes dict). Actual source is a **list of objects**. Adapted cleanly — `for entry in raw` instead of `for key, val in raw.items()`. Field name `key` (not `ability`) for ability score; `armorcheck` (not `armor_check`) for armor check penalty. Documented in debrief Pass 1 and in extraction script docstring.

**Psionic skills included:** Source includes 3 psionic-specific skills (Autohypnosis, Psicraft, Use Psionic Device). These are in the CC0 data. Included in srd_skills.json as-is — they do not affect PHB skill coverage. Control Shape also included (shifter skill). The judgment validator can filter by magic=true/psi=true if needed (those fields are NOT exported to srd_skills.json, but the skills themselves are present).

**ruling_validator.py confirmed:** WO-JUDGMENT-SHADOW-001 landed before this WO. `ruling_validator.py` exists and has `_DC_MIN=5, _DC_MAX=40`. DC parity confirmed.

### Discoveries

**FINDING-DATA-SRD-PSIONIC-SKILLS-001 (LOW, INFORMATIONAL)**
srd_skills.json includes 3 psionic skills (autohypnosis, psicraft, use_psionic_device) and control_shape. These are in the CC0 source. WO-JUDGMENT-VALIDATOR-001 may need to filter if 3.5e PHB-core-only skill coverage is required. No action needed now. Log for Phase 2 build awareness.

**FINDING-DATA-SRD-SPEAK-LANGUAGE-ABILITY-001 (LOW, INFORMATIONAL)**
Speak Language has `ability: ""` (empty string) in the source. This is correct — Speak Language is not a check-based skill (PHB p.82). Exported as-is. WO-JUDGMENT-VALIDATOR-001 should handle empty ability strings gracefully.

### Kernel Touches

None. Data extraction only. No engine, resolver, or schema changes.

### Coverage Map Update

Phase 2 Data Layer section added to `docs/ENGINE_COVERAGE_MAP.md`:

| Mechanic | Status | WO | Notes |
|----------|--------|----|-------|
| srd_skills.json + srd_dc_ranges.json | IMPLEMENTED | WO-DATA-SRD-EXTRACT-001 | Commit 70e0509; 49 skills CC0; dc_min/max PHB p.65 |
