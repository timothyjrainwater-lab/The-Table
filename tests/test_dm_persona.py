"""Tests for WO-041: DM Personality Layer

Verifies:
- ToneConfig validation and parameter ranges
- System prompt construction with tone modifiers
- NPC voice mapping and fallback behavior
- NPC characterization tracking
- Session context integration
- No mechanical data leaks into prompts
- Provenance tagging [NARRATIVE]
- Preset DM persona factories
"""

import pytest

from aidm.spark.dm_persona import (
    DMPersona,
    ToneConfig,
    create_default_dm,
    create_gritty_dm,
    create_theatrical_dm,
    create_humorous_dm,
    create_terse_dm,
)
from aidm.lens.narrative_brief import NarrativeBrief


# ══════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_brief():
    """Sample NarrativeBrief for testing."""
    return NarrativeBrief(
        action_type="attack_hit",
        actor_name="Aldric",
        target_name="Goblin",
        outcome_summary="Aldric hits Goblin with longsword",
        severity="moderate",
        weapon_name="longsword",
        damage_type="slashing",
    )


@pytest.fixture
def sample_brief_with_npc():
    """Sample NarrativeBrief with known NPC."""
    return NarrativeBrief(
        action_type="spell_damage",
        actor_name="Malakar the Dark",
        target_name="Aldric",
        outcome_summary="Malakar casts fireball on Aldric",
        severity="devastating",
        scene_description="A dimly lit throne room",
    )


@pytest.fixture
def sample_session_context():
    """Sample session context from ContextAssembler."""
    return (
        "Recent Events:\n"
        "- The goblin chieftain roars in anger!\n"
        "- Aldric readies his blade.\n"
        "- The party advances cautiously."
    )


# ══════════════════════════════════════════════════════════════════════════
# ToneConfig Validation Tests
# ══════════════════════════════════════════════════════════════════════════


def test_tone_config_defaults():
    """ToneConfig has correct default values."""
    tone = ToneConfig()
    assert tone.gravity == 0.7
    assert tone.verbosity == 0.5
    assert tone.drama == 0.6


def test_tone_config_custom():
    """ToneConfig accepts custom values."""
    tone = ToneConfig(gravity=0.9, verbosity=0.2, drama=0.8)
    assert tone.gravity == 0.9
    assert tone.verbosity == 0.2
    assert tone.drama == 0.8


def test_tone_config_gravity_out_of_range():
    """ToneConfig rejects gravity outside [0.0, 1.0]."""
    with pytest.raises(ValueError, match="gravity must be in"):
        ToneConfig(gravity=1.5)

    with pytest.raises(ValueError, match="gravity must be in"):
        ToneConfig(gravity=-0.1)


def test_tone_config_verbosity_out_of_range():
    """ToneConfig rejects verbosity outside [0.0, 1.0]."""
    with pytest.raises(ValueError, match="verbosity must be in"):
        ToneConfig(verbosity=2.0)


def test_tone_config_drama_out_of_range():
    """ToneConfig rejects drama outside [0.0, 1.0]."""
    with pytest.raises(ValueError, match="drama must be in"):
        ToneConfig(drama=-0.5)


def test_tone_config_frozen():
    """ToneConfig is immutable."""
    tone = ToneConfig()
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        tone.gravity = 0.9


# ══════════════════════════════════════════════════════════════════════════
# System Prompt Construction Tests
# ══════════════════════════════════════════════════════════════════════════


def test_build_system_prompt_basic(sample_brief):
    """System prompt includes base DM persona and action context."""
    persona = DMPersona()
    prompt = persona.build_system_prompt(sample_brief)

    # Base persona
    assert "Dungeon Master" in prompt
    assert "D&D 3.5e" in prompt

    # Action context
    assert "attack_hit" in prompt
    assert "Aldric hits Goblin with longsword" in prompt
    assert "moderate" in prompt
    assert "longsword" in prompt
    assert "slashing" in prompt


def test_build_system_prompt_with_session_context(sample_brief, sample_session_context):
    """System prompt includes session context."""
    persona = DMPersona()
    prompt = persona.build_system_prompt(
        sample_brief,
        session_context=sample_session_context,
    )

    assert "RECENT EVENTS:" in prompt
    assert "The goblin chieftain roars in anger!" in prompt
    assert "Aldric readies his blade." in prompt


def test_build_system_prompt_with_scene(sample_brief):
    """System prompt includes scene description."""
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Fighter",
        target_name="Troll",
        outcome_summary="Fighter strikes Troll",
        severity="severe",
        scene_description="A dark cavern",
    )

    persona = DMPersona()
    prompt = persona.build_system_prompt(brief)

    assert "LOCATION: A dark cavern" in prompt


