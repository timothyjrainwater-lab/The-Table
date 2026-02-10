"""Canonical ID system for AIDM entity and asset identification.

This module implements the R0 Canonical ID Schema, providing deterministic,
type-safe, human-readable identifiers for all mechanically relevant entities.

**Authority:** R0_CANONICAL_ID_SCHEMA.md (Agent A)
**Status:** Implementation (M0 → M1)
**Determinism:** All ID generation is deterministic (same inputs → same outputs)

Design Principles:
- P1. Determinism First: No UUIDs, timestamps, or random numbers
- P2. Type Safety: Namespace isolation prevents cross-type collisions
- P3. Human Readability: IDs inspectable in logs without lookup tables
- P4. Provenance Transparency: IDs reveal creation context for debugging

ID Namespaces (7 total):
1. mechanical_id: Rules entities (spells, items, conditions) - Global scope
2. entity_id: Runtime entities (PCs, NPCs, monsters) - Campaign-scoped
3. asset_id: Generated assets (portraits, sounds, backdrops) - Campaign-scoped
4. session_id: Game sessions - Campaign-scoped
5. event_id: Event log entries - Session-scoped
6. campaign_id: Campaign instances - User-scoped
7. prepjob_id: Preparation phase jobs - Campaign-scoped
"""

import hashlib
import re
from typing import Optional


# =============================================================================
# Namespace 1: Mechanical IDs (Rules Entities)
# =============================================================================

# Valid domains for mechanical IDs (R0 spec line 74)
VALID_MECHANICAL_DOMAINS = frozenset({
    'spell',
    'item',
    'condition',
    'feat',
    'class_feature',
    'monster_template',
    'action'
})


def mechanical_id(domain: str, canonical_name: str) -> str:
    """Generate mechanical ID for rules entities (global scope).

    Format: <domain>.<canonical_name>
    Example: spell.fireball, item.longsword, condition.stunned

    Args:
        domain: Rules domain (spell, item, condition, feat, class_feature,
                monster_template, action)
        canonical_name: SRD-style snake_case identifier (lowercase, alphanumeric + underscore)

    Returns:
        Mechanical ID string

    Raises:
        ValueError: If domain invalid or canonical_name malformed

    Determinism: Name = ID (no generation, purely structural)
    """
    if domain not in VALID_MECHANICAL_DOMAINS:
        raise ValueError(
            f"Invalid mechanical ID domain: '{domain}'. "
            f"Valid domains: {sorted(VALID_MECHANICAL_DOMAINS)}"
        )

    # Validate canonical_name format (snake_case, alphanumeric + underscore, lowercase)
    if not canonical_name:
        raise ValueError("canonical_name cannot be empty")

    if not canonical_name.replace('_', '').isalnum():
        raise ValueError(
            f"canonical_name must be alphanumeric + underscore only: '{canonical_name}'"
        )

    if canonical_name != canonical_name.lower():
        raise ValueError(
            f"canonical_name must be lowercase: '{canonical_name}'"
        )

    return f"{domain}.{canonical_name}"


def validate_mechanical_id(mechanical_id_str: str) -> bool:
    """Validate mechanical ID format.

    Args:
        mechanical_id_str: String to validate

    Returns:
        True if valid mechanical ID format, False otherwise

    Validation:
        - Must contain exactly one '.'
        - Domain must be in VALID_MECHANICAL_DOMAINS
        - Name must be snake_case (alphanumeric + underscore, lowercase)
    """
    if '.' not in mechanical_id_str:
        return False

    parts = mechanical_id_str.split('.', 1)
    if len(parts) != 2:
        return False

    domain, name = parts

    # Check domain
    if domain not in VALID_MECHANICAL_DOMAINS:
        return False

    # Check name format
    if not name or not name.replace('_', '').isalnum() or name != name.lower():
        return False

    return True


# =============================================================================
# Namespace 2: Entity IDs (Runtime NPCs/Monsters/PCs)
# =============================================================================

