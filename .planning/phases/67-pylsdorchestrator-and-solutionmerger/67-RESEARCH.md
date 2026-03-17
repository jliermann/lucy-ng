# Phase 67: PyLSDOrchestrator and SolutionMerger — Research

**Researched:** 2026-03-17
**Domain:** Python orchestration — LSD permutation generation, subprocess management, SMILES deduplication via InChI, JSON provenance tracking
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ORCH-01 | PyLSDOrchestrator generates permutations of LSD input files with different 4J correlation configurations (include/exclude suspect HMBCs) | `LSDProblem` with `pylsd_mode=True` is the unit of file generation. Permutation = copy of base problem with specific HMBC lines tagged `max_bonds=4` (include) or omitted (exclude). `itertools.product([True, False], repeat=K)` generates 2^K combos. `LSDInputGenerator.write_file()` writes each permutation. |
| ORCH-02 | PyLSDOrchestrator caps permutation count (K≤3 excluded correlations) to prevent combinatorial explosion | K is the number of suspect correlations passed to the orchestrator. Guard: `if K > 3: raise ValueError(...)`. Rational bound: 2^3 = 8 runs, manageable sequentially in seconds. 2^4 = 16 is the next step, explicitly out of scope per REQUIREMENTS.md. |
| ORCH-03 | SolutionMerger deduplicates solutions from multiple LSD runs using InChI canonicalization | `from rdkit.Chem.inchi import MolToInchi, InchiToInchiKey` — confirmed available in project environment. Deduplication key = InChI key (27-char base64). SMILES normalization alone is insufficient because `MolToSmiles(MolFromSmiles(x))` still produces tautomer/stereochemistry variants; InChI is canonical by spec. |
| ORCH-04 | SolutionMerger preserves provenance (which correlation configuration produced each solution) | Provenance = dict mapping InChI key → list of permutation indices that produced it. Written to `run_report.json`. Each permutation record includes its correlation configuration (which suspects were included vs excluded) and which solution indices map to it. |
</phase_requirements>

---

## Summary

Phase 67 is a **pure Python implementation** in two new classes: `PyLSDOrchestrator` (permutation generation + sequential LSD execution) and `SolutionMerger` (InChI-based deduplication + provenance JSON). No new runtime dependencies are required — RDKit (already in pyproject.toml as `rdkit>=2023.0`) provides InChI canonicalization, and the existing `LSDRunner`, `LSDInputGenerator`, and `LSDOutputParser` provide all the file generation and subprocess execution infrastructure.

The key insight from Phase 65 validation is that the orchestrator must run the LSD binary once per permutation and collect solutions from each run before merging. The merge step uses InChI keys as canonical identifiers to eliminate duplicates regardless of SMILES representation differences. The `run_report.json` file records which permutation (correlation configuration) produced each unique structure, giving the downstream ranker and agent full traceability.

The outlsd invocation pattern from Phase 65 (`outlsd 5 < compound.sol`) is the correct approach. The `LSDRunner._run_outlsd()` method has a known bug (missing `mode` argument, documented in STATE.md) — the orchestrator MUST bypass `LSDRunner._run_outlsd()` and invoke `outlsd` directly via subprocess, or call `LSDRunner.run_file()` and then run outlsd manually. Both approaches are documented below.

**Primary recommendation:** Implement `PyLSDOrchestrator` in `src/lucy_ng/lsd/orchestrator.py` and `SolutionMerger` in the same file. Place both classes in the `lucy_ng.lsd` package. Export from `lucy_ng/lsd/__init__.py`. Write tests in `tests/test_lsd_orchestrator.py`.

---

## Standard Stack

