"""CLI commands for statistical detection of structural constraints."""

from pathlib import Path

import click

from lucy_ng.database import DatabaseFinder


@click.group()
def detect() -> None:
    """Statistical detection of structural constraints from shifts."""
    pass


@detect.command("hybridisation")
@click.argument("shift_ppm", type=float)
@click.option(
    "--db", "-d", type=click.Path(exists=True), default=None,
    help="Path to SQLite database with HOSE stats.",
)
@click.option(
    "--radius", "-r", type=int, default=3,
    help="HOSE radius for query (default: 3).",
)
@click.option(
    "--window", "-w", type=float, default=2.0,
    help="Shift window in ppm (default: +/- 2.0).",
)
@click.option(
    "--threshold", "-t", type=float, default=0.01,
    help="Minimum frequency to include (default: 0.01 = 1%).",
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "json"]), default="text",
    help="Output format.",
)
def hybridisation_command(
    shift_ppm: float,
    db: str | None,
    radius: int,
    window: float,
    threshold: float,
    output_format: str,
) -> None:
    """Detect hybridisation state from 13C chemical shift.

    Queries the HOSE statistics database for all entries within a shift
    window and computes sp3/sp2/sp1 frequency distributions. States
    below the frequency threshold are excluded.

    Examples:

        lucy detect hybridisation 130.5

        lucy detect hybridisation 25.0 --radius 4 --window 1.5

        lucy detect hybridisation 155.0 --format json
    """
    from lucy_ng.detection import StatisticalDetector

    # Find database
    db_path = Path(db) if db else DatabaseFinder.find_hose_database()
    if not db_path:
        click.echo(
            "Error: No HOSE database found.\n\n"
            "Options:\n"
            "  1. Download database: lucy database download\n"
            "  2. Specify path: lucy detect hybridisation 130.5 --db /path/to/db",
            err=True,
        )
        raise SystemExit(1)

    # Run detection
    try:
        detector = StatisticalDetector(db_path)
        result = detector.detect_hybridisation(
            shift_ppm, radius=radius, window_ppm=window, threshold=threshold
        )
        detector.close()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e

    # Output
    if output_format == "json":
        click.echo(result.model_dump_json(indent=2))
    else:
        click.echo(result.summary())

    # Warn if no data
    if result.warning:
        click.echo(f"\nWarning: {result.warning}", err=True)


@detect.command("neighbours")
@click.argument("shift_ppm", type=float)
@click.option(
    "--db", "-d", type=click.Path(exists=True), default=None,
    help="Path to SQLite database with HOSE stats.",
)
@click.option(
    "--radius", "-r", type=int, default=3,
    help="HOSE radius for query (default: 3).",
)
@click.option(
    "--window", "-w", type=float, default=2.0,
    help="Shift window in ppm (default: +/- 2.0).",
)
@click.option(
    "--min-frequency", type=float, default=0.01,
    help="Minimum frequency for forbidden threshold (default: 0.01 = 1%).",
)
@click.option(
    "--max-frequency", type=float, default=0.95,
    help="Maximum frequency for mandatory threshold (default: 0.95 = 95%).",
)
@click.option(
    "--mode", type=click.Choice(["strict", "relaxed"]), default="strict",
    help="strict: 1%/95% thresholds, relaxed: 0.1%/99% thresholds.",
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "json"]), default="text",
    help="Output format.",
)
def neighbours_command(
    shift_ppm: float,
    db: str | None,
    radius: int,
    window: float,
    min_frequency: float,
    max_frequency: float,
    mode: str,
    output_format: str,
) -> None:
    """Detect forbidden and mandatory bond partner elements from 13C shift.

    Queries the HOSE statistics database for all entries within a shift
    window and computes element frequency distributions. Elements below
    the forbidden threshold are classified as forbidden, elements above
    the mandatory threshold are classified as mandatory.

    Examples:

        lucy detect neighbours 170.5

        lucy detect neighbours 25.0 --mode relaxed

        lucy detect neighbours 130.5 --min-frequency 0.05 --max-frequency 0.99

        lucy detect neighbours 155.0 --format json
    """
    from lucy_ng.detection import StatisticalDetector

    # Apply mode thresholds (overrides --min-frequency/--max-frequency)
    if mode == "relaxed":
        min_frequency = 0.001  # 0.1%
        max_frequency = 0.99   # 99%

    # Find database
    db_path = Path(db) if db else DatabaseFinder.find_hose_database()
    if not db_path:
        click.echo(
            "Error: No HOSE database found.\n\n"
            "Options:\n"
            "  1. Download database: lucy database download\n"
            "  2. Specify path: lucy detect neighbours 170.5 --db /path/to/db",
            err=True,
        )
        raise SystemExit(1)

    # Run detection
    try:
        detector = StatisticalDetector(db_path)
        result = detector.detect_neighbours(
            shift_ppm,
            radius=radius,
            window_ppm=window,
            forbidden_threshold=min_frequency,
            mandatory_threshold=max_frequency,
        )
        detector.close()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e

    # Output
    if output_format == "json":
        click.echo(result.model_dump_json(indent=2))
    else:
        click.echo(result.summary())

    # Warn if no data
    if result.warning:
        click.echo(f"\nWarning: {result.warning}", err=True)


@detect.command("hhb")
@click.argument("formula", type=str)
@click.option(
    "--db", "-d", type=click.Path(exists=True), default=None,
    help="Path to SQLite database with bond pair stats.",
)
@click.option(
    "--threshold", "-t", type=float, default=0.01,
    help="Minimum frequency for allowed bond (default: 0.01 = 1%).",
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "json"]), default="text",
    help="Output format.",
)
def hhb_command(
    formula: str,
    db: str | None,
    threshold: float,
    output_format: str,
) -> None:
    """Detect allowed hetero-hetero bonds for a molecular formula.

    Queries the database for which heteroatom-heteroatom bonds (O-O, O-N,
    N-N, etc.) occur in compounds with the given formula. Bonds below the
    threshold are considered forbidden.

    The argument is a molecular formula (e.g., C10H14O2), NOT a shift value.

    Examples:

        lucy detect hhb C10H14O2

        lucy detect hhb C10H14O2 --threshold 0.05

        lucy detect hhb C10H14O2 --format json
    """
    from lucy_ng.detection import StatisticalDetector

    # Find database
    db_path = Path(db) if db else DatabaseFinder.find_hose_database()
    if not db_path:
        click.echo(
            "Error: No HOSE database found.\n\n"
            "Options:\n"
            "  1. Download database: lucy database download\n"
            "  2. Specify path: lucy detect hhb C10H14O2 --db /path/to/db",
            err=True,
        )
        raise SystemExit(1)

    # Run detection
    try:
        detector = StatisticalDetector(db_path)
        result = detector.detect_hhb(formula, threshold=threshold)
        detector.close()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e

    # Output
    if output_format == "json":
        click.echo(result.model_dump_json(indent=2))
    else:
        click.echo(result.summary())

    # Warn if no data
    if result.warning:
        click.echo(f"\nWarning: {result.warning}", err=True)


