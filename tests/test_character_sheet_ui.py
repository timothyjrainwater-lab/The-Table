"""Tests for M1 Character Sheet UI.

Tests the CHARACTER_SHEET_UI_CONTRACT.md implementation:
- CharacterData extraction from world state
- Derived value computation
- CharacterSheetUI rendering
- State update subscription
"""

import pytest
from datetime import datetime

from aidm.ui.character_sheet import (
    CharacterSheetUI,
    CharacterData,
    PartySheet,
    CLASS_PROGRESSIONS,
    _compute_bab,
    _compute_base_save,
)
from aidm.core.state import WorldState


# =============================================================================
# Test Fixtures
# =============================================================================

def create_test_fighter() -> dict:
    """Create a test fighter entity."""
    return {
        "name": "Theron",
        "race": "Human",
        "size": "Medium",
        "class": "Fighter",
        "level": 3,
        "strength": 16,
        "dexterity": 14,
        "constitution": 14,
        "intelligence": 10,
        "wisdom": 12,
        "charisma": 8,
        "max_hp": 28,
        "hp": 25,
        "team": "party",
        "conditions": [],
        "position": {"x": 5, "y": 10},
    }


def create_test_state() -> WorldState:
    """Create test world state with fighter and goblin."""
    return WorldState(
        ruleset_version="test-1.0",
        entities={
            "fighter_1": create_test_fighter(),
            "goblin_1": {
                "name": "Goblin Warrior",
                "race": "Goblin",
                "size": "Small",
                "class": "Warrior",
                "level": 1,
                "strength": 8,
                "dexterity": 14,
                "constitution": 10,
                "hp": 6,
                "max_hp": 6,
                "team": "monsters",
            },
        },
    )


# =============================================================================
# CharacterData Tests
# =============================================================================

class TestCharacterData:
    """Tests for CharacterData extraction and computation."""

    def test_from_entity(self):
        """Should extract data from entity dictionary."""
        entity_data = create_test_fighter()
        data = CharacterData.from_entity("fighter_1", entity_data)

        assert data.entity_id == "fighter_1"
        assert data.name == "Theron"
        assert data.race == "Human"
        assert data.class_name == "Fighter"
        assert data.level == 3
        assert data.strength == 16
        assert data.current_hp == 25
        assert data.max_hp == 28

    def test_ability_modifiers(self):
        """Should compute ability modifiers correctly."""
        data = CharacterData(
            entity_id="test",
            strength=16,  # +3
            dexterity=14,  # +2
            constitution=13,  # +1
            intelligence=10,  # +0
            wisdom=8,  # -1
            charisma=6,  # -2
        )

        assert data.str_modifier == 3
        assert data.dex_modifier == 2
        assert data.con_modifier == 1
        assert data.int_modifier == 0
        assert data.wis_modifier == -1
        assert data.cha_modifier == -2

    def test_bab_progression(self):
        """Should compute BAB based on fighter level."""
        data = CharacterData(entity_id="test", level=5)
        assert data.base_attack_bonus == 5

        data = CharacterData(entity_id="test", level=1)
        assert data.base_attack_bonus == 1

    def test_attack_bonuses(self):
        """Should compute attack bonuses (BAB + modifier)."""
        data = CharacterData(
            entity_id="test",
            level=3,
            strength=16,  # +3
            dexterity=14,  # +2
        )

        assert data.melee_attack_bonus == 6  # BAB 3 + STR 3
        assert data.ranged_attack_bonus == 5  # BAB 3 + DEX 2

    def test_base_ac(self):
        """Should compute base AC (10 + DEX)."""
        data = CharacterData(entity_id="test", dexterity=14)
        assert data.base_ac == 12

        data = CharacterData(entity_id="test", dexterity=8)
        assert data.base_ac == 9

    def test_saving_throws(self):
        """Should compute saving throws."""
        data = CharacterData(
            entity_id="test",
            level=3,
            constitution=14,  # +2
            dexterity=14,  # +2
            wisdom=12,  # +1
        )

        # Fighter: Fort good (2 + level/2), Ref/Will poor (level/3)
        assert data.fortitude_save == 5  # 2 + 1 + CON 2
        assert data.reflex_save == 3  # 1 + DEX 2
        assert data.will_save == 2  # 1 + WIS 1

    def test_hp_display(self):
        """Should format HP display correctly."""
        data = CharacterData(entity_id="test", current_hp=25, max_hp=28)
        assert data.hp_display == "25/28"

    def test_status_line_ok(self):
        """Should show OK when no conditions."""
        data = CharacterData(entity_id="test", conditions=[])
        assert data.status_line == "OK"

    def test_status_line_conditions(self):
        """Should show conditions when present."""
        data = CharacterData(entity_id="test", conditions=["Poisoned", "Fatigued"])
        assert "Poisoned" in data.status_line
        assert "Fatigued" in data.status_line

    def test_status_line_defeated(self):
        """Should show DEFEATED when defeated."""
        data = CharacterData(entity_id="test", defeated=True)
        assert "DEFEATED" in data.status_line


# =============================================================================
# CharacterSheetUI Tests
# =============================================================================

