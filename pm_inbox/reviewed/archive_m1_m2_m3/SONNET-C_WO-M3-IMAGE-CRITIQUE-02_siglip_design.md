# SigLIPCritiqueAdapter Design Specification (Layer 3)

**Agent:** Sonnet-C
**Work Order:** WO-M3-IMAGE-CRITIQUE-02
**Date:** 2026-02-11
**Status:** Design Specification

---

## 1. Overview

**SigLIPCritiqueAdapter** is Layer 3 (optional) in the graduated critique pipeline. It compares generated images against reference images to ensure identity consistency—critical for regenerating NPC portraits across sessions.

**Model Details**:
- **Paper**: "Sigmoid Loss for Language Image Pre-Training" (Google Research)
- **License**: Apache 2.0
- **Size**: ~0.6 GB FP16
- **VRAM**: ~0.6 GB peak
- **Performance**: <1s per comparison on GPU

**Use Case**: Only invoked when reference images exist (e.g., regenerating an NPC portrait that must match previous sessions).

---

## 2. Architecture

### 2.1 Role in Graduated Pipeline

```
Generated Image + Reference Image(s)
    ↓
┌──────────────────────────┐
│ Layers 1 & 2 (passed)    │
└───────────┬──────────────┘
            │
            ▼
┌─────────────────────────────────┐
│ Layer 3: SigLIP (OPTIONAL)      │ <-- YOU ARE HERE
│ - Only if reference exists      │
│ - Load SigLIP model             │
│ - Compute embedding similarity  │
│ - Unload model                  │
└──────────┬──────────────────────┘
           │
      ┌────┴────┐
   FAIL       PASS
      │         │
   REGENERATE  ACCEPT
```

**When to Invoke**:
- ✅ Regenerating existing NPC portrait (anchor image available)
- ✅ Ensuring visual consistency across sessions
- ❌ First-time generation (no reference exists)
- ❌ Scene illustrations (identity less critical)

---

## 3. Class Structure

```python
class SigLIPCritiqueAdapter:
    """Layer 3: Reference-based identity consistency using SigLIP.

    Implements ImageCritiqueAdapter protocol.

    Attributes:
        model_name: SigLIP model variant (default: "ViT-B-16-SigLIP")
        device: Compute device
        similarity_threshold: Minimum cosine similarity for identity match (default: 0.70)
        model: Loaded SigLIP model
        preprocess: SigLIP preprocessing pipeline
    """

    def __init__(
        self,
        model_name: str = "ViT-B-16-SigLIP",
        device: Optional[str] = None,
        similarity_threshold: float = 0.70
    ):
        self.model_name = model_name
        self.device = device or self._detect_device()
        self.similarity_threshold = similarity_threshold
        self.model = None
        self.preprocess = None

    def load(self):
        """Load SigLIP model."""
        import open_clip
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            self.model_name,
            pretrained="webli",
            device=self.device
        )
        self.model.eval()

    def unload(self):
        """Unload model and free VRAM."""
        if self.model is not None:
            del self.model
            del self.preprocess
            self.model = None
            self.preprocess = None
            torch.cuda.empty_cache()

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        **kwargs
    ) -> CritiqueResult:
        """Compare image against reference for identity consistency.

        Args:
            image_bytes: Generated image
            rubric: Quality thresholds
            anchor_image_bytes: Reference image (REQUIRED for SigLIP)
            **kwargs: Ignored

        Returns:
            CritiqueResult with identity_match score
        """
        if anchor_image_bytes is None:
            # No reference → skip Layer 3, return perfect score
            return self._create_skip_result("No anchor image provided")

        # Load model if not loaded
        if self.model is None:
            self.load()

        # Load images
        image = self._load_image_from_bytes(image_bytes)
        anchor = self._load_image_from_bytes(anchor_image_bytes)

        # Compute embedding similarity
        similarity = self._compute_similarity(image, anchor)

        # Map similarity to CritiqueResult
        return self._map_similarity_to_result(similarity, rubric)
```

---

## 4. Similarity Computation

```python
def _compute_similarity(
    self,
    image: Image.Image,
    anchor: Image.Image
) -> float:
    """Compute cosine similarity between image embeddings.

    Args:
        image: Generated image (PIL)
        anchor: Reference image (PIL)

    Returns:
        Cosine similarity (0.0-1.0)
    """
    import torch

    # Preprocess images
    image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
    anchor_tensor = self.preprocess(anchor).unsqueeze(0).to(self.device)

    # Encode images to embeddings
    with torch.no_grad():
        image_features = self.model.encode_image(image_tensor)
        anchor_features = self.model.encode_image(anchor_tensor)

    # Normalize embeddings
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    anchor_features = anchor_features / anchor_features.norm(dim=-1, keepdim=True)

    # Compute cosine similarity
    similarity = (image_features @ anchor_features.T).item()

    # Clip to [0.0, 1.0] (should already be in this range)
    return max(0.0, min(1.0, similarity))
```

---

## 5. Score Mapping