def entity_id(campaign_id: str, entity_type: str, unique_key: str) -> str:
    """Generate entity ID for runtime entities (campaign-scoped).

    Format: entity_<campaign_id>_<12_char_hash>
    Example: entity_camp4f2a_a3f2b8c4e1d9

    Args:
        campaign_id: Campaign ID (e.g., "camp_4f2a8b1c")
        entity_type: Entity type (e.g., "pc", "npc", "monster")
        unique_key: Unique key for entity (e.g., "pc:Theron:2026-02-10T14:30:00")

    Returns:
        Entity ID string

    Raises:
        ValueError: If campaign_id malformed

    Determinism: Same campaign + same unique_key → same ID
    Hash Input: f"{campaign_id}:{entity_type}:{unique_key}"
    Hash Length: 12 characters (48 bits, ~1 in 281 trillion collision probability)
    """
    # Validate campaign_id format (must start with "camp_")
    if not campaign_id.startswith('camp_'):
        raise ValueError(
            f"campaign_id must start with 'camp_': '{campaign_id}'"
        )

    # Generate deterministic hash
    hash_input = f"{campaign_id}:{entity_type}:{unique_key}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    hash_hex = hash_bytes.hex()[:12]  # 12-char hash (48 bits)

    return f"entity_{campaign_id}_{hash_hex}"


def validate_entity_id(entity_id_str: str) -> bool:
    """Validate entity ID format.

    Args:
        entity_id_str: String to validate

    Returns:
        True if valid entity ID format, False otherwise

    Validation:
        - Must match pattern: entity_camp_[0-9a-f]{8}_[0-9a-f]{12}
    """
    pattern = r'^entity_camp_[0-9a-f]{8}_[0-9a-f]{12}$'
    return bool(re.match(pattern, entity_id_str))


# =============================================================================
# Namespace 3: Asset IDs (Generated Images/Audio)
# =============================================================================

def asset_id(campaign_id: str, asset_type: str, semantic_key: str) -> str:
    """Generate asset ID for generated assets (campaign-scoped).

    Format: asset_<campaign_id>_<asset_type>_<12_char_hash>
    Example: asset_camp4f2a_portrait_a3f2b8c4e1d9

    Args:
        campaign_id: Campaign ID (e.g., "camp_4f2a8b1c") or "shared" for shared cache
        asset_type: Asset type (portrait, scene, audio, icon)
        semantic_key: Semantic key for asset (e.g., "npc:theron:default")

    Returns:
        Asset ID string

    Raises:
        ValueError: If campaign_id malformed or asset_type invalid

    Determinism: Same campaign + same semantic_key → same ID
    Hash Input: f"{campaign_id}:{asset_type}:{semantic_key}"
    Hash Length: 12 characters (48 bits)
    """
    # Validate campaign_id format
    if campaign_id != 'shared' and not campaign_id.startswith('camp_'):
        raise ValueError(
            f"campaign_id must start with 'camp_' or be 'shared': '{campaign_id}'"
        )

    # Validate asset_type (alphanumeric + underscore, lowercase)
    if not asset_type or not asset_type.replace('_', '').isalnum() or asset_type != asset_type.lower():
        raise ValueError(
            f"asset_type must be lowercase alphanumeric + underscore: '{asset_type}'"
        )

    # Generate deterministic hash
    hash_input = f"{campaign_id}:{asset_type}:{semantic_key}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    hash_hex = hash_bytes.hex()[:12]  # 12-char hash (48 bits)

    return f"asset_{campaign_id}_{asset_type}_{hash_hex}"


def validate_asset_id(asset_id_str: str) -> bool:
    """Validate asset ID format.

    Args:
        asset_id_str: String to validate

    Returns:
        True if valid asset ID format, False otherwise

    Validation:
        - Must match pattern: asset_(camp_[0-9a-f]{8}|shared)_[a-z_]+_[0-9a-f]{12}
    """
    pattern = r'^asset_(camp_[0-9a-f]{8}|shared)_[a-z_]+_[0-9a-f]{12}$'
    return bool(re.match(pattern, asset_id_str))


# =============================================================================
# Namespace 4: Session IDs
# =============================================================================

def session_id(campaign_id: str, session_seq: int, start_hash: str) -> str:
    """Generate session ID (campaign-scoped).

    Format: session_<campaign_id>_<seq>_<8_char_hash>
    Example: session_camp4f2a_0001_a3f2b8c4

    Args:
        campaign_id: Campaign ID (e.g., "camp_4f2a8b1c")
        session_seq: Sequential session number (1-indexed, 4 digits)
        start_hash: Start hash (e.g., first event hash or timestamp hash)

    Returns:
        Session ID string

    Raises:
        ValueError: If campaign_id malformed or session_seq invalid

    Determinism: Same campaign + same session_seq + same start_hash → same ID
    Hash Input: f"{campaign_id}:{session_seq}:{start_hash}"
    Hash Length: 8 characters (32 bits, sufficient for session-level uniqueness)
    """
    # Validate campaign_id format
    if not campaign_id.startswith('camp_'):
        raise ValueError(
            f"campaign_id must start with 'camp_': '{campaign_id}'"
        )

    # Validate session_seq (must be positive integer)
    if not isinstance(session_seq, int) or session_seq < 1:
        raise ValueError(
            f"session_seq must be positive integer (1-indexed): {session_seq}"
        )

    # Generate deterministic hash
    hash_input = f"{campaign_id}:{session_seq}:{start_hash}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    hash_hex = hash_bytes.hex()[:8]  # 8-char hash (32 bits)

    return f"session_{campaign_id}_{session_seq:04d}_{hash_hex}"


