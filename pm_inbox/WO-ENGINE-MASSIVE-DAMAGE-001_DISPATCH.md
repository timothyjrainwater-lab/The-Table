# WO-ENGINE-MASSIVE-DAMAGE-001 — Massive Damage Rule

**WO ID:** WO-ENGINE-MASSIVE-DAMAGE-001
**Type:** Engine feature
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Batch:** Engine Batch N
**Gate label:** ENGINE-MASSIVE-DAMAGE
**Gate file:** `tests/test_engine_massive_damage_gate.py`
**Gate count:** 8 tests (MD-001 – MD-008)

---

## Gap Verification (coverage map confirmed NOT STARTED 2026-02-26)

PHB p.145: "If a character ever sustains a single attack that deals an amount of damage equal to half his total hit points (minimum 50 points of damage), he must succeed on a DC 15 Fortitude save or die."

Coverage map line 68: `Massive damage rule (50+ HP = Fort DC 15 or die) | NOT STARTED`.

**Assumptions to Validate before writing:**
1. Confirm `attack_resolver.py` has no `massive_damage` check. Search for "massive" in attack_resolver — if found and wired, treat as SAI (validate existing behavior, zero production changes, gate validates, finding CLOSED).
2. Confirm the Fort save mechanism in `save_resolver.py` is callable from `attack_resolver.py` — check import path.
3. Confirm `entity_defeated` event path is reachable from `attack_resolver.py` post-damage — it is if `dying_resolver.resolve_hp_transition()` already handles it.

---

## Scope

**Files:** `aidm/core/attack_resolver.py`, `aidm/core/full_attack_resolver.py`
**Read only:** `aidm/core/dying_resolver.py`, `aidm/core/save_resolver.py`

---

## Implementation

Immediately after final damage is applied and before the `entity_defeated` check in the normal HP flow, add a massive damage check:

```python
# After damage_dealt computed and applied to entity HP:
if damage_dealt >= 50:
    # Emit sensor event
    events.append(Event(event_id=..., event_type="massive_damage_check",
                        payload={"actor_id": attacker_id, "target_id": target_id,
                                 "damage": damage_dealt}))
    # Fort save DC 15
    fort_result = resolve_save(target, "fortitude", dc=15, world_state=world_state, rng=rng)
    if fort_result.failed:
        events.append(Event(event_id=..., event_type="massive_damage_death",
                            payload={"target_id": target_id, "fort_roll": fort_result.roll}))
        # Call entity defeat path (same as HP <= -10)
        # e.g., apply entity_defeated event — see dying_resolver for correct call
```

Do **not** suppress the massive damage check if the entity is already dying from the same hit — the rule fires on any single blow of 50+ damage regardless of current HP.

Apply in **both** `attack_resolver.py` (single attack path) and `full_attack_resolver.py` (each iterative in the loop).

**Immunity:**
- Undead: immune to Fort saves that affect living creatures (treat as auto-pass; no death event).
- Constructs: same. Check `EF.CREATURE_TYPE` for `"undead"` / `"construct"` / `"ooze"` / `"plant"` — if present, skip the Fort save and emit `massive_damage_immune` instead.

---

## Gate Tests (MD-001 – MD-008)

```python
# MD-001: 50 damage in single hit → Fort save triggered (event emitted)
# Expect: "massive_damage_check" event in output

# MD-002: 49 damage in single hit → no massive damage check
# Expect: no "massive_damage_check" event

# MD-003: Fort DC 15 fail (seeded RNG, low roll) → entity_defeated
# Expect: "massive_damage_death" + entity_defeated in events

# MD-004: Fort DC 15 pass (seeded RNG, high roll) → entity survives
# Expect: "massive_damage_check" present, no "massive_damage_death"

# MD-005: Critical hit dealing 50+ → massive damage check fires
# Expect: "massive_damage_check" present on crit path

# MD-006: Entity with CREATURE_TYPE="undead" takes 50+ → immune, no Fort save
# Expect: "massive_damage_immune" event, no "massive_damage_death"

# MD-007: Entity with CREATURE_TYPE="construct" takes 50+ → immune
# Expect: "massive_damage_immune" event

# MD-008: Full attack — one iterative dealing 50+ triggers massive damage check
# Expect: "massive_damage_check" for the qualifying iterative only
```

---

## Debrief Requirements

Three-pass format. Pass 3: document which call site (attack_resolver vs full_attack_resolver) was simpler to instrument and whether dying_resolver changes were needed.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-MASSIVE-DAMAGE-001.md`

---

## Session Close Conditions

- [ ] `git add aidm/core/attack_resolver.py aidm/core/full_attack_resolver.py tests/test_engine_massive_damage_gate.py`
- [ ] `git commit`
- [ ] MD-001–MD-008: 8/8 PASS (or SAI finding filed if already implemented); zero regressions
