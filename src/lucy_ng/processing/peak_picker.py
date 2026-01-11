"""Peak picking for 1D NMR spectra."""

import numpy as np
from scipy.signal import find_peaks, peak_widths

from lucy_ng.models import Peak1D, PeakList1D, Spectrum1D


class AdaptivePeakPicker:
    """Adaptive peak picker that adjusts minimum distance based on line width.

    Uses a two-pass approach:
    1. First pass: Find prominent peaks with loose criteria
    2. Measure FWHM (Full Width at Half Maximum) for each peak
    3. Calculate adaptive min_distance based on median FWHM
    4. Second pass: Re-pick with adaptive distance

    This allows detecting closely-spaced peaks in high-resolution spectra
    while avoiding noise in broader regions.
    """

    # Default instance for static method
    _default_instance: "AdaptivePeakPicker | None" = None

    def __init__(self, fwhm_factor: float = 1.5, fallback_min_distance_ppm: float = 0.1):
        """Initialize adaptive peak picker.

        Args:
            fwhm_factor: Multiplier for median FWHM to get min_distance.
                        Default 1.5 means peaks must be ~1.5 line widths apart.
            fallback_min_distance_ppm: Minimum distance to use if FWHM
                        estimation fails. Default 0.1 ppm.
        """
        self.fwhm_factor = fwhm_factor
        self.fallback_min_distance_ppm = fallback_min_distance_ppm

    @staticmethod
    def pick_peaks(
        spectrum: Spectrum1D,
        threshold: float = 0.05,
        detect_negative: bool = False,
    ) -> PeakList1D:
        """Pick peaks with adaptive minimum distance based on line width.

        Static convenience method that uses default parameters.
        For custom fwhm_factor or fallback_min_distance_ppm, create an
        instance and call pick_peaks_instance() instead.

        Args:
            spectrum: 1D NMR spectrum with data and ppm_scale
            threshold: Minimum intensity as fraction of max (0-1)
            detect_negative: If True, also detect negative peaks (for DEPT)

        Returns:
            PeakList1D containing detected peaks
        """
        # Lazily create default instance
        if AdaptivePeakPicker._default_instance is None:
            AdaptivePeakPicker._default_instance = AdaptivePeakPicker()

        return AdaptivePeakPicker._default_instance.pick_peaks_instance(
            spectrum, threshold, detect_negative
        )

    def pick_peaks_instance(
        self,
        spectrum: Spectrum1D,
        threshold: float = 0.05,
        detect_negative: bool = False,
    ) -> PeakList1D:
        """Pick peaks with adaptive minimum distance based on line width.

        Instance method that uses instance's fwhm_factor and fallback settings.

        Args:
            spectrum: 1D NMR spectrum with data and ppm_scale
            threshold: Minimum intensity as fraction of max (0-1)
            detect_negative: If True, also detect negative peaks (for DEPT)

        Returns:
            PeakList1D containing detected peaks
        """
        data = spectrum.data
        ppm_scale = spectrum.ppm_scale
        ppm_per_point = abs(ppm_scale[1] - ppm_scale[0]) if len(ppm_scale) > 1 else 1.0

        # Calculate threshold in absolute units
        max_intensity = np.max(np.abs(data))
        abs_threshold = threshold * max_intensity

        # Estimate adaptive minimum distance from line widths
        min_distance_ppm = self._estimate_min_distance(
            data, ppm_per_point, abs_threshold
        )
        min_distance_points = max(1, int(min_distance_ppm / ppm_per_point))

        # Find positive peaks
        peak_indices, _ = find_peaks(
            data,
            height=abs_threshold,
            distance=min_distance_points,
        )

        peaks = []
        for idx in peak_indices:
            position = float(ppm_scale[idx])
            intensity = float(data[idx])
            peaks.append(Peak1D(position=position, intensity=intensity))

        # Find negative peaks if requested (for DEPT spectra)
        if detect_negative:
            neg_indices, _ = find_peaks(
                -data,
                height=abs_threshold,
                distance=min_distance_points,
            )
            for idx in neg_indices:
                position = float(ppm_scale[idx])
                intensity = float(data[idx])  # Keep negative value
                peaks.append(Peak1D(position=position, intensity=intensity))

        # Sort by ppm (descending)
        peaks.sort(key=lambda p: p.position, reverse=True)

        return PeakList1D(peaks=peaks, nucleus=spectrum.nucleus)

    def estimate_line_widths(
        self,
        spectrum: Spectrum1D,
        threshold: float = 0.05,
    ) -> dict[str, float]:
        """Estimate line widths from the spectrum.

        Args:
            spectrum: 1D NMR spectrum
            threshold: Minimum intensity as fraction of max (0-1)

        Returns:
            Dictionary with 'median_fwhm_ppm', 'median_fwhm_hz',
            'min_fwhm_ppm', 'max_fwhm_ppm', 'adaptive_min_distance_ppm'
        """
        data = spectrum.data
        ppm_scale = spectrum.ppm_scale
        ppm_per_point = abs(ppm_scale[1] - ppm_scale[0]) if len(ppm_scale) > 1 else 1.0

        max_intensity = np.max(np.abs(data))
        abs_threshold = threshold * max_intensity

        # First pass with loose distance
        initial_distance = max(1, int(0.01 / ppm_per_point))  # ~0.01 ppm
        peak_indices, _ = find_peaks(
            data,
            height=abs_threshold,
            distance=initial_distance,
        )

        if len(peak_indices) == 0:
            return {
                "median_fwhm_ppm": self.fallback_min_distance_ppm,
                "median_fwhm_hz": self.fallback_min_distance_ppm * spectrum.frequency,
                "min_fwhm_ppm": self.fallback_min_distance_ppm,
                "max_fwhm_ppm": self.fallback_min_distance_ppm,
                "adaptive_min_distance_ppm": self.fallback_min_distance_ppm,
                "num_peaks_analyzed": 0,
            }

        # Measure FWHM
        try:
            widths_points, _, _, _ = peak_widths(data, peak_indices, rel_height=0.5)
            widths_ppm = widths_points * ppm_per_point

            # Filter out unreasonably wide peaks (likely baseline issues)
            reasonable_widths = widths_ppm[widths_ppm < 1.0]  # Max 1 ppm
            if len(reasonable_widths) == 0:
                reasonable_widths = widths_ppm

            median_fwhm = float(np.median(reasonable_widths))
            min_fwhm = float(np.min(reasonable_widths))
            max_fwhm = float(np.max(reasonable_widths))

        except Exception:
            median_fwhm = self.fallback_min_distance_ppm
            min_fwhm = self.fallback_min_distance_ppm
            max_fwhm = self.fallback_min_distance_ppm

        return {
            "median_fwhm_ppm": median_fwhm,
            "median_fwhm_hz": median_fwhm * spectrum.frequency,
            "min_fwhm_ppm": min_fwhm,
            "max_fwhm_ppm": max_fwhm,
            "adaptive_min_distance_ppm": median_fwhm * self.fwhm_factor,
            "num_peaks_analyzed": len(peak_indices),
        }

    def _estimate_min_distance(
        self,
        data: np.ndarray,
        ppm_per_point: float,
        abs_threshold: float,
    ) -> float:
        """Estimate minimum distance from line widths.

        Args:
            data: Spectrum intensity data
            ppm_per_point: PPM per data point
            abs_threshold: Absolute intensity threshold

        Returns:
            Adaptive minimum distance in ppm
        """
        # First pass: find peaks with very loose distance criterion
        initial_distance = max(1, int(0.01 / ppm_per_point))  # ~0.01 ppm minimum

        peak_indices, _ = find_peaks(
            data,
            height=abs_threshold,
            distance=initial_distance,
        )

        if len(peak_indices) < 2:
            return self.fallback_min_distance_ppm

        # Measure FWHM for detected peaks
        try:
            widths_points, _, _, _ = peak_widths(data, peak_indices, rel_height=0.5)
            widths_ppm = widths_points * ppm_per_point

            # Filter unreasonably wide peaks
            reasonable_widths = widths_ppm[widths_ppm < 1.0]
            if len(reasonable_widths) == 0:
                return self.fallback_min_distance_ppm

            median_fwhm = np.median(reasonable_widths)
            return float(median_fwhm * self.fwhm_factor)

        except Exception:
            return self.fallback_min_distance_ppm
