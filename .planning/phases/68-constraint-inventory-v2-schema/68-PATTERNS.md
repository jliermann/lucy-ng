# Phase 68: Constraint Inventory v2 Schema - Pattern Map

**Mapped:** 2026-05-19
**Files analyzed:** 7 new/modified files
**Analogs found:** 6 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `schemas/constraint_inventory_v2.json` | config | transform | `data/reference/` JSON files (HOSE table) | partial-match (same repo JSON artifact) |
| `src/lucy_ng/cli/lsd.py` | utility (add subcommand) | request-response | `lsd_run`, `lsd_rank` in same file | exact |
| `tests/test_inventory_schema.py` | test | transform | `tests/test_lsd_generator.py::TestPyLSDValidator` | exact |
| `~/.claude/agents/lucy-lsd-engineer.md` | config (agent skill) | — | existing Section 5 in same file (v1) | exact (in-place update) |
| `~/.claude/agents/lucy-devils-advocate.md` | config (agent skill) | — | existing Section 5 in same file (v1) | exact (in-place update) |
| `pyproject.toml` | config | — | existing `[project] dependencies` block | exact |
| `schemas/` directory | config | — | no analog (new top-level directory) | none |

---

## Pattern Assignments

### `src/lucy_ng/cli/lsd.py` — new `validate-inventory` subcommand (utility, request-response)

**Analog:** `lsd_run` command in the same file (`src/lucy_ng/cli/lsd.py` lines 41–110)

**Imports pattern** (lines 1–12 of `lsd.py`):
```python
import json
from pathlib import Path

import click

from lucy_ng.lsd import LSDRunner, LSDSolutionAnalyzer
from lucy_ng.lsd.parser import LSDOutputParser
from lucy_ng.processing import AdaptivePeakPicker
from lucy_ng.ranking import SolutionRanker
from lucy_ng.readers import BrukerReader
```
New subcommand adds `import jsonschema` at the top of the file alongside existing imports.

**Command registration pattern** (lines 41–68 of `lsd.py`):
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
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def lsd_run(
    input_file: str, timeout: int, output_dir: str | None, output_format: str
) -> None:
    """Run LSD on an input file.

    INPUT_FILE is the path to the LSD input file.
    """
```
Copy this decorator + signature shape exactly. For `validate-inventory`:
- Replace `"run"` with `"validate-inventory"`
- Replace `input_file` argument with `lsd_file`
- Keep `--format` / `output_format` pattern verbatim
- Drop `--timeout` and `--output-dir`

**Schema file path resolution pattern** (lines 112–138 of `lsd.py` — `_get_default_table_path()`):
```python
def _get_default_table_path() -> Path:
    """Get the default HOSE lookup table path."""
    import lucy_ng

    package_dir = Path(lucy_ng.__file__).parent

    # Check project data directory (development install)
    # package_dir = .../lucy-ng/src/lucy_ng -> project_root = .../lucy-ng
    project_root = package_dir.parent.parent
    project_table = project_root / "data" / "reference" / "hose_nmrshiftdb.json.gz"
    if project_table.exists():
        return project_table

    # Check package data (pip install)
    package_table = package_dir / "data" / "hose_nmrshiftdb.json.gz"
    if package_table.exists():
        return package_table
    ...
    raise FileNotFoundError(...)
```
Apply the same pattern for the schema file. The schema loader function must derive its path from `__file__`, not from `Path("schemas/...")` (which would break when invoked from a subdirectory like `analysis/iteration_NN/`). Follow the same two-tier try (project root → package data) approach:
```python
def _get_schema_path() -> Path:
    """Get the constraint inventory v2 JSON Schema path."""
    import lucy_ng
    package_dir = Path(lucy_ng.__file__).parent
    project_root = package_dir.parent.parent           # src/lucy_ng -> src -> repo root
    schema = project_root / "schemas" / "constraint_inventory_v2.json"
    if schema.exists():
        return schema
    raise FileNotFoundError(
        "Schema not found: schemas/constraint_inventory_v2.json. "
        "Ensure repo root is in Python path or schema is bundled with package."
    )
```

**`--format json` output pattern** (lines 89–97 of `lsd.py`):
```python
if output_format == "json":
    data = {
        "success": result.success,
        "solution_count": result.solution_count,
        "return_code": result.return_code,
        ...
    }
    click.echo(json.dumps(data, indent=2))
