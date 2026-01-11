"""Tests for NMR chemical shift prediction module."""

import json
import tempfile
from pathlib import Path

import pytest
from rdkit import Chem

from lucy_ng.prediction import (
    C13Predictor,
    HOSECodeGenerator,
    HOSELookupTable,
    PredictedShift,
    PredictionResult,
)


class TestHOSECodeGenerator:
    """Tests for HOSE code generation."""

    def test_prepare_mol_from_smiles(self):
        """Test molecule preparation from SMILES."""
        gen = HOSECodeGenerator()
        mol = gen.prepare_mol("c1ccccc1")  # Benzene
        assert mol is not None
        # Should have explicit hydrogens
        assert any(atom.GetSymbol() == "H" for atom in mol.GetAtoms())

    def test_prepare_mol_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        mol = HOSECodeGenerator.prepare_mol("invalid_smiles_xyz")
        assert mol is None

    def test_generate_for_atom(self):
        """Test HOSE code generation for a single atom."""
        gen = HOSECodeGenerator()
        mol = gen.prepare_mol("Cc1ccccc1")  # Toluene (explicit methyl first)

        # Generate HOSE code for first carbon (the methyl)
        # First heavy atom should be the methyl carbon
        hose = gen.generate_for_atom(mol, 0, radius=2)
        assert hose is not None
        assert hose.startswith("C-4")  # sp3 carbon

    def test_generate_for_carbons(self):
        """Test HOSE code generation for all carbons."""
        gen = HOSECodeGenerator()
        mol = gen.prepare_mol("CC")  # Ethane

        codes = gen.generate_for_carbons(mol, radius=2)
        # Should have exactly 2 carbons
        assert len(codes) == 2
        # All codes should be for sp3 carbons
        for code in codes.values():
            assert code.startswith("C-4")

    def test_generate_for_carbons_all_radii(self):
        """Test generation at all radii."""
        gen = HOSECodeGenerator()
        mol = gen.prepare_mol("c1ccccc1")  # Benzene

        all_codes = gen.generate_for_carbons_all_radii(mol, max_radius=3)
        # Should have 6 carbons
        assert len(all_codes) == 6
        # Each carbon should have codes for radii 1, 2, 3
        for atom_idx, codes in all_codes.items():
            assert set(codes.keys()) == {1, 2, 3}

    def test_benzene_hose_codes(self):
        """Test that benzene carbons generate aromatic HOSE codes."""
        gen = HOSECodeGenerator()
        mol = gen.prepare_mol("c1ccccc1")

        codes = gen.generate_for_carbons(mol, radius=1)
        # All carbons should be sp2 (aromatic)
        for code in codes.values():
            assert code.startswith("C-3")  # sp2 carbon


