# DEBRIEF: WO-VOICE-TYPED-CALL-SPEC-001 — Typed Call Contract

**Builder:** Claude Opus 4.6
**Date:** 2026-02-21
**Status:** COMPLETE — all gates pass, zero regressions

---

## 0. Scope Accuracy

Delivered exactly what was asked. ONE contract document (`docs/contracts/TYPED_CALL_CONTRACT.md`) defining all six CallTypes with input schemas, output schemas, forbidden claims, fallback templates, latency ceilings, and line type mappings. Validation pipeline specified (3 stages, Stage 3 reserved). Four invariants (TC-INV-01 through TC-INV-04) defined and testable. Gate tests (`tests/test_typed_call_gate_l.py`) with 32 tests across 10 gate categories (L-01 through L-10). Validator script (`scripts/check_typed_call.py`) reads the contract and checks structural completeness (11 checks). No engine code changes. No modifications to Tier 1.1 or Tier 1.2 contracts. No deviations from the dispatch.

## 1. Discovery Log

Research confirmed exactly six CallTypes across all sources (`RQ_LLM_TYPED_CALL_CONTRACT.md` Section 2, `RQ-SPRINT-004` Section 1.5, Playbook Section 4.3). No seventh type was found. The research also confirmed four authority levels (ATMOSPHERIC, UNCERTAIN, INFORMATIONAL, NON-AUTHORITATIVE) with unambiguous provenance tag assignments. One pattern gap discovered: "natural 20" (a common D&D mechanical assertion) was not caught by the existing 8 mechanical patterns from GrammarShield. Added MV-09 (`\bnatural\s+\d+\b`) to the forbidden claims pattern set — this is additive and does not modify GrammarShield itself (spec-only). The forbidden claims parameterization approach (three categories: `mechanical_values`, `rule_citations`, `outcome_assertions`) directly follows TD-01's resolution for game-system-independent patterns with D&D examples.

## 2. Methodology Challenge

The hardest part was the line type mapping. Each CallType's output must map to existing Tier 1.1 line types (frozen taxonomy — no new types allowed). SUMMARY output initially seemed like it should be NARRATION or RESULT, but summaries are stored in memory and never spoken — making SYSTEM the correct mapping. OPERATOR_DIRECTIVE and CLARIFICATION_QUESTION both produce clarification prompts, making PROMPT the correct mapping, which also naturally connects them to the Tier 1.2 escalation flow. The constraint that no CallType may produce TURN or ALERT (Box-originated types) was an implicit invariant I made explicit in L-03's second test.

## 3. Field Manual Entry

**When defining forbidden claim patterns, test them bidirectionally.** The L-06 gate tests both positive strings (must be caught) and negative strings (must not be caught). The "natural 20" gap was found because the positive test list included a string the patterns didn't cover. Every new mechanical assertion pattern should be tested against at least 5 clean narration strings to prevent false positives — a pattern that fires on "The goblin naturally recoils" would break atmospheric narration.

## 4. Builder Radar

- **Trap.** The OPERATOR_DIRECTIVE and CLARIFICATION_QUESTION CallTypes share the UNCERTAIN authority level and both map to PROMPT line type. A future wiring WO might conflate them. They are distinct: OPERATOR_DIRECTIVE interprets intent into candidates (structured JSON), CLARIFICATION_QUESTION asks for missing info (natural language). The `needs_clarification` handoff between them is a state machine transition, not a type equivalence.
- **Drift.** The forbidden claims pattern set (MV-01 through MV-09, RC-01 through RC-04) lives in the contract document AND is duplicated as compiled regex in the gate tests. If a future WO adds patterns to one but not the other, they drift. The validator script (`check_typed_call.py`) only checks the contract document's text, not the test file's regex list.
- **Near stop.** A5 validation (fallback templates in Playbook Section 4.3) nearly triggered a stop — the Playbook lists fallbacks as a table but does not provide the actual template strings. The contract fills this gap by defining concrete fallback strings per CallType, which is within scope ("fill the gap in the contract").
