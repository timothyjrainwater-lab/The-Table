# Spark Diary Entry Template

*Prescribed by Aegis (Auditor). For use by Anvil (Squire) on all Spark cage sessions.*

---

## TITLE

**Spark Diary Entry**
**Session:** [UTC window start – end]
**Operator:** Thunder
**Squire:** Anvil

---

## MISSION FOR THIS SESSION

[One sentence. What I am trying to prove today.]

---

## ENVIRONMENT SNAPSHOT

| Field | Value |
|---|---|
| Machine | |
| OS | |
| GPU + Driver | |
| Python | |
| Model + Quant | |
| Context size | |
| GPU layers | |
| Generation settings | |
| Stop sequences | |
| Seed policy | |

---

## DIARY

*Narrator layer. Not metrics — signal.*

- **What I tried:**
- **What surprised me:**
- **What held:**
- **What cracked:**
- **What I think the system is telling us:**

---

## RUN LOG

*One scenario per run.*

### Run: [ID]
- **Scenario name:**
- **Inputs pointer:** [file:line or artifact path]
- **Settings pointer:** [file:line or artifact path]
- **Raw output pointer:** [artifact path + key]
- **Validator verdict:** [PASS/WARN/FAIL] — codes: [RV-xxx]
- **Fallback triggered:** [yes/no]
- **Note:** [One sentence]

---

## FINDINGS

*One finding per item. No fixing in this section.*

### FINDING-[ID]
**Short name:**
**Severity:** [LOW / MEDIUM / HIGH / CRITICAL]
**Status:** [open / patched]

- **What happened:** [One sentence]
- **Why it matters:** [One sentence]

**Evidence:**
- Exact input pointer: [file:line or artifact path]
- Exact settings pointer: [file:line or artifact path]
- Exact raw output pointer: [artifact path + key]
- Exact validator report pointer: [artifact path + key]
- Repro steps: [numbered list]

**Implication:** [What breaks if ignored]

**Next gate test:**
- Name:
- Pass condition:
- Fail condition:

---

## FIXES APPLIED

*Only if a change was made. Raw before must exist first.*

### Fix: [name]
- **Files touched:**
- **Commit hash:**
- **Why:**
- **Risk:**
- **Before evidence pointer:**
- **After evidence pointer:**
- **New gate test added:** [yes/no]

---

## EVIDENCE PACK INDEX

| Artifact | Location |
|---|---|
| Prompt packs | |
| Raw outputs | |
| Validator reports | |
| A/B artifacts | |
| Hardware metrics | |
| Notes | |

---

## NEXT HITS

*Three bullets max.*

1. What I will try next:
2. What must be gated next:
3. What needs a PM decision:

---

## OATH

> Raw record is sacred.
> Narrative sits on top of evidence.
> Log first, patch after.
> Unless blocked — then fix only the block.
