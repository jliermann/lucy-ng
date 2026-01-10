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
            ["symmetry", "C13H18O2", "data/Ibuprofen/6", "data/Ibuprofen/3"],
        )
        assert result.exit_code == 0
        assert "Symmetry Analysis" in result.output
        assert "C13H18O2" in result.output
        assert "SIGNAL COUNT" in result.output
        assert "HYDROGEN BUDGET" in result.output
        assert "INTENSITY EVIDENCE" in result.output

    def test_analyze_symmetry_detects_missing_carbons(self) -> None:
        """Test that symmetry analysis detects missing carbons for Ibuprofen."""
        runner = CliRunner()
        result = runner.invoke(
            analyze,
            ["symmetry", "C13H18O2", "data/Ibuprofen/6", "data/Ibuprofen/3"],
        )
        assert result.exit_code == 0
        # Ibuprofen has 13 carbons but ~9 signals due to symmetry
        assert "Missing carbons:" in result.output
        # Should suggest equivalent carbons
        assert "equivalent" in result.output.lower()

    def test_analyze_symmetry_json(self) -> None:
        """Test symmetry analysis with JSON output."""
        runner = CliRunner()
        result = runner.invoke(
            analyze,
            [
                "symmetry",
                "C13H18O2",
                "data/Ibuprofen/6",
                "data/Ibuprofen/3",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["molecular_formula"] == "C13H18O2"
        assert "signal_count" in data
        assert "expected_carbons" in data
        assert "missing_carbons" in data
        assert "has_symmetry" in data
        assert "hydrogen_budget" in data
        assert "intensity_report" in data

    def test_analyze_symmetry_json_structure(self) -> None:
        """Test JSON output has correct structure."""
        runner = CliRunner()
        result = runner.invoke(
            analyze,
            [
                "symmetry",
                "C13H18O2",
                "data/Ibuprofen/6",
                "data/Ibuprofen/3",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)

        # Hydrogen budget structure
        hb = data["hydrogen_budget"]
        assert "expected_h" in hb
        assert "total_accounted" in hb
        assert "missing_h" in hb
        assert "has_equivalents" in hb

        # Intensity report structure
        ir = data["intensity_report"]
        assert "peak_count" in ir
        assert "has_potential_equivalents" in ir
        assert "high_intensity_peaks" in ir

    def test_analyze_symmetry_invalid_path(self) -> None:
        """Test error on invalid paths."""
        runner = CliRunner()
        result = runner.invoke(
            analyze,
            ["symmetry", "C13H18O2", "data/NonExistent/6", "data/Ibuprofen/3"],
        )
        assert result.exit_code != 0
