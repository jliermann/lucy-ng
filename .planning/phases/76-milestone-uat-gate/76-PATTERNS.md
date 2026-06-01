# Phase 76: Milestone UAT Gate - Pattern Map

**Mapped:** 2026-06-01
**Files analyzed:** 2 (verify_case_solution.py + its pytest test file)
**Analogs found:** 2 / 2

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/verify_case_solution.py` | utility / standalone script | file-I/O + transform | `scripts/figshare_upload.py` | role-match (same module-level main + argparse + JSON output + sys.exit pattern) |
| `tests/test_verify_case_solution.py` | test | request-response (pure unit) | `tests/test_lsd_regression.py` | exact (same RDKit + SMILES-file reading + tmp_path pattern) |

---

## Pattern Assignments

### `scripts/verify_case_solution.py` (utility, file-I/O + transform)

**Primary analog:** `scripts/figshare_upload.py`
**RDKit analog:** `src/lucy_ng/ranking/ranker.py` (aromatic check) + `src/lucy_ng/dereplication/nmrshiftdb.py` (CalcMolFormula)

#### Shebang + module docstring (figshare_upload.py lines 1-2)
```python
#!/usr/bin/env python3
"""Upload compounds database to Figshare with chunked/resumable uploads."""
```
Apply the same shebang + one-line docstring. For the new file: `"""Verify top-3 SMILES in a merged.smi file for aromatic ring and exact formula match."""`

#### Imports pattern (figshare_upload.py lines 4-11)
```python
import hashlib
import json
import os
import sys
from pathlib import Path

import requests
```
For the new script, replace third-party imports with rdkit:
```python
import argparse
import json
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
```
`argparse` replaces positional-arg parsing done ad-hoc in figshare_upload.py (sys.argv indexing). The new script takes two positional args (`merged_smi` path, `formula`) so argparse is cleaner.

#### Argument handling + early validation (figshare_upload.py lines 73-87)
```python
def main():
    token = os.environ.get("FIGSHARE_TOKEN")

    if len(sys.argv) > 1:
        token = sys.argv[1]

    if not token:
        print("Usage: python figshare_upload.py <FIGSHARE_TOKEN>")
        print("   or: export FIGSHARE_TOKEN='...' && python figshare_upload.py")
        print("\nGet token at: https://figshare.com/account/applications")
        sys.exit(1)

    if not FILE_PATH.exists():
        print(f"Error: File not found: {FILE_PATH}")
        sys.exit(1)
```
Pattern to copy: `main()` function with upfront guard + `sys.exit(1)` on bad input/missing file. The new script should check that the `.smi` file exists before parsing SMILES.

#### JSON output + sys.exit convention (figshare_upload.py lines 180-192 + zenodo_upload.py lines 153-167)
Both scripts use `print(...)` for all output (no logger) and `sys.exit(1)` for error paths. The new `verify_case_solution.py` should follow the same convention but emit a JSON object to stdout (since D-76-03 requires JSON output):
```python
    result = {"pass": ..., "checks": [...], "formula": formula, "top_n_checked": 3}
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["pass"] else 1)

if __name__ == "__main__":
    main()
```
Exit code 0 = PASS, exit code 1 = FAIL (matches Unix convention, integrates with CI if needed later).

#### RDKit aromatic check (ranker.py lines 3, 86-89)
```python
from rdkit import Chem

# ...
mol = Chem.MolFromSmiles(solution.smiles)
if mol is not None:
    has_aromatic = any(atom.GetIsAromatic() for atom in mol.GetAtoms())
```
This is the exact pattern already used in the codebase for per-atom aromatic detection. D-76-03 requires >= 6 aromatic atoms (not just any), so adapt to:
```python
mol = Chem.MolFromSmiles(smiles)
if mol is None:
    # invalid SMILES — fail
    ...
aromatic_atom_count = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
has_aromatic_ring = aromatic_atom_count >= 6
```
Note: The project does NOT call `AddHs()` before cheminformatics operations (CLAUDE.md "HOSE codes: NO explicit hydrogens"). That rule applies to HOSE generation but is safe to follow here too — `CalcMolFormula` from SMILES without explicit H is the standard approach and matches how `nmrshiftdb.py` uses it.

#### RDKit CalcMolFormula (nmrshiftdb.py lines 9, 112)
```python
from rdkit.Chem import rdMolDescriptors

