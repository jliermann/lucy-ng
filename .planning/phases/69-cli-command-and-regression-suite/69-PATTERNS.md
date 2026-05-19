# Phase 69: CLI Command and Regression Suite - Pattern Map

**Mapped:** 2026-05-19
**Files analyzed:** 10 (7 new, 3 modified)
**Analogs found:** 9 / 10

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/lucy_ng/cli/pylsd.py` | CLI group + command | request-response | `src/lucy_ng/cli/lsd.py` (lsd group + `lsd_run`) | exact |
| `src/lucy_ng/cli/main.py` | config/wiring | request-response | `src/lucy_ng/cli/main.py` lines 12, 52 | exact (one-line addition) |
| `src/lucy_ng/cli/lsd.py` | refactor/helper extraction | request-response | `src/lucy_ng/cli/lsd.py` `lsd_rank` lines 341-537 | exact (self-refactor) |
| `tests/test_pylsd_cli.py` | test (CLI integration) | request-response | `tests/test_inventory_schema.py` `TestValidateInventoryCLI` | exact |
| `tests/test_lsd_form_tolerance.py` | test (LSD binary integration) | request-response | `tests/test_lsd_integration.py` lines 14-17 | exact |
| `tests/test_lsd_regression.py` | test (LSD binary regression) | request-response | `tests/test_lsd_integration.py` + `tests/test_lsd_orchestrator.py` | role-match |
| `tests/fixtures/regression/ibuprofen_no_4j.lsd` | fixture | file-I/O | `.planning/phases/65-hypothesis-gate/ibuprofen_no4j.lsd` | exact (copy) |
| `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt` | fixture/baseline | file-I/O | (no analog — developer-generated baseline) | none |
| `tests/fixtures/form_tolerance/minimal.lsd` + `minimal_with_form.lsd` | fixture pair | file-I/O | ethane fixture pattern from `test_lsd_integration.py` lines 19-26 | role-match |
| `.planning/findings/form-tolerance.md` | documentation/audit-trail | — | (no code analog — reproducible-research document) | none |

---

## Pattern Assignments

### `src/lucy_ng/cli/pylsd.py` (CLI group + command, request-response)

**Primary analog:** `src/lucy_ng/cli/lsd.py`

**Imports pattern** (lines 1-13):
```python
"""CLI commands for LSD structure elucidation."""

import json
from pathlib import Path

import click
import jsonschema

from lucy_ng.lsd import LSDRunner, LSDSolutionAnalyzer
from lucy_ng.lsd.parser import LSDOutputParser
from lucy_ng.processing import AdaptivePeakPicker
from lucy_ng.ranking import SolutionRanker
from lucy_ng.readers import BrukerReader
```

For `pylsd.py`, the import block replaces the unused imports with Phase 67/68 types:
```python
"""CLI commands for PyLSD multi-run orchestration."""

import json
import re
import tempfile
from pathlib import Path

import click

from lucy_ng.lsd.orchestrator import PyLSDOrchestrator, SolutionMerger
from lucy_ng.lsd.models import LSDCorrelation, LSDProblem
from lucy_ng.lsd.parser import LSDInputParser, LSDOutputParser
from lucy_ng.lsd import LSDRunner
from lucy_ng.cli.lsd import _validate_and_parse_inventory, _perform_ranking
```

**Click group definition pattern** (lsd.py lines 16-19):
```python
@click.group()
def lsd() -> None:
    """LSD structure elucidation."""
    pass
```

New group follows the identical structure:
```python
@click.group()
def pylsd() -> None:
    """PyLSD multi-run orchestration for 4J HMBC handling."""
    pass
