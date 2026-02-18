# MEMO: RiffSpace — Bounded Improvisation Pipeline

**From:** Aegis (3rd-Party Governance / Audit), packaged by BS Buddy (Anvil)
**To:** PM (Execution Authority)
**Date:** 2026-02-18
**Lifecycle:** PM INTAKE
**Subject:** RiffSpace — improvisation without breaking law
**Source:** Operator + Aegis/GPT session, Mercer gap analysis with BS Buddy

---

## Purpose

Improvisation is the remaining Mercer-like capability that no existing subsystem covers. This memo defines a bounded proposal-and-promotion pipeline called RiffSpace that enables Spark to riff in the moment without violating A-NO-BACKFLOW, A-AUTH, or consent rules.

The core insight: you do not hard-code improvisation as "invent anything." You hard-code it as a bounded proposal system that can create new content only in an explicitly marked sandbox, then promote it to canon only with consent.

---

## Improvisation Pipeline (Four Steps, Split Across Subsystems)

Humans do all four steps in their head. The architecture splits them into subsystems with gates.

1. **Detect** a riff opportunity.
2. **Generate** 2-3 candidate continuations that fit the world.
3. **Choose** one path.
4. **Commit** it as canon only if allowed.

---

## Three Safe Categories of Improvisation

### Category A: Surface Improv (Canon-Free)

Pure performance. NPC jokes, banter, descriptions, minor flavor. No new facts. No new plot hooks. No new items. Always allowed. Zero risk.

### Category B: Soft Improv (Provisional)

Adds new "color facts" that do not affect legality. Example: "The tavern has a cracked stained-glass window." Stored as provisional with tag `PROPOSED` or `EPHEMERAL`. Not used as evidence for later decisions unless promoted.

### Category C: Hard Improv (Canon-Affecting)

New NPC, new clue, new faction move, new dungeon branch. This is the risky part. Must go through an explicit promotion path with consent.

---

## New Oracle Store: RiffSpace

Separate from FactsLedger. Stores proposed facts only.

### RiffSpace Entry Schema

- `proposed_fact_id`: stable unique identifier
- `payload`: the proposed fact content
- `provenance`: which beat and what player action triggered it
- `risk_class`: `A`, `B`, or `C`
- `status`: `PROPOSED`, `ACCEPTED`, `REJECTED`, `EXPIRED`
- `expiry`: `SCENE` or `SESSION`
- `consent_event_id`: null until promoted (required for ACCEPTED)

### Promotion Rule (Single, Non-Negotiable)

Only ACCEPTED proposals can be promoted into FactsLedger, and promotion requires a consent event ID. No exceptions.

---

## Player Experience (The Mercer Feel)

The player does not see the machinery. The player experiences:

- **Category A:** The DM riffs naturally. No interruption.
- **Category C:** The DM asks a quick confirm only when it matters.

Mercer does this too, socially:
- "Wait, are you saying you *know* the Baron?"
- "Yes."
- "Okay, then..."

Build a small set of "improv handshake" lines:
- "Okay, that is a real change. Confirm?"
- "Do you want that to be true in the world?"
- "Cool. Writing it down."

This is Declare -> Point -> Confirm applied to canon creation.

---

## Content Source: Improv Palette (Bounded Novelty)

Proposals are not random. They draw from a bounded improv palette built from:

- CampaignManifest seeds
- Existing FactsLedger entities and relationships
- Style pack and theme constraints
- Mode constraints (e.g., "no new factions unless in manifest" for strict mode)

The generator combines existing pieces in new ways but does not create new roots unless permitted.

**Allowed:** "A guard captain from faction X is bribed by faction Y." (recombination)
**Not allowed:** "A brand new god appears." (new root, unless campaign mode allows it)

Surprise comes via recombination, not hallucinated invention.

---

## Stack Integration (Who Runs What)

1. **Director** detects the riff opportunity and requests proposals.
2. **Lens** provides the allowed palette and constraints to Spark.
3. **Spark** generates 2-3 proposals.
4. **Director** picks one proposal based on pacing goals.
5. Then:
   - If **Category A**: render it, no store write.
   - If **Category B**: store as `EPHEMERAL`, auto-expires at scene/session boundary.
   - If **Category C**: require consent to promote to FactsLedger.

---

## Gates

**Gate I-G1: No Unconsented Canon Writes**
No `PROPOSED` item can enter FactsLedger without a `consent_event_id`.

**Gate I-G2: Separation of Stores**
Spark can write to RiffSpace only through a typed `PROPOSAL_REQUEST`. Spark cannot write FactsLedger directly.

**Gate I-G3: Palette Boundedness**
Proposal generation input is limited to Lens-provided palette. No free browsing of Oracle.

**Gate I-G4: Expiry**
Provisional facts expire by scene or session unless promoted. Prevents silent canon drift.

**Gate I-G5: Auditability**
Every promoted improv fact must point to the trigger event and consent event.

---

## Relationship to Existing Doctrine

- **A-NO-BACKFLOW:** Preserved. RiffSpace is a sandbox, not FactsLedger. No canon change without consent.
- **A-AUTH:** Preserved. Box remains authoritative. Proposals cannot affect legality, DCs, or mechanics.
- **A-SECRETS:** Preserved. Improv palette is filtered through Lens — locked precision tokens cannot leak into proposals.
- **Consent Model:** Extended. Category C promotion is a new consent event type (same pattern as existing handshakes).
- **UI Bans:** Preserved. Improv handshake lines are spoken-line delivery, not tooltip/popover UI.
- **Director Read-Only:** Preserved. Director selects proposals but does not write canon. Promotion is a separate consent-gated action.

---

## Phasing

**Phase 1 (Minimum Viable Riffing):**
- Category A only (surface improv, always allowed)
- Category C with single confirmation line (hard improv, consent-gated)
- Skip Category B entirely
- RiffSpace store exists but only for Category C proposals
- Gives immediate "riffing" feel while keeping canon promotion rare and explicit

**Phase 2 (Full Pipeline):**
- Category B with `EPHEMERAL` tagging and auto-expiry
- Full improv palette compilation from CampaignManifest
- Director proposal request/selection flow
- Lens palette constraint enforcement

---

## What This Solves

The engine becomes a DM who:
- riffs naturally in conversation (Category A)
- introduces surprising but fitting developments (Category B/C via recombination)
- asks "do you want that to be true?" before anything sticks (Category C consent)
- never silently changes the world behind the player's back
- never hallucinates new roots outside the campaign's genre and rules

The difference between this and unconstrained generation: RiffSpace is improv inside the campaign's genre and rules, not improv that overwrites them.

---

*End of RiffSpace improvisation pipeline memo.*
