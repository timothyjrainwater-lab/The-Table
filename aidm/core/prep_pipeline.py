"""M3 Prep Pipeline — Sequential model loading and asset generation.

Implements the prep pipeline prototype with sequential model loading:
1. Load LLM (Qwen3) → Generate NPCs, encounters, dialogues
2. Unload LLM → Load Image Gen (SDXL Lightning) → Generate portraits, scenes
3. Unload Image Gen → Load Music Gen (ACE-Step) → Generate campaign music
4. Unload Music Gen → Load SFX Library (Curated) → Load sound effects from disk

All models are loaded ONE AT A TIME to avoid memory contention.
After each model finishes generation, it is unloaded before the next model loads.

This is the **prototype** implementation. It demonstrates the architecture with:
- Real sequential orchestration
- Stub/mock model implementations (swappable with real inference)
- Deterministic asset storage

Reference: WO-M3-PREP-01, WO-M3-AUDIO-INT-01
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aidm.schemas.prep_pipeline import (
    PrepPipelineConfig,
    PrepAssetManifest,
    PrepPipelineResult,
    GeneratedAsset,
    ModelLoadConfig,
)


class PrepPipeline:
    """Sequential model loading and asset generation orchestrator.

    Loads models one at a time in deterministic order:
    1. LLM for campaign authoring
    2. Image generator for visual assets
    3. Music generator for campaign tracks
    4. SFX generator for sound effects

    Each model is unloaded before the next model loads to minimize memory usage.
    """

    def __init__(self, config: PrepPipelineConfig):
        """Initialize prep pipeline.

        Args:
            config: Pipeline configuration (includes model sequence, output dir)
        """
        self.config = config
        self.manifest = PrepAssetManifest(
            campaign_id=config.campaign_descriptor.campaign_id,
            generated_at="",  # Set during execution
        )
        self.execution_log: List[str] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def run(self) -> PrepPipelineResult:
        """Execute prep pipeline sequentially.

        Returns:
            PrepPipelineResult with status, manifest, and execution log
        """
        self._log("Starting prep pipeline...")

        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            self.errors.extend(config_errors)
            self._log(f"Configuration validation failed: {len(config_errors)} errors")
            return self._build_result(status="failed")

        # Set generation timestamp (BL-018: inject for determinism)
        self.manifest.generated_at = datetime.now(timezone.utc).isoformat()

        # Ensure output directory exists
        try:
            output_path = Path(self.config.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            self._log(f"Output directory: {self.config.output_dir}")
        except Exception as e:
            self.errors.append(f"Failed to create output directory: {e}")
            return self._build_result(status="failed")

        # Execute model sequence
        for i, model_config in enumerate(self.config.model_sequence):
            self._log(f"Step {i+1}/{len(self.config.model_sequence)}: {model_config.model_type}")

            try:
                # Load model
                self._load_model(model_config)

                # Generate assets
                assets = self._generate_assets(model_config)

                # Store assets
                for asset in assets:
                    self._store_asset(asset)
                    self.manifest.add_asset(asset)

                # Unload model
                self._unload_model(model_config)

            except Exception as e:
                error_msg = f"Step {i+1} ({model_config.model_type}) failed: {e}"
                self.errors.append(error_msg)
                self._log(error_msg)
                return self._build_result(status="partial")

        # Save asset manifest
        try:
            self._save_manifest()
        except Exception as e:
            self.warnings.append(f"Failed to save asset manifest: {e}")

        # Determine final status
        if self.errors:
            status = "partial"
        else:
            status = "success"

        self._log(f"Prep pipeline completed with status: {status}")
        return self._build_result(status=status)  # type: ignore

    # -------------------------------------------------------------------------
    # Model Loading/Unloading
    # -------------------------------------------------------------------------

    def _load_model(self, model_config: ModelLoadConfig) -> None:
        """Load a model into memory.

        In stub mode, this is a no-op. In real mode, would load model weights.

        Args:
            model_config: Model configuration
        """
        if self.config.enable_stub_mode:
            self._log(f"  [STUB] Loading {model_config.model_id} ({model_config.model_type})")
        else:
            self._log(f"  Loading {model_config.model_id} from {model_config.model_path}")
            # Real implementation would load model here:
            # model = load_model(model_config.model_path, device=model_config.device)
            raise NotImplementedError("Real model loading not yet implemented (stub mode only)")

    def _unload_model(self, model_config: ModelLoadConfig) -> None:
        """Unload model from memory to free resources.

        In stub mode, this is a no-op. In real mode, would unload model weights.

        Args:
            model_config: Model configuration
        """
        if self.config.enable_stub_mode:
            self._log(f"  [STUB] Unloading {model_config.model_id}")
        else:
            self._log(f"  Unloading {model_config.model_id}")
            # Real implementation would unload model here:
            # del model; torch.cuda.empty_cache()
            raise NotImplementedError("Real model unloading not yet implemented (stub mode only)")

    # -------------------------------------------------------------------------
    # Asset Generation
    # -------------------------------------------------------------------------

    def _generate_assets(self, model_config: ModelLoadConfig) -> List[GeneratedAsset]:
        """Generate assets using the loaded model.

        In stub mode, creates placeholder assets. In real mode, would call model inference.

        Args:
            model_config: Model configuration

        Returns:
            List of generated assets
        """
        if model_config.model_type == "llm":
            return self._generate_llm_assets(model_config)
        elif model_config.model_type == "image_gen":
            return self._generate_image_assets(model_config)
        elif model_config.model_type == "music_gen":
            return self._generate_music_assets(model_config)
        elif model_config.model_type == "sfx_gen":
            return self._generate_sfx_assets(model_config)
        else:
            raise ValueError(f"Unknown model_type: {model_config.model_type}")

    def _generate_llm_assets(self, model_config: ModelLoadConfig) -> List[GeneratedAsset]:
        """Generate NPCs, encounters, and dialogues using LLM.

        Args:
            model_config: LLM model configuration

        Returns:
            List of generated NPC/encounter/dialogue assets
        """
        assets = []
        descriptor = self.config.campaign_descriptor

        self._log(f"  Generating {descriptor.expected_npcs} NPCs...")

        for i in range(descriptor.expected_npcs):
            npc_id = f"npc_{i+1:03d}"
            asset = GeneratedAsset(
                asset_id=f"{descriptor.campaign_id}:npc:{npc_id}",
                asset_type="npc",
                semantic_key=f"npc:{npc_id}:v1",
                file_path=f"NPCs/{npc_id}.json",
                file_format="json",
                content_hash="",  # Computed during storage
                generation_method="stub" if self.config.enable_stub_mode else "llm",
                metadata={
                    "model_id": model_config.model_id,
                    "genre": descriptor.genre,
                    "story_context": descriptor.story_context,
                },
            )
            assets.append(asset)

        self._log(f"  Generated {len(assets)} NPC assets")
        return assets

    def _generate_image_assets(self, model_config: ModelLoadConfig) -> List[GeneratedAsset]:
        """Generate portraits and scenes using image generation model.

        Args:
            model_config: Image gen model configuration

        Returns:
            List of generated image assets
        """
        assets = []
        descriptor = self.config.campaign_descriptor

        # Generate portraits (one per NPC)
        self._log(f"  Generating {descriptor.expected_npcs} portraits...")
        for i in range(descriptor.expected_npcs):
            portrait_id = f"portrait_{i+1:03d}"
            asset = GeneratedAsset(
                asset_id=f"{descriptor.campaign_id}:portrait:{portrait_id}",
                asset_type="portrait",
                semantic_key=f"npc:{i+1:03d}:portrait:v1",
                file_path=f"Portraits/{portrait_id}.png",
                file_format="png",
                content_hash="",
                generation_method="stub" if self.config.enable_stub_mode else "image_gen",
                metadata={
                    "model_id": model_config.model_id,
                    "dimensions": (512, 512),
                    "genre": descriptor.genre,
                },
            )
            assets.append(asset)

        # Generate scenes
        self._log(f"  Generating {descriptor.expected_scenes} scenes...")
        for i in range(descriptor.expected_scenes):
            scene_id = f"scene_{i+1:03d}"
            asset = GeneratedAsset(
                asset_id=f"{descriptor.campaign_id}:scene:{scene_id}",
                asset_type="scene",
                semantic_key=f"scene:{scene_id}:v1",
                file_path=f"Scenes/{scene_id}.png",
                file_format="png",
                content_hash="",
                generation_method="stub" if self.config.enable_stub_mode else "image_gen",
                metadata={
                    "model_id": model_config.model_id,
                    "dimensions": (1024, 768),
                    "genre": descriptor.genre,
                },
            )
            assets.append(asset)

        self._log(f"  Generated {len(assets)} image assets")
        return assets

    def _generate_music_assets(self, model_config: ModelLoadConfig) -> List[GeneratedAsset]:
        """Generate campaign music tracks using music generation model.

        Uses ACE-Step (generative) for Recommended/Enhanced tiers or curated library (fallback).
        Music generation is Phase 4 of prep pipeline (WO-M3-AUDIO-INT-01).

        Args:
            model_config: Music gen model configuration

        Returns:
            List of generated music assets
        """
        assets = []
        descriptor = self.config.campaign_descriptor

        # Generate music tracks (one per mood tag + one ambient)
        mood_tags = descriptor.mood_tags or ["peaceful", "tense", "combat"]
        self._log(f"  Generating {len(mood_tags)} music tracks...")

        for i, mood in enumerate(mood_tags):
            track_id = f"track_{i+1:03d}_{mood}"
            asset = GeneratedAsset(
                asset_id=f"{descriptor.campaign_id}:music:{track_id}",
                asset_type="music",
                semantic_key=f"music:{mood}:v1",
                file_path=f"Music/{track_id}.ogg",
                file_format="ogg",
                content_hash="",
                generation_method="stub" if self.config.enable_stub_mode else "music_gen",
                metadata={
                    "model_id": model_config.model_id,
                    "mood": mood,
                    "genre": descriptor.genre,
                    "duration_seconds": 60,  # WO-M3-AUDIO-INT-01: 60s clips for 60-120s loops
                    "generated": False,  # Stub tracks are not generated
                },
            )
            assets.append(asset)

        self._log(f"  Generated {len(assets)} music assets")
        return assets

    def _generate_sfx_assets(self, model_config: ModelLoadConfig) -> List[GeneratedAsset]:
        """Load curated SFX library.

        SFX generation is BLOCKED by licensing (no Apache 2.0 / MIT models as of Feb 2026).
        All SFX uses curated library from Sonniss GDC, Freesound CC0, Kenney.nl.

        Args:
            model_config: SFX library configuration

        Returns:
            List of SFX library asset records (stub implementation returns minimal set)
        """
        assets = []
        descriptor = self.config.campaign_descriptor

        # Load curated SFX library (Phase 5 of prep pipeline, WO-M3-AUDIO-INT-01)
        # In stub mode, create minimal placeholder entries
        sfx_keys = [
            "combat:melee:sword:hit",
            "combat:magic:fire:impact",
            "ambient:peaceful:tavern",
            "event:door:open:wood",
            "event:dice:roll",
        ]
        self._log(f"  Loading {len(sfx_keys)} curated SFX keys (stub)...")

        for i, sfx_key in enumerate(sfx_keys):
            sfx_id = f"sfx_{i+1:03d}_{sfx_key.replace(':', '_')}"
            asset = GeneratedAsset(
                asset_id=f"{descriptor.campaign_id}:sfx:{sfx_id}",
                asset_type="sfx",
                semantic_key=f"sfx:{sfx_key}:v1",
                file_path=f"SFX/{sfx_id}.ogg",
                file_format="ogg",
                content_hash="",
                generation_method="curated",  # WO-M3-AUDIO-INT-01: curated library only
                metadata={
                    "semantic_key": sfx_key,
                    "curated_source": "Sonniss GDC 2024",
                    "duration_seconds": 2,
                },
            )
            assets.append(asset)

        self._log(f"  Loaded {len(assets)} curated SFX assets")
        return assets

    # -------------------------------------------------------------------------
    # Asset Storage
    # -------------------------------------------------------------------------

    def _store_asset(self, asset: GeneratedAsset) -> None:
        """Store generated asset to filesystem.

        Creates directory structure and writes asset file.
        Computes content hash for stored file.

        Args:
            asset: Asset to store
        """
        output_path = Path(self.config.output_dir)
        asset_path = output_path / asset.file_path

        # Ensure parent directory exists
        asset_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate stub content based on asset type
        content = self._generate_stub_content(asset)

        # Write asset file
        if asset.file_format == "json":
            with open(asset_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, sort_keys=True)
                f.write("\n")
        else:
            # For binary assets (images, audio), write placeholder bytes
            with open(asset_path, "wb") as f:
                f.write(content)  # type: ignore

        # Compute content hash
        asset.content_hash = self._compute_file_hash(asset_path)

        self._log(f"    Stored {asset.asset_id} → {asset.file_path}")

    def _generate_stub_content(self, asset: GeneratedAsset) -> Any:
        """Generate stub content for asset.

        In stub mode, creates minimal valid content. In real mode, would use actual model output.

        Args:
            asset: Asset to generate content for

        Returns:
            Content (dict for JSON, bytes for binary)
        """
        if asset.asset_type == "npc":
            # Stub NPC JSON
            npc_id = asset.semantic_key.split(":")[1]
            return {
                "npc_id": npc_id,
                "name": f"NPC {npc_id.upper()}",
                "description": f"A character from the {self.config.campaign_descriptor.genre} campaign.",
                "traits": ["mysterious", "helpful"],
                "dialogue": [
                    {"line": "Greetings, traveler."},
                    {"line": "What brings you to these parts?"},
                ],
            }

        elif asset.asset_type in ("portrait", "scene"):
            # Stub image (1x1 PNG placeholder)
            # PNG magic number + minimal IHDR chunk
            return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"

        elif asset.asset_type in ("music", "sfx"):
            # Stub audio (minimal OGG Vorbis header)
            return b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00"

        else:
            # Fallback: empty bytes
            return b""

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content.

        Args:
            file_path: Path to file

        Returns:
            Hex-encoded SHA256 hash
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def _save_manifest(self) -> None:
        """Save asset manifest to campaign output directory."""
        output_path = Path(self.config.output_dir)
        manifest_path = output_path / "asset_manifest.json"

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest.to_dict(), f, indent=2, sort_keys=True)
            f.write("\n")

        self._log(f"Saved asset manifest: {manifest_path}")

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _log(self, message: str) -> None:
        """Append message to execution log.

        Args:
            message: Log message
        """
        self.execution_log.append(message)

    def _build_result(self, status: str) -> PrepPipelineResult:
        """Build final pipeline result.

        Args:
            status: Pipeline status

        Returns:
            PrepPipelineResult with manifest and logs
        """
        return PrepPipelineResult(
            status=status,  # type: ignore
            campaign_id=self.config.campaign_descriptor.campaign_id,
            manifest=self.manifest if status != "failed" else None,
            errors=self.errors,
            warnings=self.warnings,
            execution_log=self.execution_log,
        )


# ═════════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═════════════════════════════════════════════════════════════════════════


def run_prep_pipeline(config: PrepPipelineConfig) -> PrepPipelineResult:
    """Convenience function to execute prep pipeline.

    Args:
        config: Pipeline configuration

    Returns:
        PrepPipelineResult with status and manifest
    """
    pipeline = PrepPipeline(config)
    return pipeline.run()
