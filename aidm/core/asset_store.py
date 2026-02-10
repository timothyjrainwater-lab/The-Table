"""M2 Asset Store — Campaign asset management with shared cache.

Manages campaign-specific assets with support for:
- Put/get asset lifecycle (write file + metadata)
- Deterministic asset ID generation
- Shared cache resolution (reuse generic assets across campaigns)
- Integrity verification (content hash checking)

For M2, all assets are placeholders (zero-byte files with full metadata).
Real asset generation is deferred to M3.

Per LRP-001: assets are atmospheric only, never mechanical authority.
"""

from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import json
import shutil

from aidm.schemas.campaign import AssetRecord, compute_asset_id


class AssetStoreError(Exception):
    """Raised when asset store operations fail."""


class AssetStore:
    """Campaign asset storage with shared cache support.

    Each campaign has its own assets directory. A shared cache directory
    allows reuse of generic assets (tavern scenes, etc.) across campaigns.

    Assets are identified by deterministic IDs computed from
    (campaign_id, kind, semantic_key).
    """

    def __init__(
        self,
        campaign_dir: Path,
        shared_cache_dir: Optional[Path] = None,
    ):
        """Initialize asset store.

        Args:
            campaign_dir: Campaign root directory (contains assets/)
            shared_cache_dir: Optional shared cache directory
        """
        self.campaign_dir = Path(campaign_dir)
        self.assets_dir = self.campaign_dir / "assets"
        self.shared_cache_dir = Path(shared_cache_dir) if shared_cache_dir else None

        # In-memory index of known assets
        self._index: Dict[str, AssetRecord] = {}

    def put(self, record: AssetRecord, content: bytes) -> AssetRecord:
        """Store an asset with its content.

        Args:
            record: Asset metadata
            content: Raw file content

        Returns:
            Updated AssetRecord with computed content_hash

        Raises:
            AssetStoreError: If write fails
        """
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        # Compute content hash
        content_hash = hashlib.sha256(content).hexdigest()
        record.content_hash = content_hash

        # Determine file path
        if not record.path:
            record.path = f"assets/{record.asset_id}_{record.kind.lower()}"

        # Write content
        file_path = self.campaign_dir / record.path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            file_path.write_bytes(content)
        except OSError as e:
            raise AssetStoreError(f"Failed to write asset: {e}")

        # Update index
        self._index[record.asset_id] = record

        return record

    def get(self, asset_id: str) -> Optional[AssetRecord]:
        """Look up an asset by ID.

        Args:
            asset_id: Deterministic asset identifier

        Returns:
            AssetRecord if found, None otherwise
        """
        return self._index.get(asset_id)

    def get_content(self, asset_id: str) -> Optional[bytes]:
        """Read asset file content.

        Args:
            asset_id: Asset identifier

        Returns:
            File content bytes, or None if asset not found
        """
        record = self._index.get(asset_id)
        if record is None:
            return None

        file_path = self.campaign_dir / record.path
        if not file_path.is_file():
            return None

        return file_path.read_bytes()

    def resolve(
        self,
        semantic_key: str,
        kind: str,
        campaign_id: str,
        use_shared_cache: bool = True,
    ) -> AssetRecord:
        """Resolve an asset, checking shared cache if enabled.

        Resolution order:
        1. Check campaign-local index
        2. If use_shared_cache: check shared cache
        3. If found in cache: copy to campaign assets
        4. Else: create placeholder with REGEN_ON_MISS policy

        Args:
            semantic_key: Semantic identifier (e.g., "generic:tavern:interior:v1")
            kind: Asset kind (e.g., "SCENE")
            campaign_id: Campaign identifier
            use_shared_cache: Whether to check shared cache

        Returns:
            AssetRecord (may be a placeholder)
        """
        asset_id = compute_asset_id(campaign_id, kind, semantic_key)

        # 1. Check local index
        if asset_id in self._index:
            return self._index[asset_id]

        # 2. Check shared cache
        if use_shared_cache and self.shared_cache_dir:
            cached = self._find_in_cache(semantic_key, kind)
            if cached is not None:
                return self._import_from_cache(
                    cached, asset_id, kind, semantic_key, campaign_id
                )

        # 3. Create placeholder
        record = AssetRecord(
            asset_id=asset_id,
            kind=kind,
            semantic_key=semantic_key,
            content_hash="",
            path=f"assets/{asset_id}.placeholder",
            provenance="GENERATED",
            regen_policy="REGEN_ON_MISS",
        )

        # Create placeholder file
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        placeholder_path = self.campaign_dir / record.path
        placeholder_path.touch()

        self._index[asset_id] = record
        return record

    def list_assets(self) -> List[AssetRecord]:
        """List all known assets.

        Returns:
            List of AssetRecord instances (sorted by asset_id for determinism)
        """
        return sorted(self._index.values(), key=lambda r: r.asset_id)

    def verify_integrity(self) -> List[str]:
        """Verify all assets exist and hashes match.

        Returns:
            List of issues found (empty = all valid)
        """
        issues = []

        for asset_id, record in sorted(self._index.items()):
            file_path = self.campaign_dir / record.path

            # Check file exists
            if not file_path.is_file():
                issues.append(f"Missing file for asset {asset_id}: {record.path}")
                continue

            # Check hash (skip for placeholders with empty hash)
            if record.content_hash:
                actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                if actual_hash != record.content_hash:
                    issues.append(
                        f"Hash mismatch for asset {asset_id}: "
                        f"expected {record.content_hash[:16]}..., "
                        f"got {actual_hash[:16]}..."
                    )

        return issues

    def save_index(self, path: Optional[Path] = None) -> None:
        """Save asset index to JSON file.

        Args:
            path: Output path (defaults to assets/index.json)
        """
        if path is None:
            path = self.assets_dir / "index.json"

        path.parent.mkdir(parents=True, exist_ok=True)

        records = [r.to_dict() for r in self.list_assets()]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, sort_keys=True)
            f.write("\n")

    def load_index(self, path: Optional[Path] = None) -> None:
        """Load asset index from JSON file.

        Args:
            path: Input path (defaults to assets/index.json)
        """
        if path is None:
            path = self.assets_dir / "index.json"

        if not path.is_file():
            return

        with open(path, "r", encoding="utf-8") as f:
            records = json.load(f)

        for data in records:
            record = AssetRecord.from_dict(data)
            self._index[record.asset_id] = record

    # -----------------------------------------------------------------
    # Shared Cache Helpers
    # -----------------------------------------------------------------

    def _find_in_cache(
        self, semantic_key: str, kind: str
    ) -> Optional[Path]:
        """Find an asset in the shared cache by semantic key.

        Cache layout: shared_cache/<kind>/<semantic_key_escaped>
        """
        if self.shared_cache_dir is None:
            return None

        # Escape semantic key for filesystem
        escaped_key = semantic_key.replace(":", "_").replace("/", "_")
        cache_path = self.shared_cache_dir / kind.lower() / escaped_key

        if cache_path.is_file():
            return cache_path

        return None

    def _import_from_cache(
        self,
        cache_path: Path,
        asset_id: str,
        kind: str,
        semantic_key: str,
        campaign_id: str,
    ) -> AssetRecord:
        """Import an asset from shared cache into campaign assets."""
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        # Copy file
        dest_path = self.assets_dir / f"{asset_id}_{kind.lower()}"
        shutil.copy2(cache_path, dest_path)

        # Compute hash of imported file
        content_hash = hashlib.sha256(dest_path.read_bytes()).hexdigest()

        record = AssetRecord(
            asset_id=asset_id,
            kind=kind,
            semantic_key=semantic_key,
            content_hash=content_hash,
            path=f"assets/{asset_id}_{kind.lower()}",
            provenance="SHARED_CACHE",
            regen_policy="REGEN_ON_MISS",
        )

        self._index[asset_id] = record
        return record
