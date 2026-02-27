"""
ENGINE GATE -- WO-ENGINE-POWER-ATTACK-001: Power Attack
Tests PA-001 through PA-008.
PHB p.98: Subtract up to BAB from attack rolls; gain equal bonus to damage.
Two-handed: damage bonus = 2× penalty (PHB p.98). Off-hand: floor(N * 0.5).
"""
from aidm.core.attack_resolver import resolve_attack
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


class _SeqRNG:
    """Sequenced fake RNG: returns values from a queue on each randint call."""
    def __init__(self, values):
        self._vals = list(values)
        self._idx = 0

    class _Stream:
        def __init__(self, parent):
            self._p = parent
        def randint(self, lo, hi):
            val = self._p._vals[self._p._idx % len(self._p._vals)]
            self._p._idx += 1
            return val

    def stream(self, name):
        return _SeqRNG._Stream(self)


def _rng(attack_roll=10, damage_roll=1):
    """Return RNG that yields attack_roll then damage_roll repeatedly."""
    return _SeqRNG([attack_roll, damage_roll])


def _make_ws(att, tgt):
    return WorldState(
        ruleset_version="3.5",
        entities={"att": att, "tgt": tgt},
        active_combat={
            "initiative_order": ["att", "tgt"],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _attacker(feats=None, bab=6, str_mod=2):
    return {
        EF.ENTITY_ID: "att", EF.TEAM: "player",
        EF.STR_MOD: str_mod, EF.DEX_MOD: 0,
        EF.FEATS: feats if feats is not None else ["power_attack"],
        EF.BAB: bab,
        EF.ATTACK_BONUS: bab + str_mod,
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: 15, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: [],
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.FAVORED_ENEMIES: [], EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.WEAPON: "longsword",
    }


def _target(ac=5):
    """Low AC so d20+bonus always hits without complication."""
    return {
        EF.ENTITY_ID: "tgt", EF.TEAM: "monsters",
        EF.HP_CURRENT: 100, EF.HP_MAX: 100, EF.AC: ac, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: [],
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
    }


def _one_handed():
    return Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing",
                  weapon_type="one-handed")


def _two_handed():
    return Weapon(damage_dice="2d6", damage_bonus=0, damage_type="slashing",
                  weapon_type="two-handed", is_two_handed=True)


def _offhand():
    return Weapon(damage_dice="1d6", damage_bonus=0, damage_type="slashing",
                  weapon_type="light", grip="off-hand")


def _get_event(events, event_type):
    for e in events:
        if e.event_type == event_type:
            return e
    return None


# ---------------------------------------------------------------------------
# PA-001: PA=2, 1H weapon, BAB=6 → attack roll -2, damage +2
# ---------------------------------------------------------------------------
def test_pa001_one_handed_attack_minus2_damage_plus2():
    """PA-001: PA=2, 1H weapon → attack feat_modifier=-2, damage feat_modifier=+2."""
    att = _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=att[EF.ATTACK_BONUS],
        weapon=_one_handed(),
        power_attack_penalty=2,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(10, 1),
                            next_event_id=0, timestamp=0.0)
    roll_ev = _get_event(events, "attack_roll")
    dmg_ev = _get_event(events, "damage_roll")
    assert roll_ev is not None, "Should emit attack_roll"
    assert roll_ev.payload["feat_modifier"] == -2, (
        f"Attack feat_modifier should be -2 (PA penalty); got {roll_ev.payload['feat_modifier']}")
    assert dmg_ev is not None, "Should emit damage_roll"
    assert dmg_ev.payload["feat_modifier"] == 2, (
        f"Damage feat_modifier should be +2 (1H PA bonus); got {dmg_ev.payload['feat_modifier']}")


# ---------------------------------------------------------------------------
# PA-002: PA=2, 2H weapon → damage +4 (2×2=4, PHB p.98)
# ---------------------------------------------------------------------------
def test_pa002_two_handed_damage_plus4():
    """PA-002: PA=2, 2H weapon → damage feat_modifier=+4 (2*2, PHB p.98)."""
    att = _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=att[EF.ATTACK_BONUS],
        weapon=_two_handed(),
        power_attack_penalty=2,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(10, 1),
                            next_event_id=0, timestamp=0.0)
    dmg_ev = _get_event(events, "damage_roll")
    assert dmg_ev is not None, "Should emit damage_roll"
    assert dmg_ev.payload["feat_modifier"] == 4, (
        f"2H PA=2 → feat_modifier should be 4 (2*2, PHB p.98); got {dmg_ev.payload['feat_modifier']}")


# ---------------------------------------------------------------------------
# PA-003: PA=2, off-hand weapon (TWF) → damage +1 (floor(2×0.5)=1)
# ---------------------------------------------------------------------------
def test_pa003_offhand_damage_plus1():
    """PA-003: PA=2, off-hand (grip='off-hand') → damage feat_modifier=+1 (floor(2*0.5))."""
    att = _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=att[EF.ATTACK_BONUS],
        weapon=_offhand(),
        power_attack_penalty=2,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(10, 1),
                            next_event_id=0, timestamp=0.0)
    dmg_ev = _get_event(events, "damage_roll")
    assert dmg_ev is not None, "Should emit damage_roll"
    assert dmg_ev.payload["feat_modifier"] == 1, (
        f"Off-hand PA=2 → feat_modifier should be 1 (floor(2*0.5)); got {dmg_ev.payload['feat_modifier']}")


