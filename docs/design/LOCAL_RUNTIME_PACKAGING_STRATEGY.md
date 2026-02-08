# Local Runtime Packaging Strategy
## Delivering a Self-Contained, Trustworthy Tabletop World on One Machine

**Document ID:** LRP-001
**Version:** 1.0
**Status:** ADOPTED
**Scope:** Delivery · Runtime Architecture · Portability · Durability

**Project:** AIDM — Deterministic D&D 3.5e Engine + Local Open-Source LLM
**Document Type:** Core Delivery & Runtime Architecture

---

## 1. PURPOSE

This document defines how the entire AIDM system is:

- Executed locally on a single machine
- Packaged as a coherent, durable artifact
- Isolated from external policy or infrastructure changes
- Shareable without loss of fidelity
- Replayable years later with identical results

This is the **delivery contract** for the project.

---

## 2. CORE NON-NEGOTIABLE PRINCIPLE

> **If the machine is offline, the game still works.**

No component may:
- Require cloud access
- Depend on remote policy enforcement
- Change behavior based on external updates

Trust requires locality.

---

## 3. RUNTIME COMPONENTS (LOGICAL)

The system consists of five cooperating local components:

### 3.1 Deterministic Rules Engine
- Pure logic
- Event-sourced
- Replay-safe
- No network access

This is the mechanical authority.

---

### 3.2 Local Open-Source LLM Runtime
- Fully local inference
- Weights stored on disk
- Configurable parameters
- No outbound calls

This is the creative DM mind.

---

### 3.3 Voice I/O Subsystem
- Local speech-to-text (STT)
- Local text-to-speech (TTS)
- Hot-swappable adapters
- Optional (system degrades to text if unavailable)

Voice is an interface, not a dependency.

---

### 3.4 UI Renderer (Character Sheet + Board)
- Character sheet as primary UI
- Minimal board for spatial anchoring (contextual, not always-on)
- No game logic in UI

UI reflects state; it does not create it.

---

### 3.5 World & Campaign Store
- Event logs
- World state snapshots
- Ruleset manifests
- Session Zero configs
- Prepared campaign assets

This is the memory of the world.

---

## 4. PROCESS ISOLATION & BOUNDARIES

### 4.1 Hard Boundaries Between Components

Each component must:
- Communicate only through explicit contracts
- Never share mutable state directly
- Be restartable independently

This prevents:
- State corruption
- Hidden authority
- Debugging nightmares

---

### 4.2 LLM Containment at Runtime

The LLM:
- Receives only the context it needs
- Never accesses raw engine internals
- Never mutates world state directly
- Never alters logs

It speaks; it does not act.

---

## 5. LOCAL EXECUTION MODEL

### 5.1 Single-Host Execution
All components run on the same machine, either:
- as separate local processes, or
- within a single orchestrated runtime

Choice of implementation is flexible, but locality is not.

---

### 5.2 Resource Awareness
The system must:
- Detect hardware limits
- Allow model size selection
- Degrade gracefully (e.g., text-only if voice unavailable)

No hard dependency on "high-end" hardware.

---

## 6. HARDWARE TIERS & MINIMUM REQUIREMENTS

### 6.1 Hardware Tiers

| Tier | LLM Size | RAM | Storage | GPU |
|------|----------|-----|---------|-----|
| Minimum | 7B (quantized) | 16GB | 20GB | Optional (CPU inference) |
| Recommended | 13B | 32GB | 40GB | 8GB VRAM |
| Enhanced | 30B+ | 64GB+ | 80GB+ | 16GB+ VRAM |

### 6.2 Graceful Degradation

If hardware is insufficient for the selected model tier:
- System recommends a smaller model
- Voice features may be disabled
- Image generation may be disabled or use smaller models
- Core engine functionality is never compromised

---

## 7. PACKAGING FORMAT

### 7.1 Distribution Unit

