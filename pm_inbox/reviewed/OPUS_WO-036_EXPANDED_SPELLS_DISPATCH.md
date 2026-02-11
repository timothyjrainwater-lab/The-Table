# WO-036: Expanded Spell Registry (~33 New Spells)
**Dispatched by:** Opus (PM)
**Date:** 2026-02-11
**Phase:** 2B.3 (Content Breadth)
**Priority:** Batch 2 (after WO-035)
**Status:** DISPATCHED
**Dependency:** WO-035 (Skills) — INTEGRATED (Concentration skill available)

---

## Objective

Expand the spell registry from 20 spells to ~53, covering levels 0-5 with comprehensive coverage of the most commonly used D&D 3.5e PHB spells. Each spell is purely declarative — add a SpellDefinition entry to SPELL_REGISTRY. The existing SpellResolver, DurationTracker, and AoE rasterizer handle resolution without code changes.

---

## Context

The current spell system (WO-014/WO-015) has:
- **SpellResolver** (1078 lines) — Full resolution pipeline: targeting, saves, damage, healing, conditions, STPs
- **DurationTracker** (492 lines) — Effect lifecycle, concentration management, expiration, dispelling
- **AoE rasterizer** (593 lines) — Burst/cone/line geometry per RQ-BOX-001
- **20 existing spells** in `aidm/schemas/spell_definitions.py`
- **Concentration skill** (WO-035) — `check_concentration_on_damage()` in spell_resolver.py

The SpellResolver is spell-agnostic — any SpellDefinition added to SPELL_REGISTRY is automatically resolved by the existing pipeline. This WO is primarily data entry with PHB rule accuracy.

---

## Package Structure

**Modified files:**
- `aidm/schemas/spell_definitions.py` — Add ~33 new SpellDefinition entries to SPELL_REGISTRY

**New files:**
- `tests/test_expanded_spells.py` — ~50 new tests

**Read-only references (DO NOT modify):**
- `aidm/core/spell_resolver.py` — SpellResolver, SpellCastIntent, CasterStats, TargetStats
- `aidm/core/duration_tracker.py` — DurationTracker, ActiveSpellEffect
- `aidm/core/aoe_rasterizer.py` — AoEShape, AoEDirection, rasterize_burst/cone/line
- `aidm/core/skill_resolver.py` — resolve_skill_check (for Concentration)
- `aidm/schemas/skills.py` — SkillID.CONCENTRATION

**Do NOT modify:** `aidm/core/spell_resolver.py`, `aidm/core/duration_tracker.py`, `aidm/core/aoe_rasterizer.py`, `aidm/core/play_loop.py`

---

## Existing 20 Spells (Already in SPELL_REGISTRY)

| Spell | Level | School | Type | PHB Page |
|-------|-------|--------|------|----------|
| Fireball | 3 | Evocation | Damage/Area (Burst 20ft) | p.231 |
| Burning Hands | 1 | Evocation | Damage/Area (Cone 15ft) | p.207 |
| Lightning Bolt | 3 | Evocation | Damage/Area (Line 120ft) | p.248 |
| Cone of Cold | 5 | Evocation | Damage/Area (Cone 60ft) | p.212 |
| Magic Missile | 1 | Evocation | Damage/Single (auto-hit) | p.251 |
| Scorching Ray | 2 | Evocation | Damage/Ray | p.274 |
| Acid Arrow | 2 | Conjuration | Damage/Ray | p.196 |
| Cure Light Wounds | 1 | Conjuration | Healing/Touch | p.215 |
| Cure Moderate Wounds | 2 | Conjuration | Healing/Touch | p.216 |
| Cure Serious Wounds | 3 | Conjuration | Healing/Touch | p.216 |
| Mage Armor | 1 | Conjuration | Buff/Self | p.249 |
| Bull's Strength | 2 | Transmutation | Buff/Touch | p.207 |
| Shield | 1 | Abjuration | Buff/Self | p.278 |
| Haste | 3 | Transmutation | Buff/Touch | p.239 |
| Hold Person | 3 | Enchantment | Debuff/Single | p.241 |
| Slow | 3 | Transmutation | Debuff/Area | p.280 |
| Blindness/Deafness | 2 | Necromancy | Debuff/Single | p.206 |
| Web | 2 | Conjuration | Debuff/Area | p.301 |
| Detect Magic | 0 | Divination | Utility/Self | p.219 |
| Light | 0 | Evocation | Utility/Touch | p.248 |

