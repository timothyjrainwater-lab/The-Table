"""ScenarioRunner: Reusable combat scenario execution utility.

Orchestrates combat scenarios using existing AIDM components:
- BattleGrid for geometry
- LensIndex for entity indexing
- RNGManager for deterministic randomness
- CombatController for round execution
- STPEmitter for truth packet generation

Collects metrics and verifies determinism through hash comparison.

WO-016: Multi-Encounter Stress Test Suite
"""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import time
import hashlib
import json

from aidm.schemas.testing import (
    ScenarioConfig, CombatantConfig, TerrainPlacement, CoverDegree
)
from aidm.schemas.position import Position
from aidm.schemas.geometry import PropertyMask, PropertyFlag, SizeCategory, Direction
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.geometry_engine import BattleGrid
from aidm.core.lens_index import LensIndex, SourceTier
from aidm.core.box_lens_bridge import BoxLensBridge
from aidm.core.rng_manager import RNGManager, DeterministicRNG
from aidm.core.state import WorldState
from aidm.core.event_log import Event, EventLog
from aidm.core.combat_controller import start_combat, execute_combat_round, CombatRoundResult
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.core.truth_packets import STPLog, STPType
from aidm.core.stp_emitter import STPEmitter


# ==============================================================================
# SCENARIO METRICS — Performance and execution data
# ==============================================================================

