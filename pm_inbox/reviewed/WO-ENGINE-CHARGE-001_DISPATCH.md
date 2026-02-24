# WO-ENGINE-CHARGE-001 — Charge Action Wire

```
Issued    : 2026-02-24
Authority : PM Slate
Gate      : ENGINE-CHARGE (10 tests, prefix CH-)
Parallel  : YES — new intent type + new resolver function; does not touch
            dying_resolver.py, nonlethal path, DR path, CDG path, or
            concentration. The only shared-field write is an additive new key
            in EF.TEMPORARY_MODIFIERS ("charge_ac"). No existing keys are
            modified.
Blocks    : None
Blocked-by: None
```

---

## §1 Target Lock

### What Is Missing

The engine has no representation of the Charge action (PHB p.150-151). A
player who says "I charge the orc" currently has no legal routing path:
there is no `ChargeIntent`, no resolver, and no action-economy mapping. The
+2 attack bonus and -2 AC penalty that define a charge do not exist anywhere
in the codebase. Spirited Charge feat interaction with mounted state is also
unimplemented.

### What "Done" Means

1. `ChargeIntent` dataclass exists in `aidm/schemas/intents.py` and is
   included in the `Intent` type alias and `parse_intent()` dispatch.
2. `ChargeIntent` maps to `"full_round"` in `action_economy._build_action_types()`.
3. `resolve_charge()` exists in `aidm/core/attack_resolver.py`, emits a
   `charge_attack` event, applies +2 to `intent.attack_bonus` before calling
   `resolve_attack()`, writes `{"charge_ac": -2}` into the charger's
   `EF.TEMPORARY_MODIFIERS`, and handles Spirited Charge damage multiplication.
4. `apply_charge_events()` exists in `aidm/core/attack_resolver.py` and
   handles `charge_attack`, `hp_changed`, `entity_defeated`, `entity_dying`,
   and `entity_disabled` event types.
5. `execute_turn()` in `aidm/core/play_loop.py` routes `ChargeIntent` to
   `resolve_charge()`, clears `"charge_ac"` from the charger's
   `EF.TEMPORARY_MODIFIERS` at turn-start before any other processing, and
   threads concentration-break checks over the resulting HP events (matching
   the AttackIntent pattern at line 1604).
6. Gate ENGINE-CHARGE passes all 10 tests (CH-01 through CH-10).

---

## §2 PHB Rule Reference

Source: Player's Handbook v3.5, pp.150-151.

> **Charge** (Full-Round Action)
>
> Charging is a special full-round action that allows you to move up to twice
> your speed and attack during the action. Charging, however, carries tight
> restrictions on how you can move.
>
> *Movement During a Charge*
> You must move before your attack, not after. You must move at least 10 feet
> (2 squares) and may move up to double your speed directly toward the
> designated opponent. If you move a distance equal to your speed or less (and
> moving is a separate move action), you can also draw a weapon during a charge
> attack if your base attack bonus is +1 or higher. You must have a clear path
> toward the opponent, and nothing can hinder your movement (such as difficult
> terrain or obstacles). You must move to the closest position from which you
> can attack the opponent. If this position is occupied or otherwise blocked,
> you can't charge.
>
> *Attacking on a Charge*
> After moving, you may make a single melee attack. You get a +2 bonus on the
> attack roll. You and your mount also each take a –2 penalty to AC until the
> start of your next turn.
>
> Even if you have extra attacks, such as from having a high enough base attack
> bonus or from using multiple weapons, you only get a single attack during a
> charge.

Additional rule context (PHB p.137):

> Moving out of a threatened square provokes an attack of opportunity from the
> threatening opponent. This applies to movement during a charge.

Spirited Charge (PHB p.100, Complete Warrior feat):

> When mounted and using the charge action, you deal double damage with a
> melee weapon (or triple damage with a lance).

---

## §3 New Entity Fields

No new `EF` constants are required. The implementation uses two existing
fields:

| Field | Constant | Introduced | Usage |
|---|---|---|---|
| `temporary_modifiers` | `EF.TEMPORARY_MODIFIERS` | CP-18 | Receives `{"charge_ac": -2}` after a charge |
| `feats` | `EF.FEATS` | WO-034 | Checked for `"spirited_charge"` string |
| `mounted_state` | `EF.MOUNTED_STATE` | CP-18A | Checked for mount presence (Spirited Charge) |

**No additions to `aidm/schemas/entity_fields.py` are needed for this WO.**

If `EF.TEMPORARY_MODIFIERS` is absent on an entity dict, the resolver must
treat it as an empty dict and initialise it. Pattern: `entity.get(EF.TEMPORARY_MODIFIERS, {})`.

---

## §4 Implementation Spec

### §4.1 New Intent — `ChargeIntent` in `aidm/schemas/intents.py`

Add after the `PrepareSpellsIntent` class (after line 299) and before the
`Intent` type alias (currently line 303).

```python
@dataclass
class ChargeIntent:
    """Intent to perform a charge action (PHB p.150-151).

    A charge is a full-round action: move up to 2× speed in a straight line
    toward target, then make one melee attack at +2. Charger takes -2 AC
    until start of next turn.

    WO-ENGINE-CHARGE-001
    """

    attacker_id: str
    """Entity ID of the charging entity."""

    target_id: str
    """Entity ID of the charge target (must be on opposing team)."""

    weapon: dict
    """Weapon dict in Weapon-schema format (same shape as AttackIntent.weapon)."""

    path_clear: bool = True
    """DM/AI assertion that the charge path is unobstructed.
    Set False if difficult terrain, obstacles, or blocking creatures are
    present. When False, the resolver emits intent_validation_failed with
    reason 'charge_path_blocked' and does not proceed to attack resolution.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": "charge",
            "attacker_id": self.attacker_id,
            "target_id": self.target_id,
            "weapon": self.weapon,
            "path_clear": self.path_clear,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChargeIntent":
        """Create from dictionary."""
        if data.get("type") != "charge":
            raise IntentParseError(
                f"Expected type 'charge', got '{data.get('type')}'"
            )
        return cls(
            attacker_id=data["attacker_id"],
            target_id=data["target_id"],
            weapon=data["weapon"],
            path_clear=data.get("path_clear", True),
        )
```

Update the `Intent` type alias (currently line 303):

```python
Intent = (
    CastSpellIntent | MoveIntent | DeclaredAttackIntent | BuyIntent
    | RestIntent | SummonCompanionIntent | PrepareSpellsIntent | ChargeIntent
)
```

Add `"charge"` branch to `parse_intent()` (after the `"prepare_spells"` branch,
before the `else` raise):

```python
elif intent_type == "charge":
    return ChargeIntent.from_dict(data)
```

### §4.2 Action Economy Mapping — `aidm/core/action_economy.py`

In `_build_action_types()`, add the following line after the
`MountedMoveIntent` entry (currently line 151):

```python
_try_add(mapping, "aidm.schemas.intents", "ChargeIntent", "full_round")
```

This causes `get_action_type(ChargeIntent(...))` to return `"full_round"`,
which `ActionBudget.can_use("full_round")` accepts only when both
`standard_used` and `move_used` are False (i.e., first action of turn only).
`ActionBudget.consume("full_round")` sets `full_round_used`, `standard_used`,
and `move_used` to True, preventing further actions.

### §4.3 Resolver — `resolve_charge()` in `aidm/core/attack_resolver.py`

Add `resolve_charge()` and `apply_charge_events()` at the bottom of
`aidm/core/attack_resolver.py` (after `apply_attack_events()` which ends at
line 584).

Full signature:

```python
def resolve_charge(
    intent: "ChargeIntent",
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
```

Implementation steps in order:

**Step 1 — path_clear validation.**
If `intent.path_clear` is False, emit `intent_validation_failed` with
`reason: "charge_path_blocked"` and return immediately (no attack roll).

```python
if not intent.path_clear:
    return [Event(
        event_id=next_event_id,
        event_type="intent_validation_failed",
        timestamp=timestamp,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "reason": "charge_path_blocked",
        },
        citations=[{"source_id": "681f92bc94ff", "page": 150}],
    )]
```

