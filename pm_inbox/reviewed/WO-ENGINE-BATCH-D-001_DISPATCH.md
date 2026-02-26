# ENGINE BATCH D — DISPATCH PACKET
## WO-ENGINE-SILENT-SPELL-001 + WO-ENGINE-STILL-SPELL-001 + WO-ENGINE-MONK-WIS-AC-001 + WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001

**Batch ID:** ENGINE BATCH D
**Dispatch date:** 2026-02-26
**Dispatched by:** Slate (PM)
**Authorized by:** Thunder (PO)
**Dispatch cap:** 4 WOs (confirmed)
**Pre-existing failures:** 23 (do not treat as regressions)
**Regression model:** Batch model — each builder runs their own WO gate only. Full regression runs after all four land.

---

## BATCH OVERVIEW

| WO ID | Feature | PHB Ref | Gate ID | Min Tests |
|-------|---------|---------|---------|-----------|
| WO-ENGINE-SILENT-SPELL-001 | Silent Spell metamagic | PHB p.98 | ENGINE-SILENT-SPELL | 8 |
| WO-ENGINE-STILL-SPELL-001 | Still Spell metamagic (ASF bypass) | PHB p.100 | ENGINE-STILL-SPELL | 8 |
| WO-ENGINE-MONK-WIS-AC-001 | Monk WIS bonus to AC (runtime) | PHB p.41 | ENGINE-MONK-WIS-AC | 8 |
| WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001 | Barbarian Fast Movement (+10 ft) | PHB p.26 | ENGINE-BARBARIAN-FAST-MOVEMENT | 8 |

**No file conflicts across WOs in this batch.** Each WO targets distinct resolvers. All four are independently executable.

---

---

# WO-ENGINE-SILENT-SPELL-001
## Silent Spell — Verbal Component Field + Slot Cost Enforcement

**Priority:** MEDIUM
**Classification:** FEATURE
**Gate ID:** ENGINE-SILENT-SPELL
**Minimum gate tests:** 8
**Status:** READY-TO-DISPATCH

---

## Target Lock

Add `has_verbal: bool = True` to `SpellDefinition`, wire `"Silent Spell"` feat validation through `metamagic_resolver.py`, and apply the +1 slot cost when the metamagic is declared.

**Scope:** This WO does NOT implement silence-zone enforcement (no "verbal component prohibited" condition exists yet — that is a future enforcement gap, not a current blocker). This WO establishes the data field and slot cost so Silent Spell is mechanically registered and correctly priced. Future silence-zone enforcement will read `has_verbal` when that condition layer lands.

PHB p.98: A silent spell can be cast in areas of magical silence or when the caster cannot speak. Slot cost: +1 spell level.

---

## Binary Decisions

1. **`has_verbal` default:** `True`. All spells have a verbal component unless explicitly set to False. Mirror the `has_somatic` pattern exactly.
2. **Slot cost enforcement:** Wire Silent Spell through the existing `METAMAGIC_SLOT_COST` dict in `metamagic_resolver.py`. Entry: `"silent": 1`. Feat name: `"Silent Spell"`.
3. **V-only spells that already have `has_somatic=False`:** Also mark `has_verbal=False` only if the spell is described as having no verbal component in the PHB. Do NOT add `has_verbal=False` to existing spells speculatively — only add it if you are certain from the spell registry.
4. **No silence-zone behavioral change in this WO.** The `has_verbal` field is written; it is not read for enforcement. Add a comment to the field: `# Future: checked by silence-zone enforcement when that condition layer lands.`

---

## Contract Spec

### Inputs
- `SpellCastIntent.metamagic` list containing `"silent"` (same pattern as `"empower"`, `"quicken"`, etc.)
- `"Silent Spell"` in caster's `EF.FEATS`

### Outputs
- `validate_metamagic()` returns error if `"silent"` declared but `"Silent Spell"` not in feats
- Spell slot consumed at `spell.level + 1` when `"silent"` in metamagic (via existing slot cost machinery)
- No behavioral change to the spell resolution itself

### New field on SpellDefinition
```python
has_verbal: bool = True
# PHB: True if spell has a verbal component.
# Future: checked by silence-zone enforcement when that condition layer lands.
# Silent Spell metamagic suppresses this component (PHB p.98), allowing casting
# in areas of magical silence or when speech is impossible.
```

---

## Implementation Plan

**Step 1 — `aidm/core/spell_resolver.py`**
- Add `has_verbal: bool = True` to the `SpellDefinition` dataclass, immediately after `has_somatic: bool = True` (line ~174).
- Add docstring comment as specified in Contract Spec above.

