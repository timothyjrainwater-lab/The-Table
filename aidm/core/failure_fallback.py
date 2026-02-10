"""Failure fallback resolver for AIDM image generation.

M3 IMPLEMENTATION: FailureFallbackResolver
------------------------------------------
This module provides graceful degradation when image generation fails after all
regeneration attempts are exhausted. The game remains playable without images.

Based on approved design: docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md

Core Strategy:
    Four-tier fallback hierarchy prioritizing:
    1. Shipped art pack (archetype-specific)
    2. Generic category placeholder
    3. Solid color + text overlay
    4. Text-only mode (no image)

Architecture:
    - FailureFallbackResolver: Main resolver class
    - match_archetype(): Archetype matching for shipped art pack
    - generate_solid_color(): Solid color PNG generation with text overlay
    - resolve_fallback(): Decision tree logic for fallback selection
"""

import io
import hashlib
from typing import Optional, Dict, Any, List
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from aidm.schemas.fallback import FallbackTier, FallbackResult, FallbackReason


class FailureFallbackResolver:
    """Resolver for image generation failure fallback.

    Implements four-tier fallback hierarchy with archetype matching,
    solid color generation, and text-only mode.

    Attributes:
        shipped_art_manifest: Path to shipped art pack manifest.json
        generic_placeholders_dir: Path to generic category placeholders
        enable_solid_color: Allow solid color + text generation (default: True)
        enable_text_only: Allow text-only mode (default: True)
    """

    # Color scheme by asset type (design spec Section 1.3)
    COLOR_SCHEMES = {
        "npc": "#4A90E2",  # Blue
        "scene": "#7ED321",  # Green
        "item": "#BD10E0",  # Purple
        "default": "#999999",  # Gray
    }

    def __init__(
        self,
        shipped_art_manifest: Optional[Path] = None,
        generic_placeholders_dir: Optional[Path] = None,
        enable_solid_color: bool = True,
        enable_text_only: bool = True
    ):
        """Initialize fallback resolver.

        Args:
            shipped_art_manifest: Path to shipped art pack manifest.json (optional)
            generic_placeholders_dir: Path to generic placeholders directory (optional)
            enable_solid_color: Allow solid color + text generation
            enable_text_only: Allow text-only mode (last resort)
        """
        self.shipped_art_manifest = shipped_art_manifest
        self.generic_placeholders_dir = generic_placeholders_dir
        self.enable_solid_color = enable_solid_color
        self.enable_text_only = enable_text_only

        # Load shipped art pack manifest if provided
        self._shipped_art_index: Optional[Dict[str, Any]] = None
        if shipped_art_manifest and shipped_art_manifest.exists():
            self._load_shipped_art_manifest()

    def _load_shipped_art_manifest(self):
        """Load shipped art pack manifest.json into memory.

        Manifest schema (design spec Section 9.3):
        {
            "npc_portraits": [...],
            "scenes": [...],
            "items": [...]
        }
        """
        import json
        try:
            with open(self.shipped_art_manifest, 'r') as f:
                manifest = json.load(f)
            self._shipped_art_index = manifest
        except Exception as e:
            # Non-fatal: fallback system continues without shipped art pack
            self._shipped_art_index = None

    def resolve_fallback(
        self,
        asset_metadata: Dict[str, Any],
        failure_reason: FallbackReason,
        available_art: Optional[Dict[str, Any]] = None
    ) -> FallbackResult:
        """Resolve fallback for failed image generation.

        Implements decision tree logic from design spec Section 7.

        Args:
            asset_metadata: Asset metadata (species, class, gender, location_type, etc.)
            failure_reason: Why generation failed
            available_art: Optional override for shipped art pack availability

        Returns:
            FallbackResult with selected tier, image bytes, and metadata

        Decision Tree:
            1. Check shipped art pack → archetype match?
            2. Check generic category placeholder → exists?
            3. Check solid color + text → Pillow available?
            4. Text-only mode (last resort)
        """
        asset_type = asset_metadata.get("asset_type", "unknown")
        asset_name = asset_metadata.get("asset_name", "Unknown")

        # Step 1: Check shipped art pack
        archetype_match = self.match_archetype(asset_metadata, available_art)
        if archetype_match:
            return self._create_shipped_art_fallback(
                archetype_match, asset_type, asset_name, failure_reason
            )

        # Step 2: Check generic category placeholder
        generic_placeholder = self._find_generic_placeholder(asset_type)
        if generic_placeholder:
            return self._create_generic_fallback(
                generic_placeholder, asset_type, asset_name, failure_reason
            )

        # Step 3: Check solid color + text rendering
        if self.enable_solid_color:
            try:
                return self._create_solid_color_fallback(
                    asset_metadata, asset_type, asset_name, failure_reason
                )
            except Exception:
                # Pillow not available or generation failed → continue to text-only
                pass

        # Step 4: Text-only mode (last resort)
        if self.enable_text_only:
            return self._create_text_only_fallback(
                asset_type, asset_name, failure_reason
            )

        # Impossible state: text-only disabled and solid color failed
        raise RuntimeError("All fallback tiers exhausted and text-only mode disabled")

    def match_archetype(
        self,
        metadata: Dict[str, Any],
        art_manifest: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Match asset metadata to shipped art pack archetype.

        Implements archetype matching logic from design spec Section 7.2.

        Matching Hierarchy (NPC portraits):
            1. Exact match: species + class + gender
            2. Partial match: species + class (ignore gender)
            3. Species-only match: species (ignore class + gender)
            4. No match: None

        Matching Hierarchy (Scenes):
            1. Exact match: location_type
            2. Generic match: location_category (indoor vs outdoor)
            3. No match: None

        Matching Hierarchy (Items):
            1. Exact match: item_type + item_subtype
            2. Type-only match: item_type
            3. No match: None

        Args:
            metadata: Asset metadata (species, class, gender, location_type, etc.)
            art_manifest: Optional override for shipped art pack manifest

        Returns:
            Filename of matched archetype (e.g., "human_fighter_male.png") or None
        """
        # Use provided manifest or fallback to loaded manifest
        manifest = art_manifest or self._shipped_art_index
        if not manifest:
            return None

        asset_type = metadata.get("asset_type", "unknown")

        # NPC portrait matching
        if asset_type == "npc" or asset_type == "npc_portrait":
            return self._match_npc_archetype(metadata, manifest)

        # Scene matching
        if asset_type == "scene" or asset_type == "scene_background":
            return self._match_scene_archetype(metadata, manifest)

        # Item matching
        if asset_type == "item" or asset_type == "item_icon":
            return self._match_item_archetype(metadata, manifest)

        return None

    def _match_npc_archetype(
        self,
        metadata: Dict[str, Any],
        manifest: Dict[str, Any]
    ) -> Optional[str]:
        """Match NPC portrait to shipped art pack.

        Hierarchy:
            1. Exact: species + class + gender
            2. Partial: species + class
            3. Species-only: species
            4. No match

        Args:
            metadata: NPC metadata (species, class, gender)
            manifest: Shipped art pack manifest

        Returns:
            Filename or None
        """
        species = metadata.get("species", "").lower()
        char_class = metadata.get("class", "").lower()
        gender = metadata.get("gender", "").lower()

        npc_portraits = manifest.get("npc_portraits", [])

        # 1. Exact match: species + class + gender
        for portrait in npc_portraits:
            arch = portrait.get("archetype", {})
            if (
                arch.get("species", "").lower() == species
                and arch.get("class", "").lower() == char_class
                and arch.get("gender", "").lower() == gender
            ):
                return portrait.get("filename")

        # 2. Partial match: species + class (no gender specified in archetype)
        for portrait in npc_portraits:
            arch = portrait.get("archetype", {})
            if (
                arch.get("species", "").lower() == species
                and arch.get("class", "").lower() == char_class
                and not arch.get("gender")  # Must NOT have gender field (generic match)
            ):
                return portrait.get("filename")

        # 3. Species-only match: species (no class/gender specified in archetype)
        for portrait in npc_portraits:
            arch = portrait.get("archetype", {})
            if (
                arch.get("species", "").lower() == species
                and not arch.get("class")  # Must NOT have class field (generic match)
                and not arch.get("gender")  # Must NOT have gender field (generic match)
            ):
                return portrait.get("filename")

        # 4. No match
        return None

    def _match_scene_archetype(
        self,
        metadata: Dict[str, Any],
        manifest: Dict[str, Any]
    ) -> Optional[str]:
        """Match scene background to shipped art pack.

        Hierarchy:
            1. Exact: location_type
            2. Generic: location_category (indoor vs outdoor)
            3. No match

        Args:
            metadata: Scene metadata (location_type, location_category)
            manifest: Shipped art pack manifest

        Returns:
            Filename or None
        """
        location_type = metadata.get("location_type", "").lower()
        location_category = metadata.get("location_category", "").lower()

        scenes = manifest.get("scenes", [])

        # 1. Exact match: location_type
        for scene in scenes:
            if scene.get("location_type", "").lower() == location_type:
                return scene.get("filename")

        # 2. Generic match: location_category (no location_type specified in scene)
        if location_category:
            for scene in scenes:
                if (
                    scene.get("location_category", "").lower() == location_category
                    and not scene.get("location_type")  # Must NOT have location_type (generic match)
                ):
                    return scene.get("filename")

        # 3. No match
        return None

    def _match_item_archetype(
        self,
        metadata: Dict[str, Any],
        manifest: Dict[str, Any]
    ) -> Optional[str]:
        """Match item icon to shipped art pack.

        Hierarchy:
            1. Exact: item_type + item_subtype
            2. Type-only: item_type
            3. No match

        Args:
            metadata: Item metadata (item_type, item_subtype)
            manifest: Shipped art pack manifest

        Returns:
            Filename or None
        """
        item_type = metadata.get("item_type", "").lower()
        item_subtype = metadata.get("item_subtype", "").lower()

        items = manifest.get("items", [])

        # 1. Exact match: item_type + item_subtype
        for item in items:
            if (
                item.get("item_type", "").lower() == item_type
                and item.get("item_subtype", "").lower() == item_subtype
            ):
                return item.get("filename")

        # 2. Type-only match: item_type (no item_subtype specified in item)
        for item in items:
            if (
                item.get("item_type", "").lower() == item_type
                and not item.get("item_subtype")  # Must NOT have item_subtype (generic match)
            ):
                return item.get("filename")

        # 3. No match
        return None

    def generate_solid_color(
        self,
        asset_type: str,
        asset_name: str,
        description: str,
        resolution: int = 512
    ) -> bytes:
        """Generate solid color PNG with text overlay.

        Implements solid color generation from design spec Section 1.3.

        Color Scheme by Asset Type:
            - NPC portraits: Blue (#4A90E2)
            - Scenes: Green (#7ED321)
            - Items: Purple (#BD10E0)
            - Default: Gray (#999999)

        Text Overlay:
            - Line 1: Asset type (centered, bold, 24pt)
            - Line 2: Asset name (centered, regular, 18pt)
            - Line 3: Description snippet (centered, italic, 14pt, truncated to 80 chars)

        Args:
            asset_type: Asset category (npc, scene, item)
            asset_name: Human-readable asset name
            description: Asset description (truncated to 80 chars)
            resolution: Image resolution (default: 512×512)

        Returns:
            PNG image bytes

        Raises:
            ImportError: If Pillow not available
        """
        # Select color based on asset type
        color_hex = self.COLOR_SCHEMES.get(asset_type, self.COLOR_SCHEMES["default"])
        color_rgb = self._hex_to_rgb(color_hex)

        # Create image
        img = Image.new('RGB', (resolution, resolution), color=color_rgb)
        draw = ImageDraw.Draw(img)

        # Truncate description to 80 chars
        description_truncated = description[:80] + "..." if len(description) > 80 else description

        # Text overlay (simplified - no custom fonts, use default)
        # Line 1: Asset type (uppercase)
        asset_type_text = asset_type.upper().replace("_", " ")
        text_y = resolution // 4

        # Line 2: Asset name
        asset_name_text = asset_name
        text_y += 50

        # Line 3: Description
        description_text = f'"{description_truncated}"'
        text_y += 50

        # Draw text (white color for visibility)
        text_color = (255, 255, 255)

        # Use default font (Pillow built-in)
        try:
            # Try to use a larger default font
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        except Exception:
            # Fallback to basic font
            font_large = font_medium = font_small = None

        # Draw centered text
        y_offset = resolution // 4
        self._draw_centered_text(draw, asset_type_text, resolution, y_offset, text_color, font_large)
        y_offset += 60
        self._draw_centered_text(draw, asset_name_text, resolution, y_offset, text_color, font_medium)
        y_offset += 50
        self._draw_centered_text(draw, description_text, resolution, y_offset, text_color, font_small)

        # Convert to PNG bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple.

        Args:
            hex_color: Hex color string (e.g., "#4A90E2")

        Returns:
            RGB tuple (e.g., (74, 144, 226))
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _draw_centered_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        img_width: int,
        y_pos: int,
        color: tuple,
        font
    ):
        """Draw centered text on image.

        Args:
            draw: PIL ImageDraw object
            text: Text to draw
            img_width: Image width (for centering)
            y_pos: Y position
            color: Text color (RGB tuple)
            font: PIL Font object
        """
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x_pos = (img_width - text_width) // 2
        draw.text((x_pos, y_pos), text, fill=color, font=font)

    def _find_generic_placeholder(self, asset_type: str) -> Optional[Path]:
        """Find generic category placeholder for asset type.

        Args:
            asset_type: Asset category (npc, scene, item)

        Returns:
            Path to generic placeholder file or None
        """
        if not self.generic_placeholders_dir or not self.generic_placeholders_dir.exists():
            return None

        # Map asset types to generic placeholder filenames
        placeholder_map = {
            "npc": "generic_npc_portrait.png",
            "npc_portrait": "generic_npc_portrait.png",
            "scene": "generic_scene_background.png",
            "scene_background": "generic_scene_background.png",
            "item": "generic_item_icon.png",
            "item_icon": "generic_item_icon.png",
        }

        placeholder_filename = placeholder_map.get(asset_type)
        if not placeholder_filename:
            return None

        placeholder_path = self.generic_placeholders_dir / placeholder_filename
        return placeholder_path if placeholder_path.exists() else None

    def _create_shipped_art_fallback(
        self,
        filename: str,
        asset_type: str,
        asset_name: str,
        failure_reason: FallbackReason
    ) -> FallbackResult:
        """Create FallbackResult for shipped art pack.

        Args:
            filename: Shipped art pack filename
            asset_type: Asset category
            asset_name: Asset name
            failure_reason: Why generation failed

        Returns:
            FallbackResult with SHIPPED_ART tier
        """
        # Load image bytes from shipped art pack
        if self.shipped_art_manifest:
            shipped_art_dir = self.shipped_art_manifest.parent
            file_path = shipped_art_dir / filename
        else:
            # No manifest → construct path from filename
            file_path = Path(filename)

        if file_path.exists():
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
        else:
            # File doesn't exist → fallback to next tier
            raise FileNotFoundError(f"Shipped art file not found: {file_path}")

        return FallbackResult(
            tier=FallbackTier.SHIPPED_ART,
            image_bytes=image_bytes,
            description=f"Shipped art pack placeholder for {asset_name}",
            file_path=str(file_path),
            metadata={
                "fallback_reason": failure_reason.value,
                "fallback_type": FallbackTier.SHIPPED_ART.value,
                "archetype_match": filename,
            }
        )

    def _create_generic_fallback(
        self,
        placeholder_path: Path,
        asset_type: str,
        asset_name: str,
        failure_reason: FallbackReason
    ) -> FallbackResult:
        """Create FallbackResult for generic category placeholder.

        Args:
            placeholder_path: Path to generic placeholder file
            asset_type: Asset category
            asset_name: Asset name
            failure_reason: Why generation failed

        Returns:
            FallbackResult with GENERIC tier
        """
        with open(placeholder_path, 'rb') as f:
            image_bytes = f.read()

        return FallbackResult(
            tier=FallbackTier.GENERIC,
            image_bytes=image_bytes,
            description=f"Generic {asset_type} placeholder for {asset_name}",
            file_path=str(placeholder_path),
            metadata={
                "fallback_reason": failure_reason.value,
                "fallback_type": FallbackTier.GENERIC.value,
            }
        )

    def _create_solid_color_fallback(
        self,
        asset_metadata: Dict[str, Any],
        asset_type: str,
        asset_name: str,
        failure_reason: FallbackReason
    ) -> FallbackResult:
        """Create FallbackResult for solid color + text.

        Args:
            asset_metadata: Asset metadata
            asset_type: Asset category
            asset_name: Asset name
            failure_reason: Why generation failed

        Returns:
            FallbackResult with SOLID_COLOR tier
        """
        description = asset_metadata.get("description", "No description available")
        image_bytes = self.generate_solid_color(asset_type, asset_name, description)

        # Compute deterministic filename from asset metadata
        metadata_hash = hashlib.md5(
            f"{asset_type}_{asset_name}".encode()
        ).hexdigest()[:8]
        filename = f"solid_color_{metadata_hash}.png"

        return FallbackResult(
            tier=FallbackTier.SOLID_COLOR,
            image_bytes=image_bytes,
            description=f"Solid color placeholder for {asset_name}",
            file_path=filename,  # Not a real path, just a placeholder filename
            metadata={
                "fallback_reason": failure_reason.value,
                "fallback_type": FallbackTier.SOLID_COLOR.value,
                "color_scheme": self.COLOR_SCHEMES.get(asset_type, self.COLOR_SCHEMES["default"]),
            }
        )

    def _create_text_only_fallback(
        self,
        asset_type: str,
        asset_name: str,
        failure_reason: FallbackReason
    ) -> FallbackResult:
        """Create FallbackResult for text-only mode.

        Args:
            asset_type: Asset category
            asset_name: Asset name
            failure_reason: Why generation failed

        Returns:
            FallbackResult with TEXT_ONLY tier
        """
        return FallbackResult(
            tier=FallbackTier.TEXT_ONLY,
            image_bytes=None,  # No image for text-only mode
            description=f"Text-only mode for {asset_name}",
            file_path="",  # No file for text-only mode
            metadata={
                "fallback_reason": failure_reason.value,
                "fallback_type": FallbackTier.TEXT_ONLY.value,
            }
        )
