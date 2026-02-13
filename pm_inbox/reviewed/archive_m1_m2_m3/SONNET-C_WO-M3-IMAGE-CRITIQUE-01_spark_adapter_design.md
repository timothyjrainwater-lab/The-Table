# SparkCritiqueAdapter Design Specification

**Agent:** Sonnet-C
**Work Order:** WO-M3-IMAGE-CRITIQUE-01
**Date:** 2026-02-11
**Status:** Design Specification

---

## 1. Overview

The **SparkCritiqueAdapter** is a concrete implementation of the `ImageCritiqueAdapter` protocol that uses Spark's vision-language models (Claude 3.5 Sonnet/Haiku) to perform sophisticated image quality validation during prep time.

**Design Goals**:
- Match existing adapter pattern (STTAdapter, TTSAdapter, ImageAdapter)
- Provide high-quality multi-dimensional critique
- Support fallback models for reliability
- Maintain determinism for same inputs
- Minimize API costs while ensuring quality

---

## 2. Architecture

### 2.1 Class Structure

```python
class SparkCritiqueAdapter:
    """Spark-based image critique adapter.

    Uses Claude vision models to perform multi-dimensional image quality validation.
    Supports fallback models for reliability and cost optimization.

    Attributes:
        primary_model: Model name for primary critique (e.g., "claude-3-5-sonnet")
        fallback_models: List of fallback model names
        api_key: Anthropic API key (loaded from env)
        temperature: Sampling temperature (0.0 for deterministic)
        seed: RNG seed for reproducibility
        timeout_seconds: Max wait time for API response
        max_retries: Max retry attempts on transient errors
    """

    def __init__(
        self,
        primary_model: str = "claude-3-5-sonnet-20241022",
        fallback_models: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        seed: int = 42,
        timeout_seconds: int = 30,
        max_retries: int = 3
    ):
        """Initialize Spark critique adapter.

        Args:
            primary_model: Primary model name (defaults to Claude 3.5 Sonnet)
            fallback_models: Fallback models (defaults to ["claude-3-haiku"])
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            temperature: Sampling temperature (0.0 = deterministic)
            seed: RNG seed for reproducibility
            timeout_seconds: Max wait time for API response
            max_retries: Max retry attempts on transient errors
        """
        self.primary_model = primary_model
        self.fallback_models = fallback_models or ["claude-3-haiku-20240307"]
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.temperature = temperature
        self.seed = seed
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        if not self.api_key:
            raise ValueError("Anthropic API key required (set ANTHROPIC_API_KEY env var)")

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        """Critique image using Spark vision model.

        Implements ImageCritiqueAdapter protocol.

        Args:
            image_bytes: Generated image (PNG/JPEG bytes)
            rubric: Quality thresholds for pass/fail
            anchor_image_bytes: NPC anchor image for identity match (optional)
            style_reference_bytes: Campaign style reference for style adherence (optional)

        Returns:
            CritiqueResult with pass/fail + dimension scores

        Raises:
            ValueError: If image_bytes is invalid
        """
        # Validate image format
        if not self._is_valid_image_format(image_bytes):
            return self._create_error_result("Invalid image format (must be PNG or JPEG)")

        # Build critique prompt
        prompt = self._build_critique_prompt(rubric, anchor_image_bytes, style_reference_bytes)

        # Try primary model first, then fallbacks
        models_to_try = [self.primary_model] + self.fallback_models

        for model_name in models_to_try:
            try:
                result = self._attempt_critique(
                    image_bytes=image_bytes,
                    prompt=prompt,
                    model_name=model_name
                )
                return result
            except (anthropic.APIError, anthropic.RateLimitError, TimeoutError) as e:
                # Try next model in fallback chain
                continue

        # All models failed
        return self._create_error_result("All critique models unavailable")
```

### 2.2 Core Methods

#### 2.2.1 `_build_critique_prompt()`