### Core (already in project — no new installs)
| Module | Version | Purpose | Why Standard |
|--------|---------|---------|--------------|
| `rdkit.Chem.inchi` | rdkit>=2023.0 | InChI/InChIKey generation from SMILES | Already a project dependency; confirmed `MolToInchi` + `InchiToInchiKey` work in this environment |
| `itertools.product` | stdlib | Generate 2^K boolean permutation tuples | Standard combinatorics, no external dep |
| `json` | stdlib | Serialize `run_report.json` | Standard serialization |
| `dataclasses` | stdlib | `OrchestrationResult`, `MergedSolution` models | Consistent with existing codebase pattern |
| `pathlib.Path` | stdlib | File I/O | Used throughout codebase |
| `lucy_ng.lsd.generator` | internal | `LSDInputGenerator.write_file()`, `generate()` | Produces LSD input files from `LSDProblem` |
| `lucy_ng.lsd.runner` | internal | `LSDRunner.run_file()` for subprocess | Manages LSD binary execution |
| `lucy_ng.lsd.parser` | internal | `LSDOutputParser.parse_smiles_file()` | Parses outlsd SMILES output |
| `lucy_ng.lsd.models` | internal | `LSDProblem`, `LSDCorrelation` | Data model for permutation modification |

### Supporting
| Module | Version | Purpose | When to Use |
|--------|---------|---------|-------------|
| `copy.deepcopy` | stdlib | Clone `LSDProblem` for each permutation | Needed to avoid mutating the base problem |
| `subprocess` | stdlib | Direct `outlsd` invocation (bypassing the buggy `_run_outlsd`) | LSDRunner._run_outlsd has missing `mode` argument bug — bypass until Phase 69 fixes it |
| `shutil.which` | stdlib | Locate `outlsd` binary | Same pattern as `LSDRunner._find_outlsd()` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| InChI key deduplication | Canonical SMILES | SMILES canonicalization is not guaranteed to be identical across RDKit versions or for complex stereochemistry. InChI is designed as a canonical identifier. Use InChI. |
| `dataclasses` for models | `pydantic` | Pydantic v2 is in project deps but existing `LSDProblem`, `LSDResult` use `dataclasses`. Stay consistent — use `dataclasses` for new models. |
| Sequential runs | `multiprocessing` | REQUIREMENTS.md explicitly defers parallel execution to "nice-to-have". Sequential is sufficient for ≤8 runs. Do NOT add parallel execution in Phase 67. |

**Installation:** None required.

---

## Architecture Patterns

### Recommended Project Structure

```
src/lucy_ng/lsd/
├── orchestrator.py     # NEW: PyLSDOrchestrator + SolutionMerger + supporting models
├── models.py           # Existing — no changes needed
├── generator.py        # Existing — no changes needed (Phase 66 complete)
├── runner.py           # Existing — no changes needed (outlsd bypass in orchestrator)
├── parser.py           # Existing — no changes needed
└── __init__.py         # Modify: add PyLSDOrchestrator, SolutionMerger to exports

tests/
└── test_lsd_orchestrator.py    # NEW: Tests for orchestrator + merger
```

### Pattern 1: PyLSDOrchestrator

**What:** Takes a base `LSDProblem` (with `pylsd_mode=True`) and a list of "suspect" `LSDCorrelation` objects. Generates one `LSDProblem` per permutation (each permutation either includes or excludes each suspect correlation). Runs `LSDRunner.run_file()` for each, then calls outlsd to get SMILES.

**Key constraint from REQUIREMENTS.md (ORCH-02):** Abort with `ValueError` if `len(suspect_correlations) > 3`.

