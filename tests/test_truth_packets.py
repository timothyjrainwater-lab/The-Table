"""Tests for Structured Truth Packets (STPs).

Verifies the trust/transparency system components:
- STPType enumeration
- Payload dataclasses
- StructuredTruthPacket creation and serialization
- STPBuilder factory methods
- STPLog query methods

WO-010: Structured Truth Packets
Reference: RQ-TRUST-001 (Trust & Transparency Research)
"""

import pytest
from aidm.core.truth_packets import (
    STPType,
    StructuredTruthPacket,
    AttackRollPayload,
    DamageRollPayload,
    SavingThrowPayload,
    CoverPayload,
    AoEPayload,
    SkillCheckPayload,
    LOSPayload,
    LOEPayload,
    MovementPayload,
    ConditionPayload,
    STPBuilder,
    STPLog,
    PAYLOAD_REGISTRY,
)


# ==============================================================================
# STP TYPE TESTS
# ==============================================================================

class TestSTPType:
    """Test STPType enumeration."""

    def test_all_types_exist(self):
        """All required STP types exist."""
        assert STPType.ATTACK_ROLL
        assert STPType.DAMAGE_ROLL
        assert STPType.SAVING_THROW
        assert STPType.SKILL_CHECK
        assert STPType.COVER_CALCULATION
        assert STPType.LOS_CHECK
        assert STPType.LOE_CHECK
        assert STPType.AOE_RESOLUTION
        assert STPType.MOVEMENT
        assert STPType.CONDITION_APPLIED
        assert STPType.CONDITION_REMOVED

    def test_enum_values_are_strings(self):
        """All STPType values are strings."""
        for stp_type in STPType:
            assert isinstance(stp_type.value, str)

    def test_type_count(self):
        """Verify expected number of types."""
        assert len(STPType) == 11


# ==============================================================================
# ATTACK ROLL PAYLOAD TESTS
# ==============================================================================

class TestAttackRollPayload:
    """Test AttackRollPayload dataclass."""

    def test_creation(self):
        """Create AttackRollPayload with all fields."""
        payload = AttackRollPayload(
            base_roll=15,
            attack_bonus=7,
            total_roll=24,
            target_ac=18,
            hit=True,
            critical_threat=False,
            critical_confirmed=False,
            modifiers=(("flanking", 2),),
        )
        assert payload.base_roll == 15
        assert payload.attack_bonus == 7
        assert payload.total_roll == 24
        assert payload.hit is True

    def test_serialization_round_trip(self):
        """AttackRollPayload serializes and deserializes correctly."""
        payload = AttackRollPayload(
            base_roll=20,
            attack_bonus=5,
            total_roll=27,
            target_ac=20,
            hit=True,
            critical_threat=True,
            critical_confirmed=True,
            modifiers=(("flanking", 2), ("bless", 1)),
        )
        data = payload.to_dict()
        restored = AttackRollPayload.from_dict(data)
        assert restored.base_roll == payload.base_roll
        assert restored.total_roll == payload.total_roll
        assert restored.critical_confirmed == payload.critical_confirmed
        assert restored.modifiers == payload.modifiers

    def test_immutability(self):
        """AttackRollPayload is immutable."""
        payload = AttackRollPayload(
            base_roll=10, attack_bonus=5, total_roll=15,
            target_ac=15, hit=True, critical_threat=False,
            critical_confirmed=False, modifiers=(),
        )
        with pytest.raises(Exception):
            payload.hit = False


# ==============================================================================
# DAMAGE ROLL PAYLOAD TESTS
# ==============================================================================

