# Instruction Packet: World Compiler Scaffold Agent

**Work Order:** WO-WORLDCOMPILE-SCAFFOLD-001 (World Compiler Pipeline Harness)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 1 (All other compiler stages plug into this)
**Deliverable Type:** Code implementation + tests
**Parallelization:** Must complete BEFORE Stage-specific WOs can integrate

---

## READ FIRST

The World Compiler is an offline pipeline that takes a content pack + world theme + seeds + pinned toolchain and produces a Frozen World Bundle. The full contract is in `docs/contracts/WORLD_COMPILER.md` (825 lines).

This WO builds the **pipeline harness** — Stages 0 (validation) and 8 (finalization) — plus the plugin interface that stage-specific WOs will implement. Think of this as the frame of the car: engine, wheels, and body bolt on later.

**Existing infrastructure to build on:**
- `aidm/core/prep_orchestrator.py` (420 lines) — Campaign-level prep with deterministic job queues. World compile is UPSTREAM of this.
- `aidm/core/prep_pipeline.py` (517 lines) — Sequential model loading for asset gen. World compile stages will feed into this.
- `aidm/schemas/campaign.py` (448 lines) — PrepJob, AssetRecord, CampaignManifest patterns.
- `aidm/core/provenance.py` (735 lines) — W3C PROV-DM tracing.
- `aidm/core/state.py` (267 lines) — FrozenWorldStateView pattern, deterministic hashing.

---

## YOUR TASK

### Deliverable 1: Compile Input Schemas

**File:** `aidm/schemas/world_compile.py` (NEW)

Frozen dataclasses for compile inputs (§1 of contract):

```python
@dataclass(frozen=True)
class WorldThemeBrief:
    genre: str                      # "dark_fantasy", "sci_fi", "steampunk", etc.
    tone: str                       # "grim", "heroic", "whimsical", etc.
    naming_style: str               # "anglo_saxon", "latin", "japanese", etc.
    technology_level: str = "medieval"
    magic_level: str = "high"
    cosmology_notes: str = ""
    environmental_palette: tuple = ()  # ("volcanic", "desert", "tundra")

@dataclass(frozen=True)
class ToolchainPins:
    llm_model_id: str               # "qwen3-8b-q4" — pinned, no "latest"
    hash_algorithm: str = "sha256"
    schema_version: str = "1.0.0"
    image_model_id: str = ""        # Empty = skip image gen
    music_model_id: str = ""        # Empty = skip music gen

@dataclass(frozen=True)
class CompileConfig:
    output_dir: str
    log_level: str = "INFO"
    enable_stages: tuple = ()       # Empty = all stages. ("lexicon", "rulebook") = only those.
    content_filters: dict = field(default_factory=dict)  # Use dataclasses.field()

@dataclass(frozen=True)
class CompileInputs:
    content_pack_id: str
    world_theme_brief: WorldThemeBrief
    world_seed: int                 # Non-negative 64-bit integer
    compile_config: CompileConfig
    toolchain_pins: ToolchainPins
    asset_pool_targets: dict = field(default_factory=dict)
    locale: str = "en"
    derived_seeds: dict = field(default_factory=dict)
```

All must support `to_dict()` / `from_dict()`. Follow patterns from `aidm/schemas/vocabulary.py`.

### Deliverable 2: Compile Stage Interface

**File:** `aidm/core/world_compiler.py` (NEW)

The pipeline harness:

```python
class CompileStage(ABC):
    """Abstract base for a single compile stage."""
    @property
    @abstractmethod
    def stage_id(self) -> str: ...          # "lexicon", "rulebook", etc.

    @property
    @abstractmethod
    def stage_number(self) -> int: ...      # 1, 2, 3, etc.

    @property
    @abstractmethod
    def depends_on(self) -> tuple[str, ...]: ...  # ("lexicon", "semantics")

    @abstractmethod
    def execute(self, context: CompileContext) -> StageResult: ...

@dataclass
class CompileContext:
    """Mutable context passed between stages. Accumulates outputs."""
    inputs: CompileInputs                   # Frozen inputs
    content_pack: ContentPack               # Frozen content pack (from loader)
    workspace: Path                         # Compile workspace directory
    derived_seeds: dict                     # Stage-specific seeds
    stage_outputs: dict                     # {stage_id: output_data}
    provenance: ProvenanceStore             # PROV-DM tracking
    logger: logging.Logger

@dataclass(frozen=True)
class StageResult:
    stage_id: str
    status: str                             # "success", "failed", "skipped"
    output_files: tuple                     # Files written
    warnings: tuple = ()
    error: Optional[str] = None
    elapsed_ms: int = 0

class WorldCompiler:
    """Orchestrates world compilation through registered stages."""

    def __init__(self, inputs: CompileInputs):
        self._inputs = inputs
        self._stages: dict[str, CompileStage] = {}
        self._results: list[StageResult] = []

    def register_stage(self, stage: CompileStage) -> None:
        """Register a compile stage. Order determined by dependencies."""

    def compile(self) -> CompileReport:
        """Execute all registered stages in dependency order.

        1. Stage 0: Validate inputs + create workspace
        2. Execute stages respecting depends_on (topological sort)
        3. Stage 8: Finalize hashes + write manifest

        Returns CompileReport with overall status.
        """

    def _derive_seeds(self, world_seed: int) -> dict:
        """Derive child seeds for each stage from world_seed.

        Uses sha256(f"{world_seed}:{stage_name}") → int.
        Deterministic: same world_seed always produces same child seeds.
        """
```

