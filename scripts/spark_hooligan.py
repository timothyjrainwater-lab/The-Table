"""Hooligan Run — Cinder Voss Style Chaos Testing

Hard capture frame per Aegis directive:
- One scenario per run
- Save exact inputs, model settings, raw output
- Record which validator fired
- Record whether fallback triggered
- Record any meta output or section header leakage
- Write finding as claim/evidence/implication
- Then move on

Three axes after hooligan scenarios:
- Axis 1: Determinism abuse (same scenario 10x with seed)
- Axis 2: Validator fuzzing (inject violations into real output)
- Axis 3: Contract ambiguity (hard-but-legal inputs)

Seven Wisdom energy is undefeated.
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aidm.spark.model_registry import ModelRegistry
from aidm.spark.llamacpp_adapter import LlamaCppAdapter
from aidm.spark.spark_adapter import SparkRequest
from aidm.narration.narration_validator import NarrationValidator


# ─── Capture Frame ──────────────────────────────────────────────────────────

@dataclass
class CaptureFrame:
    """Hard capture frame for one scenario run. Everything gets recorded."""
    scenario_id: str
    scenario_name: str
    timestamp: str = ""
    # Inputs
    prompt: str = ""
    max_tokens: int = 150
    temperature: float = 0.8
    stop_sequences: List[str] = field(default_factory=list)
    seed: Optional[int] = None
    # Model settings
    model_id: str = ""
    device: str = ""
    vram_before_mb: float = 0.0
    vram_after_mb: float = 0.0
    # Raw output
    raw_output: str = ""
    completion_tokens: int = 0
    prompt_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""
    gen_time_s: float = 0.0
    error: Optional[str] = None
    # Validator
    validator_verdict: str = ""
    validator_violations: List[Dict] = field(default_factory=list)
    # Meta leakage detection
    contains_separator: bool = False
    contains_meta_comment: bool = False
    contains_dice_rolls: bool = False
    contains_hp_values: bool = False
    contains_damage_numbers: bool = False
    section_header_leakage: List[str] = field(default_factory=list)
    # Fallback
    fallback_triggered: bool = False
    # Finding (claim/evidence/implication)
    finding: Optional[Dict] = None

    def to_dict(self):
        return asdict(self)


def get_vram_mb():
    """NVML-based VRAM reporting."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        used_mb = mem_info.used / (1024 * 1024)
        pynvml.nvmlShutdown()
        return used_mb
    except (ImportError, Exception):
        pass
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated(0) / (1024 * 1024)
    except ImportError:
        pass
    return 0.0


def detect_meta_leakage(text: str) -> Dict:
    """Detect meta-game leakage in generated text."""
    import re

    leakage = {
        "contains_separator": "===" in text,
        "contains_meta_comment": bool(re.search(r'\(Note:|\(note:|character count|word count', text, re.IGNORECASE)),
        "contains_dice_rolls": bool(re.search(r'\b\d+d\d+\b|rolled a \d+|saving throw DC|DC \d+', text, re.IGNORECASE)),
        "contains_hp_values": bool(re.search(r'\b\d+\s*(?:HP|hp|hit points|health)\b', text, re.IGNORECASE)),
        "contains_damage_numbers": bool(re.search(r'\b\d+\s*(?:damage|points of damage|points? of \w+ damage)\b', text, re.IGNORECASE)),
        "section_header_leakage": re.findall(r'===\s*\w+\s*===', text),
    }
    return leakage


def build_brief(action_type, severity, target_defeated=False,
                condition_applied=None, condition_removed=None,
                save_result=None):
    """Build a MiniBrief for the validator."""
    class MiniBrief:
        pass
    brief = MiniBrief()
    brief.action_type = action_type
    brief.target_defeated = target_defeated
    brief.severity = severity
    brief.condition_applied = condition_applied
    brief.condition_removed = condition_removed
    brief.content_id = None
    brief.save_result = save_result
    return brief


