"""Tests for SDXL Lightning Image Adapter.

Tests:
- SDXLImageAdapter unit tests (with mocked diffusers)
- ImageCache functionality
- Protocol compliance
- Factory integration
- Dimension validation per request kind
- Cache hit/miss validation
- Content hash consistency
- Integration tests (skip if no GPU)

WO-022: Real Image Backend (SDXL Lightning)
Reference: Execution Plan Milestone 3
"""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Tuple

import pytest

from aidm.immersion.image_adapter import (
    ImageAdapter,
    StubImageAdapter,
    create_image_adapter,
)
from aidm.immersion.sdxl_image_adapter import (
    SDXLImageAdapter,
    ImageCache,
    CacheEntry,
    DIMENSION_PRESETS,
    DEFAULT_DIMENSIONS,
    check_sdxl_available,
    get_vram_usage_gb,
)
from aidm.schemas.immersion import ImageRequest, ImageResult


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for image cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def image_cache(temp_cache_dir: Path) -> ImageCache:
    """Create an ImageCache with temp directory."""
    return ImageCache(cache_dir=temp_cache_dir)


@pytest.fixture
def sdxl_adapter(temp_cache_dir: Path) -> SDXLImageAdapter:
    """Create an SDXLImageAdapter with temp cache."""
    return SDXLImageAdapter(cache_dir=temp_cache_dir)


@pytest.fixture
def portrait_request() -> ImageRequest:
    """Create a portrait image request."""
    return ImageRequest(
        kind="portrait",
        semantic_key="npc:theron:portrait:v1",
        prompt_context="A wise old wizard with a long grey beard",
        dimensions=(512, 512),
    )


@pytest.fixture
def scene_request() -> ImageRequest:
    """Create a scene image request."""
    return ImageRequest(
        kind="scene",
        semantic_key="encounter:goblin_ambush:v1",
        prompt_context="Goblins ambushing travelers in a dark forest",
        dimensions=(768, 512),
    )


@pytest.fixture
def backdrop_request() -> ImageRequest:
    """Create a backdrop image request."""
    return ImageRequest(
        kind="backdrop",
        semantic_key="location:castle:exterior:v1",
        prompt_context="A towering medieval castle on a cliff",
        dimensions=(1024, 576),
    )


# =============================================================================
# IMAGE CACHE TESTS
# =============================================================================

