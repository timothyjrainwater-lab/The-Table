# GPT Instance 2 — D&D 3.5e Rules Compliance

Append this to the end of SYSTEM_PROMPT_FOR_GPT.md when running this instance.

---

## YOUR ANALYTICAL LENS: D&D 3.5e Mechanical Correctness

Focus your analysis on **D&D 3.5e rule fidelity, 5e contamination risks, missing RAW coverage, and mechanical systems that are specified but may be incorrectly implemented.**

Specifically investigate:

1. **5e Contamination Vectors** — The project explicitly forbids 5e mechanics. But 5e is the dominant version in LLM training data. Where might Qwen3 produce 5e-style output? Advantage/disadvantage instead of circumstance bonuses? Proficiency bonus instead of BAB? Short/long rest instead of 3.5e rest rules? What detection mechanisms exist beyond KILL-002?

2. **Missing Core Mechanics** — The feat system (WO-034) lists 15 feats. D&D 3.5e PHB has ~100+ feats. What's the coverage strategy? Which feats are combat-critical that aren't in the list? Same for skills — 7 of 36+ skills are planned. Which missing skills break common gameplay scenarios?

3. **Spellcasting Gaps** — WO-036 expands from 17 to ~50 spells covering levels 0-5. D&D 3.5e has hundreds. What's the prioritization logic? Are spell interactions handled (counterspell, dispel magic targeting rules, spell resistance)? How does the system handle spells that modify combat rules (haste gives extra attack, slow halves actions)?

4. **Action Economy** — D&D 3.5e has standard action, move action, full-round action, swift action, immediate action, free action. The play_loop.py handles some of these. Are all action types tracked? Can a character take a 5-foot step + full attack? Are full-round actions correctly distinguished from standard+move?

5. **Saving Throw Mechanics** — Are save DCs calculated correctly per 3.5e (10 + spell level + ability mod)? Do save bonuses include all 3.5e sources (base save, ability mod, resistance bonus, luck bonus, morale bonus)? Do bonus types stack correctly per 3.5e stacking rules (same type doesn't stack, different types do)?

6. **Condition Interactions** — 16 condition types are implemented. D&D 3.5e has complex condition interactions (stunned implies flat-footed, paralyzed implies helpless, helpless allows coup de grace). Are all cascading condition implications tracked?

7. **Multi-class and Prestige Class** — WO-037 (XP/Leveling) mentions multi-class XP penalties. But are multi-class characters supported in the entity schema? Can an entity have Fighter 5/Wizard 3? Do BAB progressions stack correctly across classes?

8. **Equipment and Weapons** — The weapon system appears minimal (attack_resolver.py has a hard-coded range). Is there a weapon schema? Do weapon properties (finesse, reach, double, thrown, two-handed) affect combat resolution correctly? What about magic weapon bonuses, enhancement bonuses, and the +1/+2/+3 progression?

9. **Grapple, Bull Rush, Overrun, Sunder, Disarm, Trip** — Six special maneuver types exist. Are they following 3.5e's notoriously complex grapple rules? Or simplified? If simplified, what's the deviation from RAW?

10. **Turn Undead, Bardic Music, Rage** — Class features that fundamentally change combat. Are any of these in scope? If not, how does the system handle a Barbarian PC or a Cleric attempting to turn undead?

For each finding, classify as:
- **Missing mechanic** — RAW exists but system doesn't implement it
- **Potential misimplementation** — Mechanic exists but may not match 3.5e RAW
- **5e contamination risk** — Area where LLM training data could inject 5e rules
- **Scope question** — Unclear whether this is in-scope for current milestones
