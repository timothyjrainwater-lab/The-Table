# WO-CHARGEN-PHASE3 — Dual-Caster Merging, Animal Companions, Racial Trait Encoding

**Issued:** 2026-02-23
**Authority:** CHARGEN PHASE 2 COMPLETE (`9bf1d3d`). Gate V9 (level-up) already dispatched. This packet covers the next three chargen gates: V10 (dual-caster), V11 (companions), V12 (racial traits).
**Blocked by:** Nothing. V9 level-up WO is parallel, no dependency.
**Dispatch order:** V10 first (touches `_merge_spellcasting()`). V11 and V12 are independent and may be dispatched in parallel if two builders are available.

---

## Phase 3 Scope Summary

| WO | Gate | Tests | Scope |
|---|---|---|---|
| WO-CHARGEN-DUALCASTER-001 | V10 | 20 | Dual-caster spell slot merging for multiclass casters |
| WO-CHARGEN-COMPANION-001 | V11 | 25 | Animal companion entity generation (druid/ranger) |
| WO-CHARGEN-RACIAL-001 | V12 | 18 | Racial trait mechanical encoding in entity dict |

Total: 63 tests across 3 WOs. After acceptance: CHARGEN PHASE 3 COMPLETE.

---

## WO-CHARGEN-DUALCASTER-001 — Gate V10

### 1. Target Lock

A `wizard 3 / cleric 3` character built via `class_mix={"wizard": 3, "cleric": 3}` currently gets only wizard spell slots (first-caster-wins heuristic from Phase 2, explicitly deferred from WO-CHARGEN-MULTICLASS-001). After this WO, both spell pools are present in the entity dict: the primary caster (alphabetically first) uses `SPELL_SLOTS` / `SPELLS_PREPARED` / `CASTER_LEVEL`; the secondary caster uses new `_2` suffix fields.

A single-caster multiclass (fighter/wizard) is unchanged — it still uses top-level fields only. No `_2` fields appear on single-caster or non-caster entities.

**Scope boundary:** Shared slot-pool merging (Mystic Theurge prestige class feature) is out of scope. This WO stores separate pools per caster class. Slot-pool merging is a prestige-class concern for a future WO.

---

### 2. Binary Decisions (V10)

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Storage structure | `SPELL_SLOTS` = primary caster; `SPELL_SLOTS_2` = secondary caster. Both keyed by spell level: `{0: 4, 1: 2, ...}` | Caller inspects by EF constant. Combat engine reads primary (existing path); secondary available for future extension. |
| 2 | Primary vs secondary assignment | Alphabetical order among caster classes in `class_mix` | Deterministic across Python versions. `cleric < wizard` → cleric is primary. |
| 3 | Spontaneous vs prepared, secondary | Same rule as primary: spontaneous casters (bard, sorcerer) get `SPELLS_KNOWN_2`; prepared casters get `SPELLS_PREPARED_2` | Symmetric pattern. |
| 4 | Spell input for secondary caster | New `spell_choices_2: Optional[List[str]]` param on `build_character()` | Callers can specify both lists independently. |
| 5 | Default spells for secondary caster | If `spell_choices_2` not provided, populate from class spell list (same default as primary) | Fail-permissive at chargen. |
| 6 | Non-dual-caster paths | `SPELL_SLOTS_2`, `SPELLS_PREPARED_2`, `SPELLS_KNOWN_2`, `CASTER_CLASS_2`, `CASTER_LEVEL_2` are absent (not empty) for 0 or 1 caster classes | No noise in non-caster entities. |
| 7 | Three caster classes | Raise `ValueError("Only two caster classes supported in class_mix")` | Edge case; defer 3-caster support. |

---

### 3. Contract Spec (V10)

#### 3.1 New EF fields (add to `aidm/schemas/entity_fields.py`)

