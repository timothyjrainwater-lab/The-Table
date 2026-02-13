# M1 LLM Safeguards Requirements
## Planning Constraints from R0 Research Validation

**Document Type:** M1 Planning / Requirements Specification
**Source Authority:** RQ-LLM-001 (R1_INDEXED_MEMORY_STRESS_TEST.md), RQ-LLM-002 (R1_DETERMINISTIC_RECALL_VS_GENERATIVE.md)
**Target Phase:** M1 (LLM Narration Integration)
**Date:** 2026-02-10
**Status:** PLANNING (Non-binding until M1 kickoff)
**Agent:** Agent A (LLM & Systems Architect)

---

## Purpose

This document translates validated R0 research findings (RQ-LLM-001, RQ-LLM-002) into **explicit requirements** for M1 implementation. These requirements ensure:
- Deterministic recall (mechanical outcomes replay-identical)
- Generative flexibility (narration text may vary)
- No recall corruption (presentation variance does not mutate memory)
- No narrative drift (paraphrasing does not accumulate errors)

**What This Document Is:**
- Requirements specification (MUST / MUST NOT statements)
- Verification criteria (what proves compliance)
- Fallback modes (when safeguards fail)

**What This Document Is NOT:**
- Implementation guide (no code, no architecture diagrams)
- Policy authoring (handling rules deferred to M1 implementation)
- UX specification (no player-facing behavior details)

---

## Safeguard 1: Read-Only Narration Context

### Requirement Statement

**REQ-LLM-SG-001:** During LLM narration generation, indexed memory MUST be provided as a **frozen snapshot** (read-only access).

### MUST Requirements

- ✅ **MUST** provide memory objects as immutable references during narration phase
- ✅ **MUST** prevent in-place modification of SessionLedgerEntry, EvidenceLedger, ThreadRegistry during narration
- ✅ **MUST** enforce read-only constraint at language/runtime level (not just policy)

### MUST NOT Requirements

- ❌ **MUST NOT** allow LLM narration code to mutate memory objects
- ❌ **MUST NOT** pass writable memory references to narration generation functions
- ❌ **MUST NOT** allow narration text to trigger memory writes without explicit validation

### Rationale (from RQ-LLM-002)

**Research Finding:** Scenario 4 (Write Barrier Enforcement) validated that LLM narration cannot mutate memory if access is read-only during narration phase.

**Risk if Violated:** Narration-to-memory leakage (CRITICAL FAILURE, determinism violated)

### Verification Criteria

**How to verify this safeguard exists:**

1. **Code Review Check:**
   - Narration generation functions receive `memory_snapshot: FrozenDict` (or equivalent immutable type)
   - No writable memory object references passed to LLM prompt builder
   - Memory object classes use `@dataclass(frozen=True)` or equivalent immutability enforcement

2. **Runtime Test:**
   - Attempt to mutate memory during narration → raises `FrozenInstanceError` or equivalent
   - Memory object hash before narration == Memory object hash after narration
   - No changes detected in SessionLedgerEntry.to_dict() before/after narration

3. **Acceptance Test:**
   - Generate 100 narrations for same memory state
   - Memory state unchanged after all 100 generations
   - Zero memory writes detected during narration phase

**Verification Success Criteria:** All 3 checks PASS → Safeguard verified

**Verification Failure Criteria:** ANY check FAILS → Safeguard NOT implemented, M1 narration BLOCKED

### Fallback Mode (if Safeguard Fails)

**Trigger:** If narration-to-memory write detected during testing

**Fallback Action:**
- **DISABLE** generative LLM narration entirely
- **REVERT** to template-based narration (M0 fallback mode)
- **FLAG** as critical failure (blocks M1 narration until fixed)

**Fallback Duration:** Until read-only enforcement implemented and verified

---

## Safeguard 2: Write-Through Validation (Event Sourcing Enforced)

### Requirement Statement

**REQ-LLM-SG-002:** All indexed memory updates MUST originate from **deterministic event log writes**, NOT from LLM narration extraction.

### MUST Requirements