**Permutation generation:**
```python
# Source: itertools.product documentation (stdlib)
import copy
import itertools
from pathlib import Path

from lucy_ng.lsd.generator import LSDInputGenerator
from lucy_ng.lsd.models import LSDCorrelation, LSDProblem

class PyLSDOrchestrator:
    def __init__(self, lsd_path: str | Path | None = None, timeout: int = 120):
        self.runner = LSDRunner(lsd_path)
        self.timeout = timeout

    def run(
        self,
        base_problem: LSDProblem,
        suspect_correlations: list[LSDCorrelation],
        output_dir: Path,
    ) -> "OrchestrationResult":
        K = len(suspect_correlations)
        if K > 3:
            raise ValueError(
                f"Too many suspect correlations: {K}. Maximum is 3 (2^3=8 permutations). "
                f"Reduce the number of suspect correlations or handle them manually."
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        permutation_results = []

        # itertools.product([True, False], repeat=K) generates 2^K tuples
        for perm_idx, include_flags in enumerate(itertools.product([True, False], repeat=K)):
            perm_problem = self._build_permutation(base_problem, suspect_correlations, include_flags)
            perm_dir = output_dir / f"perm_{perm_idx:02d}"
            perm_dir.mkdir(exist_ok=True)

            # Write LSD file
            lsd_file = perm_dir / f"{base_problem.name}.lsd"
            LSDInputGenerator.write_file(perm_problem, lsd_file)

            # Run LSD
            lsd_result = self.runner.run_file(lsd_file, output_dir=perm_dir, timeout=self.timeout)

            # Run outlsd to get SMILES (bypass LSDRunner._run_outlsd due to known bug)
            smiles_file = self._run_outlsd(perm_dir, lsd_file)

            permutation_results.append(PermutationResult(
                perm_index=perm_idx,
                include_flags=list(include_flags),
                suspect_correlations=suspect_correlations,
                lsd_result=lsd_result,
                smiles_file=smiles_file,
                perm_dir=perm_dir,
            ))

        return OrchestrationResult(
            base_problem=base_problem,
            suspect_correlations=suspect_correlations,
            permutation_results=permutation_results,
            output_dir=output_dir,
        )
```

**Building each permutation problem:**
```python
    def _build_permutation(
        self,
        base_problem: LSDProblem,
        suspects: list[LSDCorrelation],
        include_flags: tuple[bool, ...],
    ) -> LSDProblem:
        """Clone base problem, include/exclude suspect correlations per flags."""
        perm = copy.deepcopy(base_problem)
        # Remove all suspect correlations from the clone
        suspect_set = {id(s) for s in suspects}  # identity-based removal won't work on deep copy
        # Re-identify by (atom1_index, atom2_index, correlation_type)
        suspect_keys = {
            (s.atom1_index, s.atom2_index, s.correlation_type) for s in suspects
        }
        perm.correlations = [
            c for c in perm.correlations
            if (c.atom1_index, c.atom2_index, c.correlation_type) not in suspect_keys
        ]
        # Add back suspects that are flagged as included (with extended bond range 2-4)
        for corr, include in zip(suspects, include_flags):
            if include:
                included_corr = copy.deepcopy(corr)
                included_corr.max_bonds = 4  # Use extended range for suspect correlations
                perm.correlations.append(included_corr)
        return perm
```

### Pattern 2: outlsd Bypass

**Problem:** `LSDRunner._run_outlsd()` has a bug (missing `mode` argument — logged in STATE.md Phase 65 findings). The outlsd binary requires a mode integer before reading the sol file. The correct invocation is `outlsd 5 < compound.sol` (shell) or with explicit stdin argument.

**Working pattern from Phase 65:**
```bash
outlsd 5 < compound.sol > solutions.smi
```

**Python implementation (bypass the buggy helper):**
```python
import shutil
import subprocess

def _run_outlsd(self, perm_dir: Path, lsd_file: Path) -> Path | None:
    """Run outlsd directly, bypassing LSDRunner._run_outlsd bug."""
    outlsd_path = shutil.which("outlsd")
    if outlsd_path is None:
        return None

    sol_files = list(perm_dir.glob("*.sol"))
    if not sol_files:
        return None

    sol_file = sol_files[0]
    smiles_file = perm_dir / "solutions.smi"

    try:
        proc = subprocess.run(
            [outlsd_path, "5"],       # mode argument 5 = SMILES output
            stdin=open(sol_file),     # reads .sol file
            capture_output=True,
            text=True,
            timeout=30,
            cwd=perm_dir,
        )
        if proc.stdout.strip():
            smiles_file.write_text(proc.stdout)
            return smiles_file
    except Exception:
        pass

    return None
```

