"""Tests for CLI pick commands."""

import json

from click.testing import CliRunner

from lucy_ng.cli.pick import pick


class TestPick1D:
    """Tests for lucy pick 1d command."""

    def test_pick_1d_text(self) -> None:
        """Test picking 1D peaks with text output."""
        runner = CliRunner()
        result = runner.invoke(pick, ["1d", "data/Ibuprofen/2"])  # 13C
        assert result.exit_code == 0
        assert "Found" in result.output
        assert "peaks" in result.output
        assert "ppm" in result.output

    def test_pick_1d_json(self) -> None:
        """Test picking 1D peaks with JSON output."""
        runner = CliRunner()
        result = runner.invoke(pick, ["1d", "data/Ibuprofen/2", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "count" in data
        assert "peaks" in data
        assert data["count"] > 0
        # Each peak should have ppm and intensity
        assert "ppm" in data["peaks"][0]
        assert "intensity" in data["peaks"][0]

    def test_pick_1d_with_threshold(self) -> None:
        """Test picking with explicit threshold."""
        runner = CliRunner()
        result = runner.invoke(pick, ["1d", "data/Ibuprofen/2", "-t", "0.1"])
        assert result.exit_code == 0
        assert "Found" in result.output


class TestPick2D:
    """Tests for lucy pick 2d command."""

    def test_pick_2d_text(self) -> None:
        """Test picking 2D peaks with text output."""
        runner = CliRunner()
        result = runner.invoke(pick, ["2d", "data/Ibuprofen/6"])  # HSQC
        assert result.exit_code == 0
        assert "Found" in result.output
        assert "HSQC" in result.output
        assert "F1:" in result.output
        assert "F2:" in result.output

    def test_pick_2d_json(self) -> None:
        """Test picking 2D peaks with JSON output."""
        runner = CliRunner()
        result = runner.invoke(pick, ["2d", "data/Ibuprofen/6", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["experiment_type"] == "HSQC"
        assert "count" in data
        assert "peaks" in data
        if data["count"] > 0:
            assert "f1_position" in data["peaks"][0]
            assert "f2_position" in data["peaks"][0]


class TestPickHSQC:
    """Tests for lucy pick hsqc command."""

    def test_pick_hsqc_text(self) -> None:
        """Test DEPT-guided HSQC picking with text output."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["hsqc", "data/Ibuprofen/6", "data/Ibuprofen/3"]
        )
        assert result.exit_code == 0
        assert "DEPT-Guided HSQC" in result.output
        assert "DEPT peaks" in result.output
        assert "Validated HSQC" in result.output
        assert "Carbon multiplicities" in result.output

    def test_pick_hsqc_json(self) -> None:
        """Test DEPT-guided HSQC picking with JSON output."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["hsqc", "data/Ibuprofen/6", "data/Ibuprofen/3", "--format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "dept_peaks_count" in data
        assert "hsqc_peaks_count" in data
        assert "carbon_multiplicities" in data
        assert "all_carbons_found" in data
        assert "peaks" in data


class TestPickHMBC:
    """Tests for lucy pick hmbc command."""

    def test_pick_hmbc_text(self) -> None:
        """Test guided HMBC picking with text output."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["hmbc", "data/Ibuprofen/7", "data/Ibuprofen/2", "data/Ibuprofen/6"]
        )
        assert result.exit_code == 0
        assert "HMBC Guided" in result.output
        assert "Reference carbons:" in result.output
        assert "Reference protons:" in result.output
        assert "Validated peaks:" in result.output

    def test_pick_hmbc_json(self) -> None:
        """Test guided HMBC picking with JSON output."""
        runner = CliRunner()
        result = runner.invoke(
            pick,
            [
                "hmbc",
                "data/Ibuprofen/7",
                "data/Ibuprofen/2",
                "data/Ibuprofen/6",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "reference_carbons" in data
        assert "reference_protons" in data
        assert "validated_count" in data
        assert "rejected_count" in data
        assert "peaks" in data

    def test_pick_hmbc_with_dept(self) -> None:
        """Test guided HMBC picking with optional DEPT."""
        runner = CliRunner()
        result = runner.invoke(
            pick,
            [
                "hmbc",
                "data/Ibuprofen/7",
                "data/Ibuprofen/2",
                "data/Ibuprofen/6",
                "--dept135",
                "data/Ibuprofen/3",
            ],
        )
        assert result.exit_code == 0
        assert "HMBC Guided" in result.output
