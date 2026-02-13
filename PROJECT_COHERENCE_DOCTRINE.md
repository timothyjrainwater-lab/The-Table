# Project Coherence Doctrine

> **SCOPE CLARIFICATION ADDENDUM (2026-02-13, WO-AUDIT-007)**
>
> This doctrine was written in Feb 2025 (CP-07D) when the project had 1,225 tests
> and no immersion adapter implementations. Several specific claims have been updated:
>
> 1. **"Production Voice Integration" scope clarified (2026-02-13, WO-AUDIT-007).**
>    The M3 Immersion Layer delivered STT, TTS, Image, and AudioMixer adapters with
>    Protocol-based interfaces, stub defaults, and real backend wiring (Kokoro TTS,
>    Whisper STT, SDXL Image). These adapters are non-authoritative (they cannot
>    mutate WorldState or affect deterministic replay) and are governed by
>    `docs/IMMERSION_BOUNDARY.md`. The Scope Boundaries section has been updated:
>    voice pipeline integration (STT→intent, narration→TTS) is In Scope (M3);
>    voice model training / custom voice synthesis remains Out of Scope.
>
> 2. **Test Runtime Invariant (Section 3) — RE-BASELINED (2026-02-13, WO-AUDIT-007).**
>    The original "<5 seconds" target was set at ~1,200 tests. The suite has grown
>    to 5,254+ tests. Section 3 now reads: "<25ms average per test AND <120s total
>    for full suite." The original 4ms/test enforcement threshold is superseded.
>
> 3. **Current Status line in Section 3 updated (2026-02-13, WO-AUDIT-007).** Now
>    reads "5,254+ tests." For current counts, see `PROJECT_STATE_DIGEST.md`.
>
> **The core architectural principles (Sections 1-8) remain binding.** The scope
> boundaries should be read in light of the addendum above.
>
> **For current project state, see:** `PROJECT_STATE_DIGEST.md`
> **For document precedence, see:** `docs/CURRENT_CANON.md`

**Last Updated**: 2026-02-13 (WO-AUDIT-007)
**Status**: Locked (Project Governance)

## Purpose

This document defines the **canonical scope boundaries** and **architectural constraints** for the AIDM project. It resolves contradictions between README.md and PROJECT_STATE_DIGEST.md and locks the project's scope story.

All instruction packets must conform to this doctrine. Deviations require explicit documentation and rationale.

## Core Architectural Principles

### 1. No LLM Dependency in Deterministic Runtime

**Rule**: The deterministic gameplay runtime MUST NOT depend on LLM inference.

**Rationale**: LLMs are non-deterministic and break replay guarantees.

**Allowed**:
- LLMs in **prep phase** as untrusted generators (scene creation, NPC generation, narration drafts)
- LLM outputs MUST be gated by fail-closed validators before entering bundles
- LLM-generated content stored as static data in bundles (becomes deterministic input)

**Forbidden**:
- LLM inference during gameplay/replay
- LLM-based rule interpretation at runtime
- LLM-based tactical decisions at runtime

### 2. Campaign Continuity Records Are Allowed

**Rule**: Campaign-scale memory and continuity tracking are **in scope**.

**Rationale**: Session ledgers, evidence tracking, and mystery threads are data structures, not "campaign management workflows."

**Allowed**:
- Session ledger entries (session summaries, facts, state changes)
- Character evidence ledger (behavioral evidence, alignment data)
- Mystery investigation tracking (clue cards, thread registry)
- Campaign bundles with continuity data

**Forbidden**:
- Campaign planning UI (scheduling, calendar, session prep workflows)
- Campaign wiki/knowledge base UI
- Campaign management tools (player roster, XP tracking UI)

**Boundary**: Data structures YES, UI workflows NO.

### 3. Test Runtime Invariant

**Rule**: Full test suite MUST complete in **<25ms average per test AND <120s total for full suite** (re-baselined 2026-02-13 at 5,254 tests; original <5s target was set at ~1,200 tests).

