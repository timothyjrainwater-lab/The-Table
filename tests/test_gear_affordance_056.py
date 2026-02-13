"""Tests for WO-056: Gear Affordance Tags (AD-005 Layer 3)

Verifies:
- visible_gear field in NarrativeBrief (serialization, deserialization)
- resolve_visible_gear_names converts item_ids to display names
- assemble_narrative_brief passes visible_gear through
- End-to-end pipeline: ContainerResolver.get_visible_gear() → resolve names → NarrativeBrief → PromptPack
- Containment boundary: no item_ids leak into NarrativeBrief
"""

import pytest

from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.lens.narrative_brief import (
    NarrativeBrief,
    assemble_narrative_brief,
    resolve_visible_gear_names,
)
from aidm.data.equipment_catalog_loader import EquipmentCatalog
from aidm.core.container_resolver import ContainerResolver
from aidm.schemas.prompt_pack import (
    PromptPack,
    TruthChannel,
)


# ══════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def catalog():
    """Equipment catalog for gear resolution."""
    return EquipmentCatalog()


@pytest.fixture
def resolver(catalog):
    """Container resolver for visible gear queries."""
    return ContainerResolver(catalog)


@pytest.fixture
def frozen():
    """FrozenWorldStateView for NarrativeBrief assembly."""
    ws = WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "fighter_1": {
                "name": "Aldric the Bold",
                "hp": 45,
                "hp_max": 50,
            },
            "goblin_1": {
                "name": "Goblin Warrior",
                "hp": 6,
                "hp_max": 10,
            },
        },
    )
    return FrozenWorldStateView(ws)


# ══════════════════════════════════════════════════════════════════════════
# NarrativeBrief visible_gear Field Tests
# ══════════════════════════════════════════════════════════════════════════


class TestVisibleGearField:
    """Tests for visible_gear field on NarrativeBrief."""

    def test_visible_gear_default_none(self):
        """visible_gear defaults to None."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
        )
        assert brief.visible_gear is None

    def test_visible_gear_set(self):
        """visible_gear accepts a list of strings."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
            visible_gear=["Longsword", "Shield, Heavy Wooden", "Rope, Hemp (50 ft.)"],
        )
        assert brief.visible_gear == ["Longsword", "Shield, Heavy Wooden", "Rope, Hemp (50 ft.)"]

    def test_visible_gear_in_to_dict(self):
        """visible_gear serializes to dict."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
            visible_gear=["Longsword", "Backpack"],
        )
        data = brief.to_dict()
        assert data["visible_gear"] == ["Longsword", "Backpack"]

    def test_visible_gear_none_in_to_dict(self):
        """visible_gear=None serializes as None."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
        )
        data = brief.to_dict()
        assert data["visible_gear"] is None

    def test_visible_gear_from_dict(self):
        """visible_gear deserializes from dict."""
        data = {
            "action_type": "attack_hit",
            "actor_name": "Aldric",
            "visible_gear": ["Torch", "Rope, Hemp (50 ft.)"],
        }
        brief = NarrativeBrief.from_dict(data)
        assert brief.visible_gear == ("Torch", "Rope, Hemp (50 ft.)")

    def test_visible_gear_missing_from_dict(self):
        """visible_gear defaults to None when missing from dict."""
        data = {
            "action_type": "attack_hit",
            "actor_name": "Aldric",
        }
        brief = NarrativeBrief.from_dict(data)
        assert brief.visible_gear is None


# ══════════════════════════════════════════════════════════════════════════
# resolve_visible_gear_names Tests
# ══════════════════════════════════════════════════════════════════════════


class TestResolveVisibleGearNames:
    """Tests for converting item_ids to display names."""

    def test_known_items_resolve(self, catalog):
        """Known catalog items resolve to their display names."""
        item_ids = ["longsword", "rope_hemp_50ft", "torch"]
        names = resolve_visible_gear_names(item_ids, catalog)
        assert "Longsword" in names
        assert "Rope, Hemp (50 ft.)" in names
        assert "Torch" in names

    def test_unknown_items_humanized(self, catalog):
        """Unknown items get humanized (underscores → spaces, title case)."""
        item_ids = ["magic_ring_of_fire"]
        names = resolve_visible_gear_names(item_ids, catalog)
        assert names == ["Magic Ring Of Fire"]

    def test_empty_list(self, catalog):
        """Empty item_ids returns empty names."""
        names = resolve_visible_gear_names([], catalog)
        assert names == []

    def test_none_catalog(self):
        """None catalog still humanizes item_ids."""
        item_ids = ["holy_symbol", "cloak_of_resistance"]
        names = resolve_visible_gear_names(item_ids, None)
        assert names == ["Holy Symbol", "Cloak Of Resistance"]

    def test_mixed_known_and_unknown(self, catalog):
        """Mix of known and unknown items."""
        item_ids = ["backpack", "legendary_artifact"]
        names = resolve_visible_gear_names(item_ids, catalog)
        assert names[0] == "Backpack"
        assert names[1] == "Legendary Artifact"


# ══════════════════════════════════════════════════════════════════════════
# Container Resolver → NarrativeBrief Pipeline Tests
# ══════════════════════════════════════════════════════════════════════════


