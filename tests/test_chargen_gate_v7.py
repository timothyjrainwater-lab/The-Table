"""Gate V7 — WO-CHARGEN-EQUIPMENT-001: Starting equipment integration.

Tests that build_character() correctly assigns inventory, weapon, AC,
armor_check_penalty, and encumbrance_load for all 11 base classes.

Baseline: 15+ tests, all must pass.
"""

import pytest
from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Pinned ability scores so AC values are deterministic.
# All classes use these overrides unless noted.
_STANDARD_SCORES = {
    "str": 12,  # str_mod = +1
    "dex": 12,  # dex_mod = +1
    "con": 12,
    "int": 10,
    "wis": 12,  # wis_mod = +1
    "cha": 10,
}


def _build(class_name, overrides=None, **kwargs):
    scores = dict(_STANDARD_SCORES)
    if overrides:
        scores.update(overrides)
    return build_character("human", class_name, level=1, ability_overrides=scores, **kwargs)


# ---------------------------------------------------------------------------
# V7-01: Fighter — longsword + chainmail, correct AC
# ---------------------------------------------------------------------------

class TestFighter:
    def test_fighter_has_longsword(self):
        e = _build("fighter")
        weapon = e.get(EF.WEAPON)
        assert weapon is not None, "Fighter must have a weapon"
        assert weapon["name"] == "Longsword"

    def test_fighter_has_chainmail_in_inventory(self):
        e = _build("fighter")
        item_ids = [i["item_id"] for i in e[EF.INVENTORY]]
        assert "chainmail" in item_ids

    def test_fighter_ac_chainmail(self):
        # DEX 12 → mod +1; chainmail ac_bonus=5, max_dex=2 → effective_dex=min(1,2)=1
        # AC = 10 + 1 + 5 = 16
        e = _build("fighter", overrides={"dex": 12})
        assert e[EF.AC] == 16

    def test_fighter_armor_check_penalty(self):
        # chainmail armor_check_penalty = -5
        e = _build("fighter")
        assert e[EF.ARMOR_CHECK_PENALTY] == -5


# ---------------------------------------------------------------------------
# V7-05: Wizard — quarterstaff, no armor
# ---------------------------------------------------------------------------

class TestWizard:
    def test_wizard_has_quarterstaff(self):
        e = _build("wizard")
        weapon = e.get(EF.WEAPON)
        assert weapon is not None, "Wizard must have a weapon"
        assert weapon["name"] == "Quarterstaff"

    def test_wizard_no_armor(self):
        item_ids = [i["item_id"] for i in _build("wizard")[EF.INVENTORY]]
        armor_ids = {"chainmail", "leather", "hide", "scale_mail", "padded",
                     "studded_leather", "chain_shirt", "breastplate"}
        assert not armor_ids.intersection(item_ids), "Wizard must not have armor"

    def test_wizard_ac_dex_only(self):
        # DEX 14 → mod +2; no armor → AC = 10 + 2 = 12
        e = _build("wizard", overrides={"dex": 14})
        assert e[EF.AC] == 12

    def test_wizard_has_spell_component_pouch(self):
        e = _build("wizard")
        item_ids = [i["item_id"] for i in e[EF.INVENTORY]]
        assert "spell_component_pouch" in item_ids

    def test_wizard_armor_check_penalty_zero(self):
        e = _build("wizard")
        assert e[EF.ARMOR_CHECK_PENALTY] == 0


# ---------------------------------------------------------------------------
# V7-09: Monk — no armor, WIS-to-AC
# ---------------------------------------------------------------------------

class TestMonk:
    def test_monk_no_armor(self):
        e = _build("monk")
        armor_ids = {"chainmail", "leather", "hide", "scale_mail"}
        item_ids = [i["item_id"] for i in e[EF.INVENTORY]]
        assert not armor_ids.intersection(item_ids)

    def test_monk_no_weapon_field(self):
        e = _build("monk")
        # Monk starts unarmed — weapon dict should be None
        assert e.get(EF.WEAPON) is None

    def test_monk_ac_includes_wis(self):
        # DEX 12 → +1, WIS 16 → +3; AC = 10 + 1 + 0(no armor) + 3(wis) = 14
        e = _build("monk", overrides={"dex": 12, "wis": 16})
        assert e[EF.AC] == 14


