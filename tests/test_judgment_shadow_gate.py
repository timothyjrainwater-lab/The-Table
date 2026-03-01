"""Gate tests for WO-JUDGMENT-SHADOW-001 -- Phase 0 Judgment Layer Shadow instrumentation.

JS-001  Unknown command -> route_class "impossible_or_clarify" in shadow log
JS-002  Unknown command -> routing_confidence "escalate" in shadow log
JS-003  Unknown command -> validator_verdict present in shadow log
JS-004  Unknown command -> clarification_message populated in shadow log
JS-005  Unknown command -> _build_clarification_result() still returns correct TurnResult (no regression)
JS-006  validate_ruling_artifact() with dc=3 -> verdict="fail", reason includes "below minimum"
JS-007  validate_ruling_artifact() with dc=45 -> verdict="needs_clarification", reason includes "exceeds maximum"
JS-008  validate_ruling_artifact() with valid artifact -> verdict="pass", reasons=[]
"""

from __future__ import annotations
import json
import os
import dataclasses
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_orchestrator(log_path: str):
    """Build a SessionOrchestrator with a patched log path for isolation."""
    from aidm.runtime.session_orchestrator import SessionOrchestrator
    from aidm.runtime.play_controller import build_simple_combat_fixture
    from aidm.interaction.intent_bridge import IntentBridge
    from aidm.lens.context_assembler import ContextAssembler
    from aidm.lens.scene_manager import SceneManager
    from aidm.narration.guarded_narration_service import GuardedNarrationService
    from aidm.spark.dm_persona import DMPersona

    fixture = build_simple_combat_fixture()
    orch = SessionOrchestrator(
        world_state=fixture.world_state,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes={}),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=fixture.master_seed,
    )

    # Patch _log_shadow_ruling to write to a temp file, not logs/shadow_rulings.jsonl
    def _patched_log(artifact: object) -> None:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(dataclasses.asdict(artifact), sort_keys=True) + "\n")

    orch._log_shadow_ruling = _patched_log
    return orch


def _run_unknown(log_path: str) -> Any:
    """Drive an unknown command through process_text_turn(), capture log entries."""
    orch = _make_minimal_orchestrator(log_path)
    result = orch.process_text_turn("zzz_this_is_not_a_command", "pc_fighter")
    entries = []
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    return result, entries


# ---------------------------------------------------------------------------
# JS-001 -- route_class = "impossible_or_clarify" in shadow log
# ---------------------------------------------------------------------------

def test_JS_001_route_class_impossible_or_clarify():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as tmp:
        log_path = tmp.name
    try:
        _, entries = _run_unknown(log_path)
        assert len(entries) >= 1, "Shadow log must have at least one entry after unknown command"
        assert entries[0]["route_class"] == "impossible_or_clarify", (
            f"route_class must be 'impossible_or_clarify', got {entries[0].get('route_class')!r}"
        )
    finally:
        os.unlink(log_path)


# ---------------------------------------------------------------------------
# JS-002 -- routing_confidence = "escalate" in shadow log
# ---------------------------------------------------------------------------

def test_JS_002_routing_confidence_escalate():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as tmp:
        log_path = tmp.name
    try:
        _, entries = _run_unknown(log_path)
        assert len(entries) >= 1, "Shadow log must have at least one entry"
        assert entries[0]["routing_confidence"] == "escalate", (
            f"routing_confidence must be 'escalate', got {entries[0].get('routing_confidence')!r}"
        )
    finally:
        os.unlink(log_path)


# ---------------------------------------------------------------------------
# JS-003 -- validator_verdict present in shadow log
# ---------------------------------------------------------------------------

def test_JS_003_validator_verdict_present():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as tmp:
        log_path = tmp.name
    try:
        _, entries = _run_unknown(log_path)
        assert len(entries) >= 1, "Shadow log must have at least one entry"
        assert "validator_verdict" in entries[0], "Shadow log entry must have validator_verdict"
        assert entries[0]["validator_verdict"] in ("pass", "fail", "needs_clarification"), (
            f"validator_verdict must be one of pass/fail/needs_clarification, got {entries[0].get('validator_verdict')!r}"
        )
    finally:
        os.unlink(log_path)


