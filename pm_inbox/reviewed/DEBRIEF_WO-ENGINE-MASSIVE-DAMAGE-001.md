# DEBRIEF — WO-ENGINE-MASSIVE-DAMAGE-001
# Massive Damage Rule — DC 15 Fort or Die

**Verdict:** ACCEPTED 10/10
**Gate:** ENGINE-MASSIVE-DAMAGE
**Date:** 2026-02-26
**WO:** WO-ENGINE-MASSIVE-DAMAGE-001

---

## Pass 1 — Per-File Breakdown

### `aidm/core/attack_resolver.py`

**Changes made — one insertion block:**

DC 15 Fort check injected between `hp_after` assignment and the `if final_damage > 0:` block.

Trigger condition: `final_damage >= 50` (PHB p.142: single hit dealing 50+ damage triggers massive damage).

On save fail: `hp_after = -10` → existing `resolve_hp_transition()` handles the resulting instant death (same path as any entity reaching -10 HP).

**RNG:** Uses `rng.stream("combat")` — deterministic replay preserved. Consistent with all other random checks in the resolver.

**Insertion point rationale:** Between `hp_after` assignment and `if final_damage > 0:` is the correct slot — damage is finalized (including crits and bonuses), HP transition hasn't been evaluated yet. The check fires after damage is known, before consequences are resolved. Clean.

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-MASSIVE-DAMAGE-001 ACCEPTED 10/10. DC 15 Fort check in `attack_resolver.py` — triggers when `final_damage >= 50`. Fail → `hp_after = -10`, existing `resolve_hp_transition` emits `entity_defeated`. Uses `rng.stream("combat")` (replay-safe). Insertion point: after damage finalized, before HP transition. PHB p.142 compliant. MD-01–MD-10 all pass. No regressions.

---

## Pass 3 — Retrospective

**`full_attack_resolver.py` — not modified.** Massive damage check is in `attack_resolver.py` only. `full_attack_resolver.py` calls through to the single-attack path — if a single attack in a full attack sequence deals 50+ damage, the check fires in the underlying resolver. No duplicate logic needed.

**Insertion point is the canonical slot for damage-consequence checks.** This is the same pattern used by the coup de grace check. Any future "single-hit consequence" (stunning blow, vorpal weapon) belongs in this same window.

**Replay safety:** `rng.stream("combat")` is the right stream. All attack-phase randomness uses this stream. Using a different stream would break gold master replay for any scenario where massive damage fires.

---

*Debrief filed by Slate (PM) on builder verdict receipt.*
