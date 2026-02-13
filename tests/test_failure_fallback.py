"""Tests for failure fallback system.

M3 IMPLEMENTATION: Comprehensive Fallback Tests
-----------------------------------------------
Tests all four fallback tiers, archetype matching logic, solid color generation,
and failure trigger conditions.

Based on approved design: docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md

Test Coverage:
- FallbackTier enum and FallbackResult schema
- FailureFallbackResolver initialization
- All 4 fallback tiers (shipped art, generic, solid color, text-only)
- Archetype matching (NPC, scene, item)
- Solid color generation (deterministic colors)
- All 5 failure triggers
- Edge cases and error handling

Minimum 20 tests required by work order.
"""

import pytest
import tempfile
import json
from pathlib import Path
from PIL import Image
import io

from aidm.schemas.fallback import FallbackTier, FallbackResult, FallbackReason
from aidm.core.failure_fallback import FailureFallbackResolver


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_shipped_art_dir(tmp_path):
    """Create temporary shipped art pack directory with manifest."""
    shipped_art_dir = tmp_path / "shipped_art_pack"
    shipped_art_dir.mkdir()

    # Create NPC portraits subdirectory
    npc_dir = shipped_art_dir / "npc_portraits"
    npc_dir.mkdir()

    # Create test images
    _create_test_image(npc_dir / "human_fighter_male.png", (512, 512), (255, 0, 0))
    _create_test_image(npc_dir / "elf_wizard_female.png", (512, 512), (0, 255, 0))
    _create_test_image(npc_dir / "dwarf_cleric.png", (512, 512), (0, 0, 255))
    _create_test_image(npc_dir / "human_generic.png", (512, 512), (128, 128, 128))

    # Create scenes subdirectory
    scenes_dir = shipped_art_dir / "scenes"
    scenes_dir.mkdir()
    _create_test_image(scenes_dir / "tavern_interior.png", (512, 512), (100, 50, 0))
    _create_test_image(scenes_dir / "dungeon_corridor.png", (512, 512), (50, 50, 50))
    _create_test_image(scenes_dir / "generic_indoor_scene.png", (512, 512), (150, 150, 100))

    # Create items subdirectory
    items_dir = shipped_art_dir / "items"
    items_dir.mkdir()
    _create_test_image(items_dir / "weapon_sword.png", (512, 512), (192, 192, 192))
    _create_test_image(items_dir / "generic_weapon.png", (512, 512), (160, 160, 160))

    # Create manifest.json
    manifest = {
        "version": "1.0",
        "npc_portraits": [
            {
                "filename": "npc_portraits/human_fighter_male.png",
                "archetype": {"species": "human", "class": "fighter", "gender": "male"}
            },
            {
                "filename": "npc_portraits/elf_wizard_female.png",
                "archetype": {"species": "elf", "class": "wizard", "gender": "female"}
            },
            {
                "filename": "npc_portraits/dwarf_cleric.png",
                "archetype": {"species": "dwarf", "class": "cleric"}  # No gender (partial match)
            },
            {
                "filename": "npc_portraits/human_generic.png",
                "archetype": {"species": "human"}  # Species-only match
            }
        ],
        "scenes": [
            {
                "filename": "scenes/tavern_interior.png",
                "location_type": "tavern",
                "location_category": "indoor"
            },
            {
                "filename": "scenes/dungeon_corridor.png",
                "location_type": "dungeon",
                "location_category": "indoor"
            },
            {
                "filename": "scenes/generic_indoor_scene.png",
                "location_category": "indoor"  # Generic category match
            }
        ],
        "items": [
            {
                "filename": "items/weapon_sword.png",
                "item_type": "weapon",
                "item_subtype": "sword"
            },
            {
                "filename": "items/generic_weapon.png",
                "item_type": "weapon"  # Type-only match
            }
        ]
    }

    manifest_path = shipped_art_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return shipped_art_dir, manifest_path


@pytest.fixture
def temp_generic_placeholders_dir(tmp_path):
    """Create temporary generic placeholders directory."""
    placeholders_dir = tmp_path / "placeholders"
    placeholders_dir.mkdir()

    _create_test_image(placeholders_dir / "generic_npc_portrait.png", (512, 512), (100, 100, 200))
    _create_test_image(placeholders_dir / "generic_scene_background.png", (512, 512), (100, 200, 100))
    _create_test_image(placeholders_dir / "generic_item_icon.png", (512, 512), (200, 100, 200))

    return placeholders_dir


def _create_test_image(path: Path, size: tuple, color: tuple):
    """Create a test PNG image with solid color."""
    img = Image.new('RGB', size, color=color)
    img.save(path, format='PNG')


