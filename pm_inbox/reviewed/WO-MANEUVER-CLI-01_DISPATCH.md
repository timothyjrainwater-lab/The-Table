# WO-MANEUVER-CLI-01 — Combat Maneuvers in CLI

**Dispatch Authority:** PM (Opus)
**Priority:** Wave B — parallel dispatch (after Wave A completes)
**Risk:** LOW | **Effort:** Medium | **Breaks:** 0 expected
**Depends on:** Wave A complete

---

## Target Lock

The engine has 6 fully implemented combat maneuvers (Bull Rush, Trip, Overrun, Sunder, Disarm, Grapple) routed through `play_loop.py:1230-1280`, but the CLI has no way to invoke them.

**Goal:** All 6 maneuver commands parse and execute. Events display with success/failure.

---

## Binary Decisions (Locked)

1. **Verb mapping:** One command per maneuver type. No aliases except `"bull rush"` / `"bullrush"`.
2. **Sunder defaults to weapon.** `sunder <target>` targets weapon. `sunder <target> shield` targets shield.
3. **Target resolution:** Reuse `IntentBridge.resolve_attack()` to get the target_id, then build the maneuver intent.
4. **Event display:** New event types added to `format_events()`. Existing `condition_applied`/`hp_changed` events already rendered.

---

## Contract Spec

### File Scope (2 files)

| File | Action | Lines |
|------|--------|-------|
| `play.py` | Modify `parse_input()` (64-119), `resolve_and_execute()` (138-207), `format_events()` (263-340), `_HELP_TEXT` (122-131) | Add 6 maneuver verbs, routing, event display |
| `tests/test_play_cli.py` | Add ~12 new tests | Parser, resolution, display per maneuver |

### Implementation Detail

**Parser (play.py, `parse_input()`, add two-word verbs before single-word check):**
```python
# Two-word commands (before verb = parts[0])
if text.startswith("bull rush") or text.startswith("bullrush"):
    prefix_len = len("bull rush") if text.startswith("bull rush") else len("bullrush")
    target_ref = text[prefix_len:].strip()
    target_ref = _strip_articles(target_ref) if target_ref else None
    return "bull_rush", DeclaredAttackIntent(target_ref=target_ref, weapon=None)
```

**Single-word maneuver verbs (in the verb switch section):**
```python
if verb == "trip":
    target_ref = " ".join(parts[1:]) if len(parts) > 1 else None
    if target_ref: target_ref = _strip_articles(target_ref)
    return "trip", DeclaredAttackIntent(target_ref=target_ref, weapon=None)

if verb == "disarm":
    ...same pattern...
    return "disarm", DeclaredAttackIntent(target_ref=target_ref, weapon=None)

if verb == "grapple":
    ...same pattern...
    return "grapple", DeclaredAttackIntent(target_ref=target_ref, weapon=None)

if verb == "sunder":
    ...parse target_ref, check for "shield" suffix...
    return "sunder", DeclaredAttackIntent(target_ref=target_ref, weapon=item)

if verb == "overrun":
    ...same pattern...
    return "overrun", DeclaredAttackIntent(target_ref=target_ref, weapon=None)
```

**Resolution (play.py, `resolve_and_execute()`):**

For each maneuver type, resolve the target via bridge, then construct the appropriate intent:

```python
elif action_type in ("bull_rush", "trip", "overrun", "sunder", "disarm", "grapple"):
    resolved = bridge.resolve_attack(actor_id, declared, view)
    if isinstance(resolved, ClarificationRequest):
        return TurnResult(status="requires_clarification", ...)

    # Import maneuver intents
    from aidm.schemas.maneuvers import (
        BullRushIntent, TripIntent, OverrunIntent,
        SunderIntent, DisarmIntent, GrappleIntent,
    )

    target_id = resolved.target_id
    intent_map = {
        "bull_rush": lambda: BullRushIntent(attacker_id=actor_id, target_id=target_id),
        "trip": lambda: TripIntent(attacker_id=actor_id, target_id=target_id),
        "overrun": lambda: OverrunIntent(attacker_id=actor_id, target_id=target_id),
        "sunder": lambda: SunderIntent(attacker_id=actor_id, target_id=target_id, target_item=declared.weapon or "weapon"),
        "disarm": lambda: DisarmIntent(attacker_id=actor_id, target_id=target_id),
        "grapple": lambda: GrappleIntent(attacker_id=actor_id, target_id=target_id),
    }
    resolved = intent_map[action_type]()
```

