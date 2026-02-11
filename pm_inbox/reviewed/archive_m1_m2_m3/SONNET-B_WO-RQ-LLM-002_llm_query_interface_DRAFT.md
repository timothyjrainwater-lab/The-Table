# Work Order: WO-RQ-LLM-002 — LLM Query Interface Design

**Work Order ID:** WO-RQ-LLM-002
**Agent:** TBD (Agent A recommended)
**Milestone:** R0 Critical Research
**Priority:** 2 (Critical Path)
**Status:** DRAFT
**Research Question:** RQ-LLM-002 — LLM Query Interface Design
**Deliverable Type:** Design Documentation

---

## Objective

Design the query interface between AIDM and Qwen3 8B LLM for indexed memory retrieval, narration generation, and structured output requests. This WO defines how the LLM is invoked, what context it receives, how structured outputs are enforced, and how D&D 3.5e constraints are injected into prompts.

**Core Questions:**
- What is the prompt template structure for narration vs query vs structured output requests?
- What system prompt architecture provides world state context, character context, and tone guidance?
- How does AIDM enforce JSON responses when needed (stop sequences, grammar constraints via llama.cpp)?
- How does AIDM inject D&D 3.5e rule constraints into prompts ("do not invent abilities," "respect HP values," etc.)?
- How does `GuardedNarrationService` switch from template narration to LLM-generated narration?

---

## Background

### Existing Infrastructure

**LLM Loading:**
- [aidm/spark/llamacpp_adapter.py](../aidm/spark/llamacpp_adapter.py) — llama.cpp model loading with grammar constraints
- [aidm/spark/spark_adapter.py](../aidm/spark/spark_adapter.py) — Spark adapter protocol (text generation interface)
- [aidm/spark/model_registry.py](../aidm/spark/model_registry.py) — Model registry for swappable backends

**Narration Service:**
- [aidm/narration/guarded_narration_service.py](../aidm/narration/guarded_narration_service.py) — Existing narration service (currently uses template narration)
- [aidm/narration/narrator.py](../aidm/narration/narrator.py) — Narrator protocol

**Constraint Architecture:**
- [docs/design/M1_LLM_SAFEGUARD_ARCHITECTURE.md](../docs/design/M1_LLM_SAFEGUARD_ARCHITECTURE.md) — LLM safeguard architecture (constraint enforcement, hallucination prevention)

**Research Foundation:**
- [docs/research/R1_LLM_QUERY_INTERFACE_OPTIONS.md](../docs/research/R1_LLM_QUERY_INTERFACE_OPTIONS.md) — Non-binding research on query interface approaches (prompt engineering vs function calling vs RAG)
- [pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md](../pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md) Section 1 — Qwen3 8B capabilities, context window, structured output support

**Indexed Memory:**
- RQ-LLM-001 (LLM Indexed Memory Architecture) — COMPLETE (certified PASSED)
- Memory schemas: `SessionLedgerEntry`, `EvidenceLedger`, `ThreadRegistry` (existing)

---

## Scope

### IN SCOPE

1. **Prompt Template Design**
   - Narration generation template (combat, exploration, social, environmental descriptions)
   - Query template (entity lookup, event search, relationship queries)
   - Structured output template (JSON responses for mechanics, NPC stats, item generation)

2. **System Prompt Architecture**
   - World state summary injection (active NPCs, player location, current scene)
   - Character context injection (PC names, traits, current HP/status)
   - Tone guidance (fantasy genre, D&D 3.5e rules adherence, no modern slang)
   - Constraint injection (D&D 3.5e rule boundaries, no ability invention, respect HP values)

3. **Structured Output Enforcement**
   - Stop sequence definition for JSON responses
   - Grammar constraints via llama.cpp (GBNF grammar for JSON schema)
   - Fallback parsing when LLM deviates from schema

4. **GuardedNarrationService Integration**
   - How `GuardedNarrationService` switches from template narration to LLM narration
   - When to use templates vs LLM (latency considerations, determinism trade-offs)
   - How to pass world state to LLM for narration generation

5. **Error Handling**
   - What happens when LLM output is unparseable (malformed JSON, missing fields)
   - What happens when LLM output is off-topic (hallucinates abilities, invents NPCs)
   - What happens when LLM violates constraints (assigns HP values, changes stats)
   - Retry logic, fallback to templates, error reporting

