"""Gate tests — WO-ENGINE-CONDITION-IMMUNE-TO-WIRE-001
CIT-001..008: ConditionInstance.immune_to scan in is_immune_to_poison() and apply_disease_exposure()
"""
from __future__ import annotations
from unittest.mock import MagicMock
from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import ConditionType, ConditionInstance, ConditionModifiers
from aidm.core.poison_disease_resolver import is_immune_to_poison, apply_disease_exposure


def _petrified_entity() -> dict:
    """Entity with PETRIFIED condition (immune_to=["poison","disease"])."""
    from aidm.schemas.conditions import create_petrified_condition
    ci = create_petrified_condition("test_source", 0)
    return {
        EF.CONDITIONS: {"petrified": ci.to_dict()},
        EF.CLASS_LEVELS: {},
        EF.IS_UNDEAD: False,
    }


def _living_entity() -> dict:
    """Plain living entity with no conditions."""
    return {
        EF.CONDITIONS: {},
        EF.CLASS_LEVELS: {},
        EF.IS_UNDEAD: False,
    }


def _disease_stat() -> dict:
    return {
        "disease_id": "filth_fever",
        "dc": 12,
        "incubation_rounds": 10,
        "interval_rounds": 10,
        "damage_ability": "dex",
        "damage_amount": 1,
    }


def _poison_stat() -> dict:
    return {
        "poison_id": "giant_wasp_poison",
        "dc": 18,
        "initial_ability": "dex",
        "initial_amount": 1,
        "secondary_ability": "dex",
        "secondary_amount": 1,
    }


def _rng_fixed(roll: int = 15) -> MagicMock:
    rng = MagicMock()
    rng.stream.return_value.randint.return_value = roll
    return rng


# ==============================================================================
# CIT-001: Petrified entity — poison attempt → immune (True)
# ==============================================================================

def test_CIT001_petrified_immune_to_poison():
    """CIT-001: Petrified entity has immune_to=['poison','disease'] — is_immune_to_poison returns True."""
    entity = _petrified_entity()
    assert is_immune_to_poison(entity) is True


# ==============================================================================
# CIT-002: Non-petrified living entity — poison → NOT immune
# ==============================================================================

def test_CIT002_living_not_immune_to_poison():
    """CIT-002: Plain living entity has no immune_to entries — is_immune_to_poison returns False."""
    entity = _living_entity()
    assert is_immune_to_poison(entity) is False


# ==============================================================================
# CIT-003: Petrified entity — disease attempt → immune
# ==============================================================================

def test_CIT003_petrified_immune_to_disease():
    """CIT-003: Petrified entity — apply_disease_exposure returns disease_immunity event."""
    entity = _petrified_entity()
    rng = _rng_fixed(5)
    _, events = apply_disease_exposure(
        entity, "target_1", "source_1", _disease_stat(), 1, rng, 0, 0.0
    )
    immunity_events = [e for e in events if e.get("event_type") == "disease_immunity"]
    assert len(immunity_events) == 1
    assert immunity_events[0]["payload"]["reason"] == "condition_immune_to"


# ==============================================================================
# CIT-004: Non-petrified entity — disease → NOT immune (save attempted)
# ==============================================================================

def test_CIT004_living_not_immune_to_disease():
    """CIT-004: Plain living entity — apply_disease_exposure proceeds to save (no disease_immunity event)."""
    entity = _living_entity()
    rng = _rng_fixed(15)
    _, events = apply_disease_exposure(
        entity, "target_1", "source_1", _disease_stat(), 1, rng, 0, 0.0
    )
    immunity_events = [e for e in events if e.get("event_type") == "disease_immunity"]
    assert len(immunity_events) == 0


# ==============================================================================
# CIT-005: Entity with no conditions — poison → NOT immune
# ==============================================================================

def test_CIT005_no_conditions_not_immune():
    """CIT-005: Entity with EF.CONDITIONS={} — immune_to scan returns nothing → not immune."""
    entity = {
        EF.CONDITIONS: {},
        EF.CLASS_LEVELS: {},
        EF.IS_UNDEAD: False,
    }
    assert is_immune_to_poison(entity) is False


# ==============================================================================
# CIT-006: Undead entity — immune via class check (not immune_to scan) → True
# ==============================================================================

def test_CIT006_undead_still_immune_via_class_check():
    """CIT-006: Undead entity — is_immune_to_poison returns True via EF.IS_UNDEAD check (not immune_to)."""
    entity = {
        EF.CONDITIONS: {},
        EF.CLASS_LEVELS: {},
        EF.IS_UNDEAD: True,
    }
    assert is_immune_to_poison(entity) is True


# ==============================================================================
# CIT-007: Monk L11+ — immune via class check → still True
# ==============================================================================

def test_CIT007_monk_11_diamond_body_immune():
    """CIT-007: Monk level 11 — Diamond Body grants poison immunity via class check."""
    entity = {
        EF.CONDITIONS: {},
        EF.CLASS_LEVELS: {"monk": 11},
        EF.IS_UNDEAD: False,
    }
    assert is_immune_to_poison(entity) is True


# ==============================================================================
# CIT-008: Round-trip — immune_to survives to_dict() + from_dict()
# ==============================================================================

def test_CIT008_immune_to_roundtrip():
    """CIT-008: ConditionInstance with immune_to survives to_dict() + from_dict() intact."""
    from aidm.schemas.conditions import create_petrified_condition
    ci_orig = create_petrified_condition("test", 0)
    assert "poison" in ci_orig.immune_to
    assert "disease" in ci_orig.immune_to

    d = ci_orig.to_dict()
    assert "immune_to" in d
    assert set(d["immune_to"]) == {"poison", "disease"}

    ci_restored = ConditionInstance.from_dict(d)
    assert "poison" in ci_restored.immune_to
    assert "disease" in ci_restored.immune_to
