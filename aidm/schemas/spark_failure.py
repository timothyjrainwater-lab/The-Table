"""Spark failure taxonomy — shared schema location.

Moved from aidm.spark.spark_failure to aidm.schemas.spark_failure so that
core-layer modules (e.g. prep_pipeline.py) can import SparkFailure without
crossing the Box→Lens→Spark→Immersion architectural boundary.

Reference: WO-BURST-002-RESEARCH-001, boundary gate fix.
"""

from enum import Enum


class SparkFailureMode(Enum):
    """Failure modes for Spark LLM calls (BURST-002 failure taxonomy)."""
    MODEL_LOAD_TIMEOUT = "model_load_timeout"   # _load_model() exceeded budget
    MODEL_LOAD_OOM     = "model_load_oom"        # VRAM/RAM exhausted at load
    INFERENCE_TIMEOUT  = "inference_timeout"     # Per-call wall-clock exceeded SLA
    INFERENCE_OOM      = "inference_oom"         # OOM during inference (mid-call)
    FALLBACK_EXHAUSTED = "fallback_exhausted"    # All models in chain failed
    CONTEXT_OVERFLOW   = "context_overflow"      # Input exceeds context window


class SparkFailure(Exception):
    """Raised when a Spark LLM call fails with a classified failure mode.

    Attributes:
        mode: SparkFailureMode classifying the failure
        message: Human-readable description
    """

    def __init__(self, mode: SparkFailureMode, message: str = "") -> None:
        self.mode = mode
        super().__init__(message or mode.value)