6. **Acceptance Criteria Definition**
   - Success rate >85% for complex queries (per RQ-LLM-002)
   - No context window overflow for 50-turn sessions
   - JSON parsing success rate >95%
   - D&D 3.5e constraint adherence >95%

### OUT OF SCOPE

1. **Implementation**: This is design documentation only. No code changes to `GuardedNarrationService` or `llamacpp_adapter.py`.
2. **Model Fine-Tuning**: Qwen3 8B used as-is. No fine-tuning or LoRA adapters.
3. **Retrieval-Augmented Generation (RAG)**: Pure prompt engineering approach. RAG is M1+ scope.
4. **Function Calling**: Qwen3 8B does not support OpenAI-style function calling. Structured output via grammar constraints only.
5. **Benchmarking**: Design only. Actual query accuracy testing happens in separate validation WO.

---

## Tasks

### Task 1: Define Prompt Templates

**Action:** Design three prompt templates for different LLM interaction modes.

**Subtasks:**
1. **Narration Template**: Structure for combat/exploration/social/environmental narration
   - Input: World state, player action, environment context
   - Output: Natural language narration (2-4 sentences)
   - Example: Player attacks goblin → "You swing your sword at the goblin, catching it off guard. The blade strikes true, slicing across its chest. It stumbles backward with a pained shriek."

2. **Query Template**: Structure for indexed memory queries
   - Input: Query (entity lookup, event search, relationship query)
   - Output: Structured JSON response with entity IDs, event IDs, summary
   - Example: "What evidence exists for Theron showing loyalty?" → JSON with evidence IDs

3. **Structured Output Template**: Structure for mechanic-driven JSON responses
   - Input: Request for NPC stats, item properties, spell effects
   - Output: JSON conforming to schema (NPC stat block, item properties)
   - Example: Generate NPC goblin → JSON with HP, AC, attack bonus, etc.

**Output:**
- `PROMPT_TEMPLATES.md` section with all three templates
- Example prompts with expected outputs
- Token budget estimates per template (narration ≤500 tokens, query ≤800 tokens, structured ≤600 tokens)

---

### Task 2: Define System Prompt Architecture

**Action:** Design the system prompt that provides persistent context for all LLM interactions.

**Subtasks:**
1. **World State Summary**: Define how current world state is serialized for system prompt
   - Active NPCs (names, species, current HP/status)
   - Player location (current scene, room, dungeon level)
   - Active quests/threads (thread IDs, status)
   - Recent events (last 3-5 turns)

2. **Character Context**: Define how player character context is injected
   - PC names, classes, levels
   - Current HP, status effects
   - Equipped items, active spells

3. **Tone Guidance**: Define tone/style guidelines for LLM
   - Fantasy genre (no modern slang, sci-fi elements)
   - D&D 3.5e rules adherence
   - Descriptive but concise (2-4 sentences per narration)

4. **Constraint Injection**: Define D&D 3.5e rule boundaries
   - "Do not invent abilities, spells, or feats not in D&D 3.5e SRD"
   - "Do not assign HP values, ability scores, or stats (use provided values only)"
   - "Do not introduce new NPCs unless explicitly requested"
   - "Respect existing world state (do not contradict established facts)"

**Output:**
- `SYSTEM_PROMPT_ARCHITECTURE.md` section with system prompt template
- Example system prompt with world state, character context, tone guidance, constraints
- Token budget estimate for system prompt (≤1000 tokens target)

---

### Task 3: Define Structured Output Enforcement

**Action:** Specify how AIDM enforces JSON responses from Qwen3 8B using llama.cpp grammar constraints.

**Subtasks:**
1. **Grammar Constraint Design**: Define GBNF grammar for common JSON schemas
   - NPC stat block schema (name, HP, AC, attack bonus, species, description)
   - Item properties schema (name, type, weight, value, description, magical properties)
   - Query result schema (entity_ids, event_ids, summary)

2. **Stop Sequence Definition**: Define stop sequences for JSON responses
   - Stop at closing brace `}` for single-object responses
   - Stop at newline after closing brace for multi-object responses

