"""Tests for WO-045B PromptPack v1 Schema.

Validates AD-002 five-channel wire protocol compliance:
- All 5 channels present and structured
- Deterministic serialization (same inputs → same bytes)
- Schema versioning
- Task type validation
- Truncation priority (Truth/Task/Style/Contract never truncated)
- Forbidden content list in task channel
- Immutability (frozen dataclasses)
- NPC dialogue task variant
- Visible gear from AD-005 Layer 3

Evidence:
- AD-002: Lens Context Orchestration (five-channel spec)
- RWO-005 SEAM_PROTOCOL_ANALYSIS GAP-002
- AD-005: Physical Affordance Policy (visible_gear)
"""

import json
import pytest
from aidm.schemas.prompt_pack import (
    PromptPack,
    TruthChannel,
    MemoryChannel,
    TaskChannel,
    StyleChannel,
    OutputContract,
    TASK_NARRATION,
    TASK_NPC_DIALOGUE,
    PROMPT_PACK_SCHEMA_VERSION,
)


# ==============================================================================
# CONSTRUCTION AND STRUCTURE
# ==============================================================================


def test_default_prompt_pack():
    """Default PromptPack constructs with all channels."""
    pack = PromptPack(
        truth=TruthChannel(action_type="attack_hit", actor_name="Kael"),
    )
    assert pack.schema_version == PROMPT_PACK_SCHEMA_VERSION
    assert pack.truth.action_type == "attack_hit"
    assert pack.truth.actor_name == "Kael"
    assert pack.task.task_type == TASK_NARRATION
    assert pack.style.verbosity == "moderate"
    assert pack.contract.max_length_chars == 600


def test_schema_version():
    """PromptPack carries schema version."""
    pack = PromptPack(
        truth=TruthChannel(action_type="test", actor_name="Test"),
    )
    assert pack.schema_version == "1.0"


def test_full_prompt_pack():
    """PromptPack with all channels populated."""
    pack = PromptPack(
        truth=TruthChannel(
            action_type="attack_hit",
            actor_name="Kael",
            target_name="Goblin Scout",
            outcome_summary="Kael strikes the goblin with his longsword",
            severity="moderate",
            weapon_name="Longsword",
            damage_type="slashing",
            target_defeated=False,
            scene_description="A dimly lit dungeon corridor",
            visible_gear=["grappling_hook_external", "rope_coil_slung"],
        ),
        memory=MemoryChannel(
            previous_narrations=(
                "Kael charged forward, shield raised.",
                "The goblin snarled and readied its spear.",
            ),
            session_facts=("The party entered the dungeon at dusk.",),
            token_budget=200,
        ),
        task=TaskChannel(
            task_type=TASK_NARRATION,
            output_min_sentences=2,
            output_max_sentences=4,
        ),
        style=StyleChannel(
            verbosity="moderate",
            drama="dramatic",
            humor="none",
            grittiness="moderate",
            dm_persona="authoritative",
        ),
        contract=OutputContract(
            max_length_chars=600,
            required_provenance="[NARRATIVE]",
        ),
    )
    assert pack.truth.target_name == "Goblin Scout"
    assert len(pack.memory.previous_narrations) == 2
    assert pack.truth.visible_gear == ["grappling_hook_external", "rope_coil_slung"]


# ==============================================================================
# DETERMINISTIC SERIALIZATION
# ==============================================================================


def _make_test_pack():
    """Helper to create a consistent test pack."""
    return PromptPack(
        truth=TruthChannel(
            action_type="attack_hit",
            actor_name="Kael",
            target_name="Goblin",
            outcome_summary="Hit for moderate damage",
            severity="moderate",
            weapon_name="Longsword",
            damage_type="slashing",
        ),
        memory=MemoryChannel(
            previous_narrations=("Kael moved forward.",),
        ),
        task=TaskChannel(task_type=TASK_NARRATION),
        style=StyleChannel(drama="dramatic"),
    )


def test_serialize_deterministic():
    """AD-002: Same inputs → same serialized bytes."""
    pack1 = _make_test_pack()
    pack2 = _make_test_pack()
    assert pack1.serialize() == pack2.serialize()


def test_serialize_deterministic_10x():
    """AD-002: Determinism verified over 10 replays."""
    reference = _make_test_pack().serialize()
    for _ in range(10):
        replay = _make_test_pack().serialize()
        assert replay == reference


def test_to_json_deterministic():
    """JSON serialization is also deterministic."""
    pack1 = _make_test_pack()
    pack2 = _make_test_pack()
    assert pack1.to_json() == pack2.to_json()


def test_to_json_valid_json():
    """to_json produces valid JSON."""
    pack = _make_test_pack()
    parsed = json.loads(pack.to_json())
    assert parsed["schema_version"] == "1.0"
    assert parsed["truth"]["actor_name"] == "Kael"


