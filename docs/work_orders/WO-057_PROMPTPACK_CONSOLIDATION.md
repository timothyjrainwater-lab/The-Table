# WO-057: PromptPack Consolidation (GAP-007 Resolution)

**Status:** SPEC COMPLETE — Ready for Implementation
**Author:** Opus (PM)
**Date:** 2026-02-12
**Prerequisites:** WO-032 (ContextAssembler), WO-041 (DMPersona), WO-045B (PromptPack schema), WO-046B (NarrativeBrief)
**Resolves:** GAP-007 (dual prompt assembly paths)

---

## 1. Problem Statement

Two independent prompt assembly paths exist for Spark narration:

**PATH 1 — GuardedNarrationService._build_llm_prompt()** ([guarded_narration_service.py:622-666](aidm/narration/guarded_narration_service.py#L622-L666))
- Assembles a plain string prompt from NarrationRequest
- Includes: narration token, engine events, last 3 session facts
- **MISSING**: actor/target names, outcome summary, severity, weapon, damage type, condition, tone/persona, output contract, visible gear
- Origin: M1/M2 era, predates ContextAssembler and NarrativeBrief

**PATH 2 — ContextAssembler.assemble()** ([context_assembler.py:41-102](aidm/lens/context_assembler.py#L41-L102))
- Assembles a token-budgeted string from NarrativeBrief + session history
- Includes: current brief (outcome, weapon, damage, condition, severity), scene description, recent narrations, session history
- **MISSING**: narration token, task instructions, forbidden content, tone/persona, output contract
- Used by SessionOrchestrator → DMPersona.build_system_prompt()

**PATH 3 (emergent) — DMPersona.build_system_prompt()** ([dm_persona.py:81-136](aidm/spark/dm_persona.py#L81-L136))
- Receives ContextAssembler output + NarrativeBrief
- Adds: base persona, tone modifiers, action context, NPC hints
- **MISSING**: output contract, forbidden content list, schema version

**PromptPack** ([prompt_pack.py:143-330](aidm/schemas/prompt_pack.py#L143-L330))
- Designed as the unification target (AD-002, GAP-002)
- Five channels: Truth, Memory, Task, Style, Contract
- Deterministic serialization, versioned, sectioned
- **Currently unused in the actual narration pipeline**

The result: Spark receives different information depending on which code path is active, and PromptPack — the canonical wire protocol — is never actually used to build prompts.

---

## 2. Design

### 2.1 New Component: PromptPackBuilder

A new class in `aidm/lens/prompt_pack_builder.py` that replaces both PATH 1 and PATH 2 with a single PromptPack-based assembly.

**Inputs:**
- `NarrativeBrief` (from WO-046B event→brief assembly)
- `session_history: List[NarrativeBrief]` (previous briefs for memory)
- `session_facts: List[str]` (from FrozenMemorySnapshot)
- `style_config: Optional[StyleConfig]` (tone parameters, defaults to moderate)

**Output:**
- `PromptPack` (frozen, deterministic, five-channel)

**Assembly logic:**
1. **TruthChannel**: Populated directly from NarrativeBrief fields (action_type, actor_name, target_name, outcome_summary, severity, weapon_name, damage_type, condition_applied, target_defeated, scene_description, visible_gear)
2. **MemoryChannel**: previous_narrations from NarrativeBrief.previous_narrations, session_facts from FrozenMemorySnapshot, token budget enforced
3. **TaskChannel**: task_type=TASK_NARRATION, sentence bounds, forbidden content (mechanical numbers)
4. **StyleChannel**: From style_config or defaults
5. **OutputContract**: max_length_chars, required_provenance, prose format

### 2.2 Integration Points

**GuardedNarrationService changes:**
- `_build_llm_prompt(request)` replaced by `_build_prompt_pack(brief, session_facts)` which delegates to PromptPackBuilder
- NarrationRequest gains an optional `narrative_brief: Optional[NarrativeBrief]` field
- When narrative_brief is present, use PromptPack path. When absent (legacy), fall back to template narration.
- `_build_llm_prompt()` marked deprecated, not deleted (preserves backward compatibility during transition)

**SessionOrchestrator changes:**
- Currently builds ContextAssembler output and passes to DMPersona
- Updated to build PromptPack instead
- PromptPack.serialize() replaces the ContextAssembler output + DMPersona.build_system_prompt() combination
- DMPersona integration: StyleChannel carries the persona parameters that DMPersona currently injects

**ContextAssembler:**
- Not deleted. Its token budget logic is reused inside PromptPackBuilder for MemoryChannel truncation.
- ContextAssembler.assemble() remains available but is no longer called from the main narration pipeline.

### 2.3 What Does NOT Change

- PromptPack schema (prompt_pack.py) — no schema changes
- NarrativeBrief schema — no changes
- GrammarShield — continues to post-process Spark output
- Template fallback path — still works when no LLM available
- Kill switches — unchanged

---

## 3. Test Plan

### 3.1 PromptPackBuilder Unit Tests

| Test | Assertion |
|------|-----------|
| Build from minimal NarrativeBrief | TruthChannel populated, MemoryChannel empty, defaults for Task/Style/Contract |
| Build from full NarrativeBrief | All TruthChannel fields populated including visible_gear |
| Memory channel truncation | previous_narrations truncated to token budget |
| Session facts inclusion | session_facts from snapshot appear in MemoryChannel |
| Determinism | Same inputs → same PromptPack.serialize() output |
| Style config override | Custom StyleChannel overrides defaults |
| Forbidden content present | TaskChannel.forbidden_content includes mechanical numbers |

### 3.2 Integration Tests

| Test | Assertion |
|------|-----------|
| GuardedNarrationService uses PromptPack | When narrative_brief present, serialize() output used as prompt |
| SessionOrchestrator builds PromptPack | Orchestrator constructs PromptPack, not ContextAssembler string |
| End-to-end narration with PromptPack | Full pipeline produces narration via PromptPack path |
| Legacy path still works | When narrative_brief absent, template fallback still fires |

### 3.3 Regression Tests

- All existing tests in test_context_assembler.py continue passing (ContextAssembler unchanged)
- All existing tests in test_guarded_narration_service.py continue passing (legacy path preserved)
- All existing tests in test_prompt_pack.py continue passing (schema unchanged)
- All existing tests in test_session_orchestrator.py continue passing

---

## 4. Files Touched

| File | Change |
|------|--------|
| `aidm/lens/prompt_pack_builder.py` | **NEW** — PromptPackBuilder class |
| `aidm/narration/guarded_narration_service.py` | Add `_build_prompt_pack()`, update `_generate_llm_narration*()` to use PromptPack when available |
| `aidm/runtime/session_orchestrator.py` | Build PromptPack instead of ContextAssembler string, pass to GuardedNarrationService |
| `aidm/schemas/narration.py` | Add optional `narrative_brief` field to NarrationRequest |
| `tests/test_prompt_pack_builder.py` | **NEW** — PromptPackBuilder unit tests |
| `tests/test_session_orchestrator.py` | Update integration tests for PromptPack path |

---

## 5. Boundary Laws

- BL-003 enforced: `aidm/lens/prompt_pack_builder.py` imports from `aidm.lens` and `aidm.schemas` only, never from `aidm.core`
- PromptPackBuilder lives in Lens (it assembles context for Spark)
- No new dependencies introduced

---

## 6. Success Criteria

- [ ] Single prompt assembly path for all LLM narration calls
- [ ] PromptPack.serialize() is the canonical prompt sent to Spark
- [ ] All five channels populated from existing data sources
- [ ] Token budget enforcement on MemoryChannel
- [ ] Deterministic: same inputs → same prompt bytes
- [ ] All existing tests pass (0 regressions)
- [ ] New tests cover builder and integration
- [ ] GAP-007 entry in SEAM_PROTOCOL_ANALYSIS updated to RESOLVED
