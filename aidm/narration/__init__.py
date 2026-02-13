"""M1 Narration module for human-readable descriptions.

Components:
- Narrator: Main narration class
- NarrationContext: Context for narration generation
- NarrationTemplates: Deterministic template library
- NarrationResult: Narration output with provenance tag
- narrate_attack: Convenience function for attacks
"""

from aidm.narration.narrator import (
    Narrator,
    NarrationContext,
    NarrationTemplates,
    create_default_narrator,
    narrate_attack,
)
from aidm.narration.guarded_narration_service import NarrationResult

__all__ = [
    "Narrator",
    "NarrationContext",
    "NarrationTemplates",
    "NarrationResult",
    "create_default_narrator",
    "narrate_attack",
]
