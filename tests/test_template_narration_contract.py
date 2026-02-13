"""WO-048/WO-049: Template Narration Contract Tests

Locks the template interpolation contract to prevent regression.
Ensures the 5 micro-scenario turn archetypes produce correct,
entity-specific narration text with no placeholder leaks.

Test Categories:
1. _build_template_context unit tests (5 tests)
2. End-to-end narration snapshot tests for 5 archetypes (5 tests)
3. No-forbidden-tokens tests (3 tests)
4. Severity-branched template selection (4 tests, WO-049)
5. Provenance tag test (1 test)

Total: 18 tests
"""

import pytest

from aidm.core.state import WorldState
from aidm.interaction.intent_bridge import IntentBridge
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.narrative_brief import NarrativeBrief
from aidm.lens.scene_manager import Exit, SceneManager, SceneState
from aidm.narration.guarded_narration_service import GuardedNarrationService
from aidm.narration.narrator import NarrationTemplates
from aidm.runtime.session_orchestrator import (
    SessionOrchestrator,
    _build_template_context,
)
from aidm.schemas.entity_fields import EF
from aidm.spark.dm_persona import DMPersona


# ======================================================================
# FIXTURES
# ======================================================================


def _make_orchestrator(seed=42):
    """Factory for a deterministic orchestrator with known entities."""
    ws = WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Kael the Steadfast",
                EF.TEAM: "party",
                EF.LEVEL: 3,
                EF.HP_CURRENT: 28,
                EF.HP_MAX: 28,
                EF.AC: 17,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 7,
                EF.BAB: 3,
                EF.STR_MOD: 3,
                EF.WEAPON: "longsword",
                "weapon_damage": "1d8+3",
                EF.DEX_MOD: 1,
                EF.POSITION: {"x": 5, "y": 5},
            },
            "goblin_1": {
                EF.ENTITY_ID: "goblin_1",
                "name": "Goblin Spearman",
                EF.TEAM: "enemy",
                EF.LEVEL: 1,
                EF.HP_CURRENT: 5,
                EF.HP_MAX: 5,
                EF.AC: 14,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 2,
                EF.DEX_MOD: 1,
                EF.POSITION: {"x": 6, "y": 5},
            },
        },
    )
    scenes = {
        "room_a": SceneState(
            scene_id="room_a",
            name="Room A",
            description="A room.",
            exits=[
                Exit(
                    exit_id="east",
                    destination_scene_id="room_b",
                    description="East door",
                    locked=False,
                    hidden=False,
                ),
            ],
        ),
        "room_b": SceneState(
            scene_id="room_b",
            name="Room B",
            description="Another room.",
            exits=[],
        ),
    }
    return SessionOrchestrator(
        world_state=ws,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes=scenes),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=seed,
    )


# ======================================================================
# CATEGORY 1: _build_template_context unit tests (5 tests)
# ======================================================================


