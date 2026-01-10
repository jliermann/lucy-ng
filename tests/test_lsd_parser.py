"""Tests for LSD output parser."""

import pytest
from pathlib import Path
import tempfile

from lucy_ng.lsd.parser import LSDOutputParser, LSDSolution


class TestLSDSolution:
    """Tests for LSDSolution dataclass."""

    def test_create_solution(self):
        """Test creating a solution."""
        sol = LSDSolution(
            index=1,
            smiles="CC(C)Cc1ccc(cc1)C(C)C(=O)O",
        )
        assert sol.index == 1
        assert sol.smiles == "CC(C)Cc1ccc(cc1)C(C)C(=O)O"

    def test_solution_with_atoms_and_bonds(self):
        """Test solution with atom and bond data."""
        sol = LSDSolution(
            index=2,
            atoms=[
                {"index": 1, "element": "C"},
                {"index": 2, "element": "C"},
            ],
            bonds=[(1, 2)],
        )
        assert len(sol.atoms) == 2
        assert len(sol.bonds) == 1

    def test_summary(self):
        """Test solution summary."""
        sol = LSDSolution(
            index=1,
            smiles="C1CCCCC1",
            atoms=[{"index": i, "element": "C"} for i in range(1, 7)],
            bonds=[(i, i + 1) for i in range(1, 6)] + [(6, 1)],
        )
        summary = sol.summary()

        assert "Solution 1" in summary
        assert "C1CCCCC1" in summary
        assert "Atoms: 6" in summary
        assert "Bonds: 6" in summary


class TestLSDOutputParserFiles:
    """Tests for parsing LSD output files."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory with mock LSD output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            yield tmpdir

    def test_parse_empty_directory(self, temp_output_dir):
        """Test parsing empty directory returns empty list."""
        solutions = LSDOutputParser.parse_solutions(temp_output_dir)
        assert solutions == []

    def test_parse_sol_file(self, temp_output_dir):
        """Test parsing a single .sol file."""
        sol_content = """# Solution 1
1 C sp2 0
2 C sp3 2
3 O sp3 1
BOND 1 2
BOND 2 3
"""
        sol_file = temp_output_dir / "sol001.sol"
        sol_file.write_text(sol_content)

        solution = LSDOutputParser.parse_sol_file(sol_file)

        assert solution is not None
        assert solution.index == 1
        assert len(solution.atoms) == 3
        assert len(solution.bonds) == 2

    def test_parse_multiple_sol_files(self, temp_output_dir):
        """Test parsing multiple solution files."""
        # Create multiple solution files
        for i in range(1, 4):
            sol_file = temp_output_dir / f"sol{i:03d}.sol"
            sol_file.write_text(f"# Solution {i}\n1 C sp3 3\n")

        solutions = LSDOutputParser.parse_solutions(temp_output_dir)

        assert len(solutions) == 3
        assert solutions[0].index == 1
        assert solutions[1].index == 2
        assert solutions[2].index == 3

    def test_parse_outlsd_smiles(self, temp_output_dir):
        """Test parsing outlsd SMILES output."""
        outlsd_content = """# SMILES output
CC(C)C
CCC
C1CCCCC1
"""
        outlsd_file = temp_output_dir / "outlsd.out"
        outlsd_file.write_text(outlsd_content)

        smiles_list = LSDOutputParser.parse_outlsd_output(outlsd_file)

        assert len(smiles_list) == 3
        assert smiles_list[0] == "CC(C)C"
        assert smiles_list[1] == "CCC"
        assert smiles_list[2] == "C1CCCCC1"

    def test_parse_solutions_with_smiles(self, temp_output_dir):
        """Test that SMILES are matched to solutions."""
        # Create sol files
        (temp_output_dir / "sol001.sol").write_text("1 C sp3 3\n")
        (temp_output_dir / "sol002.sol").write_text("1 C sp3 2\n2 C sp3 3\n")

        # Create outlsd output with SMILES
        (temp_output_dir / "outlsd.out").write_text("CC\nCCC\n")

        solutions = LSDOutputParser.parse_solutions(temp_output_dir)

        assert len(solutions) == 2
        assert solutions[0].smiles == "CC"
        assert solutions[1].smiles == "CCC"


class TestLSDOutputParserContent:
    """Tests for parsing LSD output content."""

    def test_extract_index_from_filename(self):
        """Test extracting solution index from filename."""
        assert LSDOutputParser._extract_index_from_filename("sol001.sol") == 1
        assert LSDOutputParser._extract_index_from_filename("sol123.sol") == 123
        assert LSDOutputParser._extract_index_from_filename("solution_5.sol") == 5
        assert LSDOutputParser._extract_index_from_filename("noindex.sol") == 1  # Default

    def test_parse_atoms(self):
        """Test parsing atom definitions."""
        content = """
