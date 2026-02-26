# WO-ENGINE-RETRY-002 — Skill Check Intent Dispatch
## Status: DISPATCH-READY
## Priority: MEDIUM
## Closes: FINDING-ENGINE-RETRY-FARM-001 (full close — infrastructure was RETRY-001; wiring is RETRY-002)

---

## Context

WO-ENGINE-RETRY-001 (ACCEPTED) delivered:
- `aidm/core/exploration_time.py` — time costs, retry rules, cache key
- `aidm/core/retry_policy.py` — `evaluate_check()` full implementation
- `aidm/core/state.py` — `game_clock` + `skill_check_cache` on `WorldState`
- `aidm/core/play_loop.py:3136` — `execute_exploration_skill_check()` wrapper (calls `evaluate_check()`, re-sequences event IDs)
- Gate: RP-001–014 (14/14)

The RETRY-001 debrief flagged that `execute_exploration_skill_check()` is defined but never called — no `SkillCheckIntent` exists, no `parse_text_command()` branch handles "search", and no `process_text_turn()` handler routes to the function. This WO closes that gap.

**Do NOT modify `evaluate_check()` or `execute_exploration_skill_check()`.** Those are complete and tested. This WO is three targeted additions: intent class, parser branch, orchestrator handler.

---

## Section 0 — Assumptions to Validate (read before coding)

1. Read `aidm/schemas/intents.py` — confirm `SkillCheckIntent` does NOT already exist
2. Read `aidm/runtime/session_orchestrator.py` lines 179–273 (`parse_text_command()`) — confirm no "search"/"skill" branch exists
3. Read `aidm/runtime/session_orchestrator.py` lines 455–520 (`process_text_turn()`) — confirm where the skill check handler should slot in relative to attack/spell/move
4. Read `aidm/core/play_loop.py` lines 3136–3221 (`execute_exploration_skill_check()`) — confirm current signature
5. Read `aidm/core/skill_resolver.py` — confirm `resolve_skill_check()` signature and what modifiers it computes; WO-ENGINE-RETRY-001 debrief says `evaluate_check()` wraps this path — verify this is true or document actual modifier computation path

**Preflight gate:** Run `python -m pytest tests/test_engine_retry_policy_gate.py -v` — must be 14/14 before any change.

---

## Section 1 — Target Lock

Wire the exploration skill check infrastructure to the player intent pipeline. After this WO:
- A player utterance like `"search for traps"` produces a `SkillCheckIntent`
- `process_text_turn()` detects `SkillCheckIntent` and routes to `execute_exploration_skill_check()`
- The retry policy (cache hit, time cost, Take 10/20 flags) is exercised on every out-of-combat skill attempt
- The `TurnResult` returned to the WS bridge carries the retry events (`skill_check_rolled`, `skill_check_cached`, `time_advanced`)

---

## Section 2 — Binary Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Modifier computation | Read from entity dict in orchestrator | `resolve_skill_check()` may require entity context that `process_text_turn()` already holds. Builder must verify. |
| DC source | Caller-provided or hard-coded default (DC 15) | DM hasn't set DCs yet in text-command mode. Use a default DC=15; DC override is future WO scope. |
| Take 10/Take 20 flags | Derive from keywords in utterance | "take 10", "take ten", "carefully" → `take_10=True`. "take 20", "take twenty" → `take_20=True`. Default False. |
| method_tag | Derive from parsed utterance or default "default" | Simple default "default" for now. Future WO can expand to tool detection. |
| Out-of-combat gate | Check `world_state.active_combat is None` | Take 10 / Take 20 only if not in combat. If in combat, route to `execute_turn()` or return clarification. |

---

## Section 3 — Contract Spec

### New: `SkillCheckIntent` in `aidm/schemas/intents.py`

```python
@dataclass
class SkillCheckIntent:
    """Intent for an out-of-combat exploration skill check.

    WO-ENGINE-RETRY-002: routed through execute_exploration_skill_check()
    which enforces retry policy via evaluate_check().
    """
    actor_id: str
    skill_name: str           # e.g., "search", "disable_device"
    dc: int = 15              # default DC — caller may override
    take_10: bool = False
    take_20: bool = False
    target_id: Optional[str] = None
    method_tag: str = "default"
```

### Modified: `parse_text_command()` in `session_orchestrator.py`

Add a skill branch that recognizes:
- `"search [for] [object]"` → `ParsedCommand(command_type="skill", skill_name="search")`
- `"listen [for] ..."` → `ParsedCommand(command_type="skill", skill_name="listen")`
- `"disable [the] [device/trap]"` / `"pick [the] lock"` → appropriate skill_name
- `"take 10 [on] [skill]"` / `"take 20 [on] [skill]"` → `take_10=True` / `take_20=True`

Minimum recognized skills (align with `SKILL_TIME_COSTS` keys in `exploration_time.py`): `search`, `disable_device`, `open_lock`, `climb`, `swim`, `jump`, `balance`, `tumble`, `hide`, `move_silently`, `listen`, `bluff`, `diplomacy`, `intimidate`, `sense_motive`, `gather_information`, `knowledge`, `spellcraft`.

`ParsedCommand` already has a `command_type` field. Builder should add `skill_name: Optional[str] = None` and `take_10: bool = False`, `take_20: bool = False` to the `ParsedCommand` dataclass if not already present.

### Modified: `process_text_turn()` in `session_orchestrator.py`

