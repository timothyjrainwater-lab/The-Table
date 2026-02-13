"""Tests for WO-RULEBOOK-MODEL-001: Rulebook Object Model.

Covers:
1. Frozen dataclass rejects mutation
2. to_dict() / from_dict() round-trip preserves all fields
3. Registry rejects duplicate content_ids
4. get_entry() returns correct entry
5. get_entry() returns None for unknown ID
6. search() finds entries by world_name substring
7. search() is case-insensitive
8. list_by_category() returns sorted results
9. list_all() returns all entries sorted by content_id
10. Empty registry is valid
"""

import json
import tempfile
from pathlib import Path

import pytest

from aidm.schemas.rulebook import (
    RuleEntry,
    RuleParameters,
    RuleTextSlots,
    RuleProvenance,
    Prerequisite,
)
from aidm.lens.rulebook_registry import (
    RulebookRegistry,
    DuplicateContentIdError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_provenance(**overrides):
    defaults = {
        "source": "world_compiler",
        "compiler_version": "0.1.0",
        "seed_used": 42,
        "content_pack_id": "base_3.5e_v1",
    }
    defaults.update(overrides)
    return RuleProvenance(**defaults)


def _make_entry(
    content_id: str,
    world_name: str,
    rule_type: str = "spell",
    procedure_id: str = "proc.ranged_burst_damage",
    **kwargs,
):
    defaults = {
        "content_id": content_id,
        "procedure_id": procedure_id,
        "rule_type": rule_type,
        "world_name": world_name,
        "parameters": RuleParameters(
            range_ft=120,
            area_shape="burst",
            area_radius_ft=20,
            damage_dice="6d6",
            damage_type="fire",
            save_type="reflex",
            save_effect="half",
            duration_unit="instantaneous",
            action_cost="standard",
            target_type="area",
        ),
        "provenance": _make_provenance(),
        "text_slots": RuleTextSlots(
            rulebook_description=f"Description of {world_name}.",
            short_description=f"A {rule_type} called {world_name}.",
            mechanical_summary=f"Deals fire damage in a burst.",
        ),
        "tags": ("fire", "area_effect"),
    }
    defaults.update(kwargs)
    return RuleEntry(**defaults)


FIXTURE_ENTRIES = [
    _make_entry(
        content_id="spell.fire_burst_003",
        world_name="Searing Detonation",
        rule_type="spell",
        procedure_id="proc.ranged_burst_damage",
        text_slots=RuleTextSlots(
            rulebook_description="A sphere of searing energy erupts at the target point.",
            short_description="Explosive fire burst at range.",
            flavor_text="The air itself seems to scream.",
            mechanical_summary="Launches a bolt that detonates in a 20-foot burst.",
        ),
        tags=("fire", "area_effect", "evocation"),
    ),
    _make_entry(
        content_id="feat.iron_stance",
        world_name="Iron Stance",
        rule_type="feat",
        procedure_id="proc.passive_modifier",
        parameters=RuleParameters(custom={"ac_bonus": 1}),
        text_slots=RuleTextSlots(
            rulebook_description="You plant your feet and become harder to move.",
            short_description="Bonus to AC when stationary.",
            mechanical_summary="+1 AC when you haven't moved this round.",
        ),
        tags=("defensive", "stance"),
        prerequisites=(
            Prerequisite(
                prerequisite_type="ability_score",
                ref="str:13",
                display="Strength 13",
            ),
        ),
    ),
    _make_entry(
        content_id="skill.shadow_step",
        world_name="Shadow Step",
        rule_type="skill",
        procedure_id="proc.skill_check",
        parameters=RuleParameters(action_cost="move", target_type="self"),
        text_slots=RuleTextSlots(
            rulebook_description="You meld with nearby shadows to reposition.",
            short_description="Move through shadows.",
            mechanical_summary="Move action, Hide check to reposition via shadow.",
        ),
        tags=("stealth", "movement"),
    ),
    _make_entry(
        content_id="combat_maneuver.whirlwind_sweep",
        world_name="Whirlwind Sweep",
        rule_type="combat_maneuver",
        procedure_id="proc.melee_area",
        parameters=RuleParameters(
            area_shape="emanation",
            area_radius_ft=5,
            damage_dice="1d8",
            damage_type="slashing",
            action_cost="full_round",
            target_type="area",
        ),
        text_slots=RuleTextSlots(
            rulebook_description="You spin with your weapon, striking all adjacent foes.",
            short_description="Attack all adjacent enemies.",
            mechanical_summary="Full-round action, one attack roll vs each adjacent foe.",
        ),
        tags=("melee", "area_effect"),
    ),
    _make_entry(
        content_id="spell.glacial_barrier",
        world_name="Glacial Barrier",
        rule_type="spell",
        procedure_id="proc.create_barrier",
        parameters=RuleParameters(
            range_ft=60,
            duration_unit="rounds",
            duration_value=5,
            action_cost="standard",
            target_type="area",
            damage_type="cold",
        ),
        text_slots=RuleTextSlots(
            rulebook_description="A wall of solid ice forms at the designated location.",
            short_description="Create a wall of ice.",
            flavor_text="Frost crackles along the ground before the wall rises.",
            mechanical_summary="Creates a 10-ft wall of ice for 5 rounds.",
        ),
        tags=("cold", "barrier", "conjuration"),
    ),
]


def _fixture_registry() -> RulebookRegistry:
    return RulebookRegistry(
        entries=list(FIXTURE_ENTRIES),
        schema_version="1.0",
        world_id="a" * 32,
        compiler_version="0.1.0",
    )


def _fixture_registry_dict():
    return {
        "schema_version": "1.0",
        "world_id": "a" * 32,
        "compiler_version": "0.1.0",
        "entry_count": len(FIXTURE_ENTRIES),
        "entries": [e.to_dict() for e in FIXTURE_ENTRIES],
    }


# ---------------------------------------------------------------------------
# Test 1: Frozen dataclass rejects mutation
# ---------------------------------------------------------------------------

class TestFrozenDataclasses:
    def test_rule_entry_rejects_mutation(self):
        entry = FIXTURE_ENTRIES[0]
        with pytest.raises(AttributeError):
            entry.world_name = "Hacked Name"

    def test_rule_parameters_rejects_mutation(self):
        params = RuleParameters(range_ft=120)
        with pytest.raises(AttributeError):
            params.range_ft = 999

    def test_rule_text_slots_rejects_mutation(self):
        slots = RuleTextSlots(short_description="Original")
        with pytest.raises(AttributeError):
            slots.short_description = "Hacked"

    def test_rule_provenance_rejects_mutation(self):
        prov = _make_provenance()
        with pytest.raises(AttributeError):
            prov.source = "hacked"

    def test_prerequisite_rejects_mutation(self):
        prereq = Prerequisite(prerequisite_type="feat", ref="feat.dodge")
        with pytest.raises(AttributeError):
            prereq.ref = "hacked"


# ---------------------------------------------------------------------------
# Test 2: to_dict() / from_dict() round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_rule_entry_round_trip(self):
        for entry in FIXTURE_ENTRIES:
            d = entry.to_dict()
            restored = RuleEntry.from_dict(d)
            assert restored.content_id == entry.content_id
            assert restored.procedure_id == entry.procedure_id
            assert restored.rule_type == entry.rule_type
            assert restored.world_name == entry.world_name
            assert restored.tier == entry.tier
            assert restored.tags == entry.tags
            assert restored.supersedes == entry.supersedes
            # Verify nested round-trip
            assert restored.parameters.range_ft == entry.parameters.range_ft
            assert restored.parameters.damage_dice == entry.parameters.damage_dice
            assert restored.text_slots.rulebook_description == entry.text_slots.rulebook_description
            assert restored.text_slots.short_description == entry.text_slots.short_description
            assert restored.provenance.source == entry.provenance.source
            assert restored.provenance.seed_used == entry.provenance.seed_used

    def test_rule_entry_round_trip_with_prerequisites(self):
        entry = FIXTURE_ENTRIES[1]  # Iron Stance has prerequisites
        d = entry.to_dict()
        restored = RuleEntry.from_dict(d)
        assert len(restored.prerequisites) == 1
        assert restored.prerequisites[0].prerequisite_type == "ability_score"
        assert restored.prerequisites[0].ref == "str:13"
        assert restored.prerequisites[0].display == "Strength 13"

    def test_rule_parameters_round_trip_with_custom(self):
        params = RuleParameters(custom={"ac_bonus": 1, "stacks": False})
        d = params.to_dict()
        restored = RuleParameters.from_dict(d)
        assert restored.custom == {"ac_bonus": 1, "stacks": False}

    def test_registry_dict_round_trip(self):
        reg_dict = _fixture_registry_dict()
        registry = RulebookRegistry.from_dict(reg_dict)
        assert registry.entry_count == len(FIXTURE_ENTRIES)
        assert registry.schema_version == "1.0"
        assert registry.world_id == "a" * 32


# ---------------------------------------------------------------------------
# Test 3: Registry rejects duplicate content_ids
# ---------------------------------------------------------------------------

class TestDuplicateRejection:
    def test_duplicate_content_id_raises(self):
        duplicate = _make_entry(
            content_id="spell.fire_burst_003",
            world_name="Duplicate Entry",
        )
        with pytest.raises(DuplicateContentIdError, match="Duplicate content_id"):
            RulebookRegistry(entries=[FIXTURE_ENTRIES[0], duplicate])


# ---------------------------------------------------------------------------
# Test 4: get_entry() returns correct entry
# ---------------------------------------------------------------------------

class TestGetEntry:
    def test_get_existing_entry(self):
        registry = _fixture_registry()
        entry = registry.get_entry("spell.fire_burst_003")
        assert entry is not None
        assert entry.world_name == "Searing Detonation"
        assert entry.rule_type == "spell"

    def test_get_entry_with_prerequisites(self):
        registry = _fixture_registry()
        entry = registry.get_entry("feat.iron_stance")
        assert entry is not None
        assert len(entry.prerequisites) == 1


# ---------------------------------------------------------------------------
# Test 5: get_entry() returns None for unknown ID
# ---------------------------------------------------------------------------

class TestGetEntryMissing:
    def test_unknown_id_returns_none(self):
        registry = _fixture_registry()
        assert registry.get_entry("spell.nonexistent") is None

    def test_empty_string_returns_none(self):
        registry = _fixture_registry()
        assert registry.get_entry("") is None


# ---------------------------------------------------------------------------
# Test 6: search() finds entries by world_name substring
# ---------------------------------------------------------------------------

class TestSearch:
    def test_search_by_world_name(self):
        registry = _fixture_registry()
        results = registry.search("Searing")
        assert len(results) == 1
        assert results[0].content_id == "spell.fire_burst_003"

    def test_search_by_rule_text(self):
        registry = _fixture_registry()
        results = registry.search("wall of solid ice")
        assert len(results) == 1
        assert results[0].content_id == "spell.glacial_barrier"

    def test_search_by_category(self):
        registry = _fixture_registry()
        results = registry.search("combat_maneuver")
        assert len(results) == 1
        assert results[0].content_id == "combat_maneuver.whirlwind_sweep"

    def test_search_no_results(self):
        registry = _fixture_registry()
        results = registry.search("nonexistent_ability_xyz")
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Test 7: search() is case-insensitive
# ---------------------------------------------------------------------------

class TestSearchCaseInsensitive:
    def test_lowercase_query(self):
        registry = _fixture_registry()
        results = registry.search("searing")
        assert len(results) == 1

    def test_uppercase_query(self):
        registry = _fixture_registry()
        results = registry.search("SEARING")
        assert len(results) == 1

    def test_mixed_case_query(self):
        registry = _fixture_registry()
        results = registry.search("sEaRiNg")
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Test 8: list_by_category() returns sorted results
# ---------------------------------------------------------------------------

class TestListByCategory:
    def test_list_spells_sorted_by_world_name(self):
        registry = _fixture_registry()
        spells = registry.list_by_category("spell")
        assert len(spells) == 2
        # Glacial Barrier < Searing Detonation alphabetically
        assert spells[0].world_name == "Glacial Barrier"
        assert spells[1].world_name == "Searing Detonation"

    def test_list_empty_category(self):
        registry = _fixture_registry()
        results = registry.list_by_category("creature_trait")
        assert results == []


# ---------------------------------------------------------------------------
# Test 9: list_all() returns all entries sorted by content_id
# ---------------------------------------------------------------------------

class TestListAll:
    def test_all_entries_sorted(self):
        registry = _fixture_registry()
        all_entries = registry.list_all()
        assert len(all_entries) == 5
        ids = [e.content_id for e in all_entries]
        assert ids == sorted(ids)

    def test_all_entries_present(self):
        registry = _fixture_registry()
        all_entries = registry.list_all()
        all_ids = {e.content_id for e in all_entries}
        expected_ids = {e.content_id for e in FIXTURE_ENTRIES}
        assert all_ids == expected_ids


# ---------------------------------------------------------------------------
# Test 10: Empty registry is valid
# ---------------------------------------------------------------------------

class TestEmptyRegistry:
    def test_empty_registry(self):
        registry = RulebookRegistry.empty()
        assert registry.entry_count == 0
        assert registry.list_all() == []
        assert registry.get_entry("anything") is None
        assert registry.search("anything") == []
        assert registry.list_by_category("spell") == []

    def test_empty_registry_from_dict(self):
        registry = RulebookRegistry.from_dict({"entries": []})
        assert registry.entry_count == 0


# ---------------------------------------------------------------------------
# Test 11: JSON file round-trip
# ---------------------------------------------------------------------------

class TestJsonFileRoundTrip:
    def test_load_from_json_file(self, tmp_path):
        reg_dict = _fixture_registry_dict()
        json_path = tmp_path / "rule_registry.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(reg_dict, f)

        registry = RulebookRegistry.from_json_file(json_path)
        assert registry.entry_count == 5
        assert registry.get_entry("spell.fire_burst_003") is not None

    def test_load_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            RulebookRegistry.from_json_file(tmp_path / "missing.json")


# ---------------------------------------------------------------------------
# Test 12: RuleEntry convenience properties
# ---------------------------------------------------------------------------

class TestConvenienceProperties:
    def test_rule_text_property(self):
        entry = FIXTURE_ENTRIES[0]
        assert entry.rule_text == entry.text_slots.rulebook_description

    def test_category_property(self):
        entry = FIXTURE_ENTRIES[0]
        assert entry.category == entry.rule_type