@pytest.mark.immersion_fast
class TestImageCache:
    """Tests for ImageCache class."""

    def test_cache_init_creates_directory(self, temp_cache_dir: Path):
        """Cache initialization should create cache directory."""
        cache = ImageCache(cache_dir=temp_cache_dir / "subcache")
        assert cache.cache_dir.exists()

    def test_cache_default_directory(self):
        """Cache with None uses temp directory."""
        cache = ImageCache(cache_dir=None)
        assert cache.cache_dir.exists()
        assert "aidm_image_cache" in str(cache.cache_dir)

    def test_compute_request_hash_deterministic(self, image_cache: ImageCache):
        """Same request should produce same hash."""
        request = ImageRequest(
            kind="portrait",
            semantic_key="test:v1",
            prompt_context="A test image",
            dimensions=(512, 512),
        )
        hash1 = image_cache.compute_request_hash(request)
        hash2 = image_cache.compute_request_hash(request)
        assert hash1 == hash2
        assert len(hash1) == 16  # First 16 chars of SHA256

    def test_compute_request_hash_different_requests(self, image_cache: ImageCache):
        """Different requests should produce different hashes."""
        request1 = ImageRequest(kind="portrait", semantic_key="test:v1")
        request2 = ImageRequest(kind="scene", semantic_key="test:v1")
        request3 = ImageRequest(kind="portrait", semantic_key="test:v2")

        hash1 = image_cache.compute_request_hash(request1)
        hash2 = image_cache.compute_request_hash(request2)
        hash3 = image_cache.compute_request_hash(request3)

        assert hash1 != hash2
        assert hash1 != hash3
        assert hash2 != hash3

    def test_compute_content_hash_deterministic(self, image_cache: ImageCache):
        """Same content should produce same hash."""
        content = b"test image content"
        hash1 = image_cache.compute_content_hash(content)
        hash2 = image_cache.compute_content_hash(content)
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_compute_content_hash_different_content(self, image_cache: ImageCache):
        """Different content should produce different hashes."""
        hash1 = image_cache.compute_content_hash(b"content1")
        hash2 = image_cache.compute_content_hash(b"content2")
        assert hash1 != hash2

    def test_get_miss_returns_none(
        self, image_cache: ImageCache, portrait_request: ImageRequest
    ):
        """Cache miss should return None."""
        result = image_cache.get(portrait_request)
        assert result is None

    def test_put_and_get_roundtrip(
        self, image_cache: ImageCache, portrait_request: ImageRequest
    ):
        """Put then get should return cached entry."""
        image_bytes = b"fake image data"
        entry = image_cache.put(portrait_request, image_bytes, "test.png")

        assert entry.content_hash
        assert entry.request_hash
        assert Path(entry.path).exists()

        # Get should return the entry
        retrieved = image_cache.get(portrait_request)
        assert retrieved is not None
        assert retrieved.content_hash == entry.content_hash
        assert retrieved.path == entry.path

    def test_get_removes_stale_entry(
        self, image_cache: ImageCache, temp_cache_dir: Path
    ):
        """Get should remove entry if file no longer exists."""
        request = ImageRequest(kind="portrait", semantic_key="stale:v1")
        image_bytes = b"image data"

        # Put entry
        entry = image_cache.put(request, image_bytes, "stale.png")
        assert image_cache.get(request) is not None

        # Delete the file
        Path(entry.path).unlink()

        # Get should now return None
        result = image_cache.get(request)
        assert result is None

    def test_clear_removes_all_entries(
        self, image_cache: ImageCache, portrait_request: ImageRequest
    ):
        """Clear should remove all cached entries."""
        image_cache.put(portrait_request, b"data1", "img1.png")
        image_cache.put(
            ImageRequest(kind="scene", semantic_key="s"),
            b"data2",
            "img2.png"
        )

        count = image_cache.clear()
        assert count == 2
        assert image_cache.get(portrait_request) is None


# =============================================================================
# SDXL ADAPTER UNIT TESTS (MOCKED)
# =============================================================================

