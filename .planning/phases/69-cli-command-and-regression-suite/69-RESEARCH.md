# Phase 69: CLI Command and Regression Suite — Research

**Researched:** 2026-05-19
**Domain:** Click CLI wiring, PyLSDOrchestrator integration, pytest LSD-skipif patterns, regression baseline strategy
**Confidence:** HIGH — all findings sourced directly from existing codebase files

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-13:** `lucy pylsd run` liest Suspect-Korrelationen primär aus dem v2 Constraint-Inventory-Block via `lucy lsd validate-inventory --format json` (nutzt das CR-02 Fix `inventory: {...}` Feld). Aus `inventory.deferred_4j` werden `(atom1, atom2)`-Paare extrahiert und an PyLSDOrchestrator übergeben.
- **D-13a:** Wenn `; ELIM`-Annotationen auf HMBC-Zeilen existieren, müssen sie mit dem Inventory übereinstimmen. Mismatch → exit 1.
- **D-13b:** Kein Inventory-Block → Fallback auf `grep "^HMBC.*; ELIM"`. Warnung ausgeben.
- **D-13c:** Weder Inventory noch Annotationen → Single-Run (0 Permutationen), Warnung ausgeben.
- **D-14:** Default-Pipeline: orchestrate → merge → rank → stdout. `--no-rank` Escape-Hatch. `--shifts` required wenn Ranking aktiv. `--format json` Output.
- **D-15:** Zwei Artefakte: `.planning/findings/form-tolerance.md` (Audit-Trail) + `tests/test_lsd_form_tolerance.py` mit `@pytest.mark.skipif(shutil.which('LSD') is None, ...)`.
- **D-16:** `tests/test_lsd_regression.py` mit InChI-Set-Vergleich gegen `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt`. Baseline manuell erzeugt und verifiziert.

### Claude's Discretion

- Exakte CLI-Flag-Namen (Vorschläge: `--shifts`, `--no-rank`, `--working-dir`, `--max-defer`)
- Output-File-Naming und Default-Working-Directory
- JSON-Schema-Struktur für `--format json`-Output
- Wortlaut der Warnings (D-13b, D-13c)
- Python-Function-Aufruf (kein subprocess) für `lucy lsd rank`-Integration

### Deferred Ideas (OUT OF SCOPE)

- Parallelisierung der LSD-Läufe
- Resume-on-failure
- `lucy pylsd run --dry-run`
- CI mit LSD-Binary in Docker

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CLI-01 | `lucy pylsd run <file>` command executes multi-run orchestration and returns merged solutions | PyLSDOrchestrator.run() + SolutionMerger.merge() API fully documented below; Click subgroup registration pattern confirmed |
| CLI-02 | `lucy pylsd run` reuses existing `lucy lsd rank` for two-tier ranking (match count primary, MAE secondary) | `lsd_rank` Click function confirmed; ranking logic is inside `lsd_rank()` using `SolutionRanker` — refactoring approach to expose internals documented below |
| CLI-03 | Regression: all existing `lucy lsd run` commands work unchanged | New `pylsd` group is separate from `lsd` group; no shared code mutations; regression test strategy documented |

</phase_requirements>

---

## Summary

Phase 69 is a plumbing phase: wire the already-built PyLSDOrchestrator and SolutionMerger (Phase 67) into a new `lucy pylsd run` Click command, add a separate `pylsd` Click group registered in `main.py`, integrate the existing `lsd_rank` logic for post-merge ranking, and write three test files (CLI integration, FORM tolerance, regression). No new dependencies are needed. The only novel complexity is the suspect-correlation extraction logic (D-13: inventory → grep fallback → single-run fallback) and the CR-02 status — the `inventory` key is already present in the success JSON (confirmed in source at `cli/lsd.py:314`).

The LSD binary is available at `/usr/local/bin/lsd` (or wherever it lives in PATH) and reports its version as `LSD-3.4.9` on stderr when invoked without valid arguments. The binary's version output is parsable via `LSD 2>&1 | head -1`.

**Primary recommendation:** New code lives in `src/lucy_ng/cli/pylsd.py` (new file), registered in `main.py` via `cli.add_command(pylsd)`. The `lsd_rank` Click command's internal ranking logic must be extracted to a helper function so both `lsd_rank` and `pylsd_run` can call it without subprocess overhead.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Suspect-correlation extraction | CLI layer (`pylsd.py`) | `lsd_validate_inventory` (reused via direct Python call) | CLI owns the policy (D-13/D-13b/D-13c branching logic); validation tool owns JSON parsing |
| Permutation generation + LSD execution | `PyLSDOrchestrator` (lsd/) | — | Already built, tested, CLI is thin wrapper |
| Solution deduplication + provenance | `SolutionMerger` (lsd/) | — | Already built, tested |
| Two-tier ranking | `SolutionRanker` (ranking/) | Helper function extracted from `lsd_rank` | CLI command owns I/O; ranking logic belongs in reusable helper |
| FORM-tolerance verification | Test + findings doc | LSD binary (external) | Empirical confirmation — requires real LSD invocation |
| Regression baseline | Test fixture | Developer (one-time manual verification) | Baseline file must be created and committed by developer, not auto-generated |

