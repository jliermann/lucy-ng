"""lucy-ng: AI-agent powered Computer-Assisted Structure Elucidation."""

from lucy_ng.analysis import (
    HydrogenBudgetAnalyzer,
    IntensityReporter,
    SymmetryAnalyzer,
)
from lucy_ng.models import Peak1D, Peak2D, PeakList1D, PeakList2D, Spectrum1D, Spectrum2D
from lucy_ng.prediction import C13Predictor, HOSECodeGenerator, HOSELookupTable
from lucy_ng.processing import (
    AdaptivePeakPicker,
    DEPTGuidedPicker,
    DEPTGuidedResult,
    PeakPicker2D,
    PeakValidator,
    ValidationResult,
)
from lucy_ng.readers import BrukerReader

# LSD integration (import from lucy_ng.lsd for full access)
from lucy_ng.lsd import LSDInputGenerator, LSDProblem, LSDRunner

# Ranking
from lucy_ng.ranking import SolutionRanker

# NMRXiv
from lucy_ng.nmrxiv import NMRXivClient

__version__ = "0.1.0"

__all__ = [
    # Readers
    "BrukerReader",
    # Models
    "Peak1D",
    "Peak2D",
    "PeakList1D",
    "PeakList2D",
    "Spectrum1D",
    "Spectrum2D",
    # Processing
    "AdaptivePeakPicker",
    "DEPTGuidedPicker",
    "DEPTGuidedResult",
    "PeakPicker2D",
    "PeakValidator",
    "ValidationResult",
    # Analysis
    "HydrogenBudgetAnalyzer",
    "IntensityReporter",
    "SymmetryAnalyzer",
    # Prediction
    "C13Predictor",
    "HOSECodeGenerator",
    "HOSELookupTable",
    # LSD
    "LSDInputGenerator",
    "LSDProblem",
    "LSDRunner",
    # Ranking
    "SolutionRanker",
    # NMRXiv
    "NMRXivClient",
]
