# RQ-VOICE-001: TTS Quality Baseline — Empirical Benchmark Protocol

**Status:** R0 / BENCHMARK PROTOCOL / REQUIRES HUMAN EXECUTION
**Purpose:** Measure TTS latency and quality on target hardware
**Authority:** Research protocol (PM executes benchmarks)
**Last Updated:** 2026-02-10
**Lead:** Agent C (UX Research)

---

## ⚠️ EXECUTION NOTICE

This document defines **empirical TTS benchmark protocol**.

**Agent C cannot execute this protocol** (no TTS model runtime access).

**Requires:**
- PM or human tester with target hardware
- Piper TTS and/or Coqui TTS installed
- Python benchmark scripts (provided below)

---

## Benchmark Objectives

**Primary Question:** Can Piper or Coqui TTS meet AIDM thresholds on target hardware?

**Thresholds (from R1_TTS_QUALITY_BASELINE.md):**
1. **Latency:** <500ms generation time (ideal <300ms)
2. **Naturalness:** MOS ≥3.5 (sounds natural enough for D&D narration)
3. **Intelligibility:** WER ≤5% (players understand without re-listening)
4. **Session length:** Acceptable for 3+ hour sessions (no voice fatigue)

---

## Test Hardware

**Target Configuration (Median Steam User):**
- **CPU:** 6-8 cores @ 3.0-3.5 GHz (e.g., Intel i5-10400, AMD Ryzen 5 3600)
- **RAM:** 16 GB DDR4 @ 3200 MHz
- **GPU:** GTX 1660 Ti (6 GB VRAM) OR CPU-only fallback
- **OS:** Windows 10/11 or Linux

**Test Both Configurations:**
1. **CPU-only:** No GPU, all TTS on CPU (represents 15% of users)
2. **GPU-accelerated:** GTX 1660 Ti, TTS on GPU (represents 70% of users)

---

## TTS Systems Under Test

### System 1: Piper TTS

**Installation:**
```bash
# Install Piper TTS
pip install piper-tts

# Download model (example: en_US-lessac-medium)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

**Models to Test:**
- `en_US-lessac-medium` (medium quality, fast)
- `en_US-lessac-high` (high quality, slower)
- `en_US-libritts-high` (best quality, slowest)

**Expected Performance:**
- Medium model: ~200-400ms CPU latency
- High model: ~400-800ms CPU latency
- GPU: ~100-200ms latency (all models)

---

### System 2: Coqui TTS

**Installation:**
```bash
# Install Coqui TTS
pip install TTS

# Download model (example: tts_models/en/ljspeech/tacotron2-DDC)
tts --list_models  # List available models
```

**Models to Test:**
- `tts_models/en/ljspeech/tacotron2-DDC` (fast, decent quality)
- `tts_models/en/ljspeech/vits` (fast, good quality)
- `tts_models/en/vctk/vits` (multi-speaker, good quality)

**Expected Performance:**
- Tacotron2: ~300-600ms CPU latency
- VITS: ~200-500ms CPU latency
- GPU: ~100-300ms latency (all models)

---

## Benchmark 1: Latency Measurement

**Objective:** Measure time from text input to audio generation complete

### Test Corpus

**10 D&D narration samples** (varying length):
1. Short (1 sentence): "Your blade strikes true, dealing 12 points of damage."
2. Medium (2-3 sentences): "The goblin's rusty sword clangs against your shield. You feel the impact reverberate through your arm, but your defenses hold firm."
3. Long (4-5 sentences): "As you enter the dimly lit chamber, the smell of decay fills your nostrils. Ancient tapestries hang in tatters from the walls, and a thick layer of dust covers everything. In the center of the room stands a stone pedestal, atop which rests a glowing orb pulsing with arcane energy."

### Measurement Script

```python
import time
from TTS.api import TTS  # or import piper

def benchmark_latency(tts_system, text_samples, num_runs=10):
    """Measure TTS latency over multiple runs."""
    results = []

    for sample in text_samples:
        latencies = []
        for _ in range(num_runs):
            start = time.time()
            tts_system.synthesize(sample)  # Adjust method for system
            end = time.time()
            latencies.append((end - start) * 1000)  # Convert to ms

        results.append({
            'text': sample,
            'mean_latency_ms': sum(latencies) / len(latencies),
            'min_latency_ms': min(latencies),
            'max_latency_ms': max(latencies),
        })

    return results

