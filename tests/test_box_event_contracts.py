"""WO-046: Box Event Contract Tests

Validates the typed event payload schemas at the Box→Lens boundary.
Tests ensure:
1. Schema construction from real resolver payloads
2. Schema validation catches missing required fields
3. Schema validation passes through unknown event types
4. Orchestrator extraction uses validated payloads
5. Real Box events conform to schemas (integration)

Test Categories:
1. Schema Construction (10 tests)
2. Validation Function (8 tests)
3. Integration — Real Resolver Events (6 tests)

Total: 24 tests
"""

import pytest
from dataclasses import FrozenInstanceError

from aidm.schemas.box_events import (
    TurnStartPayload,
    TurnEndPayload,
    AttackRollPayload,
    DamageRollPayload,
    HPChangedPayload,
    EntityDefeatedPayload,
    SpellCastPayload,
    SaveRolledPayload,
    ConditionAppliedPayload,
    ConditionRemovedPayload,
    PAYLOAD_SCHEMAS,
    EventValidationError,
    validate_event_payload,
    validate_required_fields,
)
from aidm.core.event_log import Event
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


# ======================================================================
# CATEGORY 1: SCHEMA CONSTRUCTION (10 tests)
# ======================================================================


class TestSchemaConstruction:
    """Verify schemas construct correctly from resolver-shaped payloads."""

    def test_turn_start_from_dict(self):
        """TurnStartPayload from play_loop payload."""
        payload = {"turn_index": 0, "actor_id": "pc_fighter", "actor_team": "party"}
        p = TurnStartPayload(**payload)
        assert p.turn_index == 0
        assert p.actor_id == "pc_fighter"
        assert p.actor_team == "party"

    def test_turn_end_from_dict(self):
        """TurnEndPayload from play_loop payload."""
        payload = {"turn_index": 0, "actor_id": "pc_fighter", "events_emitted": 5}
        p = TurnEndPayload(**payload)
        assert p.events_emitted == 5

    def test_attack_roll_single_attack(self):
        """AttackRollPayload from single attack resolver."""
        payload = {
            "attacker_id": "pc_fighter",
            "target_id": "goblin_1",
            "d20_result": 15,
            "attack_bonus": 5,
            "condition_modifier": 0,
            "mounted_bonus": 0,
            "terrain_higher_ground": 0,
            "feat_modifier": 0,
            "cover_type": None,
            "cover_ac_bonus": 0,
            "total": 20,
            "target_ac": 15,
            "target_base_ac": 15,
            "target_ac_modifier": 0,
            "hit": True,
            "is_natural_20": False,
            "is_natural_1": False,
        }
        p = AttackRollPayload(**payload)
        assert p.hit is True
        assert p.d20_result == 15
        assert p.total == 20
        assert p.attack_index is None  # Not a full attack

    def test_attack_roll_full_attack(self):
        """AttackRollPayload from full attack resolver (superset)."""
        payload = {
            "attacker_id": "pc_fighter",
            "target_id": "goblin_1",
            "attack_index": 0,
            "d20_result": 18,
            "attack_bonus": 8,
            "total": 26,
            "target_ac": 15,
            "hit": True,
            "is_natural_20": False,
            "is_natural_1": False,
            "is_threat": True,
            "is_critical": True,
            "confirmation_total": 22,
        }
        p = AttackRollPayload(**payload)
        assert p.attack_index == 0
        assert p.is_critical is True
        assert p.confirmation_total == 22

    def test_damage_roll_from_dict(self):
        """DamageRollPayload from resolver payload (via validation)."""
        payload = {
            "attacker_id": "pc_fighter",
            "target_id": "goblin_1",
            "damage_dice": "1d8",
            "damage_rolls": [6],
            "damage_bonus": 2,
            "str_modifier": 2,
            "damage_total": 8,
            "damage_type": "slashing",
        }
        # Direct construction keeps lists; validation converts to tuples
        p = validate_event_payload("damage_roll", payload)
        assert p.damage_total == 8
        assert p.damage_rolls == (6,)
        assert isinstance(p.damage_rolls, tuple)

    def test_hp_changed_attack_variant(self):
        """HPChangedPayload from attack resolver (hp_before/hp_after)."""
        payload = {
            "entity_id": "goblin_1",
            "hp_before": 6,
            "hp_after": 0,
            "delta": -6,
            "source": "attack_damage",
        }
        p = HPChangedPayload(**payload)
        assert p.delta == -6
        assert p.effective_hp_before == 6
        assert p.effective_hp_after == 0

    def test_hp_changed_spell_variant(self):
        """HPChangedPayload from spell resolution (old_hp/new_hp)."""
        payload = {
            "entity_id": "goblin_1",
            "old_hp": 10,
            "new_hp": 3,
            "delta": -7,
            "source": "spell:fireball",
        }
        p = HPChangedPayload(**payload)
        assert p.effective_hp_before == 10
        assert p.effective_hp_after == 3

    def test_entity_defeated_from_dict(self):
        """EntityDefeatedPayload from resolver payload."""
        payload = {
            "entity_id": "goblin_1",
            "hp_final": -2,
            "defeated_by": "pc_fighter",
        }
        p = EntityDefeatedPayload(**payload)
        assert p.entity_id == "goblin_1"
        assert p.hp_final == -2

    def test_spell_cast_from_dict(self):
        """SpellCastPayload from play_loop payload (via validation)."""
        payload = {
            "cast_id": "cast_001",
            "caster_id": "pc_wizard",
            "spell_id": "fireball",
            "spell_name": "Fireball",
            "spell_level": 3,
            "affected_entities": ["goblin_1", "goblin_2"],
            "turn_index": 1,
        }
        p = validate_event_payload("spell_cast", payload)
        assert p.spell_id == "fireball"
        assert p.affected_entities == ("goblin_1", "goblin_2")

    def test_schemas_are_frozen(self):
        """All payload schemas are immutable."""
        p = TurnStartPayload(turn_index=0, actor_id="x", actor_team="party")
        with pytest.raises((AttributeError, FrozenInstanceError)):
            p.turn_index = 1


