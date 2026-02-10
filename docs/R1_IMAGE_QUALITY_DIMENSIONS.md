# R1 — Image Quality Dimensions Definition
## RQ-IMG-002: Quality Dimension Definition

**Agent:** Agent B (Image Generation & Critique Research Lead)
**RQ ID:** RQ-IMG-002
**Date:** 2026-02-10
**Status:** RESEARCH (Non-binding)
**Authority:** ADVISORY

---

## Research Question

**What constitutes "acceptable" generated art for AIDM?**

Define machine-checkable quality dimensions that enforce immersion standards without requiring human labeling at runtime.

---

## Methods

### Source Analysis
1. **Inbox Requirements Extraction**
   - Chronological Design Record (Phase 4-5): Image quality risk, visual presentation model
   - Secondary Pass Audit Checklist (Section 3.2): Critique checklists

2. **Literature Survey**
   - CLIP-based image quality assessment (2024-2026)
   - Heuristic artifact detection methods
   - Document image quality assessment benchmarks

3. **AIDM-Specific Constraints**
   - Prep-first generation (NPC portraits, scene backgrounds)
   - Sprite/portrait composition model (not photorealistic)
   - Hardware baseline: Steam Hardware Survey median (CPU fallback required)

---

## Quality Dimensions (Taxonomy)

Based on Inbox requirements and IQA literature, AIDM image quality assessment must cover **5 core dimensions**:

| Dimension ID | Dimension | Definition | Criticality |
|--------------|-----------|------------|-------------|
| **DIM-01** | **Readability** | Subject identifiable at intended UI size (portrait: 128×128, scene: 512×384) | CRITICAL |
| **DIM-02** | **Composition** | Subject centering, cropping, framing appropriate for use case | HIGH |
| **DIM-03** | **Artifacting** | Absence of obvious anatomical errors (hands, faces), edge coherence, texture noise | CRITICAL |
| **DIM-04** | **Style Adherence** | Consistency with campaign tone (fantasy vs sci-fi), visual palette | MEDIUM |
| **DIM-05** | **Identity Continuity** | NPC anchor portraits maintain species, gear, pose across regenerations | HIGH |

---

## Dimension Details

### DIM-01: Readability (CRITICAL)

**Definition:** Subject must be identifiable at intended UI size.

**AIDM Use Cases:**
- NPC portraits: 128×128 pixels (character sheet companion)
- Scene backgrounds: 512×384 pixels (contextual grid backdrop)
- Icon/token sprites: 64×64 pixels (combat grid)

**Machine-Checkable Proxies:**
- Contrast ratio (WCAG AAA standard: ≥7:1 for text-like elements)
- Edge sharpness (Laplacian variance > threshold)
- Downsample test: Resize to target UI size, measure perceptual hash similarity to original

**Heuristic Implementation:**
```python
# Pseudo-code for readability check
def check_readability(image, target_size=(128, 128)):
    # 1. Downsample to UI size
    downsampled = resize(image, target_size)

    # 2. Measure edge sharpness (Laplacian variance)
    gray = to_grayscale(downsampled)
    laplacian_var = variance(laplacian(gray))

    # 3. Contrast ratio (foreground vs background)
    fg_brightness = mean(brightest_20_percent(downsampled))
    bg_brightness = mean(darkest_20_percent(downsampled))
    contrast_ratio = fg_brightness / bg_brightness

    # Thresholds (empirical, to be validated in RQ-IMG-001)
    return (laplacian_var > 100) and (contrast_ratio > 3.0)
```

**Failure Mode:** Blurry portraits that look like "smudges" at 128×128.

