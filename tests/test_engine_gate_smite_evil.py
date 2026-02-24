"""ENGINE-SMITE-EVIL Gate -- Paladin Smite Evil runtime (8 tests).

Gate: ENGINE-SMITE-EVIL
Tests: SE-01 through SE-08
WO: WO-ENGINE-SMITE-EVIL-001
"""

import pytest
from copy import deepcopy
from unittest import mock

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.attack import Weapon
from aidm.schemas.intents import SmiteEvilIntent
from aidm.core.smite_evil_resolver import validate_smite, resolve_smite_evil


LONGSWORD = Weapon(
    damage_dice="1d8",
    damage_bonus=0,
    damage_type="slashing",
    critical_multiplier=2,
    critical_range=20,
    weapon_type="one-handed",
    grip="one-handed",
)


def _paladin(eid="paladin", level=5, cha_mod=3, smite_uses=2):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 16,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: 3,
        EF.DEX_MOD: 1,
        EF.CON_MOD: 2,
        EF.CHA_MOD: cha_mod,
        EF.BAB: level,
        EF.ATTACK_BONUS: level + 3,  # BAB + STR
        EF.CLASS_LEVELS: {"paladin": level},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.SMITE_USES_REMAINING: smite_uses,
    }


def _goblin(eid="goblin", hp=20):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 13,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 1, "y": 0},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
    }


def _fighter(eid="fighter"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 25,
        EF.HP_MAX: 25,
        EF.AC: 15,
        EF.DEFEATED: False,
        EF.CLASS_LEVELS: {"fighter": 3},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.SMITE_USES_REMAINING: 0,
        EF.ATTACK_BONUS: 5,
    }


def _world(entities):
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
            "cleave_used_this_turn": set(),
        },
    )


def _mock_rng(rolls):
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [10] * 200
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ===========================================================================
# SE-01: Smite vs evil -- attack events contain expected bonuses
# ===========================================================================

def test_se01_smite_vs_evil_attack_resolves():
    """SE-01: Smite Evil vs evil target resolves an attack (attack_roll event emitted)."""
    paladin = _paladin(level=5, cha_mod=3, smite_uses=1)
    goblin = _goblin()
    ws = _world({"paladin": paladin, "goblin": goblin})
    intent = SmiteEvilIntent(actor_id="paladin", target_id="goblin",
                              weapon=LONGSWORD, target_is_evil=True)
    rng = _mock_rng([15, 5])  # d20=15 (hit), damage=5

    events, ws2 = resolve_smite_evil(intent, ws, rng, 0, 0.0)

    event_types = [e.event_type for e in events]
    assert "smite_declared" in event_types, f"Expected smite_declared, got: {event_types}"
    assert "attack_roll" in event_types, f"Expected attack_roll, got: {event_types}"


# ===========================================================================
# SE-02: smite_declared event has correct bonus values
# ===========================================================================

def test_se02_smite_declared_payload():
    """SE-02: smite_declared payload has attack_bonus=CHA mod, damage_bonus=paladin level."""
    paladin = _paladin(level=5, cha_mod=3, smite_uses=1)
    goblin = _goblin()
    ws = _world({"paladin": paladin, "goblin": goblin})
    intent = SmiteEvilIntent(actor_id="paladin", target_id="goblin",
                              weapon=LONGSWORD, target_is_evil=True)
    rng = _mock_rng([15, 5])

    events, _ = resolve_smite_evil(intent, ws, rng, 0, 0.0)

    smite_ev = next(e for e in events if e.event_type == "smite_declared")
    assert smite_ev.payload["attack_bonus"] == 3, f"Expected CHA mod 3, got {smite_ev.payload['attack_bonus']}"
    assert smite_ev.payload["damage_bonus"] == 5, f"Expected paladin level 5, got {smite_ev.payload['damage_bonus']}"
    assert smite_ev.payload["target_is_evil"] is True


# ===========================================================================
# SE-03: SMITE_USES_REMAINING decremented
# ===========================================================================

def test_se03_smite_uses_decremented():
    """SE-03: SMITE_USES_REMAINING decremented by 1 after smite."""
    paladin = _paladin(level=5, cha_mod=3, smite_uses=2)
    goblin = _goblin()
    ws = _world({"paladin": paladin, "goblin": goblin})
    intent = SmiteEvilIntent(actor_id="paladin", target_id="goblin",
                              weapon=LONGSWORD, target_is_evil=True)
    rng = _mock_rng([15, 5])

    _, ws2 = resolve_smite_evil(intent, ws, rng, 0, 0.0)
    assert ws2.entities["paladin"][EF.SMITE_USES_REMAINING] == 1


