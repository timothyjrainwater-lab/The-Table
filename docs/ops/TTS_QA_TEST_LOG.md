# TTS QA Test Log

**Purpose:** Persistent record of voice tests run during BS Buddy sessions. Every voice output is product QA for the DM narration engine. This log tracks what works, what doesn't, and builds a database of proven voice configurations.

**How to use:** Append new entries at the top of the log (newest first). Every BS Buddy session should add entries here. Operator verdicts get filled in during or after the session.

---

## Log Format

| Date | Character | Persona | Reference | Text (summary) | Emotional Target | Result | Notes |
|------|-----------|---------|-----------|-----------------|-----------------|--------|-------|
| *date* | *session character* | *preset used* | *ref wav* | *what was said (shortened)* | *joy/pushback/dramatic/humor/thoughtful/storytelling* | *pass/fail/mixed* | *observations* |

**Result values:**
- **pass** — sounded good, matched emotional target
- **fail** — broke, mispronounced, wrong tone, or sounded unnatural
- **mixed** — partially worked, notable issues but usable
- **overlap** — audio collision with another concurrent call

---

## Session: 2026-02-18 — Tharrik Ashbone "Gravel" (Half-Orc Barbarian 3 / Bard 1)

| Date | Character | Persona | Reference | Text (summary) | Emotional Target | Result | Notes |
|------|-----------|---------|-----------|-----------------|-----------------|--------|-------|
| 2026-02-18 | Gravel | villainous | default | "New session, new face..." | confident/casual | pass | Operator said "that sounded good." First line of session. |
| 2026-02-18 | Gravel | npc_male | default | "That's meat. Half-orc barbarian bard..." | joy/excitement | TBD | Character establishment line. Testing npc_male for Gravel's main voice. |
| 2026-02-18 | — | dm_narrator | CREMA-D neutral (1005) | "The tavern falls silent..." | storytelling/neutral | TBD | Emotion router test — neutral mood. |
| 2026-02-18 | — | dm_narrator | CREMA-D angry (1005) | "Roll for initiative!..." | combat/excitement | mixed | Operator: "initiative was a little weak." Angry ref didn't sell urgency. |
| 2026-02-18 | — | dm_narrator | CREMA-D grief (1005) | "And with that final breath..." | dramatic/grief | TBD | Emotion router test — dramatic mood → grief register. |
| 2026-02-18 | — | villainous | CREMA-D angry (1040) | "You dare challenge me?..." | menacing/combat | pass | Operator liked this batch overall. |
| 2026-02-18 | — | villainous | CREMA-D grief (1040) | "Everything you love will burn..." | menacing/dramatic | pass | Emotion router grief register for villain. |
| 2026-02-18 | — | npc_female | CREMA-D tense (1012) | "Something is watching us..." | tense/urgent | TBD | Tense register test. |
| 2026-02-18 | — | npc_male | CREMA-D neutral (1050) | "The road to Ironhold..." | neutral/informative | TBD | Neutral register exposition. |
| 2026-02-18 | — | npc_male | CREMA-D angry (1050) | "To arms! They are breaching..." | combat/urgent | TBD | Combat register battle cry. |
| 2026-02-18 | — | villainous | CREMA-D angry (tavern medium) | "Everything you love will burn..." | menacing/dramatic | pass | **Tavern-baked ref test.** Voice identity drifted (different male) but room sound noticeably improved. Operator: "room audio is better." |
| 2026-02-18 | — | dm_narrator | CREMA-D neutral (tavern medium) | "Everything you love will burn..." | storytelling | pass | **Tavern-baked ref test.** Operator: "noticeable improvement." Room character present. |
| 2026-02-18 | — | villainous | CREMA-D angry (tavern light) | "Everything you love will burn..." | menacing/dramatic | mixed | Light bake — happy uptick on "watch." Text-dependent intonation issue, not room issue. |
| 2026-02-18 | — | villainous | CREMA-D angry (tavern light) | "There is no mercy. Only the flames remain." | menacing/dramatic | TBD | Darker text, light bake. Testing text influence on intonation. |
| 2026-02-18 | — | villainous | CREMA-D angry (tavern medium) | "There is no mercy. Only the flames remain." | menacing/dramatic | pass | **Winner.** Operator: "that second one's sound and good." Medium bake + dark text = sweet spot. |
| 2026-02-18 | — | villainous | CREMA-D angry (tavern heavy) | "There is no mercy. Only the flames remain." | menacing/dramatic | TBD | Heavy bake test. |

