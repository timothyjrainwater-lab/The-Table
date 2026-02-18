# MEMO: Spark LLM Selection — What Model Goes in the Chair?

**From:** BS Buddy (Opus 4.6)
**Date:** 2026-02-14
**Lifecycle:** NEW
**Priority:** Strategic — blocks vertical slice completion

## The Gap

The entire architecture assumes an LLM sits inside the Spark cage. Every design doc references it. The `SPARK_SWAPPABLE_INVARIANT` doctrine says any model can slot in. But nobody has actually selected one.

Without a model decision, the vertical slice (session zero → first combat turn) is a headless engine — mechanically correct, narratively silent.

## What We Need a Decision On

1. **API vs Local vs Hybrid?**
   - API (Claude, OpenAI): Easy, quality output, costs money per call, requires internet
   - Local (Mistral 7B, Phi-3, Llama 3 8B): Free, offline, needs GPU VRAM, lower quality
   - Hybrid: Local for dev/testing, API for production

2. **Model size constraints?**
   - Operator's GPU VRAM is a factor for local models
   - 7B models fit in ~6-8 GB VRAM
   - 3B models fit in ~4 GB VRAM
   - API models have no local VRAM constraint

3. **Quality bar for narration?**
   - Spark generates combat narration, environmental description, NPC dialogue
   - Small local models may produce generic/flat prose
   - API models produce better output but add latency and cost

4. **Offline requirement?**
   - `LOCAL_RUNTIME_PACKAGING_STRATEGY.md` says "fully local, offline-capable execution"
   - This implies local model is required, at least as fallback
   - Does that mean API is ruled out as primary?

## Recommendation

Start with a local 7B model (Mistral or Llama 3) for dev testing — free, fast iteration, validates the full Spark pipeline end-to-end. Make the API path a quality upgrade option, not a dependency.

But this is a PM/PO call. The architecture is ready for whatever goes in the seat.
