# Aegis Rehydration State

> Warm resume. Assume continuity. Current state banner below.

**Update rules:**
- Thunder or Opus updates this file whenever project state changes
- Aegis should confirm he has read this file at the start of every new window
- Keep it short — this is a state snapshot, not a design doc

---

## STATE BANNER

```
PHASE:       M3 (Immersion Layer v1) — design phase COMPLETE, implementation phase active
FROZEN:      M0, M1, M2 (Persistence v1.1)
COMPLETED:   All design WOs complete. Layer 1 (Heuristics) implemented. Audio stubs integrated.
             LLM Query Interface designed. 15 PM decisions this session.
ACTIVE:      None — all agents on standby
IDLE:        Sonnet A, B, C, D, E — awaiting next dispatch
BLOCKER:     None
TESTS:       1823 passing, 0 failures
INBOX:       CLEAN
```

---

## Last Updated: 2026-02-11 (PM Session — Opus Acting PM)

## PM Decisions Made This Session

1. **Audio WOs (EVAL-01 + INT-01): APPROVED** — All 6 verification points pass. Generative-primary framing correct. Sonnet-D may proceed with EVAL-01 execution.
2. **Image Critique WO: REJECTED & RESCOPED** — Sonnet-C's deliverables were for wrong models (Spark vision + CLIP). R1 specifies Heuristics + ImageReward + SigLIP. New WO-M3-IMAGE-CRITIQUE-02 issued. Sonnet-C's work was thorough but on outdated scope — not Sonnet-C's fault.
3. **M2 Persistence WO: CLOSED** — Sonnet-A correctly identified WO-M2-PERSISTENCE-01 as duplicate. M2 persistence is complete, frozen at v1.1, 72 tests passing.
4. **Spark Adapter Tests: FIXED** — 6 failing tests had stale Mistral/Phi model IDs. Updated to Qwen3/Gemma3. Full suite now 1777/1777 passing.
5. **Roadmap v3.2: CONFIRMED LIVE** — Amendment already applied by Sonnet-D. M3 audio language reads "AI-generated (ACE-Step) during prep for capable hardware."
6. **WO-M3-IMAGE-CRITIQUE-02 (Sonnet-C): APPROVED** — All 4 design docs delivered (~2,800 lines). R1-aligned: Heuristics + ImageReward + SigLIP. Standalone Layer 1 confirmed. VRAM budget validated. Protocol conformance verified. Zero schema modifications. Ready for implementation phase.
7. **WO-R0-CRITICAL-RESEARCH-DESIGN-01 (Sonnet-B): ALL 3 DRAFTS APPROVED** — RQ-LLM-002 (LLM Query Interface), RQ-IMG-010 (Bounded Regeneration), RQ-IMG-009 (Failure Fallback). All well-scoped, R1-aligned, ready for dispatch.
8. **WO-M3-AUDIO-EVAL-01 (Sonnet-D): APPROVED** — All 5 evaluation documents delivered (~1,550 lines). ACE-Step validated as primary generative music. Curated library specified as fallback. SFX curated-only (licensing blocker). Hardware tier mapping correct. Integration planning complete. WO-M3-AUDIO-INT-01 now UNBLOCKED.
9. **PM Inbox Policy: CLEAN INBOX** — Inbox root reserved for incoming deliverables only. All reviewed/reference docs moved to reviewed/. Dispatch packets delivered inline (conversation) not as files.
10. **WO-M3-MODEL-REF-CLEANUP-01 (Sonnet-A): APPROVED** — 47 stale model references replaced across 4 governance docs. Mistral→Qwen3, Phi-2→Qwen3 4B, Whisper→faster-whisper, Coqui→Kokoro, SD 1.5→SDXL Lightning. Sonnet-A now executing WO-RQ-LLM-002.
11. **WO-RQ-IMG-010 (Sonnet-B): APPROVED** — Bounded Regeneration Policy design (~410 lines). GPU: 4 attempts within 60s, CPU: 3 attempts within 120s. Backoff schedule, convergence detection, dimension-specific adjustments. Design doc at `docs/design/BOUNDED_REGENERATION_POLICY.md`. Sonnet-B now IDLE.
12. **WO-M3-HEURISTICS-IMPL-01 (Sonnet-E): APPROVED** — HeuristicsImageCritic implementation (626 lines). 29 new tests, all passing. Factory registration complete. Performance <100ms verified. Tests now 1823/1823. CPU-only Layer 1 is live.
13. **WO-RQ-IMG-009 (Sonnet-C): APPROVED** — Image Generation Failure Fallback design (~1,100 lines). Four-tier fallback hierarchy (shipped art → generic → solid color → text-only). 5 failure triggers. Tier-specific degradation. Archetype matching. Design doc at `docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md`. Sonnet-C now IDLE.
14. **WO-RQ-LLM-002 (Sonnet-A): APPROVED** — LLM Query Interface Design (~798 lines). Prompt templates (narration/query/structured), system prompt architecture, GBNF grammar constraints, GuardedNarrationService integration, error handling with retry budget, acceptance criteria. Design doc at `docs/design/LLM_QUERY_INTERFACE.md`. Sonnet-A now IDLE.
15. **WO-M3-AUDIO-INT-01 (Sonnet-D): APPROVED** — Audio pipeline integration (2,054 lines new code). Audio schemas, hardware tier detection, music generator stubs (ACE-Step + curated), SFX library stub, audio mixer stub, prep pipeline Phase 4 integration. 17 new tests. All stubs — real integration in M3 sprints 2-4. Sonnet-D now IDLE.

