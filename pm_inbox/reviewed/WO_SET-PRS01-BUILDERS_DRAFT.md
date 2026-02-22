# WO_SET: PRS-01 Builder Work Orders (5 of 6)
**Lifecycle:** DRAFT
**Date:** 2026-02-23
**Status:** DRAFT — Pending PRS-01 spec approval by Thunder
**Authority:** PRS-01 v1.0 (`docs/contracts/PUBLISHING_READINESS_SPEC.md`)
**Depends on:** PRS-01 spec FROZEN (Thunder approval of `MEMO_PRS01_REVIEW_BRIEF.md`)

---

## Overview

Five builder WOs implementing the scripts and artifacts required by PRS-01 publish gates P3-P9. These are **embarrassingly parallel** — no WO depends on any other. The 6th WO (orchestrator) is deferred until all 5 complete.

P1 (Clean Tree) and P2 (Full Test Suite) use existing tooling (`git status`, `pytest`) — no builder WO needed.

**Dispatch rule:** Thunder approves PRS-01 spec → Slate converts each section below into an individual `WO-*_DISPATCH.md` → Thunder dispatches to builders.

---

## WO-PRS-SCAN-001 — Asset Scan + Secret Scan + IP Scan

### Target Lock

Build three publish-gate scan scripts: P3 (asset scan), P5 (secret scan), P8 (IP string scan). One WO because all three are pattern-matching scans over the git tree with the same architecture: denylist + allowlist/exceptions + evidence log.

### Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | One script or three? | **Three separate scripts** — each gate logs to its own evidence file per §9.2. Shared utility module OK. |
| 2 | Image files in `docs/`? | **Allowed** — P3 spec says images in `docs/` are permitted for documentation. Script must respect this. |
| 3 | IP denylist source? | **Builder creates initial denylist** from non-OGL/SRD proper nouns. File: `scripts/ip_denylist.txt`. Thunder reviews before freeze. |
| 4 | Secret scan approach? | **Regex-based** — no external dependency. Scan for API key patterns, private key headers, token formats. Baseline file for known-safe patterns. |

### Contract Spec

**P3 — Asset Scan (`scripts/publish_scan_assets.py`):**
- Walk all tracked files (`git ls-files`)
- Check each file extension against allowlist (§3 of PRS-01: `.py`, `.ts`, `.tsx`, `.js`, `.json`, `.yaml`, `.yml`, `.toml`, `.md`, `.txt`, `.html`, `.css`, `.cfg`, `.ini`, `.sh`, `.bat`, `.ps1`, `Makefile`, `Dockerfile`, `.ahk`, `.gitignore`, `.gitattributes`, `LICENSE`, `NOTICE`)
- Check against blocklist (§3: `*.gguf`, `*.safetensors`, `*.bin`, `*.wav`, `*.mp3`, `*.ogg`, `*.flac`, `*.png`/`*.jpg`/etc outside `docs/`, `*.sqlite`, `*.db`, `*.pkl`, `*.pickle`, `*.cache`, `__pycache__/`, `node_modules/`, `weights/`, `models/`, `cache/`, `outputs/`, `recordings/`, `oracle_db/`, `image_cache/`, `audio_cache/`)
- Exit 0 if clean, exit 1 if violations found
- Log to stdout in machine-readable format (one line per finding)

**P5 — Secret Scan (`scripts/publish_secret_scan.py`):**
- Scan all tracked files for high-confidence secret patterns: API keys (`sk-`, `pk_`, `AKIA`, etc.), private key PEM headers, `password=`, `token=`, `secret=` assignments with literal values, base64-encoded blobs >40 chars in config files
- Baseline file: `scripts/secret_scan_baseline.txt` (builder creates with initial entries for test fixtures)
- Exclude `.git/`, binary files
- Exit 0 if no matches outside baseline, exit 1 otherwise

**P8 — IP Scan (`scripts/publish_scan_ip_terms.py`):**
- Scan all tracked `.py`, `.md`, `.txt`, `.ts`, `.tsx`, `.js` files for denylist terms
- Denylist: `scripts/ip_denylist.txt` — one term per line, case-insensitive match
- Exceptions: `scripts/ip_exceptions.txt` — format: `term|file_path|justification`
- Builder populates initial denylist with non-OGL proper nouns (setting names, deity names, faction names that are product identity, not SRD)
- Exit 0 if no matches outside exceptions, exit 1 otherwise

### Implementation Plan

