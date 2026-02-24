"""Spell preparation resolver. WO-ENGINE-SPELL-PREP-001.

Validates and applies PrepareSpellsIntent. Enforces PHB p.177-178 limits.

Prepared casters (wizard, cleric, druid, paladin, ranger) choose which
spells to prepare each day after a qualifying rest. Spontaneous casters
(bard, sorcerer) are rejected — they cast from SPELLS_KNOWN with no prep.

Prep count per level = SPELL_SLOTS[level] (includes INT/WIS bonus slots).
The same spell_id may appear multiple times within a level (consumes one
slot per occurrence).
"""

from copy import deepcopy
from typing import Dict, List, Tuple

from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import PrepareSpellsIntent
from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.schemas.spell_definitions import SPELL_REGISTRY
from aidm.chargen.spellcasting import SPONTANEOUS_CASTERS


def resolve_prepare_spells(
    intent: PrepareSpellsIntent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
    turn_index: int,
) -> Tuple[List[Event], WorldState, str]:
    """Validate and apply spell preparation.

    Args:
        intent: The preparation intent
        world_state: Current world state
        next_event_id: Next event ID
        timestamp: Event timestamp
        turn_index: Current turn index

    Returns:
        Tuple of (events, updated_world_state, narration_token)
    """
    events = []
    current_event_id = next_event_id

    caster_id = intent.caster_id
    actor = world_state.entities.get(caster_id)
    if actor is None:
        return [Event(
            event_id=current_event_id,
            event_type="spell_prep_failed",
            timestamp=timestamp,
            payload={
                "caster_id": caster_id,
                "reason": "entity_not_found",
                "turn_index": turn_index,
            },
        )], world_state, "spell_prep_failed"

    # Determine which slot/known fields to use
    if intent.use_secondary:
        caster_class = actor.get(EF.CASTER_CLASS_2, "")
        spell_slots: Dict = actor.get(EF.SPELL_SLOTS_2, {})
        spells_known: Dict = actor.get(EF.SPELLS_KNOWN_2, {})
        prepared_field = EF.SPELLS_PREPARED_2
    else:
        caster_class = actor.get(EF.CASTER_CLASS, "")
        spell_slots = actor.get(EF.SPELL_SLOTS, {})
        spells_known = actor.get(EF.SPELLS_KNOWN, {})
        prepared_field = EF.SPELLS_PREPARED

    # Reject spontaneous casters
    if caster_class in SPONTANEOUS_CASTERS:
        return [Event(
            event_id=current_event_id,
            event_type="spell_prep_failed",
            timestamp=timestamp,
            payload={
                "caster_id": caster_id,
                "reason": "spontaneous_caster_no_prep",
                "caster_class": caster_class,
                "turn_index": turn_index,
            },
        )], world_state, "spell_prep_failed"

    # Validate preparation dict
    errors = _validate_preparation(intent.preparation, spell_slots, spells_known)
    if errors:
        return [Event(
            event_id=current_event_id,
            event_type="spell_prep_failed",
            timestamp=timestamp,
            payload={
                "caster_id": caster_id,
                "reason": "validation_failed",
                "errors": errors,
                "turn_index": turn_index,
            },
        )], world_state, "spell_prep_failed"

    # Apply preparation
    entities = {k: deepcopy(v) for k, v in world_state.entities.items()}
    entities[caster_id][prepared_field] = deepcopy(intent.preparation)

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat,
    )

    events.append(Event(
        event_id=current_event_id,
        event_type="spells_prepared",
        timestamp=timestamp,
        payload={
            "caster_id": caster_id,
            "caster_class": caster_class,
            "preparation": intent.preparation,
            "turn_index": turn_index,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 178}],
    ))

    return events, updated_state, "spells_prepared"


def _validate_preparation(
    preparation: Dict[int, List[str]],
    spell_slots: Dict,
    spells_known: Dict,
) -> List[str]:
    """Validate preparation request against slot limits and known spells.

    Returns list of error strings. Empty list = valid.
    """
    errors = []
    for level, spell_list in preparation.items():
        level_int = int(level)
        # Convert slot keys to int for comparison (JSON may produce str keys)
        slots_for_level = spell_slots.get(level_int, spell_slots.get(str(level_int), 0))
        if slots_for_level == 0:
            errors.append(f"Level {level_int}: no slots available")
            continue

        if len(spell_list) > slots_for_level:
            errors.append(
                f"Level {level_int}: requested {len(spell_list)} spells but only {slots_for_level} slots available"
            )

        # known spells for this level (may be empty for clerics/druids with full class list access)
        known_for_level = spells_known.get(level_int, spells_known.get(str(level_int), []))
        if known_for_level:  # Only validate if known list is populated (wizard with spellbook)
            for spell_id in spell_list:
                if spell_id not in known_for_level:
                    errors.append(f"Level {level_int}: '{spell_id}' not in spellbook/known list")

        # Validate spell_id exists in SPELL_REGISTRY and is correct level
        for spell_id in spell_list:
            spell_def = SPELL_REGISTRY.get(spell_id)
            if spell_def is None:
                errors.append(f"Level {level_int}: unknown spell '{spell_id}'")
            elif spell_def.level != level_int:
                errors.append(
                    f"'{spell_id}' is level {spell_def.level}, not level {level_int}"
                )

    return errors
