# WO-ENGINE-NATURAL-ATTACK-001 — Natural Attack Resolution

**Issued:** 2026-02-24
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** HIGH (MEDIUM finding; blocks all Druid Wild Shape playtesting)
**WO type:** BUG (gap — path absent)
**Gate:** ENGINE-NATURAL-ATTACK (10 tests)

---

## 1. Target Lock

Druid Wild Shape sets `EF.NATURAL_ATTACKS` (list of attack dicts) on the actor entity but **no code path exists to resolve those attacks**. A Druid in Wolf, Bear, Eagle, or any other form cannot attack at all. This WO closes that gap.

**Root cause (confirmed by PM inspection):**
- `wild_shape_resolver.py:198` writes `actor[EF.NATURAL_ATTACKS] = list(form_data["attacks"])`
- `attack_resolver.py:219` guards `AttackIntent` with `if EF.EQUIPMENT_MELDED` → blocks all weapon attacks for transformed Druids ✓ (correct)
- **No `NaturalAttackIntent` exists in `intents.py`**
- **No `resolve_natural_attack` function exists in `attack_resolver.py`**
- **No routing branch in `play_loop.py` execute_turn for natural attacks**

**Natural attack dict format (from `WILD_SHAPE_FORMS`):**
```python
{"name": "bite", "damage": "1d6", "damage_type": "piercing"}
{"name": "claw", "damage": "1d4", "damage_type": "slashing"}
{"name": "talon", "damage": "1d4", "damage_type": "slashing"}
```

**`Weapon` dataclass** already accepts `weapon_type="natural"` (attack.py line 88). Use it.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | New intent type or reuse `AttackIntent`? | **New `NaturalAttackIntent`**. Must be distinguishable from `AttackIntent` so the `EQUIPMENT_MELDED` guard doesn't fire and the routing branch is unambiguous. |
| 2 | Full attack or single attack? | **Full attack = all natural weapons**. PHB p.273: a creature with multiple natural attacks makes all of them in a full-attack action. Each dict entry in `EF.NATURAL_ATTACKS` is one attack. |
| 3 | Primary vs secondary attack distinction? | **Deferred**. All natural attacks are treated as primary for now (no -5 secondary penalty). Flag as `FINDING-NATURAL-SECONDARY-001 LOW` if you encounter it. |
| 4 | Attack bonus calculation? | Use `entity[EF.BAB] + entity[EF.STR_MOD]`. No iterative penalty for natural attacks unless form has them (none in current forms). |
| 5 | Damage bonus (STR)? | Apply STR mod to each natural attack. grip="one-handed" → 1× STR. |
| 6 | Crit multiplier? | Default ×2, crit range 20 (none of the current forms have keen or expanded threat range). |
| 7 | Block on `EQUIPMENT_MELDED`? | **No — natural attacks are NOT blocked by EQUIPMENT_MELDED**. The melded guard is for weapon attacks. Natural attacks bypass it. |
| 8 | Where does the resolver live? | **New function `resolve_natural_attack` in `aidm/core/attack_resolver.py`** alongside the existing `resolve_attack`. Keeps all attack resolution in one file. |
| 9 | Event types? | Reuse existing event types: `attack_roll`, `damage_roll`, `hp_changed`, `entity_defeated`. Same schema as `resolve_attack`. |
| 10 | Does play_loop need to handle multiple attacks? | **Yes.** The NaturalAttackIntent carries a `target_id`; resolver loops over all natural attacks in `EF.NATURAL_ATTACKS` and resolves each. |

---

## 3. Contract Spec

### New: `NaturalAttackIntent` in `aidm/schemas/intents.py`

```python
@dataclass
class NaturalAttackIntent:
    """Intent to use natural attacks while in Wild Shape (or as a natural creature).

    PHB p.273: A creature with multiple natural attacks may use all of them
    in a full-attack action. Each attack in EF.NATURAL_ATTACKS is resolved
    independently.

    WO-ENGINE-NATURAL-ATTACK-001
    """

    actor_id: str
    """Entity performing the natural attacks (must have EF.NATURAL_ATTACKS set)."""

    target_id: str
    """Entity being attacked."""

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "natural_attack", "actor_id": self.actor_id, "target_id": self.target_id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NaturalAttackIntent":
        if data.get("type") != "natural_attack":
            raise IntentParseError(f"Expected type 'natural_attack', got '{data.get('type')}'")
        return cls(actor_id=data["actor_id"], target_id=data["target_id"])
```

Add to `Intent` union type and `parse_intent()` dispatch.

