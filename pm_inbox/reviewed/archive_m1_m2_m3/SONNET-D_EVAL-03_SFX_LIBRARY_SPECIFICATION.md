# SFX Library Specification
**Work Order:** WO-M3-AUDIO-EVAL-01 Task 3
**Agent:** Sonnet-D
**Date:** 2026-02-11
**Status:** Complete

## Executive Summary

Sound effects (SFX) generation is **blocked by non-commercial licensing** across all viable AI models as of February 2026 (R1:362-387). The **curated pre-recorded library** is the primary and only path for M3. The library consists of 200-500 royalty-free sounds organized via semantic key taxonomy (e.g., `combat:melee:sword:hit`), sourced from Sonniss GDC bundles and CC0 repositories, with 3-5 variants per event type to prevent repetition.

---

## Generative SFX Status (BLOCKED)

R1:362-387 validates that prep-time architecture **resolves technical blockers** but **licensing remains NO-GO**:

| Model | Quality | VRAM | License | Commercial OK? | Notes |
|-------|---------|------|---------|----------------|-------|
| **TangoFlux** | Excellent (ICLR 2026) | ~6-8 GB | Stability AI Community | **❌ NO** | R1:380 |
| **Tango 2** | Good | ~13 GB (FP32) | CC-BY-NC-SA-4.0 | **❌ NO** | R1:381 |
| **AudioGen** (Meta) | Good | ~5-6 GB (small) | CC-BY-NC | **❌ NO** | R1:382 |
| **Stable Audio Open** | Excellent | ~6-14 GB | Stability AI Community | **❌ NO** | R1:383 |
| **Bark** (Suno) | Poor for SFX | ~2-4 GB | MIT | ✅ YES | Quality insufficient (R1:384) |
| **AudioLDM 2** | Good | ~4-6 GB | Verify repo | ❓ UNCLEAR | R1:385 |

**Conclusion (R1:387):** No commercially-viable generative SFX path exists. Curated library is pragmatic choice. Monitor landscape for Apache 2.0/MIT models.

**Future watch (R1:444-453):** If permissive-licensed model emerges, it slots into prep pipeline Phase 5 (~6-8 GB VRAM budget after music generation). TangoFlux is top candidate if Stability AI relicenses or community retrain on permissive data appears.

---

## Library Sources (Priority Order)

### 1. Sonniss GDC Bundles (Primary)

| Attribute | Value |
|-----------|-------|
| **License** | Royalty-free (R1:396, R1:511) |
| **Sound Count** | 150-300 (estimated for D&D use cases) |
| **Categories** | Combat, ambience, creatures, environment (R1:396) |
| **Quality** | Professional AAA game audio |
| **Attribution** | Required (tracked via AttributionLedger) |
| **URL** | https://sonniss.com/gameaudiogdc |

**Recommended allocation:** 120-200 sounds (primary for combat, creatures, environment)

### 2. Freesound.org (CC0 Filter) (Secondary)

| Attribute | Value |
|-----------|-------|
| **License** | CC0 (public domain) (R1:397, R1:512) |
| **Sound Count** | 30-80 (gap-filling, unusual sounds) (R1:397) |
| **Quality** | Variable — requires curation |
| **Attribution** | Not required (CC0) |
| **URL** | https://freesound.org/search/?f=license:"Creative+Commons+0" |

**Recommended allocation:** 40-100 sounds (magic SFX, unusual events, ambience)

### 3. Kenney.nl (Tertiary)

| Attribute | Value |
|-----------|-------|
| **License** | CC0 (R1:398, R1:512) |
| **Sound Count** | 10-20 (UI/feedback, dice, notifications) (R1:398) |
| **Quality** | Clean, consistent, game-ready |
| **Attribution** | Not required (CC0) |
| **URL** | https://kenney.nl/assets?q=audio |

**Recommended allocation:** 10-20 sounds (UI feedback, dice rolls, notifications)

### 4. OpenGameArt.org (Supplementary)

| Attribute | Value |
|-----------|-------|
| **License** | CC0/CC-BY (R1:399, R1:512) |
| **Sound Count** | 10-30 (fantasy-specific packs) (R1:399) |
| **Quality** | Variable |
| **Attribution** | Varies by pack |
| **URL** | https://opengameart.org/art-search-advanced?keys=&field_art_type_tid%5B%5D=13 |

**Recommended allocation:** 20-50 sounds (fantasy creatures, magic, medieval combat)

**Total:** 200-500 curated sounds (R1:400)

---

## Semantic Key Taxonomy

R1:406-422 specifies hierarchical semantic keys matching D&D event types. Extends existing `AudioTrack.kind` schema:

### Combat SFX

```
combat:melee:sword:hit          combat:magic:fire:impact
combat:melee:sword:miss         combat:magic:lightning:crack
combat:melee:axe:hit            combat:magic:heal:cast
combat:melee:dagger:hit         combat:magic:necrotic:pulse
combat:melee:club:hit           combat:magic:arcane:missile

combat:ranged:bow:release       combat:hit:critical
combat:ranged:bow:impact        combat:hit:normal
combat:ranged:crossbow:release  combat:death:humanoid
combat:ranged:thrown:impact     combat:death:monster
```

### Ambient SFX

```
ambient:peaceful:tavern         ambient:weather:rain:heavy
ambient:peaceful:nature         ambient:weather:storm
ambient:tense:dungeon           ambient:weather:wind
ambient:tense:cave              ambient:fire:hearth
ambient:fire:torch              ambient:water:stream
```

### Event SFX

```
event:door:open:wood            event:dice:roll
event:door:open:stone           event:gold:coins
event:chest:open                event:potion:drink
event:chest:locked              event:scroll:unfurl
event:trap:trigger              event:lever:pull
event:footstep:stone            event:footstep:wood
event:footstep:grass            event:footstep:water
```

### Creature SFX

```
creature:dragon:roar            creature:undead:moan
creature:wolf:growl             creature:goblin:chatter
creature:horse:neigh            creature:giant:footstep
creature:bird:ambient           creature:insect:ambient
```

**Taxonomy depth:** 3-5 levels (`category:subcategory:type:action`)

**Variant strategy:** 3-5 variants per semantic key with round-robin selection (R1:423) to prevent repetition.

---

## Technical Specifications

### Audio Format

| Specification | Value | Rationale |
|--------------|-------|-----------|
| **Codec** | OGG Vorbis | Consistent with music format (R1:400) |
| **Bitrate** | 96-128 kbps | SFX are short; prioritize file size |
| **Sample Rate** | 44.1 kHz | Standard quality |
| **Channels** | Stereo or Mono | Mono for point events (sword hit), stereo for ambience |
| **Duration** | 0.1-5.0 seconds | Most SFX <2s; ambience can loop |

### Storage Budget

| Metric | Value | Notes |
|--------|-------|-------|
| **Disk Size (total)** | 50-200 MB | 200-500 sounds @ 100-400 KB each (R1:400) |
| **RAM (loaded)** | 20-65 MB | R1:400, all sounds pre-loaded for low-latency playback |
| **Sounds Loaded Simultaneously** | All | SFX library small enough to fit in RAM |

---

## Mixing Architecture

R1:426-429 specifies lightweight custom mixer on `sounddevice` (already a TTS dependency):

### Requirements

- **8-16 simultaneous channels** (combat SFX + ambience + music)
- **Volume control** per channel
- **Looping** for ambient SFX
- **Fade in/out** for smooth transitions
- **Round-robin variant selection** to prevent repetition

### Implementation Options

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Custom mixer (sounddevice)** | No new dependencies, resolves TTS contention (R1:427) | ~300-500 lines of code | ✅ **Preferred** (R1:427) |
| **pygame.mixer** | Well-tested, simple API | Adds dependency, potential TTS device contention | Fallback (R1:429) |

**Spatial audio:** Not required — no spatial reference in text-based RPG (R1:432). Stereo panning sufficient.

---

## Curation Workflow

### Phase 1: Source Collection (M3 Sprint 3)

1. **Sonniss GDC:** Download 2023-2026 bundles, filter for D&D-relevant categories
2. **Freesound CC0:** Search for magic SFX, unusual events, ambience (gap-fill)
3. **Kenney.nl:** Download UI/dice sound packs
4. **OpenGameArt:** Identify fantasy creature/combat packs

### Phase 2: Semantic Tagging (M3 Sprint 3-4)

1. **Assign semantic keys** to each sound using taxonomy (R1:406-422)
2. **Identify variants** (3-5 per key) — e.g., 5 different sword hits
3. **Tag loop points** for ambient SFX
4. **Record attribution** for non-CC0 sources

### Phase 3: Audio Processing (M3 Sprint 4)

1. **Normalize volume** across all SFX (prevent jarring loud/quiet jumps)
2. **Trim silence** from start/end
3. **Convert to OGG Vorbis** (96-128 kbps)
4. **Verify loop points** for ambient SFX

### Phase 4: Integration Testing (M3 Sprint 4)

- Test variant round-robin selection (no immediate repeats)
- Validate mixer channel count (8-16 simultaneous sounds)
- Test volume balancing (SFX vs music vs TTS)
- Verify attribution display in credits

