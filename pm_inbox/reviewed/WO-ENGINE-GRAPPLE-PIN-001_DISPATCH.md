# WO-ENGINE-GRAPPLE-PIN-001 — Pinned Condition (PHB p.156)

**Issued:** 2026-02-24
**Authority:** Thunder approval (parallel backend sprint)
**Gate:** ENGINE-GRAPPLE-PIN (new gate, defined below)
**Parallel-safe:** Yes — isolated to `maneuver_resolver.py`, `conditions.py`, `maneuvers.py`, and `entity_fields.py`. No overlap with CONCENTRATION-001 or SPELL-PREP-001.
**Predecessor:** CP-22 (grapple established, bidirectional conditions wired)

---

## 1. Target Lock

CP-22 implemented grapple initiation: touch attack + opposed grapple check → `grappled` on defender + `grappling` on attacker + `grapple_pairs` entry. PHB p.156 also defines **pinning**: if the grappler succeeds at a second opposed grapple check while already grappling, the defender becomes **pinned** (helpless — cannot move, loses Dex to AC, cannot take actions, melee attacks auto-hit).

**Current gap:** A second `GrappleIntent` against an already-grappled target runs the normal grapple path (touch attack + opposed check) but does not apply `pinned` on success — it just re-applies `grappled`, which is a no-op.

**Done means:** `GrappleIntent` against an entity with `GRAPPLED` condition and whose attacker is already in `grapple_pairs` escalates to a pin attempt on success. `pinned` condition is added to `conditions.py`. `PinEscapeIntent` added to `maneuvers.py`. Gate ENGINE-GRAPPLE-PIN 10/10.

---

## 2. PHB 3.5e Rule (p.156)

> "If you get a hold, you can hold that opponent (grapple) or pin them. To pin a grappled opponent, make another grapple check. If you succeed, the opponent is pinned. A pinned character is helpless and can be coup de graced."

Pin mechanics:
- **Initiation:** Second opposed grapple check (same d20 + STR + special size mod) while already grappling target
- **Pinned condition:** Helpless — Dex = 0 (lose Dex to AC), cannot take actions, melee attackers get +4 (or auto-hit for coup de grace), ranged attacks unaffected
- **Escape:** Pinned entity can attempt escape each round (full-round action: opposed grapple check)
- **Grappler while pinning:** Still considered grappling (same conditions as before)

---

## 3. Authoritative Values

| Item | Value | PHB ref |
|------|-------|---------|
| Pin attempt | Opposed grapple check: d20 + STR + special size | p.156 |
| Pinned AC vs melee | -4 (melee attackers get +4 bonus) | p.310 (helpless) |
| Pinned AC vs ranged | no change | p.310 |
| Pinned Dex | treated as 0 (-5 modifier) | p.310 |
| Pinned actions | none (cannot take actions) | p.310 |
| Pin escape check | opposed grapple (full-round) | p.156 |
| grapple_pairs | unchanged (pair still exists while pinned) | p.156 |

---

## 4. Implementation Spec

### 4.1 Add `PINNED` to `ConditionType` in `conditions.py`

```python
class ConditionType(str, Enum):
    # ... existing conditions ...
    PINNED = "pinned"   # WO-ENGINE-GRAPPLE-PIN-001: helpless from grapple escalation
```

### 4.2 Add `create_pinned_condition()` factory to `conditions.py`

```python
def create_pinned_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Pinned condition instance.

    PHB p.156: A pinned character is helpless — cannot take actions,
    loses Dexterity to AC (treated as Dex 0), and melee attackers
    gain +4 bonus (equivalent to attacking helpless target).

    Pinned is more severe than Grappled. Applied when grappler
    succeeds at a second grapple check against an already-grappled target.
    """
    return ConditionInstance(
        condition_type=ConditionType.PINNED,
        source=source,
        modifiers=ConditionModifiers(
            ac_modifier_melee=-4,        # Melee attackers get +4 (PHB p.310 helpless)
            ac_modifier_ranged=0,        # Ranged unaffected
            loses_dex_to_ac=True,        # Dex treated as 0
            auto_hit_if_helpless=True,   # Coup de grace eligible
            actions_prohibited=True,     # Cannot take actions
            movement_prohibited=True,    # Cannot move
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Pinned: helpless, Dex 0, melee +4 bonus, cannot act"
    )
```

