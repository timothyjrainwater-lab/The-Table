"""Seeded Deterministic Generator for WO-052B.

Implements AD-003 Self-Sufficiency Resolution Policy:
- Given a scene_type and seed, generates a deterministic set of placed objects
- Object counts, placements come from bounded scene templates
- All properties come from the Policy Default Library (WO-051B)
- No Spark dependency: depends ONLY on scene metadata + seed + PDL

DETERMINISM GUARANTEE:
  same scene_type + same seed = identical object list every time

SCENE TYPES (v1):
  tavern_common_room, dungeon_corridor, forest_clearing,
  temple_interior, castle_throne_room

PROVENANCE:
  Generated objects are tagged GENERATED_SEEDED with the seed value.
"""

import hashlib
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from aidm.data.policy_defaults_loader import PolicyDefaultLibrary, ObjectDefault


@dataclass(frozen=True)
class PlacedObject:
    """An environmental object placed in a scene.

    Combines the Policy Default Library data with a specific
    position and instance ID for scene use.
    """
    instance_id: str
    object_class_id: str
    name: str
    position_ft: Dict[str, float]  # {"x": float, "y": float}
    object_default: ObjectDefault
    provenance: str = "GENERATED_SEEDED"


# Scene templates: define what objects can appear in each scene type
# and the bounded ranges for their counts.
SCENE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "tavern_common_room": {
        "objects": {
            "tavern_table": {"min": 2, "max": 6},
            "tavern_chair": {"min": 4, "max": 16},
            "bar_counter": {"min": 1, "max": 1},
            "wooden_barrel": {"min": 0, "max": 3},
            "wooden_door": {"min": 1, "max": 2},
        },
        "room_width_ft": {"min": 20, "max": 40},
        "room_depth_ft": {"min": 20, "max": 35},
        "ceiling_height_ft": {"min": 8, "max": 12},
        "floor_material": "wood",
        "lighting": "bright",
    },
    "dungeon_corridor": {
        "objects": {
            "stone_wall_section": {"min": 2, "max": 4},
            "wooden_door": {"min": 1, "max": 3},
            "iron_door": {"min": 0, "max": 1},
            "stone_pillar": {"min": 0, "max": 2},
            "wooden_crate": {"min": 0, "max": 2},
            "iron_cage": {"min": 0, "max": 1},
        },
        "room_width_ft": {"min": 10, "max": 20},
        "room_depth_ft": {"min": 30, "max": 60},
        "ceiling_height_ft": {"min": 8, "max": 15},
        "floor_material": "stone",
        "lighting": "dim",
    },
    "forest_clearing": {
        "objects": {
            "hay_bale": {"min": 0, "max": 2},
            "cart_wooden": {"min": 0, "max": 1},
            "campfire": {"min": 0, "max": 1},
            "well_stone": {"min": 0, "max": 1},
            "wooden_barrel": {"min": 0, "max": 2},
        },
        "room_width_ft": {"min": 30, "max": 60},
        "room_depth_ft": {"min": 30, "max": 60},
        "ceiling_height_ft": {"min": 0, "max": 0},  # Outdoor
        "floor_material": "dirt",
        "lighting": "bright",
    },
    "temple_interior": {
        "objects": {
            "altar_stone": {"min": 1, "max": 1},
            "stone_pillar": {"min": 2, "max": 6},
            "bookshelf": {"min": 0, "max": 2},
            "wooden_door": {"min": 1, "max": 2},
            "chest_wooden": {"min": 0, "max": 1},
            "chest_iron": {"min": 0, "max": 1},
        },
        "room_width_ft": {"min": 20, "max": 40},
        "room_depth_ft": {"min": 30, "max": 50},
        "ceiling_height_ft": {"min": 12, "max": 25},
        "floor_material": "stone",
        "lighting": "dim",
    },
    "castle_throne_room": {
        "objects": {
            "throne": {"min": 1, "max": 1},
            "stone_pillar": {"min": 2, "max": 8},
            "wooden_door": {"min": 1, "max": 2},
            "iron_door": {"min": 0, "max": 1},
            "bookshelf": {"min": 0, "max": 1},
            "chest_iron": {"min": 0, "max": 1},
        },
        "room_width_ft": {"min": 30, "max": 50},
        "room_depth_ft": {"min": 40, "max": 60},
        "ceiling_height_ft": {"min": 15, "max": 30},
        "floor_material": "stone",
        "lighting": "bright",
    },
}


