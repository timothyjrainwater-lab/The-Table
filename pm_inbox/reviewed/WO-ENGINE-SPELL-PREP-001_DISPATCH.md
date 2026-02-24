# WO-ENGINE-SPELL-PREP-001 — Spell Preparation Intent (PHB p.177-178)

**Issued:** 2026-02-24
**Authority:** Thunder approval (parallel backend sprint)
**Gate:** ENGINE-SPELL-PREP (new gate, defined below)
**Parallel-safe:** Yes — new file `aidm/core/spell_prep_resolver.py` + routing in `play_loop.py`. No overlap with CONCENTRATION-001 or GRAPPLE-PIN-001.

---

## 1. Target Lock

`rest_resolver.py` currently resets `SPELLS_PREPARED` to the full `SPELLS_KNOWN` list after rest. PHB 3.5e p.177 requires:
- **Wizards:** prepare from spellbook, limited to `INT_mod + caster_level` spells per level
- **Clerics/Druids:** pray for spells from full class list, limited to slots available per level
- **Paladin/Ranger:** prepare from class list when slots become available at class level 4+

The current rest behavior (defaults to max preparation) is a generous stub — functionally correct for "rest and be ready", but does not allow the player/DM to choose which specific spells the wizard has prepared. This matters for tactical play: a wizard must choose *before* combat whether they prepared `Fireball` or `Fly`.

**Done means:** A new `PrepareSpellsIntent` is added. Players/DM can submit it after a rest to choose the wizard's active prepared list, validated against PHB prep count limits. Gate ENGINE-SPELL-PREP 12/12.

---

## 2. PHB 3.5e Rules (p.177-178)

### Wizard (p.178)
> "A wizard prepares her spells by studying her spellbook. She can prepare any spell from her spellbook; she is not limited to a subset of her known spells the way a cleric is. A wizard may prepare a number of spells of each level up to the maximum she can cast per day (her slots for that level). She may also prepare spells of a level up to the number of times she can cast spells per day, but she must leave room for any metamagic spell slots she might want."

**Simplified PHB rule for prep count:** A wizard can prepare any number of spells up to her slots for that level (including bonus slots from high INT). She may prepare the same spell multiple times if she has multiple slots of that level.

> "A wizard may prepare a number of spells of each level equal to the number of times she can cast spells of that level (her spells per day)."

So prep limit per level = `SPELL_SLOTS[level]` (total slots including INT bonus). Not `INT_mod + caster_level` as the summary said — that's a simplification. The actual limit is the slot count.

### Cleric/Druid (p.177)
> "A cleric may prepare any spell from the cleric spell list, as long as she can cast spells of that level. She may prepare any spell she knows (all cleric spells are 'known'), up to the maximum number of spells she can cast per day for each level."

Prep limit per level = `SPELL_SLOTS[level]`.

### Paladin/Ranger
Gain spells at level 4+. Same slot-based limit. Prepared casters. Can prepare any class spell.

**Spontaneous casters (bard, sorcerer):** `SPELLS_PREPARED` is not meaningful — they cast from `SPELLS_KNOWN`. `PrepareSpellsIntent` does not apply to spontaneous casters.

---

## 3. Authoritative Validation Rules

```
For each requested spell_level L in preparation_request:
  max_for_level = entity[EF.SPELL_SLOTS][L]          (total slots including INT bonus)
  requested_count[L] = len(preparation_request[L])
  REJECT if requested_count[L] > max_for_level

  For each spell_id in preparation_request[L]:
    REJECT if spell_id not in entity[EF.SPELLS_KNOWN][L]  (for wizard: spellbook)
    REJECT if spell.level != L                              (spell level must match slot level)
    # Same spell may appear multiple times up to max_for_level (PHB p.178 allows this)

Spontaneous caster check:
  REJECT if entity[EF.CASTER_CLASS] in SPONTANEOUS_CASTERS  (bard, sorcerer — no prep)
  Allow dual-caster: if CASTER_CLASS is spontaneous but CASTER_CLASS_2 is prepared, use _2 fields
```

**Cantrips (level 0):** Prepared casters have unlimited access to level 0 spells (orisons, cantrips). `PrepareSpellsIntent` may include level 0 but rejection check still applies: requested count ≤ `SPELL_SLOTS[0]`.

---

## 4. Implementation Spec

### 4.1 Add `PrepareSpellsIntent` to `aidm/schemas/intents.py`

```python
@dataclass
class PrepareSpellsIntent:
    """Intent to prepare spells after a rest. WO-ENGINE-SPELL-PREP-001.

    PHB p.177-178: Prepared casters (wizard, cleric, druid, paladin, ranger)
    choose which spells to prepare each day after a qualifying rest.

    preparation: Dict mapping spell_level (int) to list of spell_ids (str).
    Example:
        PrepareSpellsIntent(
            caster_id="wizard_pc",
            preparation={1: ["magic_missile", "magic_missile", "shield"], 2: ["scorching_ray"]}
        )

    The same spell_id may appear multiple times in a level's list — this consumes
    one slot per occurrence (PHB p.178: wizard may prepare same spell twice).
    """
    caster_id: str
    """Entity ID of the caster preparing spells."""

    preparation: Dict[int, List[str]]
    """Dict mapping spell level to list of spell_ids to prepare."""

    use_secondary: bool = False
    """True if preparing secondary caster class spells (dual-caster only)."""
```

### 4.2 Create `aidm/core/spell_prep_resolver.py`