1. Create shared utility: `scripts/_publish_scan_utils.py` — git ls-files wrapper, pattern matching, evidence logging
2. Implement `scripts/publish_scan_assets.py` with allowlist/blocklist from PRS-01 §3
3. Implement `scripts/publish_secret_scan.py` with regex patterns + baseline
4. Implement `scripts/publish_scan_ip_terms.py` with denylist/exceptions
5. Create initial `scripts/ip_denylist.txt` (non-OGL proper nouns — builder's best judgment, Thunder reviews)
6. Create initial `scripts/secret_scan_baseline.txt` (empty or with known test fixtures)
7. Create initial `scripts/ip_exceptions.txt` (empty — SRD terms are not on the denylist in the first place)
8. Run all three against current repo, document findings

### Gate Spec

**New test file:** `tests/test_publish_scan_gate_x.py` (Gate X)

| Test ID | What It Checks |
|---------|---------------|
| X-01 | `publish_scan_assets.py` exits 0 on current repo |
| X-02 | `publish_scan_assets.py` exits 1 when blocklist file is planted |
| X-03 | `publish_scan_assets.py` allows images in `docs/` |
| X-04 | `publish_secret_scan.py` exits 0 on current repo |
| X-05 | `publish_secret_scan.py` detects planted API key pattern |
| X-06 | `publish_secret_scan.py` respects baseline exclusions |
| X-07 | `publish_scan_ip_terms.py` exits 0 on current repo |
| X-08 | `publish_scan_ip_terms.py` detects planted denylist term |
| X-09 | `publish_scan_ip_terms.py` respects exceptions file |
| X-10 | All three scripts produce machine-readable output |

**Minimum 10 tests.** Gate letter: X (next available after W).

### Files to Read

- `docs/contracts/PUBLISHING_READINESS_SPEC.md` — §3 (P3), §3 (P5), §3 (P8) for exact patterns
- `scripts/check_cli_grammar.py` — Example of existing scan script pattern
- `.gitignore` — Current ignore patterns (inform allowlist)

### Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

### Integration Seams

- Scripts must log to stdout (orchestrator captures to `RC_PACKET/` in WO-PRS-ORCHESTRATOR-001)
- Exit codes: 0 = PASS, 1 = FAIL (standard for all PRS-01 scripts)
- All scan patterns must match PRS-01 §3 exactly — if the spec says `*.gguf`, the script checks `*.gguf`

### Delivery Footer

Builder delivers: 3 scripts + 3 data files + gate tests. Debrief in CODE format (500 words, 5 sections + Radar). Commit message references PRS-01 and gate letter X.

---

## WO-PRS-LICENSE-001 — License Ledger + Lint

### Target Lock

Build the P4 license compliance system: a ledger documenting every dependency with SPDX license identifiers, and a lint script that validates the ledger against actual lockfiles.

### Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Ledger format? | **Markdown table** — `docs/LICENSE_LEDGER.md` per PRS-01 §P4 schema |
| 2 | Include dev-only deps? | **Yes** — PRS-01 requires all deps documented. `redistribution` field distinguishes `dev-only` from `runtime-dep` |
| 3 | Auto-generate or manual? | **Script generates draft from lockfiles**, builder reviews and fills `where_used` field manually |
| 4 | Project license TBD? | **Yes** — ledger tracks deps regardless. Compatibility check deferred until Thunder picks a license. Script warns if UNKNOWN license found. |

### Contract Spec

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

### Implementation Plan

1. Inventory all dependency sources: `requirements.txt`, `pyproject.toml`, `package.json`/`package-lock.json`
2. Build draft generator that extracts dep names + versions
3. Manually fill license + source_url + redistribution + where_used for each dep
4. Build lint script that validates ledger against lockfiles
5. Run lint, resolve any gaps

### Gate Spec

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

### Files to Read

- `docs/contracts/PUBLISHING_READINESS_SPEC.md` — §P4, §5 for license compliance
- `requirements.txt` / `pyproject.toml` — Current Python deps
- `package.json` — Current Node deps (if exists)

### Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

### Integration Seams

- Lint script logs to stdout (orchestrator captures to `RC_PACKET/p4_license_check.log`)
- Exit codes: 0 = PASS, 1 = FAIL
- Draft generator is a helper tool, not a gate script — no evidence logging required

### Delivery Footer

Builder delivers: 1 gate script + 1 helper script + ledger + gate tests. Debrief in CODE format. Commit message references PRS-01 and gate letter Y.

---

## WO-PRS-OFFLINE-001 — Offline Guarantee

### Target Lock

Build the P6 offline guarantee enforcement: a static scan for ungated network client imports, and a runtime smoke test verifying zero outbound connections in default config.

### Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Static scan scope? | **Python + TypeScript source** — scan for `socket`, `requests`, `urllib`, `http.client`, `fetch`, `axios`, `XMLHttpRequest` per PRS-01 §P6 |
| 2 | Runtime smoke approach? | **Import-level mock** — monkey-patch `socket.socket` to fail on `connect()`, then run default startup path. If no socket error, offline guarantee holds. No external network monitor needed. |
| 3 | Opt-in gate pattern? | **Config key check** — network imports are permitted only inside code blocks guarded by an explicit opt-in config flag that defaults to `False`/`off`. Static scan checks for this pattern. |
| 4 | Exceptions file? | **Yes** — `scripts/offline_exceptions.txt` for known-safe imports (e.g., `socket` used only for local IPC, not outbound) |

### Contract Spec

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

### Implementation Plan

1. Identify all network-related imports in the codebase (baseline scan)
2. Build static scanner with pattern matching + opt-in guard detection
3. Build runtime smoke with socket monkey-patch
4. Create `scripts/offline_exceptions.txt` with any legitimate local-only uses
5. Run both scripts, document findings

### Gate Spec

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

### Files to Read

- `docs/contracts/PUBLISHING_READINESS_SPEC.md` — §P6, §6 for offline guarantee
- `aidm/` — Core package to understand import structure
- `config/` — Default config to understand opt-in flags

### Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

### Integration Seams

- Static scan logs to `RC_PACKET/p6_offline_static.log` (via orchestrator)
- Runtime smoke logs to `RC_PACKET/p6_offline_runtime.log` (via orchestrator)
- Exit codes: 0 = PASS, 1 = FAIL

### Delivery Footer

Builder delivers: 2 scripts + 1 exceptions file + gate tests. Debrief in CODE format. Commit message references PRS-01 and gate letter Z.

---

## WO-PRS-FIRSTRUN-001 — Fail-Closed First Run

### Target Lock

Build the P7 fail-closed first run test: verify that when required runtime assets (model weights, TTS voices) are missing, the application produces a deterministic error message and halts. No silent fallback.

### Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | What assets are required? | **Model weights (Qwen2.5 GGUF)** and **TTS voice models (Kokoro)**. Builder inventories actual required paths by tracing startup. |
| 2 | Test environment? | **Temp directory with clean config** — copy config but not weights/voices. Run startup. Expect error + halt. |
| 3 | Error message format? | **Must name the missing asset and suggest where to obtain it** per PRS-01 §P7. Builder validates message content, not just exit code. |
| 4 | Partial startup allowed? | **No** — per PRS-01 §P7: "No partial output is generated before the error." Script checks for clean halt. |

### Contract Spec

**`scripts/publish_first_run_missing_weights.py`:**
- Create a temporary working environment (temp dir or env vars) where model weight paths resolve to empty/missing locations
- Attempt to start the application's core initialization path
- Verify:
  1. Application exits with non-zero exit code
  2. Error output names the missing asset (e.g., "Model not found: ...")
  3. Error output suggests where to obtain it (e.g., "Download from ...")
  4. No partial output is generated before the error
- Exit 0 if all checks pass (application correctly fails closed), exit 1 if application silently starts or hangs

### Implementation Plan

1. Trace application startup path to identify all required runtime assets
2. Document required asset paths and their expected locations
3. Build test script that removes/redirects asset paths
4. Verify fail-closed behavior: deterministic error + halt
5. Verify error message quality: names asset, suggests resolution

### Gate Spec

**New test file:** `tests/test_publish_firstrun_gate_aa.py` (Gate AA)

| Test ID | What It Checks |
|---------|---------------|
| AA-01 | Script exits 0 when run (meaning: app correctly fails closed) |
| AA-02 | Missing model weights produce actionable error message |
| AA-03 | Missing TTS voices produce actionable error message |
| AA-04 | Error message names the specific missing asset |
| AA-05 | Application exits with non-zero code when assets missing |
| AA-06 | No partial output before error |

**Minimum 6 tests.** Gate letter: AA.

### Files to Read

- `docs/contracts/PUBLISHING_READINESS_SPEC.md` — §P7
- `aidm/runtime/session_orchestrator.py` — Startup path, asset loading
- `aidm/voice/` — TTS initialization, voice model loading
- `config/` — Default config, asset path definitions

### Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

### Integration Seams

- Script logs to `RC_PACKET/p7_first_run.log` (via orchestrator)
- Exit code semantics: 0 = app correctly fails closed (PASS), 1 = app silently starts or hangs (FAIL)
- Note the inverted semantics: the *publish gate* passes when the *application* fails (correctly)

### Delivery Footer

Builder delivers: 1 script + gate tests. Debrief in CODE format. Commit message references PRS-01 and gate letter AA.

---

## WO-PRS-DOCS-001 — Privacy Statement + OGL Notice + Doc Validator

### Target Lock

Build the P9 documentation compliance system: create the privacy statement (`docs/PRIVACY.md`), add the OGL notice, and build a validator script that ensures required sections exist and referenced paths are valid.

### Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Privacy statement scope? | **Per PRS-01 §7** — data locality, microphone handling, retention defaults, deletion instructions. All from the spec. |
| 2 | OGL notice location? | **`docs/OGL_NOTICE.md`** — standalone file. Also referenced from README. |
| 3 | Validator approach? | **Section heading detection + path existence check** — parse `docs/PRIVACY.md` for required sections, verify all referenced file paths exist on disk. |
| 4 | Deletion path validation? | **Yes** — validator checks that paths mentioned in "Delete Everything" section correspond to actual directories in the project structure. |

### Contract Spec

**`docs/PRIVACY.md` (builder creates):**
- Must contain all 4 required sections per PRS-01 §P9:
  1. **Data locality** — all data local, no telemetry, no cloud sync
  2. **Microphone** — opt-in only, not default, local processing, no retention unless user opts in
  3. **Retention defaults** — table per PRS-01 §7.3 (session logs, oracle state, audio cache, image cache, config)
  4. **Deletion instructions** — per PRS-01 §7.4 (specific directories to delete)
- All referenced paths must exist in repo structure

**`docs/OGL_NOTICE.md` (builder creates):**
- Standard OGL v1.0a notice
- Section 15 lists this project as a derivative work of the SRD
- References the SRD as the source of game mechanic content

**`scripts/publish_check_docs.py`:**
- Parse `docs/PRIVACY.md` — verify all 4 required section headings present
- Extract all file/directory paths referenced in the document
- Verify each referenced path exists (relative to project root)
- Check `docs/OGL_NOTICE.md` exists
- Exit 0 if all checks pass, exit 1 otherwise
- Log findings to stdout

### Implementation Plan

1. Draft `docs/PRIVACY.md` from PRS-01 §7 content
2. Draft `docs/OGL_NOTICE.md` with standard OGL v1.0a text
3. Build validator script
4. Run validator, resolve any path mismatches

### Gate Spec

**New test file:** `tests/test_publish_docs_gate_ab.py` (Gate AB)

| Test ID | What It Checks |
|---------|---------------|
| AB-01 | `publish_check_docs.py` exits 0 on current repo (after docs created) |
| AB-02 | Validator detects missing privacy section (planted) |
| AB-03 | Validator detects invalid path reference (planted) |
| AB-04 | `docs/PRIVACY.md` exists and has all 4 required sections |
| AB-05 | `docs/OGL_NOTICE.md` exists |
| AB-06 | All paths referenced in PRIVACY.md exist |

**Minimum 6 tests.** Gate letter: AB.

### Files to Read

- `docs/contracts/PUBLISHING_READINESS_SPEC.md` — §P9, §7 for privacy posture
- `docs/` — Existing docs structure
- Project root — Directory structure for path validation

### Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

### Integration Seams

- Validator logs to `RC_PACKET/p9_docs_check.log` (via orchestrator)
- Exit codes: 0 = PASS, 1 = FAIL
- Privacy statement content comes from PRS-01 §7 — builder should transcribe, not invent

### Delivery Footer

Builder delivers: 2 docs + 1 validator script + gate tests. Debrief in CODE format. Commit message references PRS-01 and gate letter AB.

---

## 6th WO — Deferred

**WO-PRS-ORCHESTRATOR-001** (RC packet builder) depends on all 5 WOs above completing. It wires `scripts/build_release_candidate_packet.py` per PRS-01 §9. Will be drafted after all scan WOs are accepted.

---

## Dispatch Sequence

All 5 WOs above are independent. Thunder can dispatch all 5 simultaneously to separate builders, or stagger as builder bandwidth allows.

| WO | Gate | Parallel? | Est. Tests |
|----|------|-----------|------------|
| WO-PRS-SCAN-001 | X | Yes | ~10 |
| WO-PRS-LICENSE-001 | Y | Yes | ~6 |
| WO-PRS-OFFLINE-001 | Z | Yes | ~6 |
| WO-PRS-FIRSTRUN-001 | AA | Yes | ~6 |
| WO-PRS-DOCS-001 | AB | Yes | ~6 |
| WO-PRS-ORCHESTRATOR-001 | (after all) | No | TBD |

**Total new gate tests (est.):** ~34 across gates X, Y, Z, AA, AB.

---

## Assumptions to Validate

1. PRS-01 spec is approved before any of these dispatch
2. Gate letters X, Y, Z, AA, AB are available (no conflicts with other planned gates)
3. `scripts/` directory is the correct location for publish scripts (consistent with existing scripts)
4. Project license decision (MIT/Apache/GPL) is not blocking WO-PRS-LICENSE-001 — ledger can be built with the license field, compatibility check deferred

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Five work orders drafted. Awaiting Thunder."
```
