"""Gate tests for WO-UI-PHASE1-ENEMY-LOOP-001 -- Enemy Turn Loop + Session Isolation.

EL-001  After player attacks, at least one enemy-originated event returned without second player_utterance
EL-002  Initiative order advances: player -> enemy -> player (cursor wraps correctly)
EL-003  All monster actors take turns before control returns to next player actor
EL-004  Enemy attack events (hit or miss) present in response payload
EL-005  Two simultaneous WebSocket connections get independent WorldStates
EL-006  Action in session A does not mutate session B WorldState
EL-007  Enemy turn loop terminates when all enemies are defeated (no infinite loop)
EL-008  Enemy logic delegates to play.run_enemy_turn() -- no reimplementation in orchestrator
"""

from __future__ import annotations

import pytest

from aidm.interaction.intent_bridge import IntentBridge
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.scene_manager import SceneManager
from aidm.narration.guarded_narration_service import GuardedNarrationService
from aidm.runtime.play_controller import build_simple_combat_fixture
from aidm.runtime.session_orchestrator import SessionOrchestrator
from aidm.spark.dm_persona import DMPersona


def _make_orch(seed: int = 42) -> SessionOrchestrator:
    """Helper: build a fresh orchestrator from a fixture."""
    fixture = build_simple_combat_fixture(master_seed=seed)
    return SessionOrchestrator(
        world_state=fixture.world_state,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes={}),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=seed,
    )


def _all_event_types(result) -> list:
    return [(e.get("event_type") or e.get("type", "?")) for e in result.events]


def _actor_ids_in_events(result) -> set:
    ids = set()
    for e in result.events:
        if e.get("actor_id"):
            ids.add(e["actor_id"])
        if e.get("attacker_id"):
            ids.add(e["attacker_id"])
    return ids


# ---------------------------------------------------------------------------
# EL-001 -- Enemy-originated events returned in single process_text_turn call
# ---------------------------------------------------------------------------

def test_EL_001_enemy_events_returned_after_player_attack():
    """After player attacks, at least one non-player event arrives in the same response.

    Seed=4: order=[pc_cleric, goblin_3, pc_fighter, goblin_2, goblin_1, pc_rogue].
    After pc_fighter (idx 2) acts, goblin_2 (idx 3) and goblin_1 (idx 4) follow.
    """
    orch = _make_orch(seed=4)
    init_order = orch._world_state.active_combat["initiative_order"]
    result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")

    assert result.success, f"Expected success; error={result.error_message}; clarify={result.clarification_message}"

    # At least one event that is NOT from pc_fighter (i.e. enemy turn fired)
    enemy_actor_ids = {
        eid for eid, e in orch._world_state.entities.items()
        if e.get("team") == "monsters"
    }
    all_actors = _actor_ids_in_events(result)
    enemy_actors_present = all_actors & enemy_actor_ids

    # Also accept: if all goblins were defeated on the player turn (seed-specific edge case),
    # there are no enemy actors left to act -- allow if combat_ended event present
    event_types = _all_event_types(result)
    combat_ended = "combat_ended" in event_types or "entity_defeated" in event_types

    assert enemy_actors_present or combat_ended, (
        f"Expected at least one enemy actor event OR combat_ended after player turn. "
        f"Event types: {event_types}, actor IDs: {all_actors}"
    )


# ---------------------------------------------------------------------------
# EL-002 -- Initiative cursor advances and wraps correctly
# ---------------------------------------------------------------------------

def test_EL_002_initiative_cursor_advances():
    """_initiative_index advances after process_text_turn."""
    orch = _make_orch(seed=1)
    idx_before = orch._initiative_index
    orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
    idx_after = orch._initiative_index

    n = len(orch._world_state.active_combat["initiative_order"])
    assert 0 <= idx_after < n, f"Index {idx_after} out of range [0, {n})"
    # Must have advanced (not stayed the same as before)
    assert idx_after != idx_before, (
        f"Initiative index did not advance: before={idx_before}, after={idx_after}"
    )


