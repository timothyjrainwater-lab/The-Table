"""WO-046: Box Event Contracts — Typed schemas for Box→Lens boundary events.

Defines frozen dataclass schemas for the event payloads that cross the
Box→Lens boundary (i.e., events the SessionOrchestrator unpacks to build
NarrativeBrief). These are CONTRACT types — resolvers emit dict payloads,
and validation occurs at the orchestrator extraction point.

Design decisions:
- Frozen dataclasses (no Pydantic) — consistent with codebase, no coercion
- Validate at extraction, not emission — resolvers keep emitting dicts
- Superset schema for attack_roll (single + full attack fields)
- Only event types the orchestrator actually unpacks are formalized here
- Everything else stays Dict[str, Any] until it breaks twice

Placement: aidm/schemas/ — neutral ground importable by both core and runtime.

Reference: docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md (P0 event contract)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


# ======================================================================
# EVENT SCHEMAS — Box→Lens boundary contracts
# ======================================================================


@dataclass(frozen=True)
class TurnStartPayload:
    """Marks the beginning of a turn. Emitted by play_loop.execute_turn().

    Source: aidm/core/play_loop.py (turn_start event)
    """

    turn_index: int
    actor_id: str
    actor_team: str


@dataclass(frozen=True)
class TurnEndPayload:
    """Marks the end of a turn. Emitted by play_loop.execute_turn().

    Source: aidm/core/play_loop.py (turn_end event)
    """

    turn_index: int
    actor_id: str
    events_emitted: int


@dataclass(frozen=True)
class AttackRollPayload:
    """Result of a single attack roll (d20 + modifiers vs AC).

    Superset schema covering both single attack (attack_resolver.py)
    and full attack (full_attack_resolver.py) variants. Full-attack-specific
    fields are Optional.

    Source: aidm/core/attack_resolution.py, aidm/core/full_attack_resolution.py
    """

    # Core fields (both single and full attack)
    attacker_id: str
    target_id: str
    d20_result: int  # 1-20
    attack_bonus: int
    total: int  # d20_result + all modifiers
    target_ac: int
    hit: bool
    is_natural_20: bool
    is_natural_1: bool

    # Single attack fields (from attack_resolver — may be absent in full attack)
    condition_modifier: int = 0
    mounted_bonus: int = 0
    terrain_higher_ground: int = 0
    feat_modifier: int = 0
    cover_type: Optional[str] = None
    cover_ac_bonus: int = 0
    target_base_ac: int = 0
    target_ac_modifier: int = 0

    # Full attack fields (from full_attack_resolver — absent in single attack)
    attack_index: Optional[int] = None
    is_threat: Optional[bool] = None
    is_critical: Optional[bool] = None
    confirmation_total: Optional[int] = None


@dataclass(frozen=True)
class DamageRollPayload:
    """Result of a damage roll following a successful hit.

    Superset schema covering both single attack and full attack variants.

    Source: aidm/core/attack_resolution.py, aidm/core/full_attack_resolution.py
    """

    attacker_id: str
    target_id: str
    damage_dice: str  # e.g., "1d8"
    damage_rolls: Tuple[int, ...]  # Individual die results (frozen-safe)
    damage_bonus: int
    str_modifier: int
    damage_total: int  # Final damage (>= 0)
    damage_type: str  # e.g., "slashing", "piercing"

    # Single attack fields
    condition_modifier: int = 0
    feat_modifier: int = 0

    # Full attack fields
    attack_index: Optional[int] = None
    base_damage: Optional[int] = None  # Pre-critical damage
    critical_multiplier: Optional[int] = None  # 1 if not critical


@dataclass(frozen=True)
class HPChangedPayload:
    """HP mutation event — damage or healing applied to an entity.

    Source: attack_resolver.py, full_attack_resolver.py, play_loop.py (spells),
            save_resolver.py
    """

    entity_id: str
    delta: int  # Negative for damage, positive for healing
    source: str  # e.g., "attack_damage", "spell:fireball", "save_effect"

    # Present in attack/full_attack resolver variants
    hp_before: Optional[int] = None
    hp_after: Optional[int] = None

    # Alternate field names from play_loop spell resolution
    old_hp: Optional[int] = None
    new_hp: Optional[int] = None

    @property
    def effective_hp_before(self) -> Optional[int]:
        """Return hp_before regardless of which field name was used."""
        return self.hp_before if self.hp_before is not None else self.old_hp

    @property
    def effective_hp_after(self) -> Optional[int]:
        """Return hp_after regardless of which field name was used."""
        return self.hp_after if self.hp_after is not None else self.new_hp


@dataclass(frozen=True)
class EntityDefeatedPayload:
    """Entity reduced to 0 or fewer HP.

    Source: attack_resolver.py, full_attack_resolver.py, play_loop.py (spells),
            save_resolver.py
    """

    entity_id: str

    # Present in attack/full_attack/save resolver variants
    hp_final: Optional[int] = None
    defeated_by: Optional[str] = None

    # Present in spell variant (play_loop)
    source: Optional[str] = None  # e.g., "spell:fireball"


@dataclass(frozen=True)
class SpellCastPayload:
    """Spell successfully cast and resolved.

    Source: aidm/core/play_loop.py (_resolve_spell_cast)
    """

    cast_id: str
    caster_id: str
    spell_id: str
    spell_name: str
    spell_level: int
    affected_entities: Tuple[str, ...]  # Entity IDs affected
    turn_index: int


@dataclass(frozen=True)
class SaveRolledPayload:
    """Saving throw result (d20 + bonus vs DC).

    Source: aidm/core/save_resolver.py
    """

    target_id: str
    save_type: str  # "fort", "ref", "will"
    d20_result: int  # 1-20
    save_bonus: int
    total: int  # d20_result + save_bonus
    dc: int
    outcome: str  # "SUCCESS", "FAILURE", "PARTIAL"
    is_natural_20: bool
    is_natural_1: bool


@dataclass(frozen=True)
class ConditionAppliedPayload:
    """Condition applied to an entity.

    Source: play_loop.py (spells), save_resolver.py
    """

    # Field names vary by source — include both patterns
    entity_id: Optional[str] = None  # play_loop variant
    target_id: Optional[str] = None  # save_resolver variant
    condition: Optional[str] = None  # play_loop variant
    condition_type: Optional[str] = None  # save_resolver variant
    source: Optional[str] = None
    duration_rounds: Optional[int] = None

    @property
    def effective_entity_id(self) -> Optional[str]:
        """Return entity ID regardless of which field name was used."""
        return self.entity_id if self.entity_id is not None else self.target_id

    @property
    def effective_condition(self) -> Optional[str]:
        """Return condition name regardless of which field name was used."""
        return self.condition if self.condition is not None else self.condition_type


@dataclass(frozen=True)
class ConditionRemovedPayload:
    """Condition removed from an entity.

    Source: play_loop.py (_check_concentration_break)
    """

    entity_id: str
    condition: str
    reason: str


# ======================================================================
# PAYLOAD REGISTRY — Maps event_type strings to schema classes
# ======================================================================

PAYLOAD_SCHEMAS = {
    "turn_start": TurnStartPayload,
    "turn_end": TurnEndPayload,
    "attack_roll": AttackRollPayload,
    "damage_roll": DamageRollPayload,
    "hp_changed": HPChangedPayload,
    "entity_defeated": EntityDefeatedPayload,
    "spell_cast": SpellCastPayload,
    "save_rolled": SaveRolledPayload,
    "condition_applied": ConditionAppliedPayload,
    "condition_removed": ConditionRemovedPayload,
}


# ======================================================================
# VALIDATION — Boundary validation at orchestrator extraction point
# ======================================================================


class EventValidationError(Exception):
    """Raised when an event payload fails schema validation."""

    def __init__(self, event_type: str, message: str, payload: Dict[str, Any]):
        self.event_type = event_type
        self.payload = payload
        super().__init__(f"Event '{event_type}' validation failed: {message}")


def validate_event_payload(
    event_type: str, payload: Dict[str, Any]
) -> Optional[Any]:
    """Validate an event payload against its schema.

    Returns a typed frozen dataclass instance if the event type has a
    registered schema. Returns None for unregistered event types (they
    pass through as raw dicts — "everything else stays dict until it
    breaks twice").

    Args:
        event_type: The event_type string from the Event object
        payload: The raw dict payload from the Event object

    Returns:
        Typed payload dataclass, or None if no schema registered

    Raises:
        EventValidationError: If payload has wrong types or missing required fields
    """
    schema_cls = PAYLOAD_SCHEMAS.get(event_type)
    if schema_cls is None:
        return None

    try:
        # Extract only the fields the schema expects
        import dataclasses

        field_names = {f.name for f in dataclasses.fields(schema_cls)}

        # Separate known fields from extras
        known = {}
        for key, value in payload.items():
            if key in field_names:
                # Convert lists to tuples for frozen dataclass fields
                field_obj = next(
                    (f for f in dataclasses.fields(schema_cls) if f.name == key),
                    None,
                )
                if field_obj and hasattr(field_obj.type, "__origin__"):
                    # Handle Tuple[...] fields that might come in as lists
                    if "Tuple" in str(field_obj.type) and isinstance(value, list):
                        value = tuple(value)
                elif field_obj:
                    type_str = str(field_obj.type)
                    if "Tuple" in type_str and isinstance(value, list):
                        value = tuple(value)
                known[key] = value

        return schema_cls(**known)

    except TypeError as e:
        raise EventValidationError(event_type, str(e), payload)


def validate_required_fields(
    event_type: str, payload: Dict[str, Any], required: List[str]
) -> None:
    """Validate that required fields are present and non-None.

    Use this for ad-hoc validation of specific fields without constructing
    the full schema object. Useful in tests for checking structural invariants.

    Args:
        event_type: Event type for error reporting
        payload: Raw dict payload
        required: List of field names that must be present

    Raises:
        EventValidationError: If any required field is missing
    """
    missing = [f for f in required if f not in payload]
    if missing:
        raise EventValidationError(
            event_type,
            f"Missing required fields: {missing}",
            payload,
        )
