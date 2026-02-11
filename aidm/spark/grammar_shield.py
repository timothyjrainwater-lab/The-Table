"""Grammar Shield: Output validation layer for Spark/LLM responses

Enforces three constraints on Spark output:
1. JSON mode outputs must parse as valid JSON
2. Structured outputs must match provided schemas
3. Narrative outputs must not contain mechanical assertions

When validation fails, Grammar Shield retries with a stricter prompt
(max 2 retries), then raises. This is the enforcement arm of the
Spark/Lens/Box doctrine's "Spark has zero mechanical authority" axiom.

BOUNDARY LAW (BL-001, BL-002): This module must NEVER import from aidm.core
or aidm.narration. Grammar Shield lives entirely in the spark layer.

Reference: docs/design/SPARK_ADAPTER_ARCHITECTURE.md
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

from aidm.spark.spark_adapter import SparkRequest, SparkResponse, FinishReason

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class GrammarValidationError(Exception):
    """Base for all Grammar Shield validation failures."""
    pass


class MechanicalAssertionError(GrammarValidationError):
    """Spark output contains unauthorized mechanical claims.

    Attributes:
        matched_patterns: Pattern names that matched (e.g. 'damage_quantity')
        matched_text: Actual text fragments that matched
        full_text: The complete output text
    """

    def __init__(
        self,
        matched_patterns: List[str],
        matched_text: List[str],
        full_text: str,
    ):
        self.matched_patterns = matched_patterns
        self.matched_text = matched_text
        self.full_text = full_text
        super().__init__(
            f"Mechanical assertion detected: {matched_patterns} "
            f"in text fragments: {matched_text}"
        )


class JsonParseError(GrammarValidationError):
    """json_mode output failed to parse as valid JSON."""
    pass


class SchemaValidationError(GrammarValidationError):
    """Structured output failed schema validation."""
    pass


# ============================================================================
# Mechanical Assertion Patterns (compiled once at module level)
# ============================================================================

MECHANICAL_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r'\b\d+\s*(points?\s+of\s+)?damage\b', re.IGNORECASE), 'damage_quantity'),
    (re.compile(r'\bAC\s*\d+\b', re.IGNORECASE), 'armor_class'),
    (re.compile(r'\b\d+\s*h(it\s*)?p(oints?)?\b', re.IGNORECASE), 'hit_points'),
    (re.compile(r'\b(PHB|DMG|MM)\s*\d+', re.IGNORECASE), 'rule_citation'),
    (re.compile(r'[+-]\d+\s*(to\s+)?(attack|hit)\b', re.IGNORECASE), 'attack_bonus'),
    (re.compile(r'\bDC\s*\d+\b', re.IGNORECASE), 'difficulty_class'),
    (re.compile(r'\broll(ed)?\s+(a\s+)?\d+\b', re.IGNORECASE), 'die_roll_result'),
    (re.compile(r'\b\d+d\d+', re.IGNORECASE), 'dice_notation'),
]


# ============================================================================
# Configuration
# ============================================================================


@dataclass
class GrammarShieldConfig:
    """Configuration for Grammar Shield validation.

    Attributes:
        max_retries: Per-request retry budget (default 2)
        mechanical_assertion_patterns: Compiled regex patterns for assertion detection
        enable_json_validation: Validate json_mode outputs
        enable_schema_validation: Validate against provided schema
        enable_assertion_detection: Detect mechanical assertions in narrative
    """

    max_retries: int = 2
    mechanical_assertion_patterns: List[Tuple[re.Pattern, str]] = field(
        default_factory=lambda: list(MECHANICAL_PATTERNS)
    )
    enable_json_validation: bool = True
    enable_schema_validation: bool = True
    enable_assertion_detection: bool = True


# ============================================================================
# Validation Result
# ============================================================================


@dataclass
class ValidationResult:
    """Result of Grammar Shield validation.

    Attributes:
        valid: Whether the output passed all checks
        errors: List of validation errors (empty if valid)
        retries_used: How many retries were attempted
        original_text: Original (pre-retry) text if retried, None otherwise
        final_text: Validated text (may be from a retry attempt)
    """

    valid: bool
    errors: List[GrammarValidationError]
    retries_used: int
    original_text: Optional[str]
    final_text: str


# ============================================================================
# Grammar Shield
# ============================================================================


class GrammarShield:
    """Output validation layer for Spark/LLM responses.

    Wraps LlamaCppAdapter.generate() to enforce:
    1. JSON mode: output must parse as valid JSON
    2. Schema: output must match provided Pydantic/JSON schema
    3. Mechanical assertion: narrative must not claim BOX authority

    Retry budget is per-request. Each call to validate_and_retry()
    starts with a fresh retry count. No global state.
    """

    def __init__(self, config: Optional[GrammarShieldConfig] = None):
        """Initialize Grammar Shield.

        Args:
            config: Optional configuration. Uses defaults if None.
        """
        self.config = config or GrammarShieldConfig()

    def validate_and_retry(
        self,
        request: SparkRequest,
        response: SparkResponse,
        generate_fn: Callable[[SparkRequest], SparkResponse],
        schema: Optional[Any] = None,
    ) -> ValidationResult:
        """Validate response, retry on failure, raise on exhaustion.

        Args:
            request: Original SparkRequest
            response: SparkResponse from generate()
            generate_fn: Callable to regenerate (for retries)
            schema: Optional schema to validate against (Pydantic model class
                    or a callable that accepts a dict and raises on mismatch)

        Returns:
            ValidationResult with validated text

        Raises:
            MechanicalAssertionError: If assertion detected after all retries exhausted
            JsonParseError: If JSON invalid after all retries exhausted
            SchemaValidationError: If schema mismatch after all retries exhausted
        """
        original_text = response.text
        current_text = response.text
        retries_used = 0
        all_errors: List[GrammarValidationError] = []

        # First validation pass
        errors = self.validate_only(
            text=current_text,
            json_mode=request.json_mode,
            schema=schema,
        )

        if not errors:
            return ValidationResult(
                valid=True,
                errors=[],
                retries_used=0,
                original_text=None,
                final_text=current_text,
            )

        all_errors = list(errors)
        logger.warning(
            f"Grammar Shield: initial validation failed with {len(errors)} error(s): "
            f"{[type(e).__name__ for e in errors]}"
        )

        # Retry loop
        for attempt in range(self.config.max_retries):
            retries_used = attempt + 1
            retry_request = self._build_retry_prompt(request, errors)

            logger.info(f"Grammar Shield: retry {retries_used}/{self.config.max_retries}")
            retry_response = generate_fn(retry_request)

            # Skip validation if generation itself failed
            if retry_response.finish_reason == FinishReason.ERROR:
                logger.warning(f"Grammar Shield: retry {retries_used} generation failed")
                continue

            current_text = retry_response.text
            errors = self.validate_only(
                text=current_text,
                json_mode=request.json_mode,
                schema=schema,
            )

            if not errors:
                logger.info(f"Grammar Shield: retry {retries_used} succeeded")
                return ValidationResult(
                    valid=True,
                    errors=all_errors,
                    retries_used=retries_used,
                    original_text=original_text,
                    final_text=current_text,
                )

            all_errors.extend(errors)
            logger.warning(
                f"Grammar Shield: retry {retries_used} still has {len(errors)} error(s)"
            )

        # All retries exhausted — raise the most specific error
        logger.error(
            f"Grammar Shield: all {self.config.max_retries} retries exhausted"
        )
        self._raise_final_error(all_errors, current_text)

        # Unreachable, but makes type checkers happy
        raise GrammarValidationError("Validation failed after all retries")  # pragma: no cover

    def validate_only(
        self,
        text: str,
        json_mode: bool = False,
        schema: Optional[Any] = None,
    ) -> List[GrammarValidationError]:
        """Validate text without retry. Returns list of errors (empty = valid).

        Args:
            text: Text to validate
            json_mode: Whether JSON parsing should be checked
            schema: Optional schema to validate against

        Returns:
            List of validation errors. Empty list means valid.
        """
        errors: List[GrammarValidationError] = []

        # 1. JSON validation
        if json_mode and self.config.enable_json_validation:
            json_error = self._check_json(text)
            if json_error is not None:
                errors.append(json_error)

        # 2. Schema validation (only if JSON parsed successfully or not in json_mode)
        if schema is not None and self.config.enable_schema_validation:
            schema_error = self._check_schema(text, schema)
            if schema_error is not None:
                errors.append(schema_error)

        # 3. Mechanical assertion detection
        if self.config.enable_assertion_detection:
            assertion_error = self._check_mechanical_assertions(text)
            if assertion_error is not None:
                errors.append(assertion_error)

        return errors

    def _check_json(self, text: str) -> Optional[JsonParseError]:
        """Validate JSON parsing. Returns None if valid.

        Args:
            text: Text to parse as JSON

        Returns:
            JsonParseError if invalid, None if valid
        """
        try:
            json.loads(text)
            return None
        except (json.JSONDecodeError, ValueError) as e:
            return JsonParseError(f"Invalid JSON: {e}")

    def _check_schema(self, text: str, schema: Any) -> Optional[SchemaValidationError]:
        """Validate against schema. Returns None if valid.

        Supports:
        - Callable validators: schema(parsed_data) should raise on mismatch
        - Pydantic model classes: schema.model_validate(parsed_data)
        - Dict-based JSON schemas: checked via key presence

        Args:
            text: Text to validate (should be valid JSON)
            schema: Schema to validate against

        Returns:
            SchemaValidationError if invalid, None if valid
        """
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return SchemaValidationError("Cannot validate schema: text is not valid JSON")

        try:
            # Pydantic model class (has model_validate)
            if hasattr(schema, 'model_validate'):
                schema.model_validate(parsed)
                return None

            # Callable validator
            if callable(schema):
                schema(parsed)
                return None

            # Dict-based schema: check required keys
            if isinstance(schema, dict) and 'required' in schema:
                required_keys = schema['required']
                if isinstance(parsed, dict):
                    missing = [k for k in required_keys if k not in parsed]
                    if missing:
                        return SchemaValidationError(
                            f"Missing required keys: {missing}"
                        )
                return None

        except Exception as e:
            return SchemaValidationError(f"Schema validation failed: {e}")

        return None

    def _check_mechanical_assertions(self, text: str) -> Optional[MechanicalAssertionError]:
        """Scan for unauthorized mechanical claims. Returns None if clean.

        Args:
            text: Text to scan

        Returns:
            MechanicalAssertionError if assertions found, None if clean
        """
        matched_patterns: List[str] = []
        matched_text: List[str] = []

        for pattern, name in self.config.mechanical_assertion_patterns:
            match = pattern.search(text)
            if match:
                matched_patterns.append(name)
                matched_text.append(match.group(0))

        if matched_patterns:
            return MechanicalAssertionError(
                matched_patterns=matched_patterns,
                matched_text=matched_text,
                full_text=text,
            )

        return None

    def _build_retry_prompt(
        self,
        original_request: SparkRequest,
        errors: List[GrammarValidationError],
    ) -> SparkRequest:
        """Build stricter retry prompt based on failure type.

        Args:
            original_request: The original request that failed
            errors: Validation errors from the failed attempt

        Returns:
            New SparkRequest with appended constraints and bumped temperature
        """
        constraints: List[str] = []

        for error in errors:
            if isinstance(error, MechanicalAssertionError):
                constraints.append(
                    "IMPORTANT: Your previous response contained invalid content. "
                    "Do NOT include specific numbers, damage values, AC values, "
                    "dice results, or rule citations. Describe the scene using "
                    "only narrative language."
                )
            elif isinstance(error, JsonParseError):
                constraints.append(
                    "IMPORTANT: Your response MUST be valid JSON. "
                    "Ensure proper quoting, braces, and no trailing commas."
                )
            elif isinstance(error, SchemaValidationError):
                constraints.append(
                    f"IMPORTANT: Your response must match the required schema. "
                    f"Error: {error}"
                )

        # Deduplicate constraints
        seen = set()
        unique_constraints = []
        for c in constraints:
            key = type(c).__name__ + c[:50]
            if key not in seen:
                seen.add(key)
                unique_constraints.append(c)

        # Build new prompt with appended constraints
        new_prompt = original_request.prompt
        if unique_constraints:
            new_prompt = new_prompt + "\n\n" + "\n".join(unique_constraints)

        # Increase temperature by 0.1 on retry (cap at 2.0)
        new_temperature = min(original_request.temperature + 0.1, 2.0)

        return SparkRequest(
            prompt=new_prompt,
            temperature=new_temperature,
            max_tokens=original_request.max_tokens,
            stop_sequences=original_request.stop_sequences,
            context_window=original_request.context_window,
            streaming=original_request.streaming,
            json_mode=original_request.json_mode,
            seed=original_request.seed,
            metadata=original_request.metadata,
        )

    def _raise_final_error(
        self,
        errors: List[GrammarValidationError],
        final_text: str,
    ) -> None:
        """Raise the most specific error after all retries exhausted.

        Priority: MechanicalAssertionError > JsonParseError > SchemaValidationError

        Args:
            errors: All accumulated errors
            final_text: The last text that failed validation
        """
        # Find most critical error type
        for error in errors:
            if isinstance(error, MechanicalAssertionError):
                raise error

        for error in errors:
            if isinstance(error, JsonParseError):
                raise error

        for error in errors:
            if isinstance(error, SchemaValidationError):
                raise error

        # Fallback (shouldn't happen)
        if errors:
            raise errors[0]
