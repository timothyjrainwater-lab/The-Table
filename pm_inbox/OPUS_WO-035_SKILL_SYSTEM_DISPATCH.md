# WO-035: Skill System (7 Skills)
**Dispatched by:** Opus (PM)
**Date:** 2026-02-11
**Phase:** 2B.2 (Content Breadth)
**Priority:** Batch 1 (immediate)
**Status:** DISPATCHED

---

## Objective

Implement 7 combat-adjacent skills per D&D 3.5e PHB Chapter 4. Each skill: check resolution with correct modifiers, opposed check support, integration with existing combat resolvers (AoO, spellcasting, initiative).

---

## Package Structure

**New files:**
- `aidm/core/skill_resolver.py` — Skill check resolution, opposed checks, DC computation
- `aidm/schemas/skills.py` — SkillDefinition dataclass, SkillID constants, rank schema
- `tests/test_skill_resolver.py` — ~40 tests

**Modified files:**
- `aidm/schemas/entity_fields.py` — Add `EF.SKILL_RANKS` (dict of skill_id -> rank), `EF.CLASS_SKILLS` (list)
- `aidm/core/aoo.py` — Tumble DC 15 check to avoid AoO on movement through threatened square
- `aidm/core/spell_resolver.py` — Concentration check when taking damage while casting

**Do NOT modify:** `aidm/core/play_loop.py`

---

## Skill List (7 Skills)

| Skill | PHB Page | Key Ability | Integration Point |
|-------|----------|------------|-------------------|
| Tumble | p.84 | DEX | AoO resolver — DC 15 to move through threatened without provoking |
| Concentration | p.69 | CON | Spell resolver — DC (10 + damage) to maintain spell when hit |
| Hide | p.76 | DEX | Opposed vs Spot — stealth in/before combat |
| Move Silently | p.79 | DEX | Opposed vs Listen — approach without detection |
| Spot | p.83 | WIS | Opposed vs Hide — detect hidden creatures |
| Listen | p.78 | WIS | Opposed vs Move Silently — hear approaching enemies |
| Balance | p.67 | DEX | DC based on surface — move on difficult surfaces without falling |

---

## Architecture

### SkillDefinition Schema

```python
@dataclass(frozen=True)
class SkillDefinition:
    skill_id: str           # "tumble", "concentration", etc.
    name: str               # "Tumble"
    key_ability: str        # "dex", "con", "wis"
    armor_check_penalty: bool  # True for Tumble, Hide, Move Silently, Balance
    trained_only: bool      # True for Tumble, Use Magic Device (not in this WO)
    phb_page: int
```

### Skill Check Resolution

```python
def resolve_skill_check(
    entity: dict,
    skill_id: str,
    dc: int,
    rng: RNGManager,
    circumstance_modifier: int = 0,
) -> SkillCheckResult:
    """Resolve a skill check against a fixed DC.

    Total = d20 + ability_mod + skill_ranks + misc_modifiers - armor_check_penalty
    """

def resolve_opposed_check(
    actor: dict,
    opponent: dict,
    actor_skill: str,
    opponent_skill: str,
    rng: RNGManager,
) -> OpposedCheckResult:
    """Resolve an opposed skill check (e.g., Hide vs Spot)."""
```

### Entity Fields

Add to entity_fields.py:
```python
EF.SKILL_RANKS = "skill_ranks"      # dict: {"tumble": 5, "hide": 3, ...}
EF.CLASS_SKILLS = "class_skills"    # list: ["tumble", "hide", "spot", ...]
```

Class skill max ranks = character level + 3.
Cross-class max ranks = (character level + 3) / 2.

### Skill Rank Computation

```
Total modifier = ability_mod + ranks + misc
  - ability_mod: from entity[EF.DEX_MOD], EF.CON_MOD, EF.WIS_MOD
  - ranks: from entity[EF.SKILL_RANKS][skill_id]
  - misc: circumstance_modifier parameter (cover, terrain, magic, etc.)
  - armor_check_penalty: subtracted if skill has armor_check_penalty=True
```

Armor check penalty is stored on entity as `EF.ARMOR_CHECK_PENALTY` (add to entity_fields.py if not present). For now, default to 0 if field not present on entity — the armor system isn't built yet.

---

## Integration Points

### 1. Tumble → AoO (aidm/core/aoo.py)

When an entity moves through a threatened square, if the entity has Tumble ranks > 0, allow a Tumble check (DC 15) to avoid provoking AoO. On success, no AoO. On failure, normal AoO provocation.

This hooks into the existing `check_aoo_provocation()` flow. The AoO resolver currently triggers AoO on movement through threatened squares — add a Tumble check gate before the trigger.

### 2. Concentration → Spell Resolver (aidm/core/spell_resolver.py)

When a caster takes damage during a round they are maintaining a concentration spell, require a Concentration check (DC = 10 + damage taken). On failure, the spell ends. On success, the spell continues.

This hooks into the existing `DurationTracker` which tracks concentration spells. The check happens when an `hp_changed` event fires for a concentrating caster.

### 3. Hide/Spot, Move Silently/Listen → Initiative (future)

These opposed checks affect surprise rounds and combat initiation. For WO-035, implement the opposed check resolution and test it in isolation. Integration with initiative and surprise mechanics is deferred to a future WO (these are non-trivial encounter-start mechanics).

### 4. Balance → Terrain Resolver (future)

Balance checks interact with difficult terrain and elevation. For WO-035, implement the skill check resolution with fixed DCs. Integration with terrain_resolver.py is deferred — the terrain system exists (CP-19) but the Balance hook point isn't defined yet.

---

## Acceptance Criteria

- [ ] All 7 skills resolve per PHB Chapter 4 (cite page numbers in tests)
- [ ] Opposed checks use correct formula: d20 + mod vs d20 + mod (higher wins, ties favor active checker)
- [ ] Tumble DC 15 check integrated with AoO resolver — trained entity can attempt to avoid AoO on move
- [ ] Concentration DC (10 + damage) check integrated with spell resolver — damage to concentrating caster triggers check
- [ ] Skill ranks respect class/cross-class distinction in validation
- [ ] Armor check penalty applied to appropriate skills (Tumble, Hide, Move Silently, Balance)
- [ ] Trained-only skills (Tumble) cannot be used untrained (0 ranks)
- [ ] EF.SKILL_RANKS and EF.CLASS_SKILLS constants added to entity_fields.py
- [ ] RNG stream: combat (for skill checks during combat)
- [ ] All existing tests pass (3302+, 0 regressions)
- [ ] ~40 new tests

---

## Boundary Laws

| Law | Enforcement |
|-----|-------------|
| EF.* constants | New EF.SKILL_RANKS, EF.CLASS_SKILLS fields via entity_fields.py |
| State mutation via deepcopy() | Concentration failure removes condition via deepcopy |
| RNG stream isolation | Skill checks use combat stream |
| D&D 3.5e only | PHB page citations in test docstrings; no 5e skill proficiency |

---

## References

- Execution Plan: `docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md` lines 299-320
- AoO resolver: `aidm/core/aoo.py`
- Spell resolver: `aidm/core/spell_resolver.py`
- Duration tracker: `aidm/core/spell_resolver.py` (DurationTracker class)
- Entity fields: `aidm/schemas/entity_fields.py`
- Agent guidelines: `AGENT_DEVELOPMENT_GUIDELINES.md`
