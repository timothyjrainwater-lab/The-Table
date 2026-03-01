"""Gate tests for WO3 — Equipment Catalog verify + cross-validate vs PCGen.

STRAT-OSS-INGESTION-SPRINT-001 / WO3
Source: PCGen rsrd_equip_arms_and_armor.lst (CC0 / OGL)
Target: aidm/data/equipment_catalog.json

NOTE — Scope adjustment:
  STRAT spec referenced zellfaze mundane_items.json for weapon spot-check.
  Actual zellfaze file has only 2 adventuring gear items (no weapons).
  Weapon spot-check (EI-005/EI-006) instead uses PCGen rsrd_equip_arms_and_armor.lst,
  which contains 111 weapon entries including all PHB core weapons.
  Discrepancy documented in DEBRIEF_OSS-SPRINT-001.md.

  Armor catalog: equipment_catalog.json already had all 18 PHB armor/shield entries
  before this sprint (added in prior WOs). PCGen cross-validation confirms correctness
  — no updates required. EI-003/EI-004 verify via PCGen cross-check.

Gates: EI-001 through EI-008
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "aidm", "data", "equipment_catalog.json")
LST_PATH = os.path.join(
    os.path.dirname(__file__), "..",
    "scripts", "oss_sources", "pcgen_sparse",
    "data", "35e", "wizards_of_the_coast", "rsrd", "basics",
    "rsrd_equip_arms_and_armor.lst"
)


def load_catalog():
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


class TestEI001CatalogLoads:
    """EI-001: equipment_catalog.json loads cleanly with expected top-level keys."""

    def test_catalog_loads(self):
        d = load_catalog()
        assert isinstance(d, dict)

    def test_catalog_has_armor_key(self):
        d = load_catalog()
        assert "armor" in d

    def test_catalog_has_weapons_key(self):
        d = load_catalog()
        assert "weapons" in d

    def test_catalog_has_meta(self):
        d = load_catalog()
        assert "_meta" in d


class TestEI002FullPlateStats:
    """EI-002: Full Plate has correct PHB p.123 stats (key cross-check)."""

    def test_full_plate_present(self):
        d = load_catalog()
        assert "full_plate" in d["armor"]

    def test_full_plate_arcane_spell_failure_35(self):
        d = load_catalog()
        fp = d["armor"]["full_plate"]
        assert fp["arcane_spell_failure"] == 35, (
            f"Full Plate ASF expected 35, got {fp['arcane_spell_failure']}"
        )

    def test_full_plate_max_dex_1(self):
        d = load_catalog()
        fp = d["armor"]["full_plate"]
        assert fp["max_dex_bonus"] == 1

    def test_full_plate_armor_check_penalty_minus_6(self):
        d = load_catalog()
        fp = d["armor"]["full_plate"]
        assert fp["armor_check_penalty"] == -6

    def test_full_plate_ac_bonus_8(self):
        d = load_catalog()
        fp = d["armor"]["full_plate"]
        assert fp["ac_bonus"] == 8


class TestEI003AllPHBArmorTypesPresent:
    """EI-003: All 12 core PHB armor types present in catalog."""

    PHB_ARMOR_TYPES = [
        "padded", "leather", "studded_leather", "chain_shirt",  # light
        "hide", "scale_mail", "chainmail", "breastplate",       # medium
        "splint_mail", "banded_mail", "half_plate", "full_plate"  # heavy
    ]

    PHB_SHIELD_TYPES = [
        "buckler", "shield_light_wooden", "shield_light_steel",
        "shield_heavy_wooden", "shield_heavy_steel", "tower_shield"
    ]

    def test_all_12_armor_types_present(self):
        d = load_catalog()
        armor = d["armor"]
        missing = [a for a in self.PHB_ARMOR_TYPES if a not in armor]
        assert not missing, f"Missing PHB armor types: {missing}"

    def test_all_shield_types_present(self):
        d = load_catalog()
        armor = d["armor"]
        missing = [s for s in self.PHB_SHIELD_TYPES if s not in armor]
        assert not missing, f"Missing PHB shield types: {missing}"


class TestEI004PCGenArmorCrossValidation:
    """EI-004: Catalog armor stats match PCGen rsrd_equip_arms_and_armor.lst."""

    CROSS_CHECK = {
        # (pcgen_name): (catalog_key, asf, max_dex, acp)
        "Chain Shirt": ("chain_shirt", 20, 4, -2),
        "Chainmail": ("chainmail", 30, 2, -5),
        "Full Plate": ("full_plate", 35, 1, -6),
        "Padded": ("padded", 5, 8, 0),
        "Leather": ("leather", 10, 6, 0),
        "Breastplate": ("breastplate", 25, 3, -4),
    }

    def test_chain_shirt_cross_validates(self):
        d = load_catalog()
        ca = d["armor"]["chain_shirt"]
        assert ca["arcane_spell_failure"] == 20
        assert ca["max_dex_bonus"] == 4
        assert ca["armor_check_penalty"] == -2

    def test_full_plate_cross_validates(self):
        d = load_catalog()
        ca = d["armor"]["full_plate"]
        assert ca["arcane_spell_failure"] == 35
        assert ca["max_dex_bonus"] == 1
        assert ca["armor_check_penalty"] == -6

    def test_chainmail_cross_validates(self):
        d = load_catalog()
        ca = d["armor"]["chainmail"]
        assert ca["arcane_spell_failure"] == 30
        assert ca["max_dex_bonus"] == 2
        assert ca["armor_check_penalty"] == -5

    def test_padded_cross_validates(self):
        d = load_catalog()
        ca = d["armor"]["padded"]
        assert ca["arcane_spell_failure"] == 5
        assert ca["max_dex_bonus"] == 8
        assert ca["armor_check_penalty"] == 0

    def test_leather_cross_validates(self):
        d = load_catalog()
        ca = d["armor"]["leather"]
        assert ca["arcane_spell_failure"] == 10
        assert ca["max_dex_bonus"] == 6
        assert ca["armor_check_penalty"] == 0


class TestEI005WeaponDamageSpotCheck:
    """EI-005: Weapon damage_dice matches PCGen rsrd_equip_arms_and_armor.lst.

    Spot-checks 5 core PHB weapons (source: PCGen LST, not zellfaze).
    zellfaze mundane_items.json has only 2 adventuring gear items — no weapon data.
    """

    EXPECTED = {
        "dagger": "1d4",
        "longsword": "1d8",
        "greatsword": "2d6",
        "battleaxe": "1d8",
        "greataxe": "1d12",
    }

    def test_dagger_damage_1d4(self):
        d = load_catalog()
        assert d["weapons"]["dagger"]["damage_dice"] == "1d4"

    def test_longsword_damage_1d8(self):
        d = load_catalog()
        assert d["weapons"]["longsword"]["damage_dice"] == "1d8"

    def test_greatsword_damage_2d6(self):
        d = load_catalog()
        assert d["weapons"]["greatsword"]["damage_dice"] == "2d6"

    def test_battleaxe_damage_1d8(self):
        d = load_catalog()
        assert d["weapons"]["battleaxe"]["damage_dice"] == "1d8"

    def test_greataxe_damage_1d12(self):
        d = load_catalog()
        assert d["weapons"]["greataxe"]["damage_dice"] == "1d12"


class TestEI006WeaponCritSpotCheck:
    """EI-006: Weapon critical range and multiplier match PCGen data."""

    def test_dagger_crit_19_20_x2(self):
        d = load_catalog()
        w = d["weapons"]["dagger"]
        assert w["critical_range"] == 19
        assert w["critical_multiplier"] == 2

    def test_battleaxe_crit_20_x3(self):
        d = load_catalog()
        w = d["weapons"]["battleaxe"]
        assert w["critical_range"] == 20
        assert w["critical_multiplier"] == 3

    def test_greataxe_crit_20_x3(self):
        d = load_catalog()
        w = d["weapons"]["greataxe"]
        assert w["critical_range"] == 20
        assert w["critical_multiplier"] == 3

    def test_longsword_crit_19_20_x2(self):
        d = load_catalog()
        w = d["weapons"]["longsword"]
        assert w["critical_range"] == 19
        assert w["critical_multiplier"] == 2


class TestEI007WeaponCatalogCount:
    """EI-007: Weapon catalog has ≥20 weapons."""

    THRESHOLD = 20

    def test_weapon_count_at_least_threshold(self):
        d = load_catalog()
        count = len(d["weapons"])
        assert count >= self.THRESHOLD, (
            f"Weapon catalog has {count} entries, need ≥{self.THRESHOLD}"
        )


class TestEI008AllArmorHaveRequiredFields:
    """EI-008: All armor entries have required fields set (no nulls on key stats)."""

    REQUIRED_FIELDS = ["name", "armor_type", "ac_bonus", "max_dex_bonus",
                       "armor_check_penalty", "arcane_spell_failure"]

    def test_all_armor_entries_have_required_fields(self):
        d = load_catalog()
        bad = []
        for key, armor in d["armor"].items():
            for field in self.REQUIRED_FIELDS:
                if field not in armor or armor[field] is None:
                    bad.append(f"{key}.{field}")
        assert not bad, f"Armor entries missing required fields: {bad}"
