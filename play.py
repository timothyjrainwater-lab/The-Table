#!/usr/bin/env python3
"""D&D 3.5e Combat CLI — play the AIDM engine from your terminal.

Usage:
    python play.py              # 3v3 party combat, seed 42
    python play.py --seed 99    # Same scenario, different dice

Party: Fighter (Aldric), Cleric (Elara), Rogue (Snitch) vs 3 Goblins.
You control all party members. Enemies act automatically.

Commands during play:
    attack <target>             attack goblin warrior
    attack <target> with <wpn>  attack goblin with longsword
    move <x> <y>               move 5 3
    cast <spell> on <target>   cast magic missile on goblin
    end / pass                 end your turn
    quit                       exit the game
"""

import argparse
import os
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple

from aidm.core.play_loop import TurnContext, TurnResult, execute_turn
from aidm.core.rng_manager import RNGManager
from aidm.core.state import FrozenWorldStateView, WorldState
from aidm.interaction.intent_bridge import ClarificationRequest, IntentBridge
from aidm.runtime.display import format_world_summary
from aidm.runtime.play_controller import build_simple_combat_fixture
from aidm.schemas.attack import AttackIntent, StepMoveIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import DeclaredAttackIntent, MoveIntent
from aidm.schemas.position import Position

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ARTICLES = {"the", "a", "an"}


def _strip_articles(text: str) -> str:
    words = text.split()
    while words and words[0] in _ARTICLES:
        words.pop(0)
    return " ".join(words) if words else text


_ATTACK_VERBS = {
    "attack", "hit", "strike", "slash", "stab",
    "shoot", "fire", "swing", "punch", "kick", "smite",
}
_MOVE_VERBS = {"move", "go", "walk", "run", "step"}


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def parse_input(text: str) -> Tuple[Optional[str], Any]:
    """Keyword-based parser.  Returns (action_type, declared_intent) or (None, None)."""
    text = text.strip().lower()
    parts = text.split()
    if not parts:
        return None, None

    # Two-word commands — check before single-word verb split
    if text.startswith("full attack"):
        target_ref = text[len("full attack"):].strip()
        target_ref = _strip_articles(target_ref) if target_ref else None
        return "full_attack", DeclaredAttackIntent(target_ref=target_ref, weapon=None)

    if text.startswith("bull rush") or text.startswith("bullrush"):
        prefix_len = len("bull rush") if text.startswith("bull rush") else len("bullrush")
        target_ref = text[prefix_len:].strip()
        target_ref = _strip_articles(target_ref) if target_ref else None
        return "bull_rush", DeclaredAttackIntent(target_ref=target_ref, weapon=None)

    if text.startswith("end turn"):
        return "end_turn", None

    verb = parts[0]

    # Attack
    if verb in _ATTACK_VERBS:
        target_ref = " ".join(parts[1:]) if len(parts) > 1 else None
        weapon = None
        if target_ref and " with " in target_ref:
            target_ref, weapon = target_ref.rsplit(" with ", 1)
            target_ref, weapon = target_ref.strip(), weapon.strip()
        if target_ref:
            target_ref = _strip_articles(target_ref)
        return "attack", DeclaredAttackIntent(target_ref=target_ref, weapon=weapon)

    # Move
    if verb in _MOVE_VERBS:
        coords = [p for p in parts[1:] if p != "to"]
        if len(coords) >= 2:
            try:
                return "move", MoveIntent(destination=Position(x=int(coords[0]), y=int(coords[1])))
            except ValueError:
                pass
        return "move", MoveIntent(destination=None)

    # Cast
    if verb == "cast":
        if len(parts) < 2:
            return "cast_no_spell", None
        rest = " ".join(parts[1:])
        spell_name, target_ref = rest, None
        for sep in (" on ", " at "):
            if sep in rest:
                spell_name, target_ref = rest.split(sep, 1)
                spell_name, target_ref = spell_name.strip(), _strip_articles(target_ref.strip())
                break
        if target_ref and target_ref.lower() in ("self", "me", "myself"):
            target_ref = "__SELF__"
        return "cast", (spell_name, target_ref)

    # Combat maneuvers (single-word verbs)
    if verb in ("trip", "disarm", "grapple", "overrun"):
        target_ref = " ".join(parts[1:]) if len(parts) > 1 else None
        if target_ref:
            target_ref = _strip_articles(target_ref)
        return verb, DeclaredAttackIntent(target_ref=target_ref, weapon=None)

    if verb == "sunder":
        target_ref = " ".join(parts[1:]) if len(parts) > 1 else None
        target_item = "weapon"
        if target_ref and target_ref.endswith(" shield"):
            target_ref = target_ref[:-len(" shield")].strip()
            target_item = "shield"
        if target_ref:
            target_ref = _strip_articles(target_ref)
        return "sunder", DeclaredAttackIntent(target_ref=target_ref, weapon=target_item)

    # End turn
    if text in ("pass", "done", "end"):
        return "end_turn", None

    # Help / status
    if verb in ("help", "?", "commands"):
        return "help", None
    if verb in ("status", "hp", "look"):
        return "status", None

    return None, None