**CRITICAL:** The `outlsd 5` mode integer is required. The bug in `LSDRunner._run_outlsd` is that it calls outlsd without the mode argument (passes the LSD input file content as stdin instead of the sol file). Do not use `runner._run_outlsd()` — call outlsd directly as shown above.

### Pattern 3: SolutionMerger

**What:** Takes a list of `PermutationResult` objects (each with a SMILES file path and correlation configuration). Deduplicates solutions by InChI key. Writes `merged.smi` and `run_report.json`.

```python
import json
from rdkit import Chem
from rdkit.Chem.inchi import MolToInchi, InchiToInchiKey
from lucy_ng.lsd.parser import LSDOutputParser

@dataclass
class MergedSolution:
    inchi_key: str
    canonical_smiles: str
    provenance: list[dict]  # [{perm_index, include_flags, original_index}]

class SolutionMerger:
    def merge(
        self,
        permutation_results: list[PermutationResult],
        output_dir: Path,
    ) -> "MergeResult":
        seen: dict[str, MergedSolution] = {}

        for perm_result in permutation_results:
            if perm_result.smiles_file is None or not perm_result.smiles_file.exists():
                continue

            solutions = LSDOutputParser.parse_smiles_file(perm_result.smiles_file)
            for solution in solutions:
                inchi_key = self._smiles_to_inchi_key(solution.smiles)
                if inchi_key is None:
                    continue

                provenance_entry = {
                    "perm_index": perm_result.perm_index,
                    "include_flags": perm_result.include_flags,
                    "original_solution_index": solution.index,
                    "active_correlations": [
                        {"atom1": c.atom1_index, "atom2": c.atom2_index}
                        for c, included in zip(perm_result.suspect_correlations, perm_result.include_flags)
                        if included
                    ],
                }

                if inchi_key not in seen:
                    canonical_smiles = self._canonicalize(solution.smiles)
                    seen[inchi_key] = MergedSolution(
                        inchi_key=inchi_key,
                        canonical_smiles=canonical_smiles or solution.smiles,
                        provenance=[provenance_entry],
                    )
                else:
                    seen[inchi_key].provenance.append(provenance_entry)

        merged_solutions = list(seen.values())

        # Write merged.smi
        merged_smi = output_dir / "merged.smi"
        merged_smi.write_text("\n".join(s.canonical_smiles for s in merged_solutions))

        # Write run_report.json
        report = {
            "total_permutations": len(permutation_results),
            "total_raw_solutions": sum(
                len(LSDOutputParser.parse_smiles_file(p.smiles_file))
                for p in permutation_results
                if p.smiles_file and p.smiles_file.exists()
            ),
            "unique_solutions": len(merged_solutions),
            "solutions": [
                {
                    "inchi_key": s.inchi_key,
                    "smiles": s.canonical_smiles,
                    "provenance": s.provenance,
                }
                for s in merged_solutions
            ],
        }
        report_file = output_dir / "run_report.json"
        report_file.write_text(json.dumps(report, indent=2))

        return MergeResult(
            merged_solutions=merged_solutions,
            merged_smi=merged_smi,
            run_report=report_file,
        )

    def _smiles_to_inchi_key(self, smiles: str) -> str | None:
        """Convert SMILES to InChI key for deduplication."""
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            inchi = MolToInchi(mol)
            if inchi is None:
                return None
            return InchiToInchiKey(inchi)
        except Exception:
            return None

    def _canonicalize(self, smiles: str) -> str | None:
        """Get canonical SMILES via RDKit."""
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            return Chem.MolToSmiles(mol)
        except Exception:
            return None
```

### Pattern 4: Supporting Dataclasses

