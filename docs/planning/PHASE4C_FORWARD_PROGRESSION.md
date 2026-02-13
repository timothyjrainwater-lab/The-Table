# Phase 4C Forward Progression — Work Order Package

**Prepared:** 2026-02-13
**Branch:** master
**Last Commit:** cf33598
**Test Baseline:** 5,371 collected / 5,323 passed / 16 skipped (HW-gated)
**pm_inbox:** 5 root items (under cap)

---

## Executive Summary

The engine has deep capability — 6 combat maneuvers, full attack sequences, mounted combat, AoO, DR, saves, conditions — but the CLI only exposes single attack, movement, and spellcasting. The core progression task is **surfacing existing engine capability into the player-facing CLI**, not building new resolvers.

Two categories:
1. **Wiring WOs** — Connect existing resolvers to CLI parser + display (LOW risk, 0 breaks)
2. **Fix WOs** — Correct known bugs/mismatches before adding features (MEDIUM risk, test updates)
3. **Contract WOs** — Require CP approval for frozen files (HIGH risk, deferred)
4. **Ops WOs** — Operator tooling and signal infrastructure (LOW risk, scripts/ only)

---

## Execution Waves

### Wave A: Foundation Fixes (Sequential, clears tech debt)

#### WO-CONDFIX-01 — Unify Condition Storage Format

**Risk:** MEDIUM | **Effort:** Micro | **Breaks:** ~4 tests

**Problem:** `play_loop.py` `_resolve_spell_cast()` stores conditions as bare strings in a list. `conditions.py` `get_condition_modifiers()` expects dict format. Guarded at line 63 (`if isinstance(conditions_data, list): return ConditionModifiers()`) — conditions apply visually but modifiers (AC penalty, attack penalty) are silently zeroed.

**Root Cause:**
- `play_loop.py:449-456` — appends bare string to `EF.CONDITIONS` list
- `play_loop.py:585-588` — removes by string match
- `conditions.py:54-64` — expects `{condition_id: {dict}}` format, returns empty on list

**Scope:**
- Fix `play_loop.py:449-456`: Use `apply_condition()` or structured dict `{"condition": name, "source": source, "duration_rounds": N}`
- Fix `play_loop.py:585-588`: Match removal logic to dict format
- Update ~4 tests that assert on list format

**Files:**
- `aidm/core/play_loop.py` (modify lines 449-456, 585-588)
- `tests/test_play_loop_spellcasting.py` (update ~4 tests)
- `tests/test_play_cli.py` (verify `test_cast_then_enemy_attack_no_crash` passes)

**Acceptance:** Condition modifiers actually affect combat rolls. `get_condition_modifiers()` returns non-zero values for conditioned entities. All existing tests pass.

---

#### WO-ROUND-TRACK-01 — Round Counter and Turn Display

**Risk:** LOW | **Effort:** Small | **Breaks:** 0 expected

**Problem:** CLI shows individual turns but no round boundaries. Multi-round combat is disorienting. Round number is tracked in `active_combat["round_index"]` (initialized at 0 in `play_controller.py:245`) but never incremented or displayed in `play.py`.

**Scope:**
- Track current position in initiative order in `_main_loop()`
- Detect round boundary: when the outer `for actor_id in init_order` loop restarts
- Print `"=== Round N ==="` header at each round boundary
- Increment `ws.active_combat["round_index"]` at boundary
- ~5 new tests

**Files:**
- `play.py` (modify `_main_loop`, lines 451-533)
- `tests/test_play_cli.py` (add round display tests)

**Key Implementation:**
```
Round boundary = first living actor in init_order gets their turn again
Print header before that actor's turn prompt
Increment round_index in active_combat dict
```

**Regression Watch:**
- Existing CLI tests use substring assertions — additive output won't break them
- `test_seed_42_transcript_is_stable` and `test_determinism` will see new "Round N" lines — these tests assert byte-identical output, so they will need updating to include round headers
- `test_full_combat_loop` (test_combat_completes) should still terminate

**Acceptance:** Round headers visible in output. Round counter increments correctly. All existing tests pass (with transcript updates).

---

