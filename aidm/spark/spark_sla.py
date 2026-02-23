"""Spark per-call latency SLA table, template narration strings, and turn budget.

Source: Thunder binary decision 2026-02-23 (WO-BURST-002-RESEARCH-001).

These constants define:
- SPARK_SLA_PER_CALL: per-call timeout_s (hard enforcement) and p95_target_s (soft target)
- TEMPLATE_NARRATION: deterministic fallback strings for each CallType
- TURN_WALL_CLOCK_BUDGET_S: secondary (recorded, not enforced) turn wall-clock budget
"""

# Per-call latency targets (wall-clock seconds, p95 enforcement).
# Keys match SparkCallType values from WO-RQ-LLM-CALL-TYPING-01.
SPARK_SLA_PER_CALL: dict = {
    "COMBAT_NARRATION":       {"timeout_s": 8.0,  "p95_target_s": 5.0},
    "OPERATOR_DIRECTIVE":     {"timeout_s": 5.0,  "p95_target_s": 3.0},
    "SUMMARY":                {"timeout_s": 12.0, "p95_target_s": 8.0},
    "RULE_EXPLAINER":         {"timeout_s": 8.0,  "p95_target_s": 5.0},
    "CLARIFICATION_QUESTION": {"timeout_s": 4.0,  "p95_target_s": 2.5},
    "NPC_DIALOGUE":           {"timeout_s": 8.0,  "p95_target_s": 5.0},
}

# Deterministic fallback narration strings.
# Used when a Spark call fails at runtime and template substitution is triggered.
# Must be non-empty for all 6 CallTypes.
TEMPLATE_NARRATION: dict = {
    "COMBAT_NARRATION":       "The action resolves.",
    "OPERATOR_DIRECTIVE":     "Understood.",
    "SUMMARY":                "Events recorded.",
    "RULE_EXPLAINER":         "See rulebook for details.",
    "CLARIFICATION_QUESTION": "Please clarify your intent.",
    "NPC_DIALOGUE":           "...",
}

# Turn wall-clock budget in seconds — secondary metric.
# Recorded for observability; NOT enforced (Thunder 2026-02-23 decision #3).
TURN_WALL_CLOCK_BUDGET_S: float = 15.0
