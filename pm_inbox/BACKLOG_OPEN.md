# BACKLOG — Open Findings Awaiting Triage

**Lifecycle:** ACTIVE (permanent file — not subject to inbox cap or archival)
**Last triaged:** 2026-03-01 (session 27) — Phase 2 OSS research memos triaged (first+second pass). 2 MEDIUM + 2 LOW findings added (WM foundation, SRD extract, third-pass targets, ZenLib queue). WSP debrief findings added (WSP-DOUBLE-COUNT closed, WSP-FAR-DEAD-PATH LOW open). Next triage: after Batch AJ verdict + Stage 3 verdict.
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
| FINDING-ENGINE-DA-ROUND-RESET-001 | `deflect_arrows_used` list in `active_combat` is initialized in `start_combat()` but NOT cleared in `execute_combat_round()` round-reset block. `aoo_used_this_round` + `aoo_count_this_round` both reset; DA list does not. Multi-round combat: any defender who deflected in round 1 is permanently locked out for the rest of combat. DA-001 gate only tests single-round. PHB p.93: "once per round." Fix: one line in `combat_controller.py:execute_combat_round()`. | Batch AI ML-002 post-debrief (Chisel + Thunder) | **CLOSED** — WO-ENGINE-DA-ROUND-RESET-001 (d1fecb4). One-line fix at combat_controller.py:348. 4/4 gates. `active_combat` inventory audit clean. |
| FINDING-AUDIT-SPELL-002 | save_resolver.get_save_bonus() likely double-counts ability modifier — chargen writes class_base+ability_mod into EF.SAVE_*, save_resolver adds ability_mod again. Affects ALL non-spell saves. | Spellcasting audit | **CLOSED** — Batch Z WO2 (37a51ed). ability_mod stripped from save_resolver. Type 2 contract enforced. |
| FINDING-PATTERN-FIELD-CONTRACT-UNDEFINED-001 | No declared contract for composite EF fields. Root cause of save double/under-count. Chargen and resolvers make independent assumptions about field contents. | Probe memo | ACTIONED — Thunder ruled: typed contract policy (3 types). SPEC-COMPUTED-FIELD-CONTRACT-001 in draft. |
| FINDING-ATTACK-WF-SCHEMA-SPLIT-001 | Weapon Focus implemented twice with incompatible key schemas. `feat_resolver.get_attack_modifier()` checks `weapon_focus_{weapon_name}` (e.g., "weapon_focus_longsword" via EF.WEAPON). `attack_resolver._wf_bonus` checks `weapon_focus_{weapon_type}` (e.g., "weapon_focus_light" via intent.weapon.weapon_type). Both are summed in the attack roll. One always fires, one always misses — which depends on chargen key format. Neither WO defines the key contract. Parallel Path Drift (CLAUDE.md failure family). MUST have WO. feat_resolver.py:154–158 vs attack_resolver.py:691–693. | WO-AUDIT-ATTACK-011 (2026-03-01) | **CLOSED** — WO-ENGINE-WF-SCHEMA-FIX-001 (686324d). _wf_bonus deleted, dict extraction at both resolver call sites, canonical weapon_focus_{weapon_name} enforced. 8/8 WFS + 8/8 WFC. |
| FINDING-INFRA-MEMORY-001 | Chisel kernel session delta bloat — 84% of `CHISEL_KERNEL_001.md` (~8,755 tokens, lines 201–828) is 15 session deltas appended sequentially and never consulted at boot. "Project State" (lines 37–59) and "State Correction" (lines 155–198) are frozen at 2026-02-26 founding values. Graduate all deltas to `CHISEL_SESSION_ARCHIVE.md`; trim kernel to Identity + Behavioral Rules + DM Kernel Quick Ref + Communication Paths (~1,750 tokens). Source: `pm_inbox/reviewed/PROBE-MEMORY-ARCHITECTURE-001.md` FINDING-001 + FINDING-008. | PROBE-MEMORY-ARCHITECTURE-001 (2026-02-28) | OPEN — WO needed: Chisel kernel compression (bundle with FINDING-008/009) |
| FINDING-INFRA-MEMORY-002 | PM Briefing historical batch bloat — 86% of `PM_BRIEFING_CURRENT.md` (~23,570 tokens) is DEAD: full entries for 25+ accepted batches, completed track progress bars (BURST/PRS/UI/CHARGEN), and Open Findings table that 100% duplicates BACKLOG_OPEN. Graduate accepted batch entries >3 old to `PM_BRIEFING_ARCHIVE.md` (one-liner per batch). Remove completed tracks + findings table. Post-compression target: ~2,930 tokens. Source: PROBE §1, FINDING-002 + FINDING-003 + FINDING-012. | PROBE-MEMORY-ARCHITECTURE-001 (2026-02-28) | OPEN — Slate self-execute (Wave 1 compression; include FINDING-012 progress bars) |

---

## MEDIUM Severity

