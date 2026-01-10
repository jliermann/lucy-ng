"""Tests for CLI dereplicate commands."""

import json

import pytest
from click.testing import CliRunner

from lucy_ng.cli.dereplicate import dereplicate


class TestDereplicateC13:
    """Tests for lucy dereplicate c13 command."""

    def test_dereplicate_invalid_database(self) -> None:
        """Test error when specified database does not exist."""
        runner = CliRunner()
        result = runner.invoke(
            dereplicate,
            ["c13", "data/Ibuprofen/2", "C13H18O2", "--database", "/nonexistent/db.sd"],
        )
        # Should fail because specified database path doesn't exist
        assert result.exit_code != 0

    def test_dereplicate_help(self) -> None:
        """Test help message shows options."""
        runner = CliRunner()
        result = runner.invoke(dereplicate, ["c13", "--help"])
        assert result.exit_code == 0
        assert "--database" in result.output
        assert "--top" in result.output
        assert "--threshold" in result.output
        assert "--format" in result.output

    def test_dereplicate_invalid_path(self) -> None:
        """Test error on invalid spectrum path."""
        runner = CliRunner()
        result = runner.invoke(dereplicate, ["c13", "data/NonExistent/2", "C13H18O2"])
        assert result.exit_code != 0

    @pytest.mark.skipif(
        not any(
            p.exists()
            for p in [
                pytest.importorskip("pathlib").Path("data/reference/nmrshiftdb2withsignals.sd"),
                pytest.importorskip("pathlib").Path("data/nmrshiftdb.sd"),
                pytest.importorskip("pathlib").Path("data/nmrshiftdb/nmrshiftdb.sd"),
            ]
        ),
        reason="nmrshiftdb database not available",
    )
    def test_dereplicate_with_database(self) -> None:
        """Test dereplication with actual database."""
        runner = CliRunner()
        result = runner.invoke(
            dereplicate,
            ["c13", "data/Ibuprofen/2", "C13H18O2"],
        )
        assert result.exit_code == 0
        assert "Dereplication" in result.output
        assert "Observed peaks" in result.output
