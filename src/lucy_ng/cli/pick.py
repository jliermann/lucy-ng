"""CLI commands for peak picking from NMR spectra."""

import json

import click
import numpy as np

from lucy_ng.processing import (
    AdaptivePeakPicker,
    PeakPicker2D,
)
from lucy_ng.readers import BrukerReader


@click.group()
def pick() -> None:
    """Peak picking from spectra."""
    pass


@pick.command("1d")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=None,
    help="Peak threshold (auto if not set).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def pick_1d(path: str, threshold: float | None, output_format: str) -> None:
    """Pick peaks from a 1D spectrum.

    PATH is the path to the Bruker experiment directory.

    Automatically detects negative peaks in spectra that contain them
    (e.g., DEPT-135 where CH2 peaks are negative).
    """
    spectrum = BrukerReader.read_1d(path)

    # Auto-detect negative peaks: if spectrum has significant negative values
    # (e.g., DEPT-135 CH2 peaks), enable negative peak detection automatically.
    effective_threshold = threshold if threshold is not None else 0.05
    max_abs = float(np.max(np.abs(spectrum.data)))
    has_significant_negative = bool(np.min(spectrum.data) < -effective_threshold * max_abs)

    # When an explicit threshold is given, disable SNR mode to preserve legacy behaviour.
    # When threshold is None (default), use SNR mode (MAD/CDCl3-aware threshold).
    use_snr = threshold is None
    if threshold is not None:
        peaks = AdaptivePeakPicker.pick_peaks(
            spectrum,
            threshold=threshold,
            detect_negative=has_significant_negative,
            use_snr=use_snr,
        )
    else:
        peaks = AdaptivePeakPicker.pick_peaks(
            spectrum,
            detect_negative=has_significant_negative,
            use_snr=use_snr,
        )

    if output_format == "json":
        data = {
            "count": len(peaks.peaks),
            "noise_sigma": peaks.noise_sigma,  # None for legacy/explicit-threshold callers
            "negative_detected": has_significant_negative,
            "peaks": [
                {
                    "ppm": p.position,
                    "intensity": p.intensity,
                    "snr": p.snr,  # None for explicit-threshold callers
                }
                for p in peaks.peaks
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        if has_significant_negative:
            click.echo(
                f"Found {len(peaks.peaks)} peaks (negative peak detection enabled):"
            )
        else:
            click.echo(f"Found {len(peaks.peaks)} peaks:")
        for p in sorted(peaks.peaks, key=lambda x: -x.position):
            click.echo(f"  {p.position:8.2f} ppm  (intensity: {p.intensity:.2e})")


@pick.command("2d")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.05,
    help="Peak threshold (default: 0.05).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def pick_2d(path: str, threshold: float, output_format: str) -> None:
    """Pick peaks from a 2D spectrum.

    PATH is the path to the Bruker experiment directory.
    """
    spectrum = BrukerReader.read_2d(path)
    peaks = PeakPicker2D.pick_peaks(spectrum, threshold=threshold)

    if output_format == "json":
        data = {
            "experiment_type": spectrum.experiment_type,
            "count": len(peaks.peaks),
            "peaks": [
                {
                    "f1_position": p.f1_position,
                    "f2_position": p.f2_position,
                    "intensity": p.intensity,
                }
                for p in peaks.peaks
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Found {len(peaks.peaks)} peaks in {spectrum.experiment_type}:")
        for p in sorted(peaks.peaks, key=lambda x: (-x.f1_position, x.f2_position)):
            click.echo(f"  F1: {p.f1_position:7.2f}  F2: {p.f2_position:6.2f}  (int: {p.intensity:.2e})")


@pick.command("hsqc")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.05,
    help="Peak threshold (default: 0.05).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def pick_hsqc(path: str, threshold: float, output_format: str) -> None:
    """Pick raw HSQC peaks above threshold.

    PATH is the path to the HSQC Bruker experiment directory.

    Returns raw cross-peaks without DEPT-guided filtering. The AI agent
    applies DEPT-guided filtering logic using skill knowledge.
    """
    spectrum = BrukerReader.read_2d(path)
    peaks = PeakPicker2D.pick_peaks(spectrum, threshold=threshold)

    if output_format == "json":
        data = {
            "experiment_type": spectrum.experiment_type,
            "count": len(peaks.peaks),
            "peaks": [
                {
                    "f1_position": p.f1_position,
                    "f2_position": p.f2_position,
                    "intensity": p.intensity,
                }
                for p in peaks.peaks
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Found {len(peaks.peaks)} peaks in {spectrum.experiment_type}:")
        for p in sorted(peaks.peaks, key=lambda x: (-x.f1_position, x.f2_position)):
            click.echo(f"  F1: {p.f1_position:7.2f}  F2: {p.f2_position:6.2f}  (int: {p.intensity:.2e})")


@pick.command("hmbc")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.05,
    help="Peak threshold (default: 0.05).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def pick_hmbc(path: str, threshold: float, output_format: str) -> None:
    """Pick raw HMBC peaks above threshold.

    PATH is the path to the HMBC Bruker experiment directory.

    Returns raw cross-peaks without cross-validation filtering. The AI agent
    applies HMBC filtering logic using skill knowledge.
    """
    spectrum = BrukerReader.read_2d(path)
    peaks = PeakPicker2D.pick_peaks(spectrum, threshold=threshold)

    if output_format == "json":
        data = {
            "experiment_type": spectrum.experiment_type,
            "count": len(peaks.peaks),
            "peaks": [
                {
                    "f1_position": p.f1_position,
                    "f2_position": p.f2_position,
                    "intensity": p.intensity,
                }
                for p in peaks.peaks
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Found {len(peaks.peaks)} peaks in {spectrum.experiment_type}:")
        for p in sorted(peaks.peaks, key=lambda x: (-x.f1_position, x.f2_position)):
            click.echo(f"  F1: {p.f1_position:7.2f}  F2: {p.f2_position:6.2f}  (int: {p.intensity:.2e})")
