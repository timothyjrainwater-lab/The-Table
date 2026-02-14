"""Tests for WO-GAP-B-001: Connect Layer B to Narration Pipeline.

Verifies:
- GAP-B-001: assemble_narrative_brief() populates presentation_semantics
  from PresentationRegistryLoader when a matching content_id exists in events
- GAP-B-001: presentation_semantics remains None when no content_id or
  no registry match
- GAP-B-002: TruthChannel serializes Layer B fields when present
- GAP-B-002: TruthChannel Layer B fields are None when no semantics present
- PromptPackBuilder threads Layer B from NarrativeBrief to TruthChannel
"""

import pytest

from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.lens.narrative_brief import NarrativeBrief, assemble_narrative_brief
from aidm.lens.presentation_registry import PresentationRegistryLoader
from aidm.lens.prompt_pack_builder import PromptPackBuilder
from aidm.schemas.presentation_semantics import (
    AbilityPresentationEntry,
    DeliveryMode,
    EventCategory,
    EventPresentationEntry,
    NarrationPriority,
    OriginRule,
    PresentationSemanticsRegistry,
    Scale,
    SemanticsProvenance,
    Staging,
)
from aidm.schemas.prompt_pack import TruthChannel


# ══════════════════════════════════════════════════════════════════════════
# Test Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_provenance():
    return SemanticsProvenance(
        source="world_compiler",
        compiler_version="1.0.0",
        seed_used=42,
    )


def _make_ability_entry(content_id="spell.fireball", **overrides):
    defaults = {
        "content_id": content_id,
        "delivery_mode": DeliveryMode.PROJECTILE,
        "staging": Staging.TRAVEL_THEN_DETONATE,
        "origin_rule": OriginRule.FROM_CASTER,
        "vfx_tags": ("fire", "explosion"),
        "sfx_tags": ("boom", "crackle"),
        "scale": Scale.DRAMATIC,
        "provenance": _make_provenance(),
        "residue": ("scorch_marks",),
        "contraindications": ("no_ice_visual",),
    }
    defaults.update(overrides)
    return AbilityPresentationEntry(**defaults)


def _make_registry(*entries):
    """Build a PresentationRegistryLoader from ability entries."""
    registry = PresentationSemanticsRegistry(
        schema_version="1.0",
        world_id="test_world",
        ability_entries=tuple(entries),
        event_entries=(),
    )
    return PresentationRegistryLoader(registry)


@pytest.fixture
def frozen_view():
    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "wizard_1": {"name": "Gandalf", "hp": 30, "hp_max": 30},
            "goblin_1": {"name": "Goblin Warrior", "hp": 5, "hp_max": 10},
        },
    )
    return FrozenWorldStateView(ws)


@pytest.fixture
def fireball_entry():
    return _make_ability_entry("spell.fireball")


@pytest.fixture
def registry_with_fireball(fireball_entry):
    return _make_registry(fireball_entry)


# ══════════════════════════════════════════════════════════════════════════
# GAP-B-001: assemble_narrative_brief() registry lookup
# ══════════════════════════════════════════════════════════════════════════


