"""
ENGINE GATE -- WO-ENGINE-PRECISE-SHOT-001: Precise Shot
Tests PS-001 through PS-008.
PHB p.140/p.99: Ranged attack on target in melee with friendly → -4 penalty.
Precise Shot feat negates the -4 and emits precise_shot_active event.
"""
from aidm.core.attack_resolver import resolve_attack
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


class _SeqRNG:
    """Sequential RNG: returns values from list cycling."""
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


def _rng(attack=15, dmg=1):
    return _SeqRNG([attack, dmg])


def _ranged_weapon():
    return Weapon(damage_dice="1d8", damage_bonus=0, damage_type="piercing",
                  weapon_type="ranged", range_increment=30)


def _melee_weapon():
    return Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing",
                  weapon_type="one-handed")


def _entity(eid, team, pos, feats=None, bab=5, str_mod=0):
    return {
        EF.ENTITY_ID: eid, EF.TEAM: team,
        EF.FEATS: feats if feats is not None else [],
        EF.ATTACK_BONUS: bab + str_mod,
        EF.BAB: bab,
        EF.STR_MOD: str_mod, EF.DEX_MOD: 2,
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: 5, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: [],
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.FAVORED_ENEMIES: [], EF.TEMPORARY_MODIFIERS: {},
        EF.WEAPON: "shortbow",
        EF.POSITION: {"x": pos[0], "y": pos[1]},
    }


def _ws(entities_list):
    entities = {e[EF.ENTITY_ID]: e for e in entities_list}
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _get_ev(events, etype):
    for e in events:
        if e.event_type == etype:
            return e
    return None


# Layout for "target in melee" tests:
#   archer at (0,0) — ranged attacker
#   target at (2,0) — range > 1 from archer (ranged shot OK)
#   fighter at (2,1) — adjacent to target, SAME team as archer → target in melee
#
# Layout for "target NOT in melee":
#   archer at (0,0), target at (5,0) — no adjacent ally


# ---------------------------------------------------------------------------
# PS-001: Ranged, target in melee, HAS Precise Shot → no -4 penalty
# ---------------------------------------------------------------------------
def test_ps001_precise_shot_negates_penalty():
    """PS-001: Ranged + in melee + Precise Shot → total not reduced by -4."""
    archer = _entity("archer", "player", (0, 0), feats=["precise_shot"])
    target = _entity("target", "monster", (2, 0))
    fighter = _entity("fighter", "player", (2, 1))  # adjacent to target = in melee
    ws = _ws([archer, target, fighter])
    intent = AttackIntent(
        attacker_id="archer", target_id="target",
        attack_bonus=archer[EF.ATTACK_BONUS],
        weapon=_ranged_weapon(),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(15, 1),
                            next_event_id=0, timestamp=0.0)
    roll_ev = _get_ev(events, "attack_roll")
    assert roll_ev is not None, "PS-001: attack_roll missing"
    # With d20=15, attack_bonus=5: total should be 20, not 16 (no -4 penalty)
    assert roll_ev.payload["total"] == 15 + archer[EF.ATTACK_BONUS], (
        f"PS-001: Precise Shot should negate -4; total={roll_ev.payload['total']}")


# ---------------------------------------------------------------------------
# PS-002: Ranged, target in melee, NO Precise Shot → -4 applied
# ---------------------------------------------------------------------------
def test_ps002_no_precise_shot_minus4_applied():
    """PS-002: Ranged + in melee + no Precise Shot → total reduced by -4."""
    archer = _entity("archer", "player", (0, 0), feats=[])  # no precise_shot
    target = _entity("target", "monster", (2, 0))
    fighter = _entity("fighter", "player", (2, 1))
    ws = _ws([archer, target, fighter])
    intent = AttackIntent(
        attacker_id="archer", target_id="target",
        attack_bonus=archer[EF.ATTACK_BONUS],
        weapon=_ranged_weapon(),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(15, 1),
                            next_event_id=0, timestamp=0.0)
    roll_ev = _get_ev(events, "attack_roll")
    assert roll_ev is not None, "PS-002: attack_roll missing"
    expected_total = 15 + archer[EF.ATTACK_BONUS] - 4
    assert roll_ev.payload["total"] == expected_total, (
        f"PS-002: No Precise Shot → -4 penalty; expected total={expected_total}, "
        f"got {roll_ev.payload['total']}")


