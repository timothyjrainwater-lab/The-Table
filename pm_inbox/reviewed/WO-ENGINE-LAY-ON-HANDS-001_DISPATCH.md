# WO-ENGINE-LAY-ON-HANDS-001 — Paladin Lay on Hands: Daily HP Pool + Heal Intent

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** HIGH (FINDING-COVERAGE-MAP-001 rank #13 — paladin has no healing ability beyond spells)
**WO type:** BUG (class feature absent)
**Gate:** ENGINE-LAY-ON-HANDS (10 tests)

---

## 1. Target Lock

**What works:** `smite_evil_resolver.py` is the established pattern for paladin class features — new intent, new resolver, routing in play_loop.py, chargen initialization. `rest_resolver.py` already recovers smite uses per rest. `EF.CHA_MOD` exists. `EF.CLASS_LEVELS` pattern confirmed throughout codebase.

**What's missing:** PHB p.44 — "A paladin can heal wounds (her own or those of others) by touch. Each day she can heal a total number of hit points of damage equal to her paladin level × her Charisma modifier." No `LayOnHandsIntent`, no pool field, no resolver, no routing.

**PHB reference:** PHB p.44 — Lay on Hands: `paladin_level × CHA_mod` HP/day. Standard action. Touch range (target_id = self or adjacent ally). Pool refreshes on full rest. CHA mod minimum 1 (if CHA mod ≤ 0, pool = 0).

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | New EF fields? | `EF.LAY_ON_HANDS_POOL` (int: max HP available today) and `EF.LAY_ON_HANDS_USED` (int: HP consumed today). Pool = `paladin_level × max(1, CHA_mod)`. If CHA_mod ≤ 0, pool = 0 (no benefit). |
| 2 | Amount per use? | PHB: split however desired. Intent carries `amount: int` — the healer declares how many HP to spend this use. Validate: amount ≤ (pool − used), amount ≥ 1. |
| 3 | Can paladin heal self? | Yes — PHB explicit. `actor_id == target_id` is valid. |
| 4 | Action cost? | Standard action — add to `_ACTION_TYPES` mapping in `action_economy.py`. |
| 5 | Does it revive dying characters? | Yes — healing HP brings a dying character back above 0 (dying_resolver handles the transition when HP updates). No special case needed. |
| 6 | Rest recovery? | Full rest restores pool to max. Add to `rest_resolver.py` alongside existing smite/turn undead recovery. |
| 7 | Chargen init? | Set `EF.LAY_ON_HANDS_POOL` and `EF.LAY_ON_HANDS_USED = 0` in `builder.py` for paladin entities. |
| 8 | New resolver file? | `aidm/core/lay_on_hands_resolver.py` — mirror `smite_evil_resolver.py` structure. |

---

## 3. Contract Spec

### New EF constants in `aidm/schemas/entity_fields.py`

```python
LAY_ON_HANDS_POOL = "lay_on_hands_pool"
# int: total HP paladin can heal today via Lay on Hands.
# = paladin_level * max(1, CHA_mod). 0 if CHA_mod <= 0.
# Refreshes on full rest. PHB p.44.

LAY_ON_HANDS_USED = "lay_on_hands_used"
# int: HP already consumed from pool this day. 0 at rest.
```

### New intent in `aidm/schemas/intents.py`

```python
@dataclass(frozen=True)
class LayOnHandsIntent:
    """PHB p.44: Paladin heals target by touch. Standard action."""
    actor_id: str
    target_id: str
    amount: int          # HP to spend from pool this use (1 to pool_remaining)
    action_type: str = "standard"
```

### New file: `aidm/core/lay_on_hands_resolver.py`

```python
def resolve_lay_on_hands(
    intent: LayOnHandsIntent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """PHB p.44: Paladin Lay on Hands healing."""
    events = []
    ws = deepcopy(world_state)
    actor = ws.entities[intent.actor_id]
    target = ws.entities[intent.target_id]

    # Validate: actor is paladin
    paladin_level = actor.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
    if paladin_level == 0:
        events.append(Event(event_id=next_event_id, event_type="lay_on_hands_invalid",
            timestamp=timestamp, payload={"reason": "not_a_paladin", "actor_id": intent.actor_id},
            citations=["PHB p.44"]))
        return events, ws

    # Validate: pool available
    pool = actor.get(EF.LAY_ON_HANDS_POOL, 0)
    used = actor.get(EF.LAY_ON_HANDS_USED, 0)
    remaining = pool - used
    if remaining <= 0:
        events.append(Event(event_id=next_event_id, event_type="lay_on_hands_exhausted",
            timestamp=timestamp, payload={"actor_id": intent.actor_id, "pool": pool, "used": used},
            citations=["PHB p.44"]))
        return events, ws

    # Clamp amount to remaining pool
    amount = min(intent.amount, remaining)

    # Apply healing
    hp_before = target.get(EF.HP_CURRENT, 0)
    hp_max = target.get(EF.HP_MAX, hp_before)
    hp_after = min(hp_before + amount, hp_max)
    actual_healed = hp_after - hp_before

    ws.entities[intent.target_id][EF.HP_CURRENT] = hp_after
    ws.entities[intent.actor_id][EF.LAY_ON_HANDS_USED] = used + amount

    events.append(Event(
        event_id=next_event_id,
        event_type="lay_on_hands_heal",
        timestamp=timestamp + 0.1,
        payload={
            "actor_id": intent.actor_id,
            "target_id": intent.target_id,
            "amount_spent": amount,
            "hp_healed": actual_healed,
            "hp_before": hp_before,
            "hp_after": hp_after,
            "pool_remaining": remaining - amount,
        },
        citations=["PHB p.44"],
    ))
    return events, ws
```

### Modification: `aidm/core/rest_resolver.py`

In the full-rest recovery block, after smite/turn undead recovery, add:

```python
# WO-ENGINE-LAY-ON-HANDS-001: Restore Lay on Hands pool on full rest
paladin_level = entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
if paladin_level > 0:
    cha_mod = entity.get(EF.CHA_MOD, 0)
    pool_max = paladin_level * max(1, cha_mod) if cha_mod > 0 else 0
    entity[EF.LAY_ON_HANDS_POOL] = pool_max
    entity[EF.LAY_ON_HANDS_USED] = 0
```

### Modification: `aidm/chargen/builder.py`

At paladin entity initialization, set pool:

```python
if class_levels.get("paladin", 0) > 0:
    paladin_level = class_levels["paladin"]
    cha_mod = ability_modifiers.get("cha", 0)
    entity[EF.LAY_ON_HANDS_POOL] = paladin_level * max(1, cha_mod) if cha_mod > 0 else 0
    entity[EF.LAY_ON_HANDS_USED] = 0
```

### Modification: `aidm/core/action_economy.py`

```python
LayOnHandsIntent: "standard",
```

### Modification: `aidm/core/play_loop.py`

Add routing elif after SmiteEvilIntent block:

```python
elif isinstance(combat_intent, LayOnHandsIntent):
    from aidm.core.lay_on_hands_resolver import resolve_lay_on_hands
    _loh_events, world_state = resolve_lay_on_hands(
        intent=combat_intent,
        world_state=world_state,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.1,
    )
    events.extend(_loh_events)
    current_event_id += len(_loh_events)
```

---

## 4. Implementation Plan

1. `aidm/schemas/entity_fields.py` — 2 new constants
2. `aidm/schemas/intents.py` — `LayOnHandsIntent` dataclass
3. `aidm/core/lay_on_hands_resolver.py` — new file (~60 lines)
4. `aidm/core/rest_resolver.py` — pool recovery block (~6 lines)
5. `aidm/chargen/builder.py` — pool initialization (~4 lines)
6. `aidm/core/action_economy.py` — 1-line mapping
7. `aidm/core/play_loop.py` — routing elif + import (~8 lines)
8. Tests

### Tests (`tests/test_engine_lay_on_hands_gate.py`)
Gate: ENGINE-LAY-ON-HANDS — 10 tests

| Test | Description |
|------|-------------|
| LOH-01 | Paladin level 5, CHA mod +3: pool = 15 HP |
| LOH-02 | Heal 5 HP from pool: target +5 HP, pool_remaining = 10 |
| LOH-03 | Heal self: actor_id == target_id valid |
| LOH-04 | Heal dying ally: HP goes from −3 to +2, no longer dying |
| LOH-05 | Pool exhausted: `lay_on_hands_exhausted` event, no healing |
| LOH-06 | Amount clamped to remaining: request 10 with 6 remaining → heals 6 |
| LOH-07 | Non-paladin entity: `lay_on_hands_invalid` event |
| LOH-08 | Full rest: pool restored to max, used reset to 0 |
| LOH-09 | CHA mod ≤ 0: pool = 0, exhausted immediately |
| LOH-10 | Regression: ENGINE-SMITE-EVIL 8/8 unchanged |

---

## Integration Seams

**Files touched:**
- `aidm/schemas/entity_fields.py` — 2 constants
- `aidm/schemas/intents.py` — 1 new dataclass
- `aidm/core/lay_on_hands_resolver.py` — new file
- `aidm/core/rest_resolver.py` — ~6 lines
- `aidm/chargen/builder.py` — ~4 lines
- `aidm/core/action_economy.py` — 1 line
- `aidm/core/play_loop.py` — ~8 lines

**Template to follow:** `aidm/core/smite_evil_resolver.py` — identical pattern for paladin class features.

**Event constructor signature (mandatory):**
```python
Event(event_id=<int>, event_type=<str>, payload=<dict>, timestamp=<float>, citations=[])
```

**CLASS_LEVELS pattern (mandatory):**
```python
entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
```

**HP cap:** `min(hp_before + amount, hp_max)` — never overheal above max HP.

---

## Assumptions to Validate

1. `EF.HP_MAX` field exists on entities — confirm from entity_fields.py
2. `smite_evil_resolver.py` routing pattern in play_loop.py — use as exact template for elif placement
3. `rest_resolver.py` full-rest recovery block structure — confirm where to insert paladin pool reset
4. `LayOnHandsIntent` must be added to the intent union type if one exists in intents.py

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_smite_evil.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_lay_on_hands_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/schemas/entity_fields.py` — 2 constants
- [ ] `aidm/schemas/intents.py` — `LayOnHandsIntent`
- [ ] `aidm/core/lay_on_hands_resolver.py` — new resolver
- [ ] `aidm/core/rest_resolver.py` — pool recovery
- [ ] `aidm/chargen/builder.py` — pool init
- [ ] `aidm/core/action_economy.py` — mapping
- [ ] `aidm/core/play_loop.py` — routing
- [ ] `tests/test_engine_lay_on_hands_gate.py` — 10/10

**Gate:** ENGINE-LAY-ON-HANDS 10/10
**Regression bar:** ENGINE-SMITE-EVIL 8/8, ENGINE-REST 12/12 unchanged.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-LAY-ON-HANDS-001.md` on completion.

Three-pass format. Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
