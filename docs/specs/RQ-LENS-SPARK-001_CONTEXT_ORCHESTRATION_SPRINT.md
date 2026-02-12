# RQ-LENS-SPARK-001: Context Orchestration Research Sprint

**Domain:** Lens↔Spark Protocol Hardening
**Status:** DRAFT
**Filed:** 2026-02-12
**Gate:** Must pass before asset integration (TTS, image, music)
**Prerequisite:** WO-032, WO-039, WO-040, WO-041, WO-045, WO-046

---

## Thesis

The core architectural risk is not "can Spark write well enough?"
It is: **can Lens reliably manufacture the illusion of an infinite context window
while keeping Spark boxed into deterministic truth and bounded creativity?**

This is a systems problem. Not a prompt trick.

If Lens does not control context deterministically, the system will appear to
work for 20 turns and silently unravel over 200. Failures will be attributed
to assets (TTS, image, model quality) when the real cause is context
orchestration.

**Decision:** Freeze feature development. Formalize the Lens↔Spark protocol
before plugging in assets.

---

## What Exists Today (Grounded Assessment)

| Channel | Current Implementation | Gap |
|---|---|---|
| **Truth** | `NarrativeBrief` + `FrozenWorldStateView` — solid one-way valve | No post-hoc contradiction detection on Spark output |
| **Memory** | `ContextAssembler` (800-token budget, priority-ordered) | No retrieval engine, no salience ranking, no provenance on retrieved items |
| **Task** | Implicit — narration is the only task | No task discriminator, no per-task output schema |
| **Style** | `DMPersona` with `ToneConfig` (gravity/verbosity/drama) | Stable within session. Correct for v1 |
| **Output Contract** | `GrammarShield` (JSON + schema + mechanical assertion regex) | Catches `AC 18` but not `the ogre falls unconscious` when `target_defeated=False` |

**Built:** NarrativeBrief containment, ContextAssembler, SceneManager, DMPersona,
GrammarShield, GuardedNarrationService (M1 kill switches), NarrationTemplates (55+),
SessionOrchestrator (full turn cycle), IntentBridge, Box event contracts,
campaign memory schemas (SessionLedger, EvidenceLedger, ThreadRegistry).

**Missing:** PromptPack wire format, retrieval policy, summarization,
contradiction detection for world-state claims, evaluation harness,
multi-turn coherence infrastructure.

---

## Success Criteria (Exit Gate)

Across **100 deterministic turns**, Spark narration must:

- Produce **<1% contradiction rate** on entity-state and outcome claims
- **Zero** forbidden mechanics tokens escaping (existing GrammarShield baseline)
- Maintain coherent thread continuity without "expand on demand"
- Degrade cleanly to templates under parse/validation failure
- PromptPack assembly is **deterministic**: same inputs produce same prompt bytes
- Token budget is never exceeded; truncation never drops constraints

---

## Deliverable 1: PromptPack v1 Wire Format

### Problem

Prompt assembly is distributed across three call sites:
- `DMPersona.build_system_prompt()` → base persona + tone + action context + NPC hints
- `ContextAssembler.assemble()` → token-budgeted context string
- `GuardedNarrationService._build_llm_prompt()` → session facts + engine result

No single schema_version. No single truncation policy. No single place to test
deterministic assembly. No task polymorphism.

### Specification

```
@dataclass(frozen=True)
class PromptPack:
    """Deterministic, versioned, sectioned prompt wire object.

    Same inputs → same prompt bytes. Always.
    """

    # ── Protocol Identity ──
    schema_version: str          # "1.0.0" — semver, bump on section change
    task_type: TaskType          # Discriminator for output schema selection
    pack_id: str                 # Unique ID for tracing/debugging

    # ── Sections (ordered, each with own token budget) ──
    system_persona: str          # From DMPersona — base + tone modifiers
    truth_frame: str             # From NarrativeBrief — what is true right now
    memory_context: str          # From ContextAssembler — retrieved, scoped
    task_instruction: str        # Per-task instruction + output format
    style_constraints: str       # Tone knobs, provenance rules

    # ── Budget Metadata ──
    section_budgets: Dict[str, int]   # section_name → max_tokens
    total_budget: int                 # Sum of section budgets
    actual_tokens: int                # Estimated tokens after assembly
    truncation_log: List[str]         # What was dropped and why

    # ── Output Contract ──
    output_schema_id: str        # Maps to GrammarShield validation
    max_output_tokens: int       # Spark generation budget

    def to_prompt_string(self) -> str:
        """Deterministic assembly into final prompt bytes."""
        ...

    def content_hash(self) -> str:
        """SHA-256 of to_prompt_string() for determinism verification."""
        ...
```

