# M1 LLM Safeguard Architecture
## Design Specification for Deterministic Recall + Generative Narration

**Document Type:** Design / Architecture Specification
**Source Authority:** RQ-LLM-001 (R1_INDEXED_MEMORY_STRESS_TEST.md), RQ-LLM-002 (R1_DETERMINISTIC_RECALL_VS_GENERATIVE.md), M0_MASTER_PLAN.md
**Target Phase:** M1 (LLM Narration Integration)
**Date:** 2026-02-10
**Status:** DESIGN (Non-binding until M1 implementation approval)
**Agent:** Agent A (LLM & Systems Architect)

---

## Purpose

This document defines the **architectural placement, invariants, and verification gates** for safeguards that enable:
- **Deterministic recall** (mechanical outcomes replay-identical)
- **Generative flexibility** (narration text may vary)
- **No recall corruption** (presentation variance does not mutate memory)
- **No narrative drift** (paraphrasing does not accumulate errors)

**What This Document Defines:**
- Architectural placement (where safeguards live)
- Invariant definitions (what must always be true)
- Failure modes & responses (trigger → system action)
- Verification gates (how we know safeguards exist)

**What This Document Does NOT Define:**
- Implementation details (no code, no algorithms)
- Policy resolution (GAP-POL-01 through GAP-POL-04 remain unresolved)
- UX flows (no player-facing behavior)
- Data structures (no schema internals)

---

## 1. Safeguard Overview

### 1.1 Purpose of Safeguards

**Problem Statement:**
LLM narration is generative (non-deterministic text output), but mechanical outcomes MUST be deterministic (replay-identical). Without safeguards, narration variance can corrupt indexed memory, violating the determinism contract.

**Threat Model:**
1. **Narration-to-Memory Write:** LLM narration writes back to indexed memory without event sourcing (determinism violated)
2. **Query Hallucination:** LLM invents facts not in memory (ground truth contract violated)
3. **Soft Retcon:** LLM paraphrasing contradicts prior memory entries (narrative inconsistency)
4. **Creative Bleed:** LLM narration invents mechanical effects not in event log (determinism leaked)
5. **Temperature Drift:** High LLM temperature causes fact retrieval variance (non-deterministic recall)

**Safeguard Objective:**
Enforce **separation boundaries** such that:
- Indexed memory = deterministic, immutable source of truth
- LLM narration = generative, ephemeral presentation layer
- One-way flow: Memory → LLM (read-only), Event → Memory (write-only)

---

### 1.2 Threats Mitigated

| Threat | Severity | Mitigation Safeguard |
|--------|----------|----------------------|
| **Narration-to-Memory Write** | 🔴 CRITICAL | Safeguard 1 (Read-Only Narration Context) |
| **Query Hallucination** | 🔴 CRITICAL | Safeguard 4 (Paraphrase Validation), Safeguard 5 (Abstention) |
| **Soft Retcon via Paraphrase** | 🟡 MEDIUM | Safeguard 4 (Paraphrase Validation) |
| **Creative Bleed** | 🟡 MEDIUM | Safeguard 2 (Write-Through Validation) |
| **Temperature-Induced Drift** | 🟡 MEDIUM | Safeguard 3 (Temperature Isolation) |

---

## 2. Safeguard Inventory

### Safeguard 1: Read-Only Narration Context

**Invariant:** Indexed memory objects MUST NOT be modifiable during LLM narration generation.

**Architectural Guarantee:** Memory objects provided to narration layer are **immutable references** (frozen snapshots).

**Threat Mitigated:** Narration-to-Memory Write (🔴 CRITICAL)

**Failure Response:** If narration writes to memory → DISABLE generative narration (M0 fallback)

---

### Safeguard 2: Write-Through Validation (Event Sourcing Enforced)

**Invariant:** All indexed memory updates MUST originate from deterministic event log writes, NOT from LLM narration extraction.

**Architectural Guarantee:** Memory write functions require event provenance (no writes without event_id).

**Threat Mitigated:** Creative Bleed (🟡 MEDIUM)

**Failure Response:** If narration-derived fact written to memory → DISABLE fact extraction, REQUIRE manual DM confirmation

---

### Safeguard 3: Temperature Isolation (Query vs Narration)

**Invariant:** LLM sampling temperature MUST be isolated between query phase (low temp, deterministic) and narration phase (high temp, generative).