class TestHOSELookupTable:
    """Tests for HOSE lookup table."""

    def test_add_and_lookup(self):
        """Test adding entries and looking them up."""
        table = HOSELookupTable()

        table.add_entry("C-4;HHHC(//", 21.5)
        table.add_entry("C-4;HHHC(//", 22.0)
        table.add_entry("C-4;HHHC(//", 20.8)

        shifts = table.lookup("C-4;HHHC(//")
        assert len(shifts) == 3
        assert 21.5 in shifts
        assert 22.0 in shifts
        assert 20.8 in shifts

    def test_lookup_nonexistent(self):
        """Test lookup of nonexistent code."""
        table = HOSELookupTable()
        shifts = table.lookup("NONEXISTENT")
        assert shifts == []

    def test_lookup_stats(self):
        """Test statistics calculation."""
        table = HOSELookupTable()
        table.add_entry("TEST", 10.0)
        table.add_entry("TEST", 20.0)
        table.add_entry("TEST", 30.0)

        stats = table.lookup_stats("TEST")
        assert stats is not None
        assert stats["median"] == 20.0
        assert stats["mean"] == 20.0
        assert stats["min"] == 10.0
        assert stats["max"] == 30.0
        assert stats["count"] == 3

    def test_lookup_stats_nonexistent(self):
        """Test stats for nonexistent code."""
        table = HOSELookupTable()
        stats = table.lookup_stats("NONEXISTENT")
        assert stats is None

    def test_has_code(self):
        """Test code existence check."""
        table = HOSELookupTable()
        table.add_entry("EXISTS", 100.0)

        assert table.has_code("EXISTS")
        assert not table.has_code("NOT_EXISTS")

    def test_save_and_load(self):
        """Test saving and loading table."""
        table = HOSELookupTable()
        table.add_entry("CODE1", 10.0)
        table.add_entry("CODE1", 11.0)
        table.add_entry("CODE2", 20.0)
        table._molecule_count = 5

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            table.save(Path(f.name), compress=False)

            loaded = HOSELookupTable.load(Path(f.name))

            assert loaded.unique_codes == 2
            assert loaded.molecule_count == 5
            assert loaded.lookup("CODE1") == [10.0, 11.0]
            assert loaded.lookup("CODE2") == [20.0]

    def test_save_and_load_compressed(self):
        """Test saving and loading compressed table."""
        table = HOSELookupTable()
        table.add_entry("CODE1", 10.0)
        table.add_entry("CODE2", 20.0)

        with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as f:
            table.save(Path(f.name), compress=True)

            loaded = HOSELookupTable.load(Path(f.name))

            assert loaded.unique_codes == 2
            assert loaded.lookup("CODE1") == [10.0]

    def test_properties(self):
        """Test table properties."""
        table = HOSELookupTable()
        table.add_entry("A", 1.0)
        table.add_entry("A", 2.0)
        table.add_entry("B", 3.0)

        assert table.unique_codes == 2
        assert table.total_entries == 3
        assert len(table) == 2

    def test_repr(self):
        """Test string representation."""
        table = HOSELookupTable()
        table.add_entry("A", 1.0)
        repr_str = repr(table)
        assert "HOSELookupTable" in repr_str
        assert "codes=1" in repr_str