**Step 2 — `aidm/core/metamagic_resolver.py`**
- Add `"silent": 1` to `METAMAGIC_SLOT_COST` dict.
- Add `"silent": "Silent Spell"` to `_FEAT_NAMES` dict.
- Add `"silent"` to `_VALID_METAMAGIC` set (or equivalent validation set).
- Confirm `validate_metamagic()` now covers `"silent"` via the existing feat check loop — no new logic required.

**Step 3 — Gate tests (`tests/test_engine_silent_spell_001_gate.py`)**

Write 8 gate tests covering:
- SS-001: Caster with Silent Spell feat + `"silent"` in metamagic → `validate_metamagic()` returns no error
- SS-002: Caster without Silent Spell feat + `"silent"` in metamagic → `validate_metamagic()` returns `"missing_metamagic_feat"`
- SS-003: `"silent"` in metamagic → slot cost = `spell.level + 1` (verify slot consumed at adjusted level)
- SS-004: `"silent"` combined with another metamagic → combined slot cost correct (e.g., silent + empower = +1+2 = +3)
- SS-005: `SpellDefinition` with `has_verbal=False` can be constructed and read back correctly
- SS-006: Default `SpellDefinition` has `has_verbal=True`
- SS-007: `"silent"` NOT in metamagic, spell cast normally → slot cost unaffected
- SS-008: `validate_metamagic()` with `"silent"` and caster feats list is case-handled (exact feat name match)

---

## Files to Modify

- `aidm/core/spell_resolver.py` — add `has_verbal` field to `SpellDefinition` dataclass (~line 174)
- `aidm/core/metamagic_resolver.py` — add `"silent"` to slot cost dict, feat name dict, valid set
- `tests/test_engine_silent_spell_001_gate.py` — NEW gate test file (8 tests)

**Do NOT modify:**
- `aidm/data/spell_definitions.py` — do not speculatively add `has_verbal=False` to any existing spells
- `aidm/runtime/session_orchestrator.py` — no orchestrator changes in this WO
- `aidm/core/play_loop.py` — no casting path changes in this WO

---

## Integration Seams

**`SpellDefinition` dataclass** (`aidm/core/spell_resolver.py`):
```python
@dataclass(frozen=True)
class SpellDefinition:
    # ... existing fields ...
    has_somatic: bool = True
    has_verbal: bool = True   # <-- INSERT AFTER has_somatic
```

**`METAMAGIC_SLOT_COST` dict** (`aidm/core/metamagic_resolver.py`):
```python
METAMAGIC_SLOT_COST: Dict[str, int] = {
    "empower": 2,
    "maximize": 3,
    "extend": 1,
    "heighten": 0,
    "quicken": 4,
    "silent": 1,   # <-- ADD
    "still": 1,    # <-- ADD (for Still Spell WO; add both together)
}
```

**`_FEAT_NAMES` dict** (`aidm/core/metamagic_resolver.py`):
```python
_FEAT_NAMES: Dict[str, str] = {
    # ... existing ...
    "silent": "Silent Spell",   # <-- ADD
    "still": "Still Spell",     # <-- ADD (for Still Spell WO)
}
```

> **Note:** Both Silent Spell and Still Spell modify `metamagic_resolver.py`. These two WOs may be dispatched to the same builder or different builders — if different builders, the builder for this WO adds `"silent"` entries only, and does NOT add `"still"` entries (that belongs to WO-ENGINE-STILL-SPELL-001). Coordinate to avoid merge conflicts on this file.

---

## Assumptions to Validate

Before writing code, confirm:
1. `metamagic_resolver.py` does NOT already have `"silent"` in `METAMAGIC_SLOT_COST`. If it does, gate tests may already pass — validate existing behavior and report.
2. `SpellDefinition` does NOT already have `has_verbal`. If it does, adjust scope accordingly.
3. The existing `validate_metamagic()` loop covers `_VALID_METAMAGIC` check — confirm the set name and how new entries are validated.

---

## Regression

**Batch WO:** Run your WO-specific gate only: `pytest tests/test_engine_silent_spell_001_gate.py`. File your debrief on that result. A dedicated regression agent runs the full suite after all Batch D WOs land.

If gate produces unexpected failures: fix once, re-run once. If still failing after one fix attempt, record the failure in your debrief and stop. Do not loop.

---

## Scope Boundaries

- Do NOT implement silence-zone enforcement (no "verbal prohibited" condition layer exists)
- Do NOT modify `aidm/data/spell_definitions.py` unless certain a specific spell has no verbal component per PHB
- Do NOT touch ASF check logic (belongs to Still Spell WO)
- Do NOT modify any resolver outside `spell_resolver.py` and `metamagic_resolver.py`

---

