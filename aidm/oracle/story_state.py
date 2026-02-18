"""StoryState — minimal evented pointers for session/scene tracking.

Phase 1: pointers only (world_id, campaign_id, scene_id, mode, version).
No threads or clocks.  Every change creates a new immutable StoryState
with an incremented version.  The log is append-only.

Authority: Oracle Memo v5.2 section 4.2, GT v12 A-ORACLE-SPINE.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from aidm.oracle.canonical import canonical_hash, canonical_json

VALID_MODES = frozenset({
    "COMBAT",
    "EXPLORATION",
    "ROLEPLAY",
    "REFERENCE",
    "NOTEBOOK",
})


@dataclass(frozen=True)
class StoryState:
    """Immutable snapshot of session/scene pointers."""

    campaign_id: str
    world_id: Optional[str] = None
    scene_id: Optional[str] = None
    mode: str = "EXPLORATION"
    version: int = 0

    def __post_init__(self) -> None:
        if self.mode not in VALID_MODES:
            raise ValueError(f"Unknown mode: {self.mode!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "world_id": self.world_id,
            "scene_id": self.scene_id,
            "mode": self.mode,
            "version": self.version,
        }


class StoryStateLog:
    """Append-only log of StoryState versions."""

    def __init__(self, initial: StoryState) -> None:
        self._history: List[StoryState] = [initial]

    def current(self) -> StoryState:
        """Return the latest StoryState."""
        return self._history[-1]

    def apply(self, event_type: str, payload: Dict[str, Any]) -> StoryState:
        """Apply an event to produce a new StoryState.

        Supported event types:
            - ``scene_start``: sets scene_id from payload["scene_id"]
            - ``scene_end``: clears scene_id to None
            - ``mode_changed``: sets mode from payload["mode"]
            - ``world_id_set``: sets world_id from payload["world_id"]

        Unknown event types are silently ignored (return current state
        unchanged, no new version appended).
        """
        cur = self.current()
        new_version = cur.version + 1

        if event_type == "scene_start":
            new_state = StoryState(
                campaign_id=cur.campaign_id,
                world_id=cur.world_id,
                scene_id=payload["scene_id"],
                mode=cur.mode,
                version=new_version,
            )
        elif event_type == "scene_end":
            new_state = StoryState(
                campaign_id=cur.campaign_id,
                world_id=cur.world_id,
                scene_id=None,
                mode=cur.mode,
                version=new_version,
            )
        elif event_type == "mode_changed":
            new_state = StoryState(
                campaign_id=cur.campaign_id,
                world_id=cur.world_id,
                scene_id=cur.scene_id,
                mode=payload["mode"],
                version=new_version,
            )
        elif event_type == "world_id_set":
            new_state = StoryState(
                campaign_id=cur.campaign_id,
                world_id=payload["world_id"],
                scene_id=cur.scene_id,
                mode=cur.mode,
                version=new_version,
            )
        else:
            # Unknown event type — ignore, no crash.
            return cur

        self._history.append(new_state)
        return new_state

    def history(self) -> List[StoryState]:
        """All versions, ordered by version number."""
        return list(self._history)

    def to_jsonl(self, path: Path) -> None:
        """Persist all versions using canonical_json()."""
        with open(path, "wb") as fh:
            for state in self._history:
                fh.write(canonical_json(state.to_dict()))
                fh.write(b"\n")

    @classmethod
    def from_jsonl(cls, path: Path) -> "StoryStateLog":
        """Load from JSONL.  First line is the initial state."""
        states: List[StoryState] = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                states.append(StoryState(**data))

        if not states:
            raise ValueError("Empty StoryState JSONL — at least one entry required.")

        log = cls(states[0])
        for state in states[1:]:
            log._history.append(state)
        return log

    def digest(self) -> str:
        """Determinism receipt of current state."""
        return canonical_hash(self.current().to_dict())