# Run benchmark
# results = benchmark_latency(tts, corpus, num_runs=10)
# print(results)
```

### Success Criteria

**CPU-only:**
- Short samples: <300ms average latency
- Medium samples: <500ms average latency
- Long samples: <1000ms average latency

**GPU:**
- Short samples: <150ms average latency
- Medium samples: <300ms average latency
- Long samples: <500ms average latency

**Failure Condition:** If average latency >500ms for medium samples on GPU, model is too slow.

---

## Benchmark 2: Naturalness (MOS Equivalent)

**Objective:** Measure perceived naturalness of TTS output

### Listening Test Protocol

**Setup:**
1. Generate audio for 10 D&D narration samples
2. Recruit 5-10 listeners (D&D players preferred)
3. Play each sample, ask: "How natural does this sound?"
   - 5 = Excellent (indistinguishable from human)
   - 4 = Good (clearly synthetic but pleasant)
   - 3 = Fair (robotic but intelligible)
   - 2 = Poor (distracting artifacts)
   - 1 = Bad (unusable)

### Test Samples

**Mix of narration types:**
- Combat: "You swing your sword at the goblin, striking its shoulder for 12 points of damage."
- Exploration: "The ancient door creaks open, revealing a dark corridor beyond."
- NPC dialogue: "The innkeeper greets you warmly. 'Welcome, traveler! What brings you to our humble village?'"
- Spell casting: "You weave the arcane gestures and speak the words of power. A bolt of fire streaks toward your target."

### Analysis

**Calculate MOS:**
- MOS = (Sum of all ratings) / (Number of ratings)

**Success Criteria:**
- MOS ≥3.5 (between Fair and Good)
- <15% of samples rated ≤2 (Poor or Bad)

**Failure Condition:** If MOS <3.5, TTS quality below threshold (text-only preferred).

---

## Benchmark 3: Intelligibility (WER)

**Objective:** Measure word error rate (can listeners understand TTS?)

### Transcription Test

**Setup:**
1. Generate audio for 10 D&D narration samples
2. Play audio to 5-10 listeners
3. Ask listeners to write down what they heard (no replay)
4. Compare transcriptions to original text

### WER Calculation

```python
def calculate_wer(reference, hypothesis):
    """Calculate Word Error Rate."""
    ref_words = reference.split()
    hyp_words = hypothesis.split()

    # Levenshtein distance (simplified)
    # (Insertions + Deletions + Substitutions) / Total words
    # Use python-Levenshtein library for accurate calculation

    import Levenshtein
    distance = Levenshtein.distance(ref_words, hyp_words)
    wer = distance / len(ref_words)
    return wer * 100  # Convert to percentage

