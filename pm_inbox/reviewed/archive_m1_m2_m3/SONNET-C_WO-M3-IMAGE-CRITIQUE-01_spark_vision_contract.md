# Spark Vision Contract for Image Critique

**Agent:** Sonnet-C
**Work Order:** WO-M3-IMAGE-CRITIQUE-01
**Date:** 2026-02-11
**Status:** Design Specification

---

## 1. Overview

This document defines the contract extension for Spark to support vision-based image critique. The existing `SparkRequest`/`SparkResponse` pattern is text-only. This specification proposes a vision-capable extension that maintains architectural consistency with the existing Spark adapter.

---

## 2. Design Principles

### 2.1 Maintain Existing Pattern

- Follow `SparkRequest`/`SparkResponse` schema validation pattern
- Preserve boundary laws (BL-001, BL-002, BL-013, BL-016)
- Use same error handling and finish reason semantics

### 2.2 Vision-Specific Requirements

- **Input**: Image bytes + text prompt (scene description)
- **Output**: Structured critique matching `CritiqueResult` schema
- **Determinism**: Same image + prompt → same critique (requires seed support)
- **Validation**: Fail fast on invalid image formats or malformed responses

---

## 3. Proposed Schema Extension

### 3.1 SparkVisionRequest

```python
@dataclass
class SparkVisionRequest:
    """Canonical vision request from AIDM to SPARK.

    Extends SparkRequest pattern for vision-language models.

    Attributes:
        image_bytes: Image data (PNG/JPEG, REQUIRED, non-empty)
        prompt: Text prompt for critique (REQUIRED, non-empty)
        temperature: Sampling temperature 0.0-2.0 (REQUIRED)
        max_tokens: Maximum response tokens (REQUIRED, positive)
        json_mode: Request structured JSON output (REQUIRED for critique)
        seed: RNG seed for reproducibility (OPTIONAL)
        metadata: Provider-specific parameters (e.g., image format, max_image_size)
    """
    image_bytes: bytes
    prompt: str
    temperature: float
    max_tokens: int
    json_mode: bool = True  # Always True for critique
    seed: Optional[int] = None
    metadata: Optional[dict] = None

    def __post_init__(self):
        if not self.image_bytes:
            raise ValueError("image_bytes MUST be non-empty")
        if not self.prompt:
            raise ValueError("prompt MUST be non-empty string")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(f"temperature MUST be in [0.0, 2.0], got {self.temperature}")
        if self.max_tokens <= 0:
            raise ValueError(f"max_tokens MUST be positive, got {self.max_tokens}")
        # Validate image format (PNG/JPEG magic bytes)
        if not self._is_valid_image_format():
            raise ValueError("image_bytes MUST be valid PNG or JPEG")

    def _is_valid_image_format(self) -> bool:
        """Check if image_bytes starts with PNG or JPEG magic bytes."""
        if self.image_bytes[:8] == b'\x89PNG\r\n\x1a\n':  # PNG
            return True
        if self.image_bytes[:2] == b'\xff\xd8':  # JPEG
            return True
        return False
```

### 3.2 SparkVisionResponse

```python
@dataclass
class SparkVisionResponse:
    """Canonical vision response from SPARK to AIDM.

    Attributes:
        critique_json: Structured critique output (JSON string)
        finish_reason: Why generation stopped (REQUIRED)
        tokens_used: Total tokens consumed (REQUIRED, non-negative)
        provider_metadata: Provider-specific info (e.g., model_name, image_tokens)
        error: Error message if critique failed
    """
    critique_json: str
    finish_reason: FinishReason
    tokens_used: int
    provider_metadata: Optional[dict] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.finish_reason == FinishReason.ERROR and not self.error:
            raise ValueError("error field MUST be populated when finish_reason is 'error'")
        if self.tokens_used < 0:
            raise ValueError(f"tokens_used MUST be non-negative, got {self.tokens_used}")
        # Validate JSON if not error
        if self.finish_reason != FinishReason.ERROR:
            try:
                json.loads(self.critique_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"critique_json MUST be valid JSON, got: {e}")
```

---

## 4. Critique Prompt Template

### 4.1 System Prompt

```
You are an expert image quality validator for a D&D campaign. Analyze the provided image against the scene description and evaluate it across five quality dimensions.
```

### 4.2 User Prompt Template

