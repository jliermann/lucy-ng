"""Dereplication module for matching compounds against nmrshiftdb."""

from lucy_ng.dereplication.matcher import (
    MatchingConfig,
    MatchMode,
    MatchResult,
    ObservedPeak,
    PeakMatch,
    SpectrumMatcher,
)
from lucy_ng.dereplication.nmrshiftdb import (
    CarbonSignal,
    HydrogenCount,
    NMRShiftDBEntry,
    NMRShiftDBLoader,
)
from lucy_ng.dereplication.service import (
    DereplicationResult,
    DereplicationService,
    create_observed_peaks_with_dept,
)

__all__ = [
    # nmrshiftdb
    "HydrogenCount",
    "CarbonSignal",
    "NMRShiftDBEntry",
    "NMRShiftDBLoader",
    # matcher
    "MatchMode",
    "MatchingConfig",
    "PeakMatch",
    "MatchResult",
    "ObservedPeak",
    "SpectrumMatcher",
    # service
    "DereplicationResult",
    "DereplicationService",
    "create_observed_peaks_with_dept",
]
