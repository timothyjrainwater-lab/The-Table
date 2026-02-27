"""Core spellcasting resolution system for D&D 3.5e.

Implements targeting validation, save resolution, damage application,
and STP generation for all spell resolutions. Integrates with existing
Box layer components (AoE rasterization, LOS/LOE, cover).

WO-014: Spellcasting Resolution Core
Reference: CP-18A (Spellcasting System), PHB Chapter 10
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.schemas.saves import SaveType
from aidm.core.geometry_engine import BattleGrid
from aidm.core.aoe_rasterizer import (
    AoEShape, AoEDirection, rasterize_burst, rasterize_cone, rasterize_line
)
from aidm.core.los_resolver import check_los
from aidm.core.truth_packets import (
    STPType, STPBuilder, StructuredTruthPacket, SavingThrowPayload,
    DamageRollPayload, AoEPayload, ConditionPayload
)
from aidm.core.rng_protocol import RNGProvider
from aidm.core.cover_resolver import calculate_cover, CoverDegree
from aidm.core.conditions import get_condition_modifiers  # CP-18: condition save modifiers


# ==============================================================================
# SPELL TARGET TYPE — How the spell selects targets
# ==============================================================================

class SpellTarget(Enum):
    """Spell targeting types per PHB Chapter 10."""
    SINGLE = "single"       # One creature/object
    AREA = "area"           # AoE (burst, cone, line, etc.)
    SELF = "self"           # Caster only
    TOUCH = "touch"         # Touch attack required
    RAY = "ray"             # Ranged touch attack


# ==============================================================================
# SPELL EFFECT TYPE — What the spell does
# ==============================================================================

class SpellEffect(Enum):
    """Primary spell effect types."""
    DAMAGE = "damage"       # Deal damage (save for half typical)
    HEALING = "healing"     # Restore HP
    BUFF = "buff"           # Apply beneficial condition
    DEBUFF = "debuff"       # Apply harmful condition
    UTILITY = "utility"     # Non-combat effect


# ==============================================================================
# SAVE EFFECT — What happens on save
# ==============================================================================

class SaveEffect(Enum):
    """Effect of a saving throw."""
    NONE = "none"           # No save allowed
    HALF = "half"           # Save for half damage
    NEGATES = "negates"     # Save negates all effects
    PARTIAL = "partial"     # Save reduces but doesn't negate


# ==============================================================================
# DAMAGE TYPE — Types of magical damage
# ==============================================================================

class DamageType(Enum):
    """Damage types for spells per PHB p.309."""
    FIRE = "fire"
    COLD = "cold"
    ACID = "acid"
    ELECTRICITY = "electricity"
    SONIC = "sonic"
    FORCE = "force"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNTYPED = "untyped"


# ==============================================================================
# SPELL DEFINITION — Immutable spell data from rulebook
# ==============================================================================

@dataclass(frozen=True)
class SpellDefinition:
    """Immutable spell definition from rulebook.

    Contains all mechanical data needed to resolve a spell cast.
    Does NOT contain spell slot or preparation info (deferred).
    """

    spell_id: str
    """Unique spell identifier."""

    name: str
    """Display name of the spell."""

    level: int
    """Spell level (0-9)."""

    school: str
    """Spell school (evocation, necromancy, etc.)."""

    target_type: SpellTarget
    """How the spell selects targets."""

    range_ft: int
    """Range in feet (0 = self/touch)."""

    aoe_shape: Optional[AoEShape] = None
    """Shape for area spells (burst, cone, line)."""

    aoe_radius_ft: Optional[int] = None
    """Radius/length for area spells in feet."""

    aoe_direction: Optional[AoEDirection] = None
    """Direction for cones and lines (optional, can be set at cast time)."""

    effect_type: SpellEffect = SpellEffect.DAMAGE
    """Primary effect type."""

    damage_dice: Optional[str] = None
    """Damage dice expression (e.g., '8d6' for fireball)."""

    damage_type: Optional[DamageType] = None
    """Type of damage dealt."""

    healing_dice: Optional[str] = None
    """Healing dice expression (e.g., '1d8' for cure light wounds)."""

    save_type: Optional[SaveType] = None
    """Type of save required (None = no save)."""

    save_effect: SaveEffect = SaveEffect.NONE
    """What happens on successful save."""

    duration_rounds: int = 0
    """Duration in rounds (0 = instantaneous)."""

    concentration: bool = False
    """Whether spell requires concentration."""

    conditions_on_fail: Tuple[str, ...] = field(default_factory=tuple)
    """Conditions applied on failed save."""

    conditions_on_success: Tuple[str, ...] = field(default_factory=tuple)
    """Conditions applied on successful save (buffs)."""

    auto_hit: bool = False
    """Whether spell automatically hits (e.g., magic missile)."""

    requires_attack_roll: bool = False
    """Whether spell requires an attack roll (touch/ray)."""

    rule_citations: Tuple[str, ...] = field(default_factory=tuple)
    """PHB/rulebook page references."""

    content_id: Optional[str] = None
    """Content pack identifier for Layer B presentation lookup (WO-COMPILE-VALIDATE-001).

    When set, resolver events include this in their payload so the Lens can
    look up AbilityPresentationEntry from the PresentationSemanticsRegistry.
    Format: 'spell.{template_id_lower}' (e.g., 'spell.spell_001').
    """

    has_somatic: bool = True
    """WO-ENGINE-ARCANE-SPELL-FAILURE-001: True if spell has a somatic component.
    V-only spells (e.g., Message, Silent Image, Alarm, Tongues) set this to False.
    All other spells default True. PHB p.174."""

    has_verbal: bool = True
    # PHB: True if spell has a verbal component.
    # Future: checked by silence-zone enforcement when that condition layer lands.
    # Silent Spell metamagic suppresses this component (PHB p.98), allowing casting
    # in areas of magical silence or when speech is impossible.

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "spell_id": self.spell_id,
            "name": self.name,
            "level": self.level,
            "school": self.school,
            "target_type": self.target_type.value,
            "range_ft": self.range_ft,
            "aoe_shape": self.aoe_shape.value if self.aoe_shape else None,
            "aoe_radius_ft": self.aoe_radius_ft,
            "aoe_direction": self.aoe_direction.value if self.aoe_direction else None,
            "effect_type": self.effect_type.value,
            "damage_dice": self.damage_dice,
            "damage_type": self.damage_type.value if self.damage_type else None,
            "healing_dice": self.healing_dice,
            "save_type": self.save_type.value if self.save_type else None,
            "save_effect": self.save_effect.value,
            "duration_rounds": self.duration_rounds,
            "concentration": self.concentration,
            "conditions_on_fail": list(self.conditions_on_fail),
            "conditions_on_success": list(self.conditions_on_success),
            "auto_hit": self.auto_hit,
            "requires_attack_roll": self.requires_attack_roll,
            "rule_citations": list(self.rule_citations),
            "content_id": self.content_id,
        }


# ==============================================================================
# SPELL CAST INTENT — Player's intent to cast a spell
# ==============================================================================

@dataclass(frozen=True)
class SpellCastIntent:
    """Player's intent to cast a spell.

    Captures all targeting information needed to resolve the spell.
    """

    caster_id: str
    """Entity casting the spell."""

    spell_id: str
    """ID of spell being cast."""

    target_position: Optional[Position] = None
    """Target position for area/ranged spells."""

    target_entity_id: Optional[str] = None
    """Target entity for single-target spells."""

    aoe_direction: Optional[AoEDirection] = None
    """Direction for cone/line spells (overrides spell default)."""

    quickened: bool = False
    """CP-23: If True, spell is cast as a free action (Quicken Spell feat) — no AoO."""

    metamagic: tuple = ()
    """WO-ENGINE-METAMAGIC-001: Tuple of metamagic keyword strings.
    Valid values: 'empower', 'maximize', 'extend', 'heighten', 'quicken'."""

    heighten_to_level: Optional[int] = None
    """WO-ENGINE-METAMAGIC-001: Required when 'heighten' in metamagic — target slot level."""

    defensive: bool = False
    """WO-ENGINE-DEFENSIVE-CASTING-001: If True, caster declared defensive casting.
    Triggers Concentration check (DC 15 + spell level) to suppress AoO.
    On success: no AoO. On failure: AoO triggers + concentration_failed event.
    On failure by 5+: spell also disrupted (spell_disrupted event, slot consumed). PHB p.140."""

    spontaneous_cure: bool = False
    """WO-ENGINE-CLERIC-SPONTANEOUS-001: Cleric spontaneous cure conversion (PHB p.32).
    When True: the declared spell slot is consumed but a cure spell of equal
    level is cast instead. Only valid for clerics. Resolver handles the redirect
    before verbal/somatic/ASF guard chain.
    FINDING-ENGINE-SPONTANEOUS-ALIGNMENT-001: PHB restricts to good clerics only.
    Alignment check not wired (EF.ALIGNMENT not tracked). Any cleric may use this.
    FINDING-ENGINE-SPONTANEOUS-DOMAIN-001: Domain slots cannot be converted (PHB p.32).
    EF.DOMAIN_SPELLS_PREPARED not tracked. Future WO."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "caster_id": self.caster_id,
            "spell_id": self.spell_id,
            "target_position": self.target_position.to_dict() if self.target_position else None,
            "target_entity_id": self.target_entity_id,
            "aoe_direction": self.aoe_direction.value if self.aoe_direction else None,
            "quickened": self.quickened,
            "metamagic": list(self.metamagic),
            "heighten_to_level": self.heighten_to_level,
            "spontaneous_cure": self.spontaneous_cure,
        }


