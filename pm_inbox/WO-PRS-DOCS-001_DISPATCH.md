# WO-PRS-DOCS-001 — Privacy Statement + OGL Notice + Doc Validator
**Lifecycle:** NEW
**Date:** 2026-02-23
**Type:** FEATURE
**Authority:** PRS-01 v1.0 FROZEN (`docs/contracts/PUBLISHING_READINESS_SPEC.md`)
**Gate:** AB (new)

---

## Target Lock

Build the P9 documentation compliance system: create the privacy statement (`docs/PRIVACY.md`), add the OGL notice, and build a validator script that ensures required sections exist and referenced paths are valid.

## Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Privacy statement scope? | **Per PRS-01 §7** — data locality, microphone handling, retention defaults, deletion instructions. All from the spec. |
| 2 | OGL notice location? | **`docs/OGL_NOTICE.md`** — standalone file. Also referenced from README. |
| 3 | Validator approach? | **Section heading detection + path existence check** — parse `docs/PRIVACY.md` for required sections, verify all referenced file paths exist on disk. |
| 4 | Deletion path validation? | **Yes** — validator checks that paths mentioned in "Delete Everything" section correspond to actual directories in the project structure. |

## Contract Spec

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

## Implementation Plan

1. Draft `docs/PRIVACY.md` from PRS-01 §7 content
2. Draft `docs/OGL_NOTICE.md` with standard OGL v1.0a text
3. Build validator script
4. Run validator, resolve any path mismatches

## Gate Spec

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

## Files to Read

- `docs/contracts/PUBLISHING_READINESS_SPEC.md` — §P9, §7 for privacy posture
- `docs/` — Existing docs structure
- Project root — Directory structure for path validation

## Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

## Integration Seams

- Validator logs to `RC_PACKET/p9_docs_check.log` (via orchestrator)
- Exit codes: 0 = PASS, 1 = FAIL
- Privacy statement content comes from PRS-01 §7 — builder should transcribe, not invent

## Assumptions to Validate

1. Directory paths referenced in PRS-01 §7.3/§7.4 (`logs/`, `oracle_db/`, `audio_cache/`, `image_cache/`, `config/`) exist in the repo structure
2. OGL v1.0a text is standard and can be included verbatim

## Delivery Footer

Builder delivers: 2 docs + 1 validator script + gate tests. Debrief in CODE format (500 words, 5 sections + Radar). Commit message references PRS-01 and gate letter AB.

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Docs work order complete. Awaiting Thunder."
```