```

**Click command decorator pattern** (lsd.py lines 42-64 — `lsd_run`):
```python
@lsd.command("run")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--timeout",
    type=int,
    default=60,
    help="Timeout in seconds.",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Directory for solution files.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def lsd_run(
    input_file: str, timeout: int, output_dir: str | None, output_format: str
) -> None:
```

New `pylsd run` follows the same decorator stacking, with additional flags:
```python
@pylsd.command("run")
@click.argument("lsd_file", type=click.Path(exists=True))
@click.option("--shifts", type=str, default=None, help="Comma-separated 13C shifts in ppm.")
@click.option("--no-rank", is_flag=True, default=False, help="Skip ranking; print output paths.")
@click.option("--working-dir", type=click.Path(), default=None, help="Directory for perm files.")
@click.option("--timeout", type=int, default=120, help="Per-permutation LSD timeout in seconds.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def pylsd_run(
    lsd_file: str, shifts: str | None, no_rank: bool,
    working_dir: str | None, timeout: int, output_format: str
) -> None:
```

**LSD availability guard pattern** (lsd.py lines 71-73):
```python
if not LSDRunner.is_available():
    click.echo("Error: LSD is not installed or not in PATH", err=True)
    raise SystemExit(1)
```

Copy verbatim as first statement in `pylsd_run`.

**`--shifts` required validation pattern** (lsd.py lines 407-413):
```python
if spectrum and shifts:
    click.echo("Error: Provide either --spectrum or --shifts, not both", err=True)
    raise SystemExit(1)

if not spectrum and not shifts:
    click.echo("Error: Provide --spectrum or --shifts", err=True)
    raise SystemExit(1)
```

For `pylsd_run`, the D-14b variant (shifts required only when ranking is active):
```python
if not no_rank and not shifts:
    click.echo("Error: --shifts is required unless --no-rank is specified.", err=True)
    raise SystemExit(1)
```

**Shifts parsing pattern** (lsd.py lines 417-423):
```python
try:
    experimental_shifts = [float(s.strip()) for s in shifts.split(",")]
except ValueError:
    click.echo("Error: Invalid shifts format. Use comma-separated numbers.", err=True)
    raise SystemExit(1)
```

Copy verbatim for `pylsd_run`.

**`--format json` output pattern** (lsd.py lines 479-507 — `lsd_rank`):
```python
if output_format == "json":
    data = {
        "total_solutions": result.total_solutions,
        "ranked_count": result.ranked_count,
        ...
        "solutions": [
            {
                "rank": i + 1,
                "smiles": sol.smiles,
                "mae": round(sol.mae, 3),
                ...
            }
            for i, sol in enumerate(result.solutions)
        ],
        "warnings": result.warnings,
    }
    click.echo(json.dumps(data, indent=2))
```

`pylsd_run --format json` wraps the ranking output in an outer dict (D-14c):
```python
if output_format == "json":
    data = {
        "permutations": len(orch_result.permutation_results),
        "merged_count": len(merge_result.merged_solutions),
        "ranked_solutions": [...],   # same structure as lsd_rank solutions[]
        "run_report_path": str(merge_result.run_report),
    }
    click.echo(json.dumps(data, indent=2))
```

**`raise SystemExit(1)` convention** — used throughout `lsd.py` (lines 39, 73, 238, 257, 275, 294, 303, 338, 409, 411, 422, 435, 453, 464, 474). Never use `sys.exit(1)`.

---

### `src/lucy_ng/cli/main.py` (config/wiring — one-line change)

**Analog:** `src/lucy_ng/cli/main.py` lines 12 and 52

**Current import pattern** (line 12):
```python
from lucy_ng.cli.lsd import lsd
```

**Add after line 12:**
```python
from lucy_ng.cli.pylsd import pylsd
```

**Current registration pattern** (line 52):
```python
cli.add_command(lsd)
```

**Add after line 52:**
```python
cli.add_command(pylsd)
```

No other changes to `main.py`. The docstring in `cli()` (lines 28-41) can optionally be extended with a `pylsd` entry, but is left to planner discretion.

---

### `src/lucy_ng/cli/lsd.py` — `_perform_ranking()` helper extraction

**Analog:** `lsd_rank` Click command body, lines 406-537

The refactor extracts the ranking body (lines 441-537) into a module-level helper, leaving `lsd_rank` as a thin arg-parsing wrapper. The extracted function signature:

```python
def _perform_ranking(
    smiles_file: str | Path,
    experimental_shifts: list[float],
    top: int = 10,
    tolerance: float = 3.0,
    table: str | Path | None = None,
    output_format: str = "text",
) -> dict | None:
    """Core ranking logic, callable from lsd_rank and pylsd_run.

    Returns the data dict when output_format=='json' (for callers to embed),
    or None when output_format=='text' (output already echoed).
    """
    # Load solutions
    try:
        solutions = LSDOutputParser.parse_smiles_file(smiles_file)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    ...
    # identical to lsd_rank body from line 441 onwards
