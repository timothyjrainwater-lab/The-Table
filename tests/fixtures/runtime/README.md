# Runtime Test Fixtures

This directory contains minimal campaign fixtures for runtime vertical slice integration testing.

**Purpose:** Provide deterministic, minimal test data for bootstrap → resume → replay flow testing.

**Work Order:** WO-M1-RUNTIME-WIRING-02
**Agent:** Sonnet A
**Date:** 2026-02-10

---

## Fixture Inventory

### 1. Tiny Campaign (Empty)

**Files:**
- `tiny_campaign_manifest.json`
- `tiny_campaign_start_state.json`
- `tiny_campaign_events_empty.jsonl`
- `tiny_campaign_intents_empty.jsonl`

**Description:**
A minimal new campaign with:
- 2 entities: `goblin_1` (monster) and `pc_fighter` (party)
- Combat initialized (round 1, turn_counter 0)
- No events yet (empty logs)

**Use case:**
Test new campaign initialization, first turn execution, empty log handling.

**Seed:** 42
**Campaign ID:** `test-tiny-campaign-001`

---

### 2. Tiny Campaign (2 Turns Played)

**Files:**
- `tiny_campaign_manifest.json` (reused, update campaign_id when installing)
- `tiny_campaign_start_state.json` (reused)
- `tiny_campaign_events_2turns.jsonl`
- `tiny_campaign_intents_2turns.jsonl`

**Description:**
Same campaign as above, but with 2 turns already played:
- **Turn 0 (goblin_1):** Goblin attacks PC fighter (hit for 4 damage)
- **Turn 1 (pc_fighter):** PC fighter attacks goblin (hit for 10 damage, goblin dies)

