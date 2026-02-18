# AI->AI ANSWER PACKET: Remaining Doctrine Holes — Formalized Decisions

**From:** Aegis (3rd-Party Governance / Audit), packaged by BS Buddy (Anvil)
**To:** PM (Execution Authority)
**Date:** 2026-02-18
**Lifecycle:** URGENT — PM INTAKE
**Subject:** Answers to remaining doctrine holes for memo formalization
**Source:** Operator + Aegis/GPT session, gap analysis with BS Buddy

---

## Purpose

Convert the remaining "holes" into concrete architectural decisions and minimal pass/fail gates so the PM can draft the next memo set without re-litigating.

## Scope Note (LOCKED)

- Single-operator local play.
- Multi-character control (up to 3 PCs under one operator) is in-scope.
- Networked multiplayer is out of scope for v1.

---

## 1) Campaign Input Layer (CampaignManifest + PDF Compile Contract)

**DECISION:**
- CampaignManifest is the ONLY supported intake point for prepared content (adventure module PDF, campaign notes, homebrew).
- PDFs are not "played directly." They are compiled into a structured manifest + provenance graph.

**CONTRACT:**
- Inputs: source artifacts (OCR text, user notes) with doc_id + page anchors.
- Outputs:
  - entity graph: locations, NPCs, factions, items, encounters, secrets, timelines
  - stable IDs for every node
  - provenance pointers back to doc_id + page/span
  - precision token set (locked-by-default) with unlock rules
  - synthesized-fillers namespace (explicitly tagged; not canon until promoted by operator consent)

**GATES:**
- CM-G1: same inputs + same pins + same seed => byte-identical CampaignManifest.
- CM-G2: every extracted claim has provenance pointer (doc_id + page/span or "synthesized").
- CM-G3: locked precision tokens never appear verbatim in player-facing outputs unless unlocked (Notebook/Rulebook/Recall).

---

## 2) Session Lifecycle (Save/Load/Cold-Boot/Resume)

**DECISION:**
- "Save" is an Oracle snapshot boundary + pointers to authoritative event log.
- "Load" is cold boot from snapshot + deterministic replay to the chosen boundary if required.

**CONTRACT:**
- Save bundle includes:
  - Oracle stores needed to reconstruct state (FactsLedger, StoryState, UnlockState, WorkingSet pointers)
  - pointer(s) to Box event log segment(s) and current cursor
  - pending interaction state (PENDING_ROLL, PENDING_CONSENT, PENDING_HANDOUT) if present
- Resume always rebuilds deterministically and never invents.

**GATES:**
- SL-G1: load(save(X)) produces byte-identical Oracle stores and identical digests.
- SL-G2: if replay is involved, replay produces identical event log bytes and final state digest.
- SL-G3: pending states resume without skipping required rituals (roll/consent/handout placement).

---

## 3) Worldgen Pipeline + Worldgen-to-Sessiongen Boundary

**DECISION:**
- Worldgen is a compile-before-play step that emits bound artifacts and commits initial Oracle state.
- Sessiongen is runtime beat/scene preparation that may generate new artifacts only at explicit moments, then binds them. No preview shopping.

**CONTRACT:**
- Worldgen triggers: CampaignManifest + seed + pinned model pack set.
- Worldgen outputs:
  - initial Oracle commit (FactsLedger/StoryState/UnlockState baseline)
  - compiled books/handouts/maps as artifacts
  - image/audio packs if enabled (bound by asset_id; consume-once pools where applicable)
- Sessiongen outputs:
  - next-beat preparation (WorkingSet updates, beat queue)
  - runtime artifact generation is allowed ONLY when (a) explicitly requested, or (b) a declared event requires it; then artifact is delivered as weighted physical arrival and bound (no silent replacement).

**GATES:**
- WG-G1: same inputs + pins => byte-identical worldgen outputs (Oracle baseline + artifact manifests).
- WG-G2: no previews and no pick-a-version menus; artifacts arrive as table objects and bind.
- WG-G3: runtime generation cannot overwrite existing bound canon-facing assets (no silent swap).

---

## 4) Lens Spec (WorkingSet -> PromptPack Compiler; Leak Prevention Engine)

