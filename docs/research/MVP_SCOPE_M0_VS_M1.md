# MVP Scope: M0 vs M1 — R0 Research Draft

**Status:** R0 / DRAFT / NON-BINDING
**Purpose:** Define ruthless feature triage for M0 launch
**Authority:** Advisory — requires stakeholder approval
**Last Updated:** 2026-02-10

---

## ⚠️ DRAFT NOTICE

This document is a **research draft** proposing M0 vs M1 feature split. It is **not binding** until:

1. R0 research validates feasibility of M0 features
2. Stakeholder review confirms scope aligns with goals
3. Formal approval locks M0 scope

**This is a triage exercise, not a roadmap commitment.**

---

## Purpose

**Identified Risk:** The inbox documents contain **zero prioritization**. Everything is marked "binding" with no distinction between launch-critical and enhancement features.

**Without ruthless triage:**
- M0 will bloat to 18+ months
- Quality will suffer (spread too thin)
- Launch will be delayed or cancelled

**With ruthless triage:**
- M0 delivers core experience in 6-9 months
- Quality focuses on critical path
- M1 adds polish and enhancements post-launch

---

## Guiding Principles

### 1. M0 is Minimum **Viable**, Not Minimum **Functional**

**Viable** means:
- Players can complete a satisfying D&D 3.5e session
- Core loop works end-to-end (character → play → progression)
- Experience is **stable** and **deterministic**

**Does NOT mean:**
- Every feature from inbox documents
- Perfect polish
- Full automation

### 2. M1 is Enhancement, Not Repair

**M1 adds:**
- Polish (better UX, faster performance)
- Convenience (adaptive DM, player modeling)
- Content (extended asset library, localization)

**Does NOT add:**
- Missing core mechanics (those are M0)
- Foundational architecture (those are M0-Pre)

### 3. If It's Not Tested in R0, It's Not in M0

**M0 can only include:**
- Features with R0 research validation
- Features with known failure modes
- Features within hardware budget

**Unvalidated features → M1**

---

## M0 Launch Scope (PROPOSED)

### M0-Pre: Foundations (Weeks 1-4)

**Goal:** Establish architectural foundations before feature work.

**Deliverables:**
- Canonical ID schema (finalized)
- Indexed memory architecture (specified)
- Hardware baseline (locked)
- Determinism contract (documented)
- UI layout design (wireframes)

**NOT in M0-Pre:**
- Full UI implementation (M0-Interaction)
- Asset generation (M0-Polish)
- Player modeling (M1)

---

### M0-Core: Deterministic Engine (Weeks 5-12)

**Goal:** Deliver core D&D 3.5e mechanics in local-only mode.

#### ✅ IN SCOPE (M0-Core)

**Character Management:**
- Create character from PHB classes (Fighter, Wizard, Cleric, Rogue only)
- Level 1-5 only (M1: levels 6-20)
- Core ability scores, skills, feats, equipment
- Character sheet UI (read-only display)

**Combat System:**
- Initiative, attack rolls, damage
- Movement, positioning, attacks of opportunity
- Core conditions (prone, grappled, stunned)
- Basic spells (PHB core list, levels 1-3)

**Dice & Determinism:**
- All rolls deterministic (replay-safe)
- RNG stream isolation
- Event log with replay capability

**Game State:**
- WorldState persistence
- Save/load from disk
- Session continuity

#### ❌ OUT OF SCOPE (Deferred to M1)

**Extended Content:**
- Prestige classes → M1
- Exotic weapons → M1
- Advanced feats (metamagic, item creation) → M1
- Spell levels 4-9 → M1
- Monster Manual beyond core creatures → M1

**Advanced Mechanics:**
- Mounted combat → M1 (already implemented, but not launch-critical)
- Grappling → M1
- Swimming/drowning → M1
- Crafting → M1

**Convenience Features:**
- Auto-leveling → M1
- Suggested builds → M1
- Rule lookup tooltips → M1

---

### M0-Interaction: Voice & Text UI (Weeks 13-18)

**Goal:** Deliver **voice-first** interaction with **text fallback**.

#### ✅ IN SCOPE (M0-Interaction)

**Voice Input (STT):**
- Player speaks actions ("I attack the goblin")
- STT transcribes to text
- Disambiguation UI for ambiguous input
- Confirmation for high-impact actions
- **Supported languages:** English only (M1: multilingual)

**Voice Output (TTS):**
- DM narrates results ("The goblin takes 8 damage")
- Single DM voice (no NPC voices in M0)
- Basic expression control (neutral tone)
- **Quality gate:** R0 must validate acceptable TTS quality

**Text Interaction:**
- Type commands as fallback
- Canonical command syntax (e.g., `/attack goblin`)
- Chat log with full history

**UI Layout:**
- Minimal UI (character sheet + chat + grid)
- Combat grid visualization (2D, static)
- No animations (M1: animated sprites)