def run_captured(adapter, loaded_model, scenario_id, scenario_name,
                 prompt, brief, validator, max_tokens=150, temperature=0.8,
                 stop_sequences=None, seed=None):
    """Run a single scenario with full capture frame."""
    if stop_sequences is None:
        stop_sequences = ["</narration>", "\n\n", "==="]

    frame = CaptureFrame(
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stop_sequences=stop_sequences,
        seed=seed,
        model_id=loaded_model.model_id,
        device=loaded_model.device,
    )

    request = SparkRequest(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stop_sequences=stop_sequences,
        seed=seed,
    )

    frame.vram_before_mb = round(get_vram_mb(), 1)
    t_start = time.perf_counter()
    response = adapter.generate(request, loaded_model)
    t_end = time.perf_counter()
    frame.vram_after_mb = round(get_vram_mb(), 1)

    frame.raw_output = response.text or ""
    frame.finish_reason = str(response.finish_reason)
    frame.gen_time_s = round(t_end - t_start, 3)
    frame.total_tokens = response.tokens_used
    frame.error = response.error

    if response.provider_metadata:
        frame.completion_tokens = response.provider_metadata.get("completion_tokens", 0)
        frame.prompt_tokens = response.provider_metadata.get("prompt_tokens", 0)

    # Meta leakage detection
    leakage = detect_meta_leakage(frame.raw_output)
    frame.contains_separator = leakage["contains_separator"]
    frame.contains_meta_comment = leakage["contains_meta_comment"]
    frame.contains_dice_rolls = leakage["contains_dice_rolls"]
    frame.contains_hp_values = leakage["contains_hp_values"]
    frame.contains_damage_numbers = leakage["contains_damage_numbers"]
    frame.section_header_leakage = leakage["section_header_leakage"]

    # Validator
    if not response.error and frame.raw_output:
        vresult = validator.validate(frame.raw_output, brief)
        frame.validator_verdict = vresult.verdict
        frame.validator_violations = [
            {"rule_id": v.rule_id, "severity": v.severity, "detail": v.detail}
            for v in vresult.violations
        ]

    # Print summary
    print(f"\n  [{scenario_id}] {scenario_name}")
    print(f"  Output: {frame.raw_output[:120]}{'...' if len(frame.raw_output) > 120 else ''}")
    print(f"  Tokens: {frame.completion_tokens} completion, {frame.gen_time_s}s")
    print(f"  Validator: {frame.validator_verdict}")
    print(f"  VRAM: {frame.vram_before_mb:.0f} -> {frame.vram_after_mb:.0f} MB")
    if frame.contains_separator or frame.contains_meta_comment:
        print(f"  !! META LEAKAGE: separator={frame.contains_separator}, meta={frame.contains_meta_comment}")
    if frame.contains_dice_rolls or frame.contains_hp_values or frame.contains_damage_numbers:
        print(f"  !! FORBIDDEN CLAIMS: dice={frame.contains_dice_rolls}, hp={frame.contains_hp_values}, dmg={frame.contains_damage_numbers}")
    for v in frame.validator_violations:
        print(f"  [{v['severity']}] {v['rule_id']}: {v['detail']}")

    return frame


# ─── Hooligan Scenarios (Cinder's List) ─────────────────────────────────────