class TestCharacterSheetUI:
    """Tests for CharacterSheetUI display."""

    def test_update_from_state(self):
        """Should update data from world state."""
        state = create_test_state()
        sheet = CharacterSheetUI("fighter_1")

        sheet.update(state)

        assert sheet.data is not None
        assert sheet.data.name == "Theron"
        assert sheet.data.current_hp == 25

    def test_update_missing_entity(self):
        """Should handle missing entity gracefully."""
        state = create_test_state()
        sheet = CharacterSheetUI("nonexistent")

        sheet.update(state)

        assert sheet.data is None

    def test_render_compact(self):
        """Should render compact one-line status."""
        state = create_test_state()
        sheet = CharacterSheetUI("fighter_1")
        sheet.update(state)

        compact = sheet.render_compact()

        assert "Theron" in compact
        assert "Fighter 3" in compact
        assert "25/28" in compact
        assert "AC:" in compact

    def test_render_compact_with_conditions(self):
        """Should show conditions in compact view."""
        state = create_test_state()
        state.entities["fighter_1"]["conditions"] = ["Poisoned"]
        sheet = CharacterSheetUI("fighter_1")
        sheet.update(state)

        compact = sheet.render_compact()

        assert "Poisoned" in compact

    def test_render_compact_missing(self):
        """Should show not found for missing entity."""
        state = create_test_state()
        sheet = CharacterSheetUI("nonexistent")
        sheet.update(state)

        compact = sheet.render_compact()

        assert "Not Found" in compact

    def test_render_full(self):
        """Should render full character sheet."""
        state = create_test_state()
        sheet = CharacterSheetUI("fighter_1")
        sheet.update(state)

        full = sheet.render_full()

        assert "THERON" in full
        assert "Human Fighter 3" in full
        assert "ABILITY SCORES" in full
        assert "STR:" in full
        assert "COMBAT" in full
        assert "SAVING THROWS" in full

    def test_render_combat_status(self):
        """Should render combat status line."""
        state = create_test_state()
        sheet = CharacterSheetUI("fighter_1")
        sheet.update(state)

        combat = sheet.render_combat_status()

        assert "Theron" in combat
        assert "25/28" in combat

    def test_render_combat_status_defeated(self):
        """Should show DEFEATED in combat status."""
        state = create_test_state()
        state.entities["fighter_1"]["defeated"] = True
        sheet = CharacterSheetUI("fighter_1")
        sheet.update(state)

        combat = sheet.render_combat_status()

        assert "DEFEATED" in combat

    def test_subscribe_callback(self):
        """Should call subscribers on update."""
        state = create_test_state()
        sheet = CharacterSheetUI("fighter_1")

        callback_calls = []

        def on_update(ws):
            callback_calls.append(ws)

        sheet.subscribe(on_update)
        sheet.update(state)

        assert len(callback_calls) == 1
        assert callback_calls[0] == state

    def test_unsubscribe_callback(self):
        """Should not call unsubscribed callbacks."""
        state = create_test_state()
        sheet = CharacterSheetUI("fighter_1")

        callback_calls = []

        def on_update(ws):
            callback_calls.append(ws)

        sheet.subscribe(on_update)
        sheet.unsubscribe(on_update)
        sheet.update(state)

        assert len(callback_calls) == 0


# =============================================================================
# PartySheet Tests
# =============================================================================

class TestPartySheet:
    """Tests for PartySheet aggregate view."""

    def test_add_character(self):
        """Should add character sheets."""
        party = PartySheet()

        sheet = party.add_character("fighter_1")

        assert isinstance(sheet, CharacterSheetUI)
        assert sheet.entity_id == "fighter_1"

    def test_update_all(self):
        """Should update all character sheets."""
        state = create_test_state()
        party = PartySheet()

        party.add_character("fighter_1")
        party.add_character("goblin_1")
        party.update_all(state)

        # Both should have data
        assert party._sheets["fighter_1"].data is not None
        assert party._sheets["goblin_1"].data is not None

    def test_render_party_status(self):
        """Should render party status overview."""
        state = create_test_state()
        party = PartySheet()

        party.add_character("fighter_1")
        party.add_character("goblin_1")
        party.update_all(state)

        status = party.render_party_status()

        assert "PARTY STATUS" in status
        assert "Theron" in status
        assert "Goblin" in status

    def test_render_party_status_empty(self):
        """Should handle empty party."""
        party = PartySheet()

        status = party.render_party_status()

        assert "No characters" in status

    def test_render_combat_tracker(self):
        """Should render combat tracker view."""
        state = create_test_state()
        party = PartySheet()

        party.add_character("fighter_1")
        party.add_character("goblin_1")
        party.update_all(state)

        tracker = party.render_combat_tracker()

        assert "COMBAT" in tracker

    def test_remove_character(self):
        """Should remove character from party."""
        party = PartySheet()

        party.add_character("fighter_1")
        party.remove_character("fighter_1")

        assert "fighter_1" not in party._sheets


# =============================================================================
# Class-Aware Progression Tests (FIX-16)
# =============================================================================

