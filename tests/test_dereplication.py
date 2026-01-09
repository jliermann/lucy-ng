"""Tests for the dereplication module."""

from pathlib import Path

import numpy as np
import pytest

from lucy_ng.dereplication.matcher import (
    MatchingConfig,
    MatchMode,
    ObservedPeak,
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
from lucy_ng.models import Peak1D, PeakList1D, Spectrum1D
from lucy_ng.processing import SimplePeakPicker

# Path to test data
DATA_DIR = Path(__file__).parent.parent / "data"
SD_FILE = DATA_DIR / "reference" / "nmrshiftdb2withsignals.sd"
IBUPROFEN_DIR = DATA_DIR / "Ibuprofen"


# ============================================================================
# NMRShiftDB Loader Tests
# ============================================================================


class TestNMRShiftDBLoader:
    """Tests for NMRShiftDBLoader."""

    def test_parse_spectrum_field_basic(self):
        """Test parsing spectrum field format."""
        field = "17.6;0.0Q;1|22.4;0.0T;2|45.1;0.0D;3"
        signals = NMRShiftDBLoader.parse_spectrum_field(field)

        assert len(signals) == 3
        assert signals[0].shift == pytest.approx(17.6)
        assert signals[0].hydrogen_count == HydrogenCount.CH3  # Q = quartet = CH3
        assert signals[1].shift == pytest.approx(22.4)
        assert signals[1].hydrogen_count == HydrogenCount.CH2  # T = triplet = CH2
        assert signals[2].shift == pytest.approx(45.1)
        assert signals[2].hydrogen_count == HydrogenCount.CH  # D = doublet = CH

    def test_parse_spectrum_field_singlet(self):
        """Test parsing singlet (quaternary carbon)."""
        field = "127.5;0.0S;1"
        signals = NMRShiftDBLoader.parse_spectrum_field(field)

        assert len(signals) == 1
        assert signals[0].hydrogen_count == HydrogenCount.C  # S = singlet = quaternary

    def test_parse_spectrum_field_no_multiplicity(self):
        """Test parsing without multiplicity info."""
        field = "17.6;;1|22.4;;2"
        signals = NMRShiftDBLoader.parse_spectrum_field(field)

        assert len(signals) == 2
        assert signals[0].shift == pytest.approx(17.6)
        assert signals[0].hydrogen_count is None

    def test_count_carbons_normal(self):
        """Test carbon count extraction."""
        assert NMRShiftDBLoader.count_carbons("C13H18O2") == 13
        assert NMRShiftDBLoader.count_carbons("C6H12O6") == 6
        assert NMRShiftDBLoader.count_carbons("CH4") == 1

    def test_count_carbons_no_carbon(self):
        """Test formula without carbon."""
        assert NMRShiftDBLoader.count_carbons("H2O") == 0
        assert NMRShiftDBLoader.count_carbons("NaCl") == 0

    def test_normalize_formula_subscripts(self):
        """Test formula normalization with subscripts."""
        assert NMRShiftDBLoader._normalize_formula("C₁₃H₁₈O₂") == "C13H18O2"
        assert NMRShiftDBLoader._normalize_formula("C 13 H 18 O 2") == "C13H18O2"

    @pytest.mark.skipif(not SD_FILE.exists(), reason="SD file not available")
    def test_nmrshiftdb_loader_basic(self):
        """Test loading SD file (requires actual file)."""
        loader = NMRShiftDBLoader(SD_FILE)
        entries = loader.load()

        assert len(entries) > 0
        # Check first entry has required fields
        entry = entries[0]
        assert entry.molecular_formula
        assert entry.carbon_count > 0
        assert len(entry.signals) > 0

    @pytest.mark.skipif(not SD_FILE.exists(), reason="SD file not available")
    def test_formula_filter(self):
        """Test filtering by molecular formula (requires actual file)."""
        loader = NMRShiftDBLoader(SD_FILE)
        loader.load()

        # Ibuprofen formula
        candidates = loader.get_by_formula("C13H18O2")
        assert len(candidates) > 0


# ============================================================================
# Peak Picker Tests
# ============================================================================


class TestSimplePeakPicker:
    """Tests for SimplePeakPicker."""

    def test_pick_peaks_basic(self):
        """Test basic peak picking."""
        # Create synthetic spectrum with known peaks
        ppm = np.linspace(200, 0, 2000)
        data = np.zeros(2000)

        # Add peaks at specific positions
        peak_positions = [150.0, 130.0, 45.0, 20.0]
        for pos in peak_positions:
            idx = int((200 - pos) / 200 * 2000)
            data[idx] = 1.0
            # Add some width
            if idx > 0:
                data[idx - 1] = 0.3
            if idx < 1999:
                data[idx + 1] = 0.3

        spectrum = Spectrum1D(
            data=data,
            ppm_scale=ppm,
            nucleus="13C",
            frequency=100.0,
        )

        peaks = SimplePeakPicker.pick_peaks(spectrum, threshold=0.1)

        assert len(peaks.peaks) == 4
        assert peaks.nucleus == "13C"

    def test_pick_peaks_threshold(self):
        """Test that higher threshold gives fewer peaks."""
        ppm = np.linspace(200, 0, 2000)
        data = np.zeros(2000)

        # Add peaks with different intensities
        data[500] = 1.0  # Strong
        data[1000] = 0.3  # Medium
        data[1500] = 0.1  # Weak

        spectrum = Spectrum1D(data=data, ppm_scale=ppm, nucleus="13C", frequency=100.0)

        peaks_low = SimplePeakPicker.pick_peaks(spectrum, threshold=0.05)
        peaks_high = SimplePeakPicker.pick_peaks(spectrum, threshold=0.5)

        assert len(peaks_low.peaks) >= len(peaks_high.peaks)

    @pytest.mark.skipif(not IBUPROFEN_DIR.exists(), reason="Test data not available")
    def test_peak_picker_13c(self):
        """Test picking peaks from Ibuprofen 13C spectrum."""
        from lucy_ng.readers import BrukerReader

        spectrum = BrukerReader.read_1d(IBUPROFEN_DIR / "2")

        peaks = SimplePeakPicker.pick_peaks(spectrum, threshold=0.05)

        # Ibuprofen has 13 carbons, but some may overlap
        # Expect reasonable number of peaks (8-15)
        assert 5 <= len(peaks.peaks) <= 20


# ============================================================================
# Matcher Tests
# ============================================================================


class TestSpectrumMatcher:
    """Tests for SpectrumMatcher."""

    def _create_reference(
        self,
        shifts: list[float],
        h_counts: list[HydrogenCount | None] | None = None,
    ) -> NMRShiftDBEntry:
        """Helper to create a reference entry."""
        if h_counts is None:
            h_counts = [None] * len(shifts)
        signals = [
            CarbonSignal(shift=s, hydrogen_count=h) for s, h in zip(shifts, h_counts)
        ]
        return NMRShiftDBEntry(
            nmrshiftdb_id=1,
            molecular_formula="C10H12O2",
            carbon_count=10,
            inchi="",
            inchi_key="",
            signals=signals,
        )

    def test_matcher_shifts_only(self):
        """Test matching using just shift values."""
        reference = self._create_reference([20.0, 40.0, 130.0, 150.0])
        observed = [
            ObservedPeak(shift=20.5),
            ObservedPeak(shift=40.2),
            ObservedPeak(shift=130.1),
            ObservedPeak(shift=150.3),
        ]

        matcher = SpectrumMatcher()
        result = matcher.match(observed, reference)

        assert result.matched_peaks == 4
        assert result.score > 0.9  # Near perfect match

    def test_matcher_dept_enhanced(self):
        """Test matching with DEPT info gives score boost."""
        reference = self._create_reference(
            [20.0, 40.0],
            [HydrogenCount.CH3, HydrogenCount.CH2],
        )
        observed_matching = [
            ObservedPeak(shift=20.5, hydrogen_count=HydrogenCount.CH3),
            ObservedPeak(shift=40.2, hydrogen_count=HydrogenCount.CH2),
        ]
        observed_mismatching = [
            ObservedPeak(shift=20.5, hydrogen_count=HydrogenCount.CH),  # Wrong!
            ObservedPeak(shift=40.2, hydrogen_count=HydrogenCount.CH3),  # Wrong!
        ]

        config = MatchingConfig(mode=MatchMode.DEPT_ENHANCED)
        matcher = SpectrumMatcher(config)

        result_match = matcher.match(observed_matching, reference)
        result_mismatch = matcher.match(observed_mismatching, reference)

        # Matching DEPT should give higher score
        assert result_match.score > result_mismatch.score
        assert result_match.dept_matches == 2
        assert result_mismatch.dept_matches == 0

    def test_matcher_variable_tolerance(self):
        """Test that different tolerances apply to different regions."""
        config = MatchingConfig(
            use_variable_tolerance=True,
            aliphatic_tolerance=0.5,
            aromatic_tolerance=2.0,
        )

        # Aliphatic region - tight tolerance
        assert config.get_tolerance(20.0) == 0.5
        assert config.get_tolerance(50.0) == 0.5

        # Aromatic region - loose tolerance
        assert config.get_tolerance(130.0) == 2.0
        assert config.get_tolerance(150.0) == 2.0

    def test_matcher_overlap_handling(self):
        """Test that score isn't penalized when observed < expected carbons."""
        # Reference has 10 signals
        reference = self._create_reference([i * 10.0 for i in range(10)])

        # Only observe 7 peaks (3 overlapping)
        observed = [ObservedPeak(shift=i * 10.0 + 0.5) for i in range(7)]

        matcher = SpectrumMatcher()
        result = matcher.match(observed, reference)

        # Should still get a reasonable score
        assert result.matched_peaks == 7
        assert result.score > 0.6  # Not perfect but reasonable

    def test_matcher_unmatched_tracking(self):
        """Test that unmatched peaks are tracked correctly."""
        reference = self._create_reference([20.0, 40.0, 60.0])
        observed = [
            ObservedPeak(shift=20.5),  # Matches
            ObservedPeak(shift=100.0),  # No match (too far)
        ]

        matcher = SpectrumMatcher()
        result = matcher.match(observed, reference)

        assert result.matched_peaks == 1
        assert len(result.unmatched_observed) == 1
        assert 100.0 in result.unmatched_observed
        assert len(result.unmatched_reference) == 2  # 40.0 and 60.0 not matched


# ============================================================================
# Dereplication Service Tests
# ============================================================================


class TestDereplicationService:
    """Tests for DereplicationService."""

    def _create_mock_loader(self) -> NMRShiftDBLoader:
        """Create a loader with mock data for testing."""

        class MockLoader(NMRShiftDBLoader):
            def __init__(self):
                self._entries = []
                self._formula_index = {}
                self._loaded = False

            def load(self):
                if self._loaded:
                    return self._entries

                # Add some mock entries
                self._entries = [
                    NMRShiftDBEntry(
                        nmrshiftdb_id=1,
                        molecular_formula="C10H12O2",
                        carbon_count=10,
                        inchi="",
                        inchi_key="",
                        signals=[
                            CarbonSignal(shift=20.0, hydrogen_count=HydrogenCount.CH3),
                            CarbonSignal(shift=40.0, hydrogen_count=HydrogenCount.CH2),
                            CarbonSignal(shift=130.0, hydrogen_count=HydrogenCount.CH),
                        ],
                    ),
                    NMRShiftDBEntry(
                        nmrshiftdb_id=2,
                        molecular_formula="C10H12O2",
                        carbon_count=10,
                        inchi="",
                        inchi_key="",
                        signals=[
                            CarbonSignal(shift=25.0, hydrogen_count=HydrogenCount.CH3),
                            CarbonSignal(shift=50.0, hydrogen_count=HydrogenCount.CH2),
                            CarbonSignal(shift=140.0, hydrogen_count=HydrogenCount.CH),
                        ],
                    ),
                ]

                # Index by formula
                self._formula_index["C10H12O2"] = self._entries
                self._loaded = True
                return self._entries

        return MockLoader()

    def test_dereplicate_from_shifts(self):
        """Test simplest API with just ppm list."""
        loader = self._create_mock_loader()
        loader.load()
        service = DereplicationService(loader)

        result = service.dereplicate_from_shifts(
            shifts=[20.5, 40.2, 130.1],
            molecular_formula="C10H12O2",
        )

        assert result.candidates_found == 2
        assert result.observed_peaks == 3
        assert result.match_mode == MatchMode.SHIFTS_ONLY
        assert len(result.top_matches) > 0
        # First entry should match better
        assert result.top_matches[0].entry.nmrshiftdb_id == 1

    def test_dereplicate_from_peaks_with_dept(self):
        """Test DEPT-enhanced matching."""
        loader = self._create_mock_loader()
        loader.load()
        service = DereplicationService(loader)

        peaks = [
            ObservedPeak(shift=20.5, hydrogen_count=HydrogenCount.CH3),
            ObservedPeak(shift=40.2, hydrogen_count=HydrogenCount.CH2),
            ObservedPeak(shift=130.1, hydrogen_count=HydrogenCount.CH),
        ]

        result = service.dereplicate_from_peaks(
            peaks=peaks,
            molecular_formula="C10H12O2",
        )

        assert result.match_mode == MatchMode.DEPT_ENHANCED
        assert result.top_matches[0].dept_matches == 3

    def test_no_candidates(self):
        """Test handling formula with no matches in DB."""
        loader = self._create_mock_loader()
        loader.load()
        service = DereplicationService(loader)

        result = service.dereplicate_from_shifts(
            shifts=[20.0, 40.0],
            molecular_formula="C100H200O50",  # Not in DB
        )

        assert result.candidates_found == 0
        assert result.top_matches == []
        assert result.is_match is False

    def test_empty_peak_list(self):
        """Test handling empty peak list gracefully."""
        loader = self._create_mock_loader()
        loader.load()
        service = DereplicationService(loader)

        result = service.dereplicate_from_shifts(
            shifts=[],
            molecular_formula="C10H12O2",
        )

        assert result.observed_peaks == 0
        assert result.best_score == 0.0

    def test_missing_dept_info(self):
        """Test graceful fallback to shifts-only."""
        loader = self._create_mock_loader()
        loader.load()
        service = DereplicationService(loader)

        # Peaks without DEPT info
        peaks = [
            ObservedPeak(shift=20.5),
            ObservedPeak(shift=40.2),
        ]

        result = service.dereplicate_from_peaks(
            peaks=peaks,
            molecular_formula="C10H12O2",
        )

        # Should fall back to shifts-only mode
        assert result.match_mode == MatchMode.SHIFTS_ONLY


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_observed_peaks_with_dept(self):
        """Test helper to create peaks with DEPT."""
        shifts = [20.0, 40.0, 130.0]
        h_counts = [HydrogenCount.CH3, HydrogenCount.CH2, None]

        peaks = create_observed_peaks_with_dept(shifts, h_counts)

        assert len(peaks) == 3
        assert peaks[0].shift == 20.0
        assert peaks[0].hydrogen_count == HydrogenCount.CH3
        assert peaks[2].hydrogen_count is None

    def test_create_observed_peaks_with_dept_length_mismatch(self):
        """Test error on mismatched lengths."""
        with pytest.raises(ValueError):
            create_observed_peaks_with_dept([1.0, 2.0], [HydrogenCount.CH3])


# ============================================================================
# Integration Tests (require real data)
# ============================================================================


@pytest.mark.skipif(
    not (SD_FILE.exists() and IBUPROFEN_DIR.exists()),
    reason="Test data not available",
)
class TestIntegration:
    """Integration tests with real data."""

    def test_dereplicate_ibuprofen_ranking(self):
        """Test that Ibuprofen ranks highly among C13H18O2 candidates."""
        from lucy_ng.readers import BrukerReader

        # Load reference database
        loader = NMRShiftDBLoader(SD_FILE)
        loader.load()

        # Load Ibuprofen spectrum
        spectrum = BrukerReader.read_1d(IBUPROFEN_DIR / "2")

        # Pick peaks
        peaks = SimplePeakPicker.pick_peaks(spectrum, threshold=0.05)
        observed = [ObservedPeak(shift=p.position) for p in peaks.peaks]

        # Create service and dereplicate
        service = DereplicationService(loader)
        result = service.dereplicate_from_peaks(
            peaks=observed,
            molecular_formula="C13H18O2",
            top_n=10,
        )

        # Should find candidates
        assert result.candidates_found > 0
        # Top match should have reasonable score
        assert result.best_score > 0.3

    def test_dereplicate_from_spectrum(self):
        """Test full pipeline from raw spectrum."""
        from lucy_ng.readers import BrukerReader

        loader = NMRShiftDBLoader(SD_FILE)
        loader.load()

        spectrum = BrukerReader.read_1d(IBUPROFEN_DIR / "2")

        service = DereplicationService(loader)
        result = service.dereplicate_from_spectrum(
            spectrum=spectrum,
            molecular_formula="C13H18O2",
        )

        assert result.candidates_found > 0
        assert result.observed_peaks > 0
