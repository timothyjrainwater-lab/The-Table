# RQ-TTS-001: Cold Start Time Breakdown

**Sprint:** WO-TTS-COLD-START-RESEARCH
**Date:** 2026-02-14
**Hardware:** NVIDIA GeForce RTX 3080 Ti (12 GB VRAM), Windows 11, Python 3.11.1
**Test text:** "The fighter raises his sword and charges across the stone bridge."

---

## Chatterbox Cold Start Breakdown

| Phase | Component | Time (ms) | % of Total |
|-------|-----------|-----------|------------|
| 1 | Python stdlib + project imports (cached) | 11 | 0.1% |
| 2 | `import torch` (first import) | 1,662 | 8.9% |
| 3 | CUDA context init (`torch.cuda.is_available()`) | 24 | 0.1% |
| 4a-i | `import chatterbox.tts` (module + dependencies) | 3,792 | 20.4% |
| 4a-ii | `ChatterboxTTS.from_pretrained()` (model load) | 7,901 | 42.4% |
| 5 | First inference (warm-up, ~104 steps) | 5,242 | 28.1% |
| **Total** | **Cold start to first audio (Original)** | **18,621** | **100%** |

### Steady-State Performance

| Tier | Inference Time (ms) | Stdev | it/s |
|------|---------------------|-------|------|
| Original (steady-state, ~100 steps) | 3,511 | 167 | ~37-40 |
| Turbo (steady-state, ~87 steps) | 1,475 | 79 | ~72-80 |

### Chatterbox Turbo Cold Start

| Phase | Component | Time (ms) |
|-------|-----------|-----------|
| 4b-i | `import chatterbox.tts_turbo` | 7 |
| 4b-ii | `ChatterboxTurboTTS.from_local()` | 14,269 |
| 5b | First inference (warm-up) | 3,011 |
| **Total** | **Turbo cold start (after torch/CUDA already loaded)** | **17,287** |

**Note:** Turbo's `from_pretrained()` requires a HuggingFace token (`token=True` hardcoded). `from_local()` was used instead. Turbo model is larger (3.8 GB on disk vs 3.0 GB for Original) and loads slower.

---

## Kokoro Cold Start Breakdown

| Phase | Component | Time (ms) | % of Total |
|-------|-----------|-----------|------------|
| 1 | `import onnxruntime` | 47 | 0.8% |
| 2 | `import kokoro_onnx` | 291 | 4.7% |
| 3 | `Kokoro()` model init (ONNX, int8, CPU) | 1,136 | 18.5% |
| 4 | First inference (warm-up) | 4,670 | 76.0% |
| **Total** | **Cold start to first audio** | **6,145** | **100%** |

### Kokoro Steady-State Performance

| Metric | Value |
|--------|-------|
| Inference time (steady-state) | 4,639 ms (stdev 358) |
| Output | 90,112 samples at 24 kHz (3.75s audio) |
| Real-time factor | ~0.81x (slower than real-time for this sentence) |

---

## Key Findings

### 1. The bottleneck is model loading (42.4% for Original)

`ChatterboxTTS.from_pretrained()` accounts for nearly half of cold start time. This is weight deserialization + GPU transfer — 3 GB of model weights moving from disk/HF cache into VRAM. This is fully amortizable by keeping the model resident.

### 2. `import chatterbox.tts` is unexpectedly expensive (20.4%)

The Chatterbox module import chain pulls in `transformers`, `diffusers`, `safetensors`, and several other heavy packages. At 3.8 seconds, this is the second-largest contributor. This cost is also amortized by any persistence approach.

### 3. `import torch` is significant but not dominant (8.9%)

At 1.7 seconds, torch import is noticeable but not the primary bottleneck. It's amortized by persistence.

### 4. CUDA context init is negligible (0.1%)

`torch.cuda.is_available()` is 24ms — not a factor.

### 5. First inference has a warm-up penalty

Original first inference (5,242ms) is ~49% slower than steady-state (3,511ms). This is typical — CUDA kernel compilation, memory allocation patterns, and JIT compilation on first run.

### 6. Kokoro cold start is 3x faster than Chatterbox

Kokoro's total cold start (6.1s) is dominated by first inference (76%), not model loading. The ONNX model loads in 1.1s vs Chatterbox's 7.9s. However, Kokoro's inference speed is much slower than Chatterbox Turbo at steady state.

### 7. Persistence eliminates 72% of Chatterbox cold start

If the model stays loaded, subsequent calls skip phases 1-4 (13,389ms) and pay only inference cost (3,511ms for Original, 1,475ms for Turbo). This is a **4-5x improvement** for Original and **12x improvement** over full cold start for Turbo.

---

## Amortization Potential

| Component | Cold Start (ms) | Can Amortize? | Strategy |
|-----------|----------------|---------------|----------|
| torch import | 1,662 | Yes | Persistent process |
| CUDA init | 24 | Yes | Persistent process |
| Module import | 3,792 | Yes | Persistent process |
| Model load | 7,901 | Yes | Keep model in VRAM |
| First inference warm-up | 1,731 | Yes | First call pays this once |
| Steady-state inference | 3,511 | No | Irreducible per-call cost |

**Total amortizable:** 15,110ms (81% of cold start)
**Irreducible per-call cost:** 3,511ms (Original) / 1,475ms (Turbo)

---

## Comparison: Chatterbox vs Kokoro

| Metric | Chatterbox Original | Chatterbox Turbo | Kokoro (CPU, int8) |
|--------|--------------------|--------------------|-------------------|
| Cold start | 18,621 ms | 17,287 ms* | 6,145 ms |
| Model load only | 7,901 ms | 14,269 ms | 1,136 ms |
| Steady-state inference | 3,511 ms | 1,475 ms | 4,639 ms |
| Audio quality | Highest (emotion) | High (no emotion) | Good (no cloning) |
| VRAM idle | 3,059 MB | 4,215 MB | 0 MB (CPU) |

*Turbo cold start measured after torch + CUDA already loaded. Full cold start would add ~1,686ms.

---

## Recommendation

**Model persistence is the clear path.** The data shows that 81% of Chatterbox cold start time is fully amortizable by keeping the process and model alive between calls. The choice between server daemon (RQ-TTS-003) and subprocess keep-alive (RQ-TTS-004) should be guided by agent integration constraints, not performance — both approaches eliminate the same 15 seconds of cold start.

For sequential narration (combat), Chatterbox Turbo at steady state (1.5s per sentence) is 3x faster than Kokoro (4.6s per sentence) — making Turbo the better choice for rapid output **if the model is already loaded**.

---

*Benchmark script: `scripts/bench_cold_start.py`*
