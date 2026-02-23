"""M3 Prep Pipeline Schemas — Sequential model loading and asset generation contracts.

Defines data structures for the prep pipeline prototype:
- CampaignDescriptor: Input format for prep pipeline (campaign metadata + story context)
- PrepPipelineConfig: Configuration for sequential model loading
- PrepAssetManifest: Tracking generated assets per campaign
- PrepPipelineResult: Result of prep pipeline execution

The prep pipeline loads models sequentially in this order:
1. LLM (Qwen3) for campaign authoring (NPCs, encounters, dialogues)
2. Image Gen (SDXL Lightning) for visual assets (scenes, portraits, locations)
3. Music Gen (MusicGen) for campaign mood music
4. SFX Gen (AudioGen/Tango 2) for sound effects

All prep work is done OFFLINE during campaign preparation.
No LLM or generative models are loaded during runtime (BL-020 compliant).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal


@dataclass
class CampaignDescriptor:
    """Campaign descriptor JSON — input to prep pipeline.

    Defines campaign metadata and story context for LLM authoring.
    This is the starting point for all asset generation.
    """

    campaign_id: str
    """Unique campaign identifier."""

    name: str
    """Campaign name (e.g., 'The Haunted Manor')."""

    genre: str
    """Campaign genre (e.g., 'gothic horror', 'high fantasy', 'dungeon crawl')."""

    story_context: str
    """High-level story context for LLM authoring (e.g., 'A haunted manor with undead inhabitants')."""

    expected_npcs: int = 3
    """Number of NPCs to generate."""

    expected_scenes: int = 2
    """Number of scenes/locations to generate."""

    expected_encounters: int = 1
    """Number of combat encounters to generate."""

    mood_tags: List[str] = field(default_factory=list)
    """Mood tags for audio generation (e.g., ['dark', 'tense', 'mysterious'])."""

    def validate(self) -> List[str]:
        """Validate descriptor fields. Returns list of errors."""
        errors = []
        if not self.campaign_id:
            errors.append("campaign_id must not be empty.")
        if not self.name:
            errors.append("name must not be empty.")
        if not self.genre:
            errors.append("genre must not be empty.")
        if not self.story_context:
            errors.append("story_context must not be empty.")
        if self.expected_npcs < 0:
            errors.append("expected_npcs must be non-negative.")
        if self.expected_scenes < 0:
            errors.append("expected_scenes must be non-negative.")
        if self.expected_encounters < 0:
            errors.append("expected_encounters must be non-negative.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "genre": self.genre,
            "story_context": self.story_context,
            "expected_npcs": self.expected_npcs,
            "expected_scenes": self.expected_scenes,
            "expected_encounters": self.expected_encounters,
            "mood_tags": self.mood_tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampaignDescriptor":
        """Create from dictionary."""
        return cls(
            campaign_id=data.get("campaign_id", ""),
            name=data.get("name", ""),
            genre=data.get("genre", ""),
            story_context=data.get("story_context", ""),
            expected_npcs=data.get("expected_npcs", 3),
            expected_scenes=data.get("expected_scenes", 2),
            expected_encounters=data.get("expected_encounters", 1),
            mood_tags=data.get("mood_tags", []),
        )


@dataclass
class ModelLoadConfig:
    """Configuration for loading a single model in the pipeline.

    Specifies model type, model path, and loading parameters.
    """

    model_type: Literal["llm", "image_gen", "music_gen", "sfx_gen"]
    """Model type in the pipeline."""

    model_id: str
    """Model identifier (e.g., 'qwen3-14b', 'sdxl-lightning', 'musicgen-large')."""

    model_path: Optional[str] = None
    """Path to model weights (None = use default registry path)."""

    device: str = "auto"
    """Device placement ('auto', 'cuda', 'cpu')."""

    enable_offload: bool = False
    """Whether to enable CPU offload for large models."""

    load_in_8bit: bool = False
    """Whether to use 8-bit quantization (for LLMs)."""

    max_batch_size: int = 1
    """Maximum batch size for generation."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_type": self.model_type,
            "model_id": self.model_id,
            "model_path": self.model_path,
            "device": self.device,
            "enable_offload": self.enable_offload,
            "load_in_8bit": self.load_in_8bit,
            "max_batch_size": self.max_batch_size,
        }


