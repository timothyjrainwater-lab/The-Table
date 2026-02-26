# ENGINE DISPATCH #16 — BATCH G
**Issued by:** Slate (PM)
**Date:** 2026-02-26
**To:** Chisel (lead builder) — or clean-slate agent per Chisel's call
**Batch:** G — 4 WOs, 32 gate tests
**Prerequisite:** ENGINE DISPATCH #15 ACCEPTED ✅ (expected — Batch F in execution)

---

## Boot Sequence

Before any work:

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm gate total is 962 (`pytest --co -q | tail -5` or equivalent count)
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md` — note Batch F is ACCEPTED, Batch G is DISPATCHED
4. Orphan check: any WO marked IN EXECUTION with no debrief? Flag to Slate before proceeding.

---

## Batch G Work Orders

### WO 1 — WO-ENGINE-MASSIVE-DAMAGE-RULE-001
**File:** `pm_inbox/WO-ENGINE-MASSIVE-DAMAGE-RULE-001_DISPATCH.md`
**Scope:** `aidm/core/attack_resolver.py` + `aidm/core/spell_resolver.py`
**Gate:** `tests/test_engine_massive_damage_rule_001_gate.py` — 8 tests (MD-001–MD-008)
**Gate label:** ENGINE-MASSIVE-DAMAGE-RULE-001
**Kernel touch:** KERNEL-01 (Entity Lifecycle) — alternate death pathway
**Dependencies:** Fort save system ✓, EF.DEFEATED ✓, EF.DYING ✓ — all live

**Summary:** 50+ HP single-hit damage triggers Fort DC 15 save or instant death (PHB p.145). No check currently exists. Two insertion points: `attack_resolver.py` after hit damage, `spell_resolver.py` after spell damage. DC is always 15 regardless of damage amount. Emits `massive_damage_death` or `massive_damage_survived` event.

**Chisel's call:** Clean throw candidate — no prior accumulated context required. Both resolvers have clear insertion points.

---

### WO 2 — WO-ENGINE-ARCANE-SPELL-FAILURE-001
**File:** `pm_inbox/WO-ENGINE-ARCANE-SPELL-FAILURE-001_DISPATCH.md`
**Scope:** `aidm/core/spell_resolver.py` only
**Gate:** `tests/test_engine_arcane_spell_failure_001_gate.py` — 8 tests (AF-001–AF-008)
**Gate label:** ENGINE-ARCANE-SPELL-FAILURE-001
**Kernel touch:** KERNEL-03 (Constraint Algebra) — equipment constrains spellcasting
**Dependencies:** `EF.ARCANE_SPELL_FAILURE` ✓ (live from prior batch) | `has_somatic` field on SpellDefinition — **verify before writing**

**Summary:** Arcane casters wearing armor have ASF% chance of somatic spell failure (PHB p.123). `EF.ARCANE_SPELL_FAILURE` field is live and set at chargen. This WO wires it to runtime: check field → if non-zero and spell has somatic component → roll d100 → if roll ≤ ASF% → spell fails, slot consumed, `arcane_spell_failure` event emitted.

**Chisel's call:** Clean throw — single file, field already registered.

**BLOCKER CHECK:** Verify `has_somatic: bool` on SpellDefinition before writing. If missing, stop and flag to Slate.

---

### WO 3 — WO-ENGINE-SOMATIC-COMPONENT-001
**File:** `pm_inbox/WO-ENGINE-SOMATIC-COMPONENT-001_DISPATCH.md`
**Scope:** `aidm/core/spell_resolver.py` only
**Gate:** `tests/test_engine_somatic_component_001_gate.py` — 8 tests (SC-001–SC-008)
**Gate label:** ENGINE-SOMATIC-COMPONENT-001
**Kernel touch:** KERNEL-02 (Containment Topology) — pinned/bound state constrains action space
**Dependencies:** `has_somatic` field on SpellDefinition (same as WO 2) | PINNED/BOUND condition names — verify in conditions.py

**Summary:** Pinned or bound casters cannot cast spells with somatic components (PHB p.174). Same entry point as Batch F's verbal spell block (WO-ENGINE-VERBAL-SPELL-BLOCK-001). Guard checks `has_somatic`, then checks caster conditions for PINNED/BOUND. Emits `spell_blocked` with `reason=somatic_component_blocked`. **Critical PHB distinction:** GRAPPLED (not pinned) does NOT block somatic casting — it triggers a Concentration check instead (future WO).

**Chisel's call:** Clean throw — same pattern as verbal block, same file, different guard.

**BLOCKER CHECK:** Same `has_somatic` dependency as WO 2. If WO 2 confirms it missing, both WO 2 and WO 3 are blocked — report to Slate.

---

### WO 4 — WO-ENGINE-DEFLECTION-BONUS-001
**File:** `pm_inbox/WO-ENGINE-DEFLECTION-BONUS-001_DISPATCH.md`
**Scope:** `aidm/schemas/entity_fields.py` + `aidm/core/attack_resolver.py`
**Gate:** `tests/test_engine_deflection_bonus_001_gate.py` — 8 tests (DB-001–DB-008)
**Gate label:** ENGINE-DEFLECTION-BONUS-001
**Kernel touch:** KERNEL-14 (Effect Composition) — first AC-modifying effect type with non-stacking rule
**Dependencies:** AC resolution in attack_resolver.py ✓ — confirm touch attack path handles deflection correctly

**Summary:** Deflection bonus to AC (PHB p.136) — magical source (rings of protection, Shield of Faith, etc.). Applies vs. ALL attacks including touch attacks (unlike armor bonus). Multiple deflection bonuses don't stack — highest wins. New `EF.DEFLECTION_BONUS` field on entity, included in AC calculation in `attack_resolver.py`. Prerequisite for ring of protection magic item WO.

**Chisel's call:** Moderate continuity value — `attack_resolver.py` has been touched in prior batches. Chisel or clean throw.

---

## Integration Seams

**`has_somatic` field (WO 2 + WO 3):**
Must exist on `SpellDefinition` in `aidm/data/spell_definitions.py`. Verify before writing either WO. If absent, both WOs are blocked — escalate to Slate immediately.

**Massive damage insertion points (WO 1):**
- `attack_resolver.py` — after `damage_dealt` is computed and HP decremented
- `spell_resolver.py` — after `total` is applied to target HP
Both checks are identical in logic; the event payload differs only in source context.

**Deflection in touch attacks (WO 4):**
Touch attacks bypass armor/shield/natural armor but NOT deflection (PHB p.136). Verify the touch attack path in `attack_resolver.py` applies deflection but strips other AC components. Document what's found even if no fix needed.

**d100 for ASF% check (WO 2):**
Confirm whether `RNGProvider` has a `d100()` method. If not, use `randint(1, 100)` via the existing provider pattern. Do not introduce a new random function outside the RNG protocol.

---

## Regression Protocol

Pre-existing failures: **12 stable** as of Batch F close. Do not treat as regressions.

Run WO-specific gates to confirm delivery:
```bash
pytest tests/test_engine_massive_damage_rule_001_gate.py -v
pytest tests/test_engine_arcane_spell_failure_001_gate.py -v
pytest tests/test_engine_somatic_component_001_gate.py -v
pytest tests/test_engine_deflection_bonus_001_gate.py -v
```

Then full suite:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. If still failing — record in debrief and stop. Do not loop.

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

WO-ENGINE-MASSIVE-DAMAGE-RULE-001:
- [ ] `git add aidm/core/attack_resolver.py aidm/core/spell_resolver.py tests/test_engine_massive_damage_rule_001_gate.py`
- [ ] `git commit` (commit hash in debrief)
- [ ] All 8 MD tests pass; zero regressions
- [ ] Debrief filed

WO-ENGINE-ARCANE-SPELL-FAILURE-001:
- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_arcane_spell_failure_001_gate.py`
- [ ] `git commit` (commit hash in debrief)
- [ ] All 8 AF tests pass; zero regressions
- [ ] Debrief filed

WO-ENGINE-SOMATIC-COMPONENT-001:
- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_somatic_component_001_gate.py`
- [ ] `git commit` (commit hash in debrief)
- [ ] All 8 SC tests pass; zero regressions
- [ ] Debrief filed

WO-ENGINE-DEFLECTION-BONUS-001:
- [ ] `git add aidm/schemas/entity_fields.py aidm/core/attack_resolver.py tests/test_engine_deflection_bonus_001_gate.py`
- [ ] `git commit` (commit hash in debrief)
- [ ] All 8 DB tests pass; zero regressions
- [ ] Debrief filed

Chisel kernel updated at session close.

---

## Audio Cue (Chisel fires on completion)

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel. Chisel does not self-dispatch.*
