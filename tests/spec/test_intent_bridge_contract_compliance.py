"""Intent Bridge Contract Compliance Tests.

WO-CODE-INTENT-002: End-to-end compliance tests for the Intent Bridge
pipeline. Tests verify:

1. DETERMINISM: Same inputs produce identical outputs (10x replay)
2. CANDIDATE ORDERING: Disambiguation candidates sorted lexicographically
3. NO-COACHING: Clarification prompts never reveal mechanical information
4. AUTHORITY BOUNDARY: Bridge never computes mechanics or mutates state
5. LIFECYCLE: CONFIRMED intents are immutable (BL-014)
6. CONTENT INDEPENDENCE: No source-material-specific vocabulary in pipeline

Evidence:
- Intent Bridge Contract: docs/contracts/INTENT_BRIDGE.md
- PHB p.50: Clarification should not reveal rogue capabilities
- AD-006: House Policy Governance (No-Opaque-DM)
- Manifesto: No mercy, no hand-holding, no system that warns
"""

import json
import os
import re
import pytest
import yaml

from aidm.interaction.intent_bridge import (
    IntentBridge,
    AmbiguityType,
    ClarificationRequest as BridgeClarification,
)
from aidm.immersion.voice_intent_parser import (
    VoiceIntentParser,
    ParseResult,
    STMContext,
)
from aidm.immersion.clarification_loop import (
    ClarificationEngine,
    ClarificationRequest as VoiceClarification,
)
from aidm.schemas.immersion import Transcript
from aidm.schemas.intents import (
    DeclaredAttackIntent,
    CastSpellIntent,
    MoveIntent,
)
from aidm.schemas.intent_lifecycle import IntentObject, IntentStatus, ActionType, IntentFrozenError
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.schemas.entity_fields import EF

from datetime import datetime

from tests.spec.helpers.intent_bridge_harness import (
    run_pipeline,
    normalize_pipeline_result,
    build_world_state,
    PipelineResult,
)


# ======================================================================
# FIXTURE LOADING
# ======================================================================

FIXTURES_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "intent_bridge_cases.yaml"
)


def load_fixtures():
    """Load test case fixtures from YAML."""
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_fixtures_by_category(category):
    """Get fixtures filtered by category."""
    return [c for c in load_fixtures() if c.get("category") == category]


# ======================================================================
# 1. DETERMINISM TESTS
# Same inputs must produce identical outputs across multiple runs
# ======================================================================


class TestDeterminism:
    """Same transcript + world state → same pipeline output, every time."""

    def _run_determinism_check(self, fixture, runs=10):
        """Run fixture through pipeline N times and assert identical results."""
        stm = STMContext()
        if "stm_context" in fixture:
            stm_data = fixture["stm_context"]
            stm.last_target = stm_data.get("last_target")
            stm.last_action = stm_data.get("last_action")
            stm.last_weapon = stm_data.get("last_weapon")
            stm.last_spell = stm_data.get("last_spell")

        results = []
        for _ in range(runs):
            result = run_pipeline(
                transcript_text=fixture["transcript"],
                entities=fixture["entities"],
                stm_context=stm,
                confidence=fixture.get("confidence", 1.0),
            )
            normalized = normalize_pipeline_result(result)
            results.append(json.dumps(normalized, sort_keys=True))

        # All runs must produce identical normalized output
        first = results[0]
        for i, r in enumerate(results[1:], 1):
            assert r == first, (
                f"Determinism failure on run {i+1}/{runs} for fixture '{fixture['id']}'.\n"
                f"Run 1: {first}\n"
                f"Run {i+1}: {r}"
            )

    @pytest.mark.parametrize(
        "fixture",
        load_fixtures(),
        ids=lambda f: f["id"],
    )
    def test_determinism_10x(self, fixture):
        """Each fixture case produces identical output across 10 runs."""
        self._run_determinism_check(fixture, runs=10)


