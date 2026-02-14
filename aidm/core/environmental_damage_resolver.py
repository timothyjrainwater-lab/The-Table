"""Environmental damage resolver for CP-20 — Discrete Environmental Damage.

Implements deterministic resolution for contact hazards:
- Fire squares (1d6 fire damage on entry)
- Acid pools (1d6 acid damage on entry)
- Lava edges (2d6 fire damage on entry)
- Spiked pits (falling damage + 1d6 piercing on fall)

DESIGN PRINCIPLES (per CP20_ENVIRONMENTAL_DAMAGE_DECISIONS.md):
- One-shot damage only (no persistence, no ongoing effects)
- No saving throws (per design doc scope)
- Triggers on entry or forced movement
- Integrates with existing hazard resolution pipeline

ORDERING CONTRACT (preserved from CP-19):
1. AoOs resolved first
2. Movement executed
3. Hazard detection (CP-19)
4. Environmental damage resolution (CP-20)

RNG STREAM: "combat" (environmental damage dice only)
"""

from copy import deepcopy
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF


# ==============================================================================
# ENVIRONMENTAL HAZARD TYPES
# ==============================================================================

class EnvironmentalHazardType(Enum):
    """Types of environmental damage hazards."""
    FIRE = "fire"
    ACID = "acid"
    LAVA = "lava"
    SPIKED_PIT = "spiked_pit"


# Hazard configuration: (dice_count, dice_size, damage_type)
HAZARD_DAMAGE_CONFIG: Dict[str, Tuple[int, int, str]] = {
    "fire": (1, 6, "fire"),           # 1d6 fire
    "acid": (1, 6, "acid"),           # 1d6 acid
    "lava": (2, 6, "fire"),           # 2d6 fire
    "spiked_pit": (1, 6, "piercing"), # 1d6 piercing (added to falling damage)
}


# ==============================================================================
# ENVIRONMENTAL DAMAGE RESULT
# ==============================================================================

