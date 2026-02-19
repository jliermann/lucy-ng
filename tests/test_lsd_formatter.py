"""Tests for DEFFFormatter -- SMILES to LSD SSTR/LINK fragment conversion."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from lucy_ng.fragments.lsd_formatter import DEFFFormatter


class TestSmilesToFragmentContent:
    """Test smiles_to_fragment_content static method."""

    def test_toluene_sstr_count(self) -> None:
        """Toluene (Cc1ccccc1) should produce 7 SSTR lines (7 heavy atoms)."""
        content = DEFFFormatter.smiles_to_fragment_content("Cc1ccccc1")
        sstr_lines = [ln for ln in content.splitlines() if ln.startswith("SSTR")]
        assert len(sstr_lines) == 7

    def test_toluene_link_count(self) -> None:
        """Toluene should produce 7 LINK lines (6 ring + 1 methyl-ring)."""
        content = DEFFFormatter.smiles_to_fragment_content("Cc1ccccc1")
        link_lines = [ln for ln in content.splitlines() if ln.startswith("LINK")]
        assert len(link_lines) == 7

    def test_toluene_1based_indices(self) -> None:
        """Atom indices in SSTR must be 1-based (S1 through S7)."""
        content = DEFFFormatter.smiles_to_fragment_content("Cc1ccccc1")
        sstr_lines = [ln for ln in content.splitlines() if ln.startswith("SSTR")]
        indices = sorted(
            int(ln.split()[1][1:]) for ln in sstr_lines  # extract N from SN
        )
        assert indices == [1, 2, 3, 4, 5, 6, 7]

    def test_toluene_hybridization(self) -> None:
        """Aromatic carbons get hyb=2, methyl carbon gets hyb=3."""
        content = DEFFFormatter.smiles_to_fragment_content("Cc1ccccc1")
        sstr_lines = [ln for ln in content.splitlines() if ln.startswith("SSTR")]
        # Collect hybridisation values (field index 3)
        hyb_values = [ln.split()[3] for ln in sstr_lines]
        assert hyb_values.count("2") == 6  # 6 aromatic carbons
        assert hyb_values.count("3") == 1  # 1 methyl sp3

    def test_toluene_h_counts(self) -> None:
        """Toluene: methyl=3H, 5 ArCH=1H, 1 ArC(subst)=0H."""
        content = DEFFFormatter.smiles_to_fragment_content("Cc1ccccc1")
        sstr_lines = [ln for ln in content.splitlines() if ln.startswith("SSTR")]
        h_counts = sorted(int(ln.split()[4]) for ln in sstr_lines)
        # 0, 1, 1, 1, 1, 1, 3
        assert h_counts == [0, 1, 1, 1, 1, 1, 3]

    def test_toluene_comment_line(self) -> None:
        """First line should be a comment with canonical SMILES."""
        content = DEFFFormatter.smiles_to_fragment_content("Cc1ccccc1")
        first_line = content.splitlines()[0]
        assert first_line.startswith("; Fragment:")

    def test_toluene_all_lines_valid(self) -> None:
        """Every line must start with SSTR, LINK, or ';'."""
        content = DEFFFormatter.smiles_to_fragment_content("Cc1ccccc1")
        for line in content.strip().splitlines():
            assert (
                line.startswith("SSTR S")
                or line.startswith("LINK S")
                or line.startswith(";")
            ), f"Unexpected line: {line}"

    def test_ethanol_atoms(self) -> None:
        """Ethanol (CCO) should produce 3 SSTR lines (C, C, O)."""
        content = DEFFFormatter.smiles_to_fragment_content("CCO")
        sstr_lines = [ln for ln in content.splitlines() if ln.startswith("SSTR")]
        assert len(sstr_lines) == 3
        # One of them must be oxygen
        elements = [ln.split()[2] for ln in sstr_lines]
        assert "O" in elements

    def test_ethanol_links(self) -> None:
        """Ethanol has 2 bonds -> 2 LINK lines."""
        content = DEFFFormatter.smiles_to_fragment_content("CCO")
        link_lines = [ln for ln in content.splitlines() if ln.startswith("LINK")]
        assert len(link_lines) == 2

    def test_invalid_smiles_raises(self) -> None:
        """Invalid SMILES should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid SMILES"):
            DEFFFormatter.smiles_to_fragment_content("not_a_smiles")

    def test_trailing_newline(self) -> None:
        """Content should end with a trailing newline."""
        content = DEFFFormatter.smiles_to_fragment_content("CCO")
        assert content.endswith("\n")


