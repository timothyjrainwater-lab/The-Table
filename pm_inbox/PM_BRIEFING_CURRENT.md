# PM Briefing — Current

**Last updated:** 2026-02-28 (session 22) — **Batch AF ACCEPTED (33/33). 1,168 gate tests. 0 MEDIUM in flight. 4 coverage rows updated. 1 new LOW finding. Next sweep audit due in 3 batches.**

---

## Stoplight: GREEN

7,211 passed / 149 pre-existing failures, 0 new gate failures. 1,168 gate tests. Commit `2edf076`. UI pivot locked — 3D client frozen, client2d/ track open.

| Gate | Tests | Gate | Tests | Gate | Tests |
|------|-------|------|-------|------|-------|
| A | 22/22 | G | 22/22 | N | 37/37 |
| B | 23/23 | H | 16/16 | O | 47/47 |
| C | 24/24 | I | 13/13 | P | 22/22 |
| D | 18/18 | J | 27/27 | Q | 33/33 |
| E | 14/14 | K | 72/72 | R | 18/18 |
| F | 10/10 | L | 32/32 | S | 31/31 |
|   |       | M | 31/31 | T | 23/23 |
|   |       |   |       | U | 20/20 |
|   |       |   |       | V | 22/22 |
|   |       |   |       | W | 14/14 |
|   |       |   |       | CL2 | 8/8 |
|   |       |   |       | X | 9/10 |
|   |       |   |       | Y (UI) | 6/6 |
|   |       |   |       | Z | 7/7 |
|   |       |   |       | AA | 7/7 |
|   |       |   |       | AB | 32/32 |
|   |       |   |       | SAVE-FIX | 16/16 |
|   |       |   |       | AC | 32/32 |
|   |       |   |       | AD | 33/33 |
|   |       |   |       | AE | 32/32 |
|   |       |   |       | V7 | 73/73 |
|   |       |   |       | V8 | 15/15 |
|   |       |   |       | V9 | 20/20 |
|   |       |   |       | V10 | 25/25 |
|   |       |   |       | V11 | 18/18 |
|   |       |   |       | V12 | 20/20 |
|   |       |   |       | UI-CAMERAS | 6/6 |
|   |       |   |       | UI-OBJECT-LAYOUT | 10/10 |
|   |       |   |       | UI-06 | 10/10 |
|   |       |   |       | BURST-003 | 10/10 |
|   |       |   |       | BURST-002 | 12/12 |
|   |       |   |       | WP | 5+18+19 |
|   |       |   |       | XP-01 | 19/19 |
|   |       |   |       | TOOLS-DUMP | 7/7 |
|   |       |   |       | CP-17 | 15/15 |
|   |       |   |       | CP-18 | 10/10 |
|   |       |   |       | CP-19 | 12/12 |
|   |       |   |       | CP-21 | 12/12 |
|   |       |   |       | CP-22 | 14/14 |
|   |       |   |       | CP-23 | 10/10 |
|   |       |   |       | CP-24 | 12/12 |
|   |       |   |       | UI-CB-PORTRAIT | 10/10 |
|   |       |   |       | UI-CS-LIVE | 16/16 |
|   |       |   |       | UI-NB-DRAW | 6/6 |
|   |       |   |       | UI-TOKEN-CHIP | 10/10 |
|   |       |   |       | UI-BESTIARY-IMG | 6/6 |
|   |       |   |       | UI-HANDOUT-READ | 4/4 |
|   |       |   |       | UI-FOG-FADE | 5/5 |
|   |       |   |       | UI-LASSO-FADE | 4/4 |
|   |       |   |       | UI-TOKEN-LABEL | (bundled) |
|   |       |   |       | UI-SCENE-IMG | 6/6 |
|   |       |   |       | UI-TEXT-INPUT | 5/5 |
|   |       |   |       | UI-FOG-VISION | 5/5 |
|   |       |   |       | UI-LIGHTING | 6/6 |
|   |       |   |       | UI-LAYOUT-PACK | 8/8 |
|   |       |   |       | UI-CAMERAS | 6/6 |
|   |       |   |       | UI-OBJECT-LAYOUT | 10/10 |
|   |       |   |       | UI-PHYSICALITY-BASELINE | 8/8 |
|   |       |   |       | ENGINE-SPELL-SLOTS | 12/12 |
|   |       |   |       | ENGINE-REST | 12/12 |
|   |       |   |       | ENGINE-CONCENTRATION | 10/10 |
|   |       |   |       | ENGINE-DR | 10/10 |
|   |       |   |       | ENGINE-NONLETHAL | 10/10 |
|   |       |   |       | ENGINE-COUP-DE-GRACE | 10/10 |
|   |       |   |       | ENGINE-CHARGE | 10/10 |
|   |       |   |       | ENGINE-TURN-UNDEAD | 10/10 |
|   |       |   |       | ENGINE-ENERGY-DRAIN | 12/12 |
|   |       |   |       | ENGINE-GOLD-MASTER-REGEN | 9/9 (replay) |
|   |       |   |       | ENGINE-READIED-ACTION | 10/10 |
|   |       |   |       | ENGINE-AID-ANOTHER | 10/10 |
|   |       |   |       | ENGINE-DEFEND | 10/10 |
|   |       |   |       | ENGINE-FEINT | 10/10 |
|   |       |   |       | UI-VISREG-PLAYWRIGHT | (pending) |
|   |       |   |       | ENGINE-ABILITY-DAMAGE | 10/10 |
|   |       |   |       | ENGINE-POISON-DISEASE | 10/10 |
|   |       |   |       | ENGINE-WITHDRAW-DELAY | 10/10 |
|   |       |   |       | ENGINE-CONDITIONS-BLIND-DEAF | 19/19 |
|   |       |   |       | ENGINE-SUNDER-DISARM-FULL | 10/10 |
|   |       |   |       | ENGINE-TWD | 8/8 |
|   |       |   |       | ENGINE-METAMAGIC | 30/30 |
|   |       |   |       | UI-2D-FOUNDATION | 10/10 |
|   |       |   |       | UI-2D-RELAYOUT | 12/12 |
|   |       |   |       | UI-2D-RELAYOUT-002 | 14/14 |
|   |       |   |       | UI-2D-ORB | 12/12 |
|   |       |   |       | UI-2D-DM-PANEL | 10/10 |
|   |       |   |       | UI-2D-MAP | 12/12 |
|   |       |   |       | UI-2D-SLIP | 10/10 |
|   |       |   |       | UI-2D-SHEET | 10/10 |
|   |       |   |       | UI-2D-NOTEBOOK | 10/10 |
|   |       |   |       | ENGINE-MANEUVER | 14/14 |
|   |       |   |       | ENGINE-CLEAVE | 10/10 |
|   |       |   |       | ENGINE-BARBARIAN-RAGE | 10/10 |
|   |       |   |       | ENGINE-SMITE-EVIL | 8/8 |
|   |       |   |       | ENGINE-BARDIC-MUSIC | 10/10 |
|   |       |   |       | ENGINE-WILD-SHAPE | 10/10 |
|   |       |   |       | ENGINE-NATURAL-ATTACK | 10/10 |
|   |       |   |       | ENGINE-PLAY-LOOP-ROUTING | 10/10 |
|   |       |   |       | ENGINE-BARDIC-DURATION | 10/10 |
|   |       |   |       | ENGINE-WILDSHAPE-DURATION | 10/10 |
|   |       |   |       | ENGINE-WILDSHAPE-HP | 10/10 |
|   |       |   |       | ENGINE-CONDITION-DURATION | 10/10 |
|   |       |   |       | ENGINE-LAY-ON-HANDS | 11/11 |
|   |       |   |       | ENGINE-SNEAK-ATTACK-IMMUNITY | 10/10 |
|   |       |   |       | ENGINE-DIVINE-HEALTH | 8/8 |
|   |       |   |       | ENGINE-PARSER-NARRATION | 9/9 |
|   |       |   |       | ENGINE-FAVORED-ENEMY | 10/10 |
|   |       |   |       | ENGINE-MASSIVE-DAMAGE | 10/10 |
|   |       |   |       | ENGINE-WEAPON-ENHANCEMENT | 10/10 |
|   |       |   |       | ENGINE-STABILIZE-ALLY | 10/10 |
|   |       |   |       | ENGINE-CHARGEN-POOL-INIT | 10/10 |
|   |       |   |       | ENGINE-SKILL-MODIFIER (SM) | 8/8 |
|   |       |   |       | ENGINE-RETRY-002 (RT2) | 11/11 |
|   |       |   |       | ENGINE-RETRY-001 (RP) | 14/14 |
|   |       |   |       | ENGINE-SAVE-FEATS (SF) | 10/10 |
|   |       |   |       | ENGINE-SPELL-FOCUS-DC (SFD) | 10/10 |
|   |       |   |       | ENGINE-ARCANE-SPELL-FAILURE (ASF) | 10/10 |
|   |       |   |       | ENGINE-CONDITION-ENFORCEMENT (CE) | 12/12 |
|   |       |   |       | ENGINE-RETRY-POLICY (RP2) | 15/15 |
|   |       |   |       | ENGINE-CLEAVE-ADJACENCY (CA) | 6/6 |
|   |       |   |       | ENGINE-COMBAT-EXPERTISE (CEX) | 8/8 |
|   |       |   |       | ENGINE-EVASION (EV) | 10/10 |
|   |       |   |       | ENGINE-DIVINE-GRACE (DG) | 8/8 |
|   |       |   |       | ENGINE-WEAPON-FINESSE (WF) | 8/8 |
|   |       |   |       | ENGINE-COMBAT-REFLEXES (CR) | 8/8 |
|   |       |   |       | ENGINE-STAGGERED-ACTION-ECONOMY (SA) | 8/8 |
|   |       |   |       | ENGINE-CONCENTRATION-VIGOROUS (CV) | 8/8 |
|   |       |   |       | ENGINE-DAZZLED-CONDITION (DZ) | 8/8 |
|   |       |   |       | ENGINE-AOO-STAND-FROM-PRONE (AP) | 8/8 |
|   |       |   |       | ENGINE-IMMEDIATE-ACTION (IA) | 8/8 |
|   |       |   |       | ENGINE-SOMATIC-HAND-FREE (SH) | 8/8 |
|   |       |   |       | ENGINE-SKILL-SYNERGY (SS) | 8/8 |
|   |       |   |       | ENGINE-RUN-ACTION (RN) | 8/8 |
|   |       |   |       | ENGINE-COWERING-FASCINATED (CF) | 8/8 |
|   |       |   |       | ENGINE-DIEHARD (DH) | 8/8 |
|   |       |   |       | ENGINE-CLERIC-SPONTANEOUS (CS) | 10/10 |
|   |       |   |       | ENGINE-IMPROVED-CRITICAL (IC) | 8/8 |
|   |       |   |       | ENGINE-IMPROVED-DISARM (ID) | 8/8 |
|   |       |   |       | ENGINE-IMPROVED-GRAPPLE (IG) | 8/8 |
|   |       |   |       | ENGINE-IMPROVED-BULL-RUSH (IB) | 8/8 |
|   |       |   |       | ENGINE-SPELL-PENETRATION (SP) | 8/8 |
|   |       |   |       | DATA-FEATS (FD) | 8/8 |
|   |       |   |       | DATA-EQUIPMENT (EQ) | 8/8 |
|   |       |   |       | DATA-SPELLS (SP2) | 8/8 |
|   |       |   |       | DATA-CLASS-TABLES (CT) | 8/8 |
|   |       |   |       | ENGINE-BARBARIAN-DR (BDR) | 8/8 |
|   |       |   |       | ENGINE-RACIAL-SAVES (RSV) | 9/9 |
|   |       |   |       | ENGINE-EXTRA-TURNING (ETN) | 8/8 |
|   |       |   |       | ENGINE-MONK-UNARMED-PROGRESSION (MUP) | 8/8 |
|   |       |   |       | ENGINE-POWER-ATTACK (PA) | 8/8 |
|   |       |   |       | ENGINE-IMPROVED-MANEUVER-BONUSES (IMB) | 8/8 |
|   |       |   |       | ENGINE-PRECISE-SHOT (PS) | 8/8 |
|   |       |   |       | ENGINE-IMPROVED-DISARM-COUNTER (IDC) | 8/8 |
|   |       |   |       | ENGINE-MULTIATTACK (MA) | 8/8 |
|   |       |   |       | ENGINE-IMPROVED-NATURAL-ATTACK (INA) | 8/8 |
|   |       |   |       | ENGINE-IMPROVED-TURNING (ITN) | 8/8 |
|   |       |   |       | ENGINE-PA-2H (PA2H) | 8/8 |
|   |       |   |       | DATA-DEAD-FILES-CLEANUP (DDC) | 4/4 |
|   |       |   |       | ENGINE-AE-DEAD-MODULE (AED) | 2/2 |
|   |       |   |       | ENGINE-AE-INTENT-MAPPING (AEM) | 6/6 |
|   |       |   |       | ENGINE-DOMAIN-SYSTEM (DOM) | 6/6 |
|   |       |   |       | ENGINE-UNCANNY-DODGE-CLASS-FIX (UDCF) | 8/8 |
|   |       |   |       | ENGINE-FAST-MOVEMENT-LOAD-FIX (FMLF) | 8/8 |
|   |       |   |       | ENGINE-MD-SAVE-RULES (MDSR+FSKL) | 8/8 |
|   |       |   |       | ENGINE-ATTACK-MODIFIER-FIDELITY (FECM+SNSH) | 8/8 |
|   |       |   |       | INFRA-SQLITE-CONSOLIDATION | 8/8 |
|   |       |   |       | ENGINE-SR-SPELL-PATH | 8/8 |
|   |       |   |       | ENGINE-RAGE-HP-TRANSITION (RHPT) | 8/8 |
|   |       |   |       | ENGINE-FATIGUE-MOBILITY (FMOB) | 8/8 |
|   |       |   |       | ENGINE-WS-FORMULA-FIX (WSFF) | 8/8 |
|   |       |   |       | ENGINE-DISARM-FIDELITY (DSFX) | 8/8 |
|   |       |   |       | ENGINE-CONCENTRATION-WRITE (CW) | 8/8 |
|   |       |   |       | ENGINE-SAVE-DOUBLE-COUNT-FIX (SDF) | 8/8 |
|   |       |   |       | ENGINE-MANEUVER-BAB-FIX (MBF) | 8/8 |
|   |       |   |       | ENGINE-SPELL-SAVE-UNIFY (SSU) | 8/8 |
|   |       |   |       | AF-LOH-PLAYLOOP | 8/8 |
|   |       |   |       | AF-MONK-UNARMED-WIRE (MUW) | 8/8 |
|   |       |   |       | AF-REMOVE-DISEASE (RD) | 9/9 |
|   |       |   |       | AF-DEFENSIVE-ROLL (DR) | 8/8 |

