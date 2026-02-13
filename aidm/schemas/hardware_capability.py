"""Hardware capability detection and LLM tier selection.

Implements dynamic model tier assignment based on available VRAM and CPU specs.
Supports automatic fallback and offload when VRAM is insufficient.

Tier System (Aligned with Spark Adapter Architecture):
- High-tier: GPU with ≥8 GB VRAM (14B models)
- Medium-tier: GPU with 6-8 GB VRAM (7B models)
- Fallback-tier: CPU or low VRAM (<6 GB, smaller models with offload)

Reference:
- Instruction Packet 03 - Hardware Detection & Tier Selection
- SPARK_ADAPTER_ARCHITECTURE.md - Spark model loading system
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
import platform


class HardwareTier(Enum):
    """Hardware capability tiers for LLM model selection.

    Tier determines which model size can be loaded and whether
    offload to CPU is required.
    """

    HIGH = "high"       # 14B models, no offload
    MEDIUM = "medium"   # 7B models, no offload
    FALLBACK = "fallback"  # Smaller models or offload required
    UNKNOWN = "unknown" # Detection failed


class GPUVendor(Enum):
    """Detected GPU vendor."""

    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"  # Apple Silicon
    UNKNOWN = "unknown"


@dataclass
class GPUInfo:
    """GPU hardware information.

    Attributes:
        vendor: GPU vendor (NVIDIA, AMD, Intel, etc.)
        device_name: GPU device name (e.g., "NVIDIA GeForce RTX 3060")
        vram_total_mb: Total VRAM in MB
        vram_available_mb: Available VRAM in MB
        compute_capability: CUDA compute capability (NVIDIA only)
        cuda_available: Whether CUDA is available
        device_id: GPU device ID (0 for primary)
    """

    vendor: GPUVendor = GPUVendor.UNKNOWN
    device_name: str = ""
    vram_total_mb: int = 0
    vram_available_mb: int = 0
    compute_capability: Optional[str] = None  # e.g., "7.5" for RTX 2060
    cuda_available: bool = False
    device_id: int = 0

    @property
    def vram_total_gb(self) -> float:
        """Total VRAM in GB."""
        return self.vram_total_mb / 1024.0

    @property
    def vram_available_gb(self) -> float:
        """Available VRAM in GB."""
        return self.vram_available_mb / 1024.0

    def has_sufficient_vram(self, required_mb: int) -> bool:
        """Check if available VRAM is sufficient for requirement.

        Args:
            required_mb: Required VRAM in MB

        Returns:
            True if available VRAM >= required amount
        """
        return self.vram_available_mb >= required_mb

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "vendor": self.vendor.value,
            "device_name": self.device_name,
            "vram_total_mb": self.vram_total_mb,
            "vram_available_mb": self.vram_available_mb,
            "vram_total_gb": round(self.vram_total_gb, 2),
            "vram_available_gb": round(self.vram_available_gb, 2),
            "compute_capability": self.compute_capability,
            "cuda_available": self.cuda_available,
            "device_id": self.device_id,
        }


@dataclass
class CPUInfo:
    """CPU hardware information.

    Attributes:
        processor: CPU model name
        physical_cores: Number of physical CPU cores
        logical_cores: Number of logical CPU cores (with hyperthreading)
        ram_total_mb: Total system RAM in MB
        ram_available_mb: Available system RAM in MB
        architecture: CPU architecture (x86_64, arm64, etc.)
    """

    processor: str = ""
    physical_cores: int = 0
    logical_cores: int = 0
    ram_total_mb: int = 0
    ram_available_mb: int = 0
    architecture: str = ""

    @property
    def ram_total_gb(self) -> float:
        """Total RAM in GB."""
        return self.ram_total_mb / 1024.0

    @property
    def ram_available_gb(self) -> float:
        """Available RAM in GB."""
        return self.ram_available_mb / 1024.0

    def has_sufficient_ram(self, required_mb: int) -> bool:
        """Check if available RAM is sufficient for requirement.

        Args:
            required_mb: Required RAM in MB

        Returns:
            True if available RAM >= required amount
        """
        return self.ram_available_mb >= required_mb

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "processor": self.processor,
            "physical_cores": self.physical_cores,
            "logical_cores": self.logical_cores,
            "ram_total_mb": self.ram_total_mb,
            "ram_available_mb": self.ram_available_mb,
            "ram_total_gb": round(self.ram_total_gb, 2),
            "ram_available_gb": round(self.ram_available_gb, 2),
            "architecture": self.architecture,
        }


@dataclass
class HardwareCapabilities:
    """Complete hardware capability profile.

    Combines GPU and CPU information to determine appropriate LLM tier.

    Attributes:
        tier: Assigned hardware tier (HIGH/MEDIUM/FALLBACK)
        gpu_info: GPU information (None if no GPU detected)
        cpu_info: CPU information
        detected_at: Timestamp of detection (for caching)
        detection_errors: Any errors encountered during detection
    """

    tier: HardwareTier = HardwareTier.UNKNOWN
    gpu_info: Optional[GPUInfo] = None
    cpu_info: Optional[CPUInfo] = None
    detected_at: str = ""
    detection_errors: List[str] = field(default_factory=list)

    @property
    def has_gpu(self) -> bool:
        """Check if GPU is available."""
        return self.gpu_info is not None and self.gpu_info.cuda_available

    @property
    def is_high_tier(self) -> bool:
        """Check if hardware supports high-tier (14B) models."""
        return self.tier == HardwareTier.HIGH

    @property
    def is_medium_tier(self) -> bool:
        """Check if hardware supports medium-tier (7B) models."""
        return self.tier == HardwareTier.MEDIUM

    @property
    def is_fallback_tier(self) -> bool:
        """Check if hardware requires fallback (offload/smaller models)."""
        return self.tier == HardwareTier.FALLBACK

    @property
    def requires_offload(self) -> bool:
        """Check if model loading requires CPU offload.

        Offload needed when:
        - No GPU available
        - GPU VRAM < required for selected model
        """
        if not self.has_gpu:
            return True

        # Check if VRAM is marginal (requires offload even for smaller models)
        if self.gpu_info and self.gpu_info.vram_total_mb < 6144:  # <6 GB
            return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "tier": self.tier.value,
            "has_gpu": self.has_gpu,
            "requires_offload": self.requires_offload,
            "gpu_info": self.gpu_info.to_dict() if self.gpu_info else None,
            "cpu_info": self.cpu_info.to_dict() if self.cpu_info else None,
            "detected_at": self.detected_at,
            "detection_errors": self.detection_errors,
        }


@dataclass
class ModelTierRequirements:
    """VRAM and RAM requirements for each model tier.

    Defines minimum hardware requirements to run models without offload.

    Attributes:
        tier: Hardware tier this requirement applies to
        model_size: Model parameter count (e.g., "14B", "7B")
        vram_required_mb: Minimum VRAM required (no offload)
        vram_recommended_mb: Recommended VRAM for optimal performance
        ram_required_mb: Minimum RAM required
        ram_recommended_mb: Recommended RAM
    """

    tier: HardwareTier
    model_size: str
    vram_required_mb: int
    vram_recommended_mb: int
    ram_required_mb: int
    ram_recommended_mb: int

    def can_run_on_gpu(self, gpu_info: GPUInfo) -> bool:
        """Check if GPU meets minimum requirements.

        Args:
            gpu_info: GPU hardware information

        Returns:
            True if GPU VRAM >= required minimum
        """
        return gpu_info.vram_available_mb >= self.vram_required_mb

    def can_run_on_cpu(self, cpu_info: CPUInfo) -> bool:
        """Check if CPU meets minimum requirements.

        Args:
            cpu_info: CPU hardware information

        Returns:
            True if RAM >= required minimum
        """
        return cpu_info.ram_available_mb >= self.ram_required_mb

    @property
    def vram_required_gb(self) -> float:
        """Required VRAM in GB."""
        return self.vram_required_mb / 1024.0

    @property
    def vram_recommended_gb(self) -> float:
        """Recommended VRAM in GB."""
        return self.vram_recommended_mb / 1024.0


# ═══════════════════════════════════════════════════════════════════════
# Tier Requirements Constants
# ═══════════════════════════════════════════════════════════════════════

# Aligned with Spark Adapter Architecture (SPARK_ADAPTER_ARCHITECTURE.md)
TIER_REQUIREMENTS: Dict[HardwareTier, ModelTierRequirements] = {
    HardwareTier.HIGH: ModelTierRequirements(
        tier=HardwareTier.HIGH,
        model_size="14B",
        vram_required_mb=8192,  # 8 GB minimum (aligned with Spark)
        vram_recommended_mb=12288,  # 12 GB recommended
        ram_required_mb=16384,  # 16 GB RAM
        ram_recommended_mb=32768,  # 32 GB RAM recommended
    ),
    HardwareTier.MEDIUM: ModelTierRequirements(
        tier=HardwareTier.MEDIUM,
        model_size="7B",
        vram_required_mb=6144,  # 6 GB minimum
        vram_recommended_mb=8192,  # 8 GB recommended
        ram_required_mb=16384,  # 16 GB RAM
        ram_recommended_mb=24576,  # 24 GB RAM recommended
    ),
    HardwareTier.FALLBACK: ModelTierRequirements(
        tier=HardwareTier.FALLBACK,
        model_size="3B",  # Smaller model or offloaded
        vram_required_mb=0,  # CPU fallback, no VRAM required
        vram_recommended_mb=3072,  # 3 GB if GPU available
        ram_required_mb=4096,  # 4 GB RAM minimum (aligned with Spark)
        ram_recommended_mb=8192,  # 8 GB RAM recommended
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# VRAM Thresholds
# ═══════════════════════════════════════════════════════════════════════

# VRAM thresholds for automatic tier assignment
# NOTE: Aligned with Spark Adapter Architecture (SPARK_ADAPTER_ARCHITECTURE.md)
VRAM_THRESHOLD_HIGH_TIER = 8192  # 8 GB → High tier (14B models)
VRAM_THRESHOLD_MEDIUM_TIER = 6144  # 6 GB → Medium tier (7B models)
VRAM_THRESHOLD_FALLBACK = 3072  # 3 GB → Fallback tier (offload required)

# RAM thresholds
RAM_THRESHOLD_MINIMUM = 8192  # 8 GB minimum for any LLM inference


@dataclass
class TierAssignmentResult:
    """Result of automatic tier assignment.

    Attributes:
        assigned_tier: Tier assigned based on hardware detection
        reason: Human-readable reason for tier assignment
        warnings: Any warnings about hardware limitations
        fallback_required: Whether fallback to smaller model is required
        offload_required: Whether CPU offload is required
    """

    assigned_tier: HardwareTier
    reason: str
    warnings: List[str] = field(default_factory=list)
    fallback_required: bool = False
    offload_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "assigned_tier": self.assigned_tier.value,
            "reason": self.reason,
            "warnings": self.warnings,
            "fallback_required": self.fallback_required,
            "offload_required": self.offload_required,
        }
