"""lucy-ng: AI-agent powered Computer-Assisted Structure Elucidation."""

from lucy_ng.models import Peak1D, Peak2D, PeakList1D, PeakList2D, Spectrum1D, Spectrum2D
from lucy_ng.processing import SimplePeakPicker
from lucy_ng.readers import BrukerReader

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
    "SimplePeakPicker",
]