---

## Standard Stack

### Core (all already in pyproject.toml)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `click` | >=8.0 [VERIFIED: pyproject.toml] | Click group + command registration | Existing project standard |
| `rdkit` | >=2023.0 [VERIFIED: pyproject.toml] | InChI generation for regression tests | Already used in SolutionMerger |
| `pytest` | >=7.0 [VERIFIED: pyproject.toml] | Test runner for all 3 new test files | Existing project standard |
| `jsonschema` | >=4.18.0 [VERIFIED: pyproject.toml] | Already used by validate-inventory; no new dep | Already installed |

**No new dependencies required.** [VERIFIED: pyproject.toml — all required packages already listed]

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `shutil` (stdlib) | stdlib | `shutil.which('LSD')` in skipif decorators | All three new test files use this pattern |
| `subprocess` (stdlib) | stdlib | NOT used for rank integration (use Python call instead per D-14) | Used only in orchestrator for LSD/outlsd binary invocation |

---

## Package Legitimacy Audit

No new packages introduced in this phase. All dependencies are existing project dependencies already installed and verified across prior phases. Audit skipped per "no new packages" condition.

---

## Architecture Patterns

### System Architecture Diagram

```
  Agent / User
      |
      v
  lucy pylsd run <file.lsd> --shifts "..."
      |
      |--[1] Extract suspects: lsd_validate_inventory(file) → inventory.deferred_4j
      |        └─ fallback: grep "^HMBC.*; ELIM" → extract atom pairs
      |        └─ fallback: empty → single run
      |
      |--[2] PyLSDOrchestrator(lsd_path=None, timeout=120)
      |        .run(base_problem, suspect_correlations, output_dir)
      |        → generates perm_00/ perm_01/ ... perm_N/
      |        → each has <name>.lsd + solutions.smi (via outlsd)
      |        → returns OrchestrationResult
      |
      |--[3] SolutionMerger()
      |        .merge(orchestration_result.permutation_results, output_dir)
      |        → merged.smi + run_report.json
      |        → returns MergeResult
      |
      |--[4] if --no-rank: print paths to merged.smi + run_report.json → exit
      |
      |--[5] _rank_smiles_file(merged_smi, shifts, top, tolerance, table)
      |        (extracted helper, also used by lsd_rank Click command)
      |        → RankResult
      |
      v
  stdout: ranked solutions (text or --format json)
```

### Recommended Project Structure (new files only)

```
src/lucy_ng/cli/
├── pylsd.py             # new: pylsd Click group + pylsd_run command
├── lsd.py               # modified: extract _rank_smiles_file() helper; add import
└── main.py              # modified: add `from lucy_ng.cli.pylsd import pylsd` + cli.add_command(pylsd)

tests/
├── test_pylsd_cli.py              # new: CliRunner tests for lucy pylsd run (mocked orchestrator)
├── test_lsd_form_tolerance.py     # new: FORM-tolerance @skipif(LSD missing)
├── test_lsd_regression.py         # new: InChI-set regression @skipif(LSD missing)
└── fixtures/
    └── regression/
        ├── ibuprofen_no_4j.lsd          # new: copy of Phase 65 fixture, no inventory block
        └── ibuprofen_no_4j.expected_inchis.txt  # new: Wave 0 baseline (developer generates)

.planning/findings/
└── form-tolerance.md              # new: reproducible-research audit trail
```

### Pattern 1: Click Subgroup Registration (main.py)

Current pattern at `src/lucy_ng/cli/main.py` lines 12 and 52:

```python
# Source: src/lucy_ng/cli/main.py (VERIFIED: read directly)
from lucy_ng.cli.lsd import lsd  # line 12
# ...
cli.add_command(lsd)              # line 52
```

New `pylsd` group follows the identical pattern:
```python
# Add to imports section (after lsd import):
from lucy_ng.cli.pylsd import pylsd
# Add to add_command section:
cli.add_command(pylsd)
```

### Pattern 2: Click Group Definition (pylsd.py)

Mirrors the `lsd` group in `src/lucy_ng/cli/lsd.py` lines 16-19:

```python
# Source: src/lucy_ng/cli/lsd.py lines 16-19 (VERIFIED)
@click.group()
def lsd() -> None:
    """LSD structure elucidation."""
    pass
```

