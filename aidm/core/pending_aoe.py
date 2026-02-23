"""PendingAoE dataclass — confirm-gate state for AoE spells.

WO-BURST-003-AOE-001: Confirm-Gated AoE Spell Overlay.

When a player casts an AoE spell, the engine creates a PendingAoE record
instead of resolving immediately.  The record is stored on WorldState and
cleared when the player confirms or cancels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from aidm.core.aoe_rasterizer import AoEResult


@dataclass(frozen=True)
class PendingAoE:
    """Immutable snapshot of a pending AoE spell awaiting player confirmation.

    Fields
    ------
    spell_name : str
        Human-readable name of the spell (e.g. "Fireball").
    caster_id : str
        Entity ID of the caster.
    origin_x : int
        Target point x-coordinate (grid squares).
    origin_y : int
        Target point y-coordinate (grid squares).
    aoe_result : AoEResult
        Pre-computed rasterization result for the targeted point.
    save_dc : int | None
        Saving throw DC, or None for no-save AoE effects.
    spell_data : dict | None
        Raw spell dict carried forward so _confirm_aoe can resolve it.
        Stored as a tuple of items for hashability.
    """

    spell_name: str
    caster_id: str
    origin_x: int
    origin_y: int
    aoe_result: AoEResult
    save_dc: Optional[int]
    # Carry raw spell data through confirmation; stored as frozenset of items
    # so the frozen dataclass can hash it.  Callers use PendingAoE.spell_dict.
    _spell_items: tuple = ()

    @property
    def spell_dict(self) -> dict:
        """Reconstruct spell data dict from the stored item tuple."""
        return dict(self._spell_items)
