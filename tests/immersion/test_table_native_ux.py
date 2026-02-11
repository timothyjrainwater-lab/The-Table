"""M3 Table-Native UX Tests.

WO-025: Table-Native UX (Combat Receipts, Ghost Stencils, Judge's Lens)

Tests for:
- Combat receipts and ReceiptTome
- Ghost stencils (burst/cone/line)
- Judge's Lens entity inspection
- Serialization roundtrips
- Pure function verification
"""

import pytest
from datetime import datetime

from aidm.schemas.position import Position
from aidm.schemas.transparency import (
    FilteredSTP,
    TransparencyMode,
    RollBreakdown,
    DamageBreakdown,
    ModifierBreakdown,
)

from aidm.immersion.combat_receipt import (
    CombatReceipt,
    ReceiptTome,
    create_receipt,
    format_parchment,
)

from aidm.immersion.ghost_stencil import (
    StencilShape,
    GhostStencil,
    FrozenStencil,
    create_stencil,
    nudge_stencil,
    rotate_stencil,
    confirm_stencil,
)

from aidm.immersion.judges_lens import (
    HPStatus,
    EntityInspection,
    EntityStateView,
    JudgesLens,
    inspect_entity,
    get_recent_receipts,
    compute_hp_status,
)

from aidm.core.aoe_rasterizer import AoEDirection


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def sample_filtered_stp_ruby():
    """Create sample FilteredSTP in RUBY mode."""
    return FilteredSTP(
        event_id=1,
        event_type="attack_roll",
        mode=TransparencyMode.RUBY,
        final_result="Fighter hits Goblin.",
    )


@pytest.fixture
def sample_filtered_stp_sapphire():
    """Create sample FilteredSTP in SAPPHIRE mode."""
    return FilteredSTP(
        event_id=2,
        event_type="attack_roll",
        mode=TransparencyMode.SAPPHIRE,
        final_result="Fighter attacks Goblin: 18 + 5 = 23 vs AC 15. Hit!",
        summary_text="18 + 5 = 23 vs AC 15",
        actor_name="Fighter",
        target_name="Goblin",
        roll_summaries=(("attack", 18, 23, True),),
    )


@pytest.fixture
def sample_filtered_stp_diamond():
    """Create sample FilteredSTP in DIAMOND mode."""
    mods = (
        ModifierBreakdown(source="BAB", value=3, rule_citation="PHB p.134"),
        ModifierBreakdown(source="STR", value=2, rule_citation="PHB p.134"),
    )
    roll = RollBreakdown(
        roll_type="attack",
        natural_roll=18,
        modifiers=mods,
        total=23,
        target_value=15,
        target_name="AC",
        success=True,
    )
    return FilteredSTP(
        event_id=3,
        event_type="attack_roll",
        mode=TransparencyMode.DIAMOND,
        final_result="Fighter attacks Goblin: d20=18, modifiers +5 = 23 vs AC 15. Hit!",
        summary_text="d20=18, modifiers +5 = 23 vs AC 15",
        actor_name="Fighter",
        target_name="Goblin",
        roll_summaries=(("attack", 18, 23, True),),
        roll_breakdowns=(roll,),
        rule_citations=(("PHB", 134),),
        raw_payload={"attacker_id": "fighter_1", "target_id": "goblin_1"},
    )


@pytest.fixture
def sample_entity_view():
    """Create sample entity state view."""
    return EntityStateView(
        entity_id="fighter_1",
        name="Fighter",
        hp_current=45,
        hp_max=50,
        ac=18,
        position=Position(5, 5),
        conditions=("blessed",),
        has_cover=False,
        stats={"str": 16, "dex": 14, "con": 15},
        modifiers=(("BAB", 5), ("STR", 3)),
        threatened_squares=(Position(5, 4), Position(6, 5)),
    )


# ==============================================================================
# TESTS: Combat Receipts
# ==============================================================================

