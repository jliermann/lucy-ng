"""CLI integration tests for lucy detect 4j and lucy detect 4j-batch commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from lucy_ng.cli.main import cli
from lucy_ng.database import DatabaseManager


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    """Create test database with hose_stats and coupling_path_stats for CLI tests.

    Uses same four-scenario setup as test_detection_4j.py:
      A) likely_4j:         carbon at 129.0, h_carbon at 45.0
      B) possible_4j:       carbon at 135.0, h_carbon at 45.0
      C) unlikely_4j:       carbon at 129.0, h_carbon at 39.0
      D) insufficient_data: carbon at 135.0, h_carbon at 39.0
    """
    db_path = tmp_path / "test_4j_cli.db"

    with DatabaseManager(db_path) as db:
        db.create_tables()

        conn = db.connection
        cursor = conn.cursor()

        # HOSE stats for carbon shifts
        cursor.execute(
            """
            INSERT INTO hose_stats
                (hose_code, radius, mean, std, count, sp3_count, sp2_count, sp1_count)
            VALUES
                ('C-3;=CC(//)', 2, 129.0, 1.5, 500, 5, 490, 5),
                ('C-3;=CC(=N/)', 2, 135.0, 1.5, 400, 4, 392, 4)
            """
        )

        # HOSE stats for h_carbon shifts
        cursor.execute(
            """
            INSERT INTO hose_stats
                (hose_code, radius, mean, std, count, sp3_count, sp2_count, sp1_count)
            VALUES
                ('C-4;CC(CC/)', 2, 45.0, 1.5, 600, 595, 5, 0),
                ('C-4;CC(CO/)', 2, 39.0, 1.5, 300, 298, 2, 0)
            """
        )

        # Coupling path stats for all four scenarios
        cursor.executemany(
            """
            INSERT INTO coupling_path_stats (carbon_hose, h_carbon_hose, bond_distance, count)
            VALUES (?, ?, ?, ?)
            """,
            [
                # Scenario A: likely_4j (4J=73.3%)
                ("C-3;=CC(//)", "C-4;CC(CC/)", 2, 10),
                ("C-3;=CC(//)", "C-4;CC(CC/)", 3, 10),
                ("C-3;=CC(//)", "C-4;CC(CC/)", 4, 55),
                # Scenario B: possible_4j (4J=20%)
                ("C-3;=CC(=N/)", "C-4;CC(CC/)", 2, 40),
                ("C-3;=CC(=N/)", "C-4;CC(CC/)", 3, 40),
                ("C-3;=CC(=N/)", "C-4;CC(CC/)", 4, 20),
                # Scenario C: unlikely_4j (4J=5%)
                ("C-3;=CC(//)", "C-4;CC(CO/)", 2, 80),
                ("C-3;=CC(//)", "C-4;CC(CO/)", 3, 15),
                ("C-3;=CC(//)", "C-4;CC(CO/)", 4, 5),
                # Scenario D: insufficient_data (total=30)
                ("C-3;=CC(=N/)", "C-4;CC(CO/)", 2, 15),
                ("C-3;=CC(=N/)", "C-4;CC(CO/)", 3, 10),
                ("C-3;=CC(=N/)", "C-4;CC(CO/)", 4, 5),
            ],
        )

        conn.commit()

    return db_path


# ---------------------------------------------------------------------------
# Tests for: lucy detect 4j
# ---------------------------------------------------------------------------


def test_4j_command_text_format(test_db: Path) -> None:
    """lucy detect 4j with text format returns human-readable output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "4j", "129.0", "45.0", "--db", str(test_db)])

    assert result.exit_code == 0, result.output
    assert "129.0" in result.output
    assert "45.0" in result.output


def test_4j_command_json_format(test_db: Path) -> None:
    """lucy detect 4j --format json returns valid JSON with required fields."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["detect", "4j", "129.0", "45.0", "--db", str(test_db), "--format", "json"]
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)

    # Required fields per plan
    assert "risk_level" in data
    assert "recommendation" in data
    assert "distribution" in data
    assert "total_observations" in data
    assert "carbon_shift" in data
    assert "h_carbon_shift" in data
    assert data["risk_level"] == "likely_4j"
    assert data["recommendation"] == "defer"


def test_4j_command_possible_tier(test_db: Path) -> None:
    """4j command correctly identifies possible_4j tier."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["detect", "4j", "135.0", "45.0", "--db", str(test_db), "--format", "json"]
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["risk_level"] == "possible_4j"


