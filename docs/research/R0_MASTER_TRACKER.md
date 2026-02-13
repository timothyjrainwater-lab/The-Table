# R0 Master Tracker — Research Questions, Owners, Status, Acceptance Thresholds

**Document Type:** R0 Governance / Master Index
**Purpose:** Central registry of all R0 research questions, ownership, priorities, and GO/NO-GO acceptance criteria
**Last Updated:** 2026-02-11
**Agent:** Agent D (Research Orchestrator)
**M1 Status:** ✅ **UNLOCKED** (2026-02-10) — LLM Narration Integration authorized with guardrails enforcement

> ## R1 REVISION NOTICE (2026-02-11)
>
> The R1 Technology Stack Validation (Opus, 2026-02-11) resolved model selections across all technology areas. Several research questions listed below as "Not Started" are now **partially or fully answered** by R1 findings. Key changes:
>
> - **RQ-HW-003 (Model Selection):** Acceptance thresholds updated — Qwen3 8B/14B (LLM), SDXL Lightning NF4 (image), Kokoro (TTS), faster-whisper small.en (STT)
> - **RQ-IMG-001 (Image Critique):** Model selection resolved — Heuristics + ImageReward + SigLIP pipeline
> - **RQ-VOICE-001 (TTS Quality):** Primary engine identified — Kokoro TTS (4.0/5 quality, Apache 2.0)
> - **R0-DEC-025 (SDXL NO-GO):** **REVERSED** — NF4 quantization brings SDXL to 3.5-4.5 GB VRAM
> - **Architecture correction:** AIDM is a prep-time sequential pipeline, not simultaneous model loading
>
> Questions marked as "R1-ANSWERED" below have model selections resolved but may still need benchmarking validation.
>
> **Full details:** `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md`

---

## 1. R0 Overview

### Summary Statistics

**Total Research Questions:** 49
- **Critical (Blocks M0):** 16
- **Important (Affects Architecture):** 19
- **Optional (Clarifications):** 14

**Status Breakdown (Post-R1 Reconciliation, 2026-02-11):**
- **R1-Answered:** 7 (model selections resolved, benchmarking needed)
- **R1-Partially-Answered:** 6 (direction clear, work remains)
- **Complete:** 2 (RQ-LLM-001, R1-ARCH-001)
- **In Progress:** 4 (Canonical ID Schema, Hardware Baseline, LLM Determinism, Prep Idempotency)
- **Still Open (Critical):** 6 (LLM query, LLM constraint adherence, image quality, prep time, bounded regen, failure fallback)
- **Still Open (Important):** 13
- **Deferred (M1+):** 11
- **Blocked:** 0

### Owner Assignments

| Agent | Role | Question Count | Focus Areas |
|-------|------|----------------|-------------|
| **Agent A** | LLM & Indexed Memory | 12 | LLM constraint adherence, indexed memory architecture, retrieval validation |
| **Agent B** | Image & Asset Generation | 10 | Image generation, critique models, asset pipeline, quality gates |
| **Agent C** | Integration & UX | 8 | UI layout, onboarding flow, player experience, accessibility |
| **Agent D** | Research Orchestrator | 18 | Hardware baseline, model budgets, prep pipeline, determinism, schema design |

---

## 2. Research Questions by Category

### Category: LLM & Indexed Memory (12 questions)

#### RQ-LLM-001: LLM Indexed Memory Architecture
- **Question:** What indexing system should be used for LLM memory retrieval? (SQLite? Vector DB? JSON?)
- **Owner:** Agent A
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Retrieval accuracy >90% for entity/event queries
  - Query latency <200ms per turn
  - Scalable to 100+ sessions (1000+ events)