# ---------------------------------------------------------------------------
# PS-003: Ranged, target NOT in melee → no penalty regardless of feat
# ---------------------------------------------------------------------------
def test_ps003_target_not_in_melee_no_penalty():
    """PS-003: Ranged + no ally adjacent to target → no -4 regardless of feat."""
    archer = _entity("archer", "player", (0, 0), feats=[])
    target = _entity("target", "monster", (5, 0))  # far away, no adjacent ally
    ws = _ws([archer, target])
    intent = AttackIntent(
        attacker_id="archer", target_id="target",
        attack_bonus=archer[EF.ATTACK_BONUS],
        weapon=_ranged_weapon(),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(15, 1),
                            next_event_id=0, timestamp=0.0)
    roll_ev = _get_ev(events, "attack_roll")
    assert roll_ev is not None, "PS-003: attack_roll missing"
    expected_total = 15 + archer[EF.ATTACK_BONUS]
    assert roll_ev.payload["total"] == expected_total, (
        f"PS-003: No in-melee condition → no penalty; expected {expected_total}, "
        f"got {roll_ev.payload['total']}")


# ---------------------------------------------------------------------------
# PS-004: Melee attack, target in melee → Precise Shot irrelevant; no ranged penalty
# ---------------------------------------------------------------------------
def test_ps004_melee_attack_no_ranged_penalty():
    """PS-004: Melee attack never gets ranged-into-melee penalty."""
    fighter = _entity("fighter", "player", (0, 0), feats=[])
    target = _entity("target", "monster", (1, 0))
    ally = _entity("ally", "player", (1, 1))  # adjacent to target, in melee
    ws = _ws([fighter, target, ally])
    intent = AttackIntent(
        attacker_id="fighter", target_id="target",
        attack_bonus=fighter[EF.ATTACK_BONUS],
        weapon=_melee_weapon(),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(15, 1),
                            next_event_id=0, timestamp=0.0)
    roll_ev = _get_ev(events, "attack_roll")
    assert roll_ev is not None, "PS-004: attack_roll missing"
    expected_total = 15 + fighter[EF.ATTACK_BONUS]
    assert roll_ev.payload["total"] == expected_total, (
        f"PS-004: Melee attack should not get -4; expected {expected_total}, "
        f"got {roll_ev.payload['total']}")


# ---------------------------------------------------------------------------
# PS-005: Precise Shot active → precise_shot_active event emitted
# ---------------------------------------------------------------------------
def test_ps005_precise_shot_active_event_emitted():
    """PS-005: precise_shot_active event emitted when Precise Shot negates penalty."""
    archer = _entity("archer", "player", (0, 0), feats=["precise_shot"])
    target = _entity("target", "monster", (2, 0))
    fighter = _entity("fighter", "player", (2, 1))  # in melee
    ws = _ws([archer, target, fighter])
    intent = AttackIntent(
        attacker_id="archer", target_id="target",
        attack_bonus=archer[EF.ATTACK_BONUS],
        weapon=_ranged_weapon(),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(15, 1),
                            next_event_id=0, timestamp=0.0)
    ps_ev = _get_ev(events, "precise_shot_active")
    assert ps_ev is not None, "PS-005: precise_shot_active event missing"
    assert ps_ev.payload["actor_id"] == "archer", (
        f"PS-005: actor_id should be 'archer'; got {ps_ev.payload.get('actor_id')}")


