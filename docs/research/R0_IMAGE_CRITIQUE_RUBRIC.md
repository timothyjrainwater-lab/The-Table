# Image Critique Rubric — R0 Research Draft

**Status:** R0 / DRAFT / NON-BINDING
**Purpose:** Define quality dimensions for automated image critique gate
**Authority:** Advisory — requires validation against actual performance
**Last Updated:** 2026-02-10
**Research Context:** Image critique viability analysis for AIDM immersion pipeline

---

## ⚠️ DRAFT NOTICE

This document is a **research draft** defining quality criteria for automated image validation. It is **not binding** until:

1. R0 research validates feasibility of automated critique
2. Error rate analysis confirms acceptable false positive/negative rates
3. Bounded regeneration policy approved
4. Formal approval locks critique rubric

**Do not use for implementation** until validated.

---

## Purpose

**Identified Gap:** AIDM immersion pipeline generates images (portraits, tokens, scenes) but has no automated quality gate before presenting to user.

**Without automated critique:**
- Low-quality images reach user interface (poor UX)
- No feedback signal to improve generation parameters
- Manual user rejection required for every bad image
- No way to enforce style consistency across campaign

**With automated critique:**
- Reject obviously broken images before user sees them
- Bounded regeneration attempts with parameter adjustment
- Style/identity consistency enforcement
- Fallback to shipped art pack if generation fails

---

## Quality Dimensions

### 1. **Readability at UI Size**

**Definition:** Can essential details be distinguished when image is rendered at target UI dimensions?

**Target UI Sizes:**
- **Portrait (NPC/PC):** 256×256px minimum, 512×512px typical
- **Token (battle map):** 128×128px minimum, 256×256px typical
- **Scene card:** 512×512px minimum, 1024×512px typical

**Pass Criteria:**
- Face visible and distinguishable (portraits)
- Key features identifiable at target size (armor, weapons, species)
- No excessive blur or noise that destroys detail at target resolution
- Text overlays (if any) remain legible

**Fail Criteria:**
- Face unrecognizable or obscured (portraits)
- Details lost in blur/noise at target size
- Critical features invisible (e.g., dwarf beard, elf ears)
- Excessive compression artifacts

**Measurement Approaches:**
- **Heuristic:** Downscale to target size, measure edge density (Sobel/Canny)
- **Blur detection:** Variance of Laplacian (low variance = blurry)
- **Compression artifact detection:** Block-edge detection in 8×8 regions
- **Face detection:** Haar cascade / lightweight face detector (portraits only)

**Threshold Examples (to be calibrated):**
- Laplacian variance < 50 → likely too blurry (portrait)
- Edge density < 0.05 → lacking detail (token)
- Face detection confidence < 0.6 → face obscured (portrait)

---

### 2. **Centering & Composition**

**Definition:** Is the subject properly framed within the canvas?

**Pass Criteria:**
- Subject occupies 40-70% of canvas (not too small, not cropped)
- Subject centered or following rule-of-thirds
- Headroom appropriate (portraits: eyes at upper 1/3, tokens: subject centered)
- No critical features clipped at edges (e.g., half a face missing)

**Fail Criteria:**
- Subject too small (<30% of canvas) or too large (>80%)
- Subject off-center with no compositional justification
- Critical clipping (face cut off, weapon half-visible)
- Excessive empty space (>50% of canvas is background)

**Measurement Approaches:**
- **Heuristic:** Saliency map (where is visual attention?)
- **Object detection:** Bounding box of primary subject
- **Center-of-mass:** Weighted pixel distribution
- **Edge clipping:** Subject bounding box intersects canvas edges

**Threshold Examples (to be calibrated):**
- Subject bounding box < 30% of canvas → too small
- Subject bounding box > 80% of canvas → too large
- Center-of-mass > 0.3 units from canvas center → off-center
- Bounding box touches edge AND is clipped → critical clipping

---

### 3. **Artifacting**

**Definition:** Are there obvious AI generation artifacts or visual corruption?

**Common Artifacts:**
- **Hands:** Extra/missing fingers, malformed fingers, incorrect joints
- **Eyes:** Asymmetric, wall-eyed, missing pupils, different colors
- **Text:** Gibberish text in background, malformed runes/sigils
- **Anatomy:** Impossible proportions, extra/missing limbs
- **Background:** Repeating patterns, obvious seams, grid artifacts
- **Style breaks:** Inconsistent rendering (photorealistic face + cartoon body)

