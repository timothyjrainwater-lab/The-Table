"""M3 Immersion Determinism Canary — Regression detector for non-deterministic behavior.

This test file serves as a **canary** for determinism regressions in the immersion layer.
If ANY test in this file fails, it signals a **critical regression** — determinism is broken.

Purpose:
- Automated CI/CD gate: If this fails, the build must not proceed
- Protects against accidental introduction of RNG, timestamps, UUIDs, or other non-deterministic sources
- Validates that identical inputs ALWAYS produce identical outputs across ALL immersion functions

Coverage:
- All pure functions: compute_scene_audio_state, compute_grid_state
- All schemas: to_dict/from_dict roundtrips must be deterministic
- All adapters: stub adapters must return deterministic outputs

Test strategy:
- Run each function 100× with identical inputs
- Assert all outputs are byte-for-byte identical (via to_dict() serialization)
- Use aggressive iteration counts (100×) to catch statistical flakiness

If a test fails here:
1. Identify the non-deterministic source (check git diff for recent changes)
2. Remove RNG, timestamps, UUIDs, or randomized dict iteration
3. Ensure all outputs are derived purely from inputs
4. Re-run this test file until all tests pass
5. Do NOT merge until this file passes 100%

Maintenance:
- When adding new immersion functions, add a corresponding canary test here
- When extending schemas, ensure new fields are deterministic
- Run this test file before every commit to immersion modules
"""

import json
import pytest

from aidm.core.state import WorldState
from aidm.immersion import (
    StubAudioMixerAdapter,
    StubImageAdapter,
    StubSTTAdapter,
    StubTTSAdapter,
    compute_grid_state,
    compute_scene_audio_state,
)
from aidm.schemas.immersion import (
    AttributionLedger,
    AttributionRecord,
    AudioTrack,
    GridEntityPosition,
    GridRenderState,
    ImageRequest,
    ImageResult,
    SceneAudioState,
    Transcript,
    VoicePersona,
)


# =============================================================================
# Pure Function Determinism Canaries
# =============================================================================