### Engine — Existing

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-ENGINE-LIFECYCLE-FSM-001 | Strategy doc (`docs/design/STRATEGY-OSS-INTEGRATION-001.md`) marks Entity Lifecycle FSM as Phase NOW: attach states (alive→dying→dead→remnant→raised) to entity dict. Unblocks KERNEL-01 (Entity Lifecycle Ontology). Design caveat: dict-vs-object representation question must be answered before WO dispatch. No backlog entry existed. | Session 23 — research sweep | OPEN — design decision required before WO dispatch |
| FINDING-ATTACK-AOO-ROUND-RESET-001 | `aoo_used_this_round` (list), `aoo_count_this_round` (dict), and `deflect_arrows_used` (list) in `active_combat` are appended but NEVER cleared at round boundaries. End-of-round block at play_loop.py:4260–4309 handles duration/dying/condition ticks but omits AoO reset. PHB p.137: 1 AoO/round per creature. PHB p.93: Deflect Arrows once/round. After round 1, both limits are permanently consumed for the entire combat. `cleave_used_this_turn` IS correctly cleared at turn start (line 1869). | WO-AUDIT-ATTACK-011 (2026-03-01) | OPEN |
| FINDING-ENGINE-WSP-SCHEMA-DRIFT-001 | `weapon_specialization_{weapon_type}` in `attack_resolver.py:960` uses old type-based key schema (e.g., `weapon_specialization_light`) instead of name-based schema (e.g., `weapon_specialization_longsword`). Same root cause as WF Path B (now fixed). PHB p.102: WSP applies to "one type of weapon" — named weapon, not meta-category. Needs same dict-extraction fix as WF. FAGU-010 fixture also uses old `weapon_specialization_light` key — will need update when WSP is fixed. | WO-ENGINE-WF-SCHEMA-FIX-001 debrief (2026-03-01) | OPEN — file WO for Batch AJ |
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
| FINDING-INFRA-WS-FORMAT-SPLIT-001 | `session_orchestrator.py` uses two incompatible event serialization formats: Format A (combat path, "type" key, lines 634-637) and Format B (exploration, "event_type" key, lines 905-909). PLUMB-001 workaround in place (`event_dict.get("event_type") or event_dict.get("type", "")`). Any new event emitter must know which path or events will silently misroute. Root fix: unify to single format. | PLUMB-001 debrief Pass 3 | OPEN — workaround stable; unification deferred |

### OSS Data Ingestion — Pipeline Not Executed

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-OSS-FEATS-INGESTION-GAP-001 | OSS research sprint (2026-02-26) identified zellfaze-zz/dnd-generator `feats.json` (221 feats, CC0, no parser needed) as primary feat benefit source. WO-DATA-FEATS-PREREQS-001 hand-populated 52 feats instead. LST parser built (WO-LST-PARSER-001 ACCEPTED). Corrective ingestion required: clone zellfaze, read feats.json, replace hand-typed data with all 221 feats + structured benefit values. Supersedes FINDING-INFRA-FEATS-COUNT-MISMATCH-001. | Session 23 — OSS ingestion audit | **IN FLIGHT** — STRAT-OSS-INGESTION-SPRINT-001.md WO1 (session 24) |
| FINDING-OSS-MONSTERS-INGESTION-GAP-001 | OSS research sprint (2026-02-26) identified Obsidian-TTRPG-Community/DnD-3.5-SRD-Markdown as primary monster source (~150-200 line regex parser described, verified as primary path). WO-DATA-MONSTERS-001 hand-populated 28 creatures instead. Corrective ingestion required: clone repo, build described regex parser, replace hand-typed data with full SRD monster set. | Session 23 — OSS ingestion audit | **IN FLIGHT** — STRAT-OSS-INGESTION-SPRINT-001.md WO4 (session 24) |
| FINDING-OSS-SPELLS-INGESTION-GAP-001 | OSS research sprint (2026-02-26) identified PCGen `rsrd_spells.lst` (~350 spells, COMPS/SCHOOL/SAVEINFO/SPELLRES fields verified) as primary spell source. Current spell registry: 45 spells. WO-DATA-SPELLS-001 was listed as an immediate action candidate but never dispatched. LST parser built (WO-LST-PARSER-001 ACCEPTED). Corrective ingestion required: clone PCGen, run LST parser against rsrd_spells.lst, expand registry 45→~350. | Session 23 — OSS ingestion audit | **IN FLIGHT** — STRAT-OSS-INGESTION-SPRINT-001.md WO2 (session 24) |
| FINDING-OSS-EQUIPMENT-INGESTION-GAP-001 | OSS research sprint (2026-02-26) identified PCGen `rsrd_equip.lst` (all 12 PHB armor types with SPELLFAILURE/MAXDEX/ACCHECK tags, verified exact values) as equipment data source. WO-DATA-EQUIPMENT-001 was listed as an immediate action candidate but never dispatched. LST parser built. Corrective ingestion required: run LST parser against rsrd_equip.lst, populate armor catalog with exact PHB values. | Session 23 — OSS ingestion audit | **IN FLIGHT** — STRAT-OSS-INGESTION-SPRINT-001.md WO3 (session 24) |
| FINDING-OSS-CLASS-TABLES-GAP-001 | OSS research sprint (2026-02-26) verified PCGen `rsrd_classes.lst` contains: CAST: spell slot tables (all casting classes, all 20 levels), KNOWN: spells-known tables (Sorc/Bard), UDAM: monk unarmed damage (all 20 levels × sizes), ABILITY: feature grant levels. `rsrd_abilities_class.lst` has BONUS:VAR formulas for class feature scaling (~20 formulas: rage/day, SA dice, LoH pool). LST parser built. WO-DATA-CLASS-TABLES-001 was an immediate action candidate but never dispatched. Strategy doc also notes 9 skill synergy pairs from `rsrd_skills.lst` — bundle into this WO. | Session 23 — research sweep | DEFERRED — Sprint 002 (BONUS:VAR formula resolution requires architecture design; after Sprint 001 ACCEPTED) |
| FINDING-OSS-WEAPON-CATALOG-SPOTCHECK-001 | OSS research sprint (2026-02-26) identifies zellfaze `mundane_items.json` as weapon catalog source (damage dice, crit range/multiplier, damage type). Strategy doc explicitly flags: "Spot-check against PCGen values before use." No spot-check has been done; no WO exists to perform it. Required before weapon catalog data is treated as validated. | Session 23 — research sweep | **IN FLIGHT** — STRAT-OSS-INGESTION-SPRINT-001.md WO3 (session 24, bundled with equipment) |

