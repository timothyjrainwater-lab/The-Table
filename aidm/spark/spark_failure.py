"""Spark failure taxonomy — re-export from aidm.schemas.spark_failure.

The canonical definition lives in aidm.schemas.spark_failure to allow
core-layer imports without boundary violations.
This module re-exports for backward compatibility with existing spark-layer code.
"""

from aidm.schemas.spark_failure import SparkFailure, SparkFailureMode

__all__ = ["SparkFailure", "SparkFailureMode"]
