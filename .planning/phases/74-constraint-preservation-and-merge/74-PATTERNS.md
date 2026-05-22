# Phase 74: Constraint Preservation and Merge — Pattern Map

**Mapped:** 2026-05-22
**Files analyzed:** 5 (2 modified Python source, 1 new package resource dir+files, 2 modified test files)
**Analogs found:** 5 / 5

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/lucy_ng/lsd/models.py` | model | CRUD (field extension) | self — existing `LSDConstraint`, `LSDCorrelation`, `LSDProblem` | exact (same file) |
| `src/lucy_ng/lsd/generator.py` | utility/serialiser | transform | self — existing `generate()`, `write_file()`, `emit_form()` | exact (same file) |
| `src/lucy_ng/lsd/filters/ring3` | config/resource | file-I/O | `/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3` (copy) | exact (verbatim copy) |
| `src/lucy_ng/lsd/filters/ring4` | config/resource | file-I/O | `/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4` (copy) | exact (verbatim copy) |
| `tests/test_lsd_generator.py` | test | — | existing `TestPyLSDExtensions` class (lines 389–507) | exact (same file, new class) |
| `tests/test_lsd_orchestrator.py` | test | — | existing `TestPermutationContent` class (lines 148–265) | exact (same file, new class) |

---

## Pattern Assignments

### `src/lucy_ng/lsd/models.py` (model, field extension)

**Analog:** `src/lucy_ng/lsd/models.py` — existing `LSDConstraint` and `LSDProblem` dataclasses

**Existing field declaration pattern** (lines 178–185, `LSDProblem`):
```python
@dataclass
class LSDProblem:
    atoms: list[LSDAtom] = field(default_factory=list)
    correlations: list[LSDCorrelation] = field(default_factory=list)
    constraints: list[LSDConstraint] = field(default_factory=list)
    molecular_formula: str | None = None
    name: str = "problem"
    comments: list[str] = field(default_factory=list)
    pylsd_mode: bool = False
    elim_commands: list[tuple[int, int]] = field(default_factory=list)
```

**Existing add_* helper method pattern** (lines 187–197):
```python
def add_atom(self, atom: LSDAtom) -> None:
    """Add an atom to the problem."""
    self.atoms.append(atom)

def add_correlation(self, correlation: LSDCorrelation) -> None:
    """Add a correlation to the problem."""
    self.correlations.append(correlation)

def add_constraint(self, constraint: LSDConstraint) -> None:
    """Add a structural constraint to the problem."""
    self.constraints.append(constraint)
```

**What to add — two new fields on `LSDProblem`:**

Option A (recommended by research — direct injection, no new model class):
```python
# New fields appended after elim_commands:
ring_exclusion_enabled: bool = False
# No new model class; equivalence pairs inject directly into
# problem.constraints (as BOND) and problem.correlations (as COSY)
# via a new add_equivalence_pair() method (see generator.py section).
```

Option B (semantically richer — new dataclass):
```python
from typing import Literal

@dataclass
class EquivalencePair:
    """A pair of topologically equivalent atoms."""
    atom1_index: int
    atom2_index: int
    equivalence_type: Literal["gem_dimethyl", "aromatic_ch_pair", "isopropyl"]
    parent_index: int | None = None

@dataclass
class RingExclusionConfig:
    """Ring exclusion via DEFF F / FEXP."""
    exclude_3_membered: bool = True
    exclude_4_membered: bool = True

# Then on LSDProblem:
equivalence_pairs: list[EquivalencePair] = field(default_factory=list)
ring_exclusion: RingExclusionConfig | None = None
```

**Research recommendation:** Option A (direct injection). `add_equivalence_pair()` adds
`LSDConstraint("BOND")` or `LSDCorrelation("COSY")` entries to the existing lists so
the existing section-rendering logic in `generate()` handles them automatically with no
new generator branches. If semantic tracking is needed later, a `reason` string on
`LSDConstraint` (already supported — see line 87) carries it.

**`LSDConstraint.__post_init__` validation** (lines 89–96) — `constraint_type` is
validated against `{"BOND", "FBND"}`. Do NOT add `"SYME"` here. The equivalence is
always expressed as `BOND` or `COSY`, never as `SYME`.

**`LSDCorrelation.__post_init__` validation** (lines 128–136) — `correlation_type`
validated against `{"HSQC", "HMBC", "COSY", "HMQC"}`. `"COSY"` is already valid;
equivalence-derived COSY lines use the existing type.

---

### `src/lucy_ng/lsd/generator.py` (serialiser, transform)

**Analog:** `src/lucy_ng/lsd/generator.py` — existing `generate()` and `write_file()` static methods

**Current imports** (lines 1–9):
```python
import re
from pathlib import Path

