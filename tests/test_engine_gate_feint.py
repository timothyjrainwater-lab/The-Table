"""Gate ENGINE-FEINT — WO-ENGINE-FEINT-001

Tests:
FT-01: Successful feint (Bluff > SM+BAB) stores marker in feint_flat_footed
FT-02: Failed feint (Bluff <= SM+BAB) stores no marker; feint_fail emitted
FT-03: Feint with no Bluff ranks → feint_invalid event; no marker
FT-04: consume_feint_marker returns True and removes marker
FT-05: Second consume_feint_marker returns False (already consumed)
FT-06: Feint marker used makes target deny Dex to AC (attack hits that would miss)
FT-07: FeintIntent costs standard action
FT-08: Feint marker expires at feinter's next turn (expire_feint_markers)
FT-09: feint_success event contains full roll breakdown
FT-10: parse_intent roundtrips FeintIntent
"""

import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.core.state import WorldState
from aidm.core.action_economy import ActionBudget, get_action_type, check_economy
from aidm.core.feint_resolver import (
    resolve_feint,
    consume_feint_marker,
    expire_feint_markers,
)
from aidm.schemas.intents import FeintIntent, parse_intent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(eid: str, team: str, hp: int = 20, ac: int = 12, bab: int = 3,
             skill_ranks: dict = None, cha_mod: int = 0, wis_mod: int = 0,
             dex_mod: int = 2, temporary_modifiers: dict = None) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
        EF.STR_MOD: 2,
        EF.DEX_MOD: dex_mod,
        EF.CHA_MOD: cha_mod,
        EF.WIS_MOD: wis_mod,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.SKILL_RANKS: skill_ranks or {},
        EF.TEMPORARY_MODIFIERS: temporary_modifiers or {},
    }


def _world(entities: dict, feint_markers: list = None) -> WorldState:
    combat: Dict[str, Any] = {"initiative_order": list(entities.keys())}
    if feint_markers is not None:
        combat["feint_flat_footed"] = feint_markers
    return WorldState(ruleset_version="3.5e", entities=entities, active_combat=combat)


def _rng(rolls) -> mock.MagicMock:
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [5] * 50
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# FT-01: Successful feint stores marker
# ---------------------------------------------------------------------------

def test_ft01_success_stores_marker():
    """When Bluff > SM+BAB, feint_flat_footed marker stored."""
    # Rogue: bluff 8 ranks, cha_mod 2 → Bluff mod = +10
    # Orc: SM 0, wis_mod 0, bab 2 → SM mod = +2
    # Rolls: rogue d20=15, orc d20=5 → 15+10=25 vs 5+2=7 → success
    rogue = _entity("rogue", "party", skill_ranks={"bluff": 8}, cha_mod=2)
    orc = _entity("orc", "enemy", bab=2, wis_mod=0)
    ws = _world({"rogue": rogue, "orc": orc})

    intent = FeintIntent(actor_id="rogue", target_id="orc")
    ws2, events, _ = resolve_feint(ws, intent, _rng([15, 5]), 0, 0.0)

    success = [e for e in events if e["event_type"] == "feint_success"]
    assert len(success) == 1

    markers = ws2.active_combat.get("feint_flat_footed", [])
    assert len(markers) == 1
    assert markers[0]["feinting_actor_id"] == "rogue"
    assert markers[0]["target_id"] == "orc"


# ---------------------------------------------------------------------------
# FT-02: Failed feint stores no marker
# ---------------------------------------------------------------------------

def test_ft02_fail_stores_no_marker():
    """When Bluff <= SM+BAB, feint_fail emitted and no marker stored."""
    # Rogue: bluff 2, cha 0 → +2
    # Orc: SM 5, wis 1, bab 3 → +9
    # Rolls: rogue d20=8, orc d20=5 → 8+2=10 vs 5+9=14 → fail (10 not > 14)
    rogue = _entity("rogue", "party", skill_ranks={"bluff": 2}, cha_mod=0)
    orc = _entity("orc", "enemy", bab=3, wis_mod=1, skill_ranks={"sense_motive": 5})
    ws = _world({"rogue": rogue, "orc": orc})

    intent = FeintIntent(actor_id="rogue", target_id="orc")
    ws2, events, _ = resolve_feint(ws, intent, _rng([8, 5]), 0, 0.0)

    fail = [e for e in events if e["event_type"] == "feint_fail"]
    assert len(fail) == 1
    assert ws2.active_combat.get("feint_flat_footed", []) == []


