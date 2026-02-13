#!/usr/bin/env python3
"""WO-047: Immersive Micro-Scenario — Text-First Dungeon Crawl

Runs a scripted 5-turn mini dungeon through the SessionOrchestrator:

    Room A: Goblin Ambush    → attack goblin
    Room A: Goblin Ambush    → attack goblin (finish it)
    Transition:              → go east to Rest Chamber
    Room B: Rest Chamber     → rest (heal up)
    Transition:              → go north to Boss Room

Each turn prints:
    - What the player said
    - What the Box resolved (events)
    - What the DM narrated (template text + provenance)
    - Before/after HP for affected entities
    - Running state hash

No new systems. No new contracts. No architecture changes.
Just the orchestrator doing what it was built to do.

Usage:
    python demo_micro_scenario.py
"""

import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent
if not (PROJECT_ROOT / "aidm").is_dir():
    print("ERROR: Must be run from the repository root.", file=sys.stderr)
    sys.exit(2)
sys.path.insert(0, str(PROJECT_ROOT))

from aidm.core.state import WorldState
from aidm.interaction.intent_bridge import IntentBridge
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.scene_manager import Exit, SceneManager, SceneState
from aidm.narration.guarded_narration_service import GuardedNarrationService
from aidm.runtime.session_orchestrator import SessionOrchestrator
from aidm.schemas.entity_fields import EF
from aidm.spark.dm_persona import DMPersona

# ── ANSI ─────────────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

DIVIDER = f"{DIM}{'-' * 60}{RESET}"


def banner(text: str) -> None:
    width = 60
    print(f"\n{BOLD}{BLUE}{'=' * width}{RESET}")
    print(f"{BOLD}{BLUE}  {text}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * width}{RESET}")


def scene_banner(name: str, desc: str) -> None:
    print(f"\n{BOLD}{MAGENTA}+{'-' * 58}+{RESET}")
    print(f"{BOLD}{MAGENTA}|  {name:56s}|{RESET}")
    print(f"{BOLD}{MAGENTA}+{'-' * 58}+{RESET}")
    print(f"  {DIM}{desc}{RESET}")


def player_says(text: str) -> None:
    print(f"\n  {BOLD}{CYAN}> {text}{RESET}")


def dm_says(text: str, provenance: str) -> None:
    print(f"\n  {BOLD}\"{text}\"{RESET}")
    print(f"  {DIM}-- provenance: {provenance}{RESET}")


def hp_bar(name: str, current: int, maximum: int, defeated: bool = False) -> str:
    if defeated:
        return f"{name}: {RED}{BOLD}DEFEATED{RESET} ({current}/{maximum})"
    pct = max(0, current / maximum) if maximum > 0 else 0
    if pct > 0.5:
        color = GREEN
    elif pct > 0.25:
        color = YELLOW
    else:
        color = RED
    filled = int(pct * 20)
    bar = f"{'#' * filled}{'.' * (20 - filled)}"
    return f"{name}: {color}{bar}{RESET} {current}/{maximum}"


def show_party_status(orch: SessionOrchestrator) -> None:
    print(f"\n  {BOLD}Party Status:{RESET}")
    for eid, entity in orch.world_state.entities.items():
        if entity.get(EF.TEAM) == "party":
            name = entity.get("name", eid)
            hp = entity.get(EF.HP_CURRENT, 0)
            hp_max = entity.get(EF.HP_MAX, 1)
            defeated = entity.get(EF.DEFEATED, False)
            print(f"    {hp_bar(name, hp, hp_max, defeated)}")
    # Show enemies too
    enemies = [
        (eid, e) for eid, e in orch.world_state.entities.items()
        if e.get(EF.TEAM) == "enemy"
    ]
    if enemies:
        print(f"  {BOLD}Enemies:{RESET}")
        for eid, entity in enemies:
            name = entity.get("name", eid)
            hp = entity.get(EF.HP_CURRENT, 0)
            hp_max = entity.get(EF.HP_MAX, 1)
            defeated = entity.get(EF.DEFEATED, False)
            print(f"    {hp_bar(name, hp, hp_max, defeated)}")