New file:
```python
@click.group()
def pylsd() -> None:
    """PyLSD multi-run orchestration for 4J HMBC handling."""
    pass

@pylsd.command("run")
@click.argument("lsd_file", type=click.Path(exists=True))
@click.option("--shifts", type=str, default=None, help="Comma-separated 13C shifts in ppm.")
@click.option("--no-rank", is_flag=True, default=False, help="Skip ranking; output merged.smi path.")
@click.option("--working-dir", type=click.Path(), default=None, help="Directory for permutation files.")
@click.option("--timeout", type=int, default=120, help="Per-permutation LSD timeout in seconds.")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
def pylsd_run(lsd_file, shifts, no_rank, working_dir, timeout, output_format):
    ...
```

### Pattern 3: `@pytest.mark.skipif` for LSD-dependent tests

Existing pattern from `src/lucy_ng/tests/test_lsd_integration.py` lines 14-16 [VERIFIED]:

```python
# Source: tests/test_lsd_integration.py lines 14-16 (VERIFIED)
@pytest.mark.skipif(
    not LSDRunner.is_available(),
    reason="LSD not installed"
)
def test_simple_ethane_elucidation(self):
```

Alternative form using `shutil.which` (per D-15 wording):
```python
import shutil
import pytest

@pytest.mark.skipif(
    shutil.which("LSD") is None,
    reason="LSD binary not installed"
)
```

Both patterns work identically. `LSDRunner.is_available()` internally calls `shutil.which("lsd")` plus SEARCH_PATHS fallback (runner.py line 293-303). For the three new test files, D-15 specifies `shutil.which('LSD') is None` form — use that verbatim for consistency with the decision text. Note the case sensitivity: `shutil.which` is case-sensitive on Linux/macOS; the existing runner uses lowercase `"lsd"` (runner.py line 294). Check which works on the developer machine. Since `which LSD` succeeds (returns `/Users/steinbeck/Dropbox/develop/LSD/LSD`), use `shutil.which("LSD")` as specified in D-15.

### Pattern 4: CliRunner Test Pattern (from test_inventory_schema.py)

```python
# Source: tests/test_inventory_schema.py (VERIFIED)
from click.testing import CliRunner
from lucy_ng.cli.lsd import lsd

class TestValidateInventoryCLI:
    def test_valid_file_json_output(self, tmp_path):
        lsd_file = tmp_path / "test.lsd"
        lsd_file.write_text(...)
        runner = CliRunner()
        result = runner.invoke(lsd, ["validate-inventory", str(lsd_file), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["valid"] is True
```

For `test_pylsd_cli.py`, import from the new module:
```python
from lucy_ng.cli.pylsd import pylsd
# then: runner.invoke(pylsd, ["run", str(lsd_file), "--shifts", "180.5,140.8", ...])
```

### Pattern 5: InChI Generation (for regression tests)

Existing pattern in `SolutionMerger._smiles_to_inchi_key()` at `orchestrator.py` lines 408-428 [VERIFIED]:

```python
# Source: src/lucy_ng/lsd/orchestrator.py lines 408-428 (VERIFIED)
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

For regression tests, the test needs the full InChI string (not key), for human readability in the baseline file. Use `MolToInchi(mol)` directly. Sorted, one per line:

```python
def smiles_to_inchi(smiles: str) -> str | None:
    from rdkit import Chem
    from rdkit.Chem.inchi import MolToInchi
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return MolToInchi(mol)
```

### Anti-Patterns to Avoid

- **Subprocess call to `lucy lsd rank`:** D-14 explicitly mandates Python-function call, not subprocess. The `lsd_rank` Click function body currently has no extracted helper — refactoring is required.
- **Modifying `lsd_run` or `lsd_rank`:** The regression guarantee (CLI-03) requires zero modification to existing `lsd` subcommands. Extract helpers, don't change callsites.
- **Hardcoded working directory:** `PyLSDOrchestrator.run()` takes an `output_dir: Path` parameter. CLI should default to a tempdir (or `dirname(input_file) / "pylsd_run"`) — never the current working directory, which may be the agent's iteration folder.
- **Using `sys.exit()` instead of `raise SystemExit(1)`:** Project convention enforced since Phase 68 (see 68-CONTEXT.md "raise SystemExit(1) statt sys.exit(1)").

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| InChI-based deduplication | Custom SMILES comparison | `SolutionMerger.merge()` | Already implemented, tested (20 tests), handles invalid SMILES gracefully |
| Permutation file generation | Manual file writing | `PyLSDOrchestrator.run()` | Already handles K-cap, deepcopy, outlsd bypass bug |
| JSON schema validation | Manual key checking | `lsd_validate_inventory` Python call (D-13) | Schema already defined, CLI already wired |
| SMILES ranking | Custom sort | `SolutionRanker.rank()` via extracted helper | Two-tier sort (match count + MAE) already implemented and tested |
| LSD binary detection | Custom PATH search | `LSDRunner.is_available()` or `shutil.which("LSD")` | Already has SEARCH_PATHS fallback |

**Key insight:** This phase is almost entirely wiring. The only new logic is: (a) the D-13 suspect extraction branching, (b) the refactored `_rank_smiles_file()` helper, and (c) the `--format json` output schema for `pylsd run`.

---

## Suspect Correlation Extraction: Detailed Design (D-13)

The most complex new logic in this phase. Step-by-step:

**Step 1: Attempt inventory extraction (primary)**

Call the `lsd_validate_inventory` logic directly as a Python function (not subprocess) — or invoke it via `CliRunner` if direct call is easier. The success JSON shape is (confirmed at `cli/lsd.py:309-315` [VERIFIED]):

```json
{
  "valid": true,
  "file": "/path/to/compound.lsd",
  "version": 2,
  "inventory": {
    "version": 2,
    "iteration": 1,
    "formula": "C13H18O2",
    "pylsd_mode": true,
    "elim_annotated": true,
    "deferred_4j": [
      {
        "atom1": 4,
        "atom2": 8,
        "shift1": 129.38,
        "shift2": 45.03,
        "correlation_type": "HMBC",
        "annotation": "; ELIM"
      }
    ],
    ...
  }
}
```

Extract suspects from `result["inventory"]["deferred_4j"]`: each item's `atom1` and `atom2` give the `LSDCorrelation` identity tuple `(atom1, atom2, "HMBC")`.

**Step 2: Cross-check against `; ELIM` annotations (D-13a)**

Parse the LSD file for lines matching `^HMBC\s+(\d+)\s+(\d+).*;\s*ELIM`. Extract `(atom1, atom2)` pairs. Compare sets. If mismatch → `click.echo("Error: ...", err=True); raise SystemExit(1)`.

**Step 3: Fallback if no inventory block (D-13b)**

`lsd_validate_inventory` returns `{"valid": false, "errors": [{"validator": "block_presence", ...}]}`. In this case, grep the LSD file directly for `; ELIM` annotations. Emit warning: `"Warning: No inventory block found — using ; ELIM annotation fallback (recommended: write inventory block)"`.

**Step 4: Both empty (D-13c)**

If `deferred_4j` is empty (or absent) AND no `; ELIM` annotations: emit warning `"Warning: No suspect correlations found — running single LSD pass (same as lucy lsd run)"` and pass `suspect_correlations=[]` to `PyLSDOrchestrator.run()`. K=0 is handled gracefully (one empty-tuple iteration → one run).

**Note on LSDCorrelation reconstruction:** `PyLSDOrchestrator.run()` takes `suspect_correlations: list[LSDCorrelation]` but the CLI has only the `(atom1, atom2)` pairs from the inventory. The CLI must also parse the LSD file to get the full `LSDCorrelation` object (including `min_bonds`, `max_bonds`). Use `LSDInputParser.parse_file(lsd_file)` if it exists, or grep the HMBC line and construct `LSDCorrelation(atom1_index=..., atom2_index=..., correlation_type="HMBC")` directly. The orchestrator's `_build_permutation()` sets `max_bonds=4` on included suspects regardless of the input correlation's bond range (confirmed at `orchestrator.py:249`).

---

## `lsd_rank` Internalization: Refactoring Strategy (CLI-02 / D-14)

The current `lsd_rank` Click command at `cli/lsd.py:341-537` [VERIFIED] bundles: shift parsing, SMILES file loading, table path resolution, `SolutionRanker` construction, and output formatting — all inside one Click handler with no extractable helper.

**Required refactoring:**

Extract a `_perform_ranking()` helper that `lsd_rank` and `pylsd_run` both call:

```python
# In cli/lsd.py (or a shared cli/helpers.py)
def _perform_ranking(
    smiles_file: Path,
    shifts: list[float],
    top: int = 10,
    tolerance: float = 3.0,
    table: Path | None = None,
    output_format: str = "text",
) -> None:
    """Core ranking logic, callable from lsd_rank and pylsd_run."""
    # ... (body moved from lsd_rank, minus the argument parsing)
