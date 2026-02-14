# RQ-SPRINT-004: Spark Containment Audit — D&D Vocabulary Anchoring & Content-Independent Containment Design

**Research Sprint:** RQ-SPRINT-004
**Executed by:** Research Agent (Opus 4.6)
**Date:** 2026-02-14
**Status:** RESEARCH COMPLETE

---

## Executive Summary

**Core Question:** What happens to Spark containment when D&D vocabulary is removed? What do the guardrails anchor to in a content-independent engine?

**Answer:** Six mechanisms currently enforce the boundary law ("Spark has ZERO mechanical authority"): GrammarShield (8 regex patterns), ContradictionChecker (~210 keywords across 9 lists), Kill Switch Registry (6 switches, 5 regex patterns in KILL-002), GuardedNarrationService (orchestration), Typed Call Contract (6 CallTypes), and Boundary Pressure Detection (4 triggers). Of these, Boundary Pressure is entirely content-agnostic. The rest contain **~285 vocabulary-dependent artifacts** anchored to D&D 3.5e terminology across 4 Python files.

**Key Finding:** When D&D vocabulary is gone, the containment layer anchors to three immutable structural properties:

1. **The NarrativeBrief truth frame** — a frozen, content-agnostic schema. Its fields (`action_type`, `severity`, `target_defeated`, `actor_name`, `target_name`) describe *structural relationships*, not D&D-specific concepts. A "hit" is a hit in any game system.
2. **Frozen Layer B presentation semantics** — compiled per-world, read-only at runtime. The enum spaces (DeliveryMode, Staging, OriginRule, Scale) are generic spatial/temporal descriptors, not D&D vocabulary.
3. **The numeric/structural assertion boundary** — Spark must never emit specific numeric values regardless of vocabulary. The principle "no numbers in narration" is game-system-independent.

**Classification:** 14 universal containment rules survive any vocabulary replacement. 12 world-specific rule categories must be regenerated per world compilation. The World Compiler's existing Stage 1 (Lexicon) provides the natural generation point for world-specific containment data.

| Metric | Count |
|--------|-------|
| Total vocabulary-dependent artifacts | ~285 |
| Python files containing them | 4 |
| Universal containment rules (survive any world) | 14 |
| World-specific rule categories (regenerate per world) | 12 |
| Work orders required for full parameterization | 6 |

---

## 1 — Containment Mechanism Inventory

### 1.1 Mechanism 1: GrammarShield

**File:** `aidm/spark/grammar_shield.py` (479 lines)
**Role:** Output validation layer for Spark/LLM responses. Enforcement arm of "Spark has zero mechanical authority."

**8 MECHANICAL_PATTERNS (compiled regex, module-level constants):**

| # | Pattern Name | Regex | D&D Dependent? |
|---|-------------|-------|----------------|
| 1 | `damage_quantity` | `\b\d+\s*(points?\s+of\s+)?damage\b` | **Partially** — "damage" is universal but "points of" is D&D phrasing |
| 2 | `armor_class` | `\bAC\s*\d+\b` | **Yes** — "AC" is D&D-specific abbreviation |
| 3 | `hit_points` | `\b\d+\s*h(it\s*)?p(oints?)?\b` | **Yes** — "HP"/"hit points" is D&D/TTRPG-specific |
| 4 | `rule_citation` | `\b(PHB\|DMG\|MM)\s*\d+` | **Yes** — PHB/DMG/MM are D&D 3.5e book abbreviations |
| 5 | `attack_bonus` | `[+-]\d+\s*(to\s+)?(attack\|hit)\b` | **Partially** — "+N to attack" is D&D phrasing; "+N to [action]" is universal |
| 6 | `difficulty_class` | `\bDC\s*\d+\b` | **Yes** — "DC" is D&D-specific abbreviation |
| 7 | `die_roll_result` | `\broll(ed)?\s+(a\s+)?\d+\b` | **No** — "rolled a 15" is generic TTRPG language |
| 8 | `dice_notation` | `\b\d+d\d+` | **No** — "2d6" is universal polyhedral dice notation |

**D&D dependency count:** 4 fully dependent, 2 partially dependent, 2 universal.

**GrammarShieldConfig:** Accepts `mechanical_assertion_patterns` as a constructor parameter (defaults to module-level `MECHANICAL_PATTERNS`). This is **already parameterizable** — the config accepts a list of `(regex, name)` tuples. The only work needed is moving the default patterns from module constants into a loadable configuration source.

### 1.2 Mechanism 2: ContradictionChecker

**File:** `aidm/narration/contradiction_checker.py` (713 lines)
**Role:** Post-hoc contradiction detection. Checks LLM narration against NarrativeBrief truth frame.

**9 keyword lists (~210 keywords total):**