```
Scene Description: {scene_description}

Evaluate this image across five dimensions and return a JSON object with this exact structure:

{{
  "passed": <true|false>,
  "overall_severity": "<critical|major|minor|acceptable>",
  "overall_score": <float 0.0-1.0>,
  "rejection_reason": "<reason if failed, null if passed>",
  "dimensions": [
    {{
      "dimension": "artifacting",
      "severity": "<critical|major|minor|acceptable>",
      "score": <float 0.0-1.0>,
      "reason": "<explanation>",
      "measurement_method": "llm_vision"
    }},
    {{
      "dimension": "composition",
      "severity": "<critical|major|minor|acceptable>",
      "score": <float 0.0-1.0>,
      "reason": "<explanation>",
      "measurement_method": "llm_vision"
    }},
    {{
      "dimension": "identity_match",
      "severity": "<critical|major|minor|acceptable>",
      "score": <float 0.0-1.0>,
      "reason": "<explanation>",
      "measurement_method": "llm_vision"
    }},
    {{
      "dimension": "readability",
      "severity": "<critical|major|minor|acceptable>",
      "score": <float 0.0-1.0>,
      "reason": "<explanation>",
      "measurement_method": "llm_vision"
    }},
    {{
      "dimension": "style_adherence",
      "severity": "<critical|major|minor|acceptable>",
      "score": <float 0.0-1.0>,
      "reason": "<explanation>",
      "measurement_method": "llm_vision"
    }}
  ]
}}

Quality Dimensions:
1. **Artifacting**: Check for AI artifacts (extra fingers, malformed anatomy, unnatural textures)
   - CRITICAL: Major anatomical errors (6 fingers, fused limbs, wrong species)
   - MAJOR: Noticeable artifacts (distorted faces, unnatural proportions)
   - MINOR: Subtle artifacts (texture inconsistencies, minor details)
   - ACCEPTABLE: No obvious artifacts

2. **Composition**: Is the subject properly framed and centered?
   - CRITICAL: Subject cut off or completely off-center
   - MAJOR: Poor framing (too much empty space, awkward cropping)
   - MINOR: Slightly off-center or suboptimal framing
   - ACCEPTABLE: Well-composed and properly framed

3. **Identity Match**: Does the image match the described subject?
   - CRITICAL: Wrong species/gender/major features
   - MAJOR: Missing key descriptors (wrong hair color, age, attire)
   - MINOR: Minor details differ (accessories, minor features)
   - ACCEPTABLE: Matches description accurately

4. **Readability**: Are details clear and distinguishable at UI size?
   - CRITICAL: Blurry, pixelated, or completely illegible
   - MAJOR: Hard to make out features, low detail
   - MINOR: Slightly soft or lacks fine detail
   - ACCEPTABLE: Sharp, clear, readable at UI size

5. **Style Adherence**: Matches campaign art style (fantasy, painterly, consistent tone)?
   - CRITICAL: Completely wrong style (photo-realistic vs fantasy art)
   - MAJOR: Noticeable style mismatch (wrong color palette, tone)
   - MINOR: Subtle style inconsistency
   - ACCEPTABLE: Matches campaign style

Scoring Guidelines:
- 0.90-1.00: Excellent quality
- 0.70-0.89: Good quality (ACCEPTABLE threshold)
- 0.50-0.69: Fair quality (MINOR issues)
- 0.30-0.49: Poor quality (MAJOR issues)
- 0.00-0.29: Critical quality (CRITICAL issues, auto-reject)

Overall Pass/Fail:
- PASS if all dimensions >= threshold AND no CRITICAL severity
- FAIL otherwise
```

---

## 5. Response Parsing

### 5.1 JSON Schema Validation

```python
def parse_spark_vision_response(response: SparkVisionResponse) -> CritiqueResult:
    """Parse Spark vision response into CritiqueResult.

    Args:
        response: Spark vision response with critique_json

    Returns:
        CritiqueResult matching existing schema

    Raises:
        ValueError: If JSON doesn't match expected schema
    """
    data = json.loads(response.critique_json, sort_keys=True)

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
            measurement_method=dim_data["measurement_method"]
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
        critique_method="llm_vision"
    )
```

---

## 6. Model Selection

### 6.1 Recommended Models

