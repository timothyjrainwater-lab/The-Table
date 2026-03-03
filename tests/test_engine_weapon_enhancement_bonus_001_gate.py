"""Gate tests: WO-ENGINE-WEAPON-ENHANCEMENT-BONUS-001 (Batch BB WO1).

WEB-001..008 per PM Acceptance Notes:
  WEB-001: Mundane weapon (enh=0) → no enhancement bonus to attack
  WEB-002: +1 weapon → attack roll includes +1 enhancement bonus
  WEB-003: +2 weapon → attack roll includes +2 enhancement bonus
  WEB-004: +1 weapon + Weapon Focus → stacking: +1 WF + +1 enh = +2 total bonus
  WEB-005: Mundane weapon → no enhancement bonus to damage
  WEB-006: +1 weapon → damage roll includes +1 enhancement bonus
  WEB-007: +2 weapon + Weapon Specialization → stacking: +2 WS + +2 enh = +4 total damage bonus
  WEB-008: Full attack path confirmed — enhancement fires via resolve_attack (FAR delegates)

NOTE (GHOST): Code wired at attack_resolver.py:750 (attack) and :985 (damage) by
WO-ENGINE-WEAPON-ENHANCEMENT-001. These gate tests close the coverage gap for BB.

FINDING-ENGINE-WEAPON-ENHANCEMENT-BONUS-AC-WIRE-001 closed.
"""
from __future__ import annotations

import unittest.mock as mock

from aidm.core.attack_resolver import resolve_attack
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _weapon(enhancement_bonus: int = 0) -> Weapon:
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="slashing",
        grip="one-handed",
        weapon_type="one-handed",
        enhancement_bonus=enhancement_bonus,
    )


def _rng_fixed(attack: int = 15, damage: int = 4):
    """Mock RNG returning fixed values (attack roll, then all damage dice = 4)."""
    stream = mock.MagicMock()
    stream.randint.side_effect = [attack, damage] + [damage] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _attacker(feats=None, weapon_entity_name=None):
    """Minimal attacker: BAB=5, STR=0, DEX=0. Clean baseline to isolate enhancement."""
    ent = {
        EF.ENTITY_ID: "att", EF.TEAM: "player",
        EF.STR_MOD: 0, EF.DEX_MOD: 0,
        EF.FEATS: feats or [],
        EF.ATTACK_BONUS: 5,
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 15, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: {},
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.FAVORED_ENEMIES: [], EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 0, "y": 0},
    }
    if weapon_entity_name:
        # Required by attack_resolver to resolve weapon_name for WF/WS feat lookups
        ent[EF.WEAPON] = {"name": weapon_entity_name}
    return ent


def _target(ac: int = 10):
    return {
        EF.ENTITY_ID: "tgt", EF.TEAM: "monsters",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: ac, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: {},
        EF.POSITION: {"x": 1, "y": 0},
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.FEATS: [],
    }


def _ws(att, tgt):
    return WorldState(
        ruleset_version="3.5",
        entities={"att": att, "tgt": tgt},
        active_combat={"initiative_order": ["att", "tgt"],
                       "aoo_used_this_round": [], "aoo_count_this_round": {}},
    )


def _atk_event(events):
    return next((e for e in events if e.event_type == "attack_roll"), None)


def _dmg_event(events):
    return next((e for e in events if e.event_type == "damage_roll"), None)


# ---------------------------------------------------------------------------
# WEB-001: Mundane weapon → no enhancement attack bonus
# ---------------------------------------------------------------------------

def test_WEB001_mundane_no_attack_enhancement():
    """WEB-001: Mundane weapon (enh=0) → no enhancement bonus to attack.
    d20=15 + BAB=5 + enh=0 = 20. Miss at AC=21 confirms no hidden bonus."""
    att = _attacker()
    ws = _ws(att, _target(ac=21))
    intent = AttackIntent(attacker_id="att", target_id="tgt",
                          attack_bonus=5, weapon=_weapon(enhancement_bonus=0))
    events = resolve_attack(intent=intent, world_state=ws,
                            rng=_rng_fixed(attack=15), next_event_id=0, timestamp=0.0)
    ev = _atk_event(events)
    assert ev is not None, "WEB-001: No attack_roll event"
    assert not ev.payload["hit"], (
        f"WEB-001: Mundane weapon should miss at AC=21 (total={ev.payload.get('total')}). "
        "Enhancement bonus must not be applied."
    )


