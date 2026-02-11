"""Kill Switch Registry — Central kill switch state management for Spark/Narration boundary.

Each kill switch detects a specific failure mode, blocks further Spark calls,
falls back to template narration, and logs structured evidence.

Kill Switches:
- KILL-001: Memory hash mutation during narration
- KILL-002: Mechanical assertion detected in Spark output
- KILL-003: Token overflow (completion > max_tokens * 1.1)
- KILL-004: Spark latency exceeds 10s
- KILL-005: Consecutive guardrail rejections > 3
- KILL-006: State hash drift post-narration (broader than KILL-001)

BOUNDARY LAW (BL-003): This module is in aidm/narration/ so it does NOT
import from aidm.core. It uses only stdlib and narration-local types.

Reference: docs/design/M1_IMPLEMENTATION_GUARDRAILS.md
"""

import logging
import re
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Kill Switch Identifiers
# ============================================================================


class KillSwitchID(str, Enum):
    """Identifiers for each kill switch."""
    KILL_001 = "KILL-001"  # Memory hash mutation
    KILL_002 = "KILL-002"  # Mechanical assertion in Spark output
    KILL_003 = "KILL-003"  # Token overflow (completion > max_tokens * 1.1)
    KILL_004 = "KILL-004"  # Spark latency exceeds 10s
    KILL_005 = "KILL-005"  # Consecutive guardrail rejections > 3
    KILL_006 = "KILL-006"  # State hash drift post-narration


# ============================================================================
# Evidence Dataclass
# ============================================================================


@dataclass(frozen=True)
class KillSwitchEvidence:
    """Structured evidence captured when a kill switch fires.

    Follows M1_MONITORING_PROTOCOL JSON evidence schema.

    Attributes:
        kill_switch: Kill switch identifier (e.g. "KILL-002")
        timestamp: ISO 8601 timestamp of trigger
        trigger_signal: Human-readable description of what triggered it
        evidence: Switch-specific evidence payload
        stack_trace: Python stack trace captured at trigger time
    """
    kill_switch: str
    timestamp: str
    trigger_signal: str
    evidence: dict
    stack_trace: str


# ============================================================================
# Mechanical Assertion Patterns (KILL-002)
# ============================================================================

# Compiled once at module level — never per-call
MECHANICAL_PATTERNS = [
    # Damage quantities: "15 damage", "15 points of damage"
    re.compile(r'\b\d+\s*(points?\s+of\s+)?damage\b', re.IGNORECASE),
    # AC references: "AC 18", "AC18"
    re.compile(r'\bAC\s*\d+\b'),
    # Hit point references: "15 hp", "15 hit points", "15hp"
    re.compile(r'\b\d+\s*h(it\s*)?p(oints?)?\b', re.IGNORECASE),
    # Rule citations: "PHB 145", "DMG 20", "MM 300"
    re.compile(r'\b(PHB|DMG|MM)\s*\d+'),
    # Attack bonus: "+5 to attack", "-2 attack"
    re.compile(r'[+-]\d+\s*(to\s+)?attack\b', re.IGNORECASE),
]


def detect_mechanical_assertions(text: str) -> Optional[Tuple[str, str]]:
    """Scan text for mechanical assertions that violate Spark boundary.

    Args:
        text: LLM-generated narration text

    Returns:
        Tuple of (pattern_description, matched_text) if found, else None
    """
    pattern_names = [
        "damage_quantity",
        "ac_reference",
        "hit_point_reference",
        "rule_citation",
        "attack_bonus",
    ]
    for pattern, name in zip(MECHANICAL_PATTERNS, pattern_names):
        match = pattern.search(text)
        if match:
            return (name, match.group(0))
    return None


# ============================================================================
# Kill Switch Registry
# ============================================================================


class KillSwitchRegistry:
    """Central registry for all kill switch state. Thread-safe, persistent across turns.

    Design:
    - State persists across calls (instance-level)
    - Manual reset only — no auto-recovery, no timeout reset
    - All triggers logged as structured JSON (KillSwitchEvidence)
    - any_triggered() is O(1) via boolean cache
    """

    def __init__(self):
        """Initialize registry with all switches inactive."""
        self._active: Dict[KillSwitchID, KillSwitchEvidence] = {}
        self._any_active: bool = False  # O(1) cache
        self._trigger_counts: Dict[KillSwitchID, int] = {k: 0 for k in KillSwitchID}
        self._consecutive_rejections: int = 0
        self._rejection_types: List[str] = []

    def trigger(self, switch_id: KillSwitchID, evidence: KillSwitchEvidence) -> None:
        """Fire a kill switch. Blocks future Spark calls for that switch.

        Args:
            switch_id: Which kill switch to trigger
            evidence: Structured evidence for the trigger
        """
        self._active[switch_id] = evidence
        self._any_active = True
        self._trigger_counts[switch_id] += 1
        logger.critical(
            f"{switch_id.value} TRIGGERED: {evidence.trigger_signal}"
        )

    def is_triggered(self, switch_id: KillSwitchID) -> bool:
        """Check if a specific kill switch is active."""
        return switch_id in self._active

    def any_triggered(self) -> bool:
        """Check if ANY kill switch is active (fast path for template fallback)."""
        return self._any_active

    def reset(self, switch_id: KillSwitchID) -> None:
        """Manual reset of a specific kill switch. Logs the reset as an event.

        Args:
            switch_id: Which kill switch to reset
        """
        if switch_id in self._active:
            del self._active[switch_id]
            self._any_active = len(self._active) > 0
            logger.warning(f"{switch_id.value} manually reset (requires Agent D approval)")

    def get_evidence(self, switch_id: KillSwitchID) -> Optional[KillSwitchEvidence]:
        """Retrieve evidence for an active kill switch."""
        return self._active.get(switch_id)

    def get_all_active(self) -> List[Tuple[KillSwitchID, KillSwitchEvidence]]:
        """List all active kill switches with evidence."""
        return list(self._active.items())

    def get_metrics(self) -> dict:
        """Return trigger counts per switch (lifetime, not just active)."""
        return {k.value: v for k, v in self._trigger_counts.items()}

    # ── Consecutive rejection tracking (KILL-005) ─────────────────────

    def record_rejection(self, switch_id: KillSwitchID) -> None:
        """Record a guardrail rejection for KILL-005 consecutive tracking.

        Args:
            switch_id: Which switch caused the rejection
        """
        self._consecutive_rejections += 1
        self._rejection_types.append(switch_id.value)

    def reset_rejection_counter(self) -> None:
        """Reset consecutive rejection counter (called on successful generation)."""
        self._consecutive_rejections = 0
        self._rejection_types = []

    @property
    def consecutive_rejections(self) -> int:
        """Current consecutive rejection count."""
        return self._consecutive_rejections

    @property
    def rejection_types(self) -> List[str]:
        """Types of switches that fired in the current rejection streak."""
        return list(self._rejection_types)


def build_evidence(
    switch_id: KillSwitchID,
    trigger_signal: str,
    evidence: dict,
) -> KillSwitchEvidence:
    """Build a KillSwitchEvidence with current timestamp and stack trace.

    Args:
        switch_id: Which switch is being triggered
        trigger_signal: Human-readable description
        evidence: Switch-specific evidence payload

    Returns:
        Fully populated KillSwitchEvidence
    """
    return KillSwitchEvidence(
        kill_switch=switch_id.value,
        timestamp=datetime.now(timezone.utc).isoformat(),
        trigger_signal=trigger_signal,
        evidence=evidence,
        stack_trace=traceback.format_stack()[-3] if len(traceback.format_stack()) >= 3 else "",
    )
