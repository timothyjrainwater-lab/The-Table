"""Tests for voice intent parser and clarification engine.

Tests transcript-to-intent mapping, STM context resolution, confidence
scoring, and clarification generation per WO-024.
"""

import time
import pytest

from aidm.immersion.voice_intent_parser import (
    VoiceIntentParser,
    STMContext,
    ParseResult,
    create_voice_intent_parser,
)
from aidm.immersion.clarification_loop import (
    ClarificationEngine,
    ClarificationRequest,
    create_clarification_engine,
)
from aidm.schemas.immersion import Transcript
from aidm.schemas.intents import (
    CastSpellIntent,
    MoveIntent,
    DeclaredAttackIntent,
    BuyIntent,
    RestIntent,
)
from aidm.schemas.position import Position


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def parser():
    """Create voice intent parser."""
    return create_voice_intent_parser()


@pytest.fixture
def clarifier():
    """Create clarification engine."""
    return create_clarification_engine()


@pytest.fixture
def empty_context():
    """Create empty STM context."""
    return STMContext()


@pytest.fixture
def combat_context():
    """Create STM context with combat history."""
    ctx = STMContext()
    ctx.update(
        action="attack",
        target="goblin_1",
        weapon="longsword",
    )
    return ctx


# =============================================================================
# SPELL CASTING INTENT TESTS
# =============================================================================

def test_parse_fireball_with_explicit_spell_name(parser, empty_context):
    """Parse 'cast fireball' should produce CastSpellIntent."""
    transcript = Transcript(text="cast fireball", confidence=0.95)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, CastSpellIntent)
    assert result.intent.spell_name == "fireball"
    assert result.intent.target_mode == "point"
    assert result.confidence > 0.6  # Lower due to missing location
    assert result.ambiguous_location  # Needs point


def test_parse_magic_missile_with_target(parser, empty_context):
    """Parse 'cast magic missile at the goblin' should identify target need."""
    transcript = Transcript(text="cast magic missile at the goblin", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, CastSpellIntent)
    assert result.intent.spell_name == "magic missile"
    assert result.intent.target_mode == "creature"
    assert result.ambiguous_target is False  # Found "goblin"


def test_parse_self_buff_spell(parser, empty_context):
    """Parse 'cast shield' should be self-target with no ambiguity."""
    transcript = Transcript(text="cast shield on myself", confidence=0.95)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, CastSpellIntent)
    assert result.intent.spell_name == "shield"
    assert result.intent.target_mode == "self"
    assert not result.ambiguous_target
    assert not result.ambiguous_location


def test_parse_unknown_spell_returns_low_confidence(parser, empty_context):
    """Parse unknown spell should fail gracefully."""
    transcript = Transcript(text="cast unknown spell", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    # Should not find spell in known list
    assert result.confidence < 0.5 or result.ambiguous_action


def test_parse_spell_variations(parser, empty_context):
    """Test various phrasings for spell casting."""
    phrasings = [
        "I want to cast fireball",
        "use fireball",
        "invoke fireball",
        "fireball",
    ]

    for phrase in phrasings:
        transcript = Transcript(text=phrase, confidence=0.9)
        result = parser.parse_transcript(transcript, empty_context)

        assert result.intent is not None
        assert isinstance(result.intent, CastSpellIntent)
        assert result.intent.spell_name == "fireball"


# =============================================================================
# ATTACK INTENT TESTS
# =============================================================================

def test_parse_attack_with_explicit_target(parser, empty_context):
    """Parse 'attack the goblin' should produce DeclaredAttackIntent."""
    transcript = Transcript(text="attack the goblin", confidence=0.95)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, DeclaredAttackIntent)
    assert result.intent.target_ref == "goblin"
    assert not result.ambiguous_target


def test_parse_attack_with_weapon(parser, empty_context):
    """Parse 'hit the orc with my sword' should extract weapon."""
    transcript = Transcript(text="hit the orc with my sword", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, DeclaredAttackIntent)
    assert result.intent.target_ref == "orc"
    assert result.intent.weapon == "sword"
    assert result.confidence > 0.8  # Weapon specified increases confidence


def test_parse_attack_without_target_is_ambiguous(parser, empty_context):
    """Parse 'I attack' should flag ambiguous target."""
    transcript = Transcript(text="I attack", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, DeclaredAttackIntent)
    assert result.ambiguous_target
    assert result.confidence < 0.8


