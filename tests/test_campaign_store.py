"""Tests for M2 Campaign Store.

Tests:
- Campaign creation with directory structure
- Manifest persistence (save/load roundtrip)
- Campaign listing and discovery
- Error handling for missing/invalid campaigns
- All operations use tmp_path fixture
"""

import json
import pytest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from aidm.core.campaign_store import CampaignStore, CampaignStoreError
from aidm.schemas.campaign import (
    CampaignManifest,
    CampaignPaths,
    SessionZeroConfig,
)


# Test helper to inject required campaign_id and created_at
def _create_campaign_injected(store, session_zero, title, seed=0):
    """Helper to create campaign with injected BL-017/018 values."""
    return store.create_campaign(
        campaign_id=str(uuid.uuid4()),
        session_zero=session_zero,
        title=title,
        created_at=datetime.now(timezone.utc).isoformat(),
        seed=seed,
    )


# =============================================================================
# Campaign Creation Tests
# =============================================================================

class TestCampaignCreation:
    """Tests for CampaignStore.create_campaign."""

    def test_create_campaign_returns_manifest(self, tmp_path):
        """Should return a valid CampaignManifest."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = _create_campaign_injected(store, sz, "Test Campaign", seed=42)

        assert isinstance(manifest, CampaignManifest)
        assert manifest.title == "Test Campaign"
        assert manifest.master_seed == 42
        assert len(manifest.campaign_id) == 36  # UUID format

    def test_create_campaign_directory_structure(self, tmp_path):
        """Should create correct directory layout."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = _create_campaign_injected(store, sz, "Test")
        campaign_dir = tmp_path / manifest.campaign_id

        # Verify directory structure
        assert campaign_dir.is_dir()
        assert (campaign_dir / "manifest.json").is_file()
        assert (campaign_dir / "events.jsonl").is_file()
        assert (campaign_dir / "intents.jsonl").is_file()
        assert (campaign_dir / "assets").is_dir()
        assert (campaign_dir / "prep").is_dir()
        assert (campaign_dir / "prep" / "prep_jobs.jsonl").is_file()

    def test_create_campaign_manifest_on_disk(self, tmp_path):
        """Manifest on disk should match returned manifest."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig(
            alignment_mode="inferred",
            preparation_depth="deep",
        )

        manifest = _create_campaign_injected(store, sz, "Roundtrip Test", seed=999)

        # Read manifest from disk
        manifest_path = tmp_path / manifest.campaign_id / "manifest.json"
        with open(manifest_path, "r") as f:
            data = json.load(f)

        assert data["title"] == "Roundtrip Test"
        assert data["master_seed"] == 999
        assert data["session_zero"]["alignment_mode"] == "inferred"
        assert data["session_zero"]["preparation_depth"] == "deep"

    def test_create_campaign_unique_ids(self, tmp_path):
        """Each campaign should get a unique ID."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        m1 = _create_campaign_injected(store, sz, "Campaign A")
        m2 = _create_campaign_injected(store, sz, "Campaign B")

        assert m1.campaign_id != m2.campaign_id

    def test_create_campaign_with_default_seed(self, tmp_path):
        """Should use seed=0 by default."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = _create_campaign_injected(store, sz, "Default Seed")

        assert manifest.master_seed == 0

    def test_create_campaign_sets_created_at(self, tmp_path):
        """Should set created_at timestamp."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = _create_campaign_injected(store, sz, "Timestamped")

        assert manifest.created_at != ""
        # Should be ISO format
        assert "T" in manifest.created_at

    def test_create_campaign_embeds_session_zero(self, tmp_path):
        """Should embed full session zero config."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig(
            ruleset_id="RAW_3.5",
            optional_rules=["flanking", "massive_damage"],
            alignment_mode="narrative_only",
            doctrine_enforcement=False,
        )

        manifest = _create_campaign_injected(store, sz, "Full SZ")

        assert manifest.session_zero.optional_rules == ["flanking", "massive_damage"]
        assert manifest.session_zero.alignment_mode == "narrative_only"
        assert manifest.session_zero.doctrine_enforcement is False

    def test_create_campaign_empty_logs(self, tmp_path):
        """Event and intent logs should start empty."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = _create_campaign_injected(store, sz, "Empty Logs")
        campaign_dir = tmp_path / manifest.campaign_id

        events = (campaign_dir / "events.jsonl").read_text()
        intents = (campaign_dir / "intents.jsonl").read_text()
        prep_jobs = (campaign_dir / "prep" / "prep_jobs.jsonl").read_text()

        assert events == ""
        assert intents == ""
        assert prep_jobs == ""

    def test_create_campaign_sets_paths(self, tmp_path):
        """Should set campaign paths with root."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = _create_campaign_injected(store, sz, "With Paths")

        assert manifest.paths.root == str(tmp_path / manifest.campaign_id)
        assert manifest.paths.events == "events.jsonl"
        assert manifest.paths.intents == "intents.jsonl"
        assert manifest.paths.assets == "assets"
        assert manifest.paths.prep == "prep"

    def test_create_campaign_root_dir_created_if_missing(self, tmp_path):
        """Should create root dir if it doesn't exist."""
        store = CampaignStore(tmp_path / "campaigns")
        sz = SessionZeroConfig()

        manifest = _create_campaign_injected(store, sz, "New Root")

        assert (tmp_path / "campaigns").is_dir()
        assert (tmp_path / "campaigns" / manifest.campaign_id).is_dir()