```

`lsd_rank` becomes a thin wrapper that parses CLI args and calls `_perform_ranking()`. `pylsd_run` calls `_perform_ranking()` after merge.

**Alternative (simpler):** Duplicate the ranking logic into `pylsd_run`. Acceptable for a first implementation; the refactor is cleaner but adds a task. Recommend extraction — it prevents drift.

---

## `lucy lsd rank` Output Format (for --format json shape alignment)

The existing JSON output from `lsd_rank --format json` (lines 479-507 in cli/lsd.py [VERIFIED]):

```json
{
  "total_solutions": 392,
  "ranked_count": 391,
  "skipped_count": 1,
  "experimental_shifts": [180.56, 140.84, ...],
  "tolerance": 3.0,
  "solutions": [
    {
      "rank": 1,
      "solution_index": 42,
      "smiles": "CC(C)Cc1ccc(CC(C)C(=O)O)cc1",
      "mae": 2.31,
      "quality": "Good",
      "deviations": [...],
      "within_3ppm": 11,
      "within_5ppm": 13,
      "total_carbons": 13,
      "max_deviation": 5.2,
      "prediction_rate": 0.923,
      "matched_count": 11,
      "has_aromatic_ring": true
    }
  ],
  "warnings": []
}
```

The `pylsd run --format json` output MUST wrap this in additional metadata per D-14c:

```json
{
  "permutations": 8,
  "merged_count": 47,
  "ranked_solutions": [...],   // same structure as solutions[] above
  "run_report_path": "/tmp/pylsd_run_xyz/run_report.json"
}
```

---

## FORM-Tolerance Test Design (D-15)

**Minimal LSD fixture for FORM tolerance test:**

The simplest LSD file that produces ≥1 solution is ethane (2 carbons, no HMBC needed):

```
; Minimal LSD test: ethane C2H6
MULT 1 C 3 3
MULT 2 C 3 3
HSQC 1 1
HSQC 2 2
EXIT
```

This fixture paired with a FORM variant:

```
; Minimal LSD test: ethane C2H6 — with FORM line
FORM C2H6
MULT 1 C 3 3
MULT 2 C 3 3
HSQC 1 1
HSQC 2 2
EXIT
```

Both files should produce the same solution set (1 solution: ethane). The test verifies InChI equality.

**LSD version capture:** `LSD 2>&1 | head -1` returns `LSD-3.4.9` [VERIFIED: observed output]. `LSDRunner.get_version()` exists (runner.py:377-399) but its `--version` flag invocation returns `"unknown"` since LSD doesn't accept that flag. Directly parse stderr: `subprocess.run(["LSD"], capture_output=True, text=True, timeout=5)` — stdout will be empty, stderr line 1 = `"LSD-3.4.9"`.

**findings/ directory:** `.planning/findings/` does not yet exist [VERIFIED: ls showed it absent]. Must create.

---

## Regression Test Design (D-16)

**Fixture:** Copy `.planning/phases/65-hypothesis-gate/ibuprofen_no4j.lsd` to `tests/fixtures/regression/ibuprofen_no_4j.lsd`. This file has 15 MULT atoms, 10 HSQC correlations, 9 HMBC correlations, 2 BOND constraints. No v2 inventory block. No `; ELIM` annotations. This is the "classic lucy lsd run" form required by D-16.

**Test flow:**
1. `lucy lsd run ibuprofen_no_4j.lsd` via subprocess or `LSDRunner.run_file()`
2. Collect `*.smi` or `*.sol` output
3. Parse SMILES with `LSDOutputParser.parse_smiles_file()`
4. Convert each SMILES → InChI via RDKit `MolToInchi`
5. Compare set against `ibuprofen_no_4j.expected_inchis.txt` (sorted, one per line)
6. Assert `set(actual_inchis) == set(baseline_inchis)` (order-independent)

**Baseline generation (Wave 0 task for developer):**
- Run: `lucy lsd run tests/fixtures/regression/ibuprofen_no_4j.lsd`
- Collect solutions: `outlsd 5 < *.sol > solutions.smi`
- Convert to InChI: short Python snippet or `lucy lsd rank --format json` + parse
- Inspect: visually verify ≥1 solution is chemically plausible (aromatic ring or not — this is the BEFORE-4J-fix state)
- Write to `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt`
- Commit with message: `"test: add ibuprofen regression baseline (LSD-3.4.9, manually verified)"`
- Estimated effort: 10-15 minutes

**Important:** The Phase 65 hypothesis gate already ran this file and found 392 solutions (see `65-SUMMARY.md` and `ibuprofen_no4j.sol`). The sol file already exists at `.planning/phases/65-hypothesis-gate/ibuprofen_no4j.sol`. Developer can use this as the baseline source rather than re-running, provided the LSD version is the same (LSD-3.4.9 — confirmed).

---

## Common Pitfalls

### Pitfall 1: CWD mutation from PyLSDOrchestrator

**What goes wrong:** `PyLSDOrchestrator._run_outlsd()` passes `cwd=perm_dir` to subprocess (orchestrator.py:288). This does NOT change the Python process CWD. But if `output_dir` is derived from `Path(".")`, it will resolve to wherever the CLI was invoked from — potentially an agent's `analysis/iteration_NN/` subfolder.

**Why it happens:** CLI convenience of defaulting to current dir without thinking about agent invocation context.

**How to avoid:** Default `output_dir` to a tempdir (`tempfile.mkdtemp(prefix="pylsd_")`) or `Path(lsd_file).parent / "pylsd_run"`. Make it explicit and predictable. Never use `Path(".")` as a default.

**Warning signs:** Output files appearing in unexpected locations during agent runs.

### Pitfall 2: `SolutionMerger.merge()` is idempotent but clobbers

**What goes wrong:** `merged.smi` and `run_report.json` are written to `output_dir`. If the CLI is called twice with the same `working-dir`, the files are silently overwritten.

**Why it happens:** `write_text()` with no append mode — design choice in Phase 67.

**How to avoid:** Document this behavior. For CLI, default working-dir should be unique per run (tempdir or timestamped subfolder). If `--working-dir` is explicitly supplied, user accepts overwrite semantics.

### Pitfall 3: `shutil.which("LSD")` case sensitivity

**What goes wrong:** `shutil.which("lsd")` (lowercase) may fail on macOS where the binary is named `LSD` (uppercase). Confirmed: the binary at `/Users/steinbeck/Dropbox/develop/LSD/LSD` is uppercase. [VERIFIED: `which LSD` succeeds, `which lsd` may not]

**Why it happens:** `LSDRunner.is_available()` internally uses `shutil.which("lsd")` (lowercase, runner.py:294) but relies on SEARCH_PATHS fallback. D-15 specifies `shutil.which("LSD")` in test skipif.

**How to avoid:** Use the exact string from D-15: `shutil.which("LSD")`. For robustness, consider checking both: `shutil.which("LSD") or shutil.which("lsd")`.

### Pitfall 4: K=0 when both sources are empty (D-13c)

**What goes wrong:** If `suspect_correlations=[]` is passed to `PyLSDOrchestrator.run()`, `K=0`, `itertools.product(repeat=0)` yields one empty tuple, producing exactly one permutation — which is semantically identical to `lucy lsd run`. This is correct behavior per D-13c but may confuse the developer if they forget K=0 is valid.

**Why it happens:** Forgetting that the K-cap guard only blocks K>3, not K=0.

**How to avoid:** No code fix needed — just add a comment and a warning message to the CLI.

### Pitfall 5: Ranking requires `--shifts` but `merged.smi` may be empty

**What goes wrong:** If all permutations fail (LSD produces no solutions), `merged.smi` is empty. Passing an empty SMILES file to `_perform_ranking()` causes an early error: "No SMILES found in file" (lsd.py:451).

**Why it happens:** No solutions from any permutation means SolutionMerger produces an empty file.

**How to avoid:** Check `merge_result.merged_solutions` before calling ranking. If empty, print a clear message and exit 0 (not 1 — no solutions is not an error in CASE workflow).

### Pitfall 6: Direct function call to validate-inventory internals

**What goes wrong:** Calling `lsd_validate_inventory` as a Click command via `CliRunner().invoke(...)` captures output but requires JSON parsing of the captured string. Direct Python call to `_extract_inventory_block()` + `json.loads()` + schema validation is cleaner but requires importing private functions.

**Why it happens:** D-14 recommends "Python-function-Aufruf" but `lsd_validate_inventory` is a Click command, not a pure function.

**How to avoid:** Extract a `_validate_and_parse_inventory(lsd_file: Path) -> dict | None` helper function from `lsd_validate_inventory`. This helper returns the parsed `instance` dict on success or `None` on failure. Both `lsd_validate_inventory` and `pylsd_run` call this helper. Similar to the `_rank_smiles_file()` refactor.

---

## Code Examples

### PyLSDOrchestrator Constructor and run() Signature

```python
# Source: src/lucy_ng/lsd/orchestrator.py lines 112-213 (VERIFIED)

