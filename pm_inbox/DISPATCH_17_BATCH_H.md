# ENGINE DISPATCH #17 — BATCH H
**Issued by:** Slate (PM)
**Date:** 2026-02-26
**To:** Chisel (lead builder)
**Batch:** H — 4 WOs, 32 gate tests
**Prerequisite:** ENGINE DISPATCH #16 ACCEPTED ✅ (Batch G — gate total target ~993)

---

## Boot Sequence

Before any work:

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm gate total is ~993 (`pytest --co -q | tail -5`)
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md` — confirm Batch G ACCEPTED, Batch H DISPATCHED
4. Orphan check: any WO marked IN EXECUTION with no debrief? Flag to Slate before proceeding.

---

## Intelligence Update (confirmed this session — act on immediately)

**`has_somatic: bool = True`** confirmed live on `SpellDefinition` (line 174 of `spell_resolver.py`). The Batch G blocker was clear — WO 2 and WO 3 execute without issue.

**`ConditionType.PINNED`, `GRAPPLED`, `ENTANGLED`, `FLAT_FOOTED`** — all confirmed live in `conditions.py`.

**`EF.CONCENTRATION_BONUS`** — confirmed live from Batch F.

---

## Batch H Work Orders

### WO 1 — WO-ENGINE-CONCENTRATION-DAMAGE-001
**File:** `pm_inbox/WO-ENGINE-CONCENTRATION-DAMAGE-001_DISPATCH.md`
**Scope:** `aidm/core/spell_resolver.py`
**Gate:** `tests/test_engine_concentration_damage_001_gate.py` — 8 tests (CD-001–CD-008)
**Gate label:** ENGINE-CONCENTRATION-DAMAGE-001
**Kernel touch:** KERNEL-03 (Constraint Algebra)
**Dependencies:** EF.CONCENTRATION_BONUS ✓ | damage-this-turn detection — builder determines approach

**Summary:** Caster hit during their casting action must make Concentration check (DC 10 + damage taken + spell level) or lose spell (PHB p.69/p.175). Surfaces from FINDING-ENGINE-CONCENTRATION-OTHER-001. Builder chooses between event-scan vs. entity-flag approach for damage detection — document in Pass 3.

**Chisel's call:** Chisel recommended — `spell_resolver.py` context live from Batch F defensive casting WO.

---

### WO 2 — WO-ENGINE-CONCENTRATION-GRAPPLE-001
**File:** `pm_inbox/WO-ENGINE-CONCENTRATION-GRAPPLE-001_DISPATCH.md`
**Scope:** `aidm/core/spell_resolver.py`
**Gate:** `tests/test_engine_concentration_grapple_001_gate.py` — 8 tests (CG-001–CG-008)
**Gate label:** ENGINE-CONCENTRATION-GRAPPLE-001
**Kernel touch:** KERNEL-02 (Containment Topology)
**Dependencies:** GRAPPLED ✓, ENTANGLED ✓ (both confirmed live)

**Summary:** Grappled (not pinned) caster → Concentration DC 20 + spell level. Entangled caster → DC 15 + spell level (PHB p.175). Both are checks-not-blocks — the spell can succeed. PINNED is a separate block (Batch G WO 3). Same file as WO 1.

**Chisel's call:** Chisel recommended — same zone as WO 1.

---

### WO 3 — WO-ENGINE-FLATFOOTED-AOO-001
**File:** `pm_inbox/WO-ENGINE-FLATFOOTED-AOO-001_DISPATCH.md`
**Scope:** `aidm/core/aoo.py`
**Gate:** `tests/test_engine_flatfooted_aoo_001_gate.py` — 8 tests (FF-001–FF-008)
**Gate label:** ENGINE-FLATFOOTED-AOO-001
**Kernel touch:** KERNEL-06 (Termination Doctrine) — flat-footed clearing timing
**Dependencies:** FLAT_FOOTED ✓ | EF.CONDITIONS ✓

**Summary:** Flat-footed entities cannot make AoOs (PHB p.136). Closes FINDING-ENGINE-FLATFOOTED-AOO-001 (open since Dispatch #12). One guard in the reactor eligibility loop in `aoo.py`. Chisel has `aoo.py` context from Combat Reflexes (Batch B R1) and Defensive Casting (Batch F).

**Chisel's call:** Chisel recommended — `aoo.py` continuity is live.

---

### WO 4 — WO-ENGINE-NONLETHAL-THRESHOLD-001
**File:** `pm_inbox/WO-ENGINE-NONLETHAL-THRESHOLD-001_DISPATCH.md`
**Scope:** `aidm/core/attack_resolver.py`
**Gate:** `tests/test_engine_nonlethal_threshold_001_gate.py` — 8 tests (NL-001–NL-008)
**Gate label:** ENGINE-NONLETHAL-THRESHOLD-001
**Kernel touch:** KERNEL-01 (Entity Lifecycle) — third unconscious pathway
**Dependencies:** EF.NONLETHAL_DAMAGE ✓ | STAGGERED ✓

**Summary:** Nonlethal damage ≥ current HP → STAGGERED; nonlethal > current HP → UNCONSCIOUS (PHB p.145). Field already accumulates; threshold check is the gap. Adds two events: `nonlethal_staggered`, `nonlethal_unconscious`. Action economy enforcement for STAGGERED is a future WO.

**Chisel's call:** Clean throw — `attack_resolver.py` insertion point is clean, no accumulated context required.

---

## Integration Seams

**WO 1 + WO 2 both land in `spell_resolver.py`:**
Run in sequence. WO 1 adds damage-this-turn check; WO 2 adds grapple/entangle check. Verify they don't collide at the same entry point. The order should be: somatic block (Batch G) → verbal block (Batch F) → grapple/entangle check (WO 2) → damage check (WO 1) → ASF (Batch G) → defensive casting → spell resolves.

**Flat-footed clearing timing (WO 3):**
The flat-footed condition is set at combat start and cleared after the entity's first action. Confirm the clearing timing in `aoo.py` or `play_loop.py` — the AoO guard must fire before the condition clears.

**Condition mutation pattern (WO 4):**
Match the SHAKEN application pattern from WO-ENGINE-INTIMIDATE-DEMORALIZE-001 (Batch F). Do not invent a new condition-setting pattern.

---

## Regression Protocol

Pre-existing failures: **12 stable** (plus any documented skips from Batch F/G). Do not treat as regressions.

Run WO-specific gates:
```bash
pytest tests/test_engine_concentration_damage_001_gate.py -v
pytest tests/test_engine_concentration_grapple_001_gate.py -v
pytest tests/test_engine_flatfooted_aoo_001_gate.py -v
pytest tests/test_engine_nonlethal_threshold_001_gate.py -v
```

Then full suite:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. If still failing — record in debrief and stop.

---

## Debrief Requirements

File debriefs to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`.

