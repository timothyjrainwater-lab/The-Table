"""Tests for Tri-Gem Socket transparency system.

WO-023: Transparency Tri-Gem Socket
Tests for all three transparency modes (RUBY/SAPPHIRE/DIAMOND),
filter correctness, format output, and edge cases.

IMMERSION BOUNDARY: Tests use event data dicts, not Event objects directly,
to maintain the boundary between immersion and engine modules.
"""

import pytest
from typing import Dict, List, Any

from aidm.schemas.transparency import (
    TransparencyMode,
    TransparencyConfig,
    FilteredSTP,
    RollBreakdown,
    DamageBreakdown,
    ModifierBreakdown,
)
from aidm.immersion.tri_gem_socket import (
    TriGemSocket,
    filter_stp,
    filter_events,
    format_for_display,
    format_events_for_display,
    get_entity_display_name,
    EventData,
)


# ==============================================================================
# TEST FIXTURES
# ==============================================================================

@pytest.fixture
def name_map() -> Dict[str, str]:
    """Standard name mapping for tests."""
    return {
        "fighter_1": "Sir Roland",
        "goblin_1": "Goblin Scout",
        "wizard_1": "Elara the Wise",
        "ogre_1": "Groknak the Smasher",
    }


@pytest.fixture
def attack_roll_hit_event() -> EventData:
    """Attack roll event that hits."""
    return {
        "event_id": 1,
        "event_type": "attack_roll",
        "timestamp": 100.0,
        "payload": {
            "attacker_id": "fighter_1",
            "target_id": "goblin_1",
            "d20_result": 18,
            "attack_bonus": 5,
            "condition_modifier": 0,
            "mounted_bonus": 0,
            "terrain_higher_ground": 0,
            "cover_type": "none",
            "cover_ac_bonus": 0,
            "total": 23,
            "target_ac": 15,
            "target_base_ac": 15,
            "target_ac_modifier": 0,
            "hit": True,
            "is_natural_20": False,
            "is_natural_1": False,
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 143}],
    }


@pytest.fixture
def attack_roll_miss_event() -> EventData:
    """Attack roll event that misses."""
    return {
        "event_id": 2,
        "event_type": "attack_roll",
        "timestamp": 100.0,
        "payload": {
            "attacker_id": "goblin_1",
            "target_id": "fighter_1",
            "d20_result": 8,
            "attack_bonus": 2,
            "condition_modifier": 0,
            "mounted_bonus": 0,
            "terrain_higher_ground": 0,
            "cover_type": "none",
            "cover_ac_bonus": 0,
            "total": 10,
            "target_ac": 18,
            "target_base_ac": 18,
            "target_ac_modifier": 0,
            "hit": False,
            "is_natural_20": False,
            "is_natural_1": False,
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 143}],
    }


@pytest.fixture
def natural_20_event() -> EventData:
    """Attack roll event with natural 20."""
    return {
        "event_id": 3,
        "event_type": "attack_roll",
        "timestamp": 100.0,
        "payload": {
            "attacker_id": "fighter_1",
            "target_id": "ogre_1",
            "d20_result": 20,
            "attack_bonus": 5,
            "condition_modifier": 0,
            "mounted_bonus": 0,
            "terrain_higher_ground": 0,
            "cover_type": "none",
            "cover_ac_bonus": 0,
            "total": 25,
            "target_ac": 30,  # Would miss normally
            "target_base_ac": 30,
            "target_ac_modifier": 0,
            "hit": True,
            "is_natural_20": True,
            "is_natural_1": False,
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 143}],
    }


@pytest.fixture
def natural_1_event() -> EventData:
    """Attack roll event with natural 1."""
    return {
        "event_id": 4,
        "event_type": "attack_roll",
        "timestamp": 100.0,
        "payload": {
            "attacker_id": "goblin_1",
            "target_id": "fighter_1",
            "d20_result": 1,
            "attack_bonus": 10,
            "condition_modifier": 0,
            "mounted_bonus": 0,
            "terrain_higher_ground": 0,
            "cover_type": "none",
            "cover_ac_bonus": 0,
            "total": 11,
            "target_ac": 5,  # Would hit normally
            "target_base_ac": 5,
            "target_ac_modifier": 0,
            "hit": False,
            "is_natural_20": False,
            "is_natural_1": True,
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 143}],
    }


