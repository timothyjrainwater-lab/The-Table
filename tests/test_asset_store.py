"""Tests for M2 Asset Store.

Tests:
- Put/get asset roundtrip
- Deterministic asset ID generation
- Shared cache resolution
- Integrity verification
- Index save/load persistence
- All operations use tmp_path fixture
"""

import hashlib
import json
import pytest
from pathlib import Path

from aidm.core.asset_store import AssetStore, AssetStoreError
from aidm.schemas.campaign import AssetRecord, compute_asset_id


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def asset_env(tmp_path):
    """Create a campaign directory with asset store."""
    campaign_dir = tmp_path / "campaign_test"
    campaign_dir.mkdir()
    (campaign_dir / "assets").mkdir()
    store = AssetStore(campaign_dir)
    return store, campaign_dir


@pytest.fixture
def cache_env(tmp_path):
    """Create campaign dir + shared cache with a cached asset."""
    campaign_dir = tmp_path / "campaign_test"
    campaign_dir.mkdir()
    (campaign_dir / "assets").mkdir()

    cache_dir = tmp_path / "shared_cache"
    cache_dir.mkdir()

    # Pre-populate cache with a scene asset
    scene_dir = cache_dir / "scene"
    scene_dir.mkdir()
    cached_file = scene_dir / "generic_tavern_interior_v1"
    cached_file.write_bytes(b"tavern scene placeholder content")

    store = AssetStore(campaign_dir, shared_cache_dir=cache_dir)
    return store, campaign_dir, cache_dir


# =============================================================================
# Put/Get Tests
# =============================================================================

class TestPutGet:
    """Tests for put/get asset lifecycle."""

    def test_put_and_get(self, asset_env):
        """Should store and retrieve asset by ID."""
        store, campaign_dir = asset_env

        record = AssetRecord(
            asset_id="test_asset_001",
            kind="SCENE",
            semantic_key="tavern:interior:v1",
        )
        content = b"scene data here"

        result = store.put(record, content)

        assert result.content_hash == hashlib.sha256(content).hexdigest()

        retrieved = store.get("test_asset_001")
        assert retrieved is not None
        assert retrieved.asset_id == "test_asset_001"
        assert retrieved.content_hash == result.content_hash

    def test_put_writes_file(self, asset_env):
        """Put should write actual file to disk."""
        store, campaign_dir = asset_env

        record = AssetRecord(
            asset_id="file_test",
            kind="PORTRAIT",
            semantic_key="npc:theron:v1",
            path="assets/theron_portrait.png",
        )
        content = b"\x89PNG fake portrait data"

        store.put(record, content)

        file_path = campaign_dir / "assets" / "theron_portrait.png"
        assert file_path.is_file()
        assert file_path.read_bytes() == content

    def test_put_auto_generates_path(self, asset_env):
        """Put should generate path if not specified."""
        store, campaign_dir = asset_env

        record = AssetRecord(
            asset_id="auto_path_test",
            kind="MAP",
            semantic_key="dungeon:level1:v1",
        )
        content = b"map data"

        result = store.put(record, content)

        assert result.path != ""
        assert "auto_path_test" in result.path

    def test_get_nonexistent(self, asset_env):
        """Should return None for unknown asset ID."""
        store, _ = asset_env

        assert store.get("nonexistent") is None

    def test_get_content(self, asset_env):
        """Should read file content by asset ID."""
        store, _ = asset_env

        record = AssetRecord(
            asset_id="content_test",
            kind="HANDOUT",
            semantic_key="quest:notice:v1",
        )
        content = b"You are invited to the king's court."

        store.put(record, content)

        retrieved_content = store.get_content("content_test")
        assert retrieved_content == content

    def test_get_content_nonexistent(self, asset_env):
        """Should return None for unknown asset content."""
        store, _ = asset_env

        assert store.get_content("nonexistent") is None

    def test_put_computes_hash(self, asset_env):
        """Content hash should be SHA256 of content."""
        store, _ = asset_env

        record = AssetRecord(
            asset_id="hash_test",
            kind="SCENE",
            semantic_key="forest:clearing:v1",
        )
        content = b"the clearing is peaceful"

        result = store.put(record, content)

        expected_hash = hashlib.sha256(content).hexdigest()
        assert result.content_hash == expected_hash