class TestDamageRollPayload:
    """Test DamageRollPayload dataclass."""

    def test_creation(self):
        """Create DamageRollPayload with all fields."""
        payload = DamageRollPayload(
            dice="2d6+4",
            rolls=(4, 5),
            base_damage=9,
            damage_type="slashing",
            modifiers=(("power attack", 4),),
            total_damage=13,
            damage_reduced=5,
            final_damage=8,
        )
        assert payload.dice == "2d6+4"
        assert payload.rolls == (4, 5)
        assert payload.final_damage == 8

    def test_calculation_verification(self):
        """Verify damage calculation correctness."""
        # 2d6+4 rolls [3, 4] = 7 base, +4 str mod = 11 total, 5 DR = 6 final
        payload = DamageRollPayload(
            dice="2d6+4",
            rolls=(3, 4),
            base_damage=7,
            damage_type="slashing",
            modifiers=(("strength", 4),),
            total_damage=11,
            damage_reduced=5,
            final_damage=6,
        )
        assert payload.base_damage == sum(payload.rolls)
        modifier_total = sum(m[1] for m in payload.modifiers)
        assert payload.total_damage == payload.base_damage + modifier_total
        assert payload.final_damage == payload.total_damage - payload.damage_reduced

    def test_serialization_round_trip(self):
        """DamageRollPayload serializes and deserializes correctly."""
        payload = DamageRollPayload(
            dice="1d8+3",
            rolls=(6,),
            base_damage=6,
            damage_type="piercing",
            modifiers=(("strength", 3),),
            total_damage=9,
            damage_reduced=0,
            final_damage=9,
        )
        data = payload.to_dict()
        restored = DamageRollPayload.from_dict(data)
        assert restored.dice == payload.dice
        assert restored.rolls == payload.rolls
        assert restored.final_damage == payload.final_damage


# ==============================================================================
# SAVING THROW PAYLOAD TESTS
# ==============================================================================

class TestSavingThrowPayload:
    """Test SavingThrowPayload dataclass."""

    def test_creation(self):
        """Create SavingThrowPayload with all fields."""
        payload = SavingThrowPayload(
            save_type="ref",
            base_roll=14,
            save_bonus=6,
            dc=15,
            total_roll=20,
            success=True,
            modifiers=(),
        )
        assert payload.save_type == "ref"
        assert payload.success is True

    def test_success_logic(self):
        """Verify success determination."""
        # Success: total >= DC
        success_payload = SavingThrowPayload(
            save_type="will", base_roll=10, save_bonus=5, dc=15,
            total_roll=15, success=True, modifiers=(),
        )
        assert success_payload.total_roll >= success_payload.dc
        assert success_payload.success is True

        # Failure: total < DC
        fail_payload = SavingThrowPayload(
            save_type="fort", base_roll=5, save_bonus=3, dc=15,
            total_roll=8, success=False, modifiers=(),
        )
        assert fail_payload.total_roll < fail_payload.dc
        assert fail_payload.success is False

    def test_serialization_round_trip(self):
        """SavingThrowPayload serializes and deserializes correctly."""
        payload = SavingThrowPayload(
            save_type="fort",
            base_roll=12,
            save_bonus=8,
            dc=18,
            total_roll=22,
            success=True,
            modifiers=(("cloak of resistance", 2),),
        )
        data = payload.to_dict()
        restored = SavingThrowPayload.from_dict(data)
        assert restored.save_type == payload.save_type
        assert restored.success == payload.success
        assert restored.modifiers == payload.modifiers


# ==============================================================================
# COVER PAYLOAD TESTS
# ==============================================================================

class TestCoverPayload:
    """Test CoverPayload dataclass."""

    def test_creation(self):
        """Create CoverPayload with all fields."""
        payload = CoverPayload(
            attacker_pos={"x": 0, "y": 0},
            defender_pos={"x": 3, "y": 3},
            lines_traced=4,
            lines_blocked=2,
            cover_degree="partial",
            ac_bonus=4,
            reflex_bonus=2,
        )
        assert payload.cover_degree == "partial"
        assert payload.ac_bonus == 4

    def test_from_cover_result(self):
        """CoverPayload can be created from cover calculation result."""
        cover_result = {
            "attacker_pos": {"x": 5, "y": 5},
            "defender_pos": {"x": 7, "y": 8},
            "lines_traced": 4,
            "lines_blocked": 1,
            "cover_degree": "partial",
            "ac_bonus": 4,
            "reflex_bonus": 2,
        }
        payload = CoverPayload(
            attacker_pos=cover_result["attacker_pos"],
            defender_pos=cover_result["defender_pos"],
            lines_traced=cover_result["lines_traced"],
            lines_blocked=cover_result["lines_blocked"],
            cover_degree=cover_result["cover_degree"],
            ac_bonus=cover_result["ac_bonus"],
            reflex_bonus=cover_result["reflex_bonus"],
        )
        assert payload.lines_blocked == 1
        assert payload.cover_degree == "partial"

    def test_serialization_round_trip(self):
        """CoverPayload serializes and deserializes correctly."""
        payload = CoverPayload(
            attacker_pos={"x": 0, "y": 0},
            defender_pos={"x": 5, "y": 5},
            lines_traced=4,
            lines_blocked=4,
            cover_degree="total",
            ac_bonus=0,
            reflex_bonus=0,
        )
        data = payload.to_dict()
        restored = CoverPayload.from_dict(data)
        assert restored.cover_degree == payload.cover_degree
        assert restored.attacker_pos == payload.attacker_pos


