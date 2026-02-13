"""Sneak Attack tests (PHB p.50, WO-050B).

Validates:
- Eligibility: rogue class levels, flanking, denied Dex to AC
- Damage calculation: Xd6 per class level pair
- Critical interaction: NOT multiplied on critical hits (precision damage)
- Immunity: undead, construct, ooze, plant, elemental
- Range limitation: ranged sneak attack limited to 30 feet
- Integration: sneak attack damage in single attack and full attack resolvers
- Event payloads: sneak attack fields in damage_roll events
- Determinism: same seed produces identical sneak attack rolls

Evidence:
- PHB p.50: Rogue class, Sneak Attack feature
- PHB p.153: Flanking rules (eligibility condition)
- PHB p.311: Conditions that deny Dex to AC
"""

import pytest

from aidm.core.sneak_attack import (
    get_sneak_attack_dice,
    is_target_immune,
    is_sneak_attack_eligible,
    roll_sneak_attack_damage,
    calculate_sneak_attack,
    SNEAK_ATTACK_IMMUNE_TYPES,
    SNEAK_ATTACK_MAX_RANGE,
)
from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.full_attack_resolver import resolve_full_attack, FullAttackIntent
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position


# ======================================================================
# HELPERS
# ======================================================================

def make_rogue(level=3, hp=20, ac=15, position=None, team="party", **extras):
    """Create a rogue entity dict."""
    entity = {
        EF.ENTITY_ID: "rogue_1",
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.DEFEATED: False,
        EF.ATTACK_BONUS: 5,
        EF.STR_MOD: 2,
        EF.CLASS_LEVELS: {"rogue": level},
        **extras,
    }
    if position is not None:
        entity[EF.POSITION] = position
    return entity


def make_target(hp=30, ac=15, position=None, team="enemy", creature_type="humanoid", **extras):
    """Create a target entity dict."""
    entity = {
        EF.ENTITY_ID: "target_1",
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.DEFEATED: False,
        **extras,
    }
    if creature_type:
        entity["creature_type"] = creature_type
    if position is not None:
        entity[EF.POSITION] = position
    return entity


def make_ally(position=None, team="party", hp=20, **extras):
    """Create an ally entity for flanking."""
    entity = {
        EF.ENTITY_ID: "ally_1",
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 15,
        EF.DEFEATED: False,
        EF.ATTACK_BONUS: 5,
        **extras,
    }
    if position is not None:
        entity[EF.POSITION] = position
    return entity


def flanking_world(rogue_level=3, creature_type="humanoid", target_extras=None):
    """Create a world state with flanking geometry.

    Rogue at (0,1), Target at (1,1), Ally at (2,1) — 180 degree angle.
    """
    target_extras = target_extras or {}
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "rogue_1": make_rogue(
                level=rogue_level,
                position={"x": 0, "y": 1},
            ),
            "target_1": make_target(
                position={"x": 1, "y": 1},
                creature_type=creature_type,
                **target_extras,
            ),
            "ally_1": make_ally(
                position={"x": 2, "y": 1},
            ),
        }
    )


