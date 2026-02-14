#!/usr/bin/env python3
"""RQ-TTS-002: VRAM Footprint and Persistence Feasibility — Instrumentation Script.

Measures:
1. Baseline VRAM (torch loaded, no models)
2. VRAM consumed by Chatterbox Original (idle)
3. VRAM consumed by Chatterbox Turbo (idle)
4. VRAM consumed by both tiers loaded simultaneously
5. Peak VRAM during active synthesis (Original + Turbo)
6. VRAM release behavior (del + empty_cache)
7. Coexistence analysis: remaining VRAM for LLM/SDXL

Run from project root:
    python scripts/bench_vram.py
"""

import gc
import os
import sys
import time
from pathlib import Path

# Force HuggingFace to use local cache only — avoid network round-trips
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

TURBO_SNAPSHOT = r"C:\Users\Thunder\.cache\huggingface\hub\models--ResembleAI--chatterbox-turbo\snapshots\749d1c1a46eb10492095d68fbcf55691ccf137cd"

REFERENCE_WAV = str(PROJECT_ROOT / "models" / "voices" / "signal_reference_michael_24k.wav")
TEST_TEXT = "The fighter raises his sword and charges across the stone bridge."


def vram_stats():
    """Return dict of VRAM stats in MB."""
    import torch
    return {
        "allocated_mb": torch.cuda.memory_allocated() / 1024**2,
        "reserved_mb": torch.cuda.memory_reserved() / 1024**2,
        "max_allocated_mb": torch.cuda.max_memory_allocated() / 1024**2,
        "total_mb": torch.cuda.get_device_properties(0).total_memory / 1024**2,
    }


def print_vram(label: str):
    stats = vram_stats()
    free = stats["total_mb"] - stats["reserved_mb"]
    print(f"  {label:.<50s}")
    print(f"    Allocated:     {stats['allocated_mb']:8.1f} MB")
    print(f"    Reserved:      {stats['reserved_mb']:8.1f} MB")
    print(f"    Max allocated: {stats['max_allocated_mb']:8.1f} MB")
    print(f"    Free (est):    {free:8.1f} MB")
    return stats