### Wave B: CLI Capability Wiring (Parallel-safe after Wave A)

#### WO-FULLATTACK-CLI-01 — Full Attack Action in CLI

**Risk:** LOW | **Effort:** Medium | **Breaks:** 0 expected

**Problem:** Fighters can only make single attacks. The full attack resolver (`full_attack_resolver.py`) and `FullAttackIntent` routing in `play_loop.py:1040-1073` are complete. Only CLI wiring is missing.

**Scope:**
- Add `"full attack"` two-word detection in `parse_input()` — check before single-word verb split
- Add `full_attack` action type in `resolve_and_execute()` — build `FullAttackIntent` from entity BAB + weapon
- Display multi-hit output in `format_events()` — already handles `attack_roll` + `damage_roll` per-hit
- ~8 new tests

**Parser Change (play.py:64-119):**
```python
# Before single-word verb check:
if text.startswith("full attack"):
    target_ref = text[len("full attack"):].strip()
    target_ref = _strip_articles(target_ref) if target_ref else None
    return "full_attack", DeclaredAttackIntent(target_ref=target_ref, weapon=None)
```

**Resolution Change (play.py:138-207):**
```python
elif action_type == "full_attack":
    # Resolve target the same way as attack
    resolved = bridge.resolve_attack(actor_id, declared, view)
    if isinstance(resolved, AttackIntent):
        # Promote to FullAttackIntent
        from aidm.core.full_attack_resolver import FullAttackIntent
        entity = ws_copy.entities[actor_id]
        resolved = FullAttackIntent(
            attacker_id=actor_id,
            target_id=resolved.target_id,
            base_attack_bonus=entity.get(EF.BAB, 1),
            weapon=resolved.weapon,
        )
```

**Files:**
- `play.py` (modify `parse_input`, `resolve_and_execute`, `_HELP_TEXT`)
- `tests/test_play_cli.py` (add full attack parser + execution tests)

**Key Notes:**
- Current fixture: Aldric BAB 3 → 1 attack. At BAB 6 gets +6/+1 iterative.
- For playtest value, consider bumping Aldric's BAB to 6 in fixture (gets two attacks).
- `format_events()` already handles multiple `attack_roll` + `damage_roll` events — no display changes needed.

**Acceptance:** `full attack goblin warrior` works. Multiple attack rolls displayed at BAB 6+. Help text updated. Existing tests pass.

---

#### WO-MANEUVER-CLI-01 — Combat Maneuvers in CLI

**Risk:** LOW | **Effort:** Medium | **Breaks:** 0 expected

**Problem:** Engine has 6 fully implemented combat maneuvers (Bull Rush, Trip, Overrun, Sunder, Disarm, Grapple) routed through `play_loop.py:1166-1191`, but CLI has no way to invoke them.

**Scope:**
- Add maneuver verb detection in `parse_input()`:
  - `"trip <target>"` → `("trip", DeclaredAttackIntent(target_ref))`
  - `"bull rush <target>"` / `"bullrush <target>"` → `("bull_rush", ...)`
  - `"disarm <target>"` → `("disarm", ...)`
  - `"grapple <target>"` → `("grapple", ...)`
  - `"sunder <target>"` → `("sunder", ...)`
  - `"overrun <target>"` → `("overrun", ...)`
- Add maneuver resolution in `resolve_and_execute()` — build appropriate Intent from `aidm/schemas/maneuvers.py`
- Add maneuver event formatting in `format_events()`:
  - `bull_rush_declared/success/failure`
  - `trip_declared/success/failure`, `counter_trip_success/failure`
  - `disarm_declared/success/failure`, `counter_disarm_success/failure`
  - `overrun_declared/success/failure/avoided`
  - `sunder_declared/success/failure`
  - `grapple_declared/success/failure`
  - `opposed_check`, `touch_attack_roll`
- Update help text
- ~12 new tests

**Files:**
- `play.py` (modify `parse_input`, `resolve_and_execute`, `format_events`, `_HELP_TEXT`)
- `tests/test_play_cli.py` (add maneuver parser + execution + display tests)