```python
def _build_critique_prompt(
    self,
    rubric: CritiqueRubric,
    anchor_image_bytes: Optional[bytes],
    style_reference_bytes: Optional[bytes]
) -> str:
    """Build critique prompt from rubric and optional references.

    Args:
        rubric: Quality thresholds
        anchor_image_bytes: NPC anchor for identity matching
        style_reference_bytes: Campaign style reference

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "You are an expert image quality validator for a D&D campaign.",
        "Analyze the provided image and evaluate it across five quality dimensions.",
        "",
        "Return a JSON object with this exact structure:",
        json.dumps(self._get_example_json(), indent=2),
        "",
        "Quality Dimensions:",
        self._format_dimension_guidelines(rubric),
        "",
        "Scoring Guidelines:",
        "- 0.90-1.00: Excellent quality",
        "- 0.70-0.89: Good quality (ACCEPTABLE threshold)",
        "- 0.50-0.69: Fair quality (MINOR issues)",
        "- 0.30-0.49: Poor quality (MAJOR issues)",
        "- 0.00-0.29: Critical quality (CRITICAL issues, auto-reject)",
    ]

    # Add anchor/style reference instructions if provided
    if anchor_image_bytes:
        prompt_parts.append("\nIMAGE 2: NPC Anchor for identity matching (evaluate identity_match dimension against this)")
    if style_reference_bytes:
        prompt_parts.append("\nIMAGE 3: Campaign style reference (evaluate style_adherence dimension against this)")

    prompt_parts.append("\nOverall Pass/Fail:")
    prompt_parts.append("- PASS if all dimensions >= threshold AND no CRITICAL severity")
    prompt_parts.append("- FAIL otherwise")

    return "\n".join(prompt_parts)
```

#### 2.2.2 `_attempt_critique()`

```python
def _attempt_critique(
    self,
    image_bytes: bytes,
    prompt: str,
    model_name: str
) -> CritiqueResult:
    """Attempt critique with specific model.

    Args:
        image_bytes: Image to critique
        prompt: Critique prompt
        model_name: Model to use

    Returns:
        CritiqueResult if successful

    Raises:
        anthropic.APIError: If API call fails
        anthropic.RateLimitError: If rate limit hit
        TimeoutError: If request times out
        ValueError: If JSON response is malformed
    """
    # Encode image to base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # Determine media type from magic bytes
    media_type = "image/png" if image_bytes[:8] == b'\x89PNG\r\n\x1a\n' else "image/jpeg"

    # Call Anthropic Messages API with vision
    try:
        message = self.client.messages.create(
            model=model_name,
            max_tokens=500,
            temperature=self.temperature,
            system="You are an expert image quality validator for a D&D campaign.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
            timeout=self.timeout_seconds,
        )

        # Extract JSON from response
        response_text = message.content[0].text

        # Parse JSON response
        return self._parse_response_json(response_text, model_name)

    except anthropic.APITimeoutError:
        raise TimeoutError(f"Critique request timed out after {self.timeout_seconds}s")
```

#### 2.2.3 `_parse_response_json()`

```python
def _parse_response_json(self, response_text: str, model_name: str) -> CritiqueResult:
    """Parse JSON response into CritiqueResult.

    Args:
        response_text: Raw text response from model
        model_name: Model that generated response

    Returns:
        CritiqueResult matching existing schema

    Raises:
        ValueError: If JSON doesn't match expected schema
    """
    # Extract JSON from response (may be wrapped in markdown code blocks)
    json_str = self._extract_json_from_text(response_text)

    # Parse JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")

    # Validate required fields
    required_fields = ["passed", "overall_severity", "overall_score", "dimensions"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Parse dimensions
    dimensions = []
    for dim_data in data["dimensions"]:
        dimension = CritiqueDimension(
            dimension=DimensionType(dim_data["dimension"]),
            severity=SeverityLevel(dim_data["severity"]),
            score=dim_data["score"],
            reason=dim_data["reason"],
            measurement_method=f"llm_vision:{model_name}"
        )
        dimensions.append(dimension)

    # Sort dimensions by dimension type (required by CritiqueResult)
    dimensions.sort(key=lambda d: d.dimension.value)

    # Build CritiqueResult
    return CritiqueResult(
        passed=data["passed"],
        overall_severity=SeverityLevel(data["overall_severity"]),
        dimensions=dimensions,
        overall_score=data["overall_score"],
        rejection_reason=data.get("rejection_reason"),
        critique_method=f"spark_vision:{model_name}"
    )
```

---

## 3. Prompt Engineering

### 3.1 Dimension Guidelines Template

