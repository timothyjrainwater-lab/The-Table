# Publishing Readiness Spec (PRS-01)
## Open-Source Release Gate Contract

**Document ID:** PRS-01
**Version:** 1.0
**Date:** 2026-02-19
**Status:** FROZEN (v1.0 ACCEPTED — Thunder approved 2026-02-23)
**Authority:** This document is the canonical contract for publishing readiness. No release occurs until all gates in this document PASS on a signed commit and the RC evidence packet exists and matches that commit exactly.
**Scope:** Release surface definition, publish gates (P1-P9), artifact hygiene, license compliance, offline guarantee, IP hygiene, privacy posture, and donation policy.

**Origin:** Aegis (GPT) audit memo dated 2026-02-19, normalized by Slate (PM) with Thunder decisions.

**Relationship to BURST-001:** Parallel track. PRS-01 does not block BURST-001 voice reliability work. BURST-001 does not block PRS-01. Neither depends on the other for gate passage.

---

## 1. Public Surfaces (Exhaustive)

The project publishes exactly these surfaces. Anything not listed here is private.

| Surface | Posture | Notes |
|---------|---------|-------|
| **GitHub repository** | PUBLIC | Source code, docs, configs, tests. The primary distribution channel. |
| **GitHub Releases** | YES — tagged releases | Each release includes an RC evidence packet (see §9). Provides stable snapshots, reduces "repo head is the release" ambiguity. |
| **Donation links** | PRESENT, GATED | Links go live only when P1-P9 PASS on a tagged release. Until then, absent. Donations are optional, decoupled from access, non-transactional. No promise of paid features. |
| **Operational artifacts** | CURATED | Templates, exemplary dispatches/debriefs, and a snapshot pack tied to releases. Full pm_inbox is not published. See §8. |

---

## 2. Ship Posture

**What the repo ships:** Source code (Python + TypeScript), documentation, configuration files, tests, and scripts.

**What the repo does NOT ship:** Model weights, audio files, image caches, generated outputs, local databases, recordings, or any binary asset that requires a license beyond the repo's own license.

**Runtime model:** Offline-first. The application runs without network access in default configuration. Any network-dependent feature must be explicitly opt-in and default-off.

**License model:** Open-source (license TBD — to be resolved before first tagged release). Optional donations. No storefront. No paid tiers.

---

## 3. Publish Gates (P1-P9)

Every gate must PASS on the release commit. Gates are executed by a single orchestrator script (§9) and produce machine-readable evidence.

### P1: Clean Tree

**Requirement:** No uncommitted changes, no untracked files outside `.gitignore`.

**Command:** `git status --porcelain`

**Pass criteria:** Output is empty.

**Evidence:** Command output logged to `RC_PACKET/p1_clean_tree.log`.

---

### P2: Full Test Suite + Gate Tests

**Requirement:** All unit tests and all gate tests pass.

**Command:** `pytest` (full suite including gate tests)

**Pass criteria:** Exit code 0. Zero failures. Pre-existing known failures must be explicitly listed in a baseline file (`tests/known_failures.txt`) and may not grow between releases.

**Evidence:** Pytest output logged to `RC_PACKET/p2_test_results.log`. Known failures baseline copied to packet.

---

### P3: No Shipped Artifacts Scan

**Requirement:** Repository contains no files matching the blocklist patterns.

**Command:** `scripts/publish_scan_assets.py`

**Allowlist (patterns permitted):**
- `*.py`, `*.ts`, `*.tsx`, `*.js`, `*.json`, `*.yaml`, `*.yml`, `*.toml`
- `*.md`, `*.txt`, `*.html`, `*.css`
- `*.cfg`, `*.ini`, `*.sh`, `*.bat`, `*.ps1`
- `Makefile`, `Dockerfile`, `*.dockerfile`
- `.gitignore`, `.gitattributes`, `LICENSE`, `NOTICE`
- `*.ahk` (AutoHotkey operator tooling)

