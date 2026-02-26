# DEBRIEF — WO-ENGINE-COMBAT-REFLEXES-001

**Verdict:** PASS [8/8]
**Gate:** ENGINE-COMBAT-REFLEXES
**Date:** 2026-02-26

## Pass 1 — Per-File Breakdown

**`aidm/core/aoo.py`**
`check_aoo_triggers()`: `aoo_count_this_round` dict read from `active_combat` (default `{}`). Boolean eligibility check replaced with count-based check in both the standard all-threateners path and the target-only path. Limit formula: `1 + max(0, dex_mod) if "combat_reflexes" in reactor_feats else 1`. Existing `aoo_used_this_round` set retained — parallel dict is additive (safer migration per spec). Flat-footed suppression preflight: **no flat-footed check exists in check_aoo_triggers()** — no bypass needed, none added.

**`aidm/core/play_loop.py`**
Both AoO update blocks now increment `aoo_count_this_round[entity_id]` immediately after updating `aoo_used_this_round`. Uses `active_combat.setdefault("aoo_count_this_round", {})` for safe first-write.

**`aidm/core/combat_controller.py`**
`aoo_count_this_round: {}` added to initial `active_combat` state. `execute_round()` round-reset clears it alongside `aoo_used_this_round`. This was a necessary extension spec anticipated ("confirm round-reset clears `active_combat` keys").

**`aidm/runtime/play_controller.py`**
`aoo_count_this_round: {}` added to initial combat state initialization. Required to match combat_controller pattern.

**`tests/test_engine_combat_reflexes_gate.py`** — NEW
CR-001 through CR-008 all pass. Coverage: no-feat one-AoO cap (CR-001); DEX +3 allows 4 AoOs (CR-002); DEX 0 same as no feat (CR-003); negative DEX floors at 1 (CR-004); DEX +2 exactly 3 AoOs (CR-005); regression single-use blocked (CR-006); count increments correctly (CR-007); two entities tracked independently (CR-008).

## Pass 2 — PM Summary (≤100 words)

Combat Reflexes fully wired. AoO count now tracked per entity via `aoo_count_this_round` dict in `active_combat`, parallel to the existing `aoo_used_this_round` set. `check_aoo_triggers()` applies `1 + max(0, dex_mod)` AoO limit for Combat Reflexes holders (1 otherwise). Both AoO execution paths increment the count. Round-reset added in combat_controller and play_controller. Target-only AoO path also updated. Flat-footed suppression not present in aoo.py — no bypass needed. 8/8 gate tests pass.

## Pass 3 — Retrospective

**Drift caught:**
- Round-reset for `aoo_count_this_round` required changes in **both** `combat_controller.py` and `play_controller.py` — spec mentioned confirming the reset but did not enumerate both files. Builder correctly found both initialization sites.
- Target-only AoO path exists and required the same update — spec noted this as "same replacement using `target_id`" and builder applied it correctly.

**Patterns:** The parallel-dict approach (keeping existing set, adding new dict) avoided breaking existing AoO tests during migration. This pattern should be the default when extending set-based tracking.

**Flat-footed note:** No flat-footed suppression exists in check_aoo_triggers() — the bypass spec was conditional ("if suppression exists") and correctly was not added. PHB flat-footed AoO immunity is a separate unimplemented mechanic; when it is added, the Combat Reflexes bypass will need to be wired at that time.

**Open findings:**
| ID | Severity | Description |
|----|----------|-------------|
| FINDING-ENGINE-FLATFOOTED-AOO-001 | MEDIUM | PHB: flat-footed entities normally cannot make AoOs; Combat Reflexes exception cannot be enforced until flat-footed AoO suppression exists in aoo.py |

## Radar

- ENGINE-COMBAT-REFLEXES: 8/8 PASS
- aoo_used_this_round confirmed: set type (created from list via set(...get(..., [])))
- Flat-footed suppression in aoo.py: not found — no bypass added
- Round-reset confirmed in combat_controller.py execute_round()
- Zero new failures in full regression
- Pre-existing failures: test_engine_gate_cleave (5, WO-ENGINE-CLEAVE-ADJACENCY-001 pending), test_aoo_kernel ImportError (pre-existing) — unchanged