```python
def _format_dimension_guidelines(self, rubric: CritiqueRubric) -> str:
    """Format dimension guidelines with thresholds from rubric."""
    return f"""
1. **Artifacting** (threshold: {rubric.artifacting_threshold:.2f}): Check for AI artifacts
   - CRITICAL: Major anatomical errors (6 fingers, fused limbs, wrong species)
   - MAJOR: Noticeable artifacts (distorted faces, unnatural proportions)
   - MINOR: Subtle artifacts (texture inconsistencies, minor details)
   - ACCEPTABLE: No obvious artifacts

2. **Composition** (threshold: {rubric.composition_threshold:.2f}): Is subject properly framed?
   - CRITICAL: Subject cut off or completely off-center
   - MAJOR: Poor framing (too much empty space, awkward cropping)
   - MINOR: Slightly off-center or suboptimal framing
   - ACCEPTABLE: Well-composed and properly framed

3. **Identity Match** (threshold: {rubric.identity_threshold:.2f}): Matches description?
   - CRITICAL: Wrong species/gender/major features
   - MAJOR: Missing key descriptors (wrong hair color, age, attire)
   - MINOR: Minor details differ (accessories, minor features)
   - ACCEPTABLE: Matches description accurately

4. **Readability** (threshold: {rubric.readability_threshold:.2f}): Details clear at UI size?
   - CRITICAL: Blurry, pixelated, or completely illegible
   - MAJOR: Hard to make out features, low detail
   - MINOR: Slightly soft or lacks fine detail
   - ACCEPTABLE: Sharp, clear, readable at UI size

5. **Style Adherence** (threshold: {rubric.style_threshold:.2f}): Matches campaign style?
   - CRITICAL: Completely wrong style (photo-realistic vs fantasy art)
   - MAJOR: Noticeable style mismatch (wrong color palette, tone)
   - MINOR: Subtle style inconsistency
   - ACCEPTABLE: Matches campaign style
"""
```

### 3.2 JSON Extraction

```python
def _extract_json_from_text(self, text: str) -> str:
    """Extract JSON from text (may be wrapped in markdown code blocks).

    Args:
        text: Raw text response

    Returns:
        Extracted JSON string

    Examples:
        Input: "```json\\n{...}\\n```" → Output: "{...}"
        Input: "{...}" → Output: "{...}"
    """
    # Check if wrapped in markdown code block
    if text.strip().startswith("```json"):
        # Extract content between ```json and ```
        start = text.find("```json") + 7
        end = text.find("```", start)
        return text[start:end].strip()
    elif text.strip().startswith("```"):
        # Extract content between ``` and ```
        start = text.find("```") + 3
        end = text.find("```", start)
        return text[start:end].strip()
    else:
        # Assume raw JSON
        return text.strip()
```

---

## 4. Error Handling

### 4.1 Error Result Factory

```python
def _create_error_result(self, error_message: str) -> CritiqueResult:
    """Create error CritiqueResult.

    Args:
        error_message: Error description

    Returns:
        CritiqueResult with passed=False and error information
    """
    return CritiqueResult(
        passed=False,
        overall_severity=SeverityLevel.CRITICAL,
        dimensions=[],  # Empty dimensions on error
        overall_score=0.0,
        rejection_reason=error_message,
        critique_method="error"
    )
```

### 4.2 Retry Logic

```python
def _attempt_critique_with_retry(
    self,
    image_bytes: bytes,
    prompt: str,
    model_name: str
) -> CritiqueResult:
    """Attempt critique with exponential backoff retry.

    Args:
        image_bytes: Image to critique
        prompt: Critique prompt
        model_name: Model to use

    Returns:
        CritiqueResult if any attempt succeeds
        Error CritiqueResult if all attempts fail
    """
    for attempt in range(self.max_retries):
        try:
            return self._attempt_critique(image_bytes, prompt, model_name)
        except anthropic.RateLimitError as e:
            if attempt < self.max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                continue
            else:
                # Final attempt failed
                raise
        except anthropic.APIError as e:
            # Non-retryable error
            raise

    # Shouldn't reach here, but handle gracefully
    return self._create_error_result("All retry attempts failed")
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

