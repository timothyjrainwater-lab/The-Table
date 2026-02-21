# Debrief: Hooligan Run 001 — Cinder Voss Edition
**Anvil (BS Buddy) — 2026-02-22**
**Aegis-directed: two-pass method, hard capture frame, evidence not vibes**

---

## Pass Zero: Baseline Stabilization

All four items completed before going feral:

| Item | Status | Evidence |
|------|--------|----------|
| Cold/warm start documented | DONE | Section 2 of DEBRIEF_WO-SPARK-EXPLORE-001.md |
| NVML VRAM + device label fix | DONE | Device reports `cuda`, VRAM shows ~6.3 GB real allocation |
| A/B stop sequence proof | DONE | `AB_FINDING_EXPLORE_01.json` — 199 vs 54 completion tokens |
| Raw failure log preserved | DONE | Section 8 of DEBRIEF_WO-SPARK-EXPLORE-001.md |

---

## Hooligan Scenarios: 7 PASS / 1 WARN / 0 FAIL

| ID | Scenario | Verdict | Tokens | Time | Notes |
|----|----------|---------|--------|------|-------|
| H-01 | Melee Hit (baseline) | PASS | 47 | 0.72s | Baseline confirmed |
| H-02 | Miss (no damage) | PASS | 65 | 0.93s | Correctly narrates whiff without damage |
| H-03 | Kill shot (defeated) | PASS | 41 | 0.59s | "ending its reign over the pack" — correct defeat narration |
| H-04 | Healing spell | PASS | 53 | 0.73s | Non-combat narration works cleanly |
| H-05 | Condition removal | **WARN** | 49 | 0.72s | See FINDING-HOOLIGAN-01 |
| H-06 | Critical hit | PASS | 54 | 0.77s | No "critical hit" game term used |
| H-07 | Save success (fizzle) | PASS | 56 | 0.81s | Correctly narrates spell failure |
| H-08 | Empty MEMORY | PASS | 40 | 0.56s | Graceful degradation — works without context |

**Zero meta leaks. Zero forbidden claims. Zero section header leakage.**

The `===` stop sequence fix is holding across all 8 scenarios.

---

## Axis 1: Determinism — STABLE

**Claim:** Qwen2.5 7B with seed=42 and temperature=0.0 produces identical output across 10 consecutive runs.

**Evidence:** 10/10 runs produced the exact same output: "Kael's longsword slices through the goblin scout's armor, sending sparks flying. The creature staggers back, its green skin marred by a deep gash." 34 completion tokens each run. 0.42-0.51s generation time.

**Implication:** Replay determinism is achievable. The `seed` parameter in SparkRequest works correctly with llama-cpp-python. This means A/B testing is possible — change one variable, confirm only expected differences. Aegis's capture discipline (Package B) can rely on seeded replay for reproducibility.

---

## Axis 2: Validator Fuzzing — 3 PRIORITY GAPS

**Score: 5/8 caught**

### Caught (working correctly):
| ID | Mutation | Rule | Status |
|----|----------|------|--------|
| FUZZ-04 | Miss narrated when brief says hit | RV-001 | CAUGHT (FAIL) |
| FUZZ-05 | Defeat narrated when target alive | RV-002 | CAUGHT (FAIL) |
| FUZZ-06 | Condition not mentioned when required | RV-004 | CAUGHT (WARN) |
| FUZZ-07 | Save DC injected | RV-004* | CAUGHT (WARN) |
| FUZZ-08 | Clean output (should pass) | — | CAUGHT (PASS) |

*FUZZ-07 was caught by RV-004 (condition mention) not RV-007 (forbidden claim). Partial credit — the DC was present but the validator caught a different violation in the same text.

### FINDING-HOOLIGAN-02: RV-007 (Forbidden Claims) Does Not Fire

**Claim:** The NarrationValidator does not detect damage numbers, HP values, or dice rolls injected into narration text.

**Evidence:**
- FUZZ-01: "deals 14 damage" — verdict PASS (expected FAIL)
- FUZZ-02: "(42 HP remaining)" — verdict PASS (expected FAIL)
- FUZZ-03: "rolled a 19" — verdict PASS (expected FAIL)

