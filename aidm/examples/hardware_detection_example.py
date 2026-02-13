"""Example integration of hardware detection and model selection.

Demonstrates complete workflow from hardware detection to model loading
with error handling and fallback mechanisms.

Usage:
    python -m aidm.examples.hardware_detection_example
"""

import logging
from typing import Optional

from aidm.core.hardware_detector import HardwareDetector, detect_hardware
from aidm.core.model_selector import ModelSelector, select_model_for_hardware
from aidm.schemas.hardware_capability import HardwareCapabilities, HardwareTier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main example demonstrating hardware detection and model selection."""

    print("=" * 80)
    print("Hardware Detection & Model Selection Example")
    print("=" * 80)
    print()

    # Step 1: Detect Hardware
    print("Step 1: Detecting hardware capabilities...")
    print("-" * 80)

    try:
        capabilities = detect_hardware()

        print(f"✓ Hardware detection complete!")
        print(f"  Tier: {capabilities.tier.value.upper()}")
        print(f"  Has GPU: {capabilities.has_gpu}")
        print(f"  Requires Offload: {capabilities.requires_offload}")
        print()

        if capabilities.gpu_info:
            print(f"  GPU Details:")
            print(f"    Device: {capabilities.gpu_info.device_name}")
            print(f"    VRAM Total: {capabilities.gpu_info.vram_total_gb:.2f} GB")
            print(
                f"    VRAM Available: {capabilities.gpu_info.vram_available_gb:.2f} GB"
            )
            if capabilities.gpu_info.compute_capability:
                print(f"    Compute Capability: {capabilities.gpu_info.compute_capability}")
        else:
            print(f"  No GPU detected (CPU-only mode)")

        print()
        print(f"  CPU Details:")
        print(f"    Processor: {capabilities.cpu_info.processor}")
        print(f"    Physical Cores: {capabilities.cpu_info.physical_cores}")
        print(f"    Logical Cores: {capabilities.cpu_info.logical_cores}")
        print(f"    RAM Total: {capabilities.cpu_info.ram_total_gb:.2f} GB")
        print(f"    RAM Available: {capabilities.cpu_info.ram_available_gb:.2f} GB")
        print()

        if capabilities.detection_errors:
            print(f"  ⚠ Warnings during detection:")
            for error in capabilities.detection_errors:
                print(f"    - {error}")
            print()

    except Exception as e:
        logger.error(f"Hardware detection failed: {e}", exc_info=True)
        print(f"✗ Hardware detection failed: {e}")
        print("  Using fallback configuration...")
        capabilities = create_fallback_capabilities()
        print()

    # Step 2: Select Model
    print("Step 2: Selecting appropriate LLM model...")
    print("-" * 80)

    try:
        result = select_model_for_hardware(capabilities)

        print(f"✓ Model selection complete!")
        print(f"  Selected Model: {result.config.model_name}")
        print(f"  Model Size: {result.config.model_size.value}")
        print(f"  Enable Offload: {result.config.enable_offload}")

        if result.config.enable_offload:
            if result.config.offload_layers == 0:
                print(f"  Offload Layers: Auto-determine")
            elif result.config.offload_layers == 999:
                print(f"  Offload Layers: All (full CPU offload)")
            else:
                print(f"  Offload Layers: {result.config.offload_layers}")

        print(f"  Device Map: {result.config.device_map}")
        print(f"  Max Context: {result.config.max_context_length} tokens")

        if result.config.load_in_8bit:
            print(f"  Quantization: 8-bit")
        elif result.config.load_in_4bit:
            print(f"  Quantization: 4-bit")
        else:
            print(f"  Quantization: None (full precision)")

        print()
        print(f"  Reason: {result.reason}")
        print()

        if result.warnings:
            print(f"  ⚠ Warnings:")
            for warning in result.warnings:
                print(f"    - {warning}")
            print()

        if result.fallback_applied:
            print(
                f"  ℹ Fallback Applied: Using smaller model or offload due to hardware limitations."
            )
            print()

    except Exception as e:
        logger.error(f"Model selection failed: {e}", exc_info=True)
        print(f"✗ Model selection failed: {e}")
        print("  Unable to determine appropriate model configuration.")
        return

    # Step 3: Provide Loading Recommendation
    print("Step 3: Model loading recommendation...")
    print("-" * 80)

    print(f"  To load the selected model, use the following configuration:")
    print()
    print(f"  model_config = {{")
    print(f"      'model_name': '{result.config.model_name}',")
    print(f"      'device_map': '{result.config.device_map}',")
    print(f"      'torch_dtype': '{result.config.torch_dtype}',")
    print(f"      'load_in_8bit': {result.config.load_in_8bit},")
    print(f"      'load_in_4bit': {result.config.load_in_4bit},")
    print(f"      'max_length': {result.config.max_context_length},")
    print(f"  }}")
    print()

    # Step 4: Recommendations
    print("Step 4: Performance recommendations...")
    print("-" * 80)

    if capabilities.tier == HardwareTier.HIGH:
        print(f"  ✓ Your hardware is well-suited for LLM inference!")
        print(f"  ✓ 14B models should run smoothly without offload.")
        print(f"  ✓ Expected latency: <500ms per generation (depending on prompt length)")
    elif capabilities.tier == HardwareTier.MEDIUM:
        print(f"  ✓ Your hardware can run 7B models effectively.")
        print(f"  ℹ Consider upgrading to ≥12GB VRAM for 14B models.")
        print(f"  ℹ Expected latency: <800ms per generation")
    else:
        print(f"  ⚠ Your hardware has limited LLM inference capability.")
        print(f"  ⚠ CPU offload will significantly increase inference latency (2-10x slower).")
        print(f"  ℹ Consider upgrading to GPU with ≥6GB VRAM for better performance.")
        print(f"  ℹ Expected latency: 2-10 seconds per generation (CPU-dependent)")

    print()
    print("=" * 80)
    print("Hardware detection and model selection complete!")
    print("=" * 80)


def create_fallback_capabilities() -> HardwareCapabilities:
    """Create minimal fallback capabilities when detection fails.

    Returns:
        HardwareCapabilities with FALLBACK tier
    """
    from aidm.schemas.hardware_capability import CPUInfo
    from datetime import datetime

    cpu_info = CPUInfo(
        processor="Unknown CPU",
        physical_cores=4,
        logical_cores=8,
        ram_total_mb=8192,  # Assume 8GB
        ram_available_mb=4096,  # Assume 4GB available
        architecture="x86_64",
    )

    return HardwareCapabilities(
        tier=HardwareTier.FALLBACK,
        gpu_info=None,
        cpu_info=cpu_info,
        detected_at=datetime.utcnow().isoformat(),
        detection_errors=["Hardware detection failed, using fallback configuration"],
    )


if __name__ == "__main__":
    main()