### 4.3 Add `PinEscapeIntent` to `maneuvers.py`

```python
@dataclass
class PinEscapeIntent:
    """Intent to escape a pin. WO-ENGINE-GRAPPLE-PIN-001.

    PHB p.156: A pinned creature can attempt to escape each round.
    Escape requires a full-round action and a successful opposed grapple check.
    """

    attacker_id: str
    """Entity ID of the pinned entity attempting to escape."""

    target_id: str
    """Entity ID of the entity holding the pin."""
```

Also add `PINNED` to `EF` in `entity_fields.py` — **not needed** since pinned is tracked via `CONDITIONS` dict (same as all other conditions). No new EF constant required.

### 4.4 Modify `resolve_grapple()` in `maneuver_resolver.py` — Pin Escalation Path

In `resolve_grapple()`, after the touch attack hits and the opposed check is built, add a branch:

```python
# Check if this is a pin attempt (attacker already grappling target)
already_grappling = False
if world_state.active_combat is not None:
    grapple_pairs = world_state.active_combat.get("grapple_pairs", [])
    already_grappling = any(
        p[0] == attacker_id and p[1] == target_id
        for p in grapple_pairs
    )

target_already_pinned = ConditionType.PINNED.value in (
    world_state.entities.get(target_id, {}).get(EF.CONDITIONS, {})
)

is_pin_attempt = already_grappling and not target_already_pinned
```

**If `is_pin_attempt` and opposed check succeeds:**
- Apply `pinned` condition (via `apply_condition`) to target
- Remove `grappled` condition from target (pinned supersedes grappled)
- Emit `pin_established` event
- Do NOT update `grapple_pairs` (pair already exists)

**If `is_pin_attempt` and opposed check fails:**
- Target remains grappled (no change to conditions)
- Emit `pin_attempt_failed` event

**Normal grapple path** (not already grappling) is unchanged.

### 4.5 Wire `PinEscapeIntent` in `play_loop.py`

In `execute_turn()`, alongside `GrappleEscapeIntent` routing:

```python
from aidm.schemas.maneuvers import PinEscapeIntent

elif isinstance(combat_intent, PinEscapeIntent):
    pin_escape_events, world_state, maneuver_result = resolve_pin_escape(
        intent=combat_intent,
        world_state=world_state,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.1,
    )
    events.extend(pin_escape_events)
    current_event_id += len(pin_escape_events)
    narration = "pin_escape_success" if maneuver_result.success else "pin_escape_failed"
```

### 4.6 Add `resolve_pin_escape()` to `maneuver_resolver.py`

```python
def resolve_pin_escape(
    intent: PinEscapeIntent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState, ManeuverResult]:
    """Resolve a pin escape attempt.

    PHB p.156: Opposed grapple check. On success: pinned condition removed,
    entity reverts to grappled (still in grapple_pairs, but no longer helpless).
    On failure: still pinned.

    RNG Consumption Order:
    1. Escaper's grapple check (d20) — "combat" stream
    2. Pinner's grapple check (d20) — "combat" stream
    """
    events = []
    current_event_id = next_event_id
    initiator_id = intent.attacker_id
    pinner_id = intent.target_id

    # Verify initiator is actually pinned
    initiator_conditions = world_state.entities.get(initiator_id, {}).get(EF.CONDITIONS, {})
    if ConditionType.PINNED.value not in initiator_conditions:
        # Not actually pinned — treat as grapple escape instead
        events.append(Event(
            event_id=current_event_id,
            event_type="pin_escape_invalid",
            timestamp=timestamp,
            payload={
                "initiator_id": initiator_id,
                "reason": "not_pinned",
            }
        ))
        return events, world_state, ManeuverResult(
            maneuver_type="pin_escape", success=False, events=[]
        )

    # Opposed grapple check
    initiator_str = _get_str_modifier(world_state, initiator_id)
    initiator_size = _get_size_modifier(world_state, initiator_id)
    initiator_mod = initiator_str + initiator_size

    pinner_str = _get_str_modifier(world_state, pinner_id)
    pinner_size = _get_size_modifier(world_state, pinner_id)
    pinner_mod = pinner_str + pinner_size

    check = _roll_opposed_check(rng, initiator_mod, pinner_mod, "grapple_escape_pin")

    if check.attacker_wins:
        # Escape: remove pinned, reapply grappled (still in grapple_pairs)
        world_state = remove_condition(world_state, initiator_id, ConditionType.PINNED.value, current_event_id)
        world_state = apply_condition(
            world_state, initiator_id,
            create_grappled_condition(source="grapple_reestablish", applied_at_event_id=current_event_id),
            current_event_id,
        )
        events.append(Event(
            event_id=current_event_id,
            event_type="pin_escape_success",
            timestamp=timestamp,
            payload={
                "initiator_id": initiator_id,
                "pinner_id": pinner_id,
                "initiator_roll": check.attacker_roll,
                "pinner_roll": check.defender_roll,
                "initiator_total": check.attacker_total,
                "pinner_total": check.defender_total,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        return events, world_state, ManeuverResult(
            maneuver_type="pin_escape", success=True,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
    else:
        events.append(Event(
            event_id=current_event_id,
            event_type="pin_escape_failed",
            timestamp=timestamp,
            payload={
                "initiator_id": initiator_id,
                "pinner_id": pinner_id,
                "initiator_roll": check.attacker_roll,
                "pinner_roll": check.defender_roll,
                "initiator_total": check.attacker_total,
                "pinner_total": check.defender_total,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 156}],
        ))
        return events, world_state, ManeuverResult(
            maneuver_type="pin_escape", success=False,
            events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
        )
```

