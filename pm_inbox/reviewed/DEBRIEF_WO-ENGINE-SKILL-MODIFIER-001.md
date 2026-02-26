# DEBRIEF — WO-ENGINE-SKILL-MODIFIER-001
# Wire Real Skill Modifier in _process_skill()

**Verdict:** ACCEPTED 10/10
**Gate:** ENGINE-SKILL-MODIFIER
**Date:** 2026-02-26
**WO:** WO-ENGINE-SKILL-MODIFIER-001

---

## Pass 1 — Per-File Breakdown

### `aidm/core/state.py`

**Changes made:**
- `game_clock: Optional[Any] = field(default=None, compare=False)` added to `WorldState`
- `skill_check_cache: Dict[str, Any] = field(default_factory=dict, compare=False)` added to `WorldState`
- Both excluded from `state_hash()` by omission (consistent with RETRY-001 design intent)

**Why:** `evaluate_check()` in `retry_policy.py` references `ws.game_clock` and `ws.skill_check_cache`. These fields were missing — the RETRY-001 debrief said they were added but the code did not reflect it. RP-010 was failing as a result. This closes the gap.

### `aidm/core/play_loop.py`

**Changes made:**
- `execute_exploration_skill_check()` appended (~55 lines) before `execute_scenario()`
- Wraps `evaluate_check()` from `retry_policy.py`
- Initializes `game_clock` to `GameClock(t_seconds=0, scale="exploration")` if absent (deep-copies to avoid mutation)
- Re-sequences raw event IDs from `evaluate_check()` (0-based internal) to monotonic from `next_event_id`
- Returns `(success, roll_used, updated_world_state, events)` tuple

**Why:** The RETRY-001 debrief said this function was added at line 3136 of play_loop.py — but it was absent. This closes the gap.

### `aidm/schemas/intents.py`

**Changes made:**
- `SkillCheckIntent` dataclass added (fields: `actor_id`, `skill_name`, `dc=15`, `take_10=False`, `take_20=False`, `target_id=None`, `method_tag="default"`)
- `to_dict()` / `from_dict()` implemented
- Added to `Intent` union type
- `parse_intent()` updated with `elif intent_type == "skill_check":` branch

### `aidm/runtime/session_orchestrator.py`

**Changes made:**

1. **`ParsedCommand` dataclass** — four new fields added (frozen=True respected via defaults):
   - `skill_name: Optional[str] = None`
   - `take_10: bool = False`
   - `take_20: bool = False`
   - `dc: Optional[int] = None`

2. **`_normalize_skill()` module-level helper** added before `parse_text_command()`:
   - Maps player verbs to canonical SKILL_TIME_COSTS keys
   - `"sneak"` → `"move_silently"`, `"disable"` → `"disable_device"`, `"pick lock"` → `"open_lock"`, etc.
   - ~30-entry lookup dict with fallback `verb.lower().replace(" ", "_")`

3. **`parse_text_command()` extended** — three skill branches inserted before `unknown` fallthrough:
   - Take 10: `r"take\s+(?:10|ten)\s+(?:on\s+)?(.+)$"` → `take_10=True`
   - Take 20: `r"take\s+(?:20|twenty)\s+(?:on\s+)?(.+)$"` → `take_20=True`
   - Generic skill verb regex covering 18 canonical skill verbs → `command_type="skill"`

4. **`process_text_turn()` routing** — `elif command.command_type == "skill": return self._process_skill(actor_id, command)` added after `"transition"` branch

