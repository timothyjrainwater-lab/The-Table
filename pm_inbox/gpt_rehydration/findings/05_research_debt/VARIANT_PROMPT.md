# GPT Instance 5 — Research Debt & Knowledge Gaps

Append this to the end of SYSTEM_PROMPT_FOR_GPT.md when running this instance.

---

## YOUR ANALYTICAL LENS: Unfinished Research & Missing Knowledge

Focus your analysis on **research that was started but never completed, questions that were asked but never answered, and knowledge gaps where the project is operating on assumptions instead of evidence.**

Specifically investigate:

1. **RQ-SPARK-001: Structured Fact Emission** — Three sub-dispatches (A/B/C) were delivered with raw findings. But no final synthesis exists. Sub-A covered schema and units. Sub-B covered prompting validation. Sub-C covered improvisation and NPCs. What would a proper synthesis document say? What conclusions should have been drawn? The Grammar Shield was built WITHOUT this research — what was lost by skipping the synthesis?

2. **RQ-NARR-001: Narrative Balance** — Same pattern: three sub-dispatches, no synthesis. Sub-A covered allowed output space. Sub-B covered templates and confirmation patterns. Sub-C covered tone evaluation unknowns. The DM Persona (WO-041) was "built empirically without RQ-NARR-001 guidance." What risks does that create? What would the synthesis have told us about tone control, output boundaries, and narrative quality evaluation?

3. **RQ-VOICE-001: Voice Design** — WO-051 is filed but NOT STARTED. The Chatterbox adapter exists but every character sounds the same. The research needs to cover: reference clip best practices, fantasy archetype recipes (dwarf, elf, villain, narrator), legal audio sourcing, post-processing pipeline, community knowledge. What existing research exists in the voice cloning community that could shortcut this?

4. **R0 GO Criteria — The Unresolved Three:**
   - **GO-1 (Canonical ID Schema):** Draft exists with 30 open sub-questions, 7 critical. What are those 7 critical questions? Why haven't they been answered? What's the actual design decision needed?
   - **GO-4 (Image Critique Pipeline):** Model selection resolved (heuristics + ImageReward + SigLIP). But no benchmarking done. What would the benchmark protocol look like? What F1/FPR/FNR targets are acceptable?
   - **GO-6 (MVP Scope Definition):** Partial, awaiting stakeholder approval. What IS the MVP? What's the minimum viable D&D session? 1 combat? 1 dungeon? Full session?

5. **RQ-PERF-001: Compute Budgeting** — Marked PARTIAL. Grammar Shield v1 is done, pytest determinism suite exists. But no real hardware benchmarks. The prep pipeline timing is projected, not measured. What specific benchmarks need to be run, on what hardware, with what workloads?

6. **Policy Gaps from RQ-LENS-001 Validation:**
   - GAP-POL-01: Cache invalidation strategy — no policy exists
   - GAP-POL-02: Entity rename propagation — no policy exists
   - GAP-POL-03: Deleted entity handling (soft delete vs tombstone vs cascade) — no decision
   - GAP-POL-04: Multilingual alias resolution — no policy exists

   These are documented but not resolved. What are the options for each? What do other systems (game engines, database systems, CMS platforms) do?

7. **Determinism Risk: DET-003** — Asset generation seeding is UNMITIGATED and marked CRITICAL. Generated images and audio are not deterministically seeded. Export/import produces different assets. Three options were listed (deterministic seeding, asset export, hybrid with hashing) but no decision was made. What's the right approach for a deterministic game engine?

8. **Lens Persistence Format** — Open question in V2 plan. SQLite vs append-only log vs hybrid. This affects WO-032 (NarrativeBrief) and WO-040 (Scene Management). What are the trade-offs? What do other event-sourced game engines use?

9. **Context Window Budget** — Open question in V2 plan. How to allocate tokens across NarrativeBrief, session memory, player model. No guidance exists. What do other LLM-integrated game systems do? What's the research on optimal context window allocation for conversational AI?

10. **Model Fallback Ladder** — Qwen3-8B → 4B → 0.5B. Exact quantization levels TBD. What quality benchmarks exist for Qwen3 at different sizes and quantization levels specifically for narrative generation? Has anyone in the community tested Qwen3 for D&D-style narration?

11. **Missing Research Tracks** — Were any research questions NEVER ASKED that should have been? Looking at the full project scope, what knowledge gaps exist that no RQ even covers? Think about: multi-session continuity, player modeling, difficulty adaptation, narrative coherence over long sessions, combat balance validation.

For each finding, classify as:
- **Abandoned research** — Started, findings exist, synthesis never done
- **Filed but not started** — WO or RQ exists on paper, zero execution
- **Unknown unknown** — Gap that no document even acknowledges exists
- **Decision debt** — Options were enumerated but no one chose
- **Community knowledge available** — The answer likely exists outside this project