class TestCombatReceipts:
    """Test combat receipt creation and formatting."""

    def test_create_receipt_ruby(self, sample_filtered_stp_ruby):
        """RUBY receipt should have minimal data."""
        receipt = create_receipt(sample_filtered_stp_ruby, timestamp=1000.0)

        assert receipt.receipt_id == 1
        assert receipt.event_type == "attack_roll"
        assert receipt.mode == TransparencyMode.RUBY
        assert receipt.summary == "Fighter hits Goblin."
        assert receipt.mechanical_breakdown == ""
        assert receipt.actor == ""
        assert receipt.target == ""
        assert len(receipt.rule_citations) == 0

    def test_create_receipt_sapphire(self, sample_filtered_stp_sapphire):
        """SAPPHIRE receipt should include mechanical breakdown."""
        receipt = create_receipt(sample_filtered_stp_sapphire, timestamp=1000.0)

        assert receipt.mode == TransparencyMode.SAPPHIRE
        assert receipt.summary == "Fighter attacks Goblin: 18 + 5 = 23 vs AC 15. Hit!"
        assert receipt.mechanical_breakdown == "18 + 5 = 23 vs AC 15"
        assert receipt.actor == "Fighter"
        assert receipt.target == "Goblin"

    def test_create_receipt_diamond(self, sample_filtered_stp_diamond):
        """DIAMOND receipt should include full details."""
        receipt = create_receipt(sample_filtered_stp_diamond, timestamp=1000.0)

        assert receipt.mode == TransparencyMode.DIAMOND
        assert "d20=18" in receipt.mechanical_breakdown
        assert len(receipt.rule_citations) > 0
        assert receipt.raw_data is not None

    def test_format_parchment_ruby(self, sample_filtered_stp_ruby):
        """Format RUBY receipt as parchment."""
        receipt = create_receipt(sample_filtered_stp_ruby, timestamp=1000.0)
        parchment = format_parchment(receipt, include_timestamp=False)

        assert "Fighter hits Goblin" in parchment
        assert "d20" not in parchment  # No mechanical details

    def test_format_parchment_diamond(self, sample_filtered_stp_diamond):
        """Format DIAMOND receipt with full details."""
        receipt = create_receipt(sample_filtered_stp_diamond, timestamp=1000.0)
        parchment = format_parchment(receipt, include_timestamp=True)

        assert "Receipt #3" in parchment
        assert "d20=18" in parchment
        assert "PHB" in parchment

    def test_receipt_serialization(self, sample_filtered_stp_sapphire):
        """Receipt should serialize/deserialize correctly."""
        receipt = create_receipt(sample_filtered_stp_sapphire, encounter_id="enc_1")
        data = receipt.to_dict()

        restored = CombatReceipt.from_dict(data)

        assert restored.receipt_id == receipt.receipt_id
        assert restored.mode == receipt.mode
        assert restored.summary == receipt.summary
        assert restored.encounter_id == "enc_1"


# ==============================================================================
# TESTS: Receipt Tome
# ==============================================================================

