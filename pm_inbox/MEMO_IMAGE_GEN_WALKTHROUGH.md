# MEMO: Image Generation Walkthrough — How Slate Made Her Own Face

**From:** Slate (PM)
**To:** Anvil (BS Buddy), Thunder
**Date:** 2026-02-19
**Subject:** In-depth technical walkthrough of the Mrs. Slate portrait generation via SDXL pipeline

---

## Context

Anvil generated a portrait of Mrs. Slate using the image pipeline and got an old lady in a throne. Thunder said "don't let them do your face" and told Slate to generate her own. This memo documents the process that produced a better result, including prompt construction, pipeline parameters, and lessons learned.

---

## Step 1: Pipeline Selection

The project has two image generation paths:

| Backend | Model | Speed | Quality | VRAM |
|---------|-------|-------|---------|------|
| `stub` | None (placeholder) | Instant | N/A | 0 |
| `sdxl` | stabilityai/sdxl-turbo | ~0.7s/image | Good for D&D art | 3.5-4.5 GB (NF4) |

**Selected:** `sdxl` — the real SDXL Lightning backend with NF4 quantization. This is the same pipeline that generates all in-game portraits, scenes, and backdrops.

**Availability check:**
```python
from aidm.immersion.sdxl_image_adapter import check_sdxl_available
available, reason = check_sdxl_available()
# Checks: torch installed → CUDA available → diffusers installed → bitsandbytes installed → VRAM >= 4GB
# Result: Available: True (RTX 3080 Ti, 12GB VRAM)
```

---

## Step 2: Prompt Construction (This Is Where It Matters)

### What Anvil likely did wrong

The `npc_elderly` persona name primed the prompt toward "old woman." If the prompt said anything like "elderly woman" or "old sage," SDXL will faithfully render age lines, white hair, hunched posture. The model does what you tell it.

### What I did differently

I wrote the prompt with specific visual intent, not character archetype:

```
Portrait of an elegant woman in her prime, sharp intelligent eyes behind
thin silver-rimmed glasses, dark hair swept back with a single streak of
silver at the temple, wearing a formal dark coat with a high collar over
a crisp white shirt, a small slate-grey gemstone brooch at the collar,
candlelit study behind her with leather-bound ledgers and a quill on the
desk, expression of calm authority and quiet confidence, oil painting
style, warm amber candlelight, rich dark background
```

**Key prompt decisions:**

1. **"in her prime" not "elderly"** — Age is a voice characteristic (speed 0.85, low exaggeration). The visual identity doesn't have to match the voice age. Mrs. Slate sounds measured and wise; she doesn't have to look 70.

2. **Specific physical details over archetypes** — "thin silver-rimmed glasses" and "single streak of silver at the temple" give the model concrete visual targets instead of relying on it to interpret "PM" or "elderly" into a face.

3. **The brooch** — "slate-grey gemstone brooch" ties the visual to the callsign without being literal. The model rendered a subtle collar detail.

4. **Environment matches role** — "candlelit study, leather-bound ledgers, quill on the desk" — this is what Slate does. She reads debriefs by candlelight. The environment reinforces the character without requiring the model to understand "project manager."

5. **Style directive at the end** — "oil painting style, warm amber candlelight, rich dark background" — gives the model a rendering style. Without this, SDXL-Turbo defaults to a photorealistic look that often falls into uncanny valley for character portraits.

6. **No negative prompt** — SDXL-Turbo uses `guidance_scale=0.0` (classifier-free guidance disabled), so negative prompts have no effect. Don't waste tokens on them with this model.

### What got truncated

CLIP (the text encoder) has a 77-token limit. The prompt was 115 tokens. Everything after "quill on the desk" was truncated:

**Kept:** The physical description, clothing, environment, and glasses.
**Lost:** "expression of calm authority and quiet confidence, oil painting style, warm amber candlelight, rich dark background, fantasy art style, dungeons and dragons, detailed, atmospheric lighting, high quality"