### Pre-Design Probes — Phase 2 Architecture

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-PROBE-WORLDMODEL-001-UNTRACKED | PROBE-WORLDMODEL-001 (12 W-class and B-class gap families: entity lifecycle, remnant ontology, constraint algebra, epistemic state, etc.) referenced in briefing as queued but has NO entry in BACKLOG_OPEN.md. Must be DEFERRED (Phase 2 gate) but it must be tracked. Source: `docs/design/` canary gap docs. | Session 23 — research sweep | DEFERRED — Phase 2; do not touch until Phase 1 closes. Track here so it survives compaction. |
| FINDING-PROBE-JUDGMENT-LAYER-001-UNTRACKED | PROBE-JUDGMENT-LAYER-001 identified in `docs/design/STRAT-AIDM-JUDGMENT-LAYER-001.md` with canary pack (10 golden test cases), three phases (Shadow/Guarded/Canonical), and explicit Thunder/Aegis direction to run Shadow phase in parallel with Batch D. No backlog entry exists. Pre-design specs (SPEC-RULING-CONTRACT-001, SPEC-ROUTING-BOUNDARY-MATRIX-001, GATE-JUDGMENT-ACCEPTANCE-001) all in DRAFT status. Source: `docs/design/STRAT-AIDM-JUDGMENT-LAYER-001.md`. | Session 23 — research sweep | OPEN — Phase 2 pre-design; Thunder/Aegis direction pending scheduling |
| FINDING-CONSTRAINT-SYSTEM-STRATEGY-PENDING-001 | `docs/design/LEDGER-CHEEVO-CANARY-EXPANSION-001.md` entry C-004 (Genie Wish Inversion) and C-005 (Kevin's Oath Stack) reference a constraint system architecture (binding rules, oath tracking, geas/bond mechanics) and explicitly note "STRATEGY-CONSTRAINT-SYSTEM-001 (new strategy item needed)." This strategy doc has not been filed. Constraint system is KERNEL-02 level (Containment Topology) and blocks proper routing of several canary findings. | Phase 0 sweep Pass B — 2026-03-01 | OPEN — Phase 2; strategy doc required before WO-ENGINE-CONTAINMENT-001 can be dispatched |

### Phase 2 — Complex Feat Mechanics (Action Economy)

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-PHASE2-COMPLEX-FEAT-BATCH-001 | Spring Attack / SOTR / Manyshot (Batch AH) + Whirlwind Attack (Batch AI) ALL IMPLEMENTED. **Remaining: Ride-By Attack only** — move-attack-move with reach consideration mid-movement is the genuinely complex case. Other "Phase 2" action economy feats were implemented as standard WOs without architectural redesign. | Session 23 — research sweep | DEFERRED — Ride-By Attack requires movement-mid-attack architecture; after position model exists |

### Memory Architecture (WO-INFRA-MEMORY-CHAIN-AUDIT-001)

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-INFRA-MEMORY-007 | MEMORY.md truncation risk — 181/200 lines (hard system cap), 19 lines remaining. Growth ~5 lines/2 batches → ~7 batches to silent truncation. Self-execute: graduate Playwright notes (~9 lines, COLD) + OSS Research (~4 lines, CLOSED) + compress Batch Status to 3-line summary. Net savings ~26 lines. **Imminent.** | PROBE-MEMORY-ARCHITECTURE-001 (2026-02-28) | OPEN — Slate self-execute (imminent; do before next batch dispatch) |
| FINDING-INFRA-MEMORY-008 | Chisel Kernel stale Project State — "Project State" section (lines 37–59) frozen at 2026-02-26: 7,211 tests (actual 8,500+), "Batch C — pending dispatch" (actual Batch AI ACCEPTED). "State Correction" (lines 155–198) same vintage. ~840 tokens of founding-session dead weight. Bundle with FINDING-001 Chisel kernel compression WO. | PROBE-MEMORY-ARCHITECTURE-001 (2026-02-28) | OPEN — bundle into Chisel kernel compression WO |
| FINDING-INFRA-MEMORY-009 | No T0a/T0b split in any kernel — invariant identity (static) mixed with variable capsule (per-session state) → unbounded accordion regrowth. Root cause of Chisel kernel bloat. All kernels need explicit T0a (identity/doctrine, append-only deliberate revision) and T0b (capsule, overwrite each session). 0 tokens recoverable immediately; prevents recurrence. Bundle with kernel compression WO. | PROBE-MEMORY-ARCHITECTURE-001 (2026-02-28) | OPEN — bundle into Chisel kernel compression WO |
| FINDING-INFRA-MEMORY-004 | Seven Wisdoms triplicated — full text in Chisel Kernel (~14 lines, ~175 tokens), BS_BUDDY (~9 lines, ~115 tokens), partial in Slate Kernel. ~700 tokens recoverable if all seats replace with pointer to DOCTRINE_09. Requires Thunder decision: consolidate Seven Wisdoms to shared pointer OR keep seats self-contained. | PROBE-MEMORY-ARCHITECTURE-001 (2026-02-28) | DEFERRED — Thunder decision required (CLAUDE.md expansion authority) |
| FINDING-INFRA-MEMORY-005 | MCP Tools list quadruplicated — Slate Kernel, MEMORY.md, BS_BUDDY, Chisel Seat each carry their own version (~8–23 lines). ~500 tokens recoverable. Recommended: move canonical list to CLAUDE.md; seats retain seat-specific notes only (1–2 lines). Requires Thunder decision: CLAUDE.md expansion authority. | PROBE-MEMORY-ARCHITECTURE-001 (2026-02-28) | DEFERRED — Thunder decision required (CLAUDE.md expansion authority) |
| FINDING-INFRA-MEMORY-006 | Seed Canon loaded every Slate boot — 54 rules (~750 tokens) from `REHYDRATION_KERNEL_LATEST.md` load every boot; not referenced operationally in 16 sessions. Graduate to `docs/doctrine/SEED_CANON_V0.1.md`; replace with 1-line pointer. Requires Thunder decision: approve philosophical doctrine graduation. | PROBE-MEMORY-ARCHITECTURE-001 (2026-02-28) | DEFERRED — Thunder decision required (approve Seed Canon graduation) |

### Phase 2 — World Model / Judgment Infrastructure (OSS Research 2026-03-01)

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-PHASE2-OSS-WM-FOUNDATION-READY-001 | SPEC-WORLD-MODEL-001 implementation foundation locked from phase 2 OSS research (both passes). Storage: simple-graph schema (copy 20-line SQL, add `t_valid`/`t_invalid` columns — do NOT pip install, own the schema). Temporal contradiction: Graphiti exact UPDATE+INSERT+SELECT SQL extracted (bi-temporal, "latest wins" rule). Traversal: AriGraph BFS concept (~30 lines Python wrapper on simple-graph CTE — AriGraph code has hard OpenAI dep, port by reference only). No speculation remaining. WO-WORLD-MODEL-RELATIONS-001 can dispatch once SPEC-WORLD-MODEL-001 is filed. | Phase 2 OSS research pass 2 (2026-03-01) | OPEN — file SPEC-WORLD-MODEL-001 next |
| FINDING-PHASE2-OSS-SRD-DATA-EXTRACT-001 | pydnd has 2 skills only — dead end. WO-DATA-PYDND-READ-001 CLOSED. **Pass 3 update: dnd-generator phb/ is the source (not DnD-3.5-SRD-Markdown).** Scope drops from "write Markdown parser" to "map JSON fields to EF schema" (~30 lines Python). Output: `aidm/data/srd_skills.json` + `aidm/data/srd_dc_ranges.json`. | Phase 2 OSS research pass 3 (2026-03-01) | OPEN — dispatch WO-DATA-SRD-EXTRACT-001 before validator WO |
| FINDING-PHASE2-OSS-DNDGEN-JSON-001 | dnd-generator (zellfaze-zz/dnd-generator) phb/ directory is the **primary 3.5e data source** — CC0/OGL, no parser needed. Contains: `skills.json` (all skills: ability key, trained flag, armor check, synergy array), `feats.json` (all feats: prerequisites as string[], numeric benefits structured), `classes.json` (full level progressions: BAB/saves/abilities per level). Also: spells, races, magic items, mundane items. This is the data source for DC validator + mechanic registry + future feat ingestion expansion. DnD-3.5-SRD-Markdown demoted to QA reference. PCGen LST fallback only. | Phase 2 OSS research pass 3 (2026-03-01) | OPEN — feeds WO-DATA-SRD-EXTRACT-001 |
| FINDING-PHASE2-OSS-INSTRUCTOR-API-CORRECTION-001 | MEMO_PHASE2_OSS_RESEARCH_BRIEF_001 instructor integration API is **WRONG**. Correct API (pass 3 confirmed): `instructor.patch(create=llama.create_chat_completion_openai_v1, mode=instructor.Mode.JSON_SCHEMA)` — NOT `instructor.patch(Llama(...))`. WO-JUDGMENT-GUARDED-001 spec must use the corrected form. Do NOT draft WO-JUDGMENT-GUARDED-001 from the brief — pull from this finding. | Phase 2 OSS research pass 3 (2026-03-01) | OPEN — apply in WO-JUDGMENT-GUARDED-001 spec |

---

## LOW Severity

| ID | Summary | Filed | Status |
|----|---------|-------|--------|
| FINDING-INFRA-MEMORY-010 | Backlog CLOSED entries not graduated — ~32 CLOSED rows still inline in active tables (~800 tokens). Graduate to `pm_inbox/reviewed/BACKLOG_GRADUATED.md` or collapsed "Graduated (CLOSED) Summary" section. Slate self-execute at next triage pass. | PROBE-MEMORY-ARCHITECTURE-001 (2026-02-28) | OPEN — Slate self-execute at next triage |
| FINDING-INFRA-MEMORY-012 | Briefing completed track progress bars — ~30 lines of done tracks (BURST-001, PRS-01, UI slices 0-7, Chargen Phase 3) in "Current Focus" as strikethrough. ~400 tokens. Bundle into FINDING-002 briefing compression self-execute. | PROBE-MEMORY-ARCHITECTURE-001 (2026-02-28) | OPEN — bundle with FINDING-002 self-execute |
| FINDING-PROCESS-BUILDER-PRE-ACCEPTED-RECURRING-001 | Builder pre-populates ACCEPTED verdict in PM_BRIEFING_CURRENT.md before PM issues verdict. 2nd occurrence (AG + AH). Correct status is FILED. Root cause: builder modifying PM artifact during debrief process. | Session 25 (PM verdict review) | OPEN |
| FINDING-COVERAGE-MAP-SECTION-MISFILE-001 | Deflect Arrows and Far Shot listed in §7b "PHB Feats Not Yet Registered" with status IMPLEMENTED. Both belong in §7a (Implemented/Active Feats). Deflect Arrows is fully IMPLEMENTED (WO-ENGINE-AI-WO3, 8 gate tests). Map underreports implemented coverage. ENGINE_COVERAGE_MAP.md §7b. | WO-AUDIT-ATTACK-011 (2026-03-01) | OPEN |
| FINDING-PROCESS-DEBRIEF-FORMAT-DRIFT-001 | Batch AI debrief missing: (1) explicit PM Acceptance Notes confirmation section (AH + PLUMB-001 both had it), (2) ML Preflight Checklist table in debrief body. Kernel cross-pollination labels also incorrect (KERNEL-06 "Feat Resolution" / KERNEL-08 "Combat State" don't exist in register). 2 consecutive batches with format gaps. Address in next dispatch with explicit debrief quality reminder. | Batch AI PM verdict | OPEN |
| FINDING-ENGINE-FREE-HAND-SETTER-002 | `EF.FREE_HANDS` has no chargen/equip setter. Default of 1 works for bare-handed / one-handed; two-handed grip, TWF, or certain conditions should set it to 0. Setter deferred to equip WO. | Batch AI WO3 CONSUME_DEFERRED | OPEN |
| FINDING-ENGINE-WHIRLWIND-REACH-001 | PHB p.102 specifies targets must be within reach. Engine trusts DM/AI assertion (target_ids list). No geometric reach check. Architectural gap — no position model. | Batch AI WO1 Pass 3 | OPEN |
| FINDING-ENGINE-RANGE-PENALTY-CONSUME-001 | `compute_range_penalty()` is a utility the DM/AI layer must call before constructing AttackIntent. No automatic range-penalty in resolve_attack(). Engine is trusted-caller for range math. Known gap. | Batch AI WO2 Pass 3 | OPEN |
| FINDING-ENGINE-CONDITION-NORMALIZE-DEAD-CODE-001 | `_normalize_condition_dict()` in `conditions.py` is production-dead — only CF-007/CF-008 gate tests call it directly. Live code path does not use it. Intentional for test verifiability but undocumented. Add comment: "# test-verifiability only — not called from live code." | Batch AI ML-002 (Chisel) | OPEN |
| FINDING-INFRA-SEEDED-RNG-DISCOVERABILITY-001 | `SeededRNG` class does not exist in `rng_protocol.py` despite module name implying it. All gate tests use `mock.MagicMock()` for the RNG interface. Discoverability gap — future builders will look for SeededRNG and find nothing. Document the mock pattern in BUILDER_FIELD_MANUAL. | Batch AI ML-002 (Chisel) | OPEN |
| FINDING-ENGINE-MANYSHOT-BAB-SCALING-001 | Manyshot 3rd/4th arrow at BAB+11/+16 not implemented (CONSUME_DEFERRED per Batch AH WO4). Note left in resolve_manyshot(). Low-priority scaling extension. | Batch AH | OPEN |
| FINDING-INFRA-CLIENT2D-DEAD-TESTS-001 | `test_ui_client_patch_001_gate.py` (CP-01–CP-09, 9 tests) all fail against `client2d/main.js` — a legacy compiled output directory. These 9 failures are in the 149 pre-existing failure baseline. client2d may be dead test coverage. PM triage: confirm if client2d is still in scope or can be cleaned up. | PLUMB-001 debrief Pass 3 | OPEN |
| FINDING-STANDING-POLICY-DECISIONS-GOVERNANCE-CAPTURE-001 | 5 policy rulings in STRATEGY-REDTEAM-AXIS-001 (called shots, psychopathy immunity, holy water targeting, degrees of success, folklore creature rules) — confirm formally documented in BUILDER_FIELD_MANUAL or standing ops; 3 of 5 have WOs (CAT-05 called shots, verbal spell block, intimidate demoralize) but 2 unconfirmed | Phase 0 sweep Pass B | OPEN |
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
| FINDING-ENGINE-FLAT-FOOTED-COND-FORMAT-001 | Empty dict `{}` for flat_footed condition key silently fails ConditionInstance.from_dict() parsing — loses_dex_to_ac stays False, sneak attack never fires. Test entities must use `create_flat_footed_condition(...).to_dict()` not bare `{}`. Latent trap for future gate authors. | Batch AG debrief | OPEN — LOW. Add to BUILDER_FIELD_MANUAL or KNOWN_TECH_DEBT. |
| FINDING-ENGINE-GNOME-ILLUSION-SAVE-001 | Gnome +2 vs illusion spells — SaveContext had no spell school field | Batch S | **CLOSED** — Batch AD WO1 (0275dea). SaveContext school field added; gnome illusion save bonus wired correctly. |
| FINDING-ENGINE-WS-SIZE-GATING-001 | Wild shape size gating absent | RAW audit | DEFERRED — architectural complexity; no current sprint |
| FINDING-ENGINE-PA-FULL-ATTACK-ROUND-LOCK-001 | PA penalty not enforced at round level — trusts caller | Batch P | DEFERRED |
| FINDING-ENGINE-GC-CHAIN-HP-MUTATION-001 | Great Cleave chain kills untestable without apply_attack_events() | Batch Q | DEFERRED — test harness gap, not runtime bug |
| FINDING-ENGINE-WF-SPECIFIC-WEAPON-001 | WF keyed on weapon_type, not specific weapon | Batch Q | DEFERRED — acceptable simplification |
| FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001 | EF.MONK_UNARMED_DICE set, resolver doesn't read it | Batch S | **CLOSED** — Batch AF WO2 (2edf076). attack_resolver.py reads MONK_UNARMED_DICE for unarmed monk strikes. Flurry path confirmed parity. |
| FINDING-ENGINE-CONDITIONS-LEGACY-FORMAT-001 | `get_condition_modifiers()` safety guard returns zero modifiers for legacy `["condition"]` list format — resolvers calling it will silently miss conditions stored in list format. DR flat-footed required explicit workaround. | Batch AF WO4 | OPEN — LOW. Foundational: affects any resolver reading condition modifiers. Future conditions cleanup WO. |
| FINDING-DATA-MONSTER-EF-FIELDS-001 | `CreatureStatBlock` has no mapping to EF.* constants. Future WO integrating creature_registry as runtime entities will need EF field mapping. | WO-DATA-MONSTERS-001 debrief | OPEN |
| FINDING-INFRA-DICE-D20-RANDGEN-001 | d20 installed version doesn't support `Roller(randgen=...)` as WO dispatch specified. Seeded path uses regex fallback for seeded rolls. No behavioral difference. | WO-INFRA-DICE-001 debrief | OPEN |
| FINDING-ENGINE-RACIAL-VISION-WRITE-ONLY-001 | low_light_vision + darkvision_range — no vision resolver | Opus audit | DEFERRED — no vision subsystem |
| FINDING-ENGINE-RACIAL-ILLUSION-WRITE-ONLY-001 | spell_resistance_illusion + illusion_dc_bonus — no illusion subsystem | Opus audit | DEFERRED — no illusion subsystem |
| FINDING-ENGINE-RACIAL-EXPLORATION-WRITE-ONLY-001 | stonecunning + automatic_search_doors — no exploration resolver | Opus audit | DEFERRED — no exploration subsystem |
| FINDING-ENGINE-IMPROVED-DISARM-COUNTER-SUPPRESS-001 | Improved Disarm counter suppression not in PHB | RAW audit | DEFERRED — remove per Thunder ruling (2026-02-27): not in PHB, not promoted to HOUSE_POLICY; add to future cleanup WO |
| FINDING-AUDIT-AE-003 | AoO round-reset in combat_controller, not execute_turn | AE audit | DEFERRED — test harness isolation gap, not production bug |
| FINDING-ENGINE-CONCENTRATION-ENTANGLED-001 | Concentration check for entangled condition unimplemented | Build plan | DEFERRED — no entangled condition resolver yet |
| FINDING-PROBE-WORLDMODEL-001-UNTRACKED | Phase 2 pre-design probe (12 gap families). Deferred until Phase 1 closes. | Session 23 | DEFERRED — Phase 2 gate |
| FINDING-PHASE2-COMPLEX-FEAT-BATCH-001 | Spring Attack / Whirlwind / Manyshot multi-phase action economy. Requires architecture design. | Session 23 | DEFERRED — Phase 2; action economy design required |
| FINDING-UI-PIPE-TARGET-AMBIGUITY-001 | "attack goblin" ambiguous in 3-goblin fixture; intent bridge returns FC-AMBIG. Correct engine behavior. Client needs disambiguation UI. | WO-UI-PHASE1-PIPE-001 debrief | OPEN — Stage 3+ scope |
| FINDING-UI-PIPE-START-SERVER-SHARED-STATE-001 | `start_server.py` shares one WorldState across all sessions — intentional for Stage 1. Must call `build_simple_combat_fixture()` inside factory() before Stage 2 multi-session dispatch. | WO-UI-PHASE1-PIPE-001 debrief | **CLOSED** — WO-UI-PHASE1-ENEMY-LOOP-001 (c9e0428). Factory now builds fresh fixture per connection. |
| FINDING-UI-ENEMY-LOOP-SEED-ENTROPY-001 | `_play_run_enemy_turn` receives constant master_seed; enemy turns use `seed + turn_index` internally so per-turn rolls differ, but two sessions with identical seeds produce identical enemy sequences. Non-issue for Stage 1 single-player. | WO-UI-PHASE1-ENEMY-LOOP-001 debrief | OPEN — Stage 3+ scope |
| FINDING-UI-ENEMY-LOOP-INITIATIVE-WRAP-001 | `_initiative_index` wraps correctly per round but orchestrator does not fire `round_start` event or increment `round_index` in `active_combat`. Engine tracks round_index; orchestrator loop does not advance it. | WO-UI-PHASE1-ENEMY-LOOP-001 debrief | OPEN — Stage 3 scope |
| FINDING-UI-ENEMY-LOOP-NARRATION-ENEMY-001 | Enemy turn events merged into TurnResult but no narration generated for enemy actions. Orchestrator narrates only player action. Enemy attacks/kills appear as raw events with no narrative text. | WO-UI-PHASE1-ENEMY-LOOP-001 debrief | OPEN — Stage 3 scope (GAP-06) |
| FINDING-UI-PIPE-ASYNCIO-DEPRECATION-001 | PIPE-005 uses deprecated `asyncio.get_event_loop().run_until_complete()` (Python 3.10+). Future test hygiene: migrate ws_bridge tests to `pytest-asyncio`. Non-fatal. | WO-UI-PHASE1-PIPE-001 debrief | OPEN — test hygiene WO |
| FINDING-PHASE2-OSS-THIRD-PASS-TARGETS-001 | 5 items from pass 2 — all resolved in pass 3: (1) dnd-generator FOUND — CC0/OGL, phb/ JSON, no parser, see FINDING-PHASE2-OSS-DNDGEN-JSON-001; (2) django-srd20 — Pathfinder only, SKIP; (3) PCGen LST Python parser — moot, dnd-generator covers the need; (4) instructor compat — corrected API documented, see FINDING-PHASE2-OSS-INSTRUCTOR-API-CORRECTION-001; (5) DnD-3.5-SRD-Markdown file structure — moot, demoted to QA reference. | Phase 2 OSS research pass 3 (2026-03-01) | **CLOSED** — all 5 targets resolved |
| FINDING-PHASE2-OSS-ZENLIB-QUEUE-001 | 10 items from OSS research memos identified for ZenLibrary indexing before Phase 2 build WOs: AriGraph paper (IJCAI 2025, HIGH), MemGPT paper (arXiv 2310.08560, HIGH), SimpleMem paper (arXiv 2601.02553, HIGH), simple-graph repo (HIGH), Graphiti design docs (MEDIUM), CALYPSO paper (AIIDE 2024, MEDIUM), instructor docs (MEDIUM), fedefreak92 DM project (LOW). WO-TOOLS-ZENLIB-INDEX-001 exists in pm_inbox — confirm scope covers these research items. | Phase 2 OSS research memos (2026-03-01) | OPEN — check WO-TOOLS-ZENLIB-INDEX-001 scope |

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
| 2026-03-01 | Batch AG ACCEPTED (PM verdict, session 24 — commit 27a7c6d) | n/a | 32/32 gates. Stunning Fist, Crippling Strike, Slippery Mind, Bard Fascinate all IMPLEMENTED. 1 new LOW: FINDING-ENGINE-FLAT-FOOTED-COND-FORMAT-001. Addendum accepted — all 3 form gaps closed (parity blocks, field contract blocks, PM-AN items). Note: builder had pre-populated this entry as "ACCEPTED" before PM verdict (process violation corrected here). |
| 2026-02-28 | Session 23 OSS ingestion audit | FINDING-OSS-FEATS-INGESTION-GAP-001, FINDING-OSS-MONSTERS-INGESTION-GAP-001, FINDING-OSS-SPELLS-INGESTION-GAP-001, FINDING-OSS-EQUIPMENT-INGESTION-GAP-001 | 4 new MEDIUM findings. OSS research sprint (2026-02-26) identified these sources as verified and actionable. LST parser built. Data was hand-typed instead of ingested from sources. Corrective WO required before next data batch. |
| 2026-03-01 | Session 24 OSS sprint dispatch | FINDING-OSS-FEATS-INGESTION-GAP-001, FINDING-OSS-MONSTERS-INGESTION-GAP-001, FINDING-OSS-SPELLS-INGESTION-GAP-001, FINDING-OSS-EQUIPMENT-INGESTION-GAP-001, FINDING-OSS-WEAPON-CATALOG-SPOTCHECK-001 | Sprint spec STRAT-OSS-INGESTION-SPRINT-001.md filed. 4 MEDIUM + 1 spot-check → IN FLIGHT. ML-012 installed in CLAUDE.md. CLASS-TABLES deferred to Sprint 002 (BONUS:VAR architecture required). Exit conditions: 4 conditions per Thunder ruling (sources present, ingestion executed, runtime disposition explicit, artifacts updated). |
| 2026-03-01 | Batch AH ACCEPTED (PM verdict, session 25 — commits 901a9c0 + 5664879) | n/a | 32/32 gates. 15 coverage rows PARTIAL→IMPLEMENTED: 12 skill-bonus feats, Spring Attack, Shot on the Run, Manyshot. filter_aoo_from_target() shared. Manyshot -4 (PHB p.97), two damage_roll events, standard action. CONSUME_DEFERRED: BAB+11/+16 scaling → FINDING-ENGINE-MANYSHOT-BAB-SCALING-001 (LOW) filed. Process violation: builder pre-populated ACCEPTED in PM_BRIEFING_CURRENT.md before PM verdict (2nd occurrence: AG+AH) → FINDING-PROCESS-BUILDER-PRE-ACCEPTED-RECURRING-001 (LOW) filed. |� commits 901a9c0 + 5664879) | n/a | 32/32 gates. 15 coverage rows PARTIAL?IMPLEMENTED: 12 skill-bonus feats (_SKILL_BONUS_FEATS dict: Alertness/Athletic/Acrobatic/Deceitful/Deft Hands/Diligent/Investigator/Negotiator/Nimble Fingers/Persuasive/Self-Sufficient/Stealthy), Spring Attack, Shot on the Run, Manyshot. Shared filter_aoo_from_target() serves Spring Attack + SOTR. Manyshot -4 penalty (not Rapid Shot -2), two damage_roll events on hit, standard action slot. Movement-validity trust-caller pattern on-record. CONSUME_DEFERRED: Manyshot BAB+11/+16 scaling (3rd/4th arrows). 0 new findings. 0 regressions. FINDING-PHASE2-COMPLEX-FEAT-BATCH-001 partial closure noted: Spring Attack, Shot on the Run, Manyshot implemented; Whirlwind Attack remains DEFERRED. |
| 2026-03-01 | Batch AI ACCEPTED (PM verdict, session 25 � commit 840280b) | FINDING-ENGINE-FLAT-FOOTED-COND-FORMAT-001 CLOSED; 3 new LOW filed (FREE-HAND-SETTER-002, WHIRLWIND-REACH-001, RANGE-PENALTY-CONSUME-001) | 32/32 gates. Whirlwind Attack PARTIAL?IMPLEMENTED (N-target delegation to resolve_attack()). Far Shot IMPLEMENTED (compute_range_penalty() utility, integer arithmetic, 1.5x ranged / 2x thrown). Deflect Arrows IMPLEMENTED (reactive gate in resolve_attack(), once-per-round via active_combat list, EF.FREE_HANDS field added). Conditions Format Fix closes FINDING-ENGINE-FLAT-FOOTED-COND-FORMAT-001 � empty-dict bypass via factory yields loses_dex_to_ac=True. Pre-existing failures confirmed by git stash. SWEEP AUDIT NOW DUE (AI = batch 3 of 3). |

---

## 2026-03-01 -- WO-ENGINE-WSP-SCHEMA-FIX-001 findings

### FINDING-ENGINE-WSP-DOUBLE-COUNT-001 (CLOSED -- fixed this WO)
**Description:** attack_resolver.py `_wsp_bonus` added +2 to base_damage AND feat_resolver.get_damage_modifier() also added +2 via feat_context[weapon_name]. Total +4 per hit (double-count). Root cause: _wsp_bonus block was written before feat_resolver WSP path existed. Both paths used weapon_type-based key so neither fired -- double-count was masked. Fixing schema (canonical name key) exposed the double-count.
**Fix:** Removed `base_damage += _wsp_bonus` from attack_resolver.py. feat_resolver is canonical source. `_wsp_bonus` retained for event emission only. zeroed in full_attack_resolver.py (dead-path resolve_single_attack_with_critical, retired by FAGU).
**Status:** CLOSED (fixed WO-ENGINE-WSP-SCHEMA-FIX-001)

### FINDING-ENGINE-WSP-FAR-DEAD-PATH-001 (LOW, OPEN)
**Description:** resolve_single_attack_with_critical() in full_attack_resolver.py still contains WSP logic (now zeroed). Function is dead code -- retired by FAGU delegation. Should be removed in a future cleanup WO. No runtime impact.
**Status:** OPEN -- future cleanup WO


---

## 2026-03-01 -- WO-ENGINE-AOO-ROUND-RESET-001 findings

### FINDING-ENGINE-AOO-CONTROLLER-RESET-DIVERGENCE-001 (LOW, OPEN)
**Description:** aoo_used_this_round + aoo_count_this_round are reset in TWO places: (1) combat_controller.py:346-347 (execute_combat_round path, used by CLI harness) and (2) play_loop.py:4350-4351 (end-of-round block, used by SessionOrchestrator path). The two reset mechanisms are now in sync but are structurally duplicated. Long-term: consolidate reset logic into a single location. Not blocking.
**Status:** OPEN -- future cleanup WO (low priority)

### FINDING-ENGINE-AOO-ACTIVE-COMBAT-AUDIT-001 (LOW, OPEN)
**Description:** Full audit of per-round/per-turn fields in active_combat conducted during this WO. Fields found: aoo_used_this_round (now fixed), aoo_count_this_round (now fixed), deflect_arrows_used (fixed d1fecb4), cleave_used_this_turn (fixed WO-ENGINE-CLEAVE-WIRE-001). No additional uncleared per-round fields found. Audit is complete as of this WO.
**Status:** OPEN (informational -- no action needed unless new per-round fields added)


---

## 2026-03-01 -- WO-UI-PHASE1-DISPLAY-001 findings

### FINDING-UI-DISPLAY-SESSION-STATE-KWARG-001 (LOW, OPEN)
**Description:** SessionStateMsg construction in ws_bridge._build_session_state() fails with `TypeError: ServerMessage.__init__() got an unexpected keyword argument session_id` when called with a real WebSocket (discovered during DS-005/DS-008 integration test harness). Pre-existing construction mismatch between _build_session_state() and SessionStateMsg frozen dataclass. Does not affect gate tests (bypassed via _turn_result_to_messages path). Needs fix before live websocket testing.
**Status:** OPEN -- future WO (LOW priority, Stage 4 scope)

### FINDING-UI-DISPLAY-SPEAKING-WRAP-MULTI-NARRATION-001 (LOW, OPEN)
**Description:** _turn_result_to_messages() has multiple NarrationEvent emission blocks (lines 662, 694, 710, 726, 741, 754, 767, 835). Only the FIRST block (line 662) received speaking_start/stop wrap in this WO. The other blocks (clarification, fallback, spell narration, etc.) do not have speaking_start/stop wrapping. They may fire narration text without triggering orb animation. Stage 3 scope -- clarification/spell narration paths are low-frequency.
**Status:** OPEN -- future WO


---

## 2026-03-01 -- WO-JUDGMENT-SHADOW-001 findings

### FINDING-JUDGMENT-SHADOW-FULL-REGRESSION-HANG-001 (LOW, OPEN)
**Description:** Full test suite (`python -m pytest tests/ -q`) hangs indefinitely (>120s) on pre-existing test infrastructure. The hang predates this WO -- baseline 161 failures implies existing broken tests. Likely culprit: test(s) that block on file I/O, network, or TTS adapter. Not caused by Shadow instrumentation. Targeted gate runs (42 tests) complete in 1.2s cleanly.
**Status:** OPEN -- pre-existing; blocked-test audit needed in future WO.

### FINDING-JUDGMENT-SHADOW-SORT-KEYS-LOG-ONLY-001 (INFO, CLOSED)
**Description:** Shadow log uses sort_keys=True per spec. Confirmed key order in sample: clarification_message, dc, player_action_raw, route_class, routing_confidence, validator_reasons, validator_verdict. Log is append-only, not emitted to game event stream. Event stream contains zero "needs_clarification" or "unroutable_action" events.
**Status:** CLOSED -- documented.