# ---------------------------------------------------------------------------
# EL-003 -- All living monster actors take turns before returning to player
# ---------------------------------------------------------------------------

def test_EL_003_all_monsters_act_before_player():
    """All non-defeated monster actors that follow the player in initiative act.

    Seed=4: order=[pc_cleric, goblin_3, pc_fighter, goblin_2, goblin_1, pc_rogue]
    After pc_fighter acts, goblin_2 and goblin_1 follow before pc_rogue.
    """
    orch = _make_orch(seed=4)
    ws = orch._world_state
    init_order = ws.active_combat["initiative_order"]

    # Find pc_fighter position
    pc_idx = init_order.index("pc_fighter")

    result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
    assert result.success

    # Determine which monsters should have acted (those after pc_fighter until next player)
    n = len(init_order)
    expected_monster_actors = []
    for step in range(1, n):
        eid = init_order[(pc_idx + step) % n]
        e = ws.entities.get(eid, {})
        if e.get("team") != "monsters":
            break  # reached next player -- stop
        if not e.get("defeated", False):
            expected_monster_actors.append(eid)

    if not expected_monster_actors:
        pytest.skip("No monsters immediately follow pc_fighter in this initiative order")

    # All expected monster actors should appear in events
    actors_in_events = _actor_ids_in_events(result)
    for monster_id in expected_monster_actors:
        # Accept that a monster may have been defeated before its turn (cascading kills)
        entity = orch._world_state.entities.get(monster_id, {})
        if entity.get("defeated", False):
            continue  # defeated before its turn is valid
        assert monster_id in actors_in_events, (
            f"Monster {monster_id} should have acted but no event found. "
            f"Actors in events: {actors_in_events}"
        )


# ---------------------------------------------------------------------------
# EL-004 -- Enemy attack events present
# ---------------------------------------------------------------------------

def test_EL_004_enemy_attack_events_present():
    """Enemy turn produces attack_roll events (hit or miss)."""
    # Try multiple seeds to find one where enemy does attack (not just move)
    attack_found = False
    for seed in range(1, 15):
        orch = _make_orch(seed=seed)
        result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
        if result.success:
            event_types = _all_event_types(result)
            # Count attack_roll events -- if > 1, at least one is enemy (player had 1)
            attack_rolls = [t for t in event_types if t == "attack_roll"]
            if len(attack_rolls) > 1:
                attack_found = True
                break

    assert attack_found, (
        "Expected at least one enemy attack_roll event across 15 seeds. "
        "Enemy turns must produce attack events."
    )


# ---------------------------------------------------------------------------
# EL-005 -- Two connections get independent WorldStates
# ---------------------------------------------------------------------------

def test_EL_005_independent_worldstates_per_session():
    """Factory produces separate WorldState per session (not the same object)."""
    from start_server import _make_session_factory

    factory = _make_session_factory()
    orch_a = factory("session-A")
    orch_b = factory("session-B")

    assert orch_a is not orch_b, "Factory must return different orchestrator instances"
    assert orch_a._world_state is not orch_b._world_state, (
        "Factory must return independent WorldState per session"
    )


# ---------------------------------------------------------------------------
# EL-006 -- Action in session A does not mutate session B WorldState
# ---------------------------------------------------------------------------

def test_EL_006_session_a_action_does_not_mutate_session_b():
    """Mutating session A WorldState (via player attack) must not affect session B."""
    from start_server import _make_session_factory

    factory = _make_session_factory()
    orch_a = factory("session-A")
    orch_b = factory("session-B")

    # Snapshot session B goblin_1 HP before session A acts
    hp_b_before = orch_b._world_state.entities.get("goblin_1", {}).get("hp_current", -999)

    # Session A attacks (may mutate goblin_1 HP in session A)
    for seed in range(1, 10):
        orch_a2 = factory("session-A2")  # fresh A with seed variation handled by factory
        result = orch_a2.process_text_turn("attack Goblin Warrior", "pc_fighter")
        event_types = _all_event_types(result)
        if "hp_changed" in event_types:
            break

    # Session B WorldState must be unchanged
    hp_b_after = orch_b._world_state.entities.get("goblin_1", {}).get("hp_current", -999)
    assert hp_b_before == hp_b_after, (
        f"Session B WorldState was mutated by session A action! "
        f"goblin_1 hp: before={hp_b_before}, after={hp_b_after}"
    )


