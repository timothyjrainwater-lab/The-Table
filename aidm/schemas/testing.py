"""Scenario configuration schemas for integration testing.

Defines data structures for multi-encounter stress tests:
- TerrainPlacement: Individual terrain feature placement
- AttackConfig: Weapon/attack configuration for combatants
- SpellConfig: Spell configuration for casters
- CombatantConfig: Complete combatant configuration
- ScenarioConfig: Full scenario definition

WO-016: Multi-Encounter Stress Test Suite
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from aidm.schemas.position import Position


# ==============================================================================
# COVER DEGREE — Cover types for terrain
# ==============================================================================

class CoverDegree(Enum):
    """Cover degree types per PHB p.150.

    - NONE: No cover (0 AC bonus)
    - PARTIAL: Half cover (+2 AC, +1 Reflex)
    - IMPROVED: 3/4 cover (+4 AC, +2 Reflex)
    - TOTAL: Full cover (cannot be targeted)
    - SOFT: Soft cover from creatures (+4 AC, no Reflex)
    """
    NONE = "none"
    PARTIAL = "partial"
    IMPROVED = "improved"
    TOTAL = "total"
    SOFT = "soft"


# ==============================================================================
# TERRAIN PLACEMENT — Individual terrain feature
# ==============================================================================

@dataclass
class TerrainPlacement:
    """Configuration for placing terrain at a grid position.

    Defines terrain type and its mechanical effects on cover,
    line of sight/effect, and elevation.
    """

    coord: Position
    """Grid position of the terrain feature."""

    terrain_type: str
    """Type of terrain: 'wall', 'table', 'pillar', 'boulder', 'stairs',
    'door_open', 'door_closed', 'window', 'pit', 'rubble'."""

    cover_provided: Optional[CoverDegree] = None
    """Cover degree this terrain provides to adjacent creatures."""

    blocks_los: bool = False
    """Whether this terrain blocks line of sight."""

    blocks_loe: bool = False
    """Whether this terrain blocks line of effect."""

    elevation: int = 0
    """Elevation in feet (for higher ground bonuses)."""

    height: int = 0
    """Height in feet (for LOS occlusion calculation)."""

    is_difficult: bool = False
    """Whether this is difficult terrain (double movement cost)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "coord": self.coord.to_dict(),
            "terrain_type": self.terrain_type,
            "cover_provided": self.cover_provided.value if self.cover_provided else None,
            "blocks_los": self.blocks_los,
            "blocks_loe": self.blocks_loe,
            "elevation": self.elevation,
            "height": self.height,
            "is_difficult": self.is_difficult,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TerrainPlacement':
        """Deserialize from dictionary."""
        cover = None
        if data.get("cover_provided"):
            cover = CoverDegree(data["cover_provided"])
        return cls(
            coord=Position.from_dict(data["coord"]),
            terrain_type=data["terrain_type"],
            cover_provided=cover,
            blocks_los=data.get("blocks_los", False),
            blocks_loe=data.get("blocks_loe", False),
            elevation=data.get("elevation", 0),
            height=data.get("height", 0),
            is_difficult=data.get("is_difficult", False),
        )


# ==============================================================================
# ATTACK CONFIG — Weapon and attack parameters
# ==============================================================================

