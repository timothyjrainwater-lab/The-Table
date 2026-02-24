"""Voice intent contract schemas for player actions.

Defines structured, JSON-serializable intents accepted from voice layer (ASR/NLU).
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any, Literal
import warnings

# CP-001: Canonical position type (replaces legacy GridPoint below)
from aidm.schemas.position import Position


class IntentParseError(Exception):
    """Raised when an intent has invalid structure or values."""
    pass


@dataclass
class GridPoint:
    """2D grid coordinate.

    DEPRECATED: Use aidm.schemas.position.Position instead.
    This class will be removed in CP-002.
    """

    x: int
    y: int

    def __post_init__(self):
        """Validate and warn about deprecation."""
        warnings.warn(
            "GridPoint in intents.py is deprecated. Use aidm.schemas.position.Position instead. "
            "This class will be removed in CP-002.",
            DeprecationWarning,
            stacklevel=2
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridPoint":
        """Create from dictionary."""
        return cls(x=data["x"], y=data["y"])


@dataclass
class CastSpellIntent:
    """Intent to cast a spell."""

    type: Literal["cast_spell"] = "cast_spell"
    spell_name: str = ""
    target_mode: Literal["point", "creature", "self", "none"] = "none"
    metamagic: List[str] = field(default_factory=list)
    # Valid values: "empower", "maximize", "extend", "heighten", "quicken"
    heighten_to_level: Optional[int] = None
    # Required when "heighten" in metamagic — target slot level

    @property
    def requires_point(self) -> bool:
        """Whether this spell requires a grid point (area effects)."""
        return self.target_mode == "point"

    @property
    def requires_target_entity(self) -> bool:
        """Whether this spell requires a target creature."""
        return self.target_mode == "creature"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "spell_name": self.spell_name,
            "target_mode": self.target_mode,
            "metamagic": list(self.metamagic),
            "heighten_to_level": self.heighten_to_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CastSpellIntent":
        """Create from dictionary."""
        if data.get("type") != "cast_spell":
            raise IntentParseError(f"Expected type 'cast_spell', got '{data.get('type')}'")

        target_mode = data.get("target_mode", "none")
        if target_mode not in ["point", "creature", "self", "none"]:
            raise IntentParseError(f"Invalid target_mode: {target_mode}")

        return cls(
            spell_name=data.get("spell_name", ""),
            target_mode=target_mode,
            metamagic=list(data.get("metamagic", [])),
            heighten_to_level=data.get("heighten_to_level"),
        )


@dataclass
class MoveIntent:
    """Intent to move to a location."""

    type: Literal["move"] = "move"
    destination: Optional[Position] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"type": self.type}
        if self.destination is not None:
            result["destination"] = self.destination.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MoveIntent":
        """Create from dictionary."""
        if data.get("type") != "move":
            raise IntentParseError(f"Expected type 'move', got '{data.get('type')}'")

        destination = None
        if "destination" in data and data["destination"] is not None:
            destination = Position.from_dict(data["destination"])

        return cls(destination=destination)


@dataclass
class DeclaredAttackIntent:
    """Voice-layer intent to attack a target.

    NOTE: This is the voice/interaction layer intent (target_ref + weapon name).
    It is NOT the combat resolution AttackIntent in aidm.schemas.attack which
    contains full weapon stats and numeric attack bonuses. A bridge layer will
    translate DeclaredAttackIntent → attack.AttackIntent for combat resolution.
    """

    type: Literal["attack"] = "attack"
    target_ref: Optional[str] = None
    weapon: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"type": self.type}
        if self.target_ref is not None:
            result["target_ref"] = self.target_ref
        if self.weapon is not None:
            result["weapon"] = self.weapon
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeclaredAttackIntent":
        """Create from dictionary."""
        if data.get("type") != "attack":
            raise IntentParseError(f"Expected type 'attack', got '{data.get('type')}'")

        return cls(
            target_ref=data.get("target_ref"),
            weapon=data.get("weapon")
        )


@dataclass
class BuyIntent:
    """Intent to purchase items."""

    type: Literal["buy"] = "buy"
    items: List[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default items list."""
        if self.items is None:
            self.items = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "items": self.items
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuyIntent":
        """Create from dictionary."""
        if data.get("type") != "buy":
            raise IntentParseError(f"Expected type 'buy', got '{data.get('type')}'")

        items = data.get("items", [])

        # Validate item structure
        for item in items:
            if not isinstance(item, dict):
                raise IntentParseError("Items must be dictionaries")
            if "name" not in item or "qty" not in item:
                raise IntentParseError("Items must have 'name' and 'qty' fields")

        return cls(items=items)


