"""A/B Test: Stop Sequence Fix for FINDING-EXPLORE-01

Proves that adding "===" to stop sequences prevents the multi-draft
behavior observed in Scenario B (Hold Person).

Run A: Old stop sequences ["</narration>", "\n\n"] — expect multi-draft
Run B: Fixed stop sequences ["</narration>", "\n\n", "==="] — expect single draft

Per Aegis directive: same prompt pack, same settings, before and after.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aidm.spark.model_registry import ModelRegistry
from aidm.spark.llamacpp_adapter import LlamaCppAdapter
from aidm.spark.spark_adapter import SparkRequest


# The exact Scenario B prompt from the shakeout
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


def get_vram_mb():
    """Get VRAM via NVML."""
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


def run_with_stop_sequences(adapter, loaded_model, stop_sequences, label):
    """Run Scenario B with specific stop sequences and capture everything."""
    print(f"\n{'='*70}")
    print(f"  RUN {label}")
    print(f"  Stop sequences: {stop_sequences}")
    print(f"{'='*70}")

    request = SparkRequest(
        prompt=SCENARIO_B_SPELL,
        max_tokens=300,  # Higher limit to let multi-draft happen if it will
        temperature=0.8,
        stop_sequences=stop_sequences,
    )

    vram_before = get_vram_mb()
    t_start = time.perf_counter()
    response = adapter.generate(request, loaded_model)
    t_end = time.perf_counter()
    vram_after = get_vram_mb()

    gen_time = t_end - t_start

    result = {
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stop_sequences": stop_sequences,
        "prompt": SCENARIO_B_SPELL,
        "max_tokens": 300,
        "temperature": 0.8,
        "raw_output": response.text,
        "tokens_used": response.tokens_used,
        "finish_reason": str(response.finish_reason),
        "gen_time_s": round(gen_time, 3),
        "vram_before_mb": round(vram_before, 1),
        "vram_after_mb": round(vram_after, 1),
        "provider_metadata": response.provider_metadata or {},
        "error": response.error,
        "contains_separator": "===" in (response.text or ""),
        "newline_count": (response.text or "").count("\n"),
        "char_count": len(response.text or ""),
    }

    print(f"\n--- Raw Output ---")
    print(response.text)
    print(f"\n--- Metrics ---")
    print(f"  Gen time: {gen_time:.2f}s")
    print(f"  Tokens: {response.tokens_used}")
    print(f"  Finish reason: {response.finish_reason}")
    print(f"  Contains '===': {result['contains_separator']}")
    print(f"  Char count: {result['char_count']}")
    print(f"  VRAM: {vram_before:.0f} -> {vram_after:.0f} MB")

    if response.provider_metadata:
        print(f"  Completion tokens: {response.provider_metadata.get('completion_tokens', '?')}")

    return result


def main():
    print("=" * 70)
    print("  A/B TEST: STOP SEQUENCE FIX (FINDING-EXPLORE-01)")
    print("  Aegis directive: same prompt, same settings, before and after")
    print("=" * 70)

    # Load model
    print("\n[1] Loading model...")
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry, models_dir=".")

    model_id = "qwen25-7b-instruct-4bit"
    t_load_start = time.perf_counter()
    loaded_model = adapter.load_model(model_id)
    t_load_end = time.perf_counter()
    print(f"  Loaded in {t_load_end - t_load_start:.2f}s")
    print(f"  Device: {loaded_model.device}")

    # Run A: OLD stop sequences (without ===)
    result_a = run_with_stop_sequences(
        adapter, loaded_model,
        stop_sequences=["</narration>", "\n\n"],
        label="A (OLD - without === stop)"
    )

    # Run B: FIXED stop sequences (with ===)
    result_b = run_with_stop_sequences(
        adapter, loaded_model,
        stop_sequences=["</narration>", "\n\n", "==="],
        label="B (FIXED - with === stop)"
    )

    # Analysis
    print(f"\n{'='*70}")
    print(f"  A/B COMPARISON")
    print(f"{'='*70}")

    print(f"\n  Run A (old):")
    print(f"    Tokens: {result_a['tokens_used']}")
    print(f"    Chars: {result_a['char_count']}")
    print(f"    Contains '===': {result_a['contains_separator']}")
    print(f"    Finish reason: {result_a['finish_reason']}")

    print(f"\n  Run B (fixed):")
    print(f"    Tokens: {result_b['tokens_used']}")
    print(f"    Chars: {result_b['char_count']}")
    print(f"    Contains '===': {result_b['contains_separator']}")
    print(f"    Finish reason: {result_b['finish_reason']}")

    # Verdict — use completion_tokens from provider_metadata, not tokens_used (which includes prompt)
    a_completion = result_a['provider_metadata'].get('completion_tokens', result_a['tokens_used'])
    b_completion = result_b['provider_metadata'].get('completion_tokens', result_b['tokens_used'])
    a_multi = result_a['contains_separator'] or a_completion > 100
    b_single = not result_b['contains_separator'] and b_completion <= 100

    print(f"\n  Run A shows multi-draft behavior: {a_multi}")
    print(f"  Run B shows single-draft behavior: {b_single}")

    if a_multi and b_single:
        verdict = "CONFIRMED: === stop sequence fix prevents multi-draft"
    elif not a_multi:
        verdict = "INCONCLUSIVE: Run A did not reproduce multi-draft (model non-deterministic)"
    elif not b_single:
        verdict = "FAILED: Run B still shows multi-draft despite fix"
    else:
        verdict = "UNEXPECTED: Review raw outputs"

    print(f"\n  VERDICT: {verdict}")

    # Save artifacts
    artifact = {
        "test": "AB_STOP_SEQUENCE_FIX",
        "finding": "FINDING-EXPLORE-01",
        "model_id": model_id,
        "load_time_s": round(t_load_end - t_load_start, 2),
        "device": loaded_model.device,
        "run_a": result_a,
        "run_b": result_b,
        "verdict": verdict,
    }

    artifact_path = "pm_inbox/AB_FINDING_EXPLORE_01.json"
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)
    print(f"\n  Artifact saved: {artifact_path}")

    # Unload
    adapter.unload_model(loaded_model)
    print("\n  Model unloaded. Test complete.")


if __name__ == "__main__":
    main()
