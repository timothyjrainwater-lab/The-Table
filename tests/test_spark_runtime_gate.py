"""Spark Runtime Constraint Gate Tests -� WO-BURST-002-RESEARCH-001

12 tests enforcing the Spark runtime constraint envelope:
T-01  SparkFailureMode has exactly 6 members
T-02  SPARK_SLA_PER_CALL has entries for all 6 CallTypes
T-03  Each SLA entry has timeout_s and p95_target_s, both floats
T-04  TEMPLATE_NARRATION has entries for all 6 CallTypes, all non-empty strings
T-05  SparkResponse has degraded, failure_mode, fallback_used fields
T-06  Degraded response carries correct template for COMBAT_NARRATION
T-07  Degraded response fallback_used=True when template substituted
T-08  Prep pipeline: asset marked prep_failed when SparkFailure raised, pipeline continues
T-09  Prep pipeline: subsequent asset after failure still processed (skip, not abort)
T-10  TTFT measurement: spark_call profiler record contains required keys
T-11  TURN_WALL_CLOCK_BUDGET_S is a float > 0
T-12  Sensor event SPARK_DEGRADED emitted on runtime failure
"""
import pytest

from aidm.spark.spark_failure import SparkFailure, SparkFailureMode
from aidm.spark.spark_sla import (
    SPARK_SLA_PER_CALL,
    TEMPLATE_NARRATION,
    TURN_WALL_CLOCK_BUDGET_S,
)
from aidm.spark.spark_adapter import FinishReason, SparkResponse

_CALL_TYPES = {
    "COMBAT_NARRATION",
    "OPERATOR_DIRECTIVE",
    "SUMMARY",
    "RULE_EXPLAINER",
    "CLARIFICATION_QUESTION",
    "NPC_DIALOGUE",
}


# ---------------------------------------------------------------------------
# T-01
# ---------------------------------------------------------------------------


def test_t01_spark_failure_mode_six_members():
    """SparkFailureMode enum has exactly 6 members."""
    members = list(SparkFailureMode)
    assert len(members) == 6, f"expected 6, got {len(members)}: {members}"
    expected = {
        "model_load_timeout",
        "model_load_oom",
        "inference_timeout",
        "inference_oom",
        "fallback_exhausted",
        "context_overflow",
    }
    assert {m.value for m in members} == expected


# ---------------------------------------------------------------------------
# T-02
# ---------------------------------------------------------------------------


def test_t02_sla_has_all_call_types():
    """SPARK_SLA_PER_CALL has entries for all 6 CallTypes."""
    assert set(SPARK_SLA_PER_CALL.keys()) == _CALL_TYPES


# ---------------------------------------------------------------------------
# T-03
# ---------------------------------------------------------------------------


def test_t03_sla_entries_have_required_float_keys():
    """Each SLA entry has timeout_s and p95_target_s keys, both floats."""
    for call_type, entry in SPARK_SLA_PER_CALL.items():
        assert "timeout_s" in entry, f"{call_type} missing timeout_s"
        assert "p95_target_s" in entry, f"{call_type} missing p95_target_s"
        assert isinstance(entry["timeout_s"], float), (
            f"{call_type}.timeout_s must be float"
        )
        assert isinstance(entry["p95_target_s"], float), (
            f"{call_type}.p95_target_s must be float"
        )


# ---------------------------------------------------------------------------
# T-04
# ---------------------------------------------------------------------------


def test_t04_template_narration_coverage():
    """TEMPLATE_NARRATION has entries for all 6 CallTypes, all non-empty strings."""
    assert set(TEMPLATE_NARRATION.keys()) == _CALL_TYPES
    for call_type, text in TEMPLATE_NARRATION.items():
        assert isinstance(text, str), f"{call_type} must be str"
        assert len(text) > 0, f"{call_type} must be non-empty"


# ---------------------------------------------------------------------------
# T-05
# ---------------------------------------------------------------------------


def test_t05_spark_response_has_degradation_fields():
    """SparkResponse has degraded, failure_mode, fallback_used fields with correct defaults."""
    resp = SparkResponse(
        text="Hello",
        finish_reason=FinishReason.COMPLETED,
        tokens_used=10,
    )
    assert hasattr(resp, "degraded"), "SparkResponse missing 'degraded'"
    assert hasattr(resp, "failure_mode"), "SparkResponse missing 'failure_mode'"
    assert hasattr(resp, "fallback_used"), "SparkResponse missing 'fallback_used'"
    assert resp.degraded is False
    assert resp.failure_mode is None
    assert resp.fallback_used is False


