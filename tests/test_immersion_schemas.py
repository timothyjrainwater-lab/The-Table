"""Tests for M3 Immersion Schemas.

Tests:
- to_dict/from_dict roundtrip for all 10 schemas
- validate() catches invalid values (fail-closed)
- Default values are correct
- Nested schema validation (SceneAudioState, GridRenderState, AttributionLedger)
"""

import pytest

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
# Transcript Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestTranscript:
    """Tests for Transcript schema."""

    def test_defaults(self):
        t = Transcript()
        assert t.text == ""
        assert t.confidence == 1.0
        assert t.adapter_id == "stub"

    def test_roundtrip(self):
        t = Transcript(text="I attack the goblin", confidence=0.95, adapter_id="whisper")
        data = t.to_dict()
        t2 = Transcript.from_dict(data)
        assert t2.text == "I attack the goblin"
        assert t2.confidence == 0.95
        assert t2.adapter_id == "whisper"

    def test_validate_valid(self):
        t = Transcript(text="hello", confidence=0.8, adapter_id="stub")
        assert t.validate() == []

    def test_validate_confidence_out_of_range(self):
        t = Transcript(confidence=1.5)
        errors = t.validate()
        assert any("confidence" in e for e in errors)

    def test_validate_confidence_negative(self):
        t = Transcript(confidence=-0.1)
        errors = t.validate()
        assert any("confidence" in e for e in errors)

    def test_validate_empty_adapter_id(self):
        t = Transcript(adapter_id="")
        errors = t.validate()
        assert any("adapter_id" in e for e in errors)


# =============================================================================
# VoicePersona Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestVoicePersona:
    """Tests for VoicePersona schema."""

    def test_defaults(self):
        vp = VoicePersona()
        assert vp.persona_id == ""
        assert vp.voice_model == "default"
        assert vp.speed == 1.0
        assert vp.pitch == 1.0

    def test_roundtrip(self):
        vp = VoicePersona(
            persona_id="dm_001",
            name="Dungeon Master",
            voice_model="en_us_male_deep",
            speed=0.9,
            pitch=0.8,
        )
        data = vp.to_dict()
        vp2 = VoicePersona.from_dict(data)
        assert vp2.persona_id == "dm_001"
        assert vp2.name == "Dungeon Master"
        assert vp2.voice_model == "en_us_male_deep"
        assert vp2.speed == 0.9
        assert vp2.pitch == 0.8

    def test_validate_valid(self):
        vp = VoicePersona(persona_id="dm", name="DM", speed=1.0, pitch=1.0)
        assert vp.validate() == []

    def test_validate_empty_persona_id(self):
        vp = VoicePersona(name="DM")
        errors = vp.validate()
        assert any("persona_id" in e for e in errors)

    def test_validate_empty_name(self):
        vp = VoicePersona(persona_id="dm")
        errors = vp.validate()
        assert any("name" in e for e in errors)

    def test_validate_speed_out_of_range(self):
        vp = VoicePersona(persona_id="dm", name="DM", speed=3.0)
        errors = vp.validate()
        assert any("speed" in e for e in errors)

    def test_validate_pitch_out_of_range(self):
        vp = VoicePersona(persona_id="dm", name="DM", pitch=0.1)
        errors = vp.validate()
        assert any("pitch" in e for e in errors)