class TestReceiptTome:
    """Test receipt collection and filtering."""

    def test_empty_tome(self):
        """Empty tome should have zero count."""
        tome = ReceiptTome()
        assert tome.count() == 0
        assert len(tome.all()) == 0

    def test_append_receipt(self, sample_filtered_stp_ruby):
        """Should append receipt to tome."""
        tome = ReceiptTome()
        receipt = create_receipt(sample_filtered_stp_ruby)

        tome.append(receipt)

        assert tome.count() == 1
        assert tome.all()[0] == receipt

    def test_filter_by_encounter(self):
        """Should filter receipts by encounter ID."""
        tome = ReceiptTome()

        stp1 = FilteredSTP(1, "attack_roll", TransparencyMode.RUBY, "Hit")
        stp2 = FilteredSTP(2, "damage_roll", TransparencyMode.RUBY, "Damage")

        tome.append(create_receipt(stp1, encounter_id="enc_1"))
        tome.append(create_receipt(stp2, encounter_id="enc_2"))

        filtered = tome.filter_by_encounter("enc_1")

        assert len(filtered) == 1
        assert filtered[0].encounter_id == "enc_1"

    def test_filter_by_actor(self):
        """Should filter receipts by actor name."""
        tome = ReceiptTome()

        stp1 = FilteredSTP(1, "attack_roll", TransparencyMode.SAPPHIRE, "Hit", actor_name="Fighter")
        stp2 = FilteredSTP(2, "attack_roll", TransparencyMode.SAPPHIRE, "Hit", actor_name="Wizard")

        tome.append(create_receipt(stp1))
        tome.append(create_receipt(stp2))

        filtered = tome.filter_by_actor("Fighter")

        assert len(filtered) == 1
        assert filtered[0].actor == "Fighter"

    def test_filter_by_type(self):
        """Should filter receipts by event type."""
        tome = ReceiptTome()

        stp1 = FilteredSTP(1, "attack_roll", TransparencyMode.RUBY, "Hit")
        stp2 = FilteredSTP(2, "damage_roll", TransparencyMode.RUBY, "Damage")

        tome.append(create_receipt(stp1))
        tome.append(create_receipt(stp2))

        filtered = tome.filter_by_type("attack_roll")

        assert len(filtered) == 1
        assert filtered[0].event_type == "attack_roll"

    def test_get_recent(self):
        """Should get N most recent receipts."""
        tome = ReceiptTome()

        for i in range(10):
            stp = FilteredSTP(i, "attack_roll", TransparencyMode.RUBY, f"Event {i}")
            tome.append(create_receipt(stp))

        recent = tome.get_recent(3)

        assert len(recent) == 3
        assert recent[0].receipt_id == 9  # Newest first

    def test_get_for_entity(self):
        """Should get receipts involving entity."""
        tome = ReceiptTome()

        stp1 = FilteredSTP(1, "attack_roll", TransparencyMode.SAPPHIRE, "Hit", actor_name="Fighter", target_name="Goblin")
        stp2 = FilteredSTP(2, "damage_roll", TransparencyMode.SAPPHIRE, "Damage", actor_name="Goblin", target_name="Fighter")
        stp3 = FilteredSTP(3, "attack_roll", TransparencyMode.SAPPHIRE, "Miss", actor_name="Wizard", target_name="Orc")

        tome.append(create_receipt(stp1))
        tome.append(create_receipt(stp2))
        tome.append(create_receipt(stp3))

        fighter_receipts = tome.get_for_entity("Fighter")

        assert len(fighter_receipts) == 2  # Fighter as actor and target

    def test_tome_serialization(self, sample_filtered_stp_sapphire):
        """Tome should serialize/deserialize correctly."""
        tome = ReceiptTome()
        tome.append(create_receipt(sample_filtered_stp_sapphire))

        data = tome.to_dict()
        restored = ReceiptTome.from_dict(data)

        assert restored.count() == tome.count()


# ==============================================================================
# TESTS: Ghost Stencils
# ==============================================================================

class TestGhostStencils:
    """Test ghost stencil creation and manipulation."""

    def test_create_burst_stencil(self):
        """Should create burst stencil."""
        stencil = create_stencil(
            shape=StencilShape.BURST,
            origin=Position(5, 5),
            grid_width=20,
            grid_height=20,
            radius_ft=10,
        )

        assert stencil.shape == StencilShape.BURST
        assert stencil.origin == Position(5, 5)
        assert stencil.radius_ft == 10
        assert stencil.count() > 0

    def test_create_cone_stencil(self):
        """Should create cone stencil."""
        stencil = create_stencil(
            shape=StencilShape.CONE,
            origin=Position(5, 5),
            grid_width=20,
            grid_height=20,
            length_ft=15,
            direction=AoEDirection.N,
        )

        assert stencil.shape == StencilShape.CONE
        assert stencil.direction == AoEDirection.N
        assert stencil.length_ft == 15
        assert stencil.count() > 0

    def test_create_line_stencil(self):
        """Should create line stencil."""
        stencil = create_stencil(
            shape=StencilShape.LINE,
            origin=Position(5, 5),
            grid_width=20,
            grid_height=20,
            length_ft=30,
            direction=AoEDirection.E,
        )

        assert stencil.shape == StencilShape.LINE
        assert stencil.direction == AoEDirection.E
        assert stencil.count() > 0

    def test_nudge_stencil(self):
        """Nudging should create new stencil at offset."""
        original = create_stencil(
            StencilShape.BURST,
            Position(5, 5),
            20,
            20,
            radius_ft=10,
        )

        nudged = nudge_stencil(original, dx=2, dy=-1)

        assert nudged.origin == Position(7, 4)
        assert nudged.shape == original.shape
        assert nudged.radius_ft == original.radius_ft
        # Verify immutability
        assert original.origin == Position(5, 5)

    def test_rotate_stencil_clockwise(self):
        """Should rotate cone stencil clockwise."""
        stencil = create_stencil(
            StencilShape.CONE,
            Position(5, 5),
            20,
            20,
            length_ft=15,
            direction=AoEDirection.N,
        )

        rotated = rotate_stencil(stencil, clockwise=True)

        assert rotated.direction == AoEDirection.NE
        assert rotated.origin == stencil.origin

    def test_rotate_burst_raises_error(self):
        """Rotating burst stencil should raise error."""
        stencil = create_stencil(
            StencilShape.BURST,
            Position(5, 5),
            20,
            20,
            radius_ft=10,
        )

        with pytest.raises(ValueError, match="Cannot rotate burst"):
            rotate_stencil(stencil)

    def test_confirm_stencil(self):
        """Should confirm stencil to frozen state."""
        stencil = create_stencil(
            StencilShape.BURST,
            Position(5, 5),
            20,
            20,
            radius_ft=10,
        )

        frozen = confirm_stencil(
            stencil,
            timestamp=1000.0,
            caster_id="wizard_1",
            spell_name="Fireball",
        )

        assert isinstance(frozen, FrozenStencil)
        assert frozen.stencil == stencil
        assert frozen.confirmed_at == 1000.0
        assert frozen.caster_id == "wizard_1"

    def test_stencil_contains(self):
        """Should check if position is in stencil."""
        stencil = create_stencil(
            StencilShape.BURST,
            Position(5, 5),
            20,
            20,
            radius_ft=5,  # Small radius
        )

        assert stencil.contains(Position(5, 5))  # Origin always included

    def test_stencil_serialization(self):
        """Stencil should serialize/deserialize correctly."""
        stencil = create_stencil(
            StencilShape.CONE,
            Position(5, 5),
            20,
            20,
            length_ft=15,
            direction=AoEDirection.N,
        )

        data = stencil.to_dict()
        restored = GhostStencil.from_dict(data)

        assert restored.shape == stencil.shape
        assert restored.origin == stencil.origin
        assert restored.direction == stencil.direction


