# WO-ENGINE-COUP-DE-GRACE-001 — Coup de Grâce

**Status:** DISPATCHED
**Date:** 2026-02-24
**Priority:** P2 — Combat correctness (helpless target mechanics)
**Parallel-safe:** YES — new intent type, new function in existing module; no shared code path with DR-001, NONLETHAL-001, CONCENTRATION-001, or TWF
**Estimated complexity:** Medium (1–2 sessions)
**Gate:** ENGINE-COUP-DE-GRACE — 10 tests

---

## §1 Target Lock

| Item | Value |
|------|-------|
| PHB rule | p.153 — Coup de Grâce |
| New intent | `CoupDeGraceIntent` — `aidm/schemas/intents.py` |
| New resolver function | `resolve_coup_de_grace()` — `aidm/core/attack_resolver.py` |
| New apply function | `apply_cdg_events()` — `aidm/core/attack_resolver.py` |
| Action economy mapping | `aidm/core/action_economy.py` — `_build_action_types()` |
| Routing | `aidm/core/play_loop.py` — `execute_turn()` |
| New EF constants | `EF.CRIT_IMMUNE` — `aidm/schemas/entity_fields.py` |
| Test file | `tests/test_engine_gate_cdg.py` (new file) |

---

## §2 PHB Rule

PHB 3.5e p.153:

> As a full-round action, you can use a melee weapon to deliver a coup de grâce to a helpless opponent. You can also use a bow or crossbow, provided you are adjacent to the target. You automatically hit and score a critical hit. If the defender survives the damage, he must make a Fortitude save (DC 10 + damage dealt) or die. Delivering a coup de grâce provokes attacks of opportunity from threatening foes. You can't deliver a coup de grâce to a creature that is immune to critical hits or not subject to extra damage from critical hits.

**Eligible targets** (disjunction — any one condition qualifies):
- `entity.get(EF.DYING, False) == True` (HP between −1 and −9)
- Entity's `EF.CONDITIONS` dict contains `"helpless"` key
- Entity's `EF.CONDITIONS` dict contains `"unconscious"` key
- Entity's `EF.CONDITIONS` dict contains `"pinned"` key
- Entity's `EF.CONDITIONS` dict contains `"paralyzed"` key

A target that is only `EF.DISABLED == True` (HP == 0) but has none of the above is **NOT** a valid CDG target.

**Crit-immune check:** If the target entity dict contains key `EF.CRIT_IMMUNE` and its value is `True`, CDG is illegal. If the key is absent, treat as `False` (not immune). See §3 for the new EF constant.

**Damage formula (PHB p.8, p.140):** On a coup de grâce, all damage dice AND all applicable bonuses are multiplied by `crit_multiplier`. The formula is:

```
damage = (sum(damage_dice_rolls) + weapon.damage_bonus + str_modifier_adjusted_for_grip) × crit_multiplier
```

Where `str_modifier_adjusted_for_grip` follows the existing grip logic in `resolve_attack()` (lines 393–399 of `aidm/core/attack_resolver.py`):
- `"two-handed"` grip: `int(str_mod * 1.5)`
- `"off-hand"` grip: `int(str_mod * 0.5)`
- all other grips: `str_mod`

**Fort save:** DC = 10 + total damage dealt (pre-DR value, consistent with how PHB phrases it — "damage dealt" means total, before reduction). Fort save total = `d20 + entity.get(EF.SAVE_FORT, 0)`. If the target has condition modifiers on `fort_save_modifier` (e.g., SHAKEN: −2), those are also applied, following the existing pattern in `resolve_attack()`.

---

## §3 New Entity Fields

Add one constant to `aidm/schemas/entity_fields.py`, inside `class _EntityFields`, in the `# --- Combat Status (CP-10) ---` group (after line 52, which currently ends with `DEFEATED = "defeated"`):

```python
# --- Combat Status (CP-10) ---
DEFEATED = "defeated"
CRIT_IMMUNE = "crit_immune"  # Bool: True if creature is immune to critical hits (e.g. undead, constructs, elementals) — WO-ENGINE-COUP-DE-GRACE-001
```

Add the comment `# WO-ENGINE-COUP-DE-GRACE-001` on the same line as the constant so the boundary law audit trail is intact.

