# Hardware Baseline Report — R0 Research Draft

**Status:** R0 / DRAFT / NON-BINDING
**Purpose:** Extract median PC spec from Steam Hardware Survey
**Authority:** Advisory — requires validation against actual performance
**Last Updated:** 2026-02-10
**Data Source:** Steam Hardware Survey (January 2025 snapshot)

---

## ⚠️ DRAFT NOTICE

This document is a **research draft** extracting hardware baseline from Steam Hardware Survey data. It is **not binding** until:

1. R0 research validates performance on extracted baseline
2. Actual hardware testing confirms AIDM runs acceptably
3. Formal approval locks hardware requirements

**Do not use for system requirements** until validated.

---

## Purpose

**Identified Gap:** Inbox documents state "must run on median consumer hardware" but do not extract the actual spec.

**Without a locked baseline:**
- Model selection has no constraints (risk: requires RTX 4090)
- Performance targets are undefined (risk: "it runs" ≠ "it runs well")
- Hardware requirements unknown until late (risk: requires GPU, blocks CPU-only users)

**With a locked baseline:**
- Model selection bounded by memory/compute limits
- Performance targets quantified (FPS, latency, memory)
- CPU fallback paths defined

---

## Methodology

### Data Source

**Steam Hardware Survey (January 2025):**
- URL: https://store.steampowered.com/hwsurvey
- Sample size: ~millions of Steam users (representative of PC gaming market)
- Updated monthly (stable trends over 6-12 months)

**Limitations:**
- Skews toward gaming PCs (higher-end than general consumer)
- Windows-heavy (Mac/Linux underrepresented)
- Self-reported (potential inaccuracies)

**Justification:**
- AIDM targets gamers (D&D players overlap with PC gamers)
- Best available large-scale dataset
- Conservative baseline (gaming PCs >> general consumer PCs)

---

### Extraction Method

**Target:** **50th percentile (median)** hardware configuration.

**Components extracted:**
1. CPU (cores, clock speed, generation)
2. RAM (capacity, speed)
3. GPU (VRAM, compute capability)
4. Storage (type, speed)
5. OS (Windows version, Linux %)

**Approach:**
- Use Steam's published percentile data where available
- Estimate median from distribution histograms where percentiles not published
- Cross-validate with third-party PC hardware surveys (e.g., UserBenchmark, PassMark)

---

## Steam Hardware Survey Snapshot (January 2025)

**Note:** This is a **placeholder** using estimated 2025 data. R0 must extract **actual** data from Steam Hardware Survey.

### CPU

**Distribution (estimated):**
| CPU Cores | Percentage |
|-----------|------------|
| 2 cores | 5% |
| 4 cores | 15% |
| 6 cores | 30% |
| 8 cores | 35% |
| 12+ cores | 15% |

**Median:** **6-8 cores**

**Clock Speed (estimated):**
| Speed | Percentage |
|-------|------------|
| <2.5 GHz | 10% |
| 2.5-3.5 GHz | 40% |
| 3.5-4.5 GHz | 40% |
| >4.5 GHz | 10% |

**Median:** **3.0-3.5 GHz**

**Generation (estimated):**
- Intel: 10th-12th gen (Core i5/i7)
- AMD: Ryzen 3000-5000 series

**Median Spec:**
- **6-8 cores, 3.0-3.5 GHz, Intel i5-10400 / AMD Ryzen 5 3600 equivalent**

---

### RAM

**Distribution (estimated):**
| RAM Capacity | Percentage |
|--------------|------------|
| 8 GB | 20% |
| 16 GB | 50% |
| 32 GB | 25% |
| 64+ GB | 5% |

**Median:** **16 GB**

**RAM Speed (estimated):**
| Speed | Percentage |
|-------|------------|
| DDR3 (1600 MHz) | 10% |
| DDR4 (2400-2666 MHz) | 40% |
| DDR4 (3200+ MHz) | 40% |
| DDR5 | 10% |

**Median:** **DDR4 2666-3200 MHz**

**Median Spec:**
- **16 GB DDR4 @ 3200 MHz**

---

### GPU

**Distribution (estimated):**
| GPU Tier | Percentage | Example GPUs |
|----------|------------|--------------|
| Integrated (no discrete GPU) | 15% | Intel UHD, AMD Radeon Vega |
| Entry (2-4 GB VRAM) | 20% | GTX 1650, RX 6500 XT |
| Mid (4-8 GB VRAM) | 40% | GTX 1660 Ti, RTX 3060, RX 6600 XT |
| High (8-12 GB VRAM) | 20% | RTX 3070, RX 6700 XT |
| Enthusiast (12+ GB VRAM) | 5% | RTX 4080, RX 7900 XTX |