# =============================================================================
# AudioTrack Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestAudioTrack:
    """Tests for AudioTrack schema."""

    def test_defaults(self):
        at = AudioTrack()
        assert at.kind == "ambient"
        assert at.volume == 1.0
        assert at.loop is False

    def test_roundtrip(self):
        at = AudioTrack(
            track_id="tavern_fire",
            kind="ambient",
            semantic_key="tavern:fireplace:loop",
            volume=0.6,
            loop=True,
        )
        data = at.to_dict()
        at2 = AudioTrack.from_dict(data)
        assert at2.track_id == "tavern_fire"
        assert at2.kind == "ambient"
        assert at2.semantic_key == "tavern:fireplace:loop"
        assert at2.volume == 0.6
        assert at2.loop is True

    def test_validate_valid(self):
        at = AudioTrack(track_id="t1", kind="combat", semantic_key="battle:theme:v1")
        assert at.validate() == []

    def test_validate_invalid_kind(self):
        at = AudioTrack(track_id="t1", kind="invalid", semantic_key="k")
        errors = at.validate()
        assert any("kind" in e for e in errors)

    def test_validate_all_valid_kinds(self):
        for kind in ("ambient", "combat", "sfx", "music"):
            at = AudioTrack(track_id="t", kind=kind, semantic_key="k")
            assert at.validate() == []

    def test_validate_volume_out_of_range(self):
        at = AudioTrack(track_id="t", kind="ambient", semantic_key="k", volume=1.5)
        errors = at.validate()
        assert any("volume" in e for e in errors)

    def test_validate_empty_track_id(self):
        at = AudioTrack(kind="ambient", semantic_key="k")
        errors = at.validate()
        assert any("track_id" in e for e in errors)

    def test_validate_empty_semantic_key(self):
        at = AudioTrack(track_id="t", kind="ambient")
        errors = at.validate()
        assert any("semantic_key" in e for e in errors)


# =============================================================================
# SceneAudioState Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestSceneAudioState:
    """Tests for SceneAudioState schema."""

    def test_defaults(self):
        s = SceneAudioState()
        assert s.mood == "neutral"
        assert s.active_tracks == []
        assert s.transition_reason == ""

    def test_roundtrip(self):
        tracks = [
            AudioTrack(track_id="t1", kind="ambient", semantic_key="forest:wind"),
            AudioTrack(track_id="t2", kind="music", semantic_key="peaceful:theme"),
        ]
        s = SceneAudioState(
            active_tracks=tracks,
            mood="peaceful",
            transition_reason="combat ended",
        )
        data = s.to_dict()
        s2 = SceneAudioState.from_dict(data)
        assert s2.mood == "peaceful"
        assert s2.transition_reason == "combat ended"
        assert len(s2.active_tracks) == 2
        assert s2.active_tracks[0].track_id == "t1"

    def test_validate_valid(self):
        s = SceneAudioState(mood="combat")
        assert s.validate() == []

    def test_validate_invalid_mood(self):
        s = SceneAudioState(mood="scary")
        errors = s.validate()
        assert any("mood" in e for e in errors)

    def test_validate_all_valid_moods(self):
        for mood in ("neutral", "tense", "combat", "peaceful", "dramatic"):
            s = SceneAudioState(mood=mood)
            assert s.validate() == []

    def test_validate_nested_track_errors(self):
        bad_track = AudioTrack(kind="invalid")
        s = SceneAudioState(active_tracks=[bad_track])
        errors = s.validate()
        assert any("active_tracks[0]" in e for e in errors)


# =============================================================================
# ImageRequest Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestImageRequest:
    """Tests for ImageRequest schema."""

    def test_defaults(self):
        r = ImageRequest()
        assert r.kind == "scene"
        assert r.dimensions == (512, 512)

    def test_roundtrip(self):
        r = ImageRequest(
            kind="portrait",
            semantic_key="npc:theron:v1",
            prompt_context="A grizzled dwarven blacksmith",
            dimensions=(256, 256),
        )
        data = r.to_dict()
        r2 = ImageRequest.from_dict(data)
        assert r2.kind == "portrait"
        assert r2.semantic_key == "npc:theron:v1"
        assert r2.prompt_context == "A grizzled dwarven blacksmith"
        assert r2.dimensions == (256, 256)

    def test_validate_valid(self):
        r = ImageRequest(kind="scene", semantic_key="forest:clearing:v1")
        assert r.validate() == []

    def test_validate_invalid_kind(self):
        r = ImageRequest(kind="thumbnail", semantic_key="k")
        errors = r.validate()
        assert any("kind" in e for e in errors)

    def test_validate_all_valid_kinds(self):
        for kind in ("portrait", "scene", "backdrop"):
            r = ImageRequest(kind=kind, semantic_key="k")
            assert r.validate() == []

    def test_validate_empty_semantic_key(self):
        r = ImageRequest(kind="scene")
        errors = r.validate()
        assert any("semantic_key" in e for e in errors)

    def test_validate_negative_dimensions(self):
        r = ImageRequest(kind="scene", semantic_key="k", dimensions=(-1, 512))
        errors = r.validate()
        assert any("dimensions" in e for e in errors)

    def test_dimensions_serialized_as_list(self):
        r = ImageRequest(dimensions=(800, 600))
        data = r.to_dict()
        assert data["dimensions"] == [800, 600]

    def test_dimensions_from_list(self):
        r = ImageRequest.from_dict({"dimensions": [1024, 768]})
        assert r.dimensions == (1024, 768)


