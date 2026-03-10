"""Tests for database schema v6 to v7 migration."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from lucy_ng.database.manager import DatabaseManager
from lucy_ng.database.models import CouplingPathStatsRecord
from lucy_ng.database.schema import (
    CREATE_COMPOUNDS_TABLE,
    CREATE_FORMULA_INDEX,
    CREATE_HOSE_STATS_INDEX,
    CREATE_HOSE_STATS_MEAN_RADIUS_INDEX,
    CREATE_HOSE_STATS_TABLE,
    CREATE_SCHEMA_META_TABLE,
    CREATE_SHIFTS_COMPOUND_INDEX,
    CREATE_SHIFTS_TABLE,
    migrate_v3_to_v4,
    migrate_v4_to_v5,
    migrate_v5_to_v6,
    migrate_v6_to_v7,
)


def create_v6_database(db_path: Path) -> None:
    """Create a v6 database with hose_stats and bond_pair_stats data."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create v3 schema first
    for statement in [
        CREATE_COMPOUNDS_TABLE,
        CREATE_SHIFTS_TABLE,
        CREATE_FORMULA_INDEX,
        CREATE_SHIFTS_COMPOUND_INDEX,
        CREATE_SCHEMA_META_TABLE,
    ]:
        cursor.execute(statement)

    # Create v3 hose_stats table (without hybridisation/neighbour/ring columns)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hose_stats (
            hose_code TEXT NOT NULL,
            radius INTEGER NOT NULL,
            mean REAL NOT NULL,
            std REAL NOT NULL,
            count INTEGER NOT NULL,
            m2 REAL NOT NULL DEFAULT 0.0,
            PRIMARY KEY (hose_code, radius)
        )
        """
    )
    cursor.execute(CREATE_HOSE_STATS_INDEX)

    # Set schema version to v3
    cursor.execute(
        "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
        ("schema_version", "3"),
    )
    conn.commit()

    # Migrate to v4 (adds hybridisation columns)
    migrate_v3_to_v4(conn)

    # Migrate to v5 (adds neighbour columns)
    migrate_v4_to_v5(conn)

    # Migrate to v6 (adds bond_pair_stats table and ring columns)
    migrate_v5_to_v6(conn)

    # Insert test hose_stats data
    cursor.execute(
        """
        INSERT INTO hose_stats
            (hose_code, radius, mean, std, count, m2,
             sp3_count, sp2_count, sp1_count,
             has_carbon_neighbor, has_oxygen_neighbor, has_nitrogen_neighbor,
             has_sulfur_neighbor, has_halogen_neighbor,
             in_3ring, in_4ring, in_aromatic)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("C-4;C(//)", 1, 25.0, 5.0, 100, 250.0, 80, 15, 5, 100, 10, 5, 0, 0, 2, 0, 50),
    )

    # Insert test bond_pair_stats data
    cursor.execute(
        """
        INSERT INTO bond_pair_stats
            (formula_normalized, element1, element2, compound_count, total_compounds, frequency)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("C13H18O2", "N", "O", 5, 100, 0.05),
    )

    conn.commit()
    conn.close()


def test_migrate_v6_to_v7() -> None:
    """Test migration from v6 to v7 creates coupling_path_stats table and indices."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        # Create v6 database
        create_v6_database(db_path)

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Verify starting version
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'")
        row = cursor.fetchone()
        assert row is not None
        assert int(row["value"]) == 6

        # Perform migration
        migrate_v6_to_v7(conn)

        # Verify schema_version updated to 7
        cursor.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'")
        row = cursor.fetchone()
        assert row is not None
        assert int(row["value"]) == 7

        # Verify coupling_path_stats table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='coupling_path_stats'"
        )
        assert cursor.fetchone() is not None

        # Verify table has correct columns
        cursor.execute("PRAGMA table_info(coupling_path_stats)")
        columns = {row["name"]: row for row in cursor.fetchall()}
        assert "carbon_hose" in columns
        assert "h_carbon_hose" in columns
        assert "bond_distance" in columns
        assert "count" in columns

        # Verify PRIMARY KEY (carbon_hose, h_carbon_hose, bond_distance)
        # SQLite encodes PK in the table definition
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='coupling_path_stats'"
        )
        table_sql = cursor.fetchone()["sql"]
        assert "PRIMARY KEY" in table_sql
        assert "carbon_hose" in table_sql
        assert "h_carbon_hose" in table_sql
        assert "bond_distance" in table_sql

        # Verify idx_coupling_path_pair index exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_coupling_path_pair'"
        )
        assert cursor.fetchone() is not None

        # Verify idx_coupling_path_carbon index exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_coupling_path_carbon'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    finally:
        db_path.unlink()


