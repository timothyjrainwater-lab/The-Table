"""Director invocation — orchestrates Director into Lens→PromptPack pipeline.

This is the call site where Director output shapes the PromptPack.  The
invocation function:
    1. Compiles DirectorPromptPack from WorkingSet + BeatHistory
    2. Runs select_beat_with_audit() (pure, deterministic, no side effects)
    3. Passes BeatIntent + NudgeDirective to compile_promptpack()
    4. Emits EV-033 NudgeSelected / EV-034 NudgeSuppressed events
    5. Updates BeatHistory
    6. Returns the enriched PromptPack + events

Events are emitted HERE (at the call site), not inside DirectorPolicy.
This keeps the policy testable as a pure function with no side effects.

Authority: Director Spec v0 §9 (Phase 2), Lens Spec v0 §2.5.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from aidm.core.event_log import Event
from aidm.lens.director.models import (
    BeatHistory,
    BeatIntent,
    NudgeDirective,
    compile_director_promptpack,
)
from aidm.lens.director.policy import (
    DirectorPolicyPins,
    SelectBeatResult,
    select_beat_with_audit,
)
from aidm.lens.promptpack_compiler import (
    AllowedToSayEnvelope,
    compile_promptpack,
)
from aidm.oracle.working_set import WorkingSet
from aidm.schemas.prompt_pack import PromptPack


@dataclass(frozen=True)
class DirectorInvocationResult:
    """Result of a Director invocation — everything the caller needs."""

    promptpack: PromptPack
    envelope: AllowedToSayEnvelope
    beat_intent: BeatIntent
    nudge_directive: NudgeDirective
    events: Tuple[Event, ...]


def invoke_director(
    working_set: WorkingSet,
    beat_history: BeatHistory,
    next_event_id: int,
    timestamp: float,
    pins: DirectorPolicyPins = DirectorPolicyPins(),
    pending_state: bool = False,
    active_thread_handles: Tuple[str, ...] = (),
    dormant_thread_handles: Tuple[str, ...] = (),
    active_clock_handles: Tuple[str, ...] = (),
) -> DirectorInvocationResult:
    """Orchestrate Director into the Lens→PromptPack pipeline.

    Pipeline:
        WorkingSet → compile_director_promptpack() → DirectorPromptPack
        DirectorPromptPack + BeatHistory → select_beat_with_audit()
            → SelectBeatResult(beat, nudge, suppressions)
        (WorkingSet + BeatIntent + NudgeDirective) → compile_promptpack()
            → (PromptPack, AllowedToSayEnvelope)

    Side effects:
        - Emits EV-033/EV-034 events (returned, not appended to EventLog)
        - Updates BeatHistory in place (record_beat, record_nudge, record_permission)

    Returns DirectorInvocationResult with promptpack, envelope, beat, nudge, events.
    """
    # Step 1: Compile DirectorPromptPack.
    dpp = compile_director_promptpack(
        working_set,
        beat_history,
        pending_state=pending_state,
        active_thread_handles=active_thread_handles,
        dormant_thread_handles=dormant_thread_handles,
        active_clock_handles=active_clock_handles,
    )

    # Step 2: Run deterministic beat selection with audit trail.
    result = select_beat_with_audit(dpp, beat_history, pins)

    # Step 3: Compile PromptPack with Director input.
    pack, envelope = compile_promptpack(
        working_set,
        beat_intent=result.beat,
        nudge_directive=result.nudge,
    )

    # Step 4: Emit events.
    events: List[Event] = []
    current_event_id = next_event_id
    scene_id = working_set.scene_id

    # Always emit director_beat_selected for BeatHistory reconstruction.
    events.append(Event(
        event_id=current_event_id,
        event_type="director_beat_selected",
        timestamp=timestamp,
        payload={
            "scene_id": scene_id,
            "beat_id": result.beat.beat_id,
            "beat_type": result.beat.beat_type,
            "pacing_mode": result.beat.pacing_mode,
            "permission_prompt": result.beat.permission_prompt,
            "target_handles": list(result.beat.target_handles),
            "nudge_type": result.nudge.type,
            "had_player_action": False,  # Director invocation = no player action this beat
        },
    ))
    current_event_id += 1

    # EV-033: NudgeSelected (when a nudge fires).
    if result.nudge.type != "NONE":
        events.append(Event(
            event_id=current_event_id,
            event_type="nudge_selected",
            timestamp=timestamp + 0.01,
            payload={
                "scene_id": scene_id,
                "nudge_type": result.nudge.type,
                "target_handle": result.nudge.target_handle,
                "reason_code": result.nudge.reason_code,
            },
        ))
        current_event_id += 1

    # EV-034: NudgeSuppressed (when a nudge rule fired but was blocked).
    for suppression in result.suppressions:
        events.append(Event(
            event_id=current_event_id,
            event_type="nudge_suppressed",
            timestamp=timestamp + 0.01,
            payload={
                "scene_id": scene_id,
                "reason_code": suppression.reason_code,
                "rule": suppression.rule_that_fired,
            },
        ))
        current_event_id += 1

    # Step 5: Update BeatHistory.
    had_player_action = False  # Director invocations are system beats.
    beat_history.record_beat(had_player_action=had_player_action)
    if result.nudge.type != "NONE":
        beat_history.record_nudge()
    if result.beat.permission_prompt:
        beat_history.record_permission()

    return DirectorInvocationResult(
        promptpack=pack,
        envelope=envelope,
        beat_intent=result.beat,
        nudge_directive=result.nudge,
        events=tuple(events),
    )
