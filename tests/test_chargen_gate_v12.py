"""Gate V12 - WO-CHARGEN-DUALCASTER-001 dual-caster spellcasting tests.

20 tests covering _merge_spellcasting() in aidm/chargen/builder.py.

Primary vs secondary determined by alphabetical sort:
  bard < cleric < druid < paladin < ranger < sorcerer < wizard

Primary uses EF.SPELL_SLOTS / CASTER_LEVEL / CASTER_CLASS
           / SPELLS_PREPARED or SPELLS_KNOWN.
Secondary uses EF.SPELL_SLOTS_2 / CASTER_LEVEL_2 / CASTER_CLASS_2
             / SPELLS_PREPARED_2 or SPELLS_KNOWN_2.
"""

import pytest
from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF

ALL_10 = {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}
INT14  = {"str": 10, "dex": 10, "con": 10, "int": 14, "wis": 10, "cha": 10}
WIS12_INT12 = {"str": 10, "dex": 10, "con": 10, "int": 12, "wis": 12, "cha": 10}


# V12-01  cleric/wizard: cleric primary (c < w), wizard secondary

def test_v12_01_cleric_wizard_primary_secondary():
    e = build_character(
        "human", "cleric",
        class_mix={"cleric": 3, "wizard": 3},
        ability_overrides=ALL_10,
    )
    assert e[EF.CASTER_CLASS] == "cleric", f"primary wrong: {e[EF.CASTER_CLASS]!r}"
    assert e[EF.CASTER_CLASS_2] == "wizard", f"secondary wrong: {e[EF.CASTER_CLASS_2]!r}"

# V12-02  cleric 5 / wizard 5: each class uses its own slot table

def test_v12_02_cleric_wizard_5_5_slot_tables():
    e = build_character(
        "human", "cleric",
        class_mix={"cleric": 5, "wizard": 5},
        ability_overrides=ALL_10,
    )
    # cleric-5, WIS 10: base (5,3,2,1) but WIS 10 gates out lvl1+ -> {0: 5}
    assert e[EF.SPELL_SLOTS] == {0: 5}, f"cleric-5 slots: {e[EF.SPELL_SLOTS]}"
    # wizard-5, INT 10: base (4,3,2,1) but INT 10 gates out lvl1+ -> {0: 4}
    assert e[EF.SPELL_SLOTS_2] == {0: 4}, f"wizard-5 slots: {e[EF.SPELL_SLOTS_2]}"

# V12-03  cleric 3 / wizard 3 slot counts match PHB tables (WIS/INT 10)

def test_v12_03_slot_counts_match_phb_tables():
    e = build_character(
        "human", "cleric",
        class_mix={"cleric": 3, "wizard": 3},
        ability_overrides=ALL_10,
    )
    # PHB cleric-3 base = (4,2,1); WIS 10 gates lvl1+ -> {0: 4}
    assert e[EF.SPELL_SLOTS] == {0: 4}, f"cleric-3 primary: {e[EF.SPELL_SLOTS]}"
    # PHB wizard-3 base = (4,2,1); INT 10 gates lvl1+ -> {0: 4}
    assert e[EF.SPELL_SLOTS_2] == {0: 4}, f"wizard-3 secondary: {e[EF.SPELL_SLOTS_2]}"


# V12-04  druid/sorcerer: sorcerer (spontaneous) -> SPELLS_KNOWN_2; druid -> SPELLS_PREPARED

def test_v12_04_druid_sorcerer_prepared_vs_known():
    e = build_character(
        "human", "druid",
        class_mix={"druid": 3, "sorcerer": 3},
        ability_overrides=ALL_10,
    )
    assert e[EF.CASTER_CLASS] == "druid"
    assert e[EF.CASTER_CLASS_2] == "sorcerer"
    assert EF.SPELLS_PREPARED in e
    assert e[EF.SPELLS_KNOWN] == {}
    assert EF.SPELLS_KNOWN_2 in e
    assert isinstance(e[EF.SPELLS_KNOWN_2], dict)
    assert e.get(EF.SPELLS_PREPARED_2) == {}


# V12-05  bard/wizard: bard primary (b < w), wizard secondary

def test_v12_05_bard_wizard_primary_secondary():
    e = build_character(
        "human", "bard",
        class_mix={"bard": 3, "wizard": 3},
        ability_overrides=ALL_10,
    )
    assert e[EF.CASTER_CLASS] == "bard"
    assert e[EF.CASTER_CLASS_2] == "wizard"


