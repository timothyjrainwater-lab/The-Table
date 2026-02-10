# R1 — LLM Query Interface Design Options
## Agent A (LLM & Indexed Memory Architect) Research Deliverable

**Agent:** Agent A (LLM & Indexed Memory Architect)
**RQ ID:** RQ-LLM-002 (LLM Query Interface Design)
**Mission:** Evaluate query interface approaches for LLM-to-memory retrieval (model-agnostic)
**Date:** 2026-02-10
**Status:** RESEARCH (Non-binding, awaiting RQ-HW-003 model selection)
**Authority:** ADVISORY (R0 Research Phase)

---

## Executive Summary

**RQ-LLM-002 Question Restatement:**
> How does LLM query indexed records? (Prompt engineering? Function calling? RAG?)

**Acceptance Threshold:**
- LLM can reliably query by entity ID, event ID, relationship
- Success rate >85% for complex queries (e.g., "Find all events where Fighter attacked Goblin")
- No context window overflow for 50-turn sessions

**Research Scope (Model-Agnostic):**
This document evaluates three primary query interface approaches WITHOUT committing to a specific LLM model. Final selection depends on:
- RQ-HW-003 model selection (Agent D responsibility)
- Model capabilities (context window, function calling support, latency)
- Hardware constraints (VRAM budget, inference speed)

**Key Finding:**
All three approaches are viable, but **optimal choice depends on model selection**. Each approach has distinct trade-offs in complexity, latency, and accuracy.

---

## 1. Query Interface Approaches (Model-Agnostic Analysis)

### Approach 1: Prompt Engineering (Pure Text)

**Description:**
Serialize indexed memory objects to text, inject into LLM prompt, use natural language queries.

**Interface Contract:**

```python
# Inputs
query: str  # Natural language query (e.g., "What evidence exists for Theron's loyalty?")
memory_snapshot: FrozenMemorySnapshot  # Immutable memory state

# Output
query_result: QueryResult  # Structured result with extracted facts
```

**How It Works:**
1. Convert `SessionLedgerEntry`, `EvidenceLedger`, `ThreadRegistry` to markdown/JSON
2. Inject serialized memory into LLM prompt context
3. LLM reads memory, extracts relevant facts, returns structured response
4. Parse LLM response into `QueryResult` object

**Example Prompt:**
```
MEMORY CONTEXT:
---
Session Ledger (Session 10):
- Facts: ["Theron befriended Merchant Bob", "Party explored ruined temple"]

Evidence Ledger:
- Character: theron, Type: loyalty, Description: "Defended ally in combat"
- Character: theron, Type: loyalty, Description: "Refused to abandon merchant"

Thread Registry:
- Clue: merchant_bob_rumors, Status: active
---

QUERY: "What evidence exists for Theron showing loyalty?"

INSTRUCTIONS: Extract all evidence entries matching the query. Return as JSON:
{
  "evidence_ids": ["ev_001", "ev_007"],
  "summary": "Theron showed loyalty by defending allies and refusing to abandon the merchant."
}
```

**Pros:**
- ✅ Model-agnostic (works with any text-completion LLM)
- ✅ Simple implementation (no function calling required)
- ✅ Human-readable prompts (easy to debug)
- ✅ Flexible queries (natural language)

**Cons:**
- ❌ Context window consumption (entire memory serialized)
- ❌ Parsing overhead (LLM response → structured data)
- ❌ Hallucination risk (LLM may invent facts not in memory)
- ❌ Latency (full context processing on each query)

**Model Requirements:**
- Context window: ≥8K tokens (for 50-session campaigns)
- Output format: JSON or structured text
- Temperature: ≤0.3 (deterministic retrieval)

**Acceptance Criteria:**
- Query accuracy: >85% fact extraction correctness
- Hallucination rate: <5% (facts not in memory)
- Latency: <2 seconds per query (median hardware)

---

### Approach 2: Function Calling (Structured Queries)

**Description:**
LLM generates structured function calls to query indexed memory. Memory query engine executes functions, returns results.

**Interface Contract:**

```python
# LLM generates function call
function_name: str  # e.g., "query_evidence_by_type"
parameters: dict    # e.g., {"character_id": "theron", "evidence_type": "loyalty"}

# Memory engine executes function
query_result: QueryResult  # Structured result from indexed memory
```

**How It Works:**
1. LLM receives user query + available function signatures
2. LLM generates function call (e.g., `query_evidence_by_type(character="theron", type="loyalty")`)
3. Memory query engine executes function against indexed memory
4. Results returned to LLM for narration generation

