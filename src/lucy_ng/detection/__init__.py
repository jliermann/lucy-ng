"""Statistical detection of structural constraints from NMR shifts."""

from lucy_ng.detection.detector import StatisticalDetector
from lucy_ng.detection.grouping import group_signals
from lucy_ng.detection.models import (
    GroupingResult,
    HHBResult,
    HybridisationResult,
    NeighbourResult,
)

__all__ = [
    "StatisticalDetector",
    "GroupingResult",
    "HHBResult",
    "HybridisationResult",
    "NeighbourResult",
    "group_signals",
]
