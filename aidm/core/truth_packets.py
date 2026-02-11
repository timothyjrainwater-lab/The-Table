"""Structured Truth Packets (STPs) for trust/transparency system.

STPs are machine-readable explanations of Box mechanical resolutions
that can be audited and narrated. They capture the "why" of every
mechanical resolution:
- What roll was made
- What modifiers applied
- What the outcome was
- What rules were invoked

This enables:
1. Audit trails for player trust
2. Narration generation from structured data
3. Replay verification

WO-010: Structured Truth Packets
Reference: RQ-TRUST-001 (Trust & Transparency Research)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import time
import uuid


# ==============================================================================
# STP TYPE — Enumeration of packet types
# ==============================================================================

class STPType(Enum):
    """Types of structured truth packets.

    Each type corresponds to a specific mechanical resolution
    that needs to be captured for audit/narration.
    """
    ATTACK_ROLL = "attack_roll"
    DAMAGE_ROLL = "damage_roll"
    SAVING_THROW = "saving_throw"
    SKILL_CHECK = "skill_check"
    COVER_CALCULATION = "cover_calculation"
    LOS_CHECK = "los_check"
    LOE_CHECK = "loe_check"
    AOE_RESOLUTION = "aoe_resolution"
    MOVEMENT = "movement"
    CONDITION_APPLIED = "condition_applied"
    CONDITION_REMOVED = "condition_removed"


# ==============================================================================
# SPECIALIZED PAYLOADS — Frozen dataclasses for specific STP types
# ==============================================================================

@dataclass(frozen=True)
class AttackRollPayload:
    """Payload for ATTACK_ROLL STP type.

    Captures all details of an attack roll including modifiers,
    critical threat/confirmation, and final outcome.
    """
    base_roll: int  # 1-20
    attack_bonus: int
    total_roll: int
    target_ac: int
    hit: bool
    critical_threat: bool
    critical_confirmed: bool
    modifiers: Tuple[Tuple[str, int], ...]  # e.g., (("flanking", 2), ("cover", -2))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "base_roll": self.base_roll,
            "attack_bonus": self.attack_bonus,
            "total_roll": self.total_roll,
            "target_ac": self.target_ac,
            "hit": self.hit,
            "critical_threat": self.critical_threat,
            "critical_confirmed": self.critical_confirmed,
            "modifiers": list(self.modifiers),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttackRollPayload':
        """Deserialize from dictionary."""
        return cls(
            base_roll=data["base_roll"],
            attack_bonus=data["attack_bonus"],
            total_roll=data["total_roll"],
            target_ac=data["target_ac"],
            hit=data["hit"],
            critical_threat=data["critical_threat"],
            critical_confirmed=data["critical_confirmed"],
            modifiers=tuple(tuple(m) for m in data["modifiers"]),
        )


@dataclass(frozen=True)
class DamageRollPayload:
    """Payload for DAMAGE_ROLL STP type.

    Captures dice expression, individual rolls, modifiers,
    damage reduction, and final damage dealt.
    """
    dice: str  # e.g., "2d6+4"
    rolls: Tuple[int, ...]  # Individual die results
    base_damage: int  # Sum of dice
    damage_type: str  # e.g., "slashing", "fire"
    modifiers: Tuple[Tuple[str, int], ...]
    total_damage: int  # Before DR
    damage_reduced: int  # From DR
    final_damage: int  # After DR

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "dice": self.dice,
            "rolls": list(self.rolls),
            "base_damage": self.base_damage,
            "damage_type": self.damage_type,
            "modifiers": list(self.modifiers),
            "total_damage": self.total_damage,
            "damage_reduced": self.damage_reduced,
            "final_damage": self.final_damage,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DamageRollPayload':
        """Deserialize from dictionary."""
        return cls(
            dice=data["dice"],
            rolls=tuple(data["rolls"]),
            base_damage=data["base_damage"],
            damage_type=data["damage_type"],
            modifiers=tuple(tuple(m) for m in data["modifiers"]),
            total_damage=data["total_damage"],
            damage_reduced=data["damage_reduced"],
            final_damage=data["final_damage"],
        )


@dataclass(frozen=True)
class SavingThrowPayload:
    """Payload for SAVING_THROW STP type.

    Captures save type, roll, DC, modifiers, and success/failure.
    """
    save_type: str  # "fort", "ref", "will"
    base_roll: int
    save_bonus: int
    dc: int
    total_roll: int
    success: bool
    modifiers: Tuple[Tuple[str, int], ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "save_type": self.save_type,
            "base_roll": self.base_roll,
            "save_bonus": self.save_bonus,
            "dc": self.dc,
            "total_roll": self.total_roll,
            "success": self.success,
            "modifiers": list(self.modifiers),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SavingThrowPayload':
        """Deserialize from dictionary."""
        return cls(
            save_type=data["save_type"],
            base_roll=data["base_roll"],
            save_bonus=data["save_bonus"],
            dc=data["dc"],
            total_roll=data["total_roll"],
            success=data["success"],
            modifiers=tuple(tuple(m) for m in data["modifiers"]),
        )


@dataclass(frozen=True)
class CoverPayload:
    """Payload for COVER_CALCULATION STP type.

    Captures the geometric cover determination between two positions.
    """
    attacker_pos: Dict[str, int]
    defender_pos: Dict[str, int]
    lines_traced: int
    lines_blocked: int
    cover_degree: str  # "none", "partial", "improved", "total"
    ac_bonus: int
    reflex_bonus: int

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "attacker_pos": dict(self.attacker_pos),
            "defender_pos": dict(self.defender_pos),
            "lines_traced": self.lines_traced,
            "lines_blocked": self.lines_blocked,
            "cover_degree": self.cover_degree,
            "ac_bonus": self.ac_bonus,
            "reflex_bonus": self.reflex_bonus,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoverPayload':
        """Deserialize from dictionary."""
        return cls(
            attacker_pos=data["attacker_pos"],
            defender_pos=data["defender_pos"],
            lines_traced=data["lines_traced"],
            lines_blocked=data["lines_blocked"],
            cover_degree=data["cover_degree"],
            ac_bonus=data["ac_bonus"],
            reflex_bonus=data["reflex_bonus"],
        )


@dataclass(frozen=True)
class AoEPayload:
    """Payload for AOE_RESOLUTION STP type.

    Captures AoE origin, shape, affected squares and entities.
    """
    origin: Dict[str, int]
    shape: str  # "burst", "cone", "line", etc.
    radius_ft: int
    affected_squares: Tuple[Dict[str, int], ...]
    affected_entities: Tuple[str, ...]
    save_dc: int
    damage_dice: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "origin": dict(self.origin),
            "shape": self.shape,
            "radius_ft": self.radius_ft,
            "affected_squares": list(self.affected_squares),
            "affected_entities": list(self.affected_entities),
            "save_dc": self.save_dc,
            "damage_dice": self.damage_dice,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AoEPayload':
        """Deserialize from dictionary."""
        return cls(
            origin=data["origin"],
            shape=data["shape"],
            radius_ft=data["radius_ft"],
            affected_squares=tuple(data["affected_squares"]),
            affected_entities=tuple(data["affected_entities"]),
            save_dc=data["save_dc"],
            damage_dice=data["damage_dice"],
        )


@dataclass(frozen=True)
class SkillCheckPayload:
    """Payload for SKILL_CHECK STP type."""
    skill_name: str
    base_roll: int
    skill_bonus: int
    dc: int
    total_roll: int
    success: bool
    modifiers: Tuple[Tuple[str, int], ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "skill_name": self.skill_name,
            "base_roll": self.base_roll,
            "skill_bonus": self.skill_bonus,
            "dc": self.dc,
            "total_roll": self.total_roll,
            "success": self.success,
            "modifiers": list(self.modifiers),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillCheckPayload':
        """Deserialize from dictionary."""
        return cls(
            skill_name=data["skill_name"],
            base_roll=data["base_roll"],
            skill_bonus=data["skill_bonus"],
            dc=data["dc"],
            total_roll=data["total_roll"],
            success=data["success"],
            modifiers=tuple(tuple(m) for m in data["modifiers"]),
        )


@dataclass(frozen=True)
class LOSPayload:
    """Payload for LOS_CHECK STP type."""
    source_pos: Dict[str, int]
    target_pos: Dict[str, int]
    has_los: bool
    blocking_cells: Tuple[Dict[str, int], ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_pos": dict(self.source_pos),
            "target_pos": dict(self.target_pos),
            "has_los": self.has_los,
            "blocking_cells": list(self.blocking_cells),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LOSPayload':
        """Deserialize from dictionary."""
        return cls(
            source_pos=data["source_pos"],
            target_pos=data["target_pos"],
            has_los=data["has_los"],
            blocking_cells=tuple(data["blocking_cells"]),
        )


@dataclass(frozen=True)
class LOEPayload:
    """Payload for LOE_CHECK STP type."""
    source_pos: Dict[str, int]
    target_pos: Dict[str, int]
    has_loe: bool
    blocking_cells: Tuple[Dict[str, int], ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_pos": dict(self.source_pos),
            "target_pos": dict(self.target_pos),
            "has_loe": self.has_loe,
            "blocking_cells": list(self.blocking_cells),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LOEPayload':
        """Deserialize from dictionary."""
        return cls(
            source_pos=data["source_pos"],
            target_pos=data["target_pos"],
            has_loe=data["has_loe"],
            blocking_cells=tuple(data["blocking_cells"]),
        )


@dataclass(frozen=True)
class MovementPayload:
    """Payload for MOVEMENT STP type."""
    start_pos: Dict[str, int]
    end_pos: Dict[str, int]
    path: Tuple[Dict[str, int], ...]
    distance_ft: int
    movement_type: str  # "walk", "run", "charge", "5-foot step"
    difficult_terrain_squares: int
    provoked_aoo_from: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "start_pos": dict(self.start_pos),
            "end_pos": dict(self.end_pos),
            "path": list(self.path),
            "distance_ft": self.distance_ft,
            "movement_type": self.movement_type,
            "difficult_terrain_squares": self.difficult_terrain_squares,
            "provoked_aoo_from": list(self.provoked_aoo_from),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MovementPayload':
        """Deserialize from dictionary."""
        return cls(
            start_pos=data["start_pos"],
            end_pos=data["end_pos"],
            path=tuple(data["path"]),
            distance_ft=data["distance_ft"],
            movement_type=data["movement_type"],
            difficult_terrain_squares=data["difficult_terrain_squares"],
            provoked_aoo_from=tuple(data["provoked_aoo_from"]),
        )


@dataclass(frozen=True)
class ConditionPayload:
    """Payload for CONDITION_APPLIED and CONDITION_REMOVED STP types."""
    condition_name: str
    source: str  # What caused the condition
    duration_rounds: Optional[int]  # None = indefinite
    save_dc: Optional[int]
    save_type: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "condition_name": self.condition_name,
            "source": self.source,
            "duration_rounds": self.duration_rounds,
            "save_dc": self.save_dc,
            "save_type": self.save_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConditionPayload':
        """Deserialize from dictionary."""
        return cls(
            condition_name=data["condition_name"],
            source=data["source"],
            duration_rounds=data.get("duration_rounds"),
            save_dc=data.get("save_dc"),
            save_type=data.get("save_type"),
        )


# ==============================================================================
# PAYLOAD REGISTRY — Maps STP types to their payload classes
# ==============================================================================

PAYLOAD_REGISTRY: Dict[STPType, type] = {
    STPType.ATTACK_ROLL: AttackRollPayload,
    STPType.DAMAGE_ROLL: DamageRollPayload,
    STPType.SAVING_THROW: SavingThrowPayload,
    STPType.SKILL_CHECK: SkillCheckPayload,
    STPType.COVER_CALCULATION: CoverPayload,
    STPType.LOS_CHECK: LOSPayload,
    STPType.LOE_CHECK: LOEPayload,
    STPType.AOE_RESOLUTION: AoEPayload,
    STPType.MOVEMENT: MovementPayload,
    STPType.CONDITION_APPLIED: ConditionPayload,
    STPType.CONDITION_REMOVED: ConditionPayload,
}


# ==============================================================================
# STRUCTURED TRUTH PACKET — Main STP dataclass
# ==============================================================================

@dataclass(frozen=True)
class StructuredTruthPacket:
    """Structured Truth Packet for mechanical resolution audit.

    Captures the complete context of a mechanical resolution including
    the actor, target, payload details, and rule citations.
    """
    packet_id: str
    packet_type: STPType
    turn: int
    initiative_count: int
    actor_id: str
    target_id: Optional[str]
    timestamp: int  # epoch ms
    payload: Dict[str, Any]
    rule_citations: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "packet_id": self.packet_id,
            "packet_type": self.packet_type.value,
            "turn": self.turn,
            "initiative_count": self.initiative_count,
            "actor_id": self.actor_id,
            "target_id": self.target_id,
            "timestamp": self.timestamp,
            "payload": dict(self.payload),
            "rule_citations": list(self.rule_citations),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StructuredTruthPacket':
        """Deserialize from dictionary."""
        return cls(
            packet_id=data["packet_id"],
            packet_type=STPType(data["packet_type"]),
            turn=data["turn"],
            initiative_count=data["initiative_count"],
            actor_id=data["actor_id"],
            target_id=data.get("target_id"),
            timestamp=data["timestamp"],
            payload=data["payload"],
            rule_citations=tuple(data["rule_citations"]),
        )


# ==============================================================================
# STP BUILDER — Factory for creating STPs
# ==============================================================================

class STPBuilder:
    """Builder for creating Structured Truth Packets.

    Maintains turn/initiative context and provides convenience methods
    for creating specific STP types with proper payloads.
    """

    def __init__(self, turn: int, initiative: int):
        """Initialize builder with combat context.

        Args:
            turn: Current combat turn number
            initiative: Current initiative count
        """
        self._turn = turn
        self._initiative = initiative

    def _generate_id(self) -> str:
        """Generate a unique packet ID."""
        return str(uuid.uuid4())

    def _timestamp(self) -> int:
        """Get current timestamp in epoch milliseconds."""
        return int(time.time() * 1000)

    def attack_roll(
        self,
        actor_id: str,
        target_id: str,
        base_roll: int,
        attack_bonus: int,
        target_ac: int,
        modifiers: List[Tuple[str, int]],
        citations: List[str],
        critical_threat: bool = False,
        critical_confirmed: bool = False,
    ) -> StructuredTruthPacket:
        """Create an ATTACK_ROLL STP.

        Args:
            actor_id: Attacker entity ID
            target_id: Target entity ID
            base_roll: The d20 result (1-20)
            attack_bonus: Total attack bonus
            target_ac: Target's AC
            modifiers: List of (name, value) modifier tuples
            citations: List of rule citations
            critical_threat: Whether the roll was a natural 20 or in threat range
            critical_confirmed: Whether critical was confirmed

        Returns:
            StructuredTruthPacket for the attack roll
        """
        # Calculate total roll
        modifier_total = sum(m[1] for m in modifiers)
        total_roll = base_roll + attack_bonus + modifier_total

        # Determine hit
        hit = total_roll >= target_ac or base_roll == 20  # Natural 20 always hits

        payload = AttackRollPayload(
            base_roll=base_roll,
            attack_bonus=attack_bonus,
            total_roll=total_roll,
            target_ac=target_ac,
            hit=hit,
            critical_threat=critical_threat,
            critical_confirmed=critical_confirmed,
            modifiers=tuple(tuple(m) for m in modifiers),
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.ATTACK_ROLL,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=actor_id,
            target_id=target_id,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )

    def damage_roll(
        self,
        actor_id: str,
        target_id: str,
        dice: str,
        rolls: List[int],
        damage_type: str,
        modifiers: List[Tuple[str, int]],
        dr: int,
        citations: List[str],
    ) -> StructuredTruthPacket:
        """Create a DAMAGE_ROLL STP.

        Args:
            actor_id: Attacker entity ID
            target_id: Target entity ID
            dice: Dice expression (e.g., "2d6+4")
            rolls: Individual die results
            damage_type: Type of damage (e.g., "slashing", "fire")
            modifiers: List of (name, value) modifier tuples
            dr: Damage reduction to apply
            citations: List of rule citations

        Returns:
            StructuredTruthPacket for the damage roll
        """
        # Calculate damage
        base_damage = sum(rolls)
        modifier_total = sum(m[1] for m in modifiers)
        total_damage = base_damage + modifier_total
        damage_reduced = min(dr, total_damage)  # Can't reduce below 0
        final_damage = max(0, total_damage - dr)

        payload = DamageRollPayload(
            dice=dice,
            rolls=tuple(rolls),
            base_damage=base_damage,
            damage_type=damage_type,
            modifiers=tuple(tuple(m) for m in modifiers),
            total_damage=total_damage,
            damage_reduced=damage_reduced,
            final_damage=final_damage,
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.DAMAGE_ROLL,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=actor_id,
            target_id=target_id,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )

    def saving_throw(
        self,
        actor_id: str,
        save_type: str,
        base_roll: int,
        save_bonus: int,
        dc: int,
        modifiers: List[Tuple[str, int]],
        citations: List[str],
    ) -> StructuredTruthPacket:
        """Create a SAVING_THROW STP.

        Args:
            actor_id: Entity making the save
            save_type: "fort", "ref", or "will"
            base_roll: The d20 result (1-20)
            save_bonus: Base save bonus
            dc: Difficulty class to meet
            modifiers: List of (name, value) modifier tuples
            citations: List of rule citations

        Returns:
            StructuredTruthPacket for the saving throw
        """
        # Calculate total and success
        modifier_total = sum(m[1] for m in modifiers)
        total_roll = base_roll + save_bonus + modifier_total
        success = total_roll >= dc

        payload = SavingThrowPayload(
            save_type=save_type,
            base_roll=base_roll,
            save_bonus=save_bonus,
            dc=dc,
            total_roll=total_roll,
            success=success,
            modifiers=tuple(tuple(m) for m in modifiers),
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.SAVING_THROW,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=actor_id,
            target_id=None,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )

    def cover_calculation(
        self,
        attacker_id: str,
        defender_id: str,
        cover_result: Dict[str, Any],
        citations: List[str],
    ) -> StructuredTruthPacket:
        """Create a COVER_CALCULATION STP.

        Args:
            attacker_id: Attacker entity ID
            defender_id: Defender entity ID
            cover_result: Dictionary with cover calculation results
            citations: List of rule citations

        Returns:
            StructuredTruthPacket for the cover calculation
        """
        payload = CoverPayload(
            attacker_pos=cover_result.get("attacker_pos", {}),
            defender_pos=cover_result.get("defender_pos", {}),
            lines_traced=cover_result.get("lines_traced", 0),
            lines_blocked=cover_result.get("lines_blocked", 0),
            cover_degree=cover_result.get("cover_degree", "none"),
            ac_bonus=cover_result.get("ac_bonus", 0),
            reflex_bonus=cover_result.get("reflex_bonus", 0),
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.COVER_CALCULATION,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=attacker_id,
            target_id=defender_id,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )

    def aoe_resolution(
        self,
        actor_id: str,
        origin: Dict[str, int],
        shape: str,
        radius_ft: int,
        affected_squares: List[Dict[str, int]],
        affected_entities: List[str],
        save_dc: int,
        damage_dice: str,
        citations: List[str],
    ) -> StructuredTruthPacket:
        """Create an AOE_RESOLUTION STP.

        Args:
            actor_id: Caster entity ID
            origin: Origin position as dict
            shape: Shape type (e.g., "burst", "cone")
            radius_ft: Radius in feet
            affected_squares: List of affected square positions
            affected_entities: List of affected entity IDs
            save_dc: Save DC for the effect
            damage_dice: Damage dice expression
            citations: List of rule citations

        Returns:
            StructuredTruthPacket for the AoE resolution
        """
        payload = AoEPayload(
            origin=origin,
            shape=shape,
            radius_ft=radius_ft,
            affected_squares=tuple(affected_squares),
            affected_entities=tuple(affected_entities),
            save_dc=save_dc,
            damage_dice=damage_dice,
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.AOE_RESOLUTION,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=actor_id,
            target_id=None,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )

    def skill_check(
        self,
        actor_id: str,
        skill_name: str,
        base_roll: int,
        skill_bonus: int,
        dc: int,
        modifiers: List[Tuple[str, int]],
        citations: List[str],
    ) -> StructuredTruthPacket:
        """Create a SKILL_CHECK STP.

        Args:
            actor_id: Entity making the check
            skill_name: Name of the skill
            base_roll: The d20 result (1-20)
            skill_bonus: Base skill bonus
            dc: Difficulty class to meet
            modifiers: List of (name, value) modifier tuples
            citations: List of rule citations

        Returns:
            StructuredTruthPacket for the skill check
        """
        modifier_total = sum(m[1] for m in modifiers)
        total_roll = base_roll + skill_bonus + modifier_total
        success = total_roll >= dc

        payload = SkillCheckPayload(
            skill_name=skill_name,
            base_roll=base_roll,
            skill_bonus=skill_bonus,
            dc=dc,
            total_roll=total_roll,
            success=success,
            modifiers=tuple(tuple(m) for m in modifiers),
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.SKILL_CHECK,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=actor_id,
            target_id=None,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )

    def los_check(
        self,
        actor_id: str,
        target_id: str,
        source_pos: Dict[str, int],
        target_pos: Dict[str, int],
        has_los: bool,
        blocking_cells: List[Dict[str, int]],
        citations: List[str],
    ) -> StructuredTruthPacket:
        """Create a LOS_CHECK STP.

        Args:
            actor_id: Observer entity ID
            target_id: Target entity ID
            source_pos: Source position
            target_pos: Target position
            has_los: Whether LOS exists
            blocking_cells: Cells blocking LOS
            citations: List of rule citations

        Returns:
            StructuredTruthPacket for the LOS check
        """
        payload = LOSPayload(
            source_pos=source_pos,
            target_pos=target_pos,
            has_los=has_los,
            blocking_cells=tuple(blocking_cells),
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.LOS_CHECK,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=actor_id,
            target_id=target_id,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )

    def loe_check(
        self,
        actor_id: str,
        target_id: str,
        source_pos: Dict[str, int],
        target_pos: Dict[str, int],
        has_loe: bool,
        blocking_cells: List[Dict[str, int]],
        citations: List[str],
    ) -> StructuredTruthPacket:
        """Create a LOE_CHECK STP.

        Args:
            actor_id: Caster entity ID
            target_id: Target entity ID
            source_pos: Source position
            target_pos: Target position
            has_loe: Whether LOE exists
            blocking_cells: Cells blocking LOE
            citations: List of rule citations

        Returns:
            StructuredTruthPacket for the LOE check
        """
        payload = LOEPayload(
            source_pos=source_pos,
            target_pos=target_pos,
            has_loe=has_loe,
            blocking_cells=tuple(blocking_cells),
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.LOE_CHECK,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=actor_id,
            target_id=target_id,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )

    def movement(
        self,
        actor_id: str,
        start_pos: Dict[str, int],
        end_pos: Dict[str, int],
        path: List[Dict[str, int]],
        distance_ft: int,
        movement_type: str,
        difficult_terrain_squares: int,
        provoked_aoo_from: List[str],
        citations: List[str],
    ) -> StructuredTruthPacket:
        """Create a MOVEMENT STP.

        Args:
            actor_id: Moving entity ID
            start_pos: Starting position
            end_pos: Ending position
            path: List of positions in the path
            distance_ft: Total distance in feet
            movement_type: Type of movement
            difficult_terrain_squares: Count of difficult terrain squares
            provoked_aoo_from: List of entities that get AoO
            citations: List of rule citations

        Returns:
            StructuredTruthPacket for the movement
        """
        payload = MovementPayload(
            start_pos=start_pos,
            end_pos=end_pos,
            path=tuple(path),
            distance_ft=distance_ft,
            movement_type=movement_type,
            difficult_terrain_squares=difficult_terrain_squares,
            provoked_aoo_from=tuple(provoked_aoo_from),
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.MOVEMENT,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=actor_id,
            target_id=None,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )

    def condition_applied(
        self,
        actor_id: str,
        target_id: str,
        condition_name: str,
        source: str,
        duration_rounds: Optional[int],
        save_dc: Optional[int],
        save_type: Optional[str],
        citations: List[str],
    ) -> StructuredTruthPacket:
        """Create a CONDITION_APPLIED STP.

        Args:
            actor_id: Entity applying the condition
            target_id: Entity receiving the condition
            condition_name: Name of the condition
            source: What caused the condition
            duration_rounds: Duration in rounds (None = indefinite)
            save_dc: Save DC if applicable
            save_type: Save type if applicable
            citations: List of rule citations

        Returns:
            StructuredTruthPacket for the condition application
        """
        payload = ConditionPayload(
            condition_name=condition_name,
            source=source,
            duration_rounds=duration_rounds,
            save_dc=save_dc,
            save_type=save_type,
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.CONDITION_APPLIED,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=actor_id,
            target_id=target_id,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )

    def condition_removed(
        self,
        actor_id: str,
        target_id: str,
        condition_name: str,
        source: str,
        citations: List[str],
    ) -> StructuredTruthPacket:
        """Create a CONDITION_REMOVED STP.

        Args:
            actor_id: Entity removing the condition
            target_id: Entity losing the condition
            condition_name: Name of the condition
            source: Why the condition was removed
            citations: List of rule citations

        Returns:
            StructuredTruthPacket for the condition removal
        """
        payload = ConditionPayload(
            condition_name=condition_name,
            source=source,
            duration_rounds=None,
            save_dc=None,
            save_type=None,
        )

        return StructuredTruthPacket(
            packet_id=self._generate_id(),
            packet_type=STPType.CONDITION_REMOVED,
            turn=self._turn,
            initiative_count=self._initiative,
            actor_id=actor_id,
            target_id=target_id,
            timestamp=self._timestamp(),
            payload=payload.to_dict(),
            rule_citations=tuple(citations),
        )


# ==============================================================================
# STP LOG — Collection of STPs with query methods
# ==============================================================================

class STPLog:
    """Collection of Structured Truth Packets with query methods.

    Provides filtering by turn, actor, and type for audit and replay.
    """

    def __init__(self):
        """Initialize an empty STP log."""
        self._packets: List[StructuredTruthPacket] = []

    def append(self, stp: StructuredTruthPacket) -> None:
        """Add an STP to the log.

        Args:
            stp: StructuredTruthPacket to add
        """
        self._packets.append(stp)

    def get_by_turn(self, turn: int) -> List[StructuredTruthPacket]:
        """Get all STPs from a specific turn.

        Args:
            turn: Turn number to filter by

        Returns:
            List of STPs from that turn
        """
        return [p for p in self._packets if p.turn == turn]

    def get_by_actor(self, actor_id: str) -> List[StructuredTruthPacket]:
        """Get all STPs involving a specific actor.

        Args:
            actor_id: Actor entity ID to filter by

        Returns:
            List of STPs with that actor
        """
        return [p for p in self._packets if p.actor_id == actor_id]

    def get_by_type(self, stp_type: STPType) -> List[StructuredTruthPacket]:
        """Get all STPs of a specific type.

        Args:
            stp_type: STPType to filter by

        Returns:
            List of STPs of that type
        """
        return [p for p in self._packets if p.packet_type == stp_type]

    def get_all(self) -> List[StructuredTruthPacket]:
        """Get all STPs in the log.

        Returns:
            List of all STPs
        """
        return list(self._packets)

    def __len__(self) -> int:
        """Return number of packets in log."""
        return len(self._packets)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the log to dictionary.

        Returns:
            Dictionary with packets list
        """
        return {
            "packets": [p.to_dict() for p in self._packets],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'STPLog':
        """Deserialize from dictionary.

        Args:
            data: Dictionary with packets list

        Returns:
            STPLog instance
        """
        log = cls()
        for packet_data in data.get("packets", []):
            log.append(StructuredTruthPacket.from_dict(packet_data))
        return log
