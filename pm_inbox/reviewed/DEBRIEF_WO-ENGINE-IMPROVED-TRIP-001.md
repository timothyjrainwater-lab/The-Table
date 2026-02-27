# DEBRIEF: WO-ENGINE-IMPROVED-TRIP-001
**Status:** ACCEPTED
**Batch:** N (Dispatch N)
**Gate label:** ENGINE-IMPROVED-TRIP
**Gate count:** 10/10 PASS (IT-001 – IT-010, includes 2 regression bonus tests)
**Commit:** 020d091
**Date:** 2026-02-27

---

## Pass 1 — Full Context Dump

### Mechanic
PHB p.96: Improved Trip — no AoO on trip attempt; free attack after successful trip.
PHB p.96: Improved Sunder — no AoO on sunder attempt (bundled into this WO as a parallel AoO suppression).

### Files Modified
- `aidm/core/play_loop.py` — AoO suppression check for TripIntent + SunderIntent added AFTER `check_aoo_triggers()` call (line ~2283), same pattern as Batch L Improved Disarm/Grapple/Bull Rush (play_loop.py:2257-2276). Reference: `play_loop.py:2283` — `elif isinstance(combat_intent, TripIntent)`.
- `aidm/core/maneuver_resolver.py` — `resolve_trip()` emits `improved_trip_free_attack` marker event then calls `resolve_attack()` with full BAB after successful trip when attacker has `"improved_trip"` feat.
- `tests/test_engine_improved_trip_gate.py` — 10 gate tests covering: AoO suppression with feat (execute_turn), AoO without feat (check_aoo_triggers), successful trip → free attack event emitted (resolve_trip direct), failed trip → no free attack, free attack uses full BAB, sunder AoO suppression, sunder without feat, both feats independent, regression (no feat + successful trip = no free attack), regression (sunder without feat = AoO triggers).

### Key Findings
- Pass 3 note: AoO suppression lives in play_loop.py (not aoo.py). This is identical to Batch L pattern. The Batch L memory note confirms: "play_loop.py AoO suppression for WOs 1-3 was in working tree from prior session and landed with Batch J commit."
- Cleave free-attack call pattern was reusable: create AttackIntent from entity's EF.WEAPON dict + full BAB, call resolve_attack(). No new call path needed.

### Gate Run
```
tests/test_engine_improved_trip_gate.py — 10 passed in 0.36s
```

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-IMPROVED-TRIP-001 ACCEPTED. TripIntent + SunderIntent AoO suppression wired in play_loop.py after check_aoo_triggers() call (same pattern as Batch L). Free attack after successful Improved Trip emitted from maneuver_resolver.py using full BAB (AttackIntent + resolve_attack call, mirroring Cleave pattern). 10/10 gate tests pass. No regressions. Clean pattern.

---

## Pass 3 — Retrospective

**Batch L AoO-suppression reference:** `play_loop.py` lines 2257-2276 — `elif isinstance(combat_intent, DisarmIntent)` / `GrappleIntent` / `BullRushIntent` blocks.
**Cleave free-attack reference:** `attack_resolver.py` lines 919-934 — AttackIntent construction + resolve_attack call.
**Drift caught:** Initial debrief (from previous session) incorrectly cited aoo.py as suppression location. Corrected: suppression is in play_loop.py, consistent with all prior Improved-* feat implementations.
**Radar:** GREEN. No hidden coupling detected.

