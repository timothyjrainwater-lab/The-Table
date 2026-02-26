# Work Order: WO-ENGINE-INTIMIDATE-DEMORALIZE-001
**Artifact ID:** WO-ENGINE-INTIMIDATE-DEMORALIZE-001
**Batch:** F (Dispatch #15)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.76 (Intimidate skill — Demoralize Opponent)

---

## Summary

The Intimidate skill has a combat use: Demoralize Opponent. A standard action opposed check (Intimidate vs. target's HD + WIS modifier + any special modifiers) renders the target Shaken for 1 round (plus 1 round per 5 by which the check beats the DC). Currently `skill_resolver.py` has Intimidate defined and tracked but no Demoralize Opponent action path exists. The Shaken condition is live in `conditions.py`.

This WO wires the combat Intimidate action: parse the intent, run the opposed check, apply Shaken if successful.

---

## Scope

**Files in scope:**
- `aidm/core/skill_resolver.py` — add `DemoralizeIntent` resolution path
- `aidm/schemas/intents.py` — add `DemoralizeIntent` dataclass
- `aidm/core/play_loop.py` — add routing branch for `DemoralizeIntent`

**Files read-only (verify, do not modify):**
- `aidm/schemas/conditions.py` — confirm SHAKEN condition exists with duration field
- `aidm/schemas/entity_fields.py` — confirm HD field and WIS modifier accessible on entities

**Files out of scope:**
- Social Intimidate (non-combat attitude change) — separate mechanic, separate WO
- Any condition resolver beyond applying SHAKEN with duration

---

## Assumptions to Validate (verify before writing)

1. Confirm SHAKEN condition is in `ConditionType` enum and has duration support.
2. Confirm entity HD field — what field stores Hit Dice count? Likely `EF.HIT_DICE` or derivable from class levels.
3. Confirm WIS modifier accessible on target entity.
4. Confirm no existing `DemoralizeIntent` or Intimidate combat path.
5. Confirm `skill_resolver.py` pattern for other opposed skill checks (e.g., Feint uses Bluff vs. Sense Motive) — follow the same pattern.

---

## Implementation

### 1. `aidm/schemas/intents.py` — DemoralizeIntent

```python
@dataclass
class DemoralizeIntent:
    """Player uses Intimidate to demoralize a target in combat (PHB p.76).
    Standard action. Opposed check: Intimidate vs. target HD + WIS mod.
    """
    actor_id: str
    target_id: str
    source_text: str
```

### 2. `aidm/core/skill_resolver.py` — resolve_demoralize()

```python
def resolve_demoralize(world_state, intent, next_event_id):
    actor = world_state["entities"][intent.actor_id]
    target = world_state["entities"][intent.target_id]

    # Intimidate check (d20 + skill ranks + CHA mod)
    intimidate_roll = _d20() + actor.get(EF.INTIMIDATE_BONUS, 0)

    # Target DC: HD + WIS modifier
    target_hd = target.get(EF.HIT_DICE, 1)
    target_wis_mod = (target.get(EF.WIS, 10) - 10) // 2
    dc = target_hd + target_wis_mod

    events = []
    if intimidate_roll >= dc:
        margin = intimidate_roll - dc
        duration = 1 + (margin // 5)
        # Apply SHAKEN condition
        # ... (follow existing condition application pattern)
        events.append(Event(
            event_id=next_event_id,
            event_type="condition_applied",
            payload={
                "target_id": intent.target_id,
                "condition": "SHAKEN",
                "duration_rounds": duration,
                "source": "intimidate_demoralize",
            }
        ))
    else:
        events.append(Event(
            event_id=next_event_id,
            event_type="skill_check_failed",
            payload={
                "actor_id": intent.actor_id,
                "skill": "intimidate",
                "roll": intimidate_roll,
                "dc": dc,
            }
        ))
    return world_state, next_event_id + len(events), events
```

**Note:** Follow the exact condition application pattern used by other condition-applying resolvers. Do not invent a new pattern.

### 3. `aidm/core/play_loop.py` — routing branch

Add after existing intent branches:
```python
elif isinstance(combat_intent, DemoralizeIntent):
    world_state, next_event_id, new_events = resolve_demoralize(
        world_state, combat_intent, next_event_id
    )
    events.extend(new_events)
    # Consumes standard action
```

---

## Acceptance Criteria

Write gate file `tests/test_engine_intimidate_demoralize_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| ID-001 | DemoralizeIntent; roll beats DC | `condition_applied` event; condition=SHAKEN |
| ID-002 | DemoralizeIntent; roll beats DC by 5+ | SHAKEN duration = 2 rounds |
| ID-003 | DemoralizeIntent; roll beats DC by 10+ | SHAKEN duration = 3 rounds |
| ID-004 | DemoralizeIntent; roll fails DC | `skill_check_failed` event; no SHAKEN applied |
| ID-005 | DemoralizeIntent; standard action consumed | Actor action budget decremented |
| ID-006 | DemoralizeIntent fails; world_state HP unchanged | No HP delta on failure |
| ID-007 | DemoralizeIntent; target already Shaken | SHAKEN reapplied / duration refreshed (not stacked to Frightened — PHB p.76 note) |
| ID-008 | DemoralizeIntent; high-WIS/high-HD target | DC reflects HD + WIS mod correctly |

8 tests total. Gate label: ENGINE-INTIMIDATE-DEMORALIZE-001.

**ID-007 note:** PHB p.76 states a target already Shaken does not become Frightened from Intimidate — just refreshes duration. Verify this edge case is handled correctly.

---

## Pass 3 Checklist

1. Confirm SHAKEN condition mechanical effect is applied correctly — Shaken imposes -2 on attack rolls, saving throws, skill checks, and ability checks (PHB p.310).
2. Confirm action economy — Demoralize is a standard action. Note if this was correctly consuming the action slot.
3. Check whether any existing Intimidate routing existed (social path) and whether this WO creates a routing conflict or clean separation.
4. Note KERNEL-07 (Social Consequence) — Demoralize is a combat tool, but Intimidate's social use (changing NPC attitude) is a different path that is still NOT STARTED. Log as FINDING if the social path is completely absent.

---

## Session Close Condition

- [ ] `git add aidm/schemas/intents.py aidm/core/skill_resolver.py aidm/core/play_loop.py tests/test_engine_intimidate_demoralize_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 ID tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`