No other entity fields are needed. `EF.DYING`, `EF.DISABLED`, `EF.STABLE`, `EF.DEFEATED`, `EF.SAVE_FORT`, `EF.STR_MOD`, and `EF.CONDITIONS` already exist.

---

## §4 Implementation Spec

### 4.1 New dataclass: `CoupDeGraceIntent` in `aidm/schemas/intents.py`

Add after the `PrepareSpellsIntent` dataclass (after line 299) and before the `Intent` type alias (line 303):

```python
@dataclass
class CoupDeGraceIntent:
    """Intent to deliver a coup de grâce to a helpless or dying target.

    PHB p.153: Full-round action. Auto-hit, auto-crit. Fort save or die.
    Provokes AoO from threatening enemies.

    WO-ENGINE-COUP-DE-GRACE-001
    """

    attacker_id: str
    """Entity performing the coup de grâce."""

    target_id: str
    """Must be DYING (EF.DYING == True) or have HELPLESS/UNCONSCIOUS/PINNED/PARALYZED condition."""

    weapon: dict
    """Weapon dict (same format as AttackIntent.weapon fields).
    Must contain: damage_dice (str), damage_bonus (int), crit_multiplier (int, default 2),
    damage_type (str), grip (str).
    """
```

Then update the `Intent` type alias on line 303 and the `parse_intent()` function:

**Line 303** — update the type alias:
```python
Intent = CastSpellIntent | MoveIntent | DeclaredAttackIntent | BuyIntent | RestIntent | SummonCompanionIntent | PrepareSpellsIntent | CoupDeGraceIntent
```

**Inside `parse_intent()`** — add a new branch after the `"prepare_spells"` branch (after line 334, before the `else`):
```python
elif intent_type == "coup_de_grace":
    return CoupDeGraceIntent.from_dict(data)
```

Also add `to_dict()` and `from_dict()` class methods to `CoupDeGraceIntent`:

```python
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "coup_de_grace",
            "attacker_id": self.attacker_id,
            "target_id": self.target_id,
            "weapon": self.weapon,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoupDeGraceIntent":
        if data.get("type") != "coup_de_grace":
            raise IntentParseError(f"Expected type 'coup_de_grace', got '{data.get('type')}'")
        return cls(
            attacker_id=data["attacker_id"],
            target_id=data["target_id"],
            weapon=data["weapon"],
        )
```

### 4.2 Action economy mapping in `aidm/core/action_economy.py`

In `_build_action_types()` (lines 126–153), inside the `# Optional imports` block, add after the last `_try_add` call (after line 151):

```python
_try_add(mapping, "aidm.schemas.intents", "CoupDeGraceIntent", "full_round")
```

This ensures `CoupDeGraceIntent` consumes the `full_round` slot, which also marks `standard_used` and `move_used` via `ActionBudget.consume()`. No changes needed to `ActionBudget` itself.

### 4.3 Routing and validation in `aidm/core/play_loop.py`

Three insertion points, in order:

**4.3.1 — Import** (top of file, line 72 area):

Add `CoupDeGraceIntent` to the existing import from `aidm.schemas.intents`:

```python
from aidm.schemas.intents import SummonCompanionIntent, RestIntent, PrepareSpellsIntent, CoupDeGraceIntent
```

**4.3.2 — Actor ID extraction** (line 1216 area, inside `if combat_intent is not None:` block):

The current block (lines 1216–1217) reads:
```python
if isinstance(combat_intent, (AttackIntent, FullAttackIntent)):
    intent_actor_id = combat_intent.attacker_id
```

Extend this to also cover `CoupDeGraceIntent`:
```python
if isinstance(combat_intent, (AttackIntent, FullAttackIntent, CoupDeGraceIntent)):
    intent_actor_id = combat_intent.attacker_id
```

**4.3.3 — Target existence + defeated validation** (line 1292 area):

The current block (lines 1292–1360) checks `isinstance(combat_intent, (AttackIntent, FullAttackIntent))`. Extend the isinstance check to include `CoupDeGraceIntent`:

```python
if isinstance(combat_intent, (AttackIntent, FullAttackIntent, CoupDeGraceIntent)):
```