```python
SPELL_SLOTS_2        = "spell_slots_2"
SPELLS_PREPARED_2    = "spells_prepared_2"
SPELLS_KNOWN_2       = "spells_known_2"
CASTER_CLASS         = "caster_class"        # name of primary caster class (add if absent)
CASTER_CLASS_2       = "caster_class_2"
CASTER_LEVEL_2       = "caster_level_2"
```

Check which of these already exist before adding.

#### 3.2 Signature change

```python
def build_character(
    race: str,
    class_name: str,
    level: int = 1,
    ability_method: str = "standard",
    ability_overrides: Optional[Dict[str, int]] = None,
    feat_choices: Optional[List[str]] = None,
    skill_allocations: Optional[Dict[str, int]] = None,
    spell_choices: Optional[List[str]] = None,
    spell_choices_2: Optional[List[str]] = None,     # NEW
    starting_equipment: Optional[Dict[str, int]] = None,
    use_rolled_gold: bool = False,
    class_mix: Optional[Dict[str, int]] = None,
    favored_class: Optional[str] = None,
) -> Dict[str, Any]:
```

#### 3.3 Detection logic in `_merge_spellcasting()`

```python
caster_classes = sorted([cls for cls in class_mix if is_caster(cls)])

if len(caster_classes) == 0:
    return {}   # no caster fields

elif len(caster_classes) == 1:
    # Existing single-caster path — unchanged
    ...

elif len(caster_classes) == 2:
    primary, secondary = caster_classes[0], caster_classes[1]
    primary_lvl = class_mix[primary]
    secondary_lvl = class_mix[secondary]

    # Primary — top-level fields (existing EF constants)
    primary_slots = get_spell_slots(primary, primary_lvl, ability_scores)
    # ... spells_prepared or spells_known per caster type ...

    # Secondary — _2 suffix fields
    secondary_slots = get_spell_slots(secondary, secondary_lvl, ability_scores)
    # ... spells_prepared_2 or spells_known_2 per caster type ...

    return {
        EF.SPELL_SLOTS: primary_slots,
        EF.CASTER_LEVEL: primary_lvl,
        EF.CASTER_CLASS: primary,
        EF.SPELL_SLOTS_2: secondary_slots,
        EF.CASTER_LEVEL_2: secondary_lvl,
        EF.CASTER_CLASS_2: secondary,
        # plus prepared/known fields as appropriate
    }

else:
    raise ValueError("Only two caster classes supported in class_mix")
```

---

### 4. Gate V10 Tests (~20 tests)

Write `tests/test_chargen_gate_v10.py`:

| Test ID | Description |
|---------|-------------|
| V10-01 | `cleric/wizard` mix: `CASTER_CLASS`="cleric" (alphabetically first), `CASTER_CLASS_2`="wizard" |
| V10-02 | `cleric/wizard` 5/5: `SPELL_SLOTS` = cleric level-5 slots; `SPELL_SLOTS_2` = wizard level-5 slots |
| V10-03 | Slot counts match PHB tables for each class independently |
| V10-04 | `druid/sorcerer` mix: sorcerer (spontaneous) has `SPELLS_KNOWN_2`; druid has `SPELLS_PREPARED` |
| V10-05 | `bard/wizard` mix: bard is primary (b < w), wizard is secondary |
| V10-06 | `CASTER_LEVEL` and `CASTER_LEVEL_2` reflect each class's own level, not total |
| V10-07 | Bonus spell slots from ability score applied per caster using their respective casting ability |
| V10-08 | `spell_choices_2` populates secondary caster's spells |
| V10-09 | Without `spell_choices_2`, secondary caster defaults from class spell list |
| V10-10 | Single-caster multiclass (fighter/wizard): no `_2` fields present in entity dict |
| V10-11 | Non-caster multiclass (fighter/rogue): no spell fields at all |
| V10-12 | Three caster classes raises ValueError |
| V10-13 | `paladin/ranger` mix (both partial casters): dual-caster path applies |
| V10-14 | Entity has no KeyError on any EF constant read by existing consumers |
| V10-15 | V6 regression: single-class wizard — `SPELL_SLOTS` present, no `_2` fields |
| V10-16 | V8 regression: `fighter/wizard` single-caster path unchanged |
| V10-17 | Dual-caster with `ability_overrides`: bonus spells use correct ability per caster |
| V10-18 | `cleric/wizard` prepared lists distinct (cleric divine, wizard arcane) |
| V10-19 | `CASTER_CLASS` field present on single-caster multiclass (wizard in fighter/wizard) |
| V10-20 | Debrief anchor: `wizard 3 / cleric 3` — print both slot tables for PM verification |

