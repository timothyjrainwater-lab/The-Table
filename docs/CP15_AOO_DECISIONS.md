# CP-15 — Attacks of Opportunity (AoO) Kernel

**Status:** ✅ IMPLEMENTED & FROZEN
**Created:** 2026-02-08
**Instruction Packet:** CP-15
**Test Coverage:** 6 integration tests (all passing)

---

## 1. Purpose

CP-15 introduces **Attacks of Opportunity (AoOs)** as AIDM's first explicit interrupt system. This packet implements RAW D&D 3.5e AoO mechanics (PHB p. 137-138) while preserving deterministic replay, explicit event ordering, and stable play-loop boundaries.

CP-15 establishes the architectural precedent for all future interrupt-capable systems (readied actions, counterspells, grapple transitions, conditions with timing effects).

---

## 2. Implementation Scope

### IN SCOPE

✅ **Threatened Squares**:
- 5-ft reach only (all 8 adjacent squares)
- Grid-based adjacency detection
- Fail-closed for missing position data

✅ **Provoking Actions**:
- Movement out of threatened square (via StepMoveIntent)
- Future: Ranged attack while threatened (deferred pending ranged attack system)
- Future: Spellcasting while threatened (deferred pending spell system)

✅ **AoO Eligibility**:
- One AoO per reactor per round
- Usage tracking via `active_combat["aoo_used_this_round"]`
- Reset at `combat_round_started` event

✅ **Deterministic Resolution Ordering**:
- Initiative order (primary sort key)
- Lexicographic actor_id (tie-breaking)
- Synchronous event-driven execution

✅ **Action Abortion**:
- Provoker defeated by AoO → main action aborts
- Explicit `action_aborted` event with defeat reason
- Early return from `execute_turn()` with special narration

✅ **Movement Declaration**:
- Minimal `StepMoveIntent` schema (single-step, adjacent squares only)
- Declarative `from_pos` → `to_pos` (not inferred from state diffs)
- RAW-faithful timing (triggers on declaration, not completion)

### OUT OF SCOPE (Deferred)

❌ **Combat Reflexes feat**: No multiple AoOs per round (CP-17+)
❌ **Reach weapons**: 5-ft reach only (10-ft/15-ft reach deferred to CP-17+)
❌ **5-foot step immunity**: No movement types yet (CP-16+)
❌ **Withdraw action**: No special movement modes (CP-16+)
❌ **Readied actions**: No delay queue or conditional triggers (CP-16+)
❌ **Full movement legality**: No speed accounting, terrain, or diagonal costs (CP-16+)

---

## 3. Canonical Architecture Decisions

All decisions below are **LOCKED** and binding for CP-16+.

### 3.1 Interrupt Model — Synchronous Event-Driven

**Decision:** AoOs resolve synchronously within `execute_turn()` call stack, not as deferred events

**Event Ordering Contract (Mandatory):**
```
1. Provoking action declared and validated
2. AoO triggers identified (check_aoo_triggers)
3. aoo_triggered events emitted (deterministic order)
4. AoO attacks resolved via existing attack pipeline
5. If provoker defeated → action_aborted, early return
6. Otherwise → provoking action resolves normally
```

**Rationale:**
- PHB p. 137: AoOs are "immediate interrupt attacks"
- Synchronous execution prevents event interleaving
- Explicit ordering contract prevents timing bugs
- Single call stack simplifies debugging and replay

**Contract:**
No other events may interleave during AoO sequence. All AoO events emitted as contiguous block before main action events.

---

### 3.2 AoO Trigger Detection — Dedicated Layer

**Decision:** Separate `check_aoo_triggers()` function isolates trigger detection from resolution

**Architecture:**
```python
# aidm/core/aoo.py
def check_aoo_triggers(
    world_state: WorldState,
    actor_id: str,
    intent: Any
) -> List[AooTrigger]:
    """Check if intent triggers any AoOs (pure function)."""
    # Returns sorted list of AooTrigger objects
```

**Rationale:**
- Trigger detection is pure function (no state mutation)
- Separation of concerns (detection vs resolution)
- Reusable for future provoking actions (ranged attack, spellcasting)
- Testable independently of combat resolution

**Contract:**
`check_aoo_triggers()` is stateless and deterministic. Same inputs always produce identical sorted trigger list.

---

### 3.3 Movement Intent — Declared Intent Data

**Decision:** AoO timing based on **declared intent data** (`StepMoveIntent.from_pos` → `to_pos`), not post-resolution position diffs

**Critical RAW Fidelity:**
PHB p. 137: "You provoke an attack of opportunity **when you move out of a threatened square**" — timing is based on declared action, not completed action.