@dataclass
class RestIntent:
    """Intent to rest.

    D&D 3.5e rest types (PHB p.146):
    - overnight: 8-hour rest (natural healing, spell preparation)
    - full_day: Full day of bed rest (3x natural healing rate)
    """

    type: Literal["rest"] = "rest"
    rest_type: Literal["overnight", "full_day"] = "overnight"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "rest_type": self.rest_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestIntent":
        """Create from dictionary."""
        if data.get("type") != "rest":
            raise IntentParseError(f"Expected type 'rest', got '{data.get('type')}'")

        rest_type = data.get("rest_type", "overnight")
        if rest_type not in ["overnight", "full_day"]:
            raise IntentParseError(f"Invalid rest_type: {rest_type}")

        return cls(rest_type=rest_type)


@dataclass
class SummonCompanionIntent:
    """Intent to summon an animal companion into the WorldState.

    WO-ENGINE-COMPANION-WIRE

    Emitted when a druid or ranger calls their animal companion to their side.
    The companion entity is built from aidm.chargen.companions.build_animal_companion()
    and inserted into WorldState via an add_entity event.

    companion_type must be one of: "wolf", "riding_dog", "eagle", "light_horse", "viper_snake".
    If companion_type is None the resolver will reject the intent (fail-closed).
    """

    type: Literal["summon_companion"] = "summon_companion"
    companion_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "companion_type": self.companion_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SummonCompanionIntent":
        """Create from dictionary."""
        if data.get("type") != "summon_companion":
            raise IntentParseError(
                f"Expected type 'summon_companion', got '{data.get('type')}'"
            )
        return cls(companion_type=data.get("companion_type"))


@dataclass
class PrepareSpellsIntent:
    """Intent to prepare spells after a rest. WO-ENGINE-SPELL-PREP-001.

    PHB p.177-178: Prepared casters (wizard, cleric, druid, paladin, ranger)
    choose which spells to prepare each day after a qualifying rest.

    preparation: Dict mapping spell_level (int) to list of spell_ids (str).
    Example:
        PrepareSpellsIntent(
            caster_id="wizard_pc",
            preparation={1: ["magic_missile", "magic_missile", "shield"], 2: ["scorching_ray"]}
        )

    The same spell_id may appear multiple times in a level's list — this consumes
    one slot per occurrence (PHB p.178: wizard may prepare same spell twice).
    """

    caster_id: str
    """Entity ID of the caster preparing spells."""

    preparation: Dict[int, List[str]]
    """Dict mapping spell level to list of spell_ids to prepare."""

    use_secondary: bool = False
    """True if preparing secondary caster class spells (dual-caster only)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": "prepare_spells",
            "caster_id": self.caster_id,
            "preparation": self.preparation,
            "use_secondary": self.use_secondary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrepareSpellsIntent":
        """Create from dictionary."""
        return cls(
            caster_id=data["caster_id"],
            preparation={int(k): v for k, v in data.get("preparation", {}).items()},
            use_secondary=data.get("use_secondary", False),
        )


@dataclass
class ChargeIntent:
    """Intent to perform a charge action (PHB p.150-151).

    A charge is a full-round action: move up to 2× speed in a straight line
    toward target, then make one melee attack at +2. Charger takes -2 AC
    until start of next turn.

    WO-ENGINE-CHARGE-001
    """

    attacker_id: str
    """Entity ID of the charging entity."""

    target_id: str
    """Entity ID of the charge target (must be on opposing team)."""

    weapon: dict
    """Weapon dict in Weapon-schema format (same shape as AttackIntent.weapon)."""

    path_clear: bool = True
    """DM/AI assertion that the charge path is unobstructed.
    Set False if difficult terrain, obstacles, or blocking creatures are
    present. When False, the resolver emits intent_validation_failed with
    reason 'charge_path_blocked' and does not proceed to attack resolution.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": "charge",
            "attacker_id": self.attacker_id,
            "target_id": self.target_id,
            "weapon": self.weapon,
            "path_clear": self.path_clear,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChargeIntent":
        """Create from dictionary."""
        if data.get("type") != "charge":
            raise IntentParseError(
                f"Expected type 'charge', got '{data.get('type')}'"
            )
        return cls(
            attacker_id=data["attacker_id"],
            target_id=data["target_id"],
            weapon=data["weapon"],
            path_clear=data.get("path_clear", True),
        )


