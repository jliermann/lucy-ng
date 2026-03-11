"""Statistical detection of structural constraints from NMR shifts."""

from lucy_ng.detection.detector import StatisticalDetector
from lucy_ng.detection.grouping import group_signals
from lucy_ng.detection.models import (
    CouplingPathDistribution,
    CouplingPathResult,
    GroupingResult,
    HHBResult,
    HybridisationResult,
    NeighbourResult,
    RiskLevel,
)

__all__ = [
    "StatisticalDetector",
    "CouplingPathDistribution",
    "CouplingPathResult",
    "GroupingResult",
    "HHBResult",
    "HybridisationResult",
    "NeighbourResult",
    "RiskLevel",
    "group_signals",
]