# =============================================================================
# Campaign Loading Tests
# =============================================================================

class TestCampaignLoading:
    """Tests for CampaignStore.load_campaign."""

    def test_load_campaign_roundtrip(self, tmp_path):
        """Should load the same manifest that was created."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig(
            alignment_mode="inferred",
            optional_rules=["flanking"],
        )

        created = _create_campaign_injected(store, sz, "Load Test", seed=42)
        loaded = store.load_campaign(created.campaign_id)

        assert loaded.campaign_id == created.campaign_id
        assert loaded.title == "Load Test"
        assert loaded.master_seed == 42
        assert loaded.session_zero.alignment_mode == "inferred"
        assert loaded.session_zero.optional_rules == ["flanking"]

    def test_load_campaign_not_found(self, tmp_path):
        """Should raise error for missing campaign."""
        store = CampaignStore(tmp_path)

        with pytest.raises(CampaignStoreError, match="Campaign not found"):
            store.load_campaign("nonexistent-id")

    def test_load_campaign_no_manifest(self, tmp_path):
        """Should raise error if manifest.json is missing."""
        store = CampaignStore(tmp_path)
        # Create directory without manifest
        (tmp_path / "bad-campaign").mkdir()

        with pytest.raises(CampaignStoreError, match="Manifest not found"):
            store.load_campaign("bad-campaign")

    def test_load_campaign_invalid_json(self, tmp_path):
        """Should raise error for invalid JSON manifest."""
        store = CampaignStore(tmp_path)
        campaign_dir = tmp_path / "bad-json"
        campaign_dir.mkdir()
        (campaign_dir / "manifest.json").write_text("not valid json{{{")

        with pytest.raises(CampaignStoreError, match="Invalid manifest JSON"):
            store.load_campaign("bad-json")


# =============================================================================
# Manifest Save Tests
# =============================================================================

class TestManifestSave:
    """Tests for CampaignStore.save_manifest."""

    def test_save_manifest_updates_on_disk(self, tmp_path):
        """Should persist manifest changes to disk."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = _create_campaign_injected(store, sz, "Original Title")

        # Modify and save
        manifest.title = "Updated Title"
        manifest.master_seed = 999
        store.save_manifest(manifest)

        # Reload and verify
        reloaded = store.load_campaign(manifest.campaign_id)
        assert reloaded.title == "Updated Title"
        assert reloaded.master_seed == 999

    def test_save_manifest_sorted_keys(self, tmp_path):
        """Manifest JSON should use sorted keys for determinism."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = _create_campaign_injected(store, sz, "Sorted")

        manifest_path = tmp_path / manifest.campaign_id / "manifest.json"
        content = manifest_path.read_text()

        # Parse and re-serialize with sorted keys to compare
        data = json.loads(content)
        expected = json.dumps(data, indent=2, sort_keys=True) + "\n"
        assert content == expected

    def test_save_manifest_missing_directory(self, tmp_path):
        """Should raise error if campaign directory doesn't exist."""
        store = CampaignStore(tmp_path)
        manifest = CampaignManifest(
            campaign_id="nonexistent",
            title="Ghost",
        )

        with pytest.raises(CampaignStoreError, match="Campaign directory not found"):
            store.save_manifest(manifest)


