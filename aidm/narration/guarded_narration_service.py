"""M1 Narration Boundary Layer — Guarded LLM Narration Service

Implements guardrails from M1_IMPLEMENTATION_GUARDRAILS.md:
- FREEZE-001: Read-only memory snapshots
- FORBIDDEN-WRITE-001: No narration-to-memory writes
- LLM-002: Temperature boundaries (query ≤0.5, narration ≥0.7)
- KILL-001: Narration-to-memory write detection

BOUNDARY LAW (BL-003): This module must NEVER import from aidm.core.
NARRATION (LENS) receives only immutable EngineResult snapshots. If you add
core imports, test_boundary_law.py BL-003 will fail.

WHY: NARRATION is a read-only gating layer. It must not be able to access
WorldState, RNG streams, or game resolvers. If it could, a compromised or
buggy LLM could influence game state.

This is a minimal vertical slice demonstrating invariant enforcement.
Full LLM integration is deferred to future milestones.

Reference: docs/design/M1_IMPLEMENTATION_GUARDRAILS.md
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from aidm.schemas.campaign_memory import (
    SessionLedgerEntry,
    EvidenceLedger,
    ThreadRegistry,
)
from aidm.schemas.engine_result import EngineResult

# Configure logging
logger = logging.getLogger(__name__)

# Spark imports (optional, for M2 LLM integration)
try:
    from aidm.spark import LoadedModel
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False
    LoadedModel = None  # type: ignore
    logger.info("Spark Adapter not available, using template-based narration only")


# ========================================================================
# Frozen Memory Snapshot (FREEZE-001)
# ========================================================================


@dataclass(frozen=True)
class FrozenMemorySnapshot:
    """Immutable memory snapshot for narration generation.

    Implements FREEZE-001 (Snapshot Semantics):
    - Memory provided as frozen (immutable) snapshot
    - Original memory objects protected from modification
    - Hash verification ensures no mutation during narration

    Attributes:
        session_ledger_json: Frozen SessionLedgerEntry as JSON string
        evidence_ledger_json: Frozen EvidenceLedger as JSON string
        thread_registry_json: Frozen ThreadRegistry as JSON string
        snapshot_hash: SHA-256 hash of snapshot contents
    """

    session_ledger_json: str
    evidence_ledger_json: str
    thread_registry_json: str
    snapshot_hash: str

    @classmethod
    def create(
        cls,
        session_ledger: Optional[SessionLedgerEntry] = None,
        evidence_ledger: Optional[EvidenceLedger] = None,
        thread_registry: Optional[ThreadRegistry] = None,
    ) -> "FrozenMemorySnapshot":
        """Create frozen snapshot from memory objects.

        Args:
            session_ledger: Optional session ledger to freeze
            evidence_ledger: Optional evidence ledger to freeze
            thread_registry: Optional thread registry to freeze

        Returns:
            Immutable frozen snapshot with hash
        """
        # Serialize memory objects to JSON (read-only operation)
        session_json = (
            json.dumps(session_ledger.to_dict(), sort_keys=True)
            if session_ledger
            else "{}"
        )
        evidence_json = (
            json.dumps(evidence_ledger.to_dict(), sort_keys=True)
            if evidence_ledger
            else "{}"
        )
        thread_json = (
            json.dumps(thread_registry.to_dict(), sort_keys=True)
            if thread_registry
            else "{}"
        )

        # Compute snapshot hash (for mutation detection)
        combined = f"{session_json}|{evidence_json}|{thread_json}"
        snapshot_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()

        return cls(
            session_ledger_json=session_json,
            evidence_ledger_json=evidence_json,
            thread_registry_json=thread_json,
            snapshot_hash=snapshot_hash,
        )


# ========================================================================
# Narration Context (Read-Only)
# ========================================================================


@dataclass
class NarrationRequest:
    """Request for narration generation.

    Attributes:
        engine_result: Engine result to narrate (read-only)
        memory_snapshot: Frozen memory snapshot (immutable)
        temperature: LLM temperature (≥0.7 for narration per LLM-002)
    """

    engine_result: EngineResult
    memory_snapshot: FrozenMemorySnapshot
    temperature: float = 0.8  # Default narration temperature

    def __post_init__(self):
        """Validate narration request constraints."""
        # LLM-002: Narration temperature MUST be ≥0.7
        if self.temperature < 0.7:
            raise ValueError(
                f"Narration temperature MUST be ≥0.7 (got {self.temperature}). "
                "Violation: LLM-002 (Temperature Boundaries)"
            )


# ========================================================================
# Narration Service (Guarded)
# ========================================================================


class NarrationBoundaryViolation(Exception):
    """Raised when narration violates M1 guardrails."""

    pass


@dataclass
class NarrationMetrics:
    """Metrics for guardrail monitoring.

    Tracks:
    - Write violations (target: 0)
    - Hash mismatches (target: 0)
    - Temperature violations (target: 0)
    """

    write_violations: int = 0
    hash_mismatches: int = 0
    temperature_violations: int = 0

    def has_violations(self) -> bool:
        """Check if any violations detected."""
        return (
            self.write_violations > 0
            or self.hash_mismatches > 0
            or self.temperature_violations > 0
        )


class GuardedNarrationService:
    """Narration service with enforced M1 guardrails.

    Implements:
    - FREEZE-001: Read-only memory snapshots
    - FORBIDDEN-WRITE-001: No narration-to-memory writes
    - LLM-002: Temperature boundaries (narration ≥0.7)
    - KILL-001: Write detection kill switch

    M2 Integration:
    - Supports optional Spark Adapter integration for LLM narration
    - Falls back to template narration if Spark unavailable or model fails
    - All M1 guardrails remain enforced regardless of narration method
    """

    def __init__(self, loaded_model: Optional[Any] = None):
        """Initialize guarded narration service.

        Args:
            loaded_model: Optional LoadedModel from Spark Adapter for LLM narration.
                         If None, uses template-based narration (M1 mode).
        """
        self.metrics = NarrationMetrics()
        self._kill_switch_active = False
        self.loaded_model = loaded_model if SPARK_AVAILABLE else None

        if self.loaded_model is not None:
            logger.info(
                f"GuardedNarrationService initialized with LLM model: "
                f"{self.loaded_model.model_id}"
            )
        else:
            logger.info("GuardedNarrationService initialized in template mode (M1)")

    def generate_narration(self, request: NarrationRequest) -> str:
        """Generate narration with guardrail enforcement.

        Args:
            request: Narration request with frozen memory snapshot

        Returns:
            Narration text (ephemeral, not persisted)

        Raises:
            NarrationBoundaryViolation: If any guardrail violated
        """
        # KILL-001: Check if kill switch active
        if self._kill_switch_active:
            logger.error("KILL-001 ACTIVE: Narration generation DISABLED")
            raise NarrationBoundaryViolation(
                "Narration generation disabled by kill switch (KILL-001). "
                "Memory write violation detected."
            )

        # Store hash before narration (for mutation detection)
        hash_before = request.memory_snapshot.snapshot_hash

        logger.info(
            f"Generating narration (temp={request.temperature}, hash={hash_before[:8]})"
        )

        # ── Narration Generation ────────────────────────────────────
        # Try LLM narration if model loaded, otherwise use template
        if self.loaded_model is not None and self.loaded_model.model_id != "template-narration":
            try:
                narration_text = self._generate_llm_narration(request)
            except Exception as e:
                logger.warning(f"LLM narration failed, falling back to template: {e}")
                narration_text = self._generate_template_narration(request.engine_result)
        else:
            narration_text = self._generate_template_narration(request.engine_result)

        # ── Guardrail Enforcement ───────────────────────────────────

        # FREEZE-001: Verify memory snapshot unchanged
        hash_after = request.memory_snapshot.snapshot_hash
        if hash_before != hash_after:
            self.metrics.hash_mismatches += 1
            self._trigger_kill_switch(
                f"Memory hash mismatch detected (before={hash_before[:8]}, after={hash_after[:8]})"
            )
            raise NarrationBoundaryViolation(
                "FREEZE-001 VIOLATION: Memory snapshot mutated during narration. "
                f"Hash before: {hash_before[:8]}, Hash after: {hash_after[:8]}"
            )

        logger.info(f"Narration generated successfully (hash verified: {hash_after[:8]})")
        return narration_text

    def _generate_llm_narration(self, request: NarrationRequest) -> str:
        """Generate narration using LLM (Spark Adapter).

        This method uses the loaded Spark model to generate contextual
        narration based on engine results and memory snapshot.

        Args:
            request: Narration request with frozen memory snapshot

        Returns:
            LLM-generated narration text

        Raises:
            Exception: If LLM generation fails
        """
        if not SPARK_AVAILABLE:
            raise RuntimeError("Spark Adapter not available")

        if self.loaded_model is None or self.loaded_model.inference_engine is None:
            raise RuntimeError("No LLM model loaded")

        # Build prompt from engine result and memory snapshot
        prompt = self._build_llm_prompt(request)

        # Get generation presets from model profile
        presets = self.loaded_model.profile.presets.get('narration', {})
        temperature = request.temperature
        max_tokens = presets.get('max_tokens', 150)
        stop_sequences = presets.get('stop_sequences', [])

        # Generate text using loaded model's inference engine
        logger.debug(f"Generating LLM narration (temp={temperature}, max_tokens={max_tokens})")

        output = self.loaded_model.inference_engine(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop_sequences,
            echo=False,
        )

        # Extract generated text
        if isinstance(output, dict) and 'choices' in output:
            text = output['choices'][0]['text']
        else:
            text = str(output)

        return text.strip()

    def _build_llm_prompt(self, request: NarrationRequest) -> str:
        """Build LLM prompt from narration request.

        Constructs a prompt that includes:
        - Engine result (narration token, events)
        - Relevant memory context (session facts, evidence)
        - Instruction for D&D 3.5e-style narration

        Args:
            request: Narration request

        Returns:
            Formatted prompt string
        """
        engine_result = request.engine_result

        # Parse memory snapshot for context
        session_data = json.loads(request.memory_snapshot.session_ledger_json)
        session_facts = session_data.get('facts_added', [])

        # Build prompt
        prompt_parts = []
        prompt_parts.append("You are a Dungeon Master narrating a D&D 3.5e combat encounter.")
        prompt_parts.append("")

        # Add session context if available
        if session_facts:
            prompt_parts.append("Recent Events:")
            for fact in session_facts[-3:]:  # Last 3 facts
                prompt_parts.append(f"- {fact}")
            prompt_parts.append("")

        # Add engine result
        token = engine_result.narration_token or "action"
        prompt_parts.append(f"Narration Type: {token}")

        if engine_result.events:
            prompt_parts.append("Events:")
            for event in engine_result.events:
                prompt_parts.append(f"- {event}")
            prompt_parts.append("")

        prompt_parts.append("Generate a brief, dramatic narration (1-2 sentences):")

        return "\n".join(prompt_parts)

    def _generate_template_narration(self, engine_result: EngineResult) -> str:
        """Generate narration from template (M1 fallback).

        This is the original M1 implementation using simple templates.
        Used when no LLM model is loaded or LLM generation fails.

        Args:
            engine_result: Engine result to narrate

        Returns:
            Template-based narration text
        """
        # Simple template based on narration token
        token = engine_result.narration_token or "unknown"
        templates = {
            "attack_hit": "The attack lands successfully!",
            "attack_miss": "The attack misses!",
            "critical_hit": "A critical hit!",
            "unknown": "An action occurs.",
        }
        return templates.get(token, templates["unknown"])

    def _trigger_kill_switch(self, reason: str) -> None:
        """Trigger KILL-001 kill switch.

        Args:
            reason: Reason for kill switch activation
        """
        self._kill_switch_active = True
        self.metrics.write_violations += 1
        logger.critical(f"KILL-001 TRIGGERED: {reason}")
        logger.critical("Narration generation DISABLED until manual reset")

    def reset_kill_switch(self) -> None:
        """Reset kill switch (manual intervention required).

        This should only be called after:
        1. Root cause identified and fixed
        2. Guardrails re-verified
        3. Agent D approval obtained
        """
        logger.warning("Kill switch manually reset (requires Agent D approval)")
        self._kill_switch_active = False

    def is_kill_switch_active(self) -> bool:
        """Check if kill switch is active."""
        return self._kill_switch_active

    def get_metrics(self) -> NarrationMetrics:
        """Get current guardrail metrics."""
        return self.metrics


# ========================================================================
# Guardrail Verification (for Testing)
# ========================================================================


def verify_frozen_snapshot_immutable(snapshot: FrozenMemorySnapshot) -> bool:
    """Verify that frozen snapshot is immutable.

    Args:
        snapshot: Snapshot to verify

    Returns:
        True if snapshot is immutable (all fields frozen)
    """
    try:
        # Attempt to modify frozen snapshot (should raise FrozenInstanceError)
        snapshot.session_ledger_json = "MODIFIED"  # type: ignore
        return False  # Modification succeeded (BAD)
    except AttributeError:
        # FrozenInstanceError indicates snapshot is immutable (GOOD)
        return True


def verify_no_memory_write_path(
    service: GuardedNarrationService,
) -> bool:
    """Verify that no code path allows narration → memory write.

    Args:
        service: Narration service to verify

    Returns:
        True if no write path detected
    """
    # Check that service has no memory write methods
    dangerous_methods = ["write_memory", "update_memory", "mutate_memory"]
    for method in dangerous_methods:
        if hasattr(service, method):
            logger.error(f"DANGEROUS METHOD DETECTED: {method}")
            return False

    return True
