"""
ENGINE GATE -- WO-ENGINE-COMBAT-EXPERTISE-001: Combat Expertise
Tests CEX-001 through CEX-008.
PHB p.92: Reduce attack by 1-5 to gain +1 dodge AC (penalty==1) or +2 dodge AC (penalty 2-5).
"""
from aidm.core.attack_resolver import resolve_attack
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


class _FixedRNG:
    class _Stream:
        def __init__(self, val):
            self._val = val
        def randint(self, lo, hi):
            return self._val
    def stream(self, name):
        if name == "combat":
            return _FixedRNG._Stream(15)
        return _FixedRNG._Stream(4)


def _make_ws(att, tgt):
    return WorldState(
        ruleset_version="3.5",
        entities={"att": att, "tgt": tgt},
        active_combat={"initiative_order": ["att", "tgt"],
                       "aoo_used_this_round": [], "aoo_count_this_round": {}},
    )


def _weapon():
    return Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing", weapon_type="one-handed")


def _attacker(feats=None, ce_bonus=0):
    return {
        EF.ENTITY_ID: "att", EF.TEAM: "player",
        EF.STR_MOD: 2, EF.DEX_MOD: 0,
        EF.FEATS: feats or [], EF.ATTACK_BONUS: 7,
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 15, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: [],
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.FAVORED_ENEMIES: [], EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.COMBAT_EXPERTISE_BONUS: ce_bonus,
    }


def _target(ac=10, ce_bonus=0):
    return {
        EF.ENTITY_ID: "tgt", EF.TEAM: "monsters",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: ac, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.FEATS: [],
        EF.COMBAT_EXPERTISE_BONUS: ce_bonus,
    }


def _get_ev(events):
    for e in events:
        if e.event_type == "attack_roll":
            return e
    return None


def test_cex001_penalty3_attack_reduced_by_3():
    att = _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=7, weapon=_weapon(),
        combat_expertise_penalty=3,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_FixedRNG(), next_event_id=0, timestamp=0.0)
    ev = _get_ev(events)
    assert ev is not None, "Should produce attack_roll event"
    # d20=15, attack_bonus=7, CE penalty=3 -> total = 15 + 7 - 3 = 19
    assert ev.payload["total"] == 19, "Expected total=19 got %r" % ev.payload["total"]


def test_cex002_penalty3_attacker_gets_bonus_2():
    att = _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=7, weapon=_weapon(),
        combat_expertise_penalty=3,
    )
    resolve_attack(intent=intent, world_state=ws, rng=_FixedRNG(), next_event_id=0, timestamp=0.0)
    ce_bonus = ws.entities["att"].get(EF.COMBAT_EXPERTISE_BONUS, 0)
    assert ce_bonus == 2, "Expected COMBAT_EXPERTISE_BONUS=2 got %r" % ce_bonus


def test_cex003_penalty1_attacker_gets_bonus_1():
    att = _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=7, weapon=_weapon(),
        combat_expertise_penalty=1,
    )
    resolve_attack(intent=intent, world_state=ws, rng=_FixedRNG(), next_event_id=0, timestamp=0.0)
    ce_bonus = ws.entities["att"].get(EF.COMBAT_EXPERTISE_BONUS, 0)
    assert ce_bonus == 1, "Expected COMBAT_EXPERTISE_BONUS=1 got %r" % ce_bonus


def test_cex004_penalty0_no_reduction_no_bonus():
    att = _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=7, weapon=_weapon(),
        combat_expertise_penalty=0,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_FixedRNG(), next_event_id=0, timestamp=0.0)
    ev = _get_ev(events)
    assert ev is not None
    # d20=15, attack_bonus=7, no penalty -> total=22
    assert ev.payload["total"] == 22, "Expected total=22 got %r" % ev.payload["total"]
    ce_bonus = ws.entities["att"].get(EF.COMBAT_EXPERTISE_BONUS, 0)
    assert ce_bonus == 0, "Expected no CE bonus got %r" % ce_bonus


def test_cex005_penalty5_attack_reduced_5_bonus_2():
    att = _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=7, weapon=_weapon(),
        combat_expertise_penalty=5,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_FixedRNG(), next_event_id=0, timestamp=0.0)
    ev = _get_ev(events)
    assert ev is not None
    # d20=15, attack_bonus=7, penalty=5 -> total = 15 + 7 - 5 = 17
    assert ev.payload["total"] == 17, "Expected total=17 got %r" % ev.payload["total"]
    ce_bonus = ws.entities["att"].get(EF.COMBAT_EXPERTISE_BONUS, 0)
    assert ce_bonus == 2, "Expected COMBAT_EXPERTISE_BONUS=2 (cap) got %r" % ce_bonus


def test_cex006_no_ce_declared_attack_unchanged():
    att = _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=7, weapon=_weapon(),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_FixedRNG(), next_event_id=0, timestamp=0.0)
    ev = _get_ev(events)
    assert ev is not None
    # d20=15, attack_bonus=7 -> total=22
    assert ev.payload["total"] == 22, "Expected total=22 got %r" % ev.payload["total"]


def test_cex007_target_with_ce_bonus_increases_target_ac():
    att = _attacker()
    tgt = _target(ac=10, ce_bonus=2)
    ws = _make_ws(att, tgt)
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=7, weapon=_weapon(),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_FixedRNG(), next_event_id=0, timestamp=0.0)
    ev = _get_ev(events)
    assert ev is not None, "Should produce attack_roll event"
    # target_ac should be 12 (base 10 + CE bonus 2)
    assert ev.payload["target_ac"] == 12, "Expected target_ac=12 got %r" % ev.payload["target_ac"]


def test_cex008_power_attack_still_works_alongside_ce():
    att = _attacker(feats=["power_attack"])
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=7, weapon=_weapon(),
        power_attack_penalty=4,
        combat_expertise_penalty=0,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_FixedRNG(), next_event_id=0, timestamp=0.0)
    assert len(events) > 0, "Power attack should produce events"
    ce_bonus = ws.entities["att"].get(EF.COMBAT_EXPERTISE_BONUS, 0)
    assert ce_bonus == 0, "No CE bonus should be set when CE penalty=0 got %r" % ce_bonus
    assert _get_ev(events) is not None, "Should produce attack_roll event"
