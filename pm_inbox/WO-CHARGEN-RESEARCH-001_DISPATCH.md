# WO-CHARGEN-RESEARCH-001 — Character Generation Walkthrough & Gap Analysis

**Type:** RESEARCH
**Lifecycle:** NEW
**Priority:** Parallel track (does not block BURST-001)
**Assigned:** Thunder (Operator) + Anvil (Squire)
**PM:** Slate (verdict authority)

---

## Target Lock

Walk through full D&D 3.5 character generation for two level 3 PCs using PHB rules. At every decision point, identify whether the codebase supports it. Produce a gap register and a pair of combat-ready entity dicts. Acceptance test: the two PCs fight each other in a PvP arena using the existing combat engine.

## Binary Decisions

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | How many characters? | 2 — enough to PvP test | Operator directive |
| 2 | Level? | 3 — matches existing fixture baseline | `build_simple_combat_fixture()` |
| 3 | Stat generation method? | 4d6-drop-lowest (standard) — document point-buy gap separately | PHB p.7 |
| 4 | Allowed classes? | Any PHB core class — the 4 with progression tables (Fighter, Rogue, Cleric, Wizard) are preferred for gap analysis depth | `leveling.py` |
| 5 | Equipment? | Standard PHB starting gold by class, selected from equipment catalog | `equipment_catalog.json` |
| 6 | Do we build the missing code? | **No.** This is RESEARCH. Document gaps only. Builder WOs come from the gap register. | Two-Force Model |

## Walkthrough Steps (PHB Chapter 2 order)

For each PC, walk through these steps. At each step, record: (a) what the player chose, (b) whether the codebase supports it, (c) if not, what's missing (gap ID + severity).

### Step 1: Ability Scores
- Roll 4d6 drop lowest, six times, assign to stats
- **Known gap:** No stat generation code exists. `DeterministicDice` can roll 4d6 but no "drop lowest" helper.
- Record: raw rolls, assignment choices, final scores

### Step 2: Race
- Choose PHB race (Human, Dwarf, Elf, Gnome, Half-Elf, Half-Orc, Halfling)
- Apply racial ability modifiers, racial traits, size, speed, languages
- **Known gap:** No race definitions exist. `entity_fields.py` has no RACE field. No racial modifier application.
- Record: race choice, which modifiers/traits apply, what's missing

### Step 3: Class
- Choose class, record class features for level 1-3
- Apply hit die, BAB progression, save progression, class features
- **Exists:** `leveling.py` has Fighter/Rogue/Cleric/Wizard progressions
- Record: class choice, which features the code handles, which are missing

### Step 4: Skill Points
- Calculate skill points per level (class base + INT mod)
- Allocate ranks (max = level + 3 for class skills, half for cross-class)
- **Partial:** 7 combat skills defined in `skills.py`. Rank storage exists. No allocation enforcement.
- Record: skill point budget, allocation choices, what enforcement is missing

### Step 5: Feats
- Select feats based on class + level slots
- Validate prerequisites
- **Exists:** 109 feats in registry, prerequisite validation in `feat_resolver.py`
- Record: feat choices, whether prereqs validate correctly

### Step 6: Equipment
- Roll starting gold by class
- Purchase from equipment catalog
- **Exists:** `equipment_catalog.json` with PHB items
- Record: gold roll, purchases, any missing items

### Step 7: Derived Values
- Compute: AC, HP, attack bonus, saves, initiative, skill modifiers
- **Exists:** Most derivation logic in `character_sheet.py`, `attack_resolver.py`
- Record: all derived values, verify against PHB expectations

### Step 8: Entity Dict Assembly
- Assemble a complete entity dict using `EF.*` field constants
- Verify it can be injected into a WorldState
- Record: full entity dict, any missing fields

## Acceptance Test

1. Create a WorldState with both PCs on opposing teams
2. Run combat using existing `_main_loop` or `resolve_and_execute`
3. Combat must complete without errors
4. All attacks, damage, HP tracking, conditions, movement must function
5. If any step crashes or produces wrong results, that's a finding

## PvP Arena Harness v1 (Aegis spec, 2026-02-22)

**Ruleset:** PHB + DMG + MM only. Level 3. Wealth 2,700 gp. Core only.

**Prep Round (simultaneous):** 1 standard + 1 move + free actions. No attacks. No hostile effects covering opponent's start zone or center sigil.

**Summons:** Companion ON. Summons ON (cap 1 active). 1-round summon may begin in prep, completes start of Round 1.

**Objective — The Sigil:** Center of map, 5-ft radius. End of each round: 1 point if you have presence and opponent doesn't. First to 5 or highest at Round 10. Tiebreaker: % HP on primary character.

**Boundary:** Leaving map = forfeit.

**Arena Suite (3 maps):**
- **A — Open Stone (40×40):** No plants, no cover. Start 40 ft apart. Tests baseline closure + damage.
- **B — Vegetated Field (60×60):** Plants present, 4 symmetric boulders. Start 50-60 ft apart. Tests zone control.
- **C — Broken Ruins (50×50):** Stone, no plants. 2 wall segments = 2 lanes + 1 choke, mirror-symmetric. Start 40 ft apart. Tests constrained geometry.

**Run each arena 3×, swap sides. Log: initiative, sigil points, full attacks, control escapes, tumble attempts, summon presence.**

## Deliverables

1. **Gap Register** — One entry per gap found:
   - GAP-CG-NNN
   - Severity: HIGH (blocks chargen) / MEDIUM (workaround exists) / LOW (cosmetic)
   - Description: what's missing
   - PHB reference: page/section
   - Suggested fix: brief description of what a builder WO would need to do

2. **Two entity dicts** — Complete, combat-ready, manually assembled from walkthrough results. These become test fixtures.

3. **Walkthrough narrative** — Step-by-step record of every decision and every gap encountered. This is the evidence base for builder WOs.

4. **PvP combat log** — Output from the acceptance test fight.

## Integration Seams

- `aidm/schemas/entity_fields.py` — Field constants (existing)
- `aidm/schemas/leveling.py` — Class progressions (existing, 4 classes)
- `aidm/schemas/feats.py` + `aidm/data/content_pack/feats.json` — Feat registry (existing)
- `aidm/schemas/skills.py` — Skill definitions (existing, 7 skills)
- `aidm/data/equipment_catalog.json` — Equipment (existing)
- `aidm/core/dice_roller.py` — Deterministic dice (existing)
- `aidm/runtime/play_controller.py` — Fixture builder pattern (existing)
- `aidm/ui/character_sheet.py` — Derived value computation (existing)

## Notes (Aegis audit, 2026-02-22)

PvP balance is arena-spec dependent; Entangle ≠ denied Dex; Mounted Combat is 1/round Ride negation; dwarf resists trip. Treat as arena sensitivity probe, not definitive balance.

## Out of Scope

- Building any missing code (that's for builder WOs after this research)
- Multi-classing rules
- Prestige classes
- Spellbook/spell preparation (note the gap but don't solve it)
- Character persistence/save-load (note the gap but don't solve it)

## Preflight

```bash
python scripts/preflight_canary.py
python -m pytest tests/ -x --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py
```

Verify green before starting walkthrough. The PvP fight must run against a clean test suite.

## Delivery Footer

**Commit requirement:** If any files are created or modified (entity dicts, test fixtures, gap register), commit with a descriptive message referencing this WO ID. Research artifacts are evidence — they get committed.
**Debrief format:** RESEARCH — no word limit. Gap register + entity dicts + walkthrough narrative + PvP log.
**Radar bank:** (1) Most critical gap found, (2) Anything that surprised you about what already works, (3) Recommended first builder WO.