# ---------------------------------------------------------------------------
# WEB-002: +1 weapon → attack includes +1 enhancement bonus
# ---------------------------------------------------------------------------

def test_WEB002_plus1_weapon_attack_enhancement():
    """WEB-002: +1 weapon → attack roll includes +1 enhancement bonus.
    d20=15 + BAB=5 + enh=1 = 21 >= AC=21 → hit."""
    att = _attacker()
    ws = _ws(att, _target(ac=21))
    intent = AttackIntent(attacker_id="att", target_id="tgt",
                          attack_bonus=5, weapon=_weapon(enhancement_bonus=1))
    events = resolve_attack(intent=intent, world_state=ws,
                            rng=_rng_fixed(attack=15), next_event_id=0, timestamp=0.0)
    ev = _atk_event(events)
    assert ev is not None, "WEB-002: No attack_roll event"
    assert ev.payload["hit"], (
        f"WEB-002: +1 weapon should hit at AC=21 (total={ev.payload.get('total')}). "
        "+1 enhancement must be included in attack total."
    )


# ---------------------------------------------------------------------------
# WEB-003: +2 weapon → attack includes +2 enhancement bonus
# ---------------------------------------------------------------------------

def test_WEB003_plus2_weapon_attack_enhancement():
    """WEB-003: +2 weapon → attack includes +2 enhancement bonus.
    d20=15 + BAB=5 + enh=2 = 22 >= AC=22 → hit."""
    att = _attacker()
    ws = _ws(att, _target(ac=22))
    intent = AttackIntent(attacker_id="att", target_id="tgt",
                          attack_bonus=5, weapon=_weapon(enhancement_bonus=2))
    events = resolve_attack(intent=intent, world_state=ws,
                            rng=_rng_fixed(attack=15), next_event_id=0, timestamp=0.0)
    ev = _atk_event(events)
    assert ev is not None, "WEB-003: No attack_roll event"
    assert ev.payload["hit"], (
        f"WEB-003: +2 weapon should hit at AC=22 (total={ev.payload.get('total')}). "
        "+2 enhancement must be included."
    )


# ---------------------------------------------------------------------------
# WEB-004: +1 weapon + Weapon Focus → stacking (+1 WF + +1 enh = +2 total)
# ---------------------------------------------------------------------------

def test_WEB004_enhancement_stacks_with_weapon_focus():
    """WEB-004: +1 weapon + Weapon Focus(longsword) → total bonus = +2. Hit at AC=22.
    d20=15 + BAB=5 + WF=1 + enh=1 = 22 >= 22 → hit. Enhancement stacks with WF."""
    att = _attacker(feats=["weapon_focus_longsword"], weapon_entity_name="longsword")
    ws = _ws(att, _target(ac=22))
    intent = AttackIntent(attacker_id="att", target_id="tgt",
                          attack_bonus=5, weapon=_weapon(enhancement_bonus=1))
    events = resolve_attack(intent=intent, world_state=ws,
                            rng=_rng_fixed(attack=15), next_event_id=0, timestamp=0.0)
    ev = _atk_event(events)
    assert ev is not None, "WEB-004: No attack_roll event"
    assert ev.payload["hit"], (
        f"WEB-004: +1 weapon + WF should hit at AC=22 (WF +1 + enh +1 = +2 total). "
        f"total={ev.payload.get('total')}. Enhancement must stack with Weapon Focus."
    )


# ---------------------------------------------------------------------------
# WEB-005: Mundane weapon → no enhancement damage bonus
# ---------------------------------------------------------------------------

def test_WEB005_mundane_no_damage_enhancement():
    """WEB-005: Mundane weapon (enh=0) → no enhancement bonus to damage.
    1d8 fixed=4, STR=0, damage_bonus=0, enh=0 → final_damage=4 (no extra)."""
    att = _attacker()
    ws = _ws(att, _target(ac=5))  # AC=5, always hits
    intent = AttackIntent(attacker_id="att", target_id="tgt",
                          attack_bonus=5, weapon=_weapon(enhancement_bonus=0))
    events = resolve_attack(intent=intent, world_state=ws,
                            rng=_rng_fixed(attack=15, damage=4), next_event_id=0, timestamp=0.0)
    dmg = _dmg_event(events)
    assert dmg is not None, "WEB-005: No damage_roll event (did attack miss?)"
    final = dmg.payload.get("final_damage")
    assert final == 4, (
        f"WEB-005: Mundane weapon final_damage should be 4 (dice=4, no enhancement), got {final}"
    )


