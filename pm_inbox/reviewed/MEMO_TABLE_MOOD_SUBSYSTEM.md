# MEMO: TableMood Subsystem — Closed-Loop Player Responsiveness

**From:** Aegis (3rd-Party Governance / Audit), packaged by BS Buddy (Anvil)
**To:** PM (Execution Authority)
**Date:** 2026-02-18
**Lifecycle:** PM INTAKE
**Subject:** TableMood — "read the room" without breaking law
**Source:** Operator + Aegis/GPT session, Mercer gap analysis with BS Buddy

---

## Purpose

Close the biggest remaining experience gap: the engine cannot read the player. This memo defines a new subsystem — TableMood — that captures player responsiveness signals and feeds them to Director and Spark as **presentation hints**, never as **truth or mechanical influence**.

This is the difference between a DM who adjusts delivery based on the room and a DM who fudges dice based on feelings. TableMood does the former. It is architecturally forbidden from doing the latter.

---

## Two Design Rules (Non-Negotiable)

**Rule 1: Mood signals can influence pacing and presentation, never truth.**
- They can steer Director and Spark style choices (tempo, brevity, warmth, recap depth).
- They cannot alter Box outcomes, DCs, encounter math, or canon.

**Rule 2: All mood inference must be explicit, local, and reversible.**
- No cloud.
- No silent profiling.
- Player can view, edit, or delete it.
- Use coarse tags, not psych eval.

---

## Signal Sources (What You Can Capture)

### A. Explicit Feedback Prompts (Best Signal)

After beats or scenes, ask one low-friction question, opt-in:
- "Was that fun, confusing, tense, or boring?"

This is gold because it is truth, not inference.

### B. Conversation Style Signals from Verbiage (Safe if Bounded)

Track simple features from the player's text:
- response length (short, medium, long)
- question frequency
- "wait, what" / "hold on" confusion markers
- laughter markers ("lol", "haha"), exclamation density
- hedges ("maybe", "i guess") vs decisive commands
- frustration markers ("this is BS", "why can't I")

Do not store raw chat logs by default. Store **summaries of signals**.

### C. Interaction Tempo (Implicit)

- time between DM beat and player response
- number of interruptions
- how often player asks for rulebook
- how often player rewinds or requests recap

### D. Optional Voice Prosody (Phase 2, Strictly Opt-In)

If STT is available, derive coarse prosody stats (rate, volume variability, pauses). This is the slipperiest privacy-wise. Keep this Phase 2 and strictly opt-in.

---

## Architecture Integration (No Law Violations)

### New Store: TableMood (Under Oracle)

Oracle owns TableMood as an append-only record of observations and explicit feedback.

**How each subsystem uses it:**
- **Lens** can include a compact "mood summary" in the PromptPack as a style hint.
- **Director** can use it to choose pacing decisions (push, breathe, recap).
- **Spark** can use it to adjust tone and beat length.

**No backflow is preserved because:**
- It does not change canon facts.
- It does not change mechanical outcomes.
- It is not used as evidence for truth, only as presentation control.

---

## Minimal Contract

### PlayerProfile (Static Preferences)

Identity-level settings, player-configured:
- `verbosity_preference`: low, medium, high
- `humor_tolerance`: low, medium, high
- `horror_intensity`: low, medium, high
- `recap_frequency`: none, light, normal
- `teaching_mode`: off, light, normal
- `interruption_style`: strict, normal
- `consent_defaults`: notebook write prompt on/off, debrief ask mode, etc.

### TableMood (Append-Only Observations)

Each entry is either explicit or inferred:
- `source`: `EXPLICIT_FEEDBACK` or `INFERRED_SIGNAL`
- `scope`: `SCENE` or `SESSION`
- `tags`: fun, confused, tense, bored, engaged, frustrated
- `confidence`: low, medium, high (only for inferred)
- `evidence`: small numeric features, not raw text
- `provenance_event_id`: the scene or beat event that triggered it

### Lens Usage — Style Capsule

Lens emits a tiny "style capsule" derived from TableMood:
- target beat length
- recap needed: yes or no
- humor window open: yes or no
- pacing mode: push or breathe

### Director Usage — Pacing Policies

Director picks from a small set of pacing policies:
- accelerate, normal, decompress
- offer recap, offer rulebook, offer debrief

Director never invents content. It only changes selection and timing.

### Spark Usage — Delivery Variation

Spark varies delivery, not facts:
- shorter beats if player is overloaded
- more sensory detail if engaged
- fewer NPC digressions if confused
- comedic timing if humor window open

---

## Gates

**Gate M-G1: No Mechanical Influence**
Prove TableMood cannot affect Box inputs. Tests assert no Box parameter changes are conditioned on mood.

**Gate M-G2: No Canon Writes**
TableMood writes do not create or modify FactsLedger facts. Only style hints.

**Gate M-G3: Consent and Visibility**
Player can view, edit, delete TableMood and PlayerProfile. If disabled, no entries are recorded.

**Gate M-G4: No Raw Transcript Retention by Default**
Only store aggregated signals unless player explicitly opts in to save transcripts.

---

## Phasing

**Phase 1 (Minimum Viable Responsiveness):**
- Explicit feedback prompts only
- Two inferred signals: confusion markers + laughter markers
- Director uses pacing policies
- Spark adjusts beat length

**Phase 2 (Full Signal Suite):**
- All conversation style signals (Section B)
- Interaction tempo tracking (Section C)
- PlayerProfile static preferences
- Full style capsule in Lens

**Phase 3 (Optional, Strictly Opt-In):**
- Voice prosody from STT (Section D)
- Extended signal features

---

## Relationship to Existing Doctrine

- **A-NO-BACKFLOW:** Preserved. TableMood influences presentation, never canon/legality/DCs/mechanics.
- **A-AUTH:** Preserved. Box remains authoritative. TableMood is advisory to Spark/Director only.
- **A-DEBRIEF:** Complementary. Explicit feedback prompts are a lighter version of the debrief offer.
- **A-SECRETS:** Preserved. TableMood never reveals locked precision tokens.
- **UI Bans:** Preserved. Feedback prompts are spoken-line delivery, not tooltip/popover UI.
- **Consent Model:** Extended. PlayerProfile and TableMood are player-visible and deletable artifacts.

---

## What This Solves

The engine becomes a DM who:
- notices when you're confused and offers a recap
- notices when you're having fun and keeps pushing
- notices when you're overloaded and shortens the beats
- notices when you laugh and opens the humor window
- asks "was that fun?" after a big moment and remembers the answer

It does NOT become a DM who:
- makes encounters easier because you're frustrated
- hides information because you seem overwhelmed
- manipulates emotions through hidden profiling
- stores psychological data without consent

The difference is the line between responsiveness and manipulation. TableMood stays on the right side by construction.

---

*End of TableMood subsystem memo.*
