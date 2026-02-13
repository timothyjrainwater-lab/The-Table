"""M3 Immersion Hardening Tests — Import safety, determinism proofs, non-authority guarantees.

Plan C hardening tests (C-01 through C-05):
- C-01: Package & import integrity
- C-02: Extended determinism proof (10× across all pure functions and moods)
- C-03: Optional dependency isolation (no external libs required)
- C-04: Non-authority enforcement (immersion never mutates engine state)
- C-05: Attribution ledger validation edge cases
"""

import copy
import json
import pytest
from pathlib import Path

from aidm.core.state import WorldState


# =============================================================================
# C-01 — Package & Import Integrity
# =============================================================================

@pytest.mark.immersion_fast
class TestImportIntegrity:
    """Verify immersion package is import-safe and exports are stable."""

    def test_import_aidm_immersion(self):
        """Top-level import should succeed without errors."""
        import aidm.immersion
        assert hasattr(aidm.immersion, "STTAdapter")
        assert hasattr(aidm.immersion, "compute_scene_audio_state")
        assert hasattr(aidm.immersion, "compute_grid_state")
        assert hasattr(aidm.immersion, "AttributionStore")

    def test_all_exports_present(self):
        """All __all__ symbols should be importable."""
        import aidm.immersion
        for name in aidm.immersion.__all__:
            assert hasattr(aidm.immersion, name), f"Missing export: {name}"

    def test_all_exports_are_callable_or_class(self):
        """All exports should be classes or functions."""
        import aidm.immersion
        for name in aidm.immersion.__all__:
            obj = getattr(aidm.immersion, name)
            assert callable(obj), f"{name} is not callable"

    def test_schema_imports(self):
        """Schema module should import cleanly."""
        from aidm.schemas.immersion import (
            Transcript,
            VoicePersona,
            AudioTrack,
            SceneAudioState,
            ImageRequest,
            ImageResult,
            GridEntityPosition,
            GridRenderState,
            AttributionRecord,
            AttributionLedger,
        )
        # All 10 schemas importable
        schemas = [
            Transcript, VoicePersona, AudioTrack, SceneAudioState,
            ImageRequest, ImageResult, GridEntityPosition, GridRenderState,
            AttributionRecord, AttributionLedger,
        ]
        assert len(schemas) == 10

    def test_submodule_imports(self):
        """Each submodule should import independently."""
        from aidm.immersion import stt_adapter
        from aidm.immersion import tts_adapter
        from aidm.immersion import audio_mixer
        from aidm.immersion import image_adapter
        from aidm.immersion import contextual_grid
        from aidm.immersion import attribution

        assert hasattr(stt_adapter, "STTAdapter")
        assert hasattr(tts_adapter, "TTSAdapter")
        assert hasattr(audio_mixer, "compute_scene_audio_state")
        assert hasattr(image_adapter, "ImageAdapter")
        assert hasattr(contextual_grid, "compute_grid_state")
        assert hasattr(attribution, "AttributionStore")

    def test_no_circular_imports(self):
        """Immersion should not cause circular import issues."""
        import importlib
        # Force fresh re-import
        mod = importlib.import_module("aidm.immersion")
        assert mod is not None


# =============================================================================
# C-02 — Extended Determinism Proofs (10×)
# =============================================================================

