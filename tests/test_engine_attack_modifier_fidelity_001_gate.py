"""Gate tests for WO-ENGINE-ATTACK-MODIFIER-FIDELITY-001.

FECM: Favored enemy crit multiplication (PHB p.47/p.140)
SNSH: Secondary natural attack ½ STR (PHB p.314)

Authority: RAW — PHB p.47, p.140, p.314; MM p.312
"""

from unittest.mock import MagicMock
from aidm.core.attack_resolver import resolve_attack
from aidm.core.natural_attack_resolver import resolve_natural_attack
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_rng(rolls):
    """Mock RNG returning rolls in sequence."""
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(side_effect=list(rolls))
    rng.stream = MagicMock(return_value=stream)
    return rng


def _find_event(events, event_type):
    return next((e for e in events if e.event_type == event_type), None)


def _fe_ws(attacker_fe_bonus=2, target_type="humanoid", target_subtype="orc"):
    attacker = {
        EF.ENTITY_ID: "a", EF.TEAM: "player",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.DEFEATED: False, EF.AC: 10,
        EF.STR_MOD: 4, EF.DEX_MOD: 0, EF.CON_MOD: 0,
        EF.CONDITIONS: {}, EF.FEATS: [],
        EF.CLASS_LEVELS: {"ranger": 5},
        EF.FAVORED_ENEMIES: [{"creature_type": target_type, "bonus": attacker_fe_bonus}],
        EF.NATURAL_ATTACKS: [],
        EF.POSITION: {"x": 0, "y": 0},
    }
    target = {
        EF.ENTITY_ID: "t", EF.TEAM: "enemy",
        EF.HP_CURRENT: 100, EF.HP_MAX: 100, EF.DEFEATED: False,
        EF.AC: 5,
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.CON_MOD: 0,
        EF.CONDITIONS: {}, EF.FEATS: [],
        EF.CLASS_LEVELS: {},
        EF.FAVORED_ENEMIES: [],
        EF.CREATURE_TYPE: target_type,
        EF.NATURAL_ATTACKS: [],
        EF.POSITION: {"x": 1, "y": 0},
    }
    return WorldState(
        ruleset_version="3.5",
        entities={"a": attacker, "t": target},
        active_combat=None,
    )


def _fe_weapon(crit_mult=2):
    return Weapon(
        damage_dice="1d8", damage_bonus=0, damage_type="slashing",
        critical_multiplier=crit_mult, critical_range=20,
        weapon_type="one-handed", grip="one-handed", is_two_handed=False,
    )


# ── FECM-001: Crit (×2) vs favored enemy → FE×2 ──────────────────────────

def test_fecm_001_crit_x2_fe_multiplied():
    # Attack roll 20 (nat crit), confirm roll 20 (confirms), damage 4
    # Base: dice(4) + STR(4) + FE(2) = 10; crit ×2 = 20
    # If FE NOT multiplied (wrong): dice(4)+STR(4)=8 ×2=16 + FE(2) = 18
    rng = _make_rng([20, 20, 4])  # attack, confirm, damage
    ws = _fe_ws(attacker_fe_bonus=2)
    intent = AttackIntent(attacker_id="a", target_id="t", weapon=_fe_weapon(crit_mult=2), attack_bonus=5)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    hp_event = _find_event(events, "hp_changed")
    assert hp_event is not None, "Attack should hit and deal damage"
    damage = abs(hp_event.payload.get("delta", 0))
    # FE included in pre-crit: (4+4+2) × 2 = 20
    assert damage == 20, f"FE should be multiplied on crit: expected 20 (10×2), got {damage}"


# ── FECM-002: Crit (×3) vs favored enemy → FE×3 ──────────────────────────

def test_fecm_002_crit_x3_fe_multiplied():
    # Attack 20 (nat crit), confirm 20, damage 4
    # Base: 4+4+2=10; crit ×3 = 30
    rng = _make_rng([20, 20, 4])
    ws = _fe_ws(attacker_fe_bonus=2)
    intent = AttackIntent(attacker_id="a", target_id="t", weapon=_fe_weapon(crit_mult=3), attack_bonus=5)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    hp_event = _find_event(events, "hp_changed")
    assert hp_event is not None
    damage = abs(hp_event.payload.get("delta", 0))
    assert damage == 30, f"FE×3 on crit: expected 30 (10×3), got {damage}"


# ── FECM-003: Non-crit vs favored enemy → FE once ─────────────────────────

def test_fecm_003_non_crit_fe_once():
    # Attack roll 15 (hits but not crit), damage 4
    # Base: 4+4+2=10; no crit
    rng = _make_rng([15, 4])
    ws = _fe_ws(attacker_fe_bonus=2)
    intent = AttackIntent(attacker_id="a", target_id="t", weapon=_fe_weapon(crit_mult=2), attack_bonus=5)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    hp_event = _find_event(events, "hp_changed")
    assert hp_event is not None
    damage = abs(hp_event.payload.get("delta", 0))
    assert damage == 10, f"Non-crit: FE once, expected 10 (4+4+2), got {damage}"


# ── FECM-004: Crit vs non-favored → no FE ─────────────────────────────────