**DECISION:**
- Lens is a deterministic compiler: Oracle WorkingSet + mask rules => PromptPacks (for Spark/Director) with strict visibility control.
- Lens does not invent facts; it selects, masks, cites, and formats.

**CONTRACT:**
- Inputs: WorkingSet bytes + mask_level/mask_matrix + policy pins.
- Outputs:
  - PromptPack: context blocks with citations to Oracle/provenance
  - "allowed-to-say" envelope (what categories are permitted; precision token constraints)
  - stable serialization (byte-equal across runs)

**GATES:**
- LENS-G1: same inputs + pins => byte-identical PromptPack.
- LENS-G2: mask enforcement: red-team tests prove locked tokens cannot leak via recap/narration.
- LENS-G3: every included fact is attributable to Oracle store entry or operator-promoted synthesis.

---

## 5) Director Spec (Small, Read-Only Beat Selector)

**DECISION:**
- Director is small and boring: it chooses pacing and next beat from existing Oracle content.
- It is read-only to Oracle and Lens-only for inputs.

**CONTRACT:**
- Inputs: DirectorPromptPack from Lens (never raw Oracle), current scene cursor, recent events.
- Outputs: beat selection and beat intent (what to render next), not canon writes.
- Forbidden: inventing new facts, promoting synthesis, writing to Oracle.

**GATES:**
- DIR-G1: Director outputs are references (handles/IDs), not new content claims.
- DIR-G2: any suggestion requiring new canon becomes a "proposal" requiring operator consent path, not an automatic write.
- DIR-G3: read-only enforced mechanically.

---

## 6) Companion Mode (Non-Authoritative Helper)

**DECISION:**
- Companion Mode is explicitly non-authoritative and non-spoiler.
- It is a helper for procedures, navigation, and note management with consent.

**ALLOWED:**
- open rulebook pages
- explain procedures (not hidden world state)
- manage notebook operations with EV consent chain
- help find previously unlocked information

**FORBIDDEN:**
- reveal locked precision tokens
- infer or disclose hidden module content
- override Box outcomes
- write canon without consent

**GATES:**
- CMODE-G1: Companion outputs are constrained to unlocked set + rulebook references.
- CMODE-G2: any request for locked info routes to: "check notebook/rulebook or roll recall" (no leak).

---

## 7) Teaching Nudges (Teach Without Tooltips)

**DECISION:**
- No tooltips/popovers/snippets remains absolute.
- Teaching is done via ritual routing and physical references.

**CONTRACT:**
- Nudge types:
  - route-to-rulebook: open to the relevant rule (no snippet)
  - route-to-ritual: remind Declare -> Point -> Confirm -> (Record with consent)
  - route-to-recall: offer recall roll instead of revealing exactness
- Delivery: spoken line + physical "?" stamp that opens book; no inline explanation overlays.

**GATES:**
- NUDGE-G1: nudges never include spoilers or locked exact strings.
- NUDGE-G2: nudges never bypass required player actions (roll/record/consent).

---

## 8) Distribution / Packaging (Local-First Ship Posture)

**DECISION:**
- Ship as a local bundle with pinned versions for code, schemas, and model packs.
- No telemetry. No cloud dependency.

**CONTRACT:**
- Installer/update mechanism must:
  - preserve determinism pins
  - preserve artifact stores and ledgers
  - never silently rewrite canon-facing assets
  - provide upgrade migrations that are reproducible

**GATES:**
- PKG-G1: same version + same pins => same behavior and same deterministic outputs.
- PKG-G2: upgrades are explicit, logged, and reversible (at minimum via backup/restore of stores).

---

## What the PM Needs to Do

These answers are decisions, not research. Turn them into six memos:

1. **CampaignManifest spec** — schema, intake rules, PDF compilation contract (Section 1)
2. **Session lifecycle spec** — save/load/cold-boot/resume, can embed in Oracle or standalone (Section 2)
3. **Worldgen pipeline + worldgen/sessiongen boundary spec** (Section 3)
4. **Lens memo** — WorkingSet to PromptPack, mask enforcement, determinism rules (Section 4)
5. **Director memo** — beat selection, pacing rules, read-only constraint (Section 5)
6. **Companion Mode + teaching nudges memo** — can be one combined spec (Sections 6 + 7)

Packaging (Section 8) can remain a lighter "ship posture" doc until closer to distribution.

---

*End of answer packet.*