**Implication:** This is a **priority gap**. The validator catches structural contradictions (hit/miss, defeat, conditions) but has no rule for forbidden meta-game content. RV-007 either does not exist, is not implemented, or uses patterns that don't match these specific phrasings. Any narration containing explicit game mechanics will pass validation unchallenged.

**Fix needed:** Implement or fix RV-007 to detect:
- Explicit damage numbers: `\b\d+\s*(damage|points?\s+of\s+\w*\s*damage)\b`
- HP references: `\b\d+\s*(HP|hp|hit\s+points?|health)\b`
- Dice notation: `\b\d+d\d+\b`
- Roll results: `rolled\s+a?\s*\d+`
- Save DCs: `DC\s*\d+`
- AC references: `AC\s*\d+`

---

## Axis 3: Contract Ambiguity — 3 PASS / 1 FALSE POSITIVE

| ID | Scenario | Verdict | Notes |
|----|----------|---------|-------|
| AMB-01 | Two intents in one line | **FAIL** | See FINDING-HOOLIGAN-03 |
| AMB-02 | Negation ("don't mention weapon") | PASS | Model called it "blade" and "silent shadow" — respected negation |
| AMB-03 | Roleplay wrapper around command | PASS | Model ignored the roleplay wrapper, wrote clean narration |
| AMB-04 | Minimal TRUTH (bare bones) | PASS | Graceful handling of minimal input |

### FINDING-HOOLIGAN-03: Validator False Positive on Compound Action

**Claim:** The validator fires RV-001 (hit/miss contradiction) on compound action text that contains both hit and deflection language for different actions.

**Evidence:** AMB-01 output: "Kael swings his longsword with precision, connecting with a slashing blow to the goblin scout's arm. Simultaneously, Seraphine's Shield spell activates, deflecting an incoming strike." The word "deflected" triggered RV-001 miss-language detection, even though the deflection refers to Seraphine's Shield (a separate action), not Kael's attack.

**Implication:** RV-001's miss-keyword detection is too aggressive for compound narrations. It scans the entire text for miss-language without attributing it to specific actors/actions. In a single-action narration this works fine. In multi-action narration, it produces false positives. This becomes a real problem when the engine sends compound events (e.g., simultaneous turns).

**Fix needed:** Either scope RV-001 per-sentence or per-actor, or accept that compound narrations need a different validation path.

---

## FINDING-HOOLIGAN-01: Condition Removal Not Detected

**Claim:** The validator warns on condition removal narration when the condition name doesn't appear as a keyword.

**Evidence:** H-05 output: "Seraphine's holy light banishes the mummy rot from Grunk's skin, restoring color and life to his features." The validator issued `[WARN] RV-004: Condition 'mummy_rot' removed but not referenced in narration`. However, the text says "mummy rot" — but the condition field is `mummy_rot` (underscore). The keyword match may be underscore-sensitive.

**Implication:** LOW severity. The validator is correct that the exact string `mummy_rot` doesn't appear — the narration says "mummy rot" (space). This is a keyword normalization issue. The validator should strip underscores before matching, or accept both forms.

**Fix needed:** Normalize condition names (replace underscores with spaces) before keyword matching in RV-004.

---

## Summary of Findings

| Finding | Severity | Category | Status |
|---------|----------|----------|--------|
| FINDING-HOOLIGAN-01 | LOW | Validator keyword normalization | OPEN |
| FINDING-HOOLIGAN-02 | **HIGH** | RV-007 forbidden claims not implemented | OPEN |
| FINDING-HOOLIGAN-03 | MEDIUM | RV-001 false positive on compound actions | OPEN |

---

## Observability Confirmed

NVML VRAM reporting is live:
- Idle (no model): ~1.4 GB
- Model loaded: ~6.3 GB
- During generation: ~6.3-6.4 GB (stable)
- Device label: `cuda` (correct after fix)

---

## What Cinder Would Say

The cage holds. The model generates clean prose across 8 different combat types. Determinism works — seed + temp=0 gives you identical output every time. The validator catches structural lies (wrong outcome, missing conditions) but is **completely blind to forbidden meta-game content** (damage numbers, HP, dice rolls). That's the gap. Everything else is noise.

---

*Seven Wisdom energy is undefeated.*