The existing "target not found" and "target already defeated" validation blocks that follow will then apply to CDG intents automatically. No other changes to that block.

**4.3.4 — CDG-specific validation block** (insert after the existing "target already defeated" return at line 1360, before the maneuver isinstance check at line 1362):

```python
        # WO-ENGINE-COUP-DE-GRACE-001: Validate CDG target is helpless/dying
        if isinstance(combat_intent, CoupDeGraceIntent):
            _cdg_target = world_state.entities[combat_intent.target_id]
            _cdg_conditions = _cdg_target.get(EF.CONDITIONS, {})
            _helpless_conditions = {"helpless", "unconscious", "pinned", "paralyzed"}
            _target_is_dying = _cdg_target.get(EF.DYING, False)
            _target_is_helpless = bool(_helpless_conditions & set(_cdg_conditions.keys()))

            if not (_target_is_dying or _target_is_helpless):
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "target_id": combat_intent.target_id,
                        "reason": "target_not_helpless",
                        "turn_index": turn_ctx.turn_index,
                        "target_dying": _target_is_dying,
                        "target_conditions": list(_cdg_conditions.keys()),
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 153}]
                ))
                current_event_id += 1
                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.2,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events),
                    }
                ))
                return TurnResult(
                    status="invalid_intent",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    failure_reason=f"Coup de grâce target {combat_intent.target_id} is not helpless or dying"
                )

            # Validate: crit immunity check
            from aidm.schemas.entity_fields import EF as _EF
            if _cdg_target.get(_EF.CRIT_IMMUNE, False):
                events.append(Event(
                    event_id=current_event_id,
                    event_type="intent_validation_failed",
                    timestamp=timestamp + 0.1,
                    payload={
                        "actor_id": turn_ctx.actor_id,
                        "target_id": combat_intent.target_id,
                        "reason": "target_crit_immune",
                        "turn_index": turn_ctx.turn_index,
                    },
                    citations=[{"source_id": "681f92bc94ff", "page": 153}]
                ))
                current_event_id += 1
                events.append(Event(
                    event_id=current_event_id,
                    event_type="turn_end",
                    timestamp=timestamp + 0.2,
                    payload={
                        "turn_index": turn_ctx.turn_index,
                        "actor_id": turn_ctx.actor_id,
                        "events_emitted": len(events),
                    }
                ))
                return TurnResult(
                    status="invalid_intent",
                    world_state=world_state,
                    events=events,
                    turn_index=turn_ctx.turn_index,
                    failure_reason=f"Coup de grâce invalid: target {combat_intent.target_id} is immune to critical hits"
                )
```

**4.3.5 — Resolver routing** (line 1559 area, inside `# Route to appropriate resolver`):

After the `elif isinstance(combat_intent, FullAttackIntent):` block ends (after line 1631) and before the `elif isinstance(combat_intent, StepMoveIntent):` block (line 1633), insert:

```python
        elif isinstance(combat_intent, CoupDeGraceIntent):
            # WO-ENGINE-COUP-DE-GRACE-001: Coup de grâce resolution
            # AoO has already been resolved above (CDG provokes per PHB p.153)
            from aidm.core.attack_resolver import resolve_coup_de_grace, apply_cdg_events
            combat_events = resolve_coup_de_grace(
                intent=combat_intent,
                world_state=world_state,
                rng=rng,
                next_event_id=current_event_id,
                timestamp=timestamp + 0.1
            )
            events.extend(combat_events)
            current_event_id += len(combat_events)

            # Apply events to get updated state
            world_state = apply_cdg_events(world_state, combat_events)

            # WO-015: Check concentration break if target took damage
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

            narration = "coup_de_grace_delivered"
```

### 4.4 `resolve_coup_de_grace()` in `aidm/core/attack_resolver.py`

Add after `apply_attack_events()` (after line 553). The function signature and full implementation:

