#!/usr/bin/env python3
"""RQ-TTS-001: Cold Start Time Breakdown — Instrumentation Script.

Measures each phase of TTS cold start independently:
1. Python interpreter startup + non-torch imports
2. `import torch` time
3. CUDA context initialization
4. Model weight loading (Original + Turbo)
5. First inference pass (warm-up)
6. Second inference pass (steady state)

Also measures the same breakdown for Kokoro (ONNX).

Run from project root:
    python scripts/bench_cold_start.py
"""

import gc
import os
import statistics
import sys
import time
from pathlib import Path

# Force HuggingFace to use local cache only — avoid network round-trips
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Kokoro model paths
KOKORO_MODEL = str(PROJECT_ROOT / "models" / "kokoro" / "kokoro-v1.0.int8.onnx")
KOKORO_VOICES = str(PROJECT_ROOT / "models" / "kokoro" / "voices-v1.0.bin")
REFERENCE_WAV = str(PROJECT_ROOT / "models" / "voices" / "signal_reference_michael_24k.wav")

TEST_TEXT = "The fighter raises his sword and charges across the stone bridge."
ITERATIONS = 5


def measure(label: str, fn, iterations: int = ITERATIONS):
    """Run fn() multiple times, return (mean_ms, stdev_ms, all_times_ms)."""
    times = []
    for i in range(iterations):
        gc.collect()
        t0 = time.perf_counter()
        result = fn()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    mean = statistics.mean(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0.0
    return mean, stdev, times, result


def banner(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def report(label: str, mean: float, stdev: float, times: list):
    print(f"  {label:.<45s} {mean:8.1f} ms  (stdev {stdev:6.1f} ms)")
    print(f"    Individual runs: {', '.join(f'{t:.1f}' for t in times)}")


# ======================================================================
# CHATTERBOX COLD START BREAKDOWN
# ======================================================================

def bench_chatterbox():
    banner("CHATTERBOX COLD START BREAKDOWN")

    # --- Phase 1: Non-torch imports ---
    def phase_stdlib_imports():
        # These are already imported, so we measure re-import (cached).
        # For cold start, we measure the initial import cost in a subprocess.
        import io          # noqa: F401
        import logging     # noqa: F401
        import wave        # noqa: F401
        from aidm.immersion.tts_chunking import chunk_by_sentence  # noqa: F401
        from aidm.schemas.immersion import VoicePersona  # noqa: F401

    mean, stdev, times, _ = measure("Phase 1: stdlib + project imports (cached)", phase_stdlib_imports)
    report("Phase 1: stdlib + project imports (cached)", mean, stdev, times)

    # --- Phase 2: import torch ---
    # First import is the expensive one; subsequent are cached.
    print("\n  Phase 2: import torch (first import)...")
    t0 = time.perf_counter()
    import torch  # noqa: F401
    t1 = time.perf_counter()
    torch_import_ms = (t1 - t0) * 1000
    print(f"  {'Phase 2: import torch':.<45s} {torch_import_ms:8.1f} ms  (single shot — cannot repeat)")

    # --- Phase 3: CUDA context init ---
    print("\n  Phase 3: CUDA context initialization...")
    t0 = time.perf_counter()
    cuda_available = torch.cuda.is_available()
    t1 = time.perf_counter()
    cuda_init_ms = (t1 - t0) * 1000
    print(f"  {'Phase 3: torch.cuda.is_available()':.<45s} {cuda_init_ms:8.1f} ms  (single shot)")
    print(f"    CUDA available: {cuda_available}")

    if cuda_available:
        t0 = time.perf_counter()
        device_name = torch.cuda.get_device_name(0)
        t1 = time.perf_counter()
        print(f"  {'Phase 3b: torch.cuda.get_device_name()':.<45s} {(t1-t0)*1000:8.1f} ms")
        print(f"    GPU: {device_name}")
        print(f"    VRAM total: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    if not cuda_available:
        print("  CUDA not available — skipping GPU model loading phases.")
        return

    # --- Phase 4a: Chatterbox Original model loading ---
    print("\n  Phase 4a: Chatterbox Original model loading...")
    t0 = time.perf_counter()
    from chatterbox.tts import ChatterboxTTS
    t1 = time.perf_counter()
    import_original_ms = (t1 - t0) * 1000
    print(f"  {'Phase 4a-i: import chatterbox.tts':.<45s} {import_original_ms:8.1f} ms")

    t0 = time.perf_counter()
    model_original = ChatterboxTTS.from_pretrained(device="cuda")
    t1 = time.perf_counter()
    load_original_ms = (t1 - t0) * 1000
    print(f"  {'Phase 4a-ii: Original from_pretrained()':.<45s} {load_original_ms:8.1f} ms")

    vram_after_original = torch.cuda.memory_allocated() / 1024**2
    print(f"    VRAM after Original load: {vram_after_original:.1f} MB")

    # --- Phase 5a: First inference (Original) ---
    print("\n  Phase 5a: First inference — Original (warm-up)...")
    t0 = time.perf_counter()
    wav_original = model_original.generate(
        text=TEST_TEXT,
        audio_prompt_path=REFERENCE_WAV,
        exaggeration=0.5,
        cfg_weight=0.5,
    )
    t1 = time.perf_counter()
    first_infer_original_ms = (t1 - t0) * 1000
    print(f"  {'Phase 5a: Original first inference':.<45s} {first_infer_original_ms:8.1f} ms")

    # --- Phase 6a: Second inference (Original, steady state) ---
    def infer_original():
        return model_original.generate(
            text=TEST_TEXT,
            audio_prompt_path=REFERENCE_WAV,
            exaggeration=0.5,
            cfg_weight=0.5,
        )
    mean, stdev, times, _ = measure("Phase 6a: Original steady-state inference", infer_original, iterations=3)
    report("Phase 6a: Original steady-state inference", mean, stdev, times)

    # Free Original to measure Turbo independently
    del model_original
    torch.cuda.empty_cache()
    gc.collect()
    vram_after_del = torch.cuda.memory_allocated() / 1024**2
    print(f"\n  VRAM after deleting Original + empty_cache: {vram_after_del:.1f} MB")

    # --- Phase 4b: Chatterbox Turbo model loading ---
    print("\n  Phase 4b: Chatterbox Turbo model loading...")
    t0 = time.perf_counter()
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    t1 = time.perf_counter()
    import_turbo_ms = (t1 - t0) * 1000
    print(f"  {'Phase 4b-i: import chatterbox.tts_turbo':.<45s} {import_turbo_ms:8.1f} ms")

    # Use from_local to bypass HuggingFace token requirement on Turbo
    turbo_snapshot = r"C:\Users\Thunder\.cache\huggingface\hub\models--ResembleAI--chatterbox-turbo\snapshots\749d1c1a46eb10492095d68fbcf55691ccf137cd"
    t0 = time.perf_counter()
    model_turbo = ChatterboxTurboTTS.from_local(turbo_snapshot, device="cuda")
    t1 = time.perf_counter()
    load_turbo_ms = (t1 - t0) * 1000
    print(f"  {'Phase 4b-ii: Turbo from_local()':.<45s} {load_turbo_ms:8.1f} ms")

    vram_after_turbo = torch.cuda.memory_allocated() / 1024**2
    print(f"    VRAM after Turbo load: {vram_after_turbo:.1f} MB")

    # --- Phase 5b: First inference (Turbo) ---
    print("\n  Phase 5b: First inference — Turbo (warm-up)...")
    t0 = time.perf_counter()
    wav_turbo = model_turbo.generate(
        text=TEST_TEXT,
        audio_prompt_path=REFERENCE_WAV,
    )
    t1 = time.perf_counter()
    first_infer_turbo_ms = (t1 - t0) * 1000
    print(f"  {'Phase 5b: Turbo first inference':.<45s} {first_infer_turbo_ms:8.1f} ms")

    # --- Phase 6b: Second inference (Turbo, steady state) ---
    def infer_turbo():
        return model_turbo.generate(
            text=TEST_TEXT,
            audio_prompt_path=REFERENCE_WAV,
        )
    mean, stdev, times, _ = measure("Phase 6b: Turbo steady-state inference", infer_turbo, iterations=3)
    report("Phase 6b: Turbo steady-state inference", mean, stdev, times)

    # --- Summary ---
    banner("CHATTERBOX TOTAL COLD START (estimated)")
    total = torch_import_ms + cuda_init_ms + import_original_ms + load_original_ms + first_infer_original_ms
    print(f"  Total cold start (to first audio, Original): {total:.0f} ms")
    print(f"    torch import:      {torch_import_ms:.0f} ms")
    print(f"    CUDA init:         {cuda_init_ms:.0f} ms")
    print(f"    Module import:     {import_original_ms:.0f} ms")
    print(f"    Model load:        {load_original_ms:.0f} ms")
    print(f"    First inference:   {first_infer_original_ms:.0f} ms")

    # Clean up
    del model_turbo
    torch.cuda.empty_cache()
    gc.collect()


# ======================================================================
# KOKORO COLD START BREAKDOWN
# ======================================================================

def bench_kokoro():
    banner("KOKORO COLD START BREAKDOWN")

    # --- Phase 1: ONNX Runtime import ---
    print("  Phase 1: ONNX Runtime import...")
    t0 = time.perf_counter()
    import onnxruntime  # noqa: F401
    t1 = time.perf_counter()
    ort_import_ms = (t1 - t0) * 1000
    print(f"  {'Phase 1: import onnxruntime':.<45s} {ort_import_ms:8.1f} ms")

    # --- Phase 2: kokoro_onnx import ---
    print("\n  Phase 2: kokoro_onnx import...")
    t0 = time.perf_counter()
    from kokoro_onnx import Kokoro
    t1 = time.perf_counter()
    kokoro_import_ms = (t1 - t0) * 1000
    print(f"  {'Phase 2: import kokoro_onnx':.<45s} {kokoro_import_ms:8.1f} ms")

    # --- Phase 3: Model loading ---
    print("\n  Phase 3: Kokoro model loading...")
    t0 = time.perf_counter()
    kokoro = Kokoro(model_path=KOKORO_MODEL, voices_path=KOKORO_VOICES)
    t1 = time.perf_counter()
    model_load_ms = (t1 - t0) * 1000
    print(f"  {'Phase 3: Kokoro() model init':.<45s} {model_load_ms:8.1f} ms")

    # --- Phase 4: First inference ---
    print("\n  Phase 4: First inference (warm-up)...")
    t0 = time.perf_counter()
    samples, sr = kokoro.create(text=TEST_TEXT, voice="af_bella", speed=1.0)
    t1 = time.perf_counter()
    first_infer_ms = (t1 - t0) * 1000
    print(f"  {'Phase 4: Kokoro first inference':.<45s} {first_infer_ms:8.1f} ms")
    print(f"    Output: {len(samples)} samples at {sr} Hz ({len(samples)/sr:.2f}s audio)")

    # --- Phase 5: Steady-state inference ---
    def infer_kokoro():
        return kokoro.create(text=TEST_TEXT, voice="af_bella", speed=1.0)
    mean, stdev, times, _ = measure("Phase 5: Kokoro steady-state inference", infer_kokoro, iterations=3)
    report("Phase 5: Kokoro steady-state inference", mean, stdev, times)

    # --- Summary ---
    banner("KOKORO TOTAL COLD START (estimated)")
    total = ort_import_ms + kokoro_import_ms + model_load_ms + first_infer_ms
    print(f"  Total cold start (to first audio): {total:.0f} ms")
    print(f"    onnxruntime import:  {ort_import_ms:.0f} ms")
    print(f"    kokoro_onnx import:  {kokoro_import_ms:.0f} ms")
    print(f"    Model load:          {model_load_ms:.0f} ms")
    print(f"    First inference:     {first_infer_ms:.0f} ms")


# ======================================================================
# MAIN
# ======================================================================

if __name__ == "__main__":
    print("RQ-TTS-001: Cold Start Time Breakdown")
    print(f"Test text: \"{TEST_TEXT}\"")
    print(f"Iterations per steady-state phase: {ITERATIONS}")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")

    bench_chatterbox()
    bench_kokoro()

    banner("BENCHMARK COMPLETE")