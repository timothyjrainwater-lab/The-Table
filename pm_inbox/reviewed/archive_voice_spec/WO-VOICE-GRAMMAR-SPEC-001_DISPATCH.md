# WO-VOICE-GRAMMAR-SPEC-001: CLI Grammar Contract Freeze

**Classification:** CODE (spec freeze + gate tests)
**Priority:** Tier 1 — critical path root for BURST-001 voice reliability
**Dispatched by:** Slate (PM)
**Date:** 2026-02-19

---

## Objective

Extract the 7 CLI grammar rules (G-01 through G-07) and 7 anti-pattern checks from research into a **binding contract document** and **enforceable gate tests**. This is a spec freeze — the research defined the rules, this WO pins them as testable invariants.

**Why this matters:** G-01 through G-07 are the foundation for voice routing (Tier 3), TTS persona selection (Tier 4), and the evaluation harness (Tier 5). Nothing downstream can be built until the grammar is frozen.

---

## Scope

### IN SCOPE

1. **Contract document:** `docs/contracts/CLI_GRAMMAR_CONTRACT.md`
   - 7 grammar rules (G-01 through G-07) with regex patterns and validation criteria
   - 7 anti-pattern checks with grep-testable patterns
   - Line-type taxonomy (TURN, RESULT, ALERT, NARRATION, PROMPT, SYSTEM, DETAIL) with salience levels (S1-S6)
   - Voice routing table (which line types are spoken, by which persona)
   - Boundary invariant: presentation never mutates game state (B-06 from playbook)

2. **Gate tests:** New test file `tests/test_gate_J_grammar_contract.py`
   - J-01: G-01 turn banner regex (`^[A-Z].*'s Turn$`)
   - J-02: G-02 action result (2 sentences max, no mechanical numbers in spoken output)
   - J-03: G-03 alert format (`{name} is {STATUS}.` where STATUS is UPPERCASE)
   - J-04: G-04 narration constraints (1-3 sentences, min 8 words/sentence, max 120 chars/line)
   - J-05: G-05 prompt is exactly `Your action?`
   - J-06: G-06 system prefix `[AIDM]` — never spoken
   - J-07: G-07 detail prefix `[RESOLVE]` — never spoken
   - J-08: Anti-pattern check — forbidden content never appears in spoken output (dashes, abbreviations, ALL CAPS sentences, emoji, numbered lists in narration, parenthetical asides, sentences < 8 words in narration)
   - J-09: Line-type classifier maps every output line to exactly one type
   - J-10: Voice routing table — spoken lines route to correct persona (DM persona for TURN/RESULT/NARRATION, Arbor for ALERT/PROMPT, never spoken for SYSTEM/DETAIL)

3. **Validator script:** `scripts/check_cli_grammar.py`
   - Regex linter that checks CLI output against G-01 through G-07
   - Takes a transcript file (or stdin) and reports violations
   - Returns exit code 0 if compliant, 1 if violations found
   - Usable as CI gate and playtest post-processor

### OUT OF SCOPE

