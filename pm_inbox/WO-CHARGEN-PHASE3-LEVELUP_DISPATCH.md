# WO-CHARGEN-PHASE3-LEVELUP — Character Advancement (Level-Up Flow)

**Issued:** 2026-02-23
**Authority:** CHARGEN PHASE 3 — post-Phase 2 natural next step. PM dispatch.
**Gate:** V9 (new gate — chargen level-up). Target: 15–20 tests.
**Blocked by:** Nothing. `build_character()` (V6) + equipment (V7) + multiclass (V8) all ACCEPTED.
**Track:** Chargen parallel track — no conflict with BURST-003/BURST-002/UI-06.

---

## 1. Target Lock

`build_character()` produces a correct L1–20 character from scratch. That's generation, not advancement. What's missing is **level-up**: taking an existing character entity and advancing it from level N to level N+1 with correct deltas.

A level-up applies:
- HP roll (hit die + CON mod, minimum 1; or max at first level of each new class)
- Feat slot trigger (every 3rd level: 3, 6, 9, 12, 15, 18 + human bonus at L1)
- Class features unlocked at the new level (paladin Smite improvements, wizard Bonus Feats, etc.)
- Spell slot increase for caster classes
- BAB/save progression increase
- Skill point award (class or cross-class rate)

The output is a **deterministic delta** applied to an existing entity dict — not a full regeneration.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Implementation style | New function `level_up(entity, class_name, level)` in `builder.py` | Separate from `build_character()` — don't touch the generation path |
| 2 | HP roll | Random (hit die roll + CON mod) with minimum 1 | PHB standard; test with seeded RNG for determinism |
| 3 | Level 1 of new class (multiclass) | Max hit die + CON mod | PHB rule: always max on first level of a class |
| 4 | Feat trigger | At levels 3, 6, 9, 12, 15, 18 + Human L1 bonus | Exact PHB table — `_feat_slots_at_level()` already implements this |
| 5 | Skill points | Class rate × INT mod award per level | Cross-class skills cost 2 points per rank |
| 6 | Class features | Unlock table per class at new level | Reference existing class progression data |
| 7 | Output shape | Returns delta dict, NOT full entity | Caller merges delta into entity; no silent mutation |
| 8 | Spell slots | Increment per caster class spell table | Reuse existing spell slot table from `build_character()` |
| 9 | Multiclass level-up | Specify which class gains the level | `level_up(entity, class_name="wizard", new_class_level=3)` |
| 10 | RNG seeding | Caller passes optional seed for test determinism | Production passes None (truly random); tests pass fixed seed |

---

## 3. Contract Spec

### 3.1 New Function Signature

```python
def level_up(
    entity: dict,
    class_name: str,
    new_class_level: int,
    feat_choices: list[str] | None = None,
    skill_allocations: dict[str, int] | None = None,
    spell_choices: list[str] | None = None,
    hp_seed: int | None = None,
) -> dict:
    """Advance entity by one level in class_name.

    Args:
        entity: Existing entity dict (from build_character or prior level_up).
        class_name: Which class gains the level (must be in entity's class mix).
        new_class_level: The new level reached in this class (e.g., 2 for L1→L2).
        feat_choices: Feats to add if a feat slot opens this level.
        skill_allocations: {skill_name: ranks_added} for new skill points.
        spell_choices: New spells learned (sorcerer/bard/wizard prepared list).
        hp_seed: Optional RNG seed for deterministic HP rolls (tests only).

    Returns:
        delta dict with keys:
          "hp_gained": int
          "feat_slots_gained": int
          "feats_added": list[str]
          "class_features_gained": list[str]
          "spell_slots": dict  (full updated slot table, or empty if non-caster)
          "skill_points_gained": int
          "bab": int  (updated total BAB)
          "saves": {"fort": int, "ref": int, "will": int}  (updated totals)
          "new_total_level": int
    """
```

### 3.2 Delta Merging

The caller is responsible for applying the delta to the entity:

```python
delta = level_up(entity, "fighter", 4)
entity[EF.HP_MAX] += delta["hp_gained"]
entity[EF.HP_CURRENT] += delta["hp_gained"]
entity[EF.FEATS] = entity.get(EF.FEATS, []) + delta["feats_added"]
# etc.
```

`level_up()` does NOT mutate the entity in place. It is a pure function.

### 3.3 HP Roll

```python
import random

def _roll_hp_for_level(hit_die: int, con_mod: int, is_first_class_level: bool,
                       seed: int | None = None) -> int:
    if is_first_class_level:
        return max(1, hit_die + con_mod)  # Max on first level of a class
    rng = random.Random(seed)
    roll = rng.randint(1, hit_die)
    return max(1, roll + con_mod)
```

### 3.4 Feat Slot Trigger

Reuse `_feat_slots_at_level(level, race)` already in `builder.py` (line 378).

```python
old_slots = _feat_slots_at_level(new_total_level - 1, race)
new_slots = _feat_slots_at_level(new_total_level, race)
feat_slots_gained = max(0, new_slots - old_slots)
```

### 3.5 Skill Points