@dataclass
class AttackConfig:
    """Configuration for a single attack type.

    Defines weapon properties and attack bonus for combat resolution.
    """

    name: str
    """Attack name (e.g., 'longsword', 'shortbow')."""

    attack_bonus: int
    """Total attack bonus (BAB + ability mod + misc)."""

    damage_dice: str
    """Damage dice expression (e.g., '1d8', '2d6')."""

    damage_bonus: int
    """Flat damage bonus."""

    damage_type: str
    """Damage type: 'slashing', 'piercing', 'bludgeoning', etc."""

    is_ranged: bool = False
    """Whether this is a ranged attack."""

    range_increment: int = 0
    """Range increment in feet (0 for melee)."""

    critical_range: int = 20
    """Minimum d20 roll for critical threat."""

    critical_multiplier: int = 2
    """Critical hit damage multiplier."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "attack_bonus": self.attack_bonus,
            "damage_dice": self.damage_dice,
            "damage_bonus": self.damage_bonus,
            "damage_type": self.damage_type,
            "is_ranged": self.is_ranged,
            "range_increment": self.range_increment,
            "critical_range": self.critical_range,
            "critical_multiplier": self.critical_multiplier,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttackConfig':
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            attack_bonus=data["attack_bonus"],
            damage_dice=data["damage_dice"],
            damage_bonus=data["damage_bonus"],
            damage_type=data["damage_type"],
            is_ranged=data.get("is_ranged", False),
            range_increment=data.get("range_increment", 0),
            critical_range=data.get("critical_range", 20),
            critical_multiplier=data.get("critical_multiplier", 2),
        )


# ==============================================================================
# SPELL CONFIG — Spell parameters for casters
# ==============================================================================

@dataclass
class SpellConfig:
    """Configuration for a prepared/known spell.

    Defines spell properties for casting during combat.
    """

    spell_id: str
    """Spell identifier (e.g., 'fireball', 'magic_missile')."""

    spell_level: int
    """Spell level (0-9)."""

    caster_level: int
    """Effective caster level for the spell."""

    dc: int
    """Save DC if applicable."""

    uses_remaining: int = 1
    """Number of times this spell can be cast."""

    is_aoe: bool = False
    """Whether this is an area of effect spell."""

    aoe_shape: Optional[str] = None
    """AoE shape: 'burst', 'cone', 'line', 'spread'."""

    aoe_radius_ft: int = 0
    """AoE radius in feet (for bursts/spreads)."""

    aoe_length_ft: int = 0
    """AoE length in feet (for cones/lines)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "spell_id": self.spell_id,
            "spell_level": self.spell_level,
            "caster_level": self.caster_level,
            "dc": self.dc,
            "uses_remaining": self.uses_remaining,
            "is_aoe": self.is_aoe,
            "aoe_shape": self.aoe_shape,
            "aoe_radius_ft": self.aoe_radius_ft,
            "aoe_length_ft": self.aoe_length_ft,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpellConfig':
        """Deserialize from dictionary."""
        return cls(
            spell_id=data["spell_id"],
            spell_level=data["spell_level"],
            caster_level=data["caster_level"],
            dc=data["dc"],
            uses_remaining=data.get("uses_remaining", 1),
            is_aoe=data.get("is_aoe", False),
            aoe_shape=data.get("aoe_shape"),
            aoe_radius_ft=data.get("aoe_radius_ft", 0),
            aoe_length_ft=data.get("aoe_length_ft", 0),
        )


# ==============================================================================
# COMBATANT CONFIG — Complete combatant definition
# ==============================================================================

