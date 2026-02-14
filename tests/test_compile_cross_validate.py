"""WO-COMPILE-VALIDATE-001: Compile-Time Cross-Validation tests.

Tests:
  1. CT-001: single target_type + AoE delivery_mode → FAIL
  2. CT-002: area_shape/delivery_mode mismatch → FAIL
  3. CT-003: range_ft=0 + wrong origin_rule/delivery_mode → FAIL
  4. CT-004: damage band / scale mismatch → WARN
  5. CT-005: no save_type + DELAYED staging → WARN
  6. CT-006: contraindication self-conflict → WARN
  7. CT-007: residue vs staging mismatch → WARN
  8. content_id emission in spell event payloads
  9. Pipeline activation: content_id → NarrativeBrief.presentation_semantics
  10. CrossValidateStage integration: FAIL blocks, WARN passes
  11. Clean data produces zero violations
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from aidm.core.compile_stages._base import CompileContext, StageResult
from aidm.core.compile_stages.cross_validate import (
    CompileValidationError,
    CompileViolation,
    CrossValidateStage,
    _check_ct_001,
    _check_ct_002,
    _check_ct_003,
    _check_ct_004,
    _check_ct_005,
    _check_ct_006,
    _check_ct_007,
    _estimate_damage_band,
    cross_validate,
)
from aidm.schemas.presentation_semantics import (
    AbilityPresentationEntry,
    DeliveryMode,
    OriginRule,
    Scale,
    SemanticsProvenance,
    Staging,
)
from aidm.schemas.rulebook import RuleEntry, RuleParameters, RuleProvenance


# ═══════════════════════════════════════════════════════════════════════
# Test fixtures
# ═══════════════════════════════════════════════════════════════════════


def _prov() -> SemanticsProvenance:
    return SemanticsProvenance(
        source="test",
        compiler_version="0.1.0",
        seed_used=42,
        content_pack_id="test_pack",
    )


def _rule_prov() -> RuleProvenance:
    return RuleProvenance(
        source="test",
        compiler_version="0.1.0",
        seed_used=42,
        content_pack_id="test_pack",
    )


def _make_rule_entry(
    content_id: str = "spell.test_spell",
    rule_type: str = "spell",
    **params_kwargs,
) -> RuleEntry:
    return RuleEntry(
        content_id=content_id,
        procedure_id=f"proc.{content_id}",
        rule_type=rule_type,
        world_name=content_id,
        parameters=RuleParameters(**params_kwargs),
        provenance=_rule_prov(),
    )


def _make_ability_entry(
    content_id: str = "spell.test_spell",
    delivery_mode: DeliveryMode = DeliveryMode.PROJECTILE,
    staging: Staging = Staging.INSTANT,
    origin_rule: OriginRule = OriginRule.FROM_CASTER,
    scale: Scale = Scale.MODERATE,
    vfx_tags: tuple = ("fire",),
    sfx_tags: tuple = ("whoosh",),
    residue: tuple = (),
    contraindications: tuple = (),
) -> AbilityPresentationEntry:
    return AbilityPresentationEntry(
        content_id=content_id,
        delivery_mode=delivery_mode,
        staging=staging,
        origin_rule=origin_rule,
        vfx_tags=vfx_tags,
        sfx_tags=sfx_tags,
        scale=scale,
        provenance=_prov(),
        residue=residue,
        contraindications=contraindications,
    )


# ═══════════════════════════════════════════════════════════════════════
# Test 1: CT-001 — Delivery Mode vs Target Type
# ═══════════════════════════════════════════════════════════════════════


class TestCT001:
    """single target_type + AoE delivery_mode → FAIL."""

    def test_single_with_burst_fails(self):
        v = _check_ct_001(
            "spell.bad",
            RuleParameters(target_type="single"),
            _make_ability_entry(delivery_mode=DeliveryMode.BURST_FROM_POINT),
        )
        assert v is not None
        assert v.severity == "FAIL"
        assert v.check_id == "CT-001"

    def test_single_with_cone_fails(self):
        v = _check_ct_001(
            "spell.bad",
            RuleParameters(target_type="single"),
            _make_ability_entry(delivery_mode=DeliveryMode.CONE),
        )
        assert v is not None
        assert v.severity == "FAIL"

    def test_single_with_line_fails(self):
        v = _check_ct_001(
            "spell.bad",
            RuleParameters(target_type="single"),
            _make_ability_entry(delivery_mode=DeliveryMode.LINE),
        )
        assert v is not None
        assert v.severity == "FAIL"

    def test_single_with_emanation_fails(self):
        v = _check_ct_001(
            "spell.bad",
            RuleParameters(target_type="single"),
            _make_ability_entry(delivery_mode=DeliveryMode.EMANATION),
        )
        assert v is not None
        assert v.severity == "FAIL"

    def test_single_with_projectile_passes(self):
        v = _check_ct_001(
            "spell.ok",
            RuleParameters(target_type="single"),
            _make_ability_entry(delivery_mode=DeliveryMode.PROJECTILE),
        )
        assert v is None

    def test_area_with_burst_passes(self):
        v = _check_ct_001(
            "spell.ok",
            RuleParameters(target_type="area"),
            _make_ability_entry(delivery_mode=DeliveryMode.BURST_FROM_POINT),
        )
        assert v is None

    def test_none_target_type_passes(self):
        v = _check_ct_001(
            "spell.ok",
            RuleParameters(target_type=None),
            _make_ability_entry(delivery_mode=DeliveryMode.BURST_FROM_POINT),
        )
        assert v is None


# ═══════════════════════════════════════════════════════════════════════
# Test 2: CT-002 — Delivery Mode vs Area Shape
# ═══════════════════════════════════════════════════════════════════════


class TestCT002:
    """area_shape must match delivery_mode."""

    def test_burst_requires_burst_from_point(self):
        v = _check_ct_002(
            "spell.bad",
            RuleParameters(area_shape="burst"),
            _make_ability_entry(delivery_mode=DeliveryMode.CONE),
        )
        assert v is not None
        assert v.severity == "FAIL"
        assert v.check_id == "CT-002"

    def test_burst_with_burst_from_point_passes(self):
        v = _check_ct_002(
            "spell.ok",
            RuleParameters(area_shape="burst"),
            _make_ability_entry(delivery_mode=DeliveryMode.BURST_FROM_POINT),
        )
        assert v is None

    def test_cone_requires_cone(self):
        v = _check_ct_002(
            "spell.bad",
            RuleParameters(area_shape="cone"),
            _make_ability_entry(delivery_mode=DeliveryMode.BURST_FROM_POINT),
        )
        assert v is not None
        assert v.severity == "FAIL"

    def test_cone_with_cone_passes(self):
        v = _check_ct_002(
            "spell.ok",
            RuleParameters(area_shape="cone"),
            _make_ability_entry(delivery_mode=DeliveryMode.CONE),
        )
        assert v is None

    def test_line_requires_line(self):
        v = _check_ct_002(
            "spell.bad",
            RuleParameters(area_shape="line"),
            _make_ability_entry(delivery_mode=DeliveryMode.PROJECTILE),
        )
        assert v is not None
        assert v.severity == "FAIL"

    def test_line_with_line_passes(self):
        v = _check_ct_002(
            "spell.ok",
            RuleParameters(area_shape="line"),
            _make_ability_entry(delivery_mode=DeliveryMode.LINE),
        )
        assert v is None

    def test_none_area_shape_passes(self):
        v = _check_ct_002(
            "spell.ok",
            RuleParameters(area_shape=None),
            _make_ability_entry(delivery_mode=DeliveryMode.PROJECTILE),
        )
        assert v is None

    def test_non_mapped_area_shape_passes(self):
        """Shapes not in the explicit map (e.g., 'emanation') skip CT-002."""
        v = _check_ct_002(
            "spell.ok",
            RuleParameters(area_shape="emanation"),
            _make_ability_entry(delivery_mode=DeliveryMode.EMANATION),
        )
        assert v is None


# ═══════════════════════════════════════════════════════════════════════
# Test 3: CT-003 — Origin Rule vs Delivery Mode for range_ft=0
# ═══════════════════════════════════════════════════════════════════════


class TestCT003:
    """range_ft=0 requires FROM_CASTER + TOUCH/SELF."""

    def test_range_0_projectile_fails(self):
        v = _check_ct_003(
            "spell.bad",
            RuleParameters(range_ft=0),
            _make_ability_entry(
                delivery_mode=DeliveryMode.PROJECTILE,
                origin_rule=OriginRule.FROM_CASTER,
            ),
        )
        assert v is not None
        assert v.severity == "FAIL"
        assert v.check_id == "CT-003"

    def test_range_0_wrong_origin_fails(self):
        v = _check_ct_003(
            "spell.bad",
            RuleParameters(range_ft=0),
            _make_ability_entry(
                delivery_mode=DeliveryMode.TOUCH,
                origin_rule=OriginRule.FROM_CHOSEN_POINT,
            ),
        )
        assert v is not None
        assert v.severity == "FAIL"

    def test_range_0_touch_from_caster_passes(self):
        v = _check_ct_003(
            "spell.ok",
            RuleParameters(range_ft=0),
            _make_ability_entry(
                delivery_mode=DeliveryMode.TOUCH,
                origin_rule=OriginRule.FROM_CASTER,
            ),
        )
        assert v is None

    def test_range_0_self_from_caster_passes(self):
        v = _check_ct_003(
            "spell.ok",
            RuleParameters(range_ft=0),
            _make_ability_entry(
                delivery_mode=DeliveryMode.SELF,
                origin_rule=OriginRule.FROM_CASTER,
            ),
        )
        assert v is None

    def test_nonzero_range_skips(self):
        v = _check_ct_003(
            "spell.ok",
            RuleParameters(range_ft=30),
            _make_ability_entry(
                delivery_mode=DeliveryMode.BURST_FROM_POINT,
                origin_rule=OriginRule.FROM_CHOSEN_POINT,
            ),
        )
        assert v is None

    def test_none_range_skips(self):
        v = _check_ct_003(
            "spell.ok",
            RuleParameters(range_ft=None),
            _make_ability_entry(
                delivery_mode=DeliveryMode.BURST_FROM_POINT,
                origin_rule=OriginRule.FROM_CHOSEN_POINT,
            ),
        )
        assert v is None


# ═══════════════════════════════════════════════════════════════════════
# Test 4: CT-004 — Scale vs Damage Magnitude
# ═══════════════════════════════════════════════════════════════════════


class TestCT004:
    """Damage band must roughly match scale."""

    def test_2d6_expects_subtle(self):
        assert _estimate_damage_band("2d6") == Scale.SUBTLE

    def test_6d6_expects_moderate(self):
        assert _estimate_damage_band("6d6") == Scale.MODERATE

    def test_8d6_expects_dramatic(self):
        assert _estimate_damage_band("8d6") == Scale.DRAMATIC

    def test_20d6_expects_catastrophic(self):
        assert _estimate_damage_band("20d6") == Scale.CATASTROPHIC

    def test_mismatch_warns(self):
        v = _check_ct_004(
            "spell.bad",
            RuleParameters(damage_dice="2d6"),
            _make_ability_entry(scale=Scale.CATASTROPHIC),
        )
        assert v is not None
        assert v.severity == "WARN"
        assert v.check_id == "CT-004"

    def test_match_passes(self):
        v = _check_ct_004(
            "spell.ok",
            RuleParameters(damage_dice="8d6"),
            _make_ability_entry(scale=Scale.DRAMATIC),
        )
        assert v is None

    def test_no_damage_dice_passes(self):
        v = _check_ct_004(
            "spell.ok",
            RuleParameters(damage_dice=None),
            _make_ability_entry(scale=Scale.CATASTROPHIC),
        )
        assert v is None

    def test_unparseable_dice_passes(self):
        v = _check_ct_004(
            "spell.ok",
            RuleParameters(damage_dice="special"),
            _make_ability_entry(scale=Scale.MODERATE),
        )
        assert v is None


# ═══════════════════════════════════════════════════════════════════════
# Test 5: CT-005 — Save Type vs Staging
# ═══════════════════════════════════════════════════════════════════════


class TestCT005:
    """No save + DELAYED staging → WARN."""

    def test_no_save_delayed_warns(self):
        v = _check_ct_005(
            "spell.bad",
            RuleParameters(save_type=None),
            _make_ability_entry(staging=Staging.DELAYED),
        )
        assert v is not None
        assert v.severity == "WARN"
        assert v.check_id == "CT-005"

    def test_has_save_delayed_passes(self):
        v = _check_ct_005(
            "spell.ok",
            RuleParameters(save_type="reflex"),
            _make_ability_entry(staging=Staging.DELAYED),
        )
        assert v is None

    def test_no_save_instant_passes(self):
        v = _check_ct_005(
            "spell.ok",
            RuleParameters(save_type=None),
            _make_ability_entry(staging=Staging.INSTANT),
        )
        assert v is None


# ═══════════════════════════════════════════════════════════════════════
# Test 6: CT-006 — Contraindication Self-Conflict
# ═══════════════════════════════════════════════════════════════════════


class TestCT006:
    """Tag in contraindications that's also in vfx_tags/sfx_tags → WARN."""

    def test_contra_in_vfx_warns(self):
        v = _check_ct_006(
            "spell.bad",
            RuleParameters(),
            _make_ability_entry(
                vfx_tags=("fire", "glow"),
                contraindications=("fire",),
            ),
        )
        assert v is not None
        assert v.severity == "WARN"
        assert v.check_id == "CT-006"

    def test_contra_in_sfx_warns(self):
        v = _check_ct_006(
            "spell.bad",
            RuleParameters(),
            _make_ability_entry(
                sfx_tags=("sizzle", "hiss"),
                contraindications=("hiss",),
            ),
        )
        assert v is not None
        assert v.severity == "WARN"

    def test_no_overlap_passes(self):
        v = _check_ct_006(
            "spell.ok",
            RuleParameters(),
            _make_ability_entry(
                vfx_tags=("fire",),
                sfx_tags=("whoosh",),
                contraindications=("water",),
            ),
        )
        assert v is None

    def test_empty_contraindications_passes(self):
        v = _check_ct_006(
            "spell.ok",
            RuleParameters(),
            _make_ability_entry(contraindications=()),
        )
        assert v is None


