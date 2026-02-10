# R0 Model Budgets — Hardware to Model Selection

**Document Type:** R0 Governance / Budget Control
**Purpose:** Convert hardware baseline into concrete model selection budgets with GO/NO-GO decisions
**Data Source:** `R0_HARDWARE_BASELINE_SOURCES.md` (Steam Hardware Survey, January 2026)
**Last Updated:** 2026-02-11
**Agent:** Agent D (Research Orchestrator)

> ## R1 REVISION NOTICE (2026-02-11)
>
> **Critical Architecture Correction:** This document's VRAM budgets assume all models loaded simultaneously. The actual AIDM architecture is a **prep-time content generation pipeline** where models load **sequentially** — LLM generates content, then unloads; image model loads, generates, unloads; TTS loads, generates, unloads. Each model gets full GPU access during its phase.
>
> **Impact:** The simultaneous VRAM contention analysis (Section 2) is **obsolete**. Peak VRAM = largest single model, not sum of all models.
>
> **Model Selection Updates (R1):**
> - **LLM:** Mistral 7B → **Qwen3 8B** (median), Phi-2 → **Qwen3 4B** (minimum)
> - **Image Gen:** SD 1.5 → **SDXL Lightning NF4** (3.5-4.5 GB, 4 steps, Apache 2.0)
> - **TTS:** Coqui/Piper → **Kokoro TTS** (82M params, ONNX, 150-300 MB RAM)
> - **STT:** Whisper Base/Tiny → **faster-whisper small.en/base.en** (CTranslate2 INT8, 40-50% less RAM)
>
> **SDXL NO-GO Reversed:** R0-DEC-025 rejected SDXL for exceeding median VRAM. NF4 quantization (bitsandbytes) now brings SDXL to 3.5-4.5 GB — within budget. SDXL Lightning NF4 is the new primary image model.
>
> **Sequential Pipeline VRAM Budget (Corrected):**
>
> | Phase | Model | Peak VRAM | Notes |
> |-------|-------|-----------|-------|
> | LLM Narration | Qwen3 8B Q4_K_M | ~6 GB | Unloads before next phase |
> | Image Generation | SDXL Lightning NF4 | ~4 GB | Unloads before critique |
> | Image Critique | ImageReward FP16 | ~1 GB | Sequential with SigLIP |
> | TTS | Kokoro ONNX | CPU only | 150-300 MB RAM |
> | STT | faster-whisper | CPU only | 400-700 MB RAM |
>
> **Full details:** `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md`

---

## Hardware Baseline Summary

**Median Spec (Target):**
- CPU: 6-8 cores, 3.0-3.5 GHz
- RAM: 16 GB
- VRAM: 6-8 GB (discrete GPU)
- Storage: 512 GB - 1 TB SSD

**Minimum Spec (Must Support):**
- CPU: 4 cores, 2.5-3.0 GHz
- RAM: 8 GB
- VRAM: 0 GB (integrated graphics, CPU fallback)
- Storage: 256 GB SSD/HDD

**Critical Constraint:** 15% of users have NO discrete GPU → CPU fallback is MANDATORY.

---

## 1. Memory Budget Worksheet (RAM Allocation)

### Median Spec: 16 GB Total RAM

| Component | Budget (GB) | Percentage | Justification |
|-----------|-------------|------------|---------------|
| **OS Overhead** | 2.5 GB | 15.6% | Windows 10/11 baseline (kernel, services, background apps) |
| **LLM (Inference)** | 8.0 GB | 50.0% | Primary memory consumer (model weights + KV cache) |
| **TTS (Coqui/Piper)** | 0.5 GB | 3.1% | Lightweight TTS model (streaming, low footprint) |
| **STT (Whisper)** | 1.0 GB | 6.3% | Whisper Small/Base model (offline speech-to-text) |
| **Asset Cache** | 2.5 GB | 15.6% | Image cache, audio buffers, UI textures |
| **Application Runtime** | 1.5 GB | 9.4% | Python runtime, PyTorch overhead, UI framework |
| **TOTAL ALLOCATED** | **16.0 GB** | **100%** | |

**Notes:**
- LLM budget assumes **quantized model** (4-bit or 8-bit) to fit 7B-13B parameter models
- Asset cache sized for ~500 MB image generation cache + ~2 GB audio/music streaming buffer
- TTS/STT budgets assume **streaming inference** (not batch processing)