@dataclass
class CombatantConfig:
    """Configuration for a single combatant in a scenario.

    Defines all mechanical properties needed for combat simulation.
    """

    name: str
    """Unique identifier for this combatant."""

    team: str
    """Team affiliation: 'party' or 'enemy'."""

    position: Position
    """Starting position on the grid."""

    size: str
    """Size category: 'Fine', 'Diminutive', 'Tiny', 'Small', 'Medium',
    'Large', 'Huge', 'Gargantuan', 'Colossal'."""

    hp: int
    """Maximum (and starting) hit points."""

    ac: int
    """Armor Class."""

    attacks: List[AttackConfig]
    """Available attack options."""

    spells: Optional[List[SpellConfig]] = None
    """Available spells (None if non-caster)."""

    reach: int = 5
    """Reach in feet (5 for most Medium creatures, 10 for Large)."""

    combat_reflexes: bool = False
    """Whether this combatant has Combat Reflexes feat."""

    max_aoo_per_round: int = 1
    """Maximum attacks of opportunity per round (1 unless Combat Reflexes)."""

    initiative_bonus: int = 0
    """Initiative modifier."""

    bab: int = 0
    """Base Attack Bonus (for iterative attacks)."""

    str_mod: int = 0
    """Strength modifier (for melee damage)."""

    dex_mod: int = 0
    """Dexterity modifier (for ranged attacks, initiative, Reflex saves)."""

    con_mod: int = 0
    """Constitution modifier (for Fortitude saves)."""

    wis_mod: int = 0
    """Wisdom modifier (for Will saves)."""

    save_fort: int = 0
    """Fortitude save total."""

    save_ref: int = 0
    """Reflex save total."""

    save_will: int = 0
    """Will save total."""

    speed: int = 30
    """Base movement speed in feet."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "team": self.team,
            "position": self.position.to_dict(),
            "size": self.size,
            "hp": self.hp,
            "ac": self.ac,
            "attacks": [a.to_dict() for a in self.attacks],
            "spells": [s.to_dict() for s in self.spells] if self.spells else None,
            "reach": self.reach,
            "combat_reflexes": self.combat_reflexes,
            "max_aoo_per_round": self.max_aoo_per_round,
            "initiative_bonus": self.initiative_bonus,
            "bab": self.bab,
            "str_mod": self.str_mod,
            "dex_mod": self.dex_mod,
            "con_mod": self.con_mod,
            "wis_mod": self.wis_mod,
            "save_fort": self.save_fort,
            "save_ref": self.save_ref,
            "save_will": self.save_will,
            "speed": self.speed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CombatantConfig':
        """Deserialize from dictionary."""
        attacks = [AttackConfig.from_dict(a) for a in data["attacks"]]
        spells = None
        if data.get("spells"):
            spells = [SpellConfig.from_dict(s) for s in data["spells"]]

        return cls(
            name=data["name"],
            team=data["team"],
            position=Position.from_dict(data["position"]),
            size=data["size"],
            hp=data["hp"],
            ac=data["ac"],
            attacks=attacks,
            spells=spells,
            reach=data.get("reach", 5),
            combat_reflexes=data.get("combat_reflexes", False),
            max_aoo_per_round=data.get("max_aoo_per_round", 1),
            initiative_bonus=data.get("initiative_bonus", 0),
            bab=data.get("bab", 0),
            str_mod=data.get("str_mod", 0),
            dex_mod=data.get("dex_mod", 0),
            con_mod=data.get("con_mod", 0),
            wis_mod=data.get("wis_mod", 0),
            save_fort=data.get("save_fort", 0),
            save_ref=data.get("save_ref", 0),
            save_will=data.get("save_will", 0),
            speed=data.get("speed", 30),
        )


# ==============================================================================
# SCENARIO CONFIG — Complete scenario definition
# ==============================================================================

@dataclass
class ScenarioConfig:
    """Configuration for a complete combat scenario.

    Defines grid dimensions, terrain, combatants, and simulation parameters.
    """

    name: str
    """Scenario name for identification."""

    grid_width: int
    """Grid width in 5-foot squares."""

    grid_height: int
    """Grid height in 5-foot squares."""

    terrain: List[TerrainPlacement]
    """List of terrain feature placements."""

    combatants: List[CombatantConfig]
    """List of combatant configurations."""

    round_limit: int
    """Maximum number of rounds to simulate."""

    seed: int
    """RNG seed for deterministic simulation."""

    description: str = ""
    """Optional scenario description."""

    victory_condition: str = "elimination"
    """Victory condition: 'elimination', 'round_limit', 'objective'."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "terrain": [t.to_dict() for t in self.terrain],
            "combatants": [c.to_dict() for c in self.combatants],
            "round_limit": self.round_limit,
            "seed": self.seed,
            "description": self.description,
            "victory_condition": self.victory_condition,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScenarioConfig':
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            grid_width=data["grid_width"],
            grid_height=data["grid_height"],
            terrain=[TerrainPlacement.from_dict(t) for t in data["terrain"]],
            combatants=[CombatantConfig.from_dict(c) for c in data["combatants"]],
            round_limit=data["round_limit"],
            seed=data["seed"],
            description=data.get("description", ""),
            victory_condition=data.get("victory_condition", "elimination"),
        )

    def get_party_combatants(self) -> List[CombatantConfig]:
        """Get all combatants on the 'party' team."""
        return [c for c in self.combatants if c.team == "party"]

    def get_enemy_combatants(self) -> List[CombatantConfig]:
        """Get all combatants on the 'enemy' team."""
        return [c for c in self.combatants if c.team == "enemy"]