from lucy_ng.lsd.models import Hybridization, LSDAtom, LSDConstraint, LSDCorrelation, LSDProblem
from lucy_ng.models import PeakList1D, PeakList2D
from lucy_ng.processing.dept_guided_picker import DEPTGuidedResult
```

New imports to add:
```python
import importlib.resources
```

**Current `generate()` section-ordering pattern** (lines 88–190):
```
1. Header comments
2. pyLSD FORM comment + ELIM lines (pylsd_mode only)
3. MULT lines (atom definitions)
4. SHIX / SHIH lines (chemical shifts)
5. HSQC correlations
6. HMBC correlations
7. COSY correlations          ← equivalence-derived COSY lines land here
8. BOND constraints            ← equivalence-derived BOND lines land here
9. FBND constraints
10. EXIT
```

If Option A (direct injection) is chosen, no new generator sections are needed — COSY
and BOND from `add_equivalence_pair()` are rendered by the existing COSY and BOND
sections. The only new generator code is for ring exclusion.

**Current `write_file()` pattern** (lines 192–206):
```python
@staticmethod
def write_file(problem: LSDProblem, output_path: Path | str) -> Path:
    output_path = Path(output_path)
    content = LSDInputGenerator.generate(problem)
    output_path.write_text(content)
    return output_path
```

**What `write_file()` must gain** — a helper call to copy filter files:
```python
@staticmethod
def write_file(problem: LSDProblem, output_path: Path | str) -> Path:
    output_path = Path(output_path)
    content = LSDInputGenerator.generate(problem)
    output_path.write_text(content)
    # Copy bundled filter files to the same directory if ring exclusion is active.
    # LSD is always invoked with cwd=output_path.parent, so relative "ring3"/"ring4"
    # in the DEFF lines will resolve correctly.
    if _problem_has_ring_exclusion(problem, content):
        LSDInputGenerator._write_filter_files(output_path.parent)
    return output_path
```

**New static helper `_write_filter_files()`** (new private method, follows existing
`@staticmethod` pattern of `emit_form`, `emit_elim`, `emit_shih`):
```python
@staticmethod
def _write_filter_files(output_dir: Path) -> None:
    """Copy bundled ring3/ring4 filter files to output_dir.

    Filter files must be co-located with the .lsd file because LSD is
    invoked with cwd=output_dir and resolves relative DEFF paths from its CWD.
    Called by write_file() when ring exclusion is active.
    """
    package = importlib.resources.files("lucy_ng.lsd.filters")
    for name in ("ring3", "ring4"):
        content = (package / name).read_text()
        (output_dir / name).write_text(content)
```

**New ring exclusion section in `generate()`** — append before `EXIT`, after FBND:
```python
# Ring exclusion (DEFF F / FEXP) — emitted after FBND, before EXIT
# Filter files are written to output_dir by write_file() separately.
# generate() only emits the DEFF/FEXP command lines (relative paths).
if _problem_has_ring_exclusion(problem):
    lines.append("; Ring exclusion filters")
    lines.append('DEFF F1 "ring3"')
    lines.append('DEFF F2 "ring4"')
    lines.append('FEXP "NOT F1 AND NOT F2"')
    lines.append("")