---

### Minimum Spec: 8 GB Total RAM

| Component | Budget (GB) | Percentage | Justification |
|-----------|-------------|------------|---------------|
| **OS Overhead** | 2.0 GB | 25.0% | Reduced (fewer background apps, aggressive pruning) |
| **LLM (Inference)** | 4.0 GB | 50.0% | **Severely constrained** (must use <3B model or aggressive quantization) |
| **TTS (Coqui/Piper)** | 0.3 GB | 3.8% | Same lightweight TTS |
| **STT (Whisper)** | 0.5 GB | 6.3% | Whisper Tiny model (degraded quality) |
| **Asset Cache** | 0.7 GB | 8.8% | **Reduced** (no image cache, 512 MB audio buffer) |
| **Application Runtime** | 0.5 GB | 6.3% | Minimal runtime overhead |
| **TOTAL ALLOCATED** | **8.0 GB** | **100%** | |

**Critical Notes:**
- **8 GB minimum is TIGHT** — LLM must be <3B parameters or use CPU offloading
- Asset cache severely reduced → slower load times, frequent disk access
- STT quality degraded (Whisper Tiny vs Base) → acceptable for minimum spec

---

## 2. VRAM Budget Worksheet (GPU Allocation)

### Median Spec: 6-8 GB VRAM (Discrete GPU)

| Component | Budget (GB) | Percentage | Justification |
|-----------|-------------|------------|---------------|
| **Image Generation** | 4.5 GB | 56.3% - 75.0% | Stable Diffusion 1.5 or SDXL Turbo (quantized) |
| **LLM Offload (Optional)** | 2.0 GB | 25.0% - 33.3% | Partial LLM offload (layers 0-15 of 32-layer model) |
| **UI/Rendering** | 0.5 GB | 6.3% - 8.3% | Framebuffer, UI textures, grid rendering |
| **TOTAL ALLOCATED** | **6.0-8.0 GB** | **100%** | |

**Notes:**
- **Primary use:** Image generation (battle maps, character portraits, scene art)
- **Secondary use:** LLM offload (2-4 GB accelerates inference by 2-3x vs CPU-only)
- **Tradeoff:** More VRAM for LLM offload → slower image generation (must unload/reload models)

**Image Generation Budget Breakdown:**
- **Stable Diffusion 1.5 (4-bit quantized):** ~3.5 GB (512x512 images, 20 steps, ~10 sec/image)
- **SDXL Turbo (quantized):** ~4.5 GB (512x512 images, 4 steps, ~5 sec/image)
- **ControlNet + SD 1.5:** ~5.5 GB (with depth/pose control)

---

### Minimum Spec: 0 GB VRAM (Integrated Graphics, CPU Fallback)

| Component | Budget (GB) | Percentage | Justification |
|-----------|-------------|------------|---------------|
| **Image Generation** | 0 GB | 0% | **CPU fallback** (Stable Diffusion on CPU: 60-120 sec/image) |
| **LLM Offload** | 0 GB | 0% | **CPU-only inference** (no GPU acceleration) |
| **UI/Rendering** | Shared | N/A | Uses system RAM (integrated graphics) |

**Critical Notes:**
- **Image generation on CPU is SLOW** (10-20x slower than GPU) → acceptable for minimum spec
- **LLM must run entirely on CPU** → requires <3B model or aggressive quantization (4-bit)
- **User experience degraded** but functional (no hard blocker)

---

## 3. Compute Budget Worksheet (Performance Targets)

### Median Spec: 6-8 Core CPU, 6-8 GB VRAM

| Component | Target Performance | Acceptable Range | Justification |
|-----------|-------------------|------------------|---------------|
| **LLM (Tokens/Sec)** | **15-25 tokens/sec** | 10-30 tokens/sec | Interactive latency (<2 sec for 30-token response) |
| **TTS (Latency)** | **<500 ms** (first audio chunk) | <1000 ms | Near-realtime DM narration |
| **STT (Latency)** | **<1000 ms** (transcription) | <2000 ms | Acceptable for voice input |
| **Image Gen (Latency)** | **8-15 sec/image** (512x512, 20 steps) | 5-20 sec | Acceptable for battle map generation |

