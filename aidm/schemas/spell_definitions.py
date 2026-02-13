"""Backward-compatible re-export shim.

The spell definitions registry has been relocated to aidm.data.spell_definitions
to respect the boundary law: schemas must not import from core.  All public
names are re-exported here so that existing ``from aidm.schemas.spell_definitions
import ...`` statements continue to work without modification.
"""

from aidm.data.spell_definitions import (  # noqa: F401 — re-export
    SPELL_REGISTRY,
    get_spell,
    get_spells_by_level,
    get_spells_by_school,
    get_damage_spells,
    get_healing_spells,
)