```python
SKILL_POINTS_PER_LEVEL = {
    "fighter": 2, "paladin": 2, "barbarian": 4, "ranger": 6,
    "rogue": 8, "bard": 6, "cleric": 2, "druid": 4,
    "monk": 4, "sorcerer": 2, "wizard": 2,
}

def _skill_points_for_level(class_name: str, int_mod: int) -> int:
    base = SKILL_POINTS_PER_LEVEL.get(class_name, 2)
    return max(1, base + int_mod)
```

### 3.6 Class Features Table

Implement a per-class feature table: `CLASS_FEATURES: dict[str, dict[int, list[str]]]`

Example:
```python
CLASS_FEATURES = {
    "paladin": {
        2: ["divine_grace", "lay_on_hands"],
        3: ["aura_of_courage", "divine_health"],
        4: ["turn_undead", "special_mount"],
        # ...
    },
    "fighter": {
        2: ["bonus_feat"],
        4: ["bonus_feat"],
        # every even level
    },
    # ...
}
```

Builder looks up `CLASS_FEATURES[class_name].get(new_class_level, [])`.

---

## 4. Implementation Plan

1. **Read** `aidm/chargen/builder.py` — understand `_feat_slots_at_level()`, `_calculate_hp()`, `_skill_points_for_class()`, spell slot tables. Do not modify existing functions.
2. **Add** `CLASS_FEATURES` dict to `builder.py` (after existing constants) — per-class feature unlocks by class level. PHB tables, L1-20 for all 11 classes.
3. **Add** `_roll_hp_for_level()` helper — seeded RNG, minimum 1, max on first class level.
4. **Add** `_skill_points_for_level()` helper — per-class rate + INT mod.
5. **Add** `level_up()` public function — assemble delta, call helpers, return pure dict.
6. **Create** `tests/test_chargen_gate_v9.py` (Gate V9) — 15–20 tests covering all delta fields.
7. **Preflight** — Gate V9 all PASS, V1-V8 zero regressions.

---

## 5. Test Spec (Gate V9 — target 15 tests)

| ID | Test | Assertion |
|----|------|-----------|
| V9-01 | Fighter L1→L2 | hp_gained ≥ 1, bab=2, saves correct, no feat slot |
| V9-02 | Fighter L2→L3 | feat_slots_gained=1 (every 3rd level) |
| V9-03 | Fighter L3→L4 | bonus_feat in class_features_gained |
| V9-04 | Wizard L1→L2 | spell_slots updated (L2 wizard table) |
| V9-05 | Paladin L1→L2 | divine_grace + lay_on_hands in class_features_gained |
| V9-06 | Rogue L1→L2 | skill_points_gained=9 (8 base + 1 INT, example) |
| V9-07 | Human fighter L1→L2 | No extra feat (human bonus already at L1) |
| V9-08 | HP minimum 1 | CON -3, d4 hit die: hp_gained ≥ 1 |
| V9-09 | HP seeded determinism | Same seed → same hp_gained, both calls identical |
| V9-10 | Multiclass: fighter3/wizard level_up wizard→L3 | BAB from fighter3+wizard3, saves combined |
| V9-11 | First class level max HP | level_up with is_first=True → max hit die + CON mod |
| V9-12 | Feat choices applied | feat_choices=["power_attack"] → feats_added=["power_attack"] |
| V9-13 | Feat choices ignored if no slot | feat_choices provided, no slot → feats_added=[] |
| V9-14 | level_up is pure (no mutation) | Original entity dict unchanged after level_up() |
| V9-15 | Invalid class raises ValueError | level_up with class_name not in entity → ValueError |

---

## 6. Deliverables Checklist

- [ ] `CLASS_FEATURES` dict in `builder.py` — all 11 classes, PHB-accurate, L1-20
- [ ] `_roll_hp_for_level()` helper — seeded RNG, minimum 1, first-class-level max
- [ ] `_skill_points_for_level()` helper — per-class rate table + INT mod
- [ ] `level_up()` public function — pure, returns delta dict
- [ ] `tests/test_chargen_gate_v9.py` — Gate V9, 15+ tests
- [ ] Gate V9 all PASS
- [ ] V1-V8 zero regressions (`pytest tests/test_chargen_gate_v*.py`)

---

## 7. Integration Seams

- **Only file modified:** `aidm/chargen/builder.py` — new functions appended, nothing existing changed
- **New test file:** `tests/test_chargen_gate_v9.py` — Gate V9
- **Do not modify:** `build_character()`, `_feat_slots_at_level()`, `_calculate_hp()` — existing chargen path untouched
- **No WorldState changes** — level_up operates on entity dicts only; caller decides when/how to apply to WorldState
- **No play.py changes** — wiring level_up into the game loop is a future WO

---

## 8. Preflight

```bash
pytest tests/test_chargen_gate_v9.py -v
pytest tests/test_chargen_gate_v*.py -v
pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

All must exit 0.

---

## 9. Debrief Focus

1. **CLASS_FEATURES table** — which class features were the hardest to locate in PHB? Any gaps or ambiguities?
2. **HP minimum edge cases** — any cases where the minimum-1 rule produced unexpected results?
3. **Multiclass level_up** — how did BAB and saves combine when advancing one class in a multiclass character? Show a test case output.

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
