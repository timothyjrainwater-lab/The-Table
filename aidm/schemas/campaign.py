"""M2 Campaign schemas — Session Zero, Campaign Manifest, Prep Jobs, Assets.

Schema-first definitions for campaign lifecycle management:
- SessionZeroConfig: Ruleset capture + boundary configuration
- CampaignPaths: Directory layout convention
- CampaignManifest: Version-pinned campaign metadata
- PrepJob: Deterministic prep task with idempotency
- AssetRecord: Campaign asset with deterministic ID and provenance

Reference: docs/design/SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md (SZ-RBC-001)
Reference: docs/design/LOCAL_RUNTIME_PACKAGING_STRATEGY.md (LRP-001)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
import hashlib
import json


# ---------------------------------------------------------------------------
# SessionZeroConfig
# ---------------------------------------------------------------------------

@dataclass
class SessionZeroConfig:
    """Session Zero ruleset and boundary configuration.

    Captures all table-level decisions before campaign start.
    Once play begins, this config is FROZEN — changes are recorded
    as append-only amendments, not in-place edits.

    Per SZ-RBC-001:
    - Ruleset foundation (base rules, optional rules)
    - Alignment system mode
    - Preparation depth
    - Visibility preferences
    - Creative boundaries (table-defined)
    - Doctrine enforcement
    - Fail-open-to-RAW policy
    """

    config_schema_version: str = "1.0"
    """Schema version for forward compatibility."""

    ruleset_id: str = "RAW_3.5"
    """Base ruleset identifier."""

    optional_rules: List[str] = field(default_factory=list)
    """Explicitly enabled optional rules (e.g., 'flanking', 'massive_damage')."""

    alignment_mode: str = "strict"
    """Alignment system mode: 'strict' | 'inferred' | 'narrative_only'."""

    preparation_depth: str = "standard"
    """Prep depth: 'light' | 'standard' | 'deep'."""

    visibility_prefs: Dict[str, Any] = field(default_factory=dict)
    """Condition visibility, enemy info display preferences."""

    creative_boundaries: Dict[str, Any] = field(default_factory=dict)
    """Table-defined creative boundaries (not model ethics)."""

    doctrine_enforcement: bool = True
    """Whether monster doctrine enforcement is enabled."""

    fail_open_to_raw: bool = True
    """On ambiguity, fail to RAW rather than blocking."""

    amendments: List[Dict[str, Any]] = field(default_factory=list)
    """Append-only ruleset amendments applied after initial config."""

    def validate(self) -> List[str]:
        """Validate config values. Returns list of errors (empty = valid)."""
        errors = []

        if self.alignment_mode not in ("strict", "inferred", "narrative_only"):
            errors.append(
                f"Invalid alignment_mode: '{self.alignment_mode}'. "
                f"Must be 'strict', 'inferred', or 'narrative_only'."
            )

        if self.preparation_depth not in ("light", "standard", "deep"):
            errors.append(
                f"Invalid preparation_depth: '{self.preparation_depth}'. "
                f"Must be 'light', 'standard', or 'deep'."
            )

        if not self.ruleset_id:
            errors.append("ruleset_id must not be empty.")

        if not self.config_schema_version:
            errors.append("config_schema_version must not be empty.")

        return errors

    def add_amendment(self, amendment: Dict[str, Any]) -> None:
        """Append an amendment to the config (append-only)."""
        self.amendments.append(amendment)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "config_schema_version": self.config_schema_version,
            "ruleset_id": self.ruleset_id,
            "optional_rules": self.optional_rules,
            "alignment_mode": self.alignment_mode,
            "preparation_depth": self.preparation_depth,
            "visibility_prefs": self.visibility_prefs,
            "creative_boundaries": self.creative_boundaries,
            "doctrine_enforcement": self.doctrine_enforcement,
            "fail_open_to_raw": self.fail_open_to_raw,
            "amendments": self.amendments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionZeroConfig":
        """Create from dictionary."""
        return cls(
            config_schema_version=data.get("config_schema_version", "1.0"),
            ruleset_id=data.get("ruleset_id", "RAW_3.5"),
            optional_rules=data.get("optional_rules", []),
            alignment_mode=data.get("alignment_mode", "strict"),
            preparation_depth=data.get("preparation_depth", "standard"),
            visibility_prefs=data.get("visibility_prefs", {}),
            creative_boundaries=data.get("creative_boundaries", {}),
            doctrine_enforcement=data.get("doctrine_enforcement", True),
            fail_open_to_raw=data.get("fail_open_to_raw", True),
            amendments=data.get("amendments", []),
        )


# ---------------------------------------------------------------------------
# CampaignPaths
# ---------------------------------------------------------------------------

@dataclass
class CampaignPaths:
    """Directory layout convention for a campaign.

    All paths are relative to the campaign root directory.
    """

    root: str = ""
    """Campaign root directory (absolute path when resolved)."""

    events: str = "events.jsonl"
    """Relative path to event log."""

    intents: str = "intents.jsonl"
    """Relative path to intent log."""

    assets: str = "assets"
    """Relative path to assets directory."""

    prep: str = "prep"
    """Relative path to prep directory."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "root": self.root,
            "events": self.events,
            "intents": self.intents,
            "assets": self.assets,
            "prep": self.prep,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampaignPaths":
        """Create from dictionary."""
        return cls(
            root=data.get("root", ""),
            events=data.get("events", "events.jsonl"),
            intents=data.get("intents", "intents.jsonl"),
            assets=data.get("assets", "assets"),
            prep=data.get("prep", "prep"),
        )