```python
"""Spell preparation resolver. WO-ENGINE-SPELL-PREP-001.

Validates and applies PrepareSpellsIntent. Enforces PHB p.177-178 limits.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import PrepareSpellsIntent
from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.schemas.spell_definitions import SPELL_REGISTRY
from aidm.chargen.spellcasting import SPONTANEOUS_CASTERS


@dataclass
class SpellPrepResult:
    """Result of spell preparation."""
    success: bool
    error: str = ""   # set on failure
    prepared: Dict[int, List[str]] = None  # set on success


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
            payload={"caster_id": caster_id, "reason": "entity_not_found", "turn_index": turn_index},
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
    from copy import deepcopy
    entities = {k: deepcopy(v) for k, v in world_state.entities.items()}
    entities[caster_id][prepared_field] = deepcopy(intent.preparation)

    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat,
        narrative_context=world_state.narrative_context,
        scene_type=world_state.scene_type,
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

        # known spells for this level (may be empty for prepared casters who can access full class list)
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
```

### 4.3 Wire `PrepareSpellsIntent` in `play_loop.py`

In `execute_turn()`, in the intent routing block (after `RestIntent` routing):

```python
# WO-ENGINE-SPELL-PREP-001: Spell preparation intent
elif isinstance(combat_intent, PrepareSpellsIntent):
    from aidm.core.spell_prep_resolver import resolve_prepare_spells
    prep_events, world_state, narration = resolve_prepare_spells(
        intent=combat_intent,
        world_state=world_state,
        next_event_id=current_event_id,
        timestamp=timestamp,
        turn_index=turn_ctx.turn_index,
    )
    events.extend(prep_events)
    current_event_id += len(prep_events)
```

Also add `PrepareSpellsIntent` to the RNG-exempt list (it uses no RNG):

```python
if rng is None and not isinstance(
    combat_intent, (SummonCompanionIntent, RestIntent, PrepareSpellsIntent)
):
    raise ValueError("RNG manager required for combat intent resolution")
```

Add `PrepareSpellsIntent` to the `intent_actor_id` routing block (actor declares):

```python
elif isinstance(combat_intent, PrepareSpellsIntent):
    intent_actor_id = turn_ctx.actor_id
```

### 4.4 Amend `rest_resolver.py` — Add Stub Note

No code change required. `rest_resolver.py` continues to reset `SPELLS_PREPARED` to `SPELLS_KNOWN` as a default (all-spells-available after rest). The `PrepareSpellsIntent` is issued *after* rest to narrow the prepared list. This is correct behavior: rest grants maximum theoretical access; player then selects the specific subset.

---

## 5. Event Types

| Event type | Emitted when |
|------------|-------------|
| `spells_prepared` | Preparation validated and applied; payload includes full preparation dict |
| `spell_prep_failed` | Validation failed; payload includes error list and reason code |

---

## 6. Gate Spec

**Gate name:** `ENGINE-SPELL-PREP`
**Test file:** `tests/test_engine_spell_prep_gate.py`

| # | Test | Check |
|---|------|-------|
| SP-01 | Wizard prepares 2 level-1 spells, has 2 slots → `spells_prepared` event, `SPELLS_PREPARED` updated | event emitted; entity `spells_prepared[1]` == chosen list |
| SP-02 | Wizard prepares 3 level-1 spells, has 2 slots → `spell_prep_failed` with `validation_failed` | error contains slot count message |
| SP-03 | Wizard prepares spell not in spellbook → `spell_prep_failed` | error contains "not in spellbook" |
| SP-04 | Wizard prepares `magic_missile` (level 1) under level 2 → `spell_prep_failed` | error contains level mismatch |
| SP-05 | Sorcerer (spontaneous) issues `PrepareSpellsIntent` → `spell_prep_failed`, reason `spontaneous_caster_no_prep` | reason field checked |
| SP-06 | Cleric issues `PrepareSpellsIntent` with valid spells → `spells_prepared` event | cleric is prepared caster, succeeds |
| SP-07 | Druid issues `PrepareSpellsIntent` → `spells_prepared` event | druid is prepared caster, succeeds |
| SP-08 | `PrepareSpellsIntent` uses no RNG — passes with `rng=None` | no `ValueError` raised |
| SP-09 | Dual-caster wizard/sorcerer: `use_secondary=True` targets wizard fields (`SPELLS_PREPARED_2`) | `spells_prepared_2` updated, not `spells_prepared` |
| SP-10 | Same spell prepared twice in same level (within slot limit) → succeeds (PHB p.178 allows) | `spells_prepared[1] == ["magic_missile", "magic_missile"]` |
| SP-11 | `PrepareSpellsIntent` for non-existent entity → `spell_prep_failed`, reason `entity_not_found` | graceful error |
| SP-12 | Zero regressions on ENGINE-REST-001 gate (12/12) and existing spell slot tests | full suite pass |

**Test count target:** 12 checks → Gate `ENGINE-SPELL-PREP` 12/12.

---

## 7. What This WO Does NOT Do

- Does not add a "you must re-prepare after rest" enforcement (prep is opt-in, not mandatory)
- Does not implement metamagic slot augmentation (separate scope)
- Does not add per-class spell access tables for cleric/druid beyond `SPELLS_KNOWN` (those lists are established at chargen)
- Does not enforce "must have rested to prepare" (preparation can be issued any time — correct if used in sequence with rest, unchecked if not)
- Does not add the "INT_mod + caster_level additional free low-level spells" rule (PHB edge case — not standard play impact)

---

## 8. Preflight

```bash
cd f:/DnD-3.5
python -m pytest tests/test_engine_spell_prep_gate.py -v
# SP-01 through SP-12 must pass.
python -m pytest tests/ -x --tb=short
# Zero new regressions.
```
