"""Simple peak picking for 1D NMR spectra."""

import numpy as np
from scipy.signal import find_peaks

from lucy_ng.models import Peak1D, PeakList1D, Spectrum1D


class SimplePeakPicker:
    """Simple threshold-based 1D peak picker.

    Uses scipy.signal.find_peaks with intensity threshold and
    minimum distance constraints.
    """

    @staticmethod
    def pick_peaks(
        spectrum: Spectrum1D,
        threshold: float = 0.05,
        min_distance_ppm: float = 0.5,
    ) -> PeakList1D:
        """Pick peaks from a 1D spectrum using threshold detection.

        Args:
            spectrum: 1D NMR spectrum with data and ppm_scale
            threshold: Minimum intensity as fraction of max (0-1)
            min_distance_ppm: Minimum separation between peaks in ppm

        Returns:
            PeakList1D containing detected peaks
        """
        data = spectrum.data
        ppm_scale = spectrum.ppm_scale

        # Calculate threshold in absolute units
        max_intensity = np.max(np.abs(data))
        abs_threshold = threshold * max_intensity

        # Calculate minimum distance in data points
        # ppm_scale is typically decreasing (high to low ppm)
        ppm_per_point = abs(ppm_scale[1] - ppm_scale[0]) if len(ppm_scale) > 1 else 1.0
        min_distance_points = max(1, int(min_distance_ppm / ppm_per_point))

        # Find peaks using scipy
        peak_indices, properties = find_peaks(
            data,
            height=abs_threshold,
            distance=min_distance_points,
        )

        # Convert to Peak1D objects
        peaks = []
        for idx in peak_indices:
            position = float(ppm_scale[idx])
            intensity = float(data[idx])
            peaks.append(Peak1D(position=position, intensity=intensity))

        # Sort by ppm (descending, high field to low field)
        peaks.sort(key=lambda p: p.position, reverse=True)

        return PeakList1D(peaks=peaks, nucleus=spectrum.nucleus)

    @staticmethod
    def pick_peaks_with_noise_estimation(
        spectrum: Spectrum1D,
        snr_threshold: float = 3.0,
        min_distance_ppm: float = 0.5,
        noise_region: tuple[float, float] | None = None,
    ) -> PeakList1D:
        """Pick peaks using noise estimation for threshold.

        Args:
            spectrum: 1D NMR spectrum
            snr_threshold: Minimum signal-to-noise ratio
            min_distance_ppm: Minimum separation between peaks in ppm
            noise_region: ppm range (low, high) to estimate noise from.
                         If None, uses edges of spectrum.

        Returns:
            PeakList1D containing detected peaks
        """
        data = spectrum.data
        ppm_scale = spectrum.ppm_scale

        # Estimate noise
        if noise_region is not None:
            low_ppm, high_ppm = noise_region
            noise_mask = (ppm_scale >= low_ppm) & (ppm_scale <= high_ppm)
            if np.any(noise_mask):
                noise_data = data[noise_mask]
            else:
                # Fallback to edges
                noise_data = np.concatenate([data[:100], data[-100:]])
        else:
            # Use first and last 5% of spectrum for noise estimation
            n_points = len(data)
            edge_size = max(10, n_points // 20)
            noise_data = np.concatenate([data[:edge_size], data[-edge_size:]])

        # Noise level as standard deviation
        noise_level = np.std(noise_data)

        # Threshold based on SNR
        abs_threshold = snr_threshold * noise_level

        # Calculate minimum distance in data points
        ppm_per_point = abs(ppm_scale[1] - ppm_scale[0]) if len(ppm_scale) > 1 else 1.0
        min_distance_points = max(1, int(min_distance_ppm / ppm_per_point))

        # Find peaks
        peak_indices, _ = find_peaks(
            data,
            height=abs_threshold,
            distance=min_distance_points,
        )

        # Convert to Peak1D objects
        peaks = []
        for idx in peak_indices:
            position = float(ppm_scale[idx])
            intensity = float(data[idx])
            peaks.append(Peak1D(position=position, intensity=intensity))

        # Sort by ppm (descending)
        peaks.sort(key=lambda p: p.position, reverse=True)

        return PeakList1D(peaks=peaks, nucleus=spectrum.nucleus)
