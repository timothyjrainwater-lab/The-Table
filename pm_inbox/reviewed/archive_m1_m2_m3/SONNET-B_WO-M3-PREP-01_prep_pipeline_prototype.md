# WO-M3-PREP-01: Prep Pipeline Prototype — Sequential Model Loading

**Agent:** Sonnet B
**Work Order:** WO-M3-PREP-01
**Date:** 2026-02-11
**Status:** Complete

## Summary

Implemented the **M3 Prep Pipeline Prototype** to demonstrate sequential model loading architecture during campaign preparation. The pipeline loads models ONE AT A TIME (LLM → Image Gen → Music Gen → SFX Gen), unloading each before loading the next to minimize memory usage. This proves the offline generation process for M3 Immersion Layer integration.

## Deliverables

### 1. Schemas (`aidm/schemas/prep_pipeline.py`, 394 lines)

- **CampaignDescriptor**: Input format for prep pipeline (campaign metadata + story context)
  - Fields: campaign_id, name, genre, story_context, expected_npcs, expected_scenes, mood_tags
  - Validation: Ensures all required fields are non-empty
  - Serialization: to_dict()/from_dict() for JSON persistence

- **ModelLoadConfig**: Configuration for loading a single model
  - Fields: model_type (llm/image_gen/music_gen/sfx_gen), model_id, model_path, device, enable_offload, load_in_8bit
  - Defines loading parameters for each model in sequence

- **PrepPipelineConfig**: Full pipeline configuration
  - Fields: campaign_descriptor, output_dir, model_sequence, enable_stub_mode
  - Validation: Checks for required model types when stub mode disabled
  - Sequential loading order enforced by model_sequence list

- **GeneratedAsset**: Single asset record
  - Fields: asset_id, asset_type (npc/portrait/scene/music/sfx), semantic_key, file_path, file_format, content_hash, generation_method, metadata
  - Tracks what was generated, where stored, and generation metadata

- **PrepAssetManifest**: Manifest of all campaign assets
  - Maintains sorted asset list (by asset_id for determinism)
  - Saved to campaign_id/asset_manifest.json
  - Provides deterministic record of generated assets

- **PrepPipelineResult**: Pipeline execution result
  - Fields: status (success/failed/partial), manifest, errors, warnings, execution_log
  - Complete audit trail of what was generated and any issues encountered

### 2. Core Pipeline (`aidm/core/prep_pipeline.py`, 549 lines)

- **PrepPipeline class**: Sequential orchestration engine
  - Executes model_sequence in deterministic order
  - Loads each model, generates assets, unloads model before next
  - Creates campaign_id/asset_type/files directory structure

- **Model loading/unloading** (stub mode):
  - _load_model(): Mock model loading (real implementation swappable)
  - _unload_model(): Mock model unloading (real implementation swappable)
  - Logs all load/unload operations for audit trail

- **Asset generation** (per model type):
  - LLM assets: NPCs with JSON format (name, description, traits, dialogue)
  - Image assets: Portraits (1 per NPC) + scenes (PNG format)
  - Music assets: Tracks based on mood_tags (OGG format, 2-minute loops)
  - SFX assets: Basic set (sword_clash, door_open, footsteps, ambient_wind, OGG format)

- **Asset storage**:
  - Deterministic file paths: campaign_id/asset_type/filename
  - Content hash computation (SHA256) for each asset
  - Stub content generation (valid JSON for NPCs, minimal PNG/OGG headers for media)

- **Manifest persistence**:
  - Saves asset_manifest.json after all generation complete
  - JSON with sorted keys for deterministic serialization
  - Lists all assets with metadata (asset_id, type, path, hash, generation method)

- **Error handling**:
  - Validates configuration before execution
  - Returns partial status on mid-pipeline failure
  - Logs all steps for debugging/audit

### 3. Tests (`tests/test_prep_pipeline.py`, 17 tests, 100% pass rate)

**Tier-1: Schema Validation (7 tests)**
- test_campaign_descriptor_validation: Required field validation
- test_campaign_descriptor_serialization: to_dict()/from_dict() roundtrip
- test_model_load_config_serialization: Config serialization
- test_prep_pipeline_config_validation: Pipeline config validation
- test_generated_asset_serialization: Asset serialization
- test_prep_asset_manifest_sorting: Manifest maintains sorted order
- test_prep_pipeline_result_serialization: Result serialization

**Tier-1: Pipeline Execution (8 tests)**
- test_prep_pipeline_stub_mode_basic: Full pipeline execution success
- test_prep_pipeline_generates_correct_asset_count: Asset counts match descriptor
- test_prep_pipeline_creates_directory_structure: Correct directory layout
- test_prep_pipeline_stores_assets_with_content: Assets have valid content
- test_prep_pipeline_computes_content_hashes: All assets have SHA256 hashes
- test_prep_pipeline_handles_configuration_validation_error: Graceful failure on invalid config
- test_prep_pipeline_sequential_execution_logged: Sequential steps logged correctly
- test_prep_pipeline_deterministic_asset_manifest: Same descriptor → same manifest structure

**Tier-2: Edge Cases (2 tests)**
- test_prep_pipeline_empty_mood_tags_generates_default_music: Fallback to ambient music
- test_prep_pipeline_partial_model_sequence: Works with subset of models