### New: `resolve_natural_attack` in `aidm/core/attack_resolver.py`

Signature:
```python
def resolve_natural_attack(
    intent: NaturalAttackIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
```

Logic (pseudocode):
```
1. Read actor = world_state.entities[intent.actor_id]
2. natural_attacks = actor.get(EF.NATURAL_ATTACKS, [])
3. If natural_attacks is empty:
   → emit intent_validation_failed (reason="no_natural_attacks")
   → return events
4. Read target — validate exists, not defeated (same as resolve_attack)
5. For each nat_atk in natural_attacks:
   a. Build Weapon(
        damage_dice=nat_atk["damage"],
        damage_bonus=0,              # base; STR added by resolver
        damage_type=nat_atk["damage_type"],
        weapon_type="natural",
        grip="one-handed",           # STR mod × 1.0
        critical_multiplier=2,
        critical_range=20,
      )
   b. Build synthetic AttackIntent(
        attacker_id=intent.actor_id,
        target_id=intent.target_id,
        attack_bonus=actor[EF.BAB] + actor[EF.STR_MOD],
        weapon=weapon,
      )
   c. Call resolve_attack(synthetic_intent, world_state, rng, current_event_id, timestamp)
      → extend events, advance current_event_id
      → apply_attack_events to update world_state between iterations
      → if target defeated after any attack, stop iterating
6. Return events
```

**IMPORTANT:** The `resolve_attack` call inside the loop must not re-check `EQUIPMENT_MELDED` for natural attacks. Since the builder is constructing a synthetic `AttackIntent`, the guard at `attack_resolver.py:219` will fire if `EQUIPMENT_MELDED` is True. Two options:
- **Option A (recommended):** Pass a `skip_melded_check=True` kwarg to `resolve_attack`.
- **Option B:** Extract the attack roll / damage roll logic into a private `_resolve_single_attack()` function and call it directly from both `resolve_attack` and `resolve_natural_attack`.

Use **Option B** — it avoids adding a kwarg footgun and makes both paths clean. The private function signature:
```python
def _resolve_single_attack(
    attacker_id: str,
    target_id: str,
    attack_bonus: int,
    weapon: Weapon,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float,
    power_attack_penalty: int = 0,
) -> List[Event]:
```

`resolve_attack` and `resolve_natural_attack` both call `_resolve_single_attack`.

### `apply_natural_attack_events` in `aidm/core/attack_resolver.py`

Same pattern as `apply_attack_events`. Can be an alias if the schema is identical.

### Play loop routing in `aidm/core/play_loop.py`

Add elif branch after `EnergyDrainAttackIntent` block (line ~1936):

```python
elif isinstance(combat_intent, NaturalAttackIntent):
    # WO-ENGINE-NATURAL-ATTACK-001: Natural attack resolution (Wild Shape)
    from aidm.core.attack_resolver import resolve_natural_attack, apply_natural_attack_events
    nat_events = resolve_natural_attack(
        intent=combat_intent,
        world_state=world_state,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.1,
    )
    events.extend(nat_events)
    current_event_id += len(nat_events)
    world_state = apply_natural_attack_events(world_state, nat_events)

    # Concentration break check (same pattern as AttackIntent)
    hp_events = [e for e in nat_events if e.event_type == "hp_changed"]
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

    narration = "natural_attack_complete"
```

Also add `NaturalAttackIntent` to:
- The actor_id extraction block (lines 1462-1466) — add to tuple
- The target validation block (lines 1510-1542) — add to isinstance check alongside `AttackIntent`

---

## 4. Implementation Plan

### Step 1 — `aidm/schemas/intents.py`
1. Add `NaturalAttackIntent` dataclass (contract spec above)
2. Add to `Intent` union type
3. Add `"natural_attack"` branch to `parse_intent()`

### Step 2 — `aidm/core/attack_resolver.py`
1. Import `NaturalAttackIntent` from intents
2. Extract `_resolve_single_attack()` private function from existing `resolve_attack` body (the attack roll + damage roll + hp_changed + entity_defeated logic)
3. Refactor `resolve_attack` to call `_resolve_single_attack` (all existing tests must still pass — no behavior change)
4. Add `resolve_natural_attack` (spec above)
5. Add `apply_natural_attack_events` (alias or copy of `apply_attack_events`)

### Step 3 — `aidm/core/play_loop.py`
1. Import `NaturalAttackIntent` at top
2. Add to actor_id extraction block
3. Add to target validation block
4. Add elif routing branch (spec above)