# ==============================================================================
# SPELL RESOLUTION — Complete resolution of a spell cast
# ==============================================================================

@dataclass(frozen=True)
class SpellResolution:
    """Complete resolution of a spell cast.

    Immutable record of all effects applied by the spell.
    """

    cast_id: str
    """Unique ID for this cast."""

    spell_id: str
    """ID of spell that was cast."""

    caster_id: str
    """Entity that cast the spell."""

    success: bool
    """Whether the spell was successfully cast."""

    affected_entities: Tuple[str, ...] = field(default_factory=tuple)
    """Entities affected by the spell."""

    damage_dealt: Dict[str, int] = field(default_factory=dict)
    """entity_id -> damage dealt."""

    healing_done: Dict[str, int] = field(default_factory=dict)
    """entity_id -> healing done."""

    saves_made: Dict[str, bool] = field(default_factory=dict)
    """entity_id -> whether they saved."""

    save_rolls: Dict[str, int] = field(default_factory=dict)
    """entity_id -> their save roll total."""

    conditions_applied: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    """(entity_id, condition) pairs."""

    stps: Tuple[StructuredTruthPacket, ...] = field(default_factory=tuple)
    """All STPs generated by this resolution."""

    error: Optional[str] = None
    """Error message if spell failed."""

    def __post_init__(self):
        """Ensure mutable fields are properly handled for frozen dataclass."""
        if not isinstance(self.affected_entities, tuple):
            object.__setattr__(self, 'affected_entities', tuple(self.affected_entities))
        if not isinstance(self.damage_dealt, dict):
            object.__setattr__(self, 'damage_dealt', dict(self.damage_dealt))
        if not isinstance(self.healing_done, dict):
            object.__setattr__(self, 'healing_done', dict(self.healing_done))
        if not isinstance(self.saves_made, dict):
            object.__setattr__(self, 'saves_made', dict(self.saves_made))
        if not isinstance(self.save_rolls, dict):
            object.__setattr__(self, 'save_rolls', dict(self.save_rolls))
        if not isinstance(self.conditions_applied, tuple):
            object.__setattr__(self, 'conditions_applied', tuple(self.conditions_applied))
        if not isinstance(self.stps, tuple):
            object.__setattr__(self, 'stps', tuple(self.stps))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "cast_id": self.cast_id,
            "spell_id": self.spell_id,
            "caster_id": self.caster_id,
            "success": self.success,
            "affected_entities": list(self.affected_entities),
            "damage_dealt": dict(self.damage_dealt),
            "healing_done": dict(self.healing_done),
            "saves_made": dict(self.saves_made),
            "save_rolls": dict(self.save_rolls),
            "conditions_applied": list(self.conditions_applied),
            "stps": [stp.to_dict() for stp in self.stps],
            "error": self.error,
        }