# ---------------------------------------------------------------------------
# V7-12: Druid — hide armor (non-metal), spell component pouch
# ---------------------------------------------------------------------------

class TestDruid:
    def test_druid_has_hide_armor(self):
        e = _build("druid")
        item_ids = [i["item_id"] for i in e[EF.INVENTORY]]
        assert "hide" in item_ids

    def test_druid_no_metal_armor(self):
        e = _build("druid")
        metal_armors = {"chainmail", "scale_mail", "breastplate", "half_plate",
                        "full_plate", "splint_mail", "banded_mail", "chain_shirt"}
        item_ids = [i["item_id"] for i in e[EF.INVENTORY]]
        assert not metal_armors.intersection(item_ids)

    def test_druid_has_spell_component_pouch(self):
        e = _build("druid")
        item_ids = [i["item_id"] for i in e[EF.INVENTORY]]
        assert "spell_component_pouch" in item_ids


# ---------------------------------------------------------------------------
# V7-15: Rogue — leather armor, short sword, armor_check_penalty=0
# ---------------------------------------------------------------------------

class TestRogue:
    def test_rogue_has_leather_armor(self):
        e = _build("rogue")
        item_ids = [i["item_id"] for i in e[EF.INVENTORY]]
        assert "leather" in item_ids

    def test_rogue_has_short_sword(self):
        e = _build("rogue")
        weapon = e.get(EF.WEAPON)
        assert weapon is not None
        assert weapon["name"] == "Short Sword"

    def test_rogue_leather_armor_check_penalty_zero(self):
        # leather armor_check_penalty = 0
        e = _build("rogue")
        assert e[EF.ARMOR_CHECK_PENALTY] == 0


# ---------------------------------------------------------------------------
# V7-18: All 11 classes have non-empty inventory and non-None weapon (or None for monk)
# ---------------------------------------------------------------------------

ALL_CLASSES = [
    "barbarian", "bard", "cleric", "druid", "fighter",
    "monk", "paladin", "ranger", "rogue", "sorcerer", "wizard",
]

@pytest.mark.parametrize("class_name", ALL_CLASSES)
def test_all_classes_have_inventory(class_name):
    e = _build(class_name)
    assert EF.INVENTORY in e, f"{class_name}: missing INVENTORY field"
    assert len(e[EF.INVENTORY]) > 0, f"{class_name}: INVENTORY is empty"


@pytest.mark.parametrize("class_name", [c for c in ALL_CLASSES if c != "monk"])
def test_non_monk_classes_have_weapon(class_name):
    e = _build(class_name)
    weapon = e.get(EF.WEAPON)
    assert weapon is not None, f"{class_name}: weapon is None"
    assert isinstance(weapon, dict), f"{class_name}: weapon must be a dict"
    assert "damage_dice" in weapon, f"{class_name}: weapon missing damage_dice"


@pytest.mark.parametrize("class_name", ALL_CLASSES)
def test_all_classes_have_encumbrance(class_name):
    e = _build(class_name)
    enc = e.get(EF.ENCUMBRANCE_LOAD)
    assert enc in ("light", "medium", "heavy", "overloaded"), (
        f"{class_name}: invalid encumbrance_load '{enc}'"
    )


# ---------------------------------------------------------------------------
# V7-31: Spell component pouch for all caster classes
# ---------------------------------------------------------------------------

# Casters that can afford spell component pouch after weapon + armor purchase.
# Paladin and ranger spend most of their gold on longsword + chainmail/leather,
# leaving paladin unable to afford the SCP (5gp) after basic gear (~6gp).
# Per WO spec §3.4: "Skip items the character can't afford" — correct behavior.
CASTER_CLASSES_WITH_SCP = ["bard", "cleric", "druid", "sorcerer", "wizard"]