# ---------------------------------------------------------------------------
# EL-007 -- Loop terminates when all enemies defeated
# ---------------------------------------------------------------------------

def test_EL_007_loop_terminates_when_all_enemies_defeated():
    """Enemy turn loop must not run after all enemies are defeated."""
    from aidm.schemas.entity_fields import EF

    # Build a fixture and manually defeat all goblins except one with 1 HP
    # so the player attack kills the last goblin, then loop should not infinite-loop
    fixture = build_simple_combat_fixture(master_seed=3)  # seed 3 hits
    ws = fixture.world_state

    # Defeat goblin_2 and goblin_3 manually
    ws.entities["goblin_2"][EF.DEFEATED] = True
    ws.entities["goblin_3"][EF.DEFEATED] = True
    # Leave goblin_1 at 1 HP so seed=3 attack kills it
    ws.entities["goblin_1"][EF.HP_CURRENT] = 1

    orch = SessionOrchestrator(
        world_state=ws,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes={}),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=3,
    )

    import signal
    import threading

    result_holder = [None]
    error_holder = [None]

    def run():
        try:
            result_holder[0] = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
        except Exception as e:
            error_holder[0] = e

    t = threading.Thread(target=run)
    t.start()
    t.join(timeout=5.0)  # 5 second timeout -- infinite loop would exceed this

    assert not t.is_alive(), "process_text_turn did not return -- possible infinite loop in enemy turn!"
    assert error_holder[0] is None, f"Exception in enemy loop: {error_holder[0]}"
    assert result_holder[0] is not None, "process_text_turn returned None"
    assert result_holder[0].success, f"Expected success after defeating last goblin"


# ---------------------------------------------------------------------------
# EL-008 -- Code inspection: no reimplementation of enemy logic in orchestrator
# ---------------------------------------------------------------------------

def test_EL_008_enemy_logic_delegates_to_play_controller():
    """Orchestrator must delegate to play.run_enemy_turn(); no reimplementation."""
    import inspect
    from aidm.runtime import session_orchestrator as so_module

    src = inspect.getsource(so_module)

    # Must contain explicit call to _play_run_enemy_turn (the imported canonical function)
    assert "_play_run_enemy_turn(" in src, (
        "Orchestrator must call _play_run_enemy_turn() (imported from play.run_enemy_turn). "
        "Enemy logic must NOT be reimplemented in orchestrator."
    )

    # Must NOT contain pick_enemy_target reimplementation
    # (It may reference the name in a comment but must not define or inline it)
    orch_src = inspect.getsource(so_module.SessionOrchestrator._run_enemy_loop)
    assert "pick_enemy_target" not in orch_src, (
        "Orchestrator _run_enemy_loop must not call pick_enemy_target directly. "
        "Target selection is inside play.run_enemy_turn() (canonical)."
    )

    # Must NOT contain AttackIntent construction in _run_enemy_loop
    assert "AttackIntent(" not in orch_src, (
        "Orchestrator _run_enemy_loop must not construct AttackIntent. "
        "Attack resolution is inside play.run_enemy_turn() (canonical)."
    )

    # Must NOT contain execute_turn call in _run_enemy_loop
    assert "execute_turn(" not in orch_src, (
        "Orchestrator _run_enemy_loop must not call execute_turn() directly. "
        "Resolution is inside play.run_enemy_turn() (canonical)."
    )
