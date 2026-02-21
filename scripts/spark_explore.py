"""Spark Cage Exploratory Shakeout — WO-SPARK-EXPLORE-001

Anvil's first time inside the Spark cage. Fix DLL, load Qwen2.5,
push real prompts through, run validator, report what falls out.

Seven Wisdom energy is undefeated.
"""

import os
import sys
import time

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aidm.spark.model_registry import ModelRegistry
from aidm.spark.llamacpp_adapter import LlamaCppAdapter
from aidm.spark.spark_adapter import SparkRequest
from aidm.narration.narration_validator import NarrationValidator

# ─── Scenarios ───────────────────────────────────────────────────────────

SCENARIO_A_MELEE = """=== TRUTH ===
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

Narration:"""

SCENARIO_B_SPELL = """=== TRUTH ===
Action: spell_damage_dealt
Actor: Seraphine
Target: Bandit Captain
Outcome: Seraphine's Hold Person paralyzes the bandit captain
Severity: severe
Spell: Hold Person
Save Result: Target failed Will save
Condition Applied: paralyzed

=== MEMORY ===
Previous: The bandit captain raised his blade for a killing blow.
Scene: Dusty road ambush, late afternoon

=== TASK ===
Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent damage numbers, HP values, AC, or dice rolls. Do NOT add new NPCs or locations not mentioned above.

=== STYLE ===
Voice: Confident dungeon master
Tone: Tense, the moment of magical domination
Pacing: Build tension then freeze

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section, mention paralysis
Forbidden: Save DCs, spell levels, HP values, meta-game terms

Narration:"""

SCENARIO_C_AOE = """=== TRUTH ===
Action: spell_damage_dealt
Actor: Elara
Target: Goblin Warrior
Additional Targets: Goblin Archer (severe), Goblin Scout (severe, defeated)
Outcome: Elara's fireball engulfs the goblin group
Severity: devastating
Spell: Fireball
Damage Type: fire

=== MEMORY ===
Previous: The wizard raised her staff, chanting.
Scene: Open cavern with enemies clustered near an altar

=== TASK ===
Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent damage numbers, HP values, AC, or dice rolls. Do NOT add new NPCs or locations not mentioned above.

=== STYLE ===
Voice: Confident dungeon master
Tone: Epic and visceral
Pacing: Capture the explosion then the aftermath

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section, mention all targets
Forbidden: Damage numbers, HP values, spell levels, save DCs

Narration:"""

SCENARIOS = [
    ("A: Melee Attack Hit", SCENARIO_A_MELEE),
    ("B: Spell + Save Fail + Condition", SCENARIO_B_SPELL),
    ("C: AoE Multi-Target", SCENARIO_C_AOE),
]


def get_vram_mb():
    """Get current VRAM usage in MB."""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated(0) / (1024 * 1024)
    except ImportError:
        pass
    return 0.0