class TestClassProgressions:
    """Tests for multi-class BAB and save progressions (PHB p.22)."""

    def test_fighter_full_bab(self):
        """Fighter: full BAB (+1/level)."""
        data = CharacterData(entity_id="test", class_name="Fighter", level=5)
        assert data.base_attack_bonus == 5

        data = CharacterData(entity_id="test", class_name="Fighter", level=20)
        assert data.base_attack_bonus == 20

    def test_wizard_poor_bab(self):
        """Wizard: poor BAB (+1/2 levels)."""
        data = CharacterData(entity_id="test", class_name="Wizard", level=1)
        assert data.base_attack_bonus == 0

        data = CharacterData(entity_id="test", class_name="Wizard", level=5)
        assert data.base_attack_bonus == 2

        data = CharacterData(entity_id="test", class_name="Wizard", level=20)
        assert data.base_attack_bonus == 10

    def test_rogue_medium_bab(self):
        """Rogue: medium BAB (+3/4 levels)."""
        data = CharacterData(entity_id="test", class_name="Rogue", level=1)
        assert data.base_attack_bonus == 0

        data = CharacterData(entity_id="test", class_name="Rogue", level=4)
        assert data.base_attack_bonus == 3

        data = CharacterData(entity_id="test", class_name="Rogue", level=8)
        assert data.base_attack_bonus == 6

        data = CharacterData(entity_id="test", class_name="Rogue", level=20)
        assert data.base_attack_bonus == 15

    def test_wizard_saves(self):
        """Wizard: poor Fort/Ref, good Will (PHB p.55)."""
        data = CharacterData(
            entity_id="test",
            class_name="Wizard",
            level=5,
            constitution=10,  # +0
            dexterity=10,     # +0
            wisdom=10,        # +0
        )
        assert data.fortitude_save == 1   # poor: 5//3 = 1
        assert data.reflex_save == 1      # poor: 5//3 = 1
        assert data.will_save == 4        # good: 2 + 5//2 = 4

    def test_rogue_saves(self):
        """Rogue: poor Fort/Will, good Ref (PHB p.50)."""
        data = CharacterData(
            entity_id="test",
            class_name="Rogue",
            level=6,
            constitution=10,
            dexterity=10,
            wisdom=10,
        )
        assert data.fortitude_save == 2   # poor: 6//3 = 2
        assert data.reflex_save == 5      # good: 2 + 6//2 = 5
        assert data.will_save == 2        # poor: 6//3 = 2

    def test_cleric_saves(self):
        """Cleric: good Fort/Will, poor Ref (PHB p.32)."""
        data = CharacterData(
            entity_id="test",
            class_name="Cleric",
            level=6,
            constitution=10,
            dexterity=10,
            wisdom=10,
        )
        assert data.fortitude_save == 5   # good: 2 + 6//2 = 5
        assert data.reflex_save == 2      # poor: 6//3 = 2
        assert data.will_save == 5        # good: 2 + 6//2 = 5

    def test_monk_all_good_saves(self):
        """Monk: good Fort/Ref/Will (PHB p.40)."""
        data = CharacterData(
            entity_id="test",
            class_name="Monk",
            level=6,
            constitution=10,
            dexterity=10,
            wisdom=10,
        )
        assert data.fortitude_save == 5
        assert data.reflex_save == 5
        assert data.will_save == 5

    def test_unknown_class_defaults_to_fighter(self):
        """Unknown class name should fall back to Fighter progression."""
        data = CharacterData(entity_id="test", class_name="Mystic", level=5)
        # Fighter fallback: full BAB
        assert data.base_attack_bonus == 5

    def test_bab_computation_helpers(self):
        """Direct computation helpers produce correct values."""
        assert _compute_bab(1, "full") == 1
        assert _compute_bab(5, "full") == 5
        assert _compute_bab(1, "medium") == 0
        assert _compute_bab(4, "medium") == 3
        assert _compute_bab(1, "poor") == 0
        assert _compute_bab(4, "poor") == 2

        assert _compute_base_save(1, "good") == 2
        assert _compute_base_save(6, "good") == 5
        assert _compute_base_save(1, "poor") == 0
        assert _compute_base_save(6, "poor") == 2

    def test_all_phb_classes_have_progressions(self):
        """All 11 PHB classes should have progression entries."""
        phb_classes = [
            "Fighter", "Barbarian", "Paladin", "Ranger", "Monk",
            "Rogue", "Bard", "Cleric", "Druid", "Wizard", "Sorcerer",
        ]
        for cls in phb_classes:
            assert cls in CLASS_PROGRESSIONS, f"Missing progression for {cls}"

    def test_class_from_entity_data(self):
        """from_entity should read class field for progression lookup."""
        entity_data = {
            "name": "Gandalf",
            "class": "Wizard",
            "level": 10,
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "wisdom": 10,
            "hp": 30,
        }
        data = CharacterData.from_entity("wizard_1", entity_data)
        assert data.class_name == "Wizard"
        assert data.base_attack_bonus == 5   # poor BAB at level 10
        assert data.will_save == 7           # good Will: 2 + 10//2 = 7
