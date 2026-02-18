"""TableObject registry types for the Table UI.

Server-side types for table object identity, position, and zone membership.
Follows the same frozen-dataclass + to_dict()/from_dict() pattern as pending.py.

Types:
- TableObjectState: Server-side record of an object's position and zone.
- ObjectPositionUpdate: Client -> Server position change REQUEST.

Zone validation:
- VALID_ZONES defines the set of valid zone names.
- validate_zone_position() checks zone membership.
- Server is authoritative for zone validation (doctrine section 16).

Authority: WO-UI-02, DOCTRINE_04_TABLE_UI_MEMO_V4 section 16, section 19.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Zone definitions — loaded from zones.json (single source of truth)
# ---------------------------------------------------------------------------

_ZONES_JSON_PATH = Path(__file__).parent / "zones.json"

def _load_zone_bounds() -> Dict[str, Tuple[float, float, float, float]]:
    """Load zone boundary data from zones.json."""
    with open(_ZONES_JSON_PATH, encoding="utf-8") as f:
        zones = json.load(f)
    return {
        z["name"]: (z["centerX"], z["centerZ"], z["halfWidth"], z["halfHeight"])
        for z in zones
    }

_ZONE_BOUNDS: Dict[str, Tuple[float, float, float, float]] = _load_zone_bounds()

VALID_ZONES: FrozenSet[str] = frozenset(_ZONE_BOUNDS.keys())


def zone_for_position(x: float, z: float) -> Optional[str]:
    """Return the zone name containing (x, z), or None if outside all zones.

    Checks zones in priority order: player, map, dm.
    If a position falls in overlapping zones, the first match wins.
    """
    for zone_name in ("player", "map", "dm"):
        cx, cz, hw, hh = _ZONE_BOUNDS[zone_name]
        if (cx - hw) <= x <= (cx + hw) and (cz - hh) <= z <= (cz + hh):
            return zone_name
    return None


def validate_zone_position(
    new_position: Tuple[float, float, float],
    new_zone: str,
) -> bool:
    """Validate that new_position is within new_zone.

    Returns True if valid, False if not.
    """
    if new_zone not in VALID_ZONES:
        logger.debug("Invalid zone: %r. Valid zones: %s", new_zone, sorted(VALID_ZONES))
        return False

    x, _y, z = new_position
    actual_zone = zone_for_position(x, z)
    if actual_zone != new_zone:
        logger.debug(
            "Position (%s, %s) is not within zone %r (detected zone: %r)",
            x, z, new_zone, actual_zone,
        )
        return False
    return True


# ---------------------------------------------------------------------------
# TableObjectState (server record)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TableObjectState:
    """Server-side record of a table object's identity and position.

    Attributes:
        object_id: Unique identifier for this object.
        kind: Object type (e.g. "card", "token", "die").
        position: World-space position as (x, y, z).
        zone: Zone the object is in ("player", "map", "dm").
    """

    object_id: str
    kind: str
    position: Tuple[float, float, float]
    zone: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "TABLE_OBJECT_STATE",
            "object_id": self.object_id,
            "kind": self.kind,
            "position": list(self.position),
            "zone": self.zone,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TableObjectState:
        return cls(
            object_id=data["object_id"],
            kind=data["kind"],
            position=tuple(data["position"]),
            zone=data["zone"],
        )


# ---------------------------------------------------------------------------
# ObjectPositionUpdate (client -> server REQUEST)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ObjectPositionUpdate:
    """Client requests to move a table object to a new position.

    This is a REQUEST type (doctrine section 16 -- UI sends REQUEST only).
    No outcome or legality fields. Server validates and acknowledges.

    Attributes:
        object_id: The object being moved.
        new_position: Target world-space position as (x, y, z).
        new_zone: Target zone name.
    """

    object_id: str
    new_position: Tuple[float, float, float]
    new_zone: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "OBJECT_POSITION_UPDATE",
            "object_id": self.object_id,
            "new_position": list(self.new_position),
            "new_zone": self.new_zone,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ObjectPositionUpdate:
        return cls(
            object_id=data["object_id"],
            new_position=tuple(data["new_position"]),
            new_zone=data["new_zone"],
        )


# ---------------------------------------------------------------------------
# Object registry — tracks objects by id
# ---------------------------------------------------------------------------

class TableObjectRegistry:
    """Server-side registry of table objects.

    Tracks TableObjectState by object_id. Rejects duplicate IDs on add.
    """

    def __init__(self) -> None:
        self._objects: Dict[str, TableObjectState] = {}

    def add(self, obj: TableObjectState) -> None:
        """Add an object to the registry. Raises ValueError on duplicate ID."""
        if obj.object_id in self._objects:
            raise ValueError(
                f"Duplicate object_id: {obj.object_id!r} already in registry"
            )
        self._objects[obj.object_id] = obj

    def get(self, object_id: str) -> Optional[TableObjectState]:
        """Get an object by ID, or None if not found."""
        return self._objects.get(object_id)

    def remove(self, object_id: str) -> Optional[TableObjectState]:
        """Remove and return an object by ID, or None if not found."""
        return self._objects.pop(object_id, None)

    def update_position(
        self,
        update: ObjectPositionUpdate,
    ) -> Optional[TableObjectState]:
        """Apply a position update. Returns the new state, or None if invalid.

        Validates zone membership. If valid, replaces the old state with a new
        frozen TableObjectState at the updated position.
        """
        old = self._objects.get(update.object_id)
        if old is None:
            return None

        valid = validate_zone_position(update.new_position, update.new_zone)
        if not valid:
            return None

        new_state = TableObjectState(
            object_id=old.object_id,
            kind=old.kind,
            position=update.new_position,
            zone=update.new_zone,
        )
        self._objects[old.object_id] = new_state
        return new_state

    def all_objects(self) -> list[TableObjectState]:
        """Return all objects sorted by object_id for deterministic ordering."""
        return sorted(self._objects.values(), key=lambda o: o.object_id)

    def __len__(self) -> int:
        return len(self._objects)

    def __contains__(self, object_id: str) -> bool:
        return object_id in self._objects