_HELP_TEXT = """\
  Commands:
    attack <target>             attack goblin warrior
    attack <target> with <wpn>  attack goblin with longsword
    full attack <target>        full attack goblin warrior
    cast <spell> on <target>    cast magic missile on goblin
    move <x> <y>                move 5 3
    trip <target>               trip goblin warrior
    bull rush <target>          bull rush goblin warrior
    disarm <target>             disarm goblin warrior
    grapple <target>            grapple goblin warrior
    sunder <target>             sunder goblin warrior
    overrun <target>            overrun goblin warrior
    status                      show HP, AC, BAB, conditions
    end / pass                  end your turn
    help                        show this message
    quit                        exit the game"""


# ---------------------------------------------------------------------------
# Turn execution
# ---------------------------------------------------------------------------

def resolve_and_execute(
    ws: WorldState,
    actor_id: str,
    action_type: str,
    declared: Any,
    seed: int,
    turn_index: int,
    next_event_id: int,
) -> TurnResult:
    """Parse + resolve + execute one turn via the real engine."""
    bridge = IntentBridge()
    rng = RNGManager(seed + turn_index)
    view = FrozenWorldStateView(ws)
    ws_copy = deepcopy(ws)

    # Resolve declared intent -> engine intent
    if action_type == "attack":
        resolved = bridge.resolve_attack(actor_id, declared, view)
    elif action_type == "full_attack":
        resolved = bridge.resolve_attack(actor_id, declared, view)
        if isinstance(resolved, ClarificationRequest):
            return TurnResult(
                status="requires_clarification", world_state=ws,
                events=[], turn_index=turn_index, failure_reason=resolved.message,
            )
        # Promote AttackIntent to FullAttackIntent
        from aidm.core.full_attack_resolver import FullAttackIntent
        entity = ws_copy.entities[actor_id]
        resolved = FullAttackIntent(
            attacker_id=actor_id,
            target_id=resolved.target_id,
            base_attack_bonus=entity.get(EF.BAB, 1),
            weapon=resolved.weapon,
        )
    elif action_type == "move":
        resolved = bridge.resolve_move(actor_id, declared, view)
    elif action_type == "cast":
        spell_name, target_ref = declared
        from aidm.schemas.intents import CastSpellIntent
        cast_intent = CastSpellIntent(spell_name=spell_name)
        actual_target_ref = actor_id if target_ref == "__SELF__" else target_ref
        resolved = bridge.resolve_spell(actor_id, cast_intent, view, target_entity_ref=actual_target_ref)
    elif action_type in ("bull_rush", "trip", "overrun", "sunder", "disarm", "grapple"):
        resolved = bridge.resolve_attack(actor_id, declared, view)
        if isinstance(resolved, ClarificationRequest):
            return TurnResult(
                status="requires_clarification", world_state=ws,
                events=[], turn_index=turn_index, failure_reason=resolved.message,
            )
        from aidm.schemas.maneuvers import (
            BullRushIntent, TripIntent, OverrunIntent,
            SunderIntent, DisarmIntent, GrappleIntent,
        )
        target_id = resolved.target_id
        if action_type == "bull_rush":
            resolved = BullRushIntent(attacker_id=actor_id, target_id=target_id)
        elif action_type == "trip":
            resolved = TripIntent(attacker_id=actor_id, target_id=target_id)
        elif action_type == "overrun":
            resolved = OverrunIntent(attacker_id=actor_id, target_id=target_id)
        elif action_type == "sunder":
            resolved = SunderIntent(attacker_id=actor_id, target_id=target_id, target_item=declared.weapon or "weapon")
        elif action_type == "disarm":
            resolved = DisarmIntent(attacker_id=actor_id, target_id=target_id)
        elif action_type == "grapple":
            resolved = GrappleIntent(attacker_id=actor_id, target_id=target_id)
    else:
        resolved = None

    # Clarification needed?
    if isinstance(resolved, ClarificationRequest):
        return TurnResult(
            status="requires_clarification",
            world_state=ws,
            events=[],
            turn_index=turn_index,
            failure_reason=resolved.message,
        )

    # MoveIntent -> StepMoveIntent
    if isinstance(resolved, MoveIntent) and resolved.destination is not None:
        pos = ws_copy.entities[actor_id].get(EF.POSITION, {"x": 0, "y": 0})
        try:
            resolved = StepMoveIntent(
                actor_id=actor_id,
                from_pos=Position(x=pos["x"], y=pos["y"]),
                to_pos=Position(x=resolved.destination.x, y=resolved.destination.y),
            )
        except ValueError:
            cur = f"({pos['x']},{pos['y']})"
            dest = f"({resolved.destination.x},{resolved.destination.y})"
            return TurnResult(
                status="requires_clarification",
                world_state=ws,
                events=[],
                turn_index=turn_index,
                failure_reason=f"Can only move to adjacent squares. You are at {cur}, {dest} is too far.",
            )

    actor_team = ws_copy.entities.get(actor_id, {}).get(EF.TEAM, "party")
    ctx = TurnContext(turn_index=turn_index, actor_id=actor_id, actor_team=actor_team)

    return execute_turn(
        world_state=ws_copy,
        turn_ctx=ctx,
        combat_intent=resolved,
        rng=rng,
        next_event_id=next_event_id,
        timestamp=float(turn_index),
    )