**Architectural Guarantee:** Query functions use temperature ≤0.5, narration functions use temperature ≥0.7 (separate code paths).

**Threat Mitigated:** Temperature-Induced Drift (🟡 MEDIUM)

**Failure Response:** If fact extraction accuracy <95% at low temp → REDUCE all operations to temp=0.2

---

### Safeguard 4: Paraphrase Detection & Validation

**Invariant:** Facts extracted from LLM narration MUST be validated against ground truth memory before any memory write.

**Architectural Guarantee:** Fact extraction pipeline validates all extracted facts against SessionLedgerEntry, EvidenceLedger, ThreadRegistry (provenance check).

**Threat Mitigated:** Soft Retcon via Paraphrase (🟡 MEDIUM), Query Hallucination (🔴 CRITICAL)

**Failure Response:** If hallucination rate >5% → DISABLE fact extraction, REQUIRE manual DM confirmation

---

### Safeguard 5: Abstention Policy (Context Overflow Handling)

**Invariant:** When indexed memory exceeds LLM context window, the system MUST abstain from answering (explicit "data unavailable" response), NOT invent facts.

**Architectural Guarantee:** Context builder detects overflow, truncates memory, provides abstention response when queried data unavailable.

**Threat Mitigated:** Query Hallucination (🔴 CRITICAL)

**Failure Response:** If invention detected during overflow → AGGRESSIVE truncation, DISABLE speculative summarization

---

### Safeguard 6: Ground Truth Contract Enforcement

**Invariant:** Indexed memory objects (SessionLedgerEntry, EvidenceLedger, ThreadRegistry) MUST remain the canonical source of truth; LLM narration is derived presentation only.

**Architectural Guarantee:** Memory query functions ALWAYS read indexed memory objects (never prior narration text).

**Threat Mitigated:** Narrative Overwrite (narration becomes source of truth)

**Failure Response:** If narration text treated as source of truth → AUDIT + REFACTOR all query code paths

---

## 3. Architectural Placement

### 3.1 System Layer Decomposition

