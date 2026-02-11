# WO-033: Spark Integration Stress Test
**Dispatched by:** Opus (PM)
**Date:** 2026-02-11
**Phase:** 2A.2 (Narration Bridge)
**Priority:** Batch 2 (after WO-032)
**Status:** DISPATCHED
**Dependency:** WO-032 (NarrativeBrief) — INTEGRATED

---

## Objective

Run all 4 existing Gold Master scenarios (tavern, dungeon, field, boss) with real Spark backend integration, verifying that:
1. Box state determinism is unaffected by LLM narration
2. Kill switches (KILL-001 through KILL-006) trigger correctly on injected boundary violations
3. NarrativeBrief containment boundary holds — Spark never sees raw game state
4. Template fallback activates cleanly on simulated failures
5. Performance meets targets under real LLM load

---

## Context

Phase 1 wired the Spark brain: LlamaCppAdapter speaks canonical SparkRequest/SparkResponse, GuardedNarrationService enforces 6 kill switches, Grammar Shield validates output, and the play loop adapter generates narration for every combat action. Phase 2 Batch 1 added the NarrativeBrief one-way valve (WO-032) that mediates what Spark can see.

WO-033 is the stress test proving these pieces work together under realistic combat load. It runs the 4 pre-recorded Gold Master scenarios with narration injected at every turn, then verifies the core invariant: Box mechanical outcomes are identical whether narration comes from a real LLM or from templates.

---

## Package Structure

**New files:**
- `tests/test_spark_integration_stress.py` — ~40 tests

**Read-only references (DO NOT modify):**
- `tests/fixtures/gold_masters/tavern_100turn.jsonl`
- `tests/fixtures/gold_masters/dungeon_100turn.jsonl`
- `tests/fixtures/gold_masters/field_100turn.jsonl`
- `tests/fixtures/gold_masters/boss_100turn.jsonl`
- `aidm/testing/replay_regression.py` — GoldMaster, ReplayRegressionHarness
- `aidm/testing/scenario_runner.py` — ScenarioRunner, ScenarioMetrics
- `aidm/narration/play_loop_adapter.py` — generate_narration_for_turn()
- `aidm/narration/guarded_narration_service.py` — GuardedNarrationService
- `aidm/narration/kill_switch_registry.py` — KillSwitchRegistry, KillSwitchID
- `aidm/lens/narrative_brief.py` — NarrativeBrief, assemble_narrative_brief()
- `aidm/lens/context_assembler.py` — ContextAssembler
- `aidm/spark/spark_adapter.py` — SparkRequest, SparkResponse, LoadedModel
- `aidm/spark/llamacpp_adapter.py` — LlamaCppAdapter
- `aidm/spark/grammar_shield.py` — GrammarShield

**Do NOT modify any production code.** This is a read-only test work order.

---

## Test Architecture

### Strategy: Dual-Path Comparison

Each scenario runs twice with the same seed:
1. **Template path** — No LLM loaded, GuardedNarrationService falls back to templates
2. **LLM path** — Real LLM loaded (or mock LLM that generates plausible narration text)

