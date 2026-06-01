#!/usr/bin/env python3
"""Verify top-3 SMILES in a merged.smi file for aromatic ring and exact formula match."""

import argparse
import json
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

_TOP_N = 3


def _parse_top3(path: Path) -> list[str]:
    """Read merged.smi and return at most the first 3 valid SMILES strings.

    Blank lines are skipped.  Invalid SMILES (``Chem.MolFromSmiles`` returns
    ``None``) are skipped rather than raising an exception.

    Args:
        path: Path to the merged.smi file (one SMILES per line, first
              whitespace-delimited field is the SMILES).

    Returns:
        List of up to 3 valid SMILES strings in file order.
    """
    valid: list[str] = []
    for raw_line in path.read_text().splitlines():
        parts = raw_line.strip().split()
        if not parts:
            continue
        smiles = parts[0]
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        valid.append(smiles)
        if len(valid) == _TOP_N:
            break
    return valid


def _check_smiles(smiles: str, formula: str) -> dict:
    """Check a single SMILES against the aromatic-ring and formula criteria.

    Args:
        smiles: A valid SMILES string (callers guarantee it parses).
        formula: Target molecular formula string (e.g. ``"C13H18O2"``).

    Returns:
        Dict with keys: smiles, aromatic_atoms, has_aromatic_ring,
        computed_formula, formula_match, passes.
    """
    mol = Chem.MolFromSmiles(smiles)
    aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
    has_aromatic_ring = aromatic_atoms >= 6
    computed_formula = rdMolDescriptors.CalcMolFormula(mol)
    formula_match = computed_formula == formula
    return {
        "smiles": smiles,
        "aromatic_atoms": aromatic_atoms,
        "has_aromatic_ring": has_aromatic_ring,
        "computed_formula": computed_formula,
        "formula_match": formula_match,
        "passes": has_aromatic_ring and formula_match,
    }


def main() -> None:
    """Entry point: parse args, verify top-3 SMILES, emit JSON, exit 0/1."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify top-3 SMILES in a merged.smi file for aromatic ring "
            "(>=6 aromatic atoms) and exact molecular formula match."
        )
    )
    parser.add_argument(
        "merged_smi",
        help="Path to merged.smi file (one SMILES per line).",
    )
    parser.add_argument(
        "formula",
        help='Exact molecular formula to match (e.g. "C13H18O2").',
    )
    args = parser.parse_args()

    smi_path = Path(args.merged_smi)
    if not smi_path.exists():
        result = {
            "pass": False,
            "error": "file not found",
            "formula": args.formula,
            "top_n_checked": _TOP_N,
            "checks": [],
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    top3_smiles = _parse_top3(smi_path)

    checks = [_check_smiles(s, args.formula) for s in top3_smiles]
    overall_pass = any(entry["passes"] for entry in checks)

    result = {
        "pass": overall_pass,
        "formula": args.formula,
        "top_n_checked": _TOP_N,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