**Blocklist (patterns forbidden):**
- `*.gguf`, `*.safetensors`, `*.bin` (model weights)
- `*.wav`, `*.mp3`, `*.ogg`, `*.flac` (audio files)
- `*.png`, `*.jpg`, `*.jpeg`, `*.gif`, `*.bmp`, `*.webp` (image files, unless in `docs/` for documentation)
- `*.sqlite`, `*.db`, `*.sqlite3` (databases)
- `*.pkl`, `*.pickle` (serialized objects)
- `*.cache`, `__pycache__/`, `.cache/`, `node_modules/`
- `weights/`, `models/`, `cache/`, `outputs/`, `recordings/`, `oracle_db/`, `image_cache/`, `audio_cache/`

**Pass criteria:** Zero blocklist matches. Allowlist violations require manual review.

**Evidence:** Scan output logged to `RC_PACKET/p3_asset_scan.log`.

---

### P4: License Ledger Complete

**Requirement:** Every dependency (Python + Node) is documented with license type and redistribution posture.

**Command:** `scripts/publish_check_licenses.py`

**Ledger schema** (`docs/LICENSE_LEDGER.md` or `.csv`):

| Field | Required | Description |
|-------|----------|-------------|
| `dependency` | YES | Package name |
| `version` | YES | Pinned version |
| `license` | YES | SPDX identifier (e.g., `MIT`, `Apache-2.0`) |
| `source_url` | YES | PyPI/npm/GitHub URL |
| `redistribution` | YES | `bundled` / `runtime-dep` / `dev-only` |
| `where_used` | YES | Module or subsystem that imports it |

**Pass criteria:** No `UNKNOWN` licenses. All deps in lockfiles are represented. Ledger schema validates (all required fields present).

**Evidence:** Ledger validation output logged to `RC_PACKET/p4_license_check.log`.

---

### P5: Secret Scan

**Requirement:** No high-confidence secrets (API keys, tokens, passwords, private keys) in tracked files.

**Command:** `scripts/publish_secret_scan.py`

**Scan scope:** All tracked files in the repository.

**Baseline:** `scripts/secret_scan_baseline.txt` — known-safe patterns (test hashes, fixture values, example tokens in documentation). Patterns in baseline are excluded from failure.

**Pass criteria:** Zero high-confidence matches outside baseline.

**Evidence:** Scan output logged to `RC_PACKET/p5_secret_scan.log`.

---

### P6: Offline Guarantee

**Requirement:** Default configuration makes zero outbound network connections.

**Static scan:**
**Command:** `scripts/publish_scan_network_calls.py`
**Method:** Scan Python and TypeScript source for network client imports and connection patterns (`socket`, `requests`, `urllib`, `http.client`, `fetch`, `axios`, `XMLHttpRequest`). Flag any usage not behind an explicit opt-in configuration gate that defaults to off.

**Runtime smoke:**
**Command:** `scripts/publish_smoke_no_network.py`
**Method:** Run the application's default startup path with network monitoring. Verify zero outbound socket connections.

**Pass criteria:** Static scan finds no ungated network clients. Runtime smoke records zero outbound connections.

**Evidence:** Both scan outputs logged to `RC_PACKET/p6_offline_static.log` and `RC_PACKET/p6_offline_runtime.log`.

---

### P7: Fail-Closed First Run

**Requirement:** When required runtime assets (model weights, TTS voices) are missing, the application produces a deterministic error message and halts. No silent fallback, no partial startup, no hang.

**Command:** `scripts/publish_first_run_missing_weights.py`

**Method:** Run the application in a clean environment with no model weights present. Verify:
1. Application exits with non-zero exit code.
2. Error message names the missing asset and suggests where to obtain it.
3. No partial output is generated before the error.

**Pass criteria:** Deterministic error + halt. Exit code non-zero. Error message is actionable.

**Evidence:** Output logged to `RC_PACKET/p7_first_run.log`.

---

### P8: IP String Hygiene

**Requirement:** No trademarked or copyrighted proper nouns from game system IP appear in published source, docs, or tests outside an explicit exceptions list.

**Command:** `scripts/publish_scan_ip_terms.py`

**Denylist:** Maintained in `scripts/ip_denylist.txt`. Contains proper nouns, product names, and setting-specific terms that are not part of the OGL/SRD.

**Exceptions:** Maintained in `scripts/ip_exceptions.txt`. Each exception includes the term, the file where it appears, and a justification (e.g., "SRD-licensed term", "generic English word").

**Pass criteria:** Zero denylist matches outside exceptions list.