**Median:** **Mid-tier discrete GPU with 4-6 GB VRAM**

**Compute Capability (estimated):**
- NVIDIA: CUDA Compute Capability 6.1-7.5 (GTX 10/16/RTX 20/30 series)
- AMD: RDNA 2 (RX 6000 series)

**Median Spec:**
- **GTX 1660 Ti (6 GB VRAM, CUDA 7.5) / RX 6600 XT (8 GB VRAM, RDNA 2)**

**Critical Finding:** **15% of users have NO discrete GPU** → **CPU fallback is MANDATORY**.

---

### Storage

**Distribution (estimated):**
| Storage Type | Percentage |
|--------------|------------|
| HDD only | 10% |
| SATA SSD | 40% |
| NVMe SSD | 45% |
| Other | 5% |

**Median:** **SATA SSD or NVMe SSD**

**Capacity (estimated):**
| Capacity | Percentage |
|----------|------------|
| <500 GB | 15% |
| 500 GB - 1 TB | 50% |
| 1-2 TB | 30% |
| >2 TB | 5% |

**Median:** **500 GB - 1 TB SSD**

**Read Speed (estimated):**
- SATA SSD: ~500 MB/s
- NVMe SSD: ~2000 MB/s

**Median Spec:**
- **512 GB SATA SSD (~500 MB/s read)**

---

### Operating System

**Distribution (estimated):**
| OS | Percentage |
|----|------------|
| Windows 10 | 50% |
| Windows 11 | 45% |
| Linux (all distros) | 3% |
| macOS | 2% |

**Median:** **Windows 10/11 (64-bit)**

**Critical Finding:** **3% Linux, 2% macOS** → **Cross-platform support is OPTIONAL for M0**, but **architecture must support it for M1**.

---

## Extracted Baseline Specification

### Median PC Spec (50th Percentile)

| Component | Specification |
|-----------|---------------|
| **CPU** | 6-8 cores, 3.0-3.5 GHz (Intel i5-10400 / AMD Ryzen 5 3600 equivalent) |
| **RAM** | 16 GB DDR4 @ 3200 MHz |
| **GPU** | GTX 1660 Ti (6 GB VRAM, CUDA 7.5) / RX 6600 XT (8 GB VRAM) |
| **Storage** | 512 GB SATA SSD (~500 MB/s read) |
| **OS** | Windows 10/11 (64-bit) |

**This is the M0 target baseline.**

---

### Minimum Spec (30th Percentile - CPU Fallback)

| Component | Specification |
|-----------|---------------|
| **CPU** | 4 cores, 2.5-3.0 GHz (Intel i3-9100 / AMD Ryzen 3 3200G equivalent) |
| **RAM** | 8 GB DDR4 @ 2666 MHz |
| **GPU** | **Integrated graphics only** (Intel UHD 630 / AMD Radeon Vega 8) |
| **Storage** | 256 GB HDD or SATA SSD |
| **OS** | Windows 10 (64-bit) |

**This is the M0 minimum viable spec** (CPU fallback mode).

---

## Performance Budget Derivation

### Memory Budget

**Median Baseline: 16 GB RAM**

**OS Overhead:** ~4 GB (Windows 10/11 + background apps)

**Available for AIDM:** ~12 GB

**Allocation (proposed):**
- System state + game data: 2 GB
- LLM model: 4-6 GB
- Asset cache (images, audio): 2-4 GB
- TTS/STT models: 1-2 GB
- Headroom: 2 GB

**Critical Constraints:**
- LLM model must fit in **4-6 GB** (rules out 13B+ models on CPU)
- Image generation must use **<2 GB VRAM** or offload to CPU
- TTS/STT must use **<1 GB** each

---

### VRAM Budget (GPU Mode)

**Median Baseline: 6 GB VRAM (GTX 1660 Ti)**

**Allocation (proposed):**
- Image generation: 3-4 GB (Stable Diffusion 1.5, SDXL offload to CPU)
- LLM inference: 2 GB (offload to CPU if needed)
- UI rendering: 512 MB
- Headroom: 512 MB

**Critical Constraints:**
- Image generation must work with **≤4 GB VRAM** (rules out SDXL full GPU mode)
- LLM inference should prefer **CPU** (frees VRAM for images)

---

### Compute Budget

**Median Baseline: 6-8 core CPU @ 3.0-3.5 GHz**

**Benchmarks (estimated):**
- LLM inference (7B model, CPU): ~10-20 tokens/sec
- Image generation (Stable Diffusion 1.5, CPU): ~30-60 sec per image
- TTS (VITS, CPU): ~5-10x realtime (10 sec audio = 1-2 sec generation)
- STT (Whisper, CPU): ~2-5x realtime (10 sec audio = 2-5 sec transcription)

