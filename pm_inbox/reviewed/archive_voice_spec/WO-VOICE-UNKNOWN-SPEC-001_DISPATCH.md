# WO-VOICE-UNKNOWN-SPEC-001: Unknown Handling Policy Freeze

**Classification:** CODE (spec freeze + gate tests)
**Priority:** Tier 1 — critical path for BURST-001 voice reliability
**Dispatched by:** Slate (PM)
**Date:** 2026-02-19

---

## Objective

Extract the 7 failure classes (FC-ASR through FC-BLEED), the STOPLIGHT bias system, and the clarification budget policy from research into a **binding contract document** and **enforceable gate tests**. This is a spec freeze — the research defined the behaviors, this WO pins them as testable invariants.

**Why this matters:** The Unknown Handling Policy is the companion to the CLI Grammar Contract (Tier 1.1). Grammar defines what valid output looks like; this contract defines what happens when input is invalid, ambiguous, or unrecognizable. Every downstream WO that touches voice input routing (Tiers 2-5) depends on these rules being frozen.

---

## Scope

### IN SCOPE

1. **Contract document:** `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md`
   - 7 failure classes (FC-ASR, FC-HOMO, FC-PARTIAL, FC-TIMING, FC-AMBIG, FC-OOG, FC-BLEED) with sub-classes, required behaviors, and forbidden behaviors
   - STOPLIGHT bias system (GREEN/YELLOW/RED definitions, classification rules, promotion/demotion rules)
   - Clarification budget policy (MAX_CLARIFICATIONS=2, escalation ladder, cancel semantics)
   - Cross-cutting rules (no silent commit, no probabilistic resolution, provenance tagging, replay compatibility, TTS interruptibility)
   - Authority boundary statement (STOPLIGHT operates in Lens layer, not Box)

2. **Gate tests:** New test file `tests/test_unknown_gate_k.py`
   - K-01: FC-ASR — ASR failure handling (empty string, low confidence, truncated, noise, stale)
   - K-02: FC-HOMO — Homophone disambiguation (single match proceed, multi-match clarify)
   - K-03: FC-PARTIAL — Partial input handling (missing target/method/action/pronoun, single-weapon inference rule)
   - K-04: FC-TIMING — Timing failure handling (out-of-turn buffer, TTS interruption, double-fire reject, stale discard)
   - K-05: FC-AMBIG — Semantic ambiguity (entity/spell/weapon/action/spatial, constraint filtering order)
   - K-06: FC-OOG — Out-of-grammar routing (nonsense reject, system command route, rules question route, narrative acknowledge, exclamation ignore)
   - K-07: FC-BLEED — Cross-mode bleed detection (conditional/past-tense/hypothetical/side-conversation)
   - K-08: STOPLIGHT — Classification rules (GREEN/YELLOW/RED thresholds, promotion/demotion rules, authority boundary)
   - K-09: Clarification budget — Escalation ladder (2 attempts → menu → timeout cancel), cancel semantics (no partial action, no penalty, state restoration)
   - K-10: Cross-cutting invariants — No silent commit, no probabilistic resolution, provenance tags present, replay determinism

3. **Policy validator script:** `scripts/check_unknown_handling.py`
   - Takes a transcript of voice interaction events (signal/response pairs) and validates against policy rules
   - Checks: STOPLIGHT classification correctness, clarification budget compliance, provenance tag presence, forbidden behavior absence
   - Returns exit code 0 if compliant, 1 if violations found
   - Exposes `check_unknown_policy(events: list[dict]) -> list[Violation]` function for programmatic use

### OUT OF SCOPE

- No changes to `play.py` or any display code (Tier 3)
- No VoiceIntentParser implementation (Tier 3)
- No STT pipeline code (Tier 4)
- No TTS changes (Tier 4)
- No ASR confidence scoring implementation — tests use fixture confidence values
- No Box, Oracle, Lens, or Spark code changes
- No doctrine file modifications

---

## Source Material

The builder should read these sections of the research artifact:

**Primary source:** `docs/research/VOICE_FAILURE_TAXONOMY_AND_UNKNOWN_POLICY.md` (WO-VOICE-RESEARCH-02)
- **Section 1** — Failure Class Taxonomy (FC-ASR through FC-BLEED, all sub-classes)
- **Section 2** — STOPLIGHT Bias Rules (classification, promotion, demotion, authority boundary)
- **Section 3** — Clarification Budget Policy (parameters, escalation ladder, cancel semantics)
- **Section 4** — Cross-Cutting Rules (no silent commit, no probabilistic resolution, provenance, replay, TTS interruptibility)
- **Section 5** — Operator-Facing Checklist (35 signal/behavior pairs: T-ASR-01 through T-BUDGET-02)

