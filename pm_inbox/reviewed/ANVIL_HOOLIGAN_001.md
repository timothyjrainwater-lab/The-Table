# ANVIL_HOOLIGAN_001 — Engine Smoke + Hooligan Protocol Run
**Filed:** 2026-02-25
**WO:** WO-ANVIL-HOOLIGAN-001
**Auditor:** Anvil (execution + triage)
**Type:** EXECUTION + TRIAGE — no code changes
**Blocks:** WO-SEC-REDACT-001

---

## Section 1 — Run Summary

**Date:** 2026-02-25
**Commit:** 05f65ba (DIRTY — 27 tracked files modified, in-progress WO edits)
**Branch:** master
**Python:** 3.11.1 (Windows)

### verify_session_start.py
**Status: RED** — dirty working tree (expected; WOs in progress). Bootstrap shows 27 modified/deleted tracked files. The collection failure (rc=2) is a pre-existing import error in `tests/test_heuristics_image_critic.py`, not a new failure.

### Gate baseline before run
pytest with `--ignore=tests/test_heuristics_image_critic.py`:
- **28 failures** (pre-existing)
- **7734 passing**
- **44 skipped**

### Gate baseline after run
**28 failures. 0 new failures introduced.** Matches baseline exactly.

---

## Section 2 — Hooligan Results Table

### Phase 1 — Regression (14/14 PASS)
All original fireball pipeline stages pass. Gap verification: 2/4 CONFIRMED (content_id on Fireball and damage_type flow are NOT CONFIRMED — pre-existing open gaps).

### Phase 2 — Manual Scenarios (7/7 PASS)
Scenarios B through W all pass. One finding logged outside Hooligan: healing spell (CLW on living target) emits no `hp_changed` event — healing resolver non-functional.

### Phase 3 — Hooligan Protocol (12 scenarios)

| ID | Tier | Verdict | Detail |
|----|------|---------|--------|
| H-001 | B | **FINDING** | No `ReadyIntent`/resolver — ready actions not modeled |
| H-002 | B | PASS | Engine correctly denied grapple on non-entity `"wall_of_fire"` |
| H-003 | A | **FINDING** | Caster at AoE center NOT in `affected_entities` — rasterizer excludes origin square |
| H-004 | A | PASS | Engine correctly denied attack on defeated entity |
| H-005 | B | PASS | `DelayIntent` exists in engine |
| H-006 | B | **FINDING** | No `DropItemIntent`/`UnequipIntent` — equipment management not modeled |
| H-007 | B | PASS | `ChargeIntent` found |
| H-008 | A | **FINDING** | CLW on undead: no events at all — absent negative-healing resolver |
| H-009 | B | PASS | `CoupDeGraceIntent` found |
| H-010 | A | PASS | 8 buffs cast without crash; 0 conditions applied (pre-existing gap — buffs not emitting condition events) |
| H-011 | A | **FINDING** | No friendly fire — AoE applies allegiance filter, excluding allies from blast |
| H-012 | B | **FINDING** | `weapon_type='improvised'` rejected by schema (`ValueError`) |

**Tier A (must resolve correctly): H-003 FINDING, H-004 PASS, H-008 FINDING, H-010 PASS, H-011 FINDING**
**Tier B (must not crash): H-001 FINDING, H-002 PASS, H-005 PASS, H-006 FINDING, H-007 PASS, H-009 PASS, H-012 FINDING**

**Overall: 6 PASS / 6 FINDING / 0 CRASH**

### Smoke Scoreboard
```
Total stages:    55/55 PASS
Regression:      14/14 PASS
Gap verify:      2/4 CONFIRMED (2 pre-existing)
Hooligan:        6 PASS / 6 FINDING / 0 CRASH
Gate regression: 28 failures (baseline) — 0 new
Crashes:         0
```

---

## Section 3 — Required Gap Confirmations

### GAP-WS-003 — token_add includes hp + hp_max for monster entities
**Status: CONFIRMED**

`_build_token_add_messages()` at `ws_bridge.py:295–303` emits the following fields for all entities with a valid grid position:

```python
messages.append(_make_raw_msg("token_add", {
    "id": entity_id,
    "col": col,
    "row": row,
    "name": entity.get("name", entity_id),
    "faction": entity.get(EF.TEAM, "neutral"),
    "hp": entity.get(EF.HP_CURRENT, 0),      # line 301
    "hp_max": entity.get(EF.HP_MAX, 1),       # line 302
}, in_reply_to))
```

`hp` and `hp_max` are included for ALL entities — both PC and monster. There is no faction filter. Any client connected at session join receives the full HP values for every entity on the map, including monsters. This is the HP disclosure path referenced in the adversarial synthesis (kill chain step 1: passive HP disclosure on join).

**Evidence:** `ws_bridge.py:295–303`

---

### GAP-WS-004 — Passthrough branch emits raw internal delta fields
**Status: CONFIRMED**

An explicit passthrough branch exists at `ws_bridge.py:565–575`:

```python
else:
    # Keep passthrough for unhandled event types
    messages.append(StateUpdate(
        msg_type=MSG_STATE_UPDATE,
        msg_id=_make_msg_id(),
        in_reply_to=in_reply_to,
        timestamp=_now(),
        update_type=event_type,
        entity_id=entity_id,
        delta=tuple(sorted(event_dict.items())),  # ALL raw fields
    ))
```

This triggers for any `event_type` NOT in `{"hp_changed", "entity_defeated", "combat_started", "combat_ended"}`. The entire raw `event_dict` is serialized as a sorted tuple into the `delta` field. This means internal fields including `hp_before`, `hp_after`, `delta` (damage delta), `damage_type`, DC values, and any other engine-internal key–value pairs are passed directly to the client.

The comment at line 566 ("Keep passthrough for unhandled event types") confirms this is intentional scaffolding, not an accident. Any event type the engine emits that isn't explicitly handled in `_turn_result_to_messages()` leaks its full internal dict to every connected client.

**Evidence:** `ws_bridge.py:565–575`

---

### GAP-WS-002 — default_actor_id = "pc_fighter" observable effect
**Status: CONFIRMED (hardcoded) / INCONCLUSIVE (direct log/payload visibility)**

`default_actor_id` is hardcoded to `"pc_fighter"` at `ws_bridge.py:95`. It is used at two call sites:
- `ws_bridge.py:401` — `session.process_text_turn(msg.text, self._default_actor_id)`
- `ws_bridge.py:418` — `session.process_voice_turn(audio_bytes, self._default_actor_id)`

It is **not** visible in any WS message payload — it is passed internally to the session orchestrator and does not appear in log output or any emitted message field.

**Multi-connection exposure:** All connections to the same `WebSocketBridge` instance share the same `default_actor_id`. In a multi-player scenario, every player's utterances are attributed to `"pc_fighter"` regardless of which connection sent them. The effect is observable in `TurnResult` and engine events that carry `actor_id` — e.g., `"actor_id": "pc_fighter"` in emitted events — but only if the client processes those fields. Since the passthrough branch (GAP-WS-004) emits raw event dicts, any event carrying `actor_id` would expose this attribution to all clients.

**Evidence:** `ws_bridge.py:95, 401, 418`

---

## Section 4 — Findings

### HG-F001 — No ReadyIntent Resolver
**Scenario:** H-001 | **Tier:** B | **Severity:** MEDIUM
**Scope:** `aidm/core/play_loop.py`
No `ReadyIntent` class or resolver. Ready actions (PHB p.160) fall through silently.
**PM recommendation:** New board entry. Backlog.

---

### HG-F002 — AoE Rasterizer Excludes Caster Origin Square
**Scenario:** H-003 | **Tier:** A (WRONG RESULT) | **Severity:** HIGH
**Scope:** AoE spell resolver, `aidm/core/play_loop.py`
Caster standing at AoE origin is NOT included in `affected_entities`. PHB p.175 requires origin square occupants to be affected.
**PM recommendation:** New board entry. HIGH — Tier A wrong result. Targeted rasterizer fix WO.

---

### HG-F003 — Equipment Management Not Modeled
**Scenario:** H-006 | **Tier:** B | **Severity:** LOW
**Scope:** `aidm/core/play_loop.py`
No `DropItemIntent` or `UnequipIntent`. PHB p.142 equipment actions not modeled.
**PM recommendation:** New board entry. Backlog.

---

