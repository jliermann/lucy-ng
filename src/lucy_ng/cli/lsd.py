"""CLI commands for LSD structure elucidation."""

import json
from pathlib import Path

import click

from lucy_ng.lsd import LSDInputGenerator, LSDProblem, LSDRunner
from lucy_ng.processing import DEPTGuidedPicker
from lucy_ng.processing.hmbc_guided_picker import HMBCGuidedPicker
from lucy_ng.readers import BrukerReader


@click.group()
def lsd() -> None:
    """LSD structure elucidation."""
    pass


@lsd.command("check")
def lsd_check() -> None:
    """Check if LSD is installed and available."""
    if LSDRunner.is_available():
        click.echo("LSD is available")
    else:
        click.echo("LSD is not installed or not in PATH", err=True)
        raise SystemExit(1)


@lsd.command("generate")
@click.argument("data_dir", type=click.Path(exists=True))
@click.argument("formula")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file (stdout if not set).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def lsd_generate(
    data_dir: str, formula: str, output: str | None, output_format: str
) -> None:
    """Generate LSD input file from NMR data directory.

    DATA_DIR is the directory containing Bruker experiments.
    FORMULA is the molecular formula (e.g., C13H18O2).

    The command auto-detects experiment types from Bruker directories
    and requires at minimum: HSQC and DEPT-135 experiments.
    """
    data_path = Path(data_dir)

    # Find experiments by checking subdirectories
    experiments: dict[str, Path] = {}
    for subdir in sorted(data_path.iterdir()):
        if subdir.is_dir() and subdir.name.isdigit():
            try:
                # Try reading as 2D first, then 1D
                try:
                    spec2d = BrukerReader.read_2d(str(subdir))
                    experiments[spec2d.experiment_type.upper()] = subdir
                except Exception:
                    spec1d = BrukerReader.read_1d(str(subdir))
                    # Distinguish DEPT from regular 13C
                    pulse_prog = spec1d.metadata.get("pulse_program", "").lower()
                    if "dept135" in pulse_prog or "dept-135" in pulse_prog:
                        experiments["DEPT135"] = subdir
                    elif "dept90" in pulse_prog or "dept-90" in pulse_prog:
                        experiments["DEPT90"] = subdir
                    elif "dept" in pulse_prog:
                        # Generic DEPT, assume 135
                        experiments["DEPT135"] = subdir
                    elif spec1d.nucleus == "13C":
                        experiments["13C"] = subdir
                    elif spec1d.nucleus == "1H":
                        experiments["1H"] = subdir
            except Exception:
                pass

    # Check required experiments
    if "HSQC" not in experiments:
        click.echo("Error: HSQC experiment not found in data directory", err=True)
        raise SystemExit(1)

    if "DEPT135" not in experiments:
        click.echo("Error: DEPT-135 experiment not found in data directory", err=True)
        raise SystemExit(1)

    # Read required spectra
    hsqc = BrukerReader.read_2d(str(experiments["HSQC"]))
    dept135 = BrukerReader.read_1d(str(experiments["DEPT135"]))

    # DEPT-guided HSQC picking
    dept_result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)

    # Optional: HMBC
    hmbc_result = None
    if "HMBC" in experiments:
        hmbc = BrukerReader.read_2d(str(experiments["HMBC"]))
        # Use 13C if available for HMBC filtering
        c13 = None
        if "13C" in experiments:
            c13 = BrukerReader.read_1d(str(experiments["13C"]))

        hmbc_result = HMBCGuidedPicker.pick_hmbc_peaks_from_spectra(
            hmbc=hmbc,
            carbon_spectrum=c13,
            hsqc=hsqc,
            dept135=dept135,
        )

    # Generate LSD problem
    problem = LSDInputGenerator.from_dept_result(
        dept_result=dept_result,
        hmbc_peaks=hmbc_result.peaks if hmbc_result else None,
        molecular_formula=formula,
        name=data_path.name,
    )

    # Generate output
    lsd_content = LSDInputGenerator.generate(problem)

    if output_format == "json":
        data = {
            "molecular_formula": formula,
            "atom_count": len(problem.atoms),
            "correlation_count": len(problem.correlations),
            "experiments_found": list(experiments.keys()),
            "lsd_content": lsd_content,
        }
        output_text = json.dumps(data, indent=2)
    else:
        output_text = lsd_content

    if output:
        Path(output).write_text(output_text)
        click.echo(f"Written to {output}")
    else:
        click.echo(output_text)


@lsd.command("run")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--timeout",
    type=int,
    default=60,
    help="Timeout in seconds.",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Directory for solution files.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def lsd_run(
    input_file: str, timeout: int, output_dir: str | None, output_format: str
) -> None:
    """Run LSD on an input file.

    INPUT_FILE is the path to the LSD input file.
    """
    if not LSDRunner.is_available():
        click.echo("Error: LSD is not installed or not in PATH", err=True)
        raise SystemExit(1)

    # Read input file and create problem
    input_content = Path(input_file).read_text()

    # Parse basic info from content
    atom_count = input_content.count("\nMULT ")
    corr_count = input_content.count("\nHMBC ") + input_content.count("\nHSQC ")

    # Run LSD
    runner = LSDRunner()
    result = runner.run_file(
        input_file=Path(input_file),
        output_dir=Path(output_dir) if output_dir else None,
        timeout=timeout,
    )

    if output_format == "json":
        data = {
            "success": result.success,
            "solution_count": result.solution_count,
            "return_code": result.return_code,
            "output_files": [str(f) for f in result.output_files],
            "stderr": result.stderr,
        }
        click.echo(json.dumps(data, indent=2))
    else:
        if result.success:
            click.echo(f"LSD completed successfully")
            click.echo(f"  Solutions found: {result.solution_count}")
            if result.output_files:
                click.echo(f"  Output files:")
                for f in result.output_files:
                    click.echo(f"    - {f}")
        else:
            click.echo(f"LSD failed (return code: {result.return_code})")
            if result.stderr:
                click.echo(f"  Error: {result.stderr[:500]}")