### Session Findings
- **CREMA-D acted clips confirmed:** Human-acted emotion clips transfer through Chatterbox. Bootstrapped (self-generated) clips do NOT — they all sound identical.
- **Studio-booth acoustic bleed:** CREMA-D dry-booth recording environment transfers through cloning. Output sounds clinical.
- **Post-processing is a dead end:** Convolution reverb on Chatterbox OUTPUT doesn't work. Chatterbox bakes the booth INTO the signal — adding room on top of cloned-booth just makes it louder, not roomier. GPT confirmed: spectral ratios 0.96-0.99 across all bands despite 476% RMS difference. The "change" was amplitude, not room character.
- **PRE-processing the reference IS the fix:** Baking tavern room ambience into the CREMA-D clips BEFORE Chatterbox clones them transfers the room character to output. Operator confirmed on two separate tests.
- **Medium tavern bake = sweet spot:** Light (corr 0.96) too subtle. Medium (corr 0.88) confirmed good. Heavy (corr 0.76) untested but higher identity drift risk.
- **Tavern IR recipe (medium):** ERs at 5/8/12/17/22/28/35ms, amps -8 to -22dB, diffuse tail 40-200ms with RT60=200ms, tail gain 0.015, LP at 4kHz. Seed=7 for reproducibility.
- **All 16 CREMA-D refs tavern-baked and deployed.** Dry originals backed up to `models/voices/dry_backup/`. Zero code changes — emotion router picks up new files by filename.
- **Text shapes intonation:** "watch" triggered happy uptick on villain line. Darker text ("no mercy, only flames") fixed it. Text selection matters for emotional delivery.
- **Emotional range narrow but present:** Operator: "almost like the actor sounds a little bored, but it's there." CREMA-D actors are academic, not performance actors. Wider range needs better source material.
- **Emotion router wired and working:** `mood` param flows through `synthesize()` to select register-specific CREMA-D clips.
- **Initiative line weak:** dm_narrator + angry register didn't sell combat urgency. May need different actor or higher exaggeration for combat callouts.
- **Post-processing attempt 1 (synthetic reverb):** Stadium echo. Operator: "sounds like a stadium."
- **Post-processing attempt 2 (dialed back):** Operator: "still a stadium."
- **GPT post-processing recipe (ER-only + tableroom):** Technically correct but imperceptible on Chatterbox output due to booth-already-cloned problem. Abandoned in favor of upstream reference bake.
- **Monster/orc voices:** Pitch-shifting human refs doesn't work — Chatterbox sees through it. Freesound CC-BY candidates identified (71s orc NPC encounter phrases, 36s orc troll vocalized, several villain command barks). Download pending.
- **GPT tuning guidance for future calibration:** ER delay <22ms, RT60 <160ms, wet 3-8%, HP 150-250Hz, LP 6-8kHz. MFCC cosine distance preferred over correlation for identity gating.

---

## Session: 2026-02-14 — Sable Kettlecatch (Gnome Illusionist 4 / Rogue 2)

| Date | Character | Persona | Reference | Text (summary) | Emotional Target | Result | Notes |
|------|-----------|---------|-----------|-----------------|-----------------|--------|-------|
| 2026-02-14 | Sable | npc_young | default | Intro line — "Sable Kettlecatch, at your service..." | joy/excitement | pass | First successful voice after fixing raw param flags. Preset worked where raw flags didn't. |
| 2026-02-14 | Sable | villainous | default | Scheming line about killing the persona system | dramatic/humor | overlap | Ran concurrently with 2 others — all 3 overlaid. Audio collision discovered. |
| 2026-02-14 | Sable | npc_elderly | default | Sage wisdom line | thoughtful | overlap | Part of the 3-way concurrent test. Overlaid with villainous + heroic. |
| 2026-02-14 | Sable | heroic | default | Excited affirmation | joy/excitement | overlap | Part of the 3-way concurrent test. Audio overlap confirmed as product bug. |
| 2026-02-14 | Sable | npc_male | default | Casual conversational line | thoughtful | pass | Single voice, no overlap. Clean playback. |
| 2026-02-14 | Sable | dm_narrator | default | "Every test should leave a trail..." | thoughtful/measured | pass | Clean. Good pacing for measured insight delivery. |

