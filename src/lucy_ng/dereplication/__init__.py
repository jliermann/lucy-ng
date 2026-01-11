"""Dereplication module for matching compounds against reference databases."""

from lucy_ng.dereplication.coconut import CoconutLoader
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
from lucy_ng.dereplication.sherlock import (
    SherlockEntry,
    SherlockLoader,
)

__all__ = [
    # coconut
    "CoconutLoader",
    # nmrshiftdb
    "HydrogenCount",
    "CarbonSignal",
    "NMRShiftDBEntry",
    "NMRShiftDBLoader",
    # sherlock
    "SherlockEntry",
    "SherlockLoader",
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