@pytest.fixture
def damage_roll_event() -> EventData:
    """Damage roll event."""
    return {
        "event_id": 5,
        "event_type": "damage_roll",
        "timestamp": 100.1,
        "payload": {
            "attacker_id": "fighter_1",
            "target_id": "goblin_1",
            "damage_dice": "1d8",
            "damage_rolls": [6],
            "damage_bonus": 2,
            "str_modifier": 3,
            "condition_modifier": 0,
            "damage_total": 11,
            "damage_type": "slashing",
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 145}],
    }


@pytest.fixture
def save_rolled_success_event() -> EventData:
    """Saving throw event - success."""
    return {
        "event_id": 6,
        "event_type": "save_rolled",
        "timestamp": 100.0,
        "payload": {
            "target_id": "fighter_1",
            "save_type": "ref",
            "d20_result": 15,
            "save_bonus": 4,
            "total": 19,
            "dc": 15,
            "outcome": "success",
            "is_natural_20": False,
            "is_natural_1": False,
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 177}],
    }


@pytest.fixture
def save_rolled_failure_event() -> EventData:
    """Saving throw event - failure."""
    return {
        "event_id": 7,
        "event_type": "save_rolled",
        "timestamp": 100.0,
        "payload": {
            "target_id": "goblin_1",
            "save_type": "will",
            "d20_result": 5,
            "save_bonus": -1,
            "total": 4,
            "dc": 15,
            "outcome": "failure",
            "is_natural_20": False,
            "is_natural_1": False,
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 177}],
    }


@pytest.fixture
def hp_changed_event() -> EventData:
    """HP changed event (damage)."""
    return {
        "event_id": 8,
        "event_type": "hp_changed",
        "timestamp": 100.2,
        "payload": {
            "entity_id": "goblin_1",
            "hp_before": 7,
            "hp_after": -4,
            "delta": -11,
            "source": "attack_damage",
        },
        "citations": [],
    }


@pytest.fixture
def entity_defeated_event() -> EventData:
    """Entity defeated event."""
    return {
        "event_id": 9,
        "event_type": "entity_defeated",
        "timestamp": 100.3,
        "payload": {
            "entity_id": "goblin_1",
            "hp_final": -4,
            "defeated_by": "fighter_1",
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 145}],
    }


@pytest.fixture
def aoo_triggered_event() -> EventData:
    """AoO triggered event."""
    return {
        "event_id": 10,
        "event_type": "aoo_triggered",
        "timestamp": 100.0,
        "payload": {
            "reactor_id": "fighter_1",
            "provoker_id": "goblin_1",
            "provoking_action": "movement_out",
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 137}],
    }


@pytest.fixture
def attack_with_modifiers_event() -> EventData:
    """Attack roll with various modifiers (condition, mounted, terrain)."""
    return {
        "event_id": 11,
        "event_type": "attack_roll",
        "timestamp": 100.0,
        "payload": {
            "attacker_id": "fighter_1",
            "target_id": "goblin_1",
            "d20_result": 12,
            "attack_bonus": 5,
            "condition_modifier": -2,  # Shaken
            "mounted_bonus": 1,
            "terrain_higher_ground": 1,
            "cover_type": "standard",
            "cover_ac_bonus": 4,
            "total": 17,
            "target_ac": 19,  # 15 base + 4 cover
            "target_base_ac": 15,
            "target_ac_modifier": 0,
            "hit": False,
            "is_natural_20": False,
            "is_natural_1": False,
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 143}],
    }


# ==============================================================================
# TRANSPARENCY MODE ENUM TESTS
# ==============================================================================

class TestTransparencyMode:
    """Tests for TransparencyMode enum."""

    def test_ruby_value(self):
        """RUBY mode has correct value."""
        assert TransparencyMode.RUBY.value == "ruby"

    def test_sapphire_value(self):
        """SAPPHIRE mode has correct value."""
        assert TransparencyMode.SAPPHIRE.value == "sapphire"

    def test_diamond_value(self):
        """DIAMOND mode has correct value."""
        assert TransparencyMode.DIAMOND.value == "diamond"

    def test_mode_from_string(self):
        """Can create mode from string value."""
        assert TransparencyMode("ruby") == TransparencyMode.RUBY
        assert TransparencyMode("sapphire") == TransparencyMode.SAPPHIRE
        assert TransparencyMode("diamond") == TransparencyMode.DIAMOND