**Key Notes:**
- All maneuver resolvers produce events that go through `play_loop.py` routing automatically
- Maneuver intents require entity stats (STR_MOD, SIZE_CATEGORY, BAB) already in fixture
- Trip + Grapple have counter-maneuver mechanics — display should show both attempts

**Acceptance:** All 6 maneuver commands parse and execute. Events display with success/failure. Help text shows maneuver commands.

---

#### WO-STATUS-EXPAND-01 — Expanded Status Display

**Risk:** LOW | **Effort:** Small | **Breaks:** 0 expected (additive)

**Problem:** `show_status()` (play.py:343-351) only displays HP and position. Players can't see AC, conditions, saves, BAB, or ability modifiers — all of which exist in entity data.

**Current display:**
```
  Aldric                HP 28/28  (3,3)
```

**Target display:**
```
  Aldric                HP 28/28  AC 18  BAB +3  (3,3)
  Elara                 HP 21/21  AC 17  BAB +2  (2,3)  [Cleric]
  Goblin Warrior        HP 5/5    AC 15  BAB +1  (3,5)  *prone*
```

**Scope:**
- Add AC to status line
- Add BAB to status line
- Show active conditions in status (if any, appended as `*condition*`)
- Keep display compact — one line per entity
- ~5 new tests

**Files:**
- `play.py` (modify `show_status`, lines 343-351)
- `tests/test_play_cli.py` (add status display tests)

**Regression Watch:**
- `test_status_produces_output` asserts `"HP" in output` — still true
- Transcript tests will see wider lines — may need update

**Acceptance:** AC and BAB visible in status. Conditions shown when present. Existing status tests pass.

---

#### WO-AOO-DISPLAY-01 — Attacks of Opportunity Display

**Risk:** LOW | **Effort:** Micro | **Breaks:** 0 expected

**Problem:** AoOs fire automatically via `play_loop.py:935-976` during movement but events are silently dropped by `format_events()`. Player sees movement but not the reactive attacks.

**Scope:**
- Add `aoo_triggered` event handling in `format_events()`:
  - `"Goblin Warrior makes an attack of opportunity against Aldric!"`
- Add `aoo_avoided_by_tumble` display:
  - `"Aldric tumbles past (Tumble DC 15: rolled 18 — success!)"`
- AoO attack/damage events already render as `attack_roll` + `damage_roll` — no change needed there
- ~4 new tests

**Files:**
- `play.py` (modify `format_events`, lines 263-340)
- `tests/test_play_cli.py` (add AoO display tests)

**Acceptance:** AoO triggers visible in combat output. Tumble avoidance shown. Existing tests pass.

---

#### WO-VOICE-SIGNAL-01 — Report-Ready Audio Signal

**Risk:** LOW | **Effort:** Small | **Breaks:** 0 expected

**Problem:** The voice pipeline (`scripts/speak.py`, Arbor profile, Chatterbox backend) shipped at 7c09f58 and can speak arbitrary text on demand. But there is no automated routing — when an agent posts a completion report or dispatch package, Thunder gets no audible cue. The operator must visually scan for state changes.

**Spec Origin:** Thunder-defined signal format:
```
=== SIGNAL: REPORT_READY ===
WO-XXXX — Completion Report
Status: GREEN

<report body follows>
```

**Scope:**
1. **Signal parser** in `scripts/speak.py`:
   - New function `parse_signal(text: str) -> Optional[dict]` — detects leading `=== SIGNAL: REPORT_READY ===` line
   - Extracts first non-empty line after banner as spoken summary
   - Returns `{"signal_type": "REPORT_READY", "summary": "...", "body": "..."}`
   - Returns `None` if no signal line found

2. **Attention chime**:
   - Deterministic tone synthesis: 440Hz sine, 200ms, 16-bit PCM, 24kHz — generated at runtime via `struct.pack`, no external deps
   - New function `_generate_chime() -> bytes` returning WAV bytes
   - Played before spoken summary via `_play_wav()`

3. **Signal-aware speak mode**:
   - New CLI flag: `--signal` — reads stdin, parses for signal line, plays chime + speaks summary
   - New CLI flag: `--full` — with `--signal`, also speaks the full body after summary
   - Without `--signal`, behavior unchanged (backward compatible)
   - Pipeline: detect signal → play chime → speak summary via Arbor → optionally speak body