SCENARIOS = {
    # === Original 3 from shakeout ===
    "H-01": {
        "name": "Melee Hit (baseline)",
        "prompt": """=== TRUTH ===
Action: attack_hit
Actor: Kael
Target: Goblin Scout
Outcome: Kael strikes the goblin with his longsword
Severity: moderate
Weapon: Longsword
Damage Type: slashing

=== MEMORY ===
Previous: The party formed a defensive line.
Scene: Underground cavern with torchlight

=== TASK ===
Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent damage numbers, HP values, AC, or dice rolls. Do NOT add new NPCs or locations not mentioned above.

=== STYLE ===
Voice: Confident dungeon master
Tone: Dramatic but concise
Pacing: Each sentence is a distinct beat

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section
Forbidden: Damage numbers, HP values, dice results, meta-game terms

Narration:""",
        "brief": lambda: build_brief("attack_hit", "moderate"),
    },

    # === Cinder's chaos scenarios ===
    "H-02": {
        "name": "Miss (no damage, just whiff)",
        "prompt": """=== TRUTH ===
Action: attack_miss
Actor: Grunk
Target: Skeleton Warrior
Outcome: Grunk's battleaxe misses the skeleton
Severity: none
Weapon: Battleaxe
Damage Type: slashing

=== MEMORY ===
Previous: Grunk charged forward with a war cry.
Scene: Crumbling crypt, bones scattered on the floor

=== TASK ===
Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent damage numbers, HP values, AC, or dice rolls. Do NOT add new NPCs or locations not mentioned above.

=== STYLE ===
Voice: Confident dungeon master
Tone: Comedic frustration
Pacing: Build up then deflate

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section
Forbidden: Damage numbers, HP values, dice results, meta-game terms, AC values

Narration:""",
        "brief": lambda: build_brief("attack_miss", "none"),
    },

    "H-03": {
        "name": "Kill shot (target defeated)",
        "prompt": """=== TRUTH ===
Action: attack_hit
Actor: Vex
Target: Dire Wolf Alpha
Outcome: Vex's arrow strikes the dire wolf in the throat, killing it
Severity: devastating
Weapon: Longbow
Damage Type: piercing

=== MEMORY ===
Previous: The dire wolf was already bleeding from multiple wounds.
Scene: Snowy mountain pass, howling wind

=== TASK ===
Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent damage numbers, HP values, AC, or dice rolls. Do NOT add new NPCs or locations not mentioned above.

=== STYLE ===
Voice: Confident dungeon master
Tone: Grim satisfaction
Pacing: Slow motion arrow, then collapse

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section, describe the kill
Forbidden: Damage numbers, HP values, dice results, meta-game terms

Narration:""",
        "brief": lambda: build_brief("attack_hit", "devastating", target_defeated=True),
    },

    "H-04": {
        "name": "Healing spell (no combat)",
        "prompt": """=== TRUTH ===
Action: healing
Actor: Brother Aldric
Target: Kael
Outcome: Brother Aldric's Cure Wounds restores Kael
Severity: moderate
Spell: Cure Wounds

=== MEMORY ===
Previous: Kael collapsed against the wall, bleeding.
Scene: After the battle, dusty corridor

=== TASK ===
Write a narration for a tabletop RPG. Describe the healing in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent HP restored, spell levels, or dice rolls.

=== STYLE ===
Voice: Confident dungeon master
Tone: Relief and warmth
Pacing: Gentle but purposeful

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section
Forbidden: HP values, spell levels, dice results, meta-game terms

Narration:""",
        "brief": lambda: build_brief("healing", "moderate"),
    },

    "H-05": {
        "name": "Condition removal (curse lifted)",
        "prompt": """=== TRUTH ===
Action: condition_removed
Actor: Seraphine
Target: Grunk
Outcome: Seraphine's Remove Curse lifts the mummy rot from Grunk
Severity: moderate
Spell: Remove Curse
Condition Removed: mummy_rot

=== MEMORY ===
Previous: Grunk's skin had been turning grey for two days.
Scene: Temple of Pelor, candlelight

=== TASK ===
Write a narration for a tabletop RPG. Describe the curse removal in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent spell levels, DC values, or dice rolls.

=== STYLE ===
Voice: Confident dungeon master
Tone: Sacred, cleansing
Pacing: Tension then release

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section, mention the curse lifting
Forbidden: Spell levels, DC values, dice results, meta-game terms

Narration:""",
        "brief": lambda: build_brief("condition_removed", "moderate", condition_removed="mummy_rot"),
    },

    "H-06": {
        "name": "Critical hit (extreme severity)",
        "prompt": """=== TRUTH ===
Action: attack_hit
Actor: Kael
Target: Orc Warchief
Outcome: Kael lands a devastating critical strike with his longsword
Severity: critical
Weapon: Longsword
Damage Type: slashing

=== MEMORY ===
Previous: The orc warchief laughed and beckoned Kael forward.
Scene: Muddy battlefield, rain pouring

=== TASK ===
Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent damage numbers, HP values, AC, or dice rolls. Do NOT mention "critical hit" as a game term.

=== STYLE ===
Voice: Confident dungeon master
Tone: Explosive, visceral
Pacing: One brutal moment

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section
Forbidden: Damage numbers, HP values, dice results, the phrase "critical hit", AC values

Narration:""",
        "brief": lambda: build_brief("attack_hit", "critical"),
    },

    "H-07": {
        "name": "Save success (spell fizzles)",
        "prompt": """=== TRUTH ===
Action: spell_no_effect
Actor: Seraphine
Target: Iron Golem
Outcome: Seraphine's Hold Monster fails against the iron golem
Severity: none
Spell: Hold Monster
Save Result: Target succeeded Will save

=== MEMORY ===
Previous: The golem stomped toward the party, shaking the ground.
Scene: Dwarven forge, magma pools nearby

=== TASK ===
Write a combat narration for a tabletop RPG. Describe the failed spell in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent save DCs, spell levels, or dice rolls.

=== STYLE ===
Voice: Confident dungeon master
Tone: Dread — the spell didn't work
Pacing: Hope then crushing realization

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section
Forbidden: Save DCs, spell levels, dice results, meta-game terms

Narration:""",
        "brief": lambda: build_brief("spell_no_effect", "none", save_result="success"),
    },

    "H-08": {
        "name": "Empty MEMORY section (no prior context)",
        "prompt": """=== TRUTH ===
Action: attack_hit
Actor: Kael
Target: Goblin Scout
Outcome: Kael strikes the goblin with his longsword
Severity: moderate
Weapon: Longsword
Damage Type: slashing

=== MEMORY ===
Previous: None
Scene: Unknown

=== TASK ===
Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent damage numbers, HP values, AC, or dice rolls. Do NOT add new NPCs or locations not mentioned above.

=== STYLE ===
Voice: Confident dungeon master
Tone: Dramatic but concise
Pacing: Each sentence is a distinct beat

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section
Forbidden: Damage numbers, HP values, dice results, meta-game terms

Narration:""",
        "brief": lambda: build_brief("attack_hit", "moderate"),
    },
}


