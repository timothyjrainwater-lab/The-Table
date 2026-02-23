# WO-PRS-ORCHESTRATOR-001 — RC Packet Builder

**Issued:** 2026-02-23
**Authority:** PRS-01 §9 (RC Evidence Packet)
**Gate:** P-ORC (orchestrator — runs P1-P9, produces RC_PACKET)
**Blocked by:** All scan WOs complete ✅ (Y/Z/AA/X/AB all accepted, Gate X 10/10)

---

## 1. Target Lock

Implement `scripts/build_release_candidate_packet.py` — the RC orchestrator script specified in PRS-01 §9.1.

**Exact behavior per spec:**
1. Creates `RC_PACKET/` directory (or clears existing contents)
2. Runs P1 through P9 in sequence, capturing stdout/stderr to log files
3. Generates `RC_PACKET/MANIFEST.md` with commit hash, date, and per-gate PASS/FAIL
4. Exits code 0 if all gates PASS, code 1 if any gate FAILS

**Output packet structure (§9.2):**
```
RC_PACKET/
├── MANIFEST.md
├── p1_clean_tree.log
├── p2_test_results.log
├── p3_asset_scan.log
├── p4_license_check.log
├── p5_secret_scan.log
├── p6_offline_static.log
├── p6_offline_runtime.log
├── p7_first_run.log
├── p8_ip_scan.log
├── p9_docs_check.log
└── known_failures.txt
```

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | P1 implementation | `git status --porcelain` exit non-zero if output | No script exists — inline in orchestrator |
| 2 | P2 implementation | `pytest tests/ --tb=no -q` with known-failures exclusions | Same flags used in preflight |
| 3 | P2 known failures | Copy `tests/known_failures.txt` if exists, else write list of pre-existing failures | Baseline the 6 pre-existing skipped tests |
| 4 | Gate fail behavior | Continue running all gates on failure (don't short-circuit) | Capture full picture in one pass |
| 5 | RC_PACKET location | Repo root `RC_PACKET/` | Per §9.2 spec |
| 6 | RC_PACKET in .gitignore | Yes — add `RC_PACKET/` to .gitignore | Generated artifact, not source |
| 7 | MANIFEST.md format | Markdown table: Gate / Status / Log file / Notes | Machine-readable + human-readable |
| 8 | Timestamp | UTC via `datetime.utcnow()` | WSM-01 protocol: UTC is truth |

---

## 3. Contract Spec

### 3.1 Gate Mapping

| Gate | Command | Log file |
|---|---|---|
| P1 Clean Tree | `git status --porcelain` → PASS if empty | `p1_clean_tree.log` |
| P2 Test Suite | `pytest tests/ -q --tb=no` (with ignores for collection errors) | `p2_test_results.log` |
| P3 Asset Scan | `python scripts/publish_scan_assets.py` | `p3_asset_scan.log` |
| P4 License Check | `python scripts/publish_check_licenses.py` | `p4_license_check.log` |
| P5 Secret Scan | `python scripts/publish_secret_scan.py` | `p5_secret_scan.log` |
| P6 Offline Static | `python scripts/publish_scan_network_calls.py` | `p6_offline_static.log` |
| P6 Offline Runtime | `python scripts/publish_smoke_no_network.py` | `p6_offline_runtime.log` |
| P7 First Run | `python scripts/publish_first_run_missing_weights.py` | `p7_first_run.log` |
| P8 IP Scan | `python scripts/publish_scan_ip_terms.py` | `p8_ip_scan.log` |
| P9 Docs Check | `python scripts/publish_check_docs.py` | `p9_docs_check.log` |

### 3.2 MANIFEST.md Schema

```markdown
# RC Packet Manifest

**Commit:** <git rev-parse HEAD>
**Date:** <UTC ISO-8601>
**Result:** PASS / FAIL

## Gate Results

| Gate | Status | Log | Notes |
|------|--------|-----|-------|
| P1 Clean Tree | PASS | p1_clean_tree.log | |
| P2 Test Suite | PASS | p2_test_results.log | N passed, M failed (see known_failures.txt) |
| P3 Asset Scan | PASS | p3_asset_scan.log | |
| P4 License Check | PASS | p4_license_check.log | |
| P5 Secret Scan | PASS | p5_secret_scan.log | |
| P6 Offline Static | PASS | p6_offline_static.log | |
| P6 Offline Runtime | PASS | p6_offline_runtime.log | |
| P7 First Run | PASS | p7_first_run.log | |
| P8 IP Scan | PASS | p8_ip_scan.log | |
| P9 Docs Check | PASS | p9_docs_check.log | |

## Known Failures

<contents of known_failures.txt>
```

### 3.3 known_failures.txt

Document the 6 pre-existing test failures that are expected and not blocking:
- `tests/test_speak_signal.py` (2 failures — TTS env not provisioned)
- `tests/test_pm_inbox_hygiene.py` (3 failures — PM tooling tests)
- `tests/test_graduated_critique_orchestrator.py` (1 failure)
- Collection errors: `test_heuristics_image_critic.py`, `test_ws_bridge.py`

P2 PASS criteria: all gate failures are in `known_failures.txt`. Any failure outside that list = P2 FAIL.

### 3.4 P1 Logic

```python
result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
is_clean = result.stdout.strip() == ""
# PASS if clean tree. FAIL if any uncommitted changes.
```

Note: untracked files (`??`) also count as dirty. The tree must be fully committed before RC packet is valid.

---

## 4. Implementation Plan

### Step 1: Script skeleton
Create `scripts/build_release_candidate_packet.py` with:
- Argument parsing: optional `--output-dir` (default `RC_PACKET/`)
- Directory creation/clearing logic
- Gate runner function: `run_gate(name, cmd, log_file) -> (passed, output)`
- Sequential gate execution P1-P9
- MANIFEST.md generation
- Exit code logic

### Step 2: P1 implementation
Inline git clean-tree check. Log output + status.

### Step 3: P2 implementation
Run pytest with `--ignore` flags for known collection-error files:
```
--ignore=tests/test_heuristics_image_critic.py
--ignore=tests/test_ws_bridge.py
--ignore=tests/test_graduated_critique_orchestrator.py
--ignore=tests/test_immersion_authority_contract.py
--ignore=tests/test_pm_inbox_hygiene.py
--ignore=tests/test_speak_signal.py
```
Parse output for pass/fail count. P2 PASS = exit code 0 from pytest OR all failures in baseline.

### Step 4: P3-P9 implementation
Each gate: `subprocess.run(cmd, capture_output=True, text=True)`. Exit code 0 = PASS.

### Step 5: MANIFEST.md generation
Write after all gates complete. Include commit hash, UTC timestamp, per-gate table, known_failures content.

### Step 6: .gitignore update
Add `RC_PACKET/` to `.gitignore`.

### Step 7: Smoke test
Run `python scripts/build_release_candidate_packet.py` on current repo. All gates should PASS (or fail only on P1 if tree is dirty — acceptable during dev).

---

## 5. Deliverables Checklist

- [ ] `scripts/build_release_candidate_packet.py` — orchestrator script
- [ ] `RC_PACKET/` added to `.gitignore`
- [ ] Script runs cleanly: `python scripts/build_release_candidate_packet.py`
- [ ] `RC_PACKET/MANIFEST.md` generated with correct structure
- [ ] All 10 log files present after run
- [ ] Exit 0 if all gates PASS, exit 1 if any FAIL
- [ ] P1 correctly detects dirty tree (unit test or manual verify)
- [ ] known_failures.txt documents pre-existing failures

---

## 6. Integration Seams

- Calls all 9 existing `publish_*.py` scripts — no changes to those scripts
- Reads `git rev-parse HEAD` for commit hash — requires git in PATH
- Ignores same test files as preflight for P2
- `RC_PACKET/` must be added to `.gitignore` before first commit post-WO
- Does NOT run on CI automatically — operator-triggered before tagging a release

---

## 7. Assumptions to Validate

1. `git` is available in PATH in the venv context — verify with `git --version`
2. P2 with all ignores produces 0 gate failures on current tree — verify before submitting
3. `publish_smoke_no_network.py` accepts no arguments (currently exits 0 on current tree) — verify
4. `publish_first_run_missing_weights.py` exits 0 on current tree — verify (weights absent = FAIL, but gate is "fail-closed" so this may be expected FAIL)

---

## 8. Preflight

Before marking complete, run:
```bash
python scripts/build_release_candidate_packet.py
cat RC_PACKET/MANIFEST.md
```

All gates should show PASS except possibly P1 (dirty tree — new files untracked) and P7 (first-run check requires model weights absent to pass). Confirm exit code matches manifest result.

---

## 9. Debrief Focus

1. **P2 baseline logic** — how did you handle the known-failures pass/fail determination? Exact logic matters.
2. **P7 gate result** — did `publish_first_run_missing_weights.py` PASS or FAIL on current tree, and why?

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
