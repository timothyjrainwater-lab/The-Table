"""STP Emitter: Integration layer that wraps Box resolvers to emit STPs.

This module provides a thin wrapper around Box mechanical resolvers that
automatically generates Structured Truth Packets for each resolution.
The STPEmitter does NOT replace resolvers — it calls them and wraps their
outputs in STPs for audit/narration.

WO-013: Vertical Slice Gate (Tavern Combat Demo)
Reference: WO-010 (Structured Truth Packets)
"""

from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json

from aidm.schemas.position import Position
from aidm.core.geometry_engine import BattleGrid
from aidm.core.truth_packets import (
    STPLog, STPBuilder, STPType, StructuredTruthPacket
)


class STPEmitter:
    """Wraps Box resolvers to emit STPs for each resolution.

    The STPEmitter maintains an STP log and provides methods that:
    1. Call Box resolvers to get mechanical results
    2. Wrap those results in appropriate STPs
    3. Log the STPs for audit/narration

    This enables the trust/transparency pipeline without modifying
    existing resolver code.
    """

    def __init__(self, stp_log: STPLog, turn: int = 1, initiative: int = 0):
        """Initialize STPEmitter.

        Args:
            stp_log: STPLog to record packets to
            turn: Current combat turn number
            initiative: Current initiative count
        """
        self._stp_log = stp_log
        self._turn = turn
        self._initiative = initiative
        self._builder = STPBuilder(turn, initiative)

    def set_context(self, turn: int, initiative: int) -> None:
        """Update combat context for STP generation.

        Args:
            turn: Current combat turn
            initiative: Current initiative count
        """
        self._turn = turn
        self._initiative = initiative
        self._builder = STPBuilder(turn, initiative)

    @property
    def stp_log(self) -> STPLog:
        """Access the STP log."""
        return self._stp_log

    # ==========================================================================
    # ATTACK RESOLUTION WITH STP
    # ==========================================================================

    def emit_attack_roll(
        self,
        actor_id: str,
        target_id: str,
        base_roll: int,
        attack_bonus: int,
        target_ac: int,
        modifiers: List[Tuple[str, int]],
        critical_threat: bool = False,
        critical_confirmed: bool = False,
    ) -> StructuredTruthPacket:
        """Emit an ATTACK_ROLL STP.

        Args:
            actor_id: Attacker entity ID
            target_id: Target entity ID
            base_roll: The d20 result (1-20)
            attack_bonus: Total attack bonus
            target_ac: Target's AC
            modifiers: List of (name, value) modifier tuples
            critical_threat: Whether roll threatens critical
            critical_confirmed: Whether critical was confirmed

        Returns:
            The generated STP
        """
        stp = self._builder.attack_roll(
            actor_id=actor_id,
            target_id=target_id,
            base_roll=base_roll,
            attack_bonus=attack_bonus,
            target_ac=target_ac,
            modifiers=modifiers,
            citations=["PHB p.134 (Attack Roll)"],
            critical_threat=critical_threat,
            critical_confirmed=critical_confirmed,
        )
        self._stp_log.append(stp)
        return stp

    def emit_damage_roll(
        self,
        actor_id: str,
        target_id: str,
        dice: str,
        rolls: List[int],
        damage_type: str,
        modifiers: List[Tuple[str, int]],
        dr: int = 0,
    ) -> StructuredTruthPacket:
        """Emit a DAMAGE_ROLL STP.

        Args:
            actor_id: Attacker entity ID
            target_id: Target entity ID
            dice: Dice expression (e.g., "1d8+3")
            rolls: Individual die results
            damage_type: Type of damage
            modifiers: List of (name, value) modifier tuples
            dr: Damage reduction to apply

        Returns:
            The generated STP
        """
        stp = self._builder.damage_roll(
            actor_id=actor_id,
            target_id=target_id,
            dice=dice,
            rolls=rolls,
            damage_type=damage_type,
            modifiers=modifiers,
            dr=dr,
            citations=["PHB p.134 (Damage Roll)"],
        )
        self._stp_log.append(stp)
        return stp

    # ==========================================================================
    # COVER CALCULATION WITH STP
    # ==========================================================================

    def emit_cover_calculation(
        self,
        attacker_id: str,
        defender_id: str,
        attacker_pos: Position,
        defender_pos: Position,
        cover_degree: str,
        ac_bonus: int,
        reflex_bonus: int,
        lines_traced: int = 4,
        lines_blocked: int = 0,
    ) -> StructuredTruthPacket:
        """Emit a COVER_CALCULATION STP.

        Args:
            attacker_id: Attacker entity ID
            defender_id: Defender entity ID
            attacker_pos: Attacker's position
            defender_pos: Defender's position
            cover_degree: Cover type ("none", "partial", "improved", "total")
            ac_bonus: AC bonus from cover
            reflex_bonus: Reflex save bonus from cover
            lines_traced: Number of corner-to-corner lines traced
            lines_blocked: Number of lines blocked

        Returns:
            The generated STP
        """
        cover_result = {
            "attacker_pos": attacker_pos.to_dict(),
            "defender_pos": defender_pos.to_dict(),
            "lines_traced": lines_traced,
            "lines_blocked": lines_blocked,
            "cover_degree": cover_degree,
            "ac_bonus": ac_bonus,
            "reflex_bonus": reflex_bonus,
        }

        stp = self._builder.cover_calculation(
            attacker_id=attacker_id,
            defender_id=defender_id,
            cover_result=cover_result,
            citations=["PHB p.150-152 (Cover)"],
        )
        self._stp_log.append(stp)
        return stp

    # ==========================================================================
    # MOVEMENT WITH STP
    # ==========================================================================

    def emit_movement(
        self,
        actor_id: str,
        start_pos: Position,
        end_pos: Position,
        path: List[Position],
        movement_type: str = "walk",
        difficult_terrain_squares: int = 0,
        provoked_aoo_from: Optional[List[str]] = None,
    ) -> StructuredTruthPacket:
        """Emit a MOVEMENT STP.

        Args:
            actor_id: Moving entity ID
            start_pos: Starting position
            end_pos: Ending position
            path: List of positions in the path
            movement_type: Type of movement ("walk", "run", "charge", "5-foot step")
            difficult_terrain_squares: Count of difficult terrain squares
            provoked_aoo_from: List of entities that get AoO

        Returns:
            The generated STP
        """
        # Calculate distance
        distance_ft = start_pos.distance_to(end_pos)

        stp = self._builder.movement(
            actor_id=actor_id,
            start_pos=start_pos.to_dict(),
            end_pos=end_pos.to_dict(),
            path=[p.to_dict() for p in path],
            distance_ft=distance_ft,
            movement_type=movement_type,
            difficult_terrain_squares=difficult_terrain_squares,
            provoked_aoo_from=provoked_aoo_from or [],
            citations=["PHB p.147 (Movement)"],
        )
        self._stp_log.append(stp)
        return stp

    # ==========================================================================
    # SAVING THROW WITH STP
    # ==========================================================================

    def emit_saving_throw(
        self,
        actor_id: str,
        save_type: str,
        base_roll: int,
        save_bonus: int,
        dc: int,
        modifiers: List[Tuple[str, int]],
    ) -> StructuredTruthPacket:
        """Emit a SAVING_THROW STP.

        Args:
            actor_id: Entity making the save
            save_type: "fort", "ref", or "will"
            base_roll: The d20 result (1-20)
            save_bonus: Base save bonus
            dc: Difficulty class
            modifiers: List of (name, value) modifier tuples

        Returns:
            The generated STP
        """
        stp = self._builder.saving_throw(
            actor_id=actor_id,
            save_type=save_type,
            base_roll=base_roll,
            save_bonus=save_bonus,
            dc=dc,
            modifiers=modifiers,
            citations=["PHB p.136 (Saving Throws)"],
        )
        self._stp_log.append(stp)
        return stp

    # ==========================================================================
    # LOS/LOE CHECKS WITH STP
    # ==========================================================================

    def emit_los_check(
        self,
        actor_id: str,
        target_id: str,
        source_pos: Position,
        target_pos: Position,
        has_los: bool,
        blocking_cells: Optional[List[Position]] = None,
    ) -> StructuredTruthPacket:
        """Emit a LOS_CHECK STP.

        Args:
            actor_id: Observer entity ID
            target_id: Target entity ID
            source_pos: Source position
            target_pos: Target position
            has_los: Whether LOS exists
            blocking_cells: Cells blocking LOS

        Returns:
            The generated STP
        """
        stp = self._builder.los_check(
            actor_id=actor_id,
            target_id=target_id,
            source_pos=source_pos.to_dict(),
            target_pos=target_pos.to_dict(),
            has_los=has_los,
            blocking_cells=[p.to_dict() for p in (blocking_cells or [])],
            citations=["PHB p.150 (Line of Sight)"],
        )
        self._stp_log.append(stp)
        return stp

    # ==========================================================================
    # STATE HASH FOR DETERMINISTIC REPLAY
    # ==========================================================================

    @staticmethod
    def compute_state_hash(
        grid: BattleGrid,
        entity_hp: Dict[str, int],
        turn: int,
    ) -> str:
        """Compute a deterministic hash of game state.

        Used for replay verification — same inputs should produce
        same hash after replay.

        Args:
            grid: BattleGrid state
            entity_hp: Dict of entity_id → current HP
            turn: Current turn number

        Returns:
            Hex string hash of state
        """
        # Build deterministic state representation
        state_data = {
            "turn": turn,
            "grid_dimensions": (grid.width, grid.height),
            "entities": {},
            "hp": entity_hp,
        }

        # Add entity positions (sorted for determinism)
        for entity_id in sorted(grid._entities.keys()):
            pos, size = grid._entities[entity_id]
            state_data["entities"][entity_id] = {
                "x": pos.x,
                "y": pos.y,
                "size": size.value,
            }

        # Serialize deterministically
        state_json = json.dumps(state_data, sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()[:16]
