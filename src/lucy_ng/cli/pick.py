"""CLI commands for peak picking from NMR spectra."""

import json

import click

from lucy_ng.processing import (
    AdaptivePeakPicker,
    DEPTGuidedPicker,
    PeakPicker2D,
)
from lucy_ng.processing.hmbc_guided_picker import HMBCGuidedPicker
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
    """
    spectrum = BrukerReader.read_1d(path)
    picker = AdaptivePeakPicker()
    peaks = picker.pick_peaks(spectrum, threshold=threshold) if threshold else picker.pick_peaks(spectrum)

    if output_format == "json":
        data = {
            "count": len(peaks.peaks),
            "peaks": [
                {
                    "ppm": p.position,
                    "intensity": p.intensity,
                }
                for p in peaks.peaks
            ],
        }
        click.echo(json.dumps(data, indent=2))
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
@click.argument("hsqc_path", type=click.Path(exists=True))
@click.argument("dept135_path", type=click.Path(exists=True))
@click.option(
    "--dept90",
    type=click.Path(exists=True),
    default=None,
    help="DEPT-90 path for CH/CH3 disambiguation.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def pick_hsqc(
    hsqc_path: str, dept135_path: str, dept90: str | None, output_format: str
) -> None:
    """Pick HSQC peaks using DEPT-guided algorithm.

    HSQC_PATH is the path to the HSQC experiment.
    DEPT135_PATH is the path to the DEPT-135 experiment.
    """
    hsqc = BrukerReader.read_2d(hsqc_path)
    dept135 = BrukerReader.read_1d(dept135_path)

    if dept90:
        dept90_spec = BrukerReader.read_1d(dept90)
        result = DEPTGuidedPicker.pick_hsqc_peaks_with_dept90(hsqc, dept135, dept90_spec)
    else:
        result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)

    if output_format == "json":
        data = {
            "dept_peaks_count": len(result.dept_peaks.peaks),
            "hsqc_peaks_count": len(result.peaks.peaks),
            "threshold_used": result.threshold_used,
            "iterations": result.iterations,
            "all_carbons_found": result.all_carbons_found,
            "carbon_multiplicities": result.carbon_multiplicities,
            "peaks": [
                {
                    "f1_position": p.f1_position,
                    "f2_position": p.f2_position,
                    "intensity": p.intensity,
                }
                for p in result.peaks.peaks
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(result.summary())


@pick.command("hmbc")
@click.argument("hmbc_path", type=click.Path(exists=True))
@click.argument("c13_path", type=click.Path(exists=True))
@click.argument("hsqc_path", type=click.Path(exists=True))
@click.option(
    "--dept135",
    type=click.Path(exists=True),
    default=None,
    help="Optional DEPT-135 path for extra carbon positions.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def pick_hmbc(
    hmbc_path: str,
    c13_path: str,
    hsqc_path: str,
    dept135: str | None,
    output_format: str,
) -> None:
    """Pick HMBC peaks using guided algorithm.

    HMBC_PATH is the path to the HMBC experiment.
    C13_PATH is the path to the 13C experiment.
    HSQC_PATH is the path to the HSQC experiment.

    The guided algorithm filters HMBC peaks to only include correlations
    where the carbon position matches known 13C/DEPT positions and the
    proton position matches HSQC proton positions.
    """
    hmbc = BrukerReader.read_2d(hmbc_path)
    c13 = BrukerReader.read_1d(c13_path)
    hsqc = BrukerReader.read_2d(hsqc_path)
    dept135_spec = BrukerReader.read_1d(dept135) if dept135 else None

    result = HMBCGuidedPicker.pick_hmbc_peaks_from_spectra(
        hmbc=hmbc,
        carbon_spectrum=c13,
        hsqc=hsqc,
        dept135=dept135_spec,
    )

    if output_format == "json":
        data = {
            "reference_carbons": len(result.carbon_positions),
            "reference_protons": len(result.proton_positions),
            "raw_peak_count": result.raw_peak_count,
            "validated_count": result.validated_count,
            "rejected_count": result.rejected_count,
            "peaks": [
                {
                    "f1_position": p.f1_position,
                    "f2_position": p.f2_position,
                    "intensity": p.intensity,
                }
                for p in result.peaks.peaks
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(result.summary())