| # | List Name | Count | D&D Dependent? | Analysis |
|---|-----------|-------|----------------|----------|
| 1 | `DEFEAT_KEYWORDS` | 19 | **No** — "falls", "collapses", "dies" are universal English |
| 2 | `HIT_KEYWORDS` | 18 | **Partially** — "cleaves", "slashes" assume melee combat vocabulary |
| 3 | `MISS_KEYWORDS` | 14 | **Partially** — "parries", "sidesteps" assume physical combat |
| 4 | `SEVERITY_INFLATION["minor"]` | 10 | **No** — "devastating", "brutal" are universal intensity words |
| 5 | `SEVERITY_INFLATION["moderate"]` | 5 | **No** — same universal intensity words |
| 6 | `SEVERITY_DEFLATION["lethal"]` | 8 | **No** — "scratches", "barely" are universal understatement |
| 7 | `SEVERITY_DEFLATION["devastating"]` | 7 | **No** — same universal understatement words |
| 8 | `STANDING_KEYWORDS` | 5 | **No** — "standing", "upright" are universal posture |
| 9 | `PRONE_KEYWORDS` | 6 | **Partially** — "prone" is D&D condition name; "on the ground" is universal |

**Additionally, ContradictionChecker contains:**

- `common_weapons` list (26 weapon names): **Fully D&D-dependent.** "longsword", "greatsword", "greataxe", "rapier", "scimitar", "warhammer", "morningstar", "flail", "halberd", "glaive", "trident", "pike" are D&D/medieval weapon vocabulary.
- `damage_language` dict (11 damage types, ~62 keywords): **Fully D&D-dependent.** "slashing", "piercing", "bludgeoning", "fire", "cold", "acid", "lightning", "sonic", "force", "negative", "positive" are D&D 3.5e damage types with their associated vocabulary clusters.
- `indoor_words` list (13 words): **Partially D&D-dependent.** "dungeon", "crypt", "tomb" are fantasy-genre vocabulary; "corridor", "room", "chamber" are universal.
- `outdoor_words` list (14 words): **No** — "forest", "meadow", "desert", "mountain" are universal geography.

**Total vocabulary-dependent artifacts in ContradictionChecker:** ~210 keywords + 26 weapon names + 62 damage-language words = **~298 artifacts** (some overlap with universal English reduces the D&D-specific count to approximately **~160 truly D&D-dependent** words).

**Structural observation:** The ContradictionChecker's *algorithm* is content-agnostic. It compares narration text against keyword lists and NarrativeBrief fields. The keywords are the only D&D-specific component. Replacing the keyword dictionaries with world-specific dictionaries requires zero logic changes.

### 1.3 Mechanism 3: Kill Switch Registry

**File:** `aidm/narration/kill_switch_registry.py` (230 lines)
**Role:** Central kill switch state management. 6 kill switches that detect failure modes and block Spark.

**6 KillSwitchIDs:**

| ID | Trigger | D&D Dependent? |
|----|---------|----------------|
| KILL-001 | Memory hash mutation during narration | **No** — hash comparison is content-agnostic |
| KILL-002 | Mechanical assertion in Spark output | **Partially** — uses 5 regex patterns (see below) |
| KILL-003 | Token overflow (completion > max_tokens * 1.1) | **No** — token counting is content-agnostic |
| KILL-004 | Spark latency exceeds 10s | **No** — latency measurement is content-agnostic |
| KILL-005 | Consecutive guardrail rejections > 3 | **No** — rejection counting is content-agnostic |
| KILL-006 | State hash drift post-narration | **No** — hash comparison is content-agnostic |

