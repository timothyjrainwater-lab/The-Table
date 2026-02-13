# R0 Prep Pipeline Timing Study — Sequential Model Loading Feasibility
## Answering RQ-PREP-001 and R0-DEC-035

**Document Type:** R0 Research / Timing Analysis
**Purpose:** Validate that sequential prep pipeline can complete within ≤30 minute target for a 2-hour session
**Author:** Opus (Agent 46)
**Date:** 2026-02-11
**Status:** PROJECTED (needs hardware benchmarking to confirm)
**References:** `aidm/core/prep_pipeline.py` (prototype), `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` (R1 model selections)

---

## 1. Context

### The Critical Question

**RQ-PREP-001:** How long should session prep take? Target: ≤30 minutes for a 2-hour session.

**R0-DEC-035:** Prep phase pipeline must be prototyped and timing validated.

### What Exists

The prep pipeline prototype (`aidm/core/prep_pipeline.py`, WO-M3-PREP-01) implements the sequential model loading architecture with stub implementations. The architecture is validated. What remains is timing analysis using R1 model selections on target hardware.

### Pipeline Architecture (from prototype)

```
Phase 1: LLM (Qwen3 8B) → Generate NPCs, encounters, dialogues → Unload
Phase 2: Image Gen (SDXL Lightning NF4) → Generate portraits, scenes → Unload
Phase 3: Image Critique (ImageReward) → Score images, reject bad ones → Unload
Phase 4: Music Gen (ACE-Step) → Generate mood tracks → Unload
Phase 5: SFX (Curated Library) → Load from disk → No model needed
Phase 6: TTS (Kokoro) → Generate narration audio → CPU, concurrent possible
```

---

## 2. Asset Scope Definition

### Typical 2-Hour Session Requires

Based on D&D 3.5e session structure analysis:

| Asset Type | Count | Description |
|-----------|-------|-------------|
| **NPC Profiles** | 5-8 | Name, description, traits, dialogue hooks (JSON) |
| **NPC Portraits** | 5-8 | 512x512 character portraits (PNG) |
| **Scene Backgrounds** | 3-5 | 1024x768 location art (PNG) |
| **Combat Encounter Plans** | 1-3 | Stat blocks, tactics, CR validation (JSON) |
| **Music Tracks** | 3-5 | 60-120s mood loops (OGG) |
| **Sound Effects** | 15-25 | Combat, ambient, event sounds (OGG, from curated library) |
| **Narration Clips** | 5-10 | Scene descriptions, NPC introductions (WAV/OGG) |

### Minimal Session (1-hour, simple)

| Asset Type | Count |
|-----------|-------|
| NPC Profiles | 3 |
| NPC Portraits | 3 |
| Scene Backgrounds | 2 |
| Combat Encounters | 1 |
| Music Tracks | 2 |
| Sound Effects | 10 |
| Narration Clips | 3 |

### Full Session (2-hour, complex)

| Asset Type | Count |
|-----------|-------|
| NPC Profiles | 8 |
| NPC Portraits | 8 |
| Scene Backgrounds | 5 |
| Combat Encounters | 3 |
| Music Tracks | 5 |
| Sound Effects | 25 |
| Narration Clips | 10 |

---

## 3. Per-Phase Timing Projections

### Phase 1: LLM Content Authoring (Qwen3 8B Q4_K_M)

**What it generates:** NPC profiles, encounter stat blocks, dialogue hooks, scene descriptions, narration scripts.

**Model:** Qwen3 8B Instruct Q4_K_M via llama.cpp
**VRAM:** ~6 GB
**Load time:** 5-15 seconds

**Token Estimates:**

| Content | Tokens (est.) | Count | Total Tokens |
|---------|---------------|-------|-------------|
| NPC Profile | ~200 tokens | 8 | 1,600 |
| Combat Encounter | ~300 tokens | 3 | 900 |
| Scene Description | ~150 tokens | 5 | 750 |
| Dialogue Hooks | ~100 tokens | 8 | 800 |
| Narration Scripts | ~80 tokens | 10 | 800 |
| **Total** | | | **4,850 tokens** |

**Generation Speed (R1 estimates):**
- Median spec (6-8 cores + GPU offload): 20-30 tokens/sec
- Minimum spec (4 cores, CPU only): 5-10 tokens/sec

**Projected Time:**

