# PM Briefing — Current

**Last updated:** 2026-02-23. **BURST-001 COMPLETE. CHARGEN PHASE 3 COMPLETE. UI SLICES 0-7 COMPLETE. PRS-01 RC READY.** Gate K 72/72. HOOLIGAN-03 ACCEPTED. **Anvil full UI workload dispatched: 12 WOs across Tier 1-3. WO-WORLDGEN-INGESTION-001 ACCEPTED — Gate INGESTION 15/15. Engine track: 5 WOs dispatched/accepted — CP-17/CP-18/CP-19 (conditions), XP-01 (level-up), V13 (companion wire ACCEPTED 24/24).**

---

## Stoplight: GREEN

6,720+ tests, 0 gate failures, 2 collection errors. **ALL GATES PASS: A-AB, X 9/10, WP, UI-06, V9-V12.** Commit `c7e571e`. P1 PASS. RC READY.

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
|   |       |   |       | UI-06 | 10/10 |
|   |       |   |       | BURST-003 | 10/10 |
|   |       |   |       | BURST-002 | 12/12 |
|   |       |   |       | WP | 5+18+19 |

**Gate test total:** 691 (447 + 88 chargen V7+V8 + 83 chargen V9-V12 + 10 UI-06 + 63 chargen Phase 3). All gates PASS. Chargen gates: V1-V6 114, V7 73, V8 15, V9 20, V10 25, V11 18, V12 20 (285 total). Pre-existing: 2 speak_signal, 3 pm_inbox_hygiene, 1 graduated_critique, 1 immersion_authority; 2 collection errors: heuristics_image_critic, ws_bridge.

## Operator Action Queue (max 3)

1. **Visual confirm spatial fix.** Thunder opens browser — book/notebook flat on shelf? Gates all Tier 1 UI work.
2. **Anvil executing full UI workload.** 12 WOs: Tier 1 (crystal ball, battle scroll, character sheet), Tier 2 (fog of war, dice bag, token slide, session zero, notebook persist), Tier 3 (settings gem, map lasso, cup holder, bestiary bind, rulebook search).
3. **Engine track in flight.** V13 (companion wire) ACCEPTED 24/24. 4 new condition/XP WOs dispatched: CP-17 (15 tests), CP-18 (10 tests), CP-19 (12 tests), XP-01 (14 tests). WO-WORLDGEN-INGESTION-001 ACCEPTED — ingestion step 1 complete, step 2 (double audit) pending.

## Current Focus (Slate's focused recall)

**UI SLICES 0-7 COMPLETE. CHARGEN PHASE 3 COMPLETE. P1 PASS (commit `c7e571e`). RC READY pending HOOLIGAN-03.**
- **UI Slices 3-7 ACCEPTED:** `book-object.ts` (PHB rulebook, page flip, QuestionStamps), `notebook-object.ts` (notes/transcript/bestiary/handouts), `handout-object.ts` (printer slot + tray 1.6×1.3m navy felt + fanstack + discard ring), `map-overlay.ts` (AoE shapes, measure line, area highlight), `entity-renderer.ts` (+getTokenMeshes), `main.ts` (all slices wired), `index.html` (AoE gate). Gate G 22/22.
- **Zone realignment:** `zones.json` player centerZ=4.75/halfHeight=0.80 (shelf), dice_tray z=1.75, dice_tower z=0.5. Gate G zone test updated to match.
- **Chargen Phase 3 COMPLETE:** V9 level_up() 20/20, V10 companions 25/25, V11 racial traits 18/18, V12 dual-caster 20/20. `build_animal_companion()` live. All 7 PHB races have mechanical trait EF fields. `_merge_spellcasting()` handles 0/1/2 caster classes. V9 `level_up()` pure delta, CLASS_FEATURES 11 classes, seeded HP roll.
- **UI-06 ACCEPTED:** `entity-renderer.ts` EntityRenderer class, faction-colored tokens, HP bar, gridToScene(), Gate UI-06 10/10.
- **PRS-01:** RC READY. All gates clean. Dirty tree resolved (commit `c7e571e`).

**Deferred:** Chatterbox swap timing (8.0s budget). GAP-B HIGH (VS Build Tools). FINDING-WORLDGEN-IP-001.

**Active dispatches:** Anvil — WO-UI-ANVIL-FULL-WORKLOAD_20260223.md (12 WOs: crystal ball, battle scroll, character sheet, fog of war, dice bag, token slide, session zero, notebook persist, settings gem, map lasso, cup holder, bestiary bind, rulebook search). Prerequisite: spatial fix visual confirm.

