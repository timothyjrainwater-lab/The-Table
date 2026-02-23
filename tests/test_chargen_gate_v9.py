"""Gate V9 — Dual-Caster Spell Slot Merging.

WO-CHARGEN-DUALCASTER-001

Tests that build_character() correctly handles multiclass characters with
two caster classes, storing each caster's slots and spells independently
using primary (flat) and secondary (_2 suffix) fields.

PHB references:
- Wizard spell table: PHB p.56
- Cleric spell table: PHB p.31
- Druid spell table: PHB p.35
- Sorcerer spell table: PHB p.54
- Bard spell table: PHB p.27
- Paladin spell table: PHB p.44
"""

import pytest
from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wizard_cleric_3_3(**kwargs):
    """Wizard 3 / Cleric 3 character with sufficient ability scores to access L1+ spells."""
    return build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 14, "wis": 14, "cha": 10},
        class_mix={"wizard": 3, "cleric": 3},
        **kwargs,
    )


# ---------------------------------------------------------------------------
# V9-01: cleric is primary alphabetically (c < w), wizard is secondary
# ---------------------------------------------------------------------------

def test_v9_01_wizard_cleric_primary_is_cleric():
    """cleric < wizard alphabetically → SPELL_SLOTS = cleric slots, SPELL_SLOTS_2 = wizard slots."""
    entity = _wizard_cleric_3_3()

    # Cleric L3 (WIS=14, mod=2): base (4,2,1) + bonus {1:1, 2:1} = {0:4, 1:3, 2:2}
    assert entity[EF.SPELL_SLOTS] == {0: 4, 1: 3, 2: 2}
    # Wizard L3 (INT=14, mod=2): base (4,2,1) + bonus {1:1, 2:1} = {0:4, 1:3, 2:2}
    assert entity[EF.SPELL_SLOTS_2] == {0: 4, 1: 3, 2: 2}


# ---------------------------------------------------------------------------
# V9-02: Level 5/5 slot counts match PHB tables
# ---------------------------------------------------------------------------

def test_v9_02_wizard_cleric_5_5_slot_counts():
    """Wizard 5 / Cleric 5 — slot counts match PHB tables for each class at level 5."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 14, "wis": 14, "cha": 10},
        class_mix={"wizard": 5, "cleric": 5},
    )
    # cleric primary (alphabetical), wizard secondary
    # Cleric L5 (WIS=14, mod=2): base (5,3,2,1) + bonus {1:1, 2:1} = {0:5, 1:4, 2:3, 3:1}
    assert entity[EF.SPELL_SLOTS] == {0: 5, 1: 4, 2: 3, 3: 1}
    # Wizard L5 (INT=14, mod=2): base (4,3,2,1) + bonus {1:1, 2:1} = {0:4, 1:4, 2:3, 3:1}
    assert entity[EF.SPELL_SLOTS_2] == {0: 4, 1: 4, 2: 3, 3: 1}


# ---------------------------------------------------------------------------
# V9-03: Alphabetical primary assignment
# ---------------------------------------------------------------------------

def test_v9_03_alphabetical_primary_cleric_lt_wizard():
    """'cleric' < 'wizard' alphabetically → cleric is primary (CASTER_CLASS)."""
    entity = _wizard_cleric_3_3()
    assert entity[EF.CASTER_CLASS] == "cleric"
    assert entity[EF.CASTER_CLASS_2] == "wizard"


# ---------------------------------------------------------------------------
# V9-04: druid/sorcerer — sorcerer SPELLS_KNOWN in _2 fields (spontaneous)
# ---------------------------------------------------------------------------

def test_v9_04_druid_sorcerer_spontaneous_secondary():
    """druid/sorcerer: sorcerer is secondary ('s' > 'd'); SPELLS_KNOWN_2 present."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        class_mix={"druid": 3, "sorcerer": 3},
    )
    # druid < sorcerer: druid is primary (prepared), sorcerer is secondary (spontaneous)
    assert entity[EF.CASTER_CLASS] == "druid"
    assert entity[EF.CASTER_CLASS_2] == "sorcerer"
    # Primary (druid) is prepared → SPELLS_PREPARED, no SPELLS_KNOWN
    assert EF.SPELLS_PREPARED in entity
    # Secondary (sorcerer) is spontaneous → SPELLS_KNOWN_2
    assert EF.SPELLS_KNOWN_2 in entity


