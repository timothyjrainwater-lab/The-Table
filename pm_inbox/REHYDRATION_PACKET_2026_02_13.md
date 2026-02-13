# REHYDRATION PACKET — DnD-3.5 AIDM Project
## For: Incoming GPT Co-PM Agent
## Date: 2026-02-13
## Prepared by: Claude (Opus 4.6) — PM execution lead

---

## 1. PROJECT IDENTITY

**What this is:** A D&D 3.5 Edition combat engine (AIDM — AI Dungeon Master) with a playable CLI. The engine is event-sourced, deterministic, and rules-faithful. The CLI (`play.py`) lets a human play 1v1 combat (Fighter vs Goblin) against the engine.

**Repository:** `f:\DnD-3.5` on branch `master`
**Language:** Python 3.11, pytest test suite
**Test suite:** 5,330+ tests (55 CLI-specific), 16 skipped, 7 hw-gated TTS failures (irrelevant to combat work)

---

## 2. CURRENT STATE (as of this packet)

### Last Committed: `11a2006`
```
11a2006 fix: conditions list-format crash found in human playtest
0f39197 feat: add playtest result logger for agent handoff
8a94e32 feat: add session bootstrap verifier
5a54972 feat: Phase 1 — movement, self-targeting, fuzzy match verified
345eb14 feat: CLI spell display + command hardening
4be2881 feat: add playable CLI, audit snapshot script, and doc reconciliation
```

### Uncommitted Changes (staged for next commit)
3 files modified, 1 new file, 1 new directory:

| File | Change | Status |
|------|--------|--------|
| `play.py` | Transcript autologging (TeeWriter), self-spell display fix, condition display fix | Modified, unstaged |
| `tests/test_play_cli.py` | Updated 2 condition display assertions to match new format | Modified, unstaged |
| `.gitignore` | Added `runtime_logs/` | Modified, unstaged |
| `scripts/triage_latest_playtest.py` | NEW — automated playtest triage from transcript logs | Untracked |
| `.vscode/tasks.json` | NEW — one-click VS Code task buttons (PLAY, TEST-CLI, TEST-ALL) | Untracked |
| `.vscode/launch.json` | Already existed — 3 debug configs (Play, Play+seed, Run Tests) | Untracked |

**All 55 CLI tests pass. Full suite: 5,330 passed, 0 regressions.**

These changes need to be committed. Suggested message:
```
feat: transcript autologging + display polish + playtest triage script

- Self-only spells now show "casts Shield on themselves!" (not "on Aldric!")
- Spell conditions show "gains Shield effect (10 rounds)" (not "is now shield")
- play.py auto-tees stdout to runtime_logs/ during interactive sessions
- New: scripts/triage_latest_playtest.py — structured analysis of play logs
- New: .vscode/tasks.json — one-click PLAY/TEST buttons
```

### Untracked Docs (NOT part of the codebase — thesis/planning artifacts)
```
docs/planning/COUNTER_THESIS_OPERATIONAL_REALITY_2026_02_13.md
docs/planning/THESIS_AI_FLEET_ORCHESTRATION_2026_02_13.md
docs/planning/THESIS_FINAL_AI_FLEET_MANAGEMENT_2026_02_13.md
docs/planning/THESIS_PART2_OPERATIONAL_SOLUTIONS_2026_02_13.md
pm_inbox/AGENT_WO-THESIS-DRIFT-001_completion.md
```
These are co-PM discussion artifacts. Do NOT commit unless Thunder explicitly requests it.

---

## 3. ARCHITECTURE — WHAT MATTERS

