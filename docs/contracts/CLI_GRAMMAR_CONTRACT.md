# CLI Grammar Contract v1
## Output Formatting + Voice Routing Specification

**Document ID:** RQ-GRAMMAR-001
**Version:** 1.0
**Date:** 2026-02-19
**Status:** DRAFT — Awaiting PM Approval
**Authority:** This document is the canonical contract for CLI output grammar rules and voice routing. It governs how all player-facing output is formatted and which lines are spoken by TTS.
**Scope:** Line type classification, grammar rules (G-01 through G-07), anti-pattern registry (AP-01 through AP-07), voice routing table, and salience levels. Presentation-layer spec only.

**References:**
- `pm_inbox/reviewed/legacy_pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md` — Source research (Sections 1.2, 2, 5.2, 9)
- `docs/contracts/INTENT_BRIDGE.md` (RQ-INTENT-001) — Upstream intent resolution
- `aidm/runtime/display.py` — Current display formatting functions
- `aidm/runtime/runner.py` — Logging prefix `[AIDM]`

**Existing Implementation (this spec formalizes):**

| Layer | File | Status |
|-------|------|--------|
| Display formatting | `aidm/runtime/display.py` | Exists — uses `[AIDM]` and `[RESOLVE]` prefixes |
| Runner logging | `aidm/runtime/runner.py` | Exists — `[AIDM]` log format |
| Grammar validator | `scripts/check_cli_grammar.py` | **New — created by this WO** |
| Gate tests | `tests/test_grammar_gate_j.py` | **New — created by this WO** |

---

## Contract Summary (1-Page)

Every line of CLI output belongs to exactly one of seven line types. Each line type has a fixed grammar rule, a salience level, and a voice routing rule. The grammar rules ensure that spoken output is natural, unambiguous, and free of mechanical artifacts. Non-spoken lines use structured prefixes (`[AIDM]`, `[RESOLVE]`) to clearly mark system and detail content.

**Three-Layer Model:**

```
CLI Output Line  →  Line Type Classifier  →  Voice Router
   (raw text)         (G-01..G-07)           (speak / skip)
```

The classifier assigns exactly one type per line. The router determines whether TTS speaks it and which persona delivers it. No line may be unclassified. No line type may have ambiguous routing.

**Invariants:**
1. **Complete classification:** Every line of CLI output maps to exactly one line type.
2. **Deterministic routing:** Every line type has exactly one voice routing rule.
3. **Presentation boundary (B-06):** This contract governs CLI output formatting and voice routing only. It has zero authority over game mechanics, Box resolution, or Oracle state. Presentation changes here produce no side effects in the engine.
4. **Frozen taxonomy:** No line type may be added, removed, or reclassified without a contract amendment WO.

> **INVARIANT:** Every line of CLI output maps to exactly one line type. Every line type has exactly one voice routing rule. No line type may be added, removed, or reclassified without a contract amendment WO.

---

## 1. Line Type Taxonomy

Seven line types with salience levels S1 (highest urgency) through S6 (lowest / never spoken).

| Tag | Spoken | Voice Persona | Salience | Detection Method |
|-----|--------|---------------|----------|------------------|
| TURN | Yes | DM persona | S3 | Regex: `^[A-Z].*'s Turn$` |
| RESULT | Yes | DM persona | S3 | Sentence-level output following an action resolution (not prefixed) |
| ALERT | Yes | Arbor (urgent) | S1 | Regex: `^.+ is [A-Z]+\.$` |
| NARRATION | Yes | DM persona | S4 | 1-3 sentences, no prefix, not matching other types |
| PROMPT | Yes | Arbor (calm) | S2 | String equality: `Your action?` |
| SYSTEM | No | — | S6 | Prefix: `[AIDM]` |
| DETAIL | No | — | S5 | Prefix: `[RESOLVE]` |

**Salience ordering:** S1 (ALERT) > S2 (PROMPT) > S3 (TURN, RESULT) > S4 (NARRATION) > S5 (DETAIL, display-only) > S6 (SYSTEM, display-only).

---

## 2. Grammar Rules (G-01 through G-07)

### G-01: Turn Banner

- **Constraint:** Turn announcement starts with an uppercase character name and ends with `'s Turn`. No dashes, no prefix tokens, no decorative separators.
- **Regex:** `^[A-Z][A-Za-z .'-]*'s Turn$`
- **Example PASS:** `Kael's Turn`
- **Example PASS:** `Goblin Scout's Turn`
- **Example FAIL:** `--- Kael's Turn ---` (dashes)
- **Example FAIL:** `[TURN] Kael's Turn` (prefix)
- **Example FAIL:** `kael's Turn` (lowercase start)

### G-02: Action Result

- **Constraint:** Action result output is at most 2 sentences. No bare mechanical numbers appear in spoken output. Mechanical details belong in `[RESOLVE]` lines.
- **Validation:** Sentence count <= 2. No regex match for `\b\d+\b` in result text (numbers in `[RESOLVE]` lines are exempt).
- **Example PASS:** `The sword bites deep. The goblin staggers backward.`
- **Example FAIL:** `The sword hits for 14 damage. The goblin has 6 HP remaining.` (bare numbers)
- **Example FAIL:** `The blade strikes true. The enemy recoils. Blood spatters the stone floor.` (3 sentences)