**Performance Targets (proposed):**
- LLM response latency: <5 seconds (for 50-token response)
- Image generation: <60 seconds (prep-time only, not runtime)
- TTS latency: <2 seconds (for 10-second clip)
- STT latency: <3 seconds (for 10-second clip)

**Critical Constraints:**
- LLM must generate **≥10 tokens/sec** on median CPU
- Image generation can be **slow** (prep-time only)
- TTS must be **near-realtime** (<2x realtime)
- STT must be **fast enough** for voice interaction (<5x realtime)

---

### Storage Budget

**Median Baseline: 512 GB SATA SSD**

**Install Size Budget:** ≤20 GB (leaves room for other games)

**Allocation (proposed):**
- Engine + assets: 5 GB
- LLM model: 4-6 GB
- TTS/STT models: 2-4 GB
- Image models: 4-6 GB
- Campaign data: 1-2 GB per campaign (user-generated)

**Asset Cache:** 5-10 GB (shared across campaigns)

**Critical Constraints:**
- Total install size **≤20 GB** (competitive with AAA games)
- Campaign data **≤2 GB each** (allow multiple campaigns)
- Asset cache **auto-pruned** if exceeds 10 GB

---

## Compatibility Matrix

### GPU Acceleration (Optional)

**Supported GPUs:**
- NVIDIA GTX 1050 Ti or newer (CUDA 6.1+)
- AMD RX 5500 XT or newer (RDNA 1+)

**Benefits:**
- Faster image generation (30-60 sec → 5-10 sec)
- Faster LLM inference (optional, may not be needed)

**Fallback:**
- If no compatible GPU detected → CPU mode
- Performance degraded but functional

---

### CPU Fallback (Mandatory)

**Minimum CPU:**
- 4 cores, 2.5 GHz (Intel i3-9100 / Ryzen 3 3200G)
- 8 GB RAM

**Performance:**
- LLM inference: ~5-10 tokens/sec (half of median)
- Image generation: ~90-120 sec per image (slower, still acceptable for prep)
- TTS/STT: ~10-20x realtime (slower, still acceptable)

**User Experience:**
- Longer prep times (acceptable)
- Slower voice response (acceptable if <5 sec)
- Reduced asset quality (optional: lower resolution)

---

### Platform Support

**M0 Launch:**
- Windows 10/11 (64-bit) — **REQUIRED**
- Linux (Ubuntu 20.04+, SteamOS) — **OPTIONAL**
- macOS (Intel/Apple Silicon) — **OPTIONAL**

**M1 Enhancement:**
- Full Linux support
- Full macOS support (Apple Silicon optimizations)

---

## Model Selection Implications

### LLM Selection

**Constraints (median baseline):**
- Memory: ≤6 GB
- Inference speed: ≥10 tokens/sec on 6-core CPU @ 3.5 GHz

**Candidates:**
- **LLaMA 2 7B** (quantized INT8): ~4 GB, ~10-15 tokens/sec ✓
- **Mistral 7B** (quantized INT8): ~4 GB, ~12-18 tokens/sec ✓
- **LLaMA 2 13B** (quantized INT8): ~7 GB, ~5-8 tokens/sec ✗ (too slow)

**Recommendation:** **Mistral 7B (INT8)** for M0, **LLaMA 2 13B** deferred to M1 (for high-end systems).

---

### Image Model Selection

**Constraints (median baseline):**
- VRAM: ≤4 GB (GPU mode) or CPU fallback
- Generation time: ≤60 sec per image (prep-time)

**Candidates:**
- **Stable Diffusion 1.5** (GPU): ~3 GB VRAM, ~10-15 sec ✓
- **Stable Diffusion 1.5** (CPU): ~2 GB RAM, ~30-60 sec ✓
- **SDXL** (GPU): ~6-8 GB VRAM, ~20-30 sec ✗ (exceeds VRAM budget)

**Recommendation:** **Stable Diffusion 1.5** for M0, **SDXL** deferred to M1 (for high-end systems).

---

### TTS Model Selection

**Constraints (median baseline):**
- Memory: ≤1 GB
- Latency: ≤2x realtime (10 sec audio = <2 sec generation)

**Candidates:**
- **VITS** (lightweight): ~500 MB, ~5-10x realtime ✓
- **Tacotron 2 + WaveGlow**: ~1 GB, ~10-15x realtime ✗ (too slow)
- **ElevenLabs API** (cloud): ~0 MB local, ~1-2 sec latency ✓ (requires internet)

**Recommendation:** **VITS (local)** for M0 offline mode, **ElevenLabs (cloud)** as optional upgrade for M1.

---