# ==============================================================================
# TRANSPARENCY CONFIG TESTS
# ==============================================================================

class TestTransparencyConfig:
    """Tests for TransparencyConfig dataclass."""

    def test_default_mode_is_sapphire(self):
        """Default mode is SAPPHIRE."""
        config = TransparencyConfig(player_id="player_1")
        assert config.mode == TransparencyMode.SAPPHIRE

    def test_create_with_custom_mode(self):
        """Can create config with custom mode."""
        config = TransparencyConfig(player_id="player_1", mode=TransparencyMode.DIAMOND)
        assert config.mode == TransparencyMode.DIAMOND

    def test_serialization_roundtrip(self):
        """Config survives serialization roundtrip."""
        original = TransparencyConfig(
            player_id="alice",
            mode=TransparencyMode.RUBY,
            show_enemy_hp=True,
            show_npc_modifiers=True,
        )
        data = original.to_dict()
        restored = TransparencyConfig.from_dict(data)

        assert restored.player_id == original.player_id
        assert restored.mode == original.mode
        assert restored.show_enemy_hp == original.show_enemy_hp
        assert restored.show_npc_modifiers == original.show_npc_modifiers

    def test_with_mode_immutable_update(self):
        """with_mode creates new config (immutable)."""
        original = TransparencyConfig(player_id="alice", mode=TransparencyMode.RUBY)
        updated = original.with_mode(TransparencyMode.DIAMOND)

        assert original.mode == TransparencyMode.RUBY  # Unchanged
        assert updated.mode == TransparencyMode.DIAMOND
        assert updated.player_id == original.player_id


# ==============================================================================
# RUBY MODE FILTER TESTS
# ==============================================================================

class TestRubyModeFiltering:
    """Tests for RUBY mode (minimal transparency)."""

    def test_attack_roll_hit_ruby(self, attack_roll_hit_event, name_map):
        """RUBY attack hit shows minimal info."""
        filtered = filter_stp(attack_roll_hit_event, TransparencyMode.RUBY, name_map)

        assert filtered.mode == TransparencyMode.RUBY
        assert "Sir Roland" in filtered.final_result
        assert "Goblin Scout" in filtered.final_result
        assert "hits" in filtered.final_result
        # No numbers in RUBY mode
        assert "23" not in filtered.final_result
        assert "15" not in filtered.final_result

    def test_attack_roll_miss_ruby(self, attack_roll_miss_event, name_map):
        """RUBY attack miss shows minimal info."""
        filtered = filter_stp(attack_roll_miss_event, TransparencyMode.RUBY, name_map)

        assert "misses" in filtered.final_result

    def test_damage_roll_ruby(self, damage_roll_event, name_map):
        """RUBY damage shows only total and type."""
        filtered = filter_stp(damage_roll_event, TransparencyMode.RUBY, name_map)

        assert "11" in filtered.final_result
        assert "slashing" in filtered.final_result
        # No dice breakdown
        assert "1d8" not in filtered.final_result

    def test_save_success_ruby(self, save_rolled_success_event, name_map):
        """RUBY save success shows outcome only."""
        filtered = filter_stp(save_rolled_success_event, TransparencyMode.RUBY, name_map)

        assert "makes" in filtered.final_result or "Save" in filtered.final_result
        # No numbers
        assert "19" not in filtered.final_result
        assert "DC" not in filtered.final_result

    def test_hp_changed_ruby(self, hp_changed_event, name_map):
        """RUBY HP change shows only narrative."""
        filtered = filter_stp(hp_changed_event, TransparencyMode.RUBY, name_map)

        assert "wounded" in filtered.final_result.lower()
        # No HP numbers
        assert "7" not in filtered.final_result
        assert "-4" not in filtered.final_result

    def test_entity_defeated_ruby(self, entity_defeated_event, name_map):
        """RUBY defeat shows only narrative."""
        filtered = filter_stp(entity_defeated_event, TransparencyMode.RUBY, name_map)

        assert "defeated" in filtered.final_result.lower()


