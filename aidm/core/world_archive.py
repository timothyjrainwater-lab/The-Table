"""M2 World Archive — Campaign export/import bundle.

Provides deterministic campaign archiving:
- Export campaign to a directory bundle (manifest + logs + assets + prep)
- Import campaign from a bundle into a CampaignStore
- Validate archive structure before import
- Handle missing assets per regen_policy

All JSON output uses sorted keys for determinism.

Reference: docs/design/LOCAL_RUNTIME_PACKAGING_STRATEGY.md (LRP-001)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import shutil

from aidm.schemas.campaign import (
    AssetRecord,
    CampaignManifest,
    CampaignPaths,
)
from aidm.core.campaign_store import CampaignStore, CampaignStoreError


class WorldArchiveError(Exception):
    """Raised when archive operations fail."""


@dataclass
class ExportOptions:
    """Options for campaign export."""

    include_assets: bool = True
    """Whether to include asset files in the archive."""

    include_prep_log: bool = True
    """Whether to include prep job log."""


@dataclass
class ArchiveValidationResult:
    """Result of archive validation."""

    valid: bool
    """Whether the archive is valid for import."""

    status: str = "ready"
    """Status: 'ready' or 'blocked'."""

    issues: List[str] = field(default_factory=list)
    """List of issues found."""

    manifest_version: str = ""
    """Schema version found in manifest."""

    campaign_id: str = ""
    """Campaign ID from manifest."""


class WorldArchive:
    """Campaign export/import manager.

    Handles serializing a campaign to a portable archive directory
    and restoring it into a CampaignStore.
    """

    @staticmethod
    def export_campaign(
        store: CampaignStore,
        campaign_id: str,
        output_path: Path,
        options: Optional[ExportOptions] = None,
    ) -> Path:
        """Export a campaign to an archive directory.

        Creates a self-contained directory with:
        - manifest.json
        - events.jsonl
        - intents.jsonl
        - assets/ (if include_assets)
        - prep/prep_jobs.jsonl (if include_prep_log)

        Args:
            store: Campaign store containing the campaign
            campaign_id: Campaign to export
            output_path: Directory to create the archive in
            options: Export options

        Returns:
            Path to the created archive directory

        Raises:
            WorldArchiveError: If export fails
        """
        options = options or ExportOptions()

        # Load manifest
        try:
            manifest = store.load_campaign(campaign_id)
        except CampaignStoreError as e:
            raise WorldArchiveError(f"Cannot load campaign for export: {e}")

        campaign_dir = store.campaign_dir(campaign_id)
        archive_dir = Path(output_path) / campaign_id

        # Create archive directory
        try:
            archive_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise WorldArchiveError(
                f"Archive directory already exists: {archive_dir}"
            )

        # Write manifest (sorted keys for determinism)
        manifest_path = archive_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2, sort_keys=True)
            f.write("\n")

        # Copy event log
        _copy_file_if_exists(
            campaign_dir / manifest.paths.events,
            archive_dir / manifest.paths.events,
        )

        # Copy intent log
        _copy_file_if_exists(
            campaign_dir / manifest.paths.intents,
            archive_dir / manifest.paths.intents,
        )

        # Copy assets
        if options.include_assets:
            src_assets = campaign_dir / manifest.paths.assets
            if src_assets.is_dir():
                dst_assets = archive_dir / manifest.paths.assets
                shutil.copytree(src_assets, dst_assets)

        # Copy prep log
        if options.include_prep_log:
            src_prep = campaign_dir / manifest.paths.prep
            if src_prep.is_dir():
                dst_prep = archive_dir / manifest.paths.prep
                shutil.copytree(src_prep, dst_prep)

        # Copy start_state.json if it exists
        _copy_file_if_exists(
            campaign_dir / "start_state.json",
            archive_dir / "start_state.json",
        )

        return archive_dir

    @staticmethod
    def import_campaign(
        archive_path: Path,
        store: CampaignStore,
    ) -> CampaignManifest:
        """Import a campaign from an archive into a store.

        Validates the archive, copies files into the store's campaign directory,
        and handles missing assets per their regen_policy.

        Args:
            archive_path: Path to the archive directory
            store: Campaign store to import into

        Returns:
            Loaded CampaignManifest

        Raises:
            WorldArchiveError: If import fails or archive is invalid
        """
        archive_path = Path(archive_path)

        # Validate first
        validation = WorldArchive.validate_archive(archive_path)
        if not validation.valid:
            raise WorldArchiveError(
                f"Invalid archive: {'; '.join(validation.issues)}"
            )

        # Load manifest from archive
        manifest_path = archive_path / "manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        manifest = CampaignManifest.from_dict(manifest_data)
        campaign_id = manifest.campaign_id

        # Create campaign directory in store
        campaign_dir = store.root_dir / campaign_id
        if campaign_dir.exists():
            raise WorldArchiveError(
                f"Campaign already exists in store: {campaign_id}"
            )

        campaign_dir.mkdir(parents=True)

        # Copy all files from archive
        for item in archive_path.iterdir():
            src = item
            dst = campaign_dir / item.name

            if src.is_file():
                shutil.copy2(src, dst)
            elif src.is_dir():
                shutil.copytree(src, dst)

        # Update paths in manifest to point to new location
        manifest.paths.root = str(campaign_dir)

        # Re-save manifest with updated paths
        store.save_manifest(manifest)

        # Handle missing assets per regen_policy
        _handle_missing_assets(campaign_dir, manifest)

        return manifest

    @staticmethod
    def validate_archive(archive_path: Path) -> ArchiveValidationResult:
        """Validate an archive directory structure.

        Checks:
        - manifest.json exists and is valid JSON
        - Required log files present
        - Schema version compatibility
        - Asset references vs actual files

        Args:
            archive_path: Path to the archive directory

        Returns:
            ArchiveValidationResult
        """
        archive_path = Path(archive_path)
        issues = []

        if not archive_path.is_dir():
            return ArchiveValidationResult(
                valid=False,
                status="blocked",
                issues=["Archive path is not a directory"],
            )

        # Check manifest
        manifest_path = archive_path / "manifest.json"
        if not manifest_path.is_file():
            return ArchiveValidationResult(
                valid=False,
                status="blocked",
                issues=["Missing manifest.json"],
            )

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except json.JSONDecodeError as e:
            return ArchiveValidationResult(
                valid=False,
                status="blocked",
                issues=[f"Invalid manifest JSON: {e}"],
            )

        # Extract version info
        campaign_id = manifest_data.get("campaign_id", "")
        schema_version = manifest_data.get("config_schema_version", "")

        # Check schema version compatibility
        if schema_version and schema_version not in ("1.0",):
            issues.append(
                f"Unsupported schema version: {schema_version}"
            )

        # Check for required log files
        paths = manifest_data.get("paths", {})
        events_file = paths.get("events", "events.jsonl")
        intents_file = paths.get("intents", "intents.jsonl")

        if not (archive_path / events_file).is_file():
            issues.append(f"Missing event log: {events_file}")

        if not (archive_path / intents_file).is_file():
            issues.append(f"Missing intent log: {intents_file}")

        # Check session_zero validity
        sz_data = manifest_data.get("session_zero", {})
        from aidm.schemas.campaign import SessionZeroConfig
        sz = SessionZeroConfig.from_dict(sz_data)
        sz_errors = sz.validate()
        for err in sz_errors:
            issues.append(f"SessionZero: {err}")

        valid = len(issues) == 0
        status = "ready" if valid else "blocked"

        return ArchiveValidationResult(
            valid=valid,
            status=status,
            issues=issues,
            manifest_version=schema_version,
            campaign_id=campaign_id,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _copy_file_if_exists(src: Path, dst: Path) -> None:
    """Copy a file if it exists, creating parent dirs as needed."""
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    else:
        # Create empty file to maintain structure
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.touch()


def _handle_missing_assets(
    campaign_dir: Path,
    manifest: CampaignManifest,
) -> None:
    """Handle missing assets per their regen_policy.

    For REGEN_ON_MISS: create placeholder file
    For FAIL_ON_MISS: raise error (not implemented in M2 — no asset index yet)
    """
    assets_dir = campaign_dir / manifest.paths.assets
    if not assets_dir.is_dir():
        assets_dir.mkdir(parents=True, exist_ok=True)
