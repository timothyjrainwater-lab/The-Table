# WO-DISCOVERY-BACKEND-001: Discovery Log Backend
**Agent:** Opus
**Work Order:** WO-DISCOVERY-BACKEND-001
**Date:** 2026-02-13
**Status:** Complete (pre-existing implementation verified)

## Summary

All three deliverables specified in the dispatch already exist and are fully tested. No new code was written. This completion report documents the verification that the existing implementation satisfies all dispatch requirements.

## Findings

### Deliverable 1: Discovery State Machine — EXISTS

**File:** `aidm/lens/discovery_log.py` (209 lines)

The `DiscoveryLog` class implements all four dispatch-specified methods:

| Dispatch Requirement | Implementation | Line |
|---------------------|---------------|------|
| `record_encounter(player_id, creature_type, knowledge_level)` | `record_encounter()` | 119 |
| `get_knowledge(player_id, creature_type) -> KnowledgeTier` | `get_knowledge()` | 148 |
| `get_all_known(player_id) -> dict[str, KnowledgeTier]` | `get_all_known()` | 156 |
| `get_visible_fields(player_id, creature_type) -> FrozenSet[str]` | `get_visible_fields()` | 168 |

All transition rules implemented:
- Transitions are ONE-WAY (monotonic — knowledge never decreases)
- Skip levels allowed (UNKNOWN -> FOUGHT is valid)
- Field gating by knowledge level via `REVEAL_SPEC` from `aidm/schemas/knowledge_mask.py`
- Serialization via `to_dict()` / `from_dict()` (lines 186-208)

### Deliverable 2: Knowledge Event Integration — EXISTS

**File:** `aidm/lens/discovery_log.py` (same file, lines 36-91)

- `KnowledgeSource` IntEnum with 6 source types: ENCOUNTER, SKILL_CHECK, NPC_CONVERSATION, SPECIAL_ABILITY, DOCUMENT, PARTY_SHARE
- `KnowledgeEvent` frozen dataclass with: `player_id`, `creature_type`, `source`, `resulting_level`, `timestamp`
- `process_event()` method (line 135) applies events to state and appends to ledger
- Timestamp is injected (BL-018 compliant), not generated internally
- Validation: empty player_id, creature_type, timestamp all raise ValueError

### Deliverable 3: Tests — EXISTS

**File:** `tests/test_discovery_log.py` (453 lines, 39 tests)

All 11 dispatch-specified test cases are covered:

| # | Dispatch Test Requirement | Test Method |
|---|--------------------------|-------------|
| 1 | New player has no knowledge | `test_new_player_has_no_knowledge` |
| 2 | Recording HEARD_OF -> query returns HEARD_OF | `test_record_heard_of` |
| 3 | Recording FOUGHT after HEARD_OF -> upgrades | `test_upgrade_heard_of_to_fought` |
| 4 | Recording HEARD_OF after FOUGHT -> stays FOUGHT | `test_no_downgrade` |
| 5 | Skip level: UNKNOWN -> FOUGHT | `test_skip_level_unknown_to_fought` |
| 6 | Field gating: HEARD_OF shows only name + type | `test_heard_of_shows_name_and_type` |
| 7 | Field gating: STUDIED shows full stat block | `test_studied_shows_full_stat_block` |
| 8 | Multiple players independent | `test_independent_players` |
| 9 | Serialization round-trip | `test_state_round_trip`, `test_event_round_trip` |
| 10 | get_all_known returns all creatures | `test_returns_all_known_creatures` |
| 11 | Knowledge events trigger transitions | `test_process_event_updates_state` |

Additional test file: `tests/test_discovery_log_knowledge_mask.py` (35 tests) covers the schema layer (tiers, masked views, field leakage, reveal spec, observed facts, serialization, validation).

### Schema Layer — EXISTS

**File:** `aidm/schemas/knowledge_mask.py` (245 lines)

- `KnowledgeTier` IntEnum: UNKNOWN=0, HEARD_OF=1, SEEN=2, FOUGHT=3, STUDIED=4
- `REVEAL_SPEC`: tier -> frozenset of visible field names (single source of truth)
- `DiscoveryEvent`, `DiscoveryEventType` (schema-level event types for the services layer)
- `KnowledgeEntry`: mutable per-player/per-entity state with event log
- `MaskedEntityView`: frozen view of entity data filtered by knowledge tier

### Stop Condition Check

| Stop Condition | Result |
|---------------|--------|
| KnowledgeLevel enum exists elsewhere | `KnowledgeTier` in `aidm/schemas/knowledge_mask.py` — reused, not duplicated |
| Contract conflicts with existing tests | No conflicts found |
| Missing field-gating tables in contract | Contract (§2.3) has complete field reveal matrix; implementation uses REVEAL_SPEC |

## Test Results

**Discovery log tests:** 74 passed (39 Lens + 35 schema)
**Full suite:** 4732 passed, 7 failed (Chatterbox TTS, external dep), 11 skipped (hardware-gated)

## Terminology Mapping

The dispatch uses slightly different terminology from the existing code:

| Dispatch Term | Code Term | Notes |
|--------------|-----------|-------|
| `KnowledgeLevel` | `KnowledgeTier` | IntEnum, same values |
| `KnowledgeSource` | `KnowledgeSource` | Exact match |
| `KnowledgeEvent` | `KnowledgeEvent` | Exact match |
| `ENCOUNTERED` / `SKILL_CHECK` etc. | Same | Exact match |

## Note for PM

This dispatch appears to have been written before the implementation was completed. The implementation at `aidm/lens/discovery_log.py` and its tests at `tests/test_discovery_log.py` already satisfy all requirements. The older implementation at `aidm/services/discovery_log.py` also exists and provides the same state machine through the `aidm.services` layer (used by `tests/test_discovery_log_knowledge_mask.py`). Both layers coexist without conflict — the Lens layer uses `KnowledgeEvent`/`KnowledgeSource` while the services layer uses `DiscoveryEvent`/`DiscoveryEventType`.