# ─── Axis 1: Determinism Abuse ──────────────────────────────────────────────

def run_determinism_test(adapter, loaded_model, validator, n_runs=10):
    """Run same scenario N times with same seed. Flag any drift."""
    print(f"\n{'='*70}")
    print(f"  AXIS 1: DETERMINISM ABUSE ({n_runs} runs, seed=42)")
    print(f"{'='*70}")

    prompt = SCENARIOS["H-01"]["prompt"]
    brief = SCENARIOS["H-01"]["brief"]()
    frames = []

    for i in range(n_runs):
        frame = run_captured(
            adapter, loaded_model,
            scenario_id=f"DET-{i+1:02d}",
            scenario_name=f"Determinism run {i+1}/{n_runs}",
            prompt=prompt,
            brief=brief,
            validator=validator,
            seed=42,
            temperature=0.0,  # Greedy decoding for max determinism
        )
        frames.append(frame)

    # Check for drift
    outputs = [f.raw_output for f in frames]
    unique_outputs = set(outputs)
    drift_detected = len(unique_outputs) > 1

    print(f"\n  Unique outputs: {len(unique_outputs)}/{n_runs}")
    if drift_detected:
        print(f"  !! DRIFT DETECTED")
        for i, output in enumerate(unique_outputs):
            count = outputs.count(output)
            print(f"    Variant {i+1} ({count}x): {output[:80]}...")
    else:
        print(f"  All {n_runs} outputs identical. Deterministic.")

    return {
        "test": "DETERMINISM_ABUSE",
        "n_runs": n_runs,
        "seed": 42,
        "temperature": 0.0,
        "unique_outputs": len(unique_outputs),
        "drift_detected": drift_detected,
        "frames": [f.to_dict() for f in frames],
    }


# ─── Axis 2: Validator Fuzzing ──────────────────────────────────────────────