# ==============================================================================
# AOE PAYLOAD TESTS
# ==============================================================================

class TestAoEPayload:
    """Test AoEPayload dataclass."""

    def test_creation(self):
        """Create AoEPayload with all fields."""
        payload = AoEPayload(
            origin={"x": 10, "y": 10},
            shape="burst",
            radius_ft=20,
            affected_squares=({"x": 9, "y": 9}, {"x": 10, "y": 10}, {"x": 11, "y": 11}),
            affected_entities=("goblin_1", "goblin_2"),
            save_dc=15,
            damage_dice="6d6",
        )
        assert payload.shape == "burst"
        assert payload.radius_ft == 20
        assert len(payload.affected_entities) == 2

    def test_multiple_entities(self):
        """AoEPayload tracks multiple affected entities."""
        payload = AoEPayload(
            origin={"x": 5, "y": 5},
            shape="cone",
            radius_ft=30,
            affected_squares=tuple({"x": x, "y": 5} for x in range(6, 12)),
            affected_entities=("orc_1", "orc_2", "orc_3", "orc_4"),
            save_dc=17,
            damage_dice="6d6",
        )
        assert len(payload.affected_entities) == 4
        assert "orc_3" in payload.affected_entities

    def test_serialization_round_trip(self):
        """AoEPayload serializes and deserializes correctly."""
        payload = AoEPayload(
            origin={"x": 0, "y": 0},
            shape="line",
            radius_ft=60,
            affected_squares=({"x": 0, "y": 0}, {"x": 1, "y": 0}),
            affected_entities=("target_1",),
            save_dc=18,
            damage_dice="8d6",
        )
        data = payload.to_dict()
        restored = AoEPayload.from_dict(data)
        assert restored.shape == payload.shape
        assert restored.affected_entities == payload.affected_entities


# ==============================================================================
# STRUCTURED TRUTH PACKET TESTS
# ==============================================================================

class TestStructuredTruthPacket:
    """Test StructuredTruthPacket dataclass."""

    def test_creation_with_all_fields(self):
        """Create STP with all fields."""
        stp = StructuredTruthPacket(
            packet_id="test-123",
            packet_type=STPType.ATTACK_ROLL,
            turn=1,
            initiative_count=15,
            actor_id="fighter_1",
            target_id="goblin_1",
            timestamp=1234567890000,
            payload={"base_roll": 15},
            rule_citations=("PHB p.145",),
        )
        assert stp.packet_id == "test-123"
        assert stp.packet_type == STPType.ATTACK_ROLL
        assert stp.actor_id == "fighter_1"

    def test_immutability(self):
        """StructuredTruthPacket is immutable."""
        stp = StructuredTruthPacket(
            packet_id="test-123",
            packet_type=STPType.ATTACK_ROLL,
            turn=1,
            initiative_count=15,
            actor_id="fighter_1",
            target_id="goblin_1",
            timestamp=1234567890000,
            payload={},
            rule_citations=(),
        )
        with pytest.raises(Exception):
            stp.turn = 2

    def test_serialization_round_trip(self):
        """STP serializes and deserializes correctly."""
        stp = StructuredTruthPacket(
            packet_id="test-456",
            packet_type=STPType.DAMAGE_ROLL,
            turn=2,
            initiative_count=10,
            actor_id="rogue_1",
            target_id="orc_1",
            timestamp=1234567890000,
            payload={"dice": "2d6+3", "final_damage": 10},
            rule_citations=("PHB p.134", "PHB p.140"),
        )
        data = stp.to_dict()
        restored = StructuredTruthPacket.from_dict(data)
        assert restored.packet_id == stp.packet_id
        assert restored.packet_type == stp.packet_type
        assert restored.payload == stp.payload
        assert restored.rule_citations == stp.rule_citations

    def test_optional_target(self):
        """STP can have None target_id."""
        stp = StructuredTruthPacket(
            packet_id="test-789",
            packet_type=STPType.SAVING_THROW,
            turn=1,
            initiative_count=5,
            actor_id="wizard_1",
            target_id=None,
            timestamp=1234567890000,
            payload={},
            rule_citations=(),
        )
        assert stp.target_id is None