**CHARGEN PHASE 3 COMPLETE:** V10 (companions 25/25) + V11 (racial traits 18/18) + V12 (dual-caster 20/20). `build_animal_companion()` live. All 7 PHB races have mechanical trait fields. `_merge_spellcasting()` handles 0/1/2 caster classes. Dual-caster: alphabetical primary (`cleric < wizard`), separate `_2` suffix fields for secondary. `spell_choices_2` param on `build_character()`. 3+ casters raises ValueError.

**BURST-001:** ~~Tier 1~~ → ~~Tier 2~~ → ~~RV-007~~ → ~~Tier 3~~ → ~~Tier 4~~ → ~~Tier 5.1-5.4~~ → ~~**5.5 Playtest v1 — ACCEPTED**~~ **BURST-001 COMPLETE.**
**PRS-01:** ~~Spec review~~ → ~~5 WOs dispatched~~ → ~~**5/5 ACCEPTED**~~ → ~~**SCAN FIX ACCEPTED**~~ → ~~pre-RC cleanup~~ → ~~**ALL GATES GREEN**~~ → ~~**ORCHESTRATOR ACCEPTED**~~ → **commit + IP remediation (WO-PRS-IP-001) → RC READY**
**UI:** ~~WO-UI-01~~ → ~~WO-UI-02~~ → ~~WO-UI-03~~ → ~~WO-UI-04~~ → ~~WO-UI-05 ACCEPTED pending visual~~ (table surface + atmosphere) → **WO-UI-06 DISPATCHED** (entity tokens, HP bars, live WS bridge)
**CHARGEN:** ~~Research~~ → ~~Foundation~~ → ~~Skills~~ → ~~Classes~~ → ~~Feats~~ → ~~Spellcasting~~ → ~~Spell Expansion~~ → ~~**Builder Capstone**~~ → ~~**CHARGEN PHASE 1 COMPLETE**~~ → ~~**WO-CHARGEN-EQUIPMENT-001 (V7 73/73)**~~ → ~~**WO-CHARGEN-MULTICLASS-001 (V8 15/15)**~~ → ~~**CHARGEN PHASE 2 COMPLETE**~~ → ~~WO-CHARGEN-PHASE3-LEVELUP (Gate V9)~~ → ~~**WO-CHARGEN-DUALCASTER-001 (V12 20/20)**~~ → ~~**WO-CHARGEN-COMPANION-001 (V10 25/25)**~~ → ~~**WO-CHARGEN-RACIAL-001 (V11 18/18)**~~ → **CHARGEN PHASE 3 COMPLETE**

## Open Findings