**Step 2 — target validation.**
Check that `intent.target_id` is in `world_state.entities`. Check that the
target is not defeated (i.e., `entity.get(EF.DEFEATED, False)` is False).
If either check fails, emit `intent_validation_failed` with
`reason: "target_not_found"` or `reason: "target_already_defeated"` and
return.

```python
target = world_state.entities.get(intent.target_id)
if target is None:
    return [Event(event_id=next_event_id, event_type="intent_validation_failed",
                  timestamp=timestamp,
                  payload={"attacker_id": intent.attacker_id,
                           "target_id": intent.target_id,
                           "reason": "target_not_found"},
                  citations=[{"source_id": "681f92bc94ff", "page": 150}])]
if target.get(EF.DEFEATED, False):
    return [Event(event_id=next_event_id, event_type="intent_validation_failed",
                  timestamp=timestamp,
                  payload={"attacker_id": intent.attacker_id,
                           "target_id": intent.target_id,
                           "reason": "target_already_defeated"},
                  citations=[{"source_id": "681f92bc94ff", "page": 150}])]
```

**Step 3 — build AttackIntent with +2 bonus.**
Import `Weapon` from `aidm.schemas.attack` and construct an `AttackIntent`
using the entity's existing `EF.ATTACK_BONUS` plus 2 for the charge:

```python
from aidm.schemas.attack import AttackIntent, Weapon

attacker = world_state.entities[intent.attacker_id]
base_attack_bonus = attacker.get(EF.ATTACK_BONUS, 0)
charge_attack_bonus = base_attack_bonus + 2          # PHB p.150: +2 on charge

weapon_obj = Weapon(**intent.weapon)                 # dict → Weapon dataclass

attack_intent = AttackIntent(
    attacker_id=intent.attacker_id,
    target_id=intent.target_id,
    attack_bonus=charge_attack_bonus,
    weapon=weapon_obj,
)
```

**Step 4 — emit `charge_attack` event (before attack roll events).**

```python
events = []
current_event_id = next_event_id

events.append(Event(
    event_id=current_event_id,
    event_type="charge_attack",
    timestamp=timestamp,
    payload={
        "attacker_id": intent.attacker_id,
        "target_id": intent.target_id,
        "attack_bonus_applied": 2,
        "ac_penalty_applied": -2,
    },
    citations=[{"source_id": "681f92bc94ff", "page": 150}],
))
current_event_id += 1
```

**Step 5 — call `resolve_attack()`.**

```python
attack_events = resolve_attack(
    intent=attack_intent,
    world_state=world_state,
    rng=rng,
    next_event_id=current_event_id,
    timestamp=timestamp + 0.1,
)
events.extend(attack_events)
current_event_id += len(attack_events)
```

**Step 6 — Spirited Charge damage multiplier.**
Check only if a hit occurred (look for an `attack_roll` event with
`payload["hit"] == True` in `attack_events`). If hit:

- Check `EF.FEATS`: `"spirited_charge" in attacker.get(EF.FEATS, [])`
- Check `EF.MOUNTED_STATE`: `attacker.get(EF.MOUNTED_STATE) is not None`
- If both true, determine multiplier:
  - `weapon["weapon_type"] == "lance"` → multiplier = 3
  - Otherwise → multiplier = 2
- Find the `hp_changed` event in `attack_events`. Replace it in-place with a
  new Event whose `payload["delta"]` is `original_delta * multiplier` and
  `payload["hp_after"]` is recalculated accordingly.

> Note: The `hp_changed` event's `delta` is negative (damage). Multiply the
> absolute value, then re-negate. Example: delta=-8, multiplier=2 → delta=-16.
> Recalculate `hp_after = hp_before + new_delta` where `hp_before` comes from
> `world_state.entities[target_id][EF.HP_CURRENT]`.

Emit a `spirited_charge_multiplier` event immediately after the modified
`hp_changed` event if the multiplier was applied, for narration transparency:

```python
Event(
    event_id=current_event_id,
    event_type="spirited_charge_multiplier",
    timestamp=timestamp + 0.25,
    payload={
        "attacker_id": intent.attacker_id,
        "target_id": intent.target_id,
        "multiplier": multiplier,
        "weapon_type": weapon.get("weapon_type", "unknown"),
    },
    citations=[{"source_id": "681f92bc94ff", "page": 100}],
)
```

**Step 7 — emit `charge_ac_applied` event.**
This event triggers `apply_charge_events()` to write the AC penalty:

```python
events.append(Event(
    event_id=current_event_id,
    event_type="charge_ac_applied",
    timestamp=timestamp + 0.3,
    payload={
        "attacker_id": intent.attacker_id,
        "charge_ac_penalty": -2,
    },
    citations=[{"source_id": "681f92bc94ff", "page": 150}],
))
```

**Step 8 — return all events.**

```python
return events
```

### §4.4 State Applicator — `apply_charge_events()` in `aidm/core/attack_resolver.py`

Add immediately after `resolve_charge()`:

```python
def apply_charge_events(world_state: WorldState, events: List[Event]) -> WorldState:
    """Apply charge resolution events to world state.

    Handles charge_attack (no-op — annotation only), charge_ac_applied
    (writes EF.TEMPORARY_MODIFIERS["charge_ac"] = -2 on attacker),
    and delegates hp_changed / entity_defeated / entity_dying /
    entity_disabled to the same mutation logic as apply_attack_events().

    WO-ENGINE-CHARGE-001
    """
    entities = deepcopy(world_state.entities)

    for event in events:
        if event.event_type == "charge_ac_applied":
            attacker_id = event.payload["attacker_id"]
            if attacker_id in entities:
                mods = dict(entities[attacker_id].get(EF.TEMPORARY_MODIFIERS, {}))
                mods["charge_ac"] = event.payload["charge_ac_penalty"]   # -2
                entities[attacker_id][EF.TEMPORARY_MODIFIERS] = mods

        elif event.event_type == "hp_changed":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.HP_CURRENT] = event.payload["hp_after"]

        elif event.event_type == "entity_defeated":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.DEFEATED] = True
                entities[entity_id][EF.DYING] = False
                entities[entity_id][EF.DISABLED] = False
                entities[entity_id][EF.STABLE] = False

        elif event.event_type == "entity_disabled":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.DISABLED] = True
                entities[entity_id][EF.DYING] = False

        elif event.event_type == "entity_dying":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.DYING] = True
                entities[entity_id][EF.DISABLED] = False
                entities[entity_id][EF.DEFEATED] = False

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )
```

### §4.5 AC Penalty Duration — Turn-Start Clearance in `aidm/core/play_loop.py`

The -2 AC penalty (`EF.TEMPORARY_MODIFIERS["charge_ac"]`) must be removed at
the **start of the charger's next turn**, before any other processing.

Insert the following block in `execute_turn()` immediately after the
`turn_start` event is appended (after line 1125, before the
`actions_prohibited` gate check at line 1127):

```python
    # WO-ENGINE-CHARGE-001: Clear charge AC penalty at start of actor's turn.
    # The -2 AC from a charge (PHB p.150) expires at the start of the charger's
    # next turn. Clearing here (after turn_start, before any action processing)
    # ensures the penalty applies for the full intervening round.
    _actor_entity = world_state.entities.get(turn_ctx.actor_id, {})
    _temp_mods = _actor_entity.get(EF.TEMPORARY_MODIFIERS, {})
    if "charge_ac" in _temp_mods:
        _entities_cleared = deepcopy(world_state.entities)
        _cleared_mods = dict(_entities_cleared[turn_ctx.actor_id].get(EF.TEMPORARY_MODIFIERS, {}))
        del _cleared_mods["charge_ac"]
        _entities_cleared[turn_ctx.actor_id][EF.TEMPORARY_MODIFIERS] = _cleared_mods
        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=_entities_cleared,
            active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
        )
        events.append(Event(
            event_id=current_event_id,
            event_type="charge_ac_expired",
            timestamp=timestamp + 0.01,
            payload={"entity_id": turn_ctx.actor_id},
            citations=[{"source_id": "681f92bc94ff", "page": 150}],
        ))
        current_event_id += 1
```