| Model | Use Case | Cost | Speed | Quality |
|-------|----------|------|-------|---------|
| Claude 3.5 Sonnet | Production critique | High | Fast | Excellent |
| Claude 3 Haiku | Budget critique | Low | Very fast | Good |
| GPT-4 Vision | Alternative provider | High | Medium | Excellent |
| Gemini Pro Vision | Budget alternative | Medium | Fast | Good |

### 6.2 Model-Specific Considerations

**Claude 3.5 Sonnet**:
- Supports vision + JSON mode natively
- Max image size: 5MB (1568 x 1568 recommended)
- Tokens: ~1270 tokens per 1024x1024 image
- Response time: ~2-5s per image

**Fallback Strategy**:
- Primary: Claude 3.5 Sonnet
- Fallback 1: Claude 3 Haiku (if quota exceeded)
- Fallback 2: Gemini Pro Vision (if Anthropic unavailable)

---

## 7. Error Handling

### 7.1 Error Categories

| Error Type | Cause | Handling |
|------------|-------|----------|
| **InvalidImageError** | Image bytes malformed | Return CritiqueResult(passed=False, error_message="Invalid image format") |
| **ModelUnavailableError** | API down or quota exceeded | Try fallback model, then fail critique |
| **JSONParseError** | LLM returned invalid JSON | Retry once with stricter prompt, then fail |
| **TimeoutError** | Request took > 30s | Retry once, then fail critique |
| **RateLimitError** | API rate limit hit | Wait + retry with exponential backoff (max 3 attempts) |

### 7.2 Fallback Behavior

```python
def critique_with_fallback(
    image_bytes: bytes,
    scene_description: str,
    rubric: CritiqueRubric
) -> CritiqueResult:
    """Attempt critique with fallback chain.

    Returns:
        CritiqueResult if any model succeeds
        CritiqueResult(passed=False, error_message=...) if all fail
    """
    models = ["claude-3-5-sonnet", "claude-3-haiku", "gemini-pro-vision"]

    for model_name in models:
        try:
            result = attempt_critique(image_bytes, scene_description, model_name)
            return result
        except (ModelUnavailableError, TimeoutError) as e:
            continue  # Try next model
        except InvalidImageError:
            return CritiqueResult(
                passed=False,
                overall_severity=SeverityLevel.CRITICAL,
                dimensions=[],
                overall_score=0.0,
                rejection_reason="Invalid image format",
                critique_method="error"
            )

    # All models failed
    return CritiqueResult(
        passed=False,
        overall_severity=SeverityLevel.CRITICAL,
        dimensions=[],
        overall_score=0.0,
        rejection_reason="All critique models unavailable",
        critique_method="error"
    )
```

---

## 8. Cost Analysis

### 8.1 Per-Image Critique Cost

| Model | Input Cost | Output Cost | Total per Image |
|-------|------------|-------------|-----------------|
| Claude 3.5 Sonnet | $3.00/1M input tokens | $15.00/1M output tokens | ~$0.005-0.008 |
| Claude 3 Haiku | $0.25/1M input tokens | $1.25/1M output tokens | ~$0.001-0.002 |
| Gemini Pro Vision | $0.25/1M input tokens | $0.50/1M output tokens | ~$0.001-0.002 |

**Assumptions**:
- Image: 1024x1024 (~1270 tokens)
- Prompt: ~500 tokens
- Response: ~400 tokens (JSON)
- Total: ~2170 tokens per critique

**Prep Time Cost Estimate** (100 NPC portraits):
- Claude 3.5 Sonnet: $0.50-0.80
- Claude 3 Haiku: $0.10-0.20

---

## 9. Determinism & Reproducibility

### 9.1 Seed Support

- **Requirement**: Same image + same seed → same critique
- **Implementation**: Pass `seed` parameter to Spark API
- **Testing**: Run same critique 10× with same seed, verify identical JSON output

### 9.2 Known Non-Determinism Risks

1. **Provider changes**: Model updates may change behavior
2. **Image encoding**: Different PNG encoders may produce different bytes
3. **Floating point precision**: JSON floats may have rounding differences

**Mitigation**:
- Pin model versions in API calls (e.g., `claude-3-5-sonnet-20241022`)
- Normalize image bytes before critique (re-encode to standard PNG)
- Use `json.dumps(sort_keys=True)` for deterministic serialization

---

## 10. Integration Points

### 10.1 Prep Pipeline Flow

