"""Gate tests: ENGINE-IMPROVED-CRITICAL-001

Improved Critical feat (PHB p.96): doubles threat range for selected weapon.
Formula: effective_range = 21 - (21 - base_range) * 2
Examples: base 20 → 19, base 19 → 17, base 18 → 15.

WO-ENGINE-IMPROVED-CRITICAL-001, Batch K (Dispatch #20).
Gate labels: IC-001 through IC-008.
"""

import pytest

from aidm.core.full_attack_resolver import resolve_single_attack_with_critical
from aidm.schemas.attack import Weapon
from aidm.schemas.entity_fields import EF


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

class _FixedRNG:
    """Deterministic RNG: first roll returns `attack_roll`, subsequent rolls return `confirm_roll`."""

    class _Stream:
        def __init__(self, values):
            self._values = iter(values)
            self._last = 15

        def randint(self, lo, hi):
            try:
                v = next(self._values)
                self._last = v
                return v
            except StopIteration:
                return self._last

    def __init__(self, attack_roll, confirm_roll=15, damage_roll=6):
        self._stream = _FixedRNG._Stream([attack_roll, confirm_roll, damage_roll])

    def stream(self, name):
        return self._stream


def _longsword():
    """Longsword: 1d8, critical_range=19 (19-20 threatens), one-handed."""
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="slashing",
        critical_range=19,
        critical_multiplier=2,
        weapon_type="one-handed",
    )


def _rapier():
    """Rapier: 1d6, critical_range=18 (18-20 threatens), light weapon."""
    return Weapon(
        damage_dice="1d6",
        damage_bonus=0,
        damage_type="piercing",
        critical_range=18,
        critical_multiplier=2,
        weapon_type="light",
    )


def _dagger():
    """Dagger: 1d4, critical_range=19 (19-20 threatens), light weapon."""
    return Weapon(
        damage_dice="1d4",
        damage_bonus=0,
        damage_type="piercing",
        critical_range=19,
        critical_multiplier=2,
        weapon_type="light",
    )


def _standard_weapon():
    """Standard weapon: 1d8, critical_range=20 (20 only threatens)."""
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="bludgeoning",
        critical_range=20,
        critical_multiplier=2,
        weapon_type="one-handed",
    )


def _run_attack(d20_roll, weapon, feats=None, target_ac=5, confirm_roll=15):
    """Run resolve_single_attack_with_critical with fixed rolls; return events."""
    rng = _FixedRNG(attack_roll=d20_roll, confirm_roll=confirm_roll, damage_roll=4)
    events, new_eid, damage = resolve_single_attack_with_critical(
        attacker_id="att",
        target_id="tgt",
        attack_bonus=10,  # High bonus; almost always hits
        weapon=weapon,
        target_ac=target_ac,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
        attack_index=0,
        attacker_feats=feats or [],
    )
    return events


def _is_threat(events):
    """Return True if any attack_roll event has is_threat=True."""
    for e in events:
        if e.event_type == "attack_roll" and e.payload.get("is_threat"):
            return True
    return False