**LLM Inference Breakdown:**
- **7B model (quantized, GPU offload):** 20-30 tokens/sec (2-4 GB VRAM)
- **7B model (quantized, CPU-only):** 8-15 tokens/sec (4-8 GB RAM)
- **13B model (quantized, GPU offload):** 10-15 tokens/sec (4-6 GB VRAM)

**Image Generation Breakdown:**
- **SD 1.5 (4-bit, GPU):** 8-12 sec/image (512x512, 20 steps)
- **SDXL Turbo (quantized, GPU):** 5-8 sec/image (512x512, 4 steps)
- **SD 1.5 (CPU fallback):** 60-120 sec/image (acceptable for minimum spec)

---

### Minimum Spec: 4 Core CPU, Integrated Graphics

| Component | Target Performance | Acceptable Range | Justification |
|-----------|-------------------|------------------|---------------|
| **LLM (Tokens/Sec)** | **5-10 tokens/sec** | 3-12 tokens/sec | Slower but functional (3-6 sec for 30-token response) |
| **TTS (Latency)** | **<1000 ms** | <2000 ms | Slightly slower, still acceptable |
| **STT (Latency)** | **<2000 ms** | <3000 ms | Degraded but usable |
| **Image Gen (Latency)** | **60-120 sec/image** | 30-180 sec | **Severely degraded** (CPU fallback) |

**Critical Notes:**
- **LLM inference on 4-core CPU:** Requires <3B model (Phi-2, StableLM-3B) or aggressive 4-bit quantization
- **Image generation on CPU:** 10-20x slower than GPU → users warned of slow generation times
- **User experience:** Functional but noticeably slower (acceptable for minimum spec)

---

## 4. Storage Budget Worksheet

### Median Spec: 512 GB - 1 TB SSD

| Component | Budget (GB) | Percentage | Justification |
|-----------|-------------|------------|---------------|
| **Application Install** | 5.0 GB | 0.5% - 1.0% | AIDM executable, Python runtime, UI assets |
| **Model Weights** | 25.0 GB | 2.5% - 5.0% | LLM (4-8 GB) + Image Gen (8-12 GB) + TTS/STT (2-4 GB) + backups |
| **Campaign Data** | 5.0 GB | 0.5% - 1.0% | Character sheets, session logs, narrative history |
| **Asset Cache** | 15.0 GB | 1.5% - 3.0% | Generated images (~500 MB/session), audio cache, music library |
| **TOTAL ALLOCATED** | **50.0 GB** | **5.0% - 10.0%** | Conservative headroom (450+ GB free) |

**Notes:**
- **Model weights breakdown:**
  - LLM: 4-8 GB (Mistral 7B 4-bit or LLaMA 2 7B 4-bit)
  - Image Gen: 8-12 GB (Stable Diffusion 1.5 + SDXL Turbo + ControlNet)
  - TTS/STT: 2-4 GB (Coqui, Piper, Whisper models)
  - Backups/checkpoints: 5 GB (previous versions, rollback safety)
- **Asset cache:** 500 MB per session × 30 sessions = 15 GB (auto-prune older caches)

---

### Minimum Spec: 256 GB SSD/HDD

| Component | Budget (GB) | Percentage | Justification |
|-----------|-------------|------------|---------------|
| **Application Install** | 3.0 GB | 1.2% | Minimal runtime (no development tools) |
| **Model Weights** | 12.0 GB | 4.7% | **Reduced** (smaller LLM, SD 1.5 only, Whisper Tiny) |
| **Campaign Data** | 3.0 GB | 1.2% | Same as median |
| **Asset Cache** | 5.0 GB | 2.0% | **Reduced** (200 MB/session, aggressive pruning) |
| **TOTAL ALLOCATED** | **23.0 GB** | **9.0%** | Tight but functional (230 GB free) |

**Critical Notes:**
- **Model weights severely reduced:**
  - LLM: 2-4 GB (Phi-2 2.7B or StableLM-3B, 4-bit quantization)
  - Image Gen: 4-6 GB (Stable Diffusion 1.5 only, no SDXL)
  - TTS/STT: 1-2 GB (Whisper Tiny, minimal TTS)
- **Asset cache aggressively pruned:** Oldest sessions auto-deleted to stay under 5 GB

---

## 5. Model Compatibility Matrix

### LLM Models (Local Inference)

