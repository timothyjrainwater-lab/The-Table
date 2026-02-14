# DEBRIEF: WO-TTS-COLD-START-RESEARCH — Full Dump

**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Session scope:** Execute 6 research questions on TTS cold start latency — measurements, architecture design, feasibility analysis.
**Lifecycle:** NEW
**Commit:** UNCOMMITTED

---

## Work Completed

All 6 RQs executed in a single session. All deliverables written to `docs/research/`.

### Deliverables Produced

| RQ | File | Type |
|----|------|------|
| RQ-TTS-001 | `docs/research/RQ-TTS-001_COLD_START_BREAKDOWN.md` | Measured timing data |
| RQ-TTS-002 | `docs/research/RQ-TTS-002_VRAM_FOOTPRINT.md` | Measured VRAM data |
| RQ-TTS-003 | `docs/research/RQ-TTS-003_PERSISTENT_SERVER.md` | Architecture design |
| RQ-TTS-004 | `docs/research/RQ-TTS-004_SUBPROCESS_KEEPALIVE.md` | Feasibility analysis (rejected) |
| RQ-TTS-005 | `docs/research/RQ-TTS-005_KOKORO_FAST_PATH.md` | Comparative analysis (rejected) |
| RQ-TTS-006 | `docs/research/RQ-TTS-006_STREAMING_OUTPUT.md` | Source code analysis (not feasible) |

### Benchmark Scripts Created

| Script | Purpose |
|--------|---------|
| `scripts/bench_cold_start.py` | Phase-by-phase timing instrumentation (Chatterbox + Kokoro) |
| `scripts/bench_vram.py` | VRAM footprint measurements (idle, active, release, coexistence) |

---

## Key Measurements

### Cold Start Breakdown (RQ-TTS-001)

- **Total Chatterbox Original cold start:** 18,621 ms
  - `import torch`: 1,662 ms (8.9%)
  - `import chatterbox.tts`: 3,792 ms (20.4%)
  - `from_pretrained()`: 7,901 ms (42.4%) ← **dominant bottleneck**
  - First inference (warm-up): 5,242 ms (28.1%)
- **Steady-state Original inference:** 3,511 ms (stdev 167)
- **Steady-state Turbo inference:** 1,475 ms (stdev 79)
- **Kokoro total cold start:** 6,145 ms
- **Kokoro steady-state inference:** 4,639 ms (stdev 358)

### VRAM Footprint (RQ-TTS-002)

- **Original idle:** 3,059 MB allocated, 3,088 MB reserved
- **Turbo idle:** 4,215 MB allocated, 4,270 MB reserved
- **Both tiers idle:** 7,587 MB allocated, 7,644 MB reserved
- **VRAM release:** clean — 8.4 MB residual after del + empty_cache
- **Original + 7B LLM (4-bit):** FITS (4,700 MB margin)
- **Both tiers + 7B LLM:** technically fits (144 MB margin — too tight)

---

## Findings That Changed Assumptions

### 1. `import chatterbox.tts` costs 3.8 seconds

The dispatch assumed torch import was the main import bottleneck. It's not — the chatterbox module import chain (transformers, diffusers, safetensors) is 2.3x more expensive than torch itself. Both are amortized by persistence, but this was unexpected.

### 2. Kokoro is SLOWER at steady state than Chatterbox Turbo

The dispatch hypothesized Kokoro as a "fast path" for sequential narration. The data reverses this: Kokoro at 4.6s/sentence is 3.1x slower than Chatterbox Turbo at 1.5s/sentence. Kokoro's advantage is cold start (6.1s vs 18.6s), which becomes irrelevant with persistence.

### 3. Chatterbox Turbo loads slower than Original

Turbo model is larger on disk (3.8 GB vs 3.0 GB) and takes 14.3s to load vs Original's 7.9s. This matters for the VRAM management strategy — if combat mode loads Turbo on demand, the first combat narration line has a 14s penalty.

### 4. Turbo's `from_pretrained()` requires HuggingFace token

The Turbo model has `token=True` hardcoded in its `from_pretrained()`. The Original model works with `HF_HUB_OFFLINE=1`, but Turbo does not. Benchmarks had to use `from_local()` with the snapshot path. This is a bug in the chatterbox-tts package and affects the adapter's lazy loader — if the user has no HF token configured, Turbo loading will fail with `from_pretrained()`.

**Action needed:** The `_ChatterboxLoader.get_turbo()` in `chatterbox_tts_adapter.py` should prefer `from_local()` with the cached snapshot path. Currently it uses `from_pretrained()` as the default path, which hits this token issue.

### 5. Streaming is architecturally impossible

The dispatch allocated P2 priority to streaming, suggesting it might be "valuable but not required." The source analysis shows it's not just low-value — it's impossible with Chatterbox's diffusion-based architecture. The vocoder requires complete mel spectrograms. This is not a fixable limitation without replacing the TTS backend.

### 6. Subprocess keep-alive is a dead end

The dispatch treated subprocess keep-alive (RQ-TTS-004) as a plausible lightweight alternative. It's not viable because Bash tool calls don't share process state. This was already suspected ("Can an agent keep a speak.py subprocess alive across multiple Bash calls?" in the dispatch), and the answer is definitively no.

---

## Side Effects and Cascading Impacts

### WO-TTS-CHUNKING-001: No scope change needed

Neither the persistent server design nor the streaming analysis changes chunking strategy. Sentence-boundary chunking remains necessary because Chatterbox quality degrades beyond ~55 words. The server wraps the adapter, which already handles chunking internally.

### Turbo HF token bug affects production code

The `from_pretrained()` token issue (finding #4 above) exists in the current adapter code at `chatterbox_tts_adapter.py:168`. If an operator has no HF token, Turbo tier will fail silently and fall back to Original, masking a configuration issue. This is a separate fix, not in scope for this research WO.

### Benchmark scripts are reusable

`bench_cold_start.py` and `bench_vram.py` can be rerun after hardware changes, driver updates, or chatterbox-tts version bumps to validate assumptions. They use `HF_HUB_OFFLINE=1` and `from_local()` to avoid network dependencies.

---

## Uncommitted Files

All research output is uncommitted. Files created this session:

```
docs/research/RQ-TTS-001_COLD_START_BREAKDOWN.md
docs/research/RQ-TTS-002_VRAM_FOOTPRINT.md
docs/research/RQ-TTS-003_PERSISTENT_SERVER.md
docs/research/RQ-TTS-004_SUBPROCESS_KEEPALIVE.md
docs/research/RQ-TTS-005_KOKORO_FAST_PATH.md
docs/research/RQ-TTS-006_STREAMING_OUTPUT.md
scripts/bench_cold_start.py
scripts/bench_vram.py
```

---

*End of full dump.*
