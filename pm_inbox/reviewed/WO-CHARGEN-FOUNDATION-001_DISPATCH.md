# WO-CHARGEN-FOUNDATION-001 — Ability Scores, Races, and Weapon/Armor Catalog

**Type:** CODE
**Priority:** CHARGEN (parallel to BURST-001)
**Depends on:** WO-CHARGEN-RESEARCH-001 (ACCEPTED, gap register)
**Blocked by:** Nothing — ready to dispatch

---

## Target Lock

Build the three foundational chargen modules that every character creation flow needs: ability score generation, race definitions, and a weapon/armor catalog. All three are HIGH gaps from the chargen research gap register. When this lands, any martial character can be assembled programmatically instead of hand-crafted as raw entity dicts.

## Binary Decisions (all resolved)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | Where do race definitions live? | New file `aidm/data/races.py` | Data concern, next to equipment catalog |
| 2 | Where does ability score generation live? | New file `aidm/chargen/ability_scores.py` | Chargen module (new) |
| 3 | Where do weapon/armor definitions live? | Extend `aidm/data/equipment_catalog.json` + new dataclasses | Equipment catalog already exists |
| 4 | Weapon dataclass — new or reuse? | Reuse `aidm/schemas/attack.py::Weapon` for resolution; new `WeaponTemplate` in catalog for definitions | Weapon is resolution-focused; template is catalog-focused |
| 5 | Point-buy budget? | 25 points (standard D&D 3.5) | PHB p.169 DMG variant |

## Contract Spec

**Source:** PHB Ch.2 (Character Creation), PHB Tables 7-5/7-6 (Weapons/Armor), WO-CHARGEN-RESEARCH-001 gap register (GAP-CG-001, GAP-CG-002, GAP-CG-003)

### Part A: Ability Score Generation (GAP-CG-001)

New module: `aidm/chargen/ability_scores.py`

```python
def roll_4d6_drop_lowest() -> int:
    """Roll 4d6, drop the lowest die. Returns sum of top 3."""

def generate_ability_array(method: str = "4d6") -> dict[str, int]:
    """Generate 6 ability scores.

    Methods:
        "4d6" — Roll 4d6 drop lowest for each score
        "point_buy" — Start all at 8, spend 25 points per PHB point-buy table
        "standard" — Fixed array [15, 14, 13, 12, 10, 8]

    Returns:
        Dict with keys: str, dex, con, int, wis, cha
    """

def ability_modifier(score: int) -> int:
    """(score - 10) // 2 per PHB p.8."""

POINT_BUY_COST = {
    8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6, 15: 8, 16: 10, 17: 13, 18: 16,
}
```

Point-buy validation: total cost must not exceed 25 points. No score below 8 or above 18 before racial modifiers.

### Part B: Race Definitions (GAP-CG-002)

New module: `aidm/data/races.py`

All 7 PHB races with complete mechanical data:

| Race | Size | Speed | Ability Mods | Favored Class |
|------|------|-------|-------------|---------------|
| Human | Medium | 30 | None | Any |
| Elf | Medium | 30 | +2 DEX, -2 CON | Wizard |
| Dwarf | Medium | 20* | +2 CON, -2 CHA | Fighter |
| Halfling | Small | 20 | +2 DEX, -2 STR | Rogue |
| Gnome | Small | 20 | +2 CON, -2 STR | Bard |
| Half-Elf | Medium | 30 | None | Any |
| Half-Orc | Medium | 30 | +2 STR, -2 INT, -2 CHA | Barbarian |

*Dwarves: 20 ft speed is not reduced by medium/heavy armor.

```python
@dataclass(frozen=True)
class RaceDefinition:
    race_id: str                    # "human", "elf", "dwarf", etc.
    name: str                       # Display name
    size: str                       # "small" or "medium"
    base_speed: int                 # In feet
    ability_mods: dict[str, int]    # e.g., {"dex": 2, "con": -2}
    favored_class: str              # Class ID or "any"
    bonus_feats: int                # 1 for Human, 0 for others
    bonus_skill_points_per_level: int  # 1 for Human, 0 for others
    racial_traits: list[str]        # Descriptive trait IDs
    languages: list[str]            # Starting languages
    speed_ignores_armor: bool       # True for Dwarf
    provenance: str                 # "RAW"
    source_ref: str                 # "PHB p.XX"

RACE_REGISTRY: dict[str, RaceDefinition]  # All 7 races keyed by race_id

def get_race(race_id: str) -> RaceDefinition:
    """Look up race by ID. Raises KeyError if not found."""

def apply_racial_mods(scores: dict[str, int], race_id: str) -> dict[str, int]:
    """Apply racial ability modifiers to a score array. Returns new dict."""

def list_races() -> list[str]:
    """Return all available race_ids."""
```