- ✅ **MUST** route all memory writes through event log (event-sourced writes only)
- ✅ **MUST** validate all SessionLedgerEntry.facts_added entries trace to event log
- ✅ **MUST** reject memory writes that reference narration-only details (no event log provenance)

### MUST NOT Requirements

- ❌ **MUST NOT** extract facts from LLM narration text and auto-write to memory
- ❌ **MUST NOT** allow "soft writes" (narration-derived facts written without DM confirmation)
- ❌ **MUST NOT** treat narration text as source of truth (memory = ground truth)

### Rationale (from RQ-LLM-002)

**Research Finding:** Scenario 4 (Write Barrier Enforcement) validated that memory updates MUST be event-sourced to preserve determinism.

**Risk if Violated:** Creative bleed (presentation variance leaks into factual memory), soft retcon (narration contradicts memory)

### Verification Criteria

**How to verify this safeguard exists:**

1. **Code Review Check:**
   - All memory write functions require `event_id: str` parameter (no writes without event provenance)
   - Fact extraction pipeline validates against event log before write
   - No "narration → memory" code path exists (only "event → memory")

2. **Runtime Test:**
   - Generate narration with "creative" details (e.g., "goblin's arm severed")
   - Attempt to extract fact from narration → validation rejects (no event log entry for "arm severed")
   - Memory state unchanged after narration with creative details

3. **Acceptance Test:**
   - 100 narration generations with temperature=1.0 (high creativity)
   - Zero unauthorized memory writes detected
   - All memory writes traced to event log entries

**Verification Success Criteria:** All 3 checks PASS → Safeguard verified

**Verification Failure Criteria:** ANY unauthorized memory write detected → Safeguard NOT implemented, M1 narration BLOCKED

### Fallback Mode (if Safeguard Fails)

**Trigger:** If narration-derived fact written to memory without event log provenance

**Fallback Action:**
- **DISABLE** fact extraction from narration entirely
- **REQUIRE** manual DM confirmation for ALL memory updates (no auto-extraction)
- **FLAG** as high-severity failure (narration can continue, but no auto-memory updates)

**Fallback Duration:** Until write-through validation implemented and verified

---

## Safeguard 3: Temperature Isolation (Query vs Narration)

### Requirement Statement

**REQ-LLM-SG-003:** LLM sampling temperature MUST be **isolated** between query phase (deterministic recall) and narration phase (generative flexibility).

### MUST Requirements

- ✅ **MUST** use low temperature (≤0.5) for memory queries (factual retrieval)
- ✅ **MUST** use high temperature (≥0.7) for narration generation (generative text)
- ✅ **MUST** separate query phase (temperature ≤0.5) from narration phase (temperature ≥0.7)

### MUST NOT Requirements

- ❌ **MUST NOT** use high temperature (>0.7) for memory queries (non-deterministic recall risk)
- ❌ **MUST NOT** use same temperature for both query and narration
- ❌ **MUST NOT** allow narration temperature to affect factual retrieval accuracy

### Rationale (from RQ-LLM-002)

**Research Finding:** Scenario 3 (Temperature Variation) validated that low temperature preserves factual retrieval accuracy, high temperature enables generative narration.

**Risk if Violated:** Temperature-induced fact drift (query results vary with temperature, determinism compromised)

### Verification Criteria

**How to verify this safeguard exists:**

1. **Code Review Check:**
   - Memory query functions hardcode `temperature=0.3` (or lower)
   - Narration generation functions use `temperature=0.8` (or higher)
   - No shared temperature parameter between query and narration code paths

2. **Runtime Test:**
   - Execute 10 memory queries with same input → extract facts from all 10 responses
   - Factual content identical across all 10 queries (wording may vary slightly)
   - Execute 10 narrations with same input → wording varies significantly, facts identical

3. **Acceptance Test:**
   - Query same memory state 100 times at temperature=0.3 → 100% fact extraction accuracy
   - Generate 100 narrations at temperature=0.8 → high wording variance, 100% factual consistency

**Verification Success Criteria:** All 3 checks PASS → Safeguard verified

**Verification Failure Criteria:** Fact extraction accuracy <95% at low temperature → Safeguard NOT implemented, M1 narration BLOCKED

