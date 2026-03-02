# DEBRIEF: BATCH-AV-ENGINE-001

**Lifecycle:** ACTIONED
**Commit:** d7c7899
**WOs:** WO-ENGINE-STINKING-CLOUD-NAUSEATE-001 (SCN-001..008), WO-ENGINE-MASSIVE-DAMAGE-THRESHOLD-001 (MDT-001..008), WO-ENGINE-MANEUVER-DOCSTRING-FIX-001 (MDF-001..004)
**Gates:** 20/20 pass
**Suite:** pre-existing 4 failures in test_engine_massive_damage_rule_001_gate.py (spell-path massive_damage_check event naming — pre-existing, not caused by AV); 0 new regressions
**Verdict Review Class:** SELF-REVIEW (ghost target documented; threshold formula verified; docstring-only edit)

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-STINKING-CLOUD-NAUSEATE-001 — Ghost Target

**Ghost target status confirmed per Rule 15c.**

Grepping `spell_definitions.py` for stinking_cloud conditions_on_fail:
```
spell_definitions.py:1046  conditions_on_fail=("nauseated",),  # Nauseated 1d4+1 rounds
```

`conditions_on_fail=("nauseated",)` already present at `spell_definitions.py:1046`. No code change made.

Gate file `tests/test_engine_stinking_cloud_nauseate_001_gate.py` created new. 8/8 SCN gates pass.

**Consume-site verified (existing):**
- Write site: `spell_definitions.py:1046` — `conditions_on_fail=("nauseated",)` in SpellDefinition
- Read site: `spell_resolver.py:806-808` — `if not saved and spell.conditions_on_fail: conditions_applied.append((entity_id, condition))`
- Effect site: `play_loop.py:1325-1368` — `for entity_id, condition in resolution.conditions_applied` → emits `condition_applied` event with `payload["condition"]="nauseated"`
- Gate proof: SCN-003 — `condition_applied` event with `condition="nauseated"` fires when `conditions_applied=(("target_01","nauseated"),)` injected

---

### WO2: WO-ENGINE-MASSIVE-DAMAGE-THRESHOLD-001 — Genuine Gap

**Genuine gap confirmed. Code change made.**

**File: `aidm/core/play_loop.py`**

**Before (line 1227):**
```python
if damage >= 50:
```

**After (lines 1225-1227):**
```python
_md_entity_max_hp = entities[entity_id].get(EF.HP_MAX, 50)
_md_threshold = max(_md_entity_max_hp // 2, 50)
if damage >= _md_threshold:
```

`EF.HP_MAX` is the canonical max HP field. Default of `50` matches the floor when HP_MAX is unavailable.

**Threshold formula confirmed:** `max(entity_max_hp // 2, 50)` as required by PHB p.145.

**Pre-existing test note:** `test_engine_massive_damage_rule_001_gate.py` has 4 pre-existing failures (MD-001, MD-002, MD-006, MD-008). These check for `massive_damage_check` event in the spell path — but the spell path emits `save_rolled` (not `massive_damage_check`). This was already failing before AV. The new MDT gate tests correctly check for `save_rolled` events with `dc==15` and `save_type=="fortitude"`.

Gate file `tests/test_engine_massive_damage_threshold_001_gate.py` created new. 8/8 MDT gates pass.

**Key distinguishing cases proving formula (not static-50):**
- MDT-003: HP_MAX=120, damage=59 → threshold=60 → 59 < 60 → no save ✓
  (Static-50 would wrongly trigger: 59 >= 50)
- MDT-005: HP_MAX=120, damage=50 → threshold=60 → 50 < 60 → no save ✓
  (Static-50 would wrongly trigger: 50 >= 50)

---

### WO3: WO-ENGINE-MANEUVER-DOCSTRING-FIX-001 — Genuine Gap

**All 3 stale lines confirmed present. Code change made.**

**File: `aidm/schemas/maneuvers.py` (lines 12-16)**

**Before:**
```
DEGRADATIONS:
- Sunder: Narrative only (no persistent item damage)
- Disarm: No persistence (weapon "drops" but no state change)
- Grapple: Unidirectional condition only (defender gets Grappled, attacker unchanged)
- Overrun: Defender avoidance controlled by AI (not interactive)
```

**After:**
```
DEGRADATIONS:
- Sunder: IMPLEMENTED (PHB p.158)
- Disarm: IMPLEMENTED — sets EF.DISARMED on success (PHB p.155)
- Grapple: IMPLEMENTED — applies grappled (defender) + grappling (attacker) conditions (PHB p.155-156)
- Overrun: Defender avoidance controlled by AI (not interactive)
```

