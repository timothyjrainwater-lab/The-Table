"""M3 Immersion Integration Tests.

Acceptance criteria verification:
1. Voice I/O round-trip: STT stub → transcript → TTS stub → bytes output
2. Audio transitions: peaceful → combat → peaceful with correct mood/transition_reason
3. Images atmospheric only: stub returns placeholder, no engine state affected
4. Grid: invisible → visible (combat) → invisible (combat ended)
5. Attribution: add records, save JSON, load back, verify
6. Determinism: compute_scene_audio_state and compute_grid_state produce identical output 10×
7. Engine authority: verify immersion functions never mutate WorldState
"""

import json
import pytest
from pathlib import Path

from aidm.core.state import WorldState
from aidm.immersion import (
    AttributionStore,
    StubAudioMixerAdapter,
    StubImageAdapter,
    StubSTTAdapter,
    StubTTSAdapter,
    compute_grid_state,
    compute_scene_audio_state,
    create_image_adapter,
    create_stt_adapter,
    create_tts_adapter,
)
from aidm.schemas.immersion import (
    AttributionRecord,
    GridRenderState,
    ImageRequest,
    SceneAudioState,
    VoicePersona,
)


# =============================================================================
# Voice I/O Round-Trip
# =============================================================================

@pytest.mark.immersion_fast
class TestVoiceRoundTrip:
    """Full voice pipeline: STT → transcript → TTS → audio bytes."""

    def test_stt_to_tts_roundtrip(self):
        """Should produce valid output through full voice pipeline."""
        stt = create_stt_adapter("stub")
        tts = create_tts_adapter("stub")

        # STT: audio → transcript
        transcript = stt.transcribe(b"fake audio data", sample_rate=16000)
        assert transcript.text != ""
        assert transcript.validate() == []

        # TTS: text → audio bytes
        audio_out = tts.synthesize(transcript.text)
        assert isinstance(audio_out, bytes)

    def test_stt_to_tts_with_persona(self):
        """Should work with custom persona."""
        stt = create_stt_adapter()
        tts = create_tts_adapter()

        transcript = stt.transcribe(b"input")
        persona = VoicePersona(
            persona_id="npc_bartender",
            name="Bartender",
            voice_model="default",
        )
        audio = tts.synthesize(transcript.text, persona=persona)
        assert isinstance(audio, bytes)

    def test_all_adapters_available(self):
        """All stub adapters should report available."""
        assert create_stt_adapter().is_available()
        assert create_tts_adapter().is_available()


# =============================================================================
# Audio Transition Lifecycle
# =============================================================================

@pytest.mark.immersion_fast
class TestAudioTransitionLifecycle:
    """Full audio lifecycle: peaceful → combat → peaceful."""

    def test_peaceful_combat_peaceful_cycle(self):
        """Should track mood transitions through combat lifecycle."""
        mixer = StubAudioMixerAdapter()

        # Phase 1: Peaceful
        ws_peaceful = WorldState(ruleset_version="RAW_3.5")
        state1 = compute_scene_audio_state(ws_peaceful)
        mixer.apply_state(state1)
        assert state1.mood == "peaceful"

        # Phase 2: Combat starts
        ws_combat = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1, "combatants": ["fighter", "goblin"]},
        )
        state2 = compute_scene_audio_state(ws_combat, previous=state1)
        mixer.apply_state(state2)
        assert state2.mood == "combat"
        assert "peaceful -> combat" in state2.transition_reason

        # Phase 3: Combat ends
        ws_peaceful2 = WorldState(ruleset_version="RAW_3.5")
        state3 = compute_scene_audio_state(ws_peaceful2, previous=state2)
        mixer.apply_state(state3)
        assert state3.mood == "peaceful"
        assert "combat -> peaceful" in state3.transition_reason

        # Mixer should have recorded 3 states
        assert len(mixer.history) == 3

    def test_tense_transition_with_hazards(self):
        """Should go tense when hazards present."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"environmental_hazards": [{"type": "lava", "damage": "2d6"}]}

        state = compute_scene_audio_state(ws, scene_card=scene)
        assert state.mood == "tense"

    def test_mixer_stop_all(self):
        """Stop all should work."""
        mixer = StubAudioMixerAdapter()
        state = SceneAudioState(mood="combat")
        mixer.apply_state(state)
        mixer.stop_all()
        assert mixer.stopped is True


# =============================================================================
# Image Pipeline (Atmospheric Only)
# =============================================================================

@pytest.mark.immersion_fast
class TestImageAtmospheric:
    """Images are atmospheric — stub returns placeholder, no state change."""

    def test_stub_returns_placeholder(self):
        """Stub should return placeholder for all requests."""
        adapter = create_image_adapter()
        request = ImageRequest(
            kind="portrait",
            semantic_key="npc:theron:v1",
            prompt_context="A battle-scarred dwarf",
        )
        result = adapter.generate(request)
        assert result.status == "placeholder"
        assert result.validate() == []

    def test_image_does_not_affect_world_state(self):
        """Image generation should never mutate world state."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"fighter": {"hp": 45}},
        )
        original_hash = ws.state_hash()

        adapter = create_image_adapter()
        request = ImageRequest(kind="scene", semantic_key="tavern:v1")
        adapter.generate(request)

        assert ws.state_hash() == original_hash

    def test_all_image_kinds_produce_placeholders(self):
        """All image kinds should produce placeholder results."""
        adapter = StubImageAdapter()
        for kind in ("portrait", "scene", "backdrop"):
            request = ImageRequest(kind=kind, semantic_key=f"test:{kind}")
            result = adapter.generate(request)
            assert result.status == "placeholder"


