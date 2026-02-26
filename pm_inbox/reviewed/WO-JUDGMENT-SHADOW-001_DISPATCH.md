# WO-JUDGMENT-SHADOW-001
## Phase 0 Judgment Layer — Routing Hook, Validator Shell, Needs-Clarification Path

**Priority:** MEDIUM
**Classification:** FEATURE
**Gate ID:** JUDGMENT-SHADOW
**Minimum gate tests:** 8
**Status:** HOLD / READY-TO-DISPATCH (do not dispatch until Batch B/C verdicts land)
**Dispatch:** JUDGMENT LAYER PHASE 0
**Parent:** STRAT-AIDM-JUDGMENT-LAYER-001, SPEC-RULING-CONTRACT-001, SPEC-ROUTING-BOUNDARY-MATRIX-001

---

## Target Lock

Wire the Shadow phase adjudication instrumentation layer. This WO does **not** change any resolver behavior. It adds three components at the parser/orchestrator boundary:

1. **Routing hook** — intercept `command_type == "unknown"` in `session_orchestrator.py:544` and classify the action before building a clarification response. Emit a structured `unroutable_action` event with `route_class` and routing confidence.

2. **Validator shell** — a minimal `RulingArtifact` schema dataclass + a validator that checks schema completeness and DC bounds. Does not check mechanic legality (Phase 1). Returns `validator_verdict` + `validator_reasons[]`.

3. **`needs_clarification` event path** — replace the plain `_build_clarification_result()` call with one that also emits a structured `needs_clarification` event to the event log. Non-canonical: this event is logged only; it does not drive game state.

**No resolver changes. No canonical ruling events. No LLM Proposer. This is instrumentation only.**

---

## Binary Decisions

1. **Insertion point:** `session_orchestrator.py:544-549` — the `if command.command_type == "unknown"` block. This is already the graceful catch point. Wrap it with the routing hook before the `_build_clarification_result()` call. Do NOT touch `play_loop.py:1534` (the crash point) — that's already unreachable from the unknown path.

2. **`RulingArtifact` dataclass location:** New file `aidm/schemas/ruling_artifact.py`. Keeps schema separate from event types. Imports into validator and event compiler (future).

3. **Validator location:** New file `aidm/core/ruling_validator.py`. Single function: `validate_ruling_artifact(artifact: RulingArtifact) -> Tuple[str, List[str]]` returns `(validator_verdict, validator_reasons)`. Phase 0 checks only: schema completeness + DC bounds (5–40). No mechanic legality check yet.

4. **`needs_clarification` event:** Add `"needs_clarification"` to the play_loop event type set. Event payload: `{action_raw, route_class, routing_confidence, clarification_message}`. Emitted to the event log but not sent to game state engine. Shadow phase: log-only.

5. **`unroutable_action` event:** Emitted at the routing hook with `{action_raw, route_class, routing_confidence, timestamp}`. This is the telemetry artifact for Shadow phase analysis.

6. **Ruling Contract schema (Shadow subset):** Not all fields required for Phase 0. Phase 0 only needs: `player_action_raw`, `route_class`, `routing_confidence`, `validator_verdict`, `validator_reasons[]`. Full schema from SPEC-RULING-CONTRACT-001 is deferred to Guarded phase.

---

## Contract Spec

### `aidm/schemas/ruling_artifact.py` — NEW FILE

```python
# WO-JUDGMENT-SHADOW-001: Phase 0 Ruling Contract schema
from dataclasses import dataclass, field
from typing import List, Literal, Optional

@dataclass
class RulingArtifactShadow:
    """
    Phase 0 (Shadow) subset of the full Ruling Contract.
    SPEC-RULING-CONTRACT-001 defines the full schema.
    This dataclass is expanded to full schema in Guarded phase.
    """
    player_action_raw: str
    route_class: Literal[
        "named",
        "named_plus_circumstance",
        "improvised_synthesis",
        "impossible_or_clarify",
    ]
    routing_confidence: Literal["certain", "probable", "uncertain", "escalate"]

    # Validator output (filled by ruling_validator.py, not by caller)
    validator_verdict: Literal["pass", "fail", "needs_clarification"] = "needs_clarification"
    validator_reasons: List[str] = field(default_factory=list)

    # Optional Phase 0 fields (populated when routing hook has more context)
    dc: Optional[int] = None
    clarification_message: Optional[str] = None
```

### `aidm/core/ruling_validator.py` — NEW FILE