# ═══════════════════════════════════════════════════════════════════════
# Test 7: CT-007 — Residue vs Staging
# ═══════════════════════════════════════════════════════════════════════


class TestCT007:
    """instantaneous + residue → WARN; LINGER + no residue → WARN."""

    def test_instantaneous_with_residue_warns(self):
        v = _check_ct_007(
            "spell.bad",
            RuleParameters(duration_unit="instantaneous"),
            _make_ability_entry(residue=("scorch_mark",)),
        )
        assert v is not None
        assert v.severity == "WARN"
        assert v.check_id == "CT-007"

    def test_linger_without_residue_warns(self):
        v = _check_ct_007(
            "spell.bad",
            RuleParameters(duration_unit="rounds"),
            _make_ability_entry(staging=Staging.LINGER, residue=()),
        )
        assert v is not None
        assert v.severity == "WARN"
        assert v.check_id == "CT-007"

    def test_instantaneous_no_residue_passes(self):
        v = _check_ct_007(
            "spell.ok",
            RuleParameters(duration_unit="instantaneous"),
            _make_ability_entry(residue=()),
        )
        assert v is None

    def test_linger_with_residue_passes(self):
        v = _check_ct_007(
            "spell.ok",
            RuleParameters(duration_unit="rounds"),
            _make_ability_entry(staging=Staging.LINGER, residue=("shimmer",)),
        )
        assert v is None