def test_build_system_prompt_target_defeated(sample_brief):
    """System prompt indicates target defeated."""
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Aldric",
        target_name="Goblin",
        outcome_summary="Aldric defeats Goblin",
        severity="lethal",
        target_defeated=True,
    )

    persona = DMPersona()
    prompt = persona.build_system_prompt(brief)

    assert "RESULT: Target defeated" in prompt


def test_build_system_prompt_condition_applied(sample_brief):
    """System prompt includes condition applied."""
    brief = NarrativeBrief(
        action_type="trip_success",
        actor_name="Monk",
        target_name="Ogre",
        outcome_summary="Monk trips Ogre",
        condition_applied="prone",
    )

    persona = DMPersona()
    prompt = persona.build_system_prompt(brief)

    assert "CONDITION: prone" in prompt


# ══════════════════════════════════════════════════════════════════════════
# Tone Modifier Tests
# ══════════════════════════════════════════════════════════════════════════


def test_tone_serious(sample_brief):
    """High gravity produces serious tone modifiers."""
    tone = ToneConfig(gravity=0.9)
    persona = DMPersona(tone=tone)
    prompt = persona.build_system_prompt(sample_brief)

    assert "serious" in prompt.lower() or "weighty" in prompt.lower()


def test_tone_humorous(sample_brief):
    """Low gravity produces humorous tone modifiers."""
    tone = ToneConfig(gravity=0.2)
    persona = DMPersona(tone=tone)
    prompt = persona.build_system_prompt(sample_brief)

    assert "humorous" in prompt.lower() or "wit" in prompt.lower()


def test_tone_verbose(sample_brief):
    """High verbosity produces verbose style guidance."""
    tone = ToneConfig(verbosity=0.9)
    persona = DMPersona(tone=tone)
    prompt = persona.build_system_prompt(sample_brief)

    assert "rich" in prompt.lower() or "descriptive" in prompt.lower()


def test_tone_terse(sample_brief):
    """Low verbosity produces terse style guidance."""
    tone = ToneConfig(verbosity=0.2)
    persona = DMPersona(tone=tone)
    prompt = persona.build_system_prompt(sample_brief)

    assert "concise" in prompt.lower() or "punchy" in prompt.lower()


def test_tone_dramatic(sample_brief):
    """High drama produces theatrical style guidance."""
    tone = ToneConfig(drama=0.9)
    persona = DMPersona(tone=tone)
    prompt = persona.build_system_prompt(sample_brief)

    assert "dramatic" in prompt.lower() or "cinematic" in prompt.lower()


def test_tone_understated(sample_brief):
    """Low drama produces understated style guidance."""
    tone = ToneConfig(drama=0.2)
    persona = DMPersona(tone=tone)
    prompt = persona.build_system_prompt(sample_brief)

    assert "understated" in prompt.lower() or "matter-of-fact" in prompt.lower()


# ══════════════════════════════════════════════════════════════════════════
# NPC Voice Mapping Tests
# ══════════════════════════════════════════════════════════════════════════


def test_get_npc_voice_default():
    """Unknown NPC falls back to default voice."""
    persona = DMPersona()
    voice = persona.get_npc_voice("Unknown NPC")

    assert voice == persona.default_voice
    assert voice == "en_us_male_narrator"


def test_get_npc_voice_registered():
    """Registered NPC returns correct voice ID."""
    persona = DMPersona()
    persona.register_npc("Malakar", "en_us_male_villain")

    voice = persona.get_npc_voice("Malakar")
    assert voice == "en_us_male_villain"


def test_register_npc_with_personality():
    """register_npc tracks personality traits."""
    persona = DMPersona()
    persona.register_npc(
        "Malakar",
        "en_us_male_villain",
        personality_traits=["arrogant", "cunning", "theatrical"],
    )

    assert "Malakar" in persona.npc_voices
    assert "Malakar" in persona.npc_characterization
    assert "arrogant" in persona.npc_characterization["Malakar"]


def test_npc_characterization_in_prompt(sample_brief_with_npc):
    """NPC characterization appears in system prompt."""
    persona = DMPersona()
    persona.register_npc(
        "Malakar the Dark",
        "en_us_male_villain",
        personality_traits=["arrogant", "power-hungry"],
    )

    prompt = persona.build_system_prompt(sample_brief_with_npc)

    assert "NPC CHARACTERIZATION:" in prompt
    assert "Malakar the Dark" in prompt
    assert "arrogant" in prompt
    assert "power-hungry" in prompt


