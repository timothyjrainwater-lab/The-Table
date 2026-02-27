# FINDING-AUDIT-SPONT-SLOT-001 — Cleric Spontaneous Casting No Same-Or-Lower Flexibility

**ID:** FINDING-AUDIT-SPONT-SLOT-001
**Severity:** LOW
**Status:** OPEN
**Found by:** AUDIT-WO-004 (2026-02-27)
**Lifecycle:** NEW

---

## Description

Cleric spontaneous cure redirect uses a strict level-to-level mapping. PHB p.32 allows substituting any prepared spell with a cure spell of the "same or lower level." The engine only supports same-level substitution.

## PHB Specification (p.32)

> "A cleric can spontaneously cast any cure spell of the same level or lower as the spell being sacrificed."

A cleric who prepared a 4th-level spell can spontaneously cast Cure Light Wounds (level 1) by sacrificing that 4th-level slot. The current engine forces a 4th-level slot to become Cure Critical Wounds (level 4).

## Evidence

**Code (`play_loop.py` lines 530-545):**
```python
_CURE_SPELLS_BY_LEVEL = {
    1: "cure_light_wounds",
    2: "cure_moderate_wounds",
    3: "cure_serious_wounds",
    4: "cure_critical_wounds",
    5: "mass_cure_light_wounds",
}
_declared_level = spell.level
_cure_id = _CURE_SPELLS_BY_LEVEL.get(_declared_level)
```

The mapping keys on `_declared_level` exactly — no sub-level selection. If you sacrifice a level 4 prepared spell, you always get `cure_critical_wounds`, never `cure_light_wounds`.

## Impact

LOW — In most combat scenarios, players choose the highest available cure spell anyway. The only scenario affected is when a player wants to cast a lower-level cure than the slot being sacrificed, which is uncommon but valid per RAW.

## Fix

The intent schema would need to carry `target_cure_level` (caller-specified, ≤ declared slot level). The mapping lookup then uses `target_cure_level` instead of `_declared_level`.

## Corrective WO

LOW priority. Defer to backlog. No gate tests currently test sub-level spontaneous casting.
