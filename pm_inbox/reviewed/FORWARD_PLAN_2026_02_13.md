# Forward Execution Plan — AIDM Project

**Author:** Opus 4.6 (PM Session)
**Date:** 2026-02-13
**Baseline:** 5,275 passed / 7 failed (Chatterbox hw-gated) / 16 skipped / 105s
**Commit:** 63a33b0 (master) + 43 uncommitted files from this session

---

## What This Document Is

An actionable plan for getting AIDM from "test suite passes" to "presentable, playable, maintainable." Not a governance doc. Not a vision statement. A list of things to do, in order, with acceptance criteria.

---

## Part 1: Immediate — Commit and Merge Current Work

### 1.1 Commit This Session's Changes

This session produced verified fixes and new infrastructure across 43 files.
These should be committed as 2-3 atomic commits:

**Commit A: Bug fixes + immutability hardening**
- `full_attack_resolver.py` — shallow copy → deepcopy
- `state.py` — to_dict() returns deep copy, _wrap_nested_dict() recursive
- `ws_bridge.py` — id(websocket) → UUID
- `fact_acquisition.py` — FactRequest/FactResponse frozen properly
- `aoo.py` — maneuver intent extraction refactored (5 blocks → 1 helper)
- `test_state.py` — 3 new mutation-prevention tests
- `test_fact_acquisition.py` — assertion updates for tuple types

**Commit B: Automated gates**
- `test_immutability_gate.py` — scans all frozen dataclasses for unprotected mutables
- `test_boundary_completeness_gate.py` — verifies all layer pairs are tested

**Commit C: Snapshot infrastructure + doc reconciliation**
- `scripts/audit_snapshot.py` — machine-generated STATE.md
- `docs/STATE.md` — canonical project numbers
- `PROJECT_COMPASS.md`, `PROJECT_STATE_DIGEST.md` — pointer to STATE.md

### 1.2 Merge Other Agent's Work

Another agent (separate branch) has committed:
- `5033169` — Playable REPL CLI + turn fixture progression
- `3173528` — Dependency alignment (requirements.txt, pyproject.toml)

These should be merged into master after this session's commits.
Resolve conflicts if any, then run full test suite.

### Acceptance: All tests green after merge. `python scripts/audit_snapshot.py` produces clean STATE.md.

---

## Part 2: Process — How to Stop AI-on-AI Drift

These are the rules for all future agent work on this project.

### Rule 1: No prose-only invariants

If a constraint matters, it must be a test or a script. Examples already done:
- "Frozen dataclasses must be frozen" → `test_immutability_gate.py`
- "Box must not import Spark" → `test_boundary_completeness_gate.py`
- "Test counts must be accurate" → `scripts/audit_snapshot.py`

If an agent writes a constraint in a markdown file without a corresponding test,
that constraint does not exist.

### Rule 2: Every agent session ends with a structured handoff

Format (6 blocks, always in this order):
```
## Outcome
- <one-line shipped change>

## Evidence
- <claim>. [file:line]

## Validation
- <command> -> <result>

## Risks / Gaps
- <risk>

## Next 3 Actions
1) <action>

## PM Decision Needed
- <binary question>
```

No prose paragraphs. No "executive summaries." File/line references or it didn't happen.

### Rule 3: Audits run on pinned commits only

Before any audit:
1. Commit or stash all changes
2. Record commit hash
3. Run `python scripts/audit_snapshot.py`
4. Audit findings reference specific file:line on THAT commit

An audit on a dirty working tree is not an audit.

### Rule 4: The playable CLI is the acceptance gate

Before any PR is considered done, the change must not break:
```
python -m aidm.runtime.play_cli
```
If a human can't type "attack goblin" and get a response, the PR is not ready.

### Rule 5: Document count stays frozen

Current root-level markdown files: whatever exists after merge.
No new root-level .md files may be created without deleting one first.
Planning docs go in `docs/planning/`. Reports go in `pm_inbox/`.

