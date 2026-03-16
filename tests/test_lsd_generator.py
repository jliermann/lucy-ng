"""Tests for LSD input file generator."""

import pytest
from pathlib import Path
import tempfile

from lucy_ng import BrukerReader, DEPTGuidedPicker, Peak1D, Peak2D, PeakList1D, PeakList2D
from lucy_ng.lsd.models import Hybridization, LSDAtom, LSDConstraint, LSDCorrelation, LSDProblem
from lucy_ng.lsd.generator import LSDInputGenerator


class TestLSDInputGeneratorBasic:
    """Basic tests for LSD input generation."""

    def test_generate_empty_problem(self):
        """Test generating input for empty problem."""
        problem = LSDProblem(name="empty")
        content = LSDInputGenerator.generate(problem)

        assert "; LSD input file: empty" in content
        assert "EXIT" in content

    def test_generate_with_atoms(self):
        """Test generating MULT lines."""
        problem = LSDProblem(name="test")
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 2))
        problem.add_atom(LSDAtom(3, "C", Hybridization.SP3, 3))

        content = LSDInputGenerator.generate(problem)

        assert "MULT 1 C 2 0" in content
        assert "MULT 2 C 3 2" in content
        assert "MULT 3 C 3 3" in content

    def test_generate_with_molecular_formula(self):
        """Test molecular formula in header."""
        problem = LSDProblem(name="ibuprofen", molecular_formula="C13H18O2")
        content = LSDInputGenerator.generate(problem)

        assert "; Molecular formula: C13H18O2" in content

    def test_generate_with_chemical_shifts(self):
        """Test SHIX lines for chemical shifts."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0, carbon_shift=129.5))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 2, carbon_shift=45.0))

        content = LSDInputGenerator.generate(problem)

        assert "SHIX 1 129.50" in content
        assert "SHIX 2 45.00" in content

    def test_generate_hsqc_correlations(self):
        """Test HSQC correlation lines."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP3, 1))
        problem.add_correlation(LSDCorrelation(1, 1, "HSQC"))

        content = LSDInputGenerator.generate(problem)

        assert "HSQC 1 1" in content
        assert "; Direct C-H correlations" in content

    def test_generate_hmbc_correlations(self):
        """Test HMBC correlation lines with bond distances."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 2))
        problem.add_correlation(LSDCorrelation(1, 2, "HMBC", min_bonds=2, max_bonds=3))

        content = LSDInputGenerator.generate(problem)

        # LSD HMBC uses 2 parameters; bond distance defaults to 2-3
        assert "HMBC 1 2" in content
        assert "; Long-range C-H correlations" in content

    def test_generate_cosy_correlations(self):
        """Test COSY correlation lines."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP3, 1))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 2))
        problem.add_correlation(LSDCorrelation(1, 2, "COSY"))

        content = LSDInputGenerator.generate(problem)

        assert "COSY 1 2" in content
        assert "; H-H correlations" in content

    def test_atoms_sorted_by_index(self):
        """Test that atoms are output in index order."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(3, "C", Hybridization.SP3, 3))
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 2))

        content = LSDInputGenerator.generate(problem)
        lines = content.split("\n")
        mult_lines = [l for l in lines if l.startswith("MULT")]

        assert mult_lines[0] == "MULT 1 C 2 0"
        assert mult_lines[1] == "MULT 2 C 3 2"
        assert mult_lines[2] == "MULT 3 C 3 3"

    def test_generate_with_bond_constraints(self):
        """Test generating BOND constraint lines."""
        problem = LSDProblem(name="test")
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0, carbon_shift=180.0))
        problem.add_atom(LSDAtom(2, "O", Hybridization.SP2, 0))
        problem.add_constraint(LSDConstraint(1, 2, "BOND", reason="carbonyl C=O"))

        content = LSDInputGenerator.generate(problem)

        assert "BOND 1 2" in content
        assert "; carbonyl C=O" in content
        assert "; Required bonds" in content

    def test_generate_with_fbnd_constraints(self):
        """Test generating FBND (forbidden bond) constraint lines."""
        problem = LSDProblem(name="test")
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 2))
        problem.add_atom(LSDAtom(3, "O", Hybridization.SP2, 0))
        problem.add_constraint(LSDConstraint(1, 3, "FBND", reason="too far"))

        content = LSDInputGenerator.generate(problem)

        assert "FBND 1 3" in content
        assert "; too far" in content
        assert "; Forbidden bonds" in content


class TestLSDInputGeneratorFile:
    """Tests for file writing."""

    def test_write_file(self):
        """Test writing LSD input to file."""
        problem = LSDProblem(name="test")
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.lsd"
            result_path = LSDInputGenerator.write_file(problem, output_path)

            assert result_path.exists()
            content = result_path.read_text()
            assert "MULT 1 C 2 0" in content


class TestLSDInputGeneratorFromPeakData:
    """Tests for building problems from peak data."""

    def test_from_carbon_peaks_only(self):
        """Test building problem from 13C peaks only."""
        carbon_peaks = PeakList1D(
            peaks=[
                Peak1D(position=129.5, intensity=1000.0),
                Peak1D(position=45.0, intensity=800.0),
                Peak1D(position=22.5, intensity=600.0),
            ],
            nucleus="13C",
        )

        problem = LSDInputGenerator.from_peak_data(
            carbon_peaks=carbon_peaks,
            name="test",
        )

        assert len(problem.atoms) == 3
        # Sorted by ppm descending, so 129.5 is index 1
        assert problem.get_atom_by_index(1).carbon_shift == 129.5
        assert problem.get_atom_by_index(2).carbon_shift == 45.0
        assert problem.get_atom_by_index(3).carbon_shift == 22.5

    def test_from_peaks_with_hsqc(self):
        """Test building problem with HSQC correlations."""
        carbon_peaks = PeakList1D(
            peaks=[
                Peak1D(position=129.5, intensity=1000.0),
                Peak1D(position=45.0, intensity=800.0),
            ],
            nucleus="13C",
        )

        hsqc_peaks = PeakList2D(
            peaks=[
                Peak2D(f1_position=129.5, f2_position=7.2, intensity=100.0),
                Peak2D(f1_position=45.0, f2_position=2.5, intensity=100.0),
            ],
            f1_nucleus="13C",
            f2_nucleus="1H",
            experiment_type="HSQC",
        )

        problem = LSDInputGenerator.from_peak_data(
            carbon_peaks=carbon_peaks,
            hsqc_peaks=hsqc_peaks,
        )

        # Should have 2 HSQC correlations
        hsqc_corrs = [c for c in problem.correlations if c.correlation_type == "HSQC"]
        assert len(hsqc_corrs) == 2

    def test_from_peaks_no_duplicate_hsqc(self):
        """Test that duplicate HSQC peaks don't create duplicate correlations."""
        carbon_peaks = PeakList1D(
            peaks=[Peak1D(position=129.5, intensity=1000.0)],
            nucleus="13C",
        )

        hsqc_peaks = PeakList2D(
            peaks=[
                Peak2D(f1_position=129.5, f2_position=7.2, intensity=100.0),
                Peak2D(f1_position=129.5, f2_position=7.2, intensity=90.0),  # Duplicate
            ],
            f1_nucleus="13C",
            f2_nucleus="1H",
            experiment_type="HSQC",
        )

        problem = LSDInputGenerator.from_peak_data(
            carbon_peaks=carbon_peaks,
            hsqc_peaks=hsqc_peaks,
        )

        hsqc_corrs = [c for c in problem.correlations if c.correlation_type == "HSQC"]
        assert len(hsqc_corrs) == 1  # Should deduplicate

    def test_from_peaks_with_molecular_formula(self):
        """Test molecular formula is preserved."""
        carbon_peaks = PeakList1D(
            peaks=[Peak1D(position=129.5, intensity=1000.0)],
            nucleus="13C",
        )

        problem = LSDInputGenerator.from_peak_data(
            carbon_peaks=carbon_peaks,
            molecular_formula="C13H18O2",
        )

        assert problem.molecular_formula == "C13H18O2"


