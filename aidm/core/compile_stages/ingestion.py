"""Stage: Content Pack Ingestion.

Loads the content pack from aidm/data/content_pack/, validates it,
and writes ingestion_report.json to the compile workspace.

This stage is the formal entry point for the audit chain defined in
FINDING-WORLDGEN-IP-001:
  ingestion complete → double audit PASS → name strip → IP scan gate → LLM mode

WO-WORLDGEN-INGESTION-001
Reference: docs/contracts/WORLD_COMPILER.md §2.0
Reference: FINDING-WORLDGEN-IP-001 (pm_inbox/PM_BRIEFING_CURRENT.md)

BOUNDARY LAW: No imports from aidm/lens/ at module scope.
ContentPackLoader is imported inside execute() to keep the core
layer boundary clean per BL-003.

Validation policy:
  BLOCKING errors (IC-002): duplicate template_ids, unresolved prereq_feat_refs,
    empty template_ids. These indicate structural corruption — the pack cannot
    be used for audit or compilation.
  WARNINGS (non-blocking): field-length violations (environment_tags,
    alignment_tendency etc. > 100 chars). These are pre-existing data quality
    issues that the double-audit step (step 2 of the IP chain) must review and
    resolve. Ingestion records them in ingestion_report.json under
    "validation_warnings" but does not fail.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional, Tuple

from aidm.core.compile_stages._base import CompileContext, CompileStage
from aidm.schemas.world_compile import StageResult

# Error codes
IC_001 = "IC-001"  # pack directory not found
IC_002 = "IC-002"  # content pack validation failed (structural)

# Default content pack path: aidm/data/content_pack/
# Three parents up from aidm/core/compile_stages/ingestion.py → aidm/
_DEFAULT_PACK_DIR = Path(__file__).parent.parent.parent / "data" / "content_pack"


def _classify_errors(errors: List[str]) -> Tuple[List[str], List[str]]:
    """Split validate() output into blocking errors and non-blocking warnings.

    Blocking (structural corruption):
      - "duplicate template_id"
      - "prereq_feat_ref ... not found"
      - "empty template_id"

    Warnings (data quality — recorded but ingestion proceeds):
      - "chars (max 100)" — field-length violations

    Args:
        errors: Raw error list from ContentPackLoader.validate().

    Returns:
        (blocking_errors, warnings)
    """
    blocking: List[str] = []
    warnings: List[str] = []
    for e in errors:
        if "chars (max 100)" in e:
            warnings.append(e)
        else:
            blocking.append(e)
    return blocking, warnings


class IngestionStage(CompileStage):
    """Compile stage 0: load and validate the content pack.

    Runs immediately after Stage 0 (validate inputs). Produces
    ingestion_report.json in the compile workspace with entity counts,
    content_hash, validation status, and any field-length warnings.

    stage_id:     "ingestion"
    stage_number:  0
    depends_on:    () — no stage dependencies
    """

    def __init__(self, content_pack_dir: Optional[Path] = None) -> None:
        self._content_pack_dir = content_pack_dir

    @property
    def stage_id(self) -> str:
        return "ingestion"

    @property
    def stage_number(self) -> int:
        return 0

    @property
    def depends_on(self) -> tuple:
        return ()

    def execute(self, context: CompileContext) -> StageResult:
        """Load and validate content pack; write ingestion_report.json.

        Args:
            context: Compile context with workspace_dir and logger.

        Returns:
            StageResult with status "success" or "failed".
            On success, output_files contains "ingestion_report.json".
            On failure, error contains IC-001 or IC-002 code.
        """
        start_ms = time.monotonic_ns() // 1_000_000

        # Resolve pack directory
        if self._content_pack_dir is not None:
            pack_dir = self._content_pack_dir
        else:
            pack_dir = _DEFAULT_PACK_DIR

        # IC-001: pack directory must exist
        if not pack_dir.exists():
            elapsed = (time.monotonic_ns() // 1_000_000) - start_ms
            return StageResult(
                stage_id=self.stage_id,
                status="failed",
                output_files=(),
                error=f"{IC_001}: content_pack_dir not found: {pack_dir}",
                elapsed_ms=elapsed,
            )

        # Import inside execute() to respect BL-003 (aidm/core → aidm/lens boundary)
        from aidm.lens.content_pack_loader import ContentPackLoader  # noqa: PLC0415

        loader = ContentPackLoader.from_directory(pack_dir)

        # Classify: structural errors block ingestion; field-length issues are warnings
        all_errors = loader.validate()
        blocking_errors, warnings = _classify_errors(all_errors)

        # IC-002: structural validation must pass
        if blocking_errors:
            elapsed = (time.monotonic_ns() // 1_000_000) - start_ms
            return StageResult(
                stage_id=self.stage_id,
                status="failed",
                output_files=(),
                error=f"{IC_002}: content pack validation failed: {'; '.join(blocking_errors)}",
                elapsed_ms=elapsed,
            )

        content_hash = loader.content_hash
        spell_count = loader.spell_count
        creature_count = loader.creature_count
        feat_count = loader.feat_count

        report = {
            "stage_id": self.stage_id,
            "status": "success",
            "content_pack_dir": str(pack_dir.resolve()),
            "content_hash": content_hash,
            "spell_count": spell_count,
            "creature_count": creature_count,
            "feat_count": feat_count,
            "validation_errors": [],
            "validation_warnings": warnings,
            "pack_id": loader.pack_id,
        }

        # Write ingestion_report.json
        report_path = context.workspace_dir / "ingestion_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)

        # Publish to stage_outputs for downstream stages
        context.stage_outputs["ingestion"] = {
            "content_hash": content_hash,
            "spell_count": spell_count,
            "creature_count": creature_count,
            "feat_count": feat_count,
        }

        result_warnings = tuple(warnings)

        elapsed = (time.monotonic_ns() // 1_000_000) - start_ms
        return StageResult(
            stage_id=self.stage_id,
            status="success",
            output_files=("ingestion_report.json",),
            warnings=result_warnings,
            elapsed_ms=elapsed,
        )