```python
def resolve_coup_de_grace(
    intent: "CoupDeGraceIntent",
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve a coup de grâce against a helpless or dying target.

    PHB p.153:
    - Auto-hit (no attack roll)
    - Auto-crit (crit_multiplier applied to all damage dice and bonuses)
    - Fort save DC = 10 + damage dealt; failure = immediate death (HP → −10)
    - Provokes AoO (handled by play_loop before this call)

    RNG consumption order (deterministic):
    1. Damage dice (XdY)
    2. Fort save (d20)

    WO-ENGINE-COUP-DE-GRACE-001
    """
    from aidm.schemas.intents import CoupDeGraceIntent  # local to avoid circular
    from aidm.core.dying_resolver import resolve_hp_transition

    events: List[Event] = []
    current_event_id = next_event_id
    combat_rng = rng.stream("combat")

    attacker = world_state.entities.get(intent.attacker_id, {})
    target = world_state.entities.get(intent.target_id, {})

    # --- Weapon stats from intent.weapon dict ---
    weapon = intent.weapon
    damage_dice: str = weapon.get("damage_dice", "1d4")
    damage_bonus: int = weapon.get("damage_bonus", 0)
    crit_multiplier: int = weapon.get("crit_multiplier", 2)
    damage_type: str = weapon.get("damage_type", "slashing")
    grip: str = weapon.get("grip", "one-handed")

    # --- STR modifier (grip-adjusted), PHB p.113 ---
    str_mod = attacker.get(EF.STR_MOD, 0)
    if grip == "two-handed":
        str_to_damage = int(str_mod * 1.5)
    elif grip == "off-hand":
        str_to_damage = int(str_mod * 0.5)
    else:
        str_to_damage = str_mod

    # --- Roll damage dice ---
    num_dice, die_size = parse_damage_dice(damage_dice)
    damage_rolls = [combat_rng.randint(1, die_size) for _ in range(num_dice)]

    # --- Crit damage: multiply all dice and bonuses by crit_multiplier ---
    # PHB p.8/p.140: On a crit, multiply damage dice AND all damage bonuses
    base_damage = sum(damage_rolls) + damage_bonus + str_to_damage
    damage_total = max(1, base_damage * crit_multiplier)

    # --- Apply Damage Reduction (WO-048) ---
    from aidm.core.damage_reduction import get_applicable_dr, apply_dr_to_damage
    dr_amount = get_applicable_dr(world_state, intent.target_id, damage_type)
    final_damage, damage_reduced = apply_dr_to_damage(damage_total, dr_amount)

    # --- Emit cdg_damage_roll event (no attack_roll event — auto-hit) ---
    events.append(Event(
        event_id=current_event_id,
        event_type="cdg_damage_roll",
        timestamp=timestamp,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "damage_dice": damage_dice,
            "damage_rolls": damage_rolls,
            "damage_bonus": damage_bonus,
            "str_modifier": str_mod,
            "grip": grip,
            "str_to_damage": str_to_damage,
            "base_damage": base_damage,
            "crit_multiplier": crit_multiplier,
            "damage_total": damage_total,
            "dr_amount": dr_amount,
            "damage_reduced": damage_reduced,
            "final_damage": final_damage,
            "damage_type": damage_type,
            "auto_hit": True,
            "auto_crit": True,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 153}]
    ))
    current_event_id += 1

    # --- Emit hp_changed ---
    hp_before = target.get(EF.HP_CURRENT, 0)
    hp_after = hp_before - final_damage

    events.append(Event(
        event_id=current_event_id,
        event_type="hp_changed",
        timestamp=timestamp + 0.1,
        payload={
            "entity_id": intent.target_id,
            "hp_before": hp_before,
            "hp_after": hp_after,
            "delta": -final_damage,
            "source": "coup_de_grace",
        }
    ))
    current_event_id += 1

    # --- Call resolve_hp_transition for dying/defeated/disabled transitions ---
    trans_events, _ = resolve_hp_transition(
        entity_id=intent.target_id,
        old_hp=hp_before,
        new_hp=hp_after,
        source="coup_de_grace",
        world_state=world_state,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.2,
    )
    events.extend(trans_events)
    current_event_id += len(trans_events)

    # --- Fort save (PHB p.153): DC = 10 + damage dealt ---
    # "damage dealt" = damage_total (pre-DR), consistent with PHB phrasing.
    # If target is already dead from hp_changed, save is moot but still emitted
    # (provides full event log).
    fort_dc = 10 + damage_total
    fort_base = target.get(EF.SAVE_FORT, 0)

    # Apply condition modifiers to Fort save (e.g., SHAKEN: −2)
    from aidm.core.conditions import get_condition_modifiers
    target_conditions = target.get(EF.CONDITIONS, {})
    # Aggregate all fort_save_modifier values from active conditions
    fort_condition_mod = sum(
        get_condition_modifiers(world_state, intent.target_id).fort_save_modifier
        for _ in [1]  # call once
    )
    # Re-fetch the aggregate properly
    _cond_mods = get_condition_modifiers(world_state, intent.target_id)
    fort_condition_mod = _cond_mods.fort_save_modifier

    fort_roll = combat_rng.randint(1, 20)
    fort_total = fort_roll + fort_base + fort_condition_mod
    fort_passed = fort_total >= fort_dc

    events.append(Event(
        event_id=current_event_id,
        event_type="cdg_fort_save",
        timestamp=timestamp + 0.3,
        payload={
            "entity_id": intent.target_id,
            "attacker_id": intent.attacker_id,
            "fort_roll": fort_roll,
            "fort_base": fort_base,
            "fort_condition_mod": fort_condition_mod,
            "fort_total": fort_total,
            "dc": fort_dc,
            "damage_total": damage_total,
            "passed": fort_passed,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 153}]
    ))
    current_event_id += 1

    # --- If Fort save fails and target not already defeated → immediate death ---
    # Check whether an entity_defeated event was already emitted by resolve_hp_transition
    already_defeated = any(e.event_type == "entity_defeated" for e in trans_events)

    if not fort_passed and not already_defeated:
        events.append(Event(
            event_id=current_event_id,
            event_type="hp_changed",
            timestamp=timestamp + 0.35,
            payload={
                "entity_id": intent.target_id,
                "hp_before": hp_after,
                "hp_after": -10,
                "delta": -(hp_after - (-10)),
                "source": "coup_de_grace_fort_fail",
            }
        ))
        current_event_id += 1

        events.append(Event(
            event_id=current_event_id,
            event_type="entity_defeated",
            timestamp=timestamp + 0.4,
            payload={
                "entity_id": intent.target_id,
                "hp_final": -10,
                "cause": "coup_de_grace",
                "attacker_id": intent.attacker_id,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 153}]
        ))
        current_event_id += 1

    return events
```