# ---------------------------------------------------------------------------
# V9-05: CASTER_CLASS and CASTER_CLASS_2 fields present and correct
# ---------------------------------------------------------------------------

def test_v9_05_caster_class_fields_present():
    """CASTER_CLASS and CASTER_CLASS_2 fields present in dual-caster entity."""
    entity = _wizard_cleric_3_3()
    assert EF.CASTER_CLASS in entity
    assert EF.CASTER_CLASS_2 in entity
    assert entity[EF.CASTER_CLASS] == "cleric"
    assert entity[EF.CASTER_CLASS_2] == "wizard"


# ---------------------------------------------------------------------------
# V9-06: CASTER_LEVEL and CASTER_LEVEL_2 reflect each class's own level
# ---------------------------------------------------------------------------

def test_v9_06_caster_level_per_class():
    """CASTER_LEVEL and CASTER_LEVEL_2 reflect each caster's own class level."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        class_mix={"wizard": 4, "cleric": 2},
    )
    # cleric is primary, wizard is secondary
    assert entity[EF.CASTER_LEVEL] == 2    # cleric level
    assert entity[EF.CASTER_LEVEL_2] == 4  # wizard level


# ---------------------------------------------------------------------------
# V9-07: Bonus spell slots from ability score applied to each caster independently
# ---------------------------------------------------------------------------

def test_v9_07_bonus_spells_per_caster():
    """High WIS boosts cleric slots; high INT boosts wizard slots independently."""
    entity = build_character(
        "human", "fighter",
        # WIS=18 (+4 mod) → cleric gets bonus spells; INT=14 (+2 mod) → wizard gets fewer bonus
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 14, "wis": 18, "cha": 10},
        class_mix={"wizard": 3, "cleric": 3},
    )
    # cleric primary with WIS 18: bonus spells at levels 1, 2, 3
    # Cleric L3 base {0:4, 1:2, 2:1} + WIS 18 bonus_spells(18):
    #   mod=4, L1: (4-1)//4+1=1, L2: (4-2)//4+1=1, L3: (4-3)//4+1=1
    #   → {0:4, 1:3, 2:2, 3:1}
    cleric_slots = entity[EF.SPELL_SLOTS]
    assert cleric_slots.get(1, 0) == 3  # 2 base + 1 bonus
    assert cleric_slots.get(2, 0) == 2  # 1 base + 1 bonus

    # Wizard secondary with INT 14: bonus_spells(14): mod=2, L1: (2-1)//4+1=1
    #   Wizard L3 base {0:4, 1:2, 2:1} + bonus L1: → {0:4, 1:3, 2:1}
    wizard_slots = entity[EF.SPELL_SLOTS_2]
    assert wizard_slots.get(1, 0) == 3  # 2 base + 1 bonus


# ---------------------------------------------------------------------------
# V9-08: spell_choices_2 populates second caster's prepared spells
# ---------------------------------------------------------------------------

def test_v9_08_spell_choices_2_populates_secondary():
    """spell_choices_2 populates wizard (secondary) SPELLS_PREPARED_2."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 14, "wis": 14, "cha": 10},
        class_mix={"wizard": 3, "cleric": 3},
        spell_choices=["cure_light_wounds"],        # cleric primary
        spell_choices_2=["magic_missile", "fireball"],  # wizard secondary
    )
    # cleric is prepared → SPELLS_PREPARED has cure_light_wounds
    assert "cure_light_wounds" in entity[EF.SPELLS_PREPARED].get(1, [])
    # wizard secondary SPELLS_PREPARED_2 has magic_missile (L1) and fireball (L3)
    assert "magic_missile" in entity[EF.SPELLS_PREPARED_2].get(1, [])
    assert "fireball" in entity[EF.SPELLS_PREPARED_2].get(3, [])


# ---------------------------------------------------------------------------
# V9-09: Without spell_choices_2, second caster defaults from class spell list
# ---------------------------------------------------------------------------

def test_v9_09_no_spell_choices_2_defaults_empty():
    """Without spell_choices_2, secondary prepared caster gets empty SPELLS_PREPARED_2."""
    entity = _wizard_cleric_3_3()
    # wizard (secondary prepared) → SPELLS_PREPARED_2 is empty dict
    assert entity[EF.SPELLS_PREPARED_2] == {}