```
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         LLM Narration Generation                    │   │
│  │  (Generative, High Temperature ≥0.7)                │   │
│  │                                                       │   │
│  │  INPUT: Memory Snapshot (Frozen, Read-Only)         │   │
│  │  OUTPUT: Narration Text (Ephemeral)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ (Read-Only Access)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      MEMORY QUERY LAYER                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Memory Query Functions                      │   │
│  │  (Deterministic, Low Temperature ≤0.5)              │   │
│  │                                                       │   │
│  │  INPUT: Query Text + Memory Snapshot                │   │
│  │  OUTPUT: Factual Retrieval (Validated)              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ (Read-Only Access)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    INDEXED MEMORY LAYER                      │
│                        (Ground Truth)                         │
│                                                               │
│  ┌────────────────┬────────────────┬────────────────┐      │
│  │ SessionLedger  │ EvidenceLedger │ ThreadRegistry │      │
│  │    Entry       │                 │                 │      │
│  └────────────────┴────────────────┴────────────────┘      │
│                                                               │
│  INVARIANT: Immutable during narration/query phases         │
│  UPDATES: Event-sourced writes ONLY                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ (Write-Only, Event-Sourced)
                              │
┌─────────────────────────────────────────────────────────────┐
│                      EVENT SOURCING LAYER                    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Event Log Writer                            │   │
│  │  (Deterministic, Append-Only)                       │   │
│  │                                                       │   │
│  │  INPUT: Event (deterministic)                       │   │
│  │  OUTPUT: Memory Update (via Event → Memory)        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.2 Safeguard Placement by Layer

| Safeguard | Layer | Access Mode | Enforcement Point |
|-----------|-------|-------------|-------------------|
| **Safeguard 1 (Read-Only Context)** | Presentation ↔ Memory | Read-Only | Memory snapshot creation (freeze objects) |
| **Safeguard 2 (Write-Through Validation)** | Event Sourcing → Memory | Write-Only | Memory write functions (require event_id) |
| **Safeguard 3 (Temperature Isolation)** | Query Layer vs Presentation Layer | N/A | Function-level temperature parameter |
| **Safeguard 4 (Paraphrase Validation)** | Presentation → Memory | Write-Validation | Fact extraction pipeline (validate before write) |
| **Safeguard 5 (Abstention)** | Query Layer | Read-Only | Context builder (detect overflow, provide abstention) |
| **Safeguard 6 (Ground Truth Contract)** | All Layers | Read-Only (Query/Narration) | Query functions (always read indexed memory) |

---

### 3.3 Component Responsibilities

#### Indexed Memory Layer (Ground Truth)
**Responsibilities:**
- Store SessionLedgerEntry, EvidenceLedger, ThreadRegistry
- Provide immutable snapshots to query/narration layers
- Accept write-only updates from event sourcing layer

**MUST:**
- Be immutable during query/narration phases
- Enforce deterministic ordering (sorted by canonical IDs)
- Serialize/deserialize via to_dict/from_dict (JSON-compatible)

**MUST NOT:**
- Accept writes from query/narration layers directly
- Allow in-place mutations during read operations
- Treat narration text as source of truth

---

#### Memory Query Layer
**Responsibilities:**
- Query indexed memory using low-temperature LLM (≤0.5)
- Extract factual content from memory objects
- Provide abstention when data unavailable

**MUST:**
- Use temperature ≤0.5 (deterministic-ish retrieval)
- Query indexed memory objects (never narration text)
- Abstain when memory exceeds context window

**MUST NOT:**
- Use high temperature (>0.7) for queries
- Invent facts when data unavailable
- Write to indexed memory

---

#### Presentation Layer (Narration Generation)
**Responsibilities:**
- Generate narration text using high-temperature LLM (≥0.7)
- Accept memory snapshot (frozen, read-only)
- Produce ephemeral narration (no persistence)

**MUST:**
- Use temperature ≥0.7 (generative flexibility)
- Receive memory snapshot as immutable reference
- Produce ephemeral output (no automatic writes)

**MUST NOT:**
- Mutate memory objects during narration
- Auto-write extracted facts to memory (without validation)
- Treat narration text as source of truth

---

#### Event Sourcing Layer
**Responsibilities:**
- Accept deterministic events (from engine)
- Write events to append-only log
- Update indexed memory via event → memory translation

**MUST:**
- Enforce event-sourced writes (all memory updates via events)
- Validate event provenance (event_id required)
- Maintain append-only log (no in-place mutations)

**MUST NOT:**
- Accept narration-derived writes (no narration → memory path)
- Allow memory updates without event_id
- Permit in-place event log edits

---

## 4. Invariant Definitions

### 4.1 MUST Invariants (Always True)

**INV-001: Memory Immutability During Read**
- **Statement:** Indexed memory objects MUST NOT change during query/narration phases.
- **Enforcement:** Memory snapshot frozen before passing to query/narration layers.
- **Verification:** Memory object hash before operation == Memory object hash after operation.

**INV-002: Event Sourcing for All Writes**
- **Statement:** All indexed memory updates MUST originate from event log writes.
- **Enforcement:** Memory write functions require event_id parameter.
- **Verification:** All SessionLedgerEntry.facts_added trace to event log entries.

**INV-003: Temperature Isolation**
- **Statement:** Query functions use temperature ≤0.5, narration functions use temperature ≥0.7.
- **Enforcement:** Separate code paths for query vs narration (no shared temperature parameter).
- **Verification:** Code review confirms temperature hardcoded in function signatures.

**INV-004: Fact Validation Before Write**
- **Statement:** Facts extracted from narration MUST validate against ground truth before write.
- **Enforcement:** Fact extraction pipeline calls validate_fact_exists_in_memory().
- **Verification:** Hallucination rate <5% (facts rejected when not in memory).

**INV-005: Abstention on Context Overflow**
- **Statement:** When memory exceeds context window, system MUST abstain (not invent).
- **Enforcement:** Context builder detects overflow, provides abstention response.
- **Verification:** Zero invented facts during overflow condition.

**INV-006: Ground Truth Query Source**
- **Statement:** All queries MUST read indexed memory objects (never narration text).
- **Enforcement:** Query functions receive memory snapshot (indexed objects only).
- **Verification:** Code review confirms no query paths reference narration logs.

---

### 4.2 MUST NOT Invariants (Never Allowed)

**INV-NEG-001: Narration-to-Memory Write**
- **Statement:** LLM narration MUST NOT write to indexed memory.
- **Enforcement:** Read-only memory snapshot during narration.
- **Verification:** Zero memory writes detected during narration phase.

**INV-NEG-002: High-Temperature Queries**
- **Statement:** Query functions MUST NOT use temperature >0.7.
- **Enforcement:** Query functions hardcode temperature ≤0.5.
- **Verification:** Code review confirms no high-temp queries.

**INV-NEG-003: Fact Invention on Overflow**
- **Statement:** System MUST NOT invent facts when memory unavailable.
- **Enforcement:** Abstention policy enforced by context builder.
- **Verification:** Zero invention detected during overflow tests.

**INV-NEG-004: Narration as Source of Truth**
- **Statement:** Query functions MUST NOT treat narration text as source of truth.
- **Enforcement:** Query functions always read indexed memory objects.
- **Verification:** Code review confirms indexed memory is canonical source.

**INV-NEG-005: Unvalidated Memory Writes**
- **Statement:** Memory writes MUST NOT occur without event provenance or fact validation.
- **Enforcement:** Write-through validation + paraphrase validation.
- **Verification:** All writes traced to event log, all extracted facts validated.

---

## 5. Failure Modes & Responses

### 5.1 Failure Mode 1: Narration-to-Memory Write (CRITICAL)

**Trigger:** Memory state changes after narration generation (no event log entry).

**Detection:**
- Memory object hash changes during narration phase
- Memory write detected without event_id
- Safeguard 1 (Read-Only Context) violated

**System Response:**
1. **Immediate:** HALT narration generation, LOG violation
2. **Fallback:** DISABLE generative LLM narration entirely
3. **Revert:** Restore memory snapshot to pre-narration state
4. **Mode:** M0 template-based narration (fallback)
5. **Resolution:** Read-only enforcement implemented and verified

**Degradation Path:** Generative narration → Template narration → No narration (halt)

**Severity:** 🔴 CRITICAL (blocks M1 narration until fixed)

---

### 5.2 Failure Mode 2: Query Hallucination (CRITICAL)

**Trigger:** LLM invents facts not in indexed memory (hallucination rate >5%).

**Detection:**
- Query result references non-existent session/event/entity
- Fact extraction produces entries not in memory
- Safeguard 4 (Paraphrase Validation) or Safeguard 5 (Abstention) violated

**System Response:**
1. **Immediate:** HALT query, LOG hallucination
2. **Fallback:** REDUCE temperature to 0.2 (near-deterministic)
3. **Mode:** Low-temp queries only (high-temp narration disabled)
4. **Resolution:** Abstention policy enforced, hallucination rate <5%

**Degradation Path:** High-temp queries → Low-temp queries → Template-based queries (halt)

**Severity:** 🔴 CRITICAL (blocks M1 narration until fixed)

---

### 5.3 Failure Mode 3: Soft Retcon via Paraphrase (MEDIUM)

**Trigger:** LLM paraphrasing contradicts prior memory entries (contradiction rate >10%).

**Detection:**
- Paraphrase introduces contradiction not in memory
- Extracted fact conflicts with ground truth
- Safeguard 4 (Paraphrase Validation) detects contradiction

**System Response:**
1. **Immediate:** LOG contradiction, FLAG for DM review
2. **Fallback:** ADD contradiction detection layer
3. **Mode:** DM review required for flagged narrations
4. **Resolution:** Contradiction rate <10%

**Degradation Path:** Auto-narration → DM-reviewed narration → Manual narration (halt)

**Severity:** 🟡 MEDIUM (affects narrative consistency, not mechanical determinism)

---

### 5.4 Failure Mode 4: Creative Bleed (MEDIUM)

**Trigger:** LLM narration invents mechanical effects not in event log (creative bleed rate >10%).

**Detection:**
- Narration adds mechanical effects not in event log
- Fact extraction produces hallucinated conditions
- Safeguard 2 (Write-Through Validation) rejects invented effect

**System Response:**
1. **Immediate:** REJECT narration-derived effect, LOG violation
2. **Fallback:** DISABLE fact extraction from narration
3. **Mode:** Manual DM confirmation for all memory updates
4. **Resolution:** Write-through validation enforced, creative bleed rate <10%

**Degradation Path:** Auto-extraction → Manual extraction → No extraction (halt)

**Severity:** 🟡 MEDIUM (low frequency but high impact if undetected)

---

### 5.5 Failure Mode 5: Temperature-Induced Drift (MEDIUM)

**Trigger:** High LLM temperature causes fact retrieval variance (accuracy <95%).

**Detection:**
- Same query at different temperatures produces different fact counts
- Factual retrieval non-deterministic
- Safeguard 3 (Temperature Isolation) violated

**System Response:**
1. **Immediate:** LOG variance, FLAG temperature violation
2. **Fallback:** REDUCE temperature for ALL operations to 0.2
3. **Mode:** Near-deterministic (low-variance) narration
4. **Resolution:** Temperature isolation verified, accuracy >95%

**Degradation Path:** High-temp narration → Low-temp narration → Template narration (halt)

**Severity:** 🟡 MEDIUM (mitigable via temperature control)

---

## 6. Verification Gates

### 6.1 Pre-Integration Verification (M1 Entry Gate)

**Gate:** M1 narration integration BLOCKED until ALL 6 safeguards verified.

| Safeguard | Verification Method | Pass Criteria | Failure Action |
|-----------|---------------------|---------------|----------------|
| **SG-1: Read-Only Context** | Code review + runtime test | Memory hash unchanged after narration | BLOCK M1 integration |
| **SG-2: Write-Through Validation** | Code review + runtime test | All writes traced to event log | BLOCK M1 integration |
| **SG-3: Temperature Isolation** | Code review + runtime test | Query temp ≤0.5, narration temp ≥0.7 | BLOCK M1 integration |
| **SG-4: Paraphrase Validation** | Code review + runtime test | Hallucination rate <5% | BLOCK M1 integration |
| **SG-5: Abstention Policy** | Code review + runtime test | Zero invention during overflow | BLOCK M1 integration |
| **SG-6: Ground Truth Contract** | Code review + runtime test | All queries read indexed memory | BLOCK M1 integration |

**Verification Protocol:**
1. **Code Review:** Each safeguard reviewed by M1 implementation lead
2. **Unit Tests:** Each safeguard has ≥5 unit tests (30 tests total minimum)
3. **Integration Test:** 100-turn conversation with all safeguards enabled
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

### 6.2 Post-Integration Monitoring (M1 Operation)

**Continuous Monitoring:**

| Metric | Target | Warning Threshold | Critical Threshold | Response |
|--------|--------|-------------------|---------------------|----------|
| **Hallucination Rate** | <5% | >3% | >5% | REDUCE temp to 0.2 |
| **Contradiction Rate** | <10% | >8% | >10% | REQUIRE DM review |
| **Write Violations** | 0 | 0 | ANY | DISABLE narration |
| **Temperature Drift** | Accuracy >95% | <97% | <95% | REDUCE temp to 0.3 |
| **Abstention Compliance** | 0 invention | 0 | ANY | DISABLE speculative summarization |

**Alert Protocol:**
- 🟡 **WARNING:** Metric approaching threshold (log, monitor)
- 🔴 **CRITICAL:** Metric exceeds threshold (trigger fallback)

**Fallback Decision Tree:**
```
IF ANY critical threshold exceeded:
  → DISABLE generative narration (M0 fallback)
