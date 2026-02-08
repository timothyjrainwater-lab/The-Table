"""M1 Character Sheet UI v0 — Terminal-based display.

Implements CHARACTER_SHEET_UI_CONTRACT.md:
- Subscribes to state changes
- Displays current state (read-only)
- Computed derived values on demand
- No player editing of engine-owned state

This is a v0 minimal implementation for the solo vertical slice.

Reference: docs/design/CHARACTER_SHEET_UI_CONTRACT.md
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime

from aidm.core.state import WorldState


# ==============================================================================
# D&D 3.5e CLASS PROGRESSIONS (PHB p.22, Table 3-1 through 3-13)
# ==============================================================================

# BAB types: "full" = +1/level, "medium" = 3/4, "poor" = 1/2
# Save types: "good" = 2 + level//2, "poor" = level//3

# (bab_type, fort_save_type, ref_save_type, will_save_type)
CLASS_PROGRESSIONS: Dict[str, Tuple[str, str, str, str]] = {
    "Fighter":     ("full",   "good", "poor", "poor"),
    "Barbarian":   ("full",   "good", "poor", "poor"),
    "Paladin":     ("full",   "good", "poor", "poor"),
    "Ranger":      ("full",   "good", "poor", "poor"),
    "Monk":        ("full",   "good", "good", "good"),
    "Rogue":       ("medium", "poor", "good", "poor"),
    "Bard":        ("medium", "poor", "good", "good"),
    "Cleric":      ("full",   "good", "poor", "good"),
    "Druid":       ("medium", "good", "poor", "good"),
    "Wizard":      ("poor",   "poor", "poor", "good"),
    "Sorcerer":    ("poor",   "poor", "poor", "good"),
    # NPC classes
    "Warrior":     ("full",   "good", "poor", "poor"),
    "Adept":       ("poor",   "poor", "poor", "good"),
    "Aristocrat":  ("medium", "poor", "poor", "good"),
    "Commoner":    ("poor",   "poor", "poor", "poor"),
    "Expert":      ("medium", "poor", "poor", "good"),
}


def _compute_bab(level: int, bab_type: str) -> int:
    """Compute base attack bonus from level and BAB type."""
    if bab_type == "full":
        return level
    elif bab_type == "medium":
        return level * 3 // 4
    else:  # poor
        return level // 2


def _compute_base_save(level: int, save_type: str) -> int:
    """Compute base save bonus from level and save type."""
    if save_type == "good":
        return 2 + level // 2
    else:  # poor
        return level // 3


@dataclass
class CharacterData:
    """Character data extracted from world state.

    Separates base attributes, persistent state, and derived values
    per CHARACTER_SHEET_UI_CONTRACT.md Section 4.
    """

    # Identity
    entity_id: str
    name: str = ""

    # Base Attributes (authored data)
    race: str = "Human"
    size: str = "Medium"
    class_name: str = "Fighter"
    level: int = 1

    # Ability scores
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    # Persistent State (engine-owned)
    max_hp: int = 10
    current_hp: int = 10
    conditions: List[str] = field(default_factory=list)
    team: str = "party"
    defeated: bool = False
    position: Optional[Dict[str, int]] = None

    # Derived values are computed on demand, not stored

    @property
    def hp_display(self) -> str:
        """Format HP for display."""
        return f"{self.current_hp}/{self.max_hp}"

    @property
    def str_modifier(self) -> int:
        """Strength modifier."""
        return (self.strength - 10) // 2

    @property
    def dex_modifier(self) -> int:
        """Dexterity modifier."""
        return (self.dexterity - 10) // 2

    @property
    def con_modifier(self) -> int:
        """Constitution modifier."""
        return (self.constitution - 10) // 2

    @property
    def int_modifier(self) -> int:
        """Intelligence modifier."""
        return (self.intelligence - 10) // 2

    @property
    def wis_modifier(self) -> int:
        """Wisdom modifier."""
        return (self.wisdom - 10) // 2

    @property
    def cha_modifier(self) -> int:
        """Charisma modifier."""
        return (self.charisma - 10) // 2

    @property
    def _class_progression(self) -> Tuple[str, str, str, str]:
        """Get (bab_type, fort_type, ref_type, will_type) for this class."""
        return CLASS_PROGRESSIONS.get(self.class_name, ("full", "good", "poor", "poor"))

    @property
    def base_attack_bonus(self) -> int:
        """BAB based on class progression (PHB p.22)."""
        bab_type = self._class_progression[0]
        return _compute_bab(self.level, bab_type)

    @property
    def melee_attack_bonus(self) -> int:
        """Melee attack bonus (BAB + STR)."""
        return self.base_attack_bonus + self.str_modifier

    @property
    def ranged_attack_bonus(self) -> int:
        """Ranged attack bonus (BAB + DEX)."""
        return self.base_attack_bonus + self.dex_modifier

    @property
    def base_ac(self) -> int:
        """Base AC (10 + DEX + armor)."""
        # Simplified: no armor tracking in M1
        return 10 + self.dex_modifier

    @property
    def fortitude_save(self) -> int:
        """Fort save (base + CON modifier)."""
        save_type = self._class_progression[1]
        base = _compute_base_save(self.level, save_type)
        return base + self.con_modifier

    @property
    def reflex_save(self) -> int:
        """Reflex save (base + DEX modifier)."""
        save_type = self._class_progression[2]
        base = _compute_base_save(self.level, save_type)
        return base + self.dex_modifier

    @property
    def will_save(self) -> int:
        """Will save (base + WIS modifier)."""
        save_type = self._class_progression[3]
        base = _compute_base_save(self.level, save_type)
        return base + self.wis_modifier

    @property
    def status_line(self) -> str:
        """One-line status summary."""
        status_parts = []
        if self.defeated:
            status_parts.append("DEFEATED")
        if self.conditions:
            status_parts.extend(self.conditions)
        return ", ".join(status_parts) if status_parts else "OK"

    @classmethod
    def from_entity(cls, entity_id: str, entity_data: Dict[str, Any]) -> "CharacterData":
        """Extract character data from world state entity."""
        return cls(
            entity_id=entity_id,
            name=entity_data.get("name", entity_id),
            race=entity_data.get("race", "Human"),
            size=entity_data.get("size", "Medium"),
            class_name=entity_data.get("class", "Fighter"),
            level=entity_data.get("level", 1),
            strength=entity_data.get("strength", 10),
            dexterity=entity_data.get("dexterity", 10),
            constitution=entity_data.get("constitution", 10),
            intelligence=entity_data.get("intelligence", 10),
            wisdom=entity_data.get("wisdom", 10),
            charisma=entity_data.get("charisma", 10),
            max_hp=entity_data.get("max_hp", entity_data.get("hp", 10)),
            current_hp=entity_data.get("hp", 10),
            conditions=entity_data.get("conditions", []),
            team=entity_data.get("team", "party"),
            defeated=entity_data.get("defeated", False),
            position=entity_data.get("position"),
        )


# Type alias for state change callback
StateChangeCallback = Callable[[WorldState], None]


class CharacterSheetUI:
    """Terminal-based character sheet display.

    Subscribes to world state changes and displays character information.
    This is a v0 implementation - read-only display, no editing.
    """

    def __init__(self, entity_id: str):
        """Initialize for a specific character.

        Args:
            entity_id: The entity to display
        """
        self.entity_id = entity_id
        self._current_data: Optional[CharacterData] = None
        self._callbacks: List[StateChangeCallback] = []
        self._last_update: Optional[datetime] = None

    def update(self, world_state: WorldState) -> None:
        """Update character data from world state.

        Called when world state changes.
        """
        if self.entity_id not in world_state.entities:
            self._current_data = None
            return

        entity_data = world_state.entities[self.entity_id]
        self._current_data = CharacterData.from_entity(self.entity_id, entity_data)
        self._last_update = datetime.utcnow()

        # Notify callbacks
        for callback in self._callbacks:
            callback(world_state)

    def subscribe(self, callback: StateChangeCallback) -> None:
        """Subscribe to state change notifications."""
        self._callbacks.append(callback)

    def unsubscribe(self, callback: StateChangeCallback) -> None:
        """Unsubscribe from state change notifications."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    @property
    def data(self) -> Optional[CharacterData]:
        """Get current character data."""
        return self._current_data

    def render_compact(self) -> str:
        """Render compact one-line status.

        Example: "Theron (Fighter 3) HP: 25/28 [Poisoned] AC: 17"
        """
        if self._current_data is None:
            return f"[{self.entity_id}: Not Found]"

        d = self._current_data
        parts = [
            f"{d.name} ({d.class_name} {d.level})",
            f"HP: {d.hp_display}",
        ]

        if d.conditions:
            parts.append(f"[{', '.join(d.conditions)}]")

        parts.append(f"AC: {d.base_ac}")

        return " | ".join(parts)

    def render_full(self) -> str:
        """Render full character sheet.

        Returns multi-line formatted character sheet.
        """
        if self._current_data is None:
            return f"Character not found: {self.entity_id}"

        d = self._current_data
        lines = []

        # Header
        lines.append("=" * 50)
        lines.append(f"  {d.name.upper()}")
        lines.append(f"  {d.race} {d.class_name} {d.level}")
        lines.append("=" * 50)

        # Status
        lines.append("")
        lines.append(f"  Status: {d.status_line}")
        lines.append(f"  HP: {d.hp_display}")
        lines.append("")

        # Ability Scores
        lines.append("  ABILITY SCORES")
        lines.append("-" * 50)
        lines.append(f"  STR: {d.strength:2d} ({d.str_modifier:+d})")
        lines.append(f"  DEX: {d.dexterity:2d} ({d.dex_modifier:+d})")
        lines.append(f"  CON: {d.constitution:2d} ({d.con_modifier:+d})")
        lines.append(f"  INT: {d.intelligence:2d} ({d.int_modifier:+d})")
        lines.append(f"  WIS: {d.wisdom:2d} ({d.wis_modifier:+d})")
        lines.append(f"  CHA: {d.charisma:2d} ({d.cha_modifier:+d})")
        lines.append("")

        # Combat
        lines.append("  COMBAT")
        lines.append("-" * 50)
        lines.append(f"  AC: {d.base_ac}")
        lines.append(f"  BAB: +{d.base_attack_bonus}")
        lines.append(f"  Melee: +{d.melee_attack_bonus}")
        lines.append(f"  Ranged: +{d.ranged_attack_bonus}")
        lines.append("")

        # Saves
        lines.append("  SAVING THROWS")
        lines.append("-" * 50)
        lines.append(f"  Fort: +{d.fortitude_save}")
        lines.append(f"  Ref:  +{d.reflex_save}")
        lines.append(f"  Will: +{d.will_save}")
        lines.append("")

        # Position (if in combat)
        if d.position:
            lines.append("  POSITION")
            lines.append("-" * 50)
            lines.append(f"  ({d.position.get('x', '?')}, {d.position.get('y', '?')})")
            lines.append("")

        lines.append("=" * 50)

        return "\n".join(lines)

    def render_combat_status(self) -> str:
        """Render minimal combat status.

        For display during combat encounters.
        """
        if self._current_data is None:
            return f"[{self.entity_id}: ???]"

        d = self._current_data
        status = "DEFEATED" if d.defeated else f"HP: {d.hp_display}"
        conditions = f" [{', '.join(d.conditions)}]" if d.conditions else ""

        return f"{d.name}: {status}{conditions}"


