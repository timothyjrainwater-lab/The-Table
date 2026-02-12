"""Tests for WO-WORLDCOMPILE-LEXICON-001: Lexicon Generation Stage.

Covers:
1. Stub mode produces deterministic names (same seed -> same names)
2. Stub mode produces valid VocabularyRegistry (round-trip via from_dict)
3. All template IDs from content pack get a lexicon entry
4. No duplicate content_ids in output
5. No duplicate lexicon_ids in output
6. lexicon_id is deterministic: sha256(seed:content_id)[:16]
7. Short descriptions <= 120 characters
8. Stage registers correctly with WorldCompiler (CompileStage interface)
9. Stage depends_on is empty (no dependencies)
10. Stage writes lexicon.json to workspace
"""

import hashlib
import json
from pathlib import Path

import pytest

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.core.compile_stages.lexicon import (
    LexiconStage,
    _make_lexicon_id,
)
from aidm.schemas.vocabulary import VocabularyEntry, VocabularyRegistry
from aidm.lens.vocabulary_registry import VocabularyRegistryLoader


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_SPELLS = [
    {"template_id": "SPELL_001", "school_category": "evocation", "effect_type": "damage"},
    {"template_id": "SPELL_002", "school_category": "conjuration", "effect_type": "summon"},
    {"template_id": "SPELL_003", "school_category": "abjuration", "effect_type": "protection"},
    {"template_id": "SPELL_004", "school_category": "necromancy", "effect_type": "damage"},
    {"template_id": "SPELL_005", "school_category": "transmutation", "effect_type": "buff"},
]

MINIMAL_CREATURES = {
    "schema_version": "1.0.0",
    "source_id": "test",
    "creature_count": 3,
    "creatures": [
        {"template_id": "CREATURE_0001", "creature_type": "aberration", "size_category": "large"},
        {"template_id": "CREATURE_0002", "creature_type": "beast", "size_category": "medium"},
        {"template_id": "CREATURE_0003", "creature_type": "undead", "size_category": "small"},
    ],
}

MINIMAL_FEATS = {
    "schema_version": "1.0.0",
    "source_id": "test",
    "feat_count": 2,
    "feats": [
        {"template_id": "FEAT_001", "feat_type": "general", "effect_type": "skill_modifier"},
        {"template_id": "FEAT_002", "feat_type": "fighter", "effect_type": "attack_modifier"},
    ],
}

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

EXPECTED_TEMPLATE_IDS = (
    ["SPELL_001", "SPELL_002", "SPELL_003", "SPELL_004", "SPELL_005"]
    + ["CREATURE_0001", "CREATURE_0002", "CREATURE_0003"]
    + ["FEAT_001", "FEAT_002"]
)


@pytest.fixture()
def content_pack_dir(tmp_path):
    """Write minimal content pack JSON files to a temp directory."""
    pack_dir = tmp_path / "content_pack"
    pack_dir.mkdir()

    # spells.json is a bare array
    with open(pack_dir / "spells.json", "w", encoding="utf-8") as f:
        json.dump(MINIMAL_SPELLS, f)

    # creatures.json is an object wrapper
    with open(pack_dir / "creatures.json", "w", encoding="utf-8") as f:
        json.dump(MINIMAL_CREATURES, f)

    # feats.json is an object wrapper
    with open(pack_dir / "feats.json", "w", encoding="utf-8") as f:
        json.dump(MINIMAL_FEATS, f)

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
def lexicon_result(compile_context):
    stage = LexiconStage()
    return stage.execute(compile_context)