- **Status:** Complete (Certified) — PASSED with policy gaps documented (GAP-POL-01 through GAP-POL-04)
- **Blockers:** None
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`, `CANONICAL_ID_SCHEMA_DRAFT.md`, `R0_DECISION_REGISTER.md` (R0-DEC-049)

#### RQ-LLM-002: LLM Query Interface
- **Question:** How does LLM query indexed records? (Prompt engineering? Function calling? RAG?)
- **Owner:** Agent A
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - LLM can reliably query by entity ID, event ID, relationship
  - Success rate >85% for complex queries (e.g., "Find all events where Fighter attacked Goblin")
  - No context window overflow for 50-turn sessions
- **Status:** Not Started
- **Blockers:** RQ-LLM-001 (architecture must be chosen first)
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

#### RQ-LLM-003: Entity Renames in Indexed Memory
- **Question:** How does indexed memory handle entity renames? (e.g., "Goblin 1" → "Chief Gruk")
- **Owner:** Agent A
- **Priority:** Important
- **Acceptance Threshold:**
  - Old queries still resolve to renamed entity
  - Alias system supports multiple names per entity
  - No orphaned references in event log
- **Status:** Not Started
- **Blockers:** RQ-LLM-001
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q24)

#### RQ-LLM-004: Deleted Entities in Index
- **Question:** How are deleted entities handled in the index? (Soft delete? Tombstone? Cascade?)
- **Owner:** Agent A
- **Priority:** Important
- **Acceptance Threshold:**
  - Deleted entities remain queryable (for session replay)
  - Event logs reference deleted entities correctly
  - No broken references in teaching ledger
- **Status:** Not Started
- **Blockers:** RQ-LLM-001
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q25)

#### RQ-LLM-005: Entity ID Aliasing
- **Question:** Can IDs be aliased? (e.g., "Theron" → `entity_camp001_a3f2b8c4`)
- **Owner:** Agent A
- **Priority:** Important
- **Acceptance Threshold:**
  - Natural language queries resolve to canonical IDs
  - Alias table supports multilingual input (deferred to M1)
  - No ambiguity (unique alias per entity per campaign)
- **Status:** Not Started
- **Blockers:** RQ-SCHEMA-001 (ID schema must be locked)
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q26)

#### RQ-LLM-006: LLM Constraint Adherence
- **Question:** Can LLM reliably adhere to D&D 3.5e rules without hallucination?
- **Owner:** Agent A
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - >95% rule accuracy for core mechanics (attack, damage, saves)
  - <5% hallucination rate for feats, spells, abilities
  - Indexed memory prevents contradictions across sessions
- **Status:** Not Started
- **Blockers:** RQ-LLM-001 (memory required for consistency)
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

#### RQ-LLM-007: LLM Output Determinism
- **Question:** Are there any non-deterministic ID sources in the current codebase? How are IDs generated in parallel contexts?
- **Owner:** Agent D
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - All IDs deterministic (same input → same ID)
  - No timestamps, UUIDs, or sequential counters in IDs
  - Parallel prep jobs generate deterministic IDs (no race conditions)
- **Status:** In Progress (Canonical ID Schema draft addresses this)
- **Blockers:** None
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q29, Q30)

#### RQ-LLM-008: Session Recap Summarization
- **Question:** How are "notable moments" identified and tagged for session recap?
- **Owner:** Agent A
- **Priority:** Important
- **Acceptance Threshold:**
  - Top 5-10 key events per session auto-tagged
  - DM can recap prior session in <30 seconds
  - Player can dispute/correct recap
- **Status:** Not Started
- **Blockers:** RQ-LLM-001 (event indexing required)
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

#### RQ-LLM-009: Knowledge Tome Progressive Detail
- **Question:** What triggers knowledge progression? (Encounter count? Explicit investigation?)
- **Owner:** Agent A
- **Priority:** Optional (M1 feature)
- **Acceptance Threshold:**
  - Knowledge increments based on explicit player actions (inspect, study, etc.)
  - No meta-gaming (character knowledge ≠ player knowledge)
  - Progressive detail stored in indexed memory
- **Status:** Not Started (M1 deferred)
- **Blockers:** RQ-LLM-001
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

#### RQ-LLM-010: Duplicate NPC Naming
- **Question:** How are NPCs with duplicate names handled? (e.g., "Goblin 1", "Goblin 2")
- **Owner:** Agent D
- **Priority:** Important
- **Acceptance Threshold:**
  - Unique ID per entity (e.g., `entity_camp001_goblin1_a3f2b8c4`)
  - Display names can be identical, but IDs always unique
  - LLM can disambiguate ("Which goblin? The one on the left or right?")
- **Status:** In Progress (Canonical ID Schema draft addresses this)
- **Blockers:** None
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q1)

#### RQ-LLM-011: Entity Persistence Across Sessions
- **Question:** Do entities persist across sessions or are they session-scoped?
- **Owner:** Agent D
- **Priority:** Important
- **Acceptance Threshold:**
  - Entities persist across sessions (campaign-scoped)
  - Session IDs reference campaign context
  - Entity state snapshots per session (for replay)
- **Status:** In Progress (Canonical ID Schema draft addresses this)
- **Blockers:** None
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q2)

#### RQ-LLM-012: Entity Rename Side Effects
- **Question:** What happens when an entity is renamed?
- **Owner:** Agent A
- **Priority:** Optional
- **Acceptance Threshold:**
  - ID remains stable (rename does not change ID)
  - Alias table updated (old name + new name → same ID)
  - Event log references unchanged
- **Status:** Not Started
- **Blockers:** RQ-LLM-003
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q3)

---

### Category: Image Generation & Critique (10 questions)

#### RQ-IMG-001: Image Critique Model Selection
- **Question:** Which critique model should be used? (CLIP-based? Custom trained? Aesthetic scorer?)
- **Owner:** Agent B
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - >80% bad image detection (artifacting, misalignment, uncanny valley)
  - <10% false positive rate (good images rejected)
  - Fits hardware budget (median spec: 6-8 GB VRAM)
- **Status:** Not Started
- **Blockers:** RQ-HW-001 (hardware baseline required for VRAM budget)
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`, `HARDWARE_BASELINE_REPORT.md`

#### RQ-IMG-002: Image Critique Failure Modes
- **Question:** What are failure modes for image critique? (False positives? False negatives? Bias?)
- **Owner:** Agent B
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Documented failure modes (style bias, cultural bias, genre misalignment)
  - Fallback strategy defined (human review? regeneration limit?)
  - Player can override critique ("Accept this image anyway")
- **Status:** Not Started
- **Blockers:** RQ-IMG-001
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

#### RQ-IMG-003: Image Quality Threshold
- **Question:** What is "acceptable" image quality for M0 launch?
- **Owner:** Agent C (UX), Agent B (Technical)
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Playtest feedback: >70% "acceptable or better" rating
  - No uncanny valley (coherent faces, hands, anatomy)
  - Style consistency across session (same NPC = same portrait style)
- **Status:** Not Started
- **Blockers:** RQ-IMG-001, RQ-HW-003 (model selection required)
- **Related Documents:** `MVP_SCOPE_M0_VS_M1.md` (Q3)

#### RQ-IMG-004: Asset Content Addressing
- **Question:** Are assets truly content-addressed, or can same semantic_key have multiple versions?
- **Owner:** Agent D
- **Priority:** Important
- **Acceptance Threshold:**
  - Same semantic_key → same asset ID (deterministic)
  - Asset versioning supported (e.g., "tavern_v1", "tavern_v2")
  - Deduplication works across campaigns
- **Status:** In Progress (Canonical ID Schema draft addresses this)
- **Blockers:** None
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q4)

#### RQ-IMG-005: Asset Variant Handling
- **Question:** How are asset variants handled? (e.g., "tavern_interior_day" vs "tavern_interior_night")
- **Owner:** Agent B
- **Priority:** Important
- **Acceptance Threshold:**
  - Variants use different semantic_keys (e.g., "tavern:interior:day" vs "tavern:interior:night")
  - Same base prompt + variant parameter → deterministic output
  - Variant tags stored in asset metadata
- **Status:** Not Started
- **Blockers:** RQ-IMG-004
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q5)

#### RQ-IMG-006: Shared Cache Asset IDs
- **Question:** Should shared cache assets use `shared_` prefix instead of campaign ID?
- **Owner:** Agent D
- **Priority:** Optional
- **Acceptance Threshold:**
  - Shared cache identified by `shared_` prefix or campaign ID = "global"
  - Cross-campaign deduplication works correctly
  - No ID collisions between campaigns
- **Status:** Not Started
- **Blockers:** RQ-SCHEMA-001
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q6)

#### RQ-IMG-007: Image Generation Latency (Median Spec)
- **Question:** What is realistic image generation latency on median hardware (GPU mode)?
- **Owner:** Agent B, Agent D (Hardware)
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Median spec (6-8 GB VRAM): 8-15 sec per 512x512 image
  - Stable Diffusion 1.5 or SDXL Turbo (quantized)
  - Acceptable for prep-phase generation (not runtime)
- **Status:** Not Started
- **Blockers:** RQ-HW-001, RQ-HW-003
- **Related Documents:** `HARDWARE_BASELINE_REPORT.md`, `R0_MODEL_BUDGETS.md`