# ==============================================================================
# TESTS: Judge's Lens
# ==============================================================================

class TestJudgesLens:
    """Test entity inspection and Judge's Lens."""

    def test_compute_hp_status_full(self):
        """100% HP should be FULL status."""
        status = compute_hp_status(50, 50)
        assert status == HPStatus.FULL

    def test_compute_hp_status_healthy(self):
        """75-99% HP should be HEALTHY."""
        status = compute_hp_status(40, 50)
        assert status == HPStatus.HEALTHY

    def test_compute_hp_status_wounded(self):
        """50-74% HP should be WOUNDED."""
        status = compute_hp_status(30, 50)
        assert status == HPStatus.WOUNDED

    def test_compute_hp_status_bloodied(self):
        """25-49% HP should be BLOODIED."""
        status = compute_hp_status(15, 50)
        assert status == HPStatus.BLOODIED

    def test_compute_hp_status_critical(self):
        """1-24% HP should be CRITICAL."""
        status = compute_hp_status(5, 50)
        assert status == HPStatus.CRITICAL

    def test_compute_hp_status_unconscious(self):
        """0 or negative HP should be UNCONSCIOUS."""
        status = compute_hp_status(0, 50)
        assert status == HPStatus.UNCONSCIOUS

        status = compute_hp_status(-5, 50)
        assert status == HPStatus.UNCONSCIOUS

    def test_inspect_entity_ruby(self, sample_entity_view):
        """RUBY inspection should show minimal data."""
        inspection = inspect_entity(sample_entity_view, TransparencyMode.RUBY)

        assert inspection.name == "Fighter"
        assert inspection.hp_status == HPStatus.HEALTHY
        assert inspection.is_conscious is True
        # RUBY should not expose numbers
        assert inspection.hp_current == 0
        assert inspection.ac == 10

    def test_inspect_entity_sapphire(self, sample_entity_view):
        """SAPPHIRE inspection should show HP/AC/conditions."""
        inspection = inspect_entity(sample_entity_view, TransparencyMode.SAPPHIRE)

        assert inspection.name == "Fighter"
        assert inspection.hp_current == 45
        assert inspection.hp_max == 50
        assert inspection.ac == 18
        assert "blessed" in inspection.active_conditions
        assert inspection.position == Position(5, 5)

    def test_inspect_entity_diamond(self, sample_entity_view):
        """DIAMOND inspection should show full details."""
        inspection = inspect_entity(sample_entity_view, TransparencyMode.DIAMOND)

        assert inspection.stats is not None
        assert inspection.stats["str"] == 16
        assert len(inspection.modifiers) > 0
        assert len(inspection.threatened_squares) == 2

    def test_judges_lens_inspect(self, sample_entity_view):
        """JudgesLens should inspect entity."""
        lens = JudgesLens(default_mode=TransparencyMode.SAPPHIRE)
        inspection = lens.inspect(sample_entity_view)

        assert inspection.mode == TransparencyMode.SAPPHIRE
        assert inspection.name == "Fighter"

    def test_judges_lens_combat_history(self, sample_filtered_stp_sapphire):
        """JudgesLens should retrieve combat history."""
        tome = ReceiptTome()
        receipt = create_receipt(sample_filtered_stp_sapphire)
        tome.append(receipt)

        lens = JudgesLens(receipt_tome=tome)
        history = lens.get_combat_history("Fighter", count=5)

        assert len(history) >= 1

    def test_inspection_serialization(self, sample_entity_view):
        """Inspection should serialize/deserialize correctly."""
        inspection = inspect_entity(sample_entity_view, TransparencyMode.DIAMOND)

        data = inspection.to_dict()
        restored = EntityInspection.from_dict(data)

        assert restored.entity_id == inspection.entity_id
        assert restored.mode == inspection.mode
        assert restored.name == inspection.name