**Required sections (all WOs):**
- Pass 1: Full context dump — per-file breakdown, actual line numbers, what was found vs expected
- Pass 2: PM summary ≤100 words
- Pass 3: Retrospective — drift caught, patterns, recommendations. **Hidden DM kernel check mandatory.**
- Radar: open findings surfaced by this WO

**Missing debrief or missing Pass 3 → REJECT.**

---

## Session Close Conditions

WO-ENGINE-CONCENTRATION-DAMAGE-001:
- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_concentration_damage_001_gate.py`
- [ ] `git commit` (hash in debrief)
- [ ] All 8 CD tests pass; zero regressions
- [ ] Debrief filed

WO-ENGINE-CONCENTRATION-GRAPPLE-001:
- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_concentration_grapple_001_gate.py`
- [ ] `git commit` (hash in debrief)
- [ ] All 8 CG tests pass; zero regressions
- [ ] Debrief filed

WO-ENGINE-FLATFOOTED-AOO-001:
- [ ] `git add aidm/core/aoo.py tests/test_engine_flatfooted_aoo_001_gate.py`
- [ ] `git commit` (hash in debrief)
- [ ] All 8 FF tests pass; zero regressions
- [ ] Debrief filed

WO-ENGINE-NONLETHAL-THRESHOLD-001:
- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_nonlethal_threshold_001_gate.py`
- [ ] `git commit` (hash in debrief)
- [ ] All 8 NL tests pass; zero regressions
- [ ] Debrief filed

Chisel kernel updated at session close.

---

## Audio Cue (Chisel fires on completion)

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel. Chisel does not self-dispatch.*