### Deliverable 3: Stage 0 — Validate Inputs

Implement within `world_compiler.py` or as a built-in stage:

1. Validate all required inputs against schemas (§1.3 of contract)
2. Verify content pack exists and is loadable
3. Verify toolchain pins don't contain "latest"
4. Derive child seeds from `world_seed`
5. Create compile workspace directory
6. Write `compile_inputs.json` (frozen snapshot)

Validation is **fail-closed**: any failure halts compilation.

### Deliverable 4: Stage 8 — Finalize

Implement within `world_compiler.py` or as a built-in stage:

1. Compute SHA-256 hash of every file in the bundle workspace
2. Write `bundle_hashes.json`
3. Compute root bundle hash: `sha256(sorted(all_file_hashes))`
4. Write `world_manifest.json` (§2.8 of contract)
5. Write `compile_report.json` with stage timings, warnings, status

### Deliverable 5: Compile Report Schema

```python
@dataclass(frozen=True)
class CompileReport:
    status: str                     # "success", "partial", "failed"
    world_id: str                   # sha256(world_seed + content_pack_id + pins_hash)[:32]
    root_hash: str                  # Bundle root hash
    stage_results: tuple            # Tuple of StageResult
    total_elapsed_ms: int
    warnings: tuple = ()
    error: Optional[str] = None
```

### Deliverable 6: Tests

**File:** `tests/test_world_compiler.py` (NEW)

1. CompileInputs validation rejects missing genre/tone/naming_style
2. CompileInputs validation rejects negative world_seed
3. CompileInputs validation rejects "latest" in toolchain_pins
4. Seed derivation is deterministic (same world_seed → same child seeds)
5. Stage dependency ordering (topological sort test)
6. Stage 0 creates workspace + writes compile_inputs.json
7. Stage 8 computes correct file hashes
8. Stage 8 writes valid world_manifest.json
9. Full compile with stub stages produces valid bundle structure
10. Failed stage halts downstream dependents
11. CompileReport round-trip serialization
12. Empty content pack is valid input (produces empty bundle)

Create a `StubStage` test helper that implements `CompileStage` with configurable success/failure.

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| World Compiler contract | `docs/contracts/WORLD_COMPILER.md` | Canonical — follow exactly |
| Prep orchestrator (pattern) | `aidm/core/prep_orchestrator.py` | Reference for job queue pattern |
| Provenance tracking | `aidm/core/provenance.py` | Use for PROV-DM in compile context |
| FrozenWorldStateView | `aidm/core/state.py` | Reference for deterministic hashing |
| Campaign schemas | `aidm/schemas/campaign.py` | Reference for PrepJob/AssetRecord patterns |
| Content pack loader | `aidm/lens/content_pack_loader.py` | May or may not exist yet — if it does, use it |
| Content pack data | `aidm/data/content_pack/` | Extracted JSON files |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `docs/contracts/WORLD_COMPILER.md` | FULL CONTRACT — especially §1 (Inputs), §2.0 (Stage 0), §2.8 (Stage 8), §2.9 (Dependency Graph), §3 (Bundle File Tree) |
| 1 | `docs/schemas/world_bundle.schema.json` | WorldManifest, BundleHashes JSON schemas |
| 2 | `aidm/core/prep_orchestrator.py` | Job queue + idempotency pattern |
| 2 | `aidm/schemas/campaign.py` | PrepJob deterministic ID pattern |
| 3 | `aidm/core/provenance.py` | PROV-DM tracing |

## STOP CONDITIONS

- If the content pack loader (`aidm/lens/content_pack_loader.py`) doesn't exist yet, create a minimal stub that loads JSON files from the content_pack directory. The real loader will come from WO-CONTENT-PACK-SCHEMA-001.
- The compiler must work with ZERO registered stages (just Stage 0 validation + Stage 8 finalization). Stage-specific implementations come from separate WOs.

## DELIVERY

- New files: `aidm/schemas/world_compile.py`, `aidm/core/world_compiler.py`, `tests/test_world_compiler.py`
- Full test suite run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-WORLDCOMPILE-SCAFFOLD-001_completion.md`

## RULES

- All schema dataclasses MUST be frozen
- WorldCompiler class itself is NOT frozen (it accumulates state during compile)
- CompileContext is NOT frozen (stages write to it)
- CompileReport, StageResult, CompileInputs ARE frozen
- Deterministic: same inputs → same outputs. `compile_timestamp` is the ONLY non-deterministic field.
- No imports from `aidm/lens/` or `aidm/immersion/` — the compiler is a core pipeline
- Follow existing code style in `aidm/core/prep_orchestrator.py`

---

END OF INSTRUCTION PACKET
