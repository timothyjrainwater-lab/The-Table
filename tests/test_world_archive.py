"""Tests for M2 World Archive (Export/Import).

Tests:
- Export creates valid archive structure
- Import restores manifest identically
- Archive validation catches issues
- Export → import → manifest roundtrip
- Missing assets handled per policy
- All operations use tmp_path fixture
"""

import json
import pytest
from pathlib import Path

from aidm.core.campaign_store import CampaignStore
from aidm.core.prep_orchestrator import PrepOrchestrator
from aidm.core.world_archive import (
    ArchiveValidationResult,
    ExportOptions,
    WorldArchive,
    WorldArchiveError,
)
from aidm.schemas.campaign import (
    CampaignManifest,
    SessionZeroConfig,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def prepared_campaign(tmp_path):
    """Create a fully-prepared campaign (all prep jobs run)."""
    store = CampaignStore(tmp_path / "campaigns")
    sz = SessionZeroConfig(
        alignment_mode="inferred",
        preparation_depth="standard",
        optional_rules=["flanking"],
    )
    manifest = store.create_campaign(sz, "Export Test Campaign", seed=42)

    # Run full prep
    orch = PrepOrchestrator(manifest, store)
    orch.run_all()

    return store, manifest


@pytest.fixture
def export_dir(tmp_path):
    """Create an export output directory."""
    export_path = tmp_path / "exports"
    export_path.mkdir()
    return export_path


@pytest.fixture
def import_store(tmp_path):
    """Create a separate store for imports."""
    store = CampaignStore(tmp_path / "import_store")
    return store


# =============================================================================
# Export Tests
# =============================================================================

class TestExport:
    """Tests for WorldArchive.export_campaign."""

    def test_export_creates_archive(self, prepared_campaign, export_dir):
        """Should create archive directory with correct structure."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        assert archive_path.is_dir()
        assert (archive_path / "manifest.json").is_file()
        assert (archive_path / "events.jsonl").is_file()
        assert (archive_path / "intents.jsonl").is_file()
        assert (archive_path / "assets").is_dir()
        assert (archive_path / "prep").is_dir()

    def test_export_manifest_matches(self, prepared_campaign, export_dir):
        """Exported manifest should match source manifest."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        with open(archive_path / "manifest.json") as f:
            exported_data = json.load(f)

        assert exported_data["campaign_id"] == manifest.campaign_id
        assert exported_data["title"] == "Export Test Campaign"
        assert exported_data["master_seed"] == 42
        assert exported_data["session_zero"]["alignment_mode"] == "inferred"

    def test_export_sorted_keys(self, prepared_campaign, export_dir):
        """Exported JSON should use sorted keys."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        content = (archive_path / "manifest.json").read_text()
        data = json.loads(content)
        expected = json.dumps(data, indent=2, sort_keys=True) + "\n"
        assert content == expected

    def test_export_without_assets(self, prepared_campaign, export_dir):
        """Should skip assets when include_assets=False."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir,
            options=ExportOptions(include_assets=False),
        )

        assert (archive_path / "manifest.json").is_file()
        assert not (archive_path / "assets").exists()

    def test_export_without_prep_log(self, prepared_campaign, export_dir):
        """Should skip prep log when include_prep_log=False."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir,
            options=ExportOptions(include_prep_log=False),
        )

        assert (archive_path / "manifest.json").is_file()
        assert not (archive_path / "prep").exists()

    def test_export_includes_start_state(self, prepared_campaign, export_dir):
        """Should include start_state.json if present."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        assert (archive_path / "start_state.json").is_file()

    def test_export_nonexistent_campaign(self, tmp_path, export_dir):
        """Should raise error for nonexistent campaign."""
        store = CampaignStore(tmp_path / "campaigns")

        with pytest.raises(WorldArchiveError, match="Cannot load campaign"):
            WorldArchive.export_campaign(store, "fake-id", export_dir)

    def test_export_existing_archive_dir(self, prepared_campaign, export_dir):
        """Should raise error if archive directory already exists."""
        store, manifest = prepared_campaign

        # Export once
        WorldArchive.export_campaign(store, manifest.campaign_id, export_dir)

        # Export again should fail
        with pytest.raises(WorldArchiveError, match="already exists"):
            WorldArchive.export_campaign(store, manifest.campaign_id, export_dir)