# ...
mol_formula = rdMolDescriptors.CalcMolFormula(mol)
```
For the new script, use this directly for formula comparison. A SMILES string parsed with `Chem.MolFromSmiles()` (implicit H, no `AddHs()`) gives the correct Hill-order formula (e.g. `C13H18O2`).

#### .smi file parsing pattern (test_lsd_regression.py lines 64-78)
The existing regression test shows the established convention for reading `.smi` files (one SMILES per line, take first whitespace-delimited field):
```python
for raw_line in smiles_path.read_text().splitlines():
    parts = raw_line.strip().split()
    if not parts:
        continue
    smiles = parts[0]
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        continue
```
Copy this verbatim for `merged.smi` parsing. The file format from `outlsd` + `lucy lsd rank` is confirmed: one SMILES per line, first field is the SMILES, remainder may be an index or name.

---

### `tests/test_verify_case_solution.py` (test, pure unit)

**Primary analog:** `tests/test_lsd_regression.py`
**Secondary analog:** `tests/test_cli_lsd.py` (tmp_path fixture + SystemExit assertion pattern)

#### Module-level imports pattern (test_lsd_regression.py lines 32-44)
```python
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from rdkit import Chem
from rdkit.Chem.inchi import MolToInchi  # type: ignore[import-untyped]

from lucy_ng.lsd.runner import LSDRunner

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "regression"
```
For the new test file:
```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from rdkit import Chem

SCRIPT = Path(__file__).parent.parent / "scripts" / "verify_case_solution.py"
```
Use a module-level `SCRIPT` constant pointing to the script under test — cleaner than computing the path inside each test.

#### tmp_path fixture + file writing (test_cli_lsd.py lines 25-31)
```python
def test_callable_with_smiles_file_and_shifts(self, tmp_path: Path) -> None:
    smiles_file = tmp_path / "solutions.smi"
    smiles_file.write_text("CCO\n")
```
Copy this pattern for each test: use `tmp_path / "merged.smi"`, write SMILES strings with `write_text()`.

#### Class-based test grouping (test_ranking.py lines 41+, test_lsd_regression.py lines 102+)
The whole test suite uses class-based grouping. The new test file should follow suit:
```python
class TestVerifyScript:
    """Tests for scripts/verify_case_solution.py."""

class TestVerifyScriptEdgeCases:
    """Edge case and error handling tests."""
```

#### pytest.mark.skipif for optional binary (test_lsd_regression.py lines 136-139)
```python
@pytest.mark.skipif(
    shutil.which("LSD") is None,
    reason="LSD binary not installed",
)
```
No skip needed for `verify_case_solution.py` (RDKit is always available in this project), but if any test needs an external dataset file it should use `@pytest.mark.skipif(not Path("...").exists(), reason="...")`.

#### SystemExit assertion (test_cli_lsd.py lines 56-66)
```python
with pytest.raises(SystemExit) as exc_info:
    _perform_ranking(...)
assert exc_info.value.code == 1
```
For subprocess-based tests, the equivalent is:
```python
result = subprocess.run([sys.executable, str(SCRIPT), str(smi_file), "C13H18O2"])
assert result.returncode == 1
```

#### Asserting JSON output
There is no exact existing analog for JSON-output assertion in tests, but the established approach from `test_cli_lsd.py` for json format tests is to parse stdout and assert structure:
```python
result = subprocess.run(
    [sys.executable, str(SCRIPT), str(smi_file), "C13H18O2"],
    capture_output=True, text=True,
)
data = json.loads(result.stdout)
assert data["pass"] is True
assert data["top_n_checked"] == 3
```

---

## Shared Patterns

### RDKit import style
**Source:** `src/lucy_ng/ranking/ranker.py` line 3 and `src/lucy_ng/dereplication/nmrshiftdb.py` lines 8-9
**Apply to:** `scripts/verify_case_solution.py`
```python
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
```
Two separate imports, not `import rdkit.Chem as Chem`. Consistent with all existing files.

### No explicit hydrogens
**Source:** CLAUDE.md "HOSE codes: NO explicit hydrogens"
**Apply to:** `scripts/verify_case_solution.py`
Do NOT call `Chem.AddHs(mol)` before `CalcMolFormula` or aromatic checks. `Chem.MolFromSmiles(s)` already gives correct formula with implicit H counted.

### `sys.exit(1)` for error paths
**Source:** `scripts/figshare_upload.py` lines 80, 87, 108; `scripts/zenodo_upload.py` lines 82, 103
**Apply to:** `scripts/verify_case_solution.py`
All error conditions (missing file, no SMILES, parse failure) exit with code 1. PASS exits with code 0. Consistent across all scripts.

### Path from `__file__` for fixture location
**Source:** `tests/test_lsd_regression.py` line 44: `FIXTURE_DIR = Path(__file__).parent / "fixtures" / "regression"`
**Apply to:** `tests/test_verify_case_solution.py`
```python
SCRIPT = Path(__file__).parent.parent / "scripts" / "verify_case_solution.py"
```

---

## No Analog Found

None — both files have close analogs in the codebase.

---

## Metadata

**Analog search scope:** `scripts/`, `tests/`, `src/lucy_ng/ranking/`, `src/lucy_ng/dereplication/`
**Files scanned:** 8 (figshare_upload.py, zenodo_upload.py, conftest.py, test_ranking.py, test_cli_lsd.py, test_lsd_regression.py, ranker.py, nmrshiftdb.py)
**Pattern extraction date:** 2026-06-01
