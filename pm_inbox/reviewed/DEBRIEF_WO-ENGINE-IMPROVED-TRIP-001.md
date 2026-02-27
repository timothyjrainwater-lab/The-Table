# DEBRIEF: WO-ENGINE-IMPROVED-TRIP-001
**Status:** ACCEPTED
**Batch:** N (Dispatch N)
**Gate label:** ENGINE-IMPROVED-TRIP
**Gate count:** 10/10 PASS (IT-001 – IT-010, includes 2 regression bonus tests)
**Commit:** included in Engine Batch N implementation
**Date:** 2026-02-27

---

## Pass 1 — Full Context Dump

### Mechanic
PHB p.96: Improved Trip — no AoO on trip attempt; free attack after successful trip.
PHB p.96: Improved Sunder — no AoO on sunder attempt (bundled into this WO as a parallel AoO suppression).

### Files Modified
- `aidm/core/aoo.py` — AoO suppression check for TripIntent + SunderIntent; reads `"improved_trip"` / `"improved_sunder"` feat from attacker's FEATS list.
- `aidm/core/maneuver_resolver.py` — `resolve_trip()` emits free attack event after successful trip when attacker has `"improved_trip"` feat. Free attack uses full BAB (not iterative). Also added `resolve_sunder()` AoO path matching same guard pattern.
- `tests/test_engine_improved_trip_gate.py` — 10 gate tests covering: AoO suppression with feat, AoO without feat, successful trip → free attack event emitted, failed trip → no free attack, free attack uses full BAB, sunder AoO suppression, sunder without feat, both feats independent, regression (no feat + successful trip = no free attack), regression (sunder without feat = AoO triggers).

### Key Findings
- None. Clean implementation. AoO suppression pattern mirrors Improved Disarm/Grapple/Bull Rush from Batch L exactly.
- FINDING: IT-006/IT-007 (Sunder AoO suppression) bundled into this WO per PM dispatch. Sunder mechanic already partially wired; this adds the AoO gate only.

### Gate Run
```
tests/test_engine_improved_trip_gate.py — 10 passed in 0.31s
```

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-IMPROVED-TRIP-001 ACCEPTED. Both trip and sunder AoO suppression wired via feat check in aoo.py. Free attack after successful Improved Trip emitted from maneuver_resolver.py using full BAB. 10/10 gate tests pass. Bundled Improved Sunder AoO suppression into same WO per dispatch spec. No regressions. Clean pattern — identical to Batch L maneuver AoO suppression series.

---

## Pass 3 — Retrospective

**Drift caught:** None.
**Pattern:** AoO suppression via feat check is a recurring motif (Improved Disarm, Grapple, Bull Rush, Overrun, Trip, Sunder). PM should flag this pattern as a completed cluster when coverage map is next audited.
**Recommendation:** Consider a helper `_feat_suppresses_aoo(attacker, intent_type)` to consolidate the six feat→intent suppression lookups. Not critical — each is 1-2 lines. File as a FINDING if PM agrees.
**Radar:** GREEN. No hidden coupling detected.
