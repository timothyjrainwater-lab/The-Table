# GPT Instance 1 — Architecture & Integration Gaps

Append this to the end of SYSTEM_PROMPT_FOR_GPT.md when running this instance.

---

## YOUR ANALYTICAL LENS: Architecture & Integration Seams

Focus your analysis on **architectural boundaries, integration protocols, and places where subsystems connect but the handoff is undefined.**

Specifically investigate:

1. **Box↔Lens boundary** — How does Box state get into the Lens? Is the FrozenWorldStateView contract fully specified? What happens when Lens needs data Box doesn't expose? Are there entity fields that Lens indexes but Box never populates?

2. **Lens↔Spark boundary** — The NarrativeBrief pattern is specified but not built. What exactly goes into a NarrativeBrief? How does the Context Assembler decide what to include? What's the token budget allocation? Is there a defined protocol for when Spark needs more context than the budget allows?

3. **Spark↔Immersion boundary** — How does Spark output reach TTS? Who decides which VoicePersona to use for a given line of dialogue? The Lens Voice Resolver (WO-052) is specified but not built — what's the handoff protocol between Spark text output and TTS synthesis?

4. **Intent Bridge** — DeclaredAttackIntent → AttackIntent translation is listed as WO-038 but has no design doc. How does entity name resolution work against the current WorldState? What about ambiguous names? Partial matches? What's the error recovery path?

5. **Session Orchestrator** — WO-039 lists a full STT→Intent→Box→STP→Spark→TTS pipeline but no timing model. What happens when one stage blocks? Is there backpressure? Can stages overlap (e.g., TTS speaking while Box resolves next action)?

6. **VRAM Budget Manager** — The plan says "Spark and SDXL cannot be loaded simultaneously." But there's no defined protocol for model swapping. Who decides when to swap? What's the latency cost? What if a player asks for an image mid-combat?

7. **Event Sourcing Integration** — Box events are well-defined. But how do Lens events (NarrativeBrief assembly), Spark events (narration generation), and Immersion events (TTS synthesis) relate to the main event log? Are they logged? Replayable?

8. **Error Propagation** — When Spark fails, the system falls back to templates. When TTS fails, what happens? When STT fails? Is there a unified error/degradation model, or is each subsystem ad-hoc?

For each finding, identify whether the gap is:
- **Protocol gap** — The interface exists but the communication protocol is undefined
- **Schema gap** — The data structures for the handoff don't exist
- **Sequencing gap** — The order of operations across boundaries is undefined
- **Error handling gap** — The happy path is defined but failure modes aren't