# ---------------------------------------------------------------------------
# FT-03: No Bluff ranks → feint_invalid
# ---------------------------------------------------------------------------

def test_ft03_no_bluff_ranks_invalid():
    """Actor with 0 Bluff ranks emits feint_invalid; no marker created."""
    rogue = _entity("rogue", "party", skill_ranks={})  # no bluff
    orc = _entity("orc", "enemy")
    ws = _world({"rogue": rogue, "orc": orc})

    intent = FeintIntent(actor_id="rogue", target_id="orc")
    ws2, events, _ = resolve_feint(ws, intent, _rng([15, 5]), 0, 0.0)

    invalid = [e for e in events if e["event_type"] == "feint_invalid"]
    assert len(invalid) == 1
    assert invalid[0]["payload"]["reason"] == "no_bluff_ranks"
    assert ws2.active_combat.get("feint_flat_footed", []) == []


# ---------------------------------------------------------------------------
# FT-04: consume_feint_marker returns True and removes marker
# ---------------------------------------------------------------------------

def test_ft04_consume_returns_true_removes_marker():
    """consume_feint_marker returns True and removes entry on first call."""
    markers = [{
        "feinting_actor_id": "rogue",
        "target_id": "orc",
        "registered_at_event_id": 5,
        "expires_at_actor_id": "rogue",
    }]
    ws = _world({"rogue": _entity("rogue", "party"), "orc": _entity("orc", "enemy")},
                feint_markers=markers)

    ws2, feint_active = consume_feint_marker(ws, "rogue", "orc")
    assert feint_active is True
    assert ws2.active_combat.get("feint_flat_footed", []) == []


# ---------------------------------------------------------------------------
# FT-05: Second consume returns False
# ---------------------------------------------------------------------------

def test_ft05_second_consume_returns_false():
    """After marker consumed, second consume returns False."""
    markers = [{
        "feinting_actor_id": "rogue",
        "target_id": "orc",
        "registered_at_event_id": 5,
        "expires_at_actor_id": "rogue",
    }]
    ws = _world({"rogue": _entity("rogue", "party"), "orc": _entity("orc", "enemy")},
                feint_markers=markers)

    ws2, _ = consume_feint_marker(ws, "rogue", "orc")
    ws3, feint_active = consume_feint_marker(ws2, "rogue", "orc")
    assert feint_active is False


# ---------------------------------------------------------------------------
# FT-06: Feint marker causes target to deny Dex to AC
# ---------------------------------------------------------------------------

def test_ft06_feint_marker_denies_dex_to_ac():
    """Attack that would miss non-feinted target hits feinted target."""
    from aidm.schemas.attack import AttackIntent, Weapon
    from aidm.core.attack_resolver import resolve_attack

    # Target AC 14 with dex_mod 4 → without Dex: AC 10, with Dex: AC 14
    markers = [{
        "feinting_actor_id": "rogue",
        "target_id": "orc",
        "registered_at_event_id": 5,
        "expires_at_actor_id": "rogue",
    }]
    rogue = _entity("rogue", "party", bab=4)
    orc = _entity("orc", "enemy", ac=10, dex_mod=4)  # effective AC normally 14
    # Manually set AC field to 14 (includes Dex)
    orc[EF.AC] = 14

    ws = _world({"rogue": rogue, "orc": orc}, feint_markers=markers)

    weapon = Weapon(
        damage_dice="1d6", damage_bonus=0, critical_range=19,
        critical_multiplier=2, grip="one-handed", damage_type="piercing",
        weapon_type="one-handed", range_increment=0, is_two_handed=False,
    )
    intent = AttackIntent(
        attacker_id="rogue", target_id="orc",
        attack_bonus=4, weapon=weapon, power_attack_penalty=0,
    )

    # d20=8, total = 8+4 = 12 < AC 14, but with feint Dex denied → effective AC 10 → hit
    stream = mock.MagicMock()
    stream.randint.side_effect = [8, 3]  # attack=8, damage=3
    rng = mock.MagicMock()
    rng.stream.return_value = stream

    events = resolve_attack(intent, ws, rng, 0, 0.0)
    attack_event = next(e for e in events if e.event_type == "attack_roll")
    assert attack_event.payload["feint_flat_footed"] is True
    assert attack_event.payload["hit"] is True  # 12 >= 10 (Dex denied)