def banner(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    print("RQ-TTS-002: VRAM Footprint and Persistence Feasibility")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")

    import torch

    if not torch.cuda.is_available():
        print("ERROR: CUDA not available. Cannot measure VRAM.")
        sys.exit(1)

    device_name = torch.cuda.get_device_name(0)
    total_vram_mb = torch.cuda.get_device_properties(0).total_memory / 1024**2
    print(f"GPU: {device_name}")
    print(f"Total VRAM: {total_vram_mb:.0f} MB ({total_vram_mb/1024:.1f} GB)")

    # ---- Baseline ----
    banner("1. BASELINE (torch loaded, no models)")
    torch.cuda.reset_peak_memory_stats()
    baseline = print_vram("Baseline")

    # ---- Original only ----
    banner("2. CHATTERBOX ORIGINAL (idle)")
    from chatterbox.tts import ChatterboxTTS
    torch.cuda.reset_peak_memory_stats()
    model_original = ChatterboxTTS.from_pretrained(device="cuda")
    original_idle = print_vram("Original loaded (idle)")

    # ---- Original active synthesis ----
    banner("3. CHATTERBOX ORIGINAL (active synthesis)")
    torch.cuda.reset_peak_memory_stats()
    wav = model_original.generate(
        text=TEST_TEXT,
        audio_prompt_path=REFERENCE_WAV,
        exaggeration=0.5,
        cfg_weight=0.5,
    )
    original_active = print_vram("Original after synthesis")
    print(f"    Peak during synthesis: {torch.cuda.max_memory_allocated()/1024**2:.1f} MB")

    # ---- Add Turbo (both loaded) ----
    banner("4. BOTH TIERS LOADED (Original + Turbo)")
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    torch.cuda.reset_peak_memory_stats()
    model_turbo = ChatterboxTurboTTS.from_local(TURBO_SNAPSHOT, device="cuda")
    both_idle = print_vram("Both tiers loaded (idle)")
    banner("5. BOTH TIERS — TURBO SYNTHESIS")
    torch.cuda.reset_peak_memory_stats()
    wav_turbo = model_turbo.generate(
        text=TEST_TEXT,
        audio_prompt_path=REFERENCE_WAV,
    )
    both_turbo_active = print_vram("After Turbo synthesis (both loaded)")
    print(f"    Peak during synthesis: {torch.cuda.max_memory_allocated()/1024**2:.1f} MB")

    # ---- Release Turbo ----
    banner("6. VRAM RELEASE — del Turbo + empty_cache")
    del model_turbo
    torch.cuda.empty_cache()
    gc.collect()
    after_del_turbo = print_vram("After deleting Turbo")

    # ---- Release Original ----
    banner("7. VRAM RELEASE — del Original + empty_cache")
    del model_original
    torch.cuda.empty_cache()
    gc.collect()
    after_del_all = print_vram("After deleting all models")

    # ---- Turbo only ----
    banner("8. CHATTERBOX TURBO ONLY (idle)")
    torch.cuda.reset_peak_memory_stats()
    model_turbo_solo = ChatterboxTurboTTS.from_local(TURBO_SNAPSHOT, device="cuda")
    turbo_idle = print_vram("Turbo loaded (idle)")

    # ---- Turbo active ----
    banner("9. CHATTERBOX TURBO (active synthesis)")
    torch.cuda.reset_peak_memory_stats()
    wav_turbo2 = model_turbo_solo.generate(
        text=TEST_TEXT,
        audio_prompt_path=REFERENCE_WAV,
    )
    turbo_active = print_vram("Turbo after synthesis")
    print(f"    Peak during synthesis: {torch.cuda.max_memory_allocated()/1024**2:.1f} MB")

    del model_turbo_solo
    torch.cuda.empty_cache()
    gc.collect()

    # ---- Summary ----
    banner("VRAM SUMMARY")
    print(f"  GPU: {device_name}")
    print(f"  Total VRAM: {total_vram_mb:.0f} MB ({total_vram_mb/1024:.1f} GB)")
    print()
    print(f"  {'Model Configuration':.<40s} {'Allocated':>10s}  {'Reserved':>10s}")
    print(f"  {'-'*40} {'-'*10}  {'-'*10}")
    print(f"  {'Baseline (no models)':.<40s} {baseline['allocated_mb']:>9.1f}M  {baseline['reserved_mb']:>9.1f}M")
    print(f"  {'Original only (idle)':.<40s} {original_idle['allocated_mb']:>9.1f}M  {original_idle['reserved_mb']:>9.1f}M")
    print(f"  {'Turbo only (idle)':.<40s} {turbo_idle['allocated_mb']:>9.1f}M  {turbo_idle['reserved_mb']:>9.1f}M")
    print(f"  {'Both tiers (idle)':.<40s} {both_idle['allocated_mb']:>9.1f}M  {both_idle['reserved_mb']:>9.1f}M")
    print()

    # Coexistence estimates
    remaining_after_original = total_vram_mb - original_idle['reserved_mb']
    remaining_after_both = total_vram_mb - both_idle['reserved_mb']
    print(f"  COEXISTENCE ANALYSIS (remaining VRAM):")
    print(f"    After Original only:   {remaining_after_original:.0f} MB ({remaining_after_original/1024:.1f} GB)")
    print(f"    After both tiers:      {remaining_after_both:.0f} MB ({remaining_after_both/1024:.1f} GB)")
    print()
    print(f"  Typical 7B LLM (4-bit):  ~4500 MB (4.4 GB)")
    print(f"  SDXL (fp16):             ~6500 MB (6.3 GB)")
    print(f"  Original + 7B LLM:      {'FITS' if remaining_after_original > 4500 else 'DOES NOT FIT'}")
    print(f"  Both tiers + 7B LLM:    {'FITS' if remaining_after_both > 4500 else 'DOES NOT FIT'}")
    print(f"  Original + SDXL:        {'FITS' if remaining_after_original > 6500 else 'DOES NOT FIT'}")

    # VRAM release effectiveness
    banner("VRAM RELEASE EFFECTIVENESS")
    print(f"  After deleting all models:")
    print(f"    Allocated: {after_del_all['allocated_mb']:.1f} MB (vs baseline {baseline['allocated_mb']:.1f} MB)")
    print(f"    Reserved:  {after_del_all['reserved_mb']:.1f} MB (vs baseline {baseline['reserved_mb']:.1f} MB)")
    leak = after_del_all['allocated_mb'] - baseline['allocated_mb']
    print(f"    VRAM leak: {leak:.1f} MB ({'CLEAN' if leak < 10 else 'FRAGMENTS PERSIST'})")

    banner("BENCHMARK COMPLETE")
