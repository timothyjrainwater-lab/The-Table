# WO-009 Completion Report: Provenance Tracking (W3C PROV-DM)

**Assigned To:** Sonnet-C (Claude 4.5 Sonnet)
**Issued By:** Opus (PM)
**Date Completed:** 2026-02-11
**Status:** Complete

---

## 1. Files Created with Line Counts

| File | Lines | Description |
|------|-------|-------------|
| `aidm/core/provenance.py` | 734 | W3C PROV-DM implementation with all core types and relations |
| `tests/test_provenance.py` | 782 | Comprehensive test suite (59 tests) |
| **Total** | **1,516** | |

---

## 2. Test Count and Pass/Fail Status

### New Tests: 59 passed

```
tests/test_provenance.py::TestComputeValueHash::test_string_hash PASSED
tests/test_provenance.py::TestComputeValueHash::test_different_values_different_hashes PASSED
tests/test_provenance.py::TestComputeValueHash::test_dict_hash_sorted PASSED
tests/test_provenance.py::TestComputeValueHash::test_nested_structure_hash PASSED
tests/test_provenance.py::TestComputeValueHash::test_number_hash PASSED
tests/test_provenance.py::TestComputeValueHash::test_list_hash PASSED
tests/test_provenance.py::TestComputeValueHash::test_none_hash PASSED
tests/test_provenance.py::TestProvenanceEntity::test_register_entity_creates PASSED
tests/test_provenance.py::TestProvenanceEntity::test_value_hash_computed_correctly PASSED
tests/test_provenance.py::TestProvenanceEntity::test_get_entity_retrieves PASSED
tests/test_provenance.py::TestProvenanceEntity::test_get_entity_returns_none_for_unknown PASSED
tests/test_provenance.py::TestProvenanceEntity::test_entity_is_frozen PASSED
tests/test_provenance.py::TestProvenanceEntity::test_entity_to_dict PASSED
tests/test_provenance.py::TestProvenanceEntity::test_entity_from_dict PASSED
tests/test_provenance.py::TestProvenanceActivity::test_register_activity_creates PASSED
tests/test_provenance.py::TestProvenanceActivity::test_complete_activity_sets_ended_at PASSED
tests/test_provenance.py::TestProvenanceActivity::test_get_activity_retrieves PASSED
tests/test_provenance.py::TestProvenanceActivity::test_get_activity_returns_none_for_unknown PASSED
tests/test_provenance.py::TestProvenanceActivity::test_complete_unknown_activity_noop PASSED
tests/test_provenance.py::TestProvenanceActivity::test_activity_types PASSED
tests/test_provenance.py::TestProvenanceActivity::test_activity_to_dict PASSED
tests/test_provenance.py::TestProvenanceActivity::test_activity_from_dict PASSED
tests/test_provenance.py::TestProvenanceAgent::test_register_agent_creates PASSED
tests/test_provenance.py::TestProvenanceAgent::test_get_agent_retrieves PASSED
tests/test_provenance.py::TestProvenanceAgent::test_get_agent_returns_none_for_unknown PASSED
tests/test_provenance.py::TestProvenanceAgent::test_agent_types PASSED
tests/test_provenance.py::TestProvenanceAgent::test_agent_to_dict PASSED
tests/test_provenance.py::TestProvenanceAgent::test_agent_from_dict PASSED
tests/test_provenance.py::TestWasGeneratedBy::test_record_generation_links_entity_to_activity PASSED
tests/test_provenance.py::TestWasGeneratedBy::test_generation_to_dict PASSED
tests/test_provenance.py::TestWasAttributedTo::test_record_attribution_links_entity_to_agent PASSED
tests/test_provenance.py::TestWasAttributedTo::test_multiple_attributions PASSED
tests/test_provenance.py::TestWasAttributedTo::test_attribution_to_dict PASSED
tests/test_provenance.py::TestWasDerivedFrom::test_record_derivation_links_entities PASSED
tests/test_provenance.py::TestWasDerivedFrom::test_derivation_with_activity PASSED
tests/test_provenance.py::TestWasDerivedFrom::test_derivation_to_dict PASSED
tests/test_provenance.py::TestProvenanceChain::test_single_step_chain PASSED
tests/test_provenance.py::TestProvenanceChain::test_two_step_chain PASSED
tests/test_provenance.py::TestProvenanceChain::test_multi_step_chain PASSED
tests/test_provenance.py::TestProvenanceChain::test_chain_for_unknown_entity PASSED
tests/test_provenance.py::TestProvenanceChain::test_circular_derivation_handled PASSED
tests/test_provenance.py::TestExplain::test_explain_returns_correct_attributed_to PASSED
tests/test_provenance.py::TestExplain::test_explain_returns_correct_derived_from PASSED
tests/test_provenance.py::TestExplain::test_explain_chain_depth_accurate PASSED
tests/test_provenance.py::TestExplain::test_explain_generation_info PASSED
tests/test_provenance.py::TestExplain::test_explain_unknown_entity PASSED
tests/test_provenance.py::TestExplain::test_explanation_to_dict PASSED
tests/test_provenance.py::TestSerialization::test_to_dict_from_dict_roundtrip PASSED
tests/test_provenance.py::TestSerialization::test_serialization_preserves_chain PASSED
tests/test_provenance.py::TestSerialization::test_empty_store_serialization PASSED
tests/test_provenance.py::TestEdgeCases::test_unknown_entity_id_returns_none PASSED
tests/test_provenance.py::TestEdgeCases::test_empty_store PASSED
tests/test_provenance.py::TestEdgeCases::test_get_entity_sources_for_unattributed_entity PASSED
tests/test_provenance.py::TestEdgeCases::test_explain_for_entity_with_no_relations PASSED
tests/test_provenance.py::TestEdgeCases::test_multiple_derivation_sources PASSED
tests/test_provenance.py::TestEdgeCases::test_activity_unique_ids PASSED
tests/test_provenance.py::TestIntegration::test_spark_generation_workflow PASSED
tests/test_provenance.py::TestIntegration::test_box_calculation_workflow PASSED
tests/test_provenance.py::TestIntegration::test_player_input_workflow PASSED
```