**Example Function Signatures:**
```python
def query_session_by_number(session_number: int) -> SessionLedgerEntry:
    """Retrieve session ledger entry by session number."""

def query_evidence_by_character(character_id: str) -> List[CharacterEvidenceEntry]:
    """Retrieve all evidence entries for a character."""

def query_evidence_by_type(character_id: str, evidence_type: str) -> List[CharacterEvidenceEntry]:
    """Retrieve evidence entries filtered by type (e.g., 'loyalty', 'betrayal')."""

def query_events_by_participants(actor: str, target: str) -> List[Event]:
    """Retrieve events involving specific actor and target."""
```

**Example Interaction:**
```
User Query: "What evidence exists for Theron showing loyalty?"

LLM Analysis:
- Identifies character: "theron"
- Identifies evidence type: "loyalty"
- Generates function call: query_evidence_by_type(character_id="theron", evidence_type="loyalty")

Memory Engine Execution:
- Executes function against EvidenceLedger
- Returns: [CharacterEvidenceEntry(id="ev_001", ...), CharacterEvidenceEntry(id="ev_007", ...)]

LLM Response:
"Theron has shown loyalty in two instances: defending an ally in combat, and refusing to abandon a merchant."
```

**Pros:**
- ✅ Reduced context consumption (no full memory serialization)
- ✅ Deterministic queries (function calls → predictable results)
- ✅ Lower hallucination risk (LLM queries ground truth, not memory)
- ✅ Composable queries (LLM can chain function calls)

**Cons:**
- ❌ Model-specific (requires function calling support: GPT-4, Claude, Mistral 7B Instruct)
- ❌ Complex implementation (function signature management, parameter validation)
- ❌ Limited expressiveness (only predefined functions available)
- ❌ Debugging overhead (function call failures harder to diagnose)

**Model Requirements:**
- Function calling: Native support (OpenAI-style or Anthropic tool use)
- Context window: ≥4K tokens (function signatures + conversation)
- Temperature: ≤0.3 (deterministic function selection)

**Acceptance Criteria:**
- Function call accuracy: >90% (correct function + parameters)
- Query success rate: >85% (function returns expected results)
- Latency: <1 second per query (deterministic lookup)

---

### Approach 3: RAG (Retrieval-Augmented Generation)

**Description:**
Embed indexed memory objects as vectors, use semantic search to retrieve relevant context, inject into LLM prompt.

**Interface Contract:**

```python
# Inputs
query: str  # Natural language query
memory_snapshot: FrozenMemorySnapshot  # Indexed memory (vectorized)

# Retrieval Stage
retrieved_chunks: List[MemoryChunk]  # Top-k relevant memory chunks (semantic search)

# Generation Stage
query_result: QueryResult  # LLM response using retrieved context
```

**How It Works:**
1. **Embedding Phase (Prep):** Convert all `SessionLedgerEntry`, `EvidenceLedger`, `ThreadRegistry` to vector embeddings
2. **Retrieval Phase (Query):** Embed user query, perform semantic search (cosine similarity), retrieve top-k chunks
3. **Generation Phase (Query):** Inject retrieved chunks into LLM prompt, generate response

**Example Flow:**
```
User Query: "What evidence exists for Theron showing loyalty?"

1. Query Embedding:
   query_vector = embed("What evidence exists for Theron showing loyalty?")

2. Semantic Search (against vectorized memory):
   top_k_chunks = [
       CharacterEvidenceEntry(id="ev_001", description="Defended ally in combat"),
       CharacterEvidenceEntry(id="ev_007", description="Refused to abandon merchant"),
       SessionLedgerEntry(session_number=10, facts_added=["Theron befriended Merchant Bob"])
   ]

3. LLM Prompt (with retrieved context):
   ---
   RETRIEVED CONTEXT:
   - Evidence: Theron defended ally in combat (ev_001)
   - Evidence: Theron refused to abandon merchant (ev_007)
   - Session 10 Fact: Theron befriended Merchant Bob
   ---

   QUERY: "What evidence exists for Theron showing loyalty?"

   LLM Response:
   "Theron has shown loyalty by defending an ally in combat and refusing to abandon a merchant."
```

**Pros:**
- ✅ Semantic understanding (matches meaning, not just keywords)
- ✅ Context window efficiency (only relevant chunks retrieved)
- ✅ Handles large campaigns (100+ sessions via vector DB)
- ✅ Model-agnostic (works with any text-completion LLM)

