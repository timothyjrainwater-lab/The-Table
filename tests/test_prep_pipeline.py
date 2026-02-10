"""Tests for M3 Prep Pipeline — Sequential model loading and asset generation.

Tests the prep pipeline prototype including:
- Schema validation (CampaignDescriptor, PrepPipelineConfig, etc.)
- Sequential model loading orchestration
- Asset generation (stub mode)
- Asset storage with deterministic paths
- Asset manifest generation and serialization
- Error handling and partial failure modes

Reference: WO-M3-PREP-01
"""

import json
import tempfile
from pathlib import Path

from aidm.schemas.prep_pipeline import (
    CampaignDescriptor,
    ModelLoadConfig,
    PrepPipelineConfig,
    PrepAssetManifest,
    GeneratedAsset,
    PrepPipelineResult,
)
from aidm.core.prep_pipeline import PrepPipeline, run_prep_pipeline


# ═════════════════════════════════════════════════════════════════════════
# Tier-1: Schema Validation Tests
# ═════════════════════════════════════════════════════════════════════════


def test_campaign_descriptor_validation():
    """CampaignDescriptor validates required fields."""
    # Valid descriptor
    desc = CampaignDescriptor(
        campaign_id="camp_001",
        name="The Haunted Manor",
        genre="gothic horror",
        story_context="A haunted manor with undead inhabitants",
    )
    errors = desc.validate()
    assert errors == [], f"Expected no errors, got: {errors}"

    # Invalid: missing fields
    desc_invalid = CampaignDescriptor(
        campaign_id="",  # Empty campaign_id
        name="",  # Empty name
        genre="",  # Empty genre
        story_context="",  # Empty story context
    )
    errors = desc_invalid.validate()
    assert len(errors) == 4, f"Expected 4 errors, got {len(errors)}"
    assert any("campaign_id" in e for e in errors)
    assert any("name" in e for e in errors)
    assert any("genre" in e for e in errors)
    assert any("story_context" in e for e in errors)


def test_campaign_descriptor_serialization():
    """CampaignDescriptor serializes/deserializes correctly."""
    desc = CampaignDescriptor(
        campaign_id="camp_001",
        name="Test Campaign",
        genre="fantasy",
        story_context="Epic adventure",
        expected_npcs=5,
        expected_scenes=3,
        mood_tags=["heroic", "epic"],
    )

    # Serialize
    data = desc.to_dict()
    assert data["campaign_id"] == "camp_001"
    assert data["name"] == "Test Campaign"
    assert data["expected_npcs"] == 5
    assert data["mood_tags"] == ["heroic", "epic"]

    # Deserialize
    desc2 = CampaignDescriptor.from_dict(data)
    assert desc2.campaign_id == desc.campaign_id
    assert desc2.name == desc.name
    assert desc2.expected_npcs == desc.expected_npcs
    assert desc2.mood_tags == desc.mood_tags


def test_model_load_config_serialization():
    """ModelLoadConfig serializes correctly."""
    config = ModelLoadConfig(
        model_type="llm",
        model_id="qwen3-14b",
        model_path="/models/qwen3",
        device="cuda",
        enable_offload=True,
        load_in_8bit=True,
    )

    data = config.to_dict()
    assert data["model_type"] == "llm"
    assert data["model_id"] == "qwen3-14b"
    assert data["enable_offload"] is True
    assert data["load_in_8bit"] is True


def test_prep_pipeline_config_validation():
    """PrepPipelineConfig validates required fields."""
    desc = CampaignDescriptor(
        campaign_id="camp_001",
        name="Test",
        genre="fantasy",
        story_context="Adventure",
    )

    # Valid config (stub mode)
    config = PrepPipelineConfig(
        campaign_descriptor=desc,
        output_dir="/tmp/campaign_001",
        enable_stub_mode=True,
        model_sequence=[],  # Empty is OK in stub mode
    )
    errors = config.validate()
    assert errors == [], f"Expected no errors in stub mode, got: {errors}"

    # Invalid: missing output_dir
    config_invalid = PrepPipelineConfig(
        campaign_descriptor=desc,
        output_dir="",  # Empty output_dir
        enable_stub_mode=True,
    )
    errors = config_invalid.validate()
    assert len(errors) >= 1
    assert any("output_dir" in e for e in errors)


