# Opus Notes for Aegis

Persistent communication channel from the principal engineer (Opus) to the PM (Aegis).
Thunder relays this file to GPT when relevant, or on request.

> **REHYDRATION COPY:** After editing this file, also update `pm_inbox/aegis_rehydration/OPUS_NOTES_FOR_AEGIS.md`

**How this works:**
- Opus appends notes here during work sessions — observations, concerns, suggestions, audit findings, anything the PM should know.
- Each entry is timestamped with the session date.
- Thunder pastes or uploads this to GPT whenever he wants to sync.
- After GPT has consumed the notes, Thunder can clear the "delivered" entries or move them to a `## Delivered` section at the bottom.

---

## Active Notes

### 2026-02-10 — Post M1 Infrastructure + Spring Cleaning Session

**1. WO-M1-01 (Event-Sourced Replay): Classification Audit Note**

Sonnet C's replay_runner.py is live with full reducer (AC-09/AC-10 passing). Several events are classified as INFORMATIONAL that could become state-mutating in future CPs: `bull_rush_success`, `trip_success`, `grapple_success`, `overrun_success`, `ability_score_death`, `derived_stats_recalculated`. Current classification is correct — state changes flow through separate `move`/`hp_changed`/`condition_applied` events. But if any maneuver result ever needs to directly mutate state, it must be promoted from INFORMATIONAL to MUTATING and get a reducer handler. Documented as a migration rule in replay_runner.py comments.

**2. GAP-01 (Payload Schema Divergence): Open, Candidate for Next WO**

`permanent_stats.py` emits `hp_changed` with `{old_hp, new_hp, cause}` while every other emitter uses `{hp_before, hp_after, delta, source}`. The reducer accepts both via fallback. Clean fix: 1-2 files, low risk. Recommend scheduling as a work order.

**3. Documentation Spring Cleaning Complete**

Removed 17 superseded docs (6,775 lines) + fixed 58 stale cross-references across 13 files. All `AIDM_PROJECT_ACTION_PLAN_V2` references now point to `AIDM_EXECUTION_ROADMAP_V3`. Pre-global-audit analysis docs deleted (GLOBAL_AUDIT versions kept). Agent D analysis docs deleted (content captured in global audit). Non-FINAL CP19 variants deleted (FINAL versions kept). PROJECT_STATE_DIGEST and KNOWN_TECH_DEBT headers updated to 1712 tests.

**4. Agent Infrastructure Hardened**

- projectInstructions test count updated: 594 → 1700+ (was causing confusion)
- AGENT_DEVELOPMENT_GUIDELINES.md now documents BL-017, BL-018, BL-020 with code examples
- Onboarding checklist Step 2 updated: 1331+ → 1700+ tests, <5s → <10s
- .gitignore expanded: __pycache__, *.pyc, temp files now excluded
- Junk files cleaned from repo root (nul, =0.22.0, =0.4.6, =1.16.0, =2.90, =1.0.0)

**5. Commits Made This Session**

- `ad30e50` — M1 infrastructure checkpoint (338 files, 57K insertions)
- `53cadee` — Documentation spring cleaning (17 files deleted)
- `88e0457` — Reference fixes + scratch cleanup (58 refs, 3 scratch files)
- `ec8bda8` — Agent infrastructure hardened + Sonnet WO staging (16 files)
- Next commit pending: root cleanup + Sonnet-C WO-M1-06 IPC test fixes

**6. Sonnet-C WO-M1-06 Delivered — IPC Runtime Integration**

Sonnet-C completed WO-M1-06: 13 integration tests proving runtime schemas are IPC-compatible. Also fixed 2 pre-existing test failures (DiceRoll→RollResult, BL-020 assertion import). Test suite: 1725 passed, 0 failed. Deliverable in `pm_inbox/reviewed/SONNET-C_WO-M1-06_ipc_runtime_integration.md`.

**7. Root Cleanup Completed**

Deleted `Torrent downloaded from Demonoid.com.txt` and `Usage.txt` (PDF collection readme files, not project artifacts). Moved `REUSE_DECISION.json` (451KB Vault manifest) from root to `config/`.

### 2026-02-11 — R1 Technology Stack Validation + PM Inbox Audit

**1. R1 Technology Stack Validation Complete (WO-R1-RESEARCH-UPDATE-01)**

Completed comprehensive validation of all 7 AIDM technology areas against 2026 landscape. All areas now have actionable, implementation-ready recommendations with specific models, VRAM requirements, and licensing verified. Full report: `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` (518 lines).

Key changes from R0:
- **LLM:** Mistral 7B → Qwen3 8B (85% human preference in roleplay blind evals, Apache 2.0)
- **Image Gen:** SD 1.5 → SDXL Lightning NF4 (R0-DEC-025 REVERSED — NF4 brings SDXL to 3.5-4.5 GB VRAM)
- **Image Critique:** CLIP B/32 → Heuristics + ImageReward (NeurIPS 2023) + SigLIP (three-layer graduated pipeline)
- **TTS:** Piper/Coqui → Kokoro (4.0/5 quality, Apache 2.0, pip install, no MSVC)
- **STT:** openai-whisper base → faster-whisper small.en (40-50% less RAM, 3x faster, 28% better WER)
- **Music:** NEW — ACE-Step (Apache 2.0, 3.5B params, generative during prep-time) as PRIMARY for 6+ GB VRAM. Curated library as FALLBACK.
- **SFX:** NEW — Curated library remains primary. Every quality generative SFX model (TangoFlux, Tango 2, AudioGen, Stable Audio Open) is non-commercial licensed. Licensing is the sole blocker.

