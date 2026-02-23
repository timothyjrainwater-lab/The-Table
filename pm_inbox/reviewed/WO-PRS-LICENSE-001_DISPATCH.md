# WO-PRS-LICENSE-001 — License Ledger + Lint
**Lifecycle:** NEW
**Date:** 2026-02-23
**Type:** FEATURE
**Authority:** PRS-01 v1.0 FROZEN (`docs/contracts/PUBLISHING_READINESS_SPEC.md`)
**Gate:** Y (new)

---

## Target Lock

Build the P4 license compliance system: a ledger documenting every dependency with SPDX license identifiers, and a lint script that validates the ledger against actual lockfiles.

## Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Ledger format? | **Markdown table** — `docs/LICENSE_LEDGER.md` per PRS-01 §P4 schema |
| 2 | Include dev-only deps? | **Yes** — PRS-01 requires all deps documented. `redistribution` field distinguishes `dev-only` from `runtime-dep` |
| 3 | Auto-generate or manual? | **Script generates draft from lockfiles**, builder reviews and fills `where_used` field manually |
| 4 | Project license TBD? | **Yes** — ledger tracks deps regardless. Compatibility check deferred until Thunder picks a license. Script warns if UNKNOWN license found. |

## Contract Spec

**`scripts/publish_check_licenses.py`:**
- Parse `requirements.txt` / `pyproject.toml` / `package-lock.json` (whichever exist)
- Cross-reference against `docs/LICENSE_LEDGER.md`
- Validate schema: all 6 required fields present per PRS-01 §P4 (dependency, version, license, source_url, redistribution, where_used)
- Flag any dependency in lockfile but not in ledger
- Flag any `UNKNOWN` license
- Exit 0 if all deps documented with valid SPDX licenses, exit 1 otherwise

**`scripts/publish_generate_license_draft.py` (helper):**
- Scan lockfiles, query PyPI/npm for license metadata (offline-safe: use cached metadata or manual entry)
- Generate draft `docs/LICENSE_LEDGER.md` with known fields, `UNKNOWN` for fields needing manual input
- This is a **one-time generation tool**, not a gate script

**`docs/LICENSE_LEDGER.md`:**
- Builder creates with all current dependencies
- Fields per PRS-01 §P4: dependency, version, license (SPDX), source_url, redistribution, where_used

## Implementation Plan

1. Inventory all dependency sources: `requirements.txt`, `pyproject.toml`, `package.json`/`package-lock.json`
2. Build draft generator that extracts dep names + versions
3. Manually fill license + source_url + redistribution + where_used for each dep
4. Build lint script that validates ledger against lockfiles
5. Run lint, resolve any gaps

## Gate Spec

**New test file:** `tests/test_publish_license_gate_y.py` (Gate Y)

| Test ID | What It Checks |
|---------|---------------|
| Y-01 | `publish_check_licenses.py` exits 0 on current repo |
| Y-02 | Lint detects missing dependency (planted) |
| Y-03 | Lint detects UNKNOWN license (planted) |
| Y-04 | Lint detects missing required field (planted) |
| Y-05 | Ledger schema validates (all 6 fields present on every row) |
| Y-06 | Every dep in lockfiles appears in ledger |

**Minimum 6 tests.** Gate letter: Y.

## Files to Read

- `docs/contracts/PUBLISHING_READINESS_SPEC.md` — §P4, §5 for license compliance
- `requirements.txt` / `pyproject.toml` — Current Python deps
- `package.json` — Current Node deps (if exists)

## Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

## Integration Seams

- Lint script logs to stdout (orchestrator captures to `RC_PACKET/p4_license_check.log`)
- Exit codes: 0 = PASS, 1 = FAIL
- Draft generator is a helper tool, not a gate script — no evidence logging required

## Assumptions to Validate

1. `requirements.txt` and/or `pyproject.toml` exist and are authoritative for Python deps
2. Project license decision (MIT/Apache/GPL) is not blocking this WO — ledger can be built now, compatibility check deferred

## Delivery Footer

Builder delivers: 1 gate script + 1 helper script + ledger + gate tests. Debrief in CODE format (500 words, 5 sections + Radar). Commit message references PRS-01 and gate letter Y.

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "License work order complete. Awaiting Thunder."
```