```
Replicate this dict-construction → `json.dumps(data, indent=2)` → `click.echo()` pattern for the validator. The JSON output contract is:
- Valid: `{"valid": true, "file": "<path>", "version": 2}`
- Invalid: `{"valid": false, "file": "<path>", "errors": [{"message": ..., "path": [...], "validator": ...}]}`
- v1 block detected: `{"valid": false, "file": "<path>", "errors": [{"message": "Legacy v1 inventory detected — upgrade to v2 format", "validator": "version"}]}`

**Error exit pattern** (lines 209–211 of `lsd.py`):
```python
click.echo("Error: Provide either --spectrum or --shifts, not both", err=True)
raise SystemExit(1)
```
Use `raise SystemExit(1)` (not `sys.exit(1)`) throughout, consistent with the file. Text errors to `err=True`. JSON errors to stdout with `exit 1`.

---

### `tests/test_inventory_schema.py` (test, transform)

**Analog:** `tests/test_lsd_generator.py::TestPyLSDValidator` (lines 500–537) and `TestPyLSDExtensions` (lines 389–497)

**File header pattern** (lines 1–9 of `test_lsd_generator.py`):
```python
"""Tests for LSD input file generator."""

import pytest
from pathlib import Path
import tempfile

from lucy_ng import BrukerReader, DEPTGuidedPicker, Peak1D, Peak2D, PeakList1D, PeakList2D
from lucy_ng.lsd.models import Hybridization, LSDAtom, LSDConstraint, LSDCorrelation, LSDProblem
from lucy_ng.lsd.generator import LSDInputGenerator
```
New test file header:
```python
"""Tests for constraint inventory v2 JSON schema and CLI validator."""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from lucy_ng.cli.lsd import lsd
```

**Class-per-feature test pattern** (lines 500–537 of `test_lsd_generator.py`):
```python
class TestPyLSDValidator:
    """Tests for validate_pylsd_input() consistency checker."""

    def test_validate_pylsd_carbon_mismatch(self):
        """Raises ValueError when FORM declares 13 carbons but MULT defines 12."""
        from lucy_ng.lsd.generator import validate_pylsd_input
        problem = LSDProblem(molecular_formula="C13H18O2")
        for i in range(1, 13):  # 12 carbons, formula says 13
            problem.add_atom(LSDAtom(i, "C", Hybridization.SP3, 0))
        with pytest.raises(ValueError, match="FORM/MULT mismatch"):
            validate_pylsd_input(problem)

    def test_validate_pylsd_carbon_match(self):
        """No error when FORM carbon count matches MULT carbon count."""
        ...
        validate_pylsd_input(problem)  # Should not raise
```
Structure the new test file with four classes:
- `TestSchemaLoading` — schema file loads, parses as valid JSON, has `$schema` field
- `TestSchemaValidation` — schema accepts correct v2 instance, rejects `version: 1`, rejects string-array `deferred_4j`, rejects missing required fields
- `TestValidateInventoryCLI` — CLI via `CliRunner`: valid file → exit 0, v1 block → exit 1 with legacy message, invalid JSON → exit 1
- `TestGateLogic` — G2 bare ELIM detection (grep pattern logic); each test 5–10 lines, one assertion per test

**CliRunner pattern** (used in `tests/test_lsd_runner.py` — import pattern):
```python
from click.testing import CliRunner

def test_valid_file_exits_0(self, tmp_path):
    runner = CliRunner()
    lsd_file = tmp_path / "compound.lsd"
    lsd_file.write_text("<LSD file content with v2 inventory block>")
    result = runner.invoke(lsd, ["validate-inventory", str(lsd_file)])
    assert result.exit_code == 0
