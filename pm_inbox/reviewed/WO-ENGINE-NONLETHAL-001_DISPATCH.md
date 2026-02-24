# WO-ENGINE-NONLETHAL-001 — Nonlethal Damage

**Issued:** 2026-02-24
**Authority:** PM Slate — Thunder approval
**Gate:** ENGINE-NONLETHAL (new gate, defined below)
**Parallel-safe:** Yes — adds a new `EF.NONLETHAL_DAMAGE` field, a new `NonlethalAttackIntent` dataclass, and a new nonlethal routing branch in `attack_resolver.py`. Does not touch the existing lethal damage path, the full-attack path, `full_attack_resolver.py`, `dying_resolver.py`, `play_loop.py` spell handling, or the DR path from WO-ENGINE-DR-001. One-line addition to `rest_resolver.py` (§4.6) is purely additive. Does not overlap with WO-ENGINE-DEATH-DYING-001, WO-ENGINE-DR-001, or WO-ENGINE-CONCENTRATION-FIX.

---

## §1 Target Lock

### What is broken

PHB 3.5e p.146 defines a nonlethal (subdual) damage pool distinct from HP. A player who wishes to knock out rather than kill an opponent can declare a nonlethal attack. Currently:

- No `NONLETHAL_DAMAGE` field exists on entities.
- No `NonlethalAttackIntent` exists in `aidm/schemas/attack.py` or `aidm/schemas/intents.py`.
- There is no routing for subdual attacks in `attack_resolver.py`.
- The STAGGERED and UNCONSCIOUS `ConditionType` values exist in `aidm/schemas/conditions.py` (lines 43–44) but are never applied by the engine.
- Nonlethal damage is never cleared on rest.

### What "done" means

- `EF.NONLETHAL_DAMAGE` field exists and is initialized to 0 on entities that lack it.
- `NonlethalAttackIntent` is a dataclass in `aidm/schemas/attack.py` alongside `AttackIntent`.
- A nonlethal attack applies a −4 penalty to the attack roll (PHB p.146), then on a hit, routes damage to the nonlethal pool rather than HP.
- After each nonlethal hit, the engine checks whether nonlethal total >= current HP and emits `STAGGERED` or `UNCONSCIOUS` condition events accordingly.
- `nonlethal_damage` event is emitted on every nonlethal hit.
- On overnight rest, `NONLETHAL_DAMAGE` is reset to 0.
- Gate ENGINE-NONLETHAL 10/10 passes.

---

## §2 PHB Rule Reference

**PHB 3.5e p.146 — Nonlethal Damage:**

> Sometimes you get roughed up or weakened, such as by getting punched, overworked, or exhausted. Nonlethal damage does not kill a character. When a character takes nonlethal damage equal to her current hit points, she's staggered. When nonlethal damage exceeds her current hit points, she falls unconscious.
>
> You can use a melee weapon that deals lethal damage to deal nonlethal damage instead, but you take a −4 penalty on your attack roll.

**Threshold table (PHB p.146):**

| Nonlethal vs. Current HP | State |
|--------------------------|-------|
| Nonlethal < current HP | No threshold crossed |
| Nonlethal == current HP | STAGGERED (can take only one move or standard action per turn) |
| Nonlethal > current HP | UNCONSCIOUS |

**Recovery (PHB p.146):**

> A character recovers 1 point of nonlethal damage per level per hour. Thus, a 1st-level character heals 1 nonlethal damage per hour; a 5th-level character heals 5.
>
> **Implementation note:** Per-hour nonlethal healing requires a timer not yet in this engine. This WO implements the simpler rule: overnight rest (8h) clears all nonlethal damage (equivalent to ≥8 × level recovery, which will always exceed any reasonable nonlethal pool). Per-hour recovery is deferred.

**Threshold re-check on HP healing:**

If an entity's lethal HP is restored (via healing), the STAGGERED/UNCONSCIOUS threshold may no longer be met. The engine must re-check the threshold after any HP increase and remove the condition if it no longer applies.

