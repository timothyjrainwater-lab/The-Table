# RQ-TTS-002: Qwen3 TTS vs Kokoro TTS Comparative Analysis

**Research Request**: RQ-TTS-002
**Date**: 2026-02-11
**Researcher**: SONNET-H
**Status**: COMPLETE

---

## Executive Summary

**RECOMMENDATION: KEEP KOKORO — DO NOT SWITCH**

Qwen3-TTS is a legitimate, high-quality TTS system released by Alibaba's Qwen team in January 2026. However, it **FAILS our critical constraints** and offers no compelling advantage over our current Kokoro implementation:

- ❌ **VRAM Constraint Violated**: Requires GPU for acceptable latency (<300ms). CPU-only inference yields 3-5x RTF (90-150s for 30s audio), making real-time interaction impossible.
- ❌ **Minimum 0.6B parameters** (7.3x larger than Kokoro's 82M), with heavier resource footprint (2.52 GB model vs Kokoro's lightweight deployment).
- ❌ **Installation complexity**: While pip-installable, practical usage requires GPU setup, FlashAttention 2 for stated latency, and careful environment management.
- ✅ Apache 2.0 license (same as Kokoro)
- ✅ Streaming support (dual-track architecture)
- ✅ Voice cloning/personas (but more complex than Kokoro's ID system)

**Kokoro remains the optimal choice** for our use case: 82M parameters, 150-300 MB RAM, CPU-only sub-300ms latency, trivial pip installation (`pip install kokoro-onnx`), 42 passing tests, and 8 configured personas. Switching to Qwen3 would sacrifice our zero-VRAM requirement for marginal (if any) quality gains.

---

## 1. Qwen3-TTS Overview

### Release & Architecture

- **Released**: January 22, 2026 by Alibaba's Qwen team
- **Technical Report**: arXiv:2601.15621
- **Architecture**: Dual-track LM with discrete multi-codebook design
  - Track 1: Plans overall speech prosody
  - Track 2: Outputs audio in real-time as text arrives
- **Model Variants**:
  - **Qwen3-TTS-12Hz-1.7B**: Flagship model (1.7B parameters, 4.54 GB)
  - **Qwen3-TTS-12Hz-0.6B**: Lightweight variant (600M parameters, 2.52 GB)

### Training & Capabilities

- **Training Data**: 5+ million hours of speech across 10 languages
- **Languages**: Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish, Italian
- **Voice Cloning**: 3-second rapid voice cloning from user audio
- **Voice Design**: Description-based voice synthesis, 9 premium timbres
- **Streaming**: Dual-track architecture with claimed 97ms end-to-end latency

### Technical Components

- **Qwen-TTS-Tokenizer-12Hz**: 12.5 Hz, 16-layer multi-codebook design, lightweight causal ConvNet (97ms first-packet emission)
- **Qwen-TTS-Tokenizer-25Hz**: Single-codebook codec for semantic content, streaming waveform reconstruction via block-wise DiT

**Sources**:
- [GitHub - QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)
- [Qwen3-TTS Technical Report (arXiv)](https://arxiv.org/abs/2601.15621)
- [Qwen3-TTS Family Blog Post](https://qwen.ai/blog?id=qwen3tts-0115)
- [Qwen/Qwen3-TTS-12Hz-0.6B-Base (Hugging Face)](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base)

---

## 2. Head-to-Head Comparison

| **Dimension** | **Kokoro TTS (Current)** | **Qwen3-TTS 0.6B** | **Qwen3-TTS 1.7B** |
|---------------|--------------------------|--------------------|--------------------|
| **Parameters** | 82M | 600M (7.3x larger) | 1.7B (20.7x larger) |
| **Model Size** | ~150-300 MB (ONNX) | 2.52 GB | 4.54 GB |
| **RAM (CPU)** | 150-300 MB | ~2-3 GB estimated | ~4-6 GB estimated |
| **VRAM (GPU)** | **0 GB (CPU-only)** | 8 GB (RTX 3060 Ti minimum) | 16 GB (RTX 4080 recommended) |
| **CPU Latency** | **100-300ms** ✅ | 3-5x RTF (90-150s for 30s audio) ❌ | 3-5x RTF (worse) ❌ |
| **GPU Latency** | N/A | ~0.85-1.15x RTF (8GB VRAM) | Requires 16GB VRAM + FA2 for 97ms claim |
| **Quality (MOS)** | 4.0/5, HF TTS Arena 1st place | No published MOS scores | Claimed "state-of-the-art, human-like" |
| **License** | Apache 2.0 ✅ | Apache 2.0 ✅ | Apache 2.0 ✅ |
| **Installation** | `pip install kokoro-onnx` (trivial) | `pip install qwen-tts` (simple) + GPU setup | Same as 0.6B + 16GB GPU |
| **Build Tools** | None (ONNX binary) | None (pip-installable) | None (pip-installable) |
| **ONNX Support** | Native | Community ONNX-INT8 available | No evidence of ONNX for 1.7B |
| **Multi-Voice** | 8 voice IDs (simple switch) | 9 premium timbres + 3s cloning | Same as 0.6B |
| **Voice Switching** | Direct voice ID parameter | 3-step: VoiceDesign → create_voice_clone_prompt → generate_voice_clone | Same as 0.6B |
| **Streaming** | Batch-only (acceptable for our use) | Dual-track streaming (97ms claim requires GPU+FA2) | Same as 0.6B |
| **Maturity** | Stable (released 2024/2025) | Released Jan 22, 2026 (~3 weeks old) | Same as 0.6B |
| **Community** | Established (HF Arena winner) | **7.4k GitHub stars, 900 forks** (rapid growth) | Same as 0.6B |
| **Our Implementation** | **42 passing tests, 8 personas** ✅ | Not implemented | Not implemented |

**Critical Constraint Violations**:
- ❌ **VRAM Requirement**: Qwen3 requires GPU for acceptable latency. CPU-only inference is 3-5x RTF (non-real-time).
- ❌ **Latency**: CPU inference misses our <300ms target by an order of magnitude.
- ❌ **Complexity**: 7.3-20.7x larger models with no clear quality advantage over Kokoro (which achieved 1st place in HF TTS Arena).

**Sources**:
- [Kokoro TTS comparison (Inferless)](https://www.inferless.com/learn/comparing-different-text-to-speech---tts--models-part-2)
- [Best Open-Source TTS Models in 2026 (BentoML)](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models)
- [Qwen3-TTS Performance Benchmarks 2026](https://qwen3-tts.app/blog/qwen3-tts-performance-benchmarks-hardware-guide-2026)
- [Qwen3-TTS CPU Inference Analysis (Medium)](https://medium.com/@zh.milo/qwen3-tts-the-complete-2026-guide-to-open-source-voice-cloning-and-ai-speech-generation-1a2efca05cd6)
- [QwenLM/Qwen3-TTS GitHub](https://github.com/QwenLM/Qwen3-TTS)

---

## 3. Quality Assessment

### Kokoro TTS

- **MOS**: 4.0/5 (reported in community benchmarks)
- **Benchmark Win**: 1st place in HuggingFace TTS Spaces Arena for single-speaker speech quality
- **Architecture**: Optimized StyleTTS2 variant with iSTFTNet waveform generation
- **Subjective Quality**: Described as "life-like speech" with 96× real-time on basic cloud GPU
- **Efficiency**: "Clear winner for speed, consistently processing texts in under 0.3 seconds across all tested lengths"

### Qwen3-TTS

- **MOS**: **No published MOS scores found** in any source
- **Quality Claims**: "State-of-the-art, human-like quality" (from vendor), "delivers human-like quality" (community)
- **Benchmark Data**: No objective quality metrics (WER, MOS, naturalness scores) found in search results
- **Subjective Impressions**: Community describes 1.7B as higher quality/expressivity than 0.6B, but no direct Kokoro comparison

### Gap Analysis

**Key Finding**: Qwen3-TTS provides **no published objective quality data** (MOS, WER, naturalness scores) to justify switching from our proven Kokoro implementation (4.0 MOS, 1st place HF Arena).

- Kokoro has established benchmarks showing 4.0/5 MOS and competitive arena performance
- Qwen3-TTS relies on vendor claims and lacks independent evaluation
- The 7.3-20.7x parameter increase **does not guarantee** quality improvement (Kokoro demonstrates that smaller, optimized models can win quality competitions)

**Evaluation Criteria Comparison**:
| **Criterion** | **Target** | **Kokoro** | **Qwen3-TTS 0.6B** |
|---------------|------------|------------|--------------------|
| **Naturalness (MOS)** | ≥3.5 | 4.0 ✅ | Unknown (no data) |
| **Intelligibility (WER)** | ≤5% | Not published | Not published |
| **Latency** | ≤300ms | 100-300ms ✅ | 3-5x RTF (CPU) ❌ |
| **Voice Fatigue** | ≥3 hours | Unknown | Unknown |
| **Local-first** | No internet | ✅ | ✅ |
| **VRAM** | 0 GB | **0 GB ✅** | 8+ GB ❌ |

**Sources**:
- [Kokoro-82M Quality Analysis (Medium)](https://medium.com/data-science-in-your-pocket/kokoro-82m-the-best-tts-model-in-just-82-million-parameters-512b4ba4f94c)
- [Best ElevenLabs Alternatives 2026 (OCDevel)](https://ocdevel.com/blog/20250720-tts)
- [Qwen3-TTS Quality Claims (GitHub)](https://github.com/QwenLM/Qwen3-TTS)

---

## 4. Resource Requirements

### Memory Footprint

**Kokoro TTS**:
- Model Size: ~150-300 MB (ONNX optimized)
- Runtime RAM: 150-300 MB
- VRAM: **0 GB (CPU-only inference)**

**Qwen3-TTS 0.6B**:
- Model Size: 2.52 GB (8.4-16.8x larger)
- Runtime RAM: ~2-3 GB (estimated based on model size)
- VRAM: 8 GB minimum (RTX 3060 Ti / 4060 Ti)
  - RTF ~0.85-1.15 on 8GB cards
  - CPU-only: 3-5x RTF (non-real-time)

**Qwen3-TTS 1.7B**:
- Model Size: 4.54 GB (15-30x larger)
- Runtime RAM: ~4-6 GB (estimated)
- VRAM: 16 GB recommended (RTX 4080 Super)
  - 8GB cards: "Not recommended due to VRAM constraints and poor real-time performance"
  - CPU-only: Worse than 0.6B

### Latency Analysis

**Kokoro TTS**:
- **CPU Inference**: 100-300ms (meets our <300ms target) ✅
- **GPU Inference**: Not applicable (not needed)

**Qwen3-TTS**:
- **CPU Inference**: 3-5x RTF = **90-150 seconds** for 30 seconds of audio ❌
  - "Go make coffee" latencies
  - Described as "viable for batch processing workloads" only
- **GPU Inference (8GB VRAM)**: 0.85-1.15x RTF (~1000-1150ms for 1s audio) for 0.6B
- **GPU Inference (16GB VRAM + FA2)**: Claimed 97ms with FlashAttention 2 for 1.7B
  - Requires Ampere+ GPU (RTX 30xx/40xx/50xx)
  - "Without FA2 support, the inference speed drops dramatically"

### Critical Constraint: Zero-VRAM Requirement

**Our Constraint**: "We need 0 GB VRAM for TTS (GPU budget goes to LLM + image gen)"

- **Kokoro**: ✅ Meets constraint perfectly (CPU-only, <300ms latency)
- **Qwen3-TTS**: ❌ **Requires GPU for acceptable performance**
  - CPU-only inference is 10-50x slower than target latency
  - Minimum 8GB VRAM for real-time inference
  - GPU acceleration is "strongly recommended for practical use"

**Sources**:
- [Qwen3-TTS Performance Benchmarks 2026](https://qwen3-tts.app/blog/qwen3-tts-performance-benchmarks-hardware-guide-2026)
- [Qwen3-TTS CPU Inference Guide (Medium)](https://medium.com/@zh.milo/qwen3-tts-the-complete-2026-guide-to-open-source-voice-cloning-and-ai-speech-generation-1a2efca05cd6)
- [DigitalOcean TTS Model Comparison](https://www.digitalocean.com/community/tutorials/best-text-to-speech-models)

---

## 5. Installation & Integration

### Installation Complexity

**Kokoro TTS (Current)**:
```bash
pip install kokoro-onnx
```
- No build tools required (ONNX binary)
- No GPU setup required
- Works out-of-box on Windows/Linux/Mac
- **Current Status**: Fully implemented (`aidm/immersion/kokoro_tts_adapter.py`, 510 lines, 42 tests)

**Qwen3-TTS**:
```bash
pip install -U qwen-tts
# For ONNX (CPU):
pip install onnxruntime
# For GPU (required for real-time):
pip install onnxruntime-gpu  # or onnxruntime-rocm for AMD
```
- No MSVC build tools required (pip-installable)
- GPU setup required for acceptable latency
- Environment management recommended (Python 3.12 conda env)
- ONNX support: Community INT8 models available (sivasub987/Qwen3-TTS-0.6B-ONNX-INT8)

### Voice Persona Management

**Kokoro TTS**:
- **System**: Simple voice ID parameter (e.g., `voice="af_bella"`)
- **Current Implementation**: 8 configured voice personas
- **Switch Cost**: Single parameter change in function call

**Qwen3-TTS**:
- **System**: 3-step workflow for consistent persona
  1. Use `VoiceDesign` model to synthesize reference clip matching target persona
  2. Call `create_voice_clone_prompt` to build reusable prompt from reference
  3. Call `generate_voice_clone` with `voice_clone_prompt` for new content
- **Voices**: 9 premium timbres + 3-second voice cloning from user audio
- **Switch Cost**: More complex workflow, but more flexible for custom voices

### Streaming Support

**Kokoro TTS**:
- Batch-only (entire utterance generated at once)
- Acceptable for our turn-based D&D use case (full responses generated per turn)

**Qwen3-TTS**:
- Dual-track streaming architecture with 97ms claimed latency
- **However**: 97ms latency requires GPU + FlashAttention 2
- CPU-only streaming is still 3-5x RTF (unusable for real-time)
- Streaming advantage **negated by CPU-only constraint**

**Sources**:
- [Qwen3-TTS PyPI Package](https://pypi.org/project/qwen-tts/)
- [Qwen3-TTS Installation Guide (GitHub)](https://github.com/QwenLM/Qwen3-TTS)
- [Qwen3-TTS Voice Cloning Workflow (Hugging Face)](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)
- [Qwen3-TTS ONNX Models (Hugging Face)](https://huggingface.co/sivasub987/Qwen3-TTS-0.6B-ONNX-INT8)

---

## 6. Maturity & Community

### Kokoro TTS

**Maturity**:
- Released 2024/2025 (established model)
- StyleTTS2-based architecture (proven foundation)
- Won 1st place in HuggingFace TTS Spaces Arena
- Stable ONNX runtime (no PyTorch dependencies)

**Community**:
- Active Hugging Face presence (hexgrad/Kokoro-82M)
- Featured in multiple TTS benchmarks (Inferless, BentoML, DigitalOcean)
- ONNX optimization indicates production-ready status

**Risk Assessment**:
- Low abandonment risk (ONNX models are self-contained)
- No corporate backing, but StyleTTS2 foundation is well-established
- Our implementation is **fully tested and operational** (42 tests passing)

### Qwen3-TTS

**Maturity**:
- **Released January 22, 2026** (~3 weeks old as of this report)
- Corporate backing: Alibaba Cloud (Qwen team)
- Technical report published (arXiv:2601.15621)
- Multiple model variants (0.6B, 1.7B, CustomVoice, VoiceDesign)

**Community**:
- **7.4k GitHub stars, 900 forks** (rapid growth in 3 weeks)
- Active development: Recent commits, ongoing issue resolution
- **Community Projects**:
  - ComfyUI integration (updated Feb 4, 2026)
  - Apple Silicon support (confirmed working)
  - Home Assistant integration
  - Android TTS application
- Active discussions on Hacker News, Reddit, community forums

**Risk Assessment**:
- Low abandonment risk (corporate backing + strong community momentum)
- Very new (3 weeks), but Alibaba's track record suggests long-term support
- Rapid community adoption indicates staying power
- **However**: Youth means fewer battle-tested production deployments than Kokoro

**Development Velocity Comparison**:
- Kokoro: Mature, stable, proven in production
- Qwen3-TTS: Rapid development, frequent updates, but **unproven at scale**

**Sources**:
- [QwenLM/Qwen3-TTS GitHub Statistics](https://github.com/QwenLM/Qwen3-TTS)
- [ComfyUI-Qwen-TTS Integration](https://github.com/flybirdxx/ComfyUI-Qwen-TTS)
- [Qwen3-TTS Release Announcement](https://qwen.ai/blog?id=qwen3tts-0115)
- [Hacker News Discussion](https://news.ycombinator.com/item?id=46719229)

---

## 7. Integration Cost Assessment

### Current Kokoro Implementation

**Files**:
- `aidm/immersion/kokoro_tts_adapter.py` (510 lines)
- `tests/immersion/test_kokoro_tts.py` (42 tests, all passing)

**Adapter API**:
```python
class KokoroTTSAdapter:
    def synthesize(self, text: str, voice: str) -> bytes:
        """Generate speech audio from text."""
        # ONNX inference, returns WAV bytes
```

**Test Coverage**:
- 8 voice persona tests
- Multi-sentence handling
- SSML/prosody tests
- Error handling
- File I/O tests
- WO-020 acceptance criteria: All passing ✅

### Estimated Qwen3-TTS Integration Cost

**Rewrite Scope**:
- **Adapter Module** (`qwen_tts_adapter.py`):
  - 70-80% rewrite (different model loading, inference API, voice management)
  - Voice persona system: 3-step workflow vs simple ID parameter
  - Model loading: HuggingFace transformers vs ONNX runtime
  - Estimated: 400-600 lines of new code
- **Test Suite**:
  - 50% rewrite (API differences, new test cases for voice cloning workflow)
  - GPU/CPU performance tests needed
  - Estimated: 20-30 tests need modification

**New Requirements**:
- GPU passthrough to container (if deploying containerized)
- FlashAttention 2 setup for claimed latency
- Larger model download/storage (2.52 GB vs 150-300 MB)
- Voice persona prompt engineering (3-step workflow)

**Risk Factors**:
- **No CPU-only fallback**: If GPU unavailable, latency becomes unacceptable (3-5x RTF)
- **Environment complexity**: Python 3.12, CUDA setup, FA2 compilation
- **Model newness**: 3 weeks old, potential for breaking changes or undocumented edge cases

**Estimated Effort**:
- Adapter rewrite: 8-12 hours
- Test suite update: 4-6 hours
- GPU setup/debugging: 4-8 hours (depends on environment)
- Voice persona engineering: 2-4 hours (learning 3-step workflow)
- **Total**: 18-30 hours (2.5-4 days)

**ROI Analysis**:
- **Cost**: 18-30 hours of engineering time, increased resource requirements, operational complexity
- **Benefit**: No proven quality improvement over Kokoro (no MOS data), advanced voice cloning (not needed for our 8 fixed personas)
- **Conclusion**: **Negative ROI** — we lose CPU-only capability for uncertain gains

---

## 8. Constraint Checklist: Qwen3-TTS vs Project Requirements

| **Constraint** | **Requirement** | **Kokoro TTS** | **Qwen3-TTS 0.6B** | **Pass?** |
|----------------|-----------------|----------------|-----------------------|-----------|
| **VRAM** | 0 GB (GPU for LLM/image gen) | 0 GB ✅ | 8+ GB ❌ | **FAIL** |
| **Latency** | ≤300ms perceived | 100-300ms ✅ | 3-5x RTF (CPU) ❌ | **FAIL** |
| **License** | Apache 2.0 or permissive | Apache 2.0 ✅ | Apache 2.0 ✅ | PASS |
| **Installation** | pip, no MSVC | pip install kokoro-onnx ✅ | pip install qwen-tts ✅ | PASS |
| **Quality (MOS)** | ≥3.5 | 4.0 ✅ | Unknown (no data) | UNKNOWN |
| **CPU Inference** | Required | ✅ | ❌ (non-real-time) | **FAIL** |

**Critical Failures**: 3/6 constraints violated (VRAM, latency, CPU inference)

---

## 9. Recommendation

### KEEP KOKORO — DO NOT SWITCH TO QWEN3-TTS

**Rationale**:

1. **Hard Constraint Violation**: Qwen3-TTS requires GPU for real-time inference, violating our zero-VRAM budget. CPU-only inference (3-5x RTF) misses our <300ms latency target by 10-50x.

2. **No Proven Quality Advantage**: Qwen3-TTS lacks published MOS scores or objective benchmarks. Kokoro has 4.0 MOS and 1st place HF Arena ranking. The 7.3x parameter increase does not guarantee quality improvement (Kokoro proves smaller models can win quality competitions).

3. **High Integration Cost**: 18-30 hours of engineering effort to rewrite adapter and tests, with no ROI. We lose CPU-only capability for uncertain gains.

4. **Operational Complexity**: Qwen3-TTS requires GPU setup, FlashAttention 2 for claimed latency, larger models (2.52 GB vs 150-300 MB), and 3-step voice persona workflow vs Kokoro's simple ID parameter.

5. **Maturity Risk**: Qwen3-TTS is 3 weeks old (released Jan 22, 2026). Kokoro is battle-tested and stable. While Alibaba backing reduces abandonment risk, production edge cases are not yet discovered.

6. **Current Implementation Works**: Our Kokoro adapter has 42 passing tests, 8 configured personas, and meets all acceptance criteria (WO-020). **If it ain't broke, don't fix it.**

### When to Reconsider

Re-evaluate Qwen3-TTS if ANY of the following change:
- **GPU Budget Opens**: If we allocate 8-16GB VRAM to TTS (e.g., separate TTS GPU)
- **CPU Performance Improves**: If future optimizations reduce CPU latency to <300ms
- **Quality Gap Emerges**: If published benchmarks show Qwen3 > Kokoro by ≥0.5 MOS
- **Voice Cloning Needed**: If project scope expands to require dynamic voice cloning (not just 8 fixed personas)
- **Kokoro Abandonment**: If Kokoro project is abandoned or security issues emerge

### Alternative Actions

Instead of switching TTS models, consider:
1. **Fine-tune Kokoro voices**: Adjust existing 8 personas for better D&D character fit
2. **Optimize Kokoro deployment**: Investigate ONNX quantization for even lower latency
3. **Expand Kokoro personas**: Add more voice IDs (cheap, no architecture change)
4. **Wait for Qwen3 maturity**: Re-evaluate in 6-12 months after community battle-testing

---

## 10. Sources Summary

**Primary Sources**:
- [GitHub - QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)
- [Qwen3-TTS Technical Report (arXiv:2601.15621)](https://arxiv.org/abs/2601.15621)
- [Qwen3-TTS Blog Post (Qwen AI)](https://qwen.ai/blog?id=qwen3tts-0115)
- [Qwen3-TTS Performance Benchmarks 2026](https://qwen3-tts.app/blog/qwen3-tts-performance-benchmarks-hardware-guide-2026)
- [12 Best Open-Source TTS Models Compared (Inferless)](https://www.inferless.com/learn/comparing-different-text-to-speech---tts--models-part-2)
- [Best Open-Source TTS Models in 2026 (BentoML)](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models)
- [Best ElevenLabs Alternatives 2026 (OCDevel)](https://ocdevel.com/blog/20250720-tts)
- [Kokoro-82M Analysis (Medium)](https://medium.com/data-science-in-your-pocket/kokoro-82m-the-best-tts-model-in-just-82-million-parameters-512b4ba4f94c)
- [Qwen3-TTS Guide (Medium)](https://medium.com/@zh.milo/qwen3-tts-the-complete-2026-guide-to-open-source-voice-cloning-and-ai-speech-generation-1a2efca05cd6)

**Model Repositories**:
- [Qwen/Qwen3-TTS-12Hz-0.6B-Base (Hugging Face)](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base)
- [Qwen/Qwen3-TTS-12Hz-1.7B-Base (Hugging Face)](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base)
- [hexgrad/Kokoro-82M (Hugging Face)](https://huggingface.co/hexgrad/Kokoro-82M)
- [sivasub987/Qwen3-TTS-0.6B-ONNX-INT8 (Hugging Face)](https://huggingface.co/sivasub987/Qwen3-TTS-0.6B-ONNX-INT8)

**Installation & Integration**:
- [qwen-tts (PyPI)](https://pypi.org/project/qwen-tts/)
- [ComfyUI-Qwen-TTS Integration (GitHub)](https://github.com/flybirdxx/ComfyUI-Qwen-TTS)
- [Qwen3-TTS Demo (Hugging Face Spaces)](https://huggingface.co/spaces/Qwen/Qwen3-TTS)

**Community & Discussion**:
- [Hacker News: Qwen3-TTS family is now open sourced](https://news.ycombinator.com/item?id=46719229)
- [DigitalOcean: Best Text-to-Speech Models](https://www.digitalocean.com/community/tutorials/best-text-to-speech-models)

---

**END OF REPORT**
**Recommendation**: KEEP KOKORO — DO NOT SWITCH
**Critical Constraint Failures**: VRAM (requires 8+ GB), Latency (3-5x RTF on CPU), No real-time CPU inference
**Next Action**: File this report, continue with current Kokoro implementation (WO-020 complete)