def show_events_summary(events: tuple) -> None:
    if not events:
        return
    for e in events:
        etype = e.get("type", "?")
        if etype == "turn_start":
            continue
        elif etype == "turn_end":
            continue
        elif etype == "attack_roll":
            d20 = e.get("d20_result", "?")
            total = e.get("total", "?")
            ac = e.get("target_ac", "?")
            hit = e.get("hit", False)
            hit_str = f"{GREEN}hit{RESET}" if hit else f"{RED}miss{RESET}"
            print(f"    {DIM}d20({d20}) + bonus = {total} vs AC {ac} -> {hit_str}{RESET}")
        elif etype == "damage_roll":
            total = e.get("damage_total", "?")
            dtype = e.get("damage_type", "?")
            print(f"    {DIM}{total} {dtype} damage{RESET}")
        elif etype == "hp_changed":
            eid = e.get("entity_id", "?")
            before = e.get("hp_before", "?")
            after = e.get("hp_after", "?")
            delta = e.get("delta", 0)
            print(f"    {DIM}{eid}: {before} -> {after} ({delta:+d} HP){RESET}")
        elif etype == "entity_defeated":
            eid = e.get("entity_id", "?")
            print(f"    {RED}{BOLD}{eid} is defeated!{RESET}")
        elif etype == "movement":
            x = e.get("destination_x", "?")
            y = e.get("destination_y", "?")
            print(f"    {DIM}moved to ({x}, {y}){RESET}")
        elif etype == "scene_transition":
            print(f"    {DIM}scene transition{RESET}")
        elif etype == "rest_healing":
            eid = e.get("entity_id", "?")
            healed = e.get("hp_healed", "?")
            print(f"    {DIM}{eid}: healed {healed} HP{RESET}")
        else:
            print(f"    {DIM}{etype}{RESET}")


# ── World Setup ──────────────────────────────────────────────────────

def build_dungeon():
    """Build a 3-room dungeon and party for the micro-scenario."""

    scenes = {
        "room_a": SceneState(
            scene_id="room_a",
            name="The Goblin Ambush",
            description="A narrow corridor opens into a torch-lit chamber. "
            "Two goblins crouch behind overturned tables, "
            "crude spears at the ready.",
            exits=[
                Exit(
                    exit_id="east",
                    destination_scene_id="room_b",
                    description="A heavy wooden door leads east",
                    locked=False,
                    hidden=False,
                ),
            ],
        ),
        "room_b": SceneState(
            scene_id="room_b",
            name="The Rest Chamber",
            description="A quiet alcove with dusty bedrolls and a cold fire pit. "
            "The air smells of old smoke and damp stone.",
            exits=[
                Exit(
                    exit_id="west",
                    destination_scene_id="room_a",
                    description="Back to the ambush chamber",
                    locked=False,
                    hidden=False,
                ),
                Exit(
                    exit_id="north",
                    destination_scene_id="room_c",
                    description="A reinforced iron door leads north",
                    locked=False,
                    hidden=False,
                ),
            ],
        ),
        "room_c": SceneState(
            scene_id="room_c",
            name="The Bone Throne",
            description="A vast, cold chamber. An ogre sits on a throne "
            "of yellowed bone, watching the doorway with dull, "
            "hungry eyes.",
            exits=[
                Exit(
                    exit_id="south",
                    destination_scene_id="room_b",
                    description="Retreat to the rest chamber",
                    locked=False,
                    hidden=False,
                ),
            ],
        ),
    }

    world_state = WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Kael the Steadfast",
                EF.TEAM: "party",
                EF.LEVEL: 3,
                EF.HP_CURRENT: 28,
                EF.HP_MAX: 28,
                EF.AC: 17,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 7,
                EF.BAB: 3,
                EF.STR_MOD: 3,
                EF.WEAPON: "longsword",
                "weapon_damage": "1d8+3",
                EF.DEX_MOD: 1,
                EF.POSITION: {"x": 5, "y": 5},
            },
            "goblin_1": {
                EF.ENTITY_ID: "goblin_1",
                "name": "Goblin Spearman",
                EF.TEAM: "enemy",
                EF.LEVEL: 1,
                EF.HP_CURRENT: 5,
                EF.HP_MAX: 5,
                EF.AC: 14,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 2,
                EF.DEX_MOD: 1,
                EF.POSITION: {"x": 6, "y": 5},
            },
        },
    )

    return scenes, world_state


# ── Scenario Runner ──────────────────────────────────────────────────