# ==============================================================================
# SAPPHIRE MODE FILTER TESTS
# ==============================================================================

class TestSapphireModeFiltering:
    """Tests for SAPPHIRE mode (standard transparency)."""

    def test_attack_roll_hit_sapphire(self, attack_roll_hit_event, name_map):
        """SAPPHIRE attack hit shows key numbers."""
        filtered = filter_stp(attack_roll_hit_event, TransparencyMode.SAPPHIRE, name_map)

        assert filtered.mode == TransparencyMode.SAPPHIRE
        assert "Sir Roland" in filtered.final_result
        assert "18" in filtered.final_result  # d20 result
        assert "5" in filtered.final_result   # attack bonus
        assert "23" in filtered.final_result  # total
        assert "AC 15" in filtered.final_result
        assert "Hit" in filtered.final_result

    def test_attack_roll_miss_sapphire(self, attack_roll_miss_event, name_map):
        """SAPPHIRE attack miss shows key numbers."""
        filtered = filter_stp(attack_roll_miss_event, TransparencyMode.SAPPHIRE, name_map)

        assert "10" in filtered.final_result  # total
        assert "AC 18" in filtered.final_result
        assert "Miss" in filtered.final_result

    def test_natural_20_sapphire(self, natural_20_event, name_map):
        """SAPPHIRE shows natural 20 notation."""
        filtered = filter_stp(natural_20_event, TransparencyMode.SAPPHIRE, name_map)

        assert "Natural 20" in filtered.final_result

    def test_natural_1_sapphire(self, natural_1_event, name_map):
        """SAPPHIRE shows natural 1 notation."""
        filtered = filter_stp(natural_1_event, TransparencyMode.SAPPHIRE, name_map)

        assert "Natural 1" in filtered.final_result

    def test_damage_roll_sapphire(self, damage_roll_event, name_map):
        """SAPPHIRE damage shows dice and total."""
        filtered = filter_stp(damage_roll_event, TransparencyMode.SAPPHIRE, name_map)

        assert "1d8" in filtered.final_result
        assert "11" in filtered.final_result  # total

    def test_save_rolled_sapphire(self, save_rolled_success_event, name_map):
        """SAPPHIRE save shows roll vs DC."""
        filtered = filter_stp(save_rolled_success_event, TransparencyMode.SAPPHIRE, name_map)

        assert "15" in filtered.final_result  # d20 result
        assert "19" in filtered.final_result  # total
        assert "DC 15" in filtered.final_result

    def test_hp_changed_sapphire(self, hp_changed_event, name_map):
        """SAPPHIRE HP change shows before/after."""
        filtered = filter_stp(hp_changed_event, TransparencyMode.SAPPHIRE, name_map)

        assert "7" in filtered.final_result  # hp_before
        assert "-4" in filtered.final_result  # hp_after

    def test_roll_summaries_populated(self, attack_roll_hit_event, name_map):
        """SAPPHIRE populates roll_summaries field."""
        filtered = filter_stp(attack_roll_hit_event, TransparencyMode.SAPPHIRE, name_map)

        assert len(filtered.roll_summaries) == 1
        roll_type, natural, total, success = filtered.roll_summaries[0]
        assert roll_type == "attack"
        assert natural == 18
        assert total == 23
        assert success is True


# ==============================================================================
# DIAMOND MODE FILTER TESTS
# ==============================================================================