# =============================================================================
# ImageResult Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestImageResult:
    """Tests for ImageResult schema."""

    def test_defaults(self):
        r = ImageResult()
        assert r.status == "placeholder"
        assert r.asset_id == ""
        assert r.content_hash == ""

    def test_roundtrip(self):
        r = ImageResult(
            status="generated",
            asset_id="img_001",
            path="assets/img_001.png",
            content_hash="abc123",
        )
        data = r.to_dict()
        r2 = ImageResult.from_dict(data)
        assert r2.status == "generated"
        assert r2.asset_id == "img_001"
        assert r2.path == "assets/img_001.png"
        assert r2.content_hash == "abc123"

    def test_validate_valid(self):
        r = ImageResult(status="placeholder")
        assert r.validate() == []

    def test_validate_invalid_status(self):
        r = ImageResult(status="pending")
        errors = r.validate()
        assert any("status" in e for e in errors)

    def test_validate_all_valid_statuses(self):
        for status in ("placeholder", "generated", "cached", "error"):
            r = ImageResult(status=status)
            assert r.validate() == []

    def test_error_result(self):
        r = ImageResult(status="error", error_message="Backend unavailable")
        data = r.to_dict()
        r2 = ImageResult.from_dict(data)
        assert r2.status == "error"
        assert r2.error_message == "Backend unavailable"


# =============================================================================
# GridEntityPosition Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestGridEntityPosition:
    """Tests for GridEntityPosition schema."""

    def test_defaults(self):
        p = GridEntityPosition()
        assert p.x == 0
        assert p.y == 0
        assert p.team == ""

    def test_roundtrip(self):
        p = GridEntityPosition(
            entity_id="goblin_1",
            x=5,
            y=3,
            label="Goblin",
            team="hostile",
        )
        data = p.to_dict()
        p2 = GridEntityPosition.from_dict(data)
        assert p2.entity_id == "goblin_1"
        assert p2.x == 5
        assert p2.y == 3
        assert p2.label == "Goblin"
        assert p2.team == "hostile"

    def test_validate_valid(self):
        p = GridEntityPosition(entity_id="e1")
        assert p.validate() == []

    def test_validate_empty_entity_id(self):
        p = GridEntityPosition()
        errors = p.validate()
        assert any("entity_id" in e for e in errors)