def test_multiple_npc_characterization():
    """Multiple NPCs tracked separately."""
    persona = DMPersona()

    persona.register_npc("Malakar", "en_us_male_villain", ["arrogant"])
    persona.register_npc("Elara", "en_us_female_scholar", ["cautious"])

    assert persona.get_npc_voice("Malakar") == "en_us_male_villain"
    assert persona.get_npc_voice("Elara") == "en_us_female_scholar"
    assert persona.npc_characterization["Malakar"] == ["arrogant"]
    assert persona.npc_characterization["Elara"] == ["cautious"]


# ══════════════════════════════════════════════════════════════════════════
# Containment Boundary Tests
# ══════════════════════════════════════════════════════════════════════════


def test_no_entity_ids_in_prompt(sample_brief):
    """System prompt contains no entity IDs."""
    persona = DMPersona()
    prompt = persona.build_system_prompt(sample_brief)

    # No internal IDs like "fighter_1" or "goblin_1"
    assert "fighter_1" not in prompt
    assert "goblin_1" not in prompt
    assert "entity_id" not in prompt.lower()


def test_no_raw_hp_in_prompt(sample_brief):
    """System prompt contains no raw HP values."""
    persona = DMPersona()
    prompt = persona.build_system_prompt(sample_brief)

    # No HP values
    assert "hp" not in prompt.lower() or "hp:" not in prompt.lower()
    assert "hit points" not in prompt.lower()

    # Severity category is OK (already abstracted)
    assert "moderate" in prompt  # This is allowed


def test_no_mechanical_details_in_prompt(sample_brief):
    """System prompt explicitly forbids mechanical details in output."""
    persona = DMPersona()
    prompt = persona.build_system_prompt(sample_brief)

    # Prompt should instruct Spark NOT to reveal mechanics
    assert "Do NOT reveal mechanical details" in prompt or "without revealing" in prompt.lower()


# ══════════════════════════════════════════════════════════════════════════
# Preset DM Persona Tests
# ══════════════════════════════════════════════════════════════════════════


def test_create_default_dm():
    """create_default_dm produces balanced tone."""
    persona = create_default_dm()

    assert persona.tone.gravity == 0.7
    assert persona.tone.verbosity == 0.5
    assert persona.tone.drama == 0.6


def test_create_gritty_dm():
    """create_gritty_dm produces serious, understated tone."""
    persona = create_gritty_dm()

    assert persona.tone.gravity == 0.9  # Serious
    assert persona.tone.drama == 0.3    # Understated


def test_create_theatrical_dm():
    """create_theatrical_dm produces dramatic, verbose tone."""
    persona = create_theatrical_dm()

    assert persona.tone.drama == 0.9      # Theatrical
    assert persona.tone.verbosity == 0.8  # Verbose


def test_create_humorous_dm():
    """create_humorous_dm produces light-hearted tone."""
    persona = create_humorous_dm()

    assert persona.tone.gravity == 0.2  # Humorous


def test_create_terse_dm():
    """create_terse_dm produces concise, efficient tone."""
    persona = create_terse_dm()

    assert persona.tone.verbosity == 0.2  # Terse
    assert persona.tone.drama == 0.3      # Understated


# ══════════════════════════════════════════════════════════════════════════
# Integration Tests
# ══════════════════════════════════════════════════════════════════════════


def test_full_prompt_construction(sample_brief, sample_session_context):
    """Full system prompt construction with all features."""
    persona = DMPersona()
    persona.register_npc(
        "Aldric",
        "en_us_male_warrior",
        personality_traits=["brave", "loyal"],
    )

    prompt = persona.build_system_prompt(
        sample_brief,
        session_context=sample_session_context,
    )

    # All sections present
    assert "Dungeon Master" in prompt
    assert "attack_hit" in prompt
    assert "RECENT EVENTS:" in prompt
    assert "NPC CHARACTERIZATION:" in prompt
    assert "brave" in prompt
    assert "loyal" in prompt


def test_tone_affects_prompt_style_not_mechanics(sample_brief):
    """Tone parameters change prompt style, not mechanical outcomes."""
    # Two different tones
    persona_serious = DMPersona(tone=ToneConfig(gravity=0.9))
    persona_humorous = DMPersona(tone=ToneConfig(gravity=0.2))

    prompt_serious = persona_serious.build_system_prompt(sample_brief)
    prompt_humorous = persona_humorous.build_system_prompt(sample_brief)

    # Prompts differ in style
    assert prompt_serious != prompt_humorous

    # But both contain same mechanical context
    assert "attack_hit" in prompt_serious
    assert "attack_hit" in prompt_humorous
    assert "moderate" in prompt_serious
    assert "moderate" in prompt_humorous