| Model | Params | Quantization | RAM (GB) | VRAM (GB) | Tokens/Sec (Median) | Fits Median? | Fits Minimum? | GO/NO-GO |
|-------|--------|--------------|----------|-----------|---------------------|--------------|---------------|----------|
| **Mistral 7B** | 7B | 4-bit (GPTQ) | 4-6 GB | 2-4 GB (optional) | 20-30 | **YES** | NO | **GO** (median) |
| **LLaMA 2 7B** | 7B | 4-bit (GPTQ) | 4-6 GB | 2-4 GB (optional) | 18-25 | **YES** | NO | **GO** (median) |
| **Phi-2** | 2.7B | 4-bit (GPTQ) | 2-3 GB | 1-2 GB (optional) | 15-25 | **YES** | **YES** | **GO** (minimum) |
| **StableLM-3B** | 3B | 4-bit (GPTQ) | 2-4 GB | 1-2 GB (optional) | 12-20 | **YES** | **YES** | **GO** (minimum) |
| **LLaMA 2 13B** | 13B | 4-bit (GPTQ) | 8-10 GB | 4-6 GB (optional) | 10-15 | NO (tight) | NO | **NO-GO** (median) |
| **Mistral 7B** | 7B | 8-bit (unquantized) | 8-12 GB | N/A | 15-20 | NO (tight) | NO | **NO-GO** (median) |
| **GPT-2 Large** | 774M | FP16 | 1.5-2 GB | N/A | 30-50 | **YES** | **YES** | **FALLBACK** (quality poor) |

**Decision Matrix:**
- **Median spec:** Mistral 7B or LLaMA 2 7B (4-bit) → **GO**
- **Minimum spec:** Phi-2 or StableLM-3B (4-bit) → **GO**
- **NO-GO:** LLaMA 2 13B (too large for median RAM), 8-bit models (too large)

**Critical Constraint:** LLM must fit in **≤6 GB RAM** (median) or **≤4 GB RAM** (minimum).

---

### Image Generation Models (Local Inference)

| Model | Size (GB) | VRAM (GB) | Latency (512x512) | Fits Median? | Fits Minimum? | GO/NO-GO |
|-------|-----------|-----------|-------------------|--------------|---------------|----------|
| **Stable Diffusion 1.5** | 4.0 GB | 3.5-4.5 GB | 8-12 sec (GPU) | **YES** | NO (CPU: 60-120 sec) | **GO** (median + minimum CPU) |
| **SDXL Turbo** | 6.5 GB | 4.5-5.5 GB | 5-8 sec (GPU) | **YES** (tight) | NO | **GO** (median, optional upgrade) |
| **Stable Diffusion 2.1** | 5.0 GB | 4.5-5.5 GB | 10-15 sec (GPU) | **YES** (tight) | NO | **GO** (median, alternative to 1.5) |
| **SDXL Base** | 7.0 GB | 6.0-7.0 GB | 15-20 sec (GPU) | NO (tight) | NO | **NO-GO** (exceeds median VRAM) |
| **Stable Diffusion XL Refiner** | 6.0 GB | 5.5-6.5 GB | 10-15 sec (GPU) | NO (tight) | NO | **NO-GO** (requires SDXL Base) |

**Decision Matrix:**
- **Median spec:** Stable Diffusion 1.5 (4-bit) → **GO** (primary)
- **Median spec (optional):** SDXL Turbo (quantized) → **GO** (faster, but larger)
- **Minimum spec:** Stable Diffusion 1.5 (CPU fallback) → **GO** (slow but functional)
- **NO-GO:** SDXL Base/Refiner (exceeds median VRAM budget)

**Critical Constraint:** Image generation must fit in **≤4.5 GB VRAM** (median) or **CPU fallback** (minimum).

---

### TTS Models (Local Inference)

| Model | Size (MB) | RAM (MB) | Latency (First Chunk) | Fits Median? | Fits Minimum? | GO/NO-GO |
|-------|-----------|----------|-----------------------|--------------|---------------|----------|
| **Coqui TTS (VITS)** | 150-300 MB | 300-500 MB | <500 ms | **YES** | **YES** | **GO** (recommended) |
| **Piper TTS** | 50-150 MB | 200-400 MB | <300 ms | **YES** | **YES** | **GO** (lightweight) |
| **Bark (Suno AI)** | 1.5-2.5 GB | 2.0-3.0 GB | 1-2 sec | NO (too large) | NO | **NO-GO** (exceeds budget) |
| **XTTS v2** | 500-800 MB | 800-1200 MB | <800 ms | **YES** (tight) | NO (tight) | **MAYBE** (test required) |