**Rationale for turn-start approach vs. duration_tracker:** The duration
tracker fires at round-end (`_tick_duration_tracker` in
`combat_controller.py`), which would clear the penalty after all actors in
a round have acted. A charge at initiative 20 would lose its AC penalty
before the enemy at initiative 5 gets their turn — incorrect. Turn-start
clearance is exact: the penalty persists for all intervening actors and
is removed precisely when the charger acts again.

### §4.6 AoO Provocation During Charge Movement

The charge movement provokes AoOs from any enemy whose threatened squares
the charger passes through (PHB p.137, p.150).

In `execute_turn()`, in the new `ChargeIntent` routing block (see §4.7),
call `check_aoo_triggers()` and `resolve_aoo_sequence()` for the movement
leg of the charge before the attack. Use a synthetic `StepMoveIntent` with
`from_pos = attacker_current_pos` and `to_pos = target_adjacent_pos`
(simplified: treat as a single movement provocation rather than per-square
path tracking — full path tracking is deferred, see §8).

If `resolve_aoo_sequence().provoker_defeated` is True, emit `action_aborted`
(reason: `"defeated_by_aoo_during_charge_movement"`) and return early,
matching the existing pattern at lines 1551-1585.

If `intent.path_clear` is False, the validator in `resolve_charge()` (§4.3
Step 1) fires before AoO resolution is reached.

### §4.7 Routing in `execute_turn()` — `aidm/core/play_loop.py`

Add the following `elif` block after the `PrepareSpellsIntent` block (which
ends around line 2044) and before the `elif doctrine is not None` fallback
(line 2047):

```python
        elif isinstance(combat_intent, ChargeIntent):
            # WO-ENGINE-CHARGE-001: Charge action (PHB p.150-151)
            # AoO for charge movement (simplified: one trigger for full path)
            from aidm.schemas.attack import StepMoveIntent as _StepMoveIntent
            from aidm.schemas.position import Position as _Position
            attacker_pos = world_state.entities.get(turn_ctx.actor_id, {}).get(EF.POSITION)
            target_pos = world_state.entities.get(combat_intent.target_id, {}).get(EF.POSITION)
            _charge_aoo_events = []
            _charge_aoo_defeated = False
            if attacker_pos and target_pos:
                _charge_step = _StepMoveIntent(
                    actor_id=turn_ctx.actor_id,
                    from_pos=_Position(x=attacker_pos["x"], y=attacker_pos["y"]),
                    to_pos=_Position(x=target_pos["x"], y=target_pos["y"]),
                )
                _charge_aoo_triggers = check_aoo_triggers(world_state, turn_ctx.actor_id, _charge_step)
                if _charge_aoo_triggers:
                    _charge_aoo_result = resolve_aoo_sequence(
                        triggers=_charge_aoo_triggers,
                        world_state=world_state,
                        rng=rng,
                        next_event_id=current_event_id,
                        timestamp=timestamp + 0.05,
                    )
                    _charge_aoo_events = _charge_aoo_result.events
                    events.extend(_charge_aoo_events)
                    current_event_id += len(_charge_aoo_events)
                    world_state = apply_attack_events(world_state, _charge_aoo_events)
                    if _charge_aoo_result.provoker_defeated:
                        _charge_aoo_defeated = True

            if _charge_aoo_defeated:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="action_aborted",
                    timestamp=timestamp + 0.2,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "reason": "defeated_by_aoo_during_charge_movement",
                        "turn_index": turn_ctx.turn_index,
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 137}],
                ))
                current_event_id += 1
                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.3,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events),
                    },
                ))
                return TurnResult(
                    status="ok",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    narration="action_aborted_by_aoo",
                )

            # Resolve the charge attack
            from aidm.core.attack_resolver import resolve_charge, apply_charge_events
            combat_events = resolve_charge(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1,
            )
            events.extend(combat_events)
            current_event_id += len(combat_events)
            world_state = apply_charge_events(world_state, combat_events)

            # WO-015 pattern: concentration break on damage
            hp_events = [e for e in combat_events if e.event_type == "hp_changed"]
            for hp_event in hp_events:
                target_id = hp_event.payload.get("entity_id")
                damage = abs(hp_event.payload.get("delta", 0))
                if damage > 0 and target_id:
                    conc_events, world_state = _check_concentration_break(
                        caster_id=target_id,
                        damage_dealt=damage,
                        world_state=world_state,
                        rng=rng,
                        next_event_id=current_event_id,
                        timestamp=timestamp + 0.15,
                    )
                    events.extend(conc_events)
                    current_event_id += len(conc_events)

            narration = "charge_complete"
```