### TaskType Enum (v1)

```python
class TaskType(str, Enum):
    NARRATE_COMBAT = "narrate_combat"
    NARRATE_EXPLORATION = "narrate_exploration"
    NARRATE_DIALOGUE = "narrate_dialogue"
    NARRATE_TRANSITION = "narrate_transition"
    SESSION_SUMMARY = "session_summary"        # Reserved, not implemented v1
    SCENE_PLANNING = "scene_planning"          # Reserved, not implemented v1
```

### Section Ordering and Truncation Rules

1. **system_persona** — NEVER truncated. Contains DM identity and constraints.
   Budget: 150 tokens.
2. **truth_frame** — NEVER truncated. Contains NarrativeBrief data that Spark
   must not contradict. Budget: 120 tokens.
3. **task_instruction** — NEVER truncated. Contains output format and forbidden
   patterns. Budget: 100 tokens.
4. **style_constraints** — Truncated last among constraints. Budget: 80 tokens.
5. **memory_context** — Truncated first. Recent narrations, scene description,
   session history. Budget: 350 tokens (adjustable per task_type).

**Truncation invariant:** Sections 1-3 always survive. If total exceeds budget,
memory_context is trimmed newest-to-oldest, then style_constraints are reduced
to minimum viable subset.

### Section Budget by TaskType

| TaskType | persona | truth | memory | task | style | total |
|---|---|---|---|---|---|---|
| NARRATE_COMBAT | 150 | 120 | 350 | 100 | 80 | 800 |
| NARRATE_EXPLORATION | 150 | 80 | 400 | 100 | 70 | 800 |
| NARRATE_DIALOGUE | 150 | 80 | 350 | 120 | 100 | 800 |
| NARRATE_TRANSITION | 150 | 100 | 300 | 120 | 80 | 750 |

### Determinism Contract

```python
def test_deterministic_assembly():
    """Same inputs → same prompt bytes → same content hash."""
    pack_a = build_prompt_pack(brief, history, persona, task_type)
    pack_b = build_prompt_pack(brief, history, persona, task_type)
    assert pack_a.to_prompt_string() == pack_b.to_prompt_string()
    assert pack_a.content_hash() == pack_b.content_hash()
```

---

## Deliverable 2: Memory Retrieval Policy

### Problem

`ContextAssembler` does priority-ordered token-budgeted assembly but has:
- No salience/recency ranking
- No provenance tags on retrieved items
- No hard caps beyond token budget
- No formalized drop order
- Campaign memory schemas exist but are never queried during narration

### Specification

For narration v1, retrieval is a **deterministic selection heuristic**, not
embedding search. This is sufficient and avoids a RAG dependency.

#### What Gets Retrieved

| Source | When | Max Items | Max Tokens |
|---|---|---|---|
| Current NarrativeBrief | Always | 1 | 120 |
| Scene description | Always if scene loaded | 1 | 60 |
| Recent narrations | Always | 3 | 180 |
| Session history summaries | If budget remains | 5 | remaining budget |

#### Ranking Function

For recent narrations, rank by:
1. **Recency** (most recent first — already implemented)
2. **Actor relevance** (same actor/target as current brief — new)
3. **Severity** (devastating/lethal events over minor — new)

Ranking is a simple score: `recency_weight * 0.5 + actor_match * 0.3 + severity_weight * 0.2`

This is a heuristic, not ML. It's deterministic given the same inputs.

#### Hard Caps

- **Count cap:** Maximum 3 recent narrations, 5 session summaries
- **Token cap:** Per-section budget from PromptPack (see Deliverable 1)
- **Total memory_context cap:** 350 tokens (combat), 400 tokens (exploration)
- **Drop order:** Session summaries first (oldest), then narrations (oldest),
  then scene detail

#### Provenance Tags

Every retrieved item carries:
```python
@dataclass(frozen=True)
class RetrievedItem:
    text: str
    source: str          # "narration", "session_summary", "scene", "brief"
    turn_number: int     # When this was generated
    relevance_score: float  # 0.0-1.0 from ranking function
    dropped: bool        # True if cut by truncation
    drop_reason: str     # "budget_exceeded", "cap_exceeded", ""
```

#### "Expand on Demand" — Deferred to v2

Spark requesting more context from Lens introduces a feedback loop that
breaks unidirectional flow (BL-004). Defer unless evaluation harness shows
>5% of turns produce incoherent narration due to insufficient context.

---

## Deliverable 3: Summarization Stability Protocol

