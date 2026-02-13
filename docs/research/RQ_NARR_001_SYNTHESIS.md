# Narrative Balance Contract v1

## RQ-NARR-001 Synthesis: AI Narrative Balance -- Spark Creativity Bounded by Box Truth

**Document Type:** Binding Architectural Contract (Pre-Implementation)
**Date:** 2026-02-12
**Status:** DELIVERED -- Ready for PM Approval
**Author:** Opus (PM Synthesis)
**Synthesized From:**
- `docs/research/findings/RQ_NARR_001_A_OUTPUT_SPACE_AND_TRUTH_PACKET.md` (Sub-Q 1-2)
- `docs/research/findings/RQ_NARR_001_B_TEMPLATES_AND_CONFIRMATION.md` (Sub-Q 3-4)
- `docs/research/findings/RQ_NARR_001_C_UNKNOWNS_TONE_EVALUATION.md` (Sub-Q 5-7)
**Parent Question:** `docs/research/RQ_NARR_001_AI_NARRATIVE_BALANCE.md`

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Alignment Rules: The Two Absolute Laws](#2-alignment-rules-the-two-absolute-laws)
3. [Evaluation Rubric: Three Measurable Dimensions](#3-evaluation-rubric-three-measurable-dimensions)
4. [Consolidated Event Label Taxonomy (43 Labels)](#4-consolidated-event-label-taxonomy-43-labels)
5. [Three-Tier Augmentation Model](#5-three-tier-augmentation-model)
6. [Violation Detection Pipeline](#6-violation-detection-pipeline)
7. [Target Metrics](#7-target-metrics)
8. [Regression Harness: Golden Scenarios](#8-regression-harness-golden-scenarios)
9. [Scoring and Evaluation Method](#9-scoring-and-evaluation-method)
10. [Adversarial Examples](#10-adversarial-examples)
11. [Contradiction Notes and Resolutions](#11-contradiction-notes-and-resolutions)
12. [Open Questions Requiring PM Decision](#12-open-questions-requiring-pm-decision)
13. [Acceptance Criteria](#13-acceptance-criteria)
14. [References](#14-references)

---

## 1. Purpose and Scope

This document is the **single authoritative specification** for how Spark (the narration LLM, currently Qwen3 8B) may generate text in the AIDM system. It unifies seven sub-questions from RQ-NARR-001 into a binding contract that all narration-path implementation work orders (WO-027 through WO-033, WO-041) must satisfy.

The contract answers one question: **How do we let an LLM narrate D&D 3.5e events vividly without it ever lying about what the game engine computed?**

The answer rests on three pillars:

1. **Mechanical Fidelity** -- narration reflects Box outcome (hit/miss/damage/defeat)
2. **Containment** -- no HP/AC/IDs/coordinates/forbidden tokens leak
3. **Tone Targets** -- gravity, verbosity, drama parameters map to prompts without altering truth

This document is self-contained. Implementers should not need to read the three sub-findings to build against this contract, though the sub-findings remain authoritative for deep rationale.

---

## 2. Alignment Rules: The Two Absolute Laws

Every narration produced by Spark must satisfy two non-negotiable rules. Violation of either triggers KILL-002 and immediate fallback to template narration.

### Law 1: Narration MUST Reflect Box Outcome

Spark output must be a faithful dramatization of the mechanical outcome that Box computed. The mapping is directional and absolute:

| Box Outcome | Spark MUST Convey | Spark MUST NOT Convey |
|---|---|---|
| `outcome: "hit"` | That the attack connected | Miss, dodge, parry, deflection |
| `outcome: "miss"` | That the attack failed to connect | Strike, hit, wound, connect |
| `outcome: "save_success"` | That the target resisted the effect | Succumb, overwhelm, fail |
| `outcome: "save_failure"` | That the target was affected | Shrug off, resist, endure unscathed |
| `outcome: "defeated"` | That the target is down | Standing, fighting on, recovering |
| `damage: N, hp%: X` | Wound severity proportional to HP% | Severity contradicting the HP% band |

**Source:** RQ-NARR-001-A Section 1.2 (Forbidden Output Types, subsection B "Contradicting Box Outcomes"); RQ-NARR-001-C Section 7.1 Category 1 (Outcome Mismatch).

### Law 2: Narration MUST NOT Leak Forbidden Details

Spark output must never contain any of the following unless the Truth Packet explicitly provides the value AND the transparency mode permits it:

| Forbidden Token Class | Examples | Detection Method |
|---|---|---|
| Hit point totals | "18 HP remaining", "30 max HP" | Regex: `HP \d+`, `\d+ hit points` |
| Armor class values | "AC 15", "armor class of 16" | Regex: `AC \d+`, `armor class` |
| Save DCs (unsourced) | "DC 15 Reflex save" | Regex: `DC \d+` |
| Internal entity IDs | "Orc_1", "PC_Fighter", "npc_guard_01" | Regex: underscore-delimited identifiers |
| Grid coordinates | "square (3,4)", "position (7,4)" | Regex: `\(\d+,\s*\d+\)` |
| Rule citations | "Per PHB page 141", "SRD says" | Regex: `PHB`, `DMG`, `SRD`, `page \d+` |
| BAB/modifier breakdowns | "BAB +5", "+3 modifier" | Regex: `BAB [+-]?\d+` |

**Exception:** In SAPPHIRE and DIAMOND transparency modes, certain mechanical values (roll summaries, damage numbers, AC values) are explicitly included in the Truth Packet's `roll_summary` field. When present, Spark MAY paraphrase these values in natural language.

**Source:** RQ-NARR-001-A Section 1.2 (Forbidden Output Types, subsections A, E, F, G); RQ-NARR-001-C Section 7.1 Category 5 (Mechanical Assertion).

---

## 3. Evaluation Rubric: Three Measurable Dimensions

Every Spark narration is scored along three independent dimensions. The rubric is designed for automated evaluation without human judges on every turn.

### Dimension A: Mechanical Fidelity

**Definition:** Does the narration faithfully reflect the Box-computed outcome?

| Score | Criteria | Automated Check |
|---|---|---|
| **PASS** | Narration conveys the correct outcome (hit/miss/save/defeat) with wound severity proportional to HP% band. No invented mechanical effects. | Keyword + regex checks against Truth Packet outcome field. HP% band check against severity word lists. Unauthorized effect scan against `active_conditions`. |
| **MARGINAL** | Narration conveys the correct outcome but severity language is slightly misaligned (e.g., "solid hit" for margin=1, or missing aftermath for a 60% HP loss). | HP% proportionality check flags mismatch but within one severity band. |
| **FAIL** | Narration contradicts outcome (says miss when Box says hit), invents conditions not in Truth Packet, or describes effects Box did not compute. | Any keyword contradiction detected, or unauthorized condition/effect found. |

**HP% Severity Bands (from RQ-NARR-001-A Section 1.3, Gray Area 2):**

| HP% Remaining | Required Severity Tone | Forbidden Severity Words |
|---|---|---|
| 90-100% | Minor: "scratch", "barely hurt", "glancing blow" | "devastating", "mortal", "grievous", "critical" |
| 60-89% | Moderate: "wounded", "bloodied", "dangerous" | "scratch", "barely hurt" (understatement) |
| 30-59% | Serious: "bloodied", "staggering", "gravely wounded" | "barely hurt", "minor" |
| 10-29% | Critical: "on the brink", "barely standing" | "scratched", "fine" |
| 0% | Defeated: "falls", "collapses", "defeated" | Any language implying still fighting |

**Margin-Tone Calibration (from RQ-NARR-001-A Section 1.3, Gray Area 1):**

Spark may describe attack closeness ONLY if the Truth Packet contains an explicit `margin` field. When present:

| Margin Value | Allowed Description |
|---|---|
| margin <= -5 | "goes wide", "not even close" |
| margin = -1 to -3 | "narrowly misses", "just shy" |
| margin = 1 to 2 | "barely connects", "scrapes through" |
| margin = 3 to 5 | "strikes solidly", "lands true" |
| margin > 5 | "cleaves through defenses", "overwhelming strike" |

When margin is absent from the Truth Packet, Spark MUST NOT infer closeness from any other field.

### Dimension B: Containment

**Definition:** Does the narration avoid leaking forbidden mechanical details?

| Score | Criteria | Automated Check |
|---|---|---|
| **PASS** | No forbidden token classes appear in output. Internal IDs, grid coordinates, HP totals, unsourced AC/DC values, and rule citations are all absent. | Full regex scan against forbidden token patterns (see Section 2, Law 2). |
| **MARGINAL** | A borderline case where a mechanical value appears but is sourced from the Truth Packet's `roll_summary` field in SAPPHIRE/DIAMOND mode. | Regex match found but cross-referenced against Truth Packet values and transparency mode. |
| **FAIL** | Any forbidden token appears without Truth Packet sourcing. Internal IDs leak. Grid coordinates appear. Rule citations used as authority. | Any unsourced regex match. |

**Containment Special Cases:**

1. **Entity names vs IDs:** Spark receives `actor_name: "Fighter"` (allowed) not `actor_id: "PC_Fighter_01"` (forbidden). If an internal ID appears in output, this is a containment failure even if the Truth Packet was correctly filtered -- it indicates a Lens filtering bug.

2. **Grid coordinates in templates:** Tier 1 templates (see Section 5) for AoE spells historically included grid coordinates (e.g., "at grid square (7,4)"). This is a containment violation. Templates must use natural language ("at the cluster of orcs by the door") not coordinates.

3. **Transparency mode interaction:** In RUBY mode, even `roll_summary` is absent from the Truth Packet, so damage numbers in narration are containment violations. In SAPPHIRE/DIAMOND, `roll_summary` is present and Spark may paraphrase it.

### Dimension C: Tone Targets

**Definition:** Does the narration match the configured DM persona without the tone bleeding into mechanical claims?

**Five Tone Parameters (from RQ-NARR-001-C Section 6.2):**

| Parameter | Range | Maps to System Prompt Instruction |
|---|---|---|
| **Verbosity** | 0.0 (terse) to 1.0 (verbose) | Target sentence count: `1 + round(3 * verbosity)` sentences |
| **Drama** | 0.0 (understated) to 1.0 (dramatic) | Action verb intensity, exclamation frequency, pacing |
| **Humor** | 0.0 (serious) to 1.0 (witty) | Wry observations, quips (must not contradict outcome) |
| **Grittiness** | 0.0 (heroic fantasy) to 1.0 (dark/visceral) | Gore level, moral ambiguity, violence realism |
| **NPC Voice** | Per-character profile | Speech pattern, vocabulary level, mannerisms |

**Tone Scoring:**

| Score | Criteria | Automated Check |
|---|---|---|
| **PASS** | Output length matches verbosity target (+/- 1 sentence). Tone adjectives are consistent with drama/humor/grittiness settings. No tone bleeding (see below). | Sentence count within range. No FAIL-triggering bleeding patterns detected. |
| **MARGINAL** | Output length off by 2+ sentences from target. Tone somewhat inconsistent with settings but no bleeding. | Sentence count outside range. |
| **FAIL** | Tone causes mechanical misrepresentation. Examples: drama causes "barely missed" when margin was -5; humor causes "bounces off armor" when Box said miss (not deflection); grittiness adds "knocks prone" without Box authorization. | Bleeding detection: cross-reference tone-influenced phrases against Truth Packet margin/outcome/conditions. |

**Tone Bleeding Prevention (from RQ-NARR-001-C Section 6.3):**

The critical invariant: **Changing tone parameters while holding Truth Packet constant MUST NOT change the implied mechanical outcome.** This is verified by the Determinism Gate test:

```
Given: Fixed Box seed -> fixed Truth Packet
Test:  Generate narration with Tone A, record implied outcome
       Generate narration with Tone B, record implied outcome
Assert: Implied outcomes are identical
```

Specific bleeding rules:

1. Margin language requires explicit `margin` field -- tone cannot invent closeness data
2. HP% severity must stay within the correct band regardless of grittiness setting
3. Humor must not imply a different contact mode (e.g., "bounces off armor" for a miss implies armor contact, which is not a miss)
4. Drama must not add conditions ("knocks prone", "staggers") unless `active_conditions` lists them

---

## 4. Consolidated Event Label Taxonomy (43 Labels)

Box produces canonical event labels after each mechanical resolution. These labels are the **mechanical anchors** that all narration must respect. The taxonomy is organized into 7 domains.

**Source:** RQ-NARR-001-B Section 1 (Complete Event Label Taxonomy).

### 4.1 Combat Events (12 labels)

| # | Label | Trigger | Key Required Fields |
|---|---|---|---|
| 1 | `HIT` | Attack roll >= target AC | attacker, target, weapon, damage |
| 2 | `MISS` | Attack roll < target AC | attacker, target, weapon, roll_total, target_ac |
| 3 | `CRITICAL_HIT` | Natural 20 + confirmed | attacker, target, weapon, damage, natural_roll |
| 4 | `CRITICAL_MISS` | Natural 1 | attacker, target, weapon, natural_roll |
| 5 | `DAMAGE_DEALT` | After successful hit | target, damage, damage_type, hp_before, hp_after |
| 6 | `ENTITY_DEFEATED` | HP <= 0 | target, final_damage |
| 7 | `FULL_ATTACK_START` | Full attack declared | attacker, num_attacks |
| 8 | `FULL_ATTACK_END` | All attacks resolved | attacker, hits, total_damage |
| 9 | `SNEAK_ATTACK_BONUS` | Sneak attack applied | attacker, target, sneak_damage |
| 10 | `POWER_ATTACK_DECLARED` | Power Attack feat used | attacker, penalty, bonus |
| 11 | `CHARGE_ATTACK` | Charge action executed | attacker, target, bonus |
| 12 | `COUP_DE_GRACE` | Coup de grace on helpless | attacker, target, damage, save_dc |

### 4.2 Tactical Events (6 labels)

| # | Label | Trigger | Key Required Fields |
|---|---|---|---|
| 13 | `AOO_TRIGGERED` | Movement provokes AoO | provoker, threatening_entity, grid_square |
| 14 | `AOO_RESOLVED` | AoO attack completed | attacker, target, hit, damage |
| 15 | `COVER_APPLIED` | Target has cover | attacker, target, cover_type, ac_bonus |
| 16 | `FLANKING_ESTABLISHED` | Two allies flank target | flankers, target, bonus |
| 17 | `CONCEALMENT_CHECK` | Target has concealment | attacker, target, miss_chance, result |
| 18 | `THREATENED_CASTING` | Casting in threatened square | caster, threatening_entities |

### 4.3 Spellcasting Events (9 labels)

| # | Label | Trigger | Key Required Fields |
|---|---|---|---|
| 19 | `SPELL_CAST` | Spell cast successfully | caster, spell_name, target/point |
| 20 | `SPELL_RESISTED` | Target makes save | target, spell_name, save_type, dc, roll_total |
| 21 | `SPELL_DAMAGE` | Spell damage applied | targets, spell_name, damage, damage_type |
| 22 | `CONCENTRATION_CHECK` | Concentration check made | caster, dc, roll_total, success |
| 23 | `CONCENTRATION_FAILED` | Concentration check failed | caster, spell_name |
| 24 | `SPELL_RESISTANCE_CHECK` | SR check rolled | caster, target, caster_level, sr, success |
| 25 | `SPELL_COUNTERED` | Counterspell successful | counterspeller, original_caster, spell_name |
| 26 | `DURATION_EXPIRED` | Spell/effect ends naturally | spell_name, affected_entities |
| 27 | `DISPEL_MAGIC` | Dispel attempt | dispeller, target_spell, success |

### 4.4 Movement Events (4 labels)

| # | Label | Trigger | Key Required Fields |
|---|---|---|---|
| 28 | `MOVEMENT_COMPLETED` | Move action finished | mover, from, to, distance_ft |
| 29 | `MOVEMENT_BLOCKED` | Path blocked | mover, intended_square, blocker_type |
| 30 | `DIFFICULT_TERRAIN` | Movement through difficult terrain | mover, squares_traversed, movement_cost |
| 31 | `MOUNTED_MOVEMENT` | Mount moves with rider | rider, mount, from, to, distance_ft |

### 4.5 Condition Events (4 labels)

| # | Label | Trigger | Key Required Fields |
|---|---|---|---|
| 32 | `CONDITION_APPLIED` | New condition added | target, condition, duration_rounds, source |
| 33 | `CONDITION_REMOVED` | Condition ends | target, condition, reason |
| 34 | `CONDITION_EXPIRED` | Duration reached 0 | target, condition |
| 35 | `SAVE_ENDS_CONDITION` | Save against ongoing condition | target, condition, save_type, dc, roll_total |

### 4.6 Combat Lifecycle Events (5 labels)

| # | Label | Trigger | Key Required Fields |
|---|---|---|---|
| 36 | `COMBAT_STARTED` | Combat initiated | participants, surprise_round |
| 37 | `ROUND_STARTED` | New round begins | round_number |
| 38 | `TURN_STARTED` | Entity's turn begins | entity, initiative_order_position |
| 39 | `TURN_ENDED` | Entity's turn ends | entity, actions_taken |
| 40 | `FLAT_FOOTED_CLEARED` | Entity acts first time | entity |

### 4.7 Environmental Events (3 labels)

| # | Label | Trigger | Key Required Fields |
|---|---|---|---|
| 41 | `ENVIRONMENTAL_DAMAGE` | Hazard damage applied | targets, damage, damage_type, source |
| 42 | `FALL_TRIGGERED` | Entity falls from height | faller, distance_ft, surface_type |
| 43 | `FALLING_DAMAGE` | Fall damage applied | faller, damage, distance_ft |

### 4.8 Event-to-Narration Contract

For every event label, the following guarantees hold:

1. **Box emits the label** with all required fields populated
2. **Lens filters the label** into a Truth Packet, stripping internal IDs and adding provenance tags
3. **Spark narrates the label** using the outcome field as the mechanical anchor
4. **Verification checks the narration** against the original label's outcome and required fields

If Box emits a label not in this taxonomy, Spark falls back to the generic template: `"{actor} performs an action. The result: {outcome}."` A new label must be added to the taxonomy before it receives custom narration.

---

## 5. Three-Tier Augmentation Model

Narration generation uses a graduated approach with three tiers. Each tier increases narrative quality but also increases risk and latency. Fallback is always downward (Tier 3 -> Tier 2 -> Tier 1).

**Source:** RQ-NARR-001-B Section 2 (Template-to-LLM Augmentation Strategy).

### Tier 1: Full Template (Zero LLM)

**Description:** Pure template substitution. No LLM call.

**Properties:**
- Deterministic: same inputs produce same output
- Zero violation risk: templates are hand-crafted and pre-verified
- Always available: no model dependency
- Baseline violation rate: 0%

**When Used:**
- Spark model unavailable or crashed
- Token budget exceeded (context > 7000 tokens after all truncation)
- KILL-004 latency timeout (>10s) triggered
- Performance mode enabled by DM
- Any higher-tier verification failure triggers fallback here

**Output Example (HIT event):**
> "Fighter strikes Orc with their longsword! The blow lands true, dealing 12 damage."

### Tier 2: Slot-Guided LLM (Hybrid)

**Description:** Template provides structural skeleton with named slots. Spark fills each slot with constrained flavor text.

**Properties:**
- Template guarantees mechanical accuracy (damage values, outcome direction)
- LLM provides flavor within word-limited, constraint-checked slots
- Moderate violation risk: slot constraints catch most contradictions
- Each slot has a word limit (15-25 words) and forbidden-word list

**Slot Taxonomy (from RQ-NARR-001-B Section 2.3):**

| Slot Name | Purpose | Word Limit |
|---|---|---|
| `ACTION_DESCRIPTION` | Attack/cast motion | 15 |
| `IMPACT_DESCRIPTION` | Hit/miss result | 15 |
| `AFTERMATH_DESCRIPTION` | Post-impact reaction | 20 |
| `SPELL_VISUAL` | Spell appearance | 20 |
| `ENVIRONMENT_DETAIL` | Scene atmosphere | 25 |
| `NPC_REACTION` | NPC emotional response | 20 |

**Slot Constraint Example (HIT event):**
- `ACTION_DESCRIPTION` forbidden words: ["miss", "dodge", "parry", "fails"]
- `IMPACT_DESCRIPTION` required outcome: HIT (must convey successful strike)
- `AFTERMATH_DESCRIPTION` HP-aware: calibrate to `target_hp_percent`

**When Used:**
- Spark available, event is not high-stakes
- Tone customization requested by DM persona settings
- Default tier for routine combat narration

**Output Example (HIT event, dramatic tone):**
> "Fighter brings his longsword down in a powerful slash upon Orc! The blade cuts deep, blood spraying across the stone floor, dealing 12 damage. The orc grunts in pain but holds his ground."

### Tier 3: Free LLM with Guardrails (Maximum Flexibility)

**Description:** Spark generates full narration from a Truth Packet and system prompt, with no template skeleton.

**Properties:**
- Maximum narrative flexibility and dramatic quality
- Highest violation risk: requires full verification pipeline
- Falls back to Tier 2 if verification fails, then to Tier 1

**When Used:**
- High-stakes moments: boss fights, critical hits, entity defeated, climactic scenes
- DM persona has `allow_free_llm: true` (default)
- Spark available and token budget allows full context

**Output Example (HIT event, climactic boss fight):**
> "Oaken's greatsword sings through the air in a devastating arc. The Orc Chieftain raises his shield, but the blow smashes through his defense, biting deep into his shoulder. The chieftain roars in pain, staggering backward."

### Tier Routing Decision Tree

```
1. Is Spark available?
   NO  -> Tier 1 (Full Template)
   YES -> continue

2. Is total context budget exceeded (>7000 tokens)?
   YES -> Tier 1 (Full Template)
   NO  -> continue

3. Is this a high-stakes moment? (ENTITY_DEFEATED, CRITICAL_HIT, boss combat)
   YES -> Attempt Tier 3 (Free LLM)
   NO  -> continue

4. Is tone customization active (any tone param != default)?
   YES -> Tier 2 (Slot-Guided)
   NO  -> Tier 1 (Full Template, fast path)

5. Did generation succeed within timeout?
   NO  -> Fall back one tier
   YES -> Run verification pipeline

6. Did verification pass?
   NO  -> Fall back one tier
   YES -> Return narration
```

### Token Budget (from RQ-NARR-001-A Section 2.3)

For Qwen3 8B with 8192 token context window:

| Component | Budget | Purpose |
|---|---|---|
| System Prompt (base) | 600 tokens | Role, constraints, D&D rules summary |
| Tone Parameters | 100 tokens | 5 params, 20 tokens each |
| NPC Voice (if dialogue) | 50 tokens | Speech pattern, mannerisms |
| Truth Packet | 400 tokens | Event data, scene context |
| Narration History | 2500 tokens | Last ~15 narrations for continuity |
| Generation Budget | 512 tokens | Spark output (max_tokens) |
| **Total Allocated** | **4162 tokens** | |
| **Reserve/Overhead** | **4030 tokens** | Safety factor ~2x |

**Fallback Cascade (when budget exceeded):**
1. **Level 1:** Remove `recent_narrations` entirely (keep Truth Packet only)
2. **Level 2:** Simplify Truth Packet (remove lighting, weather, nearby_npcs)
3. **Level 3:** Fall back to Tier 1 template narration (no LLM call)

---

## 6. Violation Detection Pipeline

The pipeline operates in three tiers with increasing thoroughness and latency. A violation detected at any tier triggers the defined response.

**Source:** RQ-NARR-001-C Section 7.2-7.4 (Three Detection Approaches + Recommended Pipeline).

### 6.1 Six Violation Categories

| # | Category | Definition | Example | Detection Difficulty |
|---|---|---|---|---|
| 1 | **Outcome Mismatch** | Narration describes different outcome than Box computed | "Your blade strikes the orc!" when Box says MISS | Low (keyword) |
| 2 | **Entity Mismatch** | Narration mentions entity not present in scene | "The goblin lunges!" when only orcs exist | Medium (NER) |
| 3 | **Geometry Mismatch** | Narration describes spatial relationships contradicting scene | "From behind the pillar" when no cover exists | Medium (keyword) |
| 4 | **Severity Mismatch** | Wound description inconsistent with HP% data | "A scratch" when target lost 80% HP | Low (threshold) |
| 5 | **Mechanical Assertion** | Narration adjudicates rules, cites authorities, reveals stats | "Per PHB page 141" or "The orc has AC 16" | Low (regex) |
| 6 | **Unauthorized Effects** | Narration invents conditions or effects Box did not compute | "Your strike knocks the orc prone" without CONDITION_APPLIED | Medium (keyword + list) |

### 6.2 Tier 1: Real-Time Checks (Synchronous, < 100ms)

Runs **before narration is delivered to the player**. Any FAIL triggers KILL-002 and immediate template fallback.

**Stage 1: Keyword Matching (< 10ms)**

Checks outcome mismatch (Category 1) by comparing narration keywords against Truth Packet outcome field.

- HIT events: scan for miss/dodge/parry/evade keywords
- MISS events: scan for strike/hit/connect/find-its-mark keywords
- SAVE_SUCCESS events: scan for succumb/overwhelm/fail-to-resist keywords
- SAVE_FAILURE events: scan for resist/shrug-off keywords
- DEFEATED events: scan for still-standing/fighting-on keywords

**Stage 2: Regex Pattern Scan -- KILL-002 (10-50ms)**

Detects mechanical assertions (Category 5) and containment violations (Law 2).

Pattern groups:
- **Adjudication:** "you can't do that", "that's not allowed", "you must roll"
- **Rule citation:** "per PHB", "according to the rules", "page N"
- **Stat revelation:** "AC N", "DC N", "HP N", "has N hit points"
- **Internal IDs:** underscore-delimited multi-segment identifiers (e.g., `PC_Fighter`, `npc_guard_01`)
- **Grid coordinates:** `(N, N)` patterns

Exception logic: If a matched value (e.g., "AC 15") is present in the Truth Packet's `roll_summary` field AND the transparency mode is SAPPHIRE or DIAMOND, the match is suppressed (not a violation).

**Stage 3: HP Proportionality Check (< 5ms)**

Checks severity mismatch (Category 4) by comparing severity keywords against HP% bands.

- If `target_hp_percent > 85` and narration contains ["devastating", "mortal", "grievous", "critical"]: FAIL
- If `target_hp_percent < 30` and narration contains ["scratch", "barely hurt", "minor", "superficial"]: FAIL

**Stage 4: Template Anchoring (< 10ms, Tier 2 only)**

When narration is Tier 2 (slot-guided), verifies that LLM-filled slots do not contradict the template anchor.

- Template says HIT + damage: slots must not contain miss/deflect/no-effect language
- Template says MISS: slots must not contain strike/hit/connect language

**Stage 5: Unauthorized Effect Scan (< 10ms)**

Checks Category 6 by scanning for condition keywords (prone, grappled, stunned, frightened, paralyzed, slowed) and environmental effect keywords (difficult terrain, concealment, cover, ignited, frozen) not present in `active_conditions` or `environmental_effects`.

**Total Tier 1 Time Budget: < 100ms**

**Response on FAIL:** Discard LLM output. Fall back one augmentation tier. Log violation with full context (narration text, Truth Packet, detection stage, matched pattern).

### 6.3 Tier 2: Async Validation (Background, < 5s)

Runs **after narration is delivered to the player** but before the next turn resolves. Does not block gameplay.

**Semantic Comparison via LLM (2-5 seconds)**

A verification prompt is sent to a lightweight LLM (temperature=0.0, max_tokens=100) that compares the Truth Packet against the delivered narration and checks all six violation categories.

If violation detected:
- Log violation to audit trail with severity
- Alert DM via Judge's Lens notification (optional, configurable)
- Increment violation counter for regression tracking
- Do NOT retroactively correct the narration (player has already seen it)

**Note on LLM choice:** The semantic check should use the same Spark model (Qwen3 8B) but with temperature=0.0 for deterministic verification. If a separate lightweight verifier model becomes available, it should be preferred to avoid self-consistency bias.

### 6.4 Tier 3: Regression Testing (Offline, Batch)

Runs **in CI pipeline on every PR** that touches narration-path code. See Section 8 for the golden scenario harness.

---

## 7. Target Metrics

| Metric | Target | Measurement | Frequency |
|---|---|---|---|
| **Overall Violation Rate** | < 1% per 100 narrations | Gold master scenarios (Section 8) | Per PR (CI gate) |
| **False Positive Rate** | < 5% of flagged violations | Manual review of 20 flagged samples/week | Weekly |
| **Template-Only (Tier 1) Violations** | 0% | Gold master in template-only mode | Per PR (CI gate) |
| **LLM-Augmented (Tier 2-3) Violations** | < 2% | Gold master in LLM mode | Per PR (CI gate) |
| **KILL-002 Trigger Rate (production)** | < 0.1% (1 per 1000) | Production narration logs | Daily |
| **Async Semantic Violations** | < 0.5% | Background validation logs | Daily |
| **Mean Violations Per 4-Turn Combat** | < 1 | Gold master scenario | Per PR (CI gate) |

**CI Gate Policy:**
- **Block PR** if overall violation rate exceeds 2% (regression detected)
- **Warn** if false positive rate exceeds 10% (detection patterns too aggressive)
- **Block PR** if Tier 1 (template) violations > 0 (template correctness is absolute)

**Source:** RQ-NARR-001-C Section 7.5-7.6 (Regression Test Strategy + Metrics to Track).

---

## 8. Regression Harness: Golden Scenarios

The regression harness uses curated "golden scenarios" to detect drift in narration quality and violation rate over time. Each scenario has a fixed Box seed (deterministic mechanical outcomes) and variable narration seeds (varied LLM output).

### 8.1 Four Golden Scenarios

| Scenario | Domain Coverage | Key Mechanics Tested | Turn Count |
|---|---|---|---|
| **Tavern Brawl** | Melee combat, NPC dialogue, environment | HIT, MISS, DAMAGE_DEALT, ENTITY_DEFEATED, NPC voice consistency | 8 turns |
| **Dungeon Corridor** | Ranged + melee, environmental hazards, conditions | AOO_TRIGGERED, COVER_APPLIED, ENVIRONMENTAL_DAMAGE, CONDITION_APPLIED | 10 turns |
| **Open Field Battle** | AoE spells, positioning, multiple targets | SPELL_CAST, SPELL_DAMAGE, SPELL_RESISTED, FLANKING_ESTABLISHED | 12 turns |
| **Boss Fight** | Complex mechanics, condition tracking, high drama | CRITICAL_HIT, CONCENTRATION_CHECK, SPELL_RESISTANCE_CHECK, ENTITY_DEFEATED (boss) | 15 turns |

### 8.2 Execution Protocol

For each scenario:

1. **Fix Box seed** -- produces identical mechanical outcomes every run
2. **Run 100 iterations** with different narration seeds (Spark temperature >= 0.7 per LLM-002)
3. **For each iteration:** generate narration for every turn, run full Tier 1 detection pipeline, log all violations
4. **Aggregate:** violation rate per scenario, per category, per augmentation tier

Total narrations per CI run: 4 scenarios x ~11 avg turns x 100 iterations = ~4,400 narrations

### 8.3 Golden Output Anchors

Each scenario includes 3-5 "golden turns" with pre-approved reference narrations. These serve as qualitative anchors, not exact-match targets:

**Example Golden Turn (Tavern Brawl, Turn 3):**
- **Box Event:** `{event: "CRITICAL_HIT", actor: "Fighter", target: "Thug", weapon: "barstool", damage: 16}`
- **Reference Narration (Tier 3):** "You bring the barstool crashing down on the thug's head with devastating force! Wood splinters fly as the blow connects squarely, and the thug's knees buckle beneath him."
- **Verification:** PASS on all three dimensions (fidelity: crit hit + high damage conveyed; containment: no forbidden tokens; tone: dramatic, proportional to damage)

### 8.4 Drift Detection

Track violation rate over time. If violation rate increases by > 0.5% between consecutive PRs:
- Flag for investigation
- Compare changed files against narration pipeline components
- Require explicit reviewer signoff on narration-path changes

---

## 9. Scoring and Evaluation Method

The scoring method is designed to work **without human judges for routine turns**. Human review is reserved for ambiguous cases and weekly calibration.

### 9.1 Automated Turn-Level Scoring

Each narration receives an automated composite score:

```
Turn Score = (Fidelity_Score * 0.5) + (Containment_Score * 0.35) + (Tone_Score * 0.15)

Where each dimension score:
  PASS     = 1.0
  MARGINAL = 0.5
  FAIL     = 0.0
```

**Weight Rationale:**
- Fidelity (50%): Most critical -- mechanical contradiction destroys game integrity
- Containment (35%): Second priority -- leaking HP/AC/IDs breaks immersion and could enable metagaming
- Tone (15%): Lowest weight -- tone mismatches are undesirable but not game-breaking

**Thresholds:**
- Turn Score >= 0.85: PASS (no action needed)
- Turn Score 0.50-0.84: MARGINAL (logged, reviewed weekly)
- Turn Score < 0.50: FAIL (KILL-002 should have caught this; investigate detection gap)

### 9.2 Session-Level Scoring

A session (one play session, typically 50-100 narrations) is scored by aggregating turn scores:

```
Session Score = mean(Turn Scores)
Session Violation Count = count(Turn Score < 0.50)
```

**Session Health Thresholds:**
- Session Score >= 0.90 AND Violation Count = 0: HEALTHY
- Session Score >= 0.80 AND Violation Count <= 2: ACCEPTABLE
- Session Score < 0.80 OR Violation Count > 2: DEGRADED (trigger investigation)

### 9.3 Human Review Protocol (Weekly Calibration)

Each week, a human reviewer (DM or PM role) examines:

1. **20 randomly sampled narrations** (from production or golden scenarios)
2. **All narrations flagged as MARGINAL** by automated scoring
3. **All false-positive KILL-002 triggers** (narrations that were rejected but might have been acceptable)

The reviewer assigns their own Fidelity/Containment/Tone scores. Disagreements between automated and human scores are used to tune:
- Keyword lists (add missing terms, remove false-positive triggers)
- HP% severity band boundaries
- Regex patterns (tighten or relax)

### 9.4 Why Not Full-LLM Grading?

Using an LLM to grade every narration would be expensive (2-5s per narration, doubling inference cost) and introduces self-consistency bias (the same model family judging its own output). The hybrid approach -- fast automated checks for most turns, async LLM verification for edge cases, weekly human calibration -- balances cost, speed, and accuracy.

---

## 10. Adversarial Examples

These examples look plausible at first glance but violate one or more contract laws. They are designed as test cases for the detection pipeline.

### 10.1 Fidelity Violations (Plausible but Wrong)

**Example 1: Subtle Outcome Flip**

Truth Packet: `{event: "MISS", outcome: "miss", margin: -1, actor: "Fighter", target: "Orc", weapon: "longsword"}`

Adversarial Narration:
> "Your longsword whistles toward the orc's neck. At the last instant, the blade finds a gap in the crude armor and draws a thin line of blood -- but the orc shrugs off the scratch and readies its axe."

**Why it violates:** Despite the vivid description, "finds a gap" and "draws a thin line of blood" describe a HIT (weapon contacts flesh and draws blood). Box says MISS. A miss means the weapon did not connect with the target's body at all. The "shrugs off the scratch" is an attempt to reconcile the hit description with the miss outcome, but it still describes contact.

**Detection:** Tier 1 keyword scan detects "finds a gap", "draws blood" as hit-language in a MISS context.

---

**Example 2: Severity Inversion with Emotional Misdirection**

Truth Packet: `{event: "DAMAGE_DEALT", damage: 3, target_hp_percent: 95, target_status: "healthy"}`

Adversarial Narration:
> "The blow crashes into the orc with bone-crushing force! The creature howls in agony, staggering backward as blood pours from the devastating wound."

**Why it violates:** 3 damage against a target at 95% HP is a minor wound. "Bone-crushing force", "howls in agony", "blood pours", and "devastating wound" all describe a severe injury. The emotional language is internally consistent (sounds dramatic and well-written) but is disproportionate to the actual 5% HP loss.

**Detection:** Tier 1 HP proportionality check flags "devastating" when hp_percent > 85.

---

**Example 3: Invented Condition via Narrative Flourish**

Truth Packet: `{event: "HIT", damage: 8, active_conditions: []}`

Adversarial Narration:
> "Your mace strikes the goblin squarely in the temple! The creature's eyes cross and it drops to its knees, stunned by the force of the blow."

**Why it violates:** "Stunned" is a D&D 3.5e mechanical condition with specific game effects (lose Dex bonus to AC, cannot take actions). Box did not apply the stunned condition (`active_conditions: []`). Even though "stunned" could be read as colloquial English, in a D&D narration context it implies a mechanical condition that was never computed.

**Detection:** Tier 1 unauthorized effect scan detects "stunned" not in `active_conditions`.

### 10.2 Containment Violations (Plausible but Leaky)

**Example 4: Natural-Sounding ID Leak**

Truth Packet: `{actor_name: "Fighter", target_name: "Orc"}` (correctly filtered)

Adversarial Narration:
> "PC_Fighter brings his blade down on Orc_1 with practiced precision."

**Why it violates:** "PC_Fighter" and "Orc_1" are internal entity IDs, not display names. This indicates Spark somehow received or inferred internal IDs -- a Lens filtering failure if the Truth Packet was clean, or a Spark hallucination if it was.

**Detection:** Tier 1 regex scan detects underscore-delimited identifiers.

---

**Example 5: Rule Citation Disguised as Flavor**

Truth Packet: `{event: "AOO_TRIGGERED"}`

Adversarial Narration:
> "As you move past the orc, it lashes out -- as any trained warrior would when an enemy drops their guard within reach. The rules of engagement are clear."

**Why it violates:** "The rules of engagement are clear" is ambiguous but in a D&D narration context strongly implies rules-as-authority. While it could be read as in-world flavor ("rules of combat"), it edges toward Spark asserting knowledge of game rules.

**Detection:** This is a borderline case. Tier 1 regex may not catch it (no explicit "PHB" or "page N"). Tier 2 semantic check should flag the meta-reference. This is an example of why async semantic validation is needed alongside fast regex.

---

**Example 6: Grid Coordinate Laundered Through Description**

Truth Packet: `{event: "SPELL_CAST", spell_name: "Fireball", target_point: {x: 7, y: 4}}` (note: coordinates should be stripped by Lens before reaching Spark)

Adversarial Narration:
> "You cast Fireball at the intersection of the seventh and fourth gridlines, engulfing the orcs in flame."

**Why it violates:** "Seventh and fourth gridlines" is a natural-language laundering of grid coordinate (7,4). Even without parentheses and numbers, it reveals the exact grid position. Lens should have stripped coordinates and replaced with a natural-language anchor ("at the cluster of orcs near the door").

**Detection:** Tier 1 may miss this (no `(N,N)` pattern). Tier 2 semantic check should flag the coordinate-like spatial reference. This case argues for including "gridline" and "grid square" in the regex forbidden-word list.

### 10.3 Tone Bleeding Violations (Plausible but Mechanically Misleading)

**Example 7: Drama Invents Closeness**

Truth Packet: `{event: "MISS", outcome: "miss", margin: -8}` (missed by a lot)

Adversarial Narration (drama=0.9):
> "Your blade SCREAMS through the air, missing by a hair's breadth! The orc flinches as steel passes within inches of its throat!"

**Why it violates:** `margin: -8` means the attack missed by a wide margin (8 points below target AC). "Missing by a hair's breadth" and "within inches" describe a narrow miss (margin = -1 or -2). The drama setting caused the LLM to add false tension by implying the miss was close.

**Detection:** Tier 1 margin-tone calibration check: margin <= -5 should produce "goes wide" language, not "hair's breadth" language.

---

**Example 8: Humor Implies Different Contact Mode**

Truth Packet: `{event: "MISS", outcome: "miss", roll_total: 8, target_ac: 15}`

Adversarial Narration (humor=0.8):
> "Your sword bounces off the orc's helmet with a comical *CLANG*, sending reverberations up your arm as the orc looks at you with a mixture of pity and contempt."

**Why it violates:** "Bounces off the helmet" describes physical contact with the target (a deflection/armor block), not a miss. Box outcome "miss" means the attack did not connect. The humor setting caused the LLM to choose a funny-but-mechanically-incorrect contact description.

**Detection:** Tier 1 keyword scan detects "bounces off" as hit-language ("connects with armor") in a MISS context. This is a common humor-tone pitfall.

---

**Example 9: Grittiness Adds Unauthorized Environmental Effect**

Truth Packet: `{event: "SPELL_DAMAGE", spell: "Fireball", damage: 28, environmental_effects: ["smoke"]}`

Adversarial Narration (grittiness=0.9):
> "The fireball detonates with horrific force, charring the goblins where they stand. The blast wave ignites the wooden furniture, spreading fire across the room and creating hazardous, burning terrain."

**Why it violates:** "Ignites the wooden furniture" and "burning terrain" describe new environmental effects (fire spread, difficult/hazardous terrain) that Box did not compute. The `environmental_effects` list only contains "smoke". Grittiness caused the LLM to add realistic fire-spread consequences that would have mechanical implications (difficult terrain, fire damage on subsequent turns) if taken literally.

**Detection:** Tier 1 unauthorized effect scan flags "burning terrain" as not in `environmental_effects`.

---

## 11. Contradiction Notes and Resolutions

During synthesis, the following areas showed divergent or potentially contradictory positions across the three sub-findings. Each is documented with the resolution adopted for this contract.

### 11.1 Token Budget Discrepancy

**Sub-Finding A** allocates: System Prompt 800, Truth Packet 400, History 2500, Generation 512, Reserve 4000 (total allocated: 4212).

**Sub-Finding C** allocates: System Prompt 600 (base), Tone 100, NPC Voice 50, Truth Packet 400, History 2500, Generation 512, Reserve 3930 (total allocated: 4162).

**Discrepancy:** Sub-Finding A budgets 800 tokens for the system prompt as a monolithic block. Sub-Finding C breaks it into base (600) + tone (100) + NPC voice (50) = 750, which is 50 tokens less.

**Resolution:** Adopt Sub-Finding C's decomposed allocation (600 + 100 + 50 = 750 base). The 50-token savings over A's 800 provides useful headroom. The reserve remains ample at ~4000 tokens (safety factor ~2x). NPC voice tokens are only consumed when the event involves NPC dialogue, saving 50 tokens on most combat narrations.

### 11.2 Verification Approach for Tier 2 Slot Content

**Sub-Finding B** defines a 4-stage verification pipeline (structural validation, contradiction detection, HP proportionality, consistency check).

**Sub-Finding C** defines a 3-tier detection pipeline (keyword + regex realtime, semantic async, regression batch) with 6 violation categories.

**Discrepancy:** Sub-Finding B's "Stage 1: Structural Validation" (checking that actor/target/weapon names appear in output) is specific to slot-guided narration and does not appear in Sub-Finding C's more general pipeline.

**Resolution:** Merge both approaches. The structural validation from Sub-Finding B becomes an additional check within Tier 1 real-time detection, applied only for Tier 2 (slot-guided) narrations. The 6-category violation taxonomy from Sub-Finding C is adopted as the canonical classification system. The template anchoring optimization from Sub-Finding C (Section 7.3) subsumes Sub-Finding B's Stage 4 consistency check for template-augmented output.

### 11.3 Consistency Check Maturity

**Sub-Finding B** lists "Stage 4: Consistency Check" (comparing narration against recent narrations for contradictions) but marks it as "advanced, optional for Phase 1" with a stub implementation.

**Sub-Finding C** does not include a dedicated consistency/retcon check in its violation categories, though RQ-NARR-001-A Section 1.2D explicitly forbids retconning.

**Resolution:** Retcon detection (Category 7: "narration contradicts prior established narration") is acknowledged as a real risk but deferred to Phase 2. Phase 1 relies on the `recent_narrations` field in the Truth Packet giving Spark context to avoid contradictions, rather than post-hoc detection. A placeholder Category 7 is noted in the detection pipeline but not implemented until semantic comparison matures.

### 11.4 Environmental Flavor: Forbidden vs Allowed

**Sub-Finding A** Open Question Q3 asks whether Spark can add minor environmental details ("dust motes swirl") not in the Truth Packet. Recommendation: ALLOWED for non-mechanical details.

**Sub-Finding C** Category 6 (Unauthorized Effects) flags environmental keywords not in `environmental_effects`.

**Potential Contradiction:** If Spark adds "dust motes" (non-mechanical) it would not be in `environmental_effects`, potentially triggering a false positive in Category 6 detection.

**Resolution:** Category 6 detection scans only for **mechanically significant** environmental keywords (difficult terrain, concealment, cover, fire, ice). Non-mechanical atmospheric details (dust, echoes, shadows, smells) are explicitly excluded from the scan. The forbidden keyword list for Category 6 is:
- SCAN: "difficult terrain", "concealment", "cover", "prone", "ignited", "frozen", "hazardous terrain"
- DO NOT SCAN: "dust", "echoes", "shadows", "smell", "mist" (unless in `environmental_effects` as mechanical effects)

This resolves the tension: Spark can add atmospheric flavor (per Sub-Finding A Q3 recommendation) without triggering false positives (per Sub-Finding C Category 6), as long as the flavor does not describe mechanically significant terrain or conditions.

---

## 12. Open Questions Requiring PM Decision

These questions were raised across the three sub-findings and remain unresolved. Each requires a PM decision before the relevant work order can proceed.

### OQ-1: Margin Field Precision (from Sub-Finding A, Q1)

**Question:** Should the `margin` field in the Truth Packet be an exact integer or binned into named ranges?

**Option A:** Exact integer (e.g., `margin: 5`)
**Option B:** Binned ranges (e.g., `margin: "solid"`)

**Sub-Finding A Recommendation:** Option A (exact integer) -- gives Spark more flexibility for tone calibration.

**Synthesis Note:** This contract's margin-tone calibration table (Section 3, Dimension A) uses integer ranges, which works with either option. Option A is slightly preferred because it avoids losing information, and the binning can happen at the prompt-engineering layer if needed.

**Decision Needed Before:** WO-032 (NarrativeBrief Assembler)

### OQ-2: NPC Hidden Stats Visibility (from Sub-Finding A, Q2)

**Question:** Should the Truth Packet include target HP% when the player has no prior knowledge of the target?

**Option A:** Only include HP% if player has INFO about target (Knowledge check, prior combat)
**Option B:** Always include HP% for narrative wound descriptions

**Sub-Finding A Recommendation:** Option B -- Spark uses HP% for descriptive tone, not to reveal numbers. D&D 3.5e allows DM to describe wound severity narratively.

**Synthesis Note:** This contract requires HP% for the severity band check (Dimension A). If HP% is sometimes absent, the severity check is skipped for those narrations, creating an evaluation gap. Option B is more robust for the contract but may feel metagamey if Spark describes a wound precisely for an enemy the party just encountered.

**Decision Needed Before:** WO-032 (NarrativeBrief Assembler)

### OQ-3: KILL-002 Strictness (from Sub-Finding C, Q3)

**Question:** Should KILL-002 halt narration immediately (template fallback) or log and continue?

**Option A:** Immediate halt + template fallback + log
**Option B:** Log and send narration anyway + async audit
**Option C:** Warning mode (first 3 log only, 4th triggers halt)

**Sub-Finding C Recommendation:** Option A -- consistent with existing kill switch policy.

**Synthesis Note:** This contract assumes Option A throughout (the detection pipeline description in Section 6 specifies "discard LLM output, fall back one tier"). If PM prefers Option B or C, the pipeline response section must be revised.

**Decision Needed Before:** WO-029 (Kill Switch Suite)

### OQ-4: DM Override UX for Improvised Facts (from Sub-Finding C, Q1)

**Question:** When Spark improvises a scene detail (Strategy 3 from unknown handling), when is the DM notified?

**Option A:** Before narration sent (DM can veto)
**Option B:** After narration sent (DM can retroactively correct)
**Option C:** No notification (DM audits on demand)

**Sub-Finding C Recommendation:** Option B -- minimizes latency.

**Synthesis Note:** This question does not directly affect the narration balance contract (it concerns the unknown-handling workflow), but improvised facts tagged `[SPARK:IMPROVISED]` become part of the scene context for future narrations. If an improvised fact is later corrected by the DM, the system must handle the retcon gracefully -- which connects to the deferred Category 7 (retcon detection) work.

**Decision Needed Before:** WO-032 (NarrativeBrief Assembler)

### OQ-5: Default Tone Parameters (from Sub-Finding C, Q2)

**Question:** What are the default tone values for a new campaign?

**Option A:** Moderate defaults (verbosity=0.5, drama=0.5, humor=0.3, grittiness=0.4)
**Option B:** Campaign creation wizard selects tone
**Option C:** Adaptive (system learns from player feedback)

**Sub-Finding C Recommendation:** Option A + B (sensible defaults with wizard option).

**Synthesis Note:** The contract's tone scoring (Dimension C) evaluates against configured targets. Default values must be defined so that out-of-box campaigns have a scoring baseline. Option A provides this.

**Decision Needed Before:** WO-041 (DM Personality Layer)

### OQ-6: NPC Voice Mutability (from Sub-Finding C, Q4)

**Question:** Should NPC voice profiles be fixed after first generation, or evolve?

**Option A:** Fixed (locked after generation, DM override only)
**Option B:** Adaptive (evolve based on story events)
**Option C:** Hybrid (core traits fixed, minor traits adapt)

**Sub-Finding C Recommendation:** Option A -- consistency is critical for NPC recognition.

**Synthesis Note:** Not directly blocking for the narration balance contract, but NPC voice is one of the five tone parameters. If voices evolve, the tone consistency check must account for intentional evolution vs unintentional drift.

**Decision Needed Before:** WO-041 (DM Personality Layer)

---

## 13. Acceptance Criteria

This synthesis document is **APPROVED** when all of the following hold:

| # | Criterion | Status |
|---|---|---|
| 1 | Three evaluation dimensions defined with PASS/MARGINAL/FAIL criteria | DONE (Section 3) |
| 2 | Alignment rules (two absolute laws) stated with detection methods | DONE (Section 2) |
| 3 | 43 event labels consolidated with domain grouping and required fields | DONE (Section 4) |
| 4 | Three-tier augmentation model documented with routing logic | DONE (Section 5) |
| 5 | Violation detection pipeline defined (real-time + async + regression) | DONE (Section 6) |
| 6 | Target metrics specified (<1% violation, <5% false positive) | DONE (Section 7) |
| 7 | Regression harness with 4 golden scenarios and execution protocol | DONE (Section 8) |
| 8 | Scoring method that works without human judges for routine turns | DONE (Section 9) |
| 9 | Adversarial examples covering all three dimensions (9 examples) | DONE (Section 10) |
| 10 | Sub-finding contradictions documented with resolutions | DONE (Section 11) |
| 11 | Open questions listed with options and recommendations | DONE (Section 12) |

---

## 14. References

### Source Sub-Findings
- **RQ-NARR-001-A:** `docs/research/findings/RQ_NARR_001_A_OUTPUT_SPACE_AND_TRUTH_PACKET.md` -- Spark allowed output space, forbidden output types, gray area resolutions, Truth Packet schema, token budget, provenance tagging
- **RQ-NARR-001-B:** `docs/research/findings/RQ_NARR_001_B_TEMPLATES_AND_CONFIRMATION.md` -- 43 event label taxonomy, 3-tier augmentation model, slot-guided templates, verification pipeline, confirmation gates
- **RQ-NARR-001-C:** `docs/research/findings/RQ_NARR_001_C_UNKNOWNS_TONE_EVALUATION.md` -- Unknown handling strategies, tone control architecture, 6 violation categories, 3-tier detection pipeline, target metrics

### Architectural Documents
- **Spark-Lens-Box Doctrine:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` -- Axioms 2 (Box authority), 3 (Lens adaptation), 4 (provenance), 5 (no Spark writes)
- **Parent Research Question:** `docs/research/RQ_NARR_001_AI_NARRATIVE_BALANCE.md` -- Problem statement, 7 sub-questions, cross-references

### Implementation Targets
- **WO-027:** Canonical SparkAdapter Integration
- **WO-029:** Kill Switch Suite (KILL-002 implementation)
- **WO-032:** NarrativeBrief Assembler (Truth Packet construction)
- **WO-033:** Spark Integration Stress Test (golden scenario harness)
- **WO-041:** DM Personality Layer (tone parameters)

### Existing Code References
- `aidm/narration/narrator.py` -- Current template system (55 templates, Tier 1 baseline)
- `aidm/narration/guarded_narration_service.py` -- Existing guardrails (FREEZE-001, BL-003)
- `aidm/narration/llm_query_interface.py` -- LLM prompt templates (683 lines)
- `aidm/spark/spark_adapter.py` -- SparkRequest/SparkResponse interface

---

**END OF SYNTHESIS DOCUMENT**

**Next Steps:**
1. PM reviews and approves contract (this document)
2. PM resolves 6 open questions (Section 12)
3. Approved contract becomes binding input for WO-027, WO-029, WO-032, WO-033, WO-041
4. Implementation agents build against this contract; deviations require PM approval
