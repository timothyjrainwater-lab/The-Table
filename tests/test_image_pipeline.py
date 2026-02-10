"""Tests for M3 Image Pipeline.

Tests:
- StubImageAdapter returns placeholder results
- Protocol compliance
- Factory creates correct adapter
- Factory rejects unknown backend
- Placeholder results validate
"""

import pytest

from aidm.immersion.image_adapter import (
    ImageAdapter,
    StubImageAdapter,
    create_image_adapter,
)
from aidm.schemas.immersion import ImageRequest, ImageResult


# =============================================================================
# Stub Image Adapter Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestStubImageAdapter:
    """Tests for StubImageAdapter."""

    def test_returns_placeholder(self):
        """Should return placeholder ImageResult."""
        adapter = StubImageAdapter()
        request = ImageRequest(kind="scene", semantic_key="forest:clearing:v1")
        result = adapter.generate(request)
        assert isinstance(result, ImageResult)
        assert result.status == "placeholder"

    def test_placeholder_has_empty_fields(self):
        """Placeholder should have empty asset_id, path, content_hash."""
        adapter = StubImageAdapter()
        request = ImageRequest(kind="portrait", semantic_key="npc:v1")
        result = adapter.generate(request)
        assert result.asset_id == ""
        assert result.path == ""
        assert result.content_hash == ""

    def test_is_available(self):
        """Stub should always be available."""
        adapter = StubImageAdapter()
        assert adapter.is_available() is True

    def test_satisfies_protocol(self):
        """StubImageAdapter should satisfy ImageAdapter protocol."""
        adapter = StubImageAdapter()
        assert isinstance(adapter, ImageAdapter)

    def test_result_validates(self):
        """Placeholder result should pass validation."""
        adapter = StubImageAdapter()
        request = ImageRequest(kind="scene", semantic_key="k")
        result = adapter.generate(request)
        assert result.validate() == []

    def test_different_requests_same_status(self):
        """All requests should produce placeholder status."""
        adapter = StubImageAdapter()
        for kind in ("portrait", "scene", "backdrop"):
            request = ImageRequest(kind=kind, semantic_key=f"test:{kind}")
            result = adapter.generate(request)
            assert result.status == "placeholder"

    def test_does_not_modify_request(self):
        """Generate should not modify the request object."""
        adapter = StubImageAdapter()
        request = ImageRequest(
            kind="scene",
            semantic_key="forest:v1",
            prompt_context="A misty forest",
            dimensions=(256, 256),
        )
        original_dict = request.to_dict()
        adapter.generate(request)
        assert request.to_dict() == original_dict


# =============================================================================
# Factory Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestImageFactory:
    """Tests for create_image_adapter factory."""

    def test_factory_creates_stub(self):
        """Factory should create StubImageAdapter for 'stub' backend."""
        adapter = create_image_adapter("stub")
        assert isinstance(adapter, StubImageAdapter)

    def test_factory_default_is_stub(self):
        """Factory default should be 'stub'."""
        adapter = create_image_adapter()
        assert isinstance(adapter, StubImageAdapter)

    def test_factory_unknown_backend_raises(self):
        """Factory should raise ValueError for unknown backend."""
        with pytest.raises(ValueError, match="Unknown image backend"):
            create_image_adapter("dalle")

    def test_factory_produces_working_adapter(self):
        """Factory-created adapter should produce valid results."""
        adapter = create_image_adapter()
        request = ImageRequest(kind="scene", semantic_key="test:v1")
        result = adapter.generate(request)
        assert result.status == "placeholder"
        assert result.validate() == []
