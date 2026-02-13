"""Testing utilities for AIDM integration testing.

WO-016: Multi-Encounter Stress Test Suite
WO-018: Replay Regression Suite
"""

from aidm.testing.scenario_runner import ScenarioRunner, ScenarioMetrics
from aidm.testing.replay_regression import (
    GoldMaster,
    DriftReport,
    ReplayResult,
    ReplayRegressionHarness,
    compute_event_log_hash,
    verify_gold_master_integrity,
    create_minimal_gold_master,
)

__all__ = [
    "ScenarioRunner",
    "ScenarioMetrics",
    "GoldMaster",
    "DriftReport",
    "ReplayResult",
    "ReplayRegressionHarness",
    "compute_event_log_hash",
    "verify_gold_master_integrity",
    "create_minimal_gold_master",
]