# =============================================================================
# Campaign Listing Tests
# =============================================================================

class TestCampaignListing:
    """Tests for CampaignStore.list_campaigns."""

    def test_list_campaigns_empty(self, tmp_path):
        """Should return empty list for new store."""
        store = CampaignStore(tmp_path)

        assert store.list_campaigns() == []

    def test_list_campaigns_multiple(self, tmp_path):
        """Should list all campaign IDs."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        m1 = _create_campaign_injected(store, sz, "A")
        m2 = _create_campaign_injected(store, sz, "B")
        m3 = _create_campaign_injected(store, sz, "C")

        campaigns = store.list_campaigns()

        assert len(campaigns) == 3
        assert m1.campaign_id in campaigns
        assert m2.campaign_id in campaigns
        assert m3.campaign_id in campaigns

    def test_list_campaigns_sorted(self, tmp_path):
        """Campaign IDs should be sorted for determinism."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        _create_campaign_injected(store, sz, "A")
        _create_campaign_injected(store, sz, "B")
        _create_campaign_injected(store, sz, "C")

        campaigns = store.list_campaigns()

        assert campaigns == sorted(campaigns)

    def test_list_campaigns_ignores_non_campaigns(self, tmp_path):
        """Should skip directories without manifest.json."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        _create_campaign_injected(store, sz, "Real")

        # Create non-campaign directories
        (tmp_path / "random_dir").mkdir()
        (tmp_path / "some_file.txt").write_text("not a campaign")

        campaigns = store.list_campaigns()
        assert len(campaigns) == 1

    def test_list_campaigns_nonexistent_root(self, tmp_path):
        """Should return empty list if root dir doesn't exist."""
        store = CampaignStore(tmp_path / "nonexistent")

        assert store.list_campaigns() == []


# =============================================================================
# Utility Method Tests
# =============================================================================

class TestCampaignStoreUtils:
    """Tests for utility methods."""

    def test_campaign_exists_true(self, tmp_path):
        """Should return True for existing campaign."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        manifest = _create_campaign_injected(store, sz, "Exists")

        assert store.campaign_exists(manifest.campaign_id) is True

    def test_campaign_exists_false(self, tmp_path):
        """Should return False for nonexistent campaign."""
        store = CampaignStore(tmp_path)

        assert store.campaign_exists("fake-id") is False

    def test_campaign_exists_no_manifest(self, tmp_path):
        """Should return False for dir without manifest."""
        store = CampaignStore(tmp_path)
        (tmp_path / "no-manifest").mkdir()

        assert store.campaign_exists("no-manifest") is False

    def test_campaign_dir(self, tmp_path):
        """Should return correct campaign directory path."""
        store = CampaignStore(tmp_path)

        path = store.campaign_dir("test-id")

        assert path == tmp_path / "test-id"

    def test_full_lifecycle(self, tmp_path):
        """Full create → load → modify → save → reload lifecycle."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig(
            alignment_mode="strict",
            preparation_depth="standard",
            optional_rules=["flanking"],
        )

        # Create
        manifest = _create_campaign_injected(store, sz, "Lifecycle Test", seed=12345)
        campaign_id = manifest.campaign_id

        # Load
        loaded = store.load_campaign(campaign_id)
        assert loaded.title == "Lifecycle Test"

        # Modify session zero (add amendment)
        loaded.session_zero.add_amendment({"rule": "flanking", "action": "disable"})
        loaded.tool_versions = {"python": "3.11"}

        # Save
        store.save_manifest(loaded)

        # Reload
        reloaded = store.load_campaign(campaign_id)
        assert len(reloaded.session_zero.amendments) == 1
        assert reloaded.session_zero.amendments[0]["rule"] == "flanking"
        assert reloaded.tool_versions == {"python": "3.11"}

        # List
        assert campaign_id in store.list_campaigns()
        assert store.campaign_exists(campaign_id) is True
