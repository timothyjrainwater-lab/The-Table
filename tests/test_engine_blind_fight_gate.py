"""
ENGINE GATE -- WO-ENGINE-BLIND-FIGHT-001: Blind-Fight feat
Tests BF-001 through BF-008.
PHB p.91: On a concealment miss, attacker with Blind-Fight may reroll d100 once.
Miss chance resolution site: attack_resolver.py WO-049 block.
Scope: miss-chance reroll only. FINDING-ENGINE-BLIND-FIGHT-INVIS-001 filed (LOW).
"""
import pytest
from aidm.core.attack_resolver import resolve_attack
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# RNG that returns a fixed d20 (always hit) then fixed d100 values in sequence
class _SequenceRNG:
    """Return d20=19 (always hit), then d100 values from sequence."""
    class _Stream:
        def __init__(self, vals):
            self._vals = list(vals)
            self._idx = 0
        def randint(self, lo, hi):
            v = self._vals[self._idx % len(self._vals)]
            self._idx += 1
            return v

    def __init__(self, d20=19, d100_vals=None):
        self._d20 = d20
        self._d100 = d100_vals or [50]
        self._calls = 0

    def stream(self, name):
        # Combat stream: first call → d20 (attack roll), subsequent → d100 (miss chance)
        outer = self
        class _MixedStream:
            def __init__(self):
                self._call = 0
            def randint(self, lo, hi):
                if hi == 20:
                    # d20 roll
                    return outer._d20
                elif hi == 6:
                    # damage die
                    return 4
                elif hi == 100:
                    # miss chance roll — pull from d100 sequence
                    val = outer._d100[outer._calls % len(outer._d100)]
                    outer._calls += 1
                    return val
                return 4
        return _MixedStream()


def _make_ws(att, tgt):
    """World state — concealment set via EF.MISS_CHANCE on target entity."""
    return WorldState(
        ruleset_version="3.5",
        entities={"att": att, "tgt": tgt},
        active_combat={
            "initiative_order": ["att", "tgt"],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _attacker(feats=None):
    return {
        EF.ENTITY_ID: "att", EF.TEAM: "player",
        EF.STR_MOD: 2, EF.DEX_MOD: 1,
        EF.FEATS: feats or [],
        EF.ATTACK_BONUS: 7,
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 15, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: {},
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.FAVORED_ENEMIES: [], EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.COMBAT_EXPERTISE_BONUS: 0,
    }


def _target(ac=8, miss_chance=50):
    e = {
        EF.ENTITY_ID: "tgt", EF.TEAM: "monsters",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: ac, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: {},
        EF.POSITION: {"x": 1, "y": 0},
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.FEATS: [],
        EF.COMBAT_EXPERTISE_BONUS: 0,
    }
    if miss_chance > 0:
        e[EF.MISS_CHANCE] = miss_chance
    return e


def _weapon():
    return Weapon(damage_dice="1d6", damage_bonus=0, damage_type="slashing", weapon_type="one-handed")


def _get_ev(events, ev_type):
    return next((e for e in events if e.event_type == ev_type), None)


def _has_ev(events, ev_type):
    return any(e.event_type == ev_type for e in events)


# ── BF-001: Blind-Fight feat → reroll triggers on initial miss (seeded RNG) ──────────────

def test_bf001_blind_fight_reroll_triggers_on_initial_miss():
    """With Blind-Fight, when the first d100 roll is a miss, blind_fight_reroll event fires."""
    att = _attacker(feats=["blind_fight"])
    # First d100=30 → miss (30 <= 50%); reroll=60 → hit (60 > 50%)
    rng = _SequenceRNG(d20=19, d100_vals=[30, 60])
    ws = _make_ws(att, _target(miss_chance=50))
    intent = AttackIntent(attacker_id="att", target_id="tgt", attack_bonus=7, weapon=_weapon())
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)
    assert _has_ev(events, "blind_fight_reroll"), "blind_fight_reroll must fire on initial miss with feat"


# ── BF-002: Reroll succeeds → attack proceeds past concealment ────────────────────────────

def test_bf002_reroll_success_attack_proceeds():
    """When reroll beats miss chance, concealment_miss NOT emitted; damage rolls."""
    att = _attacker(feats=["blind_fight"])
    # First d100=30 → miss; reroll=80 → hit (beat 50%)
    rng = _SequenceRNG(d20=19, d100_vals=[30, 80])
    ws = _make_ws(att, _target(miss_chance=50))
    intent = AttackIntent(attacker_id="att", target_id="tgt", attack_bonus=7, weapon=_weapon())
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)
    assert not _has_ev(events, "concealment_miss"), "concealment_miss must NOT fire when reroll succeeds"
    assert _has_ev(events, "blind_fight_reroll"), "blind_fight_reroll must be present"
    # Check that damage/hp change event followed (attack didn't miss)
    assert _has_ev(events, "hp_changed") or _has_ev(events, "damage_roll"), (
        "Damage must resolve after successful reroll"
    )


