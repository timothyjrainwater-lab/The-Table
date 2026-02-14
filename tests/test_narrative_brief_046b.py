"""Tests for WO-046B: NarrativeBrief Completion — All Event Types

Verifies:
- Spell event extraction (spell_cast, spell_cast_failed, concentration_broken)
- Maneuver event extraction (bull_rush, trip, overrun, sunder, disarm, grapple)
- AoO event extraction (aoo_triggered, aoo_blocked_by_cover, aoo_avoided_by_tumble)
- Movement event extraction (movement_declared, mounted_move_declared)
- Full attack events (full_attack_start, full_attack_end)
- Condition removal events (condition_removed)
- Concealment miss events
- Targeting failure events
- New NarrativeBrief fields: spell_name, condition_removed, maneuver_type
- Outcome summary templates for all narration tokens
- Backward compatibility with existing tests
- Containment boundary: no entity IDs, HP values, or mechanical data leak
"""

import pytest

from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.lens.narrative_brief import (
    NarrativeBrief,
    assemble_narrative_brief,
    _build_outcome_summary,
)


# ══════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def world_state():
    """WorldState with diverse entities for event testing."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "fighter_1": {
                "name": "Aldric the Bold",
                "hp": 45,
                "hp_max": 50,
            },
            "wizard_1": {
                "name": "Elara Stormweave",
                "hp": 22,
                "hp_max": 28,
            },
            "goblin_1": {
                "name": "Goblin Warrior",
                "hp": 6,
                "hp_max": 10,
            },
            "goblin_2": {
                "name": "Goblin Archer",
                "hp": 0,
                "hp_max": 8,
            },
            "ogre_1": {
                "name": "Ogre Brute",
                "hp": 30,
                "hp_max": 40,
            },
            "cleric_1": {
                "name": "Brother Marcus",
                "hp": 35,
                "hp_max": 38,
            },
        },
    )


@pytest.fixture
def frozen(world_state):
    """FrozenWorldStateView for testing."""
    return FrozenWorldStateView(world_state)


# ══════════════════════════════════════════════════════════════════════════
# SPELL EVENT TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestSpellEvents:
    """Tests for spell event extraction and narration."""

    def test_spell_cast_event(self, frozen):
        """spell_cast event extracts caster, target, and spell name."""
        events = [
            {
                "event_id": 100,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "fireball",
                    "targets": ["goblin_1"],
                    "resolution_type": "damage",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Elara Stormweave"
        assert brief.target_name == "Goblin Warrior"
        assert brief.spell_name == "fireball"
        assert brief.action_type == "spell_damage_dealt"

    def test_spell_cast_with_damage(self, frozen):
        """spell_cast + hp_changed computes severity."""
        events = [
            {
                "event_id": 101,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "magic_missile",
                    "targets": ["goblin_1"],
                },
            },
            {
                "event_id": 102,
                "type": "hp_changed",
                "payload": {
                    "entity_id": "goblin_1",
                    "delta": -7,
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen,
        )
        assert brief.severity == "devastating"  # 7/10 = 70%
        assert brief.spell_name == "magic_missile"
        assert "strikes" in brief.outcome_summary

    def test_spell_healed(self, frozen):
        """spell_healed narration token produces healing summary."""
        events = [
            {
                "event_id": 103,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "cleric_1",
                    "spell_id": "cure_light_wounds",
                    "targets": ["fighter_1"],
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_healed",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Brother Marcus"
        assert brief.target_name == "Aldric the Bold"
        assert "heals" in brief.outcome_summary
        assert "cure_light_wounds" in brief.outcome_summary

    def test_spell_buff_applied(self, frozen):
        """spell_buff_applied narration token."""
        events = [
            {
                "event_id": 104,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "haste",
                    "targets": ["fighter_1"],
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_buff_applied",
            frozen_view=frozen,
        )
        assert "enhances" in brief.outcome_summary
        assert "haste" in brief.outcome_summary

    def test_spell_debuff_with_condition(self, frozen):
        """spell_debuff_applied includes condition name."""
        events = [
            {
                "event_id": 105,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "hold_person",
                    "targets": ["ogre_1"],
                },
            },
            {
                "event_id": 106,
                "type": "condition_applied",
                "target": "ogre_1",
                "condition": "paralyzed",
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_debuff_applied",
            frozen_view=frozen,
        )
        assert brief.condition_applied == "paralyzed"
        assert "paralyzed" in brief.outcome_summary
        assert "hold_person" in brief.outcome_summary

    def test_spell_resisted(self, frozen):
        """spell_resisted reverses actor/target in summary."""
        events = [
            {
                "event_id": 107,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "charm_person",
                    "targets": ["ogre_1"],
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_resisted",
            frozen_view=frozen,
        )
        assert "resists" in brief.outcome_summary
        assert "Ogre Brute" in brief.outcome_summary

    def test_spell_no_effect(self, frozen):
        """spell_no_effect narration token."""
        events = [
            {
                "event_id": 108,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "sleep",
                    "targets": ["ogre_1"],
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_no_effect",
            frozen_view=frozen,
        )
        assert "no effect" in brief.outcome_summary

    def test_spell_cast_success_no_target(self, frozen):
        """spell_cast_success with no target (area/self spell)."""
        events = [
            {
                "event_id": 109,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "shield",
                    "targets": [],
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_cast_success",
            frozen_view=frozen,
        )
        assert "casts" in brief.outcome_summary
        assert "shield" in brief.outcome_summary

    def test_spell_cast_failed(self, frozen):
        """spell_cast_failed event extracts caster and spell."""
        events = [
            {
                "event_id": 110,
                "type": "spell_cast_failed",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "fireball",
                    "reason": "concentration_check_failed",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_cast_success",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Elara Stormweave"
        assert brief.spell_name == "fireball"

    def test_concentration_broken(self, frozen):
        """concentration_broken event extracts caster and spell."""
        events = [
            {
                "event_id": 111,
                "type": "concentration_broken",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "invisibility",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_no_effect",
            frozen_view=frozen,
        )
        assert brief.spell_name == "invisibility"
        assert brief.actor_name == "Elara Stormweave"

    def test_spell_defeat(self, frozen):
        """Spell kills target → lethal severity."""
        events = [
            {
                "event_id": 112,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "fireball",
                    "targets": ["goblin_1"],
                },
            },
            {
                "event_id": 113,
                "type": "hp_changed",
                "payload": {
                    "entity_id": "goblin_1",
                    "delta": -10,
                },
            },
            {
                "event_id": 114,
                "type": "entity_defeated",
                "target": "goblin_1",
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen,
        )
        assert brief.severity == "lethal"
        assert brief.target_defeated
        assert "destroys" in brief.outcome_summary


# ══════════════════════════════════════════════════════════════════════════
# MANEUVER EVENT TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestManeuverEvents:
    """Tests for combat maneuver event extraction and narration."""

    def test_bull_rush_success(self, frozen):
        """bull_rush_success event extraction."""
        events = [
            {
                "event_id": 200,
                "type": "bull_rush_success",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "goblin_1",
                    "pushed_distance": 10,
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="bull_rush_success",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"
        assert brief.target_name == "Goblin Warrior"
        assert brief.maneuver_type == "bull_rush"
        assert "bull rush" in brief.outcome_summary.lower()

    def test_bull_rush_failure(self, frozen):
        """bull_rush_failure event extraction."""
        events = [
            {
                "event_id": 201,
                "type": "bull_rush_failure",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "ogre_1",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="bull_rush_failure",
            frozen_view=frozen,
        )
        assert brief.maneuver_type == "bull_rush"
        assert "fails" in brief.outcome_summary

    def test_trip_success_with_condition(self, frozen):
        """trip_success extracts prone condition."""
        events = [
            {
                "event_id": 202,
                "type": "trip_success",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "goblin_1",
                    "condition_applied": "prone",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="trip_success",
            frozen_view=frozen,
        )
        assert brief.maneuver_type == "trip"
        assert brief.condition_applied == "prone"
        assert "trips" in brief.outcome_summary

    def test_trip_failure(self, frozen):
        """trip_failure event."""
        events = [
            {
                "event_id": 203,
                "type": "trip_failure",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "ogre_1",
                    "reason": "opposed_check_lost",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="trip_failure",
            frozen_view=frozen,
        )
        assert brief.maneuver_type == "trip"
        assert "fails" in brief.outcome_summary

    def test_counter_trip_success(self, frozen):
        """counter_trip_success uses counter_attacker as actor."""
        events = [
            {
                "event_id": 204,
                "type": "counter_trip_success",
                "payload": {
                    "counter_attacker": "ogre_1",
                    "target_id": "fighter_1",
                    "condition_applied": "prone",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="trip_success",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Ogre Brute"
        assert brief.target_name == "Aldric the Bold"
        assert brief.condition_applied == "prone"

    def test_overrun_success(self, frozen):
        """overrun_success event with defender_id field variant."""
        events = [
            {
                "event_id": 205,
                "type": "overrun_success",
                "payload": {
                    "attacker_id": "fighter_1",
                    "defender_id": "goblin_1",
                    "condition_applied": "prone",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="overrun_success",
            frozen_view=frozen,
        )
        assert brief.target_name == "Goblin Warrior"
        assert brief.maneuver_type == "overrun"
        assert "overruns" in brief.outcome_summary

    def test_overrun_avoided(self, frozen):
        """overrun_avoided event uses defender_id."""
        events = [
            {
                "event_id": 206,
                "type": "overrun_avoided",
                "payload": {
                    "attacker_id": "fighter_1",
                    "defender_id": "goblin_1",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="overrun_avoided",
            frozen_view=frozen,
        )
        assert brief.maneuver_type == "overrun"
        assert "avoids" in brief.outcome_summary

    def test_sunder_success(self, frozen):
        """sunder_success event."""
        events = [
            {
                "event_id": 207,
                "type": "sunder_success",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "goblin_1",
                    "target_item": "shortbow",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="sunder_success",
            frozen_view=frozen,
        )
        assert brief.maneuver_type == "sunder"
        assert "sunders" in brief.outcome_summary

    def test_disarm_success(self, frozen):
        """disarm_success event."""
        events = [
            {
                "event_id": 208,
                "type": "disarm_success",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "goblin_1",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="disarm_success",
            frozen_view=frozen,
        )
        assert brief.maneuver_type == "disarm"
        assert "disarms" in brief.outcome_summary

    def test_counter_disarm_success(self, frozen):
        """counter_disarm_success uses counter_attacker."""
        events = [
            {
                "event_id": 209,
                "type": "counter_disarm_success",
                "payload": {
                    "counter_attacker": "ogre_1",
                    "target_id": "fighter_1",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="disarm_success",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Ogre Brute"
        assert brief.maneuver_type == "disarm"

    def test_grapple_success(self, frozen):
        """grapple_success extracts grappled condition."""
        events = [
            {
                "event_id": 210,
                "type": "grapple_success",
                "payload": {
                    "attacker_id": "ogre_1",
                    "target_id": "fighter_1",
                    "condition_applied": "grappled",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="grapple_success",
            frozen_view=frozen,
        )
        assert brief.maneuver_type == "grapple"
        assert brief.condition_applied == "grappled"
        assert "grapples" in brief.outcome_summary

    def test_grapple_failure(self, frozen):
        """grapple_failure event."""
        events = [
            {
                "event_id": 211,
                "type": "grapple_failure",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "ogre_1",
                    "reason": "touch_attack_missed",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="grapple_failure",
            frozen_view=frozen,
        )
        assert brief.maneuver_type == "grapple"
        assert "fails" in brief.outcome_summary


# ══════════════════════════════════════════════════════════════════════════
# AOO EVENT TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestAoOEvents:
    """Tests for Attack of Opportunity event extraction."""

    def test_aoo_triggered(self, frozen):
        """aoo_triggered extracts reactor (attacker) and provoker (target)."""
        events = [
            {
                "event_id": 300,
                "type": "aoo_triggered",
                "payload": {
                    "reactor_id": "fighter_1",
                    "provoker_id": "goblin_1",
                    "provoking_action": "movement_out",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"
        assert brief.target_name == "Goblin Warrior"

    def test_aoo_blocked_by_cover(self, frozen):
        """aoo_blocked_by_cover extracts actor/target."""
        events = [
            {
                "event_id": 301,
                "type": "aoo_blocked_by_cover",
                "payload": {
                    "reactor_id": "fighter_1",
                    "provoker_id": "goblin_1",
                    "cover_type": "total",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_miss",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"
        assert brief.target_name == "Goblin Warrior"

    def test_aoo_avoided_by_tumble(self, frozen):
        """aoo_avoided_by_tumble extracts actor/target."""
        events = [
            {
                "event_id": 302,
                "type": "aoo_avoided_by_tumble",
                "payload": {
                    "reactor_id": "fighter_1",
                    "provoker_id": "goblin_1",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_miss",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"
        assert brief.target_name == "Goblin Warrior"

    def test_action_aborted_by_aoo(self, frozen):
        """action_aborted_by_aoo narration token."""
        brief = assemble_narrative_brief(
            events=[{"event_id": 303, "type": "aoo_triggered", "payload": {
                "reactor_id": "fighter_1", "provoker_id": "goblin_1",
            }}],
            narration_token="action_aborted_by_aoo",
            frozen_view=frozen,
        )
        assert "interrupted" in brief.outcome_summary
        assert "attack of opportunity" in brief.outcome_summary


# ══════════════════════════════════════════════════════════════════════════
# MOVEMENT EVENT TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestMovementEvents:
    """Tests for movement event extraction and narration."""

    def test_movement_declared(self, frozen):
        """movement_declared extracts actor_id."""
        events = [
            {
                "event_id": 400,
                "type": "movement_declared",
                "payload": {
                    "actor_id": "fighter_1",
                    "from_pos": [0, 0],
                    "to_pos": [5, 0],
                    "distance": 5,
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="movement_stub",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"
        assert brief.target_name is None
        assert "moves" in brief.outcome_summary

    def test_mounted_move_declared(self, frozen):
        """mounted_move_declared extracts rider_id."""
        events = [
            {
                "event_id": 401,
                "type": "mounted_move_declared",
                "payload": {
                    "rider_id": "fighter_1",
                    "mount_id": "warhorse_1",
                    "distance": 60,
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="mounted_movement",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"
        assert "rides" in brief.outcome_summary

    def test_mounted_narration(self, frozen):
        """'mounted' narration token."""
        events = [{"event_id": 402, "type": "movement_declared", "payload": {
            "actor_id": "fighter_1",
        }}]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="mounted",
            frozen_view=frozen,
        )
        assert "mounts up" in brief.outcome_summary

    def test_dismounted_narration(self, frozen):
        """'dismounted' narration token."""
        events = [{"event_id": 403, "type": "movement_declared", "payload": {
            "actor_id": "fighter_1",
        }}]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="dismounted",
            frozen_view=frozen,
        )
        assert "dismounts" in brief.outcome_summary


# ══════════════════════════════════════════════════════════════════════════
# FULL ATTACK EVENT TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestFullAttackEvents:
    """Tests for full attack event extraction and narration."""

    def test_full_attack_start_extracts_ids(self, frozen):
        """full_attack_start extracts attacker/target."""
        events = [
            {
                "event_id": 500,
                "type": "full_attack_start",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "ogre_1",
                    "num_attacks": 3,
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="full_attack_complete",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"
        assert brief.target_name == "Ogre Brute"
        assert "flurry" in brief.outcome_summary

    def test_full_attack_complete_with_defeat(self, frozen):
        """Full attack completing with target defeat."""
        events = [
            {"event_id": 501, "type": "full_attack_start", "payload": {
                "attacker_id": "fighter_1", "target_id": "goblin_1",
            }},
            {"event_id": 502, "type": "entity_defeated", "target": "goblin_1"},
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="full_attack_complete",
            frozen_view=frozen,
        )
        assert brief.target_defeated
        assert "strikes down" in brief.outcome_summary


# ══════════════════════════════════════════════════════════════════════════
# CONDITION EVENT TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestConditionEvents:
    """Tests for condition applied/removed event extraction."""

    def test_condition_applied_with_condition_type(self, frozen):
        """condition_applied with payload.condition_type field."""
        events = [
            {
                "event_id": 600,
                "type": "condition_applied",
                "payload": {
                    "target_id": "goblin_1",
                    "condition_type": "stunned",
                    "source": "spell",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="condition_applied",
            frozen_view=frozen,
        )
        assert brief.condition_applied == "stunned"
        assert "stunned" in brief.outcome_summary

    def test_condition_removed(self, frozen):
        """condition_removed extracts entity and condition."""
        events = [
            {
                "event_id": 601,
                "type": "condition_removed",
                "payload": {
                    "entity_id": "fighter_1",
                    "condition_type": "prone",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="condition_removed",
            frozen_view=frozen,
        )
        assert brief.condition_removed == "prone"
        assert "no longer" in brief.outcome_summary
        assert "prone" in brief.outcome_summary

    def test_condition_applied_with_spell_style_keys(self, frozen):
        """condition_applied with payload.entity_id + payload.condition (spell path).

        WO-CONDITION-EXTRACTION-FIX: play_loop emits condition_applied events
        with payload={"entity_id": ..., "condition": ...}. The assembler must
        extract both fields via fallback chain.
        """
        events = [
            {
                "event_id": 602,
                "type": "condition_applied",
                "payload": {
                    "entity_id": "goblin_1",
                    "condition": "paralyzed",
                    "source": "spell:hold_person",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="condition_applied",
            frozen_view=frozen,
        )
        assert brief.condition_applied == "paralyzed"
        assert brief.target_name == "Goblin Warrior"
        assert "paralyzed" in brief.outcome_summary

    def test_condition_removed_with_spell_style_keys(self, frozen):
        """condition_removed with payload.condition (spell/concentration path).

        WO-CONDITION-EXTRACTION-FIX: play_loop emits condition_removed events
        with payload={"entity_id": ..., "condition": ...} when concentration breaks.
        """
        events = [
            {
                "event_id": 603,
                "type": "condition_removed",
                "payload": {
                    "entity_id": "fighter_1",
                    "condition": "paralyzed",
                    "reason": "concentration_broken",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="condition_removed",
            frozen_view=frozen,
        )
        assert brief.condition_removed == "paralyzed"
        assert brief.target_name == "Aldric the Bold"
        assert "no longer" in brief.outcome_summary
        assert "paralyzed" in brief.outcome_summary


# ══════════════════════════════════════════════════════════════════════════
# CONCEALMENT & TARGETING TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestConcealmentAndTargeting:
    """Tests for concealment miss and targeting failure events."""

    def test_concealment_miss(self, frozen):
        """concealment_miss event extracts attacker/target."""
        events = [
            {
                "event_id": 700,
                "type": "concealment_miss",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "goblin_1",
                    "miss_chance_percent": 20,
                    "d100_result": 15,
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="concealment_miss",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"
        assert brief.target_name == "Goblin Warrior"
        assert "concealment" in brief.outcome_summary

    def test_targeting_failed(self, frozen):
        """targeting_failed event extracts actor/target."""
        events = [
            {
                "event_id": 701,
                "type": "targeting_failed",
                "payload": {
                    "actor_id": "fighter_1",
                    "target_id": "goblin_1",
                    "reason": "total_cover",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_miss",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"
        assert brief.target_name == "Goblin Warrior"


# ══════════════════════════════════════════════════════════════════════════
# DAMAGE_ROLL EVENT FORMAT TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestDamageRollFormat:
    """Tests for damage_roll (payload format) vs damage_dealt (flat format)."""

    def test_damage_roll_payload_format(self, frozen):
        """damage_roll event with payload-style fields."""
        events = [
            {
                "event_id": 800,
                "event_type": "attack_roll",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "goblin_1",
                },
            },
            {
                "event_id": 801,
                "event_type": "damage_roll",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "goblin_1",
                    "final_damage": 8,
                    "damage_type": "slashing",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"
        assert brief.damage_type == "slashing"
        assert brief.severity == "lethal"  # 8/10 = 80%

    def test_event_type_field_variant(self, frozen):
        """Events using 'event_type' instead of 'type' key."""
        events = [
            {
                "event_id": 802,
                "event_type": "attack_roll",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "goblin_1",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=frozen,
        )
        assert brief.actor_name == "Aldric the Bold"


# ══════════════════════════════════════════════════════════════════════════
# NEW FIELDS TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestNewFields:
    """Tests for new NarrativeBrief fields added in WO-046B."""

    def test_spell_name_in_to_dict(self):
        """spell_name serializes to dict."""
        brief = NarrativeBrief(
            action_type="spell_damage_dealt",
            actor_name="Elara",
            spell_name="fireball",
        )
        data = brief.to_dict()
        assert data["spell_name"] == "fireball"

    def test_condition_removed_in_to_dict(self):
        """condition_removed serializes to dict."""
        brief = NarrativeBrief(
            action_type="condition_removed",
            actor_name="system",
            condition_removed="prone",
        )
        data = brief.to_dict()
        assert data["condition_removed"] == "prone"

    def test_maneuver_type_in_to_dict(self):
        """maneuver_type serializes to dict."""
        brief = NarrativeBrief(
            action_type="trip_success",
            actor_name="Aldric",
            maneuver_type="trip",
        )
        data = brief.to_dict()
        assert data["maneuver_type"] == "trip"

    def test_new_fields_from_dict(self):
        """New fields deserialize from dict."""
        data = {
            "action_type": "spell_damage_dealt",
            "actor_name": "Elara",
            "spell_name": "fireball",
            "condition_removed": "prone",
            "maneuver_type": "trip",
        }
        brief = NarrativeBrief.from_dict(data)
        assert brief.spell_name == "fireball"
        assert brief.condition_removed == "prone"
        assert brief.maneuver_type == "trip"

    def test_new_fields_default_none(self):
        """New fields default to None when not specified."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
        )
        assert brief.spell_name is None
        assert brief.condition_removed is None
        assert brief.maneuver_type is None

    def test_new_fields_in_from_dict_missing(self):
        """New fields default to None in from_dict when not present."""
        data = {
            "action_type": "attack_hit",
            "actor_name": "Aldric",
        }
        brief = NarrativeBrief.from_dict(data)
        assert brief.spell_name is None
        assert brief.condition_removed is None
        assert brief.maneuver_type is None