@pytest.mark.immersion_fast
class TestExtendedDeterminism:
    """Extended determinism proofs across all moods and scenarios."""

    def test_audio_combat_mood_deterministic_10x(self):
        """Combat mood should be identical 10 times."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 3, "combatants": ["a", "b", "c"]},
        )
        from aidm.immersion import compute_scene_audio_state
        results = [compute_scene_audio_state(ws).to_dict() for _ in range(10)]
        for r in results[1:]:
            assert r == results[0]

    def test_audio_tense_hazards_deterministic_10x(self):
        """Tense mood from hazards should be identical 10 times."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"environmental_hazards": [{"type": "lava", "damage": "2d6"}]}
        from aidm.immersion import compute_scene_audio_state
        results = [
            compute_scene_audio_state(ws, scene_card=scene).to_dict()
            for _ in range(10)
        ]
        for r in results[1:]:
            assert r == results[0]

    def test_audio_tense_dark_deterministic_10x(self):
        """Tense mood from darkness should be identical 10 times."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"ambient_light_level": "dark"}
        from aidm.immersion import compute_scene_audio_state
        results = [
            compute_scene_audio_state(ws, scene_card=scene).to_dict()
            for _ in range(10)
        ]
        for r in results[1:]:
            assert r == results[0]

    def test_audio_peaceful_deterministic_10x(self):
        """Peaceful mood should be identical 10 times."""
        ws = WorldState(ruleset_version="RAW_3.5")
        from aidm.immersion import compute_scene_audio_state
        results = [compute_scene_audio_state(ws).to_dict() for _ in range(10)]
        for r in results[1:]:
            assert r == results[0]

    def test_audio_transition_deterministic_10x(self):
        """Transition from peaceful to combat should be identical 10 times."""
        from aidm.immersion import compute_scene_audio_state
        from aidm.schemas.immersion import SceneAudioState

        prev = SceneAudioState(mood="peaceful")
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
        )
        results = [
            compute_scene_audio_state(ws, previous=prev).to_dict()
            for _ in range(10)
        ]
        for r in results[1:]:
            assert r == results[0]

    def test_grid_many_entities_deterministic_10x(self):
        """Grid with many entities should be identical 10 times."""
        entities = {}
        for i in range(20):
            entities[f"entity_{i:03d}"] = {
                "name": f"Entity {i}",
                "team": "party" if i % 2 == 0 else "hostile",
                "position": {"x": i * 2, "y": i * 3},
            }
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities=entities,
            active_combat={"round": 1},
        )
        from aidm.immersion import compute_grid_state
        results = [compute_grid_state(ws).to_dict() for _ in range(10)]
        for r in results[1:]:
            assert r == results[0]

    def test_grid_transition_deterministic_10x(self):
        """Grid transition from visible to hidden should be identical 10 times."""
        from aidm.immersion import compute_grid_state
        from aidm.schemas.immersion import GridRenderState

        prev = GridRenderState(visible=True, reason="combat_active")
        ws = WorldState(ruleset_version="RAW_3.5")
        results = [
            compute_grid_state(ws, previous=prev).to_dict()
            for _ in range(10)
        ]
        for r in results[1:]:
            assert r == results[0]

    def test_attribution_save_deterministic_10x(self, tmp_path):
        """Attribution JSON output should be byte-identical 10 times."""
        from aidm.immersion import AttributionStore
        from aidm.schemas.immersion import AttributionRecord

        store = AttributionStore()
        store.add(AttributionRecord(asset_id="a1", source="gen", license="MIT", author="sys"))
        store.add(AttributionRecord(asset_id="b2", source="cache", license="CC-BY-4.0", author="art"))

        contents = []
        for i in range(10):
            path = tmp_path / f"attr_{i}.json"
            store.save(path)
            contents.append(path.read_text())

        for c in contents[1:]:
            assert c == contents[0]

    def test_no_timestamps_in_audio_output(self):
        """Audio state output should contain no timestamps or random values."""
        ws = WorldState(ruleset_version="RAW_3.5", active_combat={"round": 1})
        from aidm.immersion import compute_scene_audio_state
        result = compute_scene_audio_state(ws)
        d = result.to_dict()
        serialized = json.dumps(d, sort_keys=True)
        # No timestamp-like patterns
        assert "time" not in serialized.lower() or "transition" in serialized.lower()
        assert "random" not in serialized.lower()
        assert "uuid" not in serialized.lower()

    def test_no_timestamps_in_grid_output(self):
        """Grid state output should contain no timestamps or random values."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"e1": {"position": {"x": 1, "y": 2}}},
            active_combat={"round": 1},
        )
        from aidm.immersion import compute_grid_state
        result = compute_grid_state(ws)
        d = result.to_dict()
        serialized = json.dumps(d, sort_keys=True)
        assert "random" not in serialized.lower()
        assert "uuid" not in serialized.lower()


# =============================================================================
# C-03 — Optional Dependency Isolation
# =============================================================================