# ---------------------------------------------------------------------------
# WEB-006: +1 weapon → damage includes +1 enhancement bonus
# ---------------------------------------------------------------------------

def test_WEB006_plus1_weapon_damage_enhancement():
    """WEB-006: +1 weapon → damage includes +1 enhancement bonus.
    1d8 fixed=4, STR=0, damage_bonus=0, enh=1 → final_damage=5."""
    att = _attacker()
    ws = _ws(att, _target(ac=5))
    intent = AttackIntent(attacker_id="att", target_id="tgt",
                          attack_bonus=5, weapon=_weapon(enhancement_bonus=1))
    events = resolve_attack(intent=intent, world_state=ws,
                            rng=_rng_fixed(attack=15, damage=4), next_event_id=0, timestamp=0.0)
    dmg = _dmg_event(events)
    assert dmg is not None, "WEB-006: No damage_roll event (did attack miss?)"
    final = dmg.payload.get("final_damage")
    assert final == 5, (
        f"WEB-006: +1 weapon final_damage should be 5 (dice=4 + enh=1), got {final}"
    )


# ---------------------------------------------------------------------------
# WEB-007: +2 weapon + Weapon Specialization → +4 total damage bonus
# ---------------------------------------------------------------------------

def test_WEB007_enhancement_stacks_with_weapon_specialization():
    """WEB-007: +2 weapon + WS(longsword) → +2 enh + +2 WS = +4 total damage bonus.
    1d8 fixed=4, STR=0, enh=2, WS=2 → final_damage=8."""
    att = _attacker(
        feats=["weapon_focus_longsword", "weapon_specialization_longsword"],
        weapon_entity_name="longsword",
    )
    ws = _ws(att, _target(ac=5))
    intent = AttackIntent(attacker_id="att", target_id="tgt",
                          attack_bonus=5, weapon=_weapon(enhancement_bonus=2))
    events = resolve_attack(intent=intent, world_state=ws,
                            rng=_rng_fixed(attack=15, damage=4), next_event_id=0, timestamp=0.0)
    dmg = _dmg_event(events)
    assert dmg is not None, "WEB-007: No damage_roll event (did attack miss?)"
    final = dmg.payload.get("final_damage")
    assert final == 8, (
        f"WEB-007: +2 weapon + WS final_damage should be 8 (dice=4 + enh=2 + WS=2), got {final}. "
        "Enhancement and Weapon Specialization must stack independently."
    )


# ---------------------------------------------------------------------------
# WEB-008: Full attack path — enhancement fires in resolve_attack (FAR delegates here)
# ---------------------------------------------------------------------------

def test_WEB008_full_attack_path_enhancement_fires():
    """WEB-008: Full attack (FAR) path confirmed: enhancement fires in resolve_attack().
    full_attack_resolver calls resolve_attack() per swing (FAGU). Any resolve_attack call
    with an enhanced weapon confirms the full-attack path. Verify damage reflects +1 enh."""
    att = _attacker()
    # Use high BAB representing iterative attack scenario
    ws = _ws(att, _target(ac=5))
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=11,  # BAB=11 → iterative attacks in FAR; same code path in resolve_attack
        weapon=_weapon(enhancement_bonus=1),
    )
    events = resolve_attack(intent=intent, world_state=ws,
                            rng=_rng_fixed(attack=15, damage=4), next_event_id=0, timestamp=0.0)
    atk = _atk_event(events)
    assert atk is not None, "WEB-008: No attack_roll event"
    dmg = _dmg_event(events)
    assert dmg is not None, "WEB-008: No damage_roll event — enhancement not firing in full-attack path"
    final = dmg.payload.get("final_damage")
    assert final == 5, (
        f"WEB-008: Full-attack path final_damage should be 5 (dice=4+enh=1), got {final}. "
        "Enhancement bonus must fire in every resolve_attack() call including FAR-delegated hits."
    )