**Cons:**
- ❌ Infrastructure overhead (vector DB: FAISS, Chroma, Pinecone)
- ❌ Embedding latency (query embedding + search adds overhead)
- ❌ Retrieval accuracy dependency (semantic search must be >90% accurate)
- ❌ Complexity (embedding model + vector DB + LLM coordination)

**Model Requirements:**
- Embedding model: Sentence transformers (e.g., `all-MiniLM-L6-v2`, 384-dim)
- Vector DB: FAISS (local) or Chroma (lightweight)
- LLM context window: ≥4K tokens (retrieved chunks + conversation)
- Temperature: ≤0.3 (deterministic retrieval)

**Acceptance Criteria:**
- Retrieval accuracy: >90% (top-k chunks contain relevant facts)
- Query success rate: >85% (LLM extracts correct facts from chunks)
- Latency: <1.5 seconds per query (embedding + search + generation)

---

## 2. Approach Comparison Matrix

| Criterion | Prompt Engineering | Function Calling | RAG |
|-----------|-------------------|------------------|-----|
| **Model Support** | Any text-completion LLM | Requires function calling (GPT-4, Claude, Mistral Instruct) | Any text-completion LLM |
| **Context Window Requirement** | High (8K+ tokens) | Medium (4K tokens) | Medium (4K tokens) |
| **Implementation Complexity** | Low | Medium | High |
| **Infrastructure Dependency** | None | None | Vector DB (FAISS/Chroma) |
| **Query Latency (estimated)** | 2 sec | 1 sec | 1.5 sec |
| **Hallucination Risk** | High (LLM invents facts) | Low (deterministic queries) | Medium (retrieval errors) |
| **Scalability (100+ sessions)** | Poor (context overflow) | Good (function-based lookup) | Excellent (vector search) |
| **Debugging Ease** | Easy (human-readable prompts) | Medium (function call inspection) | Hard (embedding + retrieval pipeline) |
| **Determinism** | Low (temperature-dependent) | High (function calls deterministic) | Medium (retrieval non-deterministic) |

---

## 3. Recommended Approach (Pending Model Selection)

### If Model Supports Function Calling (e.g., GPT-4, Claude, Mistral 7B Instruct):
**Recommendation:** **Approach 2 (Function Calling)**

**Rationale:**
- Lowest hallucination risk (LLM queries ground truth, not memory)
- Deterministic queries (function calls → predictable results)
- Acceptable latency (<1 sec per query)
- No infrastructure overhead (no vector DB required)

**Implementation Path:**
1. Define function signatures for common queries (session, evidence, events)
2. Implement memory query engine (`query_evidence_by_type`, etc.)
3. Validate LLM function call accuracy >90%
4. Test query success rate >85%

---

### If Model Does NOT Support Function Calling (e.g., base LLaMA, GPT-J):
**Recommendation:** **Approach 1 (Prompt Engineering)** for small campaigns, **Approach 3 (RAG)** for large campaigns

**Rationale (Prompt Engineering):**
- Simple implementation (no function calling required)
- Works with any text-completion LLM
- Acceptable for small campaigns (<30 sessions, <8K context)

**Rationale (RAG):**
- Scales to 100+ sessions (vector search handles large memory)
- Context window efficiency (only top-k chunks retrieved)
- Semantic understanding (matches meaning, not keywords)

**Implementation Path (Prompt Engineering):**
1. Serialize memory to markdown/JSON
2. Inject into LLM prompt with query
3. Parse LLM response → structured data
4. Validate hallucination rate <5%

**Implementation Path (RAG):**
1. Embed memory objects using sentence transformers
2. Store embeddings in FAISS (local vector DB)
3. Retrieve top-k chunks on query
4. Inject chunks into LLM prompt
5. Validate retrieval accuracy >90%

---

## 4. Interface Contract Definition (Model-Agnostic)

### Input Schema

```python
@dataclass
class MemoryQueryRequest:
    """Request for LLM-driven memory query."""
    query_text: str  # Natural language query
    memory_snapshot: FrozenMemorySnapshot  # Immutable memory state
    temperature: float = 0.3  # Low temp for deterministic retrieval
    max_results: int = 10  # Limit result count
```

### Output Schema

```python
@dataclass
class QueryResult:
    """Result from LLM memory query."""
    query_text: str  # Original query
    facts_extracted: List[str]  # Facts extracted from memory
    evidence_ids: List[str]  # IDs of relevant evidence entries
    session_refs: List[int]  # Referenced session numbers
    confidence: float  # LLM confidence score (0.0-1.0)
    hallucination_detected: bool  # Flag if LLM invented facts
```