# ============================================================================
# Schema Tests
# ============================================================================

def test_fallback_tier_enum_values():
    """Test FallbackTier enum has all 4 tiers."""
    assert FallbackTier.SHIPPED_ART.value == "shipped_art_pack"
    assert FallbackTier.GENERIC.value == "generic_category_placeholder"
    assert FallbackTier.SOLID_COLOR.value == "solid_color_text"
    assert FallbackTier.TEXT_ONLY.value == "text_only"


def test_fallback_reason_enum_values():
    """Test FallbackReason enum has all 5 failure triggers."""
    assert FallbackReason.MAX_ATTEMPTS_EXHAUSTED.value == "max_attempts_exhausted"
    assert FallbackReason.TIMEOUT.value == "timeout"
    assert FallbackReason.USER_ABORTED.value == "user_aborted"
    assert FallbackReason.HARDWARE_FAILURE.value == "hardware_failure"
    assert FallbackReason.BAD_PROMPT.value == "bad_prompt"
    assert FallbackReason.TIER_DEFAULT.value == "tier_default"


def test_fallback_result_schema_valid():
    """Test FallbackResult schema with valid data."""
    result = FallbackResult(
        tier=FallbackTier.SHIPPED_ART,
        image_bytes=b"fake_image_data",
        description="Test fallback",
        file_path="/path/to/file.png",
        metadata={"test": "value"}
    )
    assert result.tier == FallbackTier.SHIPPED_ART
    assert result.image_bytes == b"fake_image_data"
    assert result.description == "Test fallback"
    assert result.file_path == "/path/to/file.png"
    assert result.metadata == {"test": "value"}


def test_fallback_result_text_only_no_image_bytes():
    """Test TEXT_ONLY tier must have image_bytes=None."""
    result = FallbackResult(
        tier=FallbackTier.TEXT_ONLY,
        image_bytes=None,
        description="Text-only fallback",
        file_path="",
        metadata={}
    )
    assert result.tier == FallbackTier.TEXT_ONLY
    assert result.image_bytes is None


def test_fallback_result_text_only_rejects_image_bytes():
    """Test TEXT_ONLY tier raises error if image_bytes provided."""
    with pytest.raises(ValueError, match="TEXT_ONLY tier must have image_bytes=None"):
        FallbackResult(
            tier=FallbackTier.TEXT_ONLY,
            image_bytes=b"should_not_exist",
            description="Invalid",
            file_path="",
            metadata={}
        )


def test_fallback_result_non_text_only_requires_image_bytes():
    """Test non-TEXT_ONLY tiers raise error if image_bytes=None."""
    with pytest.raises(ValueError, match="SHIPPED_ART tier must have non-None image_bytes"):
        FallbackResult(
            tier=FallbackTier.SHIPPED_ART,
            image_bytes=None,
            description="Invalid",
            file_path="/path/to/file.png",
            metadata={}
        )


# ============================================================================
# FailureFallbackResolver Initialization Tests
# ============================================================================

def test_resolver_initialization_no_args():
    """Test resolver initializes with no arguments."""
    resolver = FailureFallbackResolver()
    assert resolver.shipped_art_manifest is None
    assert resolver.generic_placeholders_dir is None
    assert resolver.enable_solid_color is True
    assert resolver.enable_text_only is True


def test_resolver_initialization_with_manifest(temp_shipped_art_dir):
    """Test resolver loads shipped art manifest."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)
    assert resolver.shipped_art_manifest == manifest_path
    assert resolver._shipped_art_index is not None
    assert "npc_portraits" in resolver._shipped_art_index


def test_resolver_initialization_with_generic_placeholders(temp_generic_placeholders_dir):
    """Test resolver initializes with generic placeholders directory."""
    resolver = FailureFallbackResolver(generic_placeholders_dir=temp_generic_placeholders_dir)
    assert resolver.generic_placeholders_dir == temp_generic_placeholders_dir


def test_resolver_initialization_disable_tiers():
    """Test resolver can disable solid color and text-only tiers."""
    resolver = FailureFallbackResolver(enable_solid_color=False, enable_text_only=False)
    assert resolver.enable_solid_color is False
    assert resolver.enable_text_only is False


# ============================================================================
# Archetype Matching Tests (NPC Portraits)
# ============================================================================

def test_match_archetype_npc_exact_match(temp_shipped_art_dir):
    """Test NPC archetype matching: exact match (species + class + gender)."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    metadata = {
        "asset_type": "npc",
        "species": "human",
        "class": "fighter",
        "gender": "male"
    }

    match = resolver.match_archetype(metadata)
    assert match == "npc_portraits/human_fighter_male.png"