# ==============================================================================
# TARGET STATS — Entity stats needed for spell resolution
# ==============================================================================

@dataclass
class TargetStats:
    """Stats for a potential spell target.

    Provided by caller for each entity that might be affected.
    """

    entity_id: str
    """Entity identifier."""

    position: Position
    """Current position."""

    hit_points: int
    """Current HP."""

    max_hit_points: int
    """Maximum HP."""

    fort_save: int = 0
    """Fortitude save bonus."""

    ref_save: int = 0
    """Reflex save bonus."""

    will_save: int = 0
    """Will save bonus."""

    spell_resistance: int = 0
    """Spell resistance (0 = none)."""

    is_undead: bool = False
    """True if entity is undead (positive energy damages, negative heals)."""

    def get_save_bonus(self, save_type: SaveType) -> int:
        """Get save bonus for a specific save type."""
        if save_type == SaveType.FORT:
            return self.fort_save
        elif save_type == SaveType.REF:
            return self.ref_save
        elif save_type == SaveType.WILL:
            return self.will_save
        return 0


# ==============================================================================
# CASTER STATS — Caster stats needed for spell resolution
# ==============================================================================

@dataclass
class CasterStats:
    """Stats for the spellcaster.

    Provided by caller for DC calculation and other mechanics.
    """

    caster_id: str
    """Entity identifier."""

    position: Position
    """Current position."""

    caster_level: int
    """Caster level for spell effects."""

    spell_dc_base: int
    """Base spell DC (typically 10 + ability mod)."""

    attack_bonus: int = 0
    """Attack bonus for touch/ray spells."""

    spell_focus_bonus: int = 0
    """WO-ENGINE-SPELL-FOCUS-DC-001: Bonus DC from Spell Focus / Greater Spell Focus feats."""

    def get_spell_dc(self, spell_level: int) -> int:
        """Calculate spell DC for a given spell level.

        DC = 10 + spell level + ability modifier + spell focus bonus
        spell_dc_base = 10 + ability modifier
        """
        return self.spell_dc_base + spell_level + self.spell_focus_bonus


# ==============================================================================
# SPELL RESOLVER — Main resolution engine
# ==============================================================================

