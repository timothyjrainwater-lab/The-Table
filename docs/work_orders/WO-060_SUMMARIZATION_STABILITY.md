# WO-060: Summarization Stability Protocol — Template-Based Segment Summaries

**Status:** COMPLETE
**Filed:** 2026-02-12
**Implements:** RQ-LENS-SPARK-001 Deliverable 3 (Phase 1)
**Prerequisite:** WO-059 (Memory Retrieval Policy), WO-046B (NarrativeBrief)

---

## Problem

No multi-turn summarization exists. `ContextAssembler` passes raw recent narrations.
Over 200 turns, the window of "what Spark can see" drifts away from what actually
happened, with no way to detect or correct this.

## Solution

### SessionSegmentSummary

Frozen dataclass for 10-turn segment summaries:

```python
@dataclass(frozen=True)
class SessionSegmentSummary:
    segment_id: str
    turn_range: Tuple[int, int]      # (start_turn, end_turn)
    summary_text: str                # 2-3 sentences, factual
    key_facts: Tuple[str, ...]       # Bullet points of state changes
    entity_states: Tuple[Tuple[str, str], ...]  # entity_name → status
    defeated_entities: FrozenSet[str]
    content_hash: str                # SHA-256 of inputs
    schema_version: str              # "1.0.0"
```

### Template-Based Summarization (v1)

Deterministic. No LLM involved. Same inputs always produce same summary.

Template:
```
"Turns {start}-{end}: {actor} engaged {target} in combat.
 {hit_count} hits, {miss_count} misses. Severity: {max_severity}.
 Defeated: {defeated_list}. Scene: {scene_description}."
```

### Summary Triggers

- **Every 10 turns**: Auto-generated via `SegmentTracker.record_turn()`
- **Scene transition**: Forced via `SegmentTracker.force_segment()`
- **Combat end**: Forced via `SegmentTracker.force_segment()`

### Drift Detection

Two invariants checked between consecutive segments:

1. **Entity state consistency**: Defeated entities must not appear active in later segments
2. **Fact monotonicity**: Defeat is permanent — cannot un-happen

### Rebuild from Sources

When drift is detected:
1. Log the drift event
2. Rebuild stale segment from raw NarrativeBrief history
3. Replace stale summary (deterministic operation)

## Files

| File | Lines | Description |
|------|-------|-------------|
| `aidm/lens/segment_summarizer.py` | ~345 | SessionSegmentSummary, SegmentSummarizer, SegmentTracker |
| `tests/test_segment_summarizer_060.py` | ~370 | 34 tests across 7 test classes |

## Test Coverage (34 tests)

- **TestSessionSegmentSummary** (3): frozen dataclass, entity_state_dict, schema_version
- **TestSegmentSummarizer** (13): combat summary, hit/miss counting, defeat/condition/severity tracking, scene, content hash determinism, entity states, edge cases
- **TestDriftDetection** (5): consistent segments, defeated-active drift, monotonicity, absence, frozen result
- **TestRebuildFromSources** (1): rebuild matches original
- **TestSegmentTracker** (12): auto-trigger, multiple segments, forced segments, defeated tracking, drift check, segment IDs

## Architecture

```
SessionOrchestrator
    ↓ record_turn(brief, turn_number)
SegmentTracker
    ↓ (every 10 turns or force_segment())
SegmentSummarizer.summarize(briefs, segment_id, turn_range)
    ↓
SessionSegmentSummary (frozen, deterministic)
    ↓ get_summaries() → newest-first list
ContextAssembler.retrieve(segment_summaries=...)
    ↓
RetrievedItem (source="session_summary", provenance tags)
    ↓
PromptPackBuilder → MemoryChannel
```

## Boundary Law Compliance

- **BL-003**: No aidm.core imports. NarrativeBrief accessed via getattr().
- **FREEZE-001**: SessionSegmentSummary and DriftResult are frozen dataclasses.
- **Axiom 3**: Summarization adapts presentation, not authority.

## What This Does NOT Do

- LLM-generated summaries (deferred to v2 per RQ-LENS-SPARK-001)
- Cross-session persistence (campaign memory schemas exist but not wired)
- Semantic drift detection via LLM (keyword-based in v1)
- Wiring into SessionOrchestrator (requires integration step — Step 10 of Phase 2)

## Citations

- RQ-LENS-SPARK-001: Context Orchestration Sprint (Deliverable 3)
- WO-046B: NarrativeBrief completion (source data for summaries)
- AD-002: Lens Context Orchestration (MemoryChannel budget allocation)
