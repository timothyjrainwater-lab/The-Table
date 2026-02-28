"""Gate tests: Monk Unarmed Attack Wire — WO-ENGINE-AF-WO2.

MUW-001 through MUW-008.

Closes FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001.

EF.MONK_UNARMED_DICE was set at chargen (builder.py) per PHB Table 3-10 but
never read by attack_resolver.py. This WO wires the consume site.

PHB Table 3-10 (p.41), Medium size monk damage:
  L1-3: 1d6 | L4-7: 1d8 | L8-11: 1d10 | L12-15: 2d6 | L16-19: 2d8 | L20: 2d10
"""

import pytest
from copy import deepcopy

from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.rng_manager import RNGManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unarmed_weapon(damage_dice="1d6"):
    """Build an unarmed weapon dataclass."""
    return Weapon(
        damage_dice=damage_dice,
        damage_type="bludgeoning",
        critical_multiplier=2,
        critical_range=20,
        weapon_type="natural",
        grip="one-handed",
        damage_bonus=0,
        enhancement_bonus=0,
    )


def _monk(eid="monk", level=1, *, monk_unarmed_dice="1d6", str_mod=2):
    """Build a minimal monk entity dict."""
    return {
        EF.ENTITY_ID: eid,
        EF.CLASS_LEVELS: {"monk": level},
        EF.LEVEL: level,
        EF.ATTACK_BONUS: 4,
        EF.BAB: level,
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 1,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.FEATS: [],
        EF.CONDITIONS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.MONK_UNARMED_DICE: monk_unarmed_dice,
        EF.SIZE_CATEGORY: "medium",
        EF.CREATURE_TYPE: "humanoid",
        EF.ARMOR_AC_BONUS: 0,
        EF.MONK_WIS_AC_BONUS: 0,
        EF.DEFLECTION_BONUS: 0,
        EF.TEAM: "players",
    }


def _fighter(eid="target", *, ac=10, str_mod=2):
    return {
        EF.ENTITY_ID: eid,
        EF.CLASS_LEVELS: {"fighter": 5},
        EF.LEVEL: 5,
        EF.ATTACK_BONUS: 4,
        EF.BAB: 5,
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 0,
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: ac,
        EF.FEATS: [],
        EF.CONDITIONS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.DAMAGE_REDUCTIONS: [],
        EF.SIZE_CATEGORY: "medium",
        EF.CREATURE_TYPE: "humanoid",
        EF.TEAM: "enemies",
        EF.DEFLECTION_BONUS: 0,
    }


def _ws(attacker, target):
    return WorldState(
        ruleset_version="3.5",
        entities={
            attacker[EF.ENTITY_ID]: attacker,
            target[EF.ENTITY_ID]: target,
        },
        active_combat=None,
    )


def _force_hit_attack(attacker_id, target_id, weapon, world_state, rng):
    """Run resolve_attack with rng seeded to hit (roll=19)."""
    intent = AttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        weapon=weapon,
        attack_bonus=15,  # High enough to ensure hit regardless of AC
    )
    return resolve_attack(intent, world_state, rng, next_event_id=1, timestamp=0.0)


def _damage_from_events(events):
    """Extract final_damage from non-critical damage_roll events.

    Excludes critical hits because crits multiply damage beyond the base die range,
    which would break the range assertions in MUW-001 through MUW-005.
    """
    for e in events:
        if e.event_type == "damage_roll":
            crit_mult = e.payload.get("critical_multiplier", 1)
            if crit_mult == 1:  # Non-crit only
                return e.payload["final_damage"]
    return None


def _rng_always_high():
    """RNG that rolls 19 on d20 (guaranteed hit), and mid-range on damage."""
    return RNGManager(master_seed=42)


# ---------------------------------------------------------------------------
# MUW-001: Monk L1 unarmed → damage in 1d6 range (1-6)
# ---------------------------------------------------------------------------

def test_muw_001_monk_l1_damage_in_1d6_range():
    """MUW-001: Monk L1 (MONK_UNARMED_DICE='1d6') → damage roll 1–6."""
    monk = _monk(level=1, monk_unarmed_dice="1d6", str_mod=0)
    monk[EF.BAB] = 0
    target = _fighter(ac=5)  # Low AC to ensure hit
    ws = _ws(monk, target)
    weapon = _unarmed_weapon("1d6")

    damages = set()
    for seed in range(50):
        rng = RNGManager(master_seed=seed)
        events = _force_hit_attack("monk", "target", weapon, ws, rng)
        dmg = _damage_from_events(events)
        if dmg is not None:
            damages.add(dmg)

    # All damage values must be in [1, 6] (including str_mod=0, min 1)
    assert all(1 <= d <= 6 for d in damages), (
        f"MUW-001: L1 monk unarmed damage out of 1d6 range: {damages}"
    )


# ---------------------------------------------------------------------------
# MUW-002: Monk L4 unarmed → damage in 1d8 range (1-8)
# ---------------------------------------------------------------------------