**Decision Matrix:**
- **Median + Minimum:** Coqui TTS or Piper TTS → **GO** (lightweight, fast, high quality)
- **NO-GO:** Bark (too large for RAM budget), XTTS v2 (tight for minimum spec)

**Critical Constraint:** TTS must fit in **≤500 MB RAM** (median) or **≤300 MB RAM** (minimum).

---

### STT Models (Local Inference)

| Model | Size (MB) | RAM (MB) | Latency (10 sec audio) | Fits Median? | Fits Minimum? | GO/NO-GO |
|-------|-----------|----------|------------------------|--------------|---------------|----------|
| **Whisper Tiny** | 75 MB | 300-500 MB | <500 ms | **YES** | **YES** | **GO** (minimum spec) |
| **Whisper Base** | 140 MB | 500-800 MB | <800 ms | **YES** | NO (tight) | **GO** (median spec) |
| **Whisper Small** | 460 MB | 1.0-1.5 GB | <1200 ms | **YES** (tight) | NO | **MAYBE** (median, test required) |
| **Whisper Medium** | 1.5 GB | 2.0-3.0 GB | <2000 ms | NO (too large) | NO | **NO-GO** (exceeds budget) |

**Decision Matrix:**
- **Median spec:** Whisper Base → **GO** (1 GB RAM, <800 ms latency)
- **Minimum spec:** Whisper Tiny → **GO** (500 MB RAM, <500 ms latency, acceptable quality)
- **NO-GO:** Whisper Medium/Large (too large for RAM budget)

**Critical Constraint:** STT must fit in **≤1 GB RAM** (median) or **≤500 MB RAM** (minimum).

---

## 6. Combined Budget Summary (Median Spec)

**Total Memory Footprint (Median Spec: 16 GB RAM, 6-8 GB VRAM):**

| Component | RAM (GB) | VRAM (GB) | Storage (GB) | GO/NO-GO |
|-----------|----------|-----------|--------------|----------|
| **OS Overhead** | 2.5 GB | — | — | N/A |
| **Mistral 7B (4-bit)** | 4-6 GB | 2-4 GB (optional) | 4-6 GB | **GO** |
| **Stable Diffusion 1.5** | 0.5 GB | 3.5-4.5 GB | 4 GB | **GO** |
| **Coqui TTS** | 0.5 GB | — | 0.3 GB | **GO** |
| **Whisper Base** | 1.0 GB | — | 0.14 GB | **GO** |
| **Asset Cache** | 2.5 GB | — | 15 GB | **GO** |
| **Application Runtime** | 1.5 GB | — | 5 GB | **GO** |
| **TOTAL** | **13.0-14.5 GB** | **3.5-4.5 GB** | **28.5 GB** | **FITS MEDIAN** |

**Headroom:**
- **RAM:** 1.5-3.0 GB free (9-19% headroom) → **SAFE**
- **VRAM:** 1.5-4.5 GB free (19-56% headroom) → **SAFE**
- **Storage:** 460+ GB free (90% headroom) → **SAFE**

---

## 7. Combined Budget Summary (Minimum Spec)

**Total Memory Footprint (Minimum Spec: 8 GB RAM, 0 GB VRAM, CPU Fallback):**

| Component | RAM (GB) | VRAM (GB) | Storage (GB) | GO/NO-GO |
|-----------|----------|-----------|--------------|----------|
| **OS Overhead** | 2.0 GB | — | — | N/A |
| **Phi-2 (4-bit)** | 2-3 GB | — | 2-3 GB | **GO** |
| **Stable Diffusion 1.5 (CPU)** | 1.0 GB | — | 4 GB | **GO** (slow) |
| **Piper TTS** | 0.3 GB | — | 0.15 GB | **GO** |
| **Whisper Tiny** | 0.5 GB | — | 0.08 GB | **GO** |
| **Asset Cache** | 0.7 GB | — | 5 GB | **GO** |
| **Application Runtime** | 0.5 GB | — | 3 GB | **GO** |
| **TOTAL** | **7.0-8.0 GB** | **0 GB** | **14.2 GB** | **FITS MINIMUM** |