Add `ChargeIntent` to the import from `aidm.schemas.intents` at the top of
`play_loop.py`. Locate the existing intents imports (around lines 63-75 where
`SummonCompanionIntent`, `RestIntent`, `PrepareSpellsIntent` are imported)
and add `ChargeIntent`:

```python
from aidm.schemas.intents import (
    MoveIntent, CastSpellIntent, SummonCompanionIntent,
    RestIntent, PrepareSpellsIntent, ChargeIntent,   # <-- add ChargeIntent
)
```

---

## §5 Event Types

| Event Type | Emitter | Payload Keys | Meaning |
|---|---|---|---|
| `charge_attack` | `resolve_charge()` | `attacker_id`, `target_id`, `attack_bonus_applied` (+2), `ac_penalty_applied` (-2) | Annotates that a charge occurred; emitted before attack roll events |
| `charge_ac_applied` | `resolve_charge()` | `attacker_id`, `charge_ac_penalty` (-2) | Triggers AC penalty write in `apply_charge_events()` |
| `charge_ac_expired` | `execute_turn()` turn-start block | `entity_id` | Emitted when `"charge_ac"` key is cleared from `EF.TEMPORARY_MODIFIERS` |
| `intent_validation_failed` | `resolve_charge()` | `attacker_id`, `target_id`, `reason` (`"charge_path_blocked"` or `"target_already_defeated"` or `"target_not_found"`) | Charge rejected before any RNG consumption |
| `spirited_charge_multiplier` | `resolve_charge()` | `attacker_id`, `target_id`, `multiplier` (2 or 3), `weapon_type` | Emitted when Spirited Charge damage multiplication is applied |
| `action_aborted` | `execute_turn()` | `actor_id`, `reason: "defeated_by_aoo_during_charge_movement"`, `turn_index` | Charge movement AoO killed the charger; attack never resolves |

Existing event types re-used (not new):

| Event Type | Source | Notes |
|---|---|---|
| `attack_roll` | `resolve_attack()` | Standard hit/miss event; emitted inside `resolve_charge()` via `resolve_attack()` |
| `hp_changed` | `resolve_attack()` | Standard HP delta event; may be replaced in-place by Spirited Charge multiplier logic |
| `entity_defeated` / `entity_dying` / `entity_disabled` | `resolve_attack()` | Standard death/dying/disabled events |
| `ACTION_DENIED` | `execute_turn()` action economy gate | Emitted if `ChargeIntent` arrives when `full_round` slot is already consumed |

---

## §6 Regression Risk

**Low overall.** All changes are additive.

| Area | Risk | Mitigation |
|---|---|---|
| `attack_resolver.py` | New functions appended at end of file — no edits to existing functions. Existing `resolve_attack()` and `apply_attack_events()` are untouched. | Additive-only; no line insertion into existing logic |
| `intents.py` | New `ChargeIntent` dataclass added before the `Intent` alias. `parse_intent()` gets one new `elif` branch. | Pattern matches all existing intent additions; no existing branch touched |
| `action_economy.py` | One `_try_add()` call appended to `_build_action_types()`. | Uses the existing safe-import pattern; failure is silent |
| `play_loop.py` | Two insertion points: (1) turn-start `charge_ac` clearance block after line 1125; (2) new `elif isinstance(combat_intent, ChargeIntent)` block before the `doctrine` fallback. | Insertion (1) is guarded by `if "charge_ac" in _temp_mods` — does nothing unless a charge occurred. Insertion (2) is an `elif` on a new type; all existing `elif` branches are untouched |
| Gold masters | `charge_attack` is a new event type not present in existing JSONL fixtures. Gold master tests check existing scenarios which never emit `charge_attack`; no gold master should be invalidated. Verify with `pytest tests/` after implementation. | Gold masters unaffected |
| `EF.TEMPORARY_MODIFIERS` | Existing code that reads `EF.TEMPORARY_MODIFIERS` (e.g. condition modifiers, attack resolver) uses `.get(EF.TEMPORARY_MODIFIERS, {})` and dict-key lookups. Adding `"charge_ac"` key is fully additive. | No existing reader breaks on an extra key |

