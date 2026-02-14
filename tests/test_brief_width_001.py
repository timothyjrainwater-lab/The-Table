"""Tests for WO-BRIEF-WIDTH-001: NarrativeBrief Multi-Target, Causal Chains, and Conditions.

Verifies:
- Multi-target assembly: AoE hitting multiple targets populates additional_targets
- Causal chain linkage: Events with causal_chain_id propagate to NarrativeBrief
- Condition stack population: active_conditions and actor_conditions from FrozenWorldStateView
- condition_removed serialization: Bug fix — condition_removed reaches TruthChannel
- Outcome summary includes multi-target/chain context
- Backward compatibility: existing single-target events unchanged
- NarrativeBrief serialization round-trip for new fields
- PromptPackBuilder carries new fields to TruthChannel
"""

import pytest

from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.lens.narrative_brief import (
    NarrativeBrief,
    assemble_narrative_brief,
    get_entity_conditions,
    _build_outcome_summary,
)
from aidm.lens.prompt_pack_builder import PromptPackBuilder


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def world_state_with_conditions():
    """WorldState with entities that have active conditions."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "fighter_1": {
                "name": "Aldric the Bold",
                "hp": 45,
                "hp_max": 50,
                "conditions": {
                    "haste": {"condition_type": "haste", "source": "spell"},
                },
            },
            "goblin_1": {
                "name": "Goblin Warrior",
                "hp": 6,
                "hp_max": 10,
                "conditions": {
                    "prone": {"condition_type": "prone", "source": "trip"},
                    "grappled": {"condition_type": "grappled", "source": "grapple"},
                },
            },
            "goblin_2": {
                "name": "Goblin Archer",
                "hp": 7,
                "hp_max": 8,
                "conditions": {},
            },
            "goblin_3": {
                "name": "Goblin Shaman",
                "hp": 4,
                "hp_max": 6,
                "conditions": {},
            },
            "wizard_1": {
                "name": "Elara Stormweave",
                "hp": 22,
                "hp_max": 28,
                "conditions": {},
            },
        },
    )


@pytest.fixture
def frozen(world_state_with_conditions):
    """FrozenWorldStateView for testing."""
    return FrozenWorldStateView(world_state_with_conditions)


@pytest.fixture
def simple_world_state():
    """WorldState without conditions for backward compat tests."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "fighter_1": {
                "name": "Aldric the Bold",
                "hp": 45,
                "hp_max": 50,
            },
            "goblin_1": {
                "name": "Goblin Warrior",
                "hp": 6,
                "hp_max": 10,
            },
        },
    )


@pytest.fixture
def simple_frozen(simple_world_state):
    return FrozenWorldStateView(simple_world_state)


# ==============================================================================
# CONDITION STACK TESTS
# ==============================================================================


