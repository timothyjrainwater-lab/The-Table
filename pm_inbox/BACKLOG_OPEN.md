# BACKLOG — Open Findings Awaiting Triage

**Lifecycle:** ACTIVE (permanent file — not subject to inbox cap or archival)
**Last triaged:** 2026-02-28 (session 22) — Batch AF ACCEPTED. MONK-UNARMED-ATTACK-WIRE-001 CLOSED (WO2). 1 new LOW finding filed (FINDING-ENGINE-CONDITIONS-LEGACY-FORMAT-001). 0 promotions outstanding. Next triage due after AG + 2 batches (every 3 batches).
**Triage cadence:** Every 3 engine batches, PM reviews this file. For each finding: promote to WO, explicitly defer with rationale, or close. No new batch dispatch without backlog review.

---

## Triage Rules

- **HIGH:** Must have a WO filed or explicit Thunder deferral within 2 batches
- **MEDIUM:** Must be triaged (WO, defer, or close) within 3 batches
- **LOW:** Review every 5 batches; close if superseded or no longer relevant
- **IN FLIGHT:** Finding has a WO dispatched or in a batch — monitor, do not re-dispatch
- When promoting to WO: remove from this file, reference the WO ID in Triage Log below
- When deferring: add `DEFERRED` status and move to Deferred section below

---

## HIGH Severity

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| GAP-B | llama-cpp-python / VS Build Tools — infra blocker | Pre-batch | DEFERRED — not current engine blocker; revisit when TTS/audio work resumes |
| FINDING-WORLDGEN-IP-001 | IP strip pipeline: ingestion complete, double audit + strip + scan gate not built | Pre-batch | DEFERRED — RC ships stub mode; future milestone per kernel |
| FINDING-AUDIT-SPELL-002 | save_resolver.get_save_bonus() likely double-counts ability modifier — chargen writes class_base+ability_mod into EF.SAVE_*, save_resolver adds ability_mod again. Affects ALL non-spell saves. | Spellcasting audit | **CLOSED** — Batch Z WO2 (37a51ed). ability_mod stripped from save_resolver. Type 2 contract enforced. |
| FINDING-PATTERN-FIELD-CONTRACT-UNDEFINED-001 | No declared contract for composite EF fields. Root cause of save double/under-count. Chargen and resolvers make independent assumptions about field contents. | Probe memo | ACTIONED — Thunder ruled: typed contract policy (3 types). SPEC-COMPUTED-FIELD-CONTRACT-001 in draft. |

---

## MEDIUM Severity

### Engine — Existing

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-PLAYTEST-F01 | TTS env not provisioned — live audio deferred | Pre-batch | DEFERRED |
| FINDING-NS-AUDIT-001 | North Star audit — GATES-V1 pending golden frames | Pre-batch | DEFERRED |
| FINDING-ENGINE-EXHAUSTED-CONDITION-GAP-001 | Exhaustion check uses `"exhausted" in EF.CONDITIONS` dict key — works but no formal exhaustion condition definition in schemas/conditions.py | Batch Y debrief | **CLOSED** — ML-003 confirmed formal definition EXISTS at conditions.py:41, create_exhausted_condition() at lines 535-551. Dual-track gap (EF.FATIGUED boolean vs ConditionInstance) captured separately as FINDING-AUDIT-CONDITIONS-001 (AUDIT-WO-010). |
| FINDING-ENGINE-SPONTANEOUS-ALIGNMENT-001 | Cleric spontaneous cure redirect: no alignment check — evil clerics can cast cure spells | Coverage map sync 2026-02-27 | **CLOSED** — Batch AD WO3 (0275dea). Evil Cleric inflict swap implemented with alignment guard. |
| FINDING-ENGINE-SPELL-RESOLVER-SAVE-BYPASS-001 | `spell_resolver._resolve_save()` bypasses canonical `save_resolver.resolve_save()` — spell saves miss all global save features (racial bonuses, Divine Grace, Great Fortitude, save_descriptor threading). Shadow path established by original spell resolver architecture. | Batch AD debrief (WO1) | **CLOSED** — Batch AE WO1 (ab44488). play_loop.py:274 wires save_descriptor="spell"; routes through save_resolver. Dwarf/halfling racial bonuses now fire for zero-school spells. |
| FINDING-AUDIT-CONDITIONS-002 | `poison_disease_resolver.py` double-counts CON modifier on poison Fort saves — same Type 2 field contract violation as Batch Z save_resolver fix. EF.SAVE_FORT already stores base+CON; resolver adds CON again. Flagged by AUDIT-WO-010. | Conditions audit (AUDIT-WO-010) | **CLOSED** — Batch AE WO1 (ab44488). CON double-count stripped at 4 call sites in poison_disease_resolver.py. Type 2 field contract enforced. |
| FINDING-AUDIT-CONDITIONS-001 | Rage fatigue dual-track: charge/run blocks work (play_loop checks EF.FATIGUED), but Fort/Ref save penalties are silent for post-rage fatigued characters. EF.FATIGUED boolean never propagates to save_resolver. KERNEL-02 violation (two systems for same mechanic). | Conditions audit (AUDIT-WO-010) | **CLOSED** — Batch AE WO2 (ab44488). save_resolver.py: EF.FATIGUED=True → -2 Ref penalty. Direct boolean check. Ref only (not Fort/Will). |
| FINDING-AUDIT-CONDITIONS-003 | Aura of Courage fear immunity fires at paladin L2 instead of L3 — off-by-one on level threshold. PHB p.49: Aura of Courage granted at 3rd level. | Conditions audit (AUDIT-WO-010) | **CLOSED** — Batch AE WO3 (ab44488). builder.py both paths + save_resolver.py ally check: threshold L2→L3 per PHB p.49. |