| Spec | Tokens | Speed | Generation Time | Model Load | Total Phase 1 |
|------|--------|-------|-----------------|------------|---------------|
| **Median** | 4,850 | 25 tok/s | ~194s (~3.2 min) | 10s | **~3.5 min** |
| **Minimum** | 4,850 | 7 tok/s | ~693s (~11.5 min) | 15s | **~12 min** |

**Notes:**
- Includes prompt overhead (~20% additional tokens for system prompts, context)
- Batched generation (multiple NPCs per call) reduces prompt overhead
- Content is structured JSON — shorter than prose narration

---

### Phase 2: Image Generation (SDXL Lightning NF4)

**What it generates:** NPC portraits, scene backgrounds, location art.

**Model:** SDXL Lightning NF4 (bitsandbytes), 4 inference steps
**VRAM:** ~3.5-4.5 GB
**Load time:** 10-30 seconds (first load), ~5s (cached)

**Generation Speed (R1 estimates):**
- Median spec (6-8 GB VRAM): 4-6 sec per image at 768x768
- Minimum spec (CPU, OpenVINO): 8-20 sec per image at 512x512

**Projected Time:**

| Spec | Portraits | Scenes | Per-Image | Total Images | Gen Time | Load | Total Phase 2 |
|------|-----------|--------|-----------|-------------|----------|------|---------------|
| **Median** | 8 | 5 | 5s | 13 | 65s (~1.1 min) | 15s | **~1.5 min** |
| **Minimum (CPU)** | 8 | 5 | 15s | 13 | 195s (~3.3 min) | 20s | **~3.5 min** |

**Notes:**
- SDXL Lightning uses only 4 steps (vs 20 for SD 1.5) — speed advantage
- Minimum spec uses SD 1.5 + LCM LoRA via OpenVINO (not SDXL)
- No batch generation — sequential per image (VRAM constraint)

---

### Phase 3: Image Critique (ImageReward FP16)

**What it does:** Scores each generated image. Rejects below threshold. Triggers regeneration if needed.

**Model:** ImageReward FP16
**VRAM:** ~1.0 GB
**Load time:** 5-10 seconds

**Critique Speed:** ~100ms per image on GPU

**Projected Time:**

| Spec | Images | Per-Image | Critique Time | Regen (est. 20% fail) | Total Phase 3 |
|------|--------|-----------|---------------|----------------------|---------------|
| **Median** | 13 | 100ms | 1.3s | 3 images × 5s = 15s | **~25s** |
| **Minimum** | 13 | heuristics only, 85ms | 1.1s | 3 images × 15s = 45s | **~55s** |

**Notes:**
- ImageReward loads and unloads quickly (~1 GB)
- If >3 images fail, fallback to accept with warning
- Bounded regeneration: max 3 attempts per image (R0-DEC-010)
- Critique + regen is fast relative to initial generation

---

### Phase 4: Music Generation (ACE-Step)

**What it generates:** Mood-specific music loops for campaign scenes.

**Model:** ACE-Step (Apache 2.0, 3.5B params)
**VRAM:** ~6-8 GB
**Load time:** 10-20 seconds

**Generation Speed (R1 estimates):**
- Median spec (RTX 3060): ~20-40 seconds per 60-second clip
- Minimum spec: Curated library (no generation, instant)

**Projected Time:**

| Spec | Tracks | Per-Track | Gen Time | Load | Total Phase 4 |
|------|--------|-----------|----------|------|---------------|
| **Median** | 5 | 30s | 150s (2.5 min) | 15s | **~3 min** |
| **Minimum** | 5 | 0s (curated) | 0s | 0s | **~0s** |

**Notes:**
- ACE-Step generates up to 4 min per clip; 60-120s loops are shorter
- Minimum spec uses curated royalty-free library — no generation needed
- Music generation is the most variable phase (depends heavily on GPU)

---

### Phase 5: Sound Effects (Curated Library)

**What it does:** Loads pre-curated SFX from disk. No model loading needed.

**Projected Time:** All specs: **<5 seconds** (file copy/indexing only)

---

### Phase 6: TTS Narration (Kokoro, CPU)

**What it generates:** Audio narration clips for scene descriptions, NPC introductions.

**Model:** Kokoro TTS (ONNX, CPU-based)
**RAM:** 150-300 MB
**No GPU needed** — runs on CPU

**Generation Speed:** 100-300ms per narration clip (CPU)