# ======================================================================
# 2. CANDIDATE ORDERING TESTS
# Disambiguation candidates must be sorted lexicographically
# ======================================================================


class TestCandidateOrdering:
    """ClarificationRequest candidates must be sorted for determinism.

    Contract §2.3: Lexicographic sort on display_name (case-insensitive).
    Tie-break: entity_id lexicographic order.
    """

    def test_bridge_candidates_sorted_lexicographically(self):
        """When bridge returns ambiguous targets, candidates are sorted."""
        entities = {
            "pc_rogue": {"team": "party", "hp_current": 20},
            "zombie_berserker": {"team": "enemy", "hp_current": 10, "entity_id": "zombie_berserker"},
            "zombie_archer": {"team": "enemy", "hp_current": 8, "entity_id": "zombie_archer"},
            "zombie_priest": {"team": "enemy", "hp_current": 7, "entity_id": "zombie_priest"},
        }

        result = run_pipeline("I attack the zombie", entities)

        if result.bridge_clarification is not None:
            candidates = list(result.bridge_clarification.candidates)
            # Verify candidates are sorted
            sorted_candidates = sorted(candidates, key=lambda c: c.lower())
            assert candidates == sorted_candidates, (
                f"Candidates not sorted lexicographically.\n"
                f"Got: {candidates}\n"
                f"Expected: {sorted_candidates}"
            )

    def test_voice_clarification_options_sorted(self):
        """When voice layer provides options, they are sorted."""
        entities = {
            "pc_rogue": {"team": "party", "hp_current": 20},
            "goblin_c": {"team": "enemy", "hp_current": 6, "entity_id": "goblin_c"},
            "goblin_a": {"team": "enemy", "hp_current": 6, "entity_id": "goblin_a"},
            "goblin_b": {"team": "enemy", "hp_current": 6, "entity_id": "goblin_b"},
        }

        result = run_pipeline("I attack the goblin", entities)

        if result.voice_clarification is not None:
            options = result.voice_clarification.suggested_options
            if len(options) > 1:
                sorted_options = sorted(options, key=lambda o: o.lower())
                assert options == sorted_options, (
                    f"Voice options not sorted lexicographically.\n"
                    f"Got: {options}\n"
                    f"Expected: {sorted_options}"
                )


# ======================================================================
# 3. NO-COACHING TESTS
# Clarification prompts must never reveal mechanical information
# ======================================================================


# Regex patterns that indicate coaching violations
# These patterns should NEVER appear in clarification text
COACHING_VIOLATION_PATTERNS = [
    # Mechanical state disclosure
    (r"\b\d+\s*(?:hit points?|hp|HP)\b", "reveals HP"),
    (r"\bAC\s*(?:of\s*)?\d+", "reveals AC value"),
    (r"\b(?:attack bonus|modifier)\s*[+-]?\d+", "reveals attack modifier"),
    (r"\bDC\s*\d+", "reveals DC value"),
    (r"\bspell resistance\b", "reveals spell resistance"),
    (r"\bdamage reduction\b", "reveals damage reduction"),
    # Tactical coaching
    (r"\byou (?:should|might want to|could)\b", "tactical suggestion"),
    (r"\bthat (?:would|will) provoke\b", "consequence warning"),
    (r"\battack of opportunity\b", "AoO warning"),
    (r"\byou(?:'re| are) flanking\b", "reveals flanking state"),
    (r"\b(?:regenerat(?:ion|es?)|fast healing)\b", "reveals monster trait"),
    (r"\b(?:high|low)\s+AC\b", "reveals AC assessment"),
    (r"\b(?:vulnerable|resistant|immune)\s+to\b", "reveals vulnerability/resistance"),
    (r"\b(?:very )?dangerous\b", "tactical assessment"),
    (r"\bbad idea\b", "value judgment"),
    (r"\bkeep in mind\b", "pre-emptive coaching"),
    # System language (should be DM persona)
    (r"\bwarning:\b", "system framing"),
    (r"\berror:\b", "system framing"),
    (r"\binvalid\b", "system language"),
]