# ---------------------------------------------------------------------------
# T-06
# ---------------------------------------------------------------------------


def test_t06_degraded_response_has_correct_template():
    """Degraded response with INFERENCE_TIMEOUT carries COMBAT_NARRATION template text."""
    expected_text = TEMPLATE_NARRATION["COMBAT_NARRATION"]
    resp = SparkResponse(
        text=expected_text,
        finish_reason=FinishReason.ERROR,
        tokens_used=0,
        error="inference_timeout",
        degraded=True,
        failure_mode=SparkFailureMode.INFERENCE_TIMEOUT,
        fallback_used=True,
    )
    assert resp.degraded is True
    assert resp.failure_mode == SparkFailureMode.INFERENCE_TIMEOUT
    assert resp.text == expected_text


# ---------------------------------------------------------------------------
# T-07
# ---------------------------------------------------------------------------


def test_t07_degraded_response_fallback_used_true():
    """Degraded response has fallback_used=True when template substituted."""
    resp = SparkResponse(
        text="The action resolves.",
        finish_reason=FinishReason.ERROR,
        tokens_used=0,
        error="oom",
        degraded=True,
        failure_mode=SparkFailureMode.INFERENCE_OOM,
        fallback_used=True,
    )
    assert resp.fallback_used is True


# ---------------------------------------------------------------------------
# T-08
# ---------------------------------------------------------------------------


def test_t08_prep_pipeline_marks_asset_prep_failed(tmp_path):
    """Asset marked prep_failed when SparkFailure raised; pipeline does not abort."""
    from aidm.core.prep_pipeline import PrepPipeline
    from aidm.schemas.prep_pipeline import (
        CampaignDescriptor,
        ModelLoadConfig,
        PrepPipelineConfig,
    )

    descriptor = CampaignDescriptor(
        campaign_id="c_t08",
        name="T08",
        genre="fantasy",
        story_context="Test.",
        expected_npcs=2,
        expected_scenes=0,
        expected_encounters=0,
        mood_tags=[],
    )
    config = PrepPipelineConfig(
        campaign_descriptor=descriptor,
        output_dir=str(tmp_path),
        model_sequence=[ModelLoadConfig(model_type="llm", model_id="stub")],
        enable_stub_mode=True,
    )
    pipeline = PrepPipeline(config)
    call_n = {"v": 0}
    original = pipeline._store_asset

    def patched(asset):
        call_n["v"] += 1
        if call_n["v"] == 1:
            raise SparkFailure(SparkFailureMode.INFERENCE_TIMEOUT, "timeout")
        original(asset)

    pipeline._store_asset = patched  # type: ignore

    result = pipeline.run()

    assert result.status in ("success", "partial"), f"unexpected status {result.status}"
    failed = [a for a in result.manifest.assets if a.status == "prep_failed"]
    assert len(failed) >= 1, "No asset marked prep_failed"
    assert failed[0].failure_mode == "inference_timeout"


# ---------------------------------------------------------------------------
# T-09
# ---------------------------------------------------------------------------


def test_t09_prep_pipeline_continues_after_failure(tmp_path):
    """Subsequent asset after SparkFailure is still processed (skip, not abort)."""
    from aidm.core.prep_pipeline import PrepPipeline
    from aidm.schemas.prep_pipeline import (
        CampaignDescriptor,
        ModelLoadConfig,
        PrepPipelineConfig,
    )

    descriptor = CampaignDescriptor(
        campaign_id="c_t09",
        name="T09",
        genre="fantasy",
        story_context="Test.",
        expected_npcs=3,
        expected_scenes=0,
        expected_encounters=0,
        mood_tags=[],
    )
    config = PrepPipelineConfig(
        campaign_descriptor=descriptor,
        output_dir=str(tmp_path),
        model_sequence=[ModelLoadConfig(model_type="llm", model_id="stub")],
        enable_stub_mode=True,
    )
    pipeline = PrepPipeline(config)
    original = pipeline._store_asset
    call_n = {"v": 0}

    def patched(asset):
        call_n["v"] += 1
        if call_n["v"] == 1:
            raise SparkFailure(SparkFailureMode.MODEL_LOAD_OOM, "oom")
        original(asset)

    pipeline._store_asset = patched  # type: ignore

    result = pipeline.run()

    # All 3 NPCs processed: 1 failed, 2 ok
    assert len(result.manifest.assets) == 3
    ok = [a for a in result.manifest.assets if a.status == "ok"]
    failed = [a for a in result.manifest.assets if a.status == "prep_failed"]
    assert len(ok) == 2, f"expected 2 ok, got {len(ok)}"
    assert len(failed) == 1, f"expected 1 failed, got {len(failed)}"