# ==============================================================================
# STP BUILDER TESTS
# ==============================================================================

class TestSTPBuilder:
    """Test STPBuilder factory class."""

    def test_attack_roll_builds_correct_stp(self):
        """attack_roll builds correct STP with calculated values."""
        builder = STPBuilder(turn=1, initiative=15)
        stp = builder.attack_roll(
            actor_id="fighter_1",
            target_id="goblin_1",
            base_roll=14,
            attack_bonus=7,
            target_ac=16,
            modifiers=[("flanking", 2)],
            citations=["PHB p.145"],
        )

        assert stp.packet_type == STPType.ATTACK_ROLL
        assert stp.actor_id == "fighter_1"
        assert stp.target_id == "goblin_1"
        assert stp.turn == 1
        assert stp.initiative_count == 15

        # Verify payload calculations
        payload = stp.payload
        assert payload["base_roll"] == 14
        assert payload["attack_bonus"] == 7
        assert payload["total_roll"] == 14 + 7 + 2  # 23
        assert payload["hit"] is True  # 23 >= 16

    def test_attack_roll_natural_20_always_hits(self):
        """Natural 20 always hits regardless of AC."""
        builder = STPBuilder(turn=1, initiative=10)
        stp = builder.attack_roll(
            actor_id="peasant",
            target_id="dragon",
            base_roll=20,
            attack_bonus=1,
            target_ac=50,  # Very high AC
            modifiers=[],
            citations=["PHB p.145"],
            critical_threat=True,
        )
        assert stp.payload["hit"] is True
        assert stp.payload["critical_threat"] is True

    def test_damage_roll_calculates_totals(self):
        """damage_roll calculates totals correctly."""
        builder = STPBuilder(turn=1, initiative=15)
        stp = builder.damage_roll(
            actor_id="fighter_1",
            target_id="orc_1",
            dice="2d6+4",
            rolls=[4, 5],
            damage_type="slashing",
            modifiers=[("strength", 4)],
            dr=5,
            citations=["PHB p.134"],
        )

        payload = stp.payload
        assert payload["base_damage"] == 9  # 4 + 5
        assert payload["total_damage"] == 13  # 9 + 4
        assert payload["damage_reduced"] == 5
        assert payload["final_damage"] == 8  # 13 - 5

    def test_damage_roll_dr_cannot_exceed_damage(self):
        """Damage reduction is capped at total damage."""
        builder = STPBuilder(turn=1, initiative=10)
        stp = builder.damage_roll(
            actor_id="wizard_1",
            target_id="golem_1",
            dice="1d4",
            rolls=[2],
            damage_type="bludgeoning",
            modifiers=[],
            dr=10,  # More than damage
            citations=["PHB p.134"],
        )

        payload = stp.payload
        assert payload["total_damage"] == 2
        assert payload["damage_reduced"] == 2  # Capped at total
        assert payload["final_damage"] == 0

    def test_saving_throw_determines_success(self):
        """saving_throw determines success based on roll vs DC."""
        builder = STPBuilder(turn=1, initiative=10)

        # Success case
        success_stp = builder.saving_throw(
            actor_id="rogue_1",
            save_type="ref",
            base_roll=12,
            save_bonus=8,
            dc=18,
            modifiers=[("evasion_item", 2)],
            citations=["PHB p.136"],
        )
        assert success_stp.payload["success"] is True
        assert success_stp.payload["total_roll"] == 22  # 12 + 8 + 2

        # Failure case
        fail_stp = builder.saving_throw(
            actor_id="fighter_1",
            save_type="ref",
            base_roll=5,
            save_bonus=2,
            dc=18,
            modifiers=[],
            citations=["PHB p.136"],
        )
        assert fail_stp.payload["success"] is False
        assert fail_stp.payload["total_roll"] == 7

    def test_cover_calculation_uses_cover_result(self):
        """cover_calculation uses provided cover result."""
        builder = STPBuilder(turn=1, initiative=10)
        cover_result = {
            "attacker_pos": {"x": 0, "y": 0},
            "defender_pos": {"x": 5, "y": 5},
            "lines_traced": 4,
            "lines_blocked": 2,
            "cover_degree": "partial",
            "ac_bonus": 4,
            "reflex_bonus": 2,
        }

        stp = builder.cover_calculation(
            attacker_id="archer_1",
            defender_id="goblin_1",
            cover_result=cover_result,
            citations=["DMG p.20"],
        )

        payload = stp.payload
        assert payload["cover_degree"] == "partial"
        assert payload["ac_bonus"] == 4
        assert payload["lines_blocked"] == 2

    def test_aoe_resolution_lists_affected(self):
        """aoe_resolution lists affected entities."""
        builder = STPBuilder(turn=1, initiative=10)
        stp = builder.aoe_resolution(
            actor_id="wizard_1",
            origin={"x": 10, "y": 10},
            shape="burst",
            radius_ft=20,
            affected_squares=[{"x": 9, "y": 9}, {"x": 10, "y": 10}],
            affected_entities=["goblin_1", "goblin_2", "orc_1"],
            save_dc=17,
            damage_dice="6d6",
            citations=["PHB p.224"],
        )

        payload = stp.payload
        assert payload["shape"] == "burst"
        assert len(payload["affected_entities"]) == 3
        assert "goblin_2" in payload["affected_entities"]

    def test_builder_generates_unique_ids(self):
        """Builder generates unique packet IDs."""
        builder = STPBuilder(turn=1, initiative=10)
        stp1 = builder.attack_roll(
            actor_id="a", target_id="b", base_roll=10,
            attack_bonus=5, target_ac=15, modifiers=[], citations=[],
        )
        stp2 = builder.attack_roll(
            actor_id="a", target_id="b", base_roll=10,
            attack_bonus=5, target_ac=15, modifiers=[], citations=[],
        )
        assert stp1.packet_id != stp2.packet_id