def test_4j_command_unlikely_tier(test_db: Path) -> None:
    """4j command correctly identifies unlikely_4j tier."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["detect", "4j", "129.0", "39.0", "--db", str(test_db), "--format", "json"]
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["risk_level"] == "unlikely_4j"
    assert data["recommendation"] == "normal"


def test_4j_command_no_database_exits_1() -> None:
    """4j command exits with code 1 when no database is found."""
    runner = CliRunner()
    with patch("lucy_ng.database.DatabaseFinder.find_hose_database", return_value=None):
        result = runner.invoke(cli, ["detect", "4j", "129.0", "45.0"])

    assert result.exit_code == 1


def test_4j_command_min_observations_option(test_db: Path) -> None:
    """--min-observations is forwarded correctly."""
    runner = CliRunner(mix_stderr=False)
    # 135.0:39.0 has 30 observations; with min=100 => insufficient_data
    result = runner.invoke(
        cli,
        ["detect", "4j", "135.0", "39.0", "--db", str(test_db),
         "--format", "json", "--min-observations", "100"],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["risk_level"] == "insufficient_data"


# ---------------------------------------------------------------------------
# Tests for: lucy detect 4j-batch
# ---------------------------------------------------------------------------


def test_4j_batch_json_format_two_correlations(test_db: Path) -> None:
    """4j-batch JSON output has 'correlations' list and 'summary' dict."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "detect", "4j-batch",
            "--correlations", "129.0:45.0,135.0:45.0",
            "--db", str(test_db),
            "--format", "json",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)

    assert "correlations" in data
    assert "summary" in data
    assert len(data["correlations"]) == 2
    assert data["correlations"][0]["risk_level"] == "likely_4j"
    assert data["correlations"][1]["risk_level"] == "possible_4j"


def test_4j_batch_json_summary_counts(test_db: Path) -> None:
    """4j-batch JSON summary has correct per-risk-level counts."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "detect", "4j-batch",
            "--correlations", "129.0:45.0,135.0:45.0,129.0:39.0",
            "--db", str(test_db),
            "--format", "json",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    summary = data["summary"]

    assert summary["likely_4j"] == 1
    assert summary["possible_4j"] == 1
    assert summary["unlikely_4j"] == 1
    assert summary["insufficient_data"] == 0


def test_4j_batch_text_format(test_db: Path) -> None:
    """4j-batch text format includes summaries for each correlation and a count line."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "detect", "4j-batch",
            "--correlations", "129.0:45.0,135.0:45.0",
            "--db", str(test_db),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Summary:" in result.output
    # Should mention the count categories
    assert "unlikely" in result.output.lower() or "likely" in result.output.lower()


def test_4j_batch_text_summary_line(test_db: Path) -> None:
    """4j-batch text output ends with a summary line showing risk level counts."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "detect", "4j-batch",
            "--correlations", "129.0:45.0",
            "--db", str(test_db),
        ],
    )

    assert result.exit_code == 0, result.output
    lines = result.output.strip().splitlines()
    last_line = lines[-1]
    assert "Summary:" in last_line
    assert "unlikely" in last_line
    assert "possible" in last_line
    assert "likely" in last_line
    assert "insufficient" in last_line


def test_4j_batch_invalid_correlations_format() -> None:
    """4j-batch exits with 1 on invalid --correlations format."""
    runner = CliRunner()
    with patch("lucy_ng.database.DatabaseFinder.find_hose_database", return_value=None):
        result = runner.invoke(
            cli,
            ["detect", "4j-batch", "--correlations", "bad-input-format"],
        )

    # Should exit with 1 due to parse error (before DB lookup)
    assert result.exit_code == 1


def test_4j_batch_no_database_exits_1() -> None:
    """4j-batch exits with code 1 when no database is found."""
    runner = CliRunner()
    with patch("lucy_ng.database.DatabaseFinder.find_hose_database", return_value=None):
        result = runner.invoke(
            cli,
            ["detect", "4j-batch", "--correlations", "129.0:45.0"],
        )

    assert result.exit_code == 1


def test_4j_batch_single_correlation_json(test_db: Path) -> None:
    """4j-batch with single correlation returns list of length 1."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "detect", "4j-batch",
            "--correlations", "129.0:45.0",
            "--db", str(test_db),
            "--format", "json",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert len(data["correlations"]) == 1


def test_4j_batch_all_four_scenarios(test_db: Path) -> None:
    """4j-batch handles all four risk tiers in one call."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "detect", "4j-batch",
            "--correlations", "129.0:45.0,135.0:45.0,129.0:39.0,135.0:39.0",
            "--db", str(test_db),
            "--format", "json",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)

    assert len(data["correlations"]) == 4
    risk_levels = [c["risk_level"] for c in data["correlations"]]
    assert "likely_4j" in risk_levels
    assert "possible_4j" in risk_levels
    assert "unlikely_4j" in risk_levels
    assert "insufficient_data" in risk_levels

    # Summary should show all four present
    assert data["summary"]["likely_4j"] == 1
    assert data["summary"]["possible_4j"] == 1
    assert data["summary"]["unlikely_4j"] == 1
    assert data["summary"]["insufficient_data"] == 1