5. **`_process_skill()` method** — new method implementing WO-ENGINE-SKILL-MODIFIER-001:
   - Out-of-combat gate: `active_combat is not None` → returns `TurnResult(success=False, ...)` with "combat" in narration (RT2-005)
   - **Inline modifier lookup** (FINDING-ENGINE-SKILL-MODIFIER-001 closed):
     ```python
     from aidm.schemas.skills import SKILLS
     from aidm.core import play_loop as _pl_module
     _entity = self._world_state.entities.get(actor_id, {})
     _skill_def = SKILLS.get(skill_name)
     if _skill_def is not None:
         _ability_map = {
             "str": EF.STR_MOD, "dex": EF.DEX_MOD, "con": EF.CON_MOD,
             "int": EF.INT_MOD, "wis": EF.WIS_MOD, "cha": EF.CHA_MOD,
         }
         _ability_mod = _entity.get(_ability_map.get(_skill_def.key_ability, ""), 0)
         _ranks = _entity.get(EF.SKILL_RANKS, {}).get(skill_name, 0)
         _acp = _entity.get(EF.ARMOR_CHECK_PENALTY, 0) if _skill_def.armor_check_penalty else 0
         modifier = _ability_mod + _ranks - _acp
     else:
         modifier = 0  # skill not in registry — fail soft
     ```
   - Calls `_pl_module.execute_exploration_skill_check(...)` via module reference (not direct import) — enables test spy patching on `_pl.execute_exploration_skill_check`
   - Returns `TurnResult` with `events` as tuple of dicts (matches `frozen=True` `TurnResult.events: Tuple`)

**Modifier formula confirmed:** `ability_mod + ranks − acp` (acp=0 for non-ACP-affected skills)

**Fallback on missing entity:** `entities.get(actor_id, {})` returns empty dict → all field lookups return 0 → modifier=0 (SM-006)

**Fallback on missing skill:** `SKILLS.get(skill_name)` returns None → else branch → modifier=0 (SM-005)

**FINDING-ENGINE-SKILL-MODIFIER-001:** CLOSED.

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-SKILL-MODIFIER-001 ACCEPTED 10/10. Closes FINDING-ENGINE-SKILL-MODIFIER-001. Also filled RETRY-001 infrastructure gaps: `game_clock`/`skill_check_cache` on WorldState, `execute_exploration_skill_check()` in play_loop. Delivered RETRY-002 wiring: `SkillCheckIntent`, `ParsedCommand` skill fields, `_normalize_skill()`, `_process_skill()`. Modifier formula `ability_mod + ranks − ACP` inline; no private helper imports. Graceful 0 on missing entity/skill. RT2 11/11, RP 14/14, SM 8/8. No new regressions (446 pass; 1 pre-existing gold master drift from prior WO).

---

## Pass 3 — Retrospective

**Preflight revealed RETRY-001 was partially undelivered.** `WorldState` lacked `game_clock`/`skill_check_cache`, `execute_exploration_skill_check()` was absent from play_loop, and `_process_skill()` didn't exist in session_orchestrator. The prior debrief said "FILED" not "ACCEPTED" — this WO completed all three prerequisite layers before the SM-001 modifier lookup could be validated.

**Module reference pattern required for test isolation.** `_pl_module.execute_exploration_skill_check()` via `from aidm.core import play_loop as _pl_module` (local import) allows test patches on `_pl.execute_exploration_skill_check` to intercept the call. A top-level `from aidm.core.play_loop import execute_exploration_skill_check` would bind the name at import time and defeat patching. The SM test suite uses this patch pattern — this is why all 8 SM tests returned `None` initially (spy not invoked) and passed after switching to module-attribute lookup.

**Inline vs helper is correct at this call site.** Three lines, one call site. `skill_resolver.py` private helpers exist but are intentionally private. The duplication is the right trade-off here.

**Gold master drift is pre-existing.** `test_replay_tavern_gold_master` drifts on `payload.twd_ac_bonus` (expected None, actual 0) — field added by WO-ENGINE-DEFEND-001; gold master not regenerated. Predates this session entirely.

**Radar:**
- RT2-001–011: PASS (11/11)
- RP-001–014: PASS (14/14)
- SM-001–008: PASS (8/8)
- `modifier = 0` placeholder removed: CONFIRMED
- SKILLS registry import live (local import in `_process_skill`): CONFIRMED
- Formula: ability_mod + skill_ranks − ACP: CONFIRMED
- Fallback on missing skill: CONFIRMED (SM-005)
- Fallback on missing entity: CONFIRMED (SM-006)
- No ACP applied to non-ACP skills: CONFIRMED (SM-008)
- `game_clock` + `skill_check_cache` on WorldState: CONFIRMED
- `execute_exploration_skill_check()` in play_loop: CONFIRMED
- `SkillCheckIntent` in intents.py: CONFIRMED
- FINDING-ENGINE-SKILL-MODIFIER-001: CLOSED

---

*Debrief filed by builder on 2026-02-26.*
