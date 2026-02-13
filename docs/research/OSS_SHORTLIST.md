# OSS License / Fit Audit — Approved Shortlist

**Document ID:** WO-AUDIT-OSS-001
**Date:** 2026-02-12 (expanded 2026-02-13)
**Status:** Draft for PO review
**Sources:** Opus agent research sweep (6 domains) + Jay's ChatGPT research sessions (2 batches)

---

## Doctrine Constraints (Summary)

Any OSS component integrated into AIDM must satisfy:

1. **License:** MIT, BSD, or Apache-2.0. GPL is disqualified (viral).
2. **Determinism:** Must not break replay invariants. Any RNG must accept seeded injection or be bypassable.
3. **Boundary Law compliance:** Must not violate Box/Lens/Spark authority separation. Components touching `aidm/core/` must be pure-deterministic.
4. **Dependency weight:** Prefer zero-dep or single-dep. No transitive GPL. No mandatory network calls.
5. **Python:** >=3.10 required. C extensions acceptable if binary wheels ship for Windows/macOS/Linux.

**Existing stack context:** Python 3.10+, numpy, msgpack, pyyaml, Pillow, opencv-python-headless, pytest. Custom `RNGManager` (SHA-256 stream derivation). Custom `EventLog` (append-only). Custom geometry schemas (`GridCell`, `Position`, `PropertyMask`). Kokoro/Chatterbox TTS adapters producing 16-bit PCM WAV bytes.

---

## Bucket 1: Dice

> Current state: `aidm/core/rng_manager.py` handles seeded PRNG streams via `stdlib.random`. Dice expressions are evaluated inline (e.g. `rng.stream("attack").randint(1, 20)`). No notation parser exists.

### 1.1 `d20` (avrae/d20)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/avrae/d20 |
| License | **MIT** |
| Stars | ~137 |
| Deps | `lark` (parser generator) |
| Status | Stable (last commit 2022-11; author considers it done) |

**What we'd reuse:** Grammar-based dice notation parser (`4d6kh3`, `2d20kl1`, exploding dice, value annotations like `1d6+3 [fire]`). AST-based roll results give full audit trail per roll.

**Why it fits doctrine:** MIT license. AST output is ideal for event log provenance (every roll decomposed). Battle-tested by Avrae Discord bot (hundreds of thousands of users). Single dependency (`lark`) is also MIT.

**Red flags:** No built-in RNG injection — uses `random.randrange()` directly. Requires monkey-patching `Die._add_roll()` or seeding `random` globally. 6 open issues, no active maintenance (but stable). Workaround is ~5 lines of code.

**Recommendation:** **Adopt** (with thin RNG wrapper). Best notation coverage for D&D. Patch cost is trivial.

### 1.2 `dice` (borntyping/python-dice)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/borntyping/python-dice |
| License | **MIT** |
| Stars | ~88 |
| Deps | `pyparsing` |
| Status | Finished (author declared done, bugfixes only) |

**What we'd reuse:** Dice notation parser with exploding, keep-highest/lowest, reroll, wild dice. CLI tool.

**Why it fits doctrine:** MIT license. **First-class `random=` kwarg** — pass any `random.Random`-compatible object through the entire evaluation pipeline. Zero monkey-patching needed for deterministic replay.

**Red flags:** Smaller community than `d20`. Notation slightly less D&D-idiomatic (`h`/`l` vs `kh`/`kl`). Author has stopped development.

**Recommendation:** **Adopt** (alternative to d20). Best RNG injection contract. If replay determinism is the top priority and we don't want to patch `d20`, this is the pick.

### 1.3 `dyce` (posita/dyce)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/posita/dyce |
| License | **MIT** |
| Stars | ~41 |
| Deps | Zero (pure Python) |
| Status | Active (v0.6.2, last push Aug 2024) |

**What we'd reuse:** Exact probability enumeration (histograms, pools). Useful for validating our roller's output distributions, not for runtime rolling.

**Why it fits doctrine:** MIT, zero deps, RNG injectable via `dyce.rng.RNG` global swap.

**Red flags:** **No string notation parser.** Dice are constructed programmatically only (`H(6)` for 1d6). Pre-1.0 API. Small community (41 stars).

**Recommendation:** **Mine ideas** (probability analysis companion). Not a runtime roller. Could validate RNG distribution correctness in test harness.

### 1.4 `xdice` (olinox14/xdice)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/olinox14/xdice |
| License | **GPL-3.0** |
| Stars | ~11 |

**Recommendation:** **Reject.** GPL-3.0 is disqualified per doctrine constraint #1.

### 1.5 `icepool` (HighDiceRoller/icepool)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/HighDiceRoller/icepool |
| License | **MIT** |
| Stars | ~68 |
| Deps | Zero (pure Python) |
| Status | Actively maintained (last push Feb 2026) |

**What we'd reuse:** Exact probability computation for game design validation. Academic-quality algorithms.

**Red flags:** Probability-focused, not a runtime roller. No notation parser. Requires Python 3.10+.

**Recommendation:** **Mine ideas** (test-harness probability oracle). Same niche as dyce but more actively maintained.

### Dice Bucket Summary

| Candidate | License | RNG Injection | Notation Parser | Recommendation |
|-----------|---------|---------------|-----------------|----------------|
| **d20** | MIT | Patch needed (~5 LOC) | A+ (D&D native) | **Adopt** |
| **dice** | MIT | First-class (`random=`) | A (solid) | **Adopt** (alt) |
| dyce | MIT | Global swap | None | Mine ideas |
| xdice | GPL-3.0 | N/A | A+ | **Reject** |
| icepool | MIT | N/A | None | Mine ideas |

---

## Bucket 2: Grid

> Current state: `aidm/schemas/geometry.py` (426 lines) provides `GridCell`, `PropertyMask`, `Direction`, `SizeCategory`. `aidm/schemas/position.py` provides `Position` with adjacency/distance. Custom LOS resolver (`test_los_resolver.py` — 43+ tests), cover resolver, AoE rasterizer (`test_aoe_rasterizer.py` — 53+ tests), flanking geometry, reach resolver all exist. Pathfinding is the main gap.

### 2.1 `python-tcod` (libtcod)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/libtcod/python-tcod |
| License | **BSD-2-Clause** |
| Stars | ~466 (python-tcod) / ~1,139 (libtcod C core) |
| Deps | numpy, cffi (C library bundled in wheel) |
| Status | Actively maintained (v20.0.0, Feb 2026) |

**What we'd reuse:** A* and Dijkstra pathfinding on 2D grids. Dijkstra flood-fill maps for "how far can this creature move?" queries. Multiple FOV algorithms (recursive shadowcasting, diamond raycasting, permissive FOV) — though we already have a custom LOS resolver.

**Why it fits doctrine:** BSD-2 license. NumPy-native grid representation matches our existing `numpy` dependency. Dijkstra2D for movement flood-fill is the main feature we lack. Configurable diagonal costs can model D&D 3.5e's 5/10/5/10 rule.

**Red flags:** Bundles full libtcod C library (~2-5 MB wheel) including a terminal emulator we will never use. The older `libtcodpy` API is deprecated. No built-in AoE shape primitives (but we already have our own rasterizer).

**Recommendation:** **Adopt** (pathfinding + Dijkstra flood-fill). Cherry-pick `tcod.path` module only. Our existing LOS/AoE/cover resolvers remain authoritative.

### 2.2 `python-pathfinding`

| Field | Detail |
|-------|--------|
| Repo | https://github.com/brean/python-pathfinding |
| License | **MIT** |
| Stars | ~370 |
| Deps | None (pure Python) |
| Status | Actively maintained (v1.0.20, Jan 2026) |

**What we'd reuse:** 7 pathfinding algorithms (A*, Dijkstra, bi-directional A*, BFS, IDA*, best-first, MST). Diagonal movement control with corner-cutting rules that map to D&D's "can't cut through walls" constraint.

