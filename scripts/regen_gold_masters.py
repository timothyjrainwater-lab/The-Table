"""Regenerate all four gold master fixtures against current engine state.

WO-ENGINE-GOLD-MASTER-REGEN

The fixtures in tests/fixtures/gold_masters/ were recorded before WO-ENGINE-DR-001
and WO-ENGINE-DEATH-DYING-001 landed. Those WOs added new event fields and event
types that cause drift against the old fixtures. This script re-records all four
fixtures using the same scenario configs and seeds embedded in the existing files.
"""

import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from aidm.testing.replay_regression import ReplayRegressionHarness
from aidm.schemas.testing import ScenarioConfig

OUT_DIR = Path("tests/fixtures/gold_masters")

SCENARIOS = [
    ("tavern_100turn.jsonl",  42),
    ("dungeon_100turn.jsonl", 123),
    ("field_100turn.jsonl",   456),
    ("boss_100turn.jsonl",    789),
]


def main() -> None:
    harness = ReplayRegressionHarness()

    for filename, expected_seed in SCENARIOS:
        fixture_path = OUT_DIR / filename
        print("\n--- %s ---" % filename)

        # Load existing fixture to extract embedded scenario_config and seed
        gm = harness.load_gold_master(fixture_path)
        print("  Loaded: scenario=%r, seed=%d, turns=%d" % (gm.scenario_name, gm.seed, gm.turn_count))

        if gm.scenario_config is None:
            print("  ERROR: no scenario_config embedded in %s" % filename)
            sys.exit(1)

        scenario = ScenarioConfig.from_dict(gm.scenario_config)

        # Re-record with same config, seed, and turn count
        new_gm = harness.record_gold_master(
            scenario=scenario,
            turns=gm.turn_count,
            seed=gm.seed,
        )
        print("  Re-recorded: %d events, hash=%s..." % (len(new_gm.events), new_gm.final_state_hash[:12]))

        harness.serialize_gold_master(new_gm, fixture_path)
        print("  Saved -> %s" % fixture_path)

    print("\nAll four fixtures regenerated successfully.")


if __name__ == "__main__":
    main()
