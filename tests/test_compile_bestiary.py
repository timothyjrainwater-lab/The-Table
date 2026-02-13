"""Tests for Stage 5: Bestiary Generation.

WO-COMPILE-BESTIARY-001 — Verifies that BestiaryStage correctly reads
creature templates from the content pack, generates stub descriptions,
and writes bestiary.json conforming to the BestiaryRegistry schema.
"""

import json

import pytest

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.core.compile_stages.bestiary import (
    BestiaryStage,
    _stub_appearance,
    _stub_habitat,
    _stub_behavior,
    _derive_vfx_tags,
    _derive_sfx_tags,
)
from aidm.schemas.bestiary import (
    AbilityScores,
    BestiaryEntry,
    BestiaryProvenance,
    BestiaryRegistry,
)


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


SAMPLE_CREATURES = [
    {
        "template_id": "CREATURE_0001",
        "size_category": "small",
        "creature_type": "humanoid",
        "subtypes": ["goblinoid"],
        "hit_dice": "1d8+1",
        "hp_typical": 5,
        "initiative_mod": 1,
        "speed_ft": 30,
        "ac_total": 15,
        "ac_touch": 12,
        "ac_flat_footed": 13,
        "bab": 1,
        "grapple_mod": -3,
        "fort_save": 3,
        "ref_save": 1,
        "will_save": -1,
        "str_score": 11,
        "dex_score": 13,
        "con_score": 12,
        "int_score": 10,
        "wis_score": 9,
        "cha_score": 6,
        "special_attacks": [],
        "special_qualities": ["darkvision_60ft"],
        "cr": 0.333,
        "intelligence_band": "average",
        "environment_tags": ["temperate_plains"],
        "organization_patterns": ["gang_4_9"],
    },
    {
        "template_id": "CREATURE_0002",
        "size_category": "large",
        "creature_type": "dragon",
        "subtypes": ["fire"],
        "hit_dice": "13d12+39",
        "hp_typical": 123,
        "initiative_mod": 0,
        "speed_ft": 40,
        "ac_total": 22,
        "ac_touch": 9,
        "ac_flat_footed": 22,
        "bab": 13,
        "grapple_mod": 23,
        "fort_save": 11,
        "ref_save": 8,
        "will_save": 10,
        "str_score": 23,
        "dex_score": 10,
        "con_score": 17,
        "int_score": 12,
        "wis_score": 13,
        "cha_score": 12,
        "special_attacks": ["breath_weapon", "frightful_presence"],
        "special_qualities": ["damage_reduction_5_magic", "spell_resistance_19"],
        "cr": 8.0,
        "intelligence_band": "average",
        "environment_tags": ["warm_mountains"],
        "organization_patterns": ["solitary"],
    },
    {
        "template_id": "CREATURE_0003",
        "size_category": "medium",
        "creature_type": "undead",
        "subtypes": [],
        "hit_dice": "2d12",
        "hp_typical": 16,
        "initiative_mod": -1,
        "speed_ft": 30,
        "ac_total": 11,
        "ac_touch": 9,
        "ac_flat_footed": 11,
        "bab": 1,
        "grapple_mod": 2,
        "fort_save": 0,
        "ref_save": -1,
        "will_save": 3,
        "str_score": 13,
        "dex_score": 8,
        "con_score": None,
        "int_score": None,
        "wis_score": 10,
        "cha_score": 1,
        "special_attacks": [],
        "special_qualities": ["undead_traits"],
        "cr": 0.5,
        "intelligence_band": "mindless",
        "environment_tags": [],
        "organization_patterns": ["group_2_5"],
    },
]


def _write_creatures(tmp_path, creatures=None):
    """Write sample creatures to a content pack directory."""
    if creatures is None:
        creatures = SAMPLE_CREATURES
    creatures_path = tmp_path / "creatures.json"
    with open(creatures_path, "w", encoding="utf-8") as f:
        json.dump({"creatures": creatures}, f)
    return tmp_path


def _make_context(tmp_path, content_pack_dir=None):
    """Create a CompileContext for testing."""
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    if content_pack_dir is None:
        content_pack_dir = tmp_path
    return CompileContext(
        content_pack_dir=content_pack_dir,
        workspace_dir=workspace,
        world_seed=42,
        world_theme_brief={"genre": "dark_fantasy", "tone": "grim", "naming_style": "anglo_saxon"},
        toolchain_pins={"llm_model_id": "stub", "hash_algorithm": "sha256", "schema_version": "1.0.0"},
        content_pack_id="test_pack_001",
        world_id="a" * 32,
    )


