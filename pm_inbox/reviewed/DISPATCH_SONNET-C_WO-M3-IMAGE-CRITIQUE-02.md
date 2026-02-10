# Instruction Packet: Sonnet-C

**Work Order:** WO-M3-IMAGE-CRITIQUE-02 (Image Critique Adapter Design — R1-Aligned)
**Dispatched By:** Opus (Acting PM)
**Date:** 2026-02-11
**Priority:** 2
**Deliverable Type:** Design documentation only (no code implementation)

---

## READ FIRST

1. **Your prior analysis is acknowledged.** You correctly identified that image critique infrastructure already exists (schemas, protocol, stub, factory, 36 tests). That finding was accurate and valuable.

2. **The scope has changed.** Your previous deliverables (SparkCritiqueAdapter + CLIPCritiqueAdapter) were for models that R1 has superseded. This is not your fault — the WO you received (WO-M3-IMAGE-CRITIQUE-01) predated R1. Your work was thorough but on outdated scope.

3. **R1 specifies different models.** Read `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` Section 5 (Image Critique). The three-layer pipeline is:
   - Layer 1: **HeuristicsImageCritic** (CPU-only, no ML model)
   - Layer 2: **ImageRewardCritiqueAdapter** (MIT license, ~1.0 GB FP16)
   - Layer 3: **SigLIPCritiqueAdapter** (Apache 2.0, ~0.6 GB FP16)

4. **Full work order:** `pm_inbox/WO-M3-IMAGE-CRITIQUE-02_RESCOPED.md`

---

## YOUR TASK

Design documentation for three concrete adapters that plug into the existing `ImageCritiqueAdapter` protocol.

### Deliverable 1: HeuristicsImageCritic Design Doc

Layer 1 — catch obvious failures without loading any GPU model.

- Blur detection (Laplacian variance threshold)
- Composition checks (center-of-mass, edge density, aspect ratio)
- Format validation (resolution, color space, file size)
- Transparency/corruption detection
- Scoring: binary pass/fail per check, aggregate to CritiqueResult
- OpenCV + Pillow only (no ML models, zero VRAM)
- Target: <100ms per image on CPU

**Critical:** This MUST be a standalone adapter. Do NOT fold it into ImageReward. The purpose of Layer 1 is catching obvious failures without loading a GPU model.

### Deliverable 2: ImageRewardCritiqueAdapter Design Doc

Layer 2 — text-image alignment scoring.

- Model: ImageReward (NeurIPS 2023, MIT license, ~1.0 GB FP16)
- Input: generated image + generation prompt
- Output: alignment score → CritiqueResult dimensions
- Threshold calibration strategy
- Sequential loading: loads after SDXL Lightning unloads
- Error handling: fall back to heuristics-only if model fails
- Target: <2s per image on GPU

### Deliverable 3: SigLIPCritiqueAdapter Design Doc

Layer 3 — optional reference-based comparison.

- Model: SigLIP (Apache 2.0, ~0.6 GB FP16)
- Input: generated image + reference image(s)
- Output: similarity score → CritiqueResult
- Use case: portrait consistency across sessions
- Only invoked when reference images exist
- Error handling: Layer 2 result stands if Layer 3 fails
- Target: <1s per comparison on GPU

### Deliverable 4: Prep Pipeline Integration Points

- Sequential flow: Generate → Heuristic → ImageReward → optional SigLIP
- Decision logic: which layers to invoke by hardware tier and asset type
- Regeneration policy: max attempts, parameter adjustment
- Failure handling: placeholder strategy when all attempts fail
- VRAM budget: ImageReward (~1 GB) loads after SDXL (~4 GB) unloads

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| CritiqueResult, CritiqueDimension, CritiqueRubric schemas | `aidm/schemas/image_critique.py` | Locked |
| ImageCritiqueAdapter protocol + StubImageCritic | `aidm/core/image_critique_adapter.py` | Locked |
| create_image_critic() factory | `aidm/core/image_critique_adapter.py` | Locked |
| Tests (36, all passing) | `tests/test_image_critique.py` | Locked |

Read these files to understand the protocol your adapters must conform to.

---

## WHAT IS NOT NEEDED

- Code implementation (deferred to M3 execution)
- Dependencies added to pyproject.toml (deferred)
- Changes to existing schemas, protocol, or tests
- SparkCritiqueAdapter or CLIPCritiqueAdapter designs (superseded by R1)

---

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `pm_inbox/WO-M3-IMAGE-CRITIQUE-02_RESCOPED.md` | Full work order with acceptance criteria |
| 2 | `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` Section 5 | R1 image critique findings |
| 3 | `aidm/schemas/image_critique.py` | Existing schema layer (read this) |
| 4 | `aidm/core/image_critique_adapter.py` | Existing protocol (read this) |
| 5 | `tests/test_image_critique.py` | Existing tests (read this) |

---

## DELIVERY

Place deliverables in `pm_inbox/` with naming:
- `SONNET-C_WO-M3-IMAGE-CRITIQUE-02_heuristics_design.md`
- `SONNET-C_WO-M3-IMAGE-CRITIQUE-02_imagereward_design.md`
- `SONNET-C_WO-M3-IMAGE-CRITIQUE-02_siglip_design.md`
- `SONNET-C_WO-M3-IMAGE-CRITIQUE-02_prep_integration.md`
- `SONNET-C_WO-M3-IMAGE-CRITIQUE-02_completion.md`

---

## STOP CONDITIONS

Stop and report if:
- The existing `ImageCritiqueAdapter` protocol cannot accommodate the three-layer pipeline without modification
- ImageReward or SigLIP has a licensing issue not captured in R1
- The VRAM budget doesn't work with sequential loading

---

**END OF INSTRUCTION PACKET**
