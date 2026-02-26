# Work Order: WO-DATA-EQUIPMENT-001
**Artifact ID:** WO-DATA-EQUIPMENT-001
**Batch:** OSS Data Batch A
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**Source:** PCGen `rsrd_equip.lst` (OGL — `data/35e/wizards_of_the_coast/rsrd/basics/`)
**Dependency:** LST-PARSER-001 (must complete first)

---

## Summary

The engine has `EF.ARCANE_SPELL_FAILURE` as an entity field (added by Batch G), but
there is no canonical armor table from which ASF%, max DEX cap, and armor check penalty
are populated. Chargen and equip system currently set these values ad-hoc.

This WO populates `aidm/data/equipment_definitions.py` with a verified armor and weapon
catalog sourced from PCGen rsrd_equip.lst (OGL). The data is extracted by LST-PARSER-001
— this WO reads the parser output JSON and writes the Python registry.

**No new engine behavior.** This is the data layer. Engine WOs (WO-ENGINE-MAX-DEX-001,
WO-ENGINE-ACP-001) will query this registry in subsequent batches.

---

## Scope

**Files to create:**
- `aidm/data/equipment_definitions.py` — armor and weapon catalog

**Files to read/verify (do not modify):**
- `data/pcgen_extracted/armor_raw.json` — LST-PARSER-001 output (must exist first)
- `aidm/schemas/entity_fields.py` — confirm `EF.ARMOR_TYPE`, `EF.ARCANE_SPELL_FAILURE`, `EF.ARMOR_AC_BONUS`
- zellfaze mundane_items.json — cross-check weapon data (CC0 supplemental)

**Files out of scope:**
- Any resolver — equipping logic, chargen, ASF enforcement — out of scope

---

## Confirmed EF Fields (from Batch D + Batch G)

- `EF.ARMOR_TYPE` — string: "light" | "medium" | "heavy" | "none" (landed Batch D)
- `EF.ARMOR_AC_BONUS` — int: AC bonus from armor (landed Batch D)
- `EF.ARCANE_SPELL_FAILURE` — int: percentage 0-100 (landed Batch G)
- `EF.ARMOR_CHECK_PENALTY` — int: ACP value (negative, e.g., -6 for full plate) — **verify this field name in entity_fields.py**

---

## Assumptions to Validate (verify before writing)

1. Confirm `data/pcgen_extracted/armor_raw.json` exists and has expected structure
   from LST-PARSER-001. Read it before writing any code.
2. Confirm EF.ARMOR_CHECK_PENALTY field name in entity_fields.py — exact string.
   If it doesn't exist, flag as FINDING and add it to entity_fields.py (in scope).
3. Confirm armor TYPE tag values in PCGen output — are they "Light"/"Medium"/"Heavy"
   or lowercase? Normalize to match EF.ARMOR_TYPE convention.
4. Cross-check 3 armor entries against PHB table (PHB p.123) before writing the registry.
5. Confirm zellfaze mundane_items.json weapon schema — damage_dice, crit_range,
   crit_mult, damage_type. Use as supplemental cross-check only.

---

## Implementation

### `aidm/data/equipment_definitions.py`

```python
"""Armor and weapon catalog — populated from PCGen rsrd_equip.lst (OGL).

Source: PCGen/pcgen data/35e/wizards_of_the_coast/rsrd/basics/rsrd_equip.lst (OGL)
Cross-checked against PHB p.123-126 (armor table) and zellfaze mundane_items.json (CC0).
Facts are not copyrightable. This file contains only game mechanic values.
"""

from dataclasses import dataclass
from typing import Optional, Dict

@dataclass(frozen=True)
class ArmorDefinition:
    armor_id: str           # snake_case canonical ID
    name: str               # Display name
    armor_type: str         # "light" | "medium" | "heavy" | "shield"
    ac_bonus: int           # Armor bonus to AC
    max_dex_bonus: int      # Max DEX bonus while wearing (99 = no limit)
    armor_check_penalty: int  # Negative value (e.g., -6) or 0
    arcane_spell_failure: int  # Percentage 0-100
    weight_lb: float        # Weight in pounds

@dataclass(frozen=True)
class WeaponDefinition:
    weapon_id: str
    name: str
    damage_dice: str        # e.g., "1d8"
    crit_range: int         # e.g., 19 for 19-20/x2
    crit_mult: int          # e.g., 2
    damage_type: str        # "slashing" | "piercing" | "bludgeoning"
    weight_lb: float

ARMOR_REGISTRY: Dict[str, ArmorDefinition] = {
    "leather_armor": ArmorDefinition(
        armor_id="leather_armor",
        name="Leather Armor",
        armor_type="light",
        ac_bonus=2,
        max_dex_bonus=6,
        armor_check_penalty=0,
        arcane_spell_failure=10,
        weight_lb=15.0,
    ),
    # ... (12 PHB armor types + shields)
}

WEAPON_REGISTRY: Dict[str, WeaponDefinition] = {
    # ... (from zellfaze mundane_items.json, cross-checked against PHB)
}
```

---

## Acceptance Criteria

Write gate file `tests/test_data_equipment_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| EQ-001 | `ARMOR_REGISTRY["leather_armor"].arcane_spell_failure` | 10 |
| EQ-002 | `ARMOR_REGISTRY["chain_shirt"].max_dex_bonus` | 4 |
| EQ-003 | `ARMOR_REGISTRY["full_plate"].armor_check_penalty` | -6 |
| EQ-004 | `ARMOR_REGISTRY["full_plate"].arcane_spell_failure` | 35 |
| EQ-005 | `ARMOR_REGISTRY["chain_shirt"].armor_type` | "light" |
| EQ-006 | `ARMOR_REGISTRY["full_plate"].armor_type` | "heavy" |
| EQ-007 | `len(ARMOR_REGISTRY)` | ≥ 10 (sanity floor — PHB has 12 armor types) |
| EQ-008 | Request non-existent armor key | `KeyError` or `None` — no crash, documented behavior |

8 tests total. Gate label: DATA-EQUIPMENT-001.

---

## Pass 3 Checklist

1. Document any discrepancy found between PCGen rsrd_equip.lst values and PHB p.123-126
   table values — flag each as FINDING with specific entry and delta.
2. Document the `EF.ARMOR_CHECK_PENALTY` situation — does it exist? Was it added? Same
   for `EF.ARMOR_MAX_DEX` if needed.
3. Note KERNEL-14 (Effect Composition) — armor ASF stacks with other ASF sources
   (arcane focus, mithral, etc.). This WO only provides the base table; stacking is a
   future engine WO. Document the gap if it's not already tracked.
4. Weapons from zellfaze: document coverage (how many weapon entries successfully
   cross-checked). Flag any entries with suspect values.

---

## Session Close Condition

- [ ] `git add aidm/data/equipment_definitions.py tests/test_data_equipment_001_gate.py`
- [ ] (if EF.ARMOR_CHECK_PENALTY was added) `git add aidm/schemas/entity_fields.py`
- [ ] `git commit` with hash
- [ ] All 8 EQ tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