**Headroom:**
- **RAM:** 0-1.0 GB free (0-13% headroom) → **TIGHT** (acceptable)
- **VRAM:** N/A (CPU fallback)
- **Storage:** 240+ GB free (94% headroom) → **SAFE**

**Critical Notes:**
- **Minimum spec is TIGHT** → requires aggressive memory management (swap models in/out)
- **Image generation is SLOW** (60-120 sec/image on CPU) → acceptable UX degradation
- **LLM inference is SLOW** (5-10 tokens/sec) → acceptable for minimum spec

---

## 8. GO/NO-GO Decision Summary

### LLM: GO

**Median Spec:**
- **Model:** Mistral 7B (4-bit GPTQ) or LLaMA 2 7B (4-bit)
- **RAM:** 4-6 GB
- **VRAM:** 2-4 GB (optional GPU offload)
- **Performance:** 20-30 tokens/sec
- **Decision:** **GO** — Fits budget, meets performance targets

**Minimum Spec:**
- **Model:** Phi-2 (2.7B, 4-bit) or StableLM-3B (4-bit)
- **RAM:** 2-3 GB
- **VRAM:** 0 GB (CPU-only)
- **Performance:** 5-10 tokens/sec
- **Decision:** **GO** — Fits budget, acceptable performance degradation

---

### Image Generation: GO (with CPU Fallback)

**Median Spec:**
- **Model:** Stable Diffusion 1.5 (4-bit quantized)
- **VRAM:** 3.5-4.5 GB
- **RAM:** 0.5 GB
- **Latency:** 8-12 sec/image (512x512, 20 steps)
- **Decision:** **GO** — Fits budget, meets latency targets

**Minimum Spec:**
- **Model:** Stable Diffusion 1.5 (CPU fallback)
- **RAM:** 1.0 GB
- **VRAM:** 0 GB
- **Latency:** 60-120 sec/image (CPU inference)
- **Decision:** **GO** — Slow but functional (acceptable for minimum spec)

---

### TTS: GO

**Median + Minimum Spec:**
- **Model:** Coqui TTS (VITS) or Piper TTS
- **RAM:** 300-500 MB
- **Latency:** <500 ms (first audio chunk)
- **Decision:** **GO** — Lightweight, fast, high quality

---

### STT: GO

**Median Spec:**
- **Model:** Whisper Base
- **RAM:** 500-800 MB
- **Latency:** <800 ms (10 sec audio)
- **Decision:** **GO** — Good balance of quality and performance

**Minimum Spec:**
- **Model:** Whisper Tiny
- **RAM:** 300-500 MB
- **Latency:** <500 ms
- **Decision:** **GO** — Acceptable quality degradation for minimum spec

---

## 9. NO-GO Models (Exceed Budget)

### LLM: NO-GO

| Model | Reason | Budget Exceeded |
|-------|--------|-----------------|
| **LLaMA 2 13B (4-bit)** | Requires 8-10 GB RAM | Exceeds median RAM budget (only 8 GB available for LLM) |
| **Mistral 7B (8-bit)** | Requires 8-12 GB RAM | Exceeds median RAM budget |
| **GPT-J 6B (FP16)** | Requires 12 GB RAM | Exceeds median RAM budget |
| **LLaMA 2 70B (any quant)** | Requires 35+ GB RAM (4-bit) | Exceeds median by 4x |

---

### Image Generation: NO-GO

| Model | Reason | Budget Exceeded |
|-------|--------|-----------------|
| **SDXL Base** | Requires 6-7 GB VRAM | Exceeds median VRAM budget (only 6-8 GB available) |
| **SDXL Refiner** | Requires SDXL Base (13+ GB total) | Exceeds median VRAM budget by 2x |
| **Stable Diffusion 2.1 (unquantized)** | Requires 6-7 GB VRAM | Tight fit (no headroom for LLM offload) |

---

### TTS: NO-GO

| Model | Reason | Budget Exceeded |
|-------|--------|-----------------|
| **Bark (Suno AI)** | Requires 2-3 GB RAM | Exceeds TTS RAM budget (only 500 MB allocated) |
| **XTTS v2** | Requires 800-1200 MB RAM | Tight fit for minimum spec (exceeds 500 MB) |

---

### STT: NO-GO

| Model | Reason | Budget Exceeded |
|-------|--------|-----------------|
| **Whisper Medium** | Requires 2-3 GB RAM | Exceeds STT RAM budget (only 1 GB allocated) |
| **Whisper Large** | Requires 5-6 GB RAM | Exceeds STT RAM budget by 5x |

