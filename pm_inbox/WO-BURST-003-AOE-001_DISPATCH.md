---
# WO-BURST-003-AOE-001 — Confirm-Gated AoE Spell Overlay

**Issued:** 2026-02-23
**Authority:** BURST-003 DC-2 RESOLVED (confirm-gated). Thunder authorization. AoE rasterizer complete (53 tests passing). Grid rendering live (`show_map()`).
**Gate:** New gate — target 10 tests. No existing gate letter assigned yet (PM will assign at acceptance).
**Blocked by:** Nothing. All dependencies implemented and tested.

---

## 1. Target Lock

When a player targets an AoE spell, display an ASCII overlay showing which squares are hit and which entities are in the blast radius — then require an explicit "yes" before the spell resolves. Cancel returns to targeting with no state change.

Right now `show_map()` renders the grid on demand. AoE squares are computed by `create_aoe_result()` but never shown to the player before resolution. The spell fires blind.

After this WO: player types e.g. "cast fireball at (3, -1)" → game shows the blast preview with entities marked → player confirms → spell resolves.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Trigger | AoE spells only (BURST, CONE, LINE, CYLINDER, SPHERE shapes) | Non-AoE spells (single-target) do not need overlay |
| 2 | Confirmation | Explicit "yes" / "confirm" required; any other input cancels | Per DC-2: confirm-gated. AoE is irreversible — misclick nukes must be preventable |
| 3 | Cancel behavior | Cancel returns to input prompt with no state change. No action consumed. | Canceling an AoE preview is not an action in 3.5e |
| 4 | Overlay format | Extend existing ASCII grid from `show_map()` with markers: `*` = AoE square, `!` = entity in AoE | Consistent with existing display; no new renderer needed |
| 5 | Origin marker | `@` for AoE origin (target point), distinct from entity symbols | Unambiguous; origin is not an entity |
| 6 | Save DC display | Show save DC and spell name in overlay header | Player needs this to assess risk to allies |
| 7 | Confirm prompt | Fixed string: `"Confirm AoE? [yes/cancel]: "` | Deterministic; easy to test |
| 8 | Parser integration | New action_type `"aoe_preview"` returned by parser when AoE spell pending confirm | Clean separation; no magic state |
| 9 | State storage | `PendingAoE` dataclass on WorldState: spell_name, origin, aoe_result, caster_id | Minimal; cleared on confirm or cancel |
| 10 | Audit event | Emit `AOE_PREVIEW_CONFIRMED` or `AOE_PREVIEW_CANCELLED` sensor event | Matches BURST-001 sensor discipline |

---

## 3. Contract Spec

### 3.1 PendingAoE dataclass

```python
# aidm/core/pending_aoe.py (new file)
from __future__ import annotations
from dataclasses import dataclass
from aidm.core.aoe_rasterizer import AoEResult

@dataclass(frozen=True)
class PendingAoE:
    spell_name: str
    caster_id: str
    origin_x: int
    origin_y: int
    aoe_result: AoEResult
    save_dc: int | None   # None for no-save AoE
```

### 3.2 WorldState extension

```python
# Add to WorldState (aidm/core/world_state.py or equivalent):
pending_aoe: PendingAoE | None = None
```

Clear it after confirm or cancel.

### 3.3 ASCII overlay format

```
Fireball — 20ft burst — Save DC 16 (Reflex)
Squares in blast: 13   Entities at risk: Kael, Goblin Scout A

  -3  -2  -1   0   1   2   3
4  .    .    .   .   .   .   .
3  .    .    *   *   *   .   .
2  .    *    *   @   *   *   .
1  .    .    *  [K]  *   .   .    K = Kael (ALLY)
0  .    .    !  [G]  *   .   .    G = Goblin Scout A (ENEMY)
-1  .    .    *   *   *   .   .
-2  .    .    .   .   .   .   .

Confirm AoE? [yes/cancel]: 
```

Rules:
- `@` = AoE origin (target point)
- `*` = AoE square (no entity)
- `!` = AoE square with entity (danger marker overrides `*`)
- `[X]` = entity symbol (first letter) — shown even if not in AoE (context)
- Entity list below grid: spell name, save DC, entities at risk (name + faction)
- Grid bounds: bounding box of AoE + 1-cell padding + any entities outside AoE but within 2 squares

### 3.4 Parser changes

```python
# play.py parse_player_input() additions:

# When pending_aoe exists on WorldState:
if ws.pending_aoe is not None:
    if verb in ("yes", "confirm", "y"):
        return "aoe_confirm", None
    elif verb in ("cancel", "no", "n", "back"):
        return "aoe_cancel", None
    # Any other input: treat as cancel (safe default)
    return "aoe_cancel", None

# When parsing spell cast targeting an AoE spell:
# (spell resolution already identifies AoE spells via their shape)
# Return "aoe_preview" instead of immediately resolving
```

### 3.5 Main loop additions