Gate file `tests/test_engine_maneuver_docstring_fix_001_gate.py` created new. 4/4 MDF gates pass.

---

## PM Acceptance Notes Responses

### WO1:
- **File:line for stinking_cloud definition — which file post-SDD:** `spell_definitions.py:1046` — main `spell_definitions.py`, not ext file.
- **Before/after:** Ghost target — field already present at `:1046`. No before state exists. `conditions_on_fail=("nauseated",)` was already correct.
- **save_type=FORT and duration_rounds unchanged:** Confirmed. `save_type=SaveType.FORT` (SCN-002 passes). `duration_rounds=1` unchanged.
- **SCN-003 result:** `condition_applied` event fires with `payload={"entity_id": "target_01", "condition": "nauseated", "source": "spell:Stinking Cloud", ...}` when `conditions_applied=(("target_01","nauseated"),)` injected. SCN-003 passes.
- **SPELL_REGISTRY count still 733:** Confirmed. SCN-007 passes with count=733.

### WO2:
- **Threshold computation line (file:line):** `play_loop.py:1225-1226` — `_md_entity_max_hp = entities[entity_id].get(EF.HP_MAX, 50)` and `_md_threshold = max(_md_entity_max_hp // 2, 50)`. Not a bare `50` literal.
- **Fix required:** Yes — pre-fix was `if damage >= 50:` (static). Fixed to dynamic threshold.
- **Before:** `if damage >= 50:`
- **After:** `_md_entity_max_hp = ...; _md_threshold = max(_md_entity_max_hp // 2, 50); if damage >= _md_threshold:`
- **MDT-003 result:** HP=120, damage=59, threshold=60 → `_massive_damage_saves(events)` is empty (no `save_rolled` with dc=15). Pass.
- **MDT-005 result:** HP=120, damage=50, threshold=60 → no `save_rolled` with dc=15. Pass. (Static-50 would have fired.)
- **SPH save path (resolve_save DC=15) unchanged:** Confirmed. The block after the threshold check is identical to pre-AV. MDT-006 confirms DC=15.

### WO3:
- **Before/after of maneuvers.py:12-17:** Shown above in Pass 1 WO3 section.
- **MDF-001..003 pass:** All 3 pass. Stale strings `"Narrative only"`, `"No persistence"`, `"Unidirectional condition only"` absent from module docstring.

---

## Pass 2 — PM Summary (100 words)

WO1 ghost target: `conditions_on_fail=("nauseated",)` already at `spell_definitions.py:1046`. Gate tests verify existing state (SCN-003 confirms condition_applied fires on failed save; SCN-007 confirms registry count=733). WO2 closes genuine gap: static `50` threshold replaced with `max(entity_max_hp // 2, 50)` at `play_loop.py:1225-1227` — MDT-003 and MDT-005 prove formula correctness (HP=120 entity, damage<60 correctly not triggered). Note: 4 pre-existing failures in old MD rule gate (wrong event name for spell path; pre-AV). WO3 closes docstring drift: 3 stale lines corrected in `maneuvers.py:12-16`. 20/20 gates pass. 0 new regressions.

---

## Pass 3 — Retrospective

**Out-of-scope findings:**
- FINDING-ENGINE-MASSIVE-DAMAGE-SPELL-PATH-EVENT-NAME-001 (MEDIUM): `test_engine_massive_damage_rule_001_gate.py` MD-001/MD-002 check for `massive_damage_check` event in spell path, but spell path emits `save_rolled`. These 4 tests were already failing before AV. The old gate predates the SPH path (Batch AT). The new MDT tests (AV) use the correct event. Root cause: original MD gate was written for attack path; spell path uses different event. A future WO should fix or retire the stale MD-001/MD-002/MD-006/MD-008 gates.

**Ghost target process note:**
- WO1 was a complete ghost: `conditions_on_fail=("nauseated",)` already present. Verified per Rule 15c before writing any code.
- WO2 was a genuine gap: static `50` confirmed via grep before applying fix.
- WO3 was a genuine gap: all 3 stale strings confirmed via file read before applying fix.

**Test infrastructure note:**
- `_inject_spell_damage()` requires `EF.CASTER_CLASS: "wizard"` + `EF.SPELLS_PREPARED` (not `EF.SPELLS_KNOWN`). Sorcerer casters require `EF.SPELLS_KNOWN`. Initial SCN test used `sorcerer` + `SPELLS_PREPARED` → `spell_not_known` abort. Fixed to `wizard` + `SPELLS_PREPARED`.
- `TurnResult` uses `world_state` attribute (not `updated_state`). Fixed in MDT helper.
- `feat_resolver.FEAT_REGISTRY` has 109 entries; `feat_definitions.FEAT_REGISTRY` has 66. MDF-004 uses `feat_resolver` to match project-wide registry count.

