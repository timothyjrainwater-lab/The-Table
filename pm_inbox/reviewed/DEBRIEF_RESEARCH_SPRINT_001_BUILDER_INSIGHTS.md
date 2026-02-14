# WO-RESEARCH-SPRINT-001: Builder Debrief — Full Insights Report

**From:** Builder (Opus 4.6)
**To:** PM (Aegis), via PO (Thunder)
**Date:** 2026-02-14
**Lifecycle:** NEW
**Context:** Post-sprint debrief following completion of all 11 research deliverables
**Deliverables Location:** `docs/research/RQ-SPRINT-001_*.md` through `RQ-SPRINT-011_*.md`

---

## The Big Picture

The bone layer is verified — 338 formulas proven, 30 bugs fixed, RED block lifted. This sprint asked: **what stands between that engine and a shippable product?** Eleven research questions, each targeting a specific gap in the bone-to-skin pipeline. The findings converge on a surprisingly clear picture.

---

## 1. The Architecture Is Sound

This is the headline finding. Three independent audits confirm it from different angles:

- **RQ-001 (IP Extraction):** Zero resolver modules contain game-system branching. All 47 D&D dependencies are data-driven. The engine doesn't know it's running D&D. Extraction is a data migration (2.5–3.5 days), not a refactor.
- **RQ-004 (Spark Containment):** The containment principles (no numbers in narration, no mechanical authority) are structural, not vocabulary-dependent. 14 universal rules survive any world.
- **RQ-008 (Dynamic Skin-Swapping):** Event logs use bone-layer IDs, not display names. WorldState has zero skin fields. A living campaign can be replayed through a different skin with zero data loss. This wasn't designed — it emerged from the Box/Lens/Spark separation.

**Verdict:** The bones are clean. The architecture is content-independent. The separation of concerns holds under scrutiny.

---

## 2. One 10-Line Fix Unlocks Everything Downstream

Three independent research agents (RQ-002, RQ-003, RQ-005) converged on the same finding without coordinating: **GAP-B-001**.

`NarrativeBrief.presentation_semantics` is `None` at runtime. The Lens assembler builds the brief but never populates it from the `PresentationSemanticsRegistry`. Layer B exists — frozen at compile time, schema correct, data present — but Spark never sees it.

**Downstream impact of this single gap:**
- Narration has no tonal anchor (RQ-003 finding)
- Containment can't do positive validation against Layer B (RQ-004 finding)
- The player trust chain breaks at the narration boundary (RQ-005 finding)
- Rulebook entries can't reference presentation semantics (RQ-006 finding)

**Fix:** ~10 lines in `assemble_narrative_brief()`. Highest impact-to-effort ratio in the entire sprint.

---

## 3. The NarrativeBrief Is Too Narrow

RQ-003 stress-tested 20 edge cases against the current schema:

| Result | Count | Description |
|--------|-------|-------------|
| PASS | 1 | Clean narration with full Layer B support |
| PARTIAL | 10 | Functional but loses flavor — falls back to generic templates |
| FAIL | 9 | Schema cannot represent the situation; narration contradicts or omits critical detail |

Failures aren't about content novelty — the system handles unforeseen abilities fine via fallback templates. Failures are structural:

1. **Single-target pipe vs. multi-target reality** — Fireball hitting 5 targets produces 5 disconnected briefs. Narrative unity of "one explosion, five victims" is lost.
2. **Single-condition slot vs. condition stacking** — A target that's prone, grappled, AND flanked has no way to communicate all three to Spark in one brief.
3. **Independent event mapping vs. causal chains** — An AoO triggered by a bull rush that causes a trip is three events forming one narrative moment, producing three disconnected briefs.

**Fix path:** Schema extension — `additional_targets`, `causal_chain_id`, `active_conditions`, spatial context flags. Addresses 6 of 9 failures.

---

## 4. `ui_description` Is the MVP Bottleneck