# V12-06  CASTER_LEVEL and CASTER_LEVEL_2 reflect each class own level

def test_v12_06_caster_levels_reflect_class_level():
    e = build_character(
        "human", "cleric",
        class_mix={"cleric": 4, "wizard": 2},
        ability_overrides=ALL_10,
    )
    assert e[EF.CASTER_LEVEL] == 4
    assert e[EF.CASTER_LEVEL_2] == 2


# V12-07  Bonus spell slots: wizard level 3 INT 14 vs INT 10

def test_v12_07_bonus_slots_from_int_14():
    e10 = build_character("human", "wizard", level=3, ability_overrides=ALL_10)
    e14 = build_character("human", "wizard", level=3, ability_overrides=INT14)
    slots10 = e10[EF.SPELL_SLOTS]
    slots14 = e14[EF.SPELL_SLOTS]
    assert slots10 == {0: 4}, f"INT 10 wizard-3: {slots10}"
    assert 1 in slots14, f"INT 14 wizard-3 needs lvl-1 slots; got {slots14}"
    assert slots14.get(1, 0) > slots10.get(1, 0)


# V12-08  spell_choices_2 populates SPELLS_PREPARED_2 for wizard secondary

def test_v12_08_spell_choices_2_populates_prepared_2():
    e = build_character(
        "human", "cleric",
        class_mix={"cleric": 3, "wizard": 3},
        ability_overrides=INT14,
        spell_choices_2=["magic_missile", "sleep"],
    )
    prep2 = e[EF.SPELLS_PREPARED_2]
    assert isinstance(prep2, dict)
    all_spells = [sp for lvl_spells in prep2.values() for sp in lvl_spells]
    assert "magic_missile" in all_spells or "sleep" in all_spells, f"not found: {prep2}"


# V12-09  Without spell_choices_2, secondary wizard SPELLS_PREPARED_2 defaults to {}

def test_v12_09_no_spell_choices_2_gives_empty_prepared_2():
    e = build_character(
        "human", "cleric",
        class_mix={"cleric": 3, "wizard": 3},
        ability_overrides=INT14,
    )
    assert e[EF.SPELLS_PREPARED_2] == {}


# V12-10  fighter/wizard (single caster): no _2 fields in entity

def test_v12_10_fighter_wizard_no_secondary_fields():
    e = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "wizard": 3},
        ability_overrides=ALL_10,
    )
    assert EF.SPELL_SLOTS_2 not in e
    assert EF.CASTER_CLASS_2 not in e
    assert EF.CASTER_LEVEL_2 not in e



# V12-11  Non-caster multiclass (fighter/rogue): SPELL_SLOTS is {} and no caster fields

def test_v12_11_non_caster_multiclass_no_spell_fields():
    e = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "rogue": 3},
        ability_overrides=ALL_10,
    )
    assert e.get(EF.SPELL_SLOTS) == {}
    assert EF.CASTER_CLASS not in e


# V12-12  Three caster classes raises ValueError

def test_v12_12_three_casters_raises_value_error():
    import pytest
    with pytest.raises(ValueError, match="two caster classes"):
        build_character(
            "human", "wizard",
            class_mix={"cleric": 3, "wizard": 3, "druid": 3},
            ability_overrides=ALL_10,
        )


# V12-13  paladin/ranger dual-caster path: CASTER_CLASS and CASTER_CLASS_2 both present

def test_v12_13_paladin_ranger_dual_caster():
    e = build_character(
        "human", "paladin",
        class_mix={"paladin": 6, "ranger": 6},
        ability_overrides=ALL_10,
    )
    assert EF.CASTER_CLASS in e
    assert EF.CASTER_CLASS_2 in e
    assert e[EF.CASTER_CLASS] == "paladin"
    assert e[EF.CASTER_CLASS_2] == "ranger"


# V12-14  No KeyError on standard EF reads for dual-caster entity

def test_v12_14_no_key_error_on_standard_ef_reads():
    e = build_character(
        "human", "cleric",
        class_mix={"cleric": 3, "wizard": 3},
        ability_overrides=ALL_10,
    )
    _ = e[EF.SPELL_SLOTS]
    _ = e[EF.CASTER_LEVEL]
    _ = e[EF.CASTER_CLASS]
    _ = e[EF.SPELL_SLOTS_2]
    _ = e[EF.CASTER_LEVEL_2]
    _ = e[EF.CASTER_CLASS_2]
    _ = e[EF.SPELLS_PREPARED]
    _ = e[EF.SPELLS_KNOWN]
    _ = e[EF.SPELLS_PREPARED_2]
    _ = e[EF.SPELLS_KNOWN_2]