**Kernel touches:**
- This WO touches KERNEL-02 (Spell System) — stinking_cloud conditions_on_fail verified; conditions_applied path confirmed end-to-end.
- This WO touches KERNEL-01 (Combat Core) — massive damage threshold formula corrected from static-50 to max(hp//2, 50).

---

## Radar — Findings

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| FINDING-ENGINE-MASSIVE-DAMAGE-THRESHOLD-HALF-HP-001 | Massive damage threshold was static 50, not max(hp//2, 50) | MEDIUM | CLOSED |
| FINDING-ENGINE-SPELL-DEF-STINKING-CLOUD-NAUSEATE-001 | stinking_cloud conditions_on_fail missing | MEDIUM | CLOSED (ghost target — was already present) |
| FINDING-ENGINE-MANEUVER-SCHEMA-DOCSTRING-DRIFT-001 | maneuvers.py docstring had 3 stale degradation lines | LOW | CLOSED |
| FINDING-ENGINE-MASSIVE-DAMAGE-SPELL-PATH-EVENT-NAME-001 | Old MD gate checks for massive_damage_check event; spell path emits save_rolled | LOW | OPEN — recommend future WO to retire/fix stale MD-001/002/006/008 gates |

---

## Coverage Map Updates

**Updated rows (`docs/ENGINE_COVERAGE_MAP.md`):**
- Massive damage row (line 69): threshold note added — `max(entity_max_hp // 2, 50)` formula confirmed. MDT-001..008 gate reference added. Batch AV reference added.
- stinking_cloud conditions_on_fail: NEW ROW added → IMPLEMENTED. Ghost target note. SCN-001..008. Batch AV.

---

## ML Preflight Checklist

| Check | WO1 (SCN) | WO2 (MDT) | WO3 (MDF) |
|-------|-----------|-----------|-----------|
| ML-001: No bare string literals (EF.* used) | conditions_on_fail is SpellDefinition field (not EF.*) — acceptable schema field | EF.HP_MAX used; threshold is int math, no bare string | N/A — docstring only |
| ML-002: All call sites identified | One write site (spell_definitions.py:1046), one consume site (spell_resolver:806-808), one event site (play_loop:1325-1368) | Single site: play_loop.py:1225-1227 massive damage block | Single site: maneuvers.py:12-16 docstring |
| ML-003: No float in deterministic path | No dice math | `max(hp//2, 50)` uses integer division | N/A |
| ML-004: json.dumps sort_keys if any | N/A | N/A | N/A |
| ML-005: No WorldState mutation in resolver | Ghost target — no code written | play_loop threshold check does not mutate WS before save; save returns events | N/A |
| ML-006: Coverage map updated | ✅ stinking_cloud conditions_on_fail row added | ✅ Massive damage row threshold formula confirmed | N/A (docstring only) |

---

## Consume-Site Confirmation

**WO1 (SCN) — Ghost Target:**
- Write site: `spell_definitions.py:1046` — `conditions_on_fail=("nauseated",)` in stinking_cloud SpellDefinition
- Read site: `spell_resolver.py:806-808` — condition appended to `conditions_applied` when not saved and `spell.conditions_on_fail`
- Effect site: `play_loop.py:1325-1368` — `condition_applied` event emitted for each `(entity_id, condition)` in `resolution.conditions_applied`
- Gate proof: SCN-003 — `condition_applied` with `condition="nauseated"` fires; SCN-004 — does not fire when `conditions_applied=()` (save passed)

**WO2 (MDT):**
- Write site: `play_loop.py:1225-1226` — `_md_entity_max_hp = entities[entity_id].get(EF.HP_MAX, 50)` and `_md_threshold = max(_md_entity_max_hp // 2, 50)`
- Read site: `play_loop.py:1227` — `if damage >= _md_threshold:`
- Effect: High-HP entities (HP > 100) trigger massive damage save at half-HP threshold, not at static 50
- Gate proof: MDT-003 (HP=120, damage=59 → no save) and MDT-005 (HP=120, damage=50 → no save) prove formula

**Post-AV gate count:** 1,658 (post-AU) + 8 (SCN) + 8 (MDT) + 4 (MDF) = **1,678**
**Sweep:** 2/5.
