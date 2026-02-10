# Image Critique Feasibility Analysis — R0 Research Draft

**Status:** R0 / DRAFT / NON-BINDING (R1 revision appended)
**Purpose:** Evaluate technical feasibility of automated image critique approaches
**Authority:** Advisory — requires validation against actual performance
**Last Updated:** 2026-02-11
**Research Context:** Image critique viability analysis for AIDM immersion pipeline

---

## ⚠️ DRAFT NOTICE

This document is a **research draft** analyzing technical feasibility of image critique methods. It is **not binding** until:

1. Actual benchmarking validates performance estimates
2. Error rate analysis confirms acceptable false positive/negative rates
3. Hardware testing on target baseline confirms viability
4. Formal approval locks critique approach

**Do not use for implementation** until validated.

---

## Executive Summary

**Research Question:** Can we enforce automated image quality gates locally at acceptable cost?

**TL;DR Answer (Provisional):**
- ✅ **Heuristics-only:** Viable on CPU, <200ms, limited accuracy
- ⚠️ **CLIP-style similarity:** Viable on GPU (<100ms), marginal on CPU (~800ms)
- ❌ **Heavyweight local classifier:** Too slow on CPU (>2000ms), requires GPU
- ✅ **Hybrid approach:** RECOMMENDED — heuristics on CPU, upgrade to CLIP if GPU available

**Key Finding:** **Heuristics + CLIP hybrid covers 85% of users acceptably** (15% CPU-only + 70% mid-tier GPU).

**Fallback Required:** Shipped art pack for users who cannot run CLIP on CPU and have no GPU.

---

## R1 REVISION (2026-02-11)

**This document's recommendations are superseded by R1 findings.**

The R0 feasibility study was written before ImageReward (NeurIPS 2023), SigLIP (Google, 2024-2025), and QualiCLIP (CVPR 2024) became available. These models are strictly better than the CLIP ViT-B/32 recommendation in Approach 2/4.

### Updated Recommendation: Three-Layer Pipeline

**Layer 1: Fast Heuristics (CPU, <100ms, 0 VRAM)** — Same as this document's Approach 1
- Laplacian variance for blur, BRISQUE via pyiqa, saliency center-of-mass
- Catches obviously broken images before loading any models

**Layer 2: ImageReward (GPU, ~100ms, ~1.0 GB FP16)** — Replaces CLIP ViT-B/32
- NeurIPS 2023 model (THUDM). Takes BOTH image AND text prompt as input.
- Produces single score: "how well does this image match this description per human preference?"
- Beats raw CLIP similarity by ~40% on human preference alignment.
- API: `score = model.score("description", [image_path])`

**Layer 3 (Optional): SigLIP (GPU, ~100ms, ~0.6 GB FP16)** — Replaces CLIP for reference comparison
- Google's successor to CLIP. Better calibration, smaller, outperforms same-size CLIP.
- SigLIP ViT-L/16-256 at ~600 MB FP16.
- Use for reference-based comparison: style consistency, NPC identity matching.

### Updated Performance Estimates

| Approach | F1 Score | FPR | FNR | VRAM |
|----------|----------|-----|-----|------|
| Heuristics-only (unchanged) | 0.60-0.65 | 15-20% | 25-40% | 0 GB |
| **Heuristics + ImageReward** | **0.80-0.85** | **5-8%** | **8-12%** | **~1.0 GB** |
| **Heuristics + ImageReward + SigLIP** | **0.85-0.90** | **5-8%** | **5-10%** | **~1.6 GB** |
| Old: Heuristics + CLIP B/32 | 0.75-0.80 | 8-10% | 12-15% | ~1.5 GB |

### VRAM Budget (Sequential Pipeline)

Since AIDM uses prep-time sequential model loading:
1. SDXL Lightning NF4 generates image (~4 GB VRAM). Unloads.
2. ImageReward loads (~1.0 GB). Scores. Unloads.
3. SigLIP loads (~0.6 GB). Compares. Unloads.