Racial traits are stored as string IDs (e.g., `"darkvision_60"`, `"stonecunning"`, `"weapon_familiarity_dwarf"`). Mechanical effects of traits are OUT OF SCOPE — this WO defines the data, not the trait resolution pipeline.

### Part C: Weapon & Armor Catalog (GAP-CG-003)

Extend `aidm/data/equipment_catalog.json` with two new top-level sections: `"weapons"` and `"armor"`.

**Weapon catalog entries** (minimum 20 weapons covering all proficiency groups):

```json
"weapons": {
    "longsword": {
        "name": "Longsword",
        "damage_dice": "1d8",
        "critical_range": 19,
        "critical_multiplier": 2,
        "damage_type": "slashing",
        "weapon_type": "one-handed",
        "proficiency_group": "martial",
        "weight_lb": 4.0,
        "cost_gp": 15.0,
        "range_increment_ft": 0,
        "size_category": "Medium",
        "provenance": "RAW",
        "source_notes": "PHB Table 7-5 p.116"
    }
}
```

Required weapons (minimum set — add more if time allows):
- **Simple:** dagger, club, mace (heavy), morningstar, shortspear, longspear, javelin, light crossbow, sling
- **Martial:** longsword, rapier, battleaxe, warhammer, greatsword, longbow, shortbow, handaxe, short sword
- **Exotic:** dwarven waraxe, bastard sword

**Armor catalog entries** (all PHB armors):

```json
"armor": {
    "chain_shirt": {
        "name": "Chain Shirt",
        "armor_type": "light",
        "ac_bonus": 4,
        "max_dex_bonus": 4,
        "armor_check_penalty": -2,
        "arcane_spell_failure": 20,
        "weight_lb": 25.0,
        "cost_gp": 100.0,
        "base_speed_30": 30,
        "base_speed_20": 20,
        "size_category": "Medium",
        "provenance": "RAW",
        "source_notes": "PHB Table 7-6 p.123"
    }
}
```

Required armor:
- **Light:** padded, leather, studded leather, chain shirt
- **Medium:** hide, scale mail, chainmail, breastplate
- **Heavy:** splint mail, banded mail, half-plate, full plate
- **Shields:** buckler, light shield (wood/steel), heavy shield (wood/steel), tower shield

**New dataclasses** in `aidm/data/equipment_catalog_loader.py`:

```python
@dataclass(frozen=True)
class WeaponTemplate:
    """Weapon definition from the catalog (PHB Table 7-5)."""
    item_id: str
    name: str
    damage_dice: str
    critical_range: int         # Min roll to threaten (e.g., 19 for 19-20)
    critical_multiplier: int    # x2, x3, x4
    damage_type: str            # slashing, piercing, bludgeoning
    weapon_type: str            # light, one-handed, two-handed, ranged
    proficiency_group: str      # simple, martial, exotic
    weight_lb: float
    cost_gp: float
    range_increment_ft: int     # 0 for melee
    size_category: str          # Medium (adjust for Small creatures)
    provenance: str
    source_notes: str

    def to_weapon(self, damage_bonus: int = 0) -> "Weapon":
        """Convert catalog template to resolution Weapon."""

@dataclass(frozen=True)
class ArmorTemplate:
    """Armor definition from the catalog (PHB Table 7-6)."""
    item_id: str
    name: str
    armor_type: str             # light, medium, heavy, shield
    ac_bonus: int
    max_dex_bonus: int          # 99 for no limit
    armor_check_penalty: int    # Always negative or 0
    arcane_spell_failure: int   # Percentage (0-100)
    weight_lb: float
    cost_gp: float
    base_speed_30: int          # Speed for 30ft base
    base_speed_20: int          # Speed for 20ft base
    size_category: str
    provenance: str
    source_notes: str
```

Extend `EquipmentCatalog._load()` to parse `"weapons"` and `"armor"` sections. Add `get_weapon(item_id)`, `get_armor(item_id)`, `get_weapons_by_proficiency(group)`, `get_armor_by_type(type)`.

### Part D: New EF Field

Add to `aidm/schemas/entity_fields.py`:

```python
RACE = "race"  # Race ID string (e.g., "dwarf", "halfling")
```

## Implementation Plan

1. Create `aidm/chargen/` package (`__init__.py`)
2. Create `aidm/chargen/ability_scores.py` — score generation + point-buy + modifier calc
3. Create `aidm/data/races.py` — all 7 PHB races + registry + racial mod application
4. Extend `aidm/data/equipment_catalog.json` — add `"weapons"` and `"armor"` sections
5. Add `WeaponTemplate` and `ArmorTemplate` to `equipment_catalog_loader.py`
6. Extend `EquipmentCatalog` to load weapons and armor
7. Add `EF.RACE` to `entity_fields.py`
8. Write gate tests (see gate spec below)
9. Run full suite regression

### Out of Scope

