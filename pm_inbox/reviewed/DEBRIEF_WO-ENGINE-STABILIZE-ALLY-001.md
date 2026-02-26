# DEBRIEF — WO-ENGINE-STABILIZE-ALLY-001
# Stabilize Dying Ally — DC 15 Heal Check

**Verdict:** ACCEPTED 10/10
**Gate:** ENGINE-STABILIZE-ALLY
**Date:** 2026-02-26
**WO:** WO-ENGINE-STABILIZE-ALLY-001

---

## Pass 1 — Per-File Breakdown

### `aidm/core/stabilize_resolver.py` (new file)

**Changes made:**
- New resolver following established resolver pattern
- DC 15 Heal check (d20 + actor's Heal skill modifier)
- On success: `target[EF.STABLE] = True` — target stops bleeding out
- On fail: no change to target state
- Emits appropriate events: `stabilize_success` / `stabilize_fail`

### `aidm/schemas/intents.py`

**Changes made:**
- `StabilizeIntent(actor_id, target_id, action_type="standard")` added

### `aidm/core/action_economy.py`

**Changes made:**
- `StabilizeIntent` mapped as standard action (PHB p.153: stabilizing a dying character is a standard action)

### `aidm/core/play_loop.py`

**Changes made:**
- `StabilizeIntent` routing added as new elif branch in `execute_turn()`

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-STABILIZE-ALLY-001 ACCEPTED 10/10. New `stabilize_resolver.py` — DC 15 Heal check; success sets `EF.STABLE = True`, stopping bleed-out. `StabilizeIntent` added to `intents.py`. Standard action in `action_economy.py`. Routed in `play_loop.py`. SA-01–SA-10 all pass. No regressions.

---

## Pass 3 — Retrospective

**`EF.STABLE` interaction with death save loop:** The dying/stabilization system already has an `EF.STABLE` field used by the death-and-dying resolver. This WO correctly writes to the same field — no new field introduced. The existing `resolve_hp_transition` / death-save loop respects `EF.STABLE` and stops the -1/round bleed. Integration is clean.

**Standard action cost is correct.** PHB p.153: first aid to stabilize a dying character requires a standard action. The builder did not use a full-round action (which would have been wrong) or a free action.

**Heal skill modifier source:** The resolver reads the actor's Heal skill from the entity dict. This depends on `EF.SKILL_RANKS` being present — which is set by `build_character()` at chargen. No gap here; skill ranks are initialized at chargen unlike pool fields.

---

*Debrief filed by Slate (PM) on builder verdict receipt.*