---

## New Spells to Add (~33)

### Level 0 Cantrips (4 new)

| Spell | School | Type | Target | Save | PHB Page | Notes |
|-------|--------|------|--------|------|----------|-------|
| Resistance | Abjuration | Buff/Touch | TOUCH | None | p.272 | +1 resistance bonus to saves, 1 min |
| Guidance | Divination | Buff/Touch | TOUCH | None | p.238 | +1 competence bonus to attack/save/skill, 1 min |
| Mending | Transmutation | Utility/Touch | TOUCH | None | p.253 | Repairs 1d4 HP to object, instantaneous |
| Read Magic | Divination | Utility/Self | SELF | None | p.269 | Read magical writing, 10 min/level |

### Level 1 (6 new)

| Spell | School | Type | Target | Save | PHB Page | Notes |
|-------|--------|------|--------|------|----------|-------|
| Bless | Enchantment | Buff/Area | AREA (Burst 50ft) | None | p.205 | +1 morale attack & fear saves, 1 min/level |
| Bane | Enchantment | Debuff/Area | AREA (Burst 50ft) | Will negates | p.203 | -1 morale attack & fear saves, 1 min/level |
| Grease | Conjuration | Debuff/Area | AREA (Burst 10ft) | Ref negates | p.237 | Balance DC 10 or fall prone, 1 round/level |
| Sleep | Enchantment | Debuff/Area | AREA (Burst 10ft) | Will negates | p.280 | Unconscious, 1 min/level, HD-limited |
| Entangle | Transmutation | Debuff/Area | AREA (Burst 40ft) | Ref partial | p.227 | Entangled condition, 1 min/level |
| Color Spray | Illusion | Debuff/Area | AREA (Cone 15ft) | Will negates | p.210 | Unconscious/blind/stunned by HD |

### Level 2 (7 new)

| Spell | School | Type | Target | Save | PHB Page | Notes |
|-------|--------|------|--------|------|----------|-------|
| Cure Moderate Wounds | — | — | — | — | — | Already exists |
| Invisibility | Illusion | Buff/Touch | TOUCH | None | p.245 | Invisible until attack, 1 min/level |
| Mirror Image | Illusion | Buff/Self | SELF | None | p.254 | 1d4+1 duplicates, 1 min/level |
| Cat's Grace | Transmutation | Buff/Touch | TOUCH | None | p.208 | +4 DEX, 1 min/level |
| Bear's Endurance | Transmutation | Buff/Touch | TOUCH | None | p.203 | +4 CON, 1 min/level |
| Owl's Wisdom | Transmutation | Buff/Touch | TOUCH | None | p.259 | +4 WIS, 1 min/level |
| Resist Energy | Abjuration | Buff/Touch | TOUCH | None | p.272 | Resistance 10 to chosen energy, 10 min/level |
| Silence | Illusion | Debuff/Area | AREA (Burst 20ft) | Will negates | p.279 | No sound, blocks verbal spells, 1 round/level |

### Level 3 (5 new)

| Spell | School | Type | Target | Save | PHB Page | Notes |
|-------|--------|------|--------|------|----------|-------|
| Dispel Magic | Abjuration | Utility/Single | SINGLE | None | p.223 | Caster level check to remove effects |
| Protection from Energy | Abjuration | Buff/Touch | TOUCH | None | p.266 | Absorbs 12/level energy damage (max 120) |
| Magic Circle against Evil | Abjuration | Buff/Self | AREA (Burst 10ft) | None | p.249 | +2 deflection AC, +2 resistance saves, 10 min/level |
| Fly | Transmutation | Buff/Touch | TOUCH | None | p.232 | Fly speed 60ft, 1 min/level |
| Stinking Cloud | Conjuration | Debuff/Area | AREA (Burst 20ft) | Fort negates | p.284 | Nauseated 1d4+1 rounds, 1 round/level, concentration |

### Level 4 (6 new)

