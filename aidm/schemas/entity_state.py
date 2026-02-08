"""Minimal EntityState schema extension for SKR-002 Phase 2.

This file exists solely to demonstrate **entity state integration** of the
`permanent_stat_modifiers` field required by SKR-002.

BINDING CONSTRAINTS:
- No algorithms (no derived stat recompute, no event emission).
- No CP-16 schema redefinition. Temporary modifiers are represented as an
  opaque field for separation checks only.

If a fuller EntityState schema already exists in the engine, this file should be
merged into that canonical schema instead of co-existing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from .permanent_stats import PermanentStatModifiers


@dataclass(frozen=True)
class EntityState:
    """Entity state (schema-only).

    - base_stats are immutable post-creation (enforced elsewhere).
    - permanent_stat_modifiers is the SKR-002 permanent layer.
    - temporary_modifiers is an opaque placeholder representing CP-16.
      SKR-002 must remain separate from this field.
    """

    entity_id: str
    base_stats: Dict[str, int]
    permanent_stat_modifiers: PermanentStatModifiers = field(
        default_factory=PermanentStatModifiers
    )

    # CP-16 placeholder: do not interpret here.
    temporary_modifiers: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise ValueError("entity_id must be a non-empty string")
        if not isinstance(self.base_stats, dict):
            raise ValueError("base_stats must be a dict")
        for k, v in self.base_stats.items():
            if not isinstance(k, str):
                raise ValueError("base_stats keys must be strings")
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError("base_stats values must be ints")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "base_stats": dict(self.base_stats),
            "permanent_stat_modifiers": self.permanent_stat_modifiers.to_dict(),
            "temporary_modifiers": dict(self.temporary_modifiers),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EntityState":
        if not isinstance(data, Mapping):
            raise ValueError("EntityState.from_dict expects a mapping")
        return cls(
            entity_id=data["entity_id"],
            base_stats=dict(data.get("base_stats", {})),
            permanent_stat_modifiers=PermanentStatModifiers.from_dict(
                data.get("permanent_stat_modifiers", {})
            ),
            temporary_modifiers=dict(data.get("temporary_modifiers", {})),
        )
