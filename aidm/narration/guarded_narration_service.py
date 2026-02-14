"""M1 Narration Boundary Layer — Guarded LLM Narration Service

Implements guardrails from M1_IMPLEMENTATION_GUARDRAILS.md:
- FREEZE-001: Read-only memory snapshots
- FORBIDDEN-WRITE-001: No narration-to-memory writes
- LLM-002: Temperature boundaries (query ≤0.5, narration ≥0.7)
- KILL-001: Narration-to-memory write detection
- KILL-002: Mechanical assertion in Spark output
- KILL-003: Token overflow (completion > max_tokens * 1.1)
- KILL-004: Spark latency exceeds 10s
- KILL-005: Consecutive guardrail rejections > 3
- KILL-006: State hash drift post-narration

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
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aidm.narration.kill_switch_registry import (
    KillSwitchID,
    KillSwitchRegistry,
    build_evidence,
    detect_mechanical_assertions,
)
from aidm.narration.narrator import NarrationTemplates, NarrationContext
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

# LLMQueryInterface import (optional, for M3 LLM integration)
try:
    from aidm.narration.llm_query_interface import LLMQueryInterface, WorldStateSummary, CharacterContext
    LLM_QUERY_INTERFACE_AVAILABLE = True
except ImportError:
    LLM_QUERY_INTERFACE_AVAILABLE = False
    LLMQueryInterface = None  # type: ignore
    WorldStateSummary = None  # type: ignore
    CharacterContext = None  # type: ignore
    logger.info("LLMQueryInterface not available, using basic LLM narration")

# PromptPackBuilder import (WO-057, for PromptPack-based prompt assembly)
try:
    from aidm.lens.prompt_pack_builder import PromptPackBuilder
    PROMPT_PACK_BUILDER_AVAILABLE = True
except ImportError:
    PROMPT_PACK_BUILDER_AVAILABLE = False
    PromptPackBuilder = None  # type: ignore
    logger.info("PromptPackBuilder not available, using legacy prompt assembly")

# ContradictionChecker import (WO-058, for post-hoc Spark output validation)
from aidm.narration.contradiction_checker import (
    ContradictionChecker,
    RecommendedAction,
)

# NarrationValidator import (WO-NARRATION-VALIDATOR-001)
from aidm.narration.narration_validator import (
    NarrationValidator,
    ValidationResult as NVValidationResult,
)


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
        world_state_hash: Optional world state hash for KILL-006 drift detection
        narrative_brief: Optional NarrativeBrief for PromptPack path (WO-057).
            When present, LLM prompt is built via PromptPackBuilder instead of
            the legacy _build_llm_prompt() method. When absent, legacy path used.
    """

    engine_result: EngineResult
    memory_snapshot: FrozenMemorySnapshot
    temperature: float = 0.8  # Default narration temperature
    world_state_hash: Optional[str] = None  # For KILL-006
    narrative_brief: Optional[Any] = None  # NarrativeBrief (WO-057, avoids circular import)
    segment_summaries: Optional[Any] = None  # List[SessionSegmentSummary] (WO-060, avoids circular import)

    def __post_init__(self):
        """Validate narration request constraints."""
        # LLM-002: Narration temperature MUST be ≥0.7
        if self.temperature < 0.7:
            raise ValueError(
                f"Narration temperature MUST be ≥0.7 (got {self.temperature}). "
                "Violation: LLM-002 (Temperature Boundaries)"
            )


# ========================================================================
# Narration Result (with Provenance)
# ========================================================================