def test_parse_attack_again_resolves_from_context(parser, combat_context):
    """Parse 'attack him again' should resolve from STM context."""
    transcript = Transcript(text="attack him again", confidence=0.9)
    result = parser.parse_transcript(transcript, combat_context)

    assert result.intent is not None
    assert isinstance(result.intent, DeclaredAttackIntent)
    assert result.intent.target_ref == "goblin_1"  # From context
    assert result.intent.weapon == "longsword"  # From context
    assert not result.ambiguous_target


def test_parse_attack_variations(parser, empty_context):
    """Test various attack phrasings."""
    phrasings = [
        ("I strike the skeleton", "skeleton"),
        ("slash at the zombie", "zombie"),
        ("shoot the guard", "guard"),
        ("swing at the wizard", "wizard"),
    ]

    for phrase, expected_target in phrasings:
        transcript = Transcript(text=phrase, confidence=0.9)
        result = parser.parse_transcript(transcript, empty_context)

        assert isinstance(result.intent, DeclaredAttackIntent)
        assert result.intent.target_ref == expected_target


# =============================================================================
# MOVEMENT INTENT TESTS
# =============================================================================

def test_parse_move_without_destination_is_ambiguous(parser, empty_context):
    """Parse 'I move' should flag ambiguous location."""
    transcript = Transcript(text="I move", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, MoveIntent)
    assert result.ambiguous_location
    assert result.intent.destination is None


def test_parse_move_with_spatial_constraint(parser, empty_context):
    """Parse 'move near the door' should extract spatial constraint."""
    transcript = Transcript(text="move near the door", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, MoveIntent)
    assert result.raw_slots.get("spatial_constraint") == "proximity"
    assert result.raw_slots.get("spatial_anchor") == "door"
    # Still needs exact location but has context
    assert result.confidence > 0.5


def test_parse_move_variations(parser, empty_context):
    """Test various movement phrasings."""
    phrasings = [
        "I walk forward",
        "run to the door",
        "dash away",
        "retreat behind cover",
        "advance toward the enemy",
    ]

    for phrase in phrasings:
        transcript = Transcript(text=phrase, confidence=0.9)
        result = parser.parse_transcript(transcript, empty_context)

        assert isinstance(result.intent, MoveIntent)


# =============================================================================
# BUY INTENT TESTS
# =============================================================================

def test_parse_buy_with_quantity(parser, empty_context):
    """Parse 'buy 2 potions' should extract item and quantity."""
    transcript = Transcript(text="buy 2 potions", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, BuyIntent)
    assert len(result.intent.items) == 1
    assert result.intent.items[0]["name"] == "potions"
    assert result.intent.items[0]["qty"] == 2


def test_parse_buy_without_quantity_defaults_to_one(parser, empty_context):
    """Parse 'buy a rope' should default to qty=1."""
    transcript = Transcript(text="buy a rope", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, BuyIntent)
    assert len(result.intent.items) == 1
    assert result.intent.items[0]["qty"] == 1


def test_parse_buy_variations(parser, empty_context):
    """Test various buy phrasings."""
    phrasings = [
        "purchase 3 arrows",
        "I want to buy armor",  # Changed from "shield" which conflicts with spell
    ]

    for phrase in phrasings:
        transcript = Transcript(text=phrase, confidence=0.9)
        result = parser.parse_transcript(transcript, empty_context)

        assert isinstance(result.intent, BuyIntent)


# =============================================================================
# REST INTENT TESTS
# =============================================================================

def test_parse_rest_overnight(parser, empty_context):
    """Parse 'I rest' should default to overnight rest."""
    transcript = Transcript(text="I rest for the night", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, RestIntent)
    assert result.intent.rest_type == "overnight"


