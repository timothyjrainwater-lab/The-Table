# PM Briefing — Current

**Last updated:** 2026-02-27 (session 9) — **ENGINE BATCH M ACCEPTED** (commits 548e2cf/ad21df2/14b2c18/8e07dd5, 37/37 gates: CF/EW/SI/WP2). **ENGINE BATCH N ACCEPTED** (commit 7638473, 40/40 gates: MD/SA/SF/IT — 3 SAI + 1 new work; IT bonus tests 10 vs 8 planned). **ENGINE BATCH O ACCEPTED** (commits 3232b76/9d5b6f5/6057476/99d79af, 32/32 gates: IO/CE/BF/TG — CE SAI, 3 new). **ENGINE BATCH P ACCEPTED** (commits cd429fb/336f04d/e39c921/5d088d6+0440ffa, 32/32 gates: PA/IMB/PS/IDC — findings: PA-2H-PHB-DEVIATION-001/PA-FULL-ATTACK-ROUND-LOCK-001/PRECISE-SHOT-FEAT-RESOLVER-DEAD-CODE-001/IDC-DEX-STRIPPED-001 all LOW OPEN; 6 prior findings CLOSED; ML-005 filed). **ENGINE BATCH Q DISPATCH-READY** (32 gate tests: GC/IUD/WFC/WSP — prereq: Batch P ACCEPTED; Batch Q WO3/WFC must also wait for R WO4/GTWF). **ENGINE BATCH R ACCEPTED** (32/32 gates: IE/MB/SP/GTWF — WO1/WO2/WO3 SAI, WO4 new work; commits 38f12e0/0452427/4083663; FINDING-CE-STANDING-AOO-001 CLOSED; new LOW findings: GTWF-PREREQ-CHAIN-001 + MOBILITY-DODGE-CHAIN-001; Batch Q WO3/WFC unblocked). **ENGINE BATCH S ACCEPTED** (33/33 gates: BDR/RSV/ETN/MUP — commits 9416925/dabeaee/652590d/1516009; 1 bonus RSV gate; findings: GNOME-ILLUSION-SAVE-001/MONK-UNARMED-ATTACK-WIRE-001/LEVELUP-POOL-SYNC-001 all LOW OPEN; builder.py lock released). **ENGINE BATCH T ACCEPTED (3/4 WOs)** (commits c30e1fa/f75bb6e/ce0e0f3; 24/32 gate tests: MA 8/8 + INA 8/8 + ITN 8/8; WO4 SD BLOCKED — FINDING-ENGINE-DOMAIN-SYSTEM-MISSING-001 MEDIUM OPEN; CORRIGENDUM confirmed: `EF.TURN_UNDEAD_USES` not `EF.TURN_UNDEAD_USES_REMAINING`; natural_attack_resolver.py delegates to attack_resolver.resolve_attack() — FINDING-ENGINE-NAT-ATTACK-DELEGATION-PATH-001 LOW INFO for Batch Q WO3 WFC). **DATA BATCH B IN FLIGHT**. Suite: 8407 passed / 141 pre-existing failures, 0 gate regressions.

---

## Stoplight: GREEN

7,211 passed / 23 pre-existing failures, 0 new gate failures. Commit `c6a56c0`. **ENGINE DISPATCH #7: ENGINE-TWD 8/8 + ENGINE-METAMAGIC 30/30 ACCEPTED.** All prior gates unchanged. UI pivot locked — 3D client frozen, client2d/ track open.

| Gate | Tests | Gate | Tests | Gate | Tests |
|------|-------|------|-------|------|-------|
| A | 22/22 | G | 22/22 | N | 37/37 |
| B | 23/23 | H | 16/16 | O | 47/47 |
| C | 24/24 | I | 13/13 | P | 22/22 |
| D | 18/18 | J | 27/27 | Q | 16/16 |
| E | 14/14 | K | 72/72 | R | 18/18 |
| F | 10/10 | L | 32/32 | S | 31/31 |
|   |       | M | 31/31 | T | 23/23 |
|   |       |   |       | U | 20/20 |
|   |       |   |       | V | 22/22 |
|   |       |   |       | W | 14/14 |
|   |       |   |       | X | 9/10 |
|   |       |   |       | Y | 6/6 |
|   |       |   |       | Z | 7/7 |
|   |       |   |       | AA | 7/7 |
|   |       |   |       | AB | 6/6 |
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

*Note: All Anvil UI gap WOs ACCEPTED. 12/12. Layout pack WOs: LAYOUT-PACK + CAMERAS + OBJECT-LAYOUT + LIGHTING + PHYSICALITY-BASELINE ACCEPTED (38/38 gates). ENGINE-SPELL-SLOTS-001 12/12 + ENGINE-REST-001 12/12 ACCEPTED. ENGINE-GOLD-MASTER-REGEN 9/9 + ENGINE-READIED-ACTION 10/10 + ENGINE-AID-ANOTHER 10/10 + ENGINE-DEFEND 10/10 + ENGINE-FEINT 10/10 — ENGINE DISPATCH #5 ALL ACCEPTED. ENGINE DISPATCH #6 ALL ACCEPTED: ABILITY-DAMAGE 10/10 + WITHDRAW-DELAY 10/10 + CONDITIONS-BLIND-DEAF 19/19 + SUNDER-DISARM-FULL 10/10 + POISON-DISEASE 10/10 (59/59 gate tests). Builder fix: SD-09 spurious Weapon() field names removed. 182 engine gate tests all pass. GATES-V1 blocked on golden frames. ENGINE BATCH B R1 ALL ACCEPTED (34/34): EVASION 10/10 + DIVINE-GRACE 8/8 + WEAPON-FINESSE 8/8 + COMBAT-REFLEXES 8/8. ENGINE BATCH C PARTIAL ACCEPTED (14/14): CLEAVE-ADJACENCY 6/6 + COMBAT-EXPERTISE 8/8. Coverage: 50.2% → 48.3% MISSING (first time below 50%). FINDING-ENGINE-FLATFOOTED-AOO-001 filed.*

**Gate test total:** 846 (812 prior + 34 ENGINE BATCH B R1 = 846 gate tests). All gates PASS. Pre-existing failures: 23 unchanged.

## Operator Action Queue (max 3)