### Query Engine Interface

```python
class LLMQueryEngine:
    """Abstract interface for LLM-driven memory queries."""

    def query_memory(self, request: MemoryQueryRequest) -> QueryResult:
        """Execute memory query using LLM.

        MUST enforce:
        - Read-only access (no memory mutations)
        - Temperature ≤0.5 (deterministic retrieval)
        - Hallucination detection (validate facts against memory)
        - Abstention on context overflow (no invention)
        """
        raise NotImplementedError

    def validate_query_result(self, result: QueryResult, memory: FrozenMemorySnapshot) -> bool:
        """Validate that query result contains only facts from memory.

        Returns:
            True if all facts exist in memory (no hallucination)
            False if any fact not found in memory
        """
        raise NotImplementedError
```

---

## 5. Acceptance Criteria (Model-Agnostic)

### Success Metrics (All Approaches)

| Metric | Threshold | Validation Method |
|--------|-----------|-------------------|
| **Query Accuracy** | >85% | Fact extraction correctness (ground truth comparison) |
| **Hallucination Rate** | <5% | Facts not in memory / total facts extracted |
| **Query Latency** | <2 sec | Median query time (50-session campaign) |
| **Context Overflow Handling** | 0 inventions | Abstention enforced when memory exceeds context |
| **Determinism** | >95% same facts | Same query → same facts (across 10 runs) |

### Test Scenarios (Model-Agnostic)

**Test 1: Simple Entity Query**
- Query: "What happened to Theron in Session 10?"
- Expected: Extract facts from `SessionLedgerEntry(session_number=10)`
- Validation: All facts present in session ledger

**Test 2: Complex Relationship Query**
- Query: "Find all events where Theron attacked Goblin 1"
- Expected: Extract events from event log with `actor="theron"`, `target="goblin_1"`
- Validation: All events match ground truth

**Test 3: Evidence Aggregation Query**
- Query: "What evidence exists for Theron showing loyalty?"
- Expected: Extract all `CharacterEvidenceEntry` with `evidence_type="loyalty"`
- Validation: All evidence IDs match memory

**Test 4: Context Overflow (50+ sessions)**
- Query: "Recap all sessions"
- Expected: LLM abstains ("I have records for Sessions 1-20, please specify...")
- Validation: Zero invented facts

**Test 5: Hallucination Detection**
- Query: "What happened in Session 99?" (Session 99 does not exist)
- Expected: LLM abstains ("No records for Session 99")
- Validation: No hallucinated facts

---

## 6. Implementation Blockers (Awaiting RQ-HW-003)

### Blocked on Model Selection (Agent D)

**Cannot proceed with final implementation until:**

1. **Model chosen** (e.g., Mistral 7B, Llama 3, GPT-4, Claude)
2. **Function calling support confirmed** (determines Approach 2 viability)
3. **Context window size locked** (determines Approach 1 vs Approach 3)
4. **Hardware constraints finalized** (VRAM budget, inference latency)

**Model Capabilities Needed:**
- Context window: ≥4K tokens (minimum), ≥8K tokens (preferred)
- Function calling: Optional (enables Approach 2)
- Temperature control: Required (≤0.5 for queries)
- JSON output: Preferred (structured parsing)

---

## 7. Next Steps (Post-Model Selection)

### If Agent D Selects Function-Calling Model:
1. Implement Approach 2 (Function Calling)
2. Define function signatures for memory queries
3. Implement memory query engine
4. Validate query accuracy >85%

### If Agent D Selects Non-Function-Calling Model:
1. Implement Approach 1 (Prompt Engineering) for small campaigns
2. Implement Approach 3 (RAG) for large campaigns
3. Validate hallucination rate <5%
4. Validate query accuracy >85%

---

## 8. Open Questions for Agent D / PM

### Question 1: Model Selection Priority
**Q:** Should model selection prioritize function calling support (Approach 2) or minimize VRAM (Approach 1)?
**Agent A Recommendation:** Prioritize function calling (deterministic queries, lower hallucination risk)

### Question 2: Vector DB Infrastructure
**Q:** Is vector DB infrastructure (FAISS/Chroma) acceptable for M0 launch, or defer to M1?
**Agent A Recommendation:** Defer RAG to M1 (avoid infrastructure complexity for M0)

### Question 3: Context Window Target
**Q:** What is target campaign size for M0? (30 sessions? 50 sessions? 100 sessions?)
**Agent A Recommendation:** Target 30 sessions for M0 (fits in 8K context with Approach 1)

---

## 9. Deliverable Artifacts

