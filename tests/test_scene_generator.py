"""Tests for WO-052B Seeded Deterministic Generator.

Validates AD-003 Self-Sufficiency Resolution Policy compliance:
- Same seed + scene_type = identical output (determinism)
- Object counts within template bounds
- All placed objects reference valid Policy Default Library entries
- Provenance is GENERATED_SEEDED
- Scene dimensions within bounds
- All 5 scene types generate successfully
"""

import pytest
from aidm.data.scene_generator import (
    generate_scene,
    seed_from_scene_id,
    list_scene_types,
    SCENE_TEMPLATES,
    GeneratedScene,
    PlacedObject,
)
from aidm.data.policy_defaults_loader import PolicyDefaultLibrary


@pytest.fixture
def lib():
    return PolicyDefaultLibrary()


# ==============================================================================
# DETERMINISM
# ==============================================================================


def test_same_seed_same_output():
    """AD-003: Same scene_type + same seed must produce identical output."""
    scene1 = generate_scene("tavern_common_room", seed=42)
    scene2 = generate_scene("tavern_common_room", seed=42)

    assert scene1.room_width_ft == scene2.room_width_ft
    assert scene1.room_depth_ft == scene2.room_depth_ft
    assert scene1.ceiling_height_ft == scene2.ceiling_height_ft
    assert len(scene1.objects) == len(scene2.objects)

    for obj1, obj2 in zip(scene1.objects, scene2.objects):
        assert obj1.instance_id == obj2.instance_id
        assert obj1.object_class_id == obj2.object_class_id
        assert obj1.position_ft == obj2.position_ft


def test_different_seeds_different_output():
    """Different seeds should produce different scenes."""
    scene1 = generate_scene("tavern_common_room", seed=42)
    scene2 = generate_scene("tavern_common_room", seed=99)

    # At least one of dimensions or object count should differ
    differs = (
        scene1.room_width_ft != scene2.room_width_ft or
        scene1.room_depth_ft != scene2.room_depth_ft or
        len(scene1.objects) != len(scene2.objects)
    )
    assert differs, "Different seeds produced identical scenes"


def test_determinism_over_10_replays():
    """Replay 10 times — all must match exactly."""
    reference = generate_scene("dungeon_corridor", seed=1234)
    for _ in range(10):
        replay = generate_scene("dungeon_corridor", seed=1234)
        assert len(replay.objects) == len(reference.objects)
        for r, ref in zip(replay.objects, reference.objects):
            assert r.instance_id == ref.instance_id
            assert r.position_ft == ref.position_ft


# ==============================================================================
# SCENE TYPES
# ==============================================================================


def test_all_5_scene_types_generate():
    """All 5 scene types must generate without error."""
    for scene_type in list_scene_types():
        scene = generate_scene(scene_type, seed=42)
        assert isinstance(scene, GeneratedScene)
        assert scene.scene_type == scene_type


def test_list_scene_types_returns_5():
    """v1 has 5 scene types."""
    types = list_scene_types()
    assert len(types) == 5
    assert "tavern_common_room" in types
    assert "dungeon_corridor" in types
    assert "forest_clearing" in types
    assert "temple_interior" in types
    assert "castle_throne_room" in types


def test_invalid_scene_type_raises():
    """Unknown scene type raises ValueError."""
    with pytest.raises(ValueError, match="Unknown scene_type"):
        generate_scene("haunted_mansion", seed=42)


# ==============================================================================
# OBJECT COUNTS WITHIN BOUNDS
# ==============================================================================


def test_tavern_object_counts_bounded():
    """Tavern objects must be within template min/max bounds."""
    template = SCENE_TEMPLATES["tavern_common_room"]

    # Run multiple seeds and verify bounds
    for seed in range(50):
        scene = generate_scene("tavern_common_room", seed=seed)
        counts = {}
        for obj in scene.objects:
            counts[obj.object_class_id] = counts.get(obj.object_class_id, 0) + 1

        for obj_class, bounds in template["objects"].items():
            count = counts.get(obj_class, 0)
            assert bounds["min"] <= count <= bounds["max"], (
                f"seed={seed}: {obj_class} count {count} outside [{bounds['min']}, {bounds['max']}]"
            )


def test_dungeon_object_counts_bounded():
    """Dungeon objects must be within template bounds."""
    template = SCENE_TEMPLATES["dungeon_corridor"]

    for seed in range(50):
        scene = generate_scene("dungeon_corridor", seed=seed)
        counts = {}
        for obj in scene.objects:
            counts[obj.object_class_id] = counts.get(obj.object_class_id, 0) + 1

        for obj_class, bounds in template["objects"].items():
            count = counts.get(obj_class, 0)
            assert bounds["min"] <= count <= bounds["max"]


