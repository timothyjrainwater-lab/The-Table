# WO-PRS-SCAN-001 — Asset Scan + Secret Scan + IP Scan
**Lifecycle:** NEW
**Date:** 2026-02-23
**Type:** FEATURE
**Authority:** PRS-01 v1.0 FROZEN (`docs/contracts/PUBLISHING_READINESS_SPEC.md`)
**Gate:** X (new)

---

## Target Lock

Build three publish-gate scan scripts: P3 (asset scan), P5 (secret scan), P8 (IP string scan). One WO because all three are pattern-matching scans over the git tree with the same architecture: denylist + allowlist/exceptions + evidence log.

## Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | One script or three? | **Three separate scripts** — each gate logs to its own evidence file per §9.2. Shared utility module OK. |
| 2 | Image files in `docs/`? | **Allowed** — P3 spec says images in `docs/` are permitted for documentation. Script must respect this. |
| 3 | IP denylist source? | **Builder creates initial denylist** from non-OGL/SRD proper nouns. File: `scripts/ip_denylist.txt`. Thunder reviews before freeze. |
| 4 | Secret scan approach? | **Regex-based** — no external dependency. Scan for API key patterns, private key headers, token formats. Baseline file for known-safe patterns. |

## Contract Spec

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

## Implementation Plan

1. Create shared utility: `scripts/_publish_scan_utils.py` — git ls-files wrapper, pattern matching, evidence logging
2. Implement `scripts/publish_scan_assets.py` with allowlist/blocklist from PRS-01 §3
3. Implement `scripts/publish_secret_scan.py` with regex patterns + baseline
4. Implement `scripts/publish_scan_ip_terms.py` with denylist/exceptions
5. Create initial `scripts/ip_denylist.txt` (non-OGL proper nouns — builder's best judgment, Thunder reviews)
6. Create initial `scripts/secret_scan_baseline.txt` (empty or with known test fixtures)
7. Create initial `scripts/ip_exceptions.txt` (empty — SRD terms are not on the denylist in the first place)
8. Run all three against current repo, document findings

## Gate Spec

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

## Files to Read

- `docs/contracts/PUBLISHING_READINESS_SPEC.md` — §3 (P3), §3 (P5), §3 (P8) for exact patterns
- `scripts/check_cli_grammar.py` — Example of existing scan script pattern
- `.gitignore` — Current ignore patterns (inform allowlist)

## Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

## Integration Seams

- Scripts must log to stdout (orchestrator captures to `RC_PACKET/` in WO-PRS-ORCHESTRATOR-001)
- Exit codes: 0 = PASS, 1 = FAIL (standard for all PRS-01 scripts)
- All scan patterns must match PRS-01 §3 exactly — if the spec says `*.gguf`, the script checks `*.gguf`

## Assumptions to Validate

1. `scripts/` directory is the correct location for publish scripts (consistent with existing scripts)
2. Gate letter X is available (no conflicts)
3. `.gitignore` already covers blocklist patterns (first line of defense per PRS-01 §4.1)

## Delivery Footer

Builder delivers: 3 scripts + 1 shared utility + 3 data files + gate tests. Debrief in CODE format (500 words, 5 sections + Radar). Commit message references PRS-01 and gate letter X.

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Scan work order complete. Awaiting Thunder."
```