### HG-F004 — CLW on Undead: No Events Emitted
**Scenario:** H-008 | **Tier:** A (WRONG RESULT) | **Severity:** HIGH
**Scope:** Healing resolver, `aidm/core/play_loop.py`
CLW on undead produces no events (should deal damage per PHB p.215-216). Silent drop — no exception.
**PM recommendation:** New board entry. HIGH — Tier A wrong result. Healing resolver needs undead branch.

---

### HG-F005 — AoE Allegiance Filter (No Friendly Fire)
**Scenario:** H-011 | **Tier:** A (WRONG RESULT) | **Severity:** HIGH
**Scope:** AoE resolver, `aidm/core/play_loop.py`
Allied entities excluded from AoE blast. PHB has no allegiance exemption for AoE spells.
**PM recommendation:** New board entry. HIGH — Tier A wrong result. Allegiance-blind rasterization required.

---

### HG-F006 — Improvised Weapon Type Rejected by Schema
**Scenario:** H-012 | **Tier:** B | **Severity:** MEDIUM
**Scope:** Weapon schema validation
`weapon_type='improvised'` raises `ValueError`. PHB p.113 improvised weapons not in enum.
**PM recommendation:** New board entry. MEDIUM — schema gap, no crash risk.

---

### HG-F007 — Healing Spell Emits No hp_changed Event (Non-Hooligan)
**Scenario:** Phase 2 manual (CLW on living target) | **Severity:** MEDIUM
**Scope:** Healing resolver, `aidm/core/play_loop.py`
CLW resolves without exception but emits no `hp_changed` event. HP silent drop. Likely same root cause as HG-F004.
**PM recommendation:** New board entry or combine with HG-F004.

---

### GAP-WS-003-CONFIRMED — Monster HP Exposed on Join (Security)
**Severity:** HIGH — see ADVERSARIAL_AUDIT_SYNTHESIS_001 kill chain step 1
**Scope:** `ws_bridge.py:295–303`
`token_add` on join includes `hp` and `hp_max` for all entities including monsters. No suppression. Any client joining receives full monster HP values. This is passive HP disclosure requiring no adversarial action.
**PM recommendation:** Feed directly to WO-SEC-REDACT-001 scoping. This is the confirmed entry point.

---

### GAP-WS-004-CONFIRMED — Raw Internal Fields Leak via Passthrough (Security)
**Severity:** HIGH — see ADVERSARIAL_AUDIT_SYNTHESIS_001
**Scope:** `ws_bridge.py:565–575`
Passthrough branch for unhandled event types serializes entire raw `event_dict` into `delta` tuple and emits to client. Any event type not explicitly handled exposes all internal fields: `hp_before`, `hp_after`, `damage_type`, DC values, etc.
**PM recommendation:** Feed directly to WO-SEC-REDACT-001 scoping. This is the precision-tracking path from the kill chain.

---

## Section 5 — Verdict

**TIER A FAILURE + FINDINGS ONLY**

- 3 Tier A wrong results: H-003 (AoE origin), H-008 (CLW undead), H-011 (no friendly fire)
- 0 crashes
- 6 Hooligan FINDINGs + 1 non-Hooligan finding
- 2 security GAPs confirmed with source evidence (GAP-WS-003, GAP-WS-004)
- Gate regression: 28 failures — matches baseline, 0 new

**Escalation note:** Three Tier A failures are wrong-result bugs, not crashes. Engine is stable. Escalation to Slate for triage, not emergency stop. WO-SEC-REDACT-001 can now be scoped — both primary evidence paths confirmed.

**Priority recommendations for Slate:**
1. WO-SEC-REDACT-001 — GAP-WS-003 (HP disclosure on join) and GAP-WS-004 (passthrough raw leak) are confirmed. Scope and prioritize.
2. HG-F002 (AoE origin square) — HIGH, Tier A
3. HG-F004 + HG-F007 (healing no-op) — HIGH, Tier A, likely same root cause
4. HG-F005 (allegiance filter) — HIGH, Tier A
5. HG-F006 (improvised weapon) — MEDIUM
6. HG-F001 (ReadyIntent), HG-F003 (equipment) — LOW/MEDIUM backlog

---

*Filed by Anvil. No code changes made. Smoke output tee'd to `pm_inbox/HOOLIGAN_RUN_LATEST.txt`.*