# ======================================================================
# CATEGORY 2: VALIDATION FUNCTION (8 tests)
# ======================================================================


class TestValidation:
    """Verify validate_event_payload() behavior."""

    def test_validate_known_event_returns_typed(self):
        """Known event type → typed dataclass."""
        payload = {"turn_index": 0, "actor_id": "pc", "actor_team": "party"}
        result = validate_event_payload("turn_start", payload)
        assert isinstance(result, TurnStartPayload)
        assert result.actor_id == "pc"

    def test_validate_unknown_event_returns_none(self):
        """Unknown event type → None (passthrough)."""
        result = validate_event_payload("tactic_selected", {"actor_id": "x"})
        assert result is None

    def test_validate_missing_required_field_raises(self):
        """Missing required field → EventValidationError."""
        payload = {"turn_index": 0, "actor_id": "pc"}  # Missing actor_team
        with pytest.raises(EventValidationError) as exc_info:
            validate_event_payload("turn_start", payload)
        assert "actor_team" in str(exc_info.value)

    def test_validate_attack_roll_with_extras_ignored(self):
        """Extra fields in payload are silently ignored."""
        payload = {
            "attacker_id": "pc",
            "target_id": "goblin",
            "d20_result": 10,
            "attack_bonus": 5,
            "total": 15,
            "target_ac": 14,
            "hit": True,
            "is_natural_20": False,
            "is_natural_1": False,
            "some_future_field": "ignored",
        }
        result = validate_event_payload("attack_roll", payload)
        assert isinstance(result, AttackRollPayload)
        assert result.hit is True

    def test_validate_hp_changed_minimal(self):
        """HPChangedPayload with only required fields."""
        payload = {"entity_id": "goblin_1", "delta": -5, "source": "attack_damage"}
        result = validate_event_payload("hp_changed", payload)
        assert isinstance(result, HPChangedPayload)
        assert result.delta == -5
        assert result.effective_hp_before is None

    def test_validate_list_to_tuple_conversion(self):
        """Lists in payload are converted to tuples for frozen dataclass."""
        payload = {
            "attacker_id": "pc",
            "target_id": "goblin",
            "damage_dice": "1d8",
            "damage_rolls": [3, 5],
            "damage_bonus": 2,
            "str_modifier": 2,
            "damage_total": 12,
            "damage_type": "slashing",
        }
        result = validate_event_payload("damage_roll", payload)
        assert isinstance(result, DamageRollPayload)
        assert result.damage_rolls == (3, 5)
        assert isinstance(result.damage_rolls, tuple)

    def test_validate_required_fields_helper(self):
        """validate_required_fields catches missing fields."""
        payload = {"d20_result": 15, "hit": True}
        with pytest.raises(EventValidationError) as exc_info:
            validate_required_fields(
                "attack_roll", payload, ["d20_result", "total", "hit"]
            )
        assert "total" in str(exc_info.value)

    def test_validate_required_fields_all_present(self):
        """validate_required_fields passes when all fields present."""
        payload = {"d20_result": 15, "total": 20, "hit": True}
        validate_required_fields(
            "attack_roll", payload, ["d20_result", "total", "hit"]
        )  # No exception