**Literature Support:** Document image quality assessment uses character-based features (strokes, holes, aspect ratio, black pixels) for readability ([ACM Survey on Document IQA](https://dl.acm.org/doi/10.1145/3606692)).

---

### DIM-02: Composition (HIGH)

**Definition:** Subject centering, cropping, framing appropriate for use case.

**AIDM Use Cases:**
- NPC portraits: Face/upper torso centered, appropriate headroom
- Scene backgrounds: Horizon line placement, focal point positioning

**Machine-Checkable Proxies:**
- Center-of-mass analysis (subject within central 60% of frame)
- Horizon line detection (for landscapes: horizontal line within middle third)
- Bounding box analysis (subject occupies 40-70% of frame area)

**Heuristic Implementation:**
```python
# Pseudo-code for composition check
def check_composition(image, use_case="portrait"):
    # 1. Detect subject bounding box (simple saliency or edge-based)
    bbox = detect_subject_bbox(image)

    # 2. Center-of-mass check
    img_center = (image.width / 2, image.height / 2)
    bbox_center = ((bbox.x1 + bbox.x2) / 2, (bbox.y1 + bbox.y2) / 2)
    distance_from_center = euclidean_distance(img_center, bbox_center)

    # 3. Subject area ratio
    subject_area = (bbox.x2 - bbox.x1) * (bbox.y2 - bbox.y1)
    image_area = image.width * image.height
    area_ratio = subject_area / image_area

    # Thresholds (portrait-specific)
    if use_case == "portrait":
        return (distance_from_center < 0.2 * image.width) and (0.4 < area_ratio < 0.7)

    # Scene backgrounds: different thresholds
    elif use_case == "scene":
        return (area_ratio > 0.3)  # Looser composition constraints
```

**Failure Mode:** NPC portrait cropped at neck, face off-center, excessive headroom.

**Literature Support:** Semantic Object Alignment (SOA) metric for composition in text-to-image generation ([Survey on T2I Quality Metrics](https://arxiv.org/html/2403.11821v5)).

---

### DIM-03: Artifacting (CRITICAL)

**Definition:** Absence of obvious anatomical errors, edge coherence, texture noise.

**AIDM Critical Artifacts:**
1. **Anatomical Distortions:** Malformed hands (extra/missing fingers), asymmetric faces, incoherent body geometry
2. **Edge Artifacts:** Ringing, halos, discontinuities at subject boundaries
3. **Texture Noise:** Color banding, patchy textures, compression-like artifacts

**Machine-Checkable Proxies:**

#### 3A. Hand/Face Detection (Anatomy)
- Use lightweight face/hand detector (e.g., MediaPipe Hands, MTCNN Face Detection)
- Check finger count (hands: 5 fingers expected, tolerance ±1)
- Check facial symmetry (left/right eye alignment, nose centering)

```python
# Pseudo-code for anatomical artifact detection
def check_anatomy(image):
    # 1. Detect hands
    hands = detect_hands(image)  # MediaPipe Hands (lightweight, runs on CPU)
    for hand in hands:
        finger_count = count_fingers(hand)
        if not (4 <= finger_count <= 6):  # Allow ±1 tolerance
            return FAIL("Hand anatomy: unexpected finger count")

    # 2. Detect faces
    faces = detect_faces(image)  # MTCNN (lightweight)
    for face in faces:
        left_eye, right_eye = detect_eyes(face)
        symmetry_score = abs(left_eye.y - right_eye.y) / face.height
        if symmetry_score > 0.1:  # Eyes on different horizontal levels
            return FAIL("Face anatomy: asymmetric eyes")

    return PASS
```

#### 3B. Edge Coherence
- Canny edge detection → measure edge continuity
- Detect ringing artifacts (high-frequency oscillations near edges)

```python
# Pseudo-code for edge artifact detection
def check_edge_coherence(image):
    # 1. Canny edge detection
    edges = canny_edge_detection(image, threshold1=50, threshold2=150)

    # 2. Measure edge continuity (gap detection)
    edge_gaps = detect_gaps_in_edges(edges, max_gap=5)

    # 3. Ringing detection (high-freq oscillations near edges)
    ringing_score = measure_ringing(image, edges)

    return (len(edge_gaps) < 10) and (ringing_score < 0.2)
```

#### 3C. Texture Noise
- Color banding detection (histogram analysis)
- Patch coherence (spatial autocorrelation)

```python
# Pseudo-code for texture noise detection
def check_texture_quality(image):
    # 1. Color banding (histogram spikes)
    hist = compute_histogram(image)
    banding_score = detect_histogram_spikes(hist)

    # 2. Patch coherence (spatial autocorrelation)
    patches = extract_patches(image, patch_size=32)
    coherence_scores = [spatial_autocorrelation(p) for p in patches]
    avg_coherence = mean(coherence_scores)

    return (banding_score < 0.3) and (avg_coherence > 0.5)
```

**Failure Modes:**
- NPC with 7 fingers on one hand
- Portrait with asymmetric face (one eye higher than the other)
- Scene background with ringing halos around trees

**Literature Support:**
- AI-generated images exhibit "pronounced anatomical distortions, particularly in the rendering of hands and facial features" ([arXiv: Does CLIP perceive art](https://arxiv.org/html/2505.05229v1))
- JPEG artifacts include "color shift, blocking, blurring, or ringing irregularities" ([PMC Review of IQA Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11121858/))
- Neural artifacts: "distortion of text, color, textures, and borders" ([arXiv: JPEG AI Artifacts](https://arxiv.org/html/2411.06810v1))

---

### DIM-04: Style Adherence (MEDIUM)

**Definition:** Consistency with campaign tone (fantasy vs sci-fi), visual palette.

**AIDM Use Cases:**
- Fantasy campaign: Medieval armor, stone castles, torches
- Sci-fi campaign: Power armor, neon lighting, metallic surfaces

**Machine-Checkable Proxies:**
- Color palette extraction (k-means clustering)
- Style transfer distance (compare to reference style embedding)
- CLIP-based style matching (text prompt: "fantasy art" vs "cyberpunk art")

**Heuristic Implementation:**
```python
# Pseudo-code for style adherence check
def check_style_adherence(image, campaign_style="fantasy"):
    # 1. Extract color palette
    palette = extract_color_palette(image, n_colors=5)

    # 2. Compare to reference palette
    ref_palette = REFERENCE_PALETTES[campaign_style]
    palette_distance = color_distance(palette, ref_palette)

    # 3. CLIP-based style check (if GPU available)
    if gpu_available():
        style_prompt = f"{campaign_style} art"
        clip_score = clip_text_image_similarity(image, style_prompt)
        return (palette_distance < 0.3) and (clip_score > 0.25)

    # CPU fallback: palette-only check
    else:
        return (palette_distance < 0.3)
```

**Failure Mode:** Fantasy campaign generates NPC with neon cyberpunk lighting.

**Literature Support:** CLIP direction similarity for style consistency ([HuggingFace: Evaluating Diffusion Models](https://huggingface.co/docs/diffusers/en/conceptual/evaluation)).

---

### DIM-05: Identity Continuity (HIGH)

**Definition:** NPC anchor portraits maintain species, gear, pose across regenerations.

**AIDM Constraint:** NPC portraits generated once, reused across sessions. Regeneration only on manual user override or asset corruption.

**Machine-Checkable Proxies:**
- Perceptual hash (pHash) similarity between regeneration attempts
- CLIP embedding similarity (same entity prompt → similar visual embedding)
- Bounding box overlap (subject position consistency)

**Heuristic Implementation:**
```python
# Pseudo-code for identity continuity check
def check_identity_continuity(new_image, reference_image):
    # 1. Perceptual hash similarity
    phash_new = perceptual_hash(new_image)
    phash_ref = perceptual_hash(reference_image)
    phash_distance = hamming_distance(phash_new, phash_ref)

    # 2. CLIP embedding similarity (if GPU available)
    if gpu_available():
        clip_sim = clip_image_similarity(new_image, reference_image)
        return (phash_distance < 10) and (clip_sim > 0.7)

    # CPU fallback: perceptual hash only
    else:
        return (phash_distance < 10)
```

**Failure Mode:** Regeneration of "Dwarf Fighter Theron" produces image with Elf ears instead of dwarf beard.

**Literature Support:** Perceptual hashing for image similarity ([ScienceDirect: Image Quality Assessment](https://www.sciencedirect.com/topics/engineering/image-quality-assessment)).

---

## Dimension Prioritization (Critical Path)

| Dimension | Criticality | Rationale | Failure Impact |
|-----------|-------------|-----------|----------------|
| **DIM-03 (Artifacting)** | CRITICAL | Malformed hands/faces break immersion immediately | User abandonment |
| **DIM-01 (Readability)** | CRITICAL | Blurry portraits unusable in UI | UX failure |
| **DIM-05 (Identity Continuity)** | HIGH | NPC identity drift damages campaign continuity | Immersion damage |
| **DIM-02 (Composition)** | HIGH | Poor framing noticeable but tolerable | UX degradation |
| **DIM-04 (Style Adherence)** | MEDIUM | Style drift acceptable if other dimensions pass | Minor immersion impact |

---

## Acceptance Thresholds (For RQ-IMG-001 Model Selection)

### Minimum Viable Quality (MVQ)
An image PASSES quality gate if:
- ✅ **DIM-03 (Artifacting):** No anatomical errors detected
- ✅ **DIM-01 (Readability):** Laplacian variance > 100, contrast ratio > 3.0
- ✅ **DIM-05 (Identity Continuity):** pHash distance < 10 (for regenerations only)

**Dimensions DIM-02 and DIM-04** are OPTIONAL (nice-to-have for enhanced quality).

### Model Evaluation Criteria (RQ-IMG-001)
Image critique models will be evaluated on:
1. **Precision (DIM-03):** False Positive Rate (FPR) < 0.10 (blocking good art)
2. **Recall (DIM-03):** False Negative Rate (FNR) < 0.05 (allowing broken art)
3. **Latency:** ≤ 150 ms (GPU), ≤ 250 ms (CPU)
4. **F1 Score:** ≥ 0.75 (GPU), ≥ 0.60 (CPU)

---

## Heuristic-Only Baseline (No Model Required)

**Question:** Can heuristics alone satisfy MVQ without CLIP or classifiers?

**Hypothesis:** YES, for DIM-01 and DIM-02. UNCERTAIN for DIM-03 (anatomy detection).

| Dimension | Heuristic-Only Feasibility | Notes |
|-----------|----------------------------|-------|
| DIM-01 (Readability) | ✅ YES | Laplacian variance, contrast ratio (CPU-friendly) |
| DIM-02 (Composition) | ✅ YES | Bounding box, center-of-mass (CPU-friendly) |
| DIM-03 (Artifacting) | ⚠️ PARTIAL | Hand/face detection requires lightweight ML (MediaPipe) |
| DIM-04 (Style) | ❌ NO | Requires CLIP or reference style embeddings |
| DIM-05 (Identity) | ✅ YES | Perceptual hash (CPU-friendly) |

**Conclusion:** Heuristics can cover 3.5/5 dimensions. DIM-03 requires lightweight ML (MediaPipe Hands, MTCNN Face). DIM-04 requires CLIP (GPU-optional).

---

## Test Dataset Requirements (For RQ-IMG-001)

To evaluate critique models, Agent B requires:
1. **Positive Set:** 100+ "good" AIDM-style portraits (readable, anatomically correct, well-composed)
2. **Negative Set:** 100+ "bad" portraits (blurry, malformed hands, asymmetric faces, poor composition)
3. **Ground Truth Labels:** Human-annotated binary labels (pass/fail per dimension)

**Source Options:**
- Generate synthetic test set using Stable Diffusion 1.5 + manual filtering
- Use existing AI-generated image datasets (e.g., AGIQA-3K, DrawBench)
- Commission human artists for ground truth "gold standard" examples

**Risk:** No AIDM-specific test dataset exists. Agent B must create one OR adapt existing benchmarks.

---

## Risks & Limitations

### Risk 1: Heuristic Brittleness
**Nature:** Threshold-based heuristics (e.g., Laplacian variance > 100) may not generalize across diverse art styles.

**Mitigation:** Calibrate thresholds using test dataset (RQ-IMG-001). Allow per-campaign tuning via Session Zero config.

### Risk 2: Anatomy Detection False Negatives
**Nature:** MediaPipe Hands may miss malformed hands in stylized art (e.g., cartoonish proportions).

**Mitigation:** Hybrid approach: heuristics + CLIP-based anomaly detection. If anatomy detector fails, escalate to CLIP.

### Risk 3: CLIP Bias Toward Photorealism
**Nature:** CLIP trained on natural images; may penalize stylized fantasy art.

**Mitigation:** Fine-tune CLIP on fantasy art corpus OR use CLIP only for DIM-04 (style adherence), not anatomical checks.

### Risk 4: CPU-Only Fallback Degradation
**Nature:** Without GPU, CLIP unavailable → DIM-04 (style) and enhanced DIM-03 (anatomy via CLIP) disabled.

**Mitigation:** Heuristic-only mode covers DIM-01, DIM-02, DIM-05. DIM-03 uses MediaPipe (CPU-capable). DIM-04 disabled on CPU.

---

## Dependencies for RQ-IMG-001

RQ-IMG-001 (Model Selection) depends on this document defining:
- ✅ Quality dimensions (5 defined)
- ✅ Acceptance thresholds (F1 ≥ 0.75 GPU, ≥ 0.60 CPU)
- ✅ Failure mode taxonomy (anatomical, edge, texture)
- ✅ Heuristic baselines (readability, composition, identity)

**Next Steps for RQ-IMG-001:**
1. Implement heuristic baseline (DIM-01, DIM-02, DIM-05)
2. Benchmark MediaPipe Hands + MTCNN Face (DIM-03 anatomy)
3. Benchmark CLIP-IQA (DIM-04 style)
4. Evaluate hybrid approach (heuristics + MediaPipe + CLIP)
5. Measure F1, FPR, FNR, latency on test dataset

---

## Recommendation

**APPROVE quality dimension taxonomy for RQ-IMG-001 evaluation.**

**Key Findings:**
1. **5 quality dimensions** identified: Readability, Composition, Artifacting, Style, Identity
2. **Critical dimensions:** Artifacting (DIM-03), Readability (DIM-01)
3. **Heuristics viable** for DIM-01, DIM-02, DIM-05 (CPU-friendly)
4. **Lightweight ML required** for DIM-03 anatomy detection (MediaPipe Hands, MTCNN Face)
5. **CLIP optional** for DIM-04 style adherence (GPU-only)

**NO-GO Triggers:**
- If DIM-03 (anatomical artifact detection) FNR > 0.05 (allowing broken hands/faces)
- If GPU-path F1 < 0.75 OR CPU-path F1 < 0.60
- If critique latency > 150 ms (GPU) OR > 250 ms (CPU)

---

## Sources

- [ACM Survey on Document Image Quality Assessment](https://dl.acm.org/doi/10.1145/3606692)
- [arXiv: Survey on Quality Metrics for Text-to-Image Generation](https://arxiv.org/html/2403.11821v5)
- [arXiv: Does CLIP perceive art the same way we do?](https://arxiv.org/html/2505.05229v1)
- [PMC: Review of Image Quality Assessment Methods for Compressed Images](https://pmc.ncbi.nlm.nih.gov/articles/PMC11121858/)
- [arXiv: JPEG AI Image Compression Visual Artifacts](https://arxiv.org/html/2411.06810v1)
- [HuggingFace: Evaluating Diffusion Models](https://huggingface.co/docs/diffusers/en/conceptual/evaluation)
- [ScienceDirect: Image Quality Assessment Topics](https://www.sciencedirect.com/topics/engineering/image-quality-assessment)
- [Imatest: Artifacts](https://www.imatest.com/imaging/artifacts/)
- [GitHub: Awesome Image Quality Assessment](https://github.com/chaofengc/Awesome-Image-Quality-Assessment)

---

**END OF RQ-IMG-002 DELIVERABLE**

**Date:** 2026-02-10
**Agent:** Agent B (Image Generation & Critique Research Lead)
**Status:** COMPLETE (RQ-IMG-002 answered)
**Next RQ:** RQ-IMG-001 (Model Selection)
**Confidence:** 0.88