# ═══════════════════════════════════════════════════════════════════════
# Test: cross_validate() integration
# ═══════════════════════════════════════════════════════════════════════


class TestCrossValidateFunction:
    """cross_validate() runs all 7 checks on shared content_ids."""

    def test_clean_data_zero_violations(self):
        rule_entries = {
            "spell.fireball": _make_rule_entry(
                content_id="spell.fireball",
                target_type="area",
                area_shape="burst",
                damage_dice="8d6",
                range_ft=400,
            ),
        }
        ability_entries = {
            "spell.fireball": _make_ability_entry(
                content_id="spell.fireball",
                delivery_mode=DeliveryMode.BURST_FROM_POINT,
                scale=Scale.DRAMATIC,
                origin_rule=OriginRule.FROM_CHOSEN_POINT,
            ),
        }
        violations = cross_validate(rule_entries, ability_entries)
        assert len(violations) == 0

    def test_single_fail_detected(self):
        rule_entries = {
            "spell.bad": _make_rule_entry(
                content_id="spell.bad",
                target_type="single",
                area_shape=None,
            ),
        }
        ability_entries = {
            "spell.bad": _make_ability_entry(
                content_id="spell.bad",
                delivery_mode=DeliveryMode.BURST_FROM_POINT,
            ),
        }
        violations = cross_validate(rule_entries, ability_entries)
        fails = [v for v in violations if v.severity == "FAIL"]
        assert len(fails) >= 1
        assert fails[0].check_id == "CT-001"

    def test_disjoint_content_ids_no_violations(self):
        """Content IDs in only one registry are silently skipped."""
        rule_entries = {"spell.only_in_rules": _make_rule_entry(content_id="spell.only_in_rules")}
        ability_entries = {"spell.only_in_semantics": _make_ability_entry(content_id="spell.only_in_semantics")}
        violations = cross_validate(rule_entries, ability_entries)
        assert len(violations) == 0

    def test_multiple_violations_accumulated(self):
        """Multiple violations from different checks are all collected."""
        rule_entries = {
            "spell.bad": _make_rule_entry(
                content_id="spell.bad",
                target_type="single",
                area_shape="burst",
            ),
        }
        ability_entries = {
            "spell.bad": _make_ability_entry(
                content_id="spell.bad",
                delivery_mode=DeliveryMode.CONE,
            ),
        }
        violations = cross_validate(rule_entries, ability_entries)
        check_ids = {v.check_id for v in violations}
        assert "CT-001" in check_ids  # single + CONE
        assert "CT-002" in check_ids  # burst ≠ CONE