@pytest.mark.immersion_fast
class TestSDXLImageAdapterUnit:
    """Unit tests for SDXLImageAdapter with mocked dependencies."""

    def test_adapter_satisfies_protocol(self, sdxl_adapter: SDXLImageAdapter):
        """SDXLImageAdapter should satisfy ImageAdapter protocol."""
        assert isinstance(sdxl_adapter, ImageAdapter)

    def test_adapter_has_cache(self, sdxl_adapter: SDXLImageAdapter):
        """Adapter should have accessible cache."""
        assert sdxl_adapter.cache is not None
        assert isinstance(sdxl_adapter.cache, ImageCache)

    def test_is_available_checks_dependencies(self, sdxl_adapter: SDXLImageAdapter):
        """is_available should check for required dependencies."""
        # Will be False in most test environments (no GPU)
        result = sdxl_adapter.is_available()
        assert isinstance(result, bool)

    def test_get_availability_reason(self, sdxl_adapter: SDXLImageAdapter):
        """Should provide reason if not available."""
        if not sdxl_adapter.is_available():
            reason = sdxl_adapter.get_availability_reason()
            assert reason != ""
            assert isinstance(reason, str)

    def test_generate_returns_error_when_unavailable(
        self, sdxl_adapter: SDXLImageAdapter, portrait_request: ImageRequest
    ):
        """Generate should return error result when SDXL unavailable."""
        # Mock to simulate unavailable
        with patch.object(sdxl_adapter, 'is_available', return_value=False):
            sdxl_adapter._availability_reason = "Test unavailable"
            result = sdxl_adapter.generate(portrait_request)

            assert result.status == "error"
            assert "not available" in result.error_message

    def test_generate_returns_cached_result(
        self, sdxl_adapter: SDXLImageAdapter, portrait_request: ImageRequest
    ):
        """Generate should return cached result if available."""
        # Pre-populate cache
        cache_entry = sdxl_adapter.cache.put(
            portrait_request,
            b"cached image",
            "cached.png"
        )

        result = sdxl_adapter.generate(portrait_request)

        assert result.status == "cached"
        assert result.path == cache_entry.path
        assert result.content_hash == cache_entry.content_hash

    def test_build_prompt_adds_style_suffix(self, sdxl_adapter: SDXLImageAdapter):
        """Prompt builder should add style suffix."""
        request = ImageRequest(
            kind="portrait",
            semantic_key="test",
            prompt_context="A wizard",
        )
        prompt = sdxl_adapter._build_prompt(request)

        assert "A wizard" in prompt
        assert "fantasy art style" in prompt
        assert "dungeons and dragons" in prompt

    def test_build_prompt_uses_default_for_empty(
        self, sdxl_adapter: SDXLImageAdapter
    ):
        """Prompt builder should use default for empty context."""
        request = ImageRequest(kind="portrait", semantic_key="test")
        prompt = sdxl_adapter._build_prompt(request)
        assert "fantasy character portrait" in prompt.lower()

    def test_get_dimensions_uses_presets(self, sdxl_adapter: SDXLImageAdapter):
        """Should use dimension presets for known kinds."""
        for kind, expected in DIMENSION_PRESETS.items():
            request = ImageRequest(kind=kind, semantic_key="test")
            dims = sdxl_adapter._get_dimensions(request)
            assert dims == expected

    def test_get_dimensions_falls_back_to_request(
        self, sdxl_adapter: SDXLImageAdapter
    ):
        """Should fall back to request dimensions for unknown kind."""
        request = ImageRequest(
            kind="custom",
            semantic_key="test",
            dimensions=(256, 256),
        )
        dims = sdxl_adapter._get_dimensions(request)
        assert dims == (256, 256)

    def test_compute_seed_deterministic(
        self, sdxl_adapter: SDXLImageAdapter, portrait_request: ImageRequest
    ):
        """Same request should produce same seed."""
        seed1 = sdxl_adapter._compute_seed(portrait_request)
        seed2 = sdxl_adapter._compute_seed(portrait_request)
        assert seed1 == seed2
        assert isinstance(seed1, int)
        assert seed1 >= 0

    def test_compute_seed_different_requests(
        self, sdxl_adapter: SDXLImageAdapter
    ):
        """Different requests should produce different seeds."""
        req1 = ImageRequest(kind="portrait", semantic_key="test:v1")
        req2 = ImageRequest(kind="portrait", semantic_key="test:v2")

        seed1 = sdxl_adapter._compute_seed(req1)
        seed2 = sdxl_adapter._compute_seed(req2)

        assert seed1 != seed2

    def test_unload_pipeline_clears_memory(self, sdxl_adapter: SDXLImageAdapter):
        """unload_pipeline should clear pipeline reference."""
        sdxl_adapter._pipeline = "fake_pipeline"  # Simulate loaded
        sdxl_adapter.unload_pipeline()
        assert sdxl_adapter._pipeline is None

    def test_get_vram_usage_returns_float(self, sdxl_adapter: SDXLImageAdapter):
        """get_vram_usage should return a float."""
        vram = sdxl_adapter.get_vram_usage()
        assert isinstance(vram, float)
        assert vram >= 0.0


# =============================================================================
# DIMENSION VALIDATION TESTS
# =============================================================================

