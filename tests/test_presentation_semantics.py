"""WO-AD007-IMPL-001: Presentation Semantics enforcement tests.

Tests:
  1. All enum values match the JSON schema exactly
  2. Frozen dataclass rejects mutation (TypeError on attribute set)
  3. to_dict() / from_dict() round-trip preserves all fields
  4. Registry loader validates entry counts
  5. Registry loader rejects duplicate content_id
  6. Registry lookup returns correct entry by content_id
  7. Registry returns None for unknown content_id
  8. NarrativeBrief includes presentation semantics when available
"""

import json
from pathlib import Path

import pytest

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
from aidm.lens.presentation_registry import (
    PresentationRegistryLoader,
    RegistryValidationError,
)


# ═══════════════════════════════════════════════════════════════════════
# Test fixtures
# ═══════════════════════════════════════════════════════════════════════

def _make_provenance(**overrides) -> SemanticsProvenance:
    """Build a minimal SemanticsProvenance for tests."""
    defaults = {
        "source": "world_compiler",
        "compiler_version": "0.1.0",
        "seed_used": 42,
    }
    defaults.update(overrides)
    return SemanticsProvenance(**defaults)


def _make_ability_entry(content_id: str = "spell.fireball", **overrides):
    """Build a minimal AbilityPresentationEntry for tests."""
    defaults = {
        "content_id": content_id,
        "delivery_mode": DeliveryMode.PROJECTILE,
        "staging": Staging.TRAVEL_THEN_DETONATE,
        "origin_rule": OriginRule.FROM_CASTER,
        "vfx_tags": ("fire", "expanding_ring", "scorch"),
        "sfx_tags": ("boom", "crackle"),
        "scale": Scale.DRAMATIC,
        "provenance": _make_provenance(),
        "residue": ("scorch_marks", "smoke"),
        "ui_description": "A streaking ball of fire that detonates on impact.",
        "contraindications": ("erupting_from_ground",),
    }
    defaults.update(overrides)
    return AbilityPresentationEntry(**defaults)


def _make_event_entry(
    event_category: EventCategory = EventCategory.MELEE_ATTACK,
    **overrides,
):
    """Build a minimal EventPresentationEntry for tests."""
    defaults = {
        "event_category": event_category,
        "default_scale": Scale.MODERATE,
        "default_vfx_tags": ("impact",),
        "default_sfx_tags": ("clang",),
        "default_residue": (),
        "narration_priority": NarrationPriority.ALWAYS_NARRATE,
    }
    defaults.update(overrides)
    return EventPresentationEntry(**defaults)


def _make_registry(
    ability_entries=None,
    event_entries=None,
    ability_entry_count=None,
    event_entry_count=None,
):
    """Build a minimal PresentationSemanticsRegistry for tests."""
    abilities = ability_entries if ability_entries is not None else (
        _make_ability_entry("spell.fireball"),
    )
    events = event_entries if event_entries is not None else (
        _make_event_entry(EventCategory.MELEE_ATTACK),
    )
    return PresentationSemanticsRegistry(
        schema_version="1.0",
        world_id="a" * 32,
        compiler_version="0.1.0",
        ability_entry_count=(
            ability_entry_count if ability_entry_count is not None
            else len(abilities)
        ),
        event_entry_count=(
            event_entry_count if event_entry_count is not None
            else len(events)
        ),
        ability_entries=abilities,
        event_entries=events,
    )


# ═══════════════════════════════════════════════════════════════════════
# Test 1: Enum values match JSON schema exactly
# ═══════════════════════════════════════════════════════════════════════

