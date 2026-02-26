# ENGINE DISPATCH #14 — BATCH E
**Issued by:** Slate (PM)
**Date:** 2026-02-26
**To:** Chisel (lead builder)
**Batch:** E — 2 WOs, 16 gate tests
**Prerequisite:** ENGINE DISPATCH #13 ACCEPTED ✅ (38/38, 0 regressions, coverage 143/69/188 GAP 47.5%)

---

## Boot Sequence

Before any work:

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm gate total is 914 (`pytest --co -q | tail -5` or equivalent count)
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md` — note Batch D is ACCEPTED, Batch E is DISPATCHED
4. Orphan check: any WO marked IN EXECUTION with no debrief? Flag to Slate before proceeding.

---

## Batch E Work Orders

### WO 1 — WO-ENGINE-EVASION-ARMOR-001
**File:** `pm_inbox/WO-ENGINE-EVASION-ARMOR-001_DISPATCH.md`
**Scope:** `aidm/core/spell_resolver.py` — two guard checks
**Gate:** `tests/test_engine_evasion_armor_001_gate.py` — 8 tests (EA-001–EA-008)
**Gate label:** ENGINE-EVASION-ARMOR-001
**Kernel touch:** NONE
**Dependencies:** EF.ARMOR_TYPE confirmed live from Batch D ✅

**Summary:** Evasion and Improved Evasion do not function in medium or heavy armor (PHB p.50). The blocker was `EF.ARMOR_TYPE` — now live. Two guard checks in `spell_resolver.py` at the two evasion sites (saved=True ~line 892, saved=False ~line 901). No schema changes, no new fields, no new imports.

---

### WO 2 — WO-ENGINE-CALLED-SHOT-POLICY-001
**File:** `pm_inbox/WO-ENGINE-CALLED-SHOT-POLICY-001_DISPATCH.md`
**Scope:** `aidm/schemas/intents.py` + `aidm/core/play_loop.py`
**Gate:** `tests/test_engine_called_shot_policy_001_gate.py` — 8 tests (CS-001–CS-008)
**Gate label:** ENGINE-CALLED-SHOT-001
**Kernel touch:** KERNEL-04 (Intent Semantics) + KERNEL-10 (Adjudication Constitution) — **flag to Anvil in Pass 3**
**Dependencies:** action_dropped event confirmed live from WO-PARSER-NARRATION-001 ✅

**Summary:** Called shots are not a D&D 3.5e mechanic. Option A (STRAT-CAT-05 DECIDED): hard denial + route to nearest named mechanic. New `CalledShotIntent` dataclass + routing branch in `execute_turn()` emitting `action_dropped`. No state mutation. No action consumed. Player must re-declare. This is the engine's first explicit hard-denial path for non-routable player intent.

---

## Integration Seams

**Event constructor signature (use exactly):**
```python
Event(event_id=next_event_id, event_type="action_dropped", payload={...})
```
NOT `id=`, `type=`, `data=`.

**EF.ARMOR_TYPE values:** `"none"` | `"light"` | `"medium"` | `"heavy"`. Default to `"none"` if absent (evasion active — correct for creatures).

**EF.CLASS_LEVELS pattern (if needed):**
```python
entity.get(EF.CLASS_LEVELS, {}).get("class_name", 0)
```
`EF.CLASS_FEATURES` does not exist — do not use it.

**action_dropped payload shape (from WO-PARSER-NARRATION-001):**
```python
{
    "actor_id": ...,
    "dropped_action_type": ...,
    "resolved_action_type": ...,
    "source_text": ...,
    "reason": ...,
    "suggestions": [...],
}
```

---

## Regression Protocol

Pre-existing failures: **12 stable** as of Batch D close. Do not treat these as regressions.

Run your WO-specific gate only to confirm delivery:
```bash
pytest tests/test_engine_evasion_armor_001_gate.py -v
pytest tests/test_engine_called_shot_policy_001_gate.py -v
```

Then run full suite once:
```bash
pytest --tb=short -q
```

**Retry cap:** If full suite shows new failures, fix once, re-run once. If still failing after one fix attempt — record in debrief and stop. Do not loop. PM stamps ACCEPTED; the regression runner is a separate pass.

---

## Chisel's Call: Take or Pass?

**WO-ENGINE-EVASION-ARMOR-001:** Touches `spell_resolver.py` — Chisel worked this file in Batch B R1 (Evasion WO). Continuity is an asset. Recommend: **take**.

**WO-ENGINE-CALLED-SHOT-POLICY-001:** Touches `play_loop.py` and `intents.py` — Chisel has touched both repeatedly. KERNEL-04/10 flag benefits from accumulated context. Recommend: **take**.

Chisel makes the final call per seat authority.

---

## Debrief Requirements

File debriefs to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-EVASION-ARMOR-001.md` and `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-CALLED-SHOT-POLICY-001.md`.

**Required sections (both WOs):**
- Pass 1: Full context dump — per-file breakdown, actual line numbers, what was found vs expected
- Pass 2: PM summary ≤100 words
- Pass 3: Retrospective — drift caught, patterns, recommendations. **Hidden DM kernel check mandatory.** Called Shot WO: flag KERNEL-04 + KERNEL-10 explicitly.
- Radar: open findings surfaced by this WO

**Missing debrief or missing Pass 3 → REJECT.**

---

## Post-Debrief (mandatory)

After each debrief is accepted, ask: **"Anything else you noticed outside the debrief?"**

File any loose threads as FINDINGs before closing the session.

---

## Session Close Conditions

WO-ENGINE-EVASION-ARMOR-001:
- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_evasion_armor_001_gate.py`
- [ ] `git commit` (commit hash in debrief)
- [ ] All 8 EA tests pass; zero regressions
- [ ] Debrief filed

WO-ENGINE-CALLED-SHOT-POLICY-001:
- [ ] `git add aidm/schemas/intents.py aidm/core/play_loop.py tests/test_engine_called_shot_policy_001_gate.py`
- [ ] `git commit` (commit hash in debrief)
- [ ] All 8 CS tests pass; zero regressions
- [ ] Debrief filed
- [ ] Kernel touch flagged to Anvil (KERNEL-04, KERNEL-10)

Chisel kernel updated at session close.

---

## Audio Cue (Chisel fires on completion)

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel. Chisel does not self-dispatch.*
