"""ENGINE-MULTIATTACK Gate -- Multiattack feat secondary natural attack penalty (8 tests).

Gate: ENGINE-MULTIATTACK
Tests: MA-001 through MA-008
WO: WO-ENGINE-MULTIATTACK-001

PHB p.98: Multiattack feat reduces secondary natural attack penalty from −5 to −2.
Primary natural attacks are unaffected (no penalty modifier).

Key: attack_dict["is_primary"] = False marks a secondary attack.
     attack_type defaults to attack name for INA key lookup.
"""

from copy import deepcopy

from aidm.core.natural_attack_resolver import resolve_natural_attack, _build_weapon_from_natural_attack
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import NaturalAttackIntent


# ---------------------------------------------------------------------------
# Minimal RNG stub (always rolls 10 on d20, 3 on d6/d4)
# ---------------------------------------------------------------------------

class _FixedRNG(RNGProvider):
    def __init__(self, d20_val=10, damage_val=3):
        self._d20 = d20_val
        self._dmg = damage_val

    def stream(self, name: str):
        return self

    def randint(self, lo: int, hi: int) -> int:
        if hi == 20:
            return self._d20
        return min(self._dmg, hi)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _goblin(eid="goblin"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "enemy",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 12,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.TEMPORARY_MODIFIERS: {},
        EF.DAMAGE_REDUCTIONS: [],
        EF.SIZE_CATEGORY: "small",
        EF.NEGATIVE_LEVELS: 0,
        EF.MISS_CHANCE: 0,
    }