@dataclass
class ScenarioMetrics:
    """Metrics collected during scenario execution.

    Captures timing, event counts, and state hashes for analysis.
    """

    total_rounds: int
    """Number of combat rounds executed."""

    total_actions: int
    """Total number of combat actions resolved."""

    time_per_round_ms: List[float]
    """Execution time for each round in milliseconds."""

    time_per_action_ms: List[float]
    """Execution time for each action in milliseconds."""

    stp_count: int
    """Total number of STPs generated."""

    event_log_hash: str
    """SHA-256 hash of the event log for determinism verification."""

    final_state_hash: str
    """SHA-256 hash of the final world state."""

    stps_by_type: Dict[str, int] = field(default_factory=dict)
    """Count of STPs by type."""

    entities_defeated: List[str] = field(default_factory=list)
    """List of defeated entity IDs."""

    total_time_ms: float = 0.0
    """Total execution time in milliseconds."""

    lens_consistency_errors: List[str] = field(default_factory=list)
    """Any Lens/Grid consistency errors detected."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_rounds": self.total_rounds,
            "total_actions": self.total_actions,
            "time_per_round_ms": self.time_per_round_ms,
            "time_per_action_ms": self.time_per_action_ms,
            "stp_count": self.stp_count,
            "event_log_hash": self.event_log_hash,
            "final_state_hash": self.final_state_hash,
            "stps_by_type": self.stps_by_type,
            "entities_defeated": self.entities_defeated,
            "total_time_ms": self.total_time_ms,
            "lens_consistency_errors": self.lens_consistency_errors,
        }


# ==============================================================================
# SIMPLE AI POLICY — Deterministic combat behavior
# ==============================================================================

class SimpleAIPolicy:
    """Simple deterministic AI for combat scenarios.

    Behavior:
    1. Find nearest enemy
    2. If in melee range: attack
    3. If not: move toward nearest enemy (simplified)
    4. Casters may use spells when available
    """

    @staticmethod
    def select_target(
        actor_id: str,
        actor_team: str,
        world_state: WorldState,
    ) -> Optional[str]:
        """Select the nearest valid target.

        Args:
            actor_id: Entity making the selection
            actor_team: Team of the actor
            world_state: Current world state

        Returns:
            Target entity ID, or None if no valid targets
        """
        actor_pos = SimpleAIPolicy._get_position(actor_id, world_state)
        if actor_pos is None:
            return None

        best_target = None
        best_distance = float('inf')

        for entity_id, entity in world_state.entities.items():
            if entity_id == actor_id:
                continue

            entity_team = entity.get(EF.TEAM, "unknown")
            if entity_team == actor_team:
                continue  # Don't attack allies

            if entity.get(EF.DEFEATED, False):
                continue  # Skip defeated

            target_pos = SimpleAIPolicy._get_position(entity_id, world_state)
            if target_pos is None:
                continue

            distance = actor_pos.distance_to(target_pos)
            if distance < best_distance:
                best_distance = distance
                best_target = entity_id

        return best_target

    @staticmethod
    def _get_position(entity_id: str, world_state: WorldState) -> Optional[Position]:
        """Get entity position from world state."""
        entity = world_state.entities.get(entity_id)
        if entity is None:
            return None

        pos_data = entity.get(EF.POSITION)
        if pos_data is None:
            return None

        if isinstance(pos_data, Position):
            return pos_data
        return Position(x=pos_data.get("x", 0), y=pos_data.get("y", 0))


# ==============================================================================
# SCENARIO RUNNER — Main execution utility
# ==============================================================================

class ScenarioRunner:
    """Executes combat scenarios and collects metrics.

    Uses existing AIDM infrastructure for scenario simulation.
    Supports determinism verification through state hashing.
    """

    def __init__(self):
        """Initialize the scenario runner."""
        self._grid: Optional[BattleGrid] = None
        self._lens: Optional[LensIndex] = None
        self._bridge: Optional[BoxLensBridge] = None
        self._rng: Optional[RNGManager] = None
        self._world_state: Optional[WorldState] = None
        self._event_log: Optional[EventLog] = None
        self._stp_log: Optional[STPLog] = None
        self._stp_emitter: Optional[STPEmitter] = None

    def run(self, config: ScenarioConfig) -> ScenarioMetrics:
        """Execute a scenario and collect metrics.

        Args:
            config: Scenario configuration

        Returns:
            ScenarioMetrics with execution data
        """
        start_time = time.perf_counter()

        # Initialize systems
        self._initialize_scenario(config)

        # Execute combat rounds
        time_per_round = []
        time_per_action = []
        total_actions = 0
        entities_defeated = []

        for round_num in range(config.round_limit):
            round_start = time.perf_counter()

            # Check if combat is over (one team eliminated)
            if self._is_combat_over():
                break

            # Execute one combat round
            round_result, action_times = self._execute_round(round_num + 1)

            round_time = (time.perf_counter() - round_start) * 1000
            time_per_round.append(round_time)
            time_per_action.extend(action_times)
            total_actions += len(action_times)

            # Track defeats
            for event in round_result.events:
                if event.event_type == "entity_defeated":
                    defeated_id = event.payload.get("entity_id")
                    if defeated_id and defeated_id not in entities_defeated:
                        entities_defeated.append(defeated_id)

        # Validate final consistency
        consistency_errors = self._validate_consistency()

        # Compute hashes
        event_hash = self._compute_event_log_hash()
        state_hash = self._world_state.state_hash() if self._world_state else ""

        # Collect STP statistics
        stp_count = len(self._stp_log) if self._stp_log else 0
        stps_by_type = self._count_stps_by_type()

        total_time = (time.perf_counter() - start_time) * 1000

        return ScenarioMetrics(
            total_rounds=len(time_per_round),
            total_actions=total_actions,
            time_per_round_ms=time_per_round,
            time_per_action_ms=time_per_action,
            stp_count=stp_count,
            event_log_hash=event_hash,
            final_state_hash=state_hash,
            stps_by_type=stps_by_type,
            entities_defeated=entities_defeated,
            total_time_ms=total_time,
            lens_consistency_errors=consistency_errors,
        )

    def run_determinism_check(self, config: ScenarioConfig) -> bool:
        """Run scenario twice and verify identical results.

        Args:
            config: Scenario configuration (same seed will be used both times)

        Returns:
            True if both runs produced identical results
        """
        # First run
        metrics1 = self.run(config)

        # Second run with same seed
        metrics2 = self.run(config)

        # Compare hashes
        return (
            metrics1.event_log_hash == metrics2.event_log_hash
            and metrics1.final_state_hash == metrics2.final_state_hash
        )

    def _initialize_scenario(self, config: ScenarioConfig) -> None:
        """Initialize all systems for a scenario.

        Args:
            config: Scenario configuration
        """
        # Create grid
        self._grid = BattleGrid(config.grid_width, config.grid_height)

        # Apply terrain
        self._apply_terrain(config.terrain)

        # Create Lens index
        self._lens = LensIndex()

        # Create RNG manager
        self._rng = RNGManager(config.seed)

        # Create event log
        self._event_log = EventLog()

        # Create STP infrastructure
        self._stp_log = STPLog()
        self._stp_emitter = STPEmitter(self._stp_log, turn=0, initiative=0)

        # Create world state with combatants
        self._world_state = self._create_world_state(config)

        # Create bridge
        self._bridge = BoxLensBridge(self._grid, self._lens)

        # Place entities on grid and index in Lens
        self._place_combatants(config.combatants)

        # Start combat
        actors = self._get_initiative_actors(config.combatants)
        self._world_state, events, _ = start_combat(
            world_state=self._world_state,
            actors=actors,
            rng=self._rng,
            next_event_id=0,
            timestamp=0.0,
        )

        # Add events to log
        for event in events:
            self._event_log.append(event)

    def _apply_terrain(self, terrain: List[TerrainPlacement]) -> None:
        """Apply terrain placements to the grid.

        Args:
            terrain: List of terrain placements
        """
        for placement in terrain:
            if not self._grid.in_bounds(placement.coord):
                continue

            cell = self._grid.get_cell(placement.coord)

            # Set cell properties based on terrain type
            mask = PropertyMask()

            if placement.blocks_los:
                mask = mask.set_flag(PropertyFlag.OPAQUE)
            if placement.blocks_loe:
                mask = mask.set_flag(PropertyFlag.SOLID)
            if placement.is_difficult:
                mask = mask.set_flag(PropertyFlag.DIFFICULT)

            # Common terrain types
            if placement.terrain_type == "wall":
                mask = mask.set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
            elif placement.terrain_type == "pillar":
                mask = mask.set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)
            elif placement.terrain_type == "table":
                mask = mask.set_flag(PropertyFlag.SOLID)
            elif placement.terrain_type == "boulder":
                mask = mask.set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

            cell.cell_mask = mask
            cell.elevation = placement.elevation
            cell.height = placement.height

    def _create_world_state(self, config: ScenarioConfig) -> WorldState:
        """Create initial world state from config.

        Args:
            config: Scenario configuration

        Returns:
            Initialized WorldState
        """
        entities = {}

        for combatant in config.combatants:
            entity = {
                EF.ENTITY_ID: combatant.name,
                EF.TEAM: combatant.team,
                EF.HP_CURRENT: combatant.hp,
                EF.HP_MAX: combatant.hp,
                EF.AC: combatant.ac,
                EF.POSITION: combatant.position.to_dict(),
                EF.DEFEATED: False,
                EF.SIZE_CATEGORY: combatant.size.lower(),
                EF.BAB: combatant.bab,
                EF.STR_MOD: combatant.str_mod,
                EF.DEX_MOD: combatant.dex_mod,
                EF.CON_MOD: combatant.con_mod,
                EF.WIS_MOD: combatant.wis_mod,
                EF.SAVE_FORT: combatant.save_fort,
                EF.SAVE_REF: combatant.save_ref,
                EF.SAVE_WILL: combatant.save_will,
                EF.CONDITIONS: {},
            }

            # Store attack config for later use
            if combatant.attacks:
                entity["attacks"] = [a.to_dict() for a in combatant.attacks]
                # Set attack bonus from first attack
                entity[EF.ATTACK_BONUS] = combatant.attacks[0].attack_bonus

            entities[combatant.name] = entity

        return WorldState(
            ruleset_version="RAW_3.5",
            entities=entities,
            active_combat=None,
        )

    def _place_combatants(self, combatants: List[CombatantConfig]) -> None:
        """Place combatants on grid and index in Lens.

        Args:
            combatants: List of combatant configurations
        """
        for combatant in combatants:
            # Determine size category
            size_map = {
                "fine": SizeCategory.FINE,
                "diminutive": SizeCategory.DIMINUTIVE,
                "tiny": SizeCategory.TINY,
                "small": SizeCategory.SMALL,
                "medium": SizeCategory.MEDIUM,
                "large": SizeCategory.LARGE,
                "huge": SizeCategory.HUGE,
                "gargantuan": SizeCategory.GARGANTUAN,
                "colossal": SizeCategory.COLOSSAL,
            }
            size = size_map.get(combatant.size.lower(), SizeCategory.MEDIUM)

            # Place on grid
            if self._grid.in_bounds(combatant.position):
                self._grid.place_entity(combatant.name, combatant.position, size)

            # Index in Lens
            self._lens.register_entity(combatant.name, "creature", turn=0)
            self._lens.set_position(combatant.name, combatant.position, turn=0)
            self._lens.set_fact(combatant.name, "hp", combatant.hp, SourceTier.BOX, turn=0)
            self._lens.set_fact(combatant.name, "ac", combatant.ac, SourceTier.BOX, turn=0)
            self._lens.set_fact(combatant.name, "team", combatant.team, SourceTier.CANONICAL, turn=0)

    def _get_initiative_actors(
        self, combatants: List[CombatantConfig]
    ) -> List[Tuple[str, int]]:
        """Build initiative actor list.

        Args:
            combatants: List of combatant configurations

        Returns:
            List of (actor_id, dex_modifier) tuples
        """
        return [(c.name, c.dex_mod) for c in combatants]

    def _execute_round(
        self, round_num: int
    ) -> Tuple[CombatRoundResult, List[float]]:
        """Execute a single combat round.

        Args:
            round_num: Round number (1-indexed)

        Returns:
            Tuple of (CombatRoundResult, action_times_ms)
        """
        action_times = []

        # Get initiative order
        if self._world_state.active_combat is None:
            # No active combat, return empty result
            return CombatRoundResult(
                round_index=round_num,
                world_state=self._world_state,
                events=[],
                turn_results=[],
            ), []

        initiative_order = self._world_state.active_combat.get("initiative_order", [])
        all_events = []
        turn_results = []
        next_event_id = len(self._event_log)
        timestamp = float(round_num)

        # Update STP emitter context
        self._stp_emitter.set_context(turn=round_num, initiative=20)

        # Emit round start
        round_start_event = Event(
            event_id=next_event_id,
            event_type="combat_round_started",
            timestamp=timestamp,
            payload={"round_index": round_num}
        )
        all_events.append(round_start_event)
        next_event_id += 1

        for actor_id in initiative_order:
            entity = self._world_state.entities.get(actor_id)
            if entity is None or entity.get(EF.DEFEATED, False):
                continue

            action_start = time.perf_counter()

            # Simple AI: select target and attack
            actor_team = entity.get(EF.TEAM, "unknown")
            target_id = SimpleAIPolicy.select_target(
                actor_id, actor_team, self._world_state
            )

            if target_id:
                # Get weapon from entity
                attacks = entity.get("attacks", [])
                if attacks:
                    attack_config = attacks[0]
                    weapon = Weapon(
                        damage_dice=attack_config.get("damage_dice", "1d6"),
                        damage_bonus=attack_config.get("damage_bonus", 0),
                        damage_type=attack_config.get("damage_type", "slashing"),
                    )
                    attack_bonus = attack_config.get("attack_bonus", 0)
                else:
                    # Default unarmed attack
                    weapon = Weapon(
                        damage_dice="1d3",
                        damage_bonus=entity.get(EF.STR_MOD, 0),
                        damage_type="bludgeoning",
                    )
                    attack_bonus = entity.get(EF.BAB, 0) + entity.get(EF.STR_MOD, 0)

                intent = AttackIntent(
                    attacker_id=actor_id,
                    target_id=target_id,
                    attack_bonus=attack_bonus,
                    weapon=weapon,
                )

                # Create turn context
                turn_ctx = TurnContext(
                    turn_index=len(turn_results),
                    actor_id=actor_id,
                    actor_team=actor_team,
                )

                # Execute turn
                turn_result = execute_turn(
                    world_state=self._world_state,
                    turn_ctx=turn_ctx,
                    combat_intent=intent,
                    rng=self._rng,
                    next_event_id=next_event_id,
                    timestamp=timestamp + 0.1 * len(turn_results),
                )

                all_events.extend(turn_result.events)
                turn_results.append(turn_result)
                next_event_id += len(turn_result.events)

                # Update world state
                self._world_state = turn_result.world_state

                # Emit STP for the attack
                attack_events = [e for e in turn_result.events if e.event_type == "attack_roll"]
                for atk_event in attack_events:
                    self._stp_emitter.emit_attack_roll(
                        actor_id=actor_id,
                        target_id=target_id,
                        base_roll=atk_event.payload.get("d20_result", 0),
                        attack_bonus=atk_event.payload.get("attack_bonus", 0),
                        target_ac=atk_event.payload.get("target_ac", 10),
                        modifiers=[],
                    )

                damage_events = [e for e in turn_result.events if e.event_type == "damage_roll"]
                for dmg_event in damage_events:
                    self._stp_emitter.emit_damage_roll(
                        actor_id=actor_id,
                        target_id=target_id,
                        dice=dmg_event.payload.get("damage_dice", "1d6"),
                        rolls=dmg_event.payload.get("damage_rolls", [1]),
                        damage_type=dmg_event.payload.get("damage_type", "slashing"),
                        modifiers=[],
                    )

            action_time = (time.perf_counter() - action_start) * 1000
            action_times.append(action_time)

        # Add events to log
        for event in all_events:
            self._event_log.append(event)

        # Update active_combat round index
        if self._world_state.active_combat:
            active_combat = deepcopy(self._world_state.active_combat)
            active_combat["round_index"] = round_num
            self._world_state = WorldState(
                ruleset_version=self._world_state.ruleset_version,
                entities=deepcopy(self._world_state.entities),
                active_combat=active_combat,
            )

        return CombatRoundResult(
            round_index=round_num,
            world_state=self._world_state,
            events=all_events,
            turn_results=turn_results,
        ), action_times

    def _is_combat_over(self) -> bool:
        """Check if combat has ended (one team eliminated).

        Returns:
            True if combat is over
        """
        if self._world_state is None:
            return True

        party_alive = False
        enemy_alive = False

        for entity_id, entity in self._world_state.entities.items():
            if entity.get(EF.DEFEATED, False):
                continue

            team = entity.get(EF.TEAM, "unknown")
            if team == "party":
                party_alive = True
            elif team == "enemy":
                enemy_alive = True

        return not (party_alive and enemy_alive)

    def _validate_consistency(self) -> List[str]:
        """Validate Lens/Grid consistency.

        Returns:
            List of consistency error messages
        """
        errors = []

        if self._bridge is None:
            return errors

        try:
            round_num = 0
            if self._world_state and self._world_state.active_combat:
                round_num = self._world_state.active_combat.get("round_index", 0)

            self._bridge.sync_all_entities(turn=round_num)
            validation_errors = self._bridge.validate_consistency(turn=round_num)
            errors.extend(validation_errors)
        except Exception as e:
            errors.append(f"Consistency validation error: {str(e)}")

        return errors

    def _compute_event_log_hash(self) -> str:
        """Compute deterministic hash of event log.

        Returns:
            SHA-256 hex digest
        """
        if self._event_log is None:
            return ""

        # Serialize events to JSON
        events_data = [e.to_dict() for e in self._event_log.events]
        serialized = json.dumps(events_data, sort_keys=True, separators=(",", ":"))

        return hashlib.sha256(serialized.encode()).hexdigest()

    def _count_stps_by_type(self) -> Dict[str, int]:
        """Count STPs by type.

        Returns:
            Dict mapping STP type name to count
        """
        counts = {}

        if self._stp_log is None:
            return counts

        for stp in self._stp_log.get_all():
            type_name = stp.packet_type.value
            counts[type_name] = counts.get(type_name, 0) + 1

        return counts