# =============================================================================
# Import Tests
# =============================================================================

class TestImport:
    """Tests for WorldArchive.import_campaign."""

    def test_import_restores_manifest(
        self, prepared_campaign, export_dir, import_store
    ):
        """Imported manifest should match original."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        imported = WorldArchive.import_campaign(archive_path, import_store)

        assert imported.campaign_id == manifest.campaign_id
        assert imported.title == manifest.title
        assert imported.master_seed == manifest.master_seed
        assert imported.session_zero.alignment_mode == "inferred"
        assert imported.session_zero.optional_rules == ["flanking"]

    def test_import_creates_campaign_dir(
        self, prepared_campaign, export_dir, import_store
    ):
        """Import should create campaign directory in target store."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        WorldArchive.import_campaign(archive_path, import_store)

        assert import_store.campaign_exists(manifest.campaign_id)

    def test_import_copies_files(
        self, prepared_campaign, export_dir, import_store
    ):
        """Import should copy all archive files."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        WorldArchive.import_campaign(archive_path, import_store)

        campaign_dir = import_store.campaign_dir(manifest.campaign_id)
        assert (campaign_dir / "manifest.json").is_file()
        assert (campaign_dir / "events.jsonl").is_file()
        assert (campaign_dir / "intents.jsonl").is_file()
        assert (campaign_dir / "assets").is_dir()

    def test_import_loadable_from_store(
        self, prepared_campaign, export_dir, import_store
    ):
        """Imported campaign should be loadable from the target store."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        WorldArchive.import_campaign(archive_path, import_store)

        loaded = import_store.load_campaign(manifest.campaign_id)
        assert loaded.title == "Export Test Campaign"
        assert loaded.master_seed == 42

    def test_import_duplicate_campaign(
        self, prepared_campaign, export_dir, import_store
    ):
        """Should raise error if campaign already exists in target store."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        # Import once
        WorldArchive.import_campaign(archive_path, import_store)

        # Import again should fail
        with pytest.raises(WorldArchiveError, match="already exists"):
            WorldArchive.import_campaign(archive_path, import_store)

    def test_import_invalid_archive(self, tmp_path, import_store):
        """Should raise error for invalid archive."""
        bad_archive = tmp_path / "bad_archive"
        bad_archive.mkdir()
        # No manifest.json

        with pytest.raises(WorldArchiveError, match="Invalid archive"):
            WorldArchive.import_campaign(bad_archive, import_store)


# =============================================================================
# Validation Tests
# =============================================================================

class TestValidation:
    """Tests for WorldArchive.validate_archive."""

    def test_validate_valid_archive(self, prepared_campaign, export_dir):
        """Valid archive should pass validation."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        result = WorldArchive.validate_archive(archive_path)

        assert result.valid is True
        assert result.status == "ready"
        assert result.issues == []
        assert result.campaign_id == manifest.campaign_id

    def test_validate_missing_manifest(self, tmp_path):
        """Should fail for missing manifest."""
        archive = tmp_path / "no_manifest"
        archive.mkdir()

        result = WorldArchive.validate_archive(archive)

        assert result.valid is False
        assert "Missing manifest" in result.issues[0]

    def test_validate_invalid_json(self, tmp_path):
        """Should fail for invalid manifest JSON."""
        archive = tmp_path / "bad_json"
        archive.mkdir()
        (archive / "manifest.json").write_text("not json{{{")

        result = WorldArchive.validate_archive(archive)

        assert result.valid is False
        assert "Invalid manifest JSON" in result.issues[0]

    def test_validate_not_a_directory(self, tmp_path):
        """Should fail for non-directory path."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("nope")

        result = WorldArchive.validate_archive(file_path)

        assert result.valid is False
        assert "not a directory" in result.issues[0]

    def test_validate_missing_logs(self, tmp_path):
        """Should flag missing log files."""
        archive = tmp_path / "missing_logs"
        archive.mkdir()

        manifest_data = {
            "campaign_id": "test-id",
            "title": "Test",
            "config_schema_version": "1.0",
            "paths": {
                "events": "events.jsonl",
                "intents": "intents.jsonl",
            },
            "session_zero": {},
        }
        with open(archive / "manifest.json", "w") as f:
            json.dump(manifest_data, f)

        result = WorldArchive.validate_archive(archive)

        assert result.valid is False
        assert any("Missing event log" in i for i in result.issues)
        assert any("Missing intent log" in i for i in result.issues)

    def test_validate_returns_campaign_id(self, prepared_campaign, export_dir):
        """Validation result should include campaign_id."""
        store, manifest = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )

        result = WorldArchive.validate_archive(archive_path)

        assert result.campaign_id == manifest.campaign_id
        assert result.manifest_version == "1.0"


# =============================================================================
# Export → Import Roundtrip Tests
# =============================================================================

class TestExportImportRoundtrip:
    """Tests for full export → import → verify cycle."""

    def test_manifest_roundtrip(
        self, prepared_campaign, export_dir, import_store
    ):
        """Manifest should survive export → import roundtrip."""
        store, original = prepared_campaign

        archive_path = WorldArchive.export_campaign(
            store, original.campaign_id, export_dir
        )
        imported = WorldArchive.import_campaign(archive_path, import_store)

        # Core fields should match
        assert imported.campaign_id == original.campaign_id
        assert imported.title == original.title
        assert imported.engine_version == original.engine_version
        assert imported.config_schema_version == original.config_schema_version
        assert imported.master_seed == original.master_seed

        # Session zero should match
        assert imported.session_zero.ruleset_id == original.session_zero.ruleset_id
        assert imported.session_zero.alignment_mode == original.session_zero.alignment_mode
        assert imported.session_zero.preparation_depth == original.session_zero.preparation_depth
        assert imported.session_zero.optional_rules == original.session_zero.optional_rules

    def test_event_log_roundtrip(
        self, prepared_campaign, export_dir, import_store
    ):
        """Event log should survive export → import roundtrip."""
        store, manifest = prepared_campaign

        # Write some events
        campaign_dir = store.campaign_dir(manifest.campaign_id)
        events_path = campaign_dir / "events.jsonl"
        with open(events_path, "w") as f:
            f.write(json.dumps({"type": "test_event", "data": "value"}) + "\n")
            f.write(json.dumps({"type": "second_event", "data": 42}) + "\n")

        # Export → import
        archive_path = WorldArchive.export_campaign(
            store, manifest.campaign_id, export_dir
        )
        WorldArchive.import_campaign(archive_path, import_store)

        # Verify events survived
        imported_dir = import_store.campaign_dir(manifest.campaign_id)
        imported_events = (imported_dir / "events.jsonl").read_text()

        assert "test_event" in imported_events
        assert "second_event" in imported_events

    def test_full_lifecycle_roundtrip(
        self, prepared_campaign, export_dir, import_store
    ):
        """Full lifecycle: create → prep → export → import → load."""
        store, original = prepared_campaign

        # Export
        archive_path = WorldArchive.export_campaign(
            store, original.campaign_id, export_dir
        )

        # Validate archive
        validation = WorldArchive.validate_archive(archive_path)
        assert validation.valid is True

        # Import
        imported = WorldArchive.import_campaign(archive_path, import_store)

        # Load from target store
        loaded = import_store.load_campaign(imported.campaign_id)

        # Verify
        assert loaded.campaign_id == original.campaign_id
        assert loaded.title == original.title
        assert loaded.master_seed == original.master_seed
        assert import_store.campaign_exists(loaded.campaign_id)

        # List should contain the imported campaign
        campaigns = import_store.list_campaigns()
        assert loaded.campaign_id in campaigns