def validate_session_id(session_id_str: str) -> bool:
    r"""Validate session ID format.

    Args:
        session_id_str: String to validate

    Returns:
        True if valid session ID format, False otherwise

    Validation:
        - Must match pattern: session_camp_[0-9a-f]{8}_\d{4}_[0-9a-f]{8}
    """
    pattern = r'^session_camp_[0-9a-f]{8}_\d{4}_[0-9a-f]{8}$'
    return bool(re.match(pattern, session_id_str))


# =============================================================================
# Namespace 5: Event IDs
# =============================================================================

def event_id(session_id_str: str, event_seq: int, event_type: str, event_data_hash: str) -> str:
    """Generate event ID (session-scoped).

    Format: event_<session_id>_<seq>_<8_char_hash>
    Example: event_session_camp4f2a_0001_a3f2b8c4_000001_f1c3d8a6

    Args:
        session_id_str: Session ID (e.g., "session_camp4f2a_0001_a3f2b8c4")
        event_seq: Sequential event number (0-indexed, 6 digits)
        event_type: Event type (e.g., "attack_resolved", "move", "damage")
        event_data_hash: Hash of event data (for integrity verification)

    Returns:
        Event ID string

    Raises:
        ValueError: If session_id malformed or event_seq invalid

    Determinism: Same session + same event_seq + same event_data → same ID
    Hash Input: f"{session_id_str}:{event_seq}:{event_type}:{event_data_hash}"
    Hash Length: 8 characters (32 bits, sufficient for event-level uniqueness)
    """
    # Validate session_id format
    if not validate_session_id(session_id_str):
        raise ValueError(
            f"session_id_str must be valid session ID: '{session_id_str}'"
        )

    # Validate event_seq (must be non-negative integer)
    if not isinstance(event_seq, int) or event_seq < 0:
        raise ValueError(
            f"event_seq must be non-negative integer (0-indexed): {event_seq}"
        )

    # Generate deterministic hash
    hash_input = f"{session_id_str}:{event_seq}:{event_type}:{event_data_hash}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    hash_hex = hash_bytes.hex()[:8]  # 8-char hash (32 bits)

    return f"event_{session_id_str}_{event_seq:06d}_{hash_hex}"


def validate_event_id(event_id_str: str) -> bool:
    r"""Validate event ID format.

    Args:
        event_id_str: String to validate

    Returns:
        True if valid event ID format, False otherwise

    Validation:
        - Must match pattern: event_session_camp_[0-9a-f]{8}_\d{4}_[0-9a-f]{8}_\d{6}_[0-9a-f]{8}
    """
    pattern = r'^event_session_camp_[0-9a-f]{8}_\d{4}_[0-9a-f]{8}_\d{6}_[0-9a-f]{8}$'
    return bool(re.match(pattern, event_id_str))


# =============================================================================
# Namespace 6: Campaign IDs
# =============================================================================

def campaign_id(user_id: str, campaign_title: str, creation_timestamp: str) -> str:
    """Generate campaign ID (user-scoped).

    Format: camp_<8_char_hash>
    Example: camp_4f2a8b1c

    Args:
        user_id: User identifier (e.g., OS username, Steam ID, email hash)
        campaign_title: Campaign title (user-provided string)
        creation_timestamp: ISO timestamp of campaign creation (e.g., "2026-02-10T14:30:00")

    Returns:
        Campaign ID string

    Raises:
        ValueError: If inputs are empty

    Determinism: Same user + same title + same timestamp → same ID
    Hash Input: f"{user_id}:{campaign_title}:{creation_timestamp}"
    Hash Length: 8 characters (32 bits, sufficient for user-level uniqueness)
    """
    # Validate inputs (must be non-empty)
    if not user_id:
        raise ValueError("user_id cannot be empty")
    if not campaign_title:
        raise ValueError("campaign_title cannot be empty")
    if not creation_timestamp:
        raise ValueError("creation_timestamp cannot be empty")

    # Generate deterministic hash
    hash_input = f"{user_id}:{campaign_title}:{creation_timestamp}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    hash_hex = hash_bytes.hex()[:8]  # 8-char hash (32 bits)

    return f"camp_{hash_hex}"