## Pipeline Status

### Completed Work Orders

| WO ID | Agent | Completed | Key Output |
|-------|-------|-----------|------------|
| WO-M2-01 | Sonnet A | 2026-02-10 | M2 Persistence Architecture Freeze v1.1 |
| WO-M3-PREP-01 | Sonnet B | 2026-02-11 | Prep pipeline prototype (sequential model loading) |
| WO-R1-RESEARCH-UPDATE-01 | Opus | 2026-02-11 | R1 Technology Stack Validation (7 areas) |
| WO-M3-IMAGE-CRITIQUE-02 | Sonnet C | 2026-02-11 | APPROVED — 4 design docs: Heuristics + ImageReward + SigLIP + Prep Integration |
| WO-R0-CRITICAL-RESEARCH-DESIGN-01 | Sonnet B | 2026-02-11 | APPROVED — 3 draft WOs: RQ-LLM-002, RQ-IMG-010, RQ-IMG-009 |
| WO-M3-AUDIO-EVAL-01 | Sonnet D | 2026-02-11 | APPROVED — 5 eval docs: ACE-Step, curated music, SFX, tier mapping, integration |
| WO-M3-MODEL-REF-CLEANUP-01 | Sonnet A | 2026-02-11 | APPROVED — 47 stale model refs replaced across 4 governance docs |
| WO-RQ-IMG-010 | Sonnet B | 2026-02-11 | APPROVED — Bounded Regeneration Policy design (~410 lines) |
| WO-RQ-IMG-009 | Sonnet C | 2026-02-11 | APPROVED — Failure Fallback design (~1,100 lines) |
| WO-M3-HEURISTICS-IMPL-01 | Sonnet E | 2026-02-11 | APPROVED — HeuristicsImageCritic implementation (626 lines, 29 tests) |
| WO-RQ-LLM-002 | Sonnet A | 2026-02-11 | APPROVED — LLM Query Interface Design (~798 lines) |
| WO-M3-AUDIO-INT-01 | Sonnet D | 2026-02-11 | APPROVED — Audio pipeline integration (2,054 lines, 17 tests, stubs) |

### Active Work Orders

None — all agents on standby.

### Ready for Dispatch

Implementation WOs available (designs all approved):
- **WO-M3-IMAGEREWARD-IMPL-02**: Layer 2 ImageReward adapter implementation
- **WO-M3-SIGLIP-IMPL-03**: Layer 3 SigLIP adapter implementation
- **WO-M3-BOUNDED-REGEN-IMPL**: Bounded Regeneration implementation
- **WO-M3-FAILURE-FALLBACK-IMPL**: Failure Fallback implementation
- **WO-M3-AUDIO-CURATED-MUSIC**: Curated music library curation (M3 Sprint 2)
- **WO-M3-AUDIO-SFX-CURATION**: SFX library curation (M3 Sprint 3)

### Closed / Rejected

| WO ID | Reason |
|-------|--------|
| WO-M3-IMAGE-CRITIQUE-01 | SUPERSEDED by WO-M3-IMAGE-CRITIQUE-02 (wrong model selections) |
| WO-M2-PERSISTENCE-01 | DUPLICATE — M2 persistence already complete and frozen |

### Agents

| Agent | State | Notes |
|-------|-------|-------|
| Sonnet A | IDLE | WO-RQ-LLM-002 complete and approved. Awaiting next dispatch. |
| Sonnet B | IDLE | WO-RQ-IMG-010 complete and approved. Awaiting next dispatch. |
| Sonnet C | IDLE | WO-RQ-IMG-009 complete and approved. Awaiting next dispatch. |
| Sonnet D | IDLE | WO-M3-AUDIO-INT-01 complete and approved. Awaiting next dispatch. |
| Sonnet E | IDLE | WO-M3-HEURISTICS-IMPL-01 complete and approved. Awaiting next dispatch. |
| Opus | ACTIVE | Acting PM. All 5 agents on standby. |
| Aegis | DOWN | Opus acting as PM this session. |