**Implementation note on the Fort save double-call cleanup:** The implementation above calls `get_condition_modifiers()` once and uses the result. The draft shows a vestigial double-call pattern in comments; the actual code should call `get_condition_modifiers(world_state, intent.target_id)` exactly once and store the result in `_cond_mods`, then use `_cond_mods.fort_save_modifier`. The double-call sketch in the spec above is illustrative only — the builder should use a single call.

### 4.5 `apply_cdg_events()` in `aidm/core/attack_resolver.py`

Add directly after `resolve_coup_de_grace()`. This function handles all event types that CDG can emit:

```python
def apply_cdg_events(world_state: WorldState, events: List[Event]) -> WorldState:
    """Apply coup de grâce resolution events to world state.

    Handles: hp_changed, entity_defeated, entity_dying, entity_disabled,
    entity_revived, condition_applied, condition_removed.

    Mirrors apply_attack_events() in structure.

    WO-ENGINE-COUP-DE-GRACE-001
    """
    from copy import deepcopy
    entities = deepcopy(world_state.entities)

    for event in events:
        if event.event_type == "hp_changed":
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

        elif event.event_type == "entity_revived":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.DYING] = False
                entities[entity_id][EF.DISABLED] = False
                entities[entity_id][EF.STABLE] = False

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None
    )
```

---

## §5 Event Types