class TestGapB001RegistryLookup:
    """assemble_narrative_brief populates presentation_semantics from registry."""

    def test_populates_when_content_id_matches(
        self, frozen_view, fireball_entry, registry_with_fireball,
    ):
        """presentation_semantics populated when event carries matching content_id."""
        events = [
            {
                "event_id": 1,
                "type": "spell_cast",
                "content_id": "spell.fireball",
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
            frozen_view=frozen_view,
            presentation_registry=registry_with_fireball,
        )

        assert brief.presentation_semantics is not None
        assert brief.presentation_semantics is fireball_entry
        assert brief.presentation_semantics.content_id == "spell.fireball"
        assert brief.presentation_semantics.delivery_mode == DeliveryMode.PROJECTILE

    def test_content_id_in_payload(
        self, frozen_view, fireball_entry, registry_with_fireball,
    ):
        """content_id extracted from payload when not on top-level event."""
        events = [
            {
                "event_id": 1,
                "type": "spell_cast",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "fireball",
                    "targets": ["goblin_1"],
                    "content_id": "spell.fireball",
                },
            },
        ]

        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen_view,
            presentation_registry=registry_with_fireball,
        )

        assert brief.presentation_semantics is fireball_entry

    def test_none_when_no_content_id_in_events(
        self, frozen_view, registry_with_fireball,
    ):
        """presentation_semantics remains None when events lack content_id."""
        events = [
            {
                "event_id": 1,
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
            frozen_view=frozen_view,
            presentation_registry=registry_with_fireball,
        )

        assert brief.presentation_semantics is None

    def test_none_when_content_id_not_in_registry(self, frozen_view):
        """presentation_semantics remains None when content_id has no registry match."""
        registry = _make_registry(
            _make_ability_entry("spell.magic_missile"),
        )

        events = [
            {
                "event_id": 1,
                "type": "spell_cast",
                "content_id": "spell.fireball",
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
            frozen_view=frozen_view,
            presentation_registry=registry,
        )

        assert brief.presentation_semantics is None

    def test_none_when_no_registry_provided(self, frozen_view):
        """presentation_semantics remains None when no registry is passed."""
        events = [
            {
                "event_id": 1,
                "type": "spell_cast",
                "content_id": "spell.fireball",
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
            frozen_view=frozen_view,
        )

        assert brief.presentation_semantics is None

    def test_registry_overrides_explicit_semantics(
        self, frozen_view, fireball_entry, registry_with_fireball,
    ):
        """Registry lookup overrides explicitly passed presentation_semantics."""
        other_entry = _make_ability_entry(
            "spell.other",
            delivery_mode=DeliveryMode.BEAM,
        )

        events = [
            {
                "event_id": 1,
                "type": "spell_cast",
                "content_id": "spell.fireball",
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
            frozen_view=frozen_view,
            presentation_semantics=other_entry,
            presentation_registry=registry_with_fireball,
        )

        # Registry result wins over explicitly passed entry
        assert brief.presentation_semantics is fireball_entry

    def test_explicit_semantics_used_when_registry_misses(self, frozen_view):
        """Explicit presentation_semantics used when registry has no match."""
        explicit_entry = _make_ability_entry("spell.other")
        registry = _make_registry(
            _make_ability_entry("spell.magic_missile"),
        )

        events = [
            {
                "event_id": 1,
                "type": "spell_cast",
                "content_id": "spell.lightning_bolt",
                "payload": {
                    "caster_id": "wizard_1",
                    "spell_id": "lightning_bolt",
                    "targets": ["goblin_1"],
                },
            },
        ]

        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen_view,
            presentation_semantics=explicit_entry,
            presentation_registry=registry,
        )

        # Falls back to explicit since registry miss
        assert brief.presentation_semantics is explicit_entry

    def test_non_spell_event_with_content_id(
        self, frozen_view, registry_with_fireball, fireball_entry,
    ):
        """content_id can appear on non-spell events (e.g., damage events)."""
        events = [
            {
                "event_id": 1,
                "type": "damage_dealt",
                "content_id": "spell.fireball",
                "attacker": "wizard_1",
                "target": "goblin_1",
                "damage": 3,
                "damage_type": "fire",
            },
        ]

        brief = assemble_narrative_brief(
            events=events,
            narration_token="spell_damage_dealt",
            frozen_view=frozen_view,
            presentation_registry=registry_with_fireball,
        )

        assert brief.presentation_semantics is fireball_entry


# ══════════════════════════════════════════════════════════════════════════
# GAP-B-002: TruthChannel Layer B serialization
# ══════════════════════════════════════════════════════════════════════════


class TestGapB002TruthChannelLayerB:
    """TruthChannel includes Layer B fields when present."""

    def test_layer_b_fields_present(self):
        """TruthChannel carries Layer B fields."""
        tc = TruthChannel(
            action_type="spell_damage_dealt",
            actor_name="Gandalf",
            target_name="Goblin",
            delivery_mode="projectile",
            staging="travel_then_detonate",
            origin_rule="from_caster",
            scale="dramatic",
            vfx_tags=["fire", "explosion"],
            sfx_tags=["boom", "crackle"],
            residue=["scorch_marks"],
            contraindications=["no_ice_visual"],
        )

        assert tc.delivery_mode == "projectile"
        assert tc.staging == "travel_then_detonate"
        assert tc.origin_rule == "from_caster"
        assert tc.scale == "dramatic"
        assert tc.vfx_tags == ["fire", "explosion"]
        assert tc.sfx_tags == ["boom", "crackle"]
        assert tc.residue == ["scorch_marks"]
        assert tc.contraindications == ["no_ice_visual"]

    def test_layer_b_fields_default_none(self):
        """Layer B fields default to None when not provided."""
        tc = TruthChannel(
            action_type="attack_hit",
            actor_name="Aldric",
        )

        assert tc.delivery_mode is None
        assert tc.staging is None
        assert tc.origin_rule is None
        assert tc.scale is None
        assert tc.vfx_tags is None
        assert tc.sfx_tags is None
        assert tc.residue is None
        assert tc.contraindications is None

    def test_serialize_includes_layer_b(self):
        """PromptPack.serialize() includes Layer B fields in TRUTH section."""
        from aidm.schemas.prompt_pack import PromptPack

        tc = TruthChannel(
            action_type="spell_damage_dealt",
            actor_name="Gandalf",
            delivery_mode="projectile",
            staging="travel_then_detonate",
            scale="dramatic",
            vfx_tags=["fire", "explosion"],
            sfx_tags=["boom"],
            contraindications=["no_ice_visual"],
        )
        pack = PromptPack(truth=tc)
        text = pack.serialize()

        assert "Delivery Mode: projectile" in text
        assert "Staging: travel_then_detonate" in text
        assert "Scale: dramatic" in text
        assert "VFX:" in text
        assert "SFX:" in text
        assert "Contraindications:" in text

    def test_serialize_omits_layer_b_when_none(self):
        """PromptPack.serialize() omits Layer B lines when fields are None."""
        from aidm.schemas.prompt_pack import PromptPack

        tc = TruthChannel(
            action_type="attack_hit",
            actor_name="Aldric",
        )
        pack = PromptPack(truth=tc)
        text = pack.serialize()

        assert "Delivery Mode" not in text
        assert "Staging" not in text
        assert "VFX" not in text
        assert "SFX" not in text
        assert "Contraindications" not in text

    def test_to_dict_includes_layer_b(self):
        """PromptPack.to_dict() includes Layer B in truth section."""
        from aidm.schemas.prompt_pack import PromptPack

        tc = TruthChannel(
            action_type="spell_damage_dealt",
            actor_name="Gandalf",
            delivery_mode="projectile",
            vfx_tags=["fire", "explosion"],
        )
        pack = PromptPack(truth=tc)
        d = pack.to_dict()

        assert d["truth"]["delivery_mode"] == "projectile"
        assert d["truth"]["vfx_tags"] == ["explosion", "fire"]  # sorted

    def test_to_dict_layer_b_null_when_absent(self):
        """PromptPack.to_dict() has null Layer B fields when not set."""
        from aidm.schemas.prompt_pack import PromptPack

        tc = TruthChannel(
            action_type="attack_hit",
            actor_name="Aldric",
        )
        pack = PromptPack(truth=tc)
        d = pack.to_dict()

        assert d["truth"]["delivery_mode"] is None
        assert d["truth"]["vfx_tags"] is None
        assert d["truth"]["contraindications"] is None


# ══════════════════════════════════════════════════════════════════════════
# PromptPackBuilder integration: NarrativeBrief → TruthChannel Layer B
# ══════════════════════════════════════════════════════════════════════════


class TestPromptPackBuilderLayerB:
    """PromptPackBuilder threads Layer B from brief to TruthChannel."""

    def test_layer_b_threaded_to_truth(self):
        """Layer B fields from NarrativeBrief appear in TruthChannel."""
        entry = _make_ability_entry("spell.fireball")
        brief = NarrativeBrief(
            action_type="spell_damage_dealt",
            actor_name="Gandalf",
            target_name="Goblin",
            presentation_semantics=entry,
        )

        builder = PromptPackBuilder()
        pack = builder.build(brief)

        assert pack.truth.delivery_mode == "projectile"
        assert pack.truth.staging == "travel_then_detonate"
        assert pack.truth.origin_rule == "from_caster"
        assert pack.truth.scale == "dramatic"
        assert pack.truth.vfx_tags == ["fire", "explosion"]
        assert pack.truth.sfx_tags == ["boom", "crackle"]
        assert pack.truth.residue == ["scorch_marks"]
        assert pack.truth.contraindications == ["no_ice_visual"]

    def test_layer_b_none_without_semantics(self):
        """Layer B fields are None when brief has no presentation_semantics."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
            target_name="Goblin",
        )

        builder = PromptPackBuilder()
        pack = builder.build(brief)

        assert pack.truth.delivery_mode is None
        assert pack.truth.staging is None
        assert pack.truth.vfx_tags is None
        assert pack.truth.contraindications is None

    def test_end_to_end_registry_to_spark(self, frozen_view):
        """Full pipeline: events → registry lookup → NarrativeBrief → TruthChannel."""
        entry = _make_ability_entry("spell.fireball")
        registry = _make_registry(entry)

        events = [
            {
                "event_id": 1,
                "type": "spell_cast",
                "content_id": "spell.fireball",
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
            frozen_view=frozen_view,
            presentation_registry=registry,
        )

        builder = PromptPackBuilder()
        pack = builder.build(brief)

        # Layer B reaches Spark via TruthChannel
        assert pack.truth.delivery_mode == "projectile"
        assert pack.truth.scale == "dramatic"
        assert pack.truth.vfx_tags == ["fire", "explosion"]
        assert pack.truth.contraindications == ["no_ice_visual"]

        # Serialized text contains Layer B
        text = pack.serialize()
        assert "Delivery Mode: projectile" in text
        assert "Scale: dramatic" in text