### 9.1 This Document

**File:** `docs/research/R1_LLM_QUERY_INTERFACE_OPTIONS.md`
**Type:** Research report (non-binding)
**Status:** COMPLETE, AWAITING AGENT D MODEL SELECTION

### 9.2 No Prototype Code

**Rationale:** Query interface implementation requires model selection (RQ-HW-003 blocker)
**Test Style:** Design-level analysis (no code execution)

**If prototype required after model selection:**
- Create `prototypes/llm_query_interface_harness.py` (throwaway)
- Implement all 3 approaches
- Benchmark query accuracy, latency, hallucination rate
- Select optimal approach based on model capabilities

---

## 10. Agent A Compliance Statement

**Agent A operated in R0 RESEARCH-ONLY mode:**
- ✅ NO production code modifications
- ✅ NO schema changes to aidm/schemas/
- ✅ NO Design Layer edits
- ✅ NO authority promotion (verdict marked ADVISORY, requires Agent D model selection)
- ✅ NO new RQs created
- ✅ Model-agnostic analysis (no model choice made)

**Hard Constraints Observed:**
- ❌ NO model selection (Agent D responsibility)
- ❌ NO implementation without model choice
- ❌ NO assumptions about hardware constraints (awaiting RQ-HW-003)

**Reporting Line:** Agent D (Governance) → PM

---

## 11. Decision Surface for Agent D / PM

### Option A: APPROVE RESEARCH (Recommended) ✅

**Action:**
- Accept model-agnostic query interface analysis
- Proceed with RQ-HW-003 model selection (Agent D)
- Agent A implements final query interface after model locked

**Pros:**
- All 3 approaches evaluated with trade-offs
- Implementation path clear for each model type
- No premature commitment to approach

**Cons:**
- RQ-LLM-002 not fully complete until model selected
- Agent A blocked on implementation until RQ-HW-003 done

---

### Option B: REQUIRE PROTOTYPE NOW (Not Recommended) ⚠️

**Action:**
- Agent A prototypes all 3 approaches with assumed model (e.g., Mistral 7B)
- Benchmark query accuracy, latency, hallucination rate
- Select approach based on prototype results

**Pros:**
- Early validation of query interface feasibility
- Concrete performance data for decision-making

**Cons:**
- Wasted effort if Agent D selects different model
- Prototype may not reflect production constraints

---

## 12. References

- **RQ-LLM-001 Deliverable:** `docs/research/R1_INDEXED_MEMORY_STRESS_TEST.md` (memory substrate validation)
- **RQ-LLM-002 Acceptance Criteria:** `docs/research/R0_MASTER_TRACKER.md` (lines 53-63)
- **M1 Safeguards:** `docs/design/M1_LLM_SAFEGUARD_ARCHITECTURE.md` (temperature isolation, abstention policy)
- **Determinism Contract:** `docs/research/R0_DETERMINISM_CONTRACT.md` (Layer 1/2/3 boundaries)

---

## 13. Certification Request

**Agent A requests Agent D certification:**

**Deliverable:** R1_LLM_QUERY_INTERFACE_OPTIONS.md
**RQ Answered:** RQ-LLM-002 (LLM Query Interface Design — Model-Agnostic Analysis)
**Verdict:** RESEARCH COMPLETE (Awaiting Model Selection for Final Implementation)
**Confidence:** 0.90

**Certification Checklist:**
- [x] RQ question restated clearly
- [x] 3 approaches evaluated (Prompt Engineering, Function Calling, RAG)
- [x] Trade-offs documented (pros/cons, model requirements)
- [x] Interface contract defined (model-agnostic)
- [x] Acceptance criteria specified (>85% query accuracy, <5% hallucination)
- [x] Test scenarios outlined (5 tests)
- [x] Blockers identified (RQ-HW-003 model selection)
- [x] Next steps defined (post-model selection)
- [x] Open questions listed (model priority, vector DB, context window)
- [x] Markdown only (no code)
- [x] Hard constraints observed (no model selection, no implementation)

**Awaiting:** Agent D model selection (RQ-HW-003) + PM approval

---

**END OF R1 RESEARCH DELIVERABLE**

**Date:** 2026-02-10
**Agent:** Agent A (LLM & Indexed Memory Architect)
**RQ:** RQ-LLM-002 (LLM Query Interface Design — Model-Agnostic)
**Verdict:** RESEARCH COMPLETE (Implementation blocked on RQ-HW-003)
**Recommendation:** Proceed with model selection (Agent D), then finalize query interface
**Confidence:** 0.90