Add a branch after the existing command routing:
```python
elif command.command_type == "skill":
    # Exploration skill check — requires out-of-combat context
    if self._world_state.active_combat is not None:
        return TurnResult(
            success=False,
            narration_text="You cannot use exploration skill checks in combat.",
            clarification_needed=False,
        )
    # Compute modifier from entity (ability mod + ranks — builder must verify path)
    modifier = 0  # placeholder — builder replaces with actual modifier lookup
    success, roll_used, updated_ws, events = execute_exploration_skill_check(
        world_state=self._world_state,
        actor_id=actor_id,
        skill_name=command.skill_name,
        dc=command.dc or 15,
        modifier=modifier,
        rng=self._rng,
        take_10=command.take_10,
        take_20=command.take_20,
        next_event_id=self._next_event_id(),
    )
    self._world_state = updated_ws
    # Build narration text from result
    outcome = "succeeded" if success else "failed"
    narration_text = f"{'Take 10: ' if command.take_10 else ''}{'Take 20: ' if command.take_20 else ''}{command.skill_name} check {outcome} (rolled {roll_used})."
    return TurnResult(
        success=True,
        narration_text=narration_text,
        events=events,
    )
```

Builder must verify:
- How `process_text_turn()` accesses `self._world_state` or equivalent
- How `self._rng` or equivalent RNG is accessed
- How `_next_event_id()` or equivalent is called
- Correct import of `execute_exploration_skill_check` from `aidm.core.play_loop`

---

## Section 4 — Implementation Plan

1. **Read** `aidm/schemas/intents.py` — add `SkillCheckIntent` dataclass at bottom
2. **Read** `aidm/runtime/session_orchestrator.py` fully — understand `ParsedCommand`, `parse_text_command()`, `process_text_turn()` internal state access patterns
3. **Modify** `ParsedCommand` dataclass — add `skill_name`, `take_10`, `take_20` if not present
4. **Modify** `parse_text_command()` — add skill branch before the `return ParsedCommand(command_type="unknown")` fallthrough
5. **Modify** `process_text_turn()` — add `elif command.command_type == "skill":` handler
6. **Verify** modifier lookup path — read entity dict for skill modifier or use 0 as placeholder (document which)
7. **Run** `python -m pytest tests/test_engine_retry_policy_gate.py -v` — 14/14 must hold
8. **Write** gate test file `tests/test_engine_retry_002_gate.py` — minimum 10 tests:

### Gate test spec (minimum 10)

| ID | Test | Pass condition |
|----|------|----------------|
| RT2-001 | `parse_text_command("search for traps")` | `command_type == "skill"`, `skill_name == "search"` |
| RT2-002 | `parse_text_command("take 10 on search")` | `take_10 == True`, `skill_name == "search"` |
| RT2-003 | `parse_text_command("take 20 on disable device")` | `take_20 == True`, `skill_name == "disable_device"` |
| RT2-004 | `parse_text_command("attack goblin")` | `command_type == "attack"` (regression — skill branch doesn't clobber attack) |
| RT2-005 | Skill check intent in combat → `TurnResult.success == False`, narration contains "combat" |
| RT2-006 | Out-of-combat skill check → `TurnResult.success == True`, events contain `skill_check_rolled` |
| RT2-007 | Repeat same skill check (no time elapsed) → `skill_check_cached` event emitted |
| RT2-008 | Repeat same skill check (time elapsed) → new `skill_check_rolled` event |
| RT2-009 | Knowledge skill → no retry (permanent cache hit after first fail) |
| RT2-010 | Take 10 path → `roll_used == 10`, `time_advanced` event emitted |

---

## Integration Seams

| Component | File | What to import |
|-----------|------|----------------|
| `execute_exploration_skill_check` | `aidm/core/play_loop.py:3136` | Import inside handler or at top of orchestrator |
| `SkillCheckIntent` | `aidm/schemas/intents.py` (new) | Import in orchestrator |
| `WorldState` fields | `game_clock`, `skill_check_cache` on `aidm/core/state.py:WorldState` | Already present — no change |
| `Event` constructor | `aidm/core/event_log.py` | `Event(event_id=, event_type=, timestamp=, payload=)` — NOT `id=, type=, data=` |
| `TurnResult` | `aidm/runtime/session_orchestrator.py` or adjacent | Verify import path — already used in orchestrator |

---

## Debrief Required

**File to:** `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-RETRY-002.md`

**Pass 1 — Context dump:**
- List every file modified with line ranges
- Confirm gate RT2-001–RT2-010 pass counts
- Confirm RETRY-001 gate still 14/14 after changes
- State modifier lookup: what value is passed to `execute_exploration_skill_check()` for `modifier` (0 placeholder or real value)
- State where `SkillCheckIntent` is imported in orchestrator
- Document `ParsedCommand` fields added

**Pass 2 — PM summary ≤100 words**

**Pass 3 — Retrospective:**
- Drift from spec (if any)
- Modifier placeholder: if 0 is used, flag as FINDING-ENGINE-SKILL-MODIFIER-001 for future WO
- Recommend next WO if gaps remain

**Radar (one line each):**
- RP-001–014: still PASS after changes
- RT2-001–010: all PASS
- SkillCheckIntent added to intents.py: CONFIRMED
- skill branch in parse_text_command: PRESENT
- skill handler in process_text_turn: PRESENT
- out-of-combat gate: PRESENT
- Modifier source: DOCUMENTED

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Drafted: 2026-02-25 — Slate*