```

---

### `schemas/constraint_inventory_v2.json` (config, transform)

**No close analog in codebase.** The schema is a new top-level artifact. Use RESEARCH.md Pattern 4 directly.

Key structural decisions (from RESEARCH.md lines 299–361):
- `"$schema": "https://json-schema.org/draft/2020-12/schema"`
- `"required"` array includes all 11 mandatory v2 fields: `version`, `iteration`, `formula`, `timestamp`, `mult_count`, `hsqc_count`, `hmbc_batches`, `hmbc_total`, `pylsd_mode`, `elim_annotated`, `deferred_4j`
- `"additionalProperties": true` at top level (forward compat)
- `"version": {"type": "integer", "const": 2}` — rejects v1 instances
- `deferred_4j` items use `"additionalProperties": false` for strict validation
- `deferred_4j` item `correlation_type`: `{"type": "string", "const": "HMBC"}`
- `deferred_4j` item `annotation`: `{"type": "string", "const": "; ELIM"}`

---

### `~/.claude/agents/lucy-lsd-engineer.md` — Section 5 update (agent skill)

**Analog:** The existing v1 Section 5 in the same file (lines 310–416)

Exact subsections requiring update (from RESEARCH.md lines 595–613):

| Subsection | Location | What changes |
|------------|----------|--------------|
| **5A schema table** | Lines 314–337 | Add 3 rows (`pylsd_mode`, `elim_annotated`, `deferred_4j` as object array); add schema file reference; change `version` constant from 1 to 2 |
| **5B file format** | Lines 338–379 | Replace `v1` delimiter with `v2`; replace `"version": 1` with `"version": 2`; replace string-array `deferred_4j` with object-array example; add `pylsd_mode` and `elim_annotated` fields to inline example |
| **5C init procedure** | Lines 381–396 | Step 2a: change "string descriptions" to object array with `atom1`/`atom2`/`shift1`/`shift2`; add `pylsd_mode`/`elim_annotated` initialization |
| **5D update procedure** | Lines 397–416 | Change `v1` to `v2` in delimiter string |
| **Workflow step 2a** | Upstream of section 5 | Change "string descriptions" to "structured objects per v2 schema" |

The v1 inline example to replace (lines 343–379 of `lucy-lsd-engineer.md`):
```
; === CONSTRAINT INVENTORY v1 ===
; {
;   "version": 1, ...
;   "deferred_4j": ["C4(129.4) H8(45.0)"],
; }
; === END CONSTRAINT INVENTORY ===
```

The v2 replacement (from RESEARCH.md lines 491–515):
```
; === CONSTRAINT INVENTORY v2 ===
; {
;   "version": 2, ...
;   "pylsd_mode": true,
;   "elim_annotated": true,
;   "deferred_4j": [
;     {"atom1": 4, "atom2": 8, "shift1": 129.38, "shift2": 45.03, "correlation_type": "HMBC", "annotation": "; ELIM"},
;     {"atom1": 6, "atom2": 9, "shift1": 127.26, "shift2": 44.90, "correlation_type": "HMBC", "annotation": "; ELIM"}
;   ],
; }
; === END CONSTRAINT INVENTORY ===
HMBC 4 8 2 4 ; ELIM
HMBC 6 9 2 4 ; ELIM
```

Add explicit callout in 5A:
> **UPGRADE NOTE:** `deferred_4j` changed from string array to object array in v2. The old format `["C4(129.4) H8(45.0)"]` will fail schema validation. Each entry must be a JSON object with `atom1`, `atom2`, `shift1`, `shift2`, `correlation_type`, `annotation`.

Add schema file reference in 5A intro:
> Source of Truth: `schemas/constraint_inventory_v2.json` (repo root). The table below is a summary; the schema file is authoritative.

---

### `~/.claude/agents/lucy-devils-advocate.md` — Section 5 update (agent skill)

**Analog:** Existing Section 5 in the same file (lines 217–296)

Exact subsections requiring update (from RESEARCH.md lines 604–616):

**5A Inventory Extraction** — replace bash pipeline (lines 222–233) with CLI call:

Current (lines 222–233 of `lucy-devils-advocate.md`):
```bash
grep "^; " analysis/iteration_NN/compound.lsd | \
  sed -n '/CONSTRAINT INVENTORY v1/,/END CONSTRAINT INVENTORY/p' | \
  sed 's/^; //' | grep -v "===" > /tmp/current_inv.json
```

Replacement per D-12:
```bash
RESULT=$(lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd)
VALID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['valid'])")
if [ "$VALID" != "True" ]; then
    ERRORS=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(e['message']) for e in d.get('errors',[])]")
    # BLOCK with error details
fi
```

Also add v1 detection/WARNING path in 5A:
```bash
# If validate-inventory returns legacy v1 message:
# {"valid": false, "errors": [{"message": "Legacy v1 inventory detected...", "validator": "version"}]}
# -> emit WARNING: "Legacy v1 inventory — using fallback validation"
# -> do NOT block the run, proceed with legacy grep-based checks
```

**5B — add G1/G2/G3 as Check 4** after existing Check 3 (lines 271–275):

```
**Check 4: pyLSD Mode Consistency** (CRITICAL/blocking — all three sub-checks)