| Spell | School | Type | Target | Save | PHB Page | Notes |
|-------|--------|------|--------|------|----------|-------|
| Cure Critical Wounds | Conjuration | Healing/Touch | TOUCH | None | p.215 | 4d8+level (max +20) |
| Stoneskin | Abjuration | Buff/Touch | TOUCH | None | p.284 | DR 10/adamantine (max 150 absorbed), 10 min/level |
| Wall of Fire | Evocation | Damage/Area | AREA (Line 20ft) | Ref half | p.298 | 2d4 fire within 10ft, 2d6+CL passing through, concentration |
| Dimension Door | Conjuration | Utility/Self | SELF | None | p.221 | Teleport up to 400ft+40ft/level |
| Greater Invisibility | Illusion | Buff/Touch | TOUCH | None | p.245 | Invisible even while attacking, 1 round/level |
| Ice Storm | Evocation | Damage/Area | AREA (Burst 20ft) | None | p.243 | 3d6 bludgeoning + 2d6 cold, no save |

### Level 5 (5 new)

| Spell | School | Type | Target | Save | PHB Page | Notes |
|-------|--------|------|--------|------|----------|-------|
| Hold Monster | Enchantment | Debuff/Single | SINGLE | Will negates | p.241 | Paralyzed, 1 round/level |
| Wall of Stone | Conjuration | Utility/Area | AREA (Line) | None | p.299 | Create stone wall, instantaneous (permanent) |
| Raise Dead | Conjuration | Healing/Touch | TOUCH | None | p.268 | Restore life, -1 level |
| Telekinesis | Transmutation | Utility/Single | SINGLE | Will negates | p.292 | Move 25lb/level, 1 round/level, concentration |
| Baleful Polymorph | Transmutation | Debuff/Single | SINGLE | Fort negates | p.202 | Transform into animal, permanent |

**Total new: 33 spells**
**Total after WO-036: 53 spells**

---

## SpellDefinition Pattern

Each new spell follows the exact existing pattern:

```python
SpellDefinition(
    spell_id="bless",
    name="Bless",
    level=1,
    school="enchantment",
    target_type=SpellTarget.AREA,
    range_ft=50,
    aoe_shape=AoEShape.BURST,
    aoe_radius_ft=50,
    aoe_direction=None,
    effect_type=SpellEffect.BUFF,
    damage_dice=None,
    damage_type=None,
    healing_dice=None,
    save_type=None,
    save_effect=SaveEffect.NONE,
    duration_rounds=10,  # 1 min/level at CL 1 = 10 rounds
    concentration=False,
    conditions_on_fail=(),
    conditions_on_success=("blessed",),
    auto_hit=False,
    requires_attack_roll=False,
    rule_citations=("PHB p.205",),
)
```

### Duration Encoding Convention

| Duration Text | duration_rounds Value |
|--------------|----------------------|
| Instantaneous | 0 |
| 1 round/level | 1 (per CL; SpellResolver scales) |
| 1 min/level | 10 (10 rounds = 1 minute at CL 1) |
| 10 min/level | 100 |
| Permanent | -1 |

**Note:** SpellResolver's `_apply_duration()` multiplies base duration by caster_level. Set `duration_rounds` to the base value (at CL 1).

### Concentration Spells

Spells with `concentration=True`:
- Stinking Cloud (level 3)
- Wall of Fire (level 4)
- Telekinesis (level 5)

These integrate with DurationTracker's concentration tracking and the WO-035 Concentration skill check on damage (`check_concentration_on_damage()` in spell_resolver.py, DC = 10 + damage taken).

---

## Special Cases

### 1. Spells with Unique Mechanics (Stub Notes)

Some spells have mechanics that don't map cleanly to existing SpellDefinition fields. For WO-036, implement what fits and document gaps:

| Spell | Special Mechanic | Implementation |
|-------|-----------------|----------------|
| Sleep | HD-limited targeting | Set conditions_on_fail=("unconscious",), note HD limit in rule_citations |
| Color Spray | Effect varies by HD | Simplify: conditions_on_fail=("stunned",) for all targets |
| Dispel Magic | Caster level check | Set effect_type=UTILITY, conditions_on_success=(), note caster check in citations |
| Mirror Image | Miss chance per image | Set conditions_on_success=("mirror_image",), note image count |
| Stoneskin | DR with absorption limit | Set conditions_on_success=("stoneskin",), note DR in citations |
| Dimension Door | Teleportation | Set target_type=SELF, range_ft=400, note teleport |
| Raise Dead | Restore life | Set effect_type=HEALING, healing_dice="0", note resurrection |
| Wall of Stone/Fire | Persistent terrain | Set target_type=AREA, note wall creation |

