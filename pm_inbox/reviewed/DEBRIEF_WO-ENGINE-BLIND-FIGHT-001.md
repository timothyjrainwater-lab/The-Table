# DEBRIEF: WO-ENGINE-BLIND-FIGHT-001
**Status:** ACCEPTED
**Batch:** O (Dispatch O)
**Gate label:** ENGINE-BLIND-FIGHT
**Gate count:** 8/8 PASS (BF-001 – BF-008)
**Commit:** 6057476
**Date:** 2026-02-27

---

## Pass 1 — Full Context Dump

### Mechanic
PHB p.93: Blind-Fight — when a concealment miss chance applies, the attacker may reroll the miss-chance die once. Second failure = miss (no further reroll). Applies to any concealment (20%, 50% total concealment, etc.).

### Files Modified
- `aidm/core/attack_resolver.py` — After concealment miss check, if attacker has `"blind_fight"` feat, reroll the miss-chance die once. Event sequence: `concealment_check` (initial miss) → `blind_fight_reroll` event → second roll → if second roll succeeds, attack proceeds to hit resolution; if fails, `attack_miss` (concealment) emitted.
- `tests/test_engine_blind_fight_gate.py` — 8 gate tests: BF-001 (reroll triggers on initial concealment miss), BF-002 (reroll success → attack proceeds to damage), BF-003 (both rolls fail → miss), BF-004 (no feat → no reroll), BF-005 (20% miss chance), BF-006 (50% miss chance), BF-007 (no miss chance = no reroll path), BF-008 (event sequence: reroll event emitted before miss or damage).

### Key Findings
- Concealment miss-chance check was pre-existing in attack_resolver.py. Blind Fight adds a second-chance reroll path at that check point — clean injection with no structural change.
- FINDING: BF-008 verifies event ordering — `blind_fight_reroll` event emitted before outcome. Important for UI and narrative layer ordering.

### Gate Run
```
tests/test_engine_blind_fight_gate.py — 8 passed (combined run with IO + TG)
```

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-BLIND-FIGHT-001 ACCEPTED. Blind Fight reroll wired in attack_resolver.py at the concealment-miss decision point. Reroll is one attempt only — second failure is a confirmed miss. 8/8 gate tests pass including event ordering verification. Implementation is a clean injection into the existing concealment check path. Committed 6057476.

---

## Pass 3 — Retrospective

**Drift caught:** None.
**Pattern:** Feat-conditional reroll at an existing check point. Same injection model as Evasion (conditional on save outcome) — both add a post-check second chance.
**Recommendation:** None outstanding.
**Radar:** GREEN.