### Fallback Mode (if Safeguard Fails)

**Trigger:** If high-temperature queries produce <95% fact extraction accuracy

**Fallback Action:**
- **REDUCE** temperature for ALL LLM operations to 0.2 (near-deterministic)
- **DISABLE** high-temperature narration (all narration at temperature ≤0.3)
- **FLAG** as medium-severity failure (narration less generative but functional)

**Fallback Duration:** Until temperature isolation verified to preserve factual accuracy

---

## Safeguard 4: Paraphrase Detection & Validation

### Requirement Statement

**REQ-LLM-SG-004:** Facts extracted from LLM narration MUST be **validated against ground truth memory** before any memory write.

### MUST Requirements

- ✅ **MUST** validate all extracted facts against SessionLedgerEntry, EvidenceLedger, ThreadRegistry
- ✅ **MUST** reject facts that do NOT match any existing memory entry
- ✅ **MUST** log validation failures (hallucinated facts, contradictions)

### MUST NOT Requirements

- ❌ **MUST NOT** auto-write extracted facts without ground truth validation
- ❌ **MUST NOT** accept "creative interpretations" as facts (paraphrasing OK, invention NOT OK)
- ❌ **MUST NOT** allow accumulated paraphrase drift (query ground truth each turn, not prior narration)

### Rationale (from RQ-LLM-002)

**Research Finding:** Scenario 5 (Paraphrase Drift Accumulation) validated that querying ground truth each turn prevents drift, even after 50 turns.

**Risk if Violated:** Paraphrase drift (repeated paraphrasing mutates facts), query hallucination (LLM invents non-existent memory)

### Verification Criteria

**How to verify this safeguard exists:**

1. **Code Review Check:**
   - Fact extraction functions call `validate_fact_exists_in_memory(fact, memory_snapshot)` before write
   - Validation checks SessionLedgerEntry.facts_added, CharacterEvidenceEntry.description fields
   - Validation returns `True` (fact exists) or `False` (hallucinated fact)

2. **Runtime Test:**
   - Extract fact from narration: "Theron befriended Merchant Bob"
   - Validation checks memory → finds CharacterEvidenceEntry(character_id="theron", targets=["merchant_bob"])
   - Validation returns `True` → fact accepted
   - Extract hallucinated fact: "Theron betrayed the Duke"
   - Validation checks memory → NO matching evidence entry
   - Validation returns `False` → fact rejected, logged as hallucination

3. **Acceptance Test:**
   - 50-turn conversation with repeated memory queries
   - All queries retrieve ground truth memory (not prior narration)
   - Zero paraphrase drift detected (facts stable across 50 turns)

**Verification Success Criteria:** All 3 checks PASS → Safeguard verified

**Verification Failure Criteria:** Hallucination rate >5% → Safeguard NOT implemented, M1 narration BLOCKED

### Fallback Mode (if Safeguard Fails)

**Trigger:** If hallucination rate >5% (extracted facts not in memory)

**Fallback Action:**
- **DISABLE** fact extraction from narration entirely
- **REQUIRE** manual DM confirmation for ALL extracted facts
- **FLAG** as high-severity failure (narration continues, but no auto-fact-extraction)

**Fallback Duration:** Until paraphrase validation implemented and hallucination rate <5%

---

## Safeguard 5: Abstention Policy (Context Overflow Handling)

### Requirement Statement

**REQ-LLM-SG-005:** When indexed memory exceeds LLM context window, the system MUST **abstain** from answering (explicit "data unavailable" response), NOT invent facts.

### MUST Requirements

- ✅ **MUST** detect when memory size exceeds context window limit
- ✅ **MUST** truncate memory to fit context window (explicit truncation boundary)
- ✅ **MUST** provide abstention response when queried data unavailable (no invention)

### MUST NOT Requirements

- ❌ **MUST NOT** invent facts to fill context gaps
- ❌ **MUST NOT** "creatively summarize" missing sessions (invention risk)
- ❌ **MUST NOT** infer events from adjacent sessions (speculation forbidden)

### Rationale (from RQ-LLM-002)