### Engine — RAW Fidelity Audit

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-AUDIT-SPELL-001 | Spell saves bypass save_resolver — missing save feats, Divine Grace, Inspire Courage, halfling +1 all saves, dwarf +2 vs spells. TargetStats.get_save_bonus() returns raw EF.SAVE_* only. | Spellcasting audit | **CLOSED** — Batch Z WO4 (37a51ed). TargetStats routes through save_resolver. Shadow path eliminated. |
| FINDING-ENGINE-CONCENTRATION-BONUS-UNWRITTEN-001 | EF.CONCENTRATION_BONUS never written at chargen. All casters have 0 concentration bonus. Defensive casting, grapple casting, damage concentration all broken. 4 read sites in play_loop.py. | Probe memo | **CLOSED** — Batch Z WO1 (37a51ed). Wired at builder.py:899/1150. 5 read sites confirmed. |
| FINDING-ENGINE-MANEUVER-BAB-SHADOW-001 | maneuver_resolver._get_bab() reads EF.ATTACK_BONUS (BAB+STR composite) as BAB proxy. Maneuver opposed checks add STR separately → potential double-count on grapple/bull rush. | Probe memo | **CLOSED** — Batch Z WO3 (37a51ed). _get_bab() → EF.BAB only. 11 call sites verified. |
| FINDING-ENGINE-MANEUVER-ATTACK-REPLACEMENT-001 | Trip/Disarm/Sunder as attack replacement in full attack not modeled | RAW audit | DEFERRED — complex architecture; needs design session |
| FINDING-ENGINE-RAGE-DURATION-PRECON-001 | Barbarian rage duration uses pre-rage CON (may be correct per RAW — verify) | RAW audit | DEFERRED — pending PHB verification |
| FINDING-AUDIT-SAVE-001 | Coup de grace reads raw `EF.SAVE_FORT` at attack_resolver.py:1793, bypasses `get_save_bonus()` entirely — misses Great Fortitude, Divine Grace, Inspire Courage, all racial save bonuses | Save audit (AUDIT-WO-009) | **CLOSED** — Save Fix WO2 (f58411c). CdG routes through get_save_bonus(). Nat1/nat20 added. |
| FINDING-AUDIT-SAVE-002 | Multiclass save computation uses `max()` not `sum()` per PHB p.22 at builder.py:455-457, 1574-1576 — systematically under-counts multiclass character saves | Save audit (AUDIT-WO-009) | **CLOSED** — Save Fix WO1 (f58411c). max()→sum() at all 4 sites. |
| FINDING-AUDIT-SAVE-003 | `resolve_save()` calls `get_save_bonus()` without `save_descriptor` or `school` — racial poison/spell/enchantment bonuses missed for all direct callers (save_resolver.py:315) | Save audit (AUDIT-WO-009) | **CLOSED** — Batch AD WO1 (0275dea). SaveContext extended with save_descriptor + school. resolve_save() now propagates full descriptor through get_save_bonus(). |

### Tooling / Infrastructure

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-INFRA-FEATS-COUNT-MISMATCH-001 | WO spec estimated ~221 feats; actual feats.json has 109. Gate threshold adjusted >= 100. Spec drafted against older/different source, or additional feats not yet ingested. | SQLite WO debrief | DEFERRED — informational; doesn't block engine correctness |
| FINDING-INFRA-SPELL-CLASS-ID-ABBREVIATIONS-001 | spells.json uses abbreviated class IDs (clr, drd, sor_wiz, brd, rgr, pal) — no canonical mapping table between abbreviations and full class names | SQLite WO debrief | DEFERRED — informational; doesn't block engine correctness |

---

