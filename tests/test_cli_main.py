"""Tests for CLI main module."""

from click.testing import CliRunner

from lucy_ng import __version__
from lucy_ng.cli import cli


class TestCLIMain:
    """Tests for CLI entry point."""

    def test_version(self) -> None:
        """Test --version returns correct version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_help(self) -> None:
        """Test --help shows usage info."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "lucy-ng" in result.output
        assert "Computer-Assisted Structure Elucidation" in result.output

    def test_no_args(self) -> None:
        """Test running with no arguments shows usage."""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        # Click shows usage and exits with code 0 or 2 depending on config
        assert "Usage:" in result.output

    def test_invalid_command(self) -> None:
        """Test invalid command shows error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["invalid-command"])
        assert result.exit_code != 0
        assert "No such command" in result.output

    def test_all_command_groups_registered(self) -> None:
        """Test all command groups are registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # All command groups should be visible
        assert "read" in result.output
        assert "pick" in result.output
        assert "analyze" in result.output
        assert "dereplicate" in result.output
        assert "lsd" in result.output

    def test_subcommand_help(self) -> None:
        """Test subcommand help is accessible."""
        runner = CliRunner()
        for cmd in ["read", "pick", "analyze", "dereplicate", "lsd"]:
            result = runner.invoke(cli, [cmd, "--help"])
            assert result.exit_code == 0
            assert "Usage:" in result.output


class TestCLIIntegration:
    """Integration tests for CLI workflow."""

    def test_full_pipeline_to_lsd_generate(self) -> None:
        """Test full workflow from reading to LSD generation."""
        runner = CliRunner()

        # 1. Read spectrum
        result = runner.invoke(cli, ["read", "1d", "data/Ibuprofen/2"])
        assert result.exit_code == 0
        assert "13C" in result.output

        # 2. Pick peaks
        result = runner.invoke(cli, ["pick", "1d", "data/Ibuprofen/2"])
        assert result.exit_code == 0
        assert "peaks" in result.output.lower()

        # 3. DEPT-guided HSQC
        result = runner.invoke(
            cli, ["pick", "hsqc", "data/Ibuprofen/6", "data/Ibuprofen/3"]
        )
        assert result.exit_code == 0
        assert "DEPT-Guided" in result.output

        # 4. Symmetry analysis
        result = runner.invoke(
            cli,
            ["analyze", "symmetry", "C13H18O2", "data/Ibuprofen/6", "data/Ibuprofen/3"],
        )
        assert result.exit_code == 0
        assert "Symmetry Analysis" in result.output

        # 5. LSD generate
        result = runner.invoke(
            cli, ["lsd", "generate", "data/Ibuprofen", "C13H18O2"]
        )
        assert result.exit_code == 0
        assert "MULT" in result.output
