"""ENGINE-IMPROVED-NATURAL-ATTACK Gate -- INA damage die upgrade (8 tests).

Gate: ENGINE-IMPROVED-NATURAL-ATTACK
Tests: INA-001 through INA-008
WO: WO-ENGINE-IMPROVED-NATURAL-ATTACK-001

PHB p.96: Improved Natural Attack feat increases damage die for chosen natural attack
by one step: 1d2→1d3→1d4→1d6→1d8→2d6→3d6→4d6→6d6→8d6→12d6.

Feat key format: improved_natural_attack_{attack_type}
where attack_type defaults to the attack name (e.g., "bite", "claw").

Implementation applies upgrade as a local variable at resolve time.
Entity's NATURAL_ATTACKS list is NOT mutated.
"""

from copy import deepcopy

from aidm.core.natural_attack_resolver import resolve_natural_attack, _build_weapon_from_natural_attack, _INA_STEP_TABLE
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import NaturalAttackIntent


# ---------------------------------------------------------------------------
# Minimal RNG stub
# ---------------------------------------------------------------------------

class _FixedRNG(RNGProvider):
    def stream(self, name: str):
        return self

    def randint(self, lo: int, hi: int) -> int:
        if hi == 20:
            return 10  # hits almost anything
        return min(3, hi)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _goblin(eid="goblin"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "enemy",
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 8,  # Low AC so d20=10 always hits
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.TEMPORARY_MODIFIERS: {},
        EF.DAMAGE_REDUCTIONS: [],
        EF.SIZE_CATEGORY: "small",
        EF.NEGATIVE_LEVELS: 0,
        EF.MISS_CHANCE: 0,
    }


def _creature(eid="creature", feats=None, natural_attacks=None):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 10,
        EF.DEFEATED: False,
        EF.STR_MOD: 0,  # Zero STR mod for clean damage_dice inspection
        EF.DEX_MOD: 1,
        EF.CON_MOD: 2,
        EF.BAB: 4,
        EF.ATTACK_BONUS: 6,
        EF.CLASS_LEVELS: {},
        EF.CONDITIONS: {},
        EF.FEATS: feats if feats is not None else [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.NATURAL_ATTACKS: natural_attacks if natural_attacks is not None else [],
        EF.EQUIPMENT_MELDED: True,
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


def _get_damage_dice_used(creature_eid, target_eid, attack_name, feats, natural_attacks):
    """Resolve attack and return the damage_dice string from the damage_roll event."""
    creature = _creature(eid=creature_eid, feats=feats, natural_attacks=natural_attacks)
    goblin = _goblin(eid=target_eid)
    ws = _world({creature_eid: creature, target_eid: goblin})
    rng = _FixedRNG()
    intent = NaturalAttackIntent(
        attacker_id=creature_eid,
        target_id=target_eid,
        attack_name=attack_name,
        attack_bonus=10,  # High enough to always hit goblin AC=8
    )
    events, _ = resolve_natural_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    dmg_events = [e for e in events if e.event_type == "damage_roll"]
    if not dmg_events:
        return None
    return dmg_events[0].payload.get("damage_dice")


# ===========================================================================
# INA-001: improved_natural_attack_bite + bite 1d6 → resolves as 1d8
# ===========================================================================

def test_ina001_bite_1d6_upgrades_to_1d8():
    """INA-001: bite with 1d6 base + improved_natural_attack_bite → damage resolves as 1d8."""
    attacks = [{"name": "bite", "damage": "1d6", "damage_type": "piercing", "is_primary": True}]
    dice = _get_damage_dice_used("creature", "goblin", "bite",
                                 feats=["improved_natural_attack_bite"],
                                 natural_attacks=attacks)
    assert dice == "1d8", f"Expected 1d8 (1d6 upgraded), got {dice!r}"


# ===========================================================================
# INA-002: improved_natural_attack_claw + claw 1d4 → resolves as 1d6
# ===========================================================================

def test_ina002_claw_1d4_upgrades_to_1d6():
    """INA-002: claw with 1d4 base + improved_natural_attack_claw → damage resolves as 1d6."""
    attacks = [{"name": "claw", "damage": "1d4", "damage_type": "slashing", "is_primary": True}]
    dice = _get_damage_dice_used("creature", "goblin", "claw",
                                 feats=["improved_natural_attack_claw"],
                                 natural_attacks=attacks)
    assert dice == "1d6", f"Expected 1d6 (1d4 upgraded), got {dice!r}"


# ===========================================================================
# INA-003: No INA feat → damage dice unchanged
# ===========================================================================

def test_ina003_no_feat_damage_unchanged():
    """INA-003: Without INA feat, damage dice stay at base value (regression guard)."""
    attacks = [{"name": "bite", "damage": "1d6", "damage_type": "piercing", "is_primary": True}]
    dice = _get_damage_dice_used("creature", "goblin", "bite",
                                 feats=[],
                                 natural_attacks=attacks)
    assert dice == "1d6", f"Expected 1d6 (unchanged), got {dice!r}"


# ===========================================================================
# INA-004: INA feat for bite, attack is claw → claw dice not upgraded
# ===========================================================================

def test_ina004_feat_type_mismatch_no_upgrade():
    """INA-004: improved_natural_attack_bite feat does not upgrade claw damage."""
    attacks = [
        {"name": "bite", "damage": "1d6", "damage_type": "piercing", "is_primary": True},
        {"name": "claw", "damage": "1d4", "damage_type": "slashing", "is_primary": False},
    ]
    dice = _get_damage_dice_used("creature", "goblin", "claw",
                                 feats=["improved_natural_attack_bite"],  # bite feat, not claw
                                 natural_attacks=attacks)
    assert dice == "1d4", f"Expected 1d4 (claw not upgraded by bite feat), got {dice!r}"


# ===========================================================================
# INA-005: improved_natural_attack_bite, bite = 1d8 → resolves as 2d6
# ===========================================================================

def test_ina005_bite_1d8_upgrades_to_2d6():
    """INA-005: bite with 1d8 base + INA feat → resolves as 2d6 (step crosses 1d8→2d6 boundary)."""
    attacks = [{"name": "bite", "damage": "1d8", "damage_type": "piercing", "is_primary": True}]
    dice = _get_damage_dice_used("creature", "goblin", "bite",
                                 feats=["improved_natural_attack_bite"],
                                 natural_attacks=attacks)
    assert dice == "2d6", f"Expected 2d6 (1d8 upgraded), got {dice!r}"


# ===========================================================================
# INA-006: improved_natural_attack_bite, bite = 2d6 → resolves as 3d6
# ===========================================================================

def test_ina006_bite_2d6_upgrades_to_3d6():
    """INA-006: bite with 2d6 base + INA feat → resolves as 3d6."""
    attacks = [{"name": "bite", "damage": "2d6", "damage_type": "piercing", "is_primary": True}]
    dice = _get_damage_dice_used("creature", "goblin", "bite",
                                 feats=["improved_natural_attack_bite"],
                                 natural_attacks=attacks)
    assert dice == "3d6", f"Expected 3d6 (2d6 upgraded), got {dice!r}"


# ===========================================================================
# INA-007: Entity damage_dice field unchanged after resolve — no permanent mutation
# ===========================================================================

def test_ina007_entity_not_mutated():
    """INA-007: NATURAL_ATTACKS list entry damage field unchanged after resolve."""
    attacks = [{"name": "bite", "damage": "1d6", "damage_type": "piercing", "is_primary": True}]
    creature = _creature(eid="creature",
                         feats=["improved_natural_attack_bite"],
                         natural_attacks=attacks)
    original_attacks = deepcopy(creature[EF.NATURAL_ATTACKS])

    goblin = _goblin(eid="goblin")
    ws = _world({"creature": creature, "goblin": goblin})
    rng = _FixedRNG()
    intent = NaturalAttackIntent(
        attacker_id="creature",
        target_id="goblin",
        attack_name="bite",
        attack_bonus=10,
    )
    _, ws_after = resolve_natural_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)

    # The original entity dict's NATURAL_ATTACKS must be unchanged
    entity_attacks = ws.entities["creature"].get(EF.NATURAL_ATTACKS, [])
    assert entity_attacks == original_attacks, (
        f"Entity NATURAL_ATTACKS mutated: {entity_attacks} != {original_attacks}"
    )
    # Verify the damage in the dict is still 1d6 (not 1d8)
    assert entity_attacks[0]["damage"] == "1d6", (
        f"damage field was mutated: {entity_attacks[0]['damage']!r}"
    )


