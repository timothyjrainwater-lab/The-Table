# MEMO: Builder Preflight Canary — Minimum Viable Image + Voice Validation

**From:** Slate (PM), incorporating Aegis (GPT) advisory
**To:** Builders, Anvil (BS Buddy), Thunder
**Date:** 2026-02-19
**Lifecycle:** APPROVED
**Subject:** One script, two canaries, manual log. No new frameworks.

---

## Intent

Every builder runs a first-act ritual before touching code:

1. Generate one image and one voice line (prove the pipelines work)
2. Generate one random image and one random voice line (prove prompt competency)
3. Log the results in a markdown file

No smoke suite. No enforced gates. No telemetry. No scratch namespaces. Ships now.

---

## What Ships Now

### 1. `scripts/preflight_canary.py` — One Script, Two Canaries

Runs two standardized pipeline checks:

**Image canary:**
- Fixed prompt: "A dwarf blacksmith at a forge, hammer raised, sparks flying, oil painting style"
- Fixed semantic_key: `canary:image:v1`
- Run 1: expect `status="generated"`
- Run 2: expect `status="cached"`, same `content_hash`
- Print: PASS/FAIL, content_hash, output path

**Voice canary:**
- Fixed text: "The forge is lit. Steel meets hammer. The work begins."
- Fixed persona: `dm_narrator`
- Run 1: expect success (audio plays)
- Run 2: expect success (audio plays)
- Print: PASS/FAIL

No VRAM telemetry. No machine ID. The goal is: "can I generate twice and observe stable behavior."

### 2. `pm_inbox/PREFLIGHT_CANARY_LOG.md` — Manual Log

Each builder appends one entry per session. Template format provided below.

### 3. Builder First-Act Artifacts (After Canaries Pass)

- **1 random portrait** using image methodology (`pm_inbox/MEMO_IMAGE_GEN_WALKTHROUGH.md`). Any subject. No prompts provided.
- **1 random voice line** using TTS methodology (`pm_inbox/MEMO_TTS_MONOLOGUE_WALKTHROUGH.md`). Any character. No script provided.

These are not gated. They are appended to the same log with file paths.

---

## What Does NOT Ship Now (Explicitly Deferred)

- Smoke suite framework
- Onboarding system enforcement
- Scratch namespace implementation
- Automated rubric scoring
- VRAM/runtime telemetry
- Oracle integration
- Portrait Card telemetry format

After 3-5 builders have run this manually, we decide whether to harden into real gates.

---

## Success Signals

1. `scripts/preflight_canary.py` exists and runs on the dev machine
2. It generates image + voice canaries twice each and prints clear PASS/FAIL
3. `pm_inbox/PREFLIGHT_CANARY_LOG.md` exists with a template entry
4. Builder onboarding checklist (Step 2.5) describes the ritual: run script → append to log → generate one random image + one random voice artifact

---

## Methodology References

- Image prompt rules: `pm_inbox/MEMO_IMAGE_GEN_WALKTHROUGH.md`
- Voice pipeline walkthrough: `pm_inbox/MEMO_TTS_MONOLOGUE_WALKTHROUGH.md`
- Persona registry: `aidm/immersion/chatterbox_tts_adapter.py` lines 45-119
- Reserved profiles (off-limits for random artifacts): `npc_elderly` (Mrs. Slate), Arbor signal reference, `builder_signal` (Builder Herald)

---

*End of memo.*
