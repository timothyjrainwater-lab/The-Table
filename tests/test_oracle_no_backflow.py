"""No-backflow structural gate — A-NO-BACKFLOW.

Proves Oracle stores have no write path from Spark, Immersion, or Voice
layers.  Scans all files in ``aidm/oracle/`` for imports from forbidden
packages.

Authority: WO-ORACLE-01 Change 6, GT v12 A-NO-BACKFLOW.
"""
from __future__ import annotations

import re
from pathlib import Path


ORACLE_DIR = Path(__file__).resolve().parent.parent / "aidm" / "oracle"

# Forbidden import sources — any import from these packages in oracle/ is a violation.
FORBIDDEN_PATTERNS = [
    re.compile(r"^\s*(?:from|import)\s+aidm\.spark\b"),
    re.compile(r"^\s*(?:from|import)\s+aidm\.immersion\b"),
    re.compile(r"^\s*(?:from|import)\s+aidm\.voice\b"),
]


def test_oracle_stores_no_spark_import():
    """Scan all files in aidm/oracle/ for imports from spark/immersion/voice.

    Assert zero matches.  This is a static gate for A-NO-BACKFLOW.
    """
    violations = []

    for py_file in sorted(ORACLE_DIR.glob("*.py")):
        with open(py_file, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                for pattern in FORBIDDEN_PATTERNS:
                    if pattern.search(line):
                        violations.append(
                            f"{py_file.name}:{lineno}: {line.rstrip()}"
                        )

    assert not violations, (
        f"A-NO-BACKFLOW violation: Oracle stores must not import from "
        f"spark/immersion/voice.\n"
        + "\n".join(violations)
    )
