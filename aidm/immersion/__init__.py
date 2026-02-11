"""M3 Immersion Layer — Pluggable adapters for atmospheric enhancement.

Re-exports all public symbols for convenient imports.
All immersion outputs are atmospheric only — never mechanical authority.

API STABILITY:
    All symbols in __all__ are PUBLIC_STABLE as of M3 freeze.
    Future milestones may ADD new exports but must not remove or
    rename existing ones without a migration plan.

    Protocols (STTAdapter, TTSAdapter, AudioMixerAdapter, ImageAdapter)
    define the adapter contract surface. New backends implement these
    protocols — the protocols themselves are frozen.

    Pure functions (compute_scene_audio_state, compute_grid_state) have
    frozen signatures. New keyword arguments are permitted (with defaults)
    but positional arguments must not change.

    Stubs (Stub*Adapter) are always-available defaults. Their behavior
    (canned responses, empty bytes, placeholder results) is part of the
    contract and must not change.

    Factory functions (create_*_adapter) may gain new backend keys but
    the default backend must remain "stub".
"""

# --- PUBLIC_STABLE: STT adapter contract ---
from aidm.immersion.stt_adapter import (
    STTAdapter,          # PUBLIC_STABLE: Protocol
    StubSTTAdapter,      # PUBLIC_STABLE: Default implementation
    create_stt_adapter,  # PUBLIC_STABLE: Factory
)

# --- PUBLIC_STABLE: TTS adapter contract ---
from aidm.immersion.tts_adapter import (
    TTSAdapter,          # PUBLIC_STABLE: Protocol
    StubTTSAdapter,      # PUBLIC_STABLE: Default implementation
    create_tts_adapter,  # PUBLIC_STABLE: Factory
)

# --- PUBLIC_STABLE: Kokoro TTS backend ---
from aidm.immersion.kokoro_tts_adapter import (
    KokoroTTSAdapter,    # PUBLIC_STABLE: Real TTS backend
)

# --- PUBLIC_STABLE: Audio mixer contract ---
from aidm.immersion.audio_mixer import (
    AudioMixerAdapter,          # PUBLIC_STABLE: Protocol
    StubAudioMixerAdapter,      # PUBLIC_STABLE: Default implementation
    compute_scene_audio_state,  # PUBLIC_STABLE: Pure function
)

# --- PUBLIC_STABLE: Image adapter contract ---
from aidm.immersion.image_adapter import (
    ImageAdapter,          # PUBLIC_STABLE: Protocol
    StubImageAdapter,      # PUBLIC_STABLE: Default implementation
    create_image_adapter,  # PUBLIC_STABLE: Factory
)

# --- PUBLIC_STABLE: Grid computation ---
from aidm.immersion.contextual_grid import (
    compute_grid_state,  # PUBLIC_STABLE: Pure function
)

# --- PUBLIC_STABLE: Attribution ---
from aidm.immersion.attribution import (
    AttributionStore,  # PUBLIC_STABLE: Persistence manager
)

# --- PUBLIC_STABLE: Table-Native UX (WO-025) ---
from aidm.immersion.combat_receipt import (
    CombatReceipt,       # PUBLIC_STABLE: Combat receipt dataclass
    ReceiptTome,         # PUBLIC_STABLE: Receipt collection
    create_receipt,      # PUBLIC_STABLE: Factory function
    format_parchment,    # PUBLIC_STABLE: Formatting function
)

from aidm.immersion.ghost_stencil import (
    StencilShape,        # PUBLIC_STABLE: Stencil shape enum
    GhostStencil,        # PUBLIC_STABLE: Phantom AoE overlay
    FrozenStencil,       # PUBLIC_STABLE: Confirmed stencil
    create_stencil,      # PUBLIC_STABLE: Factory function
    nudge_stencil,       # PUBLIC_STABLE: Stencil manipulation
    confirm_stencil,     # PUBLIC_STABLE: Confirmation function
)

from aidm.immersion.judges_lens import (
    HPStatus,            # PUBLIC_STABLE: HP status enum
    EntityInspection,    # PUBLIC_STABLE: Entity inspection dataclass
    EntityStateView,     # PUBLIC_STABLE: Entity state view
    JudgesLens,          # PUBLIC_STABLE: Inspection interface
    inspect_entity,      # PUBLIC_STABLE: Inspection function
)

__all__ = [
    # STT — PUBLIC_STABLE
    "STTAdapter",
    "StubSTTAdapter",
    "create_stt_adapter",
    # TTS — PUBLIC_STABLE
    "TTSAdapter",
    "StubTTSAdapter",
    "create_tts_adapter",
    "KokoroTTSAdapter",
    # Audio — PUBLIC_STABLE
    "AudioMixerAdapter",
    "StubAudioMixerAdapter",
    "compute_scene_audio_state",
    # Image — PUBLIC_STABLE
    "ImageAdapter",
    "StubImageAdapter",
    "create_image_adapter",
    # Grid — PUBLIC_STABLE
    "compute_grid_state",
    # Attribution — PUBLIC_STABLE
    "AttributionStore",
    # Table-Native UX — PUBLIC_STABLE
    "CombatReceipt",
    "ReceiptTome",
    "create_receipt",
    "format_parchment",
    "StencilShape",
    "GhostStencil",
    "FrozenStencil",
    "create_stencil",
    "nudge_stencil",
    "confirm_stencil",
    "HPStatus",
    "EntityInspection",
    "EntityStateView",
    "JudgesLens",
    "inspect_entity",
]