# ---------------------------------------------------------------------------
# V9-10: Single-caster multiclass (fighter/wizard): no _2 fields present
# ---------------------------------------------------------------------------

def test_v9_10_single_caster_multiclass_no_secondary_fields():
    """fighter/wizard multiclass — only one caster; no _2 fields in entity dict."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        class_mix={"fighter": 3, "wizard": 3},
    )
    assert EF.SPELL_SLOTS_2 not in entity
    assert EF.CASTER_LEVEL_2 not in entity
    assert EF.CASTER_CLASS_2 not in entity
    assert EF.SPELLS_KNOWN_2 not in entity
    assert EF.SPELLS_PREPARED_2 not in entity


# ---------------------------------------------------------------------------
# V9-11: Non-caster multiclass (fighter/rogue): no SPELL_SLOTS or _2 fields
# ---------------------------------------------------------------------------

def test_v9_11_non_caster_multiclass_no_spell_fields():
    """fighter/rogue — no casters; SPELL_SLOTS is empty, no _2 fields."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        class_mix={"fighter": 3, "rogue": 3},
    )
    assert entity[EF.SPELL_SLOTS] == {}
    assert entity[EF.CASTER_LEVEL] == 0
    assert EF.SPELL_SLOTS_2 not in entity


# ---------------------------------------------------------------------------
# V9-12: Three caster classes raises ValueError
# ---------------------------------------------------------------------------

def test_v9_12_three_caster_classes_raises():
    """Three caster classes in class_mix raises ValueError."""
    with pytest.raises(ValueError, match="Only two caster classes supported"):
        build_character(
            "human", "fighter",
            class_mix={"wizard": 2, "cleric": 2, "druid": 2},
        )


# ---------------------------------------------------------------------------
# V9-13: wizard/cleric/fighter mix (2 casters + martial) — valid, dual-caster
# ---------------------------------------------------------------------------

def test_v9_13_two_casters_plus_martial_valid():
    """wizard/cleric/fighter — 2 casters + 1 martial is valid; dual-caster path fires."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        class_mix={"wizard": 2, "cleric": 2, "fighter": 2},
    )
    assert EF.SPELL_SLOTS in entity
    assert EF.SPELL_SLOTS_2 in entity
    assert entity[EF.CASTER_CLASS] == "cleric"
    assert entity[EF.CASTER_CLASS_2] == "wizard"


# ---------------------------------------------------------------------------
# V9-14: bard/paladin mix — both partial casters, both get their slot tables
# ---------------------------------------------------------------------------

def test_v9_14_bard_paladin_both_partial_casters():
    """bard/paladin — both partial casters; each gets their slot tables."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        class_mix={"bard": 5, "paladin": 5},
    )
    # bard < paladin alphabetically: bard is primary
    assert entity[EF.CASTER_CLASS] == "bard"
    assert entity[EF.CASTER_CLASS_2] == "paladin"
    # Bard L5 slots should be present
    assert entity[EF.SPELL_SLOTS]  # non-empty
    # Paladin L5 slots should be present
    assert entity[EF.SPELL_SLOTS_2]  # non-empty


# ---------------------------------------------------------------------------
# V9-15: Druid 2 / Rogue 3 — druid slots only (single caster), no _2 fields
# ---------------------------------------------------------------------------

def test_v9_15_druid_rogue_single_caster():
    """Druid 2 / Rogue 3 — one caster only; no _2 fields."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        class_mix={"druid": 2, "rogue": 3},
    )
    assert EF.SPELL_SLOTS in entity
    assert entity[EF.CASTER_CLASS] == "druid"
    assert EF.SPELL_SLOTS_2 not in entity
    assert EF.CASTER_CLASS_2 not in entity


# ---------------------------------------------------------------------------
# V9-16: V6 regression — single-class wizard has SPELL_SLOTS, no _2 fields
# ---------------------------------------------------------------------------

def test_v9_16_single_class_wizard_regression():
    """Single-class wizard still has SPELL_SLOTS, no _2 fields (V6 regression)."""
    entity = build_character(
        "elf", "wizard", level=5,
        ability_overrides={"str": 10, "dex": 12, "con": 8, "int": 16, "wis": 10, "cha": 10},
    )
    assert EF.SPELL_SLOTS in entity
    assert entity[EF.SPELL_SLOTS]  # non-empty
    assert EF.SPELL_SLOTS_2 not in entity
    assert EF.CASTER_CLASS_2 not in entity


# ---------------------------------------------------------------------------
# V9-17: V8 regression — fighter/wizard still works; wizard as single caster
# ---------------------------------------------------------------------------

def test_v9_17_fighter_wizard_regression():
    """fighter/wizard multiclass still works (V8 regression)."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 14, "dex": 10, "con": 12, "int": 14, "wis": 10, "cha": 10},
        class_mix={"fighter": 4, "wizard": 3},
    )
    assert EF.SPELL_SLOTS in entity
    assert entity[EF.CASTER_CLASS] == "wizard"
    assert EF.SPELL_SLOTS_2 not in entity


