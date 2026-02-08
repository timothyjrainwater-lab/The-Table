# CP-14 — Initiative & Action Economy Kernel

**Status:** ✅ IMPLEMENTED
**Created:** 2026-02-08
**Instruction Packet:** CP-14
**Test Coverage:** 11 integration tests (all passing)

---

## 1. Purpose

CP-14 introduces the minimum deterministic combat round controller required to unlock PHB Chapter 8 (Combat) core systems. This packet establishes:

- Deterministic initiative rolling and ordering
- Combat round progression with flat-footed state tracking
- Action economy validation framework (standard/move/full)
- Event-driven combat lifecycle (start → rounds → turns)
- Backward compatibility with CP-09/CP-12 manual turn execution

---

## 2. Implementation Scope

### IN SCOPE

✅ **Initiative System**:
- d20 + Dex modifier + misc modifiers
- Deterministic tie-breaking (total → Dex → lexicographic actor_id)
- Dedicated "initiative" RNG stream
- Event emission: `initiative_rolled` per actor

✅ **Combat Round Controller**:
- Wrapper pattern: `execute_combat_round()` calls `execute_turn()` for each actor
- Initiative order traversal
- Round index management (1-indexed, PHB convention)
- Event emission: `combat_round_started` per round

✅ **Flat-Footed State**:
- All actors start flat-footed at combat start
- Clears immediately after first successful action
- Event emission: `flat_footed_cleared` per actor
- Storage: `WorldState.active_combat["flat_footed_actors"]`

✅ **Action Economy Framework**:
- Schema extension: `TurnContext.action_type` field
- Supported types: `"move"`, `"standard"`, `"move_and_standard"`, `"full"`
- Validation deferred to future packets (CP-15+)

✅ **Backward Compatibility**:
- CP-09 manual turn execution preserved (no initiative required)
- Optional fields: `TurnContext.action_type`, `TurnResult.round_index`, `TurnResult.action_type`
- Legacy mode: `execute_turn()` works standalone without `execute_combat_round()`

### OUT OF SCOPE (Deferred)

❌ **Advanced Action Economy**:
- Readied actions, delay, AoOs, interrupts (CP-15+)
- 5-foot step, withdraw, movement validation (CP-16+)
- Swift/immediate actions (CP-17+)

❌ **Movement Legality**:
- Grid-based movement, difficult terrain, AoO provocation (CP-16+)

❌ **Initiative Modifiers**:
- Surprise rounds, flatfooted AC calculation (CP-15+)

---

## 3. Canonical Architecture Decisions

All decisions below are **LOCKED** and binding for CP-14+.

### 3.1 Play Loop Integration

**Decision:** Wrapper pattern
**Rationale:** Preserves CP-09/CP-12 `execute_turn()` API, enables gradual migration

```python
# Combat round controller (CP-14)
execute_combat_round(world_state, doctrines, rng)
  └─> for actor in initiative_order:
        └─> execute_turn(world_state, turn_ctx, doctrine, rng)

# Legacy manual mode (CP-09)
execute_turn(world_state, turn_ctx, doctrine)
```

**Contract:**
- `execute_combat_round()` orchestrates initiative traversal
- `execute_turn()` remains stateless, deterministic, reusable
- Both modes produce identical events for same inputs

---

### 3.2 Initiative Storage

**Decision:** Store in `WorldState.active_combat` dictionary
**Schema:**
```python
active_combat: {
    "initiative_order": ["fighter", "goblin_1", "wizard"],  # List[str]
    "round_index": 1,  # int, 1-indexed
    "flat_footed_actors": ["goblin_1", "wizard"],  # List[str]
    "turn_counter": 3  # int, total turns executed (legacy)
}
```

**Rationale:**
- Avoids breaking `WorldState.state_hash()` (dict is already supported)
- Flexible for future fields (surprise, delay queue, etc.)
- Serializable to JSON without schema migrations

---

### 3.3 Flat-Footed Timing

**Decision:** Clear immediately after first successful action
**Trigger:** `turn_result.status == "ok"` AND action events emitted (not just turn bookends)

**Event Sequence:**
```
turn_start → attack_roll → damage_applied → flat_footed_cleared → turn_end
```

**Rationale:**
- PHB p. 137: "A character who has not yet acted during a combat is flat-footed"
- Simplest deterministic rule (no AC recalculation mid-attack)
- Event emission makes state change observable