## Debrief Required

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-SILENT-SPELL-001.md`

**Pass 1:** Per-file breakdown (files read, files modified, line ranges changed, key decisions made).
**Pass 2:** PM summary ≤100 words.
**Pass 3:** Retrospective — drift caught, patterns noticed, open questions.
**Radar:** Any coupling risks, silent gaps, or findings outside the WO scope.

Missing debrief or missing Radar → REJECT.

**Audio Cue (mandatory):**
```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

---

# WO-ENGINE-STILL-SPELL-001
## Still Spell — ASF Bypass via Somatic Suppression

**Priority:** MEDIUM
**Classification:** FEATURE
**Gate ID:** ENGINE-STILL-SPELL
**Minimum gate tests:** 8
**Status:** READY-TO-DISPATCH

---

## Target Lock

Wire `"Still Spell"` feat validation through `metamagic_resolver.py` and enforce the ASF bypass: when `"still"` is in the spell's metamagic list, the caster's `has_somatic` component is treated as absent — arcane spell failure check is skipped entirely for that cast. Slot cost: +1 spell level.

PHB p.100: A still spell can be cast while wearing armor without any chance of arcane spell failure. The spell uses up a spell slot one level higher.

---

## Binary Decisions

1. **ASF bypass location:** The ASF check currently lives in `aidm/core/play_loop.py` (wired by WO-ENGINE-ARCANE-SPELL-FAILURE-001). It checks `spell.has_somatic` before rolling. Bypass by also checking `"still" in intent.metamagic` at the same guard. If either `not spell.has_somatic` OR `"still" in intent.metamagic`, skip ASF roll.
2. **Slot cost:** Wire through `METAMAGIC_SLOT_COST["still"] = 1` in `metamagic_resolver.py` (same dict as Silent Spell — coordinate if separate builders).
3. **Feat validation:** `validate_metamagic()` already handles `"still"` via the feat-name loop once `"still": "Still Spell"` is in `_FEAT_NAMES`. No new validation logic needed.
4. **Divine casters:** Divine casters already bypass ASF entirely. The Still Spell check is only meaningful for arcane casters. The existing ASF guard already handles this — Still Spell inserts before that guard, so divine casters are unaffected.

---

## Contract Spec

### Inputs
- `SpellCastIntent.metamagic` list containing `"still"`
- `"Still Spell"` in caster's `EF.FEATS`

### Outputs
- `validate_metamagic()` returns error if `"still"` declared but `"Still Spell"` not in feats
- Spell slot consumed at `spell.level + 1`
- ASF roll skipped when `"still"` in `intent.metamagic` (even if `spell.has_somatic == True`)
- Spell resolves normally after bypass

---

## Implementation Plan

**Step 1 — `aidm/core/metamagic_resolver.py`**
- Add `"still": 1` to `METAMAGIC_SLOT_COST`.
- Add `"still": "Still Spell"` to `_FEAT_NAMES`.
- Add `"still"` to `_VALID_METAMAGIC` set.

> If WO-ENGINE-SILENT-SPELL-001 builder already added these entries (same file, same batch), confirm they exist and skip. Do not double-add.

**Step 2 — `aidm/core/play_loop.py` — ASF bypass**

Find the ASF check block (inserted by WO-ENGINE-ARCANE-SPELL-FAILURE-001). It checks `spell.has_somatic`. Extend the condition to also skip when `"still"` is in the metamagic list:

```python
# WO-ENGINE-ARCANE-SPELL-FAILURE-001: ASF check
# WO-ENGINE-STILL-SPELL-001: Still Spell suppresses somatic component → bypass ASF
_is_still = "still" in getattr(intent, "metamagic", ())
if spell.has_somatic and not _is_still and is_arcane(caster):
    # existing ASF roll logic ...
```

Find this block by searching for `has_somatic` in `play_loop.py`. The ASF check block is the only usage site.

**Step 3 — Gate tests (`tests/test_engine_still_spell_001_gate.py`)**

Write 8 gate tests covering:
- ST-001: Arcane caster with Still Spell feat + `"still"` in metamagic + high ASF% → ASF roll skipped, spell resolves
- ST-002: Arcane caster without Still Spell feat + `"still"` in metamagic → `validate_metamagic()` error
- ST-003: `"still"` in metamagic → slot cost = `spell.level + 1`
- ST-004: Arcane caster with Still Spell, `has_somatic=False` spell (V-only) + `"still"` → ASF already skipped (no double-skip error)
- ST-005: Arcane caster, NO `"still"`, high ASF% → ASF roll still fires (regression: Still Spell does not affect normal casts)
- ST-006: Divine caster with `"still"` in metamagic → ASF already skipped by divine bypass; Still Spell doesn't break divine path
- ST-007: `"still"` + `"silent"` combined → combined slot cost = +2
- ST-008: `validate_metamagic()` with `"still"` and valid feat → no error returned

