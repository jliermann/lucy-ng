"""CLI commands for fragment library management."""

from __future__ import annotations

from pathlib import Path

import click

from lucy_ng.database import DatabaseManager
from lucy_ng.fragments import FragmentDatabaseManager
from lucy_ng.fragments.extractor import SSCExtractor

DEFAULT_FRAGMENTS_DB = Path("data/reference/lucy-ng-fragments.db")


@click.group()
def fragment() -> None:
    """Fragment library management and search."""


@fragment.command()
@click.argument("db_path", type=click.Path(path_type=Path), default=DEFAULT_FRAGMENTS_DB)
def info(db_path: Path) -> None:
    """Show fragment database statistics.

    Display information about a fragment database including schema version,
    SSC count, bin size, and file size.

    Example:

        lucy fragment info data/reference/lucy-ng-fragments.db
    """
    if not db_path.exists():
        click.echo(
            f"Error: Fragment database not found: {db_path}\n"
            "Run 'lucy fragment build' to create it, or specify a path with"
            " 'lucy fragment info <path>'",
            err=True,
        )
        raise click.Abort()

    with FragmentDatabaseManager(db_path) as db:
        version = db.get_schema_version()
        if version != 7:
            click.echo(
                f"Warning: Expected schema version 7, found {version}."
                " This may not be a fragment database.",
                err=True,
            )

        ssc_count = db.get_ssc_count()
        bin_size = db.get_bin_size()
        file_size_mb = db_path.stat().st_size / 1_000_000

        click.echo(f"Fragment database: {db_path}")
        click.echo(f"  Schema version: {version}")
        click.echo(f"  SSC count: {ssc_count:,}")
        click.echo(f"  Bin size: {bin_size:.1f} ppm")
        click.echo(f"  File size: {file_size_mb:.1f} MB")


@fragment.command()
@click.argument("compound_db", type=click.Path(exists=True, path_type=Path))
@click.argument("fragment_db", type=click.Path(path_type=Path), default=DEFAULT_FRAGMENTS_DB)
@click.option(
    "--chunk-size",
    default=1000,
    type=int,
    show_default=True,
    help="Compounds per checkpoint batch",
)
@click.option(
    "--sample",
    type=int,
    default=None,
    help="Process only N compounds (for bin-size validation)",
)
@click.option(
    "--resume/--fresh",
    default=True,
    help="Resume from checkpoint (default) or restart from scratch",
)
def build(
    compound_db: Path,
    fragment_db: Path,
    chunk_size: int,
    sample: int | None,
    resume: bool,
) -> None:
    """Build fragment (SSC) database from compound database.

    Extracts substructure-subspectrum correlations from all compounds with
    atom-indexed 13C shifts. Supports checkpointing for multi-hour runs.

    COMPOUND_DB: Path to lucy-ng-derep.db (source compounds).
    FRAGMENT_DB: Path to lucy-ng-fragments.db (output, created if not exists).

    \b
    Examples:
        # Validate bin size on 1000 compounds
        lucy fragment build data/reference/lucy-ng-derep.db --sample 1000

        # Full extraction (resumable)
        lucy fragment build data/reference/lucy-ng-derep.db

        # Restart from scratch
        lucy fragment build data/reference/lucy-ng-derep.db --fresh
    """
    with DatabaseManager(compound_db) as compound_db_mgr, \
         FragmentDatabaseManager(fragment_db) as fragment_db_mgr:
        fragment_db_mgr.create_tables()

        extractor = SSCExtractor(
            compound_db=compound_db_mgr,
            fragment_db=fragment_db_mgr,
        )

        # --resume gives resume=True, --fresh gives resume=False
        result = extractor.run(
            chunk_size=chunk_size,
            sample=sample,
            resume=resume,
            fresh=not resume,
        )

        click.echo(f"Compounds processed: {result.compounds_processed:,}")
        click.echo(f"Compounds skipped:   {result.compounds_skipped:,}")
        click.echo(f"SSCs extracted:      {result.sscs_extracted:,}")
        click.echo(f"SSCs duplicate:      {result.sscs_duplicate:,}")

        # Self-search recall validation when sample mode used with 100+ compounds
        if sample is not None and sample >= 100:
            click.echo("")
            click.echo("Running self-search recall validation...")
            recall = extractor.validate_self_search(sample_size=100)
            hits = round(recall * 100)
            click.echo(f"Self-search recall: {recall:.1%} ({hits}/100)")
            if recall < 0.99:
                click.echo(
                    "WARNING: Recall below 99% — bin size may need adjustment",
                    err=True,
                )

        total_count = fragment_db_mgr.get_ssc_count()
        click.echo("")
        click.echo(f"Fragment DB total SSCs: {total_count:,}")
