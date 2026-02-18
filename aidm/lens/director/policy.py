"""DirectorPolicy — deterministic priority cascade for beat selection.

Stateless function that takes DirectorPromptPack + BeatHistory and returns
(BeatIntent, NudgeDirective).  Priority rules evaluated in order; the first
rule that fires produces the BeatIntent.

Authority: Director Spec v0 §5, GT v12 DIR-003..DIR-005.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from aidm.lens.director.models import (
    BeatHistory,
    BeatIntent,
    DirectorPromptPack,
    NudgeDirective,
    make_beat_intent,
    make_nudge_directive,
)


@dataclass(frozen=True)
class DirectorPolicyPins:
    """Configurable threshold pins for Director policy.

    All fields are deterministic policy knobs — no entropy.
    """

    stall_threshold: int = 3
    urgency_threshold: int = 2
    cooldown_beats: int = 4
    permission_cadence: int = 4


def select_beat(
    dpp: DirectorPromptPack,
    beat_history: BeatHistory,
    pins: DirectorPolicyPins = DirectorPolicyPins(),
) -> Tuple[BeatIntent, NudgeDirective]:
    """Deterministic beat selection via priority cascade.

    Priority rules (evaluated in order — first match wins):
        P1: PENDING_OBLIGATION — pending interaction → no beat (Director inert)
        P2: SCENE_TRANSITION — scene end conditions → SCENE_TRANSITION
        P3: STALL_DETECTION — no player action for N beats → SPOTLIGHT_NUDGE
        P4: THREAD_PAYOFF — thread at payoff condition → ADVANCE_THREAD
        P5: PRESSURE_ESCALATION — clock within urgency → PRESSURE_NUDGE
        P6: CALLBACK_OPPORTUNITY — dormant thread re-entry → CALLBACK_NUDGE
        P7: DEFAULT — ENVIRONMENTAL, NORMAL pacing, no nudge

    Anti-rail constraints (DIR-004, HL-006):
        - 0-1 nudge per scene
        - Cooldown after nudge
        - Hysteresis: stall requires N consecutive inactive beats

    No entropy: same inputs → same outputs.
    """
    scene_id = dpp.scene_id
    beat_seq = beat_history.beats_this_scene

    # Determine if nudges are allowed this beat.
    nudge_allowed = _nudge_allowed(beat_history, pins)

    # Determine if permission prompt should attach.
    needs_permission = _needs_permission(beat_history, pins, scene_id)

    # P1: PENDING_OBLIGATION
    if dpp.pending_state:
        # Director is inert during pending states.
        return (
            make_beat_intent(
                scene_id=scene_id,
                beat_sequence=beat_seq,
                beat_type="ENVIRONMENTAL",
                target_handles=(),
                pacing_mode="NORMAL",
                permission_prompt=False,
            ),
            make_nudge_directive(
                nudge_type="NONE",
                reason_code="pending_obligation",
            ),
        )

    # P2: SCENE_TRANSITION — Phase 1: no scene end condition model.
    # This rule requires StoryState scene lifecycle (EV-031/EV-032).
    # Deferred — always falls through.

    # P3: STALL_DETECTION
    if (
        nudge_allowed
        and dpp.beats_since_player_action >= pins.stall_threshold
    ):
        # Stall detected — emit SPOTLIGHT_NUDGE.
        # Target: first allowmention handle (deterministic).
        target = (
            dpp.allowmention_handles[0]
            if dpp.allowmention_handles
            else None
        )
        return (
            make_beat_intent(
                scene_id=scene_id,
                beat_sequence=beat_seq,
                beat_type="ENVIRONMENTAL",
                target_handles=(target,) if target else (),
                pacing_mode="NORMAL",
                permission_prompt=needs_permission,
            ),
            make_nudge_directive(
                nudge_type="SPOTLIGHT_NUDGE",
                target_handle=target,
                reason_code="stall_detected",
            ),
        )

    # P4: THREAD_PAYOFF
    # Phase 1: no thread model in StoryState.
    # If active_thread_handles were provided, the first would be the payoff target.
    # Deferred — always falls through.

    # P5: PRESSURE_ESCALATION
    # Phase 1: no clock model in StoryState.
    # If active_clock_handles were provided, the first within urgency would fire.
    # Deferred — always falls through.

    # P6: CALLBACK_OPPORTUNITY
    # Phase 1: no dormant thread re-entry model.
    # Deferred — always falls through.

    # P7: DEFAULT — ENVIRONMENTAL, NORMAL pacing, no nudge.
    return (
        make_beat_intent(
            scene_id=scene_id,
            beat_sequence=beat_seq,
            beat_type="ENVIRONMENTAL",
            target_handles=(),
            pacing_mode="NORMAL",
            permission_prompt=needs_permission,
        ),
        make_nudge_directive(
            nudge_type="NONE",
            reason_code="default",
        ),
    )


def _nudge_allowed(
    beat_history: BeatHistory,
    pins: DirectorPolicyPins,
) -> bool:
    """Check if a nudge is allowed this beat.

    Constraints (DIR-004, HL-006):
        - 0-1 nudge per scene
        - Cooldown: pins.cooldown_beats after last nudge
    """
    # Already fired a nudge this scene.
    if beat_history.nudge_fired_this_scene:
        return False

    # In cooldown period.
    if beat_history.last_nudge_beat is not None:
        beats_since_nudge = (
            beat_history.beats_this_scene - beat_history.last_nudge_beat
        )
        if beats_since_nudge < pins.cooldown_beats:
            return False

    return True


def _needs_permission(
    beat_history: BeatHistory,
    pins: DirectorPolicyPins,
    scene_id: Optional[str],
) -> bool:
    """Determine if this beat should include a permission prompt (PC-004).

    Permission prompts attach at:
        A) Scene transitions (always) — handled by beat_type check downstream
        B) Every N beats (permission_cadence)
        C) After interruption resume (always) — not modeled in Phase 1
    """
    beats_since_permission = (
        beat_history.beats_this_scene - beat_history.last_permission_beat
    )
    return beats_since_permission >= pins.permission_cadence
