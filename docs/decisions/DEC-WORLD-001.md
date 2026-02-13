# DEC-WORLD-001: Worlds Are Compiled, Frozen, and Hashed

**Status:** PROPOSED
**Author:** PM (Opus)
**Date:** 2026-02-12
**Scope:** World bundle lifecycle — compile → freeze → load
**Supersedes:** None (new decision)
**Blocked by:** AD-007 (Presentation Semantics — RATIFIED)

---

## Decision

**Worlds are offline-compiled artifacts. Once compiled, a world bundle is
frozen and integrity-hashed. Runtime cannot mutate it. Campaigns inherit it
unchanged. Modifications require recompilation to a new world.**

---

## Context

The creation stack (RQ-PRODUCT-001 §8, MANIFESTO §"Creation Stack") defines
Level 1 (World) as the expensive compilation step where names, rules,
geography, and presentation semantics are generated and frozen. Everything
above this layer (campaigns, storylines, sessions) inherits the world's
vocabulary, map, and rulebook without modification.

Without a formal compile/freeze decision, the boundary between "world
authoring" and "runtime mutation" is undefined. This creates risks:

- World identity could drift across sessions (same world_id, different content)
- Replay would fail if world facts changed between sessions
- Campaigns in the same world could see different rulebooks
- Provenance chains would be broken (what was the world when this event happened?)

---

## Decision Details

### 1. Compile Model

The World Compiler is an **offline pipeline** that takes:
- Content pack (mechanics + behavioral contracts)
- World theme brief (genre, tone, naming style)
- Seed (deterministic RNG root)
- Pinned toolchain (model IDs, versions)

And produces a **Frozen World Bundle**: a directory of JSON files containing
the world's lexicon, rulebook, bestiary, map seeds, presentation semantics,
asset pool definitions, and integrity hashes.

### 2. Freeze Semantics

Once `world_manifest.json` is written (the final step of compilation), the
bundle is **immutable**:
- No file may be added, removed, or modified
- No field in any JSON file may be changed
- Runtime loads the bundle read-only
- Any mutation attempt is a hard failure

### 3. Hash Integrity

Every file in the bundle is SHA-256 hashed. A root hash is computed from all
file hashes. The root hash is recorded in both `bundle_hashes.json` and
`world_manifest.json`. On load, runtime verifies the root hash. If it doesn't
match, the bundle is rejected.

### 4. No Patching

If a world needs to change, it must be recompiled to a new `world_id`. The old
world remains valid and playable. Campaigns reference a specific `world_id`
and verify the root hash on load. There is no in-place patching.

### 5. Campaign Inheritance

Campaigns reference a `world_id`. On creation, the campaign records the world's
`root_hash`. On every session load, the campaign verifies the hash. The
campaign inherits:
- Lexicon (all ability/spell/creature names)
- Rulebook (all rulebook entries)
- Bestiary (all creature entries)
- Map (all regions, countries, cities, governments)
- Presentation semantics (all AD-007 bindings)

The campaign adds local detail (NPCs, plot hooks, session logs) but does not
modify anything it inherited from the world.

---

## Consequences

### Positive
- **Determinism**: Same world_id + same root_hash = guaranteed identical world
- **Replay safety**: World facts never change; replay is always valid
- **Cross-campaign consistency**: All campaigns in a world see identical rules
- **Provenance**: Every world fact traces to compile inputs (seed + theme + pack)
- **Local-first**: World is a local directory; no service dependency

### Negative
- **Recompile cost**: Bug fixes require full recompile (new world_id)
- **Migration friction**: Moving a campaign to a new world is a manual decision
- **Storage**: Multiple world versions coexist (no in-place update)

### Accepted Trade-offs
The recompile cost is accepted. The PO's design explicitly frames world
creation as expensive ("come back in hours"). The benefit of guaranteed
immutability and replay safety outweighs the cost of occasional recompilation.

---

## Alignment

| Principle | How This Decision Aligns |
|-----------|-------------------------|
| No-Opaque-DM | World is inspectable; every fact traces to compile inputs |
| Determinism | Same inputs → same bundle bytes |
| Fail-closed | Corrupt bundle → rejected on load; no partial loading |
| Local-first | Bundle is a local directory |
| Content independence | World names are generated, not copied from D&D |
| AD-007 | Presentation semantics frozen in bundle |
| BL-020 | Same immutability principle, extended to file level |

---

## Related Decisions

- **AD-007** (Presentation Semantics): Defines the Layer B schema that the
  world compiler generates and freezes.
- **BL-020** (WorldState Immutability): Defines the runtime immutability
  pattern. DEC-WORLD-001 extends this pattern to the world bundle.
- **RQ-PRODUCT-001** (Content Independence): Defines the creation stack.
  DEC-WORLD-001 formalizes Level 1's compile/freeze behavior.

---

*This decision record formalizes what the MANIFESTO and RQ-PRODUCT-001 already
describe informally: worlds are compiled, frozen, and hashed. It elevates this
from an implied architectural assumption to an explicit, testable decision.*