@dataclass
class GeneratedScene:
    """Result of seeded scene generation.

    Contains the scene metadata and all placed objects.
    """
    scene_type: str
    seed: int
    room_width_ft: int
    room_depth_ft: int
    ceiling_height_ft: int
    floor_material: str
    lighting: str
    objects: List[PlacedObject]
    provenance: str = "GENERATED_SEEDED"


def generate_scene(
    scene_type: str,
    seed: int,
    library: Optional[PolicyDefaultLibrary] = None,
) -> GeneratedScene:
    """Generate a deterministic scene from a scene type and seed.

    AD-003: Same scene_type + same seed = identical output every time.
    No Spark or LLM dependency.

    Args:
        scene_type: One of the SCENE_TEMPLATES keys
        seed: Deterministic seed (e.g., hash(scene_id) % 2**31)
        library: Policy Default Library instance (loaded if None)

    Returns:
        GeneratedScene with placed objects

    Raises:
        ValueError: If scene_type is not recognized
    """
    if scene_type not in SCENE_TEMPLATES:
        raise ValueError(
            f"Unknown scene_type: {scene_type}. "
            f"Valid types: {sorted(SCENE_TEMPLATES.keys())}"
        )

    if library is None:
        library = PolicyDefaultLibrary()

    template = SCENE_TEMPLATES[scene_type]

    # Create a deterministic RNG from the seed
    rng = random.Random(seed)

    # Generate room dimensions
    room_width = rng.randint(
        template["room_width_ft"]["min"],
        template["room_width_ft"]["max"],
    )
    room_depth = rng.randint(
        template["room_depth_ft"]["min"],
        template["room_depth_ft"]["max"],
    )
    ceiling_height = rng.randint(
        template["ceiling_height_ft"]["min"],
        max(template["ceiling_height_ft"]["min"], template["ceiling_height_ft"]["max"]),
    )

    # Generate object counts and place them
    placed_objects: List[PlacedObject] = []
    instance_counter = 0

    for obj_class_id, count_range in template["objects"].items():
        obj_default = library.get(obj_class_id)
        if obj_default is None:
            continue  # Skip if not in library

        count = rng.randint(count_range["min"], count_range["max"])

        for i in range(count):
            # Generate position within room bounds (with margin for object size)
            margin_x = max(1, obj_default.dimensions_ft.length / 2)
            margin_y = max(1, obj_default.dimensions_ft.width / 2)

            pos_x = rng.uniform(margin_x, max(margin_x + 1, room_width - margin_x))
            pos_y = rng.uniform(margin_y, max(margin_y + 1, room_depth - margin_y))

            instance_id = f"{obj_class_id}_{instance_counter:03d}"
            instance_counter += 1

            placed_objects.append(PlacedObject(
                instance_id=instance_id,
                object_class_id=obj_class_id,
                name=f"{obj_default.name} #{i + 1}" if count > 1 else obj_default.name,
                position_ft={"x": round(pos_x, 1), "y": round(pos_y, 1)},
                object_default=obj_default,
            ))

    return GeneratedScene(
        scene_type=scene_type,
        seed=seed,
        room_width_ft=room_width,
        room_depth_ft=room_depth,
        ceiling_height_ft=ceiling_height,
        floor_material=template["floor_material"],
        lighting=template["lighting"],
        objects=placed_objects,
    )


def seed_from_scene_id(scene_id: str) -> int:
    """Derive a deterministic seed from a scene ID string.

    Args:
        scene_id: Unique scene identifier (e.g., "tavern_001")

    Returns:
        Deterministic integer seed (0 to 2^31-1)
    """
    h = hashlib.sha256(scene_id.encode("utf-8")).hexdigest()
    return int(h, 16) % (2**31)


def list_scene_types() -> List[str]:
    """Return all available scene types."""
    return sorted(SCENE_TEMPLATES.keys())
