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
