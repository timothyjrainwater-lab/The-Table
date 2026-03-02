# DEBRIEF: BATCH-AT-ENGINE-001

**Commit:** 719ae20
**WOs:** WO-ENGINE-SAVE-PATH-HARDEN-001 (SPH-001..008), WO-ENGINE-SPELL-DEF-DEDUP-001 (SDD-001..008)
**Gates:** 16/16 pass
**Suite:** 9,320 passed / 189 pre-existing failures (ws_bridge/UI infra) / 0 new regressions
**Verdict Review Class:** SELF-REVIEW + ANVIL SPOT-CHECK (save_resolver negative level penalty closes split-authority gap; resolver parity involved)

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-SAVE-PATH-HARDEN-001

#### File 1: `aidm/core/play_loop.py` — massive damage inline save block

**Before (lines 1224-1249, original):**
```python
# WO-ENGINE-MASSIVE-DAMAGE-RULE-001: Massive Damage check (PHB p.145)
# Single hit 50+ HP damage → Fort DC 15 save or instant death.
if damage >= 50:
    from aidm.core.save_resolver import get_save_bonus, SaveType as _SaveType
    _md_save_bonus = get_save_bonus(world_state, entity_id, _SaveType.FORT)
    _md_roll = rng.stream("combat").randint(1, 20)   # ← STREAM VIOLATION
    _md_total = _md_roll + _md_save_bonus
    _md_saved = _md_total >= 15
    events.append(Event(...event_type="massive_damage_check"...))
    current_event_id += 1
    if not _md_saved:
        new_hp = -10
```

**After:**
```python
# WO-ENGINE-SAVE-PATH-HARDEN-001: route through resolve_save() to pick up all
# global modifiers and use rng.stream("saves") — not rng.stream("combat").
if damage >= 50:
    from aidm.core.save_resolver import resolve_save as _resolve_save, SaveType as _SaveType
    from aidm.schemas.saves import SaveContext as _SaveContext, SaveOutcome as _SaveOutcome
    _md_ctx = _SaveContext(
        save_type=_SaveType.FORT, dc=15,
        source_id="massive_damage", target_id=entity_id,
    )
    _md_outcome, _md_save_events = _resolve_save(
        save_context=_md_ctx, world_state=world_state, rng=rng,
        next_event_id=current_event_id, timestamp=timestamp + 0.005,
    )
    events.extend(_md_save_events)
    current_event_id += len(_md_save_events)
    if _md_outcome != _SaveOutcome.SUCCESS:
        new_hp = -10  # Instant death on failed Fort save (PHB p.145)
```

**SPH-001 result:** Old code used `rng.stream("combat").randint(1, 20)` — explicit combat stream call. New code delegates to `resolve_save()` which uses `rng.stream("saves")` internally (save_resolver.py line 431). Confirmed via SPH-001 test: fixed saves-stream value=20 → SUCCESS; fixed combat-stream value=1 → ignored.

#### File 2: `aidm/core/save_resolver.py` — negative level penalty

**Before (total_bonus assembly, lines ~263-276):**
```python
total_bonus = (
    base_save + condition_save_mod + inspire_courage_bonus
    + feat_save_bonus + divine_grace_bonus
    ...
    + fatigue_ref_penalty
    + trap_sense_bonus
)
```

**After:**
```python
# WO-ENGINE-SAVE-PATH-HARDEN-001: Negative level save penalty (PHB p.294)
negative_level_penalty = entity.get(EF.NEGATIVE_LEVELS, 0)

total_bonus = (
    base_save + condition_save_mod + inspire_courage_bonus
    + feat_save_bonus + divine_grace_bonus
    ...
    + fatigue_ref_penalty
    + trap_sense_bonus
    - negative_level_penalty  # WO-ENGINE-SAVE-PATH-HARDEN-001: -1/level (PHB p.294)
)
```

**EF field name confirmation:** `EF.NEGATIVE_LEVELS` — confirmed via prior session grep (test_engine_improved_maneuver_001_gate.py line 77 shows `EF.NEGATIVE_LEVELS: 0` in entity builder) and direct grep. No bare string literal.