### 4. Demo Script (`scripts/prep_pipeline_demo.py`, 219 lines)

- Runnable demonstration of prep pipeline
- Creates sample campaign descriptor ("The Crimson Tower", dark fantasy genre)
- Configures 4-model sequence (Qwen3, SDXL Lightning, MusicGen, AudioGen)
- Executes pipeline in stub mode
- Displays execution log and generated assets
- Inspects sample NPC asset content
- Output: artifacts/demo_campaign_001/ with full directory structure

**Demo execution verified:**
- Successfully created campaign assets in artifacts/demo_campaign_001/
- Generated 3 NPCs, 3 portraits, 2 scenes, 3 music tracks, 4 SFX
- Saved manifest with 15 total assets
- All assets have deterministic paths and SHA256 hashes

## Acceptance Criteria Met

✓ **Sequential model loading**: Models load in order (LLM → Image → Music → SFX)
✓ **Asset generation**: Stub implementations for all 4 model types
✓ **Asset storage**: Deterministic paths (campaign_id/asset_type/files)
✓ **Manifest generation**: JSON manifest with sorted keys
✓ **Full test coverage**: 17 tests, 100% pass rate
✓ **Runnable demo**: Demo script successfully executes end-to-end
✓ **No regressions**: Full test suite passes (1777 tests, 7 pre-existing failures)

## Test Count Impact

- **Before**: 1744 tests (per PSD line 12)
- **After**: 1777 tests (33 new tests: 17 prep_pipeline + 16 other new tests since last PSD update)
- **Runtime**: ~8 seconds (no significant change)
- **Status**: 1770 passing, 7 pre-existing failures in Spark adapter tests (unrelated to this work)

## Files Added

### Schemas
- `aidm/schemas/prep_pipeline.py` (394 lines)

### Core
- `aidm/core/prep_pipeline.py` (549 lines)

### Tests
- `tests/test_prep_pipeline.py` (17 tests, 506 lines)

### Scripts
- `scripts/prep_pipeline_demo.py` (219 lines)

## Architecture Notes

### Sequential Model Loading

The pipeline demonstrates the **load → generate → unload** pattern:

```python
for model_config in model_sequence:
    # 1. Load model into memory
    _load_model(model_config)

    # 2. Generate assets using loaded model
    assets = _generate_assets(model_config)

    # 3. Store assets to filesystem
    for asset in assets:
        _store_asset(asset)

    # 4. Unload model to free memory
    _unload_model(model_config)
```

This ensures **only ONE model is in memory at a time**, critical for systems with limited VRAM.

### Stub vs Real Mode

- **Stub mode** (enable_stub_mode=True): Uses mock implementations for testing without real models
- **Real mode** (enable_stub_mode=False): Would load actual model weights (not implemented in prototype)
- Architecture is **swappable**: Real inference can replace stubs without changing pipeline structure

### Asset Storage Structure

```
campaign_id/
  NPCs/
    npc_001.json
    npc_002.json
  Portraits/
    portrait_001.png
    portrait_002.png
  Scenes/
    scene_001.png
  Music/
    track_001_dark.ogg
    track_002_ominous.ogg
  SFX/
    sfx_001_sword_clash.ogg
    sfx_002_door_open.ogg
  asset_manifest.json
```

### Deterministic Asset IDs

Asset IDs follow format: `campaign_id:asset_type:identifier`

Examples:
- `demo_campaign_001:npc:npc_001`
- `demo_campaign_001:portrait:portrait_001`
- `demo_campaign_001:music:track_001_dark`

Semantic keys follow similar pattern for cross-referencing.

## Integration with Existing Systems

- **Builds on PrepOrchestrator** (M2): Uses similar job orchestration patterns
- **Complements AssetStore** (M2): Generates assets that AssetStore can manage
- **Feeds M3 Immersion Layer**: Generated assets ready for immersion system consumption
- **BL-018 compliant**: Timestamps injected (manifest.generated_at set explicitly)
- **No LLM at runtime**: All generation happens during prep (offline)

## Next Steps (M3 Integration)

1. **Real model loading**: Replace stub implementations with actual model inference
   - LLM: Integrate Qwen3 via transformers
   - Image: Integrate SDXL Lightning via diffusers
   - Music: Integrate MusicGen via audiocraft
   - SFX: Integrate AudioGen/Tango 2

2. **M3 Immersion integration**: Wire generated assets to immersion layer
   - NPC JSON → NpcCard in SessionBundle
   - Portraits → ImageResult in immersion pipeline
   - Music/SFX → AudioTrack in SceneAudioState

3. **Hardware-aware model selection**: Use ModelSelector to choose models based on HardwareCapabilities

4. **Progress tracking**: Add progress callbacks for long-running generation

## Blockers / Issues

None. Work order complete.

## References

- Work Order: WO-M3-PREP-01
- Acceptance Criteria: Sequential model loading, asset generation/storage, manifest generation
- Dependencies: WO-M1-RUNTIME-06 (complete)
- Blocks: M3 Immersion Layer integration

---

**Deliverable routing**: This document is written to `pm_inbox/` for PM (Aegis) review per AGENT_DEVELOPMENT_GUIDELINES.md Section 10 routing rules.
