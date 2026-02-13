"""Tests for WO-WORLDCOMPILE-NPC-001: NPC Archetype + Doctrine Profile Stage.

Covers:
1. Stub mode produces 8 archetypes + 6 doctrines
2. Output round-trips via to_dict/from_dict
3. All archetype_ids are unique
4. All doctrine_ids are unique
5. Retreat threshold is between 0.0 and 1.0
6. Doctrine can be converted to MonsterDoctrine format
7. Stub mode is deterministic (same seed -> same output)
8. Stage registers with WorldCompiler correctly
"""

import json
from pathlib import Path

import pytest

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.core.compile_stages.npc_archetypes import (
    NPCArchetypeStage,
    _build_stub_archetypes,
    _build_stub_doctrines,
    _derive_npc_seed,
)
from aidm.schemas.npc_archetype import (
    DoctrineProfile,
    NPCArchetype,
    NPCArchetypeRegistry,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

WORLD_SEED = 42
CONTENT_PACK_ID = "test_pack_minimal"
THEME_BRIEF = {
    "genre": "generic_fantasy",
    "tone": "neutral",
    "naming_style": "simple_english",
}
TOOLCHAIN_PINS = {
    "llm_model_id": "stub",
    "hash_algorithm": "sha256",
    "schema_version": "1.0",
}


@pytest.fixture()
def content_pack_dir(tmp_path):
    """Create a minimal content pack directory."""
    pack_dir = tmp_path / "content_pack"
    pack_dir.mkdir()
    # NPC stage doesn't read content pack files directly in stub mode,
    # but the directory must exist for the compile context.
    return pack_dir


@pytest.fixture()
def workspace_dir(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


@pytest.fixture()
def compile_context(content_pack_dir, workspace_dir):
    return CompileContext(
        content_pack_dir=content_pack_dir,
        workspace_dir=workspace_dir,
        world_seed=WORLD_SEED,
        world_theme_brief=THEME_BRIEF,
        toolchain_pins=TOOLCHAIN_PINS,
        content_pack_id=CONTENT_PACK_ID,
    )


@pytest.fixture()
def npc_result(compile_context):
    stage = NPCArchetypeStage()
    return stage.execute(compile_context)


@pytest.fixture()
def archetypes_dict(compile_context, npc_result):
    path = compile_context.workspace_dir / "npc_archetypes.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture()
def doctrines_dict(compile_context, npc_result):
    path = compile_context.workspace_dir / "doctrine_profiles.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Test 1: Stub mode produces 8 archetypes + 6 doctrines
# ---------------------------------------------------------------------------


class TestStubCounts:
    def test_8_archetypes_produced(self, archetypes_dict):
        assert len(archetypes_dict["archetypes"]) == 8

    def test_6_doctrines_produced(self, doctrines_dict):
        assert len(doctrines_dict["doctrines"]) == 6

    def test_builder_functions_produce_correct_counts(self):
        archetypes = _build_stub_archetypes(WORLD_SEED, CONTENT_PACK_ID)
        doctrines = _build_stub_doctrines(WORLD_SEED, CONTENT_PACK_ID)
        assert len(archetypes) == 8
        assert len(doctrines) == 6

    def test_metadata_reports_counts(self, npc_result):
        # StageResult no longer carries metadata; verify via output files
        assert "npc_archetypes.json" in npc_result.output_files
        assert "doctrine_profiles.json" in npc_result.output_files


# ---------------------------------------------------------------------------
# Test 2: Output round-trips via to_dict/from_dict
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_archetype_round_trip(self, archetypes_dict):
        """Each archetype dict round-trips through NPCArchetype."""
        for a_dict in archetypes_dict["archetypes"]:
            archetype = NPCArchetype.from_dict(a_dict)
            rebuilt = archetype.to_dict()
            assert rebuilt == a_dict

    def test_doctrine_round_trip(self, doctrines_dict):
        """Each doctrine dict round-trips through DoctrineProfile."""
        for d_dict in doctrines_dict["doctrines"]:
            doctrine = DoctrineProfile.from_dict(d_dict)
            rebuilt = doctrine.to_dict()
            assert rebuilt == d_dict

    def test_registry_round_trip(self, archetypes_dict, doctrines_dict):
        """Full registry round-trips through NPCArchetypeRegistry."""
        combined = {
            "schema_version": archetypes_dict["schema_version"],
            "world_id": archetypes_dict["world_id"],
            "archetypes": archetypes_dict["archetypes"],
            "doctrines": doctrines_dict["doctrines"],
        }
        registry = NPCArchetypeRegistry.from_dict(combined)
        rebuilt = registry.to_dict()
        assert rebuilt == combined


# ---------------------------------------------------------------------------
# Test 3: All archetype_ids are unique
# ---------------------------------------------------------------------------


class TestArchetypeIdUniqueness:
    def test_all_archetype_ids_unique(self, archetypes_dict):
        ids = [a["archetype_id"] for a in archetypes_dict["archetypes"]]
        assert len(ids) == len(set(ids))

    def test_archetype_ids_have_correct_prefix(self, archetypes_dict):
        for a in archetypes_dict["archetypes"]:
            assert a["archetype_id"].startswith("archetype_")


# ---------------------------------------------------------------------------
# Test 4: All doctrine_ids are unique
# ---------------------------------------------------------------------------


class TestDoctrineIdUniqueness:
    def test_all_doctrine_ids_unique(self, doctrines_dict):
        ids = [d["doctrine_id"] for d in doctrines_dict["doctrines"]]
        assert len(ids) == len(set(ids))

    def test_doctrine_ids_have_correct_prefix(self, doctrines_dict):
        for d in doctrines_dict["doctrines"]:
            assert d["doctrine_id"].startswith("doctrine_")


# ---------------------------------------------------------------------------
# Test 5: Retreat threshold is between 0.0 and 1.0
# ---------------------------------------------------------------------------


class TestRetreatThreshold:
    def test_retreat_threshold_in_range(self, doctrines_dict):
        for d in doctrines_dict["doctrines"]:
            rt = d["retreat_threshold"]
            assert 0.0 <= rt <= 1.0, (
                f"Retreat threshold out of range for {d['doctrine_id']}: {rt}"
            )

    def test_retreat_threshold_is_float(self, doctrines_dict):
        for d in doctrines_dict["doctrines"]:
            assert isinstance(d["retreat_threshold"], (int, float))


# ---------------------------------------------------------------------------
# Test 6: Doctrine can be converted to MonsterDoctrine format
# ---------------------------------------------------------------------------


class TestDoctrineConversion:
    def test_doctrine_converts_to_monster_doctrine(self, doctrines_dict):
        """Each doctrine produces a valid MonsterDoctrine-compatible dict."""
        for d_dict in doctrines_dict["doctrines"]:
            doctrine = DoctrineProfile.from_dict(d_dict)
            monster_dict = doctrine.to_monster_doctrine(
                monster_id=f"test_{doctrine.doctrine_id}",
                source="test",
            )
            # Required MonsterDoctrine fields present
            assert "monster_id" in monster_dict
            assert "source" in monster_dict
            assert "creature_type" in monster_dict
            assert "tags" in monster_dict
            assert isinstance(monster_dict["tags"], list)

    def test_monster_doctrine_has_allowed_tactics(self, doctrines_dict):
        """Converted doctrine includes mapped tactics."""
        for d_dict in doctrines_dict["doctrines"]:
            doctrine = DoctrineProfile.from_dict(d_dict)
            monster_dict = doctrine.to_monster_doctrine(monster_id="test")
            assert "allowed_tactics" in monster_dict
            assert isinstance(monster_dict["allowed_tactics"], list)

    def test_monster_doctrine_creature_type_from_first(self, doctrines_dict):
        """creature_type comes from the first element of creature_types."""
        for d_dict in doctrines_dict["doctrines"]:
            doctrine = DoctrineProfile.from_dict(d_dict)
            monster_dict = doctrine.to_monster_doctrine(monster_id="test")
            if doctrine.creature_types:
                assert monster_dict["creature_type"] == doctrine.creature_types[0]

    def test_monster_doctrine_retreat_in_notes(self):
        """Retreat threshold is encoded in notes."""
        doctrine = DoctrineProfile(
            doctrine_id="doctrine_test",
            creature_types=("beast",),
            aggression="cautious",
            retreat_threshold=0.3,
            pack_behavior="solo",
            preferred_tactics=("ambush",),
            morale="cowardly",
            special_behaviors=("guards_lair",),
            provenance={},
        )
        monster_dict = doctrine.to_monster_doctrine(monster_id="test")
        assert "30%" in monster_dict["notes"]
        assert "guards_lair" in monster_dict["notes"]

    def test_monster_doctrine_from_dict_import(self):
        """The converted dict can be used with MonsterDoctrine.from_dict."""
        from aidm.schemas.doctrine import MonsterDoctrine

        doctrine = DoctrineProfile(
            doctrine_id="doctrine_test",
            creature_types=("beast",),
            aggression="aggressive",
            retreat_threshold=0.25,
            pack_behavior="pack",
            preferred_tactics=("flank", "charge"),
            morale="steady",
            special_behaviors=(),
            provenance={},
        )
        monster_dict = doctrine.to_monster_doctrine(
            monster_id="test_beast",
            source="world_compiler",
        )
        md = MonsterDoctrine.from_dict(monster_dict)
        assert md.monster_id == "test_beast"
        assert md.source == "world_compiler"
        assert md.creature_type == "beast"


# ---------------------------------------------------------------------------
# Test 7: Stub mode is deterministic (same seed -> same output)
# ---------------------------------------------------------------------------


class TestStubDeterminism:
    def test_same_seed_same_output(self, content_pack_dir, tmp_path):
        """Running twice with the same seed produces identical output."""
        outputs = []
        for run in range(2):
            ws = tmp_path / f"ws_{run}"
            ws.mkdir()
            ctx = CompileContext(
                content_pack_dir=content_pack_dir,
                workspace_dir=ws,
                world_seed=WORLD_SEED,
                world_theme_brief=THEME_BRIEF,
                toolchain_pins=TOOLCHAIN_PINS,
                content_pack_id=CONTENT_PACK_ID,
            )
            stage = NPCArchetypeStage()
            result = stage.execute(ctx)
            assert result.status == "success"

            with open(ws / "npc_archetypes.json", "r", encoding="utf-8") as f:
                archetypes = json.load(f)
            with open(ws / "doctrine_profiles.json", "r", encoding="utf-8") as f:
                doctrines = json.load(f)
            outputs.append((archetypes, doctrines))

        assert outputs[0] == outputs[1]

    def test_different_seed_same_structure(self, content_pack_dir, tmp_path):
        """Different seeds produce same structure (8 archetypes, 6 doctrines)."""
        for seed in [42, 9999, 0]:
            ws = tmp_path / f"ws_seed_{seed}"
            ws.mkdir()
            ctx = CompileContext(
                content_pack_dir=content_pack_dir,
                workspace_dir=ws,
                world_seed=seed,
                world_theme_brief=THEME_BRIEF,
                toolchain_pins=TOOLCHAIN_PINS,
                content_pack_id=CONTENT_PACK_ID,
            )
            stage = NPCArchetypeStage()
            result = stage.execute(ctx)
            assert result.status == "success"

            with open(ws / "npc_archetypes.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            assert len(data["archetypes"]) == 8

    def test_seed_derivation_deterministic(self):
        """_derive_npc_seed is deterministic."""
        seed_a = _derive_npc_seed(42)
        seed_b = _derive_npc_seed(42)
        assert seed_a == seed_b

    def test_seed_derivation_varies_with_input(self):
        """Different world seeds produce different NPC seeds."""
        seed_a = _derive_npc_seed(42)
        seed_b = _derive_npc_seed(9999)
        assert seed_a != seed_b


# ---------------------------------------------------------------------------
# Test 8: Stage registers with WorldCompiler correctly
# ---------------------------------------------------------------------------


class TestStageInterface:
    def test_is_compile_stage(self):
        stage = NPCArchetypeStage()
        assert isinstance(stage, CompileStage)

    def test_stage_id(self):
        stage = NPCArchetypeStage()
        assert stage.stage_id == "npc_archetypes"

    def test_stage_number(self):
        stage = NPCArchetypeStage()
        assert stage.stage_number == 4

    def test_depends_on_lexicon(self):
        stage = NPCArchetypeStage()
        assert stage.depends_on == ("lexicon",)

    def test_depends_on_is_tuple(self):
        stage = NPCArchetypeStage()
        assert isinstance(stage.depends_on, tuple)

    def test_execute_returns_stage_result(self, compile_context):
        stage = NPCArchetypeStage()
        result = stage.execute(compile_context)
        assert isinstance(result, StageResult)
        assert result.stage_id == "npc_archetypes"
        assert result.status == "success"

    def test_output_files_list(self, npc_result):
        assert "npc_archetypes.json" in npc_result.output_files
        assert "doctrine_profiles.json" in npc_result.output_files


# ---------------------------------------------------------------------------
# Extra: File output validation
# ---------------------------------------------------------------------------


class TestFileOutput:
    def test_npc_archetypes_json_exists(self, compile_context, npc_result):
        assert npc_result.status == "success"
        path = compile_context.workspace_dir / "npc_archetypes.json"
        assert path.exists()

    def test_doctrine_profiles_json_exists(self, compile_context, npc_result):
        assert npc_result.status == "success"
        path = compile_context.workspace_dir / "doctrine_profiles.json"
        assert path.exists()

    def test_npc_archetypes_has_schema_version(self, archetypes_dict):
        assert "schema_version" in archetypes_dict
        assert archetypes_dict["schema_version"] == "1.0"

    def test_doctrine_profiles_has_schema_version(self, doctrines_dict):
        assert "schema_version" in doctrines_dict
        assert doctrines_dict["schema_version"] == "1.0"

    def test_both_files_share_world_id(self, archetypes_dict, doctrines_dict):
        assert archetypes_dict["world_id"] == doctrines_dict["world_id"]
        assert archetypes_dict["world_id"] != ""


# ---------------------------------------------------------------------------
# Extra: Schema validation
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_archetypes_have_required_fields(self, archetypes_dict):
        required = {
            "archetype_id", "world_name", "personality_traits",
            "speech_register", "knowledge_domains", "behavioral_constraints",
            "interaction_hooks", "voice_description", "provenance",
        }
        for a in archetypes_dict["archetypes"]:
            assert required.issubset(a.keys()), (
                f"Missing fields in {a.get('archetype_id', '?')}: "
                f"{required - set(a.keys())}"
            )

    def test_doctrines_have_required_fields(self, doctrines_dict):
        required = {
            "doctrine_id", "creature_types", "aggression",
            "retreat_threshold", "pack_behavior", "preferred_tactics",
            "morale", "special_behaviors", "provenance",
        }
        for d in doctrines_dict["doctrines"]:
            assert required.issubset(d.keys()), (
                f"Missing fields in {d.get('doctrine_id', '?')}: "
                f"{required - set(d.keys())}"
            )

    def test_aggression_values_valid(self, doctrines_dict):
        valid = {"timid", "cautious", "aggressive", "berserk"}
        for d in doctrines_dict["doctrines"]:
            assert d["aggression"] in valid

    def test_pack_behavior_values_valid(self, doctrines_dict):
        valid = {"solo", "pair", "pack", "swarm"}
        for d in doctrines_dict["doctrines"]:
            assert d["pack_behavior"] in valid

    def test_morale_values_valid(self, doctrines_dict):
        valid = {"cowardly", "steady", "fanatical"}
        for d in doctrines_dict["doctrines"]:
            assert d["morale"] in valid

    def test_speech_register_values_valid(self, archetypes_dict):
        valid = {"formal", "colloquial", "archaic"}
        for a in archetypes_dict["archetypes"]:
            assert a["speech_register"] in valid

    def test_archetype_frozen(self):
        """NPCArchetype is frozen (immutable)."""
        a = NPCArchetype(
            archetype_id="test",
            world_name="Test",
            personality_traits=("a",),
            speech_register="formal",
            knowledge_domains=("b",),
            behavioral_constraints=("c",),
            interaction_hooks=("d",),
            voice_description="test",
            provenance={},
        )
        with pytest.raises(AttributeError):
            a.archetype_id = "changed"  # type: ignore[misc]

    def test_doctrine_frozen(self):
        """DoctrineProfile is frozen (immutable)."""
        d = DoctrineProfile(
            doctrine_id="test",
            creature_types=("beast",),
            aggression="cautious",
            retreat_threshold=0.5,
            pack_behavior="solo",
            preferred_tactics=("ambush",),
            morale="steady",
            special_behaviors=(),
            provenance={},
        )
        with pytest.raises(AttributeError):
            d.doctrine_id = "changed"  # type: ignore[misc]

    def test_registry_frozen(self):
        """NPCArchetypeRegistry is frozen (immutable)."""
        r = NPCArchetypeRegistry(
            schema_version="1.0",
            world_id="test",
            archetypes=(),
            doctrines=(),
        )
        with pytest.raises(AttributeError):
            r.schema_version = "2.0"  # type: ignore[misc]