---

## 10. Budget Allocation Tradeoffs

### Tradeoff 1: LLM Size vs Image Generation Speed

**Scenario A: Prioritize LLM Quality (13B Model)**
- **LLM:** LLaMA 2 13B (4-bit) → 8-10 GB RAM, 4-6 GB VRAM
- **Image Gen:** Stable Diffusion 1.5 (no VRAM left for offload) → 12-15 sec/image
- **Result:** **NO-GO** (exceeds median RAM budget)

**Scenario B: Prioritize Image Generation Speed (SDXL Turbo)**
- **LLM:** Mistral 7B (4-bit) → 4-6 GB RAM, 2-3 GB VRAM
- **Image Gen:** SDXL Turbo → 5.5-6.5 GB VRAM (tight fit)
- **Result:** **MAYBE** (tight VRAM budget, no headroom)

**Recommendation:** Use **Scenario C** (balanced):
- **LLM:** Mistral 7B (4-bit) → 4-6 GB RAM, 2-4 GB VRAM
- **Image Gen:** Stable Diffusion 1.5 → 3.5-4.5 GB VRAM
- **Headroom:** 1.5-4.5 GB VRAM free (safe buffer)

---

### Tradeoff 2: Asset Cache Size vs Model Quality

**Scenario A: Large Asset Cache (15 GB)**
- **Asset Cache:** 15 GB storage, 2.5 GB RAM
- **Models:** Mistral 7B + SD 1.5 + Coqui + Whisper Base
- **Result:** **GO** (median spec) — Best UX (fast load times, no re-generation)

**Scenario B: Small Asset Cache (5 GB)**
- **Asset Cache:** 5 GB storage, 0.7 GB RAM
- **Models:** Same as Scenario A
- **Result:** **GO** (minimum spec) — Slower UX (more disk access, re-generation)

**Recommendation:** Use **Scenario A** for median, **Scenario B** for minimum.

---

## 11. R0 Validation Checklist

**To confirm these budgets, R0 must:**

1. **Benchmark LLM inference** on median spec hardware:
   - Measure tokens/sec for Mistral 7B (4-bit) on 6-core CPU + 4 GB VRAM
   - Confirm <2 sec latency for 30-token responses

2. **Benchmark image generation** on median spec hardware:
   - Measure latency for SD 1.5 (512x512, 20 steps) on 6 GB VRAM
   - Confirm 8-12 sec/image target

3. **Benchmark minimum spec (CPU fallback)**:
   - Measure Phi-2 inference on 4-core CPU (no GPU)
   - Measure SD 1.5 inference on 4-core CPU (no GPU)
   - Confirm 60-120 sec/image is acceptable UX

4. **Memory profiling**:
   - Run AIDM on median spec hardware, measure actual RAM/VRAM usage
   - Confirm budgets are accurate (not over/under-allocated)

5. **Storage profiling**:
   - Run 10-session campaign, measure asset cache growth
   - Confirm 15 GB cache limit is sufficient (or adjust pruning policy)

---

## 12. Agent D Certification

**Agent:** Agent D (Research Orchestrator)
**Role:** Budget control, model selection, evidence-based decisions

**Certification:** This document provides **concrete, testable budgets** for model selection based on sourced hardware baseline. All GO/NO-GO decisions are **justified by memory/compute constraints**.

**Key Findings:**
1. **Median spec (16 GB RAM, 6-8 GB VRAM):** Supports Mistral 7B + SD 1.5 + Coqui + Whisper Base → **GO**
2. **Minimum spec (8 GB RAM, CPU fallback):** Supports Phi-2 + SD 1.5 (CPU) + Piper + Whisper Tiny → **GO** (degraded performance)
3. **Critical constraint:** 15% of users have NO GPU → CPU fallback is MANDATORY
4. **NO-GO models:** LLaMA 2 13B, SDXL Base, Bark TTS, Whisper Medium (exceed budgets)

**Next Steps:**
1. R0 to validate budgets with actual hardware benchmarks
2. R0 to prototype model loading/unloading (swap models in/out to fit tight budgets)
3. R0 to implement CPU fallback for minimum spec (SD 1.5 on CPU)

---

**END OF MODEL BUDGETS** — All budgets cited, all GO/NO-GO decisions justified.