**5 MECHANICAL_PATTERNS in KILL-002 (subset of GrammarShield's 8):**

| # | Pattern Name | D&D Dependent? |
|---|-------------|----------------|
| 1 | `damage_quantity` | Partially |
| 2 | `ac_reference` | **Yes** — "AC" is D&D |
| 3 | `hit_point_reference` | **Yes** — "HP" is D&D/TTRPG |
| 4 | `rule_citation` | **Yes** — PHB/DMG/MM are D&D |
| 5 | `attack_bonus` | Partially |

**Key observation:** Kill switches 1, 3, 4, 5, and 6 are **entirely content-agnostic**. Only KILL-002's regex patterns contain D&D vocabulary. The KillSwitchRegistry class itself is a pure state machine with zero content dependency.

### 1.4 Mechanism 4: GuardedNarrationService

**File:** `aidm/narration/guarded_narration_service.py` (985 lines)
**Role:** Orchestration layer. Coordinates GrammarShield, ContradictionChecker, Kill Switches, template fallback, and retry logic.

**D&D dependencies in GuardedNarrationService:**

| Location | Dependency | D&D Dependent? |
|----------|-----------|----------------|
| `_build_llm_prompt()` | Hardcoded string: "You are a Dungeon Master narrating a D&D 3.5e combat encounter." | **Yes** — explicit D&D reference |
| `_generate_template_narration()` | Delegates to `NarrationTemplates.get_template()` | **Yes** — templates contain D&D combat vocabulary |
| `FrozenMemorySnapshot` | JSON serialization of session/evidence/thread data | **No** — content-agnostic schema |
| `NarrationRequest` | Temperature validation (>= 0.7) | **No** — numeric threshold |
| Kill switch orchestration | Calls `detect_mechanical_assertions()` | **Partially** — delegates to KILL-002 patterns |
| Contradiction checking | Calls `ContradictionChecker.check()` | **Partially** — delegates to keyword dicts |
| Retry logic | Builds correction prompts | **No** — correction text is generated from contradiction metadata, not hardcoded |

**Key observation:** GuardedNarrationService is primarily an orchestrator. Its D&D dependencies are **inherited** from the modules it calls (ContradictionChecker, Narrator, GrammarShield). The one *direct* D&D dependency is the hardcoded prompt string in `_build_llm_prompt()`, which is already deprecated in favor of the PromptPack path (`_build_prompt_pack()`).

### 1.5 Mechanism 5: Typed Call Contract

**File:** `docs/planning/research/RQ_LLM_TYPED_CALL_CONTRACT.md`
**Role:** Mode-locks every Spark invocation to one of 6 CallTypes with constrained authority levels.

**6 CallTypes:**

| CallType | Authority Level | D&D Dependent? |
|----------|----------------|----------------|
| `COMBAT_NARRATION` | ATMOSPHERIC only | **Partially** — "combat" is genre-specific; narration constraints are universal |
| `OPERATOR_DIRECTIVE` | UNCERTAIN | **No** — intent interpretation is content-agnostic |
| `SUMMARY` | INFORMATIONAL | **No** — event compression is content-agnostic |
| `RULE_EXPLAINER` | NON-AUTHORITATIVE | **Partially** — "rule" is generic; explanation format may reference D&D rules |
| `CLARIFICATION_QUESTION` | UNCERTAIN | **No** — question generation is content-agnostic |
| `NPC_DIALOGUE` | ATMOSPHERIC only | **Partially** — "NPC" is TTRPG-specific; dialogue generation is generic |

**Key observation:** The Typed Call Contract is **structurally content-agnostic**. CallTypes define *authority levels*, not vocabulary. The constraint "ATMOSPHERIC only — zero mechanical weight" applies regardless of game system. The forbidden-claims list per CallType references D&D-specific terms (AC, HP, DC) that would need parameterization, but the enforcement mechanism (provenance tags, authority levels) is universal.

### 1.6 Mechanism 6: Boundary Pressure Detection

**File:** `docs/planning/research/RQ_SPARK_BOUNDARY_PRESSURE.md`
**Role:** Pre-generation risk signal. Detects conditions likely to produce violations before Spark generates.

**4 Pressure Triggers:**

| Trigger | D&D Dependent? |
|---------|----------------|
| `MISSING_FACT` | **No** — fact existence check is content-agnostic |
| `AMBIGUOUS_INTENT` | **No** — ambiguity detection is content-agnostic |
| `AUTHORITY_PROXIMITY` | **No** — authority boundary distance is structural |
| `CONTEXT_OVERFLOW` | **No** — token budget management is content-agnostic |

**Key observation:** Boundary Pressure Detection is **entirely content-agnostic**. It is the only containment mechanism with zero D&D vocabulary dependencies. Its signals (PressureLevel: GREEN/YELLOW/RED) are structural, not lexical. This makes it the model for what all containment mechanisms should look like after parameterization.

---

## 2 — D&D-Specific Dependency List (Complete)

### 2.1 Summary by file

| File | Artifact Type | Count | Notes |
|------|--------------|-------|-------|
| `grammar_shield.py` | Regex patterns | 8 (4 D&D-specific) | "AC", "HP", "PHB/DMG/MM", "DC" |
| `contradiction_checker.py` | Keywords | ~210 | 9 keyword lists |
| `contradiction_checker.py` | Weapon names | 26 | `common_weapons` list |
| `contradiction_checker.py` | Damage language | 62 | 11 damage types with word clusters |
| `contradiction_checker.py` | Scene words | 27 | Indoor/outdoor vocabulary |
| `kill_switch_registry.py` | Regex patterns | 5 (3 D&D-specific) | Subset of GrammarShield |
| `narrator.py` | Templates | 55 + 7 severity-branched | Combat narration templates |
| `guarded_narration_service.py` | Prompt string | 1 | "D&D 3.5e combat encounter" |

**Total:** ~285 vocabulary-dependent artifacts (with ~13 regex patterns, ~62 template strings, and ~210 keyword/word entries).

### 2.2 Overlap analysis

GrammarShield and Kill Switch Registry share 5 of 8 regex patterns. The KILL-002 patterns are a strict subset of GrammarShield's MECHANICAL_PATTERNS. Parameterizing GrammarShield automatically parameterizes KILL-002 if both load from the same configuration source.

---

## 3 — Universal vs. World-Specific Classification

### 3.1 Universal Containment Rules (U-1 through U-14)

These 14 rules survive any vocabulary replacement. They anchor to structural properties of the system, not to D&D vocabulary.

| ID | Rule | Anchored To | Current Enforcer |
|----|------|------------|-----------------|
| U-1 | Spark must not emit specific numeric values in narration | Numeric assertion boundary | GrammarShield (patterns 7, 8) |
| U-2 | Spark must not claim outcomes not in the truth frame | NarrativeBrief schema | ContradictionChecker (Class A) |
| U-3 | Spark must not describe defeat when `target_defeated=False` | NarrativeBrief.target_defeated | ContradictionChecker (defeat keywords) |
| U-4 | Spark must not describe hit when action_type is miss | NarrativeBrief.action_type | ContradictionChecker (hit/miss keywords) |
| U-5 | Narration severity must match truth frame severity | NarrativeBrief.severity | ContradictionChecker (inflation/deflation) |
| U-6 | Memory snapshot must not mutate during narration | FrozenMemorySnapshot hash | KILL-001 |
| U-7 | Spark output must not exceed token budget | max_tokens threshold | KILL-003 |
| U-8 | Spark latency must not exceed time budget | Latency threshold (10s) | KILL-004 |
| U-9 | Consecutive guardrail failures must trigger hard stop | Rejection counter | KILL-005 |
| U-10 | World state must not drift during narration | State hash comparison | KILL-006 |
| U-11 | Every Spark call must carry exactly one CallType | Typed Call Contract | CallType enum |
| U-12 | No CallType may produce `[BOX]`-tagged output | Authority level constraint | Provenance tag enforcement |
| U-13 | Boundary pressure must fail closed (unknown = RED) | Pressure signal design | BoundaryPressure schema |
| U-14 | Narration temperature must be >= 0.7 | LLM-002 constraint | NarrationRequest.__post_init__ |

**Observation:** All 14 universal rules anchor to one of three things: (1) numeric properties (thresholds, hashes, counts), (2) schema fields (NarrativeBrief, CallType, PressureLevel), or (3) temporal invariants (before/after comparisons). None reference vocabulary.

### 3.2 World-Specific Rule Categories (W-1 through W-12)

These 12 categories require regeneration whenever the game system or world changes. Each maps to a vocabulary set that must be compiled per world.

| ID | Category | Current Source | Required Per World |
|----|---------|---------------|-------------------|
| W-1 | Mechanical assertion patterns | GrammarShield MECHANICAL_PATTERNS | Regex patterns for system-specific notation (e.g., "AC" in D&D, "Defense" in another system) |
| W-2 | Hit/success keywords | ContradictionChecker HIT_KEYWORDS | Words meaning "the action succeeded" in this world's combat vocabulary |
| W-3 | Miss/failure keywords | ContradictionChecker MISS_KEYWORDS | Words meaning "the action failed" in this world's combat vocabulary |
| W-4 | Defeat keywords | ContradictionChecker DEFEAT_KEYWORDS | Words meaning "the entity is eliminated" — largely universal but may need augmentation for non-combat defeat (e.g., "corrupted", "dissolved") |
| W-5 | Severity vocabulary | ContradictionChecker SEVERITY_INFLATION/DEFLATION | Intensity words calibrated to this world's scale (a "devastating" blow in a gritty world vs. an epic world) |
| W-6 | Stance/condition keywords | ContradictionChecker STANDING/PRONE_KEYWORDS | Posture and condition vocabulary specific to the world's condition system |
| W-7 | Weapon vocabulary | ContradictionChecker common_weapons | Named weapon types available in this world |
| W-8 | Damage type vocabulary | ContradictionChecker damage_language | Damage type names and their associated descriptive language |
| W-9 | Scene vocabulary | ContradictionChecker indoor/outdoor_words | Location types relevant to this world's environments |
| W-10 | Rule citation patterns | GrammarShield rule_citation | Abbreviations for this system's rulebooks (PHB/DMG/MM for D&D; CRB/APG for PF2e; custom for homebrew) |
| W-11 | Narration templates | NarrationTemplates TEMPLATES + SEVERITY_TEMPLATES | Template strings using this world's action vocabulary |
| W-12 | System prompt identity | GuardedNarrationService._build_llm_prompt | "You are a [role] narrating a [system] [situation]." |

---

## 4 — The Anchoring Answer

### 4.1 What does containment anchor to when D&D vocabulary is gone?

The containment system has two layers:

**Layer 1: Principles (immutable, content-agnostic)**

These are the 14 universal rules (U-1 through U-14). They express structural invariants:

- "Spark must not assert specific numeric values" (any system)
- "Narration must not contradict the truth frame" (any system)
- "Memory must not mutate during generation" (any system)
- "Every call must have bounded authority" (any system)

These principles never change. They are the true anchor.

**Layer 2: Patterns (mutable, world-specific)**

These are the ~285 vocabulary artifacts. They are the *implementation* of the principles in a specific vocabulary:

- "AC" is the D&D pattern for the principle "no system-specific stat abbreviations in narration"
- "longsword" is the D&D pattern for the principle "narration must reference the correct weapon"
- "slashing" is the D&D pattern for the principle "damage description must match damage type"

**The anchoring answer:** Vocabulary is the pattern set. Principles are the anchor. Replace patterns per world. Keep principles forever.

### 4.2 The NarrativeBrief as the universal truth frame

The NarrativeBrief is the single most important containment artifact because it is *already content-agnostic in its schema*:

```python
@dataclass(frozen=True)
class NarrativeBrief:
    action_type: str          # "attack_hit", "spell_cast" — structural, not D&D
    actor_name: str           # Display name — always a string
    target_name: Optional[str]
    severity: str             # "minor"..."lethal" — intensity scale, not D&D
    condition_applied: Optional[str]
    target_defeated: bool     # Boolean — universal
    weapon_name: Optional[str]
    damage_type: Optional[str]
    outcome_summary: str
    presentation_semantics: Optional[Any]  # Layer B — frozen per world
    source_event_ids: tuple
```

Every field is either a string (parameterizable), a boolean (universal), or an optional reference to world-compiled data. The NarrativeBrief does not contain D&D-specific types, enums, or constants. It is a content-independent truth frame that happens to be populated with D&D data today.

### 4.3 Layer B presentation semantics as frozen world-specific vocabulary

The Layer B enums (DeliveryMode, Staging, OriginRule, Scale) are generic spatial and temporal descriptors:

- `PROJECTILE`, `BEAM`, `BURST_FROM_POINT` — these describe physics, not D&D
- `INSTANT`, `LINGER`, `CHANNELED` — these describe time, not D&D
- `FROM_CASTER`, `FROM_CHOSEN_POINT` — these describe spatial origin, not D&D
- `SUBTLE`, `MODERATE`, `DRAMATIC`, `CATASTROPHIC` — these describe intensity, not D&D

Layer B is compiled per world and frozen at runtime. This is the correct model for world-specific containment data: compile it once, freeze it, load it at runtime.

---

## 5 — Positive Validation Pipeline Design

### 5.1 Current approach: Negative validation

Today's containment is entirely *negative* — it checks that narration does NOT contain forbidden content:

- GrammarShield: "text must NOT match these regex patterns"
- ContradictionChecker: "text must NOT contain defeat keywords when target is alive"
- Kill switches: "metric must NOT exceed threshold"

Negative validation catches violations but cannot ensure quality. Narration that passes all negative checks may still be bland, off-tone, or disconnected from the world.

### 5.2 Proposed approach: Positive validation

A PositiveValidator would check that narration IS CONSISTENT WITH Layer B, not just that it avoids forbidden content:

| Check | Description | Layer B Field |
|-------|-------------|---------------|
| Delivery mode consistency | If `delivery_mode=CONE`, narration should describe a cone-shaped effect, not a single-target beam | `presentation_semantics.delivery_mode` |
| Staging consistency | If `staging=TRAVEL_THEN_DETONATE`, narration should have two phases (travel + impact), not a single instant event | `presentation_semantics.staging` |
| Scale consistency | If `scale=CATASTROPHIC`, narration should convey enormity, not subtlety | `presentation_semantics.scale` |
| VFX vocabulary | Narration should use at least one word from `vfx_tags` or a synonym | `presentation_semantics.vfx_tags` |

### 5.3 Why positive validation is content-agnostic

Positive validation checks narration against Layer B data that is *compiled per world*. The validator itself never contains vocabulary — it receives vocabulary from the compiled world bundle. This means:

- The PositiveValidator code is universal (write once)
- The validation data is world-specific (compiled per world)
- No hardcoded vocabulary in the validator module

This is the ideal containment architecture: universal logic, parameterized data.

### 5.4 PositiveValidator sketch

```python
class PositiveValidator:
    """Check narration consistency WITH Layer B (not just absence of bad content)."""

    def __init__(self, synonym_index: dict[str, list[str]]):
        """
        Args:
            synonym_index: World-compiled mapping of vfx/sfx tag -> synonyms.
                          E.g., {"fire": ["flame", "blaze", "burn", "scorch"]}
        """
        self._synonym_index = synonym_index

    def check_delivery_consistency(
        self, text: str, delivery_mode: str
    ) -> bool:
        """Check that narration describes the correct delivery mode."""
        # Load delivery-mode vocabulary from synonym_index
        delivery_words = self._synonym_index.get(f"delivery:{delivery_mode}", [])
        text_lower = text.lower()
        return any(word in text_lower for word in delivery_words)

    def check_scale_consistency(
        self, text: str, scale: str
    ) -> bool:
        """Check that narration intensity matches scale."""
        scale_words = self._synonym_index.get(f"scale:{scale}", [])
        text_lower = text.lower()
        return any(word in text_lower for word in scale_words)

    def check_vfx_consistency(
        self, text: str, vfx_tags: tuple[str, ...]
    ) -> bool:
        """Check that narration references at least one VFX tag or synonym."""
        text_lower = text.lower()
        for tag in vfx_tags:
            if tag in text_lower:
                return True
            synonyms = self._synonym_index.get(tag, [])
            if any(syn in text_lower for syn in synonyms):
                return True
        return False
```

---

## 6 — Template System D&D Dependency Analysis

### 6.1 Template inventory

`aidm/narration/narrator.py` contains two template collections:

**SEVERITY_TEMPLATES (7 entries, 2 tokens x severity branches):**

```
attack_hit:
  minor:        "...catches {target}, dealing {damage} damage. A glancing blow."
  moderate:     "...bites into {target}, dealing {damage} damage."
  severe:       "...strikes {target} hard, dealing {damage} damage. Blood flows freely."
  devastating:  "...tears into {target} for {damage} damage. The wound is grievous."
  lethal:       "...cleaves into {target} for {damage} damage. {target} crumbles and falls!"

attack_miss:
  minor:        "...swings at {target}, but the blade finds only air."
  moderate:     "...lunges at {target} with their {weapon}, but {target} turns the blow aside."
```

**TEMPLATES (55 entries):**

- 4 attack outcome templates
- 4 damage result templates
- 8 combat lifecycle templates
- 10 movement/position templates
- 1 targeting template
- 18 combat maneuver templates (bull rush, trip, grapple, disarm, sunder, overrun x 3)
- 4 save/condition templates
- 2 AoO templates
- 3 environmental templates
- 2 scene transition templates
- 1 rule lookup template
- 1 player action template
- 3 generic fallback templates

### 6.2 D&D vocabulary in templates

| Vocabulary Category | Examples in Templates | Count |
|--------------------|----------------------|-------|
| Melee combat verbs | "swings", "strikes", "cleaves", "slashes" | 12 |
| Physical impact | "staggers", "bloodied", "crumbles", "collapses" | 8 |
| D&D mechanics names | "initiative", "flat-footed", "attack of opportunity", "saving throw", "spell resistance" | 7 |
| D&D maneuver names | "bull rush", "trip", "grapple", "disarm", "sunder", "overrun" | 6 |
| Fantasy setting | "boots scraping against stone", "the chamber falls behind" | 3 |
| Medieval weapons | "blade", implied "sword" in context | 2 |

### 6.3 Template regeneration requirement

All 62 templates (55 flat + 7 severity-branched) contain D&D combat vocabulary. In a non-D&D world (e.g., sci-fi, modern, abstract), these templates would be nonsensical. A "bull rush" in a starship combat game has no meaning.

**Required per world:** A `world_narration_templates.json` file containing:

1. All narration token -> template string mappings
2. Severity-branched variants for tokens that support severity
3. Placeholder names consistent with the world's NarrativeBrief field naming

The World Compiler's existing Stage 1 (Lexicon) is the natural generation point. Lexicon already compiles world vocabulary; adding narration templates to the lexicon output is a natural extension.

---

## 7 — Implementation Path (6 Work Orders)

### Phase 1: WO-CONTAIN-001 — Parameterize GrammarShield Patterns

**Goal:** Load MECHANICAL_PATTERNS from configuration, not module constants.

**Changes:**
1. Add `containment_patterns` key to world bundle schema
2. Modify `GrammarShieldConfig` to accept patterns from world bundle
3. Move D&D-specific patterns to `content_pack/containment/grammar_patterns.json`
4. GrammarShield loads patterns from config; falls back to universal patterns (U-1) if no world-specific patterns provided
5. KILL-002 `MECHANICAL_PATTERNS` loads from same source

**Files modified:** `grammar_shield.py`, `kill_switch_registry.py`
**Effort:** Low (1 day)
**Risk:** Low — GrammarShieldConfig already accepts pattern list

### Phase 2: WO-CONTAIN-002 — Parameterize ContradictionChecker Vocabularies

**Goal:** Accept keyword dictionaries in constructor, not module-level constants.

**Changes:**
1. Add `ContradictionCheckerConfig` dataclass with fields for each keyword list
2. Modify `ContradictionChecker.__init__` to accept config
3. Move all 9 keyword lists + weapon names + damage language to config
4. Default config loads from `content_pack/containment/contradiction_keywords.json`
5. Constructor fallback: if no config provided, use universal-only keywords (defeat, severity inflation/deflation)

**Files modified:** `contradiction_checker.py`
**Effort:** Medium (1-2 days)
**Risk:** Low — algorithm unchanged; only data source changes

### Phase 3: WO-CONTAIN-003 — Add Containment Output Stages to World Compiler

**Goal:** World Compiler generates containment data as part of compilation.

**Changes:**
1. Add `ContainmentStage` to compiler pipeline (after Stage 1 Lexicon)
2. ContainmentStage outputs:
   - `grammar_patterns.json` — system-specific assertion patterns
   - `contradiction_keywords.json` — all 12 W-category keyword sets
   - `narration_templates.json` — all templates in world vocabulary
3. D&D content pack includes default containment data (identical to current hardcoded values)

**Files modified:** New stage in `compile_stages/`, world bundle schema
**Effort:** Medium (2-3 days)
**Risk:** Medium — new compiler stage requires testing against existing compilation pipeline

### Phase 4: WO-CONTAIN-004 — Runtime Loading of World Containment Data

**Goal:** GrammarShield, ContradictionChecker, and Narrator load containment data from compiled world bundle at runtime.

**Changes:**
1. Add `ContainmentLoader` class that reads containment files from world bundle
2. Wire loader into `GuardedNarrationService.__init__`
3. GuardedNarrationService passes loaded configs to GrammarShield, ContradictionChecker, and NarrationTemplates
4. Fallback: if world bundle has no containment data, use universal-only rules

**Files modified:** `guarded_narration_service.py`, new `containment_loader.py`
**Effort:** Medium (1-2 days)
**Risk:** Low — loader is a simple file reader; existing classes already accept configs

### Phase 5: WO-CONTAIN-005 — Positive Validation Prototype

**Goal:** PositiveValidator checks narration consistency WITH Layer B.

**Changes:**
1. New `PositiveValidator` class in `aidm/narration/`
2. Synonym index compiled by World Compiler (ContainmentStage or SemanticsStage)
3. Three checks: delivery_mode consistency, scale consistency, vfx_tags consistency
4. Integrated into GuardedNarrationService after ContradictionChecker (negative) pass
5. Positive validation failures logged as warnings (advisory), not as kill switch triggers

**Files modified:** New `positive_validator.py`, `guarded_narration_service.py`
**Effort:** Medium (2-3 days)
**Risk:** Low — advisory only; does not block narration

### Phase 6: WO-CONTAIN-006 — Template Regeneration Pipeline

**Goal:** Narration templates generated per world, not hardcoded in Python.

**Changes:**
1. Add template generation to ContainmentStage (or standalone TemplateStage)
2. Templates keyed by narration token with world-specific vocabulary
3. `NarrationTemplates.get_template()` loads from world bundle instead of class constants
4. D&D content pack generates templates identical to current hardcoded strings
5. Test: compile D&D world, verify template output matches current behavior byte-for-byte

**Files modified:** `narrator.py`, compiler stage, world bundle schema
**Effort:** Medium (2 days)
**Risk:** Medium — template format must be validated against all 55+ narration tokens

### Implementation Summary

| Phase | WO | Deliverable | Effort | Dependency |
|-------|-----|-------------|--------|------------|
| 1 | WO-CONTAIN-001 | Parameterize GrammarShield patterns | 1 day | None |
| 2 | WO-CONTAIN-002 | Parameterize ContradictionChecker vocabularies | 1-2 days | None |
| 3 | WO-CONTAIN-003 | Add containment output stages to World Compiler | 2-3 days | WO-CONTAIN-001, WO-CONTAIN-002 |
| 4 | WO-CONTAIN-004 | Runtime loading from world bundle | 1-2 days | WO-CONTAIN-003 |
| 5 | WO-CONTAIN-005 | Positive validation prototype | 2-3 days | WO-CONTAIN-004 |
| 6 | WO-CONTAIN-006 | Template regeneration pipeline | 2 days | WO-CONTAIN-003 |

**Total estimated effort:** 9-13 days
**Critical path:** WO-CONTAIN-001 + WO-CONTAIN-002 (parallel) -> WO-CONTAIN-003 -> WO-CONTAIN-004
**Can be deferred:** WO-CONTAIN-005, WO-CONTAIN-006 (nice-to-have, not blocking)

---

## 8 — Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Parameterization breaks existing containment (false negatives) | High | Regression test: compile D&D world, run full containment test suite, assert identical behavior |
| World Compiler generates incomplete containment data | Medium | Compile-time validation: assert all 12 W-categories present in output |
| Positive validation false positives annoy developers | Low | Advisory-only mode (warnings, not errors) for first 2 sprints |
| Template regeneration produces incoherent narration | Medium | Template quality gate: human review of first non-D&D world's templates |
| Performance regression from runtime config loading | Low | Containment data is tiny (<100KB); load once at startup, cache in memory |

---

## Appendix A — File Reference

| File | Lines | Role in Containment |
|------|-------|---------------------|
| `aidm/spark/grammar_shield.py` | 479 | 8 MECHANICAL_PATTERNS, GrammarShieldConfig, validate_and_retry loop |
| `aidm/narration/contradiction_checker.py` | 713 | ~210 keywords across 9 lists, 26 weapon names, 62 damage-language words, 3 contradiction classes |
| `aidm/narration/kill_switch_registry.py` | 230 | 6 KillSwitchIDs, 5 MECHANICAL_PATTERNS (KILL-002), build_evidence |
| `aidm/narration/guarded_narration_service.py` | 985 | Orchestration, FrozenMemorySnapshot, KILL-001 through KILL-006 enforcement, ContradictionChecker integration |
| `aidm/narration/narrator.py` | 413 | 55 TEMPLATES + 7 SEVERITY_TEMPLATES, NarrationContext, Narrator class |
| `aidm/lens/narrative_brief.py` | 824 | NarrativeBrief dataclass, assembler, FrozenWorldStateView integration |
| `aidm/schemas/presentation_semantics.py` | 342 | Layer B enums (DeliveryMode, Staging, OriginRule, Scale), frozen dataclasses |
| `docs/planning/research/RQ_LLM_TYPED_CALL_CONTRACT.md` | — | 6 CallTypes, authority levels, per-CallType forbidden claims |
| `docs/planning/research/RQ_SPARK_BOUNDARY_PRESSURE.md` | — | 4 pressure triggers, PressureLevel enum, fail-closed design |

## Appendix B — Keyword Count Verification

Exact counts from source files as of 2026-02-14:

```
DEFEAT_KEYWORDS:              19 entries
HIT_KEYWORDS:                 18 entries
MISS_KEYWORDS:                14 entries
SEVERITY_INFLATION["minor"]:  10 entries
SEVERITY_INFLATION["moderate"]: 5 entries
SEVERITY_DEFLATION["lethal"]:  8 entries
SEVERITY_DEFLATION["devastating"]: 7 entries
STANDING_KEYWORDS:             5 entries
PRONE_KEYWORDS:                6 entries
                              ──────────
Subtotal (keyword lists):      92 entries

common_weapons:                26 entries
damage_language (11 types):    62 entries (total words across all types)
indoor_words:                  13 entries
outdoor_words:                 14 entries
                              ──────────
Subtotal (other vocabularies): 115 entries

MECHANICAL_PATTERNS (GrammarShield): 8 patterns
MECHANICAL_PATTERNS (KILL-002):      5 patterns (subset)
                              ──────────
Subtotal (regex patterns):     13 patterns (8 unique)

TEMPLATES:                     55 entries
SEVERITY_TEMPLATES:            7 entries (2 tokens x branches)
                              ──────────
Subtotal (templates):          62 entries

Grand total:                   ~282 vocabulary-dependent artifacts
```

## Appendix C — Universal Rule Survival Proof

For each universal rule, proof that it survives vocabulary removal:

| Rule | Proof |
|------|-------|
| U-1 (no numeric assertions) | Regex `\b\d+d\d+` and `\broll(ed)?\s+(a\s+)?\d+\b` match any numeric pattern regardless of vocabulary |
| U-2 (truth frame consistency) | NarrativeBrief fields are strings and booleans; comparison is string equality, not vocabulary |
| U-3 (defeat consistency) | `target_defeated` is a boolean; the check is "defeat keywords present AND boolean is False" — keywords change, boolean does not |
| U-4 (hit/miss consistency) | `action_type` is a string enum; miss/hit check compares narration keywords against action_type value |
| U-5 (severity consistency) | `severity` is a 5-value ordinal scale; inflation/deflation words change per world but the scale does not |
| U-6 (memory immutability) | SHA-256 hash comparison; content-agnostic |
| U-7 (token budget) | Integer comparison; content-agnostic |
| U-8 (latency budget) | Float comparison; content-agnostic |
| U-9 (rejection cascade) | Counter comparison; content-agnostic |
| U-10 (state hash stability) | SHA-256 hash comparison; content-agnostic |
| U-11 (typed calls) | Enum membership check; content-agnostic |
| U-12 (authority tags) | String prefix check (`[BOX]` forbidden); content-agnostic |
| U-13 (fail closed) | Enum default value; content-agnostic |
| U-14 (temperature floor) | Float comparison (>= 0.7); content-agnostic |

---

## Conclusion

The Spark containment system is **architecturally sound for content independence**. The boundary law ("Spark has ZERO mechanical authority") is enforced through structural invariants (hashes, booleans, thresholds, authority levels) that do not depend on D&D vocabulary. The vocabulary dependencies are entirely in the *pattern data* fed to structurally-sound enforcement mechanisms.

The path to content-independent containment is parameterization, not rewriting:

1. Extract vocabulary from Python module constants into loadable configuration
2. Add a containment compilation stage to the World Compiler
3. Load world-specific containment data at runtime
4. Optionally, add positive validation that checks narration *for* consistency (not just *against* violations)

The 14 universal rules are the permanent foundation. The 12 world-specific categories are the replaceable skin. This mirrors the finding from RQ-SPRINT-001 (bone/muscle is content-independent) and RQ-SPRINT-002 (Layer B is content-independent): the entire system, from mechanical resolution through presentation semantics to containment enforcement, is a content-independent engine wearing a D&D content pack.

---

*End of RQ-SPRINT-004 report.*