*Note: All Anvil UI gap WOs ACCEPTED. 12/12. Layout pack WOs: LAYOUT-PACK + CAMERAS + OBJECT-LAYOUT + LIGHTING + PHYSICALITY-BASELINE ACCEPTED (38/38 gates). ENGINE-SPELL-SLOTS-001 12/12 + ENGINE-REST-001 12/12 ACCEPTED. ENGINE-GOLD-MASTER-REGEN 9/9 + ENGINE-READIED-ACTION 10/10 + ENGINE-AID-ANOTHER 10/10 + ENGINE-DEFEND 10/10 + ENGINE-FEINT 10/10 — ENGINE DISPATCH #5 ALL ACCEPTED. ENGINE DISPATCH #6 ALL ACCEPTED: ABILITY-DAMAGE 10/10 + WITHDRAW-DELAY 10/10 + CONDITIONS-BLIND-DEAF 19/19 + SUNDER-DISARM-FULL 10/10 + POISON-DISEASE 10/10 (59/59 gate tests). Builder fix: SD-09 spurious Weapon() field names removed. 182 engine gate tests all pass. GATES-V1 blocked on golden frames. ENGINE BATCH B R1 ALL ACCEPTED (34/34): EVASION 10/10 + DIVINE-GRACE 8/8 + WEAPON-FINESSE 8/8 + COMBAT-REFLEXES 8/8. ENGINE BATCH C PARTIAL ACCEPTED (14/14): CLEAVE-ADJACENCY 6/6 + COMBAT-EXPERTISE 8/8. Coverage: 50.2% → 48.3% MISSING (first time below 50%). FINDING-ENGINE-FLATFOOTED-AOO-001 filed.*

