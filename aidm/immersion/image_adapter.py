"""M3 Image Adapter — Image generation with pluggable backends.

Provides:
- ImageAdapter Protocol: generate(request) -> ImageResult
- StubImageAdapter: Returns placeholder results for all requests
- create_image_adapter(backend) factory with registry

Images are atmospheric only — never mechanical authority.
Does NOT write to AssetStore directly (caller orchestrates storage).
"""

from typing import Dict, List, Optional, Protocol, runtime_checkable

from aidm.schemas.immersion import ImageRequest, ImageResult


@runtime_checkable
class ImageAdapter(Protocol):
    """Protocol for image generation adapters."""

    def generate(self, request: ImageRequest) -> ImageResult:
        """Generate an image from a request.

        Args:
            request: Image generation parameters

        Returns:
            ImageResult with status, path, and metadata
        """
        ...

    def is_available(self) -> bool:
        """Check if the image generation backend is available."""
        ...


class StubImageAdapter:
    """Stub image adapter that returns placeholder results.

    Used as default when no real image generation backend is installed.
    Returns ImageResult(status="placeholder") for all requests.
    """

    def generate(self, request: ImageRequest) -> ImageResult:
        """Return a placeholder result.

        Args:
            request: Image request (used only for semantic_key)

        Returns:
            Placeholder ImageResult
        """
        return ImageResult(
            status="placeholder",
            asset_id="",
            path="",
            content_hash="",
        )

    def is_available(self) -> bool:
        """Stub is always available."""
        return True


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_IMAGE_REGISTRY: Dict[str, type] = {
    "stub": StubImageAdapter,
}


def create_image_adapter(backend: str = "stub") -> ImageAdapter:
    """Create an image adapter by backend name.

    Args:
        backend: Backend identifier (e.g., 'stub')

    Returns:
        ImageAdapter instance

    Raises:
        ValueError: If backend is unknown
    """
    if backend not in _IMAGE_REGISTRY:
        raise ValueError(
            f"Unknown image backend: '{backend}'. "
            f"Available: {list(_IMAGE_REGISTRY.keys())}"
        )
    return _IMAGE_REGISTRY[backend]()
