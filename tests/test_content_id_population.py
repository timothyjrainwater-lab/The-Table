"""Tests for WO-CONTENT-ID-POPULATION.

Validates:
1. Every SpellDefinition in SPELL_REGISTRY has a non-None content_id
2. content_id follows the naming convention "spell.<name>_003"
3. spell_cast events emitted by the spell resolver include content_id in payload

WO-CONTENT-ID-POPULATION: Populate content_id on Spell Registry + Thread Through Event Payloads
"""

import re

from aidm.data.spell_definitions import SPELL_REGISTRY
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.core.spell_resolver import SpellCastIntent


# ==============================================================================
# TEST 1: All spells have content_id
# ==============================================================================


def test_all_spells_have_content_id():
    """Every SpellDefinition in SPELL_REGISTRY must have a non-None content_id."""
    missing = []
    for spell_id, spell_def in SPELL_REGISTRY.items():
        if spell_def.content_id is None:
            missing.append(spell_id)

    assert not missing, (
        f"{len(missing)} spell(s) missing content_id: {missing}"
    )


def test_content_id_naming_convention():
    """content_id must follow 'spell.<spell_id>_003' naming convention."""
    pattern = re.compile(r"^spell\.[a-z_]+_003$")
    violations = []
    for spell_id, spell_def in SPELL_REGISTRY.items():
        expected = f"spell.{spell_id}_003"
        if spell_def.content_id != expected:
            violations.append(
                f"{spell_id}: got '{spell_def.content_id}', expected '{expected}'"
            )
        if not pattern.match(spell_def.content_id or ""):
            violations.append(
                f"{spell_id}: content_id '{spell_def.content_id}' does not match pattern"
            )

    assert not violations, (
        f"{len(violations)} naming convention violation(s):\n"
        + "\n".join(violations)
    )


def test_spell_registry_count():
    """SPELL_REGISTRY should contain all 53 spells."""
    assert len(SPELL_REGISTRY) == 53, (
        f"Expected 53 spells, found {len(SPELL_REGISTRY)}"
    )


# ==============================================================================
# TEST 2: spell_cast events contain content_id
# ==============================================================================


def _make_combat_state() -> WorldState:
    """Create minimal combat state for spell cast testing."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "wizard": {
                EF.HP_CURRENT: 30,
                EF.HP_MAX: 30,
                EF.AC: 12,
                EF.TEAM: "party",
                EF.POSITION: Position(0, 0),
                EF.SAVE_FORT: 2,
                EF.SAVE_REF: 3,
                EF.SAVE_WILL: 6,
                "caster_level": 5,
                "spell_dc_base": 14,
            },
            "goblin": {
                EF.HP_CURRENT: 6,
                EF.HP_MAX: 6,
                EF.AC: 15,
                EF.TEAM: "monsters",
                EF.POSITION: Position(3, 3),
                EF.SAVE_FORT: 1,
                EF.SAVE_REF: 2,
                EF.SAVE_WILL: 0,
            },
        },
        active_combat={
            "round": 1,
            "initiative_order": ["wizard", "goblin"],
            "current_initiative_index": 0,
        },
    )


def test_spell_cast_event_contains_content_id():
    """spell_cast events emitted by the play loop must include content_id."""
    world_state = _make_combat_state()
    rng = RNGManager(master_seed=42)

    intent = SpellCastIntent(
        caster_id="wizard",
        spell_id="magic_missile",
        target_entity_id="goblin",
    )

    turn_ctx = TurnContext(
        turn_index=0,
        actor_id="wizard",
        actor_team="party",
    )

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0,
    )

    # Find spell_cast event
    spell_cast_events = [
        e for e in result.events
        if e.event_type == "spell_cast"
    ]
    assert spell_cast_events, "No spell_cast event was emitted"

    for event in spell_cast_events:
        payload = event.payload
        assert "content_id" in payload, (
            f"spell_cast event missing content_id in payload: {payload}"
        )
        assert payload["content_id"] == "spell.magic_missile_003", (
            f"Expected content_id='spell.magic_missile_003', "
            f"got '{payload['content_id']}'"
        )


def test_spell_hp_changed_event_contains_content_id():
    """hp_changed events from spell damage should include content_id."""
    world_state = _make_combat_state()
    rng = RNGManager(master_seed=42)

    intent = SpellCastIntent(
        caster_id="wizard",
        spell_id="magic_missile",
        target_entity_id="goblin",
    )

    turn_ctx = TurnContext(
        turn_index=0,
        actor_id="wizard",
        actor_team="party",
    )

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0,
    )

    # Find hp_changed event
    hp_events = [
        e for e in result.events
        if e.event_type == "hp_changed"
    ]
    assert hp_events, "No hp_changed event was emitted"

    for event in hp_events:
        payload = event.payload
        assert "content_id" in payload, (
            f"hp_changed event missing content_id in payload: {payload}"
        )
        assert payload["content_id"] == "spell.magic_missile_003"
