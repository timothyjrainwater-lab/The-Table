# Work Order: DATA-CLASS-TABLES-001
**Artifact ID:** DATA-CLASS-TABLES-001
**Batch:** OSS Data Batch A
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**Source:** PCGen `rsrd_classes.lst` + hand-extract from `rsrd_abilities_class.lst` (OGL)
**Dependency:** LST-PARSER-001 (structural layer)

---

## Summary

Class progression data exists in the engine in scattered form:
- Spell slot tables: `aidm/chargen/spellcasting.py` ✅ (already implemented)
- Rage uses/day: `aidm/core/rage_resolver.py` ✅ (hardcoded table)
- Sneak attack dice: `aidm/core/sneak_attack.py` ✅ (formula `(rogue_level+1)//2`)
- Lay on hands pool: `aidm/core/lay_on_hands_resolver.py` ✅ (formula)

**What's missing:**
- Monk unarmed damage by level (UDAM: from rsrd_classes.lst)
- Canonical feature grant level registry (which feature unlocks at which level)
- No unified class table queryable from a single location

**This WO's job:**
1. Verify the existing spell slot tables in `spellcasting.py` against PCGen RSRD
2. Add monk UDAM table
3. Create `aidm/data/class_definitions.py` — canonical class progression registry
4. Do NOT rebuild what already works — verify, flag mismatches, add gaps

---

## Scope

**Files to create:**
- `aidm/data/class_definitions.py` — canonical class progression registry

**Files to read/verify (do not modify unless mismatch found):**
- `aidm/chargen/spellcasting.py` — existing spell slot tables
- `aidm/core/rage_resolver.py` — existing rage table
- `aidm/core/sneak_attack.py` — existing sneak attack formula
- `data/pcgen_extracted/class_tables_raw.json` — LST-PARSER-001 output

**Files out of scope:**
- Any resolver behavior — class features not in scope
- rsrd_abilities_class.lst full parsing — hand-extract the ~20 formulas only

---

## rsrd_abilities_class.lst — Hand-Extract Strategy

This 453KB file contains BONUS:VAR arithmetic formulas. Do NOT build a parser for it.
Read the file, find these specific formulas, verify against PHB, hardcode in the registry:

| Formula | PHB reference | Expected result |
|---------|---------------|-----------------|
| Rage uses/day | PHB p.25 Table 3-4 | Already in rage_resolver.py — verify only |
| Sneak attack dice | PHB p.50 | `(rogue_level+1)//2` — verify only |
| Lay on hands HP/day | PHB p.44 | `paladin_level * CHA_modifier` — verify only |
| Smite evil uses/day | PHB p.44 | 1 + extra per 5 levels — verify formula |
| Wild shape uses/day | PHB p.37 | 1+/day by level — verify table |
| Turn undead attempts/day | PHB p.159 | 3 + CHA modifier — verify formula |
| Bardic music uses/day | PHB p.29 | = bard level — verify |
| Stunning fist uses/day | PHB p.98 | = character level / 4 — verify |

For each: read the BONUS:VAR formula from the file, verify it matches PHB table, then
hardcode the verified value. Document in Pass 1 what you found in the file vs what's
in PHB.

---

## Assumptions to Validate (verify before writing)

1. Confirm `data/pcgen_extracted/class_tables_raw.json` CAST: format — is it a list
   of level-tuples for each class? What does "no spells at this level" look like (None? 0?)?
2. Compare PCGen CAST: data for Wizard level 1-5 against `spellcasting.py` SPELLS_PER_DAY_WIZARD.
   If they match → tables confirmed. If they don't → flag mismatches before writing.
3. Confirm UDAM: format in the parsed output — is it one value per class level, or
   one value per (class level × creature size)?
4. Check `aidm/data/` directory — does `class_definitions.py` already exist? If so,
   read it before writing.

---

## Implementation

### `aidm/data/class_definitions.py`