- Character creation wizard/pipeline (GAP-CG-007 — future WO)
- Skill point allocation system (GAP-CG-006 — future WO)
- Spellcasting system (GAP-CG-008 — future WO, major scope)
- Masterwork modifier system (GAP-CG-004 — future WO)
- Animal companion system (GAP-CG-009 — future WO)
- Ammunition tracking (GAP-CG-005 — future WO)
- Character persistence/save/load (GAP-CG-013 — future WO)
- Racial trait mechanical effects (data only — trait resolution is a separate WO)
- Magic weapons/armor (future WO)
- Size-variant weapon damage (note: Small creatures use smaller damage dice per PHB p.114 — log as finding if not implemented)

## Gate Specification

**New gate:** Gate U (Chargen Foundation)

| Test ID | Assertion | Type |
|---------|-----------|------|
| U-01 | `roll_4d6_drop_lowest()` returns int in range 3-18 | range check |
| U-02 | `generate_ability_array("4d6")` returns dict with 6 keys | structure |
| U-03 | `generate_ability_array("standard")` returns [15,14,13,12,10,8] | exact values |
| U-04 | `generate_ability_array("point_buy")` validates 25-point budget | budget |
| U-05 | `ability_modifier(10)` == 0, `ability_modifier(18)` == 4, `ability_modifier(7)` == -2 | formula |
| U-06 | All 7 races exist in RACE_REGISTRY | completeness |
| U-07 | Dwarf has +2 CON, -2 CHA, speed 20, size medium | field check |
| U-08 | Halfling has +2 DEX, -2 STR, size small | field check |
| U-09 | Human has bonus_feats=1, bonus_skill_points_per_level=1 | field check |
| U-10 | `apply_racial_mods({"str":10,"dex":10,...}, "elf")` returns dex=12, con=8 | computation |
| U-11 | Weapon catalog has >= 20 weapons | count |
| U-12 | Armor catalog has >= 15 entries (armor + shields) | count |
| U-13 | `get_weapon("longsword")` returns correct damage/crit/type | field check |
| U-14 | `get_armor("full_plate")` returns ac_bonus=8, max_dex=1 | field check |
| U-15 | `WeaponTemplate.to_weapon()` produces valid `Weapon` instance | conversion |
| U-16 | `get_weapons_by_proficiency("simple")` returns only simple weapons | filter |
| U-17 | `get_armor_by_type("heavy")` returns only heavy armor | filter |
| U-18 | `EF.RACE` field constant exists | import check |
| U-19 | Dwarven waraxe is exotic proficiency group | field check |
| U-20 | Tower shield has max_dex_bonus=2, armor_check_penalty=-10 | field check |
| U-21 | Full suite regression | regression |

**Expected test count:** 21 new Gate U tests.

## Integration Seams

- `aidm/schemas/entity_fields.py` — Add `RACE` field (1 line)
- `aidm/schemas/attack.py` — Read-only. `Weapon` dataclass is the target for `WeaponTemplate.to_weapon()`
- `aidm/data/equipment_catalog.json` — Extend with weapons + armor sections
- `aidm/data/equipment_catalog_loader.py` — Add `WeaponTemplate`, `ArmorTemplate`, extend `EquipmentCatalog`
- `aidm/data/races.py` — NEW file, race definitions + registry
- `aidm/chargen/ability_scores.py` — NEW file, score generation
- `aidm/chargen/__init__.py` — NEW file, package init

## Assumptions to Validate

1. `aidm/schemas/attack.py::Weapon` accepts all fields that `WeaponTemplate.to_weapon()` needs to set — verify constructor signature
2. `EquipmentCatalog._load()` can be extended without breaking existing 35-item tests — verify no assertions on item count
3. The existing `equipment_catalog.json` `_meta.sources` already references PHB Tables 7-5 and 7-6 — good, data is pre-authorized

## Files to Read

1. `aidm/schemas/attack.py` — Weapon dataclass (verify all fields)
2. `aidm/data/equipment_catalog_loader.py` — EquipmentCatalog pattern
3. `aidm/data/equipment_catalog.json` — Existing catalog structure
4. `aidm/schemas/entity_fields.py` — Where to add RACE
5. `pm_inbox/reviewed/WO-CHARGEN-RESEARCH-001_DELIVERABLES.md` — Gap register + entity dict examples

## Preflight

```bash
python scripts/preflight_canary.py
python -m pytest tests/test_equipment_catalog.py -v
python -m pytest tests/ -x --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py
```

## Delivery Footer

**Commit requirement:** After all tests pass, commit changes with a descriptive message referencing this WO ID.
**Debrief format:** CODE — 500 words max, 5 sections + Radar (3 lines).
**Radar bank:** (1) Anything that broke unexpectedly, (2) Anything that was harder than expected, (3) Anything the next WO should know.
