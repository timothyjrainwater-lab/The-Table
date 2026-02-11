"""M3 SDXL Lightning Image Adapter — Real image generation backend.

Provides:
- SDXLImageAdapter: SDXL Lightning (NF4 quantized) backend
- VRAM-aware initialization (3.5-4.5 GB target)
- Deterministic seeding for reproducible generation
- Image caching with content hash (avoids regeneration)
- Graceful fallback to stub if dependencies unavailable

Images are atmospheric only — never mechanical authority.
Does NOT write to AssetStore directly (caller orchestrates storage).

WO-022: Real Image Backend (SDXL Lightning)
Reference: Execution Plan Milestone 3
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

from aidm.schemas.immersion import ImageRequest, ImageResult

# Lazy imports — avoid import-time dependencies on diffusers/torch
if TYPE_CHECKING:
    from diffusers import StableDiffusionXLPipeline
    import torch


# =============================================================================
# DIMENSION PRESETS
# =============================================================================

# Image dimensions per kind (width, height)
DIMENSION_PRESETS: Dict[str, Tuple[int, int]] = {
    "portrait": (512, 512),    # Square, focused on face/character
    "scene": (768, 512),       # Landscape, action/encounter scenes
    "backdrop": (1024, 576),   # Wide, environmental backgrounds
}

# Default dimensions if kind not recognized
DEFAULT_DIMENSIONS = (512, 512)


# =============================================================================
# CACHE MANAGER
# =============================================================================

@dataclass
class CacheEntry:
    """Cached image entry with metadata."""
    content_hash: str
    path: str
    request_hash: str


class ImageCache:
    """Simple in-memory + disk cache for generated images.

    Uses content-addressable storage based on request hash.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the image cache.

        Args:
            cache_dir: Directory for cached images. Defaults to temp directory.
        """
        if cache_dir is None:
            cache_dir = Path(tempfile.gettempdir()) / "aidm_image_cache"
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._entries: Dict[str, CacheEntry] = {}

    @property
    def cache_dir(self) -> Path:
        """Return the cache directory path."""
        return self._cache_dir

    def compute_request_hash(self, request: ImageRequest) -> str:
        """Compute a deterministic hash for an image request.

        Args:
            request: The image request to hash

        Returns:
            SHA256 hash string (first 16 chars)
        """
        # Include all relevant fields in the hash
        hash_input = (
            f"{request.kind}|{request.semantic_key}|"
            f"{request.prompt_context}|{request.dimensions}"
        )
        full_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        return full_hash[:16]

    def compute_content_hash(self, image_bytes: bytes) -> str:
        """Compute SHA256 hash of image content.

        Args:
            image_bytes: Raw image bytes

        Returns:
            SHA256 hash string (first 16 chars)
        """
        full_hash = hashlib.sha256(image_bytes).hexdigest()
        return full_hash[:16]

    def get(self, request: ImageRequest) -> Optional[CacheEntry]:
        """Look up a cached image by request.

        Args:
            request: The image request

        Returns:
            CacheEntry if found and file exists, None otherwise
        """
        request_hash = self.compute_request_hash(request)
        entry = self._entries.get(request_hash)

        if entry is not None:
            # Verify file still exists
            if Path(entry.path).exists():
                return entry
            # File was deleted, remove stale entry
            del self._entries[request_hash]

        return None

    def put(
        self,
        request: ImageRequest,
        image_bytes: bytes,
        filename: str
    ) -> CacheEntry:
        """Store an image in the cache.

        Args:
            request: The original image request
            image_bytes: Raw image bytes
            filename: Filename for the cached image

        Returns:
            CacheEntry with path and hashes
        """
        request_hash = self.compute_request_hash(request)
        content_hash = self.compute_content_hash(image_bytes)

        # Write to cache directory
        cache_path = self._cache_dir / filename
        cache_path.write_bytes(image_bytes)

        entry = CacheEntry(
            content_hash=content_hash,
            path=str(cache_path),
            request_hash=request_hash,
        )
        self._entries[request_hash] = entry

        return entry

    def clear(self) -> int:
        """Clear all cached entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._entries)
        self._entries.clear()
        return count


# =============================================================================
# DEPENDENCY CHECKER
# =============================================================================

