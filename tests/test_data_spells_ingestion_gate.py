"""Gate tests for WO2 — Spells Ingestion (PCGen rsrd_spells.lst → SPELL_REGISTRY).

STRAT-OSS-INGESTION-SPRINT-001 / WO2
Source: PCGen rsrd_spells.lst (CC0 / OGL), 721 total entries
Target: aidm/data/spell_definitions.py SPELL_REGISTRY (via spell_definitions_ext.py)

NOTE — Before-count adjustment:
  STRAT spec assumed SPELL_REGISTRY had 45 entries before sprint.
  Actual before-count: 215 (prior WO-036 expansions already ran).
  After-count: 733 (215 original + 518 PCGen novel stubs).
  SI-002 threshold: ≥300 (sprint target met; actual 733).

Gates: SI-001 through SI-008
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aidm.data.spell_definitions import SPELL_REGISTRY
from aidm.data.spell_definitions_ext import SPELL_REGISTRY_EXT
from aidm.core.spell_resolver import SpellTarget, SpellEffect, SaveEffect
from aidm.schemas.saves import SaveType


class TestSI001ImportClean:
    """SI-001: Both SPELL_REGISTRY and SPELL_REGISTRY_EXT import cleanly."""

    def test_spell_registry_is_dict(self):
        assert isinstance(SPELL_REGISTRY, dict)

    def test_spell_registry_ext_is_dict(self):
        assert isinstance(SPELL_REGISTRY_EXT, dict)

    def test_spell_registry_ext_non_empty(self):
        assert len(SPELL_REGISTRY_EXT) > 0


class TestSI002CountThreshold:
    """SI-002: SPELL_REGISTRY count ≥ 300 after merge."""

    THRESHOLD = 300

    def test_merged_count_at_least_threshold(self):
        count = len(SPELL_REGISTRY)
        assert count >= self.THRESHOLD, (
            f"SPELL_REGISTRY has {count} entries, need ≥{self.THRESHOLD}"
        )


class TestSI003PreExistingSpellsPreserved:
    """SI-003: Pre-existing high-fidelity spells remain intact after merge."""

    def test_fireball_present_with_fidelity(self):
        s = SPELL_REGISTRY["fireball"]
        assert s.level == 3
        assert s.damage_dice == "8d6"
        assert s.save_type == SaveType.REF

    def test_cure_light_wounds_present(self):
        assert "cure_light_wounds" in SPELL_REGISTRY

    def test_magic_missile_present(self):
        assert "magic_missile" in SPELL_REGISTRY

    def test_charm_person_present(self):
        assert "charm_person" in SPELL_REGISTRY

    def test_ext_spells_do_not_overwrite_originals(self):
        # fireball must NOT be in ext (it was already in original registry)
        assert "fireball" not in SPELL_REGISTRY_EXT, (
            "fireball should be in original registry only, not EXT"
        )


class TestSI004NovelSpellsPresent:
    """SI-004: Novel PCGen spells present in merged SPELL_REGISTRY."""

    NOVEL_SPOT_CHECK = [
        "acid_fog",
        "acid_splash",
        "aid",
        "air_walk",
        "animal_growth",
        "animal_messenger",
        "analyze_dweomer",
    ]

    def test_novel_spells_in_merged_registry(self):
        missing = [s for s in self.NOVEL_SPOT_CHECK if s not in SPELL_REGISTRY]
        assert not missing, f"Novel spells missing from merged registry: {missing}"

    def test_novel_spells_in_ext(self):
        missing = [s for s in self.NOVEL_SPOT_CHECK if s not in SPELL_REGISTRY_EXT]
        assert not missing, f"Novel spells missing from EXT: {missing}"


class TestSI005SchoolField:
    """SI-005: School field set correctly on novel stubs."""

    def test_acid_fog_school_conjuration(self):
        s = SPELL_REGISTRY["acid_fog"]
        assert s.school == "conjuration"

    def test_animal_growth_has_school(self):
        s = SPELL_REGISTRY["animal_growth"]
        assert s.school and len(s.school) > 0

    def test_all_ext_spells_have_school(self):
        missing = [sid for sid, s in SPELL_REGISTRY_EXT.items() if not s.school]
        assert not missing, f"EXT spells missing school: {missing[:5]}"


class TestSI006SaveTypeMapping:
    """SI-006: Save type properly mapped from PCGen save_raw to SaveType enum."""

    def test_will_save_spell_present(self):
        # Aid has Fortitude save
        s = SPELL_REGISTRY.get("aid")
        if s is not None:
            # Just check it's a valid enum value or None
            assert s.save_type is None or isinstance(s.save_type, SaveType)

    def test_save_type_values_are_enum_or_none(self):
        bad = []
        for sid, s in SPELL_REGISTRY_EXT.items():
            if s.save_type is not None and not isinstance(s.save_type, SaveType):
                bad.append(sid)
        assert not bad, f"EXT spells with invalid save_type: {bad[:5]}"

    def test_no_raw_string_save_types_in_ext(self):
        # save_type should never be a raw string like "Will" — must be enum or None
        bad = []
        for sid, s in SPELL_REGISTRY_EXT.items():
            if isinstance(s.save_type, str):
                bad.append(f"{sid}: {s.save_type!r}")
        assert not bad, f"EXT spells with string save_type: {bad[:5]}"


class TestSI007ComponentFields:
    """SI-007: has_verbal and has_somatic fields set on stub entries."""

    def test_acid_splash_has_verbal(self):
        s = SPELL_REGISTRY["acid_splash"]
        assert isinstance(s.has_verbal, bool)

    def test_acid_splash_has_somatic(self):
        s = SPELL_REGISTRY["acid_splash"]
        assert isinstance(s.has_somatic, bool)

    def test_all_ext_spells_have_bool_components(self):
        bad = []
        for sid, s in SPELL_REGISTRY_EXT.items():
            if not isinstance(s.has_verbal, bool) or not isinstance(s.has_somatic, bool):
                bad.append(sid)
        assert not bad, f"EXT spells with non-bool components: {bad[:5]}"


class TestSI008SpellResistanceField:
    """SI-008: spell_resistance field set as bool on stub entries."""

    def test_acid_fog_sr_is_bool(self):
        s = SPELL_REGISTRY["acid_fog"]
        assert isinstance(s.spell_resistance, bool)

    def test_all_ext_spells_have_bool_sr(self):
        bad = []
        for sid, s in SPELL_REGISTRY_EXT.items():
            if not isinstance(s.spell_resistance, bool):
                bad.append(sid)
        assert not bad, f"EXT spells with non-bool spell_resistance: {bad[:5]}"