# V12-15  V6 regression: single-class wizard has SPELL_SLOTS; no SPELL_SLOTS_2

def test_v12_15_v6_regression_single_class_wizard():
    e = build_character("human", "wizard", level=3, ability_overrides=ALL_10)
    assert EF.SPELL_SLOTS in e
    assert e[EF.SPELL_SLOTS] != {}
    assert EF.SPELL_SLOTS_2 not in e


# V12-16  V8 regression: fighter/wizard single-caster CASTER_CLASS="wizard", no SPELL_SLOTS_2

def test_v12_16_v8_regression_fighter_wizard_caster_class():
    e = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "wizard": 3},
        ability_overrides=ALL_10,
    )
    assert e.get(EF.CASTER_CLASS) == "wizard"
    assert EF.SPELL_SLOTS_2 not in e



# V12-17  Dual-caster with INT 14: wizard secondary gets bonus spell slots

def test_v12_17_dual_caster_int14_wizard_secondary_bonus():
    e10 = build_character(
        "human", "cleric",
        class_mix={"cleric": 3, "wizard": 3},
        ability_overrides=ALL_10,
    )
    e14 = build_character(
        "human", "cleric",
        class_mix={"cleric": 3, "wizard": 3},
        ability_overrides=INT14,
    )
    slots10 = e10[EF.SPELL_SLOTS_2]
    slots14 = e14[EF.SPELL_SLOTS_2]
    assert 1 in slots14, f"INT 14 wizard secondary needs lvl-1 slots; got {slots14}"
    assert slots14.get(1, 0) > slots10.get(1, 0)
    # Cleric primary uses WIS, not INT -- should be unchanged
    assert e10[EF.SPELL_SLOTS] == e14[EF.SPELL_SLOTS]


# V12-18  cleric/wizard prepared lists distinct between primary and secondary

def test_v12_18_prepared_lists_distinct():
    e = build_character(
        "human", "cleric",
        class_mix={"cleric": 3, "wizard": 3},
        ability_overrides=ALL_10,
    )
    cleric_prep = e[EF.SPELLS_PREPARED]
    wizard_prep = e[EF.SPELLS_PREPARED_2]
    assert isinstance(cleric_prep, dict)
    assert isinstance(wizard_prep, dict)
    assert cleric_prep is not wizard_prep, "SPELLS_PREPARED and SPELLS_PREPARED_2 must be distinct objects"
    assert e[EF.SPELLS_KNOWN] == {}, f"cleric primary SPELLS_KNOWN should be empty; got {e[EF.SPELLS_KNOWN]}"


# V12-19  CASTER_CLASS field present on single-caster (wizard in fighter/wizard)

def test_v12_19_caster_class_present_on_single_caster():
    e = build_character(
        "human", "fighter",
        class_mix={"fighter": 3, "wizard": 3},
        ability_overrides=ALL_10,
    )
    assert EF.CASTER_CLASS in e
    assert e[EF.CASTER_CLASS] == "wizard"


# V12-20  Debrief anchor: cleric 3 / wizard 3 with WIS 12 / INT 12, both have level-2 slots

def test_v12_20_debrief_anchor_both_have_level2_slots():
    """Debrief anchor -- cleric-3 WIS12 and wizard-3 INT12 both access level-2 spell slots."""
    e = build_character(
        "human", "cleric",
        class_mix={"cleric": 3, "wizard": 3},
        ability_overrides=WIS12_INT12,
    )
    cleric_slots = e[EF.SPELL_SLOTS]
    wizard_slots = e[EF.SPELL_SLOTS_2]

    print("[V12-20] cleric-3 WIS12 slots:", cleric_slots)
    print(f"[V12-20] wizard-3 INT12 slots:  {wizard_slots}")

    # WIS/INT 12 unlocks level-2 slots (ability >= 10 + spell_level = 12)
    assert 2 in cleric_slots, f"cleric-3 WIS12 needs lvl-2 slots; got {cleric_slots}"
    assert 2 in wizard_slots, f"wizard-3 INT12 needs lvl-2 slots; got {wizard_slots}"
    assert 0 in cleric_slots
    assert 0 in wizard_slots
