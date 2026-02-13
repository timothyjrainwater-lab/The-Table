# Reality Reconciliation Table

**Date:** 2026-02-13
**Branch:** master
**Last verified commit:** 99bc913
**Tests:** 5,438 passed / 7 failed (Chatterbox GPU-gated) / 16 skipped (HW-gated)

---

## Purpose

Evidence table preventing stale inventories from driving dispatch. Each row is a claimed gap or feature with file paths, invocation method, test proof, and verified status.

**Status key:**
- **EXISTS** — Fully implemented, tested, invocable
- **PARTIAL** — Code exists but incomplete, untested, or not wired into CLI
- **NOT PRESENT** — Does not exist in codebase

---

## CLI Capabilities (play.py surface)

| Feature | Where in Code | How to Invoke | Test Proof | Status |
|---------|--------------|---------------|------------|--------|
| Single attack | `play.py:214-223` parse, `play.py:324-325` resolve | `attack goblin warrior` | `TestParseInput::test_attack_basic`, `TestResolveAndExecute::test_attack_returns_new_state` | **EXISTS** |
| Full attack | `play.py:198-201` parse, `play.py:326-341` resolve | `full attack goblin warrior` | `TestFullAttack::test_full_attack_resolves` | **EXISTS** |
| Movement | `play.py:226-233` parse, `play.py:342-343` resolve | `move 4 3` | `TestCLISmoke::test_valid_move_shows_destination` | **EXISTS** |
| Spellcasting | `play.py:236-248` parse, `play.py:344-349` resolve | `cast magic missile on goblin` | `TestCLISmoke::test_spell_cast_shows_spell_feedback` | **EXISTS** |
| Combat maneuvers (6) | `play.py:251-265` parse, `play.py:350-373` resolve | `trip goblin`, `bull rush goblin`, `disarm`, `grapple`, `sunder`, `overrun` | `TestManeuvers::test_parse_trip` through `test_trip_resolves` | **EXISTS** |
| Action economy | `play.py:87-183` ActionBudget, `play.py:652-678` enforcement | Automatic per-turn tracking | `TestActionBudget` (15 tests), `TestActionEconomyCLI` (10 tests) | **EXISTS** |
| Round tracking | `play.py:830,940-943` round boundary | Automatic display | `TestRoundTracking` (5 tests) | **EXISTS** |
| Status display (AC/BAB/conditions) | `play.py:632-650` show_status | `status` | `TestExpandedStatus` (5 tests) | **EXISTS** |
| Tactical map | `play.py:653-567` show_map | `map` | `TestTacticalMap` (5 tests) | **EXISTS** |
| AoO display | `play.py:582-598` format_events handlers | Automatic on movement | `TestAoODisplay` (4 tests) | **EXISTS** |
| AC breakdown | `play.py:369-400` format_events attack_roll | Automatic on attack rolls | `TestACBreakdown` (4 tests) | **EXISTS** |
| Character sheet | NOT in play.py | `sheet aldric` (not wired) | None in test_play_cli.py | **NOT WIRED** |
| Spell list | NOT in play.py | `spells` (not wired) | None in test_play_cli.py | **NOT WIRED** |
| Spell slot tracking | NOT in play.py | N/A | N/A | **NOT PRESENT** (blocked on CP) |

---

## Engine Modules (aidm/ surface)

| Feature | Where in Code | Test Proof | Status |
|---------|--------------|------------|--------|
| Character sheet UI | `aidm/ui/character_sheet.py` — CharacterSheetUI, CharacterData, PartySheet | `tests/test_character_sheet_ui.py` (37 tests, all pass) | **EXISTS** — not wired to CLI |
| Canonical IDs (7 namespaces) | `aidm/schemas/canonical_ids.py` (~545 lines) | `tests/test_canonical_ids.py` (56+ tests, all pass) | **EXISTS** — not integrated into production code paths |
| Spell registry (23 spells) | `aidm/data/spell_definitions.py` — SPELL_REGISTRY dict | `tests/test_spell_definitions.py` | **EXISTS** |
| Spell resolver | `aidm/core/spell_resolver.py` — SpellResolver class | `tests/test_spell_resolver.py` (100+ tests) | **EXISTS** |
| AoE rasterizer | `aidm/core/aoe_rasterizer.py` — rasterize_burst/cone/line | `tests/test_aoe_rasterizer.py` (60+ tests) | **EXISTS** |
| Reach/threat resolver | `aidm/core/reach_resolver.py` — get_threatened_squares, can_threaten | `tests/test_reach_resolver.py` (40+ tests) | **EXISTS** |
| Ghost stencil (AoE preview) | `aidm/immersion/ghost_stencil.py` — GhostStencil, create_stencil | Tests exist | **EXISTS** — not wired to CLI |
| Geometry engine / BattleGrid | `aidm/core/geometry_engine.py` — BattleGrid class | `tests/test_geometry_engine.py` (100+ tests) | **EXISTS** |
| Content pack loader | `aidm/lens/content_pack_loader.py` — spell/feat loading from JSON | Tests exist | **EXISTS** |
| Condition system | `aidm/core/conditions.py` — apply_condition, get_condition_modifiers | `tests/test_conditions_kernel.py` | **EXISTS** |
| Full attack resolver | `aidm/core/full_attack_resolver.py` — FullAttackIntent routing | `tests/test_full_attack_resolution.py` | **EXISTS** |
| Combat maneuver resolvers | `aidm/core/play_loop.py:1166-1191` — 6 maneuver routing | `tests/test_combat_maneuvers.py` | **EXISTS** |