RQ-002 and RQ-006 both identify the same gap: the `ui_description` field on `AbilityPresentationEntry` is always `None`. This is the player-readable text — the tooltip, the rulebook blurb, the thing that makes "Void Lance" feel like a real ability instead of a spreadsheet row.

**Derivability matrix (how much of Layer B can be computed from bone-layer data):**

| Field | Derivability | Notes |
|-------|-------------|-------|
| `delivery_mode` | 95% deterministic | From bone-layer targeting type |
| `staging` | 90% deterministic | From spell duration/timing |
| `origin_rule` | 85% deterministic | From range/targeting |
| `scale` | 80% deterministic | From area/damage tier |
| `vfx_tags` / `sfx_tags` | 60% | Needs world theme context |
| **`ui_description`** | **0%** | **Requires genuine creative generation** |

Current rulebook text generation is a stub producing D&D parameter dumps like `"Damage: 1d4+1; Type: force; Range: medium"`.

**Recommendation:** Hybrid strategy — deterministic core for structural fields + optional LLM at compile time for creative text. Template generation produces functional but lifeless output. LLM enrichment is the quality ceiling.

---

## 5. Versioning Is Missing — Must Come Before Any World Ships

RQ-007 found **zero version-tracking infrastructure**:

| Component | Version Field | Validated on Load? | Checked Against Engine? |
|-----------|--------------|-------------------|------------------------|
| `pyproject.toml` | `"0.1.0"` | N/A | N/A |
| `WorldState.ruleset_version` | `"RAW_3.5"` | Never | Never |
| `CampaignManifest.engine_version` | `"0.1.0"` (default) | Never | Never |
| `Event` | (none) | N/A | N/A |
| `EventLog` | (none) | N/A | N/A |
| `replay_runner.run()` | (none) | N/A | N/A |

A campaign created under engine 0.1.0 loads silently under any future version. If reducer logic changed, replay silently produces different state hashes. The user sees "corrupted save" with zero diagnostic information.

**Mitigating factor:** The 30 WRONG verdicts from the fix phase are all Type A changes (bug fixes). Events record results (`damage=10`), not formulas (`str_mod * grip_multiplier`), so fixing a formula doesn't retroactively alter replay. But this property won't hold forever.

**Minimum viable versioning (3 changes):** Validate `engine_version` on load. Add `bone_engine_version` to WorldState. Add `event_schema_version` to Event.

---

## 6. Containment Must Be Parameterized

RQ-004 inventoried ~285 vocabulary-dependent artifacts across 4 Python files:
- GrammarShield: 4 regex patterns anchored to "AC", "HP", "DC", "PHB/DMG/MM"
- ContradictionChecker: ~210 keywords in 9 lists
- Kill Switch Registry: 5 regex patterns referencing D&D book names

All break the moment D&D vocabulary is replaced.

**Content-independent anchor points:**
1. The NarrativeBrief truth frame — structural relationships, not vocabulary
2. Frozen Layer B presentation semantics — generic spatial/temporal descriptors
3. Numeric/structural assertion boundary — "no numbers in narration" is universal

**Generation strategy:** World Compiler Stage 1 (Lexicon) generates world-specific containment data. 14 universal rules stay hard-coded. 12 rule categories regenerate per world compilation.

---

## 7. Voice Is Feasible But STT Dominates

RQ-009 profiled the 9-stage voice pipeline:

| Stage | Latency | Share of Total |
|-------|---------|---------------|
| STT (Whisper small.en, CPU int8) | 2–6s per 5s clip | **50–80%** |
| Intent Parse | <1ms | ~0% |
| Box Resolution | <5ms | ~0% |
| Template Narration | <1ms | ~0% |
| TTS (streaming) | 0.5–2s | 10–30% |
| Everything else combined | <100ms | <5% |

**Hardware tier verdicts:**
- **Tier 0 (CPU only):** Cannot reliably hit the 2–4s simple action budget. STT alone takes 2–6s.
- **Tier 1+ (modest GPU):** Achievable with streaming TTS and template narration for combat.

**Active blocker:** Chatterbox TTS truncation on >60 words (TD-023).