# ---------------------------------------------------------------------------
# Enemy AI
# ---------------------------------------------------------------------------

def pick_enemy_target(ws: WorldState, actor_id: str) -> Optional[str]:
    actor_team = ws.entities[actor_id].get(EF.TEAM, "monsters")
    for eid in sorted(ws.entities):
        e = ws.entities[eid]
        if e.get(EF.TEAM) != actor_team and not e.get(EF.DEFEATED, False):
            return eid
    return None


def run_enemy_turn(
    ws: WorldState, actor_id: str, seed: int, turn_index: int, next_event_id: int,
) -> TurnResult:
    target_id = pick_enemy_target(ws, actor_id)
    if target_id is None:
        return TurnResult(status="ok", world_state=ws, events=[], turn_index=turn_index)

    entity = ws.entities[actor_id]
    weapon = Weapon(
        damage_dice=entity.get("weapon_damage", "1d4"),
        damage_bonus=0,   # resolver adds STR_MOD from entity
        damage_type="piercing",
    )
    intent = AttackIntent(
        attacker_id=actor_id,
        target_id=target_id,
        attack_bonus=entity.get(EF.ATTACK_BONUS, 0),
        weapon=weapon,
    )
    rng = RNGManager(seed + turn_index)
    ws_copy = deepcopy(ws)
    ctx = TurnContext(
        turn_index=turn_index,
        actor_id=actor_id,
        actor_team=entity.get(EF.TEAM, "monsters"),
    )
    return execute_turn(
        world_state=ws_copy, turn_ctx=ctx, combat_intent=intent,
        rng=rng, next_event_id=next_event_id, timestamp=float(turn_index),
    )


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def _name(ws: WorldState, eid: str) -> str:
    return ws.entities.get(eid, {}).get("name", eid)


