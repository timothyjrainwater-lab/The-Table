# WO-UI-04: WebSocket Protocol Formalization + roll_result Freeze

**Phase:** UI Phase 4 — Protocol Hardening
**Scope:** Narrowly scoped to protocol formalization + `roll_result` freeze + integration tests. NOT new UI objects.
**Rationale:** WO-UI-03 created protocol debt by inventing a `roll_result` message type consumed via wildcard handler. Clearing this now is cheap; leaving it infects Director and Voice work downstream.
**Predecessor:** WO-UI-03 (`f149d2d`) — dice tray/tower/PENDING_ROLL handshake

---

## Contract Changes (6)

### Change 1: Freeze `roll_result` as Named Dataclass
- Add `RollResult` as a frozen dataclass in the module that defines WebSocket protocol message types (confirm file path before writing — likely `aidm/ui/ws_protocol.py` or equivalent).
- Fields from Field Manual #32: `d20_result: int`, `total: int`, `success: bool`.
- Must include `to_dict()` / `from_dict()` following existing message type conventions.
- Must be importable from the same module as other protocol message types.

### Change 2: Register `RollResult` in Message Registry
- Add `RollResult` to the discriminator map / message registry alongside existing message types.
- The message type string must be `"roll_result"` (matching the string already in use by WO-UI-03).
- Ensure `from_dict()` dispatches correctly for `"roll_result"` messages.

### Change 3: Negative Test — Unknown Message Types
- Add a gate test that constructs a message dict with `msg_type: "garbage_nonexistent_type"` and verifies it is **rejected** (raises ValueError, returns error, or fails deserialization — whichever pattern the registry uses).
- The test must also verify that removing `roll_result` from the registry would cause the existing roll_result messages to fail. (This proves the registry is load-bearing, not decorative.)
- Gate label: **UI-G8-protocol-registry**.