---

## 5. Event Types (New)

| Event type | Emitted when |
|------------|-------------|
| `pin_established` | Second grapple check succeeds — target becomes pinned |
| `pin_attempt_failed` | Second grapple check fails — target remains grappled |
| `pin_escape_success` | Pinned entity wins opposed check — reverts to grappled |
| `pin_escape_failed` | Pinned entity loses opposed check — still pinned |
| `pin_escape_invalid` | `PinEscapeIntent` issued but target not pinned |

---

## 6. Gate Spec

**Gate name:** `ENGINE-GRAPPLE-PIN`
**Test file:** `tests/test_engine_gate_grapple_pin.py`

| # | Test | Check |
|---|------|-------|
| GP-01 | `GrappleIntent` against non-grappled target → normal grapple path (no pin) | `grapple_established` event, not `pin_established` |
| GP-02 | `GrappleIntent` against already-grappled target, check succeeds → `pin_established` emitted | event_type == "pin_established" |
| GP-03 | `GrappleIntent` against already-grappled target, check fails → `pin_attempt_failed` | no `pin_established` |
| GP-04 | After `pin_established`: target has `PINNED` condition, NOT `GRAPPLED` | `ConditionType.PINNED` in target conditions; `GRAPPLED` removed |
| GP-05 | After `pin_established`: target has `loses_dex_to_ac=True` and `ac_modifier_melee=-4` | condition modifiers match helpless profile |
| GP-06 | `PinEscapeIntent` against actually-pinned target, check succeeds → `pin_escape_success`, target reverts to `GRAPPLED` | event + condition |
| GP-07 | `PinEscapeIntent`, check fails → `pin_escape_failed`, target still `PINNED` | condition unchanged |
| GP-08 | `PinEscapeIntent` when not pinned → `pin_escape_invalid` event | event_type == "pin_escape_invalid" |
| GP-09 | `grapple_pairs` entry persists through pin escalation | active_combat.grapple_pairs contains pair |
| GP-10 | Zero regressions on CP-22 gate (grapple initiation and escape tests) | full suite pass |

**Test count target:** 10 checks → Gate `ENGINE-GRAPPLE-PIN` 10/10.

---

## 7. What This WO Does NOT Do

- Does not implement coup de grace action (PHB p.153 — separate WO scope)
- Does not enforce "pinned entity cannot cast spells" (action prohibition is metadata-only per CP-16 scope)
- Does not implement the grappler's option to deal damage while maintaining pin (PHB p.156 — degraded in CP-22)
- Does not change `grapple_pairs` structure or escape mechanics (CP-22 escape remains unchanged)

---

## 8. Preflight

```bash
cd f:/DnD-3.5
python -m pytest tests/test_engine_gate_grapple_pin.py -v
# GP-01 through GP-10 must pass.
python -m pytest tests/ -x --tb=short
# Zero new regressions.
```
