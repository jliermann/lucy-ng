"""Tests for database schema migration from v3 to v4."""

import sqlite3
from pathlib import Path

from lucy_ng.database.manager import DatabaseManager
from lucy_ng.database.models import HOSEStatsRecord


def test_migrate_v3_to_v4(tmp_path: Path) -> None:
    """Test migration from v3 to v4 schema."""
    db_path = tmp_path / "test_migration.db"

    # Create a v3 database
    with DatabaseManager(db_path) as db:
        conn = db.connection
        cursor = conn.cursor()

        # Create v3 schema (without hybridisation columns)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hose_stats (
                hose_code TEXT NOT NULL,
                radius INTEGER NOT NULL,
                mean REAL NOT NULL,
                std REAL NOT NULL,
                count INTEGER NOT NULL,
                m2 REAL NOT NULL DEFAULT 0.0,
                PRIMARY KEY (hose_code, radius)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        cursor.execute(
            "INSERT INTO schema_meta (key, value) VALUES (?, ?)",
            ("schema_version", "3"),
        )

        # Insert some test data
        cursor.execute(
            """
            INSERT INTO hose_stats (hose_code, radius, mean, std, count, m2)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("C-4;C(//)", 3, 25.0, 2.0, 100, 400.0),
        )
        cursor.execute(
            """
            INSERT INTO hose_stats (hose_code, radius, mean, std, count, m2)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("C-3;C(//)", 3, 130.0, 5.0, 50, 1250.0),
        )
        conn.commit()

    # Verify v3 schema
    with DatabaseManager(db_path) as db:
        assert db.get_schema_version() == 3

        # Run migration
        migrated = db.migrate_to_v4()
        assert migrated is True

        # Verify v4 schema
        assert db.get_schema_version() == 4

        # Check that new columns exist with default 0 values
        conn = db.connection
        cursor = conn.cursor()
        cursor.execute(
            "SELECT hose_code, sp3_count, sp2_count, sp1_count FROM hose_stats"
        )
        rows = cursor.fetchall()
        assert len(rows) == 2
        for row in rows:
            assert row["sp3_count"] == 0
            assert row["sp2_count"] == 0
            assert row["sp1_count"] == 0

        # Check that index exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_hose_stats_mean_radius'
            """
        )
        assert cursor.fetchone() is not None

    # Re-open and verify no double migration
    with DatabaseManager(db_path) as db:
        migrated = db.migrate_to_v4()
        assert migrated is False  # Already at v4


def test_get_hose_stats_by_shift_window(tmp_path: Path) -> None:
    """Test shift-window detection query."""
    db_path = tmp_path / "test_shift_window.db"

    with DatabaseManager(db_path) as db:
        db.create_tables()

        # Insert test data with known mean values
        stats = [
            HOSEStatsRecord(
                hose_code="C-4;C(//)",
                radius=3,
                mean=25.0,
                std=2.0,
                count=100,
                sp3_count=95,
                sp2_count=5,
                sp1_count=0,
            ),
            HOSEStatsRecord(
                hose_code="C-3;C(//)",
                radius=3,
                mean=130.0,
                std=5.0,
                count=50,
                sp3_count=5,
                sp2_count=40,
                sp1_count=5,
            ),
            HOSEStatsRecord(
                hose_code="C-2;C(//)",
                radius=3,
                mean=155.0,
                std=3.0,
                count=30,
                sp3_count=0,
                sp2_count=25,
                sp1_count=5,
            ),
        ]
        db.insert_hose_stats_batch(stats)

        # Query with shift=130.0, window=2.0
        results = db.get_hose_stats_by_shift_window(
            shift_ppm=130.0,
            radius=3,
            window_ppm=2.0,
        )

        # Should only return the 130.0 entry
        assert len(results) == 1
        assert results[0].hose_code == "C-3;C(//)"
        assert results[0].mean == 130.0
        assert results[0].sp2_count == 40

        # Query with larger window
        results = db.get_hose_stats_by_shift_window(
            shift_ppm=130.0,
            radius=3,
            window_ppm=30.0,
        )

        # Should return both 130.0 and 155.0
        assert len(results) == 2
        mean_values = {r.mean for r in results}
        assert mean_values == {130.0, 155.0}


def test_shift_window_min_count(tmp_path: Path) -> None:
    """Test min_count filtering in shift-window query."""
    db_path = tmp_path / "test_min_count.db"

    with DatabaseManager(db_path) as db:
        db.create_tables()

        # Insert test data with varying counts
        stats = [
            HOSEStatsRecord(
                hose_code="C-4;C(//)",
                radius=3,
                mean=130.0,
                std=2.0,
                count=3,  # Below min_count
            ),
            HOSEStatsRecord(
                hose_code="C-3;C(//)",
                radius=3,
                mean=131.0,
                std=2.0,
                count=10,  # Above min_count
            ),
        ]
        db.insert_hose_stats_batch(stats)

        # Query with min_count=5
        results = db.get_hose_stats_by_shift_window(
            shift_ppm=130.0,
            radius=3,
            window_ppm=5.0,
            min_count=5,
        )

        # Should only return the entry with count=10
        assert len(results) == 1
        assert results[0].count == 10


def test_upsert_with_hybridisation(tmp_path: Path) -> None:
    """Test upsert with hybridisation counts."""
    db_path = tmp_path / "test_upsert_hyb.db"

    with DatabaseManager(db_path) as db:
        db.create_tables()

        # Insert with hybridisation counts (8-tuple format)
        stats = [
            ("C-4;C(//)", 3, 100, 25.0, 400.0, 90, 10, 0),
        ]
        db.upsert_hose_stats_incremental(stats)

        # Retrieve and verify
        record = db.get_hose_stats("C-4;C(//)", 3)
        assert record is not None
        assert record.sp3_count == 90
        assert record.sp2_count == 10
        assert record.sp1_count == 0

        # Upsert again with new counts (should add)
        stats = [
            ("C-4;C(//)", 3, 50, 26.0, 100.0, 45, 5, 0),
        ]
        db.upsert_hose_stats_incremental(stats)

        # Verify merged counts
        record = db.get_hose_stats("C-4;C(//)", 3)
        assert record is not None
        assert record.count == 150  # 100 + 50
        assert record.sp3_count == 135  # 90 + 45
        assert record.sp2_count == 15  # 10 + 5
        assert record.sp1_count == 0


def test_upsert_backward_compatibility(tmp_path: Path) -> None:
    """Test upsert with 5-tuple format (backward compatible)."""
    db_path = tmp_path / "test_upsert_compat.db"

    with DatabaseManager(db_path) as db:
        db.create_tables()

        # Insert with 5-tuple format (no hybridisation)
        stats = [
            ("C-4;C(//)", 3, 100, 25.0, 400.0),
        ]
        db.upsert_hose_stats_incremental(stats)

        # Retrieve and verify (should have default 0 for hybridisation)
        record = db.get_hose_stats("C-4;C(//)", 3)
        assert record is not None
        assert record.sp3_count == 0
        assert record.sp2_count == 0
        assert record.sp1_count == 0


def test_v3_database_compatibility(tmp_path: Path) -> None:
    """Test that methods work with v3 database (no hybridisation columns)."""
    db_path = tmp_path / "test_v3_compat.db"

    # Create a v3 database manually
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE hose_stats (
            hose_code TEXT NOT NULL,
            radius INTEGER NOT NULL,
            mean REAL NOT NULL,
            std REAL NOT NULL,
            count INTEGER NOT NULL,
            m2 REAL NOT NULL DEFAULT 0.0,
            PRIMARY KEY (hose_code, radius)
        )
    """)

    cursor.execute("""
        CREATE TABLE schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cursor.execute(
        "INSERT INTO schema_meta (key, value) VALUES (?, ?)",
        ("schema_version", "3"),
    )

    cursor.execute(
        """INSERT INTO hose_stats (hose_code, radius, mean, std, count, m2)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("C-4;C(//)", 3, 130.0, 2.0, 100, 400.0),
    )
    conn.commit()
    conn.close()

    # Open with DatabaseManager and test queries
    with DatabaseManager(db_path) as db:
        # get_hose_stats should work (no hybridisation fields)
        record = db.get_hose_stats("C-4;C(//)", 3)
        assert record is not None
        assert record.mean == 130.0
        assert record.sp3_count == 0  # Default value

        # get_hose_stats_all_radii should work
        records = db.get_hose_stats_all_radii("C-4;C(//)")
        assert len(records) == 1

        # get_hose_stats_by_shift_window should work
        results = db.get_hose_stats_by_shift_window(
            shift_ppm=130.0,
            radius=3,
            window_ppm=2.0,
        )
        assert len(results) == 1