**Projected Time:**

| Spec | Clips | Per-Clip | Total Phase 6 |
|------|-------|----------|---------------|
| **Median** | 10 | 200ms | **~2s** |
| **Minimum** | 10 | 300ms | **~3s** |

**Notes:**
- Kokoro is extremely fast — TTS is not a bottleneck
- Can run concurrently with other CPU-light phases
- Audio encoding (WAV → OGG) adds ~50ms per clip

---

## 4. Total Prep Time Projection

### Full Session (8 NPCs, 5 scenes, 3 encounters, 5 music tracks, 10 narrations)

| Phase | Median Spec | Minimum Spec |
|-------|-------------|-------------|
| 1. LLM Content | 3.5 min | 12.0 min |
| 2. Image Gen | 1.5 min | 3.5 min |
| 3. Image Critique | 0.4 min | 0.9 min |
| 4. Music Gen | 3.0 min | 0 min (curated) |
| 5. SFX | 0.1 min | 0.1 min |
| 6. TTS | 0.03 min | 0.05 min |
| **Pipeline Overhead** | 0.5 min | 0.5 min |
| **TOTAL** | **~9 min** | **~17 min** |

### Minimal Session (3 NPCs, 2 scenes, 1 encounter, 2 music tracks, 3 narrations)

| Phase | Median Spec | Minimum Spec |
|-------|-------------|-------------|
| 1. LLM Content | 1.5 min | 5.0 min |
| 2. Image Gen | 0.5 min | 1.5 min |
| 3. Image Critique | 0.1 min | 0.3 min |
| 4. Music Gen | 1.0 min | 0 min (curated) |
| 5. SFX | 0.1 min | 0.1 min |
| 6. TTS | 0.01 min | 0.02 min |
| **Pipeline Overhead** | 0.3 min | 0.3 min |
| **TOTAL** | **~3.5 min** | **~7 min** |

---

## 5. Feasibility Assessment

### Against ≤30 Minute Target (RQ-PREP-001)

| Scenario | Median Spec | Minimum Spec | Meets Target? |
|----------|-------------|-------------|---------------|
| Minimal session | ~3.5 min | ~7 min | **YES** |
| Full session | ~9 min | ~17 min | **YES** |
| Double session (long campaign) | ~18 min | ~34 min | **YES** (median), **TIGHT** (minimum) |

### Bottleneck Analysis

| Phase | % of Total (Median) | % of Total (Minimum) | Bottleneck? |
|-------|--------------------|--------------------|-------------|
| LLM Content | 39% | 71% | **YES** (dominant on minimum spec) |
| Image Gen | 17% | 21% | Moderate |
| Music Gen | 33% | 0% | Significant on median (0% on minimum — curated) |
| Image Critique | 4% | 5% | No |
| SFX/TTS | <2% | <1% | No |
| Overhead | 6% | 3% | No |

**Key Finding:** LLM content generation is the bottleneck on minimum spec (71% of total time). On median spec, LLM and music generation split the load (~39% and ~33%).

### Optimization Opportunities

1. **Batched LLM generation:** Generate multiple NPCs per LLM call instead of one at a time. Reduces prompt overhead by ~30%.
2. **Parallel CPU tasks:** Run TTS generation on CPU while GPU handles image/music generation. Saves ~0.5 min.
3. **Cached content:** Skip generation for previously-generated assets (idempotent prep). Reduces repeat-prep to <1 min.
4. **Reduced image count:** Drop to 3-5 portraits + 2 scenes for minimum spec. Saves ~1-2 min.
5. **Lower-quality music fallback:** Use procedural MIDI instead of ACE-Step for medium-tier hardware. Saves 2-3 min.

---

## 6. Risk Analysis

### Risk 1: LLM Generation Slower Than Projected

**Trigger:** Qwen3 8B generates at <10 tok/s on median spec
**Impact:** Phase 1 doubles from 3.5 min to 7 min
**Mitigation:** Use Qwen3 4B (faster, lower quality) or reduce content scope
**Severity:** Medium (total still <15 min on median)

### Risk 2: ACE-Step Slower Than Projected

**Trigger:** ACE-Step takes >60s per track on RTX 3060
**Impact:** Phase 4 doubles from 3 min to 6 min
**Mitigation:** Use curated library fallback; procedural MIDI as middle tier
**Severity:** Low (total still <15 min; fallback eliminates music gen entirely)