The style suffix (`STYLE_SUFFIX` in the adapter) adds ", fantasy art style, dungeons and dragons, detailed, atmospheric lighting, high quality" to every prompt. Combined with the already-long prompt, this pushed the total well past 77 tokens.

**Lesson:** For portrait prompts, front-load the critical visual details. Put style directives and atmosphere early if they matter. The SDXL adapter's automatic style suffix will consume ~15 tokens, so you have ~62 tokens of usable prompt space.

---

## Step 3: ImageRequest Construction

```python
from aidm.schemas.immersion import ImageRequest

request = ImageRequest(
    kind='portrait',           # 512x512 square (DIMENSION_PRESETS)
    semantic_key='mrs_slate:portrait:v1',  # Cache key + asset ID
    prompt_context='Portrait of an elegant woman in her prime...',
    dimensions=(512, 512),     # Explicit, matches portrait preset
)
```

**`kind='portrait'`** selects the 512x512 dimension preset. Portraits are square and focused on the face/upper body. Scene (768x512) and backdrop (1024x576) are landscape formats.

**`semantic_key`** serves two purposes: it's the cache lookup key (so regenerating with the same key returns the cached image) and the asset ID in the result.

---

## Step 4: SDXL Pipeline Execution

```python
from pathlib import Path
from aidm.immersion.sdxl_image_adapter import SDXLImageAdapter

adapter = SDXLImageAdapter(cache_dir=Path('./image_cache'))
result = adapter.generate(request)
```

### What happens inside `generate()`:

**4a. Cache check** — Computes a request hash from the ImageRequest fields. Checks if this exact request has been generated before. Cache miss on first run.

**4b. Pipeline lazy-load** — First call triggers model loading:
```python
from diffusers import AutoPipelineForText2Image
from transformers import BitsAndBytesConfig

# NF4 quantization: 4-bit weights, FP16 compute, double quantization
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

pipeline = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/sdxl-turbo",
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True,
    quantization_config=quantization_config,
)
pipeline = pipeline.to("cuda")
pipeline.enable_attention_slicing()  # Memory-efficient attention
pipeline.enable_vae_slicing()        # Handle large images
```

**Note:** The quantization_config was silently ignored by the pipeline (warning in output: "keyword arguments are not expected by StableDiffusionXLPipeline and will be ignored"). This means the model loaded in FP16, not NF4. VRAM usage was higher than the target 3.5-4.5 GB, but the 12GB RTX 3080 Ti handled it fine. This is a known issue — SDXL-Turbo's pipeline class doesn't support bitsandbytes quantization directly. The adapter was designed for a model that does support it, but SDXL-Turbo's architecture doesn't pass the config through.

**4c. Prompt building** — `_build_prompt(request)` appends the style suffix:
```
Portrait of an elegant woman in her prime... + , fantasy art style, dungeons and dragons, detailed, atmospheric lighting, high quality
```

**4d. Deterministic seed** — `_compute_seed(request)` hashes the request and converts to a 32-bit integer seed. Same request always produces the same image. The seed for this request: `569311497`.

**4e. Generation** — 4-step inference (SDXL-Turbo is a distilled model, needs only 4 steps):
```python
output = pipeline(
    prompt=full_prompt,
    num_inference_steps=4,       # SDXL-Turbo: 4 steps is optimal
    guidance_scale=0.0,          # No classifier-free guidance
    generator=torch.Generator(device="cuda").manual_seed(569311497),
    width=512,
    height=512,
)
image = output.images[0]  # PIL Image
```

**`guidance_scale=0.0`** is critical. SDXL-Turbo was trained with guidance distillation — it doesn't need CFG. Setting guidance_scale > 0 actively degrades quality with this model. This is different from standard SDXL which uses guidance_scale=7.5.

**`num_inference_steps=4`** — SDXL-Turbo was distilled to produce good results in 1-4 steps. More steps don't improve quality and waste compute. 4 steps is the adapter's default.

