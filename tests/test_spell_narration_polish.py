"""Tests for WO-SPELL-NARRATION-POLISH.

Verifies:
- hp_changed events from spell damage include damage_type in payload
- assemble_narrative_brief extracts damage_type from hp_changed events
- NarrationContext.from_engine_result resolves entity names from caster_id
- Narrator produces named narration for spell events
"""

import pytest
from datetime import datetime

from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.lens.narrative_brief import assemble_narrative_brief
from aidm.narration.narrator import (
    Narrator,
    NarrationContext,
    NarrationTemplates,
)
from aidm.schemas.engine_result import EngineResultBuilder


# ══════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def spell_world_state():
    """WorldState with caster and targets for spell tests."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "evoker_1": {
                "name": "Elara the Evoker",
                "hp": 30,
                "hp_max": 30,
            },
            "goblin_1": {
                "name": "Goblin Raider",
                "hp": 10,
                "hp_max": 10,
            },
        },
    )


@pytest.fixture
def frozen_view(spell_world_state):
    return FrozenWorldStateView(spell_world_state)


# ══════════════════════════════════════════════════════════════════════════
# Gap 1: damage_type in hp_changed → NarrativeBrief
# ══════════════════════════════════════════════════════════════════════════


class TestDamageTypeInHpChanged:
    """Verify damage_type flows from hp_changed to NarrativeBrief."""

    def test_hp_changed_with_damage_type_populates_brief(self, frozen_view):
        """hp_changed event with damage_type should populate NarrativeBrief.damage_type."""
        events = [
            {
                "event_id": 1,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "evoker_1",
                    "spell_id": "fireball",
                    "spell_name": "Fireball",
                    "targets": ["goblin_1"],
                },
            },
            {
                "event_id": 2,
                "type": "hp_changed",
                "payload": {
                    "entity_id": "goblin_1",
                    "old_hp": 10,
                    "new_hp": -19,
                    "delta": -29,
                    "source": "spell:Fireball",
                    "damage_type": "fire",
                    "caster_id": "evoker_1",
                },
            },
        ]

        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen_view,
        )

        assert brief.damage_type == "fire"

    def test_hp_changed_without_damage_type_leaves_none(self, frozen_view):
        """hp_changed event without damage_type should leave NarrativeBrief.damage_type as None."""
        events = [
            {
                "event_id": 1,
                "type": "hp_changed",
                "payload": {
                    "entity_id": "goblin_1",
                    "delta": -5,
                },
            },
        ]

        brief = assemble_narrative_brief(
            events=events,
            narration_token="damage_applied",
            frozen_view=frozen_view,
        )

        assert brief.damage_type is None


# ══════════════════════════════════════════════════════════════════════════
# Gap 2: caster_id recognition in Narrator
# ══════════════════════════════════════════════════════════════════════════


class TestCasterIdRecognition:
    """Verify NarrationContext resolves entity names from caster_id."""

    def test_from_engine_result_resolves_caster_id(self):
        """NarrationContext should extract actor_id from caster_id in spell_cast events."""
        builder = EngineResultBuilder(intent_id="test-spell")
        builder.add_event({
            "type": "spell_cast",
            "payload": {
                "caster_id": "evoker_1",
                "spell_id": "fireball",
                "targets": ["goblin_1"],
            },
        })
        builder.add_event({
            "type": "hp_changed",
            "payload": {
                "entity_id": "goblin_1",
                "delta": -29,
                "damage_type": "fire",
                "caster_id": "evoker_1",
            },
        })
        builder.set_narration_token("spell_damage_dealt")
        result = builder.build(
            result_id="test-result-001",
            resolved_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        names = {
            "evoker_1": "Elara the Evoker",
            "goblin_1": "Goblin Raider",
        }
        context = NarrationContext.from_engine_result(result, names)

        assert context.actor_id == "evoker_1"
        assert context.actor_name == "Elara the Evoker"
        assert context.target_id == "goblin_1"
        assert context.target_name == "Goblin Raider"

    def test_attacker_takes_precedence_over_caster_id(self):
        """If attacker is present (attack_roll), it should take precedence over caster_id."""
        builder = EngineResultBuilder(intent_id="test-melee")
        builder.add_event({
            "type": "attack_roll",
            "attacker": "fighter_1",
            "target": "goblin_1",
            "hit": True,
        })
        builder.add_event({
            "type": "spell_cast",
            "payload": {
                "caster_id": "wizard_1",
                "spell_id": "some_spell",
            },
        })
        builder.set_narration_token("attack_hit")
        result = builder.build(
            result_id="test-result-002",
            resolved_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        context = NarrationContext.from_engine_result(result)

        # attacker from attack_roll should win
        assert context.actor_id == "fighter_1"

    def test_narrator_produces_named_spell_narration(self):
        """Narrator should produce named narration for spell events, not 'The attacker'."""
        builder = EngineResultBuilder(intent_id="test-spell")
        builder.add_event({
            "type": "spell_cast",
            "payload": {
                "caster_id": "evoker_1",
                "spell_id": "fireball",
                "targets": ["goblin_1"],
            },
        })
        builder.add_event({
            "type": "hp_changed",
            "payload": {
                "entity_id": "goblin_1",
                "delta": -29,
                "damage_type": "fire",
                "caster_id": "evoker_1",
            },
        })
        builder.set_narration_token("spell_damage_dealt")
        result = builder.build(
            result_id="test-result-003",
            resolved_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        narrator = Narrator()
        narrator.register_entity_names({
            "evoker_1": "Elara the Evoker",
            "goblin_1": "Goblin Raider",
        })

        narration = narrator.narrate(result)

        assert "Elara the Evoker" in narration
        assert "Goblin Raider" in narration
        assert "fire" in narration
        assert "29" in narration
        assert "The attacker" not in narration

    def test_narrator_spell_without_damage_type(self):
        """Narrator should handle spell events without damage_type gracefully."""
        builder = EngineResultBuilder(intent_id="test-spell")
        builder.add_event({
            "type": "spell_cast",
            "payload": {
                "caster_id": "evoker_1",
                "spell_id": "magic_missile",
                "targets": ["goblin_1"],
            },
        })
        builder.add_event({
            "type": "hp_changed",
            "payload": {
                "entity_id": "goblin_1",
                "delta": -5,
                "caster_id": "evoker_1",
            },
        })
        builder.set_narration_token("spell_damage_dealt")
        result = builder.build(
            result_id="test-result-004",
            resolved_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        narrator = Narrator()
        narrator.register_entity_names({
            "evoker_1": "Elara",
            "goblin_1": "Goblin",
        })

        narration = narrator.narrate(result)

        assert "Elara" in narration
        assert "Goblin" in narration
        assert "5" in narration


# ══════════════════════════════════════════════════════════════════════════
# Template rendering: spell_damage_dealt includes damage_type
# ══════════════════════════════════════════════════════════════════════════


class TestSpellDamageTemplate:
    """Verify spell_damage_dealt template renders damage_type."""

    def test_template_contains_damage_type_placeholder(self):
        """spell_damage_dealt template should include {damage_type} placeholder."""
        template = NarrationTemplates.get_template("spell_damage_dealt")
        assert "{damage_type}" in template

    def test_template_renders_fire(self):
        """Template should render 'fire' when damage_type is 'fire'."""
        template = NarrationTemplates.get_template("spell_damage_dealt")
        rendered = template.format(
            actor="Elara",
            target="Goblin",
            damage=29,
            damage_type="fire",
            weapon="weapon",
        )
        assert "fire" in rendered
        assert "29" in rendered


# ══════════════════════════════════════════════════════════════════════════
# event_type field variant (play_loop emits event_type, not type)
# ══════════════════════════════════════════════════════════════════════════


class TestEventTypeFieldVariant:
    """Verify assembler handles event_type (play_loop format) not just type."""

    def test_event_type_field_with_damage_type(self, frozen_view):
        """Events using event_type (not type) should still extract damage_type."""
        events = [
            {
                "event_id": 1,
                "event_type": "hp_changed",
                "payload": {
                    "entity_id": "goblin_1",
                    "delta": -29,
                    "damage_type": "fire",
                    "caster_id": "evoker_1",
                },
            },
        ]

        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen_view,
        )

        assert brief.damage_type == "fire"