@dataclass
class NarrationResult:
    """Result of narration generation with provenance tracking.

    Attributes:
        text: The narration text
        provenance: Source tag — "[NARRATIVE]" for LLM, "[NARRATIVE:TEMPLATE]" for template
    """

    text: str
    provenance: str


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
    - KILL-001 through KILL-006: Kill switch suite

    M2 Integration:
    - Supports optional Spark Adapter integration for LLM narration
    - Falls back to template narration if Spark unavailable or model fails
    - All M1 guardrails remain enforced regardless of narration method
    """

    # KILL-004 latency threshold in seconds
    LATENCY_THRESHOLD_S = 10.0

    # KILL-003 token overflow multiplier
    TOKEN_OVERFLOW_MULTIPLIER = 1.1

    # KILL-005 consecutive rejection threshold
    CONSECUTIVE_REJECTION_THRESHOLD = 3

    def __init__(self, loaded_model: Optional[Any] = None, use_llm_query_interface: bool = True,
                 kill_switch_registry: Optional[KillSwitchRegistry] = None,
                 contradiction_checker: Optional[ContradictionChecker] = None,
                 narration_validator: Optional[NarrationValidator] = None,
                 narration_log_path: Optional[str] = None):
        """Initialize guarded narration service.

        Args:
            loaded_model: Optional LoadedModel from Spark Adapter for LLM narration.
                         If None, uses template-based narration (M1 mode).
            use_llm_query_interface: If True and available, use LLMQueryInterface for narration (M3 mode).
            kill_switch_registry: Optional shared KillSwitchRegistry instance.
                                 If None, creates a private instance.
            contradiction_checker: Optional ContradictionChecker for post-hoc
                                  Spark output validation (WO-058). If None,
                                  creates a default instance.
            narration_validator: Optional NarrationValidator for unified
                                 narration validation (WO-NARRATION-VALIDATOR-001).
                                 If None, creates a default instance.
            narration_log_path: Optional path for narration JSONL log
                                (WO-NARRATION-VALIDATOR-001 Change 6). If None,
                                persistence is disabled.
        """
        self.metrics = NarrationMetrics()
        self.kill_switch_registry = kill_switch_registry or KillSwitchRegistry()
        self.contradiction_checker = contradiction_checker or ContradictionChecker()
        self.narration_validator = narration_validator or NarrationValidator()
        self.narration_log_path = narration_log_path
        self.loaded_model = loaded_model if SPARK_AVAILABLE else None

        # Backward compat: shadow property for _kill_switch_active
        # (used by existing tests that call _trigger_kill_switch directly)

        # Initialize LLMQueryInterface if requested and available
        self.llm_query_interface = None
        if use_llm_query_interface and LLM_QUERY_INTERFACE_AVAILABLE and self.loaded_model is not None:
            self.llm_query_interface = LLMQueryInterface(loaded_model=self.loaded_model)
            logger.info("GuardedNarrationService initialized with LLMQueryInterface (M3 mode)")
        elif self.loaded_model is not None:
            logger.info(
                f"GuardedNarrationService initialized with LLM model: "
                f"{self.loaded_model.model_id} (M2 mode)"
            )
        else:
            logger.info("GuardedNarrationService initialized in template mode (M1)")

    def generate_narration(self, request: NarrationRequest) -> NarrationResult:
        """Generate narration with guardrail enforcement.

        Args:
            request: Narration request with frozen memory snapshot

        Returns:
            NarrationResult with text and provenance tag

        Raises:
            NarrationBoundaryViolation: If any guardrail violated
        """
        # Check if ANY kill switch is active (O(1) via registry cache)
        if self.kill_switch_registry.any_triggered():
            active = self.kill_switch_registry.get_all_active()
            ids = ", ".join(sw.value for sw, _ in active)
            logger.error(f"Kill switch(es) ACTIVE ({ids}): Narration generation DISABLED")
            raise NarrationBoundaryViolation(
                f"Narration generation disabled by kill switch ({ids}). "
                "Manual reset required."
            )

        # Store hash before narration (for mutation detection)
        hash_before = request.memory_snapshot.snapshot_hash
        world_hash_before = request.world_state_hash

        logger.info(
            f"Generating narration (temp={request.temperature}, hash={hash_before[:8]})"
        )

        # ── Narration Generation ────────────────────────────────────
        # Try LLM narration if model loaded, otherwise use template
        provenance = "[NARRATIVE:TEMPLATE]"
        llm_narration_text = None
        llm_tokens_used = 0
        llm_max_tokens = 150  # default
        # WO-NARRATION-VALIDATOR-001: Track validation result for persistence
        validation_result = None

        if self.loaded_model is not None and self.loaded_model.model_id != "template-narration":
            try:
                t0 = time.monotonic()
                llm_narration_text, llm_tokens_used, llm_max_tokens = self._generate_llm_narration_with_meta(request)
                elapsed = time.monotonic() - t0

                # ── KILL-004: Latency check ──────────────────────────
                if elapsed > self.LATENCY_THRESHOLD_S:
                    ev = build_evidence(
                        KillSwitchID.KILL_004,
                        f"Spark latency {elapsed*1000:.0f}ms exceeds {self.LATENCY_THRESHOLD_S*1000:.0f}ms threshold",
                        {"elapsed_ms": round(elapsed * 1000), "max_allowed_ms": round(self.LATENCY_THRESHOLD_S * 1000)},
                    )
                    self.kill_switch_registry.trigger(KillSwitchID.KILL_004, ev)
                    self.kill_switch_registry.record_rejection(KillSwitchID.KILL_004)
                    self._check_kill005()
                    # Fall back to template
                    llm_narration_text = None

                # ── KILL-003: Token overflow check ───────────────────
                if llm_narration_text is not None and llm_tokens_used > llm_max_tokens * self.TOKEN_OVERFLOW_MULTIPLIER:
                    ev = build_evidence(
                        KillSwitchID.KILL_003,
                        f"Token overflow: {llm_tokens_used} > {llm_max_tokens} * {self.TOKEN_OVERFLOW_MULTIPLIER}",
                        {"max_tokens": llm_max_tokens, "tokens_used": llm_tokens_used,
                         "overflow_ratio": round(llm_tokens_used / llm_max_tokens, 2)},
                    )
                    self.kill_switch_registry.trigger(KillSwitchID.KILL_003, ev)
                    self.kill_switch_registry.record_rejection(KillSwitchID.KILL_003)
                    self._check_kill005()
                    llm_narration_text = None

                # ── KILL-002: Mechanical assertion check ─────────────
                if llm_narration_text is not None:
                    mech = detect_mechanical_assertions(llm_narration_text)
                    if mech is not None:
                        pattern_name, matched_text = mech
                        ev = build_evidence(
                            KillSwitchID.KILL_002,
                            f"Mechanical assertion detected: {pattern_name}",
                            {"pattern": pattern_name, "matched_text": matched_text,
                             "full_narration": llm_narration_text},
                        )
                        self.kill_switch_registry.trigger(KillSwitchID.KILL_002, ev)
                        self.kill_switch_registry.record_rejection(KillSwitchID.KILL_002)
                        self._check_kill005()
                        llm_narration_text = None

                # ── WO-058: Contradiction check ─────────────────────
                if llm_narration_text is not None and request.narrative_brief is not None:
                    contradiction_result = self.contradiction_checker.check(
                        llm_narration_text, request.narrative_brief,
                    )
                    if contradiction_result.has_contradiction:
                        action = contradiction_result.recommended_action
                        logger.warning(
                            f"Contradiction detected: {len(contradiction_result.matches)} match(es), "
                            f"action={action.value}"
                        )
                        if action == RecommendedAction.RETRY:
                            # Retry with correction appended to prompt
                            retry_text = self._retry_with_correction(
                                request, contradiction_result,
                            )
                            if retry_text is not None:
                                llm_narration_text = retry_text
                            else:
                                llm_narration_text = None  # Retry failed, fall back to template
                        elif action == RecommendedAction.TEMPLATE_FALLBACK:
                            llm_narration_text = None  # Fall back to template
                        # ANNOTATE: keep the text but log (Class C, first occurrence)

                # ── WO-NARRATION-VALIDATOR-001: Unified validation ────
                if llm_narration_text is not None and request.narrative_brief is not None:
                    validation_result = self.narration_validator.validate(
                        llm_narration_text, request.narrative_brief,
                    )
                    if validation_result.verdict == "FAIL":
                        logger.warning(
                            f"NarrationValidator FAIL: {len(validation_result.violations)} violation(s) — "
                            + ", ".join(v.rule_id for v in validation_result.violations)
                        )
                        llm_narration_text = None  # Template fallback
                    elif validation_result.verdict == "WARN":
                        logger.info(
                            f"NarrationValidator WARN: {len(validation_result.violations)} violation(s) — "
                            + ", ".join(v.rule_id for v in validation_result.violations)
                        )
                        # Emit text but log for post-session review

            except Exception as e:
                logger.warning(f"LLM narration failed, falling back to template: {e}")
                llm_narration_text = None

        # Determine final narration text
        if llm_narration_text is not None:
            narration_text = llm_narration_text
            provenance = "[NARRATIVE]"
            # Successful generation resets consecutive rejection counter
            self.kill_switch_registry.reset_rejection_counter()
        else:
            narration_text = self._generate_template_narration(request.engine_result)

        # ── Guardrail Enforcement ───────────────────────────────────

        # FREEZE-001 / KILL-001: Verify memory snapshot unchanged
        hash_after = request.memory_snapshot.snapshot_hash
        if hash_before != hash_after:
            self.metrics.hash_mismatches += 1
            ev = build_evidence(
                KillSwitchID.KILL_001,
                f"Memory hash mismatch detected (before={hash_before[:8]}, after={hash_after[:8]})",
                {"hash_before": hash_before, "hash_after": hash_after},
            )
            self.kill_switch_registry.trigger(KillSwitchID.KILL_001, ev)
            self.metrics.write_violations += 1
            self.kill_switch_registry.record_rejection(KillSwitchID.KILL_001)
            self._check_kill005()
            raise NarrationBoundaryViolation(
                "FREEZE-001 VIOLATION: Memory snapshot mutated during narration. "
                f"Hash before: {hash_before[:8]}, Hash after: {hash_after[:8]}"
            )

        # KILL-006: State hash drift (broader than KILL-001)
        if world_hash_before is not None:
            # Caller must provide a way to re-compute the hash post-narration.
            # Since we can't access world state directly (BL-003), we compare
            # the hash stored in the request. If the request's world_state_hash
            # has been modified between construction and now, drift is detected.
            # In practice, the caller re-computes and passes it via a callback
            # or the request is validated externally. Here we store the "before"
            # and the caller can call check_world_state_drift() after.
            pass  # Drift check happens via check_world_state_drift() method

        logger.info(f"Narration generated successfully (hash verified: {hash_after[:8]})")

        # ── WO-NARRATION-VALIDATOR-001 Change 6: Narration Persistence ──
        self._persist_narration_log(
            narration_text=narration_text,
            brief=request.narrative_brief,
            validation_result=validation_result,
        )

        return NarrationResult(text=narration_text, provenance=provenance)

    def check_world_state_drift(self, hash_before: str, hash_after: str) -> bool:
        """Check for world state hash drift (KILL-006).

        Call this after narration if the caller has access to world state hashes.

        Args:
            hash_before: World state hash before narration
            hash_after: World state hash after narration

        Returns:
            True if drift detected (kill switch triggered)
        """
        if hash_before != hash_after:
            ev = build_evidence(
                KillSwitchID.KILL_006,
                f"World state hash drift detected (before={hash_before[:8]}, after={hash_after[:8]})",
                {"hash_before": hash_before, "hash_after": hash_after, "snapshot_type": "world_state"},
            )
            self.kill_switch_registry.trigger(KillSwitchID.KILL_006, ev)
            self.kill_switch_registry.record_rejection(KillSwitchID.KILL_006)
            self._check_kill005()
            return True
        return False

    def _persist_narration_log(
        self,
        narration_text: str,
        brief: Optional[Any],
        validation_result: Optional[NVValidationResult],
    ) -> None:
        """Persist narration text + validation result to session JSONL.

        WO-NARRATION-VALIDATOR-001 Change 6: Writes one JSON line per narration
        pass to enable post-session narration quality analysis.

        Args:
            narration_text: Final narration text (LLM or template)
            brief: NarrativeBrief (may be None for template-only paths)
            validation_result: ValidationResult from NarrationValidator (may be None)
        """
        if self.narration_log_path is None:
            return

        source_event_ids = ()
        if brief is not None:
            source_event_ids = getattr(brief, "source_event_ids", ())

        verdict = "PASS"
        violations: List[dict] = []
        if validation_result is not None:
            verdict = validation_result.verdict
            violations = [
                {"rule_id": v.rule_id, "severity": v.severity, "detail": v.detail}
                for v in validation_result.violations
            ]

        entry = {
            "narration_text": narration_text,
            "source_event_ids": list(source_event_ids),
            "validation_verdict": verdict,
            "violations": violations,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with open(self.narration_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning(f"Failed to persist narration log: {e}")

    def _check_kill005(self) -> None:
        """Check if KILL-005 (consecutive rejections) should fire."""
        if self.kill_switch_registry.consecutive_rejections >= self.CONSECUTIVE_REJECTION_THRESHOLD:
            if not self.kill_switch_registry.is_triggered(KillSwitchID.KILL_005):
                ev = build_evidence(
                    KillSwitchID.KILL_005,
                    f"Consecutive guardrail rejections: {self.kill_switch_registry.consecutive_rejections}",
                    {"rejection_count": self.kill_switch_registry.consecutive_rejections,
                     "rejection_types": self.kill_switch_registry.rejection_types},
                )
                self.kill_switch_registry.trigger(KillSwitchID.KILL_005, ev)

    def _retry_with_correction(
        self, request: NarrationRequest, contradiction_result: Any,
    ) -> Optional[str]:
        """Retry LLM narration with contradiction correction appended to prompt.

        WO-058: When a contradiction is detected and response policy says "retry",
        regenerate with a correction prompt that explicitly tells Spark what it
        got wrong.

        Args:
            request: Original NarrationRequest
            contradiction_result: ContradictionResult from failed check

        Returns:
            Corrected narration text if retry succeeds, None if retry also fails
        """
        if self.loaded_model is None or self.loaded_model.inference_engine is None:
            return None

        correction = self.contradiction_checker.build_retry_correction(
            contradiction_result, request.narrative_brief,
        )

        # Build prompt with correction appended
        prompt = self._build_llm_prompt(request)
        if request.narrative_brief is not None and PROMPT_PACK_BUILDER_AVAILABLE:
            prompt = self._build_prompt_pack(request)
        prompt = prompt + "\n\n" + correction

        presets = self.loaded_model.profile.presets.get('narration', {})
        temperature = min(request.temperature + 0.1, 2.0)  # Bump temp slightly
        max_tokens = presets.get('max_tokens', 150)
        stop_sequences = presets.get('stop_sequences', [])

        try:
            output = self.loaded_model.inference_engine(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop_sequences,
                echo=False,
            )

            if isinstance(output, dict) and 'choices' in output:
                text = output['choices'][0]['text'].strip()
            else:
                text = str(output).strip()

            # Check retry output for mechanical assertions
            mech = detect_mechanical_assertions(text)
            if mech is not None:
                return None

            # Check retry output for contradictions
            retry_result = self.contradiction_checker.check(
                text, request.narrative_brief,
            )
            if retry_result.has_contradiction:
                return None  # Retry also contradicted — caller falls back to template

            return text

        except Exception as e:
            logger.warning(f"Contradiction retry failed: {e}")
            return None

    def _generate_llm_narration_with_meta(self, request: NarrationRequest):
        """Generate narration using LLM and return metadata for kill switch checks.

        Returns:
            Tuple of (narration_text, tokens_used, max_tokens)
        """
        # M3 mode: Use LLMQueryInterface if available
        if self.llm_query_interface is not None:
            try:
                world_state = self._build_world_state_summary(request)
                player_action = self._extract_player_action(request.engine_result)
                text = self.llm_query_interface.generate_narration(
                    player_action=player_action,
                    world_state_summary=world_state,
                    character_context=None,
                    temperature=request.temperature,
                    narration_type="combat",
                )
                return (text, 0, 150)  # No token info from M3 interface
            except Exception as e:
                logger.warning(f"LLMQueryInterface narration failed, falling back to basic mode: {e}")

        # M2 mode: Use basic Spark model interface
        if not SPARK_AVAILABLE:
            raise RuntimeError("Spark Adapter not available")

        if self.loaded_model is None or self.loaded_model.inference_engine is None:
            raise RuntimeError("No LLM model loaded")

        prompt = self._build_llm_prompt(request)
        # WO-057: Use PromptPack path when narrative_brief is present
        if request.narrative_brief is not None and PROMPT_PACK_BUILDER_AVAILABLE:
            prompt = self._build_prompt_pack(request)
        presets = self.loaded_model.profile.presets.get('narration', {})
        temperature = request.temperature
        max_tokens = presets.get('max_tokens', 150)
        stop_sequences = presets.get('stop_sequences', [])

        logger.debug(f"Generating LLM narration (temp={temperature}, max_tokens={max_tokens})")

        output = self.loaded_model.inference_engine(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop_sequences,
            echo=False,
        )

        # Extract text
        if isinstance(output, dict) and 'choices' in output:
            text = output['choices'][0]['text']
        else:
            text = str(output)

        # Extract token usage
        tokens_used = 0
        if isinstance(output, dict) and 'usage' in output:
            tokens_used = output['usage'].get('completion_tokens', 0)

        return (text.strip(), tokens_used, max_tokens)

    def _generate_llm_narration(self, request: NarrationRequest) -> str:
        """Generate narration using LLM (Spark Adapter or LLMQueryInterface).

        This method uses either the LLMQueryInterface (M3) if available,
        or falls back to the basic Spark model interface (M2).

        Args:
            request: Narration request with frozen memory snapshot

        Returns:
            LLM-generated narration text

        Raises:
            Exception: If LLM generation fails
        """
        # M3 mode: Use LLMQueryInterface if available
        if self.llm_query_interface is not None:
            try:
                # Build world state summary from memory snapshot
                world_state = self._build_world_state_summary(request)

                # Extract player action from engine result
                player_action = self._extract_player_action(request.engine_result)

                # Generate narration via LLMQueryInterface
                return self.llm_query_interface.generate_narration(
                    player_action=player_action,
                    world_state_summary=world_state,
                    character_context=None,  # TODO: Extract from memory snapshot
                    temperature=request.temperature,
                    narration_type="combat",  # TODO: Derive from engine result
                )
            except Exception as e:
                logger.warning(f"LLMQueryInterface narration failed, falling back to basic mode: {e}")
                # Fall through to M2 mode

        # M2 mode: Use basic Spark model interface
        if not SPARK_AVAILABLE:
            raise RuntimeError("Spark Adapter not available")

        if self.loaded_model is None or self.loaded_model.inference_engine is None:
            raise RuntimeError("No LLM model loaded")

        # Build prompt from engine result and memory snapshot
        prompt = self._build_llm_prompt(request)
        # WO-057: Use PromptPack path when narrative_brief is present
        if request.narrative_brief is not None and PROMPT_PACK_BUILDER_AVAILABLE:
            prompt = self._build_prompt_pack(request)

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

    def _build_world_state_summary(self, request: NarrationRequest) -> Any:
        """Build WorldStateSummary from memory snapshot.

        Args:
            request: Narration request

        Returns:
            WorldStateSummary object
        """
        if not LLM_QUERY_INTERFACE_AVAILABLE:
            return None

        # Parse memory snapshot
        session_data = json.loads(request.memory_snapshot.session_ledger_json)
        session_facts = session_data.get('facts_added', [])

        # Build world state summary
        return WorldStateSummary(
            active_npcs=[],  # TODO: Extract from world state
            player_location="",  # TODO: Extract from world state
            active_threads=[],  # TODO: Extract from thread registry
            recent_events=session_facts[-3:] if session_facts else [],
        )

    def _extract_player_action(self, engine_result: EngineResult) -> str:
        """Extract player action description from engine result.

        Args:
            engine_result: Engine result to extract from

        Returns:
            Player action description
        """
        token = engine_result.narration_token or "action"

        if engine_result.events:
            event_summary = "; ".join(str(e) for e in engine_result.events[:2])
            return f"{token}: {event_summary}"

        return token

    def _build_llm_prompt(self, request: NarrationRequest) -> str:
        """Build LLM prompt from narration request (LEGACY — deprecated by WO-057).

        Constructs a prompt that includes:
        - Engine result (narration token, events)
        - Relevant memory context (session facts, evidence)
        - Instruction for D&D 3.5e-style narration

        DEPRECATED: Use _build_prompt_pack() when narrative_brief is available.
        This method is preserved for backward compatibility during the transition
        period. When narrative_brief is absent in NarrationRequest, this path
        is still used as the fallback.

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

    def _build_prompt_pack(self, request: NarrationRequest) -> str:
        """Build prompt via PromptPack from narrative_brief (WO-057).

        This is the canonical prompt assembly path (GAP-007 resolution).
        All five PromptPack channels are populated from the NarrativeBrief
        and session context. The serialized PromptPack text replaces the
        ad-hoc string assembly of _build_llm_prompt().

        Args:
            request: NarrationRequest with narrative_brief set

        Returns:
            PromptPack.serialize() output — deterministic prompt string
        """
        brief = request.narrative_brief

        # Extract session facts from frozen memory snapshot
        session_data = json.loads(request.memory_snapshot.session_ledger_json)
        session_facts = session_data.get('facts_added', [])

        # WO-060: Extract summary texts from segment summaries if available
        summary_texts = []
        if request.segment_summaries:
            for s in request.segment_summaries:
                text = getattr(s, 'summary_text', str(s))
                summary_texts.append(text)

        builder = PromptPackBuilder()
        pack = builder.build(
            brief=brief,
            session_facts=session_facts,
            segment_summaries=summary_texts if summary_texts else None,
        )

        return pack.serialize()

    def _generate_template_narration(self, engine_result: EngineResult) -> str:
        """Generate narration from template (fallback path).

        Delegates to NarrationTemplates from narrator.py for the full
        55-template dictionary with placeholder substitution.

        Args:
            engine_result: Engine result to narrate

        Returns:
            Template-based narration text with placeholders filled
        """
        token = engine_result.narration_token or "unknown"

        # WO-049: Extract severity from metadata for branched template selection
        severity = ""
        if engine_result.metadata:
            severity = engine_result.metadata.get("severity", "")

        # Look up template from the full 55-entry dictionary
        # Severity-branched templates checked first for combat tokens (WO-049)
        template = NarrationTemplates.get_template(token, severity=severity)

        # Extract context from engine result events
        context = NarrationContext.from_engine_result(engine_result)

        # WO-030: Extract entity names from metadata if present
        actor_name = context.actor_name or "someone"
        target_name = context.target_name or "someone"
        weapon_name = context.weapon_name or "an attack"

        if engine_result.metadata:
            # Override with metadata names if available (from WO-030 pipeline)
            actor_name = engine_result.metadata.get("actor_name", actor_name)
            target_name = engine_result.metadata.get("target_name", target_name)
            weapon_name = engine_result.metadata.get("weapon_name", weapon_name)

        # Extract damage from events if present
        damage = "some damage"
        for event in engine_result.events:
            event_type = event.get("type") or event.get("event_type")

            if event_type == "damage_dealt":
                damage = str(event.get("damage", "some damage"))
                break
            # WO-030: Also check hp_changed events from play_loop
            if event_type == "hp_changed":
                payload = event.get("payload", event)  # Handle both dict and Event objects
                delta = payload.get("delta", 0)
                if delta < 0:
                    damage = str(abs(delta))
                    break

        # WO-048: Also check metadata for damage (from orchestrator template context)
        if damage == "some damage" and engine_result.metadata:
            meta_damage = engine_result.metadata.get("damage", "")
            if meta_damage:
                damage = meta_damage

        # Build substitution map with safe defaults for missing keys
        safe_defaults = defaultdict(
            lambda: "something",
            {
                "actor": actor_name,
                "target": target_name,
                "weapon": weapon_name,
                "damage": damage,
            },
        )

        # Substitute placeholders — never crash on missing data
        return template.format_map(safe_defaults)

    def _trigger_kill_switch(self, reason: str) -> None:
        """Trigger KILL-001 kill switch (backward compat wrapper).

        Args:
            reason: Reason for kill switch activation
        """
        ev = build_evidence(
            KillSwitchID.KILL_001,
            reason,
            {"reason": reason},
        )
        self.kill_switch_registry.trigger(KillSwitchID.KILL_001, ev)
        self.metrics.write_violations += 1
        logger.critical(f"KILL-001 TRIGGERED: {reason}")
        logger.critical("Narration generation DISABLED until manual reset")

    def reset_kill_switch(self, switch_id: Optional[KillSwitchID] = None) -> None:
        """Reset kill switch (manual intervention required).

        This should only be called after:
        1. Root cause identified and fixed
        2. Guardrails re-verified
        3. Agent D approval obtained

        Args:
            switch_id: Specific switch to reset. If None, resets KILL-001 (backward compat).
        """
        target = switch_id or KillSwitchID.KILL_001
        logger.warning(f"{target.value} manually reset (requires Agent D approval)")
        self.kill_switch_registry.reset(target)

    def is_kill_switch_active(self) -> bool:
        """Check if any kill switch is active."""
        return self.kill_switch_registry.any_triggered()

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