```

**Ground-truth DEFF/FEXP output** (from `arm_a.lsd`, lines 54–56):
```
DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
FEXP "NOT F1 AND NOT F2"
```
Generated output uses relative paths (`"ring3"`, `"ring4"`) instead of absolute paths.
LSD resolves from its CWD, which is always `output_dir` per the Phase-73 runner contract.

**Existing `emit_*` static method pattern** (lines 41–86, three examples):
```python
@staticmethod
def emit_form(formula: str) -> str:
    """..."""
    return f"; FORM {formula}"

@staticmethod
def emit_elim(n: int, m: int) -> str:
    """..."""
    return f"ELIM {n} {m}"

@staticmethod
def emit_shih(atom_idx: int, shift: float) -> str:
    """..."""
    return f"SHIH {atom_idx} {shift:.2f}"
```
New `_write_filter_files()` and any new `emit_*` methods follow the same `@staticmethod`
declaration style on `LSDInputGenerator`, same docstring format.

**How `ring_exclusion_enabled` is detected in `generate()`:**
The simplest approach (Option A) is to add `ring_exclusion_enabled: bool = False` to
`LSDProblem` and check `problem.ring_exclusion_enabled` in `generate()`. Option B checks
`problem.ring_exclusion is not None`.

**COSY deduplication guard** (existing pattern, lines 496–503):
```python
seen_cosy: set[tuple[int, int]] = set()
...
key = tuple(sorted([h1_carbon, h2_carbon]))
if key not in seen_cosy:
    seen_cosy.add(key)
    problem.add_correlation(LSDCorrelation(..., correlation_type="COSY"))
```
The new `add_equivalence_pair()` method must apply the same deduplication: check whether
a `COSY (atom1, atom2)` already exists in `problem.correlations` before adding a second
one for the equivalence. This prevents duplicate COSY lines when COSY peak data and
equivalence pairs overlap.

---

### `src/lucy_ng/lsd/filters/ring3` and `ring4` (new package resources)

**Source files:** `/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3` and `ring4`
**Destination:** `src/lucy_ng/lsd/filters/ring3` and `src/lucy_ng/lsd/filters/ring4`

**Verbatim content of `ring3`** (verified working in iter3/arm_a):
```
; a generic 3-membered ring
SSTR S1 A (2 3) (0 1 2)
SSTR S2 A (2 3) (0 1 2)
SSTR S3 A (2 3) (0 1 2)
LINK S1 S2
LINK S2 S3
LINK S1 S3
```

**Verbatim content of `ring4`** (verified working in iter3/arm_a):
```
; a generic 4-membered ring
SSTR S1 A (2 3) (0 1 2)
SSTR S2 A (2 3) (0 1 2)
SSTR S3 A (2 3) (0 1 2)
SSTR S4 A (2 3) (0 1 2)
LINK S1 S2
LINK S2 S3
LINK S3 S4
LINK S1 S4
```

**`__init__.py`** — the filters package needs an `__init__.py` (can be empty, matching
the pattern at `src/lucy_ng/data/schemas/__init__.py` which is a 1-line empty file).

**Packaging pattern** — from `pyproject.toml` lines 53–58:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/lucy_ng"]
artifacts = ["src/lucy_ng/data/schemas/*"]
```
The `artifacts` key is how hatchling includes non-Python data files in the wheel.
The new filter files must be added to the `artifacts` list:
```toml
artifacts = [
    "src/lucy_ng/data/schemas/*",
    "src/lucy_ng/lsd/filters/*",
]
```

**`importlib.resources` access pattern** (Python 3.9+, standard library):
```python
import importlib.resources

package = importlib.resources.files("lucy_ng.lsd.filters")
content = (package / "ring3").read_text()
```
This is the same API already used by `lucy_ng.data.schemas` loading if it exists;
otherwise, use the pattern directly as shown. Do NOT use `__file__`-based path
construction, which breaks in zip-imported packages.

---

### `tests/test_lsd_generator.py` (test, new class `TestNativeConstraintEmission`)

**Analog:** `TestPyLSDExtensions` class (lines 389–507) and `TestLSDInputGeneratorFile`
class (lines 133–148) — same file

**Test class declaration pattern** (lines 389–392):
```python
class TestPyLSDExtensions:
    """Tests for pyLSD-specific emission methods and generate() integration."""
```

