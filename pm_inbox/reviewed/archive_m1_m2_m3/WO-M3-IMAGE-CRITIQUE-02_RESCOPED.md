# Work Order: M3 Image Critique Adapter Design (R1-Aligned)

**Work Order ID:** WO-M3-IMAGE-CRITIQUE-02
**Supersedes:** WO-M3-IMAGE-CRITIQUE-01 (outdated model selections)
**Assigned To:** Sonnet-C (preferred — delivered existing infrastructure analysis)
**Milestone:** M3 (Immersion Layer v1)
**Priority:** 3 (after audio pipeline evaluation)
**Status:** READY FOR DISPATCH
**Created:** 2026-02-11
**Issued By:** Opus (Acting PM)

---

## Strategic Context

R1 Technology Stack Validation (pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md) established a **three-layer graduated image critique pipeline**:

| Layer | Adapter | Purpose | VRAM | License | Cost |
|-------|---------|---------|------|---------|------|
| 1 | **HeuristicsImageCritic** | Blur/composition/format checks | 0 (CPU) | N/A | $0 |
| 2 | **ImageRewardCritiqueAdapter** | Text-image alignment scoring | ~1.0 GB | MIT | $0 |
| 3 | **SigLIPCritiqueAdapter** | Reference-based comparison | ~0.6 GB | Apache 2.0 | $0 |

This replaces the outdated WO-M3-IMAGE-CRITIQUE-01 scope which specified "Spark vision + CLIP" — both were evaluated and rejected by R1:
- **Spark vision (LLM-based):** Too large, too slow, unreliable for structured pass/fail scoring, costs money per image
- **CLIP B/32:** Superseded by ImageReward which beats CLIP by 40% on human preference alignment (NeurIPS 2023)

---

## What Already Exists (DO NOT RECREATE)

Sonnet-C's analysis confirmed complete infrastructure:

| Component | Location | Lines | Status |
|-----------|----------|-------|--------|
| CritiqueResult, CritiqueDimension, CritiqueRubric schemas | `aidm/schemas/image_critique.py` | 337 | Complete |
| ImageCritiqueAdapter protocol + StubImageCritic | `aidm/core/image_critique_adapter.py` | 226 | Complete |
| create_image_critic() factory | `aidm/core/image_critique_adapter.py` | — | Complete |
| Comprehensive tests | `tests/test_image_critique.py` | 619 | 36 tests, all passing |

**The protocol, schemas, factory, and stub are locked. Do NOT modify them.**

---

## Objective

Design documentation for three concrete adapters that plug into the existing `ImageCritiqueAdapter` protocol, forming a graduated pipeline where each layer catches progressively subtler issues.

---

## Scope

### Deliverable 1: HeuristicsImageCritic Design Doc

**Purpose:** Layer 1 — catch obvious failures without loading any GPU model.

**Design must cover:**
- Blur detection (Laplacian variance threshold)
- Composition checks (center-of-mass, edge density, aspect ratio)
- Format validation (resolution, color space, file size)
- Transparency/corruption detection
- Scoring: binary pass/fail per check, aggregate to CritiqueResult
- Implementation: OpenCV + Pillow only (no ML models, no VRAM)
- Performance target: <100ms per image on CPU

**Key constraint:** This MUST be a standalone adapter, NOT folded into ImageReward. The entire purpose of Layer 1 is catching obvious failures (blurry, wrong resolution, corrupted) without loading a GPU model. If heuristics pass, then and only then does ImageReward load.

### Deliverable 2: ImageRewardCritiqueAdapter Design Doc

**Purpose:** Layer 2 — text-image alignment scoring using the ImageReward model.

**Design must cover:**
- Model: ImageReward (NeurIPS 2023, MIT license, ~1.0 GB FP16)
- Input: generated image + generation prompt (text-image pair)
- Output: alignment score mapped to CritiqueResult dimensions
- Threshold calibration strategy (pass/fail boundary)
- Sequential loading: loads after SDXL Lightning unloads in prep pipeline
- Unloads after scoring phase completes
- Error handling: if model fails to load, fall back to heuristics-only (Layer 1)
- Performance target: <2s per image on GPU