# ═══════════════════════════════════════════════════════════════════════
# Test: CrossValidateStage
# ═══════════════════════════════════════════════════════════════════════


def _write_rule_registry(workspace: Path, entries: List[Dict[str, Any]]) -> None:
    """Write a minimal rule_registry.json."""
    data = {
        "schema_version": "1.0",
        "world_id": "test",
        "compiler_version": "0.1.0",
        "entry_count": len(entries),
        "entries": entries,
    }
    with open(workspace / "rule_registry.json", "w") as f:
        json.dump(data, f)


def _write_semantics_registry(workspace: Path, entries: List[Dict[str, Any]]) -> None:
    """Write a minimal presentation_semantics.json."""
    data = {
        "schema_version": "1.0",
        "world_id": "test",
        "compiler_version": "0.1.0",
        "ability_entry_count": len(entries),
        "event_entry_count": 0,
        "ability_entries": entries,
        "event_entries": [],
    }
    with open(workspace / "presentation_semantics.json", "w") as f:
        json.dump(data, f)


def _make_stage_context(tmp_path: Path) -> CompileContext:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    return CompileContext(
        content_pack_dir=content_dir,
        workspace_dir=workspace,
        world_seed=42,
        world_theme_brief={},
        toolchain_pins={"llm_model_id": "stub"},
        content_pack_id="test_pack",
        world_id="a" * 32,
    )