---

### 3.4 Action Economy Validation

**Decision:** Extend `TurnContext` with optional `action_type` field
**Schema:**
```python
@dataclass
class TurnContext:
    turn_index: int
    actor_id: str
    actor_team: str
    action_type: Optional[Literal["move", "standard", "move_and_standard", "full"]] = None
```

**Validation Rules (CP-14):**
- `None`: No validation (CP-09/CP-12 compat)
- CP-15+ will implement legality checking (move+standard = full-round, etc.)

**Rationale:**
- Optional field preserves backward compatibility
- Explicit action type enables future validation
- Literal type provides type safety

---

### 3.5 Initiative Event Emission

**Decision:** Emit at `combat_started`, not per-round
**Event Sequence:**
```
combat_started (initiative_order in payload)
  └─> initiative_rolled (per actor, d20/dex/misc/total)
  └─> combat_round_started(1)
       └─> turn_start (actor_1) → ... → turn_end
       └─> turn_start (actor_2) → ... → turn_end
  └─> combat_round_started(2)
       └─> ...
```

**Rationale:**
- PHB p. 135: Initiative is rolled once at combat start, not per round
- Deterministic replay: same initiative across all rounds
- Event log size reduction (N actors vs N actors × M rounds)

**Citations:**
- PHB p. 135: "At the start of a battle, each combatant makes an initiative check"
- PHB p. 137: "The combatants act in order from highest initiative to lowest"

---

### 3.6 Round Indexing

**Decision:** 1-indexed
**Example:** First round = `round_index: 1`

**Rationale:**
- PHB convention: "At the end of the first round..." (not "round 0")
- Human-readable logs and narration
- Consistent with PHB terminology

---

### 3.7 Initiative Tie-Breaking

**Decision:** Deterministic three-tier sorting
**Rules:**
1. Higher initiative total (descending)
2. Higher Dex modifier (descending)
3. Lexicographic `actor_id` (ascending)

**Implementation:**
```python
sorted_rolls = sorted(
    rolls,
    key=lambda r: (-r.total, -r.dex_modifier, r.actor_id)
)
```

**Rationale:**
- PHB p. 135: Dex check for ties (tier 2)
- Lexicographic actor_id ensures determinism when Dex tied (tier 3)
- No RNG consumption for ties (preserves deterministic replay)

**Citations:**
- PHB p. 135: "If two or more combatants have the same initiative check result, the combatants who are tied act in order of total initiative modifier (highest first). If there is still a tie, the tied characters should roll again to determine which one of them goes before the other."

**Note:** We replace the PHB's "roll again" with lexicographic `actor_id` for determinism.

---

### 3.8 Action Packages

**Decision:** Single `"move_and_standard"` type (not separate move+standard)
**Supported Types:**
- `"move"`: Move action only
- `"standard"`: Standard action only
- `"move_and_standard"`: Both in same turn (PHB default)
- `"full"`: Full-round action (no move)

**Rationale:**
- PHB p. 138: "In a normal round, you can perform a standard action and a move action"
- Single type simplifies validation (no need to track "used move" / "used standard")
- Future packets can decompose if needed (AoOs, split movement)

**Citations:**
- PHB p. 138-144: Action types and round structure

---

### 3.9 TurnResult Extensions

**Decision:** Add optional `round_index` and `action_type` fields
**Schema:**
```python
@dataclass
class TurnResult:
    status: str
    world_state: WorldState
    events: List[Event]
    turn_index: int
    failure_reason: Optional[str] = None
    narration: Optional[str] = None
    round_index: Optional[int] = None  # NEW (CP-14)
    action_type: Optional[str] = None  # NEW (CP-14)
```

**Usage:**
- `round_index`: Populated by `execute_combat_round()`, `None` for manual turns
- `action_type`: Echo of `TurnContext.action_type` for audit trail

**Rationale:**
- Optional fields preserve backward compatibility
- Enables round-aware logging and narration
- Action type traceability for validation debugging

---

### 3.10 CP-09 Compatibility

**Decision:** Legacy mode fully preserved
**Contract:**
```python
# CP-09 mode: Manual turn execution (no initiative)
execute_turn(
    world_state=state,
    turn_ctx=TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters"),
    doctrine=goblin_doctrine
)
# ✅ Still works, no active_combat required
```

**Backward Compatibility Test:**
- `test_backward_compatibility_with_cp09_execute_turn()` verifies manual mode
- No breaking changes to CP-09/CP-12 test suites