### Session Findings
- **speak.py does NOT accept raw --speed/--pitch/--exaggeration flags.** Only --persona (8 presets). Custom parameters require adapter code changes.
- **Multiple concurrent speak.py calls overlay audio** — no playback queue, no mutex. One voice call per response rule established.
- **Wished for:** speed 1.15 (npc_young caps at 1.1), higher pitch range for gnome character.

---

## Session: 2026-02-14 — Cinder Voss (Fire Genasi Sorcerer 4 / Fighter 2)

| Date | Character | Persona | Reference | Text (summary) | Emotional Target | Result | Notes |
|------|-----------|---------|-----------|-----------------|-----------------|--------|-------|
| 2026-02-14 | Cinder | villainous | george | Intro — "Fresh context, fresh fire..." | dramatic/confident | pass | First test with villainous + george ref combo. Clean run, 177 sampling steps. No errors. |
| 2026-02-14 | Cinder | villainous | george | Excited — "Now we're cooking..." | joy/excitement | pass | Clean run. Archetype casting session begins. |
| 2026-02-14 | Cinder | npc_elderly | default | Old sage — "Things in those mountains older than the kingdom..." | dramatic/foreboding | mixed | PRE-FIX: persona was not wired to Chatterbox — was actually Arbor (exagg 0.15). Monotone. |
| 2026-02-14 | Cinder | npc_elderly | michael (default) | Old sage retest — same text, post-fix | dramatic/foreboding | mixed | POST-FIX: npc_elderly preset (exagg 0.3) now hitting engine. Still monotone — exagg too low. |
| 2026-02-14 | Cinder | npc_elderly | george | Old sage — exagg 0.9, speed 0.75 | dramatic/foreboding | fail | WAY too theatrical. Operator: "sounded like getting kicked in the balls." 0.9 overshoots. |
| 2026-02-14 | Cinder | npc_elderly | george | Old sage — exagg 0.5, speed 0.8 | dramatic/foreboding | fail | Wrong emotional register. Operator: "sounds super gay." Exaggeration doesn't map to gravitas — it adds breathiness/wobble. |
| 2026-02-14 | Cinder | dm_narrator_male | michael | Old sage — exagg 0.25, speed 0.8 | controlled authority | mixed-pass | Operator: "not super gay but very sweet. I might like him." Not stern sage — more gentle mentor. Potential archetype: Kind Wizard / Caring Mentor. |
| 2026-02-14 | Cinder | villainous | george | Villain monologue — exagg 0.65, speed 0.85 | menacing/theatrical | pass | Operator: "not bad for a tiny evil villain." Lands as petty tyrant / scheming imp, not ancient lich. Archetype: Mini-Boss / Goblin King / Petty Villain. |
| 2026-02-14 | Cinder | villainous | michael | Villain monologue — exagg 0.4, speed 0.8 | imposing/menacing | pass | Operator: "that voice is evil elf." Smooth, cold, precise. Archetype: Evil Elf / Drow Schemer / Poisoner. Michael ref = cleaner, more refined menace vs george's scrappier villain. |

### Session Findings
- **BUG FOUND & FIXED:** `_speak_chatterbox()` in speak.py was ignoring the `--persona` flag and hardcoding Arbor's profile (exagg 0.15) for ALL calls. All prior "persona tests" were actually Arbor. Fixed: persona string now passed to adapter for lookup.
- **NEW CLI FLAGS ADDED:** `--reference`, `--exaggeration`, `--speed` — raw parameter overrides from CLI. Anvil's session-1 wish fulfilled.
- **Exaggeration sweet spot search:** 0.15 = monotone, 0.9 = distorted/painful, 0.5 = TBD (testing now)
- All pre-fix test results in Sable's session are invalid for persona differentiation (all were Arbor)