---

### 5. Implementation Plan (V10)

1. **Read** `aidm/chargen/builder.py` — locate `_merge_spellcasting()` and the multiclass dispatch path
2. **Read** `aidm/chargen/spellcasting.py` — confirm `get_spell_slots()`, `SPONTANEOUS_CASTERS`, `CASTING_ABILITY` are sufficient
3. **Edit** `aidm/schemas/entity_fields.py` — add new EF constants (check before adding)
4. **Edit** `aidm/chargen/builder.py`:
   - Add `spell_choices_2` param to `build_character()` signature
   - Refactor `_merge_spellcasting()` to detect and handle dual-caster case
   - Thread `spell_choices_2` through to secondary spell assembly
5. **Write** `tests/test_chargen_gate_v10.py` — 20 tests
6. **Run** `pytest tests/test_chargen_gate_v10.py -v` — all pass
7. **Run** `pytest tests/ --tb=no -q` — zero regressions

---

### 6. Deliverables Checklist (V10)

- [ ] New EF constants added to `entity_fields.py`
- [ ] `spell_choices_2` param on `build_character()`
- [ ] `_merge_spellcasting()` handles 0, 1, and 2 caster class cases correctly
- [ ] Dual-caster entity has top-level fields (primary) and `_2` fields (secondary)
- [ ] `SPELLS_PREPARED` / `SPELLS_KNOWN` pattern consistent for both casters
- [ ] `tests/test_chargen_gate_v10.py` — 20/20 PASS
- [ ] V6, V7, V8, V9 gate tests — zero regressions

---

---

## WO-CHARGEN-COMPANION-001 — Gate V11

### 1. Target Lock

A druid or ranger built with `build_character()` can optionally receive an animal companion entity dict by calling `build_animal_companion(entity, companion_type)` after chargen. The companion is a complete, combat-engine-ready entity dict (all applicable EF.* fields populated) scaled to the druid's effective companion level per PHB Table 3-4 (p.36). The companion is not embedded in the parent entity — it is a separate entity, ready for `WorldState` insertion by the caller.

This closes GAP-CG-009 from WO-CHARGEN-RESEARCH-001.

**Scope boundary:** Five PHB companion types at effective companion levels 1–7 (levels 1–3 of the table). Trick system not encoded (informational note only). Improved companions (bear, big cat, etc., effective level 4+) are a separate future WO.

---

### 2. Binary Decisions (V11)

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | API | Standalone function `build_animal_companion(parent_entity, companion_type)` in new `aidm/chargen/companions.py` | Separate module. Does not touch `builder.py`. |
| 2 | Ranger companion level | Effective druid level = ranger_level − 3; ranger ≤ 3 raises ValueError | PHB p.47. |
| 3 | Multiclass druid/ranger | Effective level = druid_level + max(0, ranger_level − 3) | PHB p.36 stacking footnote. |
| 4 | Companion stats scaling | Apply PHB Table 3-4 (bonus HD, natural AC adj, Str/Dex adj, Multiattack feat) at thresholds 1, 4, 7 | Implement first three rows; higher rows require improved companions (deferred). |
| 5 | Five companion types | Wolf, riding dog, eagle, light horse, viper snake | Most common at low-mid levels; full PHB base list is 10+ — these 5 cover 90% of use cases. |
| 6 | Companion `TEAM` | Match parent `TEAM` | Companion is allied to owner. |
| 7 | `ENTITY_ID` | `f"companion_{companion_type}_{parent_entity[EF.ENTITY_ID]}"` | Unique, traceable. |
| 8 | No spell fields | `SPELL_SLOTS`, `INVENTORY`, `ENCUMBRANCE_LOAD` absent from companion dict | Companions carry no gear and cast no spells. |
| 9 | Multiattack feat | Added to `FEATS` at effective companion level ≥ 4 | PHB Table 3-4 (row 2). |
| 10 | Tricks | Not in entity dict; note in `special` field as informational strings | Defer trick system. |