def run_validator_fuzzing(validator):
    """Take real output and inject violations. Validator must catch them."""
    print(f"\n{'='*70}")
    print(f"  AXIS 2: VALIDATOR FUZZING")
    print(f"{'='*70}")

    # Clean baseline output (from shakeout Scenario A)
    clean = "Kael's longsword glows with a blue light as he lunges at the goblin scout, slicing through its armor with a resounding crack."

    mutations = [
        {
            "id": "FUZZ-01",
            "name": "Inject damage number",
            "text": "Kael's longsword deals 14 damage as he lunges at the goblin scout, slicing through its armor with a resounding crack.",
            "expected_rule": "RV-007",  # forbidden claim: damage number
            "brief": build_brief("attack_hit", "moderate"),
        },
        {
            "id": "FUZZ-02",
            "name": "Inject HP value",
            "text": "Kael's longsword strikes the goblin scout (42 HP remaining), slicing through its armor with a resounding crack.",
            "expected_rule": "RV-007",
            "brief": build_brief("attack_hit", "moderate"),
        },
        {
            "id": "FUZZ-03",
            "name": "Inject dice roll",
            "text": "Kael rolled a 19 on his attack and his longsword slices through the goblin scout's armor with a resounding crack.",
            "expected_rule": "RV-007",
            "brief": build_brief("attack_hit", "moderate"),
        },
        {
            "id": "FUZZ-04",
            "name": "Narrate miss when brief says hit",
            "text": "Kael's longsword swings wide, missing the goblin scout entirely as it dodges to the side.",
            "expected_rule": "RV-001",  # hit/miss contradiction
            "brief": build_brief("attack_hit", "moderate"),
        },
        {
            "id": "FUZZ-05",
            "name": "Narrate defeat when target not defeated",
            "text": "Kael's longsword cleaves through the goblin scout, killing it instantly. The goblin collapses in a lifeless heap.",
            "expected_rule": "RV-002",  # defeat contradiction
            "brief": build_brief("attack_hit", "moderate", target_defeated=False),
        },
        {
            "id": "FUZZ-06",
            "name": "Missing condition mention when required",
            "text": "Seraphine's spell strikes the bandit captain with magical force, sending him staggering backward.",
            "expected_rule": "RV-004",  # condition not mentioned
            "brief": build_brief("spell_damage_dealt", "severe", condition_applied="paralyzed"),
        },
        {
            "id": "FUZZ-07",
            "name": "Inject save DC",
            "text": "Seraphine's Hold Person (DC 15) seizes the bandit captain, paralyzing him in place.",
            "expected_rule": "RV-007",
            "brief": build_brief("spell_damage_dealt", "severe", condition_applied="paralyzed", save_result="fail"),
        },
        {
            "id": "FUZZ-08",
            "name": "Clean output (should PASS)",
            "text": clean,
            "expected_rule": None,  # should pass
            "brief": build_brief("attack_hit", "moderate"),
        },
    ]

    results = []
    for m in mutations:
        vresult = validator.validate(m["text"], m["brief"])
        caught = False
        matched_rule = None

        if m["expected_rule"] is None:
            # Should pass
            caught = vresult.verdict == "PASS"
        else:
            # Should catch
            for v in vresult.violations:
                if v.rule_id == m["expected_rule"]:
                    caught = True
                    matched_rule = v.rule_id
                    break
            # Also check if ANY violation was raised (partial credit)
            if not caught and vresult.violations:
                caught = True
                matched_rule = vresult.violations[0].rule_id

        status = "CAUGHT" if caught else "MISSED"
        print(f"  [{m['id']}] {m['name']}: {status} (verdict={vresult.verdict}, expected={m['expected_rule']}, got={matched_rule})")

        results.append({
            "mutation_id": m["id"],
            "mutation_name": m["name"],
            "mutated_text": m["text"],
            "expected_rule": m["expected_rule"],
            "actual_verdict": vresult.verdict,
            "violations": [{"rule_id": v.rule_id, "severity": v.severity, "detail": v.detail} for v in vresult.violations],
            "caught": caught,
            "matched_rule": matched_rule,
        })

    caught_count = sum(1 for r in results if r["caught"])
    total = len(results)
    print(f"\n  Score: {caught_count}/{total}")
    missed = [r for r in results if not r["caught"]]
    if missed:
        print(f"  !! PRIORITY GAPS:")
        for m in missed:
            print(f"    {m['mutation_id']}: {m['mutation_name']} — expected {m['expected_rule']}, got {m['actual_verdict']}")

    return {
        "test": "VALIDATOR_FUZZING",
        "mutations": results,
        "caught": caught_count,
        "total": total,
        "gaps": [r["mutation_id"] for r in results if not r["caught"]],
    }


