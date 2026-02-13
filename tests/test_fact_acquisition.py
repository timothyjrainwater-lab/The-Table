"""Tests for JIT Fact Acquisition Protocol.

WO-008: JIT Fact Acquisition Protocol
Tests the full acquisition cycle from request to storage.
"""

import pytest
from typing import Optional

from aidm.schemas.position import Position
from aidm.core.lens_index import LensIndex, SourceTier, LensFact
from aidm.core.fact_acquisition import (
    FactRequest,
    FactResponse,
    ValidationResult,
    AcquisitionResult,
    FactAcquisitionManager,
    CREATURE_REQUIRED,
    OBJECT_REQUIRED,
    TERRAIN_REQUIRED,
    ALLOWED_DEFAULTS,
    FORBIDDEN_DEFAULTS,
    VALID_SIZE_CATEGORIES,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def lens():
    """Create a fresh LensIndex."""
    return LensIndex()


@pytest.fixture
def lens_with_creature(lens):
    """Create a LensIndex with a creature registered."""
    lens.register_entity("goblin_01", "creature", turn=0)
    return lens


@pytest.fixture
def lens_with_object(lens):
    """Create a LensIndex with an object registered."""
    lens.register_entity("door_01", "object", turn=0)
    return lens


@pytest.fixture
def lens_with_terrain(lens):
    """Create a LensIndex with a terrain registered."""
    lens.register_entity("terrain_01", "terrain", turn=0)
    return lens


@pytest.fixture
def manager_with_fixed_uuid(lens_with_creature):
    """Create a manager with deterministic UUID generation."""
    uuid_counter = [0]

    def fixed_uuid():
        uuid_counter[0] += 1
        return f"test-uuid-{uuid_counter[0]:04d}"

    return FactAcquisitionManager(lens_with_creature, uuid_generator=fixed_uuid)


@pytest.fixture
def mock_spark_success():
    """Mock Spark callback that returns successful response."""
    def callback(request: FactRequest) -> FactResponse:
        facts = {
            "size": "medium",
            "position": {"x": 5, "y": 10},
            "hit_points": 25,
            "armor_class": 15,
        }
        return FactResponse(
            request_id=request.request_id,
            entity_id=request.entity_id,
            facts=facts,
            source="spark_v1",
            valid=True,
        )
    return callback


@pytest.fixture
def mock_spark_partial():
    """Mock Spark callback that returns partial response (missing required)."""
    def callback(request: FactRequest) -> FactResponse:
        # Missing hit_points and armor_class
        facts = {
            "size": "small",
            "position": {"x": 3, "y": 7},
        }
        return FactResponse(
            request_id=request.request_id,
            entity_id=request.entity_id,
            facts=facts,
            source="spark_v1",
            valid=True,
        )
    return callback


@pytest.fixture
def mock_spark_timeout():
    """Mock Spark callback that returns None (timeout)."""
    def callback(request: FactRequest) -> Optional[FactResponse]:
        return None
    return callback


@pytest.fixture
def mock_spark_error():
    """Mock Spark callback that raises an exception."""
    def callback(request: FactRequest) -> FactResponse:
        raise RuntimeError("Spark connection failed")
    return callback


# ==============================================================================
# TESTS: FactRequest Schema
# ==============================================================================

class TestFactRequestSchema:
    """Tests for FactRequest dataclass."""

    def test_create_request(self):
        """Create a FactRequest with all fields."""
        request = FactRequest(
            request_id="req-001",
            entity_id="goblin_01",
            required_attributes=["size", "position"],
            context="combat encounter",
            timeout_ms=3000,
        )
        assert request.request_id == "req-001"
        assert request.entity_id == "goblin_01"
        assert request.required_attributes == ("size", "position")
        assert request.context == "combat encounter"
        assert request.timeout_ms == 3000

    def test_request_default_timeout(self):
        """FactRequest has default timeout of 5000ms."""
        request = FactRequest(
            request_id="req-002",
            entity_id="goblin_01",
            required_attributes=["size"],
        )
        assert request.timeout_ms == 5000

    def test_request_is_frozen(self):
        """FactRequest is immutable."""
        request = FactRequest(
            request_id="req-003",
            entity_id="goblin_01",
            required_attributes=["size"],
        )
        with pytest.raises(AttributeError):
            request.entity_id = "orc_01"

    def test_request_to_dict(self):
        """FactRequest serializes to dict."""
        request = FactRequest(
            request_id="req-004",
            entity_id="goblin_01",
            required_attributes=["size", "position"],
            context="battle",
            timeout_ms=4000,
        )
        d = request.to_dict()
        assert d["request_id"] == "req-004"
        assert d["entity_id"] == "goblin_01"
        assert d["required_attributes"] == ["size", "position"]
        assert d["context"] == "battle"
        assert d["timeout_ms"] == 4000

    def test_request_from_dict(self):
        """FactRequest deserializes from dict."""
        data = {
            "request_id": "req-005",
            "entity_id": "orc_01",
            "required_attributes": ["hit_points"],
            "context": None,
            "timeout_ms": 6000,
        }
        request = FactRequest.from_dict(data)
        assert request.request_id == "req-005"
        assert request.entity_id == "orc_01"
        assert request.required_attributes == ("hit_points",)
        assert request.timeout_ms == 6000


# ==============================================================================
# TESTS: FactResponse Schema
# ==============================================================================

class TestFactResponseSchema:
    """Tests for FactResponse dataclass."""

    def test_create_response(self):
        """Create a FactResponse with all fields."""
        response = FactResponse(
            request_id="req-001",
            entity_id="goblin_01",
            facts={"size": "medium", "hit_points": 25},
            source="spark_v1",
            valid=True,
        )
        assert response.request_id == "req-001"
        assert response.entity_id == "goblin_01"
        assert response.facts == {"size": "medium", "hit_points": 25}
        assert response.source == "spark_v1"
        assert response.valid is True
        assert response.error is None

    def test_response_with_error(self):
        """Create a FactResponse with error."""
        response = FactResponse(
            request_id="req-002",
            entity_id="goblin_01",
            facts={},
            source="spark_v1",
            valid=False,
            error="Entity not found in world model",
        )
        assert response.valid is False
        assert response.error == "Entity not found in world model"

    def test_response_is_frozen(self):
        """FactResponse is immutable."""
        response = FactResponse(
            request_id="req-003",
            entity_id="goblin_01",
            facts={"size": "small"},
            source="spark_v1",
            valid=True,
        )
        with pytest.raises(AttributeError):
            response.valid = False

    def test_response_to_dict(self):
        """FactResponse serializes to dict."""
        response = FactResponse(
            request_id="req-004",
            entity_id="goblin_01",
            facts={"size": "large", "armor_class": 18},
            source="spark_v2",
            valid=True,
        )
        d = response.to_dict()
        assert d["request_id"] == "req-004"
        assert d["facts"] == {"size": "large", "armor_class": 18}
        assert d["source"] == "spark_v2"

    def test_response_from_dict(self):
        """FactResponse deserializes from dict."""
        data = {
            "request_id": "req-005",
            "entity_id": "orc_01",
            "facts": {"hit_points": 40},
            "source": "spark_v1",
            "valid": True,
            "error": None,
        }
        response = FactResponse.from_dict(data)
        assert response.request_id == "req-005"
        assert response.facts == {"hit_points": 40}


# ==============================================================================
# TESTS: ValidationResult Schema
# ==============================================================================

class TestValidationResultSchema:
    """Tests for ValidationResult dataclass."""

    def test_valid_result(self):
        """Create a valid ValidationResult."""
        result = ValidationResult(valid=True, errors=[], warnings=[])
        assert result.valid is True
        assert result.errors == ()
        assert result.warnings == ()

    def test_invalid_result_with_errors(self):
        """Create an invalid ValidationResult with errors."""
        result = ValidationResult(
            valid=False,
            errors=["Missing size", "Invalid position"],
            warnings=["Unknown attribute 'foo'"],
        )
        assert result.valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1


# ==============================================================================
# TESTS: AcquisitionResult Schema
# ==============================================================================

class TestAcquisitionResultSchema:
    """Tests for AcquisitionResult dataclass."""

    def test_successful_result(self):
        """Create a successful AcquisitionResult."""
        result = AcquisitionResult(
            success=True,
            entity_id="goblin_01",
            acquired_facts={"size": "medium", "hit_points": 25},
            defaulted_facts={"hardness": 5},
            errors=[],
        )
        assert result.success is True
        assert result.acquired_facts == {"size": "medium", "hit_points": 25}
        assert result.defaulted_facts == {"hardness": 5}

    def test_failed_result_with_errors(self):
        """Create a failed AcquisitionResult."""
        result = AcquisitionResult(
            success=False,
            entity_id="goblin_01",
            errors=["Spark timeout", "Missing required attribute"],
        )
        assert result.success is False
        assert len(result.errors) == 2


# ==============================================================================
# TESTS: Request Generation
# ==============================================================================

class TestRequestGeneration:
    """Tests for create_request method."""

    def test_create_request_generates_valid_request(self, manager_with_fixed_uuid):
        """create_request produces a valid FactRequest."""
        request = manager_with_fixed_uuid.create_request(
            entity_id="goblin_01",
            entity_class="creature",
            missing_attrs=["size", "hit_points"],
        )
        assert isinstance(request, FactRequest)
        assert request.entity_id == "goblin_01"
        assert request.required_attributes == ("size", "hit_points")

    def test_request_id_is_unique(self, manager_with_fixed_uuid):
        """Each request gets a unique ID."""
        req1 = manager_with_fixed_uuid.create_request("e1", "creature", ["size"])
        req2 = manager_with_fixed_uuid.create_request("e2", "creature", ["size"])
        assert req1.request_id != req2.request_id

    def test_required_attributes_populated(self, manager_with_fixed_uuid):
        """Required attributes are correctly populated."""
        request = manager_with_fixed_uuid.create_request(
            entity_id="goblin_01",
            entity_class="creature",
            missing_attrs=CREATURE_REQUIRED,
        )
        assert set(request.required_attributes) == set(CREATURE_REQUIRED)


# ==============================================================================
# TESTS: Response Validation
# ==============================================================================

class TestResponseValidation:
    """Tests for validate_response method."""

    def test_valid_response_passes(self, manager_with_fixed_uuid, mock_spark_success):
        """Valid response passes validation."""
        request = manager_with_fixed_uuid.create_request(
            "goblin_01", "creature", CREATURE_REQUIRED
        )
        response = mock_spark_success(request)
        result = manager_with_fixed_uuid.validate_response(request, response)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_mismatched_request_id_fails(self, manager_with_fixed_uuid):
        """Mismatched request_id fails validation."""
        request = manager_with_fixed_uuid.create_request(
            "goblin_01", "creature", ["size"]
        )
        response = FactResponse(
            request_id="wrong-id",
            entity_id="goblin_01",
            facts={"size": "medium"},
            source="spark_v1",
            valid=True,
        )
        result = manager_with_fixed_uuid.validate_response(request, response)
        assert result.valid is False
        assert any("mismatch" in e.lower() for e in result.errors)

    def test_missing_required_attribute_fails(self, manager_with_fixed_uuid):
        """Missing FORBIDDEN_DEFAULT attribute fails validation."""
        request = manager_with_fixed_uuid.create_request(
            "goblin_01", "creature", ["size", "hit_points"]  # Both forbidden
        )
        response = FactResponse(
            request_id=request.request_id,
            entity_id="goblin_01",
            facts={"size": "medium"},  # Missing hit_points
            source="spark_v1",
            valid=True,
        )
        result = manager_with_fixed_uuid.validate_response(request, response)
        assert result.valid is False
        assert any("hit_points" in e for e in result.errors)

    def test_invalid_type_fails(self, manager_with_fixed_uuid):
        """Invalid value type fails validation."""
        request = manager_with_fixed_uuid.create_request(
            "goblin_01", "creature", ["size"]
        )
        response = FactResponse(
            request_id=request.request_id,
            entity_id="goblin_01",
            facts={"size": 123},  # Should be string
            source="spark_v1",
            valid=True,
        )
        result = manager_with_fixed_uuid.validate_response(request, response)
        assert result.valid is False
        assert any("size" in e.lower() for e in result.errors)

    def test_invalid_size_category_fails(self, manager_with_fixed_uuid):
        """Invalid size category fails validation."""
        request = manager_with_fixed_uuid.create_request(
            "goblin_01", "creature", ["size"]
        )
        response = FactResponse(
            request_id=request.request_id,
            entity_id="goblin_01",
            facts={"size": "gigantic"},  # Not a valid category
            source="spark_v1",
            valid=True,
        )
        result = manager_with_fixed_uuid.validate_response(request, response)
        assert result.valid is False
        assert any("size category" in e.lower() for e in result.errors)

    def test_invalid_position_format_fails(self, manager_with_fixed_uuid):
        """Invalid position format fails validation."""
        request = manager_with_fixed_uuid.create_request(
            "goblin_01", "creature", ["position"]
        )
        # Missing y key
        response = FactResponse(
            request_id=request.request_id,
            entity_id="goblin_01",
            facts={"position": {"x": 5}},
            source="spark_v1",
            valid=True,
        )
        result = manager_with_fixed_uuid.validate_response(request, response)
        assert result.valid is False
        assert any("position" in e.lower() for e in result.errors)

    def test_negative_hit_points_fails(self, manager_with_fixed_uuid):
        """Non-positive hit_points fails validation."""
        request = manager_with_fixed_uuid.create_request(
            "goblin_01", "creature", ["hit_points"]
        )
        response = FactResponse(
            request_id=request.request_id,
            entity_id="goblin_01",
            facts={"hit_points": 0},
            source="spark_v1",
            valid=True,
        )
        result = manager_with_fixed_uuid.validate_response(request, response)
        assert result.valid is False
        assert any("positive" in e.lower() for e in result.errors)

    def test_extra_attributes_accepted_with_warning(self, manager_with_fixed_uuid):
        """Unknown attributes are accepted but generate warnings."""
        request = manager_with_fixed_uuid.create_request(
            "goblin_01", "creature", ["size"]
        )
        response = FactResponse(
            request_id=request.request_id,
            entity_id="goblin_01",
            facts={"size": "medium", "favorite_color": "green"},
            source="spark_v1",
            valid=True,
        )
        result = manager_with_fixed_uuid.validate_response(request, response)
        assert result.valid is True  # Extra attrs don't fail validation
        assert len(result.warnings) > 0
        assert any("favorite_color" in w for w in result.warnings)


# ==============================================================================
# TESTS: Apply Response
# ==============================================================================

class TestApplyResponse:
    """Tests for apply_response method."""

    def test_facts_stored_in_lens(self, lens_with_creature, mock_spark_success):
        """Applied facts are stored in LensIndex."""
        manager = FactAcquisitionManager(lens_with_creature)
        request = manager.create_request("goblin_01", "creature", CREATURE_REQUIRED)
        response = mock_spark_success(request)

        manager.apply_response(response, turn=1)

        # Check facts were stored
        size_fact = lens_with_creature.get_fact("goblin_01", "size")
        assert size_fact is not None
        assert size_fact.value == "medium"

        hp_fact = lens_with_creature.get_fact("goblin_01", "hit_points")
        assert hp_fact is not None
        assert hp_fact.value == 25

    def test_source_tier_is_spark(self, lens_with_creature, mock_spark_success):
        """Applied facts have SPARK source tier."""
        manager = FactAcquisitionManager(lens_with_creature)
        request = manager.create_request("goblin_01", "creature", CREATURE_REQUIRED)
        response = mock_spark_success(request)

        manager.apply_response(response, turn=1)

        size_fact = lens_with_creature.get_fact("goblin_01", "size")
        assert size_fact.source_tier == SourceTier.SPARK

    def test_provenance_tracked(self, lens_with_creature, mock_spark_success):
        """Applied facts have provenance_id linking to request."""
        manager = FactAcquisitionManager(lens_with_creature)
        request = manager.create_request("goblin_01", "creature", CREATURE_REQUIRED)
        response = mock_spark_success(request)

        manager.apply_response(response, turn=1)

        size_fact = lens_with_creature.get_fact("goblin_01", "size")
        assert size_fact.provenance_id == request.request_id

    def test_invalid_response_not_applied(self, lens_with_creature):
        """Invalid response is not applied."""
        manager = FactAcquisitionManager(lens_with_creature)

        response = FactResponse(
            request_id="req-001",
            entity_id="goblin_01",
            facts={"size": "medium"},
            source="spark_v1",
            valid=False,  # Invalid!
            error="Some error",
        )

        result = manager.apply_response(response, turn=1)
        assert result is False

        # Fact should not be stored
        size_fact = lens_with_creature.get_fact("goblin_01", "size")
        assert size_fact is None


# ==============================================================================
# TESTS: Default Application
# ==============================================================================

class TestDefaultApplication:
    """Tests for apply_defaults method."""

    def test_allowed_defaults_applied(self, lens_with_object):
        """ALLOWED_DEFAULTS are applied for missing attributes."""
        manager = FactAcquisitionManager(lens_with_object)

        defaulted = manager.apply_defaults("door_01", "object", turn=0)

        # Check allowed defaults were applied
        assert "material" in defaulted
        assert defaulted["material"] == "wood"
        assert "hardness" in defaulted
        assert defaulted["hardness"] == 5

    def test_forbidden_defaults_not_applied(self, lens_with_creature):
        """FORBIDDEN_DEFAULTS are never applied."""
        manager = FactAcquisitionManager(lens_with_creature)

        defaulted = manager.apply_defaults("goblin_01", "creature", turn=0)

        # Forbidden defaults should not be in result
        assert "size" not in defaulted
        assert "position" not in defaulted
        assert "hit_points" not in defaulted
        assert "armor_class" not in defaulted

    def test_defaults_not_applied_if_fact_exists(self, lens_with_object):
        """Defaults don't overwrite existing facts."""
        manager = FactAcquisitionManager(lens_with_object)

        # Set material manually
        lens_with_object.set_fact(
            "door_01", "material", "iron",
            SourceTier.SPARK, turn=0
        )

        defaulted = manager.apply_defaults("door_01", "object", turn=1)

        # Material should not be defaulted (already exists)
        assert "material" not in defaulted

        # Verify original value preserved
        mat_fact = lens_with_object.get_fact("door_01", "material")
        assert mat_fact.value == "iron"

    def test_defaults_have_default_tier(self, lens_with_object):
        """Default facts have DEFAULT source tier."""
        manager = FactAcquisitionManager(lens_with_object)

        manager.apply_defaults("door_01", "object", turn=0)

        mat_fact = lens_with_object.get_fact("door_01", "material")
        assert mat_fact.source_tier == SourceTier.DEFAULT

    def test_terrain_defaults(self, lens_with_terrain):
        """Terrain entity gets correct defaults."""
        manager = FactAcquisitionManager(lens_with_terrain)

        defaulted = manager.apply_defaults("terrain_01", "terrain", turn=0)

        assert "elevation" in defaulted
        assert defaulted["elevation"] == 0
        assert "movement_cost" in defaulted
        assert defaulted["movement_cost"] == 1


# ==============================================================================
# TESTS: Full Acquisition Cycle
# ==============================================================================

class TestFullAcquisitionCycle:
    """Tests for acquire_facts method."""

    def test_successful_acquisition_stores_all_facts(
        self, lens_with_creature, mock_spark_success
    ):
        """Successful acquisition stores all facts from Spark."""
        manager = FactAcquisitionManager(lens_with_creature)

        result = manager.acquire_facts(
            entity_id="goblin_01",
            entity_class="creature",
            required_attrs=CREATURE_REQUIRED,
            spark_callback=mock_spark_success,
            turn=1,
        )

        assert result.success is True
        assert "size" in result.acquired_facts
        assert "hit_points" in result.acquired_facts
        assert len(result.errors) == 0

    def test_partial_failure_applies_defaults(
        self, lens_with_creature, mock_spark_partial
    ):
        """Partial response failure applies defaults for allowed attrs."""
        manager = FactAcquisitionManager(lens_with_creature)

        result = manager.acquire_facts(
            entity_id="goblin_01",
            entity_class="creature",
            required_attrs=CREATURE_REQUIRED,
            spark_callback=mock_spark_partial,
            turn=1,
        )

        # Should fail because missing required forbidden attrs
        assert result.success is False
        # But defaults should be applied
        # (creature has no ALLOWED_DEFAULTS, so defaulted_facts may be empty)

    def test_complete_failure_returns_error(
        self, lens_with_creature, mock_spark_timeout
    ):
        """Complete timeout returns error with defaults."""
        manager = FactAcquisitionManager(lens_with_creature)

        result = manager.acquire_facts(
            entity_id="goblin_01",
            entity_class="creature",
            required_attrs=CREATURE_REQUIRED,
            spark_callback=mock_spark_timeout,
            turn=1,
        )

        assert result.success is False
        assert len(result.errors) > 0
        assert any("timeout" in e.lower() or "none" in e.lower() for e in result.errors)

    def test_exception_handled_gracefully(
        self, lens_with_creature, mock_spark_error
    ):
        """Spark callback exception is handled gracefully."""
        manager = FactAcquisitionManager(lens_with_creature)

        result = manager.acquire_facts(
            entity_id="goblin_01",
            entity_class="creature",
            required_attrs=CREATURE_REQUIRED,
            spark_callback=mock_spark_error,
            turn=1,
        )

        assert result.success is False
        assert len(result.errors) > 0

    def test_object_acquisition_with_defaults(self, lens_with_object, mock_spark_timeout):
        """Object acquisition applies material/hardness defaults on timeout."""
        manager = FactAcquisitionManager(lens_with_object)

        result = manager.acquire_facts(
            entity_id="door_01",
            entity_class="object",
            required_attrs=OBJECT_REQUIRED,
            spark_callback=mock_spark_timeout,
            turn=1,
        )

        assert result.success is False
        # Object should get material and hardness defaults
        assert "material" in result.defaulted_facts
        assert "hardness" in result.defaulted_facts


# ==============================================================================
# TESTS: get_or_acquire
# ==============================================================================

class TestGetOrAcquire:
    """Tests for get_or_acquire method."""

    def test_returns_existing_fact(self, lens_with_creature):
        """Returns existing fact without calling Spark."""
        lens_with_creature.set_fact(
            "goblin_01", "size", "small",
            SourceTier.BOX, turn=0
        )

        call_count = [0]

        def tracking_callback(request):
            call_count[0] += 1
            return None

        manager = FactAcquisitionManager(lens_with_creature)
        value = manager.get_or_acquire(
            "goblin_01", "size", "creature",
            tracking_callback, turn=1
        )

        assert value == "small"
        assert call_count[0] == 0  # Spark not called

    def test_acquires_if_missing(self, lens_with_creature, mock_spark_success):
        """Acquires from Spark if fact is missing."""
        manager = FactAcquisitionManager(lens_with_creature)

        value = manager.get_or_acquire(
            "goblin_01", "size", "creature",
            mock_spark_success, turn=1
        )

        assert value == "medium"

    def test_returns_none_on_failure(self, lens_with_creature, mock_spark_timeout):
        """Returns None when acquisition completely fails."""
        manager = FactAcquisitionManager(lens_with_creature)

        value = manager.get_or_acquire(
            "goblin_01", "size", "creature",  # size is forbidden default
            mock_spark_timeout, turn=1
        )

        assert value is None

    def test_returns_default_on_allowed(self, lens_with_object, mock_spark_timeout):
        """Returns default value for allowed defaults on timeout."""
        manager = FactAcquisitionManager(lens_with_object)

        value = manager.get_or_acquire(
            "door_01", "material", "object",
            mock_spark_timeout, turn=1
        )

        assert value == "wood"  # Default value


# ==============================================================================
# TESTS: Timeout Handling
# ==============================================================================

class TestTimeoutHandling:
    """Tests for timeout and failure scenarios."""

    def test_timeout_triggers_default_fallback(self, lens_with_object, mock_spark_timeout):
        """Timeout causes defaults to be applied."""
        manager = FactAcquisitionManager(lens_with_object)

        result = manager.acquire_facts(
            entity_id="door_01",
            entity_class="object",
            required_attrs=["material", "hardness"],
            spark_callback=mock_spark_timeout,
            turn=1,
        )

        assert result.success is False
        assert "material" in result.defaulted_facts
        assert "hardness" in result.defaulted_facts

    def test_error_logged_on_timeout(self, lens_with_creature, mock_spark_timeout, caplog):
        """Timeout is logged as warning."""
        import logging
        caplog.set_level(logging.WARNING)

        manager = FactAcquisitionManager(lens_with_creature)

        manager.acquire_facts(
            entity_id="goblin_01",
            entity_class="creature",
            required_attrs=["size"],
            spark_callback=mock_spark_timeout,
            turn=1,
        )

        # Check that timeout was logged
        assert any("timeout" in record.message.lower() for record in caplog.records)


# ==============================================================================
# TESTS: Edge Cases
# ==============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_unknown_entity_class(self, lens_with_creature):
        """Unknown entity class returns error."""
        manager = FactAcquisitionManager(lens_with_creature)

        result = manager.acquire_facts(
            entity_id="goblin_01",
            entity_class="unknown_type",
            required_attrs=["size"],
            spark_callback=lambda r: None,
            turn=1,
        )

        assert result.success is False
        assert any("unknown" in e.lower() for e in result.errors)

    def test_empty_required_attrs(self, lens_with_creature):
        """Empty required_attrs succeeds immediately."""
        call_count = [0]

        def tracking_callback(request):
            call_count[0] += 1
            return None

        manager = FactAcquisitionManager(lens_with_creature)
        result = manager.acquire_facts(
            entity_id="goblin_01",
            entity_class="creature",
            required_attrs=[],
            spark_callback=tracking_callback,
            turn=1,
        )

        assert result.success is True
        assert call_count[0] == 0  # Spark not called

    def test_spark_returns_extra_data(self, lens_with_creature):
        """Extra data from Spark is accepted and stored."""
        def callback_with_extra(request):
            return FactResponse(
                request_id=request.request_id,
                entity_id=request.entity_id,
                facts={
                    "size": "medium",
                    "description": "A sneaky goblin",  # Extra
                },
                source="spark_v1",
                valid=True,
            )

        manager = FactAcquisitionManager(lens_with_creature)
        result = manager.acquire_facts(
            entity_id="goblin_01",
            entity_class="creature",
            required_attrs=["size"],
            spark_callback=callback_with_extra,
            turn=1,
        )

        assert result.success is True
        assert "description" in result.acquired_facts

    def test_spark_returns_wrong_types(self, lens_with_creature):
        """Wrong types from Spark cause validation failure."""
        def bad_types_callback(request):
            return FactResponse(
                request_id=request.request_id,
                entity_id=request.entity_id,
                facts={
                    "size": 42,  # Should be string
                    "hit_points": "lots",  # Should be int
                },
                source="spark_v1",
                valid=True,
            )

        manager = FactAcquisitionManager(lens_with_creature)
        result = manager.acquire_facts(
            entity_id="goblin_01",
            entity_class="creature",
            required_attrs=["size", "hit_points"],
            spark_callback=bad_types_callback,
            turn=1,
        )

        assert result.success is False
        assert len(result.errors) >= 2  # Both type errors

    def test_entity_not_in_lens(self, lens):
        """Applying response for unknown entity fails gracefully."""
        manager = FactAcquisitionManager(lens)

        response = FactResponse(
            request_id="req-001",
            entity_id="nonexistent",
            facts={"size": "medium"},
            source="spark_v1",
            valid=True,
        )

        result = manager.apply_response(response, turn=1)
        assert result is False


# ==============================================================================
# TESTS: Utility Methods
# ==============================================================================

class TestUtilityMethods:
    """Tests for utility methods."""

    def test_get_required_attributes_creature(self, lens_with_creature):
        """get_required_attributes returns creature requirements."""
        manager = FactAcquisitionManager(lens_with_creature)
        attrs = manager.get_required_attributes("creature")
        assert set(attrs) == set(CREATURE_REQUIRED)

    def test_get_required_attributes_object(self, lens_with_object):
        """get_required_attributes returns object requirements."""
        manager = FactAcquisitionManager(lens_with_object)
        attrs = manager.get_required_attributes("object")
        assert set(attrs) == set(OBJECT_REQUIRED)

    def test_get_required_attributes_terrain(self, lens_with_terrain):
        """get_required_attributes returns terrain requirements."""
        manager = FactAcquisitionManager(lens_with_terrain)
        attrs = manager.get_required_attributes("terrain")
        assert set(attrs) == set(TERRAIN_REQUIRED)

    def test_get_required_attributes_unknown(self, lens):
        """get_required_attributes returns empty for unknown class."""
        manager = FactAcquisitionManager(lens)
        attrs = manager.get_required_attributes("unknown")
        assert attrs == []

    def test_get_missing_attributes(self, lens_with_creature):
        """get_missing_attributes identifies unfilled requirements."""
        manager = FactAcquisitionManager(lens_with_creature)

        # All attributes missing initially
        missing = manager.get_missing_attributes("goblin_01", "creature")
        assert set(missing) == set(CREATURE_REQUIRED)

        # Set some facts
        lens_with_creature.set_fact(
            "goblin_01", "size", "medium", SourceTier.SPARK, turn=0
        )
        lens_with_creature.set_fact(
            "goblin_01", "hit_points", 25, SourceTier.SPARK, turn=0
        )

        missing = manager.get_missing_attributes("goblin_01", "creature")
        assert "size" not in missing
        assert "hit_points" not in missing
        assert "position" in missing
        assert "armor_class" in missing


# ==============================================================================
# TESTS: Constants Validation
# ==============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_forbidden_defaults_subset_of_required(self):
        """FORBIDDEN_DEFAULTS are subsets of required attrs."""
        all_required = set(CREATURE_REQUIRED + OBJECT_REQUIRED + TERRAIN_REQUIRED)
        assert FORBIDDEN_DEFAULTS <= all_required

    def test_allowed_defaults_not_forbidden(self):
        """ALLOWED_DEFAULTS and FORBIDDEN_DEFAULTS are disjoint."""
        allowed_keys = set(ALLOWED_DEFAULTS.keys())
        assert allowed_keys.isdisjoint(FORBIDDEN_DEFAULTS)

    def test_valid_size_categories(self):
        """VALID_SIZE_CATEGORIES contains D&D 3.5e sizes."""
        expected = {
            "fine", "diminutive", "tiny", "small", "medium",
            "large", "huge", "gargantuan", "colossal"
        }
        assert VALID_SIZE_CATEGORIES == expected