Peak VRAM during critique: ~1.0-1.6 GB. No contention with image generation.

### Status Update

- R0-DEC-016 (Image Critique PAUSE): Now **ANSWERABLE** — model selection resolved
- R0-DEC-034 (GO Criterion 4): Now **ANSWERABLE** — requires benchmarking to confirm
- R0-DEC-037 (NO-GO Trigger 1): **NOT TRIGGERED** — viable critique path exists

**Full details:** `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md`

---

## Evaluation Criteria

**Performance:**
- **Latency:** Time to critique one image on target hardware
- **Throughput:** Images per second (for batch critique during prep)
- **Memory:** RAM/VRAM usage during critique

**Accuracy:**
- **False Positive Rate (FPR):** % of good images rejected
- **False Negative Rate (FNR):** % of bad images accepted
- **F1 Score:** Harmonic mean of precision and recall

**Deployability:**
- **Model size:** Disk space for weights
- **Dependencies:** Libraries required (ONNX, PyTorch, TensorFlow)
- **CPU fallback:** Can it run without GPU?

---

## Approach 1: Heuristics-Only (Baseline)

### Description

**No ML models.** Pure image processing using OpenCV/PIL:
- **Readability:** Laplacian variance (blur), Sobel edges (detail)
- **Composition:** Saliency map, bounding box, center-of-mass
- **Artifacting:** Edge detection for seams, color histogram for artifacts
- **Style:** Color palette histogram comparison
- **Identity:** Color histogram distance (weak proxy)

### Performance Estimates

**Target Hardware:** 6-8 core CPU @ 3.0-3.5 GHz, 16 GB RAM

**Latency (per image):**
- Blur detection (Laplacian): ~10ms
- Edge detection (Sobel): ~15ms
- Saliency map: ~30ms
- Bounding box extraction: ~20ms
- Color histogram: ~10ms
- **Total: ~85ms per image (CPU-only)**

**Throughput:** ~12 images/second (single-threaded), ~60 images/second (8 cores)

**Memory:** <100 MB RAM (no model weights)

### Accuracy Estimates (Speculative)

**Based on literature + domain knowledge:**
- **Blur detection:** FPR ~5%, FNR ~10% (decent for obvious blur)
- **Composition:** FPR ~10%, FNR ~15% (bounding box heuristics are noisy)
- **Artifacting:** FPR ~20%, FNR ~30% (weak: cannot detect hands/eyes)
- **Style adherence:** FPR ~25%, FNR ~40% (color histogram is very weak proxy)
- **Identity match:** FPR ~30%, FNR ~50% (color histogram insufficient for identity)

**Overall F1 Score (estimated):** ~0.60-0.65 (mediocre)

**Key Weakness:** Cannot detect hands, eyes, anatomical errors, or identity drift reliably.

### Deployability

- ✅ **Model size:** 0 MB (no weights)
- ✅ **Dependencies:** OpenCV, NumPy, PIL (all lightweight, CPU-native)
- ✅ **CPU fallback:** Fully CPU-native, no GPU required
- ✅ **Disk space:** <10 MB for libraries

**Verdict:** **Viable as baseline, but accuracy too low for unsupervised use.**

---

## Approach 2: CLIP-Style Similarity Scoring

### Description

**Use CLIP embeddings for style/identity checks:**
- **Readability/Composition/Artifacting:** Heuristics (as in Approach 1)
- **Style adherence:** CLIP embedding distance to reference style images
- **Identity match:** CLIP embedding distance to NPC anchor image

**CLIP Variant:** OpenCLIP ViT-B/32 (most popular, well-supported)

**Workflow:**
1. Load CLIP model (once at startup)
2. Encode reference images to embeddings (once per campaign)
3. For each generated image:
   - Encode to CLIP embedding
   - Compute cosine similarity to reference(s)
   - Accept if similarity > threshold (e.g., 0.70 for style, 0.60 for identity)