def format_events(events, ws: WorldState) -> str:
    lines = []
    for ev in events:
        p = ev.payload
        if ev.event_type == "spell_cast":
            caster_id = p.get("caster_id", "")
            caster = _name(ws, caster_id)
            spell = p.get("spell_name", p.get("spell_id", "a spell"))
            targets = p.get("affected_entities", [])
            # Self-only spells: show "on themselves" instead of repeating the name
            if targets == [caster_id]:
                lines.append(f"  {caster} casts {spell} on themselves!")
            elif targets:
                target_names = [_name(ws, t) for t in targets]
                lines.append(f"  {caster} casts {spell} on {', '.join(target_names)}!")
            else:
                lines.append(f"  {caster} casts {spell}!")
        elif ev.event_type == "spell_cast_failed":
            reason = p.get("reason", "unknown reason")
            spell = p.get("spell_name", p.get("spell_id", "spell"))
            lines.append(f"  Spell failed ({spell}): {reason}")
        elif ev.event_type == "attack_roll":
            d20 = p.get("d20_result", "?")
            bonus = p.get("attack_bonus", 0)
            total = p.get("total", 0)
            ac = p.get("target_ac", 0)
            hit = p.get("hit", False)
            lines.append(f"  Roll: [{d20}] + {bonus} = {total} vs AC {ac} -> {'HIT' if hit else 'MISS'}")
        elif ev.event_type == "damage_roll":
            dice = p.get("damage_dice", "?")
            final = p.get("final_damage", 0)
            lines.append(f"  Damage: {dice} -> {final} hp")
        elif ev.event_type == "hp_changed":
            name = _name(ws, p.get("entity_id", ""))
            hp_before = p.get("hp_before") if p.get("hp_before") is not None else p.get("old_hp", "?")
            hp_after = p.get("hp_after") if p.get("hp_after") is not None else p.get("new_hp", "?")
            source = p.get("source", "")
            if source.startswith("spell:"):
                spell_name = source[len("spell:"):]
                delta = p.get("delta", 0)
                if delta > 0:
                    lines.append(f"  {name}: healed {delta} HP ({spell_name}) — HP {hp_before} -> {hp_after}")
                else:
                    lines.append(f"  {name}: {abs(delta)} damage ({spell_name}) — HP {hp_before} -> {hp_after}")
            else:
                lines.append(f"  {name}: HP {hp_before} -> {hp_after}")
        elif ev.event_type == "entity_defeated":
            name = _name(ws, p.get("entity_id", ""))
            lines.append(f"  *** {name} is DEFEATED! ***")
        elif ev.event_type == "condition_applied":
            name = _name(ws, p.get("entity_id", p.get("target_id", "")))
            condition = p.get("condition", p.get("condition_type", "unknown"))
            source = p.get("source", "")
            duration = p.get("duration_rounds")
            # Spell-sourced conditions: "gains Shield effect" instead of "is now shield"
            if source.startswith("spell:"):
                label = condition.replace("_", " ").title()
                dur_str = f" ({duration} rounds)" if duration else ""
                lines.append(f"  {name} gains {label} effect{dur_str}")
            elif duration:
                lines.append(f"  {name} is now {condition} ({duration} rounds)")
            else:
                lines.append(f"  {name} is now {condition}")
        elif ev.event_type == "condition_removed":
            name = _name(ws, p.get("entity_id", ""))
            condition = p.get("condition", "unknown")
            lines.append(f"  {name} is no longer {condition}")
        elif ev.event_type in ("movement", "movement_declared"):
            from_pos = p.get("from_pos", {})
            to_pos = p.get("to_pos", {})
            to_x = to_pos.get("x", p.get("to_x", "?"))
            to_y = to_pos.get("y", p.get("to_y", "?"))
            actor = _name(ws, p.get("actor_id", ""))
            if actor:
                lines.append(f"  {actor} moves to ({to_x}, {to_y})")
            else:
                lines.append(f"  Moved to ({to_x}, {to_y})")
        # AoO events
        elif ev.event_type == "aoo_triggered":
            reactor = _name(ws, p.get("reactor_id", ""))
            provoker = _name(ws, p.get("provoker_id", ""))
            lines.append(f"  {reactor} makes an attack of opportunity against {provoker}!")
        elif ev.event_type == "tumble_check":
            entity = _name(ws, p.get("entity_id", ""))
            success = p.get("success", False)
            total = p.get("total", 0)
            dc = p.get("dc", 15)
            result_str = "success" if success else "failure"
            lines.append(f"  {entity} attempts to tumble (DC {dc}: rolled {total} — {result_str}!)")
        elif ev.event_type == "aoo_avoided_by_tumble":
            entity = _name(ws, p.get("entity_id", ""))
            lines.append(f"  {entity} tumbles past safely!")
        elif ev.event_type == "aoo_blocked_by_cover":
            reactor = _name(ws, p.get("reactor_id", ""))
            lines.append(f"  {reactor}'s AoO blocked by cover")
        # Maneuver events
        elif ev.event_type in ("bull_rush_declared", "trip_declared", "overrun_declared",
                               "sunder_declared", "disarm_declared", "grapple_declared"):
            attacker = _name(ws, p.get("attacker_id", ""))
            target = _name(ws, p.get("target_id", ""))
            maneuver = ev.event_type.replace("_declared", "").replace("_", " ")
            lines.append(f"  {attacker} attempts to {maneuver} {target}!")
        elif ev.event_type == "opposed_check":
            attacker_total = p.get("attacker_total", 0)
            defender_total = p.get("defender_total", 0)
            lines.append(f"  Opposed check: {attacker_total} vs {defender_total}")
        elif ev.event_type == "touch_attack_roll":
            d20 = p.get("d20_result", "?")
            total = p.get("total", 0)
            ac = p.get("target_touch_ac", p.get("target_ac", 0))
            hit = p.get("hit", False)
            lines.append(f"  Touch attack: [{d20}] = {total} vs Touch AC {ac} -> {'HIT' if hit else 'MISS'}")
        elif ev.event_type == "overrun_avoided":
            defender = _name(ws, p.get("defender_id", ""))
            lines.append(f"  {defender} steps aside!")
        elif ev.event_type in ("bull_rush_success", "trip_success", "overrun_success",
                               "sunder_success", "disarm_success", "grapple_success",
                               "counter_trip_success", "counter_disarm_success"):
            maneuver = ev.event_type.replace("_success", "").replace("_", " ").title()
            lines.append(f"  {maneuver} succeeds!")
        elif ev.event_type in ("bull_rush_failure", "trip_failure", "overrun_failure",
                               "sunder_failure", "disarm_failure", "grapple_failure",
                               "counter_trip_failure", "counter_disarm_failure"):
            maneuver = ev.event_type.replace("_failure", "").replace("_", " ").title()
            lines.append(f"  {maneuver} fails!")
    return "\n".join(lines) if lines else "  (no visible effect)"


