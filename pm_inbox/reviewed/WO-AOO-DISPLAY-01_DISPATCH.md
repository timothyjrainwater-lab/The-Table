# WO-AOO-DISPLAY-01 — Attacks of Opportunity Display

**Dispatch Authority:** PM (Opus)
**Priority:** Wave B — parallel dispatch (after Wave A completes)
**Risk:** LOW | **Effort:** Micro | **Breaks:** 0 expected
**Depends on:** Wave A complete

---

## Target Lock

AoOs fire automatically via `play_loop.py:935-976` during movement but events are silently dropped by `format_events()` in play.py. Players see movement but not the reactive attacks.

**Goal:** AoO triggers visible in combat output. Tumble avoidance shown.

---

## Binary Decisions (Locked)

1. **AoO announcement before damage.** `"Goblin Warrior makes an attack of opportunity against Aldric!"` appears before the normal `attack_roll`/`damage_roll` events.
2. **Tumble shown.** `"Aldric tumbles past (Tumble DC 15: rolled 18 — success!)"` for tumble attempts.
3. **Cover block shown.** `"AoO blocked by cover"` when cover prevents the AoO.
4. **No logic changes.** Display-only modification to `format_events()`.

---

## Contract Spec

### File Scope (2 files)

| File | Action | Lines |
|------|--------|-------|
| `play.py` | Modify `format_events()` (lines 263-340) | Add handlers for `aoo_triggered`, `aoo_avoided_by_tumble`, `tumble_check`, `aoo_blocked_by_cover` |
| `tests/test_play_cli.py` | Add ~4 new tests | AoO display assertions |

### Implementation Detail

**AoO event types emitted by `aidm/core/aoo.py`:**
- `aoo_triggered` — payload: `reactor_id`, `provoker_id`, `trigger_reason`
- `tumble_check` — payload: `entity_id`, `success`, `total`, `dc`, `d20_roll`
- `aoo_avoided_by_tumble` — payload: `entity_id`, `reactor_id`
- `aoo_blocked_by_cover` — payload: `reactor_id`, `provoker_id`, `cover_type`

**After** an `aoo_triggered` event, the normal `attack_roll` and `damage_roll` events follow (already displayed).

**Add to `format_events()` (play.py:263-340):**
```python
elif ev.event_type == "aoo_triggered":
    reactor = _name(ws, p.get("reactor_id", ""))
    provoker = _name(ws, p.get("provoker_id", ""))
    lines.append(f"  {reactor} makes an attack of opportunity against {provoker}!")

elif ev.event_type == "tumble_check":
    entity = _name(ws, p.get("entity_id", ""))
    success = p.get("success", False)
    total = p.get("total", 0)
    dc = p.get("dc", 15)
    result_str = "success" if success else "failure"
    lines.append(f"  {entity} attempts to tumble (DC {dc}: rolled {total} — {result_str}!)")

elif ev.event_type == "aoo_avoided_by_tumble":
    entity = _name(ws, p.get("entity_id", ""))
    lines.append(f"  {entity} tumbles past safely!")

elif ev.event_type == "aoo_blocked_by_cover":
    reactor = _name(ws, p.get("reactor_id", ""))
    lines.append(f"  {reactor}'s AoO blocked by cover")
```

### Frozen Contracts

None touched.

---

## Implementation Sequencing

1. Add 4 event type handlers in `format_events()`
2. Add tests:
   - `test_aoo_triggered_display` — mock event renders "attack of opportunity"
   - `test_tumble_check_display` — mock event renders tumble check with DC and result
   - `test_aoo_avoided_display` — mock event renders "tumbles past safely"
   - `test_aoo_blocked_by_cover_display` — mock event renders "blocked by cover"
3. Run full suite

---

## Acceptance Criteria

1. `aoo_triggered` events display in combat output
2. Tumble checks display with DC and success/failure
3. Cover blocks display
4. Existing tests pass
5. ~4 new tests pass

---

## Agent Instructions

- Read `AGENT_ONBOARDING_CHECKLIST.md` and `AGENT_DEVELOPMENT_GUIDELINES.md` before starting
- This WO modifies ONLY `format_events()` in `play.py`. No logic changes, no core engine modifications.
- Test by constructing mock Event objects with the right payload structure (see event types above)
- The `Event` class is at `aidm/schemas/event_log.py` — `Event(event_id=0, event_type="aoo_triggered", timestamp=0.0, payload={...})`
- Run full suite before declaring completion