**Exact line evidence:** `negative_level_penalty = entity.get(EF.NEGATIVE_LEVELS, 0)` inserted before `total_bonus` assembly in `get_save_bonus()`.

#### File 3: `aidm/core/play_loop.py` — `_create_target_stats()` double-apply removal

**Before (lines ~283-288):**
```python
# WO-ENGINE-ENERGY-DRAIN-001: Each negative level gives -1 to all saves (PHB p.215)
# save_resolver doesn't handle negative levels, so apply here.
neg_level_penalty = entity.get(EF.NEGATIVE_LEVELS, 0)
fort_save -= neg_level_penalty
ref_save -= neg_level_penalty
will_save -= neg_level_penalty
```

**After:**
```python
# WO-ENGINE-SAVE-PATH-HARDEN-001: negative_level_penalty now applied inside get_save_bonus()
# (save_resolver.py, PHB p.294). Removed explicit subtraction here to avoid double-apply.
```

**Double-apply confirmation:** `_create_target_stats()` calls `_get_save_bonus()` (which now subtracts the penalty), then previously subtracted again explicitly. Post-fix: `get_save_bonus()` is the single authority. SPH-006 confirms zero negative levels = no penalty (regression guard).

#### Gate file: `tests/test_engine_save_path_harden_001_gate.py`
Gates SPH-001..008 — 8/8 pass.

---

### WO2: WO-ENGINE-SPELL-DEF-DEDUP-001

#### File: `aidm/data/spell_definitions.py`

**Duplicate detection result:** 39 duplicate keys found in the main SPELL_REGISTRY dict. `spell_definitions_ext.py` — 0 duplicates (confirmed).

**Full duplicate list:**
mending (1996), read_magic (2011), resistance (2016), color_spray (2052), grease (2088), sleep (2174), bears_endurance (2202), cats_grace (2207), invisibility (2262), mirror_image (2283), owls_wisdom (2288), resist_energy (2298), silence (2319), dispel_magic (2375), magic_circle_against_evil (2396), stinking_cloud (2434), cure_critical_wounds (2481), dimension_door (2492), greater_invisibility (2513), ice_storm (2518), stoneskin (2569), wall_of_fire (2579), baleful_polymorph (2593), hold_monster (2622), telekinesis (2649), true_seeing (2655), antimagic_field (2667), chain_lightning (2672), disintegrate (2689), greater_dispel_magic (2722), finger_of_death (2735), greater_teleport (2741), prismatic_spray (2756), reverse_gravity (2761), horrid_wilting (2787), mind_blank (2793), polar_ray (2798), power_word_stun (2803), wish (2845).

*(Line numbers = second/compact occurrence removed. First/verbose occurrence kept.)*

**For each duplicate:** Verbose entry (earlier line, full fields: `aoe_shape`, `aoe_radius_ft`, `damage_dice`, `save_effect`, `conditions_on_fail`, `content_id`) kept. Compact OSS entry (later line, 2-4 lines, missing verbose fields) removed.

**Example — grease:**
- Kept verbose (line 710): `save_type=REF`, `aoe_shape=BURST`, `aoe_radius_ft=10`, `conditions_on_fail=("prone",)`, `content_id="spell.grease_003"` — PHB p.237 accurate
- Removed compact (line 2088): `save_type=REF` only, no aoe fields, no conditions_on_fail

**`spell_definitions_ext.py` cross-file check:** Confirmed — 0 duplicates. ext.py is auto-generated novel entries. No cross-file overlaps.

**SDD-004 — spell_school=None count:**
- Before fix: 39 compact entries (the duplicates) had `school` set, but the verbose fields they overwrote included schools. Post-dedup, all 733 entries have `school != None`. Count of `spell_school=None`: **0**.

**SDD-005 — SPELL_REGISTRY count:**
- Before: 733 (254 main dict entries - net after Python duplicate-key behavior + 518 ext entries via `.update()` — Python silently kept last value, so the count was still 733 since all duplicates map to the same set of keys)
- After: 733 (215 unique main dict entries + 518 ext entries, zero overlap confirmed)

#### Gate file: `tests/test_engine_spell_def_dedup_001_gate.py`
Gates SDD-001..008 — 8/8 pass.

---

## PM Acceptance Notes Responses

### WO1:

1. **Before/after massive damage block:** Shown above. Old: `rng.stream("combat").randint(1, 20)` + `get_save_bonus()`. New: `resolve_save()` via `SaveContext`. File line reference: old at ~play_loop.py:1227-1229, new at ~play_loop.py:1227-1244.

2. **EF field name for negative levels:** `EF.NEGATIVE_LEVELS` — confirmed via test builder (`EF.NEGATIVE_LEVELS: 0`) and direct grep. Used as `entity.get(EF.NEGATIVE_LEVELS, 0)` in `save_resolver.py`.

3. **save_resolver.py where penalty subtracted:** `negative_level_penalty = entity.get(EF.NEGATIVE_LEVELS, 0)` inserted before `total_bonus` assembly in `get_save_bonus()`. Subtracted as `- negative_level_penalty` in the total_bonus expression.

4. **_create_target_stats() double-apply:** Post-fix, the 3-line explicit subtraction (`neg_level_penalty = entity.get(EF.NEGATIVE_LEVELS, 0); fort_save -= ...; ref_save -= ...; will_save -= ...`) was REMOVED. `get_save_bonus()` is now the single authority. No double-apply. Confirmed via SPH-005: 2 negative levels → -2 on all 3 save types (not -4).

5. **SPH-001 result:** Old code explicitly called `rng.stream("combat")` for the MD save roll. New code calls `resolve_save()` which calls `rng.stream("saves")` at save_resolver.py:431. Test verifies saves stream controls the outcome (combat stream value ignored).

### WO2:

1. **Full duplicate list:** 39 entries listed above with their line numbers.

2. **Per-duplicate kept/removed summary:** Verbose (earlier, full PHB fields) kept; compact OSS (later, 2-4 line stubs) removed. See grease example above. Pattern is consistent across all 39.

3. **spell_definitions_ext.py cross-file check:** Confirmed 0 duplicates. AST parse found no duplicate keys in ext.py, and no keys in ext.py overlap with verbose entries in definitions.py (ext.py covers novel non-PHB spells).

4. **SDD-004 — spell_school=None:** Before: 0 (Python dict kept last value — compact entries all had `school` field set). After: 0. No change in school-None count, but verbose entries restored their rich field sets.

5. **SDD-005 — SPELL_REGISTRY count:** Before dedup: 733. After: 733. Count unchanged (39 duplicates removed from dict definition, but Python was only keeping one value per key anyway — the `.update()` via ext.py already handled unique novel entries).

---

## Pass 2 — PM Summary (100 words)

WO1 closes three save path gaps: (1) massive damage Fort save now routes through `resolve_save()` (eliminating inline `rng.stream("combat")` violation), (2) negative level penalty (-1/level, PHB p.294) wired into `save_resolver.get_save_bonus()` as canonical authority, (3) `_create_target_stats()` explicit redundant subtraction removed to prevent double-apply. WO2 removes 39 compact OSS duplicate dict keys from `spell_definitions.py`, restoring verbose PHB-accurate entries (save_type, aoe_shape, conditions_on_fail, content_id). SPELL_REGISTRY count unchanged at 733. All 16 gates pass. 9,320 / 189 pre-existing failures.

---

## Pass 3 — Retrospective

**Out-of-scope findings:**
- FINDING-ENGINE-MASSIVE-DAMAGE-THRESHOLD-HALF-HP-001 (LOW): PHB p.145 states massive damage fires when single hit ≥ 50 OR ≥ half max HP. Current code only checks `if damage >= 50`. The half-max-HP condition is not implemented. PHB: "an amount of damage equal to half your total hit points (minimum 50 points of damage)". An entity with 200 HP should trigger on 100+ damage even if < 50. This is in scope for a future WO. Filed to backlog.
- FINDING-ENGINE-SPELL-DEF-STINKING-CLOUD-NAUSEATE-001 (LOW): `stinking_cloud.conditions_on_fail` is missing in the restored verbose entry (it has `save_type=FORT` and `duration_rounds=1` but no condition). PHB p.262: "Any creature in the cloud must succeed on a Fortitude save (DC 15) or spend its next turn choking and retching; it can still defend itself normally but cannot move or take actions." The nauseated-equivalent condition is missing. Not in scope for AT (data integrity fix only) — filed to backlog.

