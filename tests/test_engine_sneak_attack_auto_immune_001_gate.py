"""Gate tests: WO-ENGINE-SNEAK-ATTACK-AUTO-IMMUNE-001 — SA/crit immunity auto-set.

PHB p.50: Undead, constructs, plants, oozes, elementals, and incorporeal
creatures are immune to sneak attack. Constructs and undead are also immune
to critical hits.

Auto-set happens in builder.py via _apply_creature_type_immunities() called
at end of build_character(). Verified against sneak_attack.py:is_target_immune()
which reads "creature_type", "immune_to_sneak_attack", "immune_to_critical_hits".

Gate label: ENGINE-SNEAK-ATTACK-AUTO-IMMUNE
Tests: SI-001 – SI-008
"""

import pytest
from aidm.chargen.builder import build_character, _apply_creature_type_immunities
from aidm.core.sneak_attack import is_target_immune
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


def _ws(entity, entity_id="target"):
    """Minimal WorldState wrapping one entity."""
    return WorldState(
        ruleset_version="3.5",
        entities={entity_id: entity},
        active_combat=None,
    )


def _minimal_entity(creature_type: str = "", entity_id: str = "target") -> dict:
    """Minimal entity dict for testing _apply_creature_type_immunities directly."""
    entity = {
        EF.ENTITY_ID: entity_id,
        EF.TEAM: "enemy",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.DEFEATED: False,
    }
    if creature_type:
        entity[EF.CREATURE_TYPE] = creature_type
    return entity


# ---------------------------------------------------------------------------
# SI-001: Undead creature → immune to sneak attack (auto-set)
# ---------------------------------------------------------------------------
def test_si001_undead_sa_immune():
    entity = build_character("human", "fighter", level=1, creature_type="undead",
                             ability_overrides={"str": 10, "dex": 10, "con": 10,
                                                "int": 10, "wis": 10, "cha": 10})
    assert entity.get("immune_to_sneak_attack") is True, \
        "Undead should have immune_to_sneak_attack=True auto-set"
    # Confirm is_target_immune() also returns True
    ws = _ws(entity, entity[EF.ENTITY_ID])
    assert is_target_immune(ws, entity[EF.ENTITY_ID]) is True


# ---------------------------------------------------------------------------
# SI-002: Undead creature → immune to critical hits (auto-set)
# ---------------------------------------------------------------------------
def test_si002_undead_crit_immune():
    entity = build_character("human", "fighter", level=1, creature_type="undead",
                             ability_overrides={"str": 10, "dex": 10, "con": 10,
                                                "int": 10, "wis": 10, "cha": 10})
    assert entity.get("immune_to_critical_hits") is True, \
        "Undead should have immune_to_critical_hits=True auto-set"


# ---------------------------------------------------------------------------
# SI-003: Construct → SA immune
# ---------------------------------------------------------------------------
def test_si003_construct_sa_immune():
    entity = _minimal_entity("construct")
    _apply_creature_type_immunities(entity)
    assert entity.get("immune_to_sneak_attack") is True, "Construct should be SA-immune"


# ---------------------------------------------------------------------------
# SI-004: Construct → crit immune
# ---------------------------------------------------------------------------
def test_si004_construct_crit_immune():
    entity = _minimal_entity("construct")
    _apply_creature_type_immunities(entity)
    assert entity.get("immune_to_critical_hits") is True, "Construct should be crit-immune"


# ---------------------------------------------------------------------------
# SI-005: Plant → SA immune but NOT crit immune
# ---------------------------------------------------------------------------
def test_si005_plant_sa_immune_not_crit():
    entity = _minimal_entity("plant")
    _apply_creature_type_immunities(entity)
    assert entity.get("immune_to_sneak_attack") is True, "Plant should be SA-immune"
    assert not entity.get("immune_to_critical_hits"), \
        "Plant is NOT crit-immune per PHB (only undead/construct)"


# ---------------------------------------------------------------------------
# SI-006: Elemental and Ooze → SA immune
# ---------------------------------------------------------------------------
def test_si006_elemental_and_ooze_sa_immune():
    for ct in ("elemental", "ooze"):
        entity = _minimal_entity(ct)
        _apply_creature_type_immunities(entity)
        assert entity.get("immune_to_sneak_attack") is True, \
            f"{ct} should be SA-immune but is not"


# ---------------------------------------------------------------------------
# SI-007: Humanoid creature → neither immune (no creature_type = default humanoid)
# ---------------------------------------------------------------------------
def test_si007_humanoid_not_immune():
    entity = build_character("human", "fighter", level=1,
                             ability_overrides={"str": 10, "dex": 10, "con": 10,
                                                "int": 10, "wis": 10, "cha": 10})
    # No creature_type passed → no SA or crit immunity auto-set
    assert not entity.get("immune_to_sneak_attack"), \
        "Default human fighter should NOT be SA-immune"
    assert not entity.get("immune_to_critical_hits"), \
        "Default human fighter should NOT be crit-immune"


# ---------------------------------------------------------------------------
# SI-008: Explicit True immune flag preserved even for humanoid creature_type
# ---------------------------------------------------------------------------
def test_si008_explicit_immune_flag_preserved():
    # Entity manually marked immune (e.g. via template or special ability)
    # but creature_type is humanoid — _apply_creature_type_immunities must not clear it
    entity = _minimal_entity("humanoid")
    entity["immune_to_sneak_attack"] = True  # explicit override
    _apply_creature_type_immunities(entity)
    assert entity.get("immune_to_sneak_attack") is True, \
        "Explicit immune_to_sneak_attack=True must not be cleared by auto-set"