```

The caller pattern in `lsd_rank` becomes:
```python
def lsd_rank(...) -> None:
    # [shift parsing and validation — lines 407-439, unchanged]
    _perform_ranking(smiles_file, experimental_shifts, top, tolerance, table, output_format)
```

**Important:** `_perform_ranking` is a module-private helper (single underscore prefix), consistent with the existing `_get_default_table_path`, `_get_schema_path`, and `_extract_inventory_block` helpers in the same file (lines 113, 142, 174).

---

### `tests/test_pylsd_cli.py` (test, CLI integration, request-response)

**Primary analog:** `tests/test_inventory_schema.py` class `TestValidateInventoryCLI` (lines 499-703)

**Imports pattern** (test_inventory_schema.py lines 1-11):
```python
"""Tests for constraint inventory v2 JSON schema."""

import json
import re
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from jsonschema import Draft202012Validator

from lucy_ng.cli.lsd import lsd
```

For `test_pylsd_cli.py`:
```python
"""CLI integration tests for lucy pylsd run."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from click.testing import CliRunner

from lucy_ng.cli.pylsd import pylsd
from lucy_ng.lsd.orchestrator import MergeResult, MergedSolution, OrchestrationResult, PermutationResult
```

**CliRunner invocation pattern** (test_inventory_schema.py lines 505-508):
```python
lsd_file = tmp_path / "compound.lsd"
lsd_file.write_text(_make_v2_lsd_content(_minimal_v2_inventory_json()))
runner = CliRunner()
result = runner.invoke(lsd, ["validate-inventory", str(lsd_file)], catch_exceptions=False)
assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}. Output: {result.output}"
```

For `test_pylsd_cli.py`, patch the orchestrator to avoid needing a real LSD binary:
```python
def test_run_no_rank_calls_orchestrator(self, tmp_path):
    lsd_file = tmp_path / "compound.lsd"
    lsd_file.write_text("; minimal\nEXIT\n")
    mock_orch_result = MagicMock(spec=OrchestrationResult)
    mock_orch_result.permutation_results = []
    mock_merge_result = MagicMock(spec=MergeResult)
    mock_merge_result.merged_solutions = []
    mock_merge_result.merged_smi = tmp_path / "merged.smi"
    mock_merge_result.run_report = tmp_path / "run_report.json"
    with patch("lucy_ng.cli.pylsd.PyLSDOrchestrator") as MockOrch, \
         patch("lucy_ng.cli.pylsd.SolutionMerger") as MockMerger:
        MockOrch.return_value.run.return_value = mock_orch_result
        MockMerger.return_value.merge.return_value = mock_merge_result
        runner = CliRunner()
        result = runner.invoke(pylsd, ["run", str(lsd_file), "--no-rank"])
    assert result.exit_code == 0
```

**JSON output assertion pattern** (test_inventory_schema.py lines 515-518):
```python
result = runner.invoke(lsd, ["validate-inventory", str(lsd_file), "--format", "json"], catch_exceptions=False)
assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}. Output: {result.output}"
data = json.loads(result.output)
assert data["valid"] is True, f"Expected valid=true, got: {data}"
```

**`patch` for PermissionError testing pattern** (test_inventory_schema.py lines 681-690):
```python
with patch("lucy_ng.cli.lsd.Path.read_text", side_effect=PermissionError("Permission denied: compound.lsd")):
    result = runner.invoke(
        lsd, ["validate-inventory", str(lsd_file), "--format", "json"],
        catch_exceptions=False
    )
assert result.exit_code == 1
data = json.loads(result.output)
assert data["valid"] is False
```

**Test class naming convention** — use the class-per-concern pattern from `test_inventory_schema.py`:
- `TestPylsdRunCLI` — basic invocations (no-rank, with-rank, missing-shifts)
- `TestSuspectExtraction` — D-13 inventory/grep fallback logic (unit tests without real LSD)
- `TestRankingIntegration` — `_perform_ranking()` helper called from `pylsd_run`

---

### `tests/test_lsd_form_tolerance.py` (test, LSD binary integration)

**Primary analog:** `tests/test_lsd_integration.py` lines 1-17 (class `TestLSDEndToEnd`)

**Imports pattern** (test_lsd_integration.py lines 1-8):
```python
"""End-to-end integration tests for LSD structure elucidation."""

import pytest
from pathlib import Path
import tempfile

from lucy_ng.lsd import LSDInputGenerator, LSDRunner, LSDProblem
from lucy_ng.lsd.models import Hybridization, LSDAtom, LSDCorrelation
```

For `test_lsd_form_tolerance.py`, uses `shutil.which` per D-15 (not `LSDRunner.is_available()`):
```python
"""Empirical FORM-tolerance test for LSD binary.