---

## §7 Gate Spec — ENGINE-CHARGE (10 tests)

Test file: `tests/test_engine_gate_charge.py`

All tests use deterministic RNG (seed 0 or fixed seed), a minimal WorldState
with two entities on opposing teams, and `EF.ATTACK_BONUS`, `EF.AC`,
`EF.HP_CURRENT`, `EF.HP_MAX`, `EF.POSITION` set on each entity. The
`ChargeIntent.weapon` dict must be a valid `Weapon`-schema dict (fields:
`damage_dice`, `damage_bonus`, `critical_range`, `critical_multiplier`,
`is_ranged`, `grip`, `damage_type`, `weapon_type`, `range_increment`,
`is_two_handed`).

| # | ID | Test Description | Pass Criterion |
|---|---|---|---|
| 1 | CH-01 | Charge attack applies +2 attack bonus | `charge_attack` event present with `attack_bonus_applied == 2`; `attack_roll` event's recorded `attack_bonus` equals entity `EF.ATTACK_BONUS + 2` |
| 2 | CH-02 | Charge applies -2 AC penalty to charger | After `apply_charge_events()`, `world_state.entities[attacker_id][EF.TEMPORARY_MODIFIERS]["charge_ac"] == -2` |
| 3 | CH-03 | `charge_attack` event emitted before attack roll events | In returned event list, index of `charge_attack` event < index of first `attack_roll` event |
| 4 | CH-04 | Charge is full-round action — denied if standard already used | Build a WorldState with `active_combat["action_budget"]` showing `standard_used=True`. Execute turn with `ChargeIntent`. Assert `ACTION_DENIED` event with `slot == "full_round"` is emitted and no `charge_attack` event appears |
| 5 | CH-05 | `path_clear=False` emits `intent_validation_failed` | `resolve_charge()` with `path_clear=False` returns list containing exactly one event of type `intent_validation_failed` with `reason == "charge_path_blocked"`; no `attack_roll` event present |
| 6 | CH-06 | Spirited Charge + mounted → damage ×2 | Entity has `EF.FEATS = ["spirited_charge"]` and `EF.MOUNTED_STATE = {"mount_id": "horse_01"}`. On a hit, `hp_changed` delta is double the baseline single-attack damage. `spirited_charge_multiplier` event with `multiplier == 2` present |
| 7 | CH-07 | Spirited Charge + mounted + lance → damage ×3 | Same as CH-06 but `weapon["weapon_type"] == "lance"`. `hp_changed` delta is triple baseline. `spirited_charge_multiplier` event with `multiplier == 3` present |
| 8 | CH-08 | Spirited Charge feat present but no mount → normal damage | Entity has `EF.FEATS = ["spirited_charge"]` but `EF.MOUNTED_STATE` is absent (or None). Damage is ×1. No `spirited_charge_multiplier` event |
| 9 | CH-09 | Charge AC penalty clears at start of charger's next turn | Execute a charge turn for entity A (penalty written). Then execute a second turn for entity A. Assert `charge_ac_expired` event emitted in second turn events, and `EF.TEMPORARY_MODIFIERS` on entity A does not contain `"charge_ac"` key after second turn |
| 10 | CH-10 | Charge against DEFEATED target → `intent_validation_failed` | Target entity has `EF.DEFEATED = True`. `resolve_charge()` returns `intent_validation_failed` with `reason == "target_already_defeated"`. No `attack_roll` event. No `charge_ac_applied` event |

---

## §8 What This WO Does NOT Do