@pytest.fixture
def creatures_dir(tmp_path):
    """Content pack dir with 3 sample creatures."""
    return _write_creatures(tmp_path)


@pytest.fixture
def bestiary_result(tmp_path, creatures_dir):
    """Execute BestiaryStage and return result + context."""
    context = _make_context(tmp_path, content_pack_dir=creatures_dir)
    stage = BestiaryStage()
    result = stage.execute(context)
    return result, context


@pytest.fixture
def bestiary_data(bestiary_result):
    """Load the bestiary.json output as a dict."""
    result, context = bestiary_result
    output_path = context.workspace_dir / "bestiary.json"
    with open(output_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def bestiary_registry(bestiary_data):
    """Load bestiary output into a BestiaryRegistry."""
    return BestiaryRegistry.from_dict(bestiary_data)


# ═══════════════════════════════════════════════════════════════════════
# Test 1: Stage interface compliance
# ═══════════════════════════════════════════════════════════════════════


class TestStageInterface:
    def test_is_compile_stage(self):
        assert isinstance(BestiaryStage(), CompileStage)

    def test_stage_id(self):
        assert BestiaryStage().stage_id == "bestiary"

    def test_stage_number(self):
        assert BestiaryStage().stage_number == 5

    def test_depends_on_lexicon(self):
        assert "lexicon" in BestiaryStage().depends_on

    def test_depends_on_is_tuple(self):
        assert isinstance(BestiaryStage().depends_on, tuple)

    def test_execute_returns_stage_result(self, bestiary_result):
        result, _ = bestiary_result
        assert isinstance(result, StageResult)

    def test_execute_succeeds(self, bestiary_result):
        result, _ = bestiary_result
        assert result.status == "success"

    def test_output_files_contains_bestiary(self, bestiary_result):
        result, _ = bestiary_result
        assert "bestiary.json" in result.output_files


# ═══════════════════════════════════════════════════════════════════════
# Test 2: Creature count and content
# ═══════════════════════════════════════════════════════════════════════


class TestCreatureOutput:
    def test_correct_creature_count(self, bestiary_data):
        assert bestiary_data["creature_count"] == 3

    def test_entries_match_count(self, bestiary_data):
        assert len(bestiary_data["entries"]) == bestiary_data["creature_count"]

    def test_content_ids_correct(self, bestiary_data):
        ids = [e["content_id"] for e in bestiary_data["entries"]]
        assert "creature.creature_0001" in ids
        assert "creature.creature_0002" in ids
        assert "creature.creature_0003" in ids

    def test_world_name_set(self, bestiary_data):
        for entry in bestiary_data["entries"]:
            assert entry["world_name"]

    def test_size_category_preserved(self, bestiary_data):
        entry_map = {e["content_id"]: e for e in bestiary_data["entries"]}
        assert entry_map["creature.creature_0001"]["size_category"] == "small"
        assert entry_map["creature.creature_0002"]["size_category"] == "large"

    def test_creature_type_preserved(self, bestiary_data):
        entry_map = {e["content_id"]: e for e in bestiary_data["entries"]}
        assert entry_map["creature.creature_0001"]["creature_type"] == "humanoid"
        assert entry_map["creature.creature_0002"]["creature_type"] == "dragon"

    def test_cr_preserved(self, bestiary_data):
        entry_map = {e["content_id"]: e for e in bestiary_data["entries"]}
        assert entry_map["creature.creature_0002"]["cr"] == 8.0

    def test_mechanical_stats_preserved(self, bestiary_data):
        entry_map = {e["content_id"]: e for e in bestiary_data["entries"]}
        dragon = entry_map["creature.creature_0002"]
        assert dragon["hp_typical"] == 123
        assert dragon["ac_total"] == 22
        assert dragon["speed_ft"] == 40
        assert dragon["fort_save"] == 11

    def test_ability_scores_preserved(self, bestiary_data):
        entry_map = {e["content_id"]: e for e in bestiary_data["entries"]}
        dragon = entry_map["creature.creature_0002"]
        assert dragon["ability_scores"]["str"] == 23

    def test_none_ability_scores_omitted(self, bestiary_data):
        entry_map = {e["content_id"]: e for e in bestiary_data["entries"]}
        undead = entry_map["creature.creature_0003"]
        assert "con" not in undead["ability_scores"]
        assert "int" not in undead["ability_scores"]


# ═══════════════════════════════════════════════════════════════════════
# Test 3: Stub descriptions
# ═══════════════════════════════════════════════════════════════════════


class TestStubDescriptions:
    def test_appearance_not_empty(self, bestiary_data):
        for entry in bestiary_data["entries"]:
            assert entry["appearance"]

    def test_habitat_not_empty(self, bestiary_data):
        for entry in bestiary_data["entries"]:
            assert entry["habitat"]

    def test_behavior_summary_not_empty(self, bestiary_data):
        for entry in bestiary_data["entries"]:
            assert entry["behavior_summary"]

    def test_appearance_mentions_size(self):
        creature = {"size_category": "huge", "creature_type": "dragon", "ac_total": 22}
        text = _stub_appearance(creature)
        assert "massive" in text

    def test_habitat_uses_environment_tags(self):
        creature = {"environment_tags": ["warm_desert"], "creature_type": "beast"}
        text = _stub_habitat(creature)
        assert "warm_desert" in text

    def test_habitat_uses_default_when_no_tags(self):
        creature = {"environment_tags": [], "creature_type": "undead"}
        text = _stub_habitat(creature)
        assert "ruins" in text

    def test_behavior_uses_intelligence_band(self):
        creature = {"intelligence_band": "genius", "cr": 15, "special_attacks": []}
        text = _stub_behavior(creature)
        assert "formidable intelligence" in text


# ═══════════════════════════════════════════════════════════════════════
# Test 4: VFX/SFX tags
# ═══════════════════════════════════════════════════════════════════════


class TestPresentationTags:
    def test_dragon_has_elemental_aura(self):
        tags = _derive_vfx_tags({"creature_type": "dragon", "size_category": "medium"})
        assert "elemental_aura" in tags

    def test_undead_has_shadow(self):
        tags = _derive_vfx_tags({"creature_type": "undead", "size_category": "medium"})
        assert "shadow" in tags

    def test_huge_creature_has_ground_shake(self):
        tags = _derive_vfx_tags({"creature_type": "animal", "size_category": "huge"})
        assert "ground_shake" in tags

    def test_generic_creature_gets_default_vfx(self):
        tags = _derive_vfx_tags({"creature_type": "vermin", "size_category": "small"})
        assert "generic_creature" in tags

    def test_undead_sfx_has_moan(self):
        tags = _derive_sfx_tags({"creature_type": "undead", "size_category": "medium"})
        assert "moan" in tags

    def test_animal_sfx_has_growl(self):
        tags = _derive_sfx_tags({"creature_type": "animal", "size_category": "medium"})
        assert "growl" in tags


# ═══════════════════════════════════════════════════════════════════════
# Test 5: Registry schema compliance
# ═══════════════════════════════════════════════════════════════════════


class TestRegistrySchema:
    def test_schema_version_set(self, bestiary_data):
        assert bestiary_data["schema_version"] == "1.0"

    def test_world_id_set(self, bestiary_data):
        assert bestiary_data["world_id"] == "a" * 32

    def test_compiler_version_set(self, bestiary_data):
        assert bestiary_data["compiler_version"] == "0.1.0"

    def test_habitat_distribution_present(self, bestiary_data):
        assert "habitat_distribution" in bestiary_data

    def test_habitat_distribution_populated(self, bestiary_data):
        dist = bestiary_data["habitat_distribution"]
        assert len(dist) > 0

    def test_habitat_references_valid_content_ids(self, bestiary_data):
        entry_ids = {e["content_id"] for e in bestiary_data["entries"]}
        for habitat, ids in bestiary_data["habitat_distribution"].items():
            for cid in ids:
                assert cid in entry_ids, f"{cid} in habitat {habitat} not in entries"


# ═══════════════════════════════════════════════════════════════════════
# Test 6: Round-trip serialization
# ═══════════════════════════════════════════════════════════════════════


class TestRoundTrip:
    def test_entry_round_trip(self, bestiary_data):
        for entry_dict in bestiary_data["entries"]:
            entry = BestiaryEntry.from_dict(entry_dict)
            rebuilt = entry.to_dict()
            # Check key fields match
            assert rebuilt["content_id"] == entry_dict["content_id"]
            assert rebuilt["creature_type"] == entry_dict["creature_type"]
            assert rebuilt["cr"] == entry_dict["cr"]

    def test_registry_round_trip(self, bestiary_data):
        registry = BestiaryRegistry.from_dict(bestiary_data)
        rebuilt = registry.to_dict()
        assert rebuilt["schema_version"] == bestiary_data["schema_version"]
        assert rebuilt["creature_count"] == bestiary_data["creature_count"]
        assert len(rebuilt["entries"]) == len(bestiary_data["entries"])

    def test_provenance_round_trip(self, bestiary_data):
        for entry_dict in bestiary_data["entries"]:
            prov = BestiaryProvenance.from_dict(entry_dict["provenance"])
            rebuilt = prov.to_dict()
            assert rebuilt == entry_dict["provenance"]

    def test_ability_scores_round_trip(self):
        scores = AbilityScores(str_score=18, dex_score=14, con_score=None)
        d = scores.to_dict()
        rebuilt = AbilityScores.from_dict(d)
        assert rebuilt.str_score == 18
        assert rebuilt.dex_score == 14
        assert rebuilt.con_score is None


# ═══════════════════════════════════════════════════════════════════════
# Test 7: Determinism
# ═══════════════════════════════════════════════════════════════════════


class TestDeterminism:
    def test_same_input_same_output(self, tmp_path):
        """Same creatures + same seed → identical bestiary.json."""
        outputs = []
        for i in range(2):
            run_dir = tmp_path / f"run_{i}"
            run_dir.mkdir()
            _write_creatures(run_dir)
            context = _make_context(run_dir, content_pack_dir=run_dir)
            stage = BestiaryStage()
            stage.execute(context)
            with open(context.workspace_dir / "bestiary.json") as f:
                outputs.append(json.load(f))
        assert outputs[0] == outputs[1]

    def test_entries_sorted_by_content_id(self, bestiary_data):
        ids = [e["content_id"] for e in bestiary_data["entries"]]
        assert ids == sorted(ids)


# ═══════════════════════════════════════════════════════════════════════
# Test 8: No duplicate content IDs
# ═══════════════════════════════════════════════════════════════════════


class TestNoDuplicates:
    def test_unique_content_ids(self, bestiary_data):
        ids = [e["content_id"] for e in bestiary_data["entries"]]
        assert len(ids) == len(set(ids))

    def test_duplicate_template_ids_deduplicated(self, tmp_path):
        """If content pack has duplicate template_ids, only first is kept."""
        dupes = [SAMPLE_CREATURES[0], SAMPLE_CREATURES[0].copy()]
        _write_creatures(tmp_path, dupes)
        context = _make_context(tmp_path, content_pack_dir=tmp_path)
        result = BestiaryStage().execute(context)
        assert result.status == "success"
        with open(context.workspace_dir / "bestiary.json") as f:
            data = json.load(f)
        assert data["creature_count"] == 1


# ═══════════════════════════════════════════════════════════════════════
# Test 9: Edge cases
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_content_pack_succeeds(self, tmp_path):
        """No creatures.json → success with 0 entries."""
        context = _make_context(tmp_path)
        result = BestiaryStage().execute(context)
        assert result.status == "success"
        with open(context.workspace_dir / "bestiary.json") as f:
            data = json.load(f)
        assert data["creature_count"] == 0

    def test_creatures_as_list_format(self, tmp_path):
        """Content pack with creatures as bare list (not nested dict)."""
        creatures_path = tmp_path / "creatures.json"
        with open(creatures_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_CREATURES[:1], f)
        context = _make_context(tmp_path, content_pack_dir=tmp_path)
        result = BestiaryStage().execute(context)
        assert result.status == "success"
        with open(context.workspace_dir / "bestiary.json") as f:
            data = json.load(f)
        assert data["creature_count"] == 1

    def test_provenance_has_correct_seed(self, bestiary_data):
        for entry in bestiary_data["entries"]:
            assert entry["provenance"]["seed_used"] == 42

    def test_provenance_has_correct_pack_id(self, bestiary_data):
        for entry in bestiary_data["entries"]:
            assert entry["provenance"]["content_pack_id"] == "test_pack_001"

    def test_provenance_has_template_id(self, bestiary_data):
        for entry in bestiary_data["entries"]:
            assert len(entry["provenance"]["template_ids"]) == 1

    def test_special_attacks_preserved(self, bestiary_data):
        entry_map = {e["content_id"]: e for e in bestiary_data["entries"]}
        dragon = entry_map["creature.creature_0002"]
        assert "breath_weapon" in dragon["special_attacks"]

    def test_special_qualities_preserved(self, bestiary_data):
        entry_map = {e["content_id"]: e for e in bestiary_data["entries"]}
        goblin = entry_map["creature.creature_0001"]
        assert "darkvision_60ft" in goblin["special_qualities"]