# ── BF-003: Both rolls fail → attack misses ──────────────────────────────────────────────

def test_bf003_both_rolls_fail_attack_misses():
    """When both d100 rolls are misses, concealment_miss is emitted."""
    att = _attacker(feats=["blind_fight"])
    # First d100=30 → miss; reroll=20 → also miss
    rng = _SequenceRNG(d20=19, d100_vals=[30, 20])
    ws = _make_ws(att, _target(miss_chance=50))
    intent = AttackIntent(attacker_id="att", target_id="tgt", attack_bonus=7, weapon=_weapon())
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)
    assert _has_ev(events, "concealment_miss"), "Both rolls miss → concealment_miss must fire"
    assert not _has_ev(events, "hp_changed"), "No damage when both rolls fail"


# ── BF-004: No Blind-Fight feat → no reroll on miss ─────────────────────────────────────

def test_bf004_no_feat_no_reroll():
    """Without Blind-Fight, concealment miss stands; no reroll event."""
    att = _attacker(feats=[])
    # d100=30 → miss (no reroll available)
    rng = _SequenceRNG(d20=19, d100_vals=[30, 80])  # second val irrelevant
    ws = _make_ws(att, _target(miss_chance=50))
    intent = AttackIntent(attacker_id="att", target_id="tgt", attack_bonus=7, weapon=_weapon())
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)
    assert not _has_ev(events, "blind_fight_reroll"), "No reroll without Blind-Fight feat"
    assert _has_ev(events, "concealment_miss"), "Miss stands without feat"


# ── BF-005: 20% miss chance — reroll fires on miss ───────────────────────────────────────

def test_bf005_20pct_miss_chance_reroll_fires():
    """Partial concealment (20% miss): reroll triggers on initial miss."""
    att = _attacker(feats=["blind_fight"])
    # d100=15 → miss (15 <= 20%); reroll=50 → hit (50 > 20%)
    rng = _SequenceRNG(d20=19, d100_vals=[15, 50])
    ws = _make_ws(att, _target(miss_chance=20))
    intent = AttackIntent(attacker_id="att", target_id="tgt", attack_bonus=7, weapon=_weapon())
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)
    assert _has_ev(events, "blind_fight_reroll"), "Reroll fires even with 20% miss chance"


# ── BF-006: 50% miss chance — reroll fires on miss ───────────────────────────────────────

def test_bf006_50pct_miss_chance_reroll_fires():
    """Full concealment (50% miss): reroll triggers on initial miss."""
    att = _attacker(feats=["blind_fight"])
    rng = _SequenceRNG(d20=19, d100_vals=[25, 75])
    ws = _make_ws(att, _target(miss_chance=50))
    intent = AttackIntent(attacker_id="att", target_id="tgt", attack_bonus=7, weapon=_weapon())
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)
    assert _has_ev(events, "blind_fight_reroll"), "Reroll fires with 50% miss chance"


# ── BF-007: Miss chance = 0 → no reroll triggered ────────────────────────────────────────

def test_bf007_no_miss_chance_no_reroll():
    """When miss_chance=0, no reroll is ever triggered regardless of feat."""
    att = _attacker(feats=["blind_fight"])
    rng = _SequenceRNG(d20=19, d100_vals=[30, 80])
    ws = _make_ws(att, _target(miss_chance=0))
    intent = AttackIntent(attacker_id="att", target_id="tgt", attack_bonus=7, weapon=_weapon())
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)
    assert not _has_ev(events, "blind_fight_reroll"), "No reroll when miss_chance=0"
    assert not _has_ev(events, "concealment_miss"), "No concealment miss when miss_chance=0"


# ── BF-008: Event sequence — blind_fight_reroll before hit/miss resolution ────────────────

def test_bf008_event_sequence_reroll_before_miss_or_damage():
    """blind_fight_reroll event appears before concealment_miss or damage events."""
    att = _attacker(feats=["blind_fight"])
    # Both rolls miss — so blind_fight_reroll is followed by concealment_miss
    rng = _SequenceRNG(d20=19, d100_vals=[30, 20])
    ws = _make_ws(att, _target(miss_chance=50))
    intent = AttackIntent(attacker_id="att", target_id="tgt", attack_bonus=7, weapon=_weapon())
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)
    types = [e.event_type for e in events]
    assert "blind_fight_reroll" in types, "blind_fight_reroll must be present"
    assert "concealment_miss" in types, "concealment_miss must be present"
    bf_idx = types.index("blind_fight_reroll")
    cm_idx = types.index("concealment_miss")
    assert bf_idx < cm_idx, "blind_fight_reroll must precede concealment_miss in event list"
