# WO-ENGINE-RETRY-001 — Exploration Time Model + Retry Policy

**Issued:** 2026-02-25
**Lifecycle:** DISPATCH-READY
**Track:** Engine
**Priority:** CRITICAL — closes Priority 1 exploit (retry farming collapses all DCs)
**WO type:** FEATURE (new system — schema + engine integration)
**Seat:** Builder

**Closes:** FINDING-ENGINE-RETRY-FARM-001
**Blocks nothing** — self-contained new system, no existing behavior changed

---

## 0. Section 0 — Doctrine Hard Stops

This is an engine WO. UI doctrine does not apply. Engine doctrine applies:

- **No code outside the stated integration points.** Builder adds `game_clock` to WorldState and wires the retry policy into the skill check path. Nothing else.
- **Two-pass design required for any loop that calls a resolver mid-iteration.** (ARCH-TICK-001)
- **Event constructor signature:** `Event(event_id=..., event_type=..., payload=...)` — NOT `id=`, `type=`, `data=`. Include `event_log.py` in context.
- **Class feature detection:** `entity.get(EF.CLASS_LEVELS, {}).get("class_name", 0)` — NOT `EF.CLASS_FEATURES`.
- **Gate test required:** Builder writes a new gate file `tests/test_engine_retry_policy.py` with ≥12 tests.

---

## 1. Target Lock

The retry farming exploit: no retry policy exists. Every rephrased skill check is a fresh roll. Infinite retries collapse every DC to certainty with zero cost.

**Fix:** Add a coarse exploration clock to WorldState. Every non-combat skill check costs time. The retry policy uses a context fingerprint — same actor + same skill + same target + same circumstances + no time advanced → same outcome (cached result returned, no new roll). New roll requires material state change.

**Ruling (locked 2026-02-25):**
1. Take 10: allowed outside combat when actor is not threatened/distracted. Default for routine tasks.
2. Take 20: allowed when failure has no consequence AND time is available. Costs 20× the action's `time_cost`.
3. Retry gate: new roll requires one of: time advanced ≥ `time_cost`, target state changed, actor state changed, new method/tools/assistance, environment changed. None changed → return cached outcome.

---

## 2. Binary Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Time scale for exploration | `TimeScale.EXPLORATION` (existing enum) | Already defined in `aidm/schemas/time.py` |
| Time unit for skill checks | Seconds (use `TimeSpan`) | Schema already handles this |
| Cache storage location | `WorldState.skill_check_cache` (new dict field) | Survives between calls within a session |
| Cache key structure | `(actor_id, skill_name, target_id_or_None, method_tag)` | Deterministic, covers material-change cases |
| Take 10 path | Return `10 + skill_modifier` without rolling | Correct RAW behavior |
| Take 20 path | Advance clock by 20× `time_cost`, return best possible result | Correct RAW behavior |
| Unknown skill `time_cost` | Default 60 seconds (1 minute) | Conservative, always safe |

---

## 3. Contract Spec

### 3.1 WorldState changes (`aidm/core/state.py`)

Add two new optional fields to `WorldState`:

```python
game_clock: Optional["GameClock"] = field(default=None)
skill_check_cache: Dict[str, Any] = field(default_factory=dict)
```

- `game_clock`: instance of `GameClock` from `aidm/schemas/time.py`. `None` in combat (clock is tracked by round counter during combat). Initialized to `GameClock(t_seconds=0, scale="exploration")` on session start outside combat.
- `skill_check_cache`: dict keyed by cache key string (see Section 3.3). Stores `{"outcome": bool, "roll": int, "dc": int, "t_seconds_at_check": int}`.
- Both fields excluded from `state_hash()` — cache and clock are session state, not canonical replay state.
- Both fields serialized in `to_dict()` / `from_dict()` for session persistence.

### 3.2 Time cost table (new module `aidm/core/exploration_time.py`)