---

## 8. Hardware Tiering Is Mechanical-Safe

RQ-009 and RQ-011 confirm the `SPARK_SWAPPABLE` invariant holds across hardware tiers. A Tier 0 player and a Tier 2 player rolling the same dice with the same seed get identical mechanical outcomes. Only sensory presentation changes.

RQ-011 audited 7 adapter boundaries:
- **Atmospheric components** (STT, TTS, Image, Spark): Behind tight Protocol-based interfaces. One new file + one registry line to swap. Zero changes to callers, zero changes to mechanics.
- **Mechanical components** (RNG, pathfinding, AoE rasterizer): Monolithic implementations without Protocol interfaces. This is the gap.

Per-component tiering (not global) means a player could have Tier 2 TTS but Tier 0 image generation. Mechanical experience identical across all configurations.

---

## 9. Community Literacy Has a Built-In Solution

RQ-010 found the `content_id` layer is already a universal translator. `ABILITY_003` is "Void Lance" in one world and "Thread of Unmaking" in another, but the mechanical fingerprint (deterministic hash of tactical identity fields) is identical. The pipeline already produces this mapping — it just doesn't expose it to the player.

**Key structures already in place:**
- `template_id` → `mechanical_id` → `content_id` → `world_name` chain
- `VocabularyRegistry` as the per-world translation table
- 987 mechanical entries (605 spells, 273 creatures, 109 feats) shared across all worlds

---

## 10. Cross-Cutting Themes

These patterns emerged across multiple RQs without coordination:

| Theme | Source RQs | Implication |
|-------|-----------|-------------|
| Layer B is designed but disconnected | 002, 003, 004, 005, 006 | GAP-B-001 is the single point of failure |
| Content independence is architectural, not aspirational | 001, 004, 008 | Extraction is data work, not redesign |
| Compound events are the real challenge | 003, 005 | NarrativeBrief width, not content novelty, is the bottleneck |
| Creative text is the hardest remaining problem | 002, 006 | `ui_description` generation is fundamentally an LLM quality question |
| Versioning absence is a ticking clock | 007 | Must be solved before any world ships, even internally |
| Sensory degradation is safe, mechanical swaps need work | 009, 011 | Atmospheric adapters clean, mechanical components monolithic |

---

## 11. Recommended Priority Stack

Based on cross-referencing all 11 research findings:

| # | Action | Source RQs | Effort | Impact |
|---|--------|-----------|--------|--------|
| 1 | **Fix GAP-B-001** — connect Layer B to pipeline | 002, 003, 005 | ~10 lines | Unlocks all downstream skin consumption |
| 2 | **Add minimum versioning** — 3 validation checks | 007 | Small | Prevents silent save corruption |
| 3 | **Widen NarrativeBrief** — multi-target, causal chains, conditions | 003 | Medium | Fixes 6/9 stress-test failures |
| 4 | **Implement `ui_description` generation** — hybrid template+LLM | 002, 006 | Medium–Large | Makes worlds feel authored, not generated |
| 5 | **Parameterize containment** — world-aware guards | 004 | Medium | Required for content independence |
| 6 | **IP extraction** — migrate 37 data dependencies to content pack | 001 | 2.5–3.5 days | Completes content independence |
| 7 | **Protocol-wrap mechanical components** — RNG, pathfinding, AoE | 011 | Medium | Future-proofing |

Items 1–3 are **foundational** (fix what's broken).
Items 4–6 are **MVP-critical** (build what's missing).
Item 7 is **longevity** (protect the future).

---

## 12. The Bottom Line

The engine is proven. The architecture holds. The gaps are well-defined and surprisingly concentrated — most of the pain traces back to the Layer B pipeline not being connected. The hardest unsolved problem is creative text generation (`ui_description`), which is fundamentally an LLM quality question, not an architecture question.

The path from verified engine to shippable product is clear. It starts with 10 lines of code.

---

*Debrief prepared by Builder (Opus 4.6) from direct analysis of all 11 sprint deliverables.*