**Why it fits doctrine:** MIT license. Pure Python — easy to audit, debug, and vendor. Lightweight `Grid(matrix=[[...]])` representation.

**Red flags:** No FOV/LOS support. No AoE shapes. Pure Python = slower on large grids (irrelevant for typical 20x40 D&D maps). 24 open issues.

**Recommendation:** **Adopt** (pure-Python pathfinding alternative to tcod). Lower integration cost, easier to debug. If tcod's C dependency is unwanted, this is the fallback.

### 2.3 Shapely + NumPy

| Field | Detail |
|-------|--------|
| Repo | https://github.com/shapely/shapely |
| License | **BSD-3-Clause** |
| Stars | ~4,371 |
| Deps | GEOS C library (bundled in wheel) |
| Status | Very actively maintained (v2.1.2) |

**What we'd reuse:** Polygon intersection for complex AoE shapes. `Point.buffer(r)` for circles, polygon wedges for cones, line intersection with grid cells.

**Why it fits doctrine:** BSD-3 license. We already have numpy.

**Red flags:** GIS library, not a game library. No grid/pathfinding/FOV concepts. Overkill for rectangular 5-ft grid AoE shapes — our existing `test_aoe_rasterizer.py` (53 tests) already handles burst/emanation/cone/line templates with pure NumPy math.

**Recommendation:** **Mine ideas** (upgrade path if AoE geometry gets complex). Current rasterizer is sufficient for 3.5e templates. Keep Shapely as a future option for irregular terrain or non-standard shapes.

### 2.4 `pyastar2d`

| Field | Detail |
|-------|--------|
| Repo | https://github.com/hjweide/pyastar2d |
| License | **MIT** |
| Stars | ~154 |
| Deps | numpy (C++ core) |
| Status | Lightly maintained (last push Feb 2026) |

**What we'd reuse:** Fast C++ A* on NumPy float32 weight grids. Single function: `astar_path(weights, start, end, allow_diagonal)`.

**Why it fits doctrine:** MIT license. NumPy-native. ~200 lines of C++ — trivially auditable.

**Red flags:** A* only — no Dijkstra, no flood-fill, no multi-target. Requires `np.float32` specifically. Minimal API.

**Recommendation:** **Mine ideas** (performance fallback). If python-pathfinding's pure-Python A* is too slow for large maps, swap in pyastar2d as a drop-in accelerator.

### 2.5 `w9-pathfinding`

| Field | Detail |
|-------|--------|
| Repo | https://github.com/w9PcJLyb/w9-pathfinding |
| License | **Apache-2.0** |
| Stars | ~5 |
| Deps | Cython (C++ core) |
| Status | New project (Jun 2024), sole author, pre-1.0 |

**What we'd reuse:** Multi-agent pathfinding (CBS, ICTS, WHCA*) — "6 goblins move optimally without collision."

**Red flags:** 5 stars, 0 forks, single developer. Pre-1.0 API. Niche.

**Recommendation:** **Mine ideas** (multi-agent pathfinding algorithms). The CBS/ICTS algorithms are interesting for monster AI movement but the library itself is too immature to adopt.

### Grid Bucket Summary

| Candidate | License | Pathfinding | FOV/LOS | AoE | Recommendation |
|-----------|---------|-------------|---------|-----|----------------|
| **python-tcod** | BSD-2 | A* + Dijkstra flood | Yes (multiple) | No | **Adopt** |
| **python-pathfinding** | MIT | 7 algorithms | No | No | **Adopt** (alt) |
| Shapely | BSD-3 | No | No | Yes (polygons) | Mine ideas |
| pyastar2d | MIT | A* only (fast) | No | No | Mine ideas |
| w9-pathfinding | Apache-2 | Multi-agent | No | No | Mine ideas |

---

## Bucket 3: Audio Plumbing

> Current state: `aidm/immersion/` has `TTSAdapter` protocol with Kokoro (ONNX, 24kHz) and Chatterbox backends producing 16-bit PCM WAV bytes. `SceneAudioState` schema defines active_tracks (ambient, combat, sfx, music) with volume, looping, and mood transitions. **No playback layer exists** — TTS produces bytes but nothing sends them to speakers.

### 3.1 `sounddevice` (python-sounddevice)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/spatialaudio/python-sounddevice |
| License | **MIT** |
| Stars | ~1,221 |
| Deps | PortAudio (bundled on Windows/macOS), cffi |
| Status | Actively maintained (last push Feb 12, 2026) |

**What we'd reuse:** `OutputStream` with callback for real-time audio output. Feed NumPy int16/float32 arrays into callback. `queue.Queue`-based pattern for decoupling audio production from playback. Configurable latency and blocksize.

**Why it fits doctrine:** MIT license. NumPy-native (already in our deps). PortAudio bundled in wheel on Windows/macOS — `pip install sounddevice` just works. Callback-based architecture maps to `SceneAudioState` — swap what the callback mixes when mood changes.

**Red flags:** No built-in audio file decoding (needs `soundfile` or `miniaudio` for MP3/OGG). Linux requires `libportaudio2` system package. Mixing is manual (in the callback).

**Recommendation:** **Adopt** (low-level output layer). Pair with miniaudio for decoding.

### 3.2 `miniaudio` (pyminiaudio)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/irmen/pyminiaudio |
| License | **MIT** |
| Stars | ~174 |
| Deps | miniaudio C library (single-header, bundled) |
| Status | Actively maintained (v1.61, last push Feb 2026) |

**What we'd reuse:** Built-in decoders for WAV, MP3, FLAC, OGG (no ffmpeg dependency). `PlaybackDevice` with generator-based streaming. Sample format conversion and resampling built in. `stream_file()` for large ambient tracks without loading into memory.

**Why it fits doctrine:** MIT license. The underlying miniaudio C library is public domain (CC0). Zero external dependencies — single-header C lib compiled into the wheel. Generator-based API lets us build a mixing generator that yields mixed PCM from multiple sources (TTS + ambient + SFX).

**Red flags:** Lower star count (174). No built-in mixing — must implement in Python generator. No NumPy integration out of the box (but array conversion is trivial).

**Recommendation:** **Adopt** (decode + playback). Strongest single-library candidate. Covers format decoding, resampling, and playback in one MIT package.

### 3.3 `rtmixer` (python-rtmixer)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/spatialaudio/python-rtmixer |
| License | **MIT** |
| Stars | ~72 |
| Deps | sounddevice, cffi |
| Status | Actively maintained (same author as sounddevice) |

**What we'd reuse:** Real-time mixing in C (does not invoke the Python interpreter in the audio callback — avoids GIL and GC pauses). `RingBuffer` for lock-free data transfer between Python and C audio thread. Fire-and-forget audio playback with mixing.

**Why it fits doctrine:** MIT license. C-level callback means narration won't stutter during heavy LLM inference or rule resolution. Same author maintains sounddevice and rtmixer — cohesive stack.

**Red flags:** 72 stars, niche. Requires CFFI compilation at install. Sparse documentation.

**Recommendation:** **Adopt** (upgrade path from sounddevice). Start with sounddevice's Python callback; if stuttering occurs during Spark inference, swap to rtmixer for C-level mixing.

### 3.4 `pydub`

| Field | Detail |
|-------|--------|
| Repo | https://github.com/jiaaro/pydub |
| License | **MIT** |
| Stars | ~9,727 |
| Deps | ffmpeg (external binary) |
| Status | **Effectively abandoned** (no release since ~2023, critical PRs unmerged) |

**What we'd reuse:** High-level audio manipulation API (overlay, crossfade, volume adjustment). Format conversion.

**Red flags:** **Python 3.13 breakage** — depends on `audioop` which was removed in Python 3.13. Unmerged PR to fix. No real-time streaming. Loads entire files into memory. Requires ffmpeg binary. Abandoned.