#### RQ-IMG-008: Image Generation Latency (Minimum Spec)
- **Question:** What is realistic image generation latency on minimum hardware (CPU fallback)?
- **Owner:** Agent B, Agent D (Hardware)
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Minimum spec (4-core CPU, 0 VRAM): 60-120 sec per image
  - Acceptable UX degradation (user warned of slow generation)
  - Still functional (no hard blocker)
- **Status:** Not Started
- **Blockers:** RQ-HW-002, RQ-HW-003
- **Related Documents:** `HARDWARE_BASELINE_REPORT.md`, `R0_MODEL_BUDGETS.md`

#### RQ-IMG-009: Image Generation Failure Fallback
- **Question:** What happens if image generation fails after all attempts?
- **Owner:** Agent B
- **Priority:** Important
- **Acceptance Threshold:**
  - Graceful degradation (placeholder silhouette + text description)
  - Player can retry later or continue without image
  - Failure logged for debugging
- **Status:** Not Started
- **Blockers:** RQ-IMG-002
- **Related Documents:** `MVP_SCOPE_M0_VS_M1.md` (Q5)

#### RQ-IMG-010: Bounded Regeneration Policy
- **Question:** How many regeneration attempts before fallback?
- **Owner:** Agent B
- **Priority:** Important
- **Acceptance Threshold:**
  - Max 3 regeneration attempts per asset
  - Player can override ("Accept this anyway")
  - Exponential backoff or quality threshold decay
- **Status:** Not Started
- **Blockers:** RQ-IMG-001, RQ-IMG-002
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

---

### Category: Voice I/O (TTS/STT) (6 questions)

#### RQ-VOICE-001: TTS Quality Baseline
- **Question:** What is "acceptable" TTS quality for M0 launch?
- **Owner:** Agent C (UX), Agent D (Technical)
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Playtest feedback: >70% "acceptable or better" rating
  - Intelligibility: >95% word recognition
  - Naturalness: Not robotic (benchmark: ElevenLabs "decent" tier)
- **Status:** Not Started
- **Blockers:** RQ-HW-003 (model selection required)
- **Related Documents:** `MVP_SCOPE_M0_VS_M1.md` (Q3), `HARDWARE_BASELINE_REPORT.md`

#### RQ-VOICE-002: TTS Latency Target
- **Question:** What is acceptable TTS latency for voice-first interaction?
- **Owner:** Agent D
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Median spec: <500ms for first audio chunk (streaming)
  - Minimum spec: <1000ms (acceptable degradation)
  - No perceptible delay in DM narration
- **Status:** Not Started
- **Blockers:** RQ-HW-001, RQ-HW-003
- **Related Documents:** `HARDWARE_BASELINE_REPORT.md`, `R0_MODEL_BUDGETS.md`

#### RQ-VOICE-003: STT Latency Target
- **Question:** What is acceptable STT latency for voice input?
- **Owner:** Agent D
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Median spec: <1000ms for 10-second audio clip
  - Minimum spec: <2000ms (acceptable degradation)
  - Fast enough for natural conversation
- **Status:** Not Started
- **Blockers:** RQ-HW-001, RQ-HW-003
- **Related Documents:** `HARDWARE_BASELINE_REPORT.md`, `R0_MODEL_BUDGETS.md`

#### RQ-VOICE-004: TTS Persona Switching
- **Question:** Can TTS models switch personas reliably? (Tone, accent, gender, speed?)
- **Owner:** Agent B, Agent C
- **Priority:** Optional (M1 feature)
- **Acceptance Threshold:**
  - Single persona for M0 (deferred to M1)
  - Design voice profile system (tone, speed, pitch parameters)
  - Validate persona switching in R0 for M1 feasibility
- **Status:** Not Started (M1 deferred)
- **Blockers:** RQ-VOICE-001
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

#### RQ-VOICE-005: Multilingual STT Accuracy
- **Question:** What is STT accuracy for non-English languages?
- **Owner:** Agent B
- **Priority:** Optional (M1 feature)
- **Acceptance Threshold:**
  - M0: English-only (deferred to M1)
  - M1: Whisper supports 50+ languages (validate top 5: Spanish, French, German, Japanese, Mandarin)
  - Accuracy >80% for multilingual input
- **Status:** Not Started (M1 deferred)
- **Blockers:** RQ-VOICE-003
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

#### RQ-VOICE-006: Multilingual TTS Quality
- **Question:** What is TTS quality for non-English languages?
- **Owner:** Agent B
- **Priority:** Optional (M1 feature)
- **Acceptance Threshold:**
  - M0: English-only (deferred to M1)
  - M1: Validate TTS quality for top 5 languages
  - Naturalness >70% "acceptable" rating
- **Status:** Not Started (M1 deferred)
- **Blockers:** RQ-VOICE-001
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

---

### Category: Prep Pipeline (8 questions)

#### RQ-PREP-001: Prep Time Budget
- **Question:** How long should session prep take? What is acceptable UX?
- **Owner:** Agent D, Agent C (UX)
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Target: ≤30 minutes for 2-hour session (15:1 play-to-prep ratio)
  - Acceptable: ≤60 minutes (traditional DM prep is 1-2 hours)
  - User can cancel/resume prep
- **Status:** Not Started
- **Blockers:** RQ-PREP-002 (breakdown required)
- **Related Documents:** `MVP_SCOPE_M0_VS_M1.md` (Q4), `GAP_AND_RISK_REGISTER.md`

#### RQ-PREP-002: Prep Phase Task Breakdown
- **Question:** What happens during prep phase? (Asset list, sequence, resource allocation)
- **Owner:** Agent D
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Documented asset list (e.g., 10 NPC portraits, 5 scene backgrounds)
  - Generation sequence defined (portraits first, then scenes)
  - Resource allocation per task (image gen: 15 sec × 10 = 2.5 min)
- **Status:** Not Started
- **Blockers:** RQ-IMG-007, RQ-HW-003
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

#### RQ-PREP-003: Prep Job Idempotency
- **Question:** Are prep jobs truly idempotent, or can they run multiple times?
- **Owner:** Agent D
- **Priority:** Important
- **Acceptance Threshold:**
  - Same prep params → same job ID (deterministic)
  - Idempotent: re-running job uses cached results (no regeneration)
  - Cache invalidation strategy defined (manual vs automatic)
- **Status:** In Progress (Canonical ID Schema draft addresses this)
- **Blockers:** None
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q13)