```python
SKILL_TIME_COSTS: Dict[str, int] = {
    "search": 60,          # 1 minute
    "disable_device": 60,  # 1 minute
    "open_lock": 60,       # 1 minute
    "climb": 6,            # 1 round (single attempt)
    "swim": 6,
    "jump": 6,
    "balance": 6,
    "tumble": 6,
    "hide": 6,
    "move_silently": 6,
    "knowledge": 60,       # 1 minute (study/recall)
    "spellcraft": 6,       # 1 round (identify)
    "decipher_script": 600, # 10 minutes
    "forgery": 600,
    "craft": 3600,         # 1 hour (minimum)
    "bluff": 6,
    "diplomacy": 60,
    "intimidate": 6,
    "sense_motive": 60,
    "gather_information": 3600,  # 1 hour
    "default": 60,
}

def get_time_cost(skill_name: str) -> int:
    """Return time cost in seconds for a skill check attempt."""
    return SKILL_TIME_COSTS.get(skill_name.lower(), SKILL_TIME_COSTS["default"])
```

### 3.3 Cache key function

```python
def make_check_key(actor_id: str, skill_name: str, target_id: Optional[str], method_tag: str) -> str:
    """
    Deterministic cache key for a skill check context.
    method_tag: short string describing tools/approach (e.g., "bare_hands", "thieves_tools", "aided")
    """
    return f"{actor_id}|{skill_name.lower()}|{target_id or '_'}|{method_tag}"
```

### 3.4 Retry policy function (new module `aidm/core/retry_policy.py`)

```python
def evaluate_check(
    world_state: WorldState,
    actor_id: str,
    skill_name: str,
    dc: int,
    modifier: int,
    target_id: Optional[str],
    method_tag: str,
    take_10: bool,
    take_20: bool,
    rng,
) -> Tuple[bool, int, WorldState, List[Event]]:
    """
    Evaluate a skill check with retry policy enforcement.

    Returns: (success, roll_used, updated_world_state, events)
    Roll_used is 10 for Take 10, best possible for Take 20, or actual d20 roll.
    """
```