def find_working_seed(scenes, world_state_factory, target="Goblin Spearman", max_seeds=200):
    """Find a seed where the fighter hits the goblin on the first attack.

    We want a satisfying demo — not a whiff.
    """
    for seed in range(max_seeds):
        ws = world_state_factory()
        orch = SessionOrchestrator(
            world_state=ws,
            intent_bridge=IntentBridge(),
            scene_manager=SceneManager(scenes=scenes),
            dm_persona=DMPersona(),
            narration_service=GuardedNarrationService(),
            context_assembler=ContextAssembler(token_budget=800),
            master_seed=seed,
        )
        orch.load_scene("room_a")
        result = orch.process_text_turn(f"attack {target}", "pc_fighter")
        hit = any(
            e.get("type") == "attack_roll" and e.get("hit", False)
            for e in result.events
        )
        defeated = any(
            e.get("type") == "entity_defeated"
            for e in result.events
        )
        if hit and defeated:
            return seed
    # Fallback — just take a hit without defeat
    for seed in range(max_seeds):
        ws = world_state_factory()
        orch = SessionOrchestrator(
            world_state=ws,
            intent_bridge=IntentBridge(),
            scene_manager=SceneManager(scenes=scenes),
            dm_persona=DMPersona(),
            narration_service=GuardedNarrationService(),
            context_assembler=ContextAssembler(token_budget=800),
            master_seed=seed,
        )
        orch.load_scene("room_a")
        result = orch.process_text_turn(f"attack {target}", "pc_fighter")
        hit = any(
            e.get("type") == "attack_roll" and e.get("hit", False)
            for e in result.events
        )
        if hit:
            return seed
    return 42  # Last resort