## LOW Severity

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-ENGINE-LEVELUP-POOL-SYNC-001 | Level-up path does not apply barbarian DR pool effects | Batch S | OPEN |
| FINDING-SF-SAVE-BREAKDOWN-001 | Save breakdown not surfaced in narrative output | Batch A | OPEN |
| FINDING-ASF-ARCANE-CASTER-001 | _is_arcane whitelist needs ranger/paladin extension | Batch A | OPEN |
| FINDING-ENGINE-IMPROVED-OVERRUN-BONUS-001 | Improved Overrun +4 STR bonus — confirm all paths | Batch O | OPEN |
| FINDING-ENGINE-IMPROVED-TRIP-WEAPON-CONTEXT-001 | Free attack silently skipped if no weapon in TripIntent | Batch N | OPEN |
| FINDING-ENGINE-IDC-DEX-STRIPPED-001 | Attacker loses DEX to AC for counter-disarm — not implemented | Batch P | OPEN |
| FINDING-ENGINE-INA-NONSTANDARD-DIE-001 | Non-standard dice not in INA step table silently pass through | Batch T | OPEN |
| FINDING-FAGU-RSAWC-DEAD-CODE-001 | resolve_single_attack_with_critical() retained unused | Batch U | OPEN — future code cleanup batch |
| FINDING-ENGINE-PRECISE-SHOT-FEAT-RESOLVER-DEAD-CODE-001 | ignores_shooting_into_melee_penalty() dead code | Batch P | OPEN — future code cleanup batch |
| FINDING-ENGINE-CREATURE-SUBTYPES-REGISTRY-001 | creature_registry.py not populated with orc/goblinoid/kobold subtypes — subtype gates only testable via inline entity dicts | Batch W debrief | OPEN |
| FINDING-ENGINE-THROWN-WEAPON-CATALOG-001 | equipment_catalog.json has no `is_thrown: true` on thrown weapons — halfling ATTACK_BONUS_THROWN only testable via explicit Weapon construction | Batch W debrief | OPEN |
| FINDING-ENGINE-CL-SCALED-DAMAGE-MISSING-001 | No per-CL damage dice scaling in spell resolution — spells like fireball don't scale damage with CL | CL2 WO | OPEN |
| FINDING-ENGINE-CL-SCALED-DURATION-MISSING-001 | No per-CL duration scaling in spell resolution — buff/debuff durations don't scale with CL | CL2 WO | OPEN |
| FINDING-ENGINE-TRIP-FREE-ATTACK-UNARMED-001 | Trip free attack unarmed path missing | RAW audit | OPEN |
| FINDING-ENGINE-OVERRUN-DURING-MOVE-001 | Overrun during move (movement-embedded) not modeled | RAW audit | OPEN |
| FINDING-ENGINE-MD-INLINE-SAVE-PATTERN-001 | Massive damage uses inline Fort save (d20+bonus vs DC15) instead of resolve_save() — misses global save features | Batch X debrief | OPEN — confirmed by AUDIT-WO-009 and Batch AD WO1 debrief. MD calls get_save_bonus() (not a full shadow path), but bypasses resolve_save(). Minor gap only. |
| FINDING-ENGINE-SR-PLAY-LOOP-EVENTS-001 | play_loop.py may not emit resolution.sr_events to EventLog — SR events captured on SpellResolution but may not reach log | SR WO debrief | OPEN (confirmed by spellcasting audit) |
| FINDING-AUDIT-SPELL-006 | Empower+Maximize flagged incompatible in validate_metamagic() — PHB does not prohibit stacking (RAW deviation, community-disputed) | Spellcasting audit | OPEN |
| FINDING-ENGINE-POSITION-TUPLE-FORMAT-001 | Chargen stores position as tuple `(0,0)` but `_create_target_stats()` expects dict/Position — test workaround in place, should normalize at chargen | Batch Z debrief | OPEN |
| FINDING-ENGINE-NEGATIVE-LEVEL-SAVE-001 | Negative level penalty in TargetStats but not save_resolver — minor inconsistency, only affects spell target saves vs general saves | Batch Z debrief | OPEN — confirmed by AUDIT-WO-009 (FINDING-AUDIT-SAVE-006 is same gap) |
| FINDING-ENGINE-SPELL-DEF-DUPLICATE-ENTRIES-001 | `spell_definitions.py` contains duplicate dict keys (grease, stinking_cloud, likely others). Later compact entries from OSS data import overwrite earlier verbose entries. Both must be maintained or deduplicated. | Batch AA debrief | OPEN |
| FINDING-ENGINE-SPELL-DC-BASE-NO-WRITE-SITE-001 | `EF.SPELL_DC_BASE` has no chargen write site. Read at play_loop.py:222 with default 13. CONSUME_DEFERRED. | Batch AA debrief | OPEN |
| FINDING-AUDIT-SAVE-004 | Massive damage inline saves use `rng.stream("combat")` instead of `rng.stream("saves")` — RNG stream isolation violation | Save audit (AUDIT-WO-009) | OPEN |
| FINDING-AUDIT-SAVE-005 | `SaveContext` has no `save_descriptor` or `school` field — schema gap blocks fix for FINDING-AUDIT-SAVE-003 | Save audit (AUDIT-WO-009) | **CLOSED** — Batch AD WO1 (0275dea). SaveContext extended with save_descriptor and school fields. |
| FINDING-AUDIT-SAVE-006 | Negative level save penalty applied in `play_loop._create_target_stats()` after `get_save_bonus()` — split authority, penalty missed on non-TargetStats paths | Save audit (AUDIT-WO-009) | OPEN — confirms FINDING-ENGINE-NEGATIVE-LEVEL-SAVE-001 |
| FINDING-BARDIC-SAVE-SCOPE-001 | Inspire Courage applies to all saves — PHB p.29 limits to fear/charm saves only (save_resolver.py:117-123) | Save audit (AUDIT-WO-009) | **CLOSED** — Batch AE WO3 (ab44488). save_resolver.py: Inspire Courage save bonus now gated on save_descriptor == "fear" or "charm". Attack/damage bonus unchanged. |
| FINDING-ENGINE-SCHOOL-PARAM-NON-SPELL-001 | `school` parameter in save_resolver only populated for spell saves — non-spell enchantment effects (gaze, supernatural) don't pass school, Still Mind/Indomitable Will won't fire for those paths | Batch AB debrief | **CLOSED** — Batch AD WO1 (0275dea). SaveContext school field now propagated across all save paths. |
| FINDING-ENGINE-KI-STRIKE-WILDSHAPE-001 | Monk in wild shape: does Ki Strike apply to natural attacks in animal form? PHB p.42 says "unarmed attacks" — ambiguous | Batch AB debrief | OPEN |
| FINDING-ENGINE-SAVE-DESCRIPTOR-PASS-001 | `SaveContext` has no `save_descriptor` field; `resolve_save()` cannot propagate fear/enchantment descriptor to `get_save_bonus()`. AoC full-path blocked. Same root as SAVE-003/SAVE-005/GNOME-ILLUSION/SCHOOL-PARAM. | Batch AC debrief | **CLOSED** — Batch AD WO1 (0275dea). SaveContext extended; AoC descriptor path wired. |
| FINDING-ENGINE-FLURRY-WEAPON-ID-FIELD-001 | `Weapon` dataclass has no `weapon_id` field; flurry monk-weapon check reads raw `EF.WEAPON` dict directly. Acceptable short-term. | Batch AC debrief | OPEN — future schema cleanup |
| FINDING-ENGINE-INSPIRE-GREATNESS-HD-001 | Inspire Greatness grants +2 temporary HD (HP pool + saves per bard level gating) — only the attack/save bonus was wired by WO4; temporary HD HP pool not implemented. PHB p.48. | Batch AD debrief (WO4) | OPEN — CONSUME_DEFERRED. Future WO needed for HD HP pool. |
| FINDING-ENGINE-TRAP-SENSE-AC-001 | Trap Sense provides +1 AC vs traps per 3 barb/rogue levels — the Ref save portion is wired (Batch AE WO4), but AC vs trap attacks is not implemented. No trap attack subsystem exists. | Batch AE WO4 | OPEN — CONSUME_DEFERRED. No trap attack subsystem. |
| FINDING-ENGINE-GNOME-ILLUSION-SAVE-001 | Gnome +2 vs illusion spells — SaveContext had no spell school field | Batch S | **CLOSED** — Batch AD WO1 (0275dea). SaveContext school field added; gnome illusion save bonus wired correctly. |
| FINDING-ENGINE-WS-SIZE-GATING-001 | Wild shape size gating absent | RAW audit | DEFERRED — architectural complexity; no current sprint |
| FINDING-ENGINE-PA-FULL-ATTACK-ROUND-LOCK-001 | PA penalty not enforced at round level — trusts caller | Batch P | DEFERRED |
| FINDING-ENGINE-GC-CHAIN-HP-MUTATION-001 | Great Cleave chain kills untestable without apply_attack_events() | Batch Q | DEFERRED — test harness gap, not runtime bug |
| FINDING-ENGINE-WF-SPECIFIC-WEAPON-001 | WF keyed on weapon_type, not specific weapon | Batch Q | DEFERRED — acceptable simplification |
| FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001 | EF.MONK_UNARMED_DICE set, resolver doesn't read it | Batch S | **CLOSED** — Batch AF WO2 (2edf076). attack_resolver.py reads MONK_UNARMED_DICE for unarmed monk strikes. Flurry path confirmed parity. |
| FINDING-ENGINE-CONDITIONS-LEGACY-FORMAT-001 | `get_condition_modifiers()` safety guard returns zero modifiers for legacy `["condition"]` list format — resolvers calling it will silently miss conditions stored in list format. DR flat-footed required explicit workaround. | Batch AF WO4 | OPEN — LOW. Foundational: affects any resolver reading condition modifiers. Future conditions cleanup WO. |
| FINDING-ENGINE-RACIAL-VISION-WRITE-ONLY-001 | low_light_vision + darkvision_range — no vision resolver | Opus audit | DEFERRED — no vision subsystem |
| FINDING-ENGINE-RACIAL-ILLUSION-WRITE-ONLY-001 | spell_resistance_illusion + illusion_dc_bonus — no illusion subsystem | Opus audit | DEFERRED — no illusion subsystem |
| FINDING-ENGINE-RACIAL-EXPLORATION-WRITE-ONLY-001 | stonecunning + automatic_search_doors — no exploration resolver | Opus audit | DEFERRED — no exploration subsystem |
| FINDING-ENGINE-IMPROVED-DISARM-COUNTER-SUPPRESS-001 | Improved Disarm counter suppression not in PHB | RAW audit | DEFERRED — remove per Thunder ruling (2026-02-27): not in PHB, not promoted to HOUSE_POLICY; add to future cleanup WO |
| FINDING-AUDIT-AE-003 | AoO round-reset in combat_controller, not execute_turn | AE audit | DEFERRED — test harness isolation gap, not production bug |
| FINDING-ENGINE-CONCENTRATION-ENTANGLED-001 | Concentration check for entangled condition unimplemented | Build plan | DEFERRED — no entangled condition resolver yet |