class TestCrossValidateStage:
    """CrossValidateStage integration."""

    def test_stage_properties(self):
        stage = CrossValidateStage()
        assert stage.stage_id == "cross_validate"
        assert stage.stage_number == 4
        assert "semantics" in stage.depends_on
        assert "rulebook" in stage.depends_on

    def test_clean_data_succeeds(self, tmp_path):
        ctx = _make_stage_context(tmp_path)

        rule = _make_rule_entry(
            content_id="spell.test",
            target_type="area",
            area_shape="burst",
            range_ft=400,
        )
        ability = _make_ability_entry(
            content_id="spell.test",
            delivery_mode=DeliveryMode.BURST_FROM_POINT,
            origin_rule=OriginRule.FROM_CHOSEN_POINT,
        )

        _write_rule_registry(ctx.workspace_dir, [rule.to_dict()])
        _write_semantics_registry(ctx.workspace_dir, [ability.to_dict()])

        stage = CrossValidateStage()
        result = stage.execute(ctx)
        assert result.status == "success"
        assert len(result.warnings) == 0

    def test_fail_violations_block(self, tmp_path):
        ctx = _make_stage_context(tmp_path)

        rule = _make_rule_entry(
            content_id="spell.bad",
            target_type="single",
        )
        ability = _make_ability_entry(
            content_id="spell.bad",
            delivery_mode=DeliveryMode.BURST_FROM_POINT,
        )

        _write_rule_registry(ctx.workspace_dir, [rule.to_dict()])
        _write_semantics_registry(ctx.workspace_dir, [ability.to_dict()])

        stage = CrossValidateStage()
        result = stage.execute(ctx)
        assert result.status == "failed"
        assert "CT-001" in result.error

    def test_warn_violations_pass_with_warnings(self, tmp_path):
        ctx = _make_stage_context(tmp_path)

        rule = _make_rule_entry(
            content_id="spell.warn",
            target_type="area",
            area_shape="burst",
            damage_dice="2d6",
            range_ft=400,
        )
        ability = _make_ability_entry(
            content_id="spell.warn",
            delivery_mode=DeliveryMode.BURST_FROM_POINT,
            origin_rule=OriginRule.FROM_CHOSEN_POINT,
            scale=Scale.CATASTROPHIC,  # 2d6 → SUBTLE, not CATASTROPHIC
        )

        _write_rule_registry(ctx.workspace_dir, [rule.to_dict()])
        _write_semantics_registry(ctx.workspace_dir, [ability.to_dict()])

        stage = CrossValidateStage()
        result = stage.execute(ctx)
        assert result.status == "success"
        assert len(result.warnings) > 0
        assert any("CT-004" in w for w in result.warnings)

    def test_missing_files_skips_gracefully(self, tmp_path):
        ctx = _make_stage_context(tmp_path)
        stage = CrossValidateStage()
        result = stage.execute(ctx)
        assert result.status == "success"
        assert len(result.warnings) > 0