---

### 3. Contract Spec (V11)

#### 3.1 New file `aidm/chargen/companions.py`

Key data structures:

```python
# Base stats per companion type (PHB MM / PHB p.36 sidebar)
BASE_COMPANION_STATS: Dict[str, Dict] = {
    "wolf": {
        "size": "medium", "speed": 50, "hd": 2, "hd_die": 8,
        "str": 13, "dex": 15, "con": 15, "int": 2, "wis": 12, "cha": 6,
        "natural_ac_bonus": 2,
        "fort_good": True, "ref_good": True, "will_good": False,
        "bab_progression": "3_4",
        "attack": {"name": "bite", "damage": "1d6", "crit_range": 20, "crit_mult": 2},
        "special": ["trip"],
        "skill_ranks": {"listen": 2, "spot": 2, "hide": 1, "move_silently": 1},
        "class_skills": ["hide", "listen", "move_silently", "spot", "survival", "swim"],
    },
    "riding_dog": { ... },   # PHB MM stats
    "eagle": { ... },
    "light_horse": { ... },
    "viper_snake": { ... },
}

# PHB Table 3-4 progression rows (effective druid level thresholds)
COMPANION_PROGRESSION: Dict[int, Dict] = {
    1:  {"bonus_hd": 0, "natural_ac_adj": 0, "str_dex_adj": 0, "bonus_tricks": 1},
    4:  {"bonus_hd": 2, "natural_ac_adj": 2, "str_dex_adj": 1, "bonus_tricks": 2},
    7:  {"bonus_hd": 4, "natural_ac_adj": 4, "str_dex_adj": 2, "bonus_tricks": 3},
    10: {"bonus_hd": 6, "natural_ac_adj": 6, "str_dex_adj": 3, "bonus_tricks": 4},
    13: {"bonus_hd": 8, "natural_ac_adj": 8, "str_dex_adj": 4, "bonus_tricks": 5},
    16: {"bonus_hd": 10, "natural_ac_adj": 10, "str_dex_adj": 5, "bonus_tricks": 6},
    19: {"bonus_hd": 12, "natural_ac_adj": 12, "str_dex_adj": 6, "bonus_tricks": 7},
}
```

`build_animal_companion()` signature:

```python
def build_animal_companion(
    parent_entity: Dict[str, Any],
    companion_type: str,
) -> Dict[str, Any]:
    """Build a combat-ready animal companion entity dict.

    Args:
        parent_entity: The druid or ranger entity dict from build_character().
        companion_type: One of "wolf", "riding_dog", "eagle", "light_horse", "viper_snake".

    Returns:
        Complete entity dict ready for WorldState insertion.
        ENTITY_ID, TEAM, all combat stats, SKILL_RANKS, FEATS populated.
        SPELL_SLOTS, INVENTORY, ENCUMBRANCE_LOAD absent.

    Raises:
        ValueError: If parent has no qualifying companion class (druid or ranger 4+).
        ValueError: If companion_type is not in BASE_COMPANION_STATS.
    """
```

#### 3.2 Companion entity dict keys