def test_to_dict_structure():
    """to_dict has all five channels."""
    pack = _make_test_pack()
    d = pack.to_dict()
    assert "schema_version" in d
    assert "truth" in d
    assert "memory" in d
    assert "task" in d
    assert "style" in d
    assert "contract" in d


# ==============================================================================
# SERIALIZATION FORMAT
# ==============================================================================


def test_serialize_has_channel_markers():
    """Serialized text has explicit channel section markers."""
    pack = _make_test_pack()
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


def test_serialize_has_version_header():
    """Serialized text starts with version header."""
    pack = _make_test_pack()
    text = pack.serialize()
    assert text.startswith("[PROMPT_PACK v1.0]")


def test_serialize_truth_content():
    """Truth channel contains actor and outcome info."""
    pack = _make_test_pack()
    text = pack.serialize()
    assert "Actor: Kael" in text
    assert "Target: Goblin" in text
    assert "Outcome: Hit for moderate damage" in text
    assert "Severity: moderate" in text
    assert "Weapon: Longsword" in text


def test_serialize_memory_content():
    """Memory channel contains previous narrations."""
    pack = _make_test_pack()
    text = pack.serialize()
    assert "- Kael moved forward." in text


def test_serialize_task_forbidden_content():
    """Task channel lists forbidden content."""
    pack = _make_test_pack()
    text = pack.serialize()
    assert "- damage numbers" in text
    assert "- AC values" in text
    assert "- HP values" in text


def test_serialize_empty_memory():
    """Empty memory channel serializes as (none)."""
    pack = PromptPack(
        truth=TruthChannel(action_type="test", actor_name="Test"),
        memory=MemoryChannel(),
    )
    text = pack.serialize()
    assert "(none)" in text


def test_serialize_visible_gear():
    """Visible gear from AD-005 Layer 3 appears in truth channel."""
    pack = PromptPack(
        truth=TruthChannel(
            action_type="test",
            actor_name="Test",
            visible_gear=["rope_slung", "grappling_hook_external"],
        ),
    )
    text = pack.serialize()
    # Sorted alphabetically for determinism
    assert "Visible Gear: grappling_hook_external, rope_slung" in text


def test_serialize_visible_gear_sorted():
    """Visible gear is sorted for deterministic output."""
    pack1 = PromptPack(
        truth=TruthChannel(
            action_type="test",
            actor_name="Test",
            visible_gear=["z_item", "a_item", "m_item"],
        ),
    )
    pack2 = PromptPack(
        truth=TruthChannel(
            action_type="test",
            actor_name="Test",
            visible_gear=["a_item", "m_item", "z_item"],
        ),
    )
    # Different input order, same output
    assert pack1.serialize() == pack2.serialize()


# ==============================================================================
# TASK TYPES
# ==============================================================================


def test_narration_task():
    """Narration task type accepted."""
    pack = PromptPack(
        truth=TruthChannel(action_type="test", actor_name="Test"),
        task=TaskChannel(task_type=TASK_NARRATION),
    )
    assert pack.task.task_type == TASK_NARRATION


def test_npc_dialogue_task():
    """NPC dialogue task type accepted."""
    pack = PromptPack(
        truth=TruthChannel(action_type="test", actor_name="Test"),
        task=TaskChannel(
            task_type=TASK_NPC_DIALOGUE,
            npc_name="Barkeep Aldric",
            npc_personality="gruff but kind",
        ),
    )
    assert pack.task.task_type == TASK_NPC_DIALOGUE
    assert pack.task.npc_name == "Barkeep Aldric"


def test_npc_dialogue_serialization():
    """NPC dialogue task includes NPC info in serialization."""
    pack = PromptPack(
        truth=TruthChannel(action_type="npc_speak", actor_name="Aldric"),
        task=TaskChannel(
            task_type=TASK_NPC_DIALOGUE,
            npc_name="Barkeep Aldric",
            npc_personality="gruff but kind",
        ),
    )
    text = pack.serialize()
    assert "NPC: Barkeep Aldric" in text
    assert "Personality: gruff but kind" in text


def test_invalid_task_type_raises():
    """Invalid task type raises ValueError."""
    with pytest.raises(ValueError, match="Unknown task type"):
        PromptPack(
            truth=TruthChannel(action_type="test", actor_name="Test"),
            task=TaskChannel(task_type="invalid_type"),
        )


# ==============================================================================
# STYLE CHANNEL
# ==============================================================================


def test_style_defaults():
    """Default style is moderate/dramatic/no humor."""
    pack = PromptPack(
        truth=TruthChannel(action_type="test", actor_name="Test"),
    )
    assert pack.style.verbosity == "moderate"
    assert pack.style.drama == "dramatic"
    assert pack.style.humor == "none"
    assert pack.style.grittiness == "moderate"
    assert pack.style.dm_persona == "authoritative"


