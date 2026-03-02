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

from copy import deepcopy
from typing import Dict, Any, Optional, List, Tuple
import logging
from aidm.core.state import WorldState
from aidm.schemas.conditions import ConditionInstance, ConditionModifiers
from aidm.schemas.entity_fields import EF

_log = logging.getLogger(__name__)

# Mapping from condition_id string → factory function name in aidm.schemas.conditions.
# Used by _get_modifiers_for_condition_type() to resolve empty-dict conditions.
_CONDITION_FACTORY_NAMES: Dict[str, str] = {
    "flat_footed": "create_flat_footed_condition",
    "prone": "create_prone_condition",
    "grappled": "create_grappled_condition",
    "grappling": "create_grappling_condition",
    "helpless": "create_helpless_condition",
    "stunned": "create_stunned_condition",
    "dazed": "create_dazed_condition",
    "shaken": "create_shaken_condition",
    "sickened": "create_sickened_condition",
    "frightened": "create_frightened_condition",
    "panicked": "create_panicked_condition",
    "nauseated": "create_nauseated_condition",
    "fatigued": "create_fatigued_condition",
    "exhausted": "create_exhausted_condition",
    "paralyzed": "create_paralyzed_condition",
}


def _get_modifiers_for_condition_type(condition_id: str) -> Optional[ConditionModifiers]:
    """Return canonical ConditionModifiers for a known condition type.

    WO-ENGINE-AI-WO4: Used to resolve conditions stored as empty-dict {}.
    Calls the appropriate create_XXX_condition() factory function to get canonical defaults.

    Returns None if condition_id is not a known condition type.
    """
    import aidm.schemas.conditions as _conds
    factory_name = _CONDITION_FACTORY_NAMES.get(condition_id)
    if factory_name is None:
        return None
    factory = getattr(_conds, factory_name, None)
    if factory is None:
        return None
    try:
        instance = factory("_empty_dict_default", 0)
        return instance.modifiers
    except Exception:
        return None