def test_match_archetype_npc_partial_match(temp_shipped_art_dir):
    """Test NPC archetype matching: partial match (species + class, ignore gender)."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    # Request male dwarf cleric, but only have generic dwarf cleric (no gender)
    metadata = {
        "asset_type": "npc",
        "species": "dwarf",
        "class": "cleric",
        "gender": "male"
    }

    match = resolver.match_archetype(metadata)
    assert match == "npc_portraits/dwarf_cleric.png"


def test_match_archetype_npc_species_only_match(temp_shipped_art_dir):
    """Test NPC archetype matching: species-only match (ignore class + gender)."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    # Request human rogue (not in manifest), should match human_generic
    metadata = {
        "asset_type": "npc",
        "species": "human",
        "class": "rogue",
        "gender": "female"
    }

    match = resolver.match_archetype(metadata)
    assert match == "npc_portraits/human_generic.png"


def test_match_archetype_npc_no_match(temp_shipped_art_dir):
    """Test NPC archetype matching: no match (species not in manifest)."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    # Request orc fighter (not in manifest)
    metadata = {
        "asset_type": "npc",
        "species": "orc",
        "class": "fighter",
        "gender": "male"
    }

    match = resolver.match_archetype(metadata)
    assert match is None


# ============================================================================
# Archetype Matching Tests (Scenes)
# ============================================================================

def test_match_archetype_scene_exact_match(temp_shipped_art_dir):
    """Test scene archetype matching: exact match (location_type)."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    metadata = {
        "asset_type": "scene",
        "location_type": "tavern"
    }

    match = resolver.match_archetype(metadata)
    assert match == "scenes/tavern_interior.png"


def test_match_archetype_scene_category_match(temp_shipped_art_dir):
    """Test scene archetype matching: category match (location_category)."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    # Request castle throne room (not in manifest), but have generic indoor scene
    metadata = {
        "asset_type": "scene",
        "location_type": "castle_throne_room",
        "location_category": "indoor"
    }

    match = resolver.match_archetype(metadata)
    assert match == "scenes/generic_indoor_scene.png"


def test_match_archetype_scene_no_match(temp_shipped_art_dir):
    """Test scene archetype matching: no match."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    # Request outdoor forest (not in manifest, no outdoor category)
    metadata = {
        "asset_type": "scene",
        "location_type": "forest_clearing",
        "location_category": "outdoor"
    }

    match = resolver.match_archetype(metadata)
    assert match is None


# ============================================================================
# Archetype Matching Tests (Items)
# ============================================================================

def test_match_archetype_item_exact_match(temp_shipped_art_dir):
    """Test item archetype matching: exact match (item_type + item_subtype)."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    metadata = {
        "asset_type": "item",
        "item_type": "weapon",
        "item_subtype": "sword"
    }

    match = resolver.match_archetype(metadata)
    assert match == "items/weapon_sword.png"


def test_match_archetype_item_type_only_match(temp_shipped_art_dir):
    """Test item archetype matching: type-only match (item_type)."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    # Request weapon axe (not in manifest), should match generic weapon
    metadata = {
        "asset_type": "item",
        "item_type": "weapon",
        "item_subtype": "axe"
    }

    match = resolver.match_archetype(metadata)
    assert match == "items/generic_weapon.png"


