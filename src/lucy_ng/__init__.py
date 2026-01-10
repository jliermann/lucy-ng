"""lucy-ng: AI-agent powered Computer-Assisted Structure Elucidation."""

from lucy_ng.models import Peak1D, Peak2D, PeakList1D, PeakList2D, Spectrum1D, Spectrum2D
from lucy_ng.processing import (
    AdaptivePeakPicker,
    DEPTGuidedPicker,
    DEPTGuidedResult,
    PeakPicker2D,
    PeakValidator,
    SimplePeakPicker,
    ValidationResult,
)
from lucy_ng.readers import BrukerReader

# LSD integration (import from lucy_ng.lsd for full access)
from lucy_ng.lsd import LSDInputGenerator, LSDProblem, LSDRunner

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
    "SimplePeakPicker",
    "ValidationResult",
    # LSD
    "LSDInputGenerator",
    "LSDProblem",
    "LSDRunner",
]