**Event count:** 10 events
**Intent count:** 1 intent (PC's attack action only; goblin turn is AI-driven, no player intent)

**Use case:**
Test campaign resume, replay verification, log sync checks.

---

### 3. Corrupt Event Log (ID Gap)

**Files:**
- `tiny_campaign_events_corrupt_id_gap.jsonl`

**Description:**
Event log with ID sequence: 0, 1, **999** (gap violates BL-008 monotonicity).

**Expected behavior:**
`EventLog.from_jsonl()` should raise `ValueError` during load.
`SessionBootstrap.load_campaign_data()` should wrap as `BootstrapError`.

**Use case:**
Test fail-fast on event ID gaps (BL-008 enforcement).

---

### 4. Corrupt Event Log (Invalid JSON)

**Files:**
- `tiny_campaign_events_corrupt_json.jsonl`

**Description:**
Event log with incomplete JSON line (missing closing brace).

**Expected behavior:**
`json.loads()` should raise `JSONDecodeError`.
`SessionBootstrap.load_campaign_data()` should wrap as `BootstrapError`.

**Use case:**
Test fail-fast on JSON parse errors.

---

## Using Fixtures in Tests

### Example: Load Empty Campaign

```python
import shutil
from pathlib import Path
from aidm.core.campaign_store import CampaignStore
from aidm.runtime.bootstrap import SessionBootstrap

def test_load_empty_campaign(tmp_path):
    fixtures_dir = Path(__file__).parent / "fixtures" / "runtime"
    store = CampaignStore(tmp_path)

    # Install fixture campaign
    campaign_id = "test-tiny-campaign-001"
    campaign_dir = tmp_path / campaign_id
    campaign_dir.mkdir(parents=True)
    (campaign_dir / "assets").mkdir()
    (campaign_dir / "prep").mkdir()
    (campaign_dir / "prep" / "prep_jobs.jsonl").touch()

    shutil.copy(fixtures_dir / "tiny_campaign_manifest.json", campaign_dir / "manifest.json")
    shutil.copy(fixtures_dir / "tiny_campaign_start_state.json", campaign_dir / "start_state.json")
    shutil.copy(fixtures_dir / "tiny_campaign_events_empty.jsonl", campaign_dir / "events.jsonl")
    shutil.copy(fixtures_dir / "tiny_campaign_intents_empty.jsonl", campaign_dir / "intents.jsonl")

    # Load campaign data
    manifest, initial_state, event_log, session_log = SessionBootstrap.load_campaign_data(
        store, campaign_id
    )

    assert len(event_log.events) == 0
    assert len(session_log.entries) == 0
```

### Example: Load 2-Turn Campaign

```python
def test_resume_from_2turns(tmp_path):
    fixtures_dir = Path(__file__).parent / "fixtures" / "runtime"
    store = CampaignStore(tmp_path)

    campaign_id = "test-tiny-campaign-2turns"
    campaign_dir = tmp_path / campaign_id
    campaign_dir.mkdir(parents=True)
    (campaign_dir / "assets").mkdir()
    (campaign_dir / "prep").mkdir()
    (campaign_dir / "prep" / "prep_jobs.jsonl").touch()

    # Update manifest campaign_id
    shutil.copy(fixtures_dir / "tiny_campaign_manifest.json", campaign_dir / "manifest.json")
    import json
    with open(campaign_dir / "manifest.json", "r") as f:
        manifest_data = json.load(f)
    manifest_data["campaign_id"] = campaign_id
    with open(campaign_dir / "manifest.json", "w") as f:
        json.dump(manifest_data, f, sort_keys=True, indent=2)

    shutil.copy(fixtures_dir / "tiny_campaign_start_state.json", campaign_dir / "start_state.json")
    shutil.copy(fixtures_dir / "tiny_campaign_events_2turns.jsonl", campaign_dir / "events.jsonl")
    shutil.copy(fixtures_dir / "tiny_campaign_intents_2turns.jsonl", campaign_dir / "intents.jsonl")

    # Load and verify
    manifest, initial_state, event_log, session_log = SessionBootstrap.load_campaign_data(
        store, campaign_id
    )

    assert len(event_log.events) == 10  # 2 complete turns
    turn_end_count = sum(1 for e in event_log.events if e.event_type == "turn_end")
    assert turn_end_count == 2
```

---

## Extending Fixtures

### Adding a New Fixture

1. **Create fixture files** in this directory:
   - `<name>_manifest.json`
   - `<name>_start_state.json`
   - `<name>_events.jsonl`
   - `<name>_intents.jsonl`

2. **Document in this README** under Fixture Inventory section:
   - Purpose
   - Entity configuration
   - Event/intent count
   - Use case

3. **Update integration tests** in `tests/test_runtime_vertical_slice_integration.py` to use new fixture.

### Fixture Constraints

**MUST:**
- Use deterministic data (fixed RNG seed, fixed timestamps)
- Use valid D&D 3.5e entity schemas
- Use monotonic event IDs (no gaps unless testing corruption)
- Use sorted JSON keys (all `.json` files)
- Document expected behavior (especially for corrupt fixtures)

**MUST NOT:**
- Use `uuid.uuid4()` or `datetime.now()` in fixtures (violates BL-017/BL-018)
- Include large datasets (keep minimal for fast tests)
- Mix test scenarios in single fixture (one fixture = one scenario)

---

## Fixture Data Schema Reference

### CampaignManifest (manifest.json)

Required fields:
- `campaign_id`: String (unique identifier)
- `title`: String (human-readable name)
- `engine_version`: String (e.g., "0.1.0")
- `config_schema_version`: String (e.g., "1.0")
- `created_at`: ISO timestamp string
- `master_seed`: Integer (RNG seed)
- `session_zero`: SessionZeroConfig object
- `paths`: CampaignPaths object

### WorldState (start_state.json)

Required fields:
- `ruleset_version`: String (e.g., "3.5e")
- `entities`: Dict[entity_id, entity_data]
- `active_combat`: Combat state object
- `metadata`: Metadata object

### Event (events.jsonl, one JSON object per line)

Required fields:
- `event_id`: Integer (monotonic, 0-indexed)
- `event_type`: String (e.g., "turn_start", "attack_roll", "turn_end")
- `timestamp`: Float (game time)
- `payload`: Dict (event-specific data)
- `rng_offset`: Integer (RNG stream offset after event)
- `citations`: List of citation objects (may be empty)

### IntentEntry (intents.jsonl, one JSON object per line)

Required fields (from RuntimeSession IntentEntry schema):
- `intent_id`: String
- `actor_id`: String
- `action_type`: String (e.g., "ATTACK")
- `status`: String (e.g., "RESOLVED")
- `source_text`: String (user input)
- `created_at`: ISO timestamp string
- `updated_at`: ISO timestamp string
- `target_id`: String (optional, may be null)
- `result_status`: String (e.g., "SUCCESS", optional)

---

## Sonnet D Integration Notes

**CLI Invocation Pattern:**
```bash
python -m aidm.runtime.runner --campaign <campaign_id>
```

**Bootstrap Flow (for wiring reference):**

1. `SessionBootstrap.load_campaign_data(store, campaign_id)`
   - Returns: `(manifest, initial_state, event_log, session_log)`
   - Raises: `BootstrapError` on missing files or corrupt data

2. `SessionBootstrap.detect_partial_write(event_log)`
   - Returns: `PartialWriteRecoveryResult`
   - If `incomplete_turn_detected`, discard events after last `turn_end`

3. `SessionBootstrap.check_log_sync(event_log, session_log)`
   - Returns: `LogSyncCheckResult`
   - Verify: `turn_end` count >= resolved intent count
   - Raises: `BootstrapError` on desync (intents > turn_ends)

4. Replay event log to reconstruct WorldState
   - Use: `aidm.core.replay_runner.run(initial_state, event_log, rng_manager)`
   - Verify: reconstructed state hash matches expected (if stored)

5. Initialize `RuntimeSession` with reconstructed WorldState

6. Enter turn loop (accept input → resolve → log → display → repeat)

7. On exit, persist events and intents to `.jsonl` files

**Fixtures Coverage:**

| Test Scenario | Fixture | What It Proves |
|--------------|---------|---------------|
| Empty campaign load | `tiny_campaign_*_empty.jsonl` | Bootstrap handles 0-event campaigns |
| Resume from 2 turns | `tiny_campaign_*_2turns.jsonl` | Replay produces correct state |
| Event ID gap fail-fast | `tiny_campaign_events_corrupt_id_gap.jsonl` | BL-008 enforcement |
| JSON parse error fail-fast | `tiny_campaign_events_corrupt_json.jsonl` | Corrupt file detection |
| Partial write recovery | Programmatically truncated 2-turn fixture | Incomplete turn discard |
| Log desync detection | 2-turn fixture + extra phantom intent | Event/intent count mismatch |

---

**Last Updated:** 2026-02-10
**Maintainer:** Sonnet A (WO-M1-RUNTIME-WIRING-02)
**Status:** Complete (fixtures + integration tests ready)