---

## §3 New Entity Fields

Add to `aidm/schemas/entity_fields.py` after line 156 (the `STABLE` constant), in a new section:

```python
# --- Nonlethal Damage (WO-ENGINE-NONLETHAL-001) ---
NONLETHAL_DAMAGE = "nonlethal_damage"  # Int: accumulated nonlethal damage. 0 = none.
```

This is the only new constant. `STAGGERED` and `UNCONSCIOUS` condition types already exist in `aidm/schemas/conditions.py` (`ConditionType.STAGGERED`, `ConditionType.UNCONSCIOUS`).

**Default value:** Entities that lack this field are treated as `NONLETHAL_DAMAGE = 0` via `.get(EF.NONLETHAL_DAMAGE, 0)` everywhere it is read.

---

## §4 Implementation Spec

### 4.1 New `NonlethalAttackIntent` in `aidm/schemas/attack.py`

Add after the existing `AttackIntent` dataclass (after line 135 in `attack.py`):

```python
@dataclass
class NonlethalAttackIntent:
    """Intent to perform a nonlethal (subdual) attack.

    PHB p.146: A melee attack declared as nonlethal incurs a -4 penalty to the
    attack roll. On a hit, damage goes to the nonlethal pool (NONLETHAL_DAMAGE),
    not to HP directly. When nonlethal damage >= current HP, the target is
    staggered or unconscious.

    Only valid with melee bludgeoning or unarmed strike weapons. Using a lethal
    weapon to deal nonlethal damage is permitted with the -4 penalty.
    """

    attacker_id: str
    """Entity performing the nonlethal attack"""

    target_id: str
    """Entity being attacked"""

    attack_bonus: int
    """Total attack bonus BEFORE the -4 nonlethal penalty.
    The resolver applies the -4 penalty internally."""

    weapon: "Weapon"  # noqa: F821
    """Weapon being used. Must be melee (range_increment == 0)."""

    def __post_init__(self):
        if not self.attacker_id:
            raise ValueError("attacker_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.weapon.is_ranged:
            raise ValueError(
                "NonlethalAttackIntent requires a melee weapon (PHB p.146). "
                f"Got ranged weapon with range_increment={self.weapon.range_increment}."
            )
```

### 4.2 New `resolve_nonlethal_attack()` in `attack_resolver.py`

Add a new top-level function in `aidm/core/attack_resolver.py` below `resolve_attack()`. This function follows the same structure as `resolve_attack()` but with nonlethal routing.

**Key differences from `resolve_attack()`:**

1. Attack roll uses `intent.attack_bonus - 4` (PHB p.146 nonlethal penalty).
2. On hit, damage goes to `EF.NONLETHAL_DAMAGE` pool, not HP.
3. After damage, call `check_nonlethal_threshold()` helper (§4.3).
4. Emit `nonlethal_damage` event (§4.4) instead of `hp_changed`.
5. Emit `condition_applied` if threshold crossed.
6. No `hp_changed` event is emitted (HP is not modified).
7. No `entity_dying` / `entity_defeated` / `entity_disabled` events (HP bands unchanged).

**Signature:**

```python
def resolve_nonlethal_attack(
    intent: NonlethalAttackIntent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve a nonlethal attack intent.

    PHB p.146: -4 attack penalty. On hit, damage accumulates in NONLETHAL_DAMAGE
    pool. Threshold crossed → STAGGERED or UNCONSCIOUS condition applied.

    RNG consumption order:
    1. Attack roll (d20)
    2. IF threat: Confirmation roll (d20) [standard crit rules still apply]
    3. IF hit: Damage roll (XdY)

    Does NOT consume miss-chance roll (concealment not implemented for nonlethal
    in this WO — deferred).
    """
```

**Implementation outline:**

