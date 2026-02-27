"""ENGINE-SUN-DOMAIN Gate — WO4 BLOCKED.

Gate: ENGINE-SUN-DOMAIN
WO: WO-ENGINE-SUN-DOMAIN-001

STATUS: BLOCKED — WO4 not implemented. See finding filed below.

FINDING-ENGINE-DOMAIN-SYSTEM-MISSING-001 was filed.
Batch T closes at 3/4 WOs (MA/INA/ITN all 8/8).
"""
import pytest

pytestmark = pytest.mark.skip(
    reason="WO-ENGINE-SUN-DOMAIN-001 BLOCKED: FINDING-ENGINE-DOMAIN-SYSTEM-MISSING-001 — "
           "no domain storage system (EF.DOMAINS missing, EF.GREATER_TURNING_USES_REMAINING missing). "
           "Sun domain infrastructure must be built before this WO can proceed."
)


def test_sd001_placeholder():
    """SD-001 through SD-008 skipped — WO4 BLOCKED."""
    pass
