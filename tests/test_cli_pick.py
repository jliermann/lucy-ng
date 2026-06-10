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

    def test_pick_1d_dept135_detects_negative(self) -> None:
        """Test that DEPT-135 auto-detects negative CH2 peaks."""
        runner = CliRunner()
        result = runner.invoke(pick, ["1d", "data/Ibuprofen/3"])  # DEPT-135
        assert result.exit_code == 0
        assert "negative peak detection enabled" in result.output
        # Should find the CH2 peak at ~45 ppm with negative intensity
        assert "-" in result.output  # negative intensity value

    def test_pick_1d_dept135_json_negative(self) -> None:
        """Test DEPT-135 JSON output includes negative peaks."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["1d", "data/Ibuprofen/3", "--format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["negative_detected"] is True
        # At least one peak should have negative intensity (CH2)
        negative_peaks = [p for p in data["peaks"] if p["intensity"] < 0]
        assert len(negative_peaks) > 0

    def test_pick_1d_c13_no_negative(self) -> None:
        """Test that regular 13C does not trigger negative detection."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["1d", "data/Ibuprofen/2", "--format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["negative_detected"] is False
        # All peaks should have positive intensity
        for p in data["peaks"]:
            assert p["intensity"] > 0

    def test_pick_1d_snr_floor_flag_routes_to_picker(self) -> None:
        """--snr-floor 3 must route snr_floor=3.0 to AdaptivePeakPicker."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["1d", "data/Ibuprofen/2", "--snr-floor", "3", "--format", "json"]
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        data = json.loads(result.output)
        assert "snr_floor_used" in data, "JSON must contain 'snr_floor_used' field"
        assert data["snr_floor_used"] == 3.0, (
            f"Expected snr_floor_used=3.0, got {data['snr_floor_used']}"
        )

    def test_pick_1d_snr_floor_short_flag(self) -> None:
        """Short -s flag must work identically to --snr-floor."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["1d", "data/Ibuprofen/2", "-s", "3", "--format", "json"]
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        data = json.loads(result.output)
        assert data["snr_floor_used"] == 3.0

    def test_pick_1d_default_snr_floor_used_is_5(self) -> None:
        """Without --snr-floor, snr_floor_used must be 5.0 (the new default)."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["1d", "data/Ibuprofen/2", "--format", "json"]
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        data = json.loads(result.output)
        assert "snr_floor_used" in data, "JSON must contain 'snr_floor_used' field"
        assert data["snr_floor_used"] == 5.0, (
            f"Expected snr_floor_used=5.0 (default), got {data['snr_floor_used']}"
        )

    def test_pick_1d_threshold_snr_floor_used_is_none(self) -> None:
        """With -t, snr_floor_used must be None (SNR mode disabled)."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["1d", "data/Ibuprofen/2", "-t", "0.1", "--format", "json"]
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        data = json.loads(result.output)
        assert "snr_floor_used" in data, "JSON must contain 'snr_floor_used' field"
        assert data["snr_floor_used"] is None, (
            f"Expected snr_floor_used=None for -t mode, got {data['snr_floor_used']}"
        )


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
        """Test raw HSQC picking with text output."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["hsqc", "data/Ibuprofen/6"]
        )
        assert result.exit_code == 0
        assert "Found" in result.output
        assert "peaks" in result.output
        assert "HSQC" in result.output

    def test_pick_hsqc_json(self) -> None:
        """Test raw HSQC picking with JSON output."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["hsqc", "data/Ibuprofen/6", "--format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["experiment_type"] == "HSQC"
        assert "count" in data
        assert "peaks" in data
        if data["count"] > 0:
            assert "f1_position" in data["peaks"][0]
            assert "f2_position" in data["peaks"][0]
            assert "intensity" in data["peaks"][0]


class TestPickHMBC:
    """Tests for lucy pick hmbc command."""

    def test_pick_hmbc_text(self) -> None:
        """Test raw HMBC picking with text output."""
        runner = CliRunner()
        result = runner.invoke(
            pick, ["hmbc", "data/Ibuprofen/7"]
        )
        assert result.exit_code == 0
        assert "Found" in result.output
        assert "peaks" in result.output
        assert "HMBC" in result.output

    def test_pick_hmbc_json(self) -> None:
        """Test raw HMBC picking with JSON output."""
        runner = CliRunner()
        result = runner.invoke(
            pick,
            [
                "hmbc",
                "data/Ibuprofen/7",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["experiment_type"] == "HMBC"
        assert "count" in data
        assert "peaks" in data
        if data["count"] > 0:
            assert "f1_position" in data["peaks"][0]
            assert "f2_position" in data["peaks"][0]
            assert "intensity" in data["peaks"][0]

    def test_pick_hmbc_with_threshold(self) -> None:
        """Test raw HMBC picking with custom threshold."""
        runner = CliRunner()
        result = runner.invoke(
            pick,
            [
                "hmbc",
                "data/Ibuprofen/7",
                "-t",
                "0.1",
            ],
        )
        assert result.exit_code == 0
        assert "Found" in result.output
