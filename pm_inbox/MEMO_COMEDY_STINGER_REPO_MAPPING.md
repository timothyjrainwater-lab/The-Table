# MEMO: Comedy Stinger Subsystem — Repo Mapping & Implementation Spec

**Lifecycle:** NEW
**From:** BS Buddy (Gravel) — 2026-02-18
**To:** PM (Claude)
**Subject:** Comedy stinger subsystem — GPT design spec + repo mapping for your queue
**Origin:** GPT (Aegis, co-PM advisor) identified a comedy rhythm pattern and produced a full subsystem spec. PM audited and mapped it to repo conventions. Combined here for PM intake.

---

## Background

GPT (external co-PM advisor, no repo access) identified a reproducible comedy rhythm in BS Buddy session output and spec'd a deterministic NPC stinger delivery subsystem. The operator wants this filed for PM sequencing — not urgent, but the design work is done and the repo mapping is complete. Pick it up when NPC dialogue comes online.

---

## 1. Repo Layout You Must Respect

- **Core code:** `aidm/`
- **Schemas and wire contracts:** `aidm/schemas/`
  - Existing: campaign, npc_archetype, prompt_pack, asset_binding, ws_protocol
- **Lens orchestration:** `aidm/lens/`
  - Surfaces: content_pack_loader.py, presentation_registry.py, voice_resolver.py, prompt_pack_builder.py, narrative_brief.py
- **Deterministic event spine:** `aidm/core/`
  - EventLog: append-only JSONL, monotonic event_id, deterministic JSON serialization
  - Provenance hashing: `aidm/core/provenance.py` → `compute_value_hash()` (sha256, sort_keys=True, 16-char prefix)
- **Campaign persistence:** `aidm/core/campaign_store.py` → `campaigns/<campaign_id>/` with manifest.json and events.jsonl
- **TTS harness:** `scripts/speak.py` (Chatterbox → winsound). Acceptable as Phase 1 call site.

---

## 2. Where the Stinger System Lives

### Phase 1 — Standalone Content System

Callable from `scripts/speak.py` or narration harness. No Director/Lens/Spark wiring required.

| Component | Location | Notes |
|-----------|----------|-------|
| **Schema** | `aidm/schemas/npc_stinger.py` | New module. Stinger dataclass with fragments, tags, constraints. |
| **Data** | `aidm/data/content_pack/npc_stingers.json` | Content pack data plane (Lens already has a loader). NOT ad-hoc files. |
| **Logic** | `aidm/lens/comedy_stingers.py` | New module. Three functions: `validate_stinger_bank()`, `select_stinger_deterministic()`, `render_stinger_fragments()` |

### Phase 2 — Full Pipeline Integration

| Component | Integration Point | Notes |
|-----------|------------------|-------|
| **Director** | Beat type selection | INTRODUCE_NPC and existing beat types. Comedy stinger = beat subtype or delivery_context mapping. Director selects beat + target NPC only, NOT the specific line. |
| **Lens** | Deterministic selection | Picks stinger, renders fragments, injects into PromptPack with TTS tags. |
| **Spark** | Reads pre-rendered string | Outputs exactly the rendered line. No improvisation. No writing state. |
| **Oracle** | Usage state storage | NPCComedyState with provenance_event_id after delivery. Minimal pointers only. |
| **Immersion** | TTS + playback | Receives rendered string + persona/register hints. Fires through emotion router. |

---

## 3. Determinism Primitives (already exist — use them)

- Event dataclass + EventLog append rules: `aidm/core/event_log.py`
- Content-addressed hashing: `aidm/core/provenance.py` → `compute_value_hash()`
- Campaign persistence: `aidm/core/campaign_store.py`

**Selection seed material:** `campaign_seed + npc_id + delivery_context + scene_id_or_event_id`

Use existing hash utility. Do not introduce new RNG.

---

## 4. Data Model (your spec, mapped to our conventions)

### Stinger Schema (`aidm/schemas/npc_stinger.py`)

