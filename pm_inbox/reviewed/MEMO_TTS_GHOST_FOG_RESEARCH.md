# MEMO: TTS Ghost Fog — Reference Clip Acoustic Space Research
**From:** Anvil (BS Buddy session)
**Date:** 2026-02-19
**Status:** Complete
**Lifecycle:** NEW

---

## Summary

`orc_troll__ref_b.wav` produces a "spectral fog" acoustic quality when used as a Chatterbox reference clip. The fog is baked into the clip's acoustic space (reverb, room characteristics from original recording), NOT a Chatterbox artifact. Other monster refs produce completely different character voices through the same pipeline. This is controllable and usable as a ghost/undead voice register.

## Key Findings

### 1. Fog Is Ref-Specific

| Ref Clip | Duration | Character | Fog? | Thunder Verdict |
|---|---|---|---|---|
| `orc_troll__ref_b.wav` | 6.00s | Spectral, distant, "through the fog" | **YES** | "Straight ghost material" |
| `orc_troll__ref_a.wav` | 4.40s | Indian accent, warm, present | No | "Cool accent tone" — exotic NPC |
| `orc_encounter__composite_ref.wav` | 7.70s | Deep, grounded, commanding | No | "Perfect Ogre Warrior" |

The fog is unique to ref_b. Chatterbox faithfully reproduces the reference clip's full acoustic environment — room, reverb, speaker identity, accent — not just timbre.

### 2. Exaggeration Controls Ghost Intensity

| Exaggeration | Effect on Fog | Best For |
|---|---|---|
| 0.15 | Maximum ethereal quality — flat, disconnected, centuries-dead | Ancient ghosts, whispers |
| 0.3–0.4 | Haunting with emotional undertone | Named ghost NPCs with personality |
| 0.5 | Clean speech through fog — "studio vibe" | General spectral register |
| 0.6 | Noble/dramatic ghost | Ghost kings, fallen heroes |
| 0.7+ | Emotional energy overpowers fog — "happy ghost" | NOT recommended for undead |

**Sweet spot: 0.15–0.4 for ghosts.** Lower = more dead.

### 3. Text Carries Character, Fog Carries Atmosphere

The ref clip defines the acoustic space. The text defines the emotional payload. These are independent axes:
- Same fog ref + sarcastic text = sarcastic ghost
- Same fog ref + mournful text = mournful ghost
- Same fog ref + heroic text = noble ghost

Writing quality matters more than persona selection for ghost character.

### 4. Timing Data (RTX 3080 Ti)

| Metric | Value |
|---|---|
| Sampling speed (single run) | 38–40 it/s |
| Sampling speed (parallel/contention) | 20–28 it/s |
| Early stop for 1–2 sentences | 12–17% of 1000 steps |
| Actual gen time (short line) | 3–4 seconds sampling |
| Model load (first call) | Additional overhead (CUDA init + weights) |
| `HF_HUB_OFFLINE=1` | **Required** — skips HuggingFace HEAD requests that timeout through proxy |

### 5. Three Monster Voice Registers Discovered

| Register | Ref Clip | Exaggeration | Use Case |
|---|---|---|---|
| **Spectral** | `orc_troll__ref_b.wav` | 0.15–0.4 | Ghosts, undead, spectral entities |
| **Exotic NPC** | `orc_troll__ref_a.wav` | 0.3–0.5 | Foreign merchants, distant lands NPCs |
| **Monster Warrior** | `orc_encounter__composite_ref.wav` | 0.4–0.6 | Orcs, ogres, living monsters |

## Test Log (13 runs)

| # | Ref | Persona | Exagg | Text (short) | Steps | it/s | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | ref_b | dm_narrator | 0.5 | "The dead do not welcome visitors" | ~1000 | ~35 | Fog, clean, "studio vibe" |
| 2 | ref_b | npc_male | 0.4 | "Remember what was lost" | ~1000 | ~35 | **"Hit hard"** — BEST |
| 3 | ref_b | dm_narrator | 0.5 | "The walls remember" (half vol) | ~1000 | ~35 | Fog present |
| 4 | ref_b | heroic | 0.6 | "I was a king once" | ~1000 | ~35 | "Pretty good" — noble ghost |
| 5 | ref_b | villainous | 0.7 | "You will join us" | ~1000 | ~25 | Overlapped (parallel batch) |
| 6 | ref_b | villainous | 0.7 | Sarcastic cleric roast | ~1000 | ~25 | Overlapped |
| 7 | ref_b | npc_male | 0.4 | Meta death save complaint | ~1000 | ~25 | Overlapped |
| 8 | ref_b | npc_young | 0.5 | Panicked 40yr ghost | ~1000 | ~25 | Overlapped |
| 9 | ref_b | heroic | 0.6 | "I was a king once" (replay) | FAIL | — | HF connection timeout |
| 10 | ref_b | npc_male | 0.15 | Sunlight line (2 sentences) | 168 | 38.4 | **"Straight ghost material"** |
| 11 | ref_b | heroic | 0.7 | Military funeral (3 sentences) | 121 | 39.4 | "Happy ghost" — too much energy |
| 12 | ref_a | npc_male | 0.3 | Sunlight line (2 sentences) | 161 | 38.6 | Indian accent — exotic NPC |
| 13 | composite | npc_male | 0.3 | Sunlight line (2 sentences) | 160 | 38.5 | **"Perfect Ogre Warrior"** |

## Operational Notes

- **Always use `HF_HUB_OFFLINE=1`** when running speak.py tests — prevents HuggingFace HEAD request timeouts through Clash proxy.
- **Never fire parallel TTS tests** — they overlap on playback (winsound is blocking per-process but parallel processes stack audio). Run sequentially.
- Composite ref triggers mel alignment warning (`Reference mel length is not equal to 2 * reference token length`) — still generates, but worth noting for longer clips.
- Early stopping percentage inversely correlates with text length — shorter text stops earlier (12–17%), longer text runs further into the 1000 steps.

## Next Steps (if pursued)

1. Formalize "spectral" as a persona in the emotion router with ref_b as default reference
2. Test cfg_weight variations (currently hardcoded 0.5) to see if favoring reference vs text changes fog density
3. Test speed parameter (0.7–0.9) for slow, deliberate ghost delivery
4. Record purpose-built ghost ref clips (whispered, reverb-heavy) for even more spectral control