**Kernel touches:**
- This WO touches KERNEL-06 (Save Resolver) — `get_save_bonus()` now includes negative level penalty; `_create_target_stats()` split-authority pattern resolved
- This WO touches KERNEL-02 (Data Layer) — 39 compact OSS duplicates removed from SPELL_REGISTRY definition; verbose entries restored

---

## Radar — Findings

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| FINDING-ENGINE-MD-INLINE-SAVE-PATTERN-001 | Massive damage inline save bypassed resolve_save() | HIGH | CLOSED |
| FINDING-AUDIT-SAVE-004 | MD save used rng.stream("combat") — stream isolation | MEDIUM | CLOSED |
| FINDING-AUDIT-SAVE-006 | Negative level penalty missing from general save path | MEDIUM | CLOSED |
| FINDING-ENGINE-NEGATIVE-LEVEL-SAVE-001 | Same as AUDIT-SAVE-006 | MEDIUM | CLOSED |
| FINDING-ENGINE-SPELL-DEF-DUPLICATE-ENTRIES-001 | 39 OSS compact entries overwriting verbose PHB entries | HIGH | CLOSED |
| FINDING-ENGINE-MASSIVE-DAMAGE-THRESHOLD-HALF-HP-001 | Half-HP threshold missing from massive damage check | LOW | NEW → BACKLOG |
| FINDING-ENGINE-SPELL-DEF-STINKING-CLOUD-NAUSEATE-001 | stinking_cloud missing conditions_on_fail | LOW | NEW → BACKLOG |

---

## Coverage Map Updates

**Updated rows (`docs/ENGINE_COVERAGE_MAP.md`):**
- Massive Damage Fort Save: PARTIAL → IMPLEMENTED. Note: "wired to resolve_save(). PHB p.145. SPH-001..003. Batch AT."
- Negative Level Save Penalty: NOT STARTED → IMPLEMENTED. Note: "save_resolver.py get_save_bonus(). PHB p.294. SPH-004..005. Batch AT."

**No new row for WO2** (data integrity fix, not a PHB mechanic).

---

## ML Preflight Checklist

| Check | WO1 (SPH) | WO2 (SDD) |
|-------|-----------|-----------|
| ML-001: No bare string literals (EF.* used) | ✅ `EF.NEGATIVE_LEVELS` used via constant | N/A (data file) |
| ML-002: All call sites identified | ✅ MD block: single play_loop site. `_create_target_stats`: double-apply confirmed + removed | ✅ Definitions + ext both checked |
| ML-003: No float in deterministic path | ✅ No dice math | ✅ No dice math |
| ML-004: json.dumps sort_keys if any | N/A | N/A |
| ML-005: No WorldState mutation in resolver | ✅ save_resolver returns events; no WS mutation | ✅ Data file only |
| ML-006: Coverage map updated | ✅ Massive damage + negative level rows | N/A (data integrity) |

---

## Consume-Site Confirmation

**WO1:**
- Write site: `save_resolver.py get_save_bonus()` — `entity.get(EF.NEGATIVE_LEVELS, 0)` subtracted
- Read site: `resolve_save()` calls `get_save_bonus()` at save_resolver.py:424 → all callers (including massive damage after fix) pick up penalty
- Observable effect: Entity with N negative levels has -N on all Fort/Ref/Will saves
- Gate proof: SPH-004 (1 neg level = -1 Fort), SPH-005 (2 neg levels = -2 all three saves)

**WO2:**
- Write site: `spell_definitions.py` SPELL_REGISTRY dict — 39 compact entries removed, verbose preserved
- Read site: `play_loop.py` → `resolve_spell()` → `spell_resolver.py` consumes `SPELL_REGISTRY` via import
- Observable effect: Spells like `grease` now have `conditions_on_fail=("prone",)`, `aoe_shape=BURST`, etc.
- Gate proof: SDD-002 (grease verbose fields), SDD-003 (stinking_cloud verbose fields)

**Post-AT gate count:** 1,634 + 16 = **1,650**
**Sweep counter:** 4/5 → **5/5** — AT accepted triggers AUDIT-MANEUVER-014 dispatch to Anvil seat.
