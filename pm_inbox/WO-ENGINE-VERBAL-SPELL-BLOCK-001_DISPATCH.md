# Work Order: WO-ENGINE-VERBAL-SPELL-BLOCK-001
**Artifact ID:** WO-ENGINE-VERBAL-SPELL-BLOCK-001
**Batch:** F (Dispatch #15)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.174 (Verbal components), p.58 (Silence spell)

---

## Summary

A gagged, silenced, or otherwise speech-blocked caster cannot cast spells with a Verbal (V) component (PHB p.174). The `has_verbal: bool = True` field on `SpellDefinition` landed in Batch D (WO-ENGINE-SILENT-SPELL-001). The blocker is gone — this WO closes the gap.

Current state: `spell_resolver.py` does not check whether the caster is speech-blocked before resolving a spell. A gagged caster casts freely.

**Rule:** If the caster has a condition that blocks verbal speech (SILENCED, GAGGED, or equivalent) AND the spell has `has_verbal=True`, the cast fails. No action consumed on a clean block — player must re-declare with a non-V spell or remove the condition.

---

## Scope

**Files in scope:**
- `aidm/core/spell_resolver.py` — add verbal block guard at spell resolution entry point

**Files read-only (verify, do not modify):**
- `aidm/data/spell_definitions.py` — confirm `has_verbal` is set on representative spells (Magic Missile=False, Fireball=True, etc.)
- `aidm/schemas/conditions.py` — confirm SILENCED condition exists or equivalent speech-block flag

**Files out of scope:**
- Parser layer — how the caster gets gagged/silenced is not this WO
- `aidm/schemas/intents.py` — no new intent types
- Any condition resolver

---

## Assumptions to Validate (verify before writing)

1. Confirm `has_verbal` field exists on `SpellDefinition` and is populated for common spells.
2. Confirm what condition/flag represents "cannot speak" on an entity — SILENCED condition, a boolean field, or similar. Identify the exact field name.
3. Confirm `spell_resolver.py` entry point — where the resolver first reads the spell definition, before damage/effect calculation.
4. Confirm no pre-existing verbal block guard in `spell_resolver.py`.
5. Confirm no pre-existing test covering this restriction.

---

## Implementation

### In `spell_resolver.py`:

At the top of the spell resolution path (after spell definition is loaded, before any effect resolution):

```python
# Verbal component block
if spell_def.has_verbal:
    _speech_blocked = entity.get(EF.SILENCED, False) or entity.get(EF.GAGGED, False)
    if _speech_blocked:
        events.append(Event(
            event_id=next_event_id,
            event_type="spell_blocked",
            payload={
                "actor_id": caster_id,
                "spell_id": spell_id,
                "reason": "verbal_component_blocked",
                "detail": "Caster cannot speak — Verbal component unavailable (PHB p.174).",
            }
        ))
        return world_state, next_event_id + 1, events
```

**Note on field names:** Verify the exact EF constant names for the speech-block condition before writing. If neither EF.SILENCED nor EF.GAGGED exists, document what does exist and use the correct name. Do not invent new fields — if the field doesn't exist, flag as blocker and stop.

---

## Acceptance Criteria

Write gate file `tests/test_engine_verbal_spell_block_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| VS-001 | Silenced caster casts Fireball (has_verbal=True) | `spell_blocked` event; reason=`verbal_component_blocked` |
| VS-002 | Silenced caster casts Magic Missile (has_verbal=False) | Spell resolves normally; no block event |
| VS-003 | Non-silenced caster casts Fireball | Spell resolves normally |
| VS-004 | Gagged caster casts a V spell | `spell_blocked` event emitted |
| VS-005 | Spell blocked → world_state unchanged | No HP delta, no resource consumption |
| VS-006 | Spell blocked → no action consumed | Caster action budget unchanged |
| VS-007 | Silence zone (if modeled) → V spell blocked | `spell_blocked` event (skip if silence zone not yet wired — note as FINDING) |
| VS-008 | Still Spell metamagic on V spell while silenced | Still Spell removes S requirement only — verbal still blocked; `spell_blocked` emitted |

8 tests total. Gate label: ENGINE-VERBAL-SPELL-BLOCK-001.

**VS-007 note:** If silence zone (environmental) is not yet tracked on entities, skip and log as FINDING-ENGINE-SILENCE-ZONE-001 in Pass 3.

---

## Pass 3 Checklist

1. Confirm `has_verbal` is correctly set for all spells in `spell_definitions.py` — flag any spell with obviously wrong value (e.g., a purely mental spell with has_verbal=True).
2. Confirm the speech-block condition field — document exact field name used and note any fragmentation if multiple fields could mean "cannot speak."
3. Note whether Silent Spell metamagic (already implemented) interacts correctly — Silent Spell removes the V requirement, so a silenced caster using Silent Spell should cast freely. Verify this interaction is coherent.
4. Note any other component checks that are still missing (S = somatic, M = material) — log as FINDING if found.

---

## Session Close Condition

- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_verbal_spell_block_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 VS tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
