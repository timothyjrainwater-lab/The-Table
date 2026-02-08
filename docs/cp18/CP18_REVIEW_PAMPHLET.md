# CP-18 (Combat Maneuvers) — Attachment Pamphlet for CLOG (Claude)
**Date:** 2026-02-08
**Audience:** Implementation agent ("CLOG")
**Authority:** Implementation-constrained (follow CP-18 packet exactly)

This pamphlet is meant to be **attached alongside** the following files you received:

- `test_maneuvers_integration_skeleton.py`
- `test_maneuvers_core_skeleton.py`
- `CP18_COMPLETION_CHECKLIST.md`
- `CP18_GATE_VIOLATION_SENTINELS.md`
- `CP18_DETERMINISM_RISK_CHECKLIST.md`
- `CP18_TEST_COVERAGE_MATRIX.md`

It tells you **what each file is**, **how to use it**, and **what to do in what order**.

---

## 0) Non‑Negotiables (read once, then enforce)
1. **Tier gate compliance:** Implement **Tier‑1 only** (G‑T1 is open; others are closed). Any temptation to add persistent/relational mechanics is a STOP.
2. **Determinism:** Same input → identical output, including **RNG consumption order** and **event ordering**.
3. **Follow the CP-18 Implementation Packet exactly.** If the packet doesn't authorize it, it doesn't ship.

Key references (canonical):
- `docs/CP18_IMPLEMENTATION_PACKET.md` (file touch map, forbiddens, acceptance criteria)
- `docs/CP18_COMBAT_MANEUVERS_DECISIONS.md` (design spec)
- `docs/DETERMINISM_THREAT_MODEL_CP18_CP19.md` (allowed/forbidden determinism patterns)

---

## 1) What each attached file is for

### A) `CP18_TEST_COVERAGE_MATRIX.md`
A **planning matrix** that enumerates coverage targets across:
- maneuver legality & resolution branches
- AoO provocation / abort behavior
- RNG consumption invariants
- event ordering + event-count stability
- gate-safe degradations (no persistent item state; grapple-lite unidirectional)

Use it to ensure you don't "miss a branch" when filling in tests.

### B) `test_maneuvers_core_skeleton.py`
Tier‑1 **unit test skeleton** for maneuver resolver logic.
Copy/rename into the repo as:
- `tests/test_maneuvers_core.py`

Then **fill in** as the implementation lands.

### C) `test_maneuvers_integration_skeleton.py`
Tier‑2 **integration test skeleton** covering play_loop routing + AoO integration + mounted combat edge points.
Copy/rename into the repo as:
- `tests/test_maneuvers_integration.py`

### D) `CP18_DETERMINISM_RISK_CHECKLIST.md`
A "you will regret ignoring this" list of determinism failure modes.
Use it as a pre-merge checklist.

### E) `CP18_GATE_VIOLATION_SENTINELS.md`
Concrete "red flags" that indicate you've crossed a closed capability gate.
Use it to stop scope creep early.

### F) `CP18_COMPLETION_CHECKLIST.md`
Your **Definition of Done** tracker.
The CP-18 packet requires **tests, determinism replay, and documentation updates** before marking COMPLETE.

---

## 2) Where these files should go in the repo
These are *attachments*, but once you're implementing:

1. Place skeletons into `tests/` and rename:
   - `test_maneuvers_core_skeleton.py` → `tests/test_maneuvers_core.py`
   - `test_maneuvers_integration_skeleton.py` → `tests/test_maneuvers_integration.py`

2. Keep the checklists/matrix in `docs/` (optional), or leave them outside the repo if you don't want them committed.

---

## 3) Execution order (do this in sequence)

### Step 1 — Read canonical constraints
- `PROJECT_STATE_DIGEST.md` for current gate status and what is authorized.
- `CP18_IMPLEMENTATION_PACKET.md` for file touch map and forbiddens.
- `DETERMINISM_THREAT_MODEL_CP18_CP19.md` for ordering rules (no unordered iteration; fixed RNG order; fixed event emission count).

### Step 2 — Implement code strictly per touch map
Create:
- `aidm/schemas/maneuvers.py`
- `aidm/core/maneuver_resolver.py`

Modify:
- `aidm/schemas/entity_fields.py`
- `aidm/core/play_loop.py`
- `aidm/core/aoo.py`

**Do not touch** forbidden files (notably `attack_resolver.py`).

### Step 3 — Land Tier‑1 tests first (fast feedback)
- Rename and start filling `tests/test_maneuvers_core.py`
- Work maneuver-by-maneuver (Bull Rush → Trip → Overrun → Sunder → Disarm → Grapple-lite)

### Step 4 — Integration tests (routing + AoO + mounted)
- Fill `tests/test_maneuvers_integration.py`
- Verify AoO triggers per packet.
- Verify trip vs mounted targets uses CP‑18A forced dismount hook.

### Step 5 — Determinism audits (required)
The packet requires:
- 10× replay with identical state hashes
- RNG consumption order matches design
- event ordering matches design

### Step 6 — Documentation updates (required for completion)
Update `PROJECT_STATE_DIGEST.md` with the CP‑18 update block and test count (626 → new total).

---

## 4) High‑risk spots (don't improvise)
- **RNG drift:** fixed consumption order even across branches.
- **Unordered iteration:** never iterate over `set()` for AoO threats; sort by stable keys.
- **Grapple-lite gate safety:** apply `Grappled` to defender only.

---

## 5) Escalation rule (hard stop)
STOP and escalate if:
- you discover a maneuver requires any closed gate
- determinism requires persistent multi-round state
- AoO/conditions/mounted integration behaves unexpectedly

---

**STATUS: ✅ CP-18 COMPLETE** (2026-02-08)

All steps in this pamphlet have been executed:
- Implementation complete per file touch map
- 53 new tests (36 Tier-1 + 17 Tier-2)
- 10× deterministic replay verified
- PROJECT_STATE_DIGEST.md updated (626 → 679 tests)