class TestNoCoaching:
    """Clarification prompts must not reveal mechanics or provide coaching.

    Contract §3.1: The No-Coaching Constraint (BINDING).
    Manifesto: "No mercy, no hand-holding."
    AD-006: No-Opaque-DM doctrine.
    """

    def _check_text_for_coaching(self, text: str, context: str) -> list:
        """Check text against all coaching violation patterns.

        Returns list of (pattern_desc, matched_text) tuples.
        """
        violations = []
        for pattern, description in COACHING_VIOLATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                violations.append((description, match.group(), context))
        return violations

    @pytest.mark.parametrize(
        "fixture",
        load_fixtures(),
        ids=lambda f: f["id"],
    )
    def test_no_coaching_in_clarification(self, fixture):
        """No clarification prompt contains coaching violations."""
        stm = STMContext()
        if "stm_context" in fixture:
            stm_data = fixture["stm_context"]
            stm.last_target = stm_data.get("last_target")
            stm.last_action = stm_data.get("last_action")
            stm.last_weapon = stm_data.get("last_weapon")

        result = run_pipeline(
            transcript_text=fixture["transcript"],
            entities=fixture["entities"],
            stm_context=stm,
            confidence=fixture.get("confidence", 1.0),
        )

        violations = []

        # Check bridge clarification
        if result.bridge_clarification is not None:
            violations.extend(
                self._check_text_for_coaching(
                    result.bridge_clarification.message,
                    f"bridge_clarification for '{fixture['id']}'"
                )
            )

        # Check voice clarification
        if result.voice_clarification is not None:
            violations.extend(
                self._check_text_for_coaching(
                    result.voice_clarification.prompt,
                    f"voice_clarification for '{fixture['id']}'"
                )
            )
            # Also check each suggested option
            for opt in result.voice_clarification.suggested_options:
                violations.extend(
                    self._check_text_for_coaching(
                        opt,
                        f"voice_option '{opt}' for '{fixture['id']}'"
                    )
                )

        assert violations == [], (
            f"Coaching violations found in '{fixture['id']}':\n"
            + "\n".join(
                f"  - {desc}: matched '{matched}' in {ctx}"
                for desc, matched, ctx in violations
            )
        )

    def test_clarification_engine_methods_no_coaching(self):
        """Direct ClarificationEngine method outputs contain no coaching."""
        engine = ClarificationEngine()

        # Test attack clarification with ambiguous target
        parse = ParseResult(
            intent=DeclaredAttackIntent(target_ref="goblin"),
            confidence=0.9,
            ambiguous_target=True,
        )
        clarification = engine.generate_clarification(parse)
        violations = self._check_text_for_coaching(
            clarification.prompt, "generate_clarification(ambiguous_target)"
        )
        assert violations == [], f"Coaching in target clarification: {violations}"

    def test_soft_confirmation_no_coaching(self):
        """Soft confirmation echoes intent without tactical commentary."""
        engine = ClarificationEngine()

        intents = [
            DeclaredAttackIntent(target_ref="goblin", weapon="longsword"),
            CastSpellIntent(spell_name="magic missile", target_mode="creature"),
            MoveIntent(),
        ]

        for intent in intents:
            text = engine.generate_soft_confirmation(intent)
            violations = self._check_text_for_coaching(
                text, f"soft_confirmation({type(intent).__name__})"
            )
            assert violations == [], (
                f"Coaching in soft confirmation for {type(intent).__name__}: {violations}"
            )


# ======================================================================
# 4. AUTHORITY BOUNDARY TESTS
# Bridge must not compute mechanics or mutate state
# ======================================================================