def show_status(ws: WorldState) -> None:
    for eid in sorted(ws.entities):
        e = ws.entities[eid]
        if e.get(EF.DEFEATED, False):
            continue
        hp = e.get(EF.HP_CURRENT, "?")
        mx = e.get(EF.HP_MAX, "?")
        ac = e.get(EF.AC, "?")
        bab = e.get(EF.BAB, 0)
        pos = e.get(EF.POSITION, {})
        pos_str = f"({pos.get('x','?')},{pos.get('y','?')})"
        conditions = e.get(EF.CONDITIONS, {})
        if isinstance(conditions, dict) and conditions:
            cond_str = ", ".join(sorted(conditions.keys()))
            cond_display = f"  *{cond_str}*"
        else:
            cond_display = ""
        bab_str = f"+{bab}" if bab >= 0 else str(bab)
        print(f"  {e.get('name', eid):20s}  HP {hp}/{mx}  AC {ac}  BAB {bab_str}  {pos_str}{cond_display}")


# ---------------------------------------------------------------------------
# Combat state
# ---------------------------------------------------------------------------

def is_combat_over(ws: WorldState) -> Tuple[bool, str]:
    party = any(not e.get(EF.DEFEATED, False) for e in ws.entities.values() if e.get(EF.TEAM) == "party")
    monsters = any(not e.get(EF.DEFEATED, False) for e in ws.entities.values() if e.get(EF.TEAM) == "monsters")
    if not monsters:
        return True, "All enemies defeated! Victory!"
    if not party:
        return True, "The party has fallen. Defeat."
    return False, ""


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

_LOG_DIR = Path(__file__).resolve().parent / "runtime_logs"


class _TeeWriter:
    """Tee stdout to a log file while preserving normal output."""
    def __init__(self, original, logfile):
        self._original = original
        self._logfile = logfile
    def write(self, text):
        self._original.write(text)
        self._logfile.write(text)
    def flush(self):
        self._original.flush()
        self._logfile.flush()


def main(seed: int = 42, input_fn=input) -> None:
    # Transcript autologging — only for interactive sessions (not test mocks)
    log_file = None
    tee = None
    if input_fn is input:
        _LOG_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = _LOG_DIR / f"play_{ts}.log"
        log_file = open(log_path, "w", encoding="utf-8")
        tee = _TeeWriter(sys.stdout, log_file)
        sys.stdout = tee
        # Write LATEST pointer
        (_LOG_DIR / "LATEST").write_text(log_path.name, encoding="utf-8")
        # Wrap input to record player commands
        _real_input = input_fn
        def _logging_input(prompt=""):
            text = _real_input(prompt)
            log_file.write(f"{prompt}{text}\n")
            return text
        input_fn = _logging_input

    try:
        _main_loop(seed, input_fn)
    finally:
        if tee is not None:
            sys.stdout = tee._original
        if log_file is not None:
            log_file.close()


