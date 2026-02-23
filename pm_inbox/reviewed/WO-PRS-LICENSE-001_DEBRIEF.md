# WO-PRS-LICENSE-001 Debrief
**Work Order:** WO-PRS-LICENSE-001 — License Ledger + Lint
**Gate:** Y (P4 License Compliance)
**Status:** COMPLETE
**Date:** 2026-02-22
**Format:** CODE (500 words, 5 sections + Radar)

---

## 1. Objective Recap

Build the P4 license compliance system per PRS-01: a complete license ledger documenting all dependencies with SPDX identifiers, and a lint script validating ledger completeness against lockfiles. Gate Y enforces this with 6 tests.

---

## 2. Implementation Path

**Phase 1: Draft Generator**
Created `scripts/publish_generate_license_draft.py` to scan Python (pyproject.toml, requirements.txt) and Node (package.json) lockfiles. Script extracts dependency names and versions, generates markdown table with UNKNOWN placeholders for manual completion. This is a one-time helper tool, not a gate script.

**Phase 2: Manual License Research**
Populated `docs/LICENSE_LEDGER.md` with verified license data for 13 dependencies:
- Python: pytest (MIT), psutil (BSD-3-Clause), pyyaml (MIT), msgpack (Apache-2.0), opencv-python-headless (Apache-2.0), Pillow (HPND), numpy (BSD-3-Clause), starlette (BSD-3-Clause), uvicorn (BSD-3-Clause)
- Node: three (MIT), @types/three (MIT), typescript (Apache-2.0), vite (MIT)

All licenses are permissive (MIT, Apache-2.0, BSD-3-Clause, HPND). No GPL dependencies. Full compatibility with future license selection.

**Phase 3: Validation Script**
Built `scripts/publish_check_licenses.py` (gate script) with four validation layers:
1. Schema validation: all 6 required fields present (dependency, version, license, source_url, redistribution, where_used)
2. UNKNOWN detection: fail if any license field is UNKNOWN
3. Lockfile cross-reference: detect dependencies in lockfiles but missing from ledger
4. Redistribution validation: ensure values are bundled/runtime-dep/dev-only

Exit 0 on PASS, exit 1 on FAIL. Outputs to stdout for RC packet capture.

**Phase 4: Gate Tests**
Created `tests/test_publish_license_gate_y.py` with 6 tests covering:
- Y-01: Current repo passes (baseline validation)
- Y-02: Missing dependency detection (removes pytest from ledger, verifies failure)
- Y-03: UNKNOWN license detection (plants UNKNOWN, verifies rejection)
- Y-04: Missing field detection (removes where_used column, verifies schema failure)
- Y-05: Schema completeness (validates all 6 fields present on all rows)
- Y-06: Lockfile coverage (ensures every lockfile dep appears in ledger)

All tests use backup/restore pattern to avoid polluting the working ledger. Tests passed 6/6.

---

## 3. Technical Decisions

**Ledger format:** Markdown table per PRS-01 spec, not CSV. More readable in git diffs, easier to review in PRs.

**Redistribution inference:** Draft generator marks pyproject.toml `[project.optional-dependencies]` as dev-only, `[project.dependencies]` as runtime-dep. Node devDependencies marked dev-only. Builder validates during manual completion.

**Unicode handling:** Script originally used Unicode checkmarks (✓/✗) for PASS/FAIL. Windows console (cp1252) rejected these. Changed to `[PASS]`/`[FAIL]` text markers for cross-platform compatibility.

**Test isolation:** Gate tests modify ledger in-place with backup/restore, not temp directories. Simpler, avoids cwd issues with subprocess calls. Ensures tests run against actual repo structure.

---

## 4. Risk Surface

**License accuracy:** Manual research required for each dependency. Automated PyPI/npm queries not implemented (offline-safe per PRS-01 §6). Risk: human error in license transcription. Mitigation: source_url field allows audit trail, validation script enforces SPDX identifiers.

**Version drift:** Ledger uses minimum constraint versions (e.g., 7.0.0 for pytest>=7.0.0). Lockfiles may have newer versions installed. Script validates presence, not exact version match. Risk: license change in newer versions not detected. Mitigation: acceptable for pre-1.0 project, can tighten version matching later.

**Transitive dependencies:** Ledger documents only direct dependencies. Transitive deps (e.g., numpy's dependencies) not tracked. Risk: GPL transitive dep could leak in. Mitigation: deferred to future WO, not blocking P4 gate.

---

## 5. Gate Evidence

- **Gate Y tests:** 6/6 passed
- **License validation:** Exit 0, all deps documented, no UNKNOWN licenses
- **Schema compliance:** All 6 required fields present on 13 dependencies
- **Lockfile coverage:** Python (9 deps) + Node (4 deps) = 13 total, all documented

Deliverables: 1 gate script + 1 helper script + 1 ledger + 6 gate tests. PRS-01 §P4 requirement satisfied.

---

## Radar

**P4 compliance achieved.** License ledger complete, validation enforced. Next: WO-PRS-SCAN-001 (P3/P5/P8 scans), WO-PRS-OFFLINE-001 (P6), WO-PRS-FIRSTRUN-001 (P7), WO-PRS-DOCS-001 (P9). RC orchestrator blocked until all gate scripts exist. No immediate dependencies. Gate Y stable.