```python
NONLETHAL_ATTACK_PENALTY = -4  # PHB p.146

adjusted_attack_bonus = intent.attack_bonus + NONLETHAL_ATTACK_PENALTY

# [standard attack roll / crit check sequence, same as resolve_attack()]
# ... d20, threat, confirmation ...

# On hit:
if hit:
    # Roll damage (same dice/STR logic as resolve_attack())
    # ...
    damage_total = max(1, base_damage_with_modifiers)

    # NOTE: DR does NOT apply to nonlethal damage dealt to the nonlethal pool.
    # PHB p.146 is silent on DR vs nonlethal; this WO treats nonlethal as
    # bypassing DR (nonlethal is a different pool, not physical HP damage).
    # Builder note: if this interpretation is challenged, add a follow-up WO.

    # Update nonlethal pool
    old_nonlethal = target.get(EF.NONLETHAL_DAMAGE, 0)
    new_nonlethal = old_nonlethal + damage_total
    # (Entity state update happens in apply_nonlethal_attack_events())

    # Check threshold
    current_hp = target.get(EF.HP_CURRENT, 0)
    threshold = check_nonlethal_threshold(current_hp, new_nonlethal)

    # Emit nonlethal_damage event
    events.append(Event(
        event_id=current_event_id,
        event_type="nonlethal_damage",
        timestamp=timestamp + 0.1,
        payload={
            "attacker_id": intent.attacker_id,
            "entity_id": intent.target_id,
            "amount": damage_total,
            "old_nonlethal_total": old_nonlethal,
            "new_nonlethal_total": new_nonlethal,
            "current_hp": current_hp,
            "threshold_crossed": threshold,  # "staggered", "unconscious", or None
        },
        citations=[{"source_id": "681f92bc94ff", "page": 146}]
    ))
    current_event_id += 1

    # Emit condition_applied if threshold crossed
    if threshold == "staggered":
        from aidm.schemas.conditions import ConditionType, ConditionInstance, ConditionModifiers
        events.append(Event(
            event_id=current_event_id,
            event_type="condition_applied",
            timestamp=timestamp + 0.2,
            payload={
                "entity_id": intent.target_id,
                "condition": ConditionType.STAGGERED.value,
                "source": "nonlethal_damage",
                "notes": f"Nonlethal {new_nonlethal} == HP {current_hp}",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 146}]
        ))
        current_event_id += 1

    elif threshold == "unconscious":
        from aidm.schemas.conditions import ConditionType
        events.append(Event(
            event_id=current_event_id,
            event_type="condition_applied",
            timestamp=timestamp + 0.2,
            payload={
                "entity_id": intent.target_id,
                "condition": ConditionType.UNCONSCIOUS.value,
                "source": "nonlethal_damage",
                "notes": f"Nonlethal {new_nonlethal} > HP {current_hp}",
            },
            citations=[{"source_id": "681f92bc94ff", "page": 146}]
        ))
        current_event_id += 1

return events
```

### 4.3 New helper `check_nonlethal_threshold()` in `attack_resolver.py`

Pure function, no side effects:

```python
def check_nonlethal_threshold(current_hp: int, nonlethal_total: int) -> str | None:
    """Check whether nonlethal damage has crossed a PHB p.146 threshold.

    Args:
        current_hp: Entity's current lethal HP (EF.HP_CURRENT).
        nonlethal_total: New total nonlethal damage after this hit.

    Returns:
        "staggered" if nonlethal_total == current_hp,
        "unconscious" if nonlethal_total > current_hp,
        None if below threshold.
    """
    if nonlethal_total > current_hp:
        return "unconscious"
    elif nonlethal_total == current_hp:
        return "staggered"
    return None
```

### 4.4 New `apply_nonlethal_attack_events()` in `attack_resolver.py`

Mirrors `apply_attack_events()`. Handles `nonlethal_damage` and `condition_applied` events:

```python
def apply_nonlethal_attack_events(
    world_state: WorldState,
    events: List[Event],
) -> WorldState:
    """Apply nonlethal attack events to world state.

    Handles:
    - nonlethal_damage: updates EF.NONLETHAL_DAMAGE
    - condition_applied: appends to EF.CONDITIONS
    """
    from copy import deepcopy
    entities = deepcopy(world_state.entities)

    for event in events:
        if event.event_type == "nonlethal_damage":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                entities[entity_id][EF.NONLETHAL_DAMAGE] = \
                    event.payload["new_nonlethal_total"]

        elif event.event_type == "condition_applied":
            entity_id = event.payload["entity_id"]
            if entity_id in entities:
                cond_val = event.payload["condition"]
                conds = entities[entity_id].get(EF.CONDITIONS, [])
                if cond_val not in conds:
                    conds = list(conds) + [cond_val]
                entities[entity_id][EF.CONDITIONS] = conds

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=deepcopy(world_state.active_combat) if world_state.active_combat else None,
    )
```

### 4.5 HP healing clears nonlethal conditions

When an entity's HP is restored (via `hp_changed` with positive `delta`, or `hp_restored` from rest), the engine must check whether the healed HP now exceeds the nonlethal pool. If it does, the STAGGERED or UNCONSCIOUS condition from nonlethal damage should be removed.

**Location:** In `apply_attack_events()` in `attack_resolver.py` and in `apply_full_attack_events()` in `full_attack_resolver.py`, after the `hp_changed` handler block, add:

```python
# WO-ENGINE-NONLETHAL-001: Re-check nonlethal threshold after HP gain
# (This fires only if hp_after > hp_before — i.e., a heal, not damage)
if event.event_type == "hp_changed":
    new_hp = event.payload["hp_after"]
    old_hp = event.payload.get("hp_before", new_hp)
    if new_hp > old_hp:  # healing event
        nl_total = entities[entity_id].get(EF.NONLETHAL_DAMAGE, 0)
        if nl_total < new_hp:
            # Threshold no longer met — clear nonlethal conditions
            conds = entities[entity_id].get(EF.CONDITIONS, [])
            entities[entity_id][EF.CONDITIONS] = [
                c for c in conds
                if c not in (
                    ConditionType.STAGGERED.value,
                    ConditionType.UNCONSCIOUS.value,
                )
            ]
```

**Note for builder:** Import `ConditionType` at the top of the handler block (or at module level in `attack_resolver.py`). This addition is inside the existing `for event in events:` loop, branching only on `hp_after > hp_before`.

### 4.6 Clear `NONLETHAL_DAMAGE` on overnight rest in `rest_resolver.py`

**File:** `aidm/core/rest_resolver.py`

In the `resolve_rest()` function, inside the `if is_full_rest:` block (after the HP recovery block, approximately line 107), add:

```python
# WO-ENGINE-NONLETHAL-001: Overnight rest clears all nonlethal damage (PHB p.146)
if is_full_rest and actor.get(EF.NONLETHAL_DAMAGE, 0) > 0:
    actor[EF.NONLETHAL_DAMAGE] = 0
    # Also clear staggered/unconscious conditions caused by nonlethal
    conds = actor.get(EF.CONDITIONS, [])
    actor[EF.CONDITIONS] = [
        c for c in conds
        if c not in ("staggered", "unconscious")
    ]
```

This is a one-line conceptual addition (three implementation lines). It does not change the function signature, return type, or any existing event structure.

### 4.7 Wire `NonlethalAttackIntent` in `play_loop.py`

In `play_loop.py`, in the `execute_turn()` intent routing block where `AttackIntent` is handled, add a parallel branch:

```python
elif isinstance(combat_intent, NonlethalAttackIntent):
    from aidm.core.attack_resolver import resolve_nonlethal_attack, apply_nonlethal_attack_events
    nl_events = resolve_nonlethal_attack(
        intent=combat_intent,
        world_state=world_state,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=timestamp,
    )
    events.extend(nl_events)
    world_state = apply_nonlethal_attack_events(world_state, nl_events)
    current_event_id += len(nl_events)
```

---

## §5 Event Types

| Event type | Emitted when | New? |
|------------|-------------|------|
| `nonlethal_damage` | Nonlethal attack hits; damage added to nonlethal pool | YES |
| `condition_applied` | Nonlethal threshold crossed (STAGGERED or UNCONSCIOUS) | Existing event type; nonlethal is a new source |

