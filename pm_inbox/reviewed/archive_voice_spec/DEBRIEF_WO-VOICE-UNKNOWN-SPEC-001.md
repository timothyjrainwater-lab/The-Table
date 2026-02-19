# DEBRIEF: WO-VOICE-UNKNOWN-SPEC-001

**Builder:** Anvil
**Date:** 2026-02-19
**Commit:** (pending — all deliverables ready for commit)

---

## 0. Scope Accuracy

Delivered all three artifacts as specified:

- `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` — Full contract with all 5 required sections: failure class registry (7 classes, 32 sub-classes), STOPLIGHT rules (classification truth table, promotion/demotion rules, authority boundary), clarification budget (parameters, escalation ladder, cancel semantics), cross-cutting rules (no silent commit, no probabilistic resolution, provenance tags, replay compatibility, TTS interruptibility), and authority boundary statement. All 3 verbatim invariants included.
- `tests/test_unknown_gate_k.py` — 67 test methods across 10 test classes (K-01 through K-10). Covers all 36 signal/behavior pairs from the research (T-ASR-01 through T-BUDGET-06). All fixture-based using a frozen `VoiceEvent` dataclass. Follows Gate J naming convention.
- `scripts/check_unknown_handling.py` — JSONL event validator with `check_unknown_policy(events: list[dict]) -> list[Violation]` API. 8 policy checks covering STOPLIGHT classification, confidence thresholds, no silent commit, RED terminal, provenance tags, forbidden resolution methods, clarification budget, and stale transcripts.

One deviation: the dispatch referenced 35 signal/behavior pairs (T-ASR-01 through T-BUDGET-02). The research artifact actually contains 36 (Section 5.8 has T-BUDGET-01 through T-BUDGET-06, not just T-BUDGET-02). All 36 are tested.

No changes to play.py, Box, Oracle, Lens, Spark, or doctrine files. Zero regressions: 5997 tests pass (5930 existing + 67 new Gate K), same 7 pre-existing failures.

---

## 1. Discovery Log

- **Research artifact is richer than the dispatch described.** The dispatch mentioned 35 T-* signals but the research contains 36 (6 budget signals, not 2). The extra signals (T-BUDGET-03 through T-BUDGET-06) cover explicit cancel, wait/pause, menu timeout, and menu selection — all important for the clarification ladder.
- **FC-BLEED classification is inherently context-dependent.** The T-BLEED signals require a classifier that understands conditional/past-tense/hypothetical language. The gate tests validate the policy (what the correct classification should be), but the actual NLP detection is deferred to Tier 3. The fixture schema uses a pre-set `table_talk_weight` field rather than deriving it.
- **No existing voice input classifier in the codebase.** Confirmed via grep — no STOPLIGHT, VoiceClassifier, or FailureClass types exist in aidm/ or scripts/. This contract is building on clean ground.

---

## 2. Methodology Challenge

Designing the `VoiceEvent` fixture schema was the hardest part. The 36 T-* signals test different axes (confidence, parse count, timing, game state, table-talk signals) and the dataclass needed to capture all of them without becoming a kitchen-sink. Solved by using frozen defaults for all fields — most tests only override 2-3 fields from the default "clean GREEN input" baseline. This makes each fixture self-documenting: the fields that differ from defaults are the exact conditions being tested.

The STOPLIGHT classifier function itself required careful ordering of RED/YELLOW/GREEN checks to implement the fail-closed bias correctly (RED checked first, then YELLOW, GREEN only if all filters pass). Edge case: FC-TIMING-02 (TTS interrupt) is GREEN despite TTS being active, because TTS interruptibility is a hard requirement — the classifier correctly short-circuits the TTS check.

---

## 3. Field Manual Entry

The `VoiceEvent` dataclass is designed to be extensible by Tier 3 without breaking Gate K. All fields have defaults, so adding new fields for live voice processing (e.g., `waveform_data`, `speaker_embedding`) will not break existing fixtures. Tier 3 builder: import `VoiceEvent` from the gate test file or factor it into a shared schema module — don't reinvent the fixture format.

---

## 4. Builder Radar

- **Trap.** The STOPLIGHT classifier in the gate tests is a policy-level implementation, not a production classifier. It uses pre-labeled `failure_class` and `table_talk_weight` fields set by fixtures. The Tier 3 VoiceIntentParser must implement the actual detection heuristics (conditional language detection, past-tense detection, etc.) and set these fields from raw transcripts. If Tier 3 copies the gate test classifier verbatim, it will only work with pre-labeled data.
- **Drift.** T-BLEED-01 is specified as "YELLOW or RED" in the research (ambiguous). The gate test pins it to YELLOW (clarify intent), which is the less restrictive interpretation. If PM decides BLEED-01 should be RED, the fixture and one assertion need updating.
- **Near stop.** FC-AMBIG-06 (numeric ambiguity, e.g., "cast it at third level") has no T-* signal in the research Section 5. It's defined in the taxonomy (Section 1.5) but not in the operator checklist. The contract documents it as a sub-class, but there's no dedicated gate test for it. Did not halt because the dispatch says to test the T-* signals, not to invent new ones.
---

## Debrief Focus Answers

1. **Fixture schema:** The `VoiceEvent` frozen dataclass has 18 fields with sensible defaults. It's designed for extension — Tier 3 can add fields without breaking existing tests. The schema captures: ASR output (transcript, confidence, delay), game state snapshot (active player, phase, targets, equipment), parsed intent metadata (parse count, fields populated), and table-talk signals. For Tier 3, the schema will likely need wrapping in a richer event stream model, but the fixture format should remain valid for policy-level testing.

2. **Spec divergence:** Two T-* signals diverged slightly. T-BLEED-01 is documented as "YELLOW or RED" — pinned to YELLOW. T-PART-05 (pronoun resolved via STM) is GREEN in the research but required adding a note that `[CONSTRAINED]` provenance is needed. All other 34 signals transferred verbatim without modification.
