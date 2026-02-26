# Work Order: WO-ENGINE-NONLETHAL-THRESHOLD-001
**Artifact ID:** WO-ENGINE-NONLETHAL-THRESHOLD-001
**Batch:** H (Dispatch #17)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.145-146 (Nonlethal Damage), p.301 (Staggered), p.311 (Unconscious)

---

## Summary

Nonlethal damage accumulates separately from lethal damage. When a creature's nonlethal damage total equals or exceeds its current HP, it becomes STAGGERED (PHB p.145). When nonlethal damage exceeds current HP, the creature falls UNCONSCIOUS. A staggered creature can only take a single move or standard action per turn.

`EF.NONLETHAL_DAMAGE` is already live and accumulates correctly. The gap: no threshold check exists. A creature with 10 HP that takes 12 nonlethal damage continues to act normally. This WO adds the threshold check and condition application.

---

## Scope

**Files in scope:**
- `aidm/core/attack_resolver.py` — add threshold check after nonlethal damage is applied
- `aidm/schemas/conditions.py` — confirm STAGGERED condition is live (verify, may need to add UNCONSCIOUS_NONLETHAL handling)

**Files read-only (verify, do not modify):**
- `aidm/schemas/entity_fields.py` — confirm EF.NONLETHAL_DAMAGE, EF.HP_CURRENT, EF.CONDITIONS
- `aidm/core/conditions.py` — confirm how conditions are applied to entities

**Files out of scope:**
- Nonlethal damage accumulation — already works
- Natural healing of nonlethal damage (1 HP/hour or 1 HP/level/hour with a full rest) — deferred to rest system
- Action economy restriction on staggered (single action per turn) — the condition flag is set here; enforcement is a separate WO

---

## Assumptions to Validate (verify before writing)

1. Confirm `EF.NONLETHAL_DAMAGE` exists and is the correct field. **Already confirmed live.**
2. Confirm `ConditionType.STAGGERED` is live in conditions.py. **Already confirmed live.**
3. Confirm `ConditionType.UNCONSCIOUS` is live — or determine if nonlethal unconscious uses the same UNCONSCIOUS condition as lethal (HP <= -1). If not present, use the closest available condition and document.
4. Confirm how conditions are applied to entities in the existing code — find the pattern from other WOs (e.g., SHAKEN from Batch F Intimidate WO).
5. Confirm the threshold rule: nonlethal == current HP → STAGGERED; nonlethal > current HP → UNCONSCIOUS (creature also falls to 0 HP in this reading — PHB p.145 says "treat as disabled then helpless"). Document the precise PHB rule applied.

---

## Implementation

### In `attack_resolver.py` — after nonlethal damage is applied:

```python
# Nonlethal damage threshold check (PHB p.145)
_nonlethal = target_entity.get(EF.NONLETHAL_DAMAGE, 0)
_hp_current = target_entity.get(EF.HP_CURRENT, 0)
_conditions = target_entity.get(EF.CONDITIONS, [])

if _nonlethal > _hp_current:
    # Nonlethal exceeds HP — unconscious
    if "staggered" in _conditions:
        _conditions.remove("staggered")
    if "unconscious" not in _conditions:
        _conditions.append("unconscious")
    target_entity[EF.CONDITIONS] = _conditions
    events.append(Event(
        event_type="nonlethal_unconscious",
        payload={"target_id": target_id, "nonlethal": _nonlethal, "hp": _hp_current}
    ))
elif _nonlethal == _hp_current:
    # Nonlethal equals HP — staggered
    if "staggered" not in _conditions:
        _conditions.append("staggered")
    target_entity[EF.CONDITIONS] = _conditions
    events.append(Event(
        event_type="nonlethal_staggered",
        payload={"target_id": target_id, "nonlethal": _nonlethal, "hp": _hp_current}
    ))
else:
    # Below threshold — clear staggered if it was from nonlethal (healing case)
    # Note: only clear if staggered was nonlethal-sourced; distinguish from other stagger sources
    pass
```

**Note:** Condition list mutation pattern — verify the exact pattern used by existing condition-applying code (e.g., SHAKEN application in skill_resolver). Match the existing pattern exactly.

---

## Acceptance Criteria

Write gate file `tests/test_engine_nonlethal_threshold_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| NL-001 | Entity with 10 HP takes 10 nonlethal damage | STAGGERED applied; nonlethal_staggered event |
| NL-002 | Entity with 10 HP takes 12 nonlethal damage | UNCONSCIOUS applied; nonlethal_unconscious event |
| NL-003 | Entity with 10 HP takes 9 nonlethal damage | Neither condition applied |
| NL-004 | Entity already STAGGERED; takes more nonlethal exceeding HP | Transitions to UNCONSCIOUS; STAGGERED removed |
| NL-005 | Entity with 10 HP, 8 nonlethal already; takes 2 more nonlethal | Total = 10 = HP → STAGGERED |
| NL-006 | Entity with 10 HP, 8 nonlethal already; takes 3 more nonlethal | Total = 11 > HP → UNCONSCIOUS |
| NL-007 | Entity with no NONLETHAL_DAMAGE field | No crash; treat as 0 |
| NL-008 | Entity with 0 HP (disabled); nonlethal damage applied | Nonlethal > HP → UNCONSCIOUS; event emitted |

8 tests total. Gate label: ENGINE-NONLETHAL-THRESHOLD-001.

---

## Pass 3 Checklist

1. Confirm condition clearing on recovery — if a creature heals lethal damage and nonlethal no longer equals/exceeds HP, STAGGERED should clear. This WO only adds the check on damage application; confirm whether a healing-side check is also needed or deferred.
2. Document the condition mutation pattern chosen and confirm it matches the existing pattern from Batch F (SHAKEN from DemoralizeIntent).
3. Note KERNEL-01 (Entity Lifecycle) — nonlethal unconscious is a third state path alongside lethal death and dying. The engine now has: lethal death (HP ≤ -10), dying (-9 to -1), disabled (0 HP), staggered (nonlethal = HP), nonlethal unconscious (nonlethal > HP). Document all five states are correctly wired.
4. Flag action economy enforcement for STAGGERED as a FINDING — a staggered creature is limited to one move or standard action per turn. This WO sets the condition flag; enforcement in `action_economy.py` or `play_loop.py` is a future WO.

---

## Session Close Condition

- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_nonlethal_threshold_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 NL tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