### Engine Pipeline (read order for understanding)
```
play.py                          CLI entry point, input parsing, display
  ↓
aidm/runtime/play_controller.py  build_simple_combat_fixture() — creates 1v1 world state
  ↓
aidm/interaction/intent_bridge.py  resolve_attack/move/spell — converts player input to engine intents
  ↓
aidm/core/play_loop.py           execute_turn() — event-sourced turn resolution
  ↓
aidm/core/spell_resolver.py      SpellResolver.resolve_spell() — spell targeting, damage, conditions
aidm/core/conditions.py          get_condition_modifiers() — condition query for combat math
aidm/core/rng_manager.py         RNGManager(seed + turn_index) — deterministic dice
```

### Key Schema Files
```
aidm/schemas/entity_fields.py    EF enum — all entity field keys (HP_CURRENT, POSITION, TEAM, etc.)
aidm/schemas/intents.py          DeclaredAttackIntent, MoveIntent, CastSpellIntent
aidm/schemas/attack.py           AttackIntent, StepMoveIntent, Weapon
aidm/schemas/conditions.py       ConditionInstance, ConditionModifiers
aidm/schemas/position.py         Position(x, y)
aidm/data/spell_definitions.py   SPELL_REGISTRY — all spell definitions (Shield, Magic Missile, etc.)
```

### Known Convention Mismatch (IMPORTANT)
**Two incompatible condition storage formats exist:**
- `conditions.apply_condition()` stores as **dict of dicts**: `{"shield": {condition_data...}}`
- `play_loop.py` spell resolver (line ~452) stores as **list of strings**: `["shield"]`

This was the root cause of the only playtest crash so far. Fixed in `conditions.py:get_condition_modifiers()` with an `isinstance(conditions_data, list)` guard that returns zero modifiers for list-format entries. The proper fix would be to unify the storage format, but that's a larger refactor deferred to a future WO.

---

## 4. PLAYTEST INFRASTRUCTURE

### How to play
```
python play.py              # seed 42 (default)
python play.py --seed 99    # different dice
```
Or in VS Code: F5 → "Play D&D 3.5e Combat"

### What the player can do
```
attack <target>             attack goblin warrior
attack <target> with <wpn>  attack goblin with longsword
cast <spell> on <target>    cast magic missile on goblin
cast <spell> on self        cast shield on me
move <x> <y>                move 4 3 (adjacent squares only)
status / look               show HP and positions
help / ?                    show commands
end / pass                  end your turn
quit                        exit
```

### Autologging
Interactive sessions auto-save to `runtime_logs/play_<timestamp>.log`. The `runtime_logs/LATEST` file points to the most recent log.

### Triage workflow (the rule Thunder established)
```
1. Play the game (python play.py)
2. Quit when done
3. Agent runs: python scripts/triage_latest_playtest.py
4. Triage report determines next action:
   - GREEN: proceed to next WO
   - YELLOW: open micro-WO for the finding
   - RED: fix-first, no WO advancement
```

**Operating rule:** No WO advances on "playtest passed." A WO advances on "playtest triage completed." This was explicitly established by Thunder in this session.

### Recording results
```
python scripts/record_playtest.py passed|failed|inconclusive "optional note"
# Appends to pm_inbox/playtest_log.jsonl
```

### Session bootstrap (run at start of every agent session)
```
python scripts/verify_session_start.py          # fast: git + test collection
python scripts/verify_session_start.py --full   # includes actual pytest run
```

---

## 5. COMPLETED WORK ORDERS (this session)

| WO | Status | Commit | Summary |
|----|--------|--------|---------|
| WO-COMMIT-01 | DONE | `345eb14` | Committed dirty tree (play.py + tests) |
| WO-MOVE-01 | DONE | `5a54972` | StepMoveIntent now updates entity position in world state |
| WO-FUZZY-01 | DONE (no-op) | `5a54972` | Verified substring matching already works in intent_bridge.py:316 |
| WO-SELFTARGET-01 | DONE | `5a54972` | "self"/"me"/"myself" → `__SELF__` sentinel in parse_input |
| WO-OPS-FOUNDATION-01 | DONE (stripped) | `8a94e32`, `0f39197` | verify_session_start.py + record_playtest.py only |
| CRASH FIX | DONE | `11a2006` | conditions.py list-format tolerance |
| Display polish | DONE | uncommitted | Self-spell display, condition labels, autologging, triage script |

