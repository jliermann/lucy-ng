"""Statistical detector for structural constraints from NMR shifts."""

from __future__ import annotations

from pathlib import Path

from lucy_ng.database import DatabaseManager
from lucy_ng.detection.models import HybridisationDistribution, HybridisationResult


class StatisticalDetector:
    """Detector for statistical analysis of NMR shifts.

    Queries the HOSE statistics database to determine structural
    constraints like hybridisation state based on chemical shift ranges.

    Usage:
        with StatisticalDetector("database.db") as detector:
            result = detector.detect_hybridisation(130.5)
            print(result.summary())
    """

    def __init__(self, db_path: Path | str):
        """Initialize detector with database path.

        Args:
            db_path: Path to SQLite database with HOSE statistics
        """
        self.db_path = Path(db_path)
        self._db = DatabaseManager(self.db_path)
        self._db._connect()

    def __enter__(self) -> StatisticalDetector:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close database connection."""
        if self._db:
            self._db.close()

    def detect_hybridisation(
        self,
        shift_ppm: float,
        radius: int = 3,
        window_ppm: float = 2.0,
        threshold: float = 0.01,
    ) -> HybridisationResult:
        """Detect hybridisation state from chemical shift.

        Queries all HOSE codes at the given radius whose mean shift falls
        within [shift_ppm - window_ppm, shift_ppm + window_ppm], aggregates
        their hybridisation counts, and computes frequency distributions.

        States below the threshold are filtered out (set to 0.0).

        Args:
            shift_ppm: Target chemical shift in ppm
            radius: HOSE code radius (1-6, default: 3)
            window_ppm: Window size in ppm (default: 2.0)
            threshold: Minimum frequency to include (default: 0.01 = 1%)

        Returns:
            HybridisationResult with distribution and metadata
        """
        # Query database for matching HOSE stats
        records = self._db.get_hose_stats_by_shift_window(
            shift_ppm, radius, window_ppm
        )

        # Aggregate hybridisation counts
        sp3_total = sum(r.sp3_count for r in records)
        sp2_total = sum(r.sp2_count for r in records)
        sp1_total = sum(r.sp1_count for r in records)
        total_observations = sp3_total + sp2_total + sp1_total
        unique_hose_codes = len(records)

        # Check if we have data
        if total_observations == 0:
            return HybridisationResult(
                shift_ppm=shift_ppm,
                window_ppm=window_ppm,
                radius=radius,
                threshold=threshold,
                distribution=HybridisationDistribution(),
                total_observations=0,
                unique_hose_codes=unique_hose_codes,
                has_data=False,
                warning=(
                    "No hybridisation data found. "
                    "Database may need regeneration with v4 schema."
                ),
            )

        # Compute raw frequencies
        sp3_freq = sp3_total / total_observations
        sp2_freq = sp2_total / total_observations
        sp1_freq = sp1_total / total_observations

        # Apply threshold filter
        if sp3_freq < threshold:
            sp3_freq = 0.0
        if sp2_freq < threshold:
            sp2_freq = 0.0
        if sp1_freq < threshold:
            sp1_freq = 0.0

        # Normalize remaining frequencies to sum to 1.0
        remaining_total = sp3_freq + sp2_freq + sp1_freq
        if remaining_total > 0:
            sp3_freq /= remaining_total
            sp2_freq /= remaining_total
            sp1_freq /= remaining_total

        distribution = HybridisationDistribution(
            sp3=sp3_freq,
            sp2=sp2_freq,
            sp1=sp1_freq,
        )

        return HybridisationResult(
            shift_ppm=shift_ppm,
            window_ppm=window_ppm,
            radius=radius,
            threshold=threshold,
            distribution=distribution,
            total_observations=total_observations,
            unique_hose_codes=unique_hose_codes,
            has_data=True,
        )
