# AD-002: Lens Context Orchestration Architecture

**Status:** APPROVED
**Date:** 2026-02-12
**Authority:** PM (Opus) + PO (Thunder)
**Source:** GPT architectural review — Lens↔Spark coupling analysis

---

## Decision

**Lens is the operating system for context, not a RAG pipeline.** The Lens↔Spark interface must be a deterministic, versioned wire protocol with explicitly defined channels — not ad hoc prompt text assembly.

This decision shapes the PromptPack v1 specification and all downstream Spark integration work.

---

## The Core Problem

The real question for campaign viability is not "can we write a good prompt?" — it's:

**Can Lens reliably manufacture the illusion of an infinite context window while keeping Spark boxed into deterministic truth and bounded creativity?**

This is a systems problem, not a prompt trick. If Lens doesn't control context deterministically, failures will be misattributed to assets (TTS, image critique, model quality) when the real cause is uncontrolled context assembly.

---

## The Five Channels of a PromptPack

Every Spark invocation receives a PromptPack assembled by Lens. The PromptPack is NOT free-form text. It is a structured payload with five explicit channels:

### 1. Truth Channel (Hard Constraints)
- What is true RIGHT NOW (post-settlement Box snapshot)
- What Spark MUST NOT contradict (mechanical outcomes, entity states, positions)
- What Spark MUST label as uncertain (unresolved facts, ambiguous states)
- Sourced from: FrozenWorldStateView, Box event receipts, NarrativeBrief containment layer

### 2. Memory Channel (Retrieved, Scoped)
- Only the few facts relevant to THIS turn/scene
- With provenance + recency + salience metadata
- Summarized aggressively, expanded only on demand
- Hard caps: count limit + token budget
- "Expand on demand" protocol: Spark can request more context via structured signal, but Lens decides what to provide

### 3. Task Channel (What Spark Is Doing)
- Each invocation has ONE task type with its own output schema and token budget:
  - **Narration** — describe what just happened in combat/exploration
  - **Scene Beats** — propose next narrative beats for pacing
  - **NPC Dialogue** — generate in-character speech for a specific entity
  - **Session Summary** — compress recent events into memory
  - **Scene Planning** — draft scene cards/hooks (non-authoritative, per AD-001)
- Task type determines: output schema, validation rules, token allocation, retry policy

### 4. Style Channel (Persona + Tone)
- Bounded knobs, not "be creative"
- Must be stable across a session (no jitter)
- Parameters: verbosity, drama, humor, grittiness, NPC voice identity
- Persona identity is deterministic (same character → same style parameters, per WO-052)

### 5. Output Contract (Machine-Checkable)
- Spark does NOT "write a story"
- Spark emits structured payloads with bounded free-text fields
- Validators can enforce rules because the output schema is explicit
- Per-task schemas define: required fields, optional fields, forbidden content, max lengths

---

## PromptPack Properties (Non-Negotiable)

The assembled PromptPack MUST be:

1. **Deterministic** — same inputs → same prompt bytes (no randomized ordering, no timestamp injection, no floating-point formatting variance)
2. **Versioned** — `schema_version` field in every PromptPack; validators match version
3. **Sectioned** — channels are explicit sections with markers, not interleaved prose
4. **Budgeted** — each channel has a token allocation; total cannot exceed model context minus response reserve
5. **Truncation-safe** — when budget is exceeded, truncation follows a deterministic priority:
   - Truth channel: NEVER truncated (hard constraint)
   - Task channel: NEVER truncated (defines what Spark does)
   - Style channel: NEVER truncated (small, bounded)
   - Memory channel: truncated FIRST (least-recent items dropped)
   - Output contract: NEVER truncated

If constraints survive truncation, Spark behavior degrades gracefully. If constraints are truncated, Spark behavior becomes random. Therefore: constraints are protected.

---

## Campaign Viability Requirements

A multi-session campaign works only if:

1. **Retrieval stays small and relevant** — or you drown the model in irrelevant context
2. **Contradictions are detected and handled** — or trust dies (player notices the DM contradicting itself)
3. **Summarization doesn't drift** — or continuity dies (NPCs forget conversations, quests lose threads)
4. **The system is stable under truncation** — or behavior becomes unpredictable

All four of these are Lens problems. Spark is the renderer.

---

## Five Required Research Deliverables

These are gated research items that must be completed before campaign-length play is viable:

### RD-001: Lens↔Spark PromptPack v1 Specification
- Sections, ordering, token budgets, truncation rules, schema_version
- Output schemas per task type (Narration, Scene Beats, NPC Dialogue, Session Summary)
- Deterministic serialization format
- Golden tests proving identical inputs → identical bytes

### RD-002: Memory Retrieval Policy
- What gets retrieved, when, and why
- Ranking function (recency × salience × quest relevance)
- Hard caps (item count + token budget)
- "Expand on demand" protocol (Spark signals need → Lens decides response)
- Eviction policy for session memory growth

### RD-003: Summarization Stability Protocol
- When summaries are created and updated
- How drift is detected (diff checks against source events, contradiction scans)
- What triggers "rebuild summary from primary sources"
- Provenance: every summary statement traces back to source events

### RD-004: Contradiction Handling Protocol
- What happens when Spark output contradicts truth channel
- Detection: real-time keyword/pattern scan + async semantic check
- Response: bounded retry (max N) → template fallback → log violation
- How to label uncertain claims in output ([UNCERTAIN] tagging)
- Ties to existing Grammar Shield and KILL-002 mechanisms

### RD-005: Continuity Evaluation Harness
- Small suite of scenario scripts measuring:
  - Continuity across 50-100 turns (NPC knowledge stability, quest thread persistence)
  - Contradiction rate (narration vs Box truth)
  - Prompt budget stability (does memory channel grow unbounded?)
  - Regression across model swaps (Qwen3-8B → 4B → 0.5B)
- Automated scoring without human judges for every turn

---

## Scoping Decision: Narration-First

For PromptPack v1, the initial scope is **narration only**:
- Task types: Narration, NPC Dialogue
- NOT in v1: Scene Planning, Quest Thread Management, Session Summary generation

Rationale: Lock a narrow, validatable protocol first. Campaign-authoring behaviors (scene planning, quest threads, summaries) require the Memory Retrieval Policy (RD-002) and Summarization Stability Protocol (RD-003) to be defined. Those are Phase 2 research. Narration can ship without them.

The PromptPack architecture MUST be designed to support additional task types without breaking the wire protocol — but v1 only needs to implement two.

---

## Impact on Existing Work

### RWO-005 (Seam Protocol Analysis) — Currently Running
The seam analysis agent is investigating Lens↔Spark boundaries now. This decision defines what the protocol SHOULD look like. The agent's findings will tell us what currently EXISTS vs what needs to be built.

### A2 (LensPromptPack v1) — Queued for Phase 2
This decision significantly enriches the A2 work item. The PromptPack is not just "a schema with sections" — it's a five-channel wire protocol with deterministic assembly, version control, and truncation safety. The A2 spec must implement all five channels.

### WO-032 (NarrativeBrief Assembler) — Dispatched
WO-032 is the implementation work order for the Lens→Spark context assembly. It should be reviewed against this decision to ensure it implements channel separation rather than monolithic prompt construction.

### RQ-SPARK-001 Synthesis (RWO-001) — Currently Running
The synthesis must respect this architecture: Spark's structured output schema must align with the Task Channel's per-task output contracts.

---

## The Mental Model Correction

"Systematic prompt injection" is the wrong frame. It implies ad hoc text munging.

The correct frame: **Context orchestration + deterministic assembly.**

Lens builds a PromptPack that is a wire protocol — deterministic, versioned, sectioned, budgeted, truncation-safe. Spark consumes it and emits structured payloads. Validators enforce the output contract.

This is infrastructure, not prompting.

---

*This decision was prompted by external architectural review identifying that uncontrolled Lens↔Spark coupling is the primary risk to campaign viability and system trust.*