**Rule:** If a spell's mechanic cannot be expressed in SpellDefinition fields, set the closest approximation and add a rule_citations note documenting the gap. The resolution engine resolves what it can; un-expressible mechanics are tracked for future WOs.

### 2. Duplicate Prevention

Before adding a spell, verify it's not already in SPELL_REGISTRY. The 20 existing spells are listed above. Do not re-add them.

### 3. Condition Names

Use existing condition strings where they exist in the codebase. For new conditions, use lowercase_snake_case:
- Existing: `"paralyzed"`, `"slowed"`, `"blinded"`, `"entangled"`, `"mage_armor"`, `"hasted"`
- New: `"blessed"`, `"bane"`, `"invisible"`, `"mirror_image"`, `"stoneskin"`, `"nauseated"`, `"unconscious"`, `"stunned"`, `"flying"`, `"silenced"`

---

## Test Architecture (~50 tests)

### 1. Spell Registry Tests (10 tests)

```python
def test_spell_count():
    """Registry contains ~53 spells total."""
    assert len(SPELL_REGISTRY) >= 50

def test_all_spells_have_rule_citations():
    """Every spell has at least one PHB page citation."""
    for spell in SPELL_REGISTRY.values():
        assert len(spell.rule_citations) > 0

def test_spell_levels_0_through_5():
    """Spells exist at every level 0-5."""
    for level in range(6):
        spells = get_spells_by_level(level)
        assert len(spells) > 0, f"No spells at level {level}"

def test_all_schools_represented():
    """Major schools are represented."""
    schools = {s.school for s in SPELL_REGISTRY.values()}
    for school in ["evocation", "conjuration", "transmutation", "enchantment", "abjuration", "illusion", "necromancy", "divination"]:
        assert school in schools

# + 6 more: verify each new spell's fields match PHB data
```

### 2. Level 0-1 Spell Resolution Tests (10 tests)

```python
def test_resistance_buff():
    """Resistance: +1 resistance bonus to saves (PHB p.272)."""

def test_bless_area_buff():
    """Bless: +1 attack/fear saves in 50ft burst (PHB p.205)."""

def test_bane_will_save():
    """Bane: -1 attack/fear saves, Will negates (PHB p.203)."""

def test_sleep_will_save():
    """Sleep: unconscious, Will negates (PHB p.280)."""

def test_grease_ref_save():
    """Grease: prone on failed Ref save (PHB p.237)."""

def test_entangle_area():
    """Entangle: 40ft radius, entangled condition (PHB p.227)."""

def test_color_spray_cone():
    """Color Spray: 15ft cone, stunned on failed Will (PHB p.210)."""
# ... etc
```

### 3. Level 2-3 Spell Resolution Tests (12 tests)

```python
def test_invisibility_buff():
    """Invisibility: invisible condition, breaks on attack (PHB p.245)."""

def test_cats_grace_buff():
    """Cat's Grace: +4 DEX (PHB p.208)."""

def test_mirror_image_self():
    """Mirror Image: creates duplicates (PHB p.254)."""

def test_resist_energy_buff():
    """Resist Energy: energy resistance 10 (PHB p.272)."""

def test_silence_area_debuff():
    """Silence: 20ft burst, blocks verbal spells (PHB p.279)."""

def test_dispel_magic_utility():
    """Dispel Magic: utility spell, caster level check (PHB p.223)."""

def test_stinking_cloud_concentration():
    """Stinking Cloud: concentration spell, nauseated (PHB p.284)."""
    # Verify concentration=True in SpellDefinition
    # Verify DurationTracker tracks it as concentration effect

def test_fly_buff():
    """Fly: flying condition (PHB p.232)."""

def test_protection_from_energy():
    """Protection from Energy: absorb energy damage (PHB p.266)."""
# ... etc
```

### 4. Level 4-5 Spell Resolution Tests (10 tests)