---

## R1 Technology Stack — All 7 Areas Resolved

| Area | Model | VRAM | License |
|------|-------|------|---------|
| LLM | Qwen3 8B / 14B / 4B | 6 / 10 / 3 GB | Apache 2.0 |
| Image Gen | SDXL Lightning NF4 | 3.5-4.5 GB | Apache 2.0 |
| Image Critique | Heuristics + ImageReward + SigLIP | 0 + 1.0 + 0.6 GB | CPU / MIT / Apache 2.0 |
| TTS | Kokoro (ONNX, CPU) | 0 GB | Apache 2.0 |
| STT | faster-whisper small.en | 0 GB | MIT |
| Music | ACE-Step (prep-time) | 6-8 GB | Apache 2.0 |
| SFX | Curated library | 0 GB | Various CC0/RF |

---

## Remaining Work

### Priority 1: Implementation WOs (designs approved, agents available)
- **Layer 2 ImageReward adapter** — GPU, ~1 GB VRAM, text-image alignment scoring
- **Layer 3 SigLIP adapter** — GPU, ~0.6 GB, identity consistency via reference comparison
- **Bounded Regeneration implementation** — Retry logic, backoff schedule, convergence detection
- **Failure Fallback implementation** — Fallback selection, archetype matching, solid color generation
- **Audio curated music library** — 30-45 tracks, mood tagging, library index
- **Audio SFX library curation** — 200-500 sounds, semantic key taxonomy

### Priority 2: Backlog
- R0 critical research questions requiring hardware (RQ-PREP-001, RQ-LLM-006, RQ-IMG-003 — need Thunder)
- LLM Query Interface implementation (design complete, needs M3 implementation WO)
- Audio mixer real implementation (M3 Sprint 4, needs sounddevice)
- ACE-Step model integration (M3.5+, needs model download)

---

## Key Reference Files

- `pm_inbox/reviewed/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` — R1 model selections (518 lines)
- `pm_inbox/reviewed/SONNET-C_WO-M3-IMAGE-CRITIQUE-02_heuristics_design.md` — APPROVED Layer 1 design
- `pm_inbox/reviewed/SONNET-C_WO-M3-IMAGE-CRITIQUE-02_imagereward_design.md` — APPROVED Layer 2 design
- `pm_inbox/reviewed/SONNET-C_WO-M3-IMAGE-CRITIQUE-02_siglip_design.md` — APPROVED Layer 3 design
- `pm_inbox/reviewed/SONNET-C_WO-M3-IMAGE-CRITIQUE-02_prep_integration.md` — APPROVED prep integration
- `pm_inbox/reviewed/SONNET-B_WO-RQ-IMG-010_completion.md` — APPROVED Bounded Regen design
- `pm_inbox/reviewed/SONNET-C_WO-RQ-IMG-009_completion.md` — APPROVED Failure Fallback design
- `pm_inbox/reviewed/SONNET-E_WO-M3-HEURISTICS-IMPL-01_completion.md` — APPROVED Layer 1 implementation
- `pm_inbox/reviewed/SONNET-A_WO-RQ-LLM-002_completion.md` — APPROVED LLM Query Interface design
- `pm_inbox/reviewed/SONNET-D_WO-M3-AUDIO-INT-01_completion.md` — APPROVED Audio pipeline integration
- `docs/design/BOUNDED_REGENERATION_POLICY.md` — Bounded Regen design doc (~410 lines)
- `docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md` — Failure Fallback design doc (~1,100 lines)
- `docs/design/LLM_QUERY_INTERFACE.md` — LLM Query Interface design doc (~798 lines)
- `docs/AIDM_EXECUTION_ROADMAP_V3.md` — Canonical roadmap (v3.2 live)

---

## Protocol

When Aegis opens a new context window, Thunder drops the `aegis_rehydration/` folder contents. Aegis should:
1. Read `SESSION_BOOTSTRAP.md` first (posture + state banner)
2. Read this file second (pipeline details)
3. Read `STANDING_OPS_CONTRACT.md` third (behavioral rules)
4. Read `R1_TECHNOLOGY_STACK_SUMMARY.md` fourth (R1 model selections)
5. Read `OPUS_ACTION_REPORT_2026-02-11.md` fifth (action items)
6. Confirm: "I see [N] active items, waiting on [X]. State: [status]."
7. Resume from the current state — do NOT re-plan anything already planned
