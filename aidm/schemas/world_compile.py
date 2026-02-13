"""World Compiler input schemas — frozen dataclasses for compile pipeline.

Defines the input contract for the World Compiler: theme brief, toolchain
pins, compile configuration, and the top-level CompileInputs container.

All dataclasses are frozen (immutable). The compiler validates these once
at Stage 0; they flow read-only through all subsequent stages.

Reference: docs/contracts/WORLD_COMPILER.md §1 (Inputs Contract)
Reference: docs/schemas/world_bundle.schema.json

BOUNDARY LAW: No imports from aidm/lens/ or aidm/immersion/.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════
# Validation rejection codes (§1.3)
# ═══════════════════════════════════════════════════════════════════════

IV_001 = "IV-001: content_pack_id does not resolve to a valid content pack"
IV_002 = "IV-002: world_theme_brief is missing required fields (genre, tone, naming_style)"
IV_003 = "IV-003: world_seed is negative or exceeds 64-bit range"
IV_004 = "IV-004: toolchain_pins is missing required pin (llm_model_id, hash_algorithm, schema_version)"
IV_005 = 'IV-005: toolchain_pins contains "latest" or unresolved version references'
IV_006 = "IV-006: compile_config fails schema validation"
IV_007 = "IV-007: content_pack_id version is incompatible with schema_version"

_MAX_64BIT = (2**63) - 1


# ═══════════════════════════════════════════════════════════════════════
# World Theme Brief
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class WorldThemeBrief:
    """Structured theme descriptor for world generation.

    Defines the aesthetic, tonal, and cultural parameters that shape
    how the World Compiler generates names, descriptions, and lore.

    Required fields: genre, tone, naming_style.
    """

    genre: str
    """World genre: 'dark_fantasy', 'sci_fi', 'steampunk', etc."""

    tone: str
    """Narrative tone: 'grim', 'heroic', 'whimsical', etc."""

    naming_style: str
    """Naming convention: 'anglo_saxon', 'latin', 'japanese', etc."""

    technology_level: str = "medieval"
    """Technology era: 'stone_age', 'medieval', 'renaissance', 'industrial', etc."""

    magic_level: str = "high"
    """Magic prevalence: 'none', 'low', 'medium', 'high', 'pervasive'."""

    cosmology_notes: str = ""
    """Freeform notes on the world's cosmology and metaphysics."""

    environmental_palette: tuple = ()
    """Dominant environment types: ('volcanic', 'desert', 'tundra')."""

    def validate(self) -> List[str]:
        """Return list of validation error strings (empty = valid)."""
        errors: List[str] = []
        if not self.genre:
            errors.append(IV_002)
        if not self.tone:
            errors.append(IV_002)
        if not self.naming_style:
            errors.append(IV_002)
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "genre": self.genre,
            "tone": self.tone,
            "naming_style": self.naming_style,
            "technology_level": self.technology_level,
            "magic_level": self.magic_level,
        }
        if self.cosmology_notes:
            d["cosmology_notes"] = self.cosmology_notes
        d["environmental_palette"] = list(self.environmental_palette)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldThemeBrief":
        """Deserialize from dictionary."""
        return cls(
            genre=data["genre"],
            tone=data["tone"],
            naming_style=data["naming_style"],
            technology_level=data.get("technology_level", "medieval"),
            magic_level=data.get("magic_level", "high"),
            cosmology_notes=data.get("cosmology_notes", ""),
            environmental_palette=tuple(data.get("environmental_palette", [])),
        )