def test_match_archetype_item_no_match(temp_shipped_art_dir):
    """Test item archetype matching: no match."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    # Request potion (not in manifest)
    metadata = {
        "asset_type": "item",
        "item_type": "consumable",
        "item_subtype": "potion"
    }

    match = resolver.match_archetype(metadata)
    assert match is None


# ============================================================================
# Solid Color Generation Tests
# ============================================================================

def test_generate_solid_color_npc_blue():
    """Test solid color generation for NPC (blue background)."""
    resolver = FailureFallbackResolver()
    image_bytes = resolver.generate_solid_color(
        asset_type="npc",
        asset_name="Test NPC",
        description="A test NPC description"
    )

    # Verify PNG format
    assert image_bytes.startswith(b'\x89PNG')

    # Load image and check color
    img = Image.open(io.BytesIO(image_bytes))
    assert img.size == (512, 512)
    # Check center pixel is blue (#4A90E2)
    center_color = img.getpixel((256, 256))
    assert center_color == (74, 144, 226)  # Blue


def test_generate_solid_color_scene_green():
    """Test solid color generation for scene (green background)."""
    resolver = FailureFallbackResolver()
    image_bytes = resolver.generate_solid_color(
        asset_type="scene",
        asset_name="Test Scene",
        description="A test scene description"
    )

    img = Image.open(io.BytesIO(image_bytes))
    center_color = img.getpixel((256, 256))
    assert center_color == (126, 211, 33)  # Green


def test_generate_solid_color_item_purple():
    """Test solid color generation for item (purple background)."""
    resolver = FailureFallbackResolver()
    image_bytes = resolver.generate_solid_color(
        asset_type="item",
        asset_name="Test Item",
        description="A test item description"
    )

    img = Image.open(io.BytesIO(image_bytes))
    center_color = img.getpixel((256, 256))
    assert center_color == (189, 16, 224)  # Purple


def test_generate_solid_color_deterministic():
    """Test solid color generation is deterministic for same inputs."""
    resolver = FailureFallbackResolver()

    image_bytes_1 = resolver.generate_solid_color(
        asset_type="npc",
        asset_name="Same NPC",
        description="Same description"
    )

    image_bytes_2 = resolver.generate_solid_color(
        asset_type="npc",
        asset_name="Same NPC",
        description="Same description"
    )

    # Images should be identical (same color, same text overlay)
    assert len(image_bytes_1) == len(image_bytes_2)


def test_generate_solid_color_truncates_description():
    """Test solid color generation truncates long descriptions."""
    resolver = FailureFallbackResolver()
    long_description = "A" * 100  # 100 characters, should truncate to 80 + "..."

    image_bytes = resolver.generate_solid_color(
        asset_type="npc",
        asset_name="Test",
        description=long_description
    )

    # Should succeed without error
    assert image_bytes.startswith(b'\x89PNG')


# ============================================================================
# Fallback Resolution Tests (All 4 Tiers)
# ============================================================================

def test_resolve_fallback_tier_1_shipped_art(temp_shipped_art_dir):
    """Test fallback resolution: Tier 1 (shipped art pack)."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    metadata = {
        "asset_type": "npc",
        "asset_name": "Thorin Ironforge",
        "species": "human",
        "class": "fighter",
        "gender": "male"
    }

    result = resolver.resolve_fallback(
        asset_metadata=metadata,
        failure_reason=FallbackReason.MAX_ATTEMPTS_EXHAUSTED
    )

    assert result.tier == FallbackTier.SHIPPED_ART
    assert result.image_bytes is not None
    assert "human_fighter_male" in result.file_path
    assert result.metadata["fallback_type"] == FallbackTier.SHIPPED_ART.value
    assert result.metadata["archetype_match"] == "npc_portraits/human_fighter_male.png"


def test_resolve_fallback_tier_2_generic(temp_generic_placeholders_dir):
    """Test fallback resolution: Tier 2 (generic placeholder)."""
    # No shipped art pack, but have generic placeholders
    resolver = FailureFallbackResolver(generic_placeholders_dir=temp_generic_placeholders_dir)

    metadata = {
        "asset_type": "npc",
        "asset_name": "Test NPC",
        "species": "orc",  # Not in shipped art pack
        "class": "barbarian"
    }

    result = resolver.resolve_fallback(
        asset_metadata=metadata,
        failure_reason=FallbackReason.TIMEOUT
    )

    assert result.tier == FallbackTier.GENERIC
    assert result.image_bytes is not None
    assert "generic_npc_portrait" in result.file_path
    assert result.metadata["fallback_type"] == FallbackTier.GENERIC.value


def test_resolve_fallback_tier_3_solid_color():
    """Test fallback resolution: Tier 3 (solid color + text)."""
    # No shipped art pack, no generic placeholders
    resolver = FailureFallbackResolver()

    metadata = {
        "asset_type": "npc",
        "asset_name": "Test NPC",
        "description": "A mysterious character",
        "species": "aberration"
    }

    result = resolver.resolve_fallback(
        asset_metadata=metadata,
        failure_reason=FallbackReason.HARDWARE_FAILURE
    )

    assert result.tier == FallbackTier.SOLID_COLOR
    assert result.image_bytes is not None
    assert result.metadata["fallback_type"] == FallbackTier.SOLID_COLOR.value
    assert "color_scheme" in result.metadata


def test_resolve_fallback_tier_4_text_only():
    """Test fallback resolution: Tier 4 (text-only)."""
    # Disable solid color tier
    resolver = FailureFallbackResolver(enable_solid_color=False)

    metadata = {
        "asset_type": "npc",
        "asset_name": "Test NPC",
        "species": "aberration"
    }

    result = resolver.resolve_fallback(
        asset_metadata=metadata,
        failure_reason=FallbackReason.BAD_PROMPT
    )

    assert result.tier == FallbackTier.TEXT_ONLY
    assert result.image_bytes is None
    assert result.file_path == ""
    assert result.metadata["fallback_type"] == FallbackTier.TEXT_ONLY.value


