# R1 Technology Stack Validation — Executive Summary for PM

**Source:** `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` (518 lines, full report)
**Date:** 2026-02-11
**Author:** Opus (Agent 46)
**Status:** Complete

---

## What R1 Is

R1 is the technology validation phase. It answers "which specific model/library/tool do we use for each technology area?" with concrete, implementation-ready recommendations. R0 asked the research questions. R1 answered them.

## All 7 Areas Resolved

| # | Area | R0 Choice | R1 Recommendation | License | VRAM |
|---|------|-----------|-------------------|---------|------|
| 1 | **LLM** | Mistral 7B / Phi-3 | **Qwen3 8B** (median) / **14B** (high) / **4B** (low) | Apache 2.0 | 6 / 10 / 3 GB |
| 2 | **Image Gen** | SD 1.5 | **SDXL Lightning NF4** (GPU) / SD 1.5 (CPU fallback) | Apache 2.0 | 3.5-4.5 GB |
| 3 | **Image Critique** | Heuristics + CLIP B/32 | **Heuristics + ImageReward + SigLIP** (three-layer) | CPU / MIT / Apache 2.0 | 0 + 1.0 + 0.6 GB |
| 4 | **TTS** | Piper / Coqui | **Kokoro** (ONNX, CPU) / Piper fallback | Apache 2.0 | 0 (150-300 MB RAM) |
| 5 | **STT** | Whisper Base | **faster-whisper small.en** (CTranslate2 INT8) | MIT | 0 (400-700 MB RAM) |
| 6 | **Music** | TBD | **ACE-Step** (prep-time generative, PRIMARY) + curated fallback | Apache 2.0 | 6-8 GB |
| 7 | **SFX** | TBD | **Curated library** (generative blocked by non-commercial licensing) | Various CC0/RF | 0 |

## Key Architecture Correction

**AIDM is a prep-time sequential pipeline, NOT simultaneous model loading.**

During campaign prep, models load one at a time:
```
Phase 1: LLM (Qwen3 8B, ~6 GB) → Generate content → Unload
Phase 2: Image Gen (SDXL Lightning, ~4 GB) → Generate portraits/scenes → Unload
Phase 3: Image Critique (ImageReward, ~1 GB) → Score images → Unload
Phase 4: Music Gen (ACE-Step, ~6-8 GB) → Generate music → Unload
Phase 5: SFX (curated library) → Load from disk → No model
Phase 6: TTS (Kokoro, CPU) → Generate narration → CPU only
```

**Peak VRAM = single largest model (~6-8 GB), not sum of all models.**

This is why generative music is viable on consumer hardware — ACE-Step gets full GPU during its phase.

## Prep Pipeline Timing

| Scenario | Median Spec | Minimum Spec |
|----------|-------------|-------------|
| Full session (2hr) | **~9 min** | **~17 min** |
| Minimal session (1hr) | **~3.5 min** | **~7 min** |
| Target | ≤30 min | ≤30 min |

**Bottleneck:** LLM content generation (39% of time on median, 71% on minimum).

## Music: Generative Is PRIMARY

**For capable hardware (6+ GB VRAM, "Recommended" tier):**
- **ACE-Step** (Apache 2.0, 3.5B params) generates up to 4 min of music per clip
- ~20-40 seconds per 60s clip on RTX 3060
- Supports all mainstream music styles, vocals + instrumental

**For minimum spec (no GPU, "Baseline" tier):**
- **Curated royalty-free library** (Kevin MacLeod CC BY 3.0, OpenGameArt CC0, FreePD CC0)
- 30-45 tracks, 50-200 MB on disk
- Zero compute cost

**This is Thunder's explicit strategic intent. Do not invert this framing.**

## SFX: Curated Is PRIMARY (Licensing Blocker)

Unlike music, there is **no permissively-licensed generative SFX model** as of February 2026:
- TangoFlux: Stability AI Community License (NO)
- Tango 2: CC-BY-NC-SA (NO)
- AudioGen: CC-BY-NC (NO)
- Stable Audio Open: Stability AI Community License (NO)

The prep pipeline is architecturally ready for generative SFX. When a permissively-licensed model appears, it slots in. Until then, curated library is correct.

## Decisions Reversed or Updated

| Decision | Old Status | New Status |
|----------|-----------|------------|
| R0-DEC-025 (SDXL NO-GO) | NO-GO | **REVERSED → GO** (NF4 quantization) |
| R0-DEC-035 (Prep Pipeline) | BLOCKED | **PROJECTED PASS** (~9 min median) |
| R0-DEC-020 (LLM Median) | Mistral 7B | **Updated → Qwen3 8B** |
| R0-DEC-026 (TTS) | Coqui/Piper | **Updated → Kokoro** |
| R0-DEC-028 (STT Median) | Whisper Base | **Updated → faster-whisper small.en** |

## R0 Research Questions Status (49 total)

| Category | Count |
|----------|-------|
| R1-Answered | 7 |
| R1-Partially-Answered | 6 |
| Already Complete | 2 |
| In Progress | 4 |
| Still Open (Critical) | 6 |
| Still Open (Important) | 13 |
| Deferred (M1+) | 11 |

**Most important open item:** RQ-PREP-001 (Prep Time Budget) — needs hardware benchmarking.

---

**For full details, licensing verification, model comparison tables, and hardware budget analysis, read the complete report at `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md`.**
