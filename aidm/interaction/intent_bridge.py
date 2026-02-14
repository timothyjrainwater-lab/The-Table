"""Intent Bridge: Translate player-facing intents into engine-facing intents.

Bridges the voice layer to combat resolution. Translates DeclaredAttackIntent
(target names, weapon names) into AttackIntent (entity IDs, Weapon objects).

WO-038: Intent Bridge
Architecture: Boundary layer between interaction and combat resolution
Reference: BL-020 (FrozenWorldStateView for read-only state access)
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum

from aidm.schemas.intents import DeclaredAttackIntent, CastSpellIntent, MoveIntent
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.position import Position
from aidm.core.spell_resolver import SpellCastIntent
from aidm.core.state import FrozenWorldStateView
from aidm.schemas.entity_fields import EF
from aidm.schemas.spell_definitions import SPELL_REGISTRY


# ==============================================================================
# CLARIFICATION REQUEST — When intent cannot be resolved unambiguously
# ==============================================================================

class AmbiguityType(str, Enum):
    """Types of ambiguity requiring clarification."""
    TARGET_AMBIGUOUS = "target_ambiguous"
    TARGET_NOT_FOUND = "target_not_found"
    WEAPON_AMBIGUOUS = "weapon_ambiguous"
    WEAPON_NOT_FOUND = "weapon_not_found"
    SPELL_NOT_FOUND = "spell_not_found"
    DESTINATION_OUT_OF_BOUNDS = "destination_out_of_bounds"


@dataclass(frozen=True)
class ClarificationRequest:
    """Request for user clarification when intent is ambiguous.

    Returned when the bridge cannot unambiguously resolve a declared intent
    (e.g., "Goblin" matches multiple entities, unknown weapon, etc.).

    Attributes:
        intent_type: Type of intent that failed (attack, spell, move)
        ambiguity_type: Specific type of ambiguity encountered
        candidates: List of possible matches for user to choose from
        message: Human-readable clarification prompt
    """

    intent_type: str
    """Type of intent: 'attack', 'spell', 'move'"""

    ambiguity_type: AmbiguityType
    """Specific ambiguity type"""

    candidates: Tuple[str, ...]
    """Possible matches (entity names, weapon names, spell names)"""

    message: str
    """Human-readable prompt for user"""

    def __post_init__(self):
        """Ensure candidates is a tuple."""
        if not isinstance(self.candidates, tuple):
            object.__setattr__(self, 'candidates', tuple(self.candidates))


# ==============================================================================
# INTENT BRIDGE — Main translation class
# ==============================================================================

class IntentBridge:
    """Translates player-facing declared intents into engine-facing resolved intents.

    Resolves:
    - Entity names → entity IDs
    - Weapon names → Weapon objects
    - Spell names → spell IDs
    - Position validation

    Uses FrozenWorldStateView for read-only state access (BL-020).
    No state mutation, no combat resolution.

    Usage:
        view = FrozenWorldStateView(world_state)
        bridge = IntentBridge()

        # Attack resolution
        declared = DeclaredAttackIntent(target_ref="Goblin", weapon="longsword")
        result = bridge.resolve_attack("pc_fighter", declared, view)

        if isinstance(result, AttackIntent):
            # Success - pass to combat resolver
            pass
        else:
            # ClarificationRequest - present to user
            print(result.message)
    """

    def resolve_attack(
        self,
        actor_id: str,
        declared: DeclaredAttackIntent,
        view: FrozenWorldStateView,
    ) -> AttackIntent | ClarificationRequest:
        """Resolve declared attack intent into engine-ready AttackIntent.

        Args:
            actor_id: Entity performing the attack
            declared: Player's declared attack intent (target name, weapon name)
            view: Read-only view of world state

        Returns:
            AttackIntent if resolved successfully, else ClarificationRequest

        Examples:
            >>> # Exact match
            >>> declared = DeclaredAttackIntent(target_ref="Goblin Warrior")
            >>> result = bridge.resolve_attack("pc_fighter", declared, view)
            >>> assert isinstance(result, AttackIntent)

            >>> # Ambiguous match
            >>> declared = DeclaredAttackIntent(target_ref="Goblin")  # Multiple goblins
            >>> result = bridge.resolve_attack("pc_fighter", declared, view)
            >>> assert isinstance(result, ClarificationRequest)
            >>> assert result.ambiguity_type == AmbiguityType.TARGET_AMBIGUOUS
        """
        # Resolve target entity
        target_result = self._resolve_entity_name(
            declared.target_ref,
            view,
            exclude_id=actor_id,
        )

        if isinstance(target_result, ClarificationRequest):
            # Target resolution failed - return clarification request
            return target_result

        target_id = target_result

        # Resolve weapon
        actor = view.entities.get(actor_id)
        if actor is None:
            return ClarificationRequest(
                intent_type="attack",
                ambiguity_type=AmbiguityType.TARGET_NOT_FOUND,
                candidates=tuple(),
                message=f"Actor '{actor_id}' not found in world state",
            )

        weapon_result = self._resolve_weapon(declared.weapon, actor)

        if isinstance(weapon_result, ClarificationRequest):
            return weapon_result

        weapon, attack_bonus = weapon_result

        # Build AttackIntent
        return AttackIntent(
            attacker_id=actor_id,
            target_id=target_id,
            attack_bonus=attack_bonus,
            weapon=weapon,
        )

    def resolve_spell(
        self,
        caster_id: str,
        declared: CastSpellIntent,
        view: FrozenWorldStateView,
        target_position: Optional[Position] = None,
        target_entity_ref: Optional[str] = None,
    ) -> SpellCastIntent | ClarificationRequest:
        """Resolve declared spell intent into engine-ready SpellCastIntent.

        Args:
            caster_id: Entity casting the spell
            declared: Player's declared spell intent
            view: Read-only view of world state
            target_position: Optional target position for area spells
            target_entity_ref: Optional target entity name for single-target spells

        Returns:
            SpellCastIntent if resolved successfully, else ClarificationRequest

        Citations:
            PHB p.174: Spell targeting and ranges
        """
        # Resolve spell name to spell_id
        spell_id_result = self._resolve_spell_name(declared.spell_name)

        if isinstance(spell_id_result, ClarificationRequest):
            return spell_id_result

        spell_id = spell_id_result

        # Resolve target entity if provided
        target_entity_id = None
        if target_entity_ref:
            target_result = self._resolve_entity_name(target_entity_ref, view, exclude_id=caster_id)

            if isinstance(target_result, ClarificationRequest):
                return target_result

            target_entity_id = target_result

        # Build SpellCastIntent
        return SpellCastIntent(
            caster_id=caster_id,
            spell_id=spell_id,
            target_position=target_position,
            target_entity_id=target_entity_id,
        )

    def resolve_move(
        self,
        actor_id: str,
        declared: MoveIntent,
        view: FrozenWorldStateView,
    ) -> MoveIntent | ClarificationRequest:
        """Validate declared move intent.

        Args:
            actor_id: Entity performing the move
            declared: Player's declared move intent
            view: Read-only view of world state

        Returns:
            MoveIntent if valid, else ClarificationRequest

        Note:
            This validates basic structure but does NOT check legality
            (speed limits, terrain, AoO, etc.). Full legality checking
            is deferred to movement resolver.
        """
        # Basic validation: destination must be provided
        if declared.destination is None:
            return ClarificationRequest(
                intent_type="move",
                ambiguity_type=AmbiguityType.DESTINATION_OUT_OF_BOUNDS,
                candidates=tuple(),
                message="Move intent requires a destination position",
            )

        # Return validated intent
        return declared

    # ==========================================================================
    # PRIVATE HELPERS — Entity, weapon, spell resolution
    # ==========================================================================

    def _resolve_entity_name(
        self,
        name_ref: Optional[str],
        view: FrozenWorldStateView,
        exclude_id: Optional[str] = None,
    ) -> str | ClarificationRequest:
        """Resolve entity name to entity ID.

        Args:
            name_ref: Entity name reference (can be partial)
            view: Read-only view of world state
            exclude_id: Entity ID to exclude from matches (e.g., self-targeting)

        Returns:
            entity_id if resolved, else ClarificationRequest

        Resolution strategy:
            1. Exact match on display name → entity_id
            2. Partial match with single candidate → entity_id
            3. Multiple matches → ClarificationRequest with candidates
            4. No matches → ClarificationRequest with error message
        """
        if name_ref is None or name_ref.strip() == "":
            # Build list of available targets
            available = []
            for entity_id, entity in view.entities.items():
                if exclude_id and entity_id == exclude_id:
                    continue
                if entity.get(EF.DEFEATED, False):
                    continue
                display_name = entity.get("name", entity_id)
                available.append(display_name)
            available.sort(key=lambda n: n.lower())

            return ClarificationRequest(
                intent_type="attack",
                ambiguity_type=AmbiguityType.TARGET_NOT_FOUND,
                candidates=tuple(available),
                message=f"No target specified. Available targets: {', '.join(available)}",
            )

        name_lower = name_ref.strip().lower()

        # Build list of candidates
        exact_matches = []
        partial_matches = []

        for entity_id, entity in view.entities.items():
            if exclude_id and entity_id == exclude_id:
                continue

            # Skip defeated entities
            if entity.get(EF.DEFEATED, False):
                continue

            # Get display name
            display_name = entity.get("name", entity_id)

            # Check for exact match (case-insensitive)
            if display_name.lower() == name_lower:
                exact_matches.append((entity_id, display_name))
            # Check for partial match
            elif name_lower in display_name.lower():
                partial_matches.append((entity_id, display_name))

        # Resolution logic
        if len(exact_matches) == 1:
            # Single exact match
            return exact_matches[0][0]
        elif len(exact_matches) > 1:
            # Multiple exact matches (should be rare)
            sorted_matches = sorted(exact_matches, key=lambda m: m[1].lower())
            candidates = tuple(display_name for _, display_name in sorted_matches)
            return ClarificationRequest(
                intent_type="attack",
                ambiguity_type=AmbiguityType.TARGET_AMBIGUOUS,
                candidates=candidates,
                message=f"Multiple entities match '{name_ref}': {', '.join(candidates)}",
            )
        elif len(partial_matches) == 1:
            # Single partial match
            return partial_matches[0][0]
        elif len(partial_matches) > 1:
            # Multiple partial matches
            sorted_matches = sorted(partial_matches, key=lambda m: m[1].lower())
            candidates = tuple(display_name for _, display_name in sorted_matches)
            return ClarificationRequest(
                intent_type="attack",
                ambiguity_type=AmbiguityType.TARGET_AMBIGUOUS,
                candidates=candidates,
                message=f"Ambiguous target '{name_ref}'. Did you mean: {', '.join(candidates)}?",
            )
        else:
            # No matches
            available = []
            for entity_id, entity in view.entities.items():
                if exclude_id and entity_id == exclude_id:
                    continue
                if entity.get(EF.DEFEATED, False):
                    continue
                display_name = entity.get("name", entity_id)
                available.append(display_name)
            available.sort(key=lambda n: n.lower())

            return ClarificationRequest(
                intent_type="attack",
                ambiguity_type=AmbiguityType.TARGET_NOT_FOUND,
                candidates=tuple(available),
                message=f"Target '{name_ref}' not found. Available targets: {', '.join(available)}",
            )

    def _resolve_weapon(
        self,
        weapon_name: Optional[str],
        actor: dict,
    ) -> Tuple[Weapon, int] | ClarificationRequest:
        """Resolve weapon name to Weapon object and attack bonus.

        Args:
            weapon_name: Weapon name (can be None for default weapon)
            actor: Actor entity dict

        Returns:
            (Weapon, attack_bonus) if resolved, else ClarificationRequest

        Resolution strategy:
            1. If weapon_name provided: match against entity's equipment
            2. If no weapon_name: use entity's default weapon (EF.WEAPON field)
            3. If entity has single weapon: use that weapon
            4. If no weapon found: return ClarificationRequest
        """
        # Get attack bonus
        attack_bonus = actor.get(EF.ATTACK_BONUS, 0)
        if attack_bonus == 0:
            # Fallback: compute from BAB + STR_MOD
            bab = actor.get(EF.BAB, 0)
            str_mod = actor.get(EF.STR_MOD, 0)
            attack_bonus = bab + str_mod

        # Case 1: No weapon name specified - use default
        if weapon_name is None or weapon_name.strip() == "":
            default_weapon = actor.get(EF.WEAPON)

            # WO-WEAPON-PLUMBING-001: Handle dict weapon data pattern
            if isinstance(default_weapon, dict):
                weapon = self._build_weapon_from_dict(default_weapon)
                return (weapon, attack_bonus)

            if default_weapon:
                # Entity has default weapon name string - resolve it
                weapon_data = actor.get("weapon_damage", "1d6")
                weapon = self._build_weapon_from_data(default_weapon, weapon_data)
                return (weapon, attack_bonus)

            # No default weapon - use unarmed strike
            str_mod = actor.get(EF.STR_MOD, 0)
            weapon = Weapon(
                damage_dice="1d3",
                damage_bonus=str_mod,
                damage_type="bludgeoning",
                weapon_type="natural",
            )
            return (weapon, attack_bonus)

        # Case 2: Weapon name specified - match against equipment
        weapon_name_lower = weapon_name.strip().lower()

        # WO-WEAPON-PLUMBING-001: Check if EF.WEAPON is a dict
        entity_weapon = actor.get(EF.WEAPON)
        if isinstance(entity_weapon, dict):
            weapon = self._build_weapon_from_dict(entity_weapon)
            return (weapon, attack_bonus)

        # String pattern: check if weapon name matches entity's weapon field
        entity_weapon_str = (entity_weapon or "").lower()
        if entity_weapon_str == weapon_name_lower:
            weapon_data = actor.get("weapon_damage", "1d6")
            weapon = self._build_weapon_from_data(weapon_name, weapon_data)
            return (weapon, attack_bonus)

        # Weapon not found
        available_weapons = []
        if actor.get(EF.WEAPON):
            available_weapons.append(actor[EF.WEAPON])

        return ClarificationRequest(
            intent_type="attack",
            ambiguity_type=AmbiguityType.WEAPON_NOT_FOUND,
            candidates=tuple(available_weapons),
            message=f"Weapon '{weapon_name}' not found. Available: {', '.join(available_weapons) or 'unarmed strike'}",
        )

    def _build_weapon_from_data(
        self,
        weapon_name: str,
        weapon_damage: str,
    ) -> Weapon:
        """Build Weapon object from simple damage string.

        Args:
            weapon_name: Weapon name (for damage type inference)
            weapon_damage: Damage expression like "1d8+3"

        Returns:
            Weapon object

        Note:
            This is a simplified weapon builder. Full weapon stat lookup
            would query a weapon registry by name. For WO-038, we infer
            damage type from weapon name.
        """
        # Parse damage_dice and damage_bonus from expression like "1d8+3"
        if "+" in weapon_damage:
            dice_part, bonus_part = weapon_damage.split("+", 1)
            damage_dice = dice_part.strip()
            damage_bonus = int(bonus_part.strip())
        elif "-" in weapon_damage:
            dice_part, bonus_part = weapon_damage.split("-", 1)
            damage_dice = dice_part.strip()
            damage_bonus = -int(bonus_part.strip())
        else:
            damage_dice = weapon_damage.strip()
            damage_bonus = 0

        # Infer damage type from weapon name
        weapon_lower = weapon_name.lower()
        if any(x in weapon_lower for x in ["sword", "axe", "scythe"]):
            damage_type = "slashing"
        elif any(x in weapon_lower for x in ["spear", "dagger", "arrow", "rapier"]):
            damage_type = "piercing"
        elif any(x in weapon_lower for x in ["mace", "club", "hammer", "flail"]):
            damage_type = "bludgeoning"
        else:
            # Default to slashing
            damage_type = "slashing"

        # Build weapon
        return Weapon(
            damage_dice=damage_dice,
            damage_bonus=damage_bonus,
            damage_type=damage_type,
        )

    def _build_weapon_from_dict(
        self,
        weapon_data: dict,
    ) -> Weapon:
        """Build Weapon object from entity weapon data dict.

        WO-WEAPON-PLUMBING-001: Handles the dict pattern where EF.WEAPON stores
        full weapon data (damage_dice, damage_bonus, damage_type, weapon_type,
        range_increment, grip, etc.).

        Args:
            weapon_data: Dict from entity's EF.WEAPON field

        Returns:
            Weapon object with all fields populated from dict (defaults for missing)
        """
        return Weapon(
            damage_dice=weapon_data.get("damage_dice", "1d4"),
            damage_bonus=weapon_data.get("damage_bonus", 0),
            damage_type=weapon_data.get("damage_type", "bludgeoning"),
            critical_multiplier=weapon_data.get("critical_multiplier", 2),
            critical_range=weapon_data.get("critical_range", 20),
            is_two_handed=weapon_data.get("is_two_handed", False),
            grip=weapon_data.get("grip", "one-handed"),
            weapon_type=weapon_data.get("weapon_type", "one-handed"),
            range_increment=weapon_data.get("range_increment", 0),
        )

    def _resolve_spell_name(
        self,
        spell_name: str,
    ) -> str | ClarificationRequest:
        """Resolve spell name to spell_id.

        Args:
            spell_name: Spell name from player

        Returns:
            spell_id if found in SPELL_REGISTRY, else ClarificationRequest
        """
        if not spell_name or spell_name.strip() == "":
            available = list(SPELL_REGISTRY.keys())
            return ClarificationRequest(
                intent_type="spell",
                ambiguity_type=AmbiguityType.SPELL_NOT_FOUND,
                candidates=tuple(available[:10]),  # Show first 10
                message=f"No spell specified. Available spells: {', '.join(available[:10])}...",
            )

        spell_name_lower = spell_name.strip().lower()

        # Exact match (spell_id)
        if spell_name_lower in SPELL_REGISTRY:
            return spell_name_lower

        # Match by display name
        for spell_id, spell_def in SPELL_REGISTRY.items():
            if spell_def.name.lower() == spell_name_lower:
                return spell_id

        # No match - return error
        available = list(SPELL_REGISTRY.keys())
        return ClarificationRequest(
            intent_type="spell",
            ambiguity_type=AmbiguityType.SPELL_NOT_FOUND,
            candidates=tuple(available[:10]),
            message=f"Spell '{spell_name}' not found. Available spells: {', '.join(available[:10])}...",
        )
