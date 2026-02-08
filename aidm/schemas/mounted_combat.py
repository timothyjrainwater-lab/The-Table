"""Mounted combat schemas for CP-18A — Rider–Mount Coupling.

Data-only contracts for mounted combat state and intents.
NO RESOLUTION LOGIC IN THIS MODULE.

CP-18A SCOPE:
- Rider-mount coupling model (controlled mounts only)
- Movement delegation (mount moves, rider carried)
- Dismount intents (voluntary and forced)
- Position derivation (rider at mount position)

OUT OF SCOPE:
- Independent mounts (SKR-003)
- Mounted spellcasting (blocked)
- Mounted grapple (SKR-005)
- Feat logic (Mounted Combat, etc.)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from aidm.schemas.attack import GridPosition


class MountType:
    """Mount classification per PHB p.157."""

    WARHORSE = "warhorse"       # War-trained, controllable in combat
    WARPONY = "warpony"         # War-trained pony
    LIGHT_HORSE = "light_horse" # Not war-trained, DC 20 Ride to control
    HEAVY_HORSE = "heavy_horse" # Not war-trained, DC 20 Ride to control
    PONY = "pony"               # Not war-trained, DC 20 Ride to control


class SaddleType:
    """Saddle types affecting Ride checks and dismount."""

    NONE = "none"               # Bareback: -5 Ride penalty
    RIDING = "riding"           # Standard saddle
    MILITARY = "military"       # +2 circumstance bonus, 75% unconscious stay
    PACK = "pack"               # Not for riding


@dataclass
class MountedState:
    """Rider–Mount coupling state stored on RIDER entity.

    DESIGN PRINCIPLE:
    Mount is the "ground truth" for position. Rider position is derived
    from mount position. This prevents position drift and simplifies
    movement resolution.

    Stored in: entities[rider_id]["mounted_state"]

    PHB p.157: "Your mount acts on your initiative count as you direct it.
    You move at its speed, but the mount uses its action to move."
    """

    mount_id: str
    """Entity ID of the mount."""

    is_controlled: bool
    """True if mount is war-trained or rider succeeds DC 20 Ride check.

    Controlled mount: Acts on rider's initiative, moves as directed.
    Uncontrolled mount (CP-18A scope): Rider must spend move action to control.
    Independent mount (OUT OF SCOPE): Mount has own initiative, own actions.
    """

    saddle_type: str = SaddleType.RIDING
    """Saddle type for Ride check bonuses and unconscious fall chance."""

    mounted_at_event_id: int = 0
    """Event ID when mounting occurred (provenance tracking)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for WorldState storage."""
        return {
            "mount_id": self.mount_id,
            "is_controlled": self.is_controlled,
            "saddle_type": self.saddle_type,
            "mounted_at_event_id": self.mounted_at_event_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MountedState":
        """Deserialize from WorldState storage."""
        return cls(
            mount_id=data["mount_id"],
            is_controlled=data["is_controlled"],
            saddle_type=data.get("saddle_type", SaddleType.RIDING),
            mounted_at_event_id=data.get("mounted_at_event_id", 0)
        )


@dataclass
class MountedMoveIntent:
    """Intent for mount to move while carrying rider.

    CP-18A SCOPE:
    - Controlled mount only (rider directs movement)
    - Movement uses mount's speed
    - Rider cannot take move action independently while mounted
    - AoOs provoked by mount, not rider

    PHB p.157: "Your mount acts on your initiative count as you direct it.
    You move at its speed, but the mount uses its action to move."
    """

    rider_id: str
    """Entity directing the movement (must be mounted)."""

    mount_id: str
    """Entity actually moving (derived from rider's mounted_state)."""

    from_pos: GridPosition
    """Starting position of mount."""

    to_pos: GridPosition
    """Destination position of mount."""

    path: Optional[List[GridPosition]] = None
    """Intermediate squares if provided (for AoO checking along path)."""

    is_charge: bool = False
    """True if this is a charge action (PHB p.154)."""

    is_run: bool = False
    """True if mount is running (×4 speed, PHB p.144)."""

    is_double_move: bool = False
    """True if mount is taking double move (×2 speed)."""

    def __post_init__(self):
        """Validate mounted move intent."""
        if not self.rider_id:
            raise ValueError("rider_id cannot be empty")
        if not self.mount_id:
            raise ValueError("mount_id cannot be empty")


@dataclass
class DismountIntent:
    """Intent to dismount from a mount.

    PHB p.80 (Ride skill), PHB p.143:
    - Normal dismount: Move action
    - Fast dismount (DC 20 Ride): Free action
    """

    rider_id: str
    """Entity dismounting."""

    fast_dismount: bool = False
    """True to attempt DC 20 fast dismount (free action)."""

    dismount_to: Optional[GridPosition] = None
    """Target square for dismount. If None, system chooses adjacent."""

    def __post_init__(self):
        """Validate dismount intent."""
        if not self.rider_id:
            raise ValueError("rider_id cannot be empty")


@dataclass
class MountIntent:
    """Intent to mount a creature.

    PHB p.80 (Ride skill), PHB p.143:
    - Normal mount: Move action
    - Fast mount (DC 20 Ride): Free action
    """

    rider_id: str
    """Entity mounting."""

    mount_id: str
    """Entity being mounted."""

    fast_mount: bool = False
    """True to attempt DC 20 fast mount (free action)."""

    saddle_type: str = SaddleType.RIDING
    """Saddle type (affects Ride checks and fall chance)."""

    def __post_init__(self):
        """Validate mount intent."""
        if not self.rider_id:
            raise ValueError("rider_id cannot be empty")
        if not self.mount_id:
            raise ValueError("mount_id cannot be empty")