def test_migrate_v6_to_v7_preserves_existing_data() -> None:
    """Test that v6->v7 migration preserves hose_stats and bond_pair_stats data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        create_v6_database(db_path)

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        migrate_v6_to_v7(conn)

        cursor = conn.cursor()

        # Verify hose_stats data preserved
        cursor.execute("SELECT * FROM hose_stats WHERE hose_code = 'C-4;C(//)' AND radius = 1")
        row = cursor.fetchone()
        assert row is not None
        assert row["mean"] == 25.0
        assert row["count"] == 100
        assert row["in_aromatic"] == 50

        # Verify bond_pair_stats data preserved
        cursor.execute(
            "SELECT * FROM bond_pair_stats WHERE formula_normalized = 'C13H18O2'"
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["element1"] == "N"
        assert row["element2"] == "O"
        assert row["compound_count"] == 5

        conn.close()

    finally:
        db_path.unlink()


def test_coupling_path_stats_record_model() -> None:
    """Test CouplingPathStatsRecord Pydantic model fields and instantiation."""
    record = CouplingPathStatsRecord(
        carbon_hose="C-3;=C(=C/=C/)",
        h_carbon_hose="C-3;=C(=C/=C/)",
        bond_distance=4,
        count=42,
    )

    assert record.carbon_hose == "C-3;=C(=C/=C/)"
    assert record.h_carbon_hose == "C-3;=C(=C/=C/)"
    assert record.bond_distance == 4
    assert record.count == 42


def test_coupling_path_stats_record_roundtrip() -> None:
    """Test CouplingPathStatsRecord roundtrips through dict correctly."""
    record = CouplingPathStatsRecord(
        carbon_hose="C-4;C(CC/)",
        h_carbon_hose="C-3;=C(=CC/)",
        bond_distance=3,
        count=100,
    )

    data = record.model_dump()
    restored = CouplingPathStatsRecord(**data)

    assert restored.carbon_hose == record.carbon_hose
    assert restored.h_carbon_hose == record.h_carbon_hose
    assert restored.bond_distance == record.bond_distance
    assert restored.count == record.count


def test_migrate_to_v7_via_manager() -> None:
    """Test DatabaseManager.migrate_to_v7() chains from v5 through v6 to v7."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        # Create a v5 database (without v6 migration)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        for statement in [
            CREATE_COMPOUNDS_TABLE,
            CREATE_SHIFTS_TABLE,
            CREATE_FORMULA_INDEX,
            CREATE_SHIFTS_COMPOUND_INDEX,
            CREATE_SCHEMA_META_TABLE,
        ]:
            cursor.execute(statement)

        # v3 hose_stats
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hose_stats (
                hose_code TEXT NOT NULL,
                radius INTEGER NOT NULL,
                mean REAL NOT NULL,
                std REAL NOT NULL,
                count INTEGER NOT NULL,
                m2 REAL NOT NULL DEFAULT 0.0,
                PRIMARY KEY (hose_code, radius)
            )
            """
        )
        cursor.execute(CREATE_HOSE_STATS_INDEX)

        cursor.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
            ("schema_version", "3"),
        )
        conn.commit()

        migrate_v3_to_v4(conn)
        migrate_v4_to_v5(conn)
        conn.close()

        # Use DatabaseManager to migrate to v7
        with DatabaseManager(db_path) as db:
            assert db.get_schema_version() == 5

            result = db.migrate_to_v7()

            assert result is True
            assert db.get_schema_version() == 7

            # Verify coupling_path_stats table was created
            cursor = db.connection.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='coupling_path_stats'"
            )
            assert cursor.fetchone() is not None

            # Verify bond_pair_stats table was also created (via v6 chain)
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='bond_pair_stats'"
            )
            assert cursor.fetchone() is not None

    finally:
        db_path.unlink()


def test_migrate_to_v7_idempotent() -> None:
    """Test that calling migrate_to_v7() twice returns False on second call."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        with DatabaseManager(db_path) as db:
            db.create_tables()

            # First call: should perform migration (or already be at v7 from create_tables)
            version = db.get_schema_version()

            # Force to v6 for testing idempotency properly
            # If already at v7, just test the idempotent case directly
            if version == 7:
                result = db.migrate_to_v7()
                assert result is False
            else:
                # Migrate to v7
                result1 = db.migrate_to_v7()
                assert result1 is True

                # Second call should be idempotent
                result2 = db.migrate_to_v7()
                assert result2 is False

    finally:
        db_path.unlink()


# =============================================================================
# Task 1: Query method tests
# =============================================================================