```python
from dataclasses import dataclass, field
from pathlib import Path
from lucy_ng.lsd.models import LSDCorrelation, LSDProblem
from lucy_ng.lsd.runner import LSDResult

@dataclass
class PermutationResult:
    """Result of running LSD on one permutation."""
    perm_index: int
    include_flags: list[bool]        # True=include suspect, False=exclude
    suspect_correlations: list[LSDCorrelation]
    lsd_result: LSDResult
    smiles_file: Path | None
    perm_dir: Path

@dataclass
class OrchestrationResult:
    """Result of running PyLSDOrchestrator."""
    base_problem: LSDProblem
    suspect_correlations: list[LSDCorrelation]
    permutation_results: list[PermutationResult]
    output_dir: Path

@dataclass
class MergedSolution:
    """A unique solution after deduplication."""
    inchi_key: str
    canonical_smiles: str
    provenance: list[dict] = field(default_factory=list)

@dataclass
class MergeResult:
    """Result of SolutionMerger.merge()."""
    merged_solutions: list[MergedSolution]
    merged_smi: Path
    run_report: Path
```

### Anti-Patterns to Avoid

- **Don't mutate the base `LSDProblem` directly.** Always `copy.deepcopy(base_problem)` before modification. If correlations are mutated in place, the base problem changes for subsequent permutations.
- **Don't identify suspect correlations by `id()` after deepcopy.** `deepcopy` creates new objects — the `id()` of deepcopied correlations won't match the original suspects. Use `(atom1_index, atom2_index, correlation_type)` as the removal key.
- **Don't use `LSDRunner._run_outlsd()`.** It has a known bug (missing mode argument). Call the outlsd binary directly as `[outlsd_path, "5"]` with the `.sol` file as stdin.
- **Don't deduplicate by canonical SMILES alone.** RDKit SMILES canonicalization varies for tautomers/stereoisomers. InChI key is the correct deduplication key.
- **Don't write `merged.smi` with empty lines.** Filter out None or empty canonical SMILES before writing.
- **Don't include ORCH-02 guard as just a warning.** It must be a hard `ValueError` — the success criterion requires "aborts with a clear error."

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Canonical molecule identity | Custom SMILES comparison | `InchiToInchiKey(MolToInchi(mol))` | SMILES canonicalization is not unique across representations; InChI is designed as a canonical identifier |
| Permutation enumeration | Manual binary counting | `itertools.product([True, False], repeat=K)` | stdlib, tested, readable |
| LSD file writing | String concatenation | `LSDInputGenerator.write_file(problem, path)` | Handles all the FORM/MULT/HMBC formatting — Phase 66 complete |
| LSD execution | `os.system()` | `LSDRunner.run_file(lsd_file, ...)` | Handles timeout, output capture, solution counting |
| SMILES file parsing | Line-by-line regex | `LSDOutputParser.parse_smiles_file()` | Existing, tested parser |
| Deep problem clone | Manual field-by-field copy | `copy.deepcopy(problem)` | Handles nested `LSDAtom`, `LSDCorrelation`, `LSDConstraint` lists |

---

## Common Pitfalls

### Pitfall 1: outlsd Mode Argument Missing

**What goes wrong:** `outlsd` is called without the mode argument (`5`), producing no SMILES output or an error. `LSDRunner._run_outlsd()` has this bug already — it passes the LSD input file content as stdin rather than the sol file, and omits the mode integer.

**Why it happens:** The working pattern from Phase 65 was discovered empirically: `outlsd 5 < compound.sol`. The `5` is a required positional argument specifying SMILES output mode.

**How to avoid:** Invoke outlsd as `subprocess.run([outlsd_path, "5"], stdin=open(sol_file), ...)`. Do NOT use `runner._run_outlsd()`.

**Warning signs:** `solutions.smi` is empty or missing; outlsd exits with non-zero return code.

### Pitfall 2: Suspect Correlation Identity After deepcopy

**What goes wrong:** The orchestrator uses `id(suspect)` to identify which correlations to remove from the deepcopied problem — but `deepcopy` creates new objects with different `id()` values, so none are removed.

**Why it happens:** Python `id()` is memory address — different object, different id.