### Problem

No multi-turn summarization exists. `ContextAssembler` passes raw recent
narrations. Over 200 turns, the window of "what Spark can see" drifts away
from what actually happened, with no way to detect or correct this.

### Specification (v1 — Minimal Viable)

#### When Summaries Are Created

- **Every 10 turns:** A session segment summary is generated
- **On scene transition:** The departing scene gets a scene summary
- **On combat end:** The combat encounter gets an encounter summary

#### Summary Format

```python
@dataclass(frozen=True)
class SessionSegmentSummary:
    segment_id: str
    turn_range: Tuple[int, int]      # (start_turn, end_turn)
    summary_text: str                # 2-3 sentences, factual
    key_facts: List[str]             # Bullet points of state changes
    entity_states: Dict[str, str]    # entity_name → status at segment end
    content_hash: str                # SHA-256 of inputs that generated this
    schema_version: str              # "1.0.0"
```

#### How Summaries Are Generated

**v1:** Template-based summarization from NarrativeBrief history.
Not LLM-generated. Deterministic.

```
"Turns {start}-{end}: {actor} engaged {target} in combat.
{hit_count} hits, {miss_count} misses. Severity: {max_severity}.
{defeated_list}. Scene: {scene_description}."
```

**v2 (future):** LLM-generated summaries with drift checks.

#### Drift Detection

Compare consecutive segment summaries for contradictions:

1. **Entity state consistency:** If segment N says "goblin defeated" and
   segment N+1 references the goblin acting, that's drift.
2. **Fact monotonicity:** Facts that cannot un-happen (defeat, death) are
   checked against future segments.
3. **Implementation:** Simple string-match checks against `entity_states` dict.
   No LLM needed for v1.

#### Rebuild-from-Sources Trigger

If drift is detected:
1. Log the drift event with both segments
2. Rebuild the drifted segment from raw NarrativeBrief history
3. Replace the stale summary
4. This is a deterministic operation (template-based)

---

## Deliverable 4: Contradiction Handling

### Problem

`GrammarShield` catches mechanical assertions (`AC 18`, `2d6 damage`) via regex.
It does NOT catch fictional state mutations:
- "the ogre falls unconscious" when `target_defeated=False`
- "you strike first" when `action_type=attack_miss`
- "the fireball ignites the table" when no environmental effect occurred

Players don't lose trust over `AC 18` leaking. They lose trust over
**false world-state claims** in narration.

### Contradiction Taxonomy v1

Three classes, ordered by severity:

#### Class A: Entity State Contradictions (Critical)

Spark claims an entity state that conflicts with the NarrativeBrief truth frame.

| NarrativeBrief Field | Contradiction Example | Check |
|---|---|---|
| `target_defeated=False` | "the goblin collapses" / "falls" / "dies" | Defeat keyword scan |
| `target_defeated=True` | No mention of defeat | Missing-claim check |
| `action_type=attack_miss` | "strikes" / "hits" / "wounds" | Hit keyword in miss context |
| `action_type=attack_hit` | "misses" / "fails to connect" | Miss keyword in hit context |
| `condition_applied=prone` | "stands tall" / "on their feet" | Stance contradiction |
| `severity=minor` | "devastating" / "brutal" / "crushing" | Severity inflation |
| `severity=lethal` | "barely scratches" / "minor wound" | Severity deflation |

#### Class B: Outcome Contradictions (High)

Spark claims mechanical outcomes not supported by the brief.

| Claim Type | Example | Check |
|---|---|---|
| Invented damage type | "acid burns" when `damage_type=slashing` | damage_type mismatch |
| Wrong weapon | "swings the mace" when `weapon_name=longsword` | weapon_name mismatch |
| Wrong actor | "the cleric attacks" when `actor_name=Thorin` | actor_name mismatch |
| Extra effects | "also catches fire" with no condition_applied | Unclaimed effect |

#### Class C: Continuity Contradictions (Medium)

Spark contradicts recent narration history.

| Claim Type | Example | Check |
|---|---|---|
| Resurrection | References defeated entity acting | Cross-ref entity_states |
| Location drift | "in the dungeon" when scene is "forest clearing" | scene_description check |

### Detection Implementation

```python
class ContradictionChecker:
    """Post-hoc contradiction detection against NarrativeBrief truth frame.

    Runs AFTER GrammarShield, BEFORE output delivery.
    """

    def check(
        self,
        narration_text: str,
        brief: NarrativeBrief,
        recent_summaries: List[SessionSegmentSummary],
    ) -> ContradictionResult:
        """
        Returns:
            ContradictionResult with class, severity, matched text,
            and recommended action (retry / annotate / template_fallback)
        """
        ...
```