**`generate()` content-assertion pattern** (lines 434–446):
```python
def test_generate_pylsd_form_in_header(self):
    """FORM comment line appears in output when pylsd_mode=True and molecular_formula set."""
    problem = LSDProblem(
        pylsd_mode=True,
        molecular_formula="C13H18O2",
    )
    problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
    content = LSDInputGenerator.generate(problem)
    assert "; FORM C13H18O2" in content
    # FORM comment must appear before first MULT line
    form_pos = content.index("; FORM C13H18O2")
    mult_pos = content.index("MULT")
    assert form_pos < mult_pos
```

**`write_file()` + `tmp_path` pattern** (lines 136–147):
```python
def test_write_file(self):
    problem = LSDProblem(name="test")
    problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.lsd"
        result_path = LSDInputGenerator.write_file(problem, output_path)

        assert result_path.exists()
        content = result_path.read_text()
        assert "MULT 1 C 2 0" in content
```

**New test class to add** (`TestNativeConstraintEmission`):

Six tests required (from research Finding/validation-map):

1. `test_no_syme_in_output` — build problem with equivalence pair, assert `"SYME" not in content`
2. `test_no_deff_not_in_output` — build problem with ring_exclusion, assert `"DEFF NOT" not in content`
3. `test_gem_dimethyl_emits_bond` — gem-dimethyl equivalence → `"BOND 10 11"` and `"BOND 10 12"` in content
4. `test_aromatic_ch_pair_emits_cosy` — aromatic pair equivalence → `"COSY 4 7"` in content
5. `test_ring_exclusion_emits_deff_f_fexp` — ring_exclusion_enabled=True → `'DEFF F1 "ring3"'` + `'DEFF F2 "ring4"'` + `'FEXP "NOT F1 AND NOT F2"'` in content
6. `test_ring_files_written_to_output_dir` — `write_file()` with ring_exclusion → `ring3` and `ring4` files exist in output dir

**Skeleton of new test class** (follows existing class pattern exactly):
```python
class TestNativeConstraintEmission:
    """RELI-02: generated .lsd contains no SYME or DEFF NOT; equivalence → BOND/COSY."""

    def _make_ibuprofen_gem_dimethyl_problem(self) -> LSDProblem:
        """Minimal problem: gem-dimethyl pair (atoms 10, 11, 12 as per arm_a.lsd)."""
        problem = LSDProblem(name="gem_dimethyl_test")
        problem.add_atom(LSDAtom(10, "C", Hybridization.SP3, 1))   # isobutyl CH
        problem.add_atom(LSDAtom(11, "C", Hybridization.SP3, 3))   # CH3 #1
        problem.add_atom(LSDAtom(12, "C", Hybridization.SP3, 3))   # CH3 #2
        # add_equivalence_pair: gem_dimethyl, parent=10, children 11+12
        problem.add_equivalence_pair(parent_index=10, child1_index=11, child2_index=12)
        return problem

    def test_no_syme_in_output(self):
        """Generated LSD content never contains SYME."""
        problem = self._make_ibuprofen_gem_dimethyl_problem()
        content = LSDInputGenerator.generate(problem)
        assert "SYME" not in content

    def test_no_deff_not_in_output(self):
        """Generated LSD content never contains DEFF NOT."""
        problem = LSDProblem(name="ring_excl_test", ring_exclusion_enabled=True)
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        content = LSDInputGenerator.generate(problem)
        assert "DEFF NOT" not in content

    def test_gem_dimethyl_emits_bond(self):
        """Gem-dimethyl equivalence (parent=10, atoms 11+12) emits BOND 10 11 and BOND 10 12."""
        problem = self._make_ibuprofen_gem_dimethyl_problem()
        content = LSDInputGenerator.generate(problem)
        assert "BOND 10 11" in content
        assert "BOND 10 12" in content

    def test_aromatic_ch_pair_emits_cosy(self):
        """Aromatic CH pair equivalence emits COSY 4 7 and COSY 5 6 (arm_a.lsd ground truth)."""
        problem = LSDProblem(name="aromatic_cosy_test")
        for idx in [4, 5, 6, 7]:
            problem.add_atom(LSDAtom(idx, "C", Hybridization.SP2, 1))
        problem.add_aromatic_equivalence_pair(4, 7)
        problem.add_aromatic_equivalence_pair(5, 6)
        content = LSDInputGenerator.generate(problem)
        assert "COSY 4 7" in content
        assert "COSY 5 6" in content

    def test_ring_exclusion_emits_deff_f_fexp(self):
        """ring_exclusion_enabled=True emits DEFF F1/F2 and FEXP."""
        problem = LSDProblem(name="ring_excl_test", ring_exclusion_enabled=True)
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        content = LSDInputGenerator.generate(problem)
        assert 'DEFF F1 "ring3"' in content
        assert 'DEFF F2 "ring4"' in content
        assert 'FEXP "NOT F1 AND NOT F2"' in content

    def test_ring_files_written_to_output_dir(self, tmp_path):
        """write_file() copies ring3 and ring4 filter files to output dir."""
        problem = LSDProblem(name="ring_excl_test", ring_exclusion_enabled=True)
        problem.add_atom(LSDAtom(1, "C", Hybridization.SP2, 0))
        LSDInputGenerator.write_file(problem, tmp_path / "test.lsd")
        assert (tmp_path / "ring3").exists()
        assert (tmp_path / "ring4").exists()
```