```python
def test_spark_critique_adapter_valid_image_passes():
    """SparkCritiqueAdapter passes valid image."""
    adapter = SparkCritiqueAdapter(
        primary_model="claude-3-5-sonnet",
        api_key="test_api_key"
    )

    # Mock Anthropic API response
    with mock.patch.object(adapter.client.messages, 'create') as mock_create:
        mock_create.return_value = MockAnthropicMessage(
            content=[MockTextBlock(text=MOCK_CRITIQUE_JSON_PASS)]
        )

        result = adapter.critique(
            image_bytes=VALID_PNG_BYTES,
            rubric=DEFAULT_CRITIQUE_RUBRIC
        )

        assert result.passed is True
        assert result.overall_severity == SeverityLevel.ACCEPTABLE
        assert len(result.dimensions) == 5


def test_spark_critique_adapter_invalid_image_fails():
    """SparkCritiqueAdapter rejects invalid image format."""
    adapter = SparkCritiqueAdapter(primary_model="claude-3-5-sonnet")

    result = adapter.critique(
        image_bytes=b"not a valid image",
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )

    assert result.passed is False
    assert "Invalid image format" in result.rejection_reason
```

### 5.2 Integration Tests (Mock API)

```python
def test_spark_critique_adapter_fallback_on_primary_failure():
    """SparkCritiqueAdapter falls back to Haiku when Sonnet fails."""
    adapter = SparkCritiqueAdapter(
        primary_model="claude-3-5-sonnet",
        fallback_models=["claude-3-haiku"]
    )

    with mock.patch.object(adapter.client.messages, 'create') as mock_create:
        # First call (Sonnet) raises RateLimitError
        # Second call (Haiku) succeeds
        mock_create.side_effect = [
            anthropic.RateLimitError("Rate limit exceeded"),
            MockAnthropicMessage(content=[MockTextBlock(text=MOCK_CRITIQUE_JSON_PASS)])
        ]

        result = adapter.critique(
            image_bytes=VALID_PNG_BYTES,
            rubric=DEFAULT_CRITIQUE_RUBRIC
        )

        assert result.passed is True
        assert "haiku" in result.critique_method
        assert mock_create.call_count == 2
```

### 5.3 Determinism Tests (PBHA)

```python
def test_spark_critique_adapter_deterministic():
    """SparkCritiqueAdapter returns identical results for same input."""
    adapter = SparkCritiqueAdapter(
        primary_model="claude-3-5-sonnet",
        seed=42,
        temperature=0.0
    )

    results = []
    for _ in range(10):
        result = adapter.critique(
            image_bytes=VALID_PNG_BYTES,
            rubric=DEFAULT_CRITIQUE_RUBRIC
        )
        results.append(result.to_dict())

    # All results should be identical
    assert len(set(json.dumps(r, sort_keys=True) for r in results)) == 1
```

---

## 6. Performance Optimization

### 6.1 Caching Strategy

```python
class CachedSparkCritiqueAdapter(SparkCritiqueAdapter):
    """Spark critique adapter with result caching.

    Caches critique results by image hash to avoid re-processing identical images.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}  # image_hash → CritiqueResult

    def critique(self, image_bytes: bytes, rubric: CritiqueRubric, **kwargs) -> CritiqueResult:
        """Critique with caching."""
        # Compute image hash
        image_hash = hashlib.sha256(image_bytes).hexdigest()

        # Check cache
        if image_hash in self.cache:
            return self.cache[image_hash]

        # Cache miss: run critique
        result = super().critique(image_bytes, rubric, **kwargs)

        # Store in cache
        self.cache[image_hash] = result

        return result
```

### 6.2 Batch Processing

```python
def critique_batch(
    self,
    image_batch: List[bytes],
    rubric: CritiqueRubric
) -> List[CritiqueResult]:
    """Critique multiple images (sequentially for now).

    Future: Use async/await for concurrent API calls.

    Args:
        image_batch: List of image bytes
        rubric: Quality thresholds

    Returns:
        List of CritiqueResults (same order as input)
    """
    results = []
    for image_bytes in image_batch:
        result = self.critique(image_bytes, rubric)
        results.append(result)
    return results
```

---

## 7. Cost Monitoring

### 7.1 Usage Tracking

```python
class SparkCritiqueAdapter:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.usage_stats = {
            "total_critiques": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "model_usage": {}  # model_name → count
        }

    def _attempt_critique(self, image_bytes, prompt, model_name):
        """Attempt critique with usage tracking."""
        result = super()._attempt_critique(image_bytes, prompt, model_name)

        # Update usage stats
        self.usage_stats["total_critiques"] += 1
        self.usage_stats["model_usage"][model_name] = self.usage_stats["model_usage"].get(model_name, 0) + 1

        # Track tokens and cost (from API response metadata)
        # Note: Actual implementation depends on Anthropic API response format

        return result

    def get_usage_report(self) -> Dict[str, Any]:
        """Get usage statistics.

        Returns:
            Dict with usage metrics
        """
        return {
            "total_critiques": self.usage_stats["total_critiques"],
            "total_tokens": self.usage_stats["total_tokens"],
            "total_cost_usd": self.usage_stats["total_cost_usd"],
            "model_usage": self.usage_stats["model_usage"],
            "avg_cost_per_critique": (
                self.usage_stats["total_cost_usd"] / self.usage_stats["total_critiques"]
                if self.usage_stats["total_critiques"] > 0 else 0.0
            )
        }
```

