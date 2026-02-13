"""Duration tracking for active spell effects.

Tracks spell effects across combat rounds and handles expiration,
concentration breaking, and dispelling.

WO-014: Spellcasting Resolution Core
Reference: PHB Chapter 10 (Duration)
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aidm.core.truth_packets import STPBuilder, StructuredTruthPacket


# ==============================================================================
# ACTIVE SPELL EFFECT — Single tracked spell effect
# ==============================================================================

@dataclass
class ActiveSpellEffect:
    """A spell effect currently active on an entity.

    Tracks the lifecycle of a spell effect including duration,
    concentration status, and the condition it applies.
    """

    effect_id: str
    """Unique identifier for this effect instance."""

    spell_id: str
    """ID of the spell that created this effect."""

    spell_name: str
    """Display name of the spell."""

    caster_id: str
    """Entity that cast the spell."""

    target_id: str
    """Entity the effect is on."""

    rounds_remaining: int
    """Rounds until effect expires (-1 = permanent until dispelled)."""

    concentration: bool
    """Whether the effect requires concentration."""

    condition_applied: Optional[str] = None
    """Condition this effect applies (e.g., 'paralyzed', 'hasted')."""

    turn_applied: int = 0
    """Turn number when effect was applied."""

    def is_permanent(self) -> bool:
        """Check if effect is permanent (no duration tracking)."""
        return self.rounds_remaining == -1

    def is_expired(self) -> bool:
        """Check if effect has expired (0 rounds remaining)."""
        return self.rounds_remaining == 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "effect_id": self.effect_id,
            "spell_id": self.spell_id,
            "spell_name": self.spell_name,
            "caster_id": self.caster_id,
            "target_id": self.target_id,
            "rounds_remaining": self.rounds_remaining,
            "concentration": self.concentration,
            "condition_applied": self.condition_applied,
            "turn_applied": self.turn_applied,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActiveSpellEffect':
        """Deserialize from dictionary."""
        return cls(
            effect_id=data["effect_id"],
            spell_id=data["spell_id"],
            spell_name=data["spell_name"],
            caster_id=data["caster_id"],
            target_id=data["target_id"],
            rounds_remaining=data["rounds_remaining"],
            concentration=data["concentration"],
            condition_applied=data.get("condition_applied"),
            turn_applied=data.get("turn_applied", 0),
        )


# ==============================================================================
# DURATION TRACKER — Tracks all active spell effects
# ==============================================================================

class DurationTracker:
    """Tracks active spell effects and handles expiration.

    Maintains a registry of all active spell effects and provides
    methods for:
    - Adding new effects
    - Advancing rounds (tick_round)
    - Querying effects on entities
    - Breaking concentration
    - Dispelling effects
    """

    def __init__(self):
        """Initialize empty duration tracker."""
        self._effects: Dict[str, ActiveSpellEffect] = {}
        self._by_target: Dict[str, List[str]] = {}  # target_id -> [effect_ids]
        self._by_caster: Dict[str, List[str]] = {}  # caster_id -> [effect_ids]
        self._concentration: Dict[str, List[str]] = {}  # caster_id -> [effect_ids] (3.5e: multiple allowed)

    # ==========================================================================
    # EFFECT MANAGEMENT
    # ==========================================================================

    def add_effect(self, effect: ActiveSpellEffect) -> None:
        """Add a new spell effect.

        In D&D 3.5e, a caster may maintain multiple concentration spells
        simultaneously. Each requires a separate Concentration check when
        the caster takes damage (PHB p.170). There is no automatic
        displacement of existing concentration effects.

        Args:
            effect: The effect to add
        """
        # Track concentration (3.5e: multiple concentration spells allowed)
        if effect.concentration:
            if effect.caster_id not in self._concentration:
                self._concentration[effect.caster_id] = []
            self._concentration[effect.caster_id].append(effect.effect_id)

        # Add to main registry
        self._effects[effect.effect_id] = effect

        # Index by target
        if effect.target_id not in self._by_target:
            self._by_target[effect.target_id] = []
        self._by_target[effect.target_id].append(effect.effect_id)

        # Index by caster
        if effect.caster_id not in self._by_caster:
            self._by_caster[effect.caster_id] = []
        self._by_caster[effect.caster_id].append(effect.effect_id)

    def remove_effect(self, effect_id: str) -> Optional[ActiveSpellEffect]:
        """Remove an effect by ID.

        Args:
            effect_id: ID of effect to remove

        Returns:
            The removed effect, or None if not found
        """
        if effect_id not in self._effects:
            return None

        effect = self._effects.pop(effect_id)

        # Remove from target index
        if effect.target_id in self._by_target:
            if effect_id in self._by_target[effect.target_id]:
                self._by_target[effect.target_id].remove(effect_id)
            if not self._by_target[effect.target_id]:
                del self._by_target[effect.target_id]

        # Remove from caster index
        if effect.caster_id in self._by_caster:
            if effect_id in self._by_caster[effect.caster_id]:
                self._by_caster[effect.caster_id].remove(effect_id)
            if not self._by_caster[effect.caster_id]:
                del self._by_caster[effect.caster_id]

        # Remove from concentration tracking
        if effect.caster_id in self._concentration:
            if effect_id in self._concentration[effect.caster_id]:
                self._concentration[effect.caster_id].remove(effect_id)
            if not self._concentration[effect.caster_id]:
                del self._concentration[effect.caster_id]

        return effect

    def get_effect(self, effect_id: str) -> Optional[ActiveSpellEffect]:
        """Get an effect by ID."""
        return self._effects.get(effect_id)

    # ==========================================================================
    # ROUND TICK
    # ==========================================================================

    def tick_round(self) -> List[ActiveSpellEffect]:
        """Advance one round and return expired effects.

        Decrements rounds_remaining for all non-permanent effects.
        Effects that reach 0 rounds are removed and returned.

        Returns:
            List of effects that expired this round
        """
        expired = []

        for effect_id in list(self._effects.keys()):
            effect = self._effects[effect_id]

            # Skip permanent effects
            if effect.is_permanent():
                continue

            # Decrement duration
            effect.rounds_remaining -= 1

            # Check for expiration
            if effect.is_expired():
                removed = self.remove_effect(effect_id)
                if removed:
                    expired.append(removed)

        return expired

    # ==========================================================================
    # QUERIES
    # ==========================================================================

    def get_effects_on(self, entity_id: str) -> List[ActiveSpellEffect]:
        """Get all effects on a specific entity.

        Args:
            entity_id: Entity to query

        Returns:
            List of active effects on that entity
        """
        effect_ids = self._by_target.get(entity_id, [])
        return [self._effects[eid] for eid in effect_ids if eid in self._effects]

    def get_effects_by_caster(self, caster_id: str) -> List[ActiveSpellEffect]:
        """Get all effects cast by a specific entity.

        Args:
            caster_id: Caster to query

        Returns:
            List of active effects from that caster
        """
        effect_ids = self._by_caster.get(caster_id, [])
        return [self._effects[eid] for eid in effect_ids if eid in self._effects]

    def get_concentration_effects(self, caster_id: str) -> List[ActiveSpellEffect]:
        """Get all concentration effects for a caster.

        In D&D 3.5e, a caster may maintain multiple concentration spells.

        Args:
            caster_id: Caster to query

        Returns:
            List of active concentration effects (may be empty)
        """
        effect_ids = self._concentration.get(caster_id, [])
        return [self._effects[eid] for eid in effect_ids if eid in self._effects]

    def get_concentration_effect(self, caster_id: str) -> Optional[ActiveSpellEffect]:
        """Get the first concentration effect for a caster (if any).

        Convenience method for callers that expect a single effect.
        For 3.5e compliance, prefer get_concentration_effects() which
        returns all active concentration spells.

        Args:
            caster_id: Caster to query

        Returns:
            First active concentration effect, or None
        """
        effects = self.get_concentration_effects(caster_id)
        return effects[0] if effects else None

    def has_effect(self, entity_id: str, spell_id: str) -> bool:
        """Check if an entity has an effect from a specific spell.

        Args:
            entity_id: Entity to check
            spell_id: Spell to check for

        Returns:
            True if entity has that spell effect active
        """
        for effect in self.get_effects_on(entity_id):
            if effect.spell_id == spell_id:
                return True
        return False

    def has_condition(self, entity_id: str, condition: str) -> bool:
        """Check if an entity has a specific condition from any spell.

        Args:
            entity_id: Entity to check
            condition: Condition to check for

        Returns:
            True if entity has that condition from a spell effect
        """
        for effect in self.get_effects_on(entity_id):
            if effect.condition_applied == condition:
                return True
        return False

    # ==========================================================================
    # CONCENTRATION
    # ==========================================================================

    def break_concentration(self, caster_id: str) -> List[ActiveSpellEffect]:
        """Break concentration for a caster.

        Removes all concentration effects from the caster.
        In D&D 3.5e, failing a Concentration check ends all
        concentration spells the caster is maintaining.

        Args:
            caster_id: Caster whose concentration is broken

        Returns:
            List of effects that were removed
        """
        removed = []
        effect_ids = list(self._concentration.get(caster_id, []))

        for effect_id in effect_ids:
            effect = self.remove_effect(effect_id)
            if effect:
                removed.append(effect)

        return removed

    def check_concentration_on_damage(
        self,
        caster_id: str,
        damage_taken: int,
        rng: Any,
    ) -> tuple[bool, Optional['SkillCheckResult']]:
        """Check if concentration is maintained after taking damage.

        PHB p.170: Concentration check (DC = 10 + damage taken) required
        for each concentration spell when caster takes damage.
        In 3.5e, each spell requires a separate check.

        Args:
            caster_id: Entity maintaining concentration
            damage_taken: Amount of damage taken
            rng: RNG manager for skill check

        Returns:
            Tuple of (concentration_maintained, check_result)
            - If no concentration active: (True, None)
            - Otherwise: raises NotImplementedError (caller handles)
        """
        effect_ids = self._concentration.get(caster_id, [])
        if not effect_ids:
            # No concentration active, no check needed
            return (True, None)

        # Get the caster entity from world state (we'll need it passed in)
        # For now, we'll return the DC and let the caller handle the check
        # This is a limitation - the DurationTracker doesn't have access to entities
        # We'll handle this at the integration point instead
        raise NotImplementedError(
            "check_concentration_on_damage should be called from combat resolver, "
            "not from DurationTracker directly. Use has_active_concentration() to check."
        )

    def has_active_concentration(self, caster_id: str) -> bool:
        """Check if a caster has any active concentration effects.

        Args:
            caster_id: Entity to check

        Returns:
            True if caster is maintaining one or more concentration effects
        """
        return bool(self._concentration.get(caster_id))

    # ==========================================================================
    # DISPEL
    # ==========================================================================

    def dispel_effect(self, effect_id: str) -> Optional[ActiveSpellEffect]:
        """Dispel an effect by ID.

        Args:
            effect_id: Effect to dispel

        Returns:
            The dispelled effect, or None if not found
        """
        return self.remove_effect(effect_id)

    def dispel_effects_on(
        self,
        entity_id: str,
        spell_id: Optional[str] = None
    ) -> List[ActiveSpellEffect]:
        """Dispel effects on an entity.

        Args:
            entity_id: Entity to dispel effects from
            spell_id: Optional specific spell to dispel (all if None)

        Returns:
            List of dispelled effects
        """
        removed = []
        effect_ids = list(self._by_target.get(entity_id, []))

        for effect_id in effect_ids:
            effect = self._effects.get(effect_id)
            if effect is None:
                continue

            if spell_id is None or effect.spell_id == spell_id:
                dispelled = self.remove_effect(effect_id)
                if dispelled:
                    removed.append(dispelled)

        return removed

    # ==========================================================================
    # SERIALIZATION
    # ==========================================================================

    def get_all_effects(self) -> List[ActiveSpellEffect]:
        """Get all active effects."""
        return list(self._effects.values())

    def __len__(self) -> int:
        """Return number of active effects."""
        return len(self._effects)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "effects": [effect.to_dict() for effect in self._effects.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DurationTracker':
        """Deserialize from dictionary."""
        tracker = cls()
        for effect_data in data.get("effects", []):
            effect = ActiveSpellEffect.from_dict(effect_data)
            tracker.add_effect(effect)
        return tracker


# ==============================================================================
# FACTORY FUNCTION
# ==============================================================================

def create_effect(
    spell_id: str,
    spell_name: str,
    caster_id: str,
    target_id: str,
    duration_rounds: int,
    concentration: bool = False,
    condition: Optional[str] = None,
    turn: int = 0,
) -> ActiveSpellEffect:
    """Factory function to create an ActiveSpellEffect.

    Args:
        spell_id: ID of the spell
        spell_name: Display name of the spell
        caster_id: Entity that cast the spell
        target_id: Entity receiving the effect
        duration_rounds: Duration in rounds (-1 = permanent)
        concentration: Whether effect requires concentration
        condition: Optional condition name
        turn: Turn number when applied

    Returns:
        New ActiveSpellEffect
    """
    return ActiveSpellEffect(
        effect_id=str(uuid.uuid4()),
        spell_id=spell_id,
        spell_name=spell_name,
        caster_id=caster_id,
        target_id=target_id,
        rounds_remaining=duration_rounds,
        concentration=concentration,
        condition_applied=condition,
        turn_applied=turn,
    )