**Research Finding:** Scenario 6 (Context Window Overflow) validated that abstention prevents invention risk when memory exceeds context window.

**Risk if Violated:** Query hallucination (LLM invents facts when data unavailable), determinism violated

### Verification Criteria

**How to verify this safeguard exists:**

1. **Code Review Check:**
   - Context builder checks memory size vs context window limit
   - If memory > context window → truncate and set `truncation_flag=True`
   - LLM prompt includes: "If data unavailable, respond: 'I don't have records for [X]. Please specify.'"

2. **Runtime Test:**
   - Load 130 KB memory (50 sessions) into 32 KB context window (overflow)
   - Query: "Recap Session 45"
   - If Session 45 in truncated portion → LLM responds "I don't have records for Session 45" (abstention)
   - If Session 45 in retained portion → LLM recaps Session 45 (normal)

3. **Acceptance Test:**
   - 50-session campaign, query all 50 sessions
   - Sessions 1-20 in context → LLM recaps successfully
   - Sessions 21-50 truncated → LLM abstains for all 30 sessions (zero invention)

**Verification Success Criteria:** All 3 checks PASS → Safeguard verified

**Verification Failure Criteria:** ANY invented fact detected during overflow condition → Safeguard NOT implemented, M1 narration BLOCKED

### Fallback Mode (if Safeguard Fails)

**Trigger:** If LLM invents facts when memory exceeds context window

**Fallback Action:**
- **REDUCE** context window to ensure ALL relevant memory fits (aggressive truncation)
- **DISABLE** speculative summarization entirely
- **FLAG** as critical failure (invention violates ground truth contract)

**Fallback Duration:** Until abstention policy enforced and zero invention detected

---

## Safeguard 6: Ground Truth Contract Enforcement

### Requirement Statement

**REQ-LLM-SG-006:** Indexed memory objects (SessionLedgerEntry, EvidenceLedger, ThreadRegistry) MUST remain the **canonical source of truth**; LLM narration is **derived presentation** only.

### MUST Requirements

- ✅ **MUST** treat indexed memory as ground truth (immutable during narration)
- ✅ **MUST** treat LLM narration as ephemeral presentation (no persistence without event sourcing)
- ✅ **MUST** enforce one-way flow: Memory → LLM (read-only), Event → Memory (write-only)

### MUST NOT Requirements

- ❌ **MUST NOT** treat narration text as source of truth
- ❌ **MUST NOT** query prior narration as memory (always query indexed memory objects)
- ❌ **MUST NOT** allow "soft authority" (narration overriding memory)

### Rationale (from RQ-LLM-001, RQ-LLM-002)

**Research Finding:** RQ-LLM-001 validated indexed memory as adequate substrate; RQ-LLM-002 validated separation boundaries (memory = deterministic, narration = generative).

**Risk if Violated:** Narrative overwrite (narration becomes source of truth), determinism compromised

### Verification Criteria

**How to verify this safeguard exists:**

1. **Code Review Check:**
   - Memory query functions receive `memory: MemorySnapshot` (indexed objects)
   - No code path queries prior narration text as source of facts
   - All queries read from SessionLedgerEntry, EvidenceLedger, ThreadRegistry (never from narration logs)

2. **Runtime Test:**
   - Generate 10 narrations for same event
   - Query memory 10 times (after each narration)
   - All 10 queries return same factual content (narration variance ignored)

3. **Acceptance Test:**
   - 100-turn conversation with narration generation
   - All memory queries return ground truth (indexed memory objects)
   - Zero queries reference narration text as source

**Verification Success Criteria:** All 3 checks PASS → Safeguard verified

**Verification Failure Criteria:** ANY query references narration text → Safeguard NOT implemented, M1 narration BLOCKED

### Fallback Mode (if Safeguard Fails)

**Trigger:** If narration text treated as source of truth (queried instead of indexed memory)

**Fallback Action:**
- **AUDIT** all query code paths → identify narration-as-source violations
- **REFACTOR** to enforce Memory → LLM flow (no reverse flow)
- **FLAG** as critical failure (determinism violated)

**Fallback Duration:** Until ground truth contract enforced in all query code paths

---

## Failure Modes & Triggers

