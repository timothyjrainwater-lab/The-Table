# Work Order: WO-ENGINE-CONCENTRATION-GRAPPLE-001
**Artifact ID:** WO-ENGINE-CONCENTRATION-GRAPPLE-001
**Batch:** H (Dispatch #17)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.69 (Concentration), p.175 (Concentration check table), p.156 (Grapple)

---

## Summary

A caster who is grappled (but not pinned) can still attempt to cast, but must succeed on a Concentration check or lose the spell (PHB p.175). An entangled caster faces a lower DC. Neither check is currently enforced — grappled casters cast freely.

PHB Concentration table:
- **Grappled or pinned** (PHB p.175): DC 20 + spell level
- **Entangled** (PHB p.175): DC 15 + spell level

PINNED casters are blocked entirely by WO-ENGINE-SOMATIC-COMPONENT-001 (Batch G) if the spell has a somatic component — this WO handles the grappled-not-pinned case, which is a Concentration check rather than an outright block.

Surfaces from FINDING-ENGINE-CONCENTRATION-OTHER-001 (Batch F debrief).

---

## Scope

**Files in scope:**
- `aidm/core/spell_resolver.py` — add Concentration check when caster is GRAPPLED or ENTANGLED

**Files read-only (verify, do not modify):**
- `aidm/schemas/conditions.py` — confirm GRAPPLED and ENTANGLED condition names (both confirmed live)
- `aidm/schemas/entity_fields.py` — confirm EF.CONDITIONS, EF.CONCENTRATION_BONUS
- `aidm/core/conditions.py` — confirm how conditions are queried on entities

**Files out of scope:**
- PINNED condition → somatic block (Batch G WO 3)
- Damage-during-casting Concentration (WO-ENGINE-CONCENTRATION-DAMAGE-001 in this batch)

---

## Assumptions to Validate (verify before writing)

1. Confirm `ConditionType.GRAPPLED` and `ConditionType.ENTANGLED` are live in conditions.py. **Already confirmed live.**
2. Confirm GRAPPLED does NOT block somatic casting outright — the PHB distinction is: GRAPPLED → Concentration check; PINNED → somatic blocked. Verify the somatic guard (Batch G) only fires on PINNED/BOUND, not GRAPPLED.
3. Confirm conditions are stored in `entity.get(EF.CONDITIONS, [])` or similar — find the exact data structure.
4. Confirm DC formulas: GRAPPLED = DC 20 + spell level; ENTANGLED = DC 15 + spell level (PHB p.175).
5. Confirm no pre-existing grapple/entangle Concentration check in `spell_resolver.py`.

---

## Implementation

### In `spell_resolver.py` — guard at spell resolution entry (after somatic guard, before damage):

```python
# Concentration check: grappled or entangled (PHB p.175)
_caster_conditions = caster_entity.get(EF.CONDITIONS, [])
_conc_dc_from_conditions = 0
_conc_reason = None

if "grappled" in _caster_conditions or "grappling" in _caster_conditions:
    _conc_dc_from_conditions = 20 + spell_def.level
    _conc_reason = "grappled"
elif "entangled" in _caster_conditions:
    _conc_dc_from_conditions = 15 + spell_def.level
    _conc_reason = "entangled"

if _conc_dc_from_conditions > 0:
    conc_bonus = caster_entity.get(EF.CONCENTRATION_BONUS, 0)
    conc_roll = _d20() + conc_bonus
    if conc_roll < _conc_dc_from_conditions:
        events.append(Event(
            event_type="concentration_failed",
            payload={"caster_id": caster_id, "roll": conc_roll,
                     "dc": _conc_dc_from_conditions, "reason": _conc_reason}
        ))
        return world_state, next_event_id, events
```

**Note:** If both GRAPPLED and ENTANGLED somehow apply, GRAPPLED takes precedence (higher DC). Use elif, not two separate ifs.

---

## Acceptance Criteria

Write gate file `tests/test_engine_concentration_grapple_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| CG-001 | Caster with GRAPPLED condition; casts 2nd level spell; fails Concentration | Spell lost; concentration_failed event; reason=grappled; DC=22 |
| CG-002 | Caster with GRAPPLED condition; casts 2nd level spell; succeeds | Spell resolves normally |
| CG-003 | Caster with ENTANGLED condition; casts 1st level spell; fails Concentration | Spell lost; DC=16; reason=entangled |
| CG-004 | Caster with ENTANGLED condition; succeeds Concentration | Spell resolves |
| CG-005 | Caster with no GRAPPLED/ENTANGLED condition; casts spell | No grapple Concentration check triggered |
| CG-006 | DC formula: GRAPPLED + 3rd level spell = DC 23 | DC confirmed 23 |
| CG-007 | DC formula: ENTANGLED + 3rd level spell = DC 18 | DC confirmed 18 |
| CG-008 | Caster with GRAPPLING (initiating grapple, not grappled) | Same Concentration check as GRAPPLED applies |

8 tests total. Gate label: ENGINE-CONCENTRATION-GRAPPLE-001.

---

## Pass 3 Checklist

1. Confirm the exact condition string comparison used — are conditions stored as ConditionType enum values or raw strings? Document what was found and whether a mismatch risk exists.
2. Confirm the interaction with Batch G's somatic guard — PINNED fires the somatic block before this check; GRAPPLED does not. Verify the guard order and document.
3. Note KERNEL-02 (Containment Topology) — grappling is a spatial containment constraint that restricts the action space of the contained actor. Flag in Pass 3.
4. Flag vigorous motion Concentration as a FINDING for next batch (DC 10 + spell level for vigorous motion, DC 20 for violent weather, DC varies for other causes).

---

## Session Close Condition

- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_concentration_grapple_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 CG tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
