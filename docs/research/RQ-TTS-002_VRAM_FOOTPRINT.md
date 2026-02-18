# RQ-TTS-002: VRAM Footprint and Persistence Feasibility

**Sprint:** WO-TTS-COLD-START-RESEARCH
**Date:** 2026-02-14
**Hardware:** NVIDIA GeForce RTX 3080 Ti (12,288 MB VRAM), Windows 11, Python 3.11.1

---

## VRAM Measurements

### Idle Footprint (model loaded, no active inference)

| Configuration | Allocated (MB) | Reserved (MB) | Remaining VRAM (MB) |
|---------------|---------------|---------------|---------------------|
| Baseline (no models) | 0.0 | 0.0 | 12,288 |
| Original only | 3,058.8 | 3,088.0 | 9,200 |
| Turbo only | 4,214.8 | 4,270.0 | 8,018 |
| Both tiers | 7,586.5 | 7,644.0 | 4,644 |

### Peak VRAM During Active Synthesis

| Configuration | Peak Allocated (MB) | Peak Reserved (MB) |
|---------------|--------------------|--------------------|
| Original synthesis (idle Original) | 3,517.7 | 3,730.0 |
| Turbo synthesis (idle Turbo) | 4,655.4 | 4,708.0 |
| Turbo synthesis (both tiers loaded) | 8,024.3 | 8,080.0 |

### Synthesis VRAM Overhead (peak - idle)

| Tier | VRAM Overhead During Synthesis |
|------|-------------------------------|
| Original | ~459 MB (14% above idle) |
| Turbo | ~441 MB (10% above idle) |

---

## VRAM Release Behavior

| State | Allocated (MB) | Reserved (MB) |
|-------|---------------|---------------|
| Both tiers loaded | 7,586.5 | 7,644.0 |
| After `del turbo` + `empty_cache()` | 3,381.7 | 4,536.0 |
| After `del original` + `empty_cache()` | 8.4 | 212.0 |
| Baseline (never loaded) | 0.0 | 0.0 |

**VRAM leak after full cleanup: 8.4 MB** — effectively clean. The `del model` + `torch.cuda.empty_cache()` pattern reliably frees VRAM. Reserved memory (212 MB after cleanup) is CUDA allocator pool overhead that gets reused, not a true leak.

---

## Coexistence Analysis

### Can Chatterbox coexist with a 7B LLM (Spark narration)?

Typical 7B LLM at 4-bit quantization requires ~4,500 MB VRAM.

| Configuration | Remaining VRAM | 7B LLM Fits? | Margin |
|---------------|---------------|--------------|--------|
| Original only (3,059 MB) | 9,200 MB | **YES** | 4,700 MB |
| Turbo only (4,215 MB) | 8,018 MB | **YES** | 3,518 MB |
| Both tiers (7,587 MB) | 4,644 MB | **YES** | 144 MB |

**Verdict:** Original + 7B LLM fits comfortably with 4.7 GB margin. Even both tiers + 7B LLM technically fits, but with only 144 MB margin — too tight for inference overhead. In practice, **load one tier at a time** if running alongside an LLM.

### Can Chatterbox coexist with SDXL image generation?

SDXL at fp16 requires ~6,500 MB VRAM.

| Configuration | Remaining VRAM | SDXL Fits? | Margin |
|---------------|---------------|------------|--------|
| Original only (3,059 MB) | 9,200 MB | **YES** | 2,700 MB |
| Turbo only (4,215 MB) | 8,018 MB | **YES** | 1,518 MB |
| Both tiers (7,587 MB) | 4,644 MB | **NO** | -1,856 MB |

**Verdict:** Single tier + SDXL fits. Both tiers + SDXL does not. SDXL and Chatterbox cannot run simultaneously at both tiers — a load/unload strategy is needed for SDXL coexistence.

### Triple coexistence: Chatterbox + 7B LLM + SDXL?

Total: 3,059 + 4,500 + 6,500 = 14,059 MB — exceeds 12 GB. **Not feasible.** This would require time-multiplexing: load/unload models as needed, with TTS idle during image generation and vice versa.

---

## Persistence Feasibility

### Recommendation: Keep ONE tier loaded

| Strategy | VRAM Cost | Remaining | Feasible? |
|----------|-----------|-----------|-----------|
| Keep Original resident | 3,059 MB | 9,200 MB | **YES — recommended** |
| Keep Turbo resident | 4,215 MB | 8,018 MB | YES |
| Keep both resident | 7,587 MB | 4,644 MB | Marginal |
| Load/unload on demand | 0 MB (idle) | 12,288 MB | YES (but defeats cold start goal) |

**Recommended strategy: Keep Original loaded by default.**
- Original is the primary tier for narration (emotion control, voice cloning)
- 3 GB leaves 9.2 GB for everything else — plenty for a 7B LLM
- Turbo can be loaded on demand for combat sequences (one-time 14s load, then fast 1.5s inference)
- When SDXL is needed: unload TTS, run image gen, reload TTS

### VRAM Management Strategy

1. **Default state:** Original loaded, Turbo unloaded
2. **Combat mode:** Load Turbo (14s), use for rapid sequential lines (1.5s each), unload after combat
3. **Image generation:** Unload all TTS models, run SDXL, reload TTS after
4. **Cleanup:** `del model` + `torch.cuda.empty_cache()` reliably frees VRAM (verified: 8.4 MB residual)

---

## Key Finding for Persistent Server Design (RQ-TTS-003)

VRAM budget **supports persistence**. A persistent TTS server holding Original in VRAM is feasible and leaves adequate headroom for future LLM inference. The server should support:
- Loading/unloading tiers dynamically based on usage pattern
- Graceful VRAM release when other GPU consumers need resources
- Health reporting (current VRAM usage, loaded tiers)

---

*Benchmark script: `scripts/bench_vram.py`*
