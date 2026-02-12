# WO-059: Memory Retrieval Policy — RetrievedItem Provenance, Salience Ranking, Hard Caps

**Status:** COMPLETE
**Filed:** 2026-02-12
**Implements:** RQ-LENS-SPARK-001 Deliverable 2
**Prerequisite:** WO-032 (ContextAssembler), WO-057 (PromptPackBuilder)

---

## Problem

`ContextAssembler` does priority-ordered token-budgeted assembly but has:
- No salience/recency ranking
- No provenance tags on retrieved items
- No hard caps beyond token budget
- No formalized drop order
- Campaign memory schemas exist but retrieval is undifferentiated

## Solution

Upgrade `ContextAssembler` with deterministic retrieval policy:

### RetrievedItem Provenance

Every context item fed to Spark carries provenance metadata:

```python
@dataclass(frozen=True)
class RetrievedItem:
    text: str
    source: str          # "narration", "session_summary", "scene", "brief"
    turn_number: int     # When this was generated
    relevance_score: float  # 0.0-1.0 from ranking function
    dropped: bool        # True if cut by truncation
    drop_reason: str     # "budget_exceeded", "cap_exceeded", ""
```

### Salience Ranking

Deterministic heuristic (not ML). For recent narrations, rank by:

```
score = recency_weight * 0.5 + actor_match * 0.3 + severity_weight * 0.2
```

- **Recency**: 1.0 for most recent, linear decay to 0.0 for oldest
- **Actor match**: 1.0 if narration involves same actor/target as current brief
- **Severity weight**: lethal=1.0, devastating=0.8, severe=0.6, moderate=0.4, minor=0.2

### Hard Caps

| Source | Max Items | Max Tokens |
|--------|-----------|------------|
| Current NarrativeBrief | 1 (always) | ~120 |
| Scene description | 1 | ~60 |
| Recent narrations | 3 | remaining budget |
| Session summaries | 5 | remaining budget |

### Drop Order

Items exceeding caps or budget are included in the return list with `dropped=True`
and a `drop_reason`. Drop order:
1. Session summaries (oldest first)
2. Narrations (lowest relevance first)
3. Scene description

## Files

| File | Lines | Description |
|------|-------|-------------|
| `aidm/lens/context_assembler.py` | ~545 | RetrievedItem, compute_relevance_score, retrieve() method |
| `tests/test_retrieval_policy_059.py` | ~390 | 31 tests across 5 test classes |
| `aidm/lens/__init__.py` | Modified | Exports RetrievedItem, compute_relevance_score, caps |

## Test Coverage (31 tests)

- **TestRelevanceScore** (9): formula verification, determinism, edge cases
- **TestRetrievedItem** (4): frozen dataclass, dropped status
- **TestRetrieve** (11): brief/scene/narration/summary retrieval, ranking, caps, budget drops
- **TestAssembleBackwardCompat** (5): WO-032 API unchanged
- **TestHardCaps** (2): cap constant values

## Backward Compatibility

The `assemble()` method API is **unchanged**. All existing callers continue to work.
The new `retrieve()` method is additive — it returns `List[RetrievedItem]` with
provenance metadata that callers can inspect or ignore.

## Boundary Law Compliance

- **BL-003**: No aidm.core imports. NarrativeBrief used via getattr().
- **FREEZE-001**: RetrievedItem is a frozen dataclass.
- **Axiom 3**: Retrieval policy adapts presentation, not authority.

## Citations

- RQ-LENS-SPARK-001: Context Orchestration Sprint (Deliverable 2)
- WO-032: ContextAssembler (original implementation)
- AD-002: Lens Context Orchestration (five-channel wire protocol)
