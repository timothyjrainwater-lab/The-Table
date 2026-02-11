# WO-018 Completion Report

**Work Order:** WO-018 — Replay Regression Suite
**Status:** COMPLETE
**Date:** 2026-02-11

## Summary

Built a deterministic replay regression suite that validates the 1000-turn determinism gate. Created Gold Master recordings from existing scenarios and implemented comparison infrastructure to detect any replay drift.

## Deliverables

### 1. aidm/testing/replay_regression.py (751 lines)

ReplayRegressionHarness class with:
- `record_gold_master(scenario, turns, seed)` — Run scenario, capture full event log as Gold Master
- `replay_and_compare(gold_master)` — Replay from seed, compare event-by-event
- `run_thousand_turn_gate(scenario, seed)` — Execute 1000 turns, verify final state hash matches replay
- `detect_drift(expected_log, actual_log)` — Return first divergence point with context
- `serialize_gold_master(path)` / `load_gold_master(path)` — JSONL persistence

Supporting dataclasses:
- `GoldMaster` — Contains scenario_name, seed, turn_count, events, final_state_hash, recorded_at
- `DriftReport` — Contains has_drift, turn_number, event_index, field_that_differs, expected/actual values
- `ReplayResult` — Contains success, events_processed, final_state_hash, drift_report

### 2. tests/integration/test_replay_regression.py (1018 lines)

52 tests organized into 11 test classes:
- `TestGoldMasterRecording` — Recording produces valid Gold Master (5 tests)
- `TestReplayComparison` — Replay matches Gold Master exactly (4 tests)
- `TestThousandTurnGate` — 1000-turn scenario replays deterministically (4 tests)
- `TestDriftDetection` — Drift detector finds first divergence (7 tests)
- `TestCrossScenario` — All 4 scenarios pass regression (2 tests)
- `TestSerialization` — Gold Master round-trips through JSONL (7 tests)
- `TestRNGIsolation` — Different streams don't cross-contaminate (3 tests)
- `TestUtilityFunctions` — Standalone utility function tests (6 tests)
- `TestGoldMasterDataclass` — GoldMaster dataclass methods (3 tests)
- `TestDriftReportDataclass` — DriftReport dataclass methods (2 tests)
- `TestPersistedGoldMasters` — Tests using pre-recorded Gold Masters (9 tests)

### 3. Gold Master Files (tests/fixtures/gold_masters/)

| File                   | Events | Turns | Hash (prefix)    |
|------------------------|--------|-------|------------------|
| tavern_100turn.jsonl   | 46     | 2     | 1c8c44295b36...  |
| dungeon_100turn.jsonl  | 1926   | 100   | 0656f3d0a653...  |
| field_100turn.jsonl    | 338    | 9     | faad5668fadb...  |
| boss_100turn.jsonl     | 122    | 5     | 8959627b5f7a...  |

Note: Turn counts vary because combat ends when one team is eliminated.

### 4. Supporting Files

- `tests/fixtures/gold_masters/generate.py` (277 lines) — Script to regenerate Gold Masters
- Updated `aidm/testing/__init__.py` — Exports new classes
- Updated `pyproject.toml` — Added `replay` marker for optional test skipping

## Lines of Code

| File                                      | Lines |
|-------------------------------------------|-------|
| aidm/testing/replay_regression.py         | 751   |
| tests/integration/test_replay_regression.py | 1018  |
| tests/fixtures/gold_masters/generate.py   | 277   |
| Gold Master JSONL files (total)           | 2436  |
| **Total**                                 | **4482** |

## Test Results

```
tests/integration/test_replay_regression.py: 52 passed
Full test suite: 2913 passed, 43 warnings
```

## Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| 1000-turn replay produces identical final state hash | PASS |
| All 4 scenarios have Gold Master recordings | PASS |
| Drift detection correctly identifies first divergence point | PASS |
| Gold Masters serialize/deserialize without loss | PASS |
| All existing tests pass (2861+) | PASS (2913) |

## Discoveries About Replay Determinism

1. **Combat ends naturally** — Most scenarios end within 2-9 turns when one team is eliminated, even with 100-turn round limits. The dungeon scenario goes longest (100 turns) because goblins are positioned far from the party.

2. **Event log is the source of truth** — The existing `reduce_event()` in `replay_runner.py` correctly reduces all mutating events. Replay determinism depends on:
   - RNG seed isolation (via RNGManager streams)
   - Monotonic event IDs (via EventLog)
   - Deterministic state hashing (via json.dumps with sort_keys=True)

3. **Gold Master format is human-readable** — JSONL with one event per line allows easy diffing and debugging. The header line contains metadata (scenario, seed, hash).

4. **Drift detection granularity** — The harness detects drift at the field level within payloads, reporting turn number, event index, and specific field that differs.

## Architecture Notes

The replay regression harness integrates with existing infrastructure:
- Uses `ScenarioRunner` from WO-016 for scenario execution
- Uses `RNGManager` for deterministic randomness
- Uses `WorldState.state_hash()` for final state verification
- Gold Masters include `initial_state` and `scenario_config` for self-contained replay

## Usage Examples

```python
# Record a Gold Master
harness = ReplayRegressionHarness()
gold_master = harness.record_gold_master(scenario, turns=100, seed=42)
harness.serialize_gold_master(gold_master, Path("tavern.jsonl"))

# Replay and compare
result = harness.replay_from_gold_master_file(Path("tavern.jsonl"))
assert result.success

# Run 1000-turn gate
success, drift = harness.run_thousand_turn_gate(scenario, seed=42)
assert success
```

## Files Created/Modified

### Created:
- `aidm/testing/replay_regression.py`
- `tests/integration/test_replay_regression.py`
- `tests/fixtures/gold_masters/generate.py`
- `tests/fixtures/gold_masters/tavern_100turn.jsonl`
- `tests/fixtures/gold_masters/dungeon_100turn.jsonl`
- `tests/fixtures/gold_masters/field_100turn.jsonl`
- `tests/fixtures/gold_masters/boss_100turn.jsonl`

### Modified:
- `aidm/testing/__init__.py` — Added exports
- `pyproject.toml` — Added `replay` marker