### Step 4 — Tests (`tests/test_engine_natural_attack_gate.py`)
Gate: ENGINE-NATURAL-ATTACK — 10 tests

| Test | Description |
|------|-------------|
| NA-01 | Wolf form (1 attack) — hit lands, HP reduced correctly |
| NA-02 | Wolf form — miss (attack roll below AC) |
| NA-03 | Black bear form (2 attacks: claw + bite) — both resolved, independent rolls |
| NA-04 | Natural attack blocked when `EF.NATURAL_ATTACKS` is empty — `intent_validation_failed` |
| NA-05 | Target validation — target not in world state → `intent_validation_failed` |
| NA-06 | Target validation — target defeated → `intent_validation_failed` |
| NA-07 | Eagle form (talon, small) — damage applies STR mod correctly |
| NA-08 | Critical hit on natural attack — damage multiplied ×2 |
| NA-09 | Second attack stops when target defeated by first (no ghost attacks) |
| NA-10 | `AttackIntent` on `EQUIPMENT_MELDED` entity still blocked (regression: no break from refactor) |

---

## Integration Seams

**Files touched:**
- `aidm/schemas/intents.py` — new `NaturalAttackIntent`, union update, parse dispatch
- `aidm/core/attack_resolver.py` — `_resolve_single_attack` extraction, `resolve_natural_attack`, `apply_natural_attack_events`
- `aidm/core/play_loop.py` — import, actor-id block, target-validation block, elif routing

**Event constructor signature (mandatory):**
```python
Event(
    event_id=<int>,
    event_type=<str>,
    payload=<dict>,
    timestamp=<float>,        # optional
    citations=[],             # optional
)
```
NOT `id=`, `type=`, `data=`.

**Entity field pattern (mandatory):**
```python
entity.get(EF.CLASS_LEVELS, {}).get("druid", 0)   # class level check
entity.get(EF.NATURAL_ATTACKS, [])                  # natural attacks
```
`EF.CLASS_FEATURES` does **not** exist. Do not use it.

**Bonus injection: N/A.** Natural attacks use direct BAB+STR calculation, not TEMPORARY_MODIFIERS.

**EQUIPMENT_MELDED guard:** Located at `attack_resolver.py:219`. The refactor to `_resolve_single_attack` must **not** move this guard into `_resolve_single_attack` — it stays in `resolve_attack` only, so natural attack calls bypass it cleanly.

---

## Assumptions to Validate

1. `_resolve_single_attack` extraction does not require changes to the RNG stream key — use `"combat"` throughout
2. `apply_attack_events` and `apply_natural_attack_events` can share logic — confirm by reading `apply_attack_events` body before refactor
3. No existing test calls `resolve_attack` in a way that would break if its internals are extracted to `_resolve_single_attack`
4. `EF.BAB` exists on Druid entities in Wild Shape (confirmed by WO-ENGINE-WILD-SHAPE-001 gate tests — check `test_engine_gate_cp24.py` or `test_engine_maneuver_gate.py` fixture to verify BAB field)

---

## Preflight

Before starting:
```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_cp24.py tests/test_engine_gate_barbarian_rage.py -x -q
```
Confirm green on existing wild shape and combat tests before touching any file.

After implementation:
```bash
python -m pytest tests/test_engine_natural_attack_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```
Gate passes at 10/10. No regressions.

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/schemas/intents.py` — `NaturalAttackIntent` added
- [ ] `aidm/core/attack_resolver.py` — `_resolve_single_attack`, `resolve_natural_attack`, `apply_natural_attack_events`
- [ ] `aidm/core/play_loop.py` — routing branch wired
- [ ] `tests/test_engine_natural_attack_gate.py` — 10/10

**Gate:** ENGINE-NATURAL-ATTACK 10/10
**Regression bar:** No new failures. Existing suite ~7,602 passing.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-NATURAL-ATTACK-001.md` on completion.

**Three-pass format:**

**Pass 1 — Full context dump:**
- Per-file breakdown: every file touched, functions added/modified, line counts
- Key findings: anything discovered during implementation that wasn't in the WO
- Open findings table: any new findings (ID, severity, description)

**Pass 2 — PM summary (≤100 words):**
- Gate result, regression result, any open findings registered

**Pass 3 — Retrospective:**
- Drift caught (places where you almost used the wrong pattern)
- Pattern notes (anything a future WO author should know)
- Recommendations

Missing debrief or missing Pass 3 Radar = REJECT.

---

## Audio Cue

After filing the debrief:
```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
