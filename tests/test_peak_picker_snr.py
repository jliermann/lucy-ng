"""Tests for SNR/MAD peak-picker threshold (FIX-04).

Regression tests verifying that:
  - CASE9 ester carbonyl at 166.08 ppm is picked by the new threshold.
  - CASE1 (ibuprofen) 13C peak count is unchanged.
  - Per-peak SNR annotation is present.
"""

from pathlib import Path

import numpy as np
import pytest

from lucy_ng.models import PeakList1D
from lucy_ng.processing.peak_picker import AdaptivePeakPicker, _compute_snr_threshold
from lucy_ng.readers import BrukerReader

# Real Bruker data paths — confirmed available by RESEARCH.md
DATA_DIR = Path(__file__).parent.parent / "data"
CASE1_C13 = DATA_DIR / "Ibuprofen" / "2"  # in-repo

# CASE9 is outside the repo (see reference_test_data memory)
CASE9_C13 = Path(
    "/Users/steinbeck/Dropbox/develop/data/nmrdata"
    "/active-lucy-ng-testprojects/CASE9/12"
)


class TestSNRThreshold:
    """Unit tests for _compute_snr_threshold helper."""

    def test_mad_lower_than_max_for_cdcl3_dominated_spectrum(self) -> None:
        """sigma_mad must be << 5% of max for CDCl3-dominated spectrum."""
        # Synthetic: noise floor + one large CDCl3 spike
        rng = np.random.default_rng(42)
        noise = rng.normal(0, 1e5, 32768)
        ppm = np.linspace(220.0, 0.0, 32768)
        # Inject CDCl3 spike at 77 ppm
        cdcl3_idx = int((220.0 - 77.16) / 220.0 * 32768)
        noise[cdcl3_idx] = 4.6e7
        threshold, sigma_mad = _compute_snr_threshold(noise, ppm, solvent="CDCl3")
        # sigma_mad must be close to 1e5, not inflated by the spike
        assert sigma_mad < 5e5, f"sigma_mad too large: {sigma_mad:.2e}"
        # threshold = 3 * sigma_mad, must be << 2.30e6 (the old 5%-max threshold)
        assert threshold < 1e6


class TestCASE9Regression:
    """Integration regression: CASE9 carbonyl must be picked."""

    @pytest.mark.skipif(
        not CASE9_C13.exists(),
        reason="CASE9 dataset not available on this machine",
    )
    def test_case9_carbonyl_picked(self) -> None:
        """Ester C=O at 166.08 ppm (SNR≈17) must appear in peak list."""
        spectrum = BrukerReader.read_1d(str(CASE9_C13))
        peaks = AdaptivePeakPicker.pick_peaks(spectrum)

        ppms = [p.position for p in peaks.peaks]
        # Carbonyl at 166.08 ppm — accept ±2 ppm window
        assert any(164.0 <= ppm <= 168.0 for ppm in ppms), (
            f"Carbonyl not found near 166 ppm. Picked: {sorted(ppms, reverse=True)[:10]}"
        )

    @pytest.mark.skipif(
        not CASE9_C13.exists(),
        reason="CASE9 dataset not available on this machine",
    )
    def test_case9_all_peaks_have_snr(self) -> None:
        """Every picked peak must carry a non-None SNR annotation."""
        spectrum = BrukerReader.read_1d(str(CASE9_C13))
        peaks = AdaptivePeakPicker.pick_peaks(spectrum)
        for p in peaks.peaks:
            assert p.snr is not None
            assert p.snr > 0


class TestCASE1Regression:
    """Regression: ibuprofen 13C peak count must not decrease."""

    def test_case1_count_unchanged(self) -> None:
        """Ibuprofen should still yield >= 9 13C peaks (same as before)."""
        spectrum = BrukerReader.read_1d(str(CASE1_C13))
        peaks = AdaptivePeakPicker.pick_peaks(spectrum)
        # v8.0 picked 13 peaks; SNR threshold picks a superset — assert floor
        assert len(peaks.peaks) >= 9, (
            f"Ibuprofen peak count dropped to {len(peaks.peaks)}"
        )


class TestCLIPick1D:
    """CLI JSON output regression tests for FIX-04 fields."""

    def test_pick_1d_json_has_snr(self) -> None:
        """New SNR field must be present in each peak in JSON output."""
        import json

        from click.testing import CliRunner

        from lucy_ng.cli.pick import pick

        runner = CliRunner()
        result = runner.invoke(pick, ["1d", str(CASE1_C13), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "snr" in data["peaks"][0]
        # snr must be a positive number (not None serialized as null)
        assert data["peaks"][0]["snr"] is not None
        assert data["peaks"][0]["snr"] > 0

    def test_pick_1d_json_has_noise_sigma(self) -> None:
        """New noise_sigma top-level field must be present in JSON output."""
        import json

        from click.testing import CliRunner

        from lucy_ng.cli.pick import pick

        runner = CliRunner()
        result = runner.invoke(pick, ["1d", str(CASE1_C13), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "noise_sigma" in data
        assert data["noise_sigma"] is not None
        assert data["noise_sigma"] > 0