```python
# WO-JUDGMENT-SHADOW-001: Phase 0 validator shell
from typing import List, Tuple
from aidm.schemas.ruling_artifact import RulingArtifactShadow

_DC_MIN = 5
_DC_MAX = 40

def validate_ruling_artifact(artifact: RulingArtifactShadow) -> Tuple[str, List[str]]:
    """
    Phase 0 validation: schema completeness + DC bounds only.
    Returns (validator_verdict, validator_reasons).
    Phase 1 adds: mechanic legality, modifier source checking, rationale quality.
    """
    reasons = []

    # Schema completeness
    if not artifact.player_action_raw:
        reasons.append("player_action_raw is empty")
    if not artifact.route_class:
        reasons.append("route_class is missing")
    if not artifact.routing_confidence:
        reasons.append("routing_confidence is missing")

    # DC bounds (only checked if dc is provided)
    if artifact.dc is not None:
        if artifact.dc < _DC_MIN:
            reasons.append(f"dc={artifact.dc} is below minimum ({_DC_MIN})")
        elif artifact.dc > _DC_MAX:
            reasons.append(f"dc={artifact.dc} exceeds maximum ({_DC_MAX}); flag for DM review")
            # DC > 40 is needs_clarification, not hard fail
            return "needs_clarification", reasons

    if reasons:
        return "fail", reasons
    return "pass", []
```

### `aidm/runtime/session_orchestrator.py` — MODIFY

At `command.command_type == "unknown"` block (lines 544–549), insert routing hook before `_build_clarification_result()`:

```python
if command.command_type == "unknown":
    # WO-JUDGMENT-SHADOW-001: Routing hook — classify and log unroutable action
    from aidm.schemas.ruling_artifact import RulingArtifactShadow
    from aidm.core.ruling_validator import validate_ruling_artifact

    _artifact = RulingArtifactShadow(
        player_action_raw=text_input,
        route_class="impossible_or_clarify",  # Phase 0: all unknowns → impossible_or_clarify
        routing_confidence="escalate",          # Phase 0: no route classifier yet → escalate
    )
    _verdict, _reasons = validate_ruling_artifact(_artifact)
    _artifact.validator_verdict = _verdict
    _artifact.validator_reasons = _reasons

    # Emit Shadow telemetry event (non-canonical — log only)
    _clarify_msg = (
        "I don't understand that command. Try: attack [target], "
        "cast [spell], move to [x,y], rest, or go [exit]."
    )
    _artifact.clarification_message = _clarify_msg
    self._log_shadow_ruling(_artifact)  # see helper below

    return self._build_clarification_result(
        _clarify_msg,
        self._get_available_actions(),
    )
```

Add helper method to `RuntimeSession`:

```python
def _log_shadow_ruling(self, artifact) -> None:
    """
    WO-JUDGMENT-SHADOW-001: Log Shadow phase ruling artifact to structured log.
    Non-canonical — does not emit to game state engine.
    Output file: logs/shadow_rulings.jsonl (append mode).
    """
    import json, dataclasses
    from pathlib import Path
    log_path = Path("logs/shadow_rulings.jsonl")
    log_path.parent.mkdir(exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dataclasses.asdict(artifact)) + "\n")
```

### `tests/test_judgment_shadow_gate.py` — NEW FILE

Minimum 8 gate tests, IDs JS-001 through JS-008:

| Test | Assertion |
|------|-----------|
| JS-001 | Unknown command → route_class = "impossible_or_clarify" emitted in Shadow log |
| JS-002 | Unknown command → routing_confidence = "escalate" in Shadow log |
| JS-003 | Unknown command → validator_verdict present in Shadow log (pass/fail/needs_clarification) |
| JS-004 | Unknown command → clarification_message populated in Shadow log |
| JS-005 | Unknown command → `_build_clarification_result()` still returns correct TurnResult (no regression) |
| JS-006 | `validate_ruling_artifact()` with dc=3 → verdict="fail", reason includes "below minimum" |
| JS-007 | `validate_ruling_artifact()` with dc=45 → verdict="needs_clarification", reason includes "exceeds maximum" |
| JS-008 | `validate_ruling_artifact()` with valid artifact → verdict="pass", reasons=[] |

---

## Implementation Plan

1. Read `aidm/runtime/session_orchestrator.py` lines 540–570 — confirm exact unknown-command block location.
2. Read `aidm/core/play_loop.py` lines 1530–1540 — confirm the crash point is unreachable from the unknown path (validation only; no changes here).
3. Create `aidm/schemas/ruling_artifact.py` with `RulingArtifactShadow` dataclass.
4. Create `aidm/core/ruling_validator.py` with `validate_ruling_artifact()`.
5. Modify `session_orchestrator.py` — insert routing hook + `_log_shadow_ruling()` helper.
6. Confirm `logs/` directory creation is safe (does not conflict with existing log infra).
7. Write `tests/test_judgment_shadow_gate.py` with JS-001 through JS-008.
8. Run gate suite: `python -m pytest tests/test_judgment_shadow_gate.py -v`.
9. Run regression: `python -m pytest tests/ -q --tb=short --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ui_2d_wiring.py`.
10. Confirm 0 new failures. Confirm no resolver test regressions.

