"""M1 Narration Layer v0 — Template-based narration.

Implements LLM_ENGINE_BOUNDARY_CONTRACT.md Section 3.6 Narrator:
- Receives EngineResult (read-only)
- Produces human-readable description
- Cannot alter outcomes or add mechanical effects
- Falls back to deterministic templates

For M1, this is a template-only implementation.
LLM integration will be added in future milestones.

Reference: docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from aidm.schemas.engine_result import EngineResult, EngineResultStatus


@dataclass
class NarrationContext:
    """Context for narration generation.

    Contains scene information needed to produce natural narration.
    All data is read-only — narration cannot modify anything.
    """

    # Actor information
    actor_name: str = "The attacker"
    actor_id: str = ""

    # Target information (if applicable)
    target_name: str = "the target"
    target_id: str = ""

    # Weapon/method used
    weapon_name: str = "weapon"

    # Scene context
    scene_description: str = ""

    # Additional context
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_engine_result(
        cls,
        result: EngineResult,
        entity_names: Optional[Dict[str, str]] = None,
    ) -> "NarrationContext":
        """Create context from engine result.

        Args:
            result: The engine result to narrate
            entity_names: Optional mapping of entity_id -> display name
        """
        entity_names = entity_names or {}

        # Extract actor and target from events
        actor_id = ""
        target_id = ""
        weapon = "weapon"

        for event in result.events:
            if event.get("type") == "attack_roll":
                actor_id = event.get("attacker", "")
                target_id = event.get("target", "")
            if event.get("weapon"):
                weapon = event["weapon"]

        return cls(
            actor_name=entity_names.get(actor_id, actor_id or "The attacker"),
            actor_id=actor_id,
            target_name=entity_names.get(target_id, target_id or "the target"),
            target_id=target_id,
            weapon_name=weapon,
            metadata=result.metadata,
        )


class NarrationTemplates:
    """Deterministic templates for narration.

    These are fallback templates used when LLM is unavailable.
    Each template is keyed by narration token.
    """

    TEMPLATES: Dict[str, str] = {
        # ── Attack outcomes ──────────────────────────────────────────
        "attack_hit": "{actor} strikes {target} with their {weapon}! The blow lands true, dealing {damage} damage.",
        "attack_miss": "{actor} swings at {target} with their {weapon}, but the attack goes wide!",
        "critical_hit": "{actor}'s {weapon} finds a critical opening! The devastating blow deals {damage} damage to {target}!",
        "critical_miss": "{actor} stumbles badly, their attack completely missing {target}!",

        # ── Damage results ───────────────────────────────────────────
        "target_wounded": "{target} staggers from the blow, bloodied but still standing.",
        "target_defeated": "{target} collapses, defeated!",
        "hp_changed": "{target} takes {damage} damage.",
        "damage_applied": "{target} suffers {damage} damage.",

        # ── Combat lifecycle ─────────────────────────────────────────
        "combat_started": "Combat begins! All combatants roll for initiative.",
        "combat_round_started": "A new round of combat begins.",
        "initiative_rolled": "{actor} rolls initiative.",
        "turn_start": "{actor}'s turn begins.",
        "turn_end": "{actor}'s turn ends.",
        "full_attack_start": "{actor} makes a full attack.",
        "full_attack_end": "{actor} completes the full attack.",
        "entity_defeated": "{target} falls defeated!",
        "flat_footed_cleared": "{actor} is no longer flat-footed.",

        # ── Movement and position ────────────────────────────────────
        "movement_stub": "{actor} moves across the battlefield.",
        "movement_declared": "{actor} moves across the battlefield.",
        "mounted_movement": "{actor} rides their mount across the field.",
        "mounted_move_declared": "{actor} rides forward on their mount.",
        "rider_mounted": "{actor} mounts up.",
        "rider_dismounted": "{actor} dismounts.",
        "turn_ended": "{actor} ends their turn.",
        "action_aborted_by_aoo": "{actor}'s action is interrupted by an attack of opportunity!",

        # ── Targeting ────────────────────────────────────────────────
        "targeting_failed": "{actor} cannot target {target} — the attack is blocked.",

        # ── Combat maneuvers: Bull Rush ──────────────────────────────
        "bull_rush_declared": "{actor} attempts to bull rush {target}!",
        "bull_rush_success": "{actor} pushes {target} back!",
        "bull_rush_failure": "{actor}'s bull rush fails against {target}.",

        # ── Combat maneuvers: Trip ───────────────────────────────────
        "trip_declared": "{actor} attempts to trip {target}!",
        "trip_success": "{actor} trips {target}, sending them sprawling!",
        "trip_failure": "{actor}'s trip attempt fails.",

        # ── Combat maneuvers: Grapple ────────────────────────────────
        "grapple_declared": "{actor} attempts to grapple {target}!",
        "grapple_success": "{actor} grapples {target}!",
        "grapple_failure": "{actor} fails to establish a grapple.",

        # ── Combat maneuvers: Disarm ─────────────────────────────────
        "disarm_declared": "{actor} attempts to disarm {target}!",
        "disarm_success": "{actor} knocks the weapon from {target}'s hands!",
        "disarm_failure": "{actor}'s disarm attempt fails.",

        # ── Combat maneuvers: Sunder ─────────────────────────────────
        "sunder_declared": "{actor} attempts to sunder {target}'s equipment!",
        "sunder_success": "{actor} damages {target}'s equipment!",
        "sunder_failure": "{actor}'s sunder attempt fails.",

        # ── Combat maneuvers: Overrun ────────────────────────────────
        "overrun_declared": "{actor} attempts to overrun {target}!",
        "overrun_success": "{actor} bowls through {target}!",
        "overrun_failure": "{actor}'s overrun fails.",

        # ── Saves and conditions ─────────────────────────────────────
        "save_rolled": "{target} makes a saving throw.",
        "save_negated": "{target} resists the effect!",
        "condition_applied": "{target} is affected by a condition.",
        "spell_resistance_checked": "{target}'s spell resistance is tested.",

        # ── Attacks of opportunity ───────────────────────────────────
        "aoo_triggered": "{target} provokes an attack of opportunity from {actor}!",
        "aoo_blocked_by_cover": "The attack of opportunity is blocked by cover.",

        # ── Environmental and falling ────────────────────────────────
        "environmental_damage": "{target} takes environmental damage.",
        "fall_triggered": "{target} falls!",
        "falling_damage": "{target} takes falling damage.",

        # ── Miscellaneous ────────────────────────────────────────────
        "rule_lookup": "A rule is consulted.",

        # ── Player actions ───────────────────────────────────────────
        "action_retracted": "{actor} reconsiders and withdraws the action.",

        # ── Generic fallbacks ────────────────────────────────────────
        "success": "The action succeeds.",
        "failure": "The action fails.",
        "unknown": "Something happens...",
    }

    @classmethod
    def get_template(cls, token: str) -> str:
        """Get template for a narration token."""
        return cls.TEMPLATES.get(token, cls.TEMPLATES["unknown"])


class Narrator:
    """Narration layer that produces human-readable descriptions.

    Per IPC_CONTRACT.md Section 3.6:
    - Receives EngineResult (read-only)
    - Produces narration text
    - Cannot alter outcomes or modify game state
    - Falls back to templates if LLM unavailable

    This v0 implementation is template-only.
    LLM integration will be added in future milestones.
    """

    def __init__(self, use_templates: bool = True):
        """Initialize narrator.

        Args:
            use_templates: If True, use deterministic templates.
                          Future: If False, attempt LLM narration.
        """
        self._use_templates = use_templates
        self._entity_names: Dict[str, str] = {}

    def register_entity_name(self, entity_id: str, name: str) -> None:
        """Register a display name for an entity."""
        self._entity_names[entity_id] = name

    def register_entity_names(self, names: Dict[str, str]) -> None:
        """Register multiple entity names."""
        self._entity_names.update(names)

    def narrate(
        self,
        result: EngineResult,
        context: Optional[NarrationContext] = None,
    ) -> str:
        """Generate narration for an engine result.

        Args:
            result: The engine result to narrate (read-only)
            context: Optional narration context (auto-generated if not provided)

        Returns:
            Human-readable narration string
        """
        # Get or create context
        if context is None:
            context = NarrationContext.from_engine_result(
                result, self._entity_names
            )

        # Handle failure/aborted results
        if result.status == EngineResultStatus.FAILURE:
            return self._narrate_failure(result, context)
        if result.status == EngineResultStatus.ABORTED:
            return self._narrate_aborted(result, context)

        # Get narration token
        token = result.narration_token or "unknown"

        # Generate from template
        return self._narrate_from_template(token, result, context)

    def _narrate_from_template(
        self,
        token: str,
        result: EngineResult,
        context: NarrationContext,
    ) -> str:
        """Generate narration from template.

        Args:
            token: Narration token from engine result
            result: Engine result for additional data
            context: Narration context
        """
        template = NarrationTemplates.get_template(token)

        # Extract damage from events if present
        damage = 0
        for event in result.events:
            if event.get("type") == "damage_dealt":
                damage = event.get("damage", 0)
                break

        # Format template
        try:
            narration = template.format(
                actor=context.actor_name,
                target=context.target_name,
                weapon=context.weapon_name,
                damage=damage,
            )
        except KeyError:
            # Template has unrecognized placeholder - use as-is
            narration = template

        return narration

    def _narrate_failure(
        self,
        result: EngineResult,
        context: NarrationContext,
    ) -> str:
        """Narrate a failed action."""
        reason = result.failure_reason or "unknown reason"
        return f"The action could not be completed: {reason}"

    def _narrate_aborted(
        self,
        result: EngineResult,
        context: NarrationContext,
    ) -> str:
        """Narrate an aborted action."""
        reason = result.failure_reason or "unforeseen circumstances"
        return f"{context.actor_name}'s action was interrupted by {reason}!"

    def narrate_combat_round(
        self,
        results: List[EngineResult],
    ) -> str:
        """Generate narration for a full combat round.

        Args:
            results: List of engine results for the round

        Returns:
            Combined narration for the round
        """
        if not results:
            return "The round passes without incident."

        narrations = []
        for result in results:
            narrations.append(self.narrate(result))

        return "\n\n".join(narrations)


# Type alias for custom narrator function
NarratorFunc = Callable[[EngineResult, Optional[NarrationContext]], str]


def create_default_narrator() -> Narrator:
    """Create a default narrator instance."""
    return Narrator(use_templates=True)


def narrate_attack(
    attacker_name: str,
    target_name: str,
    weapon_name: str,
    hit: bool,
    damage: int = 0,
    critical: bool = False,
    target_defeated: bool = False,
) -> str:
    """Convenience function for narrating attack results.

    Args:
        attacker_name: Name of the attacker
        target_name: Name of the target
        weapon_name: Name of the weapon used
        hit: Whether the attack hit
        damage: Damage dealt (if hit)
        critical: Whether it was a critical hit
        target_defeated: Whether the target was defeated

    Returns:
        Narration string
    """
    if not hit:
        return f"{attacker_name} swings at {target_name} with their {weapon_name}, but misses!"

    if critical:
        narration = f"{attacker_name}'s {weapon_name} finds a critical opening! The devastating blow deals {damage} damage to {target_name}!"
    else:
        narration = f"{attacker_name} strikes {target_name} with their {weapon_name}, dealing {damage} damage!"

    if target_defeated:
        narration += f" {target_name} collapses, defeated!"

    return narration