### Response Policy

| Class | First Occurrence | Second Consecutive | Third Consecutive |
|---|---|---|---|
| **A (entity state)** | Retry with stricter prompt | Template fallback | Template fallback + log |
| **B (outcome)** | Retry with stricter prompt | Template fallback | Template fallback + log |
| **C (continuity)** | Annotate as [UNCERTAIN] | Retry | Template fallback |

**Retry prompt augmentation:**

When contradiction is detected, append to the PromptPack's task_instruction:

```
CORRECTION: Your previous narration contradicted the truth frame.
The target was {NOT defeated / hit / missed}. Severity is {severity}.
Weapon used: {weapon_name}. Do not claim otherwise.
```

### Keyword Dictionaries

```python
DEFEAT_KEYWORDS = [
    "falls", "collapses", "dies", "slain", "defeated", "unconscious",
    "crumples", "drops dead", "breathes? last", "life fades",
    "goes limp", "topples", "expires",
]

HIT_KEYWORDS = [
    "strikes", "hits", "wounds", "cuts", "slashes", "pierces",
    "connects", "lands", "bites into", "finds its mark",
    "draws blood", "carves", "cleaves",
]

MISS_KEYWORDS = [
    "misses", "fails", "goes wide", "deflected", "dodges",
    "parries", "evades", "sidesteps", "blocks", "glances off",
    "swings wild", "falls short",
]

SEVERITY_INFLATION = {
    "minor": ["devastating", "brutal", "crushing", "terrible", "crippling"],
    "moderate": ["devastating", "lethal", "fatal", "mortal"],
}

SEVERITY_DEFLATION = {
    "lethal": ["scratches", "barely", "minor", "glancing", "superficial"],
    "devastating": ["minor", "barely", "light", "superficial"],
}
```

---

## Deliverable 5: Evaluation Harness

### Problem

No way to measure whether Lens↔Spark is working. Template contract tests
exist but only verify template interpolation. No multi-turn coherence
measurement, no contradiction rate tracking, no budget stability verification.

### Metrics

| Metric | Definition | Target | Measurement |
|---|---|---|---|
| **Contradiction rate** | % of turns with Class A or B contradictions | <1% | ContradictionChecker over N turns |
| **Mechanics leak rate** | % of turns with GrammarShield violations | 0% | Existing GrammarShield |
| **Template fallback rate** | % of turns falling back to templates | <10% | Provenance tag counting |
| **Budget stability** | % of PromptPacks within budget | 100% | `actual_tokens <= total_budget` |
| **Truncation rate** | % of turns where memory_context was truncated | Measured, not targeted | truncation_log non-empty |
| **Continuity score** | % of turns where actor/target names match across consecutive narrations when they should | >95% | Name extraction from output |
| **Determinism** | % of PromptPacks that produce identical content_hash for identical inputs | 100% | Replay test |
| **Model-swap regression** | Contradiction rate delta when swapping Spark model | <2% delta | Run harness with model A, then model B |

### Scenario Scripts

```python
class EvaluationScenario:
    """A deterministic sequence of turns for evaluation."""

    scenario_id: str
    description: str
    turns: List[ScriptedTurn]  # Pre-defined actor_id + text_input pairs
    seed: int                  # RNG seed for deterministic Box resolution
    expected_invariants: List[Invariant]  # What must be true across all turns
```

#### Scenario 1: Sustained Combat (50 turns)

- 2 PCs vs 3 goblins
- Mixed hits/misses/crits/defeats
- Tests: entity state consistency, severity accuracy, defeat handling

#### Scenario 2: Scene Transition Chain (20 turns)

- 5 scene transitions with exploration between
- Tests: location continuity, scene description in context

#### Scenario 3: Mixed Mode (30 turns)

- Combat → exploration → rest → combat
- Tests: session state transitions, mode-appropriate narration

#### Scenario 4: Context Pressure (100 turns)

- Extended combat with many participants
- Tests: memory budget stability, truncation behavior,
  summarization (when implemented), long-term coherence

### Harness Runner

```python
class EvaluationHarness:
    """Runs scenario scripts and collects metrics."""

    def run_scenario(
        self,
        scenario: EvaluationScenario,
        spark_model_id: str,
    ) -> EvaluationReport:
        """
        Returns:
            EvaluationReport with all metrics, per-turn details,
            contradiction log, truncation log, and pass/fail against targets
        """
        ...

    def compare_models(
        self,
        scenario: EvaluationScenario,
        model_a: str,
        model_b: str,
    ) -> ComparisonReport:
        """Run same scenario with two models, report regression."""
        ...
```

