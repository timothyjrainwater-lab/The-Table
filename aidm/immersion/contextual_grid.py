"""M3 Contextual Grid — Combat grid visibility computation.

Provides:
- compute_grid_state(): Pure function computing grid visibility from world state

Grid is visible only during active combat.
Entity positions extracted from world state entities.
Deterministic: same inputs always produce same output.

BL-020: Contextual grid is a non-engine boundary consumer — receives read-only
        FrozenWorldStateView instead of mutable WorldState.
"""

from typing import Dict, List, Optional

from aidm.core.state import FrozenWorldStateView
from aidm.schemas.immersion import GridEntityPosition, GridRenderState


def compute_grid_state(
    world_state: FrozenWorldStateView,
    previous: Optional[GridRenderState] = None,
) -> GridRenderState:
    """Compute grid render state from world state.

    Pure function — deterministic, no side effects.

    Rules:
    1. active_combat is not None → visible=True, reason="combat_active",
       extract entity positions
    2. active_combat is None + was visible → visible=False,
       reason="combat_ended"
    3. active_combat is None + was not visible → visible=False,
       reason="no_combat"

    Entity positions extracted from entities[*].get("position"),
    sorted by entity_id for determinism.
    Grid dimensions computed from max x/y of positioned entities.

    Args:
        world_state: Current world state (read-only view, BL-020)
        previous: Previous grid state (for transition detection)

    Returns:
        GridRenderState with visibility, positions, and dimensions
    """
    if world_state.active_combat is not None:
        # Combat active — show grid with entity positions
        positions = _extract_positions(world_state)
        dimensions = _compute_dimensions(positions)

        # FUTURE_HOOK: AoE visualization overlays (M4+)
        #   When spellcasting system is integrated, AoE templates
        #   (fireball radius, cone of cold, etc.) could be rendered
        #   as grid overlays. Extract AoE data from active_combat
        #   or scene_card and return as additional overlay data.
        #   Must remain pure — read AoE shapes, never resolve damage.

        # FUTURE_HOOK: terrain overlay rendering (M4+)
        #   Scene cards may include terrain features (difficult terrain,
        #   walls, water, elevation). These could be extracted here
        #   and returned as overlay cells for the grid renderer.
        #   Must remain atmospheric — terrain rules stay in engine.

        return GridRenderState(
            visible=True,
            reason="combat_active",
            entity_positions=positions,
            dimensions=dimensions,
        )

    # No active combat
    if previous is not None and previous.visible:
        return GridRenderState(
            visible=False,
            reason="combat_ended",
            entity_positions=[],
            dimensions=(0, 0),
        )

    return GridRenderState(
        visible=False,
        reason="no_combat",
        entity_positions=[],
        dimensions=(0, 0),
    )


def _extract_positions(world_state: FrozenWorldStateView) -> List[GridEntityPosition]:
    """Extract entity positions from world state.

    Looks for entities with a "position" dict containing x, y coords.
    Returns sorted by entity_id for determinism.
    """
    positions = []

    for entity_id, entity_data in sorted(world_state.entities.items()):
        if not isinstance(entity_data, dict):
            continue

        pos = entity_data.get("position")
        if pos is None or not isinstance(pos, dict):
            continue

        positions.append(
            GridEntityPosition(
                entity_id=entity_id,
                x=pos.get("x", 0),
                y=pos.get("y", 0),
                label=entity_data.get("name", entity_id),
                team=entity_data.get("team", ""),
            )
        )

    return positions


def _compute_dimensions(
    positions: List[GridEntityPosition],
) -> tuple:
    """Compute grid dimensions from entity positions.

    Returns (max_x + 1, max_y + 1) to ensure all entities fit.
    Returns (0, 0) if no positions.
    """
    if not positions:
        return (0, 0)

    max_x = max(p.x for p in positions)
    max_y = max(p.y for p in positions)

    return (max_x + 1, max_y + 1)