@dataclass
class CoupDeGraceIntent:
    """Intent to deliver a coup de grâce to a helpless or dying target.

    PHB p.153: Full-round action. Auto-hit, auto-crit. Fort save or die.
    Provokes AoO from threatening enemies.

    WO-ENGINE-COUP-DE-GRACE-001
    """

    attacker_id: str
    """Entity performing the coup de grâce."""

    target_id: str
    """Must be DYING (EF.DYING == True) or have HELPLESS/UNCONSCIOUS/PINNED/PARALYZED condition."""

    weapon: dict
    """Weapon dict. Must contain: damage_dice (str), damage_bonus (int),
    crit_multiplier (int, default 2), damage_type (str), grip (str)."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "coup_de_grace",
            "attacker_id": self.attacker_id,
            "target_id": self.target_id,
            "weapon": self.weapon,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoupDeGraceIntent":
        if data.get("type") != "coup_de_grace":
            raise IntentParseError(f"Expected type 'coup_de_grace', got '{data.get('type')}'")
        return cls(
            attacker_id=data["attacker_id"],
            target_id=data["target_id"],
            weapon=data["weapon"],
        )


@dataclass
class TurnUndeadIntent:
    """Intent to use the Turn Undead class feature.

    PHB p.159–160: Clerics (and paladins) can turn undead as a standard action,
    usable 3 + CHA modifier times per day. Roll 2d6 + cleric level + CHA modifier
    to determine the maximum HD of undead affected. Undead with HD <= (cleric level - 4)
    are destroyed (not just turned). Evil clerics rebuke/command instead of turning.

    WO-ENGINE-TURN-UNDEAD-001
    """

    cleric_id: str
    """Entity performing the turning (must have TURN_USES > 0)."""

    target_ids: List[str]
    """Undead entities to attempt to turn (must have UNDEAD_TYPE set). May be empty."""

    def __post_init__(self):
        if not self.cleric_id:
            raise IntentParseError("cleric_id cannot be empty")
        if not isinstance(self.target_ids, list):
            raise IntentParseError("target_ids must be a list")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "turn_undead",
            "cleric_id": self.cleric_id,
            "target_ids": self.target_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TurnUndeadIntent":
        if data.get("type") != "turn_undead":
            raise IntentParseError(f"Expected type 'turn_undead', got '{data.get('type')}'")
        return cls(
            cleric_id=data["cleric_id"],
            target_ids=data.get("target_ids", []),
        )


@dataclass
class ReadyActionIntent:
    """Intent to ready a standard action for a trigger condition.

    PHB p.160: Ready is a standard action. The actor specifies a trigger
    and an action to execute when the trigger fires. If the trigger never
    fires, the readied action is lost at the start of the actor's next turn.

    WO-ENGINE-READIED-ACTION-001
    """

    actor_id: str
    """Entity ID of the actor readying the action."""

    trigger_type: Literal["enemy_casts", "enemy_enters_range", "enemy_enters_square"]
    """What condition fires the readied action."""

    readied_intent: Optional[Dict[str, Any]] = None
    """Serialized intent (AttackIntent dict) to execute when trigger fires.
    None raises ValueError (fail-closed)."""

    trigger_target_id: Optional[str] = None
    """Specific enemy to watch. None = any enemy."""

    trigger_square: Optional[Dict[str, Any]] = None
    """For enemy_enters_square: {x: int, y: int} of the watched square."""

    trigger_range_ft: float = 5.0
    """For enemy_enters_range: fire when enemy comes within this many feet."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ready_action",
            "actor_id": self.actor_id,
            "trigger_type": self.trigger_type,
            "readied_intent": self.readied_intent,
            "trigger_target_id": self.trigger_target_id,
            "trigger_square": self.trigger_square,
            "trigger_range_ft": self.trigger_range_ft,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReadyActionIntent":
        if data.get("type") != "ready_action":
            raise IntentParseError(f"Expected type 'ready_action', got '{data.get('type')}'")
        return cls(
            actor_id=data["actor_id"],
            trigger_type=data["trigger_type"],
            readied_intent=data.get("readied_intent"),
            trigger_target_id=data.get("trigger_target_id"),
            trigger_square=data.get("trigger_square"),
            trigger_range_ft=data.get("trigger_range_ft", 5.0),
        )


