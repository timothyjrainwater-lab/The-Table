# Work Order: WO-ENGINE-ARCANE-SPELL-FAILURE-001
**Artifact ID:** WO-ENGINE-ARCANE-SPELL-FAILURE-001
**Batch:** G (Dispatch #16)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.123 (Armor and Arcane Spellcasting), p.175 (Arcane Spell Failure table)

---

## Summary

Arcane spellcasters (wizards, sorcerers, bards) wearing armor risk spell failure (PHB p.123). Each armor type has an ASF% — a percentile chance that any arcane spell with a somatic (S) component fails entirely. Spell slot is consumed; no effect. Divine spellcasters are unaffected.

`EF.ARCANE_SPELL_FAILURE` already exists in `entity_fields.py` — it was registered as infrastructure in a prior batch. The field is set at chargen (0 for no armor; value for armored casters). The gap is that `spell_resolver.py` never checks it. This WO wires the field to the resolution path.

**Dependency:** `EF.ARMOR_TYPE` landed in Batch D. `has_somatic` field must be confirmed live on SpellDefinition — this is the blocker to check before writing.

---

## Scope

**Files in scope:**
- `aidm/core/spell_resolver.py` — add ASF% check before spell effect resolution

**Files read-only (verify, do not modify):**
- `aidm/schemas/entity_fields.py` — confirm `EF.ARCANE_SPELL_FAILURE` field name and type
- `aidm/data/spell_definitions.py` — confirm `has_somatic` field on SpellDefinition; confirm caster class field that identifies arcane vs. divine
- `aidm/chargen/builder.py` — confirm ARCANE_SPELL_FAILURE is set at chargen for armored arcane casters

**Files out of scope:**
- `chargen/builder.py` for writing — ASF% should already be set there; this WO only wires the runtime check
- Mithral armor ASF reduction — deferred; separate equipment WO
- Arcane Spell Failure for individual spells (scroll use, etc.) — out of scope this WO

---

## Assumptions to Validate (verify before writing)

1. Confirm `EF.ARCANE_SPELL_FAILURE` exists in entity_fields.py — value is int (0–100). **Already confirmed live from prior batch.**
2. Confirm `has_somatic: bool` field exists on SpellDefinition in `spell_definitions.py`. **Critical — if missing, this WO cannot proceed. Flag to Slate immediately.**
3. Confirm caster class identification — how does `spell_resolver.py` know if the caster is arcane vs. divine? Is there a `caster_class` field, or is the check by class name ("wizard", "sorcerer", "bard")? Document what's found.
4. Confirm `EF.ARCANE_SPELL_FAILURE` is set to 0 for divine casters and non-casters at chargen (so the check is safe for all entities).
5. Confirm no pre-existing ASF% check in `spell_resolver.py`.

---

## Implementation

### In `spell_resolver.py` — at spell resolution entry, before save/damage:

```python
# Arcane Spell Failure check (PHB p.123, p.175)
_asf = caster.get(EF.ARCANE_SPELL_FAILURE, 0)
if _asf > 0 and spell_def.has_somatic:
    _asf_roll = _d100()
    if _asf_roll <= _asf:
        # Spell fails — slot consumed
        events.append(Event(
            event_type="arcane_spell_failure",
            payload={
                "caster_id": caster_id,
                "spell_name": spell_def.name,
                "asf_chance": _asf,
                "roll": _asf_roll,
            }
        ))
        return world_state, next_event_id, events
```

**Note:** `_d100()` — confirm whether the RNG provider has a `d100()` method or if this should be `_d20() * 5` or similar. Use whatever the existing RNG protocol provides. Do not invent a new random function.

**Note:** Spells without somatic components (V-only spells, M-only spells) are unaffected by ASF%. Only spells with S component check this path.

---

## Acceptance Criteria

Write gate file `tests/test_engine_arcane_spell_failure_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| AF-001 | Arcane caster with ASF 25%; somatic spell; roll ≤ 25 | Spell fails; arcane_spell_failure event; slot consumed |
| AF-002 | Arcane caster with ASF 25%; somatic spell; roll > 25 | Spell resolves normally |
| AF-003 | Arcane caster with ASF 25%; non-somatic spell (V only) | No ASF check; spell resolves normally |
| AF-004 | Arcane caster with ASF 0% (unarmored) | No ASF check regardless of components |
| AF-005 | Divine caster (EF.ARCANE_SPELL_FAILURE = 0); somatic spell | No ASF check; spell resolves normally |
| AF-006 | ASF 100%: somatic spell always fails | Spell always fails (deterministic with seeded RNG) |
| AF-007 | ASF roll exactly at boundary (roll == ASF%) | Spell fails (≤ threshold is failure) |
| AF-008 | Entity with no EF.ARCANE_SPELL_FAILURE field | No crash; full damage applied (treat as 0%) |

8 tests total. Gate label: ENGINE-ARCANE-SPELL-FAILURE-001.

---

## Pass 3 Checklist

1. Confirm `has_somatic` field exists and is populated correctly for common spells — Magic Missile (V, S), Fireball (V, S, M), Mage Armor (V, S, M). Document any spells with wrong or missing somatic flag.
2. Confirm how arcane vs. divine is determined at runtime — if purely by `EF.ARCANE_SPELL_FAILURE == 0`, that's implicit and acceptable. Document the approach.
3. Note KERNEL-03 (Constraint Algebra) — ASF is a constraint imposed by equipment on the caster's spellcasting capability. Equipment state constrains action capability. Flag in Pass 3.
4. Flag whether `EF.ARCANE_SPELL_FAILURE` is correctly set at chargen for armored arcane casters — if chargen doesn't set it for light armor bards (15% ASF) or medium armor (35%), that's a FINDING.
5. Note whether d100 RNG is available via the existing RNGProvider — document the method used and whether a d100 helper needs to be added.

---

## Session Close Condition

- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_arcane_spell_failure_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 AF tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