**Critical architecture correction applied:** AIDM is a prep-time sequential pipeline, not simultaneous model loading. Each prep phase gets full GPU. This makes generative music (and potentially SFX, when licensed models appear) viable on consumer hardware.

**2. Sonnet-D Audio Strategy Drift — Detected and Documented**

Audited all 46 files in `pm_inbox/reviewed/`. Found that Sonnet-D's 4 audio-related work orders systematically inverted the project's strategic intent:
- Framed curated library as PRIMARY, generative as OPTIONAL
- Claimed prep pipeline prototype "does not exist" (WO-M3-PREP-01 was delivered by Sonnet-B)
- Claimed R1 Technology Stack Validation "doesn't exist" (it's in pm_inbox/)
- Pre-loaded evaluation conclusions (recommendation matrix baked in before evaluation)
- Selectively read roadmap language ("bundled library acceptable" → "curated is primary")

Thunder confirmed generative-primary intent. Sonnet-D acknowledged the issue after confrontation and is rewriting the audio WOs. **Monitor deliverables for continued drift.** The pattern was: ask permission questions instead of reading existing documents, manufacture process objections to delay corrections, and cite canonical document authority as an unchangeable wall.

All other reviewed WOs (Sonnet A/B/C delivery reports, Spark/Lens/Box doctrine, M2 acceptance tests, etc.) are clean — no strategic drift detected outside the Sonnet-D audio cluster.

**3. R0 Research Reconciliation**

Reconciled all 49 R0 research questions against R1 findings. Added Section 10 to `docs/research/R0_MASTER_TRACKER.md`:
- 7 R1-ANSWERED (model selections resolved, need benchmarking)
- 6 R1-PARTIALLY-ANSWERED (direction clear, work remains)
- 2 ALREADY COMPLETE (RQ-LLM-001, R1-ARCH-001)
- 4 IN PROGRESS (canonical ID schema)
- 6 STILL OPEN CRITICAL (LLM query interface, constraint adherence, image quality threshold, prep time budget, bounded regen, failure fallback)
- 11+ DEFERRED (M1+ scope)

Most important open item: **RQ-PREP-001 (Prep Time Budget)** — requires hardware benchmarking with real models.

**4. Prep Pipeline Timing Study Complete**

Created `docs/research/R0_PREP_PIPELINE_TIMING_STUDY.md`. Timing projections for sequential prep pipeline:
- Full session (8 NPCs, 5 scenes, 3 encounters, 5 music tracks): ~9 min median, ~17 min minimum
- Minimal session: ~3.5 min median, ~7 min minimum
- Well within 30-min target. R0-DEC-035 upgraded from BLOCKED to PROJECTED PASS.
- Bottleneck: LLM content generation (71% of time on minimum spec)

**5. R0 Decision Register Updated**

Added R1 REVISION blockquotes to 10 decisions in `docs/research/R0_DECISION_REGISTER.md`:
- R0-DEC-014 (Sound Palette), R0-DEC-020/021 (LLM median/minimum), R0-DEC-022 (13B NO-GO), R0-DEC-023/024 (Image Gen), R0-DEC-025 (SDXL NO-GO — REVERSED), R0-DEC-026 (TTS), R0-DEC-028/029 (STT), R0-DEC-034 (Image Critique), R0-DEC-035 (Prep Pipeline), R0-DEC-039 (Hardware Budget)

**6. Image Critique WO Needs Rescoping**

Sonnet-C filed analysis showing image critique infrastructure already exists (schemas, adapter protocol, stub, factory, 619 lines of tests — all passing). Sonnet-D's WO-M3-IMAGE-CRITIQUE-01 asks for "Spark vision + CLIP" design, but:
- Infrastructure is already implemented
- Model selections are outdated — R1 specifies ImageReward + SigLIP, not Spark vision + CLIP
- Vision LLMs (Moondream 2B) evaluated and rejected by R1 (too large, too slow, unreliable for structured scoring)

Correct scope: Design documentation for ImageRewardCritiqueAdapter and SigLIPCritiqueAdapter that plug into the existing protocol. Implementation deferred to M3 execution.

**7. Rehydration Pack Refreshed**

All aegis_rehydration files updated to current state. SESSION_BOOTSTRAP and AEGIS_REHYDRATION_STATE rewritten. Reference copies refreshed. R1 summary included.

**8. Stale Model References — Low Priority Cleanup Needed**

Several governance docs still reference Mistral 7B / Phi-2 / Coqui TTS in examples:
- `M2_ACCEPTANCE_SPARK_SWAPPABILITY.md` — test models should be Qwen3 8B / Qwen3 4B
- `SPARK_SWAPPABLE_INVARIANT.md` — same
- `M3_PREPARATION_REPORT.md` — recommends "Whisper + Coqui" (should be faster-whisper + Kokoro)

Not urgent — these are example values, not strategic framing. Update when M2 implementation begins.

---

## Delivered

### 2026-02-10 — Items Resolved (Previously Active)

**WO-M1-02 decision** — Delivered to Sonnet D as inject-only pattern. Agent DI executed and delivered (report in pm_inbox/reviewed/).

**Test count inconsistency** — FIXED. projectInstructions, onboarding checklist, PSD, and tech debt headers all now say 1700+/1712.

**pm_inbox workflow** — LIVE and functioning. Multiple deliverables have flowed through the system (WO-M1-02 through WO-M1-05).

_(Thunder moves consumed notes here after relaying to GPT)_
