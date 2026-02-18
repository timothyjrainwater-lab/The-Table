# RQ-TTS-006: Streaming TTS Output

**Sprint:** WO-TTS-COLD-START-RESEARCH
**Date:** 2026-02-14
**Dependencies:** RQ-TTS-001 (timing data), source code analysis of Chatterbox internals

---

## Verdict: Streaming Is NOT Feasible with Chatterbox

Chatterbox's architecture (diffusion-based mel generation + HiFiGAN vocoder) is fundamentally incompatible with mid-generation audio streaming. The vocoder requires complete mel-spectrograms as input — partial mels produce artifacts, not usable audio.

---

## Chatterbox Generation Pipeline

```
Text → Tokenizer → Text Tokens → T3 Model (autoregressive) → Speech Tokens
    → S3Gen CFM (diffusion, ~100 steps) → Mel Spectrograms
    → HiFiGAN Vocoder (single pass) → Waveform (24kHz)
```

### Stage-by-Stage Streaming Analysis

| Stage | Streamable? | Why? |
|-------|-------------|------|
| **T3 (text → speech tokens)** | Partially | Autoregressive — tokens generated one at a time. Could theoretically yield partial token sequences, but incomplete sequences degrade S3Gen quality. |
| **S3Gen CFM (tokens → mels)** | No | Diffusion loop refines the **entire** mel sequence at each step. Intermediate states are noisy approximations, not usable partial audio. Uses 2 steps (Turbo) or ~100 steps (Original). |
| **HiFiGAN (mels → waveform)** | No | Requires complete mel-spectrograms. Single forward pass — no iterative loop to intercept. F0 prediction and upsampling need full temporal context. |

### Why S3Gen Blocks Streaming

The S3Gen Conditional Flow Matching (CFM) model uses Euler ODE solving to denoise mel-spectrograms:

```python
# From flow_matching.py — CausalConditionalCFM.basic_euler()
for t, r in tqdm(zip(t_span[..., :-1], t_span[..., 1:])):
    dxdt = self.estimator.forward(x, ...)  # Entire mel at once
    x = x + dt * dxdt                      # Update entire mel
return x  # Only usable at the end
```

Each iteration refines the **entire** time dimension of the mel spectrogram. After step 1 of 10, you have a globally noisy mel — not a clean first-half and noisy second-half. Extracting a partial mel and running it through the vocoder produces noise, not audio.

### Why HiFiGAN Blocks Streaming

HiFiGAN's `inference()` method takes a complete mel spectrogram and returns a complete waveform in a single forward pass. It uses:
- F0 prediction across the full sequence
- Source filtering with temporal context
- Multi-scale upsampling that operates on the full input

Feeding a partial mel produces artifacts at boundaries and missing temporal context causes the F0 predictor to generate incorrect pitch contours.

---

## Hooks and Callbacks

**None exist.** Both `generate()` methods in `tts.py` and `tts_turbo.py` are blocking functions that return a single tensor. There are `tqdm` progress bars in the sampling loops, but these are for display only — no mechanism to extract intermediate results.

The code would require significant refactoring to expose intermediate outputs:
- `T3.inference()` would need to yield partial token sequences
- `S3Token2Mel.forward()` would need to yield partial mels (architecturally unsound)
- `HiFTGenerator.inference()` would need a chunked mode (not designed for this)

---

## Turbo Tier Streaming

Chatterbox Turbo uses the same pipeline with mean-flow CFM (only 2 denoising steps instead of ~100). The fundamental constraints are identical:
- S3Gen still operates on the full mel
- HiFiGAN still needs complete input
- The 2-step diffusion is faster but not streamable

---

## Prior Art Survey

| System | Architecture | Streaming? | Notes |
|--------|-------------|------------|-------|
| **XTTS v2** | GPT-2 + HiFiGAN | Yes (partial) | GPT decoder can yield mel chunks; custom vocoder handles variable-length input |
| **Bark** | Transformer → EnCodec | Community hacks only | No official streaming; some community forks attempt chunk-based output |
| **Tortoise-TTS** | Diffusion + UnivNet | No | Diffusion-based like Chatterbox; same constraints apply |
| **Piper** | VITS (end-to-end) | Yes (sentence-level) | Fast enough that streaming is less critical; process-level parallelism instead |
| **Chatterbox** | T3 + CFM + HiFiGAN | **No** | Diffusion-based mel generation is the blocker |

**Pattern:** Autoregressive models (XTTS, Bark) have some streaming potential because they generate sequential output. Diffusion-based models (Chatterbox, Tortoise) do not because they refine the entire output simultaneously.

---

## Minimum Viable Chunk Size

**Not applicable.** Since streaming within a single synthesis is not feasible, chunk-boundary analysis is moot. The relevant chunking is at the **text level** (sentence-boundary chunking via `tts_chunking.py`), which is already implemented and working.

---

## Interaction with Sentence-Boundary Chunking (WO-TTS-CHUNKING-001)

**Streaming does NOT replace chunking.** These are complementary strategies at different levels:

| Strategy | Level | Purpose |
|----------|-------|---------|
| Sentence-boundary chunking | Text | Split long text into synthesizable pieces (max 55 words) |
| Audio streaming | Audio | Start playback before generation finishes |

Since audio-level streaming is not feasible, **sentence-boundary chunking remains the primary latency reduction strategy** for long text. It works by:
1. Splitting text at sentence boundaries
2. Synthesizing each chunk independently
3. Overlapping synthesis of chunk N+1 with playback of chunk N (within a persistent server)

This overlap-and-play strategy achieves a similar effect to streaming: the listener hears audio before the full text is synthesized. The persistent server (RQ-TTS-003) makes this pattern even more effective by eliminating the cold start before the first chunk.

**No scope change needed for WO-TTS-CHUNKING-001.** The chunking WO should proceed as designed.

---

## Alternative Approaches to Perceived Latency Reduction

Since true streaming is not feasible, here are the effective alternatives (in priority order):

| Priority | Approach | Latency Impact | Status |
|----------|----------|----------------|--------|
| 1 | **Persistent server (RQ-TTS-003)** | -15s cold start elimination | Designed, ready to build |
| 2 | **Turbo tier for short lines** | 1.5s vs 3.5s per sentence | Already implemented |
| 3 | **Sentence chunking + overlap playback** | Start audio before full text done | Chunking done; overlap needs server |
| 4 | **Prefetch/warm-up** | Pre-synthesize predictable next lines | Future optimization |

---

## Recommendation

**Do not pursue audio-level streaming for Chatterbox.** The architecture makes it infeasible without replacing the diffusion-based mel generation with an autoregressive alternative (which would be a different TTS system entirely).

**Focus on the persistent server (RQ-TTS-003) + sentence chunking (WO-TTS-CHUNKING-001).** Together, these eliminate cold start and enable overlap-and-play, achieving most of the perceived latency benefit that streaming would provide.

If true streaming becomes a hard requirement in the future, evaluate alternative TTS backends:
- **XTTS v2:** Autoregressive mel generation, supports streaming, voice cloning. Larger model (~6 GB VRAM).
- **Piper:** VITS-based, very fast, no GPU needed. Lower quality, no voice cloning.

This would be a backend replacement investigation, not a Chatterbox optimization.

---

*Key question answered: We CANNOT start playing audio before generation is complete. The diffusion architecture refines the entire output simultaneously, and the vocoder needs complete input. Sentence-level chunking with overlap playback is the practical alternative.*
