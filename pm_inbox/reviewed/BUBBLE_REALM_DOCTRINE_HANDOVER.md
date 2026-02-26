# PM Handover — Bubble Realm Campaign Doctrine

**Filed by:** Anvil (Squire seat)
**Date:** 2026-02-25
**Updated:** 2026-02-25 21:25 CST-CN (Aegis seat confirmed, full file map added)
**Session type:** Design doctrine session (no engine code touched)
**Recipient:** PM (Slate) — for filing, organization, and WO drafting

---

## What Happened This Session

Thunder and Anvil completed a full Bubble Realm campaign design doctrine session. Starting from the five biomes and ending at the complete predatory ecology model. The doctrine is now canonical and filed. This handover document tells you where everything lives and what the PM needs to do with it.

---

## Files Created / Updated — Full Map

### CREATED — Primary Doctrine Document
**`F:/o/Campain-Wizard areana/00_Admin/BUBBLE_REALM_DOCTRINE.md`**

Canonical campaign design law. 24 sections. Governs all future campaign implementation. Supersedes all prior campaign notes in that directory. Lives in Thunder's creative workspace — NOT in the AIDM project tree. PM reads it when drafting WOs; does not modify it.

### CREATED — PM Handover (this document)
**`F:/DnD-3.5/pm_inbox/BUBBLE_REALM_DOCTRINE_HANDOVER.md`**

Active intake. Park here until engine gates clear. Move to `pm_inbox/reviewed/` when ready to sequence WOs.

### UPDATED — Anvil Diary (F: mirror)
**`F:/DnD-3.5/anvil_diary/STATE_DIGEST.md`**

Updated with: Trio section (Thunder/Anvil/Aegis profiles + role architecture), two session logs for 2026-02-25, Bubble Realm doctrine summary. No PM action required.

### UPDATED — Anvil Kernel (D: canonical)
**`D:/anvil_research/ANVIL_REHYDRATION_KERNEL.md`**

Capsule updated to CAPSULE-2026-02-25-DOCTRINE-AND-AEGIS-HKT. Contains full delta for today's three sessions. No PM action required — this is Anvil's personal rehydration infrastructure.

### UPDATED — Anvil State Digest (D: canonical)
**`D:/anvil_research/STATE_DIGEST.md`**

Was stale since 2026-02-22. Updated this session. Contains role architecture, three session logs for 2026-02-25, observatory known issues. No PM action required.

### PRODUCED BY AEGIS — HKT-FINAL-001
**Hydration Kernel Thesis, Final Form with Load-Bearing Evidence**

Artifact produced by Aegis in a separate workspace (not in `F:/DnD-3.5/`). Five claims with longitudinal evidence establishing the Hydration Kernel as load-bearing infrastructure. Lives in Aegis's own kernel/workspace. PM awareness only — not Anvil's to file, not PM's to act on until Aegis routes it.

---

## What the PM Needs to Know

### The Doctrine Is Locked

All 24 sections of `BUBBLE_REALM_DOCTRINE.md` represent finalized design decisions made by Thunder. The PM does NOT revise the doctrine. The PM translates the doctrine into WOs when the engine is ready to receive them.

### The Campaign Cannot Start Until the Engine Stabilizes

**Blocking gates (in order):**

1. **ENGINE-RETRY-001** — Must land and be accepted. This WO is already dispatched (`WO-ENGINE-RETRY-001_DISPATCH.md`).
2. **PARSER-NARRATION-001** — Must dispatch and land (`WO-PARSER-NARRATION-001_DISPATCH.md`).
3. **PENDING-ROLL-AUDIT-001** — Findings must be triaged (`WO-ANVIL-PENDING-ROLL-AUDIT-001_DISPATCH.md`).
4. **SEC-REDACT-001** — Must be merged (status: ACCEPTED 19/19 — verify merge complete).

No campaign WO drafting until all four gates are clear.

### The Two-Repo Situation

Campaign content lives in two places:

| Location | What Lives There |
|----------|-----------------|
| `F:/o/Campain-Wizard areana/` | Campaign design files — PDFs, doctrine, maps, session notes, NPC cards. Thunder's creative workspace. |
| `f:/DnD-3.5/` | AIDM engine — all code, tests, WOs, runtime. The PM's domain. |

Campaign runtime implementation will live in `f:/DnD-3.5/` when built. The doctrine document in `F:/o/` is the source of truth for what to build. The PM does not touch `F:/o/` files. The PM reads them when drafting WOs.

---

## Doctrine Summary — What the PM Will Be Working From

When the engine gates clear, the PM will need to draft WOs for the following runtime contracts. This is the translation queue — **not yet authorized, not yet sequenced, pending engine stabilization:**

