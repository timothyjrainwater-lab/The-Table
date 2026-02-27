"""Domain System Gate Tests — DOMAIN-001 through DOMAIN-006.

WO: ENGINE-DOMAIN-SYSTEM-001 (Batch V WO3)
Authority: RAW — PHB p.32 (domain selection), p.33 (Sun domain Greater Turning).

DOMAIN-001: EF.DOMAINS field exists in entity_fields
DOMAIN-002: cleric built with domains=["sun"] has EF.DOMAINS == ["sun"]
DOMAIN-003: cleric built with no domains has EF.DOMAINS == []
DOMAIN-004: Sun domain cleric — greater_turning=True → undead_destroyed_by_greater_turning
DOMAIN-005: Non-Sun domain cleric — greater_turning=True treated as normal turning (no destroy)
DOMAIN-006: Sun domain cleric — regular turning (greater_turning=False) still works normally
"""
import unittest.mock as mock
from typing import Any, Dict, List

import pytest

from aidm.core.state import WorldState
from aidm.core.turn_undead_resolver import apply_turn_undead_events, resolve_turn_undead
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import TurnUndeadIntent
from aidm.chargen.builder import build_character


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cleric(
    eid: str = "cleric1",
    level: int = 5,
    cha_mod: int = 2,
    uses: int = 5,
    domains: List[str] = None,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 15,
        EF.LEVEL: level,
        EF.CHA_MOD: cha_mod,
        EF.TURN_UNDEAD_USES: uses,
        EF.TURN_UNDEAD_USES_MAX: uses,
        EF.CLASS_LEVELS: {"cleric": level},
        "class_features": {},
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.FEATS: [],
        EF.DOMAINS: list(domains) if domains else [],
    }


def _undead(eid: str, hd: int = 2, hp: int = 10) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "enemies",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 10,
        EF.IS_UNDEAD: True,
        EF.HD_COUNT: hd,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 1, "y": 0},
        EF.FEATS: [],
    }


def _world(entities: List[Dict]) -> WorldState:
    return WorldState(
        entities={e[EF.ENTITY_ID]: e for e in entities},
        active_combat={},
        ruleset_version="3.5e",
    )


def _seeded_rng(d20: int = 15, d6a: int = 3, d6b: int = 3):
    """Seeded RNG: d20 for turning check, d6×2 for HP budget."""
    rng = mock.MagicMock()
    stream = mock.MagicMock()
    stream.randint.side_effect = [d20, d6a, d6b]
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# DOMAIN-001: EF.DOMAINS exists in entity_fields
# ---------------------------------------------------------------------------

def test_domain001_ef_domains_exists():
    """DOMAIN-001: EF.DOMAINS constant must exist in entity_fields."""
    assert hasattr(EF, "DOMAINS"), "EF.DOMAINS must be defined in entity_fields.py"
    assert isinstance(EF.DOMAINS, str), "EF.DOMAINS must be a string constant"


# ---------------------------------------------------------------------------
# DOMAIN-002: cleric with domains=["sun"] built correctly
# ---------------------------------------------------------------------------

def test_domain002_cleric_with_sun_domain():
    """DOMAIN-002: build_character with domains=['sun'] stores EF.DOMAINS=['sun']."""
    entity = build_character(
        race="human",
        class_name="cleric",
        level=5,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 14},
        domains=["sun"],
    )
    assert entity.get(EF.DOMAINS) == ["sun"], (
        f"Expected EF.DOMAINS=['sun'], got {entity.get(EF.DOMAINS)!r}"
    )


# ---------------------------------------------------------------------------
# DOMAIN-003: cleric with no domains has EF.DOMAINS == []
# ---------------------------------------------------------------------------

def test_domain003_cleric_no_domains():
    """DOMAIN-003: build_character with domains=None stores EF.DOMAINS=[]."""
    entity = build_character(
        race="human",
        class_name="cleric",
        level=5,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 14},
    )
    assert entity.get(EF.DOMAINS) == [], (
        f"Expected EF.DOMAINS=[], got {entity.get(EF.DOMAINS)!r}"
    )