class TestDiamondModeFiltering:
    """Tests for DIAMOND mode (full transparency)."""

    def test_attack_roll_diamond_has_breakdowns(self, attack_roll_hit_event, name_map):
        """DIAMOND attack has full roll breakdowns."""
        filtered = filter_stp(attack_roll_hit_event, TransparencyMode.DIAMOND, name_map)

        assert filtered.mode == TransparencyMode.DIAMOND
        assert len(filtered.roll_breakdowns) == 1

        roll = filtered.roll_breakdowns[0]
        assert roll.roll_type == "attack"
        assert roll.natural_roll == 18
        assert roll.total == 23
        assert roll.target_value == 15
        assert roll.success is True

    def test_attack_roll_diamond_has_modifiers(self, attack_with_modifiers_event, name_map):
        """DIAMOND shows all modifier sources."""
        filtered = filter_stp(attack_with_modifiers_event, TransparencyMode.DIAMOND, name_map)

        roll = filtered.roll_breakdowns[0]

        # Check modifiers are present
        modifier_sources = [m.source for m in roll.modifiers]
        assert "Base Attack Bonus" in modifier_sources
        assert "Condition Modifier" in modifier_sources
        assert "Mounted Higher Ground" in modifier_sources
        assert "Terrain Higher Ground" in modifier_sources

    def test_damage_roll_diamond_has_breakdown(self, damage_roll_event, name_map):
        """DIAMOND damage has full breakdown."""
        filtered = filter_stp(damage_roll_event, TransparencyMode.DIAMOND, name_map)

        assert filtered.damage_breakdown is not None
        db = filtered.damage_breakdown

        assert db.dice_expression == "1d8"
        assert db.dice_results == (6,)
        assert db.total == 11
        assert db.damage_type == "slashing"

        # Check modifiers
        modifier_sources = [m.source for m in db.modifiers]
        assert "Weapon Damage Bonus" in modifier_sources
        assert "STR Modifier" in modifier_sources

    def test_diamond_has_rule_citations(self, attack_roll_hit_event, name_map):
        """DIAMOND includes rule citations."""
        filtered = filter_stp(attack_roll_hit_event, TransparencyMode.DIAMOND, name_map)

        assert len(filtered.rule_citations) > 0
        # Check for PHB citation
        sources = [c[0] for c in filtered.rule_citations]
        assert "681f92bc94ff" in sources

    def test_diamond_has_raw_payload(self, attack_roll_hit_event, name_map):
        """DIAMOND includes raw payload for debugging."""
        filtered = filter_stp(attack_roll_hit_event, TransparencyMode.DIAMOND, name_map)

        assert filtered.raw_payload is not None
        assert filtered.raw_payload["d20_result"] == 18


# ==============================================================================
# FORMAT FOR DISPLAY TESTS
# ==============================================================================

class TestFormatForDisplay:
    """Tests for format_for_display function."""

    def test_ruby_format_simple(self, attack_roll_hit_event, name_map):
        """RUBY format is simple one-liner."""
        filtered = filter_stp(attack_roll_hit_event, TransparencyMode.RUBY, name_map)
        output = format_for_display(filtered)

        assert "\n" not in output
        assert "Sir Roland hits Goblin Scout" in output

    def test_sapphire_format_includes_numbers(self, attack_roll_hit_event, name_map):
        """SAPPHIRE format includes key numbers."""
        filtered = filter_stp(attack_roll_hit_event, TransparencyMode.SAPPHIRE, name_map)
        output = format_for_display(filtered)

        assert "18" in output
        assert "23" in output
        assert "AC 15" in output

    def test_diamond_format_multiline(self, attack_roll_hit_event, name_map):
        """DIAMOND format can be multiline with breakdowns."""
        filtered = filter_stp(attack_roll_hit_event, TransparencyMode.DIAMOND, name_map)
        output = format_for_display(filtered)

        # DIAMOND can have multiple lines for details
        assert "Sir Roland" in output

    def test_diamond_damage_format(self, damage_roll_event, name_map):
        """DIAMOND damage format shows full breakdown."""
        filtered = filter_stp(damage_roll_event, TransparencyMode.DIAMOND, name_map)
        output = format_for_display(filtered)

        assert "1d8" in output
        assert "11" in output


# ==============================================================================
# TRI-GEM SOCKET CLASS TESTS
# ==============================================================================

