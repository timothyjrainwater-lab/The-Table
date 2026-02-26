# Work Order: WO-ENGINE-CALLED-SHOT-POLICY-001
**Artifact ID:** WO-ENGINE-CALLED-SHOT-POLICY-001
**Batch:** E (Dispatch #14 — Chisel)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**Policy ref:** STRAT-CAT-05-CALLED-SHOT-POLICY-001 (DECIDED — Option A)

---

## Summary

Called shots — player utterances like "I aim for the eyes," "I target the legs," "I shoot the sword out of his hand" — are **not a mechanic in D&D 3.5e PHB**. They are creative player flavor that the rules redirect to named mechanics (trip, disarm, feint, etc.).

The engine currently has no handling path for called shot utterances. If a player says "I shoot the orc in the knee," the parser either misroutes it as a standard attack intent (losing the player's intent signal) or produces an unrouted action (no output).

**Policy DECIDED (STRAT-CAT-05-CALLED-SHOT-POLICY-001 — Option A):**

> Hard denial + routing to nearest named mechanic.
> "Called shots are not a D&D 3.5 mechanic. Here's what you can do instead: [trip / disarm / feint / sunder / standard attack]."
> Option C upgrade path (scaffold for house-rule called shots) pre-committed pending scaffold validation — that is future work, not this WO.

This WO implements Option A: parse the called shot utterance, deny it cleanly, and surface the nearest named mechanic(s) the player can use instead.

---

## Scope

**Files in scope:**
- `aidm/core/play_loop.py` — add `CalledShotIntent` routing branch: emit `action_dropped` with denial message and mechanic suggestions
- `aidm/schemas/intents.py` — add `CalledShotIntent` dataclass

**Files out of scope:**
- Parser / NLP layer — do not modify intent classification. The parser will route called shot utterances to `CalledShotIntent` via a new intent type, but parser training/keyword lists are out of scope for this WO. This WO handles what happens when a `CalledShotIntent` reaches `execute_turn`.
- Any named mechanic resolvers (trip, disarm, etc.) — do not modify.

**Boundary note:** This WO wires the denial path. The parser keyword routing is a separate WO or can be attached as a follow-on. For gate testing, `CalledShotIntent` will be constructed directly in tests (no parser dependency).

---

## Assumptions to Validate (verify before writing)

1. Confirm `aidm/schemas/intents.py` contains no existing `CalledShotIntent` or similar.
2. Confirm `aidm/core/play_loop.py` `execute_turn()` routing — identify the pattern used for other unresolvable or "soft denial" intents (e.g. the narration bridge `action_dropped` path for compound utterances).
3. Confirm `action_dropped` event type is in use and ws_bridge handles it (WO-PARSER-NARRATION-001 wired this — verify it is live and the handler exists in `ws_bridge.py`).
4. Confirm no pre-existing test for called shot denial (search `tests/` for `called_shot`).

---

## Implementation

### 1. `aidm/schemas/intents.py` — add CalledShotIntent

```python
@dataclass
class CalledShotIntent:
    """Player declared a targeted strike without a named mechanic.

    Policy: Option A (STRAT-CAT-05-CALLED-SHOT-POLICY-001).
    Deny cleanly; surface nearest named mechanics.
    """
    actor_id: str
    target_id: Optional[str]          # may be None if target not parsed
    target_description: str           # raw body-part / target text from utterance
    source_text: str                  # original player utterance
    suggested_mechanics: List[str]    # populated by resolver; empty at parse time
```

### 2. `aidm/core/play_loop.py` — routing branch in `execute_turn()`

In the intent routing block (after existing branches), add:

```python
elif isinstance(combat_intent, CalledShotIntent):
    # Option A: Hard denial + nearest named mechanics (STRAT-CAT-05)
    suggestions = _called_shot_suggestions(combat_intent.target_description)
    payload = {
        "actor_id": combat_intent.actor_id,
        "dropped_action_type": "called_shot",
        "resolved_action_type": "none",
        "source_text": combat_intent.source_text,
        "reason": "Called shots are not a D&D 3.5e mechanic.",
        "suggestions": suggestions,
    }
    events.append(Event(event_type="action_dropped", payload=payload))
    # No state mutation. No action consumed. Player must re-declare.
    return world_state, next_event_id, events
```

### 3. `_called_shot_suggestions()` helper — in `play_loop.py`

A small pure function. No state access. Maps target description keywords to suggested mechanics.

```python
_CALLED_SHOT_SUGGESTION_MAP = {
    # body-part / intent keywords → suggested PHB mechanics
    "weapon": ["disarm (PHB p.155)", "sunder (PHB p.158)"],
    "sword": ["disarm (PHB p.155)", "sunder (PHB p.158)"],
    "shield": ["sunder (PHB p.158)"],
    "leg": ["trip (PHB p.158)"],
    "knee": ["trip (PHB p.158)"],
    "foot": ["trip (PHB p.158)"],
    "eye": ["standard attack (PHB p.140)"],
    "head": ["standard attack (PHB p.140)"],
    "throat": ["standard attack (PHB p.140)"],
    "hand": ["disarm (PHB p.155)"],
}

_CALLED_SHOT_DEFAULT_SUGGESTIONS = [
    "standard attack (PHB p.140)",
    "trip (PHB p.158)",
    "disarm (PHB p.155)",
    "feint (PHB p.68)",
]

def _called_shot_suggestions(target_description: str) -> List[str]:
    """Map a called shot target description to nearest named mechanics."""
    desc_lower = target_description.lower()
    for keyword, suggestions in _CALLED_SHOT_SUGGESTION_MAP.items():
        if keyword in desc_lower:
            return suggestions
    return _CALLED_SHOT_DEFAULT_SUGGESTIONS
```

---

## Acceptance Criteria

Write a gate test file `tests/test_engine_called_shot_policy_001_gate.py` with the following cases:

| ID | Scenario | Expected |
|----|----------|----------|
| CS-001 | `CalledShotIntent(target_description="the eye")` → `execute_turn()` | `action_dropped` event emitted; `dropped_action_type == "called_shot"`; `resolved_action_type == "none"` |
| CS-002 | `CalledShotIntent(target_description="the sword")` → suggestions | suggestions include "disarm" |
| CS-003 | `CalledShotIntent(target_description="the leg")` → suggestions | suggestions include "trip" |
| CS-004 | `CalledShotIntent(target_description="unknown target")` → suggestions | default suggestion list returned (at least one entry) |
| CS-005 | `CalledShotIntent` → world_state returned unchanged | state before == state after (no entity mutation) |
| CS-006 | `CalledShotIntent` → action budget not consumed | actor's action budget unchanged after the call |
| CS-007 | `CalledShotIntent` → zero state events in event log | no `hp_changed`, `attack_roll`, `damage_applied` events |
| CS-008 | `CalledShotIntent` → reason field populated | `payload["reason"]` contains "not a D&D 3.5e mechanic" |

8 tests total. Gate label: ENGINE-CALLED-SHOT-001.

---

## Pass 3 Checklist

Builder must report:
1. Confirm `action_dropped` handler in `ws_bridge.py` — does it surface the `suggestions` list to the client? If not, flag as FINDING (out of scope to fix here).
2. Confirm whether the suggestion map keyword list is sufficient for the hooligan test suite scenarios (check `tests/HOOLIGAN-CREATIVE-ACTION-SUITE-001` or equivalent for called shot scenarios).
3. Note any intent types in `play_loop.py` that are currently unrouted (fall through without event emission) — called shot may not be the only one. Document as finding if found.
4. Flag KERNEL-04 (Intent Semantics) — this WO is a direct implementation of what happens when player intent cannot be routed to a named mechanic. This is the adjudication layer boundary.

---

## Kernel Touch

**This WO touches KERNEL-04 (Intent Semantics)** — player declares an action with a target/manner that the rules don't directly support. The engine must choose: silently ignore, misroute to a different mechanic, or cleanly deny with reroute signal. This WO implements the clean-deny path, which is the correct behavior under KERNEL-10 (Adjudication Constitution) — the engine does not hallucinate a ruling.

Flag to Anvil: "WO-ENGINE-CALLED-SHOT-POLICY-001 touches KERNEL-04 (Intent Semantics) and KERNEL-10 (Adjudication Constitution) — Option A implements the engine's first explicit hard-denial path for non-routable player intent."

---

## Session Close Condition

- [ ] `git add aidm/schemas/intents.py aidm/core/play_loop.py tests/test_engine_called_shot_policy_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 CS tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/`
- [ ] Kernel touch flagged to Anvil (KERNEL-04, KERNEL-10)
