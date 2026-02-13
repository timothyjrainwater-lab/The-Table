# Completion Report: WO-DISCOVERY-BACKEND-001

**Work Order:** WO-DISCOVERY-BACKEND-001 (Discovery Log Backend)
**Agent:** Claude Opus 4.6
**Date:** 2026-02-13
**Status:** COMPLETE — All deliverables implemented and verified

---

## Deliverables

### Deliverable 1 + 2: Discovery State Machine + Knowledge Event Integration

**File:** `aidm/lens/discovery_log.py` (209 lines)

Implemented:

1. **`KnowledgeSource`** (IntEnum): 6 source types matching contract SS3.1:
   - ENCOUNTER, SKILL_CHECK, NPC_CONVERSATION, SPECIAL_ABILITY, DOCUMENT, PARTY_SHARE

2. **`KnowledgeEvent`** (frozen dataclass): Immutable event with player_id, creature_type, source, resulting_level, timestamp. Validation rejects empty fields. `to_dict()`/`from_dict()` for serialization. Timestamp is injected (BL-018 compliant).

3. **`DiscoveryLog`** class with:
   - `record_encounter(player_id, creature_type, knowledge_level)` — direct state mutation, monotonic only
   - `process_event(event: KnowledgeEvent) -> KnowledgeTier` — event-driven mutation with ledger append
   - `get_knowledge(player_id, creature_type) -> KnowledgeTier` — query current tier
   - `get_all_known(player_id) -> dict[str, KnowledgeTier]` — all creatures known (sorted)
   - `get_visible_fields(player_id, creature_type) -> FrozenSet[str]` — field gating via REVEAL_SPEC
   - `to_dict()` / `from_dict()` — serialization with state + event ledger

**Design decisions:**
- Reuses existing `KnowledgeTier` and `REVEAL_SPEC` from `aidm.schemas.knowledge_mask` (no duplicate enums)
- Lens-tier: imports only from `aidm.schemas`, not from `aidm.core`
- Knowledge state is append-only (monotonic advancement, skip levels allowed)
- Uses existing v1 field whitelist from `REVEAL_SPEC` — consistent with the 35 existing enforcement tests

### Deliverable 3: Tests

**File:** `tests/test_discovery_log.py` (453 lines, 39 tests)

| Test Class | Count | Coverage |
|-----------|-------|----------|
| TestTierTransitions | 11 | UNKNOWN default, record each tier, upgrades, no-downgrade, skip levels, progressive, idempotent |
| TestFieldGating | 6 | UNKNOWN->nothing, HEARD_OF fields, SEEN fields, FOUGHT fields, STUDIED full stat block, superset invariant |
| TestIndependentState | 3 | Independent players, independent creatures, cross-player isolation |
| TestGetAllKnown | 4 | Empty, all creatures, excludes other players, sorted keys |
| TestKnowledgeEvent | 9 | Process event state, advance, no-downgrade, ledger append, all sources, 3 validation tests, frozen |
| TestSerialization | 6 | Empty round-trip, state round-trip, event round-trip, KnowledgeEvent round-trip, get_all_known after, visible_fields after |

All 11 tests from the dispatch spec are covered:
1. New player has no knowledge (UNKNOWN)
2. Recording HEARD_OF -> query returns HEARD_OF
3. Recording FOUGHT after HEARD_OF -> upgrades to FOUGHT
4. Recording HEARD_OF after FOUGHT -> stays FOUGHT (no downgrade)
5. Skip level: UNKNOWN -> FOUGHT valid
6. Field gating: HEARD_OF shows only name + type
7. Field gating: STUDIED shows full stat block
8. Multiple players have independent knowledge states
9. Serialization round-trip preserves all state
10. get_all_known returns all creatures for a player
11. Knowledge events correctly trigger level transitions

---

## Test Results (Verified 2026-02-13)

**Discovery Log tests (Lens):** 39 passed, 0 failed
**Knowledge Mask tests (Services):** 35 passed, 0 failed
**Combined discovery tests:** 74 passed, 0 failed

**Full suite:** 4741 passed, 8 failed (pre-existing), 11 skipped

Pre-existing failures (unrelated to this work order):
- `tests/immersion/test_chatterbox_tts.py` (7 failures) — TTS adapter dependency issue
- `tests/spec/test_intent_bridge_contract_compliance.py` (1 failure) — candidate ordering

---

## Existing Code Reuse

| Component | Reused? | Notes |
|-----------|---------|-------|
| `KnowledgeTier` enum | Yes | From `aidm.schemas.knowledge_mask` — no duplicate |
| `REVEAL_SPEC` dict | Yes | Single source of truth for field gating |
| `DiscoveryEvent` (v1) | No | New `KnowledgeEvent` has different shape per dispatch spec |
| `DiscoveryLog` (v1 service) | No | Not modified — Lens-tier implementation is separate |

---

## Two DiscoveryLog Implementations

The codebase contains two complementary DiscoveryLog classes:

1. **`aidm/lens/discovery_log.py`** — Lens-tier (this work order)
   - Uses `KnowledgeEvent` with explicit `resulting_level` and `timestamp`
   - Lightweight state machine (dict of tuples -> KnowledgeTier)
   - Field gating via `get_visible_fields()` returning FrozenSet[str]
   - Exported in `aidm/lens/__init__.py` as `LensDiscoveryLog`

2. **`aidm/services/discovery_log.py`** — Services-tier (WO-CODE-DISCOVERY-001)
   - Uses `DiscoveryEvent` with `DiscoveryEventType` enum
   - Richer state with `KnowledgeEntry` (observed_facts, event_log)
   - Produces `MaskedEntityView` with filtered entity data
   - 35 tests in `tests/test_discovery_log_knowledge_mask.py`

---

## Stop Condition Results

| Condition | Result |
|-----------|--------|
| KnowledgeLevel enum exists elsewhere | Found `KnowledgeTier` in `aidm.schemas.knowledge_mask` — reused |
| Contract conflicts with existing tests | No conflicts — contract field naming (observed/engaged) differs from code (SEEN/FOUGHT) but behavior is consistent |
| Missing field-gating tables | Contract SS2.3 has full matrix; existing `REVEAL_SPEC` in code has a v1 mapping — used v1 mapping for consistency with 35 existing tests |

---

## Flags for PO

1. **Contract naming divergence:** The contract uses `observed`/`engaged` stage names while existing code uses `SEEN`/`FOUGHT`. Implementation follows the existing code convention. A future reconciliation pass may be needed if the contract names become canonical.

2. **v1 vs v2 field gating:** The existing `REVEAL_SPEC` (v1) uses a simple field whitelist per tier. The contract (SS2.3) specifies richer per-field reliability, provenance labels, and sub-field tracking. This implementation uses the v1 model for consistency with existing tests. Upgrading to the full v2 model (per-field `RevealedFieldState` with reliability/provenance) is a separate work item.

3. **Numeric exposure policy (SS2.4):** Not implemented in this work order. The contract defines three policies (A/B/C) for numeric field exposure at STUDIED tier. The current implementation exposes all STUDIED fields uniformly per `REVEAL_SPEC`. Policy enforcement is a future deliverable.

---

END OF COMPLETION REPORT
