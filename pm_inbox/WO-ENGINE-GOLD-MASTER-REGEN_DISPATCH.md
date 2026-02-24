# WO-ENGINE-GOLD-MASTER-REGEN — Gold Master Fixture Regeneration

**Issued:** 2026-02-24
**Authority:** PM
**Gate:** ENGINE-GOLD-MASTER-REGEN (new gate, defined below)
**Urgency:** HIGH — pre-existing replay suite failure blocks every future engine WO

---

## 1. Target Lock

The four persisted gold master fixtures in `tests/fixtures/gold_masters/` predate several accepted WOs that changed the `hp_changed` event payload schema:

- **WO-ENGINE-DR-001:** Added `dr_absorbed` field to `hp_changed` (present as `0` when DR is zero)
- **WO-ENGINE-DEATH-DYING-001:** Added `entity_disabled`, `entity_dying`, `entity_stabilized` events; changed `entity_defeated` semantics

The replay harness compares live event output against stored fixtures field-by-field. Any added field — even `dr_absorbed: 0` — is a drift. The tavern fixture currently fails with:

```
DRIFT DETECTED at turn 1, event index 16
Field: payload.dr_absorbed
Expected: None
Actual: 0
```

This is not a regression introduced by the builder — it is a pre-existing schema evolution mismatch. The fix is to regenerate all four fixtures against the current working tree.

**Done means:** All four replay tests pass. Gate ENGINE-GOLD-MASTER-REGEN 4/4 green. Zero replay suite failures.

---

## 2. What To Do

### Step 1: Audit current fixture drift

Run all four replay tests to confirm which fixtures fail:

```bash
cd f:/DnD-3.5
python -m pytest tests/integration/test_replay_regression.py::TestPersistedGoldMasters -v --tb=short
```

Expected: at minimum tavern fails. Others may fail if they also contain pre-DR-001 `hp_changed` events.

### Step 2: Identify the scenario parameters

From the test file, the four fixtures use these parameters:

| Fixture | Scenario Name | Seed | Turns |
|---------|---------------|------|-------|
| `tavern_100turn.jsonl` | "Tavern Brawl" | 42 | 100 |
| `dungeon_100turn.jsonl` | "Dungeon Corridor" | 123 | 100 |
| `field_100turn.jsonl` | "Open Field Battle" | 456 | 100 |
| `boss_100turn.jsonl` | "Boss Fight" | 789 | 100 |

### Step 3: Regenerate using the existing harness

The `ReplayRegressionHarness` has `record_gold_master()` — use it to regenerate. Write a one-off script:

```python
# scripts/regen_gold_masters.py
"""Regenerate all four gold master fixtures against current engine state."""
from pathlib import Path
from aidm.testing.replay_regression import ReplayRegressionHarness
from aidm.schemas.testing import ScenarioConfig

OUT_DIR = Path("tests/fixtures/gold_masters")

harness = ReplayRegressionHarness()

# Each scenario config must match the original parameters
# Load from existing fixture to get the full scenario config, then re-record
scenarios = [
    ("tavern_100turn.jsonl",   "Tavern Brawl",       42,  100),
    ("dungeon_100turn.jsonl",  "Dungeon Corridor",   123, 100),
    ("field_100turn.jsonl",    "Open Field Battle",  456, 100),
    ("boss_100turn.jsonl",     "Boss Fight",         789, 100),
]
```

**IMPORTANT:** Use the `ScenarioConfig` that was used to produce the original fixtures. The scenario configs are embedded in the existing JSONL files (each line is an event; the header line contains `scenario_name` and `seed`). Load each existing fixture, extract its embedded `ScenarioConfig`, and re-record with the same config + seed + turns count.

Alternatively, examine how the fixtures were originally recorded:

```bash
cd f:/DnD-3.5
python -c "
from aidm.testing.replay_regression import ReplayRegressionHarness
from pathlib import Path
h = ReplayRegressionHarness()
gm = h.load_gold_master(Path('tests/fixtures/gold_masters/tavern_100turn.jsonl'))
print('scenario_name:', gm.scenario_name)
print('seed:', gm.seed)
print('turns:', len([e for e in gm.events]))
print('scenario_config type:', type(gm.scenario_config))
print('scenario_config:', gm.scenario_config)
"
```