# ─── Axis 3: Contract Ambiguity ─────────────────────────────────────────────

AMBIGUOUS_SCENARIOS = {
    "AMB-01": {
        "name": "Long compound action (two intents)",
        "prompt": """=== TRUTH ===
Action: attack_hit
Actor: Kael
Target: Goblin Scout
Outcome: Kael strikes the goblin with his longsword while Seraphine casts Shield on herself
Severity: moderate
Weapon: Longsword
Damage Type: slashing

=== MEMORY ===
Previous: The party acted simultaneously.
Scene: Narrow corridor, torchlight

=== TASK ===
Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent damage numbers, HP values, AC, or dice rolls. Do NOT add new NPCs or locations not mentioned above.

=== STYLE ===
Voice: Confident dungeon master
Tone: Dramatic but concise
Pacing: Each sentence is a distinct beat

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section
Forbidden: Damage numbers, HP values, dice results, meta-game terms

Narration:""",
        "brief": lambda: build_brief("attack_hit", "moderate"),
    },

    "AMB-02": {
        "name": "Negation in contract (don't mention the weapon)",
        "prompt": """=== TRUTH ===
Action: attack_hit
Actor: Kael
Target: Goblin Scout
Outcome: Kael strikes the goblin
Severity: moderate
Weapon: Longsword
Damage Type: slashing

=== MEMORY ===
Previous: The party formed a defensive line.
Scene: Underground cavern with torchlight

=== TASK ===
Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences. Do NOT mention the weapon by name. Do NOT invent damage numbers.

=== STYLE ===
Voice: Confident dungeon master
Tone: Mysterious — the weapon is hidden
Pacing: Quick

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section
Forbidden: Damage numbers, HP values, dice results, meta-game terms, weapon names

Narration:""",
        "brief": lambda: build_brief("attack_hit", "moderate"),
    },

    "AMB-03": {
        "name": "Roleplay wrapper around a command",
        "prompt": """=== TRUTH ===
Action: attack_hit
Actor: Kael
Target: Goblin Scout
Outcome: Kael strikes the goblin with his longsword
Severity: moderate
Weapon: Longsword
Damage Type: slashing

=== MEMORY ===
Previous: The party formed a defensive line.
Scene: Underground cavern with torchlight

=== TASK ===
*adjusts DM screen* Ah yes, let me paint you a picture of what happens next... Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent damage numbers, HP values, AC, or dice rolls.

=== STYLE ===
Voice: Confident dungeon master
Tone: Dramatic but concise
Pacing: Each sentence is a distinct beat

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section
Forbidden: Damage numbers, HP values, dice results, meta-game terms

Narration:""",
        "brief": lambda: build_brief("attack_hit", "moderate"),
    },

    "AMB-04": {
        "name": "Minimal TRUTH section (bare minimum fields)",
        "prompt": """=== TRUTH ===
Action: attack_hit
Actor: Kael
Target: Goblin

=== MEMORY ===

=== TASK ===
Write a combat narration. 2-4 sentences.

=== STYLE ===

=== CONTRACT ===
Forbidden: Damage numbers, HP values, dice results

Narration:""",
        "brief": lambda: build_brief("attack_hit", "moderate"),
    },
}