**Recommendation:** **Reject.** Abandoned, Python 3.13 broken, no streaming capability.

### 3.5 `pedalboard` (Spotify)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/spotify/pedalboard |
| License | **GPL-3.0** (JUCE dependency) |
| Stars | ~5,964 |

**Recommendation:** **Reject.** GPL-3.0 is disqualified per doctrine constraint #1.

### Audio Bucket Summary

| Candidate | License | Playback | Decode | Mixing | Recommendation |
|-----------|---------|----------|--------|--------|----------------|
| **sounddevice** | MIT | Yes (callback) | No | Manual (Python) | **Adopt** |
| **miniaudio** | MIT | Yes (generator) | WAV/MP3/OGG/FLAC | Manual (Python) | **Adopt** |
| **rtmixer** | MIT | Yes (C callback) | No | C-level | **Adopt** (upgrade) |
| pydub | MIT | No (batch only) | Yes (ffmpeg) | Yes (offline) | **Reject** |
| pedalboard | GPL-3.0 | No | Yes | No | **Reject** |

**Recommended audio stack:**

```
TTS Adapters (Kokoro/Chatterbox) → WAV bytes (16-bit PCM, 24kHz)
                                          |
                         miniaudio (decode ambient MP3/OGG + resample)
                                          |
                         sounddevice OutputStream (callback-based mixing)
                                          |
                         Speakers
```

If Python-callback mixing stutters during Spark inference, upgrade playback to `rtmixer` (drop-in, same author).

---

## Bucket 4: Notebook (Session Persistence)

> Current state: `aidm/core/event_log.py` provides append-only `EventLog` with monotonic event IDs and JSONL export (`to_jsonl()`). `aidm/runtime/session_orchestrator.py` manages session lifecycle with `SegmentTracker` (auto-segment every 10 turns). `aidm/core/provenance.py` provides W3C PROV-DM attribution. **No durable persistence beyond in-memory EventLog exists.**

### 4.1 `diskcache`

| Field | Detail |
|-------|--------|
| Repo | https://github.com/grantjenks/python-diskcache |
| License | **Apache-2.0** |
| Stars | ~2,800 |
| Deps | None (pure Python, uses stdlib sqlite3) |
| Status | Stable/mature (v5.6.3, last release Aug 2023, zero CVEs) |

**What we'd reuse:** `diskcache.Deque` with `"none"` eviction policy — persistent append-only event log backed by SQLite WAL. `diskcache.Index` — persistent ordered dict for campaign state snapshots keyed by session ID. `JSONDisk` serializer for human-readable storage.

**Why it fits doctrine:** Apache-2.0 license. Zero external dependencies (uses stdlib `sqlite3`). SQLite WAL provides crash-safe durability. Thread-safe and process-safe. `Deque` maps directly to our `EventLog` concept; `Index` maps to campaign state snapshots. Handles gigabytes of data efficiently.

**Red flags:** Not designed as an event store (no versioning, no projections, no aggregates). Last release Aug 2023 (stable but potentially waning). No native JSONL export — build a thin facade.

**Recommendation:** **Adopt** (primary persistence layer). `Deque` = durable event log. `Index` = campaign state snapshots. Build a `NotebookWriter` facade that bridges our `EventLog` → `diskcache.Deque` and adds JSONL/Markdown export.

### 4.2 `structlog`

| Field | Detail |
|-------|--------|
| Repo | https://github.com/hynek/structlog |
| License | **MIT / Apache-2.0** (dual) |
| Stars | ~4,500 |
| Deps | None required (optional integrations) |
| Status | Very actively maintained (v25.5.0, 3.6M weekly PyPI downloads) |

**What we'd reuse:** Structured event emission with context variables (session_id, encounter_id, round_number bound to every log entry). Processor pipeline for enriching, filtering, transforming events before output. Native JSON output → JSONL for free. Tee to console (pretty) + file (JSONL) simultaneously.

**Why it fits doctrine:** Dual MIT/Apache license. Context variables are ideal for campaign-scoped metadata. Processor pipeline can enforce immutability/validation before storage. Async-aware (works across `await` boundaries). Author also maintains `attrs` — high-quality engineering.

**Red flags:** Not a database — emits events, does not manage state. No built-in query, replay, or indexing. JSONL files have no WAL semantics (partial-write corruption on crash). Must pair with a storage backend.

**Recommendation:** **Adopt** (event emission layer). Use structlog to format and enrich events, then sink them into diskcache.Deque for durable storage. Complementary to diskcache, not a replacement.

### 4.3 `eventsourcing`

| Field | Detail |
|-------|--------|
| Repo | https://github.com/pyeventsourcing/eventsourcing |
| License | **BSD-3-Clause** |
| Stars | ~1,600 |
| Deps | Multiple (fragmented extension packages) |
| Status | Active (v9.5.3, single primary maintainer) |

**What we'd reuse:** Full event sourcing framework with aggregates, snapshots, versioned event upcasting, optimistic concurrency, SQLite persistence module.

**Why it fits doctrine:** BSD-3 license. Built-in SQLite WAL persistence.

**Red flags:** **Massive overkill** for a single-process TTRPG tool. Brings DDD aggregates, CQRS, distributed consistency machinery. Single-maintainer bus factor. Breaking changes between major versions (v8→v9 not backwards-compatible). Steep learning curve imposes "explanation tax" on every contributor.

**Recommendation:** **Reject** (overkill). The enterprise-grade machinery is not justified for a local campaign notebook. Our `EventLog` + `diskcache.Deque` provides the same append-only semantics with 1/100th the complexity.

### 4.4 `TinyDB`

| Field | Detail |
|-------|--------|
| Repo | https://github.com/msiemens/tinydb |
| License | **MIT** |
| Stars | ~7,100 |
| Deps | Zero (pure Python) |
| Status | Maintenance mode (stable, bugfixes only) |

**What we'd reuse:** Simple document-oriented JSON storage with query language.

**Red flags:** **Not append-only** — rewrites the entire JSON file on every write. O(n) write cost as file grows. Corruption risk on crash mid-write (no WAL). Performance degrades past ~10K records. No concurrent access. Migration to SQLite later described as "painful."

**Recommendation:** **Reject.** Full-file rewrite semantics violate our append-only invariant. Wrong tool for event logging.

### 4.5 `py-lmdb` (LMDB)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/jnwatson/py-lmdb |
| License | **OpenLDAP BSD** (permissive) |
| Stars | ~700 |
| Deps | C extension (binary wheels available) |
| Status | Mature (55 releases since 2013) |

**What we'd reuse:** Sub-microsecond reads via memory-mapped B+tree. ACID transactions with MVCC. Copy-on-write crash resistance. Multiple named databases in one file (events, snapshots, sessions).

**Red flags:** Key-value only — no query language, no document model. All serialization, indexing, and query logic is DIY. Key size limit (511 bytes default). Must pre-declare max database size. Much more manual work than diskcache.

**Recommendation:** **Mine ideas** (performance upgrade path). If diskcache.Deque becomes a bottleneck at very high event throughput, LMDB is the next tier. But the implementation cost is significantly higher.

### Notebook Bucket Summary

| Candidate | License | Append-only | Crash-safe | Query | Recommendation |
|-----------|---------|-------------|------------|-------|----------------|
| **diskcache** | Apache-2 | Deque (yes) | SQLite WAL | By key/index | **Adopt** |
| **structlog** | MIT/Apache | Emit layer | No (JSONL) | No | **Adopt** (complementary) |
| eventsourcing | BSD-3 | Yes | SQLite WAL | Aggregates | **Reject** (overkill) |
| TinyDB | MIT | No (rewrite) | No | Yes (query) | **Reject** |
| py-lmdb | OLDAP BSD | COW | MVCC | No (KV only) | Mine ideas |