| Finding | Severity | Status | Description |
|---------|----------|--------|-------------|
| FINDING-SCAN-BASELINE-01 | MEDIUM | RESOLVED | Gate X: base64 false positives fixed (P5 skip list). `*.jsonl` on asset allowlist. X-01 remains: real tracked artifacts (`models/voices/`, `inbox/`). Gate X 9/10. |
| FINDING-ORC-P8-001 | MEDIUM | RESOLVED | P8: 296 violations → 0. 59 exceptions in `ip_exceptions.txt` (provenance docs, test fixtures, PM tooling). 4 content removals (README Vecna/Heironeous, npc_stingers Waterdeep×2). |
| FINDING-ORC-P1-001 | LOW | RESOLVED | P1 dirty tree resolved. Commit `9bf1d3d`. |
| FINDING-UI05-P2-001 | MEDIUM | RESOLVED | WO-UI-05: scene-builder.ts Math.random replaced with seeded PRNG (`makePrng`). Gate G 22/22 PASS. W-01–W-14 PASS. W-15 fails due to V7 test gap (equipment tests exist, not WO-UI-05 scope). Visual gate pending Thunder review. |
| FINDING-PLAYTEST-F01 | MEDIUM | OPEN | TTS env not provisioned. Neither Chatterbox nor Kokoro installed. 7 TTS-dependent checkpoints validated by proxy (unit tests). Live audio deferred. |
| FINDING-HOOLIGAN-03 | MEDIUM | RESOLVED | WO-FIX-HOOLIGAN-03 ACCEPTED. `_check_rv001_hit_miss()` scoped to first sentence via `. ` split. Gate K 69→72 (49/49 narration validator). FINDING-HOOLIGAN-03 RESOLVED. |
| FINDING-CHARGEN-SKILLS-01 | MEDIUM | RESOLVED | Anvil skills WO (`8a9442a`) broke 4 tests (not 3 as originally reported): stale hardcoded counts. Fixed by Thunder. |
| FINDING-GRAMMAR-01 | LOW | RESOLVED | WO-FIX-GRAMMAR-01 ACCEPTED. `play.py:647` `.title()` appended. Gate K 67→69. 2 regression tests. |
| FINDING-SIGLIP-01 | LOW | RESOLVED | `test_siglip_critique.py` merge conflicts resolved by Anvil (`20797a9`) |
| GAP-A | LOW | RESOLVED | `dm_persona.py` missing import fixed via `TYPE_CHECKING` guard — no runtime BL violation. Boundary law test PASS. |
| GAP-B | HIGH | OPEN | llama-cpp-python blocks Qwen3/Gemma3 (needs VS Build Tools) |
| FINDING-WORLDGEN-IP-001 | HIGH | OPEN | Source material names (Mind Flayer, Beholder, etc.) are retained in internal data as **audit anchors** — required for accuracy verification against source. Names cannot be stripped until: (1) source ingestion is complete ✅ **WO-WORLDGEN-INGESTION-001 ACCEPTED — Gate INGESTION 15/15. `ingestion_report.json` baseline: 273 creatures, 605 spells, 109 feats. 7 field-length warnings (environment_tags/alignment_tendency >100 chars on 7 creatures) recorded as double-audit subjects — non-blocking.**, (2) double audit confirms every mechanical value (HP, AC, attacks, abilities) matches source material exactly, (3) strip replaces names with IDs. Only after strip is complete can World Gen LLM mode be enabled to apply new skin. Additionally: no post-generation IP scan exists before bundle commit (Recognition Test in `WORLD_COMPILER.md §2.1` specified but not gated). **Full pre-condition chain:** ~~ingestion complete~~ → double audit PASS → name strip → IP scan gate on bundle output → LLM mode enabled. Not a current RC blocker — RC ships stub mode (IDs already). PRS-01 amendment candidate for bundle scan gate. |

## Inbox

