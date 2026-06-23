#!/usr/bin/env python3
"""Verify CASE solutions.

Two modes:

* Default (legacy) mode: ``verify_case_solution.py <merged_smi> <formula>`` —
  verify the top-3 SMILES in a merged.smi file for an aromatic ring and exact
  molecular-formula match. Exit 0 if any candidate passes else 1. Unchanged.

* ``check-identity`` mode: derive a deterministic structural identity
  (InChIKey + canonical SMILES) from a solution SMILES, look it up in the
  bundled dereplication DB via two complementary paths (InChIKey-first for the
  nmrshiftdb partition, canonical-SMILES fallback for the COCONUT partition),
  and gate a reported trivial name against the tool-derived identity. A
  name<->structure disagreement DOWNGRADES the name to "tentative" with a
  warning; it never hard-fails (exit 0 always for this subcommand).
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

_TOP_N = 3

# COCONUT accession pattern (e.g. "CNP0220816"): a DB hit whose name is an
# accession means the structure is known but no human/trivial name is stored.
_COCONUT_ACCESSION_RE = re.compile(r"^CNP\d+$", re.IGNORECASE)

# Generic filler tokens dropped before token-set name comparison.
_NAME_FILLER_TOKENS = frozenset({"dye", "the", "a", "an", "of"})


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


def _resolve_db_path(db_path: str | Path | None) -> Path | None:
    """Resolve the dereplication DB path.

    Prefers the explicit ``db_path`` arg, then ``DatabaseFinder``. Falls back to
    an inline probe (``LUCY_DATABASE`` env -> ``data/reference/`` -> Dropbox dev
    path) when ``lucy_ng`` is not importable (RESEARCH Pitfall 5).
    """
    if db_path is not None:
        p = Path(db_path)
        return p if p.exists() else None

    try:
        from lucy_ng.database.finder import DatabaseFinder

        return DatabaseFinder.find_derep_database()
    except Exception:  # pragma: no cover - import fallback path
        import os

        env_db = os.environ.get("LUCY_DATABASE")
        candidates = [
            Path(env_db) if env_db else None,
            Path("data/reference/lucy-ng-derep.db"),
            Path.home()
            / "Dropbox"
            / "develop"
            / "lucy-ng"
            / "data"
            / "reference"
            / "lucy-ng-derep.db",
        ]
        for cand in candidates:
            if cand is not None and cand.exists():
                return cand
        return None


def derive_identity(smiles: str, db_path: str | Path | None = None) -> dict:
    """Derive a deterministic structural identity for ``smiles`` and look it up.

    Identity is derived with RDKit (never a recalled name): canonical SMILES via
    ``Chem.MolToSmiles`` with DEFAULT flags only (byte-equality with the
    importer's stored canonicalization, RESEARCH Finding 2) and an InChIKey via
    ``Chem.MolToInchiKey``.

    DB lookup is two-path and COMPLEMENTARY:

    * Path 1 (InChIKey-first) reaches the nmrshiftdb partition (inchi_key
      populated, smiles empty).
    * Path 2 (canonical-SMILES fallback, only if Path 1 misses) reaches the
      COCONUT partition (smiles populated, inchi_key empty).

    Args:
        smiles: A solution SMILES string (semi-trusted CASE-pipeline output).
        db_path: Optional explicit DB path; auto-resolved when None.

    Returns:
        A dict always carrying ``matched`` plus ``confidence``. On a hit it adds
        ``name``, ``source``, ``inchi_key``, ``canonical_smiles``. On no hit it
        carries the structural identity with ``confidence == "novel"``. Invalid
        SMILES return ``{"matched": False, "error": ..., "confidence": "novel"}``.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"matched": False, "error": "invalid smiles", "confidence": "novel"}

    canonical_smiles = Chem.MolToSmiles(mol)
    inchi_key = Chem.MolToInchiKey(mol)

    resolved_db = _resolve_db_path(db_path)
    if resolved_db is None:
        return {
            "matched": False,
            "inchi_key": inchi_key,
            "canonical_smiles": canonical_smiles,
            "confidence": "novel",
            "db_unavailable": True,
        }

    con = sqlite3.connect(f"file:{resolved_db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        # Path 1: InChIKey-first (reaches nmrshiftdb partition).
        row = con.execute(
            "SELECT name, source FROM compounds "
            "WHERE inchi_key = ? AND inchi_key != '' LIMIT 1",
            (inchi_key,),
        ).fetchone()
        # Path 2: canonical-SMILES fallback (reaches coconut partition).
        if row is None:
            row = con.execute(
                "SELECT name, source FROM compounds "
                "WHERE smiles = ? AND smiles != '' LIMIT 1",
                (canonical_smiles,),
            ).fetchone()
    finally:
        con.close()

    if row is None:
        return {
            "matched": False,
            "inchi_key": inchi_key,
            "canonical_smiles": canonical_smiles,
            "confidence": "novel",
        }

    name = row["name"]
    result: dict = {
        "matched": True,
        "name": name,
        "source": row["source"],
        "inchi_key": inchi_key,
        "canonical_smiles": canonical_smiles,
    }
    # COCONUT-accession name => structure known, but no human/trivial name.
    if name is not None and _COCONUT_ACCESSION_RE.match(name.strip()):
        result["confidence"] = "confirmed-structure"
        result["trivial_name_confirmed"] = False
    else:
        result["confidence"] = "confirmed"
    return result


def _normalize_name(name: str | None) -> set[str]:
    """Token-normalise a (possibly ';'-delimited) chemical name for matching.

    Drops COCONUT-accession tokens, splits ';'-delimited synonym lists,
    lowercases, replaces punctuation with spaces, splits into tokens, and
    discards generic filler tokens. Returns the union token set across all
    synonyms. Used ONLY for the tolerant ``name_match`` decision — never for
    structural identity.
    """
    if not name:
        return set()
    tokens: set[str] = set()
    for synonym in name.split(";"):
        synonym = synonym.strip()
        if not synonym or _COCONUT_ACCESSION_RE.match(synonym):
            continue
        cleaned = re.sub(r"[,()'\-–—.]", " ", synonym.lower())
        for tok in cleaned.split():
            if tok and tok not in _NAME_FILLER_TOKENS:
                tokens.add(tok)
    return tokens


def _synonym_token_sets(name: str | None) -> list[set[str]]:
    """Return one token set per ';'-delimited synonym (filler/accession dropped)."""
    if not name:
        return []
    sets: list[set[str]] = []
    for synonym in name.split(";"):
        synonym = synonym.strip()
        if not synonym or _COCONUT_ACCESSION_RE.match(synonym):
            continue
        cleaned = re.sub(r"[,()'\-–—.]", " ", synonym.lower())
        toks = {t for t in cleaned.split() if t and t not in _NAME_FILLER_TOKENS}
        if toks:
            sets.append(toks)
    return sets


def _name_match(reported_name: str | None, derived_name: str | None) -> bool:
    """Tolerant token-set comparison (NOT exact, NOT naive substring).

    True iff the reported-name token set shares its chemical token(s) with any
    ';'-split synonym of the derived name — specifically when the reported token
    set is a non-empty subset of some synonym's token set, OR the two sets are
    equal. Whole-token equality is required (so "in" does NOT match "indigo"),
    and synonym-list / punctuation / word-order differences do not false-fail.
    """
    reported = _normalize_name(reported_name)
    if not reported:
        return False
    for syn_tokens in _synonym_token_sets(derived_name):
        if not syn_tokens:
            continue
        if reported == syn_tokens or reported <= syn_tokens:
            return True
    return False


def _check_identity(args: argparse.Namespace) -> None:
    """``check-identity`` subcommand: derive identity, gate the reported name.

    Emits the identity JSON block and ALWAYS exits 0 (D-06: a name<->structure
    disagreement downgrades to "tentative" + warning; it does not hard-fail).
    """
    derived = derive_identity(args.smiles, db_path=args.db)
    reported_name = args.reported_name
    matched = derived.get("matched", False)

    if reported_name is None or not matched:
        name_match: bool | None = None
    else:
        name_match = _name_match(reported_name, derived.get("name"))

    warning: str | None = None
    if matched and (name_match is True or reported_name is None):
        # Preserve the structure-only confidence for COCONUT-accession hits.
        verdict = (
            "confirmed-structure"
            if derived.get("confidence") == "confirmed-structure"
            else "confirmed"
        )
    elif (matched and name_match is False) or (not matched and reported_name is not None):
        verdict = "tentative"
        derived_label = derived.get("name") or "none (structure not in DB)"
        warning = (
            f"WARNING: reported name '{reported_name}' does not match "
            f"tool-derived identity '{derived_label}'; name downgraded to tentative."
        )
    else:
        verdict = "novel"

    result = {
        "mode": "identity",
        "reported_name": reported_name,
        "derived": derived,
        "name_match": name_match,
        "verdict": verdict,
        "warning": warning,
    }
    print(json.dumps(result, indent=2))
    sys.exit(0)


def main() -> None:
    """Entry point: parse args, verify top-3 SMILES, emit JSON, exit 0/1.

    Supports two invocations: the legacy positional ``<merged_smi> <formula>``
    default mode (exit 0/1) and the ``check-identity`` subcommand (always exit
    0). The subcommand is detected by the first positional argument so the
    legacy two-positional form keeps working unchanged.
    """
    # Route to the identity subcommand when explicitly requested.
    if len(sys.argv) > 1 and sys.argv[1] == "check-identity":
        id_parser = argparse.ArgumentParser(
            prog="verify_case_solution.py check-identity",
            description=(
                "Derive a deterministic structural identity (InChIKey + "
                "canonical SMILES) from a solution SMILES and gate a reported "
                "name against the tool-derived identity."
            ),
        )
        id_parser.add_argument("--smiles", required=True, help="Solution SMILES.")
        id_parser.add_argument(
            "--reported-name",
            default=None,
            help="Trivial name asserted by the analyst (optional).",
        )
        id_parser.add_argument(
            "--db",
            default=None,
            help="Optional explicit path to the dereplication DB.",
        )
        id_args = id_parser.parse_args(sys.argv[2:])
        _check_identity(id_args)
        return  # _check_identity calls sys.exit(0); defensive return.

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
