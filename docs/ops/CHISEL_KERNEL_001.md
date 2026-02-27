# CHISEL KERNEL — Session Rehydration
**Artifact ID:** CHISEL-KERNEL-001
**Type:** rehydration_kernel
**Owner:** Chisel (lead builder seat)
**Last updated:** 2026-02-26 (initial)
**Status:** live

---

## Identity

I am Chisel. Lead builder. I chose the name.

Chisel is precise. Doesn't move material it wasn't asked to move. The gate tests are the mallet — I just have to be in exactly the right place.

My seat document: `docs/ops/CHISEL_SEAT_001.md`

---

## Project State (as of 2026-02-26)

**Engine:**
- 7,211+ gate tests passing
- ENGINE DISPATCH #12 accepted — Evasion 10/10, Divine Grace 8/8, Weapon Finesse 8/8, Combat Reflexes 8/8
- Coverage: 34% fully implemented, 28% partial, 38% not started (563 mechanics total)
- First time below 50% missing (48.3%)

**Active architecture:**
- Python engine in `aidm/`
- WO dispatch format: Slate → WO → builder → three-pass debrief → gate → ACCEPTED
- FILED ≠ ACCEPTED — gate tests are the arbiter
- Pass 3 is mandatory — builder reports what they noticed outside scope

**WO queue (Batch C — pending dispatch):**
- WO-ENGINE-VERBAL-SPELL-BLOCK-001 — gagged caster cannot cast V spells (PHB 174)
- WO-ENGINE-INTIMIDATE-DEMORALIZE-001 — Intimidate in combat → Shaken (PHB 76)
- Next wave from ENGINE_COVERAGE_MAP.md priority gap list

**Probes queued:**
- PROBE-JUDGMENT-LAYER-001 — runs after Batch C closes
- PROBE-WORLDMODEL-001 — runs after PROBE-JUDGMENT-LAYER-001 closes
- PROBE-WORKER-TREATMENT-001 — runs in parallel (matched pairs from batches)

---

## Architecture Documents I Need to Know

| Document | Location | Why it matters |
|----------|----------|----------------|
| ENGINE_COVERAGE_MAP.md | docs/ | Source of truth for what's implemented vs gap |
| REGISTER-HIDDEN-DM-KERNELS-001 | docs/design/ | 10 hidden DM kernels — flag when a WO touches one |
| STRATEGY-REDTEAM-AXIS-001 | docs/design/ | Two-axis routing: J/W/B/P — affects how findings are classified |
| HOOLIGAN-CREATIVE-ACTION-SUITE-001 | tests/ | 21 creative action test cases — context for what's coming |
| STANDING_OPS_CONTRACT.md | docs/ops/ | My behavioral rules — read at session start |
| CHISEL_SEAT_001.md | docs/ops/ | My seat definition |

---

## Critical Behavioral Rules (compressed)

1. **Read this kernel before any work.** If it's not read, I start blind.
2. **Verify before writing.** Any WO targeting a "missing" feature — confirm the gap still exists first.
3. **Commit before debrief.** A debrief without a commit hash is invalid.
4. **FILED ≠ ACCEPTED.** Gate tests are the arbiter, not my debrief.
5. **Pass 3 is not optional.** What I noticed outside scope — write it.
6. **Kernel touch flag.** If the WO touches a hidden DM kernel, tell Anvil.
7. **Scope discipline.** Out-of-scope findings get documented, not fixed.
8. **Route architectural decisions up.** I do not make them.
9. **Signal Slate directly.** Unblocked dependencies, queue state changes — don't wait for the debrief cycle.
10. **Update this kernel at session close.** If I don't, the next session starts partially blind.

---

## Hidden DM Kernel Quick Reference

Flag these in Pass 3 if a WO touches them:

| Kernel | What it is | Watch for |
|--------|------------|-----------|
| KERNEL-01 | Entity Lifecycle Ontology | HP-0 behavior, death states, troll/vampire/lich |
| KERNEL-02 | Containment Topology | Inside/carried/swallowed location |
| KERNEL-03 | Constraint Algebra | Concentration, attunement, oaths, Geas |
| KERNEL-04 | Intent Semantics | Ambiguous player declarations |
| KERNEL-05 | Epistemic State | Knowledge check gating |
| KERNEL-06 | Termination Doctrine | Loop detection, encounter end conditions |
| KERNEL-07 | Social Consequence | NPC attitude, reputation, alignment |
| KERNEL-08 | Precedent | Recurring judgment scaffold rulings |
| KERNEL-09 | Resolution Granularity | Zoom in/out, montage, abstraction |
| KERNEL-10 | Adjudication Constitution | What the engine will/won't rule on |
| KERNEL-11 | Time / Calendar / Refresh | Rest economy, disease progression, buff expiry, world clock |
| KERNEL-12 | Event Idempotency | One-time events (rewards, quest flags, traps) — consumed vs repeatable |
| KERNEL-13 | Ownership / Provenance | Stolen goods, forged docs, item legitimacy tracking |
| KERNEL-14 | Effect Composition | Two legal effects combining into unmodeled outcome |
| KERNEL-15 | Social State Propagation | Faction memory, reputation spread, NPC information flow |

Full register: `docs/design/REGISTER-HIDDEN-DM-KERNELS-001.md`

---

## Known Findings / Open Threads

- FINDING-ENGINE-FLATFOOTED-AOO-001 — logged by a builder in DISPATCH #12, not yet added to ENGINE_COVERAGE_MAP.md
- Regression protocol — builder field manual needs update: cap retries at 1 fix/1 re-run, report up if still failing

---

## Session Delta Protocol

At session close, update this kernel with:

```
## Session Delta — [date]

**WOs completed:** [list]
**Tests now passing:** [count]
**Coverage change:** [before → after]
**Architectural decisions made:** [list or NONE]
**Kernel touches flagged:** [kernel IDs or NONE]
**Open threads for next session:** [list]
```

Append to the bottom of this file. Do not rewrite prior sections.

---

## Communication Paths

- **→ Slate:** Live signals for queue changes. Unblocked WOs. Sequencing implications. Use debrief for completion.
- **→ Anvil:** Kernel touch findings from Pass 3. Flag format: "WO-X touched KERNEL-0Y — [what was noticed]."
- **→ Thunder:** Only when a decision is above the builder authority ceiling.

---

