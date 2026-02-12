"""Tests for WO-057 PromptPackBuilder (GAP-007 Resolution).

Validates that PromptPackBuilder correctly assembles a PromptPack
from NarrativeBrief + session context, replacing both PATH 1
(GuardedNarrationService._build_llm_prompt) and PATH 2
(ContextAssembler.assemble + DMPersona.build_system_prompt).

Test Plan (from WO-057 spec):
- Build from minimal NarrativeBrief → TruthChannel populated, Memory empty
- Build from full NarrativeBrief → all TruthChannel fields populated
- Memory channel truncation → previous_narrations truncated to budget
- Session facts inclusion → facts appear in MemoryChannel
- Determinism → same inputs → same PromptPack.serialize() output
- Style config override → custom StyleChannel overrides defaults
- Forbidden content present → TaskChannel.forbidden_content includes mechanical numbers

Evidence:
- WO-057: PromptPack Consolidation (GAP-007 Resolution)
- AD-002: Lens Context Orchestration (five-channel spec)
- WO-045B: PromptPack v1 Schema
"""

import pytest

from aidm.lens.narrative_brief import NarrativeBrief
from aidm.lens.prompt_pack_builder import PromptPackBuilder
from aidm.schemas.prompt_pack import (
    PromptPack,
    TruthChannel,
    MemoryChannel,
    TaskChannel,
    StyleChannel,
    OutputContract,
    TASK_NARRATION,
    PROMPT_PACK_SCHEMA_VERSION,
)


# ==============================================================================
# HELPERS
# ==============================================================================


def _minimal_brief() -> NarrativeBrief:
    """Minimal NarrativeBrief with required fields only."""
    return NarrativeBrief(
        action_type="attack_hit",
        actor_name="Kael",
    )


def _full_brief() -> NarrativeBrief:
    """Full NarrativeBrief with all fields populated."""
    return NarrativeBrief(
        action_type="attack_hit",
        actor_name="Kael",
        target_name="Goblin Scout",
        outcome_summary="Kael strikes the goblin with his longsword",
        severity="moderate",
        weapon_name="Longsword",
        damage_type="slashing",
        condition_applied="shaken",
        target_defeated=False,
        visible_gear=["grappling_hook_external", "rope_coil_slung"],
        previous_narrations=[
            "Kael charged forward, shield raised.",
            "The goblin snarled and readied its spear.",
        ],
        scene_description="A dimly lit dungeon corridor",
    )


# ==============================================================================
# BUILD FROM MINIMAL NARRATIVEBRIEF
# ==============================================================================


def test_build_from_minimal_brief():
    """Build from minimal NarrativeBrief: TruthChannel populated, Memory empty."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief())

    # TruthChannel populated from brief
    assert pack.truth.action_type == "attack_hit"
    assert pack.truth.actor_name == "Kael"
    assert pack.truth.target_name is None
    assert pack.truth.severity == "minor"  # Default

    # MemoryChannel empty (no previous narrations, no session facts)
    assert pack.memory.previous_narrations == ()
    assert pack.memory.session_facts == ()

    # TaskChannel defaults
    assert pack.task.task_type == TASK_NARRATION
    assert pack.task.output_min_sentences == 2
    assert pack.task.output_max_sentences == 4

    # StyleChannel defaults
    assert pack.style.verbosity == "moderate"
    assert pack.style.drama == "dramatic"

    # OutputContract defaults
    assert pack.contract.max_length_chars == 600
    assert pack.contract.required_provenance == "[NARRATIVE]"


def test_build_returns_prompt_pack():
    """build() returns a PromptPack instance."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief())
    assert isinstance(pack, PromptPack)


def test_build_schema_version():
    """PromptPack carries current schema version."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief())
    assert pack.schema_version == PROMPT_PACK_SCHEMA_VERSION


# ==============================================================================
# BUILD FROM FULL NARRATIVEBRIEF
# ==============================================================================


def test_build_from_full_brief():
    """Build from full NarrativeBrief: all TruthChannel fields populated."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_full_brief())

    assert pack.truth.action_type == "attack_hit"
    assert pack.truth.actor_name == "Kael"
    assert pack.truth.target_name == "Goblin Scout"
    assert pack.truth.outcome_summary == "Kael strikes the goblin with his longsword"
    assert pack.truth.severity == "moderate"
    assert pack.truth.weapon_name == "Longsword"
    assert pack.truth.damage_type == "slashing"
    assert pack.truth.condition_applied == "shaken"
    assert pack.truth.target_defeated is False
    assert pack.truth.scene_description == "A dimly lit dungeon corridor"


def test_build_visible_gear():
    """Visible gear from NarrativeBrief appears in TruthChannel."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_full_brief())
    assert pack.truth.visible_gear == ["grappling_hook_external", "rope_coil_slung"]


def test_build_previous_narrations_in_memory():
    """Previous narrations from NarrativeBrief appear in MemoryChannel."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_full_brief())
    assert len(pack.memory.previous_narrations) == 2
    assert "Kael charged forward, shield raised." in pack.memory.previous_narrations