Verifies that LSD silently ignores an unknown FORM command and produces
the same solution set as a file without it. Living regression: if a future
LSD version changes this behaviour, this test will fail and alert the developer.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from lucy_ng.lsd.runner import LSDRunner
from lucy_ng.lsd.parser import LSDOutputParser
```

**`@pytest.mark.skipif` pattern** (test_lsd_integration.py lines 14-17):
```python
@pytest.mark.skipif(
    not LSDRunner.is_available(),
    reason="LSD not installed"
)
def test_simple_ethane_elucidation(self):
```

Per D-15, use the `shutil.which` form with uppercase `"LSD"`:
```python
@pytest.mark.skipif(
    shutil.which("LSD") is None,
    reason="LSD binary not installed"
)
def test_form_line_produces_same_solutions(tmp_path):
```

**LSD invocation pattern** (test_lsd_integration.py lines 33-37):
```python
runner = LSDRunner()
result = runner.run(problem, timeout=30)
assert result.success
assert result.solution_count == 1
```

For the FORM tolerance test, use `runner.run_file()` on the fixture files directly:
```python
runner = LSDRunner()
result_without = runner.run_file(minimal_lsd, output_dir=tmp_path / "without", timeout=30)
result_with = runner.run_file(minimal_with_form_lsd, output_dir=tmp_path / "with", timeout=30)
assert result_without.success
assert result_with.success
assert result_without.solution_count == result_with.solution_count
```

---

### `tests/test_lsd_regression.py` (test, LSD binary regression)

**Primary analog:** `tests/test_lsd_integration.py` for skipif pattern; `tests/test_lsd_orchestrator.py` for InChI handling

**Imports pattern:**
```python
"""Regression test: lucy lsd run on ibuprofen_no_4j.lsd must produce stable InChI set.

Baseline: tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt
Generated: manually from LSD-3.4.9 run, chemically verified.

If this test fails after a LSD version update, analyse the new solution set,
confirm chemical validity, and regenerate the baseline manually.
"""

import shutil
from pathlib import Path

import pytest
from rdkit import Chem
from rdkit.Chem.inchi import MolToInchi

from lucy_ng.lsd.runner import LSDRunner
from lucy_ng.lsd.parser import LSDOutputParser
```

**skipif pattern** (same `shutil.which("LSD")` form per D-16):
```python
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "regression"

