# WO-ENGINE-IMPROVED-TRIP-001 — Improved Trip + Improved Sunder AoO Suppression

**WO ID:** WO-ENGINE-IMPROVED-TRIP-001
**Type:** Engine feature
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Lifecycle:** DISPATCH-READY
**Batch:** Engine Batch N
**Gate label:** ENGINE-IMPROVED-TRIP
**Gate file:** `tests/test_engine_improved_trip_gate.py`
**Gate count:** 8 tests (IT-001 – IT-008)

---

## Gap Verification (coverage map confirmed PARTIAL 2026-02-26)

| Feat | PHB | Status |
|------|-----|--------|
| Improved Trip | p.96/158 | PARTIAL — feat registered; AoO suppression + free attack NOT wired |
| Improved Sunder | p.96/158 | PARTIAL — feat registered; AoO suppression NOT wired |

Pattern identical to Batch L (Improved Disarm, Improved Grapple, Improved Bull Rush). Reference those implementations in `maneuver_resolver.py` and `aoo.py` for the exact pattern.

**Assumptions to Validate before writing:**
1. Confirm `aoo.py` checks for Improved Disarm/Grapple/Bull Rush feats before triggering maneuver AoO — confirm the exact feat-check pattern used there.
2. Confirm Improved Trip's free-attack-after-successful-trip is NOT already present in `maneuver_resolver.py`.
3. Confirm Improved Sunder AoO suppression is NOT already present — search for "improved_sunder" in aoo.py.

---

## Scope

**Files:** `aidm/core/maneuver_resolver.py`, `aidm/core/aoo.py`
**Read only:** `aidm/schemas/feats.py` (exact feat ID strings), `aidm/core/attack_resolver.py` (understand free attack pattern — see Cleave for reference)

---

## Implementation

### Part 1 — Improved Trip AoO suppression (aoo.py)

When a `TripIntent` triggers an AoO from the target (existing behavior), check if the attacker has `"improved_trip"` feat. If yes, suppress the AoO entirely. Same pattern as Improved Disarm/Grapple/Bull Rush in Batch L.

### Part 2 — Improved Trip free attack (maneuver_resolver.py)

After a successful trip (PRONE condition applied to target), check if attacker has `"improved_trip"` feat. If yes, immediately fire one free attack at the tripped target at the attacker's full attack bonus (primary weapon, no iterative penalty). Use the same free-attack call used for Cleave in `attack_resolver.py` — do not duplicate the attack resolution logic.

```python
# In resolve_trip() after PRONE applied:
if "improved_trip" in attacker.get(EF.FEATS, []):
    # Free immediate attack — same target, full BAB, no extra AoO
    free_attack_events = resolve_single_attack(
        attacker, target, world_state, rng, bonus=0)
    events += free_attack_events
    events.append(Event(..., event_type="improved_trip_free_attack",
                        payload={"attacker_id": attacker_id, "target_id": target_id}))
```

### Part 3 — Improved Sunder AoO suppression (aoo.py)

When a `SunderIntent` triggers an AoO from the target, check if attacker has `"improved_sunder"` feat. If yes, suppress the AoO. Same pattern as Part 1.

**Scope note:** Improved Overrun AoO suppression (FINDING-ENGINE-IMPROVED-OVERRUN-AOO-001) is deferred to Batch O — it requires understanding the overrun resolver and defender-avoid path more carefully. Do NOT attempt it in this WO.

---

## Gate Tests (IT-001 – IT-008)

```python
# IT-001: Improved Trip feat → no AoO on trip attempt from target
# Expect: no AoO event emitted when trip attempt resolves

# IT-002: No Improved Trip feat → AoO fires on trip attempt (existing behavior)
# Expect: AoO event emitted as before

# IT-003: Improved Trip + successful trip → free attack at full BAB on tripped target
# Expect: "improved_trip_free_attack" + attack_roll event after PRONE applied

# IT-004: Improved Trip + failed trip → no free attack
# Expect: no "improved_trip_free_attack" event

# IT-005: Improved Trip free attack uses full attack bonus (not BAB-5 iterative)
# Expect: attack bonus on free attack = attacker base attack bonus

# IT-006: Improved Sunder feat → no AoO on sunder attempt from target
# Expect: no AoO event when SunderIntent resolves

# IT-007: No Improved Sunder feat → AoO fires on sunder (existing behavior)
# Expect: AoO event as before

# IT-008: Both Improved Trip and Improved Sunder on one entity → both work independently
# Expect: correct suppression for each separate intent
```

---

## Debrief Requirements

Three-pass format. Pass 3: document the exact AoO suppression pattern from Batch L (cite file + line). Record whether the Cleave free-attack call was reusable or if a new call path was needed for the Improved Trip free attack.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-IMPROVED-TRIP-001.md`

---

## Session Close Conditions

- [ ] `git add aidm/core/maneuver_resolver.py aidm/core/aoo.py tests/test_engine_improved_trip_gate.py`
- [ ] `git commit`
- [ ] IT-001–IT-008: 8/8 PASS; zero regressions