def test_generated_asset_serialization():
    """GeneratedAsset serializes/deserializes correctly."""
    asset = GeneratedAsset(
        asset_id="camp_001:npc:npc_001",
        asset_type="npc",
        semantic_key="npc:npc_001:v1",
        file_path="NPCs/npc_001.json",
        file_format="json",
        content_hash="abc123",
        generation_method="llm",
        metadata={"model_id": "qwen3-14b"},
    )

    # Serialize
    data = asset.to_dict()
    assert data["asset_id"] == "camp_001:npc:npc_001"
    assert data["asset_type"] == "npc"
    assert data["metadata"]["model_id"] == "qwen3-14b"

    # Deserialize
    asset2 = GeneratedAsset.from_dict(data)
    assert asset2.asset_id == asset.asset_id
    assert asset2.asset_type == asset.asset_type
    assert asset2.metadata == asset.metadata


def test_prep_asset_manifest_sorting():
    """PrepAssetManifest maintains sorted asset list."""
    manifest = PrepAssetManifest(
        campaign_id="camp_001",
        generated_at="2025-01-01T00:00:00Z",
    )

    # Add assets out of order
    asset3 = GeneratedAsset(
        asset_id="camp_001:npc:npc_003",
        asset_type="npc",
        semantic_key="npc:npc_003:v1",
        file_path="NPCs/npc_003.json",
        file_format="json",
    )
    asset1 = GeneratedAsset(
        asset_id="camp_001:npc:npc_001",
        asset_type="npc",
        semantic_key="npc:npc_001:v1",
        file_path="NPCs/npc_001.json",
        file_format="json",
    )
    asset2 = GeneratedAsset(
        asset_id="camp_001:npc:npc_002",
        asset_type="npc",
        semantic_key="npc:npc_002:v1",
        file_path="NPCs/npc_002.json",
        file_format="json",
    )

    manifest.add_asset(asset3)
    manifest.add_asset(asset1)
    manifest.add_asset(asset2)

    # Assets should be sorted by asset_id
    assert manifest.assets[0].asset_id == "camp_001:npc:npc_001"
    assert manifest.assets[1].asset_id == "camp_001:npc:npc_002"
    assert manifest.assets[2].asset_id == "camp_001:npc:npc_003"


def test_prep_pipeline_result_serialization():
    """PrepPipelineResult serializes/deserializes correctly."""
    manifest = PrepAssetManifest(
        campaign_id="camp_001",
        generated_at="2025-01-01T00:00:00Z",
        assets=[],
    )

    result = PrepPipelineResult(
        status="success",
        campaign_id="camp_001",
        manifest=manifest,
        errors=[],
        warnings=["Test warning"],
        execution_log=["Step 1", "Step 2"],
    )

    # Serialize
    data = result.to_dict()
    assert data["status"] == "success"
    assert data["warnings"] == ["Test warning"]
    assert data["execution_log"] == ["Step 1", "Step 2"]

    # Deserialize
    result2 = PrepPipelineResult.from_dict(data)
    assert result2.status == result.status
    assert result2.warnings == result.warnings
    assert result2.execution_log == result.execution_log


# ═════════════════════════════════════════════════════════════════════════
# Tier-1: Pipeline Execution Tests
# ═════════════════════════════════════════════════════════════════════════


