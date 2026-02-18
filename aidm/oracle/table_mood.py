"""TableMood — append-only observation store for player responsiveness signals.

Records mood observations (explicit feedback + inferred signals) scoped to
scenes.  Oracle-owned, read-only from everywhere else.

Phase 1 signals:
    - EXPLICIT_FEEDBACK: player-provided tags (fun, confused, tense, etc.)
    - INFERRED_SIGNAL: detected markers (confusion phrases, laughter markers)
      with confidence levels.

Authority: DOCTRINE_08_DIRECTOR_SPEC_V0 §9 (Phase 2 deferred items),
MEMO_TABLE_MOOD_SUBSYSTEM.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from aidm.oracle.canonical import canonical_hash, canonical_json, canonical_short_hash


# Valid observation sources.
OBSERVATION_SOURCES = frozenset({"EXPLICIT_FEEDBACK", "INFERRED_SIGNAL"})

# Valid observation scopes.
OBSERVATION_SCOPES = frozenset({"SCENE", "SESSION"})

# Valid mood tags.
MOOD_TAGS = frozenset({
    "fun",
    "confused",
    "tense",
    "bored",
    "engaged",
    "frustrated",
})

# Valid confidence levels for inferred signals.
CONFIDENCE_LEVELS = frozenset({"low", "medium", "high"})


@dataclass(frozen=True)
class MoodObservation:
    """A single mood observation.  Immutable and content-addressed."""

    observation_id: str
    source: str
    scope: str
    tags: Tuple[str, ...]
    scene_id: str
    provenance_event_id: int
    confidence: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.source not in OBSERVATION_SOURCES:
            raise ValueError(f"Unknown source: {self.source!r}")
        if self.scope not in OBSERVATION_SCOPES:
            raise ValueError(f"Unknown scope: {self.scope!r}")
        for tag in self.tags:
            if tag not in MOOD_TAGS:
                raise ValueError(f"Unknown mood tag: {tag!r}")
        if self.source == "INFERRED_SIGNAL":
            if self.confidence is not None and self.confidence not in CONFIDENCE_LEVELS:
                raise ValueError(f"Unknown confidence: {self.confidence!r}")
        if self.source == "EXPLICIT_FEEDBACK" and self.confidence is not None:
            raise ValueError(
                "Explicit feedback must not have a confidence level"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "source": self.source,
            "scope": self.scope,
            "tags": list(self.tags),
            "scene_id": self.scene_id,
            "provenance_event_id": self.provenance_event_id,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


def make_mood_observation(
    source: str,
    scope: str,
    tags: Tuple[str, ...],
    scene_id: str,
    provenance_event_id: int,
    confidence: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
) -> MoodObservation:
    """Factory: build a MoodObservation with auto-computed observation_id.

    The observation_id is content-addressed from the hashable fields.
    """
    # Validate evidence is canonical-safe (no floats) if present.
    if evidence is not None:
        canonical_json(evidence)

    id_payload = {
        "source": source,
        "scope": scope,
        "tags": sorted(tags),
        "scene_id": scene_id,
        "provenance_event_id": provenance_event_id,
    }
    observation_id = canonical_short_hash(id_payload)

    return MoodObservation(
        observation_id=observation_id,
        source=source,
        scope=scope,
        tags=tags,
        scene_id=scene_id,
        provenance_event_id=provenance_event_id,
        confidence=confidence,
        evidence=evidence,
    )


class TableMoodStore:
    """Append-only store of mood observations.

    No mutation, no deletion at store level.
    """

    def __init__(self) -> None:
        self._observations: List[MoodObservation] = []
        self._ids: set = set()

    def append(self, observation: MoodObservation) -> None:
        """Append an observation.  Reject duplicates by observation_id."""
        if observation.observation_id in self._ids:
            raise ValueError(
                f"Duplicate observation_id {observation.observation_id!r}"
            )
        self._ids.add(observation.observation_id)
        self._observations.append(observation)

    def observations_for_scene(self, scene_id: str) -> List[MoodObservation]:
        """All observations for a given scene, in insertion order."""
        return [o for o in self._observations if o.scene_id == scene_id]

    def recent_observations(self, n: int) -> List[MoodObservation]:
        """Last N observations across all scenes, in insertion order."""
        return self._observations[-n:]

    def all_observations(self) -> List[MoodObservation]:
        """All observations in insertion order."""
        return list(self._observations)

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic serialization — sorted by observation_id for digest."""
        sorted_obs = sorted(
            self._observations, key=lambda o: o.observation_id
        )
        return {
            "observations": [o.to_dict() for o in sorted_obs],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TableMoodStore":
        """Reconstruct from serialized dict."""
        store = cls()
        for obs_data in data.get("observations", []):
            tags = tuple(obs_data["tags"])
            obs = MoodObservation(
                observation_id=obs_data["observation_id"],
                source=obs_data["source"],
                scope=obs_data["scope"],
                tags=tags,
                scene_id=obs_data["scene_id"],
                provenance_event_id=obs_data["provenance_event_id"],
                confidence=obs_data.get("confidence"),
                evidence=obs_data.get("evidence"),
            )
            store._ids.add(obs.observation_id)
            store._observations.append(obs)
        return store

    def digest(self) -> str:
        """Determinism receipt: canonical_hash of sorted observations.

        Same observations in any insertion order produce the same digest.
        """
        sorted_dicts = sorted(
            [o.to_dict() for o in self._observations],
            key=lambda d: d["observation_id"],
        )
        return canonical_hash(sorted_dicts)

    def __len__(self) -> int:
        return len(self._observations)
