"""WO-WORLDCOMPILE-SEMANTICS-001: Presentation Semantics Binding tests.

Tests:
  1. Rule-based mapping: fire damage spell → correct delivery_mode, staging, scale, vfx_tags
  2. Rule-based mapping: touch spell → TOUCH delivery_mode
  3. Rule-based mapping: cone AoE → CONE delivery_mode
  4. Rule-based mapping: high-tier spell → CATASTROPHIC scale
  5. Rule-based mapping: healing spell → correct vfx/sfx tags
  6. All event categories get default semantics
  7. Output is valid PresentationSemanticsRegistry (loadable by PresentationRegistryLoader)
  8. No duplicate content_ids in output
  9. Stub mode produces deterministic output
  10. Passive feats are excluded from ability entries
  11. Active feats (with trigger/grants_action) get ability entries
  12. Stage registers correctly with WorldCompiler
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from aidm.core.compile_stages._base import CompileContext, StageResult
from aidm.core.compile_stages.semantics import (
    EVENT_DEFAULTS,
    SemanticsStage,
    build_event_defaults,
    is_active_feat,
    map_delivery_mode,
    map_feat_to_entry,
    map_origin_rule,
    map_scale,
    map_sfx_tags,
    map_spell_to_entry,
    map_staging,
    map_vfx_tags,
)
from aidm.lens.presentation_registry import (
    PresentationRegistryLoader,
    RegistryValidationError,
)
from aidm.schemas.presentation_semantics import (
    DeliveryMode,
    EventCategory,
    NarrationPriority,
    OriginRule,
    PresentationSemanticsRegistry,
    Scale,
    SemanticsProvenance,
    Staging,
)


# ═══════════════════════════════════════════════════════════════════════
# Test fixtures — 5 spells covering the spec requirements
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
}

ACTIVE_FEAT_WITH_GRANTS_ACTION_ONLY = {
    "template_id": "FEAT_QUICKDRAW",
    "feat_type": "general",
    "effect_type": "combat",
    "trigger": None,
    "grants_action": "draw_weapon_free",
}


def _make_provenance(**overrides) -> SemanticsProvenance:
    defaults = {
        "source": "world_compiler",
        "compiler_version": "0.1.0",
        "seed_used": 42,
        "content_pack_id": "test_pack",
    }
    defaults.update(overrides)
    return SemanticsProvenance(**defaults)


def _make_context(tmp_path: Path) -> CompileContext:
    """Build a CompileContext pointing at test fixture data."""
    content_dir = tmp_path / "content_pack"
    content_dir.mkdir()

    # Write spells
    with open(content_dir / "spells.json", "w") as f:
        json.dump(ALL_FIXTURE_SPELLS, f)

    # Write feats
    feat_data = {
        "schema_version": "1.0.0",
        "source_id": "test",
        "extraction_version": "test",
        "feat_count": 3,
        "feats": [
            PASSIVE_FEAT,
            ACTIVE_FEAT_WITH_TRIGGER,
            ACTIVE_FEAT_WITH_GRANTS_ACTION_ONLY,
        ],
    }
    with open(content_dir / "feats.json", "w") as f:
        json.dump(feat_data, f)

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    return CompileContext(
        content_pack_dir=content_dir,
        workspace_dir=workspace,
        world_seed=42,
        world_theme_brief={"genre": "dark_fantasy", "tone": "grim"},
        toolchain_pins={"llm_model_id": "stub", "schema_version": "1.0"},
        content_pack_id="test_pack",
        world_id="a" * 32,
    )


# ═══════════════════════════════════════════════════════════════════════
# Test 1: Fire damage spell mapping
# ═══════════════════════════════════════════════════════════════════════


class TestFireDamageSpell:
    """Fire AoE burst spell maps to correct semantics."""

    def test_delivery_mode_burst(self):
        assert map_delivery_mode(FIRE_AOE_BURST) == DeliveryMode.BURST_FROM_POINT

    def test_staging_travel_then_detonate(self):
        assert map_staging(FIRE_AOE_BURST) == Staging.TRAVEL_THEN_DETONATE

    def test_scale_moderate(self):
        # tier=3, aoe_radius=20 → DRAMATIC (radius >= 20)
        assert map_scale(FIRE_AOE_BURST) == Scale.DRAMATIC

    def test_vfx_tags_contain_fire(self):
        vfx = map_vfx_tags(FIRE_AOE_BURST)
        assert "fire" in vfx
        assert "glow" in vfx
        assert "heat_distortion" in vfx

    def test_sfx_tags_contain_fire(self):
        sfx = map_sfx_tags(FIRE_AOE_BURST)
        assert "whoosh" in sfx
        assert "crackle" in sfx

    def test_origin_from_chosen_point(self):
        assert map_origin_rule(FIRE_AOE_BURST) == OriginRule.FROM_CHOSEN_POINT

    def test_full_entry(self):
        prov = _make_provenance()
        entry = map_spell_to_entry(FIRE_AOE_BURST, prov)
        assert entry.content_id == "spell.spell_fireball"
        assert entry.delivery_mode == DeliveryMode.BURST_FROM_POINT
        assert entry.staging == Staging.TRAVEL_THEN_DETONATE
        assert "fire" in entry.vfx_tags


# ═══════════════════════════════════════════════════════════════════════
# Test 2: Touch spell mapping
# ═══════════════════════════════════════════════════════════════════════


class TestTouchSpell:
    """Touch spell maps to TOUCH delivery_mode."""

    def test_delivery_mode_touch(self):
        assert map_delivery_mode(COLD_TOUCH) == DeliveryMode.TOUCH

    def test_staging_instant(self):
        assert map_staging(COLD_TOUCH) == Staging.INSTANT

    def test_vfx_tags_contain_frost(self):
        vfx = map_vfx_tags(COLD_TOUCH)
        assert "frost" in vfx

    def test_sfx_tags_contain_cold(self):
        sfx = map_sfx_tags(COLD_TOUCH)
        assert "crystallize" in sfx

    def test_origin_from_caster(self):
        assert map_origin_rule(COLD_TOUCH) == OriginRule.FROM_CASTER


# ═══════════════════════════════════════════════════════════════════════
# Test 3: Cone AoE mapping
# ═══════════════════════════════════════════════════════════════════════


class TestConeAoE:
    """Cone AoE spell maps to CONE delivery_mode."""

    def test_delivery_mode_cone(self):
        cone_spell = {
            "template_id": "SPELL_CONE_COLD",
            "tier": 5,
            "school_category": "evocation",
            "target_type": "area",
            "aoe_shape": "cone",
            "aoe_radius_ft": 30,
            "effect_type": "damage",
            "damage_type": "cold",
            "range_formula": "60",
            "duration_formula": "instantaneous",
            "concentration": False,
        }
        assert map_delivery_mode(cone_spell) == DeliveryMode.CONE


# ═══════════════════════════════════════════════════════════════════════
# Test 4: High-tier spell → CATASTROPHIC scale
# ═══════════════════════════════════════════════════════════════════════


class TestHighTierScale:
    """High-tier spell (tier >= 7) maps to CATASTROPHIC scale."""

    def test_tier_7_catastrophic(self):
        spell = {"tier": 7, "aoe_radius_ft": None}
        assert map_scale(spell) == Scale.CATASTROPHIC

    def test_tier_9_catastrophic(self):
        spell = {"tier": 9, "aoe_radius_ft": 60}
        assert map_scale(spell) == Scale.CATASTROPHIC

    def test_large_radius_catastrophic(self):
        spell = {"tier": 3, "aoe_radius_ft": 40}
        assert map_scale(spell) == Scale.CATASTROPHIC

    def test_tier_5_dramatic(self):
        spell = {"tier": 5, "aoe_radius_ft": None}
        assert map_scale(spell) == Scale.DRAMATIC

    def test_tier_3_moderate(self):
        spell = {"tier": 3, "aoe_radius_ft": None}
        assert map_scale(spell) == Scale.MODERATE

    def test_tier_0_subtle(self):
        spell = {"tier": 0, "aoe_radius_ft": None}
        assert map_scale(spell) == Scale.SUBTLE


# ═══════════════════════════════════════════════════════════════════════
# Test 5: Healing spell mapping
# ═══════════════════════════════════════════════════════════════════════


class TestHealingSpell:
    """Healing spell maps to correct vfx/sfx tags."""

    def test_vfx_tags_contain_radiance(self):
        vfx = map_vfx_tags(HEALING_SINGLE)
        assert "radiance" in vfx
        assert "warmth" in vfx

    def test_sfx_tags_contain_chime(self):
        sfx = map_sfx_tags(HEALING_SINGLE)
        assert "chime" in sfx
        assert "swell" in sfx

    def test_delivery_mode_touch(self):
        assert map_delivery_mode(HEALING_SINGLE) == DeliveryMode.TOUCH


# ═══════════════════════════════════════════════════════════════════════
# Test 6: All event categories get default semantics
# ═══════════════════════════════════════════════════════════════════════


class TestEventCategoryDefaults:
    """All 18 EventCategory values get default semantics."""

    def test_all_18_categories_covered(self):
        entries = build_event_defaults()
        categories = {e.event_category for e in entries}
        expected = set(EventCategory)
        assert categories == expected
        assert len(entries) == 18

    def test_event_defaults_table_covers_all(self):
        assert set(EVENT_DEFAULTS.keys()) == set(EventCategory)

    def test_melee_attack_always_narrate(self):
        entries = build_event_defaults()
        melee = [e for e in entries if e.event_category == EventCategory.MELEE_ATTACK][0]
        assert melee.narration_priority == NarrationPriority.ALWAYS_NARRATE
        assert melee.default_scale == Scale.MODERATE

    def test_turn_boundary_never_narrate(self):
        entries = build_event_defaults()
        turn = [e for e in entries if e.event_category == EventCategory.TURN_BOUNDARY][0]
        assert turn.narration_priority == NarrationPriority.NEVER_NARRATE


# ═══════════════════════════════════════════════════════════════════════
# Test 7: Valid PresentationSemanticsRegistry (loadable)
# ═══════════════════════════════════════════════════════════════════════


class TestRegistryLoadable:
    """Output is a valid PresentationSemanticsRegistry loadable by
    PresentationRegistryLoader."""

    def test_stage_output_loadable(self, tmp_path):
        context = _make_context(tmp_path)
        stage = SemanticsStage()
        result = stage.execute(context)
        assert result.success

        output_path = context.workspace_dir / "presentation_semantics.json"
        loader = PresentationRegistryLoader.from_json_file(output_path)
        assert loader.registry.schema_version == "1.0"
        assert loader.registry.world_id == "a" * 32

    def test_round_trip_dict(self, tmp_path):
        context = _make_context(tmp_path)
        stage = SemanticsStage()
        result = stage.execute(context)
        assert result.success

        output_path = context.workspace_dir / "presentation_semantics.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        registry = PresentationSemanticsRegistry.from_dict(data)
        assert len(registry.ability_entries) == data["ability_entry_count"]
        assert len(registry.event_entries) == data["event_entry_count"]


# ═══════════════════════════════════════════════════════════════════════
# Test 8: No duplicate content_ids
# ═══════════════════════════════════════════════════════════════════════


class TestNoDuplicateContentIds:
    """No duplicate content_ids in output."""

    def test_no_duplicates(self, tmp_path):
        context = _make_context(tmp_path)
        stage = SemanticsStage()
        result = stage.execute(context)
        assert result.success

        output_path = context.workspace_dir / "presentation_semantics.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        content_ids = [e["content_id"] for e in data["ability_entries"]]
        assert len(content_ids) == len(set(content_ids)), (
            f"Duplicate content_ids found: "
            f"{[x for x in content_ids if content_ids.count(x) > 1]}"
        )

    def test_loader_rejects_duplicates(self, tmp_path):
        """PresentationRegistryLoader rejects duplicate content_ids."""
        context = _make_context(tmp_path)
        stage = SemanticsStage()
        result = stage.execute(context)
        assert result.success

        output_path = context.workspace_dir / "presentation_semantics.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        # Artificially duplicate an entry
        if data["ability_entries"]:
            data["ability_entries"].append(data["ability_entries"][0])
            data["ability_entry_count"] = len(data["ability_entries"])
            with pytest.raises(RegistryValidationError, match="duplicate"):
                PresentationRegistryLoader.from_dict(data)


# ═══════════════════════════════════════════════════════════════════════
# Test 9: Stub mode determinism
# ═══════════════════════════════════════════════════════════════════════


class TestStubModeDeterminism:
    """Stub mode produces deterministic output across runs."""

    def test_deterministic(self, tmp_path):
        # Run 1
        (tmp_path / "run1").mkdir()
        ctx1 = _make_context(tmp_path / "run1")
        stage = SemanticsStage()
        r1 = stage.execute(ctx1)
        assert r1.success

        # Run 2
        (tmp_path / "run2").mkdir()
        ctx2 = _make_context(tmp_path / "run2")
        r2 = stage.execute(ctx2)
        assert r2.success

        # Compare outputs
        with open(ctx1.workspace_dir / "presentation_semantics.json") as f:
            out1 = json.load(f)
        with open(ctx2.workspace_dir / "presentation_semantics.json") as f:
            out2 = json.load(f)

        assert out1 == out2


def _write_fixture_data(base_path: Path) -> None:
    """Write fixture data for determinism test."""
    content_dir = base_path / "content_pack"
    content_dir.mkdir(exist_ok=True)
    with open(content_dir / "spells.json", "w") as f:
        json.dump(ALL_FIXTURE_SPELLS, f)
    feat_data = {
        "schema_version": "1.0.0",
        "source_id": "test",
        "extraction_version": "test",
        "feat_count": 3,
        "feats": [PASSIVE_FEAT, ACTIVE_FEAT_WITH_TRIGGER, ACTIVE_FEAT_WITH_GRANTS_ACTION_ONLY],
    }
    with open(content_dir / "feats.json", "w") as f:
        json.dump(feat_data, f)
    workspace = base_path / "workspace"
    workspace.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════
# Test 10: Passive feats excluded
# ═══════════════════════════════════════════════════════════════════════


class TestPassiveFeatsExcluded:
    """Passive feats (no trigger, no grants_action) are excluded."""

    def test_passive_feat_not_active(self):
        assert not is_active_feat(PASSIVE_FEAT)

    def test_passive_feat_excluded_from_output(self, tmp_path):
        context = _make_context(tmp_path)
        stage = SemanticsStage()
        result = stage.execute(context)
        assert result.success

        output_path = context.workspace_dir / "presentation_semantics.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        content_ids = [e["content_id"] for e in data["ability_entries"]]
        assert "feat.feat_alertness" not in content_ids


# ═══════════════════════════════════════════════════════════════════════
# Test 11: Active feats included
# ═══════════════════════════════════════════════════════════════════════


class TestActiveFeatsIncluded:
    """Active feats (with trigger or grants_action) get ability entries."""

    def test_feat_with_trigger_is_active(self):
        assert is_active_feat(ACTIVE_FEAT_WITH_TRIGGER)

    def test_feat_with_grants_action_is_active(self):
        assert is_active_feat(ACTIVE_FEAT_WITH_GRANTS_ACTION_ONLY)

    def test_active_feat_in_output(self, tmp_path):
        context = _make_context(tmp_path)
        stage = SemanticsStage()
        result = stage.execute(context)
        assert result.success

        output_path = context.workspace_dir / "presentation_semantics.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        content_ids = [e["content_id"] for e in data["ability_entries"]]
        assert "feat.feat_cleave" in content_ids
        assert "feat.feat_quickdraw" in content_ids

    def test_active_feat_entry_semantics(self):
        prov = _make_provenance()
        entry = map_feat_to_entry(ACTIVE_FEAT_WITH_TRIGGER, prov)
        assert entry.content_id == "feat.feat_cleave"
        # Cleave grants extra_melee_attack_on_kill → "attack" in grants_action
        assert entry.delivery_mode == DeliveryMode.TOUCH
        assert entry.scale == Scale.MODERATE


# ═══════════════════════════════════════════════════════════════════════
# Test 12: Stage interface compliance
# ═══════════════════════════════════════════════════════════════════════


class TestStageInterface:
    """SemanticsStage conforms to CompileStage interface."""

    def test_stage_id(self):
        stage = SemanticsStage()
        assert stage.stage_id == "semantics"

    def test_stage_number(self):
        stage = SemanticsStage()
        assert stage.stage_number == 3

    def test_depends_on_empty(self):
        stage = SemanticsStage()
        assert stage.depends_on == ()

    def test_execute_returns_stage_result(self, tmp_path):
        context = _make_context(tmp_path)
        stage = SemanticsStage()
        result = stage.execute(context)
        assert isinstance(result, StageResult)
        assert result.stage_id == "semantics"
        assert result.success
        assert "presentation_semantics.json" in result.artifacts

    def test_execute_writes_output_file(self, tmp_path):
        context = _make_context(tmp_path)
        stage = SemanticsStage()
        stage.execute(context)
        output_path = context.workspace_dir / "presentation_semantics.json"
        assert output_path.exists()


# ═══════════════════════════════════════════════════════════════════════
# Additional edge case tests
# ═══════════════════════════════════════════════════════════════════════


class TestDeliveryModeEdgeCases:
    """Edge cases for delivery mode mapping."""

    def test_ray_maps_to_beam(self):
        spell = {"target_type": "ray", "aoe_shape": None, "effect_type": "damage",
                 "range_formula": "close"}
        assert map_delivery_mode(spell) == DeliveryMode.BEAM

    def test_emanation_maps_to_emanation(self):
        spell = {"target_type": "area", "aoe_shape": "emanation",
                 "effect_type": "buff", "range_formula": ""}
        assert map_delivery_mode(spell) == DeliveryMode.EMANATION

    def test_line_maps_to_line(self):
        assert map_delivery_mode(LIGHTNING_LINE) == DeliveryMode.LINE

    def test_self_maps_to_self(self):
        assert map_delivery_mode(ILLUSION_SELF) == DeliveryMode.SELF

    def test_summoning_maps_to_summon(self):
        spell = {"target_type": "single", "aoe_shape": None,
                 "effect_type": "summoning", "range_formula": "close"}
        assert map_delivery_mode(spell) == DeliveryMode.SUMMON

    def test_single_ranged_maps_to_projectile(self):
        spell = {"target_type": "single", "aoe_shape": None,
                 "effect_type": "damage", "range_formula": "medium"}
        assert map_delivery_mode(spell) == DeliveryMode.PROJECTILE

    def test_spread_maps_to_burst_from_point(self):
        spell = {"target_type": "area", "aoe_shape": "spread",
                 "effect_type": "damage", "range_formula": "long"}
        assert map_delivery_mode(spell) == DeliveryMode.BURST_FROM_POINT


class TestStagingEdgeCases:
    """Edge cases for staging mapping."""

    def test_concentration_channeled(self):
        spell = {"duration_formula": "1_min_per_CL", "concentration": True,
                 "aoe_shape": None}
        assert map_staging(spell) == Staging.CHANNELED

    def test_round_duration_linger(self):
        spell = {"duration_formula": "1_round_per_CL", "concentration": False,
                 "aoe_shape": None}
        assert map_staging(spell) == Staging.LINGER

    def test_illusion_self_staging(self):
        # duration has "min", not "round" → INSTANT (default)
        assert map_staging(ILLUSION_SELF) == Staging.INSTANT


class TestVfxSfxEdgeCases:
    """Edge cases for VFX/SFX tag generation."""

    def test_illusion_vfx_tags(self):
        vfx = map_vfx_tags(ILLUSION_SELF)
        assert "shimmer" in vfx
        assert "distortion" in vfx

    def test_no_damage_type_uses_school(self):
        spell = {"damage_type": None, "school_category": "abjuration",
                 "effect_type": "utility"}
        vfx = map_vfx_tags(spell)
        assert "shield" in vfx
        assert "ward" in vfx

    def test_empty_spell_gets_generic(self):
        spell = {"damage_type": None, "school_category": "universal",
                 "effect_type": "other"}
        vfx = map_vfx_tags(spell)
        assert vfx == ("generic_magic",)

    def test_empty_sfx_gets_generic(self):
        spell = {"damage_type": None, "effect_type": "other"}
        sfx = map_sfx_tags(spell)
        assert sfx == ("generic_cast",)

    def test_deduplication(self):
        # Necromancy healing (both produce "shadow" tags via different routes)
        spell = {"damage_type": None, "school_category": "necromancy",
                 "effect_type": "healing"}
        vfx = map_vfx_tags(spell)
        assert len(vfx) == len(set(vfx)), "VFX tags should be deduplicated"


class TestEmptyContentPack:
    """Stage handles empty content pack gracefully."""

    def test_no_spells_no_feats(self, tmp_path):
        content_dir = tmp_path / "content_pack"
        content_dir.mkdir()
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        context = CompileContext(
            content_pack_dir=content_dir,
            workspace_dir=workspace,
            world_seed=42,
            world_theme_brief={},
            toolchain_pins={"llm_model_id": "stub"},
            content_pack_id="empty_pack",
            world_id="b" * 32,
        )

        stage = SemanticsStage()
        result = stage.execute(context)
        assert result.success

        output_path = workspace / "presentation_semantics.json"
        with open(output_path, "r") as f:
            data = json.load(f)

        assert len(data["ability_entries"]) == 0
        assert len(data["event_entries"]) == 18