# ---------------------------------------------------------------------------
# V9-18: Dual-caster with ability_overrides — bonus spells per caster's key ability
# ---------------------------------------------------------------------------

def test_v9_18_dual_caster_ability_overrides_bonus_spells():
    """Each caster gets bonus spells from their own casting ability independently."""
    entity = build_character(
        "human", "fighter",
        # WIS=18 (+4 mod) → cleric primary gets bonus slots at L1, L2;
        # INT=10 → wizard secondary gets no bonus slots (and can't cast L1+)
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 18, "cha": 10},
        class_mix={"wizard": 3, "cleric": 3},
    )
    # Cleric (primary) WIS=18, mod=4: bonus_spells: L1=(4-1)//4+1=1, L2=(4-2)//4+1=1
    # Cleric L3 base (4,2,1): {0:4, 1:3, 2:2}
    cleric_slots = entity[EF.SPELL_SLOTS]
    assert cleric_slots.get(1, 0) == 3   # 2 base + 1 bonus from WIS 18
    assert cleric_slots.get(2, 0) == 2   # 1 base + 1 bonus from WIS 18

    # Wizard (secondary) INT=10: can_cast_spell_level(10,1)=False → only L0 accessible
    wizard_slots = entity[EF.SPELL_SLOTS_2]
    assert wizard_slots == {0: 4}  # only L0 with INT 10


# ---------------------------------------------------------------------------
# V9-19: Bard (spontaneous) + wizard (prepared) — bard primary (b < w)
# ---------------------------------------------------------------------------

def test_v9_19_bard_wizard_spontaneous_primary():
    """bard < wizard: bard is primary (spontaneous → SPELLS_KNOWN); wizard secondary (SPELLS_PREPARED_2)."""
    entity = build_character(
        "human", "fighter",
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        class_mix={"bard": 3, "wizard": 3},
    )
    assert entity[EF.CASTER_CLASS] == "bard"
    assert entity[EF.CASTER_CLASS_2] == "wizard"
    # bard is spontaneous → primary SPELLS_KNOWN present
    assert EF.SPELLS_KNOWN in entity
    # wizard is prepared secondary → SPELLS_PREPARED_2 present
    assert EF.SPELLS_PREPARED_2 in entity


# ---------------------------------------------------------------------------
# V9-20: Entity dict is valid (no KeyError on all EF constants referenced by consumer)
# ---------------------------------------------------------------------------

def test_v9_20_entity_dict_valid_dual_caster():
    """Dual-caster entity accesses all expected EF fields without KeyError."""
    entity = _wizard_cleric_3_3()

    # All standard fields accessible
    _ = entity[EF.ENTITY_ID]
    _ = entity[EF.RACE]
    _ = entity[EF.TEAM]
    _ = entity[EF.HP_MAX]
    _ = entity[EF.HP_CURRENT]
    _ = entity[EF.BAB]
    _ = entity[EF.AC]
    _ = entity[EF.SAVE_FORT]
    _ = entity[EF.SAVE_REF]
    _ = entity[EF.SAVE_WILL]
    _ = entity[EF.LEVEL]
    _ = entity[EF.CLASS_LEVELS]
    _ = entity[EF.FEATS]
    _ = entity[EF.SKILL_RANKS]

    # Dual-caster spell fields
    _ = entity[EF.SPELL_SLOTS]
    _ = entity[EF.CASTER_LEVEL]
    _ = entity[EF.CASTER_CLASS]
    _ = entity[EF.SPELL_SLOTS_2]
    _ = entity[EF.CASTER_LEVEL_2]
    _ = entity[EF.CASTER_CLASS_2]