G1: FORM/MULT consistency
- When `pylsd_mode=true` AND a `FORM C13H18O2` line exists in the file body (not comment):
  count_mult_c = grep -c "^MULT" | filter element=C
  If count_mult_c != carbon_count_from_formula -> BLOCK: "FORM/MULT mismatch: formula says N carbons, MULT defines M"

G2: No bare ELIM command in pylsd_mode
- When `pylsd_mode=true`:
  grep -n "^ELIM" analysis/iteration_NN/compound.lsd
  If any match found -> BLOCK: "Bare ELIM command detected in pylsd_mode. Use 'HMBC X Y 2 4 ; ELIM' instead. See STATE.md: ELIM drops correlations entirely — it does NOT extend bond ranges."
- NOTE: grep MUST be anchored to line start (^ELIM). Pattern HMBC 4 8 2 4 ; ELIM does NOT match ^ELIM.

G3: Annotation-vs-mode consistency
- If any HMBC line contains '; ELIM' trailing comment:
  Require ALL of: pylsd_mode=true AND elim_annotated=true AND len(deferred_4j) > 0
  Any condition false -> BLOCK: "HMBC lines carry '; ELIM' annotations but inventory is inconsistent: check pylsd_mode, elim_annotated, deferred_4j"
```

**Section 5 intro paragraph** — update delimiter references from `v1` to `v2`.

---

### `pyproject.toml` — add `jsonschema` dependency (config)

**Analog:** Existing `[project] dependencies` block (lines 26–34 of `pyproject.toml`)

Current block (lines 26–34):
```toml
dependencies = [
    "click>=8.0",
    "nmrglue>=0.9",
    "numpy>=1.24",
    "pydantic>=2.0",
    "rdkit>=2023.0",
    "scipy>=1.10",
    "tqdm>=4.0",
]
```

Add `"jsonschema>=4.18.0"` to this list (alphabetical order: between `click` and `nmrglue`):
```toml
dependencies = [
    "click>=8.0",
    "jsonschema>=4.18.0",
    "nmrglue>=0.9",
    ...
]
```

---

## Shared Patterns

### `--format json` CLI convention
**Source:** `src/lucy_ng/cli/lsd.py` lines 89–97 (`lsd_run`) and lines 279–307 (`lsd_rank`)
**Apply to:** `validate-inventory` subcommand
```python
if output_format == "json":
    data = { ... }
    click.echo(json.dumps(data, indent=2))
else:
    click.echo(...)   # human-readable text
```

### Error exit pattern
**Source:** `src/lucy_ng/cli/lsd.py` lines 70–73, 209–211
**Apply to:** `validate-inventory` subcommand
```python
click.echo("Error: ...", err=True)
raise SystemExit(1)
```
Never `sys.exit(1)` — always `raise SystemExit(1)`.

### Class-per-feature test structure
**Source:** `tests/test_lsd_generator.py` — `TestPyLSDExtensions` (line 389), `TestPyLSDValidator` (line 500); `tests/test_lsd_models.py` — `TestHybridization` (line 8), `TestLSDAtom` (line 18)
**Apply to:** `tests/test_inventory_schema.py`
- One class per logical feature group
- Docstring on class explains the feature under test
- Docstring on each method states the single invariant it verifies
- `# Should not raise` comment when testing the happy path (mirrored from line 519)

### Package-relative file resolution
**Source:** `src/lucy_ng/cli/lsd.py` lines 112–138 (`_get_default_table_path()`)
**Apply to:** schema file loader in `validate-inventory` implementation
Pattern: `Path(lucy_ng.__file__).parent.parent.parent / "schemas" / "constraint_inventory_v2.json"` resolves `src/lucy_ng -> src -> repo_root`.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `schemas/constraint_inventory_v2.json` | config | transform | No JSON Schema file exists in the repo yet; `schemas/` directory is entirely new. Use RESEARCH.md Pattern 4 (lines 299–361) as the template. |

---

## Metadata

**Analog search scope:** `src/lucy_ng/cli/`, `tests/`, `~/.claude/agents/`, `pyproject.toml`
**Files scanned:** `lsd.py` (464 lines, full read), `test_lsd_generator.py` (targeted lines 1–9, 389–537), `test_lsd_models.py` (lines 1–40), `lucy-lsd-engineer.md` (lines 290–416), `lucy-devils-advocate.md` (lines 210–296), `pyproject.toml` (lines 1–40)
**Pattern extraction date:** 2026-05-19