**Rationale**: Fast tests enable rapid iteration and prevent test suite bloat.
The threshold scales with test count: original 435 tests at ~1.5s → ~3.4ms/test.

**Enforcement**:
- Monitor test runtime in CI
- Reject patches that slow per-test average above 25ms
- Use mocking/stubbing for slow external dependencies
- Keep unit tests focused and isolated

**Current Status**: 5,254+ tests ✅

### 4. Deterministic Hashing (Not Cryptographic)

**Rule**: Use **stable hashing** for deterministic state snapshots, not cryptographic hashing.

**Rationale**: "Cryptographic hashing" implies security properties (collision resistance, preimage resistance) that are not relevant to gameplay determinism.

**Correct Terminology**:
- ✅ "Stable hashing" / "Deterministic hashing"
- ✅ "Content-based hash for replay verification"
- ❌ "Cryptographic hashing" (unless specifying algorithm + security property)

**Implementation**: Use hash functions (SHA256, MD5) for **content addressing only**, not security.

### 5. Fail-Closed Design

**Rule**: Unknown types, missing fields, and invalid inputs MUST cause **explicit errors**.

**Rationale**: Silent fallbacks hide bugs and break determinism.

**Enforcement**:
- All enum types validated in `__post_init__`
- Unknown intent types rejected by legality checker
- Bundle validator blocks unknown fields/types
- No default values for required semantic fields

### 6. Provenance & Citations First-Class

**Rule**: All rulings MUST support citations to source material.

**Rationale**: Auditability and transparency are core design goals.

**Enforcement**:
- Citation schema available in all events
- Rule lookup returns page-level results with snippets
- Validators check citation format (12-char hex sourceId)
- Doctrine metadata requires MM page references

### 7. Event Sourcing as Single Source of Truth

**Rule**: All state mutations MUST flow through the event log.

**Rationale**: Replay guarantees require append-only log as authority.

**Enforcement**:
- State mutations only through replay runner's single reducer
- No direct WorldState mutation outside reducer
- Event IDs strictly monotonic
- JSONL format for git-friendly diffs

### 8. Data-Only Schemas First

**Rule**: Define contracts and validation **before** implementing algorithms.

**Rationale**: Schemas define the interface; algorithms can be swapped without breaking contracts.

**Pattern**:
1. Write schema module (`aidm/schemas/`)
2. Write schema tests (validation, serialization, roundtrips)
3. Integrate schema into bundles (if applicable)
4. Extend bundle validator (if applicable)
5. **THEN** implement algorithms/engines that use schema

## Scope Boundaries (Locked)

### In Scope

✅ **Deterministic Gameplay Runtime**:
- Event sourcing, replay, RNG management
- Rule lookup (page-level retrieval)
- Intent validation and interaction engine
- Tactical policy evaluation (deterministic heuristics)
- Time tracking, deadlines, durations
- Hazard tracking, visibility, terrain contracts

✅ **Session Prep Bundles**:
- Scene cards, NPC cards, encounter specs
- Monster doctrine metadata
- Pre-validated assets and citations
- Readiness certification

✅ **Campaign Continuity Records**:
- Session ledger (summaries, facts, state changes)
- Character evidence ledger (behavioral tracking)
- Mystery investigation (clue cards, thread registry)

✅ **Source Layer**:
- Page-level text extraction
- Provenance metadata (647 sources)
- Citation generation
- Keyword-based rule lookup

✅ **Voice-First Contracts**:
- Structured intent schemas (not free-form NLU)
- Declare→Point→Confirm interaction pattern
- Grid coordinates for targeting

✅ **Voice Pipeline Integration (M3 Immersion Layer)**:
- STT→intent pipeline (Whisper STT → structured intents)
- Narration→TTS pipeline (Kokoro TTS)
- Protocol-based adapter interfaces with stub defaults
- Non-authoritative: cannot mutate WorldState or affect deterministic replay
- Governed by `docs/IMMERSION_BOUNDARY.md`

### Out of Scope