**How to avoid:** Identify suspect correlations by value tuple `(atom1_index, atom2_index, correlation_type)`. Build a set of these tuples from the original suspect list, then filter the copied problem's correlations against this set.

**Warning signs:** All correlations remain in the permutation even when `include_flags` contains `False`.

### Pitfall 3: InChI Generation Failure for Invalid SMILES

**What goes wrong:** `MolToInchi(mol)` returns `None` for some valid-looking SMILES (e.g., valence violations, disconnected structures). Passing `None` to `InchiToInchiKey()` raises `ValueError`.

**Why it happens:** outlsd occasionally produces technically invalid SMILES for strained structures. RDKit sanitization rejects them.

**How to avoid:** Guard with `if mol is None: return None` and `if inchi is None: return None`. These solutions are simply skipped during merge (logged as "invalid SMILES"). This is acceptable — the structure is likely chemically nonsensical.

**Warning signs:** `MolFromSmiles()` returning None for solutions that appear reasonable; cryptic errors during merge.

### Pitfall 4: K>3 Check Timing

**What goes wrong:** The combinatorial explosion check `if K > 3: raise ValueError(...)` is placed after some computation (directory creation, file writing), leaving partial state on disk when the error fires.

**Why it happens:** Defensive checks added after setup code.

**How to avoid:** Check `K = len(suspect_correlations); if K > 3: raise ValueError(...)` as the FIRST statement in `run()`, before any directory creation or file I/O.

**Warning signs:** Output directories are partially created before the error fires.

### Pitfall 5: Permutation Count Off-By-One

**What goes wrong:** With K=0 suspect correlations, `itertools.product([True, False], repeat=0)` yields exactly one empty tuple `[()]`. This is correct — it means "run LSD once with the base problem unchanged." Failing to handle K=0 gracefully breaks the single-run case.

**Why it happens:** Edge case not considered.

**How to avoid:** K=0 should work naturally — `itertools.product` with `repeat=0` yields `[()]`, which runs exactly once. No special case needed.

### Pitfall 6: run_report.json Missing Correlation Configuration Detail

**What goes wrong:** `run_report.json` records `perm_index` but not WHICH correlations were active in each run. The success criterion for ORCH-04 requires "which correlations were active in that run."

**Why it happens:** Provenance data is underspecified.

**How to avoid:** Each provenance entry must include both `include_flags` (list of booleans) AND `active_correlations` (list of `{atom1, atom2}` dicts for suspects that were included with `include_flags[i]=True`).

---

## Code Examples

### InChI Generation (confirmed working in this environment)

```python
# Source: verified in project environment 2026-03-17
from rdkit import Chem
from rdkit.Chem.inchi import MolToInchi, InchiToInchiKey

mol = Chem.MolFromSmiles("CC(C)Cc1ccc(C(C)C(=O)O)cc1")  # ibuprofen
inchi = MolToInchi(mol)
# "InChI=1S/C13H18O2/c1-9(2)8-10-4-6-11(7-5-10)12(3)13(14)15/h4-7,9,12H,8H2,1-3H3,(H,14,15)"
key = InchiToInchiKey(inchi)
# "HEFNNWSXXWATRW-UHFFFAOYSA-N"
```

### itertools.product for permutations

```python
# Source: Python stdlib documentation
import itertools

K = 3  # 3 suspect correlations
for perm_idx, include_flags in enumerate(itertools.product([True, False], repeat=K)):
    print(perm_idx, include_flags)
# 0 (True, True, True)     → all 3 included (extended range)
# 1 (True, True, False)    → first 2 included, third excluded
# 2 (True, False, True)    → ...
# ...
# 7 (False, False, False)  → all 3 excluded (base run)
```

### deepcopy pattern for LSDProblem

```python
import copy
from lucy_ng.lsd.models import LSDProblem

# CORRECT: deep copy before mutation
perm_problem = copy.deepcopy(base_problem)
perm_problem.name = f"perm_{perm_idx:02d}"

# WRONG: direct mutation corrupts the base problem
# base_problem.correlations.remove(...)  # DON'T DO THIS
```