---

## Claimed Gaps — Suspect Bucket

These were listed as "gaps" or "blockers" in prior inventories. Verified status:

| Claimed Gap | Prior Claim | Actual Status | Evidence | Verdict |
|-------------|-------------|---------------|----------|---------|
| Canonical ID Schema | "Unscheduled gap, blocks M1/M2/M3" | 7 namespaces implemented, 56+ tests pass | `aidm/schemas/canonical_ids.py`, `tests/test_canonical_ids.py` | **FALSE BLOCKER** — schema exists, production integration is separate work |
| Character sheet UI | "Missing from CLI" | Module exists (37 tests), not wired to play.py | `aidm/ui/character_sheet.py`, `tests/test_character_sheet_ui.py` | **WIRING ONLY** — no new code needed, just plumbing |
| Session persistence | "Missing" | Web server + session store exist | `aidm/runtime/session_persistence.py` | **EXISTS** — not needed for CLI playtest |
| Image critique / Skin packs | "Gap in asset pipeline" | Schema-only (M3 deferred), heuristics L1 partial, no skin pack concept exists | `aidm/schemas/image_critique.py`, `aidm/core/heuristics_image_critic.py` | **PARTIAL (schema)** — not blocking anything in current phase |
| Spell slot tracking | "Blocks infinite casting" | NOT PRESENT — requires CP for entity_fields.py | N/A | **REAL BLOCKER** — CP required |
| Elara's spell list | "Cleric spells undefined" | Registry has 23 spells but Elara has no spell fields in entity state | `aidm/data/spell_definitions.py` has spells; `play_controller.py` Elara entity has no spell fields | **PARTIAL** — registry exists, character binding missing |
| Pathfinding | "Missing for movement" | No pathfinding module exists; current movement is single-step adjacent only | `play.py` StepMoveIntent: single adjacent square | **NOT PRESENT** — but not needed until obstacles/terrain exist |
| structlog / rich terminal | "Logging/display gap" | Not present | N/A | **NOT PRESENT** — optional enhancement, not blocking |
| Audio/voice pipeline | "Chatterbox + speak.py" | speak.py exists with signal parsing, chime, sentence chunking | `scripts/speak.py`, `tests/test_speak_signal.py` | **EXISTS** — voice quality gated on BURST-001 decisions |

---

## Public API Surface for Tactical Snapshot v1

These are the functions play.py can import without touching private APIs:

```
aidm.core.aoe_rasterizer:
  discrete_distance(dx, dy) -> int
  rasterize_burst(origin, radius_ft) -> List[Position]
  rasterize_cone(origin, direction, length_ft) -> List[Position]
  rasterize_line(origin, direction, length_ft) -> List[Position]
  AoEShape, AoEDirection (enums)

aidm.core.reach_resolver:
  get_natural_reach(size, is_long) -> int
  get_threatened_squares(pos, size, reach_ft, w, h) -> List[Position]
  is_square_threatened(entity_pos, size, reach_ft, target_pos) -> bool
  can_threaten(attacker_pos, attacker_size, reach, target_pos, target_size) -> bool

aidm.immersion.ghost_stencil:
  create_stencil(shape, origin, w, h, radius_ft, ...) -> GhostStencil
  confirm_stencil(stencil, caster_id, spell_name) -> FrozenStencil

aidm.ui.character_sheet:
  CharacterSheetUI, CharacterData, PartySheet
```

**Constraint from operator:** No private core APIs (no `_discrete_distance`), no new deps.

---

## Locked Sequencing Spine

1. **Stage 0: Tactical Snapshot v1** — Enhance map with threat overlay, target marker, HP legend. Add `preview` command (template-based). Add distance roster. Add `automap on/off`. No private APIs, no new deps.
2. **Stage 0b (parallel): Character sheet CLI** — Wire `aidm/ui/character_sheet.py` into play.py. Pure plumbing.
3. **Stage 1: Spell resource gate** — Draft+approve CP for entity_fields.py. Then WO-SPELLSLOTS-01 -> WO-SPELLLIST-CLI-01.
4. **Stage 2: Difficulty from tactics** — Encounter spacing, anti-template enemy behavior. Defer pathfinding until obstacles exist.
5. **Voice gated** behind BURST-001 binary decisions.

---

## Gate Rule

This table must be updated with evidence before any "gap" claim drives dispatch. Items in the Suspect Bucket do not graduate to scheduled blockers without file paths + test proof demonstrating they are genuinely NOT PRESENT.