- **[ACCEPTED] [WO-WORLDGEN-INGESTION-001_DISPATCH.md](pm_inbox/WO-WORLDGEN-INGESTION-001_DISPATCH.md)** — Content pack ingestion stage (Gate INGESTION 15/15). Step 1 of FINDING-WORLDGEN-IP-001 chain. Baseline: 273 creatures, 605 spells, 109 feats.
- **[DEBRIEF] [WO-FIX-GRAMMAR-01_DEBRIEF.md](pm_inbox/WO-FIX-GRAMMAR-01_DEBRIEF.md)** — ACCEPTED. play.py:647 `.title()`. Gate K 69/69. BL fix applied.
- **[DISPATCH] [WO-ENGINE-LEVELUP-WIRE_DISPATCH.md](pm_inbox/WO-ENGINE-LEVELUP-WIRE_DISPATCH.md)** — XP award + level-up post-combat dispatcher. `check_level_up()` stub → full. `_award_xp_for_defeat()` helper in play_loop.py. `xp_awarded` + `level_up_applied` events. Gate XP-01 14 tests.
- **[DISPATCH] [WO-ENGINE-CONDITION-ENFORCE_DISPATCH.md](pm_inbox/WO-ENGINE-CONDITION-ENFORCE_DISPATCH.md)** — CP-17: action gate, prone-stand AoO, helpless auto-hit, loses-DEX-to-AC. ACTION_DENIED sensor event. Gate CP-17 15 tests.
- **[DISPATCH] [WO-ENGINE-CONDITION-SAVES_DISPATCH.md](pm_inbox/WO-ENGINE-CONDITION-SAVES_DISPATCH.md)** — CP-18: condition save modifiers (shaken/sickened -2) wired into SpellResolver._resolve_save(). STP transparency. Gate CP-18 10 tests.
- **[DISPATCH] [WO-ENGINE-CONDITION-DURATION_DISPATCH.md](pm_inbox/WO-ENGINE-CONDITION-DURATION_DISPATCH.md)** — CP-19: DurationTracker.tick_round() called at round end. condition_expired events. Conditions auto-remove on expiry. Gate CP-19 12 tests.
- **[DISPATCH] [WO-UI-ANVIL-FULL-WORKLOAD_20260223.md](pm_inbox/WO-UI-ANVIL-FULL-WORKLOAD_20260223.md)** — Anvil full UI workload: 12 WOs across Tier 1-3 (crystal ball, battle scroll, character sheet, fog of war, dice bag, token slide, session zero, notebook persist, settings gem, map lasso, cup holder, bestiary bind, rulebook search).
- **[DISPATCH] [WO-CHARGEN-PHASE3-LEVELUP_DISPATCH.md](pm_inbox/WO-CHARGEN-PHASE3-LEVELUP_DISPATCH.md)** — Level-up flow: level_up() delta function, CLASS_FEATURES table, Gate V9 15 tests
- **[DISPATCH] [WO-CHARGEN-PHASE3_DISPATCH.md](pm_inbox/WO-CHARGEN-PHASE3_DISPATCH.md)** — Phase 3 chargen: dual-caster merging (V10, 20 tests), animal companions (V11, 25 tests), racial trait encoding (V12, 18 tests). 63 tests total. V11+V12 are parallel-dispatchable.
- **[DISPATCH] [WO-FIX-GRAMMAR-01_DISPATCH.md](pm_inbox/WO-FIX-GRAMMAR-01_DISPATCH.md)** — Condition display title-case fix (play_loop.py, 1-line, 1 regression test)
- **[DISPATCH] [WO-BURST-003-AOE-001_DISPATCH.md](pm_inbox/WO-BURST-003-AOE-001_DISPATCH.md)** — AoE confirm-gated overlay (10 tests, `PendingAoE`, ASCII preview, yes/cancel parser)
- **[DISPATCH] [WO-BURST-002-RESEARCH-001_DISPATCH.md](pm_inbox/WO-BURST-002-RESEARCH-001_DISPATCH.md)** — Spark runtime constraint envelope (SparkFailureMode, SLA constants, template fallback, TTFT, 12 tests)
- **[DISPATCH] [WO-FIX-HOOLIGAN-03_DISPATCH.md](pm_inbox/WO-FIX-HOOLIGAN-03_DISPATCH.md)** — RV-001 compound narration fix (Gate K 67→70)
- **[READ] [MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md](pm_inbox/MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md)** — TTS pipeline reference
- **[READ] [MEMO_BUILDER_PREFLIGHT_CANARY.md](pm_inbox/MEMO_BUILDER_PREFLIGHT_CANARY.md)** — Preflight canary system
- **[READ] [TUNING_001_PROTOCOL.md](pm_inbox/TUNING_001_PROTOCOL.md)** — TUNING-001 observation protocol (research, not build)
- **[READ] [TUNING_001_LEDGER.md](pm_inbox/TUNING_001_LEDGER.md)** — TUNING-001 session ledger
- **[ACCEPTED] [WO-UI-05_DISPATCH.md](pm_inbox/WO-UI-05_DISPATCH.md)** — Table surface + atmosphere (walnut, felt vault, candlelight, stubs, shadows)
- **[ACCEPTED] [WO-PRS-IP-001_DISPATCH.md](pm_inbox/WO-PRS-IP-001_DISPATCH.md)** — P8 PASS: 59 exceptions + 4 content removals. 296 violations → 0.
- **[ACCEPTED] [WO-CHARGEN-EQUIPMENT-001_DISPATCH.md](pm_inbox/WO-CHARGEN-EQUIPMENT-001_DISPATCH.md)** — Phase 2: equipment integrated (Gate V7 73/73)
- **[ACCEPTED] [WO-CHARGEN-MULTICLASS-001_DISPATCH.md](pm_inbox/WO-CHARGEN-MULTICLASS-001_DISPATCH.md)** — Phase 2: multiclass `class_mix` param (Gate V8 15/15)
- **[DRAFTED] [PUBLISHING_READINESS_SPEC.md](docs/contracts/PUBLISHING_READINESS_SPEC.md)** — PRS-01 FROZEN (v1.0 ACCEPTED 2026-02-23)

## WO Verdicts (most recent 15 — older entries archived)