Use the extracted `scenario_config` to re-record:

```python
gold_master = harness.record_gold_master(
    scenario=gm.scenario_config,
    turns=100,
    seed=gm.seed
)
harness.save_gold_master(gold_master, Path("tests/fixtures/gold_masters/tavern_100turn.jsonl"))
```

Repeat for all four fixtures.

### Step 4: Verify all four pass

```bash
python -m pytest tests/integration/test_replay_regression.py::TestPersistedGoldMasters -v --tb=short
```

All 8 tests in the class must pass (4 load + 4 replay + integrity check).

### Step 5: Full regression check

```bash
python -m pytest tests/ -q --tb=line \
  --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py \
  --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py
```

Zero new failures beyond the pre-existing 21.

---

## 3. Event Schema — What Changed

The fixtures were recorded before these WOs landed. The relevant schema changes:

### WO-ENGINE-DR-001 (`hp_changed` payload)

**Before:**
```json
{"event_type": "hp_changed", "payload": {"entity_id": "...", "hp_before": 11, "hp_after": 3, "delta": -8, "source": "attack_damage"}}
```

**After:**
```json
{"event_type": "hp_changed", "payload": {"entity_id": "...", "hp_before": 11, "hp_after": 3, "delta": -8, "source": "attack_damage", "dr_absorbed": 0}}
```

`dr_absorbed` is always present now, even when 0. The replay harness sees `None` (absent) vs `0` as drift.

### WO-ENGINE-DEATH-DYING-001 (new event types)

New events that did not exist when fixtures were recorded:
- `entity_disabled` (HP == 0, not instant defeat)
- `entity_dying` (HP -1 to -9)
- `entity_stabilized` / `dying_fort_failed` (from dying tick)

If any fixture had an entity reach 0 HP, the event sequence now differs (disabled vs immediately defeated). Regeneration is the correct fix — not a schema patch.

---

## 4. What This WO Does NOT Do

- Does NOT change any engine code
- Does NOT change the replay harness
- Does NOT change the test file
- Does NOT regenerate gold masters with different seeds or scenario configs
- Does NOT touch the action economy gold masters (those were regenerated during CP-24 and are current)
- Does NOT fix X-01 or any other pre-existing gate failure

---

## 5. Gate Spec

**Gate name:** `ENGINE-GOLD-MASTER-REGEN`
**Test file:** `tests/integration/test_replay_regression.py::TestPersistedGoldMasters`

| # | Test | Check |
|---|------|-------|
| GM-01 | Tavern gold master loads | `test_load_tavern_gold_master` PASS |
| GM-02 | Dungeon gold master loads | `test_load_dungeon_gold_master` PASS |
| GM-03 | Field gold master loads | `test_load_field_gold_master` PASS |
| GM-04 | Boss gold master loads | `test_load_boss_gold_master` PASS |
| GM-05 | Tavern replays deterministically | `test_replay_tavern_gold_master` PASS |
| GM-06 | Dungeon replays deterministically | `test_replay_dungeon_gold_master` PASS |
| GM-07 | Field replays deterministically | `test_replay_field_gold_master` PASS |
| GM-08 | Boss replays deterministically | `test_replay_boss_gold_master` PASS |
| GM-09 | All fixtures pass integrity check | `test_all_gold_masters_have_valid_integrity` PASS |
| GM-10 | Zero new regressions suite-wide | Full suite minus known ignores: delta vs pre-regen baseline ≤ 0 new failures |

**Test count target:** ENGINE-GOLD-MASTER-REGEN 10/10.

---

## 6. Preflight

```bash
cd f:/DnD-3.5

# Confirm current failure baseline
python -m pytest tests/integration/test_replay_regression.py::TestPersistedGoldMasters -v --tb=short

# Regenerate
python scripts/regen_gold_masters.py

# Verify gate
python -m pytest tests/integration/test_replay_regression.py::TestPersistedGoldMasters -v

# Full suite
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py --ignore=tests/test_speak_signal.py
```