class TestTriGemSocket:
    """Tests for TriGemSocket class."""

    def test_default_mode_is_sapphire(self):
        """Socket default mode is SAPPHIRE."""
        socket = TriGemSocket()
        assert socket.default_mode == TransparencyMode.SAPPHIRE

    def test_custom_default_mode(self):
        """Can set custom default mode."""
        socket = TriGemSocket(default_mode=TransparencyMode.DIAMOND)
        assert socket.default_mode == TransparencyMode.DIAMOND

    def test_filter_event_uses_default_mode(self, attack_roll_hit_event):
        """filter_event uses default mode when none specified."""
        socket = TriGemSocket(default_mode=TransparencyMode.RUBY)
        filtered = socket.filter_event(attack_roll_hit_event)

        assert filtered.mode == TransparencyMode.RUBY

    def test_filter_event_explicit_mode_overrides(self, attack_roll_hit_event):
        """Explicit mode parameter overrides default."""
        socket = TriGemSocket(default_mode=TransparencyMode.RUBY)
        filtered = socket.filter_event(attack_roll_hit_event, mode=TransparencyMode.DIAMOND)

        assert filtered.mode == TransparencyMode.DIAMOND

    def test_filter_event_with_config(self, attack_roll_hit_event):
        """Config mode is used when provided."""
        socket = TriGemSocket()
        config = TransparencyConfig(player_id="alice", mode=TransparencyMode.RUBY)
        filtered = socket.filter_event(attack_roll_hit_event, config=config)

        assert filtered.mode == TransparencyMode.RUBY

    def test_explicit_mode_overrides_config(self, attack_roll_hit_event):
        """Explicit mode parameter overrides config mode."""
        socket = TriGemSocket()
        config = TransparencyConfig(player_id="alice", mode=TransparencyMode.RUBY)
        filtered = socket.filter_event(attack_roll_hit_event, mode=TransparencyMode.DIAMOND, config=config)

        assert filtered.mode == TransparencyMode.DIAMOND

    def test_filter_events_batch(self, attack_roll_hit_event, damage_roll_event, name_map):
        """filter_events handles multiple events."""
        socket = TriGemSocket(name_map=name_map)
        events = [attack_roll_hit_event, damage_roll_event]
        filtered = socket.filter_events(events, mode=TransparencyMode.SAPPHIRE)

        assert len(filtered) == 2
        assert all(f.mode == TransparencyMode.SAPPHIRE for f in filtered)

    def test_name_map_used(self, attack_roll_hit_event):
        """Socket uses name map for entity names."""
        socket = TriGemSocket(name_map={"fighter_1": "Sir Roland"})
        filtered = socket.filter_event(attack_roll_hit_event, mode=TransparencyMode.RUBY)

        assert "Sir Roland" in filtered.final_result

    def test_add_name_updates_map(self, attack_roll_hit_event):
        """add_name updates the name map."""
        socket = TriGemSocket()
        socket.add_name("fighter_1", "The Champion")
        filtered = socket.filter_event(attack_roll_hit_event, mode=TransparencyMode.RUBY)

        assert "The Champion" in filtered.final_result

    def test_set_name_map_replaces(self, attack_roll_hit_event):
        """set_name_map replaces entire map."""
        socket = TriGemSocket(name_map={"fighter_1": "Old Name"})
        socket.set_name_map({"fighter_1": "New Name"})
        filtered = socket.filter_event(attack_roll_hit_event, mode=TransparencyMode.RUBY)

        assert "New Name" in filtered.final_result

    def test_format_method(self, attack_roll_hit_event, name_map):
        """format method works correctly."""
        socket = TriGemSocket(name_map=name_map)
        filtered = socket.filter_event(attack_roll_hit_event, mode=TransparencyMode.SAPPHIRE)
        output = socket.format(filtered)

        assert "Sir Roland" in output
        assert "23" in output

    def test_format_all_method(self, attack_roll_hit_event, damage_roll_event, name_map):
        """format_all combines multiple events."""
        socket = TriGemSocket(name_map=name_map)
        events = [attack_roll_hit_event, damage_roll_event]
        filtered = socket.filter_events(events, mode=TransparencyMode.SAPPHIRE)
        output = socket.format_all(filtered)

        assert "Sir Roland" in output
        assert "1d8" in output


# ==============================================================================
# MODE SWITCHING TESTS
# ==============================================================================

