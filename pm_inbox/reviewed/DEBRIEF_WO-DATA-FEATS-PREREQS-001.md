# Debrief — WO-DATA-FEATS-PREREQS-001 — Feat Prerequisite Registry

**WO ID:** WO-DATA-FEATS-PREREQS-001
**Builder:** Chisel
**Date:** 2026-02-28
**Commit:** ed7bdbf
**Gate result:** 8/8 (FP-001 – FP-008) PASS

---

## Pass 1 — Full Context Dump

### Files changed

| File | Change | Lines |
|------|--------|-------|
| `aidm/data/feat_definitions.py` | Created (new) | 1–270 |
| `tests/test_data_feats_prereqs_001_gate.py` | Created (new) | 1–67 |

### Schema used

`aidm/data/feat_definitions.py` — new data-layer file, separate from the runtime
`aidm/schemas/feats.py` (which uses `Dict[str, Any]` for prerequisites and is consumed
by feat_resolver.py).

```python
@dataclass(frozen=True)
class FeatDefinition:
    feat_id: str
    name: str
    feat_type: str                   # "combat", "general", "metamagic", "item_creation"
    prerequisites: Tuple[str, ...]   # human-readable strings
    fort_bonus: int = 0
    ref_bonus: int = 0
    will_bonus: int = 0
    attack_bonus: int = 0
    ac_bonus: int = 0
    damage_bonus: int = 0
    hp_bonus: int = 0
    initiative_bonus: int = 0
    skill_bonus: int = 0
```

`prerequisites` is a `Tuple[str, ...]` of human-readable strings matching the
debrief-specified format, e.g. `("STR 13", "Power Attack")`.

### What was populated

All feats with PHB prerequisites received non-empty tuples:

- Combat chain: `power_attack`, `cleave`, `great_cleave`, `improved_bull_rush`,
  `improved_overrun`, `improved_sunder`
- Defense chain: `dodge`, `mobility`, `spring_attack`, `whirlwind_attack`
- Ranged chain: `precise_shot`, `rapid_shot`, `manyshot`, `shot_on_the_run`, `far_shot`
- Weapon chain: `weapon_focus`, `greater_weapon_focus`, `weapon_specialization`,
  `greater_weapon_specialization`, `improved_critical`
- Two-weapon chain: `two_weapon_fighting`, `improved_two_weapon_fighting`,
  `greater_two_weapon_fighting`, `two_weapon_defense`
- Unarmed/monk: `stunning_fist`, `deflect_arrows`, `snatch_arrows`
- Combat maneuvers: `combat_expertise`, `improved_disarm`, `improved_feint`,
  `improved_grapple`, `improved_trip`
- Mounted: `mounted_combat`, `ride_by_attack`, `spirited_charge`, `trample`
- Spell feats: `greater_spell_focus`, `greater_spell_penetration`
- Class-dependent: `extra_turning`, `natural_spell`, `diehard`

Feats with no prerequisites (save feats, toughness, initiative, skill feats, combat
reflexes, blind-fight, spell_focus, spell_penetration, track, endurance, etc.) were
left with `prerequisites=()`.

Registry count: 52 feats — FP-008 (≥ 40) passes with margin.

### Pre-existing WO-1 debrief note

A previously staged debrief (`pm_inbox/reviewed/DEBRIEF_WO-DATA-FEATS-PREREQS-001.md`)
referenced commit `edcad35` which does not exist in git history. That was a pre-written
artifact from a session that did not complete. This execution is the actual delivery.
The staged debrief was superseded by this one.

---

## Pass 2 — PM Summary

Created `aidm/data/feat_definitions.py` as the content-pack data layer for feat
definitions (distinct from runtime `aidm/schemas/feats.py`). Schema uses `Tuple[str, ...]`
for human-readable prerequisites and flat integer bonus fields. 52 feats populated; ~35
have non-empty prerequisite tuples matching PHB. Gate file written; 8/8 FP tests pass.
Zero regressions. No engine resolver was modified.

---

## Pass 3 — Retrospective

**Drift caught:** `aidm/data/feat_definitions.py` was deleted in Batch V DDC WO as a
"dead file." WO-DATA-FEATS-PREREQS-001 targets recreating it as the content-pack data
layer. The runtime feat schema (`aidm/schemas/feats.py`) was correctly NOT touched.
Two separate schemas coexist by design: schemas/feats.py (runtime resolver input),
data/feat_definitions.py (content pack data pipeline).

**Consume-site:** This data file is not yet read by any resolver — same status as at
Batch A. Prerequisites are inert until WO-ENGINE-FEAT-VALIDATION-001 (future) implements
prerequisite enforcement. No `CONSUME_DEFERRED` finding raised (noted in prior
debrief as known limitation of data WO scope).

**Kernel touches:** None. WO is data-only, no resolver path affected.

---

## Spot-Check Pass

| Feat | PHB Page | Expected Prerequisites | Actual in Registry |
|------|----------|------------------------|-------------------|
| `power_attack` | p.98 | STR 13, BAB +1 | `("STR 13", "BAB +1")` — MATCH |
| `cleave` | p.92 | STR 13, Power Attack | `("STR 13", "Power Attack")` — MATCH |
| `rapid_shot` | p.99 | DEX 13, Point Blank Shot | `("DEX 13", "Point Blank Shot")` — MATCH |
| `diehard` | p.93 | Endurance | `("Endurance",)` — MATCH |
| `whirlwind_attack` | p.102 | DEX 13, INT 13, BAB +4, Combat Expertise, Dodge, Mobility, Spring Attack | `("DEX 13", "INT 13", "BAB +4", "Combat Expertise", "Dodge", "Mobility", "Spring Attack")` — MATCH |

No mismatches found.

---

## Radar

| ID | Severity | Status | Summary |
|----|----------|--------|---------|
| None | — | — | No new findings |

---

## Consume-Site Confirmation

- **Write site:** `aidm/data/feat_definitions.py` — `FEAT_REGISTRY` dict
- **Read site:** None (CONSUME_DEFERRED — data layer only, no resolver consumer yet)
- **Effect:** N/A until future WO-ENGINE-FEAT-VALIDATION-001
- **Gate proof:** FP-001–FP-008 prove data correctness only

**CONSUME_DEFERRED** — explicitly flagged. Data is present and correct; consumption
is a future engine WO.

---

## Coverage Map Update

No engine coverage map row affected — this is a data WO with no resolver change.
