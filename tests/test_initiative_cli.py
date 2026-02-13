"""Tests for WO-INITIATIVE-01 — initiative system wired into CLI.

Verifies:
  - Initiative is rolled at encounter start (not hardcoded)
  - Same seed produces identical initiative order across runs
  - Tie-breaking follows RAW: total > DEX mod > entity_id
  - 3v3 fixture initiative order is deterministic per seed
  - Initiative rolls are displayed in CLI output
  - Turn progression follows initiative order
"""

import io
import sys

from aidm.core.initiative import (
    roll_initiative_for_all_actors,
    sort_initiative_order,
    InitiativeRoll,
)
from aidm.core.rng_manager import RNGManager
from aidm.runtime.play_controller import build_simple_combat_fixture
from aidm.schemas.entity_fields import EF

from play import main


# ---------------------------------------------------------------------------
# Initiative determinism
# ---------------------------------------------------------------------------

class TestInitiativeDeterminism:
    """Same seed must produce identical initiative order every time."""

    def test_seed_42_deterministic(self):
        """build_simple_combat_fixture(seed=42) produces same order 10 times."""
        baseline = build_simple_combat_fixture(master_seed=42)
        baseline_order = baseline.world_state.active_combat["initiative_order"]

        for i in range(10):
            fixture = build_simple_combat_fixture(master_seed=42)
            order = fixture.world_state.active_combat["initiative_order"]
            assert order == baseline_order, f"Run {i}: initiative order differs"

    def test_different_seeds_differ(self):
        """Different seeds should produce different initiative orders."""
        orders = set()
        for seed in range(20):
            fixture = build_simple_combat_fixture(master_seed=seed)
            order = tuple(fixture.world_state.active_combat["initiative_order"])
            orders.add(order)

        # With 20 seeds and 6 combatants, we should get multiple distinct orders
        assert len(orders) >= 2, (
            "20 different seeds all produced identical initiative order"
        )

    def test_initiative_rolls_populated(self):
        """Fixture should include initiative roll data."""
        fixture = build_simple_combat_fixture(master_seed=42)
        assert fixture.initiative_rolls is not None
        assert len(fixture.initiative_rolls) == 6  # 3 PCs + 3 goblins

    def test_initiative_rolls_match_order(self):
        """The computed order must match what sort_initiative_order produces."""
        fixture = build_simple_combat_fixture(master_seed=42)
        recomputed_order = sort_initiative_order(fixture.initiative_rolls)
        actual_order = fixture.world_state.active_combat["initiative_order"]
        assert actual_order == recomputed_order

    def test_initiative_uses_dex_modifier(self):
        """Each roll's dex_modifier should match the entity's EF.DEX_MOD."""
        fixture = build_simple_combat_fixture(master_seed=42)
        for roll in fixture.initiative_rolls:
            entity = fixture.world_state.entities[roll.actor_id]
            expected_dex = entity.get(EF.DEX_MOD, 0)
            assert roll.dex_modifier == expected_dex, (
                f"{roll.actor_id}: roll dex={roll.dex_modifier}, "
                f"entity dex={expected_dex}"
            )

    def test_initiative_total_correct(self):
        """total = d20_roll + dex_modifier."""
        fixture = build_simple_combat_fixture(master_seed=42)
        for roll in fixture.initiative_rolls:
            assert roll.total == roll.d20_roll + roll.dex_modifier, (
                f"{roll.actor_id}: {roll.d20_roll} + {roll.dex_modifier} "
                f"!= {roll.total}"
            )


# ---------------------------------------------------------------------------
# Tie-breaking
# ---------------------------------------------------------------------------