def validate_campaign_id(campaign_id_str: str) -> bool:
    """Validate campaign ID format.

    Args:
        campaign_id_str: String to validate

    Returns:
        True if valid campaign ID format, False otherwise

    Validation:
        - Must match pattern: camp_[0-9a-f]{8}
    """
    pattern = r'^camp_[0-9a-f]{8}$'
    return bool(re.match(pattern, campaign_id_str))


# =============================================================================
# Namespace 7: Prep Job IDs
# =============================================================================

def prepjob_id(campaign_id_str: str, job_type: str, job_params: str) -> str:
    """Generate prep job ID (campaign-scoped).

    Format: prepjob_<campaign_id>_<job_type>_<12_char_hash>
    Example: prepjob_camp4f2a_scaffold_a3f2b8c4e1d9

    Args:
        campaign_id_str: Campaign ID (e.g., "camp_4f2a8b1c")
        job_type: Job type (scaffold, portrait, soundpal, backdrop)
        job_params: Job parameters (deterministic string representation, e.g., JSON)

    Returns:
        Prep job ID string

    Raises:
        ValueError: If campaign_id malformed or job_type invalid

    Determinism: Same campaign + same job_type + same params → same ID (idempotent)
    Hash Input: f"{campaign_id_str}:{job_type}:{job_params}"
    Hash Length: 12 characters (48 bits)
    """
    # Validate campaign_id format
    if not validate_campaign_id(campaign_id_str):
        raise ValueError(
            f"campaign_id_str must be valid campaign ID: '{campaign_id_str}'"
        )

    # Validate job_type (alphanumeric + underscore, lowercase)
    if not job_type or not job_type.replace('_', '').isalnum() or job_type != job_type.lower():
        raise ValueError(
            f"job_type must be lowercase alphanumeric + underscore: '{job_type}'"
        )

    # Generate deterministic hash
    hash_input = f"{campaign_id_str}:{job_type}:{job_params}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    hash_hex = hash_bytes.hex()[:12]  # 12-char hash (48 bits)

    return f"prepjob_{campaign_id_str}_{job_type}_{hash_hex}"


def validate_prepjob_id(prepjob_id_str: str) -> bool:
    """Validate prep job ID format.

    Args:
        prepjob_id_str: String to validate

    Returns:
        True if valid prep job ID format, False otherwise

    Validation:
        - Must match pattern: prepjob_camp_[0-9a-f]{8}_[a-z_]+_[0-9a-f]{12}
    """
    pattern = r'^prepjob_camp_[0-9a-f]{8}_[a-z_]+_[0-9a-f]{12}$'
    return bool(re.match(pattern, prepjob_id_str))


# =============================================================================
# Collision Detection Registry
# =============================================================================

class IDCollisionRegistry:
    """Registry for detecting ID collisions across namespaces.

    Usage:
        registry = IDCollisionRegistry()
        registry.register("entity_camp4f2a_a3f2b8c4e1d9", "entity_id")
        registry.register("asset_camp4f2a_portrait_a3f2b8c4e1d9", "asset_id")  # OK (different namespace)

    Raises:
        ValueError: If ID collision detected within same namespace
    """

    def __init__(self):
        """Initialize empty collision registry."""
        self._registry: dict[str, str] = {}  # ID → namespace mapping

    def register(self, id_str: str, namespace: str) -> None:
        """Register ID in collision registry.

        Args:
            id_str: ID string to register
            namespace: ID namespace (mechanical_id, entity_id, asset_id, etc.)

        Raises:
            ValueError: If ID already registered in same namespace
        """
        if id_str in self._registry:
            existing_namespace = self._registry[id_str]
            if existing_namespace == namespace:
                raise ValueError(
                    f"ID collision detected in namespace '{namespace}': '{id_str}'"
                )
            # Different namespace → allow (namespace isolation prevents true collision)

        self._registry[id_str] = namespace

    def contains(self, id_str: str) -> bool:
        """Check if ID registered.

        Args:
            id_str: ID string to check

        Returns:
            True if ID registered, False otherwise
        """
        return id_str in self._registry

    def get_namespace(self, id_str: str) -> Optional[str]:
        """Get namespace for registered ID.

        Args:
            id_str: ID string to look up

        Returns:
            Namespace string if ID registered, None otherwise
        """
        return self._registry.get(id_str)

    def clear(self) -> None:
        """Clear all registered IDs."""
        self._registry.clear()
