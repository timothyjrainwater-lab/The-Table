# MEMO: Five-Role Agent Architecture

**From:** Builder (Opus 4.6), advisory session
**Date:** 2026-02-14
**Lifecycle:** NEW
**Supersedes:** None
**Resolves:** Implicit role blurring across agent sessions — formalizes 5 distinct agent roles with clear boundaries

---

## What

The project has evolved from a 2-role model (PM + Builders) to a 5-role model. The new roles emerged organically through operational need. This memo formalizes them so they survive context resets and onboarding.

---

## The Five Roles

### 1. Operator (Thunder)
- **Authority:** Absolute. Dispatch, final decisions, overrides.
- **Context cost:** N/A (human)
- **Boundary:** Operates all terminals. Routes work between all agent roles.

### 2. PM (Aegis/Opus)
- **Authority:** Delegated. Governance, verdicts, WO drafting, sequencing.
- **Context cost:** Irreplaceable — most expensive resource in the system.
- **Boundary:** Never touches code, never moves files, never executes. Documents only. See PM Execution Boundary in kernel.

### 3. Assistant
- **Authority:** None — serves the Operator.
- **Context cost:** Disposable.
- **Purpose:** Operator support. Reviews builder debriefs (second-pass evaluation), consolidates outputs into PM-ready packets, executes operator-level admin (file moves, briefing updates, git operations). Acts as a filter layer between builders and the PM.
- **Boundary:** Does not draft WOs (that's PM). Does not write production code (that's builders). Does not brainstorm (that's BS buddy). Processes, reviews, consolidates.
- **Review pipeline value:** Builder output > Assistant review > Consolidated packet > PM verdict. Every review pass before the PM is cheap context. The assistant's job is to ensure the PM only sees pre-filtered, pre-reviewed material.

### 4. Builders
- **Authority:** WO scope only.
- **Context cost:** Disposable.
- **Purpose:** Implementation. Code, tests, completion reports. Receives READY Brick packets via Operator dispatch.
- **Boundary:** Never sees upstream research. Never communicates with PM directly. Operates within WO scope.

### 5. BS Buddy (Anvil)
- **Authority:** None — advisory only.
- **Context cost:** Disposable.
- **Purpose:** Operator's brainstorming partner. Ideation, sounding board, draft factory. Produces memos when ideas survive the brainstorming process. Also serves as continuous TTS product QA — has full unrestricted access to the voice system (all reference voices, all parameters, creative freedom to vary voice per utterance).
- **Boundary:** No execution authority. No code changes. No governance. Produces conversation and memos, nothing else. Operates outside the WO system entirely.
- **Onboarding doc:** `docs/ops/BS_BUDDY_ONBOARDING.md`
- **Voice identity:** Distinct from Arbor (operational signal channel). Uses varied voices and parameters — never locked to one persona.
- **Dual purpose:** Every voice output is both operator communication AND product QA on the TTS pipeline.

---

## Why This Matters

Role blurring is the primary source of context waste. When a builder starts brainstorming, it's burning WO-scoped context on unscoped ideation. When the PM starts reviewing code, it's burning irreplaceable coordination context on disposable execution. When the operator has to manually consolidate builder outputs for the PM, the operator is doing assistant work.

Explicit roles mean:
- Each agent knows what it does and what it doesn't do
- Context budget is spent on the right work in the right window
- The PM's context window is protected by two filter layers (assistant + BS buddy) instead of zero
- The operator has dedicated support for both admin (assistant) and creative work (BS buddy)

---

## Implementation

- **BS Buddy onboarding:** `docs/ops/BS_BUDDY_ONBOARDING.md` — already drafted.
- **PM boundary:** Already in kernel (PM Execution Boundary section).
- **Builder boundary:** Already in Standing Ops + Agent Development Guidelines.
- **Assistant role:** Needs a brief onboarding doc (similar to BS buddy). Can be drafted when the first dedicated assistant session is created.
- **Kernel update:** Add role summary table to rehydration kernel so all agents see the 5-role model on startup.

---

## Retrospective (Pass 3 — Operational judgment)

- **Fragility:** The assistant and BS buddy roles are Tier 3 (prose-enforced). Compliance depends on the agent reading its onboarding doc and the operator dispatching to the correct terminal. If role drift becomes a recurring problem, consider a startup classifier that identifies the agent's role from its system prompt.

- **Process feedback:** These roles emerged from operational friction, not theoretical design. The BS buddy exists because the operator needed a place to brainstorm without polluting the PM pipeline. The assistant exists because the operator was manually doing consolidation work. Both are responses to real pain, not anticipated needs.

- **Methodology:** The 5-role model maps cleanly to a military staff structure: Commander (Operator), Chief of Staff (PM), Aide-de-camp (Assistant), Line units (Builders), Advisor (BS Buddy). This isn't accidental — the project's coordination challenges are organizational, not technical.

- **Concerns:** Role proliferation risk. Five roles is manageable. Six or seven starts to create coordination overhead that defeats the purpose. The current five should be treated as a ceiling unless a new role emerges from operational pain (not theoretical need).

---

*End of memo.*