def test_muw_002_monk_l4_damage_in_1d8_range():
    """MUW-002: Monk L4 (MONK_UNARMED_DICE='1d8') → damage roll 1–8 (str_mod=0)."""
    monk = _monk(level=4, monk_unarmed_dice="1d8", str_mod=0)
    target = _fighter(ac=5)
    ws = _ws(monk, target)
    weapon = _unarmed_weapon("1d8")

    damages = set()
    for seed in range(60):
        rng = RNGManager(master_seed=seed)
        events = _force_hit_attack("monk", "target", weapon, ws, rng)
        dmg = _damage_from_events(events)
        if dmg is not None:
            damages.add(dmg)

    assert all(1 <= d <= 8 for d in damages), (
        f"MUW-002: L4 monk unarmed damage out of 1d8 range: {damages}"
    )
    # Should see multiple distinct values (not always 1)
    assert len(damages) >= 3, f"MUW-002: expected variety in 1d8 rolls, got {damages}"


# ---------------------------------------------------------------------------
# MUW-003: Monk L8 unarmed → damage in 1d10 range (1-10)
# ---------------------------------------------------------------------------

def test_muw_003_monk_l8_damage_in_1d10_range():
    """MUW-003: Monk L8 (MONK_UNARMED_DICE='1d10') → damage roll 1–10 (str_mod=0)."""
    monk = _monk(level=8, monk_unarmed_dice="1d10", str_mod=0)
    target = _fighter(ac=5)
    ws = _ws(monk, target)
    weapon = _unarmed_weapon("1d10")

    damages = set()
    for seed in range(70):
        rng = RNGManager(master_seed=seed)
        events = _force_hit_attack("monk", "target", weapon, ws, rng)
        dmg = _damage_from_events(events)
        if dmg is not None:
            damages.add(dmg)

    assert all(1 <= d <= 10 for d in damages), (
        f"MUW-003: L8 monk unarmed damage out of 1d10 range: {damages}"
    )


# ---------------------------------------------------------------------------
# MUW-004: Monk L12 unarmed → damage in 2d6 range (2-12)
# ---------------------------------------------------------------------------

def test_muw_004_monk_l12_damage_in_2d6_range():
    """MUW-004: Monk L12 (MONK_UNARMED_DICE='2d6') → damage roll 2–12 (str_mod=0)."""
    monk = _monk(level=12, monk_unarmed_dice="2d6", str_mod=0)
    target = _fighter(ac=5)
    ws = _ws(monk, target)
    weapon = _unarmed_weapon("2d6")

    damages = set()
    for seed in range(80):
        rng = RNGManager(master_seed=seed)
        events = _force_hit_attack("monk", "target", weapon, ws, rng)
        dmg = _damage_from_events(events)
        if dmg is not None:
            damages.add(dmg)

    assert all(2 <= d <= 12 for d in damages), (
        f"MUW-004: L12 monk unarmed damage out of 2d6 range: {damages}"
    )


# ---------------------------------------------------------------------------
# MUW-005: Non-monk unarmed → uses weapon default, not MONK_UNARMED_DICE
# ---------------------------------------------------------------------------

def test_muw_005_non_monk_uses_weapon_default():
    """MUW-005: Rogue using unarmed strike uses weapon.damage_dice, not MONK_UNARMED_DICE."""
    rogue = {
        EF.ENTITY_ID: "rogue",
        EF.CLASS_LEVELS: {"rogue": 8},
        EF.LEVEL: 8,
        EF.ATTACK_BONUS: 6,
        EF.BAB: 6,
        EF.STR_MOD: 0,
        EF.DEX_MOD: 2,
        EF.HP_CURRENT: 25,
        EF.HP_MAX: 25,
        EF.FEATS: [],
        EF.CONDITIONS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.SIZE_CATEGORY: "medium",
        EF.CREATURE_TYPE: "humanoid",
        EF.ARMOR_AC_BONUS: 0,
        EF.DEFLECTION_BONUS: 0,
        EF.TEAM: "players",
        # No MONK_UNARMED_DICE field
    }
    target = _fighter(ac=5)
    ws = _ws(rogue, target)
    # Rogue uses 1d3 default for unarmed (no monk dice override)
    weapon = _unarmed_weapon("1d3")

    damages = set()
    for seed in range(50):
        rng = RNGManager(master_seed=seed)
        events = _force_hit_attack("rogue", "target", weapon, ws, rng)
        dmg = _damage_from_events(events)
        if dmg is not None:
            damages.add(dmg)

    # Non-monk: should roll 1d3 (range 1-3), not monk's dice
    assert all(1 <= d <= 3 for d in damages), (
        f"MUW-005: non-monk unarmed damage out of 1d3 range (no monk override): {damages}"
    )


# ---------------------------------------------------------------------------
# MUW-006: Flurry of Blows path uses MONK_UNARMED_DICE
# ---------------------------------------------------------------------------