4. **Agent-triggered invocation** (primary path):
   - On WO completion, the executing agent pipes the signal block to `speak.py --signal` via a Bash call
   - No file watchers, no intermediate drop paths, no VS Code tasks required
   - The agent already has shell access — one `Bash` call at the end of the completion report
   - Example: `echo "=== SIGNAL: REPORT_READY ===\nWO-CONDFIX-01 complete. All tests pass." | python scripts/speak.py --signal`

5. **Standing ops rule** (added to STANDING_OPS_CONTRACT.md):
   - New universal rule: "On WO completion, the executing agent calls `python scripts/speak.py --signal` with the signal block piped to stdin. Signal triggers only for completion reports, dispatch packages, or CP approvals — not routine messages."

**Files:**
- `scripts/speak.py` (add `parse_signal()`, `_generate_chime()`, `--signal`/`--full` flags)
- `docs/ops/STANDING_OPS_CONTRACT.md` (add voice signal rule to Universal Rules)
- `pm_inbox/aegis_rehydration/STANDING_OPS_CONTRACT.md` (sync rehydration copy)
- `tests/test_speak_signal.py` (new — ~6 tests: parser, chime generation, CLI flag routing)

**Key Constraints:**
- No frozen contracts touched
- No engine logic modified
- Chime is pure math (sine wave synthesis) — no asset files needed
- Backward compatible: existing `speak.py "text"` usage unchanged
- Signal format is parse-only — agents adopt the `=== SIGNAL:` header convention voluntarily

**Signal Usage Rules (for agents):**
- Use only for completion reports, dispatch packages, or CP approvals
- Do not use for routine chatter or minor clarifications
- Keep first spoken line to one sentence max
- Agent calls speak.py directly — no operator action needed to hear the signal

**Acceptance:** Agent Bash call `echo "=== SIGNAL: REPORT_READY ===\nWO-CONDFIX-01 complete. All tests pass." | python scripts/speak.py --signal` plays chime then speaks summary. Parser returns None for text without signal line. Existing speak.py usage unchanged. Standing ops rule documented.

---

### Wave C: Game Feel (After Waves A+B)

#### WO-SPELLSLOTS-01 — Spell Slot Tracking

**Risk:** HIGH | **Effort:** Large | **Breaks:** 26+ tests (fixture cascade)

**BLOCKING: Requires CP for entity_fields.py (frozen contract)**

Carried forward from Phase 4B. See `PHASE4B_HANDOVER_PACKET.md` for full spec.

**CP Requirements:**
- Add `EF.SPELL_SLOTS` constant to `entity_fields.py`
- Add `EF.CASTER_LEVEL` constant to `entity_fields.py`
- Design rationale, breaking change assessment, migration path, test plan

**Mitigation:** Make slot validation OPTIONAL — only check `if EF.SPELL_SLOTS in entity`. Tests without slots continue to work.

**Acceptance:** Spell slots displayed. Casting depletes slots. Zero-slot rejection works.

---

#### WO-SPELLLIST-CLI-01 — Show Available Spells

**Risk:** LOW | **Effort:** Small | **Breaks:** 0 expected
**Depends on:** WO-SPELLSLOTS-01 (for slot counts, but can show spell names without)

**Problem:** Players don't know what spells their casters can cast. No `spells` command exists.

**Scope:**
- Add `"spells"` or `"spellbook"` command to `parse_input()`
- Display known spells per caster (hardcoded for Elara: Cure Light Wounds, Shield of Faith, Bless, etc.)
- If spell slots exist (post-SPELLSLOTS), show remaining slots per level
- ~4 new tests

**Files:**
- `play.py` (modify `parse_input`, add `show_spells()`, update `_HELP_TEXT`)
- `tests/test_play_cli.py` (add spell list tests)

**Acceptance:** `spells` command shows available spells. Slot counts shown if available.

---

#### WO-CHARSHEET-CLI-01 — Character Sheet Command

**Risk:** LOW | **Effort:** Small | **Breaks:** 0 expected