---

## Files to Modify

- `aidm/core/metamagic_resolver.py` — add `"still"` to slot cost dict, feat name dict, valid set
- `aidm/core/play_loop.py` — extend ASF check to bypass when `"still"` in metamagic
- `tests/test_engine_still_spell_001_gate.py` — NEW gate test file (8 tests)

**Do NOT modify:**
- `aidm/core/spell_resolver.py` — no `SpellDefinition` changes needed for Still Spell
- Any resolver other than the ASF check in `play_loop.py`

---

## Integration Seams

**ASF check in `play_loop.py`** — locate by searching `has_somatic`. Current form (post WO-ENGINE-ARCANE-SPELL-FAILURE-001):
```python
if spell.has_somatic and is_arcane(caster):
    # d100 ASF roll ...
```
Modified form:
```python
_is_still = "still" in getattr(intent, "metamagic", ())
if spell.has_somatic and not _is_still and is_arcane(caster):
    # d100 ASF roll ...
```

**Event constructor signature** (if emitting events):
```python
Event(event_id=str(uuid4()), event_type="...", payload={...})
```
Use `event_id=`, `event_type=`, `payload=` — NOT `id=`, `type=`, `data=`.

---

## Assumptions to Validate

1. Locate the ASF check in `play_loop.py` by searching `has_somatic`. Confirm it exists and matches the pattern described above before writing the bypass.
2. Confirm `metamagic_resolver.py` does NOT already have `"still"` entries. If Silent Spell builder ran first, they may already be present.
3. Confirm `getattr(intent, "metamagic", ())` is the safe access pattern for metamagic on `SpellCastIntent` (some intents may use a tuple, not a list — use `in` operator either way).

---

## Regression

**Batch WO:** Run your WO-specific gate only: `pytest tests/test_engine_still_spell_001_gate.py`. File your debrief on that result. A dedicated regression agent runs the full suite after all Batch D WOs land.

If gate produces unexpected failures: fix once, re-run once. If still failing, record the failure in your debrief and stop. Do not loop.

---

## Scope Boundaries

- Do NOT modify the ASF check for any path other than the `"still"` metamagic check
- Do NOT add `has_verbal` to `SpellDefinition` (belongs to Silent Spell WO)
- Do NOT touch silence-zone logic
- Do NOT modify `spell_resolver.py`

---

## Debrief Required

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-STILL-SPELL-001.md`

**Pass 1:** Per-file breakdown. **Pass 2:** PM summary ≤100 words. **Pass 3:** Retrospective + Radar.

Missing debrief or missing Radar → REJECT.

**Audio Cue (mandatory):**
```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

---

# WO-ENGINE-MONK-WIS-AC-001
## Monk WIS Bonus to AC — Runtime Enforcement

**Priority:** MEDIUM
**Classification:** FEATURE
**Gate ID:** ENGINE-MONK-WIS-AC
**Minimum gate tests:** 8
**Status:** READY-TO-DISPATCH

---

## Target Lock

The Monk's WIS bonus to AC is currently baked into `EF.AC` at chargen only (`builder.py:_assign_starting_equipment` — `if kit.get("wis_to_ac"): ac += wis_mod`). This means WIS changes at runtime (ability damage, drain, temporary bonuses) do not update the monk's AC. This WO adds runtime WIS-to-AC enforcement in the attack resolver so the correct AC is computed dynamically.

PHB p.41: When unarmored and unencumbered, a monk adds her Wisdom bonus (if any) to her AC. This bonus to AC applies even against touch attacks or when the monk is flat-footed.

---

## Binary Decisions

1. **Enforcement site:** `aidm/core/attack_resolver.py` — at the `target_ac` assembly line (currently ~line 424). Add a monk WIS check to the AC computation. Do NOT modify chargen — the baked-in value remains as the base; this WO adds a dynamic correction.
2. **Correction approach:** At runtime, for a monk target, the baked-in `EF.AC` includes WIS at chargen. If WIS changes during play, `EF.WIS_MOD` will differ from what was baked in at chargen. The guard checks: `if monk and unarmored → add WIS_MOD to target_ac`. Because WIS is already in base AC, this would double-count. **Correct approach:** Add `EF.MONK_WIS_AC_BONUS` field (Int, default 0) to entity_fields. Chargen sets it to `wis_mod` when writing monk AC. Runtime reads it and adds it to the resolver's AC stack — not as a double-count, but as a tracked, mutable field. If chargen already bakes WIS into `EF.AC`, then `EF.MONK_WIS_AC_BONUS` must be subtracted from base `EF.AC` at chargen and instead applied at runtime. **PM directive: verify the chargen calculation before committing to approach.** If chargen already stores a clean `10 + DEX + armor` (no WIS) base and adds WIS separately, the runtime add is clean. If WIS is fused into `EF.AC`, the builder must use the separate field approach.
3. **Armor/encumbrance condition:** Monk WIS to AC applies only when unarmored and unencumbered (PHB p.41). Unarmored = no armor in `EF.EQUIPMENT` (or `EF.ARMOR_AC_BONUS == 0`). Encumbrance: light load only. Check both conditions before applying.
4. **Touch attacks:** WIS bonus applies even against touch attacks. The attack resolver must apply it in the touch AC path as well as normal AC. Locate where touch AC is computed and include the monk WIS bonus there too.