@dataclass
class AidAnotherIntent:
    """Intent to aid an ally with the Aid Another action.

    PHB p.154: Standard action. Helper makes attack roll vs AC 10.
    Success grants ally +2 circumstance bonus to attack or AC.
    Multiple Aid Another bonuses from different helpers stack.

    WO-ENGINE-AID-ANOTHER-001
    """

    actor_id: str
    """Entity ID of the helper making the aid action."""

    ally_id: str
    """Entity ID of the ally being aided."""

    enemy_id: str
    """Entity ID of the enemy relevant to the aid (attack target or attacker)."""

    aid_type: Literal["attack", "ac"]
    """
    'attack' — aids ally's next attack roll vs enemy_id (+2 to hit)
    'ac'     — aids ally's AC vs enemy_id's next attack (+2 AC)
    """

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "aid_another",
            "actor_id": self.actor_id,
            "ally_id": self.ally_id,
            "enemy_id": self.enemy_id,
            "aid_type": self.aid_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AidAnotherIntent":
        if data.get("type") != "aid_another":
            raise IntentParseError(f"Expected type 'aid_another', got '{data.get('type')}'")
        return cls(
            actor_id=data["actor_id"],
            ally_id=data["ally_id"],
            enemy_id=data["enemy_id"],
            aid_type=data["aid_type"],
        )


@dataclass
class FightDefensivelyIntent:
    """Intent to fight defensively this round.

    PHB p.142: Standard action. −4 attack / +2 dodge AC (or −5/+5 with
    Combat Expertise feat). Modifier persists until start of actor's next turn.

    WO-ENGINE-DEFEND-001
    """

    actor_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "fight_defensively", "actor_id": self.actor_id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FightDefensivelyIntent":
        if data.get("type") != "fight_defensively":
            raise IntentParseError(f"Expected type 'fight_defensively', got '{data.get('type')}'")
        return cls(actor_id=data["actor_id"])


@dataclass
class TotalDefenseIntent:
    """Intent to take total defense this round.

    PHB p.142: Standard action. +4 dodge AC. No attacks allowed.
    Modifier persists until start of actor's next turn.

    WO-ENGINE-DEFEND-001
    """

    actor_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "total_defense", "actor_id": self.actor_id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TotalDefenseIntent":
        if data.get("type") != "total_defense":
            raise IntentParseError(f"Expected type 'total_defense', got '{data.get('type')}'")
        return cls(actor_id=data["actor_id"])


@dataclass
class FeintIntent:
    """Intent to feint in melee combat.

    PHB p.68/76: Standard action. Bluff check vs (Sense Motive + BAB).
    Success: target denied Dex to AC against feinting actor's next melee attack.

    WO-ENGINE-FEINT-001
    """

    actor_id: str
    """Entity ID of the feinting character."""

    target_id: str
    """Entity ID of the feint target."""

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "feint", "actor_id": self.actor_id, "target_id": self.target_id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeintIntent":
        if data.get("type") != "feint":
            raise IntentParseError(f"Expected type 'feint', got '{data.get('type')}'")
        return cls(actor_id=data["actor_id"], target_id=data["target_id"])


