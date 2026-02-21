# DEBRIEF: WO-VOICE-PRESSURE-SPEC-001 — Boundary Pressure Contract

**Builder:** Claude Opus 4.6
**Date:** 2026-02-21
**Status:** COMPLETE — all gates pass, zero regressions

---

## 0. Scope Accuracy

Delivered exactly what was asked. ONE contract document (`docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md`) defining four pressure triggers, three PressureLevels, response policies per level, content-agnostic detection method (pseudocode), observability spec (9-field event payload), and integration with Tiers 1.1-1.3. Five invariants (BP-INV-01 through BP-INV-05). Six composite classification rules (R-01 through R-06). Gate tests (`tests/test_boundary_pressure_gate_m.py`) with 31 tests across 12 gate categories (M-01 through M-12). Validator (`scripts/check_boundary_pressure.py`) with 11 structural checks. No engine code changes. No modifications to Tiers 1.1, 1.2, or 1.3. No deviations from the dispatch.

## 1. Discovery Log

**Trigger completeness:** Research confirmed exactly four triggers. `RQ_SPARK_BOUNDARY_PRESSURE.md` Section 3 defines: MISSING_FACT, AUTHORITY, CONTEXT_OVERLOAD, AMBIGUITY. `RQ-SPRINT-004` Section 1.6 confirms the same four (all content-agnostic). No fifth trigger was found. The dispatch used slightly different naming (BP-AMBIGUOUS-INTENT vs. AMBIGUITY, BP-AUTHORITY-PROXIMITY vs. AUTHORITY, BP-CONTEXT-OVERFLOW vs. CONTEXT_OVERLOAD). The contract reconciles to the dispatch's naming convention.

**Boundary between BP-AMBIGUOUS-INTENT and BP-AUTHORITY-PROXIMITY:** Ambiguity is an *input* problem (what does the player want?). Authority proximity is an *output* risk (what will Spark invent?). They can co-fire — "I cast something at someone" has both ambiguous intent AND missing mechanical resolution. This is the 2-YELLOW case (stays YELLOW); if a third trigger fires simultaneously, it escalates to RED per PD-04.

**Escalation threshold:** The research (`RQ_SPARK_BOUNDARY_PRESSURE.md` Section 5.3) suggests "3+ consecutive YELLOWs = systemic issue" as a Phase 2 *trending* mechanism, which is different from the dispatch's "3+ simultaneous YELLOWs = RED" *escalation* rule. These are complementary, not contradictory. The contract implements the dispatch's simultaneous escalation; trending is future work.

## 2. Methodology Challenge

BP-MISSING-FACT has no YELLOW level — required data is binary (present or absent). This created an asymmetry: three of four triggers have GREEN/YELLOW/RED, but BP-MISSING-FACT only has GREEN/RED. The composite classification had to handle this: BP-MISSING-FACT at RED absorbs everything (R-01), so the YELLOW escalation path (R-02 through R-04) only applies to the other three triggers. This means the maximum simultaneous YELLOW count is 3 (BP-AMBIGUOUS-INTENT + BP-AUTHORITY-PROXIMITY + BP-CONTEXT-OVERFLOW), which exactly matches the PD-04 threshold. If BP-MISSING-FACT also had YELLOW, 4 simultaneous YELLOWs would be possible, and the threshold would need revisiting.

## 3. Field Manual Entry

**When writing content-agnostic detection rules, enumerate what you cannot use.** The contract explicitly lists seven forbidden detection techniques (vocabulary scanning, regex, keywords, game-system rules, NLU, embedding similarity, ML). This negative definition is more useful than the positive definition ("structural field inspection") because it gives the next builder a concrete checklist. If a future trigger tempts you to scan for keywords, the forbidden list catches it before it ships.

## 4. Builder Radar

- **Trap.** The `"pending"` sentinel value in BP-AUTHORITY-PROXIMITY detection looks like vocabulary scanning. It's not — it's a sentinel set by Box's resolution pipeline, not a game-system word. But a future builder who sees `"pending" in outcome_summary` might add more string checks, sliding toward vocabulary scanning. The contract's BP-INV-03 forbids this, but the enforcement is cultural, not mechanical.
- **Drift.** BP-MISSING-FACT's required field list (Section 1.1 table) is a copy of Tier 1.3's per-CallType input schema required fields. If Tier 1.3 adds or removes a required field, the BP-MISSING-FACT table must be updated. No cross-reference mechanism enforces this.
- **Near stop.** The research document defines a `confidence` field (0.0-1.0) on the BoundaryPressure schema that allows detectors to express certainty. The dispatch doesn't mention confidence. Including it would have added complexity (thresholds per trigger per confidence band). Omitting it keeps the contract simpler but means all detections are binary within their level. This is a design tradeoff, not a stop condition.
