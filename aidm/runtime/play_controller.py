"""WO-CODE-LOOP-001: End-to-End Play One Turn Controller.

Wires: text input → VoiceIntentParser → IntentBridge → Box (execute_turn) →
       EventLog → Narrator (template fallback) → TurnOutput.

This controller is the minimal integration proof that converts "engine exists"
into "a user can actually play a turn".  It does NOT touch aidm/core/** —
it only calls into existing resolvers via their public APIs.

INVARIANTS:
  - Same (world_state snapshot + input text + RNG seed) → identical TurnOutput
  - Clarification prompts contain no coaching, no tactical hints, no warnings
  - Template narration is the default; Spark is never required
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

from aidm.core.event_log import Event, EventLog
from aidm.core.initiative import roll_initiative_for_all_actors, InitiativeRoll
from aidm.core.play_loop import TurnContext, TurnResult as BoxTurnResult, execute_turn
from aidm.core.rng_manager import RNGManager
from aidm.core.state import FrozenWorldStateView, WorldState
from aidm.interaction.intent_bridge import (
    ClarificationRequest,
    IntentBridge,
)
from aidm.narration.narrator import (
    Narrator,
    NarrationContext,
    NarrationTemplates,
)
from aidm.schemas.attack import AttackIntent, StepMoveIntent, FullMoveIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import (
    CastSpellIntent,
    DeclaredAttackIntent,
    MoveIntent,
)
from aidm.schemas.position import Position

_ARTICLES = {"the", "a", "an"}


def _strip_articles(text: str) -> str:
    """Strip leading articles from a target reference.

    "the goblin" → "goblin"
    "a dragon"   → "dragon"
    "an orc"     → "orc"
    """
    words = text.split()
    while words and words[0] in _ARTICLES:
        words.pop(0)
    return " ".join(words) if words else text


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TurnOutput:
    """Immutable result of a single play-one-turn cycle."""

    success: bool
    intent_summary: str
    box_status: str
    events: Tuple[Dict[str, Any], ...]
    narration_text: str
    narration_provenance: str
    state_hash_before: str
    state_hash_after: str
    event_count: int
    clarification_needed: bool = False
    clarification_message: Optional[str] = None
    clarification_candidates: Optional[Tuple[str, ...]] = None
    error_message: Optional[str] = None


@dataclass
class ScenarioFixture:
    """A canned, self-contained combat scenario for one-turn execution.

    Everything needed to deterministically replay a single turn:
    world state, seed, actor, turn index, and event-ID watermark.
    """

    world_state: WorldState
    master_seed: int
    actor_id: str
    turn_index: int = 0
    next_event_id: int = 0
    timestamp: float = 0.0
    initiative_rolls: Optional[List[InitiativeRoll]] = None


# ---------------------------------------------------------------------------
# Scenario factory
# ---------------------------------------------------------------------------

def build_simple_combat_fixture(
    *,
    master_seed: int = 42,
    pc_name: str = "Aldric",
    pc_id: str = "pc_fighter",
    enemy_name: str = "Goblin Warrior",
    enemy_id: str = "goblin_1",
) -> ScenarioFixture:
    """Build a 3v3 party combat fixture.

    Returns a ScenarioFixture with:
      - Level-3 Fighter "Aldric" (longsword, AC 18, 28 HP)
      - Level-3 Cleric "Elara" (heavy mace, AC 17, 21 HP)
      - Level-3 Rogue "Snitch" (shortsword, AC 15, 18 HP)
      - 3x CR 1/3 Goblins (5-6 HP each)
      - Active combat with fixed initiative order
      - Deterministic seed
    """
    entities = {
        # --- Party ---
        pc_id: {
            EF.ENTITY_ID: pc_id,
            "name": pc_name,
            EF.HP_CURRENT: 28,
            EF.HP_MAX: 28,
            EF.AC: 18,
            EF.ATTACK_BONUS: 6,
            EF.BAB: 3,
            EF.STR_MOD: 3,
            EF.DEX_MOD: 1,
            EF.TEAM: "party",
            EF.WEAPON: "longsword",
            "weapon_damage": "1d8",
            EF.POSITION: {"x": 3, "y": 3},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,  # PHB: medium humanoid in heavy armor = 20, but fighter has medium armor
            EF.SPELL_SLOTS: {1: 5, 2: 4, 3: 3, 4: 2, 5: 1},
        },
        "pc_cleric": {
            EF.ENTITY_ID: "pc_cleric",
            "name": "Elara",
            EF.HP_CURRENT: 21,
            EF.HP_MAX: 21,
            EF.AC: 17,
            EF.ATTACK_BONUS: 4,
            EF.BAB: 2,
            EF.STR_MOD: 1,
            EF.DEX_MOD: 0,
            EF.WIS_MOD: 3,
            EF.TEAM: "party",
            EF.WEAPON: "heavy mace",
            "weapon_damage": "1d8",
            EF.POSITION: {"x": 2, "y": 3},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 20,  # PHB: cleric in heavy armor
            EF.SPELL_SLOTS: {1: 5, 2: 4, 3: 3, 4: 2, 5: 1},
        },
        "pc_rogue": {
            EF.ENTITY_ID: "pc_rogue",
            "name": "Snitch",
            EF.HP_CURRENT: 18,
            EF.HP_MAX: 18,
            EF.AC: 15,
            EF.ATTACK_BONUS: 5,
            EF.BAB: 2,
            EF.STR_MOD: 1,
            EF.DEX_MOD: 3,
            EF.TEAM: "party",
            EF.WEAPON: "shortsword",
            "weapon_damage": "1d6",
            EF.POSITION: {"x": 4, "y": 2},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,  # PHB: rogue in light armor
        },
        # --- Monsters ---
        enemy_id: {
            EF.ENTITY_ID: enemy_id,
            "name": enemy_name,
            EF.HP_CURRENT: 5,
            EF.HP_MAX: 5,
            EF.AC: 15,
            EF.ATTACK_BONUS: 3,
            EF.BAB: 1,
            EF.STR_MOD: 0,
            EF.DEX_MOD: 1,
            EF.TEAM: "monsters",
            EF.WEAPON: "shortbow",
            "weapon_damage": "1d4",
            EF.POSITION: {"x": 3, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "small",
            EF.BASE_SPEED: 30,  # MM: goblin base speed
        },
        "goblin_2": {
            EF.ENTITY_ID: "goblin_2",
            "name": "Goblin Archer",
            EF.HP_CURRENT: 5,
            EF.HP_MAX: 5,
            EF.AC: 15,
            EF.ATTACK_BONUS: 3,
            EF.BAB: 1,
            EF.STR_MOD: 0,
            EF.DEX_MOD: 1,
            EF.TEAM: "monsters",
            EF.WEAPON: "shortbow",
            "weapon_damage": "1d4",
            EF.POSITION: {"x": 4, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "small",
            EF.BASE_SPEED: 30,  # MM: goblin base speed
        },
        "goblin_3": {
            EF.ENTITY_ID: "goblin_3",
            "name": "Goblin Skirmisher",
            EF.HP_CURRENT: 6,
            EF.HP_MAX: 6,
            EF.AC: 14,
            EF.ATTACK_BONUS: 4,
            EF.BAB: 1,
            EF.STR_MOD: 1,
            EF.DEX_MOD: 2,
            EF.TEAM: "monsters",
            EF.WEAPON: "morningstar",
            "weapon_damage": "1d6",
            EF.POSITION: {"x": 2, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "small",
            EF.BASE_SPEED: 30,  # MM: goblin base speed
        },
    }

    # Roll initiative using the deterministic initiative system (CP-14)
    rng = RNGManager(master_seed)
    actors = [
        (eid, entities[eid].get(EF.DEX_MOD, 0))
        for eid in entities
    ]
    initiative_rolls, initiative_order = roll_initiative_for_all_actors(actors, rng)

    world_state = WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "turn_counter": 0,
            "round_index": 0,
            "initiative_order": initiative_order,
            "flat_footed_actors": [],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},  # WO-ENGINE-COMBAT-REFLEXES-001
        },
    )

    return ScenarioFixture(
        world_state=world_state,
        master_seed=master_seed,
        actor_id=pc_id,
        turn_index=0,
        next_event_id=0,
        timestamp=0.0,
        initiative_rolls=initiative_rolls,
    )


# ---------------------------------------------------------------------------
# Play one turn controller
# ---------------------------------------------------------------------------

class PlayOneTurnController:
    """Executes a single player turn end-to-end.

    Pipeline:
      1. Parse text input → DeclaredIntent (keyword-based, no LLM)
      2. Resolve via IntentBridge → engine intent OR ClarificationRequest
      3. If clarification needed → return TurnOutput with clarification info
      4. Execute via Box (execute_turn)
      5. Append events to EventLog
      6. Generate narration via deterministic templates
      7. Return immutable TurnOutput
    """

    def __init__(self, event_log: Optional[EventLog] = None) -> None:
        self._bridge = IntentBridge()
        self._narrator = Narrator(use_templates=True)
        self._event_log = event_log or EventLog()

    @property
    def event_log(self) -> EventLog:
        return self._event_log

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def play_turn(
        self,
        fixture: ScenarioFixture,
        input_text: str,
    ) -> TurnOutput:
        """Execute one full turn from text input to narrated output.

        Args:
            fixture: Scenario snapshot (world state, seed, actor, etc.)
            input_text: Raw player text (e.g. "attack the goblin")

        Returns:
            Immutable TurnOutput with all results and provenance.
        """
        ws = deepcopy(fixture.world_state)
        rng = RNGManager(fixture.master_seed)
        view = FrozenWorldStateView(ws)
        hash_before = ws.state_hash()

        # Register entity names for narration
        for eid, entity in ws.entities.items():
            name = entity.get("name", eid)
            self._narrator.register_entity_name(eid, name)

        # Step 1: Parse input → declared intent
        action_type, declared = self._parse_input(input_text)
        if action_type is None:
            return TurnOutput(
                success=False,
                intent_summary=f"unrecognized: {input_text!r}",
                box_status="parse_failed",
                events=(),
                narration_text="",
                narration_provenance="",
                state_hash_before=hash_before,
                state_hash_after=hash_before,
                event_count=0,
                error_message=f"Could not parse action from: {input_text!r}",
            )

        # Step 2: Resolve via IntentBridge
        resolved = self._resolve_intent(
            action_type, declared, fixture.actor_id, view,
        )

        # Step 2a: Clarification needed?
        if isinstance(resolved, ClarificationRequest):
            return TurnOutput(
                success=False,
                intent_summary=f"{action_type}: needs clarification",
                box_status="requires_clarification",
                events=(),
                narration_text="",
                narration_provenance="",
                state_hash_before=hash_before,
                state_hash_after=hash_before,
                event_count=0,
                clarification_needed=True,
                clarification_message=resolved.message,
                clarification_candidates=resolved.candidates,
            )

        # Step 3: Build TurnContext
        actor_entity = ws.entities.get(fixture.actor_id, {})
        actor_team = actor_entity.get(EF.TEAM, "party")
        turn_ctx = TurnContext(
            turn_index=fixture.turn_index,
            actor_id=fixture.actor_id,
            actor_team=actor_team,
        )

        # Step 3a: Convert MoveIntent → FullMoveIntent for Box (CP-16)
        if isinstance(resolved, MoveIntent) and resolved.destination is not None:
            from aidm.core.movement_resolver import build_full_move_intent
            full_intent, move_error = build_full_move_intent(
                fixture.actor_id, resolved.destination, ws,
            )
            if move_error is not None:
                return TurnOutput(
                    success=False,
                    intent_summary=f"move: {move_error}",
                    box_status="requires_clarification",
                    events=(),
                    narration_text="",
                    narration_provenance="",
                    state_hash_before=hash_before,
                    state_hash_after=hash_before,
                    event_count=0,
                    clarification_needed=True,
                    clarification_message=move_error,
                )
            resolved = full_intent

        # Step 4: Execute via Box
        box_result: BoxTurnResult = execute_turn(
            world_state=ws,
            turn_ctx=turn_ctx,
            combat_intent=resolved,
            rng=rng,
            next_event_id=fixture.next_event_id,
            timestamp=fixture.timestamp,
        )

        # Step 5: Append events to log
        for event in box_result.events:
            self._event_log.append(event)

        # Step 6: Narrate
        narration_text, narration_provenance = self._narrate(
            box_result, fixture.actor_id, ws,
        )

        # Step 7: Build output
        hash_after = box_result.world_state.state_hash()
        event_dicts = tuple(e.to_dict() for e in box_result.events)
        intent_summary = self._summarize_intent(action_type, resolved)

        return TurnOutput(
            success=(box_result.status == "ok"),
            intent_summary=intent_summary,
            box_status=box_result.status,
            events=event_dicts,
            narration_text=narration_text,
            narration_provenance=narration_provenance,
            state_hash_before=hash_before,
            state_hash_after=hash_after,
            event_count=len(box_result.events),
        )

    # ------------------------------------------------------------------
    # Internal: parse text → declared intent
    # ------------------------------------------------------------------

    def _parse_input(
        self, text: str,
    ) -> Tuple[Optional[str], Optional[Any]]:
        """Keyword-based parser: text → (action_type, declared_intent).

        Returns (None, None) if unparseable.
        """
        text = text.strip().lower()
        parts = text.split()

        if not parts:
            return None, None

        # Attack
        attack_verbs = {
            "attack", "hit", "strike", "slash", "stab", "shoot",
            "fire", "swing", "punch", "kick", "smite",
        }
        if parts[0] in attack_verbs:
            target_ref = " ".join(parts[1:]) if len(parts) > 1 else None
            # Check for "with <weapon>" pattern
            weapon = None
            if target_ref and " with " in target_ref:
                target_part, weapon_part = target_ref.rsplit(" with ", 1)
                target_ref = target_part.strip()
                weapon = weapon_part.strip()
            # Strip leading articles ("the goblin" → "goblin")
            if target_ref:
                target_ref = _strip_articles(target_ref)
            return "attack", DeclaredAttackIntent(
                target_ref=target_ref,
                weapon=weapon,
            )

        # Move
        move_verbs = {"move", "go", "walk", "run", "step"}
        if parts[0] in move_verbs:
            # "move <x> <y>" or "move to <x> <y>"
            coords = [p for p in parts[1:] if p not in ("to",)]
            if len(coords) >= 2:
                try:
                    x, y = int(coords[0]), int(coords[1])
                    return "move", MoveIntent(destination=Position(x=x, y=y))
                except ValueError:
                    pass
            return "move", MoveIntent(destination=None)

        # End turn
        if text in ("end turn", "pass", "done", "end"):
            return "end_turn", None

        return None, None

    # ------------------------------------------------------------------
    # Internal: resolve declared → engine intent
    # ------------------------------------------------------------------

    def _resolve_intent(
        self,
        action_type: str,
        declared: Any,
        actor_id: str,
        view: FrozenWorldStateView,
    ) -> Union[AttackIntent, StepMoveIntent, MoveIntent, ClarificationRequest]:
        """Route through IntentBridge for name→ID resolution."""
        if action_type == "attack" and isinstance(declared, DeclaredAttackIntent):
            return self._bridge.resolve_attack(actor_id, declared, view)

        if action_type == "move" and isinstance(declared, MoveIntent):
            return self._bridge.resolve_move(actor_id, declared, view)

        # end_turn: no resolution needed — return a sentinel
        if action_type == "end_turn":
            # Return None; execute_turn handles None combat_intent gracefully
            return None  # type: ignore[return-value]

        return ClarificationRequest(
            intent_type=action_type,
            ambiguity_type="ACTION_TYPE_UNKNOWN",
            candidates=(),
            message="I'm not sure how to handle that.",
        )

    # ------------------------------------------------------------------
    # Internal: narrate from template
    # ------------------------------------------------------------------

    def _narrate(
        self,
        box_result: BoxTurnResult,
        actor_id: str,
        original_state: WorldState,
    ) -> Tuple[str, str]:
        """Generate narration from Box result using deterministic templates.

        Returns (narration_text, provenance_tag).
        """
        token = box_result.narration or "unknown"

        # Extract damage and target from events
        damage = 0
        target_name = "the target"
        actor_name = original_state.entities.get(actor_id, {}).get(
            "name", actor_id,
        )
        weapon_name = original_state.entities.get(actor_id, {}).get(
            EF.WEAPON, "weapon",
        )
        target_defeated = False

        for event in box_result.events:
            payload = event.payload if hasattr(event, "payload") else {}
            if event.event_type == "attack_roll":
                tid = payload.get("target_id", "")
                if tid:
                    target_name = original_state.entities.get(
                        tid, {},
                    ).get("name", tid)
            if event.event_type == "hp_changed":
                delta = payload.get("delta", 0)
                if delta < 0:
                    damage = abs(delta)
                tid = payload.get("entity_id", "")
                if tid:
                    target_name = original_state.entities.get(
                        tid, {},
                    ).get("name", tid)
            if event.event_type == "entity_defeated":
                target_defeated = True
                tid = payload.get("entity_id", "")
                if tid:
                    target_name = original_state.entities.get(
                        tid, {},
                    ).get("name", tid)

        # Compute severity from damage vs max HP
        severity = "minor"
        if damage > 0:
            # Try to find target's max HP
            for eid, entity in original_state.entities.items():
                if entity.get("name", eid) == target_name or eid == target_name:
                    max_hp = entity.get(EF.HP_MAX, 1)
                    pct = damage / max(max_hp, 1)
                    if target_defeated or pct > 0.8:
                        severity = "lethal"
                    elif pct > 0.6:
                        severity = "devastating"
                    elif pct > 0.4:
                        severity = "severe"
                    elif pct > 0.2:
                        severity = "moderate"
                    break

        template = NarrationTemplates.get_template(token, severity)
        try:
            text = template.format(
                actor=actor_name,
                target=target_name,
                weapon=weapon_name,
                damage=damage,
            )
        except KeyError:
            text = template

        return text, "[NARRATIVE:TEMPLATE]"

    # ------------------------------------------------------------------
    # Internal: summarize intent for display
    # ------------------------------------------------------------------

    @staticmethod
    def _summarize_intent(action_type: str, resolved: Any) -> str:
        if isinstance(resolved, AttackIntent):
            return (
                f"attack: attacker={resolved.attacker_id} "
                f"target={resolved.target_id} "
                f"bonus=+{resolved.attack_bonus}"
            )
        if isinstance(resolved, StepMoveIntent):
            return f"move: destination=({resolved.to_pos.x}, {resolved.to_pos.y})"
        if isinstance(resolved, FullMoveIntent):
            return f"move: destination=({resolved.to_pos.x}, {resolved.to_pos.y})"
        if isinstance(resolved, MoveIntent):
            dest = resolved.destination
            if dest:
                return f"move: destination=({dest.x}, {dest.y})"
            return "move: no destination"
        if action_type == "end_turn":
            return "end_turn"
        return f"{action_type}: (resolved)"