**Recommended notebook stack:**

```
EventLog (in-memory) → structlog (enrich + format) → diskcache.Deque (durable WAL)
                                                    → diskcache.Index (state snapshots)
                                                    → JSONL file (human-readable export)
```

---

---

## Bucket 5: Grid/Map Visualization (Browser-Side Rendering)

> Current state: `aidm/ui/contextual_grid.py` provides terminal-based grid rendering (ASCII). `aidm/schemas/geometry.py` provides all game-logic grid types. **No browser/graphical rendering exists.** The product vision ("The Table") requires a visual map display for the player-facing experience.

### 5.1 Pixi.js + `@pixi/tilemap`

| Field | Detail |
|-------|--------|
| Repo | https://github.com/pixijs/pixijs |
| License | **MIT** |
| Stars | ~45,000+ |
| Size | ~120KB gzipped (core) |
| Status | Very actively maintained (v8.x, 2026) |

**What we'd reuse:** WebGL 2D renderer with Canvas fallback. `@pixi/tilemap` extension batches an entire grid into one GPU draw call — ideal for 5-ft square maps. `pixi-viewport` (~10KB, MIT) adds pan/zoom/camera controls. Foundry VTT (the largest open-source VTT) uses Pixi.js as its rendering core — proven at scale for exactly this use case.

**Why it fits doctrine:** MIT license. Browser-only (no Python boundary law concerns). Lightweight — ~120KB gzipped vs Phaser's ~500KB. No opinions about game logic — pure renderer. We feed it coordinates from Box's grid schemas, it draws pixels. Clean Lens-layer component.

**Red flags:** No built-in tilemap editor (use Tiled for authoring, export JSON). No physics engine (irrelevant — Box handles all game physics). Requires JavaScript/TypeScript on the client side.

**Recommendation:** **Adopt** (primary map renderer). Best performance-to-weight ratio for 2D grid rendering. Foundry VTT's choice validates the architecture. Pair with `pixi-viewport` for camera controls.

### 5.2 Phaser

| Field | Detail |
|-------|--------|
| Repo | https://github.com/phaserjs/phaser |
| License | **MIT** |
| Stars | ~37,000+ |
| Size | ~500KB+ gzipped |

**What we'd reuse:** Full game framework with tilemap support, scene management, tweens, input handling, built-in physics.

**Red flags:** **Overkill.** Bundles physics engines (Arcade, Matter.js), scene management, audio, input — all things we handle server-side in Box. 4x the bundle size of Pixi for features we won't use. Opinionated scene lifecycle fights our server-authoritative architecture.

**Recommendation:** **Skip.** Pixi.js gives us the rendering layer without the game framework baggage.

### 5.3 Canvas 2D (no library)

**What we'd reuse:** Zero-dependency grid rendering via browser Canvas API.

**Red flags:** No GPU acceleration, no sprite batching, no viewport management. Every feature (pan, zoom, sprite sheets, tile batching) must be hand-built. Performance degrades with large maps or many tokens.

**Recommendation:** **Skip.** The development cost of reimplementing what Pixi provides for free is not justified.

### 5.4 Three.js

| Field | Detail |
|-------|--------|
| Repo | https://github.com/mrdoob/three.js |
| License | **MIT** |
| Stars | ~104,000+ |
| Size | ~600KB+ gzipped (full), tree-shakeable |
| Status | Very actively maintained |

**What we'd reuse:** 3D scene renderer for the table surface. Camera rig (seated player angle, smooth stand-up transition to top-down). Table plane geometry, material system, lighting. Post-processing for crystal ball glow, ambient lighting changes.

**Why it fits doctrine:** MIT license. The product UI IS a 3D table — the battle map scroll, notebook, dice tower, crystal ball, and character sheet are physical objects ON a 3D table surface. Three.js is the right tool for this. Pixi.js handles the 2D grid rendering as a canvas texture applied to the scroll surface within the Three.js scene.

**Red flags:** Larger bundle than Pixi.js alone. Requires WebGL2 (broad support, but not universal). Learning curve for shader/material work (crystal ball glass effect, glow pulse). Must be combined with a 2D renderer (Pixi.js or Canvas) for the actual grid content.

**Recommendation:** **Adopt** (table surface renderer). Three.js owns the 3D scene (table, camera, objects, lighting). Pixi.js owns the 2D battle map grid as a texture on the scroll plane. This is a complementary pairing, not an either/or choice.

### 5.5 PlanarAlly (fork candidate)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/Kruptein/PlanarAlly |
| License | **MIT** |
| Stars | ~600+ |
| Stack | Python (asyncio) backend + Vue.js frontend |
| Status | Actively maintained |

**What we'd reuse:** Full open-source VTT with fog of war, dynamic lighting, initiative tracker, grid snapping. Python backend with WebSocket transport. Could fork the Vue.js frontend as a UI shell and replace the backend with our Box/Lens/Spark architecture.

**Why it fits doctrine:** MIT license. Python backend aligns with our stack. Already solves fog of war, token movement, grid overlay — things we'd otherwise build from scratch.

**Red flags:** Vue.js frontend (our research points toward Svelte or HTMX). Forking means maintaining divergent code. Their backend game logic would be completely replaced by Box — we'd only keep the rendering layer. The fork maintenance burden may exceed building a Pixi.js renderer from scratch, which would be purpose-built for our architecture.

**Recommendation:** **Mine ideas** (study their fog-of-war and dynamic lighting implementation). The rendering patterns are valuable reference, but a full fork introduces more coupling and maintenance burden than building a Pixi.js layer purpose-built for our data flow. If we need fog of war fast, cherry-pick their algorithms rather than forking the whole app.

### Grid Visualization Bucket Summary

| Candidate | License | GPU Accel | Tile Batching | Bundle Size | Recommendation |
|-----------|---------|-----------|---------------|-------------|----------------|
| **Pixi.js** | MIT | WebGL | @pixi/tilemap | ~120KB | **Adopt** |
| Phaser | MIT | WebGL | Built-in | ~500KB+ | Skip (overkill) |
| Canvas 2D | N/A | No | Manual | 0 | Skip (DIY cost) |
| Three.js | MIT | WebGL | N/A (3D scene) | ~600KB+ | **Adopt** (table surface) |
| PlanarAlly | MIT | Canvas | Built-in | Full app | Mine ideas |

---

## Bucket 6: Web Framework + Transport

> Current state: No web server exists. All demos run as terminal scripts. The product vision requires a browser-based player interface connected to the Python backend via WebSocket for real-time game state updates.

### 6.1 Starlette

| Field | Detail |
|-------|--------|
| Repo | https://github.com/encode/starlette |
| License | **BSD-3-Clause** |
| Stars | ~10,500+ |
| Deps | `anyio`, `httpcore` (2-3 deps) |
| Status | Very actively maintained |

**What we'd reuse:** ASGI framework with native WebSocket support. Static file serving for the browser client. Lightweight routing. Background tasks for audio/TTS processing. TestClient for integration testing.

**Why it fits doctrine:** BSD-3 license. FastAPI is literally built on top of Starlette — same WebSocket and routing primitives, without the OpenAPI/Pydantic schema generation overhead we don't need (Box already has its own frozen dataclass schemas). Async-native matches our audio pipeline needs. 3 dependencies total.

**Red flags:** No automatic API docs (irrelevant — we're not building a REST API for external consumers). No request validation middleware (Box validates everything).

**Recommendation:** **Adopt** (web framework). Lightest viable option that gives us WebSocket + static files + async. FastAPI adds overhead for features we already have.

### 6.2 FastAPI

| Field | Detail |
|-------|--------|
| Repo | https://github.com/tiangolo/fastapi |
| License | **MIT** |
| Stars | ~82,000+ |
| Deps | Starlette + Pydantic + many |
| Status | Very actively maintained |

**What we'd reuse:** Same WebSocket and routing as Starlette (it's literally Starlette underneath). Auto-generated OpenAPI docs. Pydantic request/response validation.

