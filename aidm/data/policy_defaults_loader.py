"""Policy Default Library loader for WO-051B.

Implements AD-003 Self-Sufficiency Resolution Policy:
- Loads the 20 starter environmental object classes from policy_defaults.json
- Provides typed access to object properties (dimensions, material, hardness, HP, cover)
- Every default is tagged with POLICY_DEFAULT provenance
- Deterministic: same object_class_id always returns identical data

COVERAGE (AD-003):
- Mundane environmental objects (furniture, doors, walls, containers)
- Structural geometry within bounded ranges
- Material classifications (wood, stone, iron, organic)
- NOT creature stats, encounter difficulty, or magic items

EXPANSION PATH:
1. Tavern/inn objects (v1.0 — this file)
2. Dungeon corridor objects (v1.1)
3. Outdoor terrain features (v1.2)
4. Temple/church objects (v1.3)
5. Castle/fortress objects (v1.4)
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


# Path to the JSON data file
_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULTS_PATH = os.path.join(_DATA_DIR, "policy_defaults.json")


@dataclass(frozen=True)
class Dimensions:
    """3D dimensions in feet."""
    length: float
    width: float
    height: float


@dataclass(frozen=True)
class ObjectDefault:
    """A single environmental object class from the Policy Default Library.

    All fields are immutable (frozen dataclass) and deterministic.
    Provenance is always POLICY_DEFAULT.
    """
    object_class_id: str
    name: str
    dimensions_ft: Dimensions
    material: str
    hardness: Optional[int]
    hp: Optional[int]
    cover_type: str  # "none", "partial", "total"
    break_dc: Optional[int]
    weight_lb: Optional[float]
    category: str  # "furniture", "structural", "container", "terrain", "hazard", "vehicle"
    tags: tuple  # Immutable tuple of location tags
    cover_condition: Optional[str] = None  # e.g., "closed" for doors
    cover_notes: Optional[str] = None  # Extra notes about cover behavior
    provenance: str = "POLICY_DEFAULT"


class PolicyDefaultLibrary:
    """Loader and accessor for the Policy Default Library.

    Usage:
        lib = PolicyDefaultLibrary()
        table = lib.get("tavern_table")
        print(table.hardness)  # 5
        print(table.cover_type)  # "partial"

        # Query by tag
        tavern_objects = lib.get_by_tag("tavern")

        # Query by category
        furniture = lib.get_by_category("furniture")

        # Query by material
        wood_objects = lib.get_by_material("wood")
    """

    def __init__(self, data_path: str = _DEFAULTS_PATH):
        """Load the policy defaults from JSON.

        Args:
            data_path: Path to the policy_defaults.json file.
                       Defaults to the bundled data file.
        """
        self._objects: Dict[str, ObjectDefault] = {}
        self._version: str = "unknown"
        self._policy_id: str = "unknown"
        self._load(data_path)

    def _load(self, data_path: str) -> None:
        """Parse JSON and build typed ObjectDefault instances."""
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("_meta", {})
        self._version = meta.get("library_version", "unknown")
        self._policy_id = meta.get("policy_id", "unknown")

        for obj_id, obj_data in data.get("objects", {}).items():
            dims = obj_data.get("dimensions_ft", {})
            self._objects[obj_id] = ObjectDefault(
                object_class_id=obj_id,
                name=obj_data["name"],
                dimensions_ft=Dimensions(
                    length=dims.get("length", 0),
                    width=dims.get("width", 0),
                    height=dims.get("height", 0),
                ),
                material=obj_data.get("material", "unknown"),
                hardness=obj_data.get("hardness"),
                hp=obj_data.get("hp"),
                cover_type=obj_data.get("cover_type", "none"),
                break_dc=obj_data.get("break_dc"),
                weight_lb=obj_data.get("weight_lb"),
                category=obj_data.get("category", "unknown"),
                tags=tuple(obj_data.get("tags", [])),
                cover_condition=obj_data.get("cover_condition"),
                cover_notes=obj_data.get("cover_notes"),
            )

    @property
    def version(self) -> str:
        """Library version string."""
        return self._version

    @property
    def policy_id(self) -> str:
        """Policy ID for provenance tracking."""
        return self._policy_id

    def get(self, object_class_id: str) -> Optional[ObjectDefault]:
        """Get an object class by ID.

        Args:
            object_class_id: The object class identifier (e.g., "tavern_table")

        Returns:
            ObjectDefault if found, None otherwise.
        """
        return self._objects.get(object_class_id)

    def get_all(self) -> Dict[str, ObjectDefault]:
        """Get all object classes.

        Returns:
            Dict mapping object_class_id to ObjectDefault.
        """
        return dict(self._objects)

    def get_by_tag(self, tag: str) -> List[ObjectDefault]:
        """Get all objects that have a specific tag.

        Args:
            tag: Location tag to filter by (e.g., "tavern", "dungeon")

        Returns:
            List of matching ObjectDefault instances.
        """
        return [obj for obj in self._objects.values() if tag in obj.tags]

    def get_by_category(self, category: str) -> List[ObjectDefault]:
        """Get all objects of a specific category.

        Args:
            category: Category to filter by (e.g., "furniture", "structural")

        Returns:
            List of matching ObjectDefault instances.
        """
        return [obj for obj in self._objects.values() if obj.category == category]

    def get_by_material(self, material: str) -> List[ObjectDefault]:
        """Get all objects made of a specific material.

        Args:
            material: Material to filter by (e.g., "wood", "stone", "iron")

        Returns:
            List of matching ObjectDefault instances.
        """
        return [obj for obj in self._objects.values() if obj.material == material]

    def list_ids(self) -> List[str]:
        """Get all object class IDs.

        Returns:
            Sorted list of object_class_id strings.
        """
        return sorted(self._objects.keys())

    def __len__(self) -> int:
        """Number of object classes in the library."""
        return len(self._objects)

    def __contains__(self, object_class_id: str) -> bool:
        """Check if an object class exists."""
        return object_class_id in self._objects
