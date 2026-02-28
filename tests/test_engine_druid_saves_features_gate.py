"""Gate tests — WO-ENGINE-DRUID-SAVES-FEATURES-001.

RNL-001 through RNL-004: Resist Nature's Lure (+4 vs fey, druid L4+).
NS-001 through NS-004: Nature Sense (+2 Knowledge/nature + Survival, druid L1+).
8 tests total.

Pre-existing failures: 149. Any new failures beyond 149 are regressions.
"""
import pytest

from aidm.core.save_resolver import get_save_bonus
from aidm.core.skill_resolver import resolve_skill_check
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.saves import SaveType
from aidm.chargen.builder import build_character
from aidm.core.rng_protocol import RNGProvider
from copy import deepcopy


def _ws(entities):
    return WorldState(ruleset_version="3.5", entities=deepcopy(entities), active_combat=None)


class _FixedRNG:
    def stream(self, name):
        return self
    def randint(self, lo, hi):
        return lo


# ===========================================================================
# Resist Nature's Lure (RNL)
# ===========================================================================

def _druid_entity(druid_level: int):
    """Build minimal druid entity — bypasses chargen to test save_resolver in isolation."""
    entity = {
        EF.CLASS_LEVELS: {"druid": druid_level},
        EF.SAVE_FORT: 4, EF.SAVE_REF: 1, EF.SAVE_WILL: 6,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
    }
    if druid_level >= 4:
        entity[EF.RESIST_NATURES_LURE] = True
    return entity


def test_rnl_001_druid_l4_fey_save_bonus():
    """Druid L4: save vs fey supernatural → +4 from Resist Nature's Lure."""
    entity = _druid_entity(4)
    ws = _ws({"druid1": entity})

    bonus_without = get_save_bonus(ws, "druid1", SaveType.WILL, save_descriptor="")
    bonus_with = get_save_bonus(ws, "druid1", SaveType.WILL, save_descriptor="fey")

    assert bonus_with - bonus_without == 4, (
        f"Resist Nature's Lure should add +4 vs fey. "
        f"Without: {bonus_without}, With: {bonus_with}"
    )


def test_rnl_002_druid_l3_no_bonus():
    """Druid L3 (below threshold): no Resist Nature's Lure bonus."""
    entity = _druid_entity(3)
    ws = _ws({"druid1": entity})

    bonus_without = get_save_bonus(ws, "druid1", SaveType.WILL, save_descriptor="")
    bonus_with = get_save_bonus(ws, "druid1", SaveType.WILL, save_descriptor="fey")

    assert bonus_with == bonus_without, (
        f"Druid L3 should NOT have Resist Nature's Lure (+4 vs fey). "
        f"Without: {bonus_without}, With: {bonus_with}"
    )


def test_rnl_003_druid_l4_non_fey_save_no_bonus():
    """Druid L4: non-fey save → no Resist Nature's Lure bonus."""
    entity = _druid_entity(4)
    ws = _ws({"druid1": entity})

    bonus_fey = get_save_bonus(ws, "druid1", SaveType.WILL, save_descriptor="fey")
    bonus_spell = get_save_bonus(ws, "druid1", SaveType.WILL, save_descriptor="spell")

    # spell descriptor should not trigger RNL
    assert bonus_fey - bonus_spell == 4, (
        f"RNL should fire for 'fey' but not 'spell'. fey={bonus_fey}, spell={bonus_spell}"
    )


def test_rnl_004_multiclass_druid4_fighter4():
    """Multiclass Druid 4/Fighter 4: Resist Nature's Lure fires (druid levels only)."""
    entity = build_character(
        race="human",
        class_name="druid",
        level=8,
        class_mix={"druid": 4, "fighter": 4},
        ability_overrides={"str": 12, "dex": 10, "con": 14, "int": 10, "wis": 16, "cha": 8},
    )
    ws = _ws({"multidruid1": entity})

    assert entity.get(EF.RESIST_NATURES_LURE) is True, "RESIST_NATURES_LURE must be set at chargen for Druid 4"

    bonus_without = get_save_bonus(ws, "multidruid1", SaveType.WILL, save_descriptor="")
    bonus_with = get_save_bonus(ws, "multidruid1", SaveType.WILL, save_descriptor="fey")
    assert bonus_with - bonus_without == 4