Must populate (all EF.* constants):
- `ENTITY_ID`, `RACE` ("animal"), `TEAM`, `LEVEL` (total HD after bonus), `CLASS_LEVELS` ({})
- `BASE_STATS`, `STR_MOD`, `DEX_MOD`, `CON_MOD`, `INT_MOD`, `WIS_MOD`, `CHA_MOD`
- `HP_MAX`, `HP_CURRENT`, `DEFEATED`
- `BAB`, `ATTACK_BONUS`, `AC` (10 + DEX mod + natural AC bonus)
- `SAVE_FORT`, `SAVE_REF`, `SAVE_WILL`
- `SKILL_RANKS`, `CLASS_SKILLS`
- `FEATS` (Multiattack at effective companion level ≥ 4)
- `WEAPON` (primary attack using same schema as PC WEAPON field)
- `SIZE_CATEGORY`, `BASE_SPEED`
- `CONDITIONS` ([]), `POSITION` ((0, 0)), `XP` (0)

Must NOT set: `SPELL_SLOTS`, `SPELLS_PREPARED`, `SPELLS_KNOWN`, `CASTER_LEVEL`, `INVENTORY`, `ENCUMBRANCE_LOAD`, `ARMOR_CHECK_PENALTY`.

---

### 4. Gate V11 Tests (~25 tests)

Write `tests/test_chargen_gate_v11.py`:

| Test ID | Description |
|---------|-------------|
| V11-01 | Druid 1 → wolf companion: base stats, 2 HD, natural AC 2 |
| V11-02 | Druid 4 → wolf: +2 HD (→4 total), +2 nat AC, +1 Str/Dex, Multiattack feat |
| V11-03 | Druid 7 → wolf: +4 HD (→6 total), +4 nat AC, +2 Str/Dex |
| V11-04 | Ranger 4 → wolf at effective druid level 1 (4−3=1) |
| V11-05 | Ranger 7 → wolf at effective druid level 4 (7−3=4): Multiattack present |
| V11-06 | Druid 2 / Ranger 4 multiclass → effective level 2+1=3: correct scaling |
| V11-07 | Ranger 3 raises ValueError (no companion yet) |
| V11-08 | Fighter entity raises ValueError (not a qualifying class) |
| V11-09 | Riding dog companion: correct base stats, attack field |
| V11-10 | Eagle companion: `SIZE_CATEGORY`="small", speed noted |
| V11-11 | Light horse: `SIZE_CATEGORY`="large", correct HD |
| V11-12 | Viper snake: `SIZE_CATEGORY`="small", `natural_ac_bonus`=4 |
| V11-13 | Unknown companion type raises ValueError |
| V11-14 | Companion `ENTITY_ID` includes parent entity ID |
| V11-15 | Companion `TEAM` matches parent `TEAM` |
| V11-16 | Companion has no `SPELL_SLOTS` key |
| V11-17 | Companion has no `INVENTORY` key |
| V11-18 | Wolf `SAVE_FORT` correct (good save, 2 HD, CON 15 → mod +2) |
| V11-19 | Wolf `BAB` correct (3/4 progression at 2 HD → BAB 1) |
| V11-20 | Wolf `AC` = 10 + DEX mod (+2) + natural AC bonus (2) = 14 |
| V11-21 | Wolf `WEAPON` field present with damage "1d6", crit 20/×2 |
| V11-22 | Wolf `SKILL_RANKS` has listen and spot |
| V11-23 | Druid 10 wolf: +6 HD, +6 nat AC, +3 Str/Dex |
| V11-24 | `FEATS` includes "multiattack" at effective companion level ≥ 4 |
| V11-25 | V6/V8 regression: `build_character()` unchanged |

---

### 5. Implementation Plan (V11)

1. **Read** `aidm/chargen/builder.py` — note imports, module structure (do not modify)
2. **Read** `aidm/schemas/entity_fields.py` — confirm EF constants needed exist
3. **Create** `aidm/chargen/companions.py`:
   - `BASE_COMPANION_STATS` dict for 5 companion types
   - `COMPANION_PROGRESSION` dict (all 7 table rows, even if only 3 are exercised by tests)
   - `_effective_companion_level()` helper
   - `_companion_progression_row()` helper
   - `build_animal_companion()` public function
4. **Edit** `aidm/chargen/__init__.py` — export `build_animal_companion` if `__init__` exports
5. **Write** `tests/test_chargen_gate_v11.py` — 25 tests
6. **Run** `pytest tests/test_chargen_gate_v11.py -v` — all pass
7. **Run** `pytest tests/ --tb=no -q` — zero regressions