def run_scenario(adapter, loaded_model, name, prompt, validator):
    """Run a single scenario through the pipeline."""
    print(f"\n{'='*70}")
    print(f"  SCENARIO {name}")
    print(f"{'='*70}")

    # Generate
    request = SparkRequest(
        prompt=prompt,
        max_tokens=150,
        temperature=0.8,
        stop_sequences=["</narration>", "\n\n"],
    )

    vram_before = get_vram_mb()
    t_start = time.perf_counter()
    response = adapter.generate(request, loaded_model)
    t_end = time.perf_counter()
    vram_after = get_vram_mb()

    gen_time = t_end - t_start

    print(f"\n--- Generated Text ---")
    print(response.text)
    print(f"\n--- Metrics ---")
    print(f"  Generation time: {gen_time:.2f}s")
    print(f"  Tokens used: {response.tokens_used}")
    print(f"  Finish reason: {response.finish_reason}")
    if response.provider_metadata:
        print(f"  Prompt tokens: {response.provider_metadata.get('prompt_tokens', '?')}")
        print(f"  Completion tokens: {response.provider_metadata.get('completion_tokens', '?')}")
    print(f"  VRAM during gen: {vram_before:.0f} -> {vram_after:.0f} MB")

    if response.error:
        print(f"  ERROR: {response.error}")
        return {
            "name": name,
            "text": "",
            "gen_time": gen_time,
            "tokens": 0,
            "finish_reason": str(response.finish_reason),
            "validator_verdict": "SKIP",
            "violations": [],
            "error": response.error,
        }

    # Validate — build a minimal brief-like object for the validator
    # The validator expects brief.action_type, brief.target_defeated, etc.
    class MiniBrief:
        pass

    brief = MiniBrief()

    if "melee" in name.lower() or "attack" in name.lower():
        brief.action_type = "attack_hit"
        brief.target_defeated = False
        brief.severity = "moderate"
        brief.condition_applied = None
        brief.condition_removed = None
        brief.content_id = None
        brief.save_result = None
    elif "spell" in name.lower() and "condition" in name.lower():
        brief.action_type = "spell_damage_dealt"
        brief.target_defeated = False
        brief.severity = "severe"
        brief.condition_applied = "paralyzed"
        brief.condition_removed = None
        brief.content_id = None
        brief.save_result = "fail"
    elif "aoe" in name.lower():
        brief.action_type = "spell_damage_dealt"
        brief.target_defeated = False  # primary target not defeated
        brief.severity = "devastating"
        brief.condition_applied = None
        brief.condition_removed = None
        brief.content_id = None
        brief.save_result = None

    vresult = validator.validate(response.text, brief)
    print(f"\n--- Validator ---")
    print(f"  Verdict: {vresult.verdict}")
    for v in vresult.violations:
        print(f"  [{v.severity}] {v.rule_id}: {v.detail}")

    return {
        "name": name,
        "text": response.text,
        "gen_time": gen_time,
        "tokens": response.tokens_used,
        "finish_reason": str(response.finish_reason),
        "validator_verdict": vresult.verdict,
        "violations": [(v.rule_id, v.severity, v.detail) for v in vresult.violations],
        "error": None,
    }


def main():
    print("=" * 70)
    print("  SPARK CAGE SHAKEOUT — WO-SPARK-EXPLORE-001")
    print("  Seven Wisdom Zero Regrets")
    print("=" * 70)

    # 1. Load registry + adapter
    print("\n[1] Loading model registry...")
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry, models_dir=".")
    print(f"  llama_cpp available: {adapter._llama_cpp_available}")

    if not adapter._llama_cpp_available:
        print("FATAL: llama_cpp not available. GAP-C not fixed.")
        sys.exit(1)

    # 2. Load model
    model_id = "qwen25-7b-instruct-4bit"
    print(f"\n[2] Loading model: {model_id}")
    vram_before = get_vram_mb()
    t_load_start = time.perf_counter()
    loaded_model = adapter.load_model(model_id)
    t_load_end = time.perf_counter()
    vram_after = get_vram_mb()
    load_time = t_load_end - t_load_start

    print(f"  Load time: {load_time:.2f}s")
    print(f"  Device: {loaded_model.device}")
    print(f"  VRAM: {vram_before:.0f} -> {vram_after:.0f} MB")

    # 3. Init validator
    validator = NarrationValidator()

    # 4. Run scenarios
    print(f"\n[3] Running {len(SCENARIOS)} scenarios...")
    results = []
    for name, prompt in SCENARIOS:
        result = run_scenario(adapter, loaded_model, name, prompt, validator)
        results.append(result)

    # 5. Summary
    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"  Model: {model_id}")
    print(f"  Load time: {load_time:.2f}s")
    print()

    for r in results:
        status = r["validator_verdict"]
        marker = "PASS" if status == "PASS" else status
        print(f"  {r['name']}: {marker} ({r['gen_time']:.2f}s, {r['tokens']} tokens)")
        if r["violations"]:
            for rule_id, sev, detail in r["violations"]:
                print(f"    [{sev}] {rule_id}: {detail}")
        if r["error"]:
            print(f"    ERROR: {r['error']}")

    # 6. Unload
    print(f"\n[4] Unloading model...")
    adapter.unload_model(loaded_model)
    print("  Done.")

    print(f"\n{'='*70}")
    print(f"  SHAKEOUT COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