# ==============================================================================
# STP LOG TESTS
# ==============================================================================

class TestSTPLog:
    """Test STPLog collection class."""

    def test_append_stores_stp(self):
        """append stores STP in log."""
        log = STPLog()
        stp = StructuredTruthPacket(
            packet_id="test-1",
            packet_type=STPType.ATTACK_ROLL,
            turn=1,
            initiative_count=15,
            actor_id="fighter_1",
            target_id="goblin_1",
            timestamp=1234567890000,
            payload={},
            rule_citations=(),
        )
        log.append(stp)
        assert len(log) == 1
        assert log.get_all()[0] == stp

    def test_get_by_turn_filters(self):
        """get_by_turn filters correctly."""
        log = STPLog()
        builder = STPBuilder(turn=1, initiative=10)

        # Add packets from different turns
        stp_t1 = builder.attack_roll(
            actor_id="a", target_id="b", base_roll=10,
            attack_bonus=5, target_ac=15, modifiers=[], citations=[],
        )
        log.append(stp_t1)

        builder2 = STPBuilder(turn=2, initiative=10)
        stp_t2 = builder2.attack_roll(
            actor_id="a", target_id="b", base_roll=10,
            attack_bonus=5, target_ac=15, modifiers=[], citations=[],
        )
        log.append(stp_t2)

        turn_1_packets = log.get_by_turn(1)
        assert len(turn_1_packets) == 1
        assert turn_1_packets[0].turn == 1

        turn_2_packets = log.get_by_turn(2)
        assert len(turn_2_packets) == 1
        assert turn_2_packets[0].turn == 2

    def test_get_by_actor_filters(self):
        """get_by_actor filters correctly."""
        log = STPLog()
        builder = STPBuilder(turn=1, initiative=10)

        stp_fighter = builder.attack_roll(
            actor_id="fighter_1", target_id="goblin_1", base_roll=10,
            attack_bonus=5, target_ac=15, modifiers=[], citations=[],
        )
        stp_rogue = builder.attack_roll(
            actor_id="rogue_1", target_id="goblin_1", base_roll=15,
            attack_bonus=8, target_ac=15, modifiers=[], citations=[],
        )
        log.append(stp_fighter)
        log.append(stp_rogue)

        fighter_packets = log.get_by_actor("fighter_1")
        assert len(fighter_packets) == 1
        assert fighter_packets[0].actor_id == "fighter_1"

        rogue_packets = log.get_by_actor("rogue_1")
        assert len(rogue_packets) == 1
        assert rogue_packets[0].actor_id == "rogue_1"

    def test_get_by_type_filters(self):
        """get_by_type filters correctly."""
        log = STPLog()
        builder = STPBuilder(turn=1, initiative=10)

        attack_stp = builder.attack_roll(
            actor_id="fighter_1", target_id="goblin_1", base_roll=15,
            attack_bonus=7, target_ac=15, modifiers=[], citations=[],
        )
        damage_stp = builder.damage_roll(
            actor_id="fighter_1", target_id="goblin_1", dice="1d8+4",
            rolls=[6], damage_type="slashing", modifiers=[("strength", 4)],
            dr=0, citations=[],
        )
        log.append(attack_stp)
        log.append(damage_stp)

        attack_packets = log.get_by_type(STPType.ATTACK_ROLL)
        assert len(attack_packets) == 1
        assert attack_packets[0].packet_type == STPType.ATTACK_ROLL

        damage_packets = log.get_by_type(STPType.DAMAGE_ROLL)
        assert len(damage_packets) == 1
        assert damage_packets[0].packet_type == STPType.DAMAGE_ROLL

    def test_serialization_round_trip(self):
        """STPLog serializes and deserializes correctly."""
        log = STPLog()
        builder = STPBuilder(turn=1, initiative=10)

        for i in range(3):
            stp = builder.attack_roll(
                actor_id=f"actor_{i}", target_id="target", base_roll=10 + i,
                attack_bonus=5, target_ac=15, modifiers=[], citations=[],
            )
            log.append(stp)

        data = log.to_dict()
        restored = STPLog.from_dict(data)

        assert len(restored) == 3
        assert restored.get_all()[0].actor_id == "actor_0"
        assert restored.get_all()[2].payload["base_roll"] == 12


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