| WO | Verdict | Commit |
|---|---|---|
| WO-ENGINE-COMPANION-WIRE | **ACCEPTED** — 24/24 Gate V13. `aidm/core/companion_resolver.py`: `spawn_companion()` pure function + `SummonCompanionResult` dataclass. `SummonCompanionIntent` in `aidm/schemas/intents.py` with `parse_intent()` routing. `execute_turn()` in `play_loop.py` wired: actor resolution → `spawn_companion()` → `add_entity` event → `reduce_event()` → companion lands in WorldState. Fail-closed: invalid_type/invalid_actor/actor_not_found/already_active all emit `intent_validation_failed`. New EF: `COMPANION_OWNER_ID`, `COMPANION_TYPE`. Replay-safe: `add_entity` reducer in MUTATING_EVENTS. 6,774 suite-wide, 0 new regressions. | (pending commit) |
| WO-WORLDGEN-INGESTION-001 | **ACCEPTED** — 15/15 Gate INGESTION. `IngestionStage` in `aidm/core/compile_stages/ingestion.py`. Loads `ContentPackLoader.from_directory()`, classifies validation errors (structural=blocking IC-002, field-length=non-blocking warnings), writes `ingestion_report.json` with content_hash + entity counts. Real pack baseline: 273 creatures, 605 spells, 109 feats; 7 field-length warnings (environment_tags and alignment_tendency >100 chars on 7 creatures — non-blocking, logged for double-audit). Structural errors: 0. IC-001 on missing dir. Dependency chain: `IngestionStage` → downstream stages. Zero regressions (world_compiler 51/51, world_archive 24/24). FINDING-WORLDGEN-IP-001 step 1 ✅. | (pending commit) |
| WO-FIX-HOOLIGAN-03 | **ACCEPTED** — Gate K 72/72 (69+3). `_check_rv001_hit_miss()` scoped to first sentence: `first_sentence = text.split(". ")[0] if ". " in text else text`. K-68: compound hit no false positive. K-69: compound miss no false positive. K-70: single-sentence real violation still caught. 6,702 passed suite-wide, 11 pre-existing failures, 0 new regressions. FINDING-HOOLIGAN-03 RESOLVED. | (pending commit) |
| WO-UI-06 | **ACCEPTED** — 10/10 Gate UI-06. `entity-renderer.ts`: EntityRenderer class, faction-colored cylinders (player gold/enemy red/npc blue), HP bar (green→red lerp), `gridToScene()` (1 grid=0.5 scene, y=0.08), `upsert()`/`remove()`/`syncRoster()`, `getTokenMeshes()`/`getEntityIdByMesh()`/`getEntityFaction()`. `main.ts` wired: `entity_state`→`syncRoster`, `entity_delta`→`upsert`/`remove`. `demo_entity_tokens.py` provided. | `c7e571e` |
| WO-UI-SLICES-3-7 | **ACCEPTED** — Doctrine §19 Slices 3-7. `book-object.ts` (PHB rulebook, flipForward/flipBack, openToRef, QuestionStamp). `notebook-object.ts` (notes/transcript/bestiary/handouts, addTranscriptEntry, setSection). `handout-object.ts` (printer slot z=3.82 brass rim, HandoutTray 1.6×1.3m navy felt at z=4.60, fanstack 5-deep, discard ring at trash_hole). `map-overlay.ts` (AoE shapes, MeasureLine, AreaIndicator, pulse). `main.ts` all slices wired. `index.html` AoE confirm gate. Zones.json player centerZ=4.75. Gate G 22/22. | `c7e571e` |
| WO-CHARGEN-PHASE3-LEVELUP | **ACCEPTED** — 20/20 Gate V9. `level_up(entity, class_name, new_class_level, ...)` pure delta function in `builder.py`. `CLASS_FEATURES` dict (11 classes, PHB L1-20). `_roll_hp_for_level()` seeded RNG, min 1, max on first class level. `_skill_points_for_level()` per-class table + INT mod. Delta shape: hp_gained, feat_slots_gained, feats_added, class_features_gained, spell_slots, skill_points_gained, bab, saves, new_total_level. Pure — no entity mutation. | `c7e571e` |
| WO-CHARGEN-DUALCASTER-001 | **ACCEPTED** — 20/20 Gate V12. `_merge_spellcasting()` refactored: 0/1/2 caster branching, 3+ raises ValueError. Alphabetical primary. `SPELL_SLOTS_2/CASTER_LEVEL_2/CASTER_CLASS_2/SPELLS_PREPARED_2/SPELLS_KNOWN_2` for secondary. `spell_choices_2` param on `build_character()`. 6 new EF constants. Zero regressions. | `c7e571e` |
| WO-CHARGEN-COMPANION-001 | **ACCEPTED** — 25/25 Gate V10. `build_animal_companion()` in `aidm/chargen/companions.py`. 5 types: wolf, riding_dog, eagle, light_horse, viper_snake. PHB Table 3-4 (7 rows). Effective companion level: druid_lvl + max(0, ranger_lvl−3). Multiattack at eff_lvl ≥ 4. No SPELL_SLOTS/INVENTORY. ENTITY_ID traceable to parent. | `c7e571e` |
| WO-CHARGEN-RACIAL-001 | **ACCEPTED** — 18/18 Gate V11. `apply_racial_trait_fields()` in `races.py`. 11 new EF constants. All 7 PHB races encoded — fields absent (not zero) for races without the trait. | `c7e571e` |
| WO-BURST-003-AOE-001 | **ACCEPTED** — 10/10 Gate BURST-003. `PendingAoE` frozen dataclass, `WorldState.pending_aoe` (excluded from state_hash/to_dict — ephemeral UI state). `_show_aoe_preview()`: @ origin, * AoE, ! entities at risk. `_confirm_aoe()` resolves via execute_turn, emits AOE_PREVIEW_CONFIRMED. Parser intercepts yes/cancel when pending_aoe active. State-safe on restart: field is None on fresh load, spell never resolved. | (pending commit) |
| WO-BURST-002-RESEARCH-001 | **ACCEPTED** — 12/12 Gate BURST-002. `SparkFailureMode` enum (6 modes), `SPARK_SLA_PER_CALL` per CallType (timeout_s, p95_target_s), `TEMPLATE_NARRATION` deterministic fallback, TTFT measurement + degraded field in SparkAdapter, prep_pipeline asset-level catch + prep_failed status. Sensor event on runtime failure. Zero new regressions (12 pre-existing failures confirmed as baseline). | (pending commit) |
| WO-FIX-GRAMMAR-01 | **ACCEPTED** — Gate K 69/69 (67+2). `play.py:647`: `.replace('_',' ')` → `.replace('_',' ').title()`. 1 hit total in file. 2 regression tests appended to `test_unknown_gate_k.py`. FINDING-GRAMMAR-01 RESOLVED. GAP-A BL fix: `TYPE_CHECKING` guard on `NarrativeBrief` import — boundary law PASS. | (pending commit) |
| WO-CHARGEN-MULTICLASS-001 | **ACCEPTED** — 15/15 Gate V8. `class_mix={"fighter":3,"wizard":2}` param added to `build_character()`. BAB = max across classes (fighter3/wizard2 → BAB 3). Saves = best per save independently. HP = sum of HD per class. Skill points = sum per class. Class skills = union. `favored_class` stored informational. Validation: ValueError on total>20, unknown class, ambiguous params. Multi-caster decision: first caster in mix wins (wizard/cleric → wizard slots only); dual-caster merge deferred. BAB/save table verified vs PHB p.57. Zero V1-V6 regressions. | `9bf1d3d` |
| WO-CHARGEN-EQUIPMENT-001 | **ACCEPTED** — 73/73 Gate V7. `_assign_starting_equipment()` wired into `build_character()`. All 11 classes: inventory, weapon, real AC. AC table: barbarian 14, bard 13, cleric 15, druid 14, fighter 16, monk 12 (WIS mod applied), paladin 16, ranger 13, rogue 13, sorcerer 11, wizard 11. Monk: unarmed (no weapon field), WIS-to-AC applied. Druid: hide armor (no metal). Arcane casters: quarterstaff, no armor. Encumbrance calculated. Spell component pouch for all 5 caster classes. `starting_equipment` override works. Zero chargen regressions. | `9bf1d3d` |
| WO-UI-05 | **ACCEPTED** — scene-builder.ts delivered + visual gate passed (Thunder direct iteration). Walnut table (procedural grain canvas texture, seeded PRNG), recessed felt vault, player shelf, trash hole + brass ring, cup holder, warm candlelight (3 PointLights + map spot + tray fill + HemisphereLight + ambient), per-lantern flicker, 7 object stubs (crystal ball on pedestal with glow + pulse, dice tower, character sheet with full D&D 3.5e layout, notebook, tome, parchment, d6s). Math.random → `makePrng()` seeded LCG. Gate G 22/22 PASS. | `9bf1d3d` |
| WO-PRS-IP-001 | **ACCEPTED** — P8 PASS: 0 violations (was 296). 59 exceptions in `ip_exceptions.txt` (Groups A-E: provenance docs, internal audit, test fixtures, PM tooling). 4 content removals: README (Vecna → "lich's cult", Heironeous → "lawful_deity"), npc_stingers.json (Waterdeep × 2 → Ironport). Playwright venv exception added to `offline_exceptions.txt`. P2 FAIL from WO-UI-05 parallel track (scene-builder.ts Math.random + salience) — not PRS scope. | (uncommitted) |
| WO-PRS-ORCHESTRATOR-001 | **ACCEPTED** — `build_release_candidate_packet.py` live. P1-P9 sequential runner, `RC_PACKET/MANIFEST.md` generated. Smoke: P2/P3-P7/P9 PASS, 6448 tests. P1 FAIL (dirty tree — pre-commit). P8 FAIL (292 IP violations — pre-existing, now fixed by WO-PRS-IP-001). | (uncommitted) |
| WO-PRS-SCAN-FIX-001 | **ACCEPTED** — Gate X 8/10→9/10. `SECRET_SCAN_SKIP_FILES` for base64 false positives (X-04 FIXED). `*.jsonl` on asset allowlist. X-01 remains: real tracked artifacts (pre-RC cleanup). | (uncommitted) |
| WO-PRS-DOCS-001 | **ACCEPTED** — 6/6 Gate AB. `docs/PRIVACY.md` (4 sections per PRS-01 §7), `docs/OGL_NOTICE.md` (full OGL v1.0a + Section 15), `scripts/publish_check_docs.py` (validator), gate tests. Zero new failures. | (uncommitted) |
| WO-PRS-SCAN-001 | **ACCEPTED with finding** — 8/10 Gate X (P3+P5+P8). Scanner architecture sound. FINDING-SCAN-BASELINE-01: base64 false positives in `package-lock.json`/`REUSE_DECISION.json`, `.jsonl` not on allowlist, `models/` tracked in git. Fix WO needed. | (uncommitted) |
| WO-PRS-LICENSE-001 | **ACCEPTED** — 6/6 Gate Y, 13 deps (9 Python + 4 Node), all permissive, schema valid, 4-layer validation. Unicode fix for Windows cp1252. | (uncommitted) |
| WO-PRS-OFFLINE-001 | **ACCEPTED** — 7/7 Gate Z, static scanner (network import detection + exceptions) + runtime smoke (socket monkey-patch). 7 exceptions documented. Defense-in-depth. | `b037df3` |
| WO-PRS-FIRSTRUN-001 | **ACCEPTED** — 7/7 Gate AA, fail-closed validation for model weights + TTS voices. Inverted exit semantics. | `3c6dac2` |
| WO-CHARGEN-BUILDER-001 | **ACCEPTED** — 25 Gate V6, `build_character(race, class, level)` capstone. All 11 classes × 7 races × L1-20. Ability scores, racial mods, HP, BAB, saves, skills, feats, spellcasting. | `54a1639` |
| WO-CHARGEN-SPELL-EXPANSION | **ACCEPTED** — 8 Gate V5, 28 spells for levels 6-9 (7 per level), class spell lists updated. | `60544a1` |
| WO-CHARGEN-SPELLCASTING | **ACCEPTED** — 15 Gate V4, spell-per-day tables for 7 caster classes, spells-known for sorcerer/bard, bonus spells from ability scores. | `fd82578` |
| WO-CHARGEN-FEATS-COMPLETE | **ACCEPTED** — 15 Gate V3, 66 PHB feats (51 new + 15 existing), prerequisite chains, save/skill/spell/proficiency/mounted/combat feats. | `5014834` |
| WO-CHARGEN-CLASSES-COMPLETE | **ACCEPTED** — 12 Gate V2, 11 PHB classes with class_skills + starting_gold_dice. | `335e404` |
| WO-IMPL-PRESSURE-ALERTS-001 | **ACCEPTED** — 22 Gate V, `apply_pressure_modulation()` on ProsodicPresetManager, pressure_level param on `_synthesize_tts()`. | `83f1674` |
| WO-IMPL-SALIENCE-FILTER-001 | **ACCEPTED** — 14 Gate W, `aidm/voice/line_classifier.py` (LineType enum, classify_line, filter_spoken_lines). **TIER 4 COMPLETE.** | `a3d06d3` |
| WO-CHARGEN-FOUNDATION-001 | **ACCEPTED** — 20 Gate U, ability scores, 7 PHB races, weapon/armor catalog. | `90c204e` |
| WO-VOICE-PAS-PRESETS-001 | **ACCEPTED** — 23 Gate T, 4 mode presets, ProsodicPresetManager + SessionOrchestrator. | `bb93890` |
| WO-VOICE-PAS-FIELDS-001 | **ACCEPTED** — 31 Gate S, 6 prosodic fields + 4 enums on VoicePersona. | `8df5718` |