# ===========================================================================
# Nature Sense (NS)
# ===========================================================================

def test_ns_001_druid_l1_knowledge_nature():
    """Druid L1: Knowledge (nature) check gets +2 from Nature Sense."""
    entity = build_character(
        race="human",
        class_name="druid",
        level=1,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 14, "wis": 14, "cha": 10},
        feat_choices=[],
        skill_allocations={"knowledge_nature": 4},
    )

    # Check RACIAL_SKILL_BONUS dict is populated
    skill_bonuses = entity.get(EF.RACIAL_SKILL_BONUS, {})
    assert skill_bonuses.get("knowledge_nature", 0) == 2, (
        f"Nature Sense should write +2 to RACIAL_SKILL_BONUS['knowledge_nature']. Got: {skill_bonuses}"
    )

    # Verify it is consumed in resolve_skill_check (entity dict path, not WorldState)
    rng = _FixedRNG()
    result_with_ns = resolve_skill_check(entity, "knowledge_nature", dc=10, rng=rng)
    entity_no_ns = {**entity, EF.RACIAL_SKILL_BONUS: {}}
    result_no_ns = resolve_skill_check(entity_no_ns, "knowledge_nature", dc=10, rng=rng)
    assert result_with_ns.total - result_no_ns.total == 2, (
        f"Nature Sense +2 must appear in skill total. "
        f"With NS: {result_with_ns.total}, Without: {result_no_ns.total}"
    )


def test_ns_002_druid_l1_survival():
    """Druid L1: Survival check gets +2 from Nature Sense."""
    entity = build_character(
        race="human",
        class_name="druid",
        level=1,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 10},
        feat_choices=[],
        skill_allocations={"survival": 4},
    )

    skill_bonuses = entity.get(EF.RACIAL_SKILL_BONUS, {})
    assert skill_bonuses.get("survival", 0) == 2, (
        f"Nature Sense should write +2 to RACIAL_SKILL_BONUS['survival']. Got: {skill_bonuses}"
    )


def test_ns_003_druid_l1_wrong_skill_no_bonus():
    """Druid L1: Knowledge (arcana) check gets NO Nature Sense bonus."""
    entity = build_character(
        race="human",
        class_name="druid",
        level=1,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 14, "wis": 14, "cha": 10},
        feat_choices=[],
        skill_allocations={"knowledge_arcana": 4},
    )

    skill_bonuses = entity.get(EF.RACIAL_SKILL_BONUS, {})
    assert skill_bonuses.get("knowledge_arcana", 0) == 0, (
        f"Nature Sense should NOT add to knowledge_arcana. Got: {skill_bonuses}"
    )


def test_ns_004_multiclass_druid1_ranger5():
    """Multiclass Druid 1/Ranger 5: Nature Sense present (Druid L1 always has it)."""
    entity = build_character(
        race="human",
        class_name="druid",
        level=6,
        class_mix={"druid": 1, "ranger": 5},
        ability_overrides={"str": 14, "dex": 12, "con": 12, "int": 10, "wis": 14, "cha": 8},
        skill_allocations={"knowledge_nature": 4},
    )

    skill_bonuses = entity.get(EF.RACIAL_SKILL_BONUS, {})
    assert skill_bonuses.get("knowledge_nature", 0) == 2, (
        f"Multiclass Druid1/Ranger5 should have Nature Sense +2 on knowledge_nature. Got: {skill_bonuses}"
    )
    assert skill_bonuses.get("survival", 0) == 2, (
        f"Multiclass Druid1/Ranger5 should have Nature Sense +2 on survival. Got: {skill_bonuses}"
    )