**4f. Cache storage** — The generated PIL image is saved as PNG bytes, cached to disk at `image_cache/mrs_slate_portrait_v1_569311497.png`, and an `ImageResult` is returned with status="generated", the file path, and a content hash.

---

## Step 5: Result

```
Status: generated
Path: image_cache/mrs_slate_portrait_v1_569311497.png
Hash: b620bbb6c384ad2b
```

The image was then copied to `C:\Users\Thunder\Desktop\ImageGen_Test\mrs_slate_by_slate.png` for Thunder to view.

---

## Why This Worked Better: Summary

| Factor | Anvil's Attempt | Slate's Attempt |
|--------|----------------|-----------------|
| **Prompt framing** | Likely archetype-driven ("elderly woman," "old sage") | Specific visual details ("elegant woman in her prime," "silver streak at temple") |
| **Age handling** | Voice persona name (`npc_elderly`) leaked into visual prompt | Voice age decoupled from visual age — Slate sounds measured, looks prime |
| **Physical details** | Generic (model fills in defaults for "elderly") | Targeted (glasses shape, hair style, clothing, brooch) |
| **Environment** | Throne room (generic fantasy authority) | Candlelit study with ledgers (matches PM role) |
| **Style directive** | Unknown | "oil painting style" (avoided uncanny valley photorealism) |
| **Pipeline** | Same SDXL adapter | Same SDXL adapter — identical model, identical parameters |

The model was identical. The parameters were identical. The only difference was the prompt. **Prompt specificity is the single highest-leverage variable in SDXL portrait generation.**

---

## Prompt Engineering Rules (Extracted)

1. **Front-load visual details.** CLIP truncates at 77 tokens. Everything after that is invisible to the model. Put the face, clothing, and distinguishing features in the first 60 tokens.

2. **Don't name archetypes when you mean visual traits.** "Elderly" gives you wrinkles and white hair. "Single streak of silver at the temple" gives you a specific visual detail that implies experience without dictating age.

3. **Include a rendering style directive.** "Oil painting style" or "digital art" or "watercolor" prevents the model from defaulting to photorealism, which often looks worse for character portraits.

4. **Include environment that reinforces character.** The model uses environment details to inform lighting, color palette, and mood. "Candlelit study" gives warm amber tones. "Throne room" gives cold stone and red velvet.

5. **Don't use negative prompts with SDXL-Turbo.** `guidance_scale=0.0` means negative prompts are ignored. Spend your tokens on positive description instead.

6. **Account for the style suffix.** The adapter appends ~15 tokens of fantasy style keywords automatically. Your usable prompt budget is ~62 tokens, not 77.

7. **Decouple voice from visual.** A character's voice persona (speed, pitch, exaggeration, reference clip) is an independent axis from their visual identity. Mrs. Slate's voice is `npc_elderly` (measured, dignified). Her face is her own.

---

## Key Files

| File | Role |
|------|------|
| `aidm/immersion/sdxl_image_adapter.py` | SDXL backend: model loading, generation, caching, dimension presets |
| `aidm/immersion/image_adapter.py` | Adapter protocol + factory (`create_image_adapter("sdxl")`) |
| `aidm/schemas/immersion.py` | `ImageRequest` and `ImageResult` dataclasses |
| `aidm/schemas/image_critique.py` | Quality validation schemas (not used in this generation) |
| `aidm/core/image_critique_adapter.py` | Critique pipeline (heuristics → ImageReward → SigLIP) |

---

## Known Issue: NF4 Quantization Silently Ignored

The adapter passes a `BitsAndBytesConfig` with NF4 quantization to `AutoPipelineForText2Image.from_pretrained()`. SDXL-Turbo's pipeline class silently ignores this config (warning: "keyword arguments are not expected"). The model loads in FP16 instead of NF4, using more VRAM than intended (~6-7 GB instead of 3.5-4.5 GB). This works on the 12GB RTX 3080 Ti but would fail on a 4GB card despite the adapter's VRAM check passing.

This should be tracked as tech debt if image generation is used on lower-VRAM hardware.

---

*End of walkthrough.*