# =============================================================================
# Shared Cache Tests
# =============================================================================

class TestSharedCache:
    """Tests for shared cache resolution."""

    def test_resolve_from_cache(self, cache_env):
        """Should find and import from shared cache."""
        store, campaign_dir, _ = cache_env

        record = store.resolve(
            semantic_key="generic:tavern:interior:v1",
            kind="SCENE",
            campaign_id="campaign_123",
        )

        assert record.provenance == "SHARED_CACHE"
        assert record.content_hash != ""

        # File should be copied to campaign assets
        file_path = campaign_dir / record.path
        assert file_path.is_file()

    def test_resolve_creates_placeholder(self, asset_env):
        """Should create placeholder when not in cache."""
        store, campaign_dir = asset_env

        record = store.resolve(
            semantic_key="unique:scene:v1",
            kind="SCENE",
            campaign_id="campaign_123",
        )

        assert record.provenance == "GENERATED"
        assert record.regen_policy == "REGEN_ON_MISS"
        assert record.content_hash == ""  # Placeholder

        # Placeholder file should exist
        file_path = campaign_dir / record.path
        assert file_path.is_file()

    def test_resolve_deterministic_id(self, asset_env):
        """Resolved asset should have deterministic ID."""
        store, _ = asset_env

        record = store.resolve(
            semantic_key="tavern:interior:v1",
            kind="SCENE",
            campaign_id="campaign_123",
        )

        expected_id = compute_asset_id("campaign_123", "SCENE", "tavern:interior:v1")
        assert record.asset_id == expected_id

    def test_resolve_uses_local_first(self, cache_env):
        """Should return local asset if already indexed."""
        store, _, _ = cache_env

        # First resolve creates from cache
        first = store.resolve(
            semantic_key="generic:tavern:interior:v1",
            kind="SCENE",
            campaign_id="campaign_123",
        )

        # Second resolve should return same record from index
        second = store.resolve(
            semantic_key="generic:tavern:interior:v1",
            kind="SCENE",
            campaign_id="campaign_123",
        )

        assert first.asset_id == second.asset_id
        assert first.content_hash == second.content_hash

    def test_resolve_without_cache(self, asset_env):
        """Should create placeholder when no shared cache configured."""
        store, _ = asset_env

        record = store.resolve(
            semantic_key="some:asset:v1",
            kind="PORTRAIT",
            campaign_id="campaign_123",
            use_shared_cache=True,  # No cache configured
        )

        assert record.provenance == "GENERATED"
        assert record.regen_policy == "REGEN_ON_MISS"

    def test_resolve_cache_disabled(self, cache_env):
        """Should skip cache when use_shared_cache=False."""
        store, _, _ = cache_env

        record = store.resolve(
            semantic_key="generic:tavern:interior:v1",
            kind="SCENE",
            campaign_id="campaign_123",
            use_shared_cache=False,
        )

        # Should be a placeholder, not from cache
        assert record.provenance == "GENERATED"


# =============================================================================
# Listing Tests
# =============================================================================