# =============================================================================
# Grid Lifecycle
# =============================================================================

@pytest.mark.immersion_fast
class TestGridLifecycle:
    """Grid: invisible → visible (combat) → invisible (combat ended)."""

    def test_full_grid_lifecycle(self):
        """Grid should follow combat lifecycle."""
        # Phase 1: No combat → hidden
        ws_peace = WorldState(ruleset_version="RAW_3.5")
        g1 = compute_grid_state(ws_peace)
        assert g1.visible is False
        assert g1.reason == "no_combat"

        # Phase 2: Combat starts → visible
        ws_combat = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "fighter": {
                    "name": "Fighter",
                    "team": "party",
                    "position": {"x": 2, "y": 3},
                },
                "goblin": {
                    "name": "Goblin",
                    "team": "hostile",
                    "position": {"x": 5, "y": 3},
                },
            },
            active_combat={"round": 1},
        )
        g2 = compute_grid_state(ws_combat, previous=g1)
        assert g2.visible is True
        assert g2.reason == "combat_active"
        assert len(g2.entity_positions) == 2

        # Phase 3: Combat ends → hidden with combat_ended
        ws_peace2 = WorldState(ruleset_version="RAW_3.5")
        g3 = compute_grid_state(ws_peace2, previous=g2)
        assert g3.visible is False
        assert g3.reason == "combat_ended"

        # Phase 4: Still no combat → hidden with no_combat
        g4 = compute_grid_state(ws_peace2, previous=g3)
        assert g4.visible is False
        assert g4.reason == "no_combat"

    def test_grid_does_not_affect_world_state(self):
        """Grid computation should never mutate world state."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"e1": {"position": {"x": 1, "y": 1}}},
            active_combat={"round": 1},
        )
        original_hash = ws.state_hash()
        compute_grid_state(ws)
        assert ws.state_hash() == original_hash


# =============================================================================
# Attribution Lifecycle
# =============================================================================

@pytest.mark.immersion_fast
class TestAttributionLifecycle:
    """Attribution: add → save → load → verify."""

    def test_full_attribution_lifecycle(self, tmp_path):
        """Should survive add → save → load roundtrip."""
        store = AttributionStore()

        store.add(AttributionRecord(
            asset_id="scene_001",
            source="stub_generator",
            license="generated",
            author="aidm",
        ))
        store.add(AttributionRecord(
            asset_id="portrait_002",
            source="shared_cache",
            license="CC-BY-4.0",
            author="artist_name",
        ))

        path = tmp_path / "attribution.json"
        store.save(path)

        # Load into new store
        store2 = AttributionStore()
        store2.load(path)

        records = store2.list_records()
        assert len(records) == 2

        r1 = store2.get_by_asset_id("scene_001")
        assert r1 is not None
        assert r1.license == "generated"

        r2 = store2.get_by_asset_id("portrait_002")
        assert r2 is not None
        assert r2.license == "CC-BY-4.0"

    def test_attribution_json_sorted_keys(self, tmp_path):
        """Saved JSON should use sorted keys for determinism."""
        store = AttributionStore()
        store.add(AttributionRecord(asset_id="a1", license="MIT"))
        path = tmp_path / "attr.json"
        store.save(path)

        content = path.read_text()
        data = json.loads(content)
        expected = json.dumps(data, indent=2, sort_keys=True) + "\n"
        assert content == expected


# =============================================================================
# Determinism
# =============================================================================

@pytest.mark.immersion_fast
class TestImmersionDeterminism:
    """Verify deterministic output from pure functions."""

    def test_audio_state_deterministic_10x(self):
        """compute_scene_audio_state should be deterministic."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 2},
        )
        scene = {"ambient_light_level": "dim"}

        results = [
            compute_scene_audio_state(ws, scene_card=scene).to_dict()
            for _ in range(10)
        ]
        for r in results[1:]:
            assert r == results[0]

    def test_grid_state_deterministic_10x(self):
        """compute_grid_state should be deterministic."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "a": {"name": "A", "position": {"x": 1, "y": 2}},
                "b": {"name": "B", "position": {"x": 3, "y": 4}},
            },
            active_combat={"round": 1},
        )

        results = [
            compute_grid_state(ws).to_dict()
            for _ in range(10)
        ]
        for r in results[1:]:
            assert r == results[0]


# =============================================================================
# Engine Authority
# =============================================================================

@pytest.mark.immersion_fast
class TestEngineAuthority:
    """Verify immersion never mutates engine state."""

    def test_audio_does_not_mutate_world_state(self):
        """Audio computation should never mutate WorldState."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"fighter": {"hp": 45, "ac": 18}},
            active_combat={"round": 1},
        )
        original_hash = ws.state_hash()

        compute_scene_audio_state(ws)
        assert ws.state_hash() == original_hash

    def test_grid_does_not_mutate_world_state(self):
        """Grid computation should never mutate WorldState."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "e1": {"name": "E", "position": {"x": 1, "y": 1}},
            },
            active_combat={"round": 1},
        )
        original_hash = ws.state_hash()

        compute_grid_state(ws)
        assert ws.state_hash() == original_hash

    def test_stt_does_not_produce_engine_commands(self):
        """STT output is text only — never engine commands."""
        stt = StubSTTAdapter()
        transcript = stt.transcribe(b"audio")
        # Transcript is just text + confidence — no engine authority
        assert hasattr(transcript, "text")
        assert hasattr(transcript, "confidence")
        assert not hasattr(transcript, "engine_command")
        assert not hasattr(transcript, "state_mutation")
