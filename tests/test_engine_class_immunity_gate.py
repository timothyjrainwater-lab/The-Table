"""Gate tests: WO-ENGINE-CLASS-IMMUNITY-001

Purity of Body (PHB p.42): Monk L5+ immune to all diseases.
Diamond Body (PHB p.42): Monk L11+ immune to all poisons.
Venom Immunity (PHB p.38): Druid L9+ immune to all poisons.

CLI-001 – CLI-008 (8 tests)
"""
import pytest

from aidm.core.poison_disease_resolver import (
    apply_disease_exposure,
    apply_poison,
    is_immune_to_poison,
)
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# RNG helpers
# ---------------------------------------------------------------------------

class _AlwaysFailRNG:
    """RNG that always rolls 1 — entity always fails saves."""

    class _Stream:
        def randint(self, lo, hi):
            return 1

    def stream(self, name):
        return self._Stream()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FILTH_FEVER = {
    "disease_id": "filth_fever",
    "dc": 12,
    "incubation_rounds": 0,
    "interval_rounds": 10,
    "damage_ability": "str",
    "damage_amount": 1,
}

MUMMY_ROT = {
    "disease_id": "mummy_rot",
    "dc": 20,
    "incubation_rounds": 0,
    "interval_rounds": 10,
    "damage_ability": "str",
    "damage_amount": 3,
}

GIANT_WASP_POISON = {
    "poison_id": "giant_wasp_poison",
    "dc": 18,
    "initial_ability": "dex",
    "initial_amount": 1,
    "secondary_ability": "dex",
    "secondary_amount": 1,
}


def _monk(level=5):
    return {
        EF.ENTITY_ID: "monk",
        EF.CLASS_LEVELS: {"monk": level},
        EF.SAVE_FORT: 5,
        EF.CON_MOD: 2,
        EF.ACTIVE_DISEASES: [],
        EF.ACTIVE_POISONS: [],
    }


def _druid(level=9):
    return {
        EF.ENTITY_ID: "druid",
        EF.CLASS_LEVELS: {"druid": level},
        EF.SAVE_FORT: 5,
        EF.CON_MOD: 2,
        EF.ACTIVE_DISEASES: [],
        EF.ACTIVE_POISONS: [],
    }


def _paladin(level=3):
    return {
        EF.ENTITY_ID: "paladin",
        EF.CLASS_LEVELS: {"paladin": level},
        EF.SAVE_FORT: 5,
        EF.CON_MOD: 2,
        EF.ACTIVE_DISEASES: [],
        EF.ACTIVE_POISONS: [],
    }


# ---------------------------------------------------------------------------
# CLI-001: Monk L5 immune to disease (purity_of_body)
# ---------------------------------------------------------------------------

def test_cli_001_monk_l5_disease_immune():
    """CLI-001: Monk L5 immune to disease via Purity of Body."""
    monk = _monk(level=5)
    entity, events = apply_disease_exposure(
        entity=monk, target_id="monk", source_id="rat",
        disease_stat=FILTH_FEVER, current_round=1,
        rng=_AlwaysFailRNG(), next_event_id=1, timestamp=0.0,
    )
    imm = [e for e in events if e["event_type"] == "disease_immunity"]
    assert len(imm) == 1
    assert imm[0]["payload"]["reason"] == "purity_of_body"
    assert entity.get(EF.ACTIVE_DISEASES, []) == []


# ---------------------------------------------------------------------------
# CLI-002: Monk L4 NOT immune to disease
# ---------------------------------------------------------------------------

def test_cli_002_monk_l4_not_disease_immune():
    """CLI-002: Monk L4 — Purity of Body not yet available."""
    monk = _monk(level=4)
    entity, events = apply_disease_exposure(
        entity=monk, target_id="monk", source_id="rat",
        disease_stat=FILTH_FEVER, current_round=1,
        rng=_AlwaysFailRNG(), next_event_id=1, timestamp=0.0,
    )
    assert not any(e["event_type"] == "disease_immunity" for e in events)
    # Should fail save and contract disease
    assert any(e["event_type"] == "disease_contracted" for e in events)


# ---------------------------------------------------------------------------
# CLI-003: Monk L5 blocks supernatural disease (mummy rot)
# ---------------------------------------------------------------------------