# ══════════════════════════════════════════════════════════════════════════
# OUTCOME SUMMARY COVERAGE TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestOutcomeSummaryTemplates:
    """Verify all narration tokens produce non-generic outcomes."""

    @pytest.mark.parametrize("token,expected_fragment", [
        ("attack_hit", "hits"),
        ("attack_miss", "misses"),
        ("critical", "critical hit"),
        ("full_attack_complete", "flurry"),
        ("concealment_miss", "concealment"),
        ("spell_damage_dealt", "strikes"),
        ("spell_no_effect", "no effect"),
        ("spell_healed", "heals"),
        ("spell_buff_applied", "enhances"),
        ("spell_debuff_applied", "inflicts"),
        ("spell_resisted", "resists"),
        ("spell_cast_success", "casts"),
        ("bull_rush_success", "bull rush"),
        ("bull_rush_failure", "fails"),
        ("trip_success", "trips"),
        ("trip_failure", "fails"),
        ("overrun_success", "overruns"),
        ("overrun_failure", "fails"),
        ("sunder_success", "sunders"),
        ("sunder_failure", "fails"),
        ("disarm_success", "disarms"),
        ("disarm_failure", "fails"),
        ("grapple_success", "grapples"),
        ("grapple_failure", "fails"),
        ("movement_stub", "moves"),
        ("mounted_movement", "rides"),
        ("mounted", "mounts up"),
        ("dismounted", "dismounts"),
        ("action_aborted_by_aoo", "interrupted"),
        ("defeat", "defeats"),
    ])
    def test_narration_token_outcome(self, token, expected_fragment):
        """Each narration token produces a specific summary, not generic fallback."""
        summary = _build_outcome_summary(
            action_type=token,
            actor_name="Aldric",
            target_name="Goblin",
            weapon_name="longsword",
            spell_name="fireball",
            condition_applied="prone",
            condition_removed="stunned",
            maneuver_type="trip",
            target_defeated=False,
        )
        assert expected_fragment in summary.lower(), (
            f"Token '{token}' should produce summary containing '{expected_fragment}', "
            f"got: '{summary}'"
        )