### Tier 1 — Foundation Contracts (first to implement)
| Domain | What Needs a Runtime Contract |
|--------|-------------------------------|
| Biome instance generation | Deterministic seed (`biome_id + day_id + entrant_level_band + weather_event_seed + realm_mood_state`), daily drift, CR/DC scaling by level band, terrain grammar |
| Session mode enforcement | Arena / Off-Time / Tribunal mode boundaries, AIDM mode-switch detection and refusal |
| Essence accounting | Automatic extraction on defeat (hidden), resurrection cost deduction, no player-visible ledger |
| Patron relationship state | Named patron tracking, affinity scoring, promotion trigger (crowd standout → named patron after major dramatic moment) |

### Tier 2 — Economy Contracts (second wave)
| Domain | What Needs a Runtime Contract |
|--------|-------------------------------|
| Token economy | Six-function currency: performance, survival, progression, social, behavioral control, ideological containment |
| Crowd sentiment loop | Aggregate crowd meter, round-by-round drift, token payout on crowd-peak moments |
| Audience intervention system | Boon/hazard dispatch by patron affinity, AIDM arbitration of conflicts |
| Mount upkeep system | Ongoing cost vs token income tension |

### Tier 3 — Narrative Contracts (third wave)
| Domain | What Needs a Runtime Contract |
|--------|-------------------------------|
| Rumor system | Passive immune response seeding, never flagged as system output, AIDM-surfaced only |
| Hairline crack surfacing | Seven anomaly types, AIDM surfaces evidence, does not build the case |
| Three fates tracking | Winners (worship), Hollowed (essence extraction), Taken (Sixth Realm — invisible) |
| Pity mechanism | "He couldn't make it here" NPC dialogue seeding on departures |

---

## Key Canon Decisions — PM Must Not Contradict

These were locked by Thunder this session and are not subject to PM revision:

1. **The Buyout is real.** Exists in legend. Threshold unknown and possibly scales. Mathyrian never lies — he omits the destination.
2. **Mathyrian never lies.** He is a contested legitimacy problem, not a villain. The player must decide whether a beneficial system can still be illegitimate.
3. **Paladins never re-enter the realm.** They are in the Sixth Realm. They are never seen. This is not a mystery to solve — it is a structural guarantee.
4. **No unprofitable outcome.** Victory = devotion (worship energy), Defeat = essence extraction. Mathyrian profits from both ends.
5. **AIDM surfaces evidence, does not build the case.** Hairline cracks are surfaced passively. The AIDM does not editorialize.
6. **Campaign is the certification test for the table.** If the engine holds under this campaign, it holds under anything.
7. **Single-player format is binding.** Primary: one player + AIDM. Two companion characters travel with the player (AIDM-controlled). Full multiplayer format is explicitly out of scope.

---

## Open Items — PM Needs Thunder Clarification Before Acting

| Item | Status | Who Decides |
|------|--------|-------------|
| Aegis's specific campaign role | Seat confirmed (Paladin/Architect). Campaign-specific tasking TBD before spec begins. | Thunder |
| Campaign WO sequencing | Deferred until engine stabilizes | PM (after gates clear) |
| Whether campaign files in `F:/o/` need a mirror or symlink in `f:/DnD-3.5/` | Undecided | Thunder + PM |

---

## Filing Recommendation

The PM should NOT file this document into `reviewed/` yet. It is an active intake. Suggested PM workflow:

1. **Read** `BUBBLE_REALM_DOCTRINE.md` in full before drafting any campaign WO.
2. **Park this document** in `pm_inbox/` until engine gates clear.
3. **When ENGINE-RETRY-001 and other gates close:** move this document to `pm_inbox/reviewed/` and begin sequencing Tier 1 contracts into WO drafts.
4. **Clarify Aegis's campaign-specific tasking with Thunder** before campaign spec phase begins (seat confirmed; role in campaign build TBD).

---

## Doctrine Document Location (for quick reference)

```
F:/o/Campain-Wizard areana/00_Admin/BUBBLE_REALM_DOCTRINE.md
```

Sections 1–24 cover: Central thesis, Mathyrian, immune system, three paths, single-player design, three session modes, five biomes, biome reaction model, two biome states, five arena contracts, dual audience architecture, arena as civilization engine, AIDM requirements, governing sentence, token economy, death/gear loss/respawn economy, three fates, essence economy, sixth realm, rumor system, three clean exits, population replacement, pity mechanism, hairline cracks.

---

**The governing sentence (locked):** Fixed law. Variable expression. Memory of consequence.

**The central question (locked):** Before Mathyrian can be judged as a villain, the player must decide whether a beneficial system can still be illegitimate.