def test_cli_003_monk_l5_supernatural_disease_blocked():
    """CLI-003: Purity of Body blocks supernatural diseases too."""
    monk = _monk(level=5)
    entity, events = apply_disease_exposure(
        entity=monk, target_id="monk", source_id="mummy",
        disease_stat=MUMMY_ROT, current_round=1,
        rng=_AlwaysFailRNG(), next_event_id=1, timestamp=0.0,
    )
    imm = [e for e in events if e["event_type"] == "disease_immunity"]
    assert len(imm) == 1
    assert imm[0]["payload"]["reason"] == "purity_of_body"
    assert imm[0]["payload"]["disease_id"] == "mummy_rot"


# ---------------------------------------------------------------------------
# CLI-004: Monk L11 immune to poison (diamond_body)
# ---------------------------------------------------------------------------

def test_cli_004_monk_l11_poison_immune():
    """CLI-004: Monk L11 immune to poison via Diamond Body."""
    monk = _monk(level=11)
    entity, events = apply_poison(
        entity=monk, target_id="monk", source_id="spider",
        poison_stat=GIANT_WASP_POISON, current_round=1,
        rng=_AlwaysFailRNG(), next_event_id=1, timestamp=0.0,
    )
    imm = [e for e in events if e.get("event_type") == "poison_immune"]
    assert len(imm) == 1
    assert imm[0]["payload"]["reason"] == "diamond_body"


# ---------------------------------------------------------------------------
# CLI-005: Monk L10 NOT immune to poison
# ---------------------------------------------------------------------------

def test_cli_005_monk_l10_not_poison_immune():
    """CLI-005: Monk L10 — Diamond Body not yet available."""
    monk = _monk(level=10)
    assert not is_immune_to_poison(monk)
    entity, events = apply_poison(
        entity=monk, target_id="monk", source_id="spider",
        poison_stat=GIANT_WASP_POISON, current_round=1,
        rng=_AlwaysFailRNG(), next_event_id=1, timestamp=0.0,
    )
    assert not any(e.get("event_type") == "poison_immune" for e in events)
    assert any(e.get("event_type") == "poison_save_initial" for e in events)


# ---------------------------------------------------------------------------
# CLI-006: Druid L9 immune to poison (venom_immunity)
# ---------------------------------------------------------------------------

def test_cli_006_druid_l9_poison_immune():
    """CLI-006: Druid L9 immune to poison via Venom Immunity."""
    druid = _druid(level=9)
    entity, events = apply_poison(
        entity=druid, target_id="druid", source_id="snake",
        poison_stat=GIANT_WASP_POISON, current_round=1,
        rng=_AlwaysFailRNG(), next_event_id=1, timestamp=0.0,
    )
    imm = [e for e in events if e.get("event_type") == "poison_immune"]
    assert len(imm) == 1
    assert imm[0]["payload"]["reason"] == "venom_immunity"


# ---------------------------------------------------------------------------
# CLI-007: Druid L8 NOT immune to poison
# ---------------------------------------------------------------------------

def test_cli_007_druid_l8_not_poison_immune():
    """CLI-007: Druid L8 — Venom Immunity not yet available."""
    druid = _druid(level=8)
    assert not is_immune_to_poison(druid)
    entity, events = apply_poison(
        entity=druid, target_id="druid", source_id="snake",
        poison_stat=GIANT_WASP_POISON, current_round=1,
        rng=_AlwaysFailRNG(), next_event_id=1, timestamp=0.0,
    )
    assert not any(e.get("event_type") == "poison_immune" for e in events)


# ---------------------------------------------------------------------------
# CLI-008: Paladin L3 immune to disease but NOT poison
# ---------------------------------------------------------------------------

def test_cli_008_paladin_disease_yes_poison_no():
    """CLI-008: Paladin L3 disease immune (Divine Health) but NOT poison immune."""
    paladin = _paladin(level=3)

    # Disease: immune via Divine Health
    entity_d, events_d = apply_disease_exposure(
        entity=paladin.copy(), target_id="paladin", source_id="rat",
        disease_stat=FILTH_FEVER, current_round=1,
        rng=_AlwaysFailRNG(), next_event_id=1, timestamp=0.0,
    )
    assert any(e["event_type"] == "disease_immunity" for e in events_d)

    # Poison: NOT immune
    assert not is_immune_to_poison(paladin)
    entity_p, events_p = apply_poison(
        entity=paladin.copy(), target_id="paladin", source_id="wasp",
        poison_stat=GIANT_WASP_POISON, current_round=1,
        rng=_AlwaysFailRNG(), next_event_id=1, timestamp=0.0,
    )
    assert not any(e.get("event_type") == "poison_immune" for e in events_p)
    assert any(e.get("event_type") == "poison_save_initial" for e in events_p)
