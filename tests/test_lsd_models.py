"""Tests for LSD data models."""

import pytest

from lucy_ng.lsd.models import Hybridization, LSDAtom, LSDCorrelation, LSDProblem


class TestHybridization:
    """Tests for Hybridization enum."""

    def test_hybridization_values(self):
        """Test hybridization enum values match LSD format."""
        assert Hybridization.SP.value == 1
        assert Hybridization.SP2.value == 2
        assert Hybridization.SP3.value == 3


class TestLSDAtom:
    """Tests for LSDAtom dataclass."""

    def test_create_carbon_sp2(self):
        """Test creating sp2 carbon atom."""
        atom = LSDAtom(index=1, element="C", hybridization=Hybridization.SP2, hydrogen_count=0)
        assert atom.index == 1
        assert atom.element == "C"
        assert atom.hybridization == Hybridization.SP2
        assert atom.hydrogen_count == 0
        assert atom.charge == 0

    def test_create_carbon_sp3_with_hydrogens(self):
        """Test creating sp3 carbon with hydrogens."""
        atom = LSDAtom(index=2, element="C", hybridization=Hybridization.SP3, hydrogen_count=2)
        assert atom.hydrogen_count == 2

    def test_create_nitrogen_with_charge(self):
        """Test creating charged nitrogen."""
        atom = LSDAtom(
            index=3, element="N", hybridization=Hybridization.SP3,
            hydrogen_count=4, charge=1
        )
        assert atom.element == "N"
        assert atom.charge == 1

    def test_invalid_element_raises(self):
        """Test that invalid element raises ValueError."""
        with pytest.raises(ValueError, match="Invalid element"):
            LSDAtom(index=1, element="X", hybridization=Hybridization.SP3, hydrogen_count=0)

    def test_invalid_index_raises(self):
        """Test that index < 1 raises ValueError."""
        with pytest.raises(ValueError, match="index must be >= 1"):
            LSDAtom(index=0, element="C", hybridization=Hybridization.SP3, hydrogen_count=0)

    def test_invalid_hydrogen_count_raises(self):
        """Test that negative hydrogen count raises ValueError."""
        with pytest.raises(ValueError, match="Hydrogen count"):
            LSDAtom(index=1, element="C", hybridization=Hybridization.SP3, hydrogen_count=-1)

    def test_invalid_charge_raises(self):
        """Test that invalid charge raises ValueError."""
        with pytest.raises(ValueError, match="Charge"):
            LSDAtom(index=1, element="C", hybridization=Hybridization.SP3, hydrogen_count=0, charge=3)

    def test_to_mult_line_basic(self):
        """Test MULT line generation without charge."""
        atom = LSDAtom(index=1, element="C", hybridization=Hybridization.SP2, hydrogen_count=0)
        assert atom.to_mult_line() == "MULT 1 C 2 0"

    def test_to_mult_line_with_hydrogens(self):
        """Test MULT line with hydrogens."""
        atom = LSDAtom(index=5, element="C", hybridization=Hybridization.SP3, hydrogen_count=3)
        assert atom.to_mult_line() == "MULT 5 C 3 3"

    def test_to_mult_line_with_charge(self):
        """Test MULT line with charge."""
        atom = LSDAtom(
            index=2, element="N", hybridization=Hybridization.SP3,
            hydrogen_count=4, charge=1
        )
        assert atom.to_mult_line() == "MULT 2 N 3 4 1"

    def test_chemical_shifts(self):
        """Test storing chemical shift values."""
        atom = LSDAtom(
            index=1, element="C", hybridization=Hybridization.SP2,
            hydrogen_count=1, carbon_shift=129.5, proton_shift=7.25
        )
        assert atom.carbon_shift == 129.5
        assert atom.proton_shift == 7.25