3. **Fallback Parsing**: Define fallback logic when LLM deviates from schema
   - Partial JSON parsing (extract valid fields, use defaults for missing)
   - Error detection (malformed JSON, missing required fields)
   - Retry with stricter prompt ("Output ONLY valid JSON matching schema")

**Output:**
- `STRUCTURED_OUTPUT_ENFORCEMENT.md` section with grammar constraint examples
- GBNF grammar snippets for NPC/item/query schemas
- Fallback parsing logic specification
- Expected JSON parsing success rate (>95% target)

---

### Task 4: Define GuardedNarrationService Integration

**Action:** Specify how `GuardedNarrationService` switches between template narration and LLM narration.

**Subtasks:**
1. **Template vs LLM Decision Logic**: When to use templates vs LLM
   - Templates: Deterministic mechanics (damage dealt, HP changes, status effects)
   - LLM: Descriptive flavor (combat descriptions, environment, NPC reactions)
   - Hybrid: Mechanics via templates, flavor via LLM (concatenate outputs)

2. **World State Passing**: How to pass world state to LLM for narration
   - Serialize `WorldState` snapshot to prompt context
   - Include relevant entities (NPCs in current scene, active threads)
   - Limit to ≤2000 tokens (avoid context window overflow)

3. **LLM Invocation Interface**: How `GuardedNarrationService` calls LLM
   - Method signature: `generate_narration(action: PlayerAction, world_state: WorldState) -> str`
   - Error handling: Fallback to template if LLM fails (timeout, malformed output)

**Output:**
- `GUARDED_NARRATION_INTEGRATION.md` section with integration design
- Decision tree for template vs LLM selection
- Example narration generation flow (player attacks goblin → LLM generates flavor text)

---

### Task 5: Define Error Handling

**Action:** Specify error handling for LLM failures (unparseable output, off-topic responses, constraint violations).

**Subtasks:**
1. **Unparseable Output**: LLM returns malformed JSON or non-JSON text
   - Retry with stricter prompt (emphasize JSON-only output)
   - Fallback to template narration if retry fails
   - Log error for analysis (prompt, LLM response, error type)

2. **Off-Topic Response**: LLM hallucinates abilities, invents NPCs, contradicts world state
   - Detect via keyword matching (unknown ability names, unknown NPC names)
   - Reject response, retry with constraint reminder
   - Fallback to template if retry fails

3. **Constraint Violation**: LLM assigns HP values, changes stats, invents mechanics
   - Detect via output validation (HP value in narration, ability score mention)
   - Reject response, retry with constraint enforcement
   - Fallback to template if retry fails

4. **Retry Budget**: Define max retry attempts before fallback
   - Max 2 retries per LLM invocation (total 3 attempts: original + 2 retries)
   - Timeout per attempt: 5 seconds (GPU), 10 seconds (CPU)
   - Total budget per narration: 15 seconds (GPU), 30 seconds (CPU)

**Output:**
- `ERROR_HANDLING.md` section with error handling specification
- Error detection logic for each failure mode
- Retry/fallback decision tree
- Expected error rate estimates (unparseable <5%, off-topic <10%, constraint violation <5%)

---

### Task 6: Define Acceptance Criteria

**Action:** Specify measurable acceptance criteria for query interface design validation.

**Subtasks:**
1. **Query Accuracy**: LLM retrieves correct entity IDs, event IDs, relationships
   - Success rate >85% for complex queries (per RQ-LLM-002)
   - Test corpus: 50+ queries (entity lookup, event search, relationship queries)

2. **Context Window Management**: No overflow for 50-turn sessions
   - System prompt + world state + query ≤ 8000 tokens (Qwen3 8B context window)
   - Prune old events if context exceeds limit (keep last 5 turns)

3. **JSON Parsing Success**: LLM outputs valid JSON conforming to schema
   - Success rate >95% for structured output requests
   - Test corpus: 50+ structured output requests (NPC stats, item properties, query results)

4. **Constraint Adherence**: LLM respects D&D 3.5e rules and world state
   - No invented abilities, spells, feats (0 violations in 100 narrations)
   - No HP value assignments, stat changes (0 violations in 100 narrations)
   - No invented NPCs unless requested (0 violations in 100 narrations)

