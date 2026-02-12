"""Tests for WO-VOICE-RESOLVER-001: Voice Resolver Parsing Logic.

Tests:
1. "deep gravelly voice" → matches persona with low pitch + rough timbre
2. "high-pitched nervous chatter" → matches persona with high pitch + fast pace
3. "smooth commanding tone" → matches persona with smooth timbre + authoritative style
4. Empty description → returns default persona
5. Gibberish description → returns default persona (graceful fallback)
6. Multiple matching keywords → highest-scoring persona wins
7. VoiceRoster caching: same description returns same persona on repeated calls
"""

import pytest

from aidm.schemas.immersion import VoicePersona
from aidm.lens.voice_resolver import (
    VoiceRoster,
    resolve_voice,
    resolve_voice_from_roster,
    _extract_attributes_from_freetext,
    _parse_voice_description,
    _score_persona,
    PITCH_MAP,
    PACE_MAP,
    INTENSITY_MAP,
    TIMBRE_REFERENCE_HINTS,
)


# =============================================================================
# Test personas — simulate a TTS adapter's list_personas() output
# =============================================================================

_TEST_PERSONAS = [
    VoicePersona(
        persona_id="dm_narrator",
        name="Dungeon Master",
        voice_model="af_bella",
        speed=1.0,
        pitch=1.0,
        exaggeration=0.5,
    ),
    VoicePersona(
        persona_id="npc_male",
        name="NPC Male",
        voice_model="am_michael",
        speed=1.0,
        pitch=1.0,
        exaggeration=0.5,
    ),
    VoicePersona(
        persona_id="npc_elderly",
        name="NPC Elderly",
        voice_model="bm_george",
        speed=0.9,
        pitch=0.95,
        exaggeration=0.5,
    ),
    VoicePersona(
        persona_id="npc_young",
        name="NPC Young",
        voice_model="af_sky",
        speed=1.05,
        pitch=1.05,
        exaggeration=0.5,
    ),
    VoicePersona(
        persona_id="villainous",
        name="Villain",
        voice_model="bm_lewis",
        speed=0.95,
        pitch=0.9,
        exaggeration=0.5,
    ),
    VoicePersona(
        persona_id="heroic",
        name="Hero",
        voice_model="am_adam",
        speed=1.0,
        pitch=1.0,
        exaggeration=0.5,
    ),
]


# =============================================================================
# Free-text keyword extraction tests
# =============================================================================

@pytest.mark.immersion_fast
class TestFreeTextExtraction:
    """Tests for _extract_attributes_from_freetext()."""

    def test_deep_gravelly_extracts_pitch_and_timbre(self):
        """'deep gravelly voice' should extract low pitch + gravelly timbre."""
        attrs = _extract_attributes_from_freetext("deep gravelly voice")
        assert attrs.get("pitch") == "low"
        assert attrs.get("timbre") == "gravelly"

    def test_high_pitched_nervous_chatter(self):
        """'high-pitched nervous chatter' should extract high pitch + quick pace."""
        attrs = _extract_attributes_from_freetext("high-pitched nervous chatter")
        assert attrs.get("pitch") == "high"
        # "nervous" maps to pace=quick via FREETEXT_PACE_KEYWORDS
        assert attrs.get("pace") == "quick"

    def test_smooth_commanding_tone(self):
        """'smooth commanding tone' should extract smooth timbre + style."""
        attrs = _extract_attributes_from_freetext("smooth commanding tone")
        assert attrs.get("timbre") == "smooth"
        # "commanding" maps to emotional_baseline
        assert "emotional_baseline" in attrs

    def test_empty_description_returns_empty(self):
        """Empty description should return no attributes."""
        attrs = _extract_attributes_from_freetext("")
        assert attrs == {}

    def test_gibberish_returns_empty(self):
        """Gibberish should return no attributes."""
        attrs = _extract_attributes_from_freetext("xyzzy plugh zork")
        assert attrs == {}

    def test_multiple_keywords_all_extracted(self):
        """Multiple keywords across categories should all be captured."""
        attrs = _extract_attributes_from_freetext(
            "a deep slow gravelly booming elderly voice"
        )
        assert attrs.get("pitch") == "low"
        assert attrs.get("pace") == "slow"
        assert attrs.get("timbre") == "gravelly"
        assert attrs.get("intensity") == "booming"
        assert attrs.get("age_quality") == "elderly"


