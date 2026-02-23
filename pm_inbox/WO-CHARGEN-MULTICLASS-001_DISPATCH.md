# WO-CHARGEN-MULTICLASS-001 — Phase 2 Multiclass Assembly

**Issued:** 2026-02-23
**Authority:** CHARGEN PHASE 1 COMPLETE. Phase 2 scope: equipment + multiclass.
**Gate:** V8 — new gate. Target: 15 tests.
**Blocked by:** Nothing. Multiclass runtime scaffolding exists in `experience_resolver.py`. Ready to draft — dispatch sequentially with EQUIPMENT-001 or in parallel if second builder available.

---

## 1. Target Lock

Extend `build_character()` to assemble multiclass characters. A fighter 3 / wizard 2 built at character creation should have correct BAB, saves, class skills, feat count, skill points, and spellcasting from both classes — all in a single function call.

Right now `build_character()` only supports single-class characters. `class_levels` is always `{class_name: level}`. This WO adds `class_mix` parameter support for multi-class builds.

**Scope boundary:** Spell list merging (wizard + cleric dual-casting) is deferred — too complex, low frequency. This WO handles everything except multi-school spellcasting. A fighter/wizard gets wizard spells only; a cleric/druid would be deferred.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Parameter name | `class_mix: Optional[Dict[str, int]]` (e.g., `{"fighter": 3, "wizard": 2}`) | Clear, explicit, testable. Single class via original params still works. |
| 2 | BAB calculation | Highest BAB progression of all classes | PHB p.57: "use the best attack bonus". Fighter 3 / Wizard 2 → BAB 3 (fighter), not BAB 2 (wizard). |
| 3 | Save calculation | Each save: take best progression from any class at that level | PHB p.57. Fort from fighter, Ref from rogue, Will from cleric — each independently best. |
| 4 | Class skills | Union of all classes' class_skills lists | PHB p.57. Skills from any class are class skills. |
| 5 | Skill points | Sum of each class's skill points per level | PHB p.57. 4 (fighter L1) + 2 (wizard L1) = 6 total. INT mod × class count at L1 for max ranks. |
| 6 | Feats | Total feats for total character level (not per class) | PHB p.57. Level 1+3+6 etc. by character level, not class level. |
| 7 | HP | Sum of HD rolls (or avg) per class level separately | Fighter d10 per fighter level, Wizard d4 per wizard level. |
| 8 | Spellcasting | Only from caster classes; spell level by class level only | Fighter/Wizard → wizard spells at wizard level. Not merged. |
| 9 | Favored class | Accept `favored_class: Optional[str]` param — suppress XP penalty for that class | PHB p.56. No penalty if highest two class levels differ by ≤1 and one is favored. Informational only at chargen. |
| 10 | Validation | Raise ValueError if: total level > 20, unknown class, class_mix and class_name both provided | Fail loud at chargen time. |

---

## 3. Contract Spec

### 3.1 Function signature change

```python
def build_character(
    race: str,
    class_name: str,                                       # single class (existing)
    level: int = 1,                                        # single class level (existing)
    ability_method: str = "4d6",
    ability_overrides: Optional[Dict[str, int]] = None,
    feat_choices: Optional[List[str]] = None,
    skill_allocations: Optional[Dict[str, int]] = None,
    spell_choices: Optional[List[str]] = None,
    starting_equipment: Optional[Dict[str, int]] = None,
    use_rolled_gold: bool = False,
    class_mix: Optional[Dict[str, int]] = None,           # NEW: multiclass
    favored_class: Optional[str] = None,                  # NEW: favored class (PHB p.56)
) -> Dict[str, Any]:
```

**Dispatch logic:**
- If `class_mix` provided: ignore `class_name` + `level`, use `class_mix` dict
- If `class_mix` not provided: existing single-class path unchanged

### 3.2 BAB calculation (multiclass)

```python
# BAB progressions (per class level)
BAB_FULL = lambda lvl: lvl          # fighter, paladin, ranger, barbarian
BAB_3_4 = lambda lvl: (lvl * 3) // 4  # cleric, druid, monk, rogue, bard
BAB_1_2 = lambda lvl: lvl // 2     # wizard, sorcerer

# Multiclass BAB: take highest class's BAB, not sum
bab_values = [BAB_PROGRESSION[cls](class_levels[cls]) for cls in class_levels]
bab = max(bab_values)
```

Note: PHB says "use the best attack bonus" — do NOT sum BAB across classes.

### 3.3 Save calculation (multiclass)

```python
# Each save: best across all classes at their respective levels
# Good save progression: 2 + level/2
# Poor save progression: level/3

fort = max(fort_for_class(cls, lvl) for cls, lvl in class_levels.items())
ref  = max(ref_for_class(cls, lvl) for cls, lvl in class_levels.items())
will = max(will_for_class(cls, lvl) for cls, lvl in class_levels.items())
```

Add CON/DEX/WIS modifiers after.

### 3.4 HP calculation (multiclass)

```python
# Roll (or average) HD per class
# Average HD: d4=2.5, d6=3.5, d8=4.5, d10=5.5, d12=6.5
# L1 always gets max HD regardless of class

total_hp = 0
first_level = True
for cls, lvls in class_levels.items():
    for i in range(lvls):
        if first_level:
            total_hp += HD[cls]  # max at L1
            first_level = False
        else:
            total_hp += round(HD[cls] / 2.0 + 0.5)  # average

total_hp += con_mod * total_level
```

