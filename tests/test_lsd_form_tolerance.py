"""Empirical FORM-tolerance test for LSD binary.

Verifies that LSD silently ignores an unknown FORM command and produces
the same solution set as a file without it. Living regression: if a future
LSD version changes this behaviour, this test will fail and alert the developer.

Context: Phase 66 added emit_form() to LSDInputGenerator so pylsd_mode files
include a FORM declaration. This test confirms the LSD binary (LSD-3.4.9)
tolerates this — otherwise Phase 66 changes would silently break lucy lsd run
for files generated in pylsd_mode.

See: .planning/findings/form-tolerance.md for the audit trail.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from lucy_ng.lsd.runner import LSDRunner
from lucy_ng.lsd.parser import LSDOutputParser


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "form_tolerance"


class TestLSDFormTolerance:
    """Tests confirming LSD binary silently ignores FORM lines."""

    def test_form_tolerance_fixtures_exist(self) -> None:
        """Fixture files must exist and have correct content — always runs (no LSD needed)."""
        assert FIXTURE_DIR.exists(), (
            f"Fixture directory missing: {FIXTURE_DIR}. "
            "Run from the project root."
        )

        minimal_lsd = FIXTURE_DIR / "minimal.lsd"
        minimal_with_form_lsd = FIXTURE_DIR / "minimal_with_form.lsd"

        assert minimal_lsd.exists(), (
            f"Baseline fixture missing: {minimal_lsd}"
        )
        assert minimal_with_form_lsd.exists(), (
            f"FORM-variant fixture missing: {minimal_with_form_lsd}"
        )

        # Baseline must NOT contain FORM
        assert "FORM" not in minimal_lsd.read_text(), (
            f"{minimal_lsd} must not contain a FORM line (it is the baseline without FORM)"
        )

        # FORM variant must contain FORM C2H6
        assert "FORM C2H6" in minimal_with_form_lsd.read_text(), (
            f"{minimal_with_form_lsd} must contain 'FORM C2H6'"
        )

        # Both must contain MULT and HSQC
        for fixture in (minimal_lsd, minimal_with_form_lsd):
            content = fixture.read_text()
            assert "MULT 1 C" in content, f"{fixture} missing MULT 1 C"
            assert "MULT 2 C" in content, f"{fixture} missing MULT 2 C"
            assert "HSQC 1 1" in content, f"{fixture} missing HSQC 1 1"
            assert "HSQC 2 2" in content, f"{fixture} missing HSQC 2 2"

    @pytest.mark.skipif(
        shutil.which("LSD") is None,
        reason="LSD binary not installed",
    )
    def test_form_line_produces_identical_solutions(self, tmp_path: Path) -> None:
        """LSD must produce the same solution count with and without a FORM line.

        Ethane (C2H6) has exactly one valid structure — one C-C bond.
        Both fixture files must yield solution_count == 1, confirming
        FORM is silently ignored rather than causing an error or
        changing the solution set.
        """
        minimal_lsd = FIXTURE_DIR / "minimal.lsd"
        minimal_with_form_lsd = FIXTURE_DIR / "minimal_with_form.lsd"

        assert minimal_lsd.exists(), (
            f"Fixture file missing: {minimal_lsd} — run tests from project root"
        )
        assert minimal_with_form_lsd.exists(), (
            f"Fixture file missing: {minimal_with_form_lsd} — run tests from project root"
        )

        runner = LSDRunner()

        # Run LSD on baseline (no FORM line)
        out_without = tmp_path / "without"
        out_without.mkdir()
        result_without = runner.run_file(
            minimal_lsd, output_dir=out_without, timeout=30
        )

        # Run LSD on FORM variant
        out_with = tmp_path / "with"
        out_with.mkdir()
        result_with = runner.run_file(
            minimal_with_form_lsd, output_dir=out_with, timeout=30
        )

        assert result_without.success, (
            f"LSD failed on minimal.lsd (no FORM). stderr:\n{result_without.stderr}"
        )
        assert result_with.success, (
            f"LSD failed on minimal_with_form.lsd. stderr:\n{result_with.stderr}"
        )

        assert result_without.solution_count == result_with.solution_count, (
            f"FORM line changed solution count: "
            f"without_form={result_without.solution_count}, "
            f"with_form={result_with.solution_count}. "
            "This means LSD does NOT silently ignore FORM — Phase 66 compatibility "
            "must be re-evaluated."
        )

        # Ethane should produce exactly 1 solution (the C-C bond is the only structure)
        assert result_without.solution_count == 1, (
            f"Expected exactly 1 solution for ethane, got {result_without.solution_count}. "
            "Check fixture files."
        )

        # Optional: compare SMILES via outlsd if available for extra rigor
        if LSDRunner.is_outlsd_available():
            _assert_smiles_match(out_without, out_with)


def _assert_smiles_match(dir_without: Path, dir_with: Path) -> None:
    """Compare InChI sets from two outlsd output directories.

    Optional extra-rigor check: if outlsd is available, confirm the solution
    SMILES resolve to the same InChI set (not just the same count).
    """
    from rdkit import Chem
    from rdkit.Chem.inchi import MolToInchi  # type: ignore[import-untyped]

    def _dir_to_inchis(output_dir: Path) -> set[str]:
        """Parse SMILES files in directory and return set of canonical InChIs."""
        inchis: set[str] = set()
        for smi_file in output_dir.glob("*.smi"):
            for solution in LSDOutputParser.parse_smiles_file(smi_file):
                mol = Chem.MolFromSmiles(solution.smiles)
                if mol is None:
                    continue
                inchi = MolToInchi(mol)
                if inchi:
                    inchis.add(inchi)
        return inchis

    inchis_without = _dir_to_inchis(dir_without)
    inchis_with = _dir_to_inchis(dir_with)

    if inchis_without or inchis_with:
        assert inchis_without == inchis_with, (
            f"FORM line produced different InChI sets.\n"
            f"Without FORM: {inchis_without}\n"
            f"With FORM: {inchis_with}"
        )