```python
"""Canonical class progression registry for D&D 3.5e PHB classes.

Sources:
- Structural layer: PCGen rsrd_classes.lst (OGL) via LST-PARSER-001
- Formula layer: hand-extracted from rsrd_abilities_class.lst (OGL), verified vs PHB
- Existing engine tables (spellcasting.py, rage_resolver.py) verified against PCGen

Facts are not copyrightable.
"""

from typing import Dict, List, Optional, Tuple

# Monk unarmed damage by level (PHB p.41, Table 3-10)
# (small creature size, medium creature size)
MONK_UDAM_BY_LEVEL: Dict[int, Tuple[str, str]] = {
    1:  ("1d4", "1d6"),
    2:  ("1d4", "1d6"),
    3:  ("1d4", "1d6"),
    4:  ("1d6", "1d8"),
    5:  ("1d6", "1d8"),
    # ... verified from PCGen UDAM: tag
    20: ("2d8", "2d10"),
}

# Feature grant levels by class — {class_name: {feature_id: grant_level}}
# Populated from PCGen ABILITY: tags in rsrd_classes.lst
CLASS_FEATURE_GRANTS: Dict[str, Dict[str, int]] = {
    "barbarian": {
        "fast_movement": 1,
        "illiteracy": 1,
        "rage": 1,
        "uncanny_dodge": 2,
        "trap_sense": 3,
        # ...
    },
    "rogue": {
        "sneak_attack": 1,
        "trapfinding": 1,
        "evasion": 2,
        "trap_sense": 3,
        # ...
    },
    # All 11 PHB base classes
}

# Class feature scaling formulas (verified against PHB, hand-extracted from
# rsrd_abilities_class.lst — NOT machine-parsed)
def rage_uses_per_day(barbarian_level: int) -> int:
    """PHB p.25 Table 3-4. Verified against PCGen formula (BarbarianLevel/4)+1."""
    # Already implemented in rage_resolver.py — this is the canonical source
    if barbarian_level >= 20: return 6
    if barbarian_level >= 16: return 5
    if barbarian_level >= 12: return 4
    if barbarian_level >= 8:  return 3
    if barbarian_level >= 4:  return 2
    return 1

def sneak_attack_dice(rogue_level: int) -> int:
    """Number of d6 dice for sneak attack (PHB p.50)."""
    return (rogue_level + 1) // 2

# ... (bardic music uses, smite evil uses, wild shape uses, etc.)
```

---

## Acceptance Criteria

Write gate file `tests/test_data_class_tables_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| CT-001 | `MONK_UDAM_BY_LEVEL[1]` | `("1d4", "1d6")` — small/medium (PHB p.41) |
| CT-002 | `MONK_UDAM_BY_LEVEL[20]` | `("2d8", "2d10")` |
| CT-003 | `rage_uses_per_day(1)` | 1 |
| CT-004 | `rage_uses_per_day(4)` | 2 |
| CT-005 | `rage_uses_per_day(20)` | 6 |
| CT-006 | `sneak_attack_dice(1)` | 1 |
| CT-007 | `sneak_attack_dice(10)` | 5 |
| CT-008 | `CLASS_FEATURE_GRANTS["barbarian"]["rage"]` | 1 (granted at level 1) |

8 tests total. Gate label: DATA-CLASS-TABLES-001.

---

## Pass 3 Checklist

1. **Spell slot verification result** — did PCGen CAST: data match spellcasting.py for
   all 7 spellcasting classes? List any level×class discrepancies as FINDINGs.
2. **UDAM format** — document exactly what PCGen UDAM: provides and how you mapped it
   to the (small, medium) tuple. If PCGen provides more size categories (tiny, large, etc.),
   document which two were used and why.
3. **Formula layer coverage** — list all BONUS:VAR formulas found in rsrd_abilities_class.lst
   for PHB classes. For each: what the formula says, what PHB says, whether they match.
   Flag any discrepancy as FINDING.
4. **CLASS_FEATURE_GRANTS completeness** — which classes were covered? Which feature
   grants were ambiguous in the PCGen data? Flag missing or unclear entries.
5. Note KERNEL-11 (Time/Calendar/Refresh) — class feature uses/day are the primary
   rest-economy state. This WO only provides the max values; the decrement/reset cycle
   is a future engine WO (rest system). Flag if not already tracked.

---

## Session Close Condition

- [ ] `git add aidm/data/class_definitions.py tests/test_data_class_tables_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 CT tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
- [ ] Spell slot table verification result documented (MATCH or FINDINGS list)