class TestLSDInputGeneratorIntegration:
    """Integration tests with real Ibuprofen data."""

    @pytest.fixture
    def ibuprofen_dept_result(self):
        """Load Ibuprofen DEPT-guided result."""
        hsqc = BrukerReader.read_2d("data/Ibuprofen/6")
        dept = BrukerReader.read_1d("data/Ibuprofen/3")
        return DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept)

    def test_from_dept_result(self, ibuprofen_dept_result):
        """Test building LSD problem from DEPT result."""
        problem = LSDInputGenerator.from_dept_result(
            dept_result=ibuprofen_dept_result,
            molecular_formula="C13H18O2",
            name="ibuprofen",
        )

        # Should have atoms from DEPT peaks
        assert len(problem.atoms) >= 7  # At least 7 protonated carbons
        assert problem.molecular_formula == "C13H18O2"
        assert problem.name == "ibuprofen"

    def test_from_dept_result_has_multiplicities(self, ibuprofen_dept_result):
        """Test that DEPT multiplicities are used for H count."""
        problem = LSDInputGenerator.from_dept_result(
            dept_result=ibuprofen_dept_result,
        )

        # Check that some atoms have hydrogen counts set
        h_counts = [a.hydrogen_count for a in problem.atoms]
        assert any(h > 0 for h in h_counts), "Should have atoms with hydrogens"

    def test_from_dept_result_generates_valid_lsd(self, ibuprofen_dept_result):
        """Test that generated LSD file is syntactically valid."""
        problem = LSDInputGenerator.from_dept_result(
            dept_result=ibuprofen_dept_result,
            molecular_formula="C13H18O2",
        )

        content = LSDInputGenerator.generate(problem)

        # Check basic structure
        assert content.startswith(";")  # Comment header
        assert "MULT" in content
        assert "EXIT" in content

        # Check all MULT lines are valid
        for line in content.split("\n"):
            if line.startswith("MULT"):
                parts = line.split()
                assert len(parts) >= 5  # MULT idx elem hyb hcount
                assert parts[1].isdigit()  # Index
                assert parts[2] in ("C", "N", "O", "S", "P")  # Element
                assert parts[3] in ("1", "2", "3")  # Hybridization
                assert parts[4].isdigit()  # H count

    def test_full_workflow_output(self, ibuprofen_dept_result):
        """Test complete workflow and print output for inspection."""
        problem = LSDInputGenerator.from_dept_result(
            dept_result=ibuprofen_dept_result,
            molecular_formula="C13H18O2",
            name="ibuprofen",
        )

        content = LSDInputGenerator.generate(problem)

        # Just verify it generates without error and has expected sections
        assert "; LSD input file: ibuprofen" in content
        assert "; Molecular formula: C13H18O2" in content
        assert "MULT" in content
        assert "HSQC" in content or len(problem.correlations) == 0
        assert "EXIT" in content


