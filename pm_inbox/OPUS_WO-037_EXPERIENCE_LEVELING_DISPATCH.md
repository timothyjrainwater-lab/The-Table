# WO-037: Experience and Leveling
**Dispatched by:** Opus (PM)
**Date:** 2026-02-11
**Phase:** 2B.4 (Content Breadth)
**Priority:** Batch 1 (immediate)
**Status:** DISPATCHED

---

## Objective

Implement CR-based XP calculation and level-up mechanics per D&D 3.5e DMG and PHB. Entities earn XP from defeated enemies, level up at thresholds, and gain mechanical benefits (hit dice, skill points, feat slots, ability score increases, spell slots).

---

## Package Structure

**New files:**
- `aidm/core/experience_resolver.py` — XP award calculation, level threshold checking, level-up application
- `aidm/schemas/leveling.py` — XPTable, LevelUpResult, ClassProgression dataclasses
- `tests/test_experience_resolver.py` — ~35 tests

**Modified files:**
- `aidm/schemas/entity_fields.py` — Add EF.XP, EF.LEVEL, EF.CLASS_LEVELS, EF.FEAT_SLOTS

**Do NOT modify:** `aidm/core/play_loop.py`, `aidm/core/combat_controller.py` (XP is awarded after combat, not during turns)

---

## XP Calculation (DMG Table 2-6, p.38)

XP awards depend on defeated creature's CR relative to party level:

```python
def calculate_xp_award(
    party_level: int,
    party_size: int,
    defeated_cr: float,
) -> int:
    """Calculate XP per party member for defeating a creature.

    Uses DMG Table 2-6 (p.38). XP is split equally among party members.
    CR values include fractional CRs (1/2, 1/3, 1/4, 1/6, 1/8).
    """
```

### DMG Table 2-6 Implementation

The table maps (party_level, CR_delta) to XP per character. Key structure:

- CR equal to party level = 300 XP per character (standard for 4-person party)
- CR +1 = 400, CR +2 = 500, etc.
- CR -1 = 200, CR -2 = 150, etc.
- Below a threshold, XP drops to 0 (too-easy encounters)
- Party size adjustment: base XP assumes 4 members, scale proportionally

Store the table as a lookup dict, not computed formula — the DMG table has specific values that don't follow a clean formula at all party levels.

---

## Level Thresholds (DMG Table 3-2, p.46)

| Level | XP Required |
|-------|------------|
| 1 | 0 |
| 2 | 1,000 |
| 3 | 3,000 |
| 4 | 6,000 |
| 5 | 10,000 |
| 6 | 15,000 |
| 7 | 21,000 |
| 8 | 28,000 |
| 9 | 36,000 |
| 10 | 45,000 |
| 11 | 55,000 |
| 12 | 66,000 |
| 13 | 78,000 |
| 14 | 91,000 |
| 15 | 105,000 |
| 16 | 120,000 |
| 17 | 136,000 |
| 18 | 153,000 |
| 19 | 171,000 |
| 20 | 190,000 |

---

## Level-Up Mechanics

```python
def check_level_up(entity: dict) -> Optional[LevelUpResult]:
    """Check if entity has enough XP to level up.

    Returns LevelUpResult if level up is available, None otherwise.
    """

def apply_level_up(
    entity: dict,
    level_up: LevelUpResult,
    rng: RNGManager,
) -> dict:
    """Apply level-up changes to entity. Returns new entity dict (deepcopy).

    Changes applied:
    1. Increment EF.LEVEL
    2. Roll hit die (class-dependent) + CON mod, add to EF.HP_MAX and EF.HP_CURRENT
    3. Add skill points (class-dependent + INT mod)
    4. Grant feat slot every 3rd level (3, 6, 9, 12, 15, 18)
    5. Grant ability score increase every 4th level (4, 8, 12, 16, 20)
    6. Update BAB per class progression
    7. Update save bonuses per class progression
    8. Update spell slots per class progression (if caster)
    """
```

### Class Progressions

For Phase 2, implement progressions for the 4 core classes (enough for playtesting):

| Class | Hit Die | BAB | Good Saves | Skill Points |
|-------|---------|-----|-----------|-------------|
| Fighter | d10 | Full (+1/level) | Fort | 2 + INT |
| Rogue | d6 | 3/4 | Ref | 8 + INT |
| Cleric | d8 | 3/4 | Fort, Will | 2 + INT |
| Wizard | d4 | 1/2 | Will | 2 + INT |