# ---------------------------------------------------------------------------
# PS-006: Precise Shot + Point Blank Shot → PBShot +1 bonus unaffected; both apply
# ---------------------------------------------------------------------------
def test_ps006_precise_shot_plus_point_blank_shot():
    """PS-006: Both Precise Shot and Point Blank Shot active; PBS +1 still applies."""
    # archer at (0,0), target at (1,0) — range ≤ 30 ft for PBS; fighter at (1,1) for in-melee
    archer = _entity("archer", "player", (0, 0),
                     feats=["precise_shot", "point_blank_shot"])
    target = _entity("target", "monster", (1, 0))
    fighter = _entity("fighter", "player", (1, 1))
    ws = _ws([archer, target, fighter])
    intent = AttackIntent(
        attacker_id="archer", target_id="target",
        attack_bonus=archer[EF.ATTACK_BONUS],
        weapon=_ranged_weapon(),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(10, 1),
                            next_event_id=0, timestamp=0.0)
    roll_ev = _get_ev(events, "attack_roll")
    assert roll_ev is not None, "PS-006: attack_roll missing"
    # feat_modifier should include PBS +1 (in 30 ft) and no -4 (Precise Shot active)
    # PBS is applied by get_attack_modifier via feat_resolver → feat_modifier = +1
    assert roll_ev.payload["feat_modifier"] == 1, (
        f"PS-006: feat_modifier should be +1 (PBS +1, no -4); got {roll_ev.payload['feat_modifier']}")
    # No penalty, so no -4 reduction in total
    ps_ev = _get_ev(events, "precise_shot_active")
    assert ps_ev is not None, "PS-006: precise_shot_active event should still be emitted"


# ---------------------------------------------------------------------------
# PS-007: Full-attack: second iterative attack also has no -4 (feat covers round)
# ---------------------------------------------------------------------------
def test_ps007_iterative_attacks_no_penalty_with_feat():
    """PS-007: Two ranged attacks with Precise Shot — neither gets -4."""
    archer = _entity("archer", "player", (0, 0), feats=["precise_shot"], bab=11)
    target = _entity("target", "monster", (2, 0))
    fighter = _entity("fighter", "player", (2, 1))
    ws = _ws([archer, target, fighter])

    intent1 = AttackIntent(
        attacker_id="archer", target_id="target",
        attack_bonus=archer[EF.ATTACK_BONUS],
        weapon=_ranged_weapon(),
    )
    intent2 = AttackIntent(
        attacker_id="archer", target_id="target",
        attack_bonus=archer[EF.ATTACK_BONUS] - 5,  # iterative
        weapon=_ranged_weapon(),
    )

    events1 = resolve_attack(intent=intent1, world_state=ws, rng=_rng(15, 1),
                             next_event_id=0, timestamp=0.0)
    events2 = resolve_attack(intent=intent2, world_state=ws, rng=_rng(15, 1),
                             next_event_id=0, timestamp=0.1)

    roll1 = _get_ev(events1, "attack_roll")
    roll2 = _get_ev(events2, "attack_roll")
    expected1 = 15 + archer[EF.ATTACK_BONUS]
    expected2 = 15 + archer[EF.ATTACK_BONUS] - 5
    assert roll1 is not None and roll1.payload["total"] == expected1, \
        f"PS-007: first attack total wrong; expected {expected1}, got {roll1 and roll1.payload.get('total')}"
    assert roll2 is not None and roll2.payload["total"] == expected2, \
        f"PS-007: iterative attack total wrong; expected {expected2}, got {roll2 and roll2.payload.get('total')}"


# ---------------------------------------------------------------------------
# PS-008: Regression — non-Precise-Shot actor still gets -4 into melee (after WO1/PA commit)
# ---------------------------------------------------------------------------
def test_ps008_regression_no_feat_still_penalized():
    """PS-008: After WO1 (PA) commit, attacker without Precise Shot still gets -4 into melee."""
    archer = _entity("archer", "player", (0, 0), feats=["power_attack"])  # has PA, not PS
    target = _entity("target", "monster", (2, 0))
    fighter = _entity("fighter", "player", (2, 1))
    ws = _ws([archer, target, fighter])
    intent = AttackIntent(
        attacker_id="archer", target_id="target",
        attack_bonus=archer[EF.ATTACK_BONUS],
        weapon=_ranged_weapon(),
        power_attack_penalty=0,  # PA not used on ranged
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng(15, 1),
                            next_event_id=0, timestamp=0.0)
    roll_ev = _get_ev(events, "attack_roll")
    assert roll_ev is not None, "PS-008: attack_roll missing"
    expected_total = 15 + archer[EF.ATTACK_BONUS] - 4
    assert roll_ev.payload["total"] == expected_total, (
        f"PS-008: Power Attack actor (no PS) should still get -4 into melee; "
        f"expected {expected_total}, got {roll_ev.payload['total']}")
