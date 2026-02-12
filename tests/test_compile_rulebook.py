"""WO-COMPILE-RULEBOOK-001: Rulebook Generation Stage tests.

Tests:
  1. Stage interface compliance (CompileStage, stage_id, stage_number, depends_on)
  2. Empty content pack produces valid empty registry
  3. Spells produce RuleEntry objects with correct content_id pattern
  4. Feats produce RuleEntry objects (active only)
  5. Output loads via RulebookRegistry.from_json_file()
  6. Output is deterministic (same seed -> same output)
  7. No duplicate content_ids
  8. Parameters are extracted correctly (range, damage, etc.)
  9. Provenance is correct
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.core.compile_stages.rulebook import (
    COMPILER_VERSION,
    RulebookStage,
    is_active_feat,
    _extract_spell_parameters,
    _extract_feat_parameters,
    _parse_range_ft,
    _parse_duration,
    _spell_short_description,
    _spell_mechanical_summary,
    _spell_tags,
)
from aidm.lens.rulebook_registry import RulebookRegistry
from aidm.schemas.rulebook import RuleEntry, RuleParameters, RuleProvenance


# ═══════════════════════════════════════════════════════════════════════
# Test fixtures — reuse spell/feat fixtures from semantics tests
# ═══════════════════════════════════════════════════════════════════════

FIRE_AOE_BURST = {
    "template_id": "SPELL_FIREBALL",
    "tier": 3,
    "school_category": "evocation",
    "subschool": None,
    "descriptors": ["fire"],
    "target_type": "area",
    "range_formula": "long",
    "aoe_shape": "burst",
    "aoe_radius_ft": 20,
    "effect_type": "damage",
    "damage_formula": "1d6_per_CL",
    "damage_type": "fire",
    "healing_formula": None,
    "save_type": "reflex",
    "save_effect": "half",
    "casting_time": "standard",
    "duration_formula": "instantaneous",
    "concentration": False,
    "combat_role_tags": ["aoe_damage"],
}

COLD_TOUCH = {
    "template_id": "SPELL_CHILL_TOUCH",
    "tier": 1,
    "school_category": "necromancy",
    "subschool": None,
    "descriptors": [],
    "target_type": "touch",
    "range_formula": "touch",
    "aoe_shape": None,
    "aoe_radius_ft": None,
    "effect_type": "damage",
    "damage_formula": "1d6",
    "damage_type": "cold",
    "healing_formula": None,
    "save_type": None,
    "save_effect": None,
    "casting_time": "standard",
    "duration_formula": "instantaneous",
    "concentration": False,
    "combat_role_tags": ["single_target_damage"],
}

LIGHTNING_LINE = {
    "template_id": "SPELL_LIGHTNING_BOLT",
    "tier": 3,
    "school_category": "evocation",
    "subschool": None,
    "descriptors": ["electricity"],
    "target_type": "area",
    "range_formula": "120",
    "aoe_shape": "line",
    "aoe_radius_ft": None,
    "effect_type": "damage",
    "damage_formula": "1d6_per_CL",
    "damage_type": "electricity",
    "healing_formula": None,
    "save_type": "reflex",
    "save_effect": "half",
    "casting_time": "standard",
    "duration_formula": "instantaneous",
    "concentration": False,
    "combat_role_tags": ["aoe_damage"],
}

HEALING_SINGLE = {
    "template_id": "SPELL_CURE_LIGHT",
    "tier": 1,
    "school_category": "conjuration",
    "subschool": "healing",
    "descriptors": [],
    "target_type": "touch",
    "range_formula": "touch",
    "aoe_shape": None,
    "aoe_radius_ft": None,
    "effect_type": "healing",
    "damage_formula": None,
    "damage_type": None,
    "healing_formula": "1d8+CL",
    "save_type": None,
    "save_effect": None,
    "casting_time": "standard",
    "duration_formula": "instantaneous",
    "concentration": False,
    "combat_role_tags": ["healing"],
}

ILLUSION_SELF = {
    "template_id": "SPELL_MIRROR_IMAGE",
    "tier": 2,
    "school_category": "illusion",
    "subschool": "figment",
    "descriptors": [],
    "target_type": "self",
    "range_formula": "personal",
    "aoe_shape": None,
    "aoe_radius_ft": None,
    "effect_type": "buff",
    "damage_formula": None,
    "damage_type": None,
    "healing_formula": None,
    "save_type": None,
    "save_effect": None,
    "casting_time": "standard",
    "duration_formula": "1_min_per_CL",
    "concentration": False,
    "combat_role_tags": ["defense"],
}

ALL_FIXTURE_SPELLS = [
    FIRE_AOE_BURST,
    COLD_TOUCH,
    LIGHTNING_LINE,
    HEALING_SINGLE,
    ILLUSION_SELF,
]

# ═══════════════════════════════════════════════════════════════════════
# Feat fixtures
# ═══════════════════════════════════════════════════════════════════════

PASSIVE_FEAT = {
    "template_id": "FEAT_ALERTNESS",
    "feat_type": "general",
    "effect_type": "skill_modifier",
    "bonus_value": 2,
    "bonus_type": "skill",
    "bonus_applies_to": "listen,spot",
    "trigger": None,
    "grants_action": None,
}

ACTIVE_FEAT_WITH_TRIGGER = {
    "template_id": "FEAT_CLEAVE",
    "feat_type": "general",
    "effect_type": "combat",
    "trigger": "on_kill",
    "grants_action": "extra_melee_attack_on_kill",
    "bonus_value": None,
    "bonus_type": None,
    "bonus_applies_to": None,
}

ACTIVE_FEAT_WITH_GRANTS_ACTION_ONLY = {
    "template_id": "FEAT_QUICKDRAW",
    "feat_type": "general",
    "effect_type": "combat",
    "trigger": None,
    "grants_action": "draw_weapon_free",
    "bonus_value": None,
    "bonus_type": None,
    "bonus_applies_to": None,
}

ALL_FIXTURE_FEATS = [
    PASSIVE_FEAT,
    ACTIVE_FEAT_WITH_TRIGGER,
    ACTIVE_FEAT_WITH_GRANTS_ACTION_ONLY,
]


# ═══════════════════════════════════════════════════════════════════════
# Helper: build CompileContext
# ═══════════════════════════════════════════════════════════════════════


def _make_context(tmp_path: Path, spells=None, feats=None) -> CompileContext:
    """Build a CompileContext pointing at test fixture data."""
    content_dir = tmp_path / "content_pack"
    content_dir.mkdir(exist_ok=True)

    if spells is not None:
        with open(content_dir / "spells.json", "w") as f:
            json.dump(spells, f)

    if feats is not None:
        feat_data = {
            "schema_version": "1.0.0",
            "source_id": "test",
            "extraction_version": "test",
            "feat_count": len(feats),
            "feats": feats,
        }
        with open(content_dir / "feats.json", "w") as f:
            json.dump(feat_data, f)

    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)

    return CompileContext(
        content_pack_dir=content_dir,
        workspace_dir=workspace,
        world_seed=42,
        world_theme_brief={"genre": "dark_fantasy", "tone": "grim"},
        toolchain_pins={"llm_model_id": "stub", "schema_version": "1.0"},
        content_pack_id="test_pack",
        world_id="a" * 32,
    )


def _make_full_context(tmp_path: Path) -> CompileContext:
    """Build a context with ALL fixture spells and feats."""
    return _make_context(tmp_path, spells=ALL_FIXTURE_SPELLS, feats=ALL_FIXTURE_FEATS)


# ═══════════════════════════════════════════════════════════════════════
# Test 1: Stage interface compliance
# ═══════════════════════════════════════════════════════════════════════


class TestStageInterface:
    """RulebookStage conforms to CompileStage interface."""

    def test_is_compile_stage(self):
        stage = RulebookStage()
        assert isinstance(stage, CompileStage)

    def test_stage_id(self):
        stage = RulebookStage()
        assert stage.stage_id == "rulebook"

    def test_stage_number(self):
        stage = RulebookStage()
        assert stage.stage_number == 2

    def test_depends_on(self):
        stage = RulebookStage()
        assert stage.depends_on == ("lexicon", "semantics")

    def test_execute_returns_stage_result(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        result = stage.execute(context)
        assert isinstance(result, StageResult)
        assert result.stage_id == "rulebook"
        assert result.status == "success"
        assert "rule_registry.json" in result.output_files

    def test_execute_writes_output_file(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)
        output_path = context.workspace_dir / "rule_registry.json"
        assert output_path.exists()


# ═══════════════════════════════════════════════════════════════════════
# Test 2: Empty content pack produces valid empty registry
# ═══════════════════════════════════════════════════════════════════════


class TestEmptyContentPack:
    """Empty content pack produces valid empty registry."""

    def test_no_spells_no_feats(self, tmp_path):
        context = _make_context(tmp_path)  # no spells, no feats files
        stage = RulebookStage()
        result = stage.execute(context)
        assert result.status == "success"

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        assert data["entry_count"] == 0
        assert data["entries"] == []
        assert data["schema_version"] == "1.0"

    def test_empty_spells_list(self, tmp_path):
        context = _make_context(tmp_path, spells=[], feats=[])
        stage = RulebookStage()
        result = stage.execute(context)
        assert result.status == "success"

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        assert data["entry_count"] == 0

    def test_empty_registry_loadable(self, tmp_path):
        context = _make_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        registry = RulebookRegistry.from_json_file(output_path)
        assert registry.entry_count == 0


# ═══════════════════════════════════════════════════════════════════════
# Test 3: Spells produce RuleEntry objects with correct content_id pattern
# ═══════════════════════════════════════════════════════════════════════


class TestSpellRuleEntries:
    """Spells produce RuleEntry objects with correct content_id pattern."""

    def test_spell_content_id_pattern(self, tmp_path):
        context = _make_context(tmp_path, spells=ALL_FIXTURE_SPELLS, feats=[])
        stage = RulebookStage()
        result = stage.execute(context)
        assert result.status == "success"

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        content_ids = [e["content_id"] for e in data["entries"]]
        assert "spell.spell_fireball" in content_ids
        assert "spell.spell_chill_touch" in content_ids
        assert "spell.spell_lightning_bolt" in content_ids
        assert "spell.spell_cure_light" in content_ids
        assert "spell.spell_mirror_image" in content_ids

    def test_spell_procedure_id_pattern(self, tmp_path):
        context = _make_context(tmp_path, spells=[FIRE_AOE_BURST], feats=[])
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        entry = data["entries"][0]
        assert entry["procedure_id"] == "proc.spell.spell_fireball"

    def test_spell_rule_type(self, tmp_path):
        context = _make_context(tmp_path, spells=ALL_FIXTURE_SPELLS, feats=[])
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        for entry in data["entries"]:
            assert entry["rule_type"] == "spell"

    def test_spell_world_name_is_content_id_in_stub_mode(self, tmp_path):
        context = _make_context(tmp_path, spells=[FIRE_AOE_BURST], feats=[])
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        entry = data["entries"][0]
        assert entry["world_name"] == entry["content_id"]

    def test_spell_count_matches(self, tmp_path):
        context = _make_context(tmp_path, spells=ALL_FIXTURE_SPELLS, feats=[])
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        assert data["entry_count"] == 5
        assert len(data["entries"]) == 5


# ═══════════════════════════════════════════════════════════════════════
# Test 4: Feats produce RuleEntry objects (active only)
# ═══════════════════════════════════════════════════════════════════════


class TestFeatRuleEntries:
    """Active feats produce RuleEntry objects, passive feats are excluded."""

    def test_active_feats_included(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        content_ids = [e["content_id"] for e in data["entries"]]
        assert "feat.feat_cleave" in content_ids
        assert "feat.feat_quickdraw" in content_ids

    def test_passive_feats_excluded(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        content_ids = [e["content_id"] for e in data["entries"]]
        assert "feat.feat_alertness" not in content_ids

    def test_feat_procedure_id_pattern(self, tmp_path):
        context = _make_context(
            tmp_path, spells=[], feats=[ACTIVE_FEAT_WITH_TRIGGER]
        )
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        entry = data["entries"][0]
        assert entry["procedure_id"] == "proc.feat.feat_cleave"

    def test_feat_rule_type(self, tmp_path):
        context = _make_context(
            tmp_path, spells=[], feats=[ACTIVE_FEAT_WITH_TRIGGER]
        )
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        assert data["entries"][0]["rule_type"] == "feat"

    def test_is_active_feat_logic(self):
        assert not is_active_feat(PASSIVE_FEAT)
        assert is_active_feat(ACTIVE_FEAT_WITH_TRIGGER)
        assert is_active_feat(ACTIVE_FEAT_WITH_GRANTS_ACTION_ONLY)

    def test_total_count_with_mixed_content(self, tmp_path):
        """5 spells + 2 active feats = 7 entries (1 passive excluded)."""
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        assert data["entry_count"] == 7


# ═══════════════════════════════════════════════════════════════════════
# Test 5: Output loads via RulebookRegistry.from_json_file()
# ═══════════════════════════════════════════════════════════════════════


class TestRegistryLoadable:
    """Output is loadable by RulebookRegistry."""

    def test_stage_output_loadable(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        result = stage.execute(context)
        assert result.status == "success"

        output_path = context.workspace_dir / "rule_registry.json"
        registry = RulebookRegistry.from_json_file(output_path)
        assert registry.schema_version == "1.0"
        assert registry.world_id == "a" * 32
        assert registry.compiler_version == "0.1.0"

    def test_registry_entry_count_matches(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        registry = RulebookRegistry.from_json_file(output_path)
        assert registry.entry_count == 7

    def test_registry_get_entry(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        registry = RulebookRegistry.from_json_file(output_path)

        entry = registry.get_entry("spell.spell_fireball")
        assert entry is not None
        assert entry.rule_type == "spell"
        assert entry.content_id == "spell.spell_fireball"

    def test_registry_search_by_category(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        registry = RulebookRegistry.from_json_file(output_path)

        spells = registry.list_by_category("spell")
        assert len(spells) == 5

        feats = registry.list_by_category("feat")
        assert len(feats) == 2

    def test_round_trip_dict(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        registry = RulebookRegistry.from_dict(data)
        assert registry.entry_count == data["entry_count"]


# ═══════════════════════════════════════════════════════════════════════
# Test 6: Output is deterministic (same seed -> same output)
# ═══════════════════════════════════════════════════════════════════════


class TestDeterminism:
    """Same inputs produce identical output across runs."""

    def test_deterministic(self, tmp_path):
        # Run 1
        (tmp_path / "run1").mkdir()
        ctx1 = _make_full_context(tmp_path / "run1")
        stage = RulebookStage()
        r1 = stage.execute(ctx1)
        assert r1.status == "success"

        # Run 2
        (tmp_path / "run2").mkdir()
        ctx2 = _make_full_context(tmp_path / "run2")
        r2 = stage.execute(ctx2)
        assert r2.status == "success"

        # Compare outputs
        with open(ctx1.workspace_dir / "rule_registry.json") as f:
            out1 = json.load(f)
        with open(ctx2.workspace_dir / "rule_registry.json") as f:
            out2 = json.load(f)

        assert out1 == out2

    def test_different_seed_produces_different_provenance(self, tmp_path):
        (tmp_path / "run1").mkdir()
        ctx1 = _make_full_context(tmp_path / "run1")
        stage = RulebookStage()
        stage.execute(ctx1)

        (tmp_path / "run2").mkdir()
        ctx2 = _make_full_context(tmp_path / "run2")
        # Change the seed
        ctx2.world_seed = 99
        stage.execute(ctx2)

        with open(ctx1.workspace_dir / "rule_registry.json") as f:
            out1 = json.load(f)
        with open(ctx2.workspace_dir / "rule_registry.json") as f:
            out2 = json.load(f)

        # Seed is in provenance, so outputs differ
        seed_1 = out1["entries"][0]["provenance"]["seed_used"]
        seed_2 = out2["entries"][0]["provenance"]["seed_used"]
        assert seed_1 != seed_2


# ═══════════════════════════════════════════════════════════════════════
# Test 7: No duplicate content_ids
# ═══════════════════════════════════════════════════════════════════════


class TestNoDuplicateContentIds:
    """No duplicate content_ids in output."""

    def test_no_duplicates(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        content_ids = [e["content_id"] for e in data["entries"]]
        assert len(content_ids) == len(set(content_ids)), (
            f"Duplicate content_ids found: "
            f"{[x for x in content_ids if content_ids.count(x) > 1]}"
        )

    def test_duplicate_spells_deduplicated(self, tmp_path):
        """If content pack has duplicate template_ids, only first is kept."""
        spells = [FIRE_AOE_BURST, FIRE_AOE_BURST]
        context = _make_context(tmp_path, spells=spells, feats=[])
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        content_ids = [e["content_id"] for e in data["entries"]]
        assert content_ids.count("spell.spell_fireball") == 1

    def test_entries_sorted_by_content_id(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        content_ids = [e["content_id"] for e in data["entries"]]
        assert content_ids == sorted(content_ids)


# ═══════════════════════════════════════════════════════════════════════
# Test 8: Parameters are extracted correctly
# ═══════════════════════════════════════════════════════════════════════


class TestParameterExtraction:
    """Mechanical parameters are extracted correctly from content pack data."""

    def test_fireball_range(self):
        params = _extract_spell_parameters(FIRE_AOE_BURST)
        assert params.range_ft == 400  # "long" -> 400

    def test_fireball_area(self):
        params = _extract_spell_parameters(FIRE_AOE_BURST)
        assert params.area_shape == "burst"
        assert params.area_radius_ft == 20

    def test_fireball_damage(self):
        params = _extract_spell_parameters(FIRE_AOE_BURST)
        assert params.damage_dice == "1d6_per_CL"
        assert params.damage_type == "fire"

    def test_fireball_save(self):
        params = _extract_spell_parameters(FIRE_AOE_BURST)
        assert params.save_type == "reflex"
        assert params.save_effect == "half"

    def test_fireball_duration(self):
        params = _extract_spell_parameters(FIRE_AOE_BURST)
        assert params.duration_unit == "instantaneous"

    def test_fireball_action_cost(self):
        params = _extract_spell_parameters(FIRE_AOE_BURST)
        assert params.action_cost == "standard"

    def test_fireball_target_type(self):
        params = _extract_spell_parameters(FIRE_AOE_BURST)
        assert params.target_type == "area"

    def test_touch_range(self):
        params = _extract_spell_parameters(COLD_TOUCH)
        assert params.range_ft == 0  # "touch" -> 0

    def test_numeric_range(self):
        params = _extract_spell_parameters(LIGHTNING_LINE)
        assert params.range_ft == 120  # "120" -> 120

    def test_close_range(self):
        spell = dict(FIRE_AOE_BURST)
        spell["range_formula"] = "close"
        params = _extract_spell_parameters(spell)
        assert params.range_ft == 25

    def test_medium_range(self):
        spell = dict(FIRE_AOE_BURST)
        spell["range_formula"] = "medium"
        params = _extract_spell_parameters(spell)
        assert params.range_ft == 100

    def test_round_duration_parsing(self):
        spell = dict(FIRE_AOE_BURST)
        spell["duration_formula"] = "1_round_per_CL"
        params = _extract_spell_parameters(spell)
        assert params.duration_unit == "rounds"
        assert params.duration_value == 1

    def test_minute_duration_parsing(self):
        spell = dict(ILLUSION_SELF)
        params = _extract_spell_parameters(spell)
        assert params.duration_unit == "minutes"
        assert params.duration_value == 1

    def test_healing_spell_no_damage(self):
        params = _extract_spell_parameters(HEALING_SINGLE)
        assert params.damage_type is None
        assert params.save_type is None

    def test_feat_parameters(self):
        params = _extract_feat_parameters(ACTIVE_FEAT_WITH_TRIGGER)
        assert params.target_type == "self"

    def test_feat_grants_action_free(self):
        params = _extract_feat_parameters(ACTIVE_FEAT_WITH_GRANTS_ACTION_ONLY)
        assert params.action_cost == "free"  # "draw_weapon_free" contains "free"

    def test_parse_range_ft_none_for_empty(self):
        assert _parse_range_ft("") is None
        assert _parse_range_ft(None) is None

    def test_parse_duration_none_for_empty(self):
        unit, val = _parse_duration("")
        assert unit is None
        assert val is None


# ═══════════════════════════════════════════════════════════════════════
# Test 9: Provenance is correct
# ═══════════════════════════════════════════════════════════════════════


class TestProvenance:
    """Provenance fields are set correctly."""

    def test_spell_provenance(self, tmp_path):
        context = _make_context(tmp_path, spells=[FIRE_AOE_BURST], feats=[])
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        prov = data["entries"][0]["provenance"]
        assert prov["source"] == "world_compiler"
        assert prov["compiler_version"] == "0.1.0"
        assert prov["seed_used"] == 42
        assert prov["content_pack_id"] == "test_pack"
        assert prov["template_ids"] == ["SPELL_FIREBALL"]

    def test_feat_provenance(self, tmp_path):
        context = _make_context(
            tmp_path, spells=[], feats=[ACTIVE_FEAT_WITH_TRIGGER]
        )
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        prov = data["entries"][0]["provenance"]
        assert prov["source"] == "world_compiler"
        assert prov["compiler_version"] == "0.1.0"
        assert prov["seed_used"] == 42
        assert prov["content_pack_id"] == "test_pack"
        assert prov["template_ids"] == ["FEAT_CLEAVE"]

    def test_world_id_in_registry(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        assert data["world_id"] == "a" * 32

    def test_compiler_version_in_registry(self, tmp_path):
        context = _make_full_context(tmp_path)
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        assert data["compiler_version"] == "0.1.0"


# ═══════════════════════════════════════════════════════════════════════
# Additional: Text slots and tags
# ═══════════════════════════════════════════════════════════════════════


class TestTextSlots:
    """Text slot generation for stub mode."""

    def test_spell_short_description_format(self):
        desc = _spell_short_description(FIRE_AOE_BURST)
        assert "Tier 3" in desc
        assert "evocation" in desc
        assert "damage" in desc
        assert len(desc) <= 120

    def test_spell_mechanical_summary_contains_damage(self):
        summary = _spell_mechanical_summary(FIRE_AOE_BURST)
        assert "1d6_per_CL" in summary
        assert "fire" in summary

    def test_spell_mechanical_summary_contains_range(self):
        summary = _spell_mechanical_summary(FIRE_AOE_BURST)
        assert "long" in summary

    def test_spell_mechanical_summary_contains_area(self):
        summary = _spell_mechanical_summary(FIRE_AOE_BURST)
        assert "burst" in summary
        assert "20" in summary

    def test_spell_mechanical_summary_contains_save(self):
        summary = _spell_mechanical_summary(FIRE_AOE_BURST)
        assert "reflex" in summary

    def test_text_slots_in_output(self, tmp_path):
        context = _make_context(tmp_path, spells=[FIRE_AOE_BURST], feats=[])
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        entry = data["entries"][0]
        assert "text_slots" in entry
        assert "short_description" in entry["text_slots"]
        assert "mechanical_summary" in entry["text_slots"]


class TestTags:
    """Tag extraction from spell and feat data."""

    def test_spell_tags_include_combat_role(self):
        tags = _spell_tags(FIRE_AOE_BURST)
        assert "aoe_damage" in tags

    def test_spell_tags_include_school(self):
        tags = _spell_tags(FIRE_AOE_BURST)
        assert "evocation" in tags

    def test_spell_tags_in_output(self, tmp_path):
        context = _make_context(tmp_path, spells=[FIRE_AOE_BURST], feats=[])
        stage = RulebookStage()
        stage.execute(context)

        output_path = context.workspace_dir / "rule_registry.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        entry = data["entries"][0]
        assert "tags" in entry
        assert "evocation" in entry["tags"]


# ═══════════════════════════════════════════════════════════════════════
# Error handling
# ═══════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Stage handles errors gracefully."""

    def test_corrupt_json_returns_failed(self, tmp_path):
        content_dir = tmp_path / "content_pack"
        content_dir.mkdir()
        with open(content_dir / "spells.json", "w") as f:
            f.write("{corrupt json")

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        context = CompileContext(
            content_pack_dir=content_dir,
            workspace_dir=workspace,
            world_seed=42,
            world_theme_brief={},
            toolchain_pins={"llm_model_id": "stub"},
            content_pack_id="bad_pack",
            world_id="b" * 32,
        )

        stage = RulebookStage()
        result = stage.execute(context)
        assert result.status == "failed"
        assert result.error is not None