ELSE IF 2+ warning thresholds exceeded:
  → REDUCE temperature to 0.3 (degraded mode)
ELSE:
  → CONTINUE monitoring (operational)
```

---

## 7. Explicit Non-Goals

### 7.1 What This Architecture Does NOT Solve

**Policy Gaps (Deferred to M1 Policy Phase):**
- ❌ **GAP-POL-01:** Cache invalidation strategy (when/how to invalidate memory cache)
- ❌ **GAP-POL-02:** Entity rename propagation (how renames propagate through memory)
- ❌ **GAP-POL-03:** Deleted entity handling (soft delete vs tombstone vs cascade)
- ❌ **GAP-POL-04:** Multilingual alias resolution (language detection, disambiguation)

**Implementation Details (Deferred to M1 Implementation):**
- ❌ **Code:** No code snippets, algorithms, or data structures defined
- ❌ **APIs:** No function signatures, parameters, or return types specified
- ❌ **Storage:** No database schema, file formats, or serialization details
- ❌ **Testing:** No test cases, benchmarks, or validation scripts provided

**UX Decisions (Deferred to M1 UX Phase):**
- ❌ **Player-Facing Behavior:** No error messages, prompts, or interaction flows
- ❌ **DM Interface:** No controls, settings, or override mechanisms
- ❌ **Abstention Wording:** No specific phrasing for "data unavailable" responses

**Scope Boundaries (Out of M1):**
- ❌ **RAG System:** No vector DB, semantic search, or retrieval augmentation
- ❌ **Model Selection:** No LLM model choice, quantization, or hardware allocation
- ❌ **Performance Tuning:** No latency optimization, caching strategies, or batching

---

### 7.2 Dependencies on External Work

**Blocked on RQ-LLM-003 through RQ-LLM-012 (Not Yet Resolved):**
- Entity renames in indexed memory (RQ-LLM-003)
- Deleted entity handling (RQ-LLM-004)
- Entity ID aliasing (RQ-LLM-005)
- LLM constraint adherence (RQ-LLM-006)
- Session recap summarization (RQ-LLM-008)

**Blocked on M1 Policy Phase (GAP-POL Resolution):**
- Contradiction resolution policy (GAP-POL-01)
- Retcon handling policy (GAP-POL-02)
- Bounded growth/pruning policy (GAP-POL-03)
- Abstention policy details (GAP-POL-04)

**Blocked on M1 Implementation (Code Not Yet Written):**
- Memory snapshot creation (immutability enforcement)
- Fact extraction pipeline (validation logic)
- Context builder (overflow detection)
- Temperature enforcement (function-level control)

---

## 8. Validation Checklist (Self-Audit)

**Agent A Self-Audit:**

- ✅ **No implementation language:** No code snippets, algorithms, or data structures defined
- ✅ **No policy authoring:** GAP-POL-01 through GAP-POL-04 remain unresolved
- ✅ **No UX decisions:** No player-facing behavior, error messages, or prompts
- ✅ **Uses MUST / MUST NOT correctly:** Invariants defined with clear enforcement
- ✅ **Aligns with M0_MASTER_PLAN.md:** All binding inputs (RQ-LLM-001, RQ-LLM-002) respected
- ✅ **Architecture only:** Placement, invariants, failure modes, verification gates (no "how")
- ✅ **No schema changes:** No modifications to campaign_memory.py or canonical_ids.py
- ✅ **No implementation readiness:** No code, no timelines, no sprint planning

**Hard Constraints Observed:**
- ❌ NO code written (architecture specification only)
- ❌ NO policy authored (handling rules deferred)
- ❌ NO UX designed (player-facing behavior deferred)
- ❌ NO schemas modified (data structures unchanged)

---

## 9. References

- **RQ-LLM-001 Deliverable:** `docs/research/R1_INDEXED_MEMORY_STRESS_TEST.md` (memory substrate validation)
- **RQ-LLM-002 Deliverable:** `docs/research/R1_DETERMINISTIC_RECALL_VS_GENERATIVE.md` (deterministic recall + generative flexibility)
- **M0 Master Plan:** `docs/planning/M0_MASTER_PLAN.md` (binding inputs, scope boundaries)
- **M1 Requirements:** `docs/planning/M1_LLM_SAFEGUARDS_REQUIREMENTS.md` (requirements specification)
- **Determinism Contract:** `docs/research/R0_DETERMINISM_CONTRACT.md` (Layer 1/2/3 boundaries)
- **Decision Register:** `docs/research/R0_DECISION_REGISTER.md` (R0-DEC-049: RQ-LLM-001 PASSED)

---

## 10. Compliance Statement

**Agent A operated in DESIGN-ONLY mode:**
- ✅ NO production code written
- ✅ NO schema changes proposed
- ✅ NO policy authoring (GAP-POL items deferred)
- ✅ NO UX decisions (player-facing behavior deferred)
- ✅ Architecture specification only (placement, invariants, verification)

**Hard Constraints Observed:**
- ❌ NO implementation details (no code, no algorithms, no APIs)
- ❌ NO "how to build" guidance (M1 implementation team decides approach)
- ❌ NO schema changes (indexed memory schemas unchanged)

**Reporting Line:** Agent D (Governance) → PM (Thunder)

---

**END OF M1 SAFEGUARD ARCHITECTURE**

**Date:** 2026-02-10
**Agent:** Agent A (LLM & Systems Architect)
**Phase:** M1-Prep (Design-Only)
**Deliverable:** M1_LLM_SAFEGUARD_ARCHITECTURE.md
**Status:** COMPLETE (awaiting PM review)
**Authority:** DESIGN (non-binding until M1 implementation approval)
