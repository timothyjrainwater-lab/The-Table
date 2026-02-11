"""WO-040: Scene Management — Scene Transitions, Encounters, Rest, and Loot

Manages dungeon crawl scene transitions, encounter triggers, rest mechanics, and loot.

LAYER ARCHITECTURE:
- SceneManager is Lens layer (presentation/navigation, not mechanical authority)
- Combat triggers delegate to Box (initiative.py, combat_controller.py)
- Rest healing is a Box operation via deepcopy state mutation
- FrozenWorldStateView for scene lookups, WorldState mutation only through events

D&D 3.5E REST MECHANICS (NOT 5E):
- Natural healing: 1 HP per character level per day of rest (PHB p.146)
- Long-term care (Heal DC 15): 2 HP per level per day
- Complete bed rest: 1.5 HP per level per day (level * 1.5)
- NO "short rest" hit dice spending (that's 5e only)

BOUNDARY LAWS:
- BL-003: Lens layer must NOT import Box internals (only state, initiative, combat_controller)
- BL-020: Use FrozenWorldStateView for read-only access
- Event sourcing for all state changes

Reference: docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md (WO-040)
"""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.core.event_log import Event
from aidm.core.rng_manager import RNGManager
from aidm.core.initiative import roll_initiative_for_all_actors, InitiativeRoll
from aidm.schemas.entity_fields import EF


# ==============================================================================
# SCENE DATA STRUCTURES
# ==============================================================================

@dataclass(frozen=True)
class Exit:
    """Scene exit definition."""

    exit_id: str
    """Unique identifier for this exit"""

    destination_scene_id: str
    """Scene ID this exit leads to"""

    description: str
    """Player-facing description (e.g., 'A dark corridor leading north')"""

    locked: bool = False
    """Whether exit is locked (requires unlock action)"""

    hidden: bool = False
    """Whether exit requires Search check to discover"""


@dataclass(frozen=True)
class EncounterDef:
    """Encounter definition for scene triggers."""

    encounter_id: str
    """Unique identifier for this encounter"""

    monster_ids: List[str]
    """List of monster entity IDs to spawn"""

    trigger_condition: str
    """Trigger condition (e.g., 'on_entry', 'manual', 'time:round:5')"""

    initiative_data: List[tuple[str, int]] = field(default_factory=list)
    """List of (monster_id, dex_modifier) for initiative rolls"""

    triggered: bool = False
    """Whether this encounter has already been triggered"""


@dataclass(frozen=True)
class LootDef:
    """Loot definition for scene items."""

    item_id: str
    """Unique identifier for this loot item"""

    description: str
    """Item description (e.g., '+1 longsword', '500 gp')"""

    location: str
    """Where the item is located (e.g., 'in the chest', 'on the altar')"""

    hidden: bool = False
    """Whether item requires Search check to discover"""

    collected: bool = False
    """Whether item has been collected"""


@dataclass(frozen=True)
class SceneState:
    """Complete scene state including exits, encounters, loot, and environment.

    This is the core data structure for scene management. Immutable to ensure
    scene definitions remain stable across sessions.
    """

    scene_id: str
    """Unique identifier for this scene"""

    name: str
    """Display name of the scene"""

    description: str
    """Full scene description for players"""

    exits: List[Exit] = field(default_factory=list)
    """Available exits from this scene"""

    encounters: List[EncounterDef] = field(default_factory=list)
    """Encounter definitions for this scene"""

    loot: List[LootDef] = field(default_factory=list)
    """Loot items in this scene"""

    environmental: Dict[str, Any] = field(default_factory=dict)
    """Environmental data (terrain tags, hazards, lighting)"""


# ==============================================================================
# RESULT STRUCTURES
# ==============================================================================

@dataclass(frozen=True)
class TransitionResult:
    """Result of scene transition operation."""

    success: bool
    """Whether transition succeeded"""

    new_scene: Optional[SceneState]
    """New scene state (None if transition failed)"""

    events: List[Dict[str, Any]] = field(default_factory=list)
    """Scene transition events for EventLog"""

    narrative_hint: str = ""
    """Narrative hint for Lens/Spark (e.g., 'The party enters a dark corridor')"""

    error_message: Optional[str] = None
    """Error message if transition failed"""


@dataclass(frozen=True)
class EncounterResult:
    """Result of encounter trigger operation."""

    encounter_id: str
    """Encounter ID that was triggered"""

    triggered: bool
    """Whether encounter was successfully triggered"""

    initiative_rolls: List[InitiativeRoll] = field(default_factory=list)
    """Initiative rolls for all combatants"""

    initiative_order: List[str] = field(default_factory=list)
    """Initiative order (entity IDs, highest to lowest)"""

    events: List[Dict[str, Any]] = field(default_factory=list)
    """Encounter events for EventLog"""

    narrative_hint: str = ""
    """Narrative hint for Lens/Spark"""