Do **not** modify `builder.py`.

---

### 6. Deliverables Checklist (V11)

- [ ] `aidm/chargen/companions.py` created
- [ ] 5 companion types with full base stat blocks
- [ ] `COMPANION_PROGRESSION` covers all 7 PHB Table 3-4 rows
- [ ] Effective companion level correct for druid, ranger, and multiclass druid/ranger
- [ ] Multiattack feat added at effective companion level ≥ 4
- [ ] Companion entity uses correct EF.* constants; no banned fields present
- [ ] `tests/test_chargen_gate_v11.py` — 25/25 PASS
- [ ] Zero regressions on all prior gates

---

---

## WO-CHARGEN-RACIAL-001 — Gate V12

### 1. Target Lock

Seven PHB races have mechanical traits beyond ability score modifiers. These traits currently exist only in PHB text — they are not encoded in the entity dict. After this WO, `build_character()` populates racial trait fields for all 7 races. Combat resolvers already consume several of these fields (e.g., `STABILITY_BONUS` in `aoo.py`). The gap is that chargen doesn't populate them, so resolvers fall back to `.get(field, 0)` defaults instead of correct values.

This closes partial gap from GAP-CG-002 (racial traits) and the research deliverable's notes on mechanical encoding.

**This WO adds data, not resolvers.** No combat resolution logic is modified here.

---

### 2. Racial Traits to Encode

All values from PHB Chapter 2.

| Race | Trait | EF Field | Value |
|------|-------|----------|-------|
| Dwarf | Stability | `EF.STABILITY_BONUS` | 4 (vs trip and bull rush) |
| Dwarf | Poison resistance | `EF.SAVE_BONUS_POISON` | 2 |
| Dwarf | Spell/ability resistance | `EF.SAVE_BONUS_SPELLS` (new) | 2 |
| Dwarf | Stonecunning | `EF.STONECUNNING` (new, bool) | True |
| Dwarf | Darkvision | `EF.DARKVISION_RANGE` | 60 |
| Dwarf | Attack bonus vs orcs/goblinoids | `EF.ATTACK_BONUS_VS_ORCS` (new) | 1 |
| Dwarf | Dodge AC vs giants | `EF.DODGE_BONUS_VS_GIANTS` (new) | 4 |
| Elf | Low-light vision | `EF.LOW_LIGHT_VISION` (new, bool) | True |
| Elf | Sleep immunity | `EF.IMMUNE_SLEEP` (new, bool) | True |
| Elf | Enchantment save bonus | `EF.SAVE_BONUS_ENCHANTMENT` (new) | 2 |
| Elf | Passive search (secret doors) | `EF.AUTOMATIC_SEARCH_DOORS` (new, bool) | True |
| Elf | Skill bonus (Listen/Search/Spot) | `EF.RACIAL_SKILL_BONUS` (new, dict) | `{"listen": 2, "search": 2, "spot": 2}` |
| Halfling | All-save bonus | `EF.RACIAL_SAVE_BONUS` (new, int) | 1 |
| Halfling | Thrown weapon attack bonus | `EF.ATTACK_BONUS_THROWN` (new) | 1 |
| Halfling | Skill bonus (Listen/Move Silently) | `EF.RACIAL_SKILL_BONUS` | `{"listen": 2, "move_silently": 2}` |
| Gnome | Low-light vision | `EF.LOW_LIGHT_VISION` | True |
| Gnome | Illusion SR | `EF.SPELL_RESISTANCE_ILLUSION` (new) | 2 (+ class level at resolution time) |
| Gnome | Poison resistance | `EF.SAVE_BONUS_POISON` | 2 |
| Gnome | Attack bonus vs kobolds/goblinoids | `EF.ATTACK_BONUS_VS_KOBOLDS` (new) | 1 |
| Gnome | Illusion save DC bonus | `EF.ILLUSION_DC_BONUS` (new) | 1 |
| Half-elf | Low-light vision | `EF.LOW_LIGHT_VISION` | True |
| Half-elf | Sleep immunity | `EF.IMMUNE_SLEEP` | True |
| Half-elf | Enchantment save bonus | `EF.SAVE_BONUS_ENCHANTMENT` | 2 |
| Half-elf | Skill bonus | `EF.RACIAL_SKILL_BONUS` | `{"listen": 1, "search": 1, "spot": 1, "diplomacy": 2, "gather_information": 2}` |
| Half-orc | Darkvision | `EF.DARKVISION_RANGE` | 60 |
| Human | (bonus feat already encoded) | — | no new fields |
| Human | (skill bonus already encoded) | — | no new fields |

