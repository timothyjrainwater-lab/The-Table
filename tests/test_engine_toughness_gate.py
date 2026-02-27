"""
ENGINE GATE -- WO-ENGINE-TOUGHNESS-001: Toughness feat HP bonus
Tests TG-001 through TG-008.
PHB p.101: Toughness grants +3 HP (stackable). Applied at chargen and level-up.
Source: builder.py WO-ENGINE-TOUGHNESS-001 blocks.
feats.py: no explicit stackable flag — count("toughness") handles multiples.
"""
import pytest
from aidm.chargen.builder import build_character, level_up
from aidm.schemas.entity_fields import EF


def _base_hp(race="human", class_name="fighter", level=1):
    """Build entity WITHOUT Toughness, return HP_MAX as baseline."""
    e = build_character(
        race=race, class_name=class_name, level=level,
        ability_method="standard",
        ability_overrides={"str": 14, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
    )
    return e[EF.HP_MAX]


# TG-001: Build entity with Toughness → HP_MAX = base + 3 ─────────────────────────────

def test_tg001_toughness_adds_3_to_hp_max():
    """Single Toughness: HP_MAX increases by exactly 3."""
    base = _base_hp()
    entity = build_character(
        race="human", class_name="fighter", level=1,
        ability_method="standard",
        ability_overrides={"str": 14, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
        feat_choices=["toughness"],
    )
    assert entity[EF.HP_MAX] == base + 3, (
        f"Expected HP_MAX={base + 3} with Toughness, got {entity[EF.HP_MAX]}"
    )


# TG-002: Build entity without Toughness → HP_MAX unchanged ───────────────────────────

def test_tg002_no_toughness_hp_unchanged():
    """Without Toughness: HP_MAX is unaffected."""
    entity = build_character(
        race="human", class_name="fighter", level=1,
        ability_method="standard",
        ability_overrides={"str": 14, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
    )
    base = _base_hp()
    assert entity[EF.HP_MAX] == base, (
        f"Without Toughness, HP_MAX should be {base}, got {entity[EF.HP_MAX]}"
    )


# TG-003: Two instances of Toughness → HP_MAX = base + 6 ─────────────────────────────

def test_tg003_two_toughness_instances_add_6():
    """Two Toughness feats: HP_MAX increases by 6."""
    base = _base_hp()
    entity = build_character(
        race="human", class_name="fighter", level=1,
        ability_method="standard",
        ability_overrides={"str": 14, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
        feat_choices=["toughness", "toughness"],
    )
    assert entity[EF.HP_MAX] == base + 6, (
        f"Expected HP_MAX={base + 6} with 2x Toughness, got {entity[EF.HP_MAX]}"
    )


# TG-004: Toughness at level-up → HP_MAX incremented at level-up ──────────────────────

def test_tg004_toughness_at_level_up():
    """Toughness granted at level-up (level 2→3, feat slot guaranteed): hp_gained +3."""
    # Build at level 2; level 3 always has a feat slot for all characters (PHB p.58)
    entity = build_character(
        race="human", class_name="fighter", level=2,
        ability_method="standard",
        ability_overrides={"str": 14, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
    )
    delta_with = level_up(entity, "fighter", 3, feat_choices=["toughness"], hp_seed=42)
    delta_without = level_up(entity, "fighter", 3, feat_choices=[], hp_seed=42)
    hp_with = delta_with["hp_gained"]
    hp_without = delta_without["hp_gained"]
    assert hp_with == hp_without + 3, (
        f"Level-up with Toughness should yield 3 more HP. Got with={hp_with}, without={hp_without}"
    )
    assert "toughness" in delta_with["feats_added"], "Toughness must appear in feats_added"


# TG-005: Non-fighter race with Toughness → still applies ────────────────────────────

def test_tg005_non_fighter_toughness_applies():
    """Toughness works for any race/class combo."""
    base = _base_hp(race="elf", class_name="rogue", level=1)
    entity = build_character(
        race="elf", class_name="rogue", level=1,
        ability_method="standard",
        ability_overrides={"str": 10, "dex": 14, "con": 10, "int": 10, "wis": 10, "cha": 10},
        feat_choices=["toughness"],
    )
    assert entity[EF.HP_MAX] == base + 3, (
        f"Elf rogue with Toughness: expected {base + 3}, got {entity[EF.HP_MAX]}"
    )


# TG-006: Toughness HP bonus applies to EF.HP_CURRENT as well ────────────────────────

def test_tg006_toughness_applies_to_hp_current():
    """Toughness +3 is applied to both HP_MAX and HP_CURRENT at chargen."""
    entity_no_t = build_character(
        race="human", class_name="fighter", level=1,
        ability_method="standard",
        ability_overrides={"str": 14, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
    )
    entity_t = build_character(
        race="human", class_name="fighter", level=1,
        ability_method="standard",
        ability_overrides={"str": 14, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
        feat_choices=["toughness"],
    )
    assert entity_t[EF.HP_CURRENT] == entity_no_t[EF.HP_CURRENT] + 3, (
        f"HP_CURRENT must include Toughness bonus. "
        f"Expected {entity_no_t[EF.HP_CURRENT] + 3}, got {entity_t[EF.HP_CURRENT]}"
    )


# TG-007: Toughness does not affect nonlethal threshold calculation ──────────────────

def test_tg007_toughness_does_not_affect_nonlethal_threshold():
    """Toughness raises HP_MAX but should not change the nonlethal-threshold mechanics.
    The nonlethal threshold is == HP_MAX, so it increases with HP_MAX — that is correct PHB
    behavior. What we verify is that no extra (unexpected) HP penalty or threshold shift
    is introduced beyond the +3."""
    entity_no_t = build_character(
        race="human", class_name="fighter", level=1,
        ability_method="standard",
        ability_overrides={"str": 14, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
    )
    entity_t = build_character(
        race="human", class_name="fighter", level=1,
        ability_method="standard",
        ability_overrides={"str": 14, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
        feat_choices=["toughness"],
    )
    # HP_MAX difference must be exactly 3 — no extra adjustments
    diff = entity_t[EF.HP_MAX] - entity_no_t[EF.HP_MAX]
    assert diff == 3, f"Toughness must add exactly 3 to HP_MAX, got diff={diff}"
    # HP_CURRENT difference also exactly 3
    diff_cur = entity_t[EF.HP_CURRENT] - entity_no_t[EF.HP_CURRENT]
    assert diff_cur == 3, f"Toughness must add exactly 3 to HP_CURRENT, got diff={diff_cur}"


# TG-008: Regression — chargen entities without Toughness unaffected ─────────────────

def test_tg008_regression_no_toughness_unchanged():
    """Level-1 fighter without Toughness has exact expected HP (d10 max at L1 + CON mod = 10)."""
    entity = build_character(
        race="human", class_name="fighter", level=1,
        ability_method="standard",
        ability_overrides={"str": 14, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
    )
    # First level = max HP = d10 = 10; CON 10 → +0; no Toughness → HP_MAX = 10
    assert entity[EF.HP_MAX] == 10, (
        f"Level-1 fighter, CON 10, no Toughness: expected HP_MAX=10, got {entity[EF.HP_MAX]}"
    )
    assert "toughness" not in entity.get(EF.FEATS, []), "Entity must not have Toughness feat"
