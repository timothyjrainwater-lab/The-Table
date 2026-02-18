# GPT Rehydration Packet — Upload Manifest

**Rebuilt:** 2026-02-18
**Purpose:** Curated file set for onboarding GPT (or any external LLM) to a ChatGPT Project with authoritative AIDM context. Upload files in tier order.

---

## How to Use

1. Create a new ChatGPT Project (or open the target one).
2. Upload **Tier 0** files first — these are the minimal truth set.
3. Upload **Tier 1** files next — reduces "why did we do this" churn.
4. Upload **Tier 2** files last — optional, for auditability and fast onboarding.
5. Paste the Rehydration Kernel (file 06) into the Project system prompt if supported.

---

## Tier 0 — Must Have (Minimal Truth Set)

| # | File | Purpose |
|---|------|---------|
| 1 | `01_GOLDEN_TICKET_V12.txt` | Constitutional law: subsystem contracts, hard bans, gate philosophy |
| 2 | `02_FINAL_DELIVERABLE.txt` | "How we ship" doctrine: progress definition, gates as progress |
| 3 | `03_ORACLE_MEMO_V52.txt` | Oracle contract: precision locks, canonical bytes, gates |
| 4 | `04_TABLE_UI_MEMO_V4.txt` | Table UI bans, slices, PENDING contract, declare-point-confirm grammar |
| 5 | `05_IMAGE_GEN_MEMO_V4.txt` | BULK vs HERO, pool lifecycle, Quality Director, binding persistence |
| 6 | `06_REHYDRATION_KERNEL_LATEST.md` | Single source of current commit, test counts, gates, build order, active queue |
| 7 | `07_PM_BRIEFING_CURRENT.md` | What is built, what is next, parked items, decision points |
| 8 | `08_BUILDER_FIELD_MANUAL.md` | Accumulated tradecraft that prevents repeat mistakes |
| 9 | `09_CURRENT_CANON.md` | Canonical product state and locked decisions outside GT |
| 10 | `10_PROJECT_STATE_DIGEST.md` | Project state snapshot: module inventory, test counts, architecture |

**Tier 0 alone gives ~85% of the context needed.**

---

## Tier 1 — Strongly Recommended (Keeps Drift Low)

| # | File | Purpose |
|---|------|---------|
| 11 | `11_DOCTRINE_UPGRADE_COVER_MEMO.md` | Sequencing and intent: what to read first in doctrine |
| 12 | `12_SURVEY_ORACLE_OVERLAP.md` | Maps doctrine to repo reality; prevents rebuilding what exists |
| 13 | `13_MEMO_SPARK_LLM_SELECTION.md` | Blocks BURST and voice decisions; avoids re-litigating model choices |
| 14 | `14_BURST_INTAKE_QUEUE.md` | BURST-001 thru 004: voice pipeline reliability spec (parked) |
| 15 | `15_DIRECTOR_SPEC_V0.txt` | Beat selection, pacing constraints, no backflow enforcement |
| 16 | `16_LENS_SPEC_V0.txt` | WorkingSet → PromptPack compiler contract, mask enforcement, determinism |
| 17 | `17_SESSION_LIFECYCLE_V0.txt` | Save/load/cold-boot/resume lifecycle spec |

**Tiers 0+1 covers ~95% of project context.**

---

## Tier 2 — Optional (Auditability + Fast Onboarding)

| # | File | Purpose |
|---|------|---------|
| 18 | `18_DEBRIEF_WO-UI-DRIFT-GUARD.md` | Most recent debrief: UI drift guard tests |
| 19 | `19_DEBRIEF_WO-UI-02.md` | Recent debrief: TableObject + Pick/Drag/Drop |
| 20 | `20_DEBRIEF_WO-UI-01.md` | Recent debrief: Table UI bootstrap + Slice 0 |
| 21 | `21_WO-UI-ZONE-AUTHORITY_DISPATCH.md` | Active dispatch: zones.json authority + frustum gate |
| 22 | `22_WO-UI-DRIFT-GUARD_DISPATCH.md` | Recent dispatch: UI drift guard tests |
| 23 | `23_WO-UI-02_DISPATCH.md` | Recent dispatch: TableObject base system |

---

## Files NOT Included (And Why)

| Item from Manifest | Reason |
|---|---|
| Gate registry / GATES_INDEX | No standalone file exists; gate counts live in PM_BRIEFING_CURRENT.md (file 07) and test files |
| UI client README | No `client/README` exists yet; client bootstrap is documented in WO-UI-01 debrief |
| License ledger | No LICENSE_LEDGER or ASSET_LICENSES file exists yet; audio asset licensing deferred until BURST-001 |
| BURST-001 standalone packet | No standalone BURST-001 spec exists; the BURST intake queue (file 14) covers the parked items |

---

## Key Architectural Concepts (Quick Reference)

- **Box**: Deterministic combat engine (melee, ranged, spells, conditions, terrain)
- **Lens**: Data membrane between Spark and Box (indexing, provenance, fact acquisition)
- **Spark**: LLM integration (narration, scene generation, voice characterization)
- **Oracle**: Persistence + determinism layer (FactsLedger, UnlockState, StoryState, WorkingSet, Compactions)
- **Director**: Beat selection + pacing (BeatIntent, NudgeDirective, DirectorPolicy)
- **Immersion**: Atmospheric layer (TTS, STT, image gen, audio mixer) — never mechanical authority
- **Event Sourcing**: All state changes flow through deterministic event log
- **Fail-Closed**: Invalid inputs blocked by validators, no silent fallbacks

## Current Gate Status

| Gate | Tests | Status |
|---|---|---|
| Gate A (Oracle Spine) | 22/22 | PASS |
| Gate B (WorkingSet) | 23/23 | PASS |
| Gate C (Compactions) | 24/24 | PASS |
| Gate D (Director Phase 1) | 18/18 | PASS |
| Gate E (Director Phase 2) | 14/14 | PASS |
| Gate F (UI Phase 1) | 10/10 | PASS |
| Gate G (UI Phase 2 + Drift) | 13/13 | PASS |
| No-backflow | 1/1 | PASS |
| **Total gate tests** | **125** | **ALL PASS** |