❌ **Campaign Planning UI/Workflows**:
- Session scheduling, calendar tools
- Player roster management UI
- XP tracking UI, inventory UI
- Campaign wiki UI

❌ **LLM Runtime Integration**:
- LLM inference during gameplay
- LLM-based rule interpretation at runtime
- LLM-based tactical decisions at runtime

❌ **Real-Time Optimization**:
- System optimizes for correctness, not speed
- No sub-millisecond latency requirements

❌ **NLP/Semantic Search**:
- Current search is keyword-based (token counting)
- No embeddings, no ranking models

❌ **Rule Interpretation Engine**:
- System retrieves text, doesn't parse/interpret rules
- Human DM or future LLM prep layer interprets rules

❌ **Voice Model Training / Custom Voice Synthesis**:
- Training custom voice models
- Fine-tuning TTS voices
- Custom ASR model development

❌ **UI Implementation**:
- Contracts defined (grid points, intents)
- No actual UI rendering or input handling

## Test Suite Philosophy

### Tests Are Executable Specification

**Rule**: Tests define system behavior. Code implements what tests specify.

**Corollary**: If tests don't verify it, it's not guaranteed.

### Test Organization

1. **Unit Tests**: Schema validation, core functions, isolated behavior
2. **Integration Tests**: Multi-module workflows (e.g., bundle validation)
3. **Roundtrip Tests**: Serialization → deserialization identity
4. **Determinism Tests**: Multiple runs produce identical results

### Test Naming Convention

```python
def test_<subject>_<scenario>():
    """<Subject> should <expected behavior>."""
```

Examples:
- `test_rules_question_empty_text_rejected()`
- `test_ruling_decision_citations_sorted()`

## Instruction Packet Protocol

### Packet Structure

All instruction packets MUST include:

1. **Packet ID**: CP-XX format
2. **Goal**: One-sentence objective
3. **Scope**: In scope / Out of scope sections
4. **Tasks**: Numbered task list with acceptance criteria
5. **Completion Summary Requirements**: Template for completion

### Completion Summary

Every packet completion MUST include:

1. **Packet ID** (CP-XX)
2. **Tasks completed** (all tasks from packet)
3. **Files changed** (new/modified modules and tests)
4. **Tests affected** (count change, e.g., 385 → 435)
5. **PSD update block** (exact text for PROJECT_STATE_DIGEST.md)

### Coordination Files

**Authoritative** (single source of truth):
- `PROJECT_STATE_DIGEST.md`: Canonical state snapshot (updated every packet)
- `README.md`: User-facing documentation
- Test suite: Executable specification
- Source code: Ground truth

**Reference Only** (not authoritative):
- AUDIT_REPORT.md, REUSE_DECISION.json, etc.

## Enforcement

### Who Enforces This Doctrine?

1. **Instruction packet authors**: Must conform to scope boundaries
2. **Code reviewers**: Verify adherence before merge
3. **Test suite**: Fails if invariants violated
4. **PROJECT_STATE_DIGEST.md**: Locks implemented systems

### Deviation Protocol

If a deviation from this doctrine is required:

1. Document rationale in instruction packet
2. Update this doctrine if boundary changes permanently
3. Ensure PSD and README updated to reflect change
4. Add tests to enforce new constraint

## Version History

- **2026-02-13 (WO-AUDIT-007)**: Re-baselined test runtime invariant, clarified voice scope
  - Test runtime: <25ms avg per test AND <120s total (at 5,254+ tests)
  - Voice pipeline integration (STT→intent, narration→TTS) moved to In Scope
  - Voice model training / custom voice synthesis remains Out of Scope
  - Updated stale test counts throughout
- **2025-02-08 (CP-07D)**: Initial doctrine creation
  - Locked scope boundaries (LLM, campaign continuity, test runtime)
  - Clarified terminology (stable hashing, not cryptographic)
  - Defined enforcement mechanisms

---

**Status**: This doctrine is **LOCKED**. Changes require explicit instruction packet with rationale.