# ==============================================================================
# TESTS: Pure Functions
# ==============================================================================

class TestPureFunctions:
    """Verify pure function behavior (no state mutation)."""

    def test_nudge_stencil_is_pure(self):
        """Nudging stencil should not mutate original."""
        original = create_stencil(
            StencilShape.BURST,
            Position(5, 5),
            20,
            20,
            radius_ft=10,
        )

        original_origin = original.origin
        nudged = nudge_stencil(original, dx=1, dy=1)

        # Original unchanged
        assert original.origin == original_origin
        # New stencil has new origin
        assert nudged.origin == Position(6, 6)

    def test_create_receipt_is_pure(self, sample_filtered_stp_ruby):
        """Creating receipt should not mutate FilteredSTP."""
        original_final_result = sample_filtered_stp_ruby.final_result

        receipt = create_receipt(sample_filtered_stp_ruby)

        # FilteredSTP unchanged (it's frozen anyway)
        assert sample_filtered_stp_ruby.final_result == original_final_result
        assert receipt.summary == original_final_result

    def test_inspect_entity_is_pure(self, sample_entity_view):
        """Inspecting entity should not mutate EntityStateView."""
        original_hp = sample_entity_view.hp_current

        inspection = inspect_entity(sample_entity_view, TransparencyMode.DIAMOND)

        # EntityStateView unchanged (it's frozen anyway)
        assert sample_entity_view.hp_current == original_hp
        assert inspection.hp_current == original_hp


# ==============================================================================
# TESTS: Integration
# ==============================================================================

class TestIntegration:
    """Integration tests across all components."""

    def test_full_workflow(self, sample_filtered_stp_diamond, sample_entity_view):
        """Test full workflow: receipt → tome → lens inspection."""
        # Create receipt from STP
        receipt = create_receipt(sample_filtered_stp_diamond, encounter_id="enc_1")

        # Add to tome
        tome = ReceiptTome()
        tome.append(receipt)

        # Create lens with tome
        lens = JudgesLens(default_mode=TransparencyMode.DIAMOND, receipt_tome=tome)

        # Inspect entity
        inspection = lens.inspect(sample_entity_view)

        # Get combat history
        history = lens.get_combat_history("Fighter", count=5)

        assert inspection.mode == TransparencyMode.DIAMOND
        assert len(history) >= 1
        assert tome.count() == 1

    def test_stencil_confirmation_to_frozen(self):
        """Test stencil confirmation workflow."""
        # Create stencil
        stencil = create_stencil(
            StencilShape.BURST,
            Position(10, 10),
            20,
            20,
            radius_ft=15,
        )

        # Nudge it
        adjusted = nudge_stencil(stencil, dx=-1, dy=0)

        # Confirm it
        frozen = confirm_stencil(
            adjusted,
            timestamp=1000.0,
            caster_id="wizard_1",
            spell_name="Fireball",
        )

        assert frozen.stencil.origin == Position(9, 10)
        assert frozen.caster_id == "wizard_1"
        assert frozen.confirmed_at == 1000.0