def _normalize_condition_dict(condition_id: str, condition_dict: dict) -> dict:
    """Return condition_dict unchanged (for non-empty) or a sentinel for empty dicts.

    WO-ENGINE-AI-WO4: Documents the empty-dict case. Callers that need modifiers
    for empty-dict conditions should use _get_modifiers_for_condition_type() instead.
    This function is kept for test-verifiability.

    NOTE (WO-ENGINE-CONDITIONS-LEGACY-FIX-001): test-verifiability only — not called
    from live code paths. Live code uses get_condition_modifiers() which now raises
    ValueError on non-dict conditions data.

    Args:
        condition_id: The condition key (e.g., "flat_footed")
        condition_dict: The raw dict value

    Returns:
        Original dict if non-empty; {"condition_type": condition_id} if empty.
    """
    if condition_dict == {}:
        return {"condition_type": condition_id}
    return condition_dict


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

    conditions_data = entity.get(EF.CONDITIONS, {})
    if not conditions_data:
        # No conditions: return zero modifiers
        return ConditionModifiers()

    # WO-ENGINE-CONDITIONS-LEGACY-FIX-001: Raise ValueError on non-dict conditions data.
    # Previously returned zero modifiers silently for list format — bugs went undetected.
    # Raises immediately so callers discover the format error at the point of failure.
    if not isinstance(conditions_data, dict):
        raise ValueError(
            f"get_condition_modifiers() requires a dict of {{condition_name: ConditionInstance}}, "
            f"got {type(conditions_data).__name__!r} for entity {actor_id!r}. "
            "Legacy list format ['condition'] is not supported. "
            "Use create_*_condition().to_dict() or build ConditionInstance directly."
        )

    # Aggregate modifiers
    total_ac = 0
    total_ac_melee = 0
    total_ac_ranged = 0
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
    any_aoo_blocked = False  # WO-ENGINE-GRAPPLE-CONDITION-ENFORCE-001

    # Sum all condition modifiers
    for condition_id, condition_dict in conditions_data.items():
        if not isinstance(condition_dict, dict):
            continue  # Skip malformed entries

        # WO-ENGINE-AI-WO4: Empty dict {} → condition present with default mechanics.
        # FINDING-ENGINE-FLAT-FOOTED-COND-FORMAT-001: {flat_footed: {}} was silently dropped.
        # Fix: use factory lookup to get canonical modifiers; bypass from_dict() for this case.
        if condition_dict == {}:
            mods = _get_modifiers_for_condition_type(condition_id)
            if mods is None:
                continue  # unknown condition type — no modifiers
        else:
            try:
                condition = ConditionInstance.from_dict(condition_dict)
                mods = condition.modifiers
            except (ValueError, KeyError):
                # Unknown condition type (e.g., spell buff labels like "mage_armor")
                # — no mechanical modifiers, skip aggregation
                continue

        total_ac += mods.ac_modifier
        total_ac_melee += mods.ac_modifier_melee
        total_ac_ranged += mods.ac_modifier_ranged
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
        any_aoo_blocked = any_aoo_blocked or mods.aoo_blocked  # WO-ENGINE-GRAPPLE-CONDITION-ENFORCE-001

    return ConditionModifiers(
        ac_modifier=total_ac,
        ac_modifier_melee=total_ac_melee,
        ac_modifier_ranged=total_ac_ranged,
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
        loses_dex_to_ac=any_loses_dex_to_ac,
        aoo_blocked=any_aoo_blocked  # WO-ENGINE-GRAPPLE-CONDITION-ENFORCE-001
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
    entities = deepcopy(world_state.entities)
    entity = entities[actor_id]

    # Get or create conditions dict
    conditions = entity.get(EF.CONDITIONS, {})

    # Use condition type as key (overwrites existing condition of same type)
    condition_id = condition.condition_type.value
    conditions[condition_id] = condition.to_dict()

    # Update entity
    entity[EF.CONDITIONS] = conditions
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
    entities = deepcopy(world_state.entities)
    entity = entities[actor_id]

    # Get conditions dict
    conditions = entity.get(EF.CONDITIONS, {})

    # Remove condition if present (no error if not present)
    if condition_type in conditions:
        del conditions[condition_type]

    # Update entity
    entity[EF.CONDITIONS] = conditions
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

    conditions = entity.get(EF.CONDITIONS, {})
    return condition_type in conditions


def tick_conditions(
    world_state: WorldState,
    events: List,
    current_event_id: int,
    timestamp: float,
) -> Tuple[WorldState, List, int]:
    """Decrement duration_rounds on timed conditions; remove expired ones.

    ARCH-TICK-001 two-pass protocol:
    - Pass 1: Collect conditions that will expire (duration_rounds decrements to <= 0).
              Decrement in-place on a deep copy of entities for non-expiring timed conditions.
    - Pass 2: Build new_entities from the deep copy, removing expired conditions,
              then emit condition_expired events.

    Args:
        world_state:      Current WorldState (not mutated).
        events:           Existing event list (extended in-place on the copy returned).
        current_event_id: Next event ID to use.
        timestamp:        Timestamp for emitted events.

    Returns:
        (new_world_state, new_events, new_current_event_id)
    """
    from aidm.core.event_log import Event

    # Deep-copy entities so we never mutate the caller's WorldState.
    entities_copy = deepcopy(world_state.entities)

    # ARCH-TICK-001 Pass 1 — decrement and collect expiries.
    # expiries: list of (entity_id, cond_type_str, source)
    expiries: List[Tuple[str, str, str]] = []

    for entity_id, entity in entities_copy.items():
        conditions = entity.get(EF.CONDITIONS, {})
        if not conditions:
            continue
        for cond_type_str, cond_dict in list(conditions.items()):
            if not isinstance(cond_dict, dict):
                continue
            dur = cond_dict.get("duration_rounds")
            if dur is None:
                # Permanent condition — skip.
                continue
            # Timed condition — decrement.
            new_dur = dur - 1
            if new_dur <= 0:
                # Mark for removal in Pass 2.
                source = cond_dict.get("source", "unknown")
                expiries.append((entity_id, cond_type_str, source))
            else:
                # Still alive — update the decremented value in the copy.
                cond_dict["duration_rounds"] = new_dur

    # ARCH-TICK-001 Pass 2 — remove expired conditions and emit events.
    new_events = list(events)

    for entity_id, cond_type_str, source in expiries:
        entity = entities_copy[entity_id]
        conditions = entity.get(EF.CONDITIONS, {})
        if cond_type_str in conditions:
            del conditions[cond_type_str]
        entity[EF.CONDITIONS] = conditions

        new_events.append(Event(
            event_id=current_event_id,
            event_type="condition_expired",
            timestamp=timestamp,
            payload={
                "entity_id": entity_id,
                "condition_type": cond_type_str,
                "source": source,
                "reason": "condition_tick",
            },
        ))
        current_event_id += 1

    new_world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities_copy,
        active_combat=world_state.active_combat,
    )

    return new_world_state, new_events, current_event_id