**Display (play.py, `format_events()`):**

Add handlers for maneuver event types:
```python
# Maneuver events
elif ev.event_type in ("bull_rush_declared", "trip_declared", "overrun_declared",
                       "sunder_declared", "disarm_declared", "grapple_declared"):
    attacker = _name(ws, p.get("attacker_id", ""))
    target = _name(ws, p.get("target_id", ""))
    maneuver = ev.event_type.replace("_declared", "").replace("_", " ")
    lines.append(f"  {attacker} attempts to {maneuver} {target}!")

elif ev.event_type == "opposed_check":
    attacker_total = p.get("attacker_total", 0)
    defender_total = p.get("defender_total", 0)
    lines.append(f"  Opposed check: {attacker_total} vs {defender_total}")

elif ev.event_type == "touch_attack_roll":
    d20 = p.get("d20_result", "?")
    total = p.get("total", 0)
    ac = p.get("target_touch_ac", 0)
    hit = p.get("hit", False)
    lines.append(f"  Touch attack: [{d20}] + bonus = {total} vs Touch AC {ac} -> {'HIT' if hit else 'MISS'}")

elif ev.event_type.endswith("_success"):
    maneuver = ev.event_type.replace("_success", "").replace("_", " ").title()
    lines.append(f"  {maneuver} succeeds!")

elif ev.event_type.endswith("_failure") and "disarm" not in ev.event_type:
    maneuver = ev.event_type.replace("_failure", "").replace("_", " ").title()
    lines.append(f"  {maneuver} fails!")

elif ev.event_type == "overrun_avoided":
    defender = _name(ws, p.get("defender_id", ""))
    lines.append(f"  {defender} steps aside!")
```

**Note on event type specifics from `maneuver_resolver.py`:**
- `bull_rush_declared`, `bull_rush_success`, `bull_rush_failure`
- `trip_declared`, `trip_success`, `trip_failure`, `counter_trip_success`, `counter_trip_failure`
- `overrun_declared`, `overrun_success`, `overrun_failure`, `overrun_avoided`
- `sunder_declared`, `sunder_success`, `sunder_failure`
- `disarm_declared`, `disarm_success`, `disarm_failure`, `counter_disarm_success`, `counter_disarm_failure`
- `grapple_declared`, `grapple_success`, `grapple_failure`
- `opposed_check`, `touch_attack_roll` (shared across maneuvers)

### Maneuver Intent Constructors (from `aidm/schemas/maneuvers.py`)

| Intent | Required Fields |
|--------|----------------|
| `BullRushIntent` | `attacker_id`, `target_id`, `is_charge=False` |
| `TripIntent` | `attacker_id`, `target_id` |
| `OverrunIntent` | `attacker_id`, `target_id`, `is_charge=False`, `defender_avoids=False` |
| `SunderIntent` | `attacker_id`, `target_id`, `target_item` ("weapon" or "shield") |
| `DisarmIntent` | `attacker_id`, `target_id` |
| `GrappleIntent` | `attacker_id`, `target_id` |

### Frozen Contracts

None touched.

---

## Implementation Sequencing

1. Add two-word `"bull rush"` / `"bullrush"` detection before single-word verb split
2. Add single-word verb detection for trip, disarm, grapple, sunder, overrun
3. Add maneuver routing in `resolve_and_execute()` — resolve target, build intent
4. Add maneuver event display in `format_events()`
5. Update `_HELP_TEXT` with all 6 maneuver commands
6. Add tests (~12):
   - Parser tests: one per maneuver verb + bull rush alias
   - Resolution test: at least one maneuver executes without error
   - Display tests: declared, success, failure events render
7. Run full test suite

---

## Acceptance Criteria

1. All 6 maneuver commands parse and execute
2. Events display with success/failure
3. Help text shows maneuver commands
4. All existing tests pass
5. ~12 new tests pass

---

## Agent Instructions

- Read `AGENT_ONBOARDING_CHECKLIST.md` and `AGENT_DEVELOPMENT_GUIDELINES.md` before starting
- This WO modifies `play.py` ONLY. Do NOT modify `play_loop.py`, `maneuver_resolver.py`, or any core engine file
- The engine already routes all 6 maneuver intent types — you are only wiring the CLI
- Maneuver intents flow through the same `execute_turn()` call path as attacks
- For sunder, the `target_item` field must be "weapon" or "shield" (Literal type)
- Run full suite before declaring completion
