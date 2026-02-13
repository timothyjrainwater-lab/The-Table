# RQ-HW-003 Completion Notice
## Model Selection Within Budget — COMPLETE

**Research Question:** RQ-HW-003
**Owner:** Agent D (Research Orchestrator)
**Date:** 2026-02-10
**Status:** ✅ **COMPLETE**

---

## Summary

**Question:** Which models fit median/minimum hardware budgets?

**Answer:**

### Median Spec (16 GB RAM, 6-8 GB VRAM)
- **LLM:** Mistral 7B (4-bit GPTQ) or LLaMA 2 7B (4-bit) — **GO**
- **Image:** Stable Diffusion 1.5 (4-bit quantized) — **GO**
- **TTS:** Coqui TTS (VITS) or Piper TTS — **GO**
- **STT:** Whisper Base — **GO**

### Minimum Spec (8 GB RAM, CPU Fallback)
- **LLM:** Phi-2 (2.7B, 4-bit) or StableLM-3B (4-bit) — **GO**
- **Image:** Stable Diffusion 1.5 (CPU fallback, 60-120 sec/image) — **GO**
- **TTS:** Piper TTS — **GO**
- **STT:** Whisper Tiny — **GO**

---

## Evidence

**Source Document:** `docs/research/R0_MODEL_BUDGETS.md` (504 lines)

**Key Findings:**
1. Median spec supports 7B LLM + SD 1.5 image gen with safe headroom (1.5-3.0 GB RAM free)
2. Minimum spec supports <3B LLM + CPU image gen with acceptable performance degradation
3. 15% of users have NO discrete GPU → CPU fallback MANDATORY
4. All selected models fit within budget constraints (GO/NO-GO matrix verified)

**Acceptance Threshold:** ✅ **MET**
- ✅ LLM selected for median (Mistral 7B 4-bit) and minimum (Phi-2 4-bit)
- ✅ Image gen selected for median (SD 1.5 GPU) and minimum (SD 1.5 CPU)
- ✅ TTS selected (Coqui/Piper for both specs)
- ✅ STT selected (Whisper Base for median, Whisper Tiny for minimum)

---

## Unblocked Research Questions

**RQ-HW-003 completion unblocks:**

### Agent A (LLM & Memory)
- **RQ-LLM-006:** LLM Constraint Adherence (model selection required)

### Agent B (Image & Assets)
- **RQ-IMG-007:** Image Latency Median (model selection required)
- **RQ-IMG-008:** Image Latency Minimum (model selection required)

### Agent C (UX & Integration)
- **RQ-VOICE-001:** TTS Quality Baseline (model selection required)

### Agent D (Architecture)
- **RQ-HW-006:** Cloud vs Local Models (baseline models defined)
- **RQ-MVP-003:** Feature Scope Finalization (compute budget known)

**Total Unblocked:** 6+ research questions

---

## Next Actions

### For Agent A
- Begin RQ-LLM-006 (LLM constraint adherence testing with Mistral 7B 4-bit)
- Model: Mistral 7B (4-bit GPTQ), target 20-30 tokens/sec

### For Agent B
- Begin RQ-IMG-007 (image latency median spec with SD 1.5)
- Begin RQ-IMG-008 (image latency minimum spec with SD 1.5 CPU)
- Model: Stable Diffusion 1.5 (4-bit quantized)

### For Agent C
- Begin RQ-VOICE-001 (TTS quality baseline with Coqui/Piper)
- Model: Coqui TTS (VITS) or Piper TTS

### For Agent D
- Update R0_MASTER_TRACKER.md status (RQ-HW-003: COMPLETE)
- Notify all agents of unblocked work
- Monitor R0 validation benchmarks (tokens/sec, image latency, memory profiling)

---

## Confidence

**0.95** — Model budgets are evidence-based (sourced from Steam Hardware Survey), GO/NO-GO decisions justified by memory/compute constraints, all acceptance thresholds met.

**Caveat:** R0 validation required (actual hardware benchmarking) to confirm budgets are accurate. If benchmarks show significant deviation, budgets may need revision.

---

**Certification:** Agent D (Research Orchestrator) — 2026-02-10

**Status:** ✅ **RQ-HW-003 COMPLETE**