### Change 4: Round-Trip Integration Test
- Add a gate test that exercises the full dice handshake sequence:
  1. Create a `PENDING_ROLL` state (from WO-UI-03's `PendingRoll`)
  2. Simulate a `DiceTowerDropIntent` (from WO-UI-03)
  3. Produce a `roll_result` message via the formalized `RollResult.to_dict()`
  4. Deserialize via `RollResult.from_dict()`
  5. Assert: `d20_result` matches the deterministic RNG output for the given seed
  6. Assert: the result is replay-stable (same seed → same `to_dict()` bytes)
- Gate label: **UI-G8-roll-roundtrip**.

### Change 5: Audit and Remove Wildcard Handler Consumption
- Locate where `roll_result` is currently consumed via the wildcard handler path (`msg_type`/`update_type`/`delta.type` sniffing).
- Migrate to typed consumption: the handler should construct `RollResult.from_dict(payload)` instead of reading raw dict keys.
- If the wildcard handler is used by other message types that are ALSO unfrozen, note them in the debrief but do NOT formalize them in this WO (scope boundary).

### Change 6: Gate Test Updates
- All new gate tests under `test_ui_gate_g.py` (or a new `test_ui_gate_h.py` if appropriate).
- Expected gate tests: 133+ total (130 existing + 3 new minimum: protocol-registry, roll-roundtrip, wildcard-removal confirmation).
- Existing 130 gate tests must continue to pass with 0 regressions.

---

## Hard Stop Conditions

1. **If `ws_protocol.py` (or equivalent) does not exist or cannot be located** — stop and report. This WO cannot proceed without the protocol module.
2. **If the wildcard handler is structurally required by OTHER message types** (not just `roll_result`) — stop and report before removing it. Scope is `roll_result` formalization only; collateral removal of a handler used by other types is out of scope.
3. **If `PendingRoll` or `DiceTowerDropIntent` from WO-UI-03 cannot be imported** — stop and report. These are prerequisites.
4. **If freezing `RollResult` as a dataclass would require modifying the core engine boundary** (`aidm/core/`) — stop and report. This is a UI-layer protocol change.

---

## Non-Negotiable Guardrails

1. **UI never generates randomness for outcomes.** The `RollResult` dataclass contains results received from the Box (engine), not produced by the UI. No RNG call may exist in any UI protocol module.
2. **Replay-stable.** `RollResult.to_dict()` output must be deterministic for the same inputs. No timestamps, no auto-generated IDs.
3. **No backflow.** The UI protocol module (`aidm/ui/`) must not import from `aidm/core/`. Direction is Box→UI, not UI→Box.

---

## Binary Decisions (4)

1. **File location for `RollResult`:** Same module as existing protocol types (e.g., `ws_protocol.py`) — YES/NO?
2. **Message registry pattern:** Follow the existing pattern for message type dispatch (dict mapping, match/case, if/elif chain — whichever is in use) — YES, follow existing.
3. **Separate gate file:** New gates go in existing `test_ui_gate_g.py` as UI-G8 — YES. (If G file is too large, builder may split to `test_ui_gate_h.py` and record in debrief.)
4. **Wildcard handler:** Remove roll_result from wildcard path — YES, if no other types depend on it. If other types do, migrate roll_result only and note the remaining wildcard consumers.

---

## Integration Seams

1. **WO-UI-03 → WO-UI-04 seam:** `PendingRoll`, `DiceTowerDropIntent`, and the dice tray/tower zone contracts from WO-UI-03 are prerequisites. The `roll_result` message shape was defined in WO-UI-03 but not frozen. This WO freezes it.
   - Seam snippet not available — builder should locate the `roll_result` handler in the WebSocket message dispatch code (likely `client/` TypeScript side or `aidm/ui/` Python side) and verify field names before writing the dataclass.

2. **Protocol → Frontend seam:** The TypeScript client currently consumes `roll_result` as a raw JSON object. After this WO, the Python side will have a typed `RollResult` class. The TS side should continue to consume the same JSON shape — no TS changes required unless field names change (they should not).
   - If the builder discovers the TS handler constructs typed objects from the JSON, note the file and line in the debrief.

3. **Protocol → Engine seam:** The engine (Box) produces dice results. This WO does NOT change how the engine produces results — only how the UI protocol module RECEIVES and TYPES them. No engine-side changes are in scope.
   - Test: round-trip test (Change 4) exercises this seam by verifying typed deserialization matches engine output.

4. **No integration seams with Oracle, Director, or Lens.** This WO is contained within `aidm/ui/` and `tests/`.

---

## Assumptions to Validate

1. **Assumption:** A WebSocket protocol module exists at `aidm/ui/ws_protocol.py` (or similar) that defines message types as frozen dataclasses with `to_dict()`/`from_dict()`. Confirm before writing `RollResult`.

2. **Assumption:** There is an existing message registry (dict, map, or dispatch chain) that resolves message type strings to dataclass constructors. Confirm the pattern before adding `roll_result`.

3. **Assumption:** The wildcard handler path (`msg_type`/`update_type`/`delta.type`) is the current consumption mechanism for `roll_result`. Locate it and confirm before migrating.

4. **Assumption:** `PendingRoll` and `DiceTowerDropIntent` are importable from `aidm/ui/pending.py` (per Field Manual #28). Confirm import paths.

5. **Assumption:** The existing gate tests in `test_ui_gate_g.py` can accommodate new UI-G8 tests without exceeding reasonable file size. If file is already large, split is acceptable.

---

## Debrief Focus

1. **Spec divergence:** Where did the WO spec most diverge from repo reality (one concrete example)?
2. **Underspecified anchor:** What did you have to invent because the doctrine/spec was underspecified (name the missing anchor)?

---

## Delivery

After all success criteria pass:
1. Write your debrief (`pm_inbox/DEBRIEF_WO-UI-04.md`, Section 15.5) — 500 words max. Five mandatory sections:
   - **Section 0: Scope Accuracy** — one sentence: "WO scope was [accurate / partially accurate / missed X]"
   - **Section 1: Discovery Log** — what you checked, what you learned, what you rejected (even if efficient)
   - **Section 2: Methodology Challenge** — one thing to push back on
   - **Section 3: Field Manual Entry** — one ready-to-paste tradecraft entry
   - **Section 4: Builder Radar** — MANDATORY, 3 labeled lines exactly:
     - Line 1: **Trap.** Hidden dependency or trap — what almost burned you.
     - Line 2: **Drift.** Current drift risk — what is most likely to slide next.
     - Line 3: **Near stop.** What got close to triggering a stop condition, and why it didn't.
     - All 3 lines MUST be present with their labels. Write "none identified" if a line has no content. Do NOT omit lines.
     - **REJECTION GATE:** Debriefs with missing or unlabeled Radar lines are REJECTED and re-issued. No partial accept.
   - **Section 5: Focus Questions** — answer the two questions from `## Debrief Focus` above
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md`
3. `git add` all changed/new files — code, tests, debrief, AND briefing update
4. `git commit -m "feat: WO-UI-04 — WebSocket protocol formalization + roll_result freeze"`
5. Record the commit hash and add it to the debrief header (`**Commit:** <hash>`)
6. `git add pm_inbox/DEBRIEF_WO-UI-04.md && git commit --amend --no-edit`
7. **FIRE AUDIO CUE (MANDATORY):**
   Primary: `python scripts/speak.py --persona dm_narrator "Work order complete. Awaiting operator."`
   Fallback: `powershell -c "(New-Object Media.SoundPlayer 'C:/Windows/Media/tada.wav').PlaySync()"`
   The Operator works on other tasks and cannot see your output. This cue is the ONLY notification that you are done. Missing it stalls the entire pipeline. The primary command exercises the full TTS pipeline (Chatterbox + emotion router + tavern-baked refs) — this is intentional QA.

Everything in the working tree — code AND documents — is at risk of loss if uncommitted.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.