---

## Part 3: Next Development Work (Priority Order)

### P0: Stabilize and Ship Playable Loop

The CLI exists (from other agent's branch). After merge:

1. Add a scripted smoke test that runs the CLI with canned input
   ("attack goblin", "end turn", "quit") and verifies non-crash output.
   File: `tests/runtime/test_cli_smoke.py`

2. Add a golden transcript test — save a canonical command→output sequence,
   replay it, verify deterministic output.
   File: `tests/runtime/test_cli_golden_transcript.py`

3. Wire monster AI turns into the CLI loop so combat is two-sided.
   The tactical_policy module exists and is tested. It just needs to be
   called in the REPL when it's the monster's turn.

### P1: World Compiler Stages 6 + 7

Stage 6 (Maps) and Stage 7 (Asset Pools) are the remaining compiler stages.
The infrastructure exists in `world_compiler.py` — stages register via
`register_stage()` and execute in dependency order.

- Stage 6: Generate region/city/district map data for "where am I?"
- Stage 7: Generate asset pool manifests for portrait/voice binding

These are independent of each other and of the CLI work. Can be parallelized.

### P2: Reduce the 26 Unprotected Frozen Dataclasses

The immutability gate currently has 26 known exceptions. These should be
reduced over time by adding `__post_init__` freezing to each class.
Priority order:
1. `truth_packets.py` (6 classes) — these carry game-critical data
2. `scene_manager.py` (5 classes) — these carry Lens-layer state
3. Everything else

### P3: Test Quality Improvements

These are real but not urgent:
- Remove conditional assertions in test_aoo_kernel.py
- Strengthen test_campaign_schemas.py hash tests to verify actual values
- Parameterize repetitive test patterns

---

## Part 4: What NOT to Do

- Do not write more governance documents
- Do not run speculative audits on dirty trees
- Do not create work orders for style preferences
- Do not refactor working code that isn't blocking progress
- Do not add features before the playable loop is stable

---

## PM Handoff (Structured)

### Outcome
- Fixed 4 verified bugs (shallow copy, state mutation, websocket ID, frozen containers)
- Refactored 1 code duplication (aoo.py 5-block → helper)
- Added 2 automated gate tests (immutability scanner, boundary completeness)
- Added 1 infrastructure script (audit_snapshot.py → docs/STATE.md)
- Updated 2 governance docs to reference canonical snapshot

### Evidence
- full_attack_resolver.py:660 — deepcopy replaces .copy(). [verified: 25 tests]
- state.py:56-66 — to_dict() returns deepcopy. [verified: 3 new tests]
- state.py:165-185 — _wrap_nested_dict() recursive. [verified: 1 new test]
- ws_bridge.py:82,100 — UUID replaces id(websocket). [verified: imports clean]
- fact_acquisition.py:66,125 — List→tuple, Dict→MappingProxyType. [verified: 58 tests]
- aoo.py:115-137 — _extract_maneuver_params() replaces 5 copy-paste blocks. [verified: 29 tests]

### Validation
- `python -m pytest tests/ -q` → 5,275 passed / 7 failed (hw) / 16 skipped / 105s
- `python scripts/audit_snapshot.py` → STATE.md generated, 5,298 discovered
- All 19 modified aidm/ modules import cleanly (no syntax errors)

### Risks / Gaps
- 43 uncommitted files need to be committed (3 logical commits)
- Other agent's CLI work (commits 5033169, 3173528) needs merge
- 26 frozen dataclasses still have unprotected mutable fields (tracked by gate test)
- Initial audit contained 37% fabricated claims — all subsequent work verified against code

### Next 3 Actions
1) Commit and merge all pending work (this session + other agent's CLI)
2) Add CLI smoke test as merge gate
3) Wire monster AI turns into CLI for two-sided combat

### PM Decision Needed
- Should we commit this session's 43 files as one commit or split into 3?
- Should the CLI smoke test be a required gate for all future PRs?
