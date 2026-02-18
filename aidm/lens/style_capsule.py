"""StyleCapsule — compact presentation-hint struct compiled from TableMood.

StyleCapsule is a Lens compilation artifact (NOT an Oracle store).  It
is deterministically compiled from mood observations and used by Director
to modulate pacing decisions.  No truth influence, no mechanical influence,
no backflow.

Authority: DOCTRINE_08_DIRECTOR_SPEC_V0 §9, MEMO_TABLE_MOOD_SUBSYSTEM.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from aidm.oracle.canonical import canonical_json


# Valid pacing modes for StyleCapsule.
STYLE_PACING_MODES = frozenset({"push", "breathe", "normal"})

# Valid beat lengths.
BEAT_LENGTHS = frozenset({"short", "medium", "long"})


@dataclass(frozen=True)
class StyleCapsule:
    """Compact presentation-hint struct for Director pacing modulation.

    Compiled deterministically from TableMood observations.  Internal to
    the Lens->Director->PromptPack pipeline — never sent over WebSocket.
    """

    target_beat_length: str = "medium"
    recap_needed: bool = False
    humor_window: bool = False
    pacing_mode: str = "normal"

    def __post_init__(self) -> None:
        if self.target_beat_length not in BEAT_LENGTHS:
            raise ValueError(
                f"Unknown target_beat_length: {self.target_beat_length!r}"
            )
        if self.pacing_mode not in STYLE_PACING_MODES:
            raise ValueError(f"Unknown pacing_mode: {self.pacing_mode!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_beat_length": self.target_beat_length,
            "recap_needed": self.recap_needed,
            "humor_window": self.humor_window,
            "pacing_mode": self.pacing_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StyleCapsule":
        return cls(
            target_beat_length=data.get("target_beat_length", "medium"),
            recap_needed=data.get("recap_needed", False),
            humor_window=data.get("humor_window", False),
            pacing_mode=data.get("pacing_mode", "normal"),
        )


def compile_style_capsule(
    mood_observations: List,
    scene_id: str,
) -> StyleCapsule:
    """Compile a StyleCapsule from mood observations.

    Deterministic: same observations + scene_id -> identical StyleCapsule.
    No randomness, no timestamps, no external state.

    Rules (applied to last 3 observations):
        - confusion markers (tags containing 'confused') -> recap_needed=True
        - laughter/fun markers (tags containing 'fun') -> humor_window=True
        - bored/frustrated signals -> pacing_mode='push'
        - engaged signals -> pacing_mode='normal'
        - no signals -> all defaults
    """
    if not mood_observations:
        return StyleCapsule()

    # Take the last 3 observations (most recent signals).
    recent = mood_observations[-3:]

    recap_needed = False
    humor_window = False
    pacing_mode = "normal"

    # Collect all tags from recent observations.
    all_tags: list = []
    for obs in recent:
        if hasattr(obs, "tags"):
            all_tags.extend(obs.tags)
        elif isinstance(obs, dict):
            all_tags.extend(obs.get("tags", ()))

    # Apply rules.
    if "confused" in all_tags:
        recap_needed = True
    if "fun" in all_tags:
        humor_window = True
    if "bored" in all_tags or "frustrated" in all_tags:
        pacing_mode = "push"
    if "engaged" in all_tags:
        # Engaged overrides bored/frustrated back to normal.
        pacing_mode = "normal"

    # Beat length: short when pushing, long when breathing, medium default.
    target_beat_length = "medium"
    if pacing_mode == "push":
        target_beat_length = "short"

    return StyleCapsule(
        target_beat_length=target_beat_length,
        recap_needed=recap_needed,
        humor_window=humor_window,
        pacing_mode=pacing_mode,
    )