class TestAssetListing:
    """Tests for list_assets."""

    def test_list_empty(self, asset_env):
        """Should return empty list for new store."""
        store, _ = asset_env

        assert store.list_assets() == []

    def test_list_multiple(self, asset_env):
        """Should list all stored assets."""
        store, _ = asset_env

        for i in range(3):
            record = AssetRecord(
                asset_id=f"asset_{i:03d}",
                kind="SCENE",
                semantic_key=f"scene:{i}:v1",
            )
            store.put(record, f"content_{i}".encode())

        assets = store.list_assets()
        assert len(assets) == 3

    def test_list_sorted(self, asset_env):
        """Assets should be sorted by asset_id."""
        store, _ = asset_env

        for aid in ["zzz", "aaa", "mmm"]:
            record = AssetRecord(
                asset_id=aid,
                kind="SCENE",
                semantic_key=f"scene:{aid}:v1",
            )
            store.put(record, b"data")

        assets = store.list_assets()
        ids = [a.asset_id for a in assets]
        assert ids == sorted(ids)


# =============================================================================
# Integrity Verification Tests
# =============================================================================

class TestIntegrity:
    """Tests for verify_integrity."""

    def test_integrity_valid(self, asset_env):
        """Should pass when all assets are valid."""
        store, _ = asset_env

        record = AssetRecord(
            asset_id="valid_asset",
            kind="SCENE",
            semantic_key="scene:valid:v1",
        )
        store.put(record, b"valid content")

        issues = store.verify_integrity()
        assert issues == []

    def test_integrity_missing_file(self, asset_env):
        """Should detect missing files."""
        store, campaign_dir = asset_env

        record = AssetRecord(
            asset_id="missing_file",
            kind="SCENE",
            semantic_key="scene:missing:v1",
        )
        store.put(record, b"content")

        # Delete the file
        file_path = campaign_dir / record.path
        file_path.unlink()

        issues = store.verify_integrity()
        assert len(issues) == 1
        assert "Missing file" in issues[0]

    def test_integrity_hash_mismatch(self, asset_env):
        """Should detect corrupted files (hash mismatch)."""
        store, campaign_dir = asset_env

        record = AssetRecord(
            asset_id="corrupt_asset",
            kind="SCENE",
            semantic_key="scene:corrupt:v1",
        )
        store.put(record, b"original content")

        # Corrupt the file
        file_path = campaign_dir / record.path
        file_path.write_bytes(b"tampered content")

        issues = store.verify_integrity()
        assert len(issues) == 1
        assert "Hash mismatch" in issues[0]

    def test_integrity_placeholder_no_hash_check(self, asset_env):
        """Placeholders (empty hash) should pass integrity check."""
        store, _ = asset_env

        store.resolve(
            semantic_key="placeholder:test:v1",
            kind="SCENE",
            campaign_id="test_campaign",
        )

        issues = store.verify_integrity()
        assert issues == []


# =============================================================================
# Index Persistence Tests
# =============================================================================

class TestIndexPersistence:
    """Tests for save_index / load_index."""

    def test_save_and_load_index(self, asset_env):
        """Index should survive save/load roundtrip."""
        store, campaign_dir = asset_env

        # Add some assets
        for i in range(3):
            record = AssetRecord(
                asset_id=f"persist_{i:03d}",
                kind="SCENE",
                semantic_key=f"scene:persist:{i}:v1",
            )
            store.put(record, f"content_{i}".encode())

        # Save index
        store.save_index()

        # Create new store and load index
        store2 = AssetStore(campaign_dir)
        store2.load_index()

        assets = store2.list_assets()
        assert len(assets) == 3

        for i in range(3):
            assert store2.get(f"persist_{i:03d}") is not None

    def test_save_index_json_valid(self, asset_env):
        """Saved index should be valid JSON."""
        store, campaign_dir = asset_env

        record = AssetRecord(
            asset_id="json_test",
            kind="MAP",
            semantic_key="map:test:v1",
        )
        store.put(record, b"map data")
        store.save_index()

        index_path = campaign_dir / "assets" / "index.json"
        assert index_path.is_file()

        with open(index_path) as f:
            data = json.load(f)  # Should not raise

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["asset_id"] == "json_test"

    def test_load_index_nonexistent(self, asset_env):
        """Loading nonexistent index should be a no-op."""
        store, _ = asset_env

        store.load_index()  # Should not raise

        assert store.list_assets() == []