BAB progressions (PHB p.22):
- Full: +1 per level
- 3/4: +0, +1, +2, +3, +3, +4, +5, +6, +6, +7...
- 1/2: +0, +1, +1, +2, +2, +3, +3, +4, +4, +5...

Save progressions (PHB p.22):
- Good save: +2, +3, +3, +4, +4, +5, +5, +6, +6, +7...
- Poor save: +0, +0, +1, +1, +1, +2, +2, +2, +3, +3...

---

## Entity Fields

Add to entity_fields.py:

```python
EF.XP = "xp"                    # int: total experience points
EF.LEVEL = "level"              # int: total character level
EF.CLASS_LEVELS = "class_levels" # dict: {"fighter": 3, "rogue": 1}
EF.FEAT_SLOTS = "feat_slots"    # int: number of unspent feat slots
```

---

## Multi-Class XP Penalty (PHB p.60)

If a character's class levels differ by more than 1 (excluding favored class), apply -20% XP penalty per offending class. This is a computation on XP award, not a separate mechanic.

```python
def calculate_multiclass_penalty(class_levels: dict, favored_class: str) -> float:
    """Return XP multiplier (1.0 = no penalty, 0.8 = one offending class, etc.)."""
```

For Phase 2, implement the penalty calculation but don't enforce favored class (that requires race data which isn't in the entity schema yet). Default favored_class to the highest-level class.

---

## Acceptance Criteria

- [ ] XP calculation correct for all CR/level combinations in DMG Table 2-6 (levels 1-20, CRs 1/8 through 20)
- [ ] Fractional CRs handled correctly (1/2, 1/3, 1/4, 1/6, 1/8)
- [ ] Party size adjustment works (3-6 members tested)
- [ ] Level thresholds match DMG Table 3-2 exactly
- [ ] Level-up applies all mechanical changes atomically (deepcopy → modify → return)
- [ ] Hit die rolls use correct die per class (d10, d8, d6, d4) + CON mod, minimum 1 HP per level
- [ ] BAB progression matches PHB tables for all 4 classes through level 20
- [ ] Save progression matches PHB tables for all 4 classes through level 20
- [ ] Skill points granted correctly: (class_base + INT_mod) per level, minimum 1
- [ ] Feat slots at levels 1, 3, 6, 9, 12, 15, 18 (Fighter bonus feats NOT in this WO — that's content for WO-034 integration)
- [ ] Ability score increase at levels 4, 8, 12, 16, 20 (stores available increase, doesn't auto-apply)
- [ ] Multi-class XP penalty calculated correctly for 2-3 class combinations
- [ ] EF.XP, EF.LEVEL, EF.CLASS_LEVELS, EF.FEAT_SLOTS constants added to entity_fields.py
- [ ] RNG stream: combat (for hit die rolls)
- [ ] State mutation only through deepcopy (BL-020)
- [ ] All existing tests pass (3302+, 0 regressions)
- [ ] ~35 new tests

---

## Boundary Laws

| Law | Enforcement |
|-----|-------------|
| EF.* constants | New EF.XP, EF.LEVEL, EF.CLASS_LEVELS, EF.FEAT_SLOTS via entity_fields.py |
| State mutation via deepcopy() | Level-up creates new entity dict |
| RNG stream isolation | Hit die rolls use combat stream |
| D&D 3.5e only | DMG/PHB page citations; no 5e proficiency bonus or bounded accuracy |
| No Spark authority | XP and leveling are pure Box mechanics — no LLM involvement |

---

## What This WO Does NOT Include

- Spell slot progression for casters (tracks slots available at each level but doesn't populate known spells — that's WO-036 territory)
- Fighter bonus feats (fighter gets bonus combat feats at levels 1, 2, 4, 6, etc. — this is WO-034 integration after both WOs land)
- Favored class by race (requires race schema not yet built)
- Prestige classes
- Level adjustment for powerful races

---

## References

- Execution Plan: `docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md` lines 351-368
- DMG Table 2-6 (XP Awards): DMG p.38
- DMG Table 3-2 (Level Thresholds): DMG p.46
- PHB Chapter 3 (Class Progressions): PHB p.22+
- PHB p.60 (Multi-class XP penalty)
- Entity fields: `aidm/schemas/entity_fields.py`
- Agent guidelines: `AGENT_DEVELOPMENT_GUIDELINES.md`