class TestEnumValuesMatchSchema:
    """All enum values must match the JSON schema exactly."""

    @pytest.fixture(scope="class")
    def schema(self):
        """Load the canonical JSON schema."""
        schema_path = Path("docs/schemas/presentation_semantics_registry.schema.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_delivery_mode_values(self, schema):
        """DeliveryMode enum matches JSON schema delivery_mode enum."""
        schema_values = set(
            schema["$defs"]["AbilityPresentationEntry"]
            ["properties"]["delivery_mode"]["enum"]
        )
        python_values = {m.value for m in DeliveryMode}
        assert python_values == schema_values, (
            f"DeliveryMode mismatch:\n"
            f"  Python-only: {python_values - schema_values}\n"
            f"  Schema-only: {schema_values - python_values}"
        )

    def test_staging_values(self, schema):
        """Staging enum matches JSON schema staging enum."""
        schema_values = set(
            schema["$defs"]["AbilityPresentationEntry"]
            ["properties"]["staging"]["enum"]
        )
        python_values = {s.value for s in Staging}
        assert python_values == schema_values

    def test_origin_rule_values(self, schema):
        """OriginRule enum matches JSON schema origin_rule enum."""
        schema_values = set(
            schema["$defs"]["AbilityPresentationEntry"]
            ["properties"]["origin_rule"]["enum"]
        )
        python_values = {o.value for o in OriginRule}
        assert python_values == schema_values

    def test_scale_values(self, schema):
        """Scale enum matches JSON schema scale enum."""
        schema_values = set(
            schema["$defs"]["AbilityPresentationEntry"]
            ["properties"]["scale"]["enum"]
        )
        python_values = {s.value for s in Scale}
        assert python_values == schema_values

    def test_narration_priority_values(self, schema):
        """NarrationPriority enum matches JSON schema narration_priority enum."""
        schema_values = set(
            schema["$defs"]["EventPresentationEntry"]
            ["properties"]["narration_priority"]["enum"]
        )
        python_values = {n.value for n in NarrationPriority}
        assert python_values == schema_values

    def test_event_category_values(self, schema):
        """EventCategory enum matches JSON schema event_category enum."""
        schema_values = set(
            schema["$defs"]["EventPresentationEntry"]
            ["properties"]["event_category"]["enum"]
        )
        python_values = {e.value for e in EventCategory}
        assert python_values == schema_values


# ═══════════════════════════════════════════════════════════════════════
# Test 2: Frozen dataclass rejects mutation
# ═══════════════════════════════════════════════════════════════════════

class TestFrozenRejectsMutation:
    """All frozen dataclasses must reject attribute mutation."""

    def test_provenance_rejects_mutation(self):
        prov = _make_provenance()
        with pytest.raises(AttributeError):
            prov.source = "tampered"

    def test_ability_entry_rejects_mutation(self):
        entry = _make_ability_entry()
        with pytest.raises(AttributeError):
            entry.content_id = "tampered"

    def test_ability_entry_rejects_scale_mutation(self):
        entry = _make_ability_entry()
        with pytest.raises(AttributeError):
            entry.scale = Scale.SUBTLE

    def test_event_entry_rejects_mutation(self):
        entry = _make_event_entry()
        with pytest.raises(AttributeError):
            entry.event_category = EventCategory.REST

    def test_registry_rejects_mutation(self):
        reg = _make_registry()
        with pytest.raises(AttributeError):
            reg.schema_version = "tampered"


# ═══════════════════════════════════════════════════════════════════════
# Test 3: to_dict() / from_dict() round-trip preserves all fields
# ═══════════════════════════════════════════════════════════════════════

class TestRoundTrip:
    """to_dict() → from_dict() must preserve every field value."""

    def test_provenance_round_trip(self):
        prov = SemanticsProvenance(
            source="world_compiler",
            compiler_version="0.1.0",
            seed_used=42,
            content_pack_id="srd_3.5e",
            template_ids=("tpl_fire", "tpl_generic"),
            llm_output_hash="abc123def456",
        )
        d = prov.to_dict()
        restored = SemanticsProvenance.from_dict(d)
        assert restored.source == prov.source
        assert restored.compiler_version == prov.compiler_version
        assert restored.seed_used == prov.seed_used
        assert restored.content_pack_id == prov.content_pack_id
        assert restored.template_ids == prov.template_ids
        assert restored.llm_output_hash == prov.llm_output_hash

    def test_provenance_round_trip_minimal(self):
        """Provenance with only required fields round-trips."""
        prov = _make_provenance()
        d = prov.to_dict()
        restored = SemanticsProvenance.from_dict(d)
        assert restored == prov

    def test_ability_entry_round_trip_full(self):
        entry = AbilityPresentationEntry(
            content_id="spell.fireball",
            delivery_mode=DeliveryMode.PROJECTILE,
            staging=Staging.TRAVEL_THEN_DETONATE,
            origin_rule=OriginRule.FROM_CASTER,
            vfx_tags=("fire", "expanding_ring", "scorch"),
            sfx_tags=("boom", "crackle"),
            scale=Scale.DRAMATIC,
            provenance=SemanticsProvenance(
                source="world_compiler",
                compiler_version="0.1.0",
                seed_used=42,
                content_pack_id="srd_3.5e",
                template_ids=("tpl_fire",),
                llm_output_hash="deadbeef",
            ),
            residue=("scorch_marks", "smoke", "heated_air"),
            ui_description="A streaking ball of fire.",
            token_style="fire_circle",
            handout_style="bordered_red",
            contraindications=("erupting_from_ground",),
        )
        d = entry.to_dict()
        restored = AbilityPresentationEntry.from_dict(d)
        assert restored == entry

    def test_ability_entry_round_trip_minimal(self):
        """Ability entry with only required fields round-trips."""
        entry = AbilityPresentationEntry(
            content_id="spell.magic_missile",
            delivery_mode=DeliveryMode.PROJECTILE,
            staging=Staging.INSTANT,
            origin_rule=OriginRule.FROM_CASTER,
            vfx_tags=("force", "glowing"),
            sfx_tags=("whoosh",),
            scale=Scale.SUBTLE,
            provenance=_make_provenance(),
        )
        d = entry.to_dict()
        restored = AbilityPresentationEntry.from_dict(d)
        assert restored == entry

    def test_event_entry_round_trip(self):
        entry = EventPresentationEntry(
            event_category=EventCategory.ENTITY_DEFEATED,
            default_scale=Scale.DRAMATIC,
            default_vfx_tags=("collapse", "blood"),
            default_sfx_tags=("thud",),
            default_residue=("body",),
            narration_priority=NarrationPriority.ALWAYS_NARRATE,
        )
        d = entry.to_dict()
        restored = EventPresentationEntry.from_dict(d)
        assert restored == entry

    def test_event_entry_round_trip_defaults(self):
        """Event entry with defaults round-trips."""
        entry = EventPresentationEntry(
            event_category=EventCategory.TURN_BOUNDARY,
            default_scale=Scale.SUBTLE,
            default_vfx_tags=(),
            default_sfx_tags=(),
        )
        d = entry.to_dict()
        restored = EventPresentationEntry.from_dict(d)
        assert restored == entry

    def test_registry_round_trip(self):
        reg = _make_registry()
        d = reg.to_dict()
        restored = PresentationSemanticsRegistry.from_dict(d)
        assert restored.schema_version == reg.schema_version
        assert restored.world_id == reg.world_id
        assert len(restored.ability_entries) == len(reg.ability_entries)
        assert len(restored.event_entries) == len(reg.event_entries)
        assert restored.ability_entries[0] == reg.ability_entries[0]
        assert restored.event_entries[0] == reg.event_entries[0]

    def test_registry_json_round_trip(self, tmp_path):
        """Registry survives JSON serialization (file → load → compare)."""
        reg = _make_registry()
        d = reg.to_dict()

        json_path = tmp_path / "test_registry.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(d, f, sort_keys=True)

        loader = PresentationRegistryLoader.from_json_file(json_path)
        restored = loader.registry
        assert restored.schema_version == reg.schema_version
        assert restored.ability_entries[0] == reg.ability_entries[0]

    def test_to_dict_field_names_match_schema(self):
        """to_dict() output keys must match JSON schema property names."""
        entry = _make_ability_entry()
        d = entry.to_dict()
        expected_keys = {
            "content_id", "delivery_mode", "staging", "origin_rule",
            "vfx_tags", "sfx_tags", "scale", "provenance",
            "residue", "contraindications",
            # Optional keys included only when not None
        }
        # All required keys present
        for key in expected_keys:
            assert key in d, f"Missing key: {key}"
        # Values are strings/lists, not Enum objects
        assert isinstance(d["delivery_mode"], str)
        assert isinstance(d["scale"], str)
        assert isinstance(d["vfx_tags"], list)


# ═══════════════════════════════════════════════════════════════════════
# Test 4: Registry loader validates entry counts
# ═══════════════════════════════════════════════════════════════════════

class TestRegistryValidation:
    """Registry loader must validate integrity on load."""

    def test_valid_registry_loads(self):
        reg = _make_registry()
        loader = PresentationRegistryLoader(reg)
        assert loader.registry is reg

    def test_ability_count_mismatch_raises(self):
        reg = _make_registry(ability_entry_count=99)
        with pytest.raises(RegistryValidationError, match="ability_entry_count"):
            PresentationRegistryLoader(reg)

    def test_event_count_mismatch_raises(self):
        reg = _make_registry(event_entry_count=99)
        with pytest.raises(RegistryValidationError, match="event_entry_count"):
            PresentationRegistryLoader(reg)


# ═══════════════════════════════════════════════════════════════════════
# Test 5: Registry loader rejects duplicate content_id
# ═══════════════════════════════════════════════════════════════════════

class TestRegistryRejectsDuplicates:
    """Registry must reject duplicate content_id or event_category."""

    def test_duplicate_content_id_raises(self):
        abilities = (
            _make_ability_entry("spell.fireball"),
            _make_ability_entry("spell.fireball"),  # duplicate
        )
        reg = _make_registry(
            ability_entries=abilities,
            ability_entry_count=2,
        )
        with pytest.raises(RegistryValidationError, match="duplicate content_id"):
            PresentationRegistryLoader(reg)

    def test_duplicate_event_category_raises(self):
        events = (
            _make_event_entry(EventCategory.MELEE_ATTACK),
            _make_event_entry(EventCategory.MELEE_ATTACK),  # duplicate
        )
        reg = _make_registry(
            event_entries=events,
            event_entry_count=2,
        )
        with pytest.raises(RegistryValidationError, match="duplicate event_category"):
            PresentationRegistryLoader(reg)


# ═══════════════════════════════════════════════════════════════════════
# Test 6: Registry lookup returns correct entry by content_id
# ═══════════════════════════════════════════════════════════════════════

class TestRegistryLookup:
    """Registry provides O(1) lookups by content_id and event_category."""

    def test_lookup_ability_by_content_id(self):
        fireball = _make_ability_entry("spell.fireball")
        magic_missile = _make_ability_entry("spell.magic_missile")
        reg = _make_registry(
            ability_entries=(fireball, magic_missile),
            ability_entry_count=2,
        )
        loader = PresentationRegistryLoader(reg)

        result = loader.get_ability_semantics("spell.fireball")
        assert result is fireball

        result = loader.get_ability_semantics("spell.magic_missile")
        assert result is magic_missile

    def test_lookup_event_by_category(self):
        melee = _make_event_entry(EventCategory.MELEE_ATTACK)
        ranged = _make_event_entry(EventCategory.RANGED_ATTACK)
        reg = _make_registry(
            event_entries=(melee, ranged),
            event_entry_count=2,
        )
        loader = PresentationRegistryLoader(reg)

        result = loader.get_event_semantics(EventCategory.MELEE_ATTACK)
        assert result is melee

        result = loader.get_event_semantics(EventCategory.RANGED_ATTACK)
        assert result is ranged


# ═══════════════════════════════════════════════════════════════════════
# Test 7: Registry returns None for unknown content_id
# ═══════════════════════════════════════════════════════════════════════

class TestRegistryUnknownLookup:
    """Registry returns None for missing entries."""

    def test_unknown_ability_returns_none(self):
        reg = _make_registry()
        loader = PresentationRegistryLoader(reg)
        assert loader.get_ability_semantics("spell.nonexistent") is None

    def test_unknown_event_category_returns_none(self):
        reg = _make_registry()
        loader = PresentationRegistryLoader(reg)
        assert loader.get_event_semantics(EventCategory.REST) is None


# ═══════════════════════════════════════════════════════════════════════
# Test 8: NarrativeBrief includes presentation semantics when available
# ═══════════════════════════════════════════════════════════════════════

class TestNarrativeBriefIntegration:
    """NarrativeBrief must carry presentation semantics when provided."""

    def test_narrative_brief_includes_semantics(self):
        from aidm.lens.narrative_brief import NarrativeBrief

        entry = _make_ability_entry("spell.fireball")
        brief = NarrativeBrief(
            action_type="spell_damage_dealt",
            actor_name="Gandalf",
            target_name="Goblin",
            presentation_semantics=entry,
        )
        assert brief.presentation_semantics is entry
        assert brief.presentation_semantics.content_id == "spell.fireball"
        assert brief.presentation_semantics.delivery_mode == DeliveryMode.PROJECTILE

    def test_narrative_brief_defaults_to_none(self):
        from aidm.lens.narrative_brief import NarrativeBrief

        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Fighter",
        )
        assert brief.presentation_semantics is None

    def test_narrative_brief_to_dict_includes_semantics(self):
        from aidm.lens.narrative_brief import NarrativeBrief

        entry = _make_ability_entry("spell.fireball")
        brief = NarrativeBrief(
            action_type="spell_damage_dealt",
            actor_name="Gandalf",
            presentation_semantics=entry,
        )
        d = brief.to_dict()
        assert d["presentation_semantics"] is not None
        assert d["presentation_semantics"]["content_id"] == "spell.fireball"
        assert d["presentation_semantics"]["delivery_mode"] == "projectile"

    def test_narrative_brief_to_dict_none_semantics(self):
        from aidm.lens.narrative_brief import NarrativeBrief

        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Fighter",
        )
        d = brief.to_dict()
        assert d["presentation_semantics"] is None

    def test_narrative_brief_from_dict_round_trip_with_semantics(self):
        from aidm.lens.narrative_brief import NarrativeBrief

        entry = _make_ability_entry("spell.fireball")
        brief = NarrativeBrief(
            action_type="spell_damage_dealt",
            actor_name="Gandalf",
            target_name="Goblin",
            presentation_semantics=entry,
        )
        d = brief.to_dict()
        restored = NarrativeBrief.from_dict(d)
        assert restored.presentation_semantics is not None
        assert restored.presentation_semantics.content_id == "spell.fireball"
        assert restored.presentation_semantics.delivery_mode == DeliveryMode.PROJECTILE
        assert restored.presentation_semantics.scale == Scale.DRAMATIC

    def test_assemble_narrative_brief_with_semantics(self):
        from aidm.core.state import WorldState, FrozenWorldStateView
        from aidm.lens.narrative_brief import assemble_narrative_brief

        ws = WorldState(
            ruleset_version="3.5e",
            entities={
                "wizard_1": {"name": "Gandalf"},
                "goblin_1": {"name": "Goblin Warrior", "hp": 5, "hp_max": 5},
            },
        )
        view = FrozenWorldStateView(ws)
        entry = _make_ability_entry("spell.fireball")

        events = [
            {
                "event_id": 1,
                "event_type": "spell_cast",
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
            frozen_view=view,
            presentation_semantics=entry,
        )

        assert brief.presentation_semantics is entry
        assert brief.presentation_semantics.delivery_mode == DeliveryMode.PROJECTILE

    def test_assemble_narrative_brief_without_semantics(self):
        from aidm.core.state import WorldState, FrozenWorldStateView
        from aidm.lens.narrative_brief import assemble_narrative_brief

        ws = WorldState(
            ruleset_version="3.5e",
            entities={"orc_1": {"name": "Orc"}},
        )
        view = FrozenWorldStateView(ws)

        events = [
            {
                "event_id": 1,
                "event_type": "attack_roll",
                "payload": {
                    "attacker_id": "orc_1",
                    "target_id": "orc_1",
                },
            },
        ]

        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=view,
        )

        assert brief.presentation_semantics is None