### Risk 3: Image Critique Rejects Too Many Images

**Trigger:** >50% image rejection rate
**Impact:** Phase 2+3 doubles due to regeneration
**Mitigation:** Lower critique thresholds; accept with warning instead of rejecting
**Severity:** Low (bounded regen caps at 3 attempts)

### Risk 4: Model Loading Overhead Higher Than Projected

**Trigger:** Model load/unload takes >30s per phase transition
**Impact:** Adds ~2-3 min to total pipeline
**Mitigation:** Lazy loading (keep model loaded if next phase needs it); memory mapping
**Severity:** Low (total still within budget)

---

## 7. Decision: R0-DEC-035 Status Update

### Projected Outcome

**Based on R1 model performance estimates and the timing analysis above:**

| Criterion | Target | Projected (Median) | Projected (Minimum) | Status |
|-----------|--------|--------------------|--------------------|--------|
| Prep time ≤30 min (full session) | ≤30 min | ~9 min | ~17 min | **PROJECTED PASS** |
| Prep time ≤30 min (minimal session) | ≤30 min | ~3.5 min | ~7 min | **PROJECTED PASS** |
| Pipeline prototype exists | Yes | Yes (WO-M3-PREP-01) | Yes | **PASS** |
| Sequential model loading demonstrated | Yes | Yes (stub mode) | Yes | **PASS** |

### R0-DEC-035 Status Change

**Previous status:** 🔴 BLOCKED
**Projected status:** 🟡 PROJECTED PASS (pending hardware benchmarking)

The pipeline prototype is complete and the timing projections show comfortable margin on both median and minimum spec. **Hardware benchmarking is the only remaining validation step.**

### What Must Happen to Confirm

1. **Benchmark Qwen3 8B Q4_K_M** on a 6-8 core CPU with GPU offload → confirm 20-30 tok/s
2. **Benchmark SDXL Lightning NF4** on a 6 GB VRAM GPU → confirm 4-6 sec per image
3. **Benchmark ACE-Step** on a 6-8 GB VRAM GPU → confirm 20-40 sec per 60s clip
4. **Run end-to-end prep pipeline** with real models on target hardware → confirm total <30 min
5. **Test on minimum spec** (4-core CPU, 8 GB RAM, no GPU) → confirm total <30 min with curated fallbacks

---

## 8. Acceptance Criteria for R0-DEC-035

### PASS (GO for M0 Planning)

- [ ] Full session prep completes in ≤30 minutes on median spec hardware
- [ ] Full session prep completes in ≤60 minutes on minimum spec hardware (with curated fallbacks)
- [ ] Pipeline produces complete asset manifest (all asset types present)
- [ ] No model OOM errors during sequential loading
- [ ] All generated assets pass basic validation (file exists, non-zero size, correct format)

### CONDITIONAL PASS (GO with reduced scope)

- [ ] Full session prep completes in 30-60 minutes on median spec → reduce asset count
- [ ] Minimum spec exceeds 60 minutes → drop music/SFX generation, use curated only

### FAIL (NO-GO, require architecture change)

- [ ] Full session prep exceeds 60 minutes on median spec → fundamental architecture problem
- [ ] Model loading causes OOM on median spec → model selection or pipeline architecture wrong

---

## 9. Conclusion

**The prep pipeline timing is projected to comfortably meet the ≤30 minute target on both median and minimum spec hardware.**

Key findings:
- **Median spec:** ~9 minutes for a full session (3x margin)
- **Minimum spec:** ~17 minutes for a full session (curated fallbacks for music/SFX)
- **Bottleneck:** LLM content generation (especially on minimum spec)
- **Risk level:** Low — all projections well within budget with multiple fallback paths

**Next action:** Hardware benchmarking to confirm projected timings. This requires access to target hardware (6-8 core CPU, 6-8 GB VRAM GPU) and installation of R1 model selections (Qwen3 8B, SDXL Lightning NF4, ACE-Step, Kokoro).

---

**END OF PREP PIPELINE TIMING STUDY**

**Date:** 2026-02-11
**Author:** Opus (Agent 46)
**Status:** PROJECTED (benchmarking required for confirmation)
**Unblocks:** R0-DEC-035 (Prep Pipeline GO Criterion), RQ-PREP-001 (Prep Time Budget)