# ======================================================================
# CATEGORY 3: INTEGRATION — Real Resolver Events (6 tests)
# ======================================================================


class TestRealResolverIntegration:
    """Validate real Box events conform to schemas."""

    @pytest.fixture
    def combat_world_state(self):
        """World state for combat resolution."""
        return WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "pc_fighter": {
                    EF.ENTITY_ID: "pc_fighter",
                    "name": "Kael",
                    EF.TEAM: "party",
                    EF.HP_CURRENT: 50,
                    EF.HP_MAX: 50,
                    EF.AC: 16,
                    EF.DEFEATED: False,
                    EF.ATTACK_BONUS: 10,
                    EF.BAB: 8,
                    EF.STR_MOD: 4,
                    EF.WEAPON: "longsword",
                    "weapon_damage": "1d8+4",
                    EF.DEX_MOD: 1,
                },
                "goblin_1": {
                    EF.ENTITY_ID: "goblin_1",
                    "name": "Goblin Warrior",
                    EF.TEAM: "enemy",
                    EF.HP_CURRENT: 100,
                    EF.HP_MAX: 100,
                    EF.AC: 10,
                    EF.DEFEATED: False,
                    EF.ATTACK_BONUS: 2,
                },
            },
        )

    def test_real_attack_roll_validates(self, combat_world_state):
        """Real attack_roll events from Box pass validation."""
        from aidm.core.play_loop import (
            execute_turn as box_execute_turn,
            TurnContext as BoxTurnContext,
        )
        from aidm.interaction.intent_bridge import IntentBridge
        from aidm.core.state import FrozenWorldStateView
        from aidm.schemas.intents import DeclaredAttackIntent

        view = FrozenWorldStateView(combat_world_state)
        bridge = IntentBridge()
        declared = DeclaredAttackIntent(target_ref="goblin warrior")
        bridge_result = bridge.resolve_attack("pc_fighter", declared, view)

        rng = RNGManager(master_seed=42)
        ctx = BoxTurnContext(turn_index=0, actor_id="pc_fighter", actor_team="party")
        box_result = box_execute_turn(
            world_state=combat_world_state,
            turn_ctx=ctx,
            combat_intent=bridge_result,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        # Every event should validate or pass through (no exceptions)
        for event in box_result.events:
            validated = validate_event_payload(event.event_type, event.payload)
            if event.event_type in PAYLOAD_SCHEMAS:
                assert validated is not None, (
                    f"Event '{event.event_type}' has schema but validation returned None"
                )

    def test_attack_roll_has_d20_result(self, combat_world_state):
        """Real attack_roll events have d20_result field (not natural_roll)."""
        from aidm.core.play_loop import (
            execute_turn as box_execute_turn,
            TurnContext as BoxTurnContext,
        )
        from aidm.interaction.intent_bridge import IntentBridge
        from aidm.core.state import FrozenWorldStateView
        from aidm.schemas.intents import DeclaredAttackIntent

        view = FrozenWorldStateView(combat_world_state)
        bridge = IntentBridge()
        declared = DeclaredAttackIntent(target_ref="goblin warrior")
        bridge_result = bridge.resolve_attack("pc_fighter", declared, view)

        rng = RNGManager(master_seed=42)
        ctx = BoxTurnContext(turn_index=0, actor_id="pc_fighter", actor_team="party")
        box_result = box_execute_turn(
            world_state=combat_world_state,
            turn_ctx=ctx,
            combat_intent=bridge_result,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        attack_rolls = [e for e in box_result.events if e.event_type == "attack_roll"]
        assert len(attack_rolls) >= 1

        for event in attack_rolls:
            validated = validate_event_payload("attack_roll", event.payload)
            assert isinstance(validated, AttackRollPayload)
            assert 1 <= validated.d20_result <= 20
            assert isinstance(validated.hit, bool)

    def test_hp_changed_validates_on_hit(self, combat_world_state):
        """Real hp_changed events validate when hit occurs."""
        from aidm.core.play_loop import (
            execute_turn as box_execute_turn,
            TurnContext as BoxTurnContext,
        )
        from aidm.interaction.intent_bridge import IntentBridge
        from aidm.core.state import FrozenWorldStateView
        from aidm.schemas.intents import DeclaredAttackIntent

        # Try seeds until we get a hit
        for seed in range(100):
            ws = WorldState(
                ruleset_version="RAW_3.5",
                entities=dict(combat_world_state.entities),
            )
            view = FrozenWorldStateView(ws)
            bridge = IntentBridge()
            declared = DeclaredAttackIntent(target_ref="goblin warrior")
            bridge_result = bridge.resolve_attack("pc_fighter", declared, view)

            rng = RNGManager(master_seed=seed)
            ctx = BoxTurnContext(
                turn_index=0, actor_id="pc_fighter", actor_team="party"
            )
            box_result = box_execute_turn(
                world_state=ws,
                turn_ctx=ctx,
                combat_intent=bridge_result,
                rng=rng,
                next_event_id=0,
                timestamp=0.0,
            )

            hp_events = [
                e for e in box_result.events if e.event_type == "hp_changed"
            ]
            if hp_events:
                for event in hp_events:
                    validated = validate_event_payload("hp_changed", event.payload)
                    assert isinstance(validated, HPChangedPayload)
                    assert validated.delta < 0  # Damage is negative
                    assert validated.effective_hp_before is not None
                return

        pytest.fail("No hit in 100 seeds")

    def test_turn_start_and_end_validate(self, combat_world_state):
        """Real turn_start and turn_end events validate."""
        from aidm.core.play_loop import (
            execute_turn as box_execute_turn,
            TurnContext as BoxTurnContext,
        )
        from aidm.interaction.intent_bridge import IntentBridge
        from aidm.core.state import FrozenWorldStateView
        from aidm.schemas.intents import DeclaredAttackIntent

        view = FrozenWorldStateView(combat_world_state)
        bridge = IntentBridge()
        declared = DeclaredAttackIntent(target_ref="goblin warrior")
        bridge_result = bridge.resolve_attack("pc_fighter", declared, view)

        rng = RNGManager(master_seed=42)
        ctx = BoxTurnContext(turn_index=0, actor_id="pc_fighter", actor_team="party")
        box_result = box_execute_turn(
            world_state=combat_world_state,
            turn_ctx=ctx,
            combat_intent=bridge_result,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        turn_starts = [
            e for e in box_result.events if e.event_type == "turn_start"
        ]
        turn_ends = [e for e in box_result.events if e.event_type == "turn_end"]

        assert len(turn_starts) >= 1
        assert len(turn_ends) >= 1

        for event in turn_starts:
            validated = validate_event_payload("turn_start", event.payload)
            assert isinstance(validated, TurnStartPayload)
            assert validated.actor_id == "pc_fighter"

        for event in turn_ends:
            validated = validate_event_payload("turn_end", event.payload)
            assert isinstance(validated, TurnEndPayload)
            assert validated.events_emitted > 0

    def test_payload_registry_covers_orchestrator_needs(self):
        """PAYLOAD_SCHEMAS covers all event types the orchestrator unpacks."""
        required_types = {
            "turn_start",
            "turn_end",
            "attack_roll",
            "damage_roll",
            "hp_changed",
            "entity_defeated",
            "spell_cast",
        }
        assert required_types.issubset(
            set(PAYLOAD_SCHEMAS.keys())
        ), f"Missing: {required_types - set(PAYLOAD_SCHEMAS.keys())}"

    def test_all_schemas_are_frozen(self):
        """Every schema in PAYLOAD_SCHEMAS is a frozen dataclass."""
        import dataclasses

        for event_type, schema_cls in PAYLOAD_SCHEMAS.items():
            assert dataclasses.is_dataclass(schema_cls), (
                f"{event_type}: {schema_cls} is not a dataclass"
            )
            # Check frozen by attempting construction and mutation
            fields = dataclasses.fields(schema_cls)
            # Build minimal kwargs with defaults where possible
            kwargs = {}
            for f in fields:
                if f.default is not dataclasses.MISSING:
                    continue
                if f.default_factory is not dataclasses.MISSING:
                    continue
                # Required field — provide a test value
                if f.type == "int" or "int" in str(f.type):
                    kwargs[f.name] = 0
                elif f.type == "str" or "str" in str(f.type):
                    kwargs[f.name] = "test"
                elif f.type == "bool" or "bool" in str(f.type):
                    kwargs[f.name] = False
                elif "Tuple" in str(f.type):
                    kwargs[f.name] = ()
                else:
                    kwargs[f.name] = "test"

            instance = schema_cls(**kwargs)
            first_field = fields[0].name
            with pytest.raises((AttributeError, FrozenInstanceError)):
                setattr(instance, first_field, "mutated")