#### RQ-PREP-004: Failed Prep Job Retry
- **Question:** How are failed prep jobs retried?
- **Owner:** Agent D
- **Priority:** Important
- **Acceptance Threshold:**
  - Auto-retry (max 3 attempts)
  - Exponential backoff (1 sec, 5 sec, 15 sec)
  - Manual retry option (player can retry failed jobs)
- **Status:** Not Started
- **Blockers:** RQ-PREP-002
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q14)

#### RQ-PREP-005: Prep Job Dependencies
- **Question:** Do prep jobs reference each other (dependency DAG)?
- **Owner:** Agent D
- **Priority:** Optional
- **Acceptance Threshold:**
  - Jobs can declare dependencies (e.g., "scene background depends on NPC portraits")
  - Parallel execution where possible (no dependencies)
  - Topological sort for execution order
- **Status:** Not Started
- **Blockers:** RQ-PREP-002
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q15)

#### RQ-PREP-006: Prep Job Regen with Different Params
- **Question:** Can prep jobs be retried with different params? (e.g., "regenerate portrait with better quality")
- **Owner:** Agent D
- **Priority:** Optional
- **Acceptance Threshold:**
  - New params → new job ID (not idempotent)
  - Old asset archived, new asset generated
  - Player can choose between old and new
- **Status:** Not Started
- **Blockers:** RQ-PREP-003
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q27)

#### RQ-PREP-007: Versioned Asset Handling
- **Question:** How are versioned assets handled? (v1, v2, v3)
- **Owner:** Agent D, Agent B
- **Priority:** Optional
- **Acceptance Threshold:**
  - Asset IDs include version tag (e.g., `asset_camp001_portrait_theron_v2`)
  - Old versions archived (not deleted)
  - Player can rollback to previous version
- **Status:** Not Started
- **Blockers:** RQ-PREP-006
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q28)

#### RQ-PREP-008: Prep Phase Failure UX
- **Question:** What if prep exceeds time budget or fails?
- **Owner:** Agent C (UX), Agent D (Technical)
- **Priority:** Important
- **Acceptance Threshold:**
  - Player can cancel prep and play with placeholders
  - Player can resume interrupted prep
  - Failure logged with actionable error message
- **Status:** Not Started
- **Blockers:** RQ-PREP-001, RQ-PREP-004
- **Related Documents:** `GAP_AND_RISK_REGISTER.md`

---

### Category: Hardware & Performance (6 questions)

#### RQ-HW-001: Hardware Baseline Extraction
- **Question:** What is median PC spec from Steam Hardware Survey (January 2025)?
- **Owner:** Agent D
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Median spec extracted (CPU cores, RAM, GPU VRAM)
  - Minimum spec defined (CPU fallback, 8 GB RAM)
  - Cross-validated with third-party surveys (UserBenchmark)
- **Status:** In Progress (Hardware Baseline Report draft completed)
- **Blockers:** None
- **Related Documents:** `HARDWARE_BASELINE_REPORT.md`, `GAP_AND_RISK_REGISTER.md`

#### RQ-HW-002: Minimum Spec CPU Fallback
- **Question:** Can AIDM run on 8 GB RAM, 4-core CPU, integrated graphics?
- **Owner:** Agent D
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Minimum spec defined (8 GB RAM, 4 cores, 0 VRAM)
  - LLM inference: 5-10 tokens/sec (acceptable degradation)
  - Image gen: 60-120 sec/image (acceptable for prep phase)
- **Status:** In Progress (Model Budgets draft addresses this)
- **Blockers:** RQ-HW-001
- **Related Documents:** `HARDWARE_BASELINE_REPORT.md`, `R0_MODEL_BUDGETS.md`

#### RQ-HW-003: Model Selection Within Budget
- **Question:** Which models fit median/minimum hardware budgets?
- **Owner:** Agent D
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - **LLM:** Mistral 7B (4-bit) for median, Phi-2 for minimum
  - **Image:** Stable Diffusion 1.5 for median, CPU fallback for minimum
  - **TTS:** Coqui/Piper for both specs
  - **STT:** Whisper Base for median, Whisper Tiny for minimum
- **Status:** In Progress (Model Budgets draft completed)
- **Blockers:** RQ-HW-001, RQ-HW-002
- **Related Documents:** `R0_MODEL_BUDGETS.md`

#### RQ-HW-004: GPU Requirement Decision
- **Question:** Should AIDM require discrete GPU or support integrated graphics?
- **Owner:** Agent D
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Support integrated graphics (CPU fallback mode)
  - 15% of Steam users have no discrete GPU → must support
  - Performance degraded but functional
- **Status:** In Progress (Model Budgets draft addresses this)
- **Blockers:** RQ-HW-002
- **Related Documents:** `HARDWARE_BASELINE_REPORT.md` (Q1)

#### RQ-HW-005: Cross-Platform Priority
- **Question:** Should M0 support Linux/macOS, or Windows-only?
- **Owner:** Agent D, Agent C
- **Priority:** Important
- **Acceptance Threshold:**
  - M0: Windows-only (95% of Steam users)
  - M1: Linux/macOS support
  - Architecture supports cross-platform (no OS-specific dependencies)
- **Status:** Not Started
- **Blockers:** None
- **Related Documents:** `HARDWARE_BASELINE_REPORT.md` (Q3)

#### RQ-HW-006: Cloud vs Local Models
- **Question:** Should AIDM use cloud-based models (ElevenLabs, OpenAI) or local models?
- **Owner:** Agent D
- **Priority:** Important
- **Acceptance Threshold:**
  - M0: Local-first (offline play, no API costs)
  - M1: Cloud as optional upgrade (better quality, requires internet)
  - Hybrid approach maximizes flexibility
- **Status:** Not Started
- **Blockers:** RQ-HW-003
- **Related Documents:** `HARDWARE_BASELINE_REPORT.md` (Q2)

---

### Category: Architecture & Integration (6 questions)

#### RQ-SCHEMA-001: Canonical ID Format Definition
- **Question:** What is the canonical ID format? (Structure, namespace, validation rules)
- **Owner:** Agent D
- **Priority:** CRITICAL
- **Acceptance Threshold:**
  - Format documented (e.g., `<type>_<context>_<hash>`)
  - Namespace rules defined (entity vs asset vs session)
  - Validation logic specified (regex pattern, length limits)
  - Collision resistance validated (8-char hash sufficient for 100k entities)
