"""Just-In-Time Fact Acquisition Protocol for Lens-Spark membrane.

When Box queries data that Lens doesn't have, the Lens must request it from
Spark, validate the response, store with provenance, and serve to Box.

WO-008: JIT Fact Acquisition Protocol
Reference: RQ-LENS-001 Finding 5 (Required Attributes Per Entity Class)
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from aidm.core.lens_index import LensIndex, SourceTier

logger = logging.getLogger(__name__)


# ==============================================================================
# REQUIRED ATTRIBUTES PER ENTITY CLASS (RQ-LENS-001 Finding 5)
# ==============================================================================

CREATURE_REQUIRED = ["size", "position", "hit_points", "armor_class"]
OBJECT_REQUIRED = ["size", "position", "material", "hardness"]
TERRAIN_REQUIRED = ["position", "elevation", "movement_cost"]

# Attributes that can have default values
ALLOWED_DEFAULTS: Dict[str, Any] = {
    "material": "wood",
    "hardness": 5,
    "movement_cost": 1,
    "elevation": 0,
}

# Attributes that MUST come from Spark (no defaults allowed)
FORBIDDEN_DEFAULTS = {"size", "position", "hit_points", "armor_class"}

# Valid entity classes
VALID_ENTITY_CLASSES = {"creature", "object", "terrain"}

# Valid size category values (per D&D 3.5e)
VALID_SIZE_CATEGORIES = {
    "fine", "diminutive", "tiny", "small", "medium",
    "large", "huge", "gargantuan", "colossal"
}


# ==============================================================================
# REQUEST SCHEMA
# ==============================================================================

@dataclass(frozen=True)
class FactRequest:
    """Request for facts about an entity from Spark.

    Immutable for determinism and logging.
    """

    request_id: str
    """Unique request identifier (UUID)."""

    entity_id: str
    """Entity to query facts for."""

    required_attributes: List[str]
    """Attributes that must be provided."""

    context: Optional[str] = None
    """Optional context hint for Spark."""

    timeout_ms: int = 5000
    """Timeout in milliseconds (default 5000)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "request_id": self.request_id,
            "entity_id": self.entity_id,
            "required_attributes": list(self.required_attributes),
            "context": self.context,
            "timeout_ms": self.timeout_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FactRequest':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            FactRequest instance
        """
        return cls(
            request_id=data["request_id"],
            entity_id=data["entity_id"],
            required_attributes=list(data["required_attributes"]),
            context=data.get("context"),
            timeout_ms=data.get("timeout_ms", 5000),
        )


# ==============================================================================
# RESPONSE SCHEMA
# ==============================================================================

@dataclass(frozen=True)
class FactResponse:
    """Response from Spark containing facts about an entity.

    Immutable for determinism and logging.
    """

    request_id: str
    """Request ID this response is for."""

    entity_id: str
    """Entity the facts describe."""

    facts: Dict[str, Any]
    """Attribute name → value mapping."""

    source: str
    """Source identifier (e.g., 'spark_v1')."""

    valid: bool
    """Whether the response is valid."""

    error: Optional[str] = None
    """Error message if not valid."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        # Convert facts dict for proper serialization
        serialized_facts = {}
        for key, value in self.facts.items():
            if hasattr(value, 'to_dict'):
                serialized_facts[key] = value.to_dict()
            else:
                serialized_facts[key] = value

        return {
            "request_id": self.request_id,
            "entity_id": self.entity_id,
            "facts": serialized_facts,
            "source": self.source,
            "valid": self.valid,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FactResponse':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            FactResponse instance
        """
        # Convert facts dict to immutable form
        facts = dict(data.get("facts", {}))

        return cls(
            request_id=data["request_id"],
            entity_id=data["entity_id"],
            facts=facts,
            source=data["source"],
            valid=data["valid"],
            error=data.get("error"),
        )


# ==============================================================================
# VALIDATION RESULT
# ==============================================================================

@dataclass(frozen=True)
class ValidationResult:
    """Result of validating a FactResponse.

    Immutable for determinism.
    """

    valid: bool
    """Whether the response passed all validation checks."""

    errors: List[str] = field(default_factory=list)
    """List of validation error messages."""

    warnings: List[str] = field(default_factory=list)
    """List of validation warning messages."""

    def __post_init__(self):
        """Ensure list fields are properly initialized for frozen dataclass."""
        # For frozen dataclass, we need to use object.__setattr__
        if not isinstance(self.errors, list):
            object.__setattr__(self, 'errors', list(self.errors))
        if not isinstance(self.warnings, list):
            object.__setattr__(self, 'warnings', list(self.warnings))


# ==============================================================================
# ACQUISITION RESULT
# ==============================================================================

@dataclass(frozen=True)
class AcquisitionResult:
    """Result of a full fact acquisition cycle.

    Immutable for determinism.
    """

    success: bool
    """Whether acquisition completed successfully."""

    entity_id: str
    """Entity facts were acquired for."""

    acquired_facts: Dict[str, Any] = field(default_factory=dict)
    """Facts successfully acquired from Spark."""

    defaulted_facts: Dict[str, Any] = field(default_factory=dict)
    """Facts that used default values."""

    errors: List[str] = field(default_factory=list)
    """Error messages if any."""

    def __post_init__(self):
        """Ensure fields are properly initialized for frozen dataclass."""
        if not isinstance(self.acquired_facts, dict):
            object.__setattr__(self, 'acquired_facts', dict(self.acquired_facts))
        if not isinstance(self.defaulted_facts, dict):
            object.__setattr__(self, 'defaulted_facts', dict(self.defaulted_facts))
        if not isinstance(self.errors, list):
            object.__setattr__(self, 'errors', list(self.errors))


# ==============================================================================
# FACT ACQUISITION MANAGER
# ==============================================================================

class FactAcquisitionManager:
    """Manages Just-In-Time fact acquisition from Spark to Lens.

    When Box queries data that Lens doesn't have, this manager:
    1. Creates a request for missing facts
    2. Invokes Spark callback to get facts
    3. Validates the response
    4. Stores valid facts in Lens with SPARK provenance
    5. Applies defaults for allowed attributes
    """

    def __init__(self, lens: LensIndex, uuid_generator: Optional[Callable[[], str]] = None):
        """Initialize the acquisition manager.

        Args:
            lens: LensIndex to store acquired facts
            uuid_generator: Optional function to generate UUIDs (for testing)
        """
        self._lens = lens
        self._uuid_generator = uuid_generator or (lambda: str(uuid.uuid4()))

    # ==========================================================================
    # REQUEST GENERATION
    # ==========================================================================

    def create_request(
        self,
        entity_id: str,
        entity_class: str,
        missing_attrs: List[str],
        context: Optional[str] = None,
        timeout_ms: int = 5000,
    ) -> FactRequest:
        """Create a fact request for missing attributes.

        Args:
            entity_id: Entity to query
            entity_class: Entity type ('creature', 'object', 'terrain')
            missing_attrs: Attributes that need to be acquired
            context: Optional context hint
            timeout_ms: Timeout in milliseconds

        Returns:
            FactRequest ready to send to Spark
        """
        request_id = self._uuid_generator()

        return FactRequest(
            request_id=request_id,
            entity_id=entity_id,
            required_attributes=list(missing_attrs),
            context=context,
            timeout_ms=timeout_ms,
        )

    # ==========================================================================
    # RESPONSE VALIDATION
    # ==========================================================================

    def validate_response(
        self,
        request: FactRequest,
        response: FactResponse,
    ) -> ValidationResult:
        """Validate a fact response against the original request.

        Validation rules:
        1. Response request_id must match request
        2. All FORBIDDEN_DEFAULT attributes in request must be present
        3. Values must pass type validation
        4. Unknown attributes are accepted but logged

        Args:
            request: Original request
            response: Response from Spark

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        # Rule 1: Request ID must match
        if response.request_id != request.request_id:
            errors.append(
                f"Request ID mismatch: expected {request.request_id}, "
                f"got {response.request_id}"
            )

        # Rule 2: All FORBIDDEN_DEFAULT attributes must be present
        for attr in request.required_attributes:
            if attr in FORBIDDEN_DEFAULTS:
                if attr not in response.facts:
                    errors.append(
                        f"Missing required attribute '{attr}' "
                        "(no default allowed)"
                    )

        # Rule 3: Type validation for provided facts
        for attr, value in response.facts.items():
            type_error = self._validate_type(attr, value)
            if type_error:
                errors.append(type_error)

        # Rule 4: Log unknown attributes
        known_attrs = set(CREATURE_REQUIRED + OBJECT_REQUIRED + TERRAIN_REQUIRED)
        for attr in response.facts.keys():
            if attr not in known_attrs:
                warnings.append(f"Unknown attribute '{attr}' accepted")
                logger.info("Unknown attribute '%s' in response", attr)

        valid = len(errors) == 0
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)

    def _validate_type(self, attr: str, value: Any) -> Optional[str]:
        """Validate the type of a fact value.

        Args:
            attr: Attribute name
            value: Value to validate

        Returns:
            Error message if invalid, None if valid
        """
        if attr == "size":
            if not isinstance(value, str):
                return f"'size' must be a string, got {type(value).__name__}"
            if value.lower() not in VALID_SIZE_CATEGORIES:
                return f"'size' must be a valid size category, got '{value}'"

        elif attr == "position":
            if not isinstance(value, dict):
                return f"'position' must be a dict, got {type(value).__name__}"
            if "x" not in value or "y" not in value:
                return "'position' must have 'x' and 'y' keys"
            if not isinstance(value.get("x"), int) or not isinstance(value.get("y"), int):
                return "'position' x and y must be integers"

        elif attr == "hit_points":
            if not isinstance(value, int):
                return f"'hit_points' must be an integer, got {type(value).__name__}"
            if value <= 0:
                return f"'hit_points' must be positive, got {value}"

        elif attr == "armor_class":
            if not isinstance(value, int):
                return f"'armor_class' must be an integer, got {type(value).__name__}"

        elif attr == "hardness":
            if not isinstance(value, int):
                return f"'hardness' must be an integer, got {type(value).__name__}"
            if value < 0:
                return f"'hardness' must be non-negative, got {value}"

        elif attr == "elevation":
            if not isinstance(value, int):
                return f"'elevation' must be an integer, got {type(value).__name__}"

        elif attr == "movement_cost":
            if not isinstance(value, int):
                return f"'movement_cost' must be an integer, got {type(value).__name__}"
            if value < 1:
                return f"'movement_cost' must be at least 1, got {value}"

        elif attr == "material":
            if not isinstance(value, str):
                return f"'material' must be a string, got {type(value).__name__}"

        return None

    # ==========================================================================
    # APPLY RESPONSE TO LENS
    # ==========================================================================

    def apply_response(self, response: FactResponse, turn: int) -> bool:
        """Apply validated facts from a response to the Lens.

        Args:
            response: Validated response from Spark
            turn: Current turn number

        Returns:
            True if facts were applied, False otherwise
        """
        if not response.valid:
            return False

        entity = self._lens.get_entity(response.entity_id)
        if entity is None:
            logger.warning(
                "Cannot apply facts: entity '%s' not in Lens",
                response.entity_id
            )
            return False

        for attr, value in response.facts.items():
            # Store with SPARK tier (provenance from LLM)
            self._lens.set_fact(
                entity_id=response.entity_id,
                attribute=attr,
                value=value,
                source_tier=SourceTier.SPARK,
                turn=turn,
                provenance_id=response.request_id,
            )

        return True

    # ==========================================================================
    # DEFAULT APPLICATION
    # ==========================================================================

    def apply_defaults(
        self,
        entity_id: str,
        entity_class: str,
        turn: int = 0,
    ) -> Dict[str, Any]:
        """Apply default values for allowed attributes.

        Only applies defaults for attributes in ALLOWED_DEFAULTS.
        FORBIDDEN_DEFAULTS are never defaulted.

        Args:
            entity_id: Entity to apply defaults to
            entity_class: Entity type for required attribute lookup
            turn: Current turn number

        Returns:
            Dict of attribute → value for defaults that were applied
        """
        applied = {}

        # Get required attributes for this entity class
        if entity_class == "creature":
            required = CREATURE_REQUIRED
        elif entity_class == "object":
            required = OBJECT_REQUIRED
        elif entity_class == "terrain":
            required = TERRAIN_REQUIRED
        else:
            logger.warning("Unknown entity class: %s", entity_class)
            return applied

        # Check each required attribute
        for attr in required:
            # Skip if already has a fact
            existing = self._lens.get_fact(entity_id, attr)
            if existing is not None:
                continue

            # Only apply allowed defaults
            if attr in ALLOWED_DEFAULTS:
                default_value = ALLOWED_DEFAULTS[attr]
                self._lens.set_fact(
                    entity_id=entity_id,
                    attribute=attr,
                    value=default_value,
                    source_tier=SourceTier.DEFAULT,
                    turn=turn,
                )
                applied[attr] = default_value

        return applied

    # ==========================================================================
    # FULL ACQUISITION CYCLE
    # ==========================================================================

    def acquire_facts(
        self,
        entity_id: str,
        entity_class: str,
        required_attrs: List[str],
        spark_callback: Callable[[FactRequest], Optional[FactResponse]],
        turn: int = 0,
    ) -> AcquisitionResult:
        """Execute a full fact acquisition cycle.

        1. Create request for required attributes
        2. Call Spark via callback
        3. Validate response
        4. Apply valid facts to Lens
        5. Apply defaults for missing allowed attributes
        6. Return result

        Args:
            entity_id: Entity to acquire facts for
            entity_class: Entity type
            required_attrs: Attributes to acquire
            spark_callback: Function to call Spark (takes FactRequest, returns FactResponse)
            turn: Current turn number

        Returns:
            AcquisitionResult with acquired facts, defaults, and any errors
        """
        errors = []
        acquired_facts = {}
        defaulted_facts = {}

        # Validate entity class
        if entity_class not in VALID_ENTITY_CLASSES:
            return AcquisitionResult(
                success=False,
                entity_id=entity_id,
                errors=[f"Unknown entity class: {entity_class}"],
            )

        # Handle empty required_attrs
        if not required_attrs:
            return AcquisitionResult(
                success=True,
                entity_id=entity_id,
            )

        # Create request
        request = self.create_request(entity_id, entity_class, required_attrs)

        # Call Spark
        try:
            response = spark_callback(request)
        except Exception as e:
            logger.error(
                "Spark callback failed for request %s: %s",
                request.request_id, str(e)
            )
            response = None

        # Handle timeout/failure
        if response is None:
            errors.append("Spark callback returned None (timeout or failure)")
            logger.warning(
                "Spark timeout for entity %s, request %s",
                entity_id, request.request_id
            )
            # Apply defaults for allowed attrs
            defaulted_facts = self.apply_defaults(entity_id, entity_class, turn)
            return AcquisitionResult(
                success=False,
                entity_id=entity_id,
                defaulted_facts=defaulted_facts,
                errors=errors,
            )

        # Validate response
        validation = self.validate_response(request, response)
        if not validation.valid:
            errors.extend(validation.errors)
            # Apply defaults for allowed attrs
            defaulted_facts = self.apply_defaults(entity_id, entity_class, turn)
            return AcquisitionResult(
                success=False,
                entity_id=entity_id,
                defaulted_facts=defaulted_facts,
                errors=errors,
            )

        # Apply valid response
        # Create a new response with valid=True for applying
        valid_response = FactResponse(
            request_id=response.request_id,
            entity_id=response.entity_id,
            facts=response.facts,
            source=response.source,
            valid=True,
            error=None,
        )
        self.apply_response(valid_response, turn)
        acquired_facts = dict(response.facts)

        # Apply defaults for any still-missing allowed attrs
        defaulted_facts = self.apply_defaults(entity_id, entity_class, turn)

        return AcquisitionResult(
            success=True,
            entity_id=entity_id,
            acquired_facts=acquired_facts,
            defaulted_facts=defaulted_facts,
            errors=errors,
        )

    # ==========================================================================
    # QUERY WITH ACQUISITION
    # ==========================================================================

    def get_or_acquire(
        self,
        entity_id: str,
        attribute: str,
        entity_class: str,
        spark_callback: Callable[[FactRequest], Optional[FactResponse]],
        turn: int = 0,
    ) -> Optional[Any]:
        """Get a fact, acquiring it from Spark if missing.

        Convenience method that:
        1. Checks if fact exists in Lens
        2. If missing, triggers acquisition
        3. Returns the fact value or None if acquisition failed

        Args:
            entity_id: Entity to query
            attribute: Attribute to get
            entity_class: Entity type
            spark_callback: Spark callback for acquisition
            turn: Current turn number

        Returns:
            Fact value if found or acquired, None otherwise
        """
        # Check if fact already exists
        existing = self._lens.get_fact(entity_id, attribute)
        if existing is not None:
            return existing.value

        # Try to acquire
        result = self.acquire_facts(
            entity_id=entity_id,
            entity_class=entity_class,
            required_attrs=[attribute],
            spark_callback=spark_callback,
            turn=turn,
        )

        if result.success:
            if attribute in result.acquired_facts:
                return result.acquired_facts[attribute]
            if attribute in result.defaulted_facts:
                return result.defaulted_facts[attribute]

        # Check Lens again (might have been stored)
        fact = self._lens.get_fact(entity_id, attribute)
        if fact is not None:
            return fact.value

        return None

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    def get_required_attributes(self, entity_class: str) -> List[str]:
        """Get required attributes for an entity class.

        Args:
            entity_class: Entity type

        Returns:
            List of required attribute names
        """
        if entity_class == "creature":
            return list(CREATURE_REQUIRED)
        elif entity_class == "object":
            return list(OBJECT_REQUIRED)
        elif entity_class == "terrain":
            return list(TERRAIN_REQUIRED)
        return []

    def get_missing_attributes(
        self,
        entity_id: str,
        entity_class: str,
    ) -> List[str]:
        """Get attributes that are missing for an entity.

        Args:
            entity_id: Entity to check
            entity_class: Entity type

        Returns:
            List of missing required attribute names
        """
        required = self.get_required_attributes(entity_class)
        missing = []

        for attr in required:
            fact = self._lens.get_fact(entity_id, attr)
            if fact is None:
                missing.append(attr)

        return missing