**Evidence:** Scan output logged to `RC_PACKET/p8_ip_scan.log`.

---

### P9: Privacy/Storage Statement Present + Accurate

**Requirement:** A privacy statement exists, covers all data-handling paths, and references actual file paths that exist.

**Command:** `scripts/publish_check_docs.py`

**Required sections in privacy statement (`docs/PRIVACY.md`):**
1. **Data locality:** All data stored locally. No telemetry. No cloud sync.
2. **Microphone:** Opt-in only. Not enabled by default. Audio is processed locally and not retained after transcription unless user explicitly enables recording.
3. **Retention defaults:** What is stored, where, and for how long.
4. **Deletion instructions:** How to remove all user data. Must reference actual directory paths that exist in the repo structure.

**Pass criteria:** All required sections present. All referenced file paths exist. Deletion instructions are testable.

**Evidence:** Doc validation output logged to `RC_PACKET/p9_docs_check.log`.

---

## 4. Artifact Hygiene

### 4.1 .gitignore Contract

The `.gitignore` must block all blocklist patterns from §3 (P3). The publish scan (P3) is the enforcement layer, but `.gitignore` is the first line of defense.

### 4.2 Git History Hygiene

Before first tagged release, verify git history does not contain accidentally committed blocked artifacts. If found: either rewrite history (if pre-public) or document in release notes (if post-public).

### 4.3 Release Artifact Manifest

Each tagged release includes a manifest file (`RC_PACKET/MANIFEST.md`) listing:
- Commit hash
- Date
- Gate results (P1-P9, PASS/FAIL each)
- Known issues (if any gates have documented exceptions)
- Link to full evidence packet

---

## 5. License Compliance

### 5.1 Project License

To be selected before first tagged release. Candidates: MIT, Apache-2.0, or GPL-3.0. Decision criteria: compatibility with downstream use, compatibility with dependency licenses, and project goals.

### 5.2 Dependency License Compatibility

The license ledger (P4) must be reviewed for compatibility with the chosen project license. No `GPL-3.0` dependency may be included if the project uses `MIT` or `Apache-2.0` (or vice versa, depending on direction).

### 5.3 OGL/SRD Compliance

Game mechanics reference the d20 System Reference Document (SRD) under the Open Game License (OGL). The OGL notice must be present in the repository if SRD content is referenced. IP hygiene (P8) ensures no non-OGL content leaks.

---

## 6. Offline Guarantee

### 6.1 Design Principle

The application is offline-first. Network access is never required for core functionality (combat resolution, narration, dice rolling, character management).

### 6.2 Permitted Network Use (Opt-In Only)

Future features that require network access (e.g., remote API calls for LLM inference) must:
1. Default to OFF in configuration.
2. Produce a clear user-facing message when enabled.
3. Function gracefully when network is unavailable (fail-closed, not fail-silent).

### 6.3 Enforcement

Gate P6 enforces this at release time. Any new network-dependent code must update the static scan's exception list with justification.

---

## 7. Privacy Posture

### 7.1 Core Statement

This application processes all data locally. No telemetry is collected. No data leaves the user's machine in default configuration.

### 7.2 Microphone Handling

Microphone access (for STT) is opt-in. It is not enabled by default. When enabled:
- Audio is processed locally by the STT engine.
- Raw audio is not retained after transcription unless the user explicitly enables recording via configuration.
- Transcripts are stored locally as session artifacts and can be deleted by the user.

### 7.3 Data Retention Defaults

| Data Type | Location | Retention | Deletion |
|-----------|----------|-----------|----------|
| Session logs | `logs/` | Until user deletes | Delete directory |
| Oracle state | `oracle_db/` | Until user deletes | Delete directory |
| Generated audio | `audio_cache/` | Until user deletes | Delete directory |
| Generated images | `image_cache/` | Until user deletes | Delete directory |
| Configuration | `config/` | Until user modifies | Edit or delete files |

### 7.4 Delete Everything

To remove all user-generated data: delete `logs/`, `oracle_db/`, `audio_cache/`, `image_cache/`, and any `*.sqlite` files in the project root. Configuration in `config/` can be reset by deleting and re-running setup.

---

## 8. Operational Artifact Curation

### 8.1 Publish Posture: CURATED