---

## 8. Adapter Registry Integration

### 8.1 Factory Registration

```python
# In aidm/core/image_critique_adapter.py

_IMAGE_CRITIC_REGISTRY["spark"] = SparkCritiqueAdapter

def create_image_critic(backend: str = "stub", **kwargs) -> ImageCritiqueAdapter:
    """Factory function for image critique adapters.

    Examples:
        # Stub (default)
        critic = create_image_critic("stub")

        # Spark with defaults
        critic = create_image_critic("spark")

        # Spark with custom config
        critic = create_image_critic(
            "spark",
            primary_model="claude-3-5-sonnet",
            fallback_models=["claude-3-haiku"],
            temperature=0.0,
            seed=42
        )
    """
    if backend not in _IMAGE_CRITIC_REGISTRY:
        raise ValueError(f"Unknown image critic backend '{backend}'")

    adapter_class = _IMAGE_CRITIC_REGISTRY[backend]
    return adapter_class(**kwargs)
```

---

## 9. Configuration

### 9.1 Environment Variables

```bash
# Required
ANTHROPIC_API_KEY="sk-ant-..."

# Optional (with defaults)
SPARK_CRITIQUE_PRIMARY_MODEL="claude-3-5-sonnet-20241022"
SPARK_CRITIQUE_FALLBACK_MODELS="claude-3-haiku-20240307"
SPARK_CRITIQUE_TEMPERATURE="0.0"
SPARK_CRITIQUE_SEED="42"
SPARK_CRITIQUE_TIMEOUT="30"
SPARK_CRITIQUE_MAX_RETRIES="3"
```

### 9.2 Config File Support

```python
def load_spark_critique_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load Spark critique config from TOML file.

    Args:
        config_path: Path to config file (defaults to .aidm/critique_config.toml)

    Returns:
        Dict with config values
    """
    if config_path is None:
        config_path = Path.home() / ".aidm" / "critique_config.toml"

    if not config_path.exists():
        return {}  # Use defaults

    with open(config_path, "r") as f:
        config = toml.load(f)

    return config.get("spark_critique", {})
```

---

## 10. Gap Analysis

### What Exists:
✅ `ImageCritiqueAdapter` protocol
✅ `CritiqueResult` / `CritiqueRubric` schemas
✅ Test infrastructure

### What's Missing:
❌ `SparkCritiqueAdapter` implementation
❌ Anthropic API client integration
❌ Prompt templates
❌ JSON response parser
❌ Error handling + fallback logic
❌ Usage tracking
❌ Integration tests with mock API

### Implementation Checklist:
1. ✅ Define `SparkCritiqueAdapter` class structure
2. ✅ Design prompt engineering system
3. ✅ Design error handling + fallback
4. ❌ Implement `SparkCritiqueAdapter` in `image_critique_adapter.py`
5. ❌ Add Anthropic client dependency to `pyproject.toml`
6. ❌ Write unit tests (mock API responses)
7. ❌ Write integration tests (real API with test images)
8. ❌ Add PBHA determinism tests

---

## 11. Dependencies

### 11.1 Python Packages

```toml
[tool.poetry.dependencies]
anthropic = "^0.18.0"  # Anthropic Python SDK
```

### 11.2 API Requirements

- Anthropic API key with vision model access
- Sufficient API quota (100+ images/day for typical prep workload)

---

## 12. Future Enhancements

1. **Async Critique**: Use `asyncio` for concurrent API calls
2. **Streaming Responses**: Stream dimension scores as they're evaluated
3. **Multi-Model Consensus**: Aggregate scores from 2+ models for higher confidence
4. **Custom Prompts**: Allow per-campaign prompt customization
5. **Fine-Tuned Models**: Train custom critique model on campaign-specific data

---

**END OF SPECIFICATION**
