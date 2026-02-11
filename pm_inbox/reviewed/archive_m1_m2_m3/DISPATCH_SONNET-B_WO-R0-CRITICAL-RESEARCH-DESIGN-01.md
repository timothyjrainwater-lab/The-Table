# Instruction Packet: Sonnet-B

**Work Order:** WO-R0-CRITICAL-RESEARCH-DESIGN-01 (R0 Critical Research — Design WO Drafting)
**Dispatched By:** Opus (Acting PM)
**Date:** 2026-02-11
**Priority:** 2
**Deliverable Type:** Three work order drafts ready for PM dispatch

---

## CONTEXT

R0 research identified 49 research questions. R1 answered 7 fully and 6 partially. Six remain **critical and open** (see `docs/research/R0_MASTER_TRACKER.md` Section 10). Three of these are pure design work that can be progressed now without hardware access:

| Question ID | Topic | Why It's Critical |
|-------------|-------|-------------------|
| RQ-LLM-002 | LLM Query Interface Design | AIDM has no defined way to talk to Qwen3 yet — prompt format, system prompts, structured output, constraint enforcement |
| RQ-IMG-010 | Bounded Regeneration Policy | No defined limit on how many times image generation retries — could loop forever or give up too early |
| RQ-IMG-009 | Image Generation Failure Fallback | No defined behavior when all regeneration attempts fail — user sees broken image? placeholder? error? |

The other three (RQ-PREP-001, RQ-LLM-006, RQ-IMG-003) require hardware benchmarking or user testing and cannot be progressed by agents alone.

---

## YOUR TASK

Draft three work orders, one for each critical research question. These WOs will be dispatched to agents (possibly including you) for execution. You are writing the WOs, not executing them.

### WO Draft 1: RQ-LLM-002 — LLM Query Interface Design

**Research question:** "What is the query interface between AIDM and the LLM?"

**The WO should scope:**
- Prompt template design for Qwen3 8B (narration, query, structured output)
- System prompt architecture (what context the LLM always gets: world state summary, character context, tone guidance)
- Structured output enforcement (how to get JSON responses when needed — stop sequences, grammar constraints via llama.cpp)
- Constraint injection (how to enforce D&D 3.5e rules in prompts — "do not invent abilities," "respect HP values," etc.)
- Integration with existing `GuardedNarrationService` (the service exists, but currently uses template narration — how does it switch to LLM?)
- Integration with existing Spark adapter (model loading is done — this is about what you send to the loaded model)
- Error handling: what happens when LLM output is unparseable, off-topic, or violates constraints

**Key references for the WO author:**
- `aidm/narration/guarded_narration_service.py` — existing narration service
- `aidm/spark/llamacpp_adapter.py` — existing model loading
- `docs/design/M1_LLM_SAFEGUARD_ARCHITECTURE.md` — constraint architecture
- `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` Section 1 — Qwen3 capabilities

### WO Draft 2: RQ-IMG-010 — Bounded Regeneration Policy

**Research question:** "What is the bounded regeneration policy for image generation?"

**The WO should scope:**
- Maximum regeneration attempts (1 original + N retries — what is N?)
- Parameter adjustment strategy between attempts (CFG scale, step count, negative prompts, seed variation)
- Backoff schedule (what changes on retry 1, retry 2, retry 3)
- Convergence detection (when is an image "good enough" vs "keep trying"?)
- Integration with image critique pipeline (Heuristics → ImageReward scoring drives retry decisions)
- Resource budget (time budget per asset during prep, not just attempt count)
- Edge cases: what if the prompt itself is bad? What if the model consistently fails for certain subjects?

**Key references for the WO author:**
- `aidm/schemas/image_critique.py` — RegenerationAttempt schema already exists
- `pm_inbox/WO-M3-IMAGE-CRITIQUE-02_RESCOPED.md` — critique pipeline design (in progress)
- `docs/research/R0_PREP_PIPELINE_TIMING_STUDY.md` — prep time budgets

### WO Draft 3: RQ-IMG-009 — Image Generation Failure Fallback

**Research question:** "What happens when image generation fails after all attempts?"

**The WO should scope:**
- Placeholder strategy: what does the user see? Options:
  - Text description placeholder ("A tall half-orc warrior with a battle axe")
  - Solid color with text overlay
  - Generic category placeholder (one fallback image per asset type: NPC, scene, item)
  - No image (text-only mode)
- When to trigger: after max regeneration attempts exhausted? After timeout?
- User notification: does the user know generation failed? Can they manually retry later?
- Persistence: are failed attempts logged? Can prep be re-run for just failed assets?
- Graceful degradation across tiers: Baseline tier (no GPU) always uses placeholders — same placeholder system?
- Integration with asset store: placeholder stored as real asset or marked differently?

**Key references for the WO author:**
- `aidm/core/asset_store.py` — existing asset storage (supports placeholder assets)
- `aidm/core/prep_orchestrator.py` — existing prep pipeline (idempotent execution)
- `docs/AIDM_EXECUTION_ROADMAP_V3.md` M3 deliverables — "No mechanical dependence on images"

---

## FORMAT

Each WO draft should follow the standard format (see any WO in `pm_inbox/reviewed/` for examples):
- Work Order ID, Agent (TBD), Milestone, Priority, Status (DRAFT)
- Objective
- Scope (in scope / out of scope)
- Background (reference existing infrastructure)
- Tasks (numbered, with actions and outputs)
- Deliverables
- Acceptance Criteria
- Dependencies
- Stop Conditions

Keep each WO to 150-250 lines. These are design WOs (documentation output), not implementation WOs (code output).

---

## DELIVERY

Place deliverables in `pm_inbox/`:
- `SONNET-B_WO-RQ-LLM-002_llm_query_interface_DRAFT.md`
- `SONNET-B_WO-RQ-IMG-010_bounded_regeneration_DRAFT.md`
- `SONNET-B_WO-RQ-IMG-009_failure_fallback_DRAFT.md`
- `SONNET-B_WO-R0-CRITICAL-RESEARCH-DESIGN-01_completion.md`

---

## RULES

1. **Write the WOs, don't execute them.** Your deliverable is three work order documents, not three design documents.
2. **Reference existing code.** Every WO should point the future agent to the specific files they need to read.
3. **Don't over-scope.** These are design documentation WOs. No implementation, no dependencies, no code changes.
4. **Keep them independent.** Each WO should be dispatchable separately to different agents.
5. **Flag dependencies between them.** If RQ-IMG-010 depends on RQ-IMG-009 or vice versa, state that in the Dependencies section.

---

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `docs/research/R0_MASTER_TRACKER.md` Section 10 | R1 reconciliation of all 49 research questions |
| 2 | `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` | R1 model selections |
| 3 | `docs/research/R0_PREP_PIPELINE_TIMING_STUDY.md` | Prep timing projections |
| 4 | `AGENT_DEVELOPMENT_GUIDELINES.md` | Coding standards and WO format reference |

---

## STOP CONDITIONS

Stop and report if:
- Any of the three research questions has already been answered by existing documents you discover
- The scope of any WO overlaps significantly with an existing WO in `pm_inbox/reviewed/`
- You identify additional critical research questions not in the list above

---

**END OF INSTRUCTION PACKET**