class TestModeSwitching:
    """Tests for mode switching mid-session."""

    def test_same_event_different_modes(self, attack_roll_hit_event, name_map):
        """Same event filtered differently by mode."""
        ruby = filter_stp(attack_roll_hit_event, TransparencyMode.RUBY, name_map)
        sapphire = filter_stp(attack_roll_hit_event, TransparencyMode.SAPPHIRE, name_map)
        diamond = filter_stp(attack_roll_hit_event, TransparencyMode.DIAMOND, name_map)

        # All have same event_id
        assert ruby.event_id == sapphire.event_id == diamond.event_id

        # Different modes
        assert ruby.mode == TransparencyMode.RUBY
        assert sapphire.mode == TransparencyMode.SAPPHIRE
        assert diamond.mode == TransparencyMode.DIAMOND

        # RUBY has no roll summaries (or empty)
        assert len(ruby.roll_summaries) == 0

        # SAPPHIRE has roll summaries
        assert len(sapphire.roll_summaries) > 0

        # DIAMOND has breakdowns
        assert len(diamond.roll_breakdowns) > 0

    def test_config_mode_change(self, attack_roll_hit_event, name_map):
        """Config mode change produces different output."""
        socket = TriGemSocket(name_map=name_map)

        config = TransparencyConfig(player_id="alice", mode=TransparencyMode.RUBY)
        ruby = socket.filter_event(attack_roll_hit_event, config=config)

        config = config.with_mode(TransparencyMode.DIAMOND)
        diamond = socket.filter_event(attack_roll_hit_event, config=config)

        assert ruby.mode == TransparencyMode.RUBY
        assert diamond.mode == TransparencyMode.DIAMOND


# ==============================================================================
# EDGE CASE TESTS
# ==============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_unknown_event_type_handled(self):
        """Unknown event types are handled gracefully."""
        event = {
            "event_id": 100,
            "event_type": "unknown_event_type",
            "timestamp": 100.0,
            "payload": {"some_field": "some_value"},
            "citations": [],
        }
        filtered = filter_stp(event, TransparencyMode.SAPPHIRE)

        assert filtered.event_type == "unknown_event_type"
        assert "Unknown Event Type" in filtered.final_result

    def test_missing_entity_id_handled(self):
        """Missing entity IDs don't crash."""
        event = {
            "event_id": 100,
            "event_type": "attack_roll",
            "timestamp": 100.0,
            "payload": {
                "d20_result": 15,
                "hit": True,
            },
            "citations": [],
        }
        # Should not raise
        filtered = filter_stp(event, TransparencyMode.SAPPHIRE)
        assert filtered is not None

    def test_negative_attack_bonus(self):
        """Negative attack bonus formatted correctly."""
        event = {
            "event_id": 100,
            "event_type": "attack_roll",
            "timestamp": 100.0,
            "payload": {
                "attacker_id": "weak_goblin",
                "target_id": "fighter",
                "d20_result": 10,
                "attack_bonus": -2,
                "total": 8,
                "target_ac": 15,
                "hit": False,
                "is_natural_20": False,
                "is_natural_1": False,
            },
            "citations": [],
        }
        filtered = filter_stp(event, TransparencyMode.SAPPHIRE)

        # Should show subtraction
        assert "10" in filtered.final_result
        assert "2" in filtered.final_result
        assert "8" in filtered.final_result

    def test_entity_id_fallback_no_name_map(self):
        """Entity ID used when no name map provided."""
        result = get_entity_display_name("goblin_scout_1", None)
        assert result == "Goblin Scout 1"

    def test_entity_id_fallback_not_in_map(self, name_map):
        """Entity ID used when not in name map."""
        result = get_entity_display_name("unknown_entity", name_map)
        assert result == "Unknown Entity"

    def test_empty_damage_rolls(self):
        """Empty damage rolls handled."""
        event = {
            "event_id": 100,
            "event_type": "damage_roll",
            "timestamp": 100.0,
            "payload": {
                "attacker_id": "fighter",
                "target_id": "goblin",
                "damage_dice": "0d0",
                "damage_rolls": [],
                "damage_bonus": 0,
                "str_modifier": 0,
                "damage_total": 0,
                "damage_type": "slashing",
            },
            "citations": [],
        }
        filtered = filter_stp(event, TransparencyMode.DIAMOND)
        assert filtered.damage_breakdown is not None

    def test_save_partial_outcome(self):
        """Partial save outcome (half damage)."""
        event = {
            "event_id": 100,
            "event_type": "save_rolled",
            "timestamp": 100.0,
            "payload": {
                "target_id": "fighter",
                "save_type": "ref",
                "d20_result": 15,
                "save_bonus": 6,
                "total": 21,
                "dc": 18,
                "outcome": "partial",
                "is_natural_20": False,
                "is_natural_1": False,
            },
            "citations": [],
        }
        filtered = filter_stp(event, TransparencyMode.SAPPHIRE)

        assert "partial" in filtered.final_result.lower() or "half" in filtered.final_result.lower()

    def test_hp_healing_event(self):
        """HP increase (healing) formatted correctly."""
        event = {
            "event_id": 100,
            "event_type": "hp_changed",
            "timestamp": 100.0,
            "payload": {
                "entity_id": "fighter",
                "hp_before": 10,
                "hp_after": 18,
                "delta": 8,
                "source": "cure_light_wounds",
            },
            "citations": [],
        }
        ruby = filter_stp(event, TransparencyMode.RUBY)
        sapphire = filter_stp(event, TransparencyMode.SAPPHIRE)

        assert "heal" in ruby.final_result.lower()
        assert "8" in sapphire.final_result