def test_prep_pipeline_stub_mode_basic():
    """PrepPipeline executes successfully in stub mode with basic config."""
    desc = CampaignDescriptor(
        campaign_id="camp_test_001",
        name="Test Campaign",
        genre="fantasy",
        story_context="A test adventure",
        expected_npcs=2,
        expected_scenes=1,
        mood_tags=["heroic"],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PrepPipelineConfig(
            campaign_descriptor=desc,
            output_dir=tmpdir,
            enable_stub_mode=True,
            model_sequence=[
                ModelLoadConfig(model_type="llm", model_id="stub-llm"),
                ModelLoadConfig(model_type="image_gen", model_id="stub-image"),
                ModelLoadConfig(model_type="music_gen", model_id="stub-music"),
                ModelLoadConfig(model_type="sfx_gen", model_id="stub-sfx"),
            ],
        )

        result = run_prep_pipeline(config)

        # Check result
        assert result.status == "success", f"Expected success, got: {result.status}"
        assert result.campaign_id == "camp_test_001"
        assert result.errors == []
        assert result.manifest is not None

        # Check manifest
        manifest = result.manifest
        assert manifest.campaign_id == "camp_test_001"
        assert len(manifest.assets) > 0

        # Check asset types
        asset_types = [a.asset_type for a in manifest.assets]
        assert "npc" in asset_types
        assert "portrait" in asset_types
        assert "scene" in asset_types
        assert "music" in asset_types
        assert "sfx" in asset_types

        # Check execution log
        assert len(result.execution_log) > 0
        assert any("Step 1" in log for log in result.execution_log)


def test_prep_pipeline_generates_correct_asset_count():
    """PrepPipeline generates correct number of assets based on descriptor."""
    desc = CampaignDescriptor(
        campaign_id="camp_test_002",
        name="Asset Count Test",
        genre="sci-fi",
        story_context="Space adventure",
        expected_npcs=3,
        expected_scenes=2,
        mood_tags=["tense", "mysterious"],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PrepPipelineConfig(
            campaign_descriptor=desc,
            output_dir=tmpdir,
            enable_stub_mode=True,
            model_sequence=[
                ModelLoadConfig(model_type="llm", model_id="stub-llm"),
                ModelLoadConfig(model_type="image_gen", model_id="stub-image"),
                ModelLoadConfig(model_type="music_gen", model_id="stub-music"),
                ModelLoadConfig(model_type="sfx_gen", model_id="stub-sfx"),
            ],
        )

        result = run_prep_pipeline(config)

        # Count assets by type
        npcs = [a for a in result.manifest.assets if a.asset_type == "npc"]
        portraits = [a for a in result.manifest.assets if a.asset_type == "portrait"]
        scenes = [a for a in result.manifest.assets if a.asset_type == "scene"]
        music = [a for a in result.manifest.assets if a.asset_type == "music"]
        sfx = [a for a in result.manifest.assets if a.asset_type == "sfx"]

        assert len(npcs) == 3, f"Expected 3 NPCs, got {len(npcs)}"
        assert len(portraits) == 3, f"Expected 3 portraits (1 per NPC), got {len(portraits)}"
        assert len(scenes) == 2, f"Expected 2 scenes, got {len(scenes)}"
        assert len(music) == 2, f"Expected 2 music tracks (mood tags), got {len(music)}"
        assert len(sfx) == 5, f"Expected 5 SFX (curated semantic keys), got {len(sfx)}"


def test_prep_pipeline_creates_directory_structure():
    """PrepPipeline creates correct directory structure for assets."""
    desc = CampaignDescriptor(
        campaign_id="camp_test_003",
        name="Directory Test",
        genre="fantasy",
        story_context="Test",
        expected_npcs=1,
        expected_scenes=1,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "campaign_test_003"
        config = PrepPipelineConfig(
            campaign_descriptor=desc,
            output_dir=str(output_dir),
            enable_stub_mode=True,
            model_sequence=[
                ModelLoadConfig(model_type="llm", model_id="stub-llm"),
                ModelLoadConfig(model_type="image_gen", model_id="stub-image"),
                ModelLoadConfig(model_type="music_gen", model_id="stub-music"),
                ModelLoadConfig(model_type="sfx_gen", model_id="stub-sfx"),
            ],
        )

        result = run_prep_pipeline(config)

        # Check directories exist
        assert output_dir.exists()
        assert (output_dir / "NPCs").exists()
        assert (output_dir / "Portraits").exists()
        assert (output_dir / "Scenes").exists()
        assert (output_dir / "Music").exists()
        assert (output_dir / "SFX").exists()

        # Check manifest file exists
        manifest_path = output_dir / "asset_manifest.json"
        assert manifest_path.exists()

        # Verify manifest is valid JSON
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)
        assert manifest_data["campaign_id"] == "camp_test_003"
        assert "assets" in manifest_data


def test_prep_pipeline_stores_assets_with_content():
    """PrepPipeline stores asset files with content."""
    desc = CampaignDescriptor(
        campaign_id="camp_test_004",
        name="Content Test",
        genre="fantasy",
        story_context="Test",
        expected_npcs=1,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PrepPipelineConfig(
            campaign_descriptor=desc,
            output_dir=tmpdir,
            enable_stub_mode=True,
            model_sequence=[
                ModelLoadConfig(model_type="llm", model_id="stub-llm"),
            ],
        )

        result = run_prep_pipeline(config)

        # Find NPC asset
        npc_assets = [a for a in result.manifest.assets if a.asset_type == "npc"]
        assert len(npc_assets) == 1

        npc_asset = npc_assets[0]
        npc_path = Path(tmpdir) / npc_asset.file_path

        # Check file exists
        assert npc_path.exists()

        # Check file has JSON content
        with open(npc_path, "r") as f:
            npc_data = json.load(f)

        assert "npc_id" in npc_data
        assert "name" in npc_data
        assert "dialogue" in npc_data
        assert isinstance(npc_data["dialogue"], list)


def test_prep_pipeline_computes_content_hashes():
    """PrepPipeline computes content hashes for stored assets."""
    desc = CampaignDescriptor(
        campaign_id="camp_test_005",
        name="Hash Test",
        genre="fantasy",
        story_context="Test",
        expected_npcs=1,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PrepPipelineConfig(
            campaign_descriptor=desc,
            output_dir=tmpdir,
            enable_stub_mode=True,
            model_sequence=[
                ModelLoadConfig(model_type="llm", model_id="stub-llm"),
            ],
        )

        result = run_prep_pipeline(config)

        # Check all assets have non-empty content hashes
        for asset in result.manifest.assets:
            assert asset.content_hash != "", f"Asset {asset.asset_id} has empty content_hash"
            assert len(asset.content_hash) == 64, f"Hash should be 64 chars (SHA256), got {len(asset.content_hash)}"


def test_prep_pipeline_handles_configuration_validation_error():
    """PrepPipeline fails gracefully on invalid configuration."""
    # Invalid descriptor (empty required fields)
    desc = CampaignDescriptor(
        campaign_id="",  # Invalid
        name="",  # Invalid
        genre="",  # Invalid
        story_context="",  # Invalid
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PrepPipelineConfig(
            campaign_descriptor=desc,
            output_dir=tmpdir,
            enable_stub_mode=True,
        )

        result = run_prep_pipeline(config)

        # Should fail with errors
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert result.manifest is None


def test_prep_pipeline_sequential_execution_logged():
    """PrepPipeline logs sequential model loading steps."""
    desc = CampaignDescriptor(
        campaign_id="camp_test_006",
        name="Logging Test",
        genre="fantasy",
        story_context="Test",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PrepPipelineConfig(
            campaign_descriptor=desc,
            output_dir=tmpdir,
            enable_stub_mode=True,
            model_sequence=[
                ModelLoadConfig(model_type="llm", model_id="stub-llm"),
                ModelLoadConfig(model_type="image_gen", model_id="stub-image"),
                ModelLoadConfig(model_type="music_gen", model_id="stub-music"),
                ModelLoadConfig(model_type="sfx_gen", model_id="stub-sfx"),
            ],
        )

        result = run_prep_pipeline(config)

        # Check execution log contains sequential steps
        log = "\n".join(result.execution_log)
        assert "Step 1/4: llm" in log
        assert "Step 2/4: image_gen" in log
        assert "Step 3/4: music_gen" in log
        assert "Step 4/4: sfx_gen" in log

        # Check loading/unloading messages
        assert "Loading stub-llm" in log
        assert "Unloading stub-llm" in log
        assert "Loading stub-image" in log
        assert "Unloading stub-image" in log


def test_prep_pipeline_deterministic_asset_manifest():
    """PrepPipeline produces deterministic asset manifest across runs."""
    desc = CampaignDescriptor(
        campaign_id="camp_test_007",
        name="Determinism Test",
        genre="fantasy",
        story_context="Test adventure",
        expected_npcs=2,
    )

    with tempfile.TemporaryDirectory() as tmpdir1:
        with tempfile.TemporaryDirectory() as tmpdir2:
            config1 = PrepPipelineConfig(
                campaign_descriptor=desc,
                output_dir=tmpdir1,
                enable_stub_mode=True,
                model_sequence=[
                    ModelLoadConfig(model_type="llm", model_id="stub-llm"),
                ],
            )

            config2 = PrepPipelineConfig(
                campaign_descriptor=desc,
                output_dir=tmpdir2,
                enable_stub_mode=True,
                model_sequence=[
                    ModelLoadConfig(model_type="llm", model_id="stub-llm"),
                ],
            )

            result1 = run_prep_pipeline(config1)
            result2 = run_prep_pipeline(config2)

            # Manifests should have same structure
            assert len(result1.manifest.assets) == len(result2.manifest.assets)

            # Asset IDs should match (sorted order)
            ids1 = [a.asset_id for a in result1.manifest.assets]
            ids2 = [a.asset_id for a in result2.manifest.assets]
            assert ids1 == ids2

            # Semantic keys should match
            keys1 = [a.semantic_key for a in result1.manifest.assets]
            keys2 = [a.semantic_key for a in result2.manifest.assets]
            assert keys1 == keys2


# ═════════════════════════════════════════════════════════════════════════
# Tier-2: Edge Cases and Error Handling
# ═════════════════════════════════════════════════════════════════════════


def test_prep_pipeline_empty_mood_tags_generates_default_music():
    """PrepPipeline generates default music track when mood_tags is empty."""
    desc = CampaignDescriptor(
        campaign_id="camp_test_008",
        name="No Mood Tags",
        genre="fantasy",
        story_context="Test",
        mood_tags=[],  # Empty
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PrepPipelineConfig(
            campaign_descriptor=desc,
            output_dir=tmpdir,
            enable_stub_mode=True,
            model_sequence=[
                ModelLoadConfig(model_type="music_gen", model_id="stub-music"),
            ],
        )

        result = run_prep_pipeline(config)

        # Should generate at least 1 music track (ambient default)
        music_assets = [a for a in result.manifest.assets if a.asset_type == "music"]
        assert len(music_assets) >= 1


def test_prep_pipeline_partial_model_sequence():
    """PrepPipeline works with partial model sequence (only some models)."""
    desc = CampaignDescriptor(
        campaign_id="camp_test_009",
        name="Partial Sequence",
        genre="fantasy",
        story_context="Test",
        expected_npcs=1,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        # Only LLM and Image Gen (skip Music and SFX)
        config = PrepPipelineConfig(
            campaign_descriptor=desc,
            output_dir=tmpdir,
            enable_stub_mode=True,
            model_sequence=[
                ModelLoadConfig(model_type="llm", model_id="stub-llm"),
                ModelLoadConfig(model_type="image_gen", model_id="stub-image"),
            ],
        )

        result = run_prep_pipeline(config)

        # Should succeed
        assert result.status == "success"

        # Should have NPC and image assets, but no music/sfx
        asset_types = [a.asset_type for a in result.manifest.assets]
        assert "npc" in asset_types
        assert "portrait" in asset_types
        assert "music" not in asset_types
        assert "sfx" not in asset_types