```
1. Generate image (SDXL Lightning)
2. Encode image to PNG bytes
3. Create SparkVisionRequest(image_bytes, scene_description)
4. Call Spark vision API
5. Parse SparkVisionResponse → CritiqueResult
6. If passed=False → regenerate with adjusted parameters
7. If passed=True → save image to AssetStore
```

### 10.2 Adapter Interface

```python
class SparkCritiqueAdapter:
    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        """Critique image using Spark vision model."""
        # Build prompt from rubric + scene description
        prompt = build_critique_prompt(rubric, anchor_image_bytes, style_reference_bytes)

        # Create vision request
        request = SparkVisionRequest(
            image_bytes=image_bytes,
            prompt=prompt,
            temperature=0.0,  # Deterministic
            max_tokens=500,
            json_mode=True,
            seed=42  # Fixed seed for determinism
        )

        # Call Spark vision API
        response = self.spark_client.vision_generate(request)

        # Parse response
        return parse_spark_vision_response(response)
```

---

## 11. Gap Analysis

### What Exists:
✅ `CritiqueResult` schema
✅ `CritiqueRubric` with thresholds
✅ `ImageCritiqueAdapter` protocol
✅ `StubImageCritic` placeholder

### What's Missing:
❌ `SparkVisionRequest`/`SparkVisionResponse` schemas
❌ Spark vision API client integration
❌ Critique prompt template system
❌ JSON response parser
❌ Error handling + fallback logic
❌ Cost tracking and monitoring

### Implementation Checklist:
1. Add `SparkVisionRequest`/`SparkVisionResponse` to `spark_adapter.py`
2. Implement `SparkVisionClient` (API wrapper)
3. Create `SparkCritiqueAdapter` in `image_critique_adapter.py`
4. Add critique prompt templates
5. Write tests for vision request/response validation
6. Add integration tests with mock Spark API

---

## 12. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **API costs exceed budget** | High | Use Haiku for most critiques, Sonnet only for borderline cases |
| **Slow critique (>10s)** | Medium | Run critiques in parallel, batch process during prep |
| **Non-deterministic results** | Medium | Pin model versions, use fixed seeds, validate with PBHA tests |
| **Model unavailable** | Low | Implement fallback chain (Sonnet → Haiku → Gemini) |
| **JSON schema drift** | Low | Validate response schema, fail fast on malformed JSON |

---

## 13. Future Enhancements

1. **Batch Critique**: Process multiple images in one API call (if supported)
2. **Streaming Responses**: Stream dimension scores as they're evaluated
3. **Custom Rubrics**: Allow per-campaign rubric customization
4. **Critique Caching**: Cache critiques by image hash to avoid re-processing
5. **Multi-Model Consensus**: Use 2+ models, aggregate scores for higher confidence

---

## Appendix A: Example Request/Response

### Request
```python
SparkVisionRequest(
    image_bytes=b'\x89PNG\r\n...',  # PNG bytes
    prompt="Scene Description: A stern female dwarf cleric...",
    temperature=0.0,
    max_tokens=500,
    json_mode=True,
    seed=42
)
```

### Response
```json
{
  "passed": false,
  "overall_severity": "major",
  "overall_score": 0.62,
  "rejection_reason": "Composition and artifacting issues detected",
  "dimensions": [
    {
      "dimension": "artifacting",
      "severity": "major",
      "score": 0.45,
      "reason": "Detected extra finger on right hand (6 fingers visible)",
      "measurement_method": "llm_vision"
    },
    {
      "dimension": "composition",
      "severity": "minor",
      "score": 0.68,
      "reason": "Subject slightly off-center, excessive headroom",
      "measurement_method": "llm_vision"
    },
    {
      "dimension": "identity_match",
      "severity": "acceptable",
      "score": 0.85,
      "reason": "Matches description: female dwarf, stern expression, clerical robes",
      "measurement_method": "llm_vision"
    },
    {
      "dimension": "readability",
      "severity": "acceptable",
      "score": 0.78,
      "reason": "Clear details, readable at UI size, good sharpness",
      "measurement_method": "llm_vision"
    },
    {
      "dimension": "style_adherence",
      "severity": "acceptable",
      "score": 0.82,
      "reason": "Matches fantasy art style, appropriate color palette",
      "measurement_method": "llm_vision"
    }
  ]
}
```

---

**END OF SPECIFICATION**