**Gate test total:** 1,168 (1,135 prior + 33 Batch AF = 1,168 gate tests). All gates PASS. Pre-existing failures: 149.

## Operator Action Queue (max 3)

**BATCH W — ACCEPTED (2026-02-28 — session 15):**
4/4 WOs accepted. 32/32 gate tests pass. Commits 61e1da1/fce3865/eb625e4/f42e479.
- **WO1 — ENGINE-RACIAL-ENCHANT-SAVE-001** — ACCEPTED. Elf/half-elf +2 enchantment save (save_resolver.py school param + play_loop TargetStats path) + sleep immunity guard. Dual save path covered. Closes FINDING-ENGINE-RACIAL-ENCHANTMENT-SAVE-001 + FINDING-ENGINE-RACIAL-SLEEP-IMMUNITY-001.
- **WO2 — ENGINE-RACIAL-SKILL-BONUS-001** — ACCEPTED. Single compute site (session_orchestrator — dispatch spec was wrong about two sites). Closes FINDING-ENGINE-RACIAL-SKILL-BONUS-001.
- **WO3 — ENGINE-RACIAL-ATTACK-BONUS-001** — ACCEPTED. EF.CREATURE_SUBTYPES added. Dwarf/gnome/halfling attack bonuses wired in attack_resolver. FAGU parity confirmed. Closes FINDING-ENGINE-RACIAL-ATTACK-BONUS-001. New finding: FINDING-ENGINE-CREATURE-SUBTYPES-REGISTRY-001 (LOW OPEN).
- **WO4 — ENGINE-RACIAL-DODGE-AC-001** — ACCEPTED. Flat-footed suppression via existing DEX-strip pattern. aoo.py delegates — no touch required. Closes FINDING-ENGINE-RACIAL-DODGE-AC-001.
PM Notes: 3 documentation quality gaps noted for future debrief improvement (call site enumeration, test setup description, diff format). Not functional failures.

**CL2 — ACCEPTED (2026-02-28 — session 15):**
`WO-ENGINE-CASTER-LEVEL-2-001` — 8/8 gates pass (commits 64bf5a5/bc12ab5/ab1887b). SAI — implementation pre-dated dispatch. `_get_caster_level(entity, use_secondary)` at play_loop.py:181. Consume-site chain: chargen write → _get_caster_level() read → healing delta observable → CL2-003/004 prove differentiation. PM Acceptance Notes 5/5 satisfied. Closes FINDING-ENGINE-CASTER-LEVEL-2-WRITE-ONLY-001. 3 new findings filed (1 MEDIUM: SR not in spell path; 2 LOW: CL-scaled damage/duration missing).

**BATCH X — ACCEPTED (2026-02-28 — session 16):**
4/4 WOs accepted. 32/32 gate tests pass. Commits fd792d8/d53c604/d0a36ce/9e36811/4fe933d.
- **WO1 — ENGINE-UNCANNY-DODGE-CLASS-FIX-001** — ACCEPTED 8/8 (UDCF). `_UD_THRESHOLDS = {"barbarian": 2, "rogue": 4}` — ranger removed entirely. Rogue threshold L2→L4. Single touch site (FAGU delegation). Closes FINDING-ENGINE-UD-ROGUE-THRESHOLD-001 + FINDING-ENGINE-UD-RANGER-FALSE-001.
- **WO2 — ENGINE-FAST-MOVEMENT-LOAD-FIX-001** — ACCEPTED 8/8 (FMLF). Removed "medium" from blocked load tuple in `movement_resolver.py:247`. Medium load no longer blocks +10. Closes FINDING-ENGINE-FAST-MOVEMENT-MEDIUM-LOAD-001.
- **WO3 — ENGINE-MD-SAVE-RULES-001** — ACCEPTED 8/8 (MDSR 4 + FSKL 4). nat1/nat20 auto-fail/pass added to massive damage inline Fort save (`attack_resolver.py:1000`). save_resolver already has nat1/nat20 globally — massive damage bypasses it via inline save. Fascinated -4 skill penalty wired to `_process_skill()` in `session_orchestrator.py:881`. Closes FINDING-ENGINE-MD-NAT1-NAT20-001 + FINDING-ENGINE-FASCINATED-SKILL-PENALTY-001.
- **WO4 — ENGINE-ATTACK-MODIFIER-FIDELITY-001** — ACCEPTED 8/8 (FECM 4 + SNSH 4). FE bonus moved from post-crit to `base_damage_with_modifiers` (pre-crit, PHB p.140). Secondary natural attacks use `grip="off-hand"` for ½ STR via existing `int(str_mod * 0.5)` at line 866. No floats introduced. Closes FINDING-ENGINE-FE-CRIT-MULTIPLIER-001 + FINDING-ENGINE-SECONDARY-STR-HALF-001.
New finding: FINDING-ENGINE-MD-INLINE-SAVE-PATTERN-001 (LOW) — massive damage uses inline save, not resolve_save().

**INFRA-SQLITE-CONSOLIDATION — ACCEPTED (2026-02-28 — session 16):**
`WO-INFRA-SQLITE-CONSOLIDATION-001` — 8/8 gates pass (commit 0ac1fda). 3 files: `scripts/compile_to_sqlite.py` (NEW, 395 lines), gate tests, `.gitignore` update. 7 main tables + 6 junction tables, 1216 total rows. Cross-reference query demonstrated (18 wizard evocation spells L0–L3). Zero resolver/schema/play_loop touch. DB is compiled artifact (`.gitignore`d), consumed by humans not runtime. PM Acceptance Notes 7/7 satisfied. Closes FINDING-INFRA-DATA-CONSOLIDATION-001. 2 new LOW findings filed: feats count mismatch (109 vs ~221 spec estimate), spell class ID abbreviation mapping absent.

**SR WO — ACCEPTED (2026-02-28 — session 18):**
`WO-ENGINE-SR-SPELL-PATH-001` — 8/8 gates pass (commits 8cc96f8/e1c2957). SR gate wired at `spell_resolver.py:670-694` — per-target, BEFORE save, calls existing `check_spell_resistance()` from save_resolver.py. `spell_resistance: bool = True` on SpellDefinition. Spell Penetration flows through existing feat check. PM Acceptance Notes 6/6 satisfied. Closes FINDING-ENGINE-SR-NOT-IN-SPELL-PATH-001. 1 new finding filed: FINDING-ENGINE-SR-PLAY-LOOP-EVENTS-001 (LOW).

