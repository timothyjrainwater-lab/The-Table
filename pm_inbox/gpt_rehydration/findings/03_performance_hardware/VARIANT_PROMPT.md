# GPT Instance 3 — Performance, Hardware & VRAM

Append this to the end of SYSTEM_PROMPT_FOR_GPT.md when running this instance.

---

## YOUR ANALYTICAL LENS: Performance, Hardware & VRAM Feasibility

Focus your analysis on **runtime performance, VRAM budget management, latency constraints, and hardware feasibility assumptions that haven't been empirically validated.**

Specifically investigate:

1. **VRAM Budget — The Core Constraint** — RTX 3080 Ti has 12GB VRAM. The plan says Spark (Qwen3-8B) + SDXL cannot coexist. But what are the actual numbers? Qwen3-8B Q4_K_M is ~5GB. SDXL Lightning NF4 is ~4GB. Chatterbox TTS is ~1-2GB. Whisper small.en runs on CPU. Can Spark + Chatterbox coexist? What about Spark + SDXL + Chatterbox during a scene where narration needs voice AND an image? What's the model swap latency?

2. **Latency Budget Per Turn** — The plan specifies: Box query <50ms p95, Lens query <20ms p95, full action resolution <3s p95, LLM narration <3s p95, template fallback <500ms p95. Are these measured or aspirational? The Box benchmarks exist (5.08ms p95). But LLM + TTS + STT latency is unmeasured. What's the realistic end-to-end latency for: voice in → STT → intent parse → Box resolve → STP → NarrativeBrief → Spark narrate → TTS speak?

3. **Chatterbox TTS Latency** — The adapter has two tiers: Turbo (sub-1s for short lines) and Original (3-5s for emotional narration). These were benchmarked. But what happens under sustained load? 10 combat turns back-to-back? Does GPU memory fragment? Does the model need reloading?

4. **STT Latency** — faster-whisper small.en runs on CPU. What's the transcription latency for a typical player utterance (3-10 seconds of speech)? Does it block the main thread? Is there a streaming mode that could start processing before the player finishes speaking?

5. **Model Loading/Unloading** — The session orchestrator (WO-039) must manage model lifecycles. Loading Qwen3-8B takes how long? Loading SDXL takes how long? If the player asks for a character portrait mid-combat, should the system unload Spark, load SDXL, generate, unload SDXL, reload Spark? What's that round-trip cost?

6. **Quantization Trade-offs** — The plan mentions Qwen3-8B → 4B → 0.5B fallback ladder. What quantization levels for each? Q4_K_M? Q5_K_M? Q8_0? What's the quality delta between quantization levels for D&D narration specifically? Has anyone benchmarked D&D narration quality across quant levels?

7. **Context Window Pressure** — Qwen3-8B has an 8K-32K context window depending on variant. A NarrativeBrief needs token budget for: system prompt (~200 tokens), recent events (~500 tokens), session memory (~1000 tokens), player model (~200 tokens), actual prompt (~200 tokens). That's ~2100 tokens input. How much context is actually available for the response? What happens as a session progresses and memory accumulates?

8. **Disk I/O** — Reference audio clips for Chatterbox voice cloning are read from disk every synthesis call. Image generation writes to disk. Event logs are append-only. Under sustained play, what's the I/O profile? Is there SSD contention?

9. **Prep Phase Timing** — Projected at ~9 minutes median spec, ~17 minutes minimum spec. But this projection is based on estimates, not measured. What are the actual timings with Qwen3-8B GGUF + SDXL Lightning NF4 running on the RTX 3080 Ti?

10. **Thermal Throttling** — Sustained GPU load from TTS + LLM inference + occasional image gen. Does the RTX 3080 Ti throttle under this workload? What's the thermal profile during a 2-hour play session?

11. **Memory Leak Risk** — PyTorch + llama-cpp-python + diffusers all managing GPU memory independently. Are there known memory leak patterns when loading/unloading models repeatedly? Does VRAM fragmentation accumulate over a session?

For each finding, classify as:
- **Unmeasured assumption** — A number is cited but never benchmarked
- **Budget conflict** — Multiple systems compete for the same resource
- **Scaling risk** — Works for small scenarios but may break at scale
- **Missing benchmark** — No data exists to validate the claim