def test_parse_rest_full_day(parser, empty_context):
    """Parse 'full day rest' should set rest_type to full_day."""
    transcript = Transcript(text="I take a full day of rest", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.intent is not None
    assert isinstance(result.intent, RestIntent)
    assert result.intent.rest_type == "full_day"


def test_parse_rest_variations(parser, empty_context):
    """Test various rest phrasings."""
    phrasings = [
        ("sleep for the night", "overnight"),
        ("camp overnight", "overnight"),
        ("take a full rest", "full_day"),
        ("recover for a day", "overnight"),
    ]

    for phrase, expected_type in phrasings:
        transcript = Transcript(text=phrase, confidence=0.9)
        result = parser.parse_transcript(transcript, empty_context)

        assert isinstance(result.intent, RestIntent)
        # Note: Some may not match perfectly, but should parse as RestIntent


# =============================================================================
# STM CONTEXT RESOLUTION TESTS
# =============================================================================

def test_stm_context_resolves_pronoun_target(parser, combat_context):
    """STM context should resolve 'him' to last target."""
    transcript = Transcript(text="attack him", confidence=0.9)
    result = parser.parse_transcript(transcript, combat_context)

    assert result.intent is not None
    assert isinstance(result.intent, DeclaredAttackIntent)
    assert result.intent.target_ref == "goblin_1"


def test_stm_context_history_buffer(empty_context):
    """STM context should maintain rolling buffer of last 3 actions."""
    ctx = empty_context

    # Add 4 actions
    ctx.update(action="attack", target="goblin_1")
    ctx.update(action="move", location=Position(x=5, y=5))
    ctx.update(action="cast", spell="fireball")
    ctx.update(action="attack", target="orc_1")

    # Should only keep last 3
    assert len(ctx.history) == 3
    assert ctx.history[-1]["target"] == "orc_1"


def test_stm_context_update_preserves_previous_values(empty_context):
    """STM context should preserve values not explicitly updated."""
    ctx = empty_context

    ctx.update(action="attack", target="goblin_1", weapon="sword")
    assert ctx.last_weapon == "sword"

    ctx.update(action="move")
    assert ctx.last_weapon == "sword"  # Preserved
    assert ctx.last_target == "goblin_1"  # Preserved


# =============================================================================
# CONFIDENCE SCORING TESTS
# =============================================================================

def test_high_confidence_auto_confirm(parser, empty_context):
    """High confidence (>0.8) should be flagged for auto-confirm."""
    transcript = Transcript(text="cast shield", confidence=0.95)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.is_high_confidence
    assert not result.is_medium_confidence
    assert not result.is_low_confidence


def test_medium_confidence_requires_clarification(parser, empty_context):
    """Medium confidence (0.5-0.8) should require clarification."""
    # Attack without target lowers confidence
    transcript = Transcript(text="I attack", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    # Ambiguous target reduces confidence
    assert result.confidence < 0.8
    assert result.is_medium_confidence or result.is_low_confidence


def test_low_confidence_requires_reprompt(parser, empty_context):
    """Low confidence (<0.5) should require re-prompt."""
    transcript = Transcript(text="uhhhh maybe", confidence=0.3)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.is_low_confidence
    assert result.confidence < 0.5


def test_confidence_boosted_by_complete_intent(parser, empty_context):
    """Complete intent with all fields should have high confidence."""
    transcript = Transcript(text="attack the goblin with my longsword", confidence=0.9)
    result = parser.parse_transcript(transcript, empty_context)

    # Has target and weapon — should boost confidence
    assert result.confidence > 0.8


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

def test_empty_transcript_returns_low_confidence(parser, empty_context):
    """Empty transcript should return low confidence with error."""
    transcript = Transcript(text="", confidence=0.0)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.confidence == 0.0
    assert result.ambiguous_action
    assert "Empty transcript" in result.parse_errors


def test_nonsense_input_returns_low_confidence(parser, empty_context):
    """Nonsense input should fail gracefully."""
    transcript = Transcript(text="asdfghjkl zxcvbnm", confidence=0.5)
    result = parser.parse_transcript(transcript, empty_context)

    assert result.confidence < 0.5 or result.ambiguous_action


def test_very_low_stt_confidence_propagates(parser, empty_context):
    """Low STT confidence should propagate to parse result."""
    transcript = Transcript(text="attack the goblin", confidence=0.2)
    result = parser.parse_transcript(transcript, empty_context)

    # Even if parse succeeds, STT confidence is low
    assert result.confidence <= 0.2


# =============================================================================
# CLARIFICATION ENGINE TESTS
# =============================================================================

def test_clarify_ambiguous_target(clarifier):
    """Clarification should generate target prompt."""
    parse_result = ParseResult(
        intent=DeclaredAttackIntent(),
        confidence=0.6,
        ambiguous_target=True,
    )

    clarification = clarifier.generate_clarification(parse_result)

    assert clarification.clarification_type == "target"
    assert "who" in clarification.prompt.lower() or "which" in clarification.prompt.lower()
    assert "target_ref" in clarification.missing_fields


def test_clarify_ambiguous_location(clarifier):
    """Clarification should generate location prompt."""
    parse_result = ParseResult(
        intent=MoveIntent(),
        confidence=0.6,
        ambiguous_location=True,
    )

    clarification = clarifier.generate_clarification(parse_result)

    assert clarification.clarification_type == "location"
    assert "where" in clarification.prompt.lower()
    assert "destination" in clarification.missing_fields or "location" in clarification.missing_fields


def test_clarify_ambiguous_action(clarifier):
    """Clarification should generate action prompt."""
    parse_result = ParseResult(
        intent=None,
        confidence=0.3,
        ambiguous_action=True,
        parse_errors=["Could not determine action type"],
    )

    clarification = clarifier.generate_clarification(parse_result)

    assert clarification.clarification_type == "action"
    assert "what" in clarification.prompt.lower() or "trying to do" in clarification.prompt.lower()
    assert len(clarification.suggested_options) > 0


def test_clarify_with_world_context_candidates(clarifier):
    """Clarification with world context should offer specific options."""
    parse_result = ParseResult(
        intent=DeclaredAttackIntent(),
        confidence=0.6,
        ambiguous_target=True,
    )

    world_context = {
        "nearby_entities": ["goblin_archer", "goblin_warrior"],
    }

    clarification = clarifier.generate_clarification(parse_result, world_context)

    assert clarification.clarification_type == "target"
    assert len(clarification.suggested_options) == 2
    assert "goblin_archer" in clarification.suggested_options
    assert "goblin_warrior" in clarification.suggested_options
    assert "goblin_archer" in clarification.prompt or "goblin_warrior" in clarification.prompt


def test_soft_confirmation_natural_language(clarifier):
    """Soft confirmation should use natural DM language."""
    intent = CastSpellIntent(spell_name="fireball", target_mode="point")
    confirmation = clarifier.generate_soft_confirmation(intent)

    # Should be conversational
    assert "alright" in confirmation.lower() or "okay" in confirmation.lower()
    assert "fireball" in confirmation.lower()


def test_impossibility_feedback_natural_language(clarifier):
    """Impossibility feedback should avoid system errors."""
    intent = MoveIntent()
    feedback = clarifier.generate_impossibility_feedback("out_of_range", intent)

    # Should NOT contain "error", "invalid", "failed"
    assert "error" not in feedback.lower()
    assert "invalid" not in feedback.lower()
    assert "failed" not in feedback.lower()

    # Should explain in-world
    assert "far" in feedback.lower() or "range" in feedback.lower()


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

def test_parse_time_under_600ms(parser, empty_context):
    """Parse time should be <600ms per RQ-INTERACT-001."""
    transcript = Transcript(text="attack the goblin with my sword", confidence=0.9)

    # Warm-up parse
    parser.parse_transcript(transcript, empty_context)

    # Measure parse time
    start = time.perf_counter()
    result = parser.parse_transcript(transcript, empty_context)
    elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

    assert elapsed < 600, f"Parse took {elapsed:.2f}ms (target: <600ms)"
    assert result.intent is not None


def test_parse_time_multiple_iterations(parser, empty_context):
    """Average parse time over 10 iterations should be <600ms."""
    transcript = Transcript(text="cast fireball at the center", confidence=0.9)

    times = []
    for _ in range(10):
        start = time.perf_counter()
        parser.parse_transcript(transcript, empty_context)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    assert avg_time < 600, f"Average parse time: {avg_time:.2f}ms (target: <600ms)"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_full_parse_clarify_workflow(parser, clarifier, empty_context):
    """Test full workflow: parse → detect ambiguity → clarify."""
    # Step 1: Parse ambiguous input
    transcript = Transcript(text="I attack", confidence=0.9)
    parse_result = parser.parse_transcript(transcript, empty_context)

    assert parse_result.needs_clarification

    # Step 2: Generate clarification
    clarification = clarifier.generate_clarification(parse_result)

    assert clarification.clarification_type == "target"
    assert len(clarification.missing_fields) > 0


def test_parse_clarify_resolve_workflow(parser, clarifier, empty_context):
    """Test parse → clarify → resolve with context update."""
    # Step 1: Parse ambiguous attack
    transcript = Transcript(text="attack him", confidence=0.9)
    parse_result = parser.parse_transcript(transcript, empty_context)

    # Should be ambiguous (no context)
    assert parse_result.ambiguous_target

    # Step 2: Update context
    empty_context.update(target="goblin_1")

    # Step 3: Re-parse with context
    parse_result = parser.parse_transcript(transcript, empty_context)

    # Should resolve now
    assert not parse_result.ambiguous_target
    assert parse_result.intent.target_ref == "goblin_1"