# ---------------------------------------------------------------------------
# CampaignManifest
# ---------------------------------------------------------------------------

@dataclass
class CampaignManifest:
    """Campaign manifest with version pinning.

    Pins engine version, model version, tool versions, and session zero config.
    Allows old campaigns to remain playable despite upgrades.

    The created_at timestamp is for UX only and is excluded from
    deterministic replay verification.
    """

    # Required fields — no defaults (BL-017: inject-only)
    campaign_id: str
    """Unique campaign identifier (BL-017: must be injected by caller)."""

    title: str = ""
    """Human-readable campaign title."""

    engine_version: str = "0.1.0"
    """Engine version at campaign creation."""

    config_schema_version: str = "1.0"
    """Schema version for forward compatibility."""

    created_at: str = ""
    """ISO timestamp of campaign creation (UX only, not in replay hash)."""

    master_seed: int = 0
    """Master RNG seed for deterministic campaign."""

    session_zero: SessionZeroConfig = field(default_factory=SessionZeroConfig)
    """Session Zero configuration (frozen after campaign start)."""

    paths: CampaignPaths = field(default_factory=CampaignPaths)
    """Campaign directory layout."""

    tool_versions: Dict[str, str] = field(default_factory=dict)
    """Optional version pinning for tools (e.g., {'python': '3.11'})."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "campaign_id": self.campaign_id,
            "title": self.title,
            "engine_version": self.engine_version,
            "config_schema_version": self.config_schema_version,
            "created_at": self.created_at,
            "master_seed": self.master_seed,
            "session_zero": self.session_zero.to_dict(),
            "paths": self.paths.to_dict(),
            "tool_versions": self.tool_versions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampaignManifest":
        """Create from dictionary."""
        session_zero = SessionZeroConfig.from_dict(data.get("session_zero", {}))
        paths = CampaignPaths.from_dict(data.get("paths", {}))

        return cls(
            campaign_id=data["campaign_id"],
            title=data.get("title", ""),
            engine_version=data.get("engine_version", "0.1.0"),
            config_schema_version=data.get("config_schema_version", "1.0"),
            created_at=data.get("created_at", ""),
            master_seed=data.get("master_seed", 0),
            session_zero=session_zero,
            paths=paths,
            tool_versions=data.get("tool_versions", {}),
        )


# ---------------------------------------------------------------------------
# PrepJob
# ---------------------------------------------------------------------------

def compute_job_id(campaign_id: str, job_type: str, stable_key: str) -> str:
    """Compute deterministic job ID from campaign + type + key.

    Same inputs always produce the same job_id.
    """
    raw = f"{campaign_id}:{job_type}:{stable_key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class PrepJob:
    """Deterministic prep task with idempotency support.

    Jobs are ordered by (job_type, stable_key, insertion_index)
    for deterministic queue construction.

    Idempotency: if a job with the same job_id exists with status=done
    and matching content_hash, the job is skipped on re-run.
    """

    job_id: str = ""
    """Deterministic ID: sha256(campaign_id + job_type + stable_key)[:16]."""

    job_type: str = "INIT_SCAFFOLD"
    """Job type: INIT_SCAFFOLD | SEED_ASSETS | BUILD_START_STATE | VALIDATE_READY."""

    stable_key: str = ""
    """Secondary sort key for deterministic ordering within job type."""

    insertion_index: int = 0
    """Insertion order for total ordering."""

    status: str = "pending"
    """Job status: pending | running | done | failed."""

    inputs: Dict[str, Any] = field(default_factory=dict)
    """JSON-serializable job inputs."""

    outputs: Dict[str, Any] = field(default_factory=dict)
    """JSON-serializable job outputs (populated on completion)."""

    content_hash: Optional[str] = None
    """SHA256 hash of outputs for idempotency checking."""

    error: Optional[str] = None
    """Error message if status == 'failed'."""

    def compute_output_hash(self) -> str:
        """Compute deterministic hash of outputs."""
        raw = json.dumps(self.outputs, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def validate(self) -> List[str]:
        """Validate job fields. Returns list of errors."""
        errors = []

        valid_types = ("INIT_SCAFFOLD", "SEED_ASSETS", "BUILD_START_STATE", "VALIDATE_READY")
        if self.job_type not in valid_types:
            errors.append(f"Invalid job_type: '{self.job_type}'. Must be one of {valid_types}.")

        valid_statuses = ("pending", "running", "done", "failed")
        if self.status not in valid_statuses:
            errors.append(f"Invalid status: '{self.status}'. Must be one of {valid_statuses}.")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "stable_key": self.stable_key,
            "insertion_index": self.insertion_index,
            "status": self.status,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }
        if self.content_hash is not None:
            result["content_hash"] = self.content_hash
        if self.error is not None:
            result["error"] = self.error
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrepJob":
        """Create from dictionary."""
        return cls(
            job_id=data.get("job_id", ""),
            job_type=data.get("job_type", "INIT_SCAFFOLD"),
            stable_key=data.get("stable_key", ""),
            insertion_index=data.get("insertion_index", 0),
            status=data.get("status", "pending"),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            content_hash=data.get("content_hash"),
            error=data.get("error"),
        )


# ---------------------------------------------------------------------------
# AssetRecord
# ---------------------------------------------------------------------------

def compute_asset_id(campaign_id: str, kind: str, semantic_key: str) -> str:
    """Compute deterministic asset ID from campaign + kind + key.

    Same inputs always produce the same asset_id. Not RNG-driven.
    """
    raw = f"{campaign_id}:{kind}:{semantic_key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class AssetRecord:
    """Campaign asset record with deterministic ID and provenance.

    For M2, assets are placeholders (metadata only, zero-byte files).
    Real asset generation is deferred to M3.

    Per LRP-001: assets are atmospheric only, never mechanical authority.
    """

    asset_id: str = ""
    """Deterministic ID: sha256(campaign_id + kind + semantic_key)[:16]."""

    kind: str = "PLACEHOLDER"
    """Asset kind: PLACEHOLDER | PORTRAIT | SCENE | AMBIENT_AUDIO | MAP | HANDOUT."""

    semantic_key: str = ""
    """Semantic identifier (e.g., 'generic:tavern:interior:v1')."""

    content_hash: str = ""
    """SHA256 hash of file contents (empty string for placeholders)."""

    path: str = ""
    """Relative path within campaign assets directory."""

    provenance: str = "GENERATED"
    """Asset provenance: GENERATED | BUNDLED | MANUAL | SHARED_CACHE."""

    regen_policy: str = "REGEN_ON_MISS"
    """What to do if asset is missing: REGEN_ON_MISS | FAIL_ON_MISS."""

    def validate(self) -> List[str]:
        """Validate asset record fields. Returns list of errors."""
        errors = []

        valid_kinds = ("PLACEHOLDER", "PORTRAIT", "SCENE", "AMBIENT_AUDIO", "MAP", "HANDOUT")
        if self.kind not in valid_kinds:
            errors.append(f"Invalid kind: '{self.kind}'. Must be one of {valid_kinds}.")

        valid_provenance = ("GENERATED", "BUNDLED", "MANUAL", "SHARED_CACHE")
        if self.provenance not in valid_provenance:
            errors.append(f"Invalid provenance: '{self.provenance}'.")

        valid_policies = ("REGEN_ON_MISS", "FAIL_ON_MISS")
        if self.regen_policy not in valid_policies:
            errors.append(f"Invalid regen_policy: '{self.regen_policy}'.")

        if not self.semantic_key:
            errors.append("semantic_key must not be empty.")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "asset_id": self.asset_id,
            "kind": self.kind,
            "semantic_key": self.semantic_key,
            "content_hash": self.content_hash,
            "path": self.path,
            "provenance": self.provenance,
            "regen_policy": self.regen_policy,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetRecord":
        """Create from dictionary."""
        return cls(
            asset_id=data.get("asset_id", ""),
            kind=data.get("kind", "PLACEHOLDER"),
            semantic_key=data.get("semantic_key", ""),
            content_hash=data.get("content_hash", ""),
            path=data.get("path", ""),
            provenance=data.get("provenance", "GENERATED"),
            regen_policy=data.get("regen_policy", "REGEN_ON_MISS"),
        )