class TestGearAffordancePipeline:
    """End-to-end tests: ContainerResolver → resolve_names → NarrativeBrief."""

    def test_visible_gear_from_inventory(self, resolver, catalog):
        """get_visible_gear extracts external/belt/in_hand items."""
        inventory = [
            {"item_id": "longsword", "quantity": 1, "stow_location": "in_hand"},
            {"item_id": "rope_hemp_50ft", "quantity": 1, "stow_location": "external"},
            {"item_id": "rations_trail", "quantity": 5, "stow_location": "in_pack"},
            {"item_id": "torch", "quantity": 2, "stow_location": "belt"},
        ]
        item_ids = resolver.get_visible_gear(inventory)
        # in_pack items should NOT be visible
        assert "rations_trail" not in item_ids
        # external, in_hand, belt items should be visible
        assert "longsword" in item_ids
        assert "rope_hemp_50ft" in item_ids
        assert "torch" in item_ids

    def test_pipeline_to_narrative_brief(self, resolver, catalog, frozen):
        """Full pipeline: inventory → visible_gear → resolve names → NarrativeBrief."""
        inventory = [
            {"item_id": "longsword", "quantity": 1, "stow_location": "in_hand"},
            {"item_id": "grappling_hook", "quantity": 1, "stow_location": "external"},
            {"item_id": "waterskin", "quantity": 1, "stow_location": "in_pack"},
        ]
        # Step 1: Box layer — get visible item_ids
        item_ids = resolver.get_visible_gear(inventory)

        # Step 2: Lens layer — resolve to display names
        gear_names = resolve_visible_gear_names(item_ids, catalog)

        # Step 3: Lens layer — assemble NarrativeBrief
        events = [
            {"event_id": 1, "type": "attack_roll",
             "attacker": "fighter_1", "target": "goblin_1",
             "weapon": "longsword"},
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=frozen,
            visible_gear=gear_names,
        )

        assert brief.visible_gear is not None
        assert "Longsword" in brief.visible_gear
        assert "Grappling Hook" in brief.visible_gear
        # in_pack item should NOT be in visible_gear
        assert "Waterskin" not in brief.visible_gear

    def test_pipeline_to_promptpack(self, resolver, catalog, frozen):
        """Full pipeline: NarrativeBrief.visible_gear → PromptPack.truth.visible_gear."""
        inventory = [
            {"item_id": "longsword", "quantity": 1, "stow_location": "in_hand"},
            {"item_id": "rope_hemp_50ft", "quantity": 1, "stow_location": "external"},
        ]
        item_ids = resolver.get_visible_gear(inventory)
        gear_names = resolve_visible_gear_names(item_ids, catalog)

        events = [
            {"event_id": 1, "type": "attack_roll",
             "attacker": "fighter_1", "target": "goblin_1"},
        ]
        brief = assemble_narrative_brief(
            events=events,
            narration_token="attack_hit",
            frozen_view=frozen,
            visible_gear=gear_names,
        )

        # Build PromptPack TruthChannel from NarrativeBrief
        truth = TruthChannel(
            action_type=brief.action_type,
            actor_name=brief.actor_name,
            target_name=brief.target_name,
            outcome_summary=brief.outcome_summary,
            severity=brief.severity,
            weapon_name=brief.weapon_name,
            visible_gear=brief.visible_gear,
        )
        pack = PromptPack(truth=truth)

        # Verify PromptPack serialization includes visible gear
        serialized = pack.serialize()
        assert "Visible Gear:" in serialized
        assert "Longsword" in serialized

        # Verify dict representation
        d = pack.to_dict()
        assert d["truth"]["visible_gear"] is not None
        assert "Longsword" in d["truth"]["visible_gear"]


# ══════════════════════════════════════════════════════════════════════════
# Containment Boundary Tests
# ══════════════════════════════════════════════════════════════════════════


class TestGearContainmentBoundary:
    """Verify no item_ids leak through to NarrativeBrief."""

    def test_no_item_ids_in_visible_gear(self, resolver, catalog, frozen):
        """visible_gear must contain display names, not item_ids."""
        inventory = [
            {"item_id": "grappling_hook", "quantity": 1, "stow_location": "external"},
            {"item_id": "rope_hemp_50ft", "quantity": 1, "stow_location": "external"},
        ]
        item_ids = resolver.get_visible_gear(inventory)
        gear_names = resolve_visible_gear_names(item_ids, catalog)

        brief = assemble_narrative_brief(
            events=[{"event_id": 1, "type": "attack_roll",
                     "attacker": "fighter_1", "target": "goblin_1"}],
            narration_token="attack_hit",
            frozen_view=frozen,
            visible_gear=gear_names,
        )

        # item_ids must NOT appear
        for gear_name in brief.visible_gear:
            assert "grappling_hook" not in gear_name
            assert "rope_hemp_50ft" not in gear_name
        # Display names should appear
        assert "Grappling Hook" in brief.visible_gear
        assert "Rope, Hemp (50 ft.)" in brief.visible_gear

    def test_hidden_pack_items_excluded(self, resolver, catalog, frozen):
        """Items in_pack must not appear in visible_gear."""
        inventory = [
            {"item_id": "longsword", "quantity": 1, "stow_location": "in_hand"},
            {"item_id": "potion_cure_light", "quantity": 3, "stow_location": "in_pack"},
            {"item_id": "spellbook", "quantity": 1, "stow_location": "in_pack"},
        ]
        item_ids = resolver.get_visible_gear(inventory)
        gear_names = resolve_visible_gear_names(item_ids, catalog)

        brief = assemble_narrative_brief(
            events=[{"event_id": 1, "type": "attack_roll",
                     "attacker": "fighter_1", "target": "goblin_1"}],
            narration_token="attack_hit",
            frozen_view=frozen,
            visible_gear=gear_names,
        )

        # Only in_hand items should be visible
        assert brief.visible_gear is not None
        assert len(brief.visible_gear) == 1
        assert "Longsword" in brief.visible_gear