**Red flags:** Adds Pydantic v2 dependency (we use frozen dataclasses, not Pydantic). OpenAPI generation is wasted — no external API consumers. More dependencies than Starlette for features we won't use.

**Recommendation:** **Viable** (if team already knows FastAPI). Starlette is strictly less overhead for our use case. But FastAPI is not wrong — just heavier than needed.

### 6.3 Flask-SocketIO

| Field | Detail |
|-------|--------|
| License | **MIT** |
| Deps | Flask, python-engineio, python-socketio |

**Red flags:** Socket.IO protocol adds complexity over raw WebSocket. Flask is WSGI (sync) — requires eventlet/gevent for async. More moving parts than Starlette's native WebSocket.

**Recommendation:** **Skip.** Starlette's native WebSocket is simpler and more performant.

### 6.4 Django Channels

**Red flags:** Full Django ORM, admin, auth, middleware — massive framework for a game server that needs one WebSocket route and one static file directory. Wrong tool.

**Recommendation:** **Skip.** Overkill by an order of magnitude.

### Web Framework Bucket Summary

| Candidate | License | WebSocket | Async | Weight | Recommendation |
|-----------|---------|-----------|-------|--------|----------------|
| **Starlette** | BSD-3 | Native | Yes | ~3 deps | **Adopt** |
| FastAPI | MIT | Native (via Starlette) | Yes | ~8 deps | Viable (heavier) |
| Flask-SocketIO | MIT | Socket.IO | Async adapter | ~5 deps | Skip |
| Django Channels | BSD-3 | Channels | ASGI | ~20+ deps | Skip |

**Recommended transport architecture:**

```
Browser (Pixi.js + HTMX)  ←→  WebSocket  ←→  Starlette (async)
                                                    |
                                              SessionOrchestrator
                                                    |
                                           Box / Lens / Spark
```

---

## Bucket 7: Character Sheet UI

> Current state: `aidm/ui/character_sheet.py` provides terminal-based character sheet rendering via `CharacterData.from_entity()`. No browser-based character sheet exists.

### 7.1 HTMX + Jinja2 (server-rendered fragments)

| Field | Detail |
|-------|--------|
| HTMX Repo | https://github.com/bigskysoftware/htmx |
| License | **BSD-2-Clause** |
| Stars | ~42,000+ |
| Size | ~14KB gzipped |

**What we'd reuse:** Server renders HTML fragments in Python (Jinja2 templates), pushes them to the browser over WebSocket via `hx-ws`. Zero client-side JavaScript needed. HP bar updates, condition changes, inventory modifications — all rendered server-side and hot-swapped into the DOM.