---

## Contract Spec

### Inputs
- Target entity with `EF.CLASS_LEVELS["monk"] >= 1`
- `EF.WIS_MOD` on entity
- `EF.ARMOR_AC_BONUS` == 0 (unarmored) AND encumbrance light or less

### Outputs
- `target_ac` in resolver includes WIS bonus for qualifying monks
- WIS bonus applies to touch AC
- WIS bonus is NOT applied when monk wears armor
- WIS bonus is NOT applied when monk is heavily encumbered

### New EF constant
```python
MONK_WIS_AC_BONUS = "monk_wis_ac_bonus"
# int: WIS modifier applied to monk AC at runtime (PHB p.41).
# 0 for non-monks. Set at chargen for monks. Read in attack_resolver.
# Applies only when unarmored and unencumbered (light load).
```

---

## Implementation Plan

**Step 1 — `aidm/schemas/entity_fields.py`**
- Add `MONK_WIS_AC_BONUS = "monk_wis_ac_bonus"` constant.

**Step 2 — Verify chargen approach (`aidm/chargen/builder.py`)**
- Read `_assign_starting_equipment()` to confirm whether `EF.AC` = `10 + DEX + armor` (no WIS) or `10 + DEX + armor + WIS`.
- **If WIS is already baked into `EF.AC`:** Set `entity[EF.MONK_WIS_AC_BONUS] = wis_mod` at chargen AND subtract WIS from the `EF.AC` base so it is not double-counted at runtime. Net result: `EF.AC` = `10 + DEX + armor`, `EF.MONK_WIS_AC_BONUS` = wis_mod.
- **If WIS is NOT in `EF.AC`:** Set `entity[EF.MONK_WIS_AC_BONUS] = wis_mod` and leave `EF.AC` as is.
- Set `EF.MONK_WIS_AC_BONUS = 0` for all non-monks.

**Step 3 — `aidm/core/attack_resolver.py`**
- At the `target_ac` assembly block, add:
```python
# WO-ENGINE-MONK-WIS-AC-001: Monk WIS bonus to AC (PHB p.41) — applies unarmored + light load
_monk_wis_ac = 0
_monk_level = target.get(EF.CLASS_LEVELS, {}).get("monk", 0)
if _monk_level >= 1:
    _armor_bonus = target.get(EF.ARMOR_AC_BONUS, 0)
    # Unarmored check: no armor bonus means no armor worn
    if _armor_bonus == 0:
        _monk_wis_ac = target.get(EF.MONK_WIS_AC_BONUS, 0)
        # Note: encumbrance check deferred to encumbrance system integration;
        # heavy encumbrance stripping the bonus is a future enforcement point.
```
- Add `_monk_wis_ac` to the `target_ac` sum.
- Apply the same `_monk_wis_ac` bonus in the touch AC path if touch AC is computed separately. Search `attack_resolver.py` for touch AC logic and include there.

> **Note on encumbrance deferral:** Full encumbrance check at runtime requires reading entity weight/carrying capacity, which is not currently in the attack resolver's hot path. For this WO, enforce unarmored condition (armor bonus == 0); defer heavy encumbrance stripping to a follow-up finding if needed. Document this in the debrief.

**Step 4 — Gate tests (`tests/test_engine_monk_wis_ac_001_gate.py`)**

Write 8 gate tests covering:
- MW-001: Monk (level 1+), unarmored, WIS 16 (+3 mod) → attack resolver applies +3 to target AC
- MW-002: Monk, unarmored, WIS 10 (+0 mod) → no WIS bonus applied (no effect)
- MW-003: Monk wearing armor (ARMOR_AC_BONUS > 0) → WIS bonus NOT applied
- MW-004: Non-monk entity, WIS 18 → WIS bonus NOT applied to AC
- MW-005: Monk with WIS 16 targeted by touch attack → WIS bonus still applies
- MW-006: WIS damage reduces WIS_MOD at runtime → AC computed with updated WIS_MOD
- MW-007: Monk, unarmored → `EF.MONK_WIS_AC_BONUS` correctly set at chargen (chargen init test)
- MW-008: Multiclass monk/fighter, monk level ≥ 1, unarmored → WIS bonus applies

