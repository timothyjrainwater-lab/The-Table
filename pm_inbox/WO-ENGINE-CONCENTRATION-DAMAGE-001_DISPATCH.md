# Work Order: WO-ENGINE-CONCENTRATION-DAMAGE-001
**Artifact ID:** WO-ENGINE-CONCENTRATION-DAMAGE-001
**Batch:** H (Dispatch #17)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.69 (Concentration skill), p.175 (Concentration check table)

---

## Summary

When a caster takes damage while in the process of casting a spell, they must make a Concentration check or lose the spell (PHB p.69). DC = 10 + damage taken + spell level. This is distinct from defensive casting (which is a pre-cast declaration) — this fires when the caster is hit by an attack or effect during their casting action.

Currently no such check exists. A caster can take 200 damage mid-cast and the spell resolves normally. This is the primary Concentration trigger — it comes up every time a caster is hit while casting.

Surfaces from FINDING-ENGINE-CONCENTRATION-OTHER-001 (Batch F debrief).

---

## Scope

**Files in scope:**
- `aidm/core/spell_resolver.py` — add Concentration check when caster took damage this turn before casting

**Files read-only (verify, do not modify):**
- `aidm/schemas/entity_fields.py` — confirm EF.CONCENTRATION_BONUS (live from Batch F), EF.HP_CURRENT
- `aidm/core/play_loop.py` — confirm how damage events are tracked within a turn; how does the resolver know the caster took damage this round?

**Files out of scope:**
- Grappled/entangled Concentration — separate WO (WO-ENGINE-CONCENTRATION-GRAPPLE-001 in this batch)
- Vigorous motion / violent weather — future batch
- Defensive casting — already implemented (Batch F)

---

## Assumptions to Validate (verify before writing)

1. Confirm EF.CONCENTRATION_BONUS is live in entity_fields.py. **Already confirmed live from Batch F.**
2. Determine how the engine tracks "damage taken this turn" — is there a damage event in the event log for the current turn, or a field on the entity? Find the cleanest way to detect mid-turn damage before spell resolution. Document the approach.
3. Confirm the DC formula: DC = 10 + damage dealt (this hit) + spell level (PHB p.175 table row 1).
4. Confirm spell level is accessible on the intent or SpellDefinition at the point of the check.
5. Confirm no pre-existing "took damage while casting" check in `spell_resolver.py`.

---

## Implementation

### Detection approach options (builder chooses):

**Option A — Event scan:** Before resolving the spell, scan the current-turn event log for `damage_dealt` events targeting the caster. Sum damage from this turn. If > 0, trigger Concentration check.

**Option B — Flag on entity:** A `took_damage_this_turn` field or `damage_taken_this_turn: int` set by `attack_resolver.py` when damage lands. `spell_resolver.py` reads this field. Cleaner but requires coordination across resolvers.

Builder documents the choice in Pass 3. Option A is preferred if event log is easily scannable; Option B if it results in cleaner code.

### In `spell_resolver.py` — before spell effect resolution:

```python
# Concentration check: took damage this turn (PHB p.69)
_damage_this_turn = _get_damage_taken_this_turn(caster_id, event_log)
if _damage_this_turn > 0:
    conc_bonus = caster_entity.get(EF.CONCENTRATION_BONUS, 0)
    conc_roll = _d20() + conc_bonus
    dc = 10 + _damage_this_turn + spell_def.level
    if conc_roll < dc:
        events.append(Event(
            event_type="concentration_failed",
            payload={"caster_id": caster_id, "roll": conc_roll, "dc": dc, "reason": "took_damage"}
        ))
        return world_state, next_event_id, events
    else:
        events.append(Event(
            event_type="concentration_maintained",
            payload={"caster_id": caster_id, "roll": conc_roll, "dc": dc}
        ))
```

---

## Acceptance Criteria

Write gate file `tests/test_engine_concentration_damage_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| CD-001 | Caster took 15 damage this turn; casts 3rd level spell; fails Concentration | Spell lost; concentration_failed event; reason=took_damage |
| CD-002 | Caster took 15 damage this turn; casts 3rd level spell; succeeds Concentration | Spell resolves; concentration_maintained event |
| CD-003 | Caster took 0 damage this turn; casts spell | No Concentration check triggered |
| CD-004 | DC formula: 15 damage + 3rd level spell = DC 28 | DC confirmed 28 in event payload |
| CD-005 | DC formula: 5 damage + 1st level spell = DC 16 | DC confirmed 16 |
| CD-006 | High-Concentration-bonus caster (CON mod + ranks = +12); 10 damage + 2nd level spell (DC 22) | Can still fail on low roll |
| CD-007 | Caster with no CONCENTRATION_BONUS field; took 10 damage | Treat as 0 bonus; no crash |
| CD-008 | Multiple hits same turn (10 + 8 = 18 damage total); 2nd level spell | DC = 10 + 18 + 2 = 30; total damage used |

8 tests total. Gate label: ENGINE-CONCENTRATION-DAMAGE-001.

---

## Pass 3 Checklist

1. Document the detection approach chosen (event scan vs. entity flag) and why. If a new field was needed, document it.
2. Confirm spell level is correctly read — is it from `spell_def.level` or `intent.heighten_to_level` when heightened? Document which is used and why.
3. Note KERNEL-03 (Constraint Algebra) — taking damage during casting creates a retroactive constraint on the spell action. The check fires after the hit resolves but before spell effect. Flag in Pass 3.
4. Flag vigorous motion and violent weather as FINDINGS for next batch — same DC table, different triggers, same pattern.

---

## Session Close Condition

- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_concentration_damage_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 CD tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