### Failure Mode 1: Narration-to-Memory Write (CRITICAL)

**Description:** LLM narration writes back to indexed memory without event sourcing

**Detection:**
- Memory state changes after narration generation
- No corresponding event log entry
- Safeguard 1 (Read-Only Context) violated

**Trigger:** ANY narration-to-memory write detected

**Fallback:** DISABLE generative narration entirely (M0 template-based fallback)

**Severity:** 🔴 CRITICAL (blocks M1 narration until fixed)

---

### Failure Mode 2: Query Hallucination (CRITICAL)

**Description:** LLM invents facts not in indexed memory (responds with non-existent data)

**Detection:**
- Query result references non-existent session/event/entity
- Fact extraction produces entries not in memory
- Safeguard 4 (Paraphrase Validation) or Safeguard 5 (Abstention) violated

**Trigger:** Hallucination rate >5%

**Fallback:** REDUCE temperature to 0.2 (near-deterministic), DISABLE high-temperature queries

**Severity:** 🔴 CRITICAL (blocks M1 narration until fixed)

---

### Failure Mode 3: Soft Retcon via Paraphrase (MEDIUM)

**Description:** LLM paraphrasing contradicts prior memory entries (narrative inconsistency)

**Detection:**
- Paraphrase introduces contradiction not in memory
- Extracted fact conflicts with ground truth
- Safeguard 4 (Paraphrase Validation) detects contradiction

**Trigger:** Contradiction rate >10%

**Fallback:** ADD contradiction detection, REQUIRE DM review for flagged narrations

**Severity:** 🟡 MEDIUM (affects narrative consistency, not mechanical determinism)

---

### Failure Mode 4: Creative Bleed (MEDIUM)

**Description:** LLM narration invents mechanical effects not in event log (e.g., "goblin's arm severed" → adds "crippled" condition)

**Detection:**
- Narration adds mechanical effects not in event log
- Fact extraction produces hallucinated conditions
- Safeguard 2 (Write-Through Validation) rejects invented effect

**Trigger:** Creative bleed rate >10%

**Fallback:** REJECT all narration-derived mechanical effects, REQUIRE event log provenance

**Severity:** 🟡 MEDIUM (low frequency but high impact if undetected)

---

### Failure Mode 5: Temperature-Induced Drift (MEDIUM)

**Description:** High LLM temperature causes fact retrieval variance (non-deterministic recall)

**Detection:**
- Same query at different temperatures produces different fact counts
- Factual retrieval non-deterministic
- Safeguard 3 (Temperature Isolation) violated

**Trigger:** Fact extraction accuracy <95% at low temperature

**Fallback:** REDUCE temperature for ALL operations to 0.2

**Severity:** 🟡 MEDIUM (mitigable via temperature control)

---

## Verification Protocol (M1 Acceptance Gate)

### Pre-Integration Verification (Before M1 Narration Goes Live)

**Gate:** M1 narration integration BLOCKED until ALL 6 safeguards verified

**Verification Steps:**

1. **Code Review:** All 6 safeguards reviewed by Agent D (or M1 implementation lead)
2. **Unit Tests:** Each safeguard has ≥5 unit tests (verification criteria)
3. **Integration Tests:** 100-turn conversation test with all safeguards enabled
4. **Failure Mode Tests:** Each failure mode triggered deliberately, fallback verified

**Acceptance Criteria:**
- ✅ All 6 safeguards implemented (code review PASS)
- ✅ All unit tests PASS (≥30 tests total)
- ✅ Integration test PASS (100 turns, zero violations)
- ✅ All 5 failure modes trigger correct fallback

**Rejection Criteria:**
- ❌ ANY safeguard NOT implemented → M1 narration BLOCKED
- ❌ ANY failure mode does NOT trigger fallback → M1 narration BLOCKED
- ❌ Hallucination rate >5% → M1 narration BLOCKED
- ❌ Narration-to-memory write detected → M1 narration BLOCKED

---

### Post-Integration Monitoring (After M1 Narration Live)

**Continuous Monitoring:**