---

## Files to Modify

- `aidm/schemas/entity_fields.py` — add `MONK_WIS_AC_BONUS` constant
- `aidm/chargen/builder.py` — set `EF.MONK_WIS_AC_BONUS` for monk entities; adjust `EF.AC` base if needed (verify first)
- `aidm/core/attack_resolver.py` — add WIS bonus to `target_ac` assembly; apply to touch AC path
- `tests/test_engine_monk_wis_ac_001_gate.py` — NEW gate test file (8 tests)

**Do NOT modify:**
- `aidm/core/full_attack_resolver.py` — unless touch AC is computed there and not in attack_resolver (check first)
- Any other resolver

---

## Integration Seams

**`EF.CLASS_LEVELS` pattern** (from Uncanny Dodge WO — confirmed canonical):
```python
class_levels = entity.get(EF.CLASS_LEVELS, {})
monk_level = class_levels.get("monk", 0)
```

**`target_ac` assembly in `attack_resolver.py`** (~line 424):
```python
target_ac = base_ac + condition_ac + cover_result.ac_bonus + dex_penalty + _defend_ac_total + _twd_ac_bonus + _ce_ac_bonus
```
Extend to:
```python
target_ac = base_ac + condition_ac + cover_result.ac_bonus + dex_penalty + _defend_ac_total + _twd_ac_bonus + _ce_ac_bonus + _monk_wis_ac
```

**Event constructor signature** (if emitting events):
```python
Event(event_id=str(uuid4()), event_type="...", payload={...})
```

---

## Assumptions to Validate

1. **Read `builder.py:_assign_starting_equipment()`** before writing any code. Confirm whether `EF.AC` contains WIS or not. The implementation plan branches on this. Do not guess.
2. Confirm `EF.ARMOR_AC_BONUS` exists as a field on entities (or find the equivalent field that indicates armor is worn). If it doesn't exist, use `EF.EQUIPMENT` to check for armor type.
3. Confirm touch AC is computed in `attack_resolver.py` and not in a separate file.

---

## Regression

**Batch WO:** Run your WO-specific gate only: `pytest tests/test_engine_monk_wis_ac_001_gate.py`. File your debrief on that result. A dedicated regression agent runs the full suite after all Batch D WOs land.

If gate produces unexpected failures: fix once, re-run once. If still failing, record the failure in your debrief and stop. Do not loop.

---

## Scope Boundaries

- Do NOT implement encumbrance-based WIS stripping — document as deferred finding
- Do NOT modify any other class feature WIS interaction (e.g., paladin CHA, ranger TWF)
- Do NOT touch `full_attack_resolver.py` unless you confirm touch AC is computed there

---

## Debrief Required

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-MONK-WIS-AC-001.md`

**Pass 1:** Per-file breakdown (MUST include chargen verification result — which branch you took). **Pass 2:** PM summary ≤100 words. **Pass 3:** Retrospective + Radar.

Missing debrief or missing Radar → REJECT.

**Audio Cue (mandatory):**
```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

---

# WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001
## Barbarian Fast Movement — +10 ft Speed Bonus (Unarmored)

**Priority:** MEDIUM
**Classification:** FEATURE
**Gate ID:** ENGINE-BARBARIAN-FAST-MOVEMENT
**Minimum gate tests:** 8
**Status:** READY-TO-DISPATCH

---

## Target Lock

Add the Barbarian's Fast Movement class feature: +10 ft to base speed when unarmored (or wearing light armor at most, per PHB — barbarians lose the bonus in medium or heavy armor). Wire the bonus into `movement_resolver.py` so it is applied when computing movement distance.

PHB p.26: A barbarian's base speed is faster than the norm for his race by +10 feet. This benefit applies only when the barbarian is wearing no armor, light armor, or medium armor (not heavy armor) and not carrying a heavy load.

> **PHB clarification:** The benefit applies in light and medium armor, NOT just unarmored. Barbarians lose it in heavy armor or under heavy load. This differs from the Monk WIS-to-AC restriction (unarmored only). Do not confuse the two.

---

## Binary Decisions

