"""Pydantic models for statistical detection results."""

from __future__ import annotations

from pydantic import BaseModel


class HybridisationDistribution(BaseModel):
    """Distribution of hybridisation states for a carbon shift.

    Frequencies sum to ~1.0 (or 0.0 if no data).
    """

    sp3: float = 0.0  # Frequency 0.0-1.0
    sp2: float = 0.0
    sp1: float = 0.0

    @property
    def dominant(self) -> str:
        """Return the hybridisation state with highest frequency.

        Returns:
            "sp3", "sp2", "sp1", or "unknown" if all zero
        """
        if self.sp3 == 0.0 and self.sp2 == 0.0 and self.sp1 == 0.0:
            return "unknown"

        max_freq = max(self.sp3, self.sp2, self.sp1)
        if self.sp3 == max_freq:
            return "sp3"
        elif self.sp2 == max_freq:
            return "sp2"
        else:
            return "sp1"

    @property
    def is_definitive(self) -> bool:
        """Return True if one state has >95% frequency.

        A definitive result strongly suggests the hybridisation state
        with high confidence.
        """
        return max(self.sp3, self.sp2, self.sp1) > 0.95


class HybridisationResult(BaseModel):
    """Result of hybridisation detection query.

    Contains both the frequency distribution and metadata about
    the query parameters and data coverage.
    """

    shift_ppm: float  # Queried shift
    window_ppm: float  # Query window used
    radius: int  # HOSE radius used
    threshold: float  # Minimum frequency threshold used
    distribution: HybridisationDistribution  # Filtered distribution
    total_observations: int  # Total sp3+sp2+sp1 count across all matching HOSE codes
    unique_hose_codes: int  # Number of HOSE codes that contributed
    has_data: bool  # False if no matching HOSE codes or all counts are 0
    warning: str | None = None  # Warning message

    def summary(self) -> str:
        """Generate human-readable summary of detection result.

        Returns:
            Multi-line text summary
        """
        lines = []

        # Header
        lines.append(
            f"Hybridisation Detection: {self.shift_ppm} ppm "
            f"(window +/- {self.window_ppm} ppm, radius {self.radius})"
        )

        if not self.has_data:
            lines.append("No data available")
            if self.warning:
                lines.append(f"Warning: {self.warning}")
            return "\n".join(lines)

        # Distribution line
        dist_parts = []
        excluded_parts = []

        for state, freq in [("sp3", self.distribution.sp3),
                           ("sp2", self.distribution.sp2),
                           ("sp1", self.distribution.sp1)]:
            if freq > 0.0:
                dist_parts.append(f"{state}={freq*100:.1f}%")
            elif freq == 0.0 and self.threshold > 0.0:
                # This state was excluded by threshold
                excluded_parts.append(state)

        dist_line = "Distribution: " + ", ".join(dist_parts)
        if excluded_parts:
            excluded_str = ", ".join(excluded_parts)
            dist_line += f" ({excluded_str} excluded, <{self.threshold*100:.0f}%)"
        lines.append(dist_line)

        # Dominant state
        dominant = self.distribution.dominant
        if dominant != "unknown":
            definitive = "definitive" if self.distribution.is_definitive else "not definitive"
            lines.append(f"Dominant: {dominant} ({definitive})")

        # Data coverage
        lines.append(
            f"Based on {self.total_observations:,} observations from "
            f"{self.unique_hose_codes} HOSE codes"
        )

        return "\n".join(lines)