### `nonlethal_damage` payload

```json
{
  "event_type": "nonlethal_damage",
  "payload": {
    "attacker_id": "player_rogue",
    "entity_id": "bandit_01",
    "amount": 6,
    "old_nonlethal_total": 0,
    "new_nonlethal_total": 6,
    "current_hp": 8,
    "threshold_crossed": null
  }
}
```

When threshold crossed:

```json
{
  "event_type": "nonlethal_damage",
  "payload": {
    "attacker_id": "player_rogue",
    "entity_id": "bandit_01",
    "amount": 4,
    "old_nonlethal_total": 4,
    "new_nonlethal_total": 8,
    "current_hp": 8,
    "threshold_crossed": "staggered"
  }
}
```

### `attack_roll` payload for nonlethal attacks

The `attack_roll` event emitted by `resolve_nonlethal_attack()` must include:

```json
{
  "nonlethal": true,
  "nonlethal_penalty": -4,
  "adjusted_attack_bonus": 3
}
```

This lets the narrator and UI surface the penalty clearly.

---

## §6 Regression Risk

**Minimal.** The changes are entirely additive:

1. New EF constant `NONLETHAL_DAMAGE` — additive, no existing code reads it.
2. New `NonlethalAttackIntent` dataclass — additive, no existing code routes it.
3. New `resolve_nonlethal_attack()` function — additive, not called by any existing path until `play_loop.py` is wired (§4.7).
4. New `apply_nonlethal_attack_events()` function — additive.
5. The HP healing nonlethal-condition clear in `apply_attack_events()` (§4.5) is the only change to an existing function. It only fires when `hp_after > hp_before` (a heal), which is currently a code path that existing tests do not heavily exercise during combat. Verify that no existing test in the CP-22 or CP-23 suite has a healing event inside combat that would now trigger this branch unexpectedly.
6. The one-line addition to `rest_resolver.py` (§4.6) only fires if `EF.NONLETHAL_DAMAGE > 0`, which is 0 on all existing test fixtures. Zero regression risk.

**Gold master impact:** None expected. No existing gold master scenario uses `NonlethalAttackIntent`, so no `.jsonl` files will change.

---

## §7 Gate Spec

**Gate name:** `ENGINE-NONLETHAL`
**Test file:** `tests/test_engine_nonlethal_gate.py`

| # | Test ID | Description | Assert |
|---|---------|-------------|--------|
| 1 | NL-01 | `NonlethalAttackIntent` with `attack_bonus=7` → `attack_roll` event shows adjusted bonus of `+3` and `nonlethal_penalty: -4` in payload | `event.payload["adjusted_attack_bonus"] == 3` and `event.payload["nonlethal_penalty"] == -4` |
| 2 | NL-02 | Nonlethal attack hits → `nonlethal_damage` event emitted; target `EF.HP_CURRENT` unchanged; `EF.NONLETHAL_DAMAGE` incremented by damage amount | `hp_current == original`, `nonlethal_damage == amount` |
| 3 | NL-03 | Nonlethal total 4, current HP 8 → no STAGGERED or UNCONSCIOUS condition; `threshold_crossed == null` | `conditions` list unchanged |
| 4 | NL-04 | Nonlethal total accumulates to exactly equal current HP (e.g., 8 nl == 8 HP) → `condition_applied` with `condition: "staggered"`; `threshold_crossed == "staggered"` | `condition_applied` event present, `condition == "staggered"` |
| 5 | NL-05 | Nonlethal total exceeds current HP (e.g., 10 nl > 8 HP) → `condition_applied` with `condition: "unconscious"`; `threshold_crossed == "unconscious"` | `condition_applied` event present, `condition == "unconscious"` |
| 6 | NL-06 | Successful nonlethal hit → `nonlethal_damage` event has all required payload fields: `attacker_id`, `entity_id`, `amount`, `old_nonlethal_total`, `new_nonlethal_total`, `current_hp`, `threshold_crossed` | All 7 payload keys present and correct |
| 7 | NL-07 | Entity with `NONLETHAL_DAMAGE = 6` takes overnight rest → after `resolve_rest()`, `actor[EF.NONLETHAL_DAMAGE] == 0` and STAGGERED condition cleared | `nonlethal_damage == 0`, `"staggered" not in conditions` |
| 8 | NL-08 | Entity with `HP=8`, `NONLETHAL_DAMAGE=8` (staggered) receives healing to HP=12 → STAGGERED condition removed (nl 8 < hp 12) | `"staggered" not in conditions` post-heal |
| 9 | NL-09 | Entity with no `NONLETHAL_DAMAGE` field → treated as 0; nonlethal hit of 3 → `old_nonlethal_total == 0`, `new_nonlethal_total == 3` | No KeyError; `old == 0` |
| 10 | NL-10 | Attack roll of natural 1 on nonlethal attack → miss; `nonlethal_damage` event NOT emitted; `attack_roll` event shows `nonlethal_penalty: -4` and `hit: false` | 0 `nonlethal_damage` events; `attack_roll.hit == false` |

