"""Tests for visibility schemas."""

import pytest
import json
from aidm.schemas.visibility import (
    VisibilityProfile,
    TileVisibility,
    VisibilityBlockReason,
    LightLevel,
    VisionMode,
    OcclusionTag,
    AmbientLightSchedule,
    LightSource
)


def test_visibility_profile_default():
    """VisibilityProfile should default to normal vision."""
    profile = VisibilityProfile()

    assert profile.vision_modes == ["normal"]
    assert profile.ranges == {}


def test_visibility_profile_with_darkvision():
    """VisibilityProfile should support darkvision with range."""
    profile = VisibilityProfile(
        vision_modes=["normal", "darkvision"],
        ranges={"darkvision": 60}
    )

    assert "darkvision" in profile.vision_modes
    assert profile.ranges["darkvision"] == 60


def test_visibility_profile_serialization():
    """VisibilityProfile should serialize deterministically."""
    profile = VisibilityProfile(
        vision_modes=["normal", "low_light", "darkvision"],
        ranges={"low_light": 120, "darkvision": 60}
    )

    data = profile.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = VisibilityProfile.from_dict(json.loads(json_str))

    assert restored.vision_modes == profile.vision_modes
    assert restored.ranges == profile.ranges


def test_visibility_block_reason_enum():
    """VisibilityBlockReason should have all required values."""
    assert VisibilityBlockReason.LOS_BLOCKED.value == "los_blocked"
    assert VisibilityBlockReason.LOE_BLOCKED.value == "loe_blocked"
    assert VisibilityBlockReason.OUT_OF_VISION_RANGE.value == "out_of_vision_range"
    assert VisibilityBlockReason.TARGET_NOT_VISIBLE.value == "target_not_visible"


def test_tile_visibility_default():
    """TileVisibility should default to bright light, no occlusion."""
    tile = TileVisibility()

    assert tile.light_level == "bright"
    assert tile.occlusion_tags == []


def test_tile_visibility_with_occlusion():
    """TileVisibility should support occlusion tags."""
    tile = TileVisibility(
        light_level="dim",
        occlusion_tags=["light_obscurement"]
    )

    assert tile.light_level == "dim"
    assert "light_obscurement" in tile.occlusion_tags


def test_tile_visibility_serialization():
    """TileVisibility should serialize deterministically."""
    tile = TileVisibility(
        light_level="dark",
        occlusion_tags=["heavy_obscurement", "opaque"]
    )

    data = tile.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = TileVisibility.from_dict(json.loads(json_str))

    assert restored.light_level == tile.light_level
    assert restored.occlusion_tags == tile.occlusion_tags


def test_vision_mode_literals():
    """VisionMode literal should include all basic modes."""
    # This ensures the type hints work correctly
    normal: VisionMode = "normal"
    low_light: VisionMode = "low_light"
    darkvision: VisionMode = "darkvision"
    blindsense: VisionMode = "blindsense"
    blindsight: VisionMode = "blindsight"

    assert normal == "normal"
    assert darkvision == "darkvision"


def test_light_level_literals():
    """LightLevel literal should include bright, dim, dark."""
    bright: LightLevel = "bright"
    dim: LightLevel = "dim"
    dark: LightLevel = "dark"

    assert bright == "bright"
    assert dark == "dark"


def test_occlusion_tag_literals():
    """OcclusionTag literal should include all occlusion types."""
    opaque: OcclusionTag = "opaque"
    heavy: OcclusionTag = "heavy_obscurement"
    light: OcclusionTag = "light_obscurement"

    assert opaque == "opaque"
    assert heavy == "heavy_obscurement"


def test_visibility_profile_roundtrip():
    """VisibilityProfile should roundtrip correctly."""
    original = VisibilityProfile(
        vision_modes=["normal", "darkvision", "blindsense"],
        ranges={"darkvision": 60, "blindsense": 30}
    )

    data = original.to_dict()
    restored = VisibilityProfile.from_dict(data)

    assert restored.vision_modes == original.vision_modes
    assert restored.ranges == original.ranges


def test_tile_visibility_roundtrip():
    """TileVisibility should roundtrip correctly."""
    original = TileVisibility(
        light_level="dim",
        occlusion_tags=["light_obscurement"]
    )

    data = original.to_dict()
    restored = TileVisibility.from_dict(data)

    assert restored.light_level == original.light_level
    assert restored.occlusion_tags == original.occlusion_tags


def test_ambient_light_schedule_empty():
    """AmbientLightSchedule should allow empty entries."""
    schedule = AmbientLightSchedule(entries=[])
    assert schedule.entries == []


def test_ambient_light_schedule_single_entry():
    """AmbientLightSchedule should allow single entry."""
    schedule = AmbientLightSchedule(entries=[(0, "bright")])
    assert len(schedule.entries) == 1
    assert schedule.entries[0] == (0, "bright")