**Pass Criteria:**
- Hands (if visible) have 5 fingers each, plausible joints
- Eyes (if visible) are symmetric, correctly aligned, same color
- No gibberish text visible
- Anatomy follows human/creature norms (no extra limbs)
- Background coherent (no obvious seams/repeats)

**Fail Criteria:**
- Hands with 6+ or 3- fingers (CRITICAL: automatic reject)
- Eyes asymmetric or wall-eyed (CRITICAL for portraits)
- Visible gibberish text in foreground/midground
- Extra limbs, missing limbs, impossible anatomy
- Obvious grid artifacts or seams

**Measurement Approaches:**
- **Hand detection:** Lightweight hand keypoint detector (MediaPipe Hands)
- **Eye symmetry:** Face landmark detection, measure eye alignment
- **Text detection:** OCR confidence score (low = gibberish)
- **Anatomy heuristic:** Limb count, proportions (head-to-body ratio)
- **Seam detection:** Edge analysis for repeating patterns

**Threshold Examples (to be calibrated):**
- Hand keypoints detected AND finger count ≠ 5 → reject
- Eye asymmetry > 10° rotation → reject (portraits)
- OCR detects text with confidence < 0.3 → likely gibberish
- Head-to-body ratio < 1:4 or > 1:10 → anatomical distortion

---

### 4. **Style Adherence**

**Definition:** Does the image match the target art style for the campaign?

**AIDM Art Styles (to be defined in style guide):**
- **Fantasy Realism:** Detailed, painterly, D&D PHB/MM aesthetic
- **Dark Fantasy:** Grim, muted colors, high contrast
- **Heroic Fantasy:** Bright, saturated, dynamic poses
- **Sketch/Ink:** Line art, minimal color, hand-drawn feel

**Pass Criteria:**
- Color palette matches style (e.g., muted for dark fantasy, saturated for heroic)
- Rendering technique consistent with style (photorealistic vs painterly vs sketchy)
- Lighting consistent with style (dramatic chiaroscuro vs even lighting)
- No style contamination (e.g., anime eyes in fantasy realism portrait)

**Fail Criteria:**
- Color palette violates style (neon colors in dark fantasy)
- Rendering technique breaks style (photograph in painterly campaign)
- Style contamination (anime, cartoon, modern photography in medieval fantasy)

**Measurement Approaches:**
- **Color histogram:** Compare to reference style palette
- **CLIP embedding:** Measure similarity to style reference images
- **Texture analysis:** Edge sharpness (photorealistic vs painterly)
- **Style classifier:** Lightweight CNN trained on style categories

**Threshold Examples (to be calibrated):**
- CLIP similarity to style reference < 0.7 → style mismatch
- Color histogram distance > 0.4 → palette violation
- Edge sharpness inconsistent with style → rendering mismatch

---

### 5. **Identity Match & Continuity (NPC Anchor)**

**Definition:** For recurring NPCs, does the image maintain visual consistency with previous depictions?

**Context:** Each NPC has an "identity anchor" (first approved portrait). Subsequent images must maintain:
- Same species/race (elf stays elf, dwarf stays dwarf)
- Same approximate age/gender presentation
- Same distinctive features (scars, tattoos, hair color/style)
- Same general clothing style (if specified in NPC card)

**Pass Criteria:**
- Species matches anchor (CRITICAL)
- Age/gender matches anchor (within reasonable variance)
- Distinctive features present (if defined in anchor)
- Clothing style consistent (if specified)

**Fail Criteria:**
- Species change (elf → human, dwarf → halfling)
- Drastic age change (young → elderly, child → adult)
- Missing distinctive features (scar disappears, eye color changes)
- Clothing style violates character definition

**Measurement Approaches:**
- **CLIP embedding similarity:** Measure cosine distance to anchor embedding
- **Face recognition:** FaceNet/ArcFace embedding distance (for humanoids)
- **Color histogram comparison:** Clothing/hair color consistency
- **Feature matching:** Keypoint detection for distinctive marks

**Threshold Examples (to be calibrated):**
- CLIP embedding distance > 0.5 → identity drift
- Face embedding distance > 0.6 → different person (humanoids)
- Hair color histogram distance > 0.3 → hair color changed

**Special Case: First Image (No Anchor)**
- Skip identity match checks
- Store approved image as anchor embedding
- Use anchor for all subsequent continuity checks

---

## Critique Severity Levels