---

## Graduated (CLOSED) — Summary

59 findings closed and graduated from active tables (26 session 17 + 6 session 19 Batch Y + 4 session 20 Batch Z + 7 session 20 Batch AA + 1 session 20 Batch AB + 3 session 20 Save Fix + 6 session 20 Batch AD + 5 session 20 Batch AE + 1 session 22 Batch AF).

| ID | Closed By | Commit |
|----|-----------|--------|
| FINDING-COVERAGE-MAP-001 | Coverage map bulk sync | 2026-02-27 sync |
| FINDING-AUDIT-FAGU-001 | Batch U WO1 | a2dc1e6 |
| FINDING-AUDIT-TURN-CHECK-001 | Batch U WO2 | 03b45d4 |
| FINDING-AUDIT-SMITE-USES-001 | Batch U WO3 | 3c3404d |
| FINDING-AUDIT-AE-001 | Batch V WO2 | 3b8f774 |
| FINDING-AUDIT-AE-002 | Batch V WO1 | f2acd12 |
| FINDING-ENGINE-DOMAIN-SYSTEM-MISSING-001 | Batch V WO3 | 147219b |
| FINDING-ENGINE-PA-2H-PHB-DEVIATION-001 | WO-ENGINE-PA-2H-FIX-001 | 97f8351 |
| FINDING-DATA-EQUIPMENT-DEFS-DEAD-001 | WO-DATA-DEAD-FILES-CLEANUP-001 | 45a3e55 |
| FINDING-DATA-FEAT-DEFS-DEAD-001 | WO-DATA-DEAD-FILES-CLEANUP-001 | 45a3e55 |
| FINDING-DATA-CLASS-DEFS-DEAD-001 | WO-DATA-DEAD-FILES-CLEANUP-001 | 45a3e55 |
| FINDING-ENGINE-RACIAL-ENCHANTMENT-SAVE-001 | Batch W WO1 | 61e1da1 |
| FINDING-ENGINE-RACIAL-SLEEP-IMMUNITY-001 | Batch W WO1 | 61e1da1 |
| FINDING-ENGINE-RACIAL-SKILL-BONUS-001 | Batch W WO2 | fce3865 |
| FINDING-ENGINE-RACIAL-ATTACK-BONUS-001 | Batch W WO3 | eb625e4 |
| FINDING-ENGINE-RACIAL-DODGE-AC-001 | Batch W WO4 | f42e479 |
| FINDING-ENGINE-CASTER-LEVEL-2-WRITE-ONLY-001 | WO-ENGINE-CASTER-LEVEL-2-001 | 64bf5a5 |
| FINDING-ENGINE-UD-ROGUE-THRESHOLD-001 | Batch X WO1 | fd792d8 |
| FINDING-ENGINE-UD-RANGER-FALSE-001 | Batch X WO1 | fd792d8 |
| FINDING-ENGINE-FAST-MOVEMENT-MEDIUM-LOAD-001 | Batch X WO2 | d53c604 |
| FINDING-ENGINE-MD-NAT1-NAT20-001 | Batch X WO3 | d0a36ce |
| FINDING-ENGINE-FASCINATED-SKILL-PENALTY-001 | Batch X WO3 | d0a36ce |
| FINDING-ENGINE-FE-CRIT-MULTIPLIER-001 | Batch X WO4 | 9e36811 |
| FINDING-ENGINE-SECONDARY-STR-HALF-001 | Batch X WO4 | 9e36811 |
| FINDING-INFRA-DATA-CONSOLIDATION-001 | WO-INFRA-SQLITE-CONSOLIDATION-001 | 0ac1fda |
| FINDING-ENGINE-NAT-ATTACK-DELEGATION-PATH-001 | INFO closure | N/A |
| FINDING-ENGINE-SR-NOT-IN-SPELL-PATH-001 | WO-ENGINE-SR-SPELL-PATH-001 | 8cc96f8 |
| FINDING-ENGINE-RAGE-HP-ABSENT-001 | Batch Y WO1 | b8f7f50 |
| FINDING-ENGINE-RAGE-FATIGUE-MOBILITY-001 | Batch Y WO2 | b8f7f50 |
| FINDING-ENGINE-WS-USES-FORMULA-001 | Batch Y WO3 | b8f7f50 |
| FINDING-ENGINE-WS-UNLOCK-LEVEL-001 | Batch Y WO3 | b8f7f50 |
| FINDING-ENGINE-DISARM-SIZE-MODIFIER-001 | Batch Y WO4 | b8f7f50 |
| FINDING-ENGINE-COUNTER-DISARM-THRESHOLD-001 | Batch Y WO4 | b8f7f50 |
| FINDING-ENGINE-RAGE-GREATER-MIGHTY-001 | Batch AA WO1 | 0b7cbad |
| FINDING-ENGINE-TIRELESS-RAGE-001 | Batch AA WO1 | 0b7cbad |
| FINDING-ENGINE-DISARM-2H-ADVANTAGE-001 | Ghost — already at B-AMB-04 | N/A |
| FINDING-ENGINE-OVERRUN-FAILURE-PRONE-CHECK-001 | Batch AA WO4 | 0b7cbad |
| FINDING-AUDIT-SPELL-004 | Batch AA WO2 | 0b7cbad |
| FINDING-AUDIT-SPELL-005 | Batch AA WO3 | 0b7cbad |
| FINDING-AUDIT-SPELL-007 | Batch AA WO3 | 0b7cbad |
| FINDING-ENGINE-PALADIN-POISON-IMMUNITY-BUG-001 | Batch AB WO2 | 3ec541b |
| FINDING-AUDIT-SAVE-001 | Save Fix WO2 | f58411c |
| FINDING-AUDIT-SAVE-002 | Save Fix WO1 | f58411c |
| FINDING-AUDIT-SAVE-007 | Save Fix WO1 | f58411c |
| FINDING-ENGINE-CDG-NAT1-NAT20-MISSING-001 | Save Fix WO2 | f58411c |
| FINDING-AUDIT-SAVE-003 | Batch AD WO1 | 0275dea |
| FINDING-AUDIT-SAVE-005 | Batch AD WO1 | 0275dea |
| FINDING-ENGINE-GNOME-ILLUSION-SAVE-001 | Batch AD WO1 | 0275dea |
| FINDING-ENGINE-SCHOOL-PARAM-NON-SPELL-001 | Batch AD WO1 | 0275dea |
| FINDING-ENGINE-SAVE-DESCRIPTOR-PASS-001 | Batch AD WO1 | 0275dea |
| FINDING-ENGINE-SPONTANEOUS-ALIGNMENT-001 | Batch AD WO3 | 0275dea |
| FINDING-ENGINE-SPELL-RESOLVER-SAVE-BYPASS-001 | Batch AE WO1 | ab44488 |
| FINDING-AUDIT-CONDITIONS-002 | Batch AE WO1 | ab44488 |
| FINDING-AUDIT-CONDITIONS-001 | Batch AE WO2 | ab44488 |
| FINDING-AUDIT-CONDITIONS-003 | Batch AE WO3 | ab44488 |
| FINDING-BARDIC-SAVE-SCOPE-001 | Batch AE WO3 | ab44488 |