class TestCarbonylDetection:
    """Tests for automatic carbonyl detection and constraint generation."""

    def test_detects_carboxylic_acid_carbonyl(self):
        """Test that carboxylic acid carbonyl (180 ppm) is detected."""
        carbon_peaks = PeakList1D(
            peaks=[
                Peak1D(position=180.0, intensity=1000.0),  # Carboxylic acid
                Peak1D(position=45.0, intensity=800.0),   # CH
            ],
            nucleus="13C",
        )

        problem = LSDInputGenerator.from_peak_data(
            carbon_peaks=carbon_peaks,
            molecular_formula="C2H4O2",  # Acetic acid-like
            name="test",
        )

        # Should have BOND constraint between carbonyl C and O
        assert len(problem.constraints) >= 1
        bond_constraints = [c for c in problem.constraints if c.constraint_type == "BOND"]
        assert len(bond_constraints) >= 1

        # The carbonyl carbon (180 ppm) should be atom 1 (first by descending ppm)
        carbonyl_constraint = bond_constraints[0]
        assert carbonyl_constraint.atom1_index == 1
        assert "carbonyl" in carbonyl_constraint.reason.lower()

    def test_detects_aldehyde_ketone_carbonyl(self):
        """Test that aldehyde/ketone carbonyl (200 ppm) is detected."""
        carbon_peaks = PeakList1D(
            peaks=[
                Peak1D(position=200.0, intensity=1000.0),  # Aldehyde/ketone
                Peak1D(position=30.0, intensity=800.0),   # CH3
            ],
            nucleus="13C",
        )

        problem = LSDInputGenerator.from_peak_data(
            carbon_peaks=carbon_peaks,
            molecular_formula="C2H4O",  # Acetaldehyde-like
            name="test",
        )

        # Should have BOND constraint for carbonyl
        bond_constraints = [c for c in problem.constraints if c.constraint_type == "BOND"]
        assert len(bond_constraints) >= 1
        assert "carbonyl" in bond_constraints[0].reason.lower()

    def test_no_carbonyl_detection_for_non_carbonyl_carbons(self):
        """Test that regular carbons are not detected as carbonyls."""
        carbon_peaks = PeakList1D(
            peaks=[
                Peak1D(position=130.0, intensity=1000.0),  # Aromatic
                Peak1D(position=45.0, intensity=800.0),   # Aliphatic
            ],
            nucleus="13C",
        )

        problem = LSDInputGenerator.from_peak_data(
            carbon_peaks=carbon_peaks,
            molecular_formula="C2H4",  # No oxygen
            name="test",
        )

        # Should have no constraints (no oxygen)
        assert len(problem.constraints) == 0