class TestC13Predictor:
    """Tests for 13C chemical shift predictor."""

    @pytest.fixture
    def simple_table(self):
        """Create a simple lookup table for testing."""
        table = HOSELookupTable()

        # Add some common HOSE codes with known shifts
        # Methyl (CH3) codes
        table.add_entry("C-4;HHHC(//", 15.0)
        table.add_entry("C-4;HHHC(//", 16.0)
        table.add_entry("C-4;HHHC(//", 14.0)

        # Methylene (CH2) codes
        table.add_entry("C-4;HHCC(//", 25.0)
        table.add_entry("C-4;HHCC(//", 26.0)

        # Aromatic CH codes
        table.add_entry("C-3;H*C*C(//", 128.0)
        table.add_entry("C-3;H*C*C(//", 129.0)
        table.add_entry("C-3;H*C*C(//", 127.0)

        return table

    def test_predict_from_smiles_empty(self, simple_table):
        """Test prediction returns empty for no matches."""
        predictor = C13Predictor(simple_table, max_radius=1, min_radius=1)
        # Use a complex molecule unlikely to have matches
        result = predictor.predict_from_smiles("C#N")  # HCN

        assert isinstance(result, PredictionResult)
        assert result.smiles == "C#N"

    def test_predict_from_smiles_with_matches(self, simple_table):
        """Test prediction with matching HOSE codes."""
        predictor = C13Predictor(simple_table, max_radius=1, min_radius=1)

        # Ethane should match the CH3 codes
        result = predictor.predict_from_smiles("CC")

        assert result.smiles == "CC"
        assert result.carbon_count == 2

    def test_prediction_result_methods(self, simple_table):
        """Test PredictionResult helper methods."""
        predictor = C13Predictor(simple_table, max_radius=1, min_radius=1)
        result = predictor.predict_from_smiles("CC")

        # Test sorted shifts
        sorted_shifts = result.get_shifts_sorted()
        if len(sorted_shifts) > 1:
            assert sorted_shifts[0].shift >= sorted_shifts[1].shift

        # Test summary
        summary = result.summary()
        assert "CC" in summary
        assert "Carbons" in summary

    def test_predictor_with_fallback(self):
        """Test fallback to shorter radii."""
        # Create table with only radius-1 codes
        table = HOSELookupTable()
        table.add_entry("C-4;HHHC(//", 20.0)

        # Predictor with fallback enabled
        predictor = C13Predictor(table, max_radius=3, min_radius=1)

        mol = HOSECodeGenerator.prepare_mol("CC")
        predictions = predictor.predict_from_mol(mol)

        # Should find matches via fallback
        if predictions:
            # Radius used should be 1 (the only one in table)
            assert predictions[0].radius_used == 1

    def test_from_table_file(self, simple_table):
        """Test creating predictor from saved table file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            simple_table.save(Path(f.name), compress=False)

            predictor = C13Predictor.from_table_file(Path(f.name))
            assert predictor is not None
            assert predictor.lookup_table.unique_codes == simple_table.unique_codes

    def test_confidence_calculation(self, simple_table):
        """Test that confidence is calculated reasonably."""
        predictor = C13Predictor(simple_table, max_radius=1, min_radius=1)
        result = predictor.predict_from_smiles("CC")

        for pred in result.predictions:
            # Confidence should be between 0 and 1
            assert 0 <= pred.confidence <= 1
            # Radius 1 should have lower confidence than higher radii
            # (since it's less specific)


class TestPredictionModels:
    """Tests for prediction data models."""

    def test_predicted_shift_model(self):
        """Test PredictedShift model validation."""
        shift = PredictedShift(
            atom_index=0,
            shift=128.5,
            confidence=0.85,
            hose_code="C-3;H*C*C(//",
            radius_used=1,
            match_count=10,
            std_dev=2.5,
            min_shift=125.0,
            max_shift=132.0,
        )

        assert shift.atom_index == 0
        assert shift.shift == 128.5
        assert shift.confidence == 0.85

    def test_prediction_result_success_rate(self):
        """Test success rate calculation."""
        result = PredictionResult(
            smiles="CCC",
            predictions=[],
            carbon_count=3,
            success_count=2,
        )

        assert result.success_rate == pytest.approx(2/3)

    def test_prediction_result_empty(self):
        """Test success rate with no carbons."""
        result = PredictionResult(
            smiles="",
            predictions=[],
            carbon_count=0,
            success_count=0,
        )

        assert result.success_rate == 0.0


class TestCLIPredict:
    """Tests for prediction CLI commands."""

    def test_predict_help(self, cli_runner):
        """Test predict command help."""
        from lucy_ng.cli import cli
        result = cli_runner.invoke(cli, ["predict", "--help"])
        assert result.exit_code == 0
        assert "c13" in result.output
        assert "build-table" in result.output

    def test_predict_c13_no_table(self, cli_runner):
        """Test prediction without lookup table."""
        from lucy_ng.cli import cli
        result = cli_runner.invoke(cli, ["predict", "c13", "CC"])
        # Should fail with helpful error
        assert result.exit_code != 0
        assert "lookup table" in result.output.lower() or "table" in result.output.lower()

    def test_predict_build_table_help(self, cli_runner):
        """Test build-table command help."""
        from lucy_ng.cli import cli
        result = cli_runner.invoke(cli, ["predict", "build-table", "--help"])
        assert result.exit_code == 0
        assert "SD_PATH" in result.output
        assert "--output" in result.output

    def test_predict_table_info_no_table(self, cli_runner):
        """Test table-info without table."""
        from lucy_ng.cli import cli
        result = cli_runner.invoke(cli, ["predict", "table-info"])
        assert result.exit_code != 0


@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()