1. **Storage:** Add `EF.FAST_MOVEMENT_BONUS = "fast_movement_bonus"` to entity_fields. Set at chargen for barbarians. Read in movement resolver. Default 0 for non-barbarians.
2. **Application site:** `aidm/core/movement_resolver.py` — where `EF.BASE_SPEED` is read (`speed_ft = entity.get(EF.BASE_SPEED, 30)`). Add the bonus after reading base speed, conditioned on armor type.
3. **Armor condition:** Fast Movement applies in no armor, light armor, or medium armor. Blocked by heavy armor. Use `EF.ARMOR_TYPE` or equivalent field to check. If armor type field doesn't exist, check `EF.ARMOR_AC_BONUS` threshold (heavy armor typically gives +6 or more to AC; light/medium gives less — but this is fragile). Verify the correct field before implementing.
4. **Encumbrance condition:** Heavy load also blocks Fast Movement. Encumbrance is computed in `encumbrance.py`. Either call `get_load_tier()` inline or check if the load tier is already on the entity. Do not recalculate weight from scratch inside the movement resolver — call the existing utility.
5. **Chargen:** Set `entity[EF.FAST_MOVEMENT_BONUS] = 10` for barbarian entities. This is straightforward — wire after barbarian class detection in `builder.py`.

---

## Contract Spec

### Inputs
- Entity with `EF.CLASS_LEVELS["barbarian"] >= 1`
- `EF.FAST_MOVEMENT_BONUS` = 10 (set at chargen)
- Armor type: not heavy
- Load tier: not heavy

### Outputs
- `speed_ft` in movement resolver = `EF.BASE_SPEED + EF.FAST_MOVEMENT_BONUS` when conditions met
- Bonus NOT applied when heavy armor worn
- Bonus NOT applied when heavy load carried
- Encumbrance calculation still applied after bonus (encumbrance can reduce the expanded speed)

### New EF constants
```python
FAST_MOVEMENT_BONUS = "fast_movement_bonus"
# int: bonus feet added to base speed before encumbrance (PHB p.26).
# 10 for barbarians, 0 for all others.
# Applied only when NOT wearing heavy armor and NOT under heavy load.

ARMOR_TYPE = "armor_type"
# str: "none" | "light" | "medium" | "heavy"
# Set at chargen. Read for Fast Movement and similar conditionals.
# Add only if this constant does not already exist.
```

---

## Implementation Plan

**Step 1 — `aidm/schemas/entity_fields.py`**
- Add `FAST_MOVEMENT_BONUS = "fast_movement_bonus"`.
- Check if `ARMOR_TYPE` already exists. If not, add it. If it exists under a different name, use that name instead and do NOT add a duplicate.

**Step 2 — `aidm/chargen/builder.py`**
- Set `entity[EF.FAST_MOVEMENT_BONUS] = 10` for barbarian entities.
- Set `entity[EF.FAST_MOVEMENT_BONUS] = 0` for all other classes (or rely on `.get()` default of 0).
- Set `entity[EF.ARMOR_TYPE]` to the appropriate armor category at chargen if the field is new. `"none"` for no armor, `"light"` for light, `"medium"` for medium, `"heavy"` for heavy. If this field already exists in chargen, confirm it's set correctly.

**Step 3 — `aidm/core/movement_resolver.py`**
- Find `speed_ft = entity.get(EF.BASE_SPEED, 30)` (line ~220 in `build_full_move_intent`).
- After that line, add:
```python
# WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001: Fast Movement (PHB p.26)
# +10 ft for barbarians, blocked by heavy armor or heavy load
_fast_movement = entity.get(EF.FAST_MOVEMENT_BONUS, 0)
if _fast_movement > 0:
    _armor_type = entity.get(EF.ARMOR_TYPE, "none")
    if _armor_type != "heavy":
        # Encumbrance check: heavy load blocks Fast Movement
        # Use existing encumbrance utility rather than recalculating
        from aidm.core.encumbrance import get_load_tier, calculate_total_weight
        # Note: requires item_catalog; if not available in this context, defer to a simpler flag
        # If catalog not available: document as deferred and use armor check only for now
        speed_ft += _fast_movement
```
> **If item_catalog is not available in `movement_resolver.py`'s call context:** Apply the armor check only; document the load check as deferred in the debrief. Do not import catalog infrastructure that doesn't exist in this call path. File a finding for the load check gap.

**Step 4 — Gate tests (`tests/test_engine_barbarian_fast_movement_001_gate.py`)**

