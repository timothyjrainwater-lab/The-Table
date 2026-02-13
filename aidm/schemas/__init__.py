"""Frozen dataclass schemas for AIDM layer boundaries.

This package defines the data-only contracts exchanged between AIDM layers
(core, runtime, lens).  Every schema is a plain ``dataclasses.dataclass``
— no ORM, no Pydantic, no runtime magic.
"""

from aidm.schemas.position import Position
from aidm.schemas.engine_result import (
    EngineResult,
    EngineResultBuilder,
    EngineResultStatus,
    RollResult,
    StateChange,
)
from aidm.schemas.content_pack import (
    ContentPack,
    MechanicalCreatureTemplate,
    MechanicalFeatTemplate,
    MechanicalSpellTemplate,
)

__all__ = [
    # position
    "Position",
    # engine_result
    "EngineResult",
    "EngineResultBuilder",
    "EngineResultStatus",
    "RollResult",
    "StateChange",
    # content_pack
    "ContentPack",
    "MechanicalCreatureTemplate",
    "MechanicalFeatTemplate",
    "MechanicalSpellTemplate",
]