---

### 3.11 RNG Stream Discipline

**Decision:** Dedicated `"initiative"` stream
**Stream Usage:**
- `"initiative"`: Initiative d20 rolls only
- `"combat"`: Attack rolls, damage rolls (CP-10/CP-11)
- `"policy"`: Tactic selection (CP-13)

**Consumption Order:**
```python
# Stable lexicographic actor ordering for initiative RNG
sorted_actors = sorted(actors, key=lambda a: a[0])
for actor_id, dex_mod in sorted_actors:
    roll = rng.stream("initiative").randint(1, 20)
```

**Rationale:**
- Stream isolation prevents cross-contamination
- Lexicographic sort ensures deterministic RNG consumption order
- Future initiative modifiers won't break combat RNG replay

**Citations:**
- Internal RNG discipline (established in CP-10)

---

## 4. Event Model

### 4.1 New Event Types

| Event Type | Emitted By | Payload | Citations |
|------------|-----------|---------|-----------|
| `combat_started` | `start_combat()` | `num_actors`, `initiative_order` | PHB p. 135 |
| `initiative_rolled` | `start_combat()` | `actor_id`, `d20_roll`, `dex_modifier`, `misc_modifier`, `total` | PHB p. 135 |
| `combat_round_started` | `execute_combat_round()` | `round_index` | PHB p. 137 |
| `flat_footed_cleared` | `execute_combat_round()` | `actor_id` | PHB p. 137 |

### 4.2 Event Sequence Example

```
Event 0: combat_started {num_actors: 2, initiative_order: ["fighter", "goblin_1"]}
Event 1: initiative_rolled {actor_id: "fighter", d20_roll: 17, dex_modifier: 2, total: 19}
Event 2: initiative_rolled {actor_id: "goblin_1", d20_roll: 6, dex_modifier: 1, total: 7}
Event 3: combat_round_started {round_index: 1}
Event 4: turn_start {actor_id: "fighter", turn_index: 0}
Event 5: attack_roll {attacker_id: "fighter", ...}
Event 6: damage_applied {...}
Event 7: flat_footed_cleared {actor_id: "fighter"}
Event 8: turn_end {actor_id: "fighter"}
Event 9: turn_start {actor_id: "goblin_1", turn_index: 1}
Event 10: attack_roll {attacker_id: "goblin_1", ...}
Event 11: flat_footed_cleared {actor_id: "goblin_1"}
Event 12: turn_end {actor_id: "goblin_1"}
```

---

## 5. Test Coverage

### 5.1 Tier-1 Tests (MUST PASS)

| Test | Requirement | Status |
|------|-------------|--------|
| `test_initiative_roll_deterministic` | Same RNG seed → identical rolls | ✅ PASS |
| `test_initiative_ordering_by_total` | Higher total goes first | ✅ PASS |
| `test_initiative_ordering_tie_break_by_dex` | Same total → higher Dex wins | ✅ PASS |
| `test_initiative_ordering_tie_break_by_actor_id` | Same total+Dex → lexicographic | ✅ PASS |
| `test_start_combat_emits_correct_events` | `combat_started` + `initiative_rolled` | ✅ PASS |
| `test_flat_footed_clears_after_first_action` | Flat-footed clears after action | ✅ PASS |
| `test_combat_round_progresses_initiative_order` | Turns execute in correct order | ✅ PASS |
| `test_deterministic_replay_through_combat_round` | Same seed → identical state hash | ✅ PASS |
| `test_backward_compatibility_with_cp09_execute_turn` | Legacy mode still works | ✅ PASS |

### 5.2 Tier-2 Tests (SHOULD PASS)

| Test | Requirement | Status |
|------|-------------|--------|
| `test_multiple_combat_rounds_with_state_persistence` | Round index increments correctly | ✅ PASS |
| `test_initiative_with_misc_modifiers` | Misc modifiers apply to total | ✅ PASS |

**Total Coverage:** 11 tests (8 Tier-1, 2 Tier-2)
**Regression Tests:** All 507 existing tests still pass (518 total)

---

## 6. File Manifest

### 6.1 New Files

| File | Purpose | Lines |
|------|---------|-------|
| `aidm/core/initiative.py` | Initiative roll and ordering logic | 146 |
| `aidm/core/combat_controller.py` | Combat round orchestration | 244 |
| `tests/test_initiative_and_combat_rounds.py` | CP-14 integration tests | 415 |
| `docs/CP14_INITIATIVE_DECISIONS.md` | This document | - |