**Schema:**
```python
@dataclass
class StepMoveIntent:
    actor_id: str
    from_pos: GridPosition  # Must be explicitly declared
    to_pos: GridPosition    # Must be adjacent to from_pos
```

**Rationale:**
- Prevents entire class of timing bugs (no state diff inference)
- RAW-faithful (triggers on declaration, not completion)
- Explicit intent makes replay deterministic
- Prepares for multi-step movement (CP-16+)

**Contract:**
AoO triggers MUST be evaluated using `from_pos` from intent, never by comparing `entities[actor_id]["position"]` before/after action.

---

### 3.4 Movement Scope — Single-Step Only

**Decision:** CP-15 supports **only single-step movement** (adjacent squares)

**StepMoveIntent Constraints:**
- `to_pos` must be adjacent to `from_pos` (validated in `__post_init__`)
- No speed accounting
- No terrain or diagonal cost
- No "moved through" logic

**Rationale:**
- Minimal scope for AoO detection proof
- Full movement legality deferred to CP-16
- Adjacency constraint prevents multi-step logic leakage

**Contract:**
`StepMoveIntent.__post_init__()` raises `ValueError` if `from_pos` not adjacent to `to_pos`. No validation exceptions.

---

### 3.5 AoO Resolution — Attack Pipeline Reuse

**Decision:** AoO attacks resolved via existing `resolve_attack()` pipeline

**Integration:**
```python
# aidm/core/aoo.py (resolve_aoo_sequence)
aoo_attack = AttackIntent(
    attacker_id=trigger.reactor_id,
    target_id=trigger.provoker_id,
    attack_bonus=reactor.attack_bonus,
    weapon=reactor.weapon
)

attack_events = resolve_attack(
    intent=aoo_attack,
    world_state=world_state,
    rng=rng,
    ...
)
```

**Rationale:**
- Consistency with normal attacks (same RNG discipline, same event structure)
- PHB citations already in attack pipeline
- No duplicate attack logic
- AoO attacks are mechanically identical to standard attacks

**Contract:**
AoO attacks emit identical event structure as normal attacks: `attack_roll` → `damage_applied` → `entity_defeated` (if applicable).

---

### 3.6 AoO Ordering — Initiative + Lexicographic

**Decision:** Deterministic two-tier sorting for multiple AoOs

**Sorting Rules:**
1. Initiative order index (lower = earlier in initiative, acts first)
2. Lexicographic `actor_id` (ascending, tie-breaking)

**Implementation:**
```python
# aidm/core/aoo.py (check_aoo_triggers)
def sort_key(reactor_tuple):
    reactor_id, _ = reactor_tuple
    init_index = initiative_order.index(reactor_id) if reactor_id in initiative_order else 9999
    return (init_index, reactor_id)

sorted_reactors = sorted(potential_reactors, key=sort_key)
```

**Rationale:**
- PHB p. 137: Multiple AoOs resolve in initiative order
- Lexicographic tie-breaking ensures determinism
- Matches CP-14 initiative tie-breaking discipline
- No RNG consumption for AoO ordering

**Contract:**
AoO resolution order MUST be stable across replays. Same initiative order and provoking action always produce identical AoO sequence.

---

### 3.7 AoO Usage Tracking — Round-Based Reset

**Decision:** `active_combat["aoo_used_this_round"]` list tracks usage, resets at `combat_round_started`

**Schema:**
```python
active_combat: {
    "initiative_order": List[str],
    "round_index": int,
    "flat_footed_actors": List[str],
    "aoo_used_this_round": List[str]  # CP-15
}
```

**Lifecycle:**
- **Initialization**: `start_combat()` creates empty list
- **Update**: `execute_turn()` appends reactor IDs after AoO resolution
- **Reset**: `execute_combat_round()` clears list at start of new round

**Rationale:**
- PHB p. 137: "Each combatant can make one attack of opportunity per round"
- List storage (not set) for deterministic serialization
- Reset timing matches PHB round lifecycle

**Contract:**
`aoo_used_this_round` MUST be cleared exactly once per round, at `combat_round_started` event emission (before any turns execute).

---

### 3.8 Action Abortion — Explicit Event + Early Return

**Decision:** Provoker defeated by AoO → `action_aborted` event + `narration="action_aborted_by_aoo"`

