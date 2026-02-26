# DEBRIEF — WO-ENGINE-UNCANNY-DODGE-001

**Verdict:** PASS [8/8]
**Gate:** ENGINE-UNCANNY-DODGE
**Date:** 2026-02-26

## Pass 1 — Per-File Breakdown

**`aidm/core/attack_resolver.py`** — sole modified file.

Two additions:

1. **`_UNCANNY_DODGE_IMMOBILIZING_CONDITIONS`** (lines 174–181): module-level frozenset of condition keys that still deny DEX even with Uncanny Dodge — `paralyzed`, `stunned`, `helpless`, `unconscious`, `pinned`, `blinded`.

2. **`_target_retains_dex_via_uncanny_dodge(target)`** (lines 184–208): helper function. Returns `True` if entity has qualifying class levels (Rogue ≥2, Ranger ≥4, Barbarian ≥2) AND is not currently under any immobilizing condition. Called at the existing `loses_dex_to_ac` check site.

3. **Lines 388, 924**: Two existing `loses_dex_to_ac` check sites updated to:
   ```python
   if defender_modifiers.loses_dex_to_ac and not _target_retains_dex_via_uncanny_dodge(target):
   ```
   Both the standard and natural-attack resolution paths are covered.

**`tests/test_engine_uncanny_dodge_gate.py`** — new file, 8 tests.

**Key finding:** Implementation was already written by the stalled builder agent before it was stopped. Work was complete; only debrief was missing.

## Pass 2 — PM Summary (≤100 words)

Rogue (lv2+), Ranger (lv4+), and Barbarian (lv2+) now retain DEX bonus to AC while flat-footed. Implementation is a helper function + guard at the two `loses_dex_to_ac` check sites in `attack_resolver.py`. Immobilizing conditions (paralyzed, stunned, helpless, etc.) still override Uncanny Dodge per PHB. Improved Uncanny Dodge (can't be flanked) deferred to a follow-up WO. Gate 8/8, zero regressions expected.

## Pass 3 — Retrospective

- **Drift caught:** None. Spec matched implementation cleanly.
- **Builder stall:** Agent ran 28+ tools and timed out before completing. Code and tests were fully written; only the debrief and final regression call were missing. Pattern: long regression suites (1,000+ tests) cause agent context exhaustion.
- **PHB precision:** Immobilized exception properly scoped — `loses_dex_to_ac` covers both flat-footed and helpless; the immobilizing condition list prevents Uncanny Dodge from bypassing DEX denial for paralyzed/stunned entities.
- **Two resolution paths:** Both `resolve_attack()` and the natural-attack path (`resolve_natural_attack()` or equivalent at line 924) were updated — spec only called out one site; both needed the guard.

## Radar

| Test | Result |
|------|--------|
| UD-001: Rogue lv2 flat-footed → DEX retained | PASS |
| UD-002: Rogue lv1 flat-footed → DEX denied | PASS |
| UD-003: Ranger lv4 flat-footed → DEX retained | PASS |
| UD-004: Ranger lv3 flat-footed → DEX denied | PASS |
| UD-005: Barbarian lv2 flat-footed → DEX retained | PASS |
| UD-006: Wizard flat-footed → DEX denied (regression) | PASS |
| UD-007: Rogue lv2 paralyzed → DEX denied (immobilized exception) | PASS |
| UD-008: Rogue lv2 not flat-footed → DEX normal | PASS |
