# WO-PRS-SCAN-FIX-001 — Gate X False Positive Fixes
**Lifecycle:** NEW
**Date:** 2026-02-23
**Type:** BUG
**Authority:** PRS-01 v1.0 FROZEN (`docs/contracts/PUBLISHING_READINESS_SPEC.md`)
**Gate:** X (existing — raise to 10/10)
**Parent:** WO-PRS-SCAN-001 (ACCEPTED with FINDING-SCAN-BASELINE-01)

---

## Target Lock

Fix the 2 failing Gate X tests (X-01 asset scan, X-04 secret scan) caused by false positives in the P3 asset scanner and P5 secret scanner. No architectural changes — config-level fixes only.

## Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | How to exclude `package-lock.json` from BASE64-BLOB? | **File-level skip list in secret scanner.** Add `SECRET_SCAN_SKIP_FILES` set. Do NOT use per-line baseline — npm integrity hashes produce hundreds of matches and line numbers shift. |
| 2 | How to exclude `config/REUSE_DECISION.json` from BASE64-BLOB? | **Same file-level skip list.** REUSE_DECISION.json contains base64-encoded image thumbnails for reuse decisions — not secrets. |
| 3 | How to handle `.jsonl` files in P3? | **Add `*.jsonl` to `ALLOWLIST_EXTENSIONS`.** These are test fixtures (`tests/fixtures/`) and playtest logs — legitimate source artifacts. |
| 4 | How to handle `models/` directory in P3? | **Leave as-is.** The scanner correctly flags tracked audio/model files. This is a real finding for pre-publish cleanup, not a false positive. Do NOT suppress. Track separately as a pre-RC task (untrack `models/` and add to `.gitignore`). |
| 5 | How to handle `.png` in `pm_inbox/reviewed/`? | **Add `pm_inbox/reviewed/` to asset scan exceptions** OR accept that experimental artifacts are flagged. Decision: **Leave as-is** — this is a real finding. The `.png` should be removed or untracked before publishing. |

## Contract Spec

**Changes to `scripts/publish_secret_scan.py`:**
```python
# File-level skip list for BASE64-BLOB pattern
# These files contain legitimate base64 data (npm integrity hashes, image thumbnails)
SECRET_SCAN_SKIP_FILES = {
    "client/package-lock.json",
    "config/REUSE_DECISION.json",
}
```
In `scan_secrets()`, before scanning for BASE64-BLOB pattern, check if the file path is in `SECRET_SCAN_SKIP_FILES`. If so, skip the BASE64-BLOB pattern only (still scan for API keys, PEM headers, etc.).

**Changes to `scripts/publish_scan_assets.py`:**
```python
ALLOWLIST_EXTENSIONS = [
    # ... existing entries ...
    "*.jsonl",  # Test fixtures and playtest logs
]
```

**No changes to:**
- `_publish_scan_utils.py` (shared utilities)
- `scripts/publish_scan_ip_terms.py` (P8 — already passing)
- `scripts/secret_scan_baseline.txt` (leave empty — file-level skip is better)
- Test files (existing tests should pass with scanner fixes)

## Implementation Plan

1. Add `SECRET_SCAN_SKIP_FILES` to `publish_secret_scan.py`
2. Wire the skip check into `scan_secrets()` — skip BASE64-BLOB only, not other patterns
3. Add `*.jsonl` to `ALLOWLIST_EXTENSIONS` in `publish_scan_assets.py`
4. Run Gate X tests — expect 10/10 PASS
5. Run full preflight

## Gate Spec

**No new tests.** The existing 10 Gate X tests cover all cases. The fix should make X-01 and X-04 pass (currently failing). Target: 10/10.

Verify:
- X-01: asset scan passes on current repo (`.jsonl` now on allowlist)
- X-04: secret scan passes on current repo (`package-lock.json` and `REUSE_DECISION.json` skipped for BASE64-BLOB)
- X-02 through X-10: no regressions

## Files to Read

- `scripts/publish_secret_scan.py` — current secret scan logic, add skip list
- `scripts/publish_scan_assets.py` — current asset scan, add `.jsonl` to allowlist
- `tests/test_publish_scan_gate_x.py` — existing gate tests (10 total)

## Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

## Integration Seams

- Exit codes unchanged (0 = PASS, 1 = FAIL)
- Scanner output format unchanged (machine-readable, captured by future RC orchestrator)
- No new dependencies

## Assumptions to Validate

1. `client/package-lock.json` contains only npm integrity hashes (SHA-512 base64) — not secrets
2. `config/REUSE_DECISION.json` contains base64 image thumbnails — not secrets
3. Adding `.jsonl` to allowlist doesn't inadvertently allow unwanted binary artifacts

## Delivery Footer

Builder delivers: 2 modified scripts. No new files. Debrief in CODE format (500 words, 5 sections + Radar). Gate X target: 10/10.

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Scan fix complete. Awaiting Thunder."
```
