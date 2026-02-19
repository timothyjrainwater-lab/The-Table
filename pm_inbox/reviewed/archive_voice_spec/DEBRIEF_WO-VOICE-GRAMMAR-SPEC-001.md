# DEBRIEF: WO-VOICE-GRAMMAR-SPEC-001

**Builder:** Anvil
**Date:** 2026-02-19
**Commit:** (pending — all deliverables ready for commit)

---

## 0. Scope Accuracy

Delivered exactly what was asked: contract document, gate tests, and validator script. Three files created:

- `docs/contracts/CLI_GRAMMAR_CONTRACT.md` — Full contract with all 5 required sections: line type taxonomy, grammar rules G-01 through G-07, anti-pattern registry AP-01 through AP-07, voice routing table, and boundary statement with the verbatim invariant.
- `tests/test_grammar_gate_j.py` — 27 test methods across 10 test classes (J-01 through J-10). All fixture-based, no live combat. Follows existing gate naming convention (`test_<subsystem>_gate_<letter>.py`).
- `scripts/check_cli_grammar.py` — Standalone CLI tool with `check_grammar(lines: list[str]) -> list[Violation]` public API. Exit code 0/1 for CI gating. Reads from file or stdin.

One deviation: the WO specified file name `tests/test_gate_J_grammar_contract.py` but existing convention uses `test_<subsystem>_gate_<letter>.py` (e.g., `test_ui_gate_f.py`, `test_oracle_gate_b.py`). Named it `test_grammar_gate_j.py` to match. 27 tests rather than the 10 test IDs listed because each J-ID contains multiple sub-assertions split into separate test methods for clearer failure reporting.

No changes to `play.py`, Box, Oracle, Lens, Spark, or doctrine files. Zero regressions: 5930 existing tests still pass (7 pre-existing failures unrelated to this WO).

---

## 1. Discovery Log

- **No centralized line classifier existed.** The codebase categorizes output implicitly by which `format_*` function in `display.py` produced it. The contract now defines the taxonomy explicitly; the classifier function lives in both the gate test file and the validator script.
- **Gate registration is implicit.** No central registry — pytest auto-discovers gate test files by naming convention. The boundary completeness gate (`test_boundary_completeness_gate.py`) validates layer imports, not gate registration. Gate J integrates by following the file naming convention.
- **`[AIDM]` and `[RESOLVE]` prefixes confirmed in `display.py` and `runner.py`.** The prefixes are hard-coded, not configurable. The contract formalizes what already exists.

---

## 2. Methodology Challenge

The hardest part was the NARRATION vs RESULT classifier ambiguity. Both are unprefixed prose lines. The playbook defines NARRATION as 1-3 sentences with min 8 words each, and RESULT as max 2 sentences. A 2-sentence line where every sentence has 8+ words satisfies both rules. Resolved by making NARRATION the match when the 8-word minimum is met (NARRATION is the stricter rule), falling through to RESULT otherwise. This heuristic works for fixture-based testing but will need context-aware classification (which format function produced it) when Tier 3 integrates with live output.

---

## 3. Field Manual Entry

The G-01 turn banner regex in the playbook (`^[A-Z].*'s Turn$`) is too permissive — it would match `[AIDM] Something's Turn`. The contract tightens it to `^[A-Z][A-Za-z .'-]*'s Turn$` which restricts the character set between the capital letter and the `'s Turn` suffix. Future builders: if you add character names with non-Latin characters or special punctuation, the regex needs updating in both the contract and the gate tests.

---

## 4. Builder Radar

- **Trap.** The NARRATION/RESULT classifier is a heuristic based on sentence length. When Tier 3 wires this to live output, lines that are ambiguous (2 sentences, 8+ words each) will be classified as NARRATION. If the intent was RESULT, the voice routing will use the wrong persona priority. Tier 3 WO should classify by source function, not by regex.
- **Drift.** The `[RESOLVE]` prefix in `display.py` includes indented sub-lines (`[RESOLVE]   vs DC 15`). The contract treats `[RESOLVE]` as a prefix match, so indented continuations starting with `[RESOLVE]` are correctly caught. But if someone introduces a `[RESOLVE]`-prefixed line that should be spoken, the contract forbids it — check before adding new `[RESOLVE]` output.
- **Near stop.** The pm_inbox hygiene gate flagged the dispatch file `WO-VOICE-GRAMMAR-SPEC-001_DISPATCH.md` for missing a `Lifecycle:` header. This is a pre-existing failure (the dispatch file was provided to me without that header). Did not modify the dispatch file per stop conditions. The hygiene test failures are not caused by this WO.

---

## Debrief Focus Answers

1. **Spec divergence:** The playbook's G-01 regex was tightened from `^[A-Z].*'s Turn$` to `^[A-Z][A-Za-z .'-]*'s Turn$` to prevent prefix tokens from matching. All other rules formalized without modification. The anti-pattern list was codified as-is from Section 2.3.

2. **Underspecified anchor:** G-02 (action result) is the weakest anchor. "No mechanical numbers" is defined as `\b\d+\b` absence, but edge cases like ordinals ("the 3rd goblin") or dice notation in flavor text ("she rolls the bones") are ambiguous. The current regex flags all bare digits. If results need ordinals, G-02 needs a carve-out regex.