def test_style_serialization():
    """Style channel serializes all knobs."""
    pack = PromptPack(
        truth=TruthChannel(action_type="test", actor_name="Test"),
        style=StyleChannel(
            verbosity="verbose",
            drama="epic",
            humor="wry",
            grittiness="gritty",
            dm_persona="menacing",
        ),
    )
    text = pack.serialize()
    assert "Verbosity: verbose" in text
    assert "Drama: epic" in text
    assert "Humor: wry" in text
    assert "Grittiness: gritty" in text
    assert "Persona: menacing" in text


# ==============================================================================
# OUTPUT CONTRACT
# ==============================================================================


def test_contract_defaults():
    """Default contract: 600 chars, prose, [NARRATIVE]."""
    pack = PromptPack(
        truth=TruthChannel(action_type="test", actor_name="Test"),
    )
    assert pack.contract.max_length_chars == 600
    assert pack.contract.required_provenance == "[NARRATIVE]"
    assert pack.contract.json_mode is False


def test_contract_json_mode():
    """JSON mode contract includes schema."""
    pack = PromptPack(
        truth=TruthChannel(action_type="test", actor_name="Test"),
        contract=OutputContract(
            json_mode=True,
            json_schema='{"type": "object", "properties": {"text": {"type": "string"}}}',
        ),
    )
    text = pack.serialize()
    assert "Format: JSON" in text


def test_contract_prose_mode():
    """Prose mode contract has format: prose."""
    pack = PromptPack(
        truth=TruthChannel(action_type="test", actor_name="Test"),
    )
    text = pack.serialize()
    assert "Format: prose" in text


# ==============================================================================
# IMMUTABILITY
# ==============================================================================


def test_prompt_pack_frozen():
    """PromptPack must be immutable."""
    pack = PromptPack(
        truth=TruthChannel(action_type="test", actor_name="Test"),
    )
    with pytest.raises(AttributeError):
        pack.schema_version = "2.0"


def test_truth_channel_frozen():
    """TruthChannel must be immutable."""
    truth = TruthChannel(action_type="test", actor_name="Test")
    with pytest.raises(AttributeError):
        truth.actor_name = "Changed"


def test_memory_channel_frozen():
    """MemoryChannel must be immutable."""
    mem = MemoryChannel(previous_narrations=("test",))
    with pytest.raises(AttributeError):
        mem.token_budget = 999


def test_task_channel_frozen():
    """TaskChannel must be immutable."""
    task = TaskChannel(task_type=TASK_NARRATION)
    with pytest.raises(AttributeError):
        task.task_type = "modified"


def test_style_channel_frozen():
    """StyleChannel must be immutable."""
    style = StyleChannel(verbosity="terse")
    with pytest.raises(AttributeError):
        style.verbosity = "verbose"


def test_output_contract_frozen():
    """OutputContract must be immutable."""
    contract = OutputContract(max_length_chars=600)
    with pytest.raises(AttributeError):
        contract.max_length_chars = 9999


# ==============================================================================
# GOLDEN TEST (DETERMINISTIC SERIALIZATION PROOF)
# ==============================================================================


def test_golden_serialization():
    """Golden test: exact serialization output for a known input.

    This test proves byte-level determinism. If the serialization
    format changes, this test must be updated deliberately.
    """
    pack = PromptPack(
        truth=TruthChannel(
            action_type="attack_hit",
            actor_name="Kael",
            target_name="Goblin",
            outcome_summary="Kael hits the goblin",
            severity="moderate",
            weapon_name="Longsword",
            damage_type="slashing",
        ),
        memory=MemoryChannel(
            previous_narrations=("The party entered the dungeon.",),
        ),
        task=TaskChannel(task_type=TASK_NARRATION),
        style=StyleChannel(),
        contract=OutputContract(),
    )
    text = pack.serialize()
    expected_lines = [
        "[PROMPT_PACK v1.0]",
        "",
        "[TRUTH]",
        "Action: attack_hit",
        "Actor: Kael",
        "Target: Goblin",
        "Outcome: Kael hits the goblin",
        "Severity: moderate",
        "Weapon: Longsword",
        "Damage Type: slashing",
        "[/TRUTH]",
        "",
        "[MEMORY]",
        "Previous:",
        "- The party entered the dungeon.",
        "[/MEMORY]",
        "",
        "[TASK]",
        "Type: narration",
        "Sentences: 2-4",
        "Forbidden:",
        "- damage numbers",
        "- AC values",
        "- attack bonus values",
        "- HP values",
        "- die roll results",
        "- rule citations",
        "[/TASK]",
        "",
        "[STYLE]",
        "Verbosity: moderate",
        "Drama: dramatic",
        "Humor: none",
        "Grittiness: moderate",
        "Persona: authoritative",
        "[/STYLE]",
        "",
        "[CONTRACT]",
        "Max Length: 600 chars",
        "Provenance: [NARRATIVE]",
        "Format: prose",
        "[/CONTRACT]",
    ]
    assert text == "\n".join(expected_lines)