class TestIntegration:
    """Integration tests for full combat sequences."""

    def test_full_attack_sequence(self):
        """Full attack sequence: roll, hit, damage."""
        log = STPLog()
        builder = STPBuilder(turn=1, initiative=15)

        # Attack roll
        attack_stp = builder.attack_roll(
            actor_id="fighter_1",
            target_id="orc_1",
            base_roll=17,
            attack_bonus=9,
            target_ac=18,
            modifiers=[("flanking", 2), ("bless", 1)],
            citations=["PHB p.145", "PHB p.156"],
        )
        log.append(attack_stp)

        # Verify hit
        assert attack_stp.payload["hit"] is True
        assert attack_stp.payload["total_roll"] == 29  # 17 + 9 + 2 + 1

        # Damage roll (only if hit)
        if attack_stp.payload["hit"]:
            damage_stp = builder.damage_roll(
                actor_id="fighter_1",
                target_id="orc_1",
                dice="2d6+6",
                rolls=[4, 5],
                damage_type="slashing",
                modifiers=[("strength", 4), ("power attack", 2)],
                dr=0,
                citations=["PHB p.134"],
            )
            log.append(damage_stp)

        # Verify sequence
        assert len(log) == 2
        attack_packets = log.get_by_type(STPType.ATTACK_ROLL)
        damage_packets = log.get_by_type(STPType.DAMAGE_ROLL)
        assert len(attack_packets) == 1
        assert len(damage_packets) == 1
        assert damage_packets[0].payload["final_damage"] == 15  # 9 + 4 + 2

    def test_save_or_suck_sequence(self):
        """Save-or-suck spell: AoE, saves, condition application."""
        log = STPLog()
        builder = STPBuilder(turn=2, initiative=20)

        # AoE resolution
        aoe_stp = builder.aoe_resolution(
            actor_id="wizard_1",
            origin={"x": 10, "y": 10},
            shape="burst",
            radius_ft=20,
            affected_squares=[{"x": x, "y": y} for x in range(8, 13) for y in range(8, 13)],
            affected_entities=["goblin_1", "goblin_2", "goblin_3"],
            save_dc=17,
            damage_dice="0",
            citations=["PHB p.280"],
        )
        log.append(aoe_stp)

        # Saving throws for each target
        targets = ["goblin_1", "goblin_2", "goblin_3"]
        rolls = [8, 15, 12]  # Fail, success, fail

        for target, roll in zip(targets, rolls):
            save_stp = builder.saving_throw(
                actor_id=target,
                save_type="will",
                base_roll=roll,
                save_bonus=2,
                dc=17,
                modifiers=[],
                citations=["PHB p.136"],
            )
            log.append(save_stp)

            # Apply condition if failed
            if not save_stp.payload["success"]:
                condition_stp = builder.condition_applied(
                    actor_id="wizard_1",
                    target_id=target,
                    condition_name="frightened",
                    source="Cause Fear spell",
                    duration_rounds=5,
                    save_dc=17,
                    save_type="will",
                    citations=["PHB p.208"],
                )
                log.append(condition_stp)

        # Verify sequence
        aoe_packets = log.get_by_type(STPType.AOE_RESOLUTION)
        save_packets = log.get_by_type(STPType.SAVING_THROW)
        condition_packets = log.get_by_type(STPType.CONDITION_APPLIED)

        assert len(aoe_packets) == 1
        assert len(save_packets) == 3
        assert len(condition_packets) == 2  # Two failed saves

    def test_aoe_with_multiple_targets(self):
        """AoE affects multiple entities with individual saves."""
        log = STPLog()
        builder = STPBuilder(turn=3, initiative=18)

        # Fireball hits 5 targets
        affected = ["orc_1", "orc_2", "orc_3", "goblin_1", "goblin_2"]

        aoe_stp = builder.aoe_resolution(
            actor_id="wizard_1",
            origin={"x": 15, "y": 15},
            shape="burst",
            radius_ft=20,
            affected_squares=[],  # Simplified
            affected_entities=affected,
            save_dc=19,
            damage_dice="10d6",
            citations=["PHB p.231"],
        )
        log.append(aoe_stp)

        # Each target makes reflex save
        save_results = [
            ("orc_1", 5, 3, False),   # roll, bonus, success
            ("orc_2", 18, 3, True),
            ("orc_3", 12, 3, False),
            ("goblin_1", 15, 6, True),
            ("goblin_2", 8, 6, False),
        ]

        for target, roll, bonus, expected_success in save_results:
            save_stp = builder.saving_throw(
                actor_id=target,
                save_type="ref",
                base_roll=roll,
                save_bonus=bonus,
                dc=19,
                modifiers=[],
                citations=["PHB p.136"],
            )
            log.append(save_stp)
            assert save_stp.payload["success"] == expected_success

        # 5 affected entities
        assert len(aoe_stp.payload["affected_entities"]) == 5

        # All saves recorded
        save_packets = log.get_by_type(STPType.SAVING_THROW)
        assert len(save_packets) == 5