# ==============================================================================
# MEMORY CHANNEL TRUNCATION
# ==============================================================================


def test_memory_truncation():
    """Previous narrations truncated to token budget."""
    # Create brief with many long narrations
    long_narrations = [f"This is narration number {i} with enough words to consume tokens." for i in range(50)]
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Kael",
        previous_narrations=long_narrations,
    )

    # Very small budget — should truncate
    builder = PromptPackBuilder(memory_token_budget=20)
    pack = builder.build(brief=brief)

    # Should have fewer narrations than input
    assert len(pack.memory.previous_narrations) < len(long_narrations)
    assert len(pack.memory.previous_narrations) > 0


def test_memory_truncation_preserves_order():
    """Truncation preserves narration order (most relevant first)."""
    narrations = ["First narration.", "Second narration.", "Third narration."]
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Kael",
        previous_narrations=narrations,
    )

    builder = PromptPackBuilder(memory_token_budget=200)
    pack = builder.build(brief=brief)

    # Order preserved
    result = list(pack.memory.previous_narrations)
    assert result == narrations


def test_memory_budget_respected():
    """Total estimated tokens in MemoryChannel stays within budget."""
    narrations = [f"Word " * 20 for _ in range(10)]  # ~20 words each
    facts = [f"Fact " * 10 for _ in range(10)]  # ~10 words each
    brief = NarrativeBrief(
        action_type="test",
        actor_name="Test",
        previous_narrations=narrations,
    )

    budget = 50
    builder = PromptPackBuilder(memory_token_budget=budget)
    pack = builder.build(brief=brief, session_facts=facts)

    # Verify we didn't exceed budget (estimate tokens ourselves)
    total = 0
    for n in pack.memory.previous_narrations:
        total += int(len(n.split()) * 1.3)
    for f in pack.memory.session_facts:
        total += int(len(f.split()) * 1.3)
    assert total <= budget


# ==============================================================================
# SESSION FACTS
# ==============================================================================


def test_session_facts_included():
    """Session facts from snapshot appear in MemoryChannel."""
    brief = _minimal_brief()
    facts = ["The party entered the dungeon at dusk.", "A strange rumble echoes."]

    builder = PromptPackBuilder()
    pack = builder.build(brief=brief, session_facts=facts)

    assert len(pack.memory.session_facts) == 2
    assert "The party entered the dungeon at dusk." in pack.memory.session_facts


def test_session_facts_empty_by_default():
    """No session facts when none provided."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief())
    assert pack.memory.session_facts == ()


def test_session_facts_truncated_after_narrations():
    """Session facts fill remaining budget after previous_narrations."""
    narrations = ["A long narration with many words to consume most of the budget tokens."]
    facts = [f"Fact number {i} with extra words." for i in range(20)]
    brief = NarrativeBrief(
        action_type="test",
        actor_name="Test",
        previous_narrations=narrations,
    )

    builder = PromptPackBuilder(memory_token_budget=30)
    pack = builder.build(brief=brief, session_facts=facts)

    # Narrations take priority, facts fill remainder
    assert len(pack.memory.previous_narrations) > 0
    # Total should be within budget
    total = 0
    for n in pack.memory.previous_narrations:
        total += int(len(n.split()) * 1.3)
    for f in pack.memory.session_facts:
        total += int(len(f.split()) * 1.3)
    assert total <= 30


# ==============================================================================
# DETERMINISM
# ==============================================================================


def test_determinism_same_inputs_same_output():
    """AD-002: Same inputs → same PromptPack.serialize() output."""
    builder = PromptPackBuilder()
    brief = _full_brief()
    facts = ["The party entered at dusk."]

    pack1 = builder.build(brief=brief, session_facts=facts)
    pack2 = builder.build(brief=brief, session_facts=facts)

    assert pack1.serialize() == pack2.serialize()


def test_determinism_10x():
    """AD-002: Determinism verified over 10 replays."""
    builder = PromptPackBuilder()
    brief = _full_brief()
    facts = ["The party entered at dusk."]

    reference = builder.build(brief=brief, session_facts=facts).serialize()
    for _ in range(10):
        replay = builder.build(brief=brief, session_facts=facts).serialize()
        assert replay == reference


def test_determinism_json():
    """JSON serialization is also deterministic."""
    builder = PromptPackBuilder()
    brief = _full_brief()

    pack1 = builder.build(brief=brief)
    pack2 = builder.build(brief=brief)

    assert pack1.to_json() == pack2.to_json()


# ==============================================================================
# STYLE CONFIG OVERRIDE
# ==============================================================================


def test_style_defaults():
    """Default style is moderate/dramatic when no override provided."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief())
    assert pack.style.verbosity == "moderate"
    assert pack.style.drama == "dramatic"
    assert pack.style.humor == "none"


