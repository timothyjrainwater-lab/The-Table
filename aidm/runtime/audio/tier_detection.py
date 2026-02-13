"""Hardware tier detection for M3 Audio Pipeline.

Detects GPU VRAM to determine which audio generation strategy to use:
- Enhanced tier (8+ GB VRAM): ACE-Step music generation with headroom
- Recommended tier (6-8 GB VRAM): ACE-Step music generation
- Baseline tier (<6 GB VRAM or CPU-only): Curated music library

Reference: EVAL-04 Hardware Tier Mapping
"""

from typing import Optional
from aidm.schemas.audio import AudioTier, AudioTierConfig


def detect_audio_tier(
    user_override: Optional[str] = None
) -> AudioTierConfig:
    """Detect hardware tier for audio pipeline.

    Probes GPU VRAM to determine audio generation capability.
    Falls back to CPU-only if GPU unavailable.

    Args:
        user_override: User preference override ('curated_only' or 'generative_preferred')

    Returns:
        AudioTierConfig with detected tier and settings
    """
    # Try to detect GPU VRAM
    vram_gb = _detect_vram_gb()

    # Determine tier based on VRAM
    if vram_gb >= 8.0:
        tier: AudioTier = "enhanced"
        use_generative_music = True
    elif vram_gb >= 6.0:
        tier = "recommended"
        use_generative_music = True
    else:
        tier = "baseline"
        use_generative_music = False

    # Apply user override
    if user_override == "curated_only":
        use_generative_music = False
    elif user_override == "generative_preferred":
        # Respect hardware limits (can't force generative on <6 GB)
        pass

    return AudioTierConfig(
        tier=tier,
        vram_gb=vram_gb,
        use_generative_music=use_generative_music,
        use_generative_sfx=False,  # Always False (licensing blocked, EVAL-03)
        user_override=user_override,  # type: ignore
    )


def _detect_vram_gb() -> float:
    """Detect GPU VRAM in GB.

    Returns:
        VRAM in GB, or 0.0 if CPU-only
    """
    try:
        import torch
        if torch.cuda.is_available():
            vram_bytes = torch.cuda.get_device_properties(0).total_memory
            vram_gb = vram_bytes / (1024 ** 3)
            return vram_gb
    except ImportError:
        # PyTorch not available
        pass
    except Exception:
        # CUDA detection failed
        pass

    # Fallback: CPU-only
    return 0.0


def get_tier_description(tier: AudioTier) -> str:
    """Get human-readable tier description.

    Args:
        tier: Audio tier

    Returns:
        Tier description string
    """
    descriptions = {
        "baseline": "Baseline (<6 GB VRAM or CPU-only) — Curated music library",
        "recommended": "Recommended (6-8 GB VRAM) — ACE-Step music generation",
        "enhanced": "Enhanced (8+ GB VRAM) — ACE-Step music generation (optimized)",
    }
    return descriptions.get(tier, "Unknown tier")