---

## 6. NEXT WORK — PHASE 2

### WO-ENCOUNTER-01: Expand 1v1 to 3v3 Party Combat
**Status:** READY TO START (gated on commit of current changes + playtest triage)

**Objective:** Replace the 1v1 fixture (Aldric the Fighter vs 1 Goblin Warrior) with a 3v3 party:
- **Party:** Fighter (melee), Cleric (healer/melee), Rogue (melee, sneak attack)
- **Monsters:** 3 Goblin Warriors

**Key implementation points:**
- Modify `build_simple_combat_fixture()` in `aidm/runtime/play_controller.py`
- The main loop in `play.py` already iterates `initiative_order` and handles multiple entities
- Need to decide: does the player control ALL party members, or just the Fighter?
- Enemy AI (`pick_enemy_target` in play.py) already picks the first non-defeated opposing team member — may want smarter targeting for 3v3

**Risks:**
- Initiative order with 6 entities — needs testing
- Spell targeting with multiple party members ("cast cure light wounds on cleric")
- `is_combat_over()` already checks team-level defeat, should work as-is

### Future Phases (not yet started)
- **Phase 3:** WO-CONTEXT-01, WO-INITIATIVE-01, WO-FULLATTACK-CLI-01
- **Phase 4:** WO-SPELLSLOTS-01 (plan only, needs approval)

---

## 7. OPERATING RULES (established by Thunder)

1. **No WO advances on "playtest passed."** Advances on "playtest triage completed" (evidence + findings + decision).
2. **RED state = STOP.** If runtime is paused on exception, no further work continues. Next action is always: stop run → capture evidence → apply fix → regression test → re-run exact repro.
3. **Human interlock format.** When operator action is needed, output a visually distinct block with STATUS, one task, binary response. Machine context goes below.
4. **Session bootstrap.** Every agent session starts with `python scripts/verify_session_start.py` output.
5. **Resist over-engineering.** Thunder explicitly rejected full governance systems (SOURCES_OF_TRUTH.md, handoff formats, scenario tests). Ship code, not process docs. One file, one rule.
6. **Commit only when asked** or when explicitly finishing a WO.

---

## 8. TEST COMMANDS (quick reference)

```bash
# CLI tests only (fast, ~0.3s)
python -m pytest tests/test_play_cli.py -q --tb=short

# Full suite (slow, ~2min, excludes TTS)
python -m pytest tests/ -q --tb=short --ignore=tests/immersion/test_chatterbox_tts.py

# Full suite including TTS (will fail without GPU/model)
python -m pytest tests/ -q --tb=short

# Session bootstrap
python scripts/verify_session_start.py

# Playtest triage
python scripts/triage_latest_playtest.py
```

---

## 9. PLAYTEST LOG (evidence trail)

```json
{"timestamp": "2026-02-13T08:15:21", "commit": "11a2006", "result": "passed", "note": "cast-then-attack crash fix verified, all commands functional"}
```

One playtest on record. The display polish changes (uncommitted) were verified by automated transcript capture but have not had a human playtest yet.

---

## 10. KNOWN ISSUES / TECH DEBT

1. **Condition storage mismatch** — play_loop stores as list, conditions.py expects dict. Guarded but not unified. Future WO.
2. **Melee range not enforced** — player can move away and still attack at range. Engine doesn't check adjacency for melee. Known limitation.
3. **No spell slot tracking** — all spells are unlimited. Deferred to WO-SPELLSLOTS-01.
4. **No initiative system** — turns cycle in fixed order. Deferred to WO-INITIATIVE-01.
5. **Enemy AI is trivial** — always attacks first non-defeated PC. No tactics.
6. **No full attack action** — single attack per turn only. Deferred to WO-FULLATTACK-CLI-01.
