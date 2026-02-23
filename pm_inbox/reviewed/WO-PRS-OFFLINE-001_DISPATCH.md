# WO-PRS-OFFLINE-001 — Offline Guarantee
**Lifecycle:** NEW
**Date:** 2026-02-23
**Type:** FEATURE
**Authority:** PRS-01 v1.0 FROZEN (`docs/contracts/PUBLISHING_READINESS_SPEC.md`)
**Gate:** Z (new)

---

## Target Lock

Build the P6 offline guarantee enforcement: a static scan for ungated network client imports, and a runtime smoke test verifying zero outbound connections in default config.

## Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Static scan scope? | **Python + TypeScript source** — scan for `socket`, `requests`, `urllib`, `http.client`, `fetch`, `axios`, `XMLHttpRequest` per PRS-01 §P6 |
| 2 | Runtime smoke approach? | **Import-level mock** — monkey-patch `socket.socket` to fail on `connect()`, then run default startup path. If no socket error, offline guarantee holds. No external network monitor needed. |
| 3 | Opt-in gate pattern? | **Config key check** — network imports are permitted only inside code blocks guarded by an explicit opt-in config flag that defaults to `False`/`off`. Static scan checks for this pattern. |
| 4 | Exceptions file? | **Yes** — `scripts/offline_exceptions.txt` for known-safe imports (e.g., `socket` used only for local IPC, not outbound) |

## Contract Spec

**`scripts/publish_scan_network_calls.py` (static):**
- Scan all `.py` and `.ts`/`.tsx` files for network client patterns per PRS-01 §P6
- For each match: check if it's inside an opt-in guard (config flag defaulting to off)
- Exceptions file: `scripts/offline_exceptions.txt` — format: `file_path|import_name|justification`
- Exit 0 if all network imports are gated or excepted, exit 1 otherwise
- Log findings to stdout

**`scripts/publish_smoke_no_network.py` (runtime):**
- Monkey-patch `socket.socket.connect` to raise `ConnectionRefusedError`
- Run the application's default startup path (import `aidm`, instantiate core objects)
- If no unhandled `ConnectionRefusedError`, PASS
- Exit 0 if no outbound connections attempted, exit 1 otherwise
- Log to stdout

## Implementation Plan

1. Identify all network-related imports in the codebase (baseline scan)
2. Build static scanner with pattern matching + opt-in guard detection
3. Build runtime smoke with socket monkey-patch
4. Create `scripts/offline_exceptions.txt` with any legitimate local-only uses
5. Run both scripts, document findings

## Gate Spec

**New test file:** `tests/test_publish_offline_gate_z.py` (Gate Z)

| Test ID | What It Checks |
|---------|---------------|
| Z-01 | Static scan exits 0 on current repo |
| Z-02 | Static scan detects planted ungated `requests.get()` |
| Z-03 | Static scan respects exceptions file |
| Z-04 | Runtime smoke exits 0 (no outbound connections in default config) |
| Z-05 | Runtime smoke detects planted outbound connection |
| Z-06 | Socket monkey-patch correctly intercepts `connect()` |

**Minimum 6 tests.** Gate letter: Z.

## Files to Read

- `docs/contracts/PUBLISHING_READINESS_SPEC.md` — §P6, §6 for offline guarantee
- `aidm/` — Core package to understand import structure
- `config/` — Default config to understand opt-in flags

## Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

## Integration Seams

- Static scan logs to `RC_PACKET/p6_offline_static.log` (via orchestrator)
- Runtime smoke logs to `RC_PACKET/p6_offline_runtime.log` (via orchestrator)
- Exit codes: 0 = PASS, 1 = FAIL

## Assumptions to Validate

1. Default config exists and has no network features enabled
2. `socket` imports in codebase (if any) are for local IPC only, not outbound connections

## Delivery Footer

Builder delivers: 2 scripts + 1 exceptions file + gate tests. Debrief in CODE format (500 words, 5 sections + Radar). Commit message references PRS-01 and gate letter Z.

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Offline work order complete. Awaiting Thunder."
```