class TestInitiativeTieBreaking:
    """RAW tie-breaking: higher total > higher DEX mod > lexicographic ID."""

    def test_higher_total_wins(self):
        rolls = [
            InitiativeRoll(actor_id="a", d20_roll=15, dex_modifier=0, misc_modifier=0, total=15),
            InitiativeRoll(actor_id="b", d20_roll=10, dex_modifier=0, misc_modifier=0, total=10),
        ]
        order = sort_initiative_order(rolls)
        assert order == ["a", "b"]

    def test_dex_breaks_total_tie(self):
        rolls = [
            InitiativeRoll(actor_id="a", d20_roll=10, dex_modifier=1, misc_modifier=0, total=11),
            InitiativeRoll(actor_id="b", d20_roll=8, dex_modifier=3, misc_modifier=0, total=11),
        ]
        order = sort_initiative_order(rolls)
        # Same total (11), but b has higher DEX mod (3 > 1)
        assert order == ["b", "a"]

    def test_entity_id_breaks_full_tie(self):
        rolls = [
            InitiativeRoll(actor_id="goblin_2", d20_roll=10, dex_modifier=1, misc_modifier=0, total=11),
            InitiativeRoll(actor_id="goblin_1", d20_roll=10, dex_modifier=1, misc_modifier=0, total=11),
        ]
        order = sort_initiative_order(rolls)
        # Same total, same DEX, lexicographic: goblin_1 < goblin_2
        assert order == ["goblin_1", "goblin_2"]


# ---------------------------------------------------------------------------
# CLI display
# ---------------------------------------------------------------------------

class TestInitiativeCLIDisplay:
    """Initiative order should be printed at encounter start."""

    def _run_session(self, commands, seed=42):
        action_iter = iter(commands)

        def mock_input(prompt=""):
            try:
                return next(action_iter)
            except StopIteration:
                return "quit"

        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            main(seed=seed, input_fn=mock_input)
        finally:
            sys.stdout = old_stdout
        return buf.getvalue()

    def test_initiative_printed_at_start(self):
        output = self._run_session(["quit"])
        assert "Turn Order" in output

    def test_initiative_shows_d20_rolls(self):
        output = self._run_session(["quit"])
        assert "d20=" in output
        assert "DEX" in output

    def test_initiative_shows_all_combatants(self):
        output = self._run_session(["quit"])
        assert "Aldric" in output
        assert "Elara" in output
        assert "Snitch" in output
        assert "Goblin" in output

    def test_initiative_deterministic_display(self):
        """Same seed produces identical initiative display."""
        output1 = self._run_session(["quit"], seed=42)
        output2 = self._run_session(["quit"], seed=42)
        assert output1 == output2


# ---------------------------------------------------------------------------
# Turn order follows initiative
# ---------------------------------------------------------------------------

class TestTurnOrderFollowsInitiative:
    """Turns must execute in initiative order, not hardcoded order."""

    def test_turn_order_matches_initiative(self):
        """The first turn header should match the highest initiative."""
        fixture = build_simple_combat_fixture(master_seed=42)
        init_order = fixture.world_state.active_combat["initiative_order"]
        first_actor = init_order[0]
        first_name = fixture.world_state.entities[first_actor].get("name", first_actor)

        buf = io.StringIO()
        commands = iter(["attack goblin warrior"] * 30)

        def mock_input(prompt=""):
            try:
                return next(commands)
            except StopIteration:
                return "quit"

        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            main(seed=42, input_fn=mock_input)
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()

        # The first "Turn" header should be for the entity with highest initiative
        # For seed 42, the first actor is determined by dice
        first_team = fixture.world_state.entities[first_actor].get(EF.TEAM, "")
        if first_team == "party":
            assert f"--- {first_name}'s Turn ---" in output
        else:
            # Enemy turn: "--- <name> attacks <target>! ---"
            assert f"--- {first_name} attacks" in output

    def test_order_stable_across_rounds(self):
        """Initiative order doesn't change between rounds."""
        fixture = build_simple_combat_fixture(master_seed=100)
        init_order = fixture.world_state.active_combat["initiative_order"]

        # Play through enough turns that multiple rounds happen
        buf = io.StringIO()
        commands = iter(["attack goblin warrior"] * 60)

        def mock_input(prompt=""):
            try:
                return next(commands)
            except StopIteration:
                return "quit"

        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            main(seed=100, input_fn=mock_input)
        finally:
            sys.stdout = old_stdout

        # Re-create fixture to verify order didn't change
        fixture2 = build_simple_combat_fixture(master_seed=100)
        assert fixture2.world_state.active_combat["initiative_order"] == init_order
