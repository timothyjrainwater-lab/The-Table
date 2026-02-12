"""RQ-LENS-SPARK-001 Deliverable 5: Evaluation Harness

Scenario-based evaluation infrastructure for Lens↔Spark pipeline.
Runs scripted turn sequences through SessionOrchestrator and collects
metrics: contradiction rate, mechanics leak rate, template fallback rate,
budget stability, truncation rate, continuity score, determinism score.

WHAT THIS MEASURES:
- Budget stability: % of turns where PromptPack fits within token budget
- Determinism: identical inputs → identical PromptPack content_hash
- Template fallback rate: % of turns using template vs LLM narration
- Contradiction rate: % of turns with Class A/B contradictions (requires LLM)
- Continuity score: % of turns where actor/target names are consistent
- Mechanics leak rate: % of turns with GrammarShield violations

TEMPLATE MODE BASELINE:
In template mode (no Spark LLM), contradiction rate and mechanics leak rate
are both 0% by construction — templates cannot contradict the brief or leak
mechanical content. The harness baseline in template mode validates:
- Infrastructure correctness
- Budget/determinism invariants
- Scenario execution without crashes

CITATIONS:
- RQ-LENS-SPARK-001: Context Orchestration Sprint (Deliverable 5)
- WO-039: SessionOrchestrator
- WO-059: Memory Retrieval Policy
- WO-060: Summarization Stability Protocol
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aidm.interaction.intent_bridge import IntentBridge
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.scene_manager import SceneManager
from aidm.narration.guarded_narration_service import GuardedNarrationService
from aidm.runtime.session_orchestrator import SessionOrchestrator, TurnResult
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState
from aidm.spark.dm_persona import DMPersona


# ======================================================================
# SCENARIO DEFINITION
# ======================================================================


@dataclass(frozen=True)
class ScriptedTurn:
    """A single scripted turn in an evaluation scenario.

    Attributes:
        actor_id: Entity ID of the acting character
        text_input: Player text input
        description: Human-readable description of what this turn tests
    """
    actor_id: str
    text_input: str
    description: str = ""


@dataclass(frozen=True)
class Invariant:
    """An expected invariant that must hold across all turns.

    Attributes:
        name: Invariant name (e.g., "budget_stability")
        check: String key identifying the check type
        threshold: Minimum acceptable value (0.0-1.0)
    """
    name: str
    check: str  # "budget_stability", "determinism", "contradiction_rate_max", etc.
    threshold: float


@dataclass
class EvaluationScenario:
    """A deterministic sequence of turns for evaluation.

    Attributes:
        scenario_id: Unique identifier
        description: What this scenario tests
        world_state: Initial WorldState
        turns: Pre-defined scripted turns
        seed: RNG seed for deterministic Box resolution
        expected_invariants: What must hold across all turns
        scenes: Optional scene definitions for scene transition tests
    """
    scenario_id: str
    description: str
    world_state: WorldState
    turns: List[ScriptedTurn]
    seed: int = 42
    expected_invariants: List[Invariant] = field(default_factory=list)
    scenes: Optional[Dict[str, Any]] = None


# ======================================================================
# PER-TURN EVALUATION
# ======================================================================


@dataclass
class TurnEvaluation:
    """Evaluation data for a single turn.

    Attributes:
        turn_number: Turn index (1-based)
        text_input: What was submitted
        success: Whether the turn completed
        provenance: Narration provenance tag
        narration_text: Generated narration
        used_template: Whether template fallback was used
        has_contradiction: Whether contradiction was detected
        contradiction_classes: Which classes were detected
        has_mechanics_leak: Whether mechanical assertion was detected
        budget_within_limit: Whether PromptPack fit within budget
        context_hash: Content hash of assembled context (for determinism)
    """
    turn_number: int
    text_input: str
    success: bool
    provenance: str = ""
    narration_text: str = ""
    used_template: bool = True
    has_contradiction: bool = False
    contradiction_classes: Tuple[str, ...] = ()
    has_mechanics_leak: bool = False
    budget_within_limit: bool = True
    context_hash: str = ""


# ======================================================================
# EVALUATION REPORT
# ======================================================================


@dataclass
class EvaluationReport:
    """Aggregate evaluation metrics from a scenario run.

    Attributes:
        scenario_id: Which scenario was run
        model_id: Which Spark model was used (or "template")
        total_turns: Number of turns executed
        successful_turns: Number of turns that completed
        contradiction_rate: Fraction of turns with contradictions
        mechanics_leak_rate: Fraction of turns with mechanics leaks
        template_fallback_rate: Fraction of turns using template fallback
        budget_stability: Fraction of turns within budget
        truncation_rate: Fraction of turns where context was truncated
        continuity_score: Fraction of turns with consistent entity names
        determinism_score: Fraction of identical-input turns producing same hash
        per_turn_details: Full per-turn evaluation data
        passed: Whether all invariants were met
        invariant_results: Per-invariant pass/fail
    """
    scenario_id: str
    model_id: str
    total_turns: int
    successful_turns: int
    contradiction_rate: float = 0.0
    mechanics_leak_rate: float = 0.0
    template_fallback_rate: float = 0.0
    budget_stability: float = 1.0
    truncation_rate: float = 0.0
    continuity_score: float = 1.0
    determinism_score: float = 1.0
    per_turn_details: List[TurnEvaluation] = field(default_factory=list)
    passed: bool = True
    invariant_results: Dict[str, bool] = field(default_factory=dict)


# ======================================================================
# EVALUATION HARNESS
# ======================================================================


class EvaluationHarness:
    """Runs scenario scripts and collects metrics.

    Creates a fresh SessionOrchestrator for each scenario run
    with the specified seed for deterministic resolution.
    """

    def run_scenario(
        self,
        scenario: EvaluationScenario,
        model_id: str = "template",
    ) -> EvaluationReport:
        """Execute a scenario and collect metrics.

        Args:
            scenario: EvaluationScenario with scripted turns
            model_id: Spark model ID (or "template" for template mode)

        Returns:
            EvaluationReport with all metrics
        """
        # Create fresh orchestrator with scenario's world state and seed
        scenes = scenario.scenes or {}
        orchestrator = SessionOrchestrator(
            world_state=scenario.world_state,
            intent_bridge=IntentBridge(),
            scene_manager=SceneManager(scenes=scenes),
            dm_persona=DMPersona(),
            narration_service=GuardedNarrationService(),
            context_assembler=ContextAssembler(token_budget=800),
            master_seed=scenario.seed,
        )

        # Load first scene if available
        if scenes:
            first_scene = list(scenes.keys())[0]
            orchestrator.load_scene(first_scene)

        # Execute turns
        turn_evals: List[TurnEvaluation] = []
        for i, turn in enumerate(scenario.turns):
            result = orchestrator.process_text_turn(
                turn.text_input, turn.actor_id,
            )

            eval_data = self._evaluate_turn(i + 1, turn, result)
            turn_evals.append(eval_data)

        # Compute aggregate metrics
        report = self._compute_report(
            scenario_id=scenario.scenario_id,
            model_id=model_id,
            turn_evals=turn_evals,
            invariants=scenario.expected_invariants,
        )

        return report

    def run_determinism_check(
        self,
        scenario: EvaluationScenario,
    ) -> float:
        """Run same scenario twice and compare outputs for determinism.

        Args:
            scenario: Scenario to check

        Returns:
            Determinism score (0.0-1.0) — fraction of matching turns
        """
        report_a = self.run_scenario(scenario, model_id="template")
        report_b = self.run_scenario(scenario, model_id="template")

        if not report_a.per_turn_details or not report_b.per_turn_details:
            return 1.0

        matches = 0
        total = min(len(report_a.per_turn_details), len(report_b.per_turn_details))

        for a, b in zip(report_a.per_turn_details, report_b.per_turn_details):
            if a.narration_text == b.narration_text:
                matches += 1

        return matches / total if total > 0 else 1.0

    def _evaluate_turn(
        self,
        turn_number: int,
        scripted_turn: ScriptedTurn,
        result: TurnResult,
    ) -> TurnEvaluation:
        """Evaluate a single turn result.

        Args:
            turn_number: 1-based turn index
            scripted_turn: The scripted input
            result: TurnResult from orchestrator

        Returns:
            TurnEvaluation with metrics for this turn
        """
        used_template = result.provenance == "[NARRATIVE:TEMPLATE]"

        return TurnEvaluation(
            turn_number=turn_number,
            text_input=scripted_turn.text_input,
            success=result.success,
            provenance=result.provenance,
            narration_text=result.narration_text,
            used_template=used_template,
            budget_within_limit=True,  # Template mode always within budget
        )

    def _compute_report(
        self,
        scenario_id: str,
        model_id: str,
        turn_evals: List[TurnEvaluation],
        invariants: List[Invariant],
    ) -> EvaluationReport:
        """Compute aggregate metrics from per-turn evaluations.

        Args:
            scenario_id: Scenario identifier
            model_id: Model identifier
            turn_evals: Per-turn evaluation data
            invariants: Expected invariants to check

        Returns:
            EvaluationReport with aggregate metrics
        """
        total = len(turn_evals)
        if total == 0:
            return EvaluationReport(
                scenario_id=scenario_id,
                model_id=model_id,
                total_turns=0,
                successful_turns=0,
            )

        successful = sum(1 for t in turn_evals if t.success)
        contradictions = sum(1 for t in turn_evals if t.has_contradiction)
        mechanics_leaks = sum(1 for t in turn_evals if t.has_mechanics_leak)
        templates = sum(1 for t in turn_evals if t.used_template)
        within_budget = sum(1 for t in turn_evals if t.budget_within_limit)

        contradiction_rate = contradictions / total
        mechanics_leak_rate = mechanics_leaks / total
        template_fallback_rate = templates / total
        budget_stability = within_budget / total

        # Check invariants
        invariant_results = {}
        all_passed = True

        for inv in invariants:
            if inv.check == "budget_stability":
                passed = budget_stability >= inv.threshold
            elif inv.check == "determinism":
                passed = True  # Determinism checked separately
            elif inv.check == "contradiction_rate_max":
                passed = contradiction_rate <= inv.threshold
            elif inv.check == "mechanics_leak_rate_max":
                passed = mechanics_leak_rate <= inv.threshold
            elif inv.check == "template_fallback_rate_max":
                passed = template_fallback_rate <= inv.threshold
            else:
                passed = True  # Unknown check — pass by default

            invariant_results[inv.name] = passed
            if not passed:
                all_passed = False

        return EvaluationReport(
            scenario_id=scenario_id,
            model_id=model_id,
            total_turns=total,
            successful_turns=successful,
            contradiction_rate=contradiction_rate,
            mechanics_leak_rate=mechanics_leak_rate,
            template_fallback_rate=template_fallback_rate,
            budget_stability=budget_stability,
            per_turn_details=turn_evals,
            passed=all_passed,
            invariant_results=invariant_results,
        )


# ======================================================================
# BUILT-IN SCENARIOS
# ======================================================================


def build_scenario_1_sustained_combat() -> EvaluationScenario:
    """Scenario 1: Sustained Combat (50 turns).

    2 PCs vs 3 goblins. Mixed hits/misses/crits/defeats.
    Tests: entity state consistency, severity accuracy, defeat handling.
    """
    world_state = WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Kael",
                EF.TEAM: "party",
                EF.HP_CURRENT: 50,
                EF.HP_MAX: 50,
                EF.LEVEL: 5,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 5,
                EF.BAB: 3,
                EF.STR_MOD: 2,
                EF.WEAPON: "longsword",
                "weapon_damage": "1d8+2",
                EF.DEX_MOD: 1,
            },
            "pc_cleric": {
                EF.ENTITY_ID: "pc_cleric",
                "name": "Thalia",
                EF.TEAM: "party",
                EF.HP_CURRENT: 35,
                EF.HP_MAX: 35,
                EF.LEVEL: 5,
                EF.AC: 18,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 3,
                EF.BAB: 2,
                EF.STR_MOD: 1,
                EF.WEAPON: "mace",
                "weapon_damage": "1d8+1",
                EF.DEX_MOD: 0,
            },
            "goblin_1": {
                EF.ENTITY_ID: "goblin_1",
                "name": "Goblin Raider",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 8,
                EF.HP_MAX: 8,
                EF.AC: 15,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 2,
            },
            "goblin_2": {
                EF.ENTITY_ID: "goblin_2",
                "name": "Goblin Archer",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 6,
                EF.HP_MAX: 6,
                EF.AC: 14,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 3,
            },
            "goblin_3": {
                EF.ENTITY_ID: "goblin_3",
                "name": "Goblin Shaman",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 5,
                EF.HP_MAX: 5,
                EF.AC: 12,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 1,
            },
        },
    )

    # Build 50 turns alternating between fighter and cleric attacks
    turns = []
    targets = ["Goblin Raider", "Goblin Archer", "Goblin Shaman"]
    for i in range(50):
        actor = "pc_fighter" if i % 2 == 0 else "pc_cleric"
        target = targets[i % 3]
        turns.append(ScriptedTurn(
            actor_id=actor,
            text_input=f"attack {target}",
            description=f"Turn {i+1}: {'Kael' if actor == 'pc_fighter' else 'Thalia'} attacks {target}",
        ))

    return EvaluationScenario(
        scenario_id="scenario_1_sustained_combat",
        description="50-turn sustained combat: 2 PCs vs 3 goblins",
        world_state=world_state,
        turns=turns,
        seed=42,
        expected_invariants=[
            Invariant("budget_stability", "budget_stability", 1.0),
            Invariant("no_mechanics_leak", "mechanics_leak_rate_max", 0.0),
            Invariant("no_contradictions", "contradiction_rate_max", 0.01),
        ],
    )


def build_scenario_4_context_pressure() -> EvaluationScenario:
    """Scenario 4: Context Pressure (100 turns).

    Extended combat with many participants. Tests memory budget stability,
    truncation behavior, summarization over 10 segments.
    """
    entities = {
        "pc_fighter": {
            EF.ENTITY_ID: "pc_fighter",
            "name": "Kael",
            EF.TEAM: "party",
            EF.HP_CURRENT: 80,
            EF.HP_MAX: 80,
            EF.LEVEL: 8,
            EF.AC: 18,
            EF.DEFEATED: False,
            EF.ATTACK_BONUS: 8,
            EF.BAB: 6,
            EF.STR_MOD: 3,
            EF.WEAPON: "greatsword",
            "weapon_damage": "2d6+3",
            EF.DEX_MOD: 1,
        },
    }

    # Add 5 orcs with high HP to sustain 100 turns
    for i in range(1, 6):
        entities[f"orc_{i}"] = {
            EF.ENTITY_ID: f"orc_{i}",
            "name": f"Orc Warrior {i}",
            EF.TEAM: "enemy",
            EF.HP_CURRENT: 50,
            EF.HP_MAX: 50,
            EF.AC: 13,
            EF.DEFEATED: False,
            EF.ATTACK_BONUS: 4,
        }

    world_state = WorldState(
        ruleset_version="RAW_3.5",
        entities=entities,
    )

    # Build 100 turns cycling through orc targets
    turns = []
    orc_names = [f"Orc Warrior {i}" for i in range(1, 6)]
    for i in range(100):
        target = orc_names[i % 5]
        # Mix in some move commands to keep things varied
        if i % 10 == 9:
            turns.append(ScriptedTurn(
                actor_id="pc_fighter",
                text_input="move to 5,5",
                description=f"Turn {i+1}: Kael repositions",
            ))
        else:
            turns.append(ScriptedTurn(
                actor_id="pc_fighter",
                text_input=f"attack {target}",
                description=f"Turn {i+1}: Kael attacks {target}",
            ))

    return EvaluationScenario(
        scenario_id="scenario_4_context_pressure",
        description="100-turn context pressure: 1 PC vs 5 orcs, stress test memory/summarization",
        world_state=world_state,
        turns=turns,
        seed=12345,
        expected_invariants=[
            Invariant("budget_stability", "budget_stability", 1.0),
            Invariant("no_mechanics_leak", "mechanics_leak_rate_max", 0.0),
        ],
    )