---

## Integration Seams

- **`aidm/runtime/session_orchestrator.py`** — one insertion in `if command.command_type == "unknown"` block + one new helper method. No other changes.
- **`aidm/schemas/ruling_artifact.py`** — NEW. `RulingArtifactShadow` dataclass. Phase 0 schema only.
- **`aidm/core/ruling_validator.py`** — NEW. `validate_ruling_artifact()`. Phase 0 checks only.
- **`logs/shadow_rulings.jsonl`** — NEW runtime output. Append-only, non-canonical. Not committed to git (add to `.gitignore` if not already there).
- **Event constructor:** `Event(event_id=..., event_type=..., timestamp=..., payload=...)` — NOT used in Phase 0. Shadow events are written to log file, not to the event stream. Phase 1 wires to event stream.
- **No resolver changes.** `play_loop.py`, `attack_resolver.py`, `spell_resolver.py`, etc. — untouched.

---

## Assumptions to Validate

1. Confirm `command.command_type == "unknown"` block is at lines 544–549 and contains the only unknown-command handling path (expected: yes — preflight confirmed).
2. Confirm `play_loop.py:1534` crash point is unreachable from the unknown path (expected: yes — `_build_clarification_result()` returns before execute_turn() is called).
3. Confirm `logs/` directory does not conflict with existing log infrastructure (expected: check for `logs/` in .gitignore and existing log paths before creating).
4. Confirm `session_orchestrator.py` `RuntimeSession` class is the correct class to add `_log_shadow_ruling()` to (expected: yes — `process_text_turn()` is a method of `RuntimeSession`).
5. Confirm no existing `RulingArtifact` or `ruling_validator` anywhere in the codebase (expected: none — grep to verify).

---

## Preflight

Before writing any code:
- `grep -n "command_type.*unknown\|unknown.*command_type" aidm/runtime/session_orchestrator.py` — confirm lines 544–549
- `grep -rn "ruling_artifact\|ruling_validator\|RulingArtifact" aidm/` — confirm nothing exists
- `grep -n "logs/" aidm/runtime/session_orchestrator.py` — check existing log path patterns
- `cat .gitignore | grep logs` — confirm logs directory handling
- `python -m pytest tests/ -q --tb=short --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ui_2d_wiring.py 2>&1 | tail -5` — baseline before any changes

---

## Shadow Phase Scope (explicit — do not exceed)

**In scope:**
- `RulingArtifactShadow` dataclass (Phase 0 subset)
- `validate_ruling_artifact()` (schema completeness + DC bounds only)
- Routing hook in `session_orchestrator.py` unknown-command block
- `_log_shadow_ruling()` helper (file log, non-canonical)
- Gate tests JS-001–JS-008

**Out of scope (Phase 1 / Guarded):**
- LLM Proposer — no
- Mechanic legality checking — no
- Route classifier (beyond default "escalate") — no
- Event stream emission — no
- Canary pack execution — no
- Full `RulingArtifact` schema — no
- `needs_clarification` event in game event stream — no

If the builder discovers a related gap outside this scope, document as a finding. Do not fix it.

---

## Delivery Footer

- Files created: `aidm/schemas/ruling_artifact.py`, `aidm/core/ruling_validator.py`, `tests/test_judgment_shadow_gate.py`
- Files modified: `aidm/runtime/session_orchestrator.py`
- Gate: JUDGMENT-SHADOW, minimum 8 tests
- Run full regression before filing debrief
- **Debrief Required:** File to `pm_inbox/reviewed/DEBRIEF_WO-JUDGMENT-SHADOW-001.md`

### Debrief Template

```
# DEBRIEF — WO-JUDGMENT-SHADOW-001

**Verdict:** [PASS/FAIL] [N/N]
**Gate:** JUDGMENT-SHADOW
**Date:** [DATE]

## Pass 1 — Per-File Breakdown
[Files created/modified, key findings, any scope drift]

## Pass 2 — PM Summary (≤100 words)
[Summary]

## Pass 3 — Retrospective
[Drift caught, patterns, open findings]

## Radar
[Gate results, shadow log sample output (first 3 entries), validator verdict distribution]
```

### Audio Cue
```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