**BATCH Y — ACCEPTED (2026-02-28 — session 19):**
4/4 WOs accepted. 32/32 gate tests pass (40/40 including 8 pre-existing IDC gates). Commit b8f7f50.
- **WO1 — ENGINE-RAGE-HP-TRANSITION-001** — ACCEPTED. +2 HP/HD enter, -2 HP/HD exit in `rage_resolver.py`. Multiclass HD via CLASS_LEVELS sum. `entity_unconscious` event on lethal exit. Not temporary HP per PHB p.25. Closes FINDING-ENGINE-RAGE-HP-ABSENT-001.
- **WO2 — ENGINE-FATIGUE-MOBILITY-001** — ACCEPTED. Early-return fatigue/exhaustion check at charge (`play_loop.py:~3399`) and run (`~3694`) entry points. Emits `charge_blocked_fatigued` / `run_blocked_fatigued` events. Closes FINDING-ENGINE-RAGE-FATIGUE-MOBILITY-001.
- **WO3 — ENGINE-WS-FORMULA-FIX-001** — ACCEPTED. Unlock L5 (was L4). PHB Table 3-14 lookup `{5:1, 6:2, 7:3, 10:4, 14:5, 18:6}`. Chargen delegates to resolver. Closes FINDING-ENGINE-WS-USES-FORMULA-001 + FINDING-ENGINE-WS-UNLOCK-LEVEL-001.
- **WO4 — ENGINE-DISARM-FIDELITY-001** — ACCEPTED. Counter-disarm on any failure (was margin >= 10). Stale IDC-002 test updated. Size modifier verified correct. Closes FINDING-ENGINE-DISARM-SIZE-MODIFIER-001 + FINDING-ENGINE-COUNTER-DISARM-THRESHOLD-001.
4 new findings: FINDING-ENGINE-RAGE-GREATER-MIGHTY-001 (LOW), FINDING-ENGINE-TIRELESS-RAGE-001 (LOW), FINDING-ENGINE-DISARM-2H-ADVANTAGE-001 (LOW), FINDING-ENGINE-EXHAUSTED-CONDITION-GAP-001 (MEDIUM).

**AUDIT-WO-008-SPELLCASTING — ACCEPTED (2026-02-28 — session 19):**
Anvil sweep audit: spellcasting resolution pipeline (~2,074 lines across 4 files). 10/10 questions answered. 7 new findings + 4 confirmations.
- **FINDING-AUDIT-SPELL-002 (HIGH)** — save_resolver.get_save_bonus() likely double-counts ability modifier. Chargen writes class_base+ability_mod into EF.SAVE_*, save_resolver adds ability_mod again. Affects ALL non-spell saves. Needs urgent investigation WO.
- **FINDING-AUDIT-SPELL-001 (MEDIUM)** — Spell saves bypass save_resolver: missing save feats (Great Fort/Iron Will/Lightning Ref), Divine Grace, Inspire Courage, halfling +1, dwarf +2 vs spells. TargetStats.get_save_bonus() returns raw EF.SAVE_* only. Needs builder WO.
- 5 LOW findings: SR events not reaching EventLog (confirms existing), Enlarge/Widen Spell missing, conjuration SR=False data gap, Empower+Maximize compat deviation, bare string spell_dc_base.
Good news: SR gate correctly placed, AoE per-target independence works, Heighten DC correct, save DC matches PHB p.176, Evasion/Improved Evasion correct.

**AUDIT-WO-009-SAVES — ACCEPTED (2026-02-28 — session 20):**
Anvil sweep audit: saves subsystem (7 files, ~2,400 lines). 8 new findings + 3 existing confirmed.
- **FINDING-AUDIT-SAVE-002 (MEDIUM)** — Multiclass saves use `max()` not `sum()` per PHB p.22 (builder.py:455-457, 1574-1576). Highest priority. WO queued.
- **FINDING-AUDIT-SAVE-001 (MEDIUM)** — Coup de grace reads raw `EF.SAVE_FORT`, bypasses `get_save_bonus()` entirely (attack_resolver.py:1793). WO queued.
- **FINDING-AUDIT-SAVE-003 (MEDIUM)** — `resolve_save()` bare call without `save_descriptor`/`school` (save_resolver.py:315). DEFERRED — needs SaveContext schema extension.
- **FINDING-AUDIT-SAVE-007 (LOW→promoted)** — Multiclass BAB `max()` not `sum()` (builder.py:443-446, 1562-1564). Same pattern as SAVE-002. WO queued.
- 4 LOW findings: RNG stream isolation, SaveContext schema gap, negative level split authority, bardic save scope.
- 3 existing confirmed: MD-INLINE-SAVE-PATTERN-001, NEGATIVE-LEVEL-SAVE-001, GNOME-ILLUSION-SAVE-001.
Good news: Type 2 field contract solid, spell save path correct, condition modifier aggregation clean, nat1/nat20 consistent, single-class save computation correct.

**NEXT — Scope Batch AD: SaveContext schema extension (WO1) + Class Feature Expansion III. SaveContext descriptor cluster (5 findings) warrants standalone WO to unblock Still Mind/Indomitable Will non-spell paths, AoC full path, Gnome illusion save, and bardic save scope fix.**

**Thunder rulings (session 19 cont.):**
Thunder rejects binary Option A/B. Rules: **typed contract policy** with 3 field types:
- **Type 1 (Component):** single component, resolver assembles total (e.g., `EF.SKILL_RANKS`)
- **Type 2 (Base+Permanent):** composite of permanent bonuses, resolver adds situational deltas (e.g., `EF.AC`)
- **Type 3 (Runtime-Only):** no persisted field, computed fresh (e.g., Initiative)

Canonical path authority rule: shadow paths must delegate, cache, or be labeled test-only. Anti-pattern rule: no DTO `get_*_bonus()` may independently implement rules math. Concentration finding elevated: high gameplay impact, prioritize early. Parity test template required in all stat-math WOs.

**Fix chain — COMPLETE:**
1. ~~SPEC-COMPUTED-FIELD-CONTRACT-001~~ → ACTIVE
2. ~~Fix batch Z-WO1: Concentration bonus wired~~ → ACCEPTED (37a51ed)
3. ~~Fix batch Z-WO2: Save double-count stripped~~ → ACCEPTED (37a51ed)
4. ~~Fix batch Z-WO3: Maneuver BAB → EF.BAB~~ → ACCEPTED (37a51ed)
5. ~~Fix batch Z-WO4: Spell save unified~~ → ACCEPTED (37a51ed)
6. ~~Parity tests in each WO~~ → Included in 32/32 gate tests

**Governance patches landing:** Field Contract Check + parity test template added to CLAUDE.md.

**Wild Shape closed.** WO-ENGINE-WILDSHAPE-HP-001 + WO-ENGINE-WILDSHAPE-DURATION-001 both ACCEPTED. Dispatches archived to `pm_inbox/reviewed/`. ENGINE DISPATCH #10 complete.