**CRITICAL (Automatic Reject):**
- Face unrecognizable in portrait (readability)
- Hands with wrong finger count (artifacting)
- Species mismatch for NPC with anchor (identity)
- Excessive clipping of subject (composition)

**MAJOR (Reject with High Confidence):**
- Subject too small/large (composition)
- Eye asymmetry in portrait (artifacting)
- Style contamination (style adherence)
- Visible gibberish text (artifacting)

**MINOR (Reject with Low Confidence):**
- Slight off-centering (composition)
- Minor blur at target size (readability)
- Color palette drift (style adherence)

**ACCEPTABLE (Pass):**
- All critical/major checks pass
- Minor issues acceptable if within threshold

---

## Rubric Application Strategy

### Phase 1: Critical Checks Only (Fast Path)
Run lightweight heuristics first:
1. Face detection (portraits only) — if fail, reject immediately
2. Subject bounding box (all images) — if too small/large, reject immediately
3. Blur detection (Laplacian variance) — if too blurry, reject immediately

**Goal:** Reject obviously broken images in <100ms on CPU

### Phase 2: Moderate Checks (If Phase 1 Passes)
Run heavier checks:
1. Hand detection + finger count (if hands visible)
2. Eye symmetry (if face detected)
3. Style adherence (CLIP embedding or color histogram)

**Goal:** Reject major artifacts in <500ms on CPU or <100ms on GPU

### Phase 3: Fine-Grained Checks (If Phase 2 Passes)
Run expensive checks:
1. Identity match (CLIP/FaceNet embedding distance to anchor)
2. Anatomy verification (limb count, proportions)
3. Background seam detection

**Goal:** Reject minor issues in <1000ms on CPU or <200ms on GPU

**Exit Strategy:** Pass image if all phases pass, reject at first critical/major failure.

---

## Hardware Constraints (From HARDWARE_BASELINE_REPORT.md)

**Target Hardware:** Median Steam user (6-8 core CPU, 16 GB RAM, GTX 1660 Ti / NO GPU)

**Critical Constraint:** **15% of users have NO discrete GPU** → **CPU fallback is MANDATORY**.

**Performance Targets:**
- **CPU-only critique:** <1000ms per image (Phase 1+2+3 combined)
- **GPU critique (if available):** <500ms per image (all phases)
- **Memory footprint:** <2 GB RAM per image (including model weights)

**Model Size Limits:**
- **CPU-only models:** <500 MB weights (ONNX/TensorFlow Lite preferred)
- **GPU models:** <2 GB weights (can use larger CLIP/FaceNet on GPU)

---

## Open Questions (To Be Resolved in Feasibility Analysis)

1. **Hand detection viability:** Can MediaPipe Hands run on CPU in <200ms? What's the false positive rate?
2. **CLIP vs heuristics trade-off:** Is CLIP embedding fast enough on CPU for style/identity checks?
3. **Face detection accuracy:** Does Haar cascade suffice, or do we need a heavier model?
4. **Acceptable error rates:** What false positive/negative rates are acceptable before fallback to shipped art pack?
5. **Hybrid strategy:** Can we use heuristics on CPU, upgrade to CLIP/FaceNet if GPU available?

---

## Next Steps

1. **Feasibility analysis:** Benchmark each measurement approach on target hardware (R0_IMAGE_CRITIQUE_FEASIBILITY.md)
2. **Error quantification:** Measure false positive/negative rates on sample dataset
3. **Bounded regen policy:** Define max attempts, backoff strategy, fallback (R0_BOUNDED_REGEN_POLICY.md)
4. **Threshold calibration:** Empirically determine pass/fail thresholds for each dimension

---

## References

- **Steam Hardware Survey:** https://store.steampowered.com/hwsurvey
- **MediaPipe Hands:** https://google.github.io/mediapipe/solutions/hands
- **CLIP (OpenAI):** https://github.com/openai/CLIP
- **Laplacian Variance (blur detection):** Pech-Pacheco et al., "Diatom autofocusing in brightfield microscopy"
- **FaceNet:** Schroff et al., "FaceNet: A Unified Embedding for Face Recognition and Clustering"

---

## Document Governance

**Status:** R0 / DRAFT
**Approval Required From:** Project owner (human)
**Blocks:** R0_IMAGE_CRITIQUE_FEASIBILITY.md, R0_BOUNDED_REGEN_POLICY.md
**Unblocks:** Immersion pipeline image generation integration (future CP)