# ===========================================================================
# SE-04: Smite vs non-evil -- use consumed, bonuses not applied
# ===========================================================================

def test_se04_smite_vs_non_evil_no_bonus():
    """SE-04: target_is_evil=False: use consumed, attack/damage bonuses = 0."""
    paladin = _paladin(level=5, cha_mod=3, smite_uses=1)
    goblin = _goblin()
    ws = _world({"paladin": paladin, "goblin": goblin})
    intent = SmiteEvilIntent(actor_id="paladin", target_id="goblin",
                              weapon=LONGSWORD, target_is_evil=False)
    rng = _mock_rng([15, 5])

    events, ws2 = resolve_smite_evil(intent, ws, rng, 0, 0.0)

    # Use should be consumed
    assert ws2.entities["paladin"][EF.SMITE_USES_REMAINING] == 0

    smite_ev = next(e for e in events if e.event_type == "smite_declared")
    assert smite_ev.payload["attack_bonus"] == 0, "No attack bonus vs non-evil"
    assert smite_ev.payload["damage_bonus"] == 0, "No damage bonus vs non-evil"
    assert smite_ev.payload["target_is_evil"] is False


# ===========================================================================
# SE-05: No uses remaining -- intent_validation_failed
# ===========================================================================

def test_se05_no_smite_uses():
    """SE-05: validate_smite returns no_smite_uses when SMITE_USES_REMAINING is 0."""
    paladin = _paladin(level=5, cha_mod=3, smite_uses=0)
    ws = _world({"paladin": paladin})
    reason = validate_smite(ws.entities["paladin"], ws)
    assert reason == "no_smite_uses", f"Got {reason!r}"


# ===========================================================================
# SE-06: Non-paladin cannot smite
# ===========================================================================

def test_se06_not_a_paladin():
    """SE-06: validate_smite returns not_a_paladin for non-Paladin entity."""
    fighter = _fighter()
    fighter[EF.SMITE_USES_REMAINING] = 1
    ws = _world({"fighter": fighter})
    reason = validate_smite(ws.entities["fighter"], ws)
    assert reason == "not_a_paladin", f"Got {reason!r}"


# ===========================================================================
# SE-07: Smite damage bonus = paladin class level (not total level)
# ===========================================================================

def test_se07_damage_bonus_is_paladin_level():
    """SE-07: Multiclass paladin/fighter -- damage bonus = paladin level only."""
    multiclass = _paladin(level=3, cha_mod=2, smite_uses=1)
    # Add fighter levels -- damage bonus should still be 3 (paladin level)
    multiclass[EF.CLASS_LEVELS] = {"paladin": 3, "fighter": 4}
    goblin = _goblin()
    ws = _world({"paladin": multiclass, "goblin": goblin})
    intent = SmiteEvilIntent(actor_id="paladin", target_id="goblin",
                              weapon=LONGSWORD, target_is_evil=True)
    rng = _mock_rng([15, 5])

    events, _ = resolve_smite_evil(intent, ws, rng, 0, 0.0)

    smite_ev = next(e for e in events if e.event_type == "smite_declared")
    assert smite_ev.payload["damage_bonus"] == 3, f"Expected 3 (paladin level), got {smite_ev.payload['damage_bonus']}"


# ===========================================================================
# SE-08: Smite attack bonus = CHA modifier (not CHA score)
# ===========================================================================

def test_se08_attack_bonus_is_cha_mod():
    """SE-08: smite_declared attack_bonus equals CHA modifier, not raw CHA score."""
    paladin = _paladin(level=5, cha_mod=4, smite_uses=1)
    goblin = _goblin()
    ws = _world({"paladin": paladin, "goblin": goblin})
    intent = SmiteEvilIntent(actor_id="paladin", target_id="goblin",
                              weapon=LONGSWORD, target_is_evil=True)
    rng = _mock_rng([15, 5])

    events, _ = resolve_smite_evil(intent, ws, rng, 0, 0.0)

    smite_ev = next(e for e in events if e.event_type == "smite_declared")
    assert smite_ev.payload["attack_bonus"] == 4, f"Expected CHA mod 4, got {smite_ev.payload['attack_bonus']}"