### G-03: Alert Format

- **Constraint:** Status alerts follow the pattern `{name} is {STATUS}.` where STATUS is a single UPPERCASE word.
- **Regex:** `^.+ is [A-Z]+\.$`
- **Example PASS:** `Goblin Scout is DEFEATED.`
- **Example PASS:** `Kael is BLOODIED.`
- **Example FAIL:** `goblin is hurt` (lowercase status, no period)
- **Example FAIL:** `The goblin scout has been defeated.` (not pattern-compliant)

### G-04: Narration

- **Constraint:** Narration blocks are 1-3 sentences. Each sentence has a minimum of 8 words. Maximum 120 characters per line.
- **Validation:** Sentence count 1-3. Word count per sentence >= 8. Character count per line <= 120.
- **Example PASS:** `The torchlight flickers against the damp stone walls of the corridor.`
- **Example FAIL:** `Fire burns.` (fewer than 8 words)
- **Example FAIL:** (line > 120 characters)

### G-05: Prompt

- **Constraint:** The action prompt is exactly the string `Your action?` — no variation.
- **Validation:** String equality.
- **Example PASS:** `Your action?`
- **Example FAIL:** `What do you do?`
- **Example FAIL:** `> Your action?` (prefix)

### G-06: System Prefix

- **Constraint:** System messages begin with the `[AIDM]` prefix. System lines are never spoken by TTS.
- **Detection:** Prefix match `[AIDM]`.
- **Example PASS:** `[AIDM] Loading campaign data...`
- **Example PASS:** `[AIDM] ERROR: Missing asset`
- **Example FAIL:** `AIDM: Loading...` (wrong prefix format)

### G-07: Detail Prefix

- **Constraint:** Resolution detail lines begin with the `[RESOLVE]` prefix. Detail lines are never spoken by TTS.
- **Detection:** Prefix match `[RESOLVE]`.
- **Example PASS:** `[RESOLVE] Rolling attack: [17]+5 = 22`
- **Example PASS:** `[RESOLVE] Result: HIT`
- **Example FAIL:** `Rolling attack: [17]+5 = 22` (missing prefix)

---

## 3. Anti-Pattern Registry (AP-01 through AP-07)

Anti-patterns apply to **spoken lines only** (TURN, RESULT, ALERT, NARRATION, PROMPT). SYSTEM and DETAIL lines are exempt.

| Pattern ID | Description | Grep-Testable Regex | Applies To | Severity |
|------------|-------------|---------------------|------------|----------|
| AP-01 | Dashed separators | `^-{3,}\|^={3,}` | Spoken lines | CRITICAL |
| AP-02 | Parenthetical asides | `\(.*\)` | Spoken lines | CRITICAL |
| AP-03 | Abbreviations in spoken text | `\b(atk\|dmg\|hp\|AC\|DC\|DR\|SR\|CL\|BAB)\b` | Spoken lines | CRITICAL |
| AP-04 | ALL CAPS full sentences | `^[A-Z][A-Z ]{8,}[.!?]$` | Spoken lines | CRITICAL |
| AP-05 | Numbered lists in narration | `^\d+[.)]\s` | NARRATION only | CRITICAL |
| AP-06 | Emoji or Unicode symbols | `[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u27BF]` | Spoken lines | CRITICAL |
| AP-07 | Short sentences in narration | (sentence word count < 8) | NARRATION only | CRITICAL |

**Severity key:**
- **CRITICAL:** Would produce unnatural or broken TTS output if spoken.

---

## 4. Voice Routing Table

| Line Type | Persona | TTS Behavior | Interrupt Priority |
|-----------|---------|--------------|-------------------|
| ALERT | Arbor (urgent) | Speak — immediate | Highest (S1) |
| PROMPT | Arbor (calm) | Speak — after content | High (S2) |
| TURN | DM persona | Speak — announce | Normal (S3) |
| RESULT | DM persona | Speak — narrate | Normal (S3) |
| NARRATION | DM persona | Speak — atmosphere | Low (S4) |
| DETAIL | — | Skip — display only | None (S5) |
| SYSTEM | — | Skip — display only | None (S6) |

**Routing invariants:**
- Lines with `spoken=yes` are delivered to TTS in salience order.
- Lines with `spoken=no` are displayed on the CLI but never sent to TTS.
- `[AIDM]` and `[RESOLVE]` prefixed lines must never appear in TTS output (CC-14).

---

## 5. Boundary Statement

This contract governs CLI output formatting and voice routing only. It has zero authority over game mechanics, Box resolution, or Oracle state. Presentation changes here produce no side effects in the engine. TTS, prosodics, and voice routing are Lens/Immersion concerns with zero Box impact (B-06).

---

## END OF CLI GRAMMAR CONTRACT v1.0
