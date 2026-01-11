"""CLI commands for NMR chemical shift prediction."""

import json
from pathlib import Path

import click

from lucy_ng.prediction import C13Predictor, HOSELookupTable


# Default lookup table location
DEFAULT_TABLE_PATH = Path("data/reference/hose_lookup.json.gz")
HOME_TABLE_PATH = Path.home() / ".lucy" / "hose_lookup.json.gz"


def find_lookup_table() -> Path | None:
    """Find lookup table in default locations."""
    candidates = [
        DEFAULT_TABLE_PATH,
        HOME_TABLE_PATH,
        Path("hose_lookup.json.gz"),
        Path("hose_lookup.json"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


@click.group()
def predict() -> None:
    """Predict NMR chemical shifts from structure."""
    pass


@predict.command("c13")
@click.argument("smiles")
@click.option(
    "--table",
    "-t",
    type=click.Path(exists=True),
    default=None,
    help="Path to HOSE lookup table. Uses default if not specified.",
)
@click.option(
    "--max-radius",
    "-r",
    type=int,
    default=6,
    help="Maximum HOSE radius (default: 6).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def predict_c13(
    smiles: str,
    table: str | None,
    max_radius: int,
    output_format: str,
) -> None:
    """Predict 13C NMR chemical shifts for a molecule.

    SMILES is the molecular structure in SMILES format.

    Predicts chemical shifts using HOSE code lookup against a reference database.
    Falls back to shorter HOSE radii when exact matches aren't found.

    Example:

        lucy predict c13 "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
    """
    # Find lookup table
    table_path = Path(table) if table else find_lookup_table()
    if table_path is None or not table_path.exists():
        click.echo(
            "Error: No HOSE lookup table found. Build one with:\n"
            "  lucy predict build-table <coconut.sd>",
            err=True,
        )
        raise SystemExit(1)

    # Load predictor
    try:
        predictor = C13Predictor.from_table_file(table_path, max_radius=max_radius)
    except Exception as e:
        click.echo(f"Error loading lookup table: {e}", err=True)
        raise SystemExit(1)

    # Predict
    result = predictor.predict_from_smiles(smiles)

    if output_format == "json":
        data = {
            "smiles": result.smiles,
            "carbon_count": result.carbon_count,
            "success_count": result.success_count,
            "success_rate": result.success_rate,
            "predictions": [
                {
                    "atom_index": p.atom_index,
                    "shift": p.shift,
                    "confidence": p.confidence,
                    "radius_used": p.radius_used,
                    "match_count": p.match_count,
                    "std_dev": round(p.std_dev, 2),
                    "min_shift": p.min_shift,
                    "max_shift": p.max_shift,
                    "hose_code": p.hose_code,
                }
                for p in result.get_shifts_sorted()
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(result.summary())


@predict.command("build-table")
@click.argument("sd_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=str(DEFAULT_TABLE_PATH),
    help=f"Output file path (default: {DEFAULT_TABLE_PATH}).",
)
@click.option(
    "--max-radius",
    "-r",
    type=int,
    default=6,
    help="Maximum HOSE radius (default: 6).",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=None,
    help="Limit number of molecules to process (for testing).",
)
@click.option(
    "--no-compress",
    is_flag=True,
    help="Don't compress output file.",
)
def build_table(
    sd_path: str,
    output: str,
    max_radius: int,
    limit: int | None,
    no_compress: bool,
) -> None:
    """Build HOSE lookup table from COCONUT SD file.

    SD_PATH is the path to the COCONUT SD file with predicted 13C shifts.

    This is a one-time operation that builds the lookup table for predictions.
    The resulting table file can be reused for all future predictions.

    Example:

        lucy predict build-table data/reference/coconut_predicted.sd
    """
    click.echo(f"Building HOSE lookup table from: {sd_path}")
    click.echo(f"Max radius: {max_radius}")
    if limit:
        click.echo(f"Limit: {limit} molecules")

    try:
        table = HOSELookupTable.build_from_coconut(
            sd_path=Path(sd_path),
            max_radius=max_radius,
            progress=True,
            limit=limit,
        )
    except Exception as e:
        click.echo(f"Error building table: {e}", err=True)
        raise SystemExit(1)

    # Ensure output directory exists
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save table
    click.echo(f"\nSaving to: {output_path}")
    table.save(output_path, compress=not no_compress)

    click.echo(f"\nTable built successfully:")
    click.echo(f"  Molecules processed: {table.molecule_count:,}")
    click.echo(f"  Unique HOSE codes: {table.unique_codes:,}")
    click.echo(f"  Total entries: {table.total_entries:,}")


@predict.command("table-info")
@click.option(
    "--table",
    "-t",
    type=click.Path(exists=True),
    default=None,
    help="Path to HOSE lookup table.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def table_info(
    table: str | None,
    output_format: str,
) -> None:
    """Show information about a HOSE lookup table."""
    # Find lookup table
    table_path = Path(table) if table else find_lookup_table()
    if table_path is None or not table_path.exists():
        click.echo("Error: No HOSE lookup table found.", err=True)
        raise SystemExit(1)

    try:
        lookup = HOSELookupTable.load(table_path)
    except Exception as e:
        click.echo(f"Error loading table: {e}", err=True)
        raise SystemExit(1)

    if output_format == "json":
        data = {
            "path": str(table_path),
            "molecule_count": lookup.molecule_count,
            "unique_codes": lookup.unique_codes,
            "total_entries": lookup.total_entries,
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"HOSE Lookup Table: {table_path}")
        click.echo(f"  Molecules: {lookup.molecule_count:,}")
        click.echo(f"  Unique HOSE codes: {lookup.unique_codes:,}")
        click.echo(f"  Total entries: {lookup.total_entries:,}")
        if lookup.unique_codes > 0:
            avg_entries = lookup.total_entries / lookup.unique_codes
            click.echo(f"  Avg entries per code: {avg_entries:.1f}")