**Key reference:** ImageReward outperforms CLIP by 40% on human preference alignment. It scores how well an image matches its generation prompt — exactly what we need for critique.

### Deliverable 3: SigLIPCritiqueAdapter Design Doc

**Purpose:** Layer 3 — optional reference-based comparison (e.g., NPC portrait consistency across sessions).

**Design must cover:**
- Model: SigLIP (Apache 2.0, ~0.6 GB FP16)
- Input: generated image + reference image(s)
- Output: similarity score mapped to CritiqueResult
- Use case: ensuring regenerated portraits maintain identity consistency
- When to invoke: only when reference images exist (not for first-generation)
- Sequential loading: loads after ImageReward if needed, or skipped
- Error handling: if model fails, Layer 2 result stands (Layer 3 is enhancement)
- Performance target: <1s per comparison on GPU

### Deliverable 4: Prep Pipeline Integration Points

**Design must cover:**
- Sequential flow: Generate → Heuristic check → ImageReward score → optional SigLIP comparison
- Decision logic: which layers to invoke based on hardware tier and asset type
- Regeneration policy: max attempts, parameter adjustment between attempts
- Failure handling: what happens when all attempts fail (placeholder strategy)
- VRAM budget: ImageReward (~1 GB) loads after SDXL Lightning (~4 GB) unloads — no contention

---

## Out of Scope

- **Code implementation** — deferred to M3 execution phase
- **Dependencies added to pyproject.toml** — deferred (image-reward, open-clip-torch, etc.)
- **Changes to existing schemas, protocol, or tests** — infrastructure is locked
- **SparkCritiqueAdapter or CLIPCritiqueAdapter** — these are R0 designs, superseded by R1
- **Sonnet-C's existing design docs for Spark/CLIP** — acknowledged as thorough work on the old scope, but the scope has changed

---

## Acceptance Criteria

- [ ] HeuristicsImageCritic design complete (CPU-only, no ML models, standalone adapter)
- [ ] ImageRewardCritiqueAdapter design complete (MIT license verified, ~1.0 GB, text-image alignment)
- [ ] SigLIPCritiqueAdapter design complete (Apache 2.0, ~0.6 GB, reference comparison)
- [ ] Prep pipeline integration points documented (sequential flow, decision logic, regeneration policy)
- [ ] All three adapters conform to existing `ImageCritiqueAdapter` protocol
- [ ] VRAM budget validated (peak ~1.0 GB for critique phase, sequential with image generation)
- [ ] No modifications proposed to existing schemas, protocol, or tests

---

## Dependencies

**Requires:**
- R1 Technology Stack Validation Report (complete)
- Existing image critique infrastructure (complete, 36 tests passing)

**Blocks:**
- M3 image critique implementation (future WO)

**Parallel to:**
- WO-M3-AUDIO-EVAL-01 (audio pipeline evaluation)

---

## Notes

### Why Not Spark Vision

R1 evaluated routing critique through the LLM (vision-capable models like Moondream 2B) and rejected it:
- **Too large:** Even small vision LLMs are 2+ GB — larger than dedicated critique models
- **Too slow:** LLM inference is 5-10x slower than a dedicated scoring model
- **Unreliable for structured scoring:** LLMs produce variable free-text, not reliable numerical scores
- **Costs money:** Cloud vision APIs charge per image; ImageReward/SigLIP are free local models

### Why Not CLIP B/32

ImageReward (NeurIPS 2023) was specifically designed to evaluate text-image alignment and outperforms CLIP by 40% on human preference benchmarks. CLIP was designed for text-image retrieval, not quality assessment — it's the wrong tool.

### Why Heuristics Must Be Separate

If heuristics are folded into ImageReward, you lose the key benefit: catching obvious failures (blurry, wrong resolution, corrupted file) without loading a 1 GB GPU model. A blurry image should be caught in <100ms on CPU, not after spending 2s loading and running ImageReward.

---

**END OF WORK ORDER**