# ═══════════════════════════════════════════════════════════════════════
# Test 8: content_id emission in spell event payloads
# ═══════════════════════════════════════════════════════════════════════


class TestContentIdEmission:
    """Spell events include content_id when SpellDefinition has one."""

    def test_spell_definition_has_content_id_field(self):
        from aidm.core.spell_resolver import SpellDefinition, SpellTarget
        spell = SpellDefinition(
            spell_id="test_fireball",
            name="Test Fireball",
            level=3,
            school="evocation",
            target_type=SpellTarget.AREA,
            range_ft=400,
            content_id="spell.spell_001",
        )
        assert spell.content_id == "spell.spell_001"
        d = spell.to_dict()
        assert d["content_id"] == "spell.spell_001"

    def test_spell_definition_content_id_defaults_none(self):
        from aidm.core.spell_resolver import SpellDefinition, SpellTarget
        spell = SpellDefinition(
            spell_id="test",
            name="Test",
            level=1,
            school="evocation",
            target_type=SpellTarget.SELF,
            range_ft=0,
        )
        assert spell.content_id is None
        d = spell.to_dict()
        assert d["content_id"] is None


# ═══════════════════════════════════════════════════════════════════════
# Test 9: Pipeline activation — content_id → presentation_semantics
# ═══════════════════════════════════════════════════════════════════════


class TestPipelineActivation:
    """NarrativeBrief populates presentation_semantics from event content_id."""

    def test_content_id_in_payload_activates_lookup(self):
        """Simulates the GAP-B-001 pipeline: event with content_id → registry
        lookup → NarrativeBrief.presentation_semantics is not None."""
        from aidm.lens.presentation_registry import PresentationRegistryLoader
        from aidm.schemas.presentation_semantics import PresentationSemanticsRegistry

        # Build a minimal registry with one ability entry
        ability = _make_ability_entry(
            content_id="spell.spell_001",
            delivery_mode=DeliveryMode.BURST_FROM_POINT,
        )
        registry = PresentationSemanticsRegistry(
            schema_version="1.0",
            world_id="test",
            compiler_version="0.1.0",
            ability_entry_count=1,
            event_entry_count=0,
            ability_entries=(ability,),
            event_entries=(),
        )
        loader = PresentationRegistryLoader(registry)

        # Simulate lookup as narrative_brief does (lines 726-729)
        content_id = "spell.spell_001"
        result = loader.get_ability_semantics(content_id)
        assert result is not None
        assert result.delivery_mode == DeliveryMode.BURST_FROM_POINT
        assert result.content_id == "spell.spell_001"

    def test_missing_content_id_returns_none(self):
        """Events without content_id get presentation_semantics: None."""
        from aidm.lens.presentation_registry import PresentationRegistryLoader
        from aidm.schemas.presentation_semantics import PresentationSemanticsRegistry

        registry = PresentationSemanticsRegistry(
            schema_version="1.0",
            world_id="test",
            compiler_version="0.1.0",
            ability_entry_count=0,
            event_entry_count=0,
            ability_entries=(),
            event_entries=(),
        )
        loader = PresentationRegistryLoader(registry)

        result = loader.get_ability_semantics("spell.nonexistent")
        assert result is None


