#!/usr/bin/env python3
"""Vertical Slice V1 — Runnable Demonstration Script

Demonstrates minimal deterministic play loop execution:
- 1 scene (forest clearing)
- 1 monster with doctrine (goblin)
- 2 PCs (fighter, wizard)
- 3 turns total
- Deterministic replay verification
- Event log + transcript generation

NO MECHANICS: No damage, no movement, no time advancement.
This is an execution proof, not a gameplay implementation.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aidm.core.play_loop import execute_scenario, TurnContext
from aidm.core.state import WorldState
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.core.doctrine_rules import derive_tactical_envelope
from aidm.core.event_log import EventLog
from aidm.schemas.bundles import SessionBundle, SceneCard, EncounterSpec
from aidm.core.bundle_validator import validate_session_bundle


def main():
    """Execute vertical slice V1 and generate artifacts."""
    print("=" * 70)
    print("VERTICAL SLICE V1 — Deterministic Play Loop Execution Proof")
    print("=" * 70)
    print()

    # ========================================================================
    # PHASE 1: Bundle Setup & Validation
    # ========================================================================
    print("[PHASE 1] Creating and validating SessionBundle...")

    # Create goblin doctrine
    goblin_doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        citations=[{"source_id": "e390dfd9143f", "page": 133}]
    )
    goblin_doctrine = derive_tactical_envelope(goblin_doctrine)
    print(f"  Goblin doctrine created (INT 10, WIS 11)")
    print(f"  Allowed tactics: {', '.join(goblin_doctrine.allowed_tactics)}")

    # Create scene card
    scene = SceneCard(
        scene_id="forest_clearing",
        title="Forest Clearing",
        description="A small clearing in the forest with a single goblin ambush"
    )

    # Create encounter spec
    encounter = EncounterSpec(
        encounter_id="goblin_ambush",
        name="Goblin Ambush",
        creatures=[{"type": "goblin", "count": 1}],
        monster_doctrines_by_id={"goblin": goblin_doctrine}
    )

    # Create session bundle
    bundle = SessionBundle(
        id="vertical_slice_v1",
        campaign_id="test_campaign",
        session_number=1,
        created_at="2025-02-08T00:00:00Z",
        scene_cards=[scene],
        encounter_specs=[encounter]
    )

    # Validate bundle
    cert = validate_session_bundle(bundle)
    print(f"  Bundle validation: {cert.status}")
    if cert.status != "ready":
        print(f"  [FAIL] Validation failed: {cert.notes}")
        return 1

    print("  [OK] Bundle validated successfully")
    print()

    # ========================================================================
    # PHASE 2: Initialize World State
    # ========================================================================
    print("[PHASE 2] Initializing world state...")

    initial_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            },
            "pc_fighter": {
                "hp_current": 10,
                "hp_max": 10,
                "conditions": [],
                "position": {"x": 10, "y": 0},
                "team": "party"
            },
            "pc_wizard": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 15, "y": 5},
                "team": "party"
            }
        },
        active_combat={"turn_counter": 0}
    )
    print(f"  Entities: goblin_1, pc_fighter, pc_wizard")
    print(f"  Initial state hash: {initial_state.state_hash()[:16]}...")
    print()

    # ========================================================================
    # PHASE 3: Execute 3 Turns
    # ========================================================================
    print("[PHASE 3] Executing 3-turn scenario...")

    turn_sequence = [
        TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters"),
        TurnContext(turn_index=1, actor_id="pc_fighter", actor_team="party"),
        TurnContext(turn_index=2, actor_id="goblin_1", actor_team="monsters")
    ]

    final_state, event_log = execute_scenario(
        initial_state=initial_state,
        turn_sequence=turn_sequence,
        doctrines={"goblin_1": goblin_doctrine},
        initial_event_id=0,
        initial_timestamp=0.0
    )

    print(f"  Events emitted: {len(event_log.events)}")
    print(f"  Final turn counter: {final_state.active_combat['turn_counter']}")
    print(f"  Final state hash: {final_state.state_hash()[:16]}...")
    print()

    # ========================================================================
    # PHASE 4: Generate Artifacts
    # ========================================================================
    print("[PHASE 4] Generating artifacts...")

    # Create artifacts directory
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    # Write event log JSONL
    jsonl_path = artifacts_dir / "vertical_slice_v1.jsonl"
    event_log.to_jsonl(str(jsonl_path))
    print(f"  [OK] Event log: {jsonl_path}")

    # Generate transcript
    transcript = generate_transcript(event_log, initial_state, final_state)
    transcript_path = artifacts_dir / "vertical_slice_v1_transcript.txt"
    transcript_path.write_text(transcript, encoding="utf-8")
    print(f"  [OK] Transcript: {transcript_path}")
    print()

    # ========================================================================
    # PHASE 5: Replay Verification
    # ========================================================================
    print("[PHASE 5] Verifying deterministic replay...")

    # Reload event log from JSONL
    event_log_reloaded = EventLog()
    for event_dict in EventLog.from_jsonl(str(jsonl_path)):
        event_log_reloaded.append(event_dict)

    # Re-execute from initial state
    final_state_replay, _ = execute_scenario(
        initial_state=initial_state,
        turn_sequence=turn_sequence,
        doctrines={"goblin_1": goblin_doctrine},
        initial_event_id=0,
        initial_timestamp=0.0
    )

    # Compare hashes
    original_hash = final_state.state_hash()
    replay_hash = final_state_replay.state_hash()

    print(f"  Original hash:  {original_hash[:16]}...")
    print(f"  Replay hash:    {replay_hash[:16]}...")

    if original_hash == replay_hash:
        print("  [OK] Replay verification PASSED (hashes match)")
    else:
        print("  [FAIL] Replay verification FAILED (hashes differ)")
        return 1

    print()
    print("=" * 70)
    print("VERTICAL SLICE V1 COMPLETE")
    print("=" * 70)
    print(f"\nArtifacts generated:")
    print(f"  - {jsonl_path}")
    print(f"  - {transcript_path}")
    print(f"\nFinal state hash: {original_hash}")
    print()

    return 0


def generate_transcript(event_log: EventLog, initial_state: WorldState, final_state: WorldState) -> str:
    """Generate human-readable transcript from event log."""
    lines = []
    lines.append("=" * 70)
    lines.append("VERTICAL SLICE V1 TRANSCRIPT")
    lines.append("=" * 70)
    lines.append("")
    lines.append("SCENARIO: Forest Clearing — Goblin Ambush")
    lines.append("ENTITIES: goblin_1 (monster), pc_fighter (party), pc_wizard (party)")
    lines.append(f"INITIAL STATE HASH: {initial_state.state_hash()[:16]}...")
    lines.append("")
    lines.append("-" * 70)
    lines.append("")

    # Group events by turn
    current_turn = None
    turn_events = []

    for event in event_log.events:
        if event.event_type == "turn_start":
            if current_turn is not None:
                # Emit previous turn
                lines.extend(format_turn(current_turn, turn_events))
                lines.append("")
            current_turn = event.payload
            turn_events = []
        else:
            turn_events.append(event)

    # Emit final turn
    if current_turn is not None:
        lines.extend(format_turn(current_turn, turn_events))

    lines.append("")
    lines.append("-" * 70)
    lines.append("")
    lines.append(f"FINAL STATE HASH: {final_state.state_hash()[:16]}...")
    lines.append(f"FINAL TURN COUNTER: {final_state.active_combat['turn_counter']}")
    lines.append("")
    lines.append("=" * 70)
    lines.append("END TRANSCRIPT")
    lines.append("=" * 70)

    return "\n".join(lines)


def format_turn(turn_start_payload: dict, turn_events: list) -> list:
    """Format a single turn for transcript."""
    lines = []
    turn_idx = turn_start_payload["turn_index"]
    actor_id = turn_start_payload["actor_id"]
    actor_team = turn_start_payload["actor_team"]

    lines.append(f"TURN {turn_idx + 1}: {actor_id} ({actor_team})")

    # Find key events
    tactic_events = [e for e in turn_events if e.event_type == "tactic_selected"]
    action_events = [e for e in turn_events if e.event_type == "action_declared"]
    policy_fail_events = [e for e in turn_events if e.event_type == "policy_evaluation_failed"]

    if tactic_events:
        tactic = tactic_events[0]
        lines.append(f"  Policy Evaluation:")
        lines.append(f"    Selected: {tactic.payload['tactic_class']}")
        lines.append(f"    Score: {tactic.payload['score']}")
        lines.append(f"    Rationale: {', '.join(tactic.payload['reasons'][:2])}")  # First 2 reasons
        if tactic.citations:
            cit = tactic.citations[0]
            lines.append(f"    Citation: {cit.get('source_id', 'unknown')[:8]}... p.{cit.get('page', '?')}")

    if action_events:
        action = action_events[0]
        lines.append(f"  Action: {action.payload['action_type']}")
        lines.append(f"    Note: {action.payload.get('note', 'N/A')}")
        if action.citations:
            cit = action.citations[0]
            lines.append(f"    Citation: {cit.get('source_id', 'unknown')[:8]}... p.{cit.get('page', '?')}")

    if policy_fail_events:
        fail = policy_fail_events[0]
        lines.append(f"  Policy Evaluation FAILED: {fail.payload['status']}")
        if fail.payload.get('missing_fields'):
            lines.append(f"    Missing: {fail.payload['missing_fields']}")

    # Event ID range
    event_ids = [e.event_id for e in turn_events if e.event_type != "turn_start"]
    if event_ids:
        lines.append(f"  Events: {min(event_ids)}-{max(event_ids)}")

    return lines


if __name__ == "__main__":
    sys.exit(main())