# Header
1 C sp2 0
2 N sp3 1
3 O sp2 0
"""
        atoms = LSDOutputParser._parse_atoms(content)

        assert len(atoms) == 3
        assert atoms[0]["index"] == 1
        assert atoms[0]["element"] == "C"
        assert atoms[1]["element"] == "N"

    def test_parse_bonds(self):
        """Test parsing bond definitions."""
        content = """
BOND 1 2
BOND 2 3
BOND 3 1
"""
        bonds = LSDOutputParser._parse_bonds(content)

        assert len(bonds) == 3
        assert (1, 2) in bonds
        assert (2, 3) in bonds
        assert (1, 3) in bonds

    def test_parse_bonds_dash_format(self):
        """Test parsing bonds in X-Y format."""
        content = """
1-2
2-3
3-4
"""
        bonds = LSDOutputParser._parse_bonds(content)

        assert len(bonds) == 3
        assert (1, 2) in bonds
        assert (2, 3) in bonds
        assert (3, 4) in bonds

    def test_parse_bonds_deduplicates(self):
        """Test that duplicate bonds are removed."""
        content = """
BOND 1 2
BOND 2 1
BOND 1 2
"""
        bonds = LSDOutputParser._parse_bonds(content)

        assert len(bonds) == 1  # Only one unique bond

    def test_parse_summary_output(self):
        """Test parsing LSD summary output."""
        output = "Found 5 solutions in 0.25 seconds"
        stats = LSDOutputParser.parse_summary_output(output)

        assert stats["solution_count"] == 5
        assert stats["execution_time"] == 0.25
        assert stats["status"] == "success"

    def test_parse_summary_no_solution(self):
        """Test parsing output with no solutions."""
        output = "No solution found - contradictory constraints"
        stats = LSDOutputParser.parse_summary_output(output)

        assert stats["solution_count"] == 0
        assert stats["status"] == "no_solution"

    def test_parse_summary_error(self):
        """Test parsing output with error."""
        output = "Error: invalid input format"
        stats = LSDOutputParser.parse_summary_output(output)

        assert stats["status"] == "error"


class TestLSDOutputParserUtilities:
    """Tests for parser utility functions."""

    def test_solutions_to_smiles_list(self):
        """Test extracting SMILES from solutions."""
        solutions = [
            LSDSolution(index=1, smiles="CC"),
            LSDSolution(index=2, smiles=None),
            LSDSolution(index=3, smiles="CCC"),
        ]

        smiles = LSDOutputParser.solutions_to_smiles_list(solutions)

        assert smiles == ["CC", "", "CCC"]

    def test_parse_sol_file_nonexistent(self):
        """Test parsing non-existent file returns None."""
        result = LSDOutputParser.parse_sol_file("/nonexistent/file.sol")
        assert result is None

    def test_parse_outlsd_nonexistent(self):
        """Test parsing non-existent outlsd file returns empty list."""
        result = LSDOutputParser.parse_outlsd_output("/nonexistent/outlsd.out")
        assert result == []


class TestLSDOutputParserEdgeCases:
    """Tests for edge cases."""

    def test_parse_sol_with_comments(self):
        """Test parsing sol file with various comment styles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sol_file = Path(tmpdir) / "sol001.sol"
            sol_file.write_text("""
# This is a comment
; Another comment style
1 C sp3 3
# More comments
2 C sp3 2
""")
            solution = LSDOutputParser.parse_sol_file(sol_file)

            assert len(solution.atoms) == 2

    def test_parse_sol_with_empty_lines(self):
        """Test parsing sol file with empty lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sol_file = Path(tmpdir) / "sol001.sol"
            sol_file.write_text("""
1 C sp3 3


2 C sp3 2

BOND 1 2

""")
            solution = LSDOutputParser.parse_sol_file(sol_file)

            assert len(solution.atoms) == 2
            assert len(solution.bonds) == 1

    def test_parse_outlsd_filters_invalid(self):
        """Test that invalid SMILES-like lines are filtered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outlsd_file = Path(tmpdir) / "outlsd.out"
            outlsd_file.write_text("""
CC
This is not a SMILES string!
CCC
More text here
C1CCCCC1
""")
            smiles = LSDOutputParser.parse_outlsd_output(outlsd_file)

            # Should only include valid SMILES
            assert "CC" in smiles
            assert "CCC" in smiles
            assert "C1CCCCC1" in smiles
            assert len(smiles) == 3