| Event type | Emitter | Payload fields | Notes |
|------------|---------|---------------|-------|
| `cdg_damage_roll` | `resolve_coup_de_grace()` | `attacker_id`, `target_id`, `damage_dice`, `damage_rolls`, `damage_bonus`, `str_modifier`, `grip`, `str_to_damage`, `base_damage`, `crit_multiplier`, `damage_total`, `dr_amount`, `damage_reduced`, `final_damage`, `damage_type`, `auto_hit: True`, `auto_crit: True` | No attack_roll event emitted (auto-hit) |
| `hp_changed` | `resolve_coup_de_grace()` | `entity_id`, `hp_before`, `hp_after`, `delta`, `source: "coup_de_grace"` | Emitted once for CDG damage; emitted a second time (source: `"coup_de_grace_fort_fail"`) if Fort save fails and target not already defeated |
| `cdg_fort_save` | `resolve_coup_de_grace()` | `entity_id`, `attacker_id`, `fort_roll`, `fort_base`, `fort_condition_mod`, `fort_total`, `dc`, `damage_total`, `passed` | Always emitted, regardless of outcome |
| `entity_defeated` | `resolve_coup_de_grace()` or `resolve_hp_transition()` | `entity_id`, `hp_final`, `cause: "coup_de_grace"`, `attacker_id` | Emitted by CDG function only when Fort save fails and `resolve_hp_transition` did not already defeat the target |
| `entity_dying` | `resolve_hp_transition()` (delegated) | standard dying payload | Emitted if CDG damage drops target into −1 to −9 band and target was not already dying |
| `intent_validation_failed` | `execute_turn()` | `actor_id`, `target_id`, `reason: "target_not_helpless"` or `"target_crit_immune"`, `turn_index` | Fail-closed validation before resolver call |
| `ACTION_DENIED` | `execute_turn()` via action economy | `entity_id`, `reason: "action_economy"`, `slot: "full_round"`, `denied_intent_type: "CoupDeGraceIntent"`, `turn_index` | Emitted if attacker already used standard or move action this turn |

**No new event types.** `cdg_damage_roll` and `cdg_fort_save` are new event type strings, but they follow the existing `payload: dict` contract — no schema changes required.

---

## §6 Regression Risk

| Risk | Affected modules | Mitigation |
|------|-----------------|------------|
| `isinstance` checks in `execute_turn()` widen to include `CoupDeGraceIntent` | `play_loop.py` lines 1216, 1292 | Both checks are additive (OR); existing AttackIntent/FullAttackIntent paths unchanged |
| `_build_action_types()` gains one new `_try_add` call | `action_economy.py` | `_try_add` is fail-safe; import failure skips silently |
| `apply_cdg_events()` shares `hp_changed`/`entity_defeated` event handling logic with `apply_attack_events()` | `attack_resolver.py` | Identical logic, new function — no shared mutable state |
| CDG routing block calls `_check_concentration_break()` | `play_loop.py` | Same pattern as AttackIntent block (lines 1574–1589); no new code path |
| `EF.CRIT_IMMUNE` constant added to `entity_fields.py` | All modules that do `entity.get(EF.CRIT_IMMUNE, ...)` | New constant; existing code ignores fields it doesn't read; no breakage |
| Fort save uses `get_condition_modifiers()` from `aidm.core.conditions` | `attack_resolver.py` | Already imported in `resolve_attack()` via local import; CDG function uses same pattern |
| Gold-master JSONL files | `tests/fixtures/gold_masters/` | CDG is a new intent type; existing gold masters contain no `CoupDeGraceIntent` entries; no replay impact |

**Zero changes to:**
- `dying_resolver.py` (called but not modified)
- `full_attack_resolver.py`
- `maneuver_resolver.py`
- `spell_resolver.py`
- `aoo.py`
- Any schema other than `entity_fields.py` and `intents.py`

---

## §7 Gate Spec

**Test file:** `tests/test_engine_gate_cdg.py`

**Fixture pattern:** Use deterministic `RNGProvider` seeded sequences. Construct minimal `WorldState` entities with the fields required for each test. Pass `CoupDeGraceIntent` directly to `execute_turn()`.