---

## 3. Full Suite Verification

```
python -m pytest tests/ -v --tb=short
===================== 2505 passed, 43 warnings in 10.26s ======================
```

**Zero regressions.** All existing tests continue to pass.

---

## 4. Design Decisions Made

### 4.1 W3C PROV-DM Compliance

Implemented the three core PROV concepts:
- **Entity** (`ProvenanceEntity`): A fact/data item with ID, value hash, and creation timestamp
- **Activity** (`ProvenanceActivity`): An action with start/end times and type
- **Agent** (`ProvenanceAgent`): A source (spark, box, player, system)

Implemented the three core PROV relations:
- **wasGeneratedBy**: Links entity to generating activity
- **wasAttributedTo**: Links entity to responsible agent
- **wasDerivedFrom**: Links derived entity to source entity

### 4.2 Value Hashing

- Uses SHA-256 with first 16 hex characters for compact storage
- JSON serialization with `sort_keys=True` for deterministic hashing
- `default=str` fallback for non-JSON-serializable types

```python
def compute_value_hash(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]
```

### 4.3 Activity ID Generation

- Uses UUID hex with prefix for human-readable IDs
- Format: `activity_{uuid.hex[:8]}` (e.g., `activity_a1b2c3d4`)

### 4.4 Provenance Chain Traversal

- Chains traced backwards from current entity to root
- Circular references detected and handled (breaks loop)
- Returns list ordered from root to current

### 4.5 Multiple Attributions/Derivations

- Entities can be attributed to multiple agents
- Entities can be derived from multiple sources
- All stored and queryable

---

## 5. Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All new tests pass | ✅ | 59/59 tests passing |
| All existing tests pass | ✅ | 2505 passed, zero regressions |
| PROV-DM relations implemented | ✅ | wasGeneratedBy, wasAttributedTo, wasDerivedFrom |
| Provenance chains queryable | ✅ | `get_provenance_chain()` tested |
| explain() returns useful summary | ✅ | `TestExplain` class with 6 tests |
| Serialization works | ✅ | `TestSerialization` with round-trip tests |

---

## 6. Issues Discovered

None. Implementation proceeded smoothly.

---

## 7. API Summary

### Core Types

| Type | Description |
|------|-------------|
| `ProvenanceEntity` | Fact/data item with value hash |
| `ProvenanceActivity` | Action with start/end times |
| `ProvenanceAgent` | Source (spark/box/player/system) |

### Relations

| Relation | Description |
|----------|-------------|
| `WasGeneratedBy` | Entity ← Activity |
| `WasAttributedTo` | Entity ← Agent |
| `WasDerivedFrom` | Entity ← Source Entity |

### ProvenanceStore Methods

| Method | Description |
|--------|-------------|
| `register_entity(id, value, turn)` | Create new provenance entity |
| `register_activity(type, turn)` | Create new activity |
| `register_agent(id, type)` | Create new agent |
| `record_generation(entity, activity, turn)` | Link entity to activity |
| `record_attribution(entity, agent)` | Link entity to agent |
| `record_derivation(derived, source, activity?)` | Link derived to source |
| `get_provenance_chain(entity_id)` | Get full derivation ancestry |
| `get_entity_sources(entity_id)` | Get attributed agents |
| `explain(entity_id)` | Human-readable summary |
| `to_dict()` / `from_dict()` | Serialization |

### ProvenanceExplanation

```python
@dataclass(frozen=True)
class ProvenanceExplanation:
    entity_id: str
    current_value_hash: str
    attributed_to: List[str]      # Agent IDs
    derived_from: List[str]       # Source entity IDs
    generation_activity: Optional[str]
    generation_turn: Optional[int]
    chain_depth: int              # 0 = original, N = derived N times
```

---

## 8. Integration Points

This module integrates with:
- `aidm/core/lens_index.py` — LensFact has `provenance_id` field linking to provenance entities

Example integration pattern:
```python
# When Lens stores a fact
store = ProvenanceStore()
agent = store.register_agent("spark_narrator", "spark")
activity = store.register_activity("spark_generation", turn=5)

prov_entity = store.register_entity("npc:description", value, turn=5)
store.record_generation(prov_entity.entity_id, activity.activity_id, turn=5)
store.record_attribution(prov_entity.entity_id, agent.agent_id)

# Link to LensFact
lens_fact = LensFact(
    entity_id="npc",
    attribute="description",
    value=value,
    source_tier=SourceTier.SPARK,
    timestamp=5,
    provenance_id=prov_entity.entity_id  # Link to provenance
)
```

---

## 9. Deliverables Summary

| Deliverable | Location | Status |
|-------------|----------|--------|
| Implementation | `aidm/core/provenance.py` | ✅ Complete (734 lines) |
| Tests | `tests/test_provenance.py` | ✅ Complete (782 lines, 59 tests) |
| Completion Report | `pm_inbox/SONNET-C_WO-009_PROVENANCE.md` | ✅ This document |

---

**Work Order Complete.** Ready for PM review.
