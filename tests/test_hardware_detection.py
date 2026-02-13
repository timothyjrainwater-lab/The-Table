"""Unit tests for hardware detection and model selection.

Tests tier assignment logic, model selection, and offload configuration
for various hardware configurations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from aidm.core.hardware_detector import HardwareDetector
from aidm.core.model_selector import ModelSelector, ModelSize
from aidm.schemas.hardware_capability import (
    HardwareCapabilities,
    HardwareTier,
    GPUInfo,
    GPUVendor,
    CPUInfo,
)


# ═══════════════════════════════════════════════════════════════════════
# Hardware Detector Tests
# ═══════════════════════════════════════════════════════════════════════


class TestHardwareDetector:
    """Tests for HardwareDetector tier assignment logic."""

    def test_high_tier_assignment_12gb_vram(self):
        """Test HIGH tier assignment for 12GB VRAM GPU."""
        detector = HardwareDetector()

        gpu_info = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            device_name="NVIDIA GeForce RTX 3060 12GB",
            vram_total_mb=12288,
            vram_available_mb=12288,
            compute_capability="8.6",
            cuda_available=True,
            device_id=0,
        )

        cpu_info = CPUInfo(
            processor="Intel Core i7-9700K",
            physical_cores=8,
            logical_cores=8,
            ram_total_mb=16384,
            ram_available_mb=12288,
            architecture="x86_64",
        )

        result = detector._assign_tier(gpu_info, cpu_info)

        assert result.assigned_tier == HardwareTier.HIGH
        assert not result.fallback_required
        assert not result.offload_required

    def test_high_tier_assignment_8gb_vram(self):
        """Test HIGH tier assignment for 8GB VRAM GPU (Spark-aligned threshold)."""
        detector = HardwareDetector()

        gpu_info = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            device_name="NVIDIA GeForce RTX 2080",
            vram_total_mb=8192,  # Exactly 8GB (HIGH tier threshold)
            vram_available_mb=8192,
            compute_capability="7.5",
            cuda_available=True,
            device_id=0,
        )

        cpu_info = CPUInfo(
            processor="Intel Core i7-9700K",
            physical_cores=8,
            logical_cores=8,
            ram_total_mb=16384,
            ram_available_mb=12288,
            architecture="x86_64",
        )

        result = detector._assign_tier(gpu_info, cpu_info)

        assert result.assigned_tier == HardwareTier.HIGH
        assert not result.fallback_required
        assert not result.offload_required

    def test_medium_tier_assignment_7gb_vram(self):
        """Test MEDIUM tier assignment for 7GB VRAM GPU.

        Note: With Spark-aligned thresholds, 8GB VRAM is HIGH tier (≥8GB).
        This test verifies 7GB VRAM gets MEDIUM tier (6-8GB range).
        """
        detector = HardwareDetector()

        gpu_info = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            device_name="NVIDIA GeForce GTX 1070",
            vram_total_mb=7168,  # 7GB (MEDIUM tier: 6-8GB)
            vram_available_mb=7168,
            compute_capability="6.1",
            cuda_available=True,
            device_id=0,
        )

        cpu_info = CPUInfo(
            processor="AMD Ryzen 5 3600",
            physical_cores=6,
            logical_cores=12,
            ram_total_mb=16384,
            ram_available_mb=12288,
            architecture="x86_64",
        )

        result = detector._assign_tier(gpu_info, cpu_info)

        assert result.assigned_tier == HardwareTier.MEDIUM
        assert not result.fallback_required
        assert not result.offload_required

    def test_fallback_tier_assignment_4gb_vram(self):
        """Test FALLBACK tier assignment for 4GB VRAM GPU."""
        detector = HardwareDetector()

        gpu_info = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            device_name="NVIDIA GeForce GTX 1050 Ti",
            vram_total_mb=4096,
            vram_available_mb=4096,
            compute_capability="6.1",
            cuda_available=True,
            device_id=0,
        )

        cpu_info = CPUInfo(
            processor="Intel Core i5-8400",
            physical_cores=6,
            logical_cores=6,
            ram_total_mb=16384,
            ram_available_mb=12288,
            architecture="x86_64",
        )

        result = detector._assign_tier(gpu_info, cpu_info)

        assert result.assigned_tier == HardwareTier.FALLBACK
        assert result.fallback_required
        assert result.offload_required

    def test_fallback_tier_cpu_only(self):
        """Test FALLBACK tier assignment for CPU-only (no GPU)."""
        detector = HardwareDetector()

        gpu_info = None

        cpu_info = CPUInfo(
            processor="Intel Core i7-9700K",
            physical_cores=8,
            logical_cores=8,
            ram_total_mb=16384,
            ram_available_mb=12288,
            architecture="x86_64",
        )

        result = detector._assign_tier(gpu_info, cpu_info)

        assert result.assigned_tier == HardwareTier.FALLBACK
        assert result.fallback_required
        assert result.offload_required
        assert "No CUDA-capable GPU detected" in result.reason

    def test_marginal_vram_warning(self):
        """Test warning for marginal VRAM (6-7GB)."""
        detector = HardwareDetector()

        gpu_info = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            device_name="NVIDIA GeForce GTX 1660",
            vram_total_mb=6144,  # Exactly 6GB
            vram_available_mb=6144,
            compute_capability="7.5",
            cuda_available=True,
            device_id=0,
        )

        cpu_info = CPUInfo(
            processor="AMD Ryzen 5 3600",
            physical_cores=6,
            logical_cores=12,
            ram_total_mb=16384,
            ram_available_mb=12288,
            architecture="x86_64",
        )

        result = detector._assign_tier(gpu_info, cpu_info)

        assert result.assigned_tier == HardwareTier.MEDIUM
        assert len(result.warnings) > 0
        assert "marginal" in result.warnings[0].lower()


# ═══════════════════════════════════════════════════════════════════════
# Model Selector Tests
# ═══════════════════════════════════════════════════════════════════════


class TestModelSelector:
    """Tests for ModelSelector model configuration logic."""

    def test_high_tier_selects_14b_model(self):
        """Test that HIGH tier selects 14B model without offload."""
        selector = ModelSelector()

        capabilities = HardwareCapabilities(
            tier=HardwareTier.HIGH,
            gpu_info=GPUInfo(
                vendor=GPUVendor.NVIDIA,
                device_name="NVIDIA GeForce RTX 3090",
                vram_total_mb=24576,
                vram_available_mb=24576,
                cuda_available=True,
            ),
            cpu_info=CPUInfo(
                processor="Intel Core i9",
                physical_cores=8,
                logical_cores=16,
                ram_total_mb=32768,
                ram_available_mb=24576,
            ),
        )

        result = selector.select_model(capabilities)

        assert result.config.model_size == ModelSize.LARGE_14B
        assert not result.config.enable_offload
        assert not result.fallback_applied

    def test_medium_tier_selects_7b_model(self):
        """Test that MEDIUM tier selects 7B model without offload."""
        selector = ModelSelector()

        capabilities = HardwareCapabilities(
            tier=HardwareTier.MEDIUM,
            gpu_info=GPUInfo(
                vendor=GPUVendor.NVIDIA,
                device_name="NVIDIA GeForce RTX 2060",
                vram_total_mb=8192,
                vram_available_mb=8192,
                cuda_available=True,
            ),
            cpu_info=CPUInfo(
                processor="AMD Ryzen 5",
                physical_cores=6,
                logical_cores=12,
                ram_total_mb=16384,
                ram_available_mb=12288,
            ),
        )

        result = selector.select_model(capabilities)

        assert result.config.model_size == ModelSize.MEDIUM_7B
        assert not result.config.enable_offload
        assert not result.fallback_applied

    def test_fallback_tier_selects_3b_model_with_offload(self):
        """Test that FALLBACK tier selects 3B model with offload."""
        selector = ModelSelector()

        capabilities = HardwareCapabilities(
            tier=HardwareTier.FALLBACK,
            gpu_info=GPUInfo(
                vendor=GPUVendor.NVIDIA,
                device_name="NVIDIA GeForce GTX 1050 Ti",
                vram_total_mb=4096,
                vram_available_mb=4096,
                cuda_available=True,
            ),
            cpu_info=CPUInfo(
                processor="Intel Core i5",
                physical_cores=4,
                logical_cores=4,
                ram_total_mb=16384,
                ram_available_mb=12288,
            ),
        )

        result = selector.select_model(capabilities)

        assert result.config.model_size == ModelSize.SMALL_3B
        assert result.config.enable_offload
        assert result.config.load_in_8bit  # Quantization enabled for marginal GPU
        assert result.fallback_applied

    def test_cpu_only_full_offload(self):
        """Test that CPU-only mode enables full offload."""
        selector = ModelSelector()

        capabilities = HardwareCapabilities(
            tier=HardwareTier.FALLBACK,
            gpu_info=None,  # No GPU
            cpu_info=CPUInfo(
                processor="Intel Core i7",
                physical_cores=8,
                logical_cores=8,
                ram_total_mb=16384,
                ram_available_mb=12288,
            ),
        )

        result = selector.select_model(capabilities)

        assert result.config.model_size == ModelSize.SMALL_3B
        assert result.config.enable_offload
        assert result.config.offload_layers == 999  # Full CPU offload
        assert result.config.device_map == "cpu"
        assert result.fallback_applied


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════


class TestHardwareIntegration:
    """Integration tests for hardware detection → model selection pipeline."""

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    @patch("platform.processor")
    @patch("platform.machine")
    def test_cpu_detection_fallback(
        self, mock_machine, mock_processor, mock_memory, mock_cpu_count
    ):
        """Test CPU detection with mocked psutil."""
        mock_cpu_count.side_effect = [8, 16]  # physical, logical
        mock_memory.return_value = Mock(
            total=16 * 1024 * 1024 * 1024, available=12 * 1024 * 1024 * 1024
        )
        mock_processor.return_value = "Intel Core i7-9700K"
        mock_machine.return_value = "x86_64"

        detector = HardwareDetector()
        cpu_info = detector._detect_cpu()

        assert cpu_info.physical_cores == 8
        assert cpu_info.logical_cores == 16
        assert cpu_info.ram_total_gb == 16.0
        assert "Intel" in cpu_info.processor

    def test_caching_behavior(self):
        """Test that hardware detection results are cached."""
        detector = HardwareDetector()

        # First detection
        capabilities1 = detector.detect()

        # Second detection (should return cached)
        capabilities2 = detector.detect()

        assert capabilities1 is capabilities2

        # Force refresh
        capabilities3 = detector.detect(force_refresh=True)

        # Should be new object but same values
        assert capabilities3.tier == capabilities1.tier


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
