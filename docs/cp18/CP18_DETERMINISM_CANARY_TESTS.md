# CP-18 Determinism Canary (Parallel Task Output)
**Date:** 2026-02-08
**Purpose:** Provide a lightweight *canary* test plan to catch replay-breaking nondeterminism early.

This is not a substitute for the CP-18 packet's PBHA requirement; it is a practical guardrail to run during implementation.

Authoritative determinism rules for CP-18:
- Fixed RNG stream + fixed consumption order
- No unordered iteration / deterministic event ordering
- 10× replay identical state hashes (packet requirement)

---

## 1) Recommended canary tests to add (names + intent)

### A) Replay stability (micro)
- `test_cp18_bull_rush_replay_10x_same_hash()`
- `test_cp18_trip_replay_10x_same_hash()`
- `test_cp18_overrun_replay_10x_same_hash()`

### B) RNG consumption parity across branches
- `test_cp18_trip_consumes_same_rng_on_success_and_failure()`
- `test_cp18_disarm_consumes_same_rng_with_and_without_counter_disarm()`

Threat: branch-dependent roll consumption drift.

### C) Event count stability across branches
- `test_cp18_trip_event_count_stable_success_vs_failure()`
- `test_cp18_disarm_event_count_stable_success_vs_failure()`

Threat: conditional event emission divergence.

### D) AoO ordering stability
- `test_cp18_aoo_ordering_is_initiative_then_entity_id()`

Threat: AoO cascade nondeterminism via unordered threat iteration.

---

## 2) Implementation sketch (drop into tests once code exists)

Below is a *non-binding* sketch for how replay tests might look. Adjust imports to match the repo.

```python
def run_scenario(seed: int):
    rng = RNGManager(seed=seed)
    world = build_world_state_for_cp18_scenario()
    events = simulate_cp18_action(world, rng)
    return world.state_hash(), [e.event_type for e in events]

def test_cp18_trip_replay_10x_same_hash():
    hashes = []
    for _ in range(10):
        h, _ = run_scenario(seed=12345)
        hashes.append(h)
    assert len(set(hashes)) == 1

def test_cp18_trip_event_types_stable():
    event_type_traces = []
    for _ in range(10):
        _, types = run_scenario(seed=12345)
        event_type_traces.append(types)
    assert len({tuple(t) for t in event_type_traces}) == 1
```

---

## 3) Practical note
If the repo already has a PBHA harness, reuse it; do not invent a parallel replay system.

---

**STATUS: ✅ TESTS IMPLEMENTED** (2026-02-08)

The actual implementation includes:
- `test_maneuvers_core.py`: 36 Tier-1 tests including 10× replay tests for all maneuvers
- `test_maneuvers_integration.py`: 17 Tier-2 tests including play loop determinism tests
- All determinism canary test goals are covered by the implemented test suite
