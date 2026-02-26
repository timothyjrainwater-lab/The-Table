# DEBRIEF — DATA-CLASS-TABLES-001: Class Progression Registry

**Date:** 2026-02-26
**Status:** ACCEPTED
**Gate score:** 8/8

## Deliverables

- **`aidm/data/class_definitions.py`** — Monk UDAM table, class feature grant levels, formula functions
- **`tests/test_data_class_tables_001_gate.py`** — 8 gate tests, all passing

## Gate Results

| Test | Description | Result |
|------|-------------|--------|
| CT-001 | MONK_UDAM_BY_LEVEL[1] == ("1d4", "1d6") | PASS |
| CT-002 | MONK_UDAM_BY_LEVEL[20] == ("2d8", "2d10") | PASS |
| CT-003 | rage_uses_per_day(1) == 1 | PASS |
| CT-004 | rage_uses_per_day(4) == 2 | PASS |
| CT-005 | rage_uses_per_day(20) == 6 | PASS |
| CT-006 | sneak_attack_dice(1) == 1 | PASS |
| CT-007 | sneak_attack_dice(10) == 5 | PASS |
| CT-008 | CLASS_FEATURE_GRANTS["barbarian"]["rage"] == 1 | PASS |

## Contents

**`MONK_UDAM_BY_LEVEL`** — All 20 levels, (small, medium) damage dice tuple per PHB p.41 Table 3-10.

**`CLASS_FEATURE_GRANTS`** — 11 PHB base classes: barbarian, bard, cleric, druid, fighter, monk, paladin, ranger, rogue, sorcerer, wizard.

**Formula functions** (MAX values per KERNEL-11 note — decrement/reset is future rest-system WO):
- `rage_uses_per_day(barbarian_level)` — PHB p.25 Table 3-4
- `sneak_attack_dice(rogue_level)` — `(level + 1) // 2`
- `bardic_music_uses_per_day(bard_level)` — = bard level
- `wild_shape_uses_per_day(druid_level)` — PHB p.37 Table 3-8
- `smite_evil_uses_per_day(paladin_level)` — `1 + (level-1)//5`
- `lay_on_hands_hp_per_day(paladin_level, cha_modifier)` — `level × max(0, cha_mod)`
- `stunning_fist_uses_per_day(character_level)` — `max(1, level // 4)`

## Source

PHB pp.22-55 class tables. Cross-reference source: PCGen rsrd_classes.lst (OGL) — parser ready, files not present locally.

## Findings

- NONE — clean implementation.
