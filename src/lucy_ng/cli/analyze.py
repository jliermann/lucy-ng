"""CLI commands for analysis tools."""

import json

import click

from lucy_ng.analysis import SymmetryAnalyzer
from lucy_ng.processing import DEPTGuidedPicker
from lucy_ng.readers import BrukerReader


@click.group()
def analyze() -> None:
    """Analysis tools for structure elucidation."""
    pass


@analyze.command("symmetry")
@click.argument("formula")
@click.argument("hsqc_path", type=click.Path(exists=True))
@click.argument("dept135_path", type=click.Path(exists=True))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def analyze_symmetry(
    formula: str, hsqc_path: str, dept135_path: str, output_format: str
) -> None:
    """Analyze molecular symmetry from spectroscopic data.

    FORMULA is the molecular formula (e.g., C13H18O2).
    HSQC_PATH is the path to the HSQC experiment.
    DEPT135_PATH is the path to the DEPT-135 experiment.

    This tool compares the expected atom count from the molecular formula
    with observed NMR signals to detect equivalent atoms due to symmetry.
    """
    hsqc = BrukerReader.read_2d(hsqc_path)
    dept135 = BrukerReader.read_1d(dept135_path)
    dept_result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)

    result = SymmetryAnalyzer.analyze(formula, dept_result, hsqc)

    if output_format == "json":
        data = {
            "molecular_formula": result.molecular_formula,
            "signal_count": result.signal_count,
            "expected_carbons": result.expected_carbons,
            "missing_carbons": result.missing_carbons,
            "has_symmetry": result.has_symmetry,
            "hydrogen_budget": {
                "expected_h": result.hydrogen_budget.expected_h,
                "total_accounted": result.hydrogen_budget.total_accounted,
                "missing_h": result.hydrogen_budget.missing_h,
                "has_equivalents": result.hydrogen_budget.has_equivalents,
            },
            "intensity_report": {
                "peak_count": len(result.intensity_report.peaks),
                "has_potential_equivalents": result.intensity_report.has_potential_equivalents,
                "high_intensity_peaks": [
                    {
                        "carbon_shift": p.carbon_shift,
                        "proton_shift": p.proton_shift,
                        "multiplicity": p.multiplicity,
                        "relative_intensity": p.relative_intensity,
                    }
                    for p in result.intensity_report.peaks
                    if p.is_potential_equivalent
                ],
            },
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(result.summary())