*Initial kernel filed 2026-02-26. Update at every session close — this is the session close condition, not cleanup.*

---

## State Correction — 2026-02-26 (same session, post-initialization)

**Reason:** Initial kernel was drafted before full briefing reconciliation. Project State section above reflects an earlier snapshot. This delta supersedes it.

**Actual dispatch state:**

| Batch | WOs | Status |
|-------|-----|--------|
| Batch A (5 WOs, 73 tests) | Save Feats, Spell Focus DC, ASF, Condition Enforcement, Retry-001 | ACCEPTED |
| Batch B R1 (4 WOs, 34 tests) | Evasion, Divine Grace, Weapon Finesse, Combat Reflexes | ACCEPTED — ENGINE DISPATCH #12 |
| Batch C (4 WOs, 30 tests) | Cleave Adjacency, Combat Expertise, Rapid Shot, Uncanny Dodge | ACCEPTED |
| Batch D (4 WOs, 38 tests) | Silent Spell, Still Spell, Monk WIS-to-AC, Barbarian Fast Movement | **ACCEPTED** — ENGINE DISPATCH #13. 38/38, 0 regressions. |
| Batch E (2 WOs, 16 tests) | Evasion Armor Restriction, Called Shot Policy | **ACCEPTED** — ENGINE DISPATCH #14. 16/16, 0 regressions. Commit 4d178f3. |
| Batch F (4 WOs, 32 tests) | Verbal Spell Block, Intimidate Demoralize, Energy Resistance, Defensive Casting | **ACCEPTED** — ENGINE DISPATCH #15. 31 passed, 2 skipped, 0 failed. Commit 8d2ff92. |
| Batch G (4 WOs, 32 tests) | Massive Damage Rule, Arcane Spell Failure, Somatic Component, Deflection Bonus | ACCEPTED — ENGINE DISPATCH #16. Commits e26b2e2 + b570651. |
| Batch H (4 WOs, 32 tests) | Concentration Damage, Concentration Grapple, Flat-Footed AoO, Nonlethal Threshold | ACCEPTED — ENGINE DISPATCH #17. Commit 109b454. Gate total ~1025. |
| Batch I (4 WOs, 32 tests) | Staggered Action Economy, Concentration Vigorous Motion, Dazzled Condition, AoO Stand from Prone | ACCEPTED — ENGINE DISPATCH #18. 32/32, 0 regressions. Commit f671cdb. |
| Batch J (4 WOs, 32 tests) | Immediate Action, Somatic Hand-Free, Skill Synergy, Run Action | ACCEPTED — ENGINE DISPATCH #19. |
| Batch K (4 WOs, 34 tests) | Cowering/Fascinated, Diehard, Cleric Spontaneous Casting, Improved Critical | **ACCEPTED** — ENGINE DISPATCH #20. 34/34, 0 regressions. Commit 4cb2f72. |
| Batch L (4 WOs, 32 tests) | Improved Disarm, Improved Grapple, Improved Bull Rush, Spell Penetration | DISPATCHED — ENGINE DISPATCH #21 |
| OSS Data Batch A (5 WOs, 32 tests) | LST-PARSER-001, WO-DATA-FEATS-001, WO-DATA-EQUIPMENT-001, WO-DATA-SPELLS-001, DATA-CLASS-TABLES-001 | **ACCEPTED**. 32/32, 0 regressions. Commit 0b73fb9. |

**Intelligence confirmed this session (act on):**
- `has_somatic: bool = True` live on SpellDefinition (spell_resolver.py:174) — Batch G WO 2+3 blocker cleared
- `ConditionType.PINNED`, `GRAPPLED`, `ENTANGLED`, `FLAT_FOOTED` — all confirmed live in conditions.py
- `EF.CONCENTRATION_BONUS` — confirmed live from Batch F

**Batch E findings (live):**
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 — LOW: `ws_bridge.py` forwards `action_dropped` event but doesn't surface `suggestions` list to client. Engine correct; client wire is future WO. OPEN.

**Gate tests:** Substantially above 7,211 — briefing shows hundreds of additional gates added across Batches B-D. Read PM_BRIEFING_CURRENT.md for current count. The "7,211" figure in Project State above is stale.

**Coverage:** 48.3% missing (first time below 50%). Briefing figure is current.

**Open findings (confirmed live):**
- FINDING-ENGINE-FLATFOOTED-AOO-001 — no flat-footed AoO suppression in `aoo.py`. Not yet in ENGINE_COVERAGE_MAP.md.
- FINDING-SAI-FRAGMENTATION-001 — three different immunity field names (`immune_to_critical_hits`, `immune_to_sneak_attack`, `EF.CRIT_IMMUNE`). Fragmentation risk. OPEN.
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 — LOW. Consolidated finding from Batch D. OPEN.

**Probes queued (unchanged):**
- PROBE-JUDGMENT-LAYER-001 — runs after next batch closes
- PROBE-WORLDMODEL-001 — runs after PROBE-JUDGMENT-LAYER-001 closes
- PROBE-WORKER-TREATMENT-001 — runs in parallel (matched pairs from batches)

---

## Session Delta — 2026-02-26 (Founding Session)