**Output:**
- `ACCEPTANCE_CRITERIA.md` section with validation metrics
- Test corpus definition (50+ queries, 50+ structured outputs, 100+ narrations)
- Pass/fail thresholds for each criterion

---

## Deliverables

1. **Design Document:** `docs/design/LLM_QUERY_INTERFACE_DESIGN.md` (150-250 lines)
   - Prompt templates (narration, query, structured output)
   - System prompt architecture (world state, character context, tone, constraints)
   - Structured output enforcement (grammar constraints, stop sequences, fallback parsing)
   - GuardedNarrationService integration (template vs LLM decision logic)
   - Error handling (unparseable output, off-topic, constraint violations)
   - Acceptance criteria (query accuracy, context management, JSON parsing, constraint adherence)

2. **Example Prompts:** Include 5+ example prompts with expected outputs
   - Combat narration example
   - Entity query example
   - NPC stat generation example
   - Off-topic detection example
   - Constraint violation example

3. **Integration Notes:** Reference existing code files that need updating (no implementation, just notes)
   - `aidm/narration/guarded_narration_service.py` — Add LLM narration mode
   - `aidm/spark/llamacpp_adapter.py` — Add grammar constraint support (may already exist)

---

## Acceptance Criteria

1. ✅ **Design document complete** with all six task sections (prompts, system prompt, structured output, integration, error handling, acceptance criteria)
2. ✅ **Example prompts included** with expected outputs (5+ examples covering narration, query, structured output)
3. ✅ **Token budget estimates** for each template (narration ≤500, query ≤800, structured ≤600, system prompt ≤1000)
4. ✅ **Error handling specified** for all three failure modes (unparseable, off-topic, constraint violation)
5. ✅ **Acceptance criteria defined** with measurable thresholds (query accuracy >85%, JSON parsing >95%, constraint adherence 100%)
6. ✅ **Integration notes** reference existing code files (GuardedNarrationService, llamacpp_adapter)

---

## Dependencies

**Depends On:**
- RQ-LLM-001 (LLM Indexed Memory Architecture) — COMPLETE (certified PASSED)
- RQ-HW-003 (Model Selection) — COMPLETE (R1 selected Qwen3 8B)
- M1 LLM Safeguard Architecture — COMPLETE (constraint enforcement architecture defined)

**Blocks:**
- RQ-LLM-006 (LLM Constraint Adherence Testing) — Cannot test constraint adherence until query interface is designed
- WO-M1-LLM-NARRATION-INTEGRATION (implementation) — Cannot implement LLM narration until query interface is designed

**Related:**
- RQ-LLM-002 research document ([docs/research/R1_LLM_QUERY_INTERFACE_OPTIONS.md](../docs/research/R1_LLM_QUERY_INTERFACE_OPTIONS.md)) — Non-binding research foundation
- R1 Technology Stack Validation Section 1 — Qwen3 8B capabilities

---

## Stop Conditions

**STOP and report if:**
1. **Existing design found**: A complete LLM query interface design already exists in `docs/design/` or `pm_inbox/reviewed/`
2. **Model selection changed**: R1 Technology Stack Validation is revised and Qwen3 8B is replaced with different LLM
3. **Scope overlap**: Another WO overlaps significantly with this work (e.g., WO-M1-LLM-NARRATION-INTEGRATION already includes query interface design)
4. **Blocking dependency**: RQ-LLM-001 status changes to NOT COMPLETE (indexed memory architecture must be finalized first)

---

## Notes for Agent

**Recommended Agent:** Agent A (LLM & Indexed Memory Architect)

**Key Considerations:**
- This is a **design WO**, not an implementation WO. Output is documentation, not code.
- Focus on **Qwen3 8B capabilities** (8K context window, no function calling, grammar constraints via llama.cpp).
- Prioritize **simplicity** over sophistication. Prompt engineering approach recommended (RAG is M1+ scope).
- Reference existing `GuardedNarrationService` and `llamacpp_adapter.py` for integration notes, but do not modify code.
- Use R1_LLM_QUERY_INTERFACE_OPTIONS.md as research foundation, but make binding design decisions.

**Estimated Effort:** 4-6 hours (research existing code, draft design document, create example prompts)

---

**END OF WORK ORDER DRAFT**