@dataclass(frozen=True)
class RestResult:
    """Result of rest processing."""

    rest_type: Literal["8_hours", "long_term_care", "bed_rest"]
    """Type of rest taken"""

    healing_applied: Dict[str, int]
    """Map of entity_id to HP restored"""

    events: List[Dict[str, Any]] = field(default_factory=list)
    """Rest events for EventLog"""

    narrative_hint: str = ""
    """Narrative hint for Lens/Spark"""


# ==============================================================================
# SCENE MANAGER
# ==============================================================================

class SceneManager:
    """Manages scene transitions, encounters, rest, and loot.

    This is a Lens layer component — it handles navigation and presentation,
    but delegates mechanical authority to Box components (initiative, combat).

    Usage:
        manager = SceneManager(scenes=scene_definitions)

        # Load scene
        scene = manager.load_scene("dungeon_entrance")

        # Transition between scenes
        result = manager.transition_scene(
            from_scene="dungeon_entrance",
            exit_id="north_corridor",
            world_state=state
        )

        # Trigger encounter
        encounter_result = manager.trigger_encounter(
            scene=scene,
            world_state=state,
            rng=rng_manager
        )

        # Process rest
        rest_result = manager.process_rest(
            rest_type="8_hours",
            world_state=state,
            rng=rng_manager
        )
    """

    def __init__(self, scenes: Dict[str, SceneState]):
        """Initialize scene manager.

        Args:
            scenes: Dictionary of scene_id -> SceneState
        """
        self.scenes = scenes

    def load_scene(self, scene_id: str) -> SceneState:
        """Load a scene by ID.

        Args:
            scene_id: Scene ID to load

        Returns:
            SceneState for the requested scene

        Raises:
            KeyError: If scene_id not found
        """
        if scene_id not in self.scenes:
            raise KeyError(f"Scene not found: {scene_id}")

        return self.scenes[scene_id]

    def transition_scene(
        self,
        from_scene: str,
        exit_id: str,
        world_state: WorldState,
    ) -> TransitionResult:
        """Transition from one scene to another via an exit.

        Validates the exit exists and is accessible, then loads the destination scene.
        Preserves all entity state during transition.

        Args:
            from_scene: Current scene ID
            exit_id: Exit ID to use for transition
            world_state: Current world state (preserved during transition)

        Returns:
            TransitionResult with new scene and events
        """
        # Load source scene
        try:
            source_scene = self.load_scene(from_scene)
        except KeyError:
            return TransitionResult(
                success=False,
                new_scene=None,
                error_message=f"Source scene not found: {from_scene}"
            )

        # Find exit
        exit_obj = None
        for exit_candidate in source_scene.exits:
            if exit_candidate.exit_id == exit_id:
                exit_obj = exit_candidate
                break

        if exit_obj is None:
            return TransitionResult(
                success=False,
                new_scene=None,
                error_message=f"Exit not found: {exit_id} in scene {from_scene}"
            )

        # Check if exit is locked
        if exit_obj.locked:
            return TransitionResult(
                success=False,
                new_scene=None,
                error_message=f"Exit is locked: {exit_id}"
            )

        # Load destination scene
        try:
            dest_scene = self.load_scene(exit_obj.destination_scene_id)
        except KeyError:
            return TransitionResult(
                success=False,
                new_scene=None,
                error_message=f"Destination scene not found: {exit_obj.destination_scene_id}"
            )

        # Generate transition event
        events = [
            {
                "type": "scene_transition",
                "from_scene": from_scene,
                "to_scene": exit_obj.destination_scene_id,
                "exit_id": exit_id,
                "exit_description": exit_obj.description,
            }
        ]

        # Generate narrative hint
        narrative_hint = f"The party moves through {exit_obj.description} into {dest_scene.name}."

        return TransitionResult(
            success=True,
            new_scene=dest_scene,
            events=events,
            narrative_hint=narrative_hint,
        )

    def trigger_encounter(
        self,
        scene: SceneState,
        world_state: WorldState,
        rng: RNGManager,
        trigger_condition: str = "on_entry",
    ) -> Optional[EncounterResult]:
        """Trigger an encounter in the current scene.

        Delegates to Box layer for initiative rolling via initiative.py.
        Does NOT modify world_state directly — returns events for event sourcing.

        Args:
            scene: Current scene state
            world_state: Current world state
            rng: RNG manager for initiative rolls
            trigger_condition: Trigger condition to match (default "on_entry")

        Returns:
            EncounterResult if encounter triggered, None if no matching encounter
        """
        # Find encounter matching trigger condition
        encounter = None
        for enc in scene.encounters:
            if enc.trigger_condition == trigger_condition and not enc.triggered:
                encounter = enc
                break

        if encounter is None:
            return None

        # Delegate to Box: Roll initiative for all combatants
        # Combine party and monsters
        actors = []

        # Add monsters from encounter
        for monster_id, dex_mod in encounter.initiative_data:
            actors.append((monster_id, dex_mod))

        # Add party members from world_state
        frozen_view = FrozenWorldStateView(world_state)
        for entity_id, entity in frozen_view.entities.items():
            if entity.get(EF.TEAM) == "party":
                dex_mod = entity.get(EF.DEX_MOD, 0)
                actors.append((entity_id, dex_mod))

        # Roll initiative (Box operation)
        initiative_rolls, initiative_order = roll_initiative_for_all_actors(
            actors=actors,
            rng=rng
        )

        # Generate encounter events
        events = [
            {
                "type": "encounter_triggered",
                "encounter_id": encounter.encounter_id,
                "scene_id": scene.scene_id,
                "monster_ids": encounter.monster_ids,
                "trigger_condition": trigger_condition,
            },
            {
                "type": "initiative_rolled",
                "initiative_order": initiative_order,
                "initiative_rolls": [roll.to_dict() for roll in initiative_rolls],
            }
        ]

        # Generate narrative hint
        narrative_hint = f"A combat encounter begins! {len(encounter.monster_ids)} enemies appear."

        return EncounterResult(
            encounter_id=encounter.encounter_id,
            triggered=True,
            initiative_rolls=initiative_rolls,
            initiative_order=initiative_order,
            events=events,
            narrative_hint=narrative_hint,
        )

    def process_rest(
        self,
        rest_type: Literal["8_hours", "long_term_care", "bed_rest"],
        world_state: WorldState,
        rng: RNGManager,
    ) -> RestResult:
        """Process rest healing for party members.

        D&D 3.5e rest healing rules (PHB p.146):
        - 8 hours rest: 1 HP per character level per day
        - Long-term care (Heal DC 15): 2 HP per level per day
        - Complete bed rest: level * 1.5 HP per day

        Args:
            rest_type: Type of rest ("8_hours", "long_term_care", "bed_rest")
            world_state: Current world state
            rng: RNG manager (not used for rest, but kept for consistency)

        Returns:
            RestResult with healing applied and events
        """
        healing_applied = {}
        events = []

        # Use FrozenWorldStateView for read-only access
        frozen_view = FrozenWorldStateView(world_state)

        for entity_id, entity in frozen_view.entities.items():
            # Only heal party members
            if entity.get(EF.TEAM) != "party":
                continue

            # Skip if entity has no HP data
            if EF.HP_CURRENT not in entity or EF.HP_MAX not in entity:
                continue

            # Get entity level
            level = entity.get(EF.LEVEL, 1)
            hp_current = entity.get(EF.HP_CURRENT, 0)
            hp_max = entity.get(EF.HP_MAX, 1)

            # Calculate healing amount based on rest type
            if rest_type == "8_hours":
                # 1 HP per level per day (PHB p.146)
                healing = level
            elif rest_type == "long_term_care":
                # 2 HP per level per day with Heal DC 15 (PHB p.146)
                healing = level * 2
            elif rest_type == "bed_rest":
                # 1.5 HP per level per day with complete bed rest (PHB p.146)
                healing = int(level * 1.5)
            else:
                healing = 0

            # Don't overheal
            hp_after = min(hp_current + healing, hp_max)
            actual_healing = hp_after - hp_current

            if actual_healing > 0:
                healing_applied[entity_id] = actual_healing

                # Generate healing event
                events.append({
                    "type": "rest_healing",
                    "entity_id": entity_id,
                    "rest_type": rest_type,
                    "healing_amount": actual_healing,
                    "hp_before": hp_current,
                    "hp_after": hp_after,
                })

        # Generate narrative hint
        if rest_type == "8_hours":
            narrative_hint = "The party rests for 8 hours, recovering from their wounds."
        elif rest_type == "long_term_care":
            narrative_hint = "The party receives long-term care, significantly recovering from their injuries."
        else:  # bed_rest
            narrative_hint = "The party rests in complete comfort, recovering from their wounds."

        return RestResult(
            rest_type=rest_type,
            healing_applied=healing_applied,
            events=events,
            narrative_hint=narrative_hint,
        )