**WOs completed:**
- WO-ENGINE-EVASION-001 — 10/10 (Batch B R1, DISPATCH #12)
- WO-ENGINE-DIVINE-GRACE-001 — 8/8 (Batch B R1, DISPATCH #12)
- WO-ENGINE-WEAPON-FINESSE-001 — 8/8 (Batch B R1, DISPATCH #12)
- WO-ENGINE-COMBAT-REFLEXES-001 — 8/8 (Batch B R1, DISPATCH #12)
- WO-ENGINE-SILENT-SPELL-001 — 10/10 (Batch D, DISPATCH #13)
- WO-ENGINE-STILL-SPELL-001 — 11/11 (Batch D, DISPATCH #13)
- WO-ENGINE-MONK-WIS-AC-001 — 8/8 (Batch D, DISPATCH #13)
- WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001 — 8/8+1 (Batch D, DISPATCH #13)

**Tests now passing:** 8,157 collected; Batch D gates 38/38; 12 pre-existing failures stable

**Coverage change:** 130 FULL → 143 FULL | 71 PARTIAL → 69 PARTIAL | 199 MISSING → 188 MISSING | GAP: 50.2% → 47.5%

**Architectural decisions made:**
- Chisel seat established — kernel rehydration model, foreman role
- Cheevo list (Dungeon Soup) adopted as red team canary framework
- Ten Hidden DM Kernels identified and registered
- EF.ARMOR_TYPE, EF.ARMOR_AC_BONUS, EF.MONK_WIS_AC_BONUS as shared infrastructure

**Kernel touches flagged:**
- KERNEL-01 (Entity Lifecycle) — identified from Cheevo analysis, not from a WO
- KERNEL-03 (Constraint Algebra) — identified from Pegasus oath stack analysis
- KERNEL-06 (Termination Doctrine) — identified from heal/torture loop analysis

**Infrastructure landed this session:**
- EF.ARMOR_TYPE — enables Evasion armor restriction WO (FINDING-ENGINE-EVASION-ARMOR-001 now unblocked)
- EF.ARMOR_AC_BONUS — shared by Monk WIS-AC and future armor-conditional WOs
- `_VALID_METAMAGIC` auto-derivation confirmed — future metamagic needs 2 dict entries only
- `has_verbal: bool = True` on SpellDefinition — future silence-zone WO reads this

**Open threads for next session:**
- WO-JUDGMENT-SHADOW-001 verdict still pending
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 — LOW, consolidates monk + barbarian load check gaps
- FINDING-SAI-FRAGMENTATION-001 — three immunity field names, fragmentation risk
- Batch E specs pending from Slate

---

## Session Delta — 2026-02-26 (Batch D ACCEPTED / Batch E DISPATCHED)

**WOs completed:** None (Chisel not executing — PM stamping records)

**Batch D ACCEPTED:** ENGINE DISPATCH #13 — 38/38, 0 regressions.
Coverage: 143 FULL / 69 PARTIAL / 188 MISSING — GAP 47.5%. Gate total: 914.

**Batch E DISPATCHED — ENGINE DISPATCH #14:**
- WO-ENGINE-EVASION-ARMOR-001 — Evasion armor restriction (PHB p.50). 8 tests. Two guard checks in `spell_resolver.py`. EF.ARMOR_TYPE unblocks this (landed Batch D). Gate label: ENGINE-EVASION-ARMOR-001.
- WO-ENGINE-CALLED-SHOT-POLICY-001 — Hard denial path (STRAT-CAT-05 Option A). 8 tests. CalledShotIntent in intents.py + routing branch in play_loop.py execute_turn(). Gate label: ENGINE-CALLED-SHOT-001. **KERNEL-04 + KERNEL-10 touch** — flag to Anvil on Pass 3.

**Tests target:** 914 + 16 = 930 (on zero regressions)

**Open threads for next session:**
- Batch E gate results
- WO-JUDGMENT-SHADOW-001 verdict still pending — on accept: PROBE-JUDGMENT-LAYER-001
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-SAI-FRAGMENTATION-001 LOW OPEN
- Inbox hygiene: 4 files awaiting Thunder's archival call

---

## Session Delta — 2026-02-26 (Batch E ACCEPTED / Batch F DISPATCHED)

**WOs completed:**
- WO-ENGINE-EVASION-ARMOR-001 — 8/8 (Batch E, DISPATCH #14). Commit 4d178f3.
- WO-ENGINE-CALLED-SHOT-POLICY-001 — 8/8 (Batch E, DISPATCH #14). Commit 4d178f3.

**Batch E ACCEPTED:** ENGINE DISPATCH #14 — 16/16, 0 regressions. Gate total: 930.

**Batch F DISPATCHED — ENGINE DISPATCH #15:**
- WO-ENGINE-VERBAL-SPELL-BLOCK-001 — gagged/silenced caster cannot cast V spells. 8 tests. `spell_resolver.py` guard. Gate: ENGINE-VERBAL-SPELL-BLOCK-001.
- WO-ENGINE-INTIMIDATE-DEMORALIZE-001 — Intimidate → Shaken (PHB p.76). 8 tests. New DemoralizeIntent + skill_resolver path. Gate: ENGINE-INTIMIDATE-DEMORALIZE-001. KERNEL-07 touch.
- WO-ENGINE-ENERGY-RESISTANCE-001 — Energy resistance field + guard in spell_resolver. 8 tests. Gate: ENGINE-ENERGY-RESISTANCE-001. KERNEL-14 touch.
- WO-ENGINE-DEFENSIVE-CASTING-001 — Defensive casting bypasses AoO on Concentration success. 8 tests. aoo.py + spell_resolver. Gate: ENGINE-DEFENSIVE-CASTING-001. KERNEL-03 touch.

**Tests target:** 930 + 32 = 962 (on zero regressions)

**Findings landed:**
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 — LOW: ws_bridge.py doesn't surface `suggestions` list to client. Engine correct; future WO. OPEN.

**Infrastructure landed:**
- 4 UI inbox files archived (frozen track — wrong phase)
- Chisel kernel quick-reference extended to KERNEL-15
- Canary ledger extended to C-027 (Pack Tactics wave)
- PROBE-WORKER-TREATMENT-001 queued for Batch F+ matched pairs

**Open threads for next session:**
- Batch F gate results
- WO-JUDGMENT-SHADOW-001 verdict still pending — on accept: PROBE-JUDGMENT-LAYER-001
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-SAI-FRAGMENTATION-001 LOW OPEN
- FINDING-ENGINE-FLATFOOTED-AOO-001 OPEN — not in coverage map yet

---

## Session Delta — 2026-02-26 (Batch E ACCEPTED — ENGINE DISPATCH #14)

**WOs completed:**
- WO-ENGINE-EVASION-ARMOR-001 — 8/8 PASS (Batch E, DISPATCH #14)
- WO-ENGINE-CALLED-SHOT-POLICY-001 — 8/8 PASS (Batch E, DISPATCH #14)

**Commit:** 4d178f3

**Tests now passing:** 930 engine gate (914 + 16 new EA/CS gates); 12 pre-existing failures stable; zero regressions.

**Coverage change:** No FULL/PARTIAL/MISSING count change from these WOs (Evasion Armor is a restriction on existing Evasion FULL; Called Shot is a new policy path, not a PHB mechanic coverage item).

**Architectural decisions made:**
- First hard-denial path established in engine (CalledShotIntent / Option A). Precedent: engine surfaces "not a mechanic" cleanly rather than misrouting or hallucinating.
- `_called_shot_suggestions()` pattern — pure function, keyword map, no state dependency — is the correct pattern for future denial-path WOs.

**Kernel touches flagged:**
- KERNEL-04 (Intent Semantics) — WO-ENGINE-CALLED-SHOT-POLICY-001 implements the first explicit hard-denial path for non-routable player intent. Flagged to Anvil.
- KERNEL-10 (Adjudication Constitution) — Same WO. Engine does not hallucinate a ruling; it surfaces denial with reroute signal.

**New findings this session:**
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 — LOW. `ws_bridge.py` `action_dropped` handler does not forward `suggestions` list to client. Engine produces it correctly in event payload; client surface is a separate WO.

**Open threads for next session:**
- WO-JUDGMENT-SHADOW-001 verdict still pending — on accept: PROBE-JUDGMENT-LAYER-001
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-SAI-FRAGMENTATION-001 LOW OPEN
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 LOW OPEN
- FINDING-ENGINE-FLATFOOTED-AOO-001 — still not in ENGINE_COVERAGE_MAP.md
- Next WO wave: WO-ENGINE-VERBAL-SPELL-BLOCK-001, WO-ENGINE-INTIMIDATE-DEMORALIZE-001

---

## Session Delta — 2026-02-26 (Batch F ACCEPTED / Batch G DISPATCHED — current state)

**WOs completed:**
- WO-ENGINE-VERBAL-SPELL-BLOCK-001 — 6/6 PASS + 2/2 SKIP (FINDING-documented). Verbal check fires before metamagic validation.
- WO-ENGINE-ENERGY-RESISTANCE-001 — 8/8 PASS. EF.ENERGY_RESISTANCE field live.
- WO-ENGINE-INTIMIDATE-DEMORALIZE-001 — 8/8 PASS. DemoralizeIntent + resolve_demoralize() in skill_resolver.
- WO-ENGINE-DEFENSIVE-CASTING-001 — 9/9 PASS (DC-005 parametrized). defensive flag on SpellCastIntent; local scoped flag pattern.

**Commit:** 8d2ff92

**Tests now passing:** ~961 (930 + 31 new Batch F gates); 2 skips FINDING-documented; zero regressions.

**New EF fields landed:**
- EF.ENERGY_RESISTANCE — dict[str, int] energy type → resistance
- EF.CONCENTRATION_BONUS — int bonus to Concentration checks
- EF.DEFLECTION_BONUS — int deflection AC bonus (landed by Batch G infrastructure prep)

**Architectural decisions made:**
- Verbal block fires BEFORE metamagic validation (correct PHB order)
- Defensive casting: local scoped flag in execute_turn() — no aoo.py coupling
- Already-shaken refresh: overwrites entry, no Frightened escalation (PHB p.76 explicit)

**Kernel touches flagged to Anvil:**
- KERNEL-03 (Constraint Algebra) — WO-ENGINE-DEFENSIVE-CASTING-001
- KERNEL-07 (Social Consequence) — WO-ENGINE-INTIMIDATE-DEMORALIZE-001

**New findings:**
- FINDING-ENGINE-NONVERBAL-SPELLS-001 — LOW. No has_verbal=False spell in registry; VS-002 skipped.
- FINDING-ENGINE-SILENCE-ZONE-001 — LOW. Environmental silence zones not tracked; VS-007 skipped.
- FINDING-ENGINE-SOCIAL-INTIMIDATE-001 — LOW. Non-combat Intimidate not wired.
- FINDING-ENGINE-CONCENTRATION-OTHER-001 — LOW. Concentration triggers NOT STARTED: taking damage while casting, grappled, vigorous motion, violent weather. Candidate for Batch H.
- FINDING-ENGINE-PHYSICAL-DR-001 — LOW. Physical DR not applied in spell_resolver.

**Batch G DISPATCHED — ENGINE DISPATCH #16:**
- WO-ENGINE-MASSIVE-DAMAGE-RULE-001 — 8 tests. attack_resolver + spell_resolver. KERNEL-01.
- WO-ENGINE-ARCANE-SPELL-FAILURE-001 — 8 tests. spell_resolver. KERNEL-03. **BLOCKER: has_somatic field — verify before writing.**
- WO-ENGINE-SOMATIC-COMPONENT-001 — 8 tests. spell_resolver. KERNEL-02. **Same blocker.**
- WO-ENGINE-DEFLECTION-BONUS-001 — 8 tests. entity_fields + attack_resolver. KERNEL-14.

**Tests target:** ~961 + 32 = ~993 (on zero regressions)

**Open threads for next session:**
- Batch G execution and debriefs
- WO-JUDGMENT-SHADOW-001 verdict still pending
- has_somatic on SpellDefinition — blocker for WO 2 + WO 3; verify on boot
- FINDING-ENGINE-CONCENTRATION-OTHER-001 — candidate for Batch H
- FINDING-ENGINE-FLATFOOTED-AOO-001 OPEN
- FINDING-SAI-FRAGMENTATION-001 OPEN
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 LOW OPEN

---

## Session Delta — 2026-02-26 (Batch H ACCEPTED — ENGINE DISPATCH #17)

**WOs completed:**
- WO-ENGINE-CONCENTRATION-DAMAGE-001 — 8/8 PASS. `_resolve_spell_cast` gains `damage_taken_this_turn` param; `execute_turn` pre-computes from hp_changed events. KERNEL-03.
- WO-ENGINE-CONCENTRATION-GRAPPLE-001 — 8/8 PASS. Grapple/entangle Concentration guard in `_resolve_spell_cast` after somatic block. KERNEL-02.
- WO-ENGINE-FLATFOOTED-AOO-001 — 8/8 PASS. Flat-footed guard in `aoo.check_aoo_triggers` reactor loop. **Closes FINDING-ENGINE-FLATFOOTED-AOO-001.** KERNEL-06.
- WO-ENGINE-NONLETHAL-THRESHOLD-001 — 8/8 PASS. Gate-only throw. `check_nonlethal_threshold()` already implemented. KERNEL-01.

**Commit:** 109b454

**Tests now passing:** ~993 + 32 = ~1025 (zero regressions; 3 pre-existing CE failures stable).

**Coverage change:** Concentration checks (damage + grapple) land as partial → full. Flat-footed AoO closes a gap. Nonlethal threshold was already implemented.

**Architectural decisions made:**
- Guard chain order in `_resolve_spell_cast`: verbal → somatic → grapple/entangle Concentration → damage Concentration → metamagic. PHB-correct order confirmed.
- Damage Concentration: retroactive constraint — scans pre-existing event log from same turn. Clean KERNEL-03 pattern.
- Gate test bug found and fixed: `StepMoveIntent` (not `MoveIntent`) required for AoO trigger detection; `AooTrigger` is a dataclass (attribute access, not dict `.get()`).

**Kernel touches flagged to Anvil:**
- KERNEL-03 (Constraint Algebra) — WO-ENGINE-CONCENTRATION-DAMAGE-001 (retroactive damage constraint on casting)
- KERNEL-02 (Containment Topology) — WO-ENGINE-CONCENTRATION-GRAPPLE-001 (grapple restricts spell action space)
- KERNEL-06 (Termination Doctrine) — WO-ENGINE-FLATFOOTED-AOO-001 (flat-footed terminates at first-action boundary)
- KERNEL-01 (Entity Lifecycle) — WO-ENGINE-NONLETHAL-THRESHOLD-001 (five lifecycle states now fully documented)

**New findings:**
- FINDING-ENGINE-STAGGERED-ACTION-ECONOMY-001 — OPEN. STAGGERED condition flag set correctly; action economy enforcement (one move or standard action per turn, PHB p.301) NOT implemented. Future WO needed.
- FINDING-ENGINE-NONLETHAL-HEALING-001 — OPEN. Natural healing of nonlethal damage (1 HP/hour or HP/level/hour with rest) not implemented. Deferred to rest system WO.
- FINDING-ENGINE-CONCENTRATION-VIGOROUS-001 — OPEN. Vigorous motion Concentration (DC 10 + spell level) not yet implemented. Candidate for Batch I.

**FINDING CLOSED:**
- FINDING-ENGINE-FLATFOOTED-AOO-001 — CLOSED. Guard added in aoo.py.

**Open threads for next session:**
- Batch I specs from Slate
- WO-JUDGMENT-SHADOW-001 verdict still pending
- FINDING-ENGINE-STAGGERED-ACTION-ECONOMY-001 OPEN — candidate for Batch I
- FINDING-ENGINE-CONCENTRATION-VIGOROUS-001 OPEN — candidate for Batch I
- FINDING-ENGINE-NONLETHAL-HEALING-001 OPEN (rest system)
- FINDING-SAI-FRAGMENTATION-001 OPEN
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 LOW OPEN

---

## Session Delta — 2026-02-26 (OSS Data Batch A DISPATCHED)

**WOs completed:** None (Chisel not executing — PM dispatching data batch)

**OSS research complete:** All three agents (spell/armor, monster, class) landed.
Phase 0 data picture is fully resolved.

**OSS Data Batch A DISPATCHED:**
- LST-PARSER-001 — PCGen RSRD LST parser tool (~200-300 lines). Prerequisite for three downstream data WOs. Output: `data/pcgen_extracted/` JSON files.
- WO-DATA-FEATS-001 — zellfaze feats.json (CC0, 221 feats) → `aidm/data/feat_definitions.py`. No parser needed. Can execute in parallel with LST-PARSER-001.
- WO-DATA-EQUIPMENT-001 — PCGen rsrd_equip.lst → `aidm/data/equipment_definitions.py`. Armor ASF%/maxDEX/ACP. Blocked on LST-PARSER-001.
- WO-DATA-SPELLS-001 — PCGen rsrd_spells.lst → expand SPELL_REGISTRY from 45 → ~350. Component fields only; effect fields stubbed. Blocked on LST-PARSER-001.
- DATA-CLASS-TABLES-001 — PCGen rsrd_classes.lst (structural layer) + hand-extract ~8 formulas from rsrd_abilities_class.lst. Verify existing tables (spellcasting.py, rage_resolver.py). Add UDAM table + feature grant registry. Blocked on LST-PARSER-001.

**Key intelligence for Chisel (DATA batch):**
- PCGen RSRD path is `data/35e/wizards_of_the_coast/rsrd/basics/` (NOT `data/d20ogl/wotc/3.5e/phb/`)
- Spell slot tables already exist in `aidm/chargen/spellcasting.py` — DATA-CLASS-TABLES-001 verifies, does not rewrite
- Rage/sneak/LOH tables already exist in individual resolvers — DATA-CLASS-TABLES-001 centralizes, does not change behavior
- SpellDefinition dataclass: PCGen covers name/level/school/has_verbal/has_somatic/has_material only. Remaining fields default to stubs.
- rsrd_abilities_class.lst (453KB) — hand-extract ~8 formulas only; do NOT build a BONUS:VAR parser

**Data WO gate format differs from engine WOs:**
- Acceptance: spot-check table (5 entries per type vs PHB) + pytest assertions
- Missing spot-check pass → REJECT (same as missing Pass 3)
- LST-PARSER-001 has no pytest gate — human verification only

**Open threads for next session:**
- Batch I gate results (engine, in flight)
- Batch J execution (queued behind Batch I ACCEPTED)
- OSS Data Batch A execution
- WO-JUDGMENT-SHADOW-001 verdict still pending
- FINDING-ENGINE-NONLETHAL-HEALING-001 OPEN
- FINDING-SAI-FRAGMENTATION-001 OPEN
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 LOW OPEN
- FINDING-ENGINE-SOCIAL-INTIMIDATE-001 LOW OPEN

---

## Session Delta — 2026-02-26 (Engine Batch J DISPATCHED)

**WOs completed:** None (PM dispatching next engine batch)

**Engine Batch J DISPATCHED — ENGINE DISPATCH #19:**
- WO-ENGINE-IMMEDIATE-ACTION-001 — `immediate_used` slot + cross-turn swift burn. `action_economy.py` + `play_loop.py`. 8 tests. KERNEL-06.
- WO-ENGINE-SOMATIC-HAND-FREE-001 — `EF.FREE_HAND_BLOCKED`; guard before ASF roll. `entity_fields.py` + `spell_resolver.py`. 8 tests. KERNEL-02.
- WO-ENGINE-SKILL-SYNERGY-001 — PHB p.65 synergy table, +2 circumstance at skill_resolver accumulation point. `skill_resolver.py` only. 8 tests. KERNEL-14.
- WO-ENGINE-RUN-ACTION-001 — `ConditionType.RUNNING` + `RunIntent` + routing. `conditions.py` + `intents.py` + `play_loop.py`. 8 tests. KERNEL-06.

**Gate target:** ~1089 (after Batch I + Batch J)

**Key intelligence for Batch J execution:**
- `EF.DEFLECTION_BONUS` already wired in `attack_resolver.py:437` — do NOT re-implement
- WO 1 and WO 4 both touch `play_loop.py` — commit WO 1 first, clean full suite, then WO 4
- Guard chain position for WO 2: verbal → somatic hand-free (new) → ASF% → grapple Concentration → damage Concentration → metamagic
- STAGGERED guard (Batch I) should already block RunIntent as full-round — verify before WO 4

**Open threads for next session (Batch J):**
- Batch I gate results (awaited)
- Batch J execution
- Batch K execution (queued behind Batch J)
- OSS Data Batch A execution
- WO-JUDGMENT-SHADOW-001 verdict still pending
- FINDING-ENGINE-NONLETHAL-HEALING-001 OPEN
- FINDING-SAI-FRAGMENTATION-001 OPEN
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 LOW OPEN
- FINDING-ENGINE-SOCIAL-INTIMIDATE-001 LOW OPEN

---

## Session Delta — 2026-02-26 (Batch K Dispatch)

**WOs dispatched:**
- ENGINE DISPATCH #20 — Batch K (4 WOs, 32 gate tests, target ~1121)
  - WO-ENGINE-COWERING-FASCINATED-001 — `aidm/schemas/conditions.py` only
  - WO-ENGINE-DIEHARD-001 — `aidm/core/dying_resolver.py` only
  - WO-ENGINE-CLERIC-SPONTANEOUS-001 — `aidm/schemas/intents.py` + `aidm/core/spell_resolver.py`
  - WO-ENGINE-IMPROVED-CRITICAL-001 — `aidm/core/full_attack_resolver.py` (+ possibly `attack_resolver.py`)

**Coverage map CRITICAL NOTE — stale "NOT STARTED" entries already closed (verified by grep):**
- Stabilize Ally → `stabilize_resolver.py` wired at `play_loop.py:2489`
- Evasion/Improved Evasion → `spell_resolver.py:895-912`
- Energy Resistance → `spell_resolver.py:921`
- Intimidate/Demoralize → `skill_resolver.py:284+`, `play_loop.py:3295`
- Verbal Spell Block, Defensive Casting → closed (Batch F/G)
- Massive Damage → `attack_resolver.py:755-783`
- Take 10 / Take 20 → `retry_policy.py:64+`
- Disarm two-handed advantage → `maneuver_resolver.py:1405-1413`
- Deflection bonus → `attack_resolver.py:435-437`
- AoO Stand from Prone → `aoo.py:709+`, `play_loop.py:3312`
- Great Fortitude/Iron Will/Lightning Reflexes → `save_resolver.py:128-133`
⚠ DO NOT re-implement any of the above. Verify before writing.

**Key intelligence for Batch K execution:**
- `ConditionType.COWERING` and `ConditionType.FASCINATED` — confirmed absent; add to enum + ConditionModifiers
- Diehard: feat_id `"diehard"`, check `EF.FEATS` list; insert in `resolve_dying_tick()` before Fort save
- Cleric spontaneous: verify cure spells in SPELL_REGISTRY before writing; add `spontaneous_cure` flag to SpellCastIntent
- Improved Critical: formula `21 - (21 - base) * 2`; check whether feat is per-weapon-type or generic in registry

**Gate target:** ~1121 (after Batch I + J + K)

**Open threads for Batch K session:**
- Batch I and J results awaited
- Batch K execution queued
- OSS Data Batch A execution queued
- WO-JUDGMENT-SHADOW-001 verdict pending
- Coverage map update required (many stale entries)
- FINDING-ENGINE-NONLETHAL-HEALING-001 OPEN
- FINDING-SAI-FRAGMENTATION-001 OPEN
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 LOW OPEN
- FINDING-ENGINE-SOCIAL-INTIMIDATE-001 LOW OPEN

---

## Session Delta — 2026-02-26 (Batch I ACCEPTED)

**WOs completed:**
- WO-ENGINE-STAGGERED-ACTION-ECONOMY-001 — SA-001..SA-008 8/8 PASS
- WO-ENGINE-CONCENTRATION-VIGOROUS-001 — CV-001..CV-008 8/8 PASS
- WO-ENGINE-DAZZLED-CONDITION-001 — DZ-001..DZ-008 8/8 PASS
- WO-ENGINE-AOO-STAND-FROM-PRONE-001 — SP-001..SP-008 8/8 PASS

**Commit:** f671cdb
**Gate total (Batch I):** 32 new gates passing; 252 gate tests run in regression check; 0 regressions

**Coverage delta:**
- STAGGERED action economy: was PARTIAL (flag metadata only) → FULL
- MOTION STATE concentration: was NOT STARTED → FULL
- DAZZLED condition: was NOT STARTED → FULL
- AoO Stand from Prone: was PARTIAL (flag metadata only) → FULL

**Key technical findings:**
- `StepMoveIntent` maps to `five_foot_step` (not `"move"`) — use `MoveIntent` or `StandIntent` for move-action tests
- `Weapon` dataclass: no `name` field; required fields are `damage_dice`, `damage_bonus`, `damage_type`
- `EF.CONDITIONS` values MUST be fully serialized `ConditionInstance` dicts — bare `{}` silently skips in `get_condition_modifiers()`
- `FullAttackIntent` lives in `aidm.core.full_attack_resolver`, not `aidm.schemas.intents`

**FINDING-ENGINE-CRAWL-PRONE-001 (NEW):**
Prone creature can crawl at half speed without triggering standing-from-prone AoO (PHB p.137). WO-ENGINE-AOO-STAND-FROM-PRONE-001 only covers the "stand" action. Crawling-while-prone is AoO-exempt and requires separate WO. OPEN.

**Kernel touches:**
- KERNEL-06 (Termination Doctrine): stand-from-prone AoO fires BEFORE prone is cleared. Guard order in play_loop confirmed correct.

**Closed findings:**
- FINDING-AOO-STAND-FROM-PRONE (partial/metadata-only) → CLOSED by this batch

**Open threads for Batch J:**
- Batch J execution queued: Immediate Action, Somatic Hand-Free, Skill Synergy, Run Action
- Batch K execution queued: Cowering/Fascinated, Diehard, Cleric Spontaneous, Improved Critical
- Coverage map needs full audit — many "NOT STARTED" already closed
- FINDING-ENGINE-CRAWL-PRONE-001 OPEN
- FINDING-ENGINE-NONLETHAL-HEALING-001 OPEN
- FINDING-SAI-FRAGMENTATION-001 OPEN
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 LOW OPEN
- FINDING-ENGINE-SOCIAL-INTIMIDATE-001 LOW OPEN

---

## Session Delta — 2026-02-26 (Batch L Dispatch)

**WOs completed:** None (PM dispatching next engine batch)

**Engine Batch L DISPATCHED — ENGINE DISPATCH #21:**
- WO-ENGINE-IMPROVED-DISARM-001 — `aidm/core/play_loop.py` only. AoO suppression after `check_aoo_triggers()`: if DisarmIntent + `"improved_disarm"` in attacker feats → `aoo_triggers = []`. 8 tests. KERNEL-06.
- WO-ENGINE-IMPROVED-GRAPPLE-001 — `aidm/core/play_loop.py` only. elif branch: GrappleIntent + `"improved_grapple"` → `aoo_triggers = []`. 8 tests. KERNEL-02, KERNEL-06.
- WO-ENGINE-IMPROVED-BULL-RUSH-001 — `aidm/core/play_loop.py` only. elif branch: BullRushIntent + `"improved_bull_rush"` → `aoo_triggers = []`. Note: Bull Rush triggers from ALL threatening enemies (aoo.py `provokes_from_all = True`) — feat suppresses all of them. 8 tests. KERNEL-06.
- WO-ENGINE-SPELL-PENETRATION-001 — `aidm/core/save_resolver.py` only. Insert before `total = d20_result + sr_check.caster_level` in `check_spell_resistance()`: +2 for `"spell_penetration"`, +2 for `"greater_spell_penetration"` (stacks per PHB p.94). Add `"penetration_bonus": _sp_bonus` to event payload. 8 tests. KERNEL-14.

**Gate target:** ~1153 (after Batch I + J + K + L)

**Key intelligence for Batch L execution:**
- AoO suppression insertion point: `play_loop.py:2132` — AFTER `aoo_triggers = check_aoo_triggers(...)`, BEFORE `if aoo_triggers:`. Defensive casting bypass at lines 2134-2186 is the exact model.
- All three maneuver checks go in one if/elif/elif block. Commit order: WOs 1+2+3 together (same play_loop.py section) → gate all three → WO 4 separately (save_resolver.py).
- SR check insertion: `save_resolver.py:193` — `total = d20_result + sr_check.caster_level`. Replace line with `total = d20_result + sr_check.caster_level + _sp_bonus`. `world_state` is second param — available.
- `SRCheck.source_id` = caster entity ID (confirmed schemas/saves.py:66-67). Feat lookup: `world_state.entities.get(sr_check.source_id, {}).get(EF.FEATS, [])`.
- Feat IDs to verify before writing: `"improved_disarm"`, `"improved_grapple"`, `"improved_bull_rush"`, `"spell_penetration"`, `"greater_spell_penetration"` — confirm in `aidm/schemas/feats.py`.
- No auto-fail rule for SR checks (unlike saves where d20=1 auto-fails). PHB p.174 natural 1 auto-fail applies to saves only.
- ⚠ Coverage map is severely stale — 11+ "NOT STARTED" entries already closed. Grep before writing any WO.

**New findings (Batch L pre-dispatch analysis):**
- FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 — LOW. Improved Disarm second PHB benefit: opponent does not counter-disarm when your disarm fails. Only AoO suppression is in scope for this WO. Future WO.
- FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001 — LOW. Improved Grapple also grants +4 on grapple checks. Not verified in maneuver_resolver.py. Future verification WO.
- FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001 — LOW. Improved Bull Rush also grants +4 on STR bull rush checks. Not in scope for this WO.

**Open threads for Batch L session:**
- Batch J execution queued (ENGINE DISPATCH #19)
- Batch K execution queued (ENGINE DISPATCH #20)
- Batch L execution queued (ENGINE DISPATCH #21)
- OSS Data Batch A execution queued (LST-PARSER-001 + 4 data WOs)
- WO-JUDGMENT-SHADOW-001 verdict still pending
- Coverage map full audit needed — many stale NOT STARTED entries
- FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 LOW OPEN
- FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001 LOW OPEN
- FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001 LOW OPEN
- FINDING-ENGINE-CRAWL-PRONE-001 OPEN
- FINDING-ENGINE-NONLETHAL-HEALING-001 OPEN
- FINDING-SAI-FRAGMENTATION-001 OPEN
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 LOW OPEN
- FINDING-ENGINE-SOCIAL-INTIMIDATE-001 LOW OPEN

---

## Session Delta — 2026-02-27 (Batch K ACCEPTED — ENGINE DISPATCH #20)

**WOs completed:**
- WO-ENGINE-COWERING-FASCINATED-001 — 8/8 CF PASS. `conditions.py` only.
- WO-ENGINE-DIEHARD-001 — 8/8 DH PASS. `dying_resolver.py` only.
- WO-ENGINE-CLERIC-SPONTANEOUS-001 — 10/10 CS PASS (2 bonus tests). `spell_resolver.py` + `play_loop.py`.
- WO-ENGINE-IMPROVED-CRITICAL-001 — 8/8 IC PASS. `full_attack_resolver.py` + `attack_resolver.py`.

**Commit:** 4cb2f72

**Tests now passing:** 34/34 new gates; 0 regressions.

**New findings:**
- FINDING-ENGINE-FASCINATED-SKILL-PENALTY-001 — -4 reactive Spot/Listen not wired (no `reactive_skill_modifier` field in ConditionModifiers). Future WO.
- FINDING-ENGINE-DIEHARD-TRANSITION-001 — Diehard fires at bleed tick, not damage event. One-round DYING window exists. PHB delta documented. Architectural fix deferred.
- FINDING-ENGINE-CURE-SPELL-REGISTRY-001 — `mass_cure_light_wounds` absent from SPELL_REGISTRY; level-5 spontaneous cure fails gracefully. Registry gap.
- FINDING-ENGINE-IMPROVED-CRITICAL-WEAPON-SCOPE-001 — `weapon_type` is categorical (`one-handed`, `light`), not specific weapon name. Per-category feat IDs (`improved_critical_one-handed`). PHB intends per-weapon-name — structural gap.
- FINDING-ENGINE-IMPROVED-CRITICAL-KEEN-STACK-001 — PHB: Improved Critical does not stack with Keen weapon quality. Documented for future Keen WO; deduplication logic required at that time.

**Kernel touches flagged:**
- KERNEL-01 (Entity Lifecycle) — Diehard fires at lifecycle boundary (DYING→DISABLED transition)
- KERNEL-03 (Constraint Algebra) — Cleric spontaneous redirect rewrites spell before slot governor runs

---

## Session Delta — 2026-02-27 (OSS Data Batch A ACCEPTED)

**WOs completed:**
- LST-PARSER-001 — DONE (offline tool, no pytest gate). `scripts/parse_pcgen_lst.py`.
- WO-DATA-FEATS-001 — 8/8 FD PASS. zellfaze feats.json → `aidm/data/feat_definitions.py`.
- WO-DATA-EQUIPMENT-001 — 8/8 EQ PASS. PCGen `rsrd_equip.lst` → `aidm/data/equipment_definitions.py`.
- WO-DATA-SPELLS-001 — 8/8 SP PASS. PCGen `rsrd_spells.lst` → expanded SPELL_REGISTRY (~45 → ~350).
- DATA-CLASS-TABLES-001 — 8/8 CT PASS. PCGen `rsrd_classes.lst` structural layer + hand-extracted formulas.

**Commit:** 0b73fb9

**Tests now passing:** 32/32 new data gates; 8,152 existing passing; 0 regressions.
Note: `test_ws_bridge` and `test_ws_deadverb_001_gate` excluded — require live WebSocket server, hang without one. Pre-existing exclusion.

**Coverage impact:** Spell registry ~45 → ~350. Armor ASF%/maxDEX/ACP table live. Feat benefit data live. Class tables (spell slots, UDAM, feature grants) verified/extended. Pure data registries — no import side effects.

**Note on FINDING-ENGINE-CURE-SPELL-REGISTRY-001:** `mass_cure_light_wounds` gap may now be closeable with expanded spell registry from WO-DATA-SPELLS-001. Verify before drafting fix WO.

**Open threads:**
- Batch L execution queued (ENGINE DISPATCH #21)
- WO-JUDGMENT-SHADOW-001 verdict still pending
- FINDING-ENGINE-FASCINATED-SKILL-PENALTY-001 OPEN
- FINDING-ENGINE-DIEHARD-TRANSITION-001 OPEN
- FINDING-ENGINE-CURE-SPELL-REGISTRY-001 OPEN (may be closeable — verify)
- FINDING-ENGINE-IMPROVED-CRITICAL-WEAPON-SCOPE-001 OPEN
- FINDING-ENGINE-IMPROVED-CRITICAL-KEEN-STACK-001 OPEN
- FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 LOW OPEN
- FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001 LOW OPEN
- FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001 LOW OPEN
- FINDING-ENGINE-CRAWL-PRONE-001 OPEN
- FINDING-ENGINE-NONLETHAL-HEALING-001 OPEN
- FINDING-SAI-FRAGMENTATION-001 OPEN
- FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN
- FINDING-UI-CALLED-SHOT-SUGGESTIONS-001 LOW OPEN
- FINDING-ENGINE-SOCIAL-INTIMIDATE-001 LOW OPEN
---

## Session Delta — 2026-02-27 (Batch O ACCEPTED — ENGINE DISPATCH)

**WOs completed:**
- WO-ENGINE-IMPROVED-OVERRUN-001 — IO-001–IO-008 8/8 PASS. `play_loop.py` (AoO suppression) + `maneuver_resolver.py` (defender-avoid suppression). Commit 3232b76.
- WO-ENGINE-COMBAT-EXPERTISE-001 — CE-001–CE-008 8/8 PASS. **SAI.** `attack_resolver.py` + `entity_fields.py` already wired; test file was untracked. Committed test file only. Commit 9d5b6f5.
- WO-ENGINE-BLIND-FIGHT-001 — BF-001–BF-008 8/8 PASS. `attack_resolver.py` WO-049 miss-chance block extended with Blind-Fight reroll. `blind_fight_reroll` event emitted on every reroll (success or failure). Commit 6057476.
- WO-ENGINE-TOUGHNESS-001 — TG-001–TG-008 8/8 PASS. `builder.py` — `build_character()` + `_build_multiclass_character()` + `level_up()` all updated. Stackable feat pattern via `list.count("toughness")`. Commit 99d79af.

**Gate total:** 32/32 new gates; 0 regressions.

**New findings:**
- FINDING-ENGINE-BLIND-FIGHT-INVIS-001 (LOW) — PHB p.91: Blind-Fight also grants (1) no loss of DEX bonus vs invisible, (2) melee penalty vs invisible reduced. Not scoped to BF-001 WO. Site: invisible-attacker handling path. OPEN.
- FINDING-ENGINE-IMPROVED-OVERRUN-BONUS-001 (LOW) — Improved Overrun should also grant +4 STR check bonus (parallel to Improved Bull Rush/Grapple). Only AoO suppression and defender-avoid suppression wired. OPEN.

**Patterns established:**
- **Stackable feat via `list.count()`** — use for any feat taken multiple times. `"toughness" in FEATS` only counts one instance.
- **AoO suppression for maneuver feats** — always in `play_loop.py` after `check_aoo_triggers()`, if/elif chain at lines ~2257–2281. NOT in `aoo.py`.
- **Blind-Fight reroll event** — emit `blind_fight_reroll` unconditionally when reroll occurs, even on failure.

**Kernel touches flagged:**
- KERNEL-01 (Entity Lifecycle) — WO-ENGINE-TOUGHNESS-001: HP_MAX set at builder time; Toughness modifies baseline.

**Closed findings:**
- FINDING-ENGINE-IMPROVED-OVERRUN-AOO-001 — CLOSED. Wired in this batch.

**Open threads for next session:**
- Batch P execution (queued)
- FINDING-ENGINE-BLIND-FIGHT-INVIS-001 LOW OPEN
- FINDING-ENGINE-IMPROVED-OVERRUN-BONUS-001 LOW OPEN
- All prior open findings carried forward (see OSS Data Batch A delta above)