@dataclass
class EnvironmentalDamageResult:
    """Result of environmental damage resolution.

    Captures all information needed for event emission and state update.
    """
    entity_id: str
    """Entity that took damage."""

    hazard_type: str
    """Type of hazard: 'fire', 'acid', 'lava', 'spiked_pit'."""

    position: Dict[str, int]
    """Position where damage occurred."""

    dice_count: int
    """Number of dice rolled."""

    dice_size: int
    """Size of dice (typically 6)."""

    dice_results: List[int] = field(default_factory=list)
    """Individual die results."""

    total_damage: int = 0
    """Total damage dealt."""

    damage_type: str = ""
    """Damage type: 'fire', 'acid', 'piercing'."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "entity_id": self.entity_id,
            "hazard_type": self.hazard_type,
            "position": self.position,
            "dice_count": self.dice_count,
            "dice_size": self.dice_size,
            "dice_results": list(self.dice_results),
            "total_damage": self.total_damage,
            "damage_type": self.damage_type,
        }


# ==============================================================================
# HAZARD DETECTION
# ==============================================================================

def get_environmental_hazard(
    world_state: WorldState,
    position: Dict[str, int]
) -> Optional[str]:
    """Check if position has an environmental damage hazard.

    Environmental hazards are stored in terrain_map with hazard_type field.

    Args:
        world_state: Current world state
        position: Position to check

    Returns:
        Hazard type string ('fire', 'acid', 'lava', 'spiked_pit') or None
    """
    terrain_map = world_state.active_combat.get("terrain_map") if world_state.active_combat else None
    if terrain_map is None:
        return None

    key = f"{position['x']},{position['y']}"
    cell_data = terrain_map.get(key)
    if cell_data is None:
        return None

    return cell_data.get("hazard_type")


def has_environmental_hazard(
    world_state: WorldState,
    position: Dict[str, int]
) -> bool:
    """Check if position has any environmental damage hazard.

    Args:
        world_state: Current world state
        position: Position to check

    Returns:
        True if position has an environmental hazard
    """
    return get_environmental_hazard(world_state, position) is not None


# ==============================================================================
# ENVIRONMENTAL DAMAGE RESOLUTION
# ==============================================================================

def resolve_environmental_damage(
    entity_id: str,
    position: Dict[str, int],
    hazard_type: str,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState, EnvironmentalDamageResult]:
    """Resolve environmental damage from a contact hazard.

    Per CP-20 design:
    - Damage is one-shot (triggers once on entry)
    - No persistence (no ongoing damage)
    - No saving throws
    - Uses "combat" RNG stream only

    Args:
        entity_id: Entity taking damage
        position: Position of hazard
        hazard_type: Type of hazard ('fire', 'acid', 'lava', 'spiked_pit')
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Event timestamp

    Returns:
        Tuple of (events, updated_world_state, EnvironmentalDamageResult)
    """
    events: List[Event] = []
    current_event_id = next_event_id
    current_timestamp = timestamp

    # Get hazard damage configuration
    if hazard_type not in HAZARD_DAMAGE_CONFIG:
        # Unknown hazard type - return empty result
        result = EnvironmentalDamageResult(
            entity_id=entity_id,
            hazard_type=hazard_type,
            position=position,
            dice_count=0,
            dice_size=0,
            dice_results=[],
            total_damage=0,
            damage_type="unknown",
        )
        return events, world_state, result

    dice_count, dice_size, damage_type = HAZARD_DAMAGE_CONFIG[hazard_type]

    # Roll damage
    combat_rng = rng.stream("combat")
    dice_results = [combat_rng.randint(1, dice_size) for _ in range(dice_count)]
    total_damage = sum(dice_results)

    # Create result
    result = EnvironmentalDamageResult(
        entity_id=entity_id,
        hazard_type=hazard_type,
        position=position,
        dice_count=dice_count,
        dice_size=dice_size,
        dice_results=dice_results,
        total_damage=total_damage,
        damage_type=damage_type,
    )

    # Emit environmental_damage event
    events.append(Event(
        event_id=current_event_id,
        event_type="environmental_damage",
        timestamp=current_timestamp,
        payload={
            "entity_id": entity_id,
            "hazard_type": hazard_type,
            "position": position,
            "dice": f"{dice_count}d{dice_size}",
            "dice_results": dice_results,
            "damage_type": damage_type,
            "total_damage": total_damage,
        },
        citations=[{"source_id": "dmg_srd", "page": 303}],  # DMG environmental hazards
    ))
    current_event_id += 1
    current_timestamp += 0.01

    # Apply damage to entity
    entity = world_state.entities.get(entity_id)
    if entity and total_damage > 0:
        hp_before = entity.get(EF.HP_CURRENT, 0)
        hp_after = hp_before - total_damage

        # Emit hp_changed event
        events.append(Event(
            event_id=current_event_id,
            event_type="hp_changed",
            timestamp=current_timestamp,
            payload={
                "entity_id": entity_id,
                "hp_before": hp_before,
                "hp_after": hp_after,
                "delta": -total_damage,
                "source": f"environmental_{hazard_type}",
                "damage_type": damage_type,
            },
        ))
        current_event_id += 1
        current_timestamp += 0.01

        # Update entity HP
        entities = deepcopy(world_state.entities)
        updated_entity = entities[entity_id]
        updated_entity[EF.HP_CURRENT] = hp_after
        entities[entity_id] = updated_entity

        # Check for defeat
        if hp_after <= 0:
            updated_entity[EF.DEFEATED] = True
            entities[entity_id] = updated_entity

            events.append(Event(
                event_id=current_event_id,
                event_type="entity_defeated",
                timestamp=current_timestamp,
                payload={
                    "entity_id": entity_id,
                    "hp_final": hp_after,
                    "defeated_by": f"environmental_{hazard_type}",
                },
            ))
            current_event_id += 1

        world_state = WorldState(
            ruleset_version=world_state.ruleset_version,
            entities=entities,
            active_combat=world_state.active_combat,
        )

    return events, world_state, result


def resolve_spiked_pit_damage(
    entity_id: str,
    position: Dict[str, int],
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState, EnvironmentalDamageResult]:
    """Resolve additional spike damage for spiked pits.

    Per CP-20 design: Spiked pits deal falling damage + 1d6 piercing.
    This function handles ONLY the spike damage; falling damage is
    resolved separately by resolve_falling().

    Args:
        entity_id: Entity that fell into spiked pit
        position: Position of spiked pit
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Event timestamp

    Returns:
        Tuple of (events, updated_world_state, EnvironmentalDamageResult)
    """
    return resolve_environmental_damage(
        entity_id=entity_id,
        position=position,
        hazard_type="spiked_pit",
        world_state=world_state,
        rng=rng,
        next_event_id=next_event_id,
        timestamp=timestamp,
    )


# ==============================================================================
# ENTRY HAZARD CHECK (for movement integration)
# ==============================================================================

def check_and_resolve_entry_hazard(
    entity_id: str,
    position: Dict[str, int],
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState, Optional[EnvironmentalDamageResult]]:
    """Check for and resolve environmental hazards on cell entry.

    Called when an entity enters a cell (voluntary or forced movement).
    Checks for fire, acid, or lava hazards and resolves damage.

    Note: Spiked pits are handled separately via resolve_spiked_pit_damage()
    since they occur on falling, not simple entry.

    Args:
        entity_id: Entity entering the cell
        position: Position being entered
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Event timestamp

    Returns:
        Tuple of (events, updated_world_state, EnvironmentalDamageResult or None)
    """
    hazard_type = get_environmental_hazard(world_state, position)

    # Skip spiked_pit - handled separately on falling
    if hazard_type is None or hazard_type == "spiked_pit":
        return [], world_state, None

    return resolve_environmental_damage(
        entity_id=entity_id,
        position=position,
        hazard_type=hazard_type,
        world_state=world_state,
        rng=rng,
        next_event_id=next_event_id,
        timestamp=timestamp,
    )