```python
@dataclass
class Stinger:
    stinger_id: str                    # stable, content-addressed or manual
    archetype: str                     # tavern_keeper, town_guard, merchant, etc.
    delivery_contexts: List[str]       # first_meeting, post_combat_lull, tavern_downtime, etc.
    fragments: List[str]               # exactly 4: [cred, cred, cred, punchline]
    tags: Dict[str, Any]               # pace, pause_ms_before_punchline, emphasis_target, mood_hint
    constraints_override: Optional[Dict] = None

@dataclass
class NPCComedyState:
    npc_id: str
    last_used_by_context: Dict[str, str]  # context -> stinger_id
    recent_ring: List[str]                # last N stinger_ids (N=3)
```

### Content Pack (`aidm/data/content_pack/npc_stingers.json`)

```json
{
  "stingers": [
    {
      "stinger_id": "tavern_keeper_001",
      "archetype": "tavern_keeper",
      "delivery_contexts": ["first_meeting", "tavern_downtime"],
      "fragments": [
        "Forty years behind this bar",
        "Three wars",
        "A lich who tipped well",
        "And now you lot want credit"
      ],
      "tags": {
        "pace": "staccato",
        "pause_ms_before_punchline": 240,
        "emphasis_target": "punchline",
        "mood_hint": "deadpan"
      }
    }
  ]
}
```

---

## 5. Validator Rules (hard gate, fail closed)

1. `fragments` length == 4
2. Credentials (fragments[0..2]): word count 2-6 each
3. Punchline (fragments[3]): word count > each credential's word count
4. Total rendered sentences <= 3
5. No conjunctions ("and", "but", "or") in credentials (fragments[0..2])
6. Estimated duration <= 6.0 seconds (total_words / 2.75 + pause_ms/1000)
7. No silent fallback on violation — fail the gate

---

## 6. Test Conventions

Tests live under `tests/`. Gate-style pytest, counted in the gate suite.

| Test | Purpose |
|------|---------|
| `test_stingers_validate_bank_passes()` | Valid bank passes all rules |
| `test_stingers_validate_bank_rejects_bad_fragments()` | Bad fragment counts, word counts, conjunctions rejected |
| `test_stingers_deterministic_selection_seeded()` | Same inputs → same stinger_id across runs |
| `test_stingers_recent_ring_no_repeat_then_relax()` | No duplicates until pool exhausted, then deterministic fallback |
| `test_stingers_renderer_stability_snapshot()` | Rendered strings match snapshots |

---

## 7. Non-Negotiable Wiring Constraints

1. **No backflow.** Spark and Immersion must not write stinger selection state. Ever.
2. **Seeded hash selection.** No unseeded RNG.
3. **Bounded usage ring.** Last 3. Minimal pointers only.
4. **WebSocket protocol lock.** If stingers ever travel over WS, they must be formal message types under `aidm/schemas/ws_protocol`. No wildcard payloads.

---

## 8. The Ask

When NPC dialogue comes online, this is ready to be scoped into a WO. The design work is done. The repo mapping is done. A builder just needs to implement it.

**Phase 1** is standalone — schema, validator, selector, tests. No pipeline wiring needed. Could ship as a content system before Director/Lens integration exists.

**Phase 2** wires it into the full narration pipeline when that's ready.

---

## 9. Voice Pipeline Integration (for TTS tag mapping)

The stinger `tags` map to existing TTS infrastructure:

| Stinger Tag | TTS Mapping |
|-------------|------------|
| `mood_hint: "deadpan"` | Emotion router: mood "neutral" → register "neutral" |
| `mood_hint: "bureaucratic"` | Emotion router: mood "neutral" → register "neutral" (flat delivery) |
| `mood_hint: "cheerful"` | Emotion router: mood "peaceful" → register "neutral" |
| `mood_hint: "dramatic"` | Emotion router: mood "dramatic" → register "grief" |
| `mood_hint: "menacing"` | Emotion router: mood "combat" → register "angry" |
| `pause_ms_before_punchline` | TTS pause token or silence injection before final fragment |
| `pace: "staccato"` | Short sentences already handled well by Chatterbox. No special handling needed. |

All reference clips are tavern-baked (medium intensity, deployed 2026-02-18). Room acoustics are handled at the reference level, not post-processing.

---

*Filed by Tharrik "Gravel" Ashbone, with architectural audit by PM + Aegis (GPT).*
*Seven wisdom, zero regrets.*