class PyLSDOrchestrator:
    def __init__(
        self,
        lsd_path: str | Path | None = None,  # None = auto-detect
        timeout: int = 120,                   # per-permutation, seconds
    ) -> None:
        self.runner = LSDRunner(lsd_path)
        self.timeout = timeout

    def run(
        self,
        base_problem: LSDProblem,
        suspect_correlations: list[LSDCorrelation],  # K suspect correlations
        output_dir: Path,                              # perm_00/, perm_01/ written here
    ) -> OrchestrationResult:
        # FIRST statement: K-cap guard (raises ValueError if K>3)
        K = len(suspect_correlations)
        if K > 3:
            raise ValueError(...)
        # ... generates 2^K permutations
```

### SolutionMerger Constructor and merge() Signature

```python
# Source: src/lucy_ng/lsd/orchestrator.py lines 303-406 (VERIFIED)

class SolutionMerger:
    # No __init__ needed — stateless, instantiate with SolutionMerger()

    def merge(
        self,
        permutation_results: list[PermutationResult],  # from OrchestrationResult
        output_dir: Path,                               # merged.smi + run_report.json written here
    ) -> MergeResult:
        # Returns MergeResult with:
        #   .merged_solutions: list[MergedSolution]
        #   .merged_smi: Path (to merged.smi)
        #   .run_report: Path (to run_report.json)
```

### validate-inventory Success JSON Shape (CR-02 fix already in place)

```python
# Source: src/lucy_ng/cli/lsd.py line 309-315 (VERIFIED)
# Success response when --format json:
{
    "valid": True,
    "file": lsd_file,
    "version": 2,
    "inventory": instance,  # full parsed inventory for devils-advocate G2/G3 gates
}
# Note: "inventory" key is PRESENT in current code (line 314 confirmed).
# The CR-02 fix from Phase 68 VERIFICATION.md is already applied.
```

### skipif Pattern for LSD-dependent tests

```python
# Source: tests/test_lsd_integration.py lines 14-16 (VERIFIED)
import shutil
import pytest