class TestFragmentFilename:
    """Test fragment_filename static method."""

    def test_canonical_equivalence(self) -> None:
        """Different SMILES for toluene must produce the same filename."""
        name1 = DEFFFormatter.fragment_filename("Cc1ccccc1")
        name2 = DEFFFormatter.fragment_filename("c1ccc(C)cc1")
        assert name1 == name2

    def test_filename_pattern(self) -> None:
        """Filename must match fragment_<12 hex chars>.lsd."""
        name = DEFFFormatter.fragment_filename("Cc1ccccc1")
        assert re.fullmatch(r"fragment_[0-9a-f]{12}\.lsd", name)

    def test_different_smiles_different_filenames(self) -> None:
        """Toluene and ethanol must produce different filenames."""
        name_toluene = DEFFFormatter.fragment_filename("Cc1ccccc1")
        name_ethanol = DEFFFormatter.fragment_filename("CCO")
        assert name_toluene != name_ethanol


class TestWriteFragmentFile:
    """Test write_fragment_file static method."""

    def test_writes_file(self, tmp_path: Path) -> None:
        """Fragment file should be written to the specified directory."""
        result = DEFFFormatter.write_fragment_file("Cc1ccccc1", output_dir=tmp_path)
        assert result.exists()
        assert result.parent == tmp_path

    def test_filename_matches(self, tmp_path: Path) -> None:
        """Written filename should match fragment_filename()."""
        result = DEFFFormatter.write_fragment_file("Cc1ccccc1", output_dir=tmp_path)
        expected_name = DEFFFormatter.fragment_filename("Cc1ccccc1")
        assert result.name == expected_name

    def test_file_content(self, tmp_path: Path) -> None:
        """Written file must contain SSTR and LINK lines and start with comment."""
        result = DEFFFormatter.write_fragment_file("Cc1ccccc1", output_dir=tmp_path)
        text = result.read_text()
        assert text.startswith("; Fragment:")
        assert "SSTR" in text
        assert "LINK" in text

    def test_default_output_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When output_dir is None, file is written to CWD."""
        monkeypatch.chdir(tmp_path)
        result = DEFFFormatter.write_fragment_file("CCO", output_dir=None)
        assert result.parent == tmp_path
        assert result.exists()


class TestDeffCommand:
    """Test deff_command static method."""

    def test_basic_command(self) -> None:
        """DEFF command must use double quotes around filepath."""
        cmd = DEFFFormatter.deff_command(1, "fragment_abc123.lsd")
        assert cmd == 'DEFF F1 "fragment_abc123.lsd"'

    def test_double_quotes_not_single(self) -> None:
        """Verify double quotes are used (not single quotes)."""
        cmd = DEFFFormatter.deff_command(2, "test.lsd")
        assert '"test.lsd"' in cmd
        assert "'" not in cmd


class TestFexpCommand:
    """Test fexp_command static method."""

    def test_single_fragment(self) -> None:
        """Single fragment -> FEXP "F1"."""
        cmd = DEFFFormatter.fexp_command([1])
        assert cmd == 'FEXP "F1"'

    def test_multiple_or(self) -> None:
        """Multiple fragments with OR."""
        cmd = DEFFFormatter.fexp_command([1, 2, 3])
        assert cmd == 'FEXP "F1 OR F2 OR F3"'

    def test_badlist_not(self) -> None:
        """Badlist with NOT logic."""
        cmd = DEFFFormatter.fexp_command([1], logic="NOT")
        assert cmd == 'FEXP "NOT F1"'

    def test_empty_list(self) -> None:
        """Empty fragment list returns empty string."""
        cmd = DEFFFormatter.fexp_command([])
        assert cmd == ""