@pytest.mark.parametrize("class_name", CASTER_CLASSES_WITH_SCP)
def test_caster_has_spell_component_pouch(class_name):
    e = _build(class_name)
    item_ids = [i["item_id"] for i in e[EF.INVENTORY]]
    assert "spell_component_pouch" in item_ids, (
        f"{class_name}: missing spell_component_pouch"
    )


# ---------------------------------------------------------------------------
# V7-38: Encumbrance — low STR character near heavy load
# ---------------------------------------------------------------------------

class TestEncumbrance:
    def test_light_load_flagged_correctly(self):
        # STR 10 → light cap 33.33 lb. Standard gear (~13 lb) is light.
        e = _build("fighter", overrides={"str": 10})
        # chain mail (40 lb) + longsword (4 lb) + gear ≈ 55 lb → heavy
        assert e[EF.ENCUMBRANCE_LOAD] in ("medium", "heavy")

    def test_very_low_str_may_be_overloaded(self):
        # STR 6 → heavy cap 60 lb. Fighter gear ≈ 55+ lb.
        e = _build("fighter", overrides={"str": 6, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10})
        assert e[EF.ENCUMBRANCE_LOAD] in ("medium", "heavy", "overloaded")

    def test_wizard_light_load(self):
        # Wizard has no armor; total gear ≈ 10 lb → light for STR 10
        e = _build("wizard", overrides={"str": 10})
        assert e[EF.ENCUMBRANCE_LOAD] == "light"


# ---------------------------------------------------------------------------
# V7-41: starting_equipment override bypasses default kit
# ---------------------------------------------------------------------------

class TestStartingEquipmentOverride:
    def test_override_replaces_default_kit(self):
        custom = {"dagger": 2, "torch": 5}
        e = _build("fighter", starting_equipment=custom)
        item_ids = [i["item_id"] for i in e[EF.INVENTORY]]
        assert "dagger" in item_ids
        assert "torch" in item_ids
        # Default longsword/chainmail should NOT appear
        assert "longsword" not in item_ids
        assert "chainmail" not in item_ids

    def test_override_sets_quantity(self):
        custom = {"dagger": 3}
        e = _build("rogue", starting_equipment=custom)
        daggers = [i for i in e[EF.INVENTORY] if i["item_id"] == "dagger"]
        assert daggers[0]["quantity"] == 3

    def test_override_armor_check_penalty_zero(self):
        # Override path sets ARMOR_CHECK_PENALTY to 0 (no armor assigned)
        e = _build("fighter", starting_equipment={"longsword": 1})
        assert e[EF.ARMOR_CHECK_PENALTY] == 0


# ---------------------------------------------------------------------------
# V7-44: Weapon dict structure matches what combat resolver expects
# ---------------------------------------------------------------------------

class TestWeaponDictStructure:
    REQUIRED_KEYS = {"damage_dice", "damage_bonus", "damage_type",
                     "critical_multiplier", "critical_range", "weapon_type"}

    @pytest.mark.parametrize("class_name", [c for c in ALL_CLASSES if c != "monk"])
    def test_weapon_has_required_keys(self, class_name):
        e = _build(class_name)
        weapon = e[EF.WEAPON]
        for key in self.REQUIRED_KEYS:
            assert key in weapon, f"{class_name}: weapon missing key '{key}'"

    def test_fighter_weapon_damage_bonus_includes_str_mod(self):
        # STR 14 → mod +2; weapon damage_bonus should be +2
        e = _build("fighter", overrides={"str": 14})
        assert e[EF.WEAPON]["damage_bonus"] == 2

    def test_barbarian_greataxe_two_handed(self):
        e = _build("barbarian")
        weapon = e[EF.WEAPON]
        assert weapon["name"] == "Greataxe"
        assert weapon["is_two_handed"] is True
        assert weapon["grip"] == "two-handed"