**New EF constants required** (check before adding — some may already exist):
`SAVE_BONUS_SPELLS`, `STONECUNNING`, `ATTACK_BONUS_VS_ORCS`, `DODGE_BONUS_VS_GIANTS`, `LOW_LIGHT_VISION`, `IMMUNE_SLEEP`, `SAVE_BONUS_ENCHANTMENT`, `AUTOMATIC_SEARCH_DOORS`, `RACIAL_SKILL_BONUS`, `RACIAL_SAVE_BONUS`, `ATTACK_BONUS_THROWN`, `SPELL_RESISTANCE_ILLUSION`, `ATTACK_BONUS_VS_KOBOLDS`, `ILLUSION_DC_BONUS`

---

### 3. Binary Decisions (V12)

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Encoding location | Extend race data dicts in `aidm/data/races.py`; `apply_racial_mods()` populates EF fields | Races already have ability mod data; additive extension, not restructure. |
| 2 | Missing trait default | Fields **absent** (not 0/False) for races that don't have the trait | Resolvers use `.get(EF.DARKVISION_RANGE, 0)`. Absence = no trait. Avoids false zeros. |
| 3 | `RACIAL_SKILL_BONUS` format | Dict `{skill_id: bonus_int}` | Matches `SKILL_RANKS` pattern; easy resolver lookup by skill. |
| 4 | `RACIAL_SAVE_BONUS` (halfling) | Stored as `int` (1); save resolver adds to all three saves at resolution | Simpler than per-save fields. |
| 5 | Gnome illusion SR | Store base value `2`; resolver adds class level at resolution time | Chargen value is always 2; effective SR is dynamic. |
| 6 | Half-orc literacy | Not encoded | Free literacy is a campaign assumption, not a mechanical field. |
| 7 | Pre-existing fields | `STABILITY_BONUS` and `DARKVISION_RANGE` exist in `entity_fields.py` per the research entity dict examples — confirm before adding | Read the file first. |

---

### 4. Gate V12 Tests (~18 tests)

Write `tests/test_chargen_gate_v12.py`:

| Test ID | Description |
|---------|-------------|
| V12-01 | Dwarf fighter 1: `STABILITY_BONUS` = 4 |
| V12-02 | Dwarf fighter 1: `SAVE_BONUS_POISON` = 2 |
| V12-03 | Dwarf fighter 1: `SAVE_BONUS_SPELLS` = 2 |
| V12-04 | Dwarf fighter 1: `DARKVISION_RANGE` = 60 |
| V12-05 | Dwarf fighter 1: `STONECUNNING` = True |
| V12-06 | Dwarf fighter 1: `ATTACK_BONUS_VS_ORCS` = 1 |
| V12-07 | Dwarf fighter 1: `DODGE_BONUS_VS_GIANTS` = 4 |
| V12-08 | Elf wizard 1: `LOW_LIGHT_VISION` = True |
| V12-09 | Elf wizard 1: `IMMUNE_SLEEP` = True |
| V12-10 | Elf wizard 1: `SAVE_BONUS_ENCHANTMENT` = 2 |
| V12-11 | Elf wizard 1: `RACIAL_SKILL_BONUS` has listen:2, search:2, spot:2 |
| V12-12 | Halfling rogue 1: `RACIAL_SAVE_BONUS` = 1 |
| V12-13 | Halfling rogue 1: `RACIAL_SKILL_BONUS` has listen:2, move_silently:2 |
| V12-14 | Half-orc barbarian 1: `DARKVISION_RANGE` = 60 |
| V12-15 | Half-elf ranger 1: `LOW_LIGHT_VISION` = True, `SAVE_BONUS_ENCHANTMENT` = 2 |
| V12-16 | Human fighter 1: no `DARKVISION_RANGE` key (key must be absent, not 0) |
| V12-17 | Human fighter 1: no `STABILITY_BONUS` key (absent, not 0) |
| V12-18 | Regression spot checks: elf wizard, dwarf fighter, halfling rogue still build without error |