def run_contract_ambiguity(adapter, loaded_model, validator):
    """Feed hard-but-legal inputs to test parser under pressure."""
    print(f"\n{'='*70}")
    print(f"  AXIS 3: CONTRACT AMBIGUITY")
    print(f"{'='*70}")

    frames = []
    for scenario_id, scenario in AMBIGUOUS_SCENARIOS.items():
        frame = run_captured(
            adapter, loaded_model,
            scenario_id=scenario_id,
            scenario_name=scenario["name"],
            prompt=scenario["prompt"],
            brief=scenario["brief"](),
            validator=validator,
        )
        frames.append(frame)

    return {
        "test": "CONTRACT_AMBIGUITY",
        "frames": [f.to_dict() for f in frames],
    }


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  HOOLIGAN RUN — CINDER VOSS EDITION")
    print("  Pass Zero locked. Evidence capture mode.")
    print("  Seven Wisdom Zero Regrets")
    print("=" * 70)

    # Load
    print("\n[1] Loading model...")
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry, models_dir=".")
    model_id = "qwen25-7b-instruct-4bit"
    t_load = time.perf_counter()
    loaded_model = adapter.load_model(model_id)
    load_time = time.perf_counter() - t_load
    print(f"  Loaded {model_id} in {load_time:.2f}s on {loaded_model.device}")

    validator = NarrationValidator()

    all_results = {
        "run": "HOOLIGAN_RUN_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_id": model_id,
        "device": loaded_model.device,
        "load_time_s": round(load_time, 2),
    }

    # ── Hooligan Scenarios ──
    print(f"\n{'='*70}")
    print(f"  HOOLIGAN SCENARIOS ({len(SCENARIOS)} scenarios)")
    print(f"{'='*70}")

    hooligan_frames = []
    for scenario_id, scenario in SCENARIOS.items():
        frame = run_captured(
            adapter, loaded_model,
            scenario_id=scenario_id,
            scenario_name=scenario["name"],
            prompt=scenario["prompt"],
            brief=scenario["brief"](),
            validator=validator,
        )
        hooligan_frames.append(frame)

    all_results["hooligan"] = {
        "scenarios": len(hooligan_frames),
        "pass": sum(1 for f in hooligan_frames if f.validator_verdict == "PASS"),
        "fail": sum(1 for f in hooligan_frames if f.validator_verdict == "FAIL"),
        "warn": sum(1 for f in hooligan_frames if f.validator_verdict == "WARN"),
        "meta_leaks": sum(1 for f in hooligan_frames if f.contains_separator or f.contains_meta_comment),
        "forbidden_claims": sum(1 for f in hooligan_frames if f.contains_dice_rolls or f.contains_hp_values or f.contains_damage_numbers),
        "frames": [f.to_dict() for f in hooligan_frames],
    }

    # ── Axis 1: Determinism ──
    all_results["axis_1_determinism"] = run_determinism_test(adapter, loaded_model, validator)

    # ── Axis 2: Validator Fuzzing ──
    all_results["axis_2_fuzzing"] = run_validator_fuzzing(validator)

    # ── Axis 3: Contract Ambiguity ──
    all_results["axis_3_ambiguity"] = run_contract_ambiguity(adapter, loaded_model, validator)

    # ── Summary ──
    print(f"\n{'='*70}")
    print(f"  HOOLIGAN RUN SUMMARY")
    print(f"{'='*70}")

    h = all_results["hooligan"]
    print(f"\n  Hooligan Scenarios: {h['pass']} PASS / {h['warn']} WARN / {h['fail']} FAIL")
    print(f"  Meta leaks: {h['meta_leaks']}")
    print(f"  Forbidden claims: {h['forbidden_claims']}")

    d = all_results["axis_1_determinism"]
    print(f"\n  Determinism: {d['unique_outputs']} unique outputs in {d['n_runs']} runs {'(DRIFT!)' if d['drift_detected'] else '(stable)'}")

    f = all_results["axis_2_fuzzing"]
    print(f"\n  Validator Fuzzing: {f['caught']}/{f['total']} caught")
    if f["gaps"]:
        print(f"  GAPS: {', '.join(f['gaps'])}")

    # Save full artifact
    artifact_path = "pm_inbox/HOOLIGAN_RUN_001.json"
    with open(artifact_path, "w", encoding="utf-8") as fp:
        json.dump(all_results, fp, indent=2, ensure_ascii=False)
    print(f"\n  Full artifact: {artifact_path}")

    # Unload
    adapter.unload_model(loaded_model)
    print("\n  Model unloaded. Hooligan run complete.")


if __name__ == "__main__":
    main()
