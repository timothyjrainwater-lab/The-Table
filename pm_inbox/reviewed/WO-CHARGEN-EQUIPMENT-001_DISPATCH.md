# WO-CHARGEN-EQUIPMENT-001 — Phase 2 Equipment Integration

**Issued:** 2026-02-23
**Authority:** CHARGEN PHASE 1 COMPLETE (`build_character()` capstone accepted). Phase 2 scope: equipment + multiclass.
**Gate:** V7 — new gate. Target: 15-20 tests.
**Blocked by:** Nothing. Equipment catalog exists and is fully tested. Ready to dispatch.

---

## 1. Target Lock

Extend `build_character()` to assign starting equipment — weapons, armor, adventuring gear — based on class proficiencies and starting gold. After this WO, every built character has an inventory, a weapon, and an AC that reflects actual armor.

Right now `build_character()` returns `ac = 10 + dex_mod` regardless of class. A fighter comes out naked. This WO fixes that.

**Current gap:**
- `inventory` field: not populated
- `weapon` field: not populated
- `ac`: only dex mod, no armor
- `armor_check_penalty`: not set
- `encumbrance_load`: not calculated

**Source of truth for equipment data:** `aidm/data/equipment_catalog.json` + `aidm/chargen/equipment_catalog_loader.py`. Catalog is complete and tested. Integration only — do not modify catalog.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Equipment selection approach | Default kit per class | PHB Table 5-1 starting gold → purchase standard kit. Deterministic, testable. No RNG during chargen. |
| 2 | Starting gold | Use average value from PHB Table 5-1 per class (see spec below) | Deterministic for testing. Builder may add `use_rolled_gold: bool` param, default False. |
| 3 | Weapon selection | Best proficiency-appropriate weapon builder can afford from average gold | Fighter gets longsword, wizard gets quarterstaff, rogue gets short sword, etc. See class kit table below. |
| 4 | Armor selection | Best armor builder can afford within class restrictions | Fighter → chain mail. Wizard → none (arcane failure). Monk → none (class restriction). Druid → hide (metal restriction). |
| 5 | Encumbrance | Calculate but do not enforce (flag if over light load, don't block) | Informational only at chargen. Combat resolver enforces. |
| 6 | Inventory format | `inventory: List[Dict]` — `[{"item_id": str, "quantity": int}]` | Matches EF schema. |
| 7 | Primary weapon | `weapon` field: first Weapon object converted from catalog (primary only) | Consistent with how combat resolver expects it. |
| 8 | Spell component pouch | Include for all arcane/divine casters | Bard, cleric, druid, paladin, ranger, sorcerer, wizard all get spell_component_pouch in inventory. |
| 9 | Starting gold remainder | Track as `gp_remaining` in output (informational, not stored in EF) | Visible in debrief, useful for future shopping WO. |

---

## 3. Contract Spec

### 3.1 Function signature change

```python
def build_character(
    race: str,
    class_name: str,
    level: int = 1,
    ability_method: str = "4d6",
    ability_overrides: Optional[Dict[str, int]] = None,
    feat_choices: Optional[List[str]] = None,
    skill_allocations: Optional[Dict[str, int]] = None,
    spell_choices: Optional[List[str]] = None,
    starting_equipment: Optional[Dict[str, int]] = None,  # NEW: override default kit
    use_rolled_gold: bool = False,                         # NEW: if True, roll PHB dice
) -> Dict[str, Any]:
```

If `starting_equipment` is provided, use it directly (bypass default kit logic). This allows tests to inject specific loadouts.

### 3.2 Starting gold (PHB Table 5-1, average values)

| Class | Avg Gold (gp) | Default Primary Weapon | Default Armor |
|---|---|---|---|
| barbarian | 100 | greataxe (20gp) | hide (15gp) |
| bard | 125 | rapier (20gp) | leather (10gp) |
| cleric | 125 | heavy mace (12gp) | scale mail (50gp) |
| druid | 50 | quarterstaff (0gp) | hide (15gp) — no metal |
| fighter | 175 | longsword (15gp) | chain mail (150gp) |
| monk | 25 | unarmed (0gp) | none (class restriction) |
| paladin | 175 | longsword (15gp) | chain mail (150gp) |
| ranger | 150 | longsword (15gp) | leather (10gp) |
| rogue | 125 | short sword (10gp) | leather (10gp) |
| sorcerer | 75 | quarterstaff (0gp) | none (arcane failure) |
| wizard | 75 | quarterstaff (0gp) | none (arcane failure) |

These are hardcoded defaults. If catalog item IDs differ from above names, builder adjusts to match `equipment_catalog_loader.py` item IDs.

### 3.3 EF fields to populate

```python
# After equipment assignment:
entity[EF.INVENTORY] = [
    {"item_id": "longsword", "quantity": 1},
    {"item_id": "chain_mail", "quantity": 1},
    {"item_id": "backpack", "quantity": 1},
    # ... adventuring gear
]

entity[EF.WEAPON] = catalog.get("longsword").to_weapon(damage_bonus=str_mod)

# AC update: 10 + dex_mod + armor_ac_bonus (capped by max_dex if armor applies)
entity[EF.AC] = 10 + effective_dex_mod + armor_ac_bonus

entity[EF.ARMOR_CHECK_PENALTY] = armor.armor_check_penalty  # 0 if no armor

entity[EF.ENCUMBRANCE_LOAD] = total_inventory_weight  # lbs, float
```

EF constants — use whatever key names already exist in `aidm/entity_factory.py`. If `ARMOR_CHECK_PENALTY` or `ENCUMBRANCE_LOAD` don't exist as EF constants, add them.

### 3.4 Standard adventuring gear (all classes)

Every character gets, space/gold permitting:
- `backpack` × 1
- `bedroll` × 1
- `waterskin` × 1
- `torch` × 3 (or `lantern` + `oil` × 3 if gold allows)
- `rations` × 5 (trail rations, 1 day each — add `rations` to catalog if missing, 5sp each)

Casters additionally: `spell_component_pouch` × 1

Skip items the character can't afford after primary weapon + armor purchase.

### 3.5 AC calculation correction

```python
# Armor AC
armor_ac_bonus = 0
effective_dex_bonus = dex_mod
if armor_assigned:
    armor_ac_bonus = armor.ac_bonus
    if armor.max_dex_bonus is not None:
        effective_dex_bonus = min(dex_mod, armor.max_dex_bonus)

entity[EF.AC] = 10 + effective_dex_bonus + armor_ac_bonus
```

Monk: add Wisdom bonus to AC (class feature, PHB p.41) — `ac += wis_mod` if class is monk.

---

## 4. Implementation Plan

1. **Read** `aidm/chargen/builder.py` lines 1-376 to understand current structure
2. **Read** `aidm/chargen/equipment_catalog_loader.py` to confirm API: `get()`, `get_armor()`, item IDs
3. **Add** `_assign_starting_equipment(entity, class_name, level, catalog)` function in `builder.py`:
   - Look up gold from class table
   - Assign primary weapon → update `EF.WEAPON`
   - Assign armor → update `EF.AC`, `EF.ARMOR_CHECK_PENALTY`
   - Fill adventuring gear → update `EF.INVENTORY`
   - Calculate encumbrance → update `EF.ENCUMBRANCE_LOAD`
4. **Call** `_assign_starting_equipment()` from `build_character()` after ability scores and before return
5. **Add EF constants** if `ARMOR_CHECK_PENALTY` / `ENCUMBRANCE_LOAD` / `INVENTORY` / `WEAPON` don't exist
6. **Write tests** `tests/test_chargen_gate_v7.py` — Gate V7, 15-20 tests:
   - Fighter L1: has longsword, chain mail, correct AC (16 = 10+2dex_cap+4 for chain mail)
   - Wizard L1: has quarterstaff, no armor, AC = 10 + dex_mod
   - Monk L1: no armor, AC includes WIS mod
   - Druid L1: hide armor (no metal), check armor is not metal type
   - Rogue L1: leather armor, short sword, armor_check_penalty = 0
   - All 11 classes: `build_character(race, cls, 1)` — inventory is not empty, weapon is not None
   - Encumbrance: character with STR 8 near heavy load — flagged correctly
   - `starting_equipment` override: pass custom dict, bypasses defaults
   - Spell component pouch: wizard/cleric/druid/sorcerer/bard all have it
7. **Run** `pytest tests/test_chargen_gate_v7.py -v` — all pass
8. **Run** `pytest tests/` — zero regressions vs 6,448 baseline

---

## 5. Deliverables Checklist

- [ ] `aidm/chargen/builder.py` updated: `_assign_starting_equipment()` added, called from `build_character()`
- [ ] New EF constants added if missing: `INVENTORY`, `WEAPON`, `ARMOR_CHECK_PENALTY`, `ENCUMBRANCE_LOAD`
- [ ] All 11 classes have correct default weapon + armor assignment
- [ ] AC calculation updated to include armor bonus and max DEX cap
- [ ] Monk WIS-to-AC applied
- [ ] `tests/test_chargen_gate_v7.py` — 15+ tests, all PASS
- [ ] Zero regressions vs baseline

---

## 6. Integration Seams

- Do not modify `equipment_catalog_loader.py` or `equipment_catalog.json` — read only
- Do not modify any existing chargen tests (V1-V6) — they must still pass
- EF constants: add to `entity_factory.py` if missing, do not rename existing constants
- If `rations` is missing from catalog, add it to `equipment_catalog.json` only (5sp, 1 day, 0.5 lb)
- Combat resolver reads `entity[EF.WEAPON]` and `entity[EF.AC]` — do not change the field structure, only populate what's already expected

---

## 7. Assumptions to Validate

1. Catalog item IDs — confirm the exact string IDs for `longsword`, `chain_mail`, `quarterstaff`, `leather`, `hide`, `short_sword` in the catalog before writing the class kit table
2. `EF.WEAPON` — confirm what structure the combat resolver expects (Weapon object vs dict)
3. Monk WIS-to-AC — confirm this is not already applied elsewhere before adding it

---

## 8. Preflight

```bash
pytest tests/test_chargen_gate_v7.py -v  # gate passes
pytest tests/ --tb=no -q                  # zero new failures
```

---

## 9. Debrief Focus

1. **AC values** — for each class, what is the actual AC coming out of the builder at L1? List the table.
2. **Catalog gaps** — did any item (weapon, armor, gear) need to be added to `equipment_catalog.json`? What and why?

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