**Implementation:**
```python
# aidm/core/play_loop.py (execute_turn)
if aoo_result.provoker_defeated:
    events.append(Event(
        event_type="action_aborted",
        payload={
            "actor_id": turn_ctx.actor_id,
            "reason": "defeated_by_aoo",
            "turn_index": turn_ctx.turn_index
        },
        citations=[{"source_id": "681f92bc94ff", "page": 137}]
    ))

    return TurnResult(
        status="ok",  # Turn succeeded, action aborted
        narration="action_aborted_by_aoo",
        ...
    )
```

**Rationale:**
- PHB p. 137: If provoker dropped to 0 HP or below, action does not complete
- Explicit event makes abort observable in event log
- Special narration token distinguishes from other turn outcomes
- `status="ok"` because turn execution succeeded (not a validation failure)

**Contract:**
Action abortion MUST emit `action_aborted` event before `turn_end`. Aborted turns do NOT emit events for main action (movement, attack, etc.).

---

### 3.9 RNG Stream Discipline

**Decision:** AoO attacks consume from `"combat"` RNG stream (same as normal attacks)

**Stream Usage:**
- `"initiative"`: Initiative rolls (CP-14)
- `"combat"`: Attack rolls, damage rolls, AoO attacks
- `"policy"`: Tactic selection (CP-13)

**Consumption Order:**
AoO attacks consume RNG in deterministic reactor resolution order (initiative → lexicographic).

**Rationale:**
- AoO attacks are mechanically identical to normal attacks
- Stream isolation prevents cross-contamination
- RNG consumption order matches AoO resolution order
- Deterministic replay guaranteed

**Contract:**
AoO trigger detection MUST NOT consume RNG. Only AoO attack resolution (via `resolve_attack()`) consumes from `"combat"` stream.

---

### 3.10 Position Data Validation — Fail-Closed

**Decision:** Missing position data → empty threatened squares → no AoO triggers

**Implementation:**
```python
# aidm/core/aoo.py (get_threatened_squares)
entity = world_state.entities.get(reactor_id)
if entity is None:
    return []  # Fail-closed: no entity = no threats

pos_dict = entity.get("position")
if pos_dict is None:
    return []  # Fail-closed: no position = no threats
```