# ==============================================================================
# SERIALIZATION TESTS
# ==============================================================================

class TestSerialization:
    """Tests for FilteredSTP serialization."""

    def test_filtered_stp_roundtrip(self, attack_roll_hit_event, name_map):
        """FilteredSTP survives serialization roundtrip."""
        original = filter_stp(attack_roll_hit_event, TransparencyMode.DIAMOND, name_map)
        data = original.to_dict()
        restored = FilteredSTP.from_dict(data)

        assert restored.event_id == original.event_id
        assert restored.event_type == original.event_type
        assert restored.mode == original.mode
        assert restored.final_result == original.final_result

    def test_roll_breakdown_roundtrip(self, attack_roll_hit_event, name_map):
        """RollBreakdown in FilteredSTP survives roundtrip."""
        original = filter_stp(attack_roll_hit_event, TransparencyMode.DIAMOND, name_map)
        data = original.to_dict()
        restored = FilteredSTP.from_dict(data)

        assert len(restored.roll_breakdowns) == len(original.roll_breakdowns)
        if restored.roll_breakdowns:
            orig_roll = original.roll_breakdowns[0]
            rest_roll = restored.roll_breakdowns[0]
            assert rest_roll.roll_type == orig_roll.roll_type
            assert rest_roll.natural_roll == orig_roll.natural_roll

    def test_damage_breakdown_roundtrip(self, damage_roll_event, name_map):
        """DamageBreakdown in FilteredSTP survives roundtrip."""
        original = filter_stp(damage_roll_event, TransparencyMode.DIAMOND, name_map)
        data = original.to_dict()
        restored = FilteredSTP.from_dict(data)

        assert restored.damage_breakdown is not None
        assert restored.damage_breakdown.total == original.damage_breakdown.total
        assert restored.damage_breakdown.damage_type == original.damage_breakdown.damage_type


# ==============================================================================
# PURE FUNCTION VERIFICATION
# ==============================================================================

class TestPureFunctions:
    """Tests verifying functions are pure (no state mutation)."""

    def test_filter_stp_does_not_mutate_event(self, attack_roll_hit_event, name_map):
        """filter_stp does not mutate the input event dict."""
        import copy
        original_payload = copy.deepcopy(attack_roll_hit_event)

        filter_stp(attack_roll_hit_event, TransparencyMode.RUBY, name_map)
        filter_stp(attack_roll_hit_event, TransparencyMode.SAPPHIRE, name_map)
        filter_stp(attack_roll_hit_event, TransparencyMode.DIAMOND, name_map)

        assert attack_roll_hit_event == original_payload

    def test_filter_events_does_not_mutate_list(self, attack_roll_hit_event, damage_roll_event, name_map):
        """filter_events does not mutate the input list."""
        events = [attack_roll_hit_event, damage_roll_event]
        original_len = len(events)

        filter_events(events, TransparencyMode.SAPPHIRE, name_map)

        assert len(events) == original_len

    def test_socket_does_not_mutate_events(self, attack_roll_hit_event, name_map):
        """TriGemSocket does not mutate events."""
        import copy
        socket = TriGemSocket(name_map=name_map)
        original_payload = copy.deepcopy(attack_roll_hit_event)

        socket.filter_event(attack_roll_hit_event, mode=TransparencyMode.DIAMOND)

        assert attack_roll_hit_event == original_payload