- **No per-square path tracking.** Charge movement AoO is resolved as a single
  trigger (origin → adjacent-to-target), not stepped square-by-square. Full
  path AoO tracking (matching the `FullMoveIntent` pattern at play_loop.py
  lines 1724-1775) is deferred to a future WO (e.g. WO-ENGINE-CHARGE-002).

- **No minimum distance validation.** The PHB requires the charger move at
  least 10 ft (2 squares). This WO does not validate `path_cost_ft() >= 10`.
  The `path_clear` flag is an AI/DM honor-system assertion covering all
  geometric preconditions including minimum distance. Distance validation is
  deferred.

- **No maximum distance validation.** The PHB caps charge movement at 2×
  speed. Speed computation (accounting for encumbrance via `EF.BASE_SPEED`,
  `EF.ENCUMBRANCE_LOAD`) is not performed here. Deferred.

- **No Bull Rush on charge.** PHB p.150 allows substituting a Bull Rush for
  the attack on a charge. `BullRushIntent` exists in `aidm/schemas/maneuvers.py`
  but wiring it as the charge attack is out of scope for this WO.

- **No lance double-damage for non-Spirited-Charge mounted charges.** PHB
  p.113 notes a lance deals double damage when used from a charging mount
  even without the Spirited Charge feat. This WO only implements the feat
  variant. Non-feat lance interaction is deferred.

- **No Pounce (full attack on charge).** Some monster special abilities
  (e.g. lion Pounce) allow a full attack at the end of a charge. Not in scope.

- **No AC penalty propagation into attack resolution.** The `"charge_ac": -2`
  key in `EF.TEMPORARY_MODIFIERS` is written by this WO but is not yet read
  by `resolve_attack()` when computing `target_ac`. A follow-up WO must add
  `"charge_ac"` to the condition/modifier reader so enemies correctly get +2
  to hit the charging entity during the intervening round. This WO only
  establishes the write path and duration lifecycle.

- **No mounted charge speed.** When mounted, PHB p.150 states the charge uses
  the mount's speed. This WO does not compute mount-speed overrides.
  `EF.MOUNTED_STATE` is only consulted for the Spirited Charge multiplier.

---

## §9 Preflight

Run before opening the gate PR:

```bash
# From repo root

# 1. Confirm new intent parses without error
python -c "
from aidm.schemas.intents import ChargeIntent, parse_intent
ci = ChargeIntent(
    attacker_id='hero',
    target_id='orc',
    weapon={
        'damage_dice': '1d8', 'damage_bonus': 2,
        'critical_range': 20, 'critical_multiplier': 2,
        'is_ranged': False, 'grip': 'one-handed',
        'damage_type': 'slashing', 'weapon_type': 'longsword',
        'range_increment': 0, 'is_two_handed': False,
    },
    path_clear=True,
)
print('ChargeIntent OK:', ci.to_dict())
rt = parse_intent({'type': 'charge', 'attacker_id': 'hero',
                   'target_id': 'orc', 'weapon': ci.weapon,
                   'path_clear': True})
print('parse_intent round-trip OK:', type(rt).__name__)
"

# 2. Confirm action economy mapping resolves to full_round
python -c "
from aidm.schemas.intents import ChargeIntent
from aidm.core.action_economy import get_action_type
ci = ChargeIntent(attacker_id='a', target_id='b', weapon={})
print('action_type:', get_action_type(ci))   # expect: full_round
"

# 3. Run the new gate tests
pytest tests/test_engine_gate_charge.py -v

# 4. Run existing engine gates to confirm no regression
pytest tests/test_engine_gate_cp17.py \
       tests/test_engine_gate_cp18.py \
       tests/test_engine_gate_cp19.py \
       tests/test_engine_gate_cp22.py \
       tests/test_engine_gate_cp23.py \
       tests/test_engine_gate_cp24.py \
       tests/test_engine_gate_xp01.py \
       -v

# 5. Run full test suite for broad regression
pytest tests/ -x -q
```

Gate passes when `pytest tests/test_engine_gate_charge.py` reports
`10 passed, 0 failed` and the full suite shows no new failures relative to
the pre-WO baseline.