# ---------------------------------------------------------------------------
# JS-004 -- clarification_message populated in shadow log
# ---------------------------------------------------------------------------

def test_JS_004_clarification_message_populated():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as tmp:
        log_path = tmp.name
    try:
        _, entries = _run_unknown(log_path)
        assert len(entries) >= 1, "Shadow log must have at least one entry"
        msg = entries[0].get("clarification_message", "")
        assert msg, "clarification_message must be non-empty in shadow log"
        assert "attack" in msg.lower(), (
            f"clarification_message must mention 'attack', got {msg!r}"
        )
    finally:
        os.unlink(log_path)


# ---------------------------------------------------------------------------
# JS-005 -- _build_clarification_result() still returns correct TurnResult (no regression)
# ---------------------------------------------------------------------------

def test_JS_005_build_clarification_result_no_regression():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as tmp:
        log_path = tmp.name
    try:
        result, _ = _run_unknown(log_path)
        # Must still return a TurnResult with clarification_needed=True
        assert result.success is True, f"TurnResult.success must be True after clarification, got {result.success}"
        assert result.clarification_needed is True, (
            f"TurnResult.clarification_needed must be True, got {result.clarification_needed}"
        )
        assert result.clarification_message, "clarification_message must be non-empty in TurnResult"
        assert "attack" in result.clarification_message.lower(), (
            f"clarification_message must mention 'attack', got {result.clarification_message!r}"
        )
        # narration_text should be empty (clarification path)
        assert result.narration_text == "", (
            f"narration_text must be empty for clarification, got {result.narration_text!r}"
        )
    finally:
        os.unlink(log_path)


# ---------------------------------------------------------------------------
# JS-006 -- validate_ruling_artifact() dc=3 -> verdict="fail", below minimum
# ---------------------------------------------------------------------------

def test_JS_006_validate_dc_below_minimum():
    from aidm.core.ruling_validator import validate_ruling_artifact
    from aidm.schemas.ruling_artifact import RulingArtifactShadow

    artifact = RulingArtifactShadow(
        player_action_raw="attempt impossible feat",
        route_class="impossible_or_clarify",
        routing_confidence="escalate",
        dc=3,
    )
    verdict, reasons = validate_ruling_artifact(artifact)
    assert verdict == "fail", f"verdict must be 'fail' for dc=3, got {verdict!r}"
    assert any("below minimum" in r for r in reasons), (
        f"reasons must mention 'below minimum', got {reasons}"
    )


# ---------------------------------------------------------------------------
# JS-007 -- validate_ruling_artifact() dc=45 -> verdict="needs_clarification", exceeds maximum
# ---------------------------------------------------------------------------

def test_JS_007_validate_dc_exceeds_maximum():
    from aidm.core.ruling_validator import validate_ruling_artifact
    from aidm.schemas.ruling_artifact import RulingArtifactShadow

    artifact = RulingArtifactShadow(
        player_action_raw="attempt legendary feat",
        route_class="improvised_synthesis",
        routing_confidence="uncertain",
        dc=45,
    )
    verdict, reasons = validate_ruling_artifact(artifact)
    assert verdict == "needs_clarification", (
        f"verdict must be 'needs_clarification' for dc=45, got {verdict!r}"
    )
    assert any("exceeds maximum" in r for r in reasons), (
        f"reasons must mention 'exceeds maximum', got {reasons}"
    )


# ---------------------------------------------------------------------------
# JS-008 -- validate_ruling_artifact() valid artifact -> verdict="pass", reasons=[]
# ---------------------------------------------------------------------------

def test_JS_008_validate_valid_artifact():
    from aidm.core.ruling_validator import validate_ruling_artifact
    from aidm.schemas.ruling_artifact import RulingArtifactShadow

    artifact = RulingArtifactShadow(
        player_action_raw="attack goblin",
        route_class="named",
        routing_confidence="certain",
        dc=15,
    )
    verdict, reasons = validate_ruling_artifact(artifact)
    assert verdict == "pass", f"verdict must be 'pass' for valid artifact, got {verdict!r}"
    assert reasons == [], f"reasons must be empty list for valid artifact, got {reasons}"
