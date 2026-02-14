# WO-AMBFIX-001: Implement 3 FIX-SRD Decisions from AMBIGUOUS Verdicts

**Authority:** PM (Opus 4.6)
**Date:** 2026-02-14
**Lifecycle:** NEW
**Status:** READY for dispatch
**Scope:** 3 surgical code changes from Operator AMBIGUOUS verdict decisions
**Estimated file touches:** 3-4 files

---

## Context

The Operator reviewed 7 AMBIGUOUS verdicts and decided FIX-SRD on 3 of them. These require code changes. All are small, independent fixes.

**Reference:** `docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md` — full verdict details and Operator reasoning.

---

## Fix 1: B-AMB-02 / H-AMB-01 — Opposed check ties (initiator wins)

**Current behavior:** Defender wins ties on opposed checks (uses `>` for attacker).
**Target behavior:** Initiator (active participant) wins ties (use `>=` for attacker).

**Files to change:**
- `aidm/core/maneuver_resolver.py` — find the opposed check comparison, change `attacker_total > defender_total` to `attacker_total >= defender_total`
- `aidm/core/skill_resolver.py` (if it has opposed checks) — same change

**Tests:**
- Update any test that asserts defender wins on a tie to assert attacker wins
- Add 1 test with attacker_total == defender_total, assert attacker wins

**SRD reference:** PHB p.314-315 (Opposed Checks)

---

## Fix 2: B-AMB-04 — Disarm weapon type modifiers

**Current behavior:** Disarm uses BAB + STR + size only, no weapon type modifiers.
**Target behavior:** Add +4 for two-handed weapon vs one-handed, -4 for light weapon vs one-handed.

**Files to change:**
- `aidm/core/maneuver_resolver.py` — in the disarm opposed check calculation, add weapon type modifier:
  - If attacker weapon is two-handed: +4 to attacker's check
  - If attacker weapon is light: -4 to attacker's check
  - Same for defender
- **NOTE:** This depends on weapon type being available in the combat context. If weapon type is not currently passed to the disarm resolver, add a TODO comment with the modifier logic and a note that it activates when weapon plumbing (P4-D) is complete. Do NOT block on weapon plumbing.

**Tests:**
- If weapon type is available: test two-handed +4 and light -4 modifiers
- If weapon type is not available: test the TODO exists and the function signature is ready

**SRD reference:** PHB p.155 (Disarm)

---

## Fix 3: E-AMB-03 — 5-foot step in difficult terrain

**Current behavior:** Blocks 5-foot step only at movement_cost >= 4.
**Target behavior:** Block 5-foot step at movement_cost >= 2 (any difficult terrain).

**Files to change:**
- `aidm/core/terrain_resolver.py` (or wherever the 5-foot step threshold is) — change the threshold from `>= 4` to `>= 2`

**Tests:**
- Update existing threshold test (if any) to expect >= 2
- Add test: movement_cost=2 (standard difficult terrain), assert 5-foot step blocked
- Add test: movement_cost=1 (normal terrain), assert 5-foot step allowed

**SRD reference:** PHB p.144 (5-Foot Step)

---

## Builder Protocol

- Read `docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md` for full context on each verdict.
- Surgical fixes only — do NOT refactor surrounding code.
- Each fix is independent — can be committed separately or together.
- If a test was testing the OLD behavior (defender wins ties, no weapon mods, threshold >= 4), update the test.
- Run `python -m pytest tests/ -x -q` after all fixes to confirm GREEN.
- Check `git diff` on target files before reporting completion.

---

## Completion Report

```
COMMITS: [list of commits with hashes]
TEST COUNT: [total passed / failed / skipped]
STOPLIGHT: [GREEN if all pass]
ISSUES: [any problems encountered]
```