The system must be distributable as:
- A single installer
- Or a single directory bundle

Containing:
- Engine binaries/code
- LLM runtime + weights (or installer hooks)
- UI assets
- Default configs
- Documentation

---

### 7.2 Version Pinning

Each distribution must pin:
- Engine version
- LLM model + weights
- Voice adapters
- Ruleset baseline

This ensures:
- Old campaigns remain playable
- Replays remain valid

---

## 8. VOICE ADAPTER SELECTION

### 8.1 Pluggable Architecture

Voice adapters (STT and TTS) are:
- Configurable at install or runtime
- Selectable from available options
- Swappable without engine changes

### 8.2 Selection Mechanism

The system provides:
- A list of available adapters (bundled or detected)
- Configuration UI or file for selection
- Fallback to text mode if no adapter is available

Voice is a presentation layer, not a core dependency.

---

## 9. WORLD SHAREABILITY & PORTABILITY

### 9.1 What Constitutes a "World"

A world consists of:
- Session Zero ruleset config
- Campaign content (prepared assets)
- Event log
- Current state snapshot

Nothing else.

---

### 9.2 World Export/Import

Worlds must be:
- Exportable as a single archive
- Importable without modification
- Playable on another machine with identical behavior

This is how DMs "share a table."

---

### 9.3 World Contents

A world archive includes:
- Structured intent and event logs (authoritative)
- Prepared visual and audio assets
- Session Zero configuration

LLM raw conversation history is **optional**, not required.
Mechanical state is always reconstructible from the event log.

---

## 10. ENGINE UPGRADE PATH

### 10.1 Forward Compatibility

Engine upgrades are permitted provided:
- Event log format remains backward-compatible
- Engine version is pinned per campaign
- Old campaigns specify their engine version
- Replays use the original engine version

### 10.2 Campaign Migration

Campaigns may be migrated to new engine versions if:
- A migration path is explicitly defined
- The migration is logged
- The original event log is preserved

---

## 11. LONG-TERM DURABILITY

### 11.1 Surviving Time

The system must assume:
- Models change
- Hardware changes
- Companies disappear

Therefore:
- No opaque binary formats without specs
- No cloud dependencies
- No "phone home" logic

A campaign started today should be playable in 10+ years.

---

## 12. SECURITY & TRUST MODEL

### 12.1 Player Sovereignty
- The user owns their data
- The user owns their worlds
- The user controls the runtime

No telemetry.
No analytics.
No hidden uploads.

---

## 13. ASSET MANAGEMENT

### 13.1 Campaign Assets

Prepared visual and audio assets are:
- Stored with the campaign
- Reused across sessions within that campaign
- Included in world exports

### 13.2 Shared Assets

Generic assets (common location types, standard sound effects) may be:
- Shared across campaigns to reduce preparation time
- Bundled with the distribution
- Not required for mechanical correctness

### 13.3 Audio Sourcing

Audio may be:
- Generated locally
- Sourced from bundled asset libraries
- A combination of both

Licensing and attribution requirements for bundled audio must be respected.
Audio sourcing may differ from image generation in implementation.

---

## 14. FAILURE MODES THIS STRATEGY PREVENTS

Without this strategy:
- Behavior changes unexpectedly
- Campaigns rot
- Trust erodes

With this strategy:
- Worlds are stable
- Stories persist
- The system becomes a *place*, not a service

---

## 15. SUMMARY OF NON-NEGOTIABLES

1. Fully local execution
2. Open-source LLM runtime
3. No external authority
4. Explicit component boundaries
5. Portable, replayable worlds
6. Long-term durability
7. Graceful hardware degradation
8. Engine upgrades preserve replay fidelity

---

## 16. FINAL NOTE

This strategy exists to ensure that the AIDM system is not just *used*,
but *kept*.

A tabletop world should not expire.

---

## END OF LOCAL RUNTIME PACKAGING STRATEGY