- No changes to `play.py` display output (that's Tier 3: WO-IMPL-TURN-BANNER et al.)
- No TTS pipeline changes (Tier 4)
- No prosodic control (PAS v0.1 — Tier 4)
- No boundary pressure detection (separate Tier 1 WO)
- No unknown handling policy (separate Tier 1 WO)
- No 2PC confirmation protocol code (Tier 3+)

---

## Source Material

The builder should read these sections of the playbook (located at `pm_inbox/reviewed/legacy_pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md`):

- **Section 2** — Grammar Contract Summary (line types, rules G-01..G-07, anti-patterns)
- **Section 1.2** — Authority Boundaries, specifically B-06 (presentation never mutates game state)
- **Section 5.2** — Compliance Checks CC-08 (forbidden phrasing), CC-14 (no AIDM/RESOLVE in spoken output)
- **Section 9** — MVVL definition, items 4-6 (grammar compliance, forbidden content, S5/S6 filtering)

Do NOT read the full playbook — the above sections are sufficient. Do NOT read the four upstream research artifacts (that's PM territory).

---

## Contract Document Structure

The contract document (`docs/contracts/CLI_GRAMMAR_CONTRACT.md`) must contain:

### Required Sections

1. **Line Type Taxonomy** — Table of all 7 line types with: tag, spoken (yes/no), voice persona, salience level (S1-S6), detection method (regex or prefix match).

2. **Grammar Rules (G-01 through G-07)** — Each rule gets:
   - Rule ID
   - Plain-English constraint
   - Regex or validation function signature
   - Example PASS output
   - Example FAIL output

3. **Anti-Pattern Registry** — Each pattern gets:
   - Pattern ID (AP-01 through AP-07)
   - Grep-testable regex
   - Applies to which line types (spoken lines only, or all lines)
   - Severity (CRITICAL if it would be spoken, HIGH if display-only)

4. **Voice Routing Table** — Maps line type → persona → TTS behavior (speak, skip, interrupt-priority)

5. **Boundary Statement** — One paragraph: "This contract governs CLI output formatting and voice routing only. It has zero authority over game mechanics, Box resolution, or Oracle state. Presentation changes here produce no side effects in the engine."

### Contract Invariant

The contract must include this invariant verbatim:

> **INVARIANT:** Every line of CLI output maps to exactly one line type. Every line type has exactly one voice routing rule. No line type may be added, removed, or reclassified without a contract amendment WO.

---

## Gate Test Specifications

New gate test suite: `tests/test_gate_J_grammar_contract.py`

Register as Gate J in `tests/conftest.py` (or wherever gate registration lives — confirm path before writing).

**Test structure:** Each test validates one grammar rule or anti-pattern against sample output. Tests are self-contained (no live combat needed). Use fixture strings that represent valid and invalid output.

| Test ID | Tests | Method |
|---|---|---|
| J-01 | G-01 turn banner | Regex match on valid banners; reject banners with dashes, prefixes, lowercase starts |
| J-02 | G-02 action result | Sentence count <= 2; no bare mechanical numbers (regex: `\b\d+\b` not inside `[RESOLVE]` lines) |
| J-03 | G-03 alert format | Regex: `^.+ is [A-Z]+\.$` — accept `Goblin Scout is DEFEATED.`, reject `goblin is hurt` |
| J-04 | G-04 narration | Sentence count 1-3; word count per sentence >= 8; char count per line <= 120 |
| J-05 | G-05 prompt | String equality: `Your action?` |
| J-06 | G-06 system prefix | Starts with `[AIDM]`; confirm not in "spoken lines" list |
| J-07 | G-07 detail prefix | Starts with `[RESOLVE]`; confirm not in "spoken lines" list |
| J-08 | Anti-patterns | Feed forbidden patterns through classifier; all must be rejected |
| J-09 | Line classifier completeness | Feed sample output; every line gets exactly one type assignment |
| J-10 | Voice routing table | For each line type, confirm routing matches contract (spoken/silent, persona assignment) |

**Gate convention:** Tests must follow existing gate test patterns in the repo. Check `tests/test_gate_A_*.py` through `tests/test_gate_I_*.py` for naming, marker, and assertion conventions.

---

## Integration Seams

1. **Existing contract files in `docs/contracts/`:** The new contract joins `DISCOVERY_LOG.md`, `INTENT_BRIDGE.md`, and `WORLD_COMPILER.md`. Follow existing format conventions.

2. **Gate registration:** New gate J must be registered in the boundary completeness gate (`test_boundary_completeness_gate.py`). Verify the registration mechanism before writing — confirm path.

3. **Validator script:** `scripts/check_cli_grammar.py` should be importable by future WOs (Tier 3 will use it to validate output changes, Tier 5 will call it from the evaluation harness). Design it as a standalone CLI tool that also exposes a `check_grammar(lines: list[str]) -> list[Violation]` function.

---

## Assumptions to Validate

1. **Gate registration mechanism** — Confirm how gates A-I are registered (conftest markers, boundary completeness gate, or both). Match the pattern.

2. **Existing output format** — The current `play.py` output may not comply with G-01 through G-07 (this WO freezes the spec, not the implementation). Gate tests should validate the *contract* with fixture strings, not live output. Live output compliance is Tier 3.

3. **Line classifier location** — The contract defines line types. The classifier function that implements detection should live in the contract module or a thin utility. Confirm no existing classifier conflicts.

4. **Anti-pattern regex scope** — The anti-patterns apply to "spoken output" (line types with spoken=yes). System and Detail lines are excluded from anti-pattern checks.

5. **`[RESOLVE]` vs `[AIDM]` prefix convention** — Verify these prefixes are already used in the codebase. If the codebase uses different prefixes, document the mapping in the contract.

---

## Preflight

Run `python scripts/preflight_canary.py` and log results in `pm_inbox/PREFLIGHT_CANARY_LOG.md` before starting work.

---

## Delivery

### Commit

Single commit with message format: `feat: WO-VOICE-GRAMMAR-SPEC-001 — CLI Grammar Contract freeze + Gate J tests`

All gate tests must pass. Existing 162 gate tests (A-I) must still pass. Full test suite (5,978+) must show zero regressions.

### Completion Report

File as `pm_inbox/DEBRIEF_WO-VOICE-GRAMMAR-SPEC-001.md`. 500 words max. Five mandatory sections:

0. **Scope Accuracy** — Did you deliver what was asked? Note any deviations.
1. **Discovery Log** — Anything you found that the dispatch didn't anticipate.
2. **Methodology Challenge** — Hardest part and how you solved it.
3. **Field Manual Entry** — One tradecraft tip for the next builder working in this area.
4. **Builder Radar** (mandatory, 3 labeled lines):
   - **Trap.** Hidden dependency or trap for the next WO.
   - **Drift.** Current drift risk.
   - **Near stop.** What got close to triggering a stop condition.

### Debrief Focus Questions

1. **Spec divergence:** Did the research playbook's grammar rules need any modification when you formalized them as testable invariants? What changed and why?
2. **Underspecified anchor:** Is there any grammar rule that's ambiguous enough to produce different test results depending on interpretation?

---

## Stop Conditions

- Do NOT modify `play.py` or any display code. This WO creates the spec and tests, not the implementation.
- Do NOT modify Box, Oracle, Lens, or Spark code. This is presentation-layer spec only.
- Do NOT read or modify doctrine files.
- Do NOT create gate tests that require live combat execution. Use fixture strings.
- If you discover that the existing output format contradicts the spec in a way that makes gate tests impossible, document the contradiction and halt. Do not resolve it.