# ══════════════════════════════════════════════════════════════════════════
# CONTAINMENT BOUNDARY TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestContainmentBoundary:
    """Verify NarrativeBrief never leaks mechanical data."""

    def test_no_entity_ids_in_spell_brief(self, frozen):
        """Spell events must not leak entity IDs."""
        events = [
            {
                "event_id": 900,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "fireball",
                    "targets": ["goblin_1"],
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen,
        )
        data = brief.to_dict()
        for key, value in data.items():
            if isinstance(value, str):
                assert "wizard_1" not in value, f"Entity ID leaked in field '{key}'"
                assert "goblin_1" not in value, f"Entity ID leaked in field '{key}'"

    def test_no_entity_ids_in_maneuver_brief(self, frozen):
        """Maneuver events must not leak entity IDs."""
        events = [
            {
                "event_id": 901,
                "type": "grapple_success",
                "payload": {
                    "attacker_id": "ogre_1",
                    "target_id": "fighter_1",
                    "condition_applied": "grappled",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="grapple_success",
            frozen_view=frozen,
        )
        data = brief.to_dict()
        for key, value in data.items():
            if isinstance(value, str):
                assert "ogre_1" not in value
                assert "fighter_1" not in value

    def test_no_mechanical_data_in_aoo_brief(self, frozen):
        """AoO events must not leak d100 rolls, DCs, or cover types."""
        events = [
            {
                "event_id": 902,
                "type": "aoo_blocked_by_cover",
                "payload": {
                    "reactor_id": "fighter_1",
                    "provoker_id": "goblin_1",
                    "cover_type": "total",
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_miss",
            frozen_view=frozen,
        )
        data = brief.to_dict()
        # cover_type should not appear in any field
        for key, value in data.items():
            if isinstance(value, str) and key != "action_type":
                assert "total" not in value or key == "outcome_summary"

    def test_no_hp_in_spell_damage_brief(self, frozen):
        """Spell damage brief must not contain HP numbers."""
        events = [
            {
                "event_id": 903,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "fireball",
                    "targets": ["goblin_1"],
                },
            },
            {
                "event_id": 904,
                "type": "hp_changed",
                "payload": {
                    "entity_id": "goblin_1",
                    "hp_before": 10,
                    "hp_after": 2,
                    "delta": -8,
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen,
        )
        data = brief.to_dict()
        # No field should be named "hp", "hp_before", "hp_after"
        assert "hp" not in data
        assert "hp_before" not in data
        assert "hp_after" not in data
        assert "delta" not in data


# ══════════════════════════════════════════════════════════════════════════
# MULTI-EVENT PIPELINE TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestMultiEventPipeline:
    """Tests for multi-event sequences through the assembler."""

    def test_maneuver_with_aoo_and_condition(self, frozen):
        """Trip with AoO + condition application."""
        events = [
            {"event_id": 1000, "type": "aoo_triggered", "payload": {
                "reactor_id": "goblin_1", "provoker_id": "fighter_1",
            }},
            {"event_id": 1001, "type": "trip_success", "payload": {
                "attacker_id": "fighter_1", "target_id": "goblin_1",
                "condition_applied": "prone",
            }},
            {"event_id": 1002, "type": "condition_applied",
             "target": "goblin_1", "condition": "prone"},
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="trip_success",
            frozen_view=frozen,
        )
        # trip_success should override aoo_triggered actor/target
        assert brief.actor_name == "Aldric the Bold"
        assert brief.target_name == "Goblin Warrior"
        assert brief.maneuver_type == "trip"
        assert brief.condition_applied == "prone"

    def test_spell_chain_with_defeat(self, frozen):
        """Spell → damage → defeat pipeline."""
        events = [
            {"event_id": 1003, "type": "spell_cast", "payload": {
                "caster_id": "wizard_1", "spell_id": "disintegrate",
                "targets": ["goblin_2"],
            }},
            {"event_id": 1004, "type": "hp_changed", "payload": {
                "entity_id": "goblin_2", "delta": -50,
            }},
            {"event_id": 1005, "type": "entity_defeated",
             "target": "goblin_2"},
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen,
        )
        assert brief.target_defeated
        assert brief.severity == "lethal"
        assert brief.spell_name == "disintegrate"
        assert brief.source_event_ids == (1003, 1004, 1005)

    def test_provenance_tracks_all_events(self, frozen):
        """source_event_ids collects all event IDs."""
        events = [
            {"event_id": 1, "type": "attack_roll", "attacker": "fighter_1",
             "target": "goblin_1"},
            {"event_id": 2, "type": "damage_dealt", "attacker": "fighter_1",
             "target": "goblin_1", "damage": 3},
            {"event_id": 3, "type": "hp_changed", "payload": {
                "entity_id": "goblin_1", "delta": -3,
            }},
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=frozen,
        )
        assert brief.source_event_ids == (1, 2, 3)
        assert brief.provenance_tag == "[DERIVED]"