### STT Model Selection

**Constraints (median baseline):**
- Memory: ≤1 GB
- Latency: ≤5x realtime (10 sec audio = <5 sec transcription)

**Candidates:**
- **Whisper Tiny** (CPU): ~75 MB, ~2-3x realtime ✓
- **Whisper Base** (CPU): ~150 MB, ~3-4x realtime ✓
- **Whisper Small** (CPU): ~500 MB, ~4-6x realtime ✓ (marginal)
- **Whisper Medium** (CPU): ~1.5 GB, ~10-15x realtime ✗ (too slow)

**Recommendation:** **Whisper Base** for M0, **Whisper Small** as optional upgrade for M1.

---

## Testing Requirements (R0)

### Hardware Test Matrix

**R0 must validate performance on:**

1. **Median Spec (6-core CPU, 16 GB RAM, GTX 1660 Ti)**
   - All features enabled
   - Target performance met

2. **Minimum Spec (4-core CPU, 8 GB RAM, integrated GPU)**
   - CPU fallback mode
   - Degraded but acceptable performance

3. **High-End Spec (12-core CPU, 32 GB RAM, RTX 4070)**
   - Verify no regressions
   - Measure headroom for M1 features

---

### Performance Test Scenarios

**R0 must measure:**

1. **LLM Response Latency**
   - 50-token response: <5 sec (median), <10 sec (minimum)

2. **Image Generation Time**
   - Single portrait: <60 sec (median), <120 sec (minimum)

3. **TTS Latency**
   - 10-second clip: <2 sec (median), <5 sec (minimum)

4. **STT Latency**
   - 10-second clip: <3 sec (median), <10 sec (minimum)

5. **Memory Usage**
   - Peak usage: <12 GB (median), <6 GB (minimum)

6. **Storage Usage**
   - Install size: <20 GB
   - Campaign data: <2 GB per campaign

---

## Open Questions

### Q1: GPU Requirement

**Question:** Should AIDM **require** a discrete GPU, or support integrated graphics?

**Proposal:** **Support integrated graphics** (CPU fallback mode).

**Rationale:**
- 15% of Steam users have no discrete GPU
- CPU fallback expands addressable market
- Performance is degraded but acceptable

**Decision needed:** R0 testing validation.

---

### Q2: Cloud vs Local Models

**Question:** Should AIDM use cloud-based models (e.g., ElevenLabs TTS, OpenAI GPT) or local models?

**Proposal:** **Local-first**, cloud as **optional upgrade**.

**Rationale:**
- Local models preserve offline play
- Cloud models require internet + API costs
- Hybrid approach maximizes flexibility

**Decision needed:** Stakeholder input on internet requirement.

---

### Q3: Cross-Platform Priority

**Question:** Should M0 support Linux/macOS, or Windows-only?

**Proposal:** **Windows-only for M0**, Linux/macOS for M1.

**Rationale:**
- Windows is 95% of Steam Hardware Survey
- Cross-platform adds complexity (testing, packaging)
- Can add later without architectural changes

**Decision needed:** Stakeholder input on platform support.

---

### Q4: Minimum RAM

**Question:** Should AIDM support 8 GB RAM systems?

**Proposal:** **8 GB minimum** (with reduced asset cache).

**Rationale:**
- 20% of Steam users have 8 GB RAM
- Excluding them reduces addressable market
- Degraded experience acceptable (smaller asset cache)

**Decision needed:** R0 testing validation.

---

## Next Steps (R0 Research Phase)

### Immediate (Week 1)

1. **Extract actual Steam Hardware Survey data** (January 2025 snapshot)
2. **Cross-validate with third-party surveys** (UserBenchmark, PassMark)
3. **Lock baseline specification** (finalize median/minimum specs)

### R0 Testing (Weeks 2-12)

1. **Acquire test hardware** (median spec, minimum spec, high-end spec)
2. **Benchmark model performance** (LLM, image, TTS, STT)
3. **Validate performance targets** (latency, memory, storage)
4. **Document failure modes** (what breaks on minimum spec?)

### M0 Planning (Post-R0)

1. **Lock hardware requirements** (based on R0 findings)
2. **Select models** (based on benchmarks)
3. **Define CPU fallback strategy** (graceful degradation)

---

## References

- Steam Hardware Survey: https://store.steampowered.com/hwsurvey (January 2025)
- Global Plan Audit: `docs/analysis/GAP_AND_RISK_REGISTER.md` (Blocker #3: Hardware baseline not extracted)
- Inbox Document: "Chronological Design Record, Phase 10" (Hardware reality check identified)

---

**END OF DRAFT** — R0 validation required. Extract actual Steam Hardware Survey data and benchmark on real hardware before use.
