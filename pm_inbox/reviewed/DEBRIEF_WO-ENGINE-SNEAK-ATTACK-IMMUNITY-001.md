# DEBRIEF — WO-ENGINE-SNEAK-ATTACK-IMMUNITY-001
# Auto-Apply CRIT_IMMUNE from Creature Type

**Verdict:** ACCEPTED 10/10
**Gate:** ENGINE-SNEAK-ATTACK-IMMUNITY
**Date:** 2026-02-26
**WO:** WO-ENGINE-SNEAK-ATTACK-IMMUNITY-001

---

## Pass 1 — Per-File Breakdown

### `aidm/core/sneak_attack.py`

**Production changes:** None.

`SNEAK_ATTACK_IMMUNE_TYPES` (creature_type set) and `is_target_immune()` (checks creature_type) were already correctly implemented. The coverage audit that generated this WO misread the existing function — it saw the `EF.CRIT_IMMUNE` flag check and missed the creature_type loop above it. The function was fully operational.

**Gate action:** Gate tests (SAI-01 through SAI-10) were written to validate the existing behavior. All 10 pass. Zero production changes.

**Fragmentation surfaced:** The resolver checks immunity via three separate paths:
- `entity.get("immune_to_critical_hits", False)` — bare string field
- `entity.get("immune_to_sneak_attack", False)` — bare string field
- `entity.get(EF.CRIT_IMMUNE, False)` — EF constant field

A fourth constant `EF.CRIT_IMMUNE` exists but is not the primary path for the creature_type loop. Any subsystem writing `entity[EF.CRIT_IMMUNE] = True` expecting the immunity to be recognized may produce a false negative if the lookup path doesn't check that field. FINDING-SAI-FRAGMENTATION-001 OPEN.

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-SNEAK-ATTACK-IMMUNITY-001 ACCEPTED 10/10. Pre-implemented. `sneak_attack.py` already had `SNEAK_ATTACK_IMMUNE_TYPES` + `is_target_immune()` checking creature_type — coverage audit misread the function. Zero production changes; gate tests validate existing behavior. Pass 3 surfaced structural finding: three different immunity field names (`immune_to_critical_hits`, `immune_to_sneak_attack`, bare strings; `EF.CRIT_IMMUNE`, constant) create fragmentation risk. Future subsystem writing to wrong field = silent immunity bypass. FINDING-SAI-FRAGMENTATION-001 OPEN. Non-blocking.

---

## Pass 3 — Retrospective

**Audit-map is not ground truth (second occurrence):** This is the second WO where the audit doc misread existing code. WO-SEC-REDACT-001 similarly had a partial pre-existing landing. The coverage map is the best available starting point but gate tests are the actual arbiter. Pattern: when a WO targets "missing" functionality, builder should verify the current state before writing new code.

**Three-field fragmentation risk:** The immunity resolver checks three different field names. This was fine when the codebase was small and one person could hold the whole picture. As more resolvers and creature types are added, the probability of a new field being written to the wrong slot grows. Normalization is the right long-term fix.

**Recommendation for FINDING-SAI-FRAGMENTATION-001:** A future normalization WO should: (1) pick one canonical field name (likely `EF.CRIT_IMMUNE` since it uses the EF constant pattern), (2) grep all write sites and migrate to the canonical name, (3) update `is_target_immune()` to check only the canonical field. Non-blocking for current RC — defer to after attack layer batch.

---

*Debrief filed by Slate (PM) on builder verdict receipt.*