class TestPyLSDExtensions:
    """Tests for pyLSD-specific emission methods and generate() integration."""

    # --- emit_form tests ---

    def test_emit_form_ibuprofen(self):
        """emit_form returns 'FORM C13H18O2' for ibuprofen formula."""
        assert LSDInputGenerator.emit_form("C13H18O2") == "FORM C13H18O2"

    def test_emit_form_glucose(self):
        """emit_form returns 'FORM C6H12O6' for glucose formula."""
        assert LSDInputGenerator.emit_form("C6H12O6") == "FORM C6H12O6"

    # --- emit_elim tests ---

    def test_emit_elim_same_atoms(self):
        """emit_elim(4, 4) returns 'ELIM 4 4'."""
        assert LSDInputGenerator.emit_elim(4, 4) == "ELIM 4 4"

    def test_emit_elim_different_atoms(self):
        """emit_elim(2, 3) returns 'ELIM 2 3'."""
        assert LSDInputGenerator.emit_elim(2, 3) == "ELIM 2 3"

    # --- emit_shih tests ---

    def test_emit_shih_decimal(self):
        """emit_shih(10, 3.71) returns 'SHIH 10 3.71'."""
        assert LSDInputGenerator.emit_shih(10, 3.71) == "SHIH 10 3.71"

    def test_emit_shih_aromatic(self):
        """emit_shih(1, 7.25) returns 'SHIH 1 7.25'."""
        assert LSDInputGenerator.emit_shih(1, 7.25) == "SHIH 1 7.25"

    # --- generate() integration tests ---

    def test_generate_pylsd_form_in_header(self):
        """FORM line appears in output when pylsd_mode=True and molecular_formula set."""
        problem = LSDProblem(
            pylsd_mode=True,
            molecular_formula="C13H18O2",
        )
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        content = LSDInputGenerator.generate(problem)
        assert "FORM C13H18O2" in content
        # FORM must appear before first MULT line
        form_pos = content.index("FORM C13H18O2")
        mult_pos = content.index("MULT")
        assert form_pos < mult_pos

    def test_generate_no_form_without_pylsd_mode(self):
        """FORM line does NOT appear when pylsd_mode=False, even if formula is set."""
        problem = LSDProblem(
            pylsd_mode=False,
            molecular_formula="C13H18O2",
        )
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        content = LSDInputGenerator.generate(problem)
        # Only the comment version should appear, not the FORM command
        assert "FORM C13H18O2" not in content
        assert "; Molecular formula: C13H18O2" in content

    def test_generate_pylsd_elim_commands(self):
        """ELIM lines appear after FORM but before MULT when pylsd_mode=True."""
        problem = LSDProblem(
            pylsd_mode=True,
            molecular_formula="C13H18O2",
            elim_commands=[(4, 4)],
        )
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        content = LSDInputGenerator.generate(problem)
        assert "ELIM 4 4" in content
        # ELIM must appear after FORM and before first MULT
        form_pos = content.index("FORM C13H18O2")
        elim_pos = content.index("ELIM 4 4")
        mult_pos = content.index("MULT")
        assert form_pos < elim_pos < mult_pos

    def test_generate_shih_for_proton_shift(self):
        """SHIH line appears for atom with proton_shift set."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP3, 1, proton_shift=3.71))
        content = LSDInputGenerator.generate(problem)
        assert "SHIH 1 3.71" in content

    def test_generate_no_shih_for_none_proton_shift(self):
        """No SHIH line when atom proton_shift is None."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP3, 1, proton_shift=None))
        content = LSDInputGenerator.generate(problem)
        assert "SHIH 1" not in content

    def test_generate_hmbc_bond_range_in_output(self):
        """HMBC correlation with max_bonds=4 produces 'HMBC X Y 2 4' in output."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 1))
        problem.add_correlation(LSDCorrelation(1, 2, "HMBC", min_bonds=2, max_bonds=4))
        content = LSDInputGenerator.generate(problem)
        assert "HMBC 1 2 2 4" in content

    def test_generate_hmbc_default_range_no_trailing_numbers(self):
        """Default HMBC (2-3J) emits 'HMBC X Y' without trailing bond numbers."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 1))
        problem.add_correlation(LSDCorrelation(1, 2, "HMBC", min_bonds=2, max_bonds=3))
        content = LSDInputGenerator.generate(problem)
        assert "HMBC 1 2\n" in content or content.endswith("HMBC 1 2")
        assert "HMBC 1 2 2 3" not in content


