# WO-VOICE-ROUTING-IMPL-001 — Line-Type Tags + RESOLVE/AIDM Prefixes

**Type:** CODE
**Priority:** BURST-001 Tier 3.3
**Depends on:** WO-VOICE-GRAMMAR-IMPL-001 (Tier 3.1+3.2)
**Blocked by:** WO-VOICE-GRAMMAR-IMPL-001 must land first (banners + alerts establish the patterns this WO classifies)

---

## Target Lock

Every line of CLI output maps to exactly one of 7 line types (TURN, RESULT, ALERT, NARRATION, PROMPT, SYSTEM, DETAIL). Mechanical resolution output gets `[RESOLVE]` prefix. System messages get `[AIDM]` prefix. Spoken lines contain no bare numbers, no abbreviations, no parenthetical asides.

## Binary Decisions (all resolved by contract)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | Where do attack rolls go? | `[RESOLVE]` prefixed detail lines — never spoken | G-07 |
| 2 | Where do damage numbers go? | `[RESOLVE]` prefixed detail lines — never spoken | G-07 |
| 3 | Where do HP changes go? | `[RESOLVE]` prefixed detail lines — never spoken | G-07 |
| 4 | What does the player see for attack results? | RESULT line: 1-2 sentence narrative ("The blade finds its mark.") | G-02 |
| 5 | Does `show_status()` get prefixed? | Yes — `[AIDM]` prefix. Status is system output, never spoken. | G-06 |
| 6 | What about movement output? | `[RESOLVE]` for coordinates/distances. RESULT for narrative ("Kael advances.") | G-07, G-02 |

## Contract Spec

**Source:** `docs/contracts/CLI_GRAMMAR_CONTRACT.md` (frozen, 27 Gate J tests)

### Changes Required

**Attack resolution (`play.py`, `format_events()` ~571-608)**

Current:
```
  Roll: [17] + 5 = 22 vs AC 15 -> HIT
```

Target:
```
[RESOLVE] Attack roll: [17]+5 = 22 vs AC 15 → HIT
The blade finds its mark.
```

The `[RESOLVE]` line carries the mechanical detail (display-only, never spoken). The RESULT line is the spoken narrative (1-2 sentences, no bare numbers per G-02).

**Damage output (`play.py`, ~609-612)**

Current:
```
  Damage: 2d6+3 -> 11 hp
```

Target:
```
[RESOLVE] Damage: 2d6+3 = 11
```

Damage is mechanical — entirely `[RESOLVE]`. The narrative impact goes in the RESULT line above or in the HP change line below.

**HP changes (`play.py`, ~613-626)**

Current:
```
  Kael: healed 8 HP (Cure Light Wounds) — HP 15 -> 23
```

Target:
```
[RESOLVE] HP: 15 → 23 (+8, Cure Light Wounds)
```

All HP values are mechanical detail. Healing narrative goes in a RESULT line if needed.

**Movement (`play.py`, ~648-664)**

Current:
```
  Kael moves to (3, 4) [15 ft]
```

Target:
```
[RESOLVE] Move: (3,4), 15 ft
```

Coordinate data is mechanical. If a narrative movement line is desired, it's a RESULT line: "Kael advances across the chamber."

**Status display (`play.py`, ~716-737)**

Current:
```
  Kael                  HP 45/52  AC 18  BAB +6  Spd 6sq  (3,4) PRONE
```

Target:
```
[AIDM] Kael                  HP 45/52  AC 18  BAB +6  Spd 6sq  (3,4) PRONE
```

Status display is system output — abbreviations are fine inside `[AIDM]` lines (AP-03 only applies to spoken lines).

**Victory/game-over messages**

Prefix with `[AIDM]` — these are system announcements.

### Implementation Architecture

The core change is adding a `line_type` concept to output. Two approaches:

**Approach A (minimal):** Prefix strings directly. Every `print()` or `lines.append()` call gets the right prefix. No new abstraction.

**Approach B (structured):** Create a small `OutputLine` namedtuple or dataclass with `(line_type, text)` fields. `format_events()` returns typed lines. Display layer renders with appropriate prefix.