### Performance Estimates

**Target Hardware:** GTX 1660 Ti (6 GB VRAM) OR 6-8 core CPU @ 3.0 GHz

**Model Size:** ~350 MB (ViT-B/32 weights)

**Latency (per image):**

**GPU (GTX 1660 Ti):**
- CLIP encoding: ~40ms
- Cosine similarity: ~1ms
- Heuristics: ~85ms
- **Total: ~125ms per image (GPU)**

**CPU (6-8 cores):**
- CLIP encoding: ~600-800ms (CPU inference is slow for ViT)
- Cosine similarity: ~1ms
- Heuristics: ~85ms
- **Total: ~700-900ms per image (CPU)**

**Throughput:**
- GPU: ~8 images/second
- CPU: ~1.2 images/second

**Memory:**
- GPU: ~1.5 GB VRAM (model + batch)
- CPU: ~2 GB RAM (model + working memory)

### Accuracy Estimates (Based on CLIP Literature)

**CLIP for style/identity:**
- **Style adherence:** FPR ~8%, FNR ~12% (CLIP excels at style similarity)
- **Identity match:** FPR ~10%, FNR ~15% (CLIP good for visual similarity, not identity)
- **Readability/Composition/Artifacting:** Same as heuristics (FPR ~5-20%, FNR ~10-30%)

**Overall F1 Score (estimated):** ~0.75-0.80 (good)

**Key Strength:** Excellent at style consistency, decent at identity.
**Key Weakness:** Still cannot detect hands, eyes, anatomical errors reliably. CPU inference slow.

### Deployability

- ⚠️ **Model size:** ~350 MB (moderate disk/RAM footprint)
- ⚠️ **Dependencies:** PyTorch or ONNX Runtime (heavier than OpenCV)
- ⚠️ **CPU fallback:** Viable but slow (~700-900ms per image)
- ⚠️ **GPU requirement:** Strongly recommended for acceptable latency (<200ms)

**Verdict:** **Viable on GPU, marginal on CPU. Hybrid approach recommended.**

---

## Approach 3: Lightweight Local Classifier (Custom CNN)

### Description

**Train a custom lightweight CNN for artifact detection:**
- Input: 256×256 image
- Output: Binary classification (pass/fail) OR multi-class (blur/hands/eyes/style/composition)
- Architecture: MobileNetV2 or EfficientNet-Lite (optimized for CPU/mobile)

**Training Data Required:**
- 10,000-50,000 labeled images (good/bad examples)
- Balanced classes (50/50 pass/fail)
- Diverse artifacts (hands, eyes, blur, composition, style)

**Workflow:**
1. Train classifier on labeled dataset
2. Export to ONNX or TensorFlow Lite
3. Run inference on generated images
4. Accept if classifier confidence > threshold (e.g., 0.80 for "pass")

### Performance Estimates

**Target Hardware:** GTX 1660 Ti OR 6-8 core CPU

**Model Size:** ~10-30 MB (MobileNetV2) or ~50-100 MB (EfficientNet-Lite)

**Latency (per image):**

**GPU (GTX 1660 Ti):**
- CNN inference: ~20-40ms (MobileNetV2) or ~40-80ms (EfficientNet)
- **Total: ~30-80ms per image (GPU)**

**CPU (6-8 cores):**
- CNN inference: ~150-300ms (MobileNetV2) or ~300-600ms (EfficientNet)
- **Total: ~200-600ms per image (CPU)**

**Throughput:**
- GPU: ~12-30 images/second
- CPU: ~2-5 images/second

**Memory:**
- GPU: ~500 MB VRAM
- CPU: ~1 GB RAM

### Accuracy Estimates (Speculative)

**Dependent on training data quality:**
- **If well-trained:** FPR ~5%, FNR ~8% (better than heuristics, similar to CLIP)
- **If poorly-trained:** FPR ~15%, FNR ~20% (worse than CLIP)