**Logic:**
1. If `take_20`:
   - Check eligibility: actor not in combat (`world_state.active_combat is None`), failure has no consequence (caller asserts via flag).
   - Advance `game_clock` by 20 × `get_time_cost(skill_name)` seconds.
   - Emit `TimeAdvanceEvent(delta=..., reason=f"take_20:{skill_name}", scale="exploration")`.
   - Return `(True, 20 + modifier, updated_ws, events)` if `20 + modifier >= dc` else `(False, 20 + modifier, updated_ws, events)`.
   - Do NOT cache Take 20 result (it's authoritative).

2. If `take_10`:
   - Check eligibility: actor not in combat AND not threatened/distracted (caller asserts).
   - Advance clock by `get_time_cost(skill_name)` seconds.
   - Emit `TimeAdvanceEvent`.
   - Return `(10 + modifier >= dc, 10, updated_ws, events)`.
   - Do NOT cache.

3. Normal roll (neither Take 10 nor Take 20):
   - Build cache key.
   - If key in `world_state.skill_check_cache`:
     - Compare `t_seconds_at_check` to current `game_clock.t_seconds`. If clock has NOT advanced by at least `get_time_cost(skill_name)` since the cached check → return cached outcome (no new roll, no time cost, emit `skill_check_cached` event with reason).
   - Roll d20. Advance clock by `get_time_cost(skill_name)`.
   - Store result in cache.
   - Emit `skill_check_rolled` event + `TimeAdvanceEvent`.
   - Return result.

### 3.5 Events to emit

All via `Event(event_id=..., event_type=..., payload=...)`:

- `skill_check_rolled`: `{"actor_id", "skill", "roll", "modifier", "dc", "success", "t_seconds"}`
- `skill_check_cached`: `{"actor_id", "skill", "cached_roll", "dc", "success", "reason": "no_state_change"}`
- `skill_check_take_10`: `{"actor_id", "skill", "result", "dc", "success"}`
- `skill_check_take_20`: `{"actor_id", "skill", "result", "dc", "success", "time_spent_seconds"}`
- `time_advanced`: wraps `TimeAdvanceEvent` payload

### 3.6 Per-skill retry rules (PHB p.65)

Builder must also add `RETRY_ALLOWED` dict to `exploration_time.py`:

```python
RETRY_ALLOWED: Dict[str, bool] = {
    "climb": True,
    "swim": True,
    "jump": True,
    "open_lock": True,
    "disable_device": True,   # not same round
    "bluff": True,            # target gets +10 on subsequent checks
    "diplomacy": True,        # each failure worsens attitude
    "knowledge": False,       # you know it or you don't
    "spellcraft": False,      # one attempt per spell
    "default": True,          # conservative default
}
```

For skills where `RETRY_ALLOWED = False`: a failed check is permanently cached until state changes. No retry even with time elapsed unless method changes.

---

## 4. Implementation Plan

1. **`aidm/schemas/time.py`** — no changes needed (already correct)
2. **`aidm/core/state.py`** — add `game_clock` and `skill_check_cache` fields to `WorldState`; update `to_dict`/`from_dict`; exclude from `state_hash()`
3. **`aidm/core/exploration_time.py`** — NEW FILE: `SKILL_TIME_COSTS`, `RETRY_ALLOWED`, `get_time_cost()`, `make_check_key()`
4. **`aidm/core/retry_policy.py`** — NEW FILE: `evaluate_check()` function
5. **`aidm/core/play_loop.py`** — wire `evaluate_check()` into skill check resolution path; initialize `game_clock` when entering exploration mode
6. **`tests/test_engine_retry_policy.py`** — NEW FILE: ≥12 tests covering Take 10, Take 20, cache hit, cache miss, retry on state change, retry blocked on no state change, per-skill retry rules, time advancement, events emitted

---

## 5. Integration Seams

- `aidm/core/state.py`: `WorldState` dataclass — add two fields
- `aidm/schemas/time.py`: `GameClock`, `TimeSpan`, `TimeAdvanceEvent`, `TimeScale` — import, do not modify
- `aidm/core/event_log.py`: `Event(event_id=..., event_type=..., payload=...)` — use this constructor, no other
- `aidm/core/play_loop.py`: skill check resolution path — exact entry point TBD by builder from code read

---

## 6. Assumptions to Validate

- Confirm: `aidm/schemas/time.py` `GameClock` is importable and correct as-is (no changes needed)
- Confirm: `WorldState.state_hash()` can safely exclude `game_clock` and `skill_check_cache` (these are session state, not replay-canonical)
- Confirm: current skill check call site in `play_loop.py` — find where d20 is rolled for skill checks and wire `evaluate_check()` there
- Confirm: `active_combat is None` is the correct check for "outside combat" (vs. checking a flag)

---

## 7. Preflight

Before writing code:
- [ ] Read `aidm/core/state.py` in full
- [ ] Read `aidm/schemas/time.py` in full
- [ ] Read `aidm/core/event_log.py` for Event constructor
- [ ] Find skill check call site in `play_loop.py` (grep for `skill` + `d20` + `modifier`)
- [ ] Confirm `ARCH-TICK-001` two-pass design is not needed here (retry policy is not a loop over entities)

---

## 8. Debrief Required

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-RETRY-001.md`

**Pass 1 (full context dump):**
- Files modified and created (list each with line count delta)
- `game_clock` field location in WorldState
- `skill_check_cache` key format confirmed
- Take 10/Take 20 eligibility checks implemented where
- Cache hit/miss logic line citations
- Per-skill retry table location
- `TimeAdvanceEvent` emission confirmed

**Pass 2 (PM summary ≤100 words):**
- What was implemented, what was deferred, what was discovered

**Pass 3 (retrospective):**
- Drift caught (if any)
- Patterns observed
- Recommendations

**Radar (mandatory):**
- Gate test count: __ / 12 minimum
- Integration seams confirmed: state.py / time.py / event_log.py / play_loop.py
- No stale DISPATCH-READY lifecycle in WO file

Missing debrief or missing Radar → REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