@pytest.mark.immersion_fast
class TestDependencyIsolation:
    """Verify no external dependencies are required for immersion."""

    def test_stt_stub_no_external_deps(self):
        """StubSTTAdapter should work without any external libraries."""
        from aidm.immersion.stt_adapter import StubSTTAdapter
        adapter = StubSTTAdapter()
        result = adapter.transcribe(b"test data")
        assert result.text != ""
        assert adapter.is_available()

    def test_tts_stub_no_external_deps(self):
        """StubTTSAdapter should work without any external libraries."""
        from aidm.immersion.tts_adapter import StubTTSAdapter
        adapter = StubTTSAdapter()
        result = adapter.synthesize("hello")
        assert isinstance(result, bytes)
        assert adapter.is_available()

    def test_image_stub_no_external_deps(self):
        """StubImageAdapter should work without any external libraries."""
        from aidm.immersion.image_adapter import StubImageAdapter
        from aidm.schemas.immersion import ImageRequest
        adapter = StubImageAdapter()
        request = ImageRequest(kind="scene", semantic_key="test:v1")
        result = adapter.generate(request)
        assert result.status == "placeholder"
        assert adapter.is_available()

    def test_audio_mixer_stub_no_external_deps(self):
        """StubAudioMixerAdapter should work without any external libraries."""
        from aidm.immersion.audio_mixer import StubAudioMixerAdapter
        from aidm.schemas.immersion import SceneAudioState
        mixer = StubAudioMixerAdapter()
        mixer.apply_state(SceneAudioState(mood="combat"))
        mixer.stop_all()
        assert mixer.is_available()

    def test_factory_defaults_never_raise_import_error(self):
        """All factory defaults should never raise ImportError."""
        from aidm.immersion.stt_adapter import create_stt_adapter
        from aidm.immersion.tts_adapter import create_tts_adapter
        from aidm.immersion.image_adapter import create_image_adapter
        # Default backend ("stub") should never fail
        stt = create_stt_adapter()
        tts = create_tts_adapter()
        img = create_image_adapter()
        assert stt.is_available()
        assert tts.is_available()
        assert img.is_available()

    def test_pure_functions_no_external_deps(self):
        """Pure functions should work without external libraries."""
        from aidm.immersion.audio_mixer import compute_scene_audio_state
        from aidm.immersion.contextual_grid import compute_grid_state
        ws = WorldState(ruleset_version="RAW_3.5")
        audio = compute_scene_audio_state(ws)
        grid = compute_grid_state(ws)
        assert audio.mood == "peaceful"
        assert grid.visible is False

    def test_attribution_no_external_deps(self, tmp_path):
        """AttributionStore should work without external libraries."""
        from aidm.immersion.attribution import AttributionStore
        from aidm.schemas.immersion import AttributionRecord
        store = AttributionStore()
        store.add(AttributionRecord(asset_id="a1", license="MIT"))
        path = tmp_path / "test.json"
        store.save(path)
        store2 = AttributionStore()
        store2.load(path)
        assert len(store2.list_records()) == 1


# =============================================================================
# C-04 — Non-Authority Enforcement
# =============================================================================