class TestAuthorityBoundary:
    """Bridge operates only on name resolution and slot filling.

    Contract §8: Scope Exclusions — bridge must NOT compute legality,
    apply modifiers, decide outcomes, or generate narration.
    """

    def test_bridge_does_not_import_rng(self):
        """IntentBridge module must not import RNG (determinism risk)."""
        import aidm.interaction.intent_bridge as bridge_module
        source = open(bridge_module.__file__, "r", encoding="utf-8").read()
        assert "rng_manager" not in source.lower(), (
            "intent_bridge.py imports RNG-related module — authority violation"
        )
        assert "import random" not in source, (
            "intent_bridge.py imports stdlib random — authority violation"
        )

    def test_bridge_does_not_import_resolvers(self):
        """IntentBridge must not import combat resolvers (Box authority)."""
        import aidm.interaction.intent_bridge as bridge_module
        source = open(bridge_module.__file__, "r", encoding="utf-8").read()
        forbidden_imports = [
            "attack_resolver",
            "full_attack_resolver",
            "damage_reduction",
            "sneak_attack",
            "flanking",
            "concealment",
            "grapple",
        ]
        for forbidden in forbidden_imports:
            assert forbidden not in source, (
                f"intent_bridge.py imports '{forbidden}' — Box authority violation"
            )

    def test_bridge_uses_frozen_view(self):
        """IntentBridge resolve methods accept FrozenWorldStateView, not WorldState."""
        import inspect
        bridge = IntentBridge()

        for method_name in ["resolve_attack", "resolve_spell", "resolve_move"]:
            method = getattr(bridge, method_name)
            sig = inspect.signature(method)
            param_names = list(sig.parameters.keys())
            # Should have 'view' parameter, not 'world_state'
            assert "world_state" not in param_names, (
                f"{method_name} accepts 'world_state' instead of 'view' — "
                f"should use FrozenWorldStateView for BL-020 enforcement"
            )

    def test_bridge_does_not_mutate_world_state(self):
        """Running bridge resolve does not mutate the world state."""
        entities = {
            "pc_rogue": {"team": "party", "hp_current": 20},
            "goblin_1": {"team": "enemy", "hp_current": 6, "ac": 15, "entity_id": "goblin_1"},
        }
        world_state = build_world_state(entities)
        original_entities = json.dumps(
            {k: dict(v) for k, v in world_state.entities.items()}, sort_keys=True
        )

        view = FrozenWorldStateView(world_state)
        bridge = IntentBridge()
        bridge.resolve_attack(
            actor_id="pc_rogue",
            declared=DeclaredAttackIntent(target_ref="goblin"),
            view=view,
        )

        after_entities = json.dumps(
            {k: dict(v) for k, v in world_state.entities.items()}, sort_keys=True
        )
        assert original_entities == after_entities, (
            "Bridge resolution mutated world state — BL-020 violation"
        )


# ======================================================================
# 5. LIFECYCLE IMMUTABILITY TESTS
# CONFIRMED intents must be frozen (BL-014)
# ======================================================================


