# CP-18 Determinism Risk Checklist (Implementer-Facing)
**Date:** 2026-02-08
**Authority:** Determinism Threat Model (CP-18/19) + CP-18 design + implementation packet

---

## A) Global determinism rules (binding)

1. **One action → one resolution window** (no multi-round state machines).
2. **RNG stream:** use **"combat" only**.
3. **Fixed RNG order:** consume rolls in the documented order *regardless of branch*.
4. **Ordered event emission:** deterministic ordering; stable sort keys.
5. **No hidden iteration:** never iterate over unordered collections.

---

## B) CP-18 threat catalog → concrete "do/don't" checks

### T-18-01 Opposed Roll Ordering Drift
- ✅ Always roll: attacker then defender.
- ❌ Don't conditionally roll defender only on certain outcomes.

**Applies:** Bull Rush, Trip, Overrun, Disarm, Grapple-lite.

**Test signal:** replay divergence or mismatched event sequences.

---

### T-18-02 AoO Cascade Nondeterminism
- ✅ AoO ordering must follow CP-15: initiative → entity-id lexicographic.
- ✅ Ensure threatening-entity lists are **sorted** before resolution.
- ❌ No `set()` iteration.

**Applies:** all maneuvers that provoke AoO.

---

### T-18-03 Conditional Event Emission
- ✅ Emit placeholder/no-op events (or equivalent neutral events) to preserve event counts across branches where design requires stable counts.
- ❌ Don't emit fewer events on failure.

**Applies:** Trip (counter-trip), Disarm (counter-disarm).

---

### T-18-04 Grapple-lite Leakage
- ✅ Defender only gets Grappled condition.
- ✅ Condition must **not reference attacker**.
- ❌ No attacker flags like `is_grappling`, no shared references.

---

## C) "Red flag" implementation patterns to ban

- Dict iteration without sorting when building event lists.
- Returning early *before* consuming required RNG draws.
- Branching on AoO results in a way that changes subsequent RNG draws without placeholders.
- Storing derived roll results on world state (should remain in events only).

---

## D) Verification checklist (required before CP-18 acceptance)

- [x] Each maneuver's RNG order matches the packet's order contract.
- [x] Each maneuver emits events in the fixed sequence contract.
- [x] Event counts are branch-stable where required (Trip, Disarm).
- [x] AoO ordering matches CP-15 contract.
- [x] 10× deterministic replay (PBHA) produces identical state hashes.

---

**STATUS: ✅ VERIFIED** (2026-02-08)