# =============================================================================
# Persona scoring and matching tests
# =============================================================================

@pytest.mark.immersion_fast
class TestResolveVoiceFromRoster:
    """Tests for resolve_voice_from_roster() — the core WO deliverable."""

    def test_deep_gravelly_matches_low_pitch_persona(self):
        """'deep gravelly voice' → persona with low pitch (villain or elderly)."""
        persona = resolve_voice_from_roster(
            "a deep gravelly voice",
            _TEST_PERSONAS,
        )
        # Should match a persona with low pitch — villainous (0.9) or elderly (0.95)
        assert persona.pitch <= 1.0
        assert persona.persona_id in ("villainous", "npc_elderly")

    def test_high_pitched_nervous_matches_high_pitch_fast(self):
        """'high-pitched nervous chatter' → persona with high pitch + fast pace."""
        persona = resolve_voice_from_roster(
            "high-pitched nervous chatter",
            _TEST_PERSONAS,
        )
        # Should match npc_young (pitch=1.05, speed=1.05) — closest to high+quick
        assert persona.persona_id == "npc_young"

    def test_smooth_commanding_tone(self):
        """'smooth commanding tone' → persona that fits authoritative style."""
        persona = resolve_voice_from_roster(
            "smooth commanding tone",
            _TEST_PERSONAS,
        )
        # Should match a moderate-pitch persona; commanding → dramatic exaggeration
        # dm_narrator, heroic, or npc_male are reasonable
        assert persona.persona_id in ("dm_narrator", "heroic", "npc_male")

    def test_empty_description_returns_default(self):
        """Empty description → first available persona (default fallback)."""
        persona = resolve_voice_from_roster("", _TEST_PERSONAS)
        assert persona.persona_id == _TEST_PERSONAS[0].persona_id

    def test_none_like_empty(self):
        """None-ish whitespace description → default."""
        persona = resolve_voice_from_roster("   ", _TEST_PERSONAS)
        assert persona.persona_id == _TEST_PERSONAS[0].persona_id

    def test_gibberish_returns_default(self):
        """Gibberish description → default persona (graceful fallback)."""
        persona = resolve_voice_from_roster(
            "xyzzy plugh zork blargh",
            _TEST_PERSONAS,
        )
        assert persona.persona_id == _TEST_PERSONAS[0].persona_id

    def test_multiple_keywords_highest_score_wins(self):
        """Multiple matching keywords → best-scoring persona wins."""
        # "deep slow elderly menacing" should strongly favor villainous or elderly
        persona = resolve_voice_from_roster(
            "deep slow elderly menacing rumble",
            _TEST_PERSONAS,
        )
        assert persona.persona_id in ("villainous", "npc_elderly")

    def test_empty_roster_returns_fallback(self):
        """Empty persona list → returns a default VoicePersona."""
        persona = resolve_voice_from_roster("deep voice", [])
        assert persona.persona_id == "default"
        assert persona.speed == 1.0
        assert persona.pitch == 1.0


# =============================================================================
# VoiceRoster caching tests
# =============================================================================