class SpellResolver:
    """Resolves spell casts against the tactical grid.

    Integrates with:
    - BattleGrid for spatial queries
    - AoE rasterization for area targeting
    - LOS/LOE checking for targeting validation
    - Cover calculation for reflex bonuses
    - RNGProvider for deterministic rolls
    - STPBuilder for audit trail generation
    """

    def __init__(
        self,
        grid: BattleGrid,
        rng: RNGProvider,
        spell_registry: Dict[str, SpellDefinition],
        turn: int = 0,
        initiative: int = 0
    ):
        """Initialize the spell resolver.

        Args:
            grid: BattleGrid for spatial queries
            rng: RNGProvider for deterministic rolls
            spell_registry: Dictionary of spell_id -> SpellDefinition
            turn: Current combat turn (for STPs)
            initiative: Current initiative count (for STPs)
        """
        self._grid = grid
        self._rng = rng
        self._spell_registry = spell_registry
        self._turn = turn
        self._initiative = initiative
        self._stp_builder = STPBuilder(turn, initiative)
        self._dice_rng = rng.stream("spell_dice")
        self._save_rng = rng.stream("spell_saves")

    def set_turn_context(self, turn: int, initiative: int) -> None:
        """Update turn/initiative context for STP generation."""
        self._turn = turn
        self._initiative = initiative
        self._stp_builder = STPBuilder(turn, initiative)

    # ==========================================================================
    # SPELL LOOKUP
    # ==========================================================================

    def get_spell(self, spell_id: str) -> Optional[SpellDefinition]:
        """Look up a spell by ID."""
        return self._spell_registry.get(spell_id)

    # ==========================================================================
    # CAST VALIDATION
    # ==========================================================================

    def validate_cast(
        self,
        intent: SpellCastIntent,
        caster: CasterStats,
    ) -> Tuple[bool, Optional[str]]:
        """Validate that a spell can be legally cast.

        Checks:
        1. Spell exists in registry
        2. Target is within range
        3. LOS to target (for targeted spells)
        4. LOE to target point (for area spells)
        5. Valid target type

        Args:
            intent: The casting intent
            caster: Caster stats including position

        Returns:
            (valid, error_message) tuple
        """
        spell = self.get_spell(intent.spell_id)
        if spell is None:
            return False, f"Unknown spell: {intent.spell_id}"

        # Self-targeting spells always valid
        if spell.target_type == SpellTarget.SELF:
            return True, None

        # Cone/line spells need direction (check early since they may not need target_position)
        if spell.aoe_shape in (AoEShape.CONE, AoEShape.LINE):
            direction = intent.aoe_direction or spell.aoe_direction
            if direction is None:
                return False, "Cone/line spells require a direction"
            # Cone/line spells originating from caster (range 0) are valid with just direction
            if spell.range_ft == 0:
                return True, None

        # Get target position
        target_pos: Optional[Position] = None
        if intent.target_position is not None:
            target_pos = intent.target_position
        elif intent.target_entity_id is not None:
            entity_pos = self._grid.get_entity_position(intent.target_entity_id)
            if entity_pos is None:
                return False, f"Target entity not found: {intent.target_entity_id}"
            target_pos = entity_pos

        # For area spells with range 0, target_position defaults to caster
        if target_pos is None and spell.target_type == SpellTarget.AREA and spell.range_ft == 0:
            target_pos = caster.position

        if target_pos is None and spell.target_type not in (SpellTarget.SELF,):
            return False, "No target specified"

        # Range check
        if target_pos is not None and spell.range_ft > 0:
            distance = caster.position.distance_to(target_pos)
            if distance > spell.range_ft:
                return False, f"Target out of range (distance: {distance}ft, range: {spell.range_ft}ft)"

        # LOS check for single-target spells
        if spell.target_type in (SpellTarget.SINGLE, SpellTarget.TOUCH, SpellTarget.RAY):
            if target_pos is not None:
                los_result = check_los(
                    self._grid, caster.position, 5, target_pos, 5
                )
                if not los_result.is_clear:
                    return False, f"No line of sight to target"

        return True, None

    # ==========================================================================
    # SPELL RESOLUTION
    # ==========================================================================

    def resolve_spell(
        self,
        intent: SpellCastIntent,
        caster: CasterStats,
        targets: Dict[str, TargetStats],
        world_state: Any = None,  # CP-18: optional — used to query condition save modifiers
        maximize: bool = False,  # WO-ENGINE-METAMAGIC-001: Maximize Spell feat
    ) -> SpellResolution:
        """Resolve a validated spell cast.

        Steps:
        1. Determine affected entities (single or AoE rasterization)
        2. Check LOS/LOE to each target
        3. Resolve saves for each target
        4. Apply damage (half on save if applicable)
        5. Apply conditions
        6. Generate STPs for all steps

        Args:
            intent: Validated casting intent
            caster: Caster stats
            targets: Dictionary of entity_id -> TargetStats for all potential targets

        Returns:
            SpellResolution with all effects and STPs
        """
        cast_id = str(uuid.uuid4())
        spell = self.get_spell(intent.spell_id)

        if spell is None:
            return SpellResolution(
                cast_id=cast_id,
                spell_id=intent.spell_id,
                caster_id=intent.caster_id,
                success=False,
                error=f"Unknown spell: {intent.spell_id}"
            )

        stps: List[StructuredTruthPacket] = []
        affected_entities: List[str] = []
        damage_dealt: Dict[str, int] = {}
        healing_done: Dict[str, int] = {}
        saves_made: Dict[str, bool] = {}
        save_rolls: Dict[str, int] = {}
        conditions_applied: List[Tuple[str, str]] = []

        # Determine affected entities based on target type
        if spell.target_type == SpellTarget.SELF:
            affected_entities = [intent.caster_id]

        elif spell.target_type == SpellTarget.AREA:
            affected_entities, aoe_stp = self._resolve_area_targets(
                spell, intent, caster, targets
            )
            if aoe_stp:
                stps.append(aoe_stp)

        elif intent.target_entity_id is not None:
            # Single target spells
            affected_entities = [intent.target_entity_id]

        # Calculate spell DC
        spell_dc = caster.get_spell_dc(spell.level)

        # Process each affected entity
        for entity_id in affected_entities:
            target = targets.get(entity_id)
            if target is None:
                continue

            # Check if target has cover (for reflex saves)
            cover_bonus = 0
            if spell.save_type == SaveType.REF:
                cover_result = calculate_cover(
                    caster.position, target.position, self._grid
                )
                cover_bonus = cover_result.reflex_bonus

            # Resolve save if required
            saved = False
            if spell.save_type is not None:
                # CP-18: compute condition save modifier for this target
                cond_save_mod = 0
                if world_state is not None:
                    cond_mods = get_condition_modifiers(world_state, entity_id)
                    if spell.save_type == SaveType.FORT:
                        cond_save_mod = cond_mods.fort_save_modifier
                    elif spell.save_type == SaveType.REF:
                        cond_save_mod = cond_mods.ref_save_modifier
                    else:
                        cond_save_mod = cond_mods.will_save_modifier

                saved, roll, save_stp = self._resolve_save(
                    target,
                    spell.save_type,
                    spell_dc,
                    caster.caster_id,
                    cover_bonus,
                    spell.rule_citations,
                    condition_save_mod=cond_save_mod,
                )
                saves_made[entity_id] = saved
                save_rolls[entity_id] = roll
                stps.append(save_stp)

            # Apply damage
            if spell.damage_dice is not None:
                damage, damage_stp = self._resolve_damage(
                    spell, caster, target, saved, maximize=maximize,
                    world_state=world_state, target_entity_id=entity_id
                )
                damage_dealt[entity_id] = damage
                stps.append(damage_stp)

            # Apply healing
            if spell.healing_dice is not None:
                healing, healing_stp = self._resolve_healing(
                    spell, caster, target
                )
                healing_done[entity_id] = healing
                stps.append(healing_stp)

            # Apply conditions
            if not saved and spell.conditions_on_fail:
                for condition in spell.conditions_on_fail:
                    conditions_applied.append((entity_id, condition))
                    condition_stp = self._create_condition_stp(
                        caster.caster_id, entity_id, condition, spell
                    )
                    stps.append(condition_stp)

            # Apply buff conditions (always on success for self/buff spells)
            if spell.conditions_on_success:
                for condition in spell.conditions_on_success:
                    conditions_applied.append((entity_id, condition))
                    condition_stp = self._create_condition_stp(
                        caster.caster_id, entity_id, condition, spell
                    )
                    stps.append(condition_stp)

        return SpellResolution(
            cast_id=cast_id,
            spell_id=intent.spell_id,
            caster_id=intent.caster_id,
            success=True,
            affected_entities=tuple(affected_entities),
            damage_dealt=damage_dealt,
            healing_done=healing_done,
            saves_made=saves_made,
            save_rolls=save_rolls,
            conditions_applied=tuple(conditions_applied),
            stps=tuple(stps),
        )

    # ==========================================================================
    # AREA TARGET RESOLUTION
    # ==========================================================================

    def _resolve_area_targets(
        self,
        spell: SpellDefinition,
        intent: SpellCastIntent,
        caster: CasterStats,
        targets: Dict[str, TargetStats],
    ) -> Tuple[List[str], Optional[StructuredTruthPacket]]:
        """Get all entities affected by an area spell.

        Rasterizes the AoE shape and finds all targets within it.

        Returns:
            (affected_entity_ids, aoe_stp)
        """
        if spell.aoe_shape is None or spell.aoe_radius_ft is None:
            return [], None

        origin = intent.target_position or caster.position

        # Rasterize the AoE
        if spell.aoe_shape == AoEShape.BURST:
            affected_squares = rasterize_burst(origin, spell.aoe_radius_ft)
        elif spell.aoe_shape == AoEShape.CONE:
            direction = intent.aoe_direction or spell.aoe_direction or AoEDirection.N
            affected_squares = rasterize_cone(origin, direction, spell.aoe_radius_ft)
        elif spell.aoe_shape == AoEShape.LINE:
            direction = intent.aoe_direction or spell.aoe_direction or AoEDirection.N
            affected_squares = rasterize_line(origin, direction, spell.aoe_radius_ft)
        else:
            # Default to burst for other shapes
            affected_squares = rasterize_burst(origin, spell.aoe_radius_ft)

        # Find all entities in affected squares
        affected_entities = self._grid.get_entities_in_area(affected_squares)

        # Filter out defeated entities (HP <= 0) — dead creatures are objects,
        # not valid AoE targets (D&D 3.5e rules). WO-AOE-DEFEATED-FILTER.
        affected_entities = [
            eid for eid in affected_entities
            if eid not in targets or targets[eid].hit_points > 0
        ]

        # Generate AoE STP
        aoe_stp = self._stp_builder.aoe_resolution(
            actor_id=intent.caster_id,
            origin=origin.to_dict(),
            shape=spell.aoe_shape.value,
            radius_ft=spell.aoe_radius_ft,
            affected_squares=[sq.to_dict() for sq in affected_squares],
            affected_entities=affected_entities,
            save_dc=caster.get_spell_dc(spell.level) if spell.save_type else 0,
            damage_dice=spell.damage_dice or "",
            citations=list(spell.rule_citations),
        )

        return affected_entities, aoe_stp

    # ==========================================================================
    # SAVE RESOLUTION
    # ==========================================================================

    def _resolve_save(
        self,
        target: TargetStats,
        save_type: SaveType,
        dc: int,
        caster_id: str,
        cover_bonus: int = 0,
        citations: Tuple[str, ...] = (),
        condition_save_mod: int = 0,  # CP-18: aggregated condition save penalty/bonus
    ) -> Tuple[bool, int, StructuredTruthPacket]:
        """Resolve a saving throw.

        Args:
            target: Target making the save
            save_type: Type of save (fort/ref/will)
            dc: Save DC
            caster_id: ID of caster (for STP)
            cover_bonus: Bonus from cover
            citations: Rule citations
            condition_save_mod: CP-18 — aggregated condition save modifier (e.g. -2 for shaken)

        Returns:
            (saved, roll_total, stp)
        """
        base_roll = self._save_rng.randint(1, 20)
        save_bonus = target.get_save_bonus(save_type)
        total_roll = base_roll + save_bonus + cover_bonus + condition_save_mod  # CP-18

        # PHB p.177: Natural 1 on a saving throw is always a failure,
        # natural 20 is always a success (regardless of modifiers/DC).
        if base_roll == 20:
            saved = True
        elif base_roll == 1:
            saved = False
        else:
            saved = total_roll >= dc

        modifiers = []
        if cover_bonus > 0:
            modifiers.append(("cover", cover_bonus))
        if condition_save_mod != 0:  # CP-18: include condition modifier in STP when non-zero
            modifiers.append(("condition", condition_save_mod))

        save_stp = self._stp_builder.saving_throw(
            actor_id=target.entity_id,
            save_type=save_type.value,
            base_roll=base_roll,
            save_bonus=save_bonus,
            dc=dc,
            modifiers=modifiers,
            citations=list(citations),
        )

        return saved, total_roll, save_stp

    # ==========================================================================
    # DAMAGE RESOLUTION
    # ==========================================================================

    def _resolve_damage(
        self,
        spell: SpellDefinition,
        caster: CasterStats,
        target: TargetStats,
        saved: bool,
        maximize: bool = False,  # WO-ENGINE-METAMAGIC-001: Maximize Spell feat
        world_state: Any = None,  # WO-ENGINE-EVASION-001: for Evasion/Improved Evasion lookup
        target_entity_id: Optional[str] = None,  # WO-ENGINE-EVASION-001
    ) -> Tuple[int, StructuredTruthPacket]:
        """Resolve damage for a spell.

        Args:
            spell: Spell being cast
            caster: Caster stats
            target: Target being damaged
            saved: Whether target made their save

        Returns:
            (damage_dealt, damage_stp)
        """
        if spell.damage_dice is None:
            return 0, self._stp_builder.damage_roll(
                actor_id=caster.caster_id,
                target_id=target.entity_id,
                dice="0",
                rolls=[],
                damage_type="untyped",
                modifiers=[],
                dr=0,
                citations=list(spell.rule_citations),
            )

        # Parse and roll damage dice (or maximize without consuming RNG)
        if maximize:
            from aidm.core.metamagic_resolver import apply_maximize_dice
            rolls = []  # No dice consumed — determinism preserved
            total = apply_maximize_dice(spell.damage_dice)
        else:
            rolls, total = self._roll_dice(spell.damage_dice)

        # Apply save effect
        if saved:
            if spell.save_effect == SaveEffect.HALF:
                total = total // 2
                # WO-ENGINE-EVASION-001: Evasion / Improved Evasion (PHB Rogue p.56, Monk p.41)
                if spell.save_type == SaveType.REF and world_state is not None and target_entity_id is not None:
                    _target_raw = world_state.entities.get(target_entity_id, {})
                    # WO-ENGINE-EVASION-ARMOR-001: Evasion requires light or no armor (PHB p.50)
                    _armor = _target_raw.get(EF.ARMOR_TYPE, "none")
                    _evasion_active = _armor in ("none", "light")
                    if _evasion_active and (_target_raw.get(EF.EVASION, False) or _target_raw.get(EF.IMPROVED_EVASION, False)):
                        total = 0
            elif spell.save_effect == SaveEffect.NEGATES:
                total = 0
        else:
            # WO-ENGINE-EVASION-001: Improved Evasion on failed save -> half damage (PHB Rogue p.57)
            if spell.save_type == SaveType.REF and spell.save_effect == SaveEffect.HALF:
                if world_state is not None and target_entity_id is not None:
                    _target_raw = world_state.entities.get(target_entity_id, {})
                    # WO-ENGINE-EVASION-ARMOR-001: Improved Evasion requires light or no armor (PHB p.50)
                    _armor = _target_raw.get(EF.ARMOR_TYPE, "none")
                    if _armor in ("none", "light") and _target_raw.get(EF.IMPROVED_EVASION, False):
                        total = total // 2

        # WO-ENGINE-ENERGY-RESISTANCE-001: Energy resistance (PHB p.291)
        # Resistance absorbs the first N points of a specific energy type per damage instance.
        if total > 0 and world_state is not None and target_entity_id is not None:
            _target_raw_er = world_state.entities.get(target_entity_id, {})
            _dmg_type = spell.damage_type.value if spell.damage_type else None
            if _dmg_type:
                _resistance = _target_raw_er.get(EF.ENERGY_RESISTANCE, {}).get(_dmg_type, 0)
                if _resistance > 0:
                    total = max(0, total - _resistance)

        # Generate damage STP
        damage_type = spell.damage_type.value if spell.damage_type else "untyped"
        damage_stp = self._stp_builder.damage_roll(
            actor_id=caster.caster_id,
            target_id=target.entity_id,
            dice=spell.damage_dice,
            rolls=rolls,
            damage_type=damage_type,
            modifiers=[],
            dr=0,  # DR not implemented yet
            citations=list(spell.rule_citations),
        )

        return total, damage_stp

    # ==========================================================================
    # HEALING RESOLUTION
    # ==========================================================================

    def _resolve_healing(
        self,
        spell: SpellDefinition,
        caster: CasterStats,
        target: TargetStats,
    ) -> Tuple[int, StructuredTruthPacket]:
        """Resolve healing for a spell.

        Args:
            spell: Spell being cast
            caster: Caster stats
            target: Target being healed

        Returns:
            (healing_done, healing_stp)
        """
        if spell.healing_dice is None:
            return 0, self._stp_builder.damage_roll(
                actor_id=caster.caster_id,
                target_id=target.entity_id,
                dice="0",
                rolls=[],
                damage_type="positive",
                modifiers=[],
                dr=0,
                citations=list(spell.rule_citations),
            )

        # Parse and roll healing dice (with caster level bonus for cure spells)
        rolls, total = self._roll_dice(spell.healing_dice)

        # Add caster level bonus (capped by spell level for cure spells)
        caster_level_bonus = min(caster.caster_level, spell.level * 5) if spell.level > 0 else caster.caster_level
        total += caster_level_bonus

        # WO-ENGINE-HOOLIGAN-TIER-A-001: Positive energy damages undead (PHB p.189)
        # Return negative value; play_loop applies as damage (no HP cap for damage)
        if target.is_undead:
            actual_healing = -total
        else:
            # Cap at max HP for living creatures
            max_healing = target.max_hit_points - target.hit_points
            actual_healing = min(total, max_healing)

        modifiers = [("caster_level", caster_level_bonus)]

        # Generate healing STP (using damage_roll format with positive type)
        healing_stp = self._stp_builder.damage_roll(
            actor_id=caster.caster_id,
            target_id=target.entity_id,
            dice=spell.healing_dice,
            rolls=rolls,
            damage_type="positive",
            modifiers=modifiers,
            dr=0,
            citations=list(spell.rule_citations),
        )

        return actual_healing, healing_stp

    # ==========================================================================
    # CONDITION APPLICATION
    # ==========================================================================

    def _create_condition_stp(
        self,
        caster_id: str,
        target_id: str,
        condition: str,
        spell: SpellDefinition,
    ) -> StructuredTruthPacket:
        """Create STP for condition application."""
        return self._stp_builder.condition_applied(
            actor_id=caster_id,
            target_id=target_id,
            condition_name=condition,
            source=spell.name,
            duration_rounds=spell.duration_rounds if spell.duration_rounds > 0 else None,
            save_dc=None,  # Already resolved
            save_type=spell.save_type.value if spell.save_type else None,
            citations=list(spell.rule_citations),
        )

    # ==========================================================================
    # DICE ROLLING
    # ==========================================================================

    def _roll_dice(self, dice_expr: str) -> Tuple[List[int], int]:
        """Roll dice from a dice expression.

        Supports formats like '8d6', '2d8+5', '1d12'.

        Args:
            dice_expr: Dice expression string

        Returns:
            (individual_rolls, total)
        """
        # Parse dice expression: NdX or NdX+Y
        dice_expr = dice_expr.lower().strip()

        # Handle bonus
        bonus = 0
        if '+' in dice_expr:
            parts = dice_expr.split('+')
            dice_expr = parts[0]
            bonus = int(parts[1])
        elif '-' in dice_expr:
            parts = dice_expr.split('-')
            dice_expr = parts[0]
            bonus = -int(parts[1])

        # Parse NdX
        if 'd' not in dice_expr:
            return [], bonus

        parts = dice_expr.split('d')
        num_dice = int(parts[0]) if parts[0] else 1
        die_size = int(parts[1])

        # Roll dice
        rolls = []
        for _ in range(num_dice):
            roll = self._dice_rng.randint(1, die_size)
            rolls.append(roll)

        total = sum(rolls) + bonus
        return rolls, total


