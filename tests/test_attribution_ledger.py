"""Tests for M3 Attribution Ledger.

Tests:
- Add/get attribution records
- Validation rejects invalid records
- Save/load JSON persistence
- Sorted by asset_id
- Load from initial ATTRIBUTION.json
"""

import json
import pytest
from pathlib import Path

from aidm.immersion.attribution import AttributionStore
from aidm.schemas.immersion import AttributionRecord


# =============================================================================
# Add/Get Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestAddGet:
    """Tests for add/get operations."""

    def test_add_and_get(self):
        """Should store and retrieve by asset_id."""
        store = AttributionStore()
        record = AttributionRecord(
            asset_id="scene_001",
            source="stub_generator",
            license="generated",
            author="aidm_system",
        )
        store.add(record)
        result = store.get_by_asset_id("scene_001")
        assert result is not None
        assert result.asset_id == "scene_001"
        assert result.license == "generated"

    def test_get_nonexistent(self):
        """Should return None for unknown asset_id."""
        store = AttributionStore()
        assert store.get_by_asset_id("nonexistent") is None

    def test_add_rejects_empty_asset_id(self):
        """Should reject record with empty asset_id."""
        store = AttributionStore()
        record = AttributionRecord(license="MIT")
        with pytest.raises(ValueError, match="asset_id"):
            store.add(record)

    def test_add_rejects_empty_license(self):
        """Should reject record with empty license."""
        store = AttributionStore()
        record = AttributionRecord(asset_id="a1")
        with pytest.raises(ValueError, match="license"):
            store.add(record)

    def test_add_overwrites_existing(self):
        """Adding same asset_id should overwrite."""
        store = AttributionStore()
        store.add(AttributionRecord(asset_id="a1", license="MIT"))
        store.add(AttributionRecord(asset_id="a1", license="Apache-2.0"))
        result = store.get_by_asset_id("a1")
        assert result.license == "Apache-2.0"


# =============================================================================
# Listing Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestListing:
    """Tests for list_records."""

    def test_list_empty(self):
        """Empty store should return empty list."""
        store = AttributionStore()
        assert store.list_records() == []

    def test_list_sorted_by_asset_id(self):
        """Records should be sorted by asset_id."""
        store = AttributionStore()
        for aid in ["zzz", "aaa", "mmm"]:
            store.add(AttributionRecord(asset_id=aid, license="MIT"))
        records = store.list_records()
        ids = [r.asset_id for r in records]
        assert ids == ["aaa", "mmm", "zzz"]

    def test_list_count(self):
        """Should return all added records."""
        store = AttributionStore()
        for i in range(5):
            store.add(AttributionRecord(asset_id=f"a{i}", license="MIT"))
        assert len(store.list_records()) == 5


# =============================================================================
# Persistence Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestPersistence:
    """Tests for save/load."""

    def test_save_creates_file(self, tmp_path):
        """Save should create JSON file."""
        store = AttributionStore()
        store.add(AttributionRecord(asset_id="a1", license="MIT", author="dev"))
        path = tmp_path / "attribution.json"
        store.save(path)
        assert path.is_file()

    def test_save_valid_json(self, tmp_path):
        """Saved file should be valid JSON."""
        store = AttributionStore()
        store.add(AttributionRecord(asset_id="a1", license="CC-BY-4.0"))
        path = tmp_path / "attribution.json"
        store.save(path)
        with open(path) as f:
            data = json.load(f)
        assert data["schema_version"] == "1.0"
        assert len(data["records"]) == 1

    def test_save_sorted_keys(self, tmp_path):
        """Saved JSON should use sorted keys."""
        store = AttributionStore()
        store.add(AttributionRecord(asset_id="a1", license="MIT"))
        path = tmp_path / "attribution.json"
        store.save(path)
        content = path.read_text()
        data = json.loads(content)
        expected = json.dumps(data, indent=2, sort_keys=True) + "\n"
        assert content == expected

    def test_load_roundtrip(self, tmp_path):
        """Save → load should produce identical records."""
        store = AttributionStore()
        store.add(AttributionRecord(
            asset_id="scene_001",
            source="cache",
            license="CC-BY-4.0",
            author="artist",
        ))
        store.add(AttributionRecord(
            asset_id="portrait_002",
            source="generated",
            license="generated",
            author="aidm",
        ))

        path = tmp_path / "attribution.json"
        store.save(path)

        store2 = AttributionStore()
        store2.load(path)

        records = store2.list_records()
        assert len(records) == 2
        assert records[0].asset_id == "portrait_002"
        assert records[1].asset_id == "scene_001"

    def test_load_nonexistent_raises(self, tmp_path):
        """Loading nonexistent file should raise."""
        store = AttributionStore()
        with pytest.raises(FileNotFoundError):
            store.load(tmp_path / "nope.json")

    def test_load_initial_attribution_json(self):
        """Should load the initial assets/ATTRIBUTION.json."""
        store = AttributionStore()
        path = Path("assets/ATTRIBUTION.json")
        if path.is_file():
            store.load(path)
            assert store.list_records() == []