def _main_loop(seed: int, input_fn) -> None:
    fixture = build_simple_combat_fixture(master_seed=seed)
    ws = fixture.world_state
    init_order = list(ws.active_combat["initiative_order"])
    turn_index = 0
    next_event_id = 0
    round_number = 1

    print("=" * 50)
    print("  D&D 3.5e Combat -- AIDM Engine")
    print("=" * 50)
    print()

    # Display rolled initiative order
    if fixture.initiative_rolls:
        print("  Turn Order (d20 + DEX modifier):")
        # Sort rolls by the computed initiative order for display
        order_map = {eid: idx for idx, eid in enumerate(init_order)}
        sorted_rolls = sorted(fixture.initiative_rolls, key=lambda r: order_map.get(r.actor_id, 99))
        for i, roll in enumerate(sorted_rolls, 1):
            entity = ws.entities.get(roll.actor_id, {})
            name = entity.get("name", roll.actor_id)
            team = entity.get(EF.TEAM, "")
            marker = "*" if team == "party" else " "
            dex_str = f"+{roll.dex_modifier}" if roll.dex_modifier >= 0 else str(roll.dex_modifier)
            print(f"   {marker} {i}. {name:20s}  {roll.total:2d}  (d20={roll.d20_roll}, DEX {dex_str})")
        print("     (* = your party)")
        print()

    show_status(ws)
    print()
    print("Type 'help' for commands, or 'quit' to exit.")
    print()

    print(f"\n{'=' * 20} Round {round_number} {'=' * 20}")

    while True:
        over, reason = is_combat_over(ws)
        if over:
            print(f"\n{'=' * 50}")
            print(f"  {reason}")
            print(f"{'=' * 50}")
            return

        for actor_id in init_order:
            entity = ws.entities.get(actor_id, {})
            if entity.get(EF.DEFEATED, False):
                continue

            name = entity.get("name", actor_id)
            team = entity.get(EF.TEAM, "party")

            if team == "party":
                # Player turn
                print(f"\n--- {name}'s Turn ---")
                show_status(ws)

                while True:
                    try:
                        text = input_fn(f"\n{name}> ")
                    except (EOFError, KeyboardInterrupt):
                        print("\nFarewell!")
                        return
                    text = text.strip()
                    if not text:
                        continue
                    if text.lower() in ("quit", "exit", "q"):
                        print("Farewell!")
                        return

                    action_type, declared = parse_input(text)
                    if action_type is None:
                        print("  Unknown command.")
                        print(_HELP_TEXT)
                        continue
                    if action_type == "help":
                        print(_HELP_TEXT)
                        continue
                    if action_type == "status":
                        show_status(ws)
                        continue
                    if action_type == "cast_no_spell":
                        print("  Cast what? Try: cast magic missile on goblin")
                        continue
                    if action_type == "end_turn":
                        print(f"  {name} ends their turn.")
                        break

                    result = resolve_and_execute(ws, actor_id, action_type, declared, seed, turn_index, next_event_id)

                    if result.status == "requires_clarification":
                        print(f"  {result.failure_reason}")
                        continue

                    print(format_events(result.events, ws))
                    if result.status == "ok":
                        ws = result.world_state
                        next_event_id += len(result.events)
                        turn_index += 1
                        break
                    else:
                        print(f"  Failed: {result.failure_reason or result.status}")
                        continue
            else:
                # Enemy turn
                target = pick_enemy_target(ws, actor_id)
                if target is None:
                    continue
                print(f"\n--- {name} attacks {_name(ws, target)}! ---")
                result = run_enemy_turn(ws, actor_id, seed, turn_index, next_event_id)
                print(format_events(result.events, ws))
                if result.status == "ok":
                    ws = result.world_state
                    next_event_id += len(result.events)
                    turn_index += 1

            over, reason = is_combat_over(ws)
            if over:
                break

        # Round boundary — all actors have acted, new round begins
        round_number += 1
        ws.active_combat["round_index"] = round_number - 1
        print(f"\n{'=' * 20} Round {round_number} {'=' * 20}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="D&D 3.5e Combat CLI")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")
    args = parser.parse_args()
    main(seed=args.seed)