**Note on method names for `LSDProblem`:** The research recommends `add_equivalence_pair()`
as a single method that internally adds the appropriate `LSDConstraint("BOND")` or
`LSDCorrelation("COSY")`. The test skeleton above uses two separate methods for clarity
(`add_equivalence_pair` for gem-dimethyl BOND, `add_aromatic_equivalence_pair` for COSY).
The planner may collapse these into one method with a `kind` parameter.

---

### `tests/test_lsd_orchestrator.py` (test, new class `TestPermutationConstraintPreservation`)

**Analog:** `TestPermutationContent` class (lines 148–265) — same file

**`_make_problem()` helper** (lines 21–50) — reused in new test class:
```python
def _make_problem(name: str = "test") -> LSDProblem:
    problem = LSDProblem(name=name, pylsd_mode=True)
    for i in range(1, 5):
        problem.add_atom(LSDAtom(index=i, element="C", hybridization=Hybridization.SP2, hydrogen_count=1))
    for i in range(1, 5):
        problem.add_correlation(LSDCorrelation(atom1_index=i, atom2_index=i, correlation_type="HSQC"))
    problem.add_correlation(LSDCorrelation(atom1_index=1, atom2_index=2, correlation_type="HMBC"))
    problem.add_correlation(LSDCorrelation(atom1_index=2, atom2_index=3, correlation_type="HMBC"))
    return problem
```

**`capture_write` / `patch` pattern** (lines 174–183):
```python
from lucy_ng.lsd.generator import LSDInputGenerator
original_write = LSDInputGenerator.write_file

def capture_write(prob: LSDProblem, path: Path) -> Path:
    written_problems.append(prob)
    return original_write(prob, path)

with patch("lucy_ng.lsd.orchestrator.LSDInputGenerator.write_file", side_effect=capture_write), \
     patch.object(orchestrator.runner, "run_file", return_value=_make_lsd_result()), \
     patch.object(orchestrator, "_run_outlsd", return_value=None):
    orchestrator.run(problem, suspects, output_dir=tmp_path / "out")
```

**New test class to add** (`TestPermutationConstraintPreservation`):

Two tests required:

1. `test_perm_preserves_bond_constraints` — problem with BOND constraints → all perm
   LSD files contain those BOND lines (RELI-02 permutation path)
2. `test_perm_preserves_ring_exclusion` — problem with `ring_exclusion_enabled=True` →
   all perm LSD files contain `DEFF F1` and filter files exist in each perm dir