---

## Known Issues (cumulative)

1. **Audio overlap** — No playback queue. Multiple concurrent speak.py calls play simultaneously. Mitigation: one voice call per response. Fix: persistent server with sequential queue (see HANDOFF_TTS_COLD_START_RESEARCH.md).
2. **Cold start latency** — Each speak.py invocation cold-loads Chatterbox model (~3-4s). Persistent server would solve.
3. ~~**No raw parameter CLI flags**~~ — **FIXED (2026-02-14).** speak.py now accepts --reference, --exaggeration, --speed.
4. **Arbor reservation** — michael ref + speed 0.88 + pitch 1.0 + exaggeration 0.15 is reserved for operational signals. BS Buddy must never use this exact profile.
5. ~~**Studio-booth acoustic bleed**~~ — **FIXED (2026-02-18).** All 16 CREMA-D emotion refs tavern-baked at medium intensity. Dry originals in `models/voices/dry_backup/`. Post-processing output doesn't work; pre-processing reference clips does.
6. **Narrow emotional range** — CREMA-D actors sound "a little bored." Emotion is present but subtle. Need higher-performance source material for combat/dramatic moments.
7. **No monster/non-human voices** — Pitch-shifting human refs doesn't fool Chatterbox. Need actual guttural/orc voice source clips. Freesound CC-BY candidates identified, download pending.
8. **Text shapes intonation** — Chatterbox reads word valence. Positive words ("watch") can trigger happy uptick even in villain context. Text selection matters.

---

## Persona Coverage Matrix

Track which personas have been tested across sessions to ensure full coverage.

| Persona | Times Tested | Last Tested | Best Use Case | Issues |
|---------|-------------|-------------|---------------|--------|
| dm_narrator | 4 | 2026-02-18 | Measured insight, scene-setting | Initiative line weak on angry register |
| dm_narrator_male | 0 | — | — | Untested |
| npc_male | 3 | 2026-02-18 | Casual conversation | "Doesn't have that half-orc guttural vibe" — too clean for non-human |
| npc_female | 1 | 2026-02-18 | Tense/urgent scenes | Tested with CREMA-D tense register |
| npc_elderly | 1 | 2026-02-14 | Sage wisdom | Overlapped (not tested solo) |
| npc_young | 1 | 2026-02-14 | Energetic/excited delivery | Caps at speed 1.1 |
| villainous | 8 | 2026-02-18 | Dramatic, scheming, menacing | Most tested persona. Medium tavern bake + dark text = best result. |
| heroic | 1 | 2026-02-14 | Excited affirmation | Overlapped (not tested solo) |

## Reference Voice Coverage

| Reference | Times Used | Characters | Notes |
|-----------|-----------|------------|-------|
| signal_reference_24k.wav (default) | 6 | Sable | All Sable tests |
| signal_reference_george_24k.wav | 1 | Cinder | Villainous + george = clean run |
| signal_reference_michael_24k.wav | 0 | — | Reserved for Arbor; avoid exact Arbor profile |
| CREMA-D emotion refs (dry) | 10 | Gravel session | Phase 1 emotion router tests. Clinical booth sound. |
| CREMA-D emotion refs (tavern-baked) | 6 | Gravel session | **Current active set.** Medium tavern bake. Room character confirmed. |

## Key Discovery: Reference Pre-Processing

**Post-processing Chatterbox output does NOT fix booth acoustics.** Chatterbox clones the acoustic environment from the reference clip into the output signal. Adding reverb/room after generation stacks spaces — the signal already contains the booth.

**Pre-processing the reference clip DOES work.** Baking room ambience into the 5-second CREMA-D reference before Chatterbox clones it transfers the room character to the output natively. Medium tavern bake (correlation ~0.88) confirmed as sweet spot by operator on 2026-02-18.

Tavern IR recipe: ERs at 5/8/12/17/22/28/35ms, -8 to -22dB. Diffuse tail 40-200ms, RT60=200ms, tail_gain=0.015, LP 4kHz. Seed=7.
