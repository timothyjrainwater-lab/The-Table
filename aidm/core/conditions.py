"""Condition query system for CP-16 — Conditions & Status Effects Kernel.

Provides deterministic modifier queries for combat resolution.
NO ENFORCEMENT LOGIC IN THIS MODULE.

CP-16 MINIMAL SCOPE (OPTION A):
- Conditions are data-only descriptors stored in WorldState
- Resolvers query modifiers via get_condition_modifiers()
- No enforcement of movement, actions, or legality
- All enforcement deferred to CP-17+

Conditions describe mechanical truth but do NOT enforce legality.
"""

from typing import Dict, Any, Optional, List
from aidm.core.state import WorldState
from aidm.schemas.conditions import ConditionInstance, ConditionModifiers


def get_condition_modifiers(
    world_state: WorldState,
    actor_id: str,
    context: Optional[str] = None
) -> ConditionModifiers:
    """Query aggregate condition modifiers for an actor.

    Sums all numeric modifiers from active conditions.
    Boolean flags are OR'd (any condition sets flag → flag is True).

    Args:
        world_state: Current world state
        actor_id: Entity ID to query
        context: Optional context hint (e.g., "melee_attack", "ranged_attack")

    Returns:
        ConditionModifiers with aggregate values

    CP-16 MINIMAL SCOPE:
    - No stacking logic beyond simple summation
    - No suppression or immunity (deferred to CP-17+)
    - No context-specific filtering (e.g., prone AC vs melee vs ranged)
    - Context parameter reserved for CP-17+ refinements

    CP-17 EXTENSION:
    - Saving throw modifiers aggregated (Fort/Ref/Will)
    """
    entity = world_state.entities.get(actor_id)
    if entity is None:
        # Fail-closed: missing entity returns zero modifiers
        return ConditionModifiers()

    conditions_data = entity.get("conditions", {})
    if not conditions_data:
        # No conditions: return zero modifiers
        return ConditionModifiers()

    # Aggregate modifiers
    total_ac = 0
    total_attack = 0
    total_damage = 0
    total_dex = 0
    total_fort_save = 0  # CP-17 extension
    total_ref_save = 0   # CP-17 extension
    total_will_save = 0  # CP-17 extension

    # Boolean flags (OR logic)
    any_movement_prohibited = False
    any_actions_prohibited = False
    any_standing_triggers_aoo = False
    any_auto_hit_if_helpless = False
    any_loses_dex_to_ac = False

    # Sum all condition modifiers
    for condition_id, condition_dict in conditions_data.items():
        condition = ConditionInstance.from_dict(condition_dict)
        mods = condition.modifiers

        total_ac += mods.ac_modifier
        total_attack += mods.attack_modifier
        total_damage += mods.damage_modifier
        total_dex += mods.dex_modifier
        total_fort_save += mods.fort_save_modifier  # CP-17 extension
        total_ref_save += mods.ref_save_modifier    # CP-17 extension
        total_will_save += mods.will_save_modifier  # CP-17 extension

        any_movement_prohibited = any_movement_prohibited or mods.movement_prohibited
        any_actions_prohibited = any_actions_prohibited or mods.actions_prohibited
        any_standing_triggers_aoo = any_standing_triggers_aoo or mods.standing_triggers_aoo
        any_auto_hit_if_helpless = any_auto_hit_if_helpless or mods.auto_hit_if_helpless
        any_loses_dex_to_ac = any_loses_dex_to_ac or mods.loses_dex_to_ac

    return ConditionModifiers(
        ac_modifier=total_ac,
        attack_modifier=total_attack,
        damage_modifier=total_damage,
        dex_modifier=total_dex,
        fort_save_modifier=total_fort_save,  # CP-17 extension
        ref_save_modifier=total_ref_save,    # CP-17 extension
        will_save_modifier=total_will_save,  # CP-17 extension
        movement_prohibited=any_movement_prohibited,
        actions_prohibited=any_actions_prohibited,
        standing_triggers_aoo=any_standing_triggers_aoo,
        auto_hit_if_helpless=any_auto_hit_if_helpless,
        loses_dex_to_ac=any_loses_dex_to_ac
    )


def apply_condition(
    world_state: WorldState,
    actor_id: str,
    condition: ConditionInstance
) -> WorldState:
    """Apply a condition to an entity (pure function, returns new state).

    CP-16 SCOPE:
    - No stacking logic (identical condition types overwrite)
    - No duration tracking (manual removal only)
    - No automatic expiration (deferred to CP-17+)

    Args:
        world_state: Current world state
        actor_id: Entity to apply condition to
        condition: Condition instance to apply

    Returns:
        Updated WorldState with condition applied

    Raises:
        ValueError: If actor_id not found in entities
    """
    if actor_id not in world_state.entities:
        raise ValueError(f"Cannot apply condition: actor {actor_id} not found in world state")

    # Deep copy entities
    entities = world_state.entities.copy()
    entity = entities[actor_id].copy()

    # Get or create conditions dict
    conditions = entity.get("conditions", {}).copy()

    # Use condition type as key (overwrites existing condition of same type)
    condition_id = condition.condition_type.value
    conditions[condition_id] = condition.to_dict()

    # Update entity
    entity["conditions"] = conditions
    entities[actor_id] = entity

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat
    )


def remove_condition(
    world_state: WorldState,
    actor_id: str,
    condition_type: str
) -> WorldState:
    """Remove a condition from an entity (pure function, returns new state).

    Args:
        world_state: Current world state
        actor_id: Entity to remove condition from
        condition_type: Condition type to remove (e.g., "prone", "grappled")

    Returns:
        Updated WorldState with condition removed

    Raises:
        ValueError: If actor_id not found in entities
    """
    if actor_id not in world_state.entities:
        raise ValueError(f"Cannot remove condition: actor {actor_id} not found in world state")

    # Deep copy entities
    entities = world_state.entities.copy()
    entity = entities[actor_id].copy()

    # Get conditions dict
    conditions = entity.get("conditions", {}).copy()

    # Remove condition if present (no error if not present)
    if condition_type in conditions:
        del conditions[condition_type]

    # Update entity
    entity["conditions"] = conditions
    entities[actor_id] = entity

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat
    )


def has_condition(
    world_state: WorldState,
    actor_id: str,
    condition_type: str
) -> bool:
    """Check if an entity has a specific condition.

    Args:
        world_state: Current world state
        actor_id: Entity to check
        condition_type: Condition type to check for

    Returns:
        True if entity has condition, False otherwise
    """
    entity = world_state.entities.get(actor_id)
    if entity is None:
        return False

    conditions = entity.get("conditions", {})
    return condition_type in conditions