class TestLifecycleImmutability:
    """IntentObject freeze boundary enforcement.

    Contract §7B: After transition to CONFIRMED, only resolution
    fields may be written (status, result_id, resolved_at, updated_at).
    """

    def _make_intent_object(self, **kwargs):
        """Create an IntentObject with required fields populated."""
        now = datetime.now()
        defaults = {
            "intent_id": "test-001",
            "actor_id": "pc_rogue",
            "action_type": ActionType.ATTACK,
            "status": IntentStatus.PENDING,
            "source_text": "I attack the goblin",
            "created_at": now,
            "updated_at": now,
        }
        defaults.update(kwargs)
        return IntentObject(**defaults)

    def test_confirmed_intent_is_frozen(self):
        """IntentObject in CONFIRMED status rejects field writes."""
        now = datetime.now()
        intent_obj = self._make_intent_object(
            intent_id="test-001",
            target_id="goblin_1",
            method="longsword",
        )

        # Transition to CONFIRMED
        intent_obj.transition_to(IntentStatus.CONFIRMED, now)

        # Attempt to modify a frozen field
        with pytest.raises((IntentFrozenError, AttributeError)):
            intent_obj.target_id = "different_target"

    def test_confirmed_intent_allows_resolution(self):
        """CONFIRMED intent allows status transition to RESOLVED."""
        now = datetime.now()
        intent_obj = self._make_intent_object(
            intent_id="test-002",
            target_id="goblin_1",
            method="longsword",
        )

        intent_obj.transition_to(IntentStatus.CONFIRMED, now)
        intent_obj.transition_to(IntentStatus.RESOLVED, now)
        assert intent_obj.status == IntentStatus.RESOLVED

    def test_valid_transitions_only(self):
        """Only valid status transitions are permitted."""
        now = datetime.now()
        intent_obj = self._make_intent_object(
            intent_id="test-003",
        )

        # PENDING → CONFIRMED is valid
        intent_obj.transition_to(IntentStatus.CONFIRMED, now)

        # CONFIRMED → PENDING is NOT valid
        with pytest.raises(Exception):
            intent_obj.transition_to(IntentStatus.PENDING, now)

    def test_retracted_is_terminal(self):
        """RETRACTED status is terminal — no further transitions."""
        now = datetime.now()
        intent_obj = self._make_intent_object(
            intent_id="test-004",
        )

        intent_obj.transition_to(IntentStatus.RETRACTED, now)

        with pytest.raises(Exception):
            intent_obj.transition_to(IntentStatus.CONFIRMED, now)


# ======================================================================
# 6. CONTENT INDEPENDENCE TESTS
# Pipeline must not contain source-material-specific vocabulary
# ======================================================================


class TestContentIndependence:
    """Pipeline phrasing and behavior must be content-independent.

    Per Manifesto: D&D is scaffolding, not the product. The Intent Bridge
    resolves player speech to structured actions — it should not contain
    game-system-specific vocabulary in its clarification prompts.
    """

    # Patterns that indicate source-material coupling in clarification text
    SOURCE_MATERIAL_PATTERNS = [
        (r"\bD&D\b", "D&D brand reference"),
        (r"\bDungeons\s*&?\s*Dragons\b", "D&D brand reference"),
        (r"\b3\.5(?:e|E)?\b", "edition reference"),
        (r"\bPHB\b", "sourcebook reference"),
        (r"\bDMG\b", "sourcebook reference"),
        (r"\bMonster Manual\b", "sourcebook reference"),
    ]

    @pytest.mark.parametrize(
        "fixture",
        load_fixtures(),
        ids=lambda f: f["id"],
    )
    def test_no_source_material_in_clarification(self, fixture):
        """Clarification prompts contain no source material references."""
        stm = STMContext()
        if "stm_context" in fixture:
            stm_data = fixture["stm_context"]
            stm.last_target = stm_data.get("last_target")
            stm.last_action = stm_data.get("last_action")
            stm.last_weapon = stm_data.get("last_weapon")

        result = run_pipeline(
            transcript_text=fixture["transcript"],
            entities=fixture["entities"],
            stm_context=stm,
            confidence=fixture.get("confidence", 1.0),
        )

        all_text = []
        if result.bridge_clarification is not None:
            all_text.append(result.bridge_clarification.message)
        if result.voice_clarification is not None:
            all_text.append(result.voice_clarification.prompt)
            all_text.extend(result.voice_clarification.suggested_options)

        violations = []
        for text in all_text:
            for pattern, description in self.SOURCE_MATERIAL_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    violations.append((description, match.group(), text))

        assert violations == [], (
            f"Source material references in '{fixture['id']}':\n"
            + "\n".join(
                f"  - {desc}: '{matched}' in '{ctx}'"
                for desc, matched, ctx in violations
            )
        )