**Overall F1 Score (estimated):** ~0.80-0.85 (excellent if well-trained)

**Key Strength:** Fast on GPU, can learn to detect hands/eyes/anatomy if trained on diverse dataset.
**Key Weakness:** Requires labeled training data (10k+ images), CPU inference still slow, model may overfit to training distribution.

### Deployability

- ✅ **Model size:** ~10-100 MB (small to moderate)
- ⚠️ **Dependencies:** ONNX Runtime or TensorFlow Lite (moderate weight)
- ⚠️ **CPU fallback:** Viable but slow (~200-600ms per image)
- ❌ **Training data:** Requires 10k+ labeled images (blocking if unavailable)

**Verdict:** **Viable if training data available, but slower on CPU than heuristics. Not recommended for R0 (no training data yet).**

---

## Approach 4: Hybrid (Heuristics + CLIP on GPU, Heuristics-Only on CPU)

### Description

**Adaptive critique based on hardware:**
- **CPU-only users (15%):** Heuristics-only (~85ms per image)
- **GPU users (85%):** Heuristics + CLIP (~125ms per image)

**Workflow:**
1. Detect GPU availability at startup
2. If GPU: Load CLIP model, use heuristics + CLIP
3. If CPU-only: Use heuristics-only, skip CLIP
4. Fallback: If heuristics-only rejects too many images (>40% rejection rate), offer shipped art pack

**Rationale:**
- Most users (85%) have GPU → can use CLIP for better accuracy
- CPU-only users (15%) get fast heuristics, accept lower accuracy
- Shipped art pack covers worst-case scenario (no GPU + bad generation)

### Performance Estimates

**GPU Users (85%):**
- Latency: ~125ms per image (heuristics + CLIP)
- Throughput: ~8 images/second
- Memory: ~1.5 GB VRAM

**CPU-Only Users (15%):**
- Latency: ~85ms per image (heuristics-only)
- Throughput: ~12 images/second
- Memory: <100 MB RAM

### Accuracy Estimates

**GPU Users:**
- F1 Score: ~0.75-0.80 (CLIP + heuristics)

**CPU-Only Users:**
- F1 Score: ~0.60-0.65 (heuristics-only, weaker but acceptable with fallback)

### Deployability

- ✅ **Model size:** 0 MB (CPU) or ~350 MB (GPU)
- ✅ **Dependencies:** OpenCV (CPU) + PyTorch/ONNX (GPU, optional)
- ✅ **CPU fallback:** Fully viable (heuristics-only)
- ✅ **Disk space:** <400 MB total (CLIP weights on GPU systems only)

**Verdict:** **RECOMMENDED. Covers 100% of users, optimizes for hardware available, provides fallback.**

---

## Error Rate Analysis

### False Positive Rate (Reject Good Images)

**Impact:** User must regenerate unnecessarily, wastes time/compute.

**Acceptable Threshold:** <10% FPR (reject <10% of good images)

**Estimated FPR by Approach:**
- Heuristics-only: ~15-20% FPR (ABOVE THRESHOLD — too many false rejects)
- CLIP + heuristics: ~8-10% FPR (ACCEPTABLE)
- Local classifier: ~5-8% FPR (EXCELLENT, if well-trained)
- Hybrid: ~8-10% FPR (GPU users), ~15-20% FPR (CPU-only users)

**Mitigation for High FPR:**
- Bounded regeneration (max 3 attempts before fallback)
- User override ("accept anyway" button)
- Shipped art pack fallback

### False Negative Rate (Accept Bad Images)

**Impact:** User sees low-quality image, must manually reject, poor UX.

**Acceptable Threshold:** <15% FNR (accept <15% of bad images)

**Estimated FNR by Approach:**
- Heuristics-only: ~25-40% FNR (ABOVE THRESHOLD — too many bad images slip through)
- CLIP + heuristics: ~12-15% FNR (ACCEPTABLE)
- Local classifier: ~8-12% FNR (EXCELLENT, if well-trained)
- Hybrid: ~12-15% FNR (GPU users), ~25-40% FNR (CPU-only users)