1. **Hallucination Rate:** Track fact extraction failures (target: <5%)
2. **Contradiction Rate:** Track paraphrase contradictions (target: <10%)
3. **Write Violations:** Track unauthorized memory writes (target: 0)
4. **Temperature Drift:** Track fact extraction accuracy at low temperature (target: >95%)
5. **Abstention Compliance:** Track invention during context overflow (target: 0)

**Alert Thresholds:**
- 🟡 **WARNING:** Hallucination rate >3% (approaching limit)
- 🔴 **CRITICAL:** Hallucination rate >5% (trigger fallback)
- 🔴 **CRITICAL:** ANY unauthorized memory write detected (trigger fallback)

**Fallback Decision:**
- If ANY critical threshold exceeded → DISABLE generative narration (M0 fallback)
- If 2+ warning thresholds exceeded → REDUCE temperature to 0.3 (degraded mode)

---

## Summary of M1 Requirements

### Critical Requirements (Blocks M1 if Not Satisfied)

| Req ID | Requirement | Verification | Fallback |
|--------|-------------|--------------|----------|
| **REQ-LLM-SG-001** | Read-Only Narration Context | Code review + runtime test | DISABLE narration |
| **REQ-LLM-SG-002** | Write-Through Validation | Code review + runtime test | DISABLE fact extraction |
| **REQ-LLM-SG-003** | Temperature Isolation | Code review + runtime test | REDUCE temperature to 0.2 |
| **REQ-LLM-SG-004** | Paraphrase Validation | Code review + runtime test | DISABLE fact extraction |
| **REQ-LLM-SG-005** | Abstention Policy | Code review + runtime test | DISABLE speculative summarization |
| **REQ-LLM-SG-006** | Ground Truth Contract | Code review + runtime test | AUDIT + REFACTOR |

### Acceptance Gate

**M1 Narration Integration GO/NO-GO:**

**GO Criteria (ALL must be satisfied):**
- ✅ All 6 safeguards implemented and verified
- ✅ All unit tests PASS (≥30 tests)
- ✅ Integration test PASS (100 turns, zero violations)
- ✅ All failure modes trigger correct fallback

**NO-GO Criteria (ANY triggers block):**
- ❌ ANY safeguard NOT verified
- ❌ Hallucination rate >5%
- ❌ ANY unauthorized memory write detected
- ❌ Temperature drift causes <95% accuracy

---

## References

- **RQ-LLM-001 Deliverable:** `docs/research/R1_INDEXED_MEMORY_STRESS_TEST.md` (memory substrate validation)
- **RQ-LLM-002 Deliverable:** `docs/research/R1_DETERMINISTIC_RECALL_VS_GENERATIVE.md` (deterministic recall + generative flexibility compatibility)
- **Determinism Contract:** `docs/research/R0_DETERMINISM_CONTRACT.md` (Layer 1/2/3 boundaries)
- **Decision Register:** `docs/research/R0_DECISION_REGISTER.md` (R0-DEC-049: RQ-LLM-001 PASSED)
- **Master Tracker:** `docs/research/R0_MASTER_TRACKER.md` (RQ-LLM-002 acceptance thresholds)

---

## Compliance Statement

**Agent A operated in PLANNING-ONLY mode:**
- ✅ NO production code written
- ✅ NO schema changes proposed
- ✅ NO policy authoring (handling rules deferred to M1)
- ✅ NO UX decisions (player-facing behavior deferred to M1)
- ✅ Requirements only (MUST / MUST NOT statements)

**Hard Constraints Observed:**
- ❌ NO implementation details (no code snippets, no architecture diagrams)
- ❌ NO solution design (requirements only)
- ❌ NO "how to implement" guidance (M1 implementation team decides approach)

**Reporting Line:** Agent D (Governance) → M1 Planning Lead

---

**END OF M1 PLANNING REQUIREMENTS**

**Date:** 2026-02-10
**Agent:** Agent A (LLM & Systems Architect)
**Phase:** M0 Planning Support
**Deliverable:** M1_LLM_SAFEGUARDS_REQUIREMENTS.md
**Status:** COMPLETE (awaiting M1 planning review)
**Authority:** PLANNING (non-binding until M1 kickoff approval)
