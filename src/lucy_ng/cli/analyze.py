"""CLI commands for analysis tools."""

import json
import re

import click

from lucy_ng.processing import AdaptivePeakPicker
from lucy_ng.readers import BrukerReader


@click.group()
def analyze() -> None:
    """Analysis tools for structure elucidation."""
    pass


@analyze.command("symmetry")
@click.argument("formula")
@click.argument("c13_path", type=click.Path(exists=True))
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
def analyze_symmetry(
    formula: str, c13_path: str, threshold: float | None, output_format: str
) -> None:
    """Compare observed 13C peaks with expected carbon count from formula.

    FORMULA is the molecular formula (e.g., C13H18O2).
    C13_PATH is the path to the 13C Bruker experiment.

    Returns raw comparison of observed signal count vs expected carbon count.
    The AI agent interprets the difference using symmetry detection knowledge.
    """
    # Read 1D spectrum
    spectrum = BrukerReader.read_1d(c13_path)

    # Pick peaks
    picker = AdaptivePeakPicker()
    if threshold is not None:
        peaks = picker.pick_peaks(spectrum, threshold=threshold)
    else:
        peaks = picker.pick_peaks(spectrum)

    # Parse carbon count from formula
    match = re.search(r'C(\d+)', formula)
    if not match:
        click.echo("Error: Could not parse carbon count from formula", err=True)
        raise SystemExit(1)

    expected_carbons = int(match.group(1))
    observed_peaks = len(peaks.peaks)
    difference = expected_carbons - observed_peaks

    if output_format == "json":
        data = {
            "formula": formula,
            "expected_carbons": expected_carbons,
            "observed_peaks": observed_peaks,
            "difference": difference,
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Symmetry Analysis for {formula}")
        click.echo(f"  Expected carbons: {expected_carbons}")
        click.echo(f"  Observed peaks: {observed_peaks}")
        click.echo(f"  Difference: {difference}")
        if difference > 0:
            click.echo(f"  → {difference} carbons may be equivalent due to symmetry")
        elif difference < 0:
            click.echo(f"  → Warning: More peaks than expected carbons")