def test_insert_and_query_coupling_path_stats() -> None:
    """Test insert_coupling_path_stats_batch and get_coupling_path_stats."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        with DatabaseManager(db_path) as db:
            db.create_tables()

            # Insert 3 records with different bond_distances for the same pair
            records = [
                CouplingPathStatsRecord(
                    carbon_hose="C-4;CC(//)",
                    h_carbon_hose="C-4;C(//)",
                    bond_distance=2,
                    count=50,
                ),
                CouplingPathStatsRecord(
                    carbon_hose="C-4;CC(//)",
                    h_carbon_hose="C-4;C(//)",
                    bond_distance=3,
                    count=200,
                ),
                CouplingPathStatsRecord(
                    carbon_hose="C-4;CC(//)",
                    h_carbon_hose="C-4;C(//)",
                    bond_distance=4,
                    count=30,
                ),
            ]

            inserted = db.insert_coupling_path_stats_batch(records)
            assert inserted == 3

            # Query exact pair — ordered by bond_distance ASC
            results = db.get_coupling_path_stats("C-4;CC(//)", "C-4;C(//)")
            assert len(results) == 3
            assert results[0].bond_distance == 2
            assert results[0].count == 50
            assert results[1].bond_distance == 3
            assert results[1].count == 200
            assert results[2].bond_distance == 4
            assert results[2].count == 30

            # All records carry correct HOSE codes
            for r in results:
                assert r.carbon_hose == "C-4;CC(//)"
                assert r.h_carbon_hose == "C-4;C(//)"

    finally:
        db_path.unlink()


def test_query_coupling_path_stats_nonexistent_pair() -> None:
    """Test that get_coupling_path_stats returns [] for a non-existent pair."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        with DatabaseManager(db_path) as db:
            db.create_tables()

            results = db.get_coupling_path_stats("NONEXISTENT-HOSE", "ALSO-NONEXISTENT")
            assert results == []

    finally:
        db_path.unlink()


def test_query_coupling_path_stats_by_carbon() -> None:
    """Test get_coupling_path_stats_by_carbon aggregates across h_carbon_hose values."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        with DatabaseManager(db_path) as db:
            db.create_tables()

            records = [
                CouplingPathStatsRecord(
                    carbon_hose="C-4;CC(//)",
                    h_carbon_hose="C-4;C(//)",
                    bond_distance=3,
                    count=100,
                ),
                CouplingPathStatsRecord(
                    carbon_hose="C-4;CC(//)",
                    h_carbon_hose="C-3;=C(//)",
                    bond_distance=2,
                    count=80,
                ),
                CouplingPathStatsRecord(
                    carbon_hose="C-4;CC(//)",
                    h_carbon_hose="C-3;=C(//)",
                    bond_distance=3,
                    count=40,
                ),
                # Different carbon_hose — should NOT be returned
                CouplingPathStatsRecord(
                    carbon_hose="C-3;=C(//)",
                    h_carbon_hose="C-4;C(//)",
                    bond_distance=3,
                    count=999,
                ),
            ]
            db.insert_coupling_path_stats_batch(records)

            results = db.get_coupling_path_stats_by_carbon("C-4;CC(//)")
            assert len(results) == 3

            # Ordered by bond_distance ASC
            assert results[0].bond_distance == 2
            assert results[1].bond_distance == 3
            # Both distance-3 entries are present
            d3_counts = {r.h_carbon_hose: r.count for r in results if r.bond_distance == 3}
            assert "C-4;C(//)" in d3_counts
            assert d3_counts["C-4;C(//)"] == 100

    finally:
        db_path.unlink()


def test_query_coupling_path_stats_by_carbon_nonexistent() -> None:
    """Test get_coupling_path_stats_by_carbon returns [] for non-existent carbon."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        with DatabaseManager(db_path) as db:
            db.create_tables()

            results = db.get_coupling_path_stats_by_carbon("NONEXISTENT-HOSE")
            assert results == []

    finally:
        db_path.unlink()


def test_coupling_path_stats_backward_compat_v6_db() -> None:
    """Test that query methods return [] on a v6 database (no coupling_path_stats table)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        # Create a v6 database (no coupling_path_stats table)
        create_v6_database(db_path)

        with DatabaseManager(db_path) as db:
            # Should not raise — should return empty list (backward compat)
            results_pair = db.get_coupling_path_stats("C-4;CC(//)", "C-4;C(//)")
            assert results_pair == []

            results_carbon = db.get_coupling_path_stats_by_carbon("C-4;CC(//)")
            assert results_carbon == []

    finally:
        db_path.unlink()


def test_insert_coupling_path_stats_batch_idempotent() -> None:
    """Test that INSERT OR REPLACE is idempotent (second insert updates count)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        with DatabaseManager(db_path) as db:
            db.create_tables()

            record = CouplingPathStatsRecord(
                carbon_hose="C-4;CC(//)",
                h_carbon_hose="C-4;C(//)",
                bond_distance=3,
                count=100,
            )
            db.insert_coupling_path_stats_batch([record])

            # Insert same key with updated count
            updated = CouplingPathStatsRecord(
                carbon_hose="C-4;CC(//)",
                h_carbon_hose="C-4;C(//)",
                bond_distance=3,
                count=999,
            )
            db.insert_coupling_path_stats_batch([updated])

            results = db.get_coupling_path_stats("C-4;CC(//)", "C-4;C(//)")
            assert len(results) == 1
            assert results[0].count == 999

    finally:
        db_path.unlink()