**Secondary reference (do NOT read in full):**
- `pm_inbox/reviewed/legacy_pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md` — Section 3 only (failure policy summary)
- `docs/contracts/CLI_GRAMMAR_CONTRACT.md` — Tier 1.1 companion contract (for format conventions and integration seam)

Do NOT read the full playbook or the other 3 research artifacts. The above sections are sufficient.

---

## Contract Document Structure

The contract document (`docs/contracts/UNKNOWN_HANDLING_CONTRACT.md`) must contain:

### Required Sections

1. **Failure Class Registry** — Table of all 7 failure classes with: class ID, name, sub-class count, STOPLIGHT default, spoken/silent response. Each class gets a subsection with sub-class table, required behaviors, and forbidden behaviors (transferred from research verbatim — these are already well-structured).

2. **STOPLIGHT Classification Rules** — Three-tier system:
   - GREEN/YELLOW/RED definitions with default biases
   - Classification truth table (condition → color → action)
   - Promotion rules (YELLOW→GREEN only via confirmation, menu selection, or constraint filtering)
   - Demotion rules (GREEN→YELLOW for impossible actions, GREEN→RED for rule violations)
   - Hard invariant: RED is terminal. No RED→GREEN promotion. Player must re-speak.

3. **Clarification Budget Policy** — Parameters table (MAX_CLARIFICATIONS=2, SILENCE_TIMEOUT=15s, MENU_TIMEOUT=30s), escalation ladder (attempt 0 → attempt 1 → attempt 2 → menu → cancel), clarification question rules (no repetition, increasing specificity, DM voice, no leading questions, no jargon), cancel semantics.

4. **Cross-Cutting Rules** — No silent commit, no probabilistic resolution, provenance tagging schema (6 tags), replay compatibility requirement, TTS interruptibility requirement.

5. **Authority Boundary Statement** — One paragraph: "This contract governs voice input classification, failure handling, and clarification flow. It operates in the Lens layer. It has zero authority over Box mechanical resolution, Oracle state, or game rules. STOPLIGHT classification uses ASR confidence scores and deterministic constraint filters only — never LLM inference or probabilistic NLP."

### Contract Invariants

The contract must include these invariants verbatim:

> **INVARIANT-1:** Every voice input receives exactly one STOPLIGHT classification. No input is unclassified. No input receives two classifications simultaneously.

> **INVARIANT-2:** No mechanical action is committed to game state from voice input unless the intent has reached `confirmed` status via explicit verbal confirmation, soft confirmation (no objection within timeout), or menu selection.

> **INVARIANT-3:** RED classification is terminal. A RED input cannot be promoted to YELLOW or GREEN. The player must re-speak.

---

## Gate Test Specifications

New gate test suite: `tests/test_unknown_gate_k.py`

Register as Gate K following the existing naming convention (see `test_grammar_gate_j.py` for pattern).

**Test structure:** Each test validates policy rules against fixture signal/response pairs. Tests are self-contained (no live combat, no real ASR). Use fixture dictionaries that represent voice interaction events with confidence scores, transcripts, and game state snapshots.

The research artifact Section 5 contains 35 signal/behavior pairs (T-ASR-01 through T-BUDGET-02). These are pre-formatted for test conversion. Each pair specifies a signal condition, expected behavior, and STOPLIGHT classification.

| Test ID | Tests | Source Signals | Method |
|---|---|---|---|
| K-01 | FC-ASR handling | T-ASR-01 through T-ASR-06 | Fixture events with varying confidence, empty transcripts, stale timestamps → verify correct classification + response |
| K-02 | FC-HOMO handling | T-HOMO-01 through T-HOMO-04 | Fixture transcripts with homophone ambiguity against mock game lexicons → verify clarification vs acceptance |
| K-03 | FC-PARTIAL handling | T-PART-01 through T-PART-05 | Fixture transcripts with missing intent fields, mock equipment state → verify query vs single-weapon inference |
| K-04 | FC-TIMING handling | T-TIME-01 through T-TIME-04 | Fixture events with wrong-turn context, concurrent TTS, duplicate inputs → verify buffer/ignore/discard |
| K-05 | FC-AMBIG handling | T-AMBIG-01 through T-AMBIG-05 | Fixture transcripts with multiple valid parses, mock game state for constraint filtering → verify clarify vs constrain-and-proceed |
| K-06 | FC-OOG routing | T-OOG-01 through T-OOG-05 | Fixture transcripts with no lexicon match, system commands, rules questions, narrative, exclamations → verify route vs discard |
| K-07 | FC-BLEED detection | T-BLEED-01 through T-BLEED-04 | Fixture transcripts with conditional/past-tense/hypothetical/side-conversation signals → verify ignore vs clarify |
| K-08 | STOPLIGHT rules | All T-* signals | Verify every signal maps to exactly one STOPLIGHT color; verify promotion rules (only via confirmation/menu/constraint); verify RED is terminal |
| K-09 | Clarification budget | T-BUDGET-01, T-BUDGET-02 | Fixture clarification sequences → verify escalation to menu after 2 attempts, cancel after timeout, no partial action on cancel |
| K-10 | Cross-cutting invariants | Synthetic fixtures | No silent commit (every committed intent has `confirmed` status); provenance tags present on all voice-derived intents; replay determinism (same inputs → same classification) |

