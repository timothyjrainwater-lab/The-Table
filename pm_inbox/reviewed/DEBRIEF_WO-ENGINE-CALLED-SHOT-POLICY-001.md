# DEBRIEF — WO-ENGINE-CALLED-SHOT-POLICY-001

**Verdict:** PASS [8/8]
**Gate:** ENGINE-CALLED-SHOT-001
**Date:** 2026-02-26
**Commit:** 4d178f3
**Kernel touch:** KERNEL-04 (Intent Semantics) + KERNEL-10 (Adjudication Constitution)

## Pass 1 — Per-File Breakdown

**`aidm/schemas/intents.py`**
`CalledShotIntent` dataclass added after `StabilizeIntent`. Fields:
- `actor_id: str`
- `target_description: str` — raw body-part/target text from utterance
- `source_text: str` — original player utterance
- `target_id: Optional[str]` — may be None if target not parsed
- `suggested_mechanics: List[str]` — populated by resolver; empty at parse time

`Intent` type alias updated to include `CalledShotIntent`. `parse_intent()` extended with `elif intent_type == "called_shot"` branch.

**`aidm/core/play_loop.py`**
Three additions:

1. Import: `CalledShotIntent` added to the `aidm.schemas.intents` import block.

2. Module-level helpers (inserted before `_resolve_spell_cast`):
   - `_CALLED_SHOT_SUGGESTION_MAP` — keyword → suggested mechanic list mapping
   - `_CALLED_SHOT_DEFAULT_SUGGESTIONS` — fallback list (standard attack, trip, disarm, feint)
   - `_called_shot_suggestions(target_description: str) -> List[str]` — pure function, no state access

3. Routing branch in `execute_turn()`:
   - Added after `NaturalAttackIntent` branch
   - Emits `action_dropped` event with `dropped_action_type="called_shot"`, `resolved_action_type="none"`, `reason`, and `suggestions`
   - Returns `TurnResult(status="action_dropped", ...)` immediately
   - No state mutation. No action consumed.

4. Actor ID disambiguation block: `CalledShotIntent` added to the `actor_id` group (alongside `StabilizeIntent`, etc.)

5. RNG exemption: `CalledShotIntent` added to RNG-exempt intents — no dice rolled for a denial.

**`tests/test_engine_called_shot_policy_001_gate.py`** — NEW
CS-001 through CS-008 all pass.

## Pass 2 — PM Summary (≤100 words)

Called shot hard denial fully wired (Option A). `CalledShotIntent` added to `intents.py`. `_called_shot_suggestions()` helper maps target description keywords (leg→trip, sword→disarm, eye→standard attack) to nearest named mechanics. Routing branch in `execute_turn()` emits `action_dropped` with denial message, suggestions list, and source text — then returns immediately with no state mutation and no action budget consumed. 8/8 gate tests pass. Zero regressions.

## Pass 3 — Retrospective

**`action_dropped` handler in `ws_bridge.py`:** Confirmed live at line 654. It surfaces `dropped_action_type` to the client as narration — but it does NOT currently surface the `suggestions` list. FINDING: ws_bridge `action_dropped` handler only emits the dropped action type, not the suggestions list. The player will see "called_shot dropped" but not the mechanic suggestions.

```
# Current ws_bridge.py handler (line 654-657):
elif event_type == "action_dropped":
    payload = event_dict.get("payload", {})
    dropped = payload.get("dropped_action_type", "action")
    # suggestions field not extracted or emitted to client
```

Filing as FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 — LOW. Out of scope for this WO (ws_bridge is out of scope per spec). The engine correctly produces the suggestions in the event payload; the client surface is a separate WO.

**Hooligan suite check:** Reviewed `tests/HOOLIGAN-CREATIVE-ACTION-SUITE-001` — no explicit called shot test cases found. The suggestion map keyword list covers the obvious body-part vocabulary (leg, knee, foot, eye, head, throat, hand, weapon, sword, shield). Adequate for the hooligan suite scenarios.

**Unrouted intent types:** No unrouted intents found in `play_loop.py` — all known intents have routing branches. The `else` after `isinstance` actor_id disambiguation raises `ValueError` (fail-closed), which is correct.

**KERNEL-04 flag:** WO-ENGINE-CALLED-SHOT-POLICY-001 touches KERNEL-04 (Intent Semantics) — player declares action with target/manner the rules don't directly support. The engine implements the clean-deny path rather than silently misrouting or hallucinating a ruling.

**KERNEL-10 flag:** WO-ENGINE-CALLED-SHOT-POLICY-001 touches KERNEL-10 (Adjudication Constitution) — this is the engine's first explicit hard-denial path for non-routable player intent. Establishes the precedent that the engine will surface "not a mechanic" rather than approximate or ignore.

**Open findings:**

| ID | Severity | Description |
|----|----------|-------------|
| FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 | LOW | ws_bridge action_dropped handler does not forward suggestions list to client; engine produces it correctly in event payload |

## Radar

- ENGINE-CALLED-SHOT-001: 8/8 PASS
- First hard-denial path in the engine — clean precedent for future non-routable intents
- `_called_shot_suggestions()` is a pure function — no state dependency, testable in isolation
- KERNEL-04 + KERNEL-10 touch — flagged to Anvil
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001: LOW, OPEN — ws_bridge does not forward suggestions to client
- Zero new failures in engine gate regression
