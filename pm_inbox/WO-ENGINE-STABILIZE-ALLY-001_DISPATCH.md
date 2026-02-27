# WO-ENGINE-STABILIZE-ALLY-001 — Stabilize Ally (DC 15 Heal)

**WO ID:** WO-ENGINE-STABILIZE-ALLY-001
**Type:** Engine feature
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Lifecycle:** DISPATCH-READY
**Batch:** Engine Batch N
**Gate label:** ENGINE-STABILIZE-ALLY
**Gate file:** `tests/test_engine_stabilize_ally_gate.py`
**Gate count:** 8 tests (SA-001 – SA-008)

---

## Gap Verification (coverage map confirmed NOT STARTED 2026-02-26)

PHB p.145: An adjacent ally may attempt a DC 15 Heal check (standard action) to stabilize a dying character. On success the dying character stops losing HP and becomes stable.

Coverage map line 70: `Stabilization by ally (DC 15 Heal) | NOT STARTED`.

**⚠ CRITICAL: `aidm/core/stabilize_resolver.py` already exists as an UNTRACKED file.**
On session boot, read this file immediately. If it already implements `StabilizeAllyIntent` routing and the full DC 15 Heal mechanic, treat as SAI — validate existing behavior with gate tests, zero production changes, finding CLOSED. Do **not** rewrite a working resolver.

---

## Scope

**Files:** `aidm/core/stabilize_resolver.py` (read existing; extend or replace stub), `aidm/schemas/intents.py`, `aidm/core/play_loop.py`
**Read only:** `aidm/core/dying_resolver.py` (understand DYING/STABLE fields and transitions), `aidm/core/skill_resolver.py` (understand Heal check resolution)

---

## Intent Schema

```python
@dataclass
class StabilizeAllyIntent:
    actor_id: str          # healer
    target_id: str         # dying character to stabilize
```

Add to `intents.py` alongside existing intents (near `HealIntent` if present).

---

## Implementation

In `stabilize_resolver.py` (or extend existing):

```python
def resolve_stabilize_ally(actor, target, world_state, rng) -> List[Event]:
    # Guard 1: target must be DYING (HP between -1 and -9, DYING field set)
    if not target.get(EF.DYING, False):
        return [Event(..., event_type="intent_validation_failed",
                      payload={"reason": "target_not_dying"})]

    # Guard 2: actor must be adjacent (within 1 square) — use same adjacency check
    # as aid_another_resolver.py or skip if grid not available (defer to PHB honor system)

    # Heal check: d20 + Heal ranks + WIS modifier vs DC 15 (untrained allowed)
    heal_result = resolve_skill_check(actor, "heal", dc=15, world_state=world_state, rng=rng)

    events = [Event(..., event_type="ally_stabilize_attempt",
                    payload={"actor_id": actor_id, "target_id": target_id,
                             "roll": heal_result.roll, "dc": 15})]

    if heal_result.success:
        # Set STABLE=True; entity stops losing HP; DYING remains True (still unconscious)
        events += [
            Event(..., event_type="entity_mutated",
                  payload={"entity_id": target_id, EF.STABLE: True}),
            Event(..., event_type="ally_stabilize_success",
                  payload={"actor_id": actor_id, "target_id": target_id})
        ]
    else:
        events.append(Event(..., event_type="ally_stabilize_fail",
                            payload={"actor_id": actor_id, "target_id": target_id}))
    return events
```

Wire `StabilizeAllyIntent` in `execute_turn()` → `resolve_stabilize_ally()`. Standard action slot.

---

## Gate Tests (SA-001 – SA-008)

```python
# SA-001: Target DYING (-3 HP), healer passes DC 15 Heal (seeded high roll)
# Expect: ally_stabilize_success + EF.STABLE=True on target

# SA-002: Target DYING, healer fails DC 15 Heal (seeded low roll)
# Expect: ally_stabilize_fail, EF.STABLE unchanged

# SA-003: Target NOT dying (HP > 0) → intent_validation_failed
# Expect: intent_validation_failed with reason="target_not_dying"

# SA-004: Target STABLE already → intent_validation_failed (don't re-stabilize)
# Expect: intent_validation_failed or no-op

# SA-005: Stabilized target does NOT lose HP next round (dying tick skipped)
# Expect: no "dying_fort_failed" or HP decrement event after stabilization

# SA-006: Event sequence: ally_stabilize_attempt fires before success/fail
# Expect: attempt → success in event list order

# SA-007: Standard action consumed after stabilize attempt
# Expect: second action in same turn is denied (standard_action_used flag)

# SA-008: Healer with 0 Heal ranks still rolls (Heal is untrained)
# Expect: check resolves (may fail on low roll but attempt fires)
```

---

## Debrief Requirements

Three-pass format. Pass 3: document the state of the untracked `stabilize_resolver.py` on session boot — was it a stub, partial, or complete? If SAI, record that.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-STABILIZE-ALLY-001.md`

---

## Session Close Conditions

- [ ] `git add aidm/core/stabilize_resolver.py aidm/schemas/intents.py aidm/core/play_loop.py tests/test_engine_stabilize_ally_gate.py`
- [ ] `git commit`
- [ ] SA-001–SA-008: 8/8 PASS; zero regressions
