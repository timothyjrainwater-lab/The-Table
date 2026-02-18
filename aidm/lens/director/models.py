"""Director data models — frozen dataclasses for beat selection output.

All dataclasses are frozen and carry canonical_bytes + bytes_hash
for deterministic verification.

Authority: Director Spec v0 §3, GT v12 DIR-001..DIR-004.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, Optional, Tuple

from aidm.oracle.canonical import canonical_json, canonical_short_hash


# Valid beat types (Director Spec v0 §2.3).
BEAT_TYPES = frozenset({
    "ADVANCE_THREAD",
    "INTRODUCE_NPC",
    "REVEAL_CLUE",
    "ENVIRONMENTAL",
    "COMBAT_TRANSITION",
    "SCENE_TRANSITION",
    "PERMISSION_PROMPT",
})

# Valid pacing modes (Director Spec v0 §3.1).
PACING_MODES = frozenset({
    "NORMAL",
    "SLOW_BURN",
    "ACCELERATE",
    "CLIMAX",
})

# Valid nudge types (GT DIR-003).
NUDGE_TYPES = frozenset({
    "NONE",
    "SPOTLIGHT_NUDGE",
    "CALLBACK_NUDGE",
    "PRESSURE_NUDGE",
    "CLARIFY_OPTIONS",
})


@dataclass(frozen=True)
class BeatIntent:
    """Director's beat selection output — references only, never content.

    BeatIntent is a reference document containing handles and type tags.
    Lens compiles the referenced handles into PromptPack channels.
    Director never produces renderable text.
    """

    beat_id: str
    beat_type: str
    target_handles: Tuple[str, ...]
    pacing_mode: str
    permission_prompt: bool
    canonical_bytes: bytes
    bytes_hash: str

    def __post_init__(self) -> None:
        if self.beat_type not in BEAT_TYPES:
            raise ValueError(f"Unknown beat_type: {self.beat_type!r}")
        if self.pacing_mode not in PACING_MODES:
            raise ValueError(f"Unknown pacing_mode: {self.pacing_mode!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "beat_id": self.beat_id,
            "beat_type": self.beat_type,
            "target_handles": list(self.target_handles),
            "pacing_mode": self.pacing_mode,
            "permission_prompt": self.permission_prompt,
            "bytes_hash": self.bytes_hash,
        }


@dataclass(frozen=True)
class NudgeDirective:
    """Director's nudge output — 0-1 per scene, metadata only.

    If type=NONE, no nudge is emitted (default state — DIR-004).
    """

    type: str
    target_handle: Optional[str]
    consequence_handles: Tuple[str, ...]
    reason_code: str
    canonical_bytes: bytes
    bytes_hash: str

    def __post_init__(self) -> None:
        if self.type not in NUDGE_TYPES:
            raise ValueError(f"Unknown nudge type: {self.type!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "target_handle": self.target_handle,
            "consequence_handles": list(self.consequence_handles),
            "reason_code": self.reason_code,
            "bytes_hash": self.bytes_hash,
        }


@dataclass(frozen=True)
class DirectorPromptPack:
    """Subset of WorkingSet that Director receives as its ONLY input.

    Must NOT contain locked precision tokens, mechanical data, or raw
    fact payloads.  Contains only handles and state tags from the
    WorkingSet allowmention set.
    """

    scene_id: Optional[str]
    campaign_id: str
    mode: str
    allowmention_handles: Tuple[str, ...]
    active_thread_handles: Tuple[str, ...]
    dormant_thread_handles: Tuple[str, ...]
    active_clock_handles: Tuple[str, ...]
    pending_state: bool
    beat_count_this_scene: int
    last_nudge_beat: Optional[int]
    last_permission_beat: int
    beats_since_player_action: int
    canonical_bytes: bytes
    bytes_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "campaign_id": self.campaign_id,
            "mode": self.mode,
            "allowmention_handles": list(self.allowmention_handles),
            "active_thread_handles": list(self.active_thread_handles),
            "dormant_thread_handles": list(self.dormant_thread_handles),
            "active_clock_handles": list(self.active_clock_handles),
            "pending_state": self.pending_state,
            "beat_count_this_scene": self.beat_count_this_scene,
            "last_nudge_beat": self.last_nudge_beat,
            "last_permission_beat": self.last_permission_beat,
            "beats_since_player_action": self.beats_since_player_action,
            "bytes_hash": self.bytes_hash,
        }


@dataclass
class BeatHistory:
    """Scene-scoped beat sequence counter.

    Mutable — tracks state across beats within a scene.
    Reconstructible from event log replay.
    """

    beats_this_scene: int = 0
    last_nudge_beat: Optional[int] = None
    nudge_fired_this_scene: bool = False
    beats_since_player_action: int = 0
    last_permission_beat: int = 0

    def record_beat(self, had_player_action: bool) -> None:
        """Record that a beat occurred."""
        self.beats_this_scene += 1
        if had_player_action:
            self.beats_since_player_action = 0
        else:
            self.beats_since_player_action += 1

    def record_nudge(self) -> None:
        """Record that a nudge fired this beat."""
        self.last_nudge_beat = self.beats_this_scene
        self.nudge_fired_this_scene = True

    def record_permission(self) -> None:
        """Record that a permission prompt was included."""
        self.last_permission_beat = self.beats_this_scene

    def reset_scene(self) -> None:
        """Reset for a new scene."""
        self.beats_this_scene = 0
        self.last_nudge_beat = None
        self.nudge_fired_this_scene = False
        self.beats_since_player_action = 0
        self.last_permission_beat = 0


def make_beat_intent(
    scene_id: Optional[str],
    beat_sequence: int,
    beat_type: str,
    target_handles: Tuple[str, ...],
    pacing_mode: str = "NORMAL",
    permission_prompt: bool = False,
) -> BeatIntent:
    """Factory: build BeatIntent with deterministic beat_id."""
    pre_hash = {
        "beat_type": beat_type,
        "pacing_mode": pacing_mode,
        "permission_prompt": permission_prompt,
        "scene_id": scene_id,
        "beat_sequence": beat_sequence,
        "target_handles": sorted(target_handles),
    }

    canonical_bytes = canonical_json(pre_hash)
    bytes_hash = hashlib.sha256(canonical_bytes).hexdigest()
    beat_id = canonical_short_hash(pre_hash)

    return BeatIntent(
        beat_id=beat_id,
        beat_type=beat_type,
        target_handles=target_handles,
        pacing_mode=pacing_mode,
        permission_prompt=permission_prompt,
        canonical_bytes=canonical_bytes,
        bytes_hash=bytes_hash,
    )


def make_nudge_directive(
    nudge_type: str = "NONE",
    target_handle: Optional[str] = None,
    consequence_handles: Tuple[str, ...] = (),
    reason_code: str = "default",
) -> NudgeDirective:
    """Factory: build NudgeDirective with canonical bytes."""
    pre_hash = {
        "type": nudge_type,
        "target_handle": target_handle,
        "consequence_handles": sorted(consequence_handles),
        "reason_code": reason_code,
    }

    canonical_bytes = canonical_json(pre_hash)
    bytes_hash = hashlib.sha256(canonical_bytes).hexdigest()

    return NudgeDirective(
        type=nudge_type,
        target_handle=target_handle,
        consequence_handles=consequence_handles,
        reason_code=reason_code,
        canonical_bytes=canonical_bytes,
        bytes_hash=bytes_hash,
    )


def compile_director_promptpack(
    working_set,
    beat_history: BeatHistory,
    pending_state: bool = False,
    active_thread_handles: Tuple[str, ...] = (),
    dormant_thread_handles: Tuple[str, ...] = (),
    active_clock_handles: Tuple[str, ...] = (),
) -> DirectorPromptPack:
    """Compile DirectorPromptPack from WorkingSet + beat history.

    DirectorPromptPack is the ONLY input Director receives.
    Contains only handles and state tags from the allowmention set.
    No locked precision tokens, no mechanical data, no raw fact payloads.

    Phase 1 note: StoryState has no thread/clock fields.  Thread and clock
    handles are passed explicitly (empty in Phase 1 unless externally sourced).
    """
    pre_hash = {
        "scene_id": working_set.scene_id,
        "campaign_id": working_set.campaign_id,
        "mode": working_set.mode,
        "allowmention_handles": sorted(working_set.allowmention_handles),
        "active_thread_handles": sorted(active_thread_handles),
        "dormant_thread_handles": sorted(dormant_thread_handles),
        "active_clock_handles": sorted(active_clock_handles),
        "pending_state": pending_state,
        "beat_count_this_scene": beat_history.beats_this_scene,
        "last_nudge_beat": beat_history.last_nudge_beat,
        "last_permission_beat": beat_history.last_permission_beat,
        "beats_since_player_action": beat_history.beats_since_player_action,
    }

    canonical_bytes = canonical_json(pre_hash)
    bytes_hash = hashlib.sha256(canonical_bytes).hexdigest()

    return DirectorPromptPack(
        scene_id=working_set.scene_id,
        campaign_id=working_set.campaign_id,
        mode=working_set.mode,
        allowmention_handles=working_set.allowmention_handles,
        active_thread_handles=active_thread_handles,
        dormant_thread_handles=dormant_thread_handles,
        active_clock_handles=active_clock_handles,
        pending_state=pending_state,
        beat_count_this_scene=beat_history.beats_this_scene,
        last_nudge_beat=beat_history.last_nudge_beat,
        last_permission_beat=beat_history.last_permission_beat,
        beats_since_player_action=beat_history.beats_since_player_action,
        canonical_bytes=canonical_bytes,
        bytes_hash=bytes_hash,
    )