# ---------------------------------------------------------------------------
# T-10
# ---------------------------------------------------------------------------


def test_t10_ttft_measurement_record_has_required_keys():
    """spark_call profiler record contains ttft_s, inference_s, call_type, degraded."""
    from aidm.spark.spark_adapter import SparkAdapter, SparkRequest

    class _Stub(SparkAdapter):
        def load_model(self, m):
            raise NotImplementedError

        def unload_model(self, m):
            raise NotImplementedError

        def select_model_for_tier(self, t):
            raise NotImplementedError

        def get_fallback_model(self, m):
            raise NotImplementedError

        def check_model_compatibility(self, m):
            raise NotImplementedError

        def generate_text(
            self,
            loaded_model,
            prompt,
            temperature=0.8,
            max_tokens=150,
            stop_sequences=None,
        ):
            return "text"

    adapter = _Stub()
    records = []

    def mock_profiler(bucket, record):
        assert bucket == "spark_call"
        records.append(record)

    req = SparkRequest(prompt="hi", temperature=0.7, max_tokens=10)
    adapter.generate(req, call_type="COMBAT_NARRATION", profiler=mock_profiler)

    assert len(records) == 1
    r = records[0]
    for key in ("ttft_s", "inference_s", "call_type", "degraded"):
        assert key in r, f"profiler record missing key: {key}"
    assert r["call_type"] == "COMBAT_NARRATION"
    assert r["degraded"] is False


# ---------------------------------------------------------------------------
# T-11
# ---------------------------------------------------------------------------


def test_t11_turn_wall_clock_budget_positive_float():
    """TURN_WALL_CLOCK_BUDGET_S is a float > 0."""
    assert isinstance(TURN_WALL_CLOCK_BUDGET_S, float)
    assert TURN_WALL_CLOCK_BUDGET_S > 0.0


# ---------------------------------------------------------------------------
# T-12
# ---------------------------------------------------------------------------


def test_t12_sensor_event_emitted_on_runtime_failure():
    """SPARK_DEGRADED sensor event emitted when Spark call fails at runtime."""
    from aidm.spark.spark_adapter import SparkAdapter, SparkRequest

    class _Failing(SparkAdapter):
        def load_model(self, m):
            raise NotImplementedError

        def unload_model(self, m):
            raise NotImplementedError

        def select_model_for_tier(self, t):
            raise NotImplementedError

        def get_fallback_model(self, m):
            raise NotImplementedError

        def check_model_compatibility(self, m):
            raise NotImplementedError

        def generate_text(
            self,
            loaded_model,
            prompt,
            temperature=0.8,
            max_tokens=150,
            stop_sequences=None,
        ):
            raise SparkFailure(SparkFailureMode.FALLBACK_EXHAUSTED, "all failed")

    adapter = _Failing()
    events = []

    def sensor(event_name, **kwargs):
        events.append({"event": event_name, **kwargs})

    req = SparkRequest(prompt="story", temperature=0.8, max_tokens=100)
    resp = adapter.generate(req, call_type="COMBAT_NARRATION", sensor_fn=sensor)

    assert resp.degraded is True
    assert resp.failure_mode == SparkFailureMode.FALLBACK_EXHAUSTED
    assert resp.fallback_used is True

    assert len(events) == 1
    ev = events[0]
    assert ev["event"] == "SPARK_DEGRADED"
    assert ev["failure_mode"] == SparkFailureMode.FALLBACK_EXHAUSTED
    assert ev["call_type"] == "COMBAT_NARRATION"