### Suspect correlation removal by value tuple

```python
suspect_keys = {
    (c.atom1_index, c.atom2_index, c.correlation_type)
    for c in suspect_correlations
}
perm_problem.correlations = [
    c for c in perm_problem.correlations
    if (c.atom1_index, c.atom2_index, c.correlation_type) not in suspect_keys
]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single LSD run with all HMBC | Multi-run permutation orchestration | Phase 67 (new) | Correct ibuprofen structure found at rank 219 in Phase 65 test; expected to move to top with proper inclusion |
| No deduplication across runs | InChI key deduplication | Phase 67 (new) | Prevents same structure appearing multiple times in merged output |
| LSD solutions without provenance | `run_report.json` with per-solution provenance | Phase 67 (new) | Agent can trace which correlation configuration found the correct structure |

**Deprecated/outdated:**
- `LSDRunner._run_outlsd()`: Buggy — do not use in orchestrator. Direct subprocess call is the correct pattern. Will be fixed in Phase 69.

---

## Open Questions

1. **LSD binary timeout per permutation**
   - What we know: Phase 65 ibuprofen run (9 HMBC correlations, 392 solutions) completed in approximately 30-60 seconds based on the output. 8 permutations sequentially = 8x that time.
   - What's unclear: Whether a 120-second per-run timeout is sufficient for complex problems. Default `LSDRunner.run()` timeout is 60 seconds.
   - Recommendation: Use `timeout=120` (2 minutes) per permutation as the default. Make it a constructor parameter so it can be overridden.

2. **K=0 edge case behavior**
   - What we know: `itertools.product([True, False], repeat=0)` yields `[()]` — one run with no modifications to the base problem.
   - What's unclear: Whether calling `PyLSDOrchestrator.run()` with an empty suspect list should be an error or a valid single-run mode.
   - Recommendation: Allow K=0 (single-run mode). This is a valid use case for testing orchestrator mechanics without any suspect correlations.

3. **Naming of permutation files**
   - What we know: Output goes to `output_dir/perm_00/`, `perm_01/`, etc. Each contains `{problem.name}.lsd`, the `*.sol` file, and `solutions.smi`.
   - What's unclear: Whether the permutation directory naming should encode which correlations are included (e.g., `perm_TTF` for True/True/False).
   - Recommendation: Use `perm_{idx:02d}` naming for simplicity. The mapping from index to configuration is recorded in `run_report.json`. Human-readable config names would be a nice-to-have for Phase 71 UAT but are not required by ORCH-04.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` (rootdir: `/Users/steinbeck/Dropbox/develop/lucy-ng`) |