@pytest.mark.immersion_fast
class TestPureFunctionDeterminism:
    """Canary tests for pure function determinism (100× iterations)."""

    def test_compute_scene_audio_state_100x_peaceful(self):
        """100× peaceful mood computation must be identical."""
        ws = WorldState(ruleset_version="RAW_3.5")
        results = [compute_scene_audio_state(ws) for _ in range(100)]
        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first, "Non-determinism detected in compute_scene_audio_state (peaceful)"

    def test_compute_scene_audio_state_100x_combat(self):
        """100× combat mood computation must be identical."""
        ws = WorldState(ruleset_version="RAW_3.5", active_combat={"round": 1})
        results = [compute_scene_audio_state(ws) for _ in range(100)]
        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first, "Non-determinism detected in compute_scene_audio_state (combat)"

    def test_compute_scene_audio_state_100x_tense_hazards(self):
        """100× tense mood (hazards) computation must be identical."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"environmental_hazards": [{"type": "lava"}]}
        results = [compute_scene_audio_state(ws, scene_card=scene) for _ in range(100)]
        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first, "Non-determinism detected in compute_scene_audio_state (tense/hazards)"

    def test_compute_scene_audio_state_100x_tense_dark(self):
        """100× tense mood (darkness) computation must be identical."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"ambient_light_level": "dark"}
        results = [compute_scene_audio_state(ws, scene_card=scene) for _ in range(100)]
        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first, "Non-determinism detected in compute_scene_audio_state (tense/dark)"

    def test_compute_grid_state_100x_combat_active(self):
        """100× grid state (combat active) computation must be identical."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
            entities={
                "fighter": {"position": {"x": 0, "y": 0}, "name": "Fighter", "team": "PCs"},
                "goblin": {"position": {"x": 5, "y": 5}, "name": "Goblin", "team": "Enemies"},
            },
        )
        results = [compute_grid_state(ws) for _ in range(100)]
        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first, "Non-determinism detected in compute_grid_state (combat)"

    def test_compute_grid_state_100x_no_combat(self):
        """100× grid state (no combat) computation must be identical."""
        ws = WorldState(ruleset_version="RAW_3.5")
        results = [compute_grid_state(ws) for _ in range(100)]
        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first, "Non-determinism detected in compute_grid_state (no combat)"

    def test_compute_grid_state_100x_combat_ended(self):
        """100× grid state (combat ended) transition must be identical."""
        prev = GridRenderState(visible=True, reason="combat_active")
        ws = WorldState(ruleset_version="RAW_3.5")
        results = [compute_grid_state(ws, previous=prev) for _ in range(100)]
        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first, "Non-determinism detected in compute_grid_state (combat_ended)"


# =============================================================================
# Adapter Determinism Canaries
# =============================================================================

@pytest.mark.immersion_fast
class TestAdapterDeterminism:
    """Canary tests for adapter stub determinism (100× iterations)."""

    def test_stub_stt_100x(self):
        """StubSTTAdapter must return identical output 100×."""
        adapter = StubSTTAdapter()
        results = [adapter.transcribe(b"audio data") for _ in range(100)]
        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first, "Non-determinism detected in StubSTTAdapter"

    def test_stub_tts_100x(self):
        """StubTTSAdapter must return identical output 100×."""
        adapter = StubTTSAdapter()
        persona = VoicePersona(persona_id="dm", name="DM")
        results = [adapter.synthesize("Hello", persona) for _ in range(100)]
        assert all(r == b"" for r in results), "Non-determinism detected in StubTTSAdapter"

    def test_stub_tts_list_personas_100x(self):
        """StubTTSAdapter.list_personas must return identical output 100×."""
        adapter = StubTTSAdapter()
        results = [adapter.list_personas() for _ in range(100)]
        first = [p.to_dict() for p in results[0]]
        for personas in results[1:]:
            assert [p.to_dict() for p in personas] == first, "Non-determinism detected in StubTTSAdapter.list_personas"

    def test_stub_image_100x(self):
        """StubImageAdapter must return identical output 100×."""
        adapter = StubImageAdapter()
        request = ImageRequest(kind="scene", semantic_key="forest:clearing:v1")
        results = [adapter.generate(request) for _ in range(100)]
        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first, "Non-determinism detected in StubImageAdapter"

    def test_stub_audio_mixer_100x(self):
        """StubAudioMixerAdapter must behave deterministically 100×."""
        adapter = StubAudioMixerAdapter()
        state = SceneAudioState(mood="combat")
        for _ in range(100):
            adapter.apply_state(state)
        assert len(adapter.history) == 100, "Non-determinism detected in StubAudioMixerAdapter history length"
        # All history entries should be identical
        first = adapter.history[0].to_dict()
        for entry in adapter.history[1:]:
            assert entry.to_dict() == first, "Non-determinism detected in StubAudioMixerAdapter history entries"


# =============================================================================
# Schema Determinism Canaries
# =============================================================================

@pytest.mark.immersion_fast
class TestSchemaDeterminism:
    """Canary tests for schema to_dict/from_dict determinism (100× iterations)."""

    def test_transcript_roundtrip_100x(self):
        """Transcript to_dict/from_dict must be identical 100×."""
        t = Transcript(text="hello", confidence=0.95, adapter_id="whisper")
        results = [Transcript.from_dict(t.to_dict()).to_dict() for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in Transcript roundtrip"

    def test_voice_persona_roundtrip_100x(self):
        """VoicePersona to_dict/from_dict must be identical 100×."""
        vp = VoicePersona(persona_id="dm", name="DM", speed=1.0, pitch=1.0)
        results = [VoicePersona.from_dict(vp.to_dict()).to_dict() for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in VoicePersona roundtrip"

    def test_audio_track_roundtrip_100x(self):
        """AudioTrack to_dict/from_dict must be identical 100×."""
        at = AudioTrack(track_id="t1", kind="combat", semantic_key="battle:theme:v1")
        results = [AudioTrack.from_dict(at.to_dict()).to_dict() for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in AudioTrack roundtrip"

    def test_scene_audio_state_roundtrip_100x(self):
        """SceneAudioState to_dict/from_dict must be identical 100×."""
        tracks = [AudioTrack(track_id="t1", kind="combat", semantic_key="battle:v1")]
        s = SceneAudioState(active_tracks=tracks, mood="combat", transition_reason="combat started")
        results = [SceneAudioState.from_dict(s.to_dict()).to_dict() for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in SceneAudioState roundtrip"

    def test_image_request_roundtrip_100x(self):
        """ImageRequest to_dict/from_dict must be identical 100×."""
        req = ImageRequest(kind="portrait", semantic_key="npc:v1", prompt_context="A wizard")
        results = [ImageRequest.from_dict(req.to_dict()).to_dict() for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in ImageRequest roundtrip"

    def test_image_result_roundtrip_100x(self):
        """ImageResult to_dict/from_dict must be identical 100×."""
        res = ImageResult(status="success", asset_id="img_001", path="/path/to/img.png")
        results = [ImageResult.from_dict(res.to_dict()).to_dict() for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in ImageResult roundtrip"

    def test_grid_entity_position_roundtrip_100x(self):
        """GridEntityPosition to_dict/from_dict must be identical 100×."""
        pos = GridEntityPosition(entity_id="e1", x=5, y=10, label="Fighter", team="PCs")
        results = [GridEntityPosition.from_dict(pos.to_dict()).to_dict() for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in GridEntityPosition roundtrip"

    def test_grid_render_state_roundtrip_100x(self):
        """GridRenderState to_dict/from_dict must be identical 100×."""
        positions = [GridEntityPosition(entity_id="e1", x=0, y=0, label="Fighter", team="PCs")]
        g = GridRenderState(visible=True, reason="combat_active", entity_positions=positions, dimensions=(10, 10))
        results = [GridRenderState.from_dict(g.to_dict()).to_dict() for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in GridRenderState roundtrip"

    def test_attribution_record_roundtrip_100x(self):
        """AttributionRecord to_dict/from_dict must be identical 100×."""
        rec = AttributionRecord(asset_id="a1", source="generator", license="MIT", author="system")
        results = [AttributionRecord.from_dict(rec.to_dict()).to_dict() for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in AttributionRecord roundtrip"

    def test_attribution_ledger_roundtrip_100x(self):
        """AttributionLedger to_dict/from_dict must be identical 100×."""
        records = [AttributionRecord(asset_id="a1", license="MIT")]
        ledger = AttributionLedger(records=records)
        results = [AttributionLedger.from_dict(ledger.to_dict()).to_dict() for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in AttributionLedger roundtrip"


# =============================================================================
# JSON Serialization Determinism Canaries
# =============================================================================

@pytest.mark.immersion_fast
class TestJSONSerializationDeterminism:
    """Canary tests for JSON serialization determinism (dict key ordering, float repr)."""

    def test_scene_audio_state_json_100x(self):
        """JSON serialization of SceneAudioState must be byte-identical 100×."""
        tracks = [AudioTrack(track_id="t1", kind="combat", semantic_key="battle:v1", volume=0.75)]
        state = SceneAudioState(active_tracks=tracks, mood="combat", transition_reason="combat started")
        results = [json.dumps(state.to_dict(), sort_keys=True) for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in SceneAudioState JSON serialization"

    def test_grid_render_state_json_100x(self):
        """JSON serialization of GridRenderState must be byte-identical 100×."""
        positions = [
            GridEntityPosition(entity_id="fighter", x=0, y=0, label="Fighter", team="PCs"),
            GridEntityPosition(entity_id="goblin", x=5, y=5, label="Goblin", team="Enemies"),
        ]
        grid = GridRenderState(visible=True, reason="combat_active", entity_positions=positions, dimensions=(10, 10))
        results = [json.dumps(grid.to_dict(), sort_keys=True) for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in GridRenderState JSON serialization"

    def test_attribution_ledger_json_100x(self):
        """JSON serialization of AttributionLedger must be byte-identical 100×."""
        records = [
            AttributionRecord(asset_id="a1", source="gen", license="MIT", author="sys"),
            AttributionRecord(asset_id="a2", source="gen", license="Apache-2.0", author="sys"),
        ]
        ledger = AttributionLedger(records=records)
        results = [json.dumps(ledger.to_dict(), sort_keys=True) for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r == first, "Non-determinism detected in AttributionLedger JSON serialization"


# =============================================================================
# Cross-Invocation Determinism Canaries
# =============================================================================

@pytest.mark.immersion_fast
class TestCrossInvocationDeterminism:
    """Canary tests for determinism across separate function invocations (no hidden state)."""

    def test_audio_state_no_hidden_state(self):
        """Multiple compute_scene_audio_state calls must not accumulate hidden state."""
        ws = WorldState(ruleset_version="RAW_3.5", active_combat={"round": 1})

        # First batch of 10 calls
        batch1 = [compute_scene_audio_state(ws) for _ in range(10)]

        # Second batch of 10 calls (should be identical to first batch)
        batch2 = [compute_scene_audio_state(ws) for _ in range(10)]

        for r1, r2 in zip(batch1, batch2):
            assert r1.to_dict() == r2.to_dict(), "Hidden state detected in compute_scene_audio_state"

    def test_grid_state_no_hidden_state(self):
        """Multiple compute_grid_state calls must not accumulate hidden state."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
            entities={"fighter": {"position": {"x": 0, "y": 0}}},
        )

        # First batch of 10 calls
        batch1 = [compute_grid_state(ws) for _ in range(10)]

        # Second batch of 10 calls (should be identical to first batch)
        batch2 = [compute_grid_state(ws) for _ in range(10)]

        for r1, r2 in zip(batch1, batch2):
            assert r1.to_dict() == r2.to_dict(), "Hidden state detected in compute_grid_state"

    def test_stub_adapters_no_hidden_state_except_history(self):
        """Stub adapters must not accumulate hidden state (except explicit history)."""
        # STT
        stt1 = StubSTTAdapter()
        stt2 = StubSTTAdapter()
        assert stt1.transcribe(b"data").to_dict() == stt2.transcribe(b"data").to_dict()

        # TTS
        tts1 = StubTTSAdapter()
        tts2 = StubTTSAdapter()
        persona = VoicePersona(persona_id="dm", name="DM")
        assert tts1.synthesize("hello", persona) == tts2.synthesize("hello", persona)

        # Image
        img1 = StubImageAdapter()
        img2 = StubImageAdapter()
        request = ImageRequest(kind="scene", semantic_key="forest:v1")
        assert img1.generate(request).to_dict() == img2.generate(request).to_dict()