---

## Deferred (explicitly parked with rationale)

| ID | Rationale |
|----|-----------|
| GAP-B | Not current engine correctness blocker. Revisit when TTS/audio work resumes. |
| FINDING-WORLDGEN-IP-001 | RC ships stub mode. Future milestone per kernel architectural invariant. |
| FINDING-PLAYTEST-F01 | Infrastructure gap, not engine correctness. Deferred until TTS provisioning. |
| FINDING-NS-AUDIT-001 | Golden frames for GATES-V1 not defined. Cannot audit toward undefined targets. |
| FINDING-ENGINE-MANEUVER-ATTACK-REPLACEMENT-001 | Complex architectural feature requiring action economy integration. Needs design session. |
| FINDING-ENGINE-RAGE-DURATION-PRECON-001 | Pending PHB p.27 verification — pre-rage CON for duration may be correct per RAW. |
| FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001 | No attack resolver consumption planned for current sprint. |
| FINDING-ENGINE-RACIAL-VISION-WRITE-ONLY-001 | No vision resolver subsystem exists. |
| FINDING-ENGINE-RACIAL-ILLUSION-WRITE-ONLY-001 | No illusion subsystem exists. |
| FINDING-ENGINE-RACIAL-EXPLORATION-WRITE-ONLY-001 | No exploration resolver subsystem exists. |
| FINDING-ENGINE-GC-CHAIN-HP-MUTATION-001 | Test harness architectural gap, not a runtime bug. |
| FINDING-ENGINE-WF-SPECIFIC-WEAPON-001 | Known simplification. Acceptable for current scope. |
| FINDING-ENGINE-PA-FULL-ATTACK-ROUND-LOCK-001 | Trust-caller pattern acceptable for current scope. |
| FINDING-ENGINE-IMPROVED-DISARM-COUNTER-SUPPRESS-001 | Not in PHB. Not promoted to HOUSE_POLICY. Thunder ruling: remove (2026-02-27). Add to future code cleanup WO. |
| FINDING-AUDIT-AE-003 | Test harness isolation gap, not production bug. |
| FINDING-ENGINE-CONCENTRATION-ENTANGLED-001 | No entangled condition resolver yet. |
| FINDING-ENGINE-WS-SIZE-GATING-001 | Architectural complexity, no current sprint. |
| FINDING-INFRA-FEATS-COUNT-MISMATCH-001 | Informational; doesn't block engine correctness. |
| FINDING-INFRA-SPELL-CLASS-ID-ABBREVIATIONS-001 | Informational; doesn't block engine correctness. |

---

## Triage Log