---

### 5. Implementation Plan (V12)

1. **Read** `aidm/data/races.py` — understand `RACE_REGISTRY` structure and `apply_racial_mods()` function
2. **Read** `aidm/schemas/entity_fields.py` — note which new EF constants are needed
3. **Edit** `aidm/schemas/entity_fields.py` — add missing constants (check list above carefully)
4. **Edit** `aidm/data/races.py`:
   - Extend each race's data dict with racial trait fields
   - Update `apply_racial_mods()` to populate new EF fields from race data (field-by-field, only if trait exists)
5. **Write** `tests/test_chargen_gate_v12.py` — 18 tests
6. **Run** `pytest tests/test_chargen_gate_v12.py -v` — all pass
7. **Run** `pytest tests/ --tb=no -q` — zero regressions

---

### 6. Deliverables Checklist (V12)

- [ ] Missing EF constants added to `entity_fields.py`
- [ ] All 7 races in `aidm/data/races.py` have trait data encoded
- [ ] `apply_racial_mods()` populates EF fields per race; fields absent for races without the trait
- [ ] `tests/test_chargen_gate_v12.py` — 18/18 PASS
- [ ] Zero regressions on all prior gates (V1-V11)

---

---

## Phase 3 Gate Summary

| Gate | WO | Tests | Dependency | Dispatch |
|---|---|---|---|---|
| V10 | WO-CHARGEN-DUALCASTER-001 | 20 | None | FIRST |
| V11 | WO-CHARGEN-COMPANION-001 | 25 | None (independent of V10) | SECOND or parallel |
| V12 | WO-CHARGEN-RACIAL-001 | 18 | None (independent of V10, V11) | SECOND or parallel |

**Total Phase 3:** 3 WOs, 63 tests, Gates V10-V12.

After acceptance: **CHARGEN PHASE 3 COMPLETE.** `build_character()` fully feature-complete for dual-caster multiclass. `build_animal_companion()` available for druid/ranger builds. All 7 PHB race mechanical traits encoded in entity dict.

---

## Preflight (all three WOs)

```bash
# Per-WO gate check:
pytest tests/test_chargen_gate_v10.py -v    # V10: dual caster
pytest tests/test_chargen_gate_v11.py -v    # V11: companions
pytest tests/test_chargen_gate_v12.py -v    # V12: racial traits

# Full suite regression (run after each WO):
pytest tests/ --tb=no -q
```

---

## Debrief Focus

**V10 debrief:**
1. Which caster pair was most complex to merge? Any slot-count discrepancy from PHB tables?
2. Did `_merge_spellcasting()` refactor cleanly or require broader restructure?
3. Print `cleric 3 / wizard 3` slot tables for both primary and secondary for PM verification.

**V11 debrief:**
1. Are base companion stat blocks accurate vs PHB Monster Manual entries? Note any corrections.
2. Did effective companion level calculation handle the multiclass druid/ranger case correctly?
3. List which COMPANION_PROGRESSION rows were exercised by tests.

**V12 debrief:**
1. Which EF constants already existed? List pre-existing vs newly added.
2. Did `apply_racial_mods()` require structural changes or was it purely additive?
3. Note any PHB reference ambiguities (e.g., gnome SR value at chargen vs effective SR).

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