# ---------------------------------------------------------------------------
# FT-07: FeintIntent costs standard action
# ---------------------------------------------------------------------------

def test_ft07_costs_standard_action():
    """get_action_type returns 'standard' for FeintIntent."""
    intent = FeintIntent(actor_id="rogue", target_id="orc")
    assert get_action_type(intent) == "standard"

    budget = ActionBudget(standard_used=True)
    denied = check_economy(intent, budget)
    assert denied == "standard"


# ---------------------------------------------------------------------------
# FT-08: Feint marker expires at feinter's next turn
# ---------------------------------------------------------------------------

def test_ft08_marker_expires_at_feinter_turn():
    """expire_feint_markers removes rogue's marker and emits feint_expired."""
    markers = [{
        "feinting_actor_id": "rogue",
        "target_id": "orc",
        "registered_at_event_id": 5,
        "expires_at_actor_id": "rogue",
    }]
    ws = _world({"rogue": _entity("rogue", "party"), "orc": _entity("orc", "enemy")},
                feint_markers=markers)

    ws2, events, _ = expire_feint_markers(ws, "rogue", 100, 1.0)

    expired = [e for e in events if e["event_type"] == "feint_expired"]
    assert len(expired) == 1
    assert expired[0]["payload"]["actor_id"] == "rogue"
    assert expired[0]["payload"]["target_id"] == "orc"
    assert ws2.active_combat.get("feint_flat_footed", []) == []


# ---------------------------------------------------------------------------
# FT-09: feint_success event contains full roll breakdown
# ---------------------------------------------------------------------------

def test_ft09_success_event_has_roll_breakdown():
    """feint_success payload includes bluff_d20, bluff_ranks, cha_mod, sm_d20, etc."""
    rogue = _entity("rogue", "party", skill_ranks={"bluff": 6}, cha_mod=2)
    orc = _entity("orc", "enemy", bab=2, wis_mod=0, skill_ranks={"sense_motive": 1})
    ws = _world({"rogue": rogue, "orc": orc})

    intent = FeintIntent(actor_id="rogue", target_id="orc")
    # Rolls: rogue d20=15, orc d20=3 → 15+6+2=23 vs 3+1+0+2=6 → success
    ws2, events, _ = resolve_feint(ws, intent, _rng([15, 3]), 0, 0.0)

    success = [e for e in events if e["event_type"] == "feint_success"][0]
    p = success["payload"]
    assert p["bluff_d20"] == 15
    assert p["bluff_ranks"] == 6
    assert p["cha_mod"] == 2
    assert p["bluff_roll"] == 23
    assert p["sm_d20"] == 3
    assert p["sense_motive_ranks"] == 1
    assert p["wis_mod"] == 0
    assert p["target_bab"] == 2
    assert p["sense_motive_roll"] == 6


# ---------------------------------------------------------------------------
# FT-10: parse_intent roundtrip
# ---------------------------------------------------------------------------

def test_ft10_parse_intent_roundtrip():
    """FeintIntent serializes and deserializes correctly."""
    intent = FeintIntent(actor_id="rogue", target_id="orc")
    d = intent.to_dict()
    restored = parse_intent(d)
    assert isinstance(restored, FeintIntent)
    assert restored.actor_id == "rogue"
    assert restored.target_id == "orc"
