"""Monster doctrine schemas for tactical envelope enforcement.

Defines capability-based constraints for monster behavior during combat.
This is NOT scoring or mercy - it's RAW-legal tactical gating based on
creature intelligence, wisdom, type, and Monster Manual behavior text.
"""

from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict, Any
from aidm.schemas.citation import Citation
from aidm.schemas.attack import Weapon


# Doctrine tags for behavior classification
DoctrineTag = Literal[
    "mindless_feeder",
    "animal_predator",
    "swarm_instinct",
    "cowardly",
    "fanatical",
    "disciplined",
    "pack_hunter",
    "ambusher",
    "tactician",
    "assassin",
    "guardian",
    "berserker",
    "caster_controller"
]


# Intelligence bands (derived from INT score)
IntelligenceBand = Literal[
    "NO_INT",       # None or "—"
    "INT_1",        # 1
    "INT_2",        # 2
    "INT_3_4",      # 3-4
    "INT_5_7",      # 5-7
    "INT_8_10",     # 8-10
    "INT_11_13",    # 11-13
    "INT_14_16",    # 14-16
    "INT_17_PLUS"   # 17+
]


# Wisdom bands (derived from WIS score)
WisdomBand = Literal[
    "WIS_LOW",       # 1-7
    "WIS_AVG",       # 8-12
    "WIS_HIGH",      # 13-16
    "WIS_EXCELLENT"  # 17+
]


# Tactic classes (capability gates, not scoring)
TacticClass = Literal[
    "focus_fire",
    "target_support",
    "target_controller",
    "setup_flank",
    "use_cover",
    "bait_and_switch",
    "deny_actions_chain",
    "retreat_regroup",
    "ignore_downs_keep_killing",
    "fight_to_the_death",
    "attack_nearest",
    "random_target"
]


@dataclass
class MonsterDoctrine:
    """
    Tactical envelope for a monster type.

    Constrains combat behavior based on INT/WIS and creature nature.
    This is capability gating - NOT mercy, sympathy, or nerfing.
    """

    monster_id: str
    """Stable identifier for monster type"""

    source: str
    """Source book (e.g., 'MM', 'MMI', 'FFoE')"""

    int_score: Optional[int]
    """Intelligence score (None for mindless/no INT)"""

    wis_score: Optional[int]
    """Wisdom score (None if not specified)"""

    creature_type: str
    """Type from MM (e.g., 'undead', 'aberration', 'beast')"""

    tags: List[DoctrineTag] = field(default_factory=list)
    """Behavior classification tags"""

    notes: Optional[str] = None
    """Short tactical notes (not narrative)"""

    citations: List[Dict[str, Any]] = field(default_factory=list)
    """Citations to MM behavior text"""

    # CP-13: Combat parameters for monster combat intent mapping
    weapon: Optional[Weapon] = None
    """Weapon stats for combat resolution (optional, required for attack mapping)"""

    attack_bonus: Optional[int] = None
    """Total attack bonus for combat resolution (optional, required for attack mapping)"""

    # Derived fields (populated by derive_tactical_envelope)
    int_band: Optional[IntelligenceBand] = None
    wis_band: Optional[WisdomBand] = None
    allowed_tactics: List[TacticClass] = field(default_factory=list)
    forbidden_tactics: List[TacticClass] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "monster_id": self.monster_id,
            "source": self.source,
            "creature_type": self.creature_type,
            "tags": list(self.tags),
            "citations": self.citations
        }

        # INT score (null for mindless)
        if self.int_score is not None:
            result["int_score"] = self.int_score
        else:
            result["int_score"] = None

        # WIS score (null if not specified)
        if self.wis_score is not None:
            result["wis_score"] = self.wis_score
        else:
            result["wis_score"] = None

        # Optional notes
        if self.notes is not None:
            result["notes"] = self.notes

        # CP-13: Combat parameters
        if self.weapon is not None:
            result["weapon"] = {
                "damage_dice": self.weapon.damage_dice,
                "damage_bonus": self.weapon.damage_bonus,
                "damage_type": self.weapon.damage_type,
                "critical_multiplier": self.weapon.critical_multiplier
            }

        if self.attack_bonus is not None:
            result["attack_bonus"] = self.attack_bonus

        # Derived fields (if populated)
        if self.int_band is not None:
            result["int_band"] = self.int_band

        if self.wis_band is not None:
            result["wis_band"] = self.wis_band

        if self.allowed_tactics:
            result["allowed_tactics"] = list(self.allowed_tactics)

        if self.forbidden_tactics:
            result["forbidden_tactics"] = list(self.forbidden_tactics)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonsterDoctrine":
        """Create from dictionary."""
        # CP-13: Deserialize weapon if present
        weapon = None
        if "weapon" in data and data["weapon"] is not None:
            weapon = Weapon(
                damage_dice=data["weapon"]["damage_dice"],
                damage_bonus=data["weapon"]["damage_bonus"],
                damage_type=data["weapon"]["damage_type"],
                critical_multiplier=data["weapon"].get("critical_multiplier", 2)
            )

        return cls(
            monster_id=data["monster_id"],
            source=data["source"],
            int_score=data.get("int_score"),
            wis_score=data.get("wis_score"),
            creature_type=data["creature_type"],
            tags=data.get("tags", []),
            notes=data.get("notes"),
            citations=data.get("citations", []),
            weapon=weapon,
            attack_bonus=data.get("attack_bonus"),
            int_band=data.get("int_band"),
            wis_band=data.get("wis_band"),
            allowed_tactics=data.get("allowed_tactics", []),
            forbidden_tactics=data.get("forbidden_tactics", [])
        )