# ---------------------------------------------------------------------------
# DOMAIN-004: Sun domain + greater_turning=True → undead_destroyed_by_greater_turning
# ---------------------------------------------------------------------------

def test_domain004_sun_domain_greater_turning_destroys():
    """DOMAIN-004: Sun domain cleric + greater_turning=True → turned undead destroyed.

    Seeded: d20=15 (turning check = 15+2=17), budget = (3+3)*10=60.
    Undead HD=2 ≤ turning check 17 → normally 'turned'. With Greater Turning → destroyed.
    """
    undead = _undead("u1", hd=2, hp=10)
    cleric = _cleric("c1", level=5, cha_mod=2, domains=["sun"])
    ws = _world([cleric, undead])

    intent = TurnUndeadIntent(
        cleric_id="c1",
        target_ids=["u1"],
        greater_turning=True,
    )
    events = resolve_turn_undead(intent, ws, _seeded_rng(d20=15), next_event_id=1, timestamp=0.0)
    event_types = [e.event_type for e in events]

    assert any(
        et in ("undead_destroyed", "undead_destroyed_by_greater_turning")
        for et in event_types
    ), (
        f"Sun domain Greater Turning must produce a destroy event; got {event_types}"
    )
    assert "undead_turned" not in event_types, (
        f"Greater Turning must NOT emit undead_turned; got {event_types}"
    )


# ---------------------------------------------------------------------------
# DOMAIN-005: Non-Sun domain + greater_turning=True → normal turning (no destroy)
# ---------------------------------------------------------------------------

def test_domain005_non_sun_domain_greater_turning_is_normal():
    """DOMAIN-005: Non-Sun domain + greater_turning=True → treated as normal turning.

    Seeded: d20=15, turning check=17, undead HD=2 ≤ 17 → undead_turned (not destroyed).
    """
    undead = _undead("u1", hd=2, hp=10)
    cleric = _cleric("c1", level=5, cha_mod=2, domains=["fire"])  # fire domain, NOT sun
    ws = _world([cleric, undead])

    intent = TurnUndeadIntent(
        cleric_id="c1",
        target_ids=["u1"],
        greater_turning=True,  # flag set but no Sun domain
    )
    events = resolve_turn_undead(intent, ws, _seeded_rng(d20=15), next_event_id=1, timestamp=0.0)
    event_types = [e.event_type for e in events]

    assert "undead_turned" in event_types, (
        f"Non-Sun domain cleric must emit undead_turned for eligible undead; got {event_types}"
    )
    assert "undead_destroyed_by_greater_turning" not in event_types, (
        f"Non-Sun domain must not emit destroy event; got {event_types}"
    )


# ---------------------------------------------------------------------------
# DOMAIN-006: Sun domain + greater_turning=False → regular turning still works
# ---------------------------------------------------------------------------

def test_domain006_sun_domain_regular_turning_works():
    """DOMAIN-006: Sun domain cleric with greater_turning=False → normal undead_turned.

    Seeded: d20=15, turning check=17, undead HD=2 ≤ 17 → undead_turned (not destroyed).
    """
    undead = _undead("u1", hd=2, hp=10)
    cleric = _cleric("c1", level=5, cha_mod=2, domains=["sun"])
    ws = _world([cleric, undead])

    intent = TurnUndeadIntent(
        cleric_id="c1",
        target_ids=["u1"],
        greater_turning=False,
    )
    events = resolve_turn_undead(intent, ws, _seeded_rng(d20=15), next_event_id=1, timestamp=0.0)
    event_types = [e.event_type for e in events]

    assert "undead_turned" in event_types, (
        f"Sun domain cleric regular turning must emit undead_turned; got {event_types}"
    )
    assert "undead_destroyed_by_greater_turning" not in event_types, (
        f"Regular turning must not emit greater turning destroy event; got {event_types}"
    )