**Gate convention:** Follow `test_grammar_gate_j.py` naming and assertion patterns. The 35 T-* signals from the research are your test case source — each one becomes at least one assertion.

---

## Integration Seams

1. **Companion contract:** `docs/contracts/CLI_GRAMMAR_CONTRACT.md` (Tier 1.1) governs output formatting. This contract governs input classification. They are complementary — no overlap, no conflict. The voice routing table in the Grammar Contract defines which output lines are spoken; this contract defines how input is classified before any output is generated.

2. **Gate registration:** New gate K must follow the same registration pattern as Gate J. Verify how Gate J was registered before writing.

3. **Validator script integration:** `scripts/check_unknown_handling.py` should be importable by future WOs. Tier 3 (parser implementation) will call it to validate that the parser's failure handling matches this policy. The script complements `scripts/check_cli_grammar.py` (Tier 1.1).

4. **Provenance tag contract:** The 6 provenance tags defined here (`[VOICE]`, `[INFERRED]`, `[CONSTRAINED]`, `[CLARIFIED]`, `[MENU-SELECTED]`, `[CANCELLED]`) become part of the event schema. Future WOs that implement voice intents must apply these tags.

---

## Assumptions to Validate

1. **Gate registration mechanism** — Confirm how Gate J was registered. Match the pattern for Gate K.

2. **Fixture format** — The research T-* signals use a table format. The builder must design a fixture dictionary schema that can represent: transcript text, ASR confidence, game state snapshot (entities, equipment, spells known), STOPLIGHT classification, expected behavior. This schema becomes part of the contract.

3. **Validator event schema** — The validator script needs an event schema for voice interaction events. The builder should design this as a simple dict/dataclass. This does NOT need to match any existing event schema in `aidm/` — it's a standalone policy validation tool.

4. **STOPLIGHT thresholds are configurable** — The research defines GREEN_THRESHOLD=0.85 and YELLOW_THRESHOLD=0.50 as defaults. The contract should state these as defaults with a note that they are configurable. Gate tests use the defaults.

5. **No existing classifier conflicts** — Confirm no existing voice input classifier exists in the codebase. This contract creates the spec; implementation is Tier 3.

---

## Preflight

Run `python scripts/preflight_canary.py` and log results in `pm_inbox/PREFLIGHT_CANARY_LOG.md` before starting work.

---

## Delivery

### Commit

Single commit with message format: `feat: WO-VOICE-UNKNOWN-SPEC-001 — Unknown Handling Policy freeze + Gate K tests`

All gate tests must pass. Existing 189 gate tests (A-J) must still pass. Full test suite must show zero regressions.

### Completion Report

File as `pm_inbox/DEBRIEF_WO-VOICE-UNKNOWN-SPEC-001.md`. 500 words max. Five mandatory sections:

0. **Scope Accuracy** — Did you deliver what was asked? Note any deviations.
1. **Discovery Log** — Anything you found that the dispatch didn't anticipate.
2. **Methodology Challenge** — Hardest part and how you solved it.
3. **Field Manual Entry** — One tradecraft tip for the next builder working in this area.
4. **Builder Radar** (mandatory, 3 labeled lines):
   - **Trap.** Hidden dependency or trap for the next WO.
   - **Drift.** Current drift risk.
   - **Near stop.** What got close to triggering a stop condition.

### Debrief Focus Questions

1. **Fixture schema:** How did you design the test fixture format for voice interaction events? Is it extensible enough for Tier 3 to reuse, or will it need to be replaced?
2. **Spec divergence:** Did any of the 35 T-* signal/behavior pairs from the research need modification when you formalized them as gate test assertions? What changed and why?

---

## Stop Conditions

- Do NOT modify `play.py` or any display code. This WO creates the spec and tests, not the implementation.
- Do NOT modify Box, Oracle, Lens, or Spark code. This is voice input policy spec only.
- Do NOT read or modify doctrine files.
- Do NOT create gate tests that require live ASR or live combat. Use fixture dictionaries.
- Do NOT implement a VoiceIntentParser or any voice processing pipeline. This WO freezes the policy; implementation is Tier 3.
- If you discover that the research artifact's signal/behavior pairs contain contradictions that make gate tests impossible, document the contradiction and halt. Do not resolve it.