# ═══════════════════════════════════════════════════════════════════════
# Test: CompileViolation and CompileValidationError
# ═══════════════════════════════════════════════════════════════════════


class TestCompileViolationError:
    """CompileValidationError carries violations."""

    def test_error_message_includes_details(self):
        v = CompileViolation(
            check_id="CT-001",
            content_id="spell.bad",
            severity="FAIL",
            detail="target_type/delivery_mode mismatch",
        )
        err = CompileValidationError([v])
        assert "CT-001" in str(err)
        assert "spell.bad" in str(err)
        assert len(err.violations) == 1

    def test_violation_is_frozen(self):
        v = CompileViolation(
            check_id="CT-001",
            content_id="spell.bad",
            severity="FAIL",
            detail="test",
        )
        with pytest.raises(AttributeError):
            v.check_id = "CT-999"


# ═══════════════════════════════════════════════════════════════════════
# Test: Contraindications population (WO-COMPILE-VALIDATE-001 §C1)
# ═══════════════════════════════════════════════════════════════════════


class TestContraindicationsPopulation:
    """SemanticsStage populates contraindications from damage_type."""

    def test_fire_spell_gets_contraindications(self):
        from aidm.core.compile_stages.semantics import map_contraindications
        spell = {"damage_type": "fire"}
        contra = map_contraindications(spell)
        assert "ice" in contra
        assert "frost" in contra
        assert "cold" in contra
        assert "frozen" in contra

    def test_cold_spell_gets_contraindications(self):
        from aidm.core.compile_stages.semantics import map_contraindications
        spell = {"damage_type": "cold"}
        contra = map_contraindications(spell)
        assert "fire" in contra
        assert "flame" in contra

    def test_acid_spell_gets_contraindications(self):
        from aidm.core.compile_stages.semantics import map_contraindications
        spell = {"damage_type": "acid"}
        contra = map_contraindications(spell)
        assert "clean" in contra
        assert "pristine" in contra

    def test_electricity_spell_gets_contraindications(self):
        from aidm.core.compile_stages.semantics import map_contraindications
        spell = {"damage_type": "electricity"}
        contra = map_contraindications(spell)
        assert "earth" in contra
        assert "grounded" in contra

    def test_sonic_spell_gets_contraindications(self):
        from aidm.core.compile_stages.semantics import map_contraindications
        spell = {"damage_type": "sonic"}
        contra = map_contraindications(spell)
        assert "silence" in contra
        assert "quiet" in contra

    def test_no_damage_type_empty_contraindications(self):
        from aidm.core.compile_stages.semantics import map_contraindications
        spell = {"damage_type": None}
        assert map_contraindications(spell) == ()

    def test_unknown_damage_type_empty_contraindications(self):
        from aidm.core.compile_stages.semantics import map_contraindications
        spell = {"damage_type": "force"}
        assert map_contraindications(spell) == ()

    def test_map_spell_to_entry_includes_contraindications(self):
        from aidm.core.compile_stages.semantics import map_spell_to_entry
        spell = {
            "template_id": "SPELL_FIREBALL",
            "tier": 3,
            "school_category": "evocation",
            "target_type": "area",
            "range_formula": "long",
            "aoe_shape": "burst",
            "aoe_radius_ft": 20,
            "effect_type": "damage",
            "damage_type": "fire",
            "duration_formula": "instantaneous",
            "concentration": False,
        }
        entry = map_spell_to_entry(spell, _prov())
        assert "ice" in entry.contraindications
        assert "frost" in entry.contraindications

    def test_ct_006_detects_fire_ability_with_ice_vfx(self):
        """End-to-end: fire ability has contraindication 'ice', and if
        someone adds 'ice' to vfx_tags, CT-006 catches it."""
        v = _check_ct_006(
            "spell.fire_bad",
            RuleParameters(),
            _make_ability_entry(
                vfx_tags=("fire", "ice", "glow"),
                contraindications=("ice", "frost", "cold", "frozen"),
            ),
        )
        assert v is not None
        assert v.severity == "WARN"
        assert v.check_id == "CT-006"
        assert "ice" in v.detail
