"""M1 Narration module for human-readable descriptions.

Components:
- Narrator: Main narration class
- NarrationContext: Context for narration generation
- NarrationTemplates: Deterministic template library
- narrate_attack: Convenience function for attacks
"""

from aidm.narration.narrator import (
    Narrator,
    NarrationContext,
    NarrationTemplates,
    create_default_narrator,
    narrate_attack,
)

__all__ = [
    "Narrator",
    "NarrationContext",
    "NarrationTemplates",
    "create_default_narrator",
    "narrate_attack",
]