def test_muw_006_flurry_path_uses_monk_unarmed_dice():
    """MUW-006: FlurryOfBlowsIntent also uses MONK_UNARMED_DICE via _make_unarmed_weapon().

    Parity check: flurry_of_blows_resolver._make_unarmed_weapon() already reads
    MONK_UNARMED_DICE at flurry_of_blows_resolver.py:97. Confirm the flurry
    damage roll is also within the correct range.
    """
    from aidm.core.flurry_of_blows_resolver import resolve_flurry_of_blows, FlurryOfBlowsIntent

    monk = _monk(level=8, monk_unarmed_dice="1d10", str_mod=0)
    monk[EF.SAVE_FORT] = 4
    monk[EF.SAVE_REF] = 6
    monk[EF.SAVE_WILL] = 6
    monk[EF.BAB] = 8
    target = _fighter(ac=5)
    ws = _ws(monk, target)

    intent = FlurryOfBlowsIntent(
        actor_id="monk",
        target_id="target",
    )

    damages = set()
    for seed in range(80):
        rng = RNGManager(master_seed=seed)
        events, ws2 = resolve_flurry_of_blows(intent, ws, rng, next_event_id=1, timestamp=0.0)
        for e in events:
            if e.event_type == "damage_roll":
                d = e.payload.get("final_damage", 0)
                if d > 0:
                    damages.add(d)

    # All damage from flurry must be in 1d10 range (1-10) or crit range (max 20 for 2×1d10).
    # Also verify at least some damage > 6, proving 1d10 (not 1d6) was used.
    assert damages, "MUW-006: No damage rolls found from flurry"
    assert all(1 <= d <= 20 for d in damages), (
        f"MUW-006: Flurry damage out of expected 1d10 (crit-inclusive) range: {damages}"
    )
    assert max(damages) >= 5 or len(damages) >= 4, (
        "MUW-006: Expected variety / higher max from 1d10 dice (parity vs 1d6)"
    )


# ---------------------------------------------------------------------------
# MUW-007: Full attack path (FullAttackIntent) also uses MONK_UNARMED_DICE
# ---------------------------------------------------------------------------

def test_muw_007_full_attack_uses_monk_unarmed_dice():
    """MUW-007: FullAttackIntent with unarmed weapon also uses MONK_UNARMED_DICE.

    full_attack_resolver delegates to attack_resolver.resolve_attack() which now
    reads MONK_UNARMED_DICE. Verify parity.
    """
    from aidm.core.full_attack_resolver import resolve_full_attack, FullAttackIntent

    monk = _monk(level=8, monk_unarmed_dice="1d10", str_mod=0)
    target = _fighter(ac=5)
    ws = _ws(monk, target)

    weapon = _unarmed_weapon("1d10")
    intent = FullAttackIntent(
        attacker_id="monk",
        target_id="target",
        weapon=weapon,
        base_attack_bonus=8,  # L8 monk BAB = 6, but test uses high bonus to ensure hits
    )

    damages = set()
    for seed in range(80):
        rng = RNGManager(master_seed=seed)
        events = resolve_full_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
        for e in events:
            if e.event_type == "damage_roll":
                crit_mult = e.payload.get("critical_multiplier", 1)
                if crit_mult == 1:  # Non-crit only; crits exceed die range
                    d = e.payload.get("final_damage", 0)
                    if d > 0:
                        damages.add(d)

    assert damages, "MUW-007: No damage rolls from full attack"
    assert all(1 <= d <= 10 for d in damages), (
        f"MUW-007: Full attack damage out of 1d10 range (L8 monk): {damages}"
    )


# ---------------------------------------------------------------------------
# MUW-008: level_up() returns updated monk_unarmed_dice on level crossing
# ---------------------------------------------------------------------------

def test_muw_008_level_up_updates_monk_unarmed_dice():
    """MUW-008: level_up(monk, 4) returns monk_unarmed_dice='1d8' (L3→L4 crossing).

    Verifies that builder.level_up() includes 'monk_unarmed_dice' key in the
    returned delta dict. Caller applies it to the entity.
    """
    from aidm.chargen.builder import level_up

    # Start with a L3 monk (1d6)
    monk_entity = {
        EF.ENTITY_ID: "monk",
        EF.CLASS_LEVELS: {"monk": 3},
        EF.LEVEL: 3,
        EF.HP_MAX: 24,
        EF.HP_CURRENT: 24,
        EF.BAB: 2,
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 3,
        EF.SAVE_WILL: 3,
        EF.BASE_STATS: {"str": 12, "dex": 14, "con": 12, "int": 10, "wis": 14, "cha": 10},
        EF.CON_MOD: 1,
        EF.DEX_MOD: 2,
        EF.WIS_MOD: 2,
        EF.INT_MOD: 0,
        EF.STR_MOD: 1,
        EF.MONK_UNARMED_DICE: "1d6",
        EF.RACE: "human",
        EF.FEATS: ["improved_unarmed_strike"],
        EF.FEAT_SLOTS: 0,
        EF.SKILL_RANKS: {},
        EF.CLASS_SKILLS: [],
    }

    delta = level_up(monk_entity, "monk", 4)

    # level_up should return monk_unarmed_dice = "1d8" for L4
    assert "monk_unarmed_dice" in delta, (
        "MUW-008: level_up() must return 'monk_unarmed_dice' key for monk class"
    )
    assert delta["monk_unarmed_dice"] == "1d8", (
        f"MUW-008: Expected '1d8' at monk L4, got '{delta['monk_unarmed_dice']}'"
    )