@dataclass
class AbilityDamageIntent:
    """Intent to apply ability score damage or drain to a target.

    PHB p.215: Ability damage is temporary (heals 1/ability/night's rest).
    Ability drain is permanent (does not heal naturally).

    WO-ENGINE-ABILITY-DAMAGE-001
    """

    source_id: str
    """Entity applying the ability damage (attacker or trap)."""

    target_id: str
    """Entity receiving the ability damage."""

    ability: Literal["str", "dex", "con", "int", "wis", "cha"]
    """Which ability score is damaged."""

    amount: int
    """Number of points of damage/drain."""

    is_drain: bool = False
    """If True, this is permanent drain; if False, temporary damage."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ability_damage",
            "source_id": self.source_id,
            "target_id": self.target_id,
            "ability": self.ability,
            "amount": self.amount,
            "is_drain": self.is_drain,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AbilityDamageIntent":
        if data.get("type") != "ability_damage":
            raise IntentParseError(f"Expected type 'ability_damage', got '{data.get('type')}'")
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            ability=data["ability"],
            amount=data["amount"],
            is_drain=data.get("is_drain", False),
        )


@dataclass
class WithdrawIntent:
    """Intent to use the Withdraw action (PHB p.160).

    Full-round action. The first square the actor leaves does NOT provoke AoO.
    Subsequent movement may provoke normally.

    WO-ENGINE-WITHDRAW-DELAY-001
    """

    actor_id: str
    """Entity ID of the withdrawing entity."""

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "withdraw", "actor_id": self.actor_id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WithdrawIntent":
        if data.get("type") != "withdraw":
            raise IntentParseError(f"Expected type 'withdraw', got '{data.get('type')}'")
        return cls(actor_id=data["actor_id"])


@dataclass
class DelayIntent:
    """Intent to delay (PHB p.160).

    The actor voluntarily acts later in the round at a lower initiative count.
    The initiative_order is permanently reordered for the rest of combat.

    WO-ENGINE-WITHDRAW-DELAY-001
    """

    actor_id: str
    """Entity ID of the delaying entity."""

    new_initiative: int
    """The initiative count at which the actor will now act."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "delay",
            "actor_id": self.actor_id,
            "new_initiative": self.new_initiative,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DelayIntent":
        if data.get("type") != "delay":
            raise IntentParseError(f"Expected type 'delay', got '{data.get('type')}'")
        return cls(
            actor_id=data["actor_id"],
            new_initiative=data["new_initiative"],
        )


# Type alias for all intent types
Intent = (CastSpellIntent | MoveIntent | DeclaredAttackIntent | BuyIntent | RestIntent |
          SummonCompanionIntent | PrepareSpellsIntent | ChargeIntent | CoupDeGraceIntent |
          TurnUndeadIntent | ReadyActionIntent | AidAnotherIntent | FightDefensivelyIntent |
          TotalDefenseIntent | FeintIntent | AbilityDamageIntent | WithdrawIntent | DelayIntent)


def parse_intent(data: Dict[str, Any]) -> Intent:
    """
    Parse intent from dictionary based on type field.

    Args:
        data: Intent dictionary with 'type' field

    Returns:
        Parsed intent instance

    Raises:
        IntentParseError: If type is unknown or data is invalid
    """
    intent_type = data.get("type")

    if intent_type == "cast_spell":
        return CastSpellIntent.from_dict(data)
    elif intent_type == "move":
        return MoveIntent.from_dict(data)
    elif intent_type == "attack":
        return DeclaredAttackIntent.from_dict(data)
    elif intent_type == "buy":
        return BuyIntent.from_dict(data)
    elif intent_type == "rest":
        return RestIntent.from_dict(data)
    elif intent_type == "summon_companion":
        return SummonCompanionIntent.from_dict(data)
    elif intent_type == "prepare_spells":
        return PrepareSpellsIntent.from_dict(data)
    elif intent_type == "charge":
        return ChargeIntent.from_dict(data)
    elif intent_type == "coup_de_grace":
        return CoupDeGraceIntent.from_dict(data)
    elif intent_type == "turn_undead":
        return TurnUndeadIntent.from_dict(data)
    elif intent_type == "ready_action":
        return ReadyActionIntent.from_dict(data)
    elif intent_type == "aid_another":
        return AidAnotherIntent.from_dict(data)
    elif intent_type == "fight_defensively":
        return FightDefensivelyIntent.from_dict(data)
    elif intent_type == "total_defense":
        return TotalDefenseIntent.from_dict(data)
    elif intent_type == "feint":
        return FeintIntent.from_dict(data)
    elif intent_type == "ability_damage":
        return AbilityDamageIntent.from_dict(data)
    elif intent_type == "withdraw":
        return WithdrawIntent.from_dict(data)
    elif intent_type == "delay":
        return DelayIntent.from_dict(data)
    else:
        raise IntentParseError(f"Unknown intent type: {intent_type}")