The `pm_inbox/` directory is internal operational infrastructure. It is not published in full.

### 8.2 What Gets Published

| Artifact Type | Published | Format |
|---------------|-----------|--------|
| WO dispatch templates | YES | Anonymized examples in `docs/method/` |
| Exemplary debriefs (2-3 per release) | YES | Selected for method proof, tied to specific commits |
| Doctrine files | YES | `pm_inbox/doctrine/` contents, versioned |
| PM briefing | NO | Internal tracking surface |
| Rehydration kernel | NO | Internal agent protocol |
| Active dispatches/debriefs | NO | Operational artifacts |

### 8.3 Volatility Control

Published operational artifacts must not contain volatile references (gate counts, suite totals, file counts) unless cited as point-in-time facts tied to a specific commit hash. Example:

- BAD: "189 gate tests pass."
- GOOD: "At commit `abc1234`, 189 gate tests passed."
- BEST: Omit the count entirely if it adds no value to the reader.

### 8.4 Snapshot Pack

Each tagged release may include a `docs/method/RELEASE_SNAPSHOT.md` containing:
- Selected dispatch/debrief pairs demonstrating the WO methodology
- Gate test summary tied to the release commit
- Build order narrative (what was built and in what sequence)

---

## 9. RC Evidence Packet

### 9.1 Orchestrator

**Command:** `scripts/build_release_candidate_packet.py`

**Behavior:**
1. Creates `RC_PACKET/` directory (or clears existing).
2. Runs P1 through P9 in sequence.
3. Captures all evidence logs.
4. Generates `RC_PACKET/MANIFEST.md` with commit hash, date, and per-gate PASS/FAIL.
5. Exits with code 0 if all gates PASS, code 1 if any gate FAILS.

### 9.2 Packet Contents

```
RC_PACKET/
├── MANIFEST.md                  # Summary: commit, date, gate results
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
└── known_failures.txt           # Copy of test baseline
```

### 9.3 Attachment

The RC evidence packet is attached to the GitHub Release as a zip archive. It is the proof-of-compliance artifact for that release.

---

## 10. Donation Policy

### 10.1 Posture

Donations are optional and decoupled from software access. The software is free. Donations do not unlock features, priority support, or any differential treatment.

### 10.2 Gating

Donation links are not present in the repository until P1-P9 PASS on a tagged release. This prevents soliciting support before the project meets its own quality bar.

### 10.3 Language Requirements

Donation text must:
- State that the software is free and donations are optional.
- Make no promise of future features tied to donation levels.
- Avoid language that implies a transaction (no "buy", "purchase", "subscribe", "unlock").

---

## 11. Boundary Statement

This contract governs publishing readiness and release process only. It has zero authority over game mechanics, combat resolution, Oracle state, voice pipeline behavior, or any runtime subsystem. PRS-01 gates are evaluated at release time, not during development. Development workflow (BURST-001, WO dispatch, gate tests) continues independently.

---

## 12. Durable Acceptance Rule

**DR-PRS-01:** "We do not consider publishing until all publish gates PASS on a signed commit and the RC evidence packet exists and matches that commit exactly."

No exceptions. No partial releases. No "we'll fix it after launch."

---

## Appendix A: Builder WO Sequence (Estimated)

The following builder WOs are needed to implement the scripts and artifacts required by this spec. These are estimated — PM will draft specific WOs when prioritized.

| WO | Scope | Depends On |
|----|-------|------------|
| WO-PRS-SCAN-001 | P3 asset scan + P5 secret scan + P8 IP scan scripts | PRS-01 frozen |
| WO-PRS-LICENSE-001 | P4 license ledger creation + lint script | PRS-01 frozen |
| WO-PRS-OFFLINE-001 | P6 offline guarantee (static + runtime) scripts | PRS-01 frozen |
| WO-PRS-FIRSTRUN-001 | P7 fail-closed first run script | PRS-01 frozen |
| WO-PRS-DOCS-001 | P9 privacy statement + doc validation script + OGL notice | PRS-01 frozen |
| WO-PRS-ORCHESTRATOR-001 | RC packet builder (orchestrator script) | All scan WOs complete |

Gate P1 (clean tree) and P2 (test suite) require no new scripts — they use existing tooling.