# ═══════════════════════════════════════════════════════════════════════
# Toolchain Pins
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ToolchainPins:
    """Pinned versions of all tools used during compilation.

    No field may contain 'latest' or unresolved version references.
    All required pins must be present for compilation to proceed.

    Required: llm_model_id, hash_algorithm, schema_version.
    """

    llm_model_id: str
    """Pinned LLM model ID: 'qwen3-8b-q4'. Never 'latest'."""

    hash_algorithm: str = "sha256"
    """Hash algorithm for integrity checks."""

    schema_version: str = "1.0.0"
    """Schema version for bundle format."""

    image_model_id: str = ""
    """Pinned image gen model. Empty = skip image generation."""

    music_model_id: str = ""
    """Pinned music gen model. Empty = skip music generation."""

    def validate(self) -> List[str]:
        """Return list of validation error strings (empty = valid)."""
        errors: List[str] = []
        if not self.llm_model_id:
            errors.append(IV_004)
        if not self.hash_algorithm:
            errors.append(IV_004)
        if not self.schema_version:
            errors.append(IV_004)
        # Check for "latest" in any pin field
        for pin_value in (
            self.llm_model_id,
            self.hash_algorithm,
            self.schema_version,
            self.image_model_id,
            self.music_model_id,
        ):
            if "latest" in pin_value.lower():
                errors.append(IV_005)
                break
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "llm_model_id": self.llm_model_id,
            "hash_algorithm": self.hash_algorithm,
            "schema_version": self.schema_version,
        }
        if self.image_model_id:
            d["image_model_id"] = self.image_model_id
        if self.music_model_id:
            d["music_model_id"] = self.music_model_id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolchainPins":
        """Deserialize from dictionary."""
        return cls(
            llm_model_id=data["llm_model_id"],
            hash_algorithm=data.get("hash_algorithm", "sha256"),
            schema_version=data.get("schema_version", "1.0.0"),
            image_model_id=data.get("image_model_id", ""),
            music_model_id=data.get("music_model_id", ""),
        )


# ═══════════════════════════════════════════════════════════════════════
# Compile Config
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CompileConfig:
    """Compilation parameters: output directory, log level, stage enables.

    Controls which stages run and where output is written.
    """

    output_dir: str
    """Output directory for the compiled bundle."""

    log_level: str = "INFO"
    """Logging level: 'DEBUG', 'INFO', 'WARNING', 'ERROR'."""

    enable_stages: tuple = ()
    """Stage IDs to enable. Empty = all stages."""

    content_filters: tuple = ()
    """Content filter tags as a frozen tuple of key=value pairs."""

    def validate(self) -> List[str]:
        """Return list of validation error strings (empty = valid)."""
        errors: List[str] = []
        if not self.output_dir:
            errors.append(IV_006)
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
        if self.log_level not in valid_levels:
            errors.append(IV_006)
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "output_dir": self.output_dir,
            "log_level": self.log_level,
            "enable_stages": list(self.enable_stages),
            "content_filters": list(self.content_filters),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompileConfig":
        """Deserialize from dictionary."""
        return cls(
            output_dir=data["output_dir"],
            log_level=data.get("log_level", "INFO"),
            enable_stages=tuple(data.get("enable_stages", [])),
            content_filters=tuple(data.get("content_filters", [])),
        )


# ═══════════════════════════════════════════════════════════════════════
# Compile Inputs (top-level container)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CompileInputs:
    """Top-level container for all world compilation inputs.

    Frozen snapshot of everything needed to reproduce a compile run.
    Written to compile_inputs.json at Stage 0 for reproducibility.

    Reference: docs/contracts/WORLD_COMPILER.md §1
    """

    content_pack_id: str
    """Identifies the content pack (Level 0b data)."""

    world_theme_brief: WorldThemeBrief
    """Structured theme descriptor."""

    world_seed: int
    """Primary seed for all world generation RNG. Non-negative 64-bit."""

    compile_config: CompileConfig
    """Compilation parameters."""

    toolchain_pins: ToolchainPins
    """Pinned versions of all tools."""

    asset_pool_targets: tuple = ()
    """Target sizes for asset pools as frozen tuple of (category, size) pairs."""

    locale: str = "en"
    """BCP-47 locale tag for generated text."""

    derived_seeds: tuple = ()
    """Override derived seeds as frozen tuple of (stage_id, seed) pairs."""

    def validate(self) -> List[str]:
        """Validate all inputs per §1.3. Return list of error strings."""
        errors: List[str] = []
        if not self.content_pack_id:
            errors.append(IV_001)
        errors.extend(self.world_theme_brief.validate())
        if self.world_seed < 0 or self.world_seed > _MAX_64BIT:
            errors.append(IV_003)
        errors.extend(self.compile_config.validate())
        errors.extend(self.toolchain_pins.validate())
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "content_pack_id": self.content_pack_id,
            "world_theme_brief": self.world_theme_brief.to_dict(),
            "world_seed": self.world_seed,
            "compile_config": self.compile_config.to_dict(),
            "toolchain_pins": self.toolchain_pins.to_dict(),
            "locale": self.locale,
        }
        if self.asset_pool_targets:
            d["asset_pool_targets"] = list(
                list(pair) for pair in self.asset_pool_targets
            )
        else:
            d["asset_pool_targets"] = []
        if self.derived_seeds:
            d["derived_seeds"] = {k: v for k, v in self.derived_seeds}
        else:
            d["derived_seeds"] = {}
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompileInputs":
        """Deserialize from dictionary."""
        derived_seeds_raw = data.get("derived_seeds", {})
        if isinstance(derived_seeds_raw, dict):
            derived_seeds = tuple(derived_seeds_raw.items())
        else:
            derived_seeds = tuple(
                tuple(pair) for pair in derived_seeds_raw
            )
        asset_pool_raw = data.get("asset_pool_targets", [])
        if isinstance(asset_pool_raw, dict):
            asset_pool_targets = tuple(asset_pool_raw.items())
        else:
            asset_pool_targets = tuple(
                tuple(pair) for pair in asset_pool_raw
            )
        return cls(
            content_pack_id=data["content_pack_id"],
            world_theme_brief=WorldThemeBrief.from_dict(
                data["world_theme_brief"]
            ),
            world_seed=data["world_seed"],
            compile_config=CompileConfig.from_dict(data["compile_config"]),
            toolchain_pins=ToolchainPins.from_dict(data["toolchain_pins"]),
            asset_pool_targets=asset_pool_targets,
            locale=data.get("locale", "en"),
            derived_seeds=derived_seeds,
        )


