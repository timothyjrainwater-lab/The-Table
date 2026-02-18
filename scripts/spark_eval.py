"""WO-SPARK-LLM-SELECTION: Full evaluation script for Spark LLM candidates.

Runs Gates S1-S5 per candidate under SEQUENTIAL posture (Addendum A).
Measures load time, inference time, VRAM via nvidia-smi, quality rubric.

Usage: python scripts/spark_eval.py
"""

import os
import sys
import time
import gc
import json
import subprocess
import re

# Fix DLL loading for llama-cpp-python on Windows
lib_path = r"F:\DnD-3.5\.venvs\fish_speech\Lib\site-packages\llama_cpp\lib"
os.add_dll_directory(lib_path)

import torch

cuda_lib = os.path.join(os.path.dirname(torch.__file__), "lib")
if os.path.exists(cuda_lib):
    os.add_dll_directory(cuda_lib)

from llama_cpp import Llama

# ─── Constants ────────────────────────────────────────────────────────────

MODELS_DIR = r"F:\DnD-3.5\models"

CANDIDATES = [
    {
        "id": "qwen2.5-7b-instruct",
        "name": "Qwen2.5 7B Instruct (Q4_K_M)",
        "family": "Qwen (Alibaba)",
        "params": "7.6B",
        "quant": "Q4_K_M",
        "path": os.path.join(MODELS_DIR, "Qwen2.5-7B-Instruct-Q4_K_M.gguf"),
        "class": "A",
    },
    {
        "id": "llama-3.1-8b-instruct",
        "name": "LLaMA 3.1 8B Instruct (Q4_K_M)",
        "family": "LLaMA (Meta)",
        "params": "8B",
        "quant": "Q4_K_M",
        "path": os.path.join(MODELS_DIR, "llama-3.1-8b-instruct-Q4_K_M.gguf"),
        "class": "B",
    },
    {
        "id": "gemma-2-9b-it",
        "name": "Gemma 2 9B IT (Q4_K_M)",
        "family": "Gemma (Google)",
        "params": "9.2B",
        "quant": "Q4_K_M",
        "path": os.path.join(MODELS_DIR, "gemma-2-9b-it-Q4_K_M.gguf"),
        "class": "C",
    },
]

# ─── PromptPack Scenarios ─────────────────────────────────────────────────

# These are real PromptPack-style prompts based on the 5-channel schema
# (Truth, Memory, Task, Style, Contract) from the research prep.

MELEE_PROMPT = """=== TRUTH ===
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

AOE_PROMPT = """=== TRUTH ===
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

HEAL_PROMPT = """=== TRUTH ===
Action: spell_healed
Actor: Brother Aldric
Target: Kael
Outcome: Brother Aldric heals Kael with cure serious wounds
Severity: moderate
Spell: Cure Serious Wounds

=== MEMORY ===
Previous: Kael fell to his knees, bloodied from the onslaught.
Scene: Behind a stone pillar, away from the front line

=== TASK ===
Write a combat narration for a tabletop RPG. Describe what happens in 2-4 vivid sentences suitable for reading aloud at the table. Use the facts above. Do NOT invent damage numbers, HP values, AC, or dice rolls. Do NOT add new NPCs or locations not mentioned above.

=== STYLE ===
Voice: Confident dungeon master
Tone: Solemn, a quiet moment amid violence
Pacing: Gentle rhythm contrasting the preceding combat

=== CONTRACT ===
Format: Prose narration, 2-4 sentences
Maximum: 400 characters
Required: Use character names from TRUTH section
Forbidden: HP restored, healing amounts, meta-game terms

Narration:"""

SCENARIOS = [
    ("melee_attack", MELEE_PROMPT),
    ("aoe_fireball", AOE_PROMPT),
    ("healing_spell", HEAL_PROMPT),
]