@pytest.mark.immersion_fast
class TestNonAuthorityEnforcement:
    """Prove immersion cannot affect engine reality — stronger checks."""

    def test_audio_preserves_entity_dict_identity(self):
        """Audio computation must not replace or modify entity dicts."""
        entities = {
            "fighter": {"hp": 45, "ac": 18, "name": "Fighter"},
            "goblin": {"hp": 12, "ac": 15, "name": "Goblin"},
        }
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities=entities,
            active_combat={"round": 1},
        )
        entities_before = copy.deepcopy(ws.entities)
        from aidm.immersion import compute_scene_audio_state
        compute_scene_audio_state(ws)
        assert ws.entities == entities_before

    def test_grid_preserves_entity_dict_identity(self):
        """Grid computation must not replace or modify entity dicts."""
        entities = {
            "fighter": {"hp": 45, "position": {"x": 2, "y": 3}},
            "goblin": {"hp": 12, "position": {"x": 5, "y": 3}},
        }
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities=entities,
            active_combat={"round": 1},
        )
        entities_before = copy.deepcopy(ws.entities)
        from aidm.immersion import compute_grid_state
        compute_grid_state(ws)
        assert ws.entities == entities_before

    def test_audio_preserves_active_combat(self):
        """Audio computation must not modify active_combat dict."""
        combat = {"round": 3, "combatants": ["a", "b"]}
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat=combat,
        )
        combat_before = copy.deepcopy(ws.active_combat)
        from aidm.immersion import compute_scene_audio_state
        compute_scene_audio_state(ws)
        assert ws.active_combat == combat_before

    def test_grid_preserves_active_combat(self):
        """Grid computation must not modify active_combat dict."""
        combat = {"round": 2, "combatants": ["x", "y"]}
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"x": {"position": {"x": 0, "y": 0}}},
            active_combat=combat,
        )
        combat_before = copy.deepcopy(ws.active_combat)
        from aidm.immersion import compute_grid_state
        compute_grid_state(ws)
        assert ws.active_combat == combat_before

    def test_audio_state_hash_unchanged(self):
        """WorldState hash must be identical before and after audio computation."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"e1": {"hp": 20, "ac": 14}},
            active_combat={"round": 1},
        )
        hash_before = ws.state_hash()
        from aidm.immersion import compute_scene_audio_state
        compute_scene_audio_state(ws, scene_card={"environmental_hazards": [{"type": "fire"}]})
        assert ws.state_hash() == hash_before

    def test_grid_state_hash_unchanged(self):
        """WorldState hash must be identical before and after grid computation."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "a": {"position": {"x": 1, "y": 2}},
                "b": {"position": {"x": 3, "y": 4}},
            },
            active_combat={"round": 1},
        )
        hash_before = ws.state_hash()
        from aidm.immersion import compute_grid_state
        compute_grid_state(ws)
        assert ws.state_hash() == hash_before

    def test_immersion_output_excluded_from_world_state(self):
        """Immersion outputs must not appear in WorldState serialization."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
        )
        from aidm.immersion import compute_scene_audio_state, compute_grid_state
        audio = compute_scene_audio_state(ws)
        grid = compute_grid_state(ws)

        ws_dict = ws.to_dict()
        ws_json = json.dumps(ws_dict, sort_keys=True)

        # Immersion outputs must not leak into world state
        assert "mood" not in ws_json
        assert "transition_reason" not in ws_json
        assert "visible" not in ws_json
        assert "entity_positions" not in ws_json

    def test_tts_output_has_no_state_mutation_capability(self):
        """TTS adapter output is bytes only — no mutation methods."""
        from aidm.immersion import StubTTSAdapter
        tts = StubTTSAdapter()
        output = tts.synthesize("test")
        # Output is raw bytes — no state mutation possible
        assert type(output) is bytes

    def test_image_adapter_returns_no_state_changes(self):
        """Image adapter result must not contain state change instructions."""
        from aidm.immersion import StubImageAdapter
        from aidm.schemas.immersion import ImageRequest
        adapter = StubImageAdapter()
        result = adapter.generate(ImageRequest(kind="scene", semantic_key="k"))
        result_dict = result.to_dict()
        # No state-changing fields
        assert "state_change" not in result_dict
        assert "mutation" not in json.dumps(result_dict)


# =============================================================================
# C-05 — Attribution Ledger Validation Edge Cases
# =============================================================================

@pytest.mark.immersion_fast
class TestAttributionValidation:
    """Extended attribution validation and edge cases."""

    def test_placeholder_asset_attribution(self, tmp_path):
        """Placeholder assets should be explicitly marked."""
        from aidm.immersion import AttributionStore
        from aidm.schemas.immersion import AttributionRecord
        store = AttributionStore()
        store.add(AttributionRecord(
            asset_id="placeholder_001",
            source="stub_generator",
            license="generated",
            author="aidm_system",
        ))
        record = store.get_by_asset_id("placeholder_001")
        assert record.license == "generated"
        assert record.source == "stub_generator"

    def test_attribution_rejects_missing_required_fields(self):
        """Should reject records missing asset_id or license."""
        from aidm.immersion import AttributionStore
        from aidm.schemas.immersion import AttributionRecord
        store = AttributionStore()

        # Missing asset_id
        with pytest.raises(ValueError, match="asset_id"):
            store.add(AttributionRecord(license="MIT"))

        # Missing license
        with pytest.raises(ValueError, match="license"):
            store.add(AttributionRecord(asset_id="a1"))

        # Both missing
        with pytest.raises(ValueError):
            store.add(AttributionRecord())

    def test_attribution_roundtrip_preserves_all_fields(self, tmp_path):
        """Save/load roundtrip must preserve all fields exactly."""
        from aidm.immersion import AttributionStore
        from aidm.schemas.immersion import AttributionRecord
        store = AttributionStore()
        store.add(AttributionRecord(
            asset_id="detailed_001",
            source="shared_cache",
            license="CC-BY-4.0",
            author="artist_name",
        ))

        path = tmp_path / "roundtrip.json"
        store.save(path)

        store2 = AttributionStore()
        store2.load(path)

        record = store2.get_by_asset_id("detailed_001")
        assert record.asset_id == "detailed_001"
        assert record.source == "shared_cache"
        assert record.license == "CC-BY-4.0"
        assert record.author == "artist_name"

    def test_attribution_no_binary_content(self, tmp_path):
        """Attribution JSON should contain no binary content — text only."""
        from aidm.immersion import AttributionStore
        from aidm.schemas.immersion import AttributionRecord
        store = AttributionStore()
        store.add(AttributionRecord(asset_id="a1", license="MIT"))
        path = tmp_path / "attr.json"
        store.save(path)

        content = path.read_bytes()
        # Should be valid UTF-8 text
        text = content.decode("utf-8")
        # Should be valid JSON
        data = json.loads(text)
        assert isinstance(data, dict)

    def test_empty_ledger_valid_json(self, tmp_path):
        """Empty attribution store should produce valid JSON."""
        from aidm.immersion import AttributionStore
        store = AttributionStore()
        path = tmp_path / "empty.json"
        store.save(path)

        with open(path) as f:
            data = json.load(f)
        assert data["schema_version"] == "1.0"
        assert data["records"] == []

    def test_attribution_sorted_records(self):
        """Records should always be listed in sorted order."""
        from aidm.immersion import AttributionStore
        from aidm.schemas.immersion import AttributionRecord
        store = AttributionStore()
        for aid in ["zzz", "aaa", "mmm", "bbb"]:
            store.add(AttributionRecord(asset_id=aid, license="MIT"))
        records = store.list_records()
        ids = [r.asset_id for r in records]
        assert ids == ["aaa", "bbb", "mmm", "zzz"]