```python
def test_cure_critical_wounds():
    """Cure Critical Wounds: 4d8+level healing (PHB p.215)."""

def test_stoneskin_buff():
    """Stoneskin: DR 10/adamantine (PHB p.284)."""

def test_wall_of_fire_damage():
    """Wall of Fire: fire damage in area, concentration (PHB p.298)."""
    # Verify concentration=True

def test_ice_storm_no_save():
    """Ice Storm: 3d6+2d6 damage, no save (PHB p.243)."""

def test_greater_invisibility():
    """Greater Invisibility: invisible while attacking (PHB p.245)."""

def test_hold_monster_will_save():
    """Hold Monster: paralyzed, Will negates (PHB p.241)."""

def test_baleful_polymorph():
    """Baleful Polymorph: fort negates, permanent (PHB p.202)."""

def test_telekinesis_concentration():
    """Telekinesis: concentration spell (PHB p.292)."""
    # Verify concentration=True

def test_dimension_door_self():
    """Dimension Door: self-targeting teleport (PHB p.221)."""

def test_raise_dead_healing():
    """Raise Dead: restore life, level 5 (PHB p.268)."""
```

### 5. Concentration Integration Tests (4 tests)

```python
def test_stinking_cloud_concentration_check():
    """Damage to caster triggers Concentration check for Stinking Cloud."""
    # Cast Stinking Cloud (concentration=True)
    # Deal damage to caster
    # Verify Concentration skill check triggered (DC = 10 + damage)

def test_wall_of_fire_concentration_maintained():
    """Wall of Fire persists when Concentration check succeeds."""

def test_telekinesis_concentration_broken():
    """Telekinesis ends when Concentration check fails."""

def test_non_concentration_spell_no_check():
    """Fireball (non-concentration) doesn't trigger Concentration check on damage."""
```

### 6. AoE Geometry Tests (4 tests)

```python
def test_bless_50ft_burst():
    """Bless: 50ft burst covers correct squares."""

def test_entangle_40ft_burst():
    """Entangle: 40ft burst covers correct squares."""

def test_color_spray_15ft_cone():
    """Color Spray: 15ft cone covers correct squares."""

def test_silence_20ft_burst():
    """Silence: 20ft burst covers correct squares."""
```

---

## Acceptance Criteria

- [ ] ~33 new SpellDefinition entries added to SPELL_REGISTRY
- [ ] Total spell count: ~53
- [ ] All spells levels 0-5 covered with representative selection
- [ ] Every spell has PHB page citation in rule_citations
- [ ] AoE spells use existing AoE rasterizer shapes (BURST, CONE, LINE)
- [ ] Duration tracking via existing DurationTracker (concentration flag set correctly)
- [ ] Concentration spells integrate with WO-035 Concentration skill check
- [ ] Healing spells use SpellEffect.HEALING with correct dice
- [ ] Buff/debuff spells set appropriate conditions
- [ ] No modifications to SpellResolver, DurationTracker, or AoE rasterizer
- [ ] All existing tests pass (3452+, 0 regressions)
- [ ] ~50 new tests with PHB page citations in docstrings
- [ ] D&D 3.5e rules only — no 5e spell mechanics

---

## Boundary Laws

| Law | Enforcement |
|-----|-------------|
| D&D 3.5e only | PHB page citations in every spell's rule_citations tuple; no 5e spell mechanics |
| EF.* constants | No new entity fields needed (spells use existing schema) |
| State mutation via deepcopy() | Spell effects applied through existing SpellResolver pipeline |
| RNG stream isolation | Spell resolution uses combat stream (existing) |
| Provenance | STPs generated by SpellResolver tagged [BOX] (existing behavior) |

---

## References

- Execution Plan: `docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md` lines 324-348
- Spell definitions: `aidm/schemas/spell_definitions.py`
- Spell resolver: `aidm/core/spell_resolver.py`
- Duration tracker: `aidm/core/duration_tracker.py`
- AoE rasterizer: `aidm/core/aoe_rasterizer.py`
- Concentration skill: `aidm/core/skill_resolver.py`, `aidm/schemas/skills.py`
- Existing spell tests: `tests/test_spell_resolver.py`
- Concentration tests: `tests/test_concentration_integration.py`
- Agent guidelines: `AGENT_DEVELOPMENT_GUIDELINES.md`