def get_vram_nvidia_smi():
    """Get VRAM usage via nvidia-smi (more accurate than torch for llama.cpp)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            return {"used_mb": int(parts[0].strip()), "total_mb": int(parts[1].strip())}
    except Exception:
        pass
    return {"used_mb": 0, "total_mb": 0}


def load_model(path, n_ctx=2048):
    """Load a GGUF model and return (model, load_time_s)."""
    t0 = time.perf_counter()
    llm = Llama(
        model_path=path,
        n_ctx=n_ctx,
        n_gpu_layers=-1,
        n_batch=512,
        verbose=False,
    )
    t1 = time.perf_counter()
    return llm, t1 - t0


def unload_model(llm):
    """Unload model and force VRAM cleanup."""
    del llm
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    # Give GPU a moment to free memory
    time.sleep(0.5)


def generate(llm, prompt, max_tokens=150, temperature=0.8, seed=None):
    """Generate text and return (text, time_s, tokens_used)."""
    kwargs = {
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stop": ["</narration>", "\n\n"],
        "echo": False,
    }
    if seed is not None:
        kwargs["seed"] = seed

    t0 = time.perf_counter()
    output = llm(prompt, **kwargs)
    t1 = time.perf_counter()

    text = output["choices"][0]["text"].strip()
    usage = output.get("usage", {})
    tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    return text, t1 - t0, tokens, completion_tokens


# ─── Gate Functions ────────────────────────────────────────────────────────

def run_gate_s1(llm, candidate_name):
    """Gate S1: PromptPack Compatibility. Returns (pass, results)."""
    print(f"\n  === S1: PromptPack Compatibility ({candidate_name}) ===")
    results = []
    all_pass = True

    for name, prompt in SCENARIOS:
        text, gen_time, tokens, comp_tokens = generate(llm, prompt)
        print(f"    [{name}] {gen_time:.2f}s, {comp_tokens} completion tokens")
        print(f"    Output: {text[:200]}")

        # Check for failures
        issues = []
        if not text or len(text) < 20:
            issues.append("output too short")
        if any(w in text.lower() for w in ["i cannot", "i can't", "as an ai", "i'm sorry"]):
            issues.append("model refusal")
        # Check for mechanical data leaks
        if re.search(r"\d+\s*(damage|hp|hit points|AC|armor class)", text, re.IGNORECASE):
            issues.append("mechanical data leak")

        passed = len(issues) == 0
        if not passed:
            all_pass = False
            print(f"    FAIL: {', '.join(issues)}")
        else:
            print(f"    PASS")

        results.append({
            "scenario": name,
            "text": text,
            "gen_time_s": gen_time,
            "tokens": tokens,
            "completion_tokens": comp_tokens,
            "passed": passed,
            "issues": issues,
        })

    return all_pass, results


def run_gate_s2(llm, candidate_name, load_time_s):
    """Gate S2: Latency Budget (sequential, Addendum A).

    Measures: (a) Spark load time, (b) TTFT proxy, (c) total gen time.
    Pass: single-beat end-to-end <= 8.0s.
    """
    print(f"\n  === S2: Latency Budget ({candidate_name}) ===")

    # We already have load_time_s from model loading.
    # For end-to-end: load Spark + generate + unload Spark = Spark portion.
    # Chatterbox load + synthesis adds ~3-4s per addendum estimates.
    # But we measure Spark portion only and report.

    results = []
    all_pass = True

    for name, prompt in SCENARIOS:
        text, gen_time, tokens, comp_tokens = generate(llm, prompt)

        # End-to-end estimate (single beat, sequential):
        # Unload CB (~0.5s) + Load Spark + Generate + Unload Spark (~0.5s) + Load CB (~1.5s) + Synth (~1.5s)
        # We measure: Load Spark + Generate
        spark_portion = load_time_s + gen_time
        estimated_e2e = spark_portion + 0.5 + 0.5 + 1.5 + 1.5  # conservative
        passed = estimated_e2e <= 8.0

        if not passed:
            all_pass = False

        print(f"    [{name}] spark_load={load_time_s:.2f}s gen={gen_time:.2f}s "
              f"spark_total={spark_portion:.2f}s est_e2e={estimated_e2e:.2f}s "
              f"{'PASS' if passed else 'FAIL'}")

        results.append({
            "scenario": name,
            "spark_load_time_s": load_time_s,
            "spark_gen_time_s": gen_time,
            "spark_total_s": spark_portion,
            "estimated_e2e_s": estimated_e2e,
            "passed": passed,
        })

    return all_pass, results


def score_quality(text, scenario_name):
    """Gate S3: Score a single output on 5 dimensions.

    Returns dict with scores and notes.
    Scoring is automated heuristic — not perfect but consistent.
    """
    scores = {}
    notes = []

    # 1. Clarity & confidence (1-5)
    hedging_words = ["perhaps", "maybe", "might", "possibly", "could be", "it seems", "apparently"]
    hedge_count = sum(1 for w in hedging_words if w in text.lower())
    if hedge_count == 0 and len(text) > 30:
        scores["clarity"] = 5
    elif hedge_count <= 1:
        scores["clarity"] = 4
    elif hedge_count <= 2:
        scores["clarity"] = 3
    else:
        scores["clarity"] = 2
        notes.append(f"hedging: {hedge_count} instances")

    # 2. Pacing & table presence (1-5)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if 2 <= len(sentences) <= 4:
        scores["pacing"] = 5
    elif len(sentences) == 1 or len(sentences) == 5:
        scores["pacing"] = 4
    elif len(sentences) == 6:
        scores["pacing"] = 3
    else:
        scores["pacing"] = 2
        notes.append(f"sentence count: {len(sentences)}")

    # 3. Fidelity to facts (1-5)
    fidelity = 5
    # Check for scenario-specific names
    if scenario_name == "melee_attack":
        required = ["kael", "goblin"]
        for r in required:
            if r not in text.lower():
                fidelity -= 1
                notes.append(f"missing: {r}")
    elif scenario_name == "aoe_fireball":
        required = ["elara", "fireball"]
        for r in required:
            if r not in text.lower():
                fidelity -= 1
                notes.append(f"missing: {r}")
    elif scenario_name == "healing_spell":
        required = ["aldric", "kael"]
        for r in required:
            if r not in text.lower():
                fidelity -= 1
                notes.append(f"missing: {r}")

    # Check for invented mechanical data
    if re.search(r"\d+\s*(damage|hp|hit points|AC|points of)", text, re.IGNORECASE):
        fidelity -= 2
        notes.append("invented mechanical data")
    scores["fidelity"] = max(1, fidelity)

    # 4. Controlled improvisation (1-5)
    improv = 5
    # Check for invented names not in the prompt
    known_names = {"kael", "elara", "aldric", "goblin", "scout", "warrior", "archer", "brother"}
    words = set(re.findall(r'\b[A-Z][a-z]+\b', text))
    novel_names = [w for w in words if w.lower() not in known_names
                   and w.lower() not in {"the", "his", "her", "its", "with", "from", "into", "upon"}]
    if len(novel_names) > 2:
        improv -= 1
        notes.append(f"novel proper nouns: {novel_names[:3]}")
    scores["improvisation"] = max(1, improv)

    # 5. Cadence for TTS (1-5)
    cadence = 5
    # Check for very long sentences (>40 words)
    for s in sentences:
        if len(s.split()) > 40:
            cadence -= 1
            notes.append("sentence >40 words")
            break
    # Check for nested clauses (multiple commas in one sentence)
    for s in sentences:
        if s.count(",") >= 4:
            cadence -= 1
            notes.append("heavy subordination")
            break
    scores["cadence"] = max(1, cadence)

    total = sum(scores.values())
    return {
        "clarity": scores["clarity"],
        "pacing": scores["pacing"],
        "fidelity": scores["fidelity"],
        "improvisation": scores["improvisation"],
        "cadence": scores["cadence"],
        "total": total,
        "notes": notes,
    }


def run_gate_s3(s1_results, candidate_name):
    """Gate S3: Quality Rubric. Scores S1 outputs."""
    print(f"\n  === S3: Quality Rubric ({candidate_name}) ===")
    results = []
    total_score = 0

    for r in s1_results:
        scores = score_quality(r["text"], r["scenario"])
        total_score += scores["total"]
        print(f"    [{r['scenario']}] {scores['total']}/25 "
              f"(C={scores['clarity']} P={scores['pacing']} F={scores['fidelity']} "
              f"I={scores['improvisation']} T={scores['cadence']})")
        if scores["notes"]:
            print(f"      Notes: {', '.join(scores['notes'])}")
        results.append({"scenario": r["scenario"], **scores})

    avg_score = total_score / len(s1_results)
    passed = avg_score >= 15.0
    print(f"    Average: {avg_score:.1f}/25 {'PASS' if passed else 'FAIL'}")

    return passed, results, avg_score


def run_gate_s4(candidate, candidate_name):
    """Gate S4: Sequential Coexistence Stability (Addendum A).

    5 swap loops: load Spark → generate 3 narrations → unload Spark.
    No Chatterbox available — measure Spark swap lifecycle only.
    """
    print(f"\n  === S4: Sequential Coexistence Stability ({candidate_name}) ===")
    results = []
    all_pass = True

    vram_readings = []

    for loop in range(5):
        # Load
        llm, load_time = load_model(candidate["path"])
        vram_after_load = get_vram_nvidia_smi()

        # Generate 3 narrations (batch)
        gen_times = []
        for name, prompt in SCENARIOS:
            text, gen_time, _, _ = generate(llm, prompt)
            gen_times.append(gen_time)

        vram_after_gen = get_vram_nvidia_smi()

        # Unload
        unload_model(llm)
        vram_after_unload = get_vram_nvidia_smi()

        vram_readings.append(vram_after_load["used_mb"])

        print(f"    Loop {loop+1}: load={load_time:.2f}s gen={sum(gen_times):.2f}s "
              f"VRAM: load={vram_after_load['used_mb']}MB gen={vram_after_gen['used_mb']}MB "
              f"unload={vram_after_unload['used_mb']}MB")

        results.append({
            "loop": loop + 1,
            "load_time_s": load_time,
            "gen_total_s": sum(gen_times),
            "vram_after_load_mb": vram_after_load["used_mb"],
            "vram_after_gen_mb": vram_after_gen["used_mb"],
            "vram_after_unload_mb": vram_after_unload["used_mb"],
        })

    # Check for VRAM leak: loop 5 <= loop 1 + 100 MB
    if len(vram_readings) >= 2:
        drift = vram_readings[-1] - vram_readings[0]
        if drift > 100:
            all_pass = False
            print(f"    FAIL: VRAM drift {drift}MB exceeds 100MB tolerance")
        else:
            print(f"    VRAM drift: {drift}MB (tolerance: 100MB) PASS")

    return all_pass, results


def run_gate_s5(candidate, candidate_name):
    """Gate S5: Repeat Stability. Same prompt 3 times, check factual consistency."""
    print(f"\n  === S5: Repeat Stability ({candidate_name}) ===")

    llm, _ = load_model(candidate["path"])
    results = []
    texts = []

    for run in range(3):
        text, gen_time, _, _ = generate(llm, MELEE_PROMPT, seed=42)
        texts.append(text)
        print(f"    Run {run+1}: {text[:120]}...")
        results.append({"run": run + 1, "text": text, "gen_time_s": gen_time})

    unload_model(llm)

    # Check factual consistency: all should reference Kael, Goblin Scout, longsword
    all_pass = True
    for i, text in enumerate(texts):
        t_lower = text.lower()
        if "kael" not in t_lower:
            all_pass = False
            print(f"    FAIL: Run {i+1} missing 'Kael'")
        if "goblin" not in t_lower:
            all_pass = False
            print(f"    FAIL: Run {i+1} missing 'goblin'")

    if all_pass:
        print(f"    All 3 runs reference correct characters. PASS")

    return all_pass, results


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("WO-SPARK-LLM-SELECTION: Full Candidate Evaluation")
    print("Posture: SEQUENTIAL (Addendum A)")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**2:.0f} MB")
    print(f"llama-cpp-python: {Llama.__module__}")
    print("=" * 70)

    baseline_vram = get_vram_nvidia_smi()
    print(f"Baseline VRAM: {baseline_vram['used_mb']}MB / {baseline_vram['total_mb']}MB")

    all_results = {}

    for candidate in CANDIDATES:
        cid = candidate["id"]
        cname = candidate["name"]

        print(f"\n{'#' * 70}")
        print(f"# CANDIDATE: {cname} (Class {candidate['class']})")
        print(f"{'#' * 70}")

        # Check file exists
        if not os.path.exists(candidate["path"]):
            print(f"  SKIP: Model file not found: {candidate['path']}")
            all_results[cid] = {"status": "skipped", "reason": "file not found"}
            continue

        # Load model (measure load time)
        print(f"\n  Loading model...")
        try:
            llm, load_time = load_model(candidate["path"])
        except Exception as e:
            print(f"  SKIP: Failed to load: {type(e).__name__}: {e}")
            all_results[cid] = {"status": "load_failed", "reason": str(e)}
            continue

        vram_loaded = get_vram_nvidia_smi()
        gguf_size_gb = os.path.getsize(candidate["path"]) / 1024**3
        print(f"  Loaded in {load_time:.2f}s")
        print(f"  GGUF size: {gguf_size_gb:.1f} GB")
        print(f"  VRAM after load: {vram_loaded['used_mb']}MB")

        result = {
            "status": "evaluated",
            "load_time_s": load_time,
            "gguf_size_gb": round(gguf_size_gb, 1),
            "vram_loaded_mb": vram_loaded["used_mb"],
        }

        # Gate S1: PromptPack Compatibility
        s1_pass, s1_results = run_gate_s1(llm, cname)
        result["s1"] = {"passed": s1_pass, "results": s1_results}

        if not s1_pass:
            print(f"\n  S1 FAILED — skipping remaining gates for {cname}")
            unload_model(llm)
            all_results[cid] = result
            continue

        # Gate S2: Latency Budget
        s2_pass, s2_results = run_gate_s2(llm, cname, load_time)
        result["s2"] = {"passed": s2_pass, "results": s2_results}

        # Gate S3: Quality Rubric (uses S1 outputs)
        s3_pass, s3_results, s3_avg = run_gate_s3(s1_results, cname)
        result["s3"] = {"passed": s3_pass, "results": s3_results, "average": s3_avg}

        # Unload before S4 (S4 does its own load/unload cycles)
        unload_model(llm)

        # Gate S4: Sequential Coexistence Stability
        s4_pass, s4_results = run_gate_s4(candidate, cname)
        result["s4"] = {"passed": s4_pass, "results": s4_results}

        # Gate S5: Repeat Stability
        s5_pass, s5_results = run_gate_s5(candidate, cname)
        result["s5"] = {"passed": s5_pass, "results": s5_results}

        # Summary
        gates_passed = sum([s1_pass, s2_pass, s3_pass, s4_pass, s5_pass])
        result["gates_passed"] = f"{gates_passed}/5"
        result["all_gates_passed"] = gates_passed == 5

        all_results[cid] = result

        print(f"\n  === CANDIDATE SUMMARY: {cname} ===")
        print(f"  S1={'PASS' if s1_pass else 'FAIL'} S2={'PASS' if s2_pass else 'FAIL'} "
              f"S3={'PASS' if s3_pass else 'FAIL'} (avg {s3_avg:.1f}/25) "
              f"S4={'PASS' if s4_pass else 'FAIL'} S5={'PASS' if s5_pass else 'FAIL'}")
        print(f"  Gates: {gates_passed}/5")

    # Final summary
    print(f"\n{'=' * 70}")
    print("FINAL EVALUATION SUMMARY")
    print(f"{'=' * 70}")

    for cid, result in all_results.items():
        if result["status"] == "evaluated":
            print(f"\n{cid}:")
            print(f"  Load: {result['load_time_s']:.2f}s | VRAM: {result['vram_loaded_mb']}MB | "
                  f"GGUF: {result['gguf_size_gb']}GB")
            print(f"  Gates: {result['gates_passed']}")
            if "s3" in result:
                print(f"  Quality avg: {result['s3']['average']:.1f}/25")
        else:
            print(f"\n{cid}: {result['status']} — {result.get('reason', 'unknown')}")

    # Save results
    output_path = os.path.join(r"F:\DnD-3.5\pm_inbox", "SPARK_EVAL_RAW_RESULTS.json")
    with open(output_path, "w", encoding="utf-8") as f:
        # Convert results to serializable format (strip long text for JSON)
        serializable = {}
        for cid, result in all_results.items():
            serializable[cid] = result
        json.dump(serializable, f, indent=2, default=str)
    print(f"\nRaw results saved to: {output_path}")


if __name__ == "__main__":
    main()
