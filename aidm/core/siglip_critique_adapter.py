"""SigLIP-based image critique adapter (Layer 3).

M3 IMPLEMENTATION: SigLIPCritiqueAdapter
----------------------------------------
Reference-based identity consistency validation using SigLIP embeddings.
Ensures NPC portraits maintain visual identity across regenerations.

This is Layer 3 (optional) of the graduated critique pipeline. It only runs
when a reference image exists (e.g., regenerating an existing NPC portrait).

Based on approved design: SONNET-C_WO-M3-IMAGE-CRITIQUE-02_siglip_design.md

Architecture:
    - Uses SigLIP (Sigmoid Loss for Language Image Pre-Training)
    - Model: ViT-B-16-SigLIP pretrained on WebLI (~0.6 GB FP16)
    - Computes cosine similarity between image embeddings
    - Maps to IDENTITY_MATCH dimension only
    - Implements ImageCritiqueAdapter protocol
    - Lazy loading: model loaded on first critique() or explicit load()
"""

from typing import Optional, Tuple
import io
from PIL import Image

from aidm.schemas.image_critique import (
    CritiqueResult,
    CritiqueRubric,
    CritiqueDimension,
    DimensionType,
    SeverityLevel,
)


class SigLIPCritiqueAdapter:
    """Layer 3: Reference-based identity consistency using SigLIP.

    Implements ImageCritiqueAdapter protocol.

    This adapter compares generated images against reference images to ensure
    identity consistency. Only invoked when anchor_image_bytes is provided.

    Attributes:
        model_name: SigLIP model variant (default: "ViT-B-16-SigLIP")
        pretrained: Pretrained checkpoint name (default: "webli")
        device: Compute device (cuda/mps/cpu, auto-detected if None)
        similarity_threshold: Minimum cosine similarity for pass (default: 0.70)
        model: Loaded SigLIP model (None until load() called)
        preprocess: SigLIP preprocessing pipeline (None until load() called)
    """

    def __init__(
        self,
        model_name: str = "ViT-B-16-SigLIP",
        pretrained: str = "webli",
        device: Optional[str] = None,
        similarity_threshold: float = 0.70
    ):
        """Initialize SigLIP critic.

        Args:
            model_name: SigLIP model variant
            pretrained: Pretrained checkpoint name
            device: Compute device (None for auto-detection)
            similarity_threshold: Minimum cosine similarity for identity match (0.0-1.0)
        """
        if not (0.0 <= similarity_threshold <= 1.0):
            raise ValueError(
                f"similarity_threshold must be in [0.0, 1.0], got {similarity_threshold}"
            )

        self.model_name = model_name
        self.pretrained = pretrained
        self.device = device or self._detect_device()
        self.similarity_threshold = similarity_threshold
        self.model = None
        self.preprocess = None

    def _detect_device(self) -> str:
        """Detect best available compute device.

        Returns:
            Device string: "cuda", "mps", or "cpu"
        """
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        except ImportError:
            return "cpu"

    def load(self):
        """Load SigLIP model and preprocessing pipeline.

        Loads model to self.device. Model is set to eval() mode.
        Raises ImportError if open_clip not installed.
        """
        try:
            import open_clip
        except ImportError:
            raise ImportError(
                "open-clip-torch is required for SigLIPCritiqueAdapter. "
                "Install with: pip install open-clip-torch"
            )

        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            self.model_name,
            pretrained=self.pretrained,
            device=self.device
        )
        self.model.eval()

    def unload(self):
        """Unload model and free VRAM.

        Clears model and preprocessing pipeline from memory.
        Calls torch.cuda.empty_cache() if CUDA is available.
        """
        if self.model is not None:
            del self.model
            del self.preprocess
            self.model = None
            self.preprocess = None

            # Free VRAM if CUDA available
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        """Compare image against reference for identity consistency.

        Implements ImageCritiqueAdapter protocol.

        If anchor_image_bytes is None, returns skip result immediately without
        loading the model (Layer 3 is optional).

        Args:
            image_bytes: Generated image (PNG/JPEG bytes)
            rubric: Quality thresholds
            anchor_image_bytes: Reference image for identity comparison (optional)
            style_reference_bytes: Ignored by SigLIP (handled by Layer 2)

        Returns:
            CritiqueResult with identity_match score

        Raises:
            ValueError: If image_bytes is empty or invalid
        """
        # Layer 3 is optional — skip if no anchor image provided
        if anchor_image_bytes is None:
            return self._create_skip_result("No anchor image provided (Layer 3 optional)")

        # Load model if not already loaded (lazy loading)
        if self.model is None:
            self.load()

        # Load images
        try:
            image = self._load_image_from_bytes(image_bytes)
            anchor = self._load_image_from_bytes(anchor_image_bytes)
        except Exception as e:
            return self._create_error_result(f"Image load failed: {e}")

        # Compute embedding similarity
        try:
            similarity = self._compute_similarity(image, anchor)
        except Exception as e:
            return self._create_error_result(f"Similarity computation failed: {e}")

        # Map similarity to CritiqueResult
        return self._map_similarity_to_result(similarity, rubric)

    def _load_image_from_bytes(self, image_bytes: bytes) -> Image.Image:
        """Load PIL Image from bytes.

        Args:
            image_bytes: PNG/JPEG bytes

        Returns:
            PIL Image in RGB mode

        Raises:
            ValueError: If image cannot be loaded
        """
        if not image_bytes:
            raise ValueError("Image bytes cannot be empty")

        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            # Convert to RGB (removes alpha if present)
            pil_image = pil_image.convert('RGB')
            return pil_image
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}")

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

        # Normalize embeddings (L2 normalization)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        anchor_features = anchor_features / anchor_features.norm(dim=-1, keepdim=True)

        # Compute cosine similarity (dot product of normalized vectors)
        similarity = (image_features @ anchor_features.T).item()

        # Clip to [0.0, 1.0] (should already be in this range, but ensure)
        return max(0.0, min(1.0, similarity))

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
        identity_severity = self._score_to_severity(similarity, rubric.identity_threshold)
        dimensions.append(CritiqueDimension(
            dimension=DimensionType.IDENTITY_MATCH,
            severity=identity_severity,
            score=similarity,
            reason=f"Identity similarity vs reference (cosine: {similarity:.3f})",
            measurement_method="siglip_embedding_similarity"
        ))

        # Skip other dimensions (handled by Layers 1 & 2)
        for dim_type in [
            DimensionType.ARTIFACTING,
            DimensionType.COMPOSITION,
            DimensionType.READABILITY,
            DimensionType.STYLE_ADHERENCE
        ]:
            dimensions.append(CritiqueDimension(
                dimension=dim_type,
                severity=SeverityLevel.ACCEPTABLE,
                score=1.0,
                reason=f"SigLIP does not measure {dim_type.value} (handled by earlier layers)",
                measurement_method="skipped"
            ))

        # Sort dimensions by dimension type value (required by CritiqueResult)
        dimensions.sort(key=lambda d: d.dimension.value)

        # Determine pass/fail
        passed = similarity >= self.similarity_threshold

        # Compute overall severity
        overall_severity = identity_severity

        # Create rejection reason if failed
        rejection_reason = None
        if not passed:
            rejection_reason = (
                f"Low identity similarity (score: {similarity:.3f}, "
                f"threshold: {self.similarity_threshold:.3f})"
            )

        return CritiqueResult(
            passed=passed,
            overall_severity=overall_severity,
            dimensions=dimensions,
            overall_score=similarity,
            rejection_reason=rejection_reason,
            critique_method="siglip_reference_comparison"
        )

    def _score_to_severity(self, score: float, threshold: float) -> SeverityLevel:
        """Map score to severity level.

        Args:
            score: Numeric score (0.0-1.0)
            threshold: Pass/fail threshold

        Returns:
            SeverityLevel based on score vs threshold
        """
        if score >= 0.90:
            return SeverityLevel.ACCEPTABLE
        elif score >= threshold:
            return SeverityLevel.ACCEPTABLE
        elif score >= 0.50:
            return SeverityLevel.MINOR
        elif score >= 0.30:
            return SeverityLevel.MAJOR
        else:
            return SeverityLevel.CRITICAL

    def _create_skip_result(self, reason: str) -> CritiqueResult:
        """Create skip result when no anchor image provided.

        Args:
            reason: Skip reason (e.g., "No anchor image provided")

        Returns:
            CritiqueResult with all dimensions skipped, passed=True
        """
        dimensions = []

        # All dimensions skipped with perfect scores
        for dim_type in [
            DimensionType.ARTIFACTING,
            DimensionType.COMPOSITION,
            DimensionType.IDENTITY_MATCH,
            DimensionType.READABILITY,
            DimensionType.STYLE_ADHERENCE
        ]:
            dimensions.append(CritiqueDimension(
                dimension=dim_type,
                severity=SeverityLevel.ACCEPTABLE,
                score=1.0,
                reason=reason,
                measurement_method="skipped"
            ))

        # Dimensions already sorted by dimension type value
        dimensions.sort(key=lambda d: d.dimension.value)

        return CritiqueResult(
            passed=True,
            overall_severity=SeverityLevel.ACCEPTABLE,
            dimensions=dimensions,
            overall_score=1.0,
            rejection_reason=None,
            critique_method="siglip_skipped"
        )

    def _create_error_result(self, error_message: str) -> CritiqueResult:
        """Create error CritiqueResult.

        Args:
            error_message: Error description

        Returns:
            CritiqueResult with passed=False and error information
        """
        return CritiqueResult(
            passed=False,
            overall_severity=SeverityLevel.CRITICAL,
            dimensions=[],
            overall_score=0.0,
            rejection_reason=error_message,
            critique_method="siglip_error"
        )