Write 8 gate tests covering:
- FM-001: Barbarian (level 1+), no armor → speed = `base_speed + 10`
- FM-002: Barbarian, light armor → speed = `base_speed + 10` (bonus still applies)
- FM-003: Barbarian, medium armor → speed = `base_speed + 10` (bonus still applies)
- FM-004: Barbarian, heavy armor → speed = `base_speed` only (bonus blocked)
- FM-005: Non-barbarian (fighter), no armor → speed = `base_speed` only (no Fast Movement)
- FM-006: Multiclass barbarian/fighter (barbarian ≥ 1), no armor → speed = `base_speed + 10`
- FM-007: `EF.FAST_MOVEMENT_BONUS` set to 10 at chargen for barbarian (chargen init test)
- FM-008: `EF.FAST_MOVEMENT_BONUS` set to 0 (or absent) at chargen for non-barbarian (chargen init test)

---

## Files to Modify

- `aidm/schemas/entity_fields.py` — add `FAST_MOVEMENT_BONUS` (and `ARMOR_TYPE` if missing)
- `aidm/chargen/builder.py` — set `EF.FAST_MOVEMENT_BONUS` for barbarian; set `EF.ARMOR_TYPE` if adding new field
- `aidm/core/movement_resolver.py` — apply speed bonus conditioned on armor type
- `tests/test_engine_barbarian_fast_movement_001_gate.py` — NEW gate test file (8 tests)

**Do NOT modify:**
- `aidm/core/encumbrance.py` — use existing utilities; do not modify encumbrance logic
- `aidm/core/attack_resolver.py` — Fast Movement is movement only, not AC

---

## Integration Seams

**`EF.CLASS_LEVELS` pattern** (canonical):
```python
class_levels = entity.get(EF.CLASS_LEVELS, {})
barbarian_level = class_levels.get("barbarian", 0)
```

**`build_full_move_intent` speed read** (`movement_resolver.py` ~line 220):
```python
speed_ft = entity.get(EF.BASE_SPEED, 30)
# INSERT Fast Movement bonus check here, before encumbrance penalty application
```

**Encumbrance utility** (`aidm/core/encumbrance.py`):
```python
def calculate_effective_speed(entity: Dict, catalog: ItemCatalog) -> int:
    # requires catalog — check if available in movement_resolver call context
```

---

## Assumptions to Validate

1. Confirm whether `EF.ARMOR_TYPE` already exists in entity_fields. Search for "armor_type" and "ARMOR_TYPE". If it exists under a different constant name, use that name.
2. Confirm whether `item_catalog` is available in the `build_full_move_intent()` call context. If not, document load check as deferred.
3. Confirm `EF.BASE_SPEED` is correctly set to 30 for humans and equivalent for non-human races (dwarves have 20 ft base — Fast Movement bonus brings them to 30, not 40, per PHB p.26 footnote). Check this race interaction is not broken by the bonus.

> **PHB note on dwarves:** Dwarves have 20 ft base speed and still gain +10 from Fast Movement (bringing them to 30 ft). The +10 is always additive to racial base speed.

---

## Regression

**Batch WO:** Run your WO-specific gate only: `pytest tests/test_engine_barbarian_fast_movement_001_gate.py`. File your debrief on that result. A dedicated regression agent runs the full suite after all Batch D WOs land.

If gate produces unexpected failures: fix once, re-run once. If still failing, record the failure in your debrief and stop. Do not loop.

---

## Scope Boundaries

- Do NOT implement Barbarian Rage speed bonus (separate from Fast Movement)
- Do NOT modify encumbrance logic
- Do NOT touch any other class feature speed interactions (Monk Fast Movement is different — unarmored only, different WO if needed)
- Do NOT implement load-tier checks if catalog is not available in call context — document as deferred finding

---

## Debrief Required

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001.md`

**Pass 1:** Per-file breakdown (MUST include armor type field verification result and catalog availability check). **Pass 2:** PM summary ≤100 words. **Pass 3:** Retrospective + Radar.

Missing debrief or missing Radar → REJECT.

**Audio Cue (mandatory):**
```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

---

## BATCH D — DISPATCH NOTES FOR PM

### File conflict coordination

`metamagic_resolver.py` is touched by both Silent Spell and Still Spell. If dispatched to different builders:
- Builder A (Silent Spell) adds `"silent"` entries only.
- Builder B (Still Spell) adds `"still"` entries only.
- Builder B should verify Builder A's entries exist before adding their own — do not remove or overwrite.
- Recommend: dispatch both to the same builder, or serialize Silent before Still.

### Open debrief items (ML-002 mandatory)

After each debrief is accepted, ask the builder: **"Anything else you noticed outside the debrief?"** File any new findings before closing the WO. This is mandatory per ML-002.

### Batch regression agent

After all four WO-specific gates pass and debriefs are filed, dispatch a single regression runner:
```
pytest tests/
```
Pre-existing failures: 23. Treat any new failures as regressions. Report to Slate.

---

*Drafted 2026-02-26 — Slate (PM). Authorized Thunder (PO). Batch D.*