**Skeleton**:
```python
class TestPermutationConstraintPreservation:
    """RELI-02: permutation deepcopy preserves BOND, COSY, and ring exclusion constraints."""

    def test_perm_preserves_bond_constraints(self, tmp_path: Path) -> None:
        """BOND constraints on base_problem appear in every permutation .lsd file."""
        problem = _make_problem()
        # Add a BOND constraint (e.g., gem-dimethyl equivalence)
        problem.add_atom(LSDAtom(index=10, element="C", hybridization=Hybridization.SP3, hydrogen_count=1))
        problem.add_atom(LSDAtom(index=11, element="C", hybridization=Hybridization.SP3, hydrogen_count=3))
        problem.add_atom(LSDAtom(index=12, element="C", hybridization=Hybridization.SP3, hydrogen_count=3))
        from lucy_ng.lsd.models import LSDConstraint
        problem.add_constraint(LSDConstraint(atom1_index=10, atom2_index=11, constraint_type="BOND"))
        problem.add_constraint(LSDConstraint(atom1_index=10, atom2_index=12, constraint_type="BOND"))

        suspects = _make_suspects(2)
        for s in suspects:
            problem.add_atom(LSDAtom(index=s.atom1_index, element="C",
                                     hybridization=Hybridization.SP2, hydrogen_count=0))
            problem.add_correlation(s)

        orchestrator = PyLSDOrchestrator()
        with patch.object(orchestrator.runner, "run_file", return_value=_make_lsd_result()), \
             patch.object(orchestrator, "_run_outlsd", return_value=None):
            result = orchestrator.run(problem, suspects, output_dir=tmp_path / "out")

        # Every permutation .lsd file must contain the BOND constraints
        perm_dirs = sorted((tmp_path / "out").glob("perm_*"))
        assert len(perm_dirs) == 4  # K=2
        for perm_dir in perm_dirs:
            lsd_content = next(perm_dir.glob("*.lsd")).read_text()
            assert "BOND 10 11" in lsd_content, f"{perm_dir.name} missing BOND 10 11"
            assert "BOND 10 12" in lsd_content, f"{perm_dir.name} missing BOND 10 12"

    def test_perm_preserves_ring_exclusion(self, tmp_path: Path) -> None:
        """ring_exclusion_enabled=True propagates to every permutation .lsd file."""
        problem = _make_problem()
        problem.ring_exclusion_enabled = True  # or however the field is named

        suspects = _make_suspects(1)
        for s in suspects:
            problem.add_atom(LSDAtom(index=s.atom1_index, element="C",
                                     hybridization=Hybridization.SP2, hydrogen_count=0))
            problem.add_correlation(s)

        orchestrator = PyLSDOrchestrator()
        with patch.object(orchestrator.runner, "run_file", return_value=_make_lsd_result()), \
             patch.object(orchestrator, "_run_outlsd", return_value=None):
            result = orchestrator.run(problem, suspects, output_dir=tmp_path / "out")

        perm_dirs = sorted((tmp_path / "out").glob("perm_*"))
        assert len(perm_dirs) == 2  # K=1
        for perm_dir in perm_dirs:
            lsd_content = next(perm_dir.glob("*.lsd")).read_text()
            assert 'DEFF F1 "ring3"' in lsd_content, f"{perm_dir.name} missing DEFF F1"
            assert 'FEXP "NOT F1 AND NOT F2"' in lsd_content, f"{perm_dir.name} missing FEXP"
            assert (perm_dir / "ring3").exists(), f"{perm_dir.name} missing ring3 filter file"
            assert (perm_dir / "ring4").exists(), f"{perm_dir.name} missing ring4 filter file"
```

---

## Shared Patterns

### Dataclass field extension
**Source:** `src/lucy_ng/lsd/models.py` lines 163–185
**Apply to:** `LSDProblem` extension
- All new fields use `field(default_factory=...)` for mutable defaults or a scalar default.
- `bool` fields default to `False`; optional complex fields default to `None`.
- `__post_init__` validates; do NOT add new validation for the new fields unless there is
  a clear invalid state (e.g., `ring_exclusion_enabled=True` with no filter package is
  not validated at model level — fail is caught at write time).

### `@staticmethod` on `LSDInputGenerator`
**Source:** `src/lucy_ng/lsd/generator.py` lines 41–86
**Apply to:** All new methods on `LSDInputGenerator` (`_write_filter_files`, any `emit_*`)
- All methods are `@staticmethod` — no `self` or `cls` parameter.
- Docstring: one-line summary + blank line + `Args:` + `Returns:` sections.
- Return type is explicit.

