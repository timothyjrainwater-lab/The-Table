"""M3 Immersion Authority Contract Tests.

Mechanically enforces the non-authority boundary:
1. Immersion modules only import from allowed sources (schemas + WorldState read-only)
2. Immersion functions never write to WorldState, EntityState, or EngineResult
3. Immersion outputs have no mutation capability
4. No immersion module imports engine mutators (replay_runner, event_log, attack_resolver, etc.)

These tests exist as executable invariants — if they fail, immersion has
breached its authority boundary and the build must not proceed.
"""

import ast
import copy
import inspect
import json
import sys
from pathlib import Path

import pytest

from aidm.core.state import WorldState


# =============================================================================
# Allowed Import Whitelist
# =============================================================================

# Immersion modules may ONLY import from these aidm packages
_ALLOWED_AIDM_IMPORTS = frozenset({
    "aidm.schemas.immersion",
    "aidm.core.state",
    "aidm.immersion",
    "aidm.immersion.stt_adapter",
    "aidm.immersion.tts_adapter",
    "aidm.immersion.audio_mixer",
    "aidm.immersion.image_adapter",
    "aidm.immersion.contextual_grid",
    "aidm.immersion.attribution",
})

# Immersion modules must NEVER import from these (engine mutators)
_FORBIDDEN_IMPORTS = frozenset({
    "aidm.core.replay_runner",
    "aidm.core.event_log",
    "aidm.core.attack_resolver",
    "aidm.core.full_attack_resolver",
    "aidm.core.play_loop",
    "aidm.core.combat_controller",
    "aidm.core.initiative",
    "aidm.core.aoo",
    "aidm.core.conditions",
    "aidm.core.save_resolver",
    "aidm.core.maneuver_resolver",
    "aidm.core.rng_manager",
    "aidm.core.campaign_store",
    "aidm.core.prep_orchestrator",
    "aidm.core.asset_store",
    "aidm.core.world_archive",
    "aidm.schemas.attack",
    "aidm.schemas.conditions",
    "aidm.schemas.saves",
    "aidm.schemas.engine_result",
    "aidm.schemas.intent_lifecycle",
})


