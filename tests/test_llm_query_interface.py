"""Tests for LLMQueryInterface (M3 LLM narration and memory query).

M3 IMPLEMENTATION TESTS
-----------------------
Tests LLM query interface for prompt templates, structured output, error handling.

Based on design: docs/design/LLM_QUERY_INTERFACE.md
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch

from aidm.narration.llm_query_interface import (
    LLMQueryInterface,
    WorldStateSummary,
    CharacterContext,
    LLMQueryError,
    UnparseableOutputError,
    OffTopicError,
    ConstraintViolationError,
    NarrationTemplate,
    QueryTemplate,
    StructuredOutputTemplate,
)
from aidm.schemas.campaign_memory import QueryResult


# =============================================================================
# Mock LLM Model
# =============================================================================


def create_mock_model(response_text: str = "Test narration") -> Mock:
    """Create mock LoadedModel for testing.

    Args:
        response_text: Text to return from model

    Returns:
        Mock LoadedModel
    """
    mock_model = Mock()
    mock_model.model_id = "test-model"

    # Mock inference engine
    def mock_inference(prompt, **kwargs):
        return {"choices": [{"text": response_text}]}

    mock_model.inference_engine = mock_inference

    return mock_model


# =============================================================================
# Initialization Tests
# =============================================================================


def test_llm_query_interface_initialization_with_model():
    """LLMQueryInterface initializes with model."""
    mock_model = create_mock_model()
    interface = LLMQueryInterface(loaded_model=mock_model)

    assert interface.loaded_model is not None
    assert interface.loaded_model.model_id == "test-model"
    assert interface.metrics["unparseable_output"] == 0


def test_llm_query_interface_initialization_without_model():
    """LLMQueryInterface initializes without model (fallback mode)."""
    interface = LLMQueryInterface(loaded_model=None)

    assert interface.loaded_model is None
    assert interface.metrics["unparseable_output"] == 0


# =============================================================================
# Template Tests
# =============================================================================


def test_narration_template_has_correct_token_budget():
    """NarrationTemplate has correct token budget."""
    template = NarrationTemplate()
    assert template.token_budget == 500


def test_query_template_has_correct_token_budget():
    """QueryTemplate has correct token budget."""
    template = QueryTemplate()
    assert template.token_budget == 800


def test_structured_output_template_has_correct_token_budget():
    """StructuredOutputTemplate has correct token budget."""
    template = StructuredOutputTemplate()
    assert template.token_budget == 600


# =============================================================================
# World State Summary Tests
# =============================================================================


def test_world_state_summary_to_markdown_empty():
    """WorldStateSummary converts to markdown (empty)."""
    summary = WorldStateSummary()
    markdown = summary.to_markdown()

    assert markdown == ""


def test_world_state_summary_to_markdown_with_npcs():
    """WorldStateSummary converts to markdown with NPCs."""
    summary = WorldStateSummary(
        active_npcs=["Goblin (HP 12/12)", "Orc (HP 20/20)"],
        player_location="Forest clearing",
    )
    markdown = summary.to_markdown()

    assert "Active NPCs:" in markdown
    assert "Goblin (HP 12/12)" in markdown
    assert "Orc (HP 20/20)" in markdown
    assert "Location: Forest clearing" in markdown


def test_world_state_summary_to_markdown_with_events():
    """WorldStateSummary converts to markdown with recent events."""
    summary = WorldStateSummary(
        recent_events=["Turn 1: Fighter attacked Goblin", "Turn 2: Goblin missed"],
    )
    markdown = summary.to_markdown()

    assert "Recent Events:" in markdown
    assert "Turn 1: Fighter attacked Goblin" in markdown
    assert "Turn 2: Goblin missed" in markdown


# =============================================================================
# Character Context Tests
# =============================================================================


def test_character_context_to_markdown_empty():
    """CharacterContext converts to markdown (empty)."""
    context = CharacterContext()
    markdown = context.to_markdown()

    assert markdown == ""


def test_character_context_to_markdown_with_data():
    """CharacterContext converts to markdown with data."""
    context = CharacterContext(
        pc_name="Theron",
        pc_level=5,
        pc_class="Fighter",
        hp_current=45,
        hp_max=50,
        status_effects=["Hasted"],
        equipped_items=["Longsword", "Plate Mail"],
    )
    markdown = context.to_markdown()

    assert "Player Characters:" in markdown
    assert "Theron (Level 5 Fighter)" in markdown
    assert "HP: 45/50" in markdown
    assert "Status: Hasted" in markdown
    assert "Equipment: Longsword, Plate Mail" in markdown


# =============================================================================
# Narration Generation Tests
# =============================================================================


def test_generate_narration_requires_model():
    """generate_narration raises error without model."""
    interface = LLMQueryInterface(loaded_model=None)
    world_state = WorldStateSummary()

    with pytest.raises(LLMQueryError, match="No LLM model loaded"):
        interface.generate_narration(
            player_action="Fighter attacks Goblin",
            world_state_summary=world_state,
        )


def test_generate_narration_enforces_temperature_boundary():
    """generate_narration enforces temperature ≥0.7 (LLM-002)."""
    mock_model = create_mock_model()
    interface = LLMQueryInterface(loaded_model=mock_model)
    world_state = WorldStateSummary()

    with pytest.raises(ValueError, match="temperature MUST be ≥0.7"):
        interface.generate_narration(
            player_action="Fighter attacks Goblin",
            world_state_summary=world_state,
            temperature=0.5,  # Too low
        )


def test_generate_narration_success():
    """generate_narration succeeds with valid input."""
    mock_model = create_mock_model(response_text="The fighter's blade strikes true!")
    interface = LLMQueryInterface(loaded_model=mock_model)
    world_state = WorldStateSummary()

    result = interface.generate_narration(
        player_action="Fighter attacks Goblin (HIT, 8 damage)",
        world_state_summary=world_state,
        temperature=0.8,
    )

    assert result == "The fighter's blade strikes true!"


def test_generate_narration_detects_hp_assignment():
    """generate_narration detects HP assignment constraint violation."""
    mock_model = create_mock_model(response_text="The goblin takes 15 HP damage!")
    interface = LLMQueryInterface(loaded_model=mock_model)
    world_state = WorldStateSummary()

    with pytest.raises(LLMQueryError, match="after 2 retries"):
        interface.generate_narration(
            player_action="Fighter attacks Goblin",
            world_state_summary=world_state,
            temperature=0.8,
        )

    assert interface.metrics["constraint_violations"] > 0


def test_generate_narration_detects_stat_assignment():
    """generate_narration detects stat assignment constraint violation."""
    mock_model = create_mock_model(response_text="The goblin now has AC: 15!")
    interface = LLMQueryInterface(loaded_model=mock_model)
    world_state = WorldStateSummary()

    with pytest.raises(LLMQueryError, match="after 2 retries"):
        interface.generate_narration(
            player_action="Fighter attacks Goblin",
            world_state_summary=world_state,
            temperature=0.8,
        )

    assert interface.metrics["constraint_violations"] > 0


# =============================================================================
# Memory Query Tests
# =============================================================================


def test_query_memory_requires_model():
    """query_memory raises error without model."""
    interface = LLMQueryInterface(loaded_model=None)

    with pytest.raises(LLMQueryError, match="No LLM model loaded"):
        interface.query_memory(
            natural_language_query="Find all NPCs in tavern",
            memory_snapshot={},
        )


def test_query_memory_enforces_temperature_boundary():
    """query_memory enforces temperature ≤0.5 (LLM-002)."""
    mock_model = create_mock_model()
    interface = LLMQueryInterface(loaded_model=mock_model)

    with pytest.raises(ValueError, match="temperature MUST be ≤0.5"):
        interface.query_memory(
            natural_language_query="Find all NPCs",
            memory_snapshot={},
            temperature=0.7,  # Too high
        )


def test_query_memory_success():
    """query_memory succeeds with valid JSON response."""
    response_json = {
        "entity_ids": ["theron", "merchant_bob"],
        "event_ids": ["ev_001", "ev_007"],
        "summary": "Theron showed loyalty",
    }
    mock_model = create_mock_model(response_text=json.dumps(response_json))
    interface = LLMQueryInterface(loaded_model=mock_model)

    result = interface.query_memory(
        natural_language_query="What evidence exists for Theron showing loyalty?",
        memory_snapshot={
            "session_ledger": {},
            "evidence_ledger": {},
        },
        temperature=0.3,
    )

    assert isinstance(result, QueryResult)
    assert result.entity_ids == ["theron", "merchant_bob"]
    assert result.event_ids == ["ev_001", "ev_007"]
    assert result.summary == "Theron showed loyalty"


def test_query_memory_handles_unparseable_output():
    """query_memory handles unparseable output with retry."""
    mock_model = create_mock_model(response_text="This is not JSON")
    interface = LLMQueryInterface(loaded_model=mock_model)

    result = interface.query_memory(
        natural_language_query="Find all NPCs",
        memory_snapshot={},
        temperature=0.3,
    )

    # Should return empty result after retries
    assert result.entity_ids == []
    assert result.event_ids == []
    assert "failed" in result.summary.lower()
    assert interface.metrics["unparseable_output"] > 0


def test_query_memory_partial_json_extraction():
    """query_memory extracts JSON from mixed output."""
    response_text = 'Here is the result: {"entity_ids": ["theron"], "event_ids": [], "summary": "Found one"} Extra text.'
    mock_model = create_mock_model(response_text=response_text)
    interface = LLMQueryInterface(loaded_model=mock_model)

    result = interface.query_memory(
        natural_language_query="Find Theron",
        memory_snapshot={},
        temperature=0.3,
    )

    assert result.entity_ids == ["theron"]
    assert result.summary == "Found one"


# =============================================================================
# Structured Output Tests
# =============================================================================


def test_generate_structured_output_requires_model():
    """generate_structured_output raises error without model."""
    interface = LLMQueryInterface(loaded_model=None)

    with pytest.raises(LLMQueryError, match="No LLM model loaded"):
        interface.generate_structured_output(
            request_description="NPC Goblin Warrior",
            json_schema={"name": "string", "hp": "number"},
        )


def test_generate_structured_output_success():
    """generate_structured_output succeeds with valid JSON."""
    response_json = {
        "name": "Goblin Warrior",
        "hp": 6,
        "ac": 15,
        "attack_bonus": 2,
        "species": "Goblin",
        "description": "A wiry humanoid with green skin",
    }
    mock_model = create_mock_model(response_text=json.dumps(response_json))
    interface = LLMQueryInterface(loaded_model=mock_model)

    result = interface.generate_structured_output(
        request_description="NPC Goblin Warrior",
        json_schema={
            "name": "string",
            "hp": "number (1-20)",
            "ac": "number (10-16)",
            "attack_bonus": "number (+0 to +3)",
            "species": "string",
            "description": "string",
        },
        temperature=0.4,
    )

    assert result["name"] == "Goblin Warrior"
    assert result["hp"] == 6
    assert result["ac"] == 15


def test_generate_structured_output_handles_malformed_json():
    """generate_structured_output handles malformed JSON with retry."""
    mock_model = create_mock_model(response_text='{"name": "Goblin", incomplete...')
    interface = LLMQueryInterface(loaded_model=mock_model)

    with pytest.raises(UnparseableOutputError, match="after 2 retries"):
        interface.generate_structured_output(
            request_description="NPC Goblin",
            json_schema={"name": "string"},
        )

    assert interface.metrics["unparseable_output"] > 0
    assert interface.metrics["retries"] > 0


# =============================================================================
# Prompt Building Tests
# =============================================================================


def test_build_narration_prompt_structure():
    """_build_narration_prompt creates valid prompt structure."""
    interface = LLMQueryInterface()
    world_state = WorldStateSummary(
        active_npcs=["Goblin (HP 12/12)"],
        player_location="Forest clearing",
        recent_events=["Turn 1: Fighter attacked"],
    )

    prompt = interface._build_narration_prompt(
        player_action="Fighter attacks Goblin (HIT, 8 damage)",
        world_state_summary=world_state,
        character_context=None,
    )

    assert "SYSTEM CONTEXT:" in prompt
    assert "WORLD STATE:" in prompt
    assert "NARRATION REQUEST:" in prompt
    assert "Fighter attacks Goblin" in prompt
    assert "Goblin (HP 12/12)" in prompt
    assert "Do not invent abilities" in prompt


def test_build_query_prompt_structure():
    """_build_query_prompt creates valid prompt structure."""
    interface = LLMQueryInterface()
    memory_snapshot = {
        "session_ledger": {"facts": ["Theron befriended merchant"]},
        "evidence_ledger": {"entries": []},
    }

    prompt = interface._build_query_prompt(
        query="What evidence exists for Theron?",
        memory_snapshot=memory_snapshot,
    )

    assert "SYSTEM CONTEXT:" in prompt
    assert "INDEXED MEMORY:" in prompt
    assert "QUERY:" in prompt
    assert "What evidence exists for Theron?" in prompt
    assert "Extract facts only from indexed memory" in prompt
    assert "Do not invent or infer" in prompt


def test_build_structured_output_prompt_structure():
    """_build_structured_output_prompt creates valid prompt structure."""
    interface = LLMQueryInterface()
    schema = {
        "name": "string",
        "hp": "number",
        "ac": "number",
    }

    prompt = interface._build_structured_output_prompt(
        request_description="NPC Goblin Warrior",
        json_schema=schema,
    )

    assert "SYSTEM CONTEXT:" in prompt
    assert "GENERATION REQUEST:" in prompt
    assert "NPC Goblin Warrior" in prompt
    assert "SCHEMA:" in prompt
    assert "CONSTRAINTS:" in prompt
    assert "D&D 3.5e rules only" in prompt
    assert "Output ONLY valid JSON" in prompt


# =============================================================================
# Validation Tests
# =============================================================================


def test_validate_narration_output_clean():
    """_validate_narration_output accepts clean output."""
    interface = LLMQueryInterface()

    # Should not raise
    interface._validate_narration_output(
        "The fighter's blade strikes true, and the goblin stumbles back with a cry of pain."
    )


def test_validate_narration_output_rejects_hp_mention():
    """_validate_narration_output rejects HP value mentions."""
    interface = LLMQueryInterface()

    with pytest.raises(ConstraintViolationError, match="HP values"):
        interface._validate_narration_output("The goblin takes 15 HP damage!")


def test_validate_narration_output_rejects_ability_scores():
    """_validate_narration_output rejects ability score assignments."""
    interface = LLMQueryInterface()

    with pytest.raises(ConstraintViolationError, match="ability scores"):
        interface._validate_narration_output("The goblin has Strength: 12 and Dexterity: 14")


def test_validate_narration_output_rejects_stat_assignments():
    """_validate_narration_output rejects stat assignments."""
    interface = LLMQueryInterface()

    with pytest.raises(ConstraintViolationError, match="assigns stats"):
        interface._validate_narration_output("The goblin now has AC: 15")


# =============================================================================
# Metrics Tests
# =============================================================================


def test_get_metrics_returns_copy():
    """get_metrics returns copy of metrics dict."""
    interface = LLMQueryInterface()
    interface.metrics["unparseable_output"] = 5

    metrics = interface.get_metrics()
    metrics["unparseable_output"] = 10

    # Original should be unchanged
    assert interface.metrics["unparseable_output"] == 5


def test_metrics_track_retries():
    """Metrics track retry attempts."""
    mock_model = create_mock_model(response_text="Invalid narration with 15 HP!")
    interface = LLMQueryInterface(loaded_model=mock_model)
    world_state = WorldStateSummary()

    try:
        interface.generate_narration(
            player_action="Fighter attacks",
            world_state_summary=world_state,
            temperature=0.8,
        )
    except LLMQueryError:
        pass

    assert interface.metrics["retries"] == 2  # MAX_RETRIES


def test_metrics_track_fallbacks():
    """Metrics track fallback occurrences."""
    mock_model = create_mock_model(response_text="Invalid narration with 15 HP!")
    interface = LLMQueryInterface(loaded_model=mock_model)
    world_state = WorldStateSummary()

    with pytest.raises(LLMQueryError):
        interface.generate_narration(
            player_action="Fighter attacks",
            world_state_summary=world_state,
            temperature=0.8,
        )

    # Fallback is tracked when exhausting retries
    assert interface.metrics["fallbacks"] == 1


# =============================================================================
# Integration Tests
# =============================================================================


def test_narration_with_full_context():
    """Generate narration with full world state and character context."""
    mock_model = create_mock_model(response_text="Epic battle narration!")
    interface = LLMQueryInterface(loaded_model=mock_model)

    world_state = WorldStateSummary(
        active_npcs=["Goblin Archer (HP 12/12, 30ft away)"],
        player_location="Forest clearing, dusk",
        active_threads=["clue_merchant_bob_rumors: status=active"],
        recent_events=[
            "Turn 10: Theron drew longsword, advanced 20ft",
            "Turn 11: Goblin fired arrow, missed",
        ],
    )

    character_context = CharacterContext(
        pc_name="Theron",
        pc_level=5,
        pc_class="Fighter",
        hp_current=45,
        hp_max=50,
        equipped_items=["Longsword", "Plate Mail"],
    )

    result = interface.generate_narration(
        player_action="Theron attacks Goblin with longsword (HIT, 8 damage)",
        world_state_summary=world_state,
        character_context=character_context,
        temperature=0.8,
    )

    assert result == "Epic battle narration!"


def test_query_memory_with_complex_snapshot():
    """Query memory with complex memory snapshot."""
    response_json = {
        "entity_ids": ["theron", "merchant_bob"],
        "event_ids": ["ev_001", "ev_007"],
        "summary": "Theron showed loyalty by defending allies",
    }
    mock_model = create_mock_model(response_text=json.dumps(response_json))
    interface = LLMQueryInterface(loaded_model=mock_model)

    memory_snapshot = {
        "session_ledger": {
            "session_id": "session_10",
            "facts_added": [
                "Theron befriended Merchant Bob",
                "Party explored ruined temple",
            ],
        },
        "evidence_ledger": {
            "entries": [
                {"id": "ev_001", "character_id": "theron", "evidence_type": "loyalty"},
                {"id": "ev_007", "character_id": "theron", "evidence_type": "loyalty"},
            ]
        },
        "thread_registry": {
            "clues": [{"id": "clue_merchant_bob_rumors", "status": "active"}]
        },
    }

    result = interface.query_memory(
        natural_language_query="What evidence exists for Theron showing loyalty?",
        memory_snapshot=memory_snapshot,
        temperature=0.3,
    )

    assert "theron" in result.entity_ids
    assert "ev_001" in result.event_ids
    assert "loyalty" in result.summary.lower()
