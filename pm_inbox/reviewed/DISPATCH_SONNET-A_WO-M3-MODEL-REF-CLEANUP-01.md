# Instruction Packet: Sonnet-A

**Work Order:** WO-M3-MODEL-REF-CLEANUP-01 (Stale Model Reference Cleanup)
**Dispatched By:** Opus (Acting PM)
**Date:** 2026-02-11
**Priority:** 3 (low — mechanical cleanup, no architectural decisions)
**Deliverable Type:** File edits + completion report

---

## CONTEXT

R1 Technology Stack Validation (2026-02-11) replaced all R0 model selections. The model registry (`config/models.yaml`) and spark adapter tests (`tests/test_spark_adapter.py`) have already been updated. However, several governance and design documents still reference superseded models in their examples and test specifications.

These are **example values**, not strategic framing — but stale references cause confusion when agents read these docs for context.

---

## YOUR TASK

Find and replace stale model references in the documents listed below. This is mechanical find-and-replace work. Do NOT change any architectural language, strategic framing, or acceptance criteria logic — only update the model names/IDs used as examples.

### File 1: `pm_inbox/reviewed/M2_ACCEPTANCE_SPARK_SWAPPABILITY.md`

| Find | Replace With |
|------|-------------|
| Mistral 7B (and variants like "mistral-7b-instruct") | Qwen3 8B / qwen3-8b-instruct-4bit |
| Phi-2 / Phi-3 Mini (and variants) | Qwen3 4B / qwen3-4b-instruct-4bit |
| Mistral 14B (if present) | Qwen3 14B / qwen3-14b-instruct-4bit |

### File 2: `pm_inbox/reviewed/SPARK_SWAPPABLE_INVARIANT.md`

Same replacements as File 1.

### File 3: `pm_inbox/reviewed/M3_PREPARATION_REPORT.md`

| Find | Replace With |
|------|-------------|
| "Whisper" (referring to STT) | "faster-whisper small.en" |
| "Coqui" or "Coqui TTS" | "Kokoro" |
| "Piper" (if present as TTS) | "Kokoro" |
| "SD 1.5" or "Stable Diffusion 1.5" | "SDXL Lightning NF4" |
| "Mistral 7B" | "Qwen3 8B" |
| "MusicGen" (if present) | "ACE-Step" |

### File 4: `docs/design/SPARK_ADAPTER_ARCHITECTURE.md`

Verify all model examples use Qwen3 / Gemma3 family. Replace any remaining Mistral / Phi-2 / StableLM references. This file may have been partially updated during the R1 registry update — check before editing.

---

## RULES

1. **Only change model names/IDs in examples.** Do not change acceptance criteria logic, test structure, architectural descriptions, or strategic language.
2. **Preserve formatting.** Don't reformat tables, code blocks, or sections you didn't need to change.
3. **Add an R1 update note** at the bottom of each modified file:
   ```
   > **R1 Update (2026-02-11):** Model references updated to reflect R1 Technology Stack Validation selections. See `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md`.
   ```
4. **If a document has a version or date field**, update it.
5. **If you're unsure whether a reference is an example or strategic framing**, leave it and note it in your completion report.

---

## REFERENCES

| File | What It Contains |
|------|-----------------|
| `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` | R1 model selections (source of truth) |
| `config/models.yaml` | Current model registry (already updated) |
| `tests/test_spark_adapter.py` | Test file (already updated — use as reference for correct IDs) |

---

## DELIVERY

Place completion report in `pm_inbox/`:
- `SONNET-A_WO-M3-MODEL-REF-CLEANUP-01_completion.md`

Report should list:
- Each file modified
- Number of replacements made
- Any references you were unsure about and left unchanged

---

## STOP CONDITIONS

Stop and report if:
- A document uses model names in acceptance criteria logic (not just examples) — flag for PM review
- A document has a FROZEN status that might prohibit edits — flag for PM review
- You find model references in files NOT listed above — add them to your report but don't edit without asking

---

**END OF INSTRUCTION PACKET**
