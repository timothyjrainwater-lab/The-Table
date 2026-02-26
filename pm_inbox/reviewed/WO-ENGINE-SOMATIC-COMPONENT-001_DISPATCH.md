# Work Order: WO-ENGINE-SOMATIC-COMPONENT-001
**Artifact ID:** WO-ENGINE-SOMATIC-COMPONENT-001
**Batch:** G (Dispatch #16)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.174 (Somatic Components), p.175 (Concentration)

---

## Summary

Spells with a somatic (S) component require at least one free hand (PHB p.174). A caster whose hands are fully occupied — bound, pinned in a grapple, or both hands holding a two-handed weapon with no hand free — cannot cast spells with a somatic component.

This WO is the S-component counterpart to Batch F's WO-ENGINE-VERBAL-SPELL-BLOCK-001 (V-component guard). The `has_somatic` field on SpellDefinition must be confirmed live before writing (it's the same dependency that WO-ENGINE-ARCANE-SPELL-FAILURE-001 relies on).

**Current state:** No somatic component check exists. A grappled, pinned, or bound caster can freely cast spells requiring hand gestures. This is a significant rules gap — pinning a caster in a grapple is one of the most effective anti-casting strategies in D&D 3.5e.

---

## Scope

**Files in scope:**
- `aidm/core/spell_resolver.py` — add somatic component guard at spell resolution entry

**Files read-only (verify, do not modify):**
- `aidm/data/spell_definitions.py` — confirm `has_somatic: bool` field on SpellDefinition
- `aidm/schemas/entity_fields.py` — confirm condition field names for GRAPPLED, PINNED, BOUND
- `aidm/schemas/conditions.py` — confirm what conditions block hand use

**Files out of scope:**
- Still Spell metamagic — that removes the somatic requirement entirely; it's a separate resolver path already tracked
- Arcane Spell Failure — separate WO (WO-ENGINE-ARCANE-SPELL-FAILURE-001 in this batch)
- Two-weapon fighting hand occupation — deferred; complex equipment tracking

---

## Assumptions to Validate (verify before writing)

1. Confirm `has_somatic: bool` field exists on SpellDefinition. **Critical — same blocker as ASF WO. If missing, flag to Slate immediately.**
2. Confirm the exact condition names for hand-blocking states in `entity_fields.py` or `conditions.py`: PINNED, GRAPPLED, BOUND — or equivalent. Do not invent field names.
3. Confirm which conditions block somatic casting per PHB:
   - PINNED (PHB p.310) — "pinned creatures can take no actions" → blocks somatic
   - GRAPPLED (grappling) — PHB p.156: can still cast but is subject to AoO and concentration check; **does not block somatic outright** (note this distinction)
   - BOUND — not a named PHB condition; check if engine has it
4. Confirm no pre-existing somatic guard in `spell_resolver.py`.

---

## Implementation

### Critical PHB Distinction (document in Pass 3):

- **PINNED** → cannot take actions → S-component casting blocked (spell_blocked event)
- **GRAPPLING** (not pinned) → can cast but provokes AoO and must make Concentration check → **not blocked here** (that's the Concentration-in-grapple WO, future batch)
- **BOUND** (tied up) → cannot take actions → S-component casting blocked

### In `spell_resolver.py` — guard at spell resolution entry:

```python
# Somatic component guard (PHB p.174)
if spell_def.has_somatic:
    caster_conditions = caster.get(EF.CONDITIONS, [])
    _blocking_conditions = {"pinned", "bound"}  # verify exact names
    _blocking = [c for c in caster_conditions if c in _blocking_conditions]
    if _blocking:
        events.append(Event(
            event_type="spell_blocked",
            payload={
                "caster_id": caster_id,
                "spell_name": spell_def.name,
                "reason": "somatic_component_blocked",
                "blocking_condition": _blocking[0],
            }
        ))
        return world_state, next_event_id, events
```

**Note:** Use the same `spell_blocked` event type as the verbal component guard (WO-ENGINE-VERBAL-SPELL-BLOCK-001). Reason field distinguishes verbal vs. somatic blocks.

---

## Acceptance Criteria

Write gate file `tests/test_engine_somatic_component_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| SC-001 | Caster with PINNED condition; somatic spell | Spell blocked; spell_blocked event with reason=somatic_component_blocked |
| SC-002 | Caster with PINNED condition; non-somatic spell (V only) | Spell NOT blocked by somatic guard (may be blocked by other guards) |
| SC-003 | Caster not pinned, not bound; somatic spell | Spell resolves normally |
| SC-004 | Caster with BOUND condition; somatic spell | Spell blocked; same event pattern |
| SC-005 | Caster grappling (not pinned); somatic spell | Spell NOT blocked by this guard (grapple → AoO + concentration, different path) |
| SC-006 | Spell with both V and S components; caster PINNED | Spell blocked (somatic guard fires; verbal guard would also fire — one block is sufficient) |
| SC-007 | Still Spell metamagic applied; caster PINNED | Still Spell removes somatic requirement → spell NOT blocked by somatic guard |
| SC-008 | Caster with no conditions; somatic spell | No crash; spell resolves normally |

8 tests total. Gate label: ENGINE-SOMATIC-COMPONENT-001.

---

## Pass 3 Checklist

1. Document the precise PHB ruling on GRAPPLED vs. PINNED for somatic casting — this is a common rules confusion point. GRAPPLED does not block somatic; PINNED does. Log as a FINDING if the engine's condition system doesn't distinguish these clearly.
2. Confirm `has_somatic` field is correctly populated for common spells — Fireball (V, S, M), Shield (V, S), Magic Missile (V, S). Document any wrong or missing values.
3. Note KERNEL-02 (Containment Topology) — a caster being grappled/pinned/swallowed is a containment state that constrains action space. Flag in Pass 3.
4. Note whether Still Spell correctly removes the somatic requirement before this guard runs — if Still Spell metamagic processing happens before component guards, the check is correctly skipped. Verify the order of operations and document.
5. Flag Concentration-in-grapple as a FINDING for future batch (NOT STARTED in coverage map): a grappled-but-not-pinned caster can cast, but must make a Concentration check (DC 20 + spell level per PHB p.175).

---

## Session Close Condition

- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_somatic_component_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 SC tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