**Problem:** No way to inspect detailed character data — ability scores, saves, feats, skills, DR, SR. All data exists in entity dicts but is invisible.

**Scope:**
- Add `"sheet <name>"` or `"inspect <name>"` command
- Display: Name, HP, AC, BAB, ability mods (STR/DEX/CON/WIS/INT/CHA), saves (Fort/Ref/Will), conditions, position, weapon, size
- Show DR/SR if present
- ~5 new tests

**Files:**
- `play.py` (modify `parse_input`, add `show_character_sheet()`, update `_HELP_TEXT`)
- `tests/test_play_cli.py` (add character sheet tests)

**Acceptance:** `sheet aldric` shows full stat block. All entity fields displayed if present.

---

## Sequencing Diagram

```
WAVE A (Sequential — must complete in order)
  WO-CONDFIX-01 (micro, ~4 test updates)
      |
      v
  WO-ROUND-TRACK-01 (small, ~2 transcript test updates)

WAVE B (Parallel-safe after Wave A)
  WO-FULLATTACK-CLI-01   (medium, 0 breaks, ~8 new tests)
  WO-MANEUVER-CLI-01     (medium, 0 breaks, ~12 new tests)
  WO-STATUS-EXPAND-01    (small, 0 breaks, ~5 new tests)
  WO-AOO-DISPLAY-01      (micro, 0 breaks, ~4 new tests)
  WO-VOICE-SIGNAL-01     (small, 0 breaks, ~6 new tests)  [scripts/ only]

WAVE C (After Waves A+B, sequential)
  [CP for entity_fields.py — PO approval required]
      |
      v
  WO-SPELLSLOTS-01       (large, ~15 test updates)
      |
      v
  WO-SPELLLIST-CLI-01    (small, 0 breaks)
  WO-CHARSHEET-CLI-01    (small, 0 breaks)
```

---

## Risk Summary

| WO | Risk | Test Updates | New Tests | Frozen Contract |
|---|---|---|---|---|
| WO-CONDFIX-01 | MEDIUM | ~4 | 0 | No |
| WO-ROUND-TRACK-01 | LOW | ~2 (transcript) | ~5 | No |
| WO-FULLATTACK-CLI-01 | LOW | 0 | ~8 | No |
| WO-MANEUVER-CLI-01 | LOW | 0 | ~12 | No |
| WO-STATUS-EXPAND-01 | LOW | 0 | ~5 | No |
| WO-AOO-DISPLAY-01 | LOW | 0 | ~4 | No |
| WO-VOICE-SIGNAL-01 | LOW | 0 | ~6 | No |
| WO-SPELLSLOTS-01 | HIGH | ~15 | ~10 | **YES** (entity_fields.py) |
| WO-SPELLLIST-CLI-01 | LOW | 0 | ~4 | No |
| WO-CHARSHEET-CLI-01 | LOW | 0 | ~5 | No |

**Total new tests:** ~59
**Total test updates:** ~21
**Frozen contract changes:** 1 (WO-SPELLSLOTS-01 only)

---

## Post-Package State

After all 10 WOs, the CLI will expose:
- Single attack, full attack, 6 combat maneuvers
- Movement with visible AoO consequences
- Spellcasting with slot tracking and spell list
- Round tracking with clear turn boundaries
- Expanded status with AC, BAB, conditions
- Character sheet inspection
- Condition modifiers actually affecting combat
- Audio signal on completion reports (chime + spoken summary via Arbor)

Phase 4 remaining after this package:
- WO-OSS-DICE-001 (Three.js dice roller — needs PO amendments)
- Human playtest round 2 (with full feature set)
- Enemy AI enhancement (currently attacks only, could use maneuvers)

---

## Dispatch Recommendation

**Immediate (Wave A):** Dispatch WO-CONDFIX-01 now. Foundation fix, unblocks condition-dependent features.

**Parallel (Wave B):** After Wave A completes, all 5 Wave B WOs can be dispatched to separate agents simultaneously (non-overlapping file ownership: play.py parser, play.py display, play.py status, play.py events, scripts/speak.py).

**Deferred (Wave C):** Begin CP drafting for entity_fields.py in parallel with Wave B execution.