```python
def _map_similarity_to_result(
    self,
    similarity: float,
    rubric: CritiqueRubric
) -> CritiqueResult:
    """Map similarity score to CritiqueResult.

    Args:
        similarity: Cosine similarity (0.0-1.0)
        rubric: Quality thresholds

    Returns:
        CritiqueResult with identity_match dimension
    """
    dimensions = []

    # SigLIP measures identity_match (reference similarity)
    dimensions.append(CritiqueDimension(
        dimension=DimensionType.IDENTITY_MATCH,
        severity=self._score_to_severity(similarity, rubric.identity_threshold),
        score=similarity,
        reason=f"Identity similarity vs reference (cosine: {similarity:.3f})",
        measurement_method="siglip_embedding_similarity"
    ))

    # Skip other dimensions (handled by Layers 1 & 2)
    for dim_type in [DimensionType.ARTIFACTING, DimensionType.COMPOSITION,
                     DimensionType.READABILITY, DimensionType.STYLE_ADHERENCE]:
        dimensions.append(CritiqueDimension(
            dimension=dim_type,
            severity=SeverityLevel.ACCEPTABLE,
            score=1.0,
            reason=f"SigLIP does not measure {dim_type.value} (handled by earlier layers)",
            measurement_method="skipped"
        ))

    dimensions.sort(key=lambda d: d.dimension.value)

    passed = similarity >= self.similarity_threshold

    return CritiqueResult(
        passed=passed,
        overall_severity=self._score_to_severity(similarity, self.similarity_threshold),
        dimensions=dimensions,
        overall_score=similarity,
        rejection_reason=None if passed else f"Low identity similarity (score: {similarity:.3f})",
        critique_method="siglip_reference_comparison"
    )
```

---

## 6. Threshold Calibration

### 6.1 Expected Similarity Ranges

| Scenario | Expected Similarity | Notes |
|----------|---------------------|-------|
| **Same character, different angle** | 0.75-0.85 | Good identity match |
| **Same character, different attire** | 0.70-0.80 | Acceptable match |
| **Different character, similar features** | 0.50-0.70 | Borderline |
| **Completely different** | <0.50 | Clear mismatch |

### 6.2 Recommended Threshold

**Default: 0.70** — Balances false positives and false negatives.

---

## 7. Performance Analysis

| Operation | Time (GPU) | VRAM |
|-----------|------------|------|
| **Model load** | ~2s | ~0.6 GB |
| **Image preprocessing** | ~30ms | — |
| **Embedding computation (×2)** | ~400ms | ~0.2 GB |
| **Similarity computation** | ~5ms | — |
| **TOTAL** | **~0.45s** | **~0.8 GB peak** |

✅ Well under 1s target and VRAM budget.

---

## 8. Testing Strategy

```python
def test_siglip_critic_same_character_passes():
    """SigLIPCritiqueAdapter passes similar character images."""
    critic = create_image_critic("siglip")
    critic.load()

    result = critic.critique(
        image_bytes=DWARF_V2_IMAGE,
        rubric=DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=DWARF_V1_IMAGE  # Same character, different angle
    )

    assert result.passed is True
    identity_dim = [d for d in result.dimensions if d.dimension == DimensionType.IDENTITY_MATCH][0]
    assert identity_dim.score >= 0.70

    critic.unload()


def test_siglip_critic_different_character_fails():
    """SigLIPCritiqueAdapter rejects different character."""
    critic = create_image_critic("siglip", similarity_threshold=0.70)
    critic.load()

    result = critic.critique(
        image_bytes=ELF_IMAGE,
        rubric=DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=DWARF_IMAGE  # Different species
    )

    assert result.passed is False
    assert "low identity similarity" in result.rejection_reason.lower()

    critic.unload()
```

---

## 9. Dependencies

```toml
[tool.poetry.dependencies]
open-clip-torch = "^2.20.0"  # Apache 2.0 license
torch = "^2.0.0"
Pillow = "^10.0.0"
```

---

## 10. Integration with Full Pipeline

```python
def critique_all_layers(
    image_bytes: bytes,
    generation_prompt: str,
    rubric: CritiqueRubric,
    anchor_image_bytes: Optional[bytes] = None
) -> CritiqueResult:
    """Run all 3 layers sequentially.

    Args:
        image_bytes: Generated image
        generation_prompt: Generation prompt
        rubric: Quality thresholds
        anchor_image_bytes: Reference image (optional)

    Returns:
        CritiqueResult from first failing layer or Layer 3
    """
    # Layer 1: Heuristics
    layer1_result = create_image_critic("heuristics").critique(image_bytes, rubric)
    if not layer1_result.passed:
        return layer1_result

    # Layer 2: ImageReward
    layer2_critic = create_image_critic("imagereward")
    layer2_critic.load()
    layer2_result = layer2_critic.critique(image_bytes, rubric, prompt=generation_prompt)
    layer2_critic.unload()

    if not layer2_result.passed:
        return layer2_result

    # Layer 3: SigLIP (optional)
    if anchor_image_bytes:
        layer3_critic = create_image_critic("siglip")
        layer3_critic.load()
        layer3_result = layer3_critic.critique(image_bytes, rubric, anchor_image_bytes=anchor_image_bytes)
        layer3_critic.unload()
        return layer3_result
    else:
        # No anchor → return Layer 2 result
        return layer2_result
```

---

## 11. Gap Analysis

### What Exists:
✅ ImageCritiqueAdapter protocol
✅ CritiqueResult schemas

### What's Missing:
❌ SigLIPCritiqueAdapter implementation
❌ open-clip-torch dependency
❌ Calibration data

### Implementation Checklist:
1. ✅ Design complete
2. ❌ Add open-clip-torch to pyproject.toml
3. ❌ Implement SigLIPCritiqueAdapter
4. ❌ Calibrate similarity_threshold
5. ❌ Write tests
6. ❌ Profile VRAM/performance

---

**END OF SPECIFICATION**
