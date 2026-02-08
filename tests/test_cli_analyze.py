"""Tests for CLI analyze commands."""

import json

from click.testing import CliRunner

from lucy_ng.cli.analyze import analyze


class TestAnalyzeSymmetry:
    """Tests for lucy analyze symmetry command."""

    def test_analyze_symmetry_text(self) -> None:
        """Test symmetry analysis with text output."""
        runner = CliRunner()
        result = runner.invoke(
            analyze,
            ["symmetry", "C13H18O2", "data/Ibuprofen/2"],
        )
        assert result.exit_code == 0
        assert "Symmetry Analysis" in result.output
        assert "C13H18O2" in result.output
        assert "Expected carbons:" in result.output
        assert "Observed peaks:" in result.output
        assert "Difference:" in result.output

    def test_analyze_symmetry_calculates_difference(self) -> None:
        """Test that symmetry analysis calculates carbon difference."""
        runner = CliRunner()
        result = runner.invoke(
            analyze,
            ["symmetry", "C13H18O2", "data/Ibuprofen/2"],
        )
        assert result.exit_code == 0
        # Should show expected vs observed comparison
        assert "Expected carbons:" in result.output
        assert "Observed peaks:" in result.output
        assert "Difference:" in result.output
        # Either suggests equivalents or warns about more peaks
        assert ("equivalent" in result.output.lower() or "Warning:" in result.output)

    def test_analyze_symmetry_json(self) -> None:
        """Test symmetry analysis with JSON output."""
        runner = CliRunner()
        result = runner.invoke(
            analyze,
            [
                "symmetry",
                "C13H18O2",
                "data/Ibuprofen/2",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["formula"] == "C13H18O2"
        assert "expected_carbons" in data
        assert "observed_peaks" in data
        assert "difference" in data
        assert data["expected_carbons"] == 13

    def test_analyze_symmetry_json_structure(self) -> None:
        """Test JSON output has correct structure."""
        runner = CliRunner()
        result = runner.invoke(
            analyze,
            [
                "symmetry",
                "C13H18O2",
                "data/Ibuprofen/2",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)

        # Check basic structure
        assert "formula" in data
        assert "expected_carbons" in data
        assert "observed_peaks" in data
        assert "difference" in data
        assert isinstance(data["expected_carbons"], int)
        assert isinstance(data["observed_peaks"], int)
        assert isinstance(data["difference"], int)

    def test_analyze_symmetry_invalid_path(self) -> None:
        """Test error on invalid paths."""
        runner = CliRunner()
        result = runner.invoke(
            analyze,
            ["symmetry", "C13H18O2", "data/NonExistent/6"],
        )
        assert result.exit_code != 0