@dataclass
class PrepPipelineConfig:
    """Configuration for sequential model loading and asset generation.

    Defines the order of model loading and generation parameters.
    Models are loaded sequentially to avoid memory contention.
    """

    campaign_descriptor: CampaignDescriptor
    """Input campaign descriptor."""

    output_dir: str
    """Output directory for generated assets (campaign_id/asset_type/files)."""

    model_sequence: List[ModelLoadConfig] = field(default_factory=list)
    """Sequential model loading order (loaded one at a time, then unloaded)."""

    enable_stub_mode: bool = True
    """If True, use stub/mock implementations (for testing without real models)."""

    def validate(self) -> List[str]:
        """Validate configuration. Returns list of errors."""
        errors = []

        # Validate descriptor
        desc_errors = self.campaign_descriptor.validate()
        for err in desc_errors:
            errors.append(f"campaign_descriptor: {err}")

        if not self.output_dir:
            errors.append("output_dir must not be empty.")

        # Check model sequence has expected types
        model_types = [m.model_type for m in self.model_sequence]
        expected_types = ["llm", "image_gen", "music_gen", "sfx_gen"]

        if not self.enable_stub_mode:
            for expected_type in expected_types:
                if expected_type not in model_types:
                    errors.append(
                        f"model_sequence missing required model_type: {expected_type}"
                    )

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "campaign_descriptor": self.campaign_descriptor.to_dict(),
            "output_dir": self.output_dir,
            "model_sequence": [m.to_dict() for m in self.model_sequence],
            "enable_stub_mode": self.enable_stub_mode,
        }


@dataclass
class GeneratedAsset:
    """Single generated asset record.

    Tracks what was generated, where it's stored, and its metadata.
    """

    asset_id: str
    """Unique asset identifier."""

    asset_type: Literal["npc", "scene", "portrait", "music", "sfx"]
    """Type of asset."""

    semantic_key: str
    """Semantic identifier (e.g., 'npc:vlad:portrait:v1')."""

    file_path: str
    """Relative path to asset file (from campaign output_dir)."""

    file_format: str
    """File format (e.g., 'json', 'png', 'ogg')."""

    content_hash: str = ""
    """SHA256 hash of asset content (empty for stubs)."""

    generation_method: str = "stub"
    """Generation method ('stub', 'llm', 'image_gen', 'music_gen', 'sfx_gen')."""

    status: str = "ok"
    """Asset status: 'ok' (generated) or 'prep_failed' (Spark failure during prep)."""

    failure_mode: Optional[str] = None
    """SparkFailureMode value string if status == 'prep_failed', else None."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata (model used, generation params, etc.)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "semantic_key": self.semantic_key,
            "file_path": self.file_path,
            "file_format": self.file_format,
            "content_hash": self.content_hash,
            "generation_method": self.generation_method,
            "status": self.status,
            "failure_mode": self.failure_mode,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeneratedAsset":
        """Create from dictionary."""
        return cls(
            asset_id=data.get("asset_id", ""),
            asset_type=data.get("asset_type", "npc"),  # type: ignore
            semantic_key=data.get("semantic_key", ""),
            file_path=data.get("file_path", ""),
            file_format=data.get("file_format", ""),
            content_hash=data.get("content_hash", ""),
            generation_method=data.get("generation_method", "stub"),
            status=data.get("status", "ok"),
            failure_mode=data.get("failure_mode", None),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PrepAssetManifest:
    """Manifest of all generated assets for a campaign.

    Saved to campaign_id/asset_manifest.json.
    Provides deterministic record of what assets exist.
    """

    campaign_id: str
    """Campaign identifier."""

    generated_at: str
    """ISO timestamp of generation."""

    assets: List[GeneratedAsset] = field(default_factory=list)
    """List of generated assets (sorted by asset_id for determinism)."""

    def add_asset(self, asset: GeneratedAsset) -> None:
        """Add asset to manifest (maintains sorted order)."""
        self.assets.append(asset)
        self.assets.sort(key=lambda a: a.asset_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "campaign_id": self.campaign_id,
            "generated_at": self.generated_at,
            "assets": [a.to_dict() for a in self.assets],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrepAssetManifest":
        """Create from dictionary."""
        assets = [GeneratedAsset.from_dict(a) for a in data.get("assets", [])]
        return cls(
            campaign_id=data.get("campaign_id", ""),
            generated_at=data.get("generated_at", ""),
            assets=assets,
        )


@dataclass
class PrepPipelineResult:
    """Result of prep pipeline execution.

    Reports success/failure, lists generated assets, and provides execution log.
    """

    status: Literal["success", "failed", "partial"]
    """Overall pipeline status."""

    campaign_id: str
    """Campaign identifier."""

    manifest: Optional[PrepAssetManifest] = None
    """Asset manifest (if generation succeeded)."""

    errors: List[str] = field(default_factory=list)
    """Errors encountered during pipeline execution."""

    warnings: List[str] = field(default_factory=list)
    """Warnings (non-fatal issues)."""

    execution_log: List[str] = field(default_factory=list)
    """Ordered list of execution steps (for debugging/audit)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status,
            "campaign_id": self.campaign_id,
            "manifest": self.manifest.to_dict() if self.manifest else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "execution_log": self.execution_log,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrepPipelineResult":
        """Create from dictionary."""
        manifest_data = data.get("manifest")
        manifest = (
            PrepAssetManifest.from_dict(manifest_data) if manifest_data else None
        )
        return cls(
            status=data.get("status", "failed"),  # type: ignore
            campaign_id=data.get("campaign_id", ""),
            manifest=manifest,
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            execution_log=data.get("execution_log", []),
        )