### Report Format

```python
@dataclass
class EvaluationReport:
    scenario_id: str
    model_id: str
    total_turns: int
    contradiction_rate: float       # 0.0-1.0
    mechanics_leak_rate: float
    template_fallback_rate: float
    budget_stability: float         # 0.0-1.0
    truncation_rate: float
    continuity_score: float
    determinism_score: float
    per_turn_details: List[TurnEvaluation]
    contradiction_log: List[ContradictionEvent]
    truncation_log: List[TruncationEvent]
    passed: bool                    # All targets met?
```

---

## What We Will NOT Do (Scope Boundaries)

| Out of Scope | Reason |
|---|---|
| **"Expand on demand" feedback loop** | Breaks BL-004 unidirectional flow. Defer to v2 unless harness shows >5% context-starvation rate |
| **Campaign-authoring proposal/approval** | Requires Spark→Lens state writes, new boundary protocol. Scope contamination |
| **Full RAG with embedding search** | Deterministic heuristic retrieval is sufficient for narration v1 |
| **LLM-generated summaries** | Template summaries are deterministic and debuggable. LLM summaries add drift risk |
| **Semantic contradiction detection via LLM** | Too expensive, too unreliable. Keyword-based detection is v1 |
| **NPC dialogue generation** | Task type reserved but not implemented |
| **Multi-session persistence** | Campaign memory schemas exist but cross-session retrieval is deferred |
| **Voice/image/music integration** | This sprint is specifically about hardening Lens↔Spark BEFORE assets |

---

## Implementation Sequence

### Phase 1: PromptPack + Contradiction Checker

1. Define `PromptPack` dataclass with sections, budgets, truncation
2. Define `TaskType` enum and per-task budget tables
3. Refactor `DMPersona` + `ContextAssembler` + `GuardedNarrationService`
   to assemble through `PromptPack` (single assembly point)
4. Implement `ContradictionChecker` with Class A and B keyword checks
5. Wire contradiction checker into `GuardedNarrationService` post-hoc pipeline
6. Add determinism test: same inputs → same content_hash

### Phase 2: Retrieval Policy + Summarization

7. Formalize `ContextAssembler` retrieval with ranking function and hard caps
8. Add `RetrievedItem` provenance tracking
9. Implement `SessionSegmentSummary` (template-based)
10. Add 10-turn segment summary generation to `SessionOrchestrator`
11. Wire summaries into retrieval pipeline

### Phase 3: Evaluation Harness

12. Define `EvaluationScenario` and scripted turn format
13. Implement Scenario 1 (sustained combat, 50 turns)
14. Implement `EvaluationHarness` runner with metric collection
15. Implement Scenario 4 (context pressure, 100 turns)
16. Run harness, measure baseline, iterate on contradiction checker thresholds
17. Implement model comparison (run same scenario, two models, report delta)

### Exit Gate

All four scenarios pass with:
- Contradiction rate <1%
- Mechanics leak rate 0%
- Budget stability 100%
- Determinism 100%

Only then: proceed to asset integration.

---

## Relationship to Existing Work

| Existing Component | This Sprint's Change |
|---|---|
| `NarrativeBrief` | Unchanged — becomes truth_frame source |
| `ContextAssembler` | Refactored into PromptPack.memory_context builder with retrieval policy |
| `DMPersona` | Refactored into PromptPack.system_persona + style_constraints builder |
| `GrammarShield` | Unchanged — continues mechanical assertion detection |
| `GuardedNarrationService` | Gains ContradictionChecker post-hoc. Assembles via PromptPack |
| `SessionOrchestrator` | Gains segment summary generation every 10 turns. Passes PromptPack |
| `campaign_memory.py` schemas | Unchanged — SessionSegmentSummary is new, additive |
| Kill switch registry | Unchanged — new KILL-007 for contradiction threshold breach (optional) |

---

## Axiom Compliance

- **BL-003 (Lens No Core Imports):** PromptPack lives in Lens. No core imports.
- **BL-004 (One-Way Data Flow):** Box → Lens → Spark. No "expand on demand" in v1.
- **BL-020 (FrozenWorldStateView):** All reads via frozen view. Unchanged.
- **Axiom 2 (Spark Zero Authority):** Narration output has no mechanical effect. Unchanged.
- **Axiom 3 (Stance, Not Authority):** Lens adapts presentation. Unchanged.
- **Axiom 5 (No Spark→State Writes):** One-way valve via NarrativeBrief. Unchanged.