# ---------------------------------------------------------------------------
# PA-004: PA=N where N > BAB (BAB=2, declare PA=3) → validation_failed
# ---------------------------------------------------------------------------
def test_pa004_penalty_exceeds_bab_validation_failed():
    """PA-004: PA=3 with BAB=2 → intent_validation_failed reason=penalty_exceeds_bab."""
    att = _attacker(bab=2, str_mod=0)
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=att[EF.ATTACK_BONUS],
        weapon=_one_handed(),
        power_attack_penalty=3,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(),
                            next_event_id=0, timestamp=0.0)
    fail_ev = _get_event(events, "intent_validation_failed")
    assert fail_ev is not None, "Should emit intent_validation_failed when PA > BAB"
    assert fail_ev.payload["reason"] == "penalty_exceeds_bab", (
        f"Expected reason='penalty_exceeds_bab'; got {fail_ev.payload.get('reason')}")
    assert _get_event(events, "attack_roll") is None, "No attack_roll after validation failure"


# ---------------------------------------------------------------------------
# PA-005: PA=0 declared → no effect
# ---------------------------------------------------------------------------
def test_pa005_penalty_zero_no_effect():
    """PA-005: PA=0 → no validation_failed, feat_modifier=0 on attack and damage."""
    att = _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=att[EF.ATTACK_BONUS],
        weapon=_one_handed(),
        power_attack_penalty=0,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(10, 1),
                            next_event_id=0, timestamp=0.0)
    assert _get_event(events, "intent_validation_failed") is None, \
        "PA=0 should not trigger validation_failed"
    roll_ev = _get_event(events, "attack_roll")
    assert roll_ev is not None, "Should emit attack_roll"
    assert roll_ev.payload["feat_modifier"] == 0, \
        f"PA=0 → feat_modifier on attack should be 0; got {roll_ev.payload['feat_modifier']}"


# ---------------------------------------------------------------------------
# PA-006: Actor without Power Attack feat, PA=2 → validation_failed
# ---------------------------------------------------------------------------
def test_pa006_no_feat_validation_failed():
    """PA-006: No power_attack feat, PA=2 → intent_validation_failed reason=feat_requirement_not_met."""
    att = _attacker(feats=[])  # No power_attack feat
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=att[EF.ATTACK_BONUS],
        weapon=_one_handed(),
        power_attack_penalty=2,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(),
                            next_event_id=0, timestamp=0.0)
    fail_ev = _get_event(events, "intent_validation_failed")
    assert fail_ev is not None, "Should emit intent_validation_failed without feat"
    assert fail_ev.payload["reason"] == "feat_requirement_not_met", (
        f"Expected reason='feat_requirement_not_met'; got {fail_ev.payload.get('reason')}")
    assert fail_ev.payload["feat"] == "power_attack", (
        f"Expected feat='power_attack'; got {fail_ev.payload.get('feat')}")
    assert _get_event(events, "attack_roll") is None, "No attack_roll after validation failure"


# ---------------------------------------------------------------------------
# PA-007: Full attack with PA=3 → all iterative attacks have -3 penalty
# ---------------------------------------------------------------------------
def test_pa007_iterative_attacks_all_penalized():
    """PA-007: Two separate resolve_attack calls with PA=3 both show feat_modifier=-3."""
    att = _attacker(bab=11)  # High enough BAB for iterative attacks
    ws = _make_ws(att, _target())

    intent1 = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=att[EF.ATTACK_BONUS],
        weapon=_one_handed(),
        power_attack_penalty=3,
    )
    intent2 = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=att[EF.ATTACK_BONUS] - 5,  # Iterative -5 penalty
        weapon=_one_handed(),
        power_attack_penalty=3,
    )

    events1 = resolve_attack(intent=intent1, world_state=ws, rng=_rng(10, 1),
                             next_event_id=0, timestamp=0.0)
    events2 = resolve_attack(intent=intent2, world_state=ws, rng=_rng(10, 1),
                             next_event_id=0, timestamp=0.1)

    roll1 = _get_event(events1, "attack_roll")
    roll2 = _get_event(events2, "attack_roll")
    assert roll1 is not None and roll2 is not None, "Both attacks should produce attack_roll events"
    assert roll1.payload["feat_modifier"] == -3, \
        f"First attack feat_modifier should be -3; got {roll1.payload['feat_modifier']}"
    assert roll2.payload["feat_modifier"] == -3, \
        f"Second iterative attack feat_modifier should be -3; got {roll2.payload['feat_modifier']}"


# ---------------------------------------------------------------------------
# PA-008: PA bonus stacks with Weapon Focus (+1) — net roll and damage correct
# ---------------------------------------------------------------------------
def test_pa008_stacks_with_weapon_focus():
    """PA-008: PA=2 + Weapon Focus +1 → attack feat_modifier=-1 (net), damage feat_modifier=+2."""
    att = _attacker(feats=["power_attack", "weapon_focus_longsword"])
    # EF.WEAPON = "longsword" is already set in _attacker()
    ws = _make_ws(att, _target())
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=att[EF.ATTACK_BONUS],
        weapon=_one_handed(),
        power_attack_penalty=2,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(10, 1),
                            next_event_id=0, timestamp=0.0)
    roll_ev = _get_event(events, "attack_roll")
    dmg_ev = _get_event(events, "damage_roll")
    assert roll_ev is not None, "Should emit attack_roll"
    # PA -2 + Weapon Focus +1 = -1 net
    assert roll_ev.payload["feat_modifier"] == -1, (
        f"PA=2 + WF +1 → net feat_modifier should be -1; got {roll_ev.payload['feat_modifier']}")
    assert dmg_ev is not None, "Should emit damage_roll"
    assert dmg_ev.payload["feat_modifier"] == 2, (
        f"1H PA=2 damage feat_modifier should be +2; got {dmg_ev.payload['feat_modifier']}")