### 6.2 Modified Files

| File | Changes | Rationale |
|------|---------|-----------|
| `aidm/core/play_loop.py` | Added `action_type` to `TurnContext`, `round_index`/`action_type` to `TurnResult` | Schema extensions for action economy |
| `aidm/core/state.py` | Documented `active_combat` fields (no code changes) | Clarify WorldState contract |

---

## 7. API Reference

### 7.1 Initiative System

```python
from aidm.core.initiative import roll_initiative, sort_initiative_order, roll_initiative_for_all_actors

# Single actor
roll = roll_initiative(
    actor_id="fighter",
    dex_modifier=2,
    rng=rng,
    misc_modifier=4  # Improved Initiative feat
)
# → InitiativeRoll(actor_id="fighter", d20_roll=15, dex_modifier=2, misc_modifier=4, total=21)

# Multiple actors
rolls, order = roll_initiative_for_all_actors(
    actors=[("fighter", 2), ("goblin_1", 1)],
    rng=rng,
    misc_modifiers={"fighter": 4}
)
# → order = ["fighter", "goblin_1"]
```

### 7.2 Combat Controller

```python
from aidm.core.combat_controller import start_combat, execute_combat_round

# Start combat
world_state, events, next_id = start_combat(
    world_state=world_state,
    actors=[("fighter", 2), ("goblin_1", 1)],
    rng=rng,
    next_event_id=0,
    timestamp=0.0
)
# → Emits combat_started, initiative_rolled events
# → Initializes active_combat["initiative_order", "flat_footed_actors", "round_index"]

# Execute round
result = execute_combat_round(
    world_state=world_state,
    doctrines={"goblin_1": goblin_doctrine},
    rng=rng,
    next_event_id=next_id,
    timestamp=10.0
)
# → result.round_index = 1
# → result.events contains turn_start, attack_roll, flat_footed_cleared, turn_end
```

---

## 8. Citations

All mechanics traceable to PHB 3.5e:

| Rule | Citation | Page |
|------|----------|------|
| Initiative roll (d20 + Dex) | PHB 3.5e | 135 |
| Initiative tie-breaking | PHB 3.5e | 135 |
| Flat-footed condition | PHB 3.5e | 137 |
| Round structure | PHB 3.5e | 137 |
| Action types (standard/move/full) | PHB 3.5e | 138-144 |

---

## 9. Future Work (Out of Scope)

The following systems are **explicitly deferred** to future packets:

- **CP-15:** Readied actions, delay, AoO triggers
- **CP-16:** Movement legality, grid validation, difficult terrain
- **CP-17:** Swift/immediate actions, concentration, interrupts
- **CP-18:** Surprise rounds, flatfooted AC calculation
- **CP-19:** Grapple, bull rush, trip (special maneuvers)

---

## 10. Success Criteria

✅ All acceptance criteria met:

1. ✅ Initiative rolls are deterministic (same seed → same order)
2. ✅ Tie-breaking follows PHB + lexicographic fallback
3. ✅ Flat-footed clears after first action
4. ✅ Round progression increments correctly
5. ✅ Backward compatibility with CP-09/CP-12 preserved
6. ✅ All 518 tests pass (11 new, 507 existing)
7. ✅ Event log contains `combat_started`, `initiative_rolled`, `flat_footed_cleared`
8. ✅ RNG streams isolated ("initiative" vs "combat" vs "policy")

---

## 11. Lessons Learned

### 11.1 Wrapper Pattern Wins

Preserving `execute_turn()` API enabled:
- Zero breaking changes to CP-09/CP-12 tests
- Gradual migration path for legacy code
- Clear separation of concerns (orchestration vs execution)

### 11.2 Optional Fields for Compatibility

Adding optional `round_index` and `action_type` to `TurnResult` avoided:
- Schema migration pain
- Breaking existing tests
- Version compatibility matrix

### 11.3 Lexicographic Tie-Breaking

PHB tie-breaking rule ("roll again") is non-deterministic. Lexicographic `actor_id` fallback:
- Guarantees determinism
- Stable across replays
- Acceptable deviation from PHB (rare case, no gameplay impact)

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
**Status:** LOCKED (non-negotiable for CP-15+)