# ==============================================================================
# CONVENIENCE FACTORY
# ==============================================================================

def create_spell_resolver(
    grid: BattleGrid,
    rng: RNGProvider,
    spell_registry: Dict[str, SpellDefinition],
    turn: int = 0,
    initiative: int = 0
) -> SpellResolver:
    """Factory function to create a SpellResolver.

    Args:
        grid: BattleGrid for spatial queries
        rng: RNGProvider for deterministic rolls
        spell_registry: Dictionary of spell definitions
        turn: Current turn number
        initiative: Current initiative count

    Returns:
        Configured SpellResolver
    """
    return SpellResolver(
        grid=grid,
        rng=rng,
        spell_registry=spell_registry,
        turn=turn,
        initiative=initiative,
    )


# ==============================================================================
# CONCENTRATION CHECK — WO-035 Integration
# ==============================================================================

def check_concentration_on_damage(
    caster: Dict[str, Any],
    damage_taken: int,
    rng: RNGProvider,
    duration_tracker: 'DurationTracker',
    spell_level: int = 0,
) -> Tuple[bool, Optional[Any], List[Any]]:
    """Check if concentration is maintained after taking damage.

    PHB p.69: Concentration check (DC = 10 + damage taken + spell level)
    required when caster takes damage while maintaining a concentration spell.
    Uses Concentration skill.

    Args:
        caster: Entity dict of caster maintaining concentration
        damage_taken: Amount of damage taken
        rng: RNG manager for skill check
        duration_tracker: DurationTracker instance to check active concentration

    Returns:
        Tuple of (concentration_maintained, skill_check_result, events)
        - concentration_maintained: True if check succeeded or no concentration active
        - skill_check_result: SkillCheckResult if check was made, None otherwise
        - events: List of Event objects (concentration_check, concentration_broken)
    """
    from aidm.schemas.entity_fields import EF
    from aidm.core.event_log import Event

    events = []
    caster_id = caster.get(EF.ENTITY_ID, "unknown")

    # Check if caster has active concentration
    if not duration_tracker.has_active_concentration(caster_id):
        return (True, None, events)

    # Concentration check: DC = 10 + damage taken + spell level (PHB p.69)
    dc = 10 + damage_taken + spell_level

    from aidm.core.skill_resolver import resolve_skill_check
    from aidm.schemas.skills import SkillID

    # Perform Concentration check
    check_result = resolve_skill_check(
        entity=caster,
        skill_id=SkillID.CONCENTRATION,
        dc=dc,
        rng=rng,
        circumstance_modifier=0
    )

    # Emit concentration check event
    events.append(Event(
        event_id=0,  # Caller should renumber
        event_type="concentration_check",
        timestamp=0.0,  # Caller should set timestamp
        payload={
            "entity_id": caster_id,
            "damage_taken": damage_taken,
            "dc": dc,
            "total": check_result.total,
            "d20_roll": check_result.d20_roll,
            "success": check_result.success,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 69}]  # PHB Concentration
    ))

    if check_result.success:
        # Concentration maintained
        return (True, check_result, events)
    else:
        # Concentration broken
        concentration_effect = duration_tracker.get_concentration_effect(caster_id)
        broken_effects = duration_tracker.break_concentration(caster_id)

        events.append(Event(
            event_id=0,  # Caller should renumber
            event_type="concentration_broken",
            timestamp=0.0,  # Caller should set timestamp
            payload={
                "entity_id": caster_id,
                "spell_id": concentration_effect.spell_id if concentration_effect else None,
                "spell_name": concentration_effect.spell_name if concentration_effect else None,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 69}]  # PHB Concentration
        ))

        return (False, check_result, events)