def test_ambient_light_schedule_multiple_entries():
    """AmbientLightSchedule should support multiple entries."""
    schedule = AmbientLightSchedule(entries=[
        (0, "bright"),
        (100, "dim"),
        (200, "dark")
    ])

    assert len(schedule.entries) == 3
    assert schedule.entries[0][1] == "bright"
    assert schedule.entries[1][1] == "dim"
    assert schedule.entries[2][1] == "dark"


def test_ambient_light_schedule_non_increasing_rejected():
    """AmbientLightSchedule should reject non-increasing times."""
    with pytest.raises(ValueError, match="must be strictly increasing"):
        AmbientLightSchedule(entries=[
            (100, "bright"),
            (100, "dim")  # Same time as previous
        ])


def test_ambient_light_schedule_decreasing_rejected():
    """AmbientLightSchedule should reject decreasing times."""
    with pytest.raises(ValueError, match="must be strictly increasing"):
        AmbientLightSchedule(entries=[
            (200, "bright"),
            (100, "dim")  # Earlier than previous
        ])


def test_ambient_light_schedule_serialization():
    """AmbientLightSchedule should serialize deterministically."""
    schedule = AmbientLightSchedule(entries=[
        (0, "bright"),
        (1000, "dim"),
        (2000, "dark")
    ])

    data = schedule.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = AmbientLightSchedule.from_dict(json.loads(json_str))

    assert len(restored.entries) == len(schedule.entries)
    for i, (t, level) in enumerate(schedule.entries):
        assert restored.entries[i] == (t, level)


def test_ambient_light_schedule_roundtrip():
    """AmbientLightSchedule should roundtrip correctly."""
    original = AmbientLightSchedule(entries=[
        (0, "bright"),
        (500, "dim"),
        (1000, "dark"),
        (1500, "bright")
    ])

    data = original.to_dict()
    restored = AmbientLightSchedule.from_dict(data)

    assert restored.entries == original.entries


def test_light_source_basic():
    """LightSource should store position, radius, and light level."""
    source = LightSource(
        position={"x": 10, "y": 15},
        radius=20,
        light_level="bright"
    )

    assert source.position == {"x": 10, "y": 15}
    assert source.radius == 20
    assert source.light_level == "bright"
    assert source.expires_at_t_seconds is None


def test_light_source_with_expiry():
    """LightSource should support expiration time."""
    source = LightSource(
        position={"x": 5, "y": 5},
        radius=30,
        light_level="dim",
        expires_at_t_seconds=1000
    )

    assert source.expires_at_t_seconds == 1000


def test_light_source_missing_x_rejected():
    """LightSource should reject position without 'x'."""
    with pytest.raises(ValueError, match="position must have 'x' and 'y' keys"):
        LightSource(
            position={"y": 10},
            radius=20,
            light_level="bright"
        )


def test_light_source_missing_y_rejected():
    """LightSource should reject position without 'y'."""
    with pytest.raises(ValueError, match="position must have 'x' and 'y' keys"):
        LightSource(
            position={"x": 10},
            radius=20,
            light_level="bright"
        )


def test_light_source_negative_radius_rejected():
    """LightSource should reject negative radius."""
    with pytest.raises(ValueError, match="radius must be >= 0"):
        LightSource(
            position={"x": 10, "y": 10},
            radius=-5,
            light_level="bright"
        )


def test_light_source_negative_expiry_rejected():
    """LightSource should reject negative expiration time."""
    with pytest.raises(ValueError, match="expires_at_t_seconds must be >= 0"):
        LightSource(
            position={"x": 10, "y": 10},
            radius=20,
            light_level="bright",
            expires_at_t_seconds=-100
        )


def test_light_source_zero_radius_allowed():
    """LightSource should allow zero radius (point source)."""
    source = LightSource(
        position={"x": 0, "y": 0},
        radius=0,
        light_level="dim"
    )

    assert source.radius == 0


def test_light_source_serialization():
    """LightSource should serialize deterministically."""
    source = LightSource(
        position={"x": 12, "y": 8},
        radius=25,
        light_level="bright",
        expires_at_t_seconds=5000
    )

    data = source.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = LightSource.from_dict(json.loads(json_str))

    assert restored.position == source.position
    assert restored.radius == source.radius
    assert restored.light_level == source.light_level
    assert restored.expires_at_t_seconds == source.expires_at_t_seconds


def test_light_source_serialization_omits_none_expiry():
    """LightSource serialization should omit None expiry."""
    source = LightSource(
        position={"x": 10, "y": 10},
        radius=20,
        light_level="dim"
    )

    data = source.to_dict()

    assert "position" in data
    assert "radius" in data
    assert "light_level" in data
    assert "expires_at_t_seconds" not in data  # Should be omitted


def test_light_source_roundtrip():
    """LightSource should roundtrip correctly."""
    original = LightSource(
        position={"x": 5, "y": 7},
        radius=30,
        light_level="dim",
        expires_at_t_seconds=2000
    )

    data = original.to_dict()
    restored = LightSource.from_dict(data)

    assert restored.position == original.position
    assert restored.radius == original.radius
    assert restored.light_level == original.light_level
    assert restored.expires_at_t_seconds == original.expires_at_t_seconds