@pytest.mark.skipif(
    shutil.which("LSD") is None,
    reason="LSD binary not installed"
)
def test_ibuprofen_no_4j_inchi_set_stable(tmp_path):
    """InChI set from lucy lsd run on ibuprofen_no_4j.lsd must match baseline."""
    lsd_fixture = FIXTURE_DIR / "ibuprofen_no_4j.lsd"
    baseline_file = FIXTURE_DIR / "ibuprofen_no_4j.expected_inchis.txt"
    ...
```

**InChI generation pattern** from `src/lucy_ng/lsd/orchestrator.py` lines 408-428:
```python
from rdkit import Chem
from rdkit.Chem.inchi import InchiToInchiKey, MolToInchi

mol = Chem.MolFromSmiles(smiles)
if mol is None:
    return None
inchi = MolToInchi(mol)
if inchi is None:
    return None
return InchiToInchiKey(inchi)
```

For the regression test, use `MolToInchi` directly (full InChI, not key — human-readable in baseline file):
```python
def _smiles_file_to_inchis(smiles_file: Path) -> set[str]:
    """Convert SMILES file to a set of InChI strings, skipping invalid SMILES."""
    inchis = set()
    for smiles in smiles_file.read_text().splitlines():
        smiles = smiles.strip()
        if not smiles:
            continue
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        inchi = MolToInchi(mol)
        if inchi:
            inchis.add(inchi)
    return inchis
```

**Set comparison pattern** (order-independent per D-16):
```python
baseline_inchis = set(baseline_file.read_text().splitlines())
baseline_inchis.discard("")  # strip blank lines
assert actual_inchis == baseline_inchis, (
    f"InChI set changed. "
    f"Added: {actual_inchis - baseline_inchis}. "
    f"Removed: {baseline_inchis - actual_inchis}."
)
```

---

### `tests/fixtures/regression/ibuprofen_no_4j.lsd` (fixture, file-I/O)

**Source:** Copy from `.planning/phases/65-hypothesis-gate/ibuprofen_no4j.lsd` (the file used in the Phase 65 hypothesis gate run that produced 392 solutions). No modifications — this is the "classic `lucy lsd run`" form: no v2 inventory block, no `; ELIM` annotations, standard HMBC constraints.

Destination path: `tests/fixtures/regression/ibuprofen_no_4j.lsd`

---

### `tests/fixtures/form_tolerance/minimal.lsd` + `minimal_with_form.lsd` (fixture pair, file-I/O)

**Pattern from:** `tests/test_lsd_integration.py` ethane problem definition (lines 19-26):
```python
problem = LSDProblem(name="ethane", molecular_formula="C2H6")
problem.add_atom(LSDAtom(1, "C", Hybridization.SP3, 3))  # CH3
problem.add_atom(LSDAtom(2, "C", Hybridization.SP3, 3))  # CH3
problem.add_correlation(LSDCorrelation(1, 1, "HSQC"))
problem.add_correlation(LSDCorrelation(2, 2, "HSQC"))
```

`minimal.lsd` (ethane, no FORM line):
```
; Minimal LSD test: ethane C2H6
MULT 1 C 3 3
MULT 2 C 3 3
HSQC 1 1
HSQC 2 2
EXIT
```

`minimal_with_form.lsd` (identical + FORM line to test tolerance):
```
; Minimal LSD test: ethane C2H6 — with FORM line
FORM C2H6
MULT 1 C 3 3
MULT 2 C 3 3
HSQC 1 1
HSQC 2 2
EXIT
```

Both files must produce exactly 1 solution (ethane: single C-C bond). The FORM line is expected to be silently ignored by LSD-3.4.9.

---

## Shared Patterns

### `raise SystemExit(1)` (not `sys.exit`)

**Source:** `src/lucy_ng/cli/lsd.py` — used at lines 39, 73, 238, 257, 275, 294, 303, 338, 409, 411, 422, 435, 453, 464, 474
**Apply to:** All error paths in `pylsd.py`

```python
# CORRECT (project convention since Phase 68):
raise SystemExit(1)