class TestPyLSDValidator:
    """Tests for validate_pylsd_input() consistency checker."""

    def test_validate_pylsd_carbon_mismatch(self):
        """Raises ValueError when FORM declares 13 carbons but MULT defines 12."""
        from lucy_ng.lsd.generator import validate_pylsd_input
        problem = LSDProblem(molecular_formula="C13H18O2")
        # Add only 12 carbon atoms
        for i in range(1, 13):
            problem.add_atom(LSDAtom(i, "C", Hybridization.SP3, 0))
        with pytest.raises(ValueError, match="FORM/MULT mismatch"):
            validate_pylsd_input(problem)

    def test_validate_pylsd_carbon_match(self):
        """No error when FORM carbon count matches MULT carbon count."""
        from lucy_ng.lsd.generator import validate_pylsd_input
        problem = LSDProblem(molecular_formula="C2H4O2")
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 2))
        validate_pylsd_input(problem)  # Should not raise

    def test_validate_pylsd_no_formula(self):
        """No error when molecular_formula is None."""
        from lucy_ng.lsd.generator import validate_pylsd_input
        problem = LSDProblem(molecular_formula=None)
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP3, 0))
        validate_pylsd_input(problem)  # Should not raise

    def test_validate_pylsd_ignores_heteroatom_count(self):
        """Only carbon count is checked — mismatched oxygen count does not raise."""
        from lucy_ng.lsd.generator import validate_pylsd_input
        problem = LSDProblem(molecular_formula="C2H4O2")
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 2))
        # Only 1 oxygen, formula says 2 — should not raise
        problem.add_atom(LSDAtom(3, "O", Hybridization.SP3, 0))
        validate_pylsd_input(problem)  # Should not raise


class TestHydrogenAssignment:
    """Tests for missing hydrogen detection and assignment to oxygen."""

    def test_assigns_missing_h_to_hydroxyl_oxygen(self):
        """Test that missing H from MF is assigned to sp3 oxygen."""
        carbon_peaks = PeakList1D(
            peaks=[
                Peak1D(position=180.0, intensity=1000.0),  # Carbonyl
                Peak1D(position=45.0, intensity=800.0),   # CH2
            ],
            nucleus="13C",
        )

        # C2H4O2: 4 H total
        # If CH2 has 2 H, and carbonyl has 0 H, that's 2 H on carbons
        # Missing 2 H should go to sp3 oxygens
        problem = LSDInputGenerator.from_peak_data(
            carbon_peaks=carbon_peaks,
            molecular_formula="C2H4O2",
            name="test",
        )

        # Find sp3 oxygen atoms
        sp3_oxygens = [a for a in problem.atoms if a.element == "O" and a.hybridization == Hybridization.SP3]

        # At least one sp3 oxygen should have H=1 (hydroxyl)
        h_on_oxygens = sum(a.hydrogen_count for a in sp3_oxygens)
        assert h_on_oxygens >= 1, "Missing H should be assigned to sp3 oxygen"

    def test_carboxylic_acid_structure(self):
        """Test proper structure for carboxylic acid: C=O and O-H."""
        carbon_peaks = PeakList1D(
            peaks=[
                Peak1D(position=180.0, intensity=1000.0),  # COOH carbonyl
                Peak1D(position=22.0, intensity=800.0),   # CH3
            ],
            nucleus="13C",
        )

        # Acetic acid: CH3COOH = C2H4O2
        # CH3 has 3 H, COOH carbon has 0 H = 3 H on carbons
        # 4 H total - 3 on C = 1 H missing (goes to -OH)
        problem = LSDInputGenerator.from_peak_data(
            carbon_peaks=carbon_peaks,
            molecular_formula="C2H4O2",
            name="acetic_acid",
        )

        # Check atom counts
        carbons = [a for a in problem.atoms if a.element == "C"]
        oxygens = [a for a in problem.atoms if a.element == "O"]

        assert len(carbons) == 2
        assert len(oxygens) == 2

        # One oxygen should be sp2 (C=O), one sp3 (O-H)
        sp2_oxygens = [a for a in oxygens if a.hybridization == Hybridization.SP2]
        sp3_oxygens = [a for a in oxygens if a.hybridization == Hybridization.SP3]

        assert len(sp2_oxygens) == 1, "Should have one sp2 oxygen (C=O)"
        assert len(sp3_oxygens) == 1, "Should have one sp3 oxygen (O-H)"

        # sp3 oxygen should have 1 H (hydroxyl)
        assert sp3_oxygens[0].hydrogen_count == 1, "Hydroxyl oxygen should have 1 H"

        # Should have BOND constraint
        assert len(problem.constraints) >= 1