**Full verdict history:** `reviewed/BRIEFING_ARCHIVE_GRADUATION_20260222.md` (18 older entries archived)

## Dispatches (most recent 15 — older entries archived)

- **[DISPATCHED] WO-ENGINE-LEVELUP-WIRE** — XP award + level-up post-combat dispatcher. Complete `check_level_up()` stub in experience_resolver.py. `_award_xp_for_defeat()` helper called after entity_defeated events. `xp_awarded` + `level_up_applied` events. Gate XP-01 14 tests.
- **[DISPATCHED] WO-ENGINE-CONDITION-ENFORCE** — CP-17: actions_prohibited gate (execute_turn early exit), prone-stand AoO trigger (standing_triggers_aoo flag), helpless auto-hit in attack_resolver.py (melee only), loses_dex_to_ac in AC calculation. ACTION_DENIED sensor event with condition reason. Gate CP-17 15 tests. Note: existing actions_prohibited gate at play_loop.py:804 is a partial implementation — harden to cover all flagged conditions.
- **[DISPATCHED] WO-ENGINE-CONDITION-SAVES** — CP-18: condition save modifiers (fort/ref/will) wired into SpellResolver._resolve_save(). `condition_save_mod: int = 0` param. STP modifiers list includes penalty. Gate CP-18 10 tests.
- **[DISPATCHED] WO-ENGINE-CONDITION-DURATION** — CP-19: DurationTracker.tick_round() wired into execute_turn() at round-end boundary (last actor's turn). condition_expired events with spell attribution. Gate CP-19 12 tests.
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

**Root** (15 files — 10 operational + 3 PRS-01 dispatches + 2 chargen Phase 2 drafts):
- [PM_BRIEFING_CURRENT.md](pm_inbox/PM_BRIEFING_CURRENT.md) — This file
- [REHYDRATION_KERNEL_LATEST.md](pm_inbox/REHYDRATION_KERNEL_LATEST.md) — PM rehydration block
- [README.md](pm_inbox/README.md) — Inbox hygiene rules
- [BURST_INTAKE_QUEUE.md](pm_inbox/BURST_INTAKE_QUEUE.md) — BURST-001 thru 004 (BURST-001 COMPLETE)
- [MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md](pm_inbox/MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md) — TTS pipeline reference
- [MEMO_BUILDER_PREFLIGHT_CANARY.md](pm_inbox/MEMO_BUILDER_PREFLIGHT_CANARY.md) — Preflight canary system
- [PREFLIGHT_CANARY_LOG.md](pm_inbox/PREFLIGHT_CANARY_LOG.md) — Builder preflight log
- [TUNING_001_PROTOCOL.md](pm_inbox/TUNING_001_PROTOCOL.md) — Coupled-coherence observation protocol
- [TUNING_001_LEDGER.md](pm_inbox/TUNING_001_LEDGER.md) — Session ledger + analysis framework
- [WSM_01_WATCH_SYNC.md](pm_inbox/WSM_01_WATCH_SYNC.md) — Watch Sync Memo (active operational)
- [WO-PRS-IP-001_DISPATCH.md](pm_inbox/WO-PRS-IP-001_DISPATCH.md) — P8 IP exceptions (in flight)
- [WO-UI-05_DISPATCH.md](pm_inbox/WO-UI-05_DISPATCH.md) — Table surface visual (in flight)
- [WO-CHARGEN-EQUIPMENT-001_DISPATCH.md](pm_inbox/WO-CHARGEN-EQUIPMENT-001_DISPATCH.md) — Phase 2 equipment (drafted, ready to dispatch)
- [WO-CHARGEN-MULTICLASS-001_DISPATCH.md](pm_inbox/WO-CHARGEN-MULTICLASS-001_DISPATCH.md) — Phase 2 multiclass (drafted, ready to dispatch)
- [WO-PRS-SCAN-001_DISPATCH.md](pm_inbox/WO-PRS-SCAN-001_DISPATCH.md) — Gate X original dispatch (accepted w/ finding)
- [WO-PRS-SCAN-FIX-001_DISPATCH.md](pm_inbox/WO-PRS-SCAN-FIX-001_DISPATCH.md) — Gate X fix WO (READY TO DISPATCH)
- [WO-PRS-DOCS-001_DISPATCH.md](pm_inbox/WO-PRS-DOCS-001_DISPATCH.md) — Gate AB dispatch (PARTIAL — awaiting builder)
- [MEMO_HORIZON_SCOPE_AUDIT_2026_02_22.md](pm_inbox/MEMO_HORIZON_SCOPE_AUDIT_2026_02_22.md) — Horizon scope audit

**Archived this session:** 7 files → `reviewed/` (FIRSTRUN dispatch, LICENSE dispatch+debrief, OFFLINE dispatch+debrief, BURST playtest draft+report)

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