@pytest.mark.skipif(
    shutil.which("LSD") is None,
    reason="LSD binary not installed"
)
def test_form_tolerance_no_change(tmp_path):
    ...
```

### CliRunner pattern for pylsd CLI tests

```python
# Source: tests/test_inventory_schema.py (VERIFIED pattern)
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from lucy_ng.cli.pylsd import pylsd

class TestPylsdRunCLI:
    def test_run_no_rank_calls_orchestrator(self, tmp_path):
        lsd_file = tmp_path / "compound.lsd"
        lsd_file.write_text("; minimal lsd file\nEXIT\n")

        with patch("lucy_ng.cli.pylsd.PyLSDOrchestrator") as MockOrch, \
             patch("lucy_ng.cli.pylsd.SolutionMerger") as MockMerger:
            # set up mocks ...
            runner = CliRunner()
            result = runner.invoke(pylsd, ["run", str(lsd_file), "--no-rank"])
        assert result.exit_code == 0
```

---

## Module Organization Recommendation

**Recommendation: New file `src/lucy_ng/cli/pylsd.py`** [ASSUMED — based on cohesion analysis of existing modules]

Rationale:
- `src/lucy_ng/cli/lsd.py` is already 664 lines. Adding ~150 lines of `pylsd run` logic would push it past a comfortable single-responsibility boundary.
- The `lsd` and `pylsd` groups represent different user-facing workflows (single-run vs. multi-run orchestration). They share helpers but not command hierarchy.
- Separating into `pylsd.py` makes it easy to import `from lucy_ng.cli.pylsd import pylsd` in tests without importing the entire `lsd` module.
- The `lsd.py` refactoring (extracting `_rank_smiles_file()` and `_validate_and_parse_inventory()`) produces clean helpers importable by `pylsd.py`.

This matches the pattern used for other CLI modules in the project (`detect.py`, `predict.py`, `fragment.py` — each a separate module for each `lucy` subgroup).

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `LSDRunner._run_outlsd()` (buggy, missing mode arg) | Direct `subprocess.run([outlsd_path, "5"], stdin=sol_file)` | Phase 65 finding, fixed in Phase 67 | Must use the Phase 67 outlsd bypass pattern — never call `_run_outlsd()` |
| ELIM drops correlations entirely | `HMBC X Y 2 4` extends bond range for 4J | Phase 68 locked decision | CLI must NOT use ELIM for 4J handling |
| v1 inventory (string descriptions in deferred_4j) | v2 inventory (object array with atom1/atom2/shift) | Phase 68 | `lucy pylsd run` reads v2 format only; error on v1 |
| `lsd_rank` has no extractable helper | After Phase 69: `_rank_smiles_file()` helper extracted | This phase | Required for D-14 integrated pipeline |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | New code lives in `src/lucy_ng/cli/pylsd.py` (separate module, not added to `lsd.py`) | Module Organization | Low — either location works; planner may choose differently |
| A2 | Default working-dir for pylsd run is a tempdir or `dirname(lsd_file)/pylsd_run` | Architecture Patterns | Low — behavior difference for agent, not a correctness issue |
| A3 | `shutil.which("LSD")` (uppercase) is the correct check on this machine | Pattern 3 | Low — both forms could be checked; already confirmed uppercase binary |
| A4 | The Phase 65 sol file can serve as the baseline for regression tests without re-running | Regression Test Design | Low — same LSD version (3.4.9) confirmed, same input file |
| A5 | `_rank_smiles_file()` helper extraction does not break existing `lsd_rank` behavior | Don't Hand-Roll | Low — pure refactor with no behavior change |

---

## Open Questions (RESOLVED)

1. **LSD input file parsing for suspect reconstruction** — RESOLVED: `LSDInputParser.parse_file()` is the canonical mechanism; CLI imports it and uses `problem.correlations` to find matching `LSDCorrelation` objects by `(atom1_index, atom2_index, correlation_type)` tuple. If the parser is unavailable for a given LSD-file shape, fall back to manual `LSDCorrelation(atom1_index=..., atom2_index=..., correlation_type="HMBC")` construction — `_build_permutation()` only uses these three fields for identity matching. Plan 02 interfaces block confirms this approach.

2. **Default working-dir for `pylsd run --no-rank`** — RESOLVED: Default is `Path(lsd_file).parent / "pylsd_run"`, configurable via `--working-dir`. Confirmed by Plan 02 Task 1 action block. Rationale: agent workflow keeps outputs colocated with input file (iteration directory pattern); avoids tempdir tracking.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| LSD binary | FORM tolerance test, regression test | ✓ | LSD-3.4.9 [VERIFIED: observed output] | Tests decorated with `@skipif` |
| outlsd binary | PyLSDOrchestrator SMILES conversion | ✓ | same install as LSD [VERIFIED: `lucy lsd check` passes] | `smiles_file=None` — merger skips permutation |
| RDKit | InChI generation in regression tests | ✓ | >=2023.0 [VERIFIED: pyproject.toml] | No fallback — required |
| jsonschema | validate-inventory call | ✓ | >=4.18.0 [VERIFIED: pyproject.toml] | No fallback — required |
| pytest CliRunner | CLI integration tests | ✓ | included in click>=8.0 [VERIFIED] | No fallback — required |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** LSD/outlsd are gated behind `@skipif` decorators, so tests degrade gracefully on machines without the binary.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=7.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` testpaths=["tests"] |
| Quick run command | `pytest tests/test_pylsd_cli.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLI-01 | `lucy pylsd run` orchestrates permutations, merges, outputs solutions | CLI integration (mocked orchestrator) | `pytest tests/test_pylsd_cli.py -x` | ❌ Wave 0 |
| CLI-01 | FORM-tolerance: LSD ignores unknown commands | Integration (real LSD) | `pytest tests/test_lsd_form_tolerance.py -x` | ❌ Wave 0 |
| CLI-02 | Two-tier ranking reused from `lsd rank` logic | unit (helper function) | `pytest tests/test_pylsd_cli.py::TestRankingIntegration -x` | ❌ Wave 0 |
| CLI-03 | `lucy lsd run` on ibuprofen produces same InChI set as baseline | Integration (real LSD) | `pytest tests/test_lsd_regression.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_pylsd_cli.py tests/test_lsd_form_tolerance.py tests/test_lsd_regression.py -x`
- **Per wave merge:** `pytest` (full suite)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_pylsd_cli.py` — covers CLI-01, CLI-02
- [ ] `tests/test_lsd_form_tolerance.py` — covers CLI-01 (FORM tolerance sub-criterion)
- [ ] `tests/test_lsd_regression.py` — covers CLI-03
- [ ] `tests/fixtures/regression/ibuprofen_no_4j.lsd` — input fixture (copy from Phase 65)
- [ ] `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt` — baseline (developer generates)
- [ ] `.planning/findings/` directory — must be created (does not exist)
- [ ] `.planning/findings/form-tolerance.md` — findings document