**Rationale:**
- Fail-closed design (fail safely, don't guess)
- Missing position data is explicit error, not silent assumption
- No speculative inference from previous state
- Deterministic (same missing data always produces same result)

**Contract:**
Position data MUST be present in `entities[actor_id]["position"]` for AoO detection. Missing data results in zero threatened squares (no AoOs).

---

### 3.11 Play Loop Integration — Insertion Point

**Decision:** AoO checks occur **after validation, before main action resolution**

**Execution Order in `execute_turn()`:**
```
1. turn_start event
2. Intent validation (actor match, target exists, target not defeated)
3. AoO trigger check (CP-15) ← INSERTION POINT
4. AoO resolution (if triggers exist)
5. Action abortion check (if provoker defeated)
6. Main action resolution (attack, movement, etc.)
7. turn_end event
```

**Rationale:**
- Validation ensures intent is legal before checking AoOs
- AoO resolution before main action matches RAW timing
- Single insertion point simplifies future interrupt systems

**Contract:**
AoO checks MUST occur after all validation passes. Invalid intents (actor mismatch, target defeated) do NOT trigger AoOs.

---

### 3.12 Backward Compatibility — No Breaking Changes

**Decision:** AoO logic only activates when `StepMoveIntent` provided

**Compatibility Mechanism:**
```python
# aidm/core/aoo.py (check_aoo_triggers)
if isinstance(intent, StepMoveIntent):
    provoking_action = "movement_out"
    from_pos = intent.from_pos
    to_pos = intent.to_pos
# Other intent types return empty list
```

**Result:**
- All 518 pre-CP-15 tests use `AttackIntent` or `FullAttackIntent`
- These intents do NOT match `StepMoveIntent` type check
- No AoO triggers for existing tests
- All existing tests pass unchanged

**Contract:**
CP-15 MUST NOT break any CP-09 through CP-14 tests. Test count progression: 518 → 524 (6 new tests only).

---

## 4. Event Model

### 4.1 New Event Types

| Event Type | Emitted By | Payload | Citations |
|------------|-----------|---------|-----------|
| `aoo_triggered` | `resolve_aoo_sequence()` | `reactor_id`, `provoker_id`, `provoking_action` | PHB p. 137 |
| `action_aborted` | `execute_turn()` | `actor_id`, `reason="defeated_by_aoo"`, `turn_index` | PHB p. 137 |
| `movement_declared` | `execute_turn()` | `actor_id`, `from_pos`, `to_pos`, `note="CP-15 stub"` | N/A (stub) |

**Note:** No `aoo_resolved` event. AoO resolution uses existing `attack_roll` and `damage_applied` events from attack pipeline.

### 4.2 Event Sequence Example

```
Event 0: turn_start {actor_id: "goblin_1", turn_index: 0}
Event 1: aoo_triggered {reactor_id: "fighter", provoker_id: "goblin_1", provoking_action: "movement_out"}
Event 2: attack_roll {attacker_id: "fighter", target_id: "goblin_1", hit: true, ...}
Event 3: damage_applied {entity_id: "goblin_1", damage: 8, hp_current: 0, hp_max: 6}
Event 4: entity_defeated {entity_id: "goblin_1", team: "monsters"}
Event 5: action_aborted {actor_id: "goblin_1", reason: "defeated_by_aoo"}
Event 6: turn_end {actor_id: "goblin_1", turn_index: 0}
```

**Timing invariant:** `action_aborted` always follows `entity_defeated` for provoker, never precedes.

---

## 5. Test Coverage

### 5.1 Tier-1 Tests (MUST PASS)

| Test | Requirement | Status |
|------|-------------|--------|
| `test_aoo_triggers_on_movement_out` | Moving out of threatened square triggers AoO | ✅ PASS |
| `test_aoo_defeats_provoker_action_aborts` | Provoker defeated by AoO → action aborts | ✅ PASS |
| `test_one_aoo_per_reactor_per_round` | Each reactor can make only one AoO per round | ✅ PASS |
| `test_multiple_reactors_resolve_in_initiative_order` | Multiple AoOs resolve in initiative order | ✅ PASS |
| `test_deterministic_replay_through_aoo` | Same seed → identical state hash and events | ✅ PASS |

### 5.2 Tier-2 Tests (SHOULD PASS)

| Test | Requirement | Status |
|------|-------------|--------|
| `test_aoo_usage_resets_each_round` | AoO usage resets at start of each round | ✅ PASS |

**Total Coverage:** 6 tests (5 Tier-1, 1 Tier-2)
**Regression Tests:** All 518 existing tests still pass (524 total)

---

## 6. File Manifest

### 6.1 New Files

| File | Purpose | Lines |
|------|---------|-------|
| `aidm/core/aoo.py` | AoO trigger detection and resolution logic | 320 |
| `tests/test_aoo_kernel.py` | CP-15 integration tests | 539 |
| `docs/CP15_AOO_DECISIONS.md` | This document | - |

### 6.2 Modified Files

| File | Changes | Rationale |
|------|---------|-----------|
| `aidm/schemas/attack.py` | Added `GridPosition` and `StepMoveIntent` classes | Movement intent for AoO detection |
| `aidm/core/play_loop.py` | Added AoO trigger check and resolution before main action | AoO interrupt integration |
| `aidm/core/combat_controller.py` | Added `aoo_used_this_round` initialization and reset | AoO usage tracking lifecycle |

---

## 7. API Reference

### 7.1 AoO Trigger Detection

```python
from aidm.core.aoo import check_aoo_triggers, AooTrigger
from aidm.schemas.attack import StepMoveIntent, GridPosition
from aidm.core.state import WorldState

# Create movement intent
move_intent = StepMoveIntent(
    actor_id="goblin_1",
    from_pos=GridPosition(x=5, y=5),
    to_pos=GridPosition(x=4, y=5)
)

# Check for AoO triggers
triggers = check_aoo_triggers(
    world_state=world_state,
    actor_id="goblin_1",
    intent=move_intent
)

# triggers is List[AooTrigger] sorted by (initiative_order, actor_id)
for trigger in triggers:
    print(f"{trigger.reactor_id} threatens {trigger.provoker_id}")
```

### 7.2 AoO Resolution

```python
from aidm.core.aoo import resolve_aoo_sequence, AooSequenceResult
from aidm.core.rng_manager import RNGManager

# Resolve AoO sequence
result = resolve_aoo_sequence(
    triggers=triggers,
    world_state=world_state,
    rng=rng,
    next_event_id=10,
    timestamp=1.0
)

# result.provoker_defeated: bool
# result.events: List[Event] (aoo_triggered, attack_roll, damage_applied, ...)
# result.aoo_reactors: List[str] (actor IDs that used AoO)

if result.provoker_defeated:
    print("Provoker defeated, abort main action")
```

### 7.3 Threatened Squares

```python
from aidm.core.aoo import get_threatened_squares
from aidm.schemas.attack import GridPosition

# Get all squares threatened by actor
threatened = get_threatened_squares(
    reactor_id="fighter",
    world_state=world_state
)

# threatened is List[GridPosition] (all 8 adjacent squares)
for pos in threatened:
    print(f"Fighter threatens ({pos.x}, {pos.y})")
```

---

## 8. Citations

All mechanics traceable to PHB 3.5e:

| Rule | Citation | Page |
|------|----------|------|
| Threatened squares (5-ft reach) | PHB 3.5e | 137 |
| Provoking actions (movement out) | PHB 3.5e | 137-138 |
| One AoO per combatant per round | PHB 3.5e | 137 |
| AoO timing (immediate interrupt) | PHB 3.5e | 137 |
| Action abortion (provoker defeated) | PHB 3.5e | 137 |

---

## 9. RAW Deviations

### 9.1 Lexicographic Tie-Breaking

**Deviation:** Multiple reactors with identical initiative total and Dex modifier resolve AoOs in lexicographic `actor_id` order (not PHB "roll again").

**PHB Rule:** "If there is still a tie, the tied characters should roll again" (PHB p. 135, initiative tie-breaking).

**Rationale:** Deterministic replay requirement. RNG consumption for tie-breaking would break replay determinism.

**Impact:** Negligible. Multiple reactors with identical initiative+Dex is rare edge case. Tie-breaking order does not affect game balance for AoOs.

**Precedent:** Established in CP-14 (initiative tie-breaking).

---

## 10. Future Work (Out of Scope)

The following systems are **explicitly deferred** to future packets:

- **CP-16:** Full movement legality, grid validation, difficult terrain, 5-foot step immunity
- **CP-17:** Combat Reflexes feat (multiple AoOs per round), reach weapons (10-ft/15-ft reach)
- **CP-17:** Ranged attack provocation, spellcasting provocation
- **CP-18:** Withdraw action, special movement modes (charge, run, tumble)
- **CP-18:** Readied actions, delay, conditional triggers
- **CP-19:** Grapple, bull rush, trip (special maneuvers that may provoke)

---

## 11. Architectural Precedent

CP-15 establishes the **interrupt system precedent** for all future interrupt-capable mechanics:

### 11.1 Interrupt Design Pattern

**Synchronous Event-Driven Execution:**
- Interrupts resolve synchronously within single call stack
- Explicit event ordering contract (no interleaving)
- Pure trigger detection function (separate from resolution)
- Abort semantics via early return + special event

**Future Applications:**
- Readied actions (conditional interrupts)
- Counterspells (spell casting interrupts)
- Grapple escape attempts (condition-driven interrupts)
- Divine intervention (plot-driven interrupts)

### 11.2 Intent-Based Timing

**Critical Design Principle:**
Interrupt timing based on **declared intent data**, not post-resolution state diffs.

**Why This Matters:**
- Prevents timing bugs when multi-step actions are introduced
- RAW-faithful (interrupts trigger on declaration, not completion)
- Deterministic (no state diff inference)
- Explicit (intent data makes replay unambiguous)

**Future Applications:**
- Movement through multiple threatened squares (CP-16)
- Spell components interrupted before casting completes (CP-17)
- Conditional triggers based on declared action type (CP-18)

---

## 12. Success Criteria

✅ All acceptance criteria met:

1. ✅ AoOs trigger deterministically for movement out of threatened squares
2. ✅ Multiple AoOs resolve in stable order (initiative → lexicographic)
3. ✅ AoO limits enforced (one per reactor per round, reset each round)
4. ✅ Provoking actions abort correctly when provoker defeated
5. ✅ Backward compatibility preserved (all 518 CP-09–CP-14 tests pass)
6. ✅ All 6 new tests pass (5 Tier-1, 1 Tier-2)
7. ✅ Event log contains `aoo_triggered` and `action_aborted` events
8. ✅ RNG streams isolated (`"combat"` for AoO attacks)

---

## 13. Lessons Learned

### 13.1 Declared Intent > State Diffs

Using declared intent data (`from_pos` in `StepMoveIntent`) instead of inferring movement from state changes prevented an entire class of timing bugs. This pattern will be critical for multi-step movement (CP-16+).

### 13.2 Synchronous Interrupts Win

Resolving AoOs synchronously within `execute_turn()` call stack was simpler and safer than deferred event processing. Single call stack makes debugging and replay trivial.

### 13.3 Attack Pipeline Reuse

Reusing `resolve_attack()` for AoO attacks eliminated duplicate logic and ensured consistency. AoO attacks emit identical events as normal attacks, simplifying event log analysis.

### 13.4 Fail-Closed for Position Data

Returning empty list when position data missing (instead of guessing or inferring) made debugging simpler. Missing position data is now an explicit error, not a silent failure.

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
**Status:** LOCKED (non-negotiable for CP-16+)