# ═══════════════════════════════════════════════════════════════════════
# Stage Result + Compile Report (frozen output schemas)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class StageResult:
    """Result of a single compile stage execution.

    Frozen record of what happened during one stage.
    """

    stage_id: str
    """Stage identifier: 'validate', 'lexicon', 'finalize', etc."""

    status: str
    """Outcome: 'success', 'failed', 'skipped'."""

    output_files: tuple
    """Files written by this stage. Tuple of relative path strings."""

    warnings: tuple = ()
    """Non-fatal warning messages."""

    error: Optional[str] = None
    """Error message if status is 'failed'."""

    elapsed_ms: int = 0
    """Wall-clock time for this stage in milliseconds."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "stage_id": self.stage_id,
            "status": self.status,
            "output_files": list(self.output_files),
            "elapsed_ms": self.elapsed_ms,
        }
        if self.warnings:
            d["warnings"] = list(self.warnings)
        if self.error is not None:
            d["error"] = self.error
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageResult":
        """Deserialize from dictionary."""
        return cls(
            stage_id=data["stage_id"],
            status=data["status"],
            output_files=tuple(data.get("output_files", [])),
            warnings=tuple(data.get("warnings", [])),
            error=data.get("error"),
            elapsed_ms=data.get("elapsed_ms", 0),
        )


@dataclass(frozen=True)
class CompileReport:
    """Final compilation report. Written as compile_report.json.

    Frozen record of the entire compile run: status, timings,
    warnings, and per-stage results.

    Reference: docs/contracts/WORLD_COMPILER.md §2.8
    Reference: docs/schemas/world_bundle.schema.json — CompileReport
    """

    status: str
    """Overall status: 'success', 'partial', 'failed'."""

    world_id: str
    """World identity hash: sha256(world_seed + content_pack_id + pins_hash)[:32]."""

    root_hash: str
    """Bundle root hash: sha256(sorted(all_file_hashes))."""

    stage_results: tuple
    """Per-stage results. Tuple of StageResult."""

    total_elapsed_ms: int
    """Total wall-clock time for the entire compile in milliseconds."""

    warnings: tuple = ()
    """Aggregated non-fatal warnings across all stages."""

    error: Optional[str] = None
    """Top-level error message if status is 'failed'."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "status": self.status,
            "world_id": self.world_id,
            "root_hash": self.root_hash,
            "stage_results": [r.to_dict() for r in self.stage_results],
            "total_elapsed_ms": self.total_elapsed_ms,
        }
        if self.warnings:
            d["warnings"] = list(self.warnings)
        if self.error is not None:
            d["error"] = self.error
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompileReport":
        """Deserialize from dictionary."""
        return cls(
            status=data["status"],
            world_id=data["world_id"],
            root_hash=data["root_hash"],
            stage_results=tuple(
                StageResult.from_dict(r) for r in data.get("stage_results", [])
            ),
            total_elapsed_ms=data["total_elapsed_ms"],
            warnings=tuple(data.get("warnings", [])),
            error=data.get("error"),
        )