**Historical batches (A through X + SR + ENGINE DISPATCH #5–#12):** All ACCEPTED. Graduated to `pm_inbox/reviewed/BRIEFING_ARCHIVE_GRADUATION_20260228.md`.

## Current Focus

**Engine focus:** Batches A–AF + Save Fix + SR WO ALL ACCEPTED. **0 HIGH, 0 MEDIUM in flight. 1,168 gate tests. 58 findings graduated.** Pipeline: coverage expansion (~34 NOT STARTED remaining after AF). **Next sweep audit due in 3 batches (AG + 2 more).**
**Completed tracks:** UI SLICES 0-7, CHARGEN PHASE 3, BURST-001, PRS-01 RC READY.
**Active UI dispatches:** OPTICS (DISPATCH) → FRAMING (BLOCKED) → QA-002 (DISPATCH) → VISREG (DISPATCH, BLOCKED on Thunder) → GATES-V1 (BLOCKED on golden frames).
**Deferred:** Chatterbox swap timing, GAP-B (VS Build Tools), FINDING-WORLDGEN-IP-001.

## Open Findings

**Canonical source: `pm_inbox/BACKLOG_OPEN.md`** — all open findings with triage status and deferred rationale. Do not duplicate here. Backlog has 186 lines covering HIGH/MEDIUM/LOW/DEFERRED findings with full status tracking.

## Inbox

- **[ACCEPTED] [DEBRIEF_AUDIT-WO-002-MANEUVERS.md](pm_inbox/reviewed/DEBRIEF_AUDIT-WO-002-MANEUVERS.md)** — AUDIT-WO-002: Maneuvers + natural attacks. 18 rows, 8 FULL / 10 DEGRADED. 8 findings triaged. ACCEPTED session 10 (lifecycle tag confirmed). Stale inbox entry cleared session 21. Archived.
- **[ACCEPTED] [WO_SET_ENGINE_BATCH_AF.md](pm_inbox/reviewed/WO_SET_ENGINE_BATCH_AF.md)** — Class Feature Expansion IV: LOH SAI close (8/8), Monk Unarmed Wire (8/8), Paladin Remove Disease (9/9), Rogue Defensive Roll (8/8). 33/33 gates pass. Commit `2edf076`. ACCEPTED session 22. Archived. 1 new LOW finding filed (conditions legacy format).
- **[ACCEPTED] [DEBRIEF_AUDIT-WO-010-CONDITIONS.md](pm_inbox/reviewed/DEBRIEF_AUDIT-WO-010-CONDITIONS.md)** — AUDIT-WO-010: Conditions subsystem sweep. 5 gaps (3 MEDIUM, 1 LOW unblocked). 6 confirmed working. All MEDIUMs promoted to Batch AE. Archived.
- **[ACCEPTED] [DEBRIEF_AUDIT-WO-009-SAVES.md](pm_inbox/reviewed/DEBRIEF_AUDIT-WO-009-SAVES.md)** — AUDIT-WO-009: Saves subsystem sweep. 8 new findings (3 MEDIUM, 5 LOW). 3 existing confirmed. ACCEPTED — findings triaged and filed. Archived.
- **[DISPATCH] [WO-UI-VISREG-PLAYWRIGHT-001_DISPATCH.md](pm_inbox/WO-UI-VISREG-PLAYWRIGHT-001_DISPATCH.md)** — Visual regression harness. Upgrades manual screenshot capture to `toHaveScreenshot()` baseline comparison. New `client/tests/playwright/visual-regression.spec.ts`: 4 posture snapshots (STANDARD/DOWN/LEAN_FORWARD/DICE_TRAY) + 2 vault state snapshots (REST/COMBAT), all at 1920×1080, `maxDiffPixels:200`. Two `package.json` scripts: `test:visreg` (CI-safe, no `--update-snapshots`) and `test:visreg:update` (operator-only baseline update). Snapshots committed to `client/tests/playwright/snapshots/`. Gate UI-VISREG-PLAYWRIGHT 10/10 (VR-01 through VR-10 — structural checks, no browser required). **Baseline commit BLOCKED on Thunder golden frame approval.** Sequencing: OPTICS ACCEPTED → QA-002 12/12 → Thunder approves → `npm run test:visreg:update` → baselines committed → `npm run test:visreg` PASS → unblocks GATES-V1.
- **[DISPATCH] [WO-UI-CAMERA-OPTICS-001_DISPATCH.md](pm_inbox/WO-UI-CAMERA-OPTICS-001_DISPATCH.md)** — Per-posture optics. Extends `camera_poses.json` with `fov_deg`/`near`/`far` per posture. Extends `PostureConfig` interface. Wires `camera.ts` to apply optics on posture switch + lerp during transition + `updateProjectionMatrix()`. Debug overlay: `addCameraDebugHUD()` shows posture/pos/lookAt/fov/near/far/transit%. Adds `window.__cameraController__` in DEV mode. Optics: STANDARD 55°, DOWN 45°, LEAN_FORWARD 65° (fixes orb clip), DICE_TRAY 60°, BOOK_READ 40°. Gate UI-CAMERA-OPTICS 10/10. Must ACCEPT before WO-UI-VISUAL-QA-002.
- **[BLOCKED] [WO-UI-CAMERA-FRAMING-DICE-TRAY-FINAL_DISPATCH.md](pm_inbox/WO-UI-CAMERA-FRAMING-DICE-TRAY-FINAL_DISPATCH.md)** — DICE_TRAY posture orb exclusion fix. Blocked on WO-UI-CAMERA-OPTICS-001. JSON-only change to `camera_poses.json` DICE_TRAY entry (position/lookAt/fov_deg). Hard gate: orb 0% visible at 1920×1080 with 5% safe margin. Tower mouth in frame. Tray ≥ 40% width. Camera looking downward. Evidence: `dice_tray.png` + `dice_tray_debug.png` + runtime optics JSON + optional MP4. Gate UI-CAMERA-FRAMING-DICE-TRAY 5/5.
- **[DISPATCH] [WO-UI-VISUAL-QA-002_DISPATCH.md](pm_inbox/WO-UI-VISUAL-QA-002_DISPATCH.md)** — Composition lock + golden frame commit. Blocked on CAMERA-OPTICS-001. **Amended (x2):** (1) DICE_TRAY orb exclusion hard gate (0% visible, 5% safe margin). (2) Interaction clips. (3) Room geometry evidence pack. (4) Commit hash + branch in README. Thunder reviews all 4 postures. After approval: commit 4 golden frames. Unblocks GATES-V1. Gate UI-VISUAL-QA-002 **12/12**.
- **[DISPATCH] [WO-UI-GATES-V1_DISPATCH.md](pm_inbox/WO-UI-GATES-V1_DISPATCH.md)** — Depends on CAMERAS-V1 (needs golden frames). Three test suites: screenshot diff (pixelmatch 3% tolerance, 4 postures + 4 region assertions = 8 checks), zone parity (10 checks via ?dump=1), UI ban scan (9 static grep checks). Total gate UI-GATES 27/27. CI fails on any drift. Terminates the coordinate-thrash loop permanently.
- **[READY] [WO-ENGINE-WILDSHAPE-HP-001_DISPATCH.md](pm_inbox/WO-ENGINE-WILDSHAPE-HP-001_DISPATCH.md)** — PHB delta HP formula for Wild Shape. 10 gate tests. Fixes FINDING-WILDSHAPE-HP-001 LOW.
- **[READY] [WO-ENGINE-WILDSHAPE-DURATION-001_DISPATCH.md](pm_inbox/WO-ENGINE-WILDSHAPE-DURATION-001_DISPATCH.md)** — Wild Shape auto-revert on duration expiry. 10 gate tests. Fixes FINDING-WILDSHAPE-DURATION-001 LOW.
- **[READ] [MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md](pm_inbox/MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md)** — TTS pipeline reference
- **[READ] [MEMO_BUILDER_PREFLIGHT_CANARY.md](pm_inbox/MEMO_BUILDER_PREFLIGHT_CANARY.md)** — Preflight canary system
- **[READ] [TUNING_001_PROTOCOL.md](pm_inbox/TUNING_001_PROTOCOL.md)** — TUNING-001 observation protocol
- **[READ] [TUNING_001_LEDGER.md](pm_inbox/TUNING_001_LEDGER.md)** — TUNING-001 session ledger

## WO Verdicts (most recent 15 — older entries archived)

| WO | Verdict | Commit |
|---|---|---|
| BATCH AE (4 WOs) | **ACCEPTED** — 32/32 gates (SRSP 4 + PCD 4 + RFS 8 + ALT 4 + BSS 4 + TSB 8). Commits ab44488/fb0f8f4. WO1: spell_resolver._resolve_save() shadow path eliminated (play_loop.py:274, save_descriptor="spell") — all spell saves now route through save_resolver; poison CON double-count stripped at 4 sites (Type 2 contract). WO2: EF.FATIGUED=True → -2 Ref penalty in save_resolver (PHB p.308, Ref only). WO3: AoC threshold L2→L3 (builder.py both paths + save_resolver ally check, PHB p.49); Inspire Courage save bonus scoped to fear/charm only (PHB p.29, attack/damage unchanged). WO4: EF.TRAP_SENSE_BONUS chargen write (barb//3 + rogue//3, HOUSE_POLICY sum) + save_resolver consume (REF + save_descriptor="trap"). 3 corrected tests. 1 new LOW: TRAP-SENSE-AC-001 (AC portion CONSUME_DEFERRED). 58 total graduated. | ab44488+fb0f8f4 |
| AUDIT-WO-010-CONDITIONS | **ACCEPTED** — Conditions subsystem sweep. 5 gaps / 6 confirmed working. 3 MEDIUM findings: CONDITIONS-002 (poison_disease_resolver.py CON double-count — Type 2 field contract violation, bundled into Batch AE WO1), CONDITIONS-001 (rage fatigue dual-track — Fort/Ref save penalties silent post-rage, Batch AE WO2), CONDITIONS-003 (Aura of Courage fear immunity at L2 instead of L3, PHB p.49, Batch AE WO3). BARDIC-SAVE-SCOPE-001 unblocked — fear/charm descriptor filter now feasible, 2-line fix, Batch AE WO3. FINDING-ENGINE-KI-STRIKE-WILDSHAPE-001 confirmed LOW (remains OPEN, PHB ambiguity). EXHAUSTED-CONDITION-GAP-001 closed (ML-003: formal definition existed, CONDITIONS-001 captures precise gap). 6 confirmed working: AoC fear descriptor e2e, Still Mind school descriptor, Indomitable Will, paladin/monk immunity pattern, condition duration tracking, condition application completeness. | N/A (audit) |
| BATCH AD (4 WOs) | **ACCEPTED** — 33/33 gates (SCX 8 + RNL 8 + ECI 8 + IGT 9). Commits 0275dea/3cb30ac. WO1: SaveContext extended (save_descriptor + school fields) — 5-finding descriptor cluster CLOSED. Still Mind/Indomitable Will non-spell paths wired, AoC fear-descriptor path live, gnome illusion save wired. WO2: Resist Nature's Lure (enchantment/poison saves) + Nature Sense. WO3: Evil Cleric Inflict Swap with alignment guard — closes FINDING-ENGINE-SPONTANEOUS-ALIGNMENT-001. WO4: Inspire Greatness (attack/save bonus + ally range) — +2 HD HP pool CONSUME_DEFERRED. 3 new CONSUME_DEFERRED findings: SPELL-RESOLVER-SAVE-BYPASS-001 (MEDIUM), INSPIRE-GREATNESS-HD-001 (LOW), MD-INLINE-SAVE-PATTERN-001 confirmed (LOW). 53 total findings graduated. | 0275dea+3cb30ac |
| BATCH AC (4 WOs) | **ACCEPTED** — 32/32 gates (FOB 8 + DS 8 + WOB 8 + AOC 8). Commits c99628d/563af6e. Flurry of Blows (penalty table, monk-weapon gate, play_loop wired). Diamond Soul (SR=level+10 at L13+, level_up delta, Spell Penetration integrated, max() preserves racial SR). Wholeness of Body (2×level pool, 5 guard states, 1/day). Aura of Courage (fear immunity sentinel + ally +4 morale Chebyshev scan, morale non-stacking). AoC CONSUME_DEFERRED — SaveContext no descriptor field (pre-existing gap, 5th finding in cluster). 2 new LOWs: SAVE-DESCRIPTOR-PASS-001, FLURRY-WEAPON-ID-FIELD-001. 4 coverage rows → IMPLEMENTED. | c99628d+563af6e |
| SAVE FIX (2 WOs) | **ACCEPTED** — 16/16 gates (MSF 8 + CDG 8). Commits f58411c/e452fef. Multiclass save+BAB max()→sum() at 4 builder.py sites (PHB p.22). CdG Fort save routed through get_save_bonus() — shadow path eliminated. Nat1/nat20 added to CdG (was missing despite spec claim). 6 existing tests updated, not deleted. Existing CdG 10/10 pass. Closes SAVE-001/002/007 + CDG-NAT1-NAT20-MISSING-001 (found+fixed). | f58411c+e452fef |
| BATCH AB (4 WOs) | **ACCEPTED** — 32/32 gates (SMI 8 + CLI 8 + KIS 8 + MFM 8). Commits 3ec541b/0ebc5e3. Still Mind (+2 all saves vs enchantment, monk L3+). Indomitable Will (+4 Will vs enchantment in rage, barb L14+). Purity of Body/Diamond Body/Venom Immunity (disease+poison immunities). Ki Strike (magic/lawful/adamantine DR bypass). Monk fast movement (Table 3-13 + armor/load restriction). Pre-existing paladin poison immunity bug FIXED. 7 coverage rows → IMPLEMENTED. 2 new LOWs: school param non-spell, Ki Strike wild shape. | 3ec541b+0ebc5e3 |
| BATCH AA (4 WOs) | **ACCEPTED** — 32/32 gates (RAP 8 + MMC 8 + SDC 8 + MF2 8). Commit 0b7cbad. Rage progression level-gated (Greater L11, Mighty L20, Tireless L17). Metamagic registry 9/9 PHB (+Enlarge +Widen). 4 conjuration spells SR=False + EF.SPELL_DC_BASE constant. Overrun prone max(STR,DEX). Disarm 2H = ghost (B-AMB-04). 7 LOWs closed (1 ghost). 2 new LOWs: spell def duplicates, spell_dc_base no write site. | 0b7cbad |
| BATCH Z (4 WOs) | **ACCEPTED** — 32/32 gates (CW 8 + SDF 8 + MBF 8 + SSU 8). Commits 37a51ed/c214498. Concentration bonus wired at chargen (5 read sites). Save ability_mod double-count stripped (Type 2 contract enforced, 16 stale tests updated). Maneuver _get_bab() → EF.BAB only (11 call sites, 5 maneuver types). Spell saves unified through save_resolver (shadow path eliminated). Closes FINDING-AUDIT-SPELL-002 (HIGH) + FINDING-AUDIT-SPELL-001 + FINDING-ENGINE-CONCENTRATION-BONUS-UNWRITTEN-001 + FINDING-ENGINE-MANEUVER-BAB-SHADOW-001 (3 MEDIUM). 2 new LOWs: position tuple format, negative level save. | 37a51ed+c214498 |
| BATCH Y (4 WOs) | **ACCEPTED** — 32/32 gates (RHPT 8 + FMOB 8 + WSFF 8 + DSFX 8). Commit b8f7f50. Rage HP transition (PHB p.25), fatigue mobility block (PHB p.308), wild shape Table 3-14 lookup + L5 unlock, counter-disarm any-failure (PHB p.155). 6 findings CLOSED. 4 new findings (1 MEDIUM: exhausted condition gap, 3 LOW: Greater/Mighty Rage, Tireless Rage, 2H disarm bonus). | b8f7f50 |
| WO-ENGINE-SR-SPELL-PATH-001 | **ACCEPTED** — 8/8 Gate ENGINE-SR-SPELL-PATH (SRSP-001–SRSP-008). Standalone WO, commits 8cc96f8/e1c2957. SR gate at spell_resolver.py:670-694, per-target before save. Calls existing check_spell_resistance(). Spell Penetration flows through existing feat check. Finding: SR-PLAY-LOOP-EVENTS-001 (LOW). | 8cc96f8+e1c2957 |
| WO-ENGINE-POWER-ATTACK-001 | **ACCEPTED** — 8/8 Gate ENGINE-POWER-ATTACK (PA-001–PA-008). Batch P, commit cd429fb. 2H=int(penalty×1.5), off-hand=penalty//2, one-handed=penalty; feat+BAB validation block; `grip` in feat_context. Findings: PA-2H-PHB-DEVIATION-001 + PA-FULL-ATTACK-ROUND-LOCK-001 (both LOW). | cd429fb |
| WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001 | **ACCEPTED** — 8/8 Gate ENGINE-IMPROVED-MANEUVER-BONUSES (IMB-001–IMB-008). Batch P, commit 336f04d. +4 at single opposed-check site for all 5 maneuvers in maneuver_resolver.py. Batch L "+4 wired" claim FALSE — Batch L = AoO suppression only. 5 findings CLOSED. | 336f04d |
| WO-ENGINE-PRECISE-SHOT-001 | **ACCEPTED** — 8/8 Gate ENGINE-PRECISE-SHOT (PS-001–PS-008). Batch P, commit e39c921. New `_is_target_in_melee()` in attack_resolver.py (same-team ally adjacent 8-dir). -4 penalty or `precise_shot_active` bypass. Dead code finding: PRECISE-SHOT-FEAT-RESOLVER-DEAD-CODE-001 (LOW). | e39c921 |
| WO-ENGINE-IMPROVED-DISARM-COUNTER-001 | **ACCEPTED** — 8/8 Gate ENGINE-IMPROVED-DISARM-COUNTER (IDC-001–IDC-008). Batch P, commits 5d088d6+0440ffa. Fixed inverted branches + raw-roll margin → totals. Improved Disarm suppresses counter. B-AMB-04 canary restored. Finding: IDC-DEX-STRIPPED-001 (LOW OPEN). | 5d088d6+0440ffa |
| WO-ENGINE-IMPROVED-OVERRUN-001 | **ACCEPTED** — 8/8 Gate ENGINE-IMPROVED-OVERRUN (IO-001–IO-008). Batch O, commit 3232b76. AoO suppression in play_loop.py + defender-avoid suppression in maneuver_resolver.py (check BEFORE `if intent.defender_avoids:`). New finding: FINDING-ENGINE-IMPROVED-OVERRUN-BONUS-001 (LOW). | 3232b76 |
| WO-ENGINE-COMBAT-EXPERTISE-001 (O) | **ACCEPTED** — 8/8 Gate ENGINE-COMBAT-EXPERTISE (CEX-001–CEX-008). Batch O, SAI — already wired. Untracked test file committed. Zero production changes. | 9d5b6f5 |
| WO-ENGINE-BLIND-FIGHT-001 | **ACCEPTED** — 8/8 Gate ENGINE-BLIND-FIGHT (BF-001–BF-008). Batch O, commit 6057476. Miss-chance reroll event (`blind_fight_reroll`) emitted on every reroll. `EF.MISS_CHANCE` on target entity (not WorldState). New finding: FINDING-ENGINE-BLIND-FIGHT-INVIS-001 (LOW). | 6057476 |
| WO-ENGINE-TOUGHNESS-001 | **ACCEPTED** — 8/8 Gate ENGINE-TOUGHNESS (TG-001–TG-008). Batch O, commit 99d79af. `list.count("toughness")` for stackable feat. Wired at chargen + level_up(). | 99d79af |
| WO-ENGINE-MASSIVE-DAMAGE-001 | **ACCEPTED** — 10/10 Gate ENGINE-MASSIVE-DAMAGE (MD-001–MD-010). Batch N, SAI — already wired at attack_resolver.py:761 (DR-aware threshold). Test file pre-written. Bonus finding: FINDING-ENGINE-MASSIVE-DAMAGE-FULL-ATTACK-001 (LOW — batched per-hit gap in full-attack path). | 7638473 |
| WO-ENGINE-STABILIZE-ALLY-001 | **ACCEPTED** — 10/10 Gate ENGINE-STABILIZE-ALLY (SA-001–SA-010). Batch N, SAI — stabilize_resolver.py wired into play_loop.py:2628 + action_economy.py. Test file pre-written. | 7638473 |
| WO-ENGINE-IMPROVED-TRIP-001 | **ACCEPTED** — 10/10 Gate ENGINE-IMPROVED-TRIP (IT-001–IT-010). Batch N, new work. AoO suppression wired in play_loop.py elif chain. Free attack via resolve_attack() when TripIntent.weapon present. Optional weapon field added to TripIntent. New findings: IMPROVED-TRIP-BONUS-001 + IMPROVED-SUNDER-BONUS-001 + IMPROVED-TRIP-WEAPON-CONTEXT-001 (all LOW). | 7638473 |
| WO-ENGINE-COVER-FIX-001 | **ACCEPTED** — 8/8 Gate ENGINE-COVER-FIX (CF-001–CF-008). Batch M, commit 548e2cf. IMPROVED cover fixed: +8→+4 AC, +4→+3 Ref per PHB p.150. terrain_resolver.py only. Findings: FINDING-SCHEMA-COVER-DOCSTRING-001 + FINDING-SCHEMA-TERRAIN-TAG-ORPHAN-001 (both LOW). | 548e2cf |
| WO-ENGINE-ENCUMBRANCE-WIRE-001 | **ACCEPTED** — 10/10 Gate ENGINE-ENCUMBRANCE-WIRE (EW-001–EW-010). Batch M, commit ad21df2. EF.ENCUMBRANCE_LOAD pre-computed at chargen. Two-line wire-up in movement + attack resolvers. | ad21df2 |
| WO-ENGINE-SNEAK-ATTACK-AUTO-IMMUNE-001 | **ACCEPTED** — 8/8 Gate ENGINE-SNEAK-ATTACK-IMMUNITY (SI-001–SI-008). Batch M, commit 14b2c18. `_apply_creature_type_immunities(entity)` in builder.py. Finding: FINDING-ENGINE-MULTICLASS-BUILDER-IMMUNE-001 (LOW). | 14b2c18 |
| WO-ENGINE-WEAPON-PROFICIENCY-001 | **ACCEPTED** — 11/11 Gate ENGINE-WEAPON-PROFICIENCY (WP2-001–WP2-011). Batch M, commit 8e07dd5. `proficiency_category: Optional[str]` on Weapon. `_is_weapon_proficient()` helper. Finding: FINDING-ENGINE-BARD-ROGUE-MARTIAL-PARTIAL-001 (LOW). | 8e07dd5 |
| WO-ENGINE-IMPROVED-DISARM-001 | **ACCEPTED** — 8/8 Gate ENGINE-IMPROVED-DISARM (ID-001–ID-008). Batch L, commit ba3e62f. No AoO on disarm attempt, +4 bonus to disarm check. New findings: FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 + FINDING-ENGINE-IMPROVED-DISARM-BONUS-001 (both LOW). | ba3e62f |
| WO-ENGINE-IMPROVED-GRAPPLE-001 | **ACCEPTED** — 8/8 Gate ENGINE-IMPROVED-GRAPPLE (IG-001–IG-008). Batch L, commit ba3e62f. No AoO on grapple attempt, +4 bonus to grapple checks. New finding: FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001 (LOW). | ba3e62f |
| WO-ENGINE-IMPROVED-BULL-RUSH-001 | **ACCEPTED** — 8/8 Gate ENGINE-IMPROVED-BULL-RUSH (IB-001–IB-008). Batch L, commit ba3e62f. No AoO on bull rush attempt, +4 STR check bonus. New finding: FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001 (LOW). | ba3e62f |
| WO-ENGINE-SPELL-PENETRATION-001 | **ACCEPTED** — 8/8 Gate ENGINE-SPELL-PENETRATION (SP-001–SP-008). Batch L, commit ba3e62f. SP: +2 CL bonus to SR checks. Greater SP stacks (+4 total). New finding: FINDING-ENGINE-IMPROVED-OVERRUN-AOO-001 (LOW, **CLOSED** Batch O). | ba3e62f |
**Full verdict history:** `reviewed/BRIEFING_ARCHIVE_GRADUATION_20260222.md` (18 older entries archived)

## Dispatches (active only — graduated entries archived)

- **[ACCEPTED] WO_SET_ENGINE_BATCH_AD** — SaveContext Extension + Class Feature Expansion III: 4 WOs. 33/33 gates. Commits 0275dea/3cb30ac. 4 coverage rows IMPLEMENTED. Archived to pm_inbox/reviewed/.
- **[ACCEPTED] WO_SET_ENGINE_BATCH_AC** — Class Feature Expansion II: 4 WOs. 32/32 gates. Commits c99628d/563af6e. 4 coverage rows IMPLEMENTED.
- **[ACCEPTED] WO_SET_ENGINE_BATCH_AB** — Class Feature Expansion I: 4 WOs (save bonuses, immunities, DR bypass, movement). 32/32 gates. Commits 3ec541b/0ebc5e3. 7 coverage rows IMPLEMENTED.
- **[ACCEPTED] WO_SET_ENGINE_SAVE_FIX** — Multiclass formula fix + CdG shadow path: 2 WOs. 16/16 gates. Commits f58411c/e452fef. Closes FINDING-AUDIT-SAVE-001/002/007 + CDG-NAT1-NAT20-MISSING-001.
- **[DISPATCHED] WO-UI-CAMERA-OPTICS-001** — Per-posture optics. Gate UI-CAMERA-OPTICS 10 tests. Blocks QA-002.
- **[DISPATCHED] WO-UI-VISUAL-QA-002** — Blocked on CAMERA-OPTICS-001. Composition lock + golden frames. Gate UI-VISUAL-QA-002 12 tests.
- **[DISPATCHED] WO-UI-VISREG-PLAYWRIGHT-001** — Visual regression harness. Gate UI-VISREG-PLAYWRIGHT 10 tests. Baseline BLOCKED on Thunder golden frame approval.

**Full dispatch history:** `reviewed/BRIEFING_ARCHIVE_GRADUATION_20260222.md` (older entries + all ACCEPTED dispatches graduated)

## Build Order

~~Smoke fuzzer~~ → ~~Oracle (3 phases)~~ → ~~Director (3 phases)~~ → ~~UI (4 phases + drift guards + zone authority)~~ → ~~Comedy Stingers P1~~ → ~~Spark LLM Selection~~ → ~~BURST-001 Tier 1 Spec Freeze~~ (157 tests) → ~~Waypoint (3 WOs)~~ → ~~Tier 2 Instrumentation~~ (84 tests) → ~~Spark Explore~~ → ~~RV-007~~ (22 tests) → ~~Tier 3 (Parser/Grammar)~~ (34 tests) → ~~Tier 4 (UX Prompts)~~ (90 tests) → ~~**Tier 5.5 Playtest v1 — ACCEPTED. BURST-001 COMPLETE.**~~ | **PRS-01** (~~5/5 ACCEPTED~~, ~~SCAN FIX~~, ~~pre-RC cleanup~~, ~~ALL GATES GREEN~~, ~~ORCHESTRATOR ACCEPTED~~ → IP REMEDIATION → RC READY) | ~~**CHARGEN PHASE 1 COMPLETE**~~ (7 WOs, 114 tests, `build_character()` functional)

## Doctrine (11 files in `pm_inbox/doctrine/`)

8 SPEC + 2 GOV + 1 PROC. GT v12 = product doctrine. Remaining formalization: CampaignManifest spec (PENDING), Worldgen pipeline spec (PENDING), Companion Mode spec (PENDING). Source: `reviewed/MEMO_DOCTRINE_HOLES_ANSWER_PACKET.md`.

## Suspended WO Verdicts

| WO | Status | Reason |
|---|---|---|
| WO-SPEAK-SERVER | SUSPENDED | BURST-001 Voice-First track |
| WO-FROZEN-VIEW-GUARD | SUSPENDED | Post-integration hardening |
| Resolver dedup | SUSPENDED | Known (Field Manual #5), not correctness |

## Reference Pointers (Tier 2 — access by search, not by pasting)

| Topic | Pointer |
|-------|---------|
| Architecture session (2026-02-21) | `reviewed/MEMO_ARCHITECTURE_SESSION_20260221.md` — Box/Vault/Oracle/Spark, 8 parked WO candidates |
| Cross-model experiment (2026-02-20) | `reviewed/` — Four-Layer Damage Model, DR-014, probe results |
| WO-NARRATIVE-001 | `reviewed/SEVEN_WISDOMS_ZERO_REGRETS.md` + Drive `1DOySd1zb5IEZZRtTvLWY6FdON7H_tfuP3lRMTRUR9rY` |
| Google Drive integration | `reviewed/GOOGLE_DRIVE_INTEGRATION_REFERENCE.md` — creds, token refresh, MCP setup |
| Smoke test details | `reviewed/BRIEFING_ARCHIVE_GRADUATION_20260222.md` — full hooligan/fuzzer results |
| Graduated verdicts/dispatches | `reviewed/BRIEFING_ARCHIVE_GRADUATION_20260222.md` — 18 verdicts + 14 dispatches + H1 batch |

## Google Drive (operational)

| File | Drive ID |
|------|----------|
| AEGIS_REHYDRATION_PACKET | `1ZICQUDKVuO0oNqFiFl6gq5VizthLp8LxDLYgW41Gfac` |
| AEGIS_MEMORY_LEDGER | `10fGUlCnKQUFkuNqpUOKpT3PQb_TXXjlqKT7UB4VrUX0` |
| SLATE_NOTEBOOK | `1Py1N-dCnl2Azdol2MOREdoQkT_oqvpCXRJzqca9SR3Y` |
| ANVIL_NOTEBOOK | `1pdWxIvGEsLpPUBptNVuC9uPP9ytyiwMXZGwsdzvAip0` |
| ANVIL_REHYDRATION_KERNEL | `1RlDv-9dScCGomsMjm2IjJOmEz28Y-Id5bBDofVswwm4` |
| SEVEN_WISDOMS_ZERO_REGRETS | `1DOySd1zb5IEZZRtTvLWY6FdON7H_tfuP3lRMTRUR9rY` |

**Token refresh expires ~2026-02-27.** Local backup: `C:/Users/Thunder/.slate/`. Notebooks: append-only, write-only, per-seat. Roundtable: `D:\anvil_research\ROUNDTABLE.md`.

## Active Operational Files

**Root** (active WOs + operational files):
- [PM_BRIEFING_CURRENT.md](pm_inbox/PM_BRIEFING_CURRENT.md) — This file
- [REHYDRATION_KERNEL_LATEST.md](pm_inbox/REHYDRATION_KERNEL_LATEST.md) — PM rehydration block
- [BACKLOG_OPEN.md](pm_inbox/BACKLOG_OPEN.md) — Canonical open findings backlog (permanent)
- [README.md](pm_inbox/README.md) — Inbox hygiene rules
- [WO_SET_ENGINE_BATCH_AB.md](pm_inbox/WO_SET_ENGINE_BATCH_AB.md) — **IN FLIGHT** — Class Feature Expansion I: 4 WOs, 32 gates, 7 coverage rows
- [WO_SET_ENGINE_SAVE_FIX.md](pm_inbox/WO_SET_ENGINE_SAVE_FIX.md) — **IN FLIGHT** — Multiclass formula fix + CdG save path: 2 WOs, 16 gates. Parallel with AB.
- [WO_SET_OSS_DATA_BATCH_B.md](pm_inbox/WO_SET_OSS_DATA_BATCH_B.md) — **DATA BATCH B** — WO-DATA-MONSTERS-001 + WO-INFRA-DICE-001 (deferred)
- [WO-DATA-MONSTERS-001_DISPATCH.md](pm_inbox/WO-DATA-MONSTERS-001_DISPATCH.md) — Data WO (deferred)
- [WO-INFRA-DICE-001_DISPATCH.md](pm_inbox/WO-INFRA-DICE-001_DISPATCH.md) — Infra WO (deferred)

**Archived 2026-02-28 (session 20):** Batch AA dispatch+debrief, field contract memos, AUDIT-WO-009-SAVES debrief, Batch AD dispatch (WO_SET_ENGINE_BATCH_AD.md).

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
