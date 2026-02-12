"""Job queue stub — interface-only for asset replenishment.

Records replenishment requests but does NOT execute them. Actual image/TTS
generation is out of scope for WO-CODE-DISCOVERY-001.

WO-CODE-DISCOVERY-001: Bestiary Knowledge Mask + Asset Binding Pools
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from aidm.schemas.asset_binding import ReplenishmentRequest


class JobQueueStub:
    """Stub job queue that records requests without executing them.

    This is the interface that a real generation backend would implement.
    For now, it only records requests for inspection and testing.
    """

    def __init__(self) -> None:
        self._pending: List[ReplenishmentRequest] = []
        self._completed: List[Dict[str, Any]] = []

    def enqueue(self, request: ReplenishmentRequest) -> None:
        """Record a replenishment request."""
        self._pending.append(request)

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def pending_requests(self) -> List[ReplenishmentRequest]:
        return list(self._pending)

    def get_pending_for_category(self, category_id: str) -> List[ReplenishmentRequest]:
        """Get all pending requests for a specific category."""
        return [r for r in self._pending if r.category_id == category_id]

    def clear(self) -> None:
        """Clear all pending requests (for testing)."""
        self._pending.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pending": [r.to_dict() for r in self._pending],
            "completed": list(self._completed),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "JobQueueStub":
        queue = cls()
        for r_data in data.get("pending", []):
            queue.enqueue(ReplenishmentRequest(
                category_id=r_data["category_id"],
                count=r_data["count"],
                priority=r_data.get("priority", 0),
            ))
        queue._completed = list(data.get("completed", []))
        return queue