# ==============================================================================
# ADDITIONAL PAYLOAD TESTS
# ==============================================================================

class TestAdditionalPayloads:
    """Test additional payload types."""

    def test_skill_check_payload(self):
        """SkillCheckPayload creation and serialization."""
        payload = SkillCheckPayload(
            skill_name="Hide",
            base_roll=15,
            skill_bonus=10,
            dc=20,
            total_roll=25,
            success=True,
            modifiers=(),
        )
        assert payload.skill_name == "Hide"
        assert payload.success is True

        data = payload.to_dict()
        restored = SkillCheckPayload.from_dict(data)
        assert restored.skill_name == payload.skill_name

    def test_los_payload(self):
        """LOSPayload creation and serialization."""
        payload = LOSPayload(
            source_pos={"x": 0, "y": 0},
            target_pos={"x": 5, "y": 5},
            has_los=False,
            blocking_cells=({"x": 2, "y": 2}, {"x": 3, "y": 3}),
        )
        assert payload.has_los is False
        assert len(payload.blocking_cells) == 2

        data = payload.to_dict()
        restored = LOSPayload.from_dict(data)
        assert restored.blocking_cells == payload.blocking_cells

    def test_movement_payload(self):
        """MovementPayload creation and serialization."""
        payload = MovementPayload(
            start_pos={"x": 0, "y": 0},
            end_pos={"x": 6, "y": 0},
            path=({"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 0},
                  {"x": 3, "y": 0}, {"x": 4, "y": 0}, {"x": 5, "y": 0}, {"x": 6, "y": 0}),
            distance_ft=30,
            movement_type="walk",
            difficult_terrain_squares=0,
            provoked_aoo_from=("goblin_1",),
        )
        assert payload.distance_ft == 30
        assert payload.movement_type == "walk"
        assert "goblin_1" in payload.provoked_aoo_from

        data = payload.to_dict()
        restored = MovementPayload.from_dict(data)
        assert restored.path == payload.path

    def test_condition_payload(self):
        """ConditionPayload creation and serialization."""
        payload = ConditionPayload(
            condition_name="stunned",
            source="Hold Person spell",
            duration_rounds=3,
            save_dc=16,
            save_type="will",
        )
        assert payload.condition_name == "stunned"
        assert payload.duration_rounds == 3

        data = payload.to_dict()
        restored = ConditionPayload.from_dict(data)
        assert restored.save_dc == payload.save_dc


# ==============================================================================
# BUILDER ADDITIONAL METHODS TESTS
# ==============================================================================

class TestSTPBuilderAdditional:
    """Test additional STPBuilder methods."""

    def test_skill_check_method(self):
        """skill_check builds correct STP."""
        builder = STPBuilder(turn=1, initiative=10)
        stp = builder.skill_check(
            actor_id="rogue_1",
            skill_name="Move Silently",
            base_roll=14,
            skill_bonus=12,
            dc=20,
            modifiers=[("armor check", -2)],
            citations=["PHB p.77"],
        )
        assert stp.packet_type == STPType.SKILL_CHECK
        assert stp.payload["success"] is True  # 14 + 12 - 2 = 24 >= 20

    def test_los_check_method(self):
        """los_check builds correct STP."""
        builder = STPBuilder(turn=1, initiative=10)
        stp = builder.los_check(
            actor_id="archer_1",
            target_id="goblin_1",
            source_pos={"x": 0, "y": 0},
            target_pos={"x": 5, "y": 5},
            has_los=True,
            blocking_cells=[],
            citations=["DMG p.20"],
        )
        assert stp.packet_type == STPType.LOS_CHECK
        assert stp.payload["has_los"] is True

    def test_movement_method(self):
        """movement builds correct STP."""
        builder = STPBuilder(turn=1, initiative=10)
        stp = builder.movement(
            actor_id="fighter_1",
            start_pos={"x": 0, "y": 0},
            end_pos={"x": 4, "y": 0},
            path=[{"x": i, "y": 0} for i in range(5)],
            distance_ft=20,
            movement_type="walk",
            difficult_terrain_squares=0,
            provoked_aoo_from=[],
            citations=["PHB p.147"],
        )
        assert stp.packet_type == STPType.MOVEMENT
        assert stp.payload["distance_ft"] == 20

    def test_condition_applied_method(self):
        """condition_applied builds correct STP."""
        builder = STPBuilder(turn=1, initiative=10)
        stp = builder.condition_applied(
            actor_id="cleric_1",
            target_id="fighter_1",
            condition_name="blessed",
            source="Bless spell",
            duration_rounds=10,
            save_dc=None,
            save_type=None,
            citations=["PHB p.205"],
        )
        assert stp.packet_type == STPType.CONDITION_APPLIED
        assert stp.payload["condition_name"] == "blessed"

    def test_condition_removed_method(self):
        """condition_removed builds correct STP."""
        builder = STPBuilder(turn=5, initiative=10)
        stp = builder.condition_removed(
            actor_id="cleric_1",
            target_id="fighter_1",
            condition_name="frightened",
            source="Remove Fear spell",
            citations=["PHB p.270"],
        )
        assert stp.packet_type == STPType.CONDITION_REMOVED
        assert stp.payload["condition_name"] == "frightened"
