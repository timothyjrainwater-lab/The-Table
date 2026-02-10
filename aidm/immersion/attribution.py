"""M3 Attribution — Asset attribution ledger with persistence.

Provides:
- AttributionStore: Add/query/save/load attribution records

Tracks provenance and licensing for all generated and bundled assets.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from aidm.schemas.immersion import AttributionLedger, AttributionRecord


class AttributionStore:
    """Asset attribution ledger with JSON persistence.

    Tracks provenance and licensing for generated/bundled assets.
    Records are validated on add (fail-closed: asset_id and license required).
    """

    def __init__(self):
        self._records: Dict[str, AttributionRecord] = {}

    def add(self, record: AttributionRecord) -> None:
        """Add an attribution record.

        Validates that asset_id and license are present.

        Args:
            record: Attribution record to add

        Raises:
            ValueError: If record fails validation
        """
        errors = record.validate()
        if errors:
            raise ValueError(
                f"Invalid attribution record: {'; '.join(errors)}"
            )
        self._records[record.asset_id] = record

    def get_by_asset_id(self, asset_id: str) -> Optional[AttributionRecord]:
        """Look up attribution by asset ID.

        Args:
            asset_id: Asset identifier

        Returns:
            AttributionRecord if found, None otherwise
        """
        return self._records.get(asset_id)

    def list_records(self) -> List[AttributionRecord]:
        """List all attribution records.

        Returns:
            List sorted by asset_id for determinism
        """
        return sorted(self._records.values(), key=lambda r: r.asset_id)

    def save(self, path: Path) -> None:
        """Save attribution ledger to JSON file.

        Args:
            path: Output file path
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        ledger = AttributionLedger(
            schema_version="1.0",
            records=self.list_records(),
        )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(ledger.to_dict(), f, indent=2, sort_keys=True)
            f.write("\n")

    def load(self, path: Path) -> None:
        """Load attribution ledger from JSON file.

        Args:
            path: Input file path

        Raises:
            FileNotFoundError: If file does not exist
        """
        path = Path(path)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ledger = AttributionLedger.from_dict(data)

        for record in ledger.records:
            self._records[record.asset_id] = record