```python
# In play.py main game loop:

elif action_type == "aoe_preview":
    # Compute AoE result, set pending_aoe, display overlay
    _show_aoe_preview(ws, action_data)

elif action_type == "aoe_confirm":
    # Resolve the pending AoE spell
    _confirm_aoe(ws)

elif action_type == "aoe_cancel":
    # Clear pending_aoe, return to input
    ws = ws.clear_pending_aoe()
    print("AoE cancelled. No action taken.")
```

### 3.6 Sensor events

```python
# aidm/core/sensor_events.py (add two new event types):
AOE_PREVIEW_CONFIRMED = "aoe_preview_confirmed"
AOE_PREVIEW_CANCELLED = "aoe_preview_cancelled"
```

Emit with: spell_name, origin, affected_entity_ids, caster_id.

---

## 4. Implementation Plan

1. **Read** `aidm/core/aoe_rasterizer.py` — confirm `create_aoe_result()` signature and `AoEResult` fields
2. **Read** `play.py` — locate `show_map()` (lines ~745-821), `parse_player_input()`, main game loop
3. **Read** `aidm/core/world_state.py` (or equivalent) — find where to add `pending_aoe` field
4. **Create** `aidm/core/pending_aoe.py` — `PendingAoE` dataclass
5. **Extend** `WorldState` — add `pending_aoe: PendingAoE | None = None` field + `clear_pending_aoe()` method
6. **Write** `_show_aoe_preview(ws, action_data)` in `play.py`:
   - Call `create_aoe_result()` with spell shape/params
   - Collect entities in AoE squares
   - Render overlay (grid + entity list + confirm prompt)
   - Set `ws.pending_aoe`
7. **Write** `_confirm_aoe(ws)` in `play.py`:
   - Resolve spell using existing spell resolver
   - Emit `AOE_PREVIEW_CONFIRMED` sensor event
   - Clear `ws.pending_aoe`
8. **Extend** `parse_player_input()` — intercept yes/cancel when `pending_aoe` active
9. **Extend** main loop — handle `aoe_preview`, `aoe_confirm`, `aoe_cancel` action types
10. **Write** `tests/test_aoe_preview_gate.py` — 10 tests
11. **Run** `pytest tests/test_aoe_preview_gate.py -v` — all pass
12. **Run** `pytest tests/ --tb=no -q` — zero regressions

---

## 5. Deliverables Checklist

- [ ] `aidm/core/pending_aoe.py`: `PendingAoE` frozen dataclass
- [ ] `WorldState` extended: `pending_aoe` field + `clear_pending_aoe()`
- [ ] `_show_aoe_preview()` in `play.py`: renders overlay, sets pending_aoe
- [ ] `_confirm_aoe()` in `play.py`: resolves spell, emits event, clears pending_aoe
- [ ] `parse_player_input()` extended: yes/cancel intercepted when pending_aoe active
- [ ] Main loop: `aoe_preview`, `aoe_confirm`, `aoe_cancel` handled
- [ ] `tests/test_aoe_preview_gate.py`: 10 tests, all PASS
- [ ] Zero regressions vs 6,536 baseline

---

## 6. Test Spec (10 tests)

| Test | What it checks |
|---|---|
| T-01 | `PendingAoE` is frozen, has correct fields |
| T-02 | `_show_aoe_preview()` produces output containing `*` markers and `@` origin |
| T-03 | Entity in AoE square shows `!` marker, not `*` |
| T-04 | Entity NOT in AoE shows normal symbol (no `!`) |
| T-05 | Confirm prompt string is exactly `"Confirm AoE? [yes/cancel]: "` |
| T-06 | Parser returns `("aoe_confirm", None)` for input "yes" when pending_aoe active |
| T-07 | Parser returns `("aoe_cancel", None)` for input "cancel" when pending_aoe active |
| T-08 | Parser returns `("aoe_cancel", None)` for any other input when pending_aoe active (safe default) |
| T-09 | `clear_pending_aoe()` sets `pending_aoe` to None |
| T-10 | Cancel emits `AOE_PREVIEW_CANCELLED` event; confirm emits `AOE_PREVIEW_CONFIRMED` |

---

## 7. Integration Seams

- Do NOT modify `aoe_rasterizer.py` — it is complete and tested (53 tests)
- Do NOT modify existing `show_map()` — AoE overlay is a separate render path
- `WorldState` field addition must not break existing state serialization
- Spell resolver: after confirm, call existing spell resolution — no changes to resolver
- Sensor event types: add only, do not rename existing events
- Existing 4 BURST-003 grid tests must still pass (regression check)

---

## 8. Preflight

```bash
pytest tests/test_aoe_preview_gate.py -v   # gate passes
pytest tests/test_aoe_rasterizer.py -v     # no regressions in rasterizer
pytest tests/ --tb=no -q                   # zero new failures
```

---

## 9. Debrief Focus

1. **Overlay legibility** — does the grid + entity list read clearly at typical combat sizes (6×6 to 15×15)?
2. **State safety** — what happens if session restarts while `pending_aoe` is set? Document the edge case.

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
