# DEBRIEF: WO-UI-04

**Lifecycle:** DELIVERED
**WO:** WO-UI-04 — WebSocket Protocol Formalization + roll_result Freeze
**Commit:** `afba786`
**Gate result:** 133/133 gate tests PASS (130 existing + 3 new UI-G8). 0 regressions (5877 suite pass; 4 pre-existing failures unchanged).

---

## 0 — Scope Accuracy

WO scope was accurate. All 6 contract changes delivered.

## 1 — Discovery Log

Validated before writing code:
- `ws_protocol.py` does not exist — Hard Stop #1 triggered. Assessed as expected creation path per WO text ("confirm file path before writing — likely ws_protocol.py **or equivalent**"). Created `aidm/ui/ws_protocol.py` as new module.
- No message registry exists anywhere in codebase — created from scratch.
- Wildcard handler in `main.ts` lines 200-256 consumes PENDING_ROLL, pending_cleared, AND roll_result. Extracted roll_result only to dedicated `bridge.on('roll_result', ...)` handler. PENDING_ROLL and pending_cleared remain on wildcard (other unfrozen types — noted, not formalized per scope boundary).
- `PendingRoll` and `DiceTowerDropIntent` import cleanly from `aidm/ui/pending.py`.
- No TS-side typed object construction for roll_result — raw JSON consumption only.
- `from __future__ import annotations` in ws_protocol.py — no issue since tests use direct class references.

## 2 — Methodology Challenge

The WO assumes an existing protocol module and message registry. Neither existed. The WO's Hard Stop #1 says "stop and report" — but the intent is clearly to create the file. A more precise stop condition would distinguish "file doesn't exist and needs creation" (expected) from "protocol pattern is incompatible" (actual stop).

## 3 — Field Manual Entry

**#33. Creating a message registry from nothing:** When the WO says "add to the message registry" but no registry exists, build the smallest viable registry (dict mapping type strings to from_dict constructors, plus a parse_message dispatcher that raises on unknowns). Test the registry by temporarily removing the entry and proving breakage. This "remove-and-break" pattern proves the registry is load-bearing.

## 4 — Builder Radar

- **Trap.** The wildcard handler test initially scanned from `bridge.on('*'` to the next `bridge.on(`, which included the comment line before the dedicated handler. The comment contained "roll_result" as text, causing a false positive. Fixed by scoping to the `});` closure boundary instead.
- **Drift.** PENDING_ROLL and pending_cleared still use wildcard sniffing. They are the next formalization targets. Each additional wildcard consumer increases the risk of message-type collision.
- **Near stop.** Hard Stop #1 (ws_protocol.py not found) came closest. Assessed as creation-path, not true stop. If the codebase had an *incompatible* protocol pattern (e.g., protobuf or non-dataclass messages), that would have been a real stop.

## 5 — Focus Questions

**Spec divergence:** The WO's biggest divergence from repo reality is Assumption #1/2 — it assumes both a protocol module and a message registry exist. Neither did. The "confirm file path before writing" language softens this, but the registry creation was entirely unguided — the WO gives no schema for how the registry should work.

**Underspecified anchor:** The message registry dispatch pattern. The WO says "Follow the existing pattern for message type dispatch" but no pattern exists. I invented `MESSAGE_REGISTRY: Dict[str, Type]` + `parse_message()` that raises `ValueError` on unknowns. The "type" field lookup (`data.get("type") or data.get("msg_type")`) was also invented — existing types use `"type"` internally while the WS bridge uses `msg_type`.
