"""2D NMR peak picking."""

from typing import Any

import nmrglue as ng
import numpy as np

from lucy_ng.models import Peak2D, PeakList2D, Spectrum2D


class PeakPicker2D:
    """2D NMR peak picker using nmrglue.

    Uses nmrglue's peak picking algorithm which finds local maxima
    and clusters connected regions above threshold.
    """

    @staticmethod
    def pick_peaks(
        spectrum: Spectrum2D,
        threshold: float = 0.05,
        min_separation: tuple[int, int] = (3, 3),
        detect_negative: bool = False,
    ) -> PeakList2D:
        """Pick peaks from a 2D spectrum.

        Args:
            spectrum: 2D NMR spectrum with data and ppm scales
            threshold: Minimum intensity as fraction of max (0-1)
            min_separation: Minimum separation in points (F1, F2)
            detect_negative: Also detect negative peaks (for HMBC artifacts)

        Returns:
            PeakList2D containing detected peaks
        """
        data = spectrum.data
        f1_ppm_scale = spectrum.f1_ppm_scale
        f2_ppm_scale = spectrum.f2_ppm_scale

        # Calculate threshold in absolute units
        max_intensity = np.max(np.abs(data))
        abs_threshold = threshold * max_intensity

        peaks: list[Peak2D] = []

        # Pick positive peaks
        pos_result = ng.peakpick.pick(
            data,
            pthres=abs_threshold,
            nthres=None,
            msep=min_separation,
            algorithm="connected",
            est_params=True,
            cluster=True,
            table=True,
        )

        # Convert to Peak2D objects
        for row in pos_result:
            y_idx = int(row["Y_AXIS"])
            x_idx = int(row["X_AXIS"])

            # Convert indices to ppm
            f1_ppm = float(f1_ppm_scale[y_idx]) if y_idx < len(f1_ppm_scale) else 0.0
            f2_ppm = float(f2_ppm_scale[x_idx]) if x_idx < len(f2_ppm_scale) else 0.0

            # Get intensity at peak location
            intensity = float(data[y_idx, x_idx])

            peaks.append(
                Peak2D(f1_position=f1_ppm, f2_position=f2_ppm, intensity=intensity)
            )

        # Pick negative peaks if requested
        if detect_negative:
            neg_result = ng.peakpick.pick(
                data,
                pthres=None,
                nthres=-abs_threshold,
                msep=min_separation,
                algorithm="connected",
                est_params=True,
                cluster=True,
                table=True,
            )

            for row in neg_result:
                y_idx = int(row["Y_AXIS"])
                x_idx = int(row["X_AXIS"])

                f1_ppm = float(f1_ppm_scale[y_idx]) if y_idx < len(f1_ppm_scale) else 0.0
                f2_ppm = float(f2_ppm_scale[x_idx]) if x_idx < len(f2_ppm_scale) else 0.0
                intensity = float(data[y_idx, x_idx])

                peaks.append(
                    Peak2D(f1_position=f1_ppm, f2_position=f2_ppm, intensity=intensity)
                )

        # Sort by F1 ppm (descending), then F2 ppm (descending)
        peaks.sort(key=lambda p: (-p.f1_position, -p.f2_position))

        return PeakList2D(
            peaks=peaks,
            f1_nucleus=spectrum.f1_nucleus,
            f2_nucleus=spectrum.f2_nucleus,
            experiment_type=spectrum.experiment_type,
        )

    @staticmethod
    def pick_peaks_snr(
        spectrum: Spectrum2D,
        snr_threshold: float = 5.0,
        min_separation: tuple[int, int] = (3, 3),
        detect_negative: bool = False,
    ) -> PeakList2D:
        """Pick peaks using signal-to-noise ratio threshold.

        Args:
            spectrum: 2D NMR spectrum
            snr_threshold: Minimum signal-to-noise ratio
            min_separation: Minimum separation in points (F1, F2)
            detect_negative: Also detect negative peaks

        Returns:
            PeakList2D containing detected peaks
        """
        noise = PeakPicker2D.estimate_noise(spectrum)
        abs_threshold = snr_threshold * noise

        # Use absolute threshold with pick_peaks logic
        max_intensity = np.max(np.abs(spectrum.data))
        relative_threshold = abs_threshold / max_intensity

        return PeakPicker2D.pick_peaks(
            spectrum,
            threshold=relative_threshold,
            min_separation=min_separation,
            detect_negative=detect_negative,
        )

    @staticmethod
    def estimate_noise(spectrum: Spectrum2D, corner_fraction: float = 0.1) -> float:
        """Estimate noise level from spectrum corners.

        Uses the corners of the 2D spectrum where real peaks are
        unlikely to be found.

        Args:
            spectrum: 2D NMR spectrum
            corner_fraction: Fraction of each dimension to use (0-0.5)

        Returns:
            Estimated noise level (standard deviation)
        """
        data = spectrum.data
        f1_size, f2_size = data.shape

        # Calculate corner sizes
        f1_corner = max(1, int(f1_size * corner_fraction))
        f2_corner = max(1, int(f2_size * corner_fraction))

        # Extract corners (top-left, top-right, bottom-left, bottom-right)
        corners = [
            data[:f1_corner, :f2_corner],  # Top-left
            data[:f1_corner, -f2_corner:],  # Top-right
            data[-f1_corner:, :f2_corner],  # Bottom-left
            data[-f1_corner:, -f2_corner:],  # Bottom-right
        ]

        # Combine all corner data
        corner_data = np.concatenate([c.flatten() for c in corners])

        # Return standard deviation as noise estimate
        return float(np.std(corner_data))

    @staticmethod
    def get_peak_info(spectrum: Spectrum2D, peak: Peak2D) -> dict[str, Any]:
        """Get detailed information about a peak.

        Args:
            spectrum: 2D NMR spectrum
            peak: Peak to analyze

        Returns:
            Dictionary with peak details including linewidths
        """
        # Find index of peak
        f1_idx = int(np.argmin(np.abs(spectrum.f1_ppm_scale - peak.f1_position)))
        f2_idx = int(np.argmin(np.abs(spectrum.f2_ppm_scale - peak.f2_position)))

        return {
            "f1_ppm": peak.f1_position,
            "f2_ppm": peak.f2_position,
            "f1_index": f1_idx,
            "f2_index": f2_idx,
            "intensity": peak.intensity,
            "f1_nucleus": spectrum.f1_nucleus,
            "f2_nucleus": spectrum.f2_nucleus,
        }