# WRONG — never use in this project:
sys.exit(1)
```

### `click.echo(..., err=True)` for errors

**Source:** `src/lucy_ng/cli/lsd.py` lines 31, 72, 302, 409, 411, etc.
**Apply to:** All `click.echo` calls that report errors in `pylsd.py`

```python
click.echo("Error: ...", err=True)   # goes to stderr — correct for error messages
click.echo("...")                    # goes to stdout — correct for normal output
```

### `--format` option naming and type

**Source:** `src/lucy_ng/cli/lsd.py` lines 57-63:
```python
@click.option(
    "--format",
    "output_format",       # rename to avoid shadowing Python builtins
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
```

The parameter name alias `"output_format"` is mandatory — do not use `format` as a parameter name.

### `_get_default_table_path()` resolution helper

**Source:** `src/lucy_ng/cli/lsd.py` lines 113-139
**Apply to:** `_perform_ranking()` helper (extracted from `lsd_rank`) — reuse this function when resolving the HOSE table path. Import or call it from the same `lsd.py` module.

### `@pytest.mark.skipif(shutil.which("LSD") is None, reason="LSD binary not installed")`

**Source:** `tests/test_lsd_integration.py` lines 14-16 (uses `LSDRunner.is_available()` variant); D-15 mandates the `shutil.which("LSD")` form for Phase 69 tests.
**Apply to:** Every test in `test_lsd_form_tolerance.py` and `test_lsd_regression.py`

Note: `shutil.which("LSD")` uses uppercase `"LSD"` — the binary on this machine is uppercase. See RESEARCH.md Pitfall 3.

### CliRunner with `catch_exceptions=False` for positive-path tests

**Source:** `tests/test_inventory_schema.py` lines 507, 515, 580, 619
**Apply to:** `tests/test_pylsd_cli.py` — use `catch_exceptions=False` on tests expecting exit 0 so unexpected exceptions surface clearly; omit it on tests that expect exit 1 (allow the exception to be translated to exit code).

```python
result = runner.invoke(pylsd, ["run", str(lsd_file), "--no-rank"], catch_exceptions=False)
```

### Module-private helper naming (`_function_name`)

**Source:** `src/lucy_ng/cli/lsd.py` — `_get_default_table_path` (line 113), `_get_schema_path` (line 142), `_extract_inventory_block` (line 174)
**Apply to:** All new helpers in `lsd.py` (`_perform_ranking`, `_validate_and_parse_inventory`) and in `pylsd.py` (`_extract_suspects_from_file`)

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt` | baseline fixture | file-I/O | Developer-generated file; must be produced by running the current `lucy lsd run` on the ibuprofen fixture and manually verifying solutions. A sol file from Phase 65 (`65-hypothesis-gate/ibuprofen_no4j.sol`, 392 solutions) exists and can be used to generate the baseline without re-running LSD. |
| `.planning/findings/form-tolerance.md` | audit-trail document | — | Reproducible-research document; no code analog. Structure from CONTEXT.md specifics: Hypothesis → Setup → Methode → Output → Conclusion → Reproducibility-Notes. |

---

## Metadata

**Analog search scope:** `src/lucy_ng/cli/`, `tests/`, `src/lucy_ng/lsd/orchestrator.py`
**Files read directly:** `src/lucy_ng/cli/lsd.py` (664 lines), `src/lucy_ng/cli/main.py` (57 lines), `tests/test_inventory_schema.py` (748 lines), `tests/test_lsd_integration.py` (60 lines, partial), `tests/test_lsd_orchestrator.py` (80 lines, partial), `src/lucy_ng/cli/detect.py` (50 lines, partial — confirmed group pattern), `src/lucy_ng/lsd/orchestrator.py` (230 lines, two reads)
**Pattern extraction date:** 2026-05-19