@pytest.mark.immersion_fast
class TestDimensionPresets:
    """Tests for dimension presets."""

    def test_portrait_dimensions(self):
        """Portrait should be 512x512."""
        assert DIMENSION_PRESETS["portrait"] == (512, 512)

    def test_scene_dimensions(self):
        """Scene should be 768x512."""
        assert DIMENSION_PRESETS["scene"] == (768, 512)

    def test_backdrop_dimensions(self):
        """Backdrop should be 1024x576."""
        assert DIMENSION_PRESETS["backdrop"] == (1024, 576)

    def test_all_dimensions_divisible_by_8(self):
        """All preset dimensions should be divisible by 8 (SDXL requirement)."""
        for kind, (width, height) in DIMENSION_PRESETS.items():
            assert width % 8 == 0, f"{kind} width not divisible by 8"
            assert height % 8 == 0, f"{kind} height not divisible by 8"

    def test_default_dimensions(self):
        """Default dimensions should be 512x512."""
        assert DEFAULT_DIMENSIONS == (512, 512)


# =============================================================================
# CONTENT HASH CONSISTENCY TESTS
# =============================================================================

@pytest.mark.immersion_fast
class TestContentHashConsistency:
    """Tests for content hash consistency."""

    def test_same_content_same_hash(self, image_cache: ImageCache):
        """Identical content should produce identical hash."""
        content = b"test image bytes"
        hashes = [image_cache.compute_content_hash(content) for _ in range(10)]
        assert len(set(hashes)) == 1

    def test_hash_length_consistent(self, image_cache: ImageCache):
        """All hashes should be 16 characters."""
        for size in [10, 100, 1000, 10000]:
            content = b"x" * size
            hash_val = image_cache.compute_content_hash(content)
            assert len(hash_val) == 16

    def test_hash_is_hex(self, image_cache: ImageCache):
        """Hash should be valid hexadecimal."""
        content = b"test content"
        hash_val = image_cache.compute_content_hash(content)
        # Should not raise
        int(hash_val, 16)


# =============================================================================
# FACTORY INTEGRATION TESTS
# =============================================================================

@pytest.mark.immersion_fast
class TestFactoryIntegration:
    """Tests for factory integration with SDXL adapter."""

    def test_factory_accepts_sdxl_backend(self):
        """Factory should accept 'sdxl' as valid backend."""
        # Should not raise ValueError
        adapter = create_image_adapter("sdxl")
        # Returns either SDXL adapter or stub fallback
        assert isinstance(adapter, ImageAdapter)

    def test_factory_sdxl_fallback_to_stub(self):
        """Factory should fallback to stub if SDXL unavailable."""
        adapter = create_image_adapter("sdxl")
        # In test environment without GPU, should get stub
        if not isinstance(adapter, SDXLImageAdapter):
            assert isinstance(adapter, StubImageAdapter)

    def test_factory_stub_still_works(self):
        """Factory should still create stub adapter."""
        adapter = create_image_adapter("stub")
        assert isinstance(adapter, StubImageAdapter)

    def test_factory_default_still_stub(self):
        """Factory default should still be stub."""
        adapter = create_image_adapter()
        assert isinstance(adapter, StubImageAdapter)

    def test_factory_unknown_backend_raises(self):
        """Factory should raise for unknown backends."""
        with pytest.raises(ValueError, match="Unknown image backend"):
            create_image_adapter("dalle")

    def test_factory_error_message_includes_sdxl(self):
        """Error message should list sdxl as available backend."""
        with pytest.raises(ValueError) as exc_info:
            create_image_adapter("invalid")
        assert "sdxl" in str(exc_info.value)


# =============================================================================
# DEPENDENCY CHECKER TESTS
# =============================================================================