# ============================================================================
# Failure Trigger Tests (All 5 Reasons)
# ============================================================================

def test_failure_trigger_max_attempts_exhausted():
    """Test fallback with MAX_ATTEMPTS_EXHAUSTED failure reason."""
    resolver = FailureFallbackResolver()

    metadata = {
        "asset_type": "npc",
        "asset_name": "Test",
        "description": "Test"
    }

    result = resolver.resolve_fallback(
        asset_metadata=metadata,
        failure_reason=FallbackReason.MAX_ATTEMPTS_EXHAUSTED
    )

    assert result.metadata["fallback_reason"] == FallbackReason.MAX_ATTEMPTS_EXHAUSTED.value


def test_failure_trigger_timeout():
    """Test fallback with TIMEOUT failure reason."""
    resolver = FailureFallbackResolver()

    metadata = {"asset_type": "scene", "asset_name": "Test", "description": "Test"}

    result = resolver.resolve_fallback(
        asset_metadata=metadata,
        failure_reason=FallbackReason.TIMEOUT
    )

    assert result.metadata["fallback_reason"] == FallbackReason.TIMEOUT.value


def test_failure_trigger_user_aborted():
    """Test fallback with USER_ABORTED failure reason."""
    resolver = FailureFallbackResolver()

    metadata = {"asset_type": "item", "asset_name": "Test", "description": "Test"}

    result = resolver.resolve_fallback(
        asset_metadata=metadata,
        failure_reason=FallbackReason.USER_ABORTED
    )

    assert result.metadata["fallback_reason"] == FallbackReason.USER_ABORTED.value


def test_failure_trigger_hardware_failure():
    """Test fallback with HARDWARE_FAILURE failure reason."""
    resolver = FailureFallbackResolver()

    metadata = {"asset_type": "npc", "asset_name": "Test", "description": "Test"}

    result = resolver.resolve_fallback(
        asset_metadata=metadata,
        failure_reason=FallbackReason.HARDWARE_FAILURE
    )

    assert result.metadata["fallback_reason"] == FallbackReason.HARDWARE_FAILURE.value


def test_failure_trigger_bad_prompt():
    """Test fallback with BAD_PROMPT failure reason."""
    resolver = FailureFallbackResolver()

    metadata = {"asset_type": "npc", "asset_name": "Test", "description": "Test"}

    result = resolver.resolve_fallback(
        asset_metadata=metadata,
        failure_reason=FallbackReason.BAD_PROMPT
    )

    assert result.metadata["fallback_reason"] == FallbackReason.BAD_PROMPT.value


def test_failure_trigger_tier_default():
    """Test fallback with TIER_DEFAULT failure reason (Tier 5 CPU-only)."""
    resolver = FailureFallbackResolver()

    metadata = {"asset_type": "npc", "asset_name": "Test", "description": "Test"}

    result = resolver.resolve_fallback(
        asset_metadata=metadata,
        failure_reason=FallbackReason.TIER_DEFAULT
    )

    assert result.metadata["fallback_reason"] == FallbackReason.TIER_DEFAULT.value


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

def test_resolve_fallback_no_tiers_available_raises_error():
    """Test fallback raises error when all tiers disabled and none available."""
    # Disable solid color and text-only
    resolver = FailureFallbackResolver(enable_solid_color=False, enable_text_only=False)

    metadata = {"asset_type": "npc", "asset_name": "Test", "description": "Test"}

    with pytest.raises(RuntimeError, match="All fallback tiers exhausted"):
        resolver.resolve_fallback(
            asset_metadata=metadata,
            failure_reason=FallbackReason.MAX_ATTEMPTS_EXHAUSTED
        )


def test_match_archetype_no_manifest_returns_none():
    """Test archetype matching returns None when no manifest loaded."""
    resolver = FailureFallbackResolver()  # No manifest

    metadata = {
        "asset_type": "npc",
        "species": "human",
        "class": "fighter",
        "gender": "male"
    }

    match = resolver.match_archetype(metadata)
    assert match is None


def test_match_archetype_unknown_asset_type_returns_none(temp_shipped_art_dir):
    """Test archetype matching returns None for unknown asset type."""
    shipped_art_dir, manifest_path = temp_shipped_art_dir
    resolver = FailureFallbackResolver(shipped_art_manifest=manifest_path)

    metadata = {
        "asset_type": "unknown_type",
        "species": "human"
    }

    match = resolver.match_archetype(metadata)
    assert match is None