# ===========================================================================
# INA-008: MA-008 regression guard — Multiattack penalty unaffected by INA commit
# ===========================================================================

def test_ina008_multiattack_penalty_unaffected_by_ina():
    """INA-008: INA upgrade does not alter Multiattack penalty calculation."""
    attacks = [
        {"name": "bite", "damage": "1d8", "damage_type": "piercing", "is_primary": True},
        {"name": "claw", "damage": "1d4", "damage_type": "slashing", "is_primary": False},
    ]
    # With both feats: claw gets INA upgrade AND Multiattack secondary penalty
    feats = ["multiattack", "improved_natural_attack_claw"]

    creature = _creature(eid="creature", feats=feats, natural_attacks=attacks)
    goblin = _goblin(eid="goblin")
    ws = _world({"creature": creature, "goblin": goblin})
    rng = _FixedRNG()

    intent = NaturalAttackIntent(
        attacker_id="creature",
        target_id="goblin",
        attack_name="claw",
        attack_bonus=7,
    )
    events, _ = resolve_natural_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)

    # Check attack_bonus (Multiattack: 7 − 2 = 5)
    roll_events = [e for e in events if e.event_type == "attack_roll"]
    assert roll_events, "No attack_roll event emitted"
    assert roll_events[0].payload["attack_bonus"] == 5, (
        f"Expected attack_bonus=5 (7-2 Multiattack), got {roll_events[0].payload['attack_bonus']}"
    )

    # Check damage_dice (INA upgrade: 1d4 → 1d6)
    dmg_events = [e for e in events if e.event_type == "damage_roll"]
    assert dmg_events, "No damage_roll event emitted"
    assert dmg_events[0].payload["damage_dice"] == "1d6", (
        f"Expected damage_dice=1d6 (INA upgrade), got {dmg_events[0].payload['damage_dice']!r}"
    )