class TestLSDCorrelation:
    """Tests for LSDCorrelation dataclass."""

    def test_create_hsqc_correlation(self):
        """Test creating HSQC correlation."""
        corr = LSDCorrelation(atom1_index=1, atom2_index=1, correlation_type="HSQC")
        assert corr.correlation_type == "HSQC"

    def test_create_hmbc_correlation(self):
        """Test creating HMBC correlation with bond distances."""
        corr = LSDCorrelation(
            atom1_index=1, atom2_index=2, correlation_type="HMBC",
            min_bonds=2, max_bonds=3
        )
        assert corr.min_bonds == 2
        assert corr.max_bonds == 3

    def test_create_cosy_correlation(self):
        """Test creating COSY correlation."""
        corr = LSDCorrelation(atom1_index=2, atom2_index=3, correlation_type="COSY")
        assert corr.correlation_type == "COSY"

    def test_invalid_type_raises(self):
        """Test that invalid correlation type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid correlation type"):
            LSDCorrelation(atom1_index=1, atom2_index=2, correlation_type="INVALID")

    def test_invalid_index_raises(self):
        """Test that index < 1 raises ValueError."""
        with pytest.raises(ValueError, match="indices must be >= 1"):
            LSDCorrelation(atom1_index=0, atom2_index=1, correlation_type="HSQC")

    def test_to_lsd_line_hsqc(self):
        """Test HSQC line generation."""
        corr = LSDCorrelation(atom1_index=4, atom2_index=4, correlation_type="HSQC")
        assert corr.to_lsd_line() == "HSQC 4 4"

    def test_to_lsd_line_hmbc(self):
        """Test HMBC line generation with bond distances."""
        corr = LSDCorrelation(
            atom1_index=1, atom2_index=3, correlation_type="HMBC",
            min_bonds=2, max_bonds=3
        )
        assert corr.to_lsd_line() == "HMBC 1 3 2 3"

    def test_to_lsd_line_cosy(self):
        """Test COSY line generation."""
        corr = LSDCorrelation(atom1_index=2, atom2_index=5, correlation_type="COSY")
        assert corr.to_lsd_line() == "COSY 2 5"


class TestLSDProblem:
    """Tests for LSDProblem dataclass."""

    def test_create_empty_problem(self):
        """Test creating empty problem."""
        problem = LSDProblem(name="test")
        assert problem.name == "test"
        assert len(problem.atoms) == 0
        assert len(problem.correlations) == 0

    def test_add_atom(self):
        """Test adding atoms to problem."""
        problem = LSDProblem()
        atom = LSDAtom(index=1, element="C", hybridization=Hybridization.SP2, hydrogen_count=0)
        problem.add_atom(atom)
        assert len(problem.atoms) == 1

    def test_add_correlation(self):
        """Test adding correlations to problem."""
        problem = LSDProblem()
        corr = LSDCorrelation(atom1_index=1, atom2_index=1, correlation_type="HSQC")
        problem.add_correlation(corr)
        assert len(problem.correlations) == 1

    def test_get_atom_by_index(self):
        """Test retrieving atom by index."""
        problem = LSDProblem()
        atom = LSDAtom(index=5, element="C", hybridization=Hybridization.SP3, hydrogen_count=2)
        problem.add_atom(atom)

        found = problem.get_atom_by_index(5)
        assert found is atom

        not_found = problem.get_atom_by_index(99)
        assert not_found is None

    def test_get_correlations_for_atom(self):
        """Test getting correlations for a specific atom."""
        problem = LSDProblem()
        problem.add_correlation(LSDCorrelation(1, 1, "HSQC"))
        problem.add_correlation(LSDCorrelation(1, 2, "HMBC"))
        problem.add_correlation(LSDCorrelation(2, 3, "COSY"))

        corrs = problem.get_correlations_for_atom(1)
        assert len(corrs) == 2

    def test_carbon_count(self):
        """Test carbon count property."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 2))
        problem.add_atom(LSDAtom(3, "O", Hybridization.SP3, 1))

        assert problem.carbon_count == 2
        assert problem.heteroatom_count == 1

    def test_validate_duplicate_indices(self):
        """Test validation catches duplicate atom indices."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP3, 2))  # Duplicate

        issues = problem.validate()
        assert any("Duplicate" in issue for issue in issues)

    def test_validate_missing_correlation_atom(self):
        """Test validation catches correlations to non-existent atoms."""
        problem = LSDProblem()
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_correlation(LSDCorrelation(99, 1, "HMBC"))  # Atom 99 doesn't exist

        issues = problem.validate()
        assert any("non-existent" in issue for issue in issues)

    def test_summary(self):
        """Test problem summary generation."""
        problem = LSDProblem(name="ibuprofen", molecular_formula="C13H18O2")
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        problem.add_atom(LSDAtom(2, "O", Hybridization.SP2, 0))
        problem.add_correlation(LSDCorrelation(1, 1, "HSQC"))

        summary = problem.summary()
        assert "ibuprofen" in summary
        assert "C13H18O2" in summary
        assert "HSQC: 1" in summary