class TestBuildTemplateContext:
    """Unit tests for the pure _build_template_context function."""

    def test_attack_hit_context(self):
        """Attack hit brief produces correct context dict."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            target_name="Goblin",
            weapon_name="longsword",
            damage_type="slashing",
        )
        events = [
            {"type": "attack_roll", "hit": True, "d20_result": 15},
            {"type": "hp_changed", "entity_id": "goblin_1", "delta": -8},
        ]
        ctx = _build_template_context(brief, events)

        assert ctx["actor_name"] == "Kael"
        assert ctx["target_name"] == "Goblin"
        assert ctx["weapon_name"] == "longsword"
        assert ctx["damage"] == "8"
        assert ctx["damage_type"] == "slashing"

    def test_attack_miss_context(self):
        """Attack miss brief produces context with empty damage."""
        brief = NarrativeBrief(
            action_type="attack_miss",
            actor_name="Kael",
            target_name="Goblin",
            weapon_name="longsword",
        )
        events = [
            {"type": "attack_roll", "hit": False, "d20_result": 3},
        ]
        ctx = _build_template_context(brief, events)

        assert ctx["actor_name"] == "Kael"
        assert ctx["target_name"] == "Goblin"
        assert ctx["damage"] == ""  # No damage on miss

    def test_movement_context(self):
        """Movement brief produces actor name, no target/weapon/damage."""
        brief = NarrativeBrief(
            action_type="movement",
            actor_name="Kael",
        )
        events = [{"type": "movement", "entity_id": "pc_fighter"}]
        ctx = _build_template_context(brief, events)

        assert ctx["actor_name"] == "Kael"
        assert ctx["target_name"] == ""
        assert ctx["weapon_name"] == ""
        assert ctx["damage"] == ""

    def test_scene_transition_context(self):
        """Scene transition brief uses party as actor."""
        brief = NarrativeBrief(
            action_type="scene_transition",
            actor_name="The party",
        )
        events = []
        ctx = _build_template_context(brief, events)

        assert ctx["actor_name"] == "The party"

    def test_rest_context(self):
        """Rest brief uses party as actor."""
        brief = NarrativeBrief(
            action_type="rest",
            actor_name="The party",
        )
        events = []
        ctx = _build_template_context(brief, events)

        assert ctx["actor_name"] == "The party"


# ======================================================================
# CATEGORY 2: End-to-end narration snapshot tests (5 tests)
# ======================================================================


class TestNarrationSnapshots:
    """End-to-end tests: orchestrator turn -> narration text with real names."""

    def test_attack_narration_contains_entity_names(self):
        """Attack narration must contain both actor and target names."""
        # Use a seed that produces a hit
        for seed in range(50):
            orch = _make_orchestrator(seed=seed)
            result = orch.process_text_turn("attack Goblin Spearman", "pc_fighter")
            if any(e.get("type") == "attack_roll" and e.get("hit") for e in result.events):
                assert "Kael the Steadfast" in result.narration_text
                assert "Goblin Spearman" in result.narration_text
                return
        pytest.fail("No hit found in 50 seeds")

    def test_attack_miss_narration_contains_entity_names(self):
        """Attack miss narration must contain both entity names."""
        for seed in range(50):
            orch = _make_orchestrator(seed=seed)
            result = orch.process_text_turn("attack Goblin Spearman", "pc_fighter")
            if not any(e.get("type") == "attack_roll" and e.get("hit") for e in result.events):
                assert "Kael the Steadfast" in result.narration_text
                assert "Goblin Spearman" in result.narration_text
                return
        pytest.fail("No miss found in 50 seeds")

    def test_movement_narration_contains_actor_name(self):
        """Movement narration must contain actor name."""
        orch = _make_orchestrator(seed=42)
        result = orch.process_text_turn("move to 5,5", "pc_fighter")
        assert "Kael the Steadfast" in result.narration_text

    def test_scene_transition_narration_no_something_happens(self):
        """Scene transition must not produce 'Something happens...'."""
        orch = _make_orchestrator(seed=42)
        orch.load_scene("room_a")
        result = orch.process_text_turn("go east", "pc_fighter")
        assert "Something happens" not in result.narration_text

    def test_rest_narration_no_something_happens(self):
        """Rest must not produce 'Something happens...'."""
        orch = _make_orchestrator(seed=42)
        orch.load_scene("room_a")
        result = orch.process_text_turn("rest", "pc_fighter")
        assert "Something happens" not in result.narration_text


# ======================================================================
# CATEGORY 3: No-forbidden-tokens tests (3 tests)
# ======================================================================


FORBIDDEN_GENERIC_TOKENS = [
    "Something happens",
    "The attacker",
    "the target",
]


class TestNoForbiddenTokens:
    """Template output must not contain generic placeholder text."""

    def test_attack_no_generic_placeholders(self):
        """Attack narration must not contain 'The attacker' or 'the target'."""
        for seed in range(20):
            orch = _make_orchestrator(seed=seed)
            result = orch.process_text_turn("attack Goblin Spearman", "pc_fighter")
            for forbidden in FORBIDDEN_GENERIC_TOKENS:
                assert forbidden not in result.narration_text, (
                    f"seed={seed}: narration contains forbidden token '{forbidden}': "
                    f"{result.narration_text!r}"
                )

    def test_movement_no_generic_placeholders(self):
        """Movement narration must not contain generic placeholders."""
        orch = _make_orchestrator(seed=42)
        result = orch.process_text_turn("move to 5,5", "pc_fighter")
        for forbidden in FORBIDDEN_GENERIC_TOKENS:
            assert forbidden not in result.narration_text

    def test_all_micro_scenario_archetypes_no_forbidden(self):
        """All 5 turn archetypes produce narration without forbidden tokens."""
        orch = _make_orchestrator(seed=0)
        orch.load_scene("room_a")

        commands = [
            "attack Goblin Spearman",
            "move to 5,5",
            "go east",
            "rest",
        ]

        for cmd in commands:
            result = orch.process_text_turn(cmd, "pc_fighter")
            for forbidden in FORBIDDEN_GENERIC_TOKENS:
                assert forbidden not in result.narration_text, (
                    f"Command '{cmd}' produced forbidden token '{forbidden}': "
                    f"{result.narration_text!r}"
                )


# ======================================================================
# CATEGORY 4: Severity-branched template selection (WO-049, 4 tests)
# ======================================================================


class TestSeverityBranchedTemplates:
    """WO-049: Severity-branched template selection for combat tokens."""

    def test_get_template_with_severity_returns_branch(self):
        """get_template(token, severity) returns severity-specific branch."""
        template = NarrationTemplates.get_template("attack_hit", severity="lethal")
        assert "crumbles" in template or "cleaves" in template

    def test_get_template_without_severity_returns_flat(self):
        """get_template(token) without severity returns flat template."""
        template = NarrationTemplates.get_template("attack_hit")
        flat = NarrationTemplates.TEMPLATES["attack_hit"]
        assert template == flat

    def test_non_combat_token_ignores_severity(self):
        """Non-combat tokens ignore severity and return flat template."""
        template_with = NarrationTemplates.get_template("movement", severity="severe")
        template_without = NarrationTemplates.get_template("movement")
        assert template_with == template_without

    def test_lethal_hit_narration_contains_defeat_language(self):
        """Lethal severity attack produces defeat-flavored narration."""
        # Seed 0 produces a lethal hit (11 damage vs 5 HP goblin)
        orch = _make_orchestrator(seed=0)
        result = orch.process_text_turn("attack Goblin Spearman", "pc_fighter")
        # Should use lethal template with "crumbles and falls"
        assert "crumbles" in result.narration_text or "falls" in result.narration_text


# ======================================================================
# CATEGORY 5: Provenance tag test (1 test)
# ======================================================================


class TestProvenanceTag:
    """Template narration must be tagged with correct provenance."""

    def test_template_narration_provenance(self):
        """All template narration outputs must have [NARRATIVE:TEMPLATE] provenance."""
        orch = _make_orchestrator(seed=42)
        orch.load_scene("room_a")

        commands = [
            "attack Goblin Spearman",
            "move to 5,5",
            "go east",
            "rest",
        ]

        for cmd in commands:
            result = orch.process_text_turn(cmd, "pc_fighter")
            if result.success and result.narration_text:
                assert result.provenance == "[NARRATIVE:TEMPLATE]", (
                    f"Command '{cmd}' has wrong provenance: {result.provenance}"
                )