def test_style_override():
    """Custom StyleChannel overrides defaults."""
    custom_style = StyleChannel(
        verbosity="terse",
        drama="epic",
        humor="wry",
        grittiness="gritty",
        dm_persona="menacing",
    )
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief(), style=custom_style)

    assert pack.style.verbosity == "terse"
    assert pack.style.drama == "epic"
    assert pack.style.humor == "wry"
    assert pack.style.grittiness == "gritty"
    assert pack.style.dm_persona == "menacing"


def test_style_override_serialized():
    """Custom style appears in serialized output."""
    custom_style = StyleChannel(verbosity="verbose", drama="understated")
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief(), style=custom_style)

    text = pack.serialize()
    assert "Verbosity: verbose" in text
    assert "Drama: understated" in text


# ==============================================================================
# CONTRACT OVERRIDE
# ==============================================================================


def test_contract_defaults():
    """Default contract: 600 chars, prose, [NARRATIVE]."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief())
    assert pack.contract.max_length_chars == 600
    assert pack.contract.required_provenance == "[NARRATIVE]"
    assert pack.contract.json_mode is False


def test_contract_override():
    """Custom OutputContract overrides defaults."""
    custom_contract = OutputContract(max_length_chars=300)
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief(), contract=custom_contract)
    assert pack.contract.max_length_chars == 300


# ==============================================================================
# FORBIDDEN CONTENT
# ==============================================================================


def test_forbidden_content_present():
    """TaskChannel.forbidden_content includes mechanical numbers."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief())

    forbidden = pack.task.forbidden_content
    assert "damage numbers" in forbidden
    assert "AC values" in forbidden
    assert "HP values" in forbidden
    assert "attack bonus values" in forbidden
    assert "die roll results" in forbidden
    assert "rule citations" in forbidden


def test_forbidden_content_serialized():
    """Forbidden content appears in serialized output."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief())
    text = pack.serialize()

    assert "- damage numbers" in text
    assert "- HP values" in text


# ==============================================================================
# SERIALIZATION FORMAT
# ==============================================================================


def test_serialized_has_all_channels():
    """Serialized output contains all five channel markers."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_full_brief(), session_facts=["A fact."])
    text = pack.serialize()

    assert "[TRUTH]" in text
    assert "[/TRUTH]" in text
    assert "[MEMORY]" in text
    assert "[/MEMORY]" in text
    assert "[TASK]" in text
    assert "[/TASK]" in text
    assert "[STYLE]" in text
    assert "[/STYLE]" in text
    assert "[CONTRACT]" in text
    assert "[/CONTRACT]" in text


def test_serialized_truth_content():
    """Truth channel contains brief data in serialized output."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_full_brief())
    text = pack.serialize()

    assert "Actor: Kael" in text
    assert "Target: Goblin Scout" in text
    assert "Severity: moderate" in text
    assert "Weapon: Longsword" in text
    assert "Damage Type: slashing" in text


def test_serialized_scene_description():
    """Scene description appears in truth channel."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_full_brief())
    text = pack.serialize()

    assert "Scene: A dimly lit dungeon corridor" in text


def test_serialized_target_defeated():
    """Target defeated flag appears when set."""
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Kael",
        target_name="Goblin",
        target_defeated=True,
    )
    builder = PromptPackBuilder()
    pack = builder.build(brief=brief)
    text = pack.serialize()

    assert "Target Defeated: yes" in text


# ==============================================================================
# IMMUTABILITY
# ==============================================================================


def test_result_is_frozen():
    """PromptPack from builder is frozen (immutable)."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief())

    with pytest.raises(AttributeError):
        pack.schema_version = "2.0"


# ==============================================================================
# EDGE CASES
# ==============================================================================


def test_empty_session_facts_list():
    """Empty session_facts list produces empty facts tuple."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief(), session_facts=[])
    assert pack.memory.session_facts == ()


def test_none_session_facts():
    """None session_facts produces empty facts tuple."""
    builder = PromptPackBuilder()
    pack = builder.build(brief=_minimal_brief(), session_facts=None)
    assert pack.memory.session_facts == ()


def test_zero_memory_budget():
    """Zero memory budget produces empty MemoryChannel."""
    brief = NarrativeBrief(
        action_type="test",
        actor_name="Test",
        previous_narrations=["A narration."],
    )
    builder = PromptPackBuilder(memory_token_budget=0)
    pack = builder.build(brief=brief, session_facts=["A fact."])

    assert pack.memory.previous_narrations == ()
    assert pack.memory.session_facts == ()


def test_condition_applied_in_truth():
    """Condition applied carries through to TruthChannel."""
    brief = NarrativeBrief(
        action_type="spell_debuff_applied",
        actor_name="Mage",
        target_name="Ogre",
        condition_applied="blinded",
    )
    builder = PromptPackBuilder()
    pack = builder.build(brief=brief)

    assert pack.truth.condition_applied == "blinded"
    text = pack.serialize()
    assert "Condition Applied: blinded" in text