def test_fecm_004_crit_no_fe():
    # Target is "aberration" (not in favored enemies list)
    rng = _make_rng([20, 20, 4])
    ws = _fe_ws(attacker_fe_bonus=2, target_type="aberration")
    # Attacker has FE vs humanoid, not aberration
    ws.entities["a"][EF.FAVORED_ENEMIES] = [{"creature_type": "humanoid", "bonus": 2}]
    intent = AttackIntent(attacker_id="a", target_id="t", weapon=_fe_weapon(crit_mult=2), attack_bonus=5)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    hp_event = _find_event(events, "hp_changed")
    assert hp_event is not None
    damage = abs(hp_event.payload.get("delta", 0))
    # No FE: (4+4) × 2 = 16
    assert damage == 16, f"No FE on non-favored: expected 16 (8×2), got {damage}"


# ── SNSH: Secondary natural attack ½ STR tests ────────────────────────────

def _nat_attack_ws(str_mod=3):
    actor = {
        EF.ENTITY_ID: "a", EF.TEAM: "player",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.DEFEATED: False, EF.AC: 10,
        EF.STR_MOD: str_mod, EF.DEX_MOD: 0, EF.CON_MOD: 0,
        EF.CONDITIONS: {}, EF.FEATS: [],
        EF.CLASS_LEVELS: {},
        EF.FAVORED_ENEMIES: [],
        EF.NATURAL_ATTACKS: [
            {"name": "bite", "damage": "1d6", "attack_type": "bite", "is_primary": True},
            {"name": "claw", "damage": "1d4", "attack_type": "claw", "is_primary": False},
        ],
        EF.POSITION: {"x": 0, "y": 0},
        EF.EQUIPMENT_MELDED: False,
    }
    target = {
        EF.ENTITY_ID: "t", EF.TEAM: "enemy",
        EF.HP_CURRENT: 100, EF.HP_MAX: 100, EF.DEFEATED: False,
        EF.AC: 5,
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.CON_MOD: 0,
        EF.CONDITIONS: {}, EF.FEATS: [],
        EF.CLASS_LEVELS: {},
        EF.FAVORED_ENEMIES: [],
        EF.NATURAL_ATTACKS: [],
        EF.POSITION: {"x": 1, "y": 0},
    }
    return WorldState(
        ruleset_version="3.5",
        entities={"a": actor, "t": target},
        active_combat=None,
    )


def _make_nat_intent(actor_id, target_id, attack_name, attack_bonus=5):
    """Create intent for natural attack resolver."""
    from dataclasses import dataclass

    @dataclass
    class NatAttackIntent:
        attacker_id: str
        target_id: str
        attack_name: str
        attack_bonus: int = 5

    return NatAttackIntent(attacker_id=actor_id, target_id=target_id,
                           attack_name=attack_name, attack_bonus=attack_bonus)


# ── SNSH-001: Secondary natural attack → ½ STR (STR 16/+3 → +1) ──────────

def test_snsh_001_secondary_half_str():
    # STR mod 3 → secondary gets int(3*0.5)=1
    # Attack roll 15 (hits), damage roll 2
    # Secondary: 2 + 1(½ STR) = 3
    rng = _make_rng([15, 2])
    ws = _nat_attack_ws(str_mod=3)
    intent = _make_nat_intent("a", "t", "claw")
    events, _ = resolve_natural_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    hp_event = _find_event(events, "hp_changed")
    assert hp_event is not None, "Secondary natural attack should deal damage"
    damage = abs(hp_event.payload.get("delta", 0))
    assert damage == 3, f"Secondary: ½ STR (int(3*0.5)=1), expected damage 3 (2+1), got {damage}"


# ── SNSH-002: Primary natural attack → full STR ───────────────────────────

def test_snsh_002_primary_full_str():
    # STR mod 3 → primary gets full 3
    # Attack roll 15, damage 2
    # Primary: 2 + 3(full STR) = 5
    rng = _make_rng([15, 2])
    ws = _nat_attack_ws(str_mod=3)
    intent = _make_nat_intent("a", "t", "bite")
    events, _ = resolve_natural_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    hp_event = _find_event(events, "hp_changed")
    assert hp_event is not None
    damage = abs(hp_event.payload.get("delta", 0))
    assert damage == 5, f"Primary: full STR(3), expected 5 (2+3), got {damage}"


# ── SNSH-003: Secondary with negative STR → ½ negative (STR 8/-1 → 0) ────

def test_snsh_003_negative_str_half():
    # STR mod -1 → secondary gets int(-1/2)=0 (truncates toward zero)
    rng = _make_rng([15, 4])
    ws = _nat_attack_ws(str_mod=-1)
    intent = _make_nat_intent("a", "t", "claw")
    events, _ = resolve_natural_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    hp_event = _find_event(events, "hp_changed")
    assert hp_event is not None
    damage = abs(hp_event.payload.get("delta", 0))
    # 4 + int(-1*0.5)=0 = 4 (min 1 guard may apply)
    assert damage == 4, f"Negative STR half: expected 4 (4+0), got {damage}"


# ── SNSH-004: Secondary with odd STR mod → truncated (STR 12/+1 → 0) ──────

def test_snsh_004_odd_str_truncated():
    # STR mod 1 → secondary gets int(1*0.5)=0
    rng = _make_rng([15, 3])
    ws = _nat_attack_ws(str_mod=1)
    intent = _make_nat_intent("a", "t", "claw")
    events, _ = resolve_natural_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    hp_event = _find_event(events, "hp_changed")
    assert hp_event is not None
    damage = abs(hp_event.payload.get("delta", 0))
    # 3 + int(1*0.5)=0 = 3
    assert damage == 3, f"Odd STR truncated: expected 3 (3+0), got {damage}"