| # | Test ID | Setup | Call | Assert |
|---|---------|-------|------|--------|
| CDG-01 | CDG against DYING target — auto-hit, crit damage | Target entity: `EF.DYING=True`, `EF.HP_CURRENT=−3`. Attacker has `EF.STR_MOD=2`. Weapon: `damage_dice="1d6"`, `damage_bonus=0`, `crit_multiplier=2`, `grip="one-handed"`. RNG seeded to roll 4 on damage die and 15 on Fort save (passes). | `execute_turn(CoupDeGraceIntent(...))` | No `attack_roll` event in events list. `cdg_damage_roll` event present with `auto_hit=True`, `auto_crit=True`. `damage_total == (4 + 0 + 2) * 2 == 12`. `hp_changed` delta == −final_damage. |
| CDG-02 | CDG against HELPLESS target — auto-hit, crit damage | Target entity: `EF.CONDITIONS={"helpless": {...}}`, `EF.DYING=False`, `EF.HP_CURRENT=5`. Same weapon/attacker as CDG-01. RNG seeded to roll 3 on damage, 18 on Fort (passes). | `execute_turn(CoupDeGraceIntent(...))` | No `attack_roll` event. `cdg_damage_roll` present. `damage_total == (3 + 0 + 2) * 2 == 10`. `cdg_fort_save` event present with `passed=True`. No `entity_defeated` event. |
| CDG-03 | CDG against DISABLED target — validation failure | Target entity: `EF.DISABLED=True`, `EF.DYING=False`, `EF.HP_CURRENT=0`, no helpless/unconscious/pinned/paralyzed in `EF.CONDITIONS`. | `execute_turn(CoupDeGraceIntent(...))` | `intent_validation_failed` event with `reason="target_not_helpless"`. Status == `"invalid_intent"`. No `cdg_damage_roll` event. |
| CDG-04 | CDG against conscious target — validation failure | Target entity: `EF.HP_CURRENT=15`, `EF.DYING=False`, `EF.CONDITIONS={}`. | `execute_turn(CoupDeGraceIntent(...))` | `intent_validation_failed` event with `reason="target_not_helpless"`. Status == `"invalid_intent"`. |
| CDG-05 | Fort save fails — entity_defeated with cause "coup_de_grace" | Target: `EF.DYING=True`, `EF.HP_CURRENT=−2`, `EF.SAVE_FORT=0`. Weapon: `damage_dice="1d6"`, `crit_multiplier=2`. RNG seeded: damage roll=5 → `damage_total=(5+0+0)*2=10`, Fort DC=10+10=20. Fort roll seeded=1 → total=1 < 20 (fails). | `execute_turn(CoupDeGraceIntent(...))` | `entity_defeated` event with `cause="coup_de_grace"` present. Entity HP in final world_state == −10. `EF.DEFEATED=True`. |
| CDG-06 | Fort save passes — target survives, no entity_defeated | Target: `EF.DYING=True`, `EF.HP_CURRENT=−1`, `EF.SAVE_FORT=10`. Weapon: `damage_dice="1d4"`, `crit_multiplier=2`. RNG: damage roll=1 → `damage_total=(1+0+0)*2=2`, Fort DC=12. Fort roll seeded=10 → total=20 >= 12 (passes). | `execute_turn(CoupDeGraceIntent(...))` | No `entity_defeated` event. `cdg_fort_save` event with `passed=True`. Target still exists in world_state, `EF.DEFEATED=False`. |
| CDG-07 | `cdg_fort_save` event always emitted | Any valid CDG (DYING or HELPLESS target). | `execute_turn(CoupDeGraceIntent(...))` | Exactly one `cdg_fort_save` event in events list. Event payload contains `fort_roll`, `dc`, `passed` keys. |
| CDG-08 | CDG uses full_round action — ACTION_DENIED if already acted | Target: `EF.DYING=True`. `active_combat["action_budget"]` has `standard_used=True` (actor already used standard action this turn). | `execute_turn(CoupDeGraceIntent(...))` | `ACTION_DENIED` event with `slot="full_round"`, `denied_intent_type="CoupDeGraceIntent"`. Status == `"action_denied"`. No `cdg_damage_roll` event. |
| CDG-09 | ×3 crit weapon deals ×3 damage | Attacker `EF.STR_MOD=0`. Weapon: `damage_dice="1d8"`, `damage_bonus=2`, `crit_multiplier=3`, `grip="one-handed"`. Target: `EF.DYING=True`. RNG: damage roll=4. Expected: `base_damage=(4+2+0)=6`, `damage_total=6*3=18`. Fort seeded to pass. | `execute_turn(CoupDeGraceIntent(...))` | `cdg_damage_roll` event with `crit_multiplier=3`, `damage_total=18`. `hp_changed` delta == −final_damage (18 if no DR). |
| CDG-10 | CDG against PINNED target — valid target (PINNED is helpless) | Target entity: `EF.CONDITIONS={"pinned": {...}}`, `EF.DYING=False`, `EF.HP_CURRENT=8`. | `execute_turn(CoupDeGraceIntent(...))` | No `intent_validation_failed` event. `cdg_damage_roll` event present. `auto_hit=True`. |

