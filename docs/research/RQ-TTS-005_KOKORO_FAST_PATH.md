# RQ-TTS-005: Kokoro as Fast Path

**Sprint:** WO-TTS-COLD-START-RESEARCH
**Date:** 2026-02-14
**Dependencies:** RQ-TTS-001 (timing data)

---

## Summary

Kokoro is **not** a good fast path for sequential narration. Despite having 3x faster cold start than Chatterbox, its steady-state inference is 3x **slower** than Chatterbox Turbo. With a persistent server eliminating cold start, Chatterbox Turbo is the better choice for rapid sequential output.

---

## Timing Comparison (from RQ-TTS-001)

| Metric | Chatterbox Original | Chatterbox Turbo | Kokoro (CPU, int8) |
|--------|--------------------|--------------------|-------------------|
| Cold start (total) | 18,621 ms | ~18,987 ms* | 6,145 ms |
| Model load only | 7,901 ms | 14,269 ms | 1,136 ms |
| First inference | 5,242 ms | 3,011 ms | 4,670 ms |
| **Steady-state inference** | **3,511 ms** | **1,475 ms** | **4,639 ms** |

*Turbo cold start = torch import (1,662) + CUDA init (24) + module import (7) + model load (14,269) + first inference (3,011) = 18,973ms.

### Key Insight

**Cold start is Kokoro's advantage; steady state is its weakness.**

Without persistence, Kokoro wins on first-call latency (6.1s vs 18.6s). But sequential narration means many calls — and after the first call, Chatterbox Turbo at 1.5s/sentence is 3.1x faster than Kokoro at 4.6s/sentence.

With a persistent server (RQ-TTS-003), cold start is eliminated. At that point, Chatterbox Turbo dominates:

| 5 sequential sentences | Kokoro | Chatterbox Turbo (persistent) |
|------------------------|--------|-------------------------------|
| Total time | 23,195 ms | 7,375 ms |
| Per sentence | 4,639 ms | 1,475 ms |

---

## Quality Comparison

| Dimension | Chatterbox Original | Chatterbox Turbo | Kokoro |
|-----------|--------------------|--------------------|--------|
| Voice cloning | Yes (reference audio) | Yes (reference audio) | No |
| Emotion/exaggeration | Yes (0.0-1.0) | No | No |
| Audio quality | Highest | High | Good |
| Sample rate | 24 kHz native | 24 kHz native | 24 kHz (resample to 16 kHz) |
| VRAM | 3,059 MB (GPU) | 4,215 MB (GPU) | 0 MB (CPU) |

Kokoro produces acceptable quality for short signals ("Work order complete") but lacks:
- Voice cloning — all narration uses preset voices, no character consistency
- Emotion control — flat delivery, not suitable for dramatic moments
- Quality ceiling — ONNX int8 quantization introduces subtle artifacts at longer lengths

For combat narration ("The orc swings its greataxe, catching the fighter's shield at an angle"), Chatterbox's voice cloning and emotion control provide noticeably better immersion.

---

## Kokoro Persistence Analysis

**Does Kokoro benefit from persistent loading?**

| Phase | Kokoro Time (ms) | % of Cold Start |
|-------|-----------------|-----------------|
| onnxruntime import | 47 | 0.8% |
| kokoro_onnx import | 291 | 4.7% |
| Model init | 1,136 | 18.5% |
| First inference | 4,670 | 76.0% |

Kokoro's cold start is dominated by first inference (76%), not model loading. Subsequent inferences (4,639ms) are barely faster than the first (4,670ms). **Persistence provides minimal benefit for Kokoro** — saving 1.5s of import + model load but not improving the 4.6s per-sentence inference time.

**Contrast with Chatterbox:** Persistence saves 15.1s per call by eliminating import + model load + warm-up, and steady-state inference is significantly faster (3.5s Original, 1.5s Turbo).

---

## Hybrid Strategy Analysis

**Proposed strategy from dispatch:**
- Kokoro for rapid sequential lines (combat narration)
- Chatterbox for single high-quality outputs (scenes, dramatic moments)

**This strategy is backwards.** The P0 data shows:
- Kokoro is slow per-sentence (4.6s) — bad for rapid sequential output
- Chatterbox Turbo is fast per-sentence (1.5s) — good for rapid sequential output
- Chatterbox Original is best quality — good for dramatic moments

**Revised hybrid strategy:**

| Use Case | Backend | Rationale |
|----------|---------|-----------|
| Rapid sequential (combat) | Chatterbox Turbo (persistent) | 1.5s/sentence, voice cloning |
| Dramatic single-shot | Chatterbox Original (persistent) | Emotion control, highest quality |
| Fallback (no GPU) | Kokoro | CPU-only, no VRAM needed |
| Quick signals (< 5 words) | Chatterbox Turbo (persistent) | Already loaded, sub-second for short text |

**Selection logic:** Tier selection is already implemented in `ChatterboxTTSAdapter._select_tier()` — text under 20 words uses Turbo, longer text uses Original. This heuristic is sound and doesn't need Kokoro involvement.

---

## When Kokoro Is the Right Choice

Kokoro remains valuable as a **fallback**, not a fast path:

1. **No GPU available:** Kokoro runs on CPU with zero VRAM. If the GPU is unavailable (driver crash, VRAM fully consumed by LLM/SDXL), Kokoro provides degraded but functional TTS.
2. **Development/testing:** Kokoro doesn't require CUDA setup. Developers without GPUs can test TTS integration.
3. **First-call without server:** If the persistent server isn't running, Kokoro's 6.1s cold start is better than Chatterbox's 18.6s for a one-off signal.

---

## Recommendation

**Do not implement Kokoro as a fast path. Keep it as a fallback.**

The persistent server (RQ-TTS-003) with Chatterbox Turbo provides 1.5s/sentence — 3x faster than Kokoro — with better quality and voice cloning. Kokoro's role is backup, not primary.

**No changes to `speak.py` backend selection logic needed.** The existing priority (Chatterbox > Kokoro) is correct. The persistent server amplifies Chatterbox's advantage by removing its only weakness (cold start).

---

*Key question answered: Kokoro is NOT fast enough to be the natural choice for sequential narration. Chatterbox Turbo with persistence is 3x faster at steady state.*
