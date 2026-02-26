# Work Order: WO-ENGINE-DEFENSIVE-CASTING-001
**Artifact ID:** WO-ENGINE-DEFENSIVE-CASTING-001
**Batch:** F (Dispatch #15)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.140 (Casting Defensively), p.175 (Concentration checks)

---

## Summary

When a caster is threatened in melee, casting a spell normally provokes an Attack of Opportunity (PHB p.140). The caster can instead cast defensively — declaring the intent before casting, then making a Concentration check (DC 15 + spell level). On success: no AoO. On failure: AoO still triggers AND the spell may be disrupted (failed Concentration check by 5+ means spell lost).

Current state: `aoo.py` triggers an AoO on spellcasting. There is no path for `DefensiveCastingIntent` to bypass this AoO. The PARTIAL entry in the coverage map confirms the gap: "AoO triggered on spellcasting; defensive casting intent not wired to bypass AoO."

---

## Scope

**Files in scope:**
- `aidm/schemas/intents.py` — add `DefensiveCastingIntent` or a `defensive: bool` flag on existing SpellCastIntent
- `aidm/core/aoo.py` — add check: if spell is cast defensively and Concentration succeeds, suppress AoO
- `aidm/core/spell_resolver.py` — add Concentration check for defensive casting path

**Files read-only (verify, do not modify):**
- `aidm/core/play_loop.py` — identify how SpellCastIntent is routed; determine whether a flag on the existing intent or a new intent type is cleaner
- `aidm/schemas/entity_fields.py` — confirm Concentration bonus field accessible on caster

**Files out of scope:**
- Counterspelling — separate mechanic
- Any other AoO trigger modification

---

## Assumptions to Validate (verify before writing)

1. Confirm `SpellCastIntent` schema — does it have a `defensive` field already? If not, is adding one cleaner than a new intent type?
2. Confirm how `aoo.py` determines whether spellcasting provokes AoO — find the check and understand the hook point.
3. Confirm Concentration bonus is accessible on the caster entity — what field? `EF.CONCENTRATION_BONUS` or derived from Spellcraft/skill ranks?
4. Confirm no pre-existing defensive casting path in `aoo.py` or `spell_resolver.py`.
5. Confirm the DC formula: DC = 15 + spell level (PHB p.175 Concentration table).

---

## Implementation

### Option A — Flag on existing intent (preferred if SpellCastIntent is clean)

Add `defensive: bool = False` to `SpellCastIntent`. Routing in `play_loop.py` already handles `SpellCastIntent` — no new branch needed. The flag is read in `aoo.py` and `spell_resolver.py`.

### Option B — New intent type

If `SpellCastIntent` is complex and adding a flag creates coupling risk, add `DefensiveCastingIntent` with a reference to the underlying spell intent. Builder makes the call based on what they find in the code.

### In `aoo.py`:

At the spellcasting AoO check point:
```python
if cast_is_defensive:
    # Run Concentration check: DC = 15 + spell_level
    conc_bonus = caster.get(EF.CONCENTRATION_BONUS, 0)
    conc_roll = _d20() + conc_bonus
    dc = 15 + spell_level
    if conc_roll >= dc:
        # Success: no AoO
        pass  # do not append AoO event
    else:
        # Failure: AoO still triggers; emit concentration failure event
        # Spell may be disrupted (handled in spell_resolver.py)
        _trigger_aoo(...)
        events.append(Event(event_type="concentration_failed", payload={...}))
else:
    # Standard cast: AoO triggers normally
    _trigger_aoo(...)
```

### In `spell_resolver.py`:

Check for concentration failure flag set by `aoo.py`. If concentration failed by 5 or more, the spell is lost (no effect, slot consumed):
```python
if intent.defensive and concentration_failed_badly:
    # Spell lost — emit spell_disrupted event
    events.append(Event(event_type="spell_disrupted", payload={...}))
    return world_state, next_event_id, events
```

---

## Acceptance Criteria

Write gate file `tests/test_engine_defensive_casting_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| DC-001 | Standard spell cast in threatened space | AoO triggered |
| DC-002 | Defensive cast; Concentration succeeds | No AoO; spell resolves |
| DC-003 | Defensive cast; Concentration fails | AoO triggered; concentration failure event emitted |
| DC-004 | Defensive cast; Concentration fails by 5+ | AoO + spell disrupted (spell lost, slot consumed) |
| DC-005 | Defensive cast DC = 15 + spell level | DC 16 for 1st-level spell, DC 18 for 3rd-level spell |
| DC-006 | Defensive cast success; spell effect resolves normally | Damage/effect identical to non-defensive cast |
| DC-007 | Non-threatened caster casts normally | No AoO regardless of defensive flag |
| DC-008 | High-Concentration-bonus caster; fails DC anyway | AoO and failure event still emitted correctly |

8 tests total. Gate label: ENGINE-DEFENSIVE-CASTING-001.

---

## Pass 3 Checklist

1. Confirm the Concentration bonus field — if it's a raw skill rank + CON mod calculation, document the formula and note whether it's currently computed correctly for all caster classes.
2. Confirm whether `aoo.py` and `spell_resolver.py` share state cleanly for the concentration failure flag, or whether a different architecture (event-based signal) is needed. Document the approach taken.
3. Note any other Concentration check triggers that are still PARTIAL or NOT STARTED (vigorous motion, violent weather, grappled, entangled) — log as FINDING for the next batch.
4. Flag KERNEL-03 (Constraint Algebra) — defensive casting is a behavioral constraint the caster imposes on themselves before casting. The declare-then-check pattern is a constraint-resolution sequence. Note this in Pass 3.

---

## Session Close Condition

- [ ] `git add aidm/schemas/intents.py aidm/core/aoo.py aidm/core/spell_resolver.py tests/test_engine_defensive_casting_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 DC tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
