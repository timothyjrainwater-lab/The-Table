# Work Order: WO-ENGINE-ENERGY-RESISTANCE-001
**Artifact ID:** WO-ENGINE-ENERGY-RESISTANCE-001
**Batch:** F (Dispatch #15)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.291 (Energy Resistance), Monster Manual (creature stat blocks)

---

## Summary

Energy resistance allows an entity to absorb the first N points of a specific energy type (fire, cold, acid, electricity, sonic) per damage instance. PHB p.291: "A creature with resistance to energy has the ability to ignore some damage of a certain type each time it takes such damage."

Currently no energy resistance field exists on entities and `spell_resolver.py` applies elemental damage with no resistance check. This is a frequent gap — fire-resistant creatures take full fire damage, cold-immune creatures take full cold damage. Every elemental spell interaction is wrong for any creature with resistance.

This WO adds the field and the guard. It does not add energy immunity (a separate field and separate WO).

---

## Scope

**Files in scope:**
- `aidm/schemas/entity_fields.py` — add `EF.ENERGY_RESISTANCE` field (dict: energy type → resistance value)
- `aidm/core/spell_resolver.py` — add resistance guard before applying elemental damage

**Files out of scope:**
- Immunity (separate from resistance — immunity reduces to 0 always; resistance reduces by N first)
- `aidm/chargen/builder.py` — chargen doesn't need updating for this WO; resistance is set on creature entities from their stat blocks, not chargen
- Any non-spell damage source (natural attacks, weapon damage) — out of scope; this WO covers spell damage only

---

## Assumptions to Validate (verify before writing)

1. Confirm `EF.ENERGY_RESISTANCE` does not already exist on entity_fields.py.
2. Confirm how spell damage type is tracked — is there a `damage_type` field on SpellDefinition or on the damage event payload? Identify the exact field name.
3. Confirm `spell_resolver.py` applies elemental damage at a point where a resistance deduction can be cleanly inserted before the final `total` is applied.
4. Confirm no pre-existing resistance guard in `spell_resolver.py`.

---

## Implementation

### 1. `aidm/schemas/entity_fields.py` — add field

```python
ENERGY_RESISTANCE = "energy_resistance"
# Value: dict[str, int] — e.g., {"fire": 10, "cold": 5}
# Absent key = no resistance to that type
# 0 value = no resistance (same as absent)
```

### 2. `aidm/core/spell_resolver.py` — resistance guard

After computing raw spell damage and before applying to target HP:

```python
# Energy resistance
_damage_type = spell_def.damage_type  # e.g., "fire", "cold", "acid", "electricity", "sonic"
if _damage_type:
    _resistance = _target_raw.get(EF.ENERGY_RESISTANCE, {}).get(_damage_type, 0)
    if _resistance > 0:
        total = max(0, total - _resistance)
```

**Note:** Resistance applies per damage instance, not per round. A spell with multiple damage rolls (e.g., multiple fire bolts) applies resistance to each roll independently. Confirm whether the engine resolves such spells as one or multiple damage instances and document accordingly.

---

## Acceptance Criteria

Write gate file `tests/test_engine_energy_resistance_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| ER-001 | Entity with fire resistance 10 takes 20 fire damage | 10 damage applied |
| ER-002 | Entity with fire resistance 10 takes 8 fire damage | 0 damage applied (resistance exceeds damage) |
| ER-003 | Entity with fire resistance 10 takes 20 cold damage | 20 damage applied (wrong type — no reduction) |
| ER-004 | Entity with no resistance takes 20 fire damage | 20 damage applied |
| ER-005 | Entity with fire resistance 5, cold resistance 10 takes fire damage | Only fire resistance applies |
| ER-006 | Entity with fire resistance 10 takes 20 fire damage; HP updated correctly | Final HP = start_hp - 10 |
| ER-007 | Resistance cannot reduce below 0 | 0 damage floor enforced |
| ER-008 | Entity with no ENERGY_RESISTANCE field (field absent) | Full damage applied; no crash |

8 tests total. Gate label: ENGINE-ENERGY-RESISTANCE-001.

---

## Pass 3 Checklist

1. Confirm spell damage type is correctly identified for common spells — Fireball should be "fire", Lightning Bolt should be "electricity", Cone of Cold should be "cold". Document any spells with wrong or missing damage type.
2. Note whether any existing creature entities in the data layer have ENERGY_RESISTANCE set — if none, that's a data gap to flag (creatures like Fire Elementals should have fire resistance/immunity).
3. Flag KERNEL-14 (Effect Composition) — energy resistance is the simplest case of effect interaction (incoming damage modified by entity property). More complex interactions (immunity vs resistance vs vulnerability stacking) will need a fuller Effect Composition model.
4. Note whether energy immunity needs to be a separate guard (immunity = always 0 regardless of damage amount) and flag as FINDING if the current state has no immunity field.

---

## Session Close Condition

- [ ] `git add aidm/schemas/entity_fields.py aidm/core/spell_resolver.py tests/test_engine_energy_resistance_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 ER tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