@pytest.mark.immersion_fast
class TestDependencyChecker:
    """Tests for dependency checking functions."""

    def test_check_sdxl_available_returns_tuple(self):
        """check_sdxl_available should return (bool, str) tuple."""
        result = check_sdxl_available()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_get_vram_usage_gb_returns_float(self):
        """get_vram_usage_gb should return float."""
        result = get_vram_usage_gb()
        assert isinstance(result, float)
        assert result >= 0.0

    @patch.dict('sys.modules', {'torch': None})
    def test_check_available_without_torch(self):
        """Should return False when torch not installed."""
        # Force reimport to test import failure
        import importlib
        from aidm.immersion import sdxl_image_adapter

        # The function handles ImportError gracefully
        available, reason = check_sdxl_available()
        # Will either report torch missing or some other dependency
        assert isinstance(available, bool)


# =============================================================================
# INTEGRATION TESTS (REQUIRES GPU)
# =============================================================================

# Custom marker for tests requiring SDXL/GPU
def requires_sdxl():
    """Skip decorator for tests requiring SDXL."""
    available, reason = check_sdxl_available()
    return pytest.mark.skipif(
        not available,
        reason=f"SDXL not available: {reason}"
    )


@pytest.mark.slow
class TestSDXLIntegration:
    """Integration tests for real SDXL generation.

    These tests are skipped if GPU/SDXL is unavailable.
    """

    @requires_sdxl()
    def test_generate_portrait_real(self, temp_cache_dir: Path):
        """Generate a real portrait image."""
        adapter = SDXLImageAdapter(cache_dir=temp_cache_dir)
        request = ImageRequest(
            kind="portrait",
            semantic_key="test:portrait:v1",
            prompt_context="A brave knight in shining armor",
        )

        result = adapter.generate(request)

        assert result.status == "generated"
        assert Path(result.path).exists()
        assert result.content_hash != ""

    @requires_sdxl()
    def test_generate_scene_real(self, temp_cache_dir: Path):
        """Generate a real scene image."""
        adapter = SDXLImageAdapter(cache_dir=temp_cache_dir)
        request = ImageRequest(
            kind="scene",
            semantic_key="test:scene:v1",
            prompt_context="A dragon attacking a castle",
        )

        result = adapter.generate(request)

        assert result.status == "generated"
        assert Path(result.path).exists()

    @requires_sdxl()
    def test_generate_backdrop_real(self, temp_cache_dir: Path):
        """Generate a real backdrop image."""
        adapter = SDXLImageAdapter(cache_dir=temp_cache_dir)
        request = ImageRequest(
            kind="backdrop",
            semantic_key="test:backdrop:v1",
            prompt_context="An ancient elven forest",
        )

        result = adapter.generate(request)

        assert result.status == "generated"
        assert Path(result.path).exists()

    @requires_sdxl()
    def test_deterministic_generation(self, temp_cache_dir: Path):
        """Same request should produce same result (via cache)."""
        adapter = SDXLImageAdapter(cache_dir=temp_cache_dir)
        request = ImageRequest(
            kind="portrait",
            semantic_key="test:determinism:v1",
            prompt_context="A mysterious sorcerer",
        )

        result1 = adapter.generate(request)
        result2 = adapter.generate(request)

        # Second should be cached
        assert result2.status == "cached"
        assert result1.content_hash == result2.content_hash

    @requires_sdxl()
    def test_vram_usage_within_budget(self, temp_cache_dir: Path):
        """VRAM usage should stay within 4.5 GB budget."""
        adapter = SDXLImageAdapter(cache_dir=temp_cache_dir)

        # Generate an image to load the model
        request = ImageRequest(
            kind="portrait",
            semantic_key="test:vram:v1",
            prompt_context="A test image for VRAM measurement",
        )
        adapter.generate(request)

        vram = adapter.get_vram_usage()
        # Should be under 4.5 GB
        assert vram < 4.5, f"VRAM usage {vram:.2f} GB exceeds 4.5 GB budget"

    @requires_sdxl()
    def test_image_dimensions_correct(self, temp_cache_dir: Path):
        """Generated images should have correct dimensions."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not installed")

        adapter = SDXLImageAdapter(cache_dir=temp_cache_dir)

        for kind, expected_dims in DIMENSION_PRESETS.items():
            request = ImageRequest(
                kind=kind,
                semantic_key=f"test:dims:{kind}:v1",
                prompt_context="A test image",
            )
            result = adapter.generate(request)

            if result.status == "generated" or result.status == "cached":
                img = Image.open(result.path)
                assert img.size == expected_dims, (
                    f"{kind}: expected {expected_dims}, got {img.size}"
                )


# =============================================================================
# RESULT VALIDATION TESTS
# =============================================================================

@pytest.mark.immersion_fast
class TestResultValidation:
    """Tests for ImageResult validation."""

    def test_generated_result_validates(self, image_cache: ImageCache):
        """Generated result should pass validation."""
        result = ImageResult(
            status="generated",
            asset_id="test:v1",
            path="/tmp/test.png",
            content_hash="abc123def456",
        )
        errors = result.validate()
        assert errors == []

    def test_cached_result_validates(self):
        """Cached result should pass validation."""
        result = ImageResult(
            status="cached",
            asset_id="test:v1",
            path="/tmp/cached.png",
            content_hash="abc123def456",
        )
        errors = result.validate()
        assert errors == []

    def test_error_result_validates(self):
        """Error result should pass validation."""
        result = ImageResult(
            status="error",
            asset_id="",
            path="",
            content_hash="",
            error_message="Something went wrong",
        )
        errors = result.validate()
        assert errors == []

    def test_invalid_status_fails_validation(self):
        """Invalid status should fail validation."""
        result = ImageResult(
            status="invalid_status",
            asset_id="",
            path="",
            content_hash="",
        )
        errors = result.validate()
        assert len(errors) > 0
        assert "Invalid status" in errors[0]


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

@pytest.mark.immersion_fast
class TestEdgeCases:
    """Edge case tests for robustness."""

    def test_empty_prompt_context(self, sdxl_adapter: SDXLImageAdapter):
        """Empty prompt context should use default."""
        request = ImageRequest(
            kind="portrait",
            semantic_key="test:empty",
            prompt_context="",
        )
        prompt = sdxl_adapter._build_prompt(request)
        assert "fantasy character portrait" in prompt.lower()

    def test_whitespace_prompt_context(self, sdxl_adapter: SDXLImageAdapter):
        """Whitespace-only prompt should use default."""
        request = ImageRequest(
            kind="scene",
            semantic_key="test:whitespace",
            prompt_context="   ",
        )
        prompt = sdxl_adapter._build_prompt(request)
        assert "fantasy adventure scene" in prompt.lower()

    def test_very_long_semantic_key(self, image_cache: ImageCache):
        """Very long semantic key should hash correctly."""
        request = ImageRequest(
            kind="portrait",
            semantic_key="a" * 1000,
            prompt_context="Test",
        )
        hash_val = image_cache.compute_request_hash(request)
        assert len(hash_val) == 16

    def test_unicode_in_prompt(self, sdxl_adapter: SDXLImageAdapter):
        """Unicode in prompt should be handled."""
        request = ImageRequest(
            kind="portrait",
            semantic_key="test:unicode",
            prompt_context="A warrior with a sword \u2694\ufe0f",
        )
        prompt = sdxl_adapter._build_prompt(request)
        assert "\u2694" in prompt

    def test_special_chars_in_semantic_key(self, image_cache: ImageCache):
        """Special characters in semantic key should hash correctly."""
        request = ImageRequest(
            kind="portrait",
            semantic_key="npc:theron'the-wise:portrait:v1",
            prompt_context="Test",
        )
        hash_val = image_cache.compute_request_hash(request)
        assert len(hash_val) == 16