def _is_critical(events):
    """Return True if any attack_roll or critical_hit event confirms a crit."""
    for e in events:
        if e.event_type == "critical_hit":
            return True
        if e.event_type == "attack_roll" and e.payload.get("is_critical"):
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestImprovedCritical001Gate:

    def test_IC001_improved_critical_longsword_roll17_is_threat(self):
        """IC-001: Attacker with Improved Critical (longsword, base 19) rolls 17 → threat.
        Effective range = 21 - (21-19)*2 = 17."""
        weapon = _longsword()  # base_range=19 → effective 17 with IC
        events = _run_attack(
            d20_roll=17,
            weapon=weapon,
            feats=["improved_critical"],
            confirm_roll=20,
        )
        assert _is_threat(events), \
            f"Expected roll=17 to be a threat with Improved Critical (longsword, eff=17); events={[e.event_type for e in events]}"

    def test_IC002_improved_critical_longsword_roll18_was_not_without_feat(self):
        """IC-002: With IC feat roll=18 is threat; without IC feat roll=18 is threat at base 19 → NOT a threat.
        Regression check: base=19 means roll=18 is NOT a threat without IC."""
        weapon = _longsword()  # base_range=19 → roll=18 NOT threat without IC
        events_without = _run_attack(d20_roll=18, weapon=weapon, feats=[], confirm_roll=20)
        events_with = _run_attack(d20_roll=18, weapon=weapon, feats=["improved_critical"], confirm_roll=20)

        assert not _is_threat(events_without), \
            "Roll=18 should NOT be threat with base range=19 (without IC)"
        assert _is_threat(events_with), \
            "Roll=18 SHOULD be threat with IC (longsword eff range=17)"

    def test_IC003_without_improved_critical_longsword_roll18_no_threat(self):
        """IC-003: Attacker WITHOUT Improved Critical (longsword, base 19) rolls 18 → NOT a threat."""
        weapon = _longsword()
        events = _run_attack(d20_roll=18, weapon=weapon, feats=[], confirm_roll=20)
        assert not _is_threat(events), \
            "Roll=18 must NOT be threat without IC (longsword base range=19)"

    def test_IC004_improved_critical_standard_weapon_roll19_is_threat(self):
        """IC-004: Attacker with Improved Critical (standard weapon, base 20) rolls 19 → threat.
        Effective range = 21 - (21-20)*2 = 19."""
        weapon = _standard_weapon()  # base_range=20 → effective 19 with IC
        events = _run_attack(d20_roll=19, weapon=weapon, feats=["improved_critical"], confirm_roll=20)
        assert _is_threat(events), \
            f"Roll=19 should be threat with IC (standard weapon, eff=19); events={[e.event_type for e in events]}"

    def test_IC005_improved_critical_rapier_roll15_is_threat(self):
        """IC-005: Attacker with Improved Critical (rapier, base 18) rolls 15 → threat.
        Effective range = 21 - (21-18)*2 = 15."""
        weapon = _rapier()  # base_range=18 → effective 15 with IC
        events = _run_attack(d20_roll=15, weapon=weapon, feats=["improved_critical"], confirm_roll=20)
        assert _is_threat(events), \
            f"Roll=15 should be threat with IC (rapier, eff=15)"

    def test_IC006_without_improved_critical_rapier_roll15_no_threat(self):
        """IC-006: Attacker WITHOUT Improved Critical (rapier, base 18) rolls 15 → NOT a threat."""
        weapon = _rapier()
        events = _run_attack(d20_roll=15, weapon=weapon, feats=[], confirm_roll=20)
        assert not _is_threat(events), \
            "Roll=15 must NOT be threat without IC (rapier base range=18)"

    def test_IC007_formula_validation(self):
        """IC-007: Formula validation: base 18 → effective 15; base 19 → 17; base 20 → 19."""
        def _apply(base):
            return max(1, 21 - (21 - base) * 2)

        assert _apply(18) == 15, f"Expected 15 for base=18, got {_apply(18)}"
        assert _apply(19) == 17, f"Expected 17 for base=19, got {_apply(19)}"
        assert _apply(20) == 19, f"Expected 19 for base=20, got {_apply(20)}"
        assert _apply(17) == 13, f"Expected 13 for base=17, got {_apply(17)}"

    def test_IC008_improved_critical_full_crit_confirmation(self):
        """IC-008: Attacker with IC; longsword; roll=18; confirmation hits → critical confirmed."""
        weapon = _longsword()  # base=19 → eff=17 with IC; roll=18 is threat
        # confirm_roll=20 → total=30 → vs target_ac=5 → confirmed
        events = _run_attack(
            d20_roll=18,
            weapon=weapon,
            feats=["improved_critical"],
            target_ac=5,
            confirm_roll=20,
        )
        assert _is_threat(events), "Roll=18 must be threat with IC (longsword eff=17)"
        assert _is_critical(events), \
            f"Expected confirmed critical hit (IC longsword roll=18, confirm=20 vs AC5); events={[e.event_type for e in events]}"