---

## §8 What This WO Does NOT Do

- Does not implement CDG for ranged weapons beyond accepting `"ranged"` as `damage_type` in the weapon dict — adjacency enforcement (PHB p.153: "adjacent to target" for bow/crossbow) is deferred until a position-enforcement WO.
- Does not apply sneak attack damage to CDG strikes. PHB p.153 and p.50 are silent on whether sneak attack stacks with CDG; this is deferred. The `resolve_coup_de_grace()` function intentionally does not call `calculate_sneak_attack()`.
- Does not track or enforce coup de grâce attempt limits or cooldowns (no such limit exists in PHB 3.5e; nothing to implement).
- Does not add CDG to the narrator/STP generation system. The narration token `"coup_de_grace_delivered"` is emitted in `play_loop.py` but STP wiring is out of scope.
- Does not touch `dying_resolver.py` — it is called as a dependency, not modified.
- Does not implement the "not subject to extra damage from critical hits" carve-out (e.g., swarms) beyond the `EF.CRIT_IMMUNE` boolean. Creature-type-based crit immunity (undead, constructs, elementals, oozes, plants) is data-only and deferred to a creature-type tag system.
- Does not add CDG support to the tactical policy engine. Monster AI issuing CDG intents is out of scope.

---

## §9 Preflight

```bash
# 1. Verify EF constants exist before starting
python -c "
from aidm.schemas.entity_fields import EF
assert hasattr(EF, 'DYING'), 'EF.DYING missing'
assert hasattr(EF, 'STABLE'), 'EF.STABLE missing'
assert hasattr(EF, 'DISABLED'), 'EF.DISABLED missing'
assert hasattr(EF, 'DEFEATED'), 'EF.DEFEATED missing'
assert hasattr(EF, 'SAVE_FORT'), 'EF.SAVE_FORT missing'
assert hasattr(EF, 'STR_MOD'), 'EF.STR_MOD missing'
assert hasattr(EF, 'CONDITIONS'), 'EF.CONDITIONS missing'
assert hasattr(EF, 'HP_CURRENT'), 'EF.HP_CURRENT missing'
print('EF constants OK')
"

# 2. Verify ConditionType has HELPLESS, UNCONSCIOUS, PINNED, PARALYZED
python -c "
from aidm.schemas.conditions import ConditionType
assert ConditionType.HELPLESS.value == 'helpless'
assert ConditionType.UNCONSCIOUS.value == 'unconscious'
assert ConditionType.PINNED.value == 'pinned'
assert ConditionType.PARALYZED.value == 'paralyzed'
print('ConditionType helpless-family OK')
"

# 3. Verify dying_resolver is importable and has resolve_hp_transition
python -c "
from aidm.core.dying_resolver import resolve_hp_transition
print('dying_resolver.resolve_hp_transition importable')
"

# 4. Verify action_economy._try_add mechanism is intact
python -c "
from aidm.core.action_economy import get_action_type, ActionBudget
b = ActionBudget.fresh()
assert b.can_use('full_round')
b.consume('full_round')
assert not b.can_use('full_round')
assert not b.can_use('standard')
assert not b.can_use('move')
print('ActionBudget full_round logic OK')
"

# 5. Verify get_condition_modifiers is importable
python -c "
from aidm.core.conditions import get_condition_modifiers
print('get_condition_modifiers importable')
"

# 6. Verify damage_reduction is importable
python -c "
from aidm.core.damage_reduction import get_applicable_dr, apply_dr_to_damage
print('damage_reduction importable')
"

# 7. Verify resolve_aoo_sequence is importable (CDG provokes AoO)
python -c "
from aidm.core.aoo import resolve_aoo_sequence, check_aoo_triggers
print('aoo importable')
"

# 8. Run existing attack resolver tests to confirm baseline is green before changes
python -m pytest tests/ -k "attack" -x -q 2>&1 | tail -5

# 9. After implementation — run gate
python -m pytest tests/test_engine_gate_cdg.py -v
```