def _creature(eid="creature", feats=None, natural_attacks=None):
    """Generic creature with configurable feats and natural attacks."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "enemy",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 10,
        EF.DEFEATED: False,
        EF.STR_MOD: 3,
        EF.DEX_MOD: 1,
        EF.CON_MOD: 2,
        EF.BAB: 4,
        EF.ATTACK_BONUS: 7,
        EF.CLASS_LEVELS: {},
        EF.CONDITIONS: {},
        EF.FEATS: feats if feats is not None else [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.NATURAL_ATTACKS: natural_attacks if natural_attacks is not None else [],
        EF.EQUIPMENT_MELDED: True,  # creature in natural form
        EF.SIZE_CATEGORY: "large",
        EF.DAMAGE_REDUCTIONS: [],
        EF.NEGATIVE_LEVELS: 0,
        EF.MISS_CHANCE: 0,
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


# Bear-like creature: 1 primary bite + 2 secondary claws
_BEAR_ATTACKS = [
    {"name": "bite", "damage": "1d8", "damage_type": "piercing", "is_primary": True},
    {"name": "claw", "damage": "1d6", "damage_type": "slashing", "is_primary": False},
]

# Hydra-like: 1 primary bite + 3 secondary bites (named bite2/bite3/bite4 for clarity)
_HYDRA_ATTACKS = [
    {"name": "bite", "damage": "1d10", "damage_type": "piercing", "is_primary": True},
    {"name": "bite2", "damage": "1d10", "damage_type": "piercing", "is_primary": False},
    {"name": "bite3", "damage": "1d10", "damage_type": "piercing", "is_primary": False},
    {"name": "bite4", "damage": "1d10", "damage_type": "piercing", "is_primary": False},
]

# Wolf: single natural attack type (bite only)
_WOLF_ATTACKS = [
    {"name": "bite", "damage": "1d6", "damage_type": "piercing", "is_primary": True},
]


def _resolve_attack_bonus(creature_eid, target_eid, attack_name, base_bonus, feats, natural_attacks):
    """Helper: resolve a natural attack and return the attack_bonus used in the AttackIntent."""
    creature = _creature(eid=creature_eid, feats=feats, natural_attacks=natural_attacks)
    goblin = _goblin(eid=target_eid)
    ws = _world({creature_eid: creature, target_eid: goblin})
    rng = _FixedRNG(d20_val=10, damage_val=3)
    intent = NaturalAttackIntent(
        attacker_id=creature_eid,
        target_id=target_eid,
        attack_name=attack_name,
        attack_bonus=base_bonus,
    )
    events, _ = resolve_natural_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    # Extract the attack_roll event to determine effective attack bonus used
    roll_events = [e for e in events if e.event_type == "attack_roll"]
    if not roll_events:
        return None
    e = roll_events[0]
    # attack_bonus is stored directly in the payload
    return e.payload.get("attack_bonus")


# ===========================================================================
# MA-001: Secondary natural attack without Multiattack → −5 penalty
# ===========================================================================

def test_ma001_secondary_without_multiattack_minus5():
    """MA-001: Secondary natural attack with no Multiattack → −5 penalty applied."""
    bonus = _resolve_attack_bonus("bear", "goblin", "claw", base_bonus=7,
                                  feats=[], natural_attacks=_BEAR_ATTACKS)
    # base_bonus=7, secondary_adjustment=−5 → effective = 2
    assert bonus == 2, f"Expected 2 (7-5), got {bonus}"


# ===========================================================================
# MA-002: Secondary natural attack WITH Multiattack → −2 penalty
# ===========================================================================

def test_ma002_secondary_with_multiattack_minus2():
    """MA-002: Secondary natural attack with Multiattack feat → −2 penalty (not −5)."""
    bonus = _resolve_attack_bonus("bear", "goblin", "claw", base_bonus=7,
                                  feats=["multiattack"], natural_attacks=_BEAR_ATTACKS)
    # base_bonus=7, secondary_adjustment=−2 → effective = 5
    assert bonus == 5, f"Expected 5 (7-2), got {bonus}"


# ===========================================================================
# MA-003: Primary natural attack unaffected by Multiattack
# ===========================================================================

def test_ma003_primary_unaffected_by_multiattack():
    """MA-003: Primary natural attack always resolves at full attack_bonus — no penalty."""
    bonus_no_feat = _resolve_attack_bonus("bear", "goblin", "bite", base_bonus=7,
                                          feats=[], natural_attacks=_BEAR_ATTACKS)
    bonus_with_feat = _resolve_attack_bonus("bear", "goblin", "bite", base_bonus=7,
                                            feats=["multiattack"], natural_attacks=_BEAR_ATTACKS)
    assert bonus_no_feat == 7, f"Primary without feat: expected 7, got {bonus_no_feat}"
    assert bonus_with_feat == 7, f"Primary with feat: expected 7, got {bonus_with_feat}"


# ===========================================================================
# MA-004: Multiattack with 3 secondary attacks — all three get −2
# ===========================================================================

def test_ma004_multiattack_three_secondary_all_minus2():
    """MA-004: 3 secondary attacks with Multiattack all resolve at −2 penalty."""
    feats = ["multiattack"]
    for attack_name in ("bite2", "bite3", "bite4"):
        bonus = _resolve_attack_bonus("hydra", "goblin", attack_name, base_bonus=8,
                                      feats=feats, natural_attacks=_HYDRA_ATTACKS)
        # 8 − 2 = 6
        assert bonus == 6, f"{attack_name}: expected 6 (8-2), got {bonus}"


# ===========================================================================
# MA-005: Penalty delta — same creature, same target, with/without Multiattack → 3-point delta
# ===========================================================================

def test_ma005_penalty_delta_three_points():
    """MA-005: Multiattack vs no feat on secondary attack → exactly 3-point bonus delta."""
    bonus_without = _resolve_attack_bonus("bear", "goblin", "claw", base_bonus=7,
                                          feats=[], natural_attacks=_BEAR_ATTACKS)
    bonus_with = _resolve_attack_bonus("bear", "goblin", "claw", base_bonus=7,
                                       feats=["multiattack"], natural_attacks=_BEAR_ATTACKS)
    delta = bonus_with - bonus_without
    assert delta == 3, f"Expected 3-point delta, got {delta}"


# ===========================================================================
# MA-006: Creature with only 1 natural attack type → Multiattack has no effect on primary
# ===========================================================================

def test_ma006_single_attack_type_multiattack_no_effect():
    """MA-006: Wolf with single bite (primary) — Multiattack has no effect (no secondary)."""
    bonus_without = _resolve_attack_bonus("wolf", "goblin", "bite", base_bonus=5,
                                          feats=[], natural_attacks=_WOLF_ATTACKS)
    bonus_with = _resolve_attack_bonus("wolf", "goblin", "bite", base_bonus=5,
                                       feats=["multiattack"], natural_attacks=_WOLF_ATTACKS)
    assert bonus_without == 5, f"Without Multiattack: expected 5, got {bonus_without}"
    assert bonus_with == 5, f"With Multiattack: expected 5, got {bonus_with}"


# ===========================================================================
# MA-007: Regression — non-Multiattack creature primary attack bonus unchanged
# ===========================================================================

def test_ma007_regression_primary_bonus_unchanged():
    """MA-007: Regression guard — primary attack bonus not touched by Multiattack logic."""
    bonus = _resolve_attack_bonus("bear", "goblin", "bite", base_bonus=10,
                                  feats=["power_attack", "cleave"], natural_attacks=_BEAR_ATTACKS)
    assert bonus == 10, f"Primary attack bonus must be unchanged: expected 10, got {bonus}"


# ===========================================================================
# MA-008: Multiattack + INA on same secondary attack → both apply independently
# ===========================================================================

def test_ma008_multiattack_and_ina_apply_independently():
    """MA-008: Multiattack (−2 penalty) + INA upgrade coexist on same secondary attack.

    Verify: secondary attack bonus = base - 2 (Multiattack).
    WO2 regression guard: INA does not interfere with penalty calculation.
    """
    # Claw is secondary, so Multiattack applies −2.
    # INA upgrade to claw damage is separate (WO2 concern).
    attacks = [
        {"name": "bite", "damage": "1d8", "damage_type": "piercing", "is_primary": True},
        {"name": "claw", "damage": "1d6", "damage_type": "slashing", "is_primary": False},
    ]
    feats = ["multiattack", "improved_natural_attack_claw"]
    bonus = _resolve_attack_bonus("bear", "goblin", "claw", base_bonus=7,
                                  feats=feats, natural_attacks=attacks)
    # Secondary + Multiattack → 7 − 2 = 5
    assert bonus == 5, f"Expected 5 (7-2 with Multiattack), got {bonus}"