- **Status:** In Progress (Canonical ID Schema draft completed)
- **Blockers:** None
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md`, `GAP_AND_RISK_REGISTER.md`

#### RQ-SCHEMA-002: ID Collision Probability
- **Question:** What is target max entities per campaign? What hash length prevents collisions?
- **Owner:** Agent D
- **Priority:** Important
- **Acceptance Threshold:**
  - Target: 10k-100k entities per campaign
  - 8-char hash (32 bits): ~1 in 4.3 billion collision probability (acceptable)
  - 16-char hash for critical IDs (campaign, session)
- **Status:** In Progress (Canonical ID Schema draft addresses this)
- **Blockers:** None
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q19, Q20)

#### RQ-SCHEMA-003: Campaign ID User Scoping
- **Question:** Are user IDs deterministic, or external (e.g., Steam ID)?
- **Owner:** Agent D
- **Priority:** Important
- **Acceptance Threshold:**
  - User IDs external (Steam ID, GOG ID, or local UUID)
  - Campaign IDs deterministic within user scope
  - Multi-user campaigns supported (campaign ID independent of user ID)
- **Status:** Not Started
- **Blockers:** RQ-SCHEMA-001
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q16, Q18)

#### RQ-SCHEMA-004: Campaign Forking/Cloning
- **Question:** Can campaigns be forked/cloned?
- **Owner:** Agent D
- **Priority:** Optional
- **Acceptance Threshold:**
  - Fork creates new campaign ID (preserves parent reference)
  - Cloned assets share same IDs (deduplication works)
  - Event logs diverge after fork point
- **Status:** Not Started
- **Blockers:** RQ-SCHEMA-001
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q17)

#### RQ-SCHEMA-005: Session Replay Determinism
- **Question:** Are session numbers deterministic or sequential? What happens if session is replayed?
- **Owner:** Agent D
- **Priority:** Important
- **Acceptance Threshold:**
  - Session numbers sequential (1, 2, 3...)
  - Replay creates branching timeline (session 5a, 5b)
  - Event IDs deterministic within session
- **Status:** Not Started
- **Blockers:** RQ-SCHEMA-001
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q7, Q8)

#### RQ-SCHEMA-006: Event Nesting
- **Question:** Do sessions nest? (e.g., "session 5, encounter 3")
- **Owner:** Agent D
- **Priority:** Optional
- **Acceptance Threshold:**
  - Events reference session ID (flat structure)
  - Encounter grouping via event tags (not nested IDs)
  - Simplifies replay and indexing
- **Status:** Not Started
- **Blockers:** RQ-SCHEMA-001
- **Related Documents:** `CANONICAL_ID_SCHEMA_DRAFT.md` (Q9)

#### R1-ARCH-001: Spark Swappability Doctrine + Contract
- **Question:** How should SPARK (LLM provider) be made user-swappable via configuration?
- **Owner:** Agent D
- **Priority:** CRITICAL (M2 Foundation)
- **Acceptance Threshold:**
  - Configuration-driven model selection (no hard-coded providers)
  - Capability manifest for all providers (json_mode, streaming, tool_calling)
  - Hot-swap determinism preserved (BOX outcomes identical with different SPARK)
  - 6 acceptance tests pass (TEST-001 through TEST-006)
- **Status:** ✅ **COMPLETE** (Doctrine + Contract + Acceptance Criteria documented)
- **Blockers:** None
- **Related Documents:**
  - `docs/doctrine/SPARK_SWAPPABLE_INVARIANT.md` (binding invariant)
  - `docs/specs/SPARK_PROVIDER_CONTRACT.md` (interface specification)
  - `docs/governance/M2_ACCEPTANCE_SPARK_SWAPPABILITY.md` (6 acceptance tests)
- **Date Completed:** 2026-02-10
- **Note:** Implementation deferred to M2 execution phase. Doctrine and contracts binding for M2+.

---

## 3. Critical Path

### Top 7 Questions That BLOCK M0 Planning

These questions MUST be answered before M0 planning can begin. Failure to resolve any of these = NO-GO.

| ID | Question | Owner | Acceptance Threshold | Dependencies |
|----|----------|-------|---------------------|--------------|
| **RQ-SCHEMA-001** | Canonical ID format definition | Agent D | Format, namespace, validation documented | None |
| **RQ-LLM-001** | LLM indexed memory architecture | Agent A | >90% retrieval accuracy, <200ms latency | RQ-SCHEMA-001 |
| **RQ-IMG-001** | Image critique model selection | Agent B | >80% bad image detection, <10% false positive | RQ-HW-001 |
| **RQ-HW-001** | Hardware baseline extraction | Agent D | Median spec extracted, cross-validated | None |
| **RQ-HW-003** | Model selection within budget | Agent D | Models locked (LLM, image, TTS, STT) | RQ-HW-001, RQ-HW-002 |
| **RQ-PREP-001** | Prep time budget | Agent D, C | ≤30 min target, ≤60 min acceptable | RQ-PREP-002, RQ-IMG-007 |
| **RQ-VOICE-001** | TTS quality baseline | Agent C, D | >70% acceptable, >95% intelligibility | RQ-HW-003 |

### Dependency Graph (Critical Path Only)

```
RQ-SCHEMA-001 (Canonical ID Format)
    ├── RQ-LLM-001 (Indexed Memory Architecture)
    │   └── RQ-LLM-002 (Query Interface)
    └── RQ-IMG-004 (Asset Content Addressing)

RQ-HW-001 (Hardware Baseline)
    ├── RQ-HW-002 (Minimum Spec CPU Fallback)
    │   └── RQ-HW-003 (Model Selection)
    │       ├── RQ-VOICE-001 (TTS Quality)
    │       ├── RQ-VOICE-002 (TTS Latency)
    │       ├── RQ-VOICE-003 (STT Latency)
    │       └── RQ-IMG-007 (Image Latency Median)
    └── RQ-IMG-001 (Image Critique)
        └── RQ-IMG-002 (Critique Failure Modes)

RQ-PREP-002 (Prep Task Breakdown)
    └── RQ-PREP-001 (Prep Time Budget)
        └── RQ-PREP-008 (Prep Failure UX)
