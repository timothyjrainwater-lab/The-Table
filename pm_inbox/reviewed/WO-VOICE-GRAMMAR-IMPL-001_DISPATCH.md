# WO-VOICE-GRAMMAR-IMPL-001 — Turn Banners + Alert Formatting

**Type:** CODE
**Priority:** BURST-001 Tier 3.1+3.2 (combined)
**Depends on:** WO-VOICE-GRAMMAR-SPEC-001 (ACCEPTED, 27 Gate J tests)
**Blocked by:** Nothing — ready to dispatch

---

## Target Lock

Make CLI output comply with grammar rules G-01 (turn banners), G-03 (alerts), and G-05 (prompt). All changes are presentation-only — zero engine/Box/Oracle side effects (B-06 invariant).

## Binary Decisions (all resolved by contract)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | Turn banner format | `{name}'s Turn` — no dashes, no parentheses, no suffixes | G-01 regex: `^[A-Z][A-Za-z .'-]*'s Turn$` |
| 2 | Alert format | `{name} is {STATUS}.` — STATUS is UPPERCASE, period at end | G-03 regex: `^.+ is [A-Z]+\.$` |
| 3 | Prompt string | Exactly `Your action?` — no name prefix | G-05 string equality |
| 4 | Duration info in alerts | Move to `[RESOLVE]` line, not in alert | AP-02 (no parenthetical asides in spoken lines) |
| 5 | Enemy attack banners | Same as player: `{name}'s Turn` — action details go in RESULT lines | G-01 |

## Contract Spec

**Source:** `docs/contracts/CLI_GRAMMAR_CONTRACT.md` (frozen, 27 Gate J tests)

### Changes Required

**Turn banners (`play.py`)**

| Current (line ~936) | Target |
|---|---|
| `print(f"\n--- {name}'s Turn ---")` | `print(f"\n{name}'s Turn")` |
| `print(f"\n--- {name} attacks {target}! ---")` (~1015) | `print(f"\n{name}'s Turn")` |
| `print(f"\n--- {name}'s Turn (moves toward {target}) ---")` (~1017) | `print(f"\n{name}'s Turn")` |

All three collapse to the same G-01 compliant output. Enemy action details (attacks, movement) become RESULT lines after the banner, not part of the banner.

**Alerts (`play.py`)**

| Current (line ~629) | Target |
|---|---|
| `f"  *** {name} is DEFEATED! ***"` | `f"{name} is DEFEATED."` |
| `f"  {name} is now {condition} ({duration} rounds)"` (~641) | `f"{name} is {condition.upper()}."` |
| `f"  {name} is now {condition}"` (~643) | `f"{name} is {condition.upper()}."` |

Duration info moves to a separate `[RESOLVE]` detail line: `f"[RESOLVE] {condition}: {duration} rounds remaining"`

**Prompt (`play.py`)**

| Current (line ~944) | Target |
|---|---|
| `input_fn(f"\n{name}> ")` | `print("Your action?"); input_fn("> ")` |

Note: The prompt display must be `Your action?` per G-05. The input cursor can remain `> ` for UX.

**Round headers (`play.py`)**

| Current (lines ~916, ~1032) | Target |
|---|---|
| `print(f"\n{'=' * 20} Round {n} {'=' * 20}")` | `print(f"[AIDM] Round {n}")` |

Equals separators violate AP-01. Round headers are system-level (not spoken), so `[AIDM]` prefix per G-06.

### Out of Scope

- `[RESOLVE]` prefixing for attack rolls, damage, HP changes (WO-VOICE-ROUTING-IMPL-001)
- Full line-type classification/tagging system (WO-VOICE-ROUTING-IMPL-001)
- Golden transcript regeneration (WO-VOICE-GOLDEN-REGEN-001)
- `show_status()` abbreviation cleanup (deferred — status display is `[AIDM]` system output)

## Implementation Plan

1. Fix turn banners: all three patterns → `{name}'s Turn`
2. Fix alert formatting: defeat + condition patterns → `{name} is {STATUS}.`
3. Move duration info to `[RESOLVE]` detail lines
4. Fix prompt: `Your action?` display + `> ` input cursor
5. Fix round headers: `[AIDM] Round {n}`
6. Remove decorative separators from game title/victory output (AP-01)
7. Run existing Gate J tests — expect all 27 to still pass
8. Add new gate tests for implementation (see gate spec below)

## Gate Specification

**New gate:** Gate Q (Grammar Implementation)

| Test ID | Assertion | Type |
|---------|-----------|------|
| Q-01 | Turn banner matches G-01 regex for player turns | regex |
| Q-02 | Turn banner matches G-01 regex for enemy turns | regex |
| Q-03 | Defeat alert matches G-03 regex | regex |
| Q-04 | Condition alert matches G-03 regex | regex |
| Q-05 | Condition alert has no parenthetical duration (AP-02) | anti-pattern |
| Q-06 | Duration info appears as `[RESOLVE]` line | prefix check |
| Q-07 | Prompt output is exactly `Your action?` (G-05) | string equality |
| Q-08 | Round header has `[AIDM]` prefix (G-06) | prefix check |
| Q-09 | No dashed separators in output (AP-01) | anti-pattern |
| Q-10 | No asterisk decorators in alerts | anti-pattern |
| Q-11 | Existing Gate J tests still pass (27/27) | regression |
| Q-12 | Full suite regression (6,234 baseline) | regression |

**Expected test count:** 12 new Gate Q tests.

## Integration Seams

- `format_events()` in `play.py` lines ~550-713 — alert formatting lives here
- Turn display in `play.py` lines ~936, ~1015, ~1017 — banner formatting
- `play_loop()` flow — prompt and round headers
- `[RESOLVE]` prefix is new for this file — establishes the pattern that WO-VOICE-ROUTING-IMPL-001 extends

## Assumptions to Validate

1. Enemy turn banners currently show attack intent (`Name attacks Target!`). Verify that converting to plain `Name's Turn` doesn't lose information that players need — the attack description should appear as a RESULT line immediately after.
2. Condition `.upper()` call — verify all condition names in the engine are safe to uppercase (no mixed-case names that would break).
3. `input_fn` parameter — verify the play loop's input function accepts the split display+input pattern without breaking test harnesses.

## Preflight

```bash
python scripts/preflight_canary.py
python -m pytest tests/test_grammar_gate_j.py -v
python -m pytest tests/ -x --timeout=30
```

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order ready. Grammar implementation, turn banners and alerts. Awaiting Thunder."
```

## Delivery Footer

**Debrief format:** CODE — 500 words max, 5 sections + Radar (3 lines).
**Radar bank:** (1) Anything that broke unexpectedly, (2) Anything that was harder than expected, (3) Anything the next WO should know.