**Mitigation for High FNR:**
- Manual user rejection option
- Iterative critique (Phase 1 → Phase 2 → Phase 3, fail early)
- Style reference calibration (improve CLIP thresholds)

### F1 Score Summary

| Approach | F1 Score | FPR | FNR | Verdict |
|----------|----------|-----|-----|---------|
| Heuristics-only | 0.60-0.65 | 15-20% | 25-40% | ACCEPTABLE with fallback |
| CLIP + heuristics | 0.75-0.80 | 8-10% | 12-15% | GOOD |
| Local classifier | 0.80-0.85 | 5-8% | 8-12% | EXCELLENT (if trained) |
| **Hybrid** | **0.75-0.80** (GPU) / **0.60-0.65** (CPU) | **8-10%** / **15-20%** | **12-15%** / **25-40%** | **RECOMMENDED** |

---

## Cost Analysis

### Latency Budget

**Target:** <500ms total latency per image (prep-time generation, not real-time)

**Breakdown:**
- Image generation: ~2000-5000ms (Stable Diffusion on GPU) or ~30-60 seconds (CPU)
- Critique: ~125ms (GPU hybrid) or ~85ms (CPU heuristics)
- **Total: ~2125-5125ms (GPU) or ~30-60 seconds (CPU)**

**Verdict:** Critique adds <10% overhead on GPU, <1% overhead on CPU. **Acceptable.**

### Memory Budget

**Target:** <4 GB total memory footprint (generation + critique)

**Breakdown:**
- Image generation: ~2-3 GB VRAM (Stable Diffusion) or ~4-6 GB RAM (CPU)
- Critique: ~1.5 GB VRAM (CLIP on GPU) or ~100 MB RAM (heuristics on CPU)
- **Total: ~3.5-4.5 GB VRAM (GPU) or ~4-6 GB RAM (CPU)**

**Verdict:** Within budget on GPU, marginal on CPU (may require system swap). **Acceptable with warnings.**

### Disk Space Budget

**Target:** <2 GB total disk space (model weights)

**Breakdown:**
- Image generation: ~4 GB (Stable Diffusion weights)
- Critique: ~350 MB (CLIP weights) or 0 MB (heuristics)
- **Total: ~4.35 GB (GPU) or ~4 GB (CPU)**

**Verdict:** Within budget. **Acceptable.**

---

## Hardware-Specific Recommendations

### CPU-Only Users (15% of baseline)

**Recommended Approach:** Heuristics-only
- Latency: ~85ms per image
- F1 Score: ~0.60-0.65
- Memory: <100 MB RAM
- Fallback: Shipped art pack if rejection rate >40%

**Trade-off:** Lower accuracy, but fast and no dependencies.

### Mid-Tier GPU Users (40% of baseline, e.g., GTX 1660 Ti)

**Recommended Approach:** Hybrid (Heuristics + CLIP)
- Latency: ~125ms per image
- F1 Score: ~0.75-0.80
- Memory: ~1.5 GB VRAM
- Fallback: Degrade to heuristics-only if VRAM exhausted

**Trade-off:** Good accuracy, moderate VRAM usage.

### High-End GPU Users (30% of baseline, e.g., RTX 3070)

**Recommended Approach:** Hybrid (Heuristics + CLIP) OR Local Classifier (if trained)
- Latency: ~80-125ms per image (CLIP) or ~30-80ms (classifier)
- F1 Score: ~0.75-0.85
- Memory: ~1.5 GB VRAM
- Fallback: None needed (hardware sufficient for all approaches)

**Trade-off:** Best accuracy, fastest latency.

---

## Recommended Approach: Hybrid (Heuristics + CLIP on GPU)

### Rationale