**Test count target:** 10 checks → Gate `ENGINE-NONLETHAL` 10/10.

---

## §8 What This WO Does NOT Do

- Does not implement nonlethal damage in full-attack sequences (`FullAttackIntent`) — deferred. Full nonlethal attacks (e.g., a monk's full attack subdual) require a `NonlethalFullAttackIntent`. The pattern is identical to this WO but applied to `full_attack_resolver.py`.
- Does not implement per-hour nonlethal recovery (requires a timer system — deferred). Overnight rest clears all nonlethal damage as an approximation.
- Does not implement the Heal skill stabilizing a nonlethal-unconscious creature.
- Does not implement coup de grace on a nonlethal-unconscious target (deferred to a future combat maneuver WO).
- Does not enforce that only melee weapons can deal nonlethal damage in the attack roll itself — the `__post_init__` guard on `NonlethalAttackIntent` rejects ranged weapons at intent creation time, which is sufficient for this WO.
- Does not implement Stunning Fist or similar feats that deal nonlethal via special attacks.
- Does not modify `EF.DYING`, `EF.DEFEATED`, or `EF.DISABLED` — a creature knocked unconscious by nonlethal damage is unconscious (`UNCONSCIOUS` condition) but is NOT dying, not dead, not defeated in the lethal sense.
- Does not implement the interaction where a creature already dying from lethal damage cannot be further subdued (an edge case deferred to a follow-up WO).
- Does not touch `full_attack_resolver.py` or `full_attack_resolver`'s `apply_full_attack_events()`.

---

## §9 Preflight

```bash
cd f:/DnD-3.5

# Verify entity_fields.py constant is added:
python -c "from aidm.schemas.entity_fields import EF; print(EF.NONLETHAL_DAMAGE)"
# Expected output: nonlethal_damage

# Verify NonlethalAttackIntent imports cleanly:
python -c "from aidm.schemas.attack import NonlethalAttackIntent; print('OK')"
# Expected output: OK

# Verify resolve_nonlethal_attack imports cleanly:
python -c "from aidm.core.attack_resolver import resolve_nonlethal_attack, check_nonlethal_threshold; print('OK')"
# Expected output: OK

# Run new gate:
python -m pytest tests/test_engine_nonlethal_gate.py -v
# NL-01 through NL-10 must pass.

# Regression sweep — rest gate (verifies §4.6 one-liner does not break rest):
python -m pytest tests/test_engine_rest_gate.py -v --tb=short
# All 12 rest checks must still pass.

# Regression sweep — engine gates:
python -m pytest tests/test_engine_gate_cp17.py tests/test_engine_gate_cp22.py tests/test_engine_gate_cp23.py tests/test_engine_gate_xp01.py -v --tb=short
# Zero new failures expected.

# Full suite:
python -m pytest tests/ -x --tb=short
# Zero new regressions.
```