### Test class structure
**Source:** `tests/test_lsd_generator.py` lines 389–507 (`TestPyLSDExtensions`)
**Apply to:** `TestNativeConstraintEmission`
- Class-level docstring states the requirement ID being verified (e.g., `"""RELI-02: ...`).
- Each test has a single-sentence docstring stating the expected outcome.
- Fixtures are either `tmp_path` (pytest built-in) or private `_make_*` helpers on the class.
- No `self`-state mutations across tests.

### Permutation test capture pattern
**Source:** `tests/test_lsd_orchestrator.py` lines 169–183
**Apply to:** `TestPermutationConstraintPreservation`
- Use `patch("lucy_ng.lsd.orchestrator.LSDInputGenerator.write_file", ...)` (full import
  path as used in the orchestrator module), not `patch.object(LSDInputGenerator, ...)`.
- `_run_outlsd` always patched to return `None` in unit tests.
- `orchestrator.runner.run_file` patched via `patch.object`.

### Filter file discovery (importlib.resources)
**Source:** Python 3.9+ standard library; no existing analog in codebase
**Apply to:** `LSDInputGenerator._write_filter_files()`
```python
import importlib.resources

def _get_bundled_filter(name: str) -> str:
    package = importlib.resources.files("lucy_ng.lsd.filters")
    return (package / name).read_text()
```
This pattern requires `src/lucy_ng/lsd/filters/__init__.py` to exist (even empty), so
`lucy_ng.lsd.filters` is a discoverable package namespace.

---

## No Analog Found

No files are without analog. All five file modifications/additions copy directly from
either the same file's existing patterns or verified ground-truth LSD files.

---

## Implementation Order (for planner)

The research recommends the following dependency order:

| Wave | Files | Reason |
|------|-------|--------|
| 0 | `src/lucy_ng/lsd/filters/ring3`, `ring4`, `__init__.py`; `pyproject.toml` artifacts update | No deps; must exist before generator can import them |
| 1 | `src/lucy_ng/lsd/models.py` (new fields + add_equivalence_pair()) | Generator depends on model fields |
| 1 | `tests/test_lsd_generator.py` (new `TestNativeConstraintEmission` class) | TDD RED: write tests before implementation |
| 1 | `tests/test_lsd_orchestrator.py` (new `TestPermutationConstraintPreservation` class) | TDD RED |
| 2 | `src/lucy_ng/lsd/generator.py` (ring exclusion emission + `_write_filter_files`) | Depends on models + filters package |

---

## Ground-Truth Native Constraint Lines (arm_a.lsd)

For exact emission verification, the complete constraint + ring exclusion section from
`arm_a.lsd` (verified: 2/2 aromatic solutions, ibuprofen found):

```
BOND 1 14
BOND 1 15
BOND 10 11
BOND 10 12

COSY 9 13
COSY 4 7
COSY 5 6
COSY 8 10
COSY 10 11

DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
FEXP "NOT F1 AND NOT F2"
```

Lines `BOND 10 11` + `BOND 10 12` = gem-dimethyl equivalence (parent atom 10, CH).
Lines `COSY 4 7` + `COSY 5 6` = aromatic CH-pair equivalence (para-disubstituted benzene).
`DEFF F1 "ring3"` + `DEFF F2 "ring4"` + `FEXP` = relative-path ring exclusion (Phase 74 bundled form).

---

## Metadata

**Analog search scope:** `src/lucy_ng/lsd/`, `tests/`, `.planning/phases/72-design-re-validation/experiment/`, `/Users/steinbeck/Dropbox/develop/LSD/Filters/`
**Files scanned:** 10 (models.py, generator.py, test_lsd_generator.py, test_lsd_orchestrator.py, arm_a.lsd, run_experiment.py, pyproject.toml, lsd/__init__.py, data/schemas/__init__.py, ring3, ring4)
**Pattern extraction date:** 2026-05-22