def denied_dex_world(rogue_level=3, condition_type="flat_footed"):
    """Create a world state where target is denied Dex to AC."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "rogue_1": make_rogue(
                level=rogue_level,
                position={"x": 0, "y": 1},
            ),
            "target_1": make_target(
                position={"x": 1, "y": 1},
                **{
                    EF.CONDITIONS: {
                        condition_type: {
                            "condition_type": condition_type,
                            "source": "test",
                            "modifiers": {
                                "loses_dex_to_ac": True,
                            },
                            "applied_at_event_id": 0,
                        }
                    }
                }
            ),
        }
    )


# ======================================================================
# DICE CALCULATION TESTS
# ======================================================================


class TestSneakAttackDice:
    """PHB p.50: Rogue sneak attack dice progression."""

    def test_no_rogue_levels(self):
        entity = {EF.CLASS_LEVELS: {"fighter": 5}}
        assert get_sneak_attack_dice(entity) == 0

    def test_no_class_levels(self):
        entity = {}
        assert get_sneak_attack_dice(entity) == 0

    def test_rogue_level_1(self):
        """Level 1 rogue: 1d6."""
        entity = {EF.CLASS_LEVELS: {"rogue": 1}}
        assert get_sneak_attack_dice(entity) == 1

    def test_rogue_level_2(self):
        """Level 2 rogue: still 1d6 (increases at odd levels)."""
        entity = {EF.CLASS_LEVELS: {"rogue": 2}}
        assert get_sneak_attack_dice(entity) == 1

    def test_rogue_level_3(self):
        """Level 3 rogue: 2d6."""
        entity = {EF.CLASS_LEVELS: {"rogue": 3}}
        assert get_sneak_attack_dice(entity) == 2

    def test_rogue_level_5(self):
        """Level 5 rogue: 3d6."""
        entity = {EF.CLASS_LEVELS: {"rogue": 5}}
        assert get_sneak_attack_dice(entity) == 3

    def test_rogue_level_10(self):
        """Level 10 rogue: 5d6."""
        entity = {EF.CLASS_LEVELS: {"rogue": 10}}
        assert get_sneak_attack_dice(entity) == 5

    def test_rogue_level_20(self):
        """Level 20 rogue: 10d6."""
        entity = {EF.CLASS_LEVELS: {"rogue": 20}}
        assert get_sneak_attack_dice(entity) == 10

    def test_multiclass_rogue_fighter(self):
        """Multiclass: only rogue levels count."""
        entity = {EF.CLASS_LEVELS: {"rogue": 5, "fighter": 3}}
        assert get_sneak_attack_dice(entity) == 3

    def test_explicit_precision_damage_dice(self):
        """Explicit precision_damage_dice field (prestige class, template, etc.)."""
        entity = {EF.CLASS_LEVELS: {}, "precision_damage_dice": 2}
        assert get_sneak_attack_dice(entity) == 2

    def test_rogue_plus_explicit(self):
        """Rogue levels + explicit precision dice stack."""
        entity = {EF.CLASS_LEVELS: {"rogue": 3}, "precision_damage_dice": 1}
        assert get_sneak_attack_dice(entity) == 3  # 2 from rogue + 1 explicit


# ======================================================================
# TARGET IMMUNITY TESTS
# ======================================================================


class TestTargetImmunity:
    """PHB p.50: Creatures immune to critical hits are immune to sneak attack."""

    @pytest.mark.parametrize("creature_type", list(SNEAK_ATTACK_IMMUNE_TYPES))
    def test_immune_creature_types(self, creature_type):
        """Each immune creature type should block sneak attack."""
        ws = WorldState(
            ruleset_version="3.5e",
            entities={"target_1": make_target(creature_type=creature_type)}
        )
        assert is_target_immune(ws, "target_1") is True

    def test_humanoid_not_immune(self):
        ws = WorldState(
            ruleset_version="3.5e",
            entities={"target_1": make_target(creature_type="humanoid")}
        )
        assert is_target_immune(ws, "target_1") is False

    def test_animal_not_immune(self):
        ws = WorldState(
            ruleset_version="3.5e",
            entities={"target_1": make_target(creature_type="animal")}
        )
        assert is_target_immune(ws, "target_1") is False

    def test_explicit_crit_immune_flag(self):
        ws = WorldState(
            ruleset_version="3.5e",
            entities={"target_1": make_target(immune_to_critical_hits=True)}
        )
        assert is_target_immune(ws, "target_1") is True

    def test_explicit_sneak_attack_immune_flag(self):
        ws = WorldState(
            ruleset_version="3.5e",
            entities={"target_1": make_target(immune_to_sneak_attack=True)}
        )
        assert is_target_immune(ws, "target_1") is True

    def test_nonexistent_target_immune(self):
        ws = WorldState(ruleset_version="3.5e", entities={})
        assert is_target_immune(ws, "target_1") is True

    def test_case_insensitive_creature_type(self):
        ws = WorldState(
            ruleset_version="3.5e",
            entities={"target_1": make_target(creature_type="Undead")}
        )
        assert is_target_immune(ws, "target_1") is True


# ======================================================================
# ELIGIBILITY TESTS
# ======================================================================


class TestSneakAttackEligibility:
    """PHB p.50: Sneak attack eligibility conditions."""

    def test_eligible_flanking(self):
        """Rogue flanking target is eligible for sneak attack."""
        ws = flanking_world(rogue_level=3)
        eligible, reason = is_sneak_attack_eligible(
            ws, "rogue_1", "target_1", is_flanking=True
        )
        assert eligible is True
        assert reason == "flanking"

    def test_eligible_denied_dex(self):
        """Target denied Dex to AC (flat-footed) is eligible."""
        ws = denied_dex_world(rogue_level=3)
        eligible, reason = is_sneak_attack_eligible(
            ws, "rogue_1", "target_1", is_flanking=False
        )
        assert eligible is True
        assert reason == "denied_dex_to_ac"

    def test_not_eligible_no_flanking_no_denied_dex(self):
        """Normal attack without flanking or denied dex: not eligible."""
        ws = WorldState(
            ruleset_version="3.5e",
            entities={
                "rogue_1": make_rogue(level=3, position={"x": 0, "y": 1}),
                "target_1": make_target(position={"x": 1, "y": 1}),
            }
        )
        eligible, reason = is_sneak_attack_eligible(
            ws, "rogue_1", "target_1", is_flanking=False
        )
        assert eligible is False
        assert reason == "target_not_flanked_or_denied_dex"

    def test_not_eligible_no_rogue_levels(self):
        """Fighter cannot sneak attack even when flanking."""
        ws = WorldState(
            ruleset_version="3.5e",
            entities={
                "fighter_1": {
                    EF.ENTITY_ID: "fighter_1",
                    EF.TEAM: "party",
                    EF.HP_CURRENT: 20,
                    EF.CLASS_LEVELS: {"fighter": 5},
                    EF.POSITION: {"x": 0, "y": 1},
                },
                "target_1": make_target(position={"x": 1, "y": 1}),
            }
        )
        eligible, reason = is_sneak_attack_eligible(
            ws, "fighter_1", "target_1", is_flanking=True
        )
        assert eligible is False
        assert reason == "no_sneak_attack_dice"

    def test_not_eligible_immune_target(self):
        """Undead target is immune to sneak attack."""
        ws = flanking_world(rogue_level=3, creature_type="undead")
        eligible, reason = is_sneak_attack_eligible(
            ws, "rogue_1", "target_1", is_flanking=True
        )
        assert eligible is False
        assert reason == "target_immune"

    def test_not_eligible_ranged_beyond_30ft(self):
        """Ranged sneak attack beyond 30 feet is not eligible."""
        ws = flanking_world(rogue_level=3)
        eligible, reason = is_sneak_attack_eligible(
            ws, "rogue_1", "target_1",
            is_flanking=True, is_ranged=True, range_ft=35.0
        )
        assert eligible is False
        assert reason == "range_exceeds_30ft"

    def test_eligible_ranged_within_30ft(self):
        """Ranged sneak attack within 30 feet is eligible."""
        ws = flanking_world(rogue_level=3)
        eligible, reason = is_sneak_attack_eligible(
            ws, "rogue_1", "target_1",
            is_flanking=True, is_ranged=True, range_ft=25.0
        )
        assert eligible is True

    def test_eligible_denied_dex_stunned(self):
        """Stunned target is denied Dex to AC."""
        ws = denied_dex_world(rogue_level=3, condition_type="stunned")
        eligible, reason = is_sneak_attack_eligible(
            ws, "rogue_1", "target_1", is_flanking=False
        )
        assert eligible is True
        assert reason == "denied_dex_to_ac"

    def test_attacker_not_found(self):
        ws = WorldState(
            ruleset_version="3.5e",
            entities={"target_1": make_target()}
        )
        eligible, reason = is_sneak_attack_eligible(
            ws, "nonexistent", "target_1", is_flanking=True
        )
        assert eligible is False
        assert reason == "attacker_not_found"


# ======================================================================
# DAMAGE ROLL TESTS
# ======================================================================


class TestSneakAttackDamageRoll:
    """PHB p.50: Sneak attack damage rolling."""

    def test_roll_produces_correct_count(self):
        """Rolling 3d6 should produce 3 individual rolls."""
        rng = RNGManager(master_seed=42)
        total, dice_expr, rolls = roll_sneak_attack_damage(3, rng)
        assert dice_expr == "3d6"
        assert len(rolls) == 3
        assert all(1 <= r <= 6 for r in rolls)
        assert total == sum(rolls)

    def test_roll_deterministic(self):
        """Same seed produces identical rolls."""
        results = []
        for _ in range(3):
            rng = RNGManager(master_seed=99)
            results.append(roll_sneak_attack_damage(2, rng))
        assert results[0] == results[1] == results[2]

    def test_zero_dice(self):
        """Zero dice returns zero damage."""
        rng = RNGManager(master_seed=42)
        total, dice_expr, rolls = roll_sneak_attack_damage(0, rng)
        assert total == 0
        assert dice_expr == ""
        assert rolls == []

    def test_single_die(self):
        """1d6 roll produces exactly 1 die result."""
        rng = RNGManager(master_seed=42)
        total, dice_expr, rolls = roll_sneak_attack_damage(1, rng)
        assert dice_expr == "1d6"
        assert len(rolls) == 1
        assert 1 <= rolls[0] <= 6
        assert total == rolls[0]


# ======================================================================
# FULL CALCULATION TESTS
# ======================================================================


class TestCalculateSneakAttack:
    """Full sneak attack calculation (eligibility + damage)."""

    def test_eligible_returns_damage(self):
        ws = flanking_world(rogue_level=5)  # 3d6
        rng = RNGManager(master_seed=42)
        eligible, damage, dice_expr, rolls, reason = calculate_sneak_attack(
            ws, "rogue_1", "target_1", is_flanking=True, rng=rng
        )
        assert eligible is True
        assert damage > 0
        assert dice_expr == "3d6"
        assert len(rolls) == 3
        assert reason == "flanking"

    def test_not_eligible_returns_zero(self):
        ws = WorldState(
            ruleset_version="3.5e",
            entities={
                "rogue_1": make_rogue(level=3, position={"x": 0, "y": 1}),
                "target_1": make_target(position={"x": 1, "y": 1}),
            }
        )
        rng = RNGManager(master_seed=42)
        eligible, damage, dice_expr, rolls, reason = calculate_sneak_attack(
            ws, "rogue_1", "target_1", is_flanking=False, rng=rng
        )
        assert eligible is False
        assert damage == 0
        assert dice_expr == ""
        assert rolls == []

    def test_immune_returns_zero(self):
        ws = flanking_world(rogue_level=3, creature_type="undead")
        rng = RNGManager(master_seed=42)
        eligible, damage, dice_expr, rolls, reason = calculate_sneak_attack(
            ws, "rogue_1", "target_1", is_flanking=True, rng=rng
        )
        assert eligible is False
        assert damage == 0
        assert reason == "target_immune"


# ======================================================================
# SINGLE ATTACK RESOLVER INTEGRATION
# ======================================================================


class TestSneakAttackInSingleAttack:
    """Sneak attack wired into attack_resolver.resolve_attack()."""

    def _make_intent(self, attacker="rogue_1", target="target_1"):
        return AttackIntent(
            attacker_id=attacker,
            target_id=target,
            attack_bonus=10,  # High bonus to ensure hit
            weapon=Weapon(
                damage_dice="1d6",
                damage_bonus=0,
                damage_type="piercing",
                critical_multiplier=2,
                critical_range=20,
            )
        )

    def test_sneak_attack_damage_in_event_payload(self):
        """Sneak attack fields appear in damage_roll event when eligible."""
        ws = flanking_world(rogue_level=3)  # 2d6 sneak attack
        intent = self._make_intent()
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)

        # Find damage_roll event
        damage_events = [e for e in events if e.event_type == "damage_roll"]
        if len(damage_events) > 0:
            payload = damage_events[0].payload
            assert "sneak_attack_eligible" in payload
            assert "sneak_attack_dice" in payload
            assert "sneak_attack_rolls" in payload
            assert "sneak_attack_damage" in payload
            assert "sneak_attack_reason" in payload

            if payload["sneak_attack_eligible"]:
                assert payload["sneak_attack_dice"] == "2d6"
                assert len(payload["sneak_attack_rolls"]) == 2
                assert payload["sneak_attack_damage"] > 0
                assert payload["sneak_attack_reason"] == "flanking"

    def test_sneak_attack_adds_damage(self):
        """Sneak attack damage increases total damage when flanking."""
        ws_flanking = flanking_world(rogue_level=5)  # 3d6 sneak attack

        # World without flanking (no ally)
        ws_no_flank = WorldState(
            ruleset_version="3.5e",
            entities={
                "rogue_1": make_rogue(level=5, position={"x": 0, "y": 1}),
                "target_1": make_target(position={"x": 1, "y": 1}),
            }
        )

        intent = self._make_intent()

        # Run both with same seed
        rng1 = RNGManager(master_seed=42)
        events_flanking = resolve_attack(intent, ws_flanking, rng1, next_event_id=0, timestamp=1.0)

        rng2 = RNGManager(master_seed=42)
        events_no_flank = resolve_attack(intent, ws_no_flank, rng2, next_event_id=0, timestamp=1.0)

        # Get damage from both
        dmg_flanking = [e for e in events_flanking if e.event_type == "damage_roll"]
        dmg_no_flank = [e for e in events_no_flank if e.event_type == "damage_roll"]

        if dmg_flanking and dmg_no_flank:
            # Flanking damage should be higher (has sneak attack + flanking attack bonus)
            assert dmg_flanking[0].payload["final_damage"] >= dmg_no_flank[0].payload["final_damage"]

    def test_no_sneak_attack_vs_undead(self):
        """Undead target: sneak attack not eligible even when flanking."""
        ws = flanking_world(rogue_level=5, creature_type="undead")
        intent = self._make_intent()
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)

        damage_events = [e for e in events if e.event_type == "damage_roll"]
        if damage_events:
            payload = damage_events[0].payload
            assert payload["sneak_attack_eligible"] is False
            assert payload["sneak_attack_damage"] == 0

    def test_sneak_attack_not_multiplied_on_critical(self):
        """PHB p.50: Sneak attack damage is NOT multiplied on critical hits.

        This test verifies the pipeline order:
        1. Base damage is multiplied by critical_multiplier
        2. Sneak attack damage is added flat after multiplication
        """
        ws = flanking_world(rogue_level=3)  # 2d6 sneak attack

        # Use a high attack bonus to ensure hit, and weapon with x3 crit
        intent = AttackIntent(
            attacker_id="rogue_1",
            target_id="target_1",
            attack_bonus=50,  # Guarantee hit
            weapon=Weapon(
                damage_dice="1d8",
                damage_bonus=0,
                damage_type="piercing",
                critical_multiplier=3,
                critical_range=1,  # Always threaten (d20 >= 1)
            )
        )

        # Find a seed where we get a critical hit
        for seed in range(200):
            rng = RNGManager(master_seed=seed)
            events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
            damage_events = [e for e in events if e.event_type == "damage_roll"]
            attack_events = [e for e in events if e.event_type == "attack_roll"]

            if attack_events and attack_events[0].payload.get("is_critical"):
                if damage_events:
                    p = damage_events[0].payload
                    # Verify sneak attack was eligible
                    if p["sneak_attack_eligible"]:
                        # base_damage * critical_multiplier + sneak_attack_damage = damage_total
                        base_times_crit = p["base_damage"] * p["critical_multiplier"]
                        expected_total = base_times_crit + p["sneak_attack_damage"]
                        assert p["damage_total"] == expected_total, (
                            f"Sneak attack should NOT be multiplied on crit. "
                            f"Expected {expected_total} but got {p['damage_total']}. "
                            f"base={p['base_damage']}, crit_mult={p['critical_multiplier']}, "
                            f"sa_dmg={p['sneak_attack_damage']}"
                        )
                        return  # Test passed
        pytest.skip("Could not find a seed that produces a critical hit with damage")

    def test_sneak_attack_denied_dex_no_flanking(self):
        """Sneak attack triggers on denied Dex without flanking."""
        ws = denied_dex_world(rogue_level=3)
        intent = self._make_intent()
        rng = RNGManager(master_seed=42)
        events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)

        damage_events = [e for e in events if e.event_type == "damage_roll"]
        if damage_events:
            payload = damage_events[0].payload
            assert payload["sneak_attack_eligible"] is True
            assert payload["sneak_attack_reason"] == "denied_dex_to_ac"

    def test_deterministic_replay_with_sneak_attack(self):
        """Same seed produces identical sneak attack rolls."""
        ws = flanking_world(rogue_level=5)
        intent = self._make_intent()

        results = []
        for _ in range(3):
            rng = RNGManager(master_seed=42)
            events = resolve_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)
            results.append([e.payload for e in events])

        assert results[0] == results[1] == results[2]


# ======================================================================
# FULL ATTACK RESOLVER INTEGRATION
# ======================================================================


class TestSneakAttackInFullAttack:
    """Sneak attack wired into full_attack_resolver.resolve_full_attack()."""

    def test_sneak_attack_on_each_hit(self):
        """Each hit in a full attack should get sneak attack if eligible."""
        ws = flanking_world(rogue_level=5)  # 3d6 per hit
        intent = FullAttackIntent(
            attacker_id="rogue_1",
            target_id="target_1",
            base_attack_bonus=11,  # Two attacks: +11/+6
            weapon=Weapon(
                damage_dice="1d6",
                damage_bonus=0,
                damage_type="piercing",
                critical_multiplier=2,
                critical_range=20,
            )
        )

        rng = RNGManager(master_seed=42)
        events = resolve_full_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)

        # Check full_attack_start event has sneak attack fields
        start_events = [e for e in events if e.event_type == "full_attack_start"]
        assert len(start_events) == 1
        assert start_events[0].payload["sneak_attack_eligible"] is True
        assert start_events[0].payload["sneak_attack_dice"] == 3

        # Each damage_roll should have sneak attack fields
        damage_events = [e for e in events if e.event_type == "damage_roll"]
        for de in damage_events:
            assert "sneak_attack_eligible" in de.payload
            assert "sneak_attack_dice" in de.payload
            assert "sneak_attack_damage" in de.payload
            if de.payload["sneak_attack_eligible"]:
                assert de.payload["sneak_attack_dice"] == "3d6"
                assert len(de.payload["sneak_attack_rolls"]) == 3

    def test_no_sneak_attack_in_full_attack_vs_construct(self):
        """Construct target: no sneak attack on any hit."""
        ws = flanking_world(rogue_level=5, creature_type="construct")
        intent = FullAttackIntent(
            attacker_id="rogue_1",
            target_id="target_1",
            base_attack_bonus=11,
            weapon=Weapon(
                damage_dice="1d6",
                damage_bonus=0,
                damage_type="bludgeoning",
                critical_multiplier=2,
                critical_range=20,
            )
        )

        rng = RNGManager(master_seed=42)
        events = resolve_full_attack(intent, ws, rng, next_event_id=0, timestamp=1.0)

        start_events = [e for e in events if e.event_type == "full_attack_start"]
        assert start_events[0].payload["sneak_attack_eligible"] is False

        damage_events = [e for e in events if e.event_type == "damage_roll"]
        for de in damage_events:
            assert de.payload["sneak_attack_eligible"] is False
            assert de.payload["sneak_attack_damage"] == 0


# ======================================================================
# EDGE CASES
# ======================================================================


class TestSneakAttackEdgeCases:
    """Edge cases and boundary conditions."""

    def test_rogue_level_4_gives_2d6(self):
        """Level 4 rogue: still 2d6 (same as level 3)."""
        entity = {EF.CLASS_LEVELS: {"rogue": 4}}
        assert get_sneak_attack_dice(entity) == 2

    def test_class_levels_not_dict(self):
        """Gracefully handle class_levels that isn't a dict."""
        entity = {EF.CLASS_LEVELS: "rogue 3"}
        assert get_sneak_attack_dice(entity) == 0

    def test_creature_type_empty_string(self):
        """Empty creature type should not be immune."""
        ws = WorldState(
            ruleset_version="3.5e",
            entities={"target_1": make_target(creature_type="")}
        )
        assert is_target_immune(ws, "target_1") is False

    def test_creature_type_none(self):
        """No creature type field should not be immune."""
        ws = WorldState(
            ruleset_version="3.5e",
            entities={"target_1": {
                EF.ENTITY_ID: "target_1",
                EF.HP_CURRENT: 20,
            }}
        )
        assert is_target_immune(ws, "target_1") is False

    def test_flanking_takes_priority_over_denied_dex(self):
        """When both flanking and denied dex apply, flanking reason reported."""
        ws = flanking_world(rogue_level=3, target_extras={
            EF.CONDITIONS: {
                "flat_footed": {
                    "condition_type": "flat_footed",
                    "source": "test",
                    "modifiers": {"loses_dex_to_ac": True},
                    "applied_at_event_id": 0,
                }
            }
        })
        eligible, reason = is_sneak_attack_eligible(
            ws, "rogue_1", "target_1", is_flanking=True
        )
        assert eligible is True
        assert reason == "flanking"  # Flanking checked first
