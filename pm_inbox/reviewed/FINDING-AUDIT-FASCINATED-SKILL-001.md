# FINDING-AUDIT-FASCINATED-SKILL-001 — Fascinated Condition Missing -4 Reactive Skill Penalty

**ID:** FINDING-AUDIT-FASCINATED-SKILL-001
**Severity:** LOW
**Status:** OPEN
**Found by:** AUDIT-WO-006 (2026-02-27)
**Lifecycle:** NEW

---

## Description

The Fascinated condition correctly suppresses actions but does not apply the -4 penalty to reactive skill checks (Spot, Listen) required by PHB p.308.

## PHB Specification (p.308)

> "A fascinated creature takes a –4 penalty on skill checks made as reactions, such as Listen and Spot checks."

## Evidence

**Code (`conditions.py`):**
```python
def create_fascinated_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    return ConditionInstance(
        condition_type=ConditionType.FASCINATED,
        source=source,
        modifiers=ConditionModifiers(
            actions_prohibited=True,  # No actions — correct
            # NOTE: -4 reactive skill penalty not wired
        ),
        ...
    )
```

The `ConditionModifiers` dataclass has no `reactive_skill_modifier` field. The penalty is documented in the `notes` string but not enforced.

## Impact

LOW — Fascinated creatures can hear/spot approaching enemies with full skill bonus instead of -4 penalty. Affects rarely-used skill check scenarios during fascination.

## Fix

Add `reactive_skill_modifier: int = 0` to `ConditionModifiers`. In `skill_resolver.py`, apply this penalty to Spot and Listen checks when the entity has an active Fascinated condition.

## Corrective WO

LOW priority. Defer to backlog. Requires `ConditionModifiers` schema change + skill_resolver touch.
