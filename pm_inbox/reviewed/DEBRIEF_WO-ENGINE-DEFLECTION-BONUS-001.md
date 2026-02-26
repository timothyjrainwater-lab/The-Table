# DEBRIEF: WO-ENGINE-DEFLECTION-BONUS-001

**Date:** 2026-02-26
**Status:** ACCEPTED — 8/8 gate tests passing
**Commit:** e26b2e2

---

## Kernel
KERNEL-14 (deflection bonus to AC — PHB p.136)

## Pre-existing State
`EF.DEFLECTION_BONUS` constant did not exist. AC calculation in `attack_resolver.py` had no deflection component.

## Changes Made

### `aidm/schemas/entity_fields.py`
New constant added:
```python
DEFLECTION_BONUS = "deflection_bonus"
```

### `aidm/core/attack_resolver.py`
Deflection read and included in AC composite:
```python
# WO-ENGINE-DEFLECTION-BONUS-001: Deflection bonus to AC (PHB p.136)
_deflection_ac = target.get(EF.DEFLECTION_BONUS, 0)

target_ac = base_ac + condition_ac + cover_result.ac_bonus + dex_penalty + \
            _defend_ac_total + _twd_ac_bonus + _ce_ac_bonus + _monk_wis_ac + _deflection_ac
```

**Key design decisions:**
- Deflection applies to ALL attacks including touch attacks (PHB p.136) — no special-casing needed; it's always added to `target_ac`
- Touch attack distinction (armor/shield bypass) is a future tagging concern; deflection correctly stacks in the composite unconditionally
- Missing field → `.get(EF.DEFLECTION_BONUS, 0)` → no crash, no effect
- Event payload `target_ac` will reflect deflection since it's part of the composite

## Gate File
`tests/test_engine_deflection_bonus_001_gate.py` — 8 tests (DB-001 through DB-008)

## PHB Reference
PHB p.136: "A deflection bonus deflects attacks away from you. Deflection bonuses stack with all other bonuses to AC, even other deflection bonuses."

**Note:** PHB says deflection bonuses stack — but in practice, Ring of Protection doesn't stack with Shield of Faith (same item-type restriction). The engine currently sums all `deflection_bonus` values into a single field, so the caller is responsible for passing only the highest. The engine does not enforce non-stacking — that's a chargen/item concern.