1. **Coverage:** Works for 100% of users (CPU fallback via heuristics)
2. **Accuracy:** Good F1 score (~0.75-0.80) for GPU users (85% of baseline)
3. **Latency:** <200ms on GPU, <100ms on CPU
4. **Deployability:** Optional CLIP dependency (GPU-only), core heuristics always available
5. **Cost:** <400 MB disk, <2 GB VRAM/RAM

### Implementation Strategy

**Phase 1: Ship Heuristics-Only (M0)**
- Implement blur, composition, color histogram checks
- No CLIP dependency, works on all hardware
- Acceptance threshold: F1 ~0.60-0.65
- Fallback: Shipped art pack

**Phase 2: Add CLIP for GPU Users (M1)**
- Detect GPU at startup
- Load CLIP if GPU available
- Use CLIP for style/identity, heuristics for readability/composition/artifacts
- Acceptance threshold: F1 ~0.75-0.80 (GPU), ~0.60-0.65 (CPU)

**Phase 3: Optional Local Classifier (M2+, if training data available)**
- Train on labeled dataset (10k+ images)
- Replace CLIP with custom classifier for artifact detection
- Acceptance threshold: F1 ~0.80-0.85

---

## Open Questions (Require Empirical Validation)

1. **CLIP threshold calibration:** What cosine similarity thresholds give FPR <10%, FNR <15%?
2. **Heuristic threshold calibration:** What Laplacian variance / edge density thresholds work best?
3. **Shipped art pack quality:** How good does shipped art need to be to serve as acceptable fallback?
4. **User override frequency:** How often will users click "accept anyway" to bypass critique?
5. **Training data availability:** Can we collect 10k+ labeled images for local classifier?
6. **CLIP on CPU viability:** Is ~700-900ms per image acceptable for CPU-only users during prep?

---

## Next Steps

1. **Benchmark CLIP on target hardware:** Measure actual latency on GTX 1660 Ti and 6-core CPU
2. **Calibrate thresholds:** Empirically determine FPR/FNR for CLIP and heuristics on sample dataset
3. **Define bounded regen policy:** Max attempts, backoff, fallback (R0_BOUNDED_REGEN_POLICY.md)
4. **Prototype heuristics:** Implement Phase 1 (heuristics-only) and measure accuracy
5. **User testing:** Validate FPR/FNR acceptability with sample users

---

## Decision: Can We Enforce Critique Locally?

**YES, with caveats:**

✅ **Heuristics-only viable for all users** (CPU fallback, F1 ~0.60-0.65)
✅ **CLIP + heuristics viable for GPU users** (85% of baseline, F1 ~0.75-0.80)
✅ **Hybrid approach recommended** (adaptive based on hardware)
✅ **Fallback required:** Shipped art pack for CPU-only users with high rejection rate

**Shippable Alternative (If Critique Fails):**
- Shipped art pack (pre-vetted portraits/tokens/scenes)
- User manual accept (override critique)
- Alternate generation settings (lower creativity, higher guidance)

**Blocking Issues:** None (hybrid approach covers all users acceptably)

---

## References

- **CLIP (OpenAI):** https://github.com/openai/CLIP
- **OpenCLIP:** https://github.com/mlfoundations/open_clip
- **MobileNetV2:** Sandler et al., "MobileNetV2: Inverted Residuals and Linear Bottlenecks"
- **EfficientNet:** Tan & Le, "EfficientNet: Rethinking Model Scaling for CNNs"
- **Laplacian Variance:** Pech-Pacheco et al., "Diatom autofocusing in brightfield microscopy"
- **Steam Hardware Survey:** https://store.steampowered.com/hwsurvey

---

## Document Governance

**Status:** R0 / DRAFT
**Approval Required From:** Project owner (human)
**Depends On:** R0_IMAGE_CRITIQUE_RUBRIC.md, HARDWARE_BASELINE_REPORT.md
**Unblocks:** R0_BOUNDED_REGEN_POLICY.md
**Future Work:** Empirical benchmarking, threshold calibration, user testing
