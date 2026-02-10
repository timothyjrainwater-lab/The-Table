"""Prep Pipeline Demo — Runnable demonstration of M3 prep pipeline prototype.

This script demonstrates the sequential model loading architecture:
1. Create a campaign descriptor
2. Configure sequential model loading (LLM → Image Gen → Music Gen → SFX Gen)
3. Execute prep pipeline in stub mode
4. Inspect generated assets

Usage:
    python scripts/prep_pipeline_demo.py

Output:
    - Console output showing sequential model loading
    - Generated assets in artifacts/demo_campaign_001/
    - Asset manifest in artifacts/demo_campaign_001/asset_manifest.json

Reference: WO-M3-PREP-01
"""

from pathlib import Path

from aidm.schemas.prep_pipeline import (
    CampaignDescriptor,
    ModelLoadConfig,
    PrepPipelineConfig,
)
from aidm.core.prep_pipeline import run_prep_pipeline


def main():
    """Execute prep pipeline demo."""
    print("=" * 70)
    print("M3 PREP PIPELINE PROTOTYPE — DEMO")
    print("=" * 70)
    print()

    # -------------------------------------------------------------------------
    # Step 1: Create Campaign Descriptor
    # -------------------------------------------------------------------------
    print("[STEP 1] Creating campaign descriptor...")

    descriptor = CampaignDescriptor(
        campaign_id="demo_campaign_001",
        name="The Crimson Tower",
        genre="dark fantasy",
        story_context=(
            "An ancient tower shrouded in mystery. "
            "The party must ascend its levels, facing undead guardians "
            "and uncovering the secrets of the crimson mage who built it."
        ),
        expected_npcs=3,
        expected_scenes=2,
        expected_encounters=1,
        mood_tags=["dark", "ominous", "mysterious"],
    )

    print(f"  Campaign: {descriptor.name}")
    print(f"  Genre: {descriptor.genre}")
    print(f"  Expected NPCs: {descriptor.expected_npcs}")
    print(f"  Expected Scenes: {descriptor.expected_scenes}")
    print(f"  Mood Tags: {', '.join(descriptor.mood_tags)}")
    print()

    # -------------------------------------------------------------------------
    # Step 2: Configure Sequential Model Loading
    # -------------------------------------------------------------------------
    print("[STEP 2] Configuring sequential model loading...")

    # Define model sequence (stub mode for demo)
    model_sequence = [
        ModelLoadConfig(
            model_type="llm",
            model_id="qwen3-14b",
            device="auto",
        ),
        ModelLoadConfig(
            model_type="image_gen",
            model_id="sdxl-lightning",
            device="auto",
        ),
        ModelLoadConfig(
            model_type="music_gen",
            model_id="musicgen-large",
            device="auto",
        ),
        ModelLoadConfig(
            model_type="sfx_gen",
            model_id="audiogen-medium",
            device="auto",
        ),
    ]

    print("  Model Sequence:")
    for i, model in enumerate(model_sequence, 1):
        print(f"    {i}. {model.model_type.upper()} - {model.model_id}")
    print()

    # Configure output directory
    output_dir = Path(__file__).parent.parent / "artifacts" / descriptor.campaign_id
    print(f"  Output Directory: {output_dir}")
    print()

    # Create pipeline config
    config = PrepPipelineConfig(
        campaign_descriptor=descriptor,
        output_dir=str(output_dir),
        model_sequence=model_sequence,
        enable_stub_mode=True,  # Use stub implementations for demo
    )

    # -------------------------------------------------------------------------
    # Step 3: Execute Prep Pipeline
    # -------------------------------------------------------------------------
    print("[STEP 3] Executing prep pipeline...")
    print()

    result = run_prep_pipeline(config)

    # Print execution log
    print("Execution Log:")
    print("-" * 70)
    for log_entry in result.execution_log:
        print(f"  {log_entry}")
    print("-" * 70)
    print()

    # -------------------------------------------------------------------------
    # Step 4: Report Results
    # -------------------------------------------------------------------------
    print("[STEP 4] Prep pipeline results...")
    print()

    print(f"Status: {result.status.upper()}")
    print(f"Campaign ID: {result.campaign_id}")
    print()

    if result.errors:
        print(f"Errors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")
        print()

    if result.warnings:
        print(f"Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  - {warning}")
        print()

    if result.manifest:
        manifest = result.manifest
        print(f"Generated Assets ({len(manifest.assets)}):")
        print()

        # Group by asset type
        by_type = {}
        for asset in manifest.assets:
            if asset.asset_type not in by_type:
                by_type[asset.asset_type] = []
            by_type[asset.asset_type].append(asset)

        for asset_type in ["npc", "portrait", "scene", "music", "sfx"]:
            if asset_type in by_type:
                assets = by_type[asset_type]
                print(f"  {asset_type.upper()} ({len(assets)}):")
                for asset in assets:
                    print(f"    - {asset.file_path} ({asset.file_format})")
                print()

        print(f"Asset Manifest: {output_dir / 'asset_manifest.json'}")
        print()

    # -------------------------------------------------------------------------
    # Step 5: Demonstrate Asset Inspection
    # -------------------------------------------------------------------------
    if result.manifest and result.status == "success":
        print("[STEP 5] Sample asset inspection...")
        print()

        # Find first NPC asset
        npc_assets = [a for a in result.manifest.assets if a.asset_type == "npc"]
        if npc_assets:
            npc = npc_assets[0]
            npc_path = output_dir / npc.file_path

            print(f"Sample NPC Asset: {npc.file_path}")
            print(f"  Asset ID: {npc.asset_id}")
            print(f"  Semantic Key: {npc.semantic_key}")
            print(f"  Content Hash: {npc.content_hash[:16]}...")
            print(f"  Generation Method: {npc.generation_method}")
            print()

            # Read and display NPC content (first 10 lines)
            import json
            with open(npc_path, "r") as f:
                npc_data = json.load(f)

            print("  Content Preview:")
            content_preview = json.dumps(npc_data, indent=2)
            lines = content_preview.split("\n")[:10]
            for line in lines:
                print(f"    {line}")
            if len(content_preview.split("\n")) > 10:
                print("    ...")
            print()

    # -------------------------------------------------------------------------
    # Done
    # -------------------------------------------------------------------------
    print("=" * 70)
    print("PREP PIPELINE DEMO COMPLETE")
    print("=" * 70)
    print()
    print(f"✓ Assets generated: {output_dir}")
    print(f"✓ Manifest saved: {output_dir / 'asset_manifest.json'}")
    print()


if __name__ == "__main__":
    main()
