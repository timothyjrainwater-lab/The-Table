# WO-032: NarrativeBrief Assembler
**Dispatched by:** Opus (PM)
**Date:** 2026-02-11
**Phase:** 2A.1 (Narration Bridge)
**Priority:** Batch 1 (immediate)
**Status:** DISPATCHED

---

## Objective

Build the one-way valve that transforms Structured Truth Packets (STPs) into Spark-safe context. This is the Lens mediation layer for narration — Box→Lens→Spark, no shortcuts.

---

## Context

Currently, the play_loop_adapter.py (WO-030) builds a minimal EngineResult from narration tokens + events and passes it to GuardedNarrationService. The narration service either uses templates (55-template dictionary) or LLM generation via LLMQueryInterface.

What's missing: a structured intermediate representation (NarrativeBrief) that controls exactly what mechanical data Spark can see. Right now, the adapter passes raw event dicts. NarrativeBrief should be the formal containment boundary — a curated summary of what happened, stripped of internal IDs, raw HP values, and entity dictionaries.

---

## Package Structure

Create new directory `aidm/lens/` with `__init__.py`. This is the Lens layer's first real module.

**New files:**
- `aidm/lens/__init__.py`
- `aidm/lens/narrative_brief.py` — NarrativeBrief dataclass + assembler
- `aidm/lens/context_assembler.py` — Token-budget-aware context window builder
- `tests/test_narrative_brief.py`
- `tests/test_context_assembler.py`

---

## NarrativeBrief Specification

Frozen dataclass containing only Spark-safe data:

```python
@dataclass(frozen=True)
class NarrativeBrief:
    """One-way valve: STP → Spark-safe context. Lens layer."""

    # What happened (mechanical outcome, not raw numbers)
    action_type: str          # "attack_hit", "attack_miss", "spell_damage", etc.
    actor_name: str           # "Aldric the Bold" (not "fighter_1")
    target_name: Optional[str]  # "Goblin Warrior" (not "goblin_1")

    # Outcome description (safe to show)
    outcome_summary: str      # "Aldric hits the Goblin Warrior with a longsword"
    severity: str             # "minor", "moderate", "severe", "devastating", "lethal"

    # Context for narration quality (not raw state)
    weapon_name: Optional[str]       # "longsword" (not Weapon dataclass)
    damage_type: Optional[str]       # "slashing"
    condition_applied: Optional[str]  # "prone", "stunned", etc.
    target_defeated: bool             # True if entity_defeated event present

    # Scene context (for continuity)
    previous_narrations: list[str]    # Last N narration texts (for tone consistency)
    scene_description: Optional[str]  # Brief location context

    # Provenance
    source_event_ids: list[int]       # Which STP event IDs this was built from
    provenance_tag: str = "[DERIVED]" # Always DERIVED from BOX STPs
```

**What NarrativeBrief must NOT contain:**
- Entity IDs (internal identifiers)
- Raw HP values (current or max)
- AC values
- Attack bonuses or roll results
- Damage numbers
- Entity dictionaries
- Grid coordinates
- RNG state or seeds

**Severity mapping** (from truth packet fields):
- `minor`: damage < 20% of target max HP
- `moderate`: 20-40% of target max HP
- `severe`: 40-60% of target max HP
- `devastating`: 60-80% of target max HP
- `lethal`: target defeated or > 80% of max HP

The severity mapping requires reading entity HP from a FrozenWorldStateView snapshot (BL-020 enforced — read-only access).

---

## Context Assembler Specification

Builds the minimum-necessary context window for each Spark call.

```python
class ContextAssembler:
    """Assembles token-budget-aware context for Spark narration calls."""

    def __init__(self, token_budget: int = 800):
        """Token budget for input context (not output)."""

    def assemble(
        self,
        brief: NarrativeBrief,
        session_history: list[NarrativeBrief] = None,
    ) -> str:
        """Build context string within token budget.

        Priority order (highest first):
        1. Current NarrativeBrief (always included, ~100 tokens)
        2. Scene description (if available, ~50 tokens)
        3. Most recent narration texts (for continuity, ~200 tokens)
        4. Session history summaries (if budget allows)

        Returns formatted context string for Spark prompt.
        """
```

Token estimation: use `len(text.split()) * 1.3` as rough approximation (no tokenizer dependency required).

---

## Integration Points

1. **play_loop_adapter.py** — After WO-032, the adapter should construct a NarrativeBrief from events instead of passing raw event dicts. This integration happens in a follow-up WO or as part of WO-033. For WO-032, build the assembler and test it in isolation.

2. **GuardedNarrationService** — Eventually receives NarrativeBrief instead of (or in addition to) EngineResult. Again, the wiring happens after WO-032 delivers the building blocks.

3. **FrozenWorldStateView** — NarrativeBrief assembler reads entity names and severity data from a frozen view. Import from aidm.core.state. This is read-only access, compliant with BL-020.

---

## Acceptance Criteria

- [ ] `aidm/lens/` directory created with `__init__.py`
- [ ] NarrativeBrief dataclass contains no internal IDs, no raw HP values, no entity dictionaries, no grid coordinates
- [ ] Assembler constructs NarrativeBrief from list of STP event dicts + FrozenWorldStateView
- [ ] Severity mapping uses HP percentage thresholds, sourced from frozen view
- [ ] Entity names resolved from entity dicts (using "name" field, falling back to entity_id)
- [ ] Context Assembler respects token budget (never exceeds configured limit)
- [ ] Provenance: NarrativeBrief tagged as [DERIVED] from [BOX] STPs
- [ ] All existing tests pass (3302+, 0 regressions)
- [ ] ~30 new tests covering: brief construction, severity mapping, name resolution, token budget enforcement, edge cases (no target, missing fields, defeated entities)

---

## Boundary Laws

| Law | Enforcement |
|-----|-------------|
| BL-003 | No core imports in lens layer (use FrozenWorldStateView, not WorldState) |
| BL-004 | No mechanical logic in lens — NarrativeBrief describes outcomes, doesn't compute them |
| BL-020 | FrozenWorldStateView for all state reads — no mutation |
| Axiom 3 | Lens adapts stance, not authority — NarrativeBrief is presentation, not resolution |
| Axiom 5 | No SPARK→State writes — one-way valve |

---

## References

- Execution Plan: `docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md` lines 222-245
- Spark/Lens/Box Doctrine: `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md`
- Current adapter: `aidm/narration/play_loop_adapter.py`
- Current narration service: `aidm/narration/guarded_narration_service.py`
- FrozenWorldStateView: `aidm/core/state.py`