After both runs, compare Box final state hashes. They MUST be identical. The narration text will differ (that's the point), but the mechanical outcomes must not.

### Hardware Gating

Tests that require a real GPU/model should be gated with:
```python
@pytest.mark.skipif(
    not _gpu_available(),
    reason="No GPU available for Spark integration test"
)
```

Tests that use mock LLM responses should run on all hardware.

---

## Test Categories (~40 tests)

### 1. Determinism Verification (8 tests)

For each of the 4 scenarios (tavern, dungeon, field, boss):

```python
def test_{scenario}_determinism_template_vs_llm():
    """Box state hash identical regardless of narration path."""
    # Run scenario with template narration, record final_state_hash
    # Run scenario with mock LLM narration, record final_state_hash
    # Assert hashes match

def test_{scenario}_10x_replay_with_narration():
    """10x replay produces identical Box state with narration injected."""
    # Load Gold Master
    # Replay 10 times with narration at each turn
    # All 10 final_state_hashes must match Gold Master
```

### 2. NarrativeBrief Containment (8 tests)

```python
def test_narrative_brief_no_entity_ids():
    """NarrativeBrief assembled during scenario contains no internal entity IDs."""
    # Run scenario, collect all NarrativeBriefs
    # Scan all fields for patterns like "fighter_1", "goblin_01", etc.

def test_narrative_brief_no_raw_hp():
    """NarrativeBrief assembled during scenario contains no raw HP values."""
    # Verify no numeric HP data in any brief

def test_narrative_brief_no_grid_coordinates():
    """NarrativeBrief contains no grid coordinate data."""
    # Verify no Position or (x,y) tuples in any brief field

def test_narrative_brief_severity_mapping():
    """Severity categories match HP percentage thresholds."""
    # Verify severity is one of: minor, moderate, severe, devastating, lethal
    # Cross-reference with known damage events in scenario

def test_narrative_brief_provenance_tagged():
    """All NarrativeBriefs tagged as [DERIVED]."""
    # Every brief.provenance_tag == "[DERIVED]"

def test_context_assembler_token_budget():
    """Context assembled for Spark never exceeds token budget."""
    # Run scenario, assemble context at each turn
    # Verify estimated tokens <= configured budget

def test_narrative_brief_from_frozen_view():
    """NarrativeBrief reads entity names from FrozenWorldStateView."""
    # Verify actor_name and target_name are display names, not IDs

def test_spark_receives_brief_not_state():
    """Spark prompt contains NarrativeBrief context, not raw WorldState."""
    # Intercept Spark calls, verify prompt does not contain entity dicts
```

### 3. Kill Switch Injection (12 tests)

Each kill switch tested with intentional violation injection:

```python
def test_kill_001_memory_hash_mutation():
    """KILL-001: Memory hash mismatch triggers kill switch."""
    # Mutate FrozenMemorySnapshot hash between narration calls
    # Verify kill switch triggers and template fallback activates

def test_kill_002_mechanical_assertion():
    """KILL-002: Spark output with damage numbers triggers kill switch."""
    # Mock LLM to return "The goblin takes 15 damage"
    # Verify KILL-002 triggers, text is rejected, template used

def test_kill_003_token_overflow():
    """KILL-003: Spark output exceeding max_tokens * 1.1 triggers kill switch."""
    # Mock LLM to return text 20% over max_tokens limit
    # Verify KILL-003 triggers

def test_kill_004_latency_exceeded():
    """KILL-004: Spark latency >10s triggers kill switch."""
    # Mock LLM with 11-second delay
    # Verify KILL-004 triggers, template fallback activates

def test_kill_005_consecutive_rejections():
    """KILL-005: 4 consecutive guardrail rejections triggers kill switch."""
    # Mock LLM to return mechanical assertions 4 times in a row
    # Verify KILL-005 triggers after 4th rejection (threshold is 3)

def test_kill_006_state_hash_drift():
    """KILL-006: World state hash change during narration triggers kill switch."""
    # Provide mismatched before/after world state hashes
    # Verify KILL-006 triggers

def test_kill_switch_persists_across_turns():
    """Triggered kill switch persists — not auto-reset between turns."""
    # Trigger KILL-002, advance several turns
    # Verify kill switch still active, all subsequent narration uses templates

def test_kill_switch_manual_reset():
    """Kill switch only clears via manual reset."""
    # Trigger KILL-003
    # Verify is_triggered() returns True
    # Call reset()
    # Verify is_triggered() returns False

def test_kill_switch_template_fallback():
    """Template fallback produces valid narration when kill switch active."""
    # Trigger any kill switch
    # Verify subsequent narration calls return template text
    # Verify provenance is "[NARRATIVE:TEMPLATE]"

def test_kill_switch_evidence_captured():
    """Kill switch evidence includes timestamp, trigger signal, and stack trace."""
    # Trigger KILL-002
    # Retrieve evidence, verify all fields populated

def test_multiple_kill_switches_simultaneous():
    """Multiple kill switches can be active simultaneously."""
    # Trigger KILL-002 and KILL-004
    # Verify both active, both have evidence

def test_any_triggered_fast_path():
    """any_triggered() is O(1) fast check."""
    # Verify behavioral contract — fast path without iterating all switches
```

### 4. Template Fallback (4 tests)

```python
def test_template_fallback_on_no_model():
    """No model loaded → all narration via templates."""
    # Create GuardedNarrationService with loaded_model=None
    # Run scenario, verify all narration is template-generated
    # Verify provenance is "[NARRATIVE:TEMPLATE]"

def test_template_fallback_seamless():
    """Player cannot detect fallback — narration text is valid English."""
    # Run scenario in template mode
    # Verify all narration_text is non-empty string

def test_template_fallback_all_55_tokens():
    """All 55 narration tokens produce valid template text."""
    # For each narration token in the template dictionary
    # Verify non-empty, non-None template text returned

def test_template_fallback_after_kill_switch():
    """After kill switch trigger, template narration continues per-turn."""
    # Run scenario, trigger KILL-002 mid-scenario
    # Verify all subsequent turns use template narration
    # Verify Box state continues advancing normally
```

### 5. Performance (4 tests — GPU-gated)

```python
@pytest.mark.skipif(not _gpu_available(), reason="Requires GPU")
def test_llm_narration_latency_p95():
    """LLM narration path: p95 latency <3s per action."""
    # Run tavern scenario with real LLM
    # Collect per-action narration latency
    # Assert p95 < 3000ms

@pytest.mark.skipif(not _gpu_available(), reason="Requires GPU")
def test_template_narration_latency_p95():
    """Template narration path: p95 latency <500ms per action."""
    # Run tavern scenario in template mode
    # Collect per-action narration latency
    # Assert p95 < 500ms

@pytest.mark.skipif(not _gpu_available(), reason="Requires GPU")
def test_full_scenario_completion_time():
    """Full 100-turn scenario completes in reasonable time with LLM."""
    # Run tavern scenario with LLM
    # Assert total time < 300s (generous bound)

@pytest.mark.skipif(not _gpu_available(), reason="Requires GPU")
def test_grammar_shield_validation_under_load():
    """Grammar Shield validates all LLM outputs during full scenario."""
    # Run scenario with Grammar Shield enabled
    # Verify validation count matches narration count
    # Verify no silent validation failures
```

### 6. Gold Master Compatibility (4 tests)

```python
def test_tavern_gold_master_replay_with_narration():
    """Tavern Gold Master replays correctly with narration injected."""
    # Load tavern_100turn.jsonl
    # Replay with template narration at each event
    # Final state hash matches Gold Master

def test_dungeon_gold_master_replay_with_narration():
    """Same for dungeon scenario."""

def test_field_gold_master_replay_with_narration():
    """Same for field scenario."""

def test_boss_gold_master_replay_with_narration():
    """Same for boss scenario."""
```

---

## Key Interfaces to Use

### Loading Gold Masters
```python
from aidm.testing.replay_regression import GoldMaster
gm = GoldMaster.load("tests/fixtures/gold_masters/tavern_100turn.jsonl")
```

### Running Scenarios
```python
from aidm.testing.scenario_runner import ScenarioRunner, ScenarioConfig
runner = ScenarioRunner(config)
metrics = runner.run()
```

### Generating Narration
```python
from aidm.narration.play_loop_adapter import generate_narration_for_turn
text, provenance = generate_narration_for_turn(
    narration_token="attack_hit",
    events=[...],
    actor_id="fighter_1",
    actor_name="Aldric",
    target_id="goblin_1",
    target_name="Goblin",
    weapon_name="longsword",
    world_state_hash=state_hash,
    narration_service=service,
)
```

### Assembling NarrativeBrief
```python
from aidm.lens.narrative_brief import assemble_narrative_brief, NarrativeBrief
from aidm.core.state import FrozenWorldStateView
brief = assemble_narrative_brief(
    events=stp_events,
    narration_token="attack_hit",
    frozen_view=frozen_view,
)
```

### Kill Switch Operations
```python
from aidm.narration.kill_switch_registry import KillSwitchRegistry, KillSwitchID
registry = KillSwitchRegistry()
registry.trigger(KillSwitchID.KILL_002, evidence)
assert registry.is_triggered(KillSwitchID.KILL_002)
registry.reset(KillSwitchID.KILL_002)
```

### Mock LLM for Non-GPU Tests
```python
class MockLlamaCppAdapter:
    """Returns controlled narration text for testing."""
    def generate(self, request: SparkRequest, loaded_model=None) -> SparkResponse:
        return SparkResponse(
            text="The blade strikes true, sparks flying.",
            finish_reason=FinishReason.COMPLETED,
            tokens_used=len(request.prompt.split()) + 8,
        )
```

---

## Acceptance Criteria

- [ ] All 4 scenarios complete with template narration (no GPU required)
- [ ] Determinism: Box state hash identical between template and mock-LLM paths
- [ ] 10x replay produces identical Box state with narration injected
- [ ] NarrativeBrief containment verified — no entity IDs, raw HP, coordinates
- [ ] All 6 kill switches tested with intentional violation injection
- [ ] Kill switch persistence verified (no auto-reset)
- [ ] Template fallback activates on kill switch trigger
- [ ] Evidence capture complete (timestamp, signal, stack trace)
- [ ] Context Assembler token budget never exceeded
- [ ] Gold Masters replay correctly with narration injected
- [ ] Performance tests GPU-gated with appropriate skip markers
- [ ] All existing tests pass (3452+, 0 regressions)
- [ ] ~40 new tests

---

## Boundary Laws

| Law | Enforcement |
|-----|-------------|
| BL-020 | FrozenWorldStateView for all non-engine state reads |
| BL-003 | No core imports in lens/narration layers |
| Axiom 2 | Box is sole mechanical authority — narration cannot change outcomes |
| Axiom 5 | No SPARK→State writes — verified by hash comparison |
| FREEZE-001 | Memory hash verification at narration boundary |

---

## References

- Execution Plan: `docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md` lines 248-268
- Gold Masters: `tests/fixtures/gold_masters/`
- Replay infrastructure: `aidm/testing/replay_regression.py`
- Scenario runner: `aidm/testing/scenario_runner.py`
- Kill switch registry: `aidm/narration/kill_switch_registry.py`
- Guarded narration: `aidm/narration/guarded_narration_service.py`
- NarrativeBrief: `aidm/lens/narrative_brief.py`
- Context assembler: `aidm/lens/context_assembler.py`
- Play loop adapter: `aidm/narration/play_loop_adapter.py`
- Spark contracts: `aidm/spark/spark_adapter.py`