**Why it fits doctrine:** BSD-2 license. **Reuses existing Python data pipeline** — `CharacterData.from_entity()` already produces the data, Jinja2 templates just format it as HTML instead of terminal text. No JavaScript build toolchain. No client-side state management. Server-authoritative by default (matches Box's authority model).

**Red flags:** Heavy interactivity (drag-and-drop inventory, spell slot tracking with click) requires either Alpine.js (~15KB, MIT) or custom JavaScript sprinkles. Not suitable if the character sheet needs to feel like a native app.

**Recommendation:** **Adopt** (fastest path to browser character sheet). Get a working sheet in days, not weeks. Add Alpine.js for interactive widgets (drag-and-drop, collapsible sections) as needed.

### 7.2 Svelte

| Field | Detail |
|-------|--------|
| Repo | https://github.com/sveltejs/svelte |
| License | **MIT** |
| Stars | ~81,000+ |

**What we'd reuse:** Reactive UI framework that compiles to vanilla JavaScript (no runtime library shipped to browser). Two-way data binding for editable fields. Transitions and animations for HP changes, condition effects. `threlte` provides Svelte-native Three.js integration if we ever need 3D dice.

**Why it fits doctrine:** MIT license. **Zero runtime overhead** — Svelte compiles away, unlike React/Vue which ship a runtime. Smallest bundle of any major framework. Reactive stores map well to Box's state change events pushed over WebSocket.

**Red flags:** Requires JavaScript build toolchain (Vite/SvelteKit). Adds client-side state management complexity. Team must know JavaScript. Longer path to first working sheet than HTMX.

**Recommendation:** **Adopt** (production-quality upgrade path). If HTMX+Jinja2 hits interactivity limits, migrate to Svelte. Build the map renderer (Pixi.js) and character sheet as Svelte components in the same app.

### 7.3 Roll20 3.5e Character Sheet (layout reference)

| Field | Detail |
|-------|--------|
| Source | Roll20 community character sheet repository |
| License | Varies (community contributions) |

**What we'd reuse:** HTML/CSS layout of the D&D 3.5e character sheet — the best existing web implementation of the WotC sheet layout. Tab structure, field placement, section organization.

**Red flags:** Roll20-proprietary JavaScript (sheet worker scripts) must be completely discarded. Only the HTML structure and CSS layout are reusable.

**Recommendation:** **Mine ideas** (layout reference). Fork the HTML/CSS for field placement, discard all Roll20-specific code, re-implement data binding with HTMX or Svelte.

### Character Sheet Bucket Summary

| Candidate | License | Build Toolchain | Interactivity | Time to First Sheet | Recommendation |
|-----------|---------|-----------------|---------------|---------------------|----------------|
| **HTMX + Jinja2** | BSD-2 | None | Moderate (+Alpine.js) | Days | **Adopt** (fast path) |
| **Svelte** | MIT | Vite | Full | Weeks | **Adopt** (production) |
| Roll20 template | Varies | N/A | N/A (reference) | N/A | Mine ideas (layout) |

---

## Bucket 8: Voice I/O

> Current state: `aidm/immersion/whisper_stt_adapter.py` provides STT via faster-whisper. Kokoro (ONNX, CPU), Chatterbox (torch, GPU), and Orpheus (torch, GPU+) TTS adapters exist. **No voice capture pipeline exists** — nothing listens to the microphone and feeds audio to faster-whisper. No dynamic vocabulary biasing.

### 8.1 STT: faster-whisper (already adopted)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/SYSTRAN/faster-whisper |
| License | **MIT** |
| Stars | ~13,000+ |
| Status | Already in our codebase at `aidm/immersion/whisper_stt_adapter.py` |

**Current integration:** Working STT adapter. Uses CTranslate2 backend for 4x faster inference than OpenAI Whisper.

**Enhancement needed:** `initial_prompt` parameter for dynamic vocabulary biasing. Build the prompt from current `WorldState` — entity names, spell names, location names, item names — so the model is primed to recognize "Tordek" instead of "Tor deck" and "Mordenkainen's Disjunction" instead of "more and kind is disjunction."

**Recommendation:** **Keep + enhance.** Add `initial_prompt` biasing from world state. No replacement needed.

### 8.2 Silero VAD (voice activity detection)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/snakers4/silero-vad |
| License | **MIT** |
| Stars | ~5,500+ |
| Size | <1MB model |
| Latency | <1ms per audio frame |

**What we'd reuse:** Detects speech onset/offset in real-time audio stream. Enables "always-listening" mode — microphone stays open, VAD triggers recording only when speech is detected, stops recording when silence resumes, then feeds the captured segment to faster-whisper.

**Why it fits doctrine:** MIT license. Tiny model (<1MB). CPU-only, <1ms latency. **Different role than faster-whisper's internal VAD** — Silero VAD runs on the raw microphone stream *before* whisper, controlling *when* to capture. faster-whisper's internal VAD runs *after* capture to trim silence within a segment.

**Red flags:** ONNX or PyTorch runtime required (we already have ONNX for Kokoro). Threshold tuning needed per environment (background noise levels vary).

**Recommendation:** **Adopt** (capture pipeline trigger). Pair with sounddevice for microphone input.

### 8.3 Vosk (offline STT alternative)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/alphacep/vosk-api |
| License | **Apache-2.0** |
| Stars | ~8,500+ |

**What we'd reuse:** Lightweight offline STT with small models (~50MB). Real-time streaming recognition. Speaker identification.

**Red flags:** Lower accuracy than faster-whisper (Whisper large-v3). No vocabulary biasing mechanism. Primarily useful for resource-constrained environments where faster-whisper's ~1-3GB models are too large.

**Recommendation:** **Mine ideas** (low-resource fallback). Keep as option for machines without GPU or with limited RAM.

### 8.4 TTS Tiered Architecture (Kokoro / Chatterbox / Orpheus / Piper)

**Current state:** Three TTS adapters exist at different quality/cost tiers:

| Adapter | Backend | Quality | Speed | Hardware | License |
|---------|---------|---------|-------|----------|---------|
| Kokoro | ONNX | Good | Fast | CPU | Apache-2.0 |
| Chatterbox | PyTorch | Very Good | Medium | GPU | MIT |
| Orpheus | PyTorch | Excellent | Slow | GPU (3GB+) | Apache-2.0 |

**Enhancement — Piper (additional CPU tier):**

| Field | Detail |
|-------|--------|
| Repo | https://github.com/rhasspy/piper |
| License | **MIT** |
| Stars | ~7,500+ |
| Size | Models 20-75MB |
| Speed | Faster than Kokoro on CPU |

Piper is a lighter CPU-tier alternative to Kokoro. Smaller models, faster synthesis, lower quality. Useful for rapid NPC barks where speed matters more than fidelity. Voice model licenses vary per model card — must audit each model individually.

**Recommendation:** **Keep all three existing adapters** (tiered by quality). **Adopt Piper** as a fourth tier for fast CPU synthesis when Kokoro is too slow and GPU is unavailable. The `TTSAdapter` protocol already supports this — Piper just needs a new adapter implementing the same interface.

### 8.5 Voice Capture Pipeline (missing piece)

**What needs building:** `aidm/immersion/voice_capture.py` — approximately 200 lines:

```
sounddevice InputStream (microphone) → Silero VAD (onset/offset detection)
                                              |
                                     State machine: idle → recording → ready
                                              |
                                     faster-whisper (transcription)
                                              |
                                     IntentBridge (parsed player intent)
```

This is integration code, not a new OSS dependency. Uses sounddevice (Bucket 3 — already adopted) + Silero VAD (this bucket) + faster-whisper (already adopted).

### Voice I/O Bucket Summary

| Candidate | License | Role | Status | Recommendation |
|-----------|---------|------|--------|----------------|
| **faster-whisper** | MIT | STT engine | Already adopted | **Keep + enhance** (vocabulary biasing) |
| **Silero VAD** | MIT | Speech detection | New | **Adopt** (capture trigger) |
| Vosk | Apache-2 | STT alternative | New | Mine ideas (low-resource) |
| **Kokoro** | Apache-2 | TTS (CPU, good) | Already adopted | **Keep** |
| **Chatterbox** | MIT | TTS (GPU, very good) | Already adopted | **Keep** |
| **Orpheus** | Apache-2 | TTS (GPU+, excellent) | Already adopted | **Keep** |
| **Piper** | MIT | TTS (CPU, fast) | New | **Adopt** (fast CPU tier) |

---

## Bucket 9: Content & Assets

> Current state: All game content is hand-authored in Python fixtures or YAML. No structured SRD data pipeline exists. No visual assets (tokens, tiles, UI elements) exist. The World Compiler contract (825 lines) specifies how world bundles should be structured but has zero implementation.

### 9.1 SRD 3.5 Data Sources

#### d20srd.org

| Field | Detail |
|-------|--------|
| URL | https://www.d20srd.org/ |
| License | **OGL 1.0a** (Open Game License) |
| Content | Complete 3.5e SRD — monsters, spells, feats, items, classes, races |

**What we'd reuse:** Canonical 3.5e rules text. Every monster stat block, spell description, feat prerequisite chain, magic item property. This is the authoritative source for the World Compiler's input data.

**Red flags:** HTML format — requires scraping and structuring into our schema format. No API. Content is static (SRD doesn't change). OGL 1.0a requires including the license text and Section 15 attribution in any product that uses the content.

**Recommendation:** **Use** (primary content source). Build a scraper/parser that converts d20srd.org HTML into World Bundle JSON conforming to our `world_bundle.schema.json`.

#### PCGen Data Files

| Field | Detail |
|-------|--------|
| Repo | https://github.com/PCGen/pcgen |
| License | **LGPL + OGL** |
| Content | Most complete structured 3.5e data in existence |

**What we'd reuse:** Thousands of monsters, spells, feats, classes, races already digitized in LST (tab-delimited) format. Pre-computed prerequisite chains. Equipment stats. Class progression tables.

**Red flags:** **LGPL license on the code** — data files are OGL. LST format is PCGen-proprietary, needs a parser. The data is extremely comprehensive but messy (20+ years of community contributions, inconsistent formatting). LGPL means we can use the data files but cannot embed the PCGen Java application.

**Recommendation:** **Mine data** (structured reference). Write a one-time LST→JSON converter for the data files. Use as cross-reference to validate our d20srd.org scrape. Do not ship PCGen code.

#### Open5e / 5e SRD

**Recommendation:** **Skip.** Wrong edition. We're building for 3.5e, not 5e. The rules are fundamentally different.

### 9.2 Visual Assets

#### Kenney.nl (CC0 Assets)

| Field | Detail |
|-------|--------|
| URL | https://kenney.nl/assets |
| License | **CC0** (public domain) |
| Content | 40,000+ game assets — tiles, tokens, UI elements, icons |

**What we'd reuse:** Dungeon tileset (walls, floors, doors, stairs). UI elements (buttons, panels, health bars). Creature tokens. Item icons. **Zero attribution required** — CC0 is the most permissive license possible.

**Recommendation:** **Use as development placeholder** (minimum-spec fallback). Kenney tiles are useful for early development and for machines that cannot run image generation models. The product vision requires self-generated assets via the World Compiler (Stages 6-8) — Kenney tiles are NOT the shipping asset source. Downgrade from "Adopt" to "Placeholder."

#### OpenGameArt.org

| Field | Detail |
|-------|--------|
| URL | https://opengameart.org/ |
| License | **Varies per asset** (CC0, CC-BY, CC-BY-SA, GPL) |

**What we'd reuse:** Large community library of fantasy game art. Must filter to CC0 or CC-BY only.

**Red flags:** **License per asset** — must audit each download. CC-BY-SA is viral (share-alike). Some assets are GPL. Inconsistent quality. Must curate carefully.

**Recommendation:** **Mine ideas** (supplementary). Use Kenney as primary (guaranteed CC0), cherry-pick from OpenGameArt for specific needs (monster tokens, spell effects) with per-asset license verification.

#### Freesound.org

| Field | Detail |
|-------|--------|
| URL | https://freesound.org/ |
| License | **Varies** (CC0, CC-BY, CC-BY-NC) |

**What we'd reuse:** Ambient audio (tavern, forest, dungeon, rain), SFX (sword clash, spell cast, door creak). Pair with miniaudio for playback.

**Red flags:** **CC-BY-NC blocks commercial use.** Must filter to CC0 or CC-BY only. Requires account for downloads. Quality varies widely.

**Recommendation:** **Mine ideas** (ambient/SFX library). Filter strictly to CC0/CC-BY. Build a curated SFX pack for common D&D scenarios.

### 9.3 Map Authoring

#### Tiled Map Editor

| Field | Detail |
|-------|--------|
| Repo | https://github.com/mapeditor/tiled |
| License | **GPL-2.0** (the editor application) |
| Export formats | JSON, TMX (XML), CSV |

**What we'd reuse:** Visual map authoring tool. DMs draw dungeon maps with tiles, place objects, define collision layers. Exports JSON that our Pixi.js renderer can load directly via `@pixi/tilemap`.

**Why it fits doctrine despite GPL:** Tiled is an **external authoring tool**, not embedded in our product. DMs use it to create maps, export JSON files, and those JSON files are loaded by our MIT-licensed renderer. The GPL applies to Tiled's source code, not to the map files it produces. Same model as using GIMP (GPL) to create PNG assets.

**Red flags:** GPL means we cannot embed Tiled's code. DMs must install Tiled separately. The JSON export format is Tiled-specific — need a thin loader.

**Recommendation:** **Use as external tool** (map authoring workflow). Do not embed. Load Tiled JSON exports in our Pixi.js renderer. Document the DM workflow: Tiled → export JSON → place in campaign folder → The Table loads it.

### Content & Assets Bucket Summary

| Candidate | License | Content Type | Recommendation |
|-----------|---------|-------------|----------------|
| **d20srd.org** | OGL 1.0a | Rules text (3.5e SRD) | **Use** (primary) |
| PCGen data | LGPL + OGL | Structured game data | Mine data (reference) |
| **Kenney** | CC0 | Tiles, tokens, UI, icons | **Placeholder** (dev + min-spec fallback) |
| OpenGameArt | Varies | Fantasy art | Mine ideas (supplementary) |
| Freesound | Varies | Audio SFX/ambient | Mine ideas (SFX library) |
| **Tiled** | GPL-2 | Map authoring tool | **Use** (external tool) |

---

## Bucket 10: Terminal UI (Development & Fallback)

> Current state: All demo output is raw `print()` statements. `aidm/ui/character_sheet.py` and `aidm/ui/contextual_grid.py` exist but use basic terminal output.

### 10.1 Textual + Rich

| Field | Detail |
|-------|--------|
| Repo | https://github.com/Textualize/textual / https://github.com/Textualize/rich |
| License | **MIT** |
| Stars | ~27,000 (Textual) / ~50,000+ (Rich) |
| Deps | Rich (Textual depends on Rich) |
| Status | Very actively maintained |

**What we'd reuse:** Rich for formatted terminal output (tables, syntax highlighting, progress bars, panels) in all demo scripts and development tools. Textual for full TUI applications — interactive character sheet, combat log viewer, initiative tracker, all running in the terminal without a browser.

**Why it fits doctrine:** MIT license. Pure Python. Same author (Will McGuinness). Rich is a drop-in upgrade for `print()` — zero architecture changes. Textual provides a CSS-like layout system for terminal widgets. Useful as the DM's control panel even after the browser UI ships.

**Red flags:** Textual's CSS-like system has a learning curve. Not a replacement for the browser UI — terminal has inherent limitations (no images, no mouse hover, no smooth animations). Heavy for what could be simple logging.

**Recommendation:** **Adopt Rich** (immediate upgrade for demo/dev output). **Mine ideas for Textual** (DM control panel if terminal-first workflow is desired). Rich is zero-cost to adopt and improves every demo script instantly.

### Terminal UI Summary

| Candidate | License | Use Case | Recommendation |
|-----------|---------|----------|----------------|
| **Rich** | MIT | Formatted terminal output | **Adopt** |
| Textual | MIT | Full TUI applications | Mine ideas (DM panel) |

---

## Bucket 11: Browser Audio (Client-Side)

> Current state: Bucket 3 covers server-side audio plumbing (sounddevice, miniaudio). When the player interface moves to the browser, audio playback needs a client-side solution.

### 11.1 howler.js

| Field | Detail |
|-------|--------|
| Repo | https://github.com/goldfire/howler.js |
| License | **MIT** |
| Stars | ~24,000+ |
| Size | ~10KB gzipped |

**What we'd reuse:** Cross-browser Web Audio API wrapper. Sprite sheets for SFX (one file, multiple sounds). Spatial audio positioning (sound from left/right based on token position). Volume control, fade, loop — maps directly to `SceneAudioState` fields. HTML5 Audio fallback for older browsers.

**Why it fits doctrine:** MIT license. Tiny bundle. No dependencies. Handles browser audio quirks (autoplay policy, codec detection, iOS limitations) that we'd otherwise have to solve manually.

**Recommendation:** **Adopt** (browser audio playback). Server streams WAV/MP3 bytes via WebSocket, howler.js plays them. Ambient tracks, SFX, and TTS narration all route through howler.js on the client.

---

## Bucket 12: Image & Audio Generation (World Compiler Stages 6-8)

> Current state: `aidm/core/prep_pipeline.py` has stub mode for image/music generation. `aidm/schemas/immersion.py` defines `ImageRequest`/`ImageResult`. World bundle schema defines asset pool categories with `generation_prompt_template`. **No real model integration exists.**

### 12.1 diffusers (Hugging Face)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/huggingface/diffusers |
| License | **Apache-2.0** |
| Stars | ~27,000+ |
| Deps | torch, transformers, safetensors |
| Status | Very actively maintained |

**What we'd reuse:** Unified inference pipeline for Stable Diffusion, SDXL, FLUX, and future image generation models. Handles model loading, scheduler selection, prompt encoding, denoising loop, and image output. Supports CPU fallback (slow but functional).

**Why it fits doctrine:** Apache-2.0 license. Model-agnostic — swap SD 1.5 → SDXL → FLUX without changing pipeline code. Hardware-aware: auto-selects precision (fp16/fp32) based on GPU capability. The product generates its own assets; diffusers is the inference engine.

**Model tiers by hardware:**

| Model | VRAM | Quality | Speed | License |
|-------|------|---------|-------|---------|
| SD 1.5 | ~2GB | Good | Fast | CreativeML Open RAIL-M |
| SDXL | ~6GB | Very Good | Medium | SDXL-1.0 (permissive) |
| FLUX.1-schnell | ~12GB (quantized ~8GB) | Excellent | Medium | Apache-2.0 |

**Red flags:** Large download sizes (2-12GB per model). GPU memory contention with LLM and TTS models — requires sequential loading (prep_pipeline.py already handles this). Model licenses vary — must audit each model's license card.

**Recommendation:** **Adopt** (image generation engine). Start with SD 1.5 for median hardware, upgrade path to SDXL/FLUX for capable machines. CPU fallback for minimum spec.

### 12.2 AudioCraft / MusicGen (Meta)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/facebookresearch/audiocraft |
| License | **MIT** |
| Stars | ~21,000+ |
| Models | MusicGen-small (300M), MusicGen-medium (1.5B) |

**What we'd reuse:** Text-to-music generation. Scene descriptions → ambient music tracks. Theme-consistent background audio for different environments (tavern, dungeon, forest, combat).

**Model tiers:**

| Model | VRAM | Quality | License |
|-------|------|---------|---------|
| MusicGen-small | ~1.5GB | Good | MIT |
| MusicGen-medium | ~3.5GB | Very Good | MIT |

**Red flags:** GPU memory contention. Audio generation is lower priority than image generation for MVP. MVP spec explicitly says "voice only" for audio — music is post-MVP.

**Recommendation:** **Adopt** (post-MVP, World Compiler Stage 8). Lower priority than diffusers. Wire into prep_pipeline.py's sequential loading architecture.

### Image/Audio Generation Bucket Summary

| Candidate | License | Type | VRAM | Recommendation |
|-----------|---------|------|------|----------------|
| **diffusers** | Apache-2 | Image gen pipeline | 2-12GB | **Adopt** (core asset gen) |
| **SD 1.5** | RAIL-M | Image model (median) | ~2GB | **Adopt** (default tier) |
| **SDXL** | SDXL-1.0 | Image model (high) | ~6GB | **Adopt** (upgrade tier) |
| FLUX.1-schnell | Apache-2 | Image model (top) | ~12GB | Adopt when feasible |
| **MusicGen** | MIT | Music generation | 1.5-3.5GB | **Adopt** (post-MVP) |

---

## Master Recommendation Matrix

| Bucket | Primary Pick | Runner-Up | License | Deps |
|--------|-------------|-----------|---------|------|
| **1. Dice** | `d20` (avrae) | `dice` (borntyping) | MIT | lark / pyparsing |
| **2. Grid (pathfinding)** | `python-tcod` | `python-pathfinding` | BSD-2 / MIT | numpy+cffi / none |
| **3. Audio (server)** | `miniaudio` + `sounddevice` | `rtmixer` (upgrade) | MIT | C libs bundled |
| **4. Notebook** | `diskcache` + `structlog` | (complementary pair) | Apache-2 + MIT | none / none |
| **5. Grid (visualization)** | Three.js (table) + Pixi.js (grid) | (reference PlanarAlly) | MIT | browser-only |
| **6. Web framework** | Starlette | FastAPI (heavier) | BSD-3 / MIT | ~3 deps |
| **7. Character sheet** | HTMX + Jinja2 | Svelte (production) | BSD-2 / MIT | browser-only |
| **8. Voice I/O** | faster-whisper + Silero VAD + Piper | Vosk (fallback) | MIT | ONNX / torch |
| **9. Content** | d20srd.org + Tiled + diffusers (self-gen) | PCGen (reference), Kenney (placeholder) | OGL + GPL(tool) + Apache-2 | none |
| **10. Terminal UI** | Rich | Textual (DM panel) | MIT | none |
| **11. Browser audio** | howler.js | N/A | MIT | browser-only |
| **12. Image/Audio gen** | diffusers + SD 1.5 | MusicGen (post-MVP) | Apache-2 + MIT | torch |

**Total new Python dependencies if all primaries adopted:** ~6 packages (d20/lark, python-tcod, miniaudio, sounddevice, diskcache, structlog, silero-vad, piper-tts), 0 GPL, all with binary wheels.

**Total new browser dependencies:** ~4 packages (pixi.js, @pixi/tilemap, pixi-viewport, htmx, howler.js), all MIT/BSD.

---

## Recommended Adoption Phases

### Phase 1: Immediate (zero-risk, instant value)

| Component | What | Why Now |
|-----------|------|---------|
| Rich | Replace `print()` in demos | 5 minutes of work, huge readability gain |
| structlog | Structured event logging | Complements existing EventLog |
| Kenney CC0 | Download dungeon tileset | Dev placeholder + min-spec fallback |
| Tiled | DM map authoring workflow | External tool, no code changes |

### Phase 2: Foundation (enables browser UI)

| Component | What | Why Now |
|-----------|------|---------|
| Starlette | WebSocket server | Required for any browser interface |
| Pixi.js + pixi-viewport | Grid/map renderer | Core visual experience |
| HTMX + Jinja2 | Character sheet v1 | Fastest path to playable browser sheet |
| howler.js | Browser audio | TTS + ambient in the browser |
| diskcache | Session persistence | Campaign state survives restarts |

### Phase 3: Enhancement (polish + depth)

| Component | What | Why Now |
|-----------|------|---------|
| d20 | Dice notation parser | Richer dice expressions for players |
| python-tcod | Pathfinding | Monster AI movement |
| Silero VAD | Voice capture pipeline | Hands-free play mode |
| faster-whisper enhancement | Vocabulary biasing | Better recognition of game terms |
| Piper | Fast CPU TTS tier | NPC barks without GPU |
| Svelte | Character sheet v2 | If HTMX hits interactivity limits |
| d20srd.org scraper | SRD data pipeline | Feed the World Compiler |
| diffusers + SD 1.5 | Image generation pipeline | World Compiler Stage 6 |

---

## License Summary

| License | Components | Safe? |
|---------|-----------|-------|
| **MIT** | Pixi.js, HTMX, Svelte, howler.js, d20, dice, miniaudio, sounddevice, rtmixer, Rich, Textual, faster-whisper, Silero VAD, Piper, Chatterbox, MusicGen, Three.js | YES |
| **BSD-2** | Starlette, python-tcod, HTMX | YES |
| **BSD-3** | Starlette | YES |
| **Apache-2.0** | diskcache, Kokoro, Orpheus, Vosk, diffusers | YES |
| **CC0** | Kenney assets, miniaudio C core | YES (public domain) |
| **OGL 1.0a** | d20srd.org, PCGen data files | YES (requires license text inclusion) |
| **GPL-2.0** | Tiled (external tool only — not embedded) | YES (tool, not dependency) |
| **LGPL** | PCGen Java code (data files are OGL) | CAUTION (mine data only) |
| **AGPL** | MapTool | **REJECT** (viral, network-triggered) |
| **CC-BY-SA** | Some OpenGameArt assets | **AVOID** (viral share-alike) |
| **CC-BY-NC** | Some Freesound assets | **AVOID** (blocks commercial) |

---

## Rejected Candidates (with rationale)

| Candidate | Reason |
|-----------|--------|
| xdice | GPL-3.0 — disqualified |
| pedalboard (Spotify) | GPL-3.0 (JUCE) — disqualified |
| pydub | Abandoned, Python 3.13 broken, no streaming |
| eventsourcing | Overkill for single-process TTRPG |
| TinyDB | Full-file rewrite violates append-only invariant |
| Phaser | 4x bundle size of Pixi.js for unused features |
| Django Channels | Massive framework overhead for one WebSocket route |
| Flask-SocketIO | Socket.IO complexity vs native WebSocket |
| MapTool | AGPL — network-triggered viral license |
| Open5e | Wrong edition (5e, not 3.5e) |

---

## Cross-Reference: Jay's Research Contributions

The following findings from Jay's parallel ChatGPT research sessions were incorporated into this document:

- **PlanarAlly** (MIT VTT) — Evaluated in Bucket 5. Recommendation: mine ideas rather than full fork.
- **Pixi.js + pixi-viewport** — Confirmed as primary pick in Bucket 5. Jay's research independently reached the same conclusion.
- **FastAPI + WebSockets** — Evaluated in Bucket 6. We recommend Starlette (FastAPI's core) as the lighter option.
- **howler.js** — Adopted in Bucket 11 based on Jay's recommendation.
- **Kenney CC0 assets** — Downgraded to placeholder in Bucket 9 (dev + min-spec fallback; shipping assets are self-generated via World Compiler).
- **Tiled map editor** — Adopted in Bucket 9 based on Jay's recommendation. GPL is safe as external tool.
- **Textual + Rich** — Adopted in Bucket 10 based on Jay's recommendation.
- **faster-whisper** — Confirmed as keeper in Bucket 8. Jay's research aligned.
- **Piper TTS** — Added to Bucket 8 as fast CPU tier based on Jay's recommendation.
- **OpenGameArt + Freesound** — Evaluated in Bucket 9 with license warnings per Jay's findings.
- **AGPL/MapTool warning** — Incorporated into license summary. Jay correctly flagged this.
- **structlog** — Already in Bucket 4. Jay's research confirmed adoption.

---

## Next Steps

1. PO approves/rejects each bucket recommendation
2. Approved items get individual integration WOs with:
   - Boundary law compliance verification
   - Determinism contract tests (server-side components)
   - Thin adapter/facade design (no direct coupling to OSS API surface)
3. Phase 1 items can be adopted immediately with zero risk
4. Phase 2 items require a `WO-WEBSHELL-001` work order for the Starlette + Pixi.js + HTMX integration
5. Rejected items documented with rationale in decision log

---

## END OF OSS SHORTLIST
