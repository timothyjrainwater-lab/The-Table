# Debrief: WO-ENGINE-VERBAL-SPELL-BLOCK-001
**Builder:** Chisel
**Dispatch:** #15 (Batch F)
**Date:** 2026-02-26
**Commit:** 8d2ff92
**Status:** ACCEPTED — 6/6 passed, 2/2 skipped (FINDING-documented)

---

## What Was Done

Added verbal component block guard to `_resolve_spell_cast()` in `aidm/core/play_loop.py`.

The guard fires **before metamagic validation** — correct PHB order (PHB p.174: you cannot initiate casting if the verbal component is unavailable, regardless of other metamagic modifications).

- Reads `spell.has_verbal` (defaults `True` via `getattr`)
- Reads `intent.metamagic` — `"silent"` in metamagic suppresses V requirement (Silent Spell, PHB p.98)
- Checks `EF.CONDITIONS` for `"silenced"` or `"gagged"` keys
- On block: emits `spell_blocked` event with `reason="verbal_component_blocked"`, no slot consumed, returns immediately

## Pass 3 Notes

**VS-002 skip (FINDING-ENGINE-NONVERBAL-SPELLS-001):** No spell in the current registry has `has_verbal=False`. All spells default to `True`. A non-verbal spell cannot be tested against silence blocking without adding one. Logged as LOW OPEN finding.

**VS-007 skip (FINDING-ENGINE-SILENCE-ZONE-001):** Environmental silence zones (Silence spell creating a zone) are not tracked on entity conditions by the engine. The verbal block is condition-based only — a caster in a silence zone would need `"silenced"` applied to their entity. Zone-based application is not wired. Logged as LOW OPEN finding.

**Ordering decision:** Moved the verbal check to fire before metamagic validation (prior implementation was after). This is architecturally correct — the inability to speak is a more fundamental precondition than metamagic feat validation. A silenced caster with Still Spell (VS-008) is correctly blocked by verbal before metamagic is assessed.

**Linter addition noted:** Linter inserted a somatic component block (WO-ENGINE-SOMATIC-COMPONENT-001 pattern) between the verbal check and metamagic validation in `play_loop.py`. This was from a prepped future WO and does not affect Batch F correctness.

---

## Test Results

| ID | Scenario | Result |
|----|----------|--------|
| VS-001 | Silenced caster, V spell | PASS — spell_blocked emitted |
| VS-002 | Silenced caster, V=False spell | SKIP — FINDING-ENGINE-NONVERBAL-SPELLS-001 |
| VS-003 | Non-silenced caster, V spell | PASS — resolves normally |
| VS-004 | Gagged caster, V spell | PASS — spell_blocked emitted |
| VS-005 | Blocked → world_state unchanged | PASS — no slot consumed |
| VS-006 | Blocked → no action_used event | PASS |
| VS-007 | Silence zone (environmental) | SKIP — FINDING-ENGINE-SILENCE-ZONE-001 |
| VS-008 | Silenced + Still Spell | PASS — verbal block fires before metamagic |
