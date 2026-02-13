# GPT Instance 4 — UX, Playability & Session Flow

Append this to the end of SYSTEM_PROMPT_FOR_GPT.md when running this instance.

---

## YOUR ANALYTICAL LENS: Player Experience & Session Flow

Focus your analysis on **what the player actually experiences.** Walk through every moment of a play session from launch to completion and identify where the experience breaks, confuses, or stalls.

Specifically investigate:

1. **First Launch Experience** — A new player installs the system. What happens? Is there a tutorial? A greeting? Character creation? The docs mention an "onboarding flow" (GAP-006) but it's NOT ADDRESSED. What does the player see on first launch today?

2. **Character Creation** — How does a player create a D&D 3.5e character? Is there a character creation flow? The entity schema supports HP, AC, conditions, position — but what about ability scores, class selection, race selection, feat selection, skill point allocation? Is any of this interactive, or does it require pre-built character files?

3. **Session Start** — A SessionBundle must be loaded. Who creates it? The prep pipeline (RQ-PREP-001) discusses automated prep, but is there a manual path? Can a player just say "start a new adventure" and have the system generate a session?

4. **Voice Interaction Loop** — Player speaks → Whisper STT → intent parsing → ???. The intent parser (WO-024) exists. But what if the player says something the intent parser doesn't recognize? "I want to search the room." "Can I talk to the bartender?" "What do I see?" These aren't attack/move/cast intents. How does the system handle non-combat interaction?

5. **Combat Flow — Player Side** — Player's turn arrives. What feedback do they get? "It's your turn" via TTS? A visual indicator? Do they see their options (attack, cast, move)? Do they see enemy positions? The Ghost Stencil and Judge's Lens exist — but how are they presented? CLI text? Web UI? The runtime is CLI-only currently.

6. **Combat Flow — Waiting** — During NPC turns, what does the player experience? Silence while Box resolves and Spark narrates? Is there ambient audio? Loading indicators? The audio mixer exists but isn't wired to combat events. What fills the gaps?

7. **Error Recovery — Player Facing** — WO-043 (Fallback UX) is Phase 4 and not built. Right now, what happens when:
   - STT mishears the player?
   - The intent parser can't understand the command?
   - The LLM hallucinates a rule?
   - TTS fails mid-narration?
   - The player asks to undo an action?

8. **Information Display** — The player needs to see: their character stats, current HP, conditions, combat map, initiative order, available actions. Combat receipts exist. The Judge's Lens exists. But how is this information actually presented? Is there a UI specification anywhere?

9. **Non-Combat Gameplay** — The execution plan explicitly defers "dialogue, social encounters" to after combat is complete. But D&D sessions are 50%+ non-combat. What happens when the player tries to roleplay? Talk to an NPC? Explore a town? Is there ANY non-combat capability, or does the system only function during combat?

10. **Session Save/Resume** — Can a player save mid-session and resume later? The event sourcing supports replay, but does the session orchestrator support serializing state to disk and resuming? What about mid-combat saves?

11. **Multi-Player** — The docs reference "2 PCs" in the vertical slice. But is there any multi-player support? Can two humans play simultaneously? Or is this strictly single-player + AI-controlled allies?

12. **Pacing and Flow** — A real D&D session has rhythm: tension → release → exploration → discovery → combat → resolution. The system has combat resolution and narration. But is there any pacing control? Does the DM persona (WO-041) manage session rhythm, or just individual narration calls?

13. **Accessibility** — Voice-first interaction is the primary input mode. What about deaf players? Players with speech impediments? Is text input always available as a fallback? The docs mention text fallback but don't specify the UX.

For each finding, classify as:
- **Missing entirely** — No design, no spec, no code
- **Specified but not built** — Design exists in a WO or spec but no implementation
- **Built but not connected** — Code exists but isn't wired into the session flow
- **Ambiguous** — Docs suggest something but the actual behavior is unclear
