"""M2 Campaign Store — Directory-based campaign persistence.

Provides filesystem-backed campaign lifecycle management:
- Create campaign directories with deterministic layout
- Load/save campaign manifests
- List available campaigns
- All data persisted as JSON/JSONL (no database dependency)

Directory layout per campaign:
    campaigns/<campaign_id>/
        manifest.json
        events.jsonl
        intents.jsonl
        assets/
        prep/
            prep_jobs.jsonl

Reference: docs/design/LOCAL_RUNTIME_PACKAGING_STRATEGY.md (LRP-001)
"""

from datetime import datetime
from pathlib import Path
from typing import List
import json

from aidm.schemas.campaign import (
    CampaignManifest,
    CampaignPaths,
    SessionZeroConfig,
)
from aidm.core.version_check import validate_campaign_version


class CampaignStoreError(Exception):
    """Raised when campaign store operations fail."""


class CampaignStore:
    """Filesystem-backed campaign persistence.

    Each campaign gets a directory under the root containing:
    - manifest.json: Campaign metadata + version pinning
    - events.jsonl: Append-only event log
    - intents.jsonl: Append-only intent log
    - assets/: Campaign-specific asset files
    - prep/: Prep orchestrator state
        - prep_jobs.jsonl: Append-only job log
    """

    def __init__(self, root_dir: Path):
        """Initialize campaign store.

        Args:
            root_dir: Base directory for all campaigns.
                      Each campaign gets a subdirectory here.
        """
        self.root_dir = Path(root_dir)

    def create_campaign(
        self,
        campaign_id: str,
        session_zero: SessionZeroConfig,
        title: str,
        created_at: str,
        seed: int = 0,
    ) -> CampaignManifest:
        """Create a new campaign with directory structure.

        Args:
            campaign_id: Unique campaign identifier (BL-017: must be injected,
                         e.g., str(uuid.uuid4()) by caller)
            session_zero: Session Zero configuration
            title: Human-readable campaign title
            created_at: ISO-format timestamp (BL-018: must be injected,
                        e.g., datetime.now(timezone.utc).isoformat() by caller)
            seed: Master RNG seed (0 = default)

        Returns:
            CampaignManifest for the created campaign

        Raises:
            CampaignStoreError: If campaign directory cannot be created
        """
        campaign_dir = self.root_dir / campaign_id

        # Create directory structure
        try:
            campaign_dir.mkdir(parents=True, exist_ok=False)
            (campaign_dir / "assets").mkdir()
            (campaign_dir / "prep").mkdir()
        except FileExistsError:
            raise CampaignStoreError(
                f"Campaign directory already exists: {campaign_dir}"
            )
        except OSError as e:
            raise CampaignStoreError(
                f"Failed to create campaign directory: {e}"
            )

        # Build manifest
        paths = CampaignPaths(root=str(campaign_dir))

        manifest = CampaignManifest(
            campaign_id=campaign_id,
            title=title,
            created_at=created_at,
            master_seed=seed,
            session_zero=session_zero,
            paths=paths,
        )

        # Write manifest
        self.save_manifest(manifest)

        # Create empty event and intent logs
        (campaign_dir / paths.events).touch()
        (campaign_dir / paths.intents).touch()

        # Create empty prep jobs log
        (campaign_dir / "prep" / "prep_jobs.jsonl").touch()

        return manifest

    def load_campaign(self, campaign_id: str) -> CampaignManifest:
        """Load a campaign manifest from disk.

        Args:
            campaign_id: Campaign identifier

        Returns:
            CampaignManifest

        Raises:
            CampaignStoreError: If campaign not found or manifest invalid
        """
        campaign_dir = self.root_dir / campaign_id
        manifest_path = campaign_dir / "manifest.json"

        if not campaign_dir.is_dir():
            raise CampaignStoreError(
                f"Campaign not found: {campaign_id}"
            )

        if not manifest_path.is_file():
            raise CampaignStoreError(
                f"Manifest not found for campaign: {campaign_id}"
            )

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CampaignStoreError(
                f"Invalid manifest JSON for campaign {campaign_id}: {e}"
            )

        manifest = CampaignManifest.from_dict(data)
        validate_campaign_version(manifest.engine_version)
        return manifest

    def save_manifest(self, manifest: CampaignManifest) -> None:
        """Save a campaign manifest to disk.

        Args:
            manifest: The manifest to save

        Raises:
            CampaignStoreError: If manifest cannot be written
        """
        campaign_dir = self.root_dir / manifest.campaign_id
        manifest_path = campaign_dir / "manifest.json"

        if not campaign_dir.is_dir():
            raise CampaignStoreError(
                f"Campaign directory not found: {manifest.campaign_id}"
            )

        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest.to_dict(), f, indent=2, sort_keys=True)
                f.write("\n")
        except OSError as e:
            raise CampaignStoreError(
                f"Failed to write manifest: {e}"
            )

    def list_campaigns(self) -> List[str]:
        """List all campaign IDs in the store.

        Returns:
            List of campaign_id strings (sorted for determinism)
        """
        if not self.root_dir.is_dir():
            return []

        campaign_ids = []
        for entry in self.root_dir.iterdir():
            if entry.is_dir() and (entry / "manifest.json").is_file():
                campaign_ids.append(entry.name)

        return sorted(campaign_ids)

    def campaign_dir(self, campaign_id: str) -> Path:
        """Get the directory path for a campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Path to campaign directory
        """
        return self.root_dir / campaign_id

    def campaign_exists(self, campaign_id: str) -> bool:
        """Check if a campaign exists.

        Args:
            campaign_id: Campaign identifier

        Returns:
            True if campaign directory and manifest exist
        """
        campaign_dir = self.root_dir / campaign_id
        return (
            campaign_dir.is_dir()
            and (campaign_dir / "manifest.json").is_file()
        )