def run_scenario():
    """Run the 5-turn micro-scenario."""

    scenes, ws_template = build_dungeon()

    # Find a seed that gives a satisfying first hit
    seed = find_working_seed(
        scenes,
        lambda: WorldState(
            ruleset_version=ws_template.ruleset_version,
            entities=dict(ws_template.entities),
        ),
    )

    # Build the real orchestrator with the chosen seed
    world_state = WorldState(
        ruleset_version=ws_template.ruleset_version,
        entities=dict(ws_template.entities),
    )

    orch = SessionOrchestrator(
        world_state=world_state,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes=scenes),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=seed,
    )

    banner("MICRO-SCENARIO: The Goblin Warren")
    print(f"  {DIM}Seed: {seed} | Deterministic | Template narration{RESET}")
    print(f"  {DIM}3 rooms, 5 turns, 1 fighter vs 1 goblin{RESET}")

    # ── Room A: Load scene ────────────────────────────────────────

    orch.load_scene("room_a")
    scene_banner("The Goblin Ambush", scenes["room_a"].description)
    show_party_status(orch)

    state_hash = orch.world_state.state_hash()
    print(f"\n  {DIM}State: {state_hash[:24]}...{RESET}")

    # ── Turn 1: Attack the goblin ─────────────────────────────────

    print(f"\n{DIVIDER}")
    print(f"  {BOLD}Turn 1{RESET}")
    player_says("attack Goblin Spearman")

    result = orch.process_text_turn("attack Goblin Spearman", "pc_fighter")
    show_events_summary(result.events)

    if result.narration_text:
        dm_says(result.narration_text, result.provenance)

    show_party_status(orch)
    state_hash = orch.world_state.state_hash()
    print(f"\n  {DIM}State: {state_hash[:24]}...{RESET}")

    # ── Turn 2: Attack again (or mop up) ──────────────────────────

    goblin = orch.world_state.entities.get("goblin_1", {})
    goblin_alive = not goblin.get(EF.DEFEATED, True)

    print(f"\n{DIVIDER}")
    print(f"  {BOLD}Turn 2{RESET}")

    if goblin_alive:
        player_says("attack Goblin Spearman")
        result = orch.process_text_turn("attack Goblin Spearman", "pc_fighter")
        show_events_summary(result.events)
        if result.narration_text:
            dm_says(result.narration_text, result.provenance)
    else:
        player_says("move to 5,5")
        result = orch.process_text_turn("move to 5,5", "pc_fighter")
        show_events_summary(result.events)
        if result.narration_text:
            dm_says(result.narration_text, result.provenance)

    show_party_status(orch)
    state_hash = orch.world_state.state_hash()
    print(f"\n  {DIM}State: {state_hash[:24]}...{RESET}")

    # ── Turn 3: Go east → Rest Chamber ────────────────────────────

    print(f"\n{DIVIDER}")
    print(f"  {BOLD}Turn 3{RESET}")
    player_says("go east")

    result = orch.process_text_turn("go east", "pc_fighter")

    if result.success:
        scene_banner("The Rest Chamber", scenes["room_b"].description)
        if result.narration_text:
            dm_says(result.narration_text, result.provenance)
    else:
        print(f"  {RED}Transition failed: {result.error_message}{RESET}")

    show_party_status(orch)
    state_hash = orch.world_state.state_hash()
    print(f"\n  {DIM}State: {state_hash[:24]}...{RESET}")

    # ── Turn 4: Rest ──────────────────────────────────────────────

    print(f"\n{DIVIDER}")
    print(f"  {BOLD}Turn 4{RESET}")
    player_says("rest")

    # Record HP before rest
    fighter_hp_before = orch.world_state.entities["pc_fighter"][EF.HP_CURRENT]
    fighter_hp_max = orch.world_state.entities["pc_fighter"][EF.HP_MAX]

    result = orch.process_text_turn("rest", "pc_fighter")
    show_events_summary(result.events)

    fighter_hp_after = orch.world_state.entities["pc_fighter"][EF.HP_CURRENT]

    if result.narration_text:
        dm_says(result.narration_text, result.provenance)

    if fighter_hp_after > fighter_hp_before:
        healed = fighter_hp_after - fighter_hp_before
        print(f"\n  {GREEN}Kael healed {healed} HP ({fighter_hp_before} -> {fighter_hp_after}){RESET}")
    elif fighter_hp_before == fighter_hp_max:
        print(f"\n  {DIM}Already at full health -- no healing needed.{RESET}")

    show_party_status(orch)
    state_hash = orch.world_state.state_hash()
    print(f"\n  {DIM}State: {state_hash[:24]}...{RESET}")

    # ── Turn 5: Go north → Boss Room ──────────────────────────────

    print(f"\n{DIVIDER}")
    print(f"  {BOLD}Turn 5{RESET}")
    player_says("go north")

    result = orch.process_text_turn("go north", "pc_fighter")

    if result.success:
        scene_banner("The Bone Throne", scenes["room_c"].description)
        if result.narration_text:
            dm_says(result.narration_text, result.provenance)
    else:
        print(f"  {RED}Transition failed: {result.error_message}{RESET}")

    show_party_status(orch)
    state_hash = orch.world_state.state_hash()
    print(f"\n  {DIM}State: {state_hash[:24]}...{RESET}")

    # ── Summary ───────────────────────────────────────────────────

    banner("SCENARIO COMPLETE")

    print(f"\n  {BOLD}Session Summary:{RESET}")
    print(f"    Turns played:    {orch.turn_count}")
    print(f"    Briefs recorded: {len(orch.brief_history)}")
    print(f"    Current scene:   {orch.current_scene_id}")
    print(f"    Session state:   {orch.session_state.value}")
    print(f"    Final hash:      {orch.world_state.state_hash()[:32]}...")

    # Brief history summary
    print(f"\n  {BOLD}Narrative Thread:{RESET}")
    for i, brief in enumerate(orch.brief_history):
        action = brief.action_type
        summary = brief.outcome_summary or "(no summary)"
        # Truncate long summaries
        if len(summary) > 55:
            summary = summary[:52] + "..."
        print(f"    {i + 1}. [{action}] {summary}")

    # Determinism proof
    print(f"\n  {BOLD}Determinism:{RESET}")

    # Replay with same seed
    world_state_2 = WorldState(
        ruleset_version=ws_template.ruleset_version,
        entities=dict(ws_template.entities),
    )
    orch_2 = SessionOrchestrator(
        world_state=world_state_2,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes=scenes),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=seed,
    )
    orch_2.load_scene("room_a")

    # Replay exact same commands
    replay_commands = [
        ("attack Goblin Spearman", "pc_fighter"),
    ]
    # Add turn 2 based on what happened
    if goblin_alive:
        replay_commands.append(("attack Goblin Spearman", "pc_fighter"))
    else:
        replay_commands.append(("move to 5,5", "pc_fighter"))
    replay_commands.extend([
        ("go east", "pc_fighter"),
        ("rest", "pc_fighter"),
        ("go north", "pc_fighter"),
    ])

    for text, actor in replay_commands:
        orch_2.process_text_turn(text, actor)

    hash_1 = orch.world_state.state_hash()
    hash_2 = orch_2.world_state.state_hash()

    if hash_1 == hash_2:
        print(f"    {GREEN}[PASS]{RESET} Same seed + same commands = identical final state")
        print(f"    {DIM}{hash_1[:32]}...{RESET}")
    else:
        print(f"    {RED}[FAIL]{RESET} Replay diverged!")
        print(f"    {DIM}Run 1: {hash_1[:32]}...{RESET}")
        print(f"    {DIM}Run 2: {hash_2[:32]}...{RESET}")

    print()


# ── Entry point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    run_scenario()