@pytest.mark.immersion_fast
class TestVoiceRosterCaching:
    """Tests for VoiceRoster caching with persona matching."""

    def test_same_description_returns_cached_persona(self):
        """Same character_id returns the cached persona on repeated calls."""
        roster = VoiceRoster()
        desc = "a deep gravelly voice with a slow deliberate pace"

        p1 = roster.get_or_resolve(
            character_id="theron",
            character_name="Theron",
            voice_description=desc,
            available_personas=_TEST_PERSONAS,
        )
        p2 = roster.get_or_resolve(
            character_id="theron",
            character_name="Theron",
            voice_description=desc,
            available_personas=_TEST_PERSONAS,
        )
        assert p1 is p2  # Same object (cached), not just equal

    def test_different_characters_get_different_personas(self):
        """Different character IDs can have different personas."""
        roster = VoiceRoster()

        p1 = roster.get_or_resolve(
            character_id="villain_npc",
            character_name="Dark Lord",
            voice_description="deep menacing booming voice",
            available_personas=_TEST_PERSONAS,
        )
        p2 = roster.get_or_resolve(
            character_id="child_npc",
            character_name="Pip",
            voice_description="high-pitched nervous chatter",
            available_personas=_TEST_PERSONAS,
        )
        # They should resolve to different personas
        assert p1.persona_id != p2.persona_id

    def test_cache_ignores_new_description_for_same_id(self):
        """Once cached, changing the description doesn't re-resolve."""
        roster = VoiceRoster()

        p1 = roster.get_or_resolve(
            character_id="npc_1",
            character_name="Bob",
            voice_description="deep gravelly voice",
            available_personas=_TEST_PERSONAS,
        )
        p2 = roster.get_or_resolve(
            character_id="npc_1",
            character_name="Bob",
            voice_description="high-pitched squeaky voice",
            available_personas=_TEST_PERSONAS,
        )
        assert p1 is p2  # Cache takes precedence

    def test_roster_count(self):
        """Roster count reflects unique characters."""
        roster = VoiceRoster()
        assert roster.count() == 0

        roster.get_or_resolve(
            character_id="a",
            character_name="A",
            voice_description="deep voice",
            available_personas=_TEST_PERSONAS,
        )
        assert roster.count() == 1

        roster.get_or_resolve(
            character_id="b",
            character_name="B",
            voice_description="high voice",
            available_personas=_TEST_PERSONAS,
        )
        assert roster.count() == 2

    def test_roster_clear(self):
        """Clear resets the cache."""
        roster = VoiceRoster()
        roster.get_or_resolve(
            character_id="npc",
            character_name="NPC",
            voice_description="deep voice",
            available_personas=_TEST_PERSONAS,
        )
        assert roster.count() == 1
        roster.clear()
        assert roster.count() == 0


# =============================================================================
# Existing structured parsing still works
# =============================================================================

@pytest.mark.immersion_fast
class TestStructuredParsing:
    """Ensure the existing structured key:value parsing is preserved."""

    def test_structured_description_parsed(self):
        """Structured voice description is parsed into field dict."""
        desc = (
            "pitch: low\n"
            "timbre: gravelly\n"
            "pace: measured\n"
            "intensity: booming\n"
            "age_quality: elderly\n"
        )
        fields = _parse_voice_description(desc)
        assert fields["pitch"] == "low"
        assert fields["timbre"] == "gravelly"
        assert fields["pace"] == "measured"
        assert fields["intensity"] == "booming"
        assert fields["age_quality"] == "elderly"

    def test_resolve_voice_with_structured_description(self):
        """resolve_voice() with structured input produces correct numeric values."""
        desc = (
            "pitch: low\n"
            "timbre: smooth\n"
            "pace: slow\n"
            "intensity: dramatic\n"
            "age_quality: mature\n"
        )
        persona = resolve_voice("TestNPC", voice_description=desc)
        assert persona.pitch == pytest.approx(0.7)  # PITCH_MAP["low"]
        assert persona.speed == pytest.approx(0.8)  # PACE_MAP["slow"]
        assert persona.exaggeration == pytest.approx(0.7)  # INTENSITY_MAP["dramatic"]

    def test_resolve_voice_no_description_returns_default(self):
        """resolve_voice() without description returns default persona."""
        persona = resolve_voice("Unnamed")
        assert persona.pitch == 1.0
        assert persona.speed == 1.0
        assert persona.exaggeration == 0.5
        assert persona.voice_model == "default"

    def test_structured_via_roster_matching(self):
        """Structured format also works through resolve_voice_from_roster."""
        desc = (
            "pitch: low\n"
            "timbre: gravelly\n"
            "pace: slow\n"
            "intensity: booming\n"
        )
        persona = resolve_voice_from_roster(desc, _TEST_PERSONAS)
        # Should prefer low-pitch personas
        assert persona.pitch <= 1.0