def check_sdxl_available() -> Tuple[bool, str]:
    """Check if SDXL dependencies are available.

    Returns:
        Tuple of (is_available, reason_if_not)
    """
    # Check for torch
    try:
        import torch
    except ImportError:
        return False, "torch not installed"

    # Check for CUDA
    if not torch.cuda.is_available():
        return False, "CUDA not available"

    # Check for diffusers
    try:
        import diffusers
    except ImportError:
        return False, "diffusers not installed"

    # Check for bitsandbytes (for NF4 quantization)
    try:
        import bitsandbytes
    except ImportError:
        return False, "bitsandbytes not installed (required for NF4)"

    # Check VRAM (need at least 3.5 GB free)
    try:
        device = torch.cuda.current_device()
        total_mem = torch.cuda.get_device_properties(device).total_memory
        # NF4 SDXL needs ~3.5-4.5 GB
        if total_mem < 4 * 1024 * 1024 * 1024:  # 4 GB minimum
            return False, f"Insufficient VRAM: {total_mem / 1e9:.1f} GB (need 4+ GB)"
    except Exception as e:
        return False, f"Failed to check VRAM: {e}"

    return True, ""


def get_vram_usage_gb() -> float:
    """Get current VRAM usage in GB.

    Returns:
        VRAM usage in GB, or 0.0 if unavailable
    """
    try:
        import torch
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated()
            return allocated / (1024 ** 3)
    except Exception:
        pass
    return 0.0


# =============================================================================
# SDXL IMAGE ADAPTER
# =============================================================================