**Recommendation:** Approach A. We're not building a rendering engine. We're prefixing strings. The line-type classification system already exists in the grammar contract's regex detection — Gate J tests prove it. The builder just needs to make the output match what the tests expect.

### Out of Scope

- TTS integration (speaks lines based on type) — future Tier 4/5
- Narration generation (Spark-produced NARRATION lines) — already handled by GuardedNarrationService
- RESULT line content quality (narrative sentence construction) — template fallback is acceptable for now
- Action economy budget display formatting — deferred

## Implementation Plan

1. Prefix all mechanical output with `[RESOLVE]`: attack rolls, damage, HP changes, saves, movement coordinates, maneuver checks
2. Prefix all system output with `[AIDM]`: round headers (should already be done by 3.1+3.2), status display, victory/defeat messages, game title
3. Add RESULT lines for attack outcomes: short narrative sentence (template: "The {weapon} strikes true." / "The attack goes wide.")
4. Verify no spoken line contains bare mechanical numbers (AP-03 for spoken lines)
5. Verify no spoken line contains abbreviations from AP-03 list (atk, dmg, hp, AC, DC, DR, SR, CL, BAB)
6. Run Gate J tests (27/27) + Gate Q tests (from 3.1+3.2) + new Gate R tests

## Gate Specification

**New gate:** Gate R (Voice Routing)

| Test ID | Assertion | Type |
|---------|-----------|------|
| R-01 | Attack roll output has `[RESOLVE]` prefix | prefix check |
| R-02 | Damage output has `[RESOLVE]` prefix | prefix check |
| R-03 | HP change output has `[RESOLVE]` prefix | prefix check |
| R-04 | Save roll output has `[RESOLVE]` prefix | prefix check |
| R-05 | Movement coordinate output has `[RESOLVE]` prefix | prefix check |
| R-06 | Status display has `[AIDM]` prefix | prefix check |
| R-07 | Round header has `[AIDM]` prefix | prefix check |
| R-08 | Victory/defeat message has `[AIDM]` prefix | prefix check |
| R-09 | No bare numbers in spoken (non-prefixed) lines | anti-pattern scan |
| R-10 | No AP-03 abbreviations in spoken lines | anti-pattern scan |
| R-11 | Every output line classifies to exactly one line type | completeness |
| R-12 | Gate J regression (27/27) | regression |
| R-13 | Gate Q regression (from 3.1+3.2) | regression |
| R-14 | Full suite regression (6,234+ baseline) | regression |

**Expected test count:** 14 new Gate R tests.

## Integration Seams

- `format_events()` is the primary target — this function produces most game output
- `show_status()` — needs `[AIDM]` prefix
- Play loop display — round headers, victory, prompts
- Attack RESULT lines — template text needs to be reasonable but doesn't need Spark quality. Simple templates: `"The {weapon} strikes true."` / `"The attack goes wide."` / `"The spell takes hold."`
- GuardedNarrationService already produces NARRATION-type output — verify it doesn't get double-tagged

## Assumptions to Validate

1. `format_events()` return value — currently returns `list[str]`. Adding prefixes changes string content but not the interface. Verify no downstream consumer relies on unprefixed format.
2. Smoke test scenarios capture output — verify prefixed lines don't break existing smoke test output matching.
3. RESULT template lines — verify the simple templates don't conflict with Spark-generated narration when Spark is active (they shouldn't — Spark replaces the template, not augments it).

## Preflight

```bash
python scripts/preflight_canary.py
python -m pytest tests/test_grammar_gate_j.py -v
python -m pytest tests/test_grammar_gate_q.py -v  # from 3.1+3.2
python -m pytest tests/ -x --timeout=30
```

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order ready. Voice routing implementation. Awaiting Thunder."
```

## Delivery Footer

**Debrief format:** CODE — 500 words max, 5 sections + Radar (3 lines).
**Radar bank:** (1) Anything that broke unexpectedly, (2) Any output lines that didn't cleanly classify to one type, (3) Anything the golden regen WO should know.
