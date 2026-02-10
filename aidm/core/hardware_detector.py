"""Hardware capability detection implementation.

Detects GPU (VRAM, CUDA) and CPU (cores, RAM) to assign appropriate LLM tier.
Supports NVIDIA GPUs via PyTorch/CUDA, with fallback to CPU-only detection.

Usage:
    from aidm.core.hardware_detector import HardwareDetector

    detector = HardwareDetector()
    capabilities = detector.detect()

    if capabilities.is_high_tier:
        # Load 14B model
        pass
    elif capabilities.is_medium_tier:
        # Load 7B model
        pass
    else:
        # Load smaller model with offload
        pass
"""

import logging
import platform
import psutil
from datetime import datetime
from typing import Optional

from aidm.schemas.hardware_capability import (
    HardwareCapabilities,
    HardwareTier,
    GPUInfo,
    GPUVendor,
    CPUInfo,
    TierAssignmentResult,
    VRAM_THRESHOLD_HIGH_TIER,
    VRAM_THRESHOLD_MEDIUM_TIER,
    VRAM_THRESHOLD_FALLBACK,
    RAM_THRESHOLD_MINIMUM,
)

# Configure logging
logger = logging.getLogger(__name__)


class HardwareDetector:
    """Detects hardware capabilities for LLM tier assignment.

    Performs GPU and CPU detection to determine appropriate model tier.
    Supports caching to avoid repeated detection calls.

    Attributes:
        _cached_capabilities: Cached hardware capabilities (None until first detection)
    """

    def __init__(self):
        """Initialize hardware detector."""
        self._cached_capabilities: Optional[HardwareCapabilities] = None

    def detect(self, force_refresh: bool = False) -> HardwareCapabilities:
        """Detect hardware capabilities and assign tier.

        Args:
            force_refresh: Force re-detection even if cached

        Returns:
            HardwareCapabilities with assigned tier
        """
        # Return cached capabilities if available and not forcing refresh
        if self._cached_capabilities is not None and not force_refresh:
            logger.info("Returning cached hardware capabilities")
            return self._cached_capabilities

        logger.info("Starting hardware capability detection")

        # Detect CPU
        cpu_info = self._detect_cpu()

        # Detect GPU
        gpu_info = self._detect_gpu()

        # Assign tier based on detected hardware
        tier_result = self._assign_tier(gpu_info, cpu_info)

        # Build capabilities object
        capabilities = HardwareCapabilities(
            tier=tier_result.assigned_tier,
            gpu_info=gpu_info,
            cpu_info=cpu_info,
            detected_at=datetime.utcnow().isoformat(),
            detection_errors=tier_result.warnings,
        )

        # Cache capabilities
        self._cached_capabilities = capabilities

        # Log detection results
        logger.info(
            f"Hardware detection complete: tier={capabilities.tier.value}, "
            f"has_gpu={capabilities.has_gpu}, requires_offload={capabilities.requires_offload}"
        )
        if gpu_info:
            logger.info(
                f"GPU detected: {gpu_info.device_name}, "
                f"VRAM={gpu_info.vram_total_gb:.2f}GB total, "
                f"{gpu_info.vram_available_gb:.2f}GB available"
            )
        logger.info(
            f"CPU detected: {cpu_info.physical_cores} cores, "
            f"RAM={cpu_info.ram_total_gb:.2f}GB total, "
            f"{cpu_info.ram_available_gb:.2f}GB available"
        )

        return capabilities

    def _detect_cpu(self) -> CPUInfo:
        """Detect CPU hardware information.

        Returns:
            CPUInfo with detected CPU specs
        """
        try:
            # Get CPU info using platform and psutil
            processor = platform.processor() or "Unknown CPU"
            physical_cores = psutil.cpu_count(logical=False) or 0
            logical_cores = psutil.cpu_count(logical=True) or 0

            # Get RAM info
            memory = psutil.virtual_memory()
            ram_total_mb = int(memory.total / (1024 * 1024))
            ram_available_mb = int(memory.available / (1024 * 1024))

            # Get architecture
            architecture = platform.machine()

            cpu_info = CPUInfo(
                processor=processor,
                physical_cores=physical_cores,
                logical_cores=logical_cores,
                ram_total_mb=ram_total_mb,
                ram_available_mb=ram_available_mb,
                architecture=architecture,
            )

            logger.debug(f"CPU detection successful: {cpu_info.to_dict()}")
            return cpu_info

        except Exception as e:
            logger.error(f"CPU detection failed: {e}", exc_info=True)
            # Return minimal CPUInfo on failure
            return CPUInfo(
                processor="Unknown",
                physical_cores=1,
                logical_cores=1,
                ram_total_mb=8192,  # Assume 8GB minimum
                ram_available_mb=4096,
                architecture="unknown",
            )

    def _detect_gpu(self) -> Optional[GPUInfo]:
        """Detect GPU hardware information.

        Returns:
            GPUInfo if GPU detected, None if no GPU or detection failed
        """
        # Try PyTorch CUDA detection first (most reliable)
        gpu_info = self._detect_gpu_pytorch()
        if gpu_info:
            return gpu_info

        # Fallback: Try other detection methods
        # (Future: Add ROCm for AMD, Metal for Apple Silicon)

        logger.info("No GPU detected or GPU detection failed")
        return None

    def _detect_gpu_pytorch(self) -> Optional[GPUInfo]:
        """Detect GPU using PyTorch CUDA.

        Returns:
            GPUInfo if CUDA GPU detected, None otherwise
        """
        try:
            import torch

            if not torch.cuda.is_available():
                logger.info("PyTorch CUDA not available")
                return None

            # Get primary GPU (device 0)
            device_id = 0
            device_name = torch.cuda.get_device_name(device_id)

            # Get VRAM information
            device_props = torch.cuda.get_device_properties(device_id)
            vram_total_mb = int(device_props.total_memory / (1024 * 1024))

            # Get available VRAM (total - allocated)
            vram_allocated_mb = int(
                torch.cuda.memory_allocated(device_id) / (1024 * 1024)
            )
            vram_available_mb = vram_total_mb - vram_allocated_mb

            # Get compute capability
            compute_capability = f"{device_props.major}.{device_props.minor}"

            gpu_info = GPUInfo(
                vendor=GPUVendor.NVIDIA,  # PyTorch CUDA is NVIDIA-only
                device_name=device_name,
                vram_total_mb=vram_total_mb,
                vram_available_mb=vram_available_mb,
                compute_capability=compute_capability,
                cuda_available=True,
                device_id=device_id,
            )

            logger.debug(f"GPU detection successful (PyTorch): {gpu_info.to_dict()}")
            return gpu_info

        except ImportError:
            logger.debug("PyTorch not installed, skipping CUDA detection")
            return None
        except Exception as e:
            logger.warning(f"PyTorch GPU detection failed: {e}")
            return None

    def _assign_tier(
        self, gpu_info: Optional[GPUInfo], cpu_info: CPUInfo
    ) -> TierAssignmentResult:
        """Assign hardware tier based on detected capabilities.

        Tier Assignment Logic:
        - HIGH: GPU with ≥12 GB VRAM
        - MEDIUM: GPU with 6-12 GB VRAM
        - FALLBACK: GPU with <6 GB VRAM, or CPU-only

        Args:
            gpu_info: Detected GPU information (None if no GPU)
            cpu_info: Detected CPU information

        Returns:
            TierAssignmentResult with assigned tier and reasoning
        """
        warnings = []

        # Check RAM minimum requirement
        if cpu_info.ram_total_mb < RAM_THRESHOLD_MINIMUM:
            warnings.append(
                f"System RAM ({cpu_info.ram_total_gb:.1f}GB) below minimum "
                f"requirement ({RAM_THRESHOLD_MINIMUM / 1024}GB). "
                "LLM inference may be slow or fail."
            )

        # No GPU detected → FALLBACK tier
        if gpu_info is None or not gpu_info.cuda_available:
            return TierAssignmentResult(
                assigned_tier=HardwareTier.FALLBACK,
                reason="No CUDA-capable GPU detected. Using CPU fallback.",
                warnings=warnings,
                fallback_required=True,
                offload_required=True,
            )

        # GPU detected: Check VRAM thresholds
        vram_mb = gpu_info.vram_available_mb

        # HIGH tier: ≥12 GB VRAM
        if vram_mb >= VRAM_THRESHOLD_HIGH_TIER:
            return TierAssignmentResult(
                assigned_tier=HardwareTier.HIGH,
                reason=f"GPU with {gpu_info.vram_available_gb:.1f}GB VRAM detected. "
                "Supports 14B models without offload.",
                warnings=warnings,
                fallback_required=False,
                offload_required=False,
            )

        # MEDIUM tier: 6-12 GB VRAM
        if vram_mb >= VRAM_THRESHOLD_MEDIUM_TIER:
            # Check if close to 6GB threshold (marginal for 7B)
            if vram_mb < 7168:  # <7 GB
                warnings.append(
                    f"GPU VRAM ({gpu_info.vram_available_gb:.1f}GB) is marginal "
                    "for 7B models. Consider enabling CPU offload if OOM errors occur."
                )

            return TierAssignmentResult(
                assigned_tier=HardwareTier.MEDIUM,
                reason=f"GPU with {gpu_info.vram_available_gb:.1f}GB VRAM detected. "
                "Supports 7B models without offload.",
                warnings=warnings,
                fallback_required=False,
                offload_required=False,
            )

        # FALLBACK tier: <6 GB VRAM (or <4 GB for strict fallback)
        if vram_mb >= VRAM_THRESHOLD_FALLBACK:
            # 4-6 GB VRAM: Can run smaller models with possible offload
            warnings.append(
                f"GPU VRAM ({gpu_info.vram_available_gb:.1f}GB) insufficient "
                "for 7B models. Using smaller model with CPU offload."
            )
            return TierAssignmentResult(
                assigned_tier=HardwareTier.FALLBACK,
                reason=f"GPU with {gpu_info.vram_available_gb:.1f}GB VRAM detected. "
                "Requires smaller model (3B) or CPU offload.",
                warnings=warnings,
                fallback_required=True,
                offload_required=True,
            )

        # <4 GB VRAM: Strict CPU fallback
        warnings.append(
            f"GPU VRAM ({gpu_info.vram_available_gb:.1f}GB) too low for LLM inference. "
            "Using CPU-only mode."
        )
        return TierAssignmentResult(
            assigned_tier=HardwareTier.FALLBACK,
            reason=f"GPU VRAM ({gpu_info.vram_available_gb:.1f}GB) insufficient. "
            "Using CPU fallback.",
            warnings=warnings,
            fallback_required=True,
            offload_required=True,
        )

    def clear_cache(self):
        """Clear cached hardware capabilities.

        Forces re-detection on next detect() call.
        """
        self._cached_capabilities = None
        logger.debug("Hardware capability cache cleared")


# ═══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════════════


def detect_hardware() -> HardwareCapabilities:
    """Convenience function to detect hardware capabilities.

    Returns:
        HardwareCapabilities with assigned tier
    """
    detector = HardwareDetector()
    return detector.detect()


def get_recommended_model_size(capabilities: HardwareCapabilities) -> str:
    """Get recommended model size for hardware tier.

    Args:
        capabilities: Detected hardware capabilities

    Returns:
        Model size string ("14B", "7B", "3B")
    """
    if capabilities.is_high_tier:
        return "14B"
    elif capabilities.is_medium_tier:
        return "7B"
    else:
        return "3B"


def should_enable_offload(capabilities: HardwareCapabilities) -> bool:
    """Check if CPU offload should be enabled.

    Args:
        capabilities: Detected hardware capabilities

    Returns:
        True if offload recommended
    """
    return capabilities.requires_offload