class PartySheet:
    """Aggregate view of multiple characters.

    Displays party-level status for DM/player overview.
    """

    def __init__(self):
        """Initialize empty party sheet."""
        self._sheets: Dict[str, CharacterSheetUI] = {}

    def add_character(self, entity_id: str) -> CharacterSheetUI:
        """Add a character to the party view."""
        sheet = CharacterSheetUI(entity_id)
        self._sheets[entity_id] = sheet
        return sheet

    def remove_character(self, entity_id: str) -> None:
        """Remove a character from the party view."""
        if entity_id in self._sheets:
            del self._sheets[entity_id]

    def update_all(self, world_state: WorldState) -> None:
        """Update all character sheets from world state."""
        for sheet in self._sheets.values():
            sheet.update(world_state)

    def render_party_status(self) -> str:
        """Render party status overview."""
        if not self._sheets:
            return "[No characters in party]"

        lines = ["PARTY STATUS", "=" * 40]

        for entity_id, sheet in sorted(self._sheets.items()):
            lines.append(sheet.render_compact())

        lines.append("=" * 40)
        return "\n".join(lines)

    def render_combat_tracker(self) -> str:
        """Render combat tracker view."""
        if not self._sheets:
            return "[No combatants]"

        lines = ["COMBAT", "-" * 30]

        for entity_id, sheet in sorted(self._sheets.items()):
            lines.append(f"  {sheet.render_combat_status()}")

        lines.append("-" * 30)
        return "\n".join(lines)