# =============================================================================
# GridRenderState Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestGridRenderState:
    """Tests for GridRenderState schema."""

    def test_defaults(self):
        g = GridRenderState()
        assert g.visible is False
        assert g.reason == "no_combat"
        assert g.entity_positions == []
        assert g.dimensions == (0, 0)

    def test_roundtrip(self):
        positions = [
            GridEntityPosition(entity_id="fighter_1", x=2, y=3, label="Fighter", team="party"),
            GridEntityPosition(entity_id="goblin_1", x=5, y=3, label="Goblin", team="hostile"),
        ]
        g = GridRenderState(
            visible=True,
            reason="combat_active",
            entity_positions=positions,
            dimensions=(10, 8),
        )
        data = g.to_dict()
        g2 = GridRenderState.from_dict(data)
        assert g2.visible is True
        assert g2.reason == "combat_active"
        assert len(g2.entity_positions) == 2
        assert g2.entity_positions[0].entity_id == "fighter_1"
        assert g2.dimensions == (10, 8)

    def test_validate_valid(self):
        g = GridRenderState(reason="combat_active")
        assert g.validate() == []

    def test_validate_invalid_reason(self):
        g = GridRenderState(reason="exploring")
        errors = g.validate()
        assert any("reason" in e for e in errors)

    def test_validate_all_valid_reasons(self):
        for reason in ("combat_active", "combat_ended", "no_combat"):
            g = GridRenderState(reason=reason)
            assert g.validate() == []

    def test_validate_nested_position_errors(self):
        bad_pos = GridEntityPosition()  # empty entity_id
        g = GridRenderState(entity_positions=[bad_pos])
        errors = g.validate()
        assert any("entity_positions[0]" in e for e in errors)

    def test_dimensions_serialized_as_list(self):
        g = GridRenderState(dimensions=(15, 20))
        data = g.to_dict()
        assert data["dimensions"] == [15, 20]


# =============================================================================
# AttributionRecord Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestAttributionRecord:
    """Tests for AttributionRecord schema."""

    def test_defaults(self):
        r = AttributionRecord()
        assert r.asset_id == ""
        assert r.source == ""
        assert r.license == ""
        assert r.author == ""

    def test_roundtrip(self):
        r = AttributionRecord(
            asset_id="scene_001",
            source="stub_generator",
            license="generated",
            author="aidm_system",
        )
        data = r.to_dict()
        r2 = AttributionRecord.from_dict(data)
        assert r2.asset_id == "scene_001"
        assert r2.source == "stub_generator"
        assert r2.license == "generated"
        assert r2.author == "aidm_system"

    def test_validate_valid(self):
        r = AttributionRecord(asset_id="a1", license="CC-BY-4.0")
        assert r.validate() == []

    def test_validate_empty_asset_id(self):
        r = AttributionRecord(license="MIT")
        errors = r.validate()
        assert any("asset_id" in e for e in errors)

    def test_validate_empty_license(self):
        r = AttributionRecord(asset_id="a1")
        errors = r.validate()
        assert any("license" in e for e in errors)


# =============================================================================
# AttributionLedger Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestAttributionLedger:
    """Tests for AttributionLedger schema."""

    def test_defaults(self):
        ledger = AttributionLedger()
        assert ledger.schema_version == "1.0"
        assert ledger.records == []

    def test_roundtrip(self):
        records = [
            AttributionRecord(asset_id="a1", source="gen", license="generated", author="sys"),
            AttributionRecord(asset_id="a2", source="cache", license="CC-BY-4.0", author="artist"),
        ]
        ledger = AttributionLedger(schema_version="1.0", records=records)
        data = ledger.to_dict()
        ledger2 = AttributionLedger.from_dict(data)
        assert ledger2.schema_version == "1.0"
        assert len(ledger2.records) == 2
        assert ledger2.records[0].asset_id == "a1"
        assert ledger2.records[1].license == "CC-BY-4.0"

    def test_validate_valid(self):
        ledger = AttributionLedger(records=[
            AttributionRecord(asset_id="a1", license="MIT"),
        ])
        assert ledger.validate() == []

    def test_validate_empty_schema_version(self):
        ledger = AttributionLedger(schema_version="")
        errors = ledger.validate()
        assert any("schema_version" in e for e in errors)

    def test_validate_nested_record_errors(self):
        bad_record = AttributionRecord()  # empty asset_id and license
        ledger = AttributionLedger(records=[bad_record])
        errors = ledger.validate()
        assert any("records[0]" in e for e in errors)

    def test_validate_empty_ledger_valid(self):
        ledger = AttributionLedger()
        assert ledger.validate() == []