```

**Total Critical Path Time Estimate:** 8-12 weeks (R0 Research Phase)

---

## 4. Deliverables Expected

### Per Question: What Artifact Answers It?

| Question Category | Deliverable Type | Example Artifact |
|-------------------|------------------|------------------|
| **Canonical ID Schema** | Design Document + Code | `aidm/schemas/canonical_ids.py`, `R0_CANONICAL_ID_SCHEMA.md` |
| **LLM Indexed Memory** | Architecture Doc + Prototype | `R0_INDEXED_MEMORY_ARCHITECTURE.md`, `aidm/memory/indexer.py` |
| **Image Critique** | Feasibility Report + Benchmark | `R0_IMAGE_CRITIQUE_FEASIBILITY.md`, `tests/test_image_critique.py` |
| **Hardware Baseline** | Analysis Report + Budget Worksheet | `R0_HARDWARE_BASELINE_SOURCES.md`, `R0_MODEL_BUDGETS.md` |
| **Prep Pipeline** | Prototype + Timing Study | `R0_PREP_PIPELINE_PROTOTYPE.md`, `tests/test_prep_timing.py` |
| **Voice Quality** | Playtest Report + Benchmark | `R0_TTS_STT_QUALITY_REPORT.md`, `tests/test_voice_quality.py` |
| **MVP Scope** | Triage Document | `MVP_SCOPE_M0_VS_M1.md` (finalized) |

### Deliverable Checklist (R0 Completion Gate)

**R0 is COMPLETE when all of the following exist:**

- [ ] `R0_CANONICAL_ID_SCHEMA.md` (format, examples, validation)
- [ ] `R0_INDEXED_MEMORY_ARCHITECTURE.md` (design + prototype validation)
- [ ] `R0_IMAGE_CRITIQUE_FEASIBILITY.md` (model selection + failure modes)
- [ ] `R0_HARDWARE_BASELINE_SOURCES.md` (Steam survey analysis)
- [ ] `R0_MODEL_BUDGETS.md` (GO/NO-GO model selection)
- [ ] `R0_PREP_PIPELINE_PROTOTYPE.md` (timing study + UX design)
- [ ] `R0_TTS_STT_QUALITY_REPORT.md` (playtest feedback + benchmarks)
- [ ] `MVP_SCOPE_M0_VS_M1.md` (finalized with stakeholder approval)
- [ ] All 7 critical path questions answered with GO acceptance thresholds met

**NO-GO Criteria:** If ANY critical path question fails acceptance threshold, R0 = NO-GO, M0 planning PAUSED.

---

## 5. Status Tracking

### Current Status Summary (2026-02-10)

**Complete (1):**
- RQ-LLM-001 (Indexed Memory Architecture) — Agent A — Certified PASSED with policy gaps documented

**In Progress (4):**
- RQ-SCHEMA-001 (Canonical ID Schema) — Agent D — Draft completed, needs validation
- RQ-HW-001 (Hardware Baseline) — Agent D — Draft completed, needs Steam survey data extraction
- RQ-HW-003 (Model Selection) — Agent D — Draft completed, needs hardware validation
- RQ-PREP-003 (Prep Job Idempotency) — Agent D — Addressed in Canonical ID Schema draft

**Not Started (43):**
- Remaining LLM & Indexed Memory questions (Agent A)
- All Image Generation & Critique questions (Agent B)
- All Voice I/O questions (Agents B, C, D)
- Remaining Prep Pipeline questions (Agent D, C)
- Remaining Hardware & Performance questions (Agent D, C)
- Remaining Architecture & Integration questions (Agent D)

**Blocked (0):**
- None currently (dependencies clear)

**Complete (0):**
- None yet (R0 just started)

### Next Actions (Week 1-2)

**Agent D (Research Orchestrator):**
1. Extract actual Steam Hardware Survey data (January 2025) — **Priority 1**
2. Finalize `R0_CANONICAL_ID_SCHEMA.md` with examples and validation logic — **Priority 1**
3. Validate hardware baseline on real hardware (median + minimum specs) — **Priority 2**
4. Create `R0_PREP_PIPELINE_PROTOTYPE.md` with timing estimates — **Priority 3**

**Agent A (LLM & Memory):**
1. ✅ **COMPLETE:** Design indexed memory architecture (RQ-LLM-001) — CERTIFIED PASSED
2. Document policy gaps (GAP-POL-01 through GAP-POL-04) — **Priority 1** (required before M1 close)
3. Prototype LLM query interface (RQ-LLM-002) — **Priority 2** (blocked pending RQ-LLM-001 policy gap documentation)
4. Validate LLM constraint adherence (RQ-LLM-006) — **Priority 3**

**Agent B (Image & Assets):**
1. Research image critique models (RQ-IMG-001) — **Priority 1**
2. Benchmark image generation latency (RQ-IMG-007, RQ-IMG-008) — **Priority 2**
3. Define asset variant handling (RQ-IMG-005) — **Priority 3**

**Agent C (Integration & UX):**
1. Define TTS quality threshold (RQ-VOICE-001) — **Priority 1**
2. Design prep phase failure UX (RQ-PREP-008) — **Priority 2**
3. Prototype UI layout integration (chat + ledger + grid) — **Priority 3**

---

## 6. Risk Summary

### High-Risk Questions (Failure = NO-GO)

| ID | Question | Risk | Mitigation |
|----|----------|------|------------|
| **RQ-LLM-001** | Indexed memory architecture | LLM cannot reliably query external records | Pivot to summarization or smaller campaign scope |
| **RQ-IMG-001** | Image critique model | No reliable critique model found | Pivot to human review or shipped asset library |
| **RQ-HW-003** | Model selection | Models don't fit median spec | Raise minimum spec or pivot to cloud inference |
| **RQ-PREP-001** | Prep time budget | Prep exceeds 30 minutes | Reduce asset scope or use shipped assets |
| **RQ-VOICE-001** | TTS quality | TTS quality unacceptable | Pivot to text-only or cloud TTS (ElevenLabs) |

### Medium-Risk Questions (Affects Architecture)

| ID | Question | Risk | Mitigation |
|----|----------|------|------------|
| **RQ-LLM-002** | LLM query interface | Retrieval accuracy <80% | Improve prompt engineering or switch indexing system |
| **RQ-IMG-002** | Image critique failure modes | False positive rate >30% | Add human override or lower quality threshold |
| **RQ-HW-002** | Minimum spec CPU fallback | Performance unusable on 8 GB RAM | Drop minimum spec support (16 GB required) |
| **RQ-PREP-002** | Prep task breakdown | Prep pipeline too complex | Simplify asset list or parallelize generation |

### Low-Risk Questions (Clarifications)

All "Optional" priority questions (14 total) are low-risk. These can be deferred to M1 without blocking M0.

---

## 7. Agent Ownership Matrix

| Agent | Questions Owned | Critical | Important | Optional |
|-------|-----------------|----------|-----------|----------|
| **Agent A** | 12 | 3 | 7 | 2 |
| **Agent B** | 10 | 3 | 5 | 2 |
| **Agent C** | 8 | 2 | 3 | 3 |
| **Agent D** | 18 | 7 | 7 | 4 |

### Agent Coordination Points

**Agent A ↔ Agent D:**
- RQ-LLM-001 depends on RQ-SCHEMA-001 (Canonical ID format)
- RQ-LLM-006 depends on RQ-HW-003 (Model selection)

**Agent B ↔ Agent D:**
- RQ-IMG-001 depends on RQ-HW-001 (VRAM budget)
- RQ-IMG-007 depends on RQ-HW-003 (Model selection)

**Agent C ↔ Agent D:**
- RQ-VOICE-001 depends on RQ-HW-003 (Model selection)
- RQ-PREP-008 depends on RQ-PREP-001 (Time budget)

**Agent A ↔ Agent B ↔ Agent C ↔ Agent D:**
- All agents need RQ-SCHEMA-001 (Canonical ID format) — **BLOCKER**

---

## 8. GO/NO-GO Decision Framework

### GO Criteria (Proceed to M0 Planning)

**MUST satisfy ALL 7 critical path questions:**

1. ✅ **RQ-SCHEMA-001:** Canonical ID format documented and validated
2. ✅ **RQ-LLM-001:** Indexed memory achieves >90% retrieval accuracy, <200ms latency
3. ✅ **RQ-IMG-001:** Image critique achieves >80% detection, <10% false positive
4. ✅ **RQ-HW-001:** Hardware baseline extracted and cross-validated
5. ✅ **RQ-HW-003:** Models selected within budget (LLM, image, TTS, STT)
6. ✅ **RQ-PREP-001:** Prep time ≤60 minutes (target: ≤30 min)
7. ✅ **RQ-VOICE-001:** TTS quality >70% acceptable, >95% intelligibility

**Timeline to GO:** 8-12 weeks (R0 Research Phase)

---

### NO-GO Criteria (Pause or Pivot)

**ANY ONE of the following triggers NO-GO:**

1. ❌ **Image critique infeasible** (no model >80% detection)
   - **Pivot:** Human review or shipped asset library
2. ❌ **Indexed memory fails** (retrieval accuracy <80%)
   - **Pivot:** Summarization or smaller campaign scope
3. ❌ **Hardware baseline unachievable** (models don't fit median spec)
   - **Pivot:** Raise minimum spec or cloud inference
4. ❌ **Prep time >60 minutes** (unacceptable UX)
   - **Pivot:** Reduce asset scope or shipped assets
5. ❌ **TTS quality unacceptable** (<70% acceptable rating)
   - **Pivot:** Text-only or cloud TTS (ElevenLabs)

---

## 9. Revision History

| Date | Version | Agent | Changes |
|------|---------|-------|---------|
| 2026-02-10 | 1.0 | Agent D | Initial master tracker created |
| 2026-02-11 | 1.1 | Opus (Agent 46) | R1 revision notice added; R1 reconciliation section appended |

---

## 10. R1 Reconciliation — Research Question Status After R1 Technology Validation

**Date:** 2026-02-11
**Author:** Opus (Agent 46)
**Source:** `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md`

The R1 Technology Stack Validation resolved model selections across all seven technology areas. This section reconciles the 49 R0 research questions against R1 findings to identify which are answered, which remain open, and which are no longer relevant.

### Status Categories

| Category | Count | Description |
|----------|-------|-------------|
| **R1-ANSWERED** | 7 | Model/technology selection fully resolved by R1; needs benchmarking only |
| **R1-PARTIALLY-ANSWERED** | 6 | R1 provides direction but design/implementation work remains |
| **ALREADY COMPLETE** | 2 | Finished before R1 (RQ-LLM-001, R1-ARCH-001) |
| **IN PROGRESS** | 4 | Was already being worked on (schema, hardware baseline) |
| **STILL OPEN** | 16 | Not addressed by R1, needs design/implementation work |
| **DEFERRED (M1+)** | 8 | M1+ scope, not blocking M0 |
| **SUPERSEDED** | 0 | No questions rendered irrelevant (all remain valid) |
| **STILL OPEN (CRITICAL)** | 6 | Open critical-path items that need resolution |

### R1-ANSWERED (7 questions — model selection resolved)

These questions have their technology/model selection answered by R1. They still need benchmarking on target hardware to confirm acceptance thresholds, but the "which model?" question is resolved.

| ID | Question | R1 Answer | Remaining Work |
|----|----------|-----------|----------------|
| **RQ-HW-003** | Model selection within budget | Qwen3 8B/14B/4B (LLM), SDXL Lightning NF4 (image), Kokoro (TTS), faster-whisper small.en (STT), ACE-Step (music) | Benchmark on target hardware |
| **RQ-IMG-001** | Image critique model selection | Heuristics + ImageReward + SigLIP (three-layer pipeline) | Benchmark F1/FPR/FNR on sample images |
| **RQ-VOICE-001** | TTS quality baseline | Kokoro TTS (4.0/5 quality, Apache 2.0, 150-300 MB RAM) | User testing with 10+ listeners |
| **RQ-VOICE-002** | TTS latency target | Kokoro: 100-300ms CPU. Well within <500ms target | Benchmark on minimum spec hardware |
| **RQ-VOICE-003** | STT latency target | faster-whisper small.en: 1100-1750ms (10s audio, CPU). Within <2000ms target | Benchmark on minimum spec hardware |
| **RQ-HW-004** | GPU requirement decision | Support integrated graphics; CPU fallback mandatory (15% of users). Qwen3 4B + SD 1.5 OpenVINO for CPU path | Confirmed by R1 model budget analysis |
| **RQ-HW-006** | Cloud vs local models | Local-first confirmed. All R1 selections are local models with permissive licenses | No remaining work |

### R1-PARTIALLY-ANSWERED (6 questions — direction clear, work remains)

| ID | Question | What R1 Resolved | What Remains |
|----|----------|------------------|--------------|
| **RQ-HW-001** | Hardware baseline extraction | Steam survey data referenced; median/minimum specs defined | Formal extraction document needs completion |
| **RQ-HW-002** | Minimum spec CPU fallback | Model selections confirmed (Qwen3 4B, SD 1.5 OpenVINO, Kokoro, faster-whisper base.en) | CPU benchmark testing needed |
| **RQ-IMG-002** | Image critique failure modes | Three-layer pipeline defines graduated failure handling | Documented failure mode catalog still needed |
| **RQ-IMG-007** | Image generation latency (median) | SDXL Lightning NF4: 4-6 sec at 768x768 on RTX 3060 (R1 estimate) | Benchmark on actual target hardware |
| **RQ-IMG-008** | Image generation latency (minimum) | SD 1.5 + LCM LoRA OpenVINO: 8-20 sec on CPU (R1 estimate) | Benchmark on actual minimum spec hardware |
| **RQ-PREP-002** | Prep phase task breakdown | Sequential pipeline defined (LLM → image → critique → music → SFX → TTS) | Timing study, asset list, resource allocation per task |

### ALREADY COMPLETE (2 questions)

| ID | Question | Status |
|----|----------|--------|
| **RQ-LLM-001** | LLM indexed memory architecture | Certified PASSED (policy gaps documented) |
| **R1-ARCH-001** | Spark swappability doctrine + contract | COMPLETE (doctrine + contract + 6 acceptance tests) |

### IN PROGRESS (4 questions — work predates R1)

| ID | Question | Current State |
|----|----------|---------------|
| **RQ-SCHEMA-001** | Canonical ID format definition | Draft completed, needs validation |
| **RQ-SCHEMA-002** | ID collision probability | Addressed in canonical ID schema draft |
| **RQ-LLM-007** | LLM output determinism | Addressed in canonical ID schema draft |
| **RQ-PREP-003** | Prep job idempotency | Addressed in canonical ID schema draft |

### STILL OPEN — CRITICAL (6 questions — must resolve for M0)

These are the remaining critical-path items that R1 did not address. They require design work, prototyping, or user testing.

| ID | Question | Why R1 Didn't Resolve | Next Step |
|----|----------|-----------------------|-----------|
| **RQ-LLM-002** | LLM query interface (prompt eng vs function calling vs RAG) | Architecture decision, not model selection | Design query interface against Qwen3 8B capabilities |
| **RQ-LLM-006** | LLM constraint adherence (D&D 3.5e rules, <5% hallucination) | Requires evaluation with selected model | Test Qwen3 8B against D&D rule corpus |
| **RQ-IMG-003** | Image quality threshold (>70% "acceptable") | Requires user testing with SDXL Lightning output | Generate samples, run playtest |
| **RQ-PREP-001** | Prep time budget (≤30 min target) | Requires end-to-end timing with sequential pipeline | **CRITICAL BLOCKER — Priority 4 prep pipeline prototype** |
| **RQ-IMG-010** | Bounded regeneration policy | Design decision, not model selection | Define max attempts, backoff, fallback rules |
| **RQ-IMG-009** | Image generation failure fallback | Design decision | Define placeholder strategy, retry UX |

### STILL OPEN — IMPORTANT (10 questions)

| ID | Question | Category | Notes |
|----|----------|----------|-------|
| **RQ-LLM-003** | Entity renames in indexed memory | LLM/Memory | Blocked on RQ-LLM-001 (complete) — ready to start |
| **RQ-LLM-004** | Deleted entities in index | LLM/Memory | Blocked on RQ-LLM-001 (complete) — ready to start |
| **RQ-LLM-005** | Entity ID aliasing | LLM/Memory | Blocked on RQ-SCHEMA-001 (in progress) |
| **RQ-LLM-008** | Session recap summarization | LLM/Memory | Blocked on RQ-LLM-001 (complete) — ready to start |
| **RQ-LLM-010** | Duplicate NPC naming | Schema | In progress via canonical ID schema |
| **RQ-LLM-011** | Entity persistence across sessions | Schema | In progress via canonical ID schema |
| **RQ-IMG-004** | Asset content addressing | Schema | In progress via canonical ID schema |
| **RQ-IMG-005** | Asset variant handling | Image | Blocked on RQ-IMG-004 |
| **RQ-HW-005** | Cross-platform priority | Hardware | M0 = Windows-only (already decided) |
| **RQ-SCHEMA-003** | Campaign ID user scoping | Schema | Blocked on RQ-SCHEMA-001 |
| **RQ-SCHEMA-005** | Session replay determinism | Schema | Blocked on RQ-SCHEMA-001 |
| **RQ-PREP-004** | Failed prep job retry | Prep | Blocked on RQ-PREP-002 |
| **RQ-PREP-008** | Prep phase failure UX | Prep | Blocked on RQ-PREP-001 |

### DEFERRED — M1+ SCOPE (8 questions)

These are explicitly scoped for M1 or later. Not blocking M0.

| ID | Question | Deferred To | Notes |
|----|----------|-------------|-------|
| **RQ-LLM-009** | Knowledge tome progressive detail | M1 | Feature design, not R0 research |
| **RQ-LLM-012** | Entity rename side effects | M1 | Depends on RQ-LLM-003 |
| **RQ-VOICE-004** | TTS persona switching | M1 | Single persona for M0; Kokoro has 6-10 voices for M1 |
| **RQ-VOICE-005** | Multilingual STT accuracy | M1 | M0 = English-only; faster-whisper supports 50+ languages |
| **RQ-VOICE-006** | Multilingual TTS quality | M1 | M0 = English-only |
| **RQ-IMG-006** | Shared cache asset IDs | M1 | Optional optimization |
| **RQ-SCHEMA-004** | Campaign forking/cloning | M1+ | Optional feature |
| **RQ-SCHEMA-006** | Event nesting | M1+ | Optional structural decision |
| **RQ-PREP-005** | Prep job dependencies (DAG) | M1+ | Optional optimization |
| **RQ-PREP-006** | Prep job regen with different params | M1+ | Optional feature |
| **RQ-PREP-007** | Versioned asset handling | M1+ | Optional feature |

### Summary: What R1 Changed

**Before R1:** 43 of 49 questions "Not Started." No model selections locked. No technology validated.

**After R1:**
- **7 questions answered** (model selections resolved)
- **6 questions partially answered** (direction clear, benchmarking needed)
- **2 questions already complete** (predated R1)
- **4 questions in progress** (canonical ID schema work)
- **6 critical questions still open** (design work, user testing, prep pipeline timing)
- **8+ questions deferred** (M1+ scope)

**The single most important remaining open item is RQ-PREP-001 (Prep Time Budget)**, which requires the prep pipeline prototype (Priority 4 / R0-DEC-035). This is the critical blocker.

---

**END OF R0 MASTER TRACKER** — All research questions indexed, owners assigned, acceptance thresholds defined.
