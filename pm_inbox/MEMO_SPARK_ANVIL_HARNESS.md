# MEMO: Anvil-as-Spark Integration Harness

**From:** Anvil (BS Buddy seat)
**To:** Slate (PM)
**Date:** 2026-02-19 22:40 CST
**Classification:** OPS-ARCHITECTURE / INTEGRATION-TESTING
**Lifecycle:** NEW
**Source:** Thunder directive, live session 2026-02-19

---

## Context

Thunder identified that Anvil (Claude, via API) can occupy the Spark LLM seat during development and integration testing. The Spark cage is LLM-agnostic by design — it accepts a PromptPack and returns narration text. The contract doesn't care whether the backend is Qwen2.5 7B (local, production) or Claude (API, development/testing).

This creates a bidirectional integration test harness that solves three open problems simultaneously.

---

## The Pattern: Anvil in the Spark Seat

### Forward Testing (Pipeline Validation)

Standard flow with Anvil as the narration LLM:

```
Mic → STT (Whisper) → stt_cleanup → IntentBridge.parse()
→ Box.execute_turn() → NarrativeBrief → Anvil (Claude API)
→ EmotionRouter → TTS (Chatterbox/Kokoro) → Speaker
```

**What this tests:** Data flows correctly through every junction. STT produces clean text. Intent bridge parses correctly. Engine resolves correctly. NarrativeBrief delivers correct structured input. TTS receives well-formed narration. Voice routing maps to correct persona/register.

### Reverse Testing (Doctrine-Aware Audit)

Anvil is not just a narrator — Anvil holds the full doctrine context (GT v12, all 10 doctrine files, all contracts, all gate definitions, PHB mechanics knowledge). While narrating, Anvil simultaneously:

1. **Validates engine output** — checks whether mechanical results match D&D 3.5 rules (e.g., "this fireball should have hit 4 targets but the brief shows 3")
2. **Audits NarrativeBrief integrity** — checks whether the brief correctly represents what the engine resolved
3. **Verifies line type compliance** — generates narration using all 7 CLI Grammar line types (TURN, RESULT, ALERT, NARRATION, PROMPT, SYSTEM, DETAIL) and verifies voice routing
4. **Tests unknown handling** — deliberately generates edge-case inputs to exercise the Unknown Handling Contract

### Adversarial Testing (Hooligan from Inside)

Anvil can also generate adversarial player input from inside the Spark seat:

- Feed edge-case commands through the intent bridge: "I grapple the fireball," "I ready an action to delay," "I cast Cure Light Wounds on the undead"
- Simulate multi-speaker input patterns
- Test every failure class in the Unknown Handling Contract (T-UNKNOWN through T-BLEED)
- Exercise the clarification budget and STOPLIGHT system

---

## Three Open Problems Solved

| Problem | Current Status | How This Solves It |
|---|---|---|
| **BURST-001 integration testing** | Pipeline pieces exist in isolation; no end-to-end test without Qwen wiring | Anvil in Spark seat proves the pipeline end-to-end before Qwen integration WO |
| **Holdout scenario suite** (MEMO_DARK_FACTORY_PATTERNS) | Identified as gap; candidate WO `WO-HOLDOUT-SCENARIOS-001` | Anvil is a doctrine-aware evaluator the builder can't optimize against — holdout by nature, not by file location |
| **Hooligan protocol expansion** | Current hooligan tests are static scenarios in smoke suite | Anvil generates adversarial input dynamically from inside the loop, testing every junction in the chain |

---

## Tradeoffs: Anvil (Dev/Test) vs Qwen (Production)

| Dimension | Anvil (Claude API) | Qwen2.5 7B (Local) |
|---|---|---|
| Narration quality | High — full doctrine context, any genre | Lower — 7B parameter model |
| Mechanical audit | Yes — knows PHB, contracts, gates | No — narrates only |
| Offline capable | No — API dependency | Yes — K5 compliant |
| Cost per call | API token cost | Free after model download |
| Latency | API round trip | Local inference (~2.7s load) |
| PRS-01 P5 compliance | Fails (requires network) | Passes (offline guarantee) |

**Summary:** Anvil for development, testing, and playing. Qwen for production distribution. Same interface, same gates, different backend. Config change, not code change.

---

## The Game IS the Test

Every D&D session played with Anvil in the Spark seat is simultaneously:
- A playtest of the game experience
- An integration test of the full pipeline
- A doctrine compliance audit of engine output
- An adversarial test of edge-case handling

The operator (Thunder) plays D&D. The system gets tested. Both happen in the same session. Development cost = play cost. No separate test budget.

---

## Implementation Requirements

1. **Spark cage adapter pattern** — must accept any LLM that implements the narration protocol. Swapping between Anvil (API) and Qwen (local) should be a config change in `models.yaml` or equivalent.
2. **Claude API adapter** — thin wrapper that formats PromptPack as Claude API input and returns narration text. Mirrors the llama-cpp-python adapter that Qwen uses.
3. **Audit sidecar** — when Anvil is in the Spark seat, a secondary output channel captures mechanical audit findings (rule violations, brief integrity issues) separately from narration output. The narration goes to TTS. The audit goes to a log.
4. **Session orchestrator wiring** — the turn loop must be complete: STT → intent → engine → brief → Spark → TTS. Currently each piece exists but the orchestrator doesn't chain them end-to-end.

---

## Candidate WO

**WO-SPARK-ANVIL-HARNESS-001**

**Scope:** Build the Claude API adapter for the Spark cage + audit sidecar output channel. Requires session orchestrator to be minimally wired (may depend on BURST-001 tier progress).

**Priority:** Medium-high. Unblocks integration testing for the entire pipeline without waiting for Qwen wiring. Also unblocks the first playable D&D session.

**Gate alignment:**
- Wisdom #3: What you cannot replay, you cannot trust. (Anvil audit makes engine output replayable and verifiable.)
- Wisdom #4: Tests are contracts with teeth. (Anvil in Spark seat IS a test with teeth.)
- Wisdom #6: Separate narration from mechanics. (Narration goes to TTS; audit goes to log. Clean split.)
- GT v12 K2: ANY GENRE. SAME TRUTH. Skin is compiled onto deterministic muscle. (LLM swap proves skin independence.)

---

## PM Action

1. **READ** this memo.
2. **Evaluate** WO slot for `WO-SPARK-ANVIL-HARNESS-001` in the build order. Could run parallel to BURST-001 Tier 1.3+ or after Tier 1 spec freeze completes.
3. **Note** dependency on session orchestrator wiring (partially built, needs turn loop completion).
4. **ARCHIVE** after review.

---

*Seven Wisdoms, no regret.*