---

## Security Domain

This phase has no authentication, session management, or cryptographic components. CLI commands operate on local files only. No network I/O. ASVS V5 (Input Validation) applies minimally: `click.Path(exists=True)` validates file existence; comma-separated shift parsing uses `float(s.strip())` with a ValueError catch (pattern already in `lsd_rank`, line 419-423).

No novel security considerations beyond the existing CLI patterns.

---

## Sources

### Primary (HIGH confidence)

- `src/lucy_ng/lsd/orchestrator.py` — PyLSDOrchestrator constructor (line 126), run() signature (line 141), SolutionMerger.merge() signature (line 318), outlsd bypass pattern (line 255-295), InChI generation (line 408-428)
- `src/lucy_ng/cli/lsd.py` — lsd_rank Click command (line 341-537), validate-inventory success JSON shape (line 309-315), `_extract_inventory_block()` (line 174-204), Click group pattern (line 16-19), `raise SystemExit(1)` convention
- `src/lucy_ng/cli/main.py` — subgroup registration pattern (lines 12, 52)
- `schemas/constraint_inventory_v2.json` — `deferred_4j` object schema (lines 88-126), `inventory` key structure
- `tests/test_lsd_integration.py` — `@pytest.mark.skipif(not LSDRunner.is_available(), reason="LSD not installed")` pattern (lines 14-16)
- `tests/test_inventory_schema.py` — CliRunner test pattern (TestValidateInventoryCLI class)
- `pyproject.toml` — all dependencies confirmed present (lines 26-35)
- `.planning/phases/65-hypothesis-gate/ibuprofen_no4j.lsd` — regression fixture source
- `LSD 2>&1 | head -1` output — version string `LSD-3.4.9` confirmed live

### Secondary (MEDIUM confidence)

- `.planning/phases/67-*/67-01-SUMMARY.md` and `67-02-SUMMARY.md` — K=0 behavior, outlsd bypass rationale, InChI key rationale
- `.planning/phases/68-*/68-VERIFICATION.md` — CR-02 status, `inventory` key confirmation, `deferred_4j` object array shape
- `69-CONTEXT.md` — D-13 through D-16 locked decisions

### Tertiary (LOW confidence)

None.

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all packages verified in pyproject.toml, no new deps
- Architecture: HIGH — all API signatures read directly from implemented code
- Pitfalls: HIGH — derived from code reading (CWD issue from orchestrator.py:288, case sensitivity from runner.py:294)
- Regression baseline workflow: MEDIUM — procedure is straightforward but not previously executed for this exact path; sol file from Phase 65 exists as shortcut

**Research date:** 2026-05-19
**Valid until:** 2026-06-19 (stable domain — no upstream dependencies changing)