#### ❌ OUT OF SCOPE (Deferred to M1)

**Advanced Voice:**
- Multiple NPC voices → M1
- Dynamic expression (anger, fear, excitement) → M1
- Interrupt/barge-in → M1

**Multilingual:**
- Non-English languages → M1
- Localized templates → M1
- Alias tables → M1

**Visual Polish:**
- Animated sprites → M1
- Particle effects → M1
- Dynamic lighting → M1

---

### M0-Polish: Prep & Assets (Weeks 19-24)

**Goal:** Deliver **prep-first asset generation** with **quality gates**.

#### ✅ IN SCOPE (M0-Polish)

**Prep Phase:**
- Campaign creation wizard
- Session prep checklist (scout next session's content)
- Asset generation queue (batch jobs)
- Prep log with status tracking

**Image Generation:**
- NPC portraits (anchor images)
- Scene backgrounds (static plates)
- **Quality gate:** Image critique model validates quality
- **Fallback:** Placeholder if quality fails

**Audio Assets:**
- Ambient sound palettes (tavern, forest, dungeon)
- Combat music tracks
- **Pre-generated only** (no runtime generation)

**Asset Management:**
- Asset store with deduplication
- Attribution ledger (license compliance)
- Shared cache for reusable assets

#### ❌ OUT OF SCOPE (Deferred to M1)

**Advanced Asset Generation:**
- Character portraits (player characters) → M1
- Dynamic scene composition → M1
- Sound effects (footsteps, spell casts) → M1
- Music mixing (adaptive soundtrack) → M1

**Asset Curation:**
- Manual asset editing → M1
- Asset versioning → M1
- Asset marketplace/sharing → M1

---

## M0 Feature Matrix

| Feature Category | M0 Launch | M1 Enhancement |
|------------------|-----------|----------------|
| **Character Levels** | 1-5 | 6-20 |
| **Classes** | Fighter, Wizard, Cleric, Rogue | All PHB classes + prestige |
| **Spells** | Levels 1-3, core list | Levels 4-9, full PHB |
| **Combat** | Core (attack, move, AoO) | Advanced (grapple, mount, swim) |
| **Monsters** | Core creatures (20-30 types) | Full MM (100+ types) |
| **Voice Input** | English only | Multilingual |
| **Voice Output** | Single DM voice | NPC voices + expression |
| **Images** | Portraits + backgrounds | Characters + dynamic scenes |
| **Audio** | Ambient + music | SFX + adaptive mixing |
| **UI** | Minimal (sheet + chat + grid) | Polished (animations + tooltips) |
| **Prep** | Manual batch jobs | Automated suggestion engine |
| **Memory** | Indexed records | Adaptive DM behavior |
| **Localization** | English templates | Full language packs |
| **Accessibility** | Basic (text fallback) | Advanced (screen reader, colorblind) |

---

## M0 Success Criteria

**M0 is successful if a player can:**

1. **Create a character** (Fighter, Wizard, Cleric, or Rogue, level 1)
2. **Play a session** (2-4 hours, voice-first)
3. **Complete combat** (initiative, attacks, spells, movement)
4. **Experience narration** (TTS quality acceptable, not perfect)
5. **Save and resume** (deterministic replay works)
6. **Run on median hardware** (Steam Hardware Survey baseline)

**M0 does NOT require:**
- Every PHB class
- Levels 6-20
- Multilingual support
- Perfect asset quality
- Advanced feats or spells

---

## M1 Enhancement Scope (PROPOSED)

### M1 adds (post-launch):

**Content Expansion:**
- All PHB classes (Barbarian, Bard, Druid, Monk, Paladin, Ranger, Sorcerer)
- Prestige classes (Arcane Archer, Assassin, etc.)
- Levels 6-20
- Spell levels 4-9
- Extended monster library (MM complete)

**Quality of Life:**
- Multilingual support (voice + text)
- Auto-leveling suggestions
- Rule lookup tooltips
- In-game tutorial

**Advanced Features:**
- Player modeling (adaptive DM difficulty)
- Dynamic NPC behavior (personality profiles)
- Advanced asset generation (character portraits, dynamic scenes)
- Animated sprites and particle effects

**Performance:**
- GPU acceleration (if available)
- Faster prep pipeline
- Reduced memory footprint

---

## Risks of This Triage

### Risk 1: Player Expectations

**Risk:** Players expect full PHB at launch.

**Mitigation:**
- Market M0 as "Core D&D Experience" (levels 1-5, core classes)
- Communicate M1 roadmap upfront
- Price M0 accordingly (lower price for limited scope)

### Risk 2: Incomplete Experience

**Risk:** Players hit M0 ceiling (level 5 cap) and quit.

**Mitigation:**
- Design M0 campaigns for levels 1-5 (complete arc)
- Ensure M1 upgrade path is seamless
- Offer M1 beta access to M0 players

### Risk 3: Technical Debt

**Risk:** M0 shortcuts create M1 refactoring work.

**Mitigation:**
- Ensure M0 architecture supports M1 (no hacks)
- Use feature flags, not separate codebases
- Validate extensibility during R0

---

## Open Questions

### Q1: Class Selection

**Question:** Which 4 classes for M0?

**Proposal:** Fighter, Wizard, Cleric, Rogue (classic party roles)

**Alternatives:**
- Add Barbarian (simple melee)
- Add Sorcerer (simpler than Wizard)
- Defer Wizard to M1 (spellcasting complexity)

**Decision needed:** Stakeholder input required.

---

### Q2: Level Cap

**Question:** Levels 1-5 or 1-10?

**Proposal:** Levels 1-5 (manageable scope)

**Rationale:**
- Levels 1-5 cover classic adventure arc (low-level heroes)
- Levels 6-10 add spell levels 4-5 (significant complexity)
- Levels 11+ add prestige classes and epic threats (M1)

**Decision needed:** Validate with R0 testing.

---

### Q3: Asset Quality Threshold

**Question:** What is "acceptable" TTS/image quality?

**Proposal:** R0 must establish quality baselines (playtest feedback)

**Criteria:**
- TTS: Understandable, not robotic (benchmark: ElevenLabs "decent" tier)
- Images: Coherent, not uncanny (benchmark: Stable Diffusion "good" samples)

**Decision needed:** R0 playtest validation.

---

### Q4: Prep Time Budget

**Question:** How long should session prep take?

**Proposal:** ≤30 minutes for 2-hour session (15:1 play-to-prep ratio)

**Rationale:**
- Traditional DM prep: 1-2 hours per session
- AIDM should **reduce** prep time, not increase it

**Decision needed:** R0 prototype validation.

---

### Q5: Fallback Strategy

**Question:** What happens if asset generation fails?

**Proposal:** Graceful degradation (placeholders + text descriptions)

**Example:**
- Image generation fails → show placeholder silhouette + text description
- TTS fails → show text-only narration

**Decision needed:** UX design review.

---

## Dependencies on R0 Research

**M0 scope is BLOCKED until R0 validates:**

1. **LLM indexed memory** (<200ms retrieval, >90% accuracy)
2. **Image critique** (>80% bad image detection)
3. **TTS quality** (acceptable baseline established)
4. **Prep pipeline** (≤30 min for 2-hour session)
5. **Hardware feasibility** (median spec runs M0)

**If R0 fails any validation → re-triage M0 scope.**

---

## Next Steps

### Immediate (Weeks 1-2)

1. **Stakeholder review** of this triage
2. **Lock M0 feature list** (finalize class/level/spell selections)
3. **Define M0 success metrics** (what does "launch-ready" mean?)

### R0 Research Phase (Weeks 3-12)

1. **Validate M0 features** (prototype and test)
2. **Document failure modes** (what can go wrong?)
3. **Establish quality baselines** (TTS, images, prep time)

### M0 Planning (Post-R0)

1. **Lock M0 architecture** (based on R0 findings)
2. **Create M0 project plan** (tasks, timeline, milestones)
3. **Begin M0 development** (if GO criteria met)

---

## Appendix: Scope Comparison

### Current Inbox Documents (Unbounded Scope)

**Estimated effort:** 18-24 months, high risk

**Includes:**
- All PHB classes
- All spell levels
- Player modeling
- Adaptive DM
- Multilingual
- Full asset library
- Advanced UI

**Risk:** Feature bloat, delayed launch, quality spread thin

---

### Proposed M0 Triage (Bounded Scope)

**Estimated effort:** 6-9 months, medium risk

**Includes:**
- 4 core classes
- Levels 1-5
- Core spells (1-3)
- Voice + text interaction
- Basic assets (portraits + backgrounds)
- Minimal UI

**Risk:** Player expectations, ceiling effect

---

### Recommendation

**Adopt M0 triage** and commit to **M1 enhancements post-launch**.

**Rationale:**
- Faster time-to-market (6-9 months vs 18-24 months)
- Focused quality (do 4 classes well vs 11 classes poorly)
- Reduced risk (smaller scope = fewer unknowns)
- Iterative feedback (M1 informed by M0 player data)

---

## References

- Global Plan Audit: `docs/analysis/GLOBAL_AUDIT_GAP_AND_RISK_REGISTER.md` (Risk: Feature bloat)
- Global Plan Audit: `docs/analysis/GLOBAL_AUDIT_SYNTHESIS_AND_RECOMMENDATIONS.md` (Recommendation: Ruthless M0 triage)
- Inbox Document: "Secondary Pass Audit" (lists 100+ features, no prioritization)

---

**END OF DRAFT** — R0 validation + stakeholder approval required before use.
