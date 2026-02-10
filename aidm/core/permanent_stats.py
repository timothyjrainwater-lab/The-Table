"""SKR-002 Phase 3: Permanent Stat Modification Kernel (Algorithm Implementation)

BINDING CONSTRAINTS:
- Event sourcing mandatory (all mutations via events)
- Deterministic recalculation order (SKR-002 §5.2)
- No RNG consumption (SKR-002 INV-12)
- Separation from CP-16 temporary modifiers (SKR-002 INV-3)
- Derived stats recalculate atomically (SKR-002 INV-5)

This module implements the permanent stat modification layer separate from temporary
modifiers (CP-16). See SKR-002-DESIGN-v1.0.md for full specification.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aidm.schemas.permanent_stats import (
    Ability,
    AbilityScoreDeathEvent,
    DerivedStatsRecalculatedEvent,
    PermanentModifierTotals,
    PermanentModifierType,
    PermanentStatModifiedEvent,
    PermanentStatModifiers,
    PermanentStatRestoredEvent,
)


def apply_permanent_modifier(
    entity_state: Dict[str, Any],
    ability: Ability,
    modifier_type: PermanentModifierType,
    amount: int,
    source: str,
    reversible: bool = True,
) -> List[Dict[str, Any]]:
    """Apply a permanent stat modifier and emit events.

    Args:
        entity_state: Current entity state (must contain 'entity_id', 'base_stats',
                      'permanent_stat_modifiers')
        ability: The ability to modify (STR/DEX/CON/INT/WIS/CHA)
        modifier_type: DRAIN (negative) or INHERENT (positive)
        amount: Modifier amount (must match sign of modifier_type)
        source: Source of the modification (e.g., "shadow_strength_drain")
        reversible: Whether this modification can be reversed (default True)

    Returns:
        List of events: [permanent_stat_modified, derived_stats_recalculated, ...]
                       May include hp_changed if HP max drops below current HP
                       May include ability_score_death if effective score reaches 0

    Raises:
        ValueError: If amount sign doesn't match modifier_type, or if entity_state invalid

    SKR-002 References:
        - §3.1: Modifier types (drain/inherent)
        - §4.1-4.5: Event flows
        - INV-4: Effective score calculation
        - INV-6: Ability score floor is 0 (death trigger)
        - INV-10: Event ordering (source → derived → HP clamp → death)
    """
    entity_id = entity_state["entity_id"]
    base_stats = entity_state.get("base_stats", {})
    perm_mods = entity_state.get("permanent_stat_modifiers", {})

    # Convert to schema if needed
    if not isinstance(perm_mods, PermanentStatModifiers):
        perm_mods = PermanentStatModifiers.from_dict(perm_mods)

    # Validate amount sign matches modifier_type
    if modifier_type == PermanentModifierType.DRAIN and amount >= 0:
        raise ValueError("DRAIN amount must be negative")
    if modifier_type == PermanentModifierType.INHERENT and amount <= 0:
        raise ValueError("INHERENT amount must be positive")

    # Get current effective score (before modification)
    old_effective_score = calculate_effective_ability_score(
        entity_state, ability
    )

    # Apply modifier to appropriate field
    ability_str = ability.value if hasattr(ability, "value") else ability
    current_mods = getattr(perm_mods, ability_str)

    if modifier_type == PermanentModifierType.DRAIN:
        new_drain = current_mods.drain + amount
    else:
        new_drain = current_mods.drain

    if modifier_type == PermanentModifierType.INHERENT:
        new_inherent = current_mods.inherent + amount
    else:
        new_inherent = current_mods.inherent

    # Update permanent modifiers
    new_mods_dict = perm_mods.to_dict()
    new_mods_dict[ability_str] = {
        "drain": new_drain,
        "inherent": new_inherent,
    }
    entity_state["permanent_stat_modifiers"] = new_mods_dict

    # Calculate new effective score
    new_effective_score = calculate_effective_ability_score(
        entity_state, ability
    )

    # Event 1: permanent_stat_modified
    events = []
    mod_event = PermanentStatModifiedEvent(
        event_type="permanent_stat_modified",
        entity_id=entity_id,
        ability=ability,
        modifier_type=modifier_type,
        amount=amount,
        source=source,
        reversible=reversible,
    )
    events.append(mod_event.to_dict())

    # Event 2: derived_stats_recalculated (if effective score changed)
    if new_effective_score != old_effective_score:
        recalc_event = _emit_derived_stats_recalculated(
            entity_state,
            ability,
            old_effective_score,
            new_effective_score,
        )
        events.append(recalc_event.to_dict())

        # Event 3: hp_changed (if CON changed and HP max dropped below current HP)
        if ability_str == "con":
            hp_events = _check_hp_max_clamp(entity_state, recalc_event.hp_max_new)
            events.extend(hp_events)

    # Event 4: ability_score_death (if effective score reached 0)
    if new_effective_score <= 0:
        death_event = AbilityScoreDeathEvent(
            event_type="ability_score_death",
            entity_id=entity_id,
            ability=ability,
            final_score=0,  # SKR-002 INV-6: floor is 0, not negative
            cause=source,
        )
        events.append(death_event.to_dict())

    return events


def restore_permanent_modifier(
    entity_state: Dict[str, Any],
    ability: Ability,
    amount_to_remove: int,
    source: str,
) -> List[Dict[str, Any]]:
    """Restore (remove) permanent drain from an ability.

    Restoration can only remove DRAIN, never INHERENT bonuses (SKR-002 INV-9).

    Args:
        entity_state: Current entity state
        ability: The ability to restore
        amount_to_remove: Amount of drain to remove (must be positive)
        source: Source of the restoration (e.g., "restoration_spell")

    Returns:
        List of events: [permanent_stat_restored, derived_stats_recalculated, ...]

    Raises:
        ValueError: If amount_to_remove is not positive

    SKR-002 References:
        - §4.3: Restoration event flow
        - §6.3: Restoration exceeding drain (capped)
        - INV-9: Restoration cannot exceed base
    """
    if amount_to_remove <= 0:
        raise ValueError("amount_to_remove must be positive")

    entity_id = entity_state["entity_id"]
    perm_mods = entity_state.get("permanent_stat_modifiers", {})

    if not isinstance(perm_mods, PermanentStatModifiers):
        perm_mods = PermanentStatModifiers.from_dict(perm_mods)

    ability_str = ability.value if hasattr(ability, "value") else ability
    current_mods = getattr(perm_mods, ability_str)

    # Get current effective score (before restoration)
    old_effective_score = calculate_effective_ability_score(
        entity_state, ability
    )

    # Cap restoration at total drain (cannot boost above base + inherent)
    actual_removed = min(amount_to_remove, abs(current_mods.drain))

    # Early return if no drain to remove
    events = []
    if actual_removed == 0:
        # No restoration needed - emit no events
        return events

    new_drain = current_mods.drain + actual_removed  # drain is negative, so add

    # Update permanent modifiers
    new_mods_dict = perm_mods.to_dict()
    new_mods_dict[ability_str] = {
        "drain": new_drain,
        "inherent": current_mods.inherent,
    }
    entity_state["permanent_stat_modifiers"] = new_mods_dict

    # Calculate new effective score
    new_effective_score = calculate_effective_ability_score(
        entity_state, ability
    )

    # Event 1: permanent_stat_restored
    restore_event = PermanentStatRestoredEvent(
        event_type="permanent_stat_restored",
        entity_id=entity_id,
        ability=ability,
        modifier_type=PermanentModifierType.DRAIN,
        amount_removed=actual_removed,
        source=source,
    )
    events.append(restore_event.to_dict())

    # Event 2: derived_stats_recalculated (if effective score changed)
    if new_effective_score != old_effective_score:
        recalc_event = _emit_derived_stats_recalculated(
            entity_state,
            ability,
            old_effective_score,
            new_effective_score,
        )
        events.append(recalc_event.to_dict())

        # Note: HP max increase does NOT automatically heal (SKR-002 §4.5)

    return events


def calculate_effective_ability_score(
    entity_state: Dict[str, Any],
    ability: Ability,
) -> int:
    """Calculate effective ability score (base + permanent + temporary).

    Args:
        entity_state: Current entity state
        ability: The ability to calculate

    Returns:
        Effective ability score (floored at 0)

    SKR-002 References:
        - INV-4: Effective score = base + permanent + temporary
        - INV-6: Ability score floor is 0
    """
    ability_str = ability.value if hasattr(ability, "value") else ability

    # Base score
    base_stats = entity_state.get("base_stats", {})
    base_score = base_stats.get(ability_str, 10)

    # Permanent modifiers
    perm_mods = entity_state.get("permanent_stat_modifiers", {})
    if not isinstance(perm_mods, PermanentStatModifiers):
        perm_mods = PermanentStatModifiers.from_dict(perm_mods)

    current_mods = getattr(perm_mods, ability_str)
    perm_total = current_mods.drain + current_mods.inherent

    # Temporary modifiers (CP-16 integration - placeholder)
    # Phase 3: We do NOT implement CP-16 integration yet, just compute permanent
    temp_total = 0  # TODO: Integrate with CP-16 when available

    # Effective score (floored at 0)
    effective = base_score + perm_total + temp_total
    return max(0, effective)


def _emit_derived_stats_recalculated(
    entity_state: Dict[str, Any],
    ability: Ability,
    old_effective_score: int,
    new_effective_score: int,
) -> DerivedStatsRecalculatedEvent:
    """Emit derived_stats_recalculated event.

    Recalculates HP max, AC, saves, etc. in deterministic order (SKR-002 §5.2).

    Args:
        entity_state: Current entity state
        ability: The ability that changed
        old_effective_score: Previous effective score
        new_effective_score: New effective score

    Returns:
        DerivedStatsRecalculatedEvent

    SKR-002 References:
        - §5.2: Recalculation order (HP max, AC, saves, attack, skills)
        - INV-5: Derived stats recalculate atomically
    """
    entity_id = entity_state["entity_id"]
    ability_str = ability.value if hasattr(ability, "value") else ability

    # Recalculate derived stats in deterministic order
    recalculated_stats = []
    hp_max_old = None
    hp_max_new = None

    # Phase 1: HP max (if CON changed)
    if ability_str == "con":
        hp_max_old = _calculate_hp_max(entity_state, old_effective_score)
        hp_max_new = _calculate_hp_max(entity_state, new_effective_score)
        entity_state["hp_max"] = hp_max_new
        recalculated_stats.append("hp_max")

    # Phase 2: AC (if DEX changed)
    if ability_str == "dex":
        recalculated_stats.append("ac")
        # TODO: Full AC recalculation when AC system available

    # Phase 3: Saves (if CON/DEX/WIS changed)
    if ability_str == "con":
        recalculated_stats.append("fortitude_save")
    if ability_str == "dex":
        recalculated_stats.append("reflex_save")
    if ability_str == "wis":
        recalculated_stats.append("will_save")

    # Phase 4: Attack bonuses (if STR/DEX changed)
    if ability_str == "str":
        recalculated_stats.append("melee_attack")
        recalculated_stats.append("damage")
    if ability_str == "dex":
        recalculated_stats.append("ranged_attack")

    # Phase 5: Skills (all abilities affect some skills)
    recalculated_stats.append("skills")

    return DerivedStatsRecalculatedEvent(
        event_type="derived_stats_recalculated",
        entity_id=entity_id,
        ability_affected=ability,
        old_effective_score=old_effective_score,
        new_effective_score=new_effective_score,
        hp_max_old=hp_max_old,
        hp_max_new=hp_max_new,
        recalculated_stats=recalculated_stats,
    )


def _calculate_hp_max(entity_state: Dict[str, Any], con_score: int) -> int:
    """Calculate HP max based on CON score.

    Args:
        entity_state: Current entity state
        con_score: Constitution score

    Returns:
        HP max

    SKR-002 Reference: §5.2 Phase 1 (HP max recalculation)
    """
    # CON modifier
    con_modifier = (con_score - 10) // 2

    # Base HP (from HD rolls)
    # TODO: Read from entity state when HP system available
    # For now, assume 8 HP per HD (average d8)
    hd_count = entity_state.get("hd_count", 1)
    base_hp = entity_state.get("base_hp", hd_count * 8)

    # HP max = base + (CON mod × HD count)
    hp_max = base_hp + (con_modifier * hd_count)

    return max(1, hp_max)  # Minimum 1 HP


def _check_hp_max_clamp(
    entity_state: Dict[str, Any],
    new_hp_max: Optional[int],
) -> List[Dict[str, Any]]:
    """Check if current HP exceeds new HP max and emit hp_changed event if needed.

    Args:
        entity_state: Current entity state
        new_hp_max: New HP max (or None if not CON-related)

    Returns:
        List of events (hp_changed if clamping occurred, else empty)

    SKR-002 References:
        - §4.5: CON drain with HP max reduction
        - INV-7: HP max cannot exceed current HP
    """
    if new_hp_max is None:
        return []

    current_hp = entity_state.get("hp_current", new_hp_max)

    if current_hp > new_hp_max:
        # Clamp current HP to new max
        entity_state["hp_current"] = new_hp_max

        # Emit hp_changed event
        hp_event = {
            "event_type": "hp_changed",
            "entity_id": entity_state["entity_id"],
            "old_hp": current_hp,
            "new_hp": new_hp_max,
            "cause": "hp_max_reduction",
        }
        return [hp_event]

    return []
