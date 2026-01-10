"""Tests for CLI LSD commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from lucy_ng.cli.lsd import lsd


class TestLSDCheck:
    """Tests for lucy lsd check command."""

    def test_lsd_check(self) -> None:
        """Test LSD availability check."""
        runner = CliRunner()
        result = runner.invoke(lsd, ["check"])
        # May pass or fail depending on LSD installation
        assert result.exit_code in [0, 1]
        if result.exit_code == 0:
            assert "available" in result.output.lower()
        else:
            assert "not" in result.output.lower()


class TestLSDGenerate:
    """Tests for lucy lsd generate command."""

    def test_generate_text(self) -> None:
        """Test LSD input generation with text output."""
        runner = CliRunner()
        result = runner.invoke(lsd, ["generate", "data/Ibuprofen", "C13H18O2"])
        assert result.exit_code == 0
        # Should contain LSD commands
        assert "MULT" in result.output
        # Should have header comments
        assert "lucy-ng" in result.output
        assert "C13H18O2" in result.output

    def test_generate_json(self) -> None:
        """Test LSD input generation with JSON output."""
        runner = CliRunner()
        result = runner.invoke(
            lsd, ["generate", "data/Ibuprofen", "C13H18O2", "--format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["molecular_formula"] == "C13H18O2"
        assert "atom_count" in data
        assert "correlation_count" in data
        assert "lsd_content" in data
        assert "MULT" in data["lsd_content"]

    def test_generate_experiments_detected(self) -> None:
        """Test that experiments are correctly detected."""
        runner = CliRunner()
        result = runner.invoke(
            lsd, ["generate", "data/Ibuprofen", "C13H18O2", "--format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        # Should detect key experiments
        assert "experiments_found" in data
        assert "HSQC" in data["experiments_found"]
        assert "DEPT135" in data["experiments_found"]

    def test_generate_to_file(self, tmp_path: Path) -> None:
        """Test writing LSD input to file."""
        output_file = tmp_path / "test.lsd"
        runner = CliRunner()
        result = runner.invoke(
            lsd,
            ["generate", "data/Ibuprofen", "C13H18O2", "-o", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "MULT" in content

    def test_generate_missing_hsqc(self) -> None:
        """Test error when HSQC not found."""
        runner = CliRunner()
        # Use a directory that doesn't have required experiments
        result = runner.invoke(lsd, ["generate", "data/Ibuprofen/1", "C13H18O2"])
        assert result.exit_code != 0
        assert "HSQC" in result.output or "DEPT" in result.output


class TestLSDRun:
    """Tests for lucy lsd run command."""

    def test_run_without_lsd(self, tmp_path: Path) -> None:
        """Test error when LSD not installed."""
        # Create a minimal LSD input file
        lsd_file = tmp_path / "test.lsd"
        lsd_file.write_text("; Test\nMULT 1 C 3 3\nEXIT\n")

        runner = CliRunner()
        result = runner.invoke(lsd, ["run", str(lsd_file)])

        # Should either succeed (if LSD installed) or fail with clear message
        if result.exit_code != 0:
            assert "not installed" in result.output.lower() or "not in path" in result.output.lower()

    def test_run_help(self) -> None:
        """Test run command help."""
        runner = CliRunner()
        result = runner.invoke(lsd, ["run", "--help"])
        assert result.exit_code == 0
        assert "--timeout" in result.output
        assert "--output-dir" in result.output