# ==============================================================================
# POLICY DEFAULT LIBRARY INTEGRATION
# ==============================================================================


def test_all_placed_objects_reference_valid_pdl_entries(lib):
    """Every placed object must reference a valid Policy Default Library entry."""
    for scene_type in list_scene_types():
        scene = generate_scene(scene_type, seed=42, library=lib)
        for obj in scene.objects:
            assert obj.object_class_id in lib, (
                f"{scene_type}: {obj.object_class_id} not in PDL"
            )
            assert obj.object_default is not None
            assert obj.object_default.provenance == "POLICY_DEFAULT"


def test_placed_objects_inherit_correct_properties(lib):
    """Placed objects must carry correct properties from PDL."""
    scene = generate_scene("tavern_common_room", seed=42, library=lib)

    for obj in scene.objects:
        pdl_entry = lib.get(obj.object_class_id)
        assert pdl_entry is not None
        assert obj.object_default.hardness == pdl_entry.hardness
        assert obj.object_default.hp == pdl_entry.hp
        assert obj.object_default.cover_type == pdl_entry.cover_type


# ==============================================================================
# PROVENANCE
# ==============================================================================


def test_scene_provenance_is_generated_seeded():
    """Scene provenance must be GENERATED_SEEDED."""
    scene = generate_scene("tavern_common_room", seed=42)
    assert scene.provenance == "GENERATED_SEEDED"


def test_object_provenance_is_generated_seeded():
    """Placed object provenance must be GENERATED_SEEDED."""
    scene = generate_scene("tavern_common_room", seed=42)
    for obj in scene.objects:
        assert obj.provenance == "GENERATED_SEEDED"


# ==============================================================================
# SCENE DIMENSIONS
# ==============================================================================


def test_room_dimensions_within_bounds():
    """Room dimensions must be within template bounds."""
    for scene_type in list_scene_types():
        template = SCENE_TEMPLATES[scene_type]
        for seed in range(20):
            scene = generate_scene(scene_type, seed=seed)
            assert template["room_width_ft"]["min"] <= scene.room_width_ft <= template["room_width_ft"]["max"]
            assert template["room_depth_ft"]["min"] <= scene.room_depth_ft <= template["room_depth_ft"]["max"]


def test_scene_metadata_populated():
    """Scene metadata (floor, lighting) must match template."""
    scene = generate_scene("tavern_common_room", seed=42)
    assert scene.floor_material == "wood"
    assert scene.lighting == "bright"

    scene2 = generate_scene("dungeon_corridor", seed=42)
    assert scene2.floor_material == "stone"
    assert scene2.lighting == "dim"


# ==============================================================================
# OBJECT POSITIONS
# ==============================================================================


def test_objects_within_room_bounds():
    """All placed objects must be within the room boundaries."""
    for scene_type in list_scene_types():
        for seed in range(10):
            scene = generate_scene(scene_type, seed=seed)
            for obj in scene.objects:
                assert 0 <= obj.position_ft["x"] <= scene.room_width_ft + 1, (
                    f"{obj.instance_id} x={obj.position_ft['x']} outside room width {scene.room_width_ft}"
                )
                assert 0 <= obj.position_ft["y"] <= scene.room_depth_ft + 1, (
                    f"{obj.instance_id} y={obj.position_ft['y']} outside room depth {scene.room_depth_ft}"
                )


def test_instance_ids_unique():
    """All placed object instance IDs must be unique within a scene."""
    for scene_type in list_scene_types():
        scene = generate_scene(scene_type, seed=42)
        ids = [obj.instance_id for obj in scene.objects]
        assert len(ids) == len(set(ids)), f"Duplicate instance IDs in {scene_type}"


# ==============================================================================
# SEED UTILITY
# ==============================================================================


def test_seed_from_scene_id_deterministic():
    """seed_from_scene_id must be deterministic."""
    s1 = seed_from_scene_id("tavern_001")
    s2 = seed_from_scene_id("tavern_001")
    assert s1 == s2


def test_seed_from_scene_id_different_ids():
    """Different scene IDs should produce different seeds."""
    s1 = seed_from_scene_id("tavern_001")
    s2 = seed_from_scene_id("tavern_002")
    assert s1 != s2


def test_seed_from_scene_id_range():
    """Seed must be in valid range (0 to 2^31-1)."""
    for scene_id in ["a", "test_123", "very_long_scene_id_string_here"]:
        seed = seed_from_scene_id(scene_id)
        assert 0 <= seed < 2**31