| Quick run command | `pytest tests/test_lsd_orchestrator.py -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ORCH-01 | `PyLSDOrchestrator` with 3 suspects generates 8 permutation LSD files, each valid | unit (no LSD binary) | `pytest tests/test_lsd_orchestrator.py -k "test_generates_permutation_files" -x` | Wave 0 (new) |
| ORCH-01 | Each permutation file excludes/includes the correct suspect correlations | unit | `pytest tests/test_lsd_orchestrator.py -k "test_permutation_content" -x` | Wave 0 (new) |
| ORCH-02 | `PyLSDOrchestrator.run()` raises `ValueError` when K=4 suspects | unit | `pytest tests/test_lsd_orchestrator.py -k "test_k_greater_than_3_raises" -x` | Wave 0 (new) |
| ORCH-02 | K=3 suspects succeeds; K=0 succeeds (single run) | unit | `pytest tests/test_lsd_orchestrator.py -k "test_k_boundary" -x` | Wave 0 (new) |
| ORCH-03 | `SolutionMerger` deduplicates: same structure in 3 run results appears once in merged output | unit | `pytest tests/test_lsd_orchestrator.py -k "test_deduplication" -x` | Wave 0 (new) |
| ORCH-03 | `merged.smi` written with correct count of unique SMILES | unit | `pytest tests/test_lsd_orchestrator.py -k "test_merged_smi_written" -x` | Wave 0 (new) |
| ORCH-04 | `run_report.json` contains provenance for each solution: `perm_index`, `include_flags`, `active_correlations` | unit | `pytest tests/test_lsd_orchestrator.py -k "test_run_report_provenance" -x` | Wave 0 (new) |
| ORCH-04 | Structure appearing in 3 permutations has 3 provenance entries in report | unit | `pytest tests/test_lsd_orchestrator.py -k "test_multi_perm_provenance" -x` | Wave 0 (new) |

**Testing strategy note:** The orchestrator and merger tests should NOT require the LSD binary. Use `unittest.mock.patch` to mock `LSDRunner.run_file()` returning pre-built `LSDResult` objects, and provide fixture SMILES files in `tmp_path` directories. This follows the existing `test_lsd_runner.py` pattern (tests mock the subprocess, not the binary).

### Sampling Rate
- **Per task commit:** `pytest tests/test_lsd_orchestrator.py -q`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite (893+ tests) green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_lsd_orchestrator.py` — all 8 test behaviors above; create new file
- [ ] No framework changes needed — uses existing pytest setup

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `src/lucy_ng/lsd/generator.py` — `LSDInputGenerator.write_file()`, `generate()` with `pylsd_mode`
- Direct code inspection: `src/lucy_ng/lsd/runner.py` — `LSDRunner.run_file()`, `_run_outlsd()` bug confirmed
- Direct code inspection: `src/lucy_ng/lsd/models.py` — `LSDProblem`, `LSDCorrelation` dataclasses
- Direct code inspection: `src/lucy_ng/lsd/parser.py` — `LSDOutputParser.parse_smiles_file()`
- Direct code inspection: `src/lucy_ng/ranking/ranker.py` — confirms `Chem.MolFromSmiles` pattern
- `.planning/REQUIREMENTS.md` — ORCH-01 through ORCH-04, K≤3 cap, deduplication by InChI
- `.planning/STATE.md` — "implement PyLSDOrchestrator directly in Python (~230 lines)", "ELIM does NOT extend bond ranges", outlsd bug deferred to Phase 69
- `.planning/phases/65-hypothesis-gate/validation_result.md` — confirms `outlsd 5 < compound.sol` syntax; ibuprofen 392 solutions; InChI comparison used for canonical SMILES verification
- `.planning/phases/66-lsdinputgenerator-extensions/66-02-SUMMARY.md` — confirms Phase 66 complete: `emit_form`, `emit_elim`, `emit_shih`, `validate_pylsd_input`, `pylsd_mode` flag all implemented
- Verified in project Python environment: `from rdkit.Chem.inchi import MolToInchi, InchiToInchiKey` works correctly
- `pyproject.toml` — `rdkit>=2023.0` confirmed as runtime dependency

### Secondary (MEDIUM confidence)
- `tests/test_lsd_runner.py` — established pattern for mocking LSD binary in tests
- `tests/test_ranking.py` — established `MagicMock` + `patch` pattern for avoiding real file I/O in tests
- Python stdlib `itertools.product` documentation — `product([True, False], repeat=K)` behavior for K=0 verified

### Tertiary (LOW confidence)
- STATE.md estimate "~230 lines" for PyLSDOrchestrator — from project planning notes, not measured from implemented code

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all infrastructure exists; RDKit InChI verified in environment; `itertools.product` is stdlib
- Architecture: HIGH — exact class boundaries, method signatures, and data flow identified from code inspection
- Pitfalls: HIGH — outlsd bug confirmed in STATE.md and Phase 65 artifacts; deepcopy identity issue is a standard Python pattern
- InChI deduplication correctness: HIGH — verified RDKit InChI generation in project environment
- outlsd mode argument requirement: HIGH — confirmed from Phase 65 `outlsd 5` usage in `ibuprofen_no4j.smi` production

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (internal codebase — valid until Phase 66 APIs change; no external dependencies added)