# Example
# reference = "Your blade strikes true dealing twelve points of damage"
# hypothesis = "Your blade strikes through dealing twelve points of damage"
# wer = calculate_wer(reference, hypothesis)
# print(f"WER: {wer}%")
```

### Success Criteria

- WER ≤5% (95% of words understood correctly)
- Proper nouns (NPC names, spell names) correctly heard ≥90%

**Failure Condition:** If WER >5%, intelligibility below threshold (players must re-listen or check text).

---

## Benchmark 4: Voice Fatigue (Session Length)

**Objective:** Measure listener fatigue over 3-hour session

### Long Session Test

**Setup:**
1. Generate 3-hour narration script (typical D&D session)
2. Play audio to 5-10 listeners in 30-minute blocks
3. After each block, ask: "How do you feel about the TTS voice?"
   - Still prefer TTS over text
   - Getting tired of TTS, might switch to text soon
   - Ready to switch to text now
   - Already switched to text (fatigue threshold reached)

### Fatigue Measurement

**Track preference over time:**
- 0-30 min: % preferring TTS
- 30-60 min: % preferring TTS
- 60-90 min: % preferring TTS
- 90-120 min: % preferring TTS
- 120-180 min: % preferring TTS
- 180+ min: % preferring TTS

### Success Criteria

- ≥50% of listeners prefer TTS at 180 minutes (3 hours)
- <30% of listeners switch to text before 90 minutes

**Failure Condition:** If >50% switch to text before 120 minutes, voice fatigue too high.

---

## Benchmark 5: Comparative Evaluation (Piper vs Coqui)

**Objective:** Determine which TTS system better meets AIDM thresholds

### Head-to-Head Comparison

**Test Setup:**
1. Generate same 10 samples using Piper and Coqui
2. Play pairs to listeners (blind A/B test)
3. Ask: "Which sounds better? A or B?"

### Scoring

**Winner:** System with most "better" votes

**Evaluation Criteria:**
- Naturalness (which sounds more human?)
- Clarity (which is easier to understand?)
- Preference (which would you use for 3-hour session?)

### Decision Matrix

| Metric | Piper | Coqui | Winner |
|--------|-------|-------|--------|
| Latency (CPU) | ? ms | ? ms | ? |
| Latency (GPU) | ? ms | ? ms | ? |
| MOS | ? | ? | ? |
| WER | ? % | ? % | ? |
| 3-hour preference | ? % | ? % | ? |
| **Overall** | - | - | **?** |

**Decision:** Choose system with best overall score (weighted: latency 30%, MOS 30%, WER 20%, preference 20%)

---

## Execution Checklist

**Pre-Benchmark:**
- [ ] Install Piper TTS + download 3 models
- [ ] Install Coqui TTS + download 3 models
- [ ] Prepare test corpus (10 D&D narration samples)
- [ ] Recruit 5-10 listeners (D&D players preferred)

**Benchmark Execution:**
- [ ] Run latency benchmark (Benchmark 1)
- [ ] Run listening test for naturalness (Benchmark 2)
- [ ] Run transcription test for WER (Benchmark 3)
- [ ] Run 3-hour fatigue test (Benchmark 4)
- [ ] Run A/B comparison (Benchmark 5)

**Post-Benchmark:**
- [ ] Analyze results (latency, MOS, WER, fatigue)
- [ ] Compare Piper vs Coqui
- [ ] Make recommendation: GO / NO-GO / CONDITIONAL
- [ ] Document findings in benchmark report

---

## Expected Results (Hypothetical)

**Piper TTS (en_US-lessac-medium):**
- Latency (CPU): ~300ms (✅ meets threshold)
- Latency (GPU): ~150ms (✅ meets threshold)
- MOS: ~3.6 (✅ meets threshold)
- WER: ~4% (✅ meets threshold)
- 3-hour preference: ~60% (✅ meets threshold)
- **Verdict: RECOMMENDED**

**Coqui TTS (vits):**
- Latency (CPU): ~400ms (✅ meets threshold)
- Latency (GPU): ~200ms (✅ meets threshold)
- MOS: ~3.8 (✅ meets threshold)
- WER: ~3% (✅ meets threshold)
- 3-hour preference: ~65% (✅ meets threshold)
- **Verdict: RECOMMENDED (slightly better quality, slightly slower)**

**Decision:** Use **Coqui VITS** if GPU available (best quality), fallback to **Piper medium** if CPU-only (acceptable quality, faster).

---

## Deliverables

**Benchmark Report:**
- Latency results (CPU + GPU for each model)
- MOS scores (naturalness ratings)
- WER results (intelligibility)
- Fatigue analysis (3-hour session preference)
- Comparative analysis (Piper vs Coqui)
- Recommendation: Which system to use for M1 TTS integration?

**File:** `docs/analysis/RQ_VOICE_001_BENCHMARK_RESULTS.md`

---

## Status

**Current State:** PROTOCOL DEFINED / AWAITING HUMAN EXECUTION

**Cannot Execute:** Agent C has no TTS runtime environment

**Requires:**
- PM or human tester with target hardware
- Piper + Coqui TTS installed
- 5-10 D&D player listeners for subjective tests
- ~4-6 hours total benchmark time

**Next Step:** PM executes benchmarks, provides results to Agent C for analysis

---

## Document Governance

**Status:** R0 / BENCHMARK PROTOCOL / NON-BINDING
**Purpose:** Empirical TTS quality measurement
**Approval Required From:** PM (to execute benchmarks)
**Depends On:** Target hardware availability, TTS installation, listener recruitment
**Blocks:** M1 TTS integration decision (which system to use?)
**Future Work:** Execute benchmarks, analyze results, make GO/NO-GO recommendation