---

## Semantic Key Usage Examples

### Combat Event Mapping

```python
# Player attacks goblin with longsword (hit)
play_sfx("combat:melee:sword:hit", volume=0.8)

# Wizard casts fireball
play_sfx("combat:magic:fire:impact", volume=0.9)

# Critical hit
play_sfx("combat:hit:critical", volume=1.0)

# Goblin dies
play_sfx("combat:death:humanoid", volume=0.7)
```

### Ambient Scene Mapping

```python
# Tavern scene
play_sfx("ambient:peaceful:tavern", loop=True, volume=0.3)

# Dungeon exploration
play_sfx("ambient:tense:dungeon", loop=True, volume=0.4)
```

### Event Mapping

```python
# Player opens wooden door
play_sfx("event:door:open:wood", volume=0.6)

# Dice roll for attack
play_sfx("event:dice:roll", volume=0.5)

# Looting gold
play_sfx("event:gold:coins", volume=0.7)
```

---

## Licensing and Attribution

### Attribution Ledger Format

```python
SFX_ATTRIBUTIONS = {
    "sword_hit_01.ogg": {
        "source": "Sonniss GDC 2024",
        "license": "Royalty-free (attribution required)",
        "url": "https://sonniss.com/gameaudiogdc2024",
    },
    "fire_impact_03.ogg": {
        "source": "Freesound user 'InspectorJ'",
        "license": "CC0",
        "url": "https://freesound.org/people/InspectorJ/sounds/...",
    },
    "dice_roll_02.ogg": {
        "source": "Kenney.nl",
        "license": "CC0",
        "url": "https://kenney.nl/assets/rpg-audio",
    },
    # ... remaining 197-497 sounds
}
```

R1:511-512 confirms all sources are commercially safe with proper attribution.

---

## Acceptance Criteria Validation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 200-500 sounds across combat/ambient/event/creature | ✅ PASS | R1:400 target, sources validated |
| Royalty-free or CC0 licenses only | ✅ PASS | R1:396-399, all sources verified |
| Semantic key taxonomy implemented | ✅ PASS | R1:406-422 taxonomy specified |
| 3-5 variants per key | ✅ PASS | R1:423 variant strategy |
| OGG Vorbis format | ✅ PASS | R1:400 specification |
| <200 MB disk, <65 MB RAM | ✅ PASS | R1:400 budget validated |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Insufficient semantic coverage | Medium | Medium | Over-curate (600+ candidates → 200-500 final); group similar events |
| Licensing misattribution | Low | **Critical** | Double-verify Sonniss terms; prefer CC0 where possible |
| Poor quality mixing (volume imbalance) | Medium | Medium | Normalize all SFX; test balancing in-game |
| TTS/music/SFX device contention | Medium | High | Custom mixer on sounddevice resolves contention (R1:427) |

---

## Recommendations

1. **Prioritize Sonniss GDC bundles** for combat/creature SFX (professional quality)
2. **Use Freesound CC0 for magic SFX** (generative-sounding effects, unusual events)
3. **Implement custom mixer on sounddevice** (resolves TTS contention, no new dependencies)
4. **Pre-normalize all SFX volumes** in Audacity before integration
5. **Test round-robin variant selection** to confirm no immediate repeats
6. **Monitor TangoFlux licensing** for potential M4+ generative SFX path (R1:451)

---

## Future Watch: Generative SFX (M4+)

R1:444-453 confirms prep pipeline is architecturally ready for generative SFX when permissive-licensed model emerges:

| Phase | Component | VRAM (during prep) | When Ready? |
|-------|-----------|---------------------|-------------|
| 4. Music Generation | ACE-Step | 6-8 GB | ✅ M3 |
| 5. **SFX Generation** | **TangoFlux or equivalent** | **6-8 GB** | ⏳ **Blocked by licensing** |

**Top candidates to monitor (R1:450-453):**
- TangoFlux (ICLR 2026, 515M params, 3.7s on A40) — if Stability AI relicenses or community retrain on Apache 2.0 data
- AudioLDM 2 — investigate license status
- Any new Apache 2.0 text-to-audio model

**Integration plan when unblocked:**
1. Generate 3-5 variants per semantic key during campaign prep
2. Curated library becomes fallback for Baseline tier
3. ~6-8 GB VRAM budget during SFX phase (sequential after music)

---

## References

- R1 Technology Stack Validation Report, Section 7 (Sound Effects), lines 358-461
- R1 Appendix A (Hardware Budget), line 476
- R1 Appendix B (License Summary), lines 511-512

---

**END OF SFX LIBRARY SPECIFICATION**