| Date | Action | Finding(s) | Outcome |
|------|--------|------------|---------|
| 2026-02-27 | Initial population | All above | Opus cross-layer audit populated backlog |
| 2026-02-27 | Batch U ACCEPTED | FINDING-AUDIT-FAGU-001, FINDING-AUDIT-TURN-CHECK-001, FINDING-AUDIT-SMITE-USES-001 | All 3 HIGH CLOSED. Commits a2dc1e6/03b45d4/3c3404d. |
| 2026-02-27 | Thunder ruling | FINDING-ENGINE-PA-2H-PHB-DEVIATION-001 | 2× per PHB p.98. IN FLIGHT. |
| 2026-02-27 | Option B decision | FINDING-DATA-*-DEAD-001 (3) | Delete + document. WO-DATA-DEAD-FILES-CLEANUP-001 IN FLIGHT. |
| 2026-02-27 | New LOW filed | FINDING-FAGU-RSAWC-DEAD-CODE-001 | From Batch U debrief. |
| 2026-02-27 | Coverage map sync | FINDING-ENGINE-SPONTANEOUS-ALIGNMENT-001 | New LOW filed — no alignment guard on cleric spontaneous cure redirect |
| 2026-02-27 | Batch V + PA-2H + DDC ACCEPTED | FINDING-AUDIT-AE-001/002, FINDING-ENGINE-DOMAIN-SYSTEM-MISSING-001, FINDING-DATA-*-DEAD-001 (3), FINDING-ENGINE-PA-2H-PHB-DEVIATION-001 | 7 findings CLOSED. Commits 3b8f774/f2acd12/147219b/45a3e55/97f8351/9cdf009. 26/26 gates. |
| 2026-02-28 | Batch W dispatched (session 14) | FINDING-ENGINE-RACIAL-ENCHANTMENT-SAVE-001, FINDING-ENGINE-RACIAL-SKILL-BONUS-001, FINDING-ENGINE-RACIAL-SLEEP-IMMUNITY-001, FINDING-ENGINE-RACIAL-ATTACK-BONUS-001, FINDING-ENGINE-RACIAL-DODGE-AC-001 | All 5 IN FLIGHT via Batch W WO1–WO4. 32 gate tests expected. |
| 2026-02-28 | CL2 WO drafted + dispatched (session 14) | FINDING-ENGINE-CASTER-LEVEL-2-WRITE-ONLY-001 | IN FLIGHT — WO-ENGINE-CASTER-LEVEL-2-001 DISPATCH-READY. Dispatch after Batch W returns. 8 gate tests. |
| 2026-02-28 | Batch W ACCEPTED (session 15) | FINDING-ENGINE-RACIAL-ENCHANTMENT-SAVE-001, FINDING-ENGINE-RACIAL-SKILL-BONUS-001, FINDING-ENGINE-RACIAL-SLEEP-IMMUNITY-001, FINDING-ENGINE-RACIAL-ATTACK-BONUS-001, FINDING-ENGINE-RACIAL-DODGE-AC-001 | All 5 CLOSED. Commits 61e1da1/fce3865/eb625e4/f42e479. 32/32 gates. PM notes: 3 documentation gaps noted (no functional failures). CL2 dispatched. |
| 2026-02-28 | Batch W debrief new findings (session 15) | FINDING-ENGINE-CREATURE-SUBTYPES-REGISTRY-001, FINDING-ENGINE-THROWN-WEAPON-CATALOG-001 | 2 new LOW filed. creature_registry.py not populated; thrown weapons not tagged in catalog. |
| 2026-02-28 | CL2 ACCEPTED (session 15) | FINDING-ENGINE-CASTER-LEVEL-2-WRITE-ONLY-001 | CLOSED. Commits 64bf5a5/bc12ab5/ab1887b. 8/8 gates. SAI — implementation pre-dated dispatch. 3 new findings filed (1 MEDIUM, 2 LOW). |
| 2026-02-28 | Anvil data consolidation proposal (session 15) | FINDING-INFRA-DATA-CONSOLIDATION-001 | New MEDIUM filed. Promote to WO-INFRA-SQLITE-CONSOLIDATION-001. Parallel-safe with Batch X (zero resolver overlap). |
| 2026-02-28 | Batch X dispatched (session 15) | FINDING-ENGINE-UD-*-001 (2), FINDING-ENGINE-FAST-MOVEMENT-MEDIUM-LOAD-001, FINDING-ENGINE-MD-NAT1-NAT20-001, FINDING-ENGINE-FASCINATED-SKILL-PENALTY-001, FINDING-ENGINE-FE-CRIT-MULTIPLIER-001, FINDING-ENGINE-SECONDARY-STR-HALF-001 | All 7 IN FLIGHT via Batch X WO1–WO4. 32 gate tests expected. |
| 2026-02-28 | SQLite WO dispatched (session 15) | FINDING-INFRA-DATA-CONSOLIDATION-001 | IN FLIGHT — parallel with Batch X. 8 gate tests. |
| 2026-02-28 | Batch X ACCEPTED (session 16) | FINDING-ENGINE-UD-*-001 (2), FINDING-ENGINE-FAST-MOVEMENT-MEDIUM-LOAD-001, FINDING-ENGINE-MD-NAT1-NAT20-001, FINDING-ENGINE-FASCINATED-SKILL-PENALTY-001, FINDING-ENGINE-FE-CRIT-MULTIPLIER-001, FINDING-ENGINE-SECONDARY-STR-HALF-001 | All 7 CLOSED. Commits fd792d8/d53c604/d0a36ce/9e36811. 32/32 gates. 1 new LOW filed: FINDING-ENGINE-MD-INLINE-SAVE-PATTERN-001 (inline save bypasses resolve_save). |
| 2026-02-28 | SQLite WO ACCEPTED (session 16) | FINDING-INFRA-DATA-CONSOLIDATION-001 | CLOSED. Commit 0ac1fda. 8/8 gates. 2 new LOWs filed: FINDING-INFRA-FEATS-COUNT-MISMATCH-001 (109 vs ~221 spec), FINDING-INFRA-SPELL-CLASS-ID-ABBREVIATIONS-001 (abbreviated class IDs). |
| 2026-02-28 | SR WO ACCEPTED (session 18) | FINDING-ENGINE-SR-NOT-IN-SPELL-PATH-001 | CLOSED. Commits 8cc96f8/e1c2957. 8/8 gates. 1 new LOW filed: FINDING-ENGINE-SR-PLAY-LOOP-EVENTS-001 (play_loop SR event emission gap). |
| 2026-02-28 | Backlog quick scan (session 16) | All HIGH/MED | 0 HIGH open. 5 MEDIUM promoted to WOs (4 Batch Y + 1 standalone SR). 4 MEDIUM DEFERRED confirmed (rationale holds). 0 surprise aging. Clean. |
| 2026-02-28 | Batch Y drafted (session 16) | FINDING-ENGINE-RAGE-HP-ABSENT-001, FINDING-ENGINE-RAGE-FATIGUE-MOBILITY-001, FINDING-ENGINE-WS-USES-FORMULA-001, FINDING-ENGINE-WS-UNLOCK-LEVEL-001, FINDING-ENGINE-DISARM-SIZE-MODIFIER-001, FINDING-ENGINE-COUNTER-DISARM-THRESHOLD-001 | All 6 IN FLIGHT via Batch Y WO1–WO4. 32 gate tests expected. |
| 2026-02-28 | SR WO drafted (session 16) | FINDING-ENGINE-SR-NOT-IN-SPELL-PATH-001 | IN FLIGHT — WO-ENGINE-SR-SPELL-PATH-001 standalone. 8 gate tests. Parallel-safe with Batch Y. |
| 2026-02-28 | Session 18 triage pass | All HIGH/MED/LOW | 0 HIGH open. 4 MEDIUM IN FLIGHT (Batch Y). 2 MEDIUM tooling DEFERRED (feats count, spell class IDs). 2 LOW DEFERRED (WS size gating, concentration entangled). SR finding CLOSED+graduated. 1 new LOW filed (SR play_loop events). No promotions needed — all actionable MEDIUMs already in Batch Y. |
| 2026-02-28 | Batch Y ACCEPTED (session 19) | FINDING-ENGINE-RAGE-HP-ABSENT-001, FINDING-ENGINE-RAGE-FATIGUE-MOBILITY-001, FINDING-ENGINE-WS-USES-FORMULA-001, FINDING-ENGINE-WS-UNLOCK-LEVEL-001, FINDING-ENGINE-DISARM-SIZE-MODIFIER-001, FINDING-ENGINE-COUNTER-DISARM-THRESHOLD-001 | All 6 CLOSED. Commit b8f7f50. 32/32 gates. 4 new findings filed: 1 MEDIUM (exhausted condition gap), 3 LOW (Greater/Mighty Rage, Tireless Rage, 2H disarm bonus). |
| 2026-02-28 | Spellcasting audit ACCEPTED (session 19) | FINDING-AUDIT-SPELL-001 through 007 | 7 new findings: 1 HIGH (save ability mod double-count — SPELL-002), 1 MEDIUM (spell save bypass — SPELL-001), 5 LOW (SR events, missing metamagic, SR data gap, Empower+Maximize compat, bare string literal). 4 existing findings confirmed. SPELL-002 needs urgent investigation WO. SPELL-001 needs builder WO. |
| 2026-02-28 | Probe memo processed (session 19 cont.) | FINDING-ENGINE-CONCENTRATION-BONUS-UNWRITTEN-001, FINDING-ENGINE-MANEUVER-BAB-SHADOW-001, FINDING-PATTERN-FIELD-CONTRACT-UNDEFINED-001 | 3 new findings from computed field contract drift analysis. SPELL-002 status updated: BLOCKED on field contract spec + Thunder decision. SPELL-001 status updated: BLOCKED on SPELL-002 fix. All stat-math fixes BLOCKED until Thunder chooses Option A (full totals) vs Option B (base only). Fix order: spec → convention → save double-count → spell save path → concentration → maneuver BAB → parity tests. |
| 2026-02-28 | Thunder rulings processed (session 19 cont.) | FINDING-PATTERN-FIELD-CONTRACT-UNDEFINED-001 (ACTIONED), all BLOCKED findings (UNBLOCKED) | Thunder rejects binary A/B — rules typed contract policy (3 types: Component, Base+Permanent, Runtime-Only). Fix chain unblocked. Reordered per Thunder: concentration first (high gameplay impact), then save double-count, maneuver BAB, spell save unification. SPEC-COMPUTED-FIELD-CONTRACT-001 in draft. Field Contract Check + parity test template added to CLAUDE.md. |
| 2026-02-28 | Batch AA drafted (session 20) | RAGE-GREATER-MIGHTY-001, TIRELESS-RAGE-001, AUDIT-SPELL-004, AUDIT-SPELL-005, AUDIT-SPELL-007, DISARM-2H-ADVANTAGE-001, OVERRUN-FAILURE-PRONE-CHECK-001 | 8 LOWs promoted to Batch AA (4 WOs, 32 gates). Sequenced after Batch Z ACCEPTED. EXHAUSTED-CONDITION-GAP-001 (MEDIUM) under ML-003 re-investigation — formal definition found at conditions.py:41. |
| 2026-02-28 | Batch Z ACCEPTED (session 20) | FINDING-AUDIT-SPELL-002, FINDING-AUDIT-SPELL-001, FINDING-ENGINE-CONCENTRATION-BONUS-UNWRITTEN-001, FINDING-ENGINE-MANEUVER-BAB-SHADOW-001 | All 4 CLOSED. Commits 37a51ed/c214498. 32/32 gates. 16 stale tests updated for Type 2 field contract. 2 new LOWs filed: POSITION-TUPLE-FORMAT-001, NEGATIVE-LEVEL-SAVE-001. Field contract drift pattern CLOSED. |
| 2026-02-28 | Batch AA ACCEPTED (session 20) | FINDING-ENGINE-RAGE-GREATER-MIGHTY-001, FINDING-ENGINE-TIRELESS-RAGE-001, FINDING-ENGINE-DISARM-2H-ADVANTAGE-001 (ghost), FINDING-ENGINE-OVERRUN-FAILURE-PRONE-CHECK-001, FINDING-AUDIT-SPELL-004, FINDING-AUDIT-SPELL-005, FINDING-AUDIT-SPELL-007 | All 7 CLOSED (1 ghost: disarm 2H already at B-AMB-04). Commit 0b7cbad. 32/32 gates. 2 new LOWs filed: SPELL-DEF-DUPLICATE-ENTRIES-001, SPELL-DC-BASE-NO-WRITE-SITE-001. Pipeline pivot: coverage expansion (Class Features first). |
| 2026-02-28 | AUDIT-WO-009-SAVES ACCEPTED (session 20 cont.) | FINDING-AUDIT-SAVE-001 through 007 + FINDING-BARDIC-SAVE-SCOPE-001 | 8 new findings: 3 MEDIUM (CdG shadow path, multiclass max→sum saves, resolve_save bare call) + 5 LOW (RNG stream isolation, SaveContext schema gap, negative level split authority, multiclass BAB max→sum, bardic save scope). 3 existing confirmed: MD-INLINE-SAVE-PATTERN-001, NEGATIVE-LEVEL-SAVE-001, GNOME-ILLUSION-SAVE-001. Triage: SAVE-001 + SAVE-002 + SAVE-007 queued for standalone WO (parallel-safe with AB). SAVE-003 DEFERRED (needs schema extension, overlaps AB WO1). |
| 2026-02-28 | Batch AB ACCEPTED (session 20 cont.) | FINDING-ENGINE-PALADIN-POISON-IMMUNITY-BUG-001 | 1 HIGH CLOSED (pre-existing paladin poison immunity bug found+fixed in WO2). 2 new LOWs filed: SCHOOL-PARAM-NON-SPELL-001, KI-STRIKE-WILDSHAPE-001. Commits 3ec541b/0ebc5e3. 32/32 gates. 7 coverage map rows → IMPLEMENTED. |
| 2026-02-28 | Save Fix WO ACCEPTED (session 20 cont.) | FINDING-AUDIT-SAVE-001, FINDING-AUDIT-SAVE-002, FINDING-AUDIT-SAVE-007, FINDING-ENGINE-CDG-NAT1-NAT20-MISSING-001 | 3 MEDIUM + 1 LOW CLOSED. Commits f58411c/e452fef. 16/16 gates. Multiclass max()→sum() at 4 builder.py sites. CdG shadow path eliminated. CdG nat1/nat20 added (was missing despite WO spec claim). 6 existing tests updated. |
| 2026-02-28 | Batch AC ACCEPTED (session 20 cont.) | FINDING-ENGINE-SAVE-DESCRIPTOR-PASS-001 (new), FINDING-ENGINE-FLURRY-WEAPON-ID-FIELD-001 (new) | 0 findings closed. 2 new LOWs filed. AoC CONSUME_DEFERRED — SaveContext has no descriptor field. Commits c99628d/563af6e. 32/32 gates. 4 coverage rows → IMPLEMENTED (Flurry, Diamond Soul, Wholeness of Body, Aura of Courage). SaveContext descriptor cluster now has 5 findings (SAVE-003, SAVE-005, GNOME-ILLUSION, SCHOOL-PARAM-NON-SPELL, SAVE-DESCRIPTOR-PASS) — promote SaveContext schema extension to WO for Batch AD. |
| 2026-02-28 | Batch AD ACCEPTED (session 20 cont.) | FINDING-AUDIT-SAVE-003, FINDING-AUDIT-SAVE-005, FINDING-ENGINE-GNOME-ILLUSION-SAVE-001, FINDING-ENGINE-SCHOOL-PARAM-NON-SPELL-001, FINDING-ENGINE-SAVE-DESCRIPTOR-PASS-001 | 5-finding SaveContext cluster ALL CLOSED by WO1 (0275dea/3cb30ac). 33/33 gates. SaveContext now carries save_descriptor + school fields. All descriptor-dependent paths wired (AoC fear, gnome illusion, Still Mind, Indomitable Will, racial enchantment). |
| 2026-02-28 | Batch AD ACCEPTED (session 20 cont.) | FINDING-ENGINE-SPONTANEOUS-ALIGNMENT-001 | CLOSED by WO3 (0275dea). Evil Cleric inflict swap implemented with alignment guard. 1 MEDIUM closed. |
| 2026-02-28 | Batch AD debrief new findings (session 20 cont.) | FINDING-ENGINE-SPELL-RESOLVER-SAVE-BYPASS-001 (new MEDIUM), FINDING-ENGINE-INSPIRE-GREATNESS-HD-001 (new LOW) | 2 new CONSUME_DEFERRED findings. SPELL-RESOLVER-SAVE-BYPASS-001 OPEN — spell_resolver._resolve_save() shadow path bypasses canonical save_resolver; promote to WO for Batch AE standalone or bundle. INSPIRE-GREATNESS-HD-001 OPEN — Inspire Greatness +2 HD HP pool not implemented (WO4 wired attack/save bonus only). Sweep audit due (5 batches since AUDIT-WO-009-SAVES: AA, AB, Save Fix, AC, AD). |
| 2026-02-28 | AUDIT-WO-010-CONDITIONS ACCEPTED (session 20 cont.) | FINDING-AUDIT-CONDITIONS-001, FINDING-AUDIT-CONDITIONS-002, FINDING-AUDIT-CONDITIONS-003, FINDING-BARDIC-SAVE-SCOPE-001 (unblocked), FINDING-ENGINE-KI-STRIKE-WILDSHAPE-001 (confirmed LOW) | 5 gaps, 6 confirmed working (Q2 AoC fear descriptor e2e, Q3 Still Mind, Q4 Indomitable Will, Q7 immunity pattern, Q8 duration tracking, Q10 application completeness). 3 MEDIUMs promoted to Batch AE (WO1: SPELL-RESOLVER+CONDITIONS-002 bundle; WO2: CONDITIONS-001; WO3: CONDITIONS-003+BARDIC). EXHAUSTED-CONDITION-GAP-001 closed — ML-003 confirmed formal definition exists; CONDITIONS-001 captures the precise gap. |
| 2026-02-28 | Batch AE ACCEPTED (session 20 cont.) | FINDING-ENGINE-SPELL-RESOLVER-SAVE-BYPASS-001, FINDING-AUDIT-CONDITIONS-002, FINDING-AUDIT-CONDITIONS-001, FINDING-AUDIT-CONDITIONS-003, FINDING-BARDIC-SAVE-SCOPE-001 | 4 MEDIUM + 1 LOW CLOSED. Commits ab44488/fb0f8f4. 32/32 gates. WO1: spell_resolver shadow path eliminated (play_loop.py:274) + poison CON double-count stripped (4 sites). WO2: EF.FATIGUED → -2 Ref penalty in save_resolver. WO3: AoC L2→L3 (both builder paths) + Inspire Courage scoped to fear/charm saves only. WO4: EF.TRAP_SENSE_BONUS wired at chargen (barb//3 + rogue//3) + save_resolver Ref consume for save_descriptor="trap". 1 new LOW: TRAP-SENSE-AC-001 (AC vs traps CONSUME_DEFERRED). 3 old tests corrected. 2 coverage rows → IMPLEMENTED (Barb Trap Sense, Rogue Trap Sense). 58 findings graduated. |
| 2026-02-28 | Batch AF dispatch (session 21) | FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001 | Promoted DEFERRED → IN FLIGHT (Batch AF WO2). AUDIT-WO-002 stale briefing entry cleared — verdict was already session 10. 0 HIGH/MEDIUM outstanding. 0 new findings. |