class SDXLImageAdapter:
    """SDXL Lightning image generation adapter.

    Uses SDXL Lightning with NF4 quantization for VRAM efficiency.
    Supports deterministic generation via seed parameter.
    Caches generated images to avoid regeneration.

    VRAM Budget: 3.5-4.5 GB (NF4 quantized)
    """

    # Model configuration
    MODEL_ID = "stabilityai/sdxl-turbo"  # Fast variant, 4-step generation

    # Generation defaults
    DEFAULT_STEPS = 4
    DEFAULT_GUIDANCE_SCALE = 0.0  # SDXL Turbo uses guidance_scale=0

    # Style suffix for D&D fantasy aesthetic
    STYLE_SUFFIX = (
        ", fantasy art style, dungeons and dragons, detailed, "
        "atmospheric lighting, high quality"
    )

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        device: str = "cuda",
        enable_attention_slicing: bool = True,
    ):
        """Initialize the SDXL adapter.

        Args:
            cache_dir: Optional cache directory path
            device: Device to run inference on ("cuda" or "cpu")
            enable_attention_slicing: Enable memory-efficient attention
        """
        self._device = device
        self._enable_attention_slicing = enable_attention_slicing
        self._cache = ImageCache(cache_dir)
        self._pipeline: Optional[Any] = None  # Lazy loaded
        self._available: Optional[bool] = None
        self._availability_reason = ""

    @property
    def cache(self) -> ImageCache:
        """Return the image cache."""
        return self._cache

    def is_available(self) -> bool:
        """Check if SDXL generation is available.

        Returns:
            True if all dependencies are present and CUDA is available
        """
        if self._available is None:
            self._available, self._availability_reason = check_sdxl_available()
        return self._available

    def get_availability_reason(self) -> str:
        """Get the reason if not available.

        Returns:
            Empty string if available, reason string otherwise
        """
        if self._available is None:
            self.is_available()
        return self._availability_reason

    def _load_pipeline(self) -> bool:
        """Lazy-load the SDXL pipeline.

        Returns:
            True if pipeline loaded successfully
        """
        if self._pipeline is not None:
            return True

        if not self.is_available():
            return False

        try:
            import torch
            from diffusers import AutoPipelineForText2Image
            from transformers import BitsAndBytesConfig

            # NF4 quantization config for VRAM efficiency
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )

            # Load pipeline with quantization
            self._pipeline = AutoPipelineForText2Image.from_pretrained(
                self.MODEL_ID,
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True,
                quantization_config=quantization_config,
            )

            # Move to device
            self._pipeline = self._pipeline.to(self._device)

            # Enable memory optimizations
            if self._enable_attention_slicing:
                self._pipeline.enable_attention_slicing()

            # Enable VAE slicing for large images
            self._pipeline.enable_vae_slicing()

            return True

        except Exception as e:
            self._available = False
            self._availability_reason = f"Failed to load pipeline: {e}"
            return False

    def _build_prompt(self, request: ImageRequest) -> str:
        """Build the generation prompt from request.

        Args:
            request: Image request with context

        Returns:
            Full prompt string with style suffix
        """
        prompt = request.prompt_context.strip()

        # Add default context if empty
        if not prompt:
            kind_defaults = {
                "portrait": "A fantasy character portrait",
                "scene": "A fantasy adventure scene",
                "backdrop": "A fantasy landscape environment",
            }
            prompt = kind_defaults.get(request.kind, "A fantasy image")

        # Append style suffix
        return prompt + self.STYLE_SUFFIX

    def _get_dimensions(self, request: ImageRequest) -> Tuple[int, int]:
        """Get output dimensions for request.

        Uses preset dimensions for known kinds, falls back to request dimensions.

        Args:
            request: Image request

        Returns:
            (width, height) tuple
        """
        # Use preset if kind is recognized
        if request.kind in DIMENSION_PRESETS:
            return DIMENSION_PRESETS[request.kind]

        # Fall back to request dimensions
        if request.dimensions and len(request.dimensions) == 2:
            return (request.dimensions[0], request.dimensions[1])

        return DEFAULT_DIMENSIONS

    def _compute_seed(self, request: ImageRequest) -> int:
        """Compute a deterministic seed from the request.

        Uses request hash to ensure same request produces same image.

        Args:
            request: Image request

        Returns:
            Integer seed for generation
        """
        request_hash = self._cache.compute_request_hash(request)
        # Convert hex hash to integer seed
        return int(request_hash, 16) % (2**32)

    def generate(self, request: ImageRequest) -> ImageResult:
        """Generate an image from a request.

        Args:
            request: Image generation parameters

        Returns:
            ImageResult with status, path, and metadata
        """
        # Check cache first
        cached = self._cache.get(request)
        if cached is not None:
            return ImageResult(
                status="cached",
                asset_id=request.semantic_key,
                path=cached.path,
                content_hash=cached.content_hash,
            )

        # Check availability
        if not self.is_available():
            return ImageResult(
                status="error",
                asset_id="",
                path="",
                content_hash="",
                error_message=f"SDXL not available: {self._availability_reason}",
            )

        # Load pipeline (lazy)
        if not self._load_pipeline():
            return ImageResult(
                status="error",
                asset_id="",
                path="",
                content_hash="",
                error_message=f"Failed to load pipeline: {self._availability_reason}",
            )

        try:
            import torch

            # Build prompt and get dimensions
            prompt = self._build_prompt(request)
            width, height = self._get_dimensions(request)

            # Deterministic seed
            seed = self._compute_seed(request)
            generator = torch.Generator(device=self._device).manual_seed(seed)

            # Generate image
            output = self._pipeline(
                prompt=prompt,
                num_inference_steps=self.DEFAULT_STEPS,
                guidance_scale=self.DEFAULT_GUIDANCE_SCALE,
                generator=generator,
                width=width,
                height=height,
            )

            # Get the generated image
            image = output.images[0]

            # Save to bytes for caching
            import io
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()

            # Cache the result
            filename = f"{request.semantic_key.replace(':', '_')}_{seed}.png"
            entry = self._cache.put(request, image_bytes, filename)

            return ImageResult(
                status="generated",
                asset_id=request.semantic_key,
                path=entry.path,
                content_hash=entry.content_hash,
            )

        except Exception as e:
            return ImageResult(
                status="error",
                asset_id="",
                path="",
                content_hash="",
                error_message=f"Generation failed: {e}",
            )

    def get_vram_usage(self) -> float:
        """Get current VRAM usage in GB.

        Returns:
            VRAM usage in GB
        """
        return get_vram_usage_gb()

    def unload_pipeline(self) -> None:
        """Unload the pipeline to free VRAM."""
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None

            # Force garbage collection
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass


# =============================================================================
# FACTORY FUNCTION (for registration)
# =============================================================================

def create_sdxl_adapter(**kwargs: Any) -> SDXLImageAdapter:
    """Create an SDXL image adapter.

    Args:
        **kwargs: Passed to SDXLImageAdapter constructor

    Returns:
        SDXLImageAdapter instance
    """
    return SDXLImageAdapter(**kwargs)