# =============================================================================
# Import Boundary Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestImportBoundary:
    """Verify immersion modules only import from allowed sources."""

    def _get_immersion_source_files(self):
        """Get all Python source files in aidm/immersion/."""
        immersion_dir = Path("aidm/immersion")
        return list(immersion_dir.glob("*.py"))

    def _extract_imports(self, filepath):
        """Extract all import statements from a Python file using AST."""
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def test_no_forbidden_imports(self):
        """Immersion modules must not import engine mutators."""
        violations = []
        for filepath in self._get_immersion_source_files():
            imports = self._extract_imports(filepath)
            for imp in imports:
                if imp in _FORBIDDEN_IMPORTS:
                    violations.append(f"{filepath.name} imports {imp}")

        assert violations == [], (
            f"Immersion authority breach — forbidden imports found:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_only_allowed_aidm_imports(self):
        """Immersion modules may only import from whitelisted aidm packages."""
        violations = []
        for filepath in self._get_immersion_source_files():
            imports = self._extract_imports(filepath)
            for imp in imports:
                if imp.startswith("aidm.") and imp not in _ALLOWED_AIDM_IMPORTS:
                    violations.append(f"{filepath.name} imports {imp}")

        assert violations == [], (
            f"Immersion imports outside allowed surface:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_no_rng_imports(self):
        """Immersion must never import RNG (determinism guarantee)."""
        for filepath in self._get_immersion_source_files():
            imports = self._extract_imports(filepath)
            for imp in imports:
                assert "rng" not in imp.lower(), (
                    f"{filepath.name} imports RNG-related module: {imp}"
                )

    def test_no_random_stdlib_import(self):
        """Immersion must not import stdlib random module."""
        for filepath in self._get_immersion_source_files():
            imports = self._extract_imports(filepath)
            assert "random" not in imports, (
                f"{filepath.name} imports stdlib random"
            )


# =============================================================================
# Non-Mutation Tests
# =============================================================================

class TestNonMutation:
    """Verify immersion functions never mutate engine state objects."""

    def _make_combat_world_state(self):
        """Create a WorldState with combat and entities for testing."""
        return WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "fighter_1": {
                    "name": "Fighter",
                    "hp": 45,
                    "ac": 18,
                    "team": "party",
                    "position": {"x": 2, "y": 3},
                    "conditions": {},
                },
                "goblin_1": {
                    "name": "Goblin",
                    "hp": 7,
                    "ac": 15,
                    "team": "hostile",
                    "position": {"x": 5, "y": 3},
                    "conditions": {},
                },
            },
            active_combat={
                "round": 2,
                "combatants": ["fighter_1", "goblin_1"],
                "current_turn": "fighter_1",
            },
        )

    def test_compute_scene_audio_state_no_mutation(self):
        """compute_scene_audio_state must not mutate any input."""
        from aidm.immersion import compute_scene_audio_state

        ws = self._make_combat_world_state()
        ws_snapshot = copy.deepcopy(ws)
        scene = {"ambient_light_level": "dark", "environmental_hazards": [{"type": "fire"}]}
        scene_snapshot = copy.deepcopy(scene)

        compute_scene_audio_state(ws, scene_card=scene)

        assert ws.to_dict() == ws_snapshot.to_dict()
        assert scene == scene_snapshot

    def test_compute_grid_state_no_mutation(self):
        """compute_grid_state must not mutate any input."""
        from aidm.immersion import compute_grid_state
        from aidm.schemas.immersion import GridRenderState

        ws = self._make_combat_world_state()
        ws_snapshot = copy.deepcopy(ws)
        prev = GridRenderState(visible=True, reason="combat_active")
        prev_snapshot = copy.deepcopy(prev)

        compute_grid_state(ws, previous=prev)

        assert ws.to_dict() == ws_snapshot.to_dict()
        assert prev.to_dict() == prev_snapshot.to_dict()

    def test_compute_scene_audio_preserves_nested_dicts(self):
        """Entity nested dicts (position, conditions) must survive untouched."""
        from aidm.immersion import compute_scene_audio_state

        ws = self._make_combat_world_state()
        original_positions = {
            eid: copy.deepcopy(e.get("position"))
            for eid, e in ws.entities.items()
            if isinstance(e, dict) and "position" in e
        }

        compute_scene_audio_state(ws)

        for eid, orig_pos in original_positions.items():
            assert ws.entities[eid]["position"] == orig_pos

    def test_compute_grid_preserves_nested_dicts(self):
        """Entity nested dicts must survive grid computation untouched."""
        from aidm.immersion import compute_grid_state

        ws = self._make_combat_world_state()
        original_entities = copy.deepcopy(ws.entities)

        compute_grid_state(ws)

        assert ws.entities == original_entities

    def test_state_hash_stable_through_full_pipeline(self):
        """WorldState hash must be identical before/after full immersion pipeline."""
        from aidm.immersion import compute_scene_audio_state, compute_grid_state

        ws = self._make_combat_world_state()
        hash_before = ws.state_hash()

        # Run full pipeline
        audio = compute_scene_audio_state(ws, scene_card={"ambient_light_level": "dim"})
        grid = compute_grid_state(ws)

        hash_after = ws.state_hash()
        assert hash_before == hash_after


# =============================================================================
# Output Isolation Tests
# =============================================================================

class TestOutputIsolation:
    """Verify immersion outputs cannot leak into engine state."""

    def test_audio_output_not_in_world_state(self):
        """Audio state fields must not appear in WorldState serialization."""
        from aidm.immersion import compute_scene_audio_state

        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
        )
        audio = compute_scene_audio_state(ws)

        ws_json = json.dumps(ws.to_dict(), sort_keys=True)
        assert "mood" not in ws_json
        assert "active_tracks" not in ws_json
        assert "transition_reason" not in ws_json

    def test_grid_output_not_in_world_state(self):
        """Grid state fields must not appear in WorldState serialization."""
        from aidm.immersion import compute_grid_state

        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"e1": {"position": {"x": 1, "y": 1}}},
            active_combat={"round": 1},
        )
        grid = compute_grid_state(ws)

        ws_json = json.dumps(ws.to_dict(), sort_keys=True)
        assert "entity_positions" not in ws_json
        assert "\"visible\"" not in ws_json
        assert "combat_active" not in ws_json

    def test_immersion_schemas_have_no_apply_method(self):
        """Immersion output schemas must not have apply/mutate methods."""
        from aidm.schemas.immersion import (
            SceneAudioState,
            GridRenderState,
            ImageResult,
            Transcript,
        )

        for schema_cls in [SceneAudioState, GridRenderState, ImageResult, Transcript]:
            members = dir(schema_cls)
            for member in members:
                assert "apply" not in member.lower() or member.startswith("_"), (
                    f"{schema_cls.__name__} has suspicious method: {member}"
                )
                assert "mutate" not in member.lower(), (
                    f"{schema_cls.__name__} has suspicious method: {member}"
                )
                assert "set_state" not in member.lower(), (
                    f"{schema_cls.__name__} has suspicious method: {member}"
                )
