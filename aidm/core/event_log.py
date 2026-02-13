"""Append-only event log with JSONL serialization.

BOUNDARY LAW (BL-008): EventLog enforces monotonic event IDs. Out-of-order
or duplicate IDs are rejected with ValueError. This ordering guarantee is
required for deterministic replay — events must be applied in the same order
they were emitted.

SINGLE SOURCE OF TRUTH for: Game event recording and ordering.
CANONICAL OWNER: aidm.core.event_log (this file).
"""

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional
import json
from pathlib import Path


@dataclass
class Event:
    """Immutable event record in the game log."""

    event_id: int
    event_type: str
    timestamp: float
    payload: Dict[str, Any]
    rng_offset: int = 0
    citations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create Event from dictionary."""
        return cls(**data)


class EventLog:
    """Append-only ledger enforcing monotonic event IDs."""

    def __init__(self):
        self._events: List[Event] = []
        self._next_id: int = 0

    def append(self, event: Event) -> None:
        """
        Append event to log.

        Enforces monotonic event_id constraint.
        Raises ValueError if event_id is not strictly increasing.
        """
        if event.event_id != self._next_id:
            raise ValueError(
                f"Event ID must be {self._next_id} (monotonic), got {event.event_id}"
            )

        self._events.append(event)
        self._next_id += 1

    def to_jsonl(self, path: Path) -> None:
        """Serialize event log to JSONL file (one JSON object per line)."""
        with open(path, "w", encoding="utf-8") as f:
            for event in self._events:
                json.dump(event.to_dict(), f, sort_keys=True)
                f.write("\n")

    @classmethod
    def from_jsonl(cls, path: Path) -> "EventLog":
        """Deserialize event log from JSONL file."""
        log = cls()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event_data = json.loads(line)
                event = Event.from_dict(event_data)
                log.append(event)
        return log

    @property
    def events(self) -> List[Event]:
        """Get all events (read-only)."""
        return self._events.copy()

    def __len__(self) -> int:
        """Number of events in log."""
        return len(self._events)

    def __getitem__(self, index: int) -> Event:
        """Get event by index."""
        return self._events[index]
