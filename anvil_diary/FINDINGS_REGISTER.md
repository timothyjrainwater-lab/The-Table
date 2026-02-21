# Findings Register

One line per finding. Append-only. Newest first.

| ID | Severity | Status | Source | Description | Evidence |
|----|----------|--------|--------|-------------|----------|
| FINDING-WAYPOINT-03 | LOW | RESOLVED | WO-WAYPOINT-001 | Event payload uses `d20_result` not `d20_roll` — doc note added | `pm_inbox/reviewed/archive_spark_explore/` |
| FINDING-WAYPOINT-02 | MEDIUM | RESOLVED | WO-WAYPOINT-001 | `weapon_name="unknown"` in attack_resolver disables Weapon Focus matching — plumbed in WP3 | `tests/test_waypoint_003.py` |
| FINDING-WAYPOINT-01 | HIGH | RESOLVED | WO-WAYPOINT-001 | `play_loop` does not enforce `actions_prohibited` on actor conditions — fixed in WP2 | `tests/test_waypoint_002.py` |
| FINDING-HOOLIGAN-03 | MEDIUM | OPEN | WO-SPARK-EXPLORE-001 | RV-001 false positive on compound actions (actor attribution). Needs contract decision: one-action-per-output vs per-sentence attribution | `pm_inbox/reviewed/archive_spark_explore/DEBRIEF_HOOLIGAN_RUN_001.md` |
| FINDING-HOOLIGAN-02 | HIGH | IN-PROGRESS | WO-SPARK-EXPLORE-001 | RV-007 (forbidden meta-game claims) NOT IMPLEMENTED — validator blind to damage numbers, HP, dice rolls. WO-SPARK-RV007-001 dispatched | `pm_inbox/WO-SPARK-RV007-001_DISPATCH.md` |
| FINDING-HOOLIGAN-01 | LOW | IN-PROGRESS | WO-SPARK-EXPLORE-001 | Condition keyword underscore normalization in RV-004 — `mummy_rot` doesn't match "mummy rot". Fix scoped in WO-SPARK-RV007-001 | `pm_inbox/WO-SPARK-RV007-001_DISPATCH.md` |
| FINDING-EXPLORE-03 | LOW | FIXED | WO-SPARK-EXPLORE-001 | Device reports "cpu" when on GPU — fixed via `n_gpu_layers != 0` check | `pm_inbox/reviewed/archive_spark_explore/DEBRIEF_WO-SPARK-EXPLORE-001.md` |
| FINDING-EXPLORE-02 | LOW | FIXED | WO-SPARK-EXPLORE-001 | VRAM reports 0 via torch — fixed via pynvml | `pm_inbox/reviewed/archive_spark_explore/DEBRIEF_WO-SPARK-EXPLORE-001.md` |
| FINDING-EXPLORE-01 | MEDIUM | FIXED | WO-SPARK-EXPLORE-001 | Multi-draft output from `===` separator — fixed via stop sequence | `pm_inbox/reviewed/archive_spark_explore/DEBRIEF_WO-SPARK-EXPLORE-001.md` |