class TestConditionStack:
    """Tests for active condition population from FrozenWorldStateView."""

    def test_get_entity_conditions_multiple(self, frozen):
        """Entity with multiple conditions returns sorted tuple."""
        conditions = get_entity_conditions("goblin_1", frozen)
        assert conditions == ("grappled", "prone")

    def test_get_entity_conditions_single(self, frozen):
        """Entity with single condition returns single-element tuple."""
        conditions = get_entity_conditions("fighter_1", frozen)
        assert conditions == ("haste",)

    def test_get_entity_conditions_empty(self, frozen):
        """Entity with no conditions returns empty tuple."""
        conditions = get_entity_conditions("goblin_2", frozen)
        assert conditions == ()

    def test_get_entity_conditions_missing_entity(self, frozen):
        """Missing entity returns empty tuple."""
        conditions = get_entity_conditions("nonexistent", frozen)
        assert conditions == ()

    def test_conditions_populated_on_brief(self, frozen):
        """assemble_narrative_brief populates active_conditions from target."""
        events = [
            {
                "event_id": 1,
                "type": "attack_roll",
                "attacker": "fighter_1",
                "target": "goblin_1",
                "weapon": "longsword",
            },
            {
                "event_id": 2,
                "type": "damage_dealt",
                "attacker": "fighter_1",
                "target": "goblin_1",
                "damage": 4,
                "damage_type": "slashing",
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=frozen,
        )
        assert brief.active_conditions == ("grappled", "prone")
        assert brief.actor_conditions == ("haste",)

    def test_conditions_empty_when_no_conditions(self, frozen):
        """Target without conditions gets empty tuple."""
        events = [
            {
                "event_id": 1,
                "type": "attack_roll",
                "attacker": "fighter_1",
                "target": "goblin_2",
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=frozen,
        )
        assert brief.active_conditions == ()

    def test_conditions_empty_when_no_target(self, frozen):
        """No-target event gets empty conditions."""
        events = [
            {
                "event_id": 1,
                "type": "movement_declared",
                "payload": {"actor_id": "fighter_1"},
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="movement_stub",
            frozen_view=frozen,
        )
        assert brief.active_conditions == ()


# ==============================================================================
# MULTI-TARGET ASSEMBLY TESTS
# ==============================================================================


class TestMultiTargetAssembly:
    """Tests for multi-target event grouping into additional_targets."""

    def test_single_target_no_additional(self, frozen):
        """Single-target damage produces empty additional_targets."""
        events = [
            {
                "event_id": 1,
                "type": "damage_dealt",
                "attacker": "wizard_1",
                "target": "goblin_1",
                "damage": 5,
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen,
        )
        assert brief.additional_targets == ()

    def test_multi_target_aoe(self, frozen):
        """Multiple damage_dealt events produce additional_targets."""
        events = [
            {
                "event_id": 1,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "fireball",
                    "targets": ["goblin_1", "goblin_2", "goblin_3"],
                },
            },
            {
                "event_id": 2,
                "type": "damage_dealt",
                "attacker": "wizard_1",
                "target": "goblin_1",
                "damage": 8,
                "damage_type": "fire",
            },
            {
                "event_id": 3,
                "type": "damage_dealt",
                "attacker": "wizard_1",
                "target": "goblin_2",
                "damage": 8,
                "damage_type": "fire",
            },
            {
                "event_id": 4,
                "type": "damage_dealt",
                "attacker": "wizard_1",
                "target": "goblin_3",
                "damage": 8,
                "damage_type": "fire",
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen,
        )
        # Primary target is the last target_id set (goblin_3)
        # Additional targets are goblin_1 and goblin_2
        assert len(brief.additional_targets) == 2
        additional_names = {t[0] for t in brief.additional_targets}
        assert "Goblin Warrior" in additional_names
        assert "Goblin Archer" in additional_names

    def test_multi_target_with_defeat(self, frozen):
        """Multi-target with one defeated target tracks defeated flag."""
        events = [
            {
                "event_id": 1,
                "type": "damage_dealt",
                "attacker": "wizard_1",
                "target": "goblin_1",
                "damage": 10,
            },
            {
                "event_id": 2,
                "type": "entity_defeated",
                "target": "goblin_1",
            },
            {
                "event_id": 3,
                "type": "damage_dealt",
                "attacker": "wizard_1",
                "target": "goblin_2",
                "damage": 3,
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen,
        )
        # goblin_2 is the primary (last target_id set by damage_dealt)
        # goblin_1 is additional
        assert len(brief.additional_targets) == 1
        additional = brief.additional_targets[0]
        assert additional[0] == "Goblin Warrior"
        assert additional[2] is True  # defeated

    def test_multi_target_outcome_summary(self, frozen):
        """Multi-target summary includes 'affecting N targets'."""
        events = [
            {
                "event_id": 1,
                "type": "damage_dealt",
                "attacker": "wizard_1",
                "target": "goblin_1",
                "damage": 5,
            },
            {
                "event_id": 2,
                "type": "damage_dealt",
                "attacker": "wizard_1",
                "target": "goblin_2",
                "damage": 5,
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen,
        )
        assert "affecting 2 targets" in brief.outcome_summary


# ==============================================================================
# CAUSAL CHAIN TESTS
# ==============================================================================


class TestCausalChain:
    """Tests for causal chain linkage across events."""

    def test_causal_chain_extracted_from_event(self, frozen):
        """causal_chain_id in event payload propagates to brief."""
        events = [
            {
                "event_id": 1,
                "type": "aoo_triggered",
                "payload": {
                    "reactor_id": "fighter_1",
                    "provoker_id": "goblin_1",
                    "provoking_action": "movement_out",
                    "causal_chain_id": "bull_rush_1_fighter_1",
                    "chain_position": 2,
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=frozen,
        )
        assert brief.causal_chain_id == "bull_rush_1_fighter_1"
        assert brief.chain_position == 2

    def test_causal_chain_none_when_absent(self, frozen):
        """No causal_chain_id in events → None on brief."""
        events = [
            {
                "event_id": 1,
                "type": "attack_roll",
                "attacker": "fighter_1",
                "target": "goblin_1",
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=frozen,
        )
        assert brief.causal_chain_id is None
        assert brief.chain_position == 0

    def test_chain_position_gt_1_summary(self):
        """chain_position > 1 appends 'triggered by a prior action' to summary."""
        summary = _build_outcome_summary(
            action_type="attack_hit",
            actor_name="Aldric",
            target_name="Goblin",
            weapon_name="longsword",
            spell_name=None,
            condition_applied=None,
            condition_removed=None,
            maneuver_type=None,
            target_defeated=False,
            additional_targets=(),
            causal_chain_id="chain_001",
            chain_position=2,
        )
        assert "triggered by a prior action" in summary

    def test_chain_position_1_no_suffix(self):
        """chain_position=1 (originating event) does NOT add triggered suffix."""
        summary = _build_outcome_summary(
            action_type="attack_hit",
            actor_name="Aldric",
            target_name="Goblin",
            weapon_name="longsword",
            spell_name=None,
            condition_applied=None,
            condition_removed=None,
            maneuver_type=None,
            target_defeated=False,
            additional_targets=(),
            causal_chain_id="chain_001",
            chain_position=1,
        )
        assert "triggered by a prior action" not in summary

    def test_causal_chain_from_nested_payload(self, frozen):
        """causal_chain_id in nested payload (not top-level) is extracted."""
        events = [
            {
                "event_id": 1,
                "type": "bull_rush_declared",
                "payload": {
                    "attacker_id": "fighter_1",
                    "target_id": "goblin_1",
                    "is_charge": True,
                    "causal_chain_id": "charge_1_fighter_1",
                    "chain_position": 1,
                },
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="bull_rush_success",
            frozen_view=frozen,
        )
        assert brief.causal_chain_id == "charge_1_fighter_1"
        assert brief.chain_position == 1


# ==============================================================================
# CONDITION_REMOVED TRUTHCHANNEL BUG FIX
# ==============================================================================


class TestConditionRemovedBugFix:
    """Tests for condition_removed reaching TruthChannel (was dropped)."""

    def test_condition_removed_in_truth_channel(self):
        """condition_removed from NarrativeBrief reaches TruthChannel."""
        brief = NarrativeBrief(
            action_type="condition_removed",
            actor_name="system",
            target_name="Goblin",
            condition_removed="prone",
        )
        builder = PromptPackBuilder()
        pack = builder.build(brief=brief)
        assert pack.truth.condition_removed == "prone"

    def test_condition_removed_in_serialized_output(self):
        """condition_removed appears in serialized TruthChannel."""
        brief = NarrativeBrief(
            action_type="condition_removed",
            actor_name="system",
            target_name="Goblin",
            condition_removed="stunned",
        )
        builder = PromptPackBuilder()
        pack = builder.build(brief=brief)
        text = pack.serialize()
        assert "Condition Removed: stunned" in text

    def test_condition_removed_in_to_dict(self):
        """condition_removed appears in PromptPack.to_dict()."""
        brief = NarrativeBrief(
            action_type="condition_removed",
            actor_name="system",
            target_name="Goblin",
            condition_removed="paralyzed",
        )
        builder = PromptPackBuilder()
        pack = builder.build(brief=brief)
        d = pack.to_dict()
        assert d["truth"]["condition_removed"] == "paralyzed"


# ==============================================================================
# NARRATIVEBRIEF SERIALIZATION ROUND-TRIP
# ==============================================================================


class TestSerializationRoundTrip:
    """Tests for new field serialization in NarrativeBrief to_dict/from_dict."""

    def test_additional_targets_round_trip(self):
        """additional_targets survives to_dict/from_dict round trip."""
        brief = NarrativeBrief(
            action_type="spell_damage_dealt",
            actor_name="Elara",
            additional_targets=(
                ("Goblin Warrior", "severe", False),
                ("Goblin Archer", "lethal", True),
            ),
        )
        data = brief.to_dict()
        assert len(data["additional_targets"]) == 2
        assert data["additional_targets"][0] == {"name": "Goblin Warrior", "severity": "severe", "defeated": False}

        restored = NarrativeBrief.from_dict(data)
        assert restored.additional_targets == brief.additional_targets

    def test_causal_chain_round_trip(self):
        """causal_chain_id and chain_position survive round trip."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
            causal_chain_id="chain_test_001",
            chain_position=2,
        )
        data = brief.to_dict()
        assert data["causal_chain_id"] == "chain_test_001"
        assert data["chain_position"] == 2

        restored = NarrativeBrief.from_dict(data)
        assert restored.causal_chain_id == "chain_test_001"
        assert restored.chain_position == 2

    def test_conditions_round_trip(self):
        """active_conditions and actor_conditions survive round trip."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
            active_conditions=("grappled", "prone"),
            actor_conditions=("haste",),
        )
        data = brief.to_dict()
        assert data["active_conditions"] == ["grappled", "prone"]
        assert data["actor_conditions"] == ["haste"]

        restored = NarrativeBrief.from_dict(data)
        assert restored.active_conditions == ("grappled", "prone")
        assert restored.actor_conditions == ("haste",)

    def test_new_fields_backward_compatible_defaults(self):
        """New fields have backward-compatible defaults."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
        )
        assert brief.additional_targets == ()
        assert brief.causal_chain_id is None
        assert brief.chain_position == 0
        assert brief.active_conditions == ()
        assert brief.actor_conditions == ()

    def test_from_dict_missing_new_fields(self):
        """from_dict handles missing new fields gracefully."""
        data = {
            "action_type": "attack_hit",
            "actor_name": "Aldric",
        }
        brief = NarrativeBrief.from_dict(data)
        assert brief.additional_targets == ()
        assert brief.causal_chain_id is None
        assert brief.chain_position == 0
        assert brief.active_conditions == ()
        assert brief.actor_conditions == ()


# ==============================================================================
# PROMPTPACKBUILDER NEW FIELD PROPAGATION
# ==============================================================================


class TestPromptPackBuilderNewFields:
    """Tests for PromptPackBuilder carrying new fields to TruthChannel."""

    def test_additional_targets_in_truth(self):
        """additional_targets propagates from brief to TruthChannel."""
        brief = NarrativeBrief(
            action_type="spell_damage_dealt",
            actor_name="Elara",
            target_name="Goblin Warrior",
            additional_targets=(
                ("Goblin Archer", "moderate", False),
            ),
        )
        builder = PromptPackBuilder()
        pack = builder.build(brief=brief)
        assert pack.truth.additional_targets == [{"name": "Goblin Archer", "severity": "moderate", "defeated": False}]

    def test_causal_chain_in_truth(self):
        """causal_chain_id propagates to TruthChannel."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
            causal_chain_id="chain_123",
            chain_position=2,
        )
        builder = PromptPackBuilder()
        pack = builder.build(brief=brief)
        assert pack.truth.causal_chain_id == "chain_123"
        assert pack.truth.chain_position == 2

    def test_conditions_in_truth(self):
        """active_conditions and actor_conditions propagate to TruthChannel."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
            active_conditions=("prone", "grappled"),
            actor_conditions=("haste",),
        )
        builder = PromptPackBuilder()
        pack = builder.build(brief=brief)
        assert pack.truth.active_conditions == ["prone", "grappled"]
        assert pack.truth.actor_conditions == ["haste"]

    def test_empty_additional_targets_is_none(self):
        """Empty additional_targets produces None in TruthChannel."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
        )
        builder = PromptPackBuilder()
        pack = builder.build(brief=brief)
        assert pack.truth.additional_targets is None
        assert pack.truth.causal_chain_id is None
        assert pack.truth.active_conditions is None

    def test_serialized_additional_targets(self):
        """additional_targets appears in serialized output."""
        brief = NarrativeBrief(
            action_type="spell_damage_dealt",
            actor_name="Elara",
            target_name="Goblin Warrior",
            additional_targets=(
                ("Goblin Archer", "moderate", False),
                ("Goblin Shaman", "severe", True),
            ),
        )
        builder = PromptPackBuilder()
        pack = builder.build(brief=brief)
        text = pack.serialize()
        assert "Additional Targets:" in text
        assert "Goblin Archer" in text
        assert "Goblin Shaman" in text

    def test_serialized_causal_chain(self):
        """Causal chain appears in serialized output."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
            causal_chain_id="bull_rush_1",
            chain_position=2,
        )
        builder = PromptPackBuilder()
        pack = builder.build(brief=brief)
        text = pack.serialize()
        assert "Causal Chain: bull_rush_1 (position 2)" in text

    def test_serialized_conditions(self):
        """Target/actor conditions appear in serialized output."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
            target_name="Goblin",
            active_conditions=("grappled", "prone"),
            actor_conditions=("haste",),
        )
        builder = PromptPackBuilder()
        pack = builder.build(brief=brief)
        text = pack.serialize()
        assert "Target Conditions:" in text
        assert "Actor Conditions:" in text


# ==============================================================================
# BACKWARD COMPATIBILITY
# ==============================================================================


class TestBackwardCompatibility:
    """Ensure single-target, standalone events work exactly as before."""

    def test_single_target_unchanged(self, simple_frozen):
        """Single-target attack produces identical brief to pre-WO-BRIEF-WIDTH-001."""
        events = [
            {
                "event_id": 1,
                "type": "attack_roll",
                "attacker": "fighter_1",
                "target": "goblin_1",
                "weapon": "longsword",
            },
            {
                "event_id": 2,
                "type": "damage_dealt",
                "attacker": "fighter_1",
                "target": "goblin_1",
                "damage": 4,
                "damage_type": "slashing",
            },
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=simple_frozen,
        )
        assert brief.action_type == "attack_hit"
        assert brief.actor_name == "Aldric the Bold"
        assert brief.target_name == "Goblin Warrior"
        assert brief.additional_targets == ()
        assert brief.causal_chain_id is None
        assert brief.chain_position == 0
        assert brief.weapon_name == "longsword"
        assert brief.damage_type == "slashing"