@pytest.fixture()
def lexicon_dict(compile_context, lexicon_result):
    lexicon_path = compile_context.workspace_dir / "lexicon.json"
    with open(lexicon_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Test 1: Stub mode produces deterministic names
# ---------------------------------------------------------------------------

class TestStubDeterminism:
    def test_same_seed_same_names(self, content_pack_dir, tmp_path):
        """Running twice with the same seed produces identical output."""
        results = []
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
            stage = LexiconStage()
            result = stage.execute(ctx)
            assert result.success

            with open(ws / "lexicon.json", "r", encoding="utf-8") as f:
                results.append(json.load(f))

        assert results[0] == results[1]

    def test_different_seed_different_names(self, content_pack_dir, tmp_path):
        """Different seeds produce different names."""
        outputs = []
        for seed in [42, 9999]:
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
            stage = LexiconStage()
            result = stage.execute(ctx)
            assert result.success

            with open(ws / "lexicon.json", "r", encoding="utf-8") as f:
                outputs.append(json.load(f))

        # World names differ because seed suffix differs
        names_a = {e["world_name"] for e in outputs[0]["entries"]}
        names_b = {e["world_name"] for e in outputs[1]["entries"]}
        assert names_a != names_b


# ---------------------------------------------------------------------------
# Test 2: Stub mode produces valid VocabularyRegistry (round-trip)
# ---------------------------------------------------------------------------

class TestValidRegistryOutput:
    def test_round_trip_via_from_dict(self, lexicon_dict):
        """Output JSON round-trips through VocabularyRegistry.from_dict."""
        registry = VocabularyRegistry.from_dict(lexicon_dict)
        assert registry.schema_version == "1.0"
        assert len(registry.entries) == 10

    def test_loadable_by_registry_loader(self, lexicon_dict):
        """Output JSON is loadable by VocabularyRegistryLoader.from_dict."""
        loader = VocabularyRegistryLoader.from_dict(lexicon_dict)
        assert loader.entry_count == 10
        assert loader.schema_version == "1.0"

    def test_loadable_from_json_file(self, compile_context, lexicon_result):
        """Output JSON file is loadable by VocabularyRegistryLoader.from_json_file."""
        assert lexicon_result.success
        path = compile_context.workspace_dir / "lexicon.json"
        loader = VocabularyRegistryLoader.from_json_file(path)
        assert loader.entry_count == 10


# ---------------------------------------------------------------------------
# Test 3: All template IDs get a lexicon entry
# ---------------------------------------------------------------------------

class TestAllTemplatesCovered:
    def test_every_template_has_entry(self, lexicon_dict):
        content_ids = {e["content_id"] for e in lexicon_dict["entries"]}

        for tid in EXPECTED_TEMPLATE_IDS:
            if tid.startswith("SPELL_"):
                expected_cid = f"spell.{tid}"
            elif tid.startswith("CREATURE_"):
                expected_cid = f"creature.{tid}"
            elif tid.startswith("FEAT_"):
                expected_cid = f"feat.{tid}"
            else:
                continue
            assert expected_cid in content_ids, f"Missing entry for {expected_cid}"

    def test_entry_count_matches(self, lexicon_dict):
        assert lexicon_dict["entry_count"] == 10
        assert len(lexicon_dict["entries"]) == 10


# ---------------------------------------------------------------------------
# Test 4: No duplicate content_ids
# ---------------------------------------------------------------------------

class TestNoDuplicateContentIds:
    def test_unique_content_ids(self, lexicon_dict):
        content_ids = [e["content_id"] for e in lexicon_dict["entries"]]
        assert len(content_ids) == len(set(content_ids))


# ---------------------------------------------------------------------------
# Test 5: No duplicate lexicon_ids
# ---------------------------------------------------------------------------

class TestNoDuplicateLexiconIds:
    def test_unique_lexicon_ids(self, lexicon_dict):
        lexicon_ids = [e["lexicon_id"] for e in lexicon_dict["entries"]]
        assert len(lexicon_ids) == len(set(lexicon_ids))


# ---------------------------------------------------------------------------
# Test 6: lexicon_id is deterministic: sha256(seed:content_id)[:16]
# ---------------------------------------------------------------------------

class TestLexiconIdDeterminism:
    def test_lexicon_id_matches_formula(self, lexicon_dict):
        for entry in lexicon_dict["entries"]:
            content_id = entry["content_id"]
            expected = hashlib.sha256(
                f"{WORLD_SEED}:{content_id}".encode()
            ).hexdigest()[:16]
            assert entry["lexicon_id"] == expected, (
                f"lexicon_id mismatch for {content_id}: "
                f"got {entry['lexicon_id']}, expected {expected}"
            )

    def test_helper_function_matches(self):
        cid = "spell.SPELL_001"
        expected = hashlib.sha256(f"42:{cid}".encode()).hexdigest()[:16]
        assert _make_lexicon_id(42, cid) == expected


# ---------------------------------------------------------------------------
# Test 7: Short descriptions <= 120 characters
# ---------------------------------------------------------------------------

class TestShortDescriptionLength:
    def test_all_descriptions_within_limit(self, lexicon_dict):
        for entry in lexicon_dict["entries"]:
            desc = entry.get("short_description", "")
            assert len(desc) <= 120, (
                f"Description too long for {entry['content_id']}: "
                f"{len(desc)} chars: {desc!r}"
            )


# ---------------------------------------------------------------------------
# Test 8: Stage registers correctly with WorldCompiler (CompileStage)
# ---------------------------------------------------------------------------

class TestStageInterface:
    def test_is_compile_stage(self):
        stage = LexiconStage()
        assert isinstance(stage, CompileStage)

    def test_stage_id(self):
        stage = LexiconStage()
        assert stage.stage_id == "lexicon"

    def test_stage_number(self):
        stage = LexiconStage()
        assert stage.stage_number == 1

    def test_execute_returns_stage_result(self, compile_context):
        stage = LexiconStage()
        result = stage.execute(compile_context)
        assert isinstance(result, StageResult)
        assert result.stage_id == "lexicon"
        assert result.success is True


# ---------------------------------------------------------------------------
# Test 9: Stage depends_on is empty
# ---------------------------------------------------------------------------

class TestStageDependencies:
    def test_no_dependencies(self):
        stage = LexiconStage()
        assert stage.depends_on == ()

    def test_depends_on_is_tuple(self):
        stage = LexiconStage()
        assert isinstance(stage.depends_on, tuple)


# ---------------------------------------------------------------------------
# Test 10: Stage writes lexicon.json to workspace
# ---------------------------------------------------------------------------

class TestLexiconFileOutput:
    def test_lexicon_json_exists(self, compile_context, lexicon_result):
        assert lexicon_result.success
        path = compile_context.workspace_dir / "lexicon.json"
        assert path.exists()

    def test_lexicon_json_is_valid_json(self, compile_context, lexicon_result):
        path = compile_context.workspace_dir / "lexicon.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "entries" in data
        assert "schema_version" in data

    def test_artifacts_list_contains_filename(self, lexicon_result):
        assert "lexicon.json" in lexicon_result.artifacts

    def test_metadata_reports_entry_count(self, lexicon_result):
        assert lexicon_result.metadata["entry_count"] == 10

    def test_metadata_reports_domains(self, lexicon_result):
        assert set(lexicon_result.metadata["domains"]) == {"creature", "feat", "spell"}

    def test_metadata_reports_stub_mode(self, lexicon_result):
        assert lexicon_result.metadata["mode"] == "stub"


# ---------------------------------------------------------------------------
# Extra: Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_empty_content_pack_fails(self, tmp_path):
        empty_pack = tmp_path / "empty_pack"
        empty_pack.mkdir()
        ws = tmp_path / "ws"
        ws.mkdir()
        ctx = CompileContext(
            content_pack_dir=empty_pack,
            workspace_dir=ws,
            world_seed=WORLD_SEED,
            world_theme_brief=THEME_BRIEF,
            toolchain_pins=TOOLCHAIN_PINS,
        )
        stage = LexiconStage()
        result = stage.execute(ctx)
        assert result.success is False
        assert "No template IDs" in result.error