**ENGINE BATCH D — DEBRIEFS FILED, AWAITING REGRESSION RUNNER (2026-02-26 — ENGINE DISPATCH #13):**
All four debriefs in `pm_inbox/reviewed/`. Gates: Silent Spell 10/10, Still Spell 11/11, Monk WIS-to-AC 8/8, Barbarian Fast Movement 8/8+1 = 38 total. Regression runner outstanding — full suite numbers pending before coverage map update and ACCEPTED status.
- **WO-ENGINE-SILENT-SPELL-001** — FILED 10/10. `SpellDefinition.has_verbal: bool = True` added. `"silent"` entries in metamagic_resolver. `_VALID_METAMAGIC` auto-derived from cost dict — no separate set entry needed (architectural find). Silence-zone enforcement deferred per scope.
- **WO-ENGINE-STILL-SPELL-001** — FILED 11/11. `"still"` entries in metamagic_resolver. ASF bypass at play_loop.py:669 via `not _is_still` guard. `getattr(intent, "metamagic", ())` confirmed safe for tuple/list.
- **WO-ENGINE-MONK-WIS-AC-001** — FILED 8/8. WIS was baked into EF.AC at chargen — Branch B taken. WIS removed from base AC formula, tracked in `EF.MONK_WIS_AC_BONUS`, applied dynamically in attack_resolver. Four new EF constants: `MONK_WIS_AC_BONUS`, `ARMOR_AC_BONUS`, `ARMOR_TYPE`, `FAST_MOVEMENT_BONUS`. No separate touch AC path — WIS in main path is architecturally correct. FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN (consolidated).
- **WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001** — FILED 8/8+1. `EF.FAST_MOVEMENT_BONUS = 10` at chargen. movement_resolver applies +10 blocked by `armor_type == "heavy"` only (light/medium OK per PHB p.26). Dwarf 20+10=30 confirmed. FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 LOW OPEN (consolidated). `EF.ARMOR_TYPE` now live — **UNBLOCKS Evasion armor restriction WO** (previously deferred "waiting on armor field"; blocker gone as of Batch D).

**Wild Shape closed.** WO-ENGINE-WILDSHAPE-HP-001 + WO-ENGINE-WILDSHAPE-DURATION-001 both ACCEPTED. Dispatches archived to `pm_inbox/reviewed/`. ENGINE DISPATCH #10 complete.

**ENGINE BATCH B R1 — ALL ACCEPTED (2026-02-26 — ENGINE DISPATCH #12 — 34/34 gate tests):**
- **WO-ENGINE-EVASION-001** — ACCEPTED 10/10 (EV-001–EV-010). `_resolve_damage()` threaded with `world_state` + `target_entity_id` to enable condition check. Evasion: Reflex half → zero on success (rogue/ranger/monk). Improved Evasion: still takes half on failed save. Deferred: Improved Evasion with Reflex fail-half (separate WO candidate).
- **WO-ENGINE-DIVINE-GRACE-001** — ACCEPTED 8/8 (DG-001–DG-008). CHA mod inserted in `get_save_bonus()` in `save_resolver.py` for paladin_level ≥ 2. Stacks with Great Fortitude / Iron Will / Lightning Reflexes as separate bonus type.
- **WO-ENGINE-WEAPON-FINESSE-001** — ACCEPTED 8/8 (WF-001–WF-008). DEX replaces STR on attack rolls with light/finesseable weapons when `"weapon_finesse" in feats` and weapon qualifies. Prerequisite fix: `Weapon.enhancement_bonus` was missing from dataclass — added as part of this WO (latent bug catch).
- **WO-ENGINE-COMBAT-REFLEXES-001** — ACCEPTED 8/8 (CR-001–CR-008). `aoo_count_this_round` field on entity; max AoOs = 1 + DEX mod. Round-reset wired in BOTH `combat_controller.py` AND `play_controller.py` (builder found both sites). FINDING-ENGINE-FLATFOOTED-AOO-001 filed: no flat-footed AoO suppression in `aoo.py` — nothing to bypass currently.

**ACCEPTED 2026-02-26 — ENGINE BATCH C — ALL COMPLETE (4/4, 30/30 gate tests):**
- **WO-ENGINE-CLEAVE-ADJACENCY-001** — ACCEPTED 6/6 (CA-001–CA-006). `_find_cleave_target()` in `attack_resolver.py` now validates adjacency to killed creature's position before selecting cleave target. `Position.is_adjacent_to()` reused from `position.py:75-87`. Graceful fallback when position data missing.
- **WO-ENGINE-COMBAT-EXPERTISE-001** — ACCEPTED 8/8 (CEX-001–CEX-008). `combat_expertise_penalty` field on `AttackIntent`; `EF.COMBAT_EXPERTISE_BONUS` constant; attack penalty applied in `attack_resolver.py`; AC bonus written to entity and read on target; AC bonus non-linear (penalty 1→+1 AC, penalty 2–5→+2 AC, capped); cleared per-turn in `play_loop.py`. 4 files touched.
- **WO-ENGINE-RAPID-SHOT-001** — ACCEPTED 8/8 (RS-001–RS-008). Extra ranged attack appended at highest BAB; `raw_attack_bonuses` and `attack_bonuses` rebuilt in parallel to maintain index invariant. -2 penalty flows through `feat_resolver.get_attack_modifier()` automatically — no double-application.
- **WO-ENGINE-UNCANNY-DODGE-001** — ACCEPTED 8/8 (UD-001–UD-008). Flat-footed DEX bypass for rogue≥2/ranger≥4/barbarian≥2. Guard applied at TWO resolution paths (lines 388 + 924) — spec called one site; builder found natural-attack path also required it. Improved Uncanny Dodge (flanking immunity) deferred.

**DISPATCHED — WO-JUDGMENT-SHADOW-001 (Batch C clear trigger):**
- Phase 0 routing hook + validator shell + `_log_shadow_ruling()`. HOLD lifted. Batch D queue building.

**ACCEPTED 2026-02-26 — ENGINE BATCH A (5 WOs, 73 gate tests):**
- **WO-ENGINE-SAVE-FEATS-001** — ACCEPTED 10/10 (SF-01–SF-10). Great Fortitude / Iron Will / Lightning Reflexes wired in `get_save_bonus()`. 7-line insertion after inspire_courage block.
- **WO-ENGINE-SPELL-FOCUS-DC-001** — ACCEPTED 10/10 (SFD-01–SFD-10). `spell_focus_bonus` field on `CasterStats`; pre-resolve block in `play_loop.py` computes from `EF.FEATS`. School matching via lowercase feat name concat. Stacks: Spell Focus + Greater Spell Focus = +2 on same school.
- **WO-ENGINE-ARCANE-SPELL-FAILURE-001** — ACCEPTED 10/10 (ASF-01–ASF-10). ASF d100 check in `_resolve_spell_cast()` (play_loop.py), not spell_resolver (no entity access there). Slot consumed on failure. V-only spells (`has_somatic=False`) bypass. Divine casters bypass. 4 V-only spells added to registry.
- **WO-ENGINE-CONDITION-ENFORCEMENT-001** — ACCEPTED 12/12 (CE-001–CE-010). FINDING-ENGINE-CONDITION-ENFORCEMENT-001 PARTIAL-CLOSED. CE-A: `movement_prohibited` gate in `build_full_move_intent()` + both move branches in play_loop (FullMoveIntent new; StepMoveIntent generalized from hardcoded grapple names). CE-B: `actions_prohibited` already wired (WO-WAYPOINT-002, line 1330) — confirmed. CE-C: `loses_dex_to_ac` already wired (CP-17) — confirmed. Deferred: `auto_hit_if_helpless`, `standing_triggers_aoo`.
- **WO-ENGINE-RETRY-001** — ACCEPTED 29/29 (RP 14/14 + retry_policy 15/15). `exploration_time.py` + `retry_policy.py` + `execute_exploration_skill_check()` in play_loop all confirmed. Take 10/20, cache-hit/miss, per-skill retry rules, time advance events all live.

**ACCEPTED 2026-02-26 — WO-ENGINE-SKILL-MODIFIER-001 — 33/33 (RT2 11/11 + RP 14/14 + SM 8/8). FINDING-ENGINE-SKILL-MODIFIER-001 CLOSED.**
Delivered more than modifier lookup — filled RETRY-001 infrastructure gaps: `game_clock`/`skill_check_cache` on `WorldState` (`state.py`), `execute_exploration_skill_check()` in `play_loop.py`. Also delivered RETRY-002 wiring: `SkillCheckIntent`, `ParsedCommand` skill fields, `_normalize_skill()`, `_process_skill()` in `session_orchestrator.py`. Modifier formula: `ability_mod + ranks − ACP` inline (no private helper import). Graceful 0 on missing entity/skill. **`play_loop.py` now has `execute_exploration_skill_check()` — RETRY-001 infrastructure prerequisite met. RETRY-001 hold re-evaluate: only remaining conflict is Spell Focus DC on play_loop.py.**

**ACCEPTED 2026-02-26 — WO-CHARGEN-POOL-INIT-001 — 10/10. FINDING-CHARGEN-POOL-INIT-001 CLOSED.**
Five pool fields initialized at chargen: `EF.SMITE_USES_REMAINING`, `EF.LAY_ON_HANDS_POOL`, `EF.LAY_ON_HANDS_USED`, `EF.BARDIC_MUSIC_USES_REMAINING`, `EF.WILD_SHAPE_USES_REMAINING`. Two insertion sites: `build_character()` + `_build_multiclass_character()` — multiclass path required same init. Pass 3 catches: Wild Shape threshold corrected (≥4→≥5, PHB L5) + LoH formula corrected (`max(1,cha_mod)`→`cha_mod if cha_mod > 0 else 0`). Replay drift on `twd_ac_bonus` confirmed pre-existing (WO-ENGINE-GOLD-MASTER-REGEN-001).

**Paladin/Immunity batch ACCEPTED (2026-02-26 — 29/29 gate tests):**
- **WO-ENGINE-LAY-ON-HANDS-001** — ACCEPTED 11/11 (spec 10, builder added one extra). `EF.LAY_ON_HANDS_POOL` + `EF.LAY_ON_HANDS_USED`; `LayOnHandsIntent`; `lay_on_hands_resolver.py`; `rest_resolver.py` full-rest pool recovery; `action_economy.py` mapping; `play_loop.py` routing. Pass 3: builder.py chargen init NOT added — established pattern is entity-dict-at-load-time (same as smite, bardic, wild shape).
- **WO-ENGINE-SNEAK-ATTACK-IMMUNITY-001** — ACCEPTED 10/10. Pre-implemented. `sneak_attack.py` already had `SNEAK_ATTACK_IMMUNE_TYPES` + `is_target_immune()` checking creature_type. Audit misread the existing function. Zero production changes. Gate tests validate existing behavior. Pass 3 surfaced new finding: three different immunity field names (`immune_to_critical_hits`, `immune_to_sneak_attack`, `EF.CRIT_IMMUNE`) — fragmentation risk. FINDING-SAI-FRAGMENTATION-001 OPEN.
- **WO-ENGINE-DIVINE-HEALTH-001** — ACCEPTED 8/8. Two guard blocks in `poison_disease_resolver.py`: `apply_disease_exposure()` early-return before Fort save (paladin_level ≥ 3 → disease_immunity event, skip contraction) + `process_disease_ticks()` clear guard (paladin_level ≥ 3 + has active diseases → clear list). Poison immunity (already existing for paladin 3+) untouched.

**ACCEPTED 2026-02-26:**
- **WO-SEC-REDACT-001** — ACCEPTED 29/29. GAP-WS-003 + GAP-WS-004 CLOSED. ConnectionRole enum; TokenAdd/TokenUpdate dataclasses; hp/hp_max stripped for PLAYER role on join and on hp_changed events; raw StateUpdate passthrough replaced with explicit allowlist. New gap found: `_build_session_state()` still sends raw entity dicts with hp_current — FINDING-SEC-SESSION-STATE-001 OPEN. WO-SEC-REDACT-002 DISPATCH-READY.
- **WO-SEC-REDACT-002** — ACCEPTED 10/10. FINDING-SEC-SESSION-STATE-001 CLOSED. `_build_session_state()` now role-filtered: `_player_entity_fields()` / `_dm_entity_fields()` strip `_ENTITY_STRIP_PLAYER` frozenset (hp_current, hp_max, temporary_modifiers, active_poisons, active_diseases, wild_shape_saved_stats, original_stats) for PLAYER connections. Both call sites (join + resume) pass role. Design note: two filter families in ws_bridge — _player_token_fields (TokenAdd schema keys) and _player_entity_fields (raw engine dict keys). HP disclosure path fully closed.
- **WO-PARSER-NARRATION-001** — ACCEPTED 9/9 (PN-001–PN-008 + bonus test). Narration layer live. Two additions to `ws_bridge.py`: `ConnectionRole(Enum)` with PLAYER/DM/SPECTATOR values (scaffolds SEC-REDACT-001 role filtering); `action_dropped` event handler in `_turn_result_to_messages()` — emits `NarrationEvent` correction notice before general StateUpdate passthrough. `_turn_result_to_messages` signature extended with `session=None, role=None` kwargs. Everything else (`narration_bridge.py`, adapter, play_loop call site, test files) was already correctly implemented from prior work — prior debrief had falsely claimed ws_bridge handler was present; PN-004 caught the gap. Pre-existing failure: `test_dv_004` (unknown msg_type WARNING log) confirmed pre-dates this WO by git stash check. 27/27 PN + SR gate tests clean.

**ACCEPTED 2026-02-26 — attack layer batch (40/40 gate tests):**
- **WO-ENGINE-FAVORED-ENEMY-001** — ACCEPTED 10/10. `EF.FAVORED_ENEMIES` + `EF.CREATURE_TYPE` added to `entity_fields.py`. Attack bonus in `attack_resolver.py:397-398` and `full_attack_resolver.py:706-709`. Damage bonus applied post-crit (flat, per PHB p.47) in both resolvers.
- **WO-ENGINE-MASSIVE-DAMAGE-001** — ACCEPTED 10/10. DC 15 Fort check injected in `attack_resolver.py` between `hp_after` assignment and `if final_damage > 0:` block. On fail: `hp_after = -10` → existing `resolve_hp_transition` emits `entity_defeated`. Uses `rng.stream("combat")` (deterministic replay preserved).
- **WO-ENGINE-WEAPON-ENHANCEMENT-001** — ACCEPTED 10/10. `enhancement_bonus: int = 0` added to `Weapon` dataclass. Added to base damage (pre-crit, multiplicative on crits per PHB p.224) in both resolvers. Added to `attack_bonus_with_conditions` in both resolvers. New `favored_enemy_bonus` parameter added to `resolve_single_attack_with_critical()`.
- **WO-ENGINE-STABILIZE-ALLY-001** — ACCEPTED 10/10. New `stabilize_resolver.py` — DC 15 Heal check, sets `EF.STABLE = True` on success. `StabilizeIntent` added to `intents.py`. Routed in `play_loop.py` — standard action in `action_economy.py`.

**ACCEPTED 2026-02-26:**
- **WO-SEC-REDACT-001** — ACCEPTED 29/29. GAP-WS-003 + GAP-WS-004 CLOSED. ConnectionRole enum; TokenAdd/TokenUpdate dataclasses; hp/hp_max stripped for PLAYER role on join and on hp_changed events; raw StateUpdate passthrough replaced with explicit allowlist. New gap found: `_build_session_state()` still sends raw entity dicts with hp_current — FINDING-SEC-SESSION-STATE-001 OPEN. WO-SEC-REDACT-002 DISPATCH-READY.
- **WO-SEC-REDACT-002** — ACCEPTED 10/10. FINDING-SEC-SESSION-STATE-001 CLOSED. `_build_session_state()` now role-filtered: `_player_entity_fields()` / `_dm_entity_fields()` strip `_ENTITY_STRIP_PLAYER` frozenset (hp_current, hp_max, temporary_modifiers, active_poisons, active_diseases, wild_shape_saved_stats, original_stats) for PLAYER connections. Both call sites (join + resume) pass role. Design note: two filter families in ws_bridge — _player_token_fields (TokenAdd schema keys) and _player_entity_fields (raw engine dict keys). HP disclosure path fully closed.
- **WO-PARSER-NARRATION-001** — ACCEPTED 9/9 (PN-001–PN-008 + bonus test). Narration layer live. Two additions to `ws_bridge.py`: `ConnectionRole(Enum)` with PLAYER/DM/SPECTATOR values (scaffolds SEC-REDACT-001 role filtering); `action_dropped` event handler in `_turn_result_to_messages()` — emits `NarrationEvent` correction notice before general StateUpdate passthrough. `_turn_result_to_messages` signature extended with `session=None, role=None` kwargs. Everything else (`narration_bridge.py`, adapter, play_loop call site, test files) was already correctly implemented from prior work — prior debrief had falsely claimed ws_bridge handler was present; PN-004 caught the gap. Pre-existing failure: `test_dv_004` (unknown msg_type WARNING log) confirmed pre-dates this WO by git stash check. 27/27 PN + SR gate tests clean.

Thunder to direct next dispatch on verdicts.

**BATCH E — DRAFTED, DISPATCH-READY (pending Batch D close):**
- **WO-ENGINE-EVASION-ARMOR-001** — DISPATCH-READY. Evasion armor restriction: medium/heavy armor suppresses Evasion (PHB p.50). `EF.ARMOR_TYPE` unblocks this; two guard checks in `spell_resolver.py`. 8 gate tests (EA-001–008). Dispatched to: `pm_inbox/WO-ENGINE-EVASION-ARMOR-001_DISPATCH.md`.
- **WO-ENGINE-CALLED-SHOT-POLICY-001** — DISPATCH-READY. Option A (STRAT-CAT-05): hard denial + route to nearest named mechanic. `CalledShotIntent` dataclass; `action_dropped` event emission in `execute_turn()`; suggestion map. 8 gate tests (CS-001–008). Kernel touches: KERNEL-04 (Intent Semantics), KERNEL-10 (Adjudication Constitution). Dispatched to: `pm_inbox/WO-ENGINE-CALLED-SHOT-POLICY-001_DISPATCH.md`.

**REDTEAM-CREATIVE-ADVERSARIAL-001 filed (2026-02-26 — Thunder + Anvil):** 15 adversarial player test categories. Source: Chaotic Good Barbarian Season 1 scenario patterns. Filed at `docs/design/REDTEAM-CREATIVE-ADVERSARIAL-001.md`.
- **PROBE-WORLDMODEL-001** filed to pm_inbox — queued behind PROBE-JUDGMENT-LAYER-001. World model gap: no persistent objects, no corpse/remnant state, no entity-contents model.
- **STRAT-CAT-05-CALLED-SHOT-POLICY-001** — DECIDED. Option A now (hard denial + routing to nearest named mechanic). Option C upgrade path pre-committed pending scaffold validation. WO draftable when Batch D clears.
- **REGISTER-HIDDEN-DM-KERNELS-001 filed (2026-02-26 — Thunder + Anvil):** 10 hidden DM kernels named and scoped. `docs/design/REGISTER-HIDDEN-DM-KERNELS-001.md`. Cross-pollination routing instruction live: when WO debrief Pass 3 touches a kernel, flag it in the register. Coverage map = mechanics implemented. Kernel register = assumptions implemented. Both required. KERNEL-01 (Entity Lifecycle) CRITICAL. KERNEL-03 (Constraint Algebra) / KERNEL-05 (Epistemic State) / KERNEL-06 (Termination Doctrine) / KERNEL-10 (Adjudication Constitution) HIGH.
- **PACK-CREATIVE-ADVERSARIAL-INTENTS-001** — Phase 2 material. Do not touch until PROBE-JUDGMENT-LAYER-001 closes.
- **Inbox hygiene flag:** pm_inbox root at 21 files vs. 15-file cap. Cleared 3 archived files. Remaining overage: WO-UI-GATES-V1 + WO-UI-VISREG-PLAYWRIGHT-001 + WO-SMOKE-TRIAGE-001 are blocked/pending — Thunder to call on archiving or holding.

## Current Focus (Slate's focused recall)

**UI SLICES 0-7 COMPLETE. CHARGEN PHASE 3 COMPLETE. P1 PASS (commit `c7e571e`). RC READY pending HOOLIGAN-03.**
- **UI Slices 3-7 ACCEPTED:** `book-object.ts` (PHB rulebook, page flip, QuestionStamps), `notebook-object.ts` (notes/transcript/bestiary/handouts), `handout-object.ts` (printer slot + tray 1.6×1.3m navy felt + fanstack + discard ring), `map-overlay.ts` (AoE shapes, measure line, area highlight), `entity-renderer.ts` (+getTokenMeshes), `main.ts` (all slices wired), `index.html` (AoE gate). Gate G 22/22.
- **Zone realignment:** `zones.json` player centerZ=4.75/halfHeight=0.80 (shelf), dice_tray z=1.75, dice_tower z=0.5. Gate G zone test updated to match.
- **Chargen Phase 3 COMPLETE:** V9 level_up() 20/20, V10 companions 25/25, V11 racial traits 18/18, V12 dual-caster 20/20. `build_animal_companion()` live. All 7 PHB races have mechanical trait EF fields. `_merge_spellcasting()` handles 0/1/2 caster classes. V9 `level_up()` pure delta, CLASS_FEATURES 11 classes, seeded HP roll.
- **UI-06 ACCEPTED:** `entity-renderer.ts` EntityRenderer class, faction-colored tokens, HP bar, gridToScene(), Gate UI-06 10/10.
- **PRS-01:** RC READY. All gates clean. Dirty tree resolved (commit `c7e571e`).

**Deferred:** Chatterbox swap timing (8.0s budget). GAP-B HIGH (VS Build Tools). FINDING-WORLDGEN-IP-001.

**Active dispatches:** **Layout Pack UI sequence:** WO-UI-CAMERA-OPTICS-001 (**DISPATCH**) → WO-UI-CAMERA-FRAMING-DICE-TRAY-FINAL (**BLOCKED** on OPTICS) → WO-UI-VISUAL-QA-002 (**DISPATCH**, amended ×2) → WO-UI-VISREG-PLAYWRIGHT-001 (**DISPATCH** — harness live, baseline BLOCKED on Thunder approval) → WO-UI-GATES-V1 (**BLOCKED** on golden frames). **ENGINE DISPATCH #5 — ALL ACCEPTED. ENGINE DISPATCH #6 — ALL ACCEPTED:** WO-ENGINE-ABILITY-DAMAGE-001 (10/10 AD-01..AD-10) + WO-ENGINE-POISON-DISEASE-001 (10/10 PD-01..PD-10) + WO-ENGINE-WITHDRAW-DELAY-001 (10/10 WD-01..WD-10) + WO-ENGINE-CONDITIONS-BLIND-DEAF-001 (19/19 BD-01..BD-10) + WO-ENGINE-SUNDER-DISARM-FULL-001 (10/10 SD-01..SD-10). Suite: 7,173 passing / 23 pre-existing failures.

**CHARGEN PHASE 3 COMPLETE:** V10 (companions 25/25) + V11 (racial traits 18/18) + V12 (dual-caster 20/20). `build_animal_companion()` live. All 7 PHB races have mechanical trait fields. `_merge_spellcasting()` handles 0/1/2 caster classes. Dual-caster: alphabetical primary (`cleric < wizard`), separate `_2` suffix fields for secondary. `spell_choices_2` param on `build_character()`. 3+ casters raises ValueError.

**BURST-001:** ~~Tier 1~~ → ~~Tier 2~~ → ~~RV-007~~ → ~~Tier 3~~ → ~~Tier 4~~ → ~~Tier 5.1-5.4~~ → ~~**5.5 Playtest v1 — ACCEPTED**~~ **BURST-001 COMPLETE.**
**PRS-01:** ~~Spec review~~ → ~~5 WOs dispatched~~ → ~~**5/5 ACCEPTED**~~ → ~~**SCAN FIX ACCEPTED**~~ → ~~pre-RC cleanup~~ → ~~**ALL GATES GREEN**~~ → ~~**ORCHESTRATOR ACCEPTED**~~ → **commit + IP remediation (WO-PRS-IP-001) → RC READY**
**UI:** ~~WO-UI-01~~ → ~~WO-UI-02~~ → ~~WO-UI-03~~ → ~~WO-UI-04~~ → ~~WO-UI-05 ACCEPTED pending visual~~ (table surface + atmosphere) → **WO-UI-06 DISPATCHED** (entity tokens, HP bars, live WS bridge)
**CHARGEN:** ~~Research~~ → ~~Foundation~~ → ~~Skills~~ → ~~Classes~~ → ~~Feats~~ → ~~Spellcasting~~ → ~~Spell Expansion~~ → ~~**Builder Capstone**~~ → ~~**CHARGEN PHASE 1 COMPLETE**~~ → ~~**WO-CHARGEN-EQUIPMENT-001 (V7 73/73)**~~ → ~~**WO-CHARGEN-MULTICLASS-001 (V8 15/15)**~~ → ~~**CHARGEN PHASE 2 COMPLETE**~~ → ~~WO-CHARGEN-PHASE3-LEVELUP (Gate V9)~~ → ~~**WO-CHARGEN-DUALCASTER-001 (V12 20/20)**~~ → ~~**WO-CHARGEN-COMPANION-001 (V10 25/25)**~~ → ~~**WO-CHARGEN-RACIAL-001 (V11 18/18)**~~ → **CHARGEN PHASE 3 COMPLETE**

## Open Findings

| Finding | Severity | Status | Description |
|---------|----------|--------|-------------|
| FINDING-SEC-SESSION-STATE-001 | HIGH | **CLOSED** | `_build_session_state()` in ws_bridge.py sends raw entity dicts including hp_current to all clients — second HP disclosure path. CLOSED by WO-SEC-REDACT-002 ACCEPTED 10/10. |
| FINDING-ASF-ARCANE-CASTER-001 | LOW | OPEN | `_is_arcane` in play_loop.py is a three-class whitelist (wizard/sorcerer/bard). Rangers/paladins with partial arcane casting will need extension when those classes get spell slots. Non-blocking. |
| FINDING-CE-AUTO-HIT-HELPLESS-001 | MEDIUM | **CLOSED** | Auto-hit enforcement confirmed already implemented at `attack_resolver.py:380` — coverage audit 2026-02-27 misread the function. Zero production changes. |
| FINDING-CE-STANDING-AOO-001 | LOW | OPEN | `standing_triggers_aoo` (prone stand-up provokes AoO) not wired in aoo.py. Deferred pending grapple movement WO. |
| FINDING-SF-SAVE-BREAKDOWN-001 | LOW | OPEN | `save_rolled` event payload emits single `save_bonus` int — no component breakdown (feats + inspire courage + divine grace + racial). Auditability gap, not a correctness bug. Future enhancement WO. |
| FINDING-SAI-FRAGMENTATION-001 | LOW | **CLOSED** | WO-ENGINE-SNEAK-ATTACK-AUTO-IMMUNE-001 ACCEPTED (Batch M, commit 14b2c18). `_apply_creature_type_immunities(entity)` added to `builder.py`. PHB ooze/plant/elemental = SA-immune only; undead/construct = SA + crit immune. Residual: multiclass builder path not covered → FINDING-ENGINE-MULTICLASS-BUILDER-IMMUNE-001 (LOW). |
| FINDING-CHARGEN-POOL-INIT-001 | MEDIUM | **CLOSED** | `build_character()` outputs class features as string markers only — pool fields never initialized. CLOSED by WO-CHARGEN-POOL-INIT-001 ACCEPTED 10/10. Five pool fields now init at chargen in both `build_character()` and `_build_multiclass_character()`. |
| FINDING-ENGINE-MASSIVE-DAMAGE-FULL-ATTACK-001 | LOW | OPEN | Massive damage check (PHB p.142, DC 15 Fort or die at 50+ damage) fires in `attack_resolver.py` only. In a full attack sequence, per-hit damage is finalized in `resolve_single_attack_with_critical()`, which lacks access to world_state or a save resolver; the HP transition in `full_attack_resolver.py` is batched (cumulative hp_changed). A single iterative attack dealing 50+ damage in a full attack does not trigger the check. Known architectural gap — requires per-hit consequence plumbing in full_attack_resolver.py. Defer to a dedicated WO when full-attack per-hit consequences are generally addressed. Non-blocking. |
| FINDING-SKILL-PARSER-REGISTRY-DRIFT-001 | LOW | OPEN | Two sources of truth for canonical skill names: `_normalize_skill()` in `session_orchestrator.py` (maps player verbs → canonical names) and `SKILL_TIME_COSTS` in `exploration_time.py` (defines valid skills + time costs). Not automatically synchronized — a skill added to `SKILL_TIME_COSTS` without a corresponding entry in `_normalize_skill()` would route player input to `unknown` instead of `skill`. Also: `"listen"` is in `_normalize_skill()` but absent from `SKILL_TIME_COSTS` — gets 60s default cost and `RETRY_ALLOWED` default True, which is functionally acceptable but undeclared. Conservative fix when registry grows: have `_normalize_skill()` fall back to checking whether the normalized verb is a key in `SKILL_TIME_COSTS` directly. One-line guard. Not a standalone WO — attach as a line item to any future WO touching `session_orchestrator.py` or `exploration_time.py`. |
| FINDING-PLAY-LOOP-ROUTING-001 | MEDIUM | CLOSED | WO-ENGINE-PLAY-LOOP-ROUTING-001 ACCEPTED 10/10 — 5 elif branches wired in execute_turn. Rogue local imports fixed (UnboundLocalError in 23 pre-existing tests). |
| FINDING-WILDSHAPE-NATURAL-ATTACKS-001 | MEDIUM | CLOSED | WO-ENGINE-NATURAL-ATTACK-001 ACCEPTED 10/10 — `natural_attack_resolver.py` live, `NaturalAttackIntent` wired. |
| FINDING-WILDSHAPE-HP-001 | LOW | OPEN | ENGINE DISPATCH #8: Wild Shape HP uses simplified Con-based formula. PHB proportional HP swap deferred. Non-blocking. |
| FINDING-WILDSHAPE-DURATION-001 | LOW | OPEN | ENGINE DISPATCH #8: Wild Shape duration not auto-decremented. DM must trigger revert manually. Non-blocking. |
| FINDING-BARDIC-DURATION-001 | LOW | CLOSED | WO-ENGINE-BARDIC-DURATION-001 ACCEPTED 20/20 — `_bard_is_incapacitated()` check in `tick_inspire_courage()`. Latent decrement-ghost fixed (any_mutated pattern). |
| FINDING-ENGINE-CONDITION-DURATION-001 | HIGH | CLOSED | WO-ENGINE-CONDITION-DURATION-001 ACCEPTED 10/10 — `ConditionInstance.duration_rounds: Optional[int] = None` added; `tick_conditions()` two-pass (ARCH-TICK-001) wired in play_loop:2977. STUNNED/DAZED/NAUSEATED = 1 round; PRONE/GRAPPLED permanent. CD-001–010 all PASS. |
| FINDING-SCAN-BASELINE-01 | MEDIUM | RESOLVED | Gate X: base64 false positives fixed (P5 skip list). `*.jsonl` on asset allowlist. X-01 remains: real tracked artifacts (`models/voices/`, `inbox/`). Gate X 9/10. |
| FINDING-ORC-P8-001 | MEDIUM | RESOLVED | P8: 296 violations → 0. 59 exceptions in `ip_exceptions.txt` (provenance docs, test fixtures, PM tooling). 4 content removals (README Vecna/Heironeous, npc_stingers Waterdeep×2). |
| FINDING-ORC-P1-001 | LOW | RESOLVED | P1 dirty tree resolved. Commit `9bf1d3d`. |
| FINDING-UI05-P2-001 | MEDIUM | RESOLVED | WO-UI-05: scene-builder.ts Math.random replaced with seeded PRNG (`makePrng`). Gate G 22/22 PASS. W-01–W-14 PASS. W-15 fails due to V7 test gap (equipment tests exist, not WO-UI-05 scope). Visual gate pending Thunder review. |
| FINDING-NS-AUDIT-001 | MEDIUM | OPEN | North Star full audit (2026-02-23): 3 pure-client P0 gaps (scene images on DM side, text input fallback, fog vision types); 4 P1 gaps (player-only token drag, handout→trash drag, stronger scroll grid, portrait swirl shader); 6+ P2/deferred gaps (radial notebook menu, text on page, second char sheet, full dice set, torn pages, rulebook bookmarks). Backend-required: TTS/STT (FINDING-PLAYTEST-F01), world-compiled rulebook, terrain tiles, movement enforcement, image asset pipeline. WOs drafted for 3 P0 gaps. |
| FINDING-PLAYTEST-F01 | MEDIUM | OPEN | TTS env not provisioned. Neither Chatterbox nor Kokoro installed. 7 TTS-dependent checkpoints validated by proxy (unit tests). Live audio deferred. |
| FINDING-HOOLIGAN-03 | MEDIUM | RESOLVED | WO-FIX-HOOLIGAN-03 ACCEPTED. `_check_rv001_hit_miss()` scoped to first sentence via `. ` split. Gate K 69→72 (49/49 narration validator). FINDING-HOOLIGAN-03 RESOLVED. |
| FINDING-CHARGEN-SKILLS-01 | MEDIUM | RESOLVED | Anvil skills WO (`8a9442a`) broke 4 tests (not 3 as originally reported): stale hardcoded counts. Fixed by Thunder. |
| FINDING-GRAMMAR-01 | LOW | RESOLVED | WO-FIX-GRAMMAR-01 ACCEPTED. `play.py:647` `.title()` appended. Gate K 67→69. 2 regression tests. |
| FINDING-SIGLIP-01 | LOW | RESOLVED | `test_siglip_critique.py` merge conflicts resolved by Anvil (`20797a9`) |
| GAP-A | LOW | RESOLVED | `dm_persona.py` missing import fixed via `TYPE_CHECKING` guard — no runtime BL violation. Boundary law test PASS. |
| FINDING-ENGINE-ENCUMBRANCE-CATALOG-001 | LOW | **CLOSED** | WO-ENGINE-ENCUMBRANCE-WIRE-001 ACCEPTED (Batch M, commit ad21df2). EF.ENCUMBRANCE_LOAD was already pre-computed at chargen. Two-line wire-up in each resolver. Deferred comment was wrong about catalog unavailability. |
| GAP-B | HIGH | OPEN | llama-cpp-python blocks Qwen3/Gemma3 (needs VS Build Tools) |
| FINDING-ENGINE-COVER-VALUES-001 | HIGH | **CLOSED** | Cover bonuses corrected by WO-ENGINE-COVER-FIX-001 (Batch M, commit 548e2cf). IMPROVED cover was +8 AC (no PHB basis); fixed to +4 AC/+3 Ref per PHB p.150. terrain_resolver.py only needed change. Residual: terrain.py:49 docstring still says +8 → FINDING-SCHEMA-COVER-DOCSTRING-001 LOW OPEN. |
| FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 | LOW | **CLOSED** | Counter-disarm logic inverted + raw-roll margin fixed in WO-ENGINE-IMPROVED-DISARM-COUNTER-001 (Batch P, commits 5d088d6+0440ffa). margin=defender_total−attacker_total; counter if ≥10; Improved Disarm suppresses with `counter_disarm_suppressed` event. |
| FINDING-ENGINE-IMPROVED-DISARM-BONUS-001 | LOW | **CLOSED** | Improved Disarm +4 bonus wired at single opposed check site in maneuver_resolver.py (Batch P WO2/IMB, commit 336f04d). Batch L claim "+4 already wired" confirmed FALSE. |
| FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001 | LOW | **CLOSED** | Improved Grapple +4 grapple check bonus wired at single opposed check site in maneuver_resolver.py (Batch P WO2/IMB, commit 336f04d). |
| FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001 | LOW | **CLOSED** | Improved Bull Rush +4 STR check bonus wired at single opposed check site in maneuver_resolver.py (Batch P WO2/IMB, commit 336f04d). |
| FINDING-ENGINE-IMPROVED-OVERRUN-AOO-001 | LOW | **CLOSED** | WO-ENGINE-IMPROVED-OVERRUN-001 ACCEPTED Batch O. AoO suppression wired in play_loop.py + defender-avoid suppression in maneuver_resolver.py. |
| FINDING-ENGINE-BLIND-FIGHT-INVIS-001 | LOW | OPEN | Blind Fight miss-chance reroll applies to concealment-based misses (fog/darkness) but not invisibility-based (different PHB rule set). Deferred from Batch O WO3. Future WO. |
| FINDING-ENGINE-IMPROVED-OVERRUN-BONUS-001 | LOW | OPEN | Improved Overrun +4 Strength check bonus — confirm all overrun check paths read the feat (same pattern as DISARM/GRAPPLE/BULL-RUSH bonus findings). Deferred from Batch O WO1. Future WO. |
| FINDING-SCHEMA-COVER-DOCSTRING-001 | LOW | OPEN | `terrain.py:49` docstring still says `IMPROVED = +8 AC` after WO-ENGINE-COVER-FIX-001 fixed the resolver. One-line docstring fix. Non-blocking; surfaced Batch M WO1 Pass 3. |
| FINDING-SCHEMA-TERRAIN-TAG-ORPHAN-001 | LOW | OPEN | `HALF_COVER`/`THREE_QUARTERS_COVER` enum members in `terrain.py:34-35` are unused (orphaned). Rename or remove to match implemented `CoverType.HALF`/`CoverType.IMPROVED`. Surfaced Batch M WO1 Pass 3. |
| FINDING-ENGINE-MULTICLASS-BUILDER-IMMUNE-001 | LOW | OPEN | `_apply_creature_type_immunities()` not called in `_build_multiclass_character()` — only `build_character()` got it. Multiclass undead/construct PCs will not receive SA/crit immunity at build time. Surfaced Batch M WO3 Pass 3. |
| FINDING-ENGINE-BARD-ROGUE-MARTIAL-PARTIAL-001 | LOW | OPEN | Bard and rogue have partial martial weapon proficiency (not full martial). `proficiency_category: Optional[str] = None` currently only models `simple`/`martial`/`exotic` — no "partial_martial" or per-weapon-list variant. Surfaced Batch M WO4 Pass 3. Future WO. |
| FINDING-ENGINE-IMPROVED-TRIP-BONUS-001 | LOW | **CLOSED** | Improved Trip +4 STR check bonus wired at single opposed check site in maneuver_resolver.py (Batch P WO2/IMB, commit 336f04d). |
| FINDING-ENGINE-IMPROVED-SUNDER-BONUS-001 | LOW | **CLOSED** | Improved Sunder +4 opposed attack bonus wired at single opposed check site in maneuver_resolver.py (Batch P WO2/IMB, commit 336f04d). |
| FINDING-ENGINE-PA-2H-PHB-DEVIATION-001 | LOW | OPEN | 2H Power Attack implemented at 1.5× per dispatch spec; PHB p.98 says 2×. Needs Thunder ruling: intentional game-design deviation or spec error? |
| FINDING-ENGINE-PA-FULL-ATTACK-ROUND-LOCK-001 | LOW | OPEN | PA penalty must apply to ALL attacks in the round (declared before rolling). Engine trusts caller to pass same penalty on each AttackIntent in a full-attack sequence — no round-level enforcement. Batch P PA debrief. |
| FINDING-ENGINE-PRECISE-SHOT-FEAT-RESOLVER-DEAD-CODE-001 | LOW | OPEN | `ignores_shooting_into_melee_penalty()` in feat_resolver.py is dead code — never called. The -4 penalty check lives entirely in attack_resolver.py. Future cleanup: remove or wire. No functional impact. Batch P PS debrief. |
| FINDING-ENGINE-IDC-DEX-STRIPPED-001 | LOW | OPEN | PHB p.96/155: attacker loses DEX bonus to AC for the counter-disarm attempt. Not implemented — counter uses normal `_roll_opposed_check` with no flat-footed modification. Future WO. Batch P IDC debrief. |
| FINDING-ENGINE-IMPROVED-TRIP-WEAPON-CONTEXT-001 | LOW | OPEN | Improved Trip free attack requires a weapon present in `TripIntent`. Optional weapon field added to `TripIntent` schema (Batch N WO4). If no weapon provided, free attack silently skipped. Formal validation + fallback logic deferred. |
| FINDING-ENGINE-RAPID-SHOT-001 | MEDIUM | **CLOSED** | Rapid Shot bonus attack confirmed already wired in Batch C (full_attack_resolver.py). Coverage audit 2026-02-27 confirmed live. Zero production changes needed. |
| FINDING-HG-EQUIPMENT-MGMT-001 | MEDIUM | OPEN | No DropItemIntent / UnequipIntent resolver. PHB p.142: drop item = free action, sheathe/draw = move action. Engine cannot model mid-combat equipment state changes. |
| FINDING-HG-IMPROVISED-WEAPON-001 | MEDIUM | OPEN | `weapon_type='improvised'` rejected by Weapon.__post_init__ ValueError. PHB p.113: improvised weapons valid with −4 attack penalty. Schema fix + resolver needed. |
| FINDING-HG-READY-ACTION-SCOPE-001 | LOW | OPEN | ReadyIntent is wired (execute_turn:2026) but deferred: initiative drop on fire, cross-round persistence not implemented. PHB p.160: firing a readied action moves actor to just before the creature that triggered it in initiative. Partial implementation. |
| FINDING-COVERAGE-MAP-001 | HIGH | OPEN | PHB+DMG mechanics audit complete. 148 mechanics: 62 FULL (42%), 28 PARTIAL (19%), 8 BUG (5%), 8 STUB (5%), 28 MISSING (19%), 14 DEFERRED (9%). 44 prioritized gaps filed in `audit/ENGINE_COVERAGE_MAP.md`. Priority 1 gaps (blocking every combat): Cover IMPROVED bug (+8/+4 engine vs +4/+3 PHB), Power Attack activation absent, Wild Shape HP formula wrong, Rapid Shot bonus attack missing, improvised weapons schema-rejected, no Drop/Pickup/Unequip intents, arcane spell failure not checked, massive damage rule absent. Priority 3 gap: entire Monk class unimplemented; Paladin 3 features missing; Rogue Evasion/Uncanny Dodge absent; Bard 6 performances absent. Priority 4 gap: magic items entirely unimplemented (potions, wands, scrolls, magic weapon/armor bonuses). |
| STRATEGY-AIDM-JUDGMENT-LAYER-001 | HIGH | OPEN | **Improvised action synthesis above the resolver stack.** Current architecture: Parser → Intent → Resolver (named mechanic) → Events. Creative player actions that don't map to a named mechanic fall into parser misroute or LLM hallucination (silent, unaudited). A real DM applies: (1) goal inference, (2) nearest governing mechanic, (3) circumstance/risk modification, (4) DC/consequence ruling. The engine has no synthesis layer — the LLM performs this silently and inconsistently. **Architecture direction (3-layer control loop):** LLM Proposer generates candidate ruling + rationale → Deterministic Validator checks schema/legality/modifier sources/DC range → Event Compiler emits canonical `RulingEvent`. **Ruling Contract** (minimum fields): `player_action_raw`, `intent_goal`, `chosen_mechanic`, `ability_or_skill`, `dc`, `modifiers[]`, `risk_profile`, `consequence_on_success`, `consequence_on_failure`, `confidence`, `rationale_trace`. **Testability criteria:** consistency across paraphrases, legal mechanic selection, bounded DC range, consequence coherence, replayability/audit completeness. **Routing rule needed:** formal classification for named mechanic / named+circumstance / improvised synthesis / impossible. **Phased path:** Shadow (log-only) → Guarded (structured output required) → Canonical (event-emitting, replayable). Not a WO — strategy/system-boundary decision pending Thunder direction. Filed 2026-02-26. |
| FINDING-HOOLIGAN-TOWN-DESTRUCTION-001 | HIGH | FILED | CE level-20 wizard town-destruction stress test identified as next major Hooligan gate. Requires: object HP/hardness tables (walls, doors, structures — DMG p.59); AoE rasterization against objects; structural damage propagation; fire spread; NPC HP at scale; Wish mechanic boundary condition (fail-closed vs hallucinate). Engine currently has DEEP_WATER tag and falling damage but no wall HP tracking. This is the "where does it start lying confidently" audit. Blocked until Priority 1 gaps clear. |
| FINDING-WORLDGEN-IP-001 | HIGH | OPEN | Source material names (Mind Flayer, Beholder, etc.) are retained in internal data as **audit anchors** — required for accuracy verification against source. Names cannot be stripped until: (1) source ingestion is complete ✅ **WO-WORLDGEN-INGESTION-001 ACCEPTED — Gate INGESTION 15/15. `ingestion_report.json` baseline: 273 creatures, 605 spells, 109 feats. 7 field-length warnings (environment_tags/alignment_tendency >100 chars on 7 creatures) recorded as double-audit subjects — non-blocking.**, (2) double audit confirms every mechanical value (HP, AC, attacks, abilities) matches source material exactly, (3) strip replaces names with IDs. Only after strip is complete can World Gen LLM mode be enabled to apply new skin. Additionally: no post-generation IP scan exists before bundle commit (Recognition Test in `WORLD_COMPILER.md §2.1` specified but not gated). **Full pre-condition chain:** ~~ingestion complete~~ → double audit PASS → name strip → IP scan gate on bundle output → LLM mode enabled. Not a current RC blocker — RC ships stub mode (IDs already). PRS-01 amendment candidate for bundle scan gate. |
| FINDING-ENGINE-DOMAIN-SYSTEM-MISSING-001 | MEDIUM | OPEN | No `EF.DOMAINS` field in `entity_fields.py`. No `EF.GREATER_TURNING_USES_REMAINING`. Sun domain and all other domain-granted powers (War domain, etc.) are blocked. Surfaced by WO4 SD BLOCKED (Batch T, d578e22). Requires a new WO: add `EF.DOMAINS` (list of strings) to entity_fields.py + wire domain list at chargen in builder.py + add `EF.GREATER_TURNING_USES_REMAINING` for Sun domain. |
| FINDING-ENGINE-NAT-ATTACK-DELEGATION-PATH-001 | LOW | OPEN | `natural_attack_resolver.py` delegates entirely to `attack_resolver.resolve_attack()` via deferred import. For Batch Q WO3 (Weapon Focus Creature), the bonus can be implemented in `attack_resolver.py` by checking `weapon_type="natural"` — no `natural_attack_resolver.py` touch needed. Surfaced Batch T WO1 Pass 3. INFO for Batch Q builder. |
| FINDING-ENGINE-INA-NONSTANDARD-DIE-001 | LOW | OPEN | Creatures with non-standard base damage dice not in `_INA_STEP_TABLE` (e.g., `"1d12"`, `"1d10"`) silently receive no INA die upgrade (pass-through without error). PHB standard natural attack creatures use step-table dice so risk is LOW, but edge cases with custom creatures are affected. Surfaced Batch T WO2 Pass 3. |
| FINDING-ENGINE-DISARM-SIZE-MODIFIER-001 | MEDIUM | OPEN | Disarm uses SPECIAL size modifier (`_get_size_modifier`) instead of standard attack size modifier. PHB p.155: disarm uses opposed attack rolls. 5-point swing at non-Medium sizes. Fix: one-line at `maneuver_resolver.py:1448`. Surfaced AUDIT-WO-002. |
| FINDING-ENGINE-COUNTER-DISARM-THRESHOLD-001 | MEDIUM | OPEN | Counter-disarm gated on `margin >= 10`. PHB p.155: defender counters on ANY failed disarm. No margin threshold in RAW. Surfaced AUDIT-WO-002. |
| FINDING-ENGINE-SECONDARY-STR-HALF-001 | MEDIUM | OPEN | Secondary natural attacks get 1x STR to damage instead of RAW 0.5x. `grip="one-handed"` hardcoded for all natural attacks. Fix: `grip="off-hand"` when `is_primary=False`. Surfaced AUDIT-WO-002. |
| FINDING-ENGINE-MANEUVER-ATTACK-REPLACEMENT-001 | MEDIUM | OPEN | Trip/Disarm/Sunder registered as "standard" in action_economy.py. PHB defines them as melee attack replacements (can substitute into full attack). Architectural. Surfaced AUDIT-WO-002. |
| FINDING-ENGINE-OVERRUN-FAILURE-PRONE-CHECK-001 | MEDIUM | OPEN | Overrun failure prone sub-check uses Str-only. PHB p.157: "opposed by your Dexterity or Strength check (whichever is greater)." Fix: `max(str_mod, dex_mod)` at `maneuver_resolver.py:1007`. Surfaced AUDIT-WO-002. |
| FINDING-ENGINE-TRIP-FREE-ATTACK-UNARMED-001 | LOW | OPEN | Improved Trip free attack silently skips when attacker has no `EF.WEAPON`. Monks tripping unarmed get no free attack. Surfaced AUDIT-WO-002. |
| FINDING-ENGINE-IMPROVED-DISARM-COUNTER-SUPPRESS-001 | LOW | OPEN | Improved Disarm suppresses counter-disarm — common house rule but not PHB RAW p.95. Thunder policy call needed: keep or remove? Surfaced AUDIT-WO-002. |
| FINDING-ENGINE-OVERRUN-DURING-MOVE-001 | LOW | OPEN | Overrun registered as "standard" but PHB p.157 says "taken during your move action." Movement-embedded nature not modeled. Surfaced AUDIT-WO-002. |

## Inbox

- **[NEW] [DEBRIEF_AUDIT-WO-002-MANEUVERS.md](pm_inbox/DEBRIEF_AUDIT-WO-002-MANEUVERS.md)** — AUDIT-WO-002: Domain C (maneuvers) + Domain D (natural attacks). 18 rows audited, 8 FULL / 10 DEGRADED. 8 new findings (4 MEDIUM, 4 LOW). Commit `af48465`. PM verdict needed.
- **[ACCEPTED] [WO-ENGINE-GOLD-MASTER-REGEN_DISPATCH.md](pm_inbox/WO-ENGINE-GOLD-MASTER-REGEN_DISPATCH.md)** — Pre-existing replay suite drift: `hp_changed.dr_absorbed: 0 vs None` in tavern fixture (introduced by WO-ENGINE-DR-001 adding `dr_absorbed` to every `hp_changed` payload). Also: WO-ENGINE-DEATH-DYING-001 changed `entity_defeated` semantics + added new event types, potentially affecting any fixture with HP≤0. Fix: write `scripts/regen_gold_masters.py` — load each existing JSONL, extract embedded `scenario_config`, re-record with `ReplayRegressionHarness.record_gold_master()` + `save_gold_master()`. Fixtures: tavern (seed=42), dungeon (seed=123), field (seed=456), boss (seed=789) — all 100 turns. Gate ENGINE-GOLD-MASTER-REGEN 10/10 (GM-01 through GM-10: 4 load + 4 replay + integrity + zero regressions). **PRIORITY: unblocks replay suite. No code changes.**
- **[ACCEPTED] [WO-ENGINE-READIED-ACTION-001_DISPATCH.md](pm_inbox/WO-ENGINE-READIED-ACTION-001_DISPATCH.md)** — Readied action (PHB p.160). Standard action that sets a trigger condition. New `ReadyActionIntent(actor_id, trigger_type, trigger_target_id, trigger_square, trigger_range_ft, readied_intent)`. Trigger types: `enemy_casts`, `enemy_enters_range`, `enemy_enters_square`. Storage: `WorldState.active_combat["readied_actions"]` list. New `aidm/core/readied_action_resolver.py`: `register_readied_action()`, `check_readied_triggers()`, `expire_readied_actions()`. Wired in `execute_turn()` at 3 points: expire at turn start, check triggers before intent dispatch, route `ReadyActionIntent`. New events: `readied_action_registered`, `readied_action_triggered`, `readied_action_expired`. Action economy: standard action slot. Deferred: initiative drop on fire, delay action, cross-round persistence. Gate ENGINE-READIED-ACTION 10/10 (RA-01 through RA-10).
- **[ACCEPTED] [WO-ENGINE-AID-ANOTHER-001_DISPATCH.md](pm_inbox/WO-ENGINE-AID-ANOTHER-001_DISPATCH.md)** — Aid Another (PHB p.154). Standard action. Helper rolls vs AC 10 (d20 + melee attack bonus). Success: ally gets +2 circumstance bonus to next attack vs enemy_id OR +2 AC vs enemy_id's next attack. Multiple helpers stack (explicit PHB exception to circumstance rule). New `AidAnotherIntent(actor_id, ally_id, enemy_id, aid_type: Literal["attack","ac"])`. Storage: `active_combat["aid_another_bonuses"]` list. New `aidm/core/aid_another_resolver.py`: `resolve_aid_another()`, `consume_aid_another_bonus()`, `expire_aid_another_bonuses()`. Consume called from `attack_resolver.py` when applying attack rolls and AC. Expire called at helper's next turn start. New events: `aid_another_success`, `aid_another_fail`, `aid_another_bonus_consumed`, `aid_another_bonus_expired`. Gate ENGINE-AID-ANOTHER 10/10 (AA-01 through AA-10).
- **[ACCEPTED] [WO-ENGINE-DEFEND-001_DISPATCH.md](pm_inbox/WO-ENGINE-DEFEND-001_DISPATCH.md)** — Fight Defensively + Total Defense (PHB p.142). Two standard-action defensive stances. `FightDefensivelyIntent`: −4 attack / +2 dodge AC (−5/+5 with Combat Expertise feat). `TotalDefenseIntent`: +4 dodge AC, no attacks. Both use `EF.TEMPORARY_MODIFIERS` dict pattern (keys: `fight_defensively_attack`, `fight_defensively_ac`, `total_defense_ac`) — same pattern as `charge_ac`. Cleared at actor's next turn start. Attack penalty applied in `attack_resolver.py` at roll; AC bonus applied at defender AC. New events: `fight_defensively_applied`, `total_defense_applied`, `fight_defensively_expired`, `total_defense_expired`. Gate ENGINE-DEFEND 10/10 (DF-01 through DF-10).
- **[ACCEPTED] [WO-ENGINE-FEINT-001_DISPATCH.md](pm_inbox/WO-ENGINE-FEINT-001_DISPATCH.md)** — Feint (PHB p.68/76). Standard action. `FeintIntent(actor_id, target_id)`. Bluff check (d20 + bluff_ranks + CHA_mod) vs Sense Motive (d20 + sense_motive_ranks + WIS_mod + BAB). Success: marker in `active_combat["feint_flat_footed"]` — consumed by feinting actor's first attack on target, or expires at feinting actor's next turn start. Denied-Dex path feeds existing sneak attack eligibility. New `aidm/core/feint_resolver.py`: `resolve_feint()`, `consume_feint_marker()`, `expire_feint_markers()`. `feint_invalid` if actor has 0 Bluff ranks. New events: `feint_success`, `feint_fail`, `feint_invalid`, `feint_bonus_consumed`, `feint_expired`. Gate ENGINE-FEINT 10/10 (FT-01 through FT-10).
- **[DISPATCH] [WO-UI-VISREG-PLAYWRIGHT-001_DISPATCH.md](pm_inbox/WO-UI-VISREG-PLAYWRIGHT-001_DISPATCH.md)** — Visual regression harness. Upgrades manual screenshot capture to `toHaveScreenshot()` baseline comparison. New `client/tests/playwright/visual-regression.spec.ts`: 4 posture snapshots (STANDARD/DOWN/LEAN_FORWARD/DICE_TRAY) + 2 vault state snapshots (REST/COMBAT), all at 1920×1080, `maxDiffPixels:200`. Two `package.json` scripts: `test:visreg` (CI-safe, no `--update-snapshots`) and `test:visreg:update` (operator-only baseline update). Snapshots committed to `client/tests/playwright/snapshots/`. Gate UI-VISREG-PLAYWRIGHT 10/10 (VR-01 through VR-10 — structural checks, no browser required). **Baseline commit BLOCKED on Thunder golden frame approval.** Sequencing: OPTICS ACCEPTED → QA-002 12/12 → Thunder approves → `npm run test:visreg:update` → baselines committed → `npm run test:visreg` PASS → unblocks GATES-V1.
- **[ACCEPTED] [WO-ENGINE-ABILITY-DAMAGE-001_DISPATCH.md](pm_inbox/WO-ENGINE-ABILITY-DAMAGE-001_DISPATCH.md)** — Ability damage + drain (PHB p.215). Adds 12 new EF fields (STR_DAMAGE/STR_DRAIN through CHA_DAMAGE/CHA_DRAIN). New `AbilityDamageIntent(actor_id, target_id, ability, amount, is_drain)`. New `aidm/core/ability_damage_resolver.py`: `get_effective_score()`, `get_ability_modifier()`, `apply_ability_damage()`, `heal_ability_damage()`, `expire_ability_damage_regen()`. Integration: attack_resolver (STR/DEX penalties), save_resolver (CON/DEX/WIS penalties), rest_resolver (1pt/ability heal), play_loop routing. CON to 0 = dead, STR/DEX to 0 = helpless. Gate ENGINE-ABILITY-DAMAGE 10/10 (AD-01 through AD-10).
- **[ACCEPTED] [WO-ENGINE-POISON-DISEASE-001_DISPATCH.md](pm_inbox/WO-ENGINE-POISON-DISEASE-001_DISPATCH.md)** — Poison + Disease (PHB p.292). Two-save poison: Fort vs DC at injury, secondary at round+10. Disease: incubation period, Fort save per interval, 2 consecutive saves = cured. New EF fields: `ACTIVE_POISONS`, `ACTIVE_DISEASES` (list of dicts). New `aidm/core/poison_disease_resolver.py`: `apply_poison()`, `process_poison_secondaries()`, `apply_disease_exposure()`, `process_disease_ticks()`, `is_immune_to_poison()`. Tick processing called at round end from play_loop. Gate ENGINE-POISON-DISEASE 10/10 (PD-01 through PD-10).
- **[ACCEPTED] [WO-ENGINE-WITHDRAW-DELAY-001_DISPATCH.md](pm_inbox/WO-ENGINE-WITHDRAW-DELAY-001_DISPATCH.md)** — Withdraw + Delay (PHB p.144/160). `WithdrawIntent`: full-round action, first-square AoO suppressed via `active_combat["withdrew_actors"]` set. `DelayIntent`: updates `initiative_scores` in world_state, actor acts at new (lower) count. New `aidm/core/withdraw_delay_resolver.py`. Gate ENGINE-WITHDRAW-DELAY 10/10 (WD-01 through WD-10).
- **[ACCEPTED] [WO-ENGINE-CONDITIONS-BLIND-DEAF-001_DISPATCH.md](pm_inbox/WO-ENGINE-CONDITIONS-BLIND-DEAF-001_DISPATCH.md)** — BLINDED, DEAFENED, ENTANGLED, CONFUSED added to ConditionType enum. BLINDED: 50% miss chance (d100 before d20), +2 attacker bonus, −2 AC. DEAFENED: 20% verbal spell failure. ENTANGLED: −2 attack, −4 DEX. CONFUSED: d100 behavior table each turn start (attack caster/act normally/babble/flee/attack nearest). New `aidm/core/condition_combat_resolver.py`. Integration: attack_resolver (blinded miss, entangled penalty), spell_resolver (deafened failure), play_loop (confusion turn-start hook), aoo.py (confused cannot trigger AoOs). Gate ENGINE-CONDITIONS-BLIND-DEAF 19/19 (BD-01 through BD-10, BD-09 parameterized expands to 10).
- **[ACCEPTED] [WO-ENGINE-SUNDER-DISARM-FULL-001_DISPATCH.md](pm_inbox/WO-ENGINE-SUNDER-DISARM-FULL-001_DISPATCH.md)** — Upgrades Sunder + Disarm from DEGRADED (narrative-only) to full persistent state. New EF fields: `WEAPON_HP`, `WEAPON_HP_MAX`, `WEAPON_BROKEN`, `WEAPON_DESTROYED`, `DISARMED`. Sunder: damage − hardness → WEAPON_HP; 0 HP = WEAPON_BROKEN (−2 attack penalty); −HP_MAX = WEAPON_DESTROYED. Disarm: success → target DISARMED; failure by 10+ → attacker DISARMED. DISARMED entity cannot make weapon attacks. Builder fix: SD-09 removed spurious name/attack_bonus fields from Weapon() constructor. Gate ENGINE-SUNDER-DISARM-FULL 10/10 (SD-01 through SD-10).

- **[ACCEPTED] [WO-UI-LAYOUT-PACK-V1_DISPATCH.md](pm_inbox/WO-UI-LAYOUT-PACK-V1_DISPATCH.md)** — Foundation WO. Creates `docs/design/LAYOUT_PACK_V1/` with zones.json (6 zones + anchors), camera_poses.json (5 postures, physically grounded), table_objects.json (7 objects). Wires runtime to load JSONs. Debug overlay draws zone bounds + anchors (?debug=1&zones=1). Removes orphan stub_parchment (hidden) and stray d6 stubs. Gate UI-LAYOUT-PACK 8/8. All subsequent WOs depend on this landing first.
- **[ACCEPTED] [WO-UI-CAMERAS-V1_DISPATCH.md](pm_inbox/WO-UI-CAMERAS-V1_DISPATCH.md)** — Gate UI-CAMERAS 6/6 PASS. camera.ts wired to camera_poses.json (Vite JSON import). Duration-based transitions: 350ms smoothstep, interruptible. `TRANSITION_MS` exported. Hardcoded POSTURES block removed. All 5 hotkeys (1-5) verified in main.ts. Golden frame capture pending Thunder browser session at 1920×1080.
- **[ACCEPTED] [WO-UI-OBJECT-LAYOUT-V1_DISPATCH.md](pm_inbox/WO-UI-OBJECT-LAYOUT-V1_DISPATCH.md)** — Gate UI-OBJECT-LAYOUT 10/10 PASS. Notebook geometry 1.4×0.08×1.9 (dominant footprint). Rulebook height 0.18. Orb idle emissive 0.08 (down from 0.3). `makeVaultTexture()`: dark green felt + faint 0.25-alpha grid. Vault cover plane (`vault_cover`, walnut, y=0.002, visible=true by default). Dice bag stub at `shelf_dice_bag` anchor. `vaultCoverMesh` exported; toggled on combat_start/combat_end and demo combat in main.ts.
- **[ACCEPTED] [WO-ENGINE-SPELL-SLOTS-001_DISPATCH.md](pm_inbox/WO-ENGINE-SPELL-SLOTS-001_DISPATCH.md)** — Gate ENGINE-SPELL-SLOTS 12/12 PASS. `_check_spell_slot()` + `_decrement_spell_slot()` + `_validate_spell_known()` helpers in play_loop.py. Slot check + known/prepared validation before SpellResolver call. Decrement on successful cast. `spell_slot_empty` event on depletion. Dual-caster fallback to SPELL_SLOTS_2. Cantrips exempt. `EF.SPELL_SLOTS_MAX` + `EF.SPELL_SLOTS_MAX_2` added to entity_fields.py. Set at chargen in `_merge_spellcasting()`. `rest_resolver.py` live (restores from MAX on overnight rest). CP23-08 regression fixed (entity helper now includes SPELL_SLOTS). Zero new regressions.
- **[ACCEPTED] [WO-ENGINE-REST-001_DISPATCH.md](pm_inbox/WO-ENGINE-REST-001_DISPATCH.md)** — Gate ENGINE-REST 12/12 PASS. `aidm/core/rest_resolver.py`: `resolve_rest()` + `RestResult` dataclass + `_restore_spell_slots()` + `_rest_narration()`. PHB p.130 3.5e rest: overnight/full_day = full slot recovery + natural HP healing (level × max(1,CON_mod)), fatigue/exhaustion cleared. Combat guard (rest_denied). Dual-caster: both SPELL_SLOTS + SPELL_SLOTS_2 restored. Prepared casters: SPELLS_PREPARED reset to SPELLS_KNOWN on rest. `RestIntent` routing wired in `execute_turn()`. Zero regressions.
- **[ACCEPTED] [WO-UI-LIGHTING-V1_DISPATCH.md](pm_inbox/WO-UI-LIGHTING-V1_DISPATCH.md)** — Gate UI-LIGHTING 6/6 PASS. `buildRoom()` added: back wall `PlaneGeometry(16,6)` at z=−8 (walnut), floor plane at y=−0.7. Scene background 0x08060a→0x100c0a (warm, not blue-black). Fog: near=16, far=26 (was 12/20). Walnut grain texture repeat 2×1.5→1×0.75 (grain now visible). Ambient: `0x1a1208, 0.55` (warm, removed purple cast). DM candle reduced `0x3344cc, 5` (was `0x4466ff, 8`). Map spot boosted: intensity=44, y=3.5. Parchment darkened `#b8a06a` (was #c8b483). Zero regressions. Room no longer floats in black void.
- **[ACCEPTED] [WO-UI-PHYSICALITY-BASELINE-V1_DISPATCH.md](pm_inbox/WO-UI-PHYSICALITY-BASELINE-V1_DISPATCH.md)** — Gate UI-PHYSICALITY-BASELINE 8/8 PASS. New `client/src/shelf-drag.ts`: `ShelfDragController`, lerp=0.18/frame, 8-frame settle half-life, hard SHELF_ZONE clamp (Math.max/min). Registered: characterSheetMesh, notebook.coverMesh, book.coverMesh, diceBag.bodyMesh. `register()` sets userData.draggable=true, userData.zone='SHELF_ZONE'. `shelfDrag.update(dt)` in animate loop. `notebookMesh`/`tomeMesh` exported from scene-builder.ts. `getZone` added to zones import in main.ts. 120/120 UI gates green. Zero regressions.
- **[ACCEPTED] [WO-ENGINE-COUP-DE-GRACE-001_DISPATCH.md](pm_inbox/WO-ENGINE-COUP-DE-GRACE-001_DISPATCH.md)** — Coup de grâce (PHB p.153). New `CoupDeGraceIntent` in `intents.py`. New `resolve_coup_de_grace()` + `apply_cdg_events()` in `attack_resolver.py`. Full-round action, auto-hit, auto-crit (×crit_multiplier all dice+bonuses), Fort save DC=10+damage or die (entity_defeated, HP=−10). New `EF.CRIT_IMMUNE` constant. Valid targets: DYING or has HELPLESS/UNCONSCIOUS/PINNED/PARALYZED condition. AoO provoked via existing `resolve_aoo_sequence()`. `_try_add()` mapping in `action_economy.py`. Gate ENGINE-COUP-DE-GRACE 10/10.
- **[ACCEPTED] [WO-ENGINE-CHARGE-001_DISPATCH.md](pm_inbox/WO-ENGINE-CHARGE-001_DISPATCH.md)** — Charge action (PHB p.154). `ChargeIntent` in `intents.py`, `resolve_charge()` + `apply_charge_events()` in `attack_resolver.py`. +2 attack bonus, −2 AC via `TEMPORARY_MODIFIERS["charge_ac"]` (cleared turn-start, emits `charge_ac_expired`). path_clear=False → intent_validation_failed. Spirited Charge ×2 mounted / ×3 with lance. AoO + concentration-break threading live. Gate ENGINE-CHARGE 10/10.
- **[ACCEPTED] [WO-ENGINE-TURN-UNDEAD-001_DISPATCH.md](pm_inbox/WO-ENGINE-TURN-UNDEAD-001_DISPATCH.md)** — Turn/rebuke undead (PHB p.159-161). `TurnUndeadIntent` in `intents.py`. `turn_undead_resolver.py`: `_get_cleric_level()` (paladin÷2), `_is_evil_cleric()`, `_roll_turning_check()` (2d6+level+CHA), `_roll_hp_budget()` (2d6×10), `_classify_target()` (immune/destroyed/commanded/turned/rebuked/unaffected), `resolve_turn_undead()`, `apply_turn_undead_events()`. `EF.TURN_UNDEAD_USES` / `EF.TURN_UNDEAD_USES_MAX` / `EF.IS_UNDEAD` added. `ConditionType.TURNED` + `create_turned_condition()` added. Rest restores uses. Gate ENGINE-TURN-UNDEAD 10/10.
- **[ACCEPTED] [WO-ENGINE-ENERGY-DRAIN-001_DISPATCH.md](pm_inbox/WO-ENGINE-ENERGY-DRAIN-001_DISPATCH.md)** — Energy drain / negative levels (PHB p.215-216). `EnergyDrainAttackIntent` in `attack.py`. `energy_drain_resolver.py`: `get_negative_level_attack_penalty()`, `get_negative_level_save_penalty()`, `_check_energy_drain_death()`, `_drain_spell_slot()`, `resolve_energy_drain()`, `apply_energy_drain_events()`. `EF.NEGATIVE_LEVELS` added. −1/level penalty wired into attack_resolver.py + all three save paths in play_loop.py. Drain death at negative_levels ≥ HD. Spell slot drain on each negative level. 24h permanent save deferred. Gate ENGINE-ENERGY-DRAIN 12/12 (10 spec + 2 builder bonus).
- **[ACCEPTED] [WO-ENGINE-DR-001_DISPATCH.md](pm_inbox/WO-ENGINE-DR-001_DISPATCH.md)** — Damage Reduction event surface + weapon bypass fix. `damage_reduction.py` already has `get_applicable_dr()` / `apply_dr_to_damage()` wired, but call sites don't pass weapon magic/material flags. New: `extract_weapon_bypass_flags()` helper reads `EF.WEAPON["tags"]`/`"material"`. New `damage_reduced` event when `dr_absorbed > 0`. `dr_absorbed` field added to `hp_changed` payload. `hp_changed` suppressed when DR reduces damage to 0. Gate ENGINE-DR 10/10.
- **[ACCEPTED] [WO-ENGINE-NONLETHAL-001_DISPATCH.md](pm_inbox/WO-ENGINE-NONLETHAL-001_DISPATCH.md)** — Nonlethal damage pool (PHB p.146). New `EF.NONLETHAL_DAMAGE` field. New `NonlethalAttackIntent` in `attack.py`. −4 attack penalty. Hit → damage to nonlethal pool (not HP). `check_nonlethal_threshold()` emits STAGGERED (nonlethal==HP) or UNCONSCIOUS (nonlethal>HP) conditions. `nonlethal_damage` event. HP heal re-checks threshold. Overnight rest clears nonlethal pool. Gate ENGINE-NONLETHAL 10/10.
- **[ACCEPTED] [WO-ENGINE-GRAPPLE-PIN-001_DISPATCH.md](pm_inbox/WO-ENGINE-GRAPPLE-PIN-001_DISPATCH.md)** — Gate ENGINE-GRAPPLE-PIN 10/10 PASS. Pinned condition escalation from grapple (PHB p.156). Second `GrappleIntent` against already-grappled target → `pin_established` on opposed check success. `PINNED` condition: helpless profile. `resolve_pin_escape()` + `PinEscapeIntent` wired. 7,099 passed, 25 pre-existing, zero new regressions.
- **[ACCEPTED] [WO-ENGINE-SPELL-PREP-001_DISPATCH.md](pm_inbox/WO-ENGINE-SPELL-PREP-001_DISPATCH.md)** — Gate ENGINE-SPELL-PREP 12/12 PASS. `PrepareSpellsIntent` + `spell_prep_resolver.py`. Slot count validation, spellbook membership check, spontaneous caster rejection. `use_secondary` for dual-caster. RNG-exempt. 7,099 passed, 25 pre-existing, zero new regressions.
- **[ACCEPTED] [WO-ENGINE-DEATH-DYING-001_DISPATCH.md](pm_inbox/WO-ENGINE-DEATH-DYING-001_DISPATCH.md)** — PHB p.145 death/dying/stabilization. Replaces instant `DEFEATED` on `hp≤0` with three bands: disabled (0 HP), dying (−1 to −9, bleed 1 HP/round, DC 10 Fort to stabilize), dead (−10+). New `aidm/core/dying_resolver.py`: `classify_hp()`, `resolve_hp_transition()`, `resolve_dying_tick()`. Three defeat call sites updated (attack_resolver, full_attack_resolver, play_loop spell path). End-of-round dying tick wired after `duration_tracker.tick_round()`. New event types: `entity_disabled`, `entity_dying`, `entity_stabilized`, `dying_fort_failed`, `entity_revived`. `entity_defeated` now means true death (HP ≤ −10) only. Gold masters require regeneration. Gate ENGINE-DEATH-DYING 12/12.
- **[ACCEPTED] [WO-ENGINE-CONCENTRATION-001_DISPATCH.md](pm_inbox/WO-ENGINE-CONCENTRATION-001_DISPATCH.md)** — Per-spell concentration break (3.5e PHB correct). `_check_concentration_break()` now iterates all active concentration effects, rolls DC=10+damage+spell_level per spell independently, drops only individually failing effects. Fixed pre-existing `spell_level` serialization bug in `ActiveSpellEffect.to_dict()/from_dict()`. New `remove_concentration_effect(effect_id)` on `DurationTracker`. Gate ENGINE-CONCENTRATION 10/10.
- **[DISPATCH] [WO-ENGINE-GRAPPLE-PIN-001_DISPATCH.md](pm_inbox/WO-ENGINE-GRAPPLE-PIN-001_DISPATCH.md)** — Pinned condition escalation from grapple (PHB p.156). `GrappleIntent` against already-grappled target → second opposed check → `pin_established` on success. `PINNED` condition type added to `conditions.py`. `create_pinned_condition()` factory: helpless profile (loses_dex, ac_melee=-4, auto_hit, actions_prohibited). `PinEscapeIntent` + `resolve_pin_escape()` in `maneuver_resolver.py`. `grapple_pairs` persists through pin. Gate ENGINE-GRAPPLE-PIN 10/10.
- **[DISPATCH] [WO-ENGINE-SPELL-PREP-001_DISPATCH.md](pm_inbox/WO-ENGINE-SPELL-PREP-001_DISPATCH.md)** — Spell preparation intent for prepared casters (PHB p.177-178). New `PrepareSpellsIntent(caster_id, preparation: Dict[int, List[str]])`. New `aidm/core/spell_prep_resolver.py`: `resolve_prepare_spells()` validates slot count limits and spellbook, applies to `SPELLS_PREPARED`. Spontaneous casters (bard, sorcerer) rejected. Same spell twice in same level allowed (PHB p.178). `use_secondary=True` for dual-caster secondary class prep. Uses no RNG (exempt from rng=None check). Wired in `execute_turn()`. Gate ENGINE-SPELL-PREP 12/12.
- **[DISPATCH] [WO-UI-CAMERA-OPTICS-001_DISPATCH.md](pm_inbox/WO-UI-CAMERA-OPTICS-001_DISPATCH.md)** — Per-posture optics. Extends `camera_poses.json` with `fov_deg`/`near`/`far` per posture. Extends `PostureConfig` interface. Wires `camera.ts` to apply optics on posture switch + lerp during transition + `updateProjectionMatrix()`. Debug overlay: `addCameraDebugHUD()` shows posture/pos/lookAt/fov/near/far/transit%. Adds `window.__cameraController__` in DEV mode. Optics: STANDARD 55°, DOWN 45°, LEAN_FORWARD 65° (fixes orb clip), DICE_TRAY 60°, BOOK_READ 40°. Gate UI-CAMERA-OPTICS 10/10. Must ACCEPT before WO-UI-VISUAL-QA-002.
- **[BLOCKED] [WO-UI-CAMERA-FRAMING-DICE-TRAY-FINAL_DISPATCH.md](pm_inbox/WO-UI-CAMERA-FRAMING-DICE-TRAY-FINAL_DISPATCH.md)** — DICE_TRAY posture orb exclusion fix. Blocked on WO-UI-CAMERA-OPTICS-001. JSON-only change to `camera_poses.json` DICE_TRAY entry (position/lookAt/fov_deg). Hard gate: orb 0% visible at 1920×1080 with 5% safe margin. Tower mouth in frame. Tray ≥ 40% width. Camera looking downward. Evidence: `dice_tray.png` + `dice_tray_debug.png` + runtime optics JSON + optional MP4. Gate UI-CAMERA-FRAMING-DICE-TRAY 5/5.
- **[DISPATCH] [WO-UI-VISUAL-QA-002_DISPATCH.md](pm_inbox/WO-UI-VISUAL-QA-002_DISPATCH.md)** — Composition lock + golden frame commit. Blocked on CAMERA-OPTICS-001. **Amended (×2):** (1) DICE_TRAY orb exclusion hard gate (0% visible, 5% safe margin). (2) Interaction clips §3.7 (4×10s MP4s: sheet/notebook/rulebook/dicebag drag + zone clamp — retroactive PHYSICALITY-BASELINE evidence). (3) Runtime optics dump values corrected to current camera_poses.json coordinates. **(3) Room geometry evidence pack §3.6:** ROOM_WIDE.png (STANDARD, debug ON, roomEnabled=true + object names in scene), scene_graph_dump.json (room_floor_present/room_back_wall_present/room_lights_present/postprocess booleans — all must be true), pixel-mass void check (>70% near-black = fail). (4) Commit hash + branch in README — mandatory, non-negotiable. Thunder reviews all 4 postures. After approval: commit 4 golden frames → unblocks WO-UI-GATES-V1. Gate UI-VISUAL-QA-002 **12/12** (QA2-11: room geometry not void, QA2-12: README has valid commit hash).
- **[DISPATCH] [WO-UI-GATES-V1_DISPATCH.md](pm_inbox/WO-UI-GATES-V1_DISPATCH.md)** — Depends on CAMERAS-V1 (needs golden frames). Three test suites: screenshot diff (pixelmatch 3% tolerance, 4 postures + 4 region assertions = 8 checks), zone parity (10 checks via ?dump=1), UI ban scan (9 static grep checks). Total gate UI-GATES 27/27. CI fails on any drift. Terminates the coordinate-thrash loop permanently.
- **[ACCEPTED] [WO-UI-VISUAL-QA-001_DISPATCH.md](pm_inbox/WO-UI-VISUAL-QA-001_DISPATCH.md)** — Visual self-inspection pass. 4 passes, 27 findings: P0×5 (STANDARD camera wrong, DOWN camera wrong, orb eye too low, felt vault always visible, player objects overlapping), P1×14, P2×5, Cosmetic×3. Root diagnosis: camera tuning by coordinate trial-and-error without physical grounding. Room floats in black void. Player shelf legibility poor. Findings brief: VISUAL_QA_FINDINGS_001.md. All findings addressed by the 6 LAYOUT PACK WOs above.
- **[ACCEPTED] [WO-ENGINE-GRAPPLE-001_DISPATCH.md](pm_inbox/WO-ENGINE-GRAPPLE-001_DISPATCH.md)** — Gate CP-22 14/14 PASS. Touch attack → opposed check (size mod) → `grappling`+`grappled` bidirectional. `GrappleEscapeIntent` + `resolve_grapple_escape()`. `GRAPPLING` condition type added. 5-foot step blocked while grappling in `play_loop.py`. `grapple_pairs` in `active_combat`.
- **[ACCEPTED] [WO-ENGINE-AOO-WIRE-001_DISPATCH.md](pm_inbox/WO-ENGINE-AOO-WIRE-001_DISPATCH.md)** — Gate CP-23 10/10 PASS. Ranged + spell AoO stubs → live in `aoo.py`. Concentration check (DC 10+dmg) + `spell_interrupted` wired in `execute_turn`. Quickened spells exempt.
- **[ACCEPTED] [WO-ENGINE-ACTION-ECON-001_DISPATCH.md](pm_inbox/WO-ENGINE-ACTION-ECON-001_DISPATCH.md)** — Gate CP-24 12/12 PASS. New `action_economy.py`: `ActionBudget` dataclass + `get_action_type()` mapper. Budget check at top of intent routing in `execute_turn`. `ACTION_DENIED` reason: action_economy. Full-round marks std+move. 5-foot step / move mutually exclusive. Gold masters regenerated 30/30.
- **[ACCEPTED] [WO-ENGINE-TWF-WIRE_DISPATCH.md](pm_inbox/WO-ENGINE-TWF-WIRE_DISPATCH.md)** — Gate CP-21 12/12 PASS. TWF detection, penalty table, off-hand attacks, Improved TWF second off-hand, half-STR off-hand damage in `full_attack_resolver.py`. Gold masters 34/34.
- **[ACCEPTED] [WO-ENGINE-LEVELUP-WIRE_DISPATCH.md](pm_inbox/WO-ENGINE-LEVELUP-WIRE_DISPATCH.md)** — Gate XP-01 19/19 PASS. `check_level_up()` live. `_award_xp_for_defeat()` wired. 6,905 passed, 0 new regressions.
- **[ACCEPTED] [WO-ENGINE-CONDITION-ENFORCE_DISPATCH.md](pm_inbox/WO-ENGINE-CONDITION-ENFORCE_DISPATCH.md)** — Gate CP-17 15/15 PASS. Helpless melee auto-hit + DEX stripping from AC in `attack_resolver.py`. ACTION_DENIED sensor event.
- **[ACCEPTED] [WO-ENGINE-CONDITION-SAVES_DISPATCH.md](pm_inbox/WO-ENGINE-CONDITION-SAVES_DISPATCH.md)** — Gate CP-18 10/10 PASS. Condition save modifiers (shaken, sickened, frightened) wired into `_resolve_save()` in `spell_resolver.py`.
- **[ACCEPTED] [WO-ENGINE-CONDITION-DURATION_DISPATCH.md](pm_inbox/WO-ENGINE-CONDITION-DURATION_DISPATCH.md)** — Gate CP-19 12/12 PASS. `DurationTracker.tick_round()` at end of last actor's turn in `play_loop.py`. Duplicate tick removed from `combat_controller.py`.
- **[ACCEPTED] [WO-UI-ANVIL-FULL-WORKLOAD_20260223.md](pm_inbox/WO-UI-ANVIL-FULL-WORKLOAD_20260223.md)** — Anvil 12 UI WOs: all gated (171 tests green), scene spatially correct. Visual QA complete. **9 gap WOs identified — all 12 gap+NS WOs now ACCEPTED.**
- **[ACCEPTED] [WO-UI-PORTRAIT-MESH-001_DISPATCH.md](pm_inbox/WO-UI-PORTRAIT-MESH-001_DISPATCH.md)** — Gate UI-CB-PORTRAIT 10/10 PASS. Inner `SphereGeometry(0.52)` inside outer orb. `crystalBallInnerMesh` exported. `CrystalBallController` second mesh param. Fade 0→1 on portrait, 1→0 on speaking stop.
- **[ACCEPTED] [WO-UI-SHEET-LIVE-001_DISPATCH.md](pm_inbox/WO-UI-SHEET-LIVE-001_DISPATCH.md)** — Gate UI-CS-LIVE 16/16 PASS. `characterSheetMesh` exported. Controller owns canvas/texture, `update()` calls `needsUpdate`. `onMeshClick()` emits REQUEST_DECLARE_ACTION.
- **[ACCEPTED] [WO-UI-NOTEBOOK-DRAW-WIRE-001_DISPATCH.md](pm_inbox/WO-UI-NOTEBOOK-DRAW-WIRE-001_DISPATCH.md)** — Gate UI-NB-DRAW 6/6 PASS. `pointerdown`/`pointermove`/`pointerup` on renderer.domElement. UV→canvas mapping. Section guard: only `notes` accepts strokes.
- **[ACCEPTED] [WO-UI-TOKEN-CHIP-001_DISPATCH.md](pm_inbox/WO-UI-TOKEN-CHIP-001_DISPATCH.md)** — Gate UI-TOKEN-CHIP 10/10 PASS. Flat 2D chips: `CircleGeometry(0.22,32)` + `rotation.x=-PI/2`. `MeshBasicMaterial` canvas texture: faction ring + HP arc + entity initial. HP bar mesh removed. UI-06 not regressed.
- **[ACCEPTED] [WO-UI-BESTIARY-IMAGE-001_DISPATCH.md](pm_inbox/WO-UI-BESTIARY-IMAGE-001_DISPATCH.md)** — Gate UI-BESTIARY-IMG 6/6 PASS. `image_url?: string` on BestiaryEntry. TextureLoader when present, procedural fallback when absent.
- **[ACCEPTED] [WO-UI-HANDOUT-READ-001_DISPATCH.md](pm_inbox/WO-UI-HANDOUT-READ-001_DISPATCH.md)** — Gate UI-HANDOUT-READ 4/4 PASS. Fullscreen HTML overlay. Fanstack click → REQUEST_HANDOUT_READ WS. `handout_display` → showHandoutOverlay(). Escape/click-outside dismisses.
- **[ACCEPTED] [WO-UI-FOG-FADE-001_DISPATCH.md](pm_inbox/WO-UI-FOG-FADE-001_DISPATCH.md)** — Gate UI-FOG-FADE 5/5 PASS. `FOG_FADE_DURATION_S = 0.3`. `fadingCells` map + `update(dt)` lerp. Called from main.ts render loop.
- **[ACCEPTED] [WO-UI-LASSO-FADE-001_DISPATCH.md](pm_inbox/WO-UI-LASSO-FADE-001_DISPATCH.md)** — Gate UI-LASSO-FADE 4/4 PASS. `FADE_MS = 200` wired to opacity animation. Lasso material `transparent: true`. Dispose after fade.
- **[ACCEPTED] [WO-UI-TOKEN-LABEL-001_DISPATCH.md](pm_inbox/WO-UI-TOKEN-LABEL-001_DISPATCH.md)** — Gate UI-TOKEN-LABEL bundled with TOKEN-CHIP PASS. `fillText` centered, 8-char truncation, bold 18px. Landed as part of TOKEN-CHIP-001 canvas draw.
- **[ACCEPTED] [WO-UI-SCENE-IMAGE-001_DISPATCH.md](pm_inbox/WO-UI-SCENE-IMAGE-001_DISPATCH.md)** — Gate UI-SCENE-IMG 6/6 PASS. `SceneImagePlane` (`PlaneGeometry(3.0,2.0)` flat at z=1.5). `scene_image` WS event → TextureLoader → fade in. Hides on combat_start, restores on combat_end.
- **[ACCEPTED] [WO-UI-TEXT-INPUT-001_DISPATCH.md](pm_inbox/WO-UI-TEXT-INPUT-001_DISPATCH.md)** — Gate UI-TEXT-INPUT 5/5 PASS. `#text-input-bar` always-on HTML overlay. Enter/Send → WS `player_input` → clear + blur.
- **[ACCEPTED] [WO-UI-FOG-VISION-001_DISPATCH.md](pm_inbox/WO-UI-FOG-VISION-001_DISPATCH.md)** — Gate UI-FOG-VISION 5/5 PASS. `VisionType` union (normal/low_light/darkvision). Darkvision: dark blue-gray tint `0x1a1a2e`. Low-light: 2× reveal radius. VISION_TYPE EF wired from entity_state.
- **[ACCEPTED] [WO-UI-TOOLING-VITEST-001_DISPATCH.md](pm_inbox/WO-UI-TOOLING-VITEST-001_DISPATCH.md)** — Gate TOOLS-VT 46/46.
- **[ACCEPTED] [WO-UI-TOOLING-PLAYWRIGHT-001_DISPATCH.md](pm_inbox/WO-UI-TOOLING-PLAYWRIGHT-001_DISPATCH.md)** — Gate TOOLS-PW 16/16.
- **[ACCEPTED] [WO-UI-TOOLING-DEBUG-OVERLAY-001_DISPATCH.md](pm_inbox/WO-UI-TOOLING-DEBUG-OVERLAY-001_DISPATCH.md)** — Gate TOOLS-DBG 9/9.
- **[ACCEPTED] [WO-WORLDGEN-INGESTION-001_DISPATCH.md](pm_inbox/WO-WORLDGEN-INGESTION-001_DISPATCH.md)** — Gate INGESTION 15/15. Step 1 of FINDING-WORLDGEN-IP-001 chain.
- **[READY] [WO-ENGINE-WILDSHAPE-HP-001_DISPATCH.md](pm_inbox/WO-ENGINE-WILDSHAPE-HP-001_DISPATCH.md)** — PHB delta HP formula for Wild Shape. `new_HP_MAX = saved_HP_MAX + (new_CON_mod − old_CON_mod) × druid_level`. Damage-taken offset preserved. 1 file (`wild_shape_resolver.py`) + tests. 10 gate tests. No schema change. Fixes FINDING-WILDSHAPE-HP-001 LOW.
- **[READY] [WO-ENGINE-WILDSHAPE-DURATION-001_DISPATCH.md](pm_inbox/WO-ENGINE-WILDSHAPE-DURATION-001_DISPATCH.md)** — Wild Shape auto-revert on duration expiry. `WILD_SHAPE_ROUNDS_REMAINING = druid_level × 10`. `tick_wild_shape_duration()` at round-end. 3 files (`entity_fields.py`, `wild_shape_resolver.py`, `play_loop.py`) + tests. 10 gate tests. Fixes FINDING-WILDSHAPE-DURATION-001 LOW.
- **[READ] [MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md](pm_inbox/MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md)** — TTS pipeline reference
- **[READ] [MEMO_BUILDER_PREFLIGHT_CANARY.md](pm_inbox/MEMO_BUILDER_PREFLIGHT_CANARY.md)** — Preflight canary system
- **[READ] [TUNING_001_PROTOCOL.md](pm_inbox/TUNING_001_PROTOCOL.md)** — TUNING-001 observation protocol
- **[READ] [TUNING_001_LEDGER.md](pm_inbox/TUNING_001_LEDGER.md)** — TUNING-001 session ledger

## WO Verdicts (most recent 15 — older entries archived)

| WO | Verdict | Commit |
|---|---|---|
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

## Dispatches (most recent 15 — older entries archived)

- ~~**ENGINE BATCH L — DISPATCHED (Dispatch #21, queued behind K)**~~ — Improved Disarm (play_loop.py) + Improved Grapple (play_loop.py) + Improved Bull Rush (play_loop.py) + Spell Penetration (save_resolver.py). 32 gate tests. Target ~1153. AoO suppression pattern for all 3 maneuver WOs; SP stacking: +2 base, +4 with Greater (not +6).
- ~~**ENGINE BATCH K — DISPATCHED (Dispatch #20, queued behind J)**~~ — Cowering/Fascinated + Diehard + Cleric Spontaneous + Improved Critical. 32 gate tests. Target ~1121. Coverage map WARNING live in dispatch.
- ~~**ENGINE BATCH J — DISPATCHED (Dispatch #19, in flight)**~~ — Immediate Action + Somatic Hand-Free + Skill Synergy + Run Action. 32 gate tests. Target ~1089.
- ~~**ENGINE BATCH I — ACCEPTED (Dispatch #18, commit f671cdb, 32/32, 0 regressions)**~~ — Staggered Action Economy (SA 8/8) + Concentration Vigorous (CV 8/8) + Dazzled Condition (DZ 8/8) + AoO Stand from Prone (AP 8/8). Archived to reviewed/.
- **[DISPATCHED] WO-ENGINE-GOLD-MASTER-REGEN** — Pre-existing replay drift: `dr_absorbed: 0 vs None` in tavern fixture (from WO-ENGINE-DR-001). Also death/dying event sequence changed in any fixture with HP≤0. Write `scripts/regen_gold_masters.py`: load JSONL → extract embedded scenario_config → `harness.record_gold_master(scenario, turns, seed)` → `harness.save_gold_master()`. 4 fixtures (tavern/dungeon/field/boss, all seed+100 turns). Gate ENGINE-GOLD-MASTER-REGEN 10 tests. No code changes — data-only regen. Priority: unblocks replay suite.
- **[DISPATCHED] WO-ENGINE-READIED-ACTION-001** — Readied action (PHB p.160). `ReadyActionIntent` (trigger_type: enemy_casts/enemy_enters_range/enemy_enters_square). `active_combat["readied_actions"]` queue. New `readied_action_resolver.py`: `register_readied_action()`, `check_readied_triggers()`, `expire_readied_actions()`. 3 wiring points in `execute_turn()`. 3 new event types. Standard action slot. Gate ENGINE-READIED-ACTION 10 tests.
- **[DISPATCHED] WO-ENGINE-AID-ANOTHER-001** — Aid Another (PHB p.154). `AidAnotherIntent(actor_id, ally_id, enemy_id, aid_type)`. Roll vs AC 10 → +2 circumstance bonus to ally attack or AC. Multi-helper stacking live. `active_combat["aid_another_bonuses"]` queue. New `aid_another_resolver.py`. Bonus consumed in `attack_resolver.py` on first matching roll/AC. Expire at helper's next turn start. 4 new event types. Standard action slot. Gate ENGINE-AID-ANOTHER 10 tests.
- **[DISPATCHED] WO-ENGINE-DEFEND-001** — Fight Defensively + Total Defense (PHB p.142). `FightDefensivelyIntent` / `TotalDefenseIntent`. Uses `EF.TEMPORARY_MODIFIERS` dict (keys: fight_defensively_attack/ac, total_defense_ac). Combat Expertise escalation (−5/+5). Cleared at turn start alongside charge_ac. Attack penalty applied in attack_resolver at roll. Dodge bonus applied at defender AC. 4 new event types. Both standard action. Gate ENGINE-DEFEND 10 tests.
- **[DISPATCHED] WO-ENGINE-FEINT-001** — Feint (PHB p.68/76). `FeintIntent(actor_id, target_id)`. Bluff (d20+ranks+CHA) vs Sense Motive+BAB (d20+ranks+WIS+BAB). Success marker in `active_combat["feint_flat_footed"]`. Consumed on attacker's next attack vs target. Expires at feinting actor's turn start. Denied-Dex path feeds existing sneak attack. `feint_invalid` guard (0 Bluff ranks). New `feint_resolver.py`. 5 new event types. Standard action. Gate ENGINE-FEINT 10 tests.
- **[DISPATCHED] WO-UI-VISREG-PLAYWRIGHT-001** — Visual regression harness. New `visual-regression.spec.ts`: `toHaveScreenshot()` for 4 postures + 2 vault states at 1920×1080, maxDiffPixels:200. `test:visreg` (CI-safe) + `test:visreg:update` (operator-only) in package.json. Snapshot dir: `client/tests/playwright/snapshots/`. Gate UI-VISREG-PLAYWRIGHT 10 tests (structural, no browser). Baseline commit BLOCKED on Thunder golden frame approval.

- **[DISPATCHED] WO-UI-CAMERA-OPTICS-001** — Per-posture optics: `fov_deg`/`near`/`far` in `camera_poses.json`. `camera.ts` applies + lerps optics per posture switch, calls `updateProjectionMatrix()`. Camera debug HUD overlay. LEAN_FORWARD FOV=65° eliminates orb clip. Gate UI-CAMERA-OPTICS 10 tests. Blocks QA-002.
- **[DISPATCHED] WO-UI-VISUAL-QA-002** — Blocked on CAMERA-OPTICS-001. Inspection Pack V2: 4×1080p PNGs, legibility crops, vault state, room geometry evidence pack (ROOM_WIDE.png debug-ON + scene_graph_dump.json with room boolean flags + pixel-mass void check), runtime optics dump, interaction clips (4×10s MP4s). Commit hash + branch in README mandatory. Thunder approves per-posture composition. Commits 4 golden frames. Unblocks GATES-V1. Gate UI-VISUAL-QA-002 **12 tests** (added QA2-11 room geometry + QA2-12 commit hash).
- ~~**WO-ENGINE-SPELL-SLOTS-001**~~ — **ACCEPTED**. 12/12 Gate ENGINE-SPELL-SLOTS. Slot governor live. Decrement on cast. spell_slot_empty event. Dual-caster fallback. SPELL_SLOTS_MAX set at chargen.
- ~~**WO-ENGINE-REST-001**~~ — **ACCEPTED**. 12/12 Gate ENGINE-REST. rest_resolver.py live. PHB 3.5e overnight/full_day rest. HP recovery + slot restore + condition clear. Combat guard. Dual-caster dual-pool.
- ~~WO-ENGINE-TWF-WIRE~~ — **ACCEPTED**. 12/12 Gate CP-21. TWF penalties + off-hand attacks + Improved TWF + half-STR damage. Gold masters 34/34.
- ~~WO-ENGINE-CONDITION-ENFORCE~~ — **ACCEPTED**. 15/15 Gate CP-17. Helpless auto-hit, DEX strip, ACTION_DENIED, prone-stand AoO.
- ~~WO-ENGINE-CONDITION-SAVES~~ — **ACCEPTED**. 10/10 Gate CP-18. Condition save penalties wired into SpellResolver.
- ~~WO-ENGINE-CONDITION-DURATION~~ — **ACCEPTED**. 12/12 Gate CP-19. tick_round() at round-end, condition_expired events, duplicate tick removed.
- **[DISPATCHED] WO-ENGINE-LEVELUP-WIRE** — XP award + level-up post-combat dispatcher. Complete `check_level_up()` stub in experience_resolver.py. `_award_xp_for_defeat()` helper called after entity_defeated events. `xp_awarded` + `level_up_applied` events. Gate XP-01 14 tests.
- **[DISPATCHED] WO-UI-ANVIL-FULL-WORKLOAD** — 12 UI WOs for Anvil: Tier 1 (crystal ball NPC portrait + TTS pulse, battle scroll unroll, character sheet interactive). Tier 2 (fog of war, dice bag, token slide animation, session zero flow, notebook stroke persistence). Tier 3 (settings gem, map lasso, cup holder, bestiary bind, rulebook search). Total 76 tests across 12 gates. Prerequisite: visual confirm spatial fix (book/notebook flat on shelf).
- **[DISPATCHED] WO-UI-06** — WebSocket → Three.js live entity tokens. `EntityRenderer` class. `entity_state` + `entity_delta` message handlers. Faction-colored cylinder tokens + HP bar (green→red lerp). `gridToScene()` coordinate transform (1 grid = 0.5 scene units). Gate UI-06 10 tests. Visual gate: Thunder opens browser.
- **[DISPATCHED] WO-CHARGEN-PHASE3-LEVELUP** — Level-up delta function. `level_up(entity, class_name, new_class_level)` pure function → delta dict. `CLASS_FEATURES` table (11 classes, PHB L1-20). HP roll (seeded RNG, min 1, max on first class level). Feat slot trigger. Skill points. Gate V9 15 tests. Appended to builder.py, no existing functions touched.
- **[DISPATCHED] WO-FIX-GRAMMAR-01** — Condition display title-case. `replace('_', ' ')` → `replace('_', ' ').title()` in play_loop.py. 1–2 regression tests appended to Gate K. FINDING-GRAMMAR-01 closed on completion.
- **[DISPATCHED] WO-BURST-003-AOE-001** — AoE confirm-gated overlay. `PendingAoE` frozen dataclass on `WorldState`. ASCII preview (`@`=origin, `*`=AoE, `!`=entity-in-AoE). Parser intercepts yes/cancel. Sensor events: AOE_PREVIEW_CONFIRMED / AOE_PREVIEW_CANCELLED. 10 tests. Gate: BURST-003 (new gate).
- **[DISPATCHED] WO-BURST-002-RESEARCH-001** — Spark runtime constraint envelope. `SparkFailureMode` enum (6 modes), `SPARK_SLA_PER_CALL` constants per CallType, `TEMPLATE_NARRATION` deterministic fallback, TTFT measurement in `SparkAdapter.generate()`, prep pipeline asset-level catch. 12 tests.
- **[DISPATCHED] WO-FIX-HOOLIGAN-03** — RV-001 compound narration fix. Scope `_check_rv001_hit_miss()` to first sentence via `. ` split. Gate K 67→70 on acceptance. FINDING-HOOLIGAN-03 closed on completion.
- ~~WO-BURST-003-AOE-001~~ — **ACCEPTED**. 10/10 Gate BURST-003. PendingAoE, ASCII overlay, confirm-gated parser.
- ~~WO-BURST-002-RESEARCH-001~~ — **ACCEPTED**. 12/12 Gate BURST-002. SparkFailureMode, SLA constants, template fallback, TTFT.
- ~~WO-FIX-GRAMMAR-01~~ — **ACCEPTED**. Gate K 69/69. `play.py:647` title-case fix. BL fixed.
- ~~WO-CHARGEN-MULTICLASS-001~~ — **ACCEPTED**. Gate V8 15/15. `class_mix` param. BAB/saves/HP/skills/class-skills all correct. Multi-caster: first caster wins (deferred dual-merge). Zero regressions.
- ~~WO-CHARGEN-EQUIPMENT-001~~ — **ACCEPTED**. Gate V7 73/73. Inventory, weapon, real AC, encumbrance. All 11 classes. Monk WIS-to-AC. W-15 X-01 gap resolved.
- ~~WO-UI-05~~ — **ACCEPTED pending visual**. scene-builder.ts: walnut + felt + candlelight + stubs. Math.random → seeded PRNG. Gate G 22/22. W-01–W-14 PASS. Visual gate: Thunder opens browser.
- ~~WO-PRS-ORCHESTRATOR-001~~ — **ACCEPTED**. `build_release_candidate_packet.py` + `known_failures.txt`. P2 6448 PASS. P8 292 violations (now fixed). P1 dirty (pre-commit).
- ~~WO-BURST-001-PLAYTEST-V1~~ — **ACCEPTED** (playtest report). 30/30 CP, 10/10 M, 5/5 B. **BURST-001 COMPLETE.**
- ~~WO-PRS-SCAN-FIX-001~~ — **ACCEPTED**. Gate X 8→9/10. X-04 fixed (base64 skip + jsonl allowlist). X-01 = real artifacts.
- ~~WO-PRS-SCAN-001~~ — **ACCEPTED w/ finding**. Gate X 8/10. FINDING-SCAN-BASELINE-01.
- ~~WO-PRS-LICENSE-001~~ — **ACCEPTED**. Gate Y 6/6. 13 deps, all permissive.
- ~~WO-PRS-OFFLINE-001~~ — **ACCEPTED** (`b037df3`). Gate Z 7/7. Static + runtime offline enforcement.
- ~~WO-PRS-FIRSTRUN-001~~ — **ACCEPTED** (`3c6dac2`). Gate AA 7/7. Fail-closed validation.
- ~~WO-PRS-DOCS-001~~ — **ACCEPTED**. Gate AB 6/6. PRIVACY.md + OGL_NOTICE.md + validator + tests.
- ~~WO-CHARGEN-BUILDER-001~~ — **ACCEPTED** (`54a1639`). 25 Gate V6. `build_character()` capstone. **CHARGEN PHASE 1 COMPLETE.**
- ~~WO-CHARGEN-SPELL-EXPANSION~~ — **ACCEPTED** (`60544a1`). 8 Gate V5. 28 spells L6-9.
- ~~WO-CHARGEN-SPELLCASTING~~ — **ACCEPTED** (`fd82578`). 15 Gate V4. Spell tables + class lists.
- ~~WO-CHARGEN-FEATS-COMPLETE~~ — **ACCEPTED** (`5014834`). 15 Gate V3. 66 PHB feats.
- ~~WO-CHARGEN-CLASSES-COMPLETE~~ — **ACCEPTED** (`335e404`). 12 Gate V2. 11 PHB classes.
- ~~WO-IMPL-PRESSURE-ALERTS-001~~ — ACCEPTED (`83f1674`). 22 Gate V. **TIER 4.3 COMPLETE.**
- ~~WO-IMPL-SALIENCE-FILTER-001~~ — ACCEPTED (`a3d06d3`). 14 Gate W. **TIER 4.4 COMPLETE. TIER 4 COMPLETE.**
- ~~WO-VOICE-PAS-PRESETS-001~~ — ACCEPTED (`bb93890`). 23 Gate T. **TIER 4.2 COMPLETE.**
- ~~WO-CHARGEN-FOUNDATION-001~~ — ACCEPTED (`90c204e`). 20 Gate U. **CHARGEN FOUNDATION COMPLETE.**

**Full dispatch history:** `reviewed/BRIEFING_ARCHIVE_GRADUATION_20260222.md` (14 older entries + H1+Smoke batch archived)

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
- [README.md](pm_inbox/README.md) — Inbox hygiene rules
- [WO_SET_ENGINE_BATCH_P.md](pm_inbox/WO_SET_ENGINE_BATCH_P.md) — **ACTIVE DISPATCH** — PA/IMB/PS/IDC (32 gate tests). Prereq: Batch O ACCEPTED ✓
- [WO_SET_OSS_DATA_BATCH_B.md](pm_inbox/WO_SET_OSS_DATA_BATCH_B.md) — **DATA BATCH B IN FLIGHT** — WO-DATA-MONSTERS-001 + WO-INFRA-DICE-001
- [WO-DATA-MONSTERS-001_DISPATCH.md](pm_inbox/WO-DATA-MONSTERS-001_DISPATCH.md) — Data WO (deferred)
- [WO-INFRA-DICE-001_DISPATCH.md](pm_inbox/WO-INFRA-DICE-001_DISPATCH.md) — Infra WO (deferred)
- [WO-ENGINE-MASSIVE-DAMAGE-001_DISPATCH.md](pm_inbox/WO-ENGINE-MASSIVE-DAMAGE-001_DISPATCH.md) — Batch N WO1 spec ref (SAI — accepted 7638473)
- [WO-ENGINE-STABILIZE-ALLY-001_DISPATCH.md](pm_inbox/WO-ENGINE-STABILIZE-ALLY-001_DISPATCH.md) — Batch N WO2 spec ref (SAI — accepted 7638473)
- [BURST_INTAKE_QUEUE.md](pm_inbox/BURST_INTAKE_QUEUE.md) — Research parking lot (Thunder to call)
- [PROBE-JUDGMENT-LAYER-001.md](pm_inbox/PROBE-JUDGMENT-LAYER-001.md) — Judgment layer probe (Thunder to call)
- *Batch N (7638473) — ACCEPTED (40/40) — dispatch archived to reviewed/*
- *Batch O (3232b76–99d79af) — ACCEPTED (32/32) — dispatch archived to reviewed/*
- *Batch M–L/K/J/I (prior) — all ACCEPTED — archived to reviewed/*
- [PROBE-WORLDMODEL-001.md](pm_inbox/PROBE-WORLDMODEL-001.md) — World model gap probe (Thunder to call)
- [PROBE-WORKER-TREATMENT-001.md](pm_inbox/PROBE-WORKER-TREATMENT-001.md) — (Thunder to call)
- [PROBE-JUDGMENT-LAYER-001.md](pm_inbox/PROBE-JUDGMENT-LAYER-001.md) — (Thunder to call)

**Archived 2026-02-26:** DISPATCH_14/15/17, Batch E–H WO dispatches, WSM_01_WATCH_SYNC, WO-PRS-IP-001, WO-ENGINE-BARDIC-DURATION-001, WO-UI-CAMERA-FRAMING, WO-UI-GATES-V1, WO-UI-VISREG-PLAYWRIGHT → `reviewed/`.

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
