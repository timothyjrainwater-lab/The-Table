"""WO-030: Play Loop → Narration Pipeline Adapter

This module wires play_loop narration tokens to GuardedNarrationService.
It lives in aidm/narration/ (presentation layer) to avoid BL-004 violation.

BOUNDARY LAW COMPLIANCE:
- BL-003: Narration must NOT import from core (BOX)
- BL-004: BOX (core) must not import presentation (narration)
- This adapter receives data as primitive types/dicts to avoid direct imports
- play_loop converts its types to dicts before calling adapter
- Adapter can import FROM narration (service, schemas)

Architecture:
    play_loop (core) → converts to dicts → calls adapter
    ↓
    adapter (this module) → builds EngineResult, calls narration service
    ↓
    GuardedNarrationService → generates narration text

Reference: docs/runtime/IPC_CONTRACT.md, WO-030 dispatch
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import uuid

from aidm.narration.guarded_narration_service import (
    GuardedNarrationService,
    NarrationRequest,
    NarrationResult,
    FrozenMemorySnapshot,
    NarrationBoundaryViolation,
)
from aidm.schemas.engine_result import EngineResult, EngineResultBuilder, EngineResultStatus


def build_engine_result_for_narration(
    narration_token: str,
    events: List[Dict[str, Any]],
    actor_id: str,
    actor_name: str,
    target_id: Optional[str],
    target_name: Optional[str],
    weapon_name: Optional[str],
) -> EngineResult:
    """Build a minimal EngineResult for narration context.

    Args:
        narration_token: Token identifying the type of narration needed
        events: List of event dicts from turn execution
        actor_id: ID of the actor performing the action
        actor_name: Display name of the actor
        target_id: ID of the target (if applicable)
        target_name: Display name of the target (if applicable)
        weapon_name: Name of weapon used (if applicable)

    Returns:
        EngineResult ready for narration generation
    """
    # Build EngineResult using builder
    builder = EngineResultBuilder(
        intent_id=f"turn_{actor_id}",
        rng_offset=0,
    )

    # Set narration token
    builder.set_narration_token(narration_token)

    # Add metadata for context
    builder.add_metadata("actor_name", actor_name)
    if target_name:
        builder.add_metadata("target_name", target_name)
    if weapon_name:
        builder.add_metadata("weapon_name", weapon_name)

    # Add events
    for event_dict in events:
        builder.add_event(event_dict)

    # Build the final EngineResult
    result = builder.build(
        result_id=str(uuid.uuid4()),
        resolved_at=datetime.utcnow(),
        status=EngineResultStatus.SUCCESS,
    )

    return result


def generate_narration_for_turn(
    narration_token: str,
    events: List[Dict[str, Any]],
    actor_id: str,
    actor_name: str,
    target_id: Optional[str],
    target_name: Optional[str],
    weapon_name: Optional[str],
    world_state_hash: str,
    narration_service: GuardedNarrationService,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate narration text for a turn.

    This is the main entry point from play_loop. It builds the EngineResult,
    creates the narration request, and calls the service.

    Args:
        narration_token: Token identifying the narration type
        events: Event dicts from turn execution
        actor_id: Actor entity ID
        actor_name: Actor display name
        target_id: Target entity ID (if applicable)
        target_name: Target display name (if applicable)
        weapon_name: Weapon name (if applicable)
        world_state_hash: SHA-256 hash of world state for KILL-006
        narration_service: GuardedNarrationService instance

    Returns:
        Tuple of (narration_text, narration_provenance)
        Returns (None, None) if narration fails gracefully
    """
    try:
        # Build EngineResult for narration context
        engine_result = build_engine_result_for_narration(
            narration_token=narration_token,
            events=events,
            actor_id=actor_id,
            actor_name=actor_name,
            target_id=target_id,
            target_name=target_name,
            weapon_name=weapon_name,
        )

        # Build frozen memory snapshot (empty dict for now — real memory comes in Phase 2)
        memory_snapshot = FrozenMemorySnapshot.create(
            session_ledger=None,
            evidence_ledger=None,
            thread_registry=None,
        )

        # Build request
        request = NarrationRequest(
            engine_result=engine_result,
            memory_snapshot=memory_snapshot,
            temperature=0.8,
            world_state_hash=world_state_hash,
        )

        result = narration_service.generate_narration(request)
        return result.text, result.provenance

    except NarrationBoundaryViolation:
        # Kill switch fired — use token as-is (no narration text)
        return None, None
    except Exception:
        # Any other error — narration is non-critical, don't crash the turn
        return None, None