### 3.5 Skill points (multiclass)

```python
# PHB p.57: each class contributes its own skill points per level
# L1 gets ×4 skill points for each class taken at L1 (human gets +1 skill point/level)
total_skill_points = 0
for cls, lvls in class_levels.items():
    sp_per_level = CLASS_SKILL_POINTS[cls] + int_mod
    sp_per_level = max(1, sp_per_level)  # minimum 1
    l1_bonus = sp_per_level * 3  # ×4 at L1 = ×3 extra
    total_skill_points += (sp_per_level * lvls) + l1_bonus

if race == "human":
    total_skill_points += total_level  # human: +1/level
```

### 3.6 Output fields

```python
entity[EF.CLASS_LEVELS] = class_mix            # {"fighter": 3, "wizard": 2}
entity[EF.LEVEL] = sum(class_mix.values())     # 5
entity[EF.BAB] = bab
entity[EF.SAVE_FORTITUDE] = fort + con_mod
entity[EF.SAVE_REFLEX] = ref + dex_mod
entity[EF.SAVE_WILL] = will + wis_mod
entity[EF.HP_MAX] = total_hp
entity[EF.HP_CURRENT] = total_hp
# class_skills = union of all classes
# skill_ranks allocated normally
# spells from caster class(es) only
```

---

## 4. Implementation Plan

1. **Read** `aidm/chargen/builder.py` — understand all current single-class paths
2. **Read** `aidm/data/classes.json` — confirm BAB progression, save progression, HD, skill points per class
3. **Add** `_resolve_multiclass_stats(class_mix, ability_scores)` function:
   - BAB, saves, HP, skill points, feat count, class skills
4. **Add** `_merge_spellcasting(class_mix, ability_scores, level)` function:
   - Identify caster classes in mix
   - Single caster: use existing spellcasting logic at that class's level
   - Multiple casters: call each independently, store results keyed by class (advanced — may simplify to primary caster only for V8)
5. **Wire** multiclass path in `build_character()`:
   - If `class_mix` provided → call `_resolve_multiclass_stats()` → populate EF fields
   - Existing single-class path: unchanged, zero regression risk
6. **Write** `tests/test_chargen_gate_v8.py` — Gate V8, 15 tests:
   - Fighter 3 / Wizard 2: BAB=3, correct saves, HP sum, class skills union
   - Cleric 1 / Fighter 1: Fort = good (cleric), BAB = 1 (fighter)
   - Rogue 3 / Ranger 2: Ref = good (rogue), Evasion not present yet (class feature, deferred)
   - Human Fighter 2 / Wizard 2: human skill point bonus applied
   - Invalid: `class_mix={"fighter": 15, "wizard": 10}` → ValueError (total > 20)
   - Invalid: `class_mix={"fighter": 3}` + `class_name="wizard"` → ValueError (ambiguous)
   - Spells: Fighter 3 / Wizard 2 → wizard spell slots at level 2 only
   - Favored class: `favored_class="fighter"` stored/noted in output
   - All 5 two-class combos covering all save/BAB combo types
   - Single-class path: `build_character("human", "fighter", 5)` still works (regression)
7. **Run** `pytest tests/test_chargen_gate_v8.py -v` — all pass
8. **Run** `pytest tests/ --tb=no -q` — zero regressions vs baseline

---

## 5. Deliverables Checklist

- [ ] `aidm/chargen/builder.py`: `class_mix` + `favored_class` params added
- [ ] `_resolve_multiclass_stats()` function: BAB, saves, HP, skills, feats all correct
- [ ] `_merge_spellcasting()` or equivalent: caster class(es) handled correctly
- [ ] All 11 existing single-class V6 tests still pass (zero regression)
- [ ] `tests/test_chargen_gate_v8.py` — 15 tests, all PASS
- [ ] `class_levels` dict correctly reflects multiclass split

---

## 6. Integration Seams

- Do not modify V1-V7 gate tests
- `EF.CLASS_LEVELS` already a dict — multiclass just populates it with more than one key
- Combat resolver reads `entity[EF.BAB]` and `entity[EF.LEVEL]` — do not rename
- `experience_resolver.py` already has `calculate_multiclass_penalty()` — do not duplicate, do not call it at chargen time (chargen is not a level-up event)
- Spellcasting: if two caster classes both present (wizard + cleric), store spells from each class under separate keys — or, simplest approach: store wizard spells under `spell_slots`, defer dual-caster merging to a future WO. Document the decision in debrief.

---

## 7. Assumptions to Validate

1. `classes.json` — confirm it has BAB progression type (full/3-4/1-2), save progressions (good/poor per save), HD, and skill points per level for all 11 classes
2. Whether `EF.CLASS_LEVELS` is already a dict field or needs expanding
3. Whether `build_character()` uses class data from `classes.json` or has it hardcoded — affects where to add multiclass lookup logic

---

## 8. Preflight

```bash
pytest tests/test_chargen_gate_v8.py -v   # gate passes
pytest tests/test_chargen_gate_v6.py -v   # V6 regression check
pytest tests/ --tb=no -q                   # zero new failures overall
```

---

## 9. Debrief Focus

1. **BAB/save table** — for each multiclass combo tested, what were the resulting BAB and saves? Confirm they match PHB p.57 expected values.
2. **Multi-caster decision** — if wizard + cleric combo was tested, how did you handle spellcasting? Document the choice.

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
